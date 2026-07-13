from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.owner_callable_adapter_projection import (
    ai_route_contexts,
)
from med_autoscience.profiles import WorkspaceProfile


RouteContextProjectionProducer = Callable[..., dict[str, Any]]


def current_materialized_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    mode: str,
    apply: bool,
    fresh_progress: Mapping[str, Any] | None = None,
    ai_route_context_projection_producer: RouteContextProjectionProducer,
    text: Callable[[object], str | None],
) -> list[dict[str, Any]]:
    del fresh_progress
    payload = ai_route_context_projection_producer(
        profile=profile,
        study_ids=(study_id,),
        mode=mode,
        apply=apply,
        dispatch_ready_for_execution=True,
    )
    requested = set(action_types)
    foreground_dispatches = [
        dict(dispatch)
        for dispatch in payload.get("mas_foreground_owner_callable_adapters", [])
        if isinstance(dispatch, Mapping)
        and (not requested or text(dispatch.get("action_type")) in requested)
    ]
    if foreground_dispatches:
        return foreground_dispatches
    return [
        dict(dispatch)
        for dispatch in ai_route_contexts(payload)
        if isinstance(dispatch, Mapping)
        and (not requested or text(dispatch.get("action_type")) in requested)
    ]


__all__ = ["current_materialized_dispatches"]
