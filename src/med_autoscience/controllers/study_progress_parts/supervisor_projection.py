from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import autonomy_ai_doctor
from med_autoscience.profiles import WorkspaceProfile

from .shared_base import _mapping_copy, _non_empty_text, _read_json_object


def read_ai_repair_lifecycle(*, study_root: Path) -> dict[str, Any] | None:
    try:
        from med_autoscience.controllers.runtime_watch_parts import autonomy_repair

        return autonomy_repair.read_ai_repair_lifecycle(study_root=study_root)
    except Exception:
        return None


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
    control_plane = _mapping_copy(status_payload.get("control_plane_snapshot"))
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


def portable_supervisor_hourly_path(*, profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "artifacts" / "supervision" / "hourly" / "latest.json"


def _copy_mapping_keys(value: object, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {key: value[key] for key in keys if key in value}


def portable_supervisor_study_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    hourly_path = portable_supervisor_hourly_path(profile=profile)
    payload = _read_json_object(hourly_path)
    if payload is None:
        return None
    matching = None
    for item in payload.get("studies") or []:
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id:
            matching = dict(item)
            break
    if matching is None:
        return None
    action_queue = [
        _copy_mapping_keys(item, ("action_type", "summary", "status", "owner", "surface", "action_id"))
        for item in matching.get("action_queue") or []
        if isinstance(item, Mapping)
    ]
    why_not_applied = [
        text
        for item in matching.get("why_not_applied") or []
        if (text := _non_empty_text(item)) is not None
    ]
    return {
        "surface_kind": "portable_supervisor_study_queue_dashboard",
        "read_model": "workspace_hourly_supervision_projection",
        "authority": "observability_only",
        "source_path": str(hourly_path),
        "generated_at": _non_empty_text(payload.get("generated_at")),
        "study_id": study_id,
        "quest_status": _non_empty_text(matching.get("quest_status")),
        "active_run_id": _non_empty_text(matching.get("active_run_id")),
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
        "action_queue": [item for item in action_queue if item],
        "why_not_applied": why_not_applied,
        "next_owner": _non_empty_text(matching.get("next_owner")),
        "external_supervisor_required": bool(matching.get("external_supervisor_required")),
        "blocked_reason": _non_empty_text(matching.get("blocked_reason")),
    }
