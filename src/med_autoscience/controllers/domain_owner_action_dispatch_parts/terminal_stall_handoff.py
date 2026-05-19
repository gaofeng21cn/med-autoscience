from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part
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
    if action_type == "runtime_platform_repair":
        current_owner_route = _mapping(_mapping(current_study).get("owner_route"))
        owner_route = current_owner_route or _dispatch_owner_route(dispatch)
        return owner_route_part.route_allows_action(action=dispatch, owner_route=owner_route)
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


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["owner_handoff_allowed"]
