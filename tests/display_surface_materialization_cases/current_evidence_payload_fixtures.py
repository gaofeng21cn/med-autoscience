from __future__ import annotations

from typing import Any

from med_autoscience import display_registry


def _full(template_id: str) -> str:
    return display_registry.get_evidence_figure_spec(template_id).template_id


def _make_generalizability_subgroup_composite_panel_display(display_id: str = "Figure14") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": _full("generalizability_subgroup_composite_panel"),
        "title": "Generalizability and subgroup discrimination composite for external validation",
        "caption": "Bounded composite lock for external generalizability and subgroup stability.",
        "metric_family": "discrimination",
        "primary_label": "Locked model",
        "comparator_label": "Derivation cohort",
        "overview_panel_title": "External cohort discrimination overview",
        "overview_x_label": "AUROC",
        "overview_rows": [
            {"cohort_id": "external_a", "cohort_label": "External A", "support_count": 184, "event_count": 29, "metric_value": 0.82, "comparator_metric_value": 0.79},
            {"cohort_id": "external_b", "cohort_label": "External B", "support_count": 163, "event_count": 21, "metric_value": 0.78, "comparator_metric_value": 0.79},
        ],
        "subgroup_panel_title": "Prespecified subgroup discrimination stability",
        "subgroup_x_label": "AUROC",
        "subgroup_reference_value": 0.80,
        "subgroup_rows": [
            {"subgroup_id": "age_ge_65", "subgroup_label": "Age >=65 years", "group_n": 201, "estimate": 0.82, "lower": 0.78, "upper": 0.86},
            {"subgroup_id": "female", "subgroup_label": "Female", "group_n": 173, "estimate": 0.79, "lower": 0.75, "upper": 0.83},
        ],
    }


def _binary_prediction_curve_displays() -> list[dict[str, Any]]:
    return [
        {
            "display_id": "Figure2",
            "template_id": _full("roc_curve_binary"),
            "title": "ROC curve for the primary model",
            "caption": "Discrimination of the primary model across thresholds.",
            "x_label": "1 - Specificity",
            "y_label": "Sensitivity",
            "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Chance"},
            "series": [{"label": "Primary model", "x": [0.0, 0.08, 0.24, 1.0], "y": [0.0, 0.66, 0.87, 1.0], "annotation": "AUC = 0.84"}],
        },
        {
            "display_id": "Figure3",
            "template_id": _full("pr_curve_binary"),
            "title": "Precision-recall curve for the primary model",
            "caption": "Positive predictive yield across recall levels.",
            "x_label": "Recall",
            "y_label": "Precision",
            "reference_line": {"x": [0.0, 1.0], "y": [0.42, 0.42], "label": "Prevalence"},
            "series": [{"label": "Primary model", "x": [0.0, 0.25, 0.55, 1.0], "y": [1.0, 0.82, 0.69, 0.42], "annotation": "AP = 0.73"}],
        },
        {
            "display_id": "Figure4",
            "template_id": _full("calibration_curve_binary"),
            "title": "Calibration curve for the primary model",
            "caption": "Observed versus predicted risk across bins.",
            "x_label": "Predicted probability",
            "y_label": "Observed event rate",
            "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Ideal"},
            "series": [{"label": "Primary model", "x": [0.05, 0.20, 0.40, 0.70, 0.90], "y": [0.08, 0.22, 0.36, 0.68, 0.88], "annotation": "Slope = 0.97"}],
        },
        {
            "display_id": "Figure5",
            "template_id": _full("decision_curve_binary"),
            "title": "Decision curve for the primary model",
            "caption": "Net benefit across clinically relevant thresholds.",
            "x_label": "Threshold probability",
            "y_label": "Net benefit",
            "reference_line": {"x": [0.0, 1.0], "y": [0.0, 0.0], "label": "Treat none"},
            "series": [
                {"label": "Primary model", "x": [0.05, 0.10, 0.20, 0.30, 0.40], "y": [0.18, 0.17, 0.14, 0.10, 0.07]},
                {"label": "Treat all", "x": [0.05, 0.10, 0.20, 0.30, 0.40], "y": [0.16, 0.13, 0.08, 0.03, -0.02]},
            ],
        },
        {
            "display_id": "Figure8",
            "template_id": _full("time_dependent_roc_horizon"),
            "title": "Time-dependent ROC at 24 months",
            "caption": "Horizon-specific discrimination of the locked survival model.",
            "time_horizon_months": 24,
            "x_label": "1 - Specificity",
            "y_label": "Sensitivity",
            "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Chance"},
            "series": [{"label": "24-month horizon", "x": [0.0, 0.12, 0.28, 1.0], "y": [0.0, 0.69, 0.84, 1.0], "annotation": "AUC = 0.81"}],
        },
    ]


