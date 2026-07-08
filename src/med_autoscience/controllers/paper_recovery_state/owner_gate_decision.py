from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit.stage_packet_blockers import (
    is_selected_dispatch_stage_packet_blocker as _is_selected_dispatch_stage_packet_blocker,
)


def matching_owner_gate_decision_event(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    for event in reversed(_owner_gate_decision_events(progress)):
        payload = _mapping(event.get("payload"))
        if _owner_gate_identity_matches_obligation(payload, obligation=obligation):
            return dict(event)
        if _owner_gate_identity_matches_current_execution(payload, progress=progress):
            return dict(event)
    return None


def owner_gate_decision_matches_obligation(
    payload: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    return _owner_gate_identity_matches_obligation(payload, obligation=obligation)


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
        "human_gate_ref": _text(payload.get("human_gate_ref")),
        "owner_gate_decision_ref": _text(payload.get("owner_gate_decision_ref")),
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
    for field in ("study_id", "action_type", "work_unit_id", "work_unit_fingerprint"):
        expected = _text(obligation.get(field))
        if expected is not None and _text(identity.get(field)) != expected:
            return False
    expected_blocker = _text(obligation.get("blocker_type"))
    identity_blocker = _text(identity.get("blocker_type"))
    if expected_blocker is not None and not _blocker_types_match(identity_blocker, expected_blocker):
        return False
    return _text(payload.get("human_gate_ref")) is not None


def _owner_gate_identity_matches_current_execution(
    payload: Mapping[str, Any],
    *,
    progress: Mapping[str, Any],
) -> bool:
    identity = _mapping(payload.get("current_owner_identity"))
    if not identity or _text(payload.get("human_gate_ref")) is None:
        return False
    return any(
        _owner_gate_identity_matches_source(identity, source)
        for source in _current_execution_identity_sources(progress)
    )


def _current_execution_identity_sources(progress: Mapping[str, Any]) -> list[dict[str, Any]]:
    recovery = _mapping(progress.get("paper_recovery_state"))
    recovery_next_action = _mapping(recovery.get("next_safe_action"))
    sources = [
        _mapping(progress.get("current_executable_owner_action")),
        _mapping(progress.get("current_work_unit")),
        _mapping(progress.get("current_execution_envelope")),
        _mapping(recovery_next_action.get("accepted_owner_gate_decision")),
        _mapping(recovery_next_action.get("successor_owner_action")),
    ]
    for key in ("provider_admission_candidates", "transition_request_candidates"):
        sources.extend(_mapping(item) for item in progress.get(key) or [])
    return [source for source in sources if source]


def _owner_gate_identity_matches_source(
    identity: Mapping[str, Any],
    source: Mapping[str, Any],
) -> bool:
    source_study_id = _text(source.get("study_id"))
    if source_study_id is not None and _text(identity.get("study_id")) not in {None, source_study_id}:
        return False
    for field in ("action_type", "work_unit_id", "work_unit_fingerprint"):
        if _text(identity.get(field)) != _source_identity_field(source, field):
            return False
    return True


def _source_identity_field(source: Mapping[str, Any], field: str) -> str | None:
    if field == "work_unit_fingerprint":
        return _text(source.get("work_unit_fingerprint")) or _text(source.get("action_fingerprint"))
    if field == "work_unit_id":
        return _text(source.get("work_unit_id")) or _text(source.get("next_work_unit"))
    return _text(source.get(field))


def _blocker_types_match(candidate: str | None, blocker_type: str | None) -> bool:
    if candidate == blocker_type:
        return True
    return (
        _is_selected_dispatch_stage_packet_blocker(candidate)
        and _is_selected_dispatch_stage_packet_blocker(blocker_type)
    )


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
    "owner_gate_decision_matches_obligation",
    "owner_gate_decision_refs",
]
