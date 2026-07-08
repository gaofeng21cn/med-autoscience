from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.opl_transition_readback import (
    provider_admission_opl_transition_readback,
)
from med_autoscience.controllers.paper_mission_owner_surface.opl_provider_attempts import (
    terminal_provider_attempt_closeout_for_study,
)
from med_autoscience.controllers.study_transition_receipt_consumption.owner_callable_candidates import (
    owner_callable_receipt_candidates,
)
from med_autoscience.controllers.study_transition_receipt_consumption.missing_refs_typed_closeout import (
    is_blocked_typed_closeout,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile

from ..opl_current_control_state_handoff_values import (
    _copy_mapping_keys,
    _current_control_currentness_fields,
    _first_present_mapping_value,
    _observability_mapping,
    _owner_route_projection,
    _stage_progress_log_mapping,
    _strict_running_provider_attempt,
    _string_list,
    _work_unit_identity,
)
from ..opl_current_control_state_handoff_identity import bind_live_attempt_to_handoff_identity
from .lifecycle import (
    build_readonly_ai_repair_lifecycle_projection,
    current_status_publication_gate_stationary,
    current_status_suppresses_ai_repair_lifecycle,
    read_ai_repair_lifecycle,
)
from .mode_fields import (
    _opl_current_control_state_mode_fields,
)
from .non_advancing_readback import (
    copy_opl_transition_readback_fields as _copy_opl_transition_readback_fields,
)
from .provider_readbacks import (
    apply_action_queue_provider_readbacks_to_handoff as _apply_action_queue_provider_readbacks_to_handoff,
    apply_terminal_consumed_readback_to_handoff as _apply_terminal_consumed_readback_to_handoff,
    apply_top_level_provider_admissions_to_handoff as _apply_top_level_provider_admissions_to_handoff,
    apply_top_level_transition_requests_to_handoff as _apply_top_level_transition_requests_to_handoff,
    current_control_provider_admission_candidates as _current_control_provider_admission_candidates,
    latest_provider_admission_terminal_consumed_readback_for_study as _latest_provider_admission_terminal_consumed_readback_for_study,
    terminal_consumption_candidate_can_anchor_terminal_probe as _terminal_consumption_candidate_can_anchor_terminal_probe,
)
from .terminal_closeout import (
    LIVE_ATTEMPT_SUPERSEDED_BLOCKERS,
    LIVE_ATTEMPT_SUPERSEDED_NEXT_OWNERS,
    _action_with_handoff_packet_readback,
    _apply_matching_terminal_closeout_to_handoff,
    _apply_typed_owner_callable_adapter_closeout_to_handoff,
    _handoff_candidate_list,
    _handoff_has_complete_current_transition_readback,
    _handoff_live_attempt_identity_stale,
    _live_attempt_supersedes_handoff_blocker,
    _newer_typed_closeout_blocks_stale_current_control,
    _provider_admission_terminal_closeout_consumed,
)
from .terminal_closeout_identity import (
    _terminal_closeout_matches_handoff_action,
    _terminal_matching_handoff_candidates,
)
from .transition_readbacks import (
    _matching_with_live_log_transition_readbacks,
    _top_level_provider_admission_candidates_for_study,
    _top_level_transition_request_candidates_for_study,
    _transition_candidates_with_live_log_readback,
    _transition_request_identity_key,
)
from ..opl_current_control_state_terminal_logs import (
    _latest_terminal_stage_log_projection,
    _latest_typed_owner_callable_closeout_projection,
    _typed_closeout_supersedes_terminal,
)
from ..shared_base import _mapping_copy, _non_empty_text, _read_json_object

LIVE_ATTEMPT_HANDOFF_KEYS = (
    "active_run_id",
    "active_stage_attempt_id",
    "active_workflow_id",
    "running_provider_attempt",
)
ATTEMPT_IDENTITY_KEYS = (
    "action_type",
    "work_unit_id",
    "next_work_unit",
    "work_unit_fingerprint",
    "action_fingerprint",
    "lineage_ref",
)



def opl_current_control_state_handoff_path(*, profile: WorkspaceProfile) -> Path:
    return (
        build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )




def opl_current_control_state_study_handoff_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    handoff_path = opl_current_control_state_handoff_path(profile=profile)
    payload = _read_json_object(handoff_path)
    latest_terminal_stage_log = _latest_terminal_stage_log_projection(
        profile=profile,
        study_id=study_id,
    )
    latest_typed_closeout = _latest_typed_owner_callable_closeout_projection(
        profile=profile,
        study_id=study_id,
    )
    if payload is None:
        if latest_terminal_stage_log is None and latest_typed_closeout is None:
            return None
        return _closeout_only_study_handoff_projection(
            handoff_path=handoff_path,
            latest_terminal_stage_log=latest_terminal_stage_log,
            latest_typed_closeout=latest_typed_closeout,
            study_id=study_id,
        )
    matching = None
    for item in payload.get("studies") or []:
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id:
            matching = dict(item)
            break
    matching_top_level_provider_admissions = _top_level_provider_admission_candidates_for_study(
        payload,
        study_id=study_id,
    )
    matching_provider_admissions = [
        dict(item)
        for item in matching.get("provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ] if matching is not None else []
    matching_top_level_transition_requests = _top_level_transition_request_candidates_for_study(
        payload,
        study_id=study_id,
    )
    matching_top_level_transition_requests = _transition_candidates_with_live_log_readback(
        profile=profile,
        candidates=matching_top_level_transition_requests,
    )
    latest_opl_terminal_closeout = _latest_opl_terminal_provider_attempt_closeout_projection(
        profile=profile,
        study_id=study_id,
        payload=payload,
        matching=matching,
        matching_top_level_provider_admissions=matching_top_level_provider_admissions,
        matching_top_level_transition_requests=matching_top_level_transition_requests,
    )
    if latest_opl_terminal_closeout is not None:
        latest_terminal_stage_log = latest_opl_terminal_closeout
    latest_terminal_consumed_readback = _latest_provider_admission_terminal_consumed_readback_for_study(
        payload,
        study_id=study_id,
    )
    if matching is None:
        if (
            latest_terminal_stage_log is None
            and latest_typed_closeout is None
            and not latest_terminal_consumed_readback
            and not matching_top_level_provider_admissions
            and not matching_top_level_transition_requests
        ):
            return None
        projection = _closeout_only_study_handoff_projection(
            handoff_path=handoff_path,
            latest_terminal_stage_log=latest_terminal_stage_log,
            latest_typed_closeout=latest_typed_closeout,
            study_id=study_id,
            payload=payload,
        )
        if matching_top_level_provider_admissions:
            projection = _apply_top_level_provider_admissions_to_handoff(
                projection,
                matching_top_level_provider_admissions,
            )
        if matching_top_level_transition_requests:
            projection = _apply_top_level_transition_requests_to_handoff(
                projection,
                matching_top_level_transition_requests,
            )
        if latest_terminal_consumed_readback:
            projection = _apply_terminal_consumed_readback_to_handoff(
                projection,
                latest_terminal_consumed_readback,
                apply_matching_terminal_closeout_to_handoff=_apply_matching_terminal_closeout_to_handoff,
            )
        return projection
    matching = _matching_with_live_log_transition_readbacks(
        profile=profile,
        matching=matching,
    )
    action_queue = [
        {
            **_copy_mapping_keys(
                item,
                (
                    "action_type",
                    "study_id",
                    "quest_id",
                    "summary",
                    "status",
                    "owner",
                    "surface",
                    "action_id",
                    "fingerprint",
                    "action_fingerprint",
                    "work_unit_fingerprint",
                    "authority",
                    "queue_age_hours",
                    "queued_first_seen_at",
                    "repeat_fingerprint",
                    "next_work_unit",
                    "controller_work_unit_id",
                    "work_unit_id",
                    "source_eval_id",
                    "source_fingerprint",
                    "owner_pickup",
                    "consumption",
                    "route_identity_key",
                    "attempt_idempotency_key",
                    "idempotency_key",
                    "provider_admission_identity",
                    "dispatch_ref",
                    "dispatch_path",
                    "stage_packet_ref",
                    "stage_packet_refs",
                    "checkpoint_refs",
                    "source_refs",
                    "opl_domain_progress_transition_live_readback",
                    "opl_domain_progress_transition_runtime_live_readback",
                    "opl_domain_progress_transition_result",
                ),
            ),
            "source": "opl_current_control_state_action_queue",
        }
        for item in matching.get("action_queue") or []
        if isinstance(item, Mapping)
    ]
    why_not_applied = _string_list(matching.get("why_not_applied"))
    matching_terminal_stage_log = _observability_mapping(matching.get("latest_terminal_stage_log"))
    active_run_id = _non_empty_text(matching.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(matching.get("active_stage_attempt_id"))
    active_workflow_id = _non_empty_text(matching.get("active_workflow_id"))
    running_provider_attempt = _strict_running_provider_attempt(
        matching,
        active_run_id=active_run_id,
        active_stage_attempt_id=active_stage_attempt_id,
        active_workflow_id=active_workflow_id,
    )
    projection = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": "observability_only",
        "source_path": str(handoff_path),
        "generated_at": _non_empty_text(payload.get("generated_at")),
        "study_id": study_id,
        "quest_status": _non_empty_text(matching.get("quest_status")),
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": running_provider_attempt,
        "runtime_owner": "one-person-lab" if running_provider_attempt else None,
        "provider_attempt_owner": "one-person-lab" if running_provider_attempt else None,
        "queue_owner": "one-person-lab" if running_provider_attempt else None,
        "action_type": _non_empty_text(matching.get("action_type")),
        "work_unit_id": _work_unit_identity(matching.get("work_unit_id")),
        "next_work_unit": _work_unit_identity(matching.get("next_work_unit")),
        "work_unit_fingerprint": _non_empty_text(matching.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(matching.get("action_fingerprint"))
        or _non_empty_text(matching.get("work_unit_fingerprint")),
        "runtime_health": _copy_mapping_keys(
            matching.get("runtime_health"),
            (
                "health_status",
                "runtime_liveness_status",
                "summary",
                "blocked_reason",
                *ATTEMPT_IDENTITY_KEYS,
            ),
        ),
        "artifact_delta": _copy_mapping_keys(
            matching.get("artifact_delta"),
            ("status", "summary", "latest_artifact_at", "latest_meaningful_delta_at"),
        ),
        "gate_specificity": _copy_mapping_keys(
            matching.get("gate_specificity"),
            ("status", "summary", "blocked_reason", "required_action"),
        ),
        "ai_reviewer_status": _copy_mapping_keys(
            matching.get("ai_reviewer_status"),
            ("status", "summary", "owner", "trace_complete", "blocked_reason"),
        ),
        "stage_progress_log": _stage_progress_log_mapping(matching.get("stage_progress_log")),
        "owner_route": _owner_route_projection(matching.get("owner_route")),
        "queue_slo": _copy_mapping_keys(
            matching.get("queue_slo"),
            (
                "max_queue_age_hours",
                "owner_pickup_overdue_count",
                "developer_supervisor_attention_required_count",
            ),
        ),
        "owner_pickup_overdue": bool(matching.get("owner_pickup_overdue")),
        "developer_supervisor_attention_required": bool(
            matching.get("developer_supervisor_attention_required")
        ),
        "action_queue": [item for item in action_queue if item],
        "why_not_applied": why_not_applied,
        "next_owner": _non_empty_text(matching.get("next_owner")),
        "external_supervisor_required": bool(matching.get("external_supervisor_required")),
        "blocked_reason": _non_empty_text(matching.get("blocked_reason")),
    }
    projection.update(_current_control_currentness_fields(matching))
    _copy_opl_transition_readback_fields(projection, matching)
    provider_admission_candidates = [
        *matching_provider_admissions,
        *matching_top_level_provider_admissions,
    ]
    if provider_admission_candidates:
        projection = _apply_top_level_provider_admissions_to_handoff(
            projection,
            provider_admission_candidates,
        )
    if matching_top_level_transition_requests:
        projection = _apply_top_level_transition_requests_to_handoff(
            projection,
            matching_top_level_transition_requests,
        )
    projection = _apply_action_queue_provider_readbacks_to_handoff(projection)
    if _typed_closeout_supersedes_terminal(
        typed_closeout=latest_typed_closeout,
        terminal_stage_log=latest_terminal_stage_log or matching_terminal_stage_log,
    ):
        typed_closeout = _observability_mapping(latest_typed_closeout)
        projection["latest_typed_owner_callable_closeout"] = typed_closeout
        if _newer_typed_closeout_blocks_stale_current_control(
            typed_closeout=typed_closeout,
            projection=projection,
            handoff_path=handoff_path,
        ):
            projection["blocked_reason"] = _non_empty_text(typed_closeout.get("blocked_reason"))
            projection["next_owner"] = _non_empty_text(typed_closeout.get("next_owner")) or projection["next_owner"]
            projection = _apply_typed_owner_callable_adapter_closeout_to_handoff(
                projection,
                allow_stale_identity_override=True,
            )
        elif not _handoff_has_complete_current_transition_readback(projection):
            projection["blocked_reason"] = _non_empty_text(typed_closeout.get("blocked_reason"))
            projection["next_owner"] = _non_empty_text(typed_closeout.get("next_owner")) or projection["next_owner"]
            projection = _apply_typed_owner_callable_adapter_closeout_to_handoff(projection)
    if latest_terminal_stage_log is not None:
        projection["latest_terminal_stage_log"] = latest_terminal_stage_log
    elif matching_terminal_stage_log:
        projection["latest_terminal_stage_log"] = matching_terminal_stage_log
    if latest_terminal_consumed_readback:
        projection = _apply_terminal_consumed_readback_to_handoff(
            projection,
            latest_terminal_consumed_readback,
            apply_matching_terminal_closeout_to_handoff=_apply_matching_terminal_closeout_to_handoff,
        )
    projection.update(_opl_current_control_state_mode_fields(payload))
    return _apply_matching_terminal_closeout_to_handoff(projection)


def _latest_opl_terminal_provider_attempt_closeout_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    payload: Mapping[str, Any],
    matching: Mapping[str, Any] | None,
    matching_top_level_provider_admissions: list[dict[str, Any]],
    matching_top_level_transition_requests: list[dict[str, Any]],
) -> dict[str, Any] | None:
    preferred_actions = _current_control_provider_admission_candidates(
        payload=payload,
        matching=matching,
        matching_top_level_provider_admissions=matching_top_level_provider_admissions,
        matching_top_level_transition_requests=matching_top_level_transition_requests,
    )
    if not preferred_actions:
        return None
    closeout = terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        timeout_seconds=8.0,
        max_inspect_count=2,
        preferred_actions=preferred_actions,
    )
    if not closeout:
        return None
    if not any(
        _terminal_closeout_matches_handoff_action(terminal=closeout, action=action)
        for action in preferred_actions
    ):
        return None
    return closeout


def refresh_handoff_with_terminal_closeout_candidates(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    handoff: Mapping[str, Any] | None,
    candidates: list[Mapping[str, Any]],
) -> dict[str, Any] | None:
    if handoff is None:
        return None
    preferred_actions = [
        dict(item)
        for item in candidates
        if isinstance(item, Mapping) and _terminal_consumption_candidate_can_anchor_terminal_probe(item)
    ]
    if not preferred_actions:
        return dict(handoff)
    closeout = terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        timeout_seconds=8.0,
        max_inspect_count=2,
        preferred_actions=preferred_actions,
    )
    if not closeout:
        closeout = _terminal_owner_callable_adapter_closeout_for_preferred_actions(
            profile=profile,
            study_id=study_id,
            preferred_actions=preferred_actions,
        )
    if not closeout:
        return dict(handoff)
    if not any(
        _terminal_closeout_matches_handoff_action(terminal=closeout, action=action)
        for action in preferred_actions
    ):
        return dict(handoff)
    refreshed = {
        **dict(handoff),
        "latest_terminal_stage_log": closeout,
        "active_stage_attempt_id": _non_empty_text(closeout.get("stage_attempt_id")),
        "active_run_id": (
            f"opl-stage-attempt://{stage_attempt_id}"
            if (stage_attempt_id := _non_empty_text(closeout.get("stage_attempt_id"))) is not None
            else None
        ),
        "transition_request_pending_count": len(preferred_actions),
        "transition_request_candidates": preferred_actions,
    }
    return _apply_matching_terminal_closeout_to_handoff(refreshed)


def _terminal_owner_callable_adapter_closeout_for_preferred_actions(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    preferred_actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    study_root = _study_root_for_owner_callable_candidates(profile=profile, study_id=study_id)
    if study_root is None:
        return None
    for execution, receipt_ref in owner_callable_receipt_candidates(
        study_root=study_root,
        allow_legacy_fallback=True,
    ):
        closeout = dict(execution)
        closeout.setdefault("receipt_ref", receipt_ref)
        closeout.setdefault("source", "mas_owner_callable_adapter_closeout")
        if any(_owner_callable_adapter_closeout_can_consume_preferred_action(closeout, action) for action in preferred_actions):
            return closeout
    return None


def _owner_callable_adapter_closeout_can_consume_preferred_action(
    closeout: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if not _terminal_closeout_matches_handoff_action(terminal=closeout, action=action):
        return False
    if (
        provider_admission_opl_transition_readback(action)
        and _non_empty_text(closeout.get("owner_receipt_ref")) is None
    ):
        return False
    return True


def _study_root_for_owner_callable_candidates(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> Path | None:
    candidates = [
        profile.studies_root / study_id,
        build_workspace_runtime_layout_for_profile(profile).workspace_root / "studies" / study_id,
        profile.workspace_root / "studies" / study_id,
    ]
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue
        if resolved.exists():
            return resolved
    return candidates[0].expanduser().resolve() if candidates else None


def _closeout_only_study_handoff_projection(
    *,
    handoff_path: Path,
    latest_terminal_stage_log: Mapping[str, Any] | None,
    latest_typed_closeout: Mapping[str, Any] | None,
    study_id: str,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_payload = _mapping_copy(payload)
    terminal_stage_log = _observability_mapping(latest_terminal_stage_log)
    typed_closeout = _observability_mapping(latest_typed_closeout)
    projection = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": "observability_only",
        "source_path": str(handoff_path),
        "generated_at": _non_empty_text(source_payload.get("generated_at"))
        or _non_empty_text(terminal_stage_log.get("generated_at")),
        "study_id": study_id,
        "quest_status": None,
        "active_run_id": None,
        "active_stage_attempt_id": _non_empty_text(terminal_stage_log.get("stage_attempt_id"))
        or _non_empty_text(typed_closeout.get("execution_id")),
        "active_workflow_id": None,
        "running_provider_attempt": False,
        "runtime_health": {},
        "artifact_delta": {},
        "gate_specificity": {},
        "ai_reviewer_status": {},
        "stage_progress_log": {},
        "owner_route": {},
        "queue_slo": {},
        "owner_pickup_overdue": False,
        "developer_supervisor_attention_required": False,
        "action_queue": [],
        "why_not_applied": [],
        "next_owner": _non_empty_text(typed_closeout.get("next_owner")),
        "external_supervisor_required": False,
        "blocked_reason": _non_empty_text(typed_closeout.get("blocked_reason"))
        or _non_empty_text(terminal_stage_log.get("typed_blocker_reason")),
    }
    if terminal_stage_log:
        projection["latest_terminal_stage_log"] = dict(terminal_stage_log)
    if typed_closeout:
        projection["latest_typed_owner_callable_closeout"] = dict(typed_closeout)
        projection = _apply_typed_owner_callable_adapter_closeout_to_handoff(projection)
    projection.update(_opl_current_control_state_mode_fields(source_payload))
    return projection


def opl_current_control_state_live_attempt_handoff_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    runtime_liveness_audit: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _non_empty_text(runtime_liveness_audit.get("source")) != "opl_current_control_state_provider_attempt":
        return None
    stage_progress_log = _stage_progress_log_mapping(runtime_liveness_audit.get("stage_progress_log"))
    source_path = _non_empty_text(runtime_liveness_audit.get("handoff_path")) or str(
        opl_current_control_state_handoff_path(profile=profile)
    )
    runtime_health = _copy_mapping_keys(
        runtime_liveness_audit.get("runtime_health"),
        (
            "health_status",
            "runtime_liveness_status",
            "summary",
            "blocked_reason",
            *ATTEMPT_IDENTITY_KEYS,
        ),
    )
    active_run_id = _non_empty_text(runtime_liveness_audit.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(runtime_liveness_audit.get("active_stage_attempt_id"))
    active_workflow_id = _non_empty_text(runtime_liveness_audit.get("active_workflow_id"))
    running_provider_attempt = _strict_running_provider_attempt(
        runtime_liveness_audit,
        active_run_id=active_run_id,
        active_stage_attempt_id=active_stage_attempt_id,
        active_workflow_id=active_workflow_id,
    )
    return {
        "surface_kind": "opl_current_control_state_provider_attempt_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": _non_empty_text(runtime_liveness_audit.get("authority")) or "observability_only",
        "source_path": source_path,
        "generated_at": _non_empty_text(runtime_liveness_audit.get("handoff_generated_at")),
        "study_id": study_id,
        "quest_status": None,
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": running_provider_attempt,
        "action_type": _non_empty_text(runtime_liveness_audit.get("action_type")),
        "work_unit_id": _work_unit_identity(runtime_liveness_audit.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(runtime_liveness_audit.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(runtime_liveness_audit.get("action_fingerprint"))
        or _non_empty_text(runtime_liveness_audit.get("work_unit_fingerprint")),
        "runtime_owner": "one-person-lab" if running_provider_attempt else None,
        "provider_attempt_owner": "one-person-lab" if running_provider_attempt else None,
        "queue_owner": "one-person-lab" if running_provider_attempt else None,
        "runtime_health": runtime_health,
        "artifact_delta": {},
        "gate_specificity": {},
        "ai_reviewer_status": {},
        "stage_progress_log": stage_progress_log,
        "queue_slo": {},
        "owner_pickup_overdue": False,
        "developer_supervisor_attention_required": False,
        "action_queue": [],
        "why_not_applied": [],
        "next_owner": "supervisor_only/live_provider_attempt",
        "external_supervisor_required": False,
        "blocked_reason": None,
    }


def merge_live_attempt_observability_into_handoff(
    *,
    handoff: dict[str, Any] | None,
    live_attempt_handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if handoff is None:
        return live_attempt_handoff
    if live_attempt_handoff is None:
        return handoff
    active_run_id = _non_empty_text(handoff.get("active_run_id"))
    live_active_run_id = _non_empty_text(live_attempt_handoff.get("active_run_id"))
    if active_run_id and live_active_run_id and active_run_id != live_active_run_id:
        return handoff
    merged = dict(handoff)
    live_attempt_running = live_attempt_handoff.get("running_provider_attempt") is True
    if live_attempt_running and _live_attempt_supersedes_handoff_blocker(merged):
        merged["external_supervisor_required"] = False
        merged["blocked_reason"] = None
        merged.pop("typed_blocker", None)
        merged["why_not_applied"] = [
            reason
            for reason in _string_list(merged.get("why_not_applied"))
            if reason not in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS
        ]
        if _non_empty_text(merged.get("next_owner")) in LIVE_ATTEMPT_SUPERSEDED_NEXT_OWNERS:
            merged["next_owner"] = _non_empty_text(live_attempt_handoff.get("next_owner"))
    for key in LIVE_ATTEMPT_HANDOFF_KEYS:
        if (
            key == "active_stage_attempt_id"
            and live_attempt_running
            and _handoff_live_attempt_identity_stale(
                handoff=merged,
                live_attempt_handoff=live_attempt_handoff,
            )
        ):
            merged[key] = live_attempt_handoff[key]
            continue
        if key not in merged or merged.get(key) in {None, "", False}:
            if key in live_attempt_handoff:
                merged[key] = live_attempt_handoff[key]
    if live_attempt_running:
        for key in ("runtime_owner", "provider_attempt_owner", "queue_owner"):
            value = _non_empty_text(live_attempt_handoff.get(key)) or "one-person-lab"
            merged[key] = value
    if not _stage_progress_log_mapping(merged.get("stage_progress_log")):
        stage_progress_log = _stage_progress_log_mapping(live_attempt_handoff.get("stage_progress_log"))
        if stage_progress_log:
            merged["stage_progress_log"] = stage_progress_log
    live_runtime_health = _copy_mapping_keys(
        live_attempt_handoff.get("runtime_health"),
        ("health_status", "runtime_liveness_status", "summary", "blocked_reason"),
    )
    if live_runtime_health and (
        live_attempt_running
        or not _copy_mapping_keys(merged.get("runtime_health"), ("health_status", "runtime_liveness_status"))
    ):
        merged["runtime_health"] = live_runtime_health
    if live_attempt_running:
        merged = bind_live_attempt_to_handoff_identity(
            handoff=merged,
            live_attempt_handoff=live_attempt_handoff,
        )
    return _apply_matching_terminal_closeout_to_handoff(merged)
