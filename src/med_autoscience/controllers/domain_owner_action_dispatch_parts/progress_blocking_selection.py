from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.stage_route_currentness_identity import (
    currentness_identities_match,
)


def blocking_progress_allows_current_dispatch_selection(
    progress: Mapping[str, Any],
) -> bool:
    if _paper_recovery_materialization_ready(progress):
        return True
    envelope = _mapping(progress.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind == "parked":
        return True
    if state_kind != "typed_blocker":
        return False
    return fresh_progress_typed_blocker_reason(envelope) in {
        "current_work_unit_unresolved",
        "no_selected_dispatch_for_requested_action_types",
        "stage_packet_not_current_selected_dispatch",
    }


def fresh_progress_envelope_blocks_dispatch_selection(
    progress: Mapping[str, Any],
) -> bool:
    envelope = _mapping(progress.get("current_execution_envelope"))
    current_action = _mapping(progress.get("current_executable_owner_action"))
    if typed_blocker_allows_repair_progress_followup(
        envelope=envelope,
        current_action=current_action,
    ):
        return False
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind == "typed_blocker" and fresh_progress_typed_blocker_reason(envelope) in {
        "medical_paper_readiness_missing",
        "terminal_closeout_owner_answer_required",
    }:
        return False
    return state_kind in {"typed_blocker", "parked"}


def typed_blocker_allows_repair_progress_followup(
    *,
    envelope: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind != "typed_blocker":
        return False
    if not is_repair_progress_followup_action(current_action):
        return False
    blocker = _mapping(envelope.get("typed_blocker"))
    if _text(blocker.get("owner")) != "one-person-lab":
        return False
    blocker_reasons = {
        text
        for value in (
            blocker.get("blocker_id"),
            blocker.get("blocker_type"),
            blocker.get("reason"),
            blocker.get("blocked_reason"),
            blocker.get("terminal_closeout_status"),
            blocker.get("terminal_closeout_outcome"),
        )
        if (text := _text(value)) is not None
    }
    if not any("opl_execution_authorization_required" in reason for reason in blocker_reasons):
        return False
    if _text(current_action.get("action_type")) != _text(blocker.get("action_type")):
        return False
    return currentness_identities_match(current_action, blocker, require_fingerprint=True)


def is_repair_progress_followup_action(action: Mapping[str, Any]) -> bool:
    source = _text(action.get("source")) or _text(action.get("source_surface"))
    if source != "repair_progress_projection.mas_owner_repair_execution_evidence":
        return False
    if _text(action.get("action_type")) not in {
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
    }:
        return False
    return bool(_mapping(action.get("repair_progress_precedence")) or _text(action.get("source_ref")) is not None)


def fresh_progress_typed_blocker_reason(envelope: Mapping[str, Any]) -> str | None:
    blocker = _mapping(envelope.get("typed_blocker"))
    return (
        _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("reason"))
    )


def _paper_recovery_materialization_ready(progress: Mapping[str, Any]) -> bool:
    recovery = _mapping(progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "owner_action_ready":
        return False
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    if _text(supervisor_decision.get("decision")) not in {None, "materialize_recovery_action"}:
        return False
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    return _text(next_safe_action.get("kind")) in {
        "run_mas_owner_callable",
        "materialize_successor_owner_action",
        "materialize_successor_owner_gate",
        "materialize_recovery_work_unit_or_receipt",
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "blocking_progress_allows_current_dispatch_selection",
    "fresh_progress_envelope_blocks_dispatch_selection",
    "fresh_progress_typed_blocker_reason",
    "is_repair_progress_followup_action",
    "typed_blocker_allows_repair_progress_followup",
]
