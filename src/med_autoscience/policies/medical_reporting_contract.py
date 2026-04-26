from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from med_autoscience.policies.medical_reporting_checklist import build_default_structured_reporting_contract


@dataclass(frozen=True)
class DisplayShellPlanItem:
    display_id: str
    display_kind: str
    requirement_key: str
    catalog_id: str
    story_role: str


@dataclass(frozen=True)
class DisplayBlueprintItem:
    catalog_id: str
    display_kind: str
    story_role: str
    narrative_purpose: str
    tier: str


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
    display_ambition: str
    minimum_main_text_figures: int
    recommended_main_text_figures: tuple[DisplayBlueprintItem, ...]
    structured_reporting_contract: dict[str, Any]


SUPPORTED_MANUSCRIPT_FAMILY_GUIDELINES: dict[str, str] = {
    "prediction_model": "TRIPOD",
    "clinical_observation": "STROBE",
    "randomized_trial": "CONSORT",
}
SUPPORTED_STUDY_ARCHETYPES = (
    "clinical_classifier",
    "clinical_subtype_reconstruction",
    "survey_trend_analysis",
)
SUPPORTED_ENDPOINT_TYPES = ("binary", "time_to_event", "descriptive")
SUPPORTED_SUBMISSION_TARGET_FAMILIES = ("general_medical_journal",)
_LEGACY_REQUIREMENT_KEY_ALIASES: dict[str, tuple[str, ...]] = {
    "time_to_event_risk_group_summary": ("kaplan_meier_grouped",),
}
_STUDY_SETUP_REQUIREMENT_KEYS = frozenset(
    {
        "cohort_flow_figure",
        "table1_baseline_characteristics",
    }
)
_DISPLAY_INSTANCE_MAP: dict[str, tuple[str, str, str]] = {
    "cohort_flow_figure": ("cohort_flow", "figure", "F1"),
    "table1_baseline_characteristics": ("baseline_characteristics", "table", "T1"),
    "phenotype_gap_structure_figure": ("phenotype_gap_structure", "figure", "F2"),
    "table2_phenotype_gap_summary": ("phenotype_gap_summary", "table", "T2"),
    "site_held_out_stability_figure": ("site_held_out_stability", "figure", "F3"),
    "table3_transition_site_support_summary": ("transition_site_support_summary", "table", "T3"),
    "treatment_gap_alignment_figure": ("treatment_gap_alignment", "figure", "F4"),
    "table2_time_to_event_performance_summary": ("time_to_event_performance_summary", "table", "T2"),
    "time_to_event_discrimination_calibration_panel": ("discrimination_calibration", "figure", "F2"),
    "time_to_event_risk_group_summary": ("km_risk_stratification", "figure", "F3"),
    "time_to_event_decision_curve": ("decision_curve", "figure", "F4"),
    "multicenter_generalizability_overview": ("multicenter_generalizability", "figure", "F5"),
}


def normalize_requirement_key(requirement_key: object) -> str:
    normalized = str(requirement_key or "").strip()
    if "::" in normalized:
        normalized = normalized.rsplit("::", 1)[-1]
    for canonical_key, aliases in _LEGACY_REQUIREMENT_KEY_ALIASES.items():
        if normalized in aliases:
            return canonical_key
    return normalized


def normalize_legacy_requirement_keys(payload: object) -> bool:
    if not isinstance(payload, dict):
        raise ValueError("medical_reporting_contract payload must be a JSON object")

    updated = False
    for key in ("figure_shell_requirements", "required_evidence_templates"):
        values = payload.get(key)
        if not isinstance(values, list):
            continue
        normalized_values = [normalize_requirement_key(value) for value in values]
        if normalized_values != values:
            payload[key] = normalized_values
            updated = True

    display_shell_plan = payload.get("display_shell_plan")
    if isinstance(display_shell_plan, list):
        for item in display_shell_plan:
            if not isinstance(item, dict):
                continue
            normalized_requirement_key = normalize_requirement_key(item.get("requirement_key"))
            if normalized_requirement_key and normalized_requirement_key != item.get("requirement_key"):
                item["requirement_key"] = normalized_requirement_key
                updated = True

    return updated


