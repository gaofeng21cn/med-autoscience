from __future__ import annotations

import importlib
import pytest


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
        "kaplan_meier_grouped",
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
        "kaplan_meier_grouped",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
    )
    assert contract.display_shell_plan == (
        module.DisplayShellPlanItem(
            display_id="cohort_flow",
            display_kind="figure",
            requirement_key="cohort_flow_figure",
            catalog_id="F1",
        ),
        module.DisplayShellPlanItem(
            display_id="discrimination_calibration",
            display_kind="figure",
            requirement_key="time_to_event_discrimination_calibration_panel",
            catalog_id="F2",
        ),
        module.DisplayShellPlanItem(
            display_id="km_risk_stratification",
            display_kind="figure",
            requirement_key="kaplan_meier_grouped",
            catalog_id="F3",
        ),
        module.DisplayShellPlanItem(
            display_id="decision_curve",
            display_kind="figure",
            requirement_key="time_to_event_decision_curve",
            catalog_id="F4",
        ),
        module.DisplayShellPlanItem(
            display_id="multicenter_generalizability",
            display_kind="figure",
            requirement_key="multicenter_generalizability_overview",
            catalog_id="F5",
        ),
        module.DisplayShellPlanItem(
            display_id="baseline_characteristics",
            display_kind="table",
            requirement_key="table1_baseline_characteristics",
            catalog_id="T1",
        ),
        module.DisplayShellPlanItem(
            display_id="time_to_event_performance_summary",
            display_kind="table",
            requirement_key="table2_time_to_event_performance_summary",
            catalog_id="T2",
        ),
    )
