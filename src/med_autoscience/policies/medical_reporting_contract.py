from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MedicalReportingContract:
    reporting_guideline_family: str
    cohort_flow_required: bool
    baseline_characteristics_required: bool
    table_shell_requirements: tuple[str, ...]
    figure_shell_requirements: tuple[str, ...]


SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES: dict[str, str] = {
    "prediction_model": "TRIPOD",
    "clinical_observation": "STROBE",
    "randomized_trial": "CONSORT",
}
SUPPORTED_STUDY_ARCHETYPES = ("clinical_classifier",)
SUPPORTED_ENDPOINT_TYPES = ("binary", "time_to_event")
SUPPORTED_SUBMISSION_TARGET_FAMILIES = ("general_medical_journal",)


def resolve_medical_reporting_contract(
    *,
    study_archetype: str,
    manuscript_family: str,
    endpoint_type: str | None = None,
    submission_target_family: str,
) -> MedicalReportingContract:
    if study_archetype not in SUPPORTED_STUDY_ARCHETYPES:
        supported = ", ".join(SUPPORTED_STUDY_ARCHETYPES)
        raise ValueError(
            f"Unsupported study_archetype {study_archetype}. Supported: {supported}"
        )
    if submission_target_family not in SUPPORTED_SUBMISSION_TARGET_FAMILIES:
        supported = ", ".join(SUPPORTED_SUBMISSION_TARGET_FAMILIES)
        raise ValueError(
            f"Unsupported submission_target_family {submission_target_family}. Supported: {supported}"
        )
    if endpoint_type is not None and endpoint_type not in SUPPORTED_ENDPOINT_TYPES:
        supported = ", ".join(SUPPORTED_ENDPOINT_TYPES)
        raise ValueError(
            f"Unsupported endpoint_type {endpoint_type}. Supported: {supported}"
        )
    try:
        guideline = SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES[manuscript_family]
    except KeyError as exc:
        supported = ", ".join(sorted(SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES))
        raise ValueError(
            f"Unsupported manuscript_family {manuscript_family}. Supported: {supported}"
        ) from exc

    table_shell_requirements = ("table1_baseline_characteristics",)
    figure_shell_requirements = ("cohort_flow_figure",)
    if (
        study_archetype == "clinical_classifier"
        and manuscript_family == "prediction_model"
        and endpoint_type == "time_to_event"
        and submission_target_family == "general_medical_journal"
    ):
        table_shell_requirements = (
            "table1_baseline_characteristics",
            "table2_primary_performance_by_horizon",
        )
        figure_shell_requirements = (
            "cohort_flow_figure",
            "discrimination_calibration_figure",
            "km_risk_stratification_figure",
            "decision_curve_figure",
        )

    return MedicalReportingContract(
        reporting_guideline_family=guideline,
        cohort_flow_required=True,
        baseline_characteristics_required=True,
        table_shell_requirements=table_shell_requirements,
        figure_shell_requirements=figure_shell_requirements,
    )
