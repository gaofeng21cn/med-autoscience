from __future__ import annotations

from collections.abc import Mapping
from typing import Any


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
    receipt_has_identity = _completion_has_work_unit_identity(completion)
    transition_has_identity = _transition_has_work_unit_identity(transition)
    if receipt_has_identity or transition_has_identity:
        receipt_fingerprint = _completion_work_unit_fingerprint(completion)
        transition_fingerprint = _transition_work_unit_fingerprint(transition)
        if receipt_fingerprint or transition_fingerprint:
            return bool(receipt_fingerprint and transition_fingerprint and receipt_fingerprint == transition_fingerprint)
        receipt_work_unit_id = _completion_work_unit_id(completion)
        transition_work_unit_id = _work_unit_id(transition.get("next_work_unit"))
        return bool(receipt_work_unit_id and transition_work_unit_id and receipt_work_unit_id == transition_work_unit_id)
    work_unit_id = _work_unit_id(transition.get("next_work_unit"))
    return bool(work_unit_id and work_unit_id.startswith("produce_ai_reviewer_publication_eval_record"))


def _completion_has_work_unit_identity(completion: Mapping[str, Any]) -> bool:
    basis = _mapping(completion.get("owner_route_currentness_basis"))
    return any(
        _text(value) is not None
        for value in (
            completion.get("work_unit_id"),
            completion.get("work_unit_fingerprint"),
            basis.get("work_unit_id"),
            basis.get("work_unit_fingerprint"),
        )
    )


def _transition_has_work_unit_identity(transition: Mapping[str, Any]) -> bool:
    source_refs = _mapping(transition.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    next_work_unit = _mapping(transition.get("next_work_unit"))
    return any(
        _text(value) is not None
        for value in (
            transition.get("work_unit_fingerprint"),
            source_refs.get("work_unit_id"),
            source_refs.get("work_unit_fingerprint"),
            basis.get("work_unit_id"),
            basis.get("work_unit_fingerprint"),
            next_work_unit.get("fingerprint"),
        )
    )


def _completion_work_unit_id(completion: Mapping[str, Any]) -> str | None:
    basis = _mapping(completion.get("owner_route_currentness_basis"))
    return _text(completion.get("work_unit_id")) or _text(basis.get("work_unit_id"))


def _completion_work_unit_fingerprint(completion: Mapping[str, Any]) -> str | None:
    basis = _mapping(completion.get("owner_route_currentness_basis"))
    return _text(completion.get("work_unit_fingerprint")) or _text(basis.get("work_unit_fingerprint"))


def _transition_work_unit_fingerprint(transition: Mapping[str, Any]) -> str | None:
    source_refs = _mapping(transition.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _text(transition.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(_mapping(transition.get("next_work_unit")).get("fingerprint"))
    )


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
