from __future__ import annotations

from med_autoscience import display_readability_qc

from .shared import ENGINE_ID, LayoutSidecar, _all_boxes, _check_boxes_within_device, _check_pairwise_non_overlap, _normalize_layout_sidecar, _utc_now
from .atlas_primary import _check_publication_celltype_signature_panel, _check_publication_embedding_scatter
from .curves_extended import _check_publication_landmark_performance_panel, _check_publication_model_complexity_audit, _check_publication_time_to_event_multihorizon_calibration_panel, _check_publication_time_to_event_threshold_governance_panel
from .curves_primary import _check_publication_binary_calibration_decision_curve, _check_publication_decision_curve, _check_publication_evidence_curve, _check_publication_risk_layering_bars, _check_publication_survival_curve
from .effects_panels import _check_publication_broader_heterogeneity_summary_panel, _check_publication_coefficient_path_panel, _check_publication_compact_effect_estimate_panel, _check_publication_forest_plot, _check_publication_generalizability_subgroup_composite_panel, _check_publication_interaction_effect_summary_panel
from .illustration_panels import _check_publication_design_evidence_composite_shell, _check_publication_illustration_flow, _check_publication_workflow_fact_sheet_panel, _check_submission_graphical_abstract
from .omics_panels import _check_publication_celltype_marker_dotplot_panel, _check_publication_cnv_recurrence_summary_panel, _check_publication_genomic_alteration_consequence_panel, _check_publication_genomic_alteration_landscape_panel, _check_publication_genomic_alteration_multiomic_consequence_panel, _check_publication_genomic_alteration_pathway_integrated_composite_panel, _check_publication_genomic_program_governance_summary_panel, _check_publication_heatmap, _check_publication_omics_volcano_panel, _check_publication_oncoplot_mutation_landscape_panel, _check_publication_pathway_enrichment_dotplot_panel
from .shap_summary_panels import _check_publication_shap_bar_importance, _check_publication_shap_dependence_panel, _check_publication_shap_force_like_summary_panel, _check_publication_shap_multicohort_importance_panel, _check_publication_shap_summary, _check_publication_shap_waterfall_local_explanation_panel


