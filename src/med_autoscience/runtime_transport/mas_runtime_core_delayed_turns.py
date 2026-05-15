from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def cancel_delayed_turn(
    *,
    quest_root: Path,
    source: str,
    reason: str,
    delayed_turn_path: Callable[[Path], Path],
    read_json: Callable[[Path], dict[str, Any]],
    text: Callable[[object], str | None],
    utc_now: Callable[[], str],
    append_runtime_event: Callable[..., None],
) -> dict[str, Any] | None:
    path = delayed_turn_path(quest_root)
    delayed = read_json(path)
    if not delayed:
        return None
    try:
        path.unlink()
    except FileNotFoundError:
        return None
    payload = {
        "status": "cancelled",
        "source": source,
        "reason": reason,
        "quest_id": text(delayed.get("quest_id")) or quest_root.name,
        "delayed_reason": text(delayed.get("reason")),
        "delayed_source": text(delayed.get("source")),
        "scheduled_at": text(delayed.get("scheduled_at")),
        "recorded_at": utc_now(),
    }
    append_runtime_event(
        quest_root=quest_root,
        event={
            "event": "delayed_turn_cancelled",
            "source": source,
            "recorded_at": payload["recorded_at"],
            "cancellation": payload,
        },
    )
    return payload


__all__ = ["cancel_delayed_turn"]
