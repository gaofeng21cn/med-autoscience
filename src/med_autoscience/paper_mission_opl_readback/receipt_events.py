from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_opl_readback.primitives import (
    idempotency_refs_mismatch,
    mapping,
    text_list,
    text_value,
)


OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_SURFACE_KIND = (
    "opl_domain_route_transition_receipt"
)
OPL_DOMAIN_ROUTE_DOMAIN_ID = "mas"
OPL_DOMAIN_ROUTE_TASK_KIND = "domain_route/stage-route"
DOMAIN_ROUTE_RECEIPT_REF_FIELDS = (
    "domain_route_handoff_ref",
    "domain_route_transaction_ref",
    "domain_route_command_ref",
)
RECEIPT_EVIDENCE_BOUNDARY_FALSE_FIELDS = (
    "receipt_is_input_ref_only",
    "can_write_owner_receipt",
    "can_write_typed_blocker",
    "can_write_human_gate",
    "can_write_current_package",
    "can_claim_paper_progress",
    "can_claim_publication_ready",
)


def event_closeout_refs(events: object) -> list[str]:
    if not isinstance(events, list | tuple):
        return []
    refs: list[str] = []
    for event in events:
        payload = mapping(mapping(event).get("payload"))
        for ref in text_list(payload.get("closeout_refs")):
            if ref not in refs:
                refs.append(ref)
    return refs


