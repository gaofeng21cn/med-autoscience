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
SUPPORTED_ENDPOINT_TYPES = ("binary",)
SUPPORTED_SUBMISSION_TARGET_FAMILIES = ("general_medical_journal",)

ANALYSIS_PACKAGES: dict[str, tuple[str, ...]] = {
    "clinical_classifier": (
        "discrimination_metrics",
        "calibration_assessment",
        "decision_curve_analysis",
        "subgroup_heterogeneity",
    ),
}


def resolve_medical_analysis_contract(
    *,
    study_archetype: str,
    endpoint_type: str,
    submission_target_family: str,
) -> MedicalAnalysisContract:
    if study_archetype not in ANALYSIS_PACKAGES:
        supported = ", ".join(sorted(ANALYSIS_PACKAGES))
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

    return MedicalAnalysisContract(
        study_archetype=study_archetype,
        endpoint_type=endpoint_type,
        submission_target_family=submission_target_family,
        required_analysis_packages=ANALYSIS_PACKAGES[study_archetype],
        required_reporting_items=("paper_experiment_matrix", "derived_analysis_manifest"),
        forbidden_default_routes=("figure_by_figure_results_narration",),
    )
