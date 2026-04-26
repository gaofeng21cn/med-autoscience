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
    assert payload["paper_quality_contract"] == {
        "frozen_at_startup": True,
        "target_journals": ["The BMJ", "JAMA Internal Medicine"],
        "reporting_expectations": {
            "paper_framing_summary": "Clinical survival framing is fixed around CVD-related mortality.",
            "explanation_targets": [
                "Separate endpoint-alignment gap from case-mix shift and residual unexplained gap.",
            ],
        },
        "evidence_expectations": {
            "minimum_sci_ready_evidence_package": ["external_validation", "decision_curve_analysis"],
        },
        "review_expectations": {
            "scientific_followup_questions": [
                "Why is the 5-year all-cause mortality gap between China and the US so large?",
            ],
            "manuscript_conclusion_redlines": [
                "Do not conclude only that a China-trained absolute risk model is non-transportable.",
            ],
        },
        "bounded_analysis": {
            "default_owner": "mas",
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
        "structured_reporting_contract": {
            "draft_prevention_gates": [
                "introduction_three_paragraph_medical_narrative",
                "methods_subsections_complete_before_first_full_draft",
                "statistical_reporting_plan_before_results_prose",
                "table_figure_claim_map_before_results_prose",
                "first_draft_asset_upgrade_scan_before_full_draft",
                "phenotype_clinical_actionability_before_submission_package",
                "human_metadata_todo_separated_from_scientific_blockers",
            ],
            "methods_completeness": {
                "study_design": {"status": "required_before_first_full_draft"},
                "cohort": {"status": "required_before_first_full_draft"},
                "variables": {"status": "required_before_first_full_draft"},
                "model": {"status": "required_before_first_full_draft"},
                "validation": {"status": "required_before_first_full_draft"},
                "statistical_analysis": {"status": "required_before_first_full_draft"},
            },
            "statistical_reporting": {
                "summary_format": {"status": "required_before_first_full_draft"},
                "p_values": {"status": "required_before_first_full_draft"},
                "subgroup_tests": {"status": "required_before_first_full_draft"},
            },
            "first_draft_quality_contract": {
                "status": "required_before_first_full_draft",
                "pre_draft_upgrade_scan": {
                    "status": "required_before_first_full_draft",
                    "required_axes": [
                        "timepoint_or_temporal_depth",
                        "stakeholder_or_role_contrast",
                        "center_geography_or_site_coverage",
                        "guideline_correspondence",
                        "clinically_legible_subgroup_or_association_plan",
                        "real_world_adoption_constraints",
                    ],
                },
                "field_verification_policy": {
                    "multicenter_or_national_claims": (
                        "verify supporting fields before using multicenter or national framing"
                    ),
                    "subgroup_or_association_analyses": (
                        "predeclare bounded analyses only when verified variables support them"
                    ),
                },
                "too_light_draft_route_back": {
                    "route": "analysis-campaign",
                    "trigger": (
                        "verified data dimensions can support a stronger paper than the current descriptive draft"
                    ),
                    "claim_boundary": "no_new_primary_claims_without_human_gate",
                },
                "discussion_floor": [
                    "guideline_logic",
                    "price_or_cost",
                    "reimbursement",
                    "access",
                    "safety",
                    "clinician_recommendation",
                ],
            },
            "table_figure_claim_map_required": True,
            "human_metadata_admin_todos": [
                "authors",
                "affiliations",
                "corresponding_author",
                "ethics",
                "funding",
                "conflict_of_interest",
                "data_availability",
            ],
        },
        "downstream_contract_roles": {
            "evidence_ledger": "records evidence against evidence_expectations",
            "review_ledger": "records review closure against review_expectations",
            "final_audit": "audits scientific and paper-quality readiness against this charter",
        },
    }


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
    assert payload["paper_quality_contract"] == {
        "frozen_at_startup": True,
        "target_journals": [],
        "reporting_expectations": {
            "paper_framing_summary": None,
            "explanation_targets": [],
        },
        "evidence_expectations": {
            "minimum_sci_ready_evidence_package": [],
        },
        "review_expectations": {
            "scientific_followup_questions": [],
            "manuscript_conclusion_redlines": [],
        },
        "bounded_analysis": {
            "default_owner": "mas",
            "allowed_scenarios": [
                "close_predeclared_evidence_gap_within_locked_direction",
                "close_predeclared_review_gap_within_locked_direction",
                "close_predeclared_submission_gap_within_locked_direction",
            ],
            "allowed_targets": [
                "minimum_sci_ready_evidence_package",
                "scientific_followup_questions",
                "manuscript_conclusion_redlines",
            ],
            "budget_boundary": {
                "max_analysis_rounds_per_gate_window": 2,
                "max_targets_per_round": 3,
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
        "structured_reporting_contract": {
            "draft_prevention_gates": [
                "introduction_three_paragraph_medical_narrative",
                "methods_subsections_complete_before_first_full_draft",
                "statistical_reporting_plan_before_results_prose",
                "table_figure_claim_map_before_results_prose",
                "first_draft_asset_upgrade_scan_before_full_draft",
                "phenotype_clinical_actionability_before_submission_package",
                "human_metadata_todo_separated_from_scientific_blockers",
            ],
            "methods_completeness": {
                "study_design": {"status": "required_before_first_full_draft"},
                "cohort": {"status": "required_before_first_full_draft"},
                "variables": {"status": "required_before_first_full_draft"},
                "model": {"status": "required_before_first_full_draft"},
                "validation": {"status": "required_before_first_full_draft"},
                "statistical_analysis": {"status": "required_before_first_full_draft"},
            },
            "statistical_reporting": {
                "summary_format": {"status": "required_before_first_full_draft"},
                "p_values": {"status": "required_before_first_full_draft"},
                "subgroup_tests": {"status": "required_before_first_full_draft"},
            },
            "first_draft_quality_contract": {
                "status": "required_before_first_full_draft",
                "pre_draft_upgrade_scan": {
                    "status": "required_before_first_full_draft",
                    "required_axes": [
                        "timepoint_or_temporal_depth",
                        "stakeholder_or_role_contrast",
                        "center_geography_or_site_coverage",
                        "guideline_correspondence",
                        "clinically_legible_subgroup_or_association_plan",
                        "real_world_adoption_constraints",
                    ],
                },
                "field_verification_policy": {
                    "multicenter_or_national_claims": (
                        "verify supporting fields before using multicenter or national framing"
                    ),
                    "subgroup_or_association_analyses": (
                        "predeclare bounded analyses only when verified variables support them"
                    ),
                },
                "too_light_draft_route_back": {
                    "route": "analysis-campaign",
                    "trigger": (
                        "verified data dimensions can support a stronger paper than the current descriptive draft"
                    ),
                    "claim_boundary": "no_new_primary_claims_without_human_gate",
                },
                "discussion_floor": [
                    "guideline_logic",
                    "price_or_cost",
                    "reimbursement",
                    "access",
                    "safety",
                    "clinician_recommendation",
                ],
            },
            "table_figure_claim_map_required": True,
            "human_metadata_admin_todos": [
                "authors",
                "affiliations",
                "corresponding_author",
                "ethics",
                "funding",
                "conflict_of_interest",
                "data_availability",
            ],
        },
        "downstream_contract_roles": {
            "evidence_ledger": "records evidence against evidence_expectations",
            "review_ledger": "records review closure against review_expectations",
            "final_audit": "audits scientific and paper-quality readiness against this charter",
        },
    }
