from __future__ import annotations

from pathlib import Path


def state_path(quest_root: Path) -> Path:
    return quest_root / ".ds" / "runtime_state.json"


def event_log_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "mas_runtime_events.jsonl"


def queue_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "user_message_queue.json"


def turn_receipts_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "turn_receipts.jsonl"


def delayed_turn_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "delayed_turns.json"


def run_root(*, quest_root: Path, run_id: str) -> Path:
    return quest_root / ".ds" / "runs" / run_id


def worker_lease_path(*, quest_root: Path, run_id: str) -> Path:
    return run_root(quest_root=quest_root, run_id=run_id) / "worker_lease.json"


__all__ = [
    "delayed_turn_path",
    "event_log_path",
    "queue_path",
    "run_root",
    "state_path",
    "turn_receipts_path",
    "worker_lease_path",
]
