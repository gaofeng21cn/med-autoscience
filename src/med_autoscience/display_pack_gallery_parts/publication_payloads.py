from __future__ import annotations

from typing import Any


def _matrix_cells(rows: list[str], columns: list[str], values: list[list[float]]) -> list[dict[str, Any]]:
    return [
        {"x": column, "y": row, "value": values[row_index][column_index]}
        for row_index, row in enumerate(rows)
        for column_index, column in enumerate(columns)
    ]


def _embedding_feature_matrix() -> list[dict[str, Any]]:
    latent_points = (
        ("Subtype A", -1.90, 0.32),
        ("Subtype A", -1.72, 0.62),
        ("Subtype A", -1.48, 0.84),
        ("Subtype A", -1.25, 0.98),
        ("Subtype A", -0.98, 0.86),
        ("Subtype A", -0.78, 0.58),
        ("Subtype A", -0.63, 0.24),
        ("Transition", -0.42, -0.06),
        ("Transition", -0.20, -0.27),
        ("Transition", 0.02, -0.34),
        ("Transition", 0.24, -0.27),
        ("Transition", 0.45, -0.08),
        ("Subtype B", 0.64, 0.18),
        ("Subtype B", 0.82, 0.52),
        ("Subtype B", 1.04, 0.82),
        ("Subtype B", 1.28, 0.98),
        ("Subtype B", 1.54, 0.86),
        ("Subtype B", 1.76, 0.58),
        ("Subtype B", 1.94, 0.25),
        ("Subtype A", -1.58, -0.28),
        ("Subtype A", -1.18, -0.48),
        ("Subtype B", 1.18, -0.48),
        ("Subtype B", 1.58, -0.28),
        ("Transition", 0.02, 0.18),
    )
    feature_names = (
        "immune_signal",
        "stromal_signal",
        "proliferation",
        "hypoxia",
        "metabolic_shift",
        "antigen_presentation",
        "cell_cycle_curvature",
        "microenvironment_bridge",
    )
    rows: list[dict[str, Any]] = []
    for index, (group, latent_x, latent_y) in enumerate(latent_points, start=1):
        values = (
            latent_x + 0.18 * latent_y,
            latent_y + 0.08 * latent_x,
            latent_x * latent_y,
            latent_y**2 - 0.35 * latent_x,
            (latent_x**2) * 0.45 - latent_y,
            -0.45 * latent_x + 0.70 * latent_y,
            (latent_x**2 + latent_y**2) * 0.32,
            latent_y - 0.55 * abs(latent_x),
        )
        rows.append(
            {
                "sample_id": f"S{index:02d}",
                "group": group,
                "features": {name: value for name, value in zip(feature_names, values, strict=True)},
            }
        )
    return rows


def _embedding_workflow_payload(
    *,
    display_id: str,
    template_id: str,
    title: str,
    caption: str,
    x_label: str,
    y_label: str,
    embedding_options: dict[str, Any],
) -> dict[str, Any]:
    return {
        "display_id": display_id,
        "template_id": template_id,
        "title": title,
        "caption": caption,
        "x_label": x_label,
        "y_label": y_label,
        "embedding_input_mode": "feature_matrix",
        "source_feature_matrix_digest": "gallery-shared-synthetic-embedding-matrix-v1",
        "feature_matrix": _embedding_feature_matrix(),
        "embedding_options": embedding_options,
    }


def _shap_dependence_points() -> list[dict[str, float]]:
    values = [42, 47, 51, 56, 59, 63, 66, 70, 73, 78, 82, 86]
    interaction = [0.22, 0.28, 0.34, 0.38, 0.45, 0.50, 0.58, 0.64, 0.71, 0.78, 0.84, 0.90]
    return [
        {
            "feature_value": value,
            "shap_value": round(-0.30 + (index * 0.065) + (0.035 if index % 3 == 0 else -0.018), 3),
            "interaction_value": interaction[index],
        }
        for index, value in enumerate(values)
    ]


PUBLICATION_R_DISPLAY_PAYLOADS: dict[str, dict[str, Any]] = {
    "kaplan_meier_grouped": {
        "display_id": "Figure6",
        "template_id": "kaplan_meier_grouped",
        "title": "Kaplan-Meier risk stratification",
        "caption": "Time-to-event separation across prespecified risk groups with censor marks and compact at-risk table.",
        "x_label": "Months from surgery",
        "y_label": "Survival probability",
        "groups": [
            {
                "label": "Low risk",
                "times": [0, 6, 12, 18, 24],
                "values": [1.0, 0.96, 0.93, 0.90, 0.88],
                "censor_times": [9, 15, 21],
            },
            {
                "label": "High risk",
                "times": [0, 6, 12, 18, 24],
                "values": [1.0, 0.88, 0.77, 0.69, 0.62],
                "censor_times": [7, 14, 20],
            },
        ],
        "risk_table_title": "Number at risk",
        "risk_table": [
            {"label": "Low risk", "times": [0, 6, 12, 18, 24], "at_risk": [128, 121, 110, 97, 84]},
            {"label": "High risk", "times": [0, 6, 12, 18, 24], "at_risk": [126, 112, 94, 73, 55]},
        ],
        "annotation": "Log-rank P < .001",
    },
    "celltype_marker_dotplot_panel": {
        "display_id": "Figure24",
        "template_id": "celltype_marker_dotplot_panel",
        "title": "Cell-type marker expression dotplot",
        "caption": "Marker-level effect size and detection fraction across immune cell types.",
        "x_label": "Cell type",
        "y_label": "Marker",
        "effect_scale_label": "Scaled expression",
        "size_scale_label": "Detection",
        "panel_order": [{"panel_id": "all", "panel_title": "Marker activity"}],
        "celltype_order": [{"label": item} for item in ["CD8 T", "CD4 T", "B cell", "Myeloid"]],
        "marker_order": [{"label": item} for item in ["GZMB", "CD3D", "MS4A1", "LYZ", "S100A8"]],
        "points": [
            {"panel_id": "all", "celltype_label": cell, "marker_label": marker, "effect_value": value, "size_value": size}
            for cell, marker, value, size in [
                ("CD8 T", "GZMB", 1.18, 0.84),
                ("CD8 T", "CD3D", 0.92, 0.78),
                ("CD4 T", "CD3D", 0.86, 0.74),
                ("B cell", "MS4A1", 1.05, 0.82),
                ("Myeloid", "LYZ", 1.12, 0.88),
                ("Myeloid", "S100A8", 0.74, 0.62),
                ("B cell", "CD3D", -0.42, 0.18),
                ("CD4 T", "GZMB", -0.16, 0.22),
                ("CD8 T", "LYZ", -0.38, 0.12),
                ("Myeloid", "MS4A1", -0.51, 0.14),
            ]
        ],
    },
    "coefficient_path_panel": {
        "display_id": "Figure13",
        "template_id": "coefficient_path_panel",
        "title": "Coefficient path across prespecified model stages",
        "caption": "Effect estimates remain stable as clinical adjustment layers are added.",
        "path_panel_title": "Coefficient path",
        "x_label": "Adjusted odds ratio",
        "reference_value": 1.0,
        "step_legend_title": "Model stage",
        "steps": [
            {"step_id": "base", "step_label": "Base", "step_order": 1},
            {"step_id": "clinical", "step_label": "Clinical", "step_order": 2},
            {"step_id": "imaging", "step_label": "Imaging", "step_order": 3},
            {"step_id": "full", "step_label": "Full", "step_order": 4},
        ],
        "coefficient_rows": [
            {
                "row_id": "age",
                "row_label": "Age > 60",
                "points": [
                    {"step_id": "base", "estimate": 1.36, "lower": 1.08, "upper": 1.72},
                    {"step_id": "clinical", "estimate": 1.30, "lower": 1.04, "upper": 1.62},
                    {"step_id": "imaging", "estimate": 1.24, "lower": 1.00, "upper": 1.53},
                    {"step_id": "full", "estimate": 1.21, "lower": 1.01, "upper": 1.47},
                ],
            },
            {
                "row_id": "tumor_size",
                "row_label": "Tumor size",
                "points": [
                    {"step_id": "base", "estimate": 1.88, "lower": 1.34, "upper": 2.52},
                    {"step_id": "clinical", "estimate": 1.78, "lower": 1.29, "upper": 2.38},
                    {"step_id": "imaging", "estimate": 1.68, "lower": 1.24, "upper": 2.23},
                    {"step_id": "full", "estimate": 1.61, "lower": 1.20, "upper": 2.15},
                ],
            },
            {
                "row_id": "albumin",
                "row_label": "Albumin",
                "points": [
                    {"step_id": "base", "estimate": 0.76, "lower": 0.61, "upper": 0.94},
                    {"step_id": "clinical", "estimate": 0.79, "lower": 0.64, "upper": 0.98},
                    {"step_id": "imaging", "estimate": 0.82, "lower": 0.67, "upper": 1.00},
                    {"step_id": "full", "estimate": 0.85, "lower": 0.70, "upper": 1.03},
                ],
            },
        ],
    },
    "cnv_recurrence_summary_panel": {
        "display_id": "Figure21",
        "template_id": "cnv_recurrence_summary_panel",
        "title": "CNV recurrence summary",
        "caption": "Recurrent copy-number gains and losses across representative samples.",
        "x_label": "Samples",
        "y_label": "Chromosomal region",
        "cnv_legend_title": "CNV state",
        "region_order": [{"label": item} for item in ["8q gain", "7p gain", "3q gain", "17p loss", "9p loss"]],
        "sample_order": [{"sample_id": item} for item in ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"]],
        "cnv_records": [
            {"sample_id": sample, "region_label": region, "cnv_state": state}
            for sample, region, state in [
                ("S01", "8q gain", "gain"), ("S02", "8q gain", "gain"), ("S03", "8q gain", "gain"), ("S05", "8q gain", "gain"),
                ("S01", "7p gain", "gain"), ("S04", "7p gain", "gain"), ("S06", "7p gain", "gain"),
                ("S02", "3q gain", "amplification"), ("S03", "3q gain", "gain"), ("S07", "3q gain", "gain"),
                ("S01", "17p loss", "loss"), ("S04", "17p loss", "loss"), ("S05", "17p loss", "loss"), ("S08", "17p loss", "loss"),
                ("S03", "9p loss", "deletion"), ("S06", "9p loss", "loss"), ("S08", "9p loss", "loss"),
            ]
        ],
    },
    "genomic_alteration_landscape_panel": {
        "display_id": "Figure20",
        "template_id": "genomic_alteration_landscape_panel",
        "title": "Genomic alteration landscape",
        "caption": "Driver-level mutation and copy-number classes across representative samples.",
        "x_label": "Samples",
        "y_label": "Genes",
        "alteration_legend_title": "Alteration",
        "gene_order": [{"label": item} for item in ["TP53", "KRAS", "PIK3CA", "APC", "SMAD4", "ERBB2"]],
        "sample_order": [{"sample_id": item} for item in ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S08"]],
        "sample_annotations": [
            {
                "label": "Cohort",
                "values": [
                    {"sample_id": "S01", "value": "Derivation"},
                    {"sample_id": "S02", "value": "Derivation"},
                    {"sample_id": "S03", "value": "Derivation"},
                    {"sample_id": "S04", "value": "Validation"},
                    {"sample_id": "S05", "value": "Validation"},
                    {"sample_id": "S06", "value": "Validation"},
                    {"sample_id": "S07", "value": "Validation"},
                    {"sample_id": "S08", "value": "Validation"},
                ],
            },
            {
                "label": "Site",
                "values": [
                    {"sample_id": "S01", "value": "Primary"},
                    {"sample_id": "S02", "value": "Primary"},
                    {"sample_id": "S03", "value": "Metastatic"},
                    {"sample_id": "S04", "value": "Primary"},
                    {"sample_id": "S05", "value": "Metastatic"},
                    {"sample_id": "S06", "value": "Primary"},
                    {"sample_id": "S07", "value": "Metastatic"},
                    {"sample_id": "S08", "value": "Primary"},
                ],
            },
        ],
        "alteration_records": [
            {"sample_id": sample, "gene_label": gene, key: state}
            for sample, gene, key, state in [
                ("S01", "TP53", "mutation_class", "missense"), ("S02", "TP53", "mutation_class", "truncating"),
                ("S04", "TP53", "mutation_class", "missense"), ("S07", "TP53", "cnv_state", "loss"),
                ("S01", "KRAS", "mutation_class", "missense"), ("S03", "KRAS", "mutation_class", "missense"),
                ("S06", "KRAS", "mutation_class", "missense"), ("S08", "KRAS", "mutation_class", "missense"),
                ("S02", "PIK3CA", "mutation_class", "missense"), ("S05", "PIK3CA", "cnv_state", "gain"),
                ("S03", "APC", "mutation_class", "truncating"), ("S04", "APC", "mutation_class", "truncating"), ("S08", "APC", "mutation_class", "truncating"),
                ("S05", "SMAD4", "cnv_state", "loss"), ("S07", "SMAD4", "mutation_class", "missense"),
                ("S02", "ERBB2", "cnv_state", "amplification"), ("S06", "ERBB2", "cnv_state", "amplification"),
            ]
        ],
    },
    "genomic_alteration_consequence_panel": {
        "display_id": "Figure22",
        "template_id": "genomic_alteration_consequence_panel",
        "title": "Genomic alteration consequence panel",
        "caption": "Altered driver genes are linked to transcriptomic effect direction and significance.",
        "consequence_x_label": "Effect size",
        "consequence_y_label": "-log10(q)",
        "consequence_legend_title": "Regulation",
        "effect_threshold": 0.5,
        "significance_threshold": 1.3,
        "consequence_panel_order": [{"panel_id": "rna", "panel_title": "RNA consequence"}],
        "consequence_points": [
            {"panel_id": "rna", "gene_label": gene, "effect_value": effect, "significance_value": sig, "regulation_class": klass, "label_text": label}
            for gene, effect, sig, klass, label in [
                ("TP53", 0.92, 3.05, "upregulated", "TP53"),
                ("ERBB2", 1.18, 2.72, "upregulated", "ERBB2"),
                ("KRAS", 0.64, 2.18, "upregulated", ""),
                ("SMAD4", -0.82, 2.46, "downregulated", "SMAD4"),
                ("APC", -0.61, 1.92, "downregulated", ""),
                ("PIK3CA", 0.42, 1.15, "background", ""),
                ("CDKN2A", -0.74, 2.08, "downregulated", "CDKN2A"),
                ("MYC", 0.78, 2.34, "upregulated", "MYC"),
            ]
        ],
    },
    "model_complexity_audit_panel": {
        "display_id": "model_audit",
        "template_id": "model_complexity_audit_panel",
        "title": "Model complexity audit",
        "caption": "Discrimination, calibration error, and coefficient stability are reviewed together.",
        "metric_panels": [
            {
                "panel_id": "auroc_panel",
                "panel_label": "A",
                "title": "Discrimination",
                "x_label": "AUROC",
                "rows": [
                    {"label": "Core model", "value": 0.80},
                    {"label": "Clinical model", "value": 0.82},
                    {"label": "RF comparator", "value": 0.84},
                ],
            },
            {
                "panel_id": "brier_panel",
                "panel_label": "B",
                "title": "Calibration error",
                "x_label": "Brier score",
                "rows": [
                    {"label": "Core model", "value": 0.142},
                    {"label": "Clinical model", "value": 0.112},
                    {"label": "RF comparator", "value": 0.103},
                ],
            },
        ],
        "panel_order": ["Discrimination", "Calibration error", "Coefficient stability"],
        "audit_panels": [
            {
                "panel_id": "coefficient_panel",
                "panel_label": "C",
                "title": "Coefficient stability",
                "x_label": "Mean odds ratio",
                "reference_value": 1.0,
                "rows": [
                    {"label": "Age", "value": 0.91},
                    {"label": "Tumor size", "value": 1.44},
                    {"label": "Knosp grade", "value": 1.13},
                ],
            }
        ],
    },
    "omics_volcano_panel": {
        "display_id": "Figure25",
        "template_id": "omics_volcano_panel",
        "title": "Omics volcano panel",
        "caption": "Differential features across a prespecified contrast.",
        "x_label": "Effect size",
        "y_label": "-log10(q)",
        "legend_title": "Regulation",
        "effect_threshold": 0.5,
        "significance_threshold": 1.3,
        "panel_order": [{"panel_id": "rna", "panel_title": "RNA"}],
        "points": [
            {"panel_id": "rna", "feature_label": feature, "effect_value": effect, "significance_value": sig, "regulation_class": klass, "label_text": label}
            for feature, effect, sig, klass, label in [
                ("CXCL9", 1.18, 3.10, "upregulated", "CXCL9"),
                ("GZMB", 0.92, 2.72, "upregulated", "GZMB"),
                ("IFNG", 0.74, 2.20, "upregulated", ""),
                ("COL1A1", -1.05, 2.90, "downregulated", "COL1A1"),
                ("TGFB1", -0.78, 2.12, "downregulated", ""),
                ("MKI67", 0.38, 1.05, "background", ""),
                ("EPCAM", -0.34, 0.96, "background", ""),
                ("STAT1", 0.58, 1.74, "upregulated", ""),
                ("VEGFA", -0.55, 1.48, "downregulated", ""),
                ("ACTB", 0.05, 0.42, "background", ""),
                ("GAPDH", -0.08, 0.36, "background", ""),
            ]
        ],
    },
    "pathway_enrichment_dotplot_panel": {
        "display_id": "Figure23",
        "template_id": "pathway_enrichment_dotplot_panel",
        "title": "Pathway enrichment dotplot",
        "caption": "Normalized enrichment score and support size across candidate pathways.",
        "x_label": "Normalized enrichment score",
        "y_label": "Pathway",
        "effect_scale_label": "NES",
        "size_scale_label": "Gene count",
        "panel_order": [{"panel_id": "all", "panel_title": "Pathway programs"}],
        "pathway_order": [{"label": item} for item in ["IFN response", "Cytotoxicity", "Hypoxia", "TGF-beta", "EMT"]],
        "points": [
            {"panel_id": "all", "pathway_label": pathway, "x_value": x, "effect_value": effect, "size_value": size}
            for pathway, x, effect, size in [
                ("IFN response", 2.45, 1.08, 42),
                ("Cytotoxicity", 2.10, 0.86, 36),
                ("Hypoxia", 1.55, 0.44, 27),
                ("TGF-beta", -1.76, -0.68, 31),
                ("EMT", -2.02, -0.82, 38),
            ]
        ],
    },
    "pca_scatter_grouped": _embedding_workflow_payload(
        display_id="Figure15",
        template_id="pca_scatter_grouped",
        title="PCA embedding by subtype",
        caption="Principal component projection computed from the shared high-dimensional feature matrix.",
        x_label="PC1",
        y_label="PC2",
        embedding_options={"center": True, "scale": True},
    ),
    "risk_layering_monotonic_bars": {
        "display_id": "Figure22",
        "template_id": "risk_layering_monotonic_bars",
        "title": "Risk layering by score band",
        "caption": "Predicted and observed risk increase monotonically across prespecified score bands.",
        "y_label": "Outcome risk (%)",
        "left_panel_title": "Predicted risk",
        "left_x_label": "Risk band",
        "left_bars": [
            {"label": "Low", "cases": 118, "events": 5, "risk": 0.04},
            {"label": "Intermediate", "cases": 118, "events": 12, "risk": 0.10},
            {"label": "High", "cases": 118, "events": 39, "risk": 0.33},
        ],
        "right_panel_title": "Observed risk",
        "right_x_label": "Risk band",
        "right_bars": [
            {"label": "Low", "cases": 118, "events": 4, "risk": 0.03},
            {"label": "Intermediate", "cases": 118, "events": 11, "risk": 0.09},
            {"label": "High", "cases": 118, "events": 43, "risk": 0.36},
        ],
    },
    "decision_curve_binary": {
        "display_id": "Figure5",
        "template_id": "decision_curve_binary",
        "title": "Decision curve for the primary model",
        "caption": "Net benefit across clinically relevant thresholds.",
        "x_label": "Threshold probability",
        "y_label": "Net benefit",
        "decision_focus_window": {"xmin": 0.05, "xmax": 0.40, "ymin": -0.04, "ymax": 0.20},
        "reference_line": {"x": [0.05, 0.10, 0.20, 0.30, 0.40], "y": [0.0, 0.0, 0.0, 0.0, 0.0], "label": "Treat none"},
        "series": [
            {"label": "Primary model", "x": [0.05, 0.10, 0.20, 0.30, 0.40], "y": [0.18, 0.17, 0.14, 0.10, 0.07]},
            {"label": "Treat all", "x": [0.05, 0.10, 0.20, 0.30, 0.40], "y": [0.16, 0.13, 0.08, 0.03, -0.02]},
        ],
    },
    "shap_dependence_panel": {
        "display_id": "Figure27",
        "template_id": "shap_dependence_panel",
        "title": "SHAP dependence panel",
        "caption": "SHAP value varies nonlinearly with feature level and interaction strength.",
        "y_label": "SHAP value",
        "colorbar_label": "Interaction",
        "panels": [
            {
                "panel_id": "age",
                "panel_label": "A",
                "title": "Age",
                "x_label": "Age",
                "feature": "Age",
                "interaction_feature": "Tumor size",
                "points": _shap_dependence_points(),
            }
        ],
    },
    "shap_waterfall_local_explanation_panel": {
        "display_id": "Figure28",
        "template_id": "shap_waterfall_local_explanation_panel",
        "title": "Local SHAP waterfall explanation",
        "caption": "Patient-level contribution stack from baseline to final model output.",
        "x_label": "Model output",
        "panels": [
            {
                "panel_id": "case1",
                "panel_label": "A",
                "title": "Case 1",
                "case_label": "Patient 1",
                "baseline_value": 0.18,
                "predicted_value": 0.57,
                "contributions": [
                    {"feature": "Tumor size", "shap_value": 0.21, "feature_value_text": "large"},
                    {"feature": "Age", "shap_value": 0.11, "feature_value_text": "70 y"},
                    {"feature": "Albumin", "shap_value": -0.07, "feature_value_text": "normal"},
                    {"feature": "Knosp grade", "shap_value": 0.14, "feature_value_text": "III-IV"},
                ],
            }
        ],
    },
    "time_to_event_decision_curve": {
        "display_id": "Figure10",
        "template_id": "time_to_event_decision_curve",
        "title": "Time-to-event decision curve at 24 months",
        "caption": "Net benefit and treated fraction are reviewed together at the decision horizon.",
        "time_horizon_months": 24,
        "panel_a_title": "Net benefit",
        "panel_b_title": "Treated fraction",
        "x_label": "Threshold probability",
        "y_label": "Net benefit",
        "treated_fraction_y_label": "Patients above threshold (%)",
        "reference_line": {"x": [0.05, 0.10, 0.20, 0.30, 0.40], "y": [0, 0, 0, 0, 0], "label": "Treat none"},
        "series": [
            {"label": "Locked survival model", "x": [0.05, 0.10, 0.20, 0.30, 0.40], "y": [0.18, 0.17, 0.15, 0.12, 0.08]},
            {"label": "Treat all", "x": [0.05, 0.10, 0.20, 0.30, 0.40], "y": [0.15, 0.12, 0.08, 0.03, -0.02]},
        ],
        "treated_fraction_series": {"label": "Classified high risk", "x": [0.05, 0.10, 0.20, 0.30, 0.40], "y": [0.72, 0.58, 0.41, 0.27, 0.16]},
    },
    "time_to_event_multihorizon_calibration_panel": {
        "display_id": "Figure9",
        "template_id": "time_to_event_multihorizon_calibration_panel",
        "title": "Grouped survival calibration across horizons",
        "caption": "Observed risk tracks predicted risk across risk groups at 36 and 60 months.",
        "x_label": "Predicted risk",
        "y_label": "Observed risk",
        "panels": [
            {
                "panel_id": "h36",
                "panel_label": "A",
                "title": "36 months",
                "time_horizon_months": 36,
                "calibration_summary": [
                    {"group_label": "Q1", "group_order": 1, "n": 182, "events": 5, "predicted_risk": 0.03, "observed_risk": 0.04},
                    {"group_label": "Q2", "group_order": 2, "n": 171, "events": 10, "predicted_risk": 0.07, "observed_risk": 0.06},
                    {"group_label": "Q3", "group_order": 3, "n": 132, "events": 18, "predicted_risk": 0.14, "observed_risk": 0.16},
                    {"group_label": "Q4", "group_order": 4, "n": 88, "events": 24, "predicted_risk": 0.26, "observed_risk": 0.28},
                ],
            },
            {
                "panel_id": "h60",
                "panel_label": "B",
                "title": "60 months",
                "time_horizon_months": 60,
                "calibration_summary": [
                    {"group_label": "Q1", "group_order": 1, "n": 182, "events": 8, "predicted_risk": 0.05, "observed_risk": 0.06},
                    {"group_label": "Q2", "group_order": 2, "n": 171, "events": 17, "predicted_risk": 0.11, "observed_risk": 0.10},
                    {"group_label": "Q3", "group_order": 3, "n": 132, "events": 26, "predicted_risk": 0.21, "observed_risk": 0.22},
                    {"group_label": "Q4", "group_order": 4, "n": 88, "events": 31, "predicted_risk": 0.34, "observed_risk": 0.32},
                ],
            },
        ],
    },
    "generalizability_subgroup_composite_panel": {
        "display_id": "Figure14",
        "template_id": "generalizability_subgroup_composite_panel",
        "title": "Generalizability and subgroup discrimination composite",
        "caption": "External cohort discrimination and prespecified subgroup stability are displayed together.",
        "metric_family": "discrimination",
        "primary_label": "Locked model",
        "comparator_label": "Derivation cohort",
        "overview_panel_title": "External cohorts",
        "overview_x_label": "AUROC",
        "overview_rows": [
            {"cohort_id": "external_a", "cohort_label": "External A", "support_count": 184, "event_count": 29, "metric_value": 0.82, "comparator_metric_value": 0.79},
            {"cohort_id": "external_b", "cohort_label": "External B", "support_count": 163, "event_count": 21, "metric_value": 0.78, "comparator_metric_value": 0.76},
            {"cohort_id": "external_c", "cohort_label": "External C", "support_count": 141, "event_count": 19, "metric_value": 0.81, "comparator_metric_value": 0.77},
        ],
        "subgroup_panel_title": "Prespecified subgroups",
        "subgroup_x_label": "AUROC",
        "subgroup_reference_value": 0.8,
        "subgroup_rows": [
            {"subgroup_id": "age_ge_65", "subgroup_label": "Age >=65 years", "group_n": 201, "estimate": 0.82, "lower": 0.78, "upper": 0.86},
            {"subgroup_id": "female", "subgroup_label": "Female", "group_n": 173, "estimate": 0.79, "lower": 0.75, "upper": 0.83},
            {"subgroup_id": "stage_high", "subgroup_label": "High stage", "group_n": 128, "estimate": 0.81, "lower": 0.76, "upper": 0.87},
        ],
    },
    "tsne_scatter_grouped": _embedding_workflow_payload(
        display_id="Figure16",
        template_id="tsne_scatter_grouped",
        title="t-SNE embedding by subtype",
        caption="Neighborhood-preserving t-SNE projection computed from the shared high-dimensional feature matrix.",
        x_label="t-SNE 1",
        y_label="t-SNE 2",
        embedding_options={"seed": 1, "perplexity": 3, "theta": 0.2, "max_iter": 1500, "initial_dims": 8},
    ),
    "umap_scatter_grouped": _embedding_workflow_payload(
        display_id="Figure17",
        template_id="umap_scatter_grouped",
        title="UMAP embedding by subtype",
        caption="UMAP manifold projection computed from the shared high-dimensional feature matrix.",
        x_label="UMAP 1",
        y_label="UMAP 2",
        embedding_options={"seed": 2, "n_neighbors": 10, "min_dist": 0.30, "metric": "euclidean"},
    ),
}
