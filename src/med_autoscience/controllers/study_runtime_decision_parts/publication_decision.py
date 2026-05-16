from __future__ import annotations

from typing import Callable

from med_autoscience.controllers import publication_work_units
from med_autoscience.publication_eval_record import PublicationEvalRecommendedAction

from med_autoscience.controllers.study_runtime_decision_parts import publication_stop_loss


SpecificityTargetsFn = Callable[[dict[str, object]], tuple[dict[str, str], ...]]

_PROSE_QUALITY_AUTHORITY_ACTIONS = frozenset(
    {"continue_write_stage", "continue_bundle_stage", "complete_bundle_stage"}
)
_READY_QUALITY_STATUS = "ready"
_PROSE_REVIEW_ROUTE = {
    "route_target": "review",
    "route_key_question": "Which AI-reviewer manuscript-quality issue must close before the manuscript can advance?",
    "route_rationale": (
        "AI reviewer medical_journal_prose_quality is not ready; route back to the same paper-line "
        "quality review before any write-stage or finalize-stage handoff."
    ),
}
_PROSE_REVIEW_WORK_UNIT = {
    "unit_id": "ai_reviewer_medical_prose_quality_review",
    "lane": "review",
    "summary": "Re-run AI reviewer manuscript-quality review and close medical_journal_prose_quality before draft advancement.",
}


def _medical_prose_quality_status(report: dict[str, object]) -> str:
    status = str(report.get("medical_prose_review_status") or "").strip()
    return status or "underdefined"


def _clear_stage_has_unready_prose_quality(report: dict[str, object]) -> bool:
    if str(report.get("status") or "").strip() != "clear":
        return False
    current_required_action = str(report.get("current_required_action") or "").strip()
    if current_required_action not in _PROSE_QUALITY_AUTHORITY_ACTIONS:
        return False
    status = _medical_prose_quality_status(report)
    return status != _READY_QUALITY_STATUS


def _prose_quality_route_action() -> tuple[str, dict[str, str]]:
    return "route_back_same_line", dict(_PROSE_REVIEW_ROUTE)


def _prose_quality_route_reason(report: dict[str, object]) -> str:
    status = _medical_prose_quality_status(report)
    return (
        f"AI reviewer medical_journal_prose_quality is {status}; "
        "a clear publication gate cannot authorize draft advancement until that quality dimension is ready."
    )


def _prose_quality_work_unit_payload(report: dict[str, object]) -> dict[str, object]:
    status = _medical_prose_quality_status(report)
    return {
        "fingerprint": f"medical-prose-quality::{status}",
        "blocking_work_units": [dict(_PROSE_REVIEW_WORK_UNIT)],
        "next_work_unit": dict(_PROSE_REVIEW_WORK_UNIT),
    }


def _route_contract_for_action(
    *,
    report: dict[str, object],
    action_type: str,
) -> dict[str, str] | None:
    current_required_action = str(report.get("current_required_action") or "").strip()
    controller_stage_note = str(report.get("controller_stage_note") or "").strip()
    if action_type == "bounded_analysis":
        return {
            "route_target": "analysis-campaign",
            "route_key_question": "What is the narrowest supplementary analysis still required before the paper line can continue?",
            "route_rationale": (
                controller_stage_note
                or "The current line is clear enough to continue after one bounded supplementary analysis pass."
            ),
        }
    if action_type == "stop_loss":
        return publication_stop_loss.stop_loss_route_contract(controller_stage_note=controller_stage_note)
    if action_type not in {"continue_same_line", "route_back_same_line"}:
        return None
    if current_required_action in {"continue_bundle_stage", "complete_bundle_stage"}:
        return {
            "route_target": "finalize",
            "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
            "route_rationale": (
                controller_stage_note
                or "The publication gate is clear and the current paper line can continue into finalize-stage work."
            ),
        }
    return {
        "route_target": "write",
        "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
        "route_rationale": (
            controller_stage_note
            or "The publication gate is clear and the current paper line can continue through same-line manuscript work."
        ),
    }


