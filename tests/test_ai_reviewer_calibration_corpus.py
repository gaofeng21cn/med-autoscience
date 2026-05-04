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
        "claim_overreach",
        "missing_reviewer_trace",
        "coverage_as_quality",
        "mechanical_gate_as_quality",
        "weak_external_validation",
        "statistical_discipline_waiver_misuse",
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
        "claim_overreach",
        "missing_reviewer_trace",
        "coverage_as_quality",
        "mechanical_gate_as_quality",
        "weak_external_validation",
        "statistical_discipline_waiver_misuse",
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


def test_calibration_learning_read_model_appends_real_reviewer_outcomes() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_calibration")

    existing_payload = {
        "surface": "ai_reviewer_calibration_learning_read_model",
        "learning_entries": [
            {
                "entry_id": "learn::major-revision::claim",
                "source_outcome": "major_revision",
                "failure_mode": "claim_overreach",
                "source_ref": "reviews/round-1.md#r1-c1",
                "issue_summary": "Primary clinical claim exceeded the evidence ledger.",
                "claim_refs": ["paper/claim_evidence_map.json#claim-primary"],
                "evidence_refs": ["paper/evidence_ledger.json#claim-primary"],
                "reviewer_trace_refs": ["paper/review/review_ledger.json#r1-c1"],
            },
            {
                "entry_id": "learn::reject::coverage",
                "source_outcome": "rejection",
                "failure_mode": "coverage_as_quality",
                "source_ref": "reviews/reject.md#editor",
                "issue_summary": "Checklist completion was mistaken for publishable manuscript quality.",
                "claim_refs": [],
                "evidence_refs": ["paper/reporting_guideline_checklist.json"],
                "reviewer_trace_refs": ["paper/review/review_ledger.json#editor"],
            },
            {
                "entry_id": "learn::revision::mechanical",
                "source_outcome": "reviewer_revision",
                "failure_mode": "mechanical_gate_misuse",
                "source_ref": "reviews/round-2.md#gate",
                "issue_summary": "A controller gate was used as the quality decision.",
                "claim_refs": [],
                "evidence_refs": ["artifacts/publication_eval/latest.json"],
                "reviewer_trace_refs": ["paper/review/review_ledger.json#gate"],
            },
        ],
    }
    projection = module.append_ai_reviewer_calibration_learning_entry(
        existing_payload=existing_payload,
        learning_entry={
            "entry_id": "learn::revision::missing-trace",
            "source_outcome": "major_revision",
            "failure_mode": "missing_reviewer_trace",
            "source_ref": "reviews/round-2.md#trace",
            "issue_summary": "The revision lacked traceable AI reviewer concern provenance.",
            "claim_refs": ["paper/claim_evidence_map.json#claim-secondary"],
            "evidence_refs": ["paper/evidence_ledger.json#claim-secondary"],
            "reviewer_trace_refs": ["paper/review/review_ledger.json#trace"],
        },
    )

    assert projection["surface"] == "ai_reviewer_calibration_learning_read_model"
    assert projection["schema_version"] == 1
    assert projection["supported_outcomes"] == [
        "major_revision",
        "reject",
        "accept",
        "editorial_desk_reject",
        "post_review_repair",
    ]
    assert [entry["failure_mode"] for entry in projection["learning_entries"]] == [
        "claim_overreach",
        "coverage_as_quality",
        "mechanical_gate_misuse",
        "missing_reviewer_trace",
    ]
    assert [entry["source_outcome"] for entry in projection["learning_entries"]] == [
        "major_revision",
        "reject",
        "post_review_repair",
        "major_revision",
    ]
    assert projection["required_failure_modes"] == [
        "claim_overreach",
        "coverage_as_quality",
        "mechanical_gate_misuse",
        "missing_reviewer_trace",
    ]
    assert projection["required_calibration_refs"] == [
        "ai_reviewer_calibration_corpus#claim_overreach",
        "ai_reviewer_calibration_corpus#coverage_as_quality",
        "ai_reviewer_calibration_corpus#mechanical_gate_as_quality",
        "ai_reviewer_calibration_corpus#missing_reviewer_trace",
    ]
    assert projection["failure_mode_counts"] == {
        "claim_overreach": 1,
        "coverage_as_quality": 1,
        "mechanical_gate_misuse": 1,
        "missing_reviewer_trace": 1,
    }
    assert projection["outcome_counts"] == {
        "major_revision": 2,
        "post_review_repair": 1,
        "reject": 1,
    }
    assert projection["failure_mode_projection"] == [
        {
            "failure_mode": "claim_overreach",
            "count": 1,
            "calibration_ref": "ai_reviewer_calibration_corpus#claim_overreach",
            "source_outcomes": ["major_revision"],
        },
        {
            "failure_mode": "coverage_as_quality",
            "count": 1,
            "calibration_ref": "ai_reviewer_calibration_corpus#coverage_as_quality",
            "source_outcomes": ["reject"],
        },
        {
            "failure_mode": "mechanical_gate_misuse",
            "count": 1,
            "calibration_ref": "ai_reviewer_calibration_corpus#mechanical_gate_as_quality",
            "source_outcomes": ["post_review_repair"],
        },
        {
            "failure_mode": "missing_reviewer_trace",
            "count": 1,
            "calibration_ref": "ai_reviewer_calibration_corpus#missing_reviewer_trace",
            "source_outcomes": ["major_revision"],
        },
    ]
    assert projection["authority_contract"] == {
        "read_model_only": True,
        "outcome_intake_can_authorize_quality": False,
        "outcome_intake_can_authorize_drafting": False,
        "learning_can_authorize_quality": False,
        "learning_can_authorize_drafting": False,
        "learning_can_authorize_submission": False,
        "learning_can_authorize_finalize": False,
        "required_calibration_refs_can_authorize_quality": False,
    }


