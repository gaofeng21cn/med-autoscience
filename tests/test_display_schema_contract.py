from __future__ import annotations

import importlib
from pathlib import Path


_CORE_PACK_ID = "fenggaolab.org.medical-display-core"


def _full_id(short_id: str) -> str:
    return f"{_CORE_PACK_ID}::{short_id}"


def test_schema_contract_exposes_phase2_top_level_display_classes() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    classes = module.list_display_schema_classes()

    assert {item.class_id for item in classes} == {
        "prediction_performance",
        "clinical_utility",
        "time_to_event",
        "data_geometry",
        "matrix_pattern",
        "effect_estimate",
        "model_explanation",
        "model_audit",
        "generalizability",
        "publication_shells_and_tables",
    }


def test_schema_contract_tracks_registered_templates_and_input_shapes() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    binary = module.get_input_schema_contract("binary_prediction_curve_inputs_v1")
    embedding = module.get_input_schema_contract("embedding_grouped_inputs_v1")
    celltype_signature = module.get_input_schema_contract("celltype_signature_heatmap_inputs_v1")
    atlas_overview = module.get_input_schema_contract("single_cell_atlas_overview_inputs_v1")
    atlas_spatial_bridge = module.get_input_schema_contract("atlas_spatial_bridge_panel_inputs_v1")
    spatial_niche_map = module.get_input_schema_contract("spatial_niche_map_inputs_v1")
    trajectory_progression = module.get_input_schema_contract("trajectory_progression_inputs_v1")
    density_coverage = module.get_input_schema_contract("atlas_spatial_trajectory_density_coverage_panel_inputs_v1")
    context_support = module.get_input_schema_contract("atlas_spatial_trajectory_context_support_panel_inputs_v1")
    performance_heatmap = module.get_input_schema_contract("performance_heatmap_inputs_v1")
    clustered_heatmap = module.get_input_schema_contract("clustered_heatmap_inputs_v1")
    gsva_heatmap = module.get_input_schema_contract("gsva_ssgsea_heatmap_inputs_v1")
    enrichment_dotplot = module.get_input_schema_contract("pathway_enrichment_dotplot_panel_inputs_v1")
    omics_volcano = module.get_input_schema_contract("omics_volcano_panel_inputs_v1")
    oncoplot_landscape = module.get_input_schema_contract("oncoplot_mutation_landscape_panel_inputs_v1")
    landmark_performance = module.get_input_schema_contract("time_to_event_landmark_performance_inputs_v1")
    correlation = module.get_input_schema_contract("correlation_heatmap_inputs_v1")
    forest = module.get_input_schema_contract("forest_effect_inputs_v1")
    generalizability_subgroup = module.get_input_schema_contract("generalizability_subgroup_composite_inputs_v1")
    compact_effect_estimate = module.get_input_schema_contract("compact_effect_estimate_panel_inputs_v1")
    coefficient_path = module.get_input_schema_contract("coefficient_path_panel_inputs_v1")
    shap = module.get_input_schema_contract("shap_summary_inputs_v1")
    shap_dependence = module.get_input_schema_contract("shap_dependence_panel_inputs_v1")
    shap_waterfall = module.get_input_schema_contract("shap_waterfall_local_explanation_panel_inputs_v1")
    cohort_flow = module.get_input_schema_contract("cohort_flow_shell_inputs_v1")
    time_to_event_panel = module.get_input_schema_contract("time_to_event_discrimination_calibration_inputs_v1")
    time_to_event_decision = module.get_input_schema_contract("time_to_event_decision_curve_inputs_v1")
    time_dependent_roc_comparison = module.get_input_schema_contract("time_dependent_roc_comparison_inputs_v1")
    time_to_event_stratified = module.get_input_schema_contract(
        "time_to_event_stratified_cumulative_incidence_inputs_v1"
    )
    generalizability = module.get_input_schema_contract("multicenter_generalizability_inputs_v1")
    risk_layering = module.get_input_schema_contract("risk_layering_monotonic_inputs_v1")
    binary_calibration_decision = module.get_input_schema_contract(
        "binary_calibration_decision_curve_panel_inputs_v1"
    )
    model_complexity_audit = module.get_input_schema_contract("model_complexity_audit_panel_inputs_v1")
    performance_table = module.get_input_schema_contract("time_to_event_performance_summary_v1")
    interpretation_table = module.get_input_schema_contract("clinical_interpretation_summary_v1")
    generic_performance_table = module.get_input_schema_contract("performance_summary_table_generic_v1")
    grouped_risk_table = module.get_input_schema_contract("grouped_risk_event_summary_table_v1")
    submission_graphical_abstract = module.get_input_schema_contract("submission_graphical_abstract_inputs_v1")
    workflow_fact_sheet = module.get_input_schema_contract("workflow_fact_sheet_panel_inputs_v1")
    design_evidence_composite = module.get_input_schema_contract("design_evidence_composite_shell_inputs_v1")
    baseline_missingness_qc = module.get_input_schema_contract("baseline_missingness_qc_panel_inputs_v1")
    center_coverage_batch_transportability = module.get_input_schema_contract(
        "center_coverage_batch_transportability_panel_inputs_v1"
    )
    transportability_recalibration_governance = module.get_input_schema_contract(
        "transportability_recalibration_governance_panel_inputs_v1"
    )
    time_to_event_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "time_to_event"
    )
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )
    clinical_utility_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "clinical_utility"
    )
    model_audit_class = next(item for item in module.list_display_schema_classes() if item.class_id == "model_audit")
    generalizability_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "generalizability"
    )
    effect_estimate_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "effect_estimate"
    )
    publication_shells_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "publication_shells_and_tables"
    )

    assert binary.template_ids == (
        _full_id("roc_curve_binary"),
        _full_id("pr_curve_binary"),
        _full_id("calibration_curve_binary"),
        _full_id("decision_curve_binary"),
        _full_id("time_dependent_roc_horizon"),
    )
    assert embedding.template_ids == (
        _full_id("umap_scatter_grouped"),
        _full_id("pca_scatter_grouped"),
        _full_id("tsne_scatter_grouped"),
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
    assert clustered_heatmap.template_ids == (_full_id("clustered_heatmap"),)
    assert clustered_heatmap.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "row_order",
        "column_order",
        "cells",
    )
    assert clustered_heatmap.collection_required_fields["row_order"] == ("label",)
    assert clustered_heatmap.collection_required_fields["column_order"] == ("label",)
    assert clustered_heatmap.additional_constraints == (
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_heatmap_grid_must_be_complete_and_unique",
    )
    assert gsva_heatmap.template_ids == (_full_id("gsva_ssgsea_heatmap"),)
    assert gsva_heatmap.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "score_method",
        "row_order",
        "column_order",
        "cells",
    )
    assert gsva_heatmap.collection_required_fields["row_order"] == ("label",)
    assert gsva_heatmap.collection_required_fields["column_order"] == ("label",)
    assert gsva_heatmap.additional_constraints == (
        "score_method_must_be_non_empty",
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_heatmap_grid_must_be_complete_and_unique",
    )
    assert enrichment_dotplot.template_ids == (_full_id("pathway_enrichment_dotplot_panel"),)
    assert enrichment_dotplot.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "effect_scale_label",
        "size_scale_label",
        "panel_order",
        "pathway_order",
        "points",
    )
    assert enrichment_dotplot.display_optional_fields == ("paper_role",)
    assert enrichment_dotplot.collection_required_fields["panel_order"] == ("panel_id", "panel_title")
    assert enrichment_dotplot.collection_required_fields["pathway_order"] == ("label",)
    assert enrichment_dotplot.collection_required_fields["points"] == (
        "panel_id",
        "pathway_label",
        "x_value",
        "effect_value",
        "size_value",
    )
    assert enrichment_dotplot.additional_constraints == (
        "effect_scale_label_must_be_non_empty",
        "size_scale_label_must_be_non_empty",
        "panel_order_must_be_non_empty",
        "panel_order_count_must_be_at_most_two",
        "panel_ids_must_be_unique",
        "panel_titles_must_be_non_empty",
        "pathway_order_labels_must_be_unique",
        "points_must_be_non_empty",
        "point_panel_ids_must_match_declared_panels",
        "point_pathway_labels_must_match_declared_pathways",
        "point_x_values_must_be_finite",
        "point_effect_values_must_be_finite",
        "point_size_values_must_be_non_negative",
        "declared_panel_pathway_grid_must_be_complete_and_unique",
    )
    assert omics_volcano.template_ids == (_full_id("omics_volcano_panel"),)
    assert omics_volcano.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "legend_title",
        "effect_threshold",
        "significance_threshold",
        "panel_order",
        "points",
    )
    assert omics_volcano.display_optional_fields == ("paper_role",)
    assert omics_volcano.collection_required_fields["panel_order"] == ("panel_id", "panel_title")
    assert omics_volcano.collection_required_fields["points"] == (
        "panel_id",
        "feature_label",
        "effect_value",
        "significance_value",
        "regulation_class",
    )
    assert omics_volcano.collection_optional_fields["points"] == ("label_text",)
    assert omics_volcano.additional_constraints == (
        "legend_title_must_be_non_empty",
        "effect_threshold_must_be_positive",
        "significance_threshold_must_be_positive",
        "panel_order_must_be_non_empty",
        "panel_order_count_must_be_at_most_two",
        "panel_ids_must_be_unique",
        "panel_titles_must_be_non_empty",
        "points_must_be_non_empty",
        "point_panel_ids_must_match_declared_panels",
        "each_declared_panel_must_contain_points",
        "point_feature_labels_must_be_unique_within_panel",
        "point_effect_values_must_be_finite",
        "point_significance_values_must_be_non_negative",
        "point_regulation_classes_must_use_supported_vocabulary",
        "point_label_text_must_be_non_empty_when_present",
    )
    assert oncoplot_landscape.template_ids == (_full_id("oncoplot_mutation_landscape_panel"),)
    assert oncoplot_landscape.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "burden_axis_label",
        "frequency_axis_label",
        "mutation_legend_title",
        "gene_order",
        "sample_order",
        "annotation_tracks",
        "mutation_records",
    )
    assert oncoplot_landscape.collection_required_fields == {
        "gene_order": ("label",),
        "sample_order": ("sample_id",),
        "annotation_tracks": ("track_id", "track_label", "values"),
        "mutation_records": ("sample_id", "gene_label", "alteration_class"),
    }
    assert oncoplot_landscape.nested_collection_required_fields == {
        "annotation_tracks.values": ("sample_id", "category_label"),
    }
    assert oncoplot_landscape.additional_constraints == (
        "y_label_must_be_non_empty",
        "burden_axis_label_must_be_non_empty",
        "frequency_axis_label_must_be_non_empty",
        "mutation_legend_title_must_be_non_empty",
        "gene_order_must_be_non_empty",
        "gene_order_labels_must_be_unique",
        "sample_order_must_be_non_empty",
        "sample_ids_must_be_unique",
        "annotation_tracks_must_be_non_empty",
        "annotation_track_count_must_be_at_most_three",
        "annotation_track_ids_must_be_unique",
        "annotation_track_labels_must_be_non_empty",
        "annotation_track_sample_coverage_must_match_declared_sample_order",
        "annotation_track_category_labels_must_be_non_empty",
        "mutation_records_must_be_non_empty",
        "mutation_sample_ids_must_match_declared_sample_order",
        "mutation_gene_labels_must_match_declared_gene_order",
        "mutation_sample_gene_coordinates_must_be_unique",
        "alteration_class_must_be_supported",
    )

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

    assert forest.template_ids == (_full_id("forest_effect_main"), _full_id("subgroup_forest"))
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
    assert "performance_heatmap_inputs_v1" in next(
        item for item in module.list_display_schema_classes() if item.class_id == "matrix_pattern"
    ).input_schema_ids
    assert performance_heatmap.template_ids == (_full_id("performance_heatmap"),)
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


