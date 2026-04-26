from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import yaml


def _make_profile(tmp_path: Path, **overrides):
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    payload = {
        "name": "diabetes",
        "workspace_root": workspace_root,
        "runtime_root": workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        "studies_root": workspace_root / "studies",
        "portfolio_root": workspace_root / "portfolio",
        "med_deepscientist_runtime_root": workspace_root / "ops" / "med-deepscientist" / "runtime",
        "med_deepscientist_repo_root": tmp_path / "med-deepscientist",
        "default_publication_profile": "general_medical_journal",
        "default_citation_style": "AMA",
        "enable_medical_overlay": True,
        "medical_overlay_scope": "workspace",
        "medical_overlay_skills": ("intake-audit", "baseline", "write", "finalize"),
        "research_route_bias_policy": "high_plasticity_medical",
        "preferred_study_archetypes": ("clinical_classifier",),
        "default_submission_targets": (),
        "default_startup_anchor_policy": "scout_first_for_continue_existing_state",
        "legacy_code_execution_policy": "forbid_without_user_approval",
        "startup_boundary_requirements": ("paper_framing", "journal_shortlist", "evidence_package"),
    }
    payload.update(overrides)
    return profiles.WorkspaceProfile(**payload)


def _write_study(studies_root: Path, study_id: str, payload: dict[str, object]) -> Path:
    study_root = studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return study_root


def test_resolve_medical_reporting_contract_for_prediction_manuscript() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    contract = module.resolve_medical_reporting_contract(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
        endpoint_type="binary",
        submission_target_family="general_medical_journal",
    )

    assert contract.reporting_guideline_family == "TRIPOD"
    assert contract.cohort_flow_required is True
    assert contract.baseline_characteristics_required is True
    assert contract.table_shell_requirements == ("table1_baseline_characteristics",)
    assert contract.figure_shell_requirements == ("cohort_flow_figure",)
    assert contract.required_illustration_shells == ("cohort_flow_figure",)
    assert contract.required_table_shells == ("table1_baseline_characteristics",)
    assert contract.required_evidence_templates == ()
    assert contract.structured_reporting_contract["prediction_model_reporting_required"] is True
    assert "prediction_methods" in contract.structured_reporting_contract
    assert "linked_clinical_action_scenario" in contract.structured_reporting_contract[
        "decision_curve_clinical_utility"
    ]
    assert "time_to_event_prediction_reporting" not in contract.structured_reporting_contract


def test_reporting_guideline_expectation_registry_covers_equator_families() -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_guidelines")

    assert module.SUPPORTED_REPORTING_GUIDELINE_EXPECTATION_FAMILIES == (
        "STROBE",
        "TRIPOD",
        "CONSORT",
        "PRISMA",
    )
    expectation = module.build_reporting_guideline_expectation("PRISMA")

    assert expectation["authority"] == "EQUATOR"
    assert expectation["guideline_family"] == "PRISMA"
    assert expectation["checklist_surface"] == "reporting_guideline_checklist.json"
    assert expectation["gates"]["before_first_full_draft"]["required_status"] == "closed"
    assert "prisma_search_selection_flow" in expectation["gates"]["before_review_handoff"]["required_items"]


def test_controller_summary_embeds_guideline_expectation_and_pre_review_gates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_contract")
    profile = _make_profile(tmp_path)
    study_root = _write_study(
        profile.studies_root,
        "001-survival-reporting",
        {
            "study_id": "001-survival-reporting",
            "study_archetype": "clinical_classifier",
            "endpoint_type": "time_to_event",
            "manuscript_family": "prediction_model",
        },
    )

    result = module.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    expectation = result["reporting_guideline_expectation"]
    structured_contract = result["structured_reporting_contract"]

    assert expectation["authority"] == "EQUATOR"
    assert expectation["guideline_family"] == "TRIPOD"
    assert expectation["gates"]["before_first_full_draft"]["required_status"] == "closed"
    assert "tripod_model_performance_validation_calibration" in expectation["gates"][
        "before_review_handoff"
    ]["required_items"]
    assert structured_contract["reporting_guideline_family"] == "TRIPOD"
    assert structured_contract["reporting_guideline_expectation"] == expectation
    assert structured_contract["methods_completeness"]["study_design"]["status"] == (
        "required_before_first_full_draft"
    )
    assert structured_contract["table_figure_claim_map_required"] is True


