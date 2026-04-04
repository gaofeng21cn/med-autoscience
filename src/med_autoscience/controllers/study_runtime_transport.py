from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

__all__ = [
    "_create_quest",
    "_inspect_quest_live_execution",
    "_pause_quest",
    "_resume_quest",
    "_sync_completion_with_approval",
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
) -> dict[str, Any]:
    return _router_module().med_deepscientist_transport.update_quest_startup_context(
        runtime_root=runtime_root,
        quest_id=quest_id,
        startup_contract=startup_contract,
    )


def _sync_completion_with_approval(
    *,
    runtime_root: Path,
    quest_id: str,
    decision_request_payload: dict[str, Any],
    approval_text: str,
    summary: str,
    source: str,
) -> dict[str, Any]:
    return _router_module().med_deepscientist_transport.sync_completion_with_approval(
        runtime_root=runtime_root,
        quest_id=quest_id,
        decision_request_payload=decision_request_payload,
        approval_text=approval_text,
        summary=summary,
        source=source,
    )
