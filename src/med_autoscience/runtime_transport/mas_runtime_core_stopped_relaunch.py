from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport import mas_runtime_core_turns as turn_lifecycle


def relaunch_stopped_turn(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    reason: str,
    source: str,
) -> dict[str, Any]:
    state = turn_lifecycle.load_state(quest_root=quest_root)
    runtime_status = turn_lifecycle.text(state.get("status"))
    if runtime_status not in {"stopped", "failed"}:
        return turn_lifecycle.schedule_turn(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            reason=reason,
            source=source,
        )
    turn_lifecycle.persist_state(
        quest_root=quest_root,
        updates={
            "status": "active",
            "active_run_id": None,
            "worker_running": False,
            "worker_pending": False,
            "stop_requested": False,
            "pending_turn_reason": reason,
            "pending_turn_source": source,
            "last_relaunch_stopped": {
                "previous_status": runtime_status,
                "reason": reason,
                "source": source,
                "recorded_at": turn_lifecycle.utc_now(),
            },
        },
        source=source,
        event_name="stopped_runtime_relaunch_released",
    )
    return turn_lifecycle.start_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        reason=reason,
        source=source,
    )

