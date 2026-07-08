from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit.action_projection_fields import (
    action_type,
    work_unit_fingerprint,
    work_unit_id,
)
from med_autoscience.controllers.current_work_unit.primitives import mapping


def provider_handoff_matches_transition_request_action(
    *,
    provider_admission: Mapping[str, Any] | None,
    action: Mapping[str, Any],
) -> bool:
    handoff = mapping(provider_admission)
    if not handoff:
        return False
    if handoff.get("transition_request_pending_count") in (None, 0):
        return False
    for candidate in (
        handoff.get("current_executable_owner_action"),
        *mappings(handoff.get("transition_request_candidates")),
        *mappings(handoff.get("action_queue")),
    ):
        item = mapping(candidate)
        if item and same_action_identity(item, action):
            return True
    return False


def provider_handoff_matches_action(
    *,
    provider_admission: Mapping[str, Any] | None,
    action: Mapping[str, Any] | None,
) -> bool:
    payload = mapping(action)
    handoff = mapping(provider_admission)
    if not payload or not handoff:
        return False
    candidate_count = handoff.get("provider_admission_pending_count")
    candidates = mappings(handoff.get("provider_admission_candidates"))
    queued = mappings(handoff.get("action_queue"))
    if (
        candidate_count in (None, 0)
        and not candidates
        and not queued
        and not mapping(handoff.get("current_executable_owner_action"))
    ):
        return False
    for candidate in (
        handoff.get("current_executable_owner_action"),
        handoff.get("owner_action"),
        *candidates,
        *queued,
    ):
        item = mapping(candidate)
        if item and same_action_identity(item, payload):
            return True
    return False


def same_action_identity(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if action_type(left) != action_type(right):
        return False
    left_work_unit = work_unit_id(left.get("work_unit_id")) or work_unit_id(
        left.get("next_work_unit")
    )
    right_work_unit = work_unit_id(right.get("work_unit_id")) or work_unit_id(
        right.get("next_work_unit")
    )
    if left_work_unit is None or right_work_unit is None or left_work_unit != right_work_unit:
        return False
    left_fingerprint = work_unit_fingerprint(
        left,
        currentness_basis=mapping(left.get("owner_route_currentness_basis"))
        or mapping(left.get("currentness_basis")),
    )
    right_fingerprint = work_unit_fingerprint(
        right,
        currentness_basis=mapping(right.get("owner_route_currentness_basis"))
        or mapping(right.get("currentness_basis")),
    )
    return left_fingerprint is not None and left_fingerprint == right_fingerprint


def mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


__all__ = [
    "provider_handoff_matches_action",
    "provider_handoff_matches_transition_request_action",
    "same_action_identity",
]
