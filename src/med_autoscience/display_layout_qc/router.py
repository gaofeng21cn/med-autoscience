from __future__ import annotations

from med_autoscience import display_readability_qc

from .shared import ENGINE_ID, _normalize_layout_sidecar, _utc_now
from .atlas_primary import _check_publication_atlas_spatial_bridge_panel, _check_publication_celltype_signature_panel, _check_publication_embedding_scatter, _check_publication_single_cell_atlas_overview_panel, _check_publication_spatial_niche_map_panel, _check_publication_trajectory_progression_panel
from .atlas_storyboards import _check_publication_atlas_spatial_trajectory_context_support_panel, _check_publication_atlas_spatial_trajectory_density_coverage_panel, _check_publication_atlas_spatial_trajectory_multimanifold_context_support_panel, _check_publication_atlas_spatial_trajectory_storyboard_panel
from .curves_extended import _check_publication_landmark_performance_panel, _check_publication_model_complexity_audit, _check_publication_time_to_event_multihorizon_calibration_panel, _check_publication_time_to_event_threshold_governance_panel
from .curves_primary import _check_publication_binary_calibration_decision_curve, _check_publication_decision_curve, _check_publication_evidence_curve, _check_publication_risk_layering_bars, _check_publication_survival_curve
from .effects_panels import _check_publication_broader_heterogeneity_summary_panel, _check_publication_center_transportability_governance_summary_panel, _check_publication_coefficient_path_panel, _check_publication_compact_effect_estimate_panel, _check_publication_forest_plot, _check_publication_generalizability_subgroup_composite_panel, _check_publication_interaction_effect_summary_panel, _check_publication_multicenter_overview
from .illustration_panels import _check_publication_baseline_missingness_qc_panel, _check_publication_center_coverage_batch_transportability_panel, _check_publication_design_evidence_composite_shell, _check_publication_illustration_flow, _check_publication_transportability_recalibration_governance_panel, _check_publication_workflow_fact_sheet_panel, _check_submission_graphical_abstract
from .omics_panels import _check_publication_celltype_marker_dotplot_panel, _check_publication_cnv_recurrence_summary_panel, _check_publication_genomic_alteration_consequence_panel, _check_publication_genomic_alteration_landscape_panel, _check_publication_genomic_alteration_multiomic_consequence_panel, _check_publication_genomic_alteration_pathway_integrated_composite_panel, _check_publication_genomic_program_governance_summary_panel, _check_publication_heatmap, _check_publication_omics_volcano_panel, _check_publication_oncoplot_mutation_landscape_panel, _check_publication_pathway_enrichment_dotplot_panel
from .response_panels import _check_publication_accumulated_local_effects_panel, _check_publication_partial_dependence_ice_panel, _check_publication_partial_dependence_interaction_contour_panel, _check_publication_partial_dependence_interaction_slice_panel, _check_publication_partial_dependence_subgroup_comparison_panel
from .shap_path_panels import _check_publication_shap_grouped_decision_path_panel, _check_publication_shap_grouped_local_explanation_panel, _check_publication_shap_multigroup_decision_path_panel
from .shap_summary_panels import _check_publication_shap_bar_importance, _check_publication_shap_dependence_panel, _check_publication_shap_force_like_summary_panel, _check_publication_shap_multicohort_importance_panel, _check_publication_shap_signed_importance_panel, _check_publication_shap_summary, _check_publication_shap_waterfall_local_explanation_panel
from .support_domain_panels import _check_publication_feature_response_support_domain_panel, _check_publication_shap_grouped_local_support_domain_panel, _check_publication_shap_multigroup_decision_path_support_domain_panel, _check_publication_shap_signed_importance_local_support_domain_panel

