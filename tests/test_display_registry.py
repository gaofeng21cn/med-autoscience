from __future__ import annotations

import importlib

import pytest

from med_autoscience import display_registry


_CORE_PACK_ID = "fenggaolab.org.medical-display-core"


def _full_id(short_id: str) -> str:
    return f"{_CORE_PACK_ID}::{short_id}"


def test_registry_exposes_current_display_surface_inventory() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    evidence_specs = module.list_evidence_figure_specs()
    illustration_specs = module.list_illustration_shell_specs()
    table_specs = module.list_table_shell_specs()

    assert {item.template_id for item in evidence_specs} >= {
        _full_id("roc_curve_binary"),
        _full_id("pr_curve_binary"),
        _full_id("calibration_curve_binary"),
        _full_id("decision_curve_binary"),
        _full_id("clinical_impact_curve_binary"),
        _full_id("risk_layering_monotonic_bars"),
        _full_id("binary_calibration_decision_curve_panel"),
        _full_id("model_complexity_audit_panel"),
        _full_id("time_dependent_roc_horizon"),
        _full_id("time_dependent_roc_comparison_panel"),
        _full_id("time_to_event_landmark_performance_panel"),
        _full_id("time_to_event_threshold_governance_panel"),
        _full_id("time_to_event_multihorizon_calibration_panel"),
        _full_id("kaplan_meier_grouped"),
        _full_id("cumulative_incidence_grouped"),
        _full_id("time_to_event_stratified_cumulative_incidence_panel"),
        _full_id("umap_scatter_grouped"),
        _full_id("pca_scatter_grouped"),
        _full_id("phate_scatter_grouped"),
        _full_id("tsne_scatter_grouped"),
        _full_id("celltype_signature_heatmap"),
        _full_id("single_cell_atlas_overview_panel"),
        _full_id("atlas_spatial_bridge_panel"),
        _full_id("spatial_niche_map_panel"),
        _full_id("trajectory_progression_panel"),
        _full_id("atlas_spatial_trajectory_storyboard_panel"),
        _full_id("atlas_spatial_trajectory_density_coverage_panel"),
        _full_id("atlas_spatial_trajectory_context_support_panel"),
        _full_id("heatmap_group_comparison"),
        _full_id("performance_heatmap"),
        _full_id("correlation_heatmap"),
        _full_id("clustered_heatmap"),
        _full_id("gsva_ssgsea_heatmap"),
        _full_id("pathway_enrichment_dotplot_panel"),
        _full_id("omics_volcano_panel"),
        _full_id("oncoplot_mutation_landscape_panel"),
        _full_id("cnv_recurrence_summary_panel"),
        _full_id("genomic_alteration_landscape_panel"),
        _full_id("genomic_alteration_consequence_panel"),
        _full_id("genomic_alteration_multiomic_consequence_panel"),
        _full_id("genomic_program_governance_summary_panel"),
        _full_id("forest_effect_main"),
        _full_id("subgroup_forest"),
        _full_id("multivariable_forest"),
        _full_id("generalizability_subgroup_composite_panel"),
        _full_id("compact_effect_estimate_panel"),
        _full_id("coefficient_path_panel"),
        _full_id("broader_heterogeneity_summary_panel"),
        _full_id("interaction_effect_summary_panel"),
        _full_id("center_transportability_governance_summary_panel"),
        _full_id("shap_summary_beeswarm"),
        _full_id("shap_bar_importance"),
        _full_id("shap_dependence_panel"),
        _full_id("shap_waterfall_local_explanation_panel"),
        _full_id("shap_force_like_summary_panel"),
        _full_id("shap_grouped_decision_path_panel"),
        _full_id("shap_multigroup_decision_path_panel"),
        _full_id("shap_multigroup_decision_path_support_domain_panel"),
        _full_id("partial_dependence_interaction_contour_panel"),
        _full_id("feature_response_support_domain_panel"),
        _full_id("time_to_event_discrimination_calibration_panel"),
        _full_id("time_to_event_risk_group_summary"),
        _full_id("time_to_event_decision_curve"),
        _full_id("multicenter_generalizability_overview"),
    }
    assert {item.shell_id for item in illustration_specs} == {
        _full_id("cohort_flow_figure"),
        _full_id("submission_graphical_abstract"),
        _full_id("workflow_fact_sheet_panel"),
        _full_id("design_evidence_composite_shell"),
        _full_id("baseline_missingness_qc_panel"),
        _full_id("center_coverage_batch_transportability_panel"),
        _full_id("transportability_recalibration_governance_panel"),
    }
    assert {item.shell_id for item in table_specs} >= {
        _full_id("table1_baseline_characteristics"),
        _full_id("table2_time_to_event_performance_summary"),
        _full_id("table3_clinical_interpretation_summary"),
        _full_id("performance_summary_table_generic"),
        _full_id("grouped_risk_event_summary_table"),
    }


