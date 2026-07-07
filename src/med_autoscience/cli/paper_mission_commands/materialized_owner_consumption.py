from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
from typing import Any

from med_autoscience.cli.paper_mission_commands.common import (
    _mapping,
    _optional_text,
)
from med_autoscience.cli.paper_mission_commands.owner_consumption_alignment import (
    _add_stage_attempt_identity,
    _align_current_carrier_owner_consumption,
    _carrier_matches_owner_consumed_stage_attempt,
    _carrier_stage_attempt_identities,
    _preserve_direct_successor_runtime_readback,
    _receipt_owner_consumption_stage_attempt_identities,
)


def _receipt_superseded_by_consumption(
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
