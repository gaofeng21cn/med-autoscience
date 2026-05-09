from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


TERMINAL_RECEIPT_STATUSES = frozenset(
    {
        "finished",
        "normalization_failed",
        "runner_unavailable",
    }
)


def inspect_logical_turn_completion(*, quest_root: Path, run_id: str | None) -> dict[str, Any] | None:
    if not run_id:
        return None
    closeout_path = quest_root / "artifacts" / "runtime" / "turn_closeouts" / f"{run_id}.json"
    if not closeout_path.is_file():
        return None
    stdout_path = quest_root / ".ds" / "runs" / run_id / "stdout.jsonl"
    stdout = _inspect_stdout(stdout_path)
    if not stdout["turn_completed"] or stdout["open_item_count"] != 0:
        return None
    latest_receipt = _read_json(quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json")
    receipt_status = _text(latest_receipt.get("status"))
    return {
        "state": "completed",
        "reason": "logical_turn_completed",
        "run_id": run_id,
        "closeout_path": str(closeout_path),
        "stdout_path": str(stdout_path),
        "stdout_event_count": stdout["event_count"],
        "latest_receipt_status": receipt_status,
        "latest_receipt_terminal": (
            _text(latest_receipt.get("run_id")) == run_id
            and receipt_status in TERMINAL_RECEIPT_STATUSES
        ),
    }


def _inspect_stdout(path: Path) -> dict[str, Any]:
    open_item_ids: set[str] = set()
    turn_completed = False
    event_count = 0
    if not path.is_file():
        return {
            "turn_completed": False,
            "open_item_count": 0,
            "event_count": 0,
        }
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, Mapping):
                continue
            event_count += 1
            event_type = _text(event.get("type"))
            item = event.get("item") if isinstance(event.get("item"), Mapping) else {}
            item_id = _text(item.get("id"))
            if event_type == "item.started" and item_id is not None:
                open_item_ids.add(item_id)
            elif event_type == "item.completed" and item_id is not None:
                open_item_ids.discard(item_id)
            elif event_type == "turn.completed":
                turn_completed = True
    return {
        "turn_completed": turn_completed,
        "open_item_count": len(open_item_ids),
        "event_count": event_count,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _text(value: object) -> str | None:
    rendered = str(value or "").strip()
    return rendered or None
