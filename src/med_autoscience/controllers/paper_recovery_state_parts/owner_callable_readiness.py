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
    if _current_work_unit_status(current_work_unit) != "executable_owner_action":
        return None
    action_type = _text(obligation.get("action_type"))
    if action_type is None:
        return None
    action = _mapping(progress.get("current_executable_owner_action"))
    if action and not _current_action_matches_obligation(action, obligation=obligation):
        return None
    if not _current_work_unit_matches_obligation(current_work_unit, obligation=obligation):
        return None
    if not _direct_study_or_paper_execution_allowed(progress):
        return None
    owner_callable = owner_callable_for_action(action_type)
    if owner_callable is None:
        return None
    return owner_callable


def _direct_study_or_paper_execution_allowed(progress: Mapping[str, Any]) -> bool:
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
