from __future__ import annotations

from med_autoscience import display_registry

from .core import DisplaySchemaClass, _template_ids_for_evidence_class

_DISPLAY_SCHEMA_CLASSES: tuple[DisplaySchemaClass, ...] = (
    DisplaySchemaClass(
        class_id="prediction_performance",
        display_name="Prediction Performance",
        template_ids=_template_ids_for_evidence_class("prediction_performance"),
        input_schema_ids=("binary_prediction_curve_inputs_v1",),
    ),
    DisplaySchemaClass(
        class_id="clinical_utility",
        display_name="Clinical Utility",
        template_ids=_template_ids_for_evidence_class("clinical_utility"),
        input_schema_ids=(
            "binary_prediction_curve_inputs_v1",
            "time_to_event_decision_curve_inputs_v1",
            "time_to_event_threshold_governance_inputs_v1",
            "binary_calibration_decision_curve_panel_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="time_to_event",
        display_name="Time-to-Event",
        template_ids=_template_ids_for_evidence_class("time_to_event"),
        input_schema_ids=(
            "binary_prediction_curve_inputs_v1",
            "risk_layering_monotonic_inputs_v1",
            "time_dependent_roc_comparison_inputs_v1",
            "time_to_event_landmark_performance_inputs_v1",
            "time_to_event_multihorizon_calibration_inputs_v1",
            "time_to_event_grouped_inputs_v1",
            "time_to_event_stratified_cumulative_incidence_inputs_v1",
            "time_to_event_discrimination_calibration_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="data_geometry",
        display_name="Data Geometry",
        template_ids=_template_ids_for_evidence_class("data_geometry"),
        input_schema_ids=(
            "embedding_grouped_inputs_v1",
            "celltype_signature_heatmap_inputs_v1",
            "single_cell_atlas_overview_inputs_v1",
            "atlas_spatial_bridge_panel_inputs_v1",
            "spatial_niche_map_inputs_v1",
            "trajectory_progression_inputs_v1",
            "atlas_spatial_trajectory_storyboard_inputs_v1",
            "atlas_spatial_trajectory_density_coverage_panel_inputs_v1",
            "atlas_spatial_trajectory_context_support_panel_inputs_v1",
            "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1",
            "omics_volcano_panel_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="matrix_pattern",
        display_name="Matrix Pattern",
        template_ids=_template_ids_for_evidence_class("matrix_pattern"),
        input_schema_ids=(
            "heatmap_group_comparison_inputs_v1",
            "performance_heatmap_inputs_v1",
            "confusion_matrix_heatmap_binary_inputs_v1",
            "correlation_heatmap_inputs_v1",
            "clustered_heatmap_inputs_v1",
            "gsva_ssgsea_heatmap_inputs_v1",
            "pathway_enrichment_dotplot_panel_inputs_v1",
            "celltype_marker_dotplot_panel_inputs_v1",
            "oncoplot_mutation_landscape_panel_inputs_v1",
            "cnv_recurrence_summary_panel_inputs_v1",
            "genomic_alteration_landscape_panel_inputs_v1",
            "genomic_alteration_consequence_panel_inputs_v1",
            "genomic_alteration_multiomic_consequence_panel_inputs_v1",
            "genomic_alteration_pathway_integrated_composite_panel_inputs_v1",
            "genomic_program_governance_summary_panel_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="effect_estimate",
        display_name="Effect Estimate",
        template_ids=_template_ids_for_evidence_class("effect_estimate"),
        input_schema_ids=(
            "forest_effect_inputs_v1",
            "compact_effect_estimate_panel_inputs_v1",
            "coefficient_path_panel_inputs_v1",
            "broader_heterogeneity_summary_panel_inputs_v1",
            "interaction_effect_summary_panel_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="model_explanation",
        display_name="Model Explanation",
        template_ids=_template_ids_for_evidence_class("model_explanation"),
        input_schema_ids=(
            "shap_summary_inputs_v1",
            "shap_bar_importance_inputs_v1",
            "shap_signed_importance_panel_inputs_v1",
            "shap_multicohort_importance_panel_inputs_v1",
            "shap_dependence_panel_inputs_v1",
            "shap_waterfall_local_explanation_panel_inputs_v1",
            "shap_force_like_summary_panel_inputs_v1",
            "shap_grouped_local_explanation_panel_inputs_v1",
            "shap_grouped_decision_path_panel_inputs_v1",
            "shap_multigroup_decision_path_panel_inputs_v1",
            "shap_grouped_local_support_domain_panel_inputs_v1",
            "shap_multigroup_decision_path_support_domain_panel_inputs_v1",
            "shap_signed_importance_local_support_domain_panel_inputs_v1",
            "partial_dependence_ice_panel_inputs_v1",
            "partial_dependence_interaction_contour_panel_inputs_v1",
            "partial_dependence_interaction_slice_panel_inputs_v1",
            "partial_dependence_subgroup_comparison_panel_inputs_v1",
            "accumulated_local_effects_panel_inputs_v1",
            "feature_response_support_domain_panel_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="model_audit",
        display_name="Model Audit",
        template_ids=_template_ids_for_evidence_class("model_audit"),
        input_schema_ids=("model_complexity_audit_panel_inputs_v1",),
    ),
    DisplaySchemaClass(
        class_id="generalizability",
        display_name="Generalizability",
        template_ids=_template_ids_for_evidence_class("generalizability"),
        input_schema_ids=(
            "multicenter_generalizability_inputs_v1",
            "generalizability_subgroup_composite_inputs_v1",
            "center_transportability_governance_summary_panel_inputs_v1",
        ),
    ),
    DisplaySchemaClass(
        class_id="publication_shells_and_tables",
        display_name="Publication Shells and Tables",
        template_ids=tuple(
            [
                item.template_id
                for item in display_registry.list_evidence_figure_specs()
                if item.evidence_class == "publication_shells_and_tables"
            ]
            + [item.shell_id for item in display_registry.list_illustration_shell_specs()]
            + [item.shell_id for item in display_registry.list_table_shell_specs()]
        ),
        input_schema_ids=(
            "accepted_descriptive_display_data_v1",
            "cohort_flow_shell_inputs_v1",
            "submission_graphical_abstract_inputs_v1",
            "workflow_fact_sheet_panel_inputs_v1",
            "design_evidence_composite_shell_inputs_v1",
            "baseline_missingness_qc_panel_inputs_v1",
            "center_coverage_batch_transportability_panel_inputs_v1",
            "transportability_recalibration_governance_panel_inputs_v1",
            "baseline_characteristics_schema_v1",
            "time_to_event_performance_summary_v1",
            "clinical_interpretation_summary_v1",
            "performance_summary_table_generic_v1",
            "grouped_risk_event_summary_table_v1",
        ),
    ),
)
