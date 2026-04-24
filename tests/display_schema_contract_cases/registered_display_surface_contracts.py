from .shared import *

def test_schema_contract_covers_all_registered_display_surface_items() -> None:
    schema_module = importlib.import_module("med_autoscience.display_schema_contract")
    registry_module = importlib.import_module("med_autoscience.display_registry")

    covered_templates = {
        template_id
        for schema in schema_module.list_input_schema_contracts()
        for template_id in schema.template_ids
    }
    covered_templates.update(
        template_id
        for display_class in schema_module.list_display_schema_classes()
        for template_id in display_class.template_ids
    )

    expected = {
        *(item.template_id for item in registry_module.list_evidence_figure_specs()),
        *(item.shell_id for item in registry_module.list_illustration_shell_specs()),
        *(item.shell_id for item in registry_module.list_table_shell_specs()),
    }

    assert covered_templates >= expected

def test_time_to_event_threshold_governance_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    threshold_governance = module.get_input_schema_contract("time_to_event_threshold_governance_inputs_v1")
    clinical_utility_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "clinical_utility"
    )

    assert threshold_governance.template_ids == (_full_id("time_to_event_threshold_governance_panel"),)
    assert threshold_governance.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "threshold_panel_title",
        "calibration_panel_title",
        "calibration_x_label",
        "threshold_summaries",
        "risk_group_summaries",
    )
    assert threshold_governance.display_optional_fields == ("paper_role",)
    assert threshold_governance.collection_required_fields["threshold_summaries"] == (
        "threshold_label",
        "threshold",
        "sensitivity",
        "specificity",
        "net_benefit",
    )
    assert threshold_governance.collection_required_fields["risk_group_summaries"] == (
        "group_label",
        "group_order",
        "n",
        "events",
        "predicted_risk",
        "observed_risk",
    )
    assert threshold_governance.additional_constraints == (
        "threshold_summaries_must_be_non_empty",
        "threshold_labels_must_be_unique",
        "threshold_values_must_be_strictly_increasing_probability",
        "threshold_metrics_must_be_finite",
        "risk_group_summaries_must_be_non_empty",
        "risk_group_order_must_be_strictly_increasing",
        "risk_group_risks_must_be_finite_probability",
        "risk_group_events_must_not_exceed_group_size",
    )
    assert _full_id("time_to_event_threshold_governance_panel") in clinical_utility_class.template_ids
    assert "time_to_event_threshold_governance_inputs_v1" in clinical_utility_class.input_schema_ids

def test_time_to_event_multihorizon_calibration_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    multihorizon = module.get_input_schema_contract("time_to_event_multihorizon_calibration_inputs_v1")
    time_to_event_class = next(item for item in module.list_display_schema_classes() if item.class_id == "time_to_event")

    assert multihorizon.template_ids == (_full_id("time_to_event_multihorizon_calibration_panel"),)
    assert multihorizon.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "panels",
    )
    assert multihorizon.display_optional_fields == ("paper_role",)
    assert multihorizon.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "time_horizon_months",
        "calibration_summary",
    )
    assert multihorizon.nested_collection_required_fields["panels.calibration_summary"] == (
        "group_label",
        "group_order",
        "n",
        "events",
        "predicted_risk",
        "observed_risk",
    )
    assert multihorizon.additional_constraints == (
        "multihorizon_calibration_panels_must_be_non_empty",
        "panel_ids_must_be_unique",
        "panel_labels_must_be_unique",
        "panel_time_horizon_months_must_be_positive",
        "panel_time_horizon_months_must_be_strictly_increasing",
        "panel_calibration_summary_must_be_non_empty",
        "panel_group_order_must_be_strictly_increasing",
        "panel_group_risks_must_be_finite_probability",
        "panel_group_events_must_not_exceed_group_size",
    )
    assert _full_id("time_to_event_multihorizon_calibration_panel") in time_to_event_class.template_ids
    assert "time_to_event_multihorizon_calibration_inputs_v1" in time_to_event_class.input_schema_ids

