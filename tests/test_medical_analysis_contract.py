from __future__ import annotations

import importlib
import pytest


def test_resolve_medical_analysis_contract_for_clinical_classifier() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_analysis_contract")

    contract = module.resolve_medical_analysis_contract(
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        submission_target_family="general_medical_journal",
    )
    assert contract.study_archetype == "clinical_classifier"
    assert "discrimination_metrics" in contract.required_analysis_packages
    assert "calibration_assessment" in contract.required_analysis_packages
    assert "decision_curve_analysis" in contract.required_analysis_packages
    assert "subgroup_heterogeneity" in contract.required_analysis_packages
    assert "figure_by_figure_results_narration" in contract.forbidden_default_routes


def test_resolve_medical_analysis_contract_rejects_unknown_study_archetype() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_analysis_contract")

    with pytest.raises(ValueError, match="Unsupported study_archetype"):
        module.resolve_medical_analysis_contract(
            study_archetype="unknown_archetype",
            endpoint_type="binary",
            submission_target_family="general_medical_journal",
        )


def test_medical_policies_package_exports_contracts() -> None:
    from med_autoscience.policies import (
        MedicalAnalysisContract,
        MedicalReportingContract,
        resolve_medical_analysis_contract,
        resolve_medical_reporting_contract,
    )

    assert MedicalAnalysisContract.__name__ == "MedicalAnalysisContract"
    assert MedicalReportingContract.__name__ == "MedicalReportingContract"
    assert callable(resolve_medical_analysis_contract)
    assert callable(resolve_medical_reporting_contract)


def test_resolve_medical_analysis_contract_for_survival_endpoint() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_analysis_contract")

    contract = module.resolve_medical_analysis_contract(
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        submission_target_family="general_medical_journal",
    )

    assert contract.required_analysis_packages == (
        "discrimination_metrics",
        "calibration_assessment",
        "km_risk_stratification",
        "decision_curve_analysis",
        "censoring_aware_validation",
        "subgroup_heterogeneity",
        "sensitivity_support",
    )
    assert contract.required_reporting_items == (
        "paper_experiment_matrix",
        "derived_analysis_manifest",
        "horizon_definition",
        "model_specification",
    )


def test_resolve_medical_analysis_contract_for_survey_trend_analysis() -> None:
    module = importlib.import_module("med_autoscience.policies.medical_analysis_contract")

    contract = module.resolve_medical_analysis_contract(
        study_archetype="survey_trend_analysis",
        endpoint_type="descriptive",
        submission_target_family="general_medical_journal",
    )

    assert contract.study_archetype == "survey_trend_analysis"
    assert contract.endpoint_type == "descriptive"
    assert contract.required_analysis_packages == (
        "descriptive_prevalence_estimation",
        "cross_survey_harmonization",
        "trend_shift_assessment",
        "guideline_correspondence_matrix",
        "subgroup_heterogeneity",
    )
    assert contract.required_reporting_items == (
        "paper_experiment_matrix",
        "derived_analysis_manifest",
        "harmonization_crosswalk",
    )
    assert contract.forbidden_default_routes == (
        "predictive_model_framing",
        "figure_by_figure_results_narration",
    )
