from __future__ import annotations

from collections.abc import Mapping
from typing import Any

def legal_hard_stop_blocks_dispatch_selection(
    progress: Mapping[str, Any],
) -> bool:
    stage_closure = _mapping(progress.get("stage_closure"))
    outcome = _mapping(stage_closure.get("outcome"))
    kind = _text(outcome.get("kind"))
    if kind == "human_gate":
        return True
    if kind != "typed_blocker":
        return False
    blocker = _mapping(outcome.get("typed_blocker")) or outcome
    return blocker.get("blocks_stage_transition") is True


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "legal_hard_stop_blocks_dispatch_selection",
]