def test_get_evidence_figure_spec_accepts_namespaced_template_id() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("roc_curve_binary"))
    assert spec.template_id == _full_id("roc_curve_binary")


def test_local_architecture_overview_figure_alias_resolves_to_risk_layering_template() -> None:
    spec = display_registry.get_evidence_figure_spec("local_architecture_overview_figure")

    assert spec.template_id == _full_id("risk_layering_monotonic_bars")
    assert spec.input_schema_id == "risk_layering_monotonic_inputs_v1"
    assert display_registry.is_evidence_figure_template("local_architecture_overview_figure")


def test_time_to_event_threshold_governance_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("time_to_event_threshold_governance_panel"))

    assert spec.paper_family_ids == ("A", "B")
    assert spec.evidence_class == "clinical_utility"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "time_to_event_threshold_governance_inputs_v1"
    assert spec.layout_qc_profile == "publication_time_to_event_threshold_governance_panel"


def test_genomic_program_governance_summary_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("genomic_program_governance_summary_panel"))

    assert spec.template_id == _full_id("genomic_program_governance_summary_panel")
    assert spec.paper_family_ids == ("G",)
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "genomic_program_governance_summary_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_genomic_program_governance_summary_panel"


def test_clinical_impact_curve_binary_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("clinical_impact_curve_binary"))

    assert spec.paper_family_ids == ("A",)
    assert spec.evidence_class == "clinical_utility"
    assert spec.renderer_family == "r_ggplot2"
    assert spec.input_schema_id == "binary_prediction_curve_inputs_v1"
    assert spec.layout_qc_profile == "publication_evidence_curve"


def test_time_to_event_multihorizon_calibration_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("time_to_event_multihorizon_calibration_panel"))

    assert spec.paper_family_ids == ("A", "B")
    assert spec.evidence_class == "time_to_event"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "time_to_event_multihorizon_calibration_inputs_v1"
    assert spec.layout_qc_profile == "publication_time_to_event_multihorizon_calibration_panel"


def test_single_cell_atlas_overview_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("single_cell_atlas_overview_panel"))

    assert spec.paper_family_ids == ("D", "E", "G")
    assert spec.evidence_class == "data_geometry"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "single_cell_atlas_overview_inputs_v1"
    assert spec.layout_qc_profile == "publication_single_cell_atlas_overview_panel"


def test_atlas_spatial_bridge_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("atlas_spatial_bridge_panel"))

    assert spec.paper_family_ids == ("D", "E", "G")
    assert spec.evidence_class == "data_geometry"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "atlas_spatial_bridge_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_atlas_spatial_bridge_panel"


def test_phate_scatter_grouped_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("phate_scatter_grouped"))

    assert spec.paper_family_ids == ("D",)
    assert spec.evidence_class == "data_geometry"
    assert spec.renderer_family == "r_ggplot2"
    assert spec.input_schema_id == "embedding_grouped_inputs_v1"
    assert spec.layout_qc_profile == "publication_embedding_scatter"


