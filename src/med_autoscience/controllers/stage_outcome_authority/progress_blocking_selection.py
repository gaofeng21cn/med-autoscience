from __future__ import annotations

from collections.abc import Mapping
from typing import Any

def blocking_progress_allows_current_dispatch_selection(
    progress: Mapping[str, Any],
) -> bool:
    return _canonical_next_action(progress) is not None


def fresh_progress_envelope_blocks_dispatch_selection(
    progress: Mapping[str, Any],
) -> bool:
    if _canonical_next_action(progress) is not None:
        return False
    stage_closure = _mapping(progress.get("stage_closure"))
    outcome = _mapping(stage_closure.get("outcome"))
    return _text(outcome.get("kind")) in {"typed_blocker", "human_gate", "terminal"}


def _canonical_next_action(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    action = _mapping(progress.get("next_action"))
    if _text(action.get("surface_kind")) != "mas_next_action_envelope":
        return None
    return action


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "blocking_progress_allows_current_dispatch_selection",
    "fresh_progress_envelope_blocks_dispatch_selection",
]
