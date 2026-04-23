from .shared import *

def test_schema_contract_tracks_clinical_and_publication_input_shapes() -> None:
    fx = _load_schema_contract_fixture()
    module = fx.module
    cohort_flow = fx.cohort_flow
    time_to_event_class = fx.time_to_event_class
    model_explanation_class = fx.model_explanation_class
    clinical_utility_class = fx.clinical_utility_class
    generalizability_class = fx.generalizability_class
    performance_heatmap = fx.performance_heatmap
    confusion_heatmap = fx.confusion_heatmap
    time_to_event_panel = fx.time_to_event_panel
    binary_calibration_decision = fx.binary_calibration_decision
    time_to_event_decision = fx.time_to_event_decision
    time_dependent_roc_comparison = fx.time_dependent_roc_comparison
    landmark_performance = fx.landmark_performance
    time_to_event_stratified = fx.time_to_event_stratified
    generalizability = fx.generalizability
    risk_layering = fx.risk_layering
    model_audit_class = fx.model_audit_class
    model_complexity_audit = fx.model_complexity_audit
    performance_table = fx.performance_table
    interpretation_table = fx.interpretation_table
    generic_performance_table = fx.generic_performance_table
    grouped_risk_table = fx.grouped_risk_table
    submission_graphical_abstract = fx.submission_graphical_abstract
    workflow_fact_sheet = fx.workflow_fact_sheet
    design_evidence_composite = fx.design_evidence_composite
    baseline_missingness_qc = fx.baseline_missingness_qc
    center_coverage_batch_transportability = fx.center_coverage_batch_transportability
    publication_shells_class = fx.publication_shells_class
    transportability_recalibration_governance = fx.transportability_recalibration_governance
    cohort_flow_shell = fx.cohort_flow

    assert cohort_flow.template_ids == (_full_id("cohort_flow_figure"),)
    assert cohort_flow.required_top_level_fields == ("schema_version", "shell_id", "display_id", "title", "steps")
    assert cohort_flow.optional_top_level_fields == ("caption", "exclusions", "endpoint_inventory", "design_panels")
    assert cohort_flow.collection_required_fields["steps"] == ("step_id", "label", "n")
    assert cohort_flow.collection_required_fields["exclusions"] == ("exclusion_id", "from_step_id", "label", "n")
    assert cohort_flow.collection_required_fields["endpoint_inventory"] == ("endpoint_id", "label", "event_n")
    assert cohort_flow.collection_required_fields["design_panels"] == ("panel_id", "title", "layout_role", "lines")
    assert cohort_flow.nested_collection_required_fields["design_panels.lines"] == ("label",)
    assert "exclusion_ids_must_be_unique" in cohort_flow.additional_constraints
    assert "design_panel_lines_must_be_non_empty" in cohort_flow.additional_constraints

    assert _full_id("time_dependent_roc_horizon") in time_to_event_class.template_ids
    assert _full_id("time_dependent_roc_comparison_panel") in time_to_event_class.template_ids
    assert "binary_prediction_curve_inputs_v1" in time_to_event_class.input_schema_ids
    assert "time_dependent_roc_comparison_inputs_v1" in time_to_event_class.input_schema_ids
    assert _full_id("time_to_event_landmark_performance_panel") in time_to_event_class.template_ids
    assert "time_to_event_landmark_performance_inputs_v1" in time_to_event_class.input_schema_ids
    assert _full_id("time_to_event_stratified_cumulative_incidence_panel") in time_to_event_class.template_ids
    assert "time_to_event_stratified_cumulative_incidence_inputs_v1" in time_to_event_class.input_schema_ids
    assert _full_id("celltype_signature_heatmap") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).template_ids
    assert _full_id("omics_volcano_panel") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).template_ids
    assert "omics_volcano_panel_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).input_schema_ids
    assert _full_id("oncoplot_mutation_landscape_panel") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).template_ids
    assert "oncoplot_mutation_landscape_panel_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).input_schema_ids
    assert _full_id("cnv_recurrence_summary_panel") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).template_ids
    assert "cnv_recurrence_summary_panel_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).input_schema_ids
    assert _full_id("genomic_alteration_consequence_panel") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).template_ids
    assert "genomic_alteration_consequence_panel_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).input_schema_ids
    assert _full_id("single_cell_atlas_overview_panel") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).template_ids
    assert _full_id("atlas_spatial_bridge_panel") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).template_ids
    assert _full_id("spatial_niche_map_panel") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).template_ids
    assert "celltype_signature_heatmap_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).input_schema_ids
    assert "single_cell_atlas_overview_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).input_schema_ids
    assert "atlas_spatial_bridge_panel_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).input_schema_ids
    assert "spatial_niche_map_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    ).input_schema_ids
    assert _full_id("performance_heatmap") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).template_ids
    assert _full_id("confusion_matrix_heatmap_binary") in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).template_ids
    assert "performance_heatmap_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).input_schema_ids
    assert "confusion_matrix_heatmap_binary_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).input_schema_ids
    assert performance_heatmap.template_ids == (_full_id("performance_heatmap"),)
    assert confusion_heatmap.template_ids == (_full_id("confusion_matrix_heatmap_binary"),)
    assert _full_id("shap_summary_beeswarm") in model_explanation_class.template_ids
    assert _full_id("shap_dependence_panel") in model_explanation_class.template_ids
    assert _full_id("shap_waterfall_local_explanation_panel") in model_explanation_class.template_ids
    assert _full_id("partial_dependence_ice_panel") in model_explanation_class.template_ids
    assert _full_id("generalizability_subgroup_composite_panel") in generalizability_class.template_ids
    assert "shap_summary_inputs_v1" in model_explanation_class.input_schema_ids
    assert "shap_dependence_panel_inputs_v1" in model_explanation_class.input_schema_ids
    assert "shap_waterfall_local_explanation_panel_inputs_v1" in model_explanation_class.input_schema_ids
    assert "partial_dependence_ice_panel_inputs_v1" in model_explanation_class.input_schema_ids
    assert "generalizability_subgroup_composite_inputs_v1" in generalizability_class.input_schema_ids
    assert performance_heatmap.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "metric_name",
        "row_order",
        "column_order",
        "cells",
    )
    assert performance_heatmap.collection_required_fields["row_order"] == ("label",)
    assert performance_heatmap.collection_required_fields["column_order"] == ("label",)
    assert performance_heatmap.additional_constraints == (
        "metric_name_must_be_non_empty",
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "performance_values_must_be_finite_probability",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_heatmap_grid_must_be_complete_and_unique",
    )
    assert confusion_heatmap.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "metric_name",
        "normalization",
        "row_order",
        "column_order",
        "cells",
    )
    assert confusion_heatmap.collection_required_fields["row_order"] == ("label",)
    assert confusion_heatmap.collection_required_fields["column_order"] == ("label",)
    assert confusion_heatmap.additional_constraints == (
        "metric_name_must_be_non_empty",
        "normalization_must_use_supported_vocabulary",
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "confusion_matrix_values_must_be_finite_probability",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "binary_confusion_matrix_must_have_exactly_two_row_labels",
        "binary_confusion_matrix_must_have_exactly_two_column_labels",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_heatmap_grid_must_be_complete_and_unique",
        "row_fraction_confusion_rows_must_sum_to_one_when_selected",
        "column_fraction_confusion_columns_must_sum_to_one_when_selected",
        "overall_fraction_confusion_matrix_must_sum_to_one_when_selected",
    )
    assert time_to_event_panel.template_ids == (_full_id("time_to_event_discrimination_calibration_panel"),)
    assert time_to_event_panel.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "panel_a_title",
        "panel_b_title",
        "discrimination_x_label",
        "calibration_x_label",
        "calibration_y_label",
        "discrimination_points",
        "calibration_summary",
    )
    assert time_to_event_panel.collection_required_fields["discrimination_points"] == ("label", "c_index")
    assert time_to_event_panel.collection_required_fields["calibration_summary"] == (
        "group_label",
        "group_order",
        "n",
        "events_5y",
        "predicted_risk_5y",
        "observed_risk_5y",
    )
    assert "calibration_callout" in time_to_event_panel.display_optional_fields
    assert _full_id("binary_calibration_decision_curve_panel") in clinical_utility_class.template_ids
    assert "binary_calibration_decision_curve_panel_inputs_v1" in clinical_utility_class.input_schema_ids
    assert binary_calibration_decision.template_ids == (_full_id("binary_calibration_decision_curve_panel"),)
    assert binary_calibration_decision.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "calibration_x_label",
        "calibration_y_label",
        "decision_x_label",
        "decision_y_label",
        "calibration_axis_window",
        "calibration_series",
        "decision_series",
        "decision_reference_lines",
        "decision_focus_window",
    )
    assert binary_calibration_decision.collection_required_fields["calibration_series"] == ("label", "x", "y")
    assert binary_calibration_decision.collection_required_fields["decision_series"] == ("label", "x", "y")
    assert binary_calibration_decision.collection_required_fields["decision_reference_lines"] == (
        "label",
        "x",
        "y",
    )
    assert "calibration_axis_window" not in binary_calibration_decision.display_optional_fields
    assert binary_calibration_decision.nested_collection_required_fields["calibration_axis_window"] == (
        "xmin",
        "xmax",
        "ymin",
        "ymax",
    )
    assert binary_calibration_decision.nested_collection_required_fields["decision_focus_window"] == ("xmin", "xmax")
    assert "calibration_axis_window_must_be_strictly_increasing" in binary_calibration_decision.additional_constraints
    assert "decision_focus_window_must_be_strictly_increasing" in binary_calibration_decision.additional_constraints

    assert time_to_event_decision.template_ids == (_full_id("time_to_event_decision_curve"),)
    assert time_to_event_decision.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "panel_a_title",
        "panel_b_title",
        "x_label",
        "y_label",
        "treated_fraction_y_label",
        "series",
        "treated_fraction_series",
    )
    assert time_to_event_decision.collection_required_fields["series"] == ("label", "x", "y")
    assert time_to_event_decision.collection_required_fields["treated_fraction_series"] == ("label", "x", "y")
    assert "publication_style_profile_required_at_materialization" in time_to_event_decision.additional_constraints
    assert "display_override_contract_may_adjust_layout_without_changing_data" in time_to_event_decision.additional_constraints
    assert "treated_fraction_series_x_y_lengths_must_match" in time_to_event_decision.additional_constraints
    assert time_dependent_roc_comparison.template_ids == (_full_id("time_dependent_roc_comparison_panel"),)
    assert time_dependent_roc_comparison.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "panels",
    )
    assert time_dependent_roc_comparison.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "analysis_window_label",
        "series",
    )
    assert time_dependent_roc_comparison.collection_optional_fields["panels"] == (
        "annotation",
        "time_horizon_months",
        "reference_line",
    )
    assert time_dependent_roc_comparison.nested_collection_required_fields["panels.series"] == ("label", "x", "y")
    assert time_dependent_roc_comparison.nested_collection_required_fields["panels.reference_line"] == ("x", "y")
    assert time_dependent_roc_comparison.nested_collection_optional_fields["panels.reference_line"] == ("label",)
    assert "panel_series_labels_must_be_unique_within_panel" in time_dependent_roc_comparison.additional_constraints
    assert "panel_series_label_sets_must_match_across_panels" in time_dependent_roc_comparison.additional_constraints
    assert "panel_time_horizon_months_must_be_positive_when_present" in time_dependent_roc_comparison.additional_constraints
    assert landmark_performance.template_ids == (_full_id("time_to_event_landmark_performance_panel"),)
    assert landmark_performance.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "discrimination_panel_title",
        "discrimination_x_label",
        "error_panel_title",
        "error_x_label",
        "calibration_panel_title",
        "calibration_x_label",
        "landmark_summaries",
    )
    assert landmark_performance.collection_required_fields["landmark_summaries"] == (
        "window_label",
        "analysis_window_label",
        "landmark_months",
        "prediction_months",
        "c_index",
        "brier_score",
        "calibration_slope",
    )
    assert landmark_performance.collection_optional_fields["landmark_summaries"] == ("annotation",)
    assert landmark_performance.additional_constraints == (
        "landmark_summaries_must_be_non_empty",
        "window_labels_must_be_unique",
        "analysis_window_labels_must_be_unique",
        "landmark_months_must_be_positive",
        "prediction_months_must_be_positive",
        "prediction_months_must_exceed_landmark_months",
        "c_index_values_must_be_finite_probability",
        "brier_score_values_must_be_finite_probability",
        "calibration_slope_values_must_be_finite",
    )
    assert time_to_event_stratified.template_ids == (_full_id("time_to_event_stratified_cumulative_incidence_panel"),)
    assert time_to_event_stratified.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "panels",
    )
    assert time_to_event_stratified.collection_required_fields["panels"] == ("panel_id", "panel_label", "title", "groups")
    assert time_to_event_stratified.collection_optional_fields["panels"] == ("annotation",)
    assert time_to_event_stratified.nested_collection_required_fields["panels.groups"] == ("label", "times", "values")
    assert "panel_ids_must_be_unique" in time_to_event_stratified.additional_constraints
    assert "panel_group_values_must_be_monotonic_non_decreasing" in time_to_event_stratified.additional_constraints
    assert generalizability.template_ids == (_full_id("multicenter_generalizability_overview"),)
    assert generalizability.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "overview_mode",
        "center_event_y_label",
        "coverage_y_label",
        "center_event_counts",
        "coverage_panels",
    )
    assert generalizability.collection_required_fields["center_event_counts"] == (
        "center_label",
        "split_bucket",
        "event_count",
    )
    assert generalizability.collection_required_fields["coverage_panels"] == (
        "panel_id",
        "title",
        "layout_role",
        "bars",
    )
    assert generalizability.nested_collection_required_fields["coverage_panels.bars"] == ("label", "count")
    assert "overview_mode_must_be_center_support_counts" in generalizability.additional_constraints
    assert risk_layering.template_ids == (_full_id("risk_layering_monotonic_bars"),)
    assert risk_layering.required_top_level_fields == ("schema_version", "input_schema_id", "displays")
    assert risk_layering.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "left_panel_title",
        "left_x_label",
        "left_bars",
        "right_panel_title",
        "right_x_label",
        "right_bars",
    )
    assert risk_layering.collection_required_fields["left_bars"] == ("label", "cases", "events", "risk")
    assert risk_layering.collection_required_fields["right_bars"] == ("label", "cases", "events", "risk")
    assert "bar_events_must_not_exceed_cases" in risk_layering.additional_constraints
    assert "left_bars_risk_must_be_monotonic_non_decreasing" in risk_layering.additional_constraints
    assert "right_bars_risk_must_be_monotonic_non_decreasing" in risk_layering.additional_constraints
    assert model_audit_class.template_ids == (_full_id("model_complexity_audit_panel"),)
    assert model_complexity_audit.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "metric_panels",
        "audit_panels",
    )
    assert model_complexity_audit.collection_required_fields["metric_panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "rows",
    )
    assert model_complexity_audit.collection_required_fields["audit_panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "rows",
    )
    assert model_complexity_audit.nested_collection_required_fields["metric_panels.rows"] == ("label", "value")
    assert model_complexity_audit.nested_collection_required_fields["audit_panels.rows"] == ("label", "value")
    assert performance_table.template_ids == (_full_id("table2_time_to_event_performance_summary"),)
    assert performance_table.collection_required_fields["rows"] == ("row_id", "label", "values")
    assert interpretation_table.template_ids == (_full_id("table3_clinical_interpretation_summary"),)
    assert interpretation_table.collection_required_fields["rows"] == ("row_id", "label", "values")
    assert generic_performance_table.template_ids == (_full_id("performance_summary_table_generic"),)
    assert "row_header_label" in generic_performance_table.required_top_level_fields
    assert grouped_risk_table.template_ids == (_full_id("grouped_risk_event_summary_table"),)
    assert grouped_risk_table.collection_required_fields["rows"] == (
        "row_id",
        "surface",
        "stratum",
        "cases",
        "events",
        "risk_display",
    )
    assert submission_graphical_abstract.template_ids == (_full_id("submission_graphical_abstract"),)
    assert submission_graphical_abstract.required_top_level_fields == (
        "schema_version",
        "shell_id",
        "display_id",
        "catalog_id",
        "title",
        "caption",
        "panels",
    )
    assert submission_graphical_abstract.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "subtitle",
        "rows",
    )
    assert workflow_fact_sheet.template_ids == (_full_id("workflow_fact_sheet_panel"),)
    assert workflow_fact_sheet.required_top_level_fields == (
        "schema_version",
        "shell_id",
        "display_id",
        "title",
        "sections",
    )
    assert workflow_fact_sheet.optional_top_level_fields == ("caption",)
    assert workflow_fact_sheet.collection_required_fields["sections"] == (
        "section_id",
        "panel_label",
        "title",
        "layout_role",
        "facts",
    )
    assert workflow_fact_sheet.nested_collection_required_fields["sections.facts"] == (
        "fact_id",
        "label",
        "value",
    )
    assert workflow_fact_sheet.nested_collection_optional_fields["sections.facts"] == ("detail",)
    assert "sections_must_contain_exactly_four_items" in workflow_fact_sheet.additional_constraints
    assert "section_layout_roles_must_match_four_panel_fact_sheet_grid" in workflow_fact_sheet.additional_constraints
    assert "section_fact_ids_must_be_unique_within_section" in workflow_fact_sheet.additional_constraints
    assert "section_facts_must_be_non_empty" in workflow_fact_sheet.additional_constraints
    assert design_evidence_composite.template_ids == (_full_id("design_evidence_composite_shell"),)
    assert design_evidence_composite.required_top_level_fields == (
        "schema_version",
        "shell_id",
        "display_id",
        "title",
        "workflow_stages",
        "summary_panels",
    )
    assert design_evidence_composite.optional_top_level_fields == ("caption",)
    assert design_evidence_composite.collection_required_fields["workflow_stages"] == (
        "stage_id",
        "title",
    )
    assert design_evidence_composite.collection_required_fields["summary_panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "layout_role",
        "cards",
    )
    assert design_evidence_composite.nested_collection_required_fields["summary_panels.cards"] == (
        "card_id",
        "label",
        "value",
    )
    assert design_evidence_composite.nested_collection_optional_fields["workflow_stages"] == ("detail",)
    assert design_evidence_composite.nested_collection_optional_fields["summary_panels.cards"] == ("detail",)
    assert "workflow_stages_must_contain_three_or_four_items" in design_evidence_composite.additional_constraints
    assert "summary_panels_must_contain_exactly_three_items" in design_evidence_composite.additional_constraints
    assert "summary_panel_layout_roles_must_match_three_panel_composite" in design_evidence_composite.additional_constraints
    assert "summary_panel_cards_must_be_non_empty" in design_evidence_composite.additional_constraints
    assert baseline_missingness_qc.template_ids == (_full_id("baseline_missingness_qc_panel"),)
    assert baseline_missingness_qc.required_top_level_fields == (
        "schema_version",
        "shell_id",
        "display_id",
        "title",
        "balance_panel_title",
        "balance_x_label",
        "balance_threshold",
        "primary_balance_label",
        "balance_variables",
        "missingness_panel_title",
        "missingness_x_label",
        "missingness_y_label",
        "missingness_rows",
        "missingness_columns",
        "missingness_cells",
        "qc_panel_title",
        "qc_cards",
    )
    assert baseline_missingness_qc.optional_top_level_fields == (
        "caption",
        "secondary_balance_label",
    )
    assert baseline_missingness_qc.collection_required_fields["balance_variables"] == (
        "variable_id",
        "label",
        "primary_value",
    )
    assert baseline_missingness_qc.collection_optional_fields["balance_variables"] == ("secondary_value",)
    assert baseline_missingness_qc.collection_required_fields["missingness_rows"] == ("label",)
    assert baseline_missingness_qc.collection_required_fields["missingness_columns"] == ("label",)
    assert baseline_missingness_qc.collection_required_fields["missingness_cells"] == ("x", "y", "value")
    assert baseline_missingness_qc.collection_required_fields["qc_cards"] == (
        "card_id",
        "label",
        "value",
    )
    assert baseline_missingness_qc.collection_optional_fields["qc_cards"] == ("detail",)
    assert baseline_missingness_qc.additional_constraints == (
        "balance_variables_must_be_non_empty",
        "balance_variable_ids_must_be_unique",
        "balance_variable_labels_must_be_unique",
        "balance_primary_values_must_be_finite_non_negative",
        "balance_secondary_values_require_secondary_label",
        "balance_secondary_values_must_be_finite_non_negative",
        "balance_threshold_must_be_positive_finite",
        "missingness_rows_must_be_non_empty",
        "missingness_row_labels_must_be_unique",
        "missingness_columns_must_be_non_empty",
        "missingness_column_labels_must_be_unique",
        "missingness_cells_must_be_non_empty",
        "missingness_cell_values_must_be_probability",
        "declared_missingness_rows_must_match_cells",
        "declared_missingness_columns_must_match_cells",
        "declared_missingness_grid_must_be_complete_and_unique",
        "qc_cards_must_be_non_empty",
        "qc_card_ids_must_be_unique",
    )
    assert center_coverage_batch_transportability.template_ids == (
        _full_id("center_coverage_batch_transportability_panel"),
    )
    assert center_coverage_batch_transportability.required_top_level_fields == (
        "schema_version",
        "shell_id",
        "display_id",
        "title",
        "coverage_panel_title",
        "coverage_x_label",
        "center_rows",
        "batch_panel_title",
        "batch_x_label",
        "batch_y_label",
        "batch_threshold",
        "batch_rows",
        "batch_columns",
        "batch_cells",
        "transportability_panel_title",
        "transportability_cards",
    )
    assert center_coverage_batch_transportability.optional_top_level_fields == ("caption",)
    assert center_coverage_batch_transportability.collection_required_fields["center_rows"] == (
        "center_id",
        "center_label",
        "cohort_role",
        "support_count",
        "event_count",
    )
    assert center_coverage_batch_transportability.collection_required_fields["batch_rows"] == ("label",)
    assert center_coverage_batch_transportability.collection_required_fields["batch_columns"] == ("label",)
    assert center_coverage_batch_transportability.collection_required_fields["batch_cells"] == ("x", "y", "value")
    assert center_coverage_batch_transportability.collection_required_fields["transportability_cards"] == (
        "card_id",
        "label",
        "value",
    )
    assert center_coverage_batch_transportability.collection_optional_fields["transportability_cards"] == ("detail",)
    assert "center_coverage_batch_transportability_panel_inputs_v1" in publication_shells_class.input_schema_ids
    assert transportability_recalibration_governance.template_ids == (
        _full_id("transportability_recalibration_governance_panel"),
    )
    assert transportability_recalibration_governance.required_top_level_fields == (
        "schema_version",
        "shell_id",
        "display_id",
        "title",
        "coverage_panel_title",
        "coverage_x_label",
        "center_rows",
        "batch_panel_title",
        "batch_x_label",
        "batch_y_label",
        "batch_threshold",
        "batch_rows",
        "batch_columns",
        "batch_cells",
        "recalibration_panel_title",
        "slope_acceptance_lower",
        "slope_acceptance_upper",
        "oe_ratio_acceptance_lower",
        "oe_ratio_acceptance_upper",
        "recalibration_rows",
    )
    assert transportability_recalibration_governance.optional_top_level_fields == ("caption",)
    assert transportability_recalibration_governance.collection_required_fields["center_rows"] == (
        "center_id",
        "center_label",
        "cohort_role",
        "support_count",
        "event_count",
    )
    assert transportability_recalibration_governance.collection_required_fields["batch_rows"] == ("label",)
    assert transportability_recalibration_governance.collection_required_fields["batch_columns"] == ("label",)
    assert transportability_recalibration_governance.collection_required_fields["batch_cells"] == ("x", "y", "value")
    assert transportability_recalibration_governance.collection_required_fields["recalibration_rows"] == (
        "center_id",
        "slope",
        "oe_ratio",
        "action",
    )
    assert transportability_recalibration_governance.collection_optional_fields["recalibration_rows"] == ("detail",)
    assert "transportability_recalibration_governance_panel_inputs_v1" in publication_shells_class.input_schema_ids
    cohort_flow_shell = module.get_input_schema_contract("cohort_flow_shell_inputs_v1")
    assert cohort_flow_shell.required_top_level_fields == ("schema_version", "shell_id", "display_id", "title", "steps")
    assert cohort_flow_shell.optional_top_level_fields == (
        "caption",
        "exclusions",
        "endpoint_inventory",
        "design_panels",
    )
    assert cohort_flow_shell.collection_required_fields["steps"] == ("step_id", "label", "n")
    assert cohort_flow_shell.collection_required_fields["exclusions"] == ("exclusion_id", "from_step_id", "label", "n")
    assert cohort_flow_shell.collection_required_fields["endpoint_inventory"] == ("endpoint_id", "label", "event_n")
    assert cohort_flow_shell.collection_required_fields["design_panels"] == ("panel_id", "title", "layout_role", "lines")
    assert cohort_flow_shell.nested_collection_required_fields["design_panels.lines"] == ("label",)
    assert "exclusion_ids_must_be_unique" in cohort_flow_shell.additional_constraints
    assert "design_panel_lines_must_be_non_empty" in cohort_flow_shell.additional_constraints
