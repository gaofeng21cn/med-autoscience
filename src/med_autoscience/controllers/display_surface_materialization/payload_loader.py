from __future__ import annotations

from collections.abc import Callable

from .shared import Any, Path, _evidence_payload_path, display_registry, load_json
from .validation_atlas_primary import _validate_celltype_signature_heatmap_display_payload, _validate_embedding_display_payload
from .validation_curves_extended import _validate_model_complexity_audit_display_payload, _validate_time_to_event_discrimination_calibration_display_payload, _validate_time_to_event_display_payload, _validate_time_to_event_landmark_performance_display_payload, _validate_time_to_event_multihorizon_calibration_display_payload, _validate_time_to_event_stratified_cumulative_incidence_display_payload, _validate_time_to_event_threshold_governance_display_payload
from .validation_curves_primary import _validate_binary_calibration_decision_curve_display_payload, _validate_binary_curve_display_payload, _validate_risk_layering_display_payload, _validate_time_dependent_roc_comparison_display_payload, _validate_time_to_event_decision_curve_display_payload
from .validation_effects import _validate_broader_heterogeneity_summary_panel_display_payload, _validate_coefficient_path_panel_display_payload, _validate_compact_effect_estimate_panel_display_payload, _validate_forest_display_payload, _validate_interaction_effect_summary_panel_display_payload
from .validation_generalizability import _validate_generalizability_subgroup_composite_display_payload
from .validation_omics_genomic import _validate_genomic_alteration_consequence_panel_display_payload, _validate_genomic_alteration_landscape_panel_display_payload, _validate_genomic_alteration_multiomic_consequence_panel_display_payload, _validate_genomic_alteration_pathway_integrated_composite_panel_display_payload, _validate_genomic_program_governance_summary_panel_display_payload, _validate_omics_volcano_panel_display_payload
from .validation_omics_heatmaps import _validate_clustered_heatmap_display_payload, _validate_confusion_matrix_heatmap_binary_display_payload, _validate_gsva_ssgsea_heatmap_display_payload, _validate_heatmap_display_payload, _validate_performance_heatmap_display_payload
from .validation_omics_panels import _validate_celltype_marker_dotplot_panel_display_payload, _validate_cnv_recurrence_summary_panel_display_payload, _validate_oncoplot_mutation_landscape_panel_display_payload, _validate_pathway_enrichment_dotplot_panel_display_payload
from .validation_shap_importance import _validate_shap_bar_importance_display_payload, _validate_shap_multicohort_importance_panel_display_payload
from .validation_shap_summary import _validate_shap_dependence_panel_display_payload, _validate_shap_force_like_summary_panel_display_payload, _validate_shap_summary_display_payload, _validate_shap_waterfall_local_explanation_panel_display_payload

_EvidenceDisplayValidator = Callable[..., dict[str, Any]]

_VALIDATOR_BY_SCHEMA_ID: dict[str, _EvidenceDisplayValidator] = {
    "binary_prediction_curve_inputs_v1": _validate_binary_curve_display_payload,
    "time_dependent_roc_comparison_inputs_v1": _validate_time_dependent_roc_comparison_display_payload,
    "risk_layering_monotonic_inputs_v1": _validate_risk_layering_display_payload,
    "binary_calibration_decision_curve_panel_inputs_v1": _validate_binary_calibration_decision_curve_display_payload,
    "model_complexity_audit_panel_inputs_v1": _validate_model_complexity_audit_display_payload,
    "time_to_event_landmark_performance_inputs_v1": _validate_time_to_event_landmark_performance_display_payload,
    "time_to_event_threshold_governance_inputs_v1": _validate_time_to_event_threshold_governance_display_payload,
    "time_to_event_multihorizon_calibration_inputs_v1": _validate_time_to_event_multihorizon_calibration_display_payload,
    "time_to_event_grouped_inputs_v1": _validate_time_to_event_display_payload,
    "time_to_event_stratified_cumulative_incidence_inputs_v1": _validate_time_to_event_stratified_cumulative_incidence_display_payload,
    "time_to_event_discrimination_calibration_inputs_v1": _validate_time_to_event_discrimination_calibration_display_payload,
    "time_to_event_decision_curve_inputs_v1": _validate_time_to_event_decision_curve_display_payload,
    "embedding_grouped_inputs_v1": _validate_embedding_display_payload,
    "celltype_signature_heatmap_inputs_v1": _validate_celltype_signature_heatmap_display_payload,
    "heatmap_group_comparison_inputs_v1": _validate_heatmap_display_payload,
    "correlation_heatmap_inputs_v1": _validate_heatmap_display_payload,
    "performance_heatmap_inputs_v1": _validate_performance_heatmap_display_payload,
    "confusion_matrix_heatmap_binary_inputs_v1": _validate_confusion_matrix_heatmap_binary_display_payload,
    "clustered_heatmap_inputs_v1": _validate_clustered_heatmap_display_payload,
    "gsva_ssgsea_heatmap_inputs_v1": _validate_gsva_ssgsea_heatmap_display_payload,
    "pathway_enrichment_dotplot_panel_inputs_v1": _validate_pathway_enrichment_dotplot_panel_display_payload,
    "celltype_marker_dotplot_panel_inputs_v1": _validate_celltype_marker_dotplot_panel_display_payload,
    "oncoplot_mutation_landscape_panel_inputs_v1": _validate_oncoplot_mutation_landscape_panel_display_payload,
    "cnv_recurrence_summary_panel_inputs_v1": _validate_cnv_recurrence_summary_panel_display_payload,
    "genomic_alteration_landscape_panel_inputs_v1": _validate_genomic_alteration_landscape_panel_display_payload,
    "genomic_alteration_consequence_panel_inputs_v1": _validate_genomic_alteration_consequence_panel_display_payload,
    "genomic_alteration_multiomic_consequence_panel_inputs_v1": _validate_genomic_alteration_multiomic_consequence_panel_display_payload,
    "genomic_alteration_pathway_integrated_composite_panel_inputs_v1": _validate_genomic_alteration_pathway_integrated_composite_panel_display_payload,
    "genomic_program_governance_summary_panel_inputs_v1": _validate_genomic_program_governance_summary_panel_display_payload,
    "omics_volcano_panel_inputs_v1": _validate_omics_volcano_panel_display_payload,
    "forest_effect_inputs_v1": _validate_forest_display_payload,
    "compact_effect_estimate_panel_inputs_v1": _validate_compact_effect_estimate_panel_display_payload,
    "coefficient_path_panel_inputs_v1": _validate_coefficient_path_panel_display_payload,
    "broader_heterogeneity_summary_panel_inputs_v1": _validate_broader_heterogeneity_summary_panel_display_payload,
    "interaction_effect_summary_panel_inputs_v1": _validate_interaction_effect_summary_panel_display_payload,
    "shap_summary_inputs_v1": _validate_shap_summary_display_payload,
    "shap_dependence_panel_inputs_v1": _validate_shap_dependence_panel_display_payload,
    "shap_waterfall_local_explanation_panel_inputs_v1": _validate_shap_waterfall_local_explanation_panel_display_payload,
    "shap_force_like_summary_panel_inputs_v1": _validate_shap_force_like_summary_panel_display_payload,
    "shap_bar_importance_inputs_v1": _validate_shap_bar_importance_display_payload,
    "shap_multicohort_importance_panel_inputs_v1": _validate_shap_multicohort_importance_panel_display_payload,
    "generalizability_subgroup_composite_inputs_v1": _validate_generalizability_subgroup_composite_display_payload,
}


