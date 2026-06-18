from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def runtime_health_events_path(*, study_root: Path, event_log_relative_path: Path) -> Path:
    return Path(study_root).expanduser().resolve() / event_log_relative_path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        payload = json.loads(text)
        if isinstance(payload, dict):
            events.append(dict(payload))
    return events


def stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_event_id(
    *,
    study_id: str,
    quest_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
) -> str:
    seed = stable_json(
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "event_type": event_type,
            "payload": dict(payload),
            "recorded_at": recorded_at,
            "sequence": sequence,
        }
    )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"runtime-health-event-{sequence:06d}-{digest}"


def event_source_signature(
    *,
    event_type: str,
    payload: Mapping[str, Any],
    stable_event_payload: Callable[[str, Mapping[str, Any]], dict[str, Any]],
) -> str:
    digest = hashlib.sha256(
        stable_json(
            {
                "event_type": event_type,
                "payload": stable_event_payload(event_type, payload),
            }
        ).encode("utf-8")
    ).hexdigest()[:24]
    return f"runtime-health-source::{event_type}::{digest}"


def source_signature_for_event(
    event: Mapping[str, Any],
    *,
    text: Callable[[object], str | None],
    mapping: Callable[[object], dict[str, Any]],
    stable_event_payload: Callable[[str, Mapping[str, Any]], dict[str, Any]],
) -> str:
    event_type = str(event.get("event_type") or "").strip()
    payload = mapping(event.get("payload"))
    return text(event.get("source_signature")) or event_source_signature(
        event_type=event_type,
        payload=payload,
        stable_event_payload=stable_event_payload,
    )


def snapshot_source_signature(
    events: list[dict[str, Any]],
    *,
    source_signature_for_event: Callable[[Mapping[str, Any]], str],
) -> str | None:
    if not events:
        return None
    digest = hashlib.sha256(
        stable_json(
            [
                {
                    "event_type": event.get("event_type"),
                    "source_signature": source_signature_for_event(event),
                }
                for event in events
            ]
        ).encode("utf-8")
    ).hexdigest()[:24]
    return f"runtime-health-snapshot::{digest}"