def test_resolve_medical_reporting_contract_for_randomized_trial_publication() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    contract = module.resolve_medical_reporting_contract(
        study_archetype="clinical_classifier",
        manuscript_family="randomized_trial",
        endpoint_type="binary",
        submission_target_family="general_medical_journal",
    )

    assert contract.reporting_guideline_family == "CONSORT"
    assert contract.table_shell_requirements == ("table1_baseline_characteristics",)
    assert contract.figure_shell_requirements == ("cohort_flow_figure",)


def test_resolve_medical_reporting_contract_rejects_unknown_manuscript_family() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    with pytest.raises(ValueError, match="Unsupported manuscript_family"):
        module.resolve_medical_reporting_contract(
            study_archetype="clinical_classifier",
            manuscript_family="some_other_manuscript",
            endpoint_type="binary",
            submission_target_family="general_medical_journal",
        )


def test_resolve_medical_reporting_contract_defaults_to_strobe_for_non_prediction() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    contract = module.resolve_medical_reporting_contract(
        study_archetype="clinical_classifier",
        manuscript_family="clinical_observation",
        endpoint_type="binary",
        submission_target_family="general_medical_journal",
    )

    assert contract.reporting_guideline_family == "STROBE"


def test_resolve_medical_reporting_contract_for_clinical_subtype_reconstruction() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    contract = module.resolve_medical_reporting_contract(
        study_archetype="clinical_subtype_reconstruction",
        manuscript_family="clinical_observation",
        endpoint_type="descriptive",
        submission_target_family="general_medical_journal",
    )

    assert contract.reporting_guideline_family == "STROBE"
    assert contract.table_shell_requirements == (
        "table1_baseline_characteristics",
        "table2_phenotype_gap_summary",
        "table3_transition_site_support_summary",
    )
    assert contract.figure_shell_requirements == (
        "cohort_flow_figure",
        "phenotype_gap_structure_figure",
        "site_held_out_stability_figure",
        "treatment_gap_alignment_figure",
    )
    assert contract.required_illustration_shells == ("cohort_flow_figure",)
    assert contract.required_table_shells == (
        "table1_baseline_characteristics",
        "table2_phenotype_gap_summary",
        "table3_transition_site_support_summary",
    )
    assert contract.required_evidence_templates == (
        "phenotype_gap_structure_figure",
        "site_held_out_stability_figure",
        "treatment_gap_alignment_figure",
    )
    assert contract.display_shell_plan == (
        module.DisplayShellPlanItem(
            display_id="cohort_flow",
            display_kind="figure",
            requirement_key="cohort_flow_figure",
            catalog_id="F1",
            story_role="study_setup",
        ),
        module.DisplayShellPlanItem(
            display_id="phenotype_gap_structure",
            display_kind="figure",
            requirement_key="phenotype_gap_structure_figure",
            catalog_id="F2",
            story_role="result_evidence",
        ),
        module.DisplayShellPlanItem(
            display_id="site_held_out_stability",
            display_kind="figure",
            requirement_key="site_held_out_stability_figure",
            catalog_id="F3",
            story_role="result_evidence",
        ),
        module.DisplayShellPlanItem(
            display_id="treatment_gap_alignment",
            display_kind="figure",
            requirement_key="treatment_gap_alignment_figure",
            catalog_id="F4",
            story_role="result_evidence",
        ),
        module.DisplayShellPlanItem(
            display_id="baseline_characteristics",
            display_kind="table",
            requirement_key="table1_baseline_characteristics",
            catalog_id="T1",
            story_role="study_setup",
        ),
        module.DisplayShellPlanItem(
            display_id="phenotype_gap_summary",
            display_kind="table",
            requirement_key="table2_phenotype_gap_summary",
            catalog_id="T2",
            story_role="result_evidence",
        ),
        module.DisplayShellPlanItem(
            display_id="transition_site_support_summary",
            display_kind="table",
            requirement_key="table3_transition_site_support_summary",
            catalog_id="T3",
            story_role="result_evidence",
        ),
    )
    assert contract.display_ambition == "strong"
    assert contract.minimum_main_text_figures == 4
    assert contract.recommended_main_text_figures == (
        module.DisplayBlueprintItem(
            catalog_id="F2",
            display_kind="figure",
            story_role="result_primary",
            narrative_purpose="phenotype_characterization_and_gap_structure",
            tier="core",
        ),
        module.DisplayBlueprintItem(
            catalog_id="F3",
            display_kind="figure",
            story_role="result_validation",
            narrative_purpose="site_held_out_reproducibility_or_assignment_stability",
            tier="core",
        ),
        module.DisplayBlueprintItem(
            catalog_id="F4",
            display_kind="figure",
            story_role="result_treatment",
            narrative_purpose="treatment_target_gap_alignment",
            tier="core",
        ),
    )