def test_shap_bar_importance_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    shap_bar = module.get_input_schema_contract("shap_bar_importance_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert shap_bar.template_ids == (_full_id("shap_bar_importance"),)
    assert shap_bar.display_name == "SHAP Bar Importance Panel"
    assert shap_bar.collection_required_fields["bars"] == ("rank", "feature", "importance_value")
    assert "bars_must_be_non_empty" in shap_bar.additional_constraints
    assert "bar_features_must_be_unique" in shap_bar.additional_constraints
    assert "bar_ranks_must_be_strictly_increasing" in shap_bar.additional_constraints
    assert "bar_importance_values_must_be_non_negative_finite" in shap_bar.additional_constraints
    assert "bar_importance_values_must_be_sorted_descending_by_rank" in shap_bar.additional_constraints
    assert _full_id("shap_bar_importance") in model_explanation_class.template_ids
    assert "shap_bar_importance_inputs_v1" in model_explanation_class.input_schema_ids


def test_shap_signed_importance_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    signed_panel = module.get_input_schema_contract("shap_signed_importance_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert signed_panel.template_ids == (_full_id("shap_signed_importance_panel"),)
    assert signed_panel.display_name == "SHAP Signed Importance Panel"
    assert signed_panel.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "negative_label",
        "positive_label",
        "bars",
    )
    assert signed_panel.collection_required_fields["bars"] == ("rank", "feature", "signed_importance_value")
    assert "bars_must_be_non_empty" in signed_panel.additional_constraints
    assert "bar_features_must_be_unique" in signed_panel.additional_constraints
    assert "bar_ranks_must_be_strictly_increasing" in signed_panel.additional_constraints
    assert "bar_signed_importance_values_must_be_finite_and_non_zero" in signed_panel.additional_constraints
    assert "bar_signed_importance_values_must_be_sorted_by_absolute_magnitude_descending" in signed_panel.additional_constraints
    assert _full_id("shap_signed_importance_panel") in model_explanation_class.template_ids
    assert "shap_signed_importance_panel_inputs_v1" in model_explanation_class.input_schema_ids


def test_shap_multicohort_importance_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    multicohort_panel = module.get_input_schema_contract("shap_multicohort_importance_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert multicohort_panel.template_ids == (_full_id("shap_multicohort_importance_panel"),)
    assert multicohort_panel.display_name == "SHAP Multicohort Importance Panel"
    assert multicohort_panel.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "panels",
    )
    assert multicohort_panel.collection_required_fields["panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "cohort_label",
        "bars",
    )
    assert multicohort_panel.nested_collection_required_fields["panels.bars"] == (
        "rank",
        "feature",
        "importance_value",
    )
    assert "panels_must_be_non_empty" in multicohort_panel.additional_constraints
    assert "panel_count_must_not_exceed_three" in multicohort_panel.additional_constraints
    assert "panel_ids_must_be_unique" in multicohort_panel.additional_constraints
    assert "panel_labels_must_be_unique" in multicohort_panel.additional_constraints
    assert "panel_cohort_labels_must_be_unique" in multicohort_panel.additional_constraints
    assert "panel_bars_must_be_non_empty" in multicohort_panel.additional_constraints
    assert "panel_bar_features_must_be_unique_within_panel" in multicohort_panel.additional_constraints
    assert "panel_bar_ranks_must_be_strictly_increasing" in multicohort_panel.additional_constraints
    assert "panel_bar_importance_values_must_be_non_negative_finite" in multicohort_panel.additional_constraints
    assert "panel_bar_importance_values_must_be_sorted_descending_by_rank" in multicohort_panel.additional_constraints
    assert "panel_feature_orders_must_match_across_panels" in multicohort_panel.additional_constraints
    assert _full_id("shap_multicohort_importance_panel") in model_explanation_class.template_ids
    assert "shap_multicohort_importance_panel_inputs_v1" in model_explanation_class.input_schema_ids


def test_generalizability_subgroup_composite_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    composite = module.get_input_schema_contract("generalizability_subgroup_composite_inputs_v1")
    generalizability_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "generalizability"
    )

    assert composite.template_ids == (_full_id("generalizability_subgroup_composite_panel"),)
    assert composite.display_name == "Generalizability and Subgroup Composite Panel"
    assert composite.collection_required_fields["overview_rows"] == (
        "cohort_id",
        "cohort_label",
        "support_count",
        "metric_value",
    )
    assert composite.collection_required_fields["subgroup_rows"] == (
        "subgroup_id",
        "subgroup_label",
        "estimate",
        "lower",
        "upper",
    )
    assert "overview_rows_must_be_non_empty" in composite.additional_constraints
    assert "overview_metric_values_must_be_finite" in composite.additional_constraints
    assert "subgroup_rows_must_satisfy_lower_le_estimate_le_upper" in composite.additional_constraints
    assert _full_id("generalizability_subgroup_composite_panel") in generalizability_class.template_ids
    assert "generalizability_subgroup_composite_inputs_v1" in generalizability_class.input_schema_ids


