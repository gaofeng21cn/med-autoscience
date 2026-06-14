from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def matching_owner_gate_decision_event(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    for event in reversed(_owner_gate_decision_events(progress)):
        payload = _mapping(event.get("payload"))
        if _owner_gate_identity_matches_obligation(payload, obligation=obligation):
            return dict(event)
    return None


def owner_gate_decision_refs(payload: Mapping[str, Any]) -> list[str]:
    refs = [
        _text(payload.get("human_gate_ref")),
        _text(payload.get("route_back_evidence_ref")),
        _text(payload.get("owner_gate_decision_ref")),
        _text(payload.get("stable_typed_blocker_ref")),
        *_text_items(payload.get("stage_packet_refs")),
    ]
    return _dedupe(refs)


def accepted_owner_gate_decision(payload: Mapping[str, Any]) -> dict[str, Any]:
    identity = _mapping(payload.get("current_owner_identity"))
    accepted = {
        "decision": _text(payload.get("decision")),
        "action_type": _text(identity.get("action_type")),
        "work_unit_id": _text(identity.get("work_unit_id")),
        "work_unit_fingerprint": _text(identity.get("work_unit_fingerprint")),
        "route_back_evidence_ref": _text(payload.get("route_back_evidence_ref")),
    }
    return {key: value for key, value in accepted.items() if value not in (None, "", [], {})}


def _owner_gate_decision_events(progress: Mapping[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for key in ("study_intervention_events", "intervention_events"):
        for item in progress.get(key) or []:
            event = _mapping(item)
            if _text(event.get("intent")) == "owner_gate_decision":
                events.append(event)
    return events


def _owner_gate_identity_matches_obligation(
    payload: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    identity = _mapping(payload.get("current_owner_identity"))
    if not identity:
        return False
    for field in ("study_id", "action_type", "work_unit_id", "work_unit_fingerprint", "blocker_type"):
        expected = _text(obligation.get(field))
        if expected is not None and _text(identity.get(field)) != expected:
            return False
    return _text(payload.get("human_gate_ref")) is not None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _dedupe(values: list[str | None]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


__all__ = [
    "accepted_owner_gate_decision",
    "matching_owner_gate_decision_event",
    "owner_gate_decision_refs",
]