def _build_validator_registry() -> dict[tuple[str, str], _EvidenceDisplayValidator]:
    registry: dict[tuple[str, str], _EvidenceDisplayValidator] = {}
    current_schema_ids = {
        spec.input_schema_id
        for spec in display_registry.list_evidence_figure_specs()
    }
    extra_schema_ids = sorted(set(_VALIDATOR_BY_SCHEMA_ID) - current_schema_ids)
    if extra_schema_ids:
        raise RuntimeError(
            "retired evidence input schemas must not be registered in current materialization: "
            + ", ".join(extra_schema_ids)
        )
    for spec in display_registry.list_evidence_figure_specs():
        validator = _VALIDATOR_BY_SCHEMA_ID.get(spec.input_schema_id)
        if validator is None:
            continue
        key = (spec.input_schema_id, spec.evidence_class)
        existing = registry.get(key)
        if existing is not None and existing is not validator:
            raise RuntimeError(
                f"display validator registry conflict for schema `{spec.input_schema_id}` "
                f"and display family `{spec.evidence_class}`"
            )
        registry[key] = validator
    return registry


_VALIDATOR_BY_SCHEMA_AND_DISPLAY_FAMILY = _build_validator_registry()


def _validate_evidence_display_payload(
    *,
    payload_path: Path,
    payload: dict[str, Any],
    spec: display_registry.EvidenceFigureSpec,
    display_id: str,
) -> dict[str, Any]:
    registry_key = (spec.input_schema_id, spec.evidence_class)
    try:
        validator = _VALIDATOR_BY_SCHEMA_AND_DISPLAY_FAMILY[registry_key]
    except KeyError as exc:
        raise ValueError(
            f"unsupported evidence input schema `{spec.input_schema_id}` "
            f"for display family `{spec.evidence_class}`"
        ) from exc
    return validator(
        path=payload_path,
        payload=payload,
        expected_template_id=spec.template_id,
        expected_display_id=display_id,
    )


def _load_evidence_display_payload(
    *,
    paper_root: Path,
    spec: display_registry.EvidenceFigureSpec,
    display_id: str,
) -> tuple[Path, dict[str, Any]]:
    payload_path = _evidence_payload_path(paper_root=paper_root, input_schema_id=spec.input_schema_id)
    payload = load_json(payload_path)
    if str(payload.get("input_schema_id") or "").strip() != spec.input_schema_id:
        raise ValueError(f"{payload_path.name} must declare input_schema_id `{spec.input_schema_id}`")
    displays = payload.get("displays")
    if not isinstance(displays, list) or not displays:
        raise ValueError(f"{payload_path.name} must contain a non-empty displays list")
    matched_display: dict[str, Any] | None = None
    for index, item in enumerate(displays):
        if not isinstance(item, dict):
            raise ValueError(f"{payload_path.name} displays[{index}] must be an object")
        if str(item.get("display_id") or "").strip() == display_id:
            matched_display = item
            break
    if matched_display is None:
        raise ValueError(f"{payload_path.name} does not define display `{display_id}` for template `{spec.template_id}`")

    return payload_path, _validate_evidence_display_payload(
        payload_path=payload_path,
        payload=matched_display,
        spec=spec,
        display_id=display_id,
    )


__all__ = [
    "_load_evidence_display_payload",
]
