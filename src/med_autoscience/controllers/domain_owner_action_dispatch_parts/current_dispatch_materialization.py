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


__all__ = ["current_materialized_dispatches"]
