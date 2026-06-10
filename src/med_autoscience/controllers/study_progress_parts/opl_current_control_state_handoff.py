from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import autonomy_ai_doctor
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.missing_refs_typed_closeout import (
    is_blocked_typed_closeout,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile

from .opl_current_control_state_handoff_values import (
    _copy_mapping_keys,
    _first_present_mapping_value,
    _observability_mapping,
    _owner_route_projection,
    _stage_progress_log_mapping,
    _string_list,
)
from .opl_current_control_state_terminal_logs import (
    _latest_terminal_stage_log_projection,
    _latest_typed_default_executor_closeout_projection,
    _typed_closeout_supersedes_terminal,
)
from .shared_base import _mapping_copy, _non_empty_text, _read_json_object

LIVE_ATTEMPT_HANDOFF_KEYS = (
    "active_run_id",
    "active_stage_attempt_id",
    "active_workflow_id",
    "running_provider_attempt",
)
LIVE_ATTEMPT_SUPERSEDED_BLOCKERS = frozenset(
    {
        "live_worker_requires_worker_running",
        "managed_runtime_audit_unhealthy",
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "quest_waiting_opl_runtime_owner_route",
        "repair_progress_ai_reviewer_recheck_required",
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
    }
)
LIVE_ATTEMPT_SUPERSEDED_NEXT_OWNERS = frozenset(
    {
        "external_supervisor",
        "one-person-lab",
    }
)
TERMINAL_STAGE_LOG_STATUSES = frozenset(
    {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "failed",
        "terminal",
        "typed_blocked",
    }
)


def _work_unit_identity(value: object) -> str | None:
    if isinstance(value, Mapping):
        return (
            _non_empty_text(value.get("unit_id"))
            or _non_empty_text(value.get("work_unit_id"))
            or _non_empty_text(value.get("id"))
            or _non_empty_text(value.get("ref"))
        )
    return _non_empty_text(value)


def read_ai_repair_lifecycle(*, study_root: Path) -> dict[str, Any] | None:
    try:
        from med_autoscience.controllers.domain_health_diagnostic_parts import autonomy_repair

        return autonomy_repair.read_ai_repair_lifecycle(study_root=study_root)
    except Exception:
        return None


def current_status_suppresses_ai_repair_lifecycle(status_payload: Mapping[str, Any]) -> bool:
    reason = _non_empty_text(status_payload.get("reason"))
    next_route = _mapping_copy(status_payload.get("controller_work_unit_next_route"))
    return (
        reason == "controller_work_unit_evidence_adopted"
        and _non_empty_text(next_route.get("owner")) == "publication_gate"
        and next_route.get("runtime_relaunch_required") is False
    )


def current_status_publication_gate_stationary(status_payload: Mapping[str, Any]) -> bool:
    return current_status_suppresses_ai_repair_lifecycle(status_payload)


def _projection_string_items(value: object) -> set[str]:
    if isinstance(value, str):
        text = value.strip()
        return {text} if text else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _non_empty_text(item)) is not None}


