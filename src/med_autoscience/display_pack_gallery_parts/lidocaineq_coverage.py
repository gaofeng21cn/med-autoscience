from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LidocaineQCoverageItem:
    reference_template_id: str
    title: str
    category_label: str
    mas_template_id: str
    expected_source_renderer: str
    required_mas_template_ids: tuple[str, ...] = ()
    mapping_relation: str = "direct_current_template"
    replacement_reason: str = "reference_template_id_matches_current_mas_template"
    do_not_restore_legacy_alias: bool = False


LIDOCAINEQ_COVERAGE_ITEMS: tuple[LidocaineQCoverageItem, ...] = (
    LidocaineQCoverageItem("survival_km", "Kaplan-Meier survival with risk table", "Survival / Kaplan-Meier", "kaplan_meier_grouped", "LidocaineQ/Figure_Template::survival_km", mapping_relation="renamed_current_template", replacement_reason="MAS current canonical template is grouped Kaplan-Meier evidence; keep PDF reference id as external source id."),
    LidocaineQCoverageItem("cumulative_incidence_grouped", "Cumulative incidence curve", "Survival / Kaplan-Meier", "cumulative_incidence_grouped", "LidocaineQ/Figure_Template::cumulative_incidence_grouped"),
    LidocaineQCoverageItem("roc_auc", "ROC curve with model comparison", "ROC / AUC", "roc_curve_binary", "LidocaineQ/Figure_Template::roc_auc", mapping_relation="renamed_current_template", replacement_reason="MAS current canonical template names the binary ROC curve surface; roc_auc remains a source renderer id."),
    LidocaineQCoverageItem("time_dependent_roc_horizon", "Time-dependent ROC horizon", "ROC / AUC", "time_dependent_roc_horizon", "LidocaineQ/Figure_Template::time_dependent_roc_horizon"),
    LidocaineQCoverageItem("calibration_curve_binary", "Calibration curve (binary outcome)", "ROC / AUC", "calibration_curve_binary", "LidocaineQ/Figure_Template::calibration_curve_binary"),
    LidocaineQCoverageItem("pr_curve_binary", "Precision-recall curve", "ROC / AUC", "pr_curve_binary", "LidocaineQ/Figure_Template::pr_curve_binary"),
    LidocaineQCoverageItem("decision_curve_binary", "Decision curve (binary outcome)", "ROC / AUC", "decision_curve_binary", "LidocaineQ/Figure_Template::decision_curve_binary"),
    LidocaineQCoverageItem("time_to_event_decision_curve", "Decision curve (time-to-event horizon)", "ROC / AUC", "time_to_event_decision_curve", "LidocaineQ/Figure_Template::time_to_event_decision_curve"),
    LidocaineQCoverageItem("time_to_event_multihorizon_calibration_panel", "Multi-horizon calibration panel", "ROC / AUC", "time_to_event_multihorizon_calibration_panel", "LidocaineQ/Figure_Template::time_to_event_multihorizon_calibration_panel"),
    LidocaineQCoverageItem("forest_cox", "Cox/effect forest plot", "Forest / Cox model", "forest_effect_main", "LidocaineQ/Figure_Template::forest_cox", mapping_relation="renamed_current_template", replacement_reason="MAS current canonical template generalizes Cox forest to effect forest while preserving the LidocaineQ source renderer."),
    LidocaineQCoverageItem("coefficient_path_panel", "Coefficient path panel", "Forest / Cox model", "coefficient_path_panel", "LidocaineQ/Figure_Template::coefficient_path_panel"),
    LidocaineQCoverageItem("generalizability_subgroup_composite_panel", "Generalizability subgroup composite", "Forest / Cox model", "generalizability_subgroup_composite_panel", "LidocaineQ/Figure_Template::generalizability_subgroup_composite_panel"),
    LidocaineQCoverageItem("violin_box", "Distribution comparison violin-box", "Violin / box comparison", "distribution_violin_box", "LidocaineQ/Figure_Template::violin_box"),
    LidocaineQCoverageItem("bar_stacked", "Stacked proportion bars", "Bar / stacked proportion", "composition_stacked_bar", "LidocaineQ/Figure_Template::bar_stacked"),
    LidocaineQCoverageItem("risk_layering_monotonic_bars", "Monotonic risk layering bars", "Bar / stacked proportion", "risk_layering_monotonic_bars", "LidocaineQ/Figure_Template::risk_layering_monotonic_bars"),
    LidocaineQCoverageItem("scatter_correlation", "Scatter correlation panel", "Scatter / correlation", "correlation_scatter", "LidocaineQ/Figure_Template::scatter_correlation"),
    LidocaineQCoverageItem(
        "embedding_umap_tsne",
        "Embedding scatter",
        "UMAP / t-SNE embedding",
        "umap_scatter_grouped",
        "LidocaineQ/Figure_Template::embedding_umap_tsne",
        ("umap_scatter_grouped", "tsne_scatter_grouped"),
        mapping_relation="renamed_current_template",
        replacement_reason="One LidocaineQ embedding reference covers MAS current UMAP and t-SNE computed-workflow templates; do not add a duplicate external-id alias.",
    ),
    LidocaineQCoverageItem("heatmap", "ComplexHeatmap annotated matrix", "Heatmap / matrix pattern", "heatmap_group_comparison", "LidocaineQ/Figure_Template::heatmap", mapping_relation="renamed_current_template", replacement_reason="MAS current canonical template names the group-comparison heatmap surface; heatmap remains the external source renderer id."),
    LidocaineQCoverageItem("confusion_matrix_heatmap_binary", "Binary confusion matrix heatmap", "Heatmap / matrix pattern", "confusion_matrix_heatmap_binary", "LidocaineQ/Figure_Template::confusion_matrix_heatmap_binary"),
    LidocaineQCoverageItem("volcano_deg", "Differential-expression volcano", "Volcano / differential expression", "omics_volcano_panel", "LidocaineQ/Figure_Template::volcano_deg", mapping_relation="renamed_current_template", replacement_reason="MAS current canonical template names the omics volcano panel surface; volcano_deg remains the source renderer id."),
    LidocaineQCoverageItem("gsea_enrichment", "Pathway enrichment dotplot", "GSEA / enrichment", "pathway_enrichment_dotplot_panel", "LidocaineQ/Figure_Template::gsea_enrichment", mapping_relation="renamed_current_template", replacement_reason="MAS current canonical template names the pathway enrichment dotplot surface; gsea_enrichment remains the source renderer id."),
    LidocaineQCoverageItem("oncoplot_mutation", "Mutation landscape oncoplot", "Oncoplot / mutation landscape", "genomic_alteration_landscape_panel", "LidocaineQ/Figure_Template::oncoplot_mutation", mapping_relation="renamed_current_template", replacement_reason="MAS current canonical template names the genomic alteration landscape surface; oncoplot_mutation remains the source renderer id."),
    LidocaineQCoverageItem("genomic_alteration_consequence_panel", "Genomic alteration consequence", "Oncoplot / mutation landscape", "genomic_alteration_consequence_panel", "LidocaineQ/Figure_Template::genomic_alteration_consequence_panel"),
    LidocaineQCoverageItem("cnv_recurrence_summary_panel", "CNV recurrence summary", "Oncoplot / mutation landscape", "cnv_recurrence_summary_panel", "LidocaineQ/Figure_Template::cnv_recurrence_summary_panel"),
    LidocaineQCoverageItem("waterfall", "Ranked risk-score waterfall", "Waterfall / ranked risk score", "waterfall_response", "LidocaineQ/Figure_Template::waterfall"),
    LidocaineQCoverageItem("shap_dependence_panel", "SHAP dependence panel", "Scatter / correlation", "shap_dependence_panel", "LidocaineQ/Figure_Template::shap_dependence_panel"),
    LidocaineQCoverageItem("shap_summary_beeswarm", "SHAP summary beeswarm", "Scatter / correlation", "shap_summary_beeswarm", "LidocaineQ/Figure_Template::shap_summary_beeswarm"),
    LidocaineQCoverageItem("shap_waterfall_local_explanation_panel", "SHAP waterfall local explanation", "Waterfall / ranked risk score", "shap_waterfall_local_explanation_panel", "LidocaineQ/Figure_Template::shap_waterfall_local_explanation_panel"),
    LidocaineQCoverageItem("model_complexity_audit_panel", "Model complexity audit", "Scatter / correlation", "model_complexity_audit_panel", "LidocaineQ/Figure_Template::model_complexity_audit_panel"),
    LidocaineQCoverageItem("celltype_marker_dotplot_panel", "Cell-type marker dotplot", "Heatmap / matrix pattern", "celltype_marker_dotplot_panel", "LidocaineQ/Figure_Template::celltype_marker_dotplot_panel"),
    LidocaineQCoverageItem("sankey_alluvial", "Subtype transition alluvial", "Sankey / alluvial flow", "alluvial_transition", "LidocaineQ/Figure_Template::sankey_alluvial"),
    LidocaineQCoverageItem("radar", "Radial immune/pathology profile", "Radar / radial profile", "radar_profile", "LidocaineQ/Figure_Template::radar"),
    LidocaineQCoverageItem("baseline_table", "Baseline summary table", "Baseline / summary table", "table1_baseline_characteristics", "LidocaineQ/Figure_Template::baseline_table", mapping_relation="renamed_current_template", replacement_reason="MAS current canonical template keeps Table 1 semantics and uses a Gallery-only R preview for the LidocaineQ baseline table reference."),
)

