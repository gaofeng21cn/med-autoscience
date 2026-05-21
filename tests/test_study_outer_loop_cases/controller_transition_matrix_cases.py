from __future__ import annotations

from dataclasses import dataclass

import pytest

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


@dataclass(frozen=True)
class WorkUnitTransitionCase:
    case_id: str
    gate_report: dict[str, object]
    expected_actionability_status: str
    expected_unit_id: str
    expected_lane: str


@pytest.mark.parametrize(
    "case",
    (
        WorkUnitTransitionCase(
            case_id="clear_bundle_stage_moves_to_submission_authority_sync",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "current",
            },
            expected_actionability_status="controller_bundle_stage_required",
            expected_unit_id="submission_authority_sync_closure",
            expected_lane="controller",
        ),
        WorkUnitTransitionCase(
            case_id="blocked_bundle_stage_stale_authority_moves_to_submission_authority_sync",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["stale_submission_minimal_authority"],
                "current_required_action": "complete_bundle_stage",
                "supervisor_phase": "bundle_stage_blocked",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "stale_source_changed",
                "submission_minimal_evaluated_source_signature": "source::new",
                "submission_minimal_authority_source_signature": "source::old",
            },
            expected_actionability_status="controller_authority_sync_required",
            expected_unit_id="submission_authority_sync_closure",
            expected_lane="controller",
        ),
        WorkUnitTransitionCase(
            case_id="publishability_gate_blocked_claim_evidence_stays_analysis_repair",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
                "blocking_artifact_refs": [{"source_path": "paper/evidence_ledger.json"}],
            },
            expected_actionability_status="actionable",
            expected_unit_id="analysis_claim_evidence_repair",
            expected_lane="analysis-campaign",
        ),
        WorkUnitTransitionCase(
            case_id="publishability_gate_blocked_label_only_claim_requires_specificity",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
            },
            expected_actionability_status="blocked_by_non_actionable_gate",
            expected_unit_id="gate_needs_specificity",
            expected_lane="controller",
        ),
    ),
    ids=lambda case: case.case_id,
)
def test_publication_gate_report_to_work_unit_transition_matrix(case: WorkUnitTransitionCase) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_work_units")

    result = module.derive_publication_work_units(case.gate_report)

    assert result["actionability_status"] == case.expected_actionability_status
    assert result["next_work_unit"]["unit_id"] == case.expected_unit_id
    assert result["next_work_unit"]["lane"] == case.expected_lane


@dataclass(frozen=True)
class OuterLoopTransitionCase:
    case_id: str
    gate_report: dict[str, object]
    publication_eval_action: dict[str, object]
    publication_eval_verdict: str
    publication_supervisor_state: dict[str, object]
    expected_decision_type: str
    expected_route_target: str
    expected_controller_action_type: str
    expected_unit_id: str
    task_intake_action: dict[str, object] | None = None
    assessment_provenance: dict[str, object] | None = None
    quality_assessment: dict[str, object] | None = None


def _ready_reviewer_operating_system(study_root: Path) -> dict[str, object]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    refs = {
        "manuscript": str(study_root / "paper" / "manuscript.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(publication_eval_path),
    }
    dimensions = (
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    )
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": refs,
        "rubric_scores": {
            dimension: {
                "status": "ready",
                "rationale": f"{dimension} is closed by AI reviewer currentness evidence.",
                "evidence_refs": [refs["manuscript"], refs["evidence_ledger"], refs["review_ledger"]],
            }
            for dimension in dimensions
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": "ready",
                "rationale": f"{dimension} is closed by AI reviewer currentness evidence.",
            }
            for dimension in dimensions
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": "sha256:transition-matrix-medical-prose-review-request",
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": "sha256:transition-matrix-manuscript",
            },
            "current_package_freshness": {
                "status": "fresh",
                "source_eval_id": "publication-eval::001-risk::quest-001::transition-matrix",
            },
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "Finalize authorization is limited to the reviewed manuscript snapshot.",
                "impact_on_claim": "Paper claims must remain restrained to the reviewed evidence support.",
                "required_future_analysis_data_or_design": "Refresh AI reviewer currentness after substantive changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "continue_finalize",
            "rationale": "AI reviewer currentness evidence is closed for this transition fixture.",
        },
    }


