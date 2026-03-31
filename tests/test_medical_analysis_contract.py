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
