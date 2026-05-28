from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import request_output_surface_for_action_type
from med_autoscience.controllers import study_domain_transition_guard as domain_transition_guard
from med_autoscience.controllers.story_surface_work_units import (
    is_story_surface_delta_write_work_unit,
)
from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner


def actions(status: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    if domain_transition_guard.blocks_auto_redrive(status):
        return []
    action_type = domain_transition_guard.supported_action_type(status)
    if action_type is None:
        return None
    decision_type = domain_transition_guard.decision_type(status)
    work_unit_id = domain_transition_guard.next_work_unit_id(status)
    transition = domain_transition_guard.transition_from_status(status)
    route_target = _text(transition.get("route_target"))
    controller_next_work_unit = _mapping(transition.get("next_work_unit"))
    controller_work_unit_id = work_unit_id
    unit_harmonized_analysis_route = _is_unit_harmonized_analysis_route(
        decision_type=decision_type,
        route_target=route_target,
        work_unit_id=work_unit_id,
    )
    write_repair_route = _is_write_repair_route(
        decision_type=decision_type,
        route_target=route_target,
        next_work_unit=controller_next_work_unit,
    )
    current_ai_reviewer_materialization_route = _is_current_ai_reviewer_materialization_route(
        decision_type=decision_type,
        route_target=route_target,
        next_work_unit=controller_next_work_unit,
    )
    finalize_gate_replay_route = _is_finalize_gate_replay_route(
        decision_type=decision_type,
        route_target=route_target,
        next_work_unit=controller_next_work_unit,
    )
    if unit_harmonized_analysis_route:
        action_type = "unit_harmonized_external_validation_rerun"
        work_unit_id = "unit_harmonized_external_validation_rerun"
    elif finalize_gate_replay_route:
        action_type = "run_gate_clearing_batch"
    owner = (
        _owner_for_domain_action(action_type)
        if unit_harmonized_analysis_route or finalize_gate_replay_route or decision_type == "publication_gate_blocker"
        else "write"
        if write_repair_route or current_ai_reviewer_materialization_route
        else domain_transition_guard.owner(status) or _owner_for_domain_action(action_type)
    )
    reason = (
        "unit_harmonized_rerun_required"
        if unit_harmonized_analysis_route
        else work_unit_id
        if finalize_gate_replay_route
        else domain_transition_guard.reason(status) or f"domain_transition_{decision_type or 'current'}"
    )
    action: dict[str, Any] = {
        "action_type": action_type,
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": reason,
        "summary": "MAS domain transition oracle selected the current owner work unit.",
        "required_output_surface": _required_output_surface(action_type),
        "next_work_unit": work_unit_id,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    if unit_harmonized_analysis_route:
        action["controller_next_work_unit"] = controller_next_work_unit
        action["controller_work_unit_id"] = controller_work_unit_id
        action["executable_work_unit"] = "unit_harmonized_external_validation_rerun"
    if write_repair_route or current_ai_reviewer_materialization_route:
        action["controller_next_work_unit"] = controller_next_work_unit
        action["controller_work_unit_id"] = controller_work_unit_id
        action["executable_work_unit"] = work_unit_id
        action["route_target"] = "write"
        action["domain_transition_decision_type"] = decision_type
        if decision_type and work_unit_id:
            action["work_unit_fingerprint"] = f"domain-transition::{decision_type}::{work_unit_id}"
        if route_target and route_target != "write":
            action["original_route_target"] = route_target
    if finalize_gate_replay_route:
        action["controller_next_work_unit"] = controller_next_work_unit
        action["controller_work_unit_id"] = controller_work_unit_id
        action["executable_work_unit"] = work_unit_id
        action["controller_action"] = "run_gate_clearing_batch"
        action["domain_transition_decision_type"] = decision_type
        if decision_type and work_unit_id:
            action["work_unit_fingerprint"] = f"domain-transition::{decision_type}::{work_unit_id}"
        if route_target:
            action["original_route_target"] = route_target
    if decision_type == "bundle_stage_finalize":
        action["authority"] = "observability_only"
        action["owner"] = "one-person-lab"
        action["request_owner"] = "one-person-lab"
        action["recommended_owner"] = "one-person-lab"
        action["reason"] = current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
        action["summary"] = (
            "MAS domain transition oracle selected bundle-stage finalization; request OPL stage "
            "attempt admission instead of redriving a MAS-owned runtime repair action."
        )
        action["controller_route_required"] = True
        action["domain_transition_decision_type"] = decision_type
    elif decision_type == "publication_gate_blocker":
        action["summary"] = "MAS domain transition oracle selected the publication gate blocker owner route."
        action["controller_action"] = "run_gate_clearing_batch"
        action["domain_transition_decision_type"] = decision_type
    return [action]


def _owner_for_domain_action(action_type: str) -> str:
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    if action_type == "unit_harmonized_external_validation_rerun":
        return "analysis_harmonization_owner"
    if action_type == "run_gate_clearing_batch":
        return "gate_clearing_batch"
    if action_type == "publication_gate_specificity_required":
        return "publication_gate"
    if action_type == "request_opl_stage_attempt":
        return "one-person-lab"
    return "med-autoscience"


def _required_output_surface(action_type: str) -> str:
    return request_output_surface_for_action_type(action_type)


def _is_unit_harmonized_analysis_route(
    *,
    decision_type: str | None,
    route_target: str | None,
    work_unit_id: str | None,
) -> bool:
    if decision_type != "route_back_same_line":
        return False
    if route_target != "analysis-campaign":
        return False
    return work_unit_id in {
        "unit_harmonized_external_validation_rerun",
        "unit_harmonized_validation_uncertainty_and_grouped_calibration",
    }


def _is_write_repair_route(
    *,
    decision_type: str | None,
    route_target: str | None,
    next_work_unit: Mapping[str, Any],
) -> bool:
    if decision_type != "route_back_same_line":
        return False
    if route_target == "write":
        return True
    if is_story_surface_delta_write_work_unit(next_work_unit.get("unit_id")):
        return True
    return _text(next_work_unit.get("lane")) == "write"


def _is_current_ai_reviewer_materialization_route(
    *,
    decision_type: str | None,
    route_target: str | None,
    next_work_unit: Mapping[str, Any],
) -> bool:
    return (
        decision_type == "route_back_same_line"
        and route_target == "controller"
        and _text(next_work_unit.get("unit_id"))
        == "materialize_current_ai_reviewer_record_through_mas_owner_surface"
    )


def _is_finalize_gate_replay_route(
    *,
    decision_type: str | None,
    route_target: str | None,
    next_work_unit: Mapping[str, Any],
) -> bool:
    return (
        decision_type == "route_back_same_line"
        and route_target == "finalize"
        and _text(next_work_unit.get("unit_id")) == "owner_authorized_publication_gate_replay"
    )


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["actions"]