def test_spatial_niche_map_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("spatial_niche_map_panel"))

    assert spec.paper_family_ids == ("D", "E", "G")
    assert spec.evidence_class == "data_geometry"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "spatial_niche_map_inputs_v1"
    assert spec.layout_qc_profile == "publication_spatial_niche_map_panel"


def test_trajectory_progression_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("trajectory_progression_panel"))

    assert spec.paper_family_ids == ("D", "E", "G")
    assert spec.evidence_class == "data_geometry"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "trajectory_progression_inputs_v1"
    assert spec.layout_qc_profile == "publication_trajectory_progression_panel"


def test_atlas_spatial_trajectory_storyboard_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("atlas_spatial_trajectory_storyboard_panel"))

    assert spec.paper_family_ids == ("D", "E", "G")
    assert spec.evidence_class == "data_geometry"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "atlas_spatial_trajectory_storyboard_inputs_v1"
    assert spec.layout_qc_profile == "publication_atlas_spatial_trajectory_storyboard_panel"


def test_atlas_spatial_trajectory_density_coverage_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("atlas_spatial_trajectory_density_coverage_panel"))

    assert spec.paper_family_ids == ("D", "E", "G")
    assert spec.evidence_class == "data_geometry"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "atlas_spatial_trajectory_density_coverage_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_atlas_spatial_trajectory_density_coverage_panel"


def test_atlas_spatial_trajectory_context_support_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("atlas_spatial_trajectory_context_support_panel"))

    assert spec.paper_family_ids == ("D", "E", "G")
    assert spec.evidence_class == "data_geometry"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "atlas_spatial_trajectory_context_support_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_atlas_spatial_trajectory_context_support_panel"


def test_atlas_spatial_trajectory_context_support_panel_keeps_stable_registry_order() -> None:
    evidence_template_ids = [item.template_id for item in display_registry.list_evidence_figure_specs()]

    assert evidence_template_ids.index(_full_id("atlas_spatial_trajectory_storyboard_panel")) < evidence_template_ids.index(
        _full_id("atlas_spatial_trajectory_density_coverage_panel")
    )
    assert evidence_template_ids.index(_full_id("atlas_spatial_trajectory_density_coverage_panel")) < evidence_template_ids.index(
        _full_id("atlas_spatial_trajectory_context_support_panel")
    )
    assert evidence_template_ids.index(_full_id("atlas_spatial_trajectory_context_support_panel")) < evidence_template_ids.index(
        _full_id("heatmap_group_comparison")
    )


def test_pathway_enrichment_dotplot_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("pathway_enrichment_dotplot_panel"))

    assert spec.paper_family_ids == ("E", "G")
    assert spec.evidence_class == "matrix_pattern"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "pathway_enrichment_dotplot_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_pathway_enrichment_dotplot_panel"


def test_multivariable_forest_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("multivariable_forest"))

    assert spec.paper_family_ids == ("C",)
    assert spec.evidence_class == "effect_estimate"
    assert spec.renderer_family == "r_ggplot2"
    assert spec.input_schema_id == "forest_effect_inputs_v1"
    assert spec.layout_qc_profile == "publication_forest_plot"


def test_omics_volcano_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("omics_volcano_panel"))

    assert spec.paper_family_ids == ("G",)
    assert spec.evidence_class == "data_geometry"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "omics_volcano_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_omics_volcano_panel"


def test_oncoplot_mutation_landscape_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("oncoplot_mutation_landscape_panel"))

    assert spec.paper_family_ids == ("G",)
    assert spec.evidence_class == "matrix_pattern"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "oncoplot_mutation_landscape_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_oncoplot_mutation_landscape_panel"


def test_cnv_recurrence_summary_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("cnv_recurrence_summary_panel"))

    assert spec.paper_family_ids == ("G",)
    assert spec.evidence_class == "matrix_pattern"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "cnv_recurrence_summary_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_cnv_recurrence_summary_panel"


