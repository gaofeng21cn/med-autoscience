from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DIRECT_FOREGROUND_COMPLETION_GLOB = "direct_foreground_*_completion_*.json"


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalized_strings(values: list[object]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            normalized.append(text)
    return normalized


def _normalize_timestamp(value: object) -> datetime | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _surface_emitted_at(payload: dict[str, Any] | None) -> datetime | None:
    if not isinstance(payload, dict):
        return None
    return _normalize_timestamp(
        payload.get("emitted_at")
        or payload.get("generated_at")
        or payload.get("created_at")
        or payload.get("completed_at")
    )


def _latest_direct_foreground_completion(*, task_intake_root: Path | None) -> dict[str, Any] | None:
    if task_intake_root is None:
        return None
    root = Path(task_intake_root).expanduser().resolve()
    if not root.exists():
        return None
    candidates: list[tuple[datetime, str, dict[str, Any]]] = []
    for path in root.glob(DIRECT_FOREGROUND_COMPLETION_GLOB):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        timestamp = _surface_emitted_at(payload)
        if timestamp is None:
            try:
                timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
        candidates.append((timestamp, path.name, payload))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def _direct_foreground_completion_confirms_task(
    *,
    task_intake_payload: dict[str, Any] | None,
    completion_payload: dict[str, Any] | None,
) -> bool:
    if not isinstance(task_intake_payload, dict) or not isinstance(completion_payload, dict):
        return False
    task_intake_emitted_at = _surface_emitted_at(task_intake_payload)
    completion_emitted_at = _surface_emitted_at(completion_payload)
    if (
        task_intake_emitted_at is None
        or completion_emitted_at is None
        or completion_emitted_at < task_intake_emitted_at
    ):
        return False
    task_id = _non_empty_text(task_intake_payload.get("task_id"))
    referenced_task_id = _non_empty_text(
        completion_payload.get("source_task_id") or completion_payload.get("retired_task_intake_id")
    )
    if task_id is not None and referenced_task_id is not None and referenced_task_id != task_id:
        return False
    event_id = (_non_empty_text(completion_payload.get("event_id")) or "").lower()
    record_type = (_non_empty_text(completion_payload.get("record_type")) or "").lower()
    if not event_id.startswith("direct-foreground-") and not record_type.startswith("direct_foreground_"):
        return False
    completed_scope = _normalized_strings(completion_payload.get("completed_scope") or [])
    if not completed_scope:
        return False
    scope_text = "\n".join(completed_scope).lower()
    required_markers = (
        "paper/submission_minimal",
        "manuscript/current_package",
        "current_package.zip",
    )
    if any(marker not in scope_text for marker in required_markers):
        return False
    unchanged_boundaries = {
        item.lower()
        for item in _normalized_strings(completion_payload.get("unchanged_boundaries") or [])
    }
    return {"endpoint", "cohort definition", "model results", "claim boundary"}.issubset(
        unchanged_boundaries
    )


def task_intake_yields_to_direct_foreground_completion(
    payload: dict[str, Any] | None,
    *,
    task_intake_root: Path | None,
) -> bool:
    return _direct_foreground_completion_confirms_task(
        task_intake_payload=payload,
        completion_payload=_latest_direct_foreground_completion(task_intake_root=task_intake_root),
    )