def test_resolve_medical_reporting_contract_for_survival_prediction_model_shells() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    contract = module.resolve_medical_reporting_contract(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
        endpoint_type="time_to_event",
        submission_target_family="general_medical_journal",
    )

    assert contract.reporting_guideline_family == "TRIPOD"
    assert contract.table_shell_requirements == (
        "table1_baseline_characteristics",
        "table2_time_to_event_performance_summary",
    )
    assert contract.figure_shell_requirements == (
        "cohort_flow_figure",
        "time_to_event_discrimination_calibration_panel",
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
    )
    assert contract.required_illustration_shells == ("cohort_flow_figure",)
    assert contract.required_table_shells == (
        "table1_baseline_characteristics",
        "table2_time_to_event_performance_summary",
    )
    assert contract.required_evidence_templates == (
        "time_to_event_discrimination_calibration_panel",
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
    )
    assert contract.display_shell_plan == (
        module.DisplayShellPlanItem(
            display_id="cohort_flow",
            display_kind="figure",
            requirement_key="cohort_flow_figure",
            catalog_id="F1",
            story_role="study_setup",
        ),
        module.DisplayShellPlanItem(
            display_id="discrimination_calibration",
            display_kind="figure",
            requirement_key="time_to_event_discrimination_calibration_panel",
            catalog_id="F2",
            story_role="result_evidence",
        ),
        module.DisplayShellPlanItem(
            display_id="km_risk_stratification",
            display_kind="figure",
            requirement_key="time_to_event_risk_group_summary",
            catalog_id="F3",
            story_role="result_evidence",
        ),
        module.DisplayShellPlanItem(
            display_id="decision_curve",
            display_kind="figure",
            requirement_key="time_to_event_decision_curve",
            catalog_id="F4",
            story_role="result_evidence",
        ),
        module.DisplayShellPlanItem(
            display_id="multicenter_generalizability",
            display_kind="figure",
            requirement_key="multicenter_generalizability_overview",
            catalog_id="F5",
            story_role="result_evidence",
        ),
        module.DisplayShellPlanItem(
            display_id="baseline_characteristics",
            display_kind="table",
            requirement_key="table1_baseline_characteristics",
            catalog_id="T1",
            story_role="study_setup",
        ),
        module.DisplayShellPlanItem(
            display_id="time_to_event_performance_summary",
            display_kind="table",
            requirement_key="table2_time_to_event_performance_summary",
            catalog_id="T2",
            story_role="result_evidence",
        ),
    )
    assert contract.structured_reporting_contract["prediction_model_reporting_required"] is True
    assert contract.structured_reporting_contract["endpoint_type"] == "time_to_event"
    assert "competing_event_screen" in contract.structured_reporting_contract[
        "time_to_event_prediction_reporting"
    ]
    assert (
        contract.structured_reporting_contract["competing_risk_reporting_required"]
        == "when_non_target_deaths_present"
    )


