from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


_SCHEMA_VERSION = 1


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _texts(values: object) -> tuple[str, ...]:
    if not isinstance(values, list | tuple | set):
        value = _text(values)
        return (value,) if value is not None else ()
    return tuple(sorted({text for item in values if (text := _text(item))}))


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ControlIntentIdentity:
    study_id: str
    route_target: str
    work_unit_id: str
    blocker_authority_fingerprint: str
    controller_actions: tuple[str, ...]
    quest_id: str | None = None
    source_kind: str = "controller_intent"

    @property
    def business_key(self) -> str:
        return f"control-intent::{_digest(self._canonical_payload())}"

    @property
    def dedupe_key(self) -> str:
        return self.business_key

    def _canonical_payload(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "study_id": self.study_id,
            "quest_id": self.quest_id,
            "route_target": self.route_target,
            "work_unit_id": self.work_unit_id,
            "blocker_authority_fingerprint": self.blocker_authority_fingerprint,
            "controller_actions": list(self.controller_actions),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._canonical_payload(),
            "business_key": self.business_key,
            "dedupe_key": self.dedupe_key,
        }


def build_control_intent_identity(
    *,
    study_id: str,
    route_target: str,
    work_unit_id: str,
    blocker_authority_fingerprint: str,
    controller_actions: object,
    quest_id: str | None = None,
    source_kind: str = "controller_intent",
) -> ControlIntentIdentity:
    normalized_study_id = _text(study_id)
    normalized_route_target = _text(route_target)
    normalized_work_unit_id = _text(work_unit_id)
    normalized_fingerprint = _text(blocker_authority_fingerprint)
    normalized_actions = _texts(controller_actions)
    if (
        normalized_study_id is None
        or normalized_route_target is None
        or normalized_work_unit_id is None
        or normalized_fingerprint is None
        or not normalized_actions
    ):
        raise ValueError("control intent identity requires study, route, work unit, blocker authority, and action")
    return ControlIntentIdentity(
        study_id=normalized_study_id,
        quest_id=_text(quest_id),
        route_target=normalized_route_target,
        work_unit_id=normalized_work_unit_id,
        blocker_authority_fingerprint=normalized_fingerprint,
        controller_actions=normalized_actions,
        source_kind=_text(source_kind) or "controller_intent",
    )


def ledger_path(study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / "artifacts" / "runtime" / "control_intent_ledger" / "events.jsonl"


def append_event(
    *,
    study_root: Path,
    identity: ControlIntentIdentity,
    event_type: str,
    payload: Mapping[str, Any] | None = None,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    event_payload = dict(payload or {})
    timestamp = recorded_at or utc_now()
    event = {
        "schema_version": _SCHEMA_VERSION,
        "event_id": f"control-intent-event::{_digest({'business_key': identity.business_key, 'event_type': event_type, 'recorded_at': timestamp, 'payload': event_payload})}",
        "event_type": event_type,
        "recorded_at": timestamp,
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


def latest_event(*, study_root: Path, business_key: str) -> dict[str, Any] | None:
    latest: dict[str, Any] | None = None
    for event in read_events(study_root=study_root):
        identity = event.get("identity")
        if isinstance(identity, Mapping) and identity.get("business_key") == business_key:
            latest = event
    return latest