def test_compact_effect_estimate_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    compact = module.get_input_schema_contract("compact_effect_estimate_panel_inputs_v1")
    effect_estimate_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "effect_estimate"
    )

    assert compact.template_ids == (_full_id("compact_effect_estimate_panel"),)
    assert compact.display_name == "Compact Effect Estimate Panel"
    assert compact.collection_required_fields["panels"] == ("panel_id", "panel_label", "title", "rows")
    assert compact.nested_collection_required_fields["panels.rows"] == (
        "row_id",
        "row_label",
        "estimate",
        "lower",
        "upper",
    )
    assert "panel_count_must_be_between_two_and_four" in compact.additional_constraints
    assert "panel_row_orders_must_match_across_panels" in compact.additional_constraints
    assert _full_id("compact_effect_estimate_panel") in effect_estimate_class.template_ids
    assert "compact_effect_estimate_panel_inputs_v1" in effect_estimate_class.input_schema_ids


def test_broader_heterogeneity_summary_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    broader = module.get_input_schema_contract("broader_heterogeneity_summary_panel_inputs_v1")
    effect_estimate_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "effect_estimate"
    )

    assert broader.template_ids == (_full_id("broader_heterogeneity_summary_panel"),)
    assert broader.display_name == "Broader Heterogeneity Summary Panel"
    assert broader.collection_required_fields["slices"] == ("slice_id", "slice_label", "slice_kind", "slice_order")
    assert broader.collection_required_fields["effect_rows"] == ("row_id", "row_label", "verdict", "slice_estimates")
    assert broader.nested_collection_required_fields["effect_rows.slice_estimates"] == (
        "slice_id",
        "estimate",
        "lower",
        "upper",
    )
    assert "slice_count_must_be_between_two_and_five" in broader.additional_constraints
    assert "slice_kinds_must_be_supported" in broader.additional_constraints
    assert "effect_row_verdicts_must_be_supported" in broader.additional_constraints
    assert "effect_row_slice_estimates_must_cover_declared_slices_exactly_once" in broader.additional_constraints
    assert _full_id("broader_heterogeneity_summary_panel") in effect_estimate_class.template_ids
    assert "broader_heterogeneity_summary_panel_inputs_v1" in effect_estimate_class.input_schema_ids


