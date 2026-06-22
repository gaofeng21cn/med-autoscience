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
    transition_request_projection_producer: TransitionRequestProjectionProducer,
    text: Callable[[object], str | None],
) -> list[dict[str, Any]]:
    payload = transition_request_projection_producer(
        profile=profile,
        study_ids=(study_id,),
        mode=mode,
        apply=apply,
        dispatch_ready_for_execution=not apply,
    )
    requested = set(action_types)
    return [
        dict(dispatch)
        for dispatch in domain_progress_transition_requests(payload)
        if isinstance(dispatch, Mapping)
        and (not requested or text(dispatch.get("action_type")) in requested)
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


__all__ = ["current_materialized_dispatches"]
