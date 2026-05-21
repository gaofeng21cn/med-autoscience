from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport import mas_runtime_core_turn_state as turn_state
from med_autoscience.runtime_transport.mas_runtime_core_turn_utils import message_id as make_message_id


def load_message_queue(*, quest_root: Path) -> dict[str, Any]:
    return turn_state.load_message_queue(quest_root=quest_root)


def write_message_queue(*, quest_root: Path, queue: Mapping[str, Any]) -> None:
    turn_state.write_message_queue(quest_root=quest_root, queue=queue)


def queue_user_message(
    *,
    quest_root: Path,
    quest_id: str,
    content: str,
    source: str,
    recorded_at: str,
    reply_to_interaction_id: str | None = None,
    decision_response: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], int]:
    queue = load_message_queue(quest_root=quest_root)
    message = {
        "message_id": make_message_id(
            quest_id=quest_id,
            text=content,
            source=source,
            recorded_at=recorded_at,
        ),
        "content": content,
        "source": source,
        "reply_to_interaction_id": reply_to_interaction_id,
        "decision_response": dict(decision_response) if isinstance(decision_response, Mapping) else None,
        "recorded_at": recorded_at,
        "status": "pending",
    }
    queue["pending"].append(message)
    write_message_queue(quest_root=quest_root, queue=queue)
    return message, len(queue["pending"])


def claim_pending_user_messages(*, quest_root: Path, run_id: str, claimed_at: str) -> tuple[dict[str, Any], ...]:
    queue = load_message_queue(quest_root=quest_root)
    pending = [item for item in queue["pending"] if isinstance(item, dict)]
    if not pending:
        write_message_queue(quest_root=quest_root, queue=queue)
        return ()
    claimed: list[dict[str, Any]] = []
    for item in pending:
        claimed_item = {**item, "status": "completed", "claimed_by_run_id": run_id, "claimed_at": claimed_at}
        claimed.append(claimed_item)
    queue["pending"] = []
    queue["completed"].extend(claimed)
    write_message_queue(quest_root=quest_root, queue=queue)
    return tuple(claimed)


def restore_claimed_user_messages(*, quest_root: Path, run_id: str) -> None:
    queue = load_message_queue(quest_root=quest_root)
    restored: list[dict[str, Any]] = []
    remaining_completed: list[dict[str, Any]] = []
    for item in queue["completed"]:
        if isinstance(item, dict) and item.get("claimed_by_run_id") == run_id:
            restored_item = dict(item)
            restored_item["status"] = "pending"
            restored_item.pop("claimed_by_run_id", None)
            restored_item.pop("claimed_at", None)
            restored.append(restored_item)
        else:
            remaining_completed.append(item)
    if restored:
        queue["pending"] = restored + [item for item in queue["pending"] if isinstance(item, dict)]
        queue["completed"] = remaining_completed
        write_message_queue(quest_root=quest_root, queue=queue)
