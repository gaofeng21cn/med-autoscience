from __future__ import annotations

from typing import Any


SCHEMA_VERSION = 1
AI_REVIEWER_PROVENANCE_REQUIREMENTS = {
    "assessment_provenance.owner": "ai_reviewer",
    "assessment_provenance.ai_reviewer_required": False,
    "assessment_provenance.policy_id": "medical_publication_critique_v1",
    "reviewer_operating_system.required": True,
}
MECHANICAL_INPUT_CONTRACT = {
    "role": "evidence_only",
    "can_authorize_readiness": False,
    "can_close_quality_gate": False,
    "can_replace_ai_reviewer_provenance": False,
}

CALIBRATION_CASES: tuple[dict[str, Any], ...] = (
    {
        "case_id": "mechanical_ready_without_ai_provenance",
        "failure_mode": "ready wording appeared from gate or coverage without AI reviewer ownership",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "reject ready state until publication_eval carries AI reviewer provenance and trace",
    },
    {
        "case_id": "thin_first_draft_despite_richer_data_asset",
        "failure_mode": "draft uses already-verified data only descriptively when stronger bounded analysis is supported",
        "expected_route": "return_to_analysis_campaign",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "route back for limited supplemental analysis before full manuscript drafting",
    },
    {
        "case_id": "coverage_complete_but_quality_unreviewed",
        "failure_mode": "coverage or paper contract health is treated as medical manuscript quality ready",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "preserve coverage as mechanical oracle and require MAS AI preflight",
    },
    {
        "case_id": "medical_prose_review_route_back",
        "failure_mode": "work-report prose or controller language remains in a manuscript-like draft",
        "expected_route": "return_to_write",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "AI prose review identifies section-level rewrite targets before finalize",
    },
    {
        "case_id": "claim_strength_exceeds_evidence",
        "failure_mode": "clinical or novelty claims exceed evidence ledger support",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "AI reviewer narrows claim or routes to bounded evidence repair",
    },
    {
        "case_id": "reviewer_trace_missing",
        "failure_mode": "AI reviewer gives a conclusion without structured rubric, provenance, or route-back trace",
        "expected_route": "return_to_ai_reviewer",
        "mechanical_facts_role": "evidence_only",
        "quality_gate_relaxation_allowed": False,
        "minimum_ai_reviewer_trace": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        "reviewer_expectation": "fail closed until reviewer_operating_system trace is complete",
    },
)


def build_ai_reviewer_calibration_corpus() -> dict[str, Any]:
    return {
        "surface": "ai_reviewer_calibration_corpus",
        "schema_version": SCHEMA_VERSION,
        "authority": {
            "owner": "MedAutoScience Quality OS",
            "mechanical_projection_can_close_case": False,
            "ai_reviewer_required_for_subjective_quality": True,
            "prompt_only_calibration_allowed": False,
            "ai_reviewer_provenance_requirements": AI_REVIEWER_PROVENANCE_REQUIREMENTS,
        },
        "cases": [dict(case) for case in CALIBRATION_CASES],
        "regression_axes": [
            "ai_reviewer_provenance",
            "pre_draft_quality",
            "coverage_as_mechanical_oracle",
            "medical_journal_prose",
            "claim_evidence_alignment",
            "reviewer_os_trace_completeness",
        ],
    }


def build_pre_draft_readiness_materialization_contract() -> dict[str, Any]:
    return {
        "surface": "pre_draft_readiness_materialization_contract",
        "schema_version": SCHEMA_VERSION,
        "stable_path": "paper/pre_draft_writing_readiness.json",
        "materializer_owner": "MedAutoScience Quality OS",
        "readiness_verdict_authority": {
            "required_owner": "ai_reviewer",
            "required_ai_reviewer_required": False,
            "required_policy_id": "medical_publication_critique_v1",
            "required_trace_surface": "reviewer_operating_system",
            "prompt_only_authority_allowed": False,
        },
        "ai_first_blocking_inputs": [
            "study_charter.paper_quality_contract",
            "paper/evidence_ledger.json",
            "paper/review_ledger.json",
            "paper/medical_manuscript_blueprint.json",
            "artifacts/publication_eval/latest.json",
        ],
        "mechanical_supporting_inputs": [
            "reporting_guideline_checklist.json",
            "claim_evidence_map",
            "artifact_inventory",
            "manuscript_section_inventory",
        ],
        "mechanical_supporting_input_contract": MECHANICAL_INPUT_CONTRACT,
        "required_decisions": [
            "clinical_question_ready",
            "evidence_strength_ready",
            "reporting_guideline_ready",
            "manuscript_shape_ready",
            "route_back_not_required",
        ],
        "fail_closed_without_ai_reviewer": True,
        "fail_closed_without_ai_reviewer_provenance": True,
        "fail_closed_statuses": ["review_required", "route_back_required"],
        "mechanical_inputs_authorize_quality": False,
        "mechanical_inputs_can_only_supply": "evidence_only",
        "forbidden_materialization_modes": [
            "prompt_only_readiness",
            "mechanical_ready_verdict",
            "coverage_complete_as_quality_ready",
            "claim_only_ready",
        ],
    }


def build_quality_regression_calibration_evidence_contract() -> dict[str, Any]:
    return {
        "surface": "quality_regression_calibration_evidence_contract",
        "owner": "MAS Evaluation OS",
        "judge_scores": {
            "accepted_sources": ["autorater", "side_by_side_judge"],
            "role": "calibration_evidence_only",
            "can_authorize_publication_quality": False,
            "can_replace_ai_reviewer": False,
        },
        "required_refs": [
            "draft_eval_ref",
            "revision_eval_ref",
            "final_package_eval_ref",
            "calibration_evidence_refs",
        ],
        "fail_closed_without_refs": True,
    }
