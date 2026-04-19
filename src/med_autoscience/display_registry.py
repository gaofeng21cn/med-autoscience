from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TypeVar

from med_autoscience.display_pack_contract import DisplayTemplateManifest
from med_autoscience.display_pack_loader import load_enabled_local_display_pack_templates
from med_autoscience.display_pack_resolver import split_full_template_id


_CORE_DISPLAY_PACK_ID = "fenggaolab.org.medical-display-core"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_T = TypeVar("_T")


def _full_id(short_id: str) -> str:
    return f"{_CORE_DISPLAY_PACK_ID}::{short_id}"


_EVIDENCE_TEMPLATE_ORDER = tuple(
    _full_id(item)
    for item in (
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "risk_layering_monotonic_bars",
        "binary_calibration_decision_curve_panel",
        "model_complexity_audit_panel",
        "time_dependent_roc_horizon",
        "time_dependent_roc_comparison_panel",
        "time_to_event_landmark_performance_panel",
        "time_to_event_threshold_governance_panel",
        "time_to_event_multihorizon_calibration_panel",
        "kaplan_meier_grouped",
        "cumulative_incidence_grouped",
        "time_to_event_stratified_cumulative_incidence_panel",
        "umap_scatter_grouped",
        "pca_scatter_grouped",
        "tsne_scatter_grouped",
        "celltype_signature_heatmap",
        "single_cell_atlas_overview_panel",
        "atlas_spatial_bridge_panel",
        "spatial_niche_map_panel",
        "trajectory_progression_panel",
        "atlas_spatial_trajectory_storyboard_panel",
        "atlas_spatial_trajectory_density_coverage_panel",
        "atlas_spatial_trajectory_context_support_panel",
        "omics_volcano_panel",
        "heatmap_group_comparison",
        "performance_heatmap",
        "correlation_heatmap",
        "clustered_heatmap",
        "gsva_ssgsea_heatmap",
        "pathway_enrichment_dotplot_panel",
        "oncoplot_mutation_landscape_panel",
        "cnv_recurrence_summary_panel",
        "genomic_alteration_landscape_panel",
        "forest_effect_main",
        "subgroup_forest",
        "generalizability_subgroup_composite_panel",
        "compact_effect_estimate_panel",
        "coefficient_path_panel",
        "broader_heterogeneity_summary_panel",
        "center_transportability_governance_summary_panel",
        "shap_summary_beeswarm",
        "shap_bar_importance",
        "shap_signed_importance_panel",
        "shap_multicohort_importance_panel",
        "shap_dependence_panel",
        "shap_waterfall_local_explanation_panel",
        "shap_force_like_summary_panel",
        "shap_grouped_local_explanation_panel",
        "shap_grouped_decision_path_panel",
        "shap_multigroup_decision_path_panel",
        "partial_dependence_ice_panel",
        "partial_dependence_interaction_contour_panel",
        "partial_dependence_interaction_slice_panel",
        "partial_dependence_subgroup_comparison_panel",
        "accumulated_local_effects_panel",
        "feature_response_support_domain_panel",
        "shap_grouped_local_support_domain_panel",
        "time_to_event_discrimination_calibration_panel",
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
        "treatment_shift_alignment_figure",
        "practical_factor_dot_figure",
        "preferred_class_sensitivity_figure",
    )
)
_ILLUSTRATION_SHELL_ORDER = tuple(
    _full_id(item)
    for item in (
        "cohort_flow_figure",
        "submission_graphical_abstract",
        "workflow_fact_sheet_panel",
        "design_evidence_composite_shell",
        "baseline_missingness_qc_panel",
        "center_coverage_batch_transportability_panel",
        "transportability_recalibration_governance_panel",
    )
)
_TABLE_SHELL_ORDER = tuple(
    _full_id(item)
    for item in (
        "table1_baseline_characteristics",
        "table2_time_to_event_performance_summary",
        "table3_clinical_interpretation_summary",
        "performance_summary_table_generic",
        "grouped_risk_event_summary_table",
    )
)
_SEMANTIC_REGISTRY_ID_ALIASES = {
    _full_id("local_architecture_overview_figure"): _full_id("risk_layering_monotonic_bars"),
}


