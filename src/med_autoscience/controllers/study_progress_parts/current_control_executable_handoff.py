from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .current_action_identity import action_matches_canonical_executable_work_unit
from .shared import _mapping_copy, _non_empty_text

TRANSITION_REQUEST_SOURCE = "opl_current_control_state.transition_request_candidates"


def current_control_executable_owner_action(handoff: Mapping[str, Any]) -> dict[str, Any] | None:
    if handoff.get("running_provider_attempt") is True:
        return None
    current_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    current_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    request_action = _transition_request_executable_owner_action(
        handoff,
        current_work_unit=current_work_unit,
        current_envelope=current_envelope,
    )
    if request_action is not None:
        return request_action
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return None
    if current_envelope and _non_empty_text(current_envelope.get("state_kind")) != "executable_owner_action":
        return None
    action = _mapping_copy(handoff.get("current_executable_owner_action"))
    if _non_empty_text(action.get("surface_kind")) != "current_executable_owner_action":
        return None
    if not action_matches_canonical_executable_work_unit(
        action=action,
        current_work_unit=current_work_unit,
        require_ready_status=True,
    ):
        return None
    if not _envelope_matches_executable_action(
        envelope=current_envelope,
        current_work_unit=current_work_unit,
        action=action,
    ):
        return None
    return action