def _current_write_route_back_reviewer_operating_system(study_root: Path) -> dict[str, object]:
    payload = _ready_reviewer_operating_system(study_root)
    payload["currentness_checks"]["medical_prose_review"] = {
        "status": "current",
        "request_ref": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
        "request_digest": "sha256:transition-matrix-current-route-back-request",
        "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
        "manuscript_digest": "sha256:transition-matrix-current-route-back-manuscript",
        "route_back_required": True,
        "route_target": "write",
    }
    payload["route_back_decision"] = {
        "recommended_action": "route_back_same_line",
        "rationale": "AI reviewer currentness is closed and routes the same paper line back to write.",
    }
    return payload


def _publication_eval_payload(
    *,
    study_root: Path,
    quest_root: Path,
    action: dict[str, object],
    verdict: str,
    assessment_provenance: dict[str, object] | None = None,
    quality_assessment: dict[str, object] | None = None,
) -> dict[str, object]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    default_quality_dimension = {
        "status": "ready",
        "summary": "Transition matrix fixture quality dimension is ready.",
        "evidence_refs": [str(publication_eval_path)],
    }
    payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::transition-matrix",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-05-14T09:30:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(
                quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
            ),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": assessment_provenance
        or {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [str(study_root / "paper" / "manuscript.md")],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": verdict,
            "primary_claim_status": "supported" if verdict == "promising" else "partial",
            "summary": "Transition-matrix publication evaluation fixture.",
            "stop_loss_pressure": "none" if verdict == "promising" else "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-transition-matrix",
                "gap_type": "delivery" if action.get("route_target") == "finalize" else "evidence",
                "severity": "important",
                "summary": "Transition matrix gap fixture.",
                "evidence_refs": [str(publication_eval_path)],
            }
        ],
        "quality_assessment": quality_assessment
        or {
            "clinical_significance": dict(default_quality_dimension),
            "evidence_strength": dict(default_quality_dimension),
            "novelty_positioning": dict(default_quality_dimension),
            "human_review_readiness": dict(default_quality_dimension),
            "medical_journal_prose_quality": {
                **default_quality_dimension,
                "summary": "AI reviewer judged the medical-journal prose quality ready.",
            },
        },
        "reviewer_operating_system": (
            _current_write_route_back_reviewer_operating_system(study_root)
            if action.get("action_type") == "route_back_same_line" and action.get("route_target") == "write"
            else _ready_reviewer_operating_system(study_root)
        ),
        "recommended_actions": [action],
    }
    return payload


def _finalize_review_only_action(study_root: Path) -> dict[str, object]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    return {
        "action_id": "action-finalize-review-only",
        "action_type": "continue_same_line",
        "priority": "now",
        "reason": "Bundle-stage work is unlocked and should continue on the finalize lane.",
        "route_target": "finalize",
        "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "route_rationale": "Only bundle-stage controller work remains.",
        "evidence_refs": [str(publication_eval_path)],
        "work_unit_fingerprint": "publication-blockers::review",
        "next_work_unit": {
            "unit_id": "publication_gate_blocker_review",
            "lane": "review",
            "summary": "Review the current publication gate blockers and select the narrowest repair unit.",
        },
        "blocking_work_units": [
            {
                "unit_id": "publication_gate_blocker_review",
                "lane": "review",
                "summary": "Review the current publication gate blockers and select the narrowest repair unit.",
            }
        ],
        "requires_controller_decision": True,
    }


