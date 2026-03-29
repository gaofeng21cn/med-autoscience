from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import quote
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


def enqueue_user_message(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
    message: str,
    source: str = "cli",
) -> dict[str, Any]:
    queue_path = quest_root / ".ds" / "user_message_queue.json"
    queue_payload = load_json(queue_path, default={"version": 1, "pending": [], "completed": []}) or {}
    pending = list(queue_payload.get("pending") or [])
    for item in pending:
        if item.get("content") == message:
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
    pending.append(record)
    queue_payload["pending"] = pending
    dump_json(queue_path, queue_payload)

    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    updated_runtime_state = load_json(runtime_state_path, default={}) or {}
    updated_runtime_state["pending_user_message_count"] = len(pending)
    dump_json(runtime_state_path, updated_runtime_state)

    append_jsonl(
        quest_root / ".ds" / "interaction_journal.jsonl",
        {
            "event_id": f"evt-{uuid4().hex[:8]}",
            "type": "user_inbound",
            "quest_id": str(runtime_state.get("quest_id") or quest_root.name),
            **record,
        },
    )
    return record


def post_quest_control(*, daemon_url: str, quest_id: str, action: str, source: str) -> dict[str, Any]:
    payload = json.dumps({"action": action, "source": source}, ensure_ascii=False).encode("utf-8")
    url = f"{daemon_url.rstrip('/')}/api/quests/{quote(quest_id)}/control"
    http_request = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    http_request.headers["Content-Type"] = "application/json"
    try:
        with request.urlopen(http_request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Quest control request failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Quest control request failed: {exc}") from exc
