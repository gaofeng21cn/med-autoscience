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
    readiness_contract = draft_contract["pre_draft_writing_readiness_contract"]
    assert readiness_contract["surface"] == "pre_draft_writing_readiness_contract"
    assert readiness_contract["required_before"] == "first_full_draft"
    assert readiness_contract["gate_relaxation_allowed"] is False
    assert [item["readiness_id"] for item in readiness_contract["required_readiness_items"]] == [
        "clinical_question",
        "population_design_outcome",
        "display_to_claim_map",
        "claim_evidence_map",
        "section_purpose",
        "reader_flow_plan",
        "journal_voice",
        "ai_prose_review_feedback_loop",
    ]
    assert readiness_contract["quality_proxy_exclusion_policy"]["forbidden_quality_proxies"] == [
        "controller_checklist",
        "run_log_or_execution_transcript",
        "progress_prose",
        "generic_completion_checklist",
        "packaging_metadata",
    ]
    assert readiness_contract["stronger_paper_shape_route_back"]["default_route"] == (
        "bounded_analysis_or_analysis_campaign"
    )
    assert readiness_contract["stronger_paper_shape_route_back"]["forbidden_action"] == (
        "write_light_descriptive_first_draft"
    )
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


def test_quality_os_materializes_default_runtime_quality_flow_contract() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    contract = module.build_medical_quality_operating_system_contract(
        study_archetype="clinical_observation",
        manuscript_family="observational_study",
    )

    assert "quality_runtime_materialization" in contract["quality_contract"]
    runtime_contract = contract["quality_contract"]["quality_runtime_materialization"]
    assert runtime_contract == module.build_quality_os_runtime_materialization_contract()
    assert runtime_contract["surface"] == "quality_os_runtime_materialization_contract"
    assert runtime_contract["default_verdict_when_unclosed"] == "NEEDS_REVIEW"
    assert runtime_contract["mechanical_gate_output_contract"] == {
        "allowed_output_kinds": ["completeness", "evidence", "blocker", "projection"],
        "forbidden_output_kinds": ["ready_authorization", "quality_closure", "submission_authorization"],
        "mechanical_projection_can_authorize_ready": False,
    }

    write_gate = runtime_contract["default_flow"]["write"]
    assert write_gate["required_before"] == "first_full_draft"
    assert write_gate["required_runtime_surface"] == "paper/pre_draft_writing_readiness.json"
    assert write_gate["required_status"] == "closed"
    assert write_gate["must_read"] == [
        "study_charter.paper_quality_contract",
        "paper/evidence_ledger.json",
        "paper/review_ledger.json",
        "paper/medical_manuscript_blueprint.json",
        "artifacts/publication_eval/latest.json",
    ]
    assert write_gate["fail_closed_when_missing"] == "route_back_required"
    assert write_gate["ai_reviewer_provenance_required"] is True
    assert write_gate["mechanical_gate_can_authorize_ready"] is False

    revise_gate = runtime_contract["default_flow"]["revise"]
    assert revise_gate["required_runtime_surface"] == "paper/review_ledger.json"
    assert revise_gate["route_back_required"] is True
    assert revise_gate["route_back_trace_fields"] == [
        "finding_refs",
        "affected_claim_refs",
        "fix_refs",
        "acceptance_criteria",
        "next_route",
    ]
    assert revise_gate["fail_closed_when_route_back_missing"] == "review_ledger_route_back_required"

    finalize_gate = runtime_contract["default_flow"]["finalize"]
    submission_gate = runtime_contract["default_flow"]["submission"]
    for gate in (finalize_gate, submission_gate):
        assert gate["requires_ai_reviewer_provenance"] is True
        assert gate["required_provenance"] == {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        }
        assert gate["required_runtime_surfaces"] == [
            "artifacts/publication_eval/latest.json",
            "artifacts/publication_eval/medical_prose_review.json",
            "paper/review_ledger.json",
        ]
        assert gate["fail_closed_when_missing_provenance"] == "review_required"
        assert gate["mechanical_gate_can_authorize_ready"] is False

    assert runtime_contract["runtime_surfaces"] == {
        "pre_draft_readiness": "paper/pre_draft_writing_readiness.json",
        "ai_review_ledger": "paper/review_ledger.json",
        "publication_eval": "artifacts/publication_eval/latest.json",
        "medical_prose_review": "artifacts/publication_eval/medical_prose_review.json",
        "controller_decision": "artifacts/controller_decisions/latest.json",
    }


