from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    has_provider_admission_opl_transition_readback,
    provider_admission_opl_transition_readback,
)

from .shared import _mapping_copy, _non_empty_text


SOURCE = "opl_current_control_state.provider_admission_candidates"
LIVE_READBACK_SOURCE = "opl_domain_progress_transition_runtime_live_readback"


def active_provider_control(handoff: Mapping[str, Any]) -> bool:
    active_candidates = _unconsumed_provider_admission_candidates(handoff)
    if handoff.get("running_provider_attempt") is True:
        return bool(provider_admission_opl_transition_readback(handoff))
    if handoff.get("provider_admission_pending_count") not in (None, 0):
        return has_provider_admission_opl_transition_readback(handoff) or any(
            has_provider_admission_opl_transition_readback(item)
            for item in active_candidates
        )
    if any(
        has_provider_admission_opl_transition_readback(item)
        for item in active_candidates
    ):
        return True
    return False


def current_control_provider_admission_action(handoff: Mapping[str, Any]) -> dict[str, Any] | None:
    candidate = first_handoff_provider_admission_candidate(handoff)
    if candidate is None:
        return None
    action_type = _non_empty_text(candidate.get("action_type"))
    work_unit_id = _non_empty_text(candidate.get("work_unit_id")) or _non_empty_text(candidate.get("next_work_unit"))
    work_unit_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    if action_type is None or work_unit_id is None or work_unit_fingerprint is None:
        return None
    next_owner = (
        _non_empty_text(candidate.get("next_executable_owner"))
        or _non_empty_text(candidate.get("next_owner"))
        or _non_empty_text(candidate.get("owner"))
    )
    return {
        key: value
        for key, value in {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": SOURCE,
            "source_surface": SOURCE,
            "study_id": _non_empty_text(candidate.get("study_id")) or _non_empty_text(handoff.get("study_id")),
            "quest_id": _non_empty_text(candidate.get("quest_id")),
            "next_owner": next_owner,
            "owner": next_owner,
            "action_type": action_type,
            "allowed_actions": [action_type],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": _non_empty_text(candidate.get("action_fingerprint")) or work_unit_fingerprint,
            "route_identity_key": _non_empty_text(candidate.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(candidate.get("attempt_idempotency_key")),
            "idempotency_key": _non_empty_text(candidate.get("idempotency_key"))
            or _non_empty_text(candidate.get("attempt_idempotency_key"))
            or _non_empty_text(candidate.get("route_identity_key")),
            "provider_admission_pending": True,
            "transition_request_pending": False,
            "provider_attempt_or_lease_required": True,
            "provider_admission_requires_opl_runtime_result": False,
            "opl_transition_runtime_required": False,
            "opl_transition_readback_source": LIVE_READBACK_SOURCE,
            "authority_boundary": {
                "projection_only": True,
                "runtime_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "can_authorize_provider_admission": False,
                "can_start_provider_attempt": False,
                "provider_completion_is_domain_completion": False,
                "paper_progress_delta": False,
            },
        }.items()
        if value not in (None, "", [], {})
    }


def with_provider_admission_executable_currentness(
    handoff: Mapping[str, Any],
    *,
    current_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    action = _mapping_copy(current_action)
    if _non_empty_text(action.get("source")) != SOURCE:
        return dict(handoff)
    work_unit_id = _non_empty_text(action.get("work_unit_id")) or _non_empty_text(action.get("next_work_unit"))
    action_type = _non_empty_text(action.get("action_type"))
    work_unit_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    if action_type is None or work_unit_id is None or work_unit_fingerprint is None:
        return dict(handoff)
    owner = _non_empty_text(action.get("next_owner")) or _non_empty_text(action.get("owner"))
    currentness_basis = {
        key: value
        for key, value in {
            **_mapping_copy(action.get("owner_route_currentness_basis")),
            **_mapping_copy(action.get("currentness_basis")),
            "source": SOURCE,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "route_identity_key": _non_empty_text(action.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(action.get("attempt_idempotency_key")),
        }.items()
        if value not in (None, "", [], {})
    }
    updated = dict(handoff)
    updated["typed_blocker"] = None
    updated["blocked_reason"] = None
    updated["next_owner"] = owner
    updated["current_work_unit"] = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "executable_owner_action",
        "study_id": _non_empty_text(action.get("study_id")) or _non_empty_text(handoff.get("study_id")),
        "quest_id": _non_empty_text(action.get("quest_id")),
        "owner": owner,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": _non_empty_text(action.get("action_fingerprint")) or work_unit_fingerprint,
        "currentness_basis": currentness_basis,
        "state": {
            "state_kind": "executable_owner_action",
            "source": SOURCE,
            "provider_admission_pending": True,
            "transition_request_pending": False,
            "provider_attempt_or_lease_required": True,
            "provider_admission_requires_opl_runtime_result": False,
            "opl_transition_runtime_required": False,
        },
        "authority_boundary": {
            "projection_only": True,
            "runtime_owner": "one-person-lab",
            "domain_truth_owner": "med-autoscience",
            "can_authorize_provider_admission": False,
            "can_start_provider_attempt": False,
            "provider_completion_is_domain_completion": False,
        },
    }
    updated["current_execution_envelope"] = {
        "state_kind": "executable_owner_action",
        "owner": owner,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": _non_empty_text(action.get("action_fingerprint")) or work_unit_fingerprint,
        "source": SOURCE,
        "authority_boundary": {
            "projection_only": True,
            "runtime_owner": "one-person-lab",
            "domain_truth_owner": "med-autoscience",
            "can_authorize_provider_admission": False,
            "can_start_provider_attempt": False,
        },
    }
    updated["current_executable_owner_action"] = dict(action)
    return updated


def first_handoff_provider_admission_candidate(handoff: Mapping[str, Any]) -> dict[str, Any] | None:
    for item in _unconsumed_provider_admission_candidates(handoff):
        if provider_admission_opl_transition_readback(item):
            return dict(item)
    return None


def _unconsumed_provider_admission_candidates(handoff: Mapping[str, Any]) -> list[dict[str, Any]]:
    consumed = _mapping_copy(handoff.get("provider_admission_terminal_closeout_consumed"))
    candidates: list[dict[str, Any]] = []
    for item in handoff.get("provider_admission_candidates") or []:
        if not isinstance(item, Mapping):
            continue
        candidate = dict(item)
        if consumed and _same_terminal_consumption_identity(
            _identity_for_terminal_consumption(consumed),
            _identity_for_terminal_consumption(candidate),
        ):
            continue
        candidates.append(candidate)
    return candidates


def _identity_for_terminal_consumption(value: Mapping[str, Any]) -> dict[str, str]:
    payload = _mapping_copy(value)
    work_unit_fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
        payload.get("action_fingerprint")
    )
    return {
        key: result
        for key, result in {
            "action_type": _non_empty_text(payload.get("action_type")),
            "work_unit_id": _non_empty_text(payload.get("work_unit_id"))
            or _non_empty_text(payload.get("next_work_unit")),
            "work_unit_fingerprint": work_unit_fingerprint,
            "route_identity_key": _non_empty_text(payload.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(payload.get("attempt_idempotency_key")),
        }.items()
        if result is not None
    }


def _same_terminal_consumption_identity(
    consumed: Mapping[str, str],
    candidate: Mapping[str, str],
) -> bool:
    for key in ("action_type", "work_unit_id", "work_unit_fingerprint"):
        if not consumed.get(key) or consumed.get(key) != candidate.get(key):
            return False
    for key in ("route_identity_key", "attempt_idempotency_key"):
        consumed_value = consumed.get(key)
        candidate_value = candidate.get(key)
        if consumed_value is not None and candidate_value is not None and consumed_value != candidate_value:
            return False
    return True
