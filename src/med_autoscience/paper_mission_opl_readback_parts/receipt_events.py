from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_opl_readback_parts.primitives import (
    mapping,
    text_list,
    text_value,
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
    if text_value(receipt.get("surface_kind")) != "opl_transition_receipt":
        return False
    for field in (
        "study_id",
        "paper_mission_transaction_ref",
        "opl_route_command_ref",
    ):
        carrier_value = text_value(carrier.get(field))
        if carrier_value is not None and text_value(receipt.get(field)) != carrier_value:
            return False
    command_kind = carrier_command_kind(carrier)
    if not matches_receipt_command_kind(
        carrier_command_kind=command_kind,
        observed_command_kind=text_value(receipt.get("command_kind")),
    ):
        return False
    route_target = carrier_route_target(carrier)
    if route_target is not None and text_value(receipt.get("route_target")) != route_target:
        return False
    boundary = mapping(receipt.get("authority_boundary"))
    return (
        receipt.get("can_change_stage_terminal_decision") is False
        and receipt.get("can_select_next_owner") is False
        and boundary.get("writes_owner_receipt") is False
        and boundary.get("writes_typed_blocker") is False
        and boundary.get("writes_human_gate") is False
        and boundary.get("writes_current_package") is False
        and boundary.get("can_claim_paper_progress") is False
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
