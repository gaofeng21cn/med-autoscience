from .shared import *

def test_schema_contract_tracks_data_geometry_input_shapes() -> None:
    fx = _load_schema_contract_fixture()
    module = fx.module
    binary = fx.binary
    embedding = fx.embedding
    celltype_signature = fx.celltype_signature
    atlas_overview = fx.atlas_overview
    atlas_spatial_bridge = fx.atlas_spatial_bridge
    spatial_niche_map = fx.spatial_niche_map
    trajectory_progression = fx.trajectory_progression
    density_coverage = fx.density_coverage
    context_support = fx.context_support
    multimanifold_context_support = fx.multimanifold_context_support

    assert binary.template_ids == (
        _full_id("roc_curve_binary"),
        _full_id("pr_curve_binary"),
        _full_id("calibration_curve_binary"),
        _full_id("decision_curve_binary"),
        _full_id("clinical_impact_curve_binary"),
        _full_id("time_dependent_roc_horizon"),
    )
    assert embedding.template_ids == (
        _full_id("umap_scatter_grouped"),
        _full_id("pca_scatter_grouped"),
        _full_id("phate_scatter_grouped"),
        _full_id("tsne_scatter_grouped"),
        _full_id("diffusion_map_scatter_grouped"),
    )
    assert celltype_signature.template_ids == (_full_id("celltype_signature_heatmap"),)
    assert celltype_signature.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "embedding_panel_title",
        "embedding_x_label",
        "embedding_y_label",
        "embedding_points",
        "heatmap_panel_title",
        "heatmap_x_label",
        "heatmap_y_label",
        "score_method",
        "row_order",
        "column_order",
        "cells",
    )
    assert celltype_signature.display_optional_fields == (
        "paper_role",
        "embedding_annotation",
        "heatmap_annotation",
    )
    assert celltype_signature.collection_required_fields["embedding_points"] == ("x", "y", "group")
    assert celltype_signature.collection_required_fields["row_order"] == ("label",)
    assert celltype_signature.collection_required_fields["column_order"] == ("label",)
    assert celltype_signature.collection_required_fields["cells"] == ("x", "y", "value")
    assert celltype_signature.additional_constraints == (
        "embedding_points_must_be_non_empty",
        "embedding_point_coordinates_must_be_finite",
        "embedding_point_group_must_be_non_empty",
        "score_method_must_be_non_empty",
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_column_labels_must_match_embedding_groups",
        "declared_heatmap_grid_must_be_complete_and_unique",
    )
    assert atlas_overview.template_ids == (_full_id("single_cell_atlas_overview_panel"),)
    assert atlas_overview.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "embedding_panel_title",
        "embedding_x_label",
        "embedding_y_label",
        "embedding_points",
        "composition_panel_title",
        "composition_x_label",
        "composition_y_label",
        "composition_groups",
        "heatmap_panel_title",
        "heatmap_x_label",
        "heatmap_y_label",
        "score_method",
        "row_order",
        "column_order",
        "cells",
    )
    assert atlas_overview.display_optional_fields == (
        "paper_role",
        "embedding_annotation",
        "composition_annotation",
        "heatmap_annotation",
    )
    assert atlas_overview.collection_required_fields["embedding_points"] == ("x", "y", "state_label")
    assert atlas_overview.collection_optional_fields["embedding_points"] == ("group_label",)
    assert atlas_overview.collection_required_fields["composition_groups"] == (
        "group_label",
        "group_order",
        "state_proportions",
    )
    assert atlas_overview.nested_collection_required_fields["composition_groups.state_proportions"] == (
        "state_label",
        "proportion",
    )
    assert atlas_overview.collection_required_fields["row_order"] == ("label",)
    assert atlas_overview.collection_required_fields["column_order"] == ("label",)
    assert atlas_overview.collection_required_fields["cells"] == ("x", "y", "value")
    assert atlas_overview.additional_constraints == (
        "embedding_points_must_be_non_empty",
        "embedding_point_coordinates_must_be_finite",
        "embedding_point_state_label_must_be_non_empty",
        "composition_groups_must_be_non_empty",
        "composition_group_labels_must_be_unique",
        "composition_group_order_must_be_strictly_increasing",
        "composition_group_state_proportions_must_be_non_empty",
        "composition_group_state_labels_must_match_declared_columns",
        "composition_group_proportions_must_be_finite_probability",
        "composition_group_proportions_must_sum_to_one",
        "score_method_must_be_non_empty",
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_column_labels_must_match_embedding_states",
        "declared_heatmap_grid_must_be_complete_and_unique",
    )
    assert atlas_spatial_bridge.template_ids == (_full_id("atlas_spatial_bridge_panel"),)
    assert atlas_spatial_bridge.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "atlas_panel_title",
        "atlas_x_label",
        "atlas_y_label",
        "atlas_points",
        "spatial_panel_title",
        "spatial_x_label",
        "spatial_y_label",
        "spatial_points",
        "composition_panel_title",
        "composition_x_label",
        "composition_y_label",
        "composition_groups",
        "heatmap_panel_title",
        "heatmap_x_label",
        "heatmap_y_label",
        "score_method",
        "row_order",
        "column_order",
        "cells",
    )
    assert atlas_spatial_bridge.display_optional_fields == (
        "paper_role",
        "atlas_annotation",
        "spatial_annotation",
        "composition_annotation",
        "heatmap_annotation",
    )
    assert atlas_spatial_bridge.collection_required_fields["atlas_points"] == ("x", "y", "state_label")
    assert atlas_spatial_bridge.collection_optional_fields["atlas_points"] == ("group_label",)
    assert atlas_spatial_bridge.collection_required_fields["spatial_points"] == ("x", "y", "state_label")
    assert atlas_spatial_bridge.collection_optional_fields["spatial_points"] == ("region_label",)
    assert atlas_spatial_bridge.collection_required_fields["composition_groups"] == (
        "group_label",
        "group_order",
        "state_proportions",
    )
    assert atlas_spatial_bridge.nested_collection_required_fields["composition_groups.state_proportions"] == (
        "state_label",
        "proportion",
    )
    assert atlas_spatial_bridge.collection_required_fields["row_order"] == ("label",)
    assert atlas_spatial_bridge.collection_required_fields["column_order"] == ("label",)
    assert atlas_spatial_bridge.collection_required_fields["cells"] == ("x", "y", "value")
    assert atlas_spatial_bridge.additional_constraints == (
        "atlas_points_must_be_non_empty",
        "atlas_point_coordinates_must_be_finite",
        "atlas_point_state_label_must_be_non_empty",
        "spatial_points_must_be_non_empty",
        "spatial_point_coordinates_must_be_finite",
        "spatial_point_state_label_must_be_non_empty",
        "composition_groups_must_be_non_empty",
        "composition_group_labels_must_be_unique",
        "composition_group_order_must_be_strictly_increasing",
        "composition_group_state_proportions_must_be_non_empty",
        "composition_group_state_labels_must_match_declared_columns",
        "composition_group_proportions_must_be_finite_probability",
        "composition_group_proportions_must_sum_to_one",
        "score_method_must_be_non_empty",
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_column_labels_must_match_atlas_states",
        "declared_column_labels_must_match_spatial_states",
        "declared_heatmap_grid_must_be_complete_and_unique",
    )
    assert spatial_niche_map.template_ids == (_full_id("spatial_niche_map_panel"),)
    assert spatial_niche_map.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "spatial_panel_title",
        "spatial_x_label",
        "spatial_y_label",
        "spatial_points",
        "composition_panel_title",
        "composition_x_label",
        "composition_y_label",
        "composition_groups",
        "heatmap_panel_title",
        "heatmap_x_label",
        "heatmap_y_label",
        "score_method",
        "row_order",
        "column_order",
        "cells",
    )
    assert spatial_niche_map.display_optional_fields == (
        "paper_role",
        "spatial_annotation",
        "composition_annotation",
        "heatmap_annotation",
    )
    assert spatial_niche_map.collection_required_fields["spatial_points"] == ("x", "y", "niche_label")
    assert spatial_niche_map.collection_optional_fields["spatial_points"] == ("region_label",)
    assert spatial_niche_map.collection_required_fields["composition_groups"] == (
        "group_label",
        "group_order",
        "niche_proportions",
    )
    assert spatial_niche_map.nested_collection_required_fields["composition_groups.niche_proportions"] == (
        "niche_label",
        "proportion",
    )
    assert spatial_niche_map.collection_required_fields["row_order"] == ("label",)
    assert spatial_niche_map.collection_required_fields["column_order"] == ("label",)
    assert spatial_niche_map.collection_required_fields["cells"] == ("x", "y", "value")
    assert spatial_niche_map.additional_constraints == (
        "spatial_points_must_be_non_empty",
        "spatial_point_coordinates_must_be_finite",
        "spatial_point_niche_label_must_be_non_empty",
        "composition_groups_must_be_non_empty",
        "composition_group_labels_must_be_unique",
        "composition_group_order_must_be_strictly_increasing",
        "composition_group_niche_proportions_must_be_non_empty",
        "composition_group_niche_labels_must_match_declared_columns",
        "composition_group_proportions_must_be_finite_probability",
        "composition_group_proportions_must_sum_to_one",
        "score_method_must_be_non_empty",
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_column_labels_must_match_spatial_niches",
        "declared_heatmap_grid_must_be_complete_and_unique",
    )
    assert trajectory_progression.template_ids == (_full_id("trajectory_progression_panel"),)
    assert trajectory_progression.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "trajectory_panel_title",
        "trajectory_x_label",
        "trajectory_y_label",
        "trajectory_points",
        "composition_panel_title",
        "composition_x_label",
        "composition_y_label",
        "branch_order",
        "progression_bins",
        "heatmap_panel_title",
        "heatmap_x_label",
        "heatmap_y_label",
        "score_method",
        "row_order",
        "column_order",
        "cells",
    )
    assert trajectory_progression.display_optional_fields == (
        "paper_role",
        "trajectory_annotation",
        "composition_annotation",
        "heatmap_annotation",
    )
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
    assert trajectory_progression.collection_required_fields["row_order"] == ("label",)
    assert trajectory_progression.collection_required_fields["column_order"] == ("label",)
    assert trajectory_progression.collection_required_fields["cells"] == ("x", "y", "value")
    assert trajectory_progression.additional_constraints == (
        "trajectory_points_must_be_non_empty",
        "trajectory_point_coordinates_must_be_finite",
        "trajectory_point_branch_label_must_be_non_empty",
        "trajectory_point_state_label_must_be_non_empty",
        "trajectory_point_pseudotime_must_be_finite_probability",
        "branch_order_labels_must_be_unique",
        "branch_order_labels_must_match_trajectory_branches",
        "progression_bins_must_be_non_empty",
        "progression_bin_labels_must_be_unique",
        "progression_bin_order_must_be_strictly_increasing",
        "progression_bin_intervals_must_be_strictly_increasing",
        "progression_bin_branch_weights_must_be_non_empty",
        "progression_bin_branch_labels_must_match_declared_branch_order",
        "progression_bin_branch_weights_must_be_finite_probability",
        "progression_bin_branch_weights_must_sum_to_one",
        "score_method_must_be_non_empty",
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_column_labels_must_match_progression_bins",
        "declared_heatmap_grid_must_be_complete_and_unique",
    )
    assert _full_id("trajectory_progression_panel") in next(
        item.template_ids for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    )
    assert "trajectory_progression_inputs_v1" in next(
        item.input_schema_ids for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    )
    assert density_coverage.template_ids == (_full_id("atlas_spatial_trajectory_density_coverage_panel"),)
    assert density_coverage.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "atlas_panel_title",
        "atlas_x_label",
        "atlas_y_label",
        "atlas_points",
        "spatial_panel_title",
        "spatial_x_label",
        "spatial_y_label",
        "spatial_points",
        "trajectory_panel_title",
        "trajectory_x_label",
        "trajectory_y_label",
        "trajectory_points",
        "support_panel_title",
        "support_x_label",
        "support_y_label",
        "support_scale_label",
        "state_order",
        "context_order",
        "support_cells",
    )
    assert density_coverage.display_optional_fields == (
        "paper_role",
        "atlas_annotation",
        "spatial_annotation",
        "trajectory_annotation",
        "support_annotation",
    )
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
    assert density_coverage.additional_constraints == (
        "atlas_points_must_be_non_empty",
        "atlas_point_coordinates_must_be_finite",
        "atlas_point_state_label_must_be_non_empty",
        "spatial_points_must_be_non_empty",
        "spatial_point_coordinates_must_be_finite",
        "spatial_point_state_label_must_be_non_empty",
        "spatial_point_region_label_must_be_non_empty",
        "trajectory_points_must_be_non_empty",
        "trajectory_point_coordinates_must_be_finite",
        "trajectory_point_branch_label_must_be_non_empty",
        "trajectory_point_state_label_must_be_non_empty",
        "trajectory_point_pseudotime_must_be_finite_probability",
        "support_scale_label_must_be_non_empty",
        "state_order_labels_must_be_unique",
        "context_order_labels_must_be_unique",
        "context_order_kinds_must_be_supported_and_unique",
        "context_order_kinds_must_cover_all_required_contexts",
        "support_cells_must_be_non_empty",
        "support_cell_coordinates_must_be_non_empty",
        "support_cell_values_must_be_finite_probability",
        "declared_state_labels_must_match_atlas_states",
        "declared_state_labels_must_match_spatial_states",
        "declared_state_labels_must_match_trajectory_states",
        "declared_state_labels_must_match_support_rows",
        "declared_context_labels_must_match_support_columns",
        "declared_support_grid_must_be_complete_and_unique",
    )
    assert _full_id("atlas_spatial_trajectory_density_coverage_panel") in next(
        item.template_ids for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    )
    assert "atlas_spatial_trajectory_density_coverage_panel_inputs_v1" in next(
        item.input_schema_ids for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    )
    assert context_support.template_ids == (_full_id("atlas_spatial_trajectory_context_support_panel"),)
    assert context_support.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "atlas_panel_title",
        "atlas_x_label",
        "atlas_y_label",
        "atlas_points",
        "spatial_panel_title",
        "spatial_x_label",
        "spatial_y_label",
        "spatial_points",
        "trajectory_panel_title",
        "trajectory_x_label",
        "trajectory_y_label",
        "trajectory_points",
        "composition_panel_title",
        "composition_x_label",
        "composition_y_label",
        "composition_groups",
        "heatmap_panel_title",
        "heatmap_x_label",
        "heatmap_y_label",
        "score_method",
        "state_order",
        "branch_order",
        "progression_bins",
        "row_order",
        "column_order",
        "cells",
        "support_panel_title",
        "support_x_label",
        "support_y_label",
        "support_scale_label",
        "context_order",
        "support_cells",
    )
    assert context_support.display_optional_fields == (
        "paper_role",
        "atlas_annotation",
        "spatial_annotation",
        "trajectory_annotation",
        "composition_annotation",
        "heatmap_annotation",
        "support_annotation",
    )
    assert context_support.collection_required_fields["spatial_points"] == ("x", "y", "state_label", "region_label")
    assert context_support.collection_required_fields["composition_groups"] == (
        "group_label",
        "group_order",
        "state_proportions",
    )
    assert context_support.collection_required_fields["context_order"] == ("label", "context_kind")
    assert context_support.collection_required_fields["support_cells"] == ("x", "y", "value")
    assert "declared_column_labels_must_match_progression_bins" in context_support.additional_constraints
    assert "context_order_kinds_must_cover_all_required_contexts" in context_support.additional_constraints
    assert "declared_context_labels_must_match_support_columns" in context_support.additional_constraints
    assert "declared_support_grid_must_be_complete_and_unique" in context_support.additional_constraints
    assert _full_id("atlas_spatial_trajectory_context_support_panel") in next(
        item.template_ids for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    )
    assert "atlas_spatial_trajectory_context_support_panel_inputs_v1" in next(
        item.input_schema_ids for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    )
    assert _full_id("atlas_spatial_trajectory_multimanifold_context_support_panel") in next(
        item.template_ids for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    )
    assert "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1" in next(
        item.input_schema_ids for item in module.list_display_schema_classes() if item.class_id == "data_geometry"
    )
    assert multimanifold_context_support.display_kind == "evidence_figure"
