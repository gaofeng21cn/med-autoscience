from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.cli.paper_mission_commands.common import (
    _first_text,
    _mapping,
    _mapping_list,
    _optional_text,
)
from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    align_carrier_readback_with_owner_consumption as _align_carrier_readback_with_owner_consumption,
)
from med_autoscience.paper_mission_owner_answer import (
    terminal_owner_gate_authority_consume_readback as _terminal_owner_gate_authority_consume_readback,
    terminal_owner_gate_owner_answer_readback as _terminal_owner_gate_owner_answer_readback,
)
from med_autoscience.paper_mission_terminal_owner_gate import (
    terminal_owner_gate_authority_readback as _terminal_owner_gate_authority_readback,
    terminal_owner_gate_from_carrier_readback as _terminal_owner_gate_from_carrier_readback,
)


def _receipt_owner_consumed_route_checkpoint(
    readback: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping(readback)
    if _optional_text(payload.get("status")) != "owner_consumption_applied":
        return False
    consumption = _mapping(payload.get("mas_receipt_consumption"))
    return _optional_text(consumption.get("status")) == "owner_consumed_route_checkpoint"


def _align_current_carrier_owner_consumption(
    *,
    transaction_output_fields: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> dict[str, Any]:
    fields = dict(transaction_output_fields)
    changed = False
    current = _mapping(fields.get("current_opl_runtime_carrier_readback"))
    aligned_current = current
    preserve_direct_successor = _preserve_direct_successor_runtime_readback(
        transaction_output_fields=fields,
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
    )
    if current and not preserve_direct_successor:
        aligned_current = _align_carrier_readback_with_owner_consumption(
            carrier_readback=current,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        )
        if aligned_current != current:
            fields["current_opl_runtime_carrier_readback"] = aligned_current
            changed = True
    direct = _mapping(fields.get("domain_transition_direct_stage_attempt"))
    if direct and aligned_current != current:
        fields["domain_transition_direct_stage_attempt"] = {
            **direct,
            "opl_runtime_carrier_readback": aligned_current,
        }
    carrier = _mapping(fields.get("opl_runtime_carrier_readback"))
    if carrier:
        aligned_carrier = _align_carrier_readback_with_owner_consumption(
            carrier_readback=carrier,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        )
        if aligned_carrier != carrier:
            fields["opl_runtime_carrier_readback"] = aligned_carrier
            changed = True
            aligned_gate = _terminal_owner_gate_from_carrier_readback(aligned_carrier)
            owner_answer_readback = {}
            transaction_readback = _mapping(fields.get("paper_mission_transaction_readback"))
            if transaction_readback:
                paper_mission_transaction = _mapping(
                    transaction_readback.get("paper_mission_transaction")
                )
                if paper_mission_transaction and aligned_gate:
                    owner_answer_readback = _terminal_owner_gate_owner_answer_readback(
                        terminal_owner_gate=aligned_gate,
                        paper_mission_transaction=paper_mission_transaction,
                        artifact_delta_refs=_mapping_list(
                            transaction_readback.get("artifact_delta_refs")
                        )
                        or _mapping_list(
                            paper_mission_transaction.get("artifact_delta_refs")
                        ),
                        paper_audit_pack_refs=_mapping(
                            transaction_readback.get("paper_audit_pack_refs")
                        )
                        or _mapping(
                            paper_mission_transaction.get("paper_audit_pack_refs")
                        ),
                    )
                authority_readback = _terminal_owner_gate_authority_readback(aligned_gate)
                if owner_answer_readback:
                    authority_readback = _terminal_owner_gate_authority_consume_readback(
                        terminal_owner_gate_authority_readback=authority_readback,
                        owner_answer_readback=owner_answer_readback,
                    )
                fields["paper_mission_transaction_readback"] = {
                    **transaction_readback,
                    "opl_runtime_carrier_readback": aligned_carrier,
                    "terminal_owner_gate": aligned_gate or None,
                    "terminal_owner_gate_authority_readback": authority_readback or None,
                    "terminal_owner_gate_owner_answer_readback": (
                        owner_answer_readback or None
                    ),
                }
            if aligned_gate:
                fields["terminal_owner_gate"] = aligned_gate
                authority_readback = _terminal_owner_gate_authority_readback(aligned_gate)
                if owner_answer_readback:
                    authority_readback = _terminal_owner_gate_authority_consume_readback(
                        terminal_owner_gate_authority_readback=authority_readback,
                        owner_answer_readback=owner_answer_readback,
                    )
                fields["terminal_owner_gate_authority_readback"] = authority_readback or None
                fields["terminal_owner_gate_owner_answer_readback"] = (
                    owner_answer_readback or None
                )
    return fields if changed else transaction_output_fields


def _preserve_direct_successor_runtime_readback(
    *,
    transaction_output_fields: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> bool:
    direct = _mapping(transaction_output_fields.get("domain_transition_direct_stage_attempt"))
    if not direct:
        return False
    handoff = _mapping(direct.get("opl_route_handoff"))
    successor_owner_consumption_ref = _optional_text(
        handoff.get("owner_consumption_readback_ref")
    )
    if successor_owner_consumption_ref is None:
        return False
    applied_owner_consumption_ref = _first_text(
        receipt_owner_consumption_readback.get("source_ref"),
        receipt_owner_consumption_readback.get("decision_ref"),
    )
    if successor_owner_consumption_ref != applied_owner_consumption_ref:
        return False
    carrier_readback = _mapping(direct.get("opl_runtime_carrier_readback"))
    if _carrier_matches_owner_consumed_stage_attempt(
        carrier_readback=carrier_readback,
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
    ):
        return False
    carrier_status = _optional_text(carrier_readback.get("carrier_status"))
    return carrier_status in {
        "opl_runtime_attempt_running_observed",
        "opl_runtime_terminal_readback_observed",
    }


def _carrier_matches_owner_consumed_stage_attempt(
    *,
    carrier_readback: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> bool:
    carrier_identities = _carrier_stage_attempt_identities(carrier_readback)
    receipt_identities = _receipt_owner_consumption_stage_attempt_identities(
        receipt_owner_consumption_readback
    )
    return bool(carrier_identities and receipt_identities & carrier_identities)


def _carrier_stage_attempt_identities(carrier_readback: Mapping[str, Any]) -> set[str]:
    identities: set[str] = set()
    for surface in (
        carrier_readback,
        _mapping(carrier_readback.get("opl_transition_receipt")),
        _mapping(carrier_readback.get("receipt_evidence")),
        _mapping(carrier_readback.get("terminal_closeout")),
    ):
        _add_stage_attempt_identity(identities, surface.get("stage_attempt_id"))
        _add_stage_attempt_identity(identities, surface.get("stage_attempt_ref"))
        _add_stage_attempt_identity(identities, surface.get("receipt_ref"))
        _add_stage_attempt_identity(identities, surface.get("receipt_evidence_ref"))
    return identities


def _receipt_owner_consumption_stage_attempt_identities(
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> set[str]:
    identities: set[str] = set()
    stage_closure_decision = _mapping(
        receipt_owner_consumption_readback.get("stage_closure_decision")
    )
    for surface in (
        receipt_owner_consumption_readback,
        _mapping(receipt_owner_consumption_readback.get("mas_receipt_consumption")),
        _mapping(receipt_owner_consumption_readback.get("opl_transition_receipt")),
        _mapping(receipt_owner_consumption_readback.get("receipt_evidence")),
        _mapping(stage_closure_decision.get("opl_closeout")),
    ):
        _add_stage_attempt_identity(identities, surface.get("stage_attempt_id"))
        _add_stage_attempt_identity(identities, surface.get("stage_attempt_ref"))
        _add_stage_attempt_identity(identities, surface.get("receipt_ref"))
        _add_stage_attempt_identity(identities, surface.get("receipt_evidence_ref"))
    return identities


def _add_stage_attempt_identity(identities: set[str], value: object) -> None:
    text = _optional_text(value)
    if text is None:
        return
    identities.add(text)
    prefix = "opl://stage-attempts/"
    if text.startswith(prefix):
        identities.add(text.removeprefix(prefix))
