from __future__ import annotations

from .shared import Any, Path, _evidence_payload_path, display_registry, load_json
from .validation_atlas_primary import _validate_atlas_spatial_bridge_display_payload, _validate_celltype_signature_heatmap_display_payload, _validate_embedding_display_payload, _validate_single_cell_atlas_overview_display_payload
from .validation_atlas_storyboards import _validate_atlas_spatial_trajectory_context_support_display_payload, _validate_atlas_spatial_trajectory_density_coverage_display_payload, _validate_atlas_spatial_trajectory_multimanifold_context_support_display_payload, _validate_atlas_spatial_trajectory_storyboard_display_payload
from .validation_atlas_trajectory import _validate_spatial_niche_map_display_payload, _validate_trajectory_progression_display_payload
from .validation_curves_extended import _validate_model_complexity_audit_display_payload, _validate_time_to_event_discrimination_calibration_display_payload, _validate_time_to_event_display_payload, _validate_time_to_event_landmark_performance_display_payload, _validate_time_to_event_multihorizon_calibration_display_payload, _validate_time_to_event_stratified_cumulative_incidence_display_payload, _validate_time_to_event_threshold_governance_display_payload
from .validation_curves_primary import _validate_binary_calibration_decision_curve_display_payload, _validate_binary_curve_display_payload, _validate_risk_layering_display_payload, _validate_time_dependent_roc_comparison_display_payload, _validate_time_to_event_decision_curve_display_payload
from .validation_effects import _validate_broader_heterogeneity_summary_panel_display_payload, _validate_coefficient_path_panel_display_payload, _validate_compact_effect_estimate_panel_display_payload, _validate_forest_display_payload, _validate_interaction_effect_summary_panel_display_payload
from .validation_generalizability import _validate_center_transportability_governance_summary_panel_display_payload, _validate_generalizability_subgroup_composite_display_payload, _validate_multicenter_generalizability_display_payload
from .validation_omics_genomic import _validate_genomic_alteration_consequence_panel_display_payload, _validate_genomic_alteration_landscape_panel_display_payload, _validate_genomic_alteration_multiomic_consequence_panel_display_payload, _validate_genomic_alteration_pathway_integrated_composite_panel_display_payload, _validate_genomic_program_governance_summary_panel_display_payload, _validate_omics_volcano_panel_display_payload
from .validation_omics_heatmaps import _validate_clustered_heatmap_display_payload, _validate_confusion_matrix_heatmap_binary_display_payload, _validate_gsva_ssgsea_heatmap_display_payload, _validate_heatmap_display_payload, _validate_performance_heatmap_display_payload
from .validation_omics_panels import _validate_celltype_marker_dotplot_panel_display_payload, _validate_cnv_recurrence_summary_panel_display_payload, _validate_oncoplot_mutation_landscape_panel_display_payload, _validate_pathway_enrichment_dotplot_panel_display_payload
from .validation_response_primary import _validate_partial_dependence_ice_panel_display_payload, _validate_partial_dependence_interaction_contour_panel_display_payload
from .validation_response_secondary import _validate_accumulated_local_effects_panel_display_payload, _validate_partial_dependence_interaction_slice_panel_display_payload, _validate_partial_dependence_subgroup_comparison_panel_display_payload
from .validation_shap_importance import _validate_shap_bar_importance_display_payload, _validate_shap_multicohort_importance_panel_display_payload, _validate_shap_signed_importance_panel_display_payload
from .validation_shap_paths import _validate_shap_grouped_decision_path_panel_display_payload, _validate_shap_multigroup_decision_path_panel_display_payload
from .validation_shap_summary import _validate_shap_dependence_panel_display_payload, _validate_shap_force_like_summary_panel_display_payload, _validate_shap_grouped_local_explanation_panel_display_payload, _validate_shap_summary_display_payload, _validate_shap_waterfall_local_explanation_panel_display_payload
from .validation_support_domain import _validate_feature_response_support_domain_panel_display_payload, _validate_shap_grouped_local_support_domain_panel_display_payload, _validate_shap_multigroup_decision_path_support_domain_panel_display_payload, _validate_shap_signed_importance_local_support_domain_panel_display_payload

