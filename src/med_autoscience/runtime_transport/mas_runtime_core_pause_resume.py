from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def release_paused_explicit_resume(
    *,
    quest_root: Path,
    state: Mapping[str, Any],
    reason: str,
    source: str,
    allow_paused_explicit_resume: bool,
    text: Callable[[object], str | None],
    utc_now: Callable[[], str],
    persist_state: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    runtime_status = text(state.get("status"))
    if not (
        allow_paused_explicit_resume
        and runtime_status == "paused"
        and reason == "explicit_resume"
        and text(state.get("active_run_id")) is None
        and state.get("worker_running") is not True
    ):
        return None
    return persist_state(
        quest_root=quest_root,
        updates={
            "status": "active",
            "active_run_id": None,
            "worker_running": False,
            "worker_pending": False,
            "stop_requested": False,
            "pending_turn_reason": None,
            "pending_turn_source": None,
            "last_paused_explicit_resume": {
                "source": source,
                "reason": reason,
                "previous_status": runtime_status,
                "released_at": utc_now(),
            },
        },
        source=source,
        event_name="paused_explicit_resume_released",
    )


__all__ = ["release_paused_explicit_resume"]