def test_single_cell_atlas_overview_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    atlas_overview = module.get_input_schema_contract("single_cell_atlas_overview_inputs_v1")
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert atlas_overview.template_ids == (_full_id("single_cell_atlas_overview_panel"),)
    assert atlas_overview.display_name == "Single-Cell Atlas Overview Panel"
    assert atlas_overview.collection_required_fields["composition_groups"] == (
        "group_label",
        "group_order",
        "state_proportions",
    )
    assert atlas_overview.nested_collection_required_fields["composition_groups.state_proportions"] == (
        "state_label",
        "proportion",
    )
    assert "composition_group_proportions_must_sum_to_one" in atlas_overview.additional_constraints
    assert "declared_column_labels_must_match_embedding_states" in atlas_overview.additional_constraints
    assert _full_id("single_cell_atlas_overview_panel") in data_geometry_class.template_ids
    assert "single_cell_atlas_overview_inputs_v1" in data_geometry_class.input_schema_ids

def test_spatial_niche_map_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    spatial_niche_map = module.get_input_schema_contract("spatial_niche_map_inputs_v1")
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert spatial_niche_map.template_ids == (_full_id("spatial_niche_map_panel"),)
    assert spatial_niche_map.display_name == "Spatial Niche Map Panel"
    assert spatial_niche_map.collection_required_fields["composition_groups"] == (
        "group_label",
        "group_order",
        "niche_proportions",
    )
    assert spatial_niche_map.nested_collection_required_fields["composition_groups.niche_proportions"] == (
        "niche_label",
        "proportion",
    )
    assert "composition_group_proportions_must_sum_to_one" in spatial_niche_map.additional_constraints
    assert "declared_column_labels_must_match_spatial_niches" in spatial_niche_map.additional_constraints
    assert _full_id("spatial_niche_map_panel") in data_geometry_class.template_ids
    assert "spatial_niche_map_inputs_v1" in data_geometry_class.input_schema_ids

def test_atlas_spatial_bridge_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")
    atlas_spatial_bridge = module.get_input_schema_contract("atlas_spatial_bridge_panel_inputs_v1")
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert atlas_spatial_bridge.template_ids == (_full_id("atlas_spatial_bridge_panel"),)
    assert atlas_spatial_bridge.display_name == "Atlas-Spatial Bridge Panel"
    assert atlas_spatial_bridge.collection_required_fields["atlas_points"] == ("x", "y", "state_label")
    assert atlas_spatial_bridge.collection_required_fields["spatial_points"] == ("x", "y", "state_label")
    assert atlas_spatial_bridge.collection_required_fields["composition_groups"] == (
        "group_label",
        "group_order",
        "state_proportions",
    )
    assert atlas_spatial_bridge.nested_collection_required_fields["composition_groups.state_proportions"] == (
        "state_label",
        "proportion",
    )
    assert "declared_column_labels_must_match_atlas_states" in atlas_spatial_bridge.additional_constraints
    assert "declared_column_labels_must_match_spatial_states" in atlas_spatial_bridge.additional_constraints
    assert _full_id("atlas_spatial_bridge_panel") in data_geometry_class.template_ids
    assert "atlas_spatial_bridge_panel_inputs_v1" in data_geometry_class.input_schema_ids

def test_trajectory_progression_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    trajectory_progression = module.get_input_schema_contract("trajectory_progression_inputs_v1")
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert trajectory_progression.template_ids == (_full_id("trajectory_progression_panel"),)
    assert trajectory_progression.display_name == "Trajectory Progression Panel"
    assert trajectory_progression.collection_required_fields["trajectory_points"] == (
        "x",
        "y",
        "branch_label",
        "state_label",
        "pseudotime",
    )
    assert trajectory_progression.collection_required_fields["branch_order"] == ("label",)
    assert trajectory_progression.collection_required_fields["progression_bins"] == (
        "bin_label",
        "bin_order",
        "pseudotime_start",
        "pseudotime_end",
        "branch_weights",
    )
    assert trajectory_progression.nested_collection_required_fields["progression_bins.branch_weights"] == (
        "branch_label",
        "proportion",
    )
    assert "progression_bin_branch_weights_must_sum_to_one" in trajectory_progression.additional_constraints
    assert "declared_column_labels_must_match_progression_bins" in trajectory_progression.additional_constraints
    assert _full_id("trajectory_progression_panel") in data_geometry_class.template_ids
    assert "trajectory_progression_inputs_v1" in data_geometry_class.input_schema_ids

