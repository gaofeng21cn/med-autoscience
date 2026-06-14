from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part

from . import consumed_transition_owner_routes
from . import stage_artifact_publication_handoff_currentness
from . import stage_native_dispatch_selection


def fresh_progress_current_owner_action_route(
    *,
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    route = dispatch_owner_route(dispatch)
    if not route or not owner_route_part.route_allows_action(action=dispatch, owner_route=route):
        return None
    for action in fresh_progress_current_owner_actions(progress):
        if current_owner_action_identity_matches_dispatch(
            progress=progress,
            action=action,
            dispatch=dispatch,
        ):
            return route
    return None


def dispatch_matches_fresh_progress_current_owner_action(
    *,
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    return fresh_progress_current_owner_action_route(
        progress=progress,
        dispatch=dispatch,
    ) is not None


def fresh_progress_owner_action_selectable(
    *,
    current_study: Mapping[str, Any],
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    if (
        consumed_transition_owner_routes.consumed_transition_owner_route(current_study)
        and not stage_artifact_publication_handoff_currentness.is_current(current_study)
    ):
        return False
    return dispatch_matches_fresh_progress_current_owner_action(
        progress=progress,
        dispatch=dispatch,
    )


def fresh_progress_current_owner_actions(progress: Mapping[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    current_action = _mapping(progress.get("current_executable_owner_action"))
    if _text(current_action.get("action_type")) is not None:
        actions.append(current_action)
    current_work_unit = _mapping(progress.get("current_work_unit"))
    if (
        _text(current_work_unit.get("status")) == "executable_owner_action"
        and _text(current_work_unit.get("action_type")) is not None
    ):
        actions.append(current_work_unit)
    return actions


def current_owner_action_identity_matches_dispatch(
    *,
    progress: Mapping[str, Any],
    action: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    action_type = _text(action.get("action_type"))
    if action_type is None or action_type != _text(dispatch.get("action_type")):
        return False
    progress_study_id = _text(action.get("study_id")) or _text(progress.get("study_id"))
    dispatch_study_id = _text(dispatch.get("study_id"))
    if progress_study_id is None or dispatch_study_id != progress_study_id:
        return False
    action_owner = (
        _text(action.get("next_owner"))
        or _text(action.get("owner"))
        or _text(action.get("next_executable_owner"))
    )
    dispatch_owner = (
        _text(dispatch.get("next_executable_owner"))
        or _text(dispatch.get("owner"))
        or _text(dispatch_owner_route(dispatch).get("next_owner"))
    )
    if action_owner is None or dispatch_owner != action_owner:
        return False
    action_work_unit = owner_action_work_unit_id(action)
    dispatch_work_unit = dispatch_work_unit_id(dispatch)
    if action_work_unit is None or dispatch_work_unit != action_work_unit:
        return False
    action_fingerprint = owner_action_work_unit_fingerprint(action)
    if action_fingerprint is None:
        return False
    return action_fingerprint in dispatch_work_unit_fingerprint_values(dispatch)


def owner_action_work_unit_id(action: Mapping[str, Any]) -> str | None:
    return (
        work_unit_id(action.get("work_unit_id"))
        or work_unit_id(action.get("next_work_unit"))
        or work_unit_id(action.get("work_unit"))
    )


def owner_action_work_unit_fingerprint(action: Mapping[str, Any]) -> str | None:
    return (
        _text(action.get("work_unit_fingerprint"))
        or _text(action.get("action_fingerprint"))
        or _text(action.get("source_fingerprint"))
    )


def dispatch_work_unit_id(dispatch: Mapping[str, Any]) -> str | None:
    route = dispatch_owner_route(dispatch)
    refs = _mapping(route.get("source_refs"))
    basis = _mapping(refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    return (
        work_unit_id(refs.get("work_unit_id"))
        or work_unit_id(basis.get("work_unit_id"))
        or work_unit_id(prompt_contract.get("next_work_unit"))
        or work_unit_id(dispatch.get("next_work_unit"))
        or work_unit_id(source_action.get("next_work_unit"))
    )


def dispatch_work_unit_fingerprint_values(dispatch: Mapping[str, Any]) -> set[str]:
    route = dispatch_owner_route(dispatch)
    refs = _mapping(route.get("source_refs"))
    basis = _mapping(refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    prompt_basis = _mapping(prompt_contract.get("owner_route_currentness_basis"))
    source_action = _mapping(dispatch.get("source_action"))
    values = (
        dispatch.get("work_unit_fingerprint"),
        dispatch.get("action_fingerprint"),
        dispatch.get("source_fingerprint"),
        prompt_contract.get("work_unit_fingerprint"),
        prompt_contract.get("action_fingerprint"),
        prompt_basis.get("work_unit_fingerprint"),
        route.get("work_unit_fingerprint"),
        route.get("source_fingerprint"),
        refs.get("work_unit_fingerprint"),
        basis.get("work_unit_fingerprint"),
        source_action.get("work_unit_fingerprint"),
        source_action.get("action_fingerprint"),
    )
    return {text for value in values if (text := _text(value)) is not None}


def work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return stage_native_dispatch_selection.dispatch_owner_route(dispatch)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "dispatch_matches_fresh_progress_current_owner_action",
    "dispatch_work_unit_id",
    "dispatch_work_unit_fingerprint_values",
    "fresh_progress_current_owner_action_route",
    "fresh_progress_owner_action_selectable",
    "work_unit_id",
]