def test_center_transportability_governance_summary_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    transportability = module.get_input_schema_contract("center_transportability_governance_summary_panel_inputs_v1")
    generalizability_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "generalizability"
    )

    assert transportability.template_ids == (_full_id("center_transportability_governance_summary_panel"),)
    assert transportability.display_name == "Center Transportability Governance Summary Panel"
    assert transportability.collection_required_fields["centers"] == (
        "center_id",
        "center_label",
        "cohort_role",
        "support_count",
        "event_count",
        "metric_estimate",
        "metric_lower",
        "metric_upper",
        "max_shift",
        "slope",
        "oe_ratio",
        "verdict",
        "action",
    )
    assert "metric_family_must_be_supported" in transportability.additional_constraints
    assert "center_metric_intervals_must_wrap_estimate" in transportability.additional_constraints
    assert "center_max_shift_must_be_probability" in transportability.additional_constraints
    assert "center_verdicts_must_be_supported" in transportability.additional_constraints
    assert _full_id("center_transportability_governance_summary_panel") in generalizability_class.template_ids
    assert "center_transportability_governance_summary_panel_inputs_v1" in generalizability_class.input_schema_ids


def test_render_display_template_catalog_covers_all_registered_templates() -> None:
    module = importlib.import_module("med_autoscience.display_template_catalog")

    markdown = module.render_display_template_catalog_markdown()

    assert "| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |" in markdown
    assert "`A. Predictive Performance and Decision`" in markdown
    assert "`H. Cohort and Study Design Evidence`" in markdown
    assert _full_id("roc_curve_binary") in markdown
    assert "shap_summary_inputs_v1" in markdown
    assert _full_id("cohort_flow_figure") in markdown
    assert _full_id("center_coverage_batch_transportability_panel") in markdown
    assert _full_id("table1_baseline_characteristics") in markdown
    assert _full_id("time_dependent_roc_horizon") in markdown
    assert _full_id("time_dependent_roc_comparison_panel") in markdown
    assert _full_id("single_cell_atlas_overview_panel") in markdown
    assert _full_id("atlas_spatial_bridge_panel") in markdown
    assert _full_id("trajectory_progression_panel") in markdown
    assert _full_id("atlas_spatial_trajectory_density_coverage_panel") in markdown
    assert _full_id("atlas_spatial_trajectory_context_support_panel") in markdown
    assert _full_id("broader_heterogeneity_summary_panel") in markdown
    assert _full_id("center_transportability_governance_summary_panel") in markdown
    assert "time_dependent_roc_comparison_inputs_v1" in markdown
    assert "single_cell_atlas_overview_inputs_v1" in markdown
    assert "atlas_spatial_bridge_panel_inputs_v1" in markdown
    assert "trajectory_progression_inputs_v1" in markdown
    assert "atlas_spatial_trajectory_density_coverage_panel_inputs_v1" in markdown
    assert "atlas_spatial_trajectory_context_support_panel_inputs_v1" in markdown
    assert "broader_heterogeneity_summary_panel_inputs_v1" in markdown
    assert "center_transportability_governance_summary_panel_inputs_v1" in markdown
    assert _full_id("time_to_event_landmark_performance_panel") in markdown
    assert "time_to_event_landmark_performance_inputs_v1" in markdown
    assert _full_id("time_to_event_threshold_governance_panel") in markdown
    assert "time_to_event_threshold_governance_inputs_v1" in markdown
    assert _full_id("time_to_event_multihorizon_calibration_panel") in markdown
    assert "time_to_event_multihorizon_calibration_inputs_v1" in markdown
    assert _full_id("time_to_event_stratified_cumulative_incidence_panel") in markdown
    assert "time_to_event_stratified_cumulative_incidence_inputs_v1" in markdown
    assert _full_id("tsne_scatter_grouped") in markdown
    assert _full_id("celltype_signature_heatmap") in markdown
    assert "celltype_signature_heatmap_inputs_v1" in markdown
    assert "center_coverage_batch_transportability_panel_inputs_v1" in markdown
    assert _full_id("shap_dependence_panel") in markdown
    assert "shap_dependence_panel_inputs_v1" in markdown
    assert _full_id("shap_bar_importance") in markdown
    assert "shap_bar_importance_inputs_v1" in markdown
    assert _full_id("shap_signed_importance_panel") in markdown
    assert "shap_signed_importance_panel_inputs_v1" in markdown
    assert _full_id("shap_multicohort_importance_panel") in markdown
    assert "shap_multicohort_importance_panel_inputs_v1" in markdown
    assert _full_id("shap_waterfall_local_explanation_panel") in markdown
    assert "shap_waterfall_local_explanation_panel_inputs_v1" in markdown
    assert _full_id("shap_force_like_summary_panel") in markdown
    assert "shap_force_like_summary_panel_inputs_v1" in markdown
    assert _full_id("shap_grouped_local_explanation_panel") in markdown
    assert "shap_grouped_local_explanation_panel_inputs_v1" in markdown
    assert _full_id("shap_grouped_decision_path_panel") in markdown
    assert "shap_grouped_decision_path_panel_inputs_v1" in markdown
    assert _full_id("shap_multigroup_decision_path_panel") in markdown
    assert "shap_multigroup_decision_path_panel_inputs_v1" in markdown
    assert _full_id("shap_grouped_local_support_domain_panel") in markdown
    assert "shap_grouped_local_support_domain_panel_inputs_v1" in markdown
    assert _full_id("partial_dependence_ice_panel") in markdown
    assert "partial_dependence_ice_panel_inputs_v1" in markdown
    assert _full_id("partial_dependence_interaction_contour_panel") in markdown
    assert "partial_dependence_interaction_contour_panel_inputs_v1" in markdown
    assert _full_id("feature_response_support_domain_panel") in markdown
    assert "feature_response_support_domain_panel_inputs_v1" in markdown
    assert _full_id("performance_heatmap") in markdown
    assert "performance_heatmap_inputs_v1" in markdown
    assert _full_id("clustered_heatmap") in markdown
    assert "clustered_heatmap_inputs_v1" in markdown
    assert _full_id("gsva_ssgsea_heatmap") in markdown
    assert "gsva_ssgsea_heatmap_inputs_v1" in markdown
    assert _full_id("pathway_enrichment_dotplot_panel") in markdown
    assert "pathway_enrichment_dotplot_panel_inputs_v1" in markdown
    assert _full_id("omics_volcano_panel") in markdown
    assert "omics_volcano_panel_inputs_v1" in markdown
    assert _full_id("oncoplot_mutation_landscape_panel") in markdown
    assert "oncoplot_mutation_landscape_panel_inputs_v1" in markdown
    assert _full_id("subgroup_forest") in markdown
    assert _full_id("generalizability_subgroup_composite_panel") in markdown
    assert "generalizability_subgroup_composite_inputs_v1" in markdown
    assert _full_id("compact_effect_estimate_panel") in markdown
    assert "compact_effect_estimate_panel_inputs_v1" in markdown
    assert _full_id("time_to_event_discrimination_calibration_panel") in markdown
    assert "time_to_event_decision_curve_inputs_v1" in markdown
    assert _full_id("multicenter_generalizability_overview") in markdown
    assert _full_id("risk_layering_monotonic_bars") in markdown
    assert _full_id("binary_calibration_decision_curve_panel") in markdown
    assert _full_id("model_complexity_audit_panel") in markdown
    assert _full_id("table2_time_to_event_performance_summary") in markdown
    assert _full_id("performance_summary_table_generic") in markdown
    assert _full_id("grouped_risk_event_summary_table") in markdown


