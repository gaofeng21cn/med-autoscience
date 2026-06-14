from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def action_matches_obligation(
    action: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    if _text(action.get("status")) != "ready":
        return False
    if not _identity_fields_match(action, obligation=obligation):
        return False
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if fingerprint is None:
        return False
    action_fingerprints = {
        value
        for value in (
            _text(action.get("work_unit_fingerprint")),
            _text(action.get("action_fingerprint")),
            _text(action.get("source_fingerprint")),
            _text(_mapping(action.get("owner_route_currentness_basis")).get("work_unit_fingerprint")),
            _text(_mapping(action.get("owner_route_currentness_basis")).get("source_fingerprint")),
            _text(_mapping(action.get("currentness_basis")).get("work_unit_fingerprint")),
            _text(_mapping(action.get("currentness_basis")).get("source_fingerprint")),
            _text(_mapping(action.get("repair_progress_precedence")).get("source_fingerprint")),
        )
        if value is not None
    }
    return fingerprint in action_fingerprints


def current_work_unit_matches_obligation(
    current_work_unit: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    if _text(obligation.get("study_id")) is not None and _text(current_work_unit.get("study_id")) != _text(
        obligation.get("study_id")
    ):
        return False
    if not _identity_fields_match(current_work_unit, obligation=obligation):
        return False
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if fingerprint is None:
        return False
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    current_fingerprints = {
        value
        for value in (
            _text(current_work_unit.get("work_unit_fingerprint")),
            _text(current_work_unit.get("action_fingerprint")),
            _text(currentness_basis.get("work_unit_fingerprint")),
            _text(currentness_basis.get("action_fingerprint")),
        )
        if value is not None
    }
    return fingerprint in current_fingerprints


def _identity_fields_match(candidate: Mapping[str, Any], *, obligation: Mapping[str, Any]) -> bool:
    action_type = _text(obligation.get("action_type"))
    if action_type is not None and _text(candidate.get("action_type")) != action_type:
        return False
    work_unit_id = _text(obligation.get("work_unit_id"))
    if work_unit_id is not None and _text(candidate.get("work_unit_id")) != work_unit_id:
        return False
    return True


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


__all__ = [
    "action_matches_obligation",
    "current_work_unit_matches_obligation",
]
