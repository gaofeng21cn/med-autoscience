from __future__ import annotations

from typing import Any, Mapping


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def progress_pressure_from_slo_status(
    *,
    payload: Mapping[str, Any],
    repair: Mapping[str, Any],
    profile_payload: Mapping[str, Any],
    schema_version: int,
) -> dict[str, Any]:
    repair_actions = _list(repair.get("actions"))
    top_action = dict(repair_actions[0]) if repair_actions and isinstance(repair_actions[0], Mapping) else None
    executable_action = next(
        (
            dict(action)
            for action in repair_actions
            if isinstance(action, Mapping) and _text(action.get("action_type")) != "ai_doctor_diagnosis"
        ),
        top_action,
    )
    runtime_failure = _mapping(
        profile_payload.get("runtime_failure_classification")
        or _mapping(profile_payload.get("autonomy_slo")).get("runtime_failure_classification")
    )
    action_mode = _text(runtime_failure.get("action_mode"))
    external_blocker = bool(runtime_failure.get("external_blocker"))
    state = _text(payload.get("state"))
    stop_allowed = state in {"blocked_external", "human_gate_required"}
    gate_summary = _mapping(profile_payload.get("gate_blocker_summary"))
    next_work_unit = _mapping(gate_summary.get("next_work_unit"))
    sli_summary = _mapping(profile_payload.get("sli_summary"))
    next_work_unit_id = (
        _text(next_work_unit.get("unit_id"))
        or _text(sli_summary.get("next_work_unit_id"))
        or _text(executable_action.get("repair_kind") if executable_action else None)
    )
    if stop_allowed:
        status = "handoff_or_human_gate"
    elif state == "breach" or top_action is not None:
        status = "advance_now"
    elif state in {"met", "unknown"}:
        status = "monitor"
    else:
        status = "advance_now"
    return {
        "surface": "progress_first_advancement_pressure",
        "schema_version": schema_version,
        "status": status,
        "purpose": "continue_progress",
        "no_progress_is_terminal_failure": False,
        "timeout_is_terminal_failure": False,
        "continuation_required": status in {"advance_now", "monitor"},
        "quality_gate_relaxation_allowed": False,
        "external_blocker": external_blocker,
        "runtime_action_mode": action_mode,
        "state_signal": state,
        "breach_types": list(_list(payload.get("breach_types"))),
        "next_owner": (
            "mas_controller"
            if next_work_unit_id is not None and not stop_allowed
            else _text(executable_action.get("owner") if executable_action else None) or "mas_controller"
        ),
        "next_action_type": (
            "domain_route/reconcile-apply"
            if next_work_unit_id is not None and not stop_allowed
            else _text(executable_action.get("action_type") if executable_action else None) or "monitor_autonomy_slo"
        ),
        "next_repair_kind": _text(executable_action.get("repair_kind") if executable_action else None),
        "next_work_unit_id": next_work_unit_id,
        "stop_allowed": stop_allowed,
        "terminal_failure": False,
        "repair_state": _text(repair.get("state")) or "unknown",
    }


__all__ = ["progress_pressure_from_slo_status"]
