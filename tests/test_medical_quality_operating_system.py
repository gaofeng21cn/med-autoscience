from __future__ import annotations

import importlib


def test_quality_os_selects_strobe_with_record_overlay_for_real_world_observation() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    contract = module.build_medical_quality_operating_system_contract(
        study_archetype="real_world_data",
        manuscript_family="clinical_observation",
    )

    assert contract["surface"] == "medical_quality_operating_system_contract"
    assert contract["guideline_selection"]["primary_guideline_family"] == "STROBE"
    assert contract["guideline_selection"]["overlay_guideline_families"] == ["RECORD"]
    assert contract["quality_contract"]["owner_surface"] == "study_charter.paper_quality_contract"
    assert contract["quality_contract"]["authority_surfaces"] == {
        "study_charter_owner": "study_charter.paper_quality_contract",
        "evidence_ledger": "paper/evidence_ledger.json",
        "review_ledger": "paper/review_ledger.json",
        "medical_manuscript_blueprint": "paper/medical_manuscript_blueprint.json",
        "medical_prose_review": "artifacts/publication_eval/medical_prose_review.json",
        "publication_eval": "artifacts/publication_eval/latest.json",
        "reporting_guideline_checklist": "reporting_guideline_checklist.json",
    }
    assert contract["quality_contract"]["first_draft_quality_floor"]["required_before"] == (
        "first_full_draft"
    )
    draft_contract = contract["quality_contract"]["first_draft_manuscript_quality_contract"]
    assert draft_contract["guideline_family"] == "STROBE"
    assert draft_contract["required_before"] == "first_full_draft"
    assert "Introduction" in draft_contract["core_structure"]["article_body"]
    assert "author_confirmation_placeholder" in draft_contract["manuscript_native_prose"]["forbidden_modes"]
    prose_contract = draft_contract["medical_prose_style_contract"]
    assert prose_contract["style_profile_id"] == "general_medical_journal_prose_v1"
    assert prose_contract["target_voice"] == "neutral_clinical_original_research"
    assert "clinician_researcher" in prose_contract["target_readers"]
    assert "clinical_problem_to_evidence_gap_to_objective" in prose_contract["introduction_rhetoric"]["paragraph_sequence"]
    assert "old_to_new_information_flow" in prose_contract["sentence_information_flow"]["required_patterns"]
    assert "clinical_finding_as_sentence_subject" in prose_contract["results_prose"]["required_patterns"]
    assert "figure_or_table_as_sentence_subject" in prose_contract["results_prose"]["forbidden_patterns"]
    assert "principal_finding_then_prior_work_then_interpretation_then_limitations" in prose_contract["discussion_prose"]["paragraph_sequence"]
    assert "unsupported_no_difference_or_no_association" in prose_contract["forbidden_scientific_style"]
    blueprint_contract = draft_contract["medical_manuscript_blueprint_contract"]
    assert blueprint_contract["surface"] == "medical_manuscript_blueprint"
    assert blueprint_contract["required_before"] == "first_full_draft"
    assert "clinical_problem" in blueprint_contract["required_fields"]
    assert "paper/claim_evidence_map.json" in blueprint_contract["required_source_surfaces"]
    assert "display_to_claim_map" in draft_contract["first_draft_generation_model"]["pre_draft_inputs"]
    assert "medical_manuscript_blueprint" in draft_contract["first_draft_generation_model"]["pre_draft_inputs"]
    assert "medical_prose_style_contract" in draft_contract["first_draft_generation_model"]["pre_draft_inputs"]
    assert "medical_prose_review" in draft_contract["first_draft_generation_model"]["pre_draft_inputs"]
    prose_review_contract = draft_contract["medical_prose_review_contract"]
    assert prose_review_contract["owner"] == "ai_reviewer"
    assert prose_review_contract["mechanical_projection_can_authorize_quality"] is False
    assert "paper/results_narrative_map.json" in draft_contract["must_bind_existing_surfaces"]
    assert contract["quality_contract"]["stronger_paper_shape_scan"]["status"] == (
        "required_before_first_full_draft"
    )
    assert contract["quality_contract"]["completion_claim_policy"][
        "mechanical_repair_complete_equals_scientific_quality_complete"
    ] is False
    assert contract["quality_contract"]["publication_eval"][
        "must_be_ai_reviewer_backed_for_quality_closure"
    ] is True
    reviewer_os = contract["quality_contract"]["ai_reviewer_operating_system"]
    assert reviewer_os["contract_id"] == "medical_publication_ai_reviewer_os_v1"
    assert reviewer_os["owner"] == "ai_reviewer"
    assert reviewer_os["mechanical_projection_can_authorize_quality"] is False
    assert "manuscript" in reviewer_os["required_input_surfaces"]
    assert "evidence_ledger" in reviewer_os["required_input_surfaces"]
    assert "medical_journal_prose_quality" in reviewer_os["rubric_dimensions"]
    assert "decision_matrix" in reviewer_os["required_trace_fields"]
    assert reviewer_os["required_provenance"] == {
        "assessment_owner": "ai_reviewer",
        "policy_id": "medical_publication_critique_v1",
        "ai_reviewer_required": False,
    }


