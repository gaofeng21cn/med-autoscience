from __future__ import annotations

import importlib
from functools import lru_cache
from types import SimpleNamespace

_INPUT_SCHEMAS = {
    "binary": "binary_prediction_curve_inputs_v1",
    "risk_layering": "risk_layering_monotonic_inputs_v1",
    "time_to_event_multihorizon": "time_to_event_multihorizon_calibration_inputs_v1",
    "time_to_event_grouped": "time_to_event_grouped_inputs_v1",
    "time_to_event_decision": "time_to_event_decision_curve_inputs_v1",
    "model_complexity_audit": "model_complexity_audit_panel_inputs_v1",
    "dimensionality_reduction": "dimensionality_reduction_inputs_v1",
    "omics_volcano": "omics_volcano_panel_inputs_v1",
    "heatmap": "heatmap_group_comparison_inputs_v1",
    "confusion_heatmap": "confusion_matrix_heatmap_binary_inputs_v1",
    "enrichment_dotplot": "pathway_enrichment_dotplot_panel_inputs_v1",
    "celltype_marker_dotplot": "celltype_marker_dotplot_panel_inputs_v1",
    "cnv_recurrence": "cnv_recurrence_summary_panel_inputs_v1",
    "genomic_alteration_landscape": "genomic_alteration_landscape_panel_inputs_v1",
    "genomic_alteration_consequence": "genomic_alteration_consequence_panel_inputs_v1",
    "forest": "forest_effect_inputs_v1",
    "generalizability_subgroup": "generalizability_subgroup_composite_inputs_v1",
    "coefficient_path": "coefficient_path_panel_inputs_v1",
    "shap": "shap_summary_inputs_v1",
    "shap_dependence": "shap_dependence_panel_inputs_v1",
    "shap_waterfall": "shap_waterfall_local_explanation_panel_inputs_v1",
    "cohort_flow": "cohort_flow_shell_inputs_v1",
    "submission_graphical_abstract": "submission_graphical_abstract_inputs_v1",
    "baseline_table": "baseline_characteristics_schema_v1",
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
    contracts = {name: module.get_input_schema_contract(schema_id) for name, schema_id in _INPUT_SCHEMAS.items()}
    classes = {name: _display_class_by_id(module, class_id) for name, class_id in _CLASS_IDS.items()}
    return SimpleNamespace(module=module, **contracts, **classes)
