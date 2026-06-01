from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CANONICAL_WORK_UNIT_IDENTITY_KEYS = (
    "work_unit_id",
    "work_unit_fingerprint",
    "source_eval_id",
    "truth_epoch",
    "runtime_health_epoch",
)


def canonical_work_unit_identity_from_owner_route(owner_route: Mapping[str, Any]) -> dict[str, Any]:
    route = _mapping(owner_route)
    source_refs = _mapping(route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return _compact_mapping(
        {
            "work_unit_id": _text(basis.get("work_unit_id"))
            or _text(source_refs.get("work_unit_id"))
            or _text(route.get("work_unit_id")),
            "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint"))
            or _text(source_refs.get("work_unit_fingerprint"))
            or _text(route.get("work_unit_fingerprint")),
            "source_eval_id": _text(basis.get("source_eval_id"))
            or _text(source_refs.get("source_eval_id"))
            or _text(source_refs.get("publication_eval_id"))
            or _text(route.get("source_eval_id"))
            or _text(route.get("publication_eval_id")),
            "truth_epoch": _text(basis.get("truth_epoch"))
            or _text(source_refs.get("study_truth_epoch"))
            or _text(route.get("truth_epoch"))
            or _text(route.get("route_epoch")),
            "runtime_health_epoch": _text(basis.get("runtime_health_epoch"))
            or _text(source_refs.get("runtime_health_epoch"))
            or _text(route.get("runtime_health_epoch")),
        }
    )


def canonical_work_unit_identity_from_completion(completion: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(completion)
    canonical = _mapping(payload.get("canonical_work_unit_identity"))
    basis = _mapping(payload.get("owner_route_currentness_basis"))
    return _compact_mapping(
        {
            "work_unit_id": _text(canonical.get("work_unit_id"))
            or _text(payload.get("work_unit_id"))
            or _text(basis.get("work_unit_id")),
            "work_unit_fingerprint": _text(canonical.get("work_unit_fingerprint"))
            or _text(payload.get("work_unit_fingerprint"))
            or _text(basis.get("work_unit_fingerprint")),
            "source_eval_id": _text(canonical.get("source_eval_id"))
            or _text(payload.get("source_eval_id"))
            or _text(payload.get("eval_id"))
            or _text(basis.get("source_eval_id")),
            "truth_epoch": _text(canonical.get("truth_epoch"))
            or _text(payload.get("truth_epoch"))
            or _text(basis.get("truth_epoch")),
            "runtime_health_epoch": _text(canonical.get("runtime_health_epoch"))
            or _text(payload.get("runtime_health_epoch"))
            or _text(basis.get("runtime_health_epoch")),
        }
    )


def canonical_work_unit_identity_from_transition(transition: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(transition)
    source_refs = _mapping(payload.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    next_work_unit = _mapping(payload.get("next_work_unit"))
    return _compact_mapping(
        {
            "work_unit_id": _text(basis.get("work_unit_id"))
            or _text(source_refs.get("work_unit_id"))
            or _text(payload.get("work_unit_id"))
            or _work_unit_id(next_work_unit),
            "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint"))
            or _text(source_refs.get("work_unit_fingerprint"))
            or _text(payload.get("work_unit_fingerprint"))
            or _text(next_work_unit.get("fingerprint")),
            "source_eval_id": _text(basis.get("source_eval_id"))
            or _text(source_refs.get("source_eval_id"))
            or _text(source_refs.get("publication_eval_id"))
            or _text(payload.get("source_eval_id"))
            or _text(payload.get("publication_eval_id")),
            "truth_epoch": _text(basis.get("truth_epoch"))
            or _text(source_refs.get("study_truth_epoch"))
            or _text(payload.get("truth_epoch"))
            or _text(payload.get("route_epoch")),
            "runtime_health_epoch": _text(basis.get("runtime_health_epoch"))
            or _text(source_refs.get("runtime_health_epoch"))
            or _text(payload.get("runtime_health_epoch")),
        }
    )


def consumed_ai_reviewer_receipt_matches_transition_work_unit(
    *,
    transition: Mapping[str, Any],
    completion: Mapping[str, Any],
) -> bool:
    if _text(completion.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return False
    if _text(transition.get("decision_type")) != "ai_reviewer_re_eval":
        return False
    if _text(transition.get("controller_action")) != "return_to_ai_reviewer_workflow":
        return False
    receipt_identity = canonical_work_unit_identity_from_completion(completion)
    transition_identity = canonical_work_unit_identity_from_transition(transition)
    receipt_has_identity = _has_work_unit_identity(receipt_identity)
    transition_has_identity = _transition_has_explicit_work_unit_identity(transition)
    if receipt_has_identity or transition_has_identity:
        receipt_fingerprint = _text(receipt_identity.get("work_unit_fingerprint"))
        transition_fingerprint = _text(transition_identity.get("work_unit_fingerprint"))
        if receipt_fingerprint or transition_fingerprint:
            return bool(receipt_fingerprint and transition_fingerprint and receipt_fingerprint == transition_fingerprint)
        receipt_work_unit_id = _text(receipt_identity.get("work_unit_id"))
        transition_work_unit_id = _text(transition_identity.get("work_unit_id"))
        return bool(receipt_work_unit_id and transition_work_unit_id and receipt_work_unit_id == transition_work_unit_id)
    work_unit_id = _work_unit_id(transition.get("next_work_unit"))
    return bool(work_unit_id and work_unit_id.startswith("produce_ai_reviewer_publication_eval_record"))


def _has_work_unit_identity(identity: Mapping[str, Any]) -> bool:
    return any(
        _text(value) is not None
        for value in (
            identity.get("work_unit_id"),
            identity.get("work_unit_fingerprint"),
        )
    )


def _transition_has_explicit_work_unit_identity(transition: Mapping[str, Any]) -> bool:
    source_refs = _mapping(transition.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    next_work_unit = _mapping(transition.get("next_work_unit"))
    return any(
        _text(value) is not None
        for value in (
            transition.get("work_unit_id"),
            transition.get("work_unit_fingerprint"),
            source_refs.get("work_unit_id"),
            source_refs.get("work_unit_fingerprint"),
            basis.get("work_unit_id"),
            basis.get("work_unit_fingerprint"),
            next_work_unit.get("fingerprint"),
        )
    )


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _compact_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: text
        for key in CANONICAL_WORK_UNIT_IDENTITY_KEYS
        if (text := _text(payload.get(key))) is not None
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "canonical_work_unit_identity_from_completion",
    "canonical_work_unit_identity_from_owner_route",
    "canonical_work_unit_identity_from_transition",
    "consumed_ai_reviewer_receipt_matches_transition_work_unit",
]
