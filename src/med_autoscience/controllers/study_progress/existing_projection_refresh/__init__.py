from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from ..delivery_inspection import attach_delivery_inspection_projection
from ..opl_current_control_state_handoff import (
    merge_live_attempt_observability_into_handoff,
    opl_current_control_state_live_attempt_handoff_projection,
    opl_current_control_state_study_handoff_projection,
)
from ..operator_view import _study_command_surfaces
from ..progression import _domain_transition_route_repair
from ..projection_payload_assembly.progress_delta import progress_delta_metrics
from ..publication_runtime_followthrough import (
    _gate_clearing_batch_followthrough,
    _quality_repair_batch_followthrough,
)
from ..repair_progress_projection import build_repair_progress_projection
from ..shared import _mapping_copy, _non_empty_text, _route_repair_summary
from ..user_visible_projection import build_user_visible_projection


def refresh_existing_projection_user_visible_status(payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    if next_action := current_redrive_top_level_next_action(updated):
        updated["next_system_action"] = next_action
    updated["user_visible_projection"] = build_user_visible_projection(updated)
    return updated


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
    del profile_ref
    updated = dict(payload)
    commands = _study_command_surfaces(profile=profile, study_id=study_id, profile_ref=None)
    eval_ids = current_gate_clearing_eval_ids(status=status)
    updated["gate_clearing_batch_followthrough"] = _gate_clearing_batch_followthrough(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        current_eval_ids=eval_ids,
    )
    updated["quality_repair_batch_followthrough"] = _quality_repair_batch_followthrough(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        current_eval_ids=eval_ids,
        recommended_command=commands.get("quality_repair_batch"),
    )
    return refresh_existing_projection_repair_progress(payload=updated, study_root=study_root)


def refresh_existing_projection_repair_progress(
    *, payload: dict[str, Any], study_root: Path
) -> dict[str, Any]:
    updated = dict(payload)
    repair = build_repair_progress_projection(study_root=study_root)
    updated["repair_progress_projection"] = repair
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
            repair_progress_projection=repair,
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
    study_id = _non_empty_text(updated.get("study_id")) or _non_empty_text(status.get("study_id")) or ""
    handoff = opl_current_control_state_study_handoff_projection(profile=profile, study_id=study_id)
    handoff = merge_live_attempt_observability_into_handoff(
        handoff=handoff,
        live_attempt_handoff=opl_current_control_state_live_attempt_handoff_projection(
            profile=profile,
            study_id=study_id,
            runtime_liveness_audit=_mapping_copy(status.get("runtime_liveness_audit")),
        ),
    )
    updated["opl_current_control_state_handoff"] = handoff or None
    for legacy_field in (
        "current_work_unit",
        "current_execution_envelope",
        "current_executable_owner_action",
        "paper_recovery_state",
        "provider_admission_candidates",
        "provider_admission_pending_count",
        "transition_request_candidates",
        "transition_request_pending_count",
    ):
        updated.pop(legacy_field, None)
    updated["user_visible_projection"] = build_user_visible_projection(updated)
    return attach_delivery_inspection_projection_fn(
        updated,
        profile=profile,
        profile_ref=profile_ref,
        study_root=study_root,
    )


def current_redrive_top_level_next_action(payload: dict[str, Any]) -> str | None:
    transition = _mapping_copy(payload.get("domain_transition"))
    if _non_empty_text(transition.get("decision_type")) not in {
        "ai_reviewer_re_eval",
        "bundle_stage_finalize",
        "publication_gate_blocker",
        "route_back_same_line",
    }:
        return None
    if _non_empty_text(_mapping_copy(payload.get("study_macro_state")).get("writer_state")) == "live":
        return None
    intervention = _mapping_copy(payload.get("intervention_lane"))
    next_work_unit = _mapping_copy(transition.get("next_work_unit"))
    return (
        _non_empty_text(intervention.get("route_summary"))
        or _non_empty_text(intervention.get("summary"))
        or _route_repair_summary(_domain_transition_route_repair(payload))
        or _non_empty_text(next_work_unit.get("unit_id"))
    )


def current_gate_clearing_eval_ids(
    *, status: Mapping[str, Any], next_forced_delta: Mapping[str, Any] | None = None
) -> list[str]:
    values: list[object] = []
    transition = _mapping_copy(status.get("domain_transition"))
    completion = _mapping_copy(transition.get("completion_receipt_consumption"))
    values.extend((completion.get("eval_id"), completion.get("source_eval_id")))
    values.append(_mapping_copy(completion.get("owner_route_currentness_basis")).get("source_eval_id"))
    values.append(_mapping_copy(transition.get("source_refs")).get("source_eval_id"))
    if next_forced_delta is not None:
        delta = _mapping_copy(next_forced_delta)
        owner_action = _mapping_copy(delta.get("owner_action"))
        ticket_refs = _mapping_copy(_mapping_copy(delta.get("current_owner_ticket")).get("source_refs"))
        values.extend(
            (
                delta.get("eval_id"),
                delta.get("source_eval_id"),
                owner_action.get("eval_id"),
                owner_action.get("source_eval_id"),
                ticket_refs.get("source_eval_id"),
            )
        )
    return list(dict.fromkeys(text for value in values if (text := _non_empty_text(value))))


__all__ = [
    "current_gate_clearing_eval_ids",
    "current_redrive_top_level_next_action",
    "refresh_existing_projection_batch_followthroughs",
    "refresh_existing_projection_current_owner_surfaces",
    "refresh_existing_projection_repair_progress",
    "refresh_existing_projection_user_visible_status",
]