def test_normalize_legacy_requirement_keys_rewrites_time_to_event_aliases() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    payload = {
        "figure_shell_requirements": [
            "cohort_flow_figure",
            "kaplan_meier_grouped",
        ],
        "required_evidence_templates": [
            "kaplan_meier_grouped",
            "time_to_event_decision_curve",
        ],
        "display_shell_plan": [
            {
                "display_id": "km_risk_stratification",
                "display_kind": "figure",
                "requirement_key": "kaplan_meier_grouped",
                "catalog_id": "F3",
            }
        ],
    }

    updated = module.normalize_legacy_requirement_keys(payload)

    assert updated is True
    assert payload["figure_shell_requirements"] == [
        "cohort_flow_figure",
        "time_to_event_risk_group_summary",
    ]
    assert payload["required_evidence_templates"] == [
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
    ]
    assert payload["display_shell_plan"][0]["requirement_key"] == "time_to_event_risk_group_summary"


def test_display_story_role_normalizes_namespaced_requirement_keys() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    assert (
        module.display_story_role_for_requirement_key(
            "fenggaolab.org.medical-display-core::cohort_flow_figure"
        )
        == "study_setup"
    )
    assert (
        module.display_story_role_for_requirement_key(
            "fenggaolab.org.medical-display-core::table1_baseline_characteristics"
        )
        == "study_setup"
    )


def test_resolve_medical_reporting_contract_for_survey_trend_observation() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_reporting_contract")

    contract = module.resolve_medical_reporting_contract(
        study_archetype="survey_trend_analysis",
        manuscript_family="clinical_observation",
        endpoint_type="descriptive",
        submission_target_family="general_medical_journal",
    )

    assert contract.reporting_guideline_family == "STROBE"
    assert contract.cohort_flow_required is True
    assert contract.baseline_characteristics_required is True
    assert contract.table_shell_requirements == ("table1_baseline_characteristics",)
    assert contract.figure_shell_requirements == ("cohort_flow_figure",)
    assert contract.required_illustration_shells == ("cohort_flow_figure",)
    assert contract.required_table_shells == ("table1_baseline_characteristics",)
    assert contract.required_evidence_templates == ()
    assert contract.display_ambition == "strong"
    assert contract.minimum_main_text_figures == 4
    assert contract.recommended_main_text_figures == (
        module.DisplayBlueprintItem(
            catalog_id="F2",
            display_kind="figure",
            story_role="result_primary",
            narrative_purpose="historical_to_current_patient_migration",
            tier="core",
        ),
        module.DisplayBlueprintItem(
            catalog_id="F3",
            display_kind="figure",
            story_role="result_alignment",
            narrative_purpose="clinician_surface_and_guideline_alignment",
            tier="core",
        ),
        module.DisplayBlueprintItem(
            catalog_id="F4",
            display_kind="figure",
            story_role="result_interpretive",
            narrative_purpose="divergence_decomposition_or_robustness",
            tier="core",
        ),
    )
    assert contract.display_shell_plan == (
        module.DisplayShellPlanItem(
            display_id="cohort_flow",
            display_kind="figure",
            requirement_key="cohort_flow_figure",
            catalog_id="F1",
            story_role="study_setup",
        ),
        module.DisplayShellPlanItem(
            display_id="baseline_characteristics",
            display_kind="table",
            requirement_key="table1_baseline_characteristics",
            catalog_id="T1",
            story_role="study_setup",
        ),
    )
