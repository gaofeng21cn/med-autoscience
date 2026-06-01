from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import action_projection
from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.owner_route_reconcile_parts import domain_route_contract


def action_after_consumed_receipt(
    *,
    study_id: str,
    quest_id: str | None,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    consumed_receipt: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _text(consumed_receipt.get("execution_status")) != "executed":
        return None
    if _text(consumed_receipt.get("status")) != "consumed":
        return None
    controller_route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return None
    action = _action_from_controller_route(controller_route)
    if action is None:
        return None
    consumed_action_type = _text(consumed_receipt.get("action_type"))
    action_type = _text(action.get("action_type"))
    consumed_work_unit_id = _text(consumed_receipt.get("work_unit_id")) or _text(
        _mapping(consumed_receipt.get("owner_route_currentness_basis")).get("work_unit_id")
    )
    if action_type == consumed_action_type and _text(action.get("controller_work_unit_id")) == consumed_work_unit_id:
        return None
    return action_projection.decorate_action(
        study_id=study_id,
        quest_id=quest_id,
        action=action,
        request_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
        control_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
        forbidden_actions=list(domain_route_contract.SUPERVISION_FORBIDDEN_ACTIONS),
    )


def _action_from_controller_route(controller_route: Mapping[str, Any]) -> dict[str, Any] | None:
    controller_actions = {_text(item) for item in controller_route.get("controller_actions") or []}
    controller_actions.discard(None)
    work_unit_id = _text(controller_route.get("work_unit_id"))
    if work_unit_id is None:
        return None
    if "return_to_ai_reviewer_workflow" in controller_actions:
        return {
            "action_type": "return_to_ai_reviewer_workflow",
            "authority": "observability_only",
            "owner": "ai_reviewer",
            "request_owner": "ai_reviewer",
            "recommended_owner": "ai_reviewer",
            "reason": "domain_transition_ai_reviewer_re_eval",
            "summary": "The current controller decision routes this study back to the AI reviewer workflow.",
            "required_output_surface": "artifacts/publication_eval/latest.json",
            "next_work_unit": work_unit_id,
            "executable_work_unit": work_unit_id,
            "controller_work_unit_id": work_unit_id,
            "route_target": _text(controller_route.get("route_target")) or "review",
            "domain_transition_decision_type": "ai_reviewer_re_eval",
            "controller_route": dict(controller_route),
            "work_unit_fingerprint": _text(controller_route.get("work_unit_fingerprint")),
            "publication_eval_latest_write_allowed": False,
            "controller_decision_write_allowed": False,
            "paper_package_mutation_allowed": False,
        }
    if "run_gate_clearing_batch" in controller_actions:
        return {
            "action_type": "run_gate_clearing_batch",
            "authority": "observability_only",
            "owner": "gate_clearing_batch",
            "request_owner": "gate_clearing_batch",
            "recommended_owner": "gate_clearing_batch",
            "reason": work_unit_id,
            "summary": "The current controller decision routes publication-gate replay through the gate-clearing owner.",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "next_work_unit": work_unit_id,
            "executable_work_unit": work_unit_id,
            "controller_work_unit_id": work_unit_id,
            "controller_next_work_unit": {"unit_id": work_unit_id},
            "controller_action": "run_gate_clearing_batch",
            "route_target": _text(controller_route.get("route_target")),
            "domain_transition_decision_type": "route_back_same_line",
            "controller_route": dict(controller_route),
            "work_unit_fingerprint": _text(controller_route.get("work_unit_fingerprint")),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "current_package_write_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        }
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["action_after_consumed_receipt"]
