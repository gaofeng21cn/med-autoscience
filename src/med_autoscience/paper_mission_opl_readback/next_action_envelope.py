from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.next_action_envelope import (
    compile_next_action_envelope,
)

from .receipt_events import matches_opl_transition_receipt


def paper_mission_next_action_envelope(
    *,
    transaction: Mapping[str, Any] | None = None,
    stage_terminal_decision: Mapping[str, Any] | None = None,
    opl_route_command: Mapping[str, Any] | None = None,
    opl_runtime_carrier: Mapping[str, Any] | None = None,
    opl_runtime_carrier_readback: Mapping[str, Any] | None = None,
    opl_route_handoff: Mapping[str, Any] | None = None,
    diagnostic_refs: list[str] | None = None,
) -> dict[str, Any] | None:
    """Project the canonical MAS next-action envelope into readback surfaces."""

    transaction_payload = _mapping(transaction)
    handoff = _mapping(opl_route_handoff)
    decision = _first_mapping(
        _mapping(stage_terminal_decision),
        _mapping(handoff.get("stage_terminal_decision")),
        _mapping(transaction_payload.get("stage_terminal_decision")),
    )
    route = _first_mapping(
        _mapping(opl_route_command),
        _mapping(handoff.get("opl_route_command")),
        _mapping(transaction_payload.get("opl_route_command")),
    )
    carrier = _first_mapping(
        _mapping(opl_runtime_carrier),
        _mapping(handoff.get("opl_runtime_carrier")),
    )
    carrier_readback = _mapping(opl_runtime_carrier_readback)
    transition_receipt = _mapping(carrier_readback.get("opl_transition_receipt"))
    has_valid_transition_receipt = matches_opl_transition_receipt(
        receipt=transition_receipt,
        carrier=carrier,
    )
    terminal_closeout = _mapping(carrier_readback.get("terminal_closeout"))
    mas_receipt_consumption = _mapping(carrier_readback.get("mas_receipt_consumption"))
    if not decision and not route:
        return None
    transaction_ref = _first_text(
        transaction_payload.get("transaction_id"),
        handoff.get("paper_mission_transaction_ref"),
        carrier.get("paper_mission_transaction_ref"),
    )
    stage_ref = _first_text(
        handoff.get("stage_terminal_decision_ref"),
        carrier.get("stage_terminal_decision_ref"),
        f"{transaction_ref}#stage_terminal_decision" if transaction_ref else None,
    )
    route_ref = _first_text(
        handoff.get("opl_route_command_ref"),
        carrier.get("opl_route_command_ref"),
        f"{transaction_ref}#opl_route_command" if transaction_ref else None,
    )
    return compile_next_action_envelope(
        stage_outcome={
            **decision,
            "study_id": _first_text(
                decision.get("study_id"),
                transaction_payload.get("study_id"),
                carrier.get("study_id"),
            ),
            "stage_id": _first_text(
                decision.get("stage_id"),
                transaction_payload.get("stage_id"),
                carrier.get("stage_id"),
            ),
            "work_unit_id": _first_text(
                route.get("target"),
                decision.get("next_stage_id"),
                decision.get("target_stage_id"),
                decision.get("next_work_unit"),
                decision.get("blocker_id"),
                decision.get("required_receipt"),
                transaction_payload.get("stage_id"),
                carrier.get("work_unit_id"),
            ),
            "stage_closure_decision_ref": stage_ref,
        },
        study_id=_first_text(
            transaction_payload.get("study_id"),
            decision.get("study_id"),
            carrier.get("study_id"),
        ),
        stage_id=_first_text(
            transaction_payload.get("stage_id"),
            decision.get("stage_id"),
            carrier.get("stage_id"),
        ),
        outcome_ref=stage_ref,
        route_command={
            **route,
            "runtime_owner": _first_text(
                route.get("runtime_owner"),
                handoff.get("runtime_owner"),
                carrier.get("target_runtime_owner"),
                "one-person-lab",
            ),
            "work_unit_id": _first_text(route.get("target"), carrier.get("work_unit_id")),
            "request_idempotency_key": _first_text(
                route.get("request_idempotency_key"),
                handoff.get("request_idempotency_key"),
                carrier.get("request_idempotency_key"),
            ),
            "attempt_idempotency_key": _first_text(
                route.get("attempt_idempotency_key"),
                handoff.get("attempt_idempotency_key"),
                carrier.get("attempt_idempotency_key"),
            ),
        },
        owner_route={
            **handoff,
            **(
                {
                    "action_family": _transition_receipt_action_family(
                        transition_receipt=transition_receipt,
                        mas_receipt_consumption=mas_receipt_consumption,
                    ),
                    "opl_transition_receipt": transition_receipt,
                    "terminal_closeout": terminal_closeout,
                    **(
                        {"mas_receipt_consumption": mas_receipt_consumption}
                        if mas_receipt_consumption
                        else {}
                    ),
                    "allowed_actions": _transition_receipt_allowed_actions(
                        transition_receipt=transition_receipt,
                        mas_receipt_consumption=mas_receipt_consumption,
                    ),
                    "next_owner": "mas_authority_kernel",
                }
                if has_valid_transition_receipt
                else {}
            ),
            "next_owner": _first_text(
                "mas_authority_kernel"
                if has_valid_transition_receipt
                else None,
                handoff.get("next_owner"),
                decision.get("next_owner"),
            ),
        },
        authority_boundary={
            "projection_only": carrier.get("projection_only") is True
            or handoff.get("transaction_materialized") is True,
        },
        diagnostic_refs=_diagnostic_ref_items(
            diagnostic_refs=diagnostic_refs,
            transaction_ref=transaction_ref,
            stage_ref=stage_ref,
            route_ref=route_ref,
            handoff=handoff,
            decision=decision,
        ),
    )