def _survival_grouped_displays() -> list[dict[str, Any]]:
    return [
        {
            "display_id": "Figure6",
            "template_id": _full("kaplan_meier_grouped"),
            "title": "Kaplan-Meier risk stratification",
            "caption": "Time-to-event separation across prespecified risk groups.",
            "x_label": "Months from surgery",
            "y_label": "Survival probability",
            "groups": [
                {"label": "Low risk", "times": [0, 6, 12, 18, 24], "values": [1.0, 0.96, 0.93, 0.90, 0.88]},
                {"label": "High risk", "times": [0, 6, 12, 18, 24], "values": [1.0, 0.88, 0.77, 0.69, 0.62]},
            ],
            "annotation": "Log-rank P < .001",
        },
        {
            "display_id": "Figure7",
            "template_id": _full("cumulative_incidence_grouped"),
            "title": "Cumulative incidence by risk group",
            "caption": "Event accumulation across prespecified risk strata.",
            "x_label": "Months from surgery",
            "y_label": "Cumulative incidence",
            "groups": [
                {"label": "Low risk", "times": [0, 6, 12, 18, 24], "values": [0.00, 0.04, 0.07, 0.09, 0.12]},
                {"label": "High risk", "times": [0, 6, 12, 18, 24], "values": [0.00, 0.12, 0.23, 0.31, 0.38]},
            ],
            "annotation": "Gray test P = .002",
        },
    ]


def _time_to_event_multihorizon_display() -> dict[str, Any]:
    return {
        "display_id": "Figure9",
        "template_id": _full("time_to_event_multihorizon_calibration_panel"),
        "title": "Grouped survival calibration governance across 36 and 60 months",
        "caption": "Parallel grouped calibration panels lock multi-horizon review to audited contracts.",
        "x_label": "Predicted / observed risk",
        "panels": [
            {"panel_id": "h36", "panel_label": "A", "title": "36-month calibration", "time_horizon_months": 36, "calibration_summary": [
                {"group_label": "Low risk", "group_order": 1, "n": 182, "events": 5, "predicted_risk": 0.03, "observed_risk": 0.04},
                {"group_label": "High risk", "group_order": 2, "n": 88, "events": 22, "predicted_risk": 0.24, "observed_risk": 0.27},
            ]},
            {"panel_id": "h60", "panel_label": "B", "title": "60-month calibration", "time_horizon_months": 60, "calibration_summary": [
                {"group_label": "Low risk", "group_order": 1, "n": 182, "events": 8, "predicted_risk": 0.04, "observed_risk": 0.05},
                {"group_label": "High risk", "group_order": 2, "n": 88, "events": 27, "predicted_risk": 0.31, "observed_risk": 0.29},
            ]},
        ],
    }


def _time_to_event_decision_curve_display() -> dict[str, Any]:
    return {
        "display_id": "Figure10",
        "template_id": _full("time_to_event_decision_curve"),
        "title": "Time-to-event decision curve at 24 months",
        "caption": "Net benefit for the survival model at the clinical decision horizon.",
        "time_horizon_months": 24,
        "panel_a_title": "Decision-curve net benefit",
        "panel_b_title": "Model-treated fraction",
        "x_label": "Threshold probability",
        "y_label": "Net benefit",
        "treated_fraction_y_label": "Patients classified above threshold (%)",
        "reference_line": {"x": [0.05, 0.45], "y": [0.0, 0.0], "label": "Treat none"},
        "series": [
            {"label": "Locked survival model", "x": [0.05, 0.10, 0.20, 0.30], "y": [0.18, 0.17, 0.15, 0.12]},
            {"label": "Treat all", "x": [0.05, 0.10, 0.20, 0.30], "y": [0.15, 0.12, 0.08, 0.03]},
        ],
        "treated_fraction_series": {"label": "Locked survival model", "x": [0.05, 0.10, 0.20, 0.30], "y": [62.0, 49.0, 31.0, 18.0]},
    }


