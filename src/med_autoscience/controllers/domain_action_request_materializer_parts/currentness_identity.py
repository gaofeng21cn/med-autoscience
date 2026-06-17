from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route_attempt_protocol


CURRENTNESS_BASIS_FIELDS = owner_route_attempt_protocol.CURRENTNESS_BASIS_FIELDS


def currentness_basis(*candidates: object) -> dict[str, Any]:
    return owner_route_attempt_protocol.normalize_currentness_sources(*candidates)


def normalize_currentness_sources(*candidates: object) -> dict[str, Any]:
    return currentness_basis(*candidates)


def normalize_owner_route_currentness(
    owner_route: Mapping[str, Any],
    *candidates: object,
) -> dict[str, Any]:
    return with_owner_route_basis(
        owner_route,
        basis=normalize_currentness_sources(owner_route_basis(owner_route), *candidates),
    )


def normalize_transition_request_currentness(
    transition_request: Mapping[str, Any],
    *candidates: object,
) -> dict[str, Any]:
    return with_transition_request_basis(
        transition_request,
        basis=normalize_currentness_sources(
            _mapping(transition_request).get("currentness_basis"),
            *candidates,
        ),
    )


def normalize_action_handoff_currentness(
    action: Mapping[str, Any],
    *candidates: object,
) -> dict[str, Any]:
    return with_action_handoff_basis(
        action,
        basis=normalize_currentness_sources(*candidates),
    )


def owner_route_basis(owner_route: Mapping[str, Any]) -> dict[str, Any]:
    route = _mapping(owner_route)
    source_refs = _mapping(route.get("source_refs"))
    return currentness_basis(
        owner_route_attempt_protocol.currentness_basis(route),
        source_refs,
        route,
        _mapping(route.get("currentness_contract")).get("basis"),
        source_refs.get("owner_route_currentness_basis"),
    )


def action_basis(action: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(action)
    return currentness_basis(
        {
            "source_eval_id": payload.get("source_eval_id"),
            "source_fingerprint": payload.get("source_fingerprint"),
            "work_unit_id": payload.get("controller_work_unit_id")
            or payload.get("executable_work_unit")
            or payload.get("work_unit_id"),
            "work_unit_fingerprint": payload.get("work_unit_fingerprint")
            or payload.get("action_fingerprint"),
        }
    )


def source_eval_id_from_domain_transition(transition: Mapping[str, Any]) -> str | None:
    payload = _mapping(transition)
    completion = _mapping(payload.get("completion_receipt_consumption"))
    publication_eval_ref = _mapping(payload.get("publication_eval_ref"))
    return _first_text(
        completion.get("eval_id"),
        payload.get("source_eval_id"),
        payload.get("publication_eval_id"),
        publication_eval_ref.get("eval_id"),
    )


def source_eval_id_from_study(study: Mapping[str, Any]) -> str | None:
    return source_eval_id_from_domain_transition(_mapping(_mapping(study).get("domain_transition")))


def with_owner_route_basis(
    owner_route: Mapping[str, Any],
    *,
    basis: Mapping[str, Any],
) -> dict[str, Any]:
    route = dict(owner_route)
    merged_basis = currentness_basis(owner_route_basis(route), basis)
    if not route or not merged_basis:
        return route
    source_refs = dict(_mapping(route.get("source_refs")))
    source_refs["owner_route_currentness_basis"] = currentness_basis(
        source_refs.get("owner_route_currentness_basis"),
        merged_basis,
    )
    if _text(merged_basis.get("source_eval_id")) is not None:
        source_refs["source_eval_id"] = merged_basis["source_eval_id"]
    route["source_refs"] = source_refs
    currentness_contract = dict(_mapping(route.get("currentness_contract")))
    currentness_contract["basis"] = currentness_basis(
        currentness_contract.get("basis"),
        merged_basis,
    )
    route["currentness_contract"] = currentness_contract
    return route


def with_transition_request_basis(
    transition_request: Mapping[str, Any],
    *,
    basis: Mapping[str, Any],
) -> dict[str, Any]:
    request = dict(transition_request)
    merged_basis = currentness_basis(request.get("currentness_basis"), basis)
    if merged_basis:
        request["currentness_basis"] = merged_basis
    return request


def with_action_handoff_basis(
    action: Mapping[str, Any],
    *,
    basis: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(action)
    handoff_packet = dict(_mapping(payload.get("handoff_packet")))
    owner_route = _mapping(payload.get("owner_route")) or _mapping(handoff_packet.get("owner_route"))
    merged_basis = currentness_basis(
        owner_route_basis(owner_route),
        action_basis(payload),
        action_basis(handoff_packet),
        basis,
    )
    if not merged_basis:
        return payload
    for key in ("source_eval_id", "source_fingerprint", "work_unit_id", "work_unit_fingerprint"):
        if _text(merged_basis.get(key)) is not None:
            payload[key] = merged_basis[key]
    normalized_route = with_owner_route_basis(owner_route, basis=merged_basis)
    if normalized_route:
        payload["owner_route"] = normalized_route
    if handoff_packet:
        for key in ("source_eval_id", "source_fingerprint", "work_unit_id", "work_unit_fingerprint"):
            if _text(merged_basis.get(key)) is not None:
                handoff_packet[key] = merged_basis[key]
        if normalized_route:
            handoff_packet["owner_route"] = normalized_route
        payload["handoff_packet"] = handoff_packet
    return payload


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _text(value):
            return text
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "action_basis",
    "currentness_basis",
    "normalize_action_handoff_currentness",
    "normalize_currentness_sources",
    "normalize_owner_route_currentness",
    "normalize_transition_request_currentness",
    "owner_route_basis",
    "source_eval_id_from_domain_transition",
    "source_eval_id_from_study",
    "with_action_handoff_basis",
    "with_owner_route_basis",
    "with_transition_request_basis",
]
