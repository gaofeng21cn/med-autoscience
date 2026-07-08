from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import autonomy_ai_doctor
from med_autoscience.controllers.autonomy_repair_readback import (
    read_ai_repair_lifecycle as _read_ai_repair_lifecycle,
)

from ..shared_base import _mapping_copy, _non_empty_text, _read_json_object

def read_ai_repair_lifecycle(*, study_root: Path) -> dict[str, Any] | None:
    return _read_ai_repair_lifecycle(study_root=study_root)


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
