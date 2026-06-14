from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)


def owner_action_from_domain_transition(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    transition = _mapping_copy(payload.get("domain_transition"))
    next_work_unit = _mapping_copy(transition.get("next_work_unit"))
    owner = _non_empty_text(transition.get("owner")) or _non_empty_text(transition.get("route_target"))
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    action = _non_empty_text(transition.get("controller_action"))
    if owner is None and work_unit_id is None and action is None:
        return None
    decision_type = _non_empty_text(transition.get("decision_type"))
    work_unit_fingerprint = _non_empty_text(transition.get("work_unit_fingerprint"))
    if work_unit_fingerprint is None and decision_type is not None and work_unit_id is not None:
        work_unit_fingerprint = f"domain-transition::{decision_type}::{work_unit_id}"
    target_surface = _target_surface(transition=transition, route_target=owner)
    return _compact(
        {
            "surface_kind": surface_kind,
            "schema_version": 1,
            "status": "ready",
            "source": "domain_transition",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "source_eval_id": _source_eval_id(transition),
            "action_type": action,
            "allowed_actions": [action] if action is not None else [],
            "owner_receipt_required": True,
            "required_delta_kind": "domain_transition_owner_delta_or_typed_blocker",
            "target_surface": target_surface,
            "target_surface_specificity": "domain_transition_required_owner_surface"
            if target_surface
            else None,
            "domain_transition_decision_type": decision_type,
            "authority_boundary": _authority_boundary(),
        }
    )


def consumed_closeout_typed_blocker_allows_domain_transition_successor(
    *,
    payload: Mapping[str, Any],
    domain_transition_action: Mapping[str, Any],
    repair_progress_action: Mapping[str, Any] | None,
) -> bool:
    if _non_empty_text(domain_transition_action.get("action_type")) is None:
        return False
    transition = _mapping_copy(payload.get("domain_transition"))
    completion = _mapping_copy(transition.get("completion_receipt_consumption"))
    if _non_empty_text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if not _mapping_copy(transition.get("next_work_unit")):
        return False
    if not _current_work_unit_is_consumed_closeout_typed_blocker(payload):
        return False
    if repair_progress_action is None:
        return True
    source_work_unit = _non_empty_text(
        _mapping_copy(repair_progress_action.get("repair_progress_precedence")).get("source_work_unit_id")
    )
    if source_work_unit is None:
        source_work_unit = _non_empty_text(_mapping_copy(payload.get("repair_progress_projection")).get("work_unit_id"))
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if source_work_unit is None:
        return True
    return source_work_unit == _non_empty_text(current_work_unit.get("work_unit_id"))


def _current_work_unit_is_consumed_closeout_typed_blocker(payload: Mapping[str, Any]) -> bool:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    envelope = _mapping_copy(payload.get("current_execution_envelope"))
    if _non_empty_text(current_work_unit.get("status")) not in {"typed_blocker", "blocked_current_work_unit"} and (
        _non_empty_text(envelope.get("state_kind")) != "typed_blocker"
    ):
        return False
    state = _mapping_copy(current_work_unit.get("state"))
    if (
        _non_empty_text(state.get("source")) != "accepted_closeout_consumed_pending"
        and _non_empty_text(envelope.get("source")) != "accepted_closeout_consumed_pending"
    ):
        return False
    typed_blocker = (
        _mapping_copy(state.get("typed_blocker"))
        or _mapping_copy(current_work_unit.get("typed_blocker"))
        or _mapping_copy(envelope.get("typed_blocker"))
    )
    return _non_empty_text(typed_blocker.get("blocker_type")) == "provider_completion_is_not_domain_ready" or (
        _non_empty_text(typed_blocker.get("reason")) == "provider_completion_is_not_domain_ready"
    )


def _target_surface(
    *,
    transition: Mapping[str, Any],
    route_target: str | None,
) -> dict[str, Any] | None:
    guard_boundary = _mapping_copy(transition.get("guard_boundary"))
    surface_ref = _non_empty_text(guard_boundary.get("required_owner_surface"))
    if surface_ref is None:
        surface_ref = _non_empty_text(_mapping_copy(transition.get("target_surface")).get("surface_ref"))
    if surface_ref is None:
        return None
    return _compact(
        {
            "ref_kind": "route_obligation",
            "route_target": _non_empty_text(transition.get("route_target")) or route_target,
            "surface_ref": surface_ref,
        }
    )


def _source_eval_id(transition: Mapping[str, Any]) -> str | None:
    completion = _mapping_copy(transition.get("completion_receipt_consumption"))
    publication_eval_ref = _mapping_copy(transition.get("publication_eval_ref"))
    return (
        _non_empty_text(completion.get("eval_id"))
        or _non_empty_text(transition.get("source_eval_id"))
        or _non_empty_text(transition.get("publication_eval_id"))
        or _non_empty_text(publication_eval_ref.get("eval_id"))
    )


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = [
    "consumed_closeout_typed_blocker_allows_domain_transition_successor",
    "owner_action_from_domain_transition",
]