def _bounded_analysis_action(study_root: Path) -> dict[str, object]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    return {
        "action_id": "action-analysis-repair",
        "action_type": "bounded_analysis",
        "priority": "now",
        "reason": "Claim-evidence blockers require bounded analysis repair before publication packaging.",
        "route_target": "analysis-campaign",
        "route_key_question": "Which claim-evidence repair is still blocking publishability?",
        "route_rationale": "Publication gate selected a claim-evidence repair work unit.",
        "evidence_refs": [str(publication_eval_path)],
        "requires_controller_decision": True,
        "next_work_unit": {
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
        },
        "blocking_work_units": [
            {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
            }
        ],
        "work_unit_fingerprint": "publication-blockers::analysis",
    }


def _write_route_back_action(study_root: Path) -> dict[str, object]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    return {
        "action_id": "ai-reviewer-action::return-to-write-clean-story",
        "action_type": "route_back_same_line",
        "priority": "now",
        "reason": "The current manuscript needs story-level write repair.",
        "route_target": "write",
        "route_key_question": "Can the writer produce a clean external-validation manuscript from the current evidence?",
        "route_rationale": "AI reviewer currentness is closed; the next owner is write, not another reviewer pass.",
        "evidence_refs": [str(publication_eval_path), str(study_root / "paper" / "manuscript.md")],
        "requires_controller_decision": True,
        "next_work_unit": {
            "unit_id": "manuscript_story_repair",
            "lane": "write",
            "summary": "Rewrite the manuscript as a clean external-validation paper.",
        },
        "blocking_work_units": [
            {
                "unit_id": "manuscript_story_repair",
                "lane": "write",
                "summary": "Rewrite the manuscript as a clean external-validation paper.",
            }
        ],
        "work_unit_fingerprint": "ai_reviewer_story_clean_external_validation_v3",
    }


def _stale_write_task_intake_action() -> dict[str, object]:
    return {
        "action_id": "task-intake::001-risk::write",
        "action_type": "continue_same_line",
        "priority": "now",
        "reason": "Stale write task intake should yield once bundle-stage is authoritative.",
        "route_target": "write",
        "route_key_question": "旧 manuscript revision work unit。",
        "route_rationale": "Old write task intake residue.",
        "requires_controller_decision": True,
        "controller_action_type": "ensure_study_runtime",
        "next_work_unit": {
            "unit_id": "manuscript_story_repair",
            "lane": "write",
            "summary": "Repair the paper story around the current evidence and claim boundary.",
        },
        "work_unit_fingerprint": "publication-blockers::stale-write",
    }