def _canonicalize_registry_id(identifier: str) -> str:
    normalized = str(identifier or "").strip()
    if not normalized:
        return normalized
    if "::" in normalized:
        pack_id, short_id = split_full_template_id(normalized)
        canonical = f"{pack_id}::{short_id}"
    else:
        canonical = _full_id(normalized)
    return _SEMANTIC_REGISTRY_ID_ALIASES.get(canonical, canonical)


@dataclass(frozen=True)
class EvidenceFigureSpec:
    template_id: str
    display_name: str
    evidence_class: str
    paper_family_ids: tuple[str, ...]
    renderer_family: str
    input_schema_id: str
    layout_qc_profile: str
    required_exports: tuple[str, ...]
    allowed_paper_roles: tuple[str, ...] = ("main_text", "supplementary")
    paper_proven: bool = False


@dataclass(frozen=True)
class IllustrationShellSpec:
    shell_id: str
    display_name: str
    paper_family_ids: tuple[str, ...]
    renderer_family: str
    input_schema_id: str
    shell_qc_profile: str
    required_exports: tuple[str, ...]
    allowed_paper_roles: tuple[str, ...] = ("main_text",)
    paper_proven: bool = False


@dataclass(frozen=True)
class TableShellSpec:
    shell_id: str
    display_name: str
    paper_family_ids: tuple[str, ...]
    input_schema_id: str
    table_qc_profile: str
    required_exports: tuple[str, ...]
    allowed_paper_roles: tuple[str, ...] = ("main_text", "supplementary")
    paper_proven: bool = False


_PAPER_FAMILY_LABELS: dict[str, str] = {
    "A": "A. Predictive Performance and Decision",
    "B": "B. Survival and Time-to-Event",
    "C": "C. Effect Size and Heterogeneity",
    "D": "D. Representation Structure and Data Geometry",
    "E": "E. Feature Pattern and Matrix",
    "F": "F. Model Explanation",
    "G": "G. Bioinformatics and Omics Evidence",
    "H": "H. Cohort and Study Design Evidence",
}


def _build_evidence_figure_spec(manifest: DisplayTemplateManifest) -> EvidenceFigureSpec:
    return EvidenceFigureSpec(
        template_id=manifest.full_template_id,
        display_name=manifest.display_name,
        evidence_class=manifest.display_class_id,
        paper_family_ids=manifest.paper_family_ids,
        renderer_family=manifest.renderer_family,
        input_schema_id=manifest.input_schema_ref,
        layout_qc_profile=manifest.qc_profile_ref,
        required_exports=manifest.required_exports,
        allowed_paper_roles=manifest.allowed_paper_roles,
        paper_proven=manifest.paper_proven,
    )


def _build_illustration_shell_spec(manifest: DisplayTemplateManifest) -> IllustrationShellSpec:
    return IllustrationShellSpec(
        shell_id=manifest.full_template_id,
        display_name=manifest.display_name,
        paper_family_ids=manifest.paper_family_ids,
        renderer_family=manifest.renderer_family,
        input_schema_id=manifest.input_schema_ref,
        shell_qc_profile=manifest.qc_profile_ref,
        required_exports=manifest.required_exports,
        allowed_paper_roles=manifest.allowed_paper_roles,
        paper_proven=manifest.paper_proven,
    )


def _build_table_shell_spec(manifest: DisplayTemplateManifest) -> TableShellSpec:
    return TableShellSpec(
        shell_id=manifest.full_template_id,
        display_name=manifest.display_name,
        paper_family_ids=manifest.paper_family_ids,
        input_schema_id=manifest.input_schema_ref,
        table_qc_profile=manifest.qc_profile_ref,
        required_exports=manifest.required_exports,
        allowed_paper_roles=manifest.allowed_paper_roles,
        paper_proven=manifest.paper_proven,
    )


def _sort_items_by_stable_order(
    items: list[_T],
    *,
    order: tuple[str, ...],
    key: str,
) -> tuple[_T, ...]:
    order_index = {item: index for index, item in enumerate(order)}
    return tuple(
        sorted(
            items,
            key=lambda item: (
                order_index.get(getattr(item, key), len(order)),
                getattr(item, key),
            ),
        )
    )


@lru_cache(maxsize=1)
def _active_template_manifests() -> tuple[DisplayTemplateManifest, ...]:
    return tuple(load_enabled_local_display_pack_templates(_REPO_ROOT))


