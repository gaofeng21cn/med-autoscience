from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import owner_route_attempt_protocol
from med_autoscience.runtime_control import repeat_suppression

from . import output_readiness


def owner_handoff_allowed(
    *,
    action_type: str,
    dispatch: Mapping[str, Any],
    current_study: Mapping[str, Any] | None,
) -> bool:
    if action_type == "publication_gate_specificity_required":
        current_owner_route = _mapping(_mapping(current_study).get("owner_route"))
        owner_route = current_owner_route or _dispatch_owner_route(dispatch)
        return repeat_suppression.publication_gate_specificity_route(owner_route) and owner_route_part.route_allows_action(
            action=dispatch,
            owner_route=owner_route,
        )
    if action_type == "unit_harmonized_external_validation_rerun":
        current_owner_route = _mapping(_mapping(current_study).get("owner_route"))
        owner_route = current_owner_route or _dispatch_owner_route(dispatch)
        return repeat_suppression.hard_methodology_harmonization_route(
            owner_route
        ) and owner_route_part.route_allows_action(action=dispatch, owner_route=owner_route)
    if action_type == "recover_transport_model_provenance":
        current_owner_route = _mapping(_mapping(current_study).get("owner_route"))
        owner_route = current_owner_route or _dispatch_owner_route(dispatch)
        return repeat_suppression.source_provenance_recovery_route(owner_route) and owner_route_part.route_allows_action(
            action=dispatch,
            owner_route=owner_route,
        )
    if action_type == "methodology_reframe_route_decision":
        current_owner_route = _mapping(_mapping(current_study).get("owner_route"))
        owner_route = current_owner_route or _dispatch_owner_route(dispatch)
        return (
            _text(owner_route.get("next_owner")) == "decision"
            and _text(owner_route.get("owner_reason")) == "methodology_reframe_required"
            and owner_route_part.route_allows_action(action=dispatch, owner_route=owner_route)
        )
    if action_type == "provenance_limited_harmonization_audit":
        current_owner_route = _mapping(_mapping(current_study).get("owner_route"))
        owner_route = current_owner_route or _dispatch_owner_route(dispatch)
        return repeat_suppression.provenance_limited_harmonization_route(
            owner_route
        ) and owner_route_part.route_allows_action(action=dispatch, owner_route=owner_route)
    if action_type == "run_quality_repair_batch":
        current_owner_route = _mapping(_mapping(current_study).get("owner_route"))
        owner_route = current_owner_route or _dispatch_owner_route(dispatch)
        if _text(owner_route.get("next_owner")) != "write":
            return False
        if not owner_route_part.route_allows_action(action=dispatch, owner_route=owner_route):
            return False
        if _text(owner_route.get("failure_signature")) == "manuscript_story_surface_delta_missing":
            return True
        if _registered_write_route_back_handoff(
            action_type=action_type,
            owner_route=owner_route,
        ):
            return True
        next_work_unit_id = _work_unit_id(
            _mapping(dispatch.get("source_action")).get("next_work_unit")
            or dispatch.get("next_work_unit")
            or _mapping(dispatch.get("prompt_contract")).get("next_work_unit")
            or _mapping(_mapping(current_study).get("domain_transition")).get("next_work_unit")
        )
        return (
            _text(owner_route.get("failure_signature")) == "quest_waiting_opl_runtime_owner_route"
            and next_work_unit_id == "medical_prose_write_repair"
        )
    if action_type != "return_to_ai_reviewer_workflow":
        return False
    if output_readiness.ai_reviewer_output_pending(current_study):
        return True
    owner_route = _dispatch_owner_route(dispatch)
    if _text(owner_route.get("failure_signature")) not in repeat_suppression.OWNER_HANDOFF_REASONS:
        return False
    next_owner = _text(owner_route.get("next_owner"))
    next_executable_owner = _text(dispatch.get("next_executable_owner")) or _text(
        _mapping(dispatch.get("prompt_contract")).get("next_executable_owner")
    )
    if next_owner not in {"ai_reviewer", "write/ai_reviewer"}:
        return False
    return next_executable_owner in {"ai_reviewer", "write/ai_reviewer"}


def _dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _registered_write_route_back_handoff(
    *,
    action_type: str,
    owner_route: Mapping[str, Any],
) -> bool:
    reason_contract = owner_route_attempt_protocol.owner_reason_contract(
        reason=_text(owner_route.get("owner_reason")) or _text(owner_route.get("failure_signature")),
        owner=_text(owner_route.get("next_owner")),
        action_type=action_type,
    )
    if reason_contract.get("registered") is not True:
        return False
    if _text(reason_contract.get("owner")) != "write":
        return False
    if _text(reason_contract.get("priority_class")) != "write_route_back":
        return False
    if action_type not in {_text(action) for action in reason_contract.get("allowed_actions") or []}:
        return False

    protocol = _mapping(owner_route.get("owner_route_attempt_protocol"))
    if not protocol:
        protocol = _mapping(
            owner_route_attempt_protocol.decorate_owner_route(owner_route).get("owner_route_attempt_protocol")
        )
    if protocol.get("dispatchable") is not True:
        return False
    if _text(protocol.get("priority_class")) != "write_route_back":
        return False

    currentness_contract = _mapping(owner_route.get("currentness_contract"))
    if not currentness_contract:
        currentness_contract = owner_route_attempt_protocol.currentness_contract(owner_route)
    if currentness_contract.get("missing_required_fields"):
        return False
    if _text(owner_route.get("source_fingerprint")) is None:
        return False
    currentness_basis = _owner_route_currentness_basis(owner_route)
    return _text(currentness_basis.get("work_unit_id")) is not None


def _owner_route_currentness_basis(owner_route: Mapping[str, Any]) -> dict[str, Any]:
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    if basis:
        return basis
    return owner_route_attempt_protocol.currentness_basis(owner_route)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["owner_handoff_allowed"]