def event_opl_transition_receipt(
    *,
    events: object,
    carrier: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(events, list | tuple):
        return None
    for event in reversed(events):
        payload = mapping(mapping(event).get("payload"))
        receipt = mapping(payload.get("opl_transition_receipt"))
        if matches_opl_transition_receipt(receipt=receipt, carrier=carrier):
            return dict(receipt)
    return None


def event_mas_impact_receipt(
    *,
    events: object,
    carrier: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(events, list | tuple):
        return None
    for event in reversed(events):
        payload = mapping(mapping(event).get("payload"))
        receipt = mapping(payload.get("mas_impact_receipt"))
        if matches_mas_impact_receipt(receipt=receipt, carrier=carrier):
            return dict(receipt)
    return None


def first_opl_transition_receipt(
    carrier: Mapping[str, Any],
    *sources: Mapping[str, Any],
) -> dict[str, Any] | None:
    for source in sources:
        receipt = mapping(source.get("opl_transition_receipt"))
        if matches_opl_transition_receipt(receipt=receipt, carrier=carrier):
            return dict(receipt)
    return None


def first_mas_impact_receipt(
    carrier: Mapping[str, Any],
    *sources: Mapping[str, Any],
) -> dict[str, Any] | None:
    for source in sources:
        receipt = mapping(source.get("mas_impact_receipt"))
        if matches_mas_impact_receipt(receipt=receipt, carrier=carrier):
            return dict(receipt)
    return None


def matches_opl_transition_receipt(
    *,
    receipt: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    if (
        text_value(receipt.get("surface_kind"))
        != OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_SURFACE_KIND
    ):
        return False
    if text_value(receipt.get("domain_id")) != OPL_DOMAIN_ROUTE_DOMAIN_ID:
        return False
    if text_value(receipt.get("task_kind")) != OPL_DOMAIN_ROUTE_TASK_KIND:
        return False
    if not matches_domain_route_identity(source=receipt, carrier=carrier):
        return False
    if idempotency_refs_mismatch(
        expected_payload=carrier,
        observed_payload=receipt,
    ):
        return False
    command_kind = carrier_command_kind(carrier)
    if not matches_receipt_command_kind(
        carrier_command_kind=command_kind,
        observed_command_kind=text_value(receipt.get("command_kind")),
    ):
        return False
    route_target = carrier_route_target(carrier)
    if (
        route_target is not None
        and text_value(receipt.get("route_target")) != route_target
    ):
        return False
    boundary = mapping(receipt.get("authority_boundary"))
    return (
        text_value(receipt.get("role")) == "transport_receipt_only"
        and boundary.get("writes_domain_owner_receipt") is False
        and boundary.get("writes_domain_typed_blocker") is False
        and boundary.get("writes_domain_human_gate") is False
        and boundary.get("writes_domain_current_package") is False
        and boundary.get("can_select_next_owner") is False
        and boundary.get("can_claim_domain_progress") is False
    )


def matches_domain_route_identity(
    *,
    source: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    for field in DOMAIN_ROUTE_RECEIPT_REF_FIELDS:
        expected = text_value(carrier.get(field))
        if expected is None or text_value(source.get(field)) != expected:
            return False
    return True


def matches_receipt_evidence(
    *,
    evidence: Mapping[str, Any],
    receipt: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    if not matches_opl_transition_receipt(receipt=receipt, carrier=carrier):
        return False
    if text_value(evidence.get("surface_kind")) != "mas_receipt_evidence":
        return False
    if (
        text_value(evidence.get("receipt_kind"))
        != OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_SURFACE_KIND
    ):
        return False
    if not matches_domain_route_identity(source=evidence, carrier=carrier):
        return False
    for field in DOMAIN_ROUTE_RECEIPT_REF_FIELDS:
        if text_value(evidence.get(field)) != text_value(receipt.get(field)):
            return False
    receipt_ref = text_value(evidence.get("receipt_ref"))
    if receipt_ref is None:
        return False
    if receipt_ref not in {
        text_value(receipt.get("domain_route_handoff_ref")),
        text_value(receipt.get("stage_attempt_ref")),
        text_value(receipt.get("runtime_closeout_ref")),
    }:
        return False
    if evidence.get("can_claim_paper_progress") is not False:
        return False
    if evidence.get("can_claim_publication_ready") is not False:
        return False
    boundary = mapping(evidence.get("authority_boundary"))
    return (
        boundary.get("receipt_is_input_ref_only") is True
        and all(
            boundary.get(field) is False
            for field in RECEIPT_EVIDENCE_BOUNDARY_FALSE_FIELDS[1:]
        )
    )


def matches_mas_receipt_consumption(
    *,
    consumption: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> bool:
    if (
        text_value(consumption.get("surface_kind"))
        != "mas_receipt_consumption_projection"
    ):
        return False
    evidence_ref = text_value(evidence.get("receipt_ref"))
    if (
        evidence_ref is None
        or text_value(consumption.get("receipt_evidence_ref")) != evidence_ref
    ):
        return False
    for field in ("typed_runtime_blocker_ref", "route_back_evidence_ref"):
        expected = text_value(evidence.get(field))
        observed = text_value(consumption.get(field))
        if expected is not None and observed is not None and observed != expected:
            return False
    return not any(
        consumption.get(field) is True
        for field in (
            "can_claim_paper_progress",
            "can_claim_publication_ready",
            "can_claim_runtime_ready",
        )
    )


def matches_receipt_bundle(
    *,
    receipt: Mapping[str, Any],
    evidence: Mapping[str, Any],
    consumption: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    return matches_receipt_evidence(
        evidence=evidence,
        receipt=receipt,
        carrier=carrier,
    ) and matches_mas_receipt_consumption(
        consumption=consumption,
        evidence=evidence,
    )


def matches_mas_impact_receipt(
    *,
    receipt: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    if text_value(receipt.get("surface_kind")) != "mas_impact_receipt":
        return False
    for field in (
        "study_id",
        "paper_mission_transaction_ref",
        "opl_route_command_ref",
    ):
        carrier_value = text_value(carrier.get(field))
        if carrier_value is not None and text_value(receipt.get(field)) != carrier_value:
            return False
    return (
        receipt.get("can_claim_paper_progress") is False
        and receipt.get("can_claim_publication_ready") is False
    )


def matches_receipt_command_kind(
    *,
    carrier_command_kind: str | None,
    observed_command_kind: str | None,
) -> bool:
    if carrier_command_kind is None:
        return True
    if observed_command_kind == carrier_command_kind:
        return True
    return carrier_command_kind == "resume_stage" and observed_command_kind == "route_back"


def carrier_command_kind(carrier: Mapping[str, Any]) -> str | None:
    route = mapping(carrier.get("opl_route_command"))
    return text_value(carrier.get("command_kind")) or text_value(route.get("command_kind"))


def carrier_route_target(carrier: Mapping[str, Any]) -> str | None:
    command_kind = carrier_command_kind(carrier)
    route_target = text_value(carrier.get("route_target"))
    route = mapping(carrier.get("opl_route_command"))
    route_target = route_target or text_value(route.get("target"))
    if command_kind in {"start_next_stage", "resume_stage", "route_back"}:
        return route_target
    return None
