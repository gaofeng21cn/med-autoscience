from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.paper_recovery_state_parts.obligation_matching import (
    action_matches_obligation as _current_action_matches_obligation,
    current_work_unit_matches_obligation as _current_work_unit_matches_obligation,
)
from med_autoscience.runtime_control.owner_callable_registry import owner_callable_for_action


def current_mas_owner_callable(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    current_work_unit = _mapping(progress.get("current_work_unit"))
    current_status = _current_work_unit_status(current_work_unit)
    if current_status not in {
        "executable_owner_action",
        "typed_blocker",
    }:
        return None
    if current_status == "typed_blocker" and _typed_blocker_has_terminal_owner_answer(current_work_unit):
        return None
    action_type = _text(obligation.get("action_type"))
    if action_type is None:
        return None
    owner_callable = owner_callable_for_action(action_type)
    if owner_callable is None:
        return None
    action = _mapping(progress.get("current_executable_owner_action"))
    if action and not _current_action_matches_obligation(action, obligation=obligation):
        return None
    if not _current_work_unit_matches_obligation(current_work_unit, obligation=obligation):
        return None
    if not _direct_study_or_paper_execution_allowed(progress):
        return None
    return owner_callable


def _typed_blocker_has_terminal_owner_answer(current_work_unit: Mapping[str, Any]) -> bool:
    state = _mapping(current_work_unit.get("state"))
    typed_blocker = _mapping(state.get("typed_blocker")) or _mapping(current_work_unit.get("typed_blocker"))
    owner_answer_binding = _mapping(state.get("owner_answer_binding"))
    required_output_contract = _mapping(current_work_unit.get("required_output_contract"))
    return any(
        _text(value) is not None
        for value in (
            owner_answer_binding.get("latest_owner_answer_ref"),
            owner_answer_binding.get("typed_blocker_ref"),
            typed_blocker.get("latest_owner_answer_ref"),
            typed_blocker.get("typed_blocker_ref"),
            required_output_contract.get("typed_blocker_ref"),
        )
    )


def _direct_study_or_paper_execution_allowed(progress: Mapping[str, Any]) -> bool:
    route_authorization = _mapping(_mapping(progress.get("authority_snapshot")).get("route_authorization"))
    if route_authorization.get("paper_write_allowed") is True or route_authorization.get(
        "managed_worker_paper_write_allowed"
    ) is True:
        return True
    allowed = {
        *_text_items(_mapping(progress.get("study_truth_snapshot")).get("allowed_controller_actions")),
        *_text_items(_mapping(progress.get("authority_snapshot")).get("allowed_controller_actions")),
    }
    return bool(allowed & {"direct_study_execution", "direct_paper_line_write"})


def _current_work_unit_status(work_unit: Mapping[str, Any]) -> str | None:
    return _text(work_unit.get("status")) or _text(_mapping(work_unit.get("state")).get("state_kind"))


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def _text_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item)) is not None]