def _load_evidence_display_payload(
    *,
    paper_root: Path,
    spec: display_registry.EvidenceFigureSpec,
    display_id: str,
) -> tuple[Path, dict[str, Any]]:
    payload_path = _evidence_payload_path(paper_root=paper_root, input_schema_id=spec.input_schema_id)
    payload = load_json(payload_path)
    if str(payload.get("input_schema_id") or "").strip() != spec.input_schema_id:
        raise ValueError(f"{payload_path.name} must declare input_schema_id `{spec.input_schema_id}`")
    displays = payload.get("displays")
    if not isinstance(displays, list) or not displays:
        raise ValueError(f"{payload_path.name} must contain a non-empty displays list")
    matched_display: dict[str, Any] | None = None
    for index, item in enumerate(displays):
        if not isinstance(item, dict):
            raise ValueError(f"{payload_path.name} displays[{index}] must be an object")
        if str(item.get("display_id") or "").strip() == display_id:
            matched_display = item
            break
    if matched_display is None:
        raise ValueError(f"{payload_path.name} does not define display `{display_id}` for template `{spec.template_id}`")

    if spec.input_schema_id == "binary_prediction_curve_inputs_v1":
        return payload_path, _validate_binary_curve_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_dependent_roc_comparison_inputs_v1":
        return payload_path, _validate_time_dependent_roc_comparison_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "risk_layering_monotonic_inputs_v1":
        return payload_path, _validate_risk_layering_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "binary_calibration_decision_curve_panel_inputs_v1":
        return payload_path, _validate_binary_calibration_decision_curve_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "model_complexity_audit_panel_inputs_v1":
        return payload_path, _validate_model_complexity_audit_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_landmark_performance_inputs_v1":
        return payload_path, _validate_time_to_event_landmark_performance_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_threshold_governance_inputs_v1":
        return payload_path, _validate_time_to_event_threshold_governance_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_multihorizon_calibration_inputs_v1":
        return payload_path, _validate_time_to_event_multihorizon_calibration_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_grouped_inputs_v1":
        return payload_path, _validate_time_to_event_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_stratified_cumulative_incidence_inputs_v1":
        return payload_path, _validate_time_to_event_stratified_cumulative_incidence_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_discrimination_calibration_inputs_v1":
        return payload_path, _validate_time_to_event_discrimination_calibration_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "time_to_event_decision_curve_inputs_v1":
        return payload_path, _validate_time_to_event_decision_curve_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "embedding_grouped_inputs_v1":
        return payload_path, _validate_embedding_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "celltype_signature_heatmap_inputs_v1":
        return payload_path, _validate_celltype_signature_heatmap_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "single_cell_atlas_overview_inputs_v1":
        return payload_path, _validate_single_cell_atlas_overview_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "atlas_spatial_bridge_panel_inputs_v1":
        return payload_path, _validate_atlas_spatial_bridge_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "spatial_niche_map_inputs_v1":
        return payload_path, _validate_spatial_niche_map_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "trajectory_progression_inputs_v1":
        return payload_path, _validate_trajectory_progression_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "atlas_spatial_trajectory_storyboard_inputs_v1":
        return payload_path, _validate_atlas_spatial_trajectory_storyboard_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "atlas_spatial_trajectory_density_coverage_panel_inputs_v1":
        return payload_path, _validate_atlas_spatial_trajectory_density_coverage_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "atlas_spatial_trajectory_context_support_panel_inputs_v1":
        return payload_path, _validate_atlas_spatial_trajectory_context_support_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1":
        return payload_path, _validate_atlas_spatial_trajectory_multimanifold_context_support_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id in {"heatmap_group_comparison_inputs_v1", "correlation_heatmap_inputs_v1"}:
        return payload_path, _validate_heatmap_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "performance_heatmap_inputs_v1":
        return payload_path, _validate_performance_heatmap_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "confusion_matrix_heatmap_binary_inputs_v1":
        return payload_path, _validate_confusion_matrix_heatmap_binary_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "clustered_heatmap_inputs_v1":
        return payload_path, _validate_clustered_heatmap_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "gsva_ssgsea_heatmap_inputs_v1":
        return payload_path, _validate_gsva_ssgsea_heatmap_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "pathway_enrichment_dotplot_panel_inputs_v1":
        return payload_path, _validate_pathway_enrichment_dotplot_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "celltype_marker_dotplot_panel_inputs_v1":
        return payload_path, _validate_celltype_marker_dotplot_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "oncoplot_mutation_landscape_panel_inputs_v1":
        return payload_path, _validate_oncoplot_mutation_landscape_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "cnv_recurrence_summary_panel_inputs_v1":
        return payload_path, _validate_cnv_recurrence_summary_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "genomic_alteration_landscape_panel_inputs_v1":
        return payload_path, _validate_genomic_alteration_landscape_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "genomic_alteration_consequence_panel_inputs_v1":
        return payload_path, _validate_genomic_alteration_consequence_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "genomic_alteration_multiomic_consequence_panel_inputs_v1":
        return payload_path, _validate_genomic_alteration_multiomic_consequence_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "genomic_alteration_pathway_integrated_composite_panel_inputs_v1":
        return payload_path, _validate_genomic_alteration_pathway_integrated_composite_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "genomic_program_governance_summary_panel_inputs_v1":
        return payload_path, _validate_genomic_program_governance_summary_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "omics_volcano_panel_inputs_v1":
        return payload_path, _validate_omics_volcano_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "forest_effect_inputs_v1":
        return payload_path, _validate_forest_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "compact_effect_estimate_panel_inputs_v1":
        return payload_path, _validate_compact_effect_estimate_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "coefficient_path_panel_inputs_v1":
        return payload_path, _validate_coefficient_path_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "broader_heterogeneity_summary_panel_inputs_v1":
        return payload_path, _validate_broader_heterogeneity_summary_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "interaction_effect_summary_panel_inputs_v1":
        return payload_path, _validate_interaction_effect_summary_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "center_transportability_governance_summary_panel_inputs_v1":
        return payload_path, _validate_center_transportability_governance_summary_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_summary_inputs_v1":
        return payload_path, _validate_shap_summary_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_dependence_panel_inputs_v1":
        return payload_path, _validate_shap_dependence_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_waterfall_local_explanation_panel_inputs_v1":
        return payload_path, _validate_shap_waterfall_local_explanation_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_force_like_summary_panel_inputs_v1":
        return payload_path, _validate_shap_force_like_summary_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_grouped_local_explanation_panel_inputs_v1":
        return payload_path, _validate_shap_grouped_local_explanation_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_grouped_decision_path_panel_inputs_v1":
        return payload_path, _validate_shap_grouped_decision_path_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_multigroup_decision_path_panel_inputs_v1":
        return payload_path, _validate_shap_multigroup_decision_path_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_bar_importance_inputs_v1":
        return payload_path, _validate_shap_bar_importance_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_signed_importance_panel_inputs_v1":
        return payload_path, _validate_shap_signed_importance_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_multicohort_importance_panel_inputs_v1":
        return payload_path, _validate_shap_multicohort_importance_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "partial_dependence_ice_panel_inputs_v1":
        return payload_path, _validate_partial_dependence_ice_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "partial_dependence_interaction_contour_panel_inputs_v1":
        return payload_path, _validate_partial_dependence_interaction_contour_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "partial_dependence_interaction_slice_panel_inputs_v1":
        return payload_path, _validate_partial_dependence_interaction_slice_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "partial_dependence_subgroup_comparison_panel_inputs_v1":
        return payload_path, _validate_partial_dependence_subgroup_comparison_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "accumulated_local_effects_panel_inputs_v1":
        return payload_path, _validate_accumulated_local_effects_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "feature_response_support_domain_panel_inputs_v1":
        return payload_path, _validate_feature_response_support_domain_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_grouped_local_support_domain_panel_inputs_v1":
        return payload_path, _validate_shap_grouped_local_support_domain_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_multigroup_decision_path_support_domain_panel_inputs_v1":
        return payload_path, _validate_shap_multigroup_decision_path_support_domain_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "shap_signed_importance_local_support_domain_panel_inputs_v1":
        return payload_path, _validate_shap_signed_importance_local_support_domain_panel_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "multicenter_generalizability_inputs_v1":
        return payload_path, _validate_multicenter_generalizability_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    if spec.input_schema_id == "generalizability_subgroup_composite_inputs_v1":
        return payload_path, _validate_generalizability_subgroup_composite_display_payload(
            path=payload_path,
            payload=matched_display,
            expected_template_id=spec.template_id,
            expected_display_id=display_id,
        )
    raise ValueError(f"unsupported evidence input schema `{spec.input_schema_id}`")


__all__ = [
    "_load_evidence_display_payload",
]