def test_quality_os_explains_automated_medical_paper_chain_without_lowering_authority() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    contract = module.build_medical_quality_operating_system_contract(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
    )

    automation_chain = contract["quality_contract"]["automated_medical_paper_chain"]
    assert automation_chain["claim"] == "medical_paper_as_governed_research_state_machine"
    assert automation_chain["text_is_projection_not_authority"] is True
    assert automation_chain["gate_relaxation_allowed"] is False
    assert [item["component_id"] for item in automation_chain["stable_components"]] == [
        "mas_owner_truth",
        "mds_controlled_backend",
        "durable_evidence_truth",
        "ai_reviewer_quality_authority",
        "canonical_source_first_artifact_authority",
    ]
    assert automation_chain["stable_components"][0]["authority_surface"] == (
        "study_charter.paper_quality_contract"
    )
    assert automation_chain["stable_components"][1]["authority_role"] == (
        "controlled_backend_oracle_intake_buffer"
    )
    assert automation_chain["stable_components"][2]["authority_surfaces"] == [
        "paper/evidence_ledger.json",
        "paper/review_ledger.json",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ]
    assert automation_chain["stable_components"][3]["required_provenance"] == {
        "assessment_owner": "ai_reviewer",
        "policy_id": "medical_publication_critique_v1",
        "ai_reviewer_required": False,
    }
    assert automation_chain["stable_components"][4]["derived_surfaces_not_authority"] == [
        "manuscript/current_package/",
        "submission_minimal/",
        "artifacts/final/",
    ]
    assert automation_chain["upstream_judgment_gap"] == {
        "problem": "research_creativity_and_route_choice_are_less_stable_than_governance",
        "must_strengthen": [
            "literature_understanding",
            "study_line_selection",
            "analysis_design_discipline",
            "stop_loss_reasoning",
            "target_journal_writing_fit",
        ],
    }


def test_quality_os_includes_archetype_specific_analysis_discipline() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    contract = module.build_medical_quality_operating_system_contract(
        study_archetype="clinical_subtype_reconstruction",
        manuscript_family="observational_study",
    )

    analysis_contract = contract["quality_contract"]["archetype_analysis_contract"]
    assert analysis_contract["surface"] == "archetype_specific_analysis_contract"
    assert analysis_contract["required_before"] == "analysis-campaign"
    assert analysis_contract["gate_relaxation_allowed"] is False
    assert analysis_contract["analysis_is_not_work_volume"] == (
        "each analysis must close a claim, reviewer concern, or publication gate blocker"
    )
    assert [item["discipline_id"] for item in analysis_contract["statistical_disciplines"]] == [
        "missingness",
        "sample_size_precision",
        "external_validation",
        "subgroup_analysis",
        "multiplicity",
        "clinical_utility",
        "endpoint_time_window",
        "sensitivity_robustness",
    ]
    missingness = analysis_contract["statistical_disciplines"][0]
    assert missingness["why"] == (
        "missingness changes the analyzed population and can reverse bias direction"
    )
    assert missingness["required_record"] == [
        "missingness_mechanism_assumption",
        "handling_method",
        "complete_case_or_imputation_rationale",
        "sensitivity_analysis",
    ]
    clinical_utility = next(
        item
        for item in analysis_contract["statistical_disciplines"]
        if item["discipline_id"] == "clinical_utility"
    )
    assert "AUC_or_p_value_alone_is_not_clinical_value" in clinical_utility["forbidden_shortcuts"]
    assert "decision_curve_or_threshold_net_benefit" in clinical_utility["required_record"]
    assert analysis_contract["archetype_requirements"]["clinical_subtype_reconstruction"] == [
        "subtype_stability",
        "between_subtype_clinical_difference",
        "prognosis_or_treatment_response_contrast",
        "subtype_identifier",
        "clinical_interpretability",
    ]


def test_quality_os_bounded_analysis_requires_candidate_board_and_stop_loss_memo() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    contract = module.build_medical_quality_operating_system_contract(
        study_archetype="gray_zone_triage",
        manuscript_family="observational_study",
    )

    bounded = contract["quality_contract"]["bounded_analysis_decision_contract"]
    assert bounded["surface"] == "bounded_analysis_decision_contract"
    assert bounded["route_meanings"] == ["explore", "exploit", "fusion", "debug", "stop"]
    assert bounded["candidate_board_required_fields"] == [
        "candidate_id",
        "route_meaning",
        "target_claim_or_concern",
        "expected_evidence_gain",
        "cost_and_risk",
        "clinical_interpretability",
        "decision",
        "decision_reason",
    ]
    assert bounded["plateau_stop_triggers"] == [
        "new_analysis_repeats_existing_result",
        "evidence_gain_cannot_close_claim_or_reviewer_concern",
        "analysis_would_break_study_charter_or_data_permission",
        "claim_requires_post_hoc_storytelling",
    ]
    assert bounded["stop_loss_memo"]["required_when"] == [
        "publication_eval_overall_verdict_weak_or_blocked",
        "stop_loss_pressure_high",
        "bounded_analysis_plateau",
    ]
    assert bounded["stop_loss_memo"]["required_fields"] == [
        "attempted_paths",
        "failure_reason",
        "evidence_gain_ceiling",
        "continuation_cost_and_risk",
        "alternative_routes",
        "human_gate_question",
    ]
