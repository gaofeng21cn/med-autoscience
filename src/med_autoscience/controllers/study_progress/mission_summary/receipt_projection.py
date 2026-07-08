from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _summary_helpers():
    from med_autoscience.controllers.study_progress import mission_summary

    return mission_summary


def _mapping(value: object) -> dict[str, Any]:
    return _summary_helpers()._mapping(value)


def _non_empty_text(value: object) -> str | None:
    return _summary_helpers()._non_empty_text(value)


def _summary_with_receipt_projection(
    summary: Mapping[str, Any],
    *,
    progress: Mapping[str, Any] | None = None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    updated = dict(summary)
    updated["opl_transition_receipt"] = _opl_transition_receipt(
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
        summary=updated,
    )
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
) -> dict[str, Any]:
    for source in _receipt_projection_sources(
        summary=summary,
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
    ):
        receipt = _mapping(source.get("opl_transition_receipt"))
        if _non_empty_text(receipt.get("surface_kind")) == "opl_transition_receipt":
            return {
                **dict(receipt),
                "role": "transport_receipt_only",
                "can_change_stage_terminal_decision": False,
                "can_select_next_owner": False,
                "can_claim_paper_progress": False,
            }
    return {
        "surface_kind": "opl_transition_receipt",
        "status": "not_requested_from_study_progress",
        "role": "transport_receipt_only",
        "can_change_stage_terminal_decision": False,
        "can_select_next_owner": False,
    }


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


def _receipt_evidence(
    *,
    summary: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    consumption_ledger_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    for source in _receipt_projection_sources(
        summary=summary,
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
    ):
        evidence = _mapping(source.get("receipt_evidence"))
        if _non_empty_text(evidence.get("surface_kind")) == "mas_receipt_evidence":
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
    for source in _receipt_projection_sources(
        summary=summary,
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
    ):
        consumption = _mapping(source.get("mas_receipt_consumption"))
        if _non_empty_text(consumption.get("surface_kind")) == (
            "mas_receipt_consumption_projection"
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
