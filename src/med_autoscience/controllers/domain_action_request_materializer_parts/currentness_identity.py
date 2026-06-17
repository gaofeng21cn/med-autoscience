from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route_attempt_protocol


CURRENTNESS_BASIS_FIELDS = frozenset(
    {
        "source_eval_id",
        "work_unit_id",
        "work_unit_fingerprint",
        "truth_epoch",
        "runtime_health_epoch",
    }
)


def currentness_basis(*candidates: object) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for candidate in candidates:
        for key, value in _mapping(candidate).items():
            if key in CURRENTNESS_BASIS_FIELDS and _text(value) is not None:
                payload[key] = value
    return payload


def owner_route_basis(owner_route: Mapping[str, Any]) -> dict[str, Any]:
    route = _mapping(owner_route)
    source_refs = _mapping(route.get("source_refs"))
    return currentness_basis(
        owner_route_attempt_protocol.currentness_basis(route),
        _mapping(route.get("currentness_contract")).get("basis"),
        source_refs.get("owner_route_currentness_basis"),
    )


def action_basis(action: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(action)
    return currentness_basis(
        {
            "source_eval_id": payload.get("source_eval_id"),
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
    if _text(merged_basis.get("source_eval_id")) is not None:
        payload["source_eval_id"] = merged_basis["source_eval_id"]
    normalized_route = with_owner_route_basis(owner_route, basis=merged_basis)
    if normalized_route:
        payload["owner_route"] = normalized_route
    if handoff_packet:
        if _text(merged_basis.get("source_eval_id")) is not None:
            handoff_packet["source_eval_id"] = merged_basis["source_eval_id"]
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
    "owner_route_basis",
    "source_eval_id_from_domain_transition",
    "source_eval_id_from_study",
    "with_action_handoff_basis",
    "with_owner_route_basis",
    "with_transition_request_basis",
]
