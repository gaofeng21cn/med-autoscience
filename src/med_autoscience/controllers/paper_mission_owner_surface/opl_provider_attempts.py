from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def action_is_covered_by_live_attempt(
    *,
    live_attempt: Mapping[str, Any] | None,
    action: Mapping[str, Any],
) -> bool:
    if not live_attempt:
        return False
    live_action_type = _text(live_attempt.get("action_type"))
    action_type = _text(action.get("action_type"))
    if live_action_type != action_type:
        return False
    live_work_unit = _text(live_attempt.get("work_unit_id"))
    action_work_unit = _text(action.get("work_unit_id")) or _text(
        action.get("next_work_unit")
    )
    return live_work_unit is None or action_work_unit is None or live_work_unit == action_work_unit


def filter_actions_covered_by_live_attempt(
    *,
    live_attempt: Mapping[str, Any] | None,
    actions: Iterable[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    return [
        action
        for action in actions
        if not action_is_covered_by_live_attempt(
            live_attempt=live_attempt,
            action=action,
        )
    ]


def owner_route_is_covered_by_live_attempt(
    *,
    live_attempt: Mapping[str, Any] | None,
    owner_route: Mapping[str, Any],
) -> bool:
    if not live_attempt:
        return False
    live_action_type = _text(live_attempt.get("action_type"))
    allowed_actions = {
        item
        for value in _iter_values(owner_route.get("allowed_actions"))
        if (item := _text(value)) is not None
    }
    if live_action_type is None or live_action_type not in allowed_actions:
        return False
    live_work_unit = _text(live_attempt.get("work_unit_id"))
    route_work_unit = _text(owner_route.get("work_unit_id")) or _text(
        owner_route.get("next_work_unit")
    )
    return live_work_unit is None or route_work_unit is None or live_work_unit == route_work_unit


def owner_state_overlay(
    *,
    live_attempt: Mapping[str, Any] | None,
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    if not owner_route_is_covered_by_live_attempt(
        live_attempt=live_attempt,
        owner_route=owner_route,
    ):
        return {}
    return {
        "why_not_applied": None,
        "blocked_reason": None,
        "next_owner": "supervisor_only/live_provider_attempt",
        "lifecycle": {},
    }


def projection_fields(
    *,
    live_attempt: Mapping[str, Any] | None,
    fallback_active_run_id: str | None,
    fallback_runtime_health: Mapping[str, Any],
) -> dict[str, Any]:
    if not live_attempt:
        return {
            "active_run_id": fallback_active_run_id,
            "active_stage_attempt_id": None,
            "active_workflow_id": None,
            "running_provider_attempt": False,
            "runtime_health": dict(fallback_runtime_health),
        }
    return {
        "active_run_id": _text(live_attempt.get("active_run_id")),
        "active_stage_attempt_id": _text(live_attempt.get("active_stage_attempt_id")),
        "active_workflow_id": _text(live_attempt.get("active_workflow_id")),
        "running_provider_attempt": live_attempt.get("running_provider_attempt") is True,
        "runtime_health": _mapping(live_attempt.get("runtime_health")),
        "stage_progress_log": _mapping(live_attempt.get("stage_progress_log")),
    }


def _iter_values(value: object) -> tuple[object, ...]:
    if isinstance(value, (list, tuple, set)):
        return tuple(value)
    return ()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "action_is_covered_by_live_attempt",
    "filter_actions_covered_by_live_attempt",
    "owner_route_is_covered_by_live_attempt",
    "owner_state_overlay",
    "projection_fields",
]