@pytest.mark.parametrize(
    "case_factory",
    (
        lambda study_root: OuterLoopTransitionCase(
            case_id="domain_transition_bundle_finalize_preempts_stale_rebuttal_task_intake",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "current",
            },
            publication_eval_action={
                "action_id": "action-stale-rebuttal-coverage",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Stale rebuttal coverage closeout should yield to bundle-stage authority.",
                "route_target": "analysis-campaign",
                "route_key_question": "paper/rebuttal/review_matrix.md and action_plan.md coverage closeout",
                "route_rationale": "Old analysis-campaign route residue.",
                "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                "requires_controller_decision": True,
                "next_work_unit": {
                    "unit_id": "rebuttal_coverage_closeout",
                    "lane": "analysis-campaign",
                    "summary": "Confirm reviewer feedback coverage.",
                },
                "blocking_work_units": [
                    {
                        "unit_id": "rebuttal_coverage_closeout",
                        "lane": "analysis-campaign",
                        "summary": "Confirm reviewer feedback coverage.",
                    }
                ],
            },
            publication_eval_verdict="promising",
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            task_intake_action={
                "action_id": "task-intake::001-risk::rebuttal",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Old rebuttal coverage task intake residue.",
                "route_target": "analysis-campaign",
                "route_key_question": "paper/rebuttal/review_matrix.md and action_plan.md coverage closeout",
                "route_rationale": "Old analysis-campaign route residue.",
                "requires_controller_decision": True,
                "controller_action_type": "ensure_study_runtime",
                "next_work_unit": {
                    "unit_id": "rebuttal_coverage_closeout",
                    "lane": "analysis-campaign",
                    "summary": "Confirm reviewer feedback coverage.",
                },
                "work_unit_fingerprint": "publication-blockers::stale-rebuttal",
            },
            expected_decision_type="continue_same_line",
            expected_route_target="finalize",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="submission_authority_sync_closure",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="domain_transition_ai_reviewer_required_preempts_stale_write_task_intake",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
            },
            publication_eval_action={
                "action_id": "action-stale-write",
                "action_type": "continue_same_line",
                "priority": "now",
                "reason": "Old manuscript write task should yield to AI reviewer assessment.",
                "route_target": "write",
                "route_key_question": "MAS/MDS-supervised revised manuscript package",
                "route_rationale": "Old write route residue.",
                "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                "requires_controller_decision": True,
                "next_work_unit": {
                    "unit_id": "revised_manuscript_package",
                    "lane": "write",
                    "summary": "Continue canonical manuscript revisions.",
                },
            },
            publication_eval_verdict="promising",
            assessment_provenance={
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "policy_id": "publication_gate_projection_v1",
                "source_refs": [str(study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
                "ai_reviewer_required": True,
            },
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            task_intake_action=_stale_write_task_intake_action(),
            expected_decision_type="continue_same_line",
            expected_route_target="review",
            expected_controller_action_type="return_to_ai_reviewer_workflow",
            expected_unit_id="ai_reviewer_recheck",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="ai_reviewer_underdefined_medical_prose_preempts_bundle_finalize",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "current",
            },
            publication_eval_action=_finalize_review_only_action(study_root),
            publication_eval_verdict="promising",
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            quality_assessment={
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical significance is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence strength is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Novelty positioning is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human review readiness is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": (
                        "AI reviewer has not yet closed medical-journal prose quality for this manuscript."
                    ),
                    "evidence_refs": [str(study_root / "paper")],
                }
            },
            expected_decision_type="continue_same_line",
            expected_route_target="review",
            expected_controller_action_type="return_to_ai_reviewer_workflow",
            expected_unit_id="ai_reviewer_medical_prose_quality_review",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="methodology_harmonization_route_back_preempts_ai_reviewer_prose_recheck",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "bundle_tasks_downstream_only": True,
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
                "blocking_artifact_refs": [{"source_path": "analysis/clean_room_execution/20_transportability"}],
            },
            publication_eval_action={
                **_bounded_analysis_action(study_root),
                "reason": (
                    "HDL/unit harmonization and unit-standardized transport rerun must be resolved "
                    "before prose quality can close."
                ),
                "route_key_question": (
                    "Can the HDL/unit harmonization issue be rerun as a unit-standardized external validation, "
                    "or must the transported-score claim be typed-blocked?"
                ),
                "next_work_unit": {
                    "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                    "lane": "analysis-campaign",
                    "summary": (
                        "Materialize or type-block model reproducibility, uncertainty, calibration, "
                        "and HDL harmonization evidence before prose/finalize review."
                    ),
                },
                "blocking_work_units": [
                    {
                        "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                        "lane": "analysis-campaign",
                        "summary": (
                            "Materialize or type-block model reproducibility, uncertainty, calibration, "
                            "and HDL harmonization evidence before prose/finalize review."
                        ),
                    }
                ],
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::medical_prose_quality_route_back_analysis"
                ),
            },
            publication_eval_verdict="blocked",
            publication_supervisor_state={
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
                "bundle_tasks_downstream_only": True,
                "publication_gate_allows_direct_write": False,
            },
            task_intake_action={
                "action_id": "task-intake::001-risk::analysis-campaign",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Methodology correction requires analysis/harmonization owner before prose repair.",
                "route_target": "analysis-campaign",
                "route_key_question": (
                    "unit-harmonized external validation rerun or typed blocker"
                ),
                "route_rationale": "Latest reviewer_revision intake is a methodology correction, not prose polish.",
                "requires_controller_decision": True,
                "controller_action_type": "ensure_study_runtime",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::medical_prose_quality_route_back_analysis"
                ),
            },
            quality_assessment={
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical significance is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "evidence_strength": {
                    "status": "partial",
                    "summary": "HDL/unit harmonization remains unresolved.",
                    "evidence_refs": [str(study_root / "analysis")],
                },
                "novelty_positioning": {
                    "status": "partial",
                    "summary": "Novelty depends on a valid unit-harmonized external validation.",
                    "evidence_refs": [str(study_root / "analysis")],
                },
                "human_review_readiness": {
                    "status": "partial",
                    "summary": "Human review must wait for analysis repair.",
                    "evidence_refs": [str(study_root / "paper")],
                },
                "medical_journal_prose_quality": {
                    "status": "partial",
                    "summary": "Prose cannot close until the methodologic blocker is repaired.",
                    "evidence_refs": [str(study_root / "paper")],
                },
            },
            expected_decision_type="bounded_analysis",
            expected_route_target="analysis-campaign",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="medical_prose_quality_analysis_source_documentation_repair",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="current_ai_reviewer_write_route_back_preempts_ai_reviewer_prose_recheck",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "bundle_tasks_downstream_only": True,
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["manuscript_voice_reporting_incomplete"],
                "blocking_artifact_refs": [{"source_path": "paper/manuscript.md"}],
            },
            publication_eval_action=_write_route_back_action(study_root),
            publication_eval_verdict="blocked",
            publication_supervisor_state={
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
                "bundle_tasks_downstream_only": True,
                "publication_gate_allows_direct_write": False,
            },
            quality_assessment={
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical significance is bounded by the current validation evidence.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence is sufficient for a clean external-validation manuscript.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Novelty positioning is clear.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "human_review_readiness": {
                    "status": "blocked",
                    "summary": "Human review must wait for manuscript story repair.",
                    "evidence_refs": [str(study_root / "paper" / "manuscript.md")],
                },
                "medical_journal_prose_quality": {
                    "status": "blocked",
                    "summary": "The current reviewer judgment routes prose repair to the write owner.",
                    "evidence_refs": [str(study_root / "paper" / "manuscript.md")],
                },
            },
            expected_decision_type="route_back_same_line",
            expected_route_target="write",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="manuscript_story_repair",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="domain_transition_gate_blocker_replays_gate_after_terminal_analysis_handoff",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "bundle_tasks_downstream_only": True,
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
            },
            publication_eval_action={
                "action_id": "action-stale-terminal-analysis",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Old terminal analysis repair should not be redriven without gate replay.",
                "route_target": "analysis-campaign",
                "route_key_question": "analysis_claim_evidence_repair",
                "route_rationale": "Old terminal repair route residue.",
                "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                "requires_controller_decision": True,
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence blockers.",
                },
            },
            publication_eval_verdict="blocked",
            publication_supervisor_state={
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
                "bundle_tasks_downstream_only": True,
                "publication_gate_allows_direct_write": False,
            },
            expected_decision_type="bounded_analysis",
            expected_route_target="review",
            expected_controller_action_type="run_gate_clearing_batch",
            expected_unit_id="publication_gate_replay",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="clear_bundle_stage_preempts_stale_write_task_intake",
            gate_report={
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "medical_publication_surface_status": "clear",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "current",
            },
            publication_eval_action=_finalize_review_only_action(study_root),
            publication_eval_verdict="promising",
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            task_intake_action=_stale_write_task_intake_action(),
            expected_decision_type="continue_same_line",
            expected_route_target="finalize",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="submission_authority_sync_closure",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="blocked_bundle_stage_preempts_stale_write_task_intake",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["stale_submission_minimal_authority"],
                "current_required_action": "complete_bundle_stage",
                "supervisor_phase": "bundle_stage_blocked",
                "study_delivery_status": "current",
                "submission_minimal_authority_status": "stale_source_changed",
                "submission_minimal_evaluated_source_signature": "source::new",
                "submission_minimal_authority_source_signature": "source::old",
            },
            publication_eval_action=_finalize_review_only_action(study_root),
            publication_eval_verdict="promising",
            publication_supervisor_state={
                "supervisor_phase": "bundle_stage_blocked",
                "current_required_action": "complete_bundle_stage",
                "publication_gate_allows_direct_write": False,
            },
            task_intake_action=_stale_write_task_intake_action(),
            expected_decision_type="continue_same_line",
            expected_route_target="finalize",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="submission_authority_sync_closure",
        ),
        lambda study_root: OuterLoopTransitionCase(
            case_id="publishability_gate_blocked_routes_analysis_repair_not_finalize",
            gate_report={
                "status": "blocked",
                "allow_write": False,
                "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
                "current_required_action": "return_to_publishability_gate",
                "supervisor_phase": "publishability_gate_blocked",
                "bundle_tasks_downstream_only": True,
                "medical_publication_surface_status": "blocked",
                "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
                "blocking_artifact_refs": [{"source_path": "paper/evidence_ledger.json"}],
            },
            publication_eval_action=_bounded_analysis_action(study_root),
            publication_eval_verdict="blocked",
            publication_supervisor_state={
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
                "bundle_tasks_downstream_only": True,
                "publication_gate_allows_direct_write": False,
            },
            expected_decision_type="bounded_analysis",
            expected_route_target="analysis-campaign",
            expected_controller_action_type="ensure_study_runtime",
            expected_unit_id="analysis_claim_evidence_repair",
        ),
    ),
    ids=lambda factory: factory(Path("/tmp/study")).case_id,
)
def test_runtime_watch_outer_loop_controller_transition_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case_factory,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    case = case_factory(study_root)
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _publication_eval_payload(
            study_root=study_root,
            quest_root=quest_root,
            action=case.publication_eval_action,
            verdict=case.publication_eval_verdict,
            assessment_provenance=case.assessment_provenance,
            quality_assessment=case.quality_assessment,
        ),
    )
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(_runtime_watch_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: dict(case.gate_report))
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "build_gate_clearing_batch_recommended_action",
        lambda **_: None,
    )
    monkeypatch.setattr(
        module.quality_repair_batch,
        "build_quality_repair_batch_recommended_action",
        lambda **_: None,
    )
    monkeypatch.setattr(_runtime_watch_tick_request_module(), "recommended_task_intake_action", lambda **_: case.task_intake_action)

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "mas-run-001",
            "reason": "quest_already_running",
            "publication_supervisor_state": case.publication_supervisor_state,
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == case.expected_decision_type
    assert request["route_target"] == case.expected_route_target
    assert request["controller_actions"][0]["action_type"] == case.expected_controller_action_type
    assert request["next_work_unit"]["unit_id"] == case.expected_unit_id


