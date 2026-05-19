from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_outer_loop_parts.decision_refs import (
    _read_evaluation_summary_payload,
)
from med_autoscience.controllers.study_outer_loop_parts.runtime_state import _runtime_status_is_live
from med_autoscience.study_decision_record import (
    StudyDecisionActionType,
    StudyDecisionType,
)
from med_autoscience.publication_eval_reviewer_os import current_ai_reviewer_route_back_action
from med_autoscience.publication_eval_specificity_targets import specificity_target_status


_GATE_NEEDS_SPECIFICITY_UNIT_ID = "gate_needs_specificity"
_GATE_NEEDS_SPECIFICITY_QUESTION = (
    "gate_needs_specificity: Which exact claim, figure, table, metric, source path, or package artifact is blocking "
    "the publication gate?"
)
_GATE_NEEDS_SPECIFICITY_RATIONALE = (
    "Publication gate selected gate_needs_specificity because the current blocker is generic and lacks concrete "
    "claim, display, evidence, citation, metric, source path, package artifact, or provenance target details."
)
_SUBMISSION_HANDOFF_GAP_TYPES = frozenset({"delivery", "reporting"})
_SUBMISSION_HANDOFF_TERMS = (
    "admin metadata",
    "administrative metadata",
    "author metadata",
    "author-confirmed",
    "author confirmed",
    "affiliation",
    "corresponding author",
    "title-page",
    "title page",
    "declaration",
    "declarations",
    "funding",
    "conflict of interest",
    "competing interest",
    "ethics",
    "consent",
    "data availability",
    "cover letter",
    "submission metadata",
    "submission-ready release",
    "bundle proof",
    "bundle proofing",
    "final proofing",
    "provenance proof",
    "provenance surfaces",
)
_SUBMISSION_HANDOFF_BLOCKING_TERMS = (
    "claim",
    "evidence gap",
    "external validation",
    "analysis",
    "model",
    "sensitivity",
    "subgroup",
    "endpoint",
    "cohort",
    "method",
    "methods",
    "result",
    "results",
    "figure",
    "table",
    "metric",
    "data cleaning",
    "rerun",
    "re-run",
    "experiment",
)


def _publication_supervisor_human_gate_requested(status_payload: dict[str, Any]) -> bool:
    publication_supervisor_state = status_payload.get("publication_supervisor_state")
    if not isinstance(publication_supervisor_state, dict):
        return False
    return str(publication_supervisor_state.get("current_required_action") or "").strip() == "human_confirmation_required"


def _recommended_publication_eval_action(publication_eval_payload: dict[str, Any]) -> dict[str, Any] | None:
    recommended_actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(recommended_actions, list):
        return None
    for action in recommended_actions:
        if not isinstance(action, dict):
            continue
        if action.get("requires_controller_decision") is not True:
            continue
        if _autonomous_decision_type_for_publication_eval_action(action) is None:
            continue
        return dict(action)
    return None


def _current_ai_reviewer_route_back_preempts_ai_reviewer_recheck(
    *,
    domain_transition_decision_type: str,
    publication_eval_payload: dict[str, Any],
) -> bool:
    action = current_ai_reviewer_route_back_action(publication_eval_payload)
    return domain_transition_decision_type == "ai_reviewer_re_eval" and (
        action is not None and _autonomous_decision_type_for_publication_eval_action(action) is not None
    )


def _quality_dimension_status(*, payload: dict[str, Any], dimension: str) -> str | None:
    quality_assessment = payload.get("quality_assessment")
    if not isinstance(quality_assessment, dict):
        return None
    dimension_payload = quality_assessment.get(dimension)
    if not isinstance(dimension_payload, dict):
        return None
    status = str(dimension_payload.get("status") or "").strip()
    return status or None


def _publication_eval_has_only_optional_gaps(publication_eval_payload: dict[str, Any]) -> bool:
    gaps = publication_eval_payload.get("gaps")
    if not isinstance(gaps, list):
        return False
    for gap in gaps:
        if not isinstance(gap, dict):
            return False
        if not _publication_eval_gap_is_submission_milestone_handoff(gap):
            return False
    return True


def _publication_eval_gap_is_submission_milestone_handoff(gap: dict[str, Any]) -> bool:
    severity = str(gap.get("severity") or "").strip()
    if severity == "optional":
        return True
    if severity != "important":
        return False
    gap_type = str(gap.get("gap_type") or "").strip()
    if gap_type not in _SUBMISSION_HANDOFF_GAP_TYPES:
        return False
    text = " ".join(
        str(value or "").strip().lower()
        for value in (
            gap.get("gap_id"),
            gap.get("gap_type"),
            gap.get("summary"),
        )
        if str(value or "").strip()
    )
    if any(term in text for term in _SUBMISSION_HANDOFF_BLOCKING_TERMS):
        return False
    return any(term in text for term in _SUBMISSION_HANDOFF_TERMS)


