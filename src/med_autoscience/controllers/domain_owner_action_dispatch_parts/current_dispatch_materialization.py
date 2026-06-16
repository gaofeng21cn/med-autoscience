from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


CurrentDefaultDispatches = Callable[..., dict[str, Any]]


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
        for dispatch in payload.get("owner_callable_adapters") or payload.get("default_executor_dispatches") or []
        if isinstance(dispatch, Mapping)
        and (not requested or text(dispatch.get("action_type")) in requested)
    ]


__all__ = ["current_materialized_dispatches"]
