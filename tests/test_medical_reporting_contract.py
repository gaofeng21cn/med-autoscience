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
        "table2_primary_performance_by_horizon",
    )
    assert contract.figure_shell_requirements == (
        "cohort_flow_figure",
        "discrimination_calibration_figure",
        "km_risk_stratification_figure",
        "decision_curve_figure",
    )
    assert contract.required_illustration_shells == ("cohort_flow_figure",)
    assert contract.required_table_shells == (
        "table1_baseline_characteristics",
        "table2_primary_performance_by_horizon",
    )
    assert contract.required_evidence_templates == ()