def _check_publication_result_display(sidecar: LayoutSidecar) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    issues.extend(_check_boxes_within_device(sidecar))
    text_boxes = tuple(
        box
        for box in _all_boxes(sidecar)
        if box.box_type in {"title", "subtitle", "axis_title", "x_axis_title", "y_axis_title", "label", "annotation"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    return issues


def _check_publication_table_shell(sidecar: LayoutSidecar) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    issues.extend(_check_boxes_within_device(sidecar))
    text_boxes = tuple(
        box
        for box in _all_boxes(sidecar)
        if box.box_type in {"title", "subtitle", "table_title", "table_note", "caption", "text"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    return issues


QC_PROFILE_RUNNERS = {
    "publication_illustration_flow": _check_publication_illustration_flow,
    "publication_risk_layering_bars": _check_publication_risk_layering_bars,
    "publication_evidence_curve": _check_publication_evidence_curve,
    "publication_binary_calibration_decision_curve": _check_publication_binary_calibration_decision_curve,
    "publication_decision_curve": _check_publication_decision_curve,
    "publication_survival_curve": _check_publication_survival_curve,
    "publication_embedding_scatter": _check_publication_embedding_scatter,
    "publication_celltype_signature_panel": _check_publication_celltype_signature_panel,
    "publication_heatmap": _check_publication_heatmap,
    "publication_pathway_enrichment_dotplot_panel": _check_publication_pathway_enrichment_dotplot_panel,
    "publication_celltype_marker_dotplot_panel": _check_publication_celltype_marker_dotplot_panel,
    "publication_oncoplot_mutation_landscape_panel": _check_publication_oncoplot_mutation_landscape_panel,
    "publication_cnv_recurrence_summary_panel": _check_publication_cnv_recurrence_summary_panel,
    "publication_genomic_alteration_landscape_panel": _check_publication_genomic_alteration_landscape_panel,
    "publication_genomic_alteration_consequence_panel": _check_publication_genomic_alteration_consequence_panel,
    "publication_genomic_alteration_multiomic_consequence_panel": _check_publication_genomic_alteration_multiomic_consequence_panel,
    "publication_genomic_alteration_pathway_integrated_composite_panel": _check_publication_genomic_alteration_pathway_integrated_composite_panel,
    "publication_genomic_program_governance_summary_panel": _check_publication_genomic_program_governance_summary_panel,
    "publication_omics_volcano_panel": _check_publication_omics_volcano_panel,
    "publication_forest_plot": _check_publication_forest_plot,
    "publication_compact_effect_estimate_panel": _check_publication_compact_effect_estimate_panel,
    "publication_coefficient_path_panel": _check_publication_coefficient_path_panel,
    "publication_broader_heterogeneity_summary_panel": _check_publication_broader_heterogeneity_summary_panel,
    "publication_interaction_effect_summary_panel": _check_publication_interaction_effect_summary_panel,
    "publication_model_complexity_audit": _check_publication_model_complexity_audit,
    "publication_landmark_performance_panel": _check_publication_landmark_performance_panel,
    "publication_time_to_event_threshold_governance_panel": _check_publication_time_to_event_threshold_governance_panel,
    "publication_time_to_event_multihorizon_calibration_panel": _check_publication_time_to_event_multihorizon_calibration_panel,
    "publication_generalizability_subgroup_composite_panel": _check_publication_generalizability_subgroup_composite_panel,
    "submission_graphical_abstract": _check_submission_graphical_abstract,
    "publication_workflow_fact_sheet_panel": _check_publication_workflow_fact_sheet_panel,
    "publication_design_evidence_composite_shell": _check_publication_design_evidence_composite_shell,
    "publication_shap_summary": _check_publication_shap_summary,
    "publication_shap_bar_importance": _check_publication_shap_bar_importance,
    "publication_shap_multicohort_importance_panel": _check_publication_shap_multicohort_importance_panel,
    "publication_shap_dependence_panel": _check_publication_shap_dependence_panel,
    "publication_shap_waterfall_local_explanation_panel": _check_publication_shap_waterfall_local_explanation_panel,
    "publication_shap_force_like_summary_panel": _check_publication_shap_force_like_summary_panel,
    "publication_result_display": _check_publication_result_display,
    "publication_table_shell": _check_publication_table_shell,
    "publication_table_baseline": _check_publication_table_shell,
    "publication_table_interpretation": _check_publication_table_shell,
    "publication_table_performance": _check_publication_table_shell,
}


def run_display_layout_qc(*, qc_profile: str, layout_sidecar: dict[str, object]) -> dict[str, object]:
    normalized_sidecar = _normalize_layout_sidecar(layout_sidecar)
    normalized_profile = str(qc_profile or "").strip()
    try:
        layout_checker = QC_PROFILE_RUNNERS[normalized_profile]
    except KeyError as exc:
        raise ValueError(f"unsupported qc_profile `{qc_profile}`") from exc
    layout_issues = layout_checker(normalized_sidecar)
    readability_issues = display_readability_qc.run_readability_qc(
        qc_profile=normalized_profile,
        layout_sidecar=layout_sidecar,
    )
    issues = layout_issues + readability_issues
    audit_classes = sorted(
        {
            str(issue.get("audit_class") or "layout").strip()
            for issue in issues
            if str(issue.get("audit_class") or "layout").strip()
        }
    )
    readability_findings = [issue for issue in issues if str(issue.get("audit_class") or "").strip() == "readability"]
    failure_reason = str(issues[0].get("rule_id") or "").strip() if issues else ""

    return {
        "status": "fail" if issues else "pass",
        "checked_at": _utc_now(),
        "engine_id": ENGINE_ID,
        "qc_profile": normalized_profile,
        "issues": issues,
        "audit_classes": audit_classes,
        "failure_reason": failure_reason,
        "readability_findings": readability_findings,
        "revision_note": "",
        "metrics": normalized_sidecar.metrics,
    }