def _risk_layering_display() -> dict[str, Any]:
    return {
        "display_id": "Figure11",
        "template_id": _full("risk_layering_monotonic_bars"),
        "title": "Risk layering by score band",
        "caption": "Predicted and observed event proportions remain monotonic across prespecified strata.",
        "y_label": "Outcome risk (%)",
        "left_panel_title": "Predicted risk by tertile",
        "left_x_label": "Predicted risk tertile",
        "left_bars": [
            {"label": "Low", "cases": 120, "events": 2, "risk": 2 / 120},
            {"label": "Intermediate", "cases": 120, "events": 4, "risk": 4 / 120},
            {"label": "High", "cases": 120, "events": 11, "risk": 11 / 120},
        ],
        "right_panel_title": "Observed risk by tertile",
        "right_x_label": "Observed risk tertile",
        "right_bars": [
            {"label": "Low", "cases": 120, "events": 2, "risk": 2 / 120},
            {"label": "Intermediate", "cases": 120, "events": 5, "risk": 5 / 120},
            {"label": "High", "cases": 120, "events": 14, "risk": 14 / 120},
        ],
    }


def _forest_display() -> dict[str, Any]:
    return {
        "display_id": "Figure12",
        "template_id": _full("forest_effect_main"),
        "title": "Main-effect forest plot",
        "caption": "Adjusted effect estimates for prespecified predictors.",
        "x_label": "Odds ratio",
        "reference_value": 1.0,
        "rows": [
            {"label": "Age > 60 years", "estimate": 1.42, "lower": 1.11, "upper": 1.83},
            {"label": "Tumor size > 30 mm", "estimate": 1.89, "lower": 1.35, "upper": 2.62},
        ],
    }


def _coefficient_path_display() -> dict[str, Any]:
    return {
        "display_id": "Figure13",
        "template_id": _full("coefficient_path_panel"),
        "title": "Coefficient path across model stages",
        "caption": "Effect estimates remain stable across prespecified adjustment stages.",
        "path_panel_title": "Coefficient path",
        "x_label": "Adjusted odds ratio",
        "reference_value": 1.0,
        "step_legend_title": "Model stage",
        "steps": [{"step_id": "base", "step_label": "Base", "step_order": 1}, {"step_id": "full", "step_label": "Full", "step_order": 2}],
        "coefficient_rows": [
            {"row_id": "age", "row_label": "Age > 60", "points": [{"step_id": "base", "estimate": 1.30, "lower": 1.05, "upper": 1.62}, {"step_id": "full", "estimate": 1.22, "lower": 1.01, "upper": 1.48}]},
            {"row_id": "tumor", "row_label": "Tumor size", "points": [{"step_id": "base", "estimate": 1.80, "lower": 1.30, "upper": 2.40}, {"step_id": "full", "estimate": 1.64, "lower": 1.22, "upper": 2.20}]},
        ],
        "summary_panel_title": "Model stability",
        "summary_cards": [{"card_id": "n", "label": "Rows", "value": "2"}, {"card_id": "stage", "label": "Stages", "value": "2"}],
    }


def _embedding_displays() -> list[dict[str, Any]]:
    specs = [("Figure15", "pca_scatter_grouped", "PC1", "PC2"), ("Figure16", "tsne_scatter_grouped", "t-SNE 1", "t-SNE 2"), ("Figure17", "umap_scatter_grouped", "UMAP 1", "UMAP 2")]
    return [
        {"display_id": display_id, "template_id": _full(template_id), "title": f"{template_id.split('_')[0].upper()} embedding by subtype", "caption": "Two-dimensional embedding with subtype labels.", "x_label": x_label, "y_label": y_label, "points": [
            {"x": -1.2, "y": 0.6, "group": "Subtype A"}, {"x": -0.9, "y": 0.4, "group": "Subtype A"}, {"x": 0.8, "y": -0.5, "group": "Subtype B"}, {"x": 1.1, "y": -0.7, "group": "Subtype B"},
        ]}
        for display_id, template_id, x_label, y_label in specs
    ]


def _heatmap_display(display_id: str = "Figure18") -> dict[str, Any]:
    return {"display_id": display_id, "template_id": _full("heatmap_group_comparison"), "title": "Group comparison heatmap", "caption": "Standardized feature contrast across prespecified groups.", "x_label": "Group", "y_label": "Feature", "cells": [
        {"x": "Low risk", "y": "Age", "value": -0.6}, {"x": "High risk", "y": "Age", "value": 0.7}, {"x": "Low risk", "y": "Tumor size", "value": -0.4}, {"x": "High risk", "y": "Tumor size", "value": 0.8},
    ]}


