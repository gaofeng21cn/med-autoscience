from .shared import *


def test_schema_contract_tracks_current_clinical_and_publication_shapes() -> None:
    fx = _load_schema_contract_fixture()
    time_to_event_class = fx.time_to_event_class
    model_explanation_class = fx.model_explanation_class
    clinical_utility_class = fx.clinical_utility_class
    publication_shells_class = fx.publication_shells_class

    assert _full_id("time_dependent_roc_horizon") in time_to_event_class.template_ids
    assert _full_id("time_dependent_roc_comparison_panel") not in time_to_event_class.template_ids
    assert _full_id("time_to_event_landmark_performance_panel") not in time_to_event_class.template_ids
    assert "time_dependent_roc_comparison_inputs_v1" not in time_to_event_class.input_schema_ids
    assert "time_to_event_landmark_performance_inputs_v1" not in time_to_event_class.input_schema_ids
    assert fx.time_to_event_grouped.template_ids == (
        _full_id("kaplan_meier_grouped"),
        _full_id("cumulative_incidence_grouped"),
    )
    assert fx.time_to_event_grouped.collection_required_fields["groups"] == ("label", "times", "values")
    assert fx.time_to_event_multihorizon.template_ids == (_full_id("time_to_event_multihorizon_calibration_panel"),)
    assert "panel_time_horizon_months_must_be_strictly_increasing" in (
        fx.time_to_event_multihorizon.additional_constraints
    )

    assert _full_id("decision_curve_binary") in clinical_utility_class.template_ids
    assert _full_id("time_to_event_decision_curve") in clinical_utility_class.template_ids
    assert fx.time_to_event_decision.template_ids == (_full_id("time_to_event_decision_curve"),)
    assert fx.time_to_event_decision.collection_required_fields["treated_fraction_series"] == ("label", "x", "y")

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

    assert fx.baseline_table.template_ids == (_full_id("table1_baseline_characteristics"),)
    assert fx.baseline_table.collection_required_fields["variables"] == ("variable_id", "label", "values")