def test_genomic_alteration_landscape_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("genomic_alteration_landscape_panel"))

    assert spec.paper_family_ids == ("G",)
    assert spec.evidence_class == "matrix_pattern"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "genomic_alteration_landscape_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_genomic_alteration_landscape_panel"


def test_genomic_alteration_consequence_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("genomic_alteration_consequence_panel"))

    assert spec.paper_family_ids == ("G",)
    assert spec.evidence_class == "matrix_pattern"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "genomic_alteration_consequence_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_genomic_alteration_consequence_panel"


def test_genomic_alteration_multiomic_consequence_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("genomic_alteration_multiomic_consequence_panel"))

    assert spec.paper_family_ids == ("G",)
    assert spec.evidence_class == "matrix_pattern"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "genomic_alteration_multiomic_consequence_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_genomic_alteration_multiomic_consequence_panel"


def test_genomic_alteration_pathway_integrated_composite_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("genomic_alteration_pathway_integrated_composite_panel"))

    assert spec.paper_family_ids == ("G",)
    assert spec.evidence_class == "matrix_pattern"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "genomic_alteration_pathway_integrated_composite_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_genomic_alteration_pathway_integrated_composite_panel"


def test_shap_waterfall_local_explanation_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_waterfall_local_explanation_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_waterfall_local_explanation_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_waterfall_local_explanation_panel"


def test_shap_force_like_summary_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_force_like_summary_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_force_like_summary_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_force_like_summary_panel"


def test_shap_grouped_local_explanation_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_grouped_local_explanation_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_grouped_local_explanation_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_grouped_local_explanation_panel"


def test_shap_grouped_decision_path_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_grouped_decision_path_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_grouped_decision_path_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_grouped_decision_path_panel"


def test_shap_multigroup_decision_path_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_multigroup_decision_path_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_multigroup_decision_path_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_multigroup_decision_path_panel"


def test_shap_multigroup_decision_path_support_domain_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_multigroup_decision_path_support_domain_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_multigroup_decision_path_support_domain_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_multigroup_decision_path_support_domain_panel"


def test_shap_bar_importance_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_bar_importance"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_bar_importance_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_bar_importance"


def test_shap_signed_importance_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_signed_importance_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_signed_importance_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_signed_importance_panel"


def test_shap_multicohort_importance_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_multicohort_importance_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_multicohort_importance_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_multicohort_importance_panel"


