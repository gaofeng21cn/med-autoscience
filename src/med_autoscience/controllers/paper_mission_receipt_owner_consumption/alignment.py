from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.paper_mission_receipt_owner_consumption.common import (
    _first_text,
    _mapping,
    _text,
)

def align_carrier_readback_with_owner_consumption(
    *,
    carrier_readback: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    carrier = dict(_mapping(carrier_readback))
    receipt_owner_consumption = _mapping(receipt_owner_consumption_readback)
    if not carrier or not receipt_owner_consumption:
        return carrier
    applied_consumption = _mapping(receipt_owner_consumption.get("mas_receipt_consumption"))
    status = _text(applied_consumption.get("status"))
    if not status.startswith("owner_consumed_"):
        return carrier
    applied_evidence = _mapping(receipt_owner_consumption.get("receipt_evidence"))
    if _owner_consumption_matches_carrier(
        carrier=carrier,
        applied_consumption=applied_consumption,
        applied_evidence=applied_evidence,
    ):
        return _attach_owner_consumption_to_carrier(
            carrier=carrier,
            receipt_owner_consumption=receipt_owner_consumption,
            applied_consumption=applied_consumption,
            applied_evidence=applied_evidence,
        )
    if not _owner_consumption_supersedes_pending_carrier(
        carrier=carrier,
        receipt_owner_consumption=receipt_owner_consumption,
        applied_consumption=applied_consumption,
        applied_evidence=applied_evidence,
    ):
        return carrier
    return _owner_consumed_carrier_readback(
        carrier=carrier,
        receipt_owner_consumption=receipt_owner_consumption,
        applied_consumption=applied_consumption,
        applied_evidence=applied_evidence,
    )


def _attach_owner_consumption_to_carrier(
    *,
    carrier: Mapping[str, Any],
    receipt_owner_consumption: Mapping[str, Any],
    applied_consumption: Mapping[str, Any],
    applied_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    aligned = {
        **carrier,
        "receipt_evidence": {
            **dict(_mapping(carrier.get("receipt_evidence"))),
            **dict(applied_evidence),
            "authority_materialized": True,
        },
        "mas_receipt_consumption": dict(applied_consumption),
        "owner_consumption_readback_ref": _first_text(
            receipt_owner_consumption.get("source_ref"),
            receipt_owner_consumption.get("decision_ref"),
        ),
        "owner_consumption_status": _text(applied_consumption.get("status")),
    }
    if "terminal_closeout" in aligned:
        aligned["terminal_closeout"] = {
            **dict(_mapping(aligned.get("terminal_closeout"))),
            "mas_receipt_consumption": dict(applied_consumption),
        }
    return aligned


def _owner_consumption_supersedes_pending_carrier(
    *,
    carrier: Mapping[str, Any],
    receipt_owner_consumption: Mapping[str, Any],
    applied_consumption: Mapping[str, Any],
    applied_evidence: Mapping[str, Any],
) -> bool:
    carrier_consumption = _mapping(carrier.get("mas_receipt_consumption"))
    if _text(carrier_consumption.get("status")) != "requires_mas_owner_consumption":
        return False
    carrier_work_unit = _carrier_work_unit_id(carrier)
    consumed_work_unit = _receipt_owner_consumption_work_unit_id(
        receipt_owner_consumption
    )
    if carrier_work_unit is None or consumed_work_unit is None:
        return False
    if carrier_work_unit != consumed_work_unit:
        return False
    carrier_attempt_id = _stage_attempt_id_from_refs(
        _mapping(carrier.get("opl_transition_receipt")).get("stage_attempt_id"),
        _mapping(carrier.get("opl_transition_receipt")).get("stage_attempt_ref"),
        _mapping(carrier.get("terminal_closeout")).get("stage_attempt_id"),
        _mapping(carrier.get("receipt_evidence")).get("stage_attempt_ref"),
        _mapping(carrier.get("receipt_evidence")).get("receipt_ref"),
    )
    consumed_attempt_id = _stage_attempt_id_from_refs(
        _mapping(receipt_owner_consumption.get("opl_transition_receipt")).get(
            "stage_attempt_id"
        ),
        _mapping(receipt_owner_consumption.get("opl_transition_receipt")).get(
            "stage_attempt_ref"
        ),
        applied_evidence.get("stage_attempt_ref"),
        applied_evidence.get("receipt_ref"),
        applied_consumption.get("runtime_closeout_ref"),
        applied_consumption.get("route_checkpoint_evidence_ref"),
    )
    return bool(consumed_attempt_id and carrier_attempt_id != consumed_attempt_id)


def _owner_consumed_carrier_readback(
    *,
    carrier: Mapping[str, Any],
    receipt_owner_consumption: Mapping[str, Any],
    applied_consumption: Mapping[str, Any],
    applied_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    receipt = _mapping(receipt_owner_consumption.get("opl_transition_receipt"))
    stage_closure = _mapping(receipt_owner_consumption.get("stage_closure_decision"))
    opl_closeout = _mapping(stage_closure.get("opl_closeout"))
    terminal_closeout = _mapping(carrier.get("terminal_closeout"))
    consumed_attempt_id = _stage_attempt_id_from_refs(
        receipt.get("stage_attempt_id"),
        receipt.get("stage_attempt_ref"),
        applied_evidence.get("stage_attempt_ref"),
        applied_evidence.get("receipt_ref"),
        applied_consumption.get("runtime_closeout_ref"),
        applied_consumption.get("route_checkpoint_evidence_ref"),
    )
    carrier_attempt_id = _stage_attempt_id_from_refs(
        _mapping(carrier.get("opl_transition_receipt")).get("stage_attempt_id"),
        _mapping(carrier.get("opl_transition_receipt")).get("stage_attempt_ref"),
        terminal_closeout.get("stage_attempt_id"),
        _mapping(carrier.get("receipt_evidence")).get("stage_attempt_ref"),
        _mapping(carrier.get("receipt_evidence")).get("receipt_ref"),
    )
    closeout_ref = _first_text(
        applied_consumption.get("runtime_closeout_ref"),
        applied_consumption.get("route_checkpoint_evidence_ref"),
        applied_evidence.get("runtime_closeout_ref"),
        applied_evidence.get("route_checkpoint_evidence_ref"),
        terminal_closeout.get("closeout_ref"),
    )
    receipt_ref = _first_text(
        receipt.get("stage_attempt_ref"),
        applied_evidence.get("stage_attempt_ref"),
        applied_evidence.get("receipt_ref"),
        applied_consumption.get("receipt_ref"),
    )
    work_unit_id = (
        _receipt_owner_consumption_work_unit_id(receipt_owner_consumption)
        or _carrier_work_unit_id(carrier)
    )
    aligned_receipt = {
        **dict(_mapping(carrier.get("opl_transition_receipt"))),
        **dict(receipt),
        "stage_attempt_id": consumed_attempt_id,
        "stage_attempt_ref": receipt_ref,
        "work_unit_id": work_unit_id,
    }
    aligned_evidence = {
        **dict(_mapping(carrier.get("receipt_evidence"))),
        **dict(applied_evidence),
        "receipt_ref": receipt_ref,
        "runtime_closeout_ref": closeout_ref,
        "stage_attempt_ref": receipt_ref,
        "authority_materialized": True,
    }
    aligned_terminal_closeout = {
        **dict(terminal_closeout),
        **dict(opl_closeout),
        "stage_attempt_id": consumed_attempt_id,
        "work_unit_id": work_unit_id,
        "closeout_ref": closeout_ref,
        "receipt_evidence": aligned_evidence,
        "opl_transition_receipt": aligned_receipt,
        "mas_receipt_consumption": dict(applied_consumption),
    }
    return {
        **dict(carrier),
        "domain_ready_verdict": _first_text(
            applied_consumption.get("status"),
            carrier.get("domain_ready_verdict"),
        ),
        "owner_consumption_status": _text(applied_consumption.get("status")),
        "owner_consumption_readback_ref": _first_text(
            receipt_owner_consumption.get("source_ref"),
            receipt_owner_consumption.get("decision_ref"),
        ),
        "owner_consumption_aligned_current_readback": True,
        "owner_consumed_stage_attempt_id": consumed_attempt_id,
        "superseded_terminal_stage_attempt_id": carrier_attempt_id,
        "receipt_evidence": aligned_evidence,
        "opl_transition_receipt": aligned_receipt,
        "mas_receipt_consumption": dict(applied_consumption),
        "terminal_closeout": aligned_terminal_closeout,
    }


def _carrier_work_unit_id(carrier: Mapping[str, Any]) -> str | None:
    return _first_text(
        _mapping(carrier.get("opl_transition_receipt")).get("work_unit_id"),
        _mapping(carrier.get("terminal_closeout")).get("work_unit_id"),
    )


def _receipt_owner_consumption_work_unit_id(
    receipt_owner_consumption: Mapping[str, Any],
) -> str | None:
    stage_closure = _mapping(receipt_owner_consumption.get("stage_closure_decision"))
    return _first_text(
        stage_closure.get("work_unit_id"),
        _mapping(stage_closure.get("opl_closeout")).get("work_unit_id"),
        _mapping(receipt_owner_consumption.get("opl_transition_receipt")).get(
            "work_unit_id"
        ),
    )


def _owner_consumption_matches_carrier(
    *,
    carrier: Mapping[str, Any],
    applied_consumption: Mapping[str, Any],
    applied_evidence: Mapping[str, Any],
) -> bool:
    carrier_attempt_id = _stage_attempt_id_from_refs(
        _mapping(carrier.get("opl_transition_receipt")).get("stage_attempt_id"),
        _mapping(carrier.get("opl_transition_receipt")).get("stage_attempt_ref"),
        _mapping(carrier.get("receipt_evidence")).get("stage_attempt_ref"),
        _mapping(carrier.get("receipt_evidence")).get("receipt_ref"),
        _mapping(carrier.get("terminal_closeout")).get("stage_attempt_id"),
    )
    consumed_attempt_id = _stage_attempt_id_from_refs(
        applied_evidence.get("stage_attempt_ref"),
        applied_evidence.get("receipt_ref"),
        applied_consumption.get("receipt_evidence_ref"),
        applied_consumption.get("route_checkpoint_evidence_ref"),
        applied_consumption.get("typed_runtime_blocker_ref"),
    )
    if carrier_attempt_id and consumed_attempt_id:
        return carrier_attempt_id == consumed_attempt_id
    carrier_refs = _carrier_identity_refs(carrier)
    consumed_refs = {
        ref
        for ref in (
            _first_text(applied_evidence.get("runtime_closeout_ref")),
            _first_text(applied_consumption.get("route_checkpoint_evidence_ref")),
            _first_text(applied_consumption.get("typed_runtime_blocker_ref")),
            _first_text(applied_evidence.get("receipt_ref")),
            _first_text(applied_consumption.get("receipt_evidence_ref")),
        )
        if ref
    }
    return bool(carrier_refs and consumed_refs and carrier_refs.intersection(consumed_refs))


def _carrier_identity_refs(carrier: Mapping[str, Any]) -> set[str]:
    receipt = _mapping(carrier.get("opl_transition_receipt"))
    evidence = _mapping(carrier.get("receipt_evidence"))
    terminal = _mapping(carrier.get("terminal_closeout"))
    return {
        ref
        for ref in (
            _first_text(receipt.get("stage_attempt_ref")),
            _first_text(receipt.get("runtime_closeout_ref")),
            _first_text(evidence.get("receipt_ref")),
            _first_text(evidence.get("runtime_closeout_ref")),
            _first_text(terminal.get("closeout_ref")),
        )
        if ref
    }


def _stage_attempt_id_from_refs(*values: object) -> str | None:
    for value in values:
        text = _first_text(value)
        if text is None:
            continue
        if text.startswith("sat_") or text.startswith("sat-"):
            return text
        marker = "opl://stage-attempts/"
        if marker in text:
            suffix = text.split(marker, 1)[1]
            return suffix.split("/", 1)[0].split("#", 1)[0]
        path_marker = "paper_mission_stage_attempts/"
        if path_marker in text:
            suffix = text.split(path_marker, 1)[1]
            return suffix.split("/", 1)[0]
    return None
