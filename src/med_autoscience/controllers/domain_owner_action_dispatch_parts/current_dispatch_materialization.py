from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.owner_callable_adapter_projection import (
    domain_progress_transition_requests,
)


TransitionRequestProjectionProducer = Callable[..., dict[str, Any]]


def current_materialized_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    mode: str,
    apply: bool,
    fresh_progress: Mapping[str, Any] | None = None,
    transition_request_projection_producer: TransitionRequestProjectionProducer,
    text: Callable[[object], str | None],
) -> list[dict[str, Any]]:
    payload = transition_request_projection_producer(
        profile=profile,
        study_ids=(study_id,),
        mode=mode,
        apply=apply,
        dispatch_ready_for_execution=True,
    )
    requested = set(action_types)
    foreground_dispatches = [
        dict(dispatch)
        for dispatch in payload.get("mas_foreground_owner_callable_dispatches", [])
        if isinstance(dispatch, Mapping)
        and (not requested or text(dispatch.get("action_type")) in requested)
    ]
    if foreground_dispatches:
        return foreground_dispatches
    return [
        dict(dispatch)
        for dispatch in domain_progress_transition_requests(payload)
        if isinstance(dispatch, Mapping)
        and (not requested or text(dispatch.get("action_type")) in requested)
        and not _superseded_by_current_mas_owner_callable(
            progress=fresh_progress,
            dispatch=dispatch,
            text=text,
        )
    ]


def _materialized_from_requested_action(
    *,
    dispatch: Mapping[str, Any],
    requested: set[str],
    text: Callable[[object], str | None],
) -> bool:
    source_action_ref = dispatch.get("source_action_ref")
    source_action = source_action_ref if isinstance(source_action_ref, Mapping) else {}
    owner_route_ref = dispatch.get("owner_route_ref")
    owner_route = owner_route_ref if isinstance(owner_route_ref, Mapping) else {}
    source_refs = owner_route.get("source_refs")
    route_source_refs = source_refs if isinstance(source_refs, Mapping) else {}
    for value in (
        source_action.get("materialized_from_action_type"),
        route_source_refs.get("materialized_from_action_type"),
    ):
        action_type = text(value)
        if action_type in requested:
            return True
    return False


def _superseded_by_current_mas_owner_callable(
    *,
    progress: Mapping[str, Any] | None,
    dispatch: Mapping[str, Any],
    text: Callable[[object], str | None],
) -> bool:
    if not progress or text(dispatch.get("surface")) != "mas_domain_progress_transition_request_projection":
        return False
    current_action = _mapping(progress.get("current_executable_owner_action"))
    current_work_unit = _mapping(progress.get("current_work_unit"))
    if not _mas_owner_callable_action_is_current(
        progress=progress,
        current_action=current_action,
        current_work_unit=current_work_unit,
        text=text,
    ):
        return False
    return _same_owner_action_identity(
        progress=progress,
        action=current_action,
        dispatch=dispatch,
        text=text,
    )


def _mas_owner_callable_action_is_current(
    *,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    text: Callable[[object], str | None],
) -> bool:
    target_surface = _mapping(current_action.get("target_surface"))
    if text(target_surface.get("ref_kind")) != "mas_owner_callable":
        return False
    if text(current_action.get("status")) not in {"ready", "executable_owner_action"}:
        return False
    paper_recovery_state = _mapping(progress.get("paper_recovery_state"))
    next_safe_action = _mapping(paper_recovery_state.get("next_safe_action"))
    if text(next_safe_action.get("kind")) not in {None, "run_mas_owner_callable"}:
        return False
    if any(_flag(current_action, key) for key in _OPL_TRANSITION_FLAGS):
        return False
    work_unit_state = _mapping(current_work_unit.get("state"))
    return not any(_flag(work_unit_state, key) for key in _OPL_TRANSITION_FLAGS)


