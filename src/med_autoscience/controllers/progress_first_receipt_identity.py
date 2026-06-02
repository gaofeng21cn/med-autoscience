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
GATE_CLEARING_BATCH_RECEIPT_REF = "artifacts/controller/gate_clearing_batch/latest.json"
GATE_CLEARING_BATCH_CONSUMED_STATUSES = frozenset(
    {
        "executed",
        "completed",
        "fresh",
        "skipped_stale_gate_replay_closed",
        "platform_terminal",
    }
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


def canonical_work_unit_identity_from_gate_clearing_batch(record: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping(record)
    basis = _mapping(payload.get("owner_route_currentness_basis"))
    currentness = _mapping(payload.get("work_unit_currentness"))
    explicit_work_unit = _mapping(payload.get("explicit_publication_work_unit"))
    return _compact_mapping(
        {
            "work_unit_id": _text(basis.get("work_unit_id"))
            or _text(payload.get("work_unit_id"))
            or _text(payload.get("source_work_unit_id"))
            or _text(currentness.get("explicit_publication_work_unit_id"))
            or _work_unit_id(explicit_work_unit),
            "work_unit_fingerprint": _text(basis.get("work_unit_fingerprint"))
            or _text(payload.get("work_unit_fingerprint"))
            or _text(payload.get("source_work_unit_fingerprint"))
            or _text(currentness.get("explicit_work_unit_fingerprint"))
            or _text(explicit_work_unit.get("fingerprint")),
            "source_eval_id": _text(basis.get("source_eval_id")) or _text(payload.get("source_eval_id")),
            "truth_epoch": _text(basis.get("truth_epoch")) or _text(payload.get("truth_epoch")),
            "runtime_health_epoch": _text(basis.get("runtime_health_epoch"))
            or _text(payload.get("runtime_health_epoch")),
        }
    )


def gate_clearing_batch_receipt_consumption_for_transition(
    *,
    transition: Mapping[str, Any],
    record: Mapping[str, Any],
    receipt_ref: str | None = None,
) -> dict[str, Any] | None:
    if not gate_clearing_batch_receipt_matches_transition_work_unit(
        transition=transition,
        record=record,
    ):
        return None
    identity = canonical_work_unit_identity_from_gate_clearing_batch(record)
    return {
        "consumption_status": "receipt_consumed",
        "receipt_ref": receipt_ref or GATE_CLEARING_BATCH_RECEIPT_REF,
        "receipt_kind": "gate_clearing_batch",
        "execution_status": _text(record.get("status")),
        "work_unit_id": _text(identity.get("work_unit_id")),
        "work_unit_fingerprint": _text(identity.get("work_unit_fingerprint")),
        "canonical_work_unit_identity": identity or None,
    }


def gate_clearing_batch_receipt_matches_transition_work_unit(
    *,
    transition: Mapping[str, Any],
    record: Mapping[str, Any],
) -> bool:
    if not _transition_is_gate_clearing_batch(transition):
        return False
    if _text(record.get("status")) not in GATE_CLEARING_BATCH_CONSUMED_STATUSES:
        return False
    receipt_identity = canonical_work_unit_identity_from_gate_clearing_batch(record)
    transition_identity = canonical_work_unit_identity_from_transition(transition)
    receipt_eval_id = _text(receipt_identity.get("source_eval_id"))
    transition_eval_id = _text(transition_identity.get("source_eval_id"))
    if receipt_eval_id is None or transition_eval_id is None or receipt_eval_id != transition_eval_id:
        return False
    receipt_work_unit_ids = _gate_clearing_work_unit_ids(record=record, identity=receipt_identity)
    transition_work_unit_ids = _work_unit_identity_values(transition_identity, key="work_unit_id")
    if receipt_work_unit_ids and transition_work_unit_ids:
        return bool(receipt_work_unit_ids & transition_work_unit_ids)
    receipt_fingerprints = _gate_clearing_work_unit_fingerprints(record=record, identity=receipt_identity)
    transition_fingerprints = _work_unit_identity_values(transition_identity, key="work_unit_fingerprint")
    if receipt_fingerprints and transition_fingerprints:
        return bool(receipt_fingerprints & transition_fingerprints)
    return False


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
        if transition_fingerprint:
            return bool(receipt_fingerprint and receipt_fingerprint == transition_fingerprint)
        if receipt_fingerprint:
            receipt_work_unit_id = _text(receipt_identity.get("work_unit_id"))
            transition_work_unit_id = _text(transition_identity.get("work_unit_id"))
            return bool(receipt_work_unit_id and transition_work_unit_id and receipt_work_unit_id == transition_work_unit_id)
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


def _transition_is_gate_clearing_batch(transition: Mapping[str, Any]) -> bool:
    return (
        _text(transition.get("controller_action")) == "run_gate_clearing_batch"
        or _text(transition.get("owner")) == "gate_clearing_batch"
    )


def _gate_clearing_work_unit_ids(
    *,
    record: Mapping[str, Any],
    identity: Mapping[str, Any],
) -> set[str]:
    currentness = _mapping(record.get("work_unit_currentness"))
    explicit_work_unit = _mapping(record.get("explicit_publication_work_unit"))
    return _text_set(
        (
            identity.get("work_unit_id"),
            record.get("work_unit_id"),
            record.get("source_work_unit_id"),
            currentness.get("explicit_publication_work_unit_id"),
            _work_unit_id(explicit_work_unit),
        )
    )


def _gate_clearing_work_unit_fingerprints(
    *,
    record: Mapping[str, Any],
    identity: Mapping[str, Any],
) -> set[str]:
    currentness = _mapping(record.get("work_unit_currentness"))
    explicit_work_unit = _mapping(record.get("explicit_publication_work_unit"))
    return _text_set(
        (
            identity.get("work_unit_fingerprint"),
            record.get("work_unit_fingerprint"),
            record.get("source_work_unit_fingerprint"),
            currentness.get("explicit_work_unit_fingerprint"),
            explicit_work_unit.get("fingerprint"),
        )
    )


def _work_unit_identity_values(identity: Mapping[str, Any], *, key: str) -> set[str]:
    return _text_set((identity.get(key),))


def _text_set(values: object) -> set[str]:
    if not isinstance(values, tuple | list | set):
        values = (values,)
    return {text for value in values if (text := _text(value)) is not None}


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
    "canonical_work_unit_identity_from_gate_clearing_batch",
    "canonical_work_unit_identity_from_owner_route",
    "canonical_work_unit_identity_from_transition",
    "consumed_ai_reviewer_receipt_matches_transition_work_unit",
    "gate_clearing_batch_receipt_consumption_for_transition",
    "gate_clearing_batch_receipt_matches_transition_work_unit",
]
