from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import study_domain_transition_guard as domain_transition_guard
from med_autoscience.controllers.domain_route_scan_parts import current_truth_owner


def actions(status: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    if domain_transition_guard.blocks_auto_redrive(status):
        return []
    action_type = domain_transition_guard.supported_action_type(status)
    if action_type is None:
        return None
    decision_type = domain_transition_guard.decision_type(status)
    work_unit_id = domain_transition_guard.next_work_unit_id(status)
    owner = domain_transition_guard.owner(status) or _owner_for_domain_action(action_type)
    reason = domain_transition_guard.reason(status) or f"domain_transition_{decision_type or 'current'}"
    action: dict[str, Any] = {
        "action_type": action_type,
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": reason,
        "summary": "MAS domain transition oracle selected the current owner work unit.",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "next_work_unit": work_unit_id,
        "paper_package_mutation_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    if decision_type == "bundle_stage_finalize":
        action["authority"] = "observability_only"
        action["owner"] = "mas_controller"
        action["request_owner"] = "mas_controller"
        action["recommended_owner"] = "mas_controller"
        action["reason"] = current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
        action["summary"] = (
            "MAS domain transition oracle selected bundle-stage finalization; redrive the current "
            "controller route instead of repeating a stale analysis or write work unit."
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
    if action_type == "publication_gate_specificity_required":
        return "publication_gate"
    if action_type == "runtime_platform_repair":
        return "mas_controller"
    return "med-autoscience"


__all__ = ["actions"]