def attach_paper_mission_next_action(
    payload: Mapping[str, Any],
    *,
    opl_route_handoff: Mapping[str, Any] | None = None,
    diagnostic_refs: list[str] | None = None,
) -> dict[str, Any]:
    result = dict(payload)
    transaction = _mapping(result.get("paper_mission_transaction"))
    handoff = _mapping(opl_route_handoff) or _mapping(result.get("opl_route_handoff"))
    envelope = paper_mission_next_action_envelope(
        transaction=transaction,
        stage_terminal_decision=_mapping(result.get("stage_terminal_decision")),
        opl_route_command=_mapping(result.get("opl_route_command")),
        opl_runtime_carrier=_mapping(result.get("opl_runtime_carrier")),
        opl_runtime_carrier_readback=_mapping(
            result.get("opl_runtime_carrier_readback")
        ),
        opl_route_handoff=handoff,
        diagnostic_refs=diagnostic_refs,
    )
    if envelope is not None:
        result["next_action"] = envelope
    return result


def _diagnostic_ref_items(
    *,
    diagnostic_refs: list[str] | None,
    transaction_ref: str | None,
    stage_ref: str | None,
    route_ref: str | None,
    handoff: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for item in diagnostic_refs or []:
        if text := _text(item):
            refs.append({"role": "diagnostic", "ref": text})
    for role, ref in (
        ("paper_mission_transaction", transaction_ref),
        ("stage_terminal_decision", stage_ref),
        ("opl_route_command", route_ref),
        ("handoff_source", handoff.get("source_ref")),
        ("handoff_candidate", handoff.get("candidate_ref")),
        ("route_back_evidence", decision.get("route_back_evidence_ref")),
        ("source_route_back_evidence", decision.get("source_route_back_evidence_ref")),
    ):
        if text := _text(ref):
            refs.append({"role": role, "ref": text})
    return _dedupe_ref_items(refs)


def _dedupe_ref_items(refs: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for ref in refs:
        key = (ref["role"], ref["ref"])
        if key in seen:
            continue
        seen.add(key)
        result.append(ref)
    return result


def _transition_receipt_action_family(
    *,
    transition_receipt: Mapping[str, Any],
    mas_receipt_consumption: Mapping[str, Any],
) -> str:
    if _transition_receipt_requires_route_checkpoint(
        transition_receipt=transition_receipt,
        mas_receipt_consumption=mas_receipt_consumption,
    ):
        return "paper.stage_closure.owner_consumption"
    if _transition_receipt_requires_typed_blocker(
        transition_receipt=transition_receipt,
        mas_receipt_consumption=mas_receipt_consumption,
    ):
        return "blocked.typed"
    return "paper.gate.publishability_replay"


def _transition_receipt_allowed_actions(
    *,
    transition_receipt: Mapping[str, Any],
    mas_receipt_consumption: Mapping[str, Any],
) -> list[str]:
    if _transition_receipt_requires_typed_blocker(
        transition_receipt=transition_receipt,
        mas_receipt_consumption=mas_receipt_consumption,
    ):
        return ["record_typed_blocker"]
    if _transition_receipt_requires_route_checkpoint(
        transition_receipt=transition_receipt,
        mas_receipt_consumption=mas_receipt_consumption,
    ):
        return ["consume_route_back_checkpoint_or_materialize_terminalizer_outcome"]
    return [
        "consume_opl_transition_receipt",
        "route_terminal_closeout_to_mas_owner_gate",
    ]


def _transition_receipt_requires_route_checkpoint(
    *,
    transition_receipt: Mapping[str, Any],
    mas_receipt_consumption: Mapping[str, Any],
) -> bool:
    return (
        _text(mas_receipt_consumption.get("next_legal_action"))
        == "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
        or _text(transition_receipt.get("route_back_evidence_ref")) is not None
        or _text(mas_receipt_consumption.get("route_back_evidence_ref")) is not None
    )


def _transition_receipt_requires_typed_blocker(
    *,
    transition_receipt: Mapping[str, Any],
    mas_receipt_consumption: Mapping[str, Any],
) -> bool:
    return (
        _text(transition_receipt.get("receipt_status"))
        == "typed_runtime_blocker_observed"
        or _text(transition_receipt.get("typed_runtime_blocker_ref")) is not None
        or _text(mas_receipt_consumption.get("next_legal_action"))
        == "record_typed_blocker"
        or _text(mas_receipt_consumption.get("typed_runtime_blocker_ref")) is not None
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_mapping(*values: Mapping[str, Any]) -> dict[str, Any]:
    for value in values:
        if value:
            return dict(value)
    return {}


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
    "attach_paper_mission_next_action",
    "paper_mission_next_action_envelope",
]
