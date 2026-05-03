from __future__ import annotations

import importlib

import pytest


pytestmark = pytest.mark.meta


def test_calibration_corpus_turns_repair_toil_into_ai_reviewer_regressions() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_calibration")

    corpus = module.build_ai_reviewer_calibration_corpus()

    assert corpus["surface"] == "ai_reviewer_calibration_corpus"
    assert corpus["authority"] == {
        "owner": "MedAutoScience Quality OS",
        "mechanical_projection_can_close_case": False,
        "ai_reviewer_required_for_subjective_quality": True,
        "prompt_only_calibration_allowed": False,
        "ai_reviewer_provenance_requirements": {
            "assessment_provenance.owner": "ai_reviewer",
            "assessment_provenance.ai_reviewer_required": False,
            "assessment_provenance.policy_id": "medical_publication_critique_v1",
            "reviewer_operating_system.required": True,
        },
    }
    assert {case["case_id"] for case in corpus["cases"]} == {
        "mechanical_ready_without_ai_provenance",
        "thin_first_draft_despite_richer_data_asset",
        "coverage_complete_but_quality_unreviewed",
        "medical_prose_review_route_back",
        "claim_strength_exceeds_evidence",
        "reviewer_trace_missing",
        "thin_first_draft",
        "overstrong_claim",
        "missing_reviewer_trace",
        "coverage_as_quality",
        "mechanical_gate_as_quality",
    }
    for case in corpus["cases"]:
        assert case["expected_route"] in {"return_to_ai_reviewer", "return_to_analysis_campaign", "return_to_write"}
        assert case["quality_gate_relaxation_allowed"] is False
        assert case["mechanical_facts_role"] == "evidence_only"
        assert case["minimum_ai_reviewer_trace"] == corpus["authority"]["ai_reviewer_provenance_requirements"]


def test_calibration_corpus_exposes_required_case_families_and_soak_matrix() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_calibration")

    corpus = module.build_ai_reviewer_calibration_corpus()

    cases = {case["case_id"]: case for case in corpus["cases"]}
    for required_case_id in (
        "thin_first_draft",
        "overstrong_claim",
        "missing_reviewer_trace",
        "coverage_as_quality",
        "mechanical_gate_as_quality",
    ):
        case = cases[required_case_id]
        assert case["mechanical_facts_role"] == "evidence_only"
        assert case["quality_gate_relaxation_allowed"] is False
        assert case["minimum_ai_reviewer_trace"] == corpus["authority"]["ai_reviewer_provenance_requirements"]

    assert corpus["soak_matrix"] == {
        "surface": "real_study_soak_matrix",
        "role": "quality_regression_and_route_back_proof",
        "mechanical_projection_can_authorize_quality": False,
        "required_stages": [
            "literature_scout",
            "line_selection",
            "main_analysis",
            "bounded_analysis",
            "route_back",
            "stop_loss",
            "revision_reopen",
            "runtime_recovery",
            "finalize_rebuild",
            "final_pre_submission_audit",
        ],
        "stage_evidence_contract": {
            "requires_ai_reviewer_provenance_for_quality": True,
            "requires_route_back_trace": True,
            "requires_quality_regression_projection": True,
            "mechanical_gate_role": "evidence_only",
        },
    }


def test_pre_draft_readiness_materializer_requires_ai_authorized_inputs() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_calibration")

    readiness = module.build_pre_draft_readiness_materialization_contract()

    assert readiness["surface"] == "pre_draft_readiness_materialization_contract"
    assert readiness["stable_path"] == "paper/pre_draft_writing_readiness.json"
    assert readiness["materializer_owner"] == "MedAutoScience Quality OS"
    assert readiness["readiness_verdict_authority"] == {
        "required_owner": "ai_reviewer",
        "required_ai_reviewer_required": False,
        "required_policy_id": "medical_publication_critique_v1",
        "required_trace_surface": "reviewer_operating_system",
        "prompt_only_authority_allowed": False,
    }
    assert readiness["ai_first_blocking_inputs"] == [
        "study_charter.paper_quality_contract",
        "paper/evidence_ledger.json",
        "paper/review_ledger.json",
        "paper/medical_manuscript_blueprint.json",
        "artifacts/publication_eval/latest.json",
    ]
    assert readiness["fail_closed_without_ai_reviewer"] is True
    assert readiness["fail_closed_without_ai_reviewer_provenance"] is True
    assert readiness["fail_closed_statuses"] == ["review_required", "route_back_required"]
    assert readiness["mechanical_inputs_authorize_quality"] is False
    assert readiness["mechanical_inputs_can_only_supply"] == "evidence_only"
    assert readiness["mechanical_supporting_input_contract"] == {
        "role": "evidence_only",
        "can_authorize_readiness": False,
        "can_close_quality_gate": False,
        "can_replace_ai_reviewer_provenance": False,
    }
    assert readiness["forbidden_materialization_modes"] == [
        "prompt_only_readiness",
        "mechanical_ready_verdict",
        "coverage_complete_as_quality_ready",
        "claim_only_ready",
    ]


def test_quality_regression_calibration_evidence_contract_keeps_judge_scores_non_authoritative() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_calibration")

    contract = module.build_quality_regression_calibration_evidence_contract()

    assert contract["surface"] == "quality_regression_calibration_evidence_contract"
    assert contract["owner"] == "MAS Evaluation OS"
    assert contract["judge_scores"] == {
        "accepted_sources": ["autorater", "side_by_side_judge"],
        "role": "calibration_evidence_only",
        "can_authorize_publication_quality": False,
        "can_replace_ai_reviewer": False,
    }
    assert contract["required_refs"] == [
        "draft_eval_ref",
        "revision_eval_ref",
        "final_package_eval_ref",
        "calibration_evidence_refs",
    ]
    assert contract["fail_closed_without_refs"] is True


def test_ai_first_drift_audit_tracks_calibration_corpus() -> None:
    module = importlib.import_module("med_autoscience.ai_first_drift_audit")

    result = module.run_ai_first_drift_audit()

    assert result["status"] == "pass"
    assert "ai_reviewer_calibration_corpus_freezes_repair_toil_regressions" not in result["summary"][
        "failed_check_ids"
    ]