def _submission_milestone_route_context(
    *,
    study_root: Path,
    publication_eval_payload: dict[str, Any],
) -> dict[str, Any] | None:
    summary_payload = _read_evaluation_summary_payload(study_root=study_root)
    if summary_payload is None:
        return None
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    if str(quality_closure_truth.get("state") or "").strip() != "bundle_only_remaining":
        return None
    verdict = publication_eval_payload.get("verdict")
    if not isinstance(verdict, dict) or str(verdict.get("overall_verdict") or "").strip() != "promising":
        return None
    if not _publication_eval_has_only_optional_gaps(publication_eval_payload):
        return None
    human_review_status = _quality_dimension_status(
        payload=summary_payload,
        dimension="human_review_readiness",
    ) or _quality_dimension_status(
        payload=publication_eval_payload,
        dimension="human_review_readiness",
    )
    if human_review_status != "ready":
        return None
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), dict)
        else {}
    )
    route_target = str(
        quality_execution_lane.get("route_target") or quality_closure_truth.get("route_target") or ""
    ).strip()
    if route_target and route_target != "finalize":
        return None
    route_key_question = str(quality_execution_lane.get("route_key_question") or "").strip()
    route_rationale = str(
        quality_execution_lane.get("summary")
        or quality_closure_truth.get("summary")
        or "Human-review milestone reached and only finalize-level bundle cleanup remains."
    ).strip()
    return {
        "summary_payload": summary_payload,
        "route_target": "finalize",
        "route_key_question": route_key_question
        or "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "route_rationale": route_rationale,
    }