def test_outcome_intake_appends_canonical_outcomes_and_required_regression_refs() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_calibration")

    payload: dict[str, object] = {}
    for outcome_type, failure_mode in (
        ("major_revision", "claim_overreach"),
        ("reject", "missing_reviewer_trace"),
        ("accept", "coverage_as_quality"),
        ("editorial_desk_reject", "weak_external_validation"),
        ("post_review_repair", "statistical_discipline_waiver_misuse"),
    ):
        payload = module.append_ai_reviewer_calibration_outcome_intake(
            existing_payload=payload,
            outcome_intake={
                "outcome_id": f"outcome::{outcome_type}",
                "outcome_type": outcome_type,
                "failure_mode": failure_mode,
                "outcome_ref": f"reviews/{outcome_type}.json",
                "outcome_summary": f"{outcome_type} exposed {failure_mode}.",
                "claim_refs": ["paper/claim_evidence_map.json#claim-primary"],
                "evidence_refs": ["paper/evidence_ledger.json#claim-primary"],
                "reviewer_trace_refs": ["paper/review/review_ledger.json#claim-primary"],
            },
        )

    assert payload["outcome_counts"] == {
        "accept": 1,
        "editorial_desk_reject": 1,
        "major_revision": 1,
        "post_review_repair": 1,
        "reject": 1,
    }
    assert payload["required_failure_modes"] == [
        "claim_overreach",
        "missing_reviewer_trace",
        "coverage_as_quality",
        "weak_external_validation",
        "statistical_discipline_waiver_misuse",
    ]
    assert payload["required_calibration_refs"] == [
        "ai_reviewer_calibration_corpus#claim_overreach",
        "ai_reviewer_calibration_corpus#missing_reviewer_trace",
        "ai_reviewer_calibration_corpus#coverage_as_quality",
        "ai_reviewer_calibration_corpus#weak_external_validation",
        "ai_reviewer_calibration_corpus#statistical_discipline_waiver_misuse",
    ]
    assert payload["authority_contract"]["outcome_intake_can_authorize_quality"] is False
    assert payload["authority_contract"]["learning_can_authorize_drafting"] is False
    regression = payload["outcome_learning_regression"]
    assert regression["surface"] == "ai_reviewer_outcome_learning_regression"
    assert regression["status"] == "ready"
    assert regression["planning_mode"] == "calibration_regression_ready_for_authoring_review"
    assert regression["missing_required_failure_modes"] == []
    assert regression["required_calibration_refs"] == payload["required_calibration_refs"]
    assert regression["full_drafting_allowed_without_required_refs"] is False
    assert regression["repair_planning_allowed"] is True
    assert regression["pre_draft_planning_allowed"] is True
    assert regression["authority_contract"] == {
        "read_model_only": True,
        "can_authorize_quality": False,
        "can_authorize_drafting": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def test_outcome_learning_regression_blocks_without_real_outcome_refs() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_calibration")

    regression = module.build_outcome_learning_calibration_regression()

    assert regression["surface"] == "ai_reviewer_outcome_learning_regression"
    assert regression["status"] == "blocked"
    assert regression["planning_mode"] == "pre_draft_planning_only"
    assert regression["required_calibration_refs"] == []
    assert regression["missing_required_failure_modes"] == [
        "claim_overreach",
        "missing_reviewer_trace",
        "coverage_as_quality",
        "weak_external_validation",
        "statistical_discipline_waiver_misuse",
    ]
    assert regression["full_drafting_allowed_without_required_refs"] is False
    assert regression["repair_planning_allowed"] is False
    assert regression["pre_draft_planning_allowed"] is True


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
