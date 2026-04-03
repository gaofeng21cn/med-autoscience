from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DisplayShellPlanItem:
    display_id: str
    display_kind: str
    requirement_key: str
    catalog_id: str


@dataclass(frozen=True)
class MedicalReportingContract:
    reporting_guideline_family: str
    cohort_flow_required: bool
    baseline_characteristics_required: bool
    table_shell_requirements: tuple[str, ...]
    figure_shell_requirements: tuple[str, ...]
    required_illustration_shells: tuple[str, ...]
    required_table_shells: tuple[str, ...]
    required_evidence_templates: tuple[str, ...]
    display_registry_required: bool
    display_shell_plan: tuple[DisplayShellPlanItem, ...]


SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES: dict[str, str] = {
    "prediction_model": "TRIPOD",
    "clinical_observation": "STROBE",
    "randomized_trial": "CONSORT",
}
SUPPORTED_STUDY_ARCHETYPES = ("clinical_classifier",)
SUPPORTED_ENDPOINT_TYPES = ("binary", "time_to_event")
SUPPORTED_SUBMISSION_TARGET_FAMILIES = ("general_medical_journal",)
_DISPLAY_INSTANCE_MAP: dict[str, tuple[str, str, str]] = {
    "cohort_flow_figure": ("cohort_flow", "figure", "F1"),
    "table1_baseline_characteristics": ("baseline_characteristics", "table", "T1"),
    "table2_time_to_event_performance_summary": ("time_to_event_performance_summary", "table", "T2"),
    "time_to_event_discrimination_calibration_panel": ("discrimination_calibration", "figure", "F2"),
    "kaplan_meier_grouped": ("km_risk_stratification", "figure", "F3"),
    "time_to_event_decision_curve": ("decision_curve", "figure", "F4"),
}


def _build_display_shell_plan(
    *,
    figure_shell_requirements: tuple[str, ...],
    table_shell_requirements: tuple[str, ...],
) -> tuple[DisplayShellPlanItem, ...]:
    items: list[DisplayShellPlanItem] = []
    for requirement_key in figure_shell_requirements + table_shell_requirements:
        display_instance = _DISPLAY_INSTANCE_MAP.get(requirement_key)
        if display_instance is None:
            continue
        display_id, display_kind, catalog_id = display_instance
        items.append(
            DisplayShellPlanItem(
                display_id=display_id,
                display_kind=display_kind,
                requirement_key=requirement_key,
                catalog_id=catalog_id,
            )
        )
    return tuple(items)


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
            "table2_time_to_event_performance_summary",
        )
        figure_shell_requirements = (
            "cohort_flow_figure",
            "time_to_event_discrimination_calibration_panel",
            "kaplan_meier_grouped",
            "time_to_event_decision_curve",
        )

    return MedicalReportingContract(
        reporting_guideline_family=guideline,
        cohort_flow_required=True,
        baseline_characteristics_required=True,
        table_shell_requirements=table_shell_requirements,
        figure_shell_requirements=figure_shell_requirements,
        required_illustration_shells=tuple(
            item for item in figure_shell_requirements if item == "cohort_flow_figure"
        ),
        required_table_shells=table_shell_requirements,
        required_evidence_templates=(),
        display_registry_required=True,
        display_shell_plan=_build_display_shell_plan(
            figure_shell_requirements=figure_shell_requirements,
            table_shell_requirements=table_shell_requirements,
        ),
    )
