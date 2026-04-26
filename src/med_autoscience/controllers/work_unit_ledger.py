from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.control_identity import ControlWorkUnitIdentity


_SCHEMA_VERSION = 1


def ledger_path(study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / "artifacts" / "runtime" / "work_unit_ledger" / "events.jsonl"


def _event_id(*, identity: ControlWorkUnitIdentity, event_type: str, recorded_at: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        {
            "dispatch_key": identity.dispatch_key,
            "event_type": event_type,
            "recorded_at": recorded_at,
            "payload": payload,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"work-unit-event::{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:20]}"


def append_event(
    *,
    study_root: Path,
    identity: ControlWorkUnitIdentity,
    event_type: str,
    payload: Mapping[str, Any] | None = None,
    recorded_at: str,
) -> dict[str, Any]:
    event_payload = dict(payload or {})
    event = {
        "schema_version": _SCHEMA_VERSION,
        "event_id": _event_id(
            identity=identity,
            event_type=event_type,
            recorded_at=recorded_at,
            payload=event_payload,
        ),
        "event_type": event_type,
        "recorded_at": recorded_at,
        "identity": identity.to_dict(),
        "payload": event_payload,
    }
    path = ledger_path(study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def read_events(*, study_root: Path) -> list[dict[str, Any]]:
    path = ledger_path(study_root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            events.append(payload)
    return events


def latest_event(*, study_root: Path, dispatch_key: str) -> dict[str, Any] | None:
    latest: dict[str, Any] | None = None
    for event in read_events(study_root=study_root):
        identity = event.get("identity")
        if isinstance(identity, Mapping) and identity.get("dispatch_key") == dispatch_key:
            latest = event
    return latest