def run_display_layout_qc(*, qc_profile: str, layout_sidecar: dict[str, object]) -> dict[str, object]:
    normalized_sidecar = _normalize_layout_sidecar(layout_sidecar)
    normalized_profile = str(qc_profile or "").strip()
    if normalized_profile == "publication_illustration_flow":
        layout_issues = _check_publication_illustration_flow(normalized_sidecar)
    elif normalized_profile == "publication_risk_layering_bars":
        layout_issues = _check_publication_risk_layering_bars(normalized_sidecar)
    elif normalized_profile == "publication_evidence_curve":
        layout_issues = _check_publication_evidence_curve(normalized_sidecar)
    elif normalized_profile == "publication_binary_calibration_decision_curve":
        layout_issues = _check_publication_binary_calibration_decision_curve(normalized_sidecar)
    elif normalized_profile == "publication_decision_curve":
        layout_issues = _check_publication_decision_curve(normalized_sidecar)
    elif normalized_profile == "publication_survival_curve":
        layout_issues = _check_publication_survival_curve(normalized_sidecar)
    elif normalized_profile == "publication_embedding_scatter":
        layout_issues = _check_publication_embedding_scatter(normalized_sidecar)
    elif normalized_profile == "publication_celltype_signature_panel":
        layout_issues = _check_publication_celltype_signature_panel(normalized_sidecar)
    elif normalized_profile == "publication_single_cell_atlas_overview_panel":
        layout_issues = _check_publication_single_cell_atlas_overview_panel(normalized_sidecar)
    elif normalized_profile == "publication_atlas_spatial_bridge_panel":
        layout_issues = _check_publication_atlas_spatial_bridge_panel(normalized_sidecar)
    elif normalized_profile == "publication_spatial_niche_map_panel":
        layout_issues = _check_publication_spatial_niche_map_panel(normalized_sidecar)
    elif normalized_profile == "publication_trajectory_progression_panel":
        layout_issues = _check_publication_trajectory_progression_panel(normalized_sidecar)
    elif normalized_profile == "publication_atlas_spatial_trajectory_storyboard_panel":
        layout_issues = _check_publication_atlas_spatial_trajectory_storyboard_panel(normalized_sidecar)
    elif normalized_profile == "publication_atlas_spatial_trajectory_density_coverage_panel":
        layout_issues = _check_publication_atlas_spatial_trajectory_density_coverage_panel(normalized_sidecar)
    elif normalized_profile == "publication_atlas_spatial_trajectory_context_support_panel":
        layout_issues = _check_publication_atlas_spatial_trajectory_context_support_panel(normalized_sidecar)
    elif normalized_profile == "publication_atlas_spatial_trajectory_multimanifold_context_support_panel":
        layout_issues = _check_publication_atlas_spatial_trajectory_multimanifold_context_support_panel(
            normalized_sidecar
        )
    elif normalized_profile == "publication_heatmap":
        layout_issues = _check_publication_heatmap(normalized_sidecar)
    elif normalized_profile == "publication_pathway_enrichment_dotplot_panel":
        layout_issues = _check_publication_pathway_enrichment_dotplot_panel(normalized_sidecar)
    elif normalized_profile == "publication_celltype_marker_dotplot_panel":
        layout_issues = _check_publication_celltype_marker_dotplot_panel(normalized_sidecar)
    elif normalized_profile == "publication_oncoplot_mutation_landscape_panel":
        layout_issues = _check_publication_oncoplot_mutation_landscape_panel(normalized_sidecar)
    elif normalized_profile == "publication_cnv_recurrence_summary_panel":
        layout_issues = _check_publication_cnv_recurrence_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_alteration_landscape_panel":
        layout_issues = _check_publication_genomic_alteration_landscape_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_alteration_consequence_panel":
        layout_issues = _check_publication_genomic_alteration_consequence_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_alteration_multiomic_consequence_panel":
        layout_issues = _check_publication_genomic_alteration_multiomic_consequence_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_alteration_pathway_integrated_composite_panel":
        layout_issues = _check_publication_genomic_alteration_pathway_integrated_composite_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_program_governance_summary_panel":
        layout_issues = _check_publication_genomic_program_governance_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_omics_volcano_panel":
        layout_issues = _check_publication_omics_volcano_panel(normalized_sidecar)
    elif normalized_profile == "publication_forest_plot":
        layout_issues = _check_publication_forest_plot(normalized_sidecar)
    elif normalized_profile == "publication_compact_effect_estimate_panel":
        layout_issues = _check_publication_compact_effect_estimate_panel(normalized_sidecar)
    elif normalized_profile == "publication_coefficient_path_panel":
        layout_issues = _check_publication_coefficient_path_panel(normalized_sidecar)
    elif normalized_profile == "publication_broader_heterogeneity_summary_panel":
        layout_issues = _check_publication_broader_heterogeneity_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_interaction_effect_summary_panel":
        layout_issues = _check_publication_interaction_effect_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_center_transportability_governance_summary_panel":
        layout_issues = _check_publication_center_transportability_governance_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_model_complexity_audit":
        layout_issues = _check_publication_model_complexity_audit(normalized_sidecar)
    elif normalized_profile == "publication_landmark_performance_panel":
        layout_issues = _check_publication_landmark_performance_panel(normalized_sidecar)
    elif normalized_profile == "publication_time_to_event_threshold_governance_panel":
        layout_issues = _check_publication_time_to_event_threshold_governance_panel(normalized_sidecar)
    elif normalized_profile == "publication_time_to_event_multihorizon_calibration_panel":
        layout_issues = _check_publication_time_to_event_multihorizon_calibration_panel(normalized_sidecar)
    elif normalized_profile == "publication_multicenter_overview":
        layout_issues = _check_publication_multicenter_overview(normalized_sidecar)
    elif normalized_profile == "publication_generalizability_subgroup_composite_panel":
        layout_issues = _check_publication_generalizability_subgroup_composite_panel(normalized_sidecar)
    elif normalized_profile == "submission_graphical_abstract":
        layout_issues = _check_submission_graphical_abstract(normalized_sidecar)
    elif normalized_profile == "publication_workflow_fact_sheet_panel":
        layout_issues = _check_publication_workflow_fact_sheet_panel(normalized_sidecar)
    elif normalized_profile == "publication_design_evidence_composite_shell":
        layout_issues = _check_publication_design_evidence_composite_shell(normalized_sidecar)
    elif normalized_profile == "publication_baseline_missingness_qc_panel":
        layout_issues = _check_publication_baseline_missingness_qc_panel(normalized_sidecar)
    elif normalized_profile == "publication_center_coverage_batch_transportability_panel":
        layout_issues = _check_publication_center_coverage_batch_transportability_panel(normalized_sidecar)
    elif normalized_profile == "publication_transportability_recalibration_governance_panel":
        layout_issues = _check_publication_transportability_recalibration_governance_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_summary":
        layout_issues = _check_publication_shap_summary(normalized_sidecar)
    elif normalized_profile == "publication_shap_bar_importance":
        layout_issues = _check_publication_shap_bar_importance(normalized_sidecar)
    elif normalized_profile == "publication_shap_signed_importance_panel":
        layout_issues = _check_publication_shap_signed_importance_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_multicohort_importance_panel":
        layout_issues = _check_publication_shap_multicohort_importance_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_dependence_panel":
        layout_issues = _check_publication_shap_dependence_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_waterfall_local_explanation_panel":
        layout_issues = _check_publication_shap_waterfall_local_explanation_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_force_like_summary_panel":
        layout_issues = _check_publication_shap_force_like_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_grouped_local_explanation_panel":
        layout_issues = _check_publication_shap_grouped_local_explanation_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_grouped_decision_path_panel":
        layout_issues = _check_publication_shap_grouped_decision_path_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_multigroup_decision_path_panel":
        layout_issues = _check_publication_shap_multigroup_decision_path_panel(normalized_sidecar)
    elif normalized_profile == "publication_partial_dependence_ice_panel":
        layout_issues = _check_publication_partial_dependence_ice_panel(normalized_sidecar)
    elif normalized_profile == "publication_partial_dependence_interaction_contour_panel":
        layout_issues = _check_publication_partial_dependence_interaction_contour_panel(normalized_sidecar)
    elif normalized_profile == "publication_partial_dependence_interaction_slice_panel":
        layout_issues = _check_publication_partial_dependence_interaction_slice_panel(normalized_sidecar)
    elif normalized_profile == "publication_partial_dependence_subgroup_comparison_panel":
        layout_issues = _check_publication_partial_dependence_subgroup_comparison_panel(normalized_sidecar)
    elif normalized_profile == "publication_accumulated_local_effects_panel":
        layout_issues = _check_publication_accumulated_local_effects_panel(normalized_sidecar)
    elif normalized_profile == "publication_feature_response_support_domain_panel":
        layout_issues = _check_publication_feature_response_support_domain_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_grouped_local_support_domain_panel":
        layout_issues = _check_publication_shap_grouped_local_support_domain_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_multigroup_decision_path_support_domain_panel":
        layout_issues = _check_publication_shap_multigroup_decision_path_support_domain_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_signed_importance_local_support_domain_panel":
        layout_issues = _check_publication_shap_signed_importance_local_support_domain_panel(normalized_sidecar)
    else:
        raise ValueError(f"unsupported qc_profile `{qc_profile}`")
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
