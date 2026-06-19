from .shared import *


def test_schema_contract_tracks_current_clinical_and_publication_shapes() -> None:
    fx = _load_schema_contract_fixture()
    time_to_event_class = fx.time_to_event_class
    model_explanation_class = fx.model_explanation_class
    clinical_utility_class = fx.clinical_utility_class
    publication_shells_class = fx.publication_shells_class

    assert _full_id("time_dependent_roc_horizon") in time_to_event_class.template_ids
    assert _full_id("time_dependent_roc_comparison_panel") in time_to_event_class.template_ids
    assert _full_id("time_to_event_landmark_performance_panel") in time_to_event_class.template_ids
    assert _full_id("time_to_event_stratified_cumulative_incidence_panel") in time_to_event_class.template_ids
    assert "time_dependent_roc_comparison_inputs_v1" in time_to_event_class.input_schema_ids
    assert "time_to_event_landmark_performance_inputs_v1" in time_to_event_class.input_schema_ids

    assert fx.time_to_event_panel.template_ids == (_full_id("time_to_event_discrimination_calibration_panel"),)
    assert fx.time_to_event_panel.collection_required_fields["discrimination_points"] == ("label", "c_index")
    assert fx.time_to_event_panel.collection_required_fields["calibration_summary"] == (
        "group_label",
        "group_order",
        "n",
        "events_5y",
        "predicted_risk_5y",
        "observed_risk_5y",
    )

    assert _full_id("binary_calibration_decision_curve_panel") in clinical_utility_class.template_ids
    assert fx.binary_calibration_decision.template_ids == (_full_id("binary_calibration_decision_curve_panel"),)
    assert fx.binary_calibration_decision.collection_required_fields["calibration_series"] == ("label", "x", "y")
    assert "decision_focus_window_must_be_strictly_increasing" in fx.binary_calibration_decision.additional_constraints

    assert fx.performance_heatmap.template_ids == (_full_id("performance_heatmap"),)
    assert fx.performance_heatmap.collection_required_fields["cells"] == ("x", "y", "value")
    assert "declared_heatmap_grid_must_be_complete_and_unique" in fx.performance_heatmap.additional_constraints
    assert fx.confusion_heatmap.template_ids == (_full_id("confusion_matrix_heatmap_binary"),)
    assert "binary_confusion_matrix_must_have_exactly_two_row_labels" in fx.confusion_heatmap.additional_constraints

    assert _full_id("shap_summary_beeswarm") in model_explanation_class.template_ids
    assert _full_id("shap_waterfall_local_explanation_panel") in model_explanation_class.template_ids
    assert "shap_summary_inputs_v1" in model_explanation_class.input_schema_ids
    assert "shap_waterfall_local_explanation_panel_inputs_v1" in model_explanation_class.input_schema_ids

    assert fx.cohort_flow.template_ids == (_full_id("cohort_flow_figure"),)
    assert fx.cohort_flow.required_top_level_fields == ("schema_version", "shell_id", "display_id", "title", "steps")
    assert fx.cohort_flow.collection_required_fields["steps"] == ("step_id", "label", "n")
    assert _full_id("submission_graphical_abstract") in publication_shells_class.template_ids
    assert _full_id("generalizability_subgroup_composite_panel") in fx.generalizability_class.template_ids
    assert "generalizability_subgroup_composite_inputs_v1" in fx.generalizability_class.input_schema_ids

    assert fx.performance_table.template_ids == (_full_id("table2_time_to_event_performance_summary"),)
    assert fx.performance_table.collection_required_fields["rows"] == ("row_id", "label", "values")
    assert fx.generic_performance_table.template_ids == (_full_id("performance_summary_table_generic"),)
    assert "row_header_label" in fx.generic_performance_table.required_top_level_fields