def test_checked_in_template_catalog_guide_matches_renderer_output() -> None:
    module = importlib.import_module("med_autoscience.display_template_catalog")
    guide_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "capabilities"
        / "medical-display"
        / "medical_display_template_catalog.md"
    )

    assert guide_path.read_text(encoding="utf-8") == module.render_display_template_catalog_markdown()


def test_checked_in_display_audit_guide_tracks_current_counts_and_class_map() -> None:
    schema_module = importlib.import_module("med_autoscience.display_schema_contract")
    registry_module = importlib.import_module("med_autoscience.display_registry")
    guide_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "capabilities"
        / "medical-display"
        / "medical_display_audit_guide.md"
    )

    guide_text = guide_path.read_text(encoding="utf-8")
    evidence_classes = [
        display_class
        for display_class in schema_module.list_display_schema_classes()
        if display_class.class_id != "publication_shells_and_tables"
    ]

    assert f"- Evidence figure classes: `{len(evidence_classes)}`" in guide_text
    assert f"- Implemented evidence figure templates: `{len(registry_module.list_evidence_figure_specs())}`" in guide_text
    assert f"- Illustration shells: `{len(registry_module.list_illustration_shell_specs())}`" in guide_text
    assert f"- Table shells: `{len(registry_module.list_table_shell_specs())}`" in guide_text
    total_templates = (
        len(registry_module.list_evidence_figure_specs())
        + len(registry_module.list_illustration_shell_specs())
        + len(registry_module.list_table_shell_specs())
    )
    assert f"- Total implemented display templates: `{total_templates}`" in guide_text

    for display_class in evidence_classes:
        assert display_class.display_name in guide_text


