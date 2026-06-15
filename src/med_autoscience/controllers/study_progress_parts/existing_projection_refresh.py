from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state
from med_autoscience.controllers import current_execution_envelope, current_work_unit
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    PROVIDER_ADMISSION_AUTHORITIES,
)
from med_autoscience.controllers.stage_artifact_index import build_stage_artifact_index
from med_autoscience.profiles import WorkspaceProfile

from .current_executable_owner_action import build_current_executable_owner_action
from .current_owner_action_projection_reconcile import (
    current_execution_evidence_actions,
    current_execution_envelope_actions,
    current_control_typed_blocker_successor_action,
    reconcile_current_owner_action_projection,
)
from .current_control_executable_handoff import (
    current_control_executable_currentness_handoff,
    current_control_executable_owner_action,
)
from .delivery_inspection import attach_delivery_inspection_projection
from .opl_current_control_state_handoff import (
    merge_live_attempt_observability_into_handoff,
    opl_current_control_state_live_attempt_handoff_projection,
)
from .operator_view import _study_command_surfaces
from .progress_first_monitoring import build_progress_first_monitoring_summary
from .projection_payload_assembly_parts.current_execution_surfaces import (
    refresh_current_execution_surfaces,
)
from .projection_payload_assembly_parts.progress_delta import progress_delta_metrics
from .projection_payload_assembly_parts.paper_recovery_visibility import (
    apply_paper_recovery_state_user_visible_status,
)
from .progression import _domain_transition_route_repair
from .provider_admission_projection import provider_admission_projection_fields
from .provider_admission_sync import sync_progress_first_owner_action_admission
from .publication_runtime_followthrough import (
    _gate_clearing_batch_followthrough,
    _quality_repair_batch_followthrough,
)
from .repair_progress_projection import build_repair_progress_projection
from .projection_payload_assembly_parts.running_provider_status import (
    apply_running_provider_attempt_top_level_status,
)
from .shared import _mapping_copy, _non_empty_text, _route_repair_summary
from .user_visible_projection import build_user_visible_projection


def refresh_existing_projection_user_visible_status(payload: dict[str, Any]) -> dict[str, Any]:
    redrive_next_action = current_redrive_top_level_next_action(payload)
    if redrive_next_action is not None:
        updated = dict(payload)
        updated["user_visible_projection"] = build_user_visible_projection(updated)
        updated["next_system_action"] = redrive_next_action
        status_contract = _mapping_copy(updated.get("status_narration_contract"))
        if status_contract:
            status_contract["next_step"] = redrive_next_action
            updated["status_narration_contract"] = status_contract
        return updated
    return payload


