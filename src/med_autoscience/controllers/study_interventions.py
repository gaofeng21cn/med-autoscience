from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
EVENT_LOG_RELATIVE_PATH = Path("artifacts") / "interventions" / "events.jsonl"
INTERVENTION_INTENTS = frozenset({"user_decision", "new_plan", "abandon", "submit_info"})
STORAGE_POLICY = {"primary_store": "file", "sqlite_role": "index_only"}


def intervention_events_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / EVENT_LOG_RELATIVE_PATH


def read_intervention_events(*, study_root: Path) -> list[dict[str, Any]]:
    path = intervention_events_path(study_root=study_root)
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        payload = json.loads(text)
        if isinstance(payload, Mapping):
            events.append(dict(payload))
    return events


def append_intervention_event(
    *,
    study_root: Path,
    study_id: str,
    intent: str,
    payload: Mapping[str, Any] | None = None,
    recorded_at: str,
    actor: str = "user",
    source: str = "manual",
    agent_handoff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    intent_text = _text(intent)
    if intent_text not in INTERVENTION_INTENTS:
        raise ValueError(f"unknown study intervention intent: {intent}")
    resolved_payload = dict(payload or {})
    resolved_agent_handoff = _mapping(agent_handoff)
    path = intervention_events_path(study_root=study_root)
    sequence = len(read_intervention_events(study_root=study_root)) + 1
    event = {
        "schema_version": SCHEMA_VERSION,
        "surface": "study_intervention_event",
        "event_id": _event_id(
            study_id=study_id,
            intent=intent_text,
            payload=resolved_payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ),
        "sequence": sequence,
        "study_id": study_id,
        "intent": intent_text,
        "actor": _text(actor) or "user",
        "source": _text(source) or "manual",
        "recorded_at": recorded_at,
        "payload": resolved_payload,
        "storage_policy": dict(STORAGE_POLICY),
    }
    if resolved_agent_handoff:
        event["agent_handoff"] = resolved_agent_handoff
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def build_truth_event_input(event: Mapping[str, Any]) -> dict[str, Any]:
    intent = _required_text(event.get("intent"), field="intent")
    if intent not in INTERVENTION_INTENTS:
        raise ValueError(f"unknown study intervention intent: {intent}")
    event_id = _required_text(event.get("event_id"), field="event_id")
    study_id = _required_text(event.get("study_id"), field="study_id")
    payload = _mapping(event.get("payload"))
    truth_payload = {
        "intervention_event_id": event_id,
        "intervention_intent": intent,
        "actor": _text(event.get("actor")) or "user",
        "source": _text(event.get("source")) or "manual",
        **payload,
    }
    agent_handoff = _mapping(event.get("agent_handoff"))
    if agent_handoff:
        truth_payload["agent_handoff"] = agent_handoff
    if intent == "abandon" and _text(truth_payload.get("current_required_action")) is None:
        truth_payload["current_required_action"] = "abandon_study_line"
    return {
        "study_id": study_id,
        "event_type": "task_intake" if intent == "new_plan" else "human_gate",
        "payload": truth_payload,
        "recorded_at": _required_text(event.get("recorded_at"), field="recorded_at"),
        "source_signature": f"intervention::{event_id}",
    }


def _event_id(
    *,
    study_id: str,
    intent: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
) -> str:
    encoded = json.dumps(
        {
            "study_id": study_id,
            "intent": intent,
            "payload": dict(payload),
            "recorded_at": recorded_at,
            "sequence": sequence,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"intervention-event-{sequence:06d}-{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _required_text(value: object, *, field: str) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"study intervention event requires {field}")
    return text


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