def test_atlas_spatial_trajectory_storyboard_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    storyboard = module.get_input_schema_contract("atlas_spatial_trajectory_storyboard_inputs_v1")
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert storyboard.template_ids == (_full_id("atlas_spatial_trajectory_storyboard_panel"),)
    assert storyboard.display_name == "Atlas-Spatial Trajectory Storyboard Panel"
    assert storyboard.collection_required_fields["atlas_points"] == ("x", "y", "state_label")
    assert storyboard.collection_required_fields["spatial_points"] == ("x", "y", "state_label")
    assert storyboard.collection_required_fields["trajectory_points"] == (
        "x",
        "y",
        "branch_label",
        "state_label",
        "pseudotime",
    )
    assert storyboard.collection_required_fields["composition_groups"] == (
        "group_label",
        "group_order",
        "state_proportions",
    )
    assert storyboard.collection_required_fields["progression_bins"] == (
        "bin_label",
        "bin_order",
        "pseudotime_start",
        "pseudotime_end",
        "branch_weights",
    )
    assert storyboard.nested_collection_required_fields["composition_groups.state_proportions"] == (
        "state_label",
        "proportion",
    )
    assert storyboard.nested_collection_required_fields["progression_bins.branch_weights"] == (
        "branch_label",
        "proportion",
    )
    assert "declared_state_labels_must_match_atlas_states" in storyboard.additional_constraints
    assert "declared_state_labels_must_match_spatial_states" in storyboard.additional_constraints
    assert "declared_state_labels_must_match_trajectory_states" in storyboard.additional_constraints
    assert "declared_column_labels_must_match_progression_bins" in storyboard.additional_constraints
    assert _full_id("atlas_spatial_trajectory_storyboard_panel") in data_geometry_class.template_ids
    assert "atlas_spatial_trajectory_storyboard_inputs_v1" in data_geometry_class.input_schema_ids

def test_atlas_spatial_trajectory_density_coverage_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    density_coverage = module.get_input_schema_contract("atlas_spatial_trajectory_density_coverage_panel_inputs_v1")
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert density_coverage.template_ids == (_full_id("atlas_spatial_trajectory_density_coverage_panel"),)
    assert density_coverage.display_name == "Atlas-Spatial Trajectory Density Coverage Panel"
    assert density_coverage.collection_required_fields["atlas_points"] == ("x", "y", "state_label")
    assert density_coverage.collection_required_fields["spatial_points"] == ("x", "y", "state_label", "region_label")
    assert density_coverage.collection_required_fields["trajectory_points"] == (
        "x",
        "y",
        "branch_label",
        "state_label",
        "pseudotime",
    )
    assert density_coverage.collection_required_fields["state_order"] == ("label",)
    assert density_coverage.collection_required_fields["context_order"] == ("label", "context_kind")
    assert density_coverage.collection_required_fields["support_cells"] == ("x", "y", "value")
    assert "context_order_kinds_must_cover_all_required_contexts" in density_coverage.additional_constraints
    assert "declared_state_labels_must_match_support_rows" in density_coverage.additional_constraints
    assert "declared_context_labels_must_match_support_columns" in density_coverage.additional_constraints
    assert "declared_support_grid_must_be_complete_and_unique" in density_coverage.additional_constraints
    assert _full_id("atlas_spatial_trajectory_density_coverage_panel") in data_geometry_class.template_ids
    assert "atlas_spatial_trajectory_density_coverage_panel_inputs_v1" in data_geometry_class.input_schema_ids