def test_quality_os_selects_ai_guidelines_without_record_overlay_when_not_rwd() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    prediction_contract = module.build_medical_quality_operating_system_contract(
        study_archetype="clinical_classifier",
        manuscript_family="ai_prediction_model",
    )
    trial_contract = module.build_medical_quality_operating_system_contract(
        study_archetype="randomized_trial",
        manuscript_family="ai_trial",
    )

    assert prediction_contract["guideline_selection"]["primary_guideline_family"] == "TRIPOD+AI"
    assert prediction_contract["guideline_selection"]["overlay_guideline_families"] == []
    prediction_draft_contract = prediction_contract["quality_contract"]["first_draft_manuscript_quality_contract"]
    assert prediction_draft_contract["guideline_family"] == "TRIPOD+AI"
    assert any(
        "AI preprocessing" in item
        for item in prediction_draft_contract["guideline_specific_obligations"]
    )
    assert trial_contract["guideline_selection"]["primary_guideline_family"] == "CONSORT-AI"
    assert trial_contract["guideline_selection"]["overlay_guideline_families"] == []


def test_quality_os_selects_expected_non_ai_guideline_families() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    assert module.select_reporting_guideline_families(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
    ) == {
        "primary_guideline_family": "TRIPOD",
        "overlay_guideline_families": [],
    }
    assert module.select_reporting_guideline_families(
        study_archetype="randomized_trial",
        manuscript_family="randomized_trial",
    )["primary_guideline_family"] == "CONSORT"
    assert module.select_reporting_guideline_families(
        study_archetype="systematic_review",
        manuscript_family="systematic_review",
    )["primary_guideline_family"] == "PRISMA"


def test_quality_os_blocks_claim_only_ready_and_fast_lane_gate_relaxation() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    contract = module.build_medical_quality_operating_system_contract(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
    )
    evidence_gate = contract["quality_contract"]["evidence_over_claims_gate"]
    fast_lane = contract["quality_contract"]["quality_preserving_fast_lane_policy"]

    assert evidence_gate["policy_id"] == "mas_evidence_over_claims_v1"
    assert evidence_gate["claim_only_ready_allowed"] is False
    assert evidence_gate["ready_verbs_require_authority_refs"] is True
    assert "paper/evidence_ledger.json" in evidence_gate["required_refs"]
    assert "paper/review_ledger.json" in evidence_gate["required_refs"]
    assert "artifacts/publication_eval/latest.json" in evidence_gate["required_refs"]
    assert evidence_gate["ai_reviewer_publication_eval"]["required_for"] == [
        "reviewer_first_ready",
        "finalize_ready",
        "submission_facing_quality_closure",
    ]
    assert evidence_gate["ai_reviewer_publication_eval"][
        "mechanical_projection_can_authorize_quality"
    ] is False
    assert evidence_gate["ai_reviewer_publication_eval"][
        "reviewer_operating_system_contract"
    ] == "medical_publication_ai_reviewer_os_v1"
    assert "generic_persona_approval" in evidence_gate["forbidden_authority_sources"]
    assert fast_lane["gate_relaxation_allowed"] is False
    assert "bounded_analysis_unit" in fast_lane["allowed_parallelism"]
    assert "skip_publication_eval" in fast_lane["forbidden_shortcuts"]
    assert "claim_only_ready" in fast_lane["forbidden_shortcuts"]
