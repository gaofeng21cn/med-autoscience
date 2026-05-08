from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
import os
import subprocess


def message_id(*, quest_id: str, text: str, source: str, recorded_at: str) -> str:
    payload = json.dumps(
        {"quest_id": quest_id, "text": text, "source": source, "recorded_at": recorded_at},
        ensure_ascii=False,
        sort_keys=True,
    )
    return f"msg-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def idempotency_key(*, quest_id: str, reason: str, source: str, active_run_id: str | None) -> str:
    payload = json.dumps(
        {"quest_id": quest_id, "reason": reason, "source": source, "active_run_id": active_run_id},
        sort_keys=True,
    )
    return f"turn-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:20]}"


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def runner_unavailable(receipt: Mapping[str, object]) -> bool:
    return receipt.get("fail_closed") is True or receipt.get("available") is False


def pid_live(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def command_available(binary: str) -> bool:
    return subprocess.run(["/usr/bin/env", "which", binary], text=True, capture_output=True, check=False).returncode == 0


def text(value: object) -> str | None:
    rendered = str(value or "").strip()
    return rendered or None