def display_story_role_for_requirement_key(requirement_key: object) -> str:
    normalized = normalize_requirement_key(requirement_key)
    if normalized in _STUDY_SETUP_REQUIREMENT_KEYS:
        return "study_setup"
    return "result_evidence"


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
                story_role=display_story_role_for_requirement_key(requirement_key),
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
    display_ambition = "baseline"
    minimum_main_text_figures = 1
    recommended_main_text_figures: tuple[DisplayBlueprintItem, ...] = ()
    if (
        study_archetype == "clinical_subtype_reconstruction"
        and manuscript_family == "clinical_observation"
        and endpoint_type == "descriptive"
        and submission_target_family == "general_medical_journal"
    ):
        table_shell_requirements = (
            "table1_baseline_characteristics",
            "table2_phenotype_gap_summary",
            "table3_transition_site_support_summary",
        )
        figure_shell_requirements = (
            "cohort_flow_figure",
            "phenotype_gap_structure_figure",
            "site_held_out_stability_figure",
            "treatment_gap_alignment_figure",
        )
        display_ambition = "strong"
        minimum_main_text_figures = 4
        recommended_main_text_figures = (
            DisplayBlueprintItem(
                catalog_id="F2",
                display_kind="figure",
                story_role="result_primary",
                narrative_purpose="phenotype_characterization_and_gap_structure",
                tier="core",
            ),
            DisplayBlueprintItem(
                catalog_id="F3",
                display_kind="figure",
                story_role="result_validation",
                narrative_purpose="site_held_out_reproducibility_or_assignment_stability",
                tier="core",
            ),
            DisplayBlueprintItem(
                catalog_id="F4",
                display_kind="figure",
                story_role="result_treatment",
                narrative_purpose="treatment_target_gap_alignment",
                tier="core",
            ),
        )
    elif (
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
            "time_to_event_risk_group_summary",
            "time_to_event_decision_curve",
            "multicenter_generalizability_overview",
        )
        display_ambition = "strong"
        minimum_main_text_figures = 4
    elif (
        study_archetype == "survey_trend_analysis"
        and manuscript_family == "clinical_observation"
        and endpoint_type == "descriptive"
        and submission_target_family == "general_medical_journal"
    ):
        display_ambition = "strong"
        minimum_main_text_figures = 4
        recommended_main_text_figures = (
            DisplayBlueprintItem(
                catalog_id="F2",
                display_kind="figure",
                story_role="result_primary",
                narrative_purpose="historical_to_current_patient_migration",
                tier="core",
            ),
            DisplayBlueprintItem(
                catalog_id="F3",
                display_kind="figure",
                story_role="result_alignment",
                narrative_purpose="clinician_surface_and_guideline_alignment",
                tier="core",
            ),
            DisplayBlueprintItem(
                catalog_id="F4",
                display_kind="figure",
                story_role="result_interpretive",
                narrative_purpose="divergence_decomposition_or_robustness",
                tier="core",
            ),
        )

    structured_reporting_contract = (
        build_default_structured_reporting_contract(
            study_archetype=study_archetype,
            manuscript_family=manuscript_family,
            endpoint_type=endpoint_type,
        )
        if manuscript_family == "prediction_model"
        else {}
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
        required_evidence_templates=tuple(
            item for item in figure_shell_requirements if item != "cohort_flow_figure"
        ),
        display_registry_required=True,
        display_shell_plan=_build_display_shell_plan(
            figure_shell_requirements=figure_shell_requirements,
            table_shell_requirements=table_shell_requirements,
        ),
        display_ambition=display_ambition,
        minimum_main_text_figures=minimum_main_text_figures,
        recommended_main_text_figures=recommended_main_text_figures,
        structured_reporting_contract=structured_reporting_contract,
    )
