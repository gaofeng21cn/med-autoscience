from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..owner_action_admission import provider_attempt_proof_for_current_action
from .primitives import _mapping, _text
from .summary_work_units import work_unit_id


def strict_running_provider_liveness(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is not True:
        return False
    if _text(handoff.get("active_run_id")) is None:
        return False
    if handoff_has_matching_terminal_closeout(handoff):
        return False
    runtime_health = _mapping(handoff.get("runtime_health"))
    runtime_liveness_status = _text(runtime_health.get("runtime_liveness_status"))
    health_status = _text(runtime_health.get("health_status"))
    return runtime_liveness_status in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    } or health_status in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    }


def canonical_current_work_unit_running_provider_attempt(
    *,
    current_work_unit: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    if _text(current_work_unit.get("status")) != "running_provider_attempt":
        return False
    if not strict_running_provider_liveness(handoff):
        return False
    handoff_attempt_id = _text(handoff.get("active_stage_attempt_id"))
    if handoff_attempt_id is None:
        return False
    state = _mapping(current_work_unit.get("state"))
    proof = _mapping(state.get("provider_attempt_proof"))
    proof_attempt_id = _text(proof.get("active_stage_attempt_id"))
    if proof_attempt_id is not None and proof_attempt_id != handoff_attempt_id:
        return False
    current_work_unit_id = work_unit_id(current_work_unit.get("work_unit_id"))
    proof_work_unit_id = work_unit_id(proof.get("work_unit_id")) or work_unit_id(
        proof.get("next_work_unit")
    )
    handoff_work_unit_id = work_unit_id(handoff.get("work_unit_id")) or work_unit_id(
        handoff.get("next_work_unit")
    )
    comparable_identity_observed = False
    if (
        current_work_unit_id is not None
        and proof_work_unit_id is not None
        and proof_work_unit_id != current_work_unit_id
    ):
        return False
    comparable_identity_observed = comparable_identity_observed or (
        current_work_unit_id is not None and proof_work_unit_id is not None
    )
    if current_work_unit_id is not None:
        if handoff_work_unit_id is None:
            return False
        if handoff_work_unit_id != current_work_unit_id:
            return False
        comparable_identity_observed = True
    fingerprint = _text(current_work_unit.get("work_unit_fingerprint")) or _text(
        current_work_unit.get("action_fingerprint")
    )
    handoff_fingerprints = {
        text
        for value in (
            handoff.get("work_unit_fingerprint"),
            handoff.get("action_fingerprint"),
            _mapping(handoff.get("runtime_health")).get("work_unit_fingerprint"),
            _mapping(handoff.get("runtime_health")).get("action_fingerprint"),
        )
        if (text := _text(value)) is not None
    }
    if fingerprint is not None and handoff_fingerprints and fingerprint not in handoff_fingerprints:
        return False
    comparable_identity_observed = comparable_identity_observed or (
        fingerprint is not None and bool(handoff_fingerprints)
    )
    return comparable_identity_observed


def handoff_identity_conflicts_current_action(
    *,
    handoff: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    if not current_action:
        return False
    return provider_attempt_proof_for_current_action(
        handoff=handoff,
        current_action=current_action,
    ) is None


def handoff_has_matching_terminal_closeout(handoff: Mapping[str, Any]) -> bool:
    terminal = _mapping(handoff.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = handoff_stage_attempt_id(handoff)
    terminal_attempt_id = _text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    status = _text(terminal.get("status"))
    if status in {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "failed",
        "terminal",
        "typed_blocked",
    }:
        return True
    return _text(terminal.get("source_path")) is not None and _text(terminal.get("record_path")) is not None


def handoff_stage_attempt_id(handoff: Mapping[str, Any]) -> str | None:
    if text := _text(handoff.get("active_stage_attempt_id")):
        return text
    active_run_id = _text(handoff.get("active_run_id"))
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


__all__ = [
    "canonical_current_work_unit_running_provider_attempt",
    "handoff_has_matching_terminal_closeout",
    "handoff_identity_conflicts_current_action",
    "handoff_stage_attempt_id",
    "strict_running_provider_liveness",
]
