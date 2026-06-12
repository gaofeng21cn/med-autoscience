from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def currentness_identity(progress: Mapping[str, Any]) -> dict[str, Any]:
    envelope = _mapping(progress.get("current_execution_envelope"))
    blocker = _mapping(envelope.get("typed_blocker"))
    current_work_unit = _mapping(progress.get("current_work_unit"))
    current_work_unit_state = _mapping(current_work_unit.get("state"))
    current_work_unit_blocker = _mapping(current_work_unit_state.get("typed_blocker"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    source_refs = {
        key: value
        for key, value in {
            "work_unit_id": work_unit_id(progress),
            "work_unit_fingerprint": (
                _text(blocker.get("work_unit_fingerprint"))
                or _text(blocker.get("action_fingerprint"))
                or _text(current_work_unit_blocker.get("work_unit_fingerprint"))
                or _text(current_work_unit_blocker.get("action_fingerprint"))
                or _text(current_work_unit.get("work_unit_fingerprint"))
                or _text(current_work_unit.get("action_fingerprint"))
                or _text(currentness_basis.get("work_unit_fingerprint"))
                or _text(currentness_basis.get("action_fingerprint"))
            ),
            "source_eval_id": (
                _text(blocker.get("source_eval_id"))
                or _text(current_work_unit_blocker.get("source_eval_id"))
                or _text(current_work_unit.get("source_eval_id"))
                or _text(currentness_basis.get("source_eval_id"))
            ),
            "owner_route_currentness_basis": currentness_basis,
        }.items()
        if value not in (None, "", [], {})
    }
    return {
        key: value
        for key, value in {
            "action_type": (
                _text(blocker.get("action_type"))
                or _text(current_work_unit_blocker.get("action_type"))
                or _text(current_work_unit.get("action_type"))
            ),
            "work_unit_id": source_refs.get("work_unit_id"),
            "work_unit_fingerprint": source_refs.get("work_unit_fingerprint"),
            "action_fingerprint": source_refs.get("work_unit_fingerprint"),
            "source_eval_id": source_refs.get("source_eval_id"),
            "owner_route_currentness_basis": currentness_basis,
            "owner_route": {"source_refs": source_refs},
        }.items()
        if value not in (None, "", [], {})
    }


def work_unit_id(progress: Mapping[str, Any]) -> str | None:
    envelope = _mapping(progress.get("current_execution_envelope"))
    blocker = _mapping(envelope.get("typed_blocker"))
    current_work_unit = _mapping(progress.get("current_work_unit"))
    current_work_unit_state = _mapping(current_work_unit.get("state"))
    current_work_unit_blocker = _mapping(current_work_unit_state.get("typed_blocker"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    return (
        _work_unit_id(blocker.get("work_unit_id"))
        or _work_unit_id(current_work_unit_blocker.get("work_unit_id"))
        or _work_unit_id(current_work_unit.get("work_unit_id"))
        or _work_unit_id(currentness_basis.get("work_unit_id"))
    )


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("work_unit_id")) or _text(value.get("unit_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["currentness_identity", "work_unit_id"]
