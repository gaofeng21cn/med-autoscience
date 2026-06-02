from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def effective_transition_for_monitoring(
    *,
    transition: Mapping[str, Any],
    monitoring: Mapping[str, Any],
) -> dict[str, Any]:
    if not monitoring_has_authoritative_owner_action(monitoring):
        return dict(transition)
    if not _monitoring_disagrees_with_transition(monitoring=monitoring, transition=transition):
        return dict(transition)
    next_work_unit = _monitoring_next_work_unit(monitoring)
    return {
        "study_id": _text(monitoring.get("study_id")) or _text(transition.get("study_id")),
        "decision_type": "current_owner_handoff",
        "route_target": _text(monitoring.get("route_target")) or _text(monitoring.get("next_owner")) or "inspect",
        "next_work_unit": next_work_unit,
        "controller_action": _text(monitoring.get("controller_action")) or "owner_action",
        "owner": _text(monitoring.get("next_owner")) or "med-autoscience",
        "typed_blocker": None,
        "guard_boundary": _current_owner_action_guard_boundary(monitoring),
        "source_refs": _string_list(monitoring.get("source_refs")),
    }


def monitoring_has_authoritative_owner_action(monitoring: Mapping[str, Any]) -> bool:
    if monitoring.get("owner_action_current") is not True:
        return False
    if _text(monitoring.get("execution_state_kind")) != "executable_owner_action":
        return False
    if _dict(monitoring.get("typed_blocker")):
        return False
    return (
        _text(monitoring.get("next_owner")) is not None
        or _text(monitoring.get("controller_action")) is not None
        or _work_unit_id(monitoring.get("next_work_unit")) is not None
    )


def completion_receipt_consumed_handoff(transition: Mapping[str, Any]) -> bool:
    if _text(transition.get("decision_type")) != "completion_receipt_consumed":
        return False
    completion = _dict(transition.get("completion_receipt_consumption"))
    return _text(completion.get("status")) in {"consumed", "receipt_consumed", "completed"}


def _monitoring_disagrees_with_transition(
    *,
    monitoring: Mapping[str, Any],
    transition: Mapping[str, Any],
) -> bool:
    if _text(monitoring.get("next_owner")) != _text(transition.get("owner")):
        return True
    if _text(monitoring.get("controller_action")) != _text(transition.get("controller_action")):
        return True
    return _work_unit_id(monitoring.get("next_work_unit")) != _work_unit_id(transition.get("next_work_unit"))


def _monitoring_next_work_unit(monitoring: Mapping[str, Any]) -> dict[str, Any]:
    existing = _dict(monitoring.get("next_work_unit"))
    if existing:
        return existing
    unit_id = _work_unit_id(monitoring.get("next_work_unit")) or _text(monitoring.get("controller_action"))
    return {
        "unit_id": unit_id or "current_owner_action",
        "lane": _text(monitoring.get("route_target")) or _text(monitoring.get("next_owner")),
        "summary": "Current Progress-first owner handoff action.",
    }


def _current_owner_action_guard_boundary(monitoring: Mapping[str, Any]) -> dict[str, Any]:
    next_forced_delta = _dict(monitoring.get("next_forced_delta"))
    target_surface = _dict(next_forced_delta.get("target_surface"))
    payload: dict[str, Any] = {
        "runner_boundary": "mas_domain_read_model_only",
        "can_write_domain_truth": False,
        "can_execute_generic_state_machine": False,
        "opl_generic_runner_may_resume": True,
    }
    if surface := _text(target_surface.get("surface_ref")):
        payload["required_owner_surface"] = surface
    return payload


def _dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return dict(value.to_dict())
    return {}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "completion_receipt_consumed_handoff",
    "effective_transition_for_monitoring",
    "monitoring_has_authoritative_owner_action",
]
