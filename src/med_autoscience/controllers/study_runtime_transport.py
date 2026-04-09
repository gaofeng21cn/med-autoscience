from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_runtime_types import StudyRuntimeStartupContextSyncResult

_UNSET = object()

__all__ = [
    "_create_quest",
    "_inspect_quest_live_execution",
    "_pause_quest",
    "_resume_quest",
    "_update_quest_startup_context",
]


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


def _inspect_quest_live_execution(*, runtime_root: Path, quest_id: str) -> dict[str, Any]:
    return _router_module().med_deepscientist_transport.inspect_quest_live_execution(
        runtime_root=runtime_root,
        quest_id=quest_id,
    )


def _create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return _router_module().med_deepscientist_transport.create_quest(
        runtime_root=runtime_root,
        payload=payload,
    )


def _resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return _router_module().med_deepscientist_transport.resume_quest(
        runtime_root=runtime_root,
        quest_id=quest_id,
        source=source,
    )


def _pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return _router_module().med_deepscientist_transport.pause_quest(
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
) -> StudyRuntimeStartupContextSyncResult:
    kwargs: dict[str, Any] = {
        "runtime_root": runtime_root,
        "quest_id": quest_id,
        "startup_contract": startup_contract,
    }
    if requested_baseline_ref is not _UNSET:
        kwargs["requested_baseline_ref"] = requested_baseline_ref
    return StudyRuntimeStartupContextSyncResult.from_payload(
        _router_module().med_deepscientist_transport.update_quest_startup_context(**kwargs)
    )