_RETIRED_ALIAS_REFERENCE_IDS = {
    "violin_box",
    "bar_stacked",
    "scatter_correlation",
    "waterfall",
    "sankey_alluvial",
    "radar",
}


def _item_mapping_relation(item: LidocaineQCoverageItem) -> str:
    if item.reference_template_id in _RETIRED_ALIAS_REFERENCE_IDS:
        return "retired_alias_to_current_template"
    return item.mapping_relation


def _item_replacement_reason(item: LidocaineQCoverageItem) -> str:
    if item.reference_template_id in _RETIRED_ALIAS_REFERENCE_IDS:
        return "PDF reference id is preserved as LidocaineQ source id; MAS current canonical template replaces the retired duplicate alias."
    return item.replacement_reason


def _item_do_not_restore_alias(item: LidocaineQCoverageItem) -> bool:
    return item.do_not_restore_legacy_alias or item.reference_template_id in _RETIRED_ALIAS_REFERENCE_IDS


def lidocaineq_coverage_payload(
    *,
    rendered_by_template_id: dict[str, Any],
    source_renderer_by_template_id: dict[str, str],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in LIDOCAINEQ_COVERAGE_ITEMS:
        required_template_ids = item.required_mas_template_ids or (item.mas_template_id,)
        render_status_by_template_id: dict[str, str] = {}
        source_renderer_by_required_template_id: dict[str, str] = {}
        missing_or_downgraded_template_ids: list[str] = []
        covered_template_ids: list[str] = []
        for template_id in required_template_ids:
            asset = rendered_by_template_id.get(template_id)
            render_status = getattr(asset, "status", "missing")
            source_renderer = source_renderer_by_template_id.get(template_id, "")
            render_status_by_template_id[template_id] = render_status
            source_renderer_by_required_template_id[template_id] = source_renderer
            if render_status == "rendered" and source_renderer == item.expected_source_renderer:
                covered_template_ids.append(template_id)
            else:
                missing_or_downgraded_template_ids.append(template_id)
        primary_render_status = render_status_by_template_id.get(item.mas_template_id, "missing")
        primary_source_renderer = source_renderer_by_required_template_id.get(item.mas_template_id, "")
        covered = not missing_or_downgraded_template_ids
        rows.append({
            "reference_template_id": item.reference_template_id,
            "title": item.title,
            "category_label": item.category_label,
            "mas_template_id": item.mas_template_id,
            "mas_template_ids": list(required_template_ids),
            "mapping_relation": _item_mapping_relation(item),
            "replacement_reason": _item_replacement_reason(item),
            "legacy_alias_status": (
                "retired_do_not_restore"
                if _item_do_not_restore_alias(item)
                else "not_a_mas_legacy_alias"
            ),
            "do_not_restore_legacy_alias": _item_do_not_restore_alias(item),
            "expected_source_renderer": item.expected_source_renderer,
            "actual_source_renderer": primary_source_renderer,
            "actual_source_renderers": source_renderer_by_required_template_id,
            "render_status": primary_render_status,
            "render_status_by_template_id": render_status_by_template_id,
            "covered_mas_template_ids": covered_template_ids,
            "missing_or_downgraded_mas_template_ids": missing_or_downgraded_template_ids,
            "coverage_status": "covered" if covered else "missing_or_downgraded",
        })
    missing = [row["reference_template_id"] for row in rows if row["coverage_status"] != "covered"]
    relation_counts: dict[str, int] = {}
    for row in rows:
        relation = str(row["mapping_relation"])
        relation_counts[relation] = relation_counts.get(relation, 0) + 1
    return {
        "schema_version": 1,
        "source_project": "LidocaineQ/Figure_Template",
        "reference_template_count": len(LIDOCAINEQ_COVERAGE_ITEMS),
        "covered_reference_template_count": len(rows) - len(missing),
        "coverage_complete": not missing,
        "missing_or_downgraded_reference_template_ids": missing,
        "mapping_relation_counts": relation_counts,
        "replacement_template_count": sum(
            relation_counts.get(key, 0)
            for key in ("renamed_current_template", "retired_alias_to_current_template")
        ),
        "retired_alias_reference_template_count": relation_counts.get("retired_alias_to_current_template", 0),
        "do_not_restore_legacy_alias_count": sum(
            1 for row in rows if row["do_not_restore_legacy_alias"]
        ),
        "items": rows,
    }