def _confusion_matrix_display() -> dict[str, Any]:
    return {"display_id": "Figure19", "template_id": _full("confusion_matrix_heatmap_binary"), "title": "Binary confusion matrix", "caption": "Row-normalized confusion matrix on the held-out cohort.", "x_label": "Predicted class", "y_label": "Observed class", "metric_name": "Observed proportion", "normalization": "row_fraction", "row_order": [{"label": "Observed negative"}, {"label": "Observed positive"}], "column_order": [{"label": "Predicted negative"}, {"label": "Predicted positive"}], "cells": [
        {"x": "Predicted negative", "y": "Observed negative", "value": 0.88}, {"x": "Predicted positive", "y": "Observed negative", "value": 0.12}, {"x": "Predicted negative", "y": "Observed positive", "value": 0.19}, {"x": "Predicted positive", "y": "Observed positive", "value": 0.81},
    ]}


def _genomic_base(template_id: str, display_id: str) -> dict[str, Any]:
    return {"display_id": display_id, "template_id": _full(template_id), "title": "Genomic alteration landscape", "caption": "Alteration classes across representative samples.", "y_label": "Genes", "burden_axis_label": "Alteration burden", "frequency_axis_label": "Frequency", "alteration_legend_title": "Alteration", "gene_order": [{"label": "TP53"}, {"label": "KRAS"}], "sample_order": [{"sample_id": "S1"}, {"sample_id": "S2"}], "annotation_tracks": [{"track_id": "subtype", "track_label": "Subtype", "values": [{"sample_id": "S1", "category_label": "A"}, {"sample_id": "S2", "category_label": "B"}]}], "alteration_records": [
        {"sample_id": "S1", "gene_label": "TP53", "mutation_class": "missense"}, {"sample_id": "S1", "gene_label": "KRAS", "cnv_state": "gain"}, {"sample_id": "S2", "gene_label": "TP53", "mutation_class": "truncating"}, {"sample_id": "S2", "gene_label": "KRAS", "cnv_state": "loss"},
    ]}


def _cnv_display() -> dict[str, Any]:
    return {"display_id": "Figure21", "template_id": _full("cnv_recurrence_summary_panel"), "title": "CNV recurrence summary", "caption": "Recurrent copy-number events across representative samples.", "y_label": "Regions", "burden_axis_label": "CNV burden", "frequency_axis_label": "Frequency", "cnv_legend_title": "CNV state", "region_order": [{"label": "8q"}, {"label": "17p"}], "sample_order": [{"sample_id": "S1"}, {"sample_id": "S2"}], "annotation_tracks": [{"track_id": "subtype", "track_label": "Subtype", "values": [{"sample_id": "S1", "category_label": "A"}, {"sample_id": "S2", "category_label": "B"}]}], "cnv_records": [
        {"sample_id": "S1", "region_label": "8q", "cnv_state": "gain"}, {"sample_id": "S1", "region_label": "17p", "cnv_state": "loss"}, {"sample_id": "S2", "region_label": "8q", "cnv_state": "amplification"}, {"sample_id": "S2", "region_label": "17p", "cnv_state": "deep_loss"},
    ]}


def _genomic_consequence_display() -> dict[str, Any]:
    payload = _genomic_base("genomic_alteration_consequence_panel", "Figure22")
    payload.update({"consequence_x_label": "Effect", "consequence_y_label": "-log10(q)", "consequence_legend_title": "Regulation", "effect_threshold": 0.5, "significance_threshold": 1.3, "driver_gene_order": [{"label": "TP53"}, {"label": "KRAS"}], "consequence_panel_order": [{"panel_id": "rna", "panel_title": "RNA"}], "consequence_points": [
        {"panel_id": "rna", "gene_label": "TP53", "effect_value": 0.8, "significance_value": 2.1, "regulation_class": "upregulated"},
        {"panel_id": "rna", "gene_label": "KRAS", "effect_value": -0.7, "significance_value": 1.8, "regulation_class": "downregulated"},
    ]})
    return payload


