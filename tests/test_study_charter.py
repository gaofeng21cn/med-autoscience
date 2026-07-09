from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


MODULE_NAME = "med_autoscience.study_charter"
def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_resolve_study_charter_ref_defaults_to_controller_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_study_charter_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "controller" / "study_charter.json").resolve()


def test_read_study_charter_reads_stable_controller_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    _write_json(
        charter_path,
        {
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
    )

    payload = module.read_study_charter(study_root=study_root)

    assert payload == {
        "charter_id": "charter::001-risk::v1",
        "publication_objective": "risk stratification external validation",
    }


def test_resolve_study_charter_ref_rejects_runtime_backflow_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    runtime_ref = study_root / "runtime" / "quests" / "001-risk" / "quest.yaml"

    with pytest.raises(ValueError, match="stable controller artifact"):
        module.resolve_study_charter_ref(study_root=study_root, ref=runtime_ref)


def test_resolve_study_charter_ref_rejects_status_root_pollution_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    status_ref = study_root / "artifacts" / "status" / "study_charter.json"

    with pytest.raises(ValueError, match="stable controller artifact"):
        module.resolve_study_charter_ref(study_root=study_root, ref=status_ref)


def test_resolve_study_charter_ref_rejects_cross_repo_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "repo-a" / "studies" / "001-risk"
    cross_repo_ref = tmp_path / "repo-b" / "studies" / "001-risk" / "artifacts" / "controller" / "study_charter.json"

    with pytest.raises(ValueError, match="stable controller artifact"):
        module.resolve_study_charter_ref(study_root=study_root, ref=cross_repo_ref)


def test_read_study_charter_rejects_non_object_payload(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    _write_json(charter_path, ["not", "an", "object"])

    with pytest.raises(ValueError, match="JSON object"):
        module.read_study_charter(study_root=study_root)


def test_materialize_study_charter_writes_stable_controller_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    written_ref = module.materialize_study_charter(
        study_root=study_root,
        study_id="001-risk",
        study_payload={
            "title": "Diabetes mortality risk paper",
            "primary_question": "Build a submission-ready survival-risk study.",
            "paper_framing_summary": "Clinical survival framing is fixed around CVD-related mortality.",
            "journal_shortlist": ["The BMJ", "JAMA Internal Medicine"],
            "minimum_sci_ready_evidence_package": ["external_validation", "decision_curve_analysis"],
            "scientific_followup_questions": [
                "Why is the 5-year all-cause mortality gap between China and the US so large?",
            ],
            "explanation_targets": [
                "Separate endpoint-alignment gap from case-mix shift and residual unexplained gap.",
            ],
            "manuscript_conclusion_redlines": [
                "Do not conclude only that a China-trained absolute risk model is non-transportable.",
            ],
            "bounded_analysis": {
                "allowed_scenarios": [
                    "close_survival_calibration_gap_within_locked_direction",
                    "answer_predeclared_reviewer_method_question",
                ],
                "allowed_targets": [
                    "minimum_sci_ready_evidence_package",
                    "scientific_followup_questions",
                ],
                "budget_boundary": {
                    "max_analysis_rounds_per_gate_window": 3,
                    "max_targets_per_round": 2,
                    "max_new_primary_claims": 0,
                },
                "completion_boundary": {
                    "return_to_main_gate": "publication_eval",
                    "return_to_mainline_action": "return_to_controller",
                    "completion_criteria": [
                        "all_requested_targets_closed",
                        "budget_boundary_reached",
                        "major_boundary_signal_detected",
                    ],
                    "required_updates": [
                        "evidence_ledger",
                        "review_ledger",
                        "publication_eval",
                    ],
                },
            },
        },
        execution={
            "decision_policy": "autonomous",
            "launch_profile": "continue_existing_state",
        },
        required_first_anchor="write",
    )

    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    payload = json.loads(charter_path.read_text(encoding="utf-8"))

    assert written_ref == {
        "charter_id": "charter::001-risk::v1",
        "artifact_path": str(charter_path.resolve()),
    }
    assert payload["schema_version"] == 1
    assert payload["charter_id"] == "charter::001-risk::v1"
    assert payload["study_id"] == "001-risk"
    assert payload["title"] == "Diabetes mortality risk paper"
    assert payload["publication_objective"] == "Build a submission-ready survival-risk study."
    assert payload["paper_framing_summary"] == "Clinical survival framing is fixed around CVD-related mortality."
    assert payload["minimum_sci_ready_evidence_package"] == ["external_validation", "decision_curve_analysis"]
    assert payload["scientific_followup_questions"] == [
        "Why is the 5-year all-cause mortality gap between China and the US so large?",
    ]
    assert payload["explanation_targets"] == [
        "Separate endpoint-alignment gap from case-mix shift and residual unexplained gap.",
    ]
    assert payload["manuscript_conclusion_redlines"] == [
        "Do not conclude only that a China-trained absolute risk model is non-transportable.",
    ]
    assert payload["autonomy_envelope"] == {
        "decision_policy": "autonomous",
        "launch_profile": "continue_existing_state",
        "required_first_anchor": "write",
        "direction_lock_state": "startup_frozen",
        "autonomous_scientific_decision_scope": {
            "phase": "post_direction_lock",
            "default_owner": "mas",
            "covered_decisions": [
                "analysis_plan_within_locked_direction",
                "evidence_generation_and_sufficiency_judgment",
                "manuscript_argumentation_and_revision",
                "journal_target_tradeoffs_within_frozen_quality_contract",
            ],
        },
        "human_gate_boundary": {
            "policy": "major_boundary_only",
            "required_human_decisions": [
                "direction_reset_or_primary_question_change",
                "major_claim_boundary_expansion",
                "external_release_or_submission_authorization",
            ],
        },
        "final_scientific_audit_boundary": {
            "audit_surfaces": ["evidence_ledger", "review_ledger", "final_audit"],
            "required_checks": [
                "claim_traceability_to_evidence_ledger",
                "review_closure_against_review_ledger",
                "submission_readiness_against_paper_quality_contract",
            ],
        },
    }
    paper_quality_contract = payload["paper_quality_contract"]
    assert paper_quality_contract["frozen_at_startup"] is True
    assert paper_quality_contract["target_journals"] == ["The BMJ", "JAMA Internal Medicine"]
    assert paper_quality_contract["reporting_expectations"] == {
        "paper_framing_summary": "Clinical survival framing is fixed around CVD-related mortality.",
        "explanation_targets": [
            "Separate endpoint-alignment gap from case-mix shift and residual unexplained gap.",
        ],
    }
    assert paper_quality_contract["evidence_expectations"] == {
        "minimum_sci_ready_evidence_package": ["external_validation", "decision_curve_analysis"],
    }
    assert paper_quality_contract["review_expectations"] == {
        "scientific_followup_questions": [
            "Why is the 5-year all-cause mortality gap between China and the US so large?",
        ],
        "manuscript_conclusion_redlines": [
            "Do not conclude only that a China-trained absolute risk model is non-transportable.",
        ],
    }

    assert paper_quality_contract["protocol_sap_freeze"]["status"] == "requires_freeze_before_analysis"
    bounded_analysis = paper_quality_contract["bounded_analysis"]
    assert bounded_analysis["default_owner"] == "mas"
    assert bounded_analysis["allowed_scenarios"] == [
        "close_survival_calibration_gap_within_locked_direction",
        "answer_predeclared_reviewer_method_question",
    ]
    assert bounded_analysis["allowed_targets"] == [
        "minimum_sci_ready_evidence_package",
        "scientific_followup_questions",
    ]
    assert bounded_analysis["budget_boundary"] == {
        "max_analysis_rounds_per_gate_window": 3,
        "max_targets_per_round": 2,
        "max_new_primary_claims": 0,
    }
    assert bounded_analysis["completion_boundary"]["return_to_main_gate"] == "publication_eval"
    assert bounded_analysis["completion_boundary"]["required_updates"] == [
        "evidence_ledger",
        "review_ledger",
        "publication_eval",
    ]
    assert paper_quality_contract["structured_reporting_contract"]["table_figure_claim_map_required"] is True
    assert paper_quality_contract["downstream_contract_roles"]["final_audit"] == (
        "audits scientific and paper-quality readiness against this charter"
    )


def test_materialize_study_charter_adds_prediction_model_reporting_guardrails(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "003-survival"

    module.materialize_study_charter(
        study_root=study_root,
        study_id="003-survival",
        study_payload={
            "title": "Survival prediction",
            "study_archetype": "clinical_classifier",
            "manuscript_family": "prediction_model",
            "endpoint_type": "time_to_event",
        },
        execution={},
        required_first_anchor=None,
    )

    payload = json.loads((study_root / "artifacts" / "controller" / "study_charter.json").read_text(encoding="utf-8"))
    contract = payload["paper_quality_contract"]["structured_reporting_contract"]

    assert contract["prediction_model_reporting_required"] is True
    assert contract["manuscript_family"] == "prediction_model"
    assert contract["endpoint_type"] == "time_to_event"
    assert "data_source_years" in contract["prediction_methods"]
    assert "linked_clinical_action_scenario" in contract["decision_curve_clinical_utility"]
    assert "standardized_mean_differences" in contract["baseline_balance_reporting"]
    assert "competing_event_screen" in contract["time_to_event_prediction_reporting"]
    assert contract["competing_risk_reporting_required"] == "when_non_target_deaths_present"
    assert contract["reporting_guideline_family"] == "TRIPOD"
    assert contract["quality_gate_expectation"]["guideline_family"] == "TRIPOD"
    assert contract["quality_gate_expectation"]["gate_relaxation_allowed"] is False
    assert "tripod_model_performance_validation_calibration" in contract["quality_gate_expectation"][
        "gates"
    ]["before_review_handoff"]["required_items"]


def test_materialize_study_charter_freezes_protocol_sap_contract(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "004-protocol"

    module.materialize_study_charter(
        study_root=study_root,
        study_id="004-protocol",
        study_payload={
            "title": "Protocol SAP study",
            "study_design": "retrospective cohort",
            "target_population": "Adults with diabetes in primary care",
            "cohort_boundary": "2016-2024 outpatient cohort with complete baseline labs",
            "endpoint_type": "time_to_event",
            "primary_endpoint": "5-year cardiovascular mortality",
            "primary_analysis": "Cox proportional hazards model with external validation",
            "secondary_analyses": ["calibration by age group", "decision curve analysis"],
            "statistical_methods": ["Cox regression", "Harrell C-index", "calibration slope"],
            "missing_data_plan": "Multiple imputation for baseline covariates",
            "subgroup_plan": ["age strata", "sex strata"],
            "multiplicity_guardrails": ["subgroups are exploratory", "no new primary claim"],
            "power_precision_rationale": "Precision justified by expected event count and confidence interval width.",
            "reporting_guideline_family": "TRIPOD",
            "protocol_ref": "protocol.md",
            "sap_ref": "analysis_plan.json",
            "freeze_owner": "mas",
            "freeze_ref": "controller_decision::freeze-protocol-sap",
        },
        execution={},
        required_first_anchor=None,
    )

    payload = json.loads((study_root / "artifacts" / "controller" / "study_charter.json").read_text(encoding="utf-8"))
    freeze_contract = payload["paper_quality_contract"]["protocol_sap_freeze"]

    assert freeze_contract == {
        "surface": "protocol_sap_freeze",
        "status": "frozen_at_startup",
        "required_before_routes": ["analysis-campaign", "write", "finalize"],
        "gate_relaxation_allowed": False,
        "owner": "mas",
        "freeze_ref": "controller_decision::freeze-protocol-sap",
        "protocol_ref": "protocol.md",
        "sap_ref": "analysis_plan.json",
        "study_design": "retrospective cohort",
        "population_or_cohort_boundary": "2016-2024 outpatient cohort with complete baseline labs",
        "target_population": "Adults with diabetes in primary care",
        "endpoint_type": "time_to_event",
        "primary_endpoint": "5-year cardiovascular mortality",
        "primary_analysis": "Cox proportional hazards model with external validation",
        "secondary_analyses": ["calibration by age group", "decision curve analysis"],
        "statistical_methods": ["Cox regression", "Harrell C-index", "calibration slope"],
        "missing_data_plan": "Multiple imputation for baseline covariates",
        "subgroup_plan": ["age strata", "sex strata"],
        "multiplicity_guardrails": ["subgroups are exploratory", "no new primary claim"],
        "power_precision_or_feasibility_rationale": (
            "Precision justified by expected event count and confidence interval width."
        ),
        "reporting_guideline_family": "TRIPOD",
        "required_updates_when_changed": [
            "study_charter",
            "analysis_campaign_plan",
            "evidence_ledger",
            "review_ledger",
            "publication_eval",
        ],
        "route_back_policy": {
            "missing_required_item": "decision",
            "changed_primary_question_or_endpoint": "human_gate",
            "changed_analysis_plan_within_locked_direction": "analysis-campaign",
        },
    }


def test_materialize_study_charter_sets_default_contract_boundaries(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "002-minimal"

    module.materialize_study_charter(
        study_root=study_root,
        study_id="002-minimal",
        study_payload={
            "title": "Minimal charter",
        },
        execution={},
        required_first_anchor=None,
    )

    payload = json.loads((study_root / "artifacts" / "controller" / "study_charter.json").read_text(encoding="utf-8"))

    assert payload["autonomy_envelope"]["decision_policy"] == "autonomous"
    assert payload["autonomy_envelope"]["launch_profile"] == "continue_existing_state"
    assert payload["autonomy_envelope"]["required_first_anchor"] is None
    assert payload["autonomy_envelope"]["direction_lock_state"] == "startup_frozen"
    assert payload["autonomy_envelope"]["human_gate_boundary"]["policy"] == "major_boundary_only"
    assert payload["autonomy_envelope"]["final_scientific_audit_boundary"]["audit_surfaces"] == [
        "evidence_ledger",
        "review_ledger",
        "final_audit",
    ]
    paper_quality_contract = payload["paper_quality_contract"]
    assert paper_quality_contract["frozen_at_startup"] is True
    assert paper_quality_contract["target_journals"] == []
    assert paper_quality_contract["reporting_expectations"] == {
        "paper_framing_summary": None,
        "explanation_targets": [],
    }
    assert paper_quality_contract["evidence_expectations"] == {
        "minimum_sci_ready_evidence_package": [],
    }
    assert paper_quality_contract["review_expectations"] == {
        "scientific_followup_questions": [],
        "manuscript_conclusion_redlines": [],
    }
    assert paper_quality_contract["bounded_analysis"]["default_owner"] == "mas"
    assert paper_quality_contract["bounded_analysis"]["budget_boundary"] == {
        "max_analysis_rounds_per_gate_window": 2,
        "max_targets_per_round": 3,
        "max_new_primary_claims": 0,
    }
    assert paper_quality_contract["bounded_analysis"]["completion_boundary"]["required_updates"] == [
        "evidence_ledger",
        "review_ledger",
        "publication_eval",
    ]
    assert paper_quality_contract["protocol_sap_freeze"] == {
        "surface": "protocol_sap_freeze",
        "status": "requires_freeze_before_analysis",
        "required_before_routes": ["analysis-campaign", "write", "finalize"],
        "gate_relaxation_allowed": False,
        "owner": "mas",
        "freeze_ref": None,
        "protocol_ref": None,
        "sap_ref": None,
        "study_design": None,
        "population_or_cohort_boundary": None,
        "target_population": None,
        "endpoint_type": None,
        "primary_endpoint": None,
        "primary_analysis": None,
        "secondary_analyses": [],
        "statistical_methods": [],
        "missing_data_plan": None,
        "subgroup_plan": [],
        "multiplicity_guardrails": [],
        "power_precision_or_feasibility_rationale": None,
        "reporting_guideline_family": None,
        "required_updates_when_changed": [
            "study_charter",
            "analysis_campaign_plan",
            "evidence_ledger",
            "review_ledger",
            "publication_eval",
        ],
        "route_back_policy": {
            "missing_required_item": "decision",
            "changed_primary_question_or_endpoint": "human_gate",
            "changed_analysis_plan_within_locked_direction": "analysis-campaign",
        },
    }
    assert paper_quality_contract["downstream_contract_roles"] == {
        "evidence_ledger": "records evidence against evidence_expectations",
        "review_ledger": "records review closure against review_expectations",
        "final_audit": "audits scientific and paper-quality readiness against this charter",
    }

    structured_contract = paper_quality_contract["structured_reporting_contract"]
    assert structured_contract["draft_prevention_gates"] == [
        "introduction_three_paragraph_medical_narrative",
        "methods_subsections_complete_before_first_full_draft",
        "statistical_reporting_plan_before_results_prose",
        "table_figure_claim_map_before_results_prose",
        "first_draft_asset_upgrade_scan_before_full_draft",
        "phenotype_clinical_actionability_before_submission_package",
        "human_metadata_todo_separated_from_scientific_blockers",
    ]
    assert structured_contract["methods_completeness"]["study_design"] == {"status": "required_before_first_full_draft"}
    assert structured_contract["statistical_reporting"]["p_values"] == {"status": "required_before_first_full_draft"}
    assert structured_contract["table_figure_claim_map_required"] is True
    assert structured_contract["human_metadata_admin_todos"] == [
        "authors",
        "affiliations",
        "corresponding_author",
        "ethics",
        "funding",
        "conflict_of_interest",
        "data_availability",
    ]

    first_draft_contract = structured_contract["first_draft_quality_contract"]
    assert first_draft_contract["status"] == "required_before_first_full_draft"
    readiness_contract = first_draft_contract["pre_draft_writing_readiness_contract"]
    assert readiness_contract["surface"] == "pre_draft_writing_readiness_contract"
    assert readiness_contract["stable_path"] == "paper/pre_draft_writing_readiness.json"
    assert readiness_contract["required_before"] == "first_full_draft"
    assert readiness_contract["readiness_status_required"] == "closed"
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
    readiness_item_by_id = {
        str(item["readiness_id"]): item for item in readiness_contract["required_readiness_items"]
    }
    assert readiness_item_by_id["clinical_question"]["required_fields"] == [
        "clinical_problem",
        "evidence_gap",
        "study_objective",
    ]
    assert readiness_item_by_id["population_design_outcome"]["required_fields"] == [
        "target_population",
        "study_design",
        "exposure_or_predictor_window",
        "main_outcome",
        "outcome_horizon",
    ]
    assert readiness_item_by_id["display_to_claim_map"]["source_surfaces"] == [
        "paper/results_narrative_map.json",
        "paper/figure_semantics_manifest.json",
    ]
    assert readiness_item_by_id["claim_evidence_map"]["source_surfaces"] == [
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
    ]
    assert readiness_item_by_id["ai_prose_review_feedback_loop"]["source_surfaces"] == [
        "artifacts/publication_eval/medical_prose_review_request.json",
        "artifacts/publication_eval/medical_prose_review.json",
    ]
    assert readiness_contract["quality_proxy_exclusion_policy"] == {
        "policy_id": "manuscript_quality_proxy_exclusion_v1",
        "controller_or_progress_surfaces_can_authorize_body_quality": False,
        "forbidden_quality_proxies": [
            "controller_checklist",
            "run_log_or_execution_transcript",
            "progress_prose",
            "generic_completion_checklist",
            "packaging_metadata",
        ],
        "required_body_quality_authority": [
            "paper/medical_manuscript_blueprint.json",
            "paper/claim_evidence_map.json",
            "artifacts/publication_eval/medical_prose_review.json",
            "artifacts/publication_eval/latest.json",
        ],
    }
    assert readiness_contract["stronger_paper_shape_route_back"] == {
        "default_route": "bounded_analysis_or_analysis_campaign",
        "trigger": "verified evidence surfaces support a stronger manuscript shape than a descriptive first draft",
        "preferred_targets": [
            "minimum_sci_ready_evidence_package",
            "scientific_followup_questions",
            "manuscript_conclusion_redlines",
        ],
        "bounded_analysis_owner": "mas",
        "analysis_campaign_allowed": True,
        "forbidden_action": "write_light_descriptive_first_draft",
        "claim_boundary": "no_new_primary_claims_without_human_gate",
    }
    assert first_draft_contract["imrad_section_contract"]["article_body"] == [
        "Title",
        "Abstract",
        "Introduction",
        "Methods",
        "Results",
        "Discussion",
        "Conclusion",
    ]
    assert first_draft_contract["manuscript_native_prose"]["required"] is True
    assert "work_report_question_answer_frame" in first_draft_contract["manuscript_native_prose"]["forbidden_modes"]
    assert first_draft_contract["medical_prose_style_contract"]["style_profile_id"] == (
        "general_medical_journal_prose_v1"
    )
    assert first_draft_contract["medical_prose_style_contract"]["target_voice"] == (
        "neutral_clinical_original_research"
    )
    assert "clinical_problem_to_evidence_gap_to_objective" in first_draft_contract[
        "medical_prose_style_contract"
    ]["introduction_rhetoric"]["paragraph_sequence"]
    assert first_draft_contract["medical_prose_style_contract"]["source_basis"] == [
        "Zeiger biomedical research paper clear-writing and paper-text model",
        "Gopen and Swan reader-expectation information flow",
        "JAMA concise, specific, informative, non-overstated medical-journal wording",
        "Elsevier medical manuscript audience, relevance, and avoid-overstatement guidance",
        "JAMA Network Open original investigation prose exemplars",
    ]
    blueprint_contract = first_draft_contract["medical_manuscript_blueprint_contract"]
    assert blueprint_contract["surface"] == "medical_manuscript_blueprint"
    assert blueprint_contract["stable_path"] == "paper/medical_manuscript_blueprint.json"
    assert blueprint_contract["required_before"] == "first_full_draft"
    assert "clinical_problem" in blueprint_contract["required_fields"]
    assert "main_findings_by_clinical_importance" in blueprint_contract["required_fields"]
    assert "figure_table_rhetorical_roles" in blueprint_contract["required_fields"]
    assert "discussion_claim_boundary" in blueprint_contract["required_fields"]
    assert "journal_voice_target" in blueprint_contract["required_fields"]
    assert blueprint_contract["required_argument_order"] == [
        "clinical_problem",
        "evidence_gap",
        "study_objective",
        "main_findings_by_clinical_importance",
        "clinical_interpretation",
        "limitations",
    ]
    assert "paper/claim_evidence_map.json" in blueprint_contract["required_source_surfaces"]
    prose_review_contract = first_draft_contract["medical_prose_review_contract"]
    assert prose_review_contract["surface"] == "medical_prose_review"
    assert prose_review_contract["stable_path"] == "artifacts/publication_eval/medical_prose_review.json"
    assert prose_review_contract["owner"] == "ai_reviewer"
    assert prose_review_contract["mechanical_projection_can_authorize_quality"] is False
    assert "work_report_residue_judgment" in prose_review_contract["subjective_quality_authority"]
    assert first_draft_contract["first_draft_generation_model"]["pre_draft_inputs"] == [
        "clinical_problem",
        "study_design",
        "target_population",
        "prediction_timepoint_or_exposure_window",
        "outcome_definition_and_horizon",
        "analysis_plan",
        "display_to_claim_map",
        "reader_facing_contribution",
        "medical_manuscript_blueprint",
        "pre_draft_writing_readiness",
        "medical_prose_style_contract",
        "medical_prose_review",
    ]
    assert first_draft_contract["first_draft_generation_model"]["route_back_if_missing"] == (
        "return_to_outline_or_analysis_campaign_before_first_full_draft"
    )
    assert first_draft_contract["pre_draft_upgrade_scan"]["status"] == "required_before_first_full_draft"
    assert first_draft_contract["field_verification_policy"]["multicenter_or_national_claims"] == (
        "verify supporting fields before using multicenter or national framing"
    )
    assert first_draft_contract["too_light_draft_route_back"]["route"] == "analysis-campaign"
    assert "clinician_recommendation" in first_draft_contract["discussion_floor"]


def test_materialize_study_charter_preserves_required_readiness_when_first_draft_contract_is_custom(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "003-custom"

    module.materialize_study_charter(
        study_root=study_root,
        study_id="003-custom",
        study_payload={
            "title": "Custom first draft contract",
            "first_draft_quality_contract": {
                "status": "custom_required_before_first_full_draft",
                "site_specific_axis": {"status": "required_before_first_full_draft"},
            },
        },
        execution={},
        required_first_anchor=None,
    )

    payload = json.loads((study_root / "artifacts" / "controller" / "study_charter.json").read_text(encoding="utf-8"))
    first_draft_contract = payload["paper_quality_contract"]["structured_reporting_contract"][
        "first_draft_quality_contract"
    ]

    assert first_draft_contract["status"] == "custom_required_before_first_full_draft"
    assert first_draft_contract["site_specific_axis"] == {"status": "required_before_first_full_draft"}
    assert first_draft_contract["pre_draft_writing_readiness_contract"]["required_before"] == (
        "first_full_draft"
    )
    assert "pre_draft_writing_readiness" in first_draft_contract["first_draft_generation_model"][
        "pre_draft_inputs"
    ]
    assert first_draft_contract["quality_proxy_exclusion_policy"] == {
        "controller_or_progress_surfaces_can_authorize_body_quality": False,
        "forbidden_quality_proxies": [
            "controller_checklist",
            "run_log_or_execution_transcript",
            "progress_prose",
            "generic_completion_checklist",
            "packaging_metadata",
        ],
    }
