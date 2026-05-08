from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience.runtime_backend import ManagedRuntimeBackend

_UNSET = object()

__all__ = [
    "_create_quest",
    "_get_quest_session",
    "_inspect_quest_live_execution",
    "_pause_quest",
    "_resume_quest",
    "_schedule_turn",
    "_complete_turn_and_normalize",
    "_inspect_turn_lifecycle",
    "_update_quest_startup_context",
]


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


def _default_runtime_backend() -> ManagedRuntimeBackend:
    router = _router_module()
    if hasattr(router, "managed_runtime_transport"):
        return router.managed_runtime_transport
    if hasattr(router, "_default_managed_runtime_backend"):
        return router._default_managed_runtime_backend()
    if hasattr(router, "managed_runtime_backend"):
        return router.managed_runtime_backend
    raise AttributeError(
        "study_runtime_transport requires router to expose managed_runtime_transport or managed_runtime_backend"
    )


def _inspect_quest_live_execution(
    *,
    runtime_root: Path,
    quest_id: str,
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> dict[str, Any]:
    backend = runtime_backend or _default_runtime_backend()
    return backend.inspect_quest_live_execution(
        runtime_root=runtime_root,
        quest_id=quest_id,
    )


def _get_quest_session(
    *,
    runtime_root: Path,
    quest_id: str,
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> dict[str, Any]:
    backend = runtime_backend or _default_runtime_backend()
    return backend.get_quest_session(
        runtime_root=runtime_root,
        quest_id=quest_id,
    )


def _create_quest(
    *,
    runtime_root: Path,
    payload: dict[str, Any],
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> dict[str, Any]:
    backend = runtime_backend or _default_runtime_backend()
    return backend.create_quest(
        runtime_root=runtime_root,
        payload=payload,
    )


def _resume_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    source: str,
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> dict[str, Any]:
    backend = runtime_backend or _default_runtime_backend()
    return backend.resume_quest(
        runtime_root=runtime_root,
        quest_id=quest_id,
        source=source,
    )


def _schedule_turn(
    *,
    runtime_root: Path,
    quest_id: str,
    reason: str,
    source: str,
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> dict[str, Any]:
    backend = runtime_backend or _default_runtime_backend()
    return backend.schedule_turn(
        runtime_root=runtime_root,
        quest_id=quest_id,
        reason=reason,
        source=source,
    )


def _complete_turn_and_normalize(
    *,
    runtime_root: Path,
    quest_id: str,
    run_id: str,
    runner_status: str,
    source: str,
    blocking_decision_request: dict[str, Any] | None = None,
    same_fingerprint: bool = False,
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> dict[str, Any]:
    backend = runtime_backend or _default_runtime_backend()
    return backend.complete_turn_and_normalize(
        runtime_root=runtime_root,
        quest_id=quest_id,
        run_id=run_id,
        runner_status=runner_status,
        source=source,
        blocking_decision_request=blocking_decision_request,
        same_fingerprint=same_fingerprint,
    )


def _inspect_turn_lifecycle(
    *,
    runtime_root: Path,
    quest_id: str,
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> dict[str, Any]:
    backend = runtime_backend or _default_runtime_backend()
    return backend.inspect_turn_lifecycle(
        runtime_root=runtime_root,
        quest_id=quest_id,
    )


def _pause_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    source: str,
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> dict[str, Any]:
    backend = runtime_backend or _default_runtime_backend()
    return backend.pause_quest(
        runtime_root=runtime_root,
        quest_id=quest_id,
        source=source,
    )


def _update_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    startup_contract: dict[str, Any],
    requested_baseline_ref: dict[str, Any] | None | object = _UNSET,
    runtime_backend: ManagedRuntimeBackend | None = None,
) -> Any:
    from med_autoscience.controllers.study_runtime_types import StudyRuntimeStartupContextSyncResult

    kwargs: dict[str, Any] = {
        "runtime_root": runtime_root,
        "quest_id": quest_id,
        "startup_contract": startup_contract,
    }
    if requested_baseline_ref is not _UNSET:
        kwargs["requested_baseline_ref"] = requested_baseline_ref
    backend = runtime_backend or _default_runtime_backend()
    return StudyRuntimeStartupContextSyncResult.from_payload(
        backend.update_quest_startup_context(**kwargs)
    )
