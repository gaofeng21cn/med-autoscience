from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def terminal_owner_gate_from_carrier_readback(
    carrier_readback: Mapping[str, Any],
) -> dict[str, Any]:
    terminal_closeout = _mapping(carrier_readback.get("terminal_closeout"))
    if not terminal_closeout:
        return {}
    typed_blocker_ref = _text(terminal_closeout.get("typed_blocker_ref"))
    closeout_ref = _text(terminal_closeout.get("closeout_ref"))
    blocked_reason = _first_text(
        terminal_closeout.get("blocked_reason"),
        carrier_readback.get("domain_ready_verdict"),
    )
    if not typed_blocker_ref and not closeout_ref and not blocked_reason:
        return {}
    return _compact(
        {
            "surface_kind": "paper_mission_terminal_owner_gate",
            "owner": "one-person-lab",
            "gate_kind": "typed_blocker" if typed_blocker_ref else "owner_gate",
            "blocked_reason": blocked_reason,
            "typed_blocker_ref": typed_blocker_ref,
            "closeout_ref": closeout_ref,
            "stage_attempt_id": terminal_closeout.get("stage_attempt_id"),
            "work_unit_id": terminal_closeout.get("work_unit_id"),
            "can_claim_paper_progress": carrier_readback.get("can_claim_paper_progress")
            is True,
            "can_claim_runtime_ready": carrier_readback.get("can_claim_runtime_ready")
            is True,
            "authority_materialized": carrier_readback.get("authority_materialized")
            is True,
            "legal_next_action": "route_to_owner_or_human_gate",
        }
    )


def terminal_owner_gate_next_decision(
    terminal_owner_gate: Mapping[str, Any],
) -> dict[str, Any]:
    return _compact(
        {
            "kind": "owner_or_route",
            "next_owner": terminal_owner_gate.get("owner"),
            "human_decision_required": False,
            "summary": terminal_owner_gate.get("blocked_reason"),
            "typed_blocker_ref": terminal_owner_gate.get("typed_blocker_ref"),
            "can_execute": False,
            "can_authorize_provider_admission": False,
        }
    )


def stage_terminal_next_owner_or_human_decision(
    *,
    stage_terminal_decision: Mapping[str, Any],
    opl_route_command: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    decision = _mapping(stage_terminal_decision)
    route = _mapping(opl_route_command)
    decision_kind = _text(decision.get("decision_kind"))
    status = _text(decision.get("status"))
    needs_human = decision_kind in {
        "human_gate",
        "human_interrupt",
        "waiting_human_decision",
    } or status in {
        "human_gate",
        "human_interrupt",
        "waiting_human_decision",
    }
    typed_blocker_ref = (
        _first_text(
            decision.get("typed_blocker_ref"),
            decision.get("blocker_ref"),
            decision.get("blocker_id"),
            route.get("target") if decision_kind == "typed_blocker" else None,
        )
        if decision_kind == "typed_blocker" or status == "typed_blocker"
        else None
    )
    return _compact(
        {
            "kind": "human_decision" if needs_human else "owner_or_route",
            "next_owner": _first_text(
                decision.get("next_owner"),
                route.get("runtime_owner"),
            ),
            "human_decision_required": needs_human,
            "summary": _first_text(
                decision.get("reason"),
                status,
                decision.get("blocker_id"),
                route.get("reason"),
            ),
            "typed_blocker_ref": typed_blocker_ref,
            "can_execute": False,
            "can_authorize_provider_admission": False,
        }
    )


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "stage_terminal_next_owner_or_human_decision",
    "terminal_owner_gate_from_carrier_readback",
    "terminal_owner_gate_next_decision",
]