def build_readonly_ai_repair_lifecycle_projection(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    try:
        repair_path = autonomy_ai_doctor.repair_actions_root(study_root=study_root) / "latest.json"
        repair_payload = _read_json_object(repair_path)
    except Exception:
        return None
    if not isinstance(repair_payload, dict) or _non_empty_text(repair_payload.get("state")) != "ready_for_repair":
        return None
    actions = repair_payload.get("actions")
    if not isinstance(actions, list):
        return None
    top_action = next((dict(item) for item in actions if isinstance(item, Mapping)), None)
    if top_action is None:
        return None
    control_plane = _mapping_copy(status_payload.get("authority_snapshot"))
    dispatch_gate = _mapping_copy(control_plane.get("dispatch_gate"))
    route_authorization = _mapping_copy(control_plane.get("route_authorization"))
    runtime_health = _mapping_copy(status_payload.get("runtime_health_snapshot"))
    blocking_reasons = {
        *_projection_string_items(control_plane.get("blocking_reasons")),
        *_projection_string_items(dispatch_gate.get("blocking_reasons")),
        *_projection_string_items(runtime_health.get("blocking_reasons")),
    }
    runtime_blocked = (
        route_authorization.get("runtime_recovery_allowed") is False
        or _non_empty_text(dispatch_gate.get("state")) == "blocked"
        or "runtime_recovery_retry_budget_exhausted" in blocking_reasons
        or _non_empty_text(runtime_health.get("attempt_state")) == "escalated"
        or runtime_health.get("retry_budget_remaining") == 0
    )
    if runtime_blocked:
        blocked_reason = "runtime_recovery_not_authorized"
        next_owner = "external_supervisor"
        external_supervisor_required = True
        state = "external_supervisor_required"
    else:
        blocked_reason = "controller_repair_authorization_missing"
        next_owner = "mas_controller"
        external_supervisor_required = False
        state = "blocked"
    return {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": _non_empty_text(repair_payload.get("study_id"))
        or _non_empty_text(status_payload.get("study_id")),
        "quest_id": _non_empty_text(repair_payload.get("quest_id"))
        or _non_empty_text(status_payload.get("quest_id")),
        "state": state,
        "top_action": top_action,
        "auto_apply_allowed": bool(top_action.get("auto_apply_allowed")),
        "last_apply_attempt_at": None,
        "applied_at": None,
        "blocked_reason": blocked_reason,
        "next_owner": next_owner,
        "external_supervisor_required": external_supervisor_required,
        "quality_gate_relaxation_allowed": False,
        "projection_only": True,
        "refs": {"repair_action_path": str(repair_path)},
    }


def opl_current_control_state_handoff_path(*, profile: WorkspaceProfile) -> Path:
    return (
        build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )



def _opl_current_control_state_mode_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    scheduler_contract = _mapping_copy(payload.get("scheduler_contract"))
    developer_supervisor = _mapping_copy(payload.get("developer_supervisor"))
    developer_supervisor_mode = _mapping_copy(payload.get("developer_supervisor_mode"))
    supervisor_mode = _mapping_copy(payload.get("supervisor_mode"))
    sources = (developer_supervisor, developer_supervisor_mode, supervisor_mode, scheduler_contract, payload)
    projection: dict[str, Any] = {}
    text_fields = (
        "mode",
        "mode_label",
        "scheduler_owner",
    )
    for key in text_fields:
        text = _non_empty_text(_first_present_mapping_value(sources, key))
        if text is not None:
            projection[key] = text
    for key in ("codex_app_heartbeat_required", "safe_actions_enabled", "repo_level_repair_authority"):
        for source in sources:
            if key in source:
                projection[key] = bool(source[key])
                break
    github_user_gate = _first_present_mapping_value(sources, "github_user_gate")
    if isinstance(github_user_gate, Mapping):
        projection["github_user_gate"] = dict(github_user_gate)
    else:
        text = _non_empty_text(github_user_gate)
        if text is not None:
            projection["github_user_gate"] = text
    authority_gate = _first_present_mapping_value(sources, "authority_gate")
    if isinstance(authority_gate, Mapping):
        projection["authority_gate"] = dict(authority_gate)
    else:
        text = _non_empty_text(authority_gate)
        if text is not None:
            projection["authority_gate"] = text
    if "safe_actions_enabled" not in projection and "apply_safe_actions" in payload:
        projection["safe_actions_enabled"] = bool(payload.get("apply_safe_actions"))
    return projection


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
    latest_typed_closeout = _latest_typed_default_executor_closeout_projection(
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
    if matching is None:
        if latest_terminal_stage_log is None and latest_typed_closeout is None:
            return None
        return _closeout_only_study_handoff_projection(
            handoff_path=handoff_path,
            latest_terminal_stage_log=latest_terminal_stage_log,
            latest_typed_closeout=latest_typed_closeout,
            study_id=study_id,
            payload=payload,
        )
    action_queue = [
        {
            **_copy_mapping_keys(
                item,
                (
                    "action_type",
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
                ),
            ),
            "source": "opl_current_control_state_action_queue",
        }
        for item in matching.get("action_queue") or []
        if isinstance(item, Mapping)
    ]
    why_not_applied = _string_list(matching.get("why_not_applied"))
    matching_terminal_stage_log = _observability_mapping(matching.get("latest_terminal_stage_log"))
    projection = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": "observability_only",
        "source_path": str(handoff_path),
        "generated_at": _non_empty_text(payload.get("generated_at")),
        "study_id": study_id,
        "quest_status": _non_empty_text(matching.get("quest_status")),
        "active_run_id": _non_empty_text(matching.get("active_run_id")),
        "active_stage_attempt_id": _non_empty_text(matching.get("active_stage_attempt_id")),
        "active_workflow_id": _non_empty_text(matching.get("active_workflow_id")),
        "running_provider_attempt": (
            bool(matching.get("running_provider_attempt"))
            if "running_provider_attempt" in matching
            else False
        ),
        "runtime_owner": "one-person-lab" if matching.get("running_provider_attempt") is True else None,
        "provider_attempt_owner": "one-person-lab" if matching.get("running_provider_attempt") is True else None,
        "queue_owner": "one-person-lab" if matching.get("running_provider_attempt") is True else None,
        "runtime_health": _copy_mapping_keys(
            matching.get("runtime_health"),
            ("health_status", "runtime_liveness_status", "summary", "blocked_reason"),
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
    if _typed_closeout_supersedes_terminal(
        typed_closeout=latest_typed_closeout,
        terminal_stage_log=latest_terminal_stage_log or matching_terminal_stage_log,
    ):
        typed_closeout = _observability_mapping(latest_typed_closeout)
        projection["blocked_reason"] = _non_empty_text(typed_closeout.get("blocked_reason"))
        projection["next_owner"] = _non_empty_text(typed_closeout.get("next_owner")) or projection["next_owner"]
        projection["latest_typed_default_executor_closeout"] = typed_closeout
        projection = _apply_typed_default_executor_closeout_to_handoff(projection)
    if latest_terminal_stage_log is not None:
        projection["latest_terminal_stage_log"] = latest_terminal_stage_log
    elif matching_terminal_stage_log:
        projection["latest_terminal_stage_log"] = matching_terminal_stage_log
    projection.update(_opl_current_control_state_mode_fields(payload))
    return _apply_matching_terminal_closeout_to_handoff(projection)


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
        projection["latest_typed_default_executor_closeout"] = dict(typed_closeout)
        projection = _apply_typed_default_executor_closeout_to_handoff(projection)
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
        ("health_status", "runtime_liveness_status", "summary", "blocked_reason"),
    )
    return {
        "surface_kind": "opl_current_control_state_provider_attempt_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": _non_empty_text(runtime_liveness_audit.get("authority")) or "observability_only",
        "source_path": source_path,
        "generated_at": _non_empty_text(runtime_liveness_audit.get("handoff_generated_at")),
        "study_id": study_id,
        "quest_status": None,
        "active_run_id": _non_empty_text(runtime_liveness_audit.get("active_run_id")),
        "active_stage_attempt_id": _non_empty_text(runtime_liveness_audit.get("active_stage_attempt_id")),
        "active_workflow_id": _non_empty_text(runtime_liveness_audit.get("active_workflow_id")),
        "running_provider_attempt": bool(runtime_liveness_audit.get("running_provider_attempt")),
        "runtime_owner": "one-person-lab" if runtime_liveness_audit.get("running_provider_attempt") is True else None,
        "provider_attempt_owner": "one-person-lab" if runtime_liveness_audit.get("running_provider_attempt") is True else None,
        "queue_owner": "one-person-lab" if runtime_liveness_audit.get("running_provider_attempt") is True else None,
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
    return _apply_matching_terminal_closeout_to_handoff(merged)


def _apply_matching_terminal_closeout_to_handoff(projection: dict[str, Any]) -> dict[str, Any]:
    if not _handoff_has_matching_terminal_closeout(projection):
        return projection
    updated = dict(projection)
    terminal = _observability_mapping(updated.get("latest_terminal_stage_log"))
    updated["running_provider_attempt"] = False
    updated["runtime_owner"] = None
    updated["provider_attempt_owner"] = None
    updated["queue_owner"] = None
    updated["active_run_id"] = None
    updated["active_workflow_id"] = None
    updated["active_stage_attempt_id"] = (
        _non_empty_text(terminal.get("stage_attempt_id"))
        or _non_empty_text(updated.get("active_stage_attempt_id"))
    )
    runtime_health = _observability_mapping(updated.get("runtime_health"))
    if runtime_health:
        runtime_health["runtime_liveness_status"] = "terminal"
        runtime_health["health_status"] = "terminal"
        updated["runtime_health"] = runtime_health
    return _apply_terminal_closeout_owner_answer_gate(updated)


def _apply_terminal_closeout_owner_answer_gate(projection: dict[str, Any]) -> dict[str, Any]:
    terminal = _observability_mapping(projection.get("latest_terminal_stage_log"))
    if not terminal or _terminal_closeout_has_owner_answer(terminal, projection):
        return projection
    action_queue = [dict(item) for item in projection.get("action_queue") or [] if isinstance(item, Mapping)]
    matching_actions = [
        item
        for item in action_queue
        if _terminal_closeout_matches_handoff_action(terminal=terminal, action=item)
    ]
    if action_queue and not matching_actions:
        return projection
    updated = dict(projection)
    blocker = _terminal_closeout_owner_answer_blocker(
        terminal=terminal,
        matching_action=matching_actions[0] if matching_actions else None,
    )
    updated["typed_blocker"] = blocker
    updated["blocked_reason"] = blocker["blocker_id"]
    updated["next_owner"] = blocker["owner"]
    updated["external_supervisor_required"] = True
    why_not_applied = _string_list(updated.get("why_not_applied"))
    if blocker["blocker_id"] not in why_not_applied:
        why_not_applied.append(blocker["blocker_id"])
    updated["why_not_applied"] = why_not_applied
    if matching_actions:
        source_ref = _non_empty_text(terminal.get("record_path")) or _non_empty_text(terminal.get("source_path"))
        updated["consumed_action_queue"] = [
            {
                **dict(item),
                "consumption": {
                    **_observability_mapping(item.get("consumption")),
                    "state": "blocked_by_terminal_closeout_missing_owner_answer",
                    "typed_blocker_ref": source_ref,
                },
            }
            for item in matching_actions
        ]
        updated["action_queue"] = [
            dict(item)
            for item in action_queue
            if item not in matching_actions
        ]
    return updated


def _terminal_closeout_has_owner_answer(
    terminal: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> bool:
    if _observability_mapping(projection.get("latest_typed_default_executor_closeout")):
        return True
    if _observability_mapping(projection.get("typed_blocker")):
        return True
    if _observability_mapping(terminal.get("typed_blocker")):
        return True
    if _string_list(terminal.get("typed_blocker_refs")) or _string_list(terminal.get("owner_receipt_refs")):
        return True
    paper_stage_log = _observability_mapping(terminal.get("paper_stage_log"))
    if _string_list(paper_stage_log.get("changed_paper_surfaces")):
        return True
    outcome = _non_empty_text(paper_stage_log.get("outcome"))
    return outcome in {
        "typed_blocker",
        "blocked_with_domain_typed_blocker",
        "owner_receipt",
        "owner_receipt_recorded",
        "handoff_ready",
        "next_handoff",
    }


def _terminal_closeout_matches_handoff_action(
    *,
    terminal: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    terminal_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    action_attempt_id = _non_empty_text(action.get("stage_attempt_id")) or _non_empty_text(
        action.get("active_stage_attempt_id")
    )
    if terminal_attempt_id and action_attempt_id:
        return terminal_attempt_id == action_attempt_id
    terminal_action_type = _non_empty_text(terminal.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    if terminal_action_type and action_type and terminal_action_type != action_type:
        return False
    terminal_work_unit = _work_unit_identity(terminal.get("work_unit_id")) or _work_unit_identity(
        terminal.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    if terminal_work_unit and action_work_unit:
        return terminal_work_unit == action_work_unit
    return terminal_action_type is not None and terminal_action_type == action_type


def _terminal_closeout_owner_answer_blocker(
    *,
    terminal: Mapping[str, Any],
    matching_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    action = _observability_mapping(matching_action)
    source_ref = _non_empty_text(terminal.get("record_path")) or _non_empty_text(terminal.get("source_path"))
    blocker = {
        "blocker_id": "terminal_closeout_owner_answer_required",
        "blocker_type": "terminal_closeout_owner_answer_required",
        "owner": "one-person-lab",
        "summary": (
            "Terminal provider closeout must include a MAS owner receipt, typed blocker, or next handoff "
            "before the current work unit can continue."
        ),
        "required_input": "MAS owner receipt, typed blocker, or next handoff",
        "stage_attempt_id": _non_empty_text(terminal.get("stage_attempt_id")),
        "action_type": _non_empty_text(terminal.get("action_type")) or _non_empty_text(action.get("action_type")),
        "work_unit_id": _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
            action.get("next_work_unit")
        ),
        "work_unit_fingerprint": _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "action_fingerprint": _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "source_ref": source_ref,
        "typed_blocker_ref": source_ref,
        "closeout_refs": _string_list(terminal.get("closeout_refs")),
    }
    return {key: value for key, value in blocker.items() if value not in (None, "", [], {})}


def _apply_typed_default_executor_closeout_to_handoff(
    projection: dict[str, Any],
) -> dict[str, Any]:
    typed_closeout = _observability_mapping(projection.get("latest_typed_default_executor_closeout"))
    if not typed_closeout:
        return projection
    matching_actions = [
        item
        for item in projection.get("action_queue") or []
        if isinstance(item, Mapping)
        and _typed_closeout_matches_handoff_action(typed_closeout=typed_closeout, action=item)
    ]
    if projection.get("action_queue") and not matching_actions:
        return projection
    typed_blocker = _typed_closeout_blocker_projection(
        typed_closeout=typed_closeout,
        matching_action=matching_actions[0] if matching_actions else None,
    )
    if not typed_blocker:
        return projection
    updated = dict(projection)
    if matching_actions:
        consumed = [
            {
                **dict(item),
                "consumption": {
                    **_observability_mapping(item.get("consumption")),
                    "state": "consumed_by_typed_default_executor_closeout",
                    "typed_blocker_ref": _non_empty_text(typed_closeout.get("receipt_ref"))
                    or _non_empty_text(typed_closeout.get("source_path")),
                },
            }
            for item in matching_actions
        ]
        updated["consumed_action_queue"] = consumed
        updated["action_queue"] = [
            dict(item)
            for item in updated.get("action_queue") or []
            if isinstance(item, Mapping) and item not in matching_actions
        ]
    updated["typed_blocker"] = typed_blocker
    updated["blocked_reason"] = _non_empty_text(typed_blocker.get("blocker_type")) or updated.get("blocked_reason")
    updated["next_owner"] = _non_empty_text(typed_blocker.get("owner")) or updated.get("next_owner")
    updated["running_provider_attempt"] = False
    updated["runtime_owner"] = None
    updated["provider_attempt_owner"] = None
    updated["queue_owner"] = None
    return updated


def _typed_closeout_matches_handoff_action(
    *,
    typed_closeout: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    closeout_attempt_id = _non_empty_text(typed_closeout.get("execution_id")) or _non_empty_text(
        typed_closeout.get("stage_attempt_id")
    )
    action_attempt_id = _non_empty_text(action.get("stage_attempt_id")) or _non_empty_text(
        action.get("active_stage_attempt_id")
    )
    if closeout_attempt_id and action_attempt_id:
        return closeout_attempt_id == action_attempt_id
    closeout_fingerprints = _identity_values(
        typed_closeout,
        ("work_unit_fingerprint", "action_fingerprint", "fingerprint"),
    )
    action_fingerprints = _identity_values(
        action,
        ("work_unit_fingerprint", "action_fingerprint", "fingerprint"),
    )
    if closeout_fingerprints and action_fingerprints:
        return bool(closeout_fingerprints.intersection(action_fingerprints))
    closeout_work_unit = _work_unit_identity(typed_closeout.get("work_unit_id")) or _work_unit_identity(
        typed_closeout.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    closeout_action_type = _non_empty_text(typed_closeout.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    return (
        closeout_work_unit is not None
        and action_work_unit == closeout_work_unit
        and closeout_action_type is not None
        and action_type == closeout_action_type
    )


def _identity_values(value: Mapping[str, Any], keys: tuple[str, ...]) -> set[str]:
    return {
        text
        for key in keys
        if (text := _non_empty_text(value.get(key))) is not None
    }


def _typed_closeout_blocker_projection(
    *,
    typed_closeout: Mapping[str, Any],
    matching_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    embedded = _observability_mapping(typed_closeout.get("typed_blocker"))
    blocked_reason = (
        _non_empty_text(embedded.get("blocker_type"))
        or _non_empty_text(embedded.get("blocker_id"))
        or _non_empty_text(embedded.get("reason"))
        or _non_empty_text(embedded.get("blocked_reason"))
        or _non_empty_text(typed_closeout.get("blocked_reason"))
    )
    if blocked_reason is None:
        return {}
    owner = (
        _non_empty_text(embedded.get("owner"))
        or _non_empty_text(embedded.get("next_owner"))
        or _non_empty_text(embedded.get("phase_owner"))
        or _non_empty_text(typed_closeout.get("next_owner"))
    )
    action = _observability_mapping(matching_action)
    blocker = {
        **embedded,
        "blocker_type": blocked_reason,
        "blocked_reason": blocked_reason,
        "owner": owner or "med-autoscience",
        "action_type": _non_empty_text(typed_closeout.get("action_type"))
        or _non_empty_text(action.get("action_type")),
        "work_unit_id": _work_unit_identity(typed_closeout.get("work_unit_id"))
        or _work_unit_identity(action.get("work_unit_id"))
        or _work_unit_identity(action.get("next_work_unit")),
        "work_unit_fingerprint": _non_empty_text(typed_closeout.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "action_fingerprint": _non_empty_text(typed_closeout.get("action_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "source_ref": _non_empty_text(typed_closeout.get("receipt_ref"))
        or _non_empty_text(typed_closeout.get("source_path")),
        "typed_blocker_ref": _non_empty_text(typed_closeout.get("receipt_ref"))
        or _non_empty_text(typed_closeout.get("source_path")),
        "closeout_refs": _string_list(typed_closeout.get("closeout_refs")),
    }
    owner_route = _observability_mapping(typed_closeout.get("owner_route"))
    source_refs = _observability_mapping(owner_route.get("source_refs"))
    currentness_basis = _observability_mapping(source_refs.get("owner_route_currentness_basis"))
    if currentness_basis:
        blocker["currentness_basis"] = currentness_basis
    return {key: value for key, value in blocker.items() if value not in (None, "", [], {})}


def _handoff_has_matching_terminal_closeout(handoff: Mapping[str, Any]) -> bool:
    terminal = _observability_mapping(handoff.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = _handoff_stage_attempt_id(handoff)
    terminal_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    status = _non_empty_text(terminal.get("status"))
    if status in TERMINAL_STAGE_LOG_STATUSES:
        return True
    return (
        _non_empty_text(terminal.get("source_path")) is not None
        and _non_empty_text(terminal.get("record_path")) is not None
    )


def _handoff_stage_attempt_id(handoff: Mapping[str, Any]) -> str | None:
    if text := _non_empty_text(handoff.get("active_stage_attempt_id")):
        return text
    return _stage_attempt_id_from_active_run_id(handoff.get("active_run_id"))


def _stage_attempt_id_from_active_run_id(value: object) -> str | None:
    active_run_id = _non_empty_text(value)
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


def _handoff_live_attempt_identity_stale(
    *,
    handoff: Mapping[str, Any],
    live_attempt_handoff: Mapping[str, Any],
) -> bool:
    live_stage_attempt_id = _non_empty_text(live_attempt_handoff.get("active_stage_attempt_id"))
    if live_stage_attempt_id is None:
        return False
    handoff_stage_attempt_id = _non_empty_text(handoff.get("active_stage_attempt_id"))
    if handoff_stage_attempt_id in {None, live_stage_attempt_id}:
        return False
    handoff_run_attempt_id = _stage_attempt_id_from_active_run_id(handoff.get("active_run_id"))
    live_run_attempt_id = _stage_attempt_id_from_active_run_id(live_attempt_handoff.get("active_run_id"))
    return live_stage_attempt_id in {handoff_run_attempt_id, live_run_attempt_id}


def _live_attempt_supersedes_handoff_blocker(handoff: Mapping[str, Any]) -> bool:
    blocked_reason = _non_empty_text(handoff.get("blocked_reason"))
    if blocked_reason in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS:
        return True
    why_not_applied = set(_string_list(handoff.get("why_not_applied")))
    if why_not_applied.intersection(LIVE_ATTEMPT_SUPERSEDED_BLOCKERS):
        return True
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    runtime_blockers = set(_string_list(runtime_health.get("blocking_reasons")))
    return bool(runtime_blockers.intersection(LIVE_ATTEMPT_SUPERSEDED_BLOCKERS))