def test_checked_in_display_audit_guide_mentions_all_registered_publication_shells_and_tables() -> None:
    registry_module = importlib.import_module("med_autoscience.display_registry")
    guide_path = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "capabilities"
        / "medical-display"
        / "medical_display_audit_guide.md"
    )

    guide_text = guide_path.read_text(encoding="utf-8")

    for shell in registry_module.list_illustration_shell_specs():
        assert shell.shell_id in guide_text
        assert shell.input_schema_id in guide_text

    for table in registry_module.list_table_shell_specs():
        assert table.shell_id in guide_text
        assert table.input_schema_id in guide_text


def test_display_platform_truth_docs_track_current_paper_proven_baseline() -> None:
    docs_root = Path(__file__).resolve().parents[1] / "docs" / "capabilities" / "medical-display"
    roadmap_text = (docs_root / "medical_display_family_roadmap.md").read_text(encoding="utf-8")
    audit_text = (docs_root / "medical_display_audit_guide.md").read_text(encoding="utf-8")
    catalog_text = (docs_root / "medical_display_template_catalog.md").read_text(encoding="utf-8")

    expected_short_templates = (
        "binary_calibration_decision_curve_panel",
        "time_to_event_discrimination_calibration_panel",
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
        "submission_graphical_abstract",
    )

    for text in (roadmap_text, audit_text, catalog_text):
        assert "Current Paper-Proven Baseline (001/003)" in text

    for template_id in expected_short_templates:
        assert template_id in roadmap_text
        assert _full_id(template_id) in audit_text
        assert _full_id(template_id) in catalog_text
