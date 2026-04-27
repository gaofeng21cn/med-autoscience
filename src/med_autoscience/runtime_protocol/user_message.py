from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _pending_identity(item: Any) -> tuple[str, str] | None:
    if not isinstance(item, dict):
        return None
    dedupe_key = str(item.get("dedupe_key") or "").strip()
    if dedupe_key:
        return ("dedupe_key", dedupe_key)
    content = str(item.get("content") or "").strip()
    if content:
        return ("content", content)
    return None


def _compact_pending_messages(pending: list[Any]) -> tuple[list[dict[str, Any]], bool]:
    compacted: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    changed = False
    for item in pending:
        if not isinstance(item, dict):
            changed = True
            continue
        identity = _pending_identity(item)
        if identity is not None and identity in seen:
            changed = True
            continue
        if identity is not None:
            seen.add(identity)
        compacted.append(item)
    return compacted, changed


def _update_pending_count(*, quest_root: Path, pending_count: int) -> None:
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    updated_runtime_state = load_json(runtime_state_path, default={}) or {}
    updated_runtime_state["pending_user_message_count"] = pending_count
    dump_json(runtime_state_path, updated_runtime_state)


def enqueue_user_message(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
    message: str,
    source: str = "cli",
    dedupe_key: str | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    queue_path = resolved_quest_root / ".ds" / "user_message_queue.json"
    queue_payload = load_json(queue_path, default={"version": 1, "pending": [], "completed": []}) or {}
    pending, pending_compacted = _compact_pending_messages(list(queue_payload.get("pending") or []))
    if pending_compacted:
        queue_payload["pending"] = pending
        dump_json(queue_path, queue_payload)
        _update_pending_count(quest_root=resolved_quest_root, pending_count=len(pending))
    normalized_dedupe_key = str(dedupe_key or "").strip()
    for item in pending:
        if item.get("content") == message:
            return item
        if normalized_dedupe_key and item.get("dedupe_key") == normalized_dedupe_key:
            return item

    created_at = utc_now()
    record = {
        "message_id": f"msg-{uuid4().hex[:8]}",
        "source": source,
        "conversation_id": "local:default",
        "content": message,
        "created_at": created_at,
        "reply_to_interaction_id": runtime_state.get("active_interaction_id"),
        "attachments": [],
        "status": "queued",
    }
    if normalized_dedupe_key:
        record["dedupe_key"] = normalized_dedupe_key
    pending.append(record)
    queue_payload["pending"] = pending
    dump_json(queue_path, queue_payload)
    _update_pending_count(quest_root=resolved_quest_root, pending_count=len(pending))

    append_jsonl(
        resolved_quest_root / ".ds" / "interaction_journal.jsonl",
        {
            "event_id": f"evt-{uuid4().hex[:8]}",
            "type": "user_inbound",
            "quest_id": str(runtime_state.get("quest_id") or resolved_quest_root.name),
            **record,
        },
    )
    return record
