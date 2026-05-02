from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


_SCHEMA_VERSION = 1
AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY = "await_artifact_delta_or_gate_replay"
GATE_REREAD_REQUIRED = "gate_reread_required"
PLATFORM_REPAIR_REQUIRED = "platform_repair_required"
_LIFECYCLE_EVENT_TYPES = frozenset(
    {
        "planned",
        "dispatched",
        "delivered",
        "accepted",
        "artifact_written",
        "gate_replayed",
        "needs_specificity",
        GATE_REREAD_REQUIRED,
        "explicit_recovery",
        "closed",
        "superseded",
        PLATFORM_REPAIR_REQUIRED,
        "skipped_duplicate",
        AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY,
    }
)
_SUPERSEDING_EVENT_TYPES = frozenset(
    {
        "planned",
        "dispatched",
        "delivered",
        "accepted",
        AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY,
    }
)
_TERMINAL_EVENT_TYPES = frozenset(
    {
        "closed",
        "needs_specificity",
        "superseded",
        GATE_REREAD_REQUIRED,
        PLATFORM_REPAIR_REQUIRED,
    }
)
_ACTIVE_EVENT_TYPES = _LIFECYCLE_EVENT_TYPES - _TERMINAL_EVENT_TYPES
_CONSUMED_BLOCKING_EVENT_TYPES = _ACTIVE_EVENT_TYPES | (_TERMINAL_EVENT_TYPES - {"superseded"})
_ARTIFACT_DELTA_EVENT_TYPES = frozenset({"artifact_written"})
_DELIVERY_ANCHOR_EVENT_TYPES = frozenset({"planned", "dispatched", "delivered", "accepted"})
_DIRECT_BLOCK_REASON_EVENT_TYPES = frozenset(
    {
        "closed",
        "needs_specificity",
        GATE_REREAD_REQUIRED,
        PLATFORM_REPAIR_REQUIRED,
        AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY,
    }
)


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

    @property
    def supersession_key(self) -> str:
        return f"control-intent-series::{_digest(self._supersession_payload())}"

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

    def _supersession_payload(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "study_id": self.study_id,
            "quest_id": self.quest_id,
            "route_target": self.route_target,
            "controller_actions": list(self.controller_actions),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **self._canonical_payload(),
            "business_key": self.business_key,
            "dedupe_key": self.dedupe_key,
            "supersession_key": self.supersession_key,
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


def _event_record(
    *,
    identity_payload: Mapping[str, Any],
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    business_key = str(identity_payload.get("business_key") or "").strip()
    event_payload = dict(payload)
    return {
        "schema_version": _SCHEMA_VERSION,
        "event_id": f"control-intent-event::{_digest({'business_key': business_key, 'event_type': event_type, 'recorded_at': recorded_at, 'payload': event_payload})}",
        "event_type": event_type,
        "recorded_at": recorded_at,
        "identity": dict(identity_payload),
        "payload": event_payload,
    }


def _write_event(*, study_root: Path, event: Mapping[str, Any]) -> dict[str, Any]:
    path = ledger_path(study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    event_payload = dict(event)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event_payload, ensure_ascii=False, sort_keys=True) + "\n")
    return event_payload


def _event_type(event: Mapping[str, Any]) -> str | None:
    return _text(event.get("event_type"))


def _business_key(identity: Mapping[str, Any]) -> str | None:
    return _text(identity.get("business_key"))


def _supersession_key(identity: Mapping[str, Any]) -> str | None:
    existing = _text(identity.get("supersession_key"))
    if existing is not None:
        return existing
    study_id = _text(identity.get("study_id"))
    route_target = _text(identity.get("route_target"))
    controller_actions = _texts(identity.get("controller_actions"))
    if study_id is None or route_target is None or not controller_actions:
        return None
    payload = {
        'source_kind': _text(identity.get('source_kind')) or 'controller_intent',
        'study_id': study_id,
        'quest_id': _text(identity.get('quest_id')),
        'route_target': route_target,
        'controller_actions': list(controller_actions),
    }
    return f"control-intent-series::{_digest(payload)}"


def _active_events_by_business_key(
    *,
    study_root: Path,
    supersession_key: str,
) -> dict[str, dict[str, Any]]:
    active: dict[str, dict[str, Any]] = {}
    for event in read_events(study_root=study_root):
        identity = event.get("identity")
        if not isinstance(identity, Mapping):
            continue
        if _supersession_key(identity) != supersession_key:
            continue
        business_key = _business_key(identity)
        event_type = _event_type(event)
        if business_key is None or event_type is None:
            continue
        if event_type in _TERMINAL_EVENT_TYPES:
            active.pop(business_key, None)
            continue
        if event_type in _ACTIVE_EVENT_TYPES:
            active[business_key] = event
    return active


def _supersede_prior_active_intents(
    *,
    study_root: Path,
    identity: ControlIntentIdentity,
    event_type: str,
    recorded_at: str,
) -> None:
    active = _active_events_by_business_key(
        study_root=study_root,
        supersession_key=identity.supersession_key,
    )
    for business_key, previous in sorted(active.items()):
        if business_key == identity.business_key:
            continue
        previous_identity = previous.get("identity")
        if not isinstance(previous_identity, Mapping):
            continue
        payload = {
            "reason": "superseded_by_control_intent_change",
            "previous_event_type": _event_type(previous),
            "superseded_business_key": business_key,
            "superseding_business_key": identity.business_key,
            "superseding_event_type": event_type,
        }
        _write_event(
            study_root=study_root,
            event=_event_record(
                identity_payload=previous_identity,
                event_type="superseded",
                payload=payload,
                recorded_at=recorded_at,
            ),
        )


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
    if event_type in _SUPERSEDING_EVENT_TYPES:
        _supersede_prior_active_intents(
            study_root=study_root,
            identity=identity,
            event_type=event_type,
            recorded_at=timestamp,
        )
    return _write_event(
        study_root=study_root,
        event=_event_record(
            identity_payload=identity.to_dict(),
            event_type=event_type,
            payload=event_payload,
            recorded_at=timestamp,
        ),
    )


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


def events_for_business_key(*, study_root: Path, business_key: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for event in read_events(study_root=study_root):
        identity = event.get("identity")
        if isinstance(identity, Mapping) and identity.get("business_key") == business_key:
            events.append(event)
    return events


def artifact_delta_observed(events: list[dict[str, Any]]) -> bool:
    anchor_index = -1
    for index, event in enumerate(events):
        if _event_type(event) in _DELIVERY_ANCHOR_EVENT_TYPES:
            anchor_index = index
    scoped_events = events[anchor_index + 1 :] if anchor_index >= 0 else events
    for event in scoped_events:
        payload = event.get("payload")
        if _event_type(event) in _ARTIFACT_DELTA_EVENT_TYPES:
            return True
        if isinstance(payload, Mapping) and payload.get("artifact_delta") is True:
            return True
    return False


def lifecycle_state(*, study_root: Path, identity: ControlIntentIdentity) -> dict[str, Any]:
    events = events_for_business_key(study_root=study_root, business_key=identity.business_key)
    if not events:
        return {
            "schema_version": _SCHEMA_VERSION,
            "business_key": identity.business_key,
            "supersession_key": identity.supersession_key,
            "lifecycle_state": "new",
            "latest_event_type": None,
            "artifact_delta_observed": False,
            "delivery_blocked": False,
            "block_reason": None,
        }
    latest = events[-1]
    latest_type = _event_type(latest)
    has_artifact_delta = artifact_delta_observed(events)
    delivery_blocked = latest_type in _CONSUMED_BLOCKING_EVENT_TYPES
    block_reason: str | None = None
    if latest_type in _DIRECT_BLOCK_REASON_EVENT_TYPES:
        block_reason = latest_type
    elif latest_type == "skipped_duplicate":
        payload = latest.get("payload")
        block_reason = _text(payload.get("reason")) if isinstance(payload, Mapping) else None
        block_reason = block_reason or "skipped_duplicate"
    elif latest_type == AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY:
        block_reason = AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY
    elif delivery_blocked and not has_artifact_delta:
        block_reason = "same_fingerprint_no_artifact_delta"
    elif delivery_blocked:
        block_reason = "same_fingerprint_artifact_delta_observed"
    return {
        "schema_version": _SCHEMA_VERSION,
        "business_key": identity.business_key,
        "supersession_key": identity.supersession_key,
        "lifecycle_state": latest_type or "unknown",
        "latest_event_type": latest_type,
        "latest_recorded_at": _text(latest.get("recorded_at")),
        "artifact_delta_observed": has_artifact_delta,
        "delivery_blocked": delivery_blocked,
        "terminal_consumed": latest_type in _TERMINAL_EVENT_TYPES and latest_type != "superseded",
        "block_reason": block_reason,
    }


def append_skipped_duplicate_if_needed(
    *,
    study_root: Path,
    identity: ControlIntentIdentity,
    payload: Mapping[str, Any] | None = None,
    recorded_at: str | None = None,
) -> dict[str, Any] | None:
    latest = latest_event(study_root=study_root, business_key=identity.business_key)
    if isinstance(latest, Mapping) and _event_type(latest) == "skipped_duplicate":
        return None
    return append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload=payload,
        recorded_at=recorded_at,
    )
