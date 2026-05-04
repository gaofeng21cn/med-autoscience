from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import autonomy_ai_doctor, study_runtime_router
from med_autoscience.profiles import WorkspaceProfile


AI_DOCTOR_REPAIR_SOURCE = "runtime_watch_ai_doctor_repair"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else None


def _write_json_object(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _latest_ai_doctor_repair_path(*, study_root: Path) -> Path:
    return autonomy_ai_doctor.repair_actions_root(study_root=study_root) / "latest.json"


def _first_ai_doctor_repair_action(repair_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if _non_empty_text(repair_payload.get("state")) != "ready_for_repair":
        return None
    if repair_payload.get("quality_gate_relaxation_allowed") is True:
        return None
    actions = repair_payload.get("actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if isinstance(action, Mapping):
            return dict(action)
    return None


def read_ready_ai_doctor_repair(*, study_root: Path) -> dict[str, Any] | None:
    repair_payload = _read_json_object(_latest_ai_doctor_repair_path(study_root=study_root))
    if repair_payload is None:
        return None
    if _first_ai_doctor_repair_action(repair_payload) is None:
        return None
    return repair_payload


def _serialize_ai_doctor_repair_result(
    *,
    repair_payload: Mapping[str, Any],
    action: Mapping[str, Any],
    state: str,
    dispatch_status: str,
    reason: str | None = None,
) -> dict[str, Any]:
    result = {
        "study_id": _non_empty_text(repair_payload.get("study_id")),
        "quest_id": _non_empty_text(repair_payload.get("quest_id")),
        "state": state,
        "action_type": _non_empty_text(action.get("action_type")),
        "repair_kind": _non_empty_text(action.get("repair_kind")),
        "owner": _non_empty_text(action.get("owner")),
        "auto_apply_allowed": bool(action.get("auto_apply_allowed")),
        "quality_gate_relaxation_allowed": False,
        "dispatch_status": dispatch_status,
        "source": AI_DOCTOR_REPAIR_SOURCE,
    }
    if reason is not None:
        result["reason"] = reason
    return result


def _string_items(value: object) -> set[str]:
    if isinstance(value, str):
        text = value.strip()
        return {text} if text else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _non_empty_text(item)) is not None}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def status_allows_ai_doctor_repair(status_payload: Mapping[str, Any]) -> bool:
    reason = _non_empty_text(status_payload.get("reason"))
    runtime_health = _mapping(status_payload.get("runtime_health_snapshot"))
    runtime_action = _non_empty_text(runtime_health.get("canonical_runtime_action"))
    attempt_state = _non_empty_text(runtime_health.get("attempt_state"))
    runtime_reasons = _string_items(runtime_health.get("blocking_reasons"))
    if runtime_action in {"recover_runtime", "relaunch_runtime"} and (
        attempt_state in {"recovering", "probe_required"} or "runtime_recovery_retry_budget_exhausted" in runtime_reasons
    ):
        return True
    control_plane = _mapping(status_payload.get("control_plane_snapshot"))
    control_reasons = _string_items(control_plane.get("blocking_reasons"))
    route_authorization = _mapping(control_plane.get("route_authorization"))
    if (
        reason
        in {
            "quest_marked_running_but_no_live_session",
            "quest_waiting_on_invalid_blocking",
            "quest_stopped_by_controller_guard",
        }
        and route_authorization.get("runtime_recovery_allowed") is True
    ):
        return True
    if (
        "runtime_recovery_retry_budget_exhausted" in control_reasons
        and route_authorization.get("runtime_recovery_allowed") is True
    ):
        return True
    return False


def _mark_ai_doctor_repair_applied(
    *,
    repair_path: Path,
    repair_payload: Mapping[str, Any],
    action: Mapping[str, Any],
    result: Mapping[str, Any],
) -> None:
    updated = {
        **dict(repair_payload),
        "state": "applied",
        "applied_at": utc_now(),
        "applied_action": dict(action),
        "application_result": dict(result),
        "quality_gate_relaxation_allowed": False,
    }
    _write_json_object(repair_path, updated)


def _apply_ai_doctor_repair_action(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    repair_payload: Mapping[str, Any],
    action: Mapping[str, Any],
) -> dict[str, Any]:
    action_type = _non_empty_text(action.get("action_type"))
    repair_kind = _non_empty_text(action.get("repair_kind"))
    auto_apply_allowed = action.get("auto_apply_allowed") is True
    if action_type == "platform_repair":
        return _serialize_ai_doctor_repair_result(
            repair_payload=repair_payload,
            action=action,
            state="blocked",
            dispatch_status="not_dispatched",
            reason="ai_doctor_platform_repair_requires_repo_level_fix",
        )
    if not auto_apply_allowed or action.get("quality_gate_relaxation_allowed") is True:
        return _serialize_ai_doctor_repair_result(
            repair_payload=repair_payload,
            action=action,
            state="blocked",
            dispatch_status="not_dispatched",
            reason="ai_doctor_repair_not_auto_applicable",
        )
    if action_type not in {"controller_repair", "task_repair"}:
        return _serialize_ai_doctor_repair_result(
            repair_payload=repair_payload,
            action=action,
            state="blocked",
            dispatch_status="not_dispatched",
            reason="ai_doctor_repair_action_type_not_supported",
        )

    study_runtime_router.ensure_study_runtime(
        profile=profile,
        study_root=study_root,
        allow_stopped_relaunch=repair_kind in {"analysis_claim_evidence_redrive", "bounded_work_unit_redrive"},
        force=False,
        source=AI_DOCTOR_REPAIR_SOURCE,
    )
    return _serialize_ai_doctor_repair_result(
        repair_payload=repair_payload,
        action=action,
        state="applied",
        dispatch_status="executed",
    )


def apply_ready_ai_doctor_repair(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: Mapping[str, Any],
    repair_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not status_allows_ai_doctor_repair(status_payload):
        return None
    repair_path = _latest_ai_doctor_repair_path(study_root=study_root)
    repair_payload = dict(repair_payload) if isinstance(repair_payload, Mapping) else _read_json_object(repair_path)
    if repair_payload is None:
        return None
    action = _first_ai_doctor_repair_action(repair_payload)
    if action is None:
        return None
    result = _apply_ai_doctor_repair_action(
        profile=profile,
        study_root=study_root,
        repair_payload=repair_payload,
        action=action,
    )
    if result.get("state") == "applied":
        _mark_ai_doctor_repair_applied(
            repair_path=repair_path,
            repair_payload=repair_payload,
            action=action,
            result=result,
        )
    return result


__all__ = [
    "AI_DOCTOR_REPAIR_SOURCE",
    "apply_ready_ai_doctor_repair",
    "read_ready_ai_doctor_repair",
]
