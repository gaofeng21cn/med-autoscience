from __future__ import annotations

from pathlib import Path
from typing import Any

from ..shared import _require_namespaced_registry_id
from .atlas_geometry import (
    _render_python_atlas_spatial_bridge_panel,
    _render_python_atlas_spatial_trajectory_context_support_panel,
    _render_python_atlas_spatial_trajectory_density_coverage_panel,
    _render_python_atlas_spatial_trajectory_multimanifold_context_support_panel,
    _render_python_atlas_spatial_trajectory_storyboard_panel,
    _render_python_celltype_signature_heatmap,
    _render_python_single_cell_atlas_overview_panel,
    _render_python_spatial_niche_map_panel,
    _render_python_trajectory_progression_panel,
)
from .clinical_time_to_event import (
    _render_python_binary_calibration_decision_curve_panel,
    _render_python_risk_layering_monotonic_bars,
    _render_python_time_dependent_roc_comparison_panel,
    _render_python_time_to_event_decision_curve,
    _render_python_time_to_event_discrimination_calibration_panel,
    _render_python_time_to_event_landmark_performance_panel,
    _render_python_time_to_event_multihorizon_calibration_panel,
    _render_python_time_to_event_risk_group_summary,
    _render_python_time_to_event_stratified_cumulative_incidence_panel,
    _render_python_time_to_event_threshold_governance_panel,
)
from .effect_generalizability import (
    _render_python_broader_heterogeneity_summary_panel,
    _render_python_center_transportability_governance_summary_panel,
    _render_python_coefficient_path_panel,
    _render_python_compact_effect_estimate_panel,
    _render_python_generalizability_subgroup_composite_panel,
    _render_python_interaction_effect_summary_panel,
    _render_python_multicenter_generalizability_overview,
)
from .model_explanation_composites import (
    _render_python_feature_response_support_domain_panel,
    _render_python_shap_grouped_local_support_domain_panel,
    _render_python_shap_multigroup_decision_path_support_domain_panel,
    _render_python_shap_signed_importance_local_support_domain_panel,
)
from .dpcc_primary_care import (
    _render_python_phenotype_gap_structure_figure,
    _render_python_site_held_out_stability_figure,
    _render_python_treatment_gap_alignment_figure,
)
from .model_explanation_response import (
    _render_python_accumulated_local_effects_panel,
    _render_python_partial_dependence_ice_panel,
    _render_python_partial_dependence_interaction_contour_panel,
    _render_python_partial_dependence_interaction_slice_panel,
    _render_python_partial_dependence_subgroup_comparison_panel,
)
from .model_explanation_shap import (
    _render_python_model_complexity_audit_panel,
    _render_python_shap_bar_importance,
    _render_python_shap_dependence_panel,
    _render_python_shap_force_like_summary_panel,
    _render_python_shap_grouped_decision_path_panel,
    _render_python_shap_grouped_local_explanation_panel,
    _render_python_shap_multicohort_importance_panel,
    _render_python_shap_multigroup_decision_path_panel,
    _render_python_shap_signed_importance_panel,
    _render_python_shap_summary_beeswarm,
    _render_python_shap_waterfall_local_explanation_panel,
)
from .omics_matrix import (
    _render_python_celltype_marker_dotplot_panel,
    _render_python_cnv_recurrence_summary_panel,
    _render_python_genomic_alteration_consequence_panel,
    _render_python_genomic_alteration_landscape_panel,
    _render_python_genomic_alteration_pathway_integrated_composite_panel,
    _render_python_genomic_program_governance_summary_panel,
    _render_python_omics_volcano_panel,
    _render_python_oncoplot_mutation_landscape_panel,
    _render_python_pathway_enrichment_dotplot_panel,
)
_PYTHON_EVIDENCE_RENDERERS = {
    "binary_calibration_decision_curve_panel": _render_python_binary_calibration_decision_curve_panel,
    "celltype_signature_heatmap": _render_python_celltype_signature_heatmap,
    "compact_effect_estimate_panel": _render_python_compact_effect_estimate_panel,
    "coefficient_path_panel": _render_python_coefficient_path_panel,
    "broader_heterogeneity_summary_panel": _render_python_broader_heterogeneity_summary_panel,
    "phenotype_gap_structure_figure": _render_python_phenotype_gap_structure_figure,
    "site_held_out_stability_figure": _render_python_site_held_out_stability_figure,
    "treatment_gap_alignment_figure": _render_python_treatment_gap_alignment_figure,
    "interaction_effect_summary_panel": _render_python_interaction_effect_summary_panel,
    "center_transportability_governance_summary_panel": _render_python_center_transportability_governance_summary_panel,
    "generalizability_subgroup_composite_panel": _render_python_generalizability_subgroup_composite_panel,
    "model_complexity_audit_panel": _render_python_model_complexity_audit_panel,
    "single_cell_atlas_overview_panel": _render_python_single_cell_atlas_overview_panel,
    "pathway_enrichment_dotplot_panel": _render_python_pathway_enrichment_dotplot_panel,
    "celltype_marker_dotplot_panel": _render_python_celltype_marker_dotplot_panel,
    "oncoplot_mutation_landscape_panel": _render_python_oncoplot_mutation_landscape_panel,
    "cnv_recurrence_summary_panel": _render_python_cnv_recurrence_summary_panel,
    "genomic_alteration_landscape_panel": _render_python_genomic_alteration_landscape_panel,
    "genomic_alteration_consequence_panel": _render_python_genomic_alteration_consequence_panel,
    "genomic_alteration_multiomic_consequence_panel": _render_python_genomic_alteration_consequence_panel,
    "genomic_alteration_pathway_integrated_composite_panel": _render_python_genomic_alteration_pathway_integrated_composite_panel,
    "genomic_program_governance_summary_panel": _render_python_genomic_program_governance_summary_panel,
    "omics_volcano_panel": _render_python_omics_volcano_panel,
    "atlas_spatial_bridge_panel": _render_python_atlas_spatial_bridge_panel,
    "spatial_niche_map_panel": _render_python_spatial_niche_map_panel,
    "trajectory_progression_panel": _render_python_trajectory_progression_panel,
    "atlas_spatial_trajectory_storyboard_panel": _render_python_atlas_spatial_trajectory_storyboard_panel,
    "atlas_spatial_trajectory_density_coverage_panel": _render_python_atlas_spatial_trajectory_density_coverage_panel,
    "atlas_spatial_trajectory_context_support_panel": _render_python_atlas_spatial_trajectory_context_support_panel,
    "atlas_spatial_trajectory_multimanifold_context_support_panel": _render_python_atlas_spatial_trajectory_multimanifold_context_support_panel,
    "risk_layering_monotonic_bars": _render_python_risk_layering_monotonic_bars,
    "shap_dependence_panel": _render_python_shap_dependence_panel,
    "shap_summary_beeswarm": _render_python_shap_summary_beeswarm,
    "shap_bar_importance": _render_python_shap_bar_importance,
    "shap_signed_importance_panel": _render_python_shap_signed_importance_panel,
    "shap_multicohort_importance_panel": _render_python_shap_multicohort_importance_panel,
    "shap_force_like_summary_panel": _render_python_shap_force_like_summary_panel,
    "shap_grouped_local_explanation_panel": _render_python_shap_grouped_local_explanation_panel,
    "shap_grouped_decision_path_panel": _render_python_shap_grouped_decision_path_panel,
    "shap_multigroup_decision_path_panel": _render_python_shap_multigroup_decision_path_panel,
    "partial_dependence_ice_panel": _render_python_partial_dependence_ice_panel,
    "partial_dependence_interaction_contour_panel": _render_python_partial_dependence_interaction_contour_panel,
    "partial_dependence_interaction_slice_panel": _render_python_partial_dependence_interaction_slice_panel,
    "partial_dependence_subgroup_comparison_panel": _render_python_partial_dependence_subgroup_comparison_panel,
    "accumulated_local_effects_panel": _render_python_accumulated_local_effects_panel,
    "feature_response_support_domain_panel": _render_python_feature_response_support_domain_panel,
    "shap_grouped_local_support_domain_panel": _render_python_shap_grouped_local_support_domain_panel,
    "shap_multigroup_decision_path_support_domain_panel": _render_python_shap_multigroup_decision_path_support_domain_panel,
    "shap_signed_importance_local_support_domain_panel": _render_python_shap_signed_importance_local_support_domain_panel,
    "shap_waterfall_local_explanation_panel": _render_python_shap_waterfall_local_explanation_panel,
    "time_dependent_roc_comparison_panel": _render_python_time_dependent_roc_comparison_panel,
    "time_to_event_landmark_performance_panel": _render_python_time_to_event_landmark_performance_panel,
    "time_to_event_multihorizon_calibration_panel": _render_python_time_to_event_multihorizon_calibration_panel,
    "time_to_event_threshold_governance_panel": _render_python_time_to_event_threshold_governance_panel,
    "time_to_event_stratified_cumulative_incidence_panel": _render_python_time_to_event_stratified_cumulative_incidence_panel,
    "time_to_event_risk_group_summary": _render_python_time_to_event_risk_group_summary,
    "time_to_event_decision_curve": _render_python_time_to_event_decision_curve,
    "time_to_event_discrimination_calibration_panel": _render_python_time_to_event_discrimination_calibration_panel,
    "multicenter_generalizability_overview": _render_python_multicenter_generalizability_overview,
}


def render_python_evidence_figure(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    _, template_short_id = _require_namespaced_registry_id(template_id, label="template_id")
    try:
        renderer = _PYTHON_EVIDENCE_RENDERERS[template_short_id]
    except KeyError as exc:
        raise RuntimeError(f"unsupported python evidence template `{template_id}`") from exc
    renderer(
        template_id=template_short_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )
