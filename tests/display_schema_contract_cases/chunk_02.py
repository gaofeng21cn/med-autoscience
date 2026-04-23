from .shared import *

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
    multimanifold_context_support = module.get_input_schema_contract(
        "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1"
    )
    performance_heatmap = module.get_input_schema_contract("performance_heatmap_inputs_v1")
    confusion_heatmap = module.get_input_schema_contract("confusion_matrix_heatmap_binary_inputs_v1")
    clustered_heatmap = module.get_input_schema_contract("clustered_heatmap_inputs_v1")
    gsva_heatmap = module.get_input_schema_contract("gsva_ssgsea_heatmap_inputs_v1")
    enrichment_dotplot = module.get_input_schema_contract("pathway_enrichment_dotplot_panel_inputs_v1")
    celltype_marker_dotplot = module.get_input_schema_contract("celltype_marker_dotplot_panel_inputs_v1")
    omics_volcano = module.get_input_schema_contract("omics_volcano_panel_inputs_v1")
    oncoplot_landscape = module.get_input_schema_contract("oncoplot_mutation_landscape_panel_inputs_v1")
    cnv_recurrence = module.get_input_schema_contract("cnv_recurrence_summary_panel_inputs_v1")
    genomic_alteration_landscape = module.get_input_schema_contract("genomic_alteration_landscape_panel_inputs_v1")
    genomic_alteration_consequence = module.get_input_schema_contract(
        "genomic_alteration_consequence_panel_inputs_v1"
    )
    genomic_alteration_multiomic_consequence = module.get_input_schema_contract(
        "genomic_alteration_multiomic_consequence_panel_inputs_v1"
    )
    genomic_alteration_pathway_integrated = module.get_input_schema_contract(
        "genomic_alteration_pathway_integrated_composite_panel_inputs_v1"
    )
    genomic_program_governance_summary = module.get_input_schema_contract(
        "genomic_program_governance_summary_panel_inputs_v1"
    )
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
    assert celltype_marker_dotplot.template_ids == (_full_id("celltype_marker_dotplot_panel"),)
    assert celltype_marker_dotplot.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "effect_scale_label",
        "size_scale_label",
        "panel_order",
        "celltype_order",
        "marker_order",
        "points",
    )
    assert celltype_marker_dotplot.display_optional_fields == ("paper_role",)
    assert celltype_marker_dotplot.collection_required_fields["panel_order"] == ("panel_id", "panel_title")
    assert celltype_marker_dotplot.collection_required_fields["celltype_order"] == ("label",)
    assert celltype_marker_dotplot.collection_required_fields["marker_order"] == ("label",)
    assert celltype_marker_dotplot.collection_required_fields["points"] == (
        "panel_id",
        "celltype_label",
        "marker_label",
        "effect_value",
        "size_value",
    )
    assert celltype_marker_dotplot.additional_constraints == (
        "effect_scale_label_must_be_non_empty",
        "size_scale_label_must_be_non_empty",
        "panel_order_must_be_non_empty",
        "panel_order_count_must_be_at_most_two",
        "panel_ids_must_be_unique",
        "panel_titles_must_be_non_empty",
        "celltype_order_labels_must_be_unique",
        "marker_order_labels_must_be_unique",
        "points_must_be_non_empty",
        "point_panel_ids_must_match_declared_panels",
        "point_celltype_labels_must_match_declared_celltypes",
        "point_marker_labels_must_match_declared_markers",
        "point_effect_values_must_be_finite",
        "point_size_values_must_be_non_negative",
        "declared_panel_celltype_marker_grid_must_be_complete_and_unique",
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
    assert cnv_recurrence.template_ids == (_full_id("cnv_recurrence_summary_panel"),)
    assert cnv_recurrence.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "burden_axis_label",
        "frequency_axis_label",
        "cnv_legend_title",
        "region_order",
        "sample_order",
        "annotation_tracks",
        "cnv_records",
    )
    assert cnv_recurrence.collection_required_fields == {
        "region_order": ("label",),
        "sample_order": ("sample_id",),
        "annotation_tracks": ("track_id", "track_label", "values"),
        "cnv_records": ("sample_id", "region_label", "cnv_state"),
    }
    assert cnv_recurrence.nested_collection_required_fields == {
        "annotation_tracks.values": ("sample_id", "category_label"),
    }
    assert cnv_recurrence.additional_constraints == (
        "y_label_must_be_non_empty",
        "burden_axis_label_must_be_non_empty",
        "frequency_axis_label_must_be_non_empty",
        "cnv_legend_title_must_be_non_empty",
        "region_order_must_be_non_empty",
        "region_order_labels_must_be_unique",
        "sample_order_must_be_non_empty",
        "sample_ids_must_be_unique",
        "annotation_tracks_must_be_non_empty",
        "annotation_track_count_must_be_at_most_three",
        "annotation_track_ids_must_be_unique",
        "annotation_track_labels_must_be_non_empty",
        "annotation_track_sample_coverage_must_match_declared_sample_order",
        "annotation_track_category_labels_must_be_non_empty",
        "cnv_records_must_be_non_empty",
        "cnv_sample_ids_must_match_declared_sample_order",
        "cnv_region_labels_must_match_declared_region_order",
        "cnv_sample_region_coordinates_must_be_unique",
        "cnv_state_must_be_supported",
    )
    assert genomic_alteration_landscape.template_ids == (_full_id("genomic_alteration_landscape_panel"),)
    assert genomic_alteration_landscape.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "burden_axis_label",
        "frequency_axis_label",
        "alteration_legend_title",
        "gene_order",
        "sample_order",
        "annotation_tracks",
        "alteration_records",
    )
    assert genomic_alteration_landscape.collection_required_fields == {
        "gene_order": ("label",),
        "sample_order": ("sample_id",),
        "annotation_tracks": ("track_id", "track_label", "values"),
        "alteration_records": ("sample_id", "gene_label"),
    }
    assert genomic_alteration_landscape.nested_collection_required_fields == {
        "annotation_tracks.values": ("sample_id", "category_label"),
    }
    assert genomic_alteration_landscape.additional_constraints == (
        "y_label_must_be_non_empty",
        "burden_axis_label_must_be_non_empty",
        "frequency_axis_label_must_be_non_empty",
        "alteration_legend_title_must_be_non_empty",
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
        "alteration_records_must_be_non_empty",
        "alteration_sample_ids_must_match_declared_sample_order",
        "alteration_gene_labels_must_match_declared_gene_order",
        "alteration_sample_gene_coordinates_must_be_unique",
        "alteration_record_must_define_mutation_or_cnv",
        "mutation_class_must_be_supported_when_present",
        "cnv_state_must_be_supported_when_present",
    )
    assert genomic_alteration_consequence.template_ids == (_full_id("genomic_alteration_consequence_panel"),)
    assert genomic_alteration_consequence.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "burden_axis_label",
        "frequency_axis_label",
        "alteration_legend_title",
        "gene_order",
        "sample_order",
        "annotation_tracks",
        "alteration_records",
        "consequence_x_label",
        "consequence_y_label",
        "consequence_legend_title",
        "effect_threshold",
        "significance_threshold",
        "driver_gene_order",
        "consequence_panel_order",
        "consequence_points",
    )
    assert genomic_alteration_consequence.display_optional_fields == ("paper_role",)
    assert genomic_alteration_consequence.collection_required_fields["gene_order"] == ("label",)
    assert genomic_alteration_consequence.collection_required_fields["sample_order"] == ("sample_id",)
    assert genomic_alteration_consequence.collection_required_fields["annotation_tracks"] == (
        "track_id",
        "track_label",
        "values",
    )
    assert genomic_alteration_consequence.nested_collection_required_fields["annotation_tracks.values"] == (
        "sample_id",
        "category_label",
    )
    assert genomic_alteration_consequence.collection_required_fields["alteration_records"] == ("sample_id", "gene_label")
    assert genomic_alteration_consequence.collection_required_fields["driver_gene_order"] == ("label",)
    assert genomic_alteration_consequence.collection_required_fields["consequence_panel_order"] == (
        "panel_id",
        "panel_title",
    )
    assert genomic_alteration_consequence.collection_required_fields["consequence_points"] == (
        "panel_id",
        "gene_label",
        "effect_value",
        "significance_value",
        "regulation_class",
    )
    assert genomic_alteration_consequence.additional_constraints == (
        "y_label_must_be_non_empty",
        "burden_axis_label_must_be_non_empty",
        "frequency_axis_label_must_be_non_empty",
        "alteration_legend_title_must_be_non_empty",
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
        "alteration_records_must_be_non_empty",
        "alteration_sample_ids_must_match_declared_sample_order",
        "alteration_gene_labels_must_match_declared_gene_order",
        "alteration_sample_gene_coordinates_must_be_unique",
        "alteration_record_must_define_mutation_or_cnv",
        "mutation_class_must_be_supported_when_present",
        "cnv_state_must_be_supported_when_present",
        "consequence_x_label_must_be_non_empty",
        "consequence_y_label_must_be_non_empty",
        "consequence_legend_title_must_be_non_empty",
        "effect_threshold_must_be_positive",
        "significance_threshold_must_be_positive",
        "driver_gene_order_must_be_non_empty",
        "driver_gene_labels_must_be_unique",
        "driver_gene_labels_must_be_subset_of_gene_order",
        "consequence_panel_order_must_be_non_empty",
        "consequence_panel_order_count_must_be_at_most_two",
        "consequence_panel_ids_must_be_unique",
        "consequence_panel_titles_must_be_non_empty",
        "consequence_points_must_be_non_empty",
        "consequence_point_panel_ids_must_match_declared_panels",
        "consequence_point_gene_labels_must_match_declared_driver_genes",
        "consequence_point_coordinates_must_be_complete_and_unique",
        "consequence_point_effect_values_must_be_finite",
        "consequence_point_significance_values_must_be_non_negative",
        "consequence_point_regulation_classes_must_use_supported_vocabulary",
    )
    assert genomic_alteration_multiomic_consequence.template_ids == (
        _full_id("genomic_alteration_multiomic_consequence_panel"),
    )
    assert genomic_alteration_pathway_integrated.template_ids == (
        _full_id("genomic_alteration_pathway_integrated_composite_panel"),
    )
    assert genomic_program_governance_summary.template_ids == (
        _full_id("genomic_program_governance_summary_panel"),
    )
    assert genomic_program_governance_summary.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "evidence_panel_title",
        "summary_panel_title",
        "effect_scale_label",
        "support_scale_label",
        "layer_order",
        "programs",
    )
    assert genomic_program_governance_summary.display_optional_fields == ("paper_role",)
    assert genomic_program_governance_summary.collection_required_fields["layer_order"] == ("layer_id", "layer_label")
    assert genomic_program_governance_summary.collection_required_fields["programs"] == (
        "program_id",
        "program_label",
        "lead_driver_label",
        "dominant_pathway_label",
        "pathway_hit_count",
        "priority_rank",
        "priority_band",
        "verdict",
        "action",
        "layer_supports",
    )
    assert genomic_program_governance_summary.collection_optional_fields["programs"] == ("detail",)
    assert genomic_program_governance_summary.nested_collection_required_fields["programs.layer_supports"] == (
        "layer_id",
        "effect_value",
        "support_fraction",
    )
    assert genomic_alteration_pathway_integrated.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "burden_axis_label",
        "frequency_axis_label",
        "alteration_legend_title",
        "gene_order",
        "sample_order",
        "annotation_tracks",
        "alteration_records",
        "consequence_x_label",
        "consequence_y_label",
        "consequence_legend_title",
        "effect_threshold",
        "significance_threshold",
        "driver_gene_order",
        "consequence_panel_order",
        "consequence_points",
        "pathway_x_label",
        "pathway_y_label",
        "pathway_effect_scale_label",
        "pathway_size_scale_label",
        "pathway_order",
        "pathway_panel_order",
        "pathway_points",
    )
    assert genomic_alteration_pathway_integrated.display_optional_fields == ("paper_role",)
    assert genomic_alteration_pathway_integrated.collection_required_fields["pathway_order"] == ("label",)
    assert genomic_alteration_pathway_integrated.collection_required_fields["pathway_panel_order"] == (
        "panel_id",
        "panel_title",
    )
    assert genomic_alteration_pathway_integrated.collection_required_fields["pathway_points"] == (
        "panel_id",
        "pathway_label",
        "x_value",
        "effect_value",
        "size_value",
    )
    assert genomic_alteration_multiomic_consequence.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "burden_axis_label",
        "frequency_axis_label",
        "alteration_legend_title",
        "gene_order",
        "sample_order",
        "annotation_tracks",
        "alteration_records",
        "consequence_x_label",
        "consequence_y_label",
        "consequence_legend_title",
        "effect_threshold",
        "significance_threshold",
        "driver_gene_order",
        "consequence_panel_order",
        "consequence_points",
    )
    assert genomic_alteration_multiomic_consequence.display_optional_fields == ("paper_role",)
    assert genomic_alteration_multiomic_consequence.collection_required_fields["driver_gene_order"] == ("label",)
    assert genomic_alteration_multiomic_consequence.collection_required_fields["consequence_panel_order"] == (
        "panel_id",
        "panel_title",
    )
    assert genomic_alteration_multiomic_consequence.collection_required_fields["consequence_points"] == (
        "panel_id",
        "gene_label",
        "effect_value",
        "significance_value",
        "regulation_class",
    )
    assert genomic_alteration_multiomic_consequence.additional_constraints == (
        "y_label_must_be_non_empty",
        "burden_axis_label_must_be_non_empty",
        "frequency_axis_label_must_be_non_empty",
        "alteration_legend_title_must_be_non_empty",
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
        "alteration_records_must_be_non_empty",
        "alteration_sample_ids_must_match_declared_sample_order",
        "alteration_gene_labels_must_match_declared_gene_order",
        "alteration_sample_gene_coordinates_must_be_unique",
        "alteration_record_must_define_mutation_or_cnv",
        "mutation_class_must_be_supported_when_present",
        "cnv_state_must_be_supported_when_present",
        "consequence_x_label_must_be_non_empty",
        "consequence_y_label_must_be_non_empty",
        "consequence_legend_title_must_be_non_empty",
        "effect_threshold_must_be_positive",
        "significance_threshold_must_be_positive",
        "driver_gene_order_must_be_non_empty",
        "driver_gene_labels_must_be_unique",
        "driver_gene_labels_must_be_subset_of_gene_order",
        "consequence_panel_order_must_be_non_empty",
        "consequence_panel_order_count_must_equal_three",
        "consequence_panel_ids_must_match_multiomic_layers",
        "consequence_panel_titles_must_be_non_empty",
        "consequence_points_must_be_non_empty",
        "consequence_point_panel_ids_must_match_declared_panels",
        "consequence_point_gene_labels_must_match_declared_driver_genes",
        "consequence_point_coordinates_must_be_complete_and_unique",
        "consequence_point_effect_values_must_be_finite",
        "consequence_point_significance_values_must_be_non_negative",
        "consequence_point_regulation_classes_must_use_supported_vocabulary",
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