def _recommended_submission_milestone_autopark_action(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
    publication_eval_payload: dict[str, Any],
    require_live_runtime: bool = True,
) -> dict[str, Any] | None:
    if require_live_runtime and not _runtime_status_is_live(status_payload):
        return None
    route_context = _submission_milestone_route_context(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if route_context is None:
        return None
    return {
        "action_id": f"quality-milestone::{study_root.name}::autopark",
        "action_type": StudyDecisionType.CONTINUE_SAME_LINE.value,
        "priority": "now",
        "reason": "Human-review milestone reached; stop the live runtime and wait for explicit resume.",
        "route_target": str(route_context.get("route_target") or "").strip() or "finalize",
        "route_key_question": str(route_context.get("route_key_question") or "").strip()
        or "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "route_rationale": str(route_context.get("route_rationale") or "").strip(),
        "requires_controller_decision": True,
        "controller_action_type": StudyDecisionActionType.STOP_RUNTIME.value,
    }


def _recommended_manuscript_fast_lane_closeout_autopark_action(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any] | None:
    if not _runtime_status_is_live(status_payload):
        return None
    return {
        "action_id": f"manuscript-fast-lane-closeout::{study_root.name}::autopark",
        "action_type": StudyDecisionType.CONTINUE_SAME_LINE.value,
        "priority": "now",
        "reason": (
            "Manuscript fast lane closeout supersedes the latest task intake; "
            "stop the live runtime and wait for explicit resume."
        ),
        "route_target": "write",
        "route_key_question": "Should MAS/MDS resume this paper line after foreground fast lane closeout?",
        "route_rationale": (
            "A controller-visible manuscript fast lane closeout is newer than the latest task intake and "
            "declares that the superseded task intake must not auto-resume."
        ),
        "requires_controller_decision": True,
        "controller_action_type": StudyDecisionActionType.STOP_RUNTIME.value,
    }


def _recommended_quality_review_loop_action(*, study_root: Path) -> dict[str, Any] | None:
    summary_payload = _read_evaluation_summary_payload(study_root=study_root)
    if summary_payload is None:
        return None
    quality_review_loop = (
        dict(summary_payload.get("quality_review_loop") or {})
        if isinstance(summary_payload.get("quality_review_loop"), dict)
        else {}
    )
    current_phase = str(quality_review_loop.get("current_phase") or "").strip()
    if current_phase != "re_review_required" and quality_review_loop.get("re_review_ready") is not True:
        return None
    next_review_focus = [
        str(item).strip()
        for item in (quality_review_loop.get("next_review_focus") or [])
        if str(item).strip()
    ]
    route_key_question = next_review_focus[0] if next_review_focus else "当前 blocking issues 是否已真正闭环？"
    summary = str(quality_review_loop.get("summary") or "").strip()
    recommended_next_action = str(quality_review_loop.get("recommended_next_action") or "").strip()
    reason = recommended_next_action or summary or "MAS 应发起下一轮质量复评，确认当前 blocking issues 是否已真正闭环。"
    route_rationale = summary or reason
    return {
        "action_id": f"quality-review-loop::{quality_review_loop.get('loop_id') or study_root.name}::re_review",
        "action_type": StudyDecisionType.CONTINUE_SAME_LINE.value,
        "priority": "now",
        "reason": reason,
        "route_target": "review",
        "route_key_question": route_key_question,
        "route_rationale": route_rationale,
        "requires_controller_decision": True,
    }


def _autonomous_decision_type_for_publication_eval_action(action_payload: dict[str, Any]) -> str | None:
    action_type = str(action_payload.get("action_type") or "").strip()
    next_work_unit = action_payload.get("next_work_unit")
    next_work_unit_id = (
        str(next_work_unit.get("unit_id") or "").strip()
        if isinstance(next_work_unit, dict)
        else ""
    )
    if action_type == StudyDecisionType.RETURN_TO_CONTROLLER.value and next_work_unit_id == _GATE_NEEDS_SPECIFICITY_UNIT_ID:
        return StudyDecisionType.RETURN_TO_CONTROLLER.value
    if action_type == StudyDecisionType.CONTINUE_SAME_LINE.value:
        return StudyDecisionType.CONTINUE_SAME_LINE.value
    if action_type == StudyDecisionType.ROUTE_BACK_SAME_LINE.value:
        return StudyDecisionType.ROUTE_BACK_SAME_LINE.value
    if action_type == StudyDecisionType.BOUNDED_ANALYSIS.value:
        return StudyDecisionType.BOUNDED_ANALYSIS.value
    if action_type == StudyDecisionType.STOP_LOSS.value:
        return StudyDecisionType.STOP_LOSS.value
    return None


def _action_has_gate_needs_specificity_work_unit(action_payload: dict[str, Any]) -> bool:
    next_work_unit = action_payload.get("next_work_unit")
    if isinstance(next_work_unit, dict) and str(next_work_unit.get("unit_id") or "").strip() == _GATE_NEEDS_SPECIFICITY_UNIT_ID:
        return True
    blocking_work_units = action_payload.get("blocking_work_units")
    if not isinstance(blocking_work_units, list):
        return False
    for work_unit in blocking_work_units:
        if isinstance(work_unit, dict) and str(work_unit.get("unit_id") or "").strip() == _GATE_NEEDS_SPECIFICITY_UNIT_ID:
            return True
    return False


def _promote_gate_needs_specificity_action(action_payload: dict[str, Any]) -> dict[str, Any]:
    if not _action_has_gate_needs_specificity_work_unit(action_payload):
        return action_payload
    if specificity_target_status(action_payload.get("specificity_targets")).get("complete") is True:
        return action_payload
    promoted = dict(action_payload)
    prior_route_key_question = str(promoted.get("route_key_question") or "").strip()
    if prior_route_key_question and not str(promoted.get("source_route_key_question") or "").strip():
        promoted["source_route_key_question"] = prior_route_key_question
    promoted["action_type"] = StudyDecisionType.RETURN_TO_CONTROLLER.value
    promoted["route_target"] = "controller"
    promoted["route_key_question"] = _GATE_NEEDS_SPECIFICITY_QUESTION
    promoted["route_rationale"] = _GATE_NEEDS_SPECIFICITY_RATIONALE
    promoted["reason"] = _GATE_NEEDS_SPECIFICITY_RATIONALE
    promoted["controller_action_type"] = StudyDecisionActionType.REQUEST_GATE_SPECIFICITY.value
    promoted["requires_controller_decision"] = True
    return promoted


def _autonomous_controller_action_type_for_runtime_status(status_payload: dict[str, Any]) -> str:
    if str(status_payload.get("reason") or "").strip() == "quest_stopped_requires_explicit_rerun":
        return StudyDecisionActionType.ENSURE_STUDY_RUNTIME_RELAUNCH_STOPPED.value
    return StudyDecisionActionType.ENSURE_STUDY_RUNTIME.value


def _quality_repair_batch_preempts_task_intake(batch_action: dict[str, Any] | None) -> bool:
    if not isinstance(batch_action, dict):
        return False
    return (
        str(batch_action.get("controller_action_type") or "").strip()
        == StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value
    )
