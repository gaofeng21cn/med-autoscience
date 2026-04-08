from __future__ import annotations


INPUT_FILENAME_BY_SCHEMA_ID: dict[str, str] = {
    "binary_prediction_curve_inputs_v1": "binary_prediction_curve_inputs.json",
    "time_dependent_roc_comparison_inputs_v1": "time_dependent_roc_comparison_inputs.json",
    "time_to_event_landmark_performance_inputs_v1": "time_to_event_landmark_performance_inputs.json",
    "time_to_event_threshold_governance_inputs_v1": "time_to_event_threshold_governance_inputs.json",
    "time_to_event_multihorizon_calibration_inputs_v1": "time_to_event_multihorizon_calibration_inputs.json",
    "time_to_event_grouped_inputs_v1": "time_to_event_grouped_inputs.json",
    "time_to_event_stratified_cumulative_incidence_inputs_v1": "time_to_event_stratified_cumulative_incidence_inputs.json",
    "time_to_event_discrimination_calibration_inputs_v1": "time_to_event_discrimination_calibration_inputs.json",
    "time_to_event_decision_curve_inputs_v1": "time_to_event_decision_curve_inputs.json",
    "risk_layering_monotonic_inputs_v1": "risk_layering_monotonic_inputs.json",
    "binary_calibration_decision_curve_panel_inputs_v1": "binary_calibration_decision_curve_panel_inputs.json",
    "model_complexity_audit_panel_inputs_v1": "model_complexity_audit_panel_inputs.json",
    "embedding_grouped_inputs_v1": "embedding_grouped_inputs.json",
    "celltype_signature_heatmap_inputs_v1": "celltype_signature_heatmap_inputs.json",
    "single_cell_atlas_overview_inputs_v1": "single_cell_atlas_overview_inputs.json",
    "heatmap_group_comparison_inputs_v1": "heatmap_group_comparison_inputs.json",
    "performance_heatmap_inputs_v1": "performance_heatmap_inputs.json",
    "correlation_heatmap_inputs_v1": "correlation_heatmap_inputs.json",
    "clustered_heatmap_inputs_v1": "clustered_heatmap_inputs.json",
    "gsva_ssgsea_heatmap_inputs_v1": "gsva_ssgsea_heatmap_inputs.json",
    "forest_effect_inputs_v1": "forest_effect_inputs.json",
    "shap_summary_inputs_v1": "shap_summary_inputs.json",
    "shap_dependence_panel_inputs_v1": "shap_dependence_panel_inputs.json",
    "multicenter_generalizability_inputs_v1": "multicenter_generalizability_inputs.json",
}


TABLE_INPUT_FILENAME_BY_SCHEMA_ID: dict[str, str] = {
    "baseline_characteristics_schema_v1": "baseline_characteristics_schema.json",
    "time_to_event_performance_summary_v1": "time_to_event_performance_summary.json",
    "clinical_interpretation_summary_v1": "clinical_interpretation_summary.json",
    "performance_summary_table_generic_v1": "performance_summary_table_generic.json",
    "grouped_risk_event_summary_table_v1": "grouped_risk_event_summary_table.json",
}
