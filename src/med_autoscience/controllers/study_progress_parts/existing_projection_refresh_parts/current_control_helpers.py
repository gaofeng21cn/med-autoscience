from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_transition_readback import (
    provider_admission_opl_transition_readback,
)

from ..current_control_executable_handoff import current_control_executable_owner_action
from ..shared import _mapping_copy, _non_empty_text


def _apply_current_control_currentness_to_existing_projection(
    payload: dict[str, Any],
    *,
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    if handoff.get("running_provider_attempt") is True:
        return payload
    handoff_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    handoff_executable_action = current_control_executable_owner_action(handoff)
    if _non_empty_text(handoff_work_unit.get("status")) not in {"typed_blocker", "blocked_current_work_unit"}:
        if (
            _non_empty_text(handoff_envelope.get("state_kind")) != "typed_blocker"
            and not handoff_executable_action
        ):
            return payload
    updated = dict(payload)
    if handoff_work_unit:
        updated["current_work_unit"] = handoff_work_unit
    if handoff_envelope:
        updated["current_execution_envelope"] = handoff_envelope
    if _mapping_copy(handoff.get("typed_blocker")):
        updated["current_executable_owner_action"] = None
    elif handoff_executable_action:
        updated["current_executable_owner_action"] = handoff_executable_action
    elif "current_executable_owner_action" in handoff:
        updated["current_executable_owner_action"] = _mapping_copy(
            handoff.get("current_executable_owner_action")
        ) or None
    _sync_handoff_counts(updated, handoff=handoff)
    return updated


def _provider_admission_action_supersedes_request_action(
    provider_action: Mapping[str, Any],
    *,
    request_action: Mapping[str, Any] | None,
) -> bool:
    if provider_action.get("provider_admission_pending") is not True:
        return False
    request = _mapping_copy(request_action)
    if not request:
        return True
    if not _same_current_action_identity(provider_action, request):
        return False
    for key in ("route_identity_key", "attempt_idempotency_key"):
        provider_value = _non_empty_text(provider_action.get(key))
        request_value = _non_empty_text(request.get(key))
        if provider_value is not None and request_value is not None and provider_value != request_value:
            return False
    return True


def _sync_handoff_provider_admission_fields(
    payload: dict[str, Any],
    *,
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(payload)
    _sync_handoff_counts(updated, handoff=handoff)
    return updated


def _handoff_has_bound_running_provider_attempt(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is not True:
        return False
    if not provider_admission_opl_transition_readback(handoff):
        return False
    if _non_empty_text(handoff.get("active_stage_attempt_id")) is None and _non_empty_text(
        handoff.get("active_run_id")
    ) is None and _non_empty_text(handoff.get("active_workflow_id")) is None:
        return False
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    runtime_liveness_status = _non_empty_text(runtime_health.get("runtime_liveness_status"))
    health_status = _non_empty_text(runtime_health.get("health_status"))
    if runtime_liveness_status not in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    } and health_status not in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    }:
        return False
    return any(
        _non_empty_text(value) is not None
        for value in (
            handoff.get("action_type"),
            handoff.get("work_unit_id"),
            handoff.get("work_unit_fingerprint"),
            handoff.get("action_fingerprint"),
            runtime_health.get("action_type"),
            runtime_health.get("work_unit_id"),
            runtime_health.get("work_unit_fingerprint"),
            runtime_health.get("action_fingerprint"),
        )
    )


def _running_handoff_conflicts_current_surface(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    if not _handoff_has_bound_running_provider_attempt(handoff):
        return False
    handoff_identity = _identity_values(handoff)
    for surface in (
        _mapping_copy(payload.get("current_work_unit")),
        _mapping_copy(payload.get("current_execution_envelope")),
        _mapping_copy(payload.get("current_executable_owner_action")),
    ):
        if not surface:
            continue
        if _non_empty_text(surface.get("status")) not in {
            "executable_owner_action",
            "running_provider_attempt",
            "typed_blocker",
            "blocked_current_work_unit",
        } and _non_empty_text(surface.get("state_kind")) not in {
            "executable_owner_action",
            "running_provider_attempt",
            "typed_blocker",
            "blocked_current_work_unit",
        } and _non_empty_text(surface.get("surface_kind")) != "current_executable_owner_action":
            continue
        surface_identity = _identity_values(surface)
        if _identities_conflict(handoff_identity, surface_identity):
            return True
    return False


def _current_control_handoff_is_typed_blocker(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is True:
        return False
    handoff_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    if _non_empty_text(handoff_work_unit.get("status")) in {"typed_blocker", "blocked_current_work_unit"}:
        return True
    handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    return _non_empty_text(handoff_envelope.get("state_kind")) == "typed_blocker"


def _current_control_typed_blocker_for_successor_check(handoff: Mapping[str, Any]) -> dict[str, Any]:
    typed_blocker = _mapping_copy(handoff.get("typed_blocker"))
    if typed_blocker:
        return typed_blocker
    current = _mapping_copy(handoff.get("current_work_unit"))
    state = _mapping_copy(current.get("state"))
    current_blocker = _mapping_copy(state.get("typed_blocker"))
    if current_blocker:
        return current_blocker
    envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    envelope_blocker = _mapping_copy(envelope.get("typed_blocker"))
    if envelope_blocker:
        return envelope_blocker
    return {}


def _sync_handoff_counts(updated: dict[str, Any], *, handoff: Mapping[str, Any]) -> None:
    if "provider_admission_pending_count" in handoff:
        updated["provider_admission_pending_count"] = int(
            handoff.get("provider_admission_pending_count") or 0
        )
    if "provider_admission_candidates" in handoff:
        updated["provider_admission_candidates"] = [
            dict(item)
            for item in handoff.get("provider_admission_candidates") or []
            if isinstance(item, Mapping)
        ]
    if "transition_request_pending_count" in handoff:
        updated["transition_request_pending_count"] = int(
            handoff.get("transition_request_pending_count") or 0
        )
    if "transition_request_candidates" in handoff:
        updated["transition_request_candidates"] = [
            dict(item)
            for item in handoff.get("transition_request_candidates") or []
            if isinstance(item, Mapping)
        ]
    consumed = _mapping_copy(handoff.get("provider_admission_terminal_closeout_consumed"))
    if consumed:
        updated["provider_admission_terminal_closeout_consumed"] = consumed
        updated["provider_admission_pending_count"] = 0
        updated["provider_admission_candidates"] = []
        updated["transition_request_pending_count"] = 0
        updated["transition_request_candidates"] = []


def _same_current_action_identity(
    left: Mapping[str, Any] | None,
    right: Mapping[str, Any] | None,
) -> bool:
    left_action = _mapping_copy(left)
    right_action = _mapping_copy(right)
    if not left_action or not right_action:
        return False
    left_owner = _non_empty_text(left_action.get("next_owner")) or _non_empty_text(left_action.get("owner"))
    right_owner = _non_empty_text(right_action.get("next_owner")) or _non_empty_text(right_action.get("owner"))
    if left_owner is not None and right_owner is not None and left_owner != right_owner:
        return False
    for key in ("action_type", "work_unit_id"):
        left_value = _non_empty_text(left_action.get(key))
        right_value = _non_empty_text(right_action.get(key))
        if left_value is not None and right_value is not None and left_value != right_value:
            return False
    left_fingerprint = _non_empty_text(left_action.get("work_unit_fingerprint")) or _non_empty_text(
        left_action.get("action_fingerprint")
    )
    right_fingerprint = _non_empty_text(right_action.get("work_unit_fingerprint")) or _non_empty_text(
        right_action.get("action_fingerprint")
    )
    if left_fingerprint is not None and right_fingerprint is not None and left_fingerprint != right_fingerprint:
        return False
    return True


def _identity_values(value: Mapping[str, Any]) -> dict[str, str | None]:
    basis = _mapping_copy(value.get("owner_route_currentness_basis")) or _mapping_copy(
        value.get("currentness_basis")
    )
    state = _mapping_copy(value.get("state"))
    runtime_health = _mapping_copy(value.get("runtime_health"))
    return {
        "action_type": _non_empty_text(value.get("action_type"))
        or _non_empty_text(runtime_health.get("action_type")),
        "work_unit_id": _non_empty_text(value.get("work_unit_id"))
        or _non_empty_text(value.get("next_work_unit"))
        or _non_empty_text(runtime_health.get("work_unit_id"))
        or _non_empty_text(runtime_health.get("next_work_unit"))
        or _non_empty_text(state.get("next_work_unit"))
        or _non_empty_text(basis.get("work_unit_id")),
        "fingerprint": _non_empty_text(value.get("work_unit_fingerprint"))
        or _non_empty_text(value.get("action_fingerprint"))
        or _non_empty_text(runtime_health.get("work_unit_fingerprint"))
        or _non_empty_text(runtime_health.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint")),
    }


def _identities_conflict(left: Mapping[str, str | None], right: Mapping[str, str | None]) -> bool:
    return any(
        left.get(key) is not None and right.get(key) is not None and left.get(key) != right.get(key)
        for key in ("action_type", "work_unit_id", "fingerprint")
    )
