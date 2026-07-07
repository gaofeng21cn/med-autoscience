from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


def receipt_owner_consumption_superseded_by_consumption(
    *,
    receipt_owner_consumption_readback: Mapping[str, Any],
    consumption_ledger_readback: Mapping[str, Any] | None,
) -> bool:
    if consumption_ledger_readback is None:
        return False
    receipt_mtime = _path_mtime(
        _optional_text(receipt_owner_consumption_readback.get("source_ref"))
    )
    consume_mtime = _path_mtime(
        _optional_text(consumption_ledger_readback.get("source_ref"))
    )
    if receipt_mtime is None or consume_mtime is None or consume_mtime <= receipt_mtime:
        return False
    if _receipt_is_consumed_typed_blocker(
        receipt_owner_consumption_readback
    ) and _consumption_is_non_advancing_route_back(consumption_ledger_readback):
        return False
    if (
        _optional_text(consumption_ledger_readback.get("route_handoff_status"))
        == "ready_for_opl_route_command"
    ):
        return True
    handoff = _mapping(consumption_ledger_readback.get("opl_route_handoff"))
    return (
        _optional_text(handoff.get("handoff_status")) == "ready_for_opl_route_command"
        and handoff.get("can_submit_to_opl_runtime") is True
    )


def receipt_owner_consumption_superseded_by_stage_closure(
    *,
    receipt_owner_consumption_readback: Mapping[str, Any],
    stage_closure_ledger_readback: Mapping[str, Any] | None,
) -> bool:
    if stage_closure_ledger_readback is None:
        return False
    if _receipt_is_consumed_typed_blocker(receipt_owner_consumption_readback):
        return False
    decision = _mapping(receipt_owner_consumption_readback.get("stage_closure_decision"))
    receipt_outcome = _mapping(decision.get("outcome"))
    if (
        _optional_text(receipt_outcome.get("kind")) != "next_stage_transition"
        or _optional_text(receipt_outcome.get("transition_kind"))
        != "route_back_candidate_checkpoint"
    ):
        return False
    if not _has_route_checkpoint_evidence(stage_closure_ledger_readback):
        return False
    if _same_route_checkpoint_identity(
        decision,
        stage_closure_ledger_readback,
    ):
        return False
    receipt_mtime = _path_mtime(
        _optional_text(receipt_owner_consumption_readback.get("source_ref"))
    )
    stage_mtime = _path_mtime(
        _optional_text(stage_closure_ledger_readback.get("source_ref"))
        or _optional_text(stage_closure_ledger_readback.get("decision_ref"))
    )
    if receipt_mtime is not None and stage_mtime is not None:
        return stage_mtime > receipt_mtime
    return _different_route_checkpoint_identity(
        decision,
        stage_closure_ledger_readback,
    )


def _same_route_checkpoint_identity(
    receipt_decision: Mapping[str, Any],
    stage_decision: Mapping[str, Any],
) -> bool:
    stage_outcome = _mapping(stage_decision.get("outcome"))
    if (
        _optional_text(stage_outcome.get("kind")) != "next_stage_transition"
        or _optional_text(stage_outcome.get("transition_kind"))
        != "route_back_candidate_checkpoint"
    ):
        return False
    receipt_identity = _route_checkpoint_identity(receipt_decision)
    stage_identity = _route_checkpoint_identity(stage_decision)
    if receipt_identity == stage_identity and any(receipt_identity):
        return True
    return any(
        receipt_item is not None and receipt_item == stage_item
        for receipt_item, stage_item in zip(receipt_identity, stage_identity)
    ) and not _different_route_checkpoint_identity(receipt_decision, stage_decision)


def _different_route_checkpoint_identity(
    receipt_decision: Mapping[str, Any],
    stage_decision: Mapping[str, Any],
) -> bool:
    receipt_identity = _route_checkpoint_identity(receipt_decision)
    stage_identity = _route_checkpoint_identity(stage_decision)
    return any(
        receipt_item is not None
        and stage_item is not None
        and receipt_item != stage_item
        for receipt_item, stage_item in zip(receipt_identity, stage_identity)
    )


def _has_route_checkpoint_evidence(decision: Mapping[str, Any]) -> bool:
    outcome = _mapping(decision.get("outcome"))
    return any(
        _optional_text(value) is not None
        for value in (
            decision.get("route_checkpoint_evidence_ref"),
            outcome.get("route_checkpoint_evidence_ref"),
            decision.get("receipt_evidence_ref"),
            outcome.get("receipt_evidence_ref"),
        )
    )


def _route_checkpoint_identity(decision: Mapping[str, Any]) -> tuple[str | None, ...]:
    outcome = _mapping(decision.get("outcome"))
    opl_closeout = _mapping(decision.get("opl_closeout"))
    return (
        _optional_text(decision.get("stage_id")),
        _optional_text(decision.get("work_unit_id")),
        _optional_text(decision.get("route_checkpoint_evidence_ref"))
        or _optional_text(outcome.get("route_checkpoint_evidence_ref")),
        _optional_text(decision.get("receipt_evidence_ref"))
        or _optional_text(outcome.get("receipt_evidence_ref")),
        _optional_text(opl_closeout.get("stage_attempt_id")),
    )


def _receipt_is_consumed_typed_blocker(receipt: Mapping[str, Any]) -> bool:
    if _optional_text(receipt.get("status")) != "owner_consumption_applied":
        return False
    consumption = _mapping(receipt.get("mas_receipt_consumption"))
    if _optional_text(consumption.get("status")) == "owner_consumed_typed_blocker":
        return True
    decision = _mapping(receipt.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    return _optional_text(outcome.get("kind")) == "typed_blocker"


def _consumption_is_non_advancing_route_back(
    consumption_ledger_readback: Mapping[str, Any],
) -> bool:
    stage_decision = _mapping(consumption_ledger_readback.get("stage_terminal_decision"))
    handoff = _mapping(consumption_ledger_readback.get("opl_route_handoff"))
    handoff_decision = _mapping(handoff.get("stage_terminal_decision"))
    opl_route_command = _mapping(consumption_ledger_readback.get("opl_route_command")) or _mapping(
        handoff.get("opl_route_command")
    )
    route_command_kind = _optional_text(opl_route_command.get("command_kind")) or _optional_text(
        handoff.get("route_command_kind")
    )
    transaction_state = _optional_text(consumption_ledger_readback.get("transaction_state")) or _optional_text(
        handoff.get("transaction_state")
    )
    decision_kind = _optional_text(stage_decision.get("decision_kind")) or _optional_text(
        handoff_decision.get("decision_kind")
    )
    decision_status = _optional_text(stage_decision.get("status")) or _optional_text(
        handoff_decision.get("status")
    )
    reason = _optional_text(stage_decision.get("reason")) or _optional_text(
        handoff_decision.get("reason")
    )
    if route_command_kind == "route_back":
        return True
    if transaction_state == "route_back":
        return True
    if decision_kind == "route_back" or decision_status == "route_back":
        return True
    return reason == "paper_mission_stage_route_domain_gate_pending"


def _path_mtime(path_text: str | None) -> float | None:
    if path_text is None:
        return None
    try:
        return Path(path_text).expanduser().resolve().stat().st_mtime
    except OSError:
        return None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