def _blocked_route_action(report: dict[str, object]) -> tuple[str, dict[str, str]] | None:
    route_back_recommendation = str(report.get("medical_publication_surface_route_back_recommendation") or "").strip()
    controller_stage_note = str(report.get("controller_stage_note") or "").strip()
    if publication_stop_loss.report_requests_stop_loss(report):
        return ("stop_loss", _route_contract_for_action(report=report, action_type="stop_loss") or {})
    if route_back_recommendation == "return_to_analysis_campaign":
        return (
            "bounded_analysis",
            {
                "route_target": "analysis-campaign",
                "route_key_question": "What is the narrowest supplementary analysis still required before the paper line can continue?",
                "route_rationale": (
                    controller_stage_note
                    or "The current blocked publication surface is best repaired through one bounded supplementary analysis pass."
                ),
            },
        )
    if route_back_recommendation == "return_to_finalize":
        return (
            "route_back_same_line",
            {
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "route_rationale": (
                    controller_stage_note
                    or "The current blocked publication surface should route back to finalize on the same paper line."
                ),
            },
        )
    if route_back_recommendation == "return_to_write":
        return (
            "route_back_same_line",
            {
                "route_target": "write",
                "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
                "route_rationale": (
                    controller_stage_note
                    or "The current blocked publication surface should route back to manuscript repair on the same paper line."
                ),
            },
        )
    return None


def _clear_publication_action(report: dict[str, object]) -> tuple[str, dict[str, str]]:
    if _clear_stage_has_unready_prose_quality(report):
        return _prose_quality_route_action()
    current_required_action = str(report.get("current_required_action") or "").strip()
    if current_required_action == "prepare_promotion_review":
        action_type = "prepare_promotion_review"
    elif current_required_action == "continue_write_stage":
        action_type = "bounded_analysis"
    else:
        action_type = "continue_same_line"
    return action_type, _route_contract_for_action(report=report, action_type=action_type) or {}


def _blocked_publication_action(report: dict[str, object]) -> tuple[str, dict[str, str]]:
    blocked_route_action = _blocked_route_action(report)
    if blocked_route_action is not None:
        return blocked_route_action
    current_required_action = str(report.get("current_required_action") or "").strip()
    if publication_stop_loss.report_requests_stop_loss(report):
        return "stop_loss", _route_contract_for_action(report=report, action_type="stop_loss") or {}
    if current_required_action in {"continue_bundle_stage", "complete_bundle_stage"}:
        action_type = "route_back_same_line"
        return action_type, _route_contract_for_action(report=report, action_type=action_type) or {}
    return "return_to_controller", {}


def publication_eval_action(
    *,
    report: dict[str, object],
    generated_at: str,
    evidence_refs: tuple[str, ...],
    specificity_targets: SpecificityTargetsFn,
) -> PublicationEvalRecommendedAction:
    status = str(report.get("status") or "").strip()
    if status == "clear":
        action_type, route_contract = _clear_publication_action(report)
        reason = (
            _prose_quality_route_reason(report)
            if _clear_stage_has_unready_prose_quality(report)
            else str(report.get("controller_stage_note") or "").strip()
            or "Publication gate is clear and the current line can continue."
        )
    else:
        action_type, route_contract = _blocked_publication_action(report)
        reason = (
            str(report.get("controller_stage_note") or "").strip()
            or "Publication gate is blocked and requires controller review."
        )
    if _clear_stage_has_unready_prose_quality(report):
        work_unit_payload = _prose_quality_work_unit_payload(report)
    else:
        work_unit_payload = publication_work_units.derive_publication_work_units(report)
    if publication_stop_loss.non_actionable_gate_overrides(status=status, action_type=action_type, work_unit_payload=work_unit_payload):
        action_type = "return_to_controller"
        route_contract = {}
    work_unit_fingerprint = str(work_unit_payload.get("fingerprint") or "").strip()
    action_id_suffix = work_unit_fingerprint or generated_at
    return PublicationEvalRecommendedAction(
        action_id=f"publication-eval-action::{action_type}::{action_id_suffix}",
        action_type=action_type,
        priority="now",
        reason=reason,
        evidence_refs=evidence_refs,
        route_target=route_contract.get("route_target"),
        route_key_question=route_contract.get("route_key_question"),
        route_rationale=route_contract.get("route_rationale"),
        requires_controller_decision=True,
        work_unit_fingerprint=work_unit_fingerprint or None,
        blocking_work_units=tuple(work_unit_payload.get("blocking_work_units") or ()),
        next_work_unit=work_unit_payload.get("next_work_unit") if isinstance(work_unit_payload.get("next_work_unit"), dict) else None,
        specificity_targets=specificity_targets(report),
    )