def test_partial_dependence_ice_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("partial_dependence_ice_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "partial_dependence_ice_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_partial_dependence_ice_panel"


def test_partial_dependence_interaction_contour_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("partial_dependence_interaction_contour_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "partial_dependence_interaction_contour_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_partial_dependence_interaction_contour_panel"


def test_partial_dependence_interaction_slice_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("partial_dependence_interaction_slice_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "partial_dependence_interaction_slice_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_partial_dependence_interaction_slice_panel"


def test_partial_dependence_subgroup_comparison_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("partial_dependence_subgroup_comparison_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "partial_dependence_subgroup_comparison_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_partial_dependence_subgroup_comparison_panel"


def test_accumulated_local_effects_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("accumulated_local_effects_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "accumulated_local_effects_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_accumulated_local_effects_panel"


def test_feature_response_support_domain_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("feature_response_support_domain_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "feature_response_support_domain_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_feature_response_support_domain_panel"


def test_shap_grouped_local_support_domain_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("shap_grouped_local_support_domain_panel"))

    assert spec.paper_family_ids == ("F",)
    assert spec.evidence_class == "model_explanation"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "shap_grouped_local_support_domain_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_shap_grouped_local_support_domain_panel"


def test_feature_response_support_domain_panel_keeps_stable_registry_order() -> None:
    evidence_template_ids = [item.template_id for item in display_registry.list_evidence_figure_specs()]

    assert evidence_template_ids.index(_full_id("accumulated_local_effects_panel")) < evidence_template_ids.index(
        _full_id("feature_response_support_domain_panel")
    )
    assert evidence_template_ids.index(_full_id("feature_response_support_domain_panel")) < evidence_template_ids.index(
        _full_id("shap_grouped_local_support_domain_panel")
    )
    assert evidence_template_ids.index(_full_id("shap_grouped_local_support_domain_panel")) < evidence_template_ids.index(
        _full_id("shap_multigroup_decision_path_support_domain_panel")
    )
    assert evidence_template_ids.index(
        _full_id("shap_multigroup_decision_path_support_domain_panel")
    ) < evidence_template_ids.index(
        _full_id("time_to_event_discrimination_calibration_panel")
    )


def test_generalizability_subgroup_composite_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("generalizability_subgroup_composite_panel"))

    assert spec.paper_family_ids == ("C", "H")
    assert spec.evidence_class == "generalizability"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "generalizability_subgroup_composite_inputs_v1"
    assert spec.layout_qc_profile == "publication_generalizability_subgroup_composite_panel"


def test_compact_effect_estimate_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("compact_effect_estimate_panel"))

    assert spec.paper_family_ids == ("C", "H")
    assert spec.evidence_class == "effect_estimate"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "compact_effect_estimate_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_compact_effect_estimate_panel"


def test_coefficient_path_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("coefficient_path_panel"))

    assert spec.paper_family_ids == ("C", "H")
    assert spec.evidence_class == "effect_estimate"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "coefficient_path_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_coefficient_path_panel"


def test_broader_heterogeneity_summary_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("broader_heterogeneity_summary_panel"))

    assert spec.paper_family_ids == ("C", "H")
    assert spec.evidence_class == "effect_estimate"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "broader_heterogeneity_summary_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_broader_heterogeneity_summary_panel"


def test_interaction_effect_summary_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("interaction_effect_summary_panel"))

    assert spec.paper_family_ids == ("C", "H")
    assert spec.evidence_class == "effect_estimate"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "interaction_effect_summary_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_interaction_effect_summary_panel"


def test_center_transportability_governance_summary_panel_is_registered() -> None:
    spec = display_registry.get_evidence_figure_spec(_full_id("center_transportability_governance_summary_panel"))

    assert spec.paper_family_ids == ("H",)
    assert spec.evidence_class == "generalizability"
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "center_transportability_governance_summary_panel_inputs_v1"
    assert spec.layout_qc_profile == "publication_center_transportability_governance_summary_panel"


def test_compact_effect_estimate_panel_keeps_stable_registry_order() -> None:
    evidence_template_ids = [item.template_id for item in display_registry.list_evidence_figure_specs()]

    assert evidence_template_ids.index(_full_id("generalizability_subgroup_composite_panel")) < evidence_template_ids.index(
        _full_id("compact_effect_estimate_panel")
    )
    assert evidence_template_ids.index(_full_id("compact_effect_estimate_panel")) < evidence_template_ids.index(
        _full_id("coefficient_path_panel")
    )
    assert evidence_template_ids.index(_full_id("coefficient_path_panel")) < evidence_template_ids.index(
        _full_id("broader_heterogeneity_summary_panel")
    )
    assert evidence_template_ids.index(_full_id("broader_heterogeneity_summary_panel")) < evidence_template_ids.index(
        _full_id("interaction_effect_summary_panel")
    )
    assert evidence_template_ids.index(_full_id("interaction_effect_summary_panel")) < evidence_template_ids.index(
        _full_id("center_transportability_governance_summary_panel")
    )
    assert evidence_template_ids.index(_full_id("center_transportability_governance_summary_panel")) < evidence_template_ids.index(
        _full_id("shap_summary_beeswarm")
    )


def test_workflow_fact_sheet_panel_is_registered() -> None:
    spec = display_registry.get_illustration_shell_spec(_full_id("workflow_fact_sheet_panel"))

    assert spec.paper_family_ids == ("H",)
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "workflow_fact_sheet_panel_inputs_v1"
    assert spec.shell_qc_profile == "publication_workflow_fact_sheet_panel"


