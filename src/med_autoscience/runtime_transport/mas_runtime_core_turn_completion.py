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
INCOMPLETE_RUNNER_STATUS = "runner_incomplete"
RETRYABLE_RUNNER_STATUSES = frozenset({"failed", "error", "timeout", "runner_failed", INCOMPLETE_RUNNER_STATUS})
STALE_COMPLETION_STATUS = "stale_completion_ignored"


def inspect_runner_completion(
    *,
    quest_root: Path,
    run_id: str | None,
    runner_status: str,
) -> dict[str, Any]:
    normalized_runner_status = _text(runner_status) or "succeeded"
    if normalized_runner_status != "succeeded" or not run_id:
        return {
            "state": "not_checked",
            "reason": "runner_status_not_success" if normalized_runner_status != "succeeded" else "run_id_missing",
            "run_id": run_id,
            "raw_runner_status": normalized_runner_status,
            "normalized_runner_status": normalized_runner_status,
        }
    closeout_path = quest_root / "artifacts" / "runtime" / "turn_closeouts" / f"{run_id}.json"
    stdout_path = quest_root / ".ds" / "runs" / run_id / "stdout.jsonl"
    if not closeout_path.is_file() and not stdout_path.is_file():
        return {
            "state": "not_checked",
            "reason": "runner_surfaces_missing",
            "run_id": run_id,
            "raw_runner_status": normalized_runner_status,
            "normalized_runner_status": normalized_runner_status,
        }
    stdout = _inspect_stdout(stdout_path)
    if not closeout_path.is_file():
        return {
            "state": "incomplete",
            "reason": "missing_turn_closeout",
            "run_id": run_id,
            "raw_runner_status": normalized_runner_status,
            "normalized_runner_status": INCOMPLETE_RUNNER_STATUS,
            "closeout_path": str(closeout_path),
            "stdout_path": str(stdout_path),
            "stdout_event_count": stdout["event_count"],
            "stdout_open_item_count": stdout["open_item_count"],
            "stdout_turn_completed": stdout["turn_completed"],
        }
    if stdout["open_item_count"] != 0:
        return {
            "state": "incomplete",
            "reason": "stdout_items_still_open",
            "run_id": run_id,
            "raw_runner_status": normalized_runner_status,
            "normalized_runner_status": INCOMPLETE_RUNNER_STATUS,
            "closeout_path": str(closeout_path),
            "stdout_path": str(stdout_path),
            "stdout_event_count": stdout["event_count"],
            "stdout_open_item_count": stdout["open_item_count"],
            "stdout_turn_completed": stdout["turn_completed"],
        }
    return {
        "state": "completed",
        "reason": "turn_closeout_present",
        "run_id": run_id,
        "raw_runner_status": normalized_runner_status,
        "normalized_runner_status": normalized_runner_status,
        "closeout_path": str(closeout_path),
        "stdout_path": str(stdout_path),
        "stdout_event_count": stdout["event_count"],
        "stdout_open_item_count": stdout["open_item_count"],
        "stdout_turn_completed": stdout["turn_completed"],
    }


def inspect_logical_turn_completion(*, quest_root: Path, run_id: str | None) -> dict[str, Any] | None:
    if not run_id:
        return None
    closeout_path = quest_root / "artifacts" / "runtime" / "turn_closeouts" / f"{run_id}.json"
    if not closeout_path.is_file():
        return None
    stdout_path = quest_root / ".ds" / "runs" / run_id / "stdout.jsonl"
    stdout = _inspect_stdout(stdout_path)
    if stdout["open_item_count"] != 0:
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
        "stdout_turn_completed": stdout["turn_completed"],
        "latest_receipt_status": receipt_status,
        "latest_receipt_terminal": (
            _text(latest_receipt.get("run_id")) == run_id
            and receipt_status in TERMINAL_RECEIPT_STATUSES
        ),
    }


def stale_runner_completion_result(
    *,
    previous: Mapping[str, Any],
    quest_id: str,
    run_id: str,
    runner_status: str,
    source: str,
    recorded_at: str,
    backend_id: str,
    snapshot_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    active_run_id = _text(previous.get("active_run_id"))
    if active_run_id == run_id:
        return None
    if active_run_id is None and previous.get("worker_running") is not True:
        return None
    payload = {
        "event": "stale_runner_completion_ignored",
        "source": source,
        "recorded_at": recorded_at,
        "quest_id": quest_id,
        "run_id": run_id,
        "active_run_id": active_run_id,
        "runner_status": _text(runner_status) or "succeeded",
        "worker_running": previous.get("worker_running") is True,
    }
    return {
        "ok": False,
        "status": STALE_COMPLETION_STATUS,
        "source": backend_id,
        "quest_id": quest_id,
        "run_id": run_id,
        "active_run_id": active_run_id,
        "snapshot": dict(snapshot_payload),
        "next_turn": None,
        "ignored_completion": payload,
    }


def status_after_runner(runner_status: str) -> str:
    if runner_status in RETRYABLE_RUNNER_STATUSES:
        return "active"
    if runner_status in {"stopped", "paused", "completed", "failed", "error", "cancelled"}:
        return runner_status
    if runner_status in {"waiting_for_user", "blocked_waiting_for_user"}:
        return "waiting_for_user"
    if runner_status in {"failed", "error"}:
        return "failed"
    return "active"


def next_retry_state(
    *,
    previous: Mapping[str, Any],
    runner_status: str,
    max_attempts: int,
    backoff_base_seconds: float,
) -> dict[str, Any] | None:
    if runner_status not in RETRYABLE_RUNNER_STATUSES:
        return None
    previous_retry = previous.get("retry_state") if isinstance(previous.get("retry_state"), Mapping) else {}
    attempt = int(previous_retry.get("attempt") or 0) + 1
    return {
        "attempt": attempt,
        "max_attempts": max_attempts,
        "next_delay_seconds": backoff_base_seconds * (2 ** max(0, attempt - 1)),
        "last_runner_status": runner_status,
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
