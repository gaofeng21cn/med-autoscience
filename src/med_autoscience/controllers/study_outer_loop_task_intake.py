from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience import study_task_intake
from med_autoscience.study_decision_record import StudyDecisionActionType, StudyDecisionType


def recommended_task_intake_action(
    *,
    study_root: Path,
    publishability_gate_report: dict[str, Any] | None = None,
    evaluation_summary: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    task_intake_payload = study_task_intake.read_latest_task_intake(study_root=study_root)
    task_intake_override = study_task_intake.build_task_intake_progress_override(
        task_intake_payload,
        publishability_gate_report=publishability_gate_report,
        evaluation_summary=evaluation_summary,
    )
    if not isinstance(task_intake_override, dict):
        return None
    current_required_action = str(task_intake_override.get("current_required_action") or "").strip()
    if current_required_action not in {"return_to_analysis_campaign", "continue_write_stage"}:
        return None
    quality_closure_truth = (
        dict(task_intake_override.get("quality_closure_truth") or {})
        if isinstance(task_intake_override.get("quality_closure_truth"), dict)
        else {}
    )
    quality_execution_lane = (
        dict(task_intake_override.get("quality_execution_lane") or {})
        if isinstance(task_intake_override.get("quality_execution_lane"), dict)
        else {}
    )
    same_line_route_truth = (
        dict(task_intake_override.get("same_line_route_truth") or {})
        if isinstance(task_intake_override.get("same_line_route_truth"), dict)
        else {}
    )
    route_target = (
        str(quality_execution_lane.get("route_target") or "").strip()
        or str(same_line_route_truth.get("route_target") or "").strip()
        or ("analysis-campaign" if current_required_action == "return_to_analysis_campaign" else "write")
    )
    route_key_question = (
        str(quality_execution_lane.get("route_key_question") or "").strip()
        or str(same_line_route_truth.get("current_focus") or "").strip()
        or "What is the narrowest supplementary analysis still required before the paper line can continue?"
    )
    route_rationale = (
        str(quality_execution_lane.get("summary") or "").strip()
        or str(quality_closure_truth.get("summary") or "").strip()
        or str(task_intake_override.get("next_system_action") or "").strip()
        or "Latest task intake requires bounded supplementary analysis before returning to the publication gate."
    )
    decision_type = (
        StudyDecisionType.BOUNDED_ANALYSIS.value
        if current_required_action == "return_to_analysis_campaign"
        else StudyDecisionType.CONTINUE_SAME_LINE.value
    )
    return {
        "action_id": f"task-intake::{Path(study_root).expanduser().resolve().name}::{route_target}",
        "action_type": decision_type,
        "priority": "now",
        "reason": route_rationale,
        "route_target": route_target,
        "route_key_question": route_key_question,
        "route_rationale": route_rationale,
        "requires_controller_decision": True,
        "controller_action_type": StudyDecisionActionType.ENSURE_STUDY_RUNTIME.value,
    }
