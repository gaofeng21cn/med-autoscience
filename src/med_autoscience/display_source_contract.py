from __future__ import annotations


INPUT_FILENAME_BY_SCHEMA_ID: dict[str, str] = {
    "binary_prediction_curve_inputs_v1": "binary_prediction_curve_inputs.json",
    "time_to_event_discrimination_calibration_inputs_v1": "time_to_event_discrimination_calibration_inputs.json",
    "time_to_event_multihorizon_calibration_inputs_v1": "time_to_event_multihorizon_calibration_inputs.json",
    "time_to_event_grouped_inputs_v1": "time_to_event_grouped_inputs.json",
    "time_to_event_decision_curve_inputs_v1": "time_to_event_decision_curve_inputs.json",
    "risk_layering_monotonic_inputs_v1": "risk_layering_monotonic_inputs.json",
    "model_complexity_audit_panel_inputs_v1": "model_complexity_audit_panel_inputs.json",
    "dimensionality_reduction_inputs_v1": "dimensionality_reduction_inputs.json",
    "omics_volcano_panel_inputs_v1": "omics_volcano_panel_inputs.json",
    "heatmap_group_comparison_inputs_v1": "heatmap_group_comparison_inputs.json",
    "confusion_matrix_heatmap_binary_inputs_v1": "confusion_matrix_heatmap_binary_inputs.json",
    "pathway_enrichment_dotplot_panel_inputs_v1": "pathway_enrichment_dotplot_panel_inputs.json",
    "celltype_marker_dotplot_panel_inputs_v1": "celltype_marker_dotplot_panel_inputs.json",
    "cnv_recurrence_summary_panel_inputs_v1": "cnv_recurrence_summary_panel_inputs.json",
    "genomic_alteration_landscape_panel_inputs_v1": "genomic_alteration_landscape_panel_inputs.json",
    "genomic_alteration_consequence_panel_inputs_v1": "genomic_alteration_consequence_panel_inputs.json",
    "forest_effect_inputs_v1": "forest_effect_inputs.json",
    "generalizability_subgroup_composite_inputs_v1": "generalizability_subgroup_composite_inputs.json",
    "distribution_violin_box_inputs_v1": "distribution_violin_box_inputs.json",
    "composition_stacked_bar_inputs_v1": "composition_stacked_bar_inputs.json",
    "correlation_scatter_inputs_v1": "correlation_scatter_inputs.json",
    "alluvial_transition_inputs_v1": "alluvial_transition_inputs.json",
    "radar_profile_inputs_v1": "radar_profile_inputs.json",
    "waterfall_response_inputs_v1": "waterfall_response_inputs.json",
    "coefficient_path_panel_inputs_v1": "coefficient_path_panel_inputs.json",
    "shap_summary_inputs_v1": "shap_summary_inputs.json",
    "shap_dependence_panel_inputs_v1": "shap_dependence_panel_inputs.json",
    "shap_waterfall_local_explanation_panel_inputs_v1": "shap_waterfall_local_explanation_panel_inputs.json",
}


TABLE_INPUT_FILENAME_BY_SCHEMA_ID: dict[str, str] = {
    "baseline_characteristics_schema_v1": "baseline_characteristics_schema.json",
}