def test_design_evidence_composite_shell_is_registered() -> None:
    spec = display_registry.get_illustration_shell_spec(_full_id("design_evidence_composite_shell"))

    assert spec.paper_family_ids == ("H",)
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "design_evidence_composite_shell_inputs_v1"
    assert spec.shell_qc_profile == "publication_design_evidence_composite_shell"


def test_baseline_missingness_qc_panel_is_registered() -> None:
    spec = display_registry.get_illustration_shell_spec(_full_id("baseline_missingness_qc_panel"))

    assert spec.paper_family_ids == ("H",)
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "baseline_missingness_qc_panel_inputs_v1"
    assert spec.shell_qc_profile == "publication_baseline_missingness_qc_panel"


def test_center_coverage_batch_transportability_panel_is_registered() -> None:
    spec = display_registry.get_illustration_shell_spec(_full_id("center_coverage_batch_transportability_panel"))

    assert spec.paper_family_ids == ("H",)
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "center_coverage_batch_transportability_panel_inputs_v1"
    assert spec.shell_qc_profile == "publication_center_coverage_batch_transportability_panel"


def test_transportability_recalibration_governance_panel_is_registered() -> None:
    spec = display_registry.get_illustration_shell_spec(_full_id("transportability_recalibration_governance_panel"))

    assert spec.paper_family_ids == ("H",)
    assert spec.renderer_family == "python"
    assert spec.input_schema_id == "transportability_recalibration_governance_panel_inputs_v1"
    assert spec.shell_qc_profile == "publication_transportability_recalibration_governance_panel"


def test_registry_exposes_pack_manifest_paper_proven_truth() -> None:
    evidence_spec = display_registry.get_evidence_figure_spec(_full_id("time_to_event_decision_curve"))
    shell_spec = display_registry.get_illustration_shell_spec(_full_id("submission_graphical_abstract"))
    table_spec = display_registry.get_table_shell_spec(_full_id("table2_time_to_event_performance_summary"))

    assert evidence_spec.paper_proven is True
    assert shell_spec.paper_proven is True
    assert table_spec.paper_proven is False