def _dotplot(template_id: str, display_id: str, *, celltype: bool = False) -> dict[str, Any]:
    base = {"display_id": display_id, "template_id": _full(template_id), "title": "Dotplot panel", "caption": "Effect-size and support encoded dotplot.", "x_label": "Effect", "y_label": "Pathway", "effect_scale_label": "Effect", "size_scale_label": "Support", "panel_order": [{"panel_id": "all", "panel_title": "All"}]}
    if celltype:
        base.update({"celltype_order": [{"label": "T cells"}, {"label": "Myeloid"}], "marker_order": [{"label": "CD3D"}, {"label": "LYZ"}], "points": [
            {"panel_id": "all", "celltype_label": "T cells", "marker_label": "CD3D", "effect_value": 1.1, "size_value": 0.8}, {"panel_id": "all", "celltype_label": "T cells", "marker_label": "LYZ", "effect_value": -0.2, "size_value": 0.2}, {"panel_id": "all", "celltype_label": "Myeloid", "marker_label": "CD3D", "effect_value": -0.4, "size_value": 0.2}, {"panel_id": "all", "celltype_label": "Myeloid", "marker_label": "LYZ", "effect_value": 1.4, "size_value": 0.9},
        ]})
    else:
        base.update({"pathway_order": [{"label": "IFN response"}, {"label": "TGF-beta"}], "points": [
            {"panel_id": "all", "pathway_label": "IFN response", "x_value": 2.1, "effect_value": 0.8, "size_value": 12}, {"panel_id": "all", "pathway_label": "TGF-beta", "x_value": 1.4, "effect_value": -0.5, "size_value": 8},
        ]})
    return base


def _omics_volcano_display() -> dict[str, Any]:
    return {"display_id": "Figure25", "template_id": _full("omics_volcano_panel"), "title": "Omics volcano panel", "caption": "Differential features across prespecified contrasts.", "x_label": "Effect size", "y_label": "-log10(q)", "legend_title": "Regulation", "effect_threshold": 0.5, "significance_threshold": 1.3, "panel_order": [{"panel_id": "rna", "panel_title": "RNA"}], "points": [
        {"panel_id": "rna", "feature_label": "GENE1", "effect_value": 0.8, "significance_value": 2.0, "regulation_class": "upregulated", "label_text": "GENE1"}, {"panel_id": "rna", "feature_label": "GENE2", "effect_value": -0.7, "significance_value": 1.8, "regulation_class": "downregulated"},
    ]}


def _shap_summary_display() -> dict[str, Any]:
    return {"display_id": "Figure26", "template_id": _full("shap_summary_beeswarm"), "title": "SHAP summary beeswarm", "caption": "Feature-level SHAP distribution ranked by mean absolute contribution.", "x_label": "SHAP value", "rows": [{"feature": "Tumor size", "points": [{"shap_value": -0.42, "feature_value": 0.15}, {"shap_value": 0.31, "feature_value": 0.83}]}, {"feature": "Age", "points": [{"shap_value": -0.18, "feature_value": 0.28}, {"shap_value": 0.22, "feature_value": 0.74}]}]}


def _shap_dependence_display() -> dict[str, Any]:
    return {"display_id": "Figure27", "template_id": _full("shap_dependence_panel"), "title": "SHAP dependence panel", "caption": "Dependence of SHAP value on feature level and interaction value.", "y_label": "SHAP value", "colorbar_label": "Interaction", "panels": [{"panel_id": "age", "panel_label": "A", "title": "Age", "x_label": "Age", "feature": "Age", "interaction_feature": "Tumor size", "points": [{"feature_value": 45, "shap_value": -0.2, "interaction_value": 0.3}, {"feature_value": 70, "shap_value": 0.4, "interaction_value": 0.8}]}]}


def _shap_waterfall_display() -> dict[str, Any]:
    return {"display_id": "Figure28", "template_id": _full("shap_waterfall_local_explanation_panel"), "title": "Local SHAP waterfall explanation", "caption": "Patient-level contribution stack for local explanation.", "x_label": "Model output", "panels": [{"panel_id": "case1", "panel_label": "A", "title": "Case 1", "case_label": "Patient 1", "baseline_value": 0.20, "predicted_value": 0.50, "contributions": [{"feature": "Tumor size", "shap_value": 0.22, "feature_value_text": "Large"}, {"feature": "Age", "shap_value": 0.08, "feature_value_text": "70"}]}]}


def _model_complexity_display() -> dict[str, Any]:
    panel = {"panel_id": "auc", "panel_label": "A", "title": "Discrimination", "x_label": "AUROC", "rows": [{"label": "Base", "value": 0.78}, {"label": "Full", "value": 0.84}]}
    audit = {"panel_id": "df", "panel_label": "B", "title": "Complexity", "x_label": "Parameters", "rows": [{"label": "Base", "value": 8}, {"label": "Full", "value": 14}]}
    return {"display_id": "Figure29", "template_id": _full("model_complexity_audit_panel"), "title": "Model complexity audit", "caption": "Discrimination and complexity are audited together.", "metric_panels": [panel], "audit_panels": [audit]}


