from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers import study_macro_state
from med_autoscience.study_decision_record import StudyDecisionActionType, StudyDecisionType


_TRANSITION_DECISION_TYPES = frozenset(
    {
        "ai_reviewer_re_eval",
        "bundle_stage_finalize",
        "publication_gate_blocker",
    }
)


def domain_transition_recommended_action(
    *,
    study_id: str,
    study_root: Path,
    status_payload: Mapping[str, Any],
    active_run_id: str | None,
) -> dict[str, Any] | None:
    macro_state = study_macro_state.derive_study_macro_state(
        study_id=study_id,
        status=dict(status_payload),
        progress={},
    )
    transition = study_domain_transition_table.project_domain_transition(
        study_id=study_id,
        study_root=study_root,
        status=status_payload,
        macro_state=macro_state,
        active_run_id=active_run_id,
    )
    decision_type = _text(transition.get("decision_type"))
    if decision_type not in _TRANSITION_DECISION_TYPES:
        return None
    if decision_type == "publication_gate_blocker" and _gate_report_has_concrete_blocker_refs(
        _mapping(status_payload.get("publication_gate_report"))
    ):
        return None
    next_work_unit = _mapping(transition.get("next_work_unit"))
    unit_id = _text(next_work_unit.get("unit_id"))
    if unit_id is None:
        return None
    controller_action_type = _controller_action_type_for_transition(transition)
    if controller_action_type is None:
        return None
    action_type = _decision_action_type_for_transition(transition)
    if action_type is None:
        return None
    route_target = _text(transition.get("route_target")) or "controller"
    return {
        "action_id": f"domain-transition::{study_id}::{decision_type}",
        "action_type": action_type,
        "priority": "now",
        "reason": _transition_reason(transition),
        "route_target": route_target,
        "route_key_question": _route_key_question(transition),
        "route_rationale": _route_rationale(transition),
        "requires_controller_decision": True,
        "controller_action_type": controller_action_type,
        "evidence_refs": list(transition.get("source_refs") or []),
        "work_unit_fingerprint": f"domain-transition::{decision_type}::{unit_id}",
        "next_work_unit": dict(next_work_unit),
        "blocking_work_units": [dict(next_work_unit)],
        "domain_transition": dict(transition),
    }


def _controller_action_type_for_transition(transition: Mapping[str, Any]) -> str | None:
    controller_action = _text(transition.get("controller_action"))
    if controller_action == "run_gate_clearing_batch":
        return StudyDecisionActionType.RUN_GATE_CLEARING_BATCH.value
    if controller_action == "return_to_ai_reviewer_workflow":
        return StudyDecisionActionType.RETURN_TO_AI_REVIEWER_WORKFLOW.value
    if controller_action == "continue_bundle_stage":
        return StudyDecisionActionType.ENSURE_STUDY_RUNTIME.value
    return None


def _decision_action_type_for_transition(transition: Mapping[str, Any]) -> str | None:
    decision_type = _text(transition.get("decision_type"))
    if decision_type == "publication_gate_blocker":
        return StudyDecisionType.BOUNDED_ANALYSIS.value
    if decision_type in {"ai_reviewer_re_eval", "bundle_stage_finalize"}:
        return StudyDecisionType.CONTINUE_SAME_LINE.value
    return None


def _transition_reason(transition: Mapping[str, Any]) -> str:
    decision_type = _text(transition.get("decision_type"))
    blocker = _mapping(transition.get("typed_blocker"))
    next_work_unit = _mapping(transition.get("next_work_unit"))
    if summary := _text(blocker.get("summary")):
        return summary
    if summary := _text(next_work_unit.get("summary")):
        return summary
    return f"MAS domain transition selected {decision_type or 'current'} as the current controller route."


def _route_key_question(transition: Mapping[str, Any]) -> str:
    decision_type = _text(transition.get("decision_type"))
    if decision_type == "ai_reviewer_re_eval":
        return "当前稿件是否已经通过 AI reviewer-owned publication evaluation？"
    if decision_type == "bundle_stage_finalize":
        return "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"
    if decision_type == "publication_gate_blocker":
        return "当前 publication gate blockers 应由哪一个 MAS owner surface 重新判定并派发？"
    return "当前 MAS domain transition 要求执行哪个 controller owner work unit？"


def _route_rationale(transition: Mapping[str, Any]) -> str:
    decision_type = _text(transition.get("decision_type"))
    if decision_type == "ai_reviewer_re_eval":
        return "Mechanical or stale publication projection cannot authorize quality closure; AI reviewer must own the next evaluation."
    if decision_type == "bundle_stage_finalize":
        return "The publication gate is clear and bundle-stage controller closure now supersedes stale analysis or write work units."
    if decision_type == "publication_gate_blocker":
        return "The publication gate is blocked; replay the gate through MAS owner authority before redriving any repair unit."
    return _transition_reason(transition)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _gate_report_has_concrete_blocker_refs(gate_report: Mapping[str, Any]) -> bool:
    for key in ("blocking_artifact_refs", "blocker_details", "gate_blocker_details", "gaps"):
        value = gate_report.get(key)
        if isinstance(value, list) and value:
            return True
        if isinstance(value, Mapping) and value:
            return True
    return False


__all__ = ["domain_transition_recommended_action"]
