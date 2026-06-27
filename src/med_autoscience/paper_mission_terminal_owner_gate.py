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
    owner = _terminal_owner_gate_owner(blocked_reason)
    if not typed_blocker_ref and not closeout_ref and not blocked_reason:
        return {}
    return _compact(
        {
            "surface_kind": "paper_mission_terminal_owner_gate",
            "owner": owner,
            "gate_kind": (
                "domain_gate"
                if owner == "mas_authority_kernel"
                else "typed_blocker"
                if typed_blocker_ref
                else "owner_gate"
            ),
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


def terminal_owner_gate_from_stage_terminal_decision(
    *,
    stage_terminal_decision: Mapping[str, Any],
    paper_mission_transaction: Mapping[str, Any],
) -> dict[str, Any]:
    decision = _mapping(stage_terminal_decision)
    decision_kind = _text(decision.get("decision_kind"))
    status = _text(decision.get("status"))
    blocked_reason = _first_text(decision.get("reason"), status)
    if decision_kind != "route_back" and status != "route_back":
        return {}
    if _terminal_owner_gate_owner(blocked_reason) != "mas_authority_kernel":
        return {}
    transaction = _mapping(paper_mission_transaction)
    return _compact(
        {
            "surface_kind": "paper_mission_terminal_owner_gate",
            "owner": "mas_authority_kernel",
            "gate_kind": "domain_gate",
            "blocked_reason": blocked_reason,
            "typed_blocker_ref": _text(decision.get("typed_blocker_ref")),
            "closeout_ref": _text(decision.get("closeout_ref")),
            "stage_attempt_id": _text(decision.get("stage_attempt_id")),
            "work_unit_id": _first_text(
                transaction.get("stage_id"),
                decision.get("target_stage_id"),
            ),
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
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


def terminal_owner_gate_authority_readback(
    terminal_owner_gate: Mapping[str, Any],
) -> dict[str, Any]:
    gate = _mapping(terminal_owner_gate)
    if not gate:
        return {}
    typed_blocker_ref = _text(gate.get("typed_blocker_ref"))
    closeout_ref = _text(gate.get("closeout_ref"))
    owner = _first_text(gate.get("owner"), "one-person-lab") or "one-person-lab"
    mas_authority_owner = owner == "mas_authority_kernel"
    status = (
        "owner_answer_required"
        if mas_authority_owner
        else "typed_blocker_required"
        if typed_blocker_ref
        else "owner_gate_required"
    )
    return _compact(
        {
            "surface_kind": "mas_terminal_owner_gate_authority_readback",
            "schema_version": 1,
            "status": status,
            "selected_outcome": status,
            "next_owner": owner,
            "resume_condition": _first_text(
                gate.get("blocked_reason"),
                "MAS authority or the named runtime owner must consume the terminal owner gate",
            ),
            "terminal_owner_gate": gate,
            "owner_answer_contract": _compact(
                {
                    "required_surface": (
                        (
                            "domain_owner_receipt_quality_gate_typed_blocker_"
                            "human_gate_or_route_back_ref"
                        )
                        if mas_authority_owner
                        else "typed_blocker_ref"
                        if typed_blocker_ref
                        else "owner_receipt_typed_blocker_human_gate_or_route_back_ref"
                    ),
                    "typed_blocker_ref": typed_blocker_ref,
                    "closeout_ref": closeout_ref,
                    "stage_attempt_id": gate.get("stage_attempt_id"),
                    "work_unit_id": gate.get("work_unit_id"),
                    "accepted_shapes": [
                        "domain_owner_receipt_ref",
                        "quality_gate_receipt_ref",
                        "paper_facing_delta_ref",
                        "typed_blocker_ref",
                        "human_gate_ref",
                        "route_back_evidence_ref",
                    ],
                }
            ),
            "consume_result": {
                "status": (
                    "owner_answer_required"
                    if mas_authority_owner
                    else "typed_blocker"
                    if typed_blocker_ref
                    else "route_back"
                ),
                "outcome": status,
                "authority_materialized": False,
            },
            "write_plan": {
                "mode": "readback_only",
                "written_files": [],
                "can_write_owner_receipts": False,
                "can_write_typed_blockers": False,
                "can_write_human_gate_authority_records": False,
                "can_write_current_package": False,
                "can_write_runtime_queues_or_provider_attempts": False,
            },
            "authority_boundary": {
                "mas_authority_owner": "MedAutoScience",
                "runtime_owner": "one-person-lab",
                "authority_materialized": False,
                "can_claim_paper_progress": False,
                "can_claim_runtime_ready": False,
                "can_authorize_provider_admission": False,
                "can_write_owner_receipt": False,
                "can_write_typed_blocker": False,
                "can_write_human_gate": False,
                "can_write_current_package": False,
                "can_write_runtime_queue_or_provider_attempt": False,
            },
        }
    )


def _terminal_owner_gate_owner(blocked_reason: str | None) -> str:
    reason = _text(blocked_reason) or ""
    if reason in {
        "domain_gate_pending",
        "paper_mission_stage_route_domain_gate_pending",
    } or reason.endswith("_domain_gate_pending"):
        return "mas_authority_kernel"
    return "one-person-lab"


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
    "terminal_owner_gate_authority_readback",
    "terminal_owner_gate_from_carrier_readback",
    "terminal_owner_gate_from_stage_terminal_decision",
    "terminal_owner_gate_next_decision",
]
