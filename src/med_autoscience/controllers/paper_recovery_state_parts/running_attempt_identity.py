from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def running_attempt_has_obligation_identity(
    handoff: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    if handoff.get("running_provider_attempt") is not True:
        return False
    action_type = _text(obligation.get("action_type"))
    work_unit_id = _text(obligation.get("work_unit_id"))
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    obligation_id = _text(obligation.get("recovery_obligation_id"))
    handoff_obligation_id = _text(handoff.get("recovery_obligation_id"))
    fingerprint_matches = fingerprint is not None and fingerprint in {
        _text(handoff.get("work_unit_fingerprint")),
        _text(handoff.get("action_fingerprint")),
    }
    obligation_matches = (
        obligation_id is not None
        and handoff_obligation_id is not None
        and handoff_obligation_id == obligation_id
    )
    return (
        action_type is not None
        and _text(handoff.get("action_type")) == action_type
        and work_unit_id is not None
        and _first_text(handoff.get("work_unit_id"), handoff.get("next_work_unit")) == work_unit_id
        and (fingerprint_matches or obligation_matches)
    )


def running_attempt_identity_surface(progress: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping(progress.get("opl_current_control_state_handoff"))
    if handoff:
        return handoff
    current_work_unit = _mapping(progress.get("current_work_unit"))
    state = _mapping(current_work_unit.get("state"))
    proof = _mapping(state.get("provider_attempt_proof"))
    if not proof:
        envelope = _mapping(progress.get("current_execution_envelope"))
        proof = _mapping(envelope.get("provider_attempt_proof"))
    if not proof:
        return {}
    runtime_health = _mapping(proof.get("runtime_health"))
    return {
        **dict(runtime_health),
        **dict(proof),
        "action_type": _first_text(proof.get("action_type"), runtime_health.get("action_type")),
        "work_unit_id": _first_text(
            proof.get("work_unit_id"),
            proof.get("next_work_unit"),
            runtime_health.get("work_unit_id"),
        ),
        "work_unit_fingerprint": _first_text(
            proof.get("work_unit_fingerprint"),
            proof.get("action_fingerprint"),
            runtime_health.get("work_unit_fingerprint"),
            runtime_health.get("action_fingerprint"),
        ),
        "action_fingerprint": _first_text(
            proof.get("action_fingerprint"),
            proof.get("work_unit_fingerprint"),
            runtime_health.get("action_fingerprint"),
            runtime_health.get("work_unit_fingerprint"),
        ),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


__all__ = [
    "running_attempt_has_obligation_identity",
    "running_attempt_identity_surface",
]
