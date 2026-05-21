from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport.mas_runtime_core_turn_paths import (
    event_log_path,
    queue_path,
    state_path,
)
from med_autoscience.runtime_transport.mas_runtime_core_turn_policy import BACKEND_ID, ENGINE_ID
from med_autoscience.runtime_transport.mas_runtime_core_turn_utils import text


_NOW: Callable[[], datetime] = lambda: datetime.now(UTC)


def set_clock_for_tests(clock: Callable[[], datetime]) -> None:
    global _NOW
    _NOW = clock


def reset_clock_for_tests() -> None:
    global _NOW
    _NOW = lambda: datetime.now(UTC)


def now() -> datetime:
    return _NOW().astimezone(UTC)


def utc_now() -> str:
    return now().replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def load_state(*, quest_root: Path) -> dict[str, Any]:
    state = read_json(state_path(quest_root))
    state.setdefault("quest_id", quest_root.name)
    state.setdefault("runtime_backend_id", BACKEND_ID)
    state.setdefault("runtime_engine_id", ENGINE_ID)
    state.setdefault("external_mds_required", False)
    state.setdefault("continuation_policy", "auto")
    state["pending_user_message_count"] = int(state.get("pending_user_message_count") or 0)
    return state


def append_runtime_event(*, quest_root: Path, event: Mapping[str, Any]) -> None:
    append_jsonl(event_log_path(quest_root), event)


def persist_state(
    *,
    quest_root: Path,
    updates: Mapping[str, Any],
    source: str,
    event_name: str,
    delete_keys: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    recorded_at = utc_now()
    previous = load_state(quest_root=quest_root)
    for key in delete_keys or ():
        previous.pop(key, None)
    payload = {
        **previous,
        **dict(updates),
        "quest_id": quest_root.name,
        "runtime_backend_id": BACKEND_ID,
        "runtime_engine_id": ENGINE_ID,
        "external_mds_required": False,
        "source": source,
        "updated_at": recorded_at,
    }
    payload.setdefault("continuation_policy", "auto")
    payload["pending_user_message_count"] = int(payload.get("pending_user_message_count") or 0)
    write_json(state_path(quest_root), payload)
    append_runtime_event(
        quest_root=quest_root,
        event={"event": event_name, "source": source, "recorded_at": recorded_at, "snapshot": payload},
    )
    return payload


def load_message_queue(*, quest_root: Path) -> dict[str, Any]:
    payload = read_json(queue_path(quest_root))
    pending = payload.get("pending") if isinstance(payload.get("pending"), list) else []
    completed = payload.get("completed") if isinstance(payload.get("completed"), list) else []
    return {"schema_version": 1, "pending": list(pending), "completed": list(completed)}


def write_message_queue(*, quest_root: Path, queue: Mapping[str, Any]) -> None:
    write_json(queue_path(quest_root), queue)


def snapshot(*, quest_root: Path, state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    runtime_state = dict(state or load_state(quest_root=quest_root))
    active_run_id = text(runtime_state.get("active_run_id"))
    return {
        "quest_id": str(runtime_state.get("quest_id") or quest_root.name),
        "status": text(runtime_state.get("status")),
        "active_run_id": active_run_id,
        "runtime_backend_id": str(runtime_state.get("runtime_backend_id") or BACKEND_ID),
        "runtime_engine_id": str(runtime_state.get("runtime_engine_id") or ENGINE_ID),
        "worker_running": runtime_state.get("worker_running") if isinstance(runtime_state.get("worker_running"), bool) else None,
        "worker_pending": runtime_state.get("worker_pending") if isinstance(runtime_state.get("worker_pending"), bool) else None,
        "stop_requested": runtime_state.get("stop_requested") if isinstance(runtime_state.get("stop_requested"), bool) else None,
        "pending_user_message_count": int(runtime_state.get("pending_user_message_count") or 0),
        "continuation_policy": text(runtime_state.get("continuation_policy")) or "auto",
        "updated_at": text(runtime_state.get("updated_at")),
    }
