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
    source = _current_work_unit_source(monitoring)
    next_work_unit = _monitoring_next_work_unit(monitoring)
    return {
        "study_id": _text(monitoring.get("study_id")) or _text(transition.get("study_id")),
        "decision_type": "current_owner_handoff",
        "route_target": _text(source.get("route_target")) or _owner(source) or "inspect",
        "next_work_unit": next_work_unit,
        "controller_action": _controller_action(source) or "owner_action",
        "owner": _owner(source) or "med-autoscience",
        "typed_blocker": None,
        "guard_boundary": _current_owner_action_guard_boundary(monitoring),
        "source_refs": _string_list(monitoring.get("source_refs")),
    }


def monitoring_has_authoritative_owner_action(monitoring: Mapping[str, Any]) -> bool:
    source = _current_work_unit_source(monitoring)
    if _execution_state_kind(source) != "executable_owner_action":
        return False
    if _typed_blocker(source):
        return False
    if source is monitoring and monitoring.get("owner_action_current") is not True:
        return False
    return (
        _owner(source) is not None
        or _controller_action(source) is not None
        or _work_unit_id(source.get("next_work_unit")) is not None
        or _work_unit_id(source.get("work_unit_id")) is not None
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
    source = _current_work_unit_source(monitoring)
    if _owner(source) != _text(transition.get("owner")):
        return True
    if _controller_action(source) != _text(transition.get("controller_action")):
        return True
    source_work_unit = _work_unit_id(source.get("work_unit_id")) or _work_unit_id(source.get("next_work_unit"))
    return source_work_unit != _work_unit_id(transition.get("next_work_unit"))


def _monitoring_next_work_unit(monitoring: Mapping[str, Any]) -> dict[str, Any]:
    source = _current_work_unit_source(monitoring)
    existing = _dict(source.get("next_work_unit"))
    if existing:
        return existing
    unit_id = (
        _work_unit_id(source.get("work_unit_id"))
        or _work_unit_id(source.get("next_work_unit"))
        or _controller_action(source)
    )
    return {
        "unit_id": unit_id or "current_owner_action",
        "lane": _text(source.get("route_target")) or _owner(source),
        "summary": "Current Progress-first owner handoff action.",
    }


def _current_owner_action_guard_boundary(monitoring: Mapping[str, Any]) -> dict[str, Any]:
    source = _current_work_unit_source(monitoring)
    next_forced_delta = _dict(source.get("next_forced_delta")) or _dict(monitoring.get("next_forced_delta"))
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


def _current_work_unit_source(monitoring: Mapping[str, Any]) -> Mapping[str, Any]:
    return _dict(monitoring.get("current_work_unit")) or monitoring


def _execution_state_kind(source: Mapping[str, Any]) -> str | None:
    status = _text(source.get("status"))
    if status in {"executable_owner_action", "running_provider_attempt", "typed_blocker"}:
        return status
    return _text(source.get("execution_state_kind"))


def _owner(source: Mapping[str, Any]) -> str | None:
    return _text(source.get("next_owner")) or _text(source.get("owner"))


def _controller_action(source: Mapping[str, Any]) -> str | None:
    return _text(source.get("controller_action")) or _text(source.get("action_type"))


def _typed_blocker(source: Mapping[str, Any]) -> dict[str, Any]:
    state = _dict(source.get("state"))
    return _dict(source.get("typed_blocker")) or _dict(state.get("typed_blocker"))


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