def test_domain_transition_arbitration_candidates_ai_reviewer_prose_quality_gap(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.domain_transition_arbitration"
    )
    status_module = importlib.import_module("med_autoscience.controllers.study_runtime_status_parts")
    study_root = tmp_path / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    _write_charter(study_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        _publication_eval_payload(
            study_root=study_root,
            quest_root=tmp_path / "runtime" / "quests" / "quest-001",
            action=_finalize_review_only_action(study_root),
            verdict="promising",
            quality_assessment={
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical significance is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence strength is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Novelty positioning is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human review readiness is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "AI reviewer has not yet closed medical-journal prose quality.",
                    "evidence_refs": [str(study_root / "paper")],
                },
            },
        ),
    )
    status = status_module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "runtime_backend": "mas_runtime_core",
                "decision_policy": "autonomous",
            },
            "quest_id": "quest-001",
            "quest_root": str(tmp_path / "runtime" / "quests" / "quest-001"),
            "quest_exists": True,
            "quest_status": "waiting_for_user",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "decision": "blocked",
            "reason": "quest_waiting_for_user",
            "publication_supervisor_state": {
            "supervisor_phase": "bundle_stage_ready",
            "current_required_action": "continue_bundle_stage",
            },
        }
    )

    module.record_domain_transition_if_required(status=status, study_root=study_root)

    transition = status.extras["domain_transition"]
    assert transition["decision_type"] == "ai_reviewer_re_eval"
    assert transition["route_target"] == "review"
    assert transition["controller_action"] == "return_to_ai_reviewer_workflow"
    assert transition["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"
