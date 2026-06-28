from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


CONTROL_PLANE_MESSAGE_SOURCES = {
    "codex-data-asset-gate",
    "codex-medical-publication-surface",
    "codex-publication-gate",
}


def pending_count(value: Mapping[str, Any]) -> int:
    try:
        return int(value.get("pending_user_message_count") or 0)
    except (TypeError, ValueError):
        return 0


def only_control_plane_messages(*, runtime_state_path: Path, expected_count: int | None = None) -> bool:
    queue = _read_queue(runtime_state_path.parent / "user_message_queue.json")
    pending = queue.get("pending")
    if not isinstance(pending, list) or not pending:
        return False
    records = [item for item in pending if isinstance(item, Mapping)]
    if len(records) != len(pending):
        return False
    if expected_count is not None and len(records) != expected_count:
        return False
    return all(_is_control_plane_message(item) for item in records)


def _is_control_plane_message(item: Mapping[str, Any]) -> bool:
    source = str(item.get("source") or "").strip()
    if source not in CONTROL_PLANE_MESSAGE_SOURCES:
        return False
    content = str(item.get("content") or "").strip()
    return "control message from Codex orchestration layer" in content


def _read_queue(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


__all__ = ["only_control_plane_messages", "pending_count"]
