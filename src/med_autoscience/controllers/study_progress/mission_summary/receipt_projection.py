from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_opl_readback.receipt_events import (
    matches_mas_receipt_consumption,
    matches_opl_transition_receipt,
    matches_receipt_evidence,
)


def _summary_helpers():
    from med_autoscience.controllers.study_progress import mission_summary

    return mission_summary


def _mapping(value: object) -> dict[str, Any]:
    return _summary_helpers()._mapping(value)


def _summary_with_receipt_projection(
    summary: Mapping[str, Any],
    *,
    progress: Mapping[str, Any] | None = None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    updated = dict(summary)
    receipt = _opl_transition_receipt(
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
        summary=updated,
    )
    if receipt:
        updated["opl_transition_receipt"] = receipt
    updated["receipt_evidence"] = (
        _receipt_evidence(
            progress=progress,
            consumption_ledger_readback=consumption_ledger_readback,
            summary=updated,
        )
    )
    updated["mas_receipt_consumption"] = (
        _mas_receipt_consumption(
            progress=progress,
            consumption_ledger_readback=consumption_ledger_readback,
            summary=updated,
        )
    )
    return updated


def _opl_transition_receipt(
    *,
    progress: Mapping[str, Any] | None = None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
    summary: Mapping[str, Any] | None = None,
    carrier: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_carrier = _mapping(carrier) or _request_carrier(
        summary=summary,
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
    )
    if not request_carrier:
        return {}
    for source in _receipt_projection_sources(
        summary=summary,
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
    ):
        receipt = _mapping(source.get("opl_transition_receipt"))
        if matches_opl_transition_receipt(
            receipt=receipt,
            carrier=request_carrier,
        ):
            return {
                **dict(receipt),
                "role": "transport_receipt_only",
                "can_change_stage_terminal_decision": False,
                "can_select_next_owner": False,
                "can_claim_paper_progress": False,
            }
    return {}


def _receipt_projection_sources(
    *,
    summary: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
) -> tuple[Mapping[str, Any], ...]:
    return (
        _mapping(summary),
        _mapping(_mapping(summary).get("receipt_owner_consumption_readback")),
        _mapping(_mapping(summary).get("opl_runtime_carrier_readback")),
        _mapping(
            _mapping(_mapping(summary).get("opl_runtime_carrier_readback")).get(
                "terminal_closeout"
            )
        ),
        _mapping(progress),
        _mapping(consumption_ledger_readback),
        _mapping(_mapping(progress).get("opl_runtime_carrier_readback")),
        _mapping(_mapping(consumption_ledger_readback).get("opl_runtime_carrier_readback")),
        _mapping(
            _mapping(_mapping(progress).get("opl_runtime_carrier_readback")).get(
                "terminal_closeout"
            )
        ),
        _mapping(
            _mapping(
                _mapping(consumption_ledger_readback).get("opl_runtime_carrier_readback")
            ).get("terminal_closeout")
        ),
    )


def _request_carrier(
    *,
    summary: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    for source in (
        _mapping(summary),
        _mapping(progress),
        _mapping(consumption_ledger_readback),
    ):
        carrier = _mapping(source.get("opl_runtime_carrier"))
        if carrier:
            return carrier
    return {}


def _receipt_evidence(
    *,
    summary: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_carrier = _request_carrier(
        summary=summary,
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
    )
    for source in _receipt_projection_sources(
        summary=summary,
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
    ):
        evidence = _mapping(source.get("receipt_evidence"))
        receipt = _mapping(source.get("opl_transition_receipt"))
        if request_carrier and matches_receipt_evidence(
            evidence=evidence,
            receipt=receipt,
            carrier=request_carrier,
        ):
            return dict(evidence)
    return {
        "surface_kind": "mas_receipt_evidence",
        "status": "not_requested_from_study_progress",
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "durable_stop_allowed": False,
    }


def _mas_receipt_consumption(
    *,
    summary: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    request_carrier = _request_carrier(
        summary=summary,
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
    )
    for source in _receipt_projection_sources(
        summary=summary,
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
    ):
        consumption = _mapping(source.get("mas_receipt_consumption"))
        receipt = _mapping(source.get("opl_transition_receipt"))
        evidence = _mapping(source.get("receipt_evidence"))
        if request_carrier and matches_opl_transition_receipt(
            receipt=receipt,
            carrier=request_carrier,
        ) and matches_receipt_evidence(
            evidence=evidence,
            receipt=receipt,
            carrier=request_carrier,
        ) and matches_mas_receipt_consumption(
            consumption=consumption,
            evidence=evidence,
        ):
            return dict(consumption)
    return {
        "surface_kind": "mas_receipt_consumption_projection",
        "status": "not_requested_from_study_progress",
        "next_legal_action": "request_opl_runtime_readback",
        "forbidden_next_action": "synonymous_route_back_redrive",
        "durable_stop_allowed": False,
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
    }