def test_atlas_spatial_trajectory_context_support_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    context_support = module.get_input_schema_contract("atlas_spatial_trajectory_context_support_panel_inputs_v1")
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert context_support.template_ids == (_full_id("atlas_spatial_trajectory_context_support_panel"),)
    assert context_support.display_name == "Atlas-Spatial Trajectory Context Support Panel"
    assert context_support.collection_required_fields["atlas_points"] == ("x", "y", "state_label")
    assert context_support.collection_required_fields["spatial_points"] == ("x", "y", "state_label", "region_label")
    assert context_support.collection_required_fields["trajectory_points"] == (
        "x",
        "y",
        "branch_label",
        "state_label",
        "pseudotime",
    )
    assert context_support.collection_required_fields["composition_groups"] == (
        "group_label",
        "group_order",
        "state_proportions",
    )
    assert context_support.collection_required_fields["progression_bins"] == (
        "bin_label",
        "bin_order",
        "pseudotime_start",
        "pseudotime_end",
        "branch_weights",
    )
    assert context_support.collection_required_fields["context_order"] == ("label", "context_kind")
    assert context_support.collection_required_fields["support_cells"] == ("x", "y", "value")
    assert context_support.nested_collection_required_fields["composition_groups.state_proportions"] == (
        "state_label",
        "proportion",
    )
    assert context_support.nested_collection_required_fields["progression_bins.branch_weights"] == (
        "branch_label",
        "proportion",
    )
    assert "declared_state_labels_must_match_atlas_states" in context_support.additional_constraints
    assert "declared_state_labels_must_match_trajectory_states" in context_support.additional_constraints
    assert "declared_column_labels_must_match_progression_bins" in context_support.additional_constraints
    assert "declared_state_labels_must_match_support_rows" in context_support.additional_constraints
    assert "declared_support_grid_must_be_complete_and_unique" in context_support.additional_constraints
    assert _full_id("atlas_spatial_trajectory_context_support_panel") in data_geometry_class.template_ids
    assert "atlas_spatial_trajectory_context_support_panel_inputs_v1" in data_geometry_class.input_schema_ids

def test_atlas_spatial_trajectory_multimanifold_context_support_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    multimanifold_context_support = module.get_input_schema_contract(
        "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1"
    )
    data_geometry_class = next(item for item in module.list_display_schema_classes() if item.class_id == "data_geometry")

    assert multimanifold_context_support.template_ids == (
        _full_id("atlas_spatial_trajectory_multimanifold_context_support_panel"),
    )
    assert multimanifold_context_support.display_name == "Atlas-Spatial Trajectory Multimanifold Context Support Panel"
    assert multimanifold_context_support.collection_required_fields["atlas_manifold_panels"] == (
        "panel_id",
        "panel_label",
        "panel_title",
        "manifold_method",
        "x_label",
        "y_label",
        "points",
    )
    assert multimanifold_context_support.nested_collection_required_fields["atlas_manifold_panels.points"] == (
        "x",
        "y",
        "state_label",
    )
    assert "atlas_manifold_panels_must_contain_exactly_two_panels" in multimanifold_context_support.additional_constraints
    assert "atlas_manifold_methods_must_be_supported_and_unique" in multimanifold_context_support.additional_constraints
    assert "declared_state_labels_must_match_all_atlas_manifold_states" in multimanifold_context_support.additional_constraints
    assert _full_id("atlas_spatial_trajectory_multimanifold_context_support_panel") in data_geometry_class.template_ids
    assert "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1" in data_geometry_class.input_schema_ids

