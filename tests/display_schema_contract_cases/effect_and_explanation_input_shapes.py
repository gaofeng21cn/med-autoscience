from .shared import *

def test_schema_contract_tracks_effect_and_explanation_input_shapes() -> None:
    fx = _load_schema_contract_fixture()
    correlation = fx.correlation
    forest = fx.forest
    generalizability_subgroup = fx.generalizability_subgroup
    compact_effect_estimate = fx.compact_effect_estimate
    effect_estimate_class = fx.effect_estimate_class
    coefficient_path = fx.coefficient_path
    shap = fx.shap
    shap_dependence = fx.shap_dependence
    shap_waterfall = fx.shap_waterfall

    assert correlation.template_ids == (_full_id("correlation_heatmap"),)
    assert correlation.required_top_level_fields == ("schema_version", "input_schema_id", "displays")
    assert correlation.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "cells",
    )
    assert correlation.collection_required_fields["cells"] == ("x", "y", "value")
    assert correlation.additional_constraints == (
        "matrix_must_be_square",
        "matrix_must_include_diagonal",
        "matrix_must_be_symmetric",
    )

    assert forest.template_ids == (
        _full_id("forest_effect_main"),
        _full_id("subgroup_forest"),
        _full_id("multivariable_forest"),
    )
    assert generalizability_subgroup.template_ids == (_full_id("generalizability_subgroup_composite_panel"),)
    assert compact_effect_estimate.template_ids == (_full_id("compact_effect_estimate_panel"),)
    assert generalizability_subgroup.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "metric_family",
        "primary_label",
        "overview_panel_title",
        "overview_x_label",
        "overview_rows",
        "subgroup_panel_title",
        "subgroup_x_label",
        "subgroup_reference_value",
        "subgroup_rows",
    )
    assert generalizability_subgroup.display_optional_fields == ("paper_role", "comparator_label")
    assert generalizability_subgroup.collection_required_fields["overview_rows"] == (
        "cohort_id",
        "cohort_label",
        "support_count",
        "metric_value",
    )
    assert generalizability_subgroup.collection_optional_fields["overview_rows"] == (
        "comparator_metric_value",
        "event_count",
    )
    assert generalizability_subgroup.collection_required_fields["subgroup_rows"] == (
        "subgroup_id",
        "subgroup_label",
        "estimate",
        "lower",
        "upper",
    )
    assert generalizability_subgroup.collection_optional_fields["subgroup_rows"] == ("group_n",)
    assert "metric_family_must_be_supported" in generalizability_subgroup.additional_constraints
    assert (
        "overview_comparator_metric_values_must_be_present_for_all_rows_when_comparator_label_is_declared"
        in generalizability_subgroup.additional_constraints
    )
    assert "subgroup_rows_must_satisfy_lower_le_estimate_le_upper" in generalizability_subgroup.additional_constraints
    assert compact_effect_estimate.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "reference_value",
        "panels",
    )
    assert compact_effect_estimate.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "rows",
    )
    assert compact_effect_estimate.nested_collection_required_fields["panels.rows"] == (
        "row_id",
        "row_label",
        "estimate",
        "lower",
        "upper",
    )
    assert compact_effect_estimate.nested_collection_optional_fields["panels.rows"] == ("support_n",)
    assert compact_effect_estimate.additional_constraints == (
        "panels_must_be_non_empty",
        "panel_count_must_be_between_two_and_four",
        "panel_ids_must_be_unique",
        "panel_labels_must_be_unique",
        "reference_value_must_be_finite",
        "panel_rows_must_be_non_empty",
        "panel_row_ids_must_be_unique_within_panel",
        "panel_row_labels_must_be_unique_within_panel",
        "panel_row_values_must_be_finite",
        "panel_row_intervals_must_wrap_estimate",
        "panel_row_support_n_must_be_positive_when_present",
        "panel_row_orders_must_match_across_panels",
    )
    assert _full_id("compact_effect_estimate_panel") in effect_estimate_class.template_ids
    assert "compact_effect_estimate_panel_inputs_v1" in effect_estimate_class.input_schema_ids
    assert coefficient_path.template_ids == (_full_id("coefficient_path_panel"),)
    assert coefficient_path.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "path_panel_title",
        "x_label",
        "reference_value",
        "step_legend_title",
        "steps",
        "coefficient_rows",
        "summary_panel_title",
        "summary_cards",
    )
    assert coefficient_path.display_optional_fields == ("paper_role",)
    assert coefficient_path.collection_required_fields["steps"] == ("step_id", "step_label", "step_order")
    assert coefficient_path.collection_required_fields["coefficient_rows"] == (
        "row_id",
        "row_label",
        "points",
    )
    assert coefficient_path.collection_required_fields["summary_cards"] == ("card_id", "label", "value")
    assert coefficient_path.collection_optional_fields["summary_cards"] == ("detail",)
    assert coefficient_path.nested_collection_required_fields["coefficient_rows.points"] == (
        "step_id",
        "estimate",
        "lower",
        "upper",
    )
    assert coefficient_path.nested_collection_optional_fields["coefficient_rows.points"] == ("support_n",)
    assert coefficient_path.additional_constraints == (
        "steps_must_contain_between_two_and_five_entries",
        "step_ids_must_be_unique",
        "step_orders_must_be_strictly_increasing",
        "reference_value_must_be_finite",
        "coefficient_rows_must_be_non_empty",
        "coefficient_row_ids_must_be_unique",
        "coefficient_row_labels_must_be_unique",
        "coefficient_points_must_cover_all_declared_steps_once",
        "coefficient_point_values_must_be_finite",
        "coefficient_point_intervals_must_wrap_estimate",
        "coefficient_point_support_n_must_be_positive_when_present",
        "summary_cards_must_contain_between_two_and_four_entries",
        "summary_card_ids_must_be_unique",
    )
    assert _full_id("coefficient_path_panel") in effect_estimate_class.template_ids
    assert "coefficient_path_panel_inputs_v1" in effect_estimate_class.input_schema_ids
    assert forest.collection_required_fields["rows"] == ("label", "estimate", "lower", "upper")
    assert shap.template_ids == (_full_id("shap_summary_beeswarm"),)
    assert shap.collection_required_fields["rows"] == ("feature", "points")
    assert shap.nested_collection_required_fields["rows.points"] == ("shap_value", "feature_value")
    assert shap_dependence.template_ids == (_full_id("shap_dependence_panel"),)
    assert shap_dependence.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "colorbar_label",
        "panels",
    )
    assert shap_dependence.display_optional_fields == ("paper_role",)
    assert shap_dependence.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "feature",
        "interaction_feature",
        "points",
    )
    assert shap_dependence.nested_collection_required_fields["panels.points"] == (
        "feature_value",
        "shap_value",
        "interaction_value",
    )
    assert shap_dependence.additional_constraints == (
        "panels_must_be_non_empty",
        "panel_ids_must_be_unique",
        "panel_labels_must_be_unique",
        "panel_features_must_be_unique",
        "panel_points_must_be_non_empty",
        "panel_point_values_must_be_finite",
    )
    assert shap_waterfall.template_ids == (_full_id("shap_waterfall_local_explanation_panel"),)
    assert shap_waterfall.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "panels",
    )
    assert shap_waterfall.display_optional_fields == ("paper_role",)
    assert shap_waterfall.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "case_label",
        "baseline_value",
        "predicted_value",
        "contributions",
    )
    assert shap_waterfall.nested_collection_required_fields["panels.contributions"] == ("feature", "shap_value")
    assert shap_waterfall.nested_collection_optional_fields["panels.contributions"] == ("feature_value_text",)
    assert shap_waterfall.additional_constraints == (
        "panels_must_be_non_empty",
        "panel_count_must_not_exceed_three",
        "panel_ids_must_be_unique",
        "panel_labels_must_be_unique",
        "panel_case_labels_must_be_unique",
        "panel_values_must_be_finite",
        "panel_contributions_must_be_non_empty",
        "panel_contribution_features_must_be_unique_within_panel",
        "panel_contribution_values_must_be_finite_and_non_zero",
        "panel_prediction_value_must_equal_baseline_plus_contributions",
    )
