from __future__ import annotations

import math

from typing import Any


def _matrix_cells(rows: list[str], columns: list[str], values: list[list[float]]) -> list[dict[str, Any]]:
    return [
        {"x": column, "y": row, "value": values[row_index][column_index]}
        for row_index, row in enumerate(rows)
        for column_index, column in enumerate(columns)
    ]


def _embedding_feature_matrix() -> list[dict[str, Any]]:
    centers = (
        ("Myeloid", -1.8, 0.9, 0.45),
        ("Stromal", 1.6, 0.85, -0.28),
        ("T cell", 0.2, -1.45, 0.70),
        ("Tumor", -0.45, -0.55, -0.62),
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
    sample_index = 1
    for group_index, (group, center_x, center_y, center_z) in enumerate(centers, start=1):
        for point_index in range(90):
            angle = point_index * 2.399963229728653
            radius = 0.18 + 0.018 * (point_index % 13)
            local_x = math.cos(angle) * radius + math.sin(point_index * 0.31 + group_index) * 0.16
            local_y = math.sin(angle) * radius + math.cos(point_index * 0.27 + group_index) * 0.15
            local_z = math.sin(point_index * 0.17 + group_index) * 0.18
            latent_x = center_x + local_x
            latent_y = center_y + local_y
            latent_z = center_z + local_z
            values = (
                latent_x + 0.10 * local_z,
                latent_y + 0.08 * local_x,
                latent_z + 0.12 * local_y,
                0.55 * latent_x + 0.35 * latent_y + 0.20 * latent_z,
                latent_x * latent_y + 0.30 * local_z,
                (latent_x**2) * 0.22 - 0.40 * latent_y,
                (latent_y**2) * 0.25 + 0.35 * latent_z,
                latent_x - latent_y + 0.48 * latent_z,
            )
            rows.append(
                {
                    "sample_id": f"S{sample_index:03d}",
                    "group": group,
                    "features": {name: value for name, value in zip(feature_names, values, strict=True)},
                }
            )
            sample_index += 1
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
    values = [index / 179 for index in range(180)]
    return [
        {
            "feature_value": round(value, 4),
            "shap_value": round(0.75 * ((value - 0.45) ** 2) - 0.10 + 0.045 * math.sin(index * 1.7), 4),
            "interaction_value": round(value, 4),
            "subgroup": "High context" if value > 0.55 else "Low context",
        }
        for index, value in enumerate(values)
    ]


def _volcano_points() -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    labels_by_index = {12: "CXCL9", 44: "GZMB", 88: "IFNG", 153: "COL1A1", 211: "TGFB1", 266: "STAT1", 318: "VEGFA", 377: "MKI67"}
    for index in range(420):
        effect = 1.08 * math.sin(index * 0.37) + 0.55 * math.cos(index * 0.11)
        background = 0.18 + (abs(math.sin(index * 0.19)) ** 1.85) * 4.8
        tail_bonus = max(0.0, abs(effect) - 0.95) * 2.2
        label_bonus = 2.8 if index in labels_by_index else 0.0
        significance = background + tail_bonus + label_bonus
        status = "NS"
        if effect > 1.0 and significance > 1.3:
            status = "Up"
        elif effect < -1.0 and significance > 1.3:
            status = "Down"
        points.append(
            {
                "panel_id": "rna",
                "feature_label": labels_by_index.get(index, f"GENE{index + 1:03d}"),
                "effect_value": round(effect, 4),
                "significance_value": round(significance, 4),
                "regulation_class": status,
                "label_text": labels_by_index.get(index, ""),
            }
        )
    return points


def _shap_summary_rows() -> list[dict[str, Any]]:
    features = [f"Feature {letter}" for letter in "ABCDEFGH"]
    rows: list[dict[str, Any]] = []
    for feature_index, feature in enumerate(features, start=1):
        rows.append(
            {
                "feature": feature,
                "points": [
                    {
                        "shap_value": round((9 - feature_index) / 28 + math.sin(point_index * 1.3 + feature_index) * (0.08 + 0.02 * feature_index), 4),
                        "feature_value": round(((point_index * 17 + feature_index * 11) % 100) / 99, 4),
                    }
                    for point_index in range(55)
                ],
            }
        )
    return rows


PUBLICATION_R_DISPLAY_PAYLOADS: dict[str, dict[str, Any]] = {
    "kaplan_meier_grouped": {
        "display_id": "Figure6",
        "template_id": "kaplan_meier_grouped",
        "title": "Kaplan-Meier curve with risk table",
        "caption": "ctcluster v4-style No. at risk.",
        "x_label": "Time (months)",
        "y_label": "Survival probability",
        "groups": [
            {
                "label": "Low Risk",
                "times": [0, 12, 24, 36, 48, 60],
                "values": [1.0, 0.97, 0.92, 0.86, 0.80, 0.74],
            },
            {
                "label": "High Risk",
                "times": [0, 12, 24, 36, 48, 60],
                "values": [1.0, 0.93, 0.84, 0.74, 0.65, 0.56],
            },
        ],
        "risk_table_title": "No. at risk",
        "hide_risk_table_title": True,
        "risk_table": [
            {"label": "High Risk", "times": [0, 12, 24, 36, 48, 60], "at_risk": [168, 132, 101, 78, 49, 29]},
            {"label": "Low Risk", "times": [0, 12, 24, 36, 48, 60], "at_risk": [162, 145, 128, 96, 71, 55]},
        ],
        "annotation": "log-rank P = 0.012",
        "render_context": {
            "typography": {
                "base_size": 9.5,
                "title_size": 11.0,
                "subtitle_size": 8.2,
                "axis_title_size": 8.6,
                "tick_size": 7.6,
                "legend_size": 7.8
            },
            "layout_override": {"output_width_in": 4.8, "output_height_in": 4.8}
        },
    },
    "cumulative_incidence_grouped": {
        "display_id": "Figure7",
        "template_id": "cumulative_incidence_grouped",
        "title": "Cumulative incidence curve",
        "caption": "Grouped time-to-event incidence.",
        "x_label": "Time, months",
        "y_label": "Cumulative incidence",
        "groups": [
            {
                "label": "Low Risk",
                "times": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
                "values": [0.00, 0.04, 0.07, 0.11, 0.15, 0.18, 0.22, 0.25, 0.29, 0.32, 0.35, 0.38, 0.41],
            },
            {
                "label": "High Risk",
                "times": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
                "values": [0.00, 0.08, 0.13, 0.20, 0.27, 0.33, 0.39, 0.43, 0.47, 0.52, 0.56, 0.60, 0.63],
            },
        ],
    },
    "celltype_marker_dotplot_panel": {
        "display_id": "Figure24",
        "template_id": "celltype_marker_dotplot_panel",
        "title": "Cell-type marker dotplot",
        "caption": "Expression percent and average expression.",
        "x_label": "",
        "y_label": "",
        "effect_scale_label": "Avg exp",
        "size_scale_label": "Pct",
        "panel_order": [{"panel_id": "all", "panel_title": "Marker activity"}],
        "celltype_order": [{"label": item} for item in ["Fibroblast", "Myeloid", "Treg", "CD8 T", "Tumor"]],
        "marker_order": [{"label": item} for item in ["EPCAM", "CD8A", "FOXP3", "LYZ", "COL1A1"]],
        "points": [
            {"panel_id": "all", "celltype_label": cell, "marker_label": marker, "effect_value": value, "size_value": size}
            for cell, marker, value, size in [
                ("Tumor", "EPCAM", 2.00, 0.80), ("Tumor", "CD8A", -0.42, 0.08), ("Tumor", "FOXP3", -0.70, 0.02), ("Tumor", "LYZ", -0.56, 0.05), ("Tumor", "COL1A1", -0.84, 0.01),
                ("CD8 T", "EPCAM", -0.52, 0.04), ("CD8 T", "CD8A", 1.35, 0.72), ("CD8 T", "FOXP3", -0.35, 0.07), ("CD8 T", "LYZ", -0.58, 0.04), ("CD8 T", "COL1A1", -0.80, 0.02),
                ("Treg", "EPCAM", -0.82, 0.01), ("Treg", "CD8A", -0.38, 0.08), ("Treg", "FOXP3", 1.05, 0.62), ("Treg", "LYZ", -0.20, 0.10), ("Treg", "COL1A1", -0.72, 0.03),
                ("Myeloid", "EPCAM", -0.45, 0.04), ("Myeloid", "CD8A", -0.50, 0.05), ("Myeloid", "FOXP3", -0.20, 0.10), ("Myeloid", "LYZ", 1.55, 0.70), ("Myeloid", "COL1A1", -0.48, 0.05),
                ("Fibroblast", "EPCAM", -0.35, 0.06), ("Fibroblast", "CD8A", -0.82, 0.02), ("Fibroblast", "FOXP3", -0.50, 0.05), ("Fibroblast", "LYZ", -0.38, 0.08), ("Fibroblast", "COL1A1", 1.95, 0.76),
            ]
        ],
    },
    "coefficient_path_panel": {
        "display_id": "Figure13",
        "template_id": "coefficient_path_panel",
        "title": "Coefficient path panel",
        "caption": "Regularization path with selected lambda.",
        "x_label": "log(lambda)",
        "y_label": "Coefficient",
        "selected_log_lambda": -1.2,
        "path_points": [
            {"feature": feature, "log_lambda": round(log_lambda, 4), "coefficient": round(coefficient, 4)}
            for feature_index, feature in enumerate(["Feature A", "Feature B", "Feature C", "Feature D", "Feature E", "Feature F"], start=1)
            for step_index in range(80)
            for log_lambda in [-4.0 + step_index * 5.0 / 79.0]
            for coefficient in [
                (
                    math.sin(log_lambda + feature_index / 2.0)
                    * (7 - feature_index)
                    / 10.0
                    * max(0.0, (log_lambda + 4.0) / 5.0)
                )
            ]
        ],
    },
    "cnv_recurrence_summary_panel": {
        "display_id": "Figure21",
        "template_id": "cnv_recurrence_summary_panel",
        "title": "CNV recurrence summary",
        "caption": "Recurrent gains and losses.",
        "x_label": "",
        "y_label": "Sample frequency",
        "cnv_records": [
            {"chrom": chrom, "event": event, "freq": freq}
            for chrom, gain, loss in [
                ("chr1", 0.18, 0.05),
                ("chr2", 0.22, 0.09),
                ("chr3", 0.12, 0.16),
                ("chr4", 0.28, 0.07),
                ("chr5", 0.15, 0.11),
                ("chr6", 0.10, 0.20),
            ]
            for event, freq in [("Gain", gain), ("Loss", loss)]
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
        "title": "Genomic alteration consequence",
        "caption": "Functional or clinical effect summary.",
        "consequence_x_label": "Effect estimate",
        "reference_value": 1.0,
        "consequence_points": [
            {"gene_label": gene, "estimate": estimate, "lower": lower, "upper": upper, "q": q}
            for gene, estimate, lower, upper, q in [
                ("KRAS mut", 1.32, 1.05, 1.72, ".030"),
                ("BRAF mut", 1.78, 1.18, 2.65, ".008"),
                ("SMAD4 loss", 1.55, 1.10, 2.30, ".018"),
                ("PIK3CA mut", 0.82, 0.58, 1.16, ".24"),
            ]
        ],
    },
    "model_complexity_audit_panel": {
        "display_id": "model_audit",
        "template_id": "model_complexity_audit_panel",
        "title": "Model complexity audit",
        "caption": "Performance vs feature count.",
        "selected_feature_count": 35,
        "complexity_points": [
            {"features": features, "cv_auc": cv_auc, "external_auc": external_auc}
            for features, cv_auc, external_auc in [
                (5, 0.72, 0.70),
                (10, 0.79, 0.77),
                (20, 0.84, 0.82),
                (35, 0.86, 0.84),
                (55, 0.855, 0.825),
                (80, 0.845, 0.80),
            ]
        ],
    },
    "omics_volcano_panel": {
        "display_id": "Figure25",
        "template_id": "omics_volcano_panel",
        "title": "Volcano plot",
        "caption": "Differential-expression screening.",
        "x_label": "log2 fold-change",
        "y_label": "-log10 adjusted P",
        "effect_threshold": 1.0,
        "significance_threshold": 1.3,
        "points": _volcano_points(),
    },
    "pathway_enrichment_dotplot_panel": {
        "display_id": "Figure23",
        "template_id": "pathway_enrichment_dotplot_panel",
        "title": "Pathway enrichment dotplot",
        "caption": "NES colour, FDR size.",
        "x_label": "Gene ratio",
        "y_label": "Pathway",
        "effect_scale_label": "NES",
        "size_scale_label": "-log10 FDR",
        "pathway_order": [{"label": item} for item in ["EMT", "G2M checkpoint", "Angiogenesis", "IFN-gamma", "Oxidative phosphorylation", "T cell activation"]],
        "points": [
            {"panel_id": "all", "pathway_label": pathway, "x_value": x, "effect_value": effect, "size_value": size}
            for pathway, x, effect, size in [
                ("EMT", 0.21, 2.10, 3.00),
                ("G2M checkpoint", 0.18, 1.70, 2.22),
                ("Angiogenesis", 0.14, 1.35, 1.74),
                ("IFN-gamma", 0.12, -1.40, 1.52),
                ("Oxidative phosphorylation", 0.10, -1.65, 1.85),
                ("T cell activation", 0.08, -2.00, 2.40),
            ]
        ],
    },
    "pca_scatter_grouped": _embedding_workflow_payload(
        display_id="Figure15",
        template_id="pca_scatter_grouped",
        title="PCA embedding scatter",
        caption="Computed PCA view from the MAS feature-matrix workflow.",
        x_label="PC1",
        y_label="PC2",
        embedding_options={"center": True, "scale": True},
    ),
    "risk_layering_monotonic_bars": {
        "display_id": "Figure22",
        "template_id": "risk_layering_monotonic_bars",
        "title": "Monotonic risk layering",
        "caption": "Risk strata show a clinical gradient.",
        "x_label": "",
        "y_label": "Event rate",
        "risk_group_summaries": [
            {"label": "Q1 lowest", "event_rate": 0.09, "lower": 0.05, "upper": 0.15},
            {"label": "Q2", "event_rate": 0.16, "lower": 0.10, "upper": 0.24},
            {"label": "Q3", "event_rate": 0.28, "lower": 0.20, "upper": 0.37},
            {"label": "Q4 highest", "event_rate": 0.43, "lower": 0.33, "upper": 0.54},
        ],
    },
    "decision_curve_binary": {
        "display_id": "Figure5",
        "template_id": "decision_curve_binary",
        "title": "Decision curve",
        "caption": "Net benefit across clinical thresholds.",
        "x_label": "Threshold probability",
        "y_label": "Net benefit",
        "decision_focus_window": {"xmin": 0.05, "xmax": 0.80, "ymin": -0.02, "ymax": 0.20},
        "reference_line": {"x": [round(0.05 + i * 0.75 / 79, 4) for i in range(80)], "y": [0.0 for _ in range(80)], "label": "Treat none"},
        "series": [
            {
                "label": "MAS model",
                "x": [round(0.05 + i * 0.75 / 79, 4) for i in range(80)],
                "y": [round(0.18 - 0.13 * (0.05 + i * 0.75 / 79) + 0.025 * math.sin((0.05 + i * 0.75 / 79) * 9), 4) for i in range(80)],
            },
            {
                "label": "Clinical model",
                "x": [round(0.05 + i * 0.75 / 79, 4) for i in range(80)],
                "y": [round(0.12 - 0.11 * (0.05 + i * 0.75 / 79), 4) for i in range(80)],
            },
            {
                "label": "Treat all",
                "x": [round(0.05 + i * 0.75 / 79, 4) for i in range(80)],
                "y": [round(0.06 - 0.07 * (0.05 + i * 0.75 / 79), 4) for i in range(80)],
            },
        ],
    },
    "shap_dependence_panel": {
        "display_id": "Figure27",
        "template_id": "shap_dependence_panel",
        "title": "SHAP dependence panel",
        "caption": "Feature value vs model contribution.",
        "y_label": "SHAP value",
        "colorbar_label": "Interaction",
        "panels": [
            {
                "panel_id": "age",
                "panel_label": "A",
                "title": "Feature value",
                "x_label": "Feature value",
                "feature": "Feature value",
                "interaction_feature": "Context",
                "points": _shap_dependence_points(),
            }
        ],
    },
    "shap_summary_beeswarm": {
        "display_id": "Figure26",
        "template_id": "shap_summary_beeswarm",
        "title": "SHAP summary beeswarm",
        "caption": "Global feature contribution distribution.",
        "x_label": "SHAP value",
        "colorbar_label": "Feature value",
        "rows": _shap_summary_rows(),
    },
    "shap_waterfall_local_explanation_panel": {
        "display_id": "Figure28",
        "template_id": "shap_waterfall_local_explanation_panel",
        "title": "SHAP waterfall explanation",
        "caption": "Single-patient local contribution.",
        "y_label": "Prediction contribution",
        "panels": [
            {
                "panel_id": "case1",
                "panel_label": "A",
                "title": "Case 1",
                "case_label": "Patient 1",
                "baseline_value": 0.0,
                "predicted_value": 0.46,
                "contributions": [
                    {"feature": "Baseline", "shap_value": 0.22, "contribution_type": "base"},
                    {"feature": "CEA", "shap_value": 0.09},
                    {"feature": "N stage", "shap_value": 0.13},
                    {"feature": "Texture", "shap_value": -0.05},
                    {"feature": "KRAS", "shap_value": 0.07},
                ],
            }
        ],
    },
    "time_to_event_decision_curve": {
        "display_id": "Figure10",
        "template_id": "time_to_event_decision_curve",
        "title": "Decision curve",
        "caption": "Net benefit across clinical thresholds.",
        "time_horizon_months": 24,
        "panel_a_title": "Net benefit",
        "panel_b_title": "Treated fraction",
        "x_label": "Threshold probability",
        "y_label": "Net benefit",
        "treated_fraction_y_label": "Patients above threshold (%)",
        "decision_focus_window": {"xmin": 0.05, "xmax": 0.80, "ymin": -0.02, "ymax": 0.20},
        "reference_line": {"x": [round(0.05 + i * 0.75 / 79, 4) for i in range(80)], "y": [0.0 for _ in range(80)], "label": "Treat none"},
        "series": [
            {
                "label": "MAS model",
                "x": [round(0.05 + i * 0.75 / 79, 4) for i in range(80)],
                "y": [round(0.18 - 0.13 * (0.05 + i * 0.75 / 79) + 0.025 * math.sin((0.05 + i * 0.75 / 79) * 9), 4) for i in range(80)],
            },
            {
                "label": "Clinical model",
                "x": [round(0.05 + i * 0.75 / 79, 4) for i in range(80)],
                "y": [round(0.12 - 0.11 * (0.05 + i * 0.75 / 79), 4) for i in range(80)],
            },
            {
                "label": "Treat all",
                "x": [round(0.05 + i * 0.75 / 79, 4) for i in range(80)],
                "y": [round(0.06 - 0.07 * (0.05 + i * 0.75 / 79), 4) for i in range(80)],
            },
        ],
    },
    "time_to_event_multihorizon_calibration_panel": {
        "display_id": "Figure9",
        "template_id": "time_to_event_multihorizon_calibration_panel",
        "title": "Multi-horizon calibration",
        "caption": "Time-to-event predicted risk reliability.",
        "x_label": "Predicted risk",
        "y_label": "Observed risk",
        "panels": [
            {
                "panel_id": "h12",
                "title": "12 months",
                "calibration_summary": [
                    {"predicted_risk": 0.10, "observed_risk": 0.05},
                    {"predicted_risk": 0.26, "observed_risk": 0.27},
                    {"predicted_risk": 0.42, "observed_risk": 0.45},
                    {"predicted_risk": 0.58, "observed_risk": 0.56},
                    {"predicted_risk": 0.74, "observed_risk": 0.76},
                    {"predicted_risk": 0.90, "observed_risk": 0.93},
                ],
            },
            {
                "panel_id": "h36",
                "title": "36 months",
                "calibration_summary": [
                    {"predicted_risk": 0.10, "observed_risk": 0.07},
                    {"predicted_risk": 0.26, "observed_risk": 0.30},
                    {"predicted_risk": 0.42, "observed_risk": 0.46},
                    {"predicted_risk": 0.58, "observed_risk": 0.58},
                    {"predicted_risk": 0.74, "observed_risk": 0.80},
                    {"predicted_risk": 0.90, "observed_risk": 0.95},
                ],
            },
            {
                "panel_id": "h60",
                "title": "60 months",
                "calibration_summary": [
                    {"predicted_risk": 0.10, "observed_risk": 0.09},
                    {"predicted_risk": 0.26, "observed_risk": 0.32},
                    {"predicted_risk": 0.42, "observed_risk": 0.49},
                    {"predicted_risk": 0.58, "observed_risk": 0.60},
                    {"predicted_risk": 0.74, "observed_risk": 0.82},
                    {"predicted_risk": 0.90, "observed_risk": 0.97},
                ],
            },
        ],
    },
    "generalizability_subgroup_composite_panel": {
        "display_id": "Figure14",
        "template_id": "generalizability_subgroup_composite_panel",
        "title": "Generalizability composite",
        "caption": "Performance stability across cohorts and subgroups.",
        "metric_family": "discrimination",
        "primary_label": "Locked model",
        "comparator_label": "Derivation cohort",
        "overview_panel_title": "External cohorts",
        "overview_x_label": "AUROC",
        "overview_rows": [
            {"cohort_id": "internal", "cohort_label": "Internal", "metric_value": 0.86, "lower": 0.82, "upper": 0.90},
            {"cohort_id": "external_a", "cohort_label": "External A", "metric_value": 0.82, "lower": 0.76, "upper": 0.88},
            {"cohort_id": "external_b", "cohort_label": "External B", "metric_value": 0.79, "lower": 0.71, "upper": 0.86},
        ],
        "subgroup_panel_title": "Prespecified subgroups",
        "subgroup_x_label": "AUROC",
        "subgroup_reference_value": 0.8,
        "subgroup_rows": [
            {"subgroup_id": "age_lt_65", "subgroup_label": "Age <65", "estimate": 0.85, "lower": 0.79, "upper": 0.91},
            {"subgroup_id": "age_ge_65", "subgroup_label": "Age >=65", "estimate": 0.81, "lower": 0.75, "upper": 0.87},
            {"subgroup_id": "stage_ii", "subgroup_label": "Stage II", "estimate": 0.83, "lower": 0.77, "upper": 0.89},
            {"subgroup_id": "stage_iii", "subgroup_label": "Stage III", "estimate": 0.84, "lower": 0.78, "upper": 0.90},
        ],
    },
    "tsne_scatter_grouped": _embedding_workflow_payload(
        display_id="Figure16",
        template_id="tsne_scatter_grouped",
        title="t-SNE embedding scatter",
        caption="Computed t-SNE view from the MAS feature-matrix workflow.",
        x_label="t-SNE 1",
        y_label="t-SNE 2",
        embedding_options={"seed": 1, "perplexity": 3, "theta": 0.2, "max_iter": 1500, "initial_dims": 8},
    ),
    "umap_scatter_grouped": _embedding_workflow_payload(
        display_id="Figure17",
        template_id="umap_scatter_grouped",
        title="UMAP embedding scatter",
        caption="Computed UMAP view from the MAS feature-matrix workflow.",
        x_label="UMAP 1",
        y_label="UMAP 2",
        embedding_options={"seed": 2, "n_neighbors": 26, "min_dist": 0.46, "metric": "euclidean"},
    ),
}
