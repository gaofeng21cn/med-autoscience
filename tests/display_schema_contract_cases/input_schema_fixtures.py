from __future__ import annotations

import importlib
from functools import lru_cache
from types import SimpleNamespace

_INPUT_SCHEMAS = {
    "binary": "binary_prediction_curve_inputs_v1",
    "embedding": "embedding_grouped_inputs_v1",
    "celltype_signature": "celltype_signature_heatmap_inputs_v1",
    "atlas_overview": "single_cell_atlas_overview_inputs_v1",
    "atlas_spatial_bridge": "atlas_spatial_bridge_panel_inputs_v1",
    "spatial_niche_map": "spatial_niche_map_inputs_v1",
    "trajectory_progression": "trajectory_progression_inputs_v1",
    "density_coverage": "atlas_spatial_trajectory_density_coverage_panel_inputs_v1",
    "context_support": "atlas_spatial_trajectory_context_support_panel_inputs_v1",
    "multimanifold_context_support": "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1",
    "performance_heatmap": "performance_heatmap_inputs_v1",
    "confusion_heatmap": "confusion_matrix_heatmap_binary_inputs_v1",
    "clustered_heatmap": "clustered_heatmap_inputs_v1",
    "gsva_heatmap": "gsva_ssgsea_heatmap_inputs_v1",
    "enrichment_dotplot": "pathway_enrichment_dotplot_panel_inputs_v1",
    "celltype_marker_dotplot": "celltype_marker_dotplot_panel_inputs_v1",
    "omics_volcano": "omics_volcano_panel_inputs_v1",
    "oncoplot_landscape": "oncoplot_mutation_landscape_panel_inputs_v1",
    "cnv_recurrence": "cnv_recurrence_summary_panel_inputs_v1",
    "genomic_alteration_landscape": "genomic_alteration_landscape_panel_inputs_v1",
    "genomic_alteration_consequence": "genomic_alteration_consequence_panel_inputs_v1",
    "genomic_alteration_multiomic_consequence": "genomic_alteration_multiomic_consequence_panel_inputs_v1",
    "genomic_alteration_pathway_integrated": "genomic_alteration_pathway_integrated_composite_panel_inputs_v1",
    "genomic_program_governance_summary": "genomic_program_governance_summary_panel_inputs_v1",
    "landmark_performance": "time_to_event_landmark_performance_inputs_v1",
    "correlation": "correlation_heatmap_inputs_v1",
    "forest": "forest_effect_inputs_v1",
    "generalizability_subgroup": "generalizability_subgroup_composite_inputs_v1",
    "compact_effect_estimate": "compact_effect_estimate_panel_inputs_v1",
    "coefficient_path": "coefficient_path_panel_inputs_v1",
    "shap": "shap_summary_inputs_v1",
    "shap_dependence": "shap_dependence_panel_inputs_v1",
    "shap_waterfall": "shap_waterfall_local_explanation_panel_inputs_v1",
    "cohort_flow": "cohort_flow_shell_inputs_v1",
    "time_to_event_panel": "time_to_event_discrimination_calibration_inputs_v1",
    "time_to_event_decision": "time_to_event_decision_curve_inputs_v1",
    "time_dependent_roc_comparison": "time_dependent_roc_comparison_inputs_v1",
    "time_to_event_stratified": "time_to_event_stratified_cumulative_incidence_inputs_v1",
    "generalizability": "multicenter_generalizability_inputs_v1",
    "risk_layering": "risk_layering_monotonic_inputs_v1",
    "binary_calibration_decision": "binary_calibration_decision_curve_panel_inputs_v1",
    "model_complexity_audit": "model_complexity_audit_panel_inputs_v1",
    "performance_table": "time_to_event_performance_summary_v1",
    "interpretation_table": "clinical_interpretation_summary_v1",
    "generic_performance_table": "performance_summary_table_generic_v1",
    "grouped_risk_table": "grouped_risk_event_summary_table_v1",
    "submission_graphical_abstract": "submission_graphical_abstract_inputs_v1",
    "workflow_fact_sheet": "workflow_fact_sheet_panel_inputs_v1",
    "design_evidence_composite": "design_evidence_composite_shell_inputs_v1",
    "baseline_missingness_qc": "baseline_missingness_qc_panel_inputs_v1",
    "center_coverage_batch_transportability": "center_coverage_batch_transportability_panel_inputs_v1",
    "transportability_recalibration_governance": "transportability_recalibration_governance_panel_inputs_v1",
}

_CLASS_IDS = {
    "time_to_event_class": "time_to_event",
    "model_explanation_class": "model_explanation",
    "clinical_utility_class": "clinical_utility",
    "model_audit_class": "model_audit",
    "generalizability_class": "generalizability",
    "effect_estimate_class": "effect_estimate",
    "publication_shells_class": "publication_shells_and_tables",
}


def _display_class_by_id(module, class_id: str):
    return next(item for item in module.list_display_schema_classes() if item.class_id == class_id)


@lru_cache(maxsize=1)
def _load_schema_contract_fixture() -> SimpleNamespace:
    module = importlib.import_module("med_autoscience.display_schema_contract")
    contracts = {
        name: module.get_input_schema_contract(schema_id)
        for name, schema_id in _INPUT_SCHEMAS.items()
    }
    classes = {
        name: _display_class_by_id(module, class_id)
        for name, class_id in _CLASS_IDS.items()
    }
    return SimpleNamespace(module=module, **contracts, **classes)
