from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import _mapping_copy, _non_empty_text


def terminal_consumption_matches_current_pending_identity(
    *,
    consumed: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    consumed_identity = action_identity_for_terminal_consumption(consumed)
    if not consumed_identity:
        return False
    for candidate in terminal_consumption_current_identity_candidates(payload):
        if same_terminal_consumption_identity(consumed_identity, candidate):
            return True
    return False


def terminal_consumption_current_identity_candidates(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for value in (
        payload.get("current_executable_owner_action"),
        payload.get("current_work_unit"),
    ):
        identity = action_identity_for_terminal_consumption(_mapping_copy(value))
        if identity:
            candidates.append(identity)
    for key in ("provider_admission_candidates", "transition_request_candidates"):
        for item in payload.get(key) or []:
            if not isinstance(item, Mapping):
                continue
            identity = action_identity_for_terminal_consumption(item)
            if identity:
                candidates.append(identity)
    return candidates


def action_identity_for_terminal_consumption(value: Mapping[str, Any]) -> dict[str, Any]:
    payload = _mapping_copy(value)
    if not payload:
        return {}
    work_unit_fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
        payload.get("action_fingerprint")
    )
    identity = {
        key: result
        for key, result in {
            "owner": _non_empty_text(payload.get("next_owner")) or _non_empty_text(payload.get("owner")),
            "action_type": _non_empty_text(payload.get("action_type")),
            "work_unit_id": _non_empty_text(payload.get("work_unit_id"))
            or _non_empty_text(payload.get("next_work_unit")),
            "work_unit_fingerprint": work_unit_fingerprint,
            "route_identity_key": _non_empty_text(payload.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(payload.get("attempt_idempotency_key")),
        }.items()
        if result not in (None, "")
    }
    if (
        _non_empty_text(identity.get("action_type")) is None
        or _non_empty_text(identity.get("work_unit_id")) is None
        or _non_empty_text(identity.get("work_unit_fingerprint")) is None
    ):
        return {}
    return identity


def same_terminal_consumption_identity(
    consumed: Mapping[str, Any],
    current: Mapping[str, Any],
) -> bool:
    for key in ("action_type", "work_unit_id", "work_unit_fingerprint"):
        if _non_empty_text(consumed.get(key)) != _non_empty_text(current.get(key)):
            return False
    for key in ("route_identity_key", "attempt_idempotency_key"):
        consumed_value = _non_empty_text(consumed.get(key))
        current_value = _non_empty_text(current.get(key))
        if consumed_value is not None and current_value is not None and consumed_value != current_value:
            return False
    return True


def transition_request_candidates_from_payload(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in payload.get("transition_request_candidates") or []
        if isinstance(item, Mapping)
    ]


def terminal_consumption_candidates_from_payload(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for key in ("provider_admission_candidates", "transition_request_candidates"):
        candidates.extend(
            dict(item)
            for item in payload.get(key) or []
            if isinstance(item, Mapping)
        )
    return candidates


def provider_admission_candidate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    candidate_payload = dict(payload)
    for key in (
        "provider_admission_terminal_closeout_consumed",
        "paper_autonomy_supervisor_decision",
        "provider_admission_blocked_by_supervisor_decision",
    ):
        candidate_payload.pop(key, None)
    return candidate_payload


__all__ = [
    "provider_admission_candidate_payload",
    "terminal_consumption_candidates_from_payload",
    "terminal_consumption_matches_current_pending_identity",
    "transition_request_candidates_from_payload",
]
