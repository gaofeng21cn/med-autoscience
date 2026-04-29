from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.control_identity import ControlWorkUnitIdentity


_SCHEMA_VERSION = 1
_LIFECYCLE_EVENT_TYPES = frozenset(
    {
        "planned",
        "proposed",
        "dispatched",
        "accepted",
        "artifact_written",
        "gate_replayed",
        "closed",
        "needs_specificity",
        "superseded",
        "skipped_duplicate",
    }
)
_TERMINAL_EVENT_TYPES = frozenset({"closed", "needs_specificity", "superseded"})


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
    resolved_event_type = event_type
    if event_type == "accepted":
        existing = latest_active_accepted_writer(
            study_root=study_root,
            quest_id=identity.quest_id,
            dispatch_key=identity.dispatch_key,
        )
        writer_id = _non_empty_text(event_payload.get("writer_id"))
        if existing is not None and writer_id is not None and existing != writer_id:
            resolved_event_type = "superseded"
            event_payload["accepted_writer_id"] = existing
            event_payload["superseded_writer_id"] = writer_id
    event = {
        "schema_version": _SCHEMA_VERSION,
        "event_id": _event_id(
            identity=identity,
            event_type=resolved_event_type,
            recorded_at=recorded_at,
            payload=event_payload,
        ),
        "event_type": resolved_event_type,
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


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def latest_active_accepted_writer(
    *,
    study_root: Path,
    quest_id: str | None,
    dispatch_key: str,
) -> str | None:
    accepted_writer: str | None = None
    for event in read_events(study_root=study_root):
        identity = event.get("identity")
        if not isinstance(identity, Mapping):
            continue
        if identity.get("dispatch_key") != dispatch_key:
            continue
        if identity.get("quest_id") != quest_id:
            continue
        event_type = _non_empty_text(event.get("event_type"))
        if event_type in _TERMINAL_EVENT_TYPES:
            accepted_writer = None
            continue
        if event_type == "accepted":
            payload = event.get("payload")
            writer_id = _non_empty_text(payload.get("writer_id")) if isinstance(payload, Mapping) else None
            if writer_id is not None:
                accepted_writer = writer_id
    return accepted_writer


def lifecycle_summary(*, study_root: Path) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in read_events(study_root=study_root):
        identity = event.get("identity")
        dispatch_key = _non_empty_text(identity.get("dispatch_key")) if isinstance(identity, Mapping) else None
        event_type = _non_empty_text(event.get("event_type"))
        if dispatch_key is None or event_type not in _LIFECYCLE_EVENT_TYPES:
            continue
        grouped.setdefault(dispatch_key, []).append(event)

    units: list[dict[str, Any]] = []
    state_counts: Counter[str] = Counter()
    replay_count = 0
    specificity_request_count = 0
    for dispatch_key, unit_events in sorted(grouped.items()):
        ordered = sorted(unit_events, key=lambda event: _non_empty_text(event.get("recorded_at")) or "")
        event_types = [_non_empty_text(event.get("event_type")) for event in ordered]
        compact_event_types = [event_type for event_type in event_types if event_type is not None]
        latest = ordered[-1]
        latest_type = _non_empty_text(latest.get("event_type")) or "unknown"
        identity = latest.get("identity") if isinstance(latest.get("identity"), Mapping) else {}
        accepted_writer_id: str | None = None
        for event in ordered:
            if _non_empty_text(event.get("event_type")) != "accepted":
                continue
            payload = event.get("payload")
            writer_id = _non_empty_text(payload.get("writer_id")) if isinstance(payload, Mapping) else None
            if writer_id is not None:
                accepted_writer_id = writer_id
                break
        replay_events = [event for event in ordered if _non_empty_text(event.get("event_type")) == "gate_replayed"]
        specificity_events = [event for event in ordered if _non_empty_text(event.get("event_type")) == "needs_specificity"]
        replay_count += len(replay_events)
        specificity_request_count += len(specificity_events)
        state_counts[latest_type] += 1
        units.append(
            {
                "dispatch_key": dispatch_key,
                "study_id": _non_empty_text(identity.get("study_id")) if isinstance(identity, Mapping) else None,
                "quest_id": _non_empty_text(identity.get("quest_id")) if isinstance(identity, Mapping) else None,
                "lane": _non_empty_text(identity.get("lane")) if isinstance(identity, Mapping) else None,
                "unit_id": _non_empty_text(identity.get("unit_id")) if isinstance(identity, Mapping) else None,
                "action_type": _non_empty_text(identity.get("action_type")) if isinstance(identity, Mapping) else None,
                "lifecycle_state": latest_type,
                "accepted_writer_id": accepted_writer_id,
                "event_types": compact_event_types,
                "event_count": len(ordered),
                "first_recorded_at": _non_empty_text(ordered[0].get("recorded_at")),
                "latest_recorded_at": _non_empty_text(latest.get("recorded_at")),
                "latest_gate_replayed_at": (
                    _non_empty_text(replay_events[-1].get("recorded_at")) if replay_events else None
                ),
            }
        )
    return {
        "schema_version": _SCHEMA_VERSION,
        "ledger_path": str(ledger_path(study_root)),
        "totals": {
            "unit_count": len(units),
            "replay_count": replay_count,
            "specificity_request_count": specificity_request_count,
            "state_counts": dict(sorted(state_counts.items())),
        },
        "units": units,
    }