def test_shap_waterfall_local_explanation_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    shap_waterfall = module.get_input_schema_contract("shap_waterfall_local_explanation_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert shap_waterfall.template_ids == (_full_id("shap_waterfall_local_explanation_panel"),)
    assert shap_waterfall.display_name == "SHAP Waterfall Local Explanation Panel"
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
    assert "panel_count_must_not_exceed_three" in shap_waterfall.additional_constraints
    assert "panel_prediction_value_must_equal_baseline_plus_contributions" in shap_waterfall.additional_constraints
    assert _full_id("shap_waterfall_local_explanation_panel") in model_explanation_class.template_ids
    assert "shap_waterfall_local_explanation_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_shap_force_like_summary_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    force_like = module.get_input_schema_contract("shap_force_like_summary_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert force_like.template_ids == (_full_id("shap_force_like_summary_panel"),)
    assert force_like.display_name == "SHAP Force-like Summary Panel"
    assert force_like.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "case_label",
        "baseline_value",
        "predicted_value",
        "contributions",
    )
    assert force_like.nested_collection_required_fields["panels.contributions"] == ("feature", "shap_value")
    assert force_like.nested_collection_optional_fields["panels.contributions"] == ("feature_value_text",)
    assert "panel_count_must_not_exceed_three" in force_like.additional_constraints
    assert "panel_prediction_value_must_equal_baseline_plus_contributions" in force_like.additional_constraints
    assert "panel_contributions_must_be_sorted_by_absolute_magnitude_descending" in force_like.additional_constraints
    assert _full_id("shap_force_like_summary_panel") in model_explanation_class.template_ids
    assert "shap_force_like_summary_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_shap_grouped_local_explanation_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    grouped_local = module.get_input_schema_contract("shap_grouped_local_explanation_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert grouped_local.template_ids == (_full_id("shap_grouped_local_explanation_panel"),)
    assert grouped_local.display_name == "SHAP Grouped Local Explanation Panel"
    assert grouped_local.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "panels",
    )
    assert grouped_local.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "group_label",
        "baseline_value",
        "predicted_value",
        "contributions",
    )
    assert grouped_local.nested_collection_required_fields["panels.contributions"] == (
        "rank",
        "feature",
        "shap_value",
    )
    assert "panel_count_must_not_exceed_three" in grouped_local.additional_constraints
    assert "panel_group_labels_must_be_unique" in grouped_local.additional_constraints
    assert "panel_prediction_value_must_equal_baseline_plus_contributions" in grouped_local.additional_constraints
    assert "panel_contribution_ranks_must_be_strictly_increasing" in grouped_local.additional_constraints
    assert "panel_contribution_values_must_be_finite_and_non_zero" in grouped_local.additional_constraints
    assert "panel_feature_orders_must_match_across_panels" in grouped_local.additional_constraints
    assert _full_id("shap_grouped_local_explanation_panel") in model_explanation_class.template_ids
    assert "shap_grouped_local_explanation_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_shap_grouped_decision_path_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    decision_path = module.get_input_schema_contract("shap_grouped_decision_path_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert decision_path.template_ids == (_full_id("shap_grouped_decision_path_panel"),)
    assert decision_path.display_name == "SHAP Grouped Decision Path Panel"
    assert decision_path.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "panel_title",
        "x_label",
        "y_label",
        "legend_title",
        "baseline_value",
        "groups",
    )
    assert decision_path.collection_required_fields["groups"] == (
        "group_id",
        "group_label",
        "predicted_value",
        "contributions",
    )
    assert decision_path.nested_collection_required_fields["groups.contributions"] == (
        "rank",
        "feature",
        "shap_value",
    )
    assert "group_count_must_equal_two" in decision_path.additional_constraints
    assert "group_labels_must_be_unique" in decision_path.additional_constraints
    assert "baseline_value_must_be_finite" in decision_path.additional_constraints
    assert "group_prediction_value_must_equal_baseline_plus_contributions" in decision_path.additional_constraints
    assert "group_contribution_ranks_must_be_strictly_increasing" in decision_path.additional_constraints
    assert "group_contribution_values_must_be_finite_and_non_zero" in decision_path.additional_constraints
    assert "group_feature_orders_must_match" in decision_path.additional_constraints
    assert _full_id("shap_grouped_decision_path_panel") in model_explanation_class.template_ids
    assert "shap_grouped_decision_path_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_shap_multigroup_decision_path_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    decision_path = module.get_input_schema_contract("shap_multigroup_decision_path_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert decision_path.template_ids == (_full_id("shap_multigroup_decision_path_panel"),)
    assert decision_path.display_name == "SHAP Multigroup Decision Path Panel"
    assert decision_path.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "panel_title",
        "x_label",
        "y_label",
        "legend_title",
        "baseline_value",
        "groups",
    )
    assert decision_path.collection_required_fields["groups"] == (
        "group_id",
        "group_label",
        "predicted_value",
        "contributions",
    )
    assert decision_path.nested_collection_required_fields["groups.contributions"] == (
        "rank",
        "feature",
        "shap_value",
    )
    assert "group_count_must_equal_three" in decision_path.additional_constraints
    assert "group_labels_must_be_unique" in decision_path.additional_constraints
    assert "baseline_value_must_be_finite" in decision_path.additional_constraints
    assert "group_prediction_value_must_equal_baseline_plus_contributions" in decision_path.additional_constraints
    assert "group_contribution_ranks_must_be_strictly_increasing" in decision_path.additional_constraints
    assert "group_contribution_values_must_be_finite_and_non_zero" in decision_path.additional_constraints
    assert "group_feature_orders_must_match" in decision_path.additional_constraints
    assert _full_id("shap_multigroup_decision_path_panel") in model_explanation_class.template_ids
    assert "shap_multigroup_decision_path_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_partial_dependence_ice_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    pdp_ice = module.get_input_schema_contract("partial_dependence_ice_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert pdp_ice.template_ids == (_full_id("partial_dependence_ice_panel"),)
    assert pdp_ice.display_name == "Partial Dependence and ICE Panel"
    assert pdp_ice.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "feature",
        "reference_value",
        "reference_label",
        "pdp_curve",
        "ice_curves",
    )
    assert pdp_ice.nested_collection_required_fields["panels.pdp_curve"] == ("x", "y")
    assert pdp_ice.nested_collection_required_fields["panels.ice_curves"] == ("curve_id", "x", "y")
    assert "panel_count_must_not_exceed_three" in pdp_ice.additional_constraints
    assert "panel_reference_values_must_fall_within_pdp_curve_range" in pdp_ice.additional_constraints
    assert "ice_curve_x_grids_must_match_pdp_curve_x" in pdp_ice.additional_constraints
    assert _full_id("partial_dependence_ice_panel") in model_explanation_class.template_ids
    assert "partial_dependence_ice_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_partial_dependence_interaction_contour_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    pdp_interaction = module.get_input_schema_contract("partial_dependence_interaction_contour_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert pdp_interaction.template_ids == (_full_id("partial_dependence_interaction_contour_panel"),)
    assert pdp_interaction.display_name == "Partial Dependence Interaction Contour Panel"
    assert pdp_interaction.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "y_label",
        "x_feature",
        "y_feature",
        "reference_x_value",
        "reference_y_value",
        "reference_label",
        "x_grid",
        "y_grid",
        "response_grid",
        "observed_points",
    )
    assert pdp_interaction.nested_collection_required_fields["panels.observed_points"] == ("point_id", "x", "y")
    assert "panel_count_must_not_exceed_two" in pdp_interaction.additional_constraints
    assert "panel_x_grids_must_be_strictly_increasing" in pdp_interaction.additional_constraints
    assert "panel_y_grids_must_be_strictly_increasing" in pdp_interaction.additional_constraints
    assert "panel_response_grids_must_match_declared_axes" in pdp_interaction.additional_constraints
    assert "panel_observed_points_must_fall_within_declared_grid_range" in pdp_interaction.additional_constraints
    assert "panel_reference_point_must_fall_within_declared_grid_range" in pdp_interaction.additional_constraints
    assert _full_id("partial_dependence_interaction_contour_panel") in model_explanation_class.template_ids
    assert "partial_dependence_interaction_contour_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_partial_dependence_interaction_slice_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    interaction_slice = module.get_input_schema_contract("partial_dependence_interaction_slice_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert interaction_slice.template_ids == (_full_id("partial_dependence_interaction_slice_panel"),)
    assert interaction_slice.display_name == "Partial Dependence Interaction Slice Panel"
    assert interaction_slice.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "legend_title",
        "panels",
    )
    assert interaction_slice.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "x_feature",
        "slice_feature",
        "reference_value",
        "reference_label",
        "slice_curves",
    )
    assert interaction_slice.nested_collection_required_fields["panels.slice_curves"] == (
        "slice_id",
        "slice_label",
        "conditioning_value",
        "x",
        "y",
    )
    assert "panels_must_be_non_empty" in interaction_slice.additional_constraints
    assert "panel_count_must_not_exceed_two" in interaction_slice.additional_constraints
    assert "panel_feature_pairs_must_be_unique" in interaction_slice.additional_constraints
    assert "panel_slice_curves_must_have_at_least_two_entries" in interaction_slice.additional_constraints
    assert "panel_slice_curve_x_grids_must_match_within_panel" in interaction_slice.additional_constraints
    assert "panel_reference_values_must_fall_within_slice_curve_range" in interaction_slice.additional_constraints
    assert "panel_slice_label_sets_must_match_across_panels" in interaction_slice.additional_constraints
    assert _full_id("partial_dependence_interaction_slice_panel") in model_explanation_class.template_ids
    assert "partial_dependence_interaction_slice_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_partial_dependence_subgroup_comparison_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    subgroup_panel = module.get_input_schema_contract("partial_dependence_subgroup_comparison_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert subgroup_panel.template_ids == (_full_id("partial_dependence_subgroup_comparison_panel"),)
    assert subgroup_panel.display_name == "Partial Dependence Subgroup Comparison Panel"
    assert subgroup_panel.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "subgroup_panel_label",
        "subgroup_panel_title",
        "subgroup_x_label",
        "panels",
        "subgroup_rows",
    )
    assert subgroup_panel.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "subgroup_label",
        "title",
        "x_label",
        "feature",
        "reference_value",
        "reference_label",
        "pdp_curve",
        "ice_curves",
    )
    assert subgroup_panel.collection_required_fields["subgroup_rows"] == (
        "row_id",
        "panel_id",
        "row_label",
        "estimate",
        "lower",
        "upper",
        "support_n",
    )
    assert subgroup_panel.nested_collection_required_fields["panels.pdp_curve"] == ("x", "y")
    assert subgroup_panel.nested_collection_required_fields["panels.ice_curves"] == ("curve_id", "x", "y")
    assert "panel_count_must_not_exceed_three" in subgroup_panel.additional_constraints
    assert "panel_subgroup_labels_must_be_unique" in subgroup_panel.additional_constraints
    assert "subgroup_panel_label_must_be_distinct_from_top_panel_labels" in subgroup_panel.additional_constraints
    assert "subgroup_rows_must_match_panels_by_panel_id" in subgroup_panel.additional_constraints
    assert "subgroup_row_intervals_must_wrap_estimate" in subgroup_panel.additional_constraints
    assert "panel_ice_curve_x_grids_must_match_pdp_curve_x" in subgroup_panel.additional_constraints
    assert _full_id("partial_dependence_subgroup_comparison_panel") in model_explanation_class.template_ids
    assert "partial_dependence_subgroup_comparison_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_accumulated_local_effects_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    ale_panel = module.get_input_schema_contract("accumulated_local_effects_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert ale_panel.template_ids == (_full_id("accumulated_local_effects_panel"),)
    assert ale_panel.display_name == "Accumulated Local Effects Panel"
    assert ale_panel.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "panels",
    )
    assert ale_panel.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "feature",
        "reference_value",
        "reference_label",
        "ale_curve",
        "local_effect_bins",
    )
    assert ale_panel.nested_collection_required_fields["panels.ale_curve"] == ("x", "y")
    assert ale_panel.nested_collection_required_fields["panels.local_effect_bins"] == (
        "bin_id",
        "bin_left",
        "bin_right",
        "bin_center",
        "local_effect",
        "support_count",
    )
    assert "panels_must_be_non_empty" in ale_panel.additional_constraints
    assert "panel_count_must_not_exceed_three" in ale_panel.additional_constraints
    assert "panel_features_must_be_unique" in ale_panel.additional_constraints
    assert "panel_local_effect_bins_must_be_non_empty" in ale_panel.additional_constraints
    assert "panel_local_effect_bins_must_be_strictly_ordered_and_non_overlapping" in ale_panel.additional_constraints
    assert "panel_ale_curve_x_must_match_bin_centers" in ale_panel.additional_constraints
    assert "panel_ale_curve_must_match_cumulative_local_effects" in ale_panel.additional_constraints
    assert "panel_reference_values_must_fall_within_declared_bin_range" in ale_panel.additional_constraints
    assert _full_id("accumulated_local_effects_panel") in model_explanation_class.template_ids
    assert "accumulated_local_effects_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_feature_response_support_domain_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    support_domain_panel = module.get_input_schema_contract("feature_response_support_domain_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert support_domain_panel.template_ids == (_full_id("feature_response_support_domain_panel"),)
    assert support_domain_panel.display_name == "Feature Response Support Domain Panel"
    assert support_domain_panel.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "panels",
    )
    assert support_domain_panel.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "feature",
        "reference_value",
        "reference_label",
        "response_curve",
        "support_segments",
    )
    assert support_domain_panel.nested_collection_required_fields["panels.response_curve"] == ("x", "y")
    assert support_domain_panel.nested_collection_required_fields["panels.support_segments"] == (
        "segment_id",
        "segment_label",
        "support_kind",
        "domain_start",
        "domain_end",
    )
    assert "panel_count_must_be_between_two_and_three" in support_domain_panel.additional_constraints
    assert "panel_features_must_be_unique" in support_domain_panel.additional_constraints
    assert "panel_response_curve_x_must_be_strictly_increasing" in support_domain_panel.additional_constraints
    assert "panel_support_segment_ids_must_be_unique_within_panel" in support_domain_panel.additional_constraints
    assert "panel_support_segment_kinds_must_be_supported" in support_domain_panel.additional_constraints
    assert "panel_support_segments_must_be_strictly_ordered_and_non_overlapping" in support_domain_panel.additional_constraints
    assert "panel_support_segments_must_cover_curve_range" in support_domain_panel.additional_constraints
    assert "panel_reference_values_must_fall_within_response_curve_range" in support_domain_panel.additional_constraints
    assert _full_id("feature_response_support_domain_panel") in model_explanation_class.template_ids
    assert "feature_response_support_domain_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_shap_grouped_local_support_domain_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    explanation_scene = module.get_input_schema_contract("shap_grouped_local_support_domain_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert explanation_scene.template_ids == (_full_id("shap_grouped_local_support_domain_panel"),)
    assert explanation_scene.display_name == "SHAP Grouped Local Support-Domain Panel"
    assert explanation_scene.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "grouped_local_x_label",
        "support_y_label",
        "support_legend_title",
        "local_panels",
        "support_panels",
    )
    assert explanation_scene.collection_required_fields["local_panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "group_label",
        "baseline_value",
        "predicted_value",
        "contributions",
    )
    assert explanation_scene.collection_required_fields["support_panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "feature",
        "reference_value",
        "reference_label",
        "response_curve",
        "support_segments",
    )
    assert explanation_scene.nested_collection_required_fields["local_panels.contributions"] == (
        "rank",
        "feature",
        "shap_value",
    )
    assert explanation_scene.nested_collection_required_fields["support_panels.response_curve"] == ("x", "y")
    assert explanation_scene.nested_collection_required_fields["support_panels.support_segments"] == (
        "segment_id",
        "segment_label",
        "support_kind",
        "domain_start",
        "domain_end",
    )
    assert "local_panel_count_must_be_between_two_and_three" in explanation_scene.additional_constraints
    assert "local_panel_feature_orders_must_match_across_panels" in explanation_scene.additional_constraints
    assert "support_panel_count_must_equal_two" in explanation_scene.additional_constraints
    assert "support_panel_labels_must_be_distinct_from_local_panel_labels" in explanation_scene.additional_constraints
    assert "support_panel_support_segments_must_cover_curve_range" in explanation_scene.additional_constraints
    assert "support_panel_features_must_be_subset_of_local_feature_order" in explanation_scene.additional_constraints
    assert _full_id("shap_grouped_local_support_domain_panel") in model_explanation_class.template_ids
    assert "shap_grouped_local_support_domain_panel_inputs_v1" in model_explanation_class.input_schema_ids