@lru_cache(maxsize=1)
def _active_registry_state() -> tuple[
    tuple[EvidenceFigureSpec, ...],
    tuple[IllustrationShellSpec, ...],
    tuple[TableShellSpec, ...],
    dict[str, EvidenceFigureSpec],
    dict[str, IllustrationShellSpec],
    dict[str, TableShellSpec],
]:
    evidence_specs: list[EvidenceFigureSpec] = []
    illustration_specs: list[IllustrationShellSpec] = []
    table_specs: list[TableShellSpec] = []

    for manifest in _active_template_manifests():
        if manifest.kind == "evidence_figure":
            evidence_specs.append(_build_evidence_figure_spec(manifest))
            continue
        if manifest.kind == "illustration_shell":
            illustration_specs.append(_build_illustration_shell_spec(manifest))
            continue
        if manifest.kind == "table_shell":
            table_specs.append(_build_table_shell_spec(manifest))
            continue
        raise ValueError(f"unsupported template kind `{manifest.kind}`")

    evidence_specs_tuple = _sort_items_by_stable_order(
        evidence_specs,
        order=_EVIDENCE_TEMPLATE_ORDER,
        key="template_id",
    )
    illustration_specs_tuple = _sort_items_by_stable_order(
        illustration_specs,
        order=_ILLUSTRATION_SHELL_ORDER,
        key="shell_id",
    )
    table_specs_tuple = _sort_items_by_stable_order(
        table_specs,
        order=_TABLE_SHELL_ORDER,
        key="shell_id",
    )

    return (
        evidence_specs_tuple,
        illustration_specs_tuple,
        table_specs_tuple,
        {item.template_id: item for item in evidence_specs_tuple},
        {item.shell_id: item for item in illustration_specs_tuple},
        {item.shell_id: item for item in table_specs_tuple},
    )


def list_evidence_figure_specs() -> tuple[EvidenceFigureSpec, ...]:
    evidence_specs, _, _, _, _, _ = _active_registry_state()
    return evidence_specs


def list_illustration_shell_specs() -> tuple[IllustrationShellSpec, ...]:
    _, illustration_specs, _, _, _, _ = _active_registry_state()
    return illustration_specs


def list_table_shell_specs() -> tuple[TableShellSpec, ...]:
    _, _, table_specs, _, _, _ = _active_registry_state()
    return table_specs


def get_paper_family_label(paper_family_id: str) -> str:
    normalized = str(paper_family_id or "").strip()
    try:
        return _PAPER_FAMILY_LABELS[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown paper family `{paper_family_id}`") from exc


def get_evidence_figure_spec(template_id: str) -> EvidenceFigureSpec:
    normalized = _canonicalize_registry_id(template_id)
    _, _, _, evidence_by_template, _, _ = _active_registry_state()
    try:
        return evidence_by_template[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown evidence figure template `{template_id}`") from exc


def get_illustration_shell_spec(shell_id: str) -> IllustrationShellSpec:
    normalized = _canonicalize_registry_id(shell_id)
    _, _, _, _, illustration_by_shell, _ = _active_registry_state()
    try:
        return illustration_by_shell[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown illustration shell `{shell_id}`") from exc


def get_table_shell_spec(shell_id: str) -> TableShellSpec:
    normalized = _canonicalize_registry_id(shell_id)
    _, _, _, _, _, table_by_shell = _active_registry_state()
    try:
        return table_by_shell[normalized]
    except KeyError as exc:
        raise ValueError(f"unknown table shell `{shell_id}`") from exc


def is_evidence_figure_template(template_id: str) -> bool:
    normalized = _canonicalize_registry_id(template_id)
    _, _, _, evidence_by_template, _, _ = _active_registry_state()
    return normalized in evidence_by_template


def is_illustration_shell(shell_id: str) -> bool:
    normalized = _canonicalize_registry_id(shell_id)
    _, _, _, _, illustration_by_shell, _ = _active_registry_state()
    return normalized in illustration_by_shell


def is_table_shell(shell_id: str) -> bool:
    normalized = _canonicalize_registry_id(shell_id)
    _, _, _, _, _, table_by_shell = _active_registry_state()
    return normalized in table_by_shell
