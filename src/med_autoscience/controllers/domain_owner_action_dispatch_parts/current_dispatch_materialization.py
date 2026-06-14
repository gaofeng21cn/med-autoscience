from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


CurrentDefaultDispatches = Callable[..., dict[str, Any]]
Dispatches = Callable[..., list[dict[str, Any]]]
MaterializeRequests = Callable[..., dict[str, Any]]


def current_materialized_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    mode: str,
    apply: bool,
    current_default_executor_dispatches: CurrentDefaultDispatches,
    text: Callable[[object], str | None],
) -> list[dict[str, Any]]:
    payload = current_default_executor_dispatches(
        profile=profile,
        study_ids=(study_id,),
        mode=mode,
        apply=apply,
        dispatch_ready_for_execution=not apply,
    )
    requested = set(action_types)
    return [
        dict(dispatch)
        for dispatch in payload.get("default_executor_dispatches") or []
        if isinstance(dispatch, Mapping)
        and (not requested or text(dispatch.get("action_type")) in requested)
    ]


def materialize_current_dispatches_for_apply(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    mode: str,
    materialize_domain_action_requests: MaterializeRequests,
    dispatches: Dispatches,
    current_default_executor_dispatches: CurrentDefaultDispatches,
    text: Callable[[object], str | None],
) -> list[dict[str, Any]]:
    materialize_domain_action_requests(
        profile=profile,
        study_ids=(study_id,),
        mode=mode,
        apply=True,
    )
    selected = dispatches(profile, study_id, action_types)
    if selected:
        return selected
    return current_materialized_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=action_types,
        mode=mode,
        apply=False,
        current_default_executor_dispatches=current_default_executor_dispatches,
        text=text,
    )


__all__ = ["current_materialized_dispatches", "materialize_current_dispatches_for_apply"]
