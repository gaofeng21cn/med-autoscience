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
BLOCKED_CLOSEOUT_STATUS = "blocked"
BLOCKED_CLOSEOUT_RUNNER_STATUS = "blocked_waiting_for_user"
BLOCKED_CLOSEOUT_REASON = "blocked_turn_closeout_waiting_for_owner"


def blocked_closeout_wait_state(*, completion: Mapping[str, Any], run_id: str) -> dict[str, Any]:
    return {
        "continuation_policy": "wait_for_user_or_resume",
        "continuation_anchor": "turn_closeout",
        "continuation_reason": BLOCKED_CLOSEOUT_REASON,
        "blocked_turn_closeout": {
            "run_id": run_id,
            "closeout_path": _text(completion.get("closeout_path")),
            "blocked_reason": _text(completion.get("blocked_reason")),
            "next_owner": _text(completion.get("next_owner")),
        },
    }


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
    closeout = _read_json(closeout_path)
    closeout_fields = _closeout_fields(closeout)
    invalid_delta_refs = _invalid_meaningful_delta_refs(closeout)
    if invalid_delta_refs:
        return {
            "state": "incomplete",
            "reason": "invalid_meaningful_artifact_delta",
            "run_id": run_id,
            "raw_runner_status": normalized_runner_status,
            "normalized_runner_status": INCOMPLETE_RUNNER_STATUS,
            "closeout_path": str(closeout_path),
            "stdout_path": str(stdout_path),
            "stdout_event_count": stdout["event_count"],
            "stdout_open_item_count": stdout["open_item_count"],
            "stdout_turn_completed": stdout["turn_completed"],
            "invalid_artifact_refs": invalid_delta_refs,
            **closeout_fields,
        }
    blocked_closeout = closeout_fields["closeout_status"] == BLOCKED_CLOSEOUT_STATUS
    return {
        "state": "completed",
        "reason": "turn_closeout_blocked" if blocked_closeout else "turn_closeout_present",
        "run_id": run_id,
        "raw_runner_status": normalized_runner_status,
        "normalized_runner_status": BLOCKED_CLOSEOUT_RUNNER_STATUS if blocked_closeout else normalized_runner_status,
        "closeout_path": str(closeout_path),
        "stdout_path": str(stdout_path),
        "stdout_event_count": stdout["event_count"],
        "stdout_open_item_count": stdout["open_item_count"],
        "stdout_turn_completed": stdout["turn_completed"],
        **closeout_fields,
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
    closeout = _read_json(closeout_path)
    closeout_fields = _closeout_fields(closeout)
    blocked_closeout = closeout_fields["closeout_status"] == BLOCKED_CLOSEOUT_STATUS
    latest_receipt = _read_json(quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json")
    receipt_status = _text(latest_receipt.get("status"))
    return {
        "state": "completed",
        "reason": BLOCKED_CLOSEOUT_REASON if blocked_closeout else "logical_turn_completed",
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
        "completion_runner_status": BLOCKED_CLOSEOUT_RUNNER_STATUS if blocked_closeout else "succeeded",
        "target_status": "waiting_for_user" if blocked_closeout else "active",
        **closeout_fields,
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


def _closeout_fields(closeout: Mapping[str, Any]) -> dict[str, Any]:
    closeout_status = _text(closeout.get("status")) or "completed"
    meaningful_artifact_delta = closeout.get("meaningful_artifact_delta")
    return {
        "closeout_status": closeout_status,
        "meaningful_artifact_delta": meaningful_artifact_delta if isinstance(meaningful_artifact_delta, bool) else None,
        "blocked_reason": _text(closeout.get("blocked_reason")),
        "next_owner": _text(closeout.get("next_owner")),
    }


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


def _invalid_meaningful_delta_refs(closeout: Mapping[str, Any]) -> list[str]:
    if closeout.get("meaningful_artifact_delta") is not True:
        return []
    refs = closeout.get("artifact_refs")
    if not isinstance(refs, list):
        return ["<artifact_refs_missing>"]
    text_refs = [_text(item) for item in refs]
    concrete_refs = [item for item in text_refs if item is not None]
    if not concrete_refs:
        return ["<artifact_refs_empty>"]
    invalid_refs = [item for item in concrete_refs if _is_bookkeeping_artifact_ref(item)]
    return invalid_refs if len(invalid_refs) == len(concrete_refs) else []


def _is_bookkeeping_artifact_ref(ref: str) -> bool:
    normalized = ref.strip().replace("\\", "/").lstrip("./")
    parts = tuple(part.lower() for part in normalized.split("/") if part not in {"", "."})
    if "current_package" in parts or "submission_minimal" in parts:
        return True
    if parts and parts[-1] in {"current_package.zip", "current_package.tar.gz", "delivery_manifest.json"}:
        return True
    bookkeeping_subpaths = (
        ("artifacts", "autonomy"),
        ("artifacts", "controller"),
        ("artifacts", "reports"),
        ("artifacts", "runtime"),
        ("artifacts", "supervision"),
    )
    return any(_contains_subpath(parts, subpath) for subpath in bookkeeping_subpaths)


def _contains_subpath(parts: tuple[str, ...], subpath: tuple[str, ...]) -> bool:
    if len(parts) < len(subpath):
        return False
    return any(parts[index : index + len(subpath)] == subpath for index in range(len(parts) - len(subpath) + 1))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _text(value: object) -> str | None:
    rendered = str(value or "").strip()
    return rendered or None


def read_blocked_closeout_payload(path: Path) -> dict[str, Any] | None:
    closeout = _read_json(path)
    closeout_fields = _closeout_fields(closeout)
    if closeout_fields["closeout_status"] != BLOCKED_CLOSEOUT_STATUS:
        return None
    run_id = _text(closeout.get("run_id")) or path.stem
    return {
        "run_id": run_id,
        "closeout_path": str(path),
        **closeout_fields,
    }
