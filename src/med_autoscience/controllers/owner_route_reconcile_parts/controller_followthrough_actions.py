from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def action_from_controller_route(controller_route: Mapping[str, Any]) -> dict[str, Any] | None:
    controller_actions = set(_controller_action_types(controller_route.get("controller_actions")))
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


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _controller_action_types(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    action_types: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            text = _text(item.get("action_type"))
        else:
            text = _text(item)
        if text is not None and text not in action_types:
            action_types.append(text)
    return action_types


__all__ = ["action_from_controller_route"]