def refresh_existing_projection_batch_followthroughs(
    *,
    payload: dict[str, Any],
    status: dict[str, Any],
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_id: str,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    updated = dict(payload)
    study_commands = _study_command_surfaces(
        profile=profile,
        study_id=study_id,
        profile_ref=profile_ref,
    )
    updated["gate_clearing_batch_followthrough"] = _gate_clearing_batch_followthrough(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        current_eval_ids=current_gate_clearing_eval_ids(status=status),
    )
    updated["quality_repair_batch_followthrough"] = _quality_repair_batch_followthrough(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        recommended_command=study_commands.get("quality_repair_batch"),
    )
    return refresh_existing_projection_repair_progress(
        payload=updated,
        study_root=study_root,
    )


def refresh_existing_projection_repair_progress(
    *,
    payload: dict[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    updated = dict(payload)
    repair_progress = build_repair_progress_projection(study_root=study_root)
    updated["repair_progress_projection"] = repair_progress
    updated.update(
        progress_delta_metrics(
            quality_repair_batch_followthrough=_mapping_copy(
                updated.get("quality_repair_batch_followthrough")
            ),
            gate_clearing_batch_followthrough=_mapping_copy(
                updated.get("gate_clearing_batch_followthrough")
            ),
            opl_current_control_state_handoff=_mapping_copy(
                updated.get("opl_current_control_state_handoff")
            ),
            runtime_efficiency=_mapping_copy(updated.get("runtime_efficiency")),
            repair_progress_projection=repair_progress,
        )
    )
    return updated


def refresh_existing_projection_current_owner_surfaces(
    *,
    payload: dict[str, Any],
    status: dict[str, Any],
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
    attach_delivery_inspection_projection_fn: Callable[..., dict[str, Any]] = attach_delivery_inspection_projection,
) -> dict[str, Any]:
    updated = dict(payload)
    if publication_eval_payload is not None:
        updated["publication_eval"] = publication_eval_payload
    handoff = merge_live_attempt_observability_into_handoff(
        handoff=_optional_mapping(updated.get("opl_current_control_state_handoff")),
        live_attempt_handoff=opl_current_control_state_live_attempt_handoff_projection(
            profile=profile,
            study_id=_non_empty_text(updated.get("study_id")) or _non_empty_text(status.get("study_id")) or "",
            runtime_liveness_audit=_mapping_copy(status.get("runtime_liveness_audit")),
        ),
    )
    if handoff is not None:
        updated["opl_current_control_state_handoff"] = handoff
    else:
        updated["opl_current_control_state_handoff"] = None
        handoff = {}
    current_control_executable_action = current_control_executable_owner_action(handoff)
    if current_control_executable_action and not _handoff_is_active_provider_control(handoff):
        recomputed_action = build_current_executable_owner_action(updated)
        if recomputed_action is not None:
            current_control_executable_action = recomputed_action
    currentness_handoff = current_control_executable_currentness_handoff(
        handoff,
        current_control_executable_action=current_control_executable_action,
    )
    updated = _apply_current_control_currentness_to_existing_projection(updated, handoff=handoff)
    typed_blocker_successor_action = (
        current_control_executable_action
        or build_current_executable_owner_action(updated)
    )
    if _current_control_handoff_is_typed_blocker(handoff) and not current_control_typed_blocker_successor_action(
        typed_blocker_successor_action,
        typed_blocker=_current_control_typed_blocker_for_successor_check(handoff),
        progress=updated,
    ):
        updated["current_executable_owner_action"] = None
        updated["progress_first_monitoring_summary"] = build_progress_first_monitoring_summary(updated)
        updated.update(
            provider_admission_projection_fields(
                payload=updated,
                handoff=currentness_handoff,
                study_root=study_root,
            )
        )
        updated["owner_action_admission"] = {
            "admission_pending": False,
            "reason": "current_control_typed_blocker",
        }
        updated = sync_current_execution_evidence(updated, handoff=currentness_handoff)
        updated["paper_recovery_state"] = build_paper_recovery_state(updated)
        updated = refresh_paper_recovery_successor_surfaces(
            payload=updated,
            status=status,
            handoff=currentness_handoff,
            study_root=study_root,
        )
        updated = apply_paper_recovery_state_user_visible_status(updated)
        updated["user_visible_projection"] = build_user_visible_projection(updated)
        return attach_delivery_inspection_projection_fn(
            updated,
            profile=profile,
            profile_ref=profile_ref,
            study_root=study_root,
        )
    current_action = typed_blocker_successor_action
    if current_action is None and handoff.get("running_provider_attempt") is not True:
        updated.update(
            provider_admission_projection_fields(
                payload=updated,
                handoff=currentness_handoff,
                study_root=study_root,
            )
        )
        if _mapping_copy(updated.get("current_executable_owner_action")) or _mapping_copy(
            updated.get("progress_first_monitoring_summary")
        ):
            updated["progress_first_monitoring_summary"] = build_progress_first_monitoring_summary(updated)
            updated = sync_progress_first_owner_action_admission(updated)
        updated = sync_current_execution_evidence(updated, handoff=currentness_handoff)
        return attach_delivery_inspection_projection_fn(
            updated,
            profile=profile,
            profile_ref=profile_ref,
            study_root=study_root,
        )
    if current_action is not None:
        updated["current_executable_owner_action"] = current_action
        updated = reconcile_current_owner_action_projection(updated)
    current_control_typed_blocker = _mapping_copy(currentness_handoff.get("typed_blocker"))
    current_control_blocked_reason = _non_empty_text(currentness_handoff.get("blocked_reason"))
    current_control_next_owner = _non_empty_text(currentness_handoff.get("next_owner"))
    if current_action is not None and current_work_unit.action_supersedes_typed_blocker(
        action=current_action,
        blocker=current_control_typed_blocker,
        progress=updated,
    ):
        current_control_typed_blocker = {}
        current_control_blocked_reason = None
        current_control_next_owner = None
    progress_state = _mapping_copy(updated.get("progress_first_sprint_state"))
    envelope_actions = current_execution_envelope_actions(
        handoff=currentness_handoff,
        current_executable_owner_action=_mapping_copy(updated.get("current_executable_owner_action")),
        paper_progress_delta_counted=progress_state.get("paper_progress_delta_counted") is True,
    )
    runtime_health_snapshot = _mapping_copy(updated.get("runtime_health_snapshot"))
    updated["current_work_unit"] = current_work_unit.build_current_work_unit(
        status=status,
        progress=updated,
        actions=envelope_actions,
        current_executable_owner_action=_mapping_copy(updated.get("current_executable_owner_action")),
        provider_admission=currentness_handoff,
        live_provider_attempt=currentness_handoff,
        typed_blocker=current_control_typed_blocker,
        blocked_reason=current_control_blocked_reason,
        next_owner=current_control_next_owner,
        runtime_health=runtime_health_snapshot,
    )
    updated["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
        status=status,
        progress=updated,
        actions=envelope_actions,
        blocked_reason=current_control_blocked_reason,
        next_owner=current_control_next_owner,
        typed_blocker=current_control_typed_blocker,
        runtime_health=runtime_health_snapshot,
        live_provider_attempt=currentness_handoff,
        current_work_unit_payload=_mapping_copy(updated.get("current_work_unit")),
    )
    updated["progress_first_monitoring_summary"] = build_progress_first_monitoring_summary(updated)
    updated.update(
        provider_admission_projection_fields(
            payload=updated,
            handoff=currentness_handoff,
            study_root=study_root,
        )
    )
    updated = sync_progress_first_owner_action_admission(updated)
    updated = apply_running_provider_attempt_top_level_status(updated)
    updated = sync_current_execution_evidence(
        updated,
        handoff=currentness_handoff,
        action_queue=envelope_actions,
    )
    updated["paper_recovery_state"] = build_paper_recovery_state(updated)
    updated = refresh_paper_recovery_successor_surfaces(
        payload=updated,
        status=status,
        handoff=currentness_handoff,
        study_root=study_root,
    )
    updated = apply_paper_recovery_state_user_visible_status(updated)
    updated["user_visible_projection"] = build_user_visible_projection(updated)
    return attach_delivery_inspection_projection_fn(
        updated,
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )


def _apply_current_control_currentness_to_existing_projection(
    payload: dict[str, Any],
    *,
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    if handoff.get("running_provider_attempt") is True:
        return payload
    handoff_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    handoff_executable_action = current_control_executable_owner_action(handoff)
    if _non_empty_text(handoff_work_unit.get("status")) not in {"typed_blocker", "blocked_current_work_unit"}:
        if (
            _non_empty_text(handoff_envelope.get("state_kind")) != "typed_blocker"
            and not handoff_executable_action
        ):
            return payload
    updated = dict(payload)
    if handoff_work_unit:
        updated["current_work_unit"] = handoff_work_unit
    if handoff_envelope:
        updated["current_execution_envelope"] = handoff_envelope
    if _mapping_copy(handoff.get("typed_blocker")):
        updated["current_executable_owner_action"] = None
    elif handoff_executable_action:
        updated["current_executable_owner_action"] = handoff_executable_action
    elif "current_executable_owner_action" in handoff:
        updated["current_executable_owner_action"] = _mapping_copy(
            handoff.get("current_executable_owner_action")
        ) or None
    if "provider_admission_pending_count" in handoff:
        updated["provider_admission_pending_count"] = int(
            handoff.get("provider_admission_pending_count") or 0
        )
    if "provider_admission_candidates" in handoff:
        updated["provider_admission_candidates"] = [
            dict(item)
            for item in handoff.get("provider_admission_candidates") or []
            if isinstance(item, Mapping)
        ]
    return updated


def _handoff_is_active_provider_control(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is True:
        return True
    if handoff.get("provider_admission_pending_count") not in (None, 0):
        return True
    if handoff.get("provider_attempt_or_lease_required") is True:
        return True
    if _non_empty_text(handoff.get("execution_status")) == "handoff_ready":
        return True
    if any(_mapping_copy(item) for item in handoff.get("provider_admission_candidates") or []):
        return True
    return any(
        _non_empty_text(_mapping_copy(item).get("authority")) in PROVIDER_ADMISSION_AUTHORITIES
        for item in handoff.get("action_queue") or []
    )


def _current_control_handoff_is_typed_blocker(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is True:
        return False
    handoff_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    if _non_empty_text(handoff_work_unit.get("status")) in {"typed_blocker", "blocked_current_work_unit"}:
        return True
    handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    return _non_empty_text(handoff_envelope.get("state_kind")) == "typed_blocker"


def _current_control_typed_blocker_for_successor_check(handoff: Mapping[str, Any]) -> dict[str, Any]:
    typed_blocker = _mapping_copy(handoff.get("typed_blocker"))
    if typed_blocker:
        return typed_blocker
    current = _mapping_copy(handoff.get("current_work_unit"))
    state = _mapping_copy(current.get("state"))
    current_blocker = _mapping_copy(state.get("typed_blocker"))
    if current_blocker:
        return current_blocker
    envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    envelope_blocker = _mapping_copy(envelope.get("typed_blocker"))
    if envelope_blocker:
        return envelope_blocker
    return {}


def refresh_paper_recovery_successor_surfaces(
    *,
    payload: dict[str, Any],
    status: dict[str, Any],
    handoff: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    current_control_executable_action = current_control_executable_owner_action(handoff)
    if current_control_executable_action:
        return payload
    if _repair_progress_gate_followup_current(payload):
        return payload
    recovery_payload = dict(payload)
    recovery_payload["paper_recovery_state"] = build_paper_recovery_state(recovery_payload)
    current_action = build_current_executable_owner_action(recovery_payload)
    if _non_empty_text(_mapping_copy(current_action).get("source")) != (
        "paper_recovery_state.next_safe_action.successor_owner_action"
    ):
        return payload
    runtime_health_snapshot = _mapping_copy(payload.get("runtime_health_snapshot")) or _mapping_copy(
        status.get("runtime_health_snapshot")
    )
    updated = refresh_current_execution_surfaces(
        payload={**payload, "current_executable_owner_action": current_action},
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    updated.update(
        provider_admission_projection_fields(
            payload=updated,
            handoff=handoff,
            study_root=study_root,
        )
    )
    updated["progress_first_monitoring_summary"] = build_progress_first_monitoring_summary(updated)
    updated = sync_progress_first_owner_action_admission(updated)
    updated = sync_current_execution_evidence(updated, handoff=handoff)
    updated["paper_recovery_state"] = build_paper_recovery_state(updated)
    return updated


def _repair_progress_gate_followup_current(payload: Mapping[str, Any]) -> bool:
    action = _mapping_copy(payload.get("current_executable_owner_action"))
    if _non_empty_text(action.get("source")) != "repair_progress_projection.mas_owner_repair_execution_evidence":
        return False
    if _non_empty_text(action.get("action_type")) != "run_gate_clearing_batch":
        return False
    repair_progress = _mapping_copy(payload.get("repair_progress_projection"))
    if repair_progress.get("paper_delta_observed") is not True:
        return False
    if repair_progress.get("accepted_owner_receipt") is not True:
        return False
    if repair_progress.get("gate_replay_done") is not True:
        return False
    current = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current.get("status")) != "executable_owner_action":
        return False
    return (
        _non_empty_text(current.get("action_type")) == "run_gate_clearing_batch"
        and _non_empty_text(current.get("work_unit_id")) == "publication_gate_replay"
    )


def _optional_mapping(value: object) -> dict[str, Any] | None:
    return dict(value) if isinstance(value, Mapping) else None


def sync_current_execution_evidence(
    payload: dict[str, Any],
    *,
    handoff: Mapping[str, Any],
    action_queue: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    updated = dict(payload)
    runtime_health_snapshot = _mapping_copy(updated.get("runtime_health_snapshot"))
    progress_state = _mapping_copy(updated.get("progress_first_sprint_state"))
    evidence_actions = (
        action_queue
        if action_queue is not None
        else current_execution_evidence_actions(
            handoff=handoff,
            current_executable_owner_action=_mapping_copy(updated.get("current_executable_owner_action")),
            paper_progress_delta_counted=progress_state.get("paper_progress_delta_counted") is True,
        )
    )
    updated["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
        action_queue=evidence_actions,
        runtime_health=runtime_health_snapshot,
        extra={
            "opl_current_control_state_handoff": dict(handoff) if handoff else None,
        },
    )
    return updated


def current_redrive_top_level_next_action(payload: dict[str, Any]) -> str | None:
    transition = _mapping_copy(payload.get("domain_transition"))
    if _non_empty_text(transition.get("decision_type")) not in {
        "ai_reviewer_re_eval",
        "bundle_stage_finalize",
        "publication_gate_blocker",
        "route_back_same_line",
    }:
        return None
    macro_state = _mapping_copy(payload.get("study_macro_state"))
    if _non_empty_text(macro_state.get("writer_state")) == "live":
        return None
    intervention_lane = _mapping_copy(payload.get("intervention_lane"))
    route_repair = _domain_transition_route_repair(payload)
    next_work_unit = _mapping_copy(transition.get("next_work_unit"))
    return (
        _non_empty_text(intervention_lane.get("route_summary"))
        or _non_empty_text(intervention_lane.get("summary"))
        or _route_repair_summary(route_repair)
        or _non_empty_text(next_work_unit.get("unit_id"))
    )


def current_gate_clearing_eval_ids(
    *,
    status: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any] | None = None,
) -> list[str]:
    eval_ids: list[str] = []

    def add(value: object) -> None:
        text = _non_empty_text(value)
        if text is not None and text not in eval_ids:
            eval_ids.append(text)

    transition = _mapping_copy(status.get("domain_transition"))
    completion = _mapping_copy(transition.get("completion_receipt_consumption"))
    add(completion.get("eval_id"))
    add(completion.get("source_eval_id"))
    completion_basis = _mapping_copy(completion.get("owner_route_currentness_basis"))
    add(completion_basis.get("source_eval_id"))
    transition_refs = _mapping_copy(transition.get("source_refs"))
    add(transition_refs.get("source_eval_id"))
    if next_forced_delta is not None:
        delta = _mapping_copy(next_forced_delta)
        add(delta.get("eval_id"))
        add(delta.get("source_eval_id"))
        owner_action = _mapping_copy(delta.get("owner_action"))
        add(owner_action.get("eval_id"))
        add(owner_action.get("source_eval_id"))
        ticket_refs = _mapping_copy(_mapping_copy(delta.get("current_owner_ticket")).get("source_refs"))
        add(ticket_refs.get("source_eval_id"))
    return eval_ids


def stage_artifact_index_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    build_stage_artifact_index_fn: Callable[..., dict[str, Any] | None] = build_stage_artifact_index,
) -> dict[str, Any] | None:
    del profile
    payload = build_stage_artifact_index_fn(study_id=study_id, study_root=study_root)
    if not isinstance(payload, dict):
        return None
    if _non_empty_text(payload.get("surface_kind")) != "stage_artifact_index":
        return None
    return dict(payload)


__all__ = [
    "current_gate_clearing_eval_ids",
    "current_redrive_top_level_next_action",
    "refresh_existing_projection_batch_followthroughs",
    "refresh_existing_projection_current_owner_surfaces",
    "refresh_existing_projection_repair_progress",
    "refresh_existing_projection_user_visible_status",
    "stage_artifact_index_projection",
    "sync_progress_first_owner_action_admission",
]