def current_control_executable_currentness_handoff(
    handoff: Mapping[str, Any],
    *,
    current_control_executable_action: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    action = _mapping_copy(current_control_executable_action) or current_control_executable_owner_action(handoff)
    if not action:
        return dict(handoff)
    current_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    current_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    updated = dict(handoff)
    updated["typed_blocker"] = None
    updated["blocked_reason"] = None
    updated["next_owner"] = _non_empty_text(action.get("next_owner")) or _non_empty_text(
        current_work_unit.get("owner")
    )
    if (
        _non_empty_text(current_work_unit.get("status")) != "executable_owner_action"
        and action.get("transition_request_pending") is True
    ):
        current_work_unit = _current_work_unit_from_transition_request_action(
            action,
            handoff=handoff,
        )
    work_unit_matches_action = (
        _non_empty_text(current_work_unit.get("status")) == "executable_owner_action"
        and action_matches_canonical_executable_work_unit(
            action=action,
            current_work_unit=current_work_unit,
            require_ready_status=True,
        )
    )
    if work_unit_matches_action:
        updated["current_work_unit"] = current_work_unit
    if _non_empty_text(current_envelope.get("state_kind")) == "executable_owner_action" and (
        work_unit_matches_action
        or _envelope_matches_action_identity(envelope=current_envelope, action=action)
    ):
        updated["current_execution_envelope"] = current_envelope
    updated["current_executable_owner_action"] = dict(action)
    return updated


def _transition_request_executable_owner_action(
    handoff: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    current_envelope: Mapping[str, Any],
) -> dict[str, Any] | None:
    candidate = _first_matching_transition_request_candidate(
        handoff,
        current_work_unit=current_work_unit,
        current_envelope=current_envelope,
    )
    if candidate is None:
        return None
    action_type = _non_empty_text(candidate.get("action_type"))
    work_unit_id = _non_empty_text(candidate.get("work_unit_id")) or _non_empty_text(
        candidate.get("next_work_unit")
    )
    work_unit_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    if action_type is None or work_unit_id is None or work_unit_fingerprint is None:
        return None
    next_owner = (
        _non_empty_text(candidate.get("next_executable_owner"))
        or _non_empty_text(candidate.get("next_owner"))
        or _non_empty_text(candidate.get("owner"))
        or _matching_queue_owner(
            handoff,
            action_type=action_type,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
        )
    )
    if next_owner is None:
        return None
    action_fingerprint = _non_empty_text(candidate.get("action_fingerprint")) or work_unit_fingerprint
    source_refs = _mapping_copy(candidate.get("source_refs"))
    route_identity_key = (
        _non_empty_text(candidate.get("route_identity_key"))
        or _non_empty_text(source_refs.get("route_identity_key"))
    )
    attempt_idempotency_key = (
        _non_empty_text(candidate.get("attempt_idempotency_key"))
        or _non_empty_text(source_refs.get("attempt_idempotency_key"))
    )
    idempotency_key = (
        _non_empty_text(candidate.get("idempotency_key"))
        or attempt_idempotency_key
        or route_identity_key
    )
    source = (
        _non_empty_text(candidate.get("mas_owner_action_source"))
        or _non_empty_text(candidate.get("source"))
        or TRANSITION_REQUEST_SOURCE
    )
    action = {
        key: value
        for key, value in {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": source,
            "source_surface": TRANSITION_REQUEST_SOURCE,
            "study_id": _non_empty_text(candidate.get("study_id")) or _non_empty_text(handoff.get("study_id")),
            "quest_id": _non_empty_text(candidate.get("quest_id")),
            "next_owner": next_owner,
            "owner": next_owner,
            "action_type": action_type,
            "allowed_actions": [action_type],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": action_fingerprint,
            "route_identity_key": route_identity_key,
            "attempt_idempotency_key": attempt_idempotency_key,
            "idempotency_key": idempotency_key,
            "required_output_surface": _non_empty_text(candidate.get("required_output_surface")),
            "required_delta_kind": _non_empty_text(candidate.get("required_delta_kind"))
            or _transition_request_required_delta_kind(source),
            "provider_admission_pending": False,
            "transition_request_pending": True,
            "provider_attempt_or_lease_required": False,
            "provider_admission_requires_opl_runtime_result": candidate.get(
                "provider_admission_requires_opl_runtime_result"
            )
            is not False,
            "opl_transition_runtime_required": candidate.get("opl_transition_runtime_required") is not False,
            "currentness_basis": {
                key: value
                for key, value in {
                    **_mapping_copy(candidate.get("currentness_basis")),
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "route_identity_key": route_identity_key,
                    "attempt_idempotency_key": attempt_idempotency_key,
                }.items()
                if value not in (None, "", [], {})
            },
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
    if not _envelope_matches_executable_action(
        envelope=current_envelope,
        current_work_unit=current_work_unit,
        action=action,
    ):
        return None
    return action


def _first_matching_transition_request_candidate(
    handoff: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    current_envelope: Mapping[str, Any],
) -> dict[str, Any] | None:
    for item in handoff.get("transition_request_candidates") or []:
        if not isinstance(item, Mapping):
            continue
        candidate = dict(item)
        if _non_empty_text(candidate.get("status")) != "transition_request_pending":
            continue
        if not _transition_candidate_has_identity(candidate):
            continue
        if not _candidate_matches_current_identity(
            candidate,
            current_work_unit=current_work_unit,
            current_envelope=current_envelope,
        ):
            continue
        return candidate
    return None


def _transition_candidate_has_identity(candidate: Mapping[str, Any]) -> bool:
    return (
        _non_empty_text(candidate.get("action_type")) is not None
        and (
            _non_empty_text(candidate.get("work_unit_id"))
            or _non_empty_text(candidate.get("next_work_unit"))
        )
        is not None
        and (
            _non_empty_text(candidate.get("work_unit_fingerprint"))
            or _non_empty_text(candidate.get("action_fingerprint"))
        )
        is not None
    )


def _candidate_matches_current_identity(
    candidate: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    current_envelope: Mapping[str, Any],
) -> bool:
    candidate_action = _non_empty_text(candidate.get("action_type"))
    candidate_work_unit = _non_empty_text(candidate.get("work_unit_id")) or _non_empty_text(
        candidate.get("next_work_unit")
    )
    candidate_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    candidate_owner = (
        _non_empty_text(candidate.get("next_executable_owner"))
        or _non_empty_text(candidate.get("next_owner"))
        or _non_empty_text(candidate.get("owner"))
    )
    for surface in (current_work_unit, current_envelope):
        if not surface:
            continue
        surface_owner = _non_empty_text(surface.get("owner"))
        if surface_owner is not None and candidate_owner is not None and surface_owner != candidate_owner:
            return False
        surface_work_unit = _non_empty_text(surface.get("work_unit_id")) or _non_empty_text(
            surface.get("next_work_unit")
        )
        if surface_work_unit is not None and candidate_work_unit is not None and surface_work_unit != candidate_work_unit:
            return False
        surface_action = _non_empty_text(surface.get("action_type"))
        if surface_action is not None and candidate_action is not None and surface_action != candidate_action:
            return False
        surface_fingerprint = _non_empty_text(surface.get("work_unit_fingerprint")) or _non_empty_text(
            surface.get("action_fingerprint")
        )
        if (
            surface_fingerprint is not None
            and candidate_fingerprint is not None
            and surface_fingerprint != candidate_fingerprint
        ):
            return False
    return True


def _matching_queue_owner(
    handoff: Mapping[str, Any],
    *,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> str | None:
    for item in handoff.get("action_queue") or []:
        if not isinstance(item, Mapping):
            continue
        queue_action = _non_empty_text(item.get("action_type"))
        queue_work_unit = _non_empty_text(item.get("work_unit_id")) or _non_empty_text(item.get("next_work_unit"))
        queue_fingerprint = _non_empty_text(item.get("work_unit_fingerprint")) or _non_empty_text(
            item.get("action_fingerprint")
        )
        if (
            queue_action == action_type
            and queue_work_unit == work_unit_id
            and queue_fingerprint == work_unit_fingerprint
        ):
            return _non_empty_text(item.get("owner")) or _non_empty_text(item.get("next_owner"))
    return None


def _transition_request_required_delta_kind(source: str) -> str | None:
    if source == "paper_recovery_state.next_safe_action.successor_owner_action":
        return "paper_recovery_successor_owner_delta_or_typed_blocker"
    return None


def _current_work_unit_from_transition_request_action(
    action: Mapping[str, Any],
    *,
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    owner = _non_empty_text(action.get("next_owner")) or _non_empty_text(action.get("owner"))
    action_type = _non_empty_text(action.get("action_type"))
    work_unit_id = _non_empty_text(action.get("work_unit_id"))
    work_unit_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    action_fingerprint = _non_empty_text(action.get("action_fingerprint")) or work_unit_fingerprint
    currentness_basis = {
        key: value
        for key, value in {
            **_mapping_copy(action.get("currentness_basis")),
            "source": _non_empty_text(action.get("source_surface")) or TRANSITION_REQUEST_SOURCE,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": action_fingerprint,
            "route_identity_key": _non_empty_text(action.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(action.get("attempt_idempotency_key")),
        }.items()
        if value not in (None, "", [], {})
    }
    return {
        key: value
        for key, value in {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "executable_owner_action",
            "study_id": _non_empty_text(action.get("study_id")) or _non_empty_text(handoff.get("study_id")),
            "quest_id": _non_empty_text(action.get("quest_id")) or _non_empty_text(handoff.get("quest_id")),
            "owner": owner,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": action_fingerprint,
            "currentness_basis": currentness_basis,
            "state": {
                "state_kind": "executable_owner_action",
                "source": _non_empty_text(action.get("source")),
                "provider_admission_pending": False,
                "transition_request_pending": True,
                "provider_admission_requires_opl_runtime_result": action.get(
                    "provider_admission_requires_opl_runtime_result"
                )
                is True,
                "opl_transition_runtime_required": action.get("opl_transition_runtime_required") is True,
            },
            "authority_boundary": {
                "projection_only": True,
                "runtime_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "can_authorize_provider_admission": False,
                "can_start_provider_attempt": False,
                "provider_completion_is_domain_completion": False,
            },
        }.items()
        if value not in (None, "", [], {})
    }


def _envelope_matches_executable_action(
    *,
    envelope: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if not envelope:
        return True
    envelope_owner = _non_empty_text(envelope.get("owner"))
    canonical_owner = _non_empty_text(current_work_unit.get("owner")) or _non_empty_text(
        action.get("next_owner")
    )
    if envelope_owner is not None and canonical_owner is not None and envelope_owner != canonical_owner:
        return False
    envelope_work_unit = _non_empty_text(envelope.get("next_work_unit")) or _non_empty_text(
        envelope.get("work_unit_id")
    )
    canonical_work_unit = _non_empty_text(current_work_unit.get("work_unit_id")) or _non_empty_text(
        action.get("work_unit_id")
    )
    if (
        envelope_work_unit is not None
        and canonical_work_unit is not None
        and envelope_work_unit != canonical_work_unit
    ):
        return False
    envelope_action = _non_empty_text(envelope.get("action_type"))
    canonical_action = _non_empty_text(current_work_unit.get("action_type")) or _non_empty_text(
        action.get("action_type")
    )
    if envelope_action is not None and canonical_action is not None and envelope_action != canonical_action:
        return False
    envelope_fingerprint = _non_empty_text(envelope.get("work_unit_fingerprint")) or _non_empty_text(
        envelope.get("action_fingerprint")
    )
    canonical_fingerprint = _non_empty_text(current_work_unit.get("work_unit_fingerprint")) or _non_empty_text(
        current_work_unit.get("action_fingerprint")
    ) or _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(action.get("action_fingerprint"))
    if (
        envelope_fingerprint is not None
        and canonical_fingerprint is not None
        and envelope_fingerprint != canonical_fingerprint
    ):
        return False
    return True


def _envelope_matches_action_identity(
    *,
    envelope: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    action_owner = _non_empty_text(action.get("next_owner"))
    envelope_owner = _non_empty_text(envelope.get("owner"))
    if action_owner is None or envelope_owner != action_owner:
        return False
    action_work_unit = _non_empty_text(action.get("work_unit_id"))
    envelope_work_unit = _non_empty_text(envelope.get("next_work_unit")) or _non_empty_text(
        envelope.get("work_unit_id")
    )
    if action_work_unit is None or envelope_work_unit != action_work_unit:
        return False
    action_type = _non_empty_text(action.get("action_type"))
    envelope_action = _non_empty_text(envelope.get("action_type"))
    if envelope_action is not None and action_type is not None and envelope_action != action_type:
        return False
    action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    envelope_fingerprint = _non_empty_text(envelope.get("work_unit_fingerprint")) or _non_empty_text(
        envelope.get("action_fingerprint")
    )
    if envelope_fingerprint is not None and action_fingerprint is not None:
        return envelope_fingerprint == action_fingerprint
    return True