def _current_evidence_input_envelopes() -> dict[str, dict[str, Any]]:
    return {
        "binary_prediction_curve_inputs.json": {"schema_version": 1, "input_schema_id": "binary_prediction_curve_inputs_v1", "displays": _binary_prediction_curve_displays()},
        "time_to_event_grouped_inputs.json": {"schema_version": 1, "input_schema_id": "time_to_event_grouped_inputs_v1", "displays": _survival_grouped_displays()},
        "time_to_event_multihorizon_calibration_inputs.json": {"schema_version": 1, "input_schema_id": "time_to_event_multihorizon_calibration_inputs_v1", "displays": [_time_to_event_multihorizon_display()]},
        "time_to_event_decision_curve_inputs.json": {"schema_version": 1, "input_schema_id": "time_to_event_decision_curve_inputs_v1", "displays": [_time_to_event_decision_curve_display()]},
        "risk_layering_monotonic_inputs.json": {"schema_version": 1, "input_schema_id": "risk_layering_monotonic_inputs_v1", "displays": [_risk_layering_display()]},
        "forest_effect_inputs.json": {"schema_version": 1, "input_schema_id": "forest_effect_inputs_v1", "displays": [_forest_display()]},
        "coefficient_path_panel_inputs.json": {"schema_version": 1, "input_schema_id": "coefficient_path_panel_inputs_v1", "displays": [_coefficient_path_display()]},
        "generalizability_subgroup_composite_inputs.json": {"schema_version": 1, "input_schema_id": "generalizability_subgroup_composite_inputs_v1", "displays": [_make_generalizability_subgroup_composite_panel_display()]},
        "embedding_grouped_inputs.json": {"schema_version": 1, "input_schema_id": "embedding_grouped_inputs_v1", "displays": _embedding_displays()},
        "heatmap_group_comparison_inputs.json": {"schema_version": 1, "input_schema_id": "heatmap_group_comparison_inputs_v1", "displays": [_heatmap_display()]},
        "confusion_matrix_heatmap_binary_inputs.json": {"schema_version": 1, "input_schema_id": "confusion_matrix_heatmap_binary_inputs_v1", "displays": [_confusion_matrix_display()]},
        "genomic_alteration_landscape_panel_inputs.json": {"schema_version": 1, "input_schema_id": "genomic_alteration_landscape_panel_inputs_v1", "displays": [_genomic_base("genomic_alteration_landscape_panel", "Figure20")]},
        "cnv_recurrence_summary_panel_inputs.json": {"schema_version": 1, "input_schema_id": "cnv_recurrence_summary_panel_inputs_v1", "displays": [_cnv_display()]},
        "genomic_alteration_consequence_panel_inputs.json": {"schema_version": 1, "input_schema_id": "genomic_alteration_consequence_panel_inputs_v1", "displays": [_genomic_consequence_display()]},
        "pathway_enrichment_dotplot_panel_inputs.json": {"schema_version": 1, "input_schema_id": "pathway_enrichment_dotplot_panel_inputs_v1", "displays": [_dotplot("pathway_enrichment_dotplot_panel", "Figure23")]},
        "celltype_marker_dotplot_panel_inputs.json": {"schema_version": 1, "input_schema_id": "celltype_marker_dotplot_panel_inputs_v1", "displays": [_dotplot("celltype_marker_dotplot_panel", "Figure24", celltype=True)]},
        "omics_volcano_panel_inputs.json": {"schema_version": 1, "input_schema_id": "omics_volcano_panel_inputs_v1", "displays": [_omics_volcano_display()]},
        "shap_summary_inputs.json": {"schema_version": 1, "input_schema_id": "shap_summary_inputs_v1", "displays": [_shap_summary_display()]},
        "shap_dependence_panel_inputs.json": {"schema_version": 1, "input_schema_id": "shap_dependence_panel_inputs_v1", "displays": [_shap_dependence_display()]},
        "shap_waterfall_local_explanation_panel_inputs.json": {"schema_version": 1, "input_schema_id": "shap_waterfall_local_explanation_panel_inputs_v1", "displays": [_shap_waterfall_display()]},
        "model_complexity_audit_panel_inputs.json": {"schema_version": 1, "input_schema_id": "model_complexity_audit_panel_inputs_v1", "displays": [_model_complexity_display()]},
    }


__all__ = ["_current_evidence_input_envelopes", "_make_generalizability_subgroup_composite_panel_display"]