def _same_owner_action_identity(
    *,
    progress: Mapping[str, Any],
    action: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    text: Callable[[object], str | None],
) -> bool:
    action_type = text(action.get("action_type")) or _first_text(action.get("allowed_actions"), text)
    if action_type is None or action_type != text(dispatch.get("action_type")):
        return False
    action_study_id = text(action.get("study_id")) or text(progress.get("study_id"))
    if action_study_id is None or action_study_id != text(dispatch.get("study_id")):
        return False
    action_owner = (
        text(action.get("next_owner"))
        or text(action.get("owner"))
        or text(action.get("next_executable_owner"))
    )
    dispatch_owner = (
        text(dispatch.get("next_executable_owner"))
        or text(dispatch.get("owner"))
        or text(_dispatch_owner_route(dispatch).get("next_owner"))
    )
    if action_owner is None or action_owner != dispatch_owner:
        return False
    action_work_unit_id = _work_unit_id(action, text)
    dispatch_work_unit_id = _dispatch_work_unit_id(dispatch, text)
    if action_work_unit_id is None or action_work_unit_id != dispatch_work_unit_id:
        return False
    return bool(
        _owner_action_fingerprints(action, text).intersection(
            _dispatch_fingerprints(dispatch, text)
        )
    )


def _dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    return (
        _mapping(dispatch.get("owner_route"))
        or _mapping(dispatch.get("owner_route_ref"))
        or _mapping(prompt_contract.get("owner_route"))
        or _mapping(prompt_contract.get("owner_route_ref"))
    )


def _dispatch_work_unit_id(
    dispatch: Mapping[str, Any],
    text: Callable[[object], str | None],
) -> str | None:
    route = _dispatch_owner_route(dispatch)
    source_refs = _mapping(route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action")) or _mapping(dispatch.get("source_action_ref"))
    return (
        text(dispatch.get("work_unit_id"))
        or text(source_refs.get("work_unit_id"))
        or text(basis.get("work_unit_id"))
        or _work_unit_id(prompt_contract.get("next_work_unit"), text)
        or _work_unit_id(dispatch.get("next_work_unit"), text)
        or _work_unit_id(source_action.get("work_unit_id"), text)
        or _work_unit_id(source_action.get("next_work_unit"), text)
    )


def _owner_action_fingerprints(
    action: Mapping[str, Any],
    text: Callable[[object], str | None],
) -> set[str]:
    currentness_basis = _mapping(action.get("currentness_basis")) or _mapping(
        action.get("owner_route_currentness_basis")
    )
    return _text_set(
        (
            action.get("work_unit_fingerprint"),
            action.get("action_fingerprint"),
            action.get("source_fingerprint"),
            currentness_basis.get("work_unit_fingerprint"),
            currentness_basis.get("action_fingerprint"),
            currentness_basis.get("source_fingerprint"),
        ),
        text,
    )


def _dispatch_fingerprints(
    dispatch: Mapping[str, Any],
    text: Callable[[object], str | None],
) -> set[str]:
    route = _dispatch_owner_route(dispatch)
    source_refs = _mapping(route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    prompt_basis = _mapping(prompt_contract.get("owner_route_currentness_basis"))
    source_action = _mapping(dispatch.get("source_action")) or _mapping(dispatch.get("source_action_ref"))
    return _text_set(
        (
            dispatch.get("work_unit_fingerprint"),
            dispatch.get("action_fingerprint"),
            dispatch.get("source_fingerprint"),
            prompt_contract.get("work_unit_fingerprint"),
            prompt_contract.get("action_fingerprint"),
            prompt_basis.get("work_unit_fingerprint"),
            route.get("work_unit_fingerprint"),
            route.get("source_fingerprint"),
            source_refs.get("work_unit_fingerprint"),
            basis.get("work_unit_fingerprint"),
            source_action.get("work_unit_fingerprint"),
            source_action.get("action_fingerprint"),
        ),
        text,
    )


def _work_unit_id(value: object, text: Callable[[object], str | None]) -> str | None:
    if isinstance(value, Mapping):
        return text(value.get("unit_id")) or text(value.get("work_unit_id"))
    return text(value)


def _text_set(
    values: tuple[object, ...],
    text: Callable[[object], str | None],
) -> set[str]:
    return {item for value in values if (item := text(value)) is not None}


def _first_text(value: object, text: Callable[[object], str | None]) -> str | None:
    if isinstance(value, str):
        return text(value)
    if isinstance(value, list | tuple | set):
        for item in value:
            if item_text := text(item):
                return item_text
    return None


def _flag(payload: Mapping[str, Any], key: str) -> bool:
    return payload.get(key) is True


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


_OPL_TRANSITION_FLAGS = (
    "provider_admission_pending",
    "transition_request_pending",
    "provider_attempt_or_lease_required",
    "provider_admission_requires_opl_runtime_result",
    "opl_transition_runtime_required",
)


__all__ = ["current_materialized_dispatches"]
