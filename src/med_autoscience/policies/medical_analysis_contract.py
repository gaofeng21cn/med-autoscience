from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MedicalAnalysisContract:
    study_archetype: str
    endpoint_type: str
    submission_target_family: str
    required_analysis_packages: tuple[str, ...]
    required_reporting_items: tuple[str, ...]
    forbidden_default_routes: tuple[str, ...]

SUPPORTED_STUDY_ARCHETYPES = ("clinical_classifier",)
SUPPORTED_ENDPOINT_TYPES = ("binary", "time_to_event")
SUPPORTED_SUBMISSION_TARGET_FAMILIES = ("general_medical_journal",)

ANALYSIS_PACKAGES: dict[tuple[str, str], tuple[str, ...]] = {
    ("clinical_classifier", "binary"): (
        "discrimination_metrics",
        "calibration_assessment",
        "decision_curve_analysis",
        "subgroup_heterogeneity",
    ),
    ("clinical_classifier", "time_to_event"): (
        "discrimination_metrics",
        "calibration_assessment",
        "km_risk_stratification",
        "decision_curve_analysis",
        "censoring_aware_validation",
        "subgroup_heterogeneity",
        "sensitivity_support",
    ),
}
REQUIRED_REPORTING_ITEMS: dict[tuple[str, str], tuple[str, ...]] = {
    ("clinical_classifier", "binary"): (
        "paper_experiment_matrix",
        "derived_analysis_manifest",
    ),
    ("clinical_classifier", "time_to_event"): (
        "paper_experiment_matrix",
        "derived_analysis_manifest",
        "horizon_definition",
        "model_specification",
    ),
}
FORBIDDEN_DEFAULT_ROUTES: dict[tuple[str, str], tuple[str, ...]] = {
    ("clinical_classifier", "binary"): ("figure_by_figure_results_narration",),
    ("clinical_classifier", "time_to_event"): ("figure_by_figure_results_narration",),
}


def resolve_medical_analysis_contract(
    *,
    study_archetype: str,
    endpoint_type: str,
    submission_target_family: str,
) -> MedicalAnalysisContract:
    supported_study_archetypes = sorted({item[0] for item in ANALYSIS_PACKAGES})
    if study_archetype not in supported_study_archetypes:
        supported = ", ".join(supported_study_archetypes)
        raise ValueError(
            f"Unsupported study_archetype {study_archetype}. Supported: {supported}"
        )
    if endpoint_type not in SUPPORTED_ENDPOINT_TYPES:
        supported = ", ".join(SUPPORTED_ENDPOINT_TYPES)
        raise ValueError(
            f"Unsupported endpoint_type {endpoint_type}. Supported: {supported}"
        )
    if submission_target_family not in SUPPORTED_SUBMISSION_TARGET_FAMILIES:
        supported = ", ".join(SUPPORTED_SUBMISSION_TARGET_FAMILIES)
        raise ValueError(
            f"Unsupported submission_target_family {submission_target_family}. Supported: {supported}"
        )
    contract_key = (study_archetype, endpoint_type)
    if contract_key not in ANALYSIS_PACKAGES:
        raise ValueError(
            "Unsupported medical analysis contract combination "
            f"study_archetype={study_archetype}, endpoint_type={endpoint_type}"
        )

    return MedicalAnalysisContract(
        study_archetype=study_archetype,
        endpoint_type=endpoint_type,
        submission_target_family=submission_target_family,
        required_analysis_packages=ANALYSIS_PACKAGES[contract_key],
        required_reporting_items=REQUIRED_REPORTING_ITEMS[contract_key],
        forbidden_default_routes=FORBIDDEN_DEFAULT_ROUTES[contract_key],
    )
