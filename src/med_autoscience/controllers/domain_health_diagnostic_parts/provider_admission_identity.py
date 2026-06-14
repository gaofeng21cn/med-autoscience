from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    text_items as _text_items,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER


def current_work_unit_opl_authorization_required(current_work_unit: Mapping[str, Any]) -> bool:
    state = _mapping(current_work_unit.get("state"))
    blocker = _mapping(state.get("typed_blocker"))
    for value in (
        blocker.get("blocker_id"),
        blocker.get("blocker_type"),
        blocker.get("blocked_reason"),
        blocker.get("reason"),
        state.get("blocker_type"),
        state.get("blocked_reason"),
    ):
        if _non_empty_text(value) == OPL_EXECUTION_AUTHORIZATION_BLOCKER:
            return True
    for value in (
        blocker.get("terminal_closeout_outcome"),
        current_work_unit.get("terminal_closeout_outcome"),
    ):
        text = _non_empty_text(value)
        if text is not None and OPL_EXECUTION_AUTHORIZATION_BLOCKER in text:
            return True
    return False


def current_identity_is_opl_authorization_typed_blocker(identity: Mapping[str, Any]) -> bool:
    return identity.get("opl_execution_authorization_required") is True


def current_action_currentness_basis(
    *,
    status_payload: Mapping[str, Any],
    current: Mapping[str, Any],
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
) -> dict[str, Any]:
    existing = _mapping(current.get("owner_route_currentness_basis")) or _mapping(
        current.get("currentness_basis")
    )
    generated_at = _non_empty_text(status_payload.get("study_progress_generated_at")) or _non_empty_text(
        status_payload.get("generated_at")
    )
    basis = {
        **dict(existing),
        "source_eval_id": _non_empty_text(existing.get("source_eval_id"))
        or _non_empty_text(current.get("source_eval_id")),
        "work_unit_id": _non_empty_text(existing.get("work_unit_id")) or work_unit_id,
        "work_unit_fingerprint": _non_empty_text(existing.get("work_unit_fingerprint"))
        or work_unit_fingerprint,
        "truth_epoch": _non_empty_text(existing.get("truth_epoch"))
        or _non_empty_text(current.get("truth_epoch"))
        or generated_at,
        "runtime_health_epoch": _non_empty_text(existing.get("runtime_health_epoch"))
        or _non_empty_text(current.get("runtime_health_epoch"))
        or generated_at,
    }
    return {key: value for key, value in basis.items() if value is not None}


def owner_route_currentness_basis_complete(currentness_basis: Mapping[str, Any]) -> bool:
    if _non_empty_text(currentness_basis.get("work_unit_id")) is None:
        return False
    if _non_empty_text(currentness_basis.get("work_unit_fingerprint")) is None:
        return False
    if _non_empty_text(currentness_basis.get("truth_epoch")) is None:
        return False
    return (
        _non_empty_text(currentness_basis.get("runtime_health_epoch")) is not None
        or _non_empty_text(currentness_basis.get("source_eval_id")) is not None
    )


def status_requires_current_identity(status_payload: Mapping[str, Any]) -> bool:
    if _mapping(status_payload.get("current_work_unit")):
        return True
    if _mapping(status_payload.get("current_executable_owner_action")):
        return True
    envelope = _mapping(status_payload.get("current_execution_envelope"))
    state_kind = _non_empty_text(envelope.get("state_kind")) or _non_empty_text(
        envelope.get("execution_state_kind")
    )
    if state_kind in {"executable_owner_action", "running_provider_attempt"}:
        return True
    if _mapping(status_payload.get("opl_current_control_state_handoff")):
        return True
    if _mapping(status_payload.get("opl_current_control_state")):
        return True
    return False


def matches_current_action(
    *,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if not current_action_identity:
        return False
    expected_work_unit_id = _non_empty_text(current_action_identity.get("work_unit_id"))
    action_ids = set(_text_items(current_action_identity.get("action_ids")))
    expected_fingerprints = set(_text_items(current_action_identity.get("work_unit_fingerprints")))
    if expected_fingerprints:
        if control_ticket := _control_ticket_fingerprint(expected_fingerprints):
            if not provider_admission_ticket_matches_action(
                work_unit_fingerprint=control_ticket,
                action_type=action_type,
                work_unit_id=work_unit_id,
            ):
                return False
        real_expected_fingerprints = {
            fingerprint
            for fingerprint in expected_fingerprints
            if not fingerprint.startswith("study-progress-current-owner-ticket::")
        }
        if real_expected_fingerprints and work_unit_fingerprint not in real_expected_fingerprints:
            return False
        if action_ids and action_type not in action_ids:
            return False
        if expected_work_unit_id is not None and not work_unit_ids_equivalent_for_action(
            action_type=action_type,
            left=work_unit_id,
            right=expected_work_unit_id,
        ):
            return False
        return True
    expected_fingerprint = _non_empty_text(current_action_identity.get("work_unit_fingerprint"))
    if expected_fingerprint is not None:
        if work_unit_fingerprint != expected_fingerprint:
            return False
        if not provider_admission_ticket_matches_action(
            work_unit_fingerprint=work_unit_fingerprint,
            action_type=action_type,
            work_unit_id=work_unit_id,
        ):
            return False
        if action_ids and action_type not in action_ids:
            return False
        return True
    if expected_work_unit_id is not None and not work_unit_ids_equivalent_for_action(
        action_type=action_type,
        left=work_unit_id,
        right=expected_work_unit_id,
    ):
        return False
    if action_ids and action_type not in action_ids:
        return False
    expected_source_ref = _non_empty_text(current_action_identity.get("source_ref"))
    if expected_source_ref is not None:
        return expected_source_ref in work_unit_fingerprint
    return True


def matches_current_action_without_fingerprint(
    *,
    action_type: str,
    work_unit_id: str,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if not current_action_identity:
        return False
    expected_work_unit_id = _non_empty_text(current_action_identity.get("work_unit_id"))
    if expected_work_unit_id is not None and not work_unit_ids_equivalent_for_action(
        action_type=action_type,
        left=work_unit_id,
        right=expected_work_unit_id,
    ):
        return False
    action_ids = set(_text_items(current_action_identity.get("action_ids")))
    return not action_ids or action_type in action_ids


def provider_admission_ticket_matches_action(
    *,
    work_unit_fingerprint: str,
    action_type: str,
    work_unit_id: str,
) -> bool:
    prefix = "study-progress-current-owner-ticket::"
    if not work_unit_fingerprint.startswith(prefix):
        return True
    parts = work_unit_fingerprint.split("::")
    if len(parts) < 4:
        return False
    ticket_work_unit_id = _non_empty_text(parts[2])
    ticket_action_type = _non_empty_text(parts[3])
    return (
        ticket_work_unit_id == work_unit_id
        and (ticket_action_type == action_type or ticket_action_type == work_unit_id)
    )


def _control_ticket_fingerprint(fingerprints: set[str]) -> str | None:
    for fingerprint in fingerprints:
        if fingerprint.startswith("study-progress-current-owner-ticket::"):
            return fingerprint
    return None


def work_unit_ids_equivalent_for_action(
    *,
    action_type: str | None,
    left: str | None,
    right: str | None,
) -> bool:
    if left == right:
        return True
    return (
        action_type == "run_gate_clearing_batch"
        and left in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
        and right in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
    )
