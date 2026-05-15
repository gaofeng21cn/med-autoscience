from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def terminal_runtime_schedule_block(
    *,
    quest_root: Path,
    quest_id: str,
    reason: str,
    state: Mapping[str, Any],
    runtime_status: str,
    backend_id: str,
    text: Callable[[object], str | None],
    snapshot: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "blocked",
        "source": backend_id,
        "quest_id": quest_id,
        "active_run_id": text(state.get("active_run_id")),
        "scheduled": False,
        "started": False,
        "queued": False,
        "reason": reason,
        "turn_reason": reason,
        "blocked_reason": "terminal_runtime_state",
        "runtime_status": runtime_status,
        "snapshot": snapshot(quest_root=quest_root, state=state),
    }


__all__ = ["terminal_runtime_schedule_block"]
