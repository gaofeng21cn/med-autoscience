from .shared import *

def test_shap_multigroup_decision_path_support_domain_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    explanation_scene = module.get_input_schema_contract("shap_multigroup_decision_path_support_domain_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert explanation_scene.template_ids == (_full_id("shap_multigroup_decision_path_support_domain_panel"),)
    assert explanation_scene.display_name == "SHAP Multigroup Decision Path Support-Domain Panel"
    assert explanation_scene.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "decision_panel_title",
        "decision_x_label",
        "decision_y_label",
        "decision_legend_title",
        "support_y_label",
        "support_legend_title",
        "baseline_value",
        "groups",
        "support_panels",
    )
    assert explanation_scene.collection_required_fields["groups"] == (
        "group_id",
        "group_label",
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
    assert explanation_scene.nested_collection_required_fields["groups.contributions"] == (
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
    assert "group_count_must_equal_three" in explanation_scene.additional_constraints
    assert "group_prediction_value_must_equal_baseline_plus_contributions" in explanation_scene.additional_constraints
    assert "group_feature_orders_must_match" in explanation_scene.additional_constraints
    assert "support_panel_count_must_equal_two" in explanation_scene.additional_constraints
    assert "support_panel_features_must_be_subset_of_group_feature_order" in explanation_scene.additional_constraints
    assert "support_panel_feature_order_must_follow_group_feature_order" in explanation_scene.additional_constraints
    assert "support_panel_support_segments_must_cover_curve_range" in explanation_scene.additional_constraints
    assert _full_id("shap_multigroup_decision_path_support_domain_panel") in model_explanation_class.template_ids
    assert "shap_multigroup_decision_path_support_domain_panel_inputs_v1" in model_explanation_class.input_schema_ids

def test_shap_signed_importance_local_support_domain_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    explanation_scene = module.get_input_schema_contract("shap_signed_importance_local_support_domain_panel_inputs_v1")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    assert explanation_scene.template_ids == (_full_id("shap_signed_importance_local_support_domain_panel"),)
    assert explanation_scene.display_name == "SHAP Signed Importance Local Support-Domain Panel"
    assert explanation_scene.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "support_y_label",
        "support_legend_title",
        "importance_panel",
        "local_panel",
        "support_panels",
    )
    assert explanation_scene.collection_required_fields["importance_panel.bars"] == (
        "rank",
        "feature",
        "signed_importance_value",
    )
    assert explanation_scene.collection_required_fields["local_panel.contributions"] == (
        "feature",
        "shap_value",
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
    assert explanation_scene.nested_collection_required_fields["support_panels.response_curve"] == ("x", "y")
    assert explanation_scene.nested_collection_required_fields["support_panels.support_segments"] == (
        "segment_id",
        "segment_label",
        "support_kind",
        "domain_start",
        "domain_end",
    )
    assert "importance_bars_must_be_non_empty" in explanation_scene.additional_constraints
    assert "local_panel_prediction_value_must_equal_baseline_plus_contributions" in explanation_scene.additional_constraints
    assert "support_panel_count_must_equal_two" in explanation_scene.additional_constraints
    assert "local_panel_feature_order_must_follow_global_feature_order" in explanation_scene.additional_constraints
    assert "support_panel_feature_order_must_follow_global_feature_order" in explanation_scene.additional_constraints
    assert _full_id("shap_signed_importance_local_support_domain_panel") in model_explanation_class.template_ids
    assert "shap_signed_importance_local_support_domain_panel_inputs_v1" in model_explanation_class.input_schema_ids

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

def test_interaction_effect_summary_panel_schema_contract_is_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    interaction = module.get_input_schema_contract("interaction_effect_summary_panel_inputs_v1")
    effect_estimate_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "effect_estimate"
    )

    assert interaction.template_ids == (_full_id("interaction_effect_summary_panel"),)
    assert interaction.display_name == "Interaction Effect Summary Panel"
    assert interaction.collection_required_fields["modifiers"] == (
        "modifier_id",
        "modifier_label",
        "interaction_estimate",
        "lower",
        "upper",
        "support_n",
        "favored_group_label",
        "interaction_p_value",
        "verdict",
    )
    assert "modifier_count_must_be_between_two_and_six" in interaction.additional_constraints
    assert "modifier_ids_must_be_unique" in interaction.additional_constraints
    assert "modifier_labels_must_be_unique" in interaction.additional_constraints
    assert "interaction_estimates_must_be_finite" in interaction.additional_constraints
    assert "interaction_intervals_must_wrap_estimate" in interaction.additional_constraints
    assert "interaction_p_values_must_be_between_zero_and_one" in interaction.additional_constraints
    assert "modifier_verdicts_must_use_controlled_vocabulary" in interaction.additional_constraints
    assert _full_id("interaction_effect_summary_panel") in effect_estimate_class.template_ids
    assert "interaction_effect_summary_panel_inputs_v1" in effect_estimate_class.input_schema_ids

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
    assert _full_id("interaction_effect_summary_panel") in markdown
    assert _full_id("center_transportability_governance_summary_panel") in markdown
    assert "time_dependent_roc_comparison_inputs_v1" in markdown
    assert "single_cell_atlas_overview_inputs_v1" in markdown
    assert "atlas_spatial_bridge_panel_inputs_v1" in markdown
    assert "trajectory_progression_inputs_v1" in markdown
    assert "atlas_spatial_trajectory_density_coverage_panel_inputs_v1" in markdown
    assert "atlas_spatial_trajectory_context_support_panel_inputs_v1" in markdown
    assert "broader_heterogeneity_summary_panel_inputs_v1" in markdown
    assert "interaction_effect_summary_panel_inputs_v1" in markdown
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
    assert _full_id("shap_multigroup_decision_path_support_domain_panel") in markdown
    assert "shap_multigroup_decision_path_support_domain_panel_inputs_v1" in markdown
    assert _full_id("shap_signed_importance_local_support_domain_panel") in markdown
    assert "shap_signed_importance_local_support_domain_panel_inputs_v1" in markdown
    assert _full_id("partial_dependence_ice_panel") in markdown
    assert "partial_dependence_ice_panel_inputs_v1" in markdown
    assert _full_id("partial_dependence_interaction_contour_panel") in markdown
    assert "partial_dependence_interaction_contour_panel_inputs_v1" in markdown
    assert _full_id("feature_response_support_domain_panel") in markdown
    assert "feature_response_support_domain_panel_inputs_v1" in markdown
    assert _full_id("performance_heatmap") in markdown
    assert "performance_heatmap_inputs_v1" in markdown
    assert _full_id("confusion_matrix_heatmap_binary") in markdown
    assert "confusion_matrix_heatmap_binary_inputs_v1" in markdown
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
    assert _full_id("cnv_recurrence_summary_panel") in markdown
    assert "cnv_recurrence_summary_panel_inputs_v1" in markdown
    assert _full_id("genomic_alteration_landscape_panel") in markdown
    assert "genomic_alteration_landscape_panel_inputs_v1" in markdown
    assert _full_id("genomic_alteration_consequence_panel") in markdown
    assert "genomic_alteration_consequence_panel_inputs_v1" in markdown
    assert _full_id("genomic_alteration_multiomic_consequence_panel") in markdown
    assert "genomic_alteration_multiomic_consequence_panel_inputs_v1" in markdown
    assert _full_id("genomic_alteration_pathway_integrated_composite_panel") in markdown
    assert "genomic_alteration_pathway_integrated_composite_panel_inputs_v1" in markdown
    assert _full_id("genomic_program_governance_summary_panel") in markdown
    assert "genomic_program_governance_summary_panel_inputs_v1" in markdown
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
        Path(__file__).resolve().parents[2]
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
        Path(__file__).resolve().parents[2]
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
        Path(__file__).resolve().parents[2]
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
    docs_root = Path(__file__).resolve().parents[2] / "docs" / "capabilities" / "medical-display"
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