def test_time_to_event_publication_surface_specs_are_registered() -> None:
    figure7 = display_registry.get_evidence_figure_spec(_full_id("time_dependent_roc_horizon"))
    figure8 = display_registry.get_evidence_figure_spec(
        _full_id("time_dependent_roc_comparison_panel")
    )
    figure8b = display_registry.get_evidence_figure_spec(
        _full_id("time_to_event_landmark_performance_panel")
    )
    figure9 = display_registry.get_evidence_figure_spec(_full_id("tsne_scatter_grouped"))
    figure9b = display_registry.get_evidence_figure_spec(_full_id("celltype_signature_heatmap"))
    figure10 = display_registry.get_evidence_figure_spec(_full_id("performance_heatmap"))
    figure10b = display_registry.get_evidence_figure_spec(_full_id("clustered_heatmap"))
    figure10c = display_registry.get_evidence_figure_spec(_full_id("gsva_ssgsea_heatmap"))
    figure10d = display_registry.get_evidence_figure_spec(_full_id("pathway_enrichment_dotplot_panel"))
    figure12 = display_registry.get_evidence_figure_spec(_full_id("subgroup_forest"))
    figure13 = display_registry.get_evidence_figure_spec(_full_id("shap_dependence_panel"))
    figure14 = display_registry.get_evidence_figure_spec(
        _full_id("time_to_event_discrimination_calibration_panel")
    )
    figure15 = display_registry.get_evidence_figure_spec(_full_id("time_to_event_risk_group_summary"))
    figure16 = display_registry.get_evidence_figure_spec(_full_id("time_to_event_decision_curve"))
    figure17 = display_registry.get_evidence_figure_spec(
        _full_id("multicenter_generalizability_overview")
    )
    figure17b = display_registry.get_evidence_figure_spec(
        _full_id("generalizability_subgroup_composite_panel")
    )
    figure19 = display_registry.get_evidence_figure_spec(
        _full_id("time_to_event_stratified_cumulative_incidence_panel")
    )
    figure22 = display_registry.get_evidence_figure_spec(_full_id("risk_layering_monotonic_bars"))
    figure3 = display_registry.get_evidence_figure_spec(
        _full_id("binary_calibration_decision_curve_panel")
    )
    figure4 = display_registry.get_evidence_figure_spec(_full_id("model_complexity_audit_panel"))
    table2 = display_registry.get_table_shell_spec(_full_id("table2_time_to_event_performance_summary"))
    table3 = display_registry.get_table_shell_spec(_full_id("table3_clinical_interpretation_summary"))
    generic_performance = display_registry.get_table_shell_spec(
        _full_id("performance_summary_table_generic")
    )
    grouped_risk = display_registry.get_table_shell_spec(_full_id("grouped_risk_event_summary_table"))

    assert figure7.input_schema_id == "binary_prediction_curve_inputs_v1"
    assert figure7.template_id == _full_id("time_dependent_roc_horizon")
    assert figure7.evidence_class == "time_to_event"
    assert figure8.renderer_family == "python"
    assert figure8.input_schema_id == "time_dependent_roc_comparison_inputs_v1"
    assert figure8.layout_qc_profile == "publication_evidence_curve"
    assert figure8b.paper_family_ids == ("A", "B")
    assert figure8b.evidence_class == "time_to_event"
    assert figure8b.renderer_family == "python"
    assert figure8b.input_schema_id == "time_to_event_landmark_performance_inputs_v1"
    assert figure8b.layout_qc_profile == "publication_landmark_performance_panel"
    assert figure9.layout_qc_profile == "publication_embedding_scatter"
    assert figure9b.paper_family_ids == ("D", "E", "G")
    assert figure9b.evidence_class == "data_geometry"
    assert figure9b.renderer_family == "python"
    assert figure9b.input_schema_id == "celltype_signature_heatmap_inputs_v1"
    assert figure9b.layout_qc_profile == "publication_celltype_signature_panel"
    assert figure10.input_schema_id == "performance_heatmap_inputs_v1"
    assert figure10.layout_qc_profile == "publication_heatmap"
    assert figure10.paper_family_ids == ("B", "E")
    assert figure10.renderer_family == "r_ggplot2"
    assert figure10b.input_schema_id == "clustered_heatmap_inputs_v1"
    assert figure10b.layout_qc_profile == "publication_heatmap"
    assert figure10c.paper_family_ids == ("G",)
    assert figure10c.evidence_class == "matrix_pattern"
    assert figure10c.input_schema_id == "gsva_ssgsea_heatmap_inputs_v1"
    assert figure10c.layout_qc_profile == "publication_heatmap"
    assert figure10d.paper_family_ids == ("E", "G")
    assert figure10d.evidence_class == "matrix_pattern"
    assert figure10d.renderer_family == "python"
    assert figure10d.input_schema_id == "pathway_enrichment_dotplot_panel_inputs_v1"
    assert figure10d.layout_qc_profile == "publication_pathway_enrichment_dotplot_panel"
    assert figure12.input_schema_id == "forest_effect_inputs_v1"
    assert figure12.layout_qc_profile == "publication_forest_plot"
    assert figure13.paper_family_ids == ("F",)
    assert figure13.evidence_class == "model_explanation"
    assert figure13.renderer_family == "python"
    assert figure13.input_schema_id == "shap_dependence_panel_inputs_v1"
    assert figure13.layout_qc_profile == "publication_shap_dependence_panel"
    figure13b = display_registry.get_evidence_figure_spec(_full_id("shap_waterfall_local_explanation_panel"))
    assert figure13b.paper_family_ids == ("F",)
    assert figure13b.evidence_class == "model_explanation"
    assert figure13b.renderer_family == "python"
    assert figure13b.input_schema_id == "shap_waterfall_local_explanation_panel_inputs_v1"
    assert figure13b.layout_qc_profile == "publication_shap_waterfall_local_explanation_panel"
    figure13c = display_registry.get_evidence_figure_spec(_full_id("shap_force_like_summary_panel"))
    assert figure13c.paper_family_ids == ("F",)
    assert figure13c.evidence_class == "model_explanation"
    assert figure13c.renderer_family == "python"
    assert figure13c.input_schema_id == "shap_force_like_summary_panel_inputs_v1"
    assert figure13c.layout_qc_profile == "publication_shap_force_like_summary_panel"
    figure13d = display_registry.get_evidence_figure_spec(_full_id("partial_dependence_ice_panel"))
    assert figure13d.paper_family_ids == ("F",)
    assert figure13d.evidence_class == "model_explanation"
    assert figure13d.renderer_family == "python"
    assert figure13d.input_schema_id == "partial_dependence_ice_panel_inputs_v1"
    assert figure13d.layout_qc_profile == "publication_partial_dependence_ice_panel"
    assert figure14.renderer_family == "python"
    assert figure14.required_exports == ("png", "pdf")
    assert figure14.input_schema_id == "time_to_event_discrimination_calibration_inputs_v1"
    assert figure15.input_schema_id == "time_to_event_grouped_inputs_v1"
    assert figure16.layout_qc_profile == "publication_decision_curve"
    assert figure17.allowed_paper_roles == ("main_text", "supplementary")
    assert figure17.evidence_class == "generalizability"
    assert figure17b.paper_family_ids == ("C", "H")
    assert figure17b.evidence_class == "generalizability"
    assert figure17b.renderer_family == "python"
    assert figure17b.input_schema_id == "generalizability_subgroup_composite_inputs_v1"
    assert figure17b.layout_qc_profile == "publication_generalizability_subgroup_composite_panel"
    assert figure19.renderer_family == "python"
    assert figure19.input_schema_id == "time_to_event_stratified_cumulative_incidence_inputs_v1"
    assert figure19.layout_qc_profile == "publication_survival_curve"
    assert figure22.renderer_family == "python"
    assert figure22.input_schema_id == "risk_layering_monotonic_inputs_v1"
    assert figure22.layout_qc_profile == "publication_risk_layering_bars"
    assert figure3.input_schema_id == "binary_calibration_decision_curve_panel_inputs_v1"
    assert figure3.layout_qc_profile == "publication_binary_calibration_decision_curve"
    assert figure3.renderer_family == "python"
    assert figure4.evidence_class == "model_audit"
    assert figure4.input_schema_id == "model_complexity_audit_panel_inputs_v1"
    assert figure4.layout_qc_profile == "publication_model_complexity_audit"
    assert table2.shell_id == _full_id("table2_time_to_event_performance_summary")
    assert table2.required_exports == ("md",)
    assert table3.input_schema_id == "clinical_interpretation_summary_v1"
    assert table3.shell_id == _full_id("table3_clinical_interpretation_summary")
    assert generic_performance.input_schema_id == "performance_summary_table_generic_v1"
    assert generic_performance.shell_id == _full_id("performance_summary_table_generic")
    assert generic_performance.required_exports == ("csv", "md")
    assert grouped_risk.input_schema_id == "grouped_risk_event_summary_table_v1"
    assert grouped_risk.shell_id == _full_id("grouped_risk_event_summary_table")
    assert grouped_risk.table_qc_profile == "publication_table_interpretation"


def test_resolve_display_registry_rejects_unknown_template() -> None:
    module = importlib.import_module("med_autoscience.display_registry")

    with pytest.raises(ValueError, match="unknown evidence figure template"):
        module.get_evidence_figure_spec("unknown_template")
