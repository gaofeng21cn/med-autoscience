from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


def action_queue_with_terminal_publication_handoff(
    *,
    actions: list[dict[str, Any]],
    progress: Mapping[str, Any],
    study_id: str,
    quest_id: str | None,
    decorate_action: Callable[..., dict[str, Any]],
    publication_eval_payload: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    del progress, study_id, quest_id, decorate_action, publication_eval_payload
    return actions


def projection_fields(
    progress: Mapping[str, Any],
    actions: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    stage_artifact_index = _mapping(progress.get("stage_artifact_index"))
    next_action = _mapping(progress.get("next_action"))
    if stage_artifact_index.get("surface_kind") == "stage_artifact_index":
        result["stage_artifact_index"] = stage_artifact_index
    if next_action.get("surface_kind") == "mas_next_action_envelope":
        result["next_action"] = next_action
    del actions
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "action_queue_with_terminal_publication_handoff",
    "projection_fields",
]
