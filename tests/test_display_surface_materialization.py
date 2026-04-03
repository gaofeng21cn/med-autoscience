from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_display_surface_workspace(
    tmp_path: Path,
    *,
    include_evidence: bool = False,
    include_extended_evidence: bool = False,
) -> Path:
    paper_root = tmp_path / "paper"
    include_evidence = include_evidence or include_extended_evidence
    displays = [
        {
            "display_id": "Figure1",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "shell_path": "paper/figures/Figure1.shell.json",
        },
        {
            "display_id": "Table1",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "shell_path": "paper/tables/Table1.shell.json",
        },
    ]
    if include_evidence:
        displays.extend(
            [
                {
                    "display_id": "Figure2",
                    "display_kind": "figure",
                    "requirement_key": "roc_curve_binary",
                    "shell_path": "paper/figures/Figure2.shell.json",
                },
                {
                    "display_id": "Figure3",
                    "display_kind": "figure",
                    "requirement_key": "pr_curve_binary",
                    "shell_path": "paper/figures/Figure3.shell.json",
                },
                {
                    "display_id": "Figure4",
                    "display_kind": "figure",
                    "requirement_key": "calibration_curve_binary",
                    "shell_path": "paper/figures/Figure4.shell.json",
                },
                {
                    "display_id": "Figure5",
                    "display_kind": "figure",
                    "requirement_key": "decision_curve_binary",
                    "shell_path": "paper/figures/Figure5.shell.json",
                },
                {
                    "display_id": "Figure6",
                    "display_kind": "figure",
                    "requirement_key": "kaplan_meier_grouped",
                    "shell_path": "paper/figures/Figure6.shell.json",
                },
            ]
        )
    if include_extended_evidence:
        displays.extend(
            [
                {
                    "display_id": "Figure7",
                    "display_kind": "figure",
                    "requirement_key": "cumulative_incidence_grouped",
                    "shell_path": "paper/figures/Figure7.shell.json",
                },
                {
                    "display_id": "Figure8",
                    "display_kind": "figure",
                    "requirement_key": "umap_scatter_grouped",
                    "shell_path": "paper/figures/Figure8.shell.json",
                },
                {
                    "display_id": "Figure9",
                    "display_kind": "figure",
                    "requirement_key": "pca_scatter_grouped",
                    "shell_path": "paper/figures/Figure9.shell.json",
                },
                {
                    "display_id": "Figure10",
                    "display_kind": "figure",
                    "requirement_key": "heatmap_group_comparison",
                    "shell_path": "paper/figures/Figure10.shell.json",
                },
                {
                    "display_id": "Figure11",
                    "display_kind": "figure",
                    "requirement_key": "correlation_heatmap",
                    "shell_path": "paper/figures/Figure11.shell.json",
                },
                {
                    "display_id": "Figure12",
                    "display_kind": "figure",
                    "requirement_key": "forest_effect_main",
                    "shell_path": "paper/figures/Figure12.shell.json",
                },
                {
                    "display_id": "Figure13",
                    "display_kind": "figure",
                    "requirement_key": "shap_summary_beeswarm",
                    "shell_path": "paper/figures/Figure13.shell.json",
                },
            ]
        )
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": displays,
        },
    )
    dump_json(
        paper_root / "figures" / "Figure1.shell.json",
        {
            "schema_version": 1,
            "display_id": "Figure1",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
        },
    )
    dump_json(
        paper_root / "tables" / "Table1.shell.json",
        {
            "schema_version": 1,
            "display_id": "Table1",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
        },
    )
    if include_evidence:
        template_bindings = [
            (2, "roc_curve_binary"),
            (3, "pr_curve_binary"),
            (4, "calibration_curve_binary"),
            (5, "decision_curve_binary"),
            (6, "kaplan_meier_grouped"),
        ]
        if include_extended_evidence:
            template_bindings.extend(
                [
                    (7, "cumulative_incidence_grouped"),
                    (8, "umap_scatter_grouped"),
                    (9, "pca_scatter_grouped"),
                    (10, "heatmap_group_comparison"),
                    (11, "correlation_heatmap"),
                    (12, "forest_effect_main"),
                    (13, "shap_summary_beeswarm"),
                ]
            )
        for figure_index, template_id in template_bindings:
            dump_json(
                paper_root / "figures" / f"Figure{figure_index}.shell.json",
                {
                    "schema_version": 1,
                    "display_id": f"Figure{figure_index}",
                    "display_kind": "figure",
                    "requirement_key": template_id,
                },
            )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort flow",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Patients screened",
                    "n": 186,
                    "detail": "Consecutive surgical cases",
                },
                {
                    "step_id": "eligible",
                    "label": "Eligible after criteria review",
                    "n": 142,
                    "detail": "Complete preoperative variables",
                },
                {
                    "step_id": "included",
                    "label": "Included in analysis",
                    "n": 128,
                    "detail": "Primary cohort",
                },
            ],
        },
    )
    if include_evidence:
        dump_json(
            paper_root / "binary_prediction_curve_inputs.json",
            {
                "schema_version": 1,
                "input_schema_id": "binary_prediction_curve_inputs_v1",
                "displays": [
                    {
                        "display_id": "Figure2",
                        "template_id": "roc_curve_binary",
                        "title": "ROC curve for the primary model",
                        "caption": "Discrimination of the primary model across thresholds.",
                        "x_label": "1 - Specificity",
                        "y_label": "Sensitivity",
                        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Chance"},
                        "series": [
                            {
                                "label": "Primary model",
                                "x": [0.0, 0.08, 0.24, 1.0],
                                "y": [0.0, 0.66, 0.87, 1.0],
                                "annotation": "AUC = 0.84",
                            }
                        ],
                    },
                    {
                        "display_id": "Figure3",
                        "template_id": "pr_curve_binary",
                        "title": "Precision-recall curve for the primary model",
                        "caption": "Positive predictive yield across recall levels.",
                        "x_label": "Recall",
                        "y_label": "Precision",
                        "reference_line": {"x": [0.0, 1.0], "y": [0.42, 0.42], "label": "Prevalence"},
                        "series": [
                            {
                                "label": "Primary model",
                                "x": [0.0, 0.25, 0.55, 1.0],
                                "y": [1.0, 0.82, 0.69, 0.42],
                                "annotation": "AP = 0.73",
                            }
                        ],
                    },
                    {
                        "display_id": "Figure4",
                        "template_id": "calibration_curve_binary",
                        "title": "Calibration curve for the primary model",
                        "caption": "Observed versus predicted risk across bins.",
                        "x_label": "Predicted probability",
                        "y_label": "Observed event rate",
                        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Ideal"},
                        "series": [
                            {
                                "label": "Primary model",
                                "x": [0.05, 0.20, 0.40, 0.70, 0.90],
                                "y": [0.08, 0.22, 0.36, 0.68, 0.88],
                                "annotation": "Slope = 0.97",
                            }
                        ],
                    },
                    {
                        "display_id": "Figure5",
                        "template_id": "decision_curve_binary",
                        "title": "Decision curve for the primary model",
                        "caption": "Net benefit across clinically relevant thresholds.",
                        "x_label": "Threshold probability",
                        "y_label": "Net benefit",
                        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 0.0], "label": "Treat none"},
                        "series": [
                            {
                                "label": "Primary model",
                                "x": [0.05, 0.10, 0.20, 0.30, 0.40],
                                "y": [0.18, 0.17, 0.14, 0.10, 0.07],
                                "annotation": "Model",
                            },
                            {
                                "label": "Treat all",
                                "x": [0.05, 0.10, 0.20, 0.30, 0.40],
                                "y": [0.16, 0.13, 0.08, 0.03, -0.02],
                                "annotation": "Treat all",
                            },
                        ],
                    },
                ],
            },
        )
        dump_json(
            paper_root / "time_to_event_grouped_inputs.json",
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_grouped_inputs_v1",
                "displays": [
                    {
                        "display_id": "Figure6",
                        "template_id": "kaplan_meier_grouped",
                        "title": "Kaplan-Meier risk stratification",
                        "caption": "Time-to-event separation across prespecified risk groups.",
                        "x_label": "Months from surgery",
                        "y_label": "Survival probability",
                        "groups": [
                            {
                                "label": "Low risk",
                                "times": [0, 6, 12, 18, 24],
                                "values": [1.0, 0.96, 0.93, 0.90, 0.88],
                            },
                            {
                                "label": "High risk",
                                "times": [0, 6, 12, 18, 24],
                                "values": [1.0, 0.88, 0.77, 0.69, 0.62],
                            },
                        ],
                        "annotation": "Log-rank P < .001",
                    },
                    {
                        "display_id": "Figure7",
                        "template_id": "cumulative_incidence_grouped",
                        "title": "Cumulative incidence by risk group",
                        "caption": "Event accumulation across prespecified risk strata.",
                        "x_label": "Months from surgery",
                        "y_label": "Cumulative incidence",
                        "groups": [
                            {
                                "label": "Low risk",
                                "times": [0, 6, 12, 18, 24],
                                "values": [0.00, 0.04, 0.07, 0.09, 0.12],
                            },
                            {
                                "label": "High risk",
                                "times": [0, 6, 12, 18, 24],
                                "values": [0.00, 0.12, 0.23, 0.31, 0.38],
                            },
                        ],
                        "annotation": "Gray test P = .002",
                    }
                ],
            },
        )
        if include_extended_evidence:
            dump_json(
                paper_root / "embedding_grouped_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "embedding_grouped_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure8",
                            "template_id": "umap_scatter_grouped",
                            "title": "UMAP embedding by subtype",
                            "caption": "Two-dimensional manifold embedding with subtype labels.",
                            "x_label": "UMAP 1",
                            "y_label": "UMAP 2",
                            "points": [
                                {"x": -2.1, "y": 1.2, "group": "Subtype A"},
                                {"x": -1.7, "y": 1.0, "group": "Subtype A"},
                                {"x": 1.4, "y": -0.8, "group": "Subtype B"},
                                {"x": 1.8, "y": -1.1, "group": "Subtype B"},
                            ],
                        },
                        {
                            "display_id": "Figure9",
                            "template_id": "pca_scatter_grouped",
                            "title": "PCA embedding by subtype",
                            "caption": "Principal component separation across latent subgroups.",
                            "x_label": "PC1",
                            "y_label": "PC2",
                            "points": [
                                {"x": -1.2, "y": 0.6, "group": "Subtype A"},
                                {"x": -0.9, "y": 0.4, "group": "Subtype A"},
                                {"x": 0.8, "y": -0.5, "group": "Subtype B"},
                                {"x": 1.1, "y": -0.7, "group": "Subtype B"},
                            ],
                        },
                    ],
                },
            )
            dump_json(
                paper_root / "heatmap_group_comparison_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "heatmap_group_comparison_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure10",
                            "template_id": "heatmap_group_comparison",
                            "title": "Group comparison heatmap",
                            "caption": "Standardized feature contrast across prespecified groups.",
                            "x_label": "Group",
                            "y_label": "Feature",
                            "cells": [
                                {"x": "Low risk", "y": "Age", "value": -0.6},
                                {"x": "High risk", "y": "Age", "value": 0.7},
                                {"x": "Low risk", "y": "Tumor size", "value": -0.4},
                                {"x": "High risk", "y": "Tumor size", "value": 0.8},
                            ],
                        }
                    ],
                },
            )
            dump_json(
                paper_root / "correlation_heatmap_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "correlation_heatmap_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure11",
                            "template_id": "correlation_heatmap",
                            "title": "Correlation heatmap",
                            "caption": "Pairwise correlation structure across core predictors.",
                            "x_label": "Variable",
                            "y_label": "Variable",
                            "cells": [
                                {"x": "Age", "y": "Age", "value": 1.0},
                                {"x": "Age", "y": "Tumor size", "value": 0.34},
                                {"x": "Tumor size", "y": "Age", "value": 0.34},
                                {"x": "Tumor size", "y": "Tumor size", "value": 1.0},
                            ],
                        }
                    ],
                },
            )
            dump_json(
                paper_root / "forest_effect_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "forest_effect_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure12",
                            "template_id": "forest_effect_main",
                            "title": "Main-effect forest plot",
                            "caption": "Adjusted effect estimates for prespecified predictors.",
                            "x_label": "Odds ratio",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Age > 60 years", "estimate": 1.42, "lower": 1.11, "upper": 1.83},
                                {"label": "Tumor size > 30 mm", "estimate": 1.89, "lower": 1.35, "upper": 2.62},
                            ],
                        }
                    ],
                },
            )
            dump_json(
                paper_root / "shap_summary_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "shap_summary_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure13",
                            "template_id": "shap_summary_beeswarm",
                            "title": "SHAP summary beeswarm",
                            "caption": "Feature-level SHAP distribution ranked by mean absolute contribution.",
                            "x_label": "SHAP value",
                            "rows": [
                                {
                                    "feature": "Tumor size",
                                    "points": [
                                        {"shap_value": -0.42, "feature_value": 0.15},
                                        {"shap_value": 0.31, "feature_value": 0.83},
                                    ],
                                },
                                {
                                    "feature": "Age",
                                    "points": [
                                        {"shap_value": -0.18, "feature_value": 0.28},
                                        {"shap_value": 0.22, "feature_value": 0.74},
                                    ],
                                },
                            ],
                        }
                    ],
                },
            )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "Table1",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "overall", "label": "Overall (n=128)"},
                {"group_id": "low_risk", "label": "Low risk (n=73)"},
                {"group_id": "high_risk", "label": "High risk (n=55)"},
            ],
            "variables": [
                {
                    "variable_id": "age",
                    "label": "Age, median (IQR)",
                    "values": ["52 (44-61)", "49 (42-56)", "58 (50-66)"],
                },
                {
                    "variable_id": "female",
                    "label": "Female sex, n (%)",
                    "values": ["71 (55.5)", "45 (61.6)", "26 (47.3)"],
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    return paper_root


def _minimal_layout_sidecar_for_template(template_id: str) -> dict[str, object]:
    if template_id in {"roc_curve_binary", "pr_curve_binary", "calibration_curve_binary", "decision_curve_binary"}:
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.56, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.74, "y1": 0.86},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.80, "y0": 0.30, "x1": 0.96, "y1": 0.44},
            ],
            "metrics": {
                "series": [{"label": "Model", "x": [0.0, 0.5, 1.0], "y": [0.0, 0.7, 1.0]}],
                "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
            },
        }
    if template_id in {"kaplan_meier_grouped", "cumulative_incidence_grouped"}:
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.56, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.74, "y1": 0.86},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.80, "y0": 0.30, "x1": 0.96, "y1": 0.44},
            ],
            "metrics": {
                "groups": [{"label": "Low risk", "times": [0.0, 12.0], "values": [1.0, 0.78]}],
            },
        }
    if template_id in {"umap_scatter_grouped", "pca_scatter_grouped"}:
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.56, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.74, "y1": 0.86},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.80, "y0": 0.30, "x1": 0.96, "y1": 0.44},
            ],
            "metrics": {
                "points": [
                    {"x": 0.22, "y": 0.32, "group": "A"},
                    {"x": 0.44, "y": 0.54, "group": "B"},
                ]
            },
        }
    if template_id == "heatmap_group_comparison":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.28, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "heatmap_tile_region", "x0": 0.12, "y0": 0.16, "x1": 0.72, "y1": 0.84},
            ],
            "guide_boxes": [
                {"box_id": "colorbar", "box_type": "colorbar", "x0": 0.80, "y0": 0.22, "x1": 0.90, "y1": 0.80},
            ],
            "metrics": {},
        }
    if template_id == "correlation_heatmap":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.28, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "heatmap_tile_region", "x0": 0.12, "y0": 0.16, "x1": 0.72, "y1": 0.84},
            ],
            "guide_boxes": [
                {"box_id": "colorbar", "box_type": "colorbar", "x0": 0.80, "y0": 0.22, "x1": 0.90, "y1": 0.80},
            ],
            "metrics": {
                "matrix_cells": [
                    {"x": "A", "y": "A", "value": 1.0},
                    {"x": "A", "y": "B", "value": 0.42},
                    {"x": "B", "y": "A", "value": 0.42},
                    {"x": "B", "y": "B", "value": 1.0},
                ]
            },
        }
    if template_id == "forest_effect_main":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "reference_line", "box_type": "reference_line", "x0": 0.52, "y0": 0.18, "x1": 0.52, "y1": 0.86},
                {"box_id": "row_label_1", "box_type": "row_label", "x0": 0.02, "y0": 0.24, "x1": 0.20, "y1": 0.30},
                {"box_id": "estimate_marker_1", "box_type": "estimate_marker", "x0": 0.62, "y0": 0.25, "x1": 0.64, "y1": 0.29},
                {"box_id": "ci_segment_1", "box_type": "ci_segment", "x0": 0.56, "y0": 0.27, "x1": 0.74, "y1": 0.27},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.28, "y0": 0.16, "x1": 0.80, "y1": 0.88},
            ],
            "guide_boxes": [],
            "metrics": {
                "rows": [{"row_id": "1", "label": "Age >= 60", "lower": 0.90, "estimate": 1.05, "upper": 1.20}],
            },
        }
    if template_id == "shap_summary_beeswarm":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.56, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.62, "y1": 0.97},
                {"box_id": "feature_row_Age", "box_type": "feature_row", "x0": 0.14, "y0": 0.24, "x1": 0.76, "y1": 0.36},
                {"box_id": "feature_row_Ki-67", "box_type": "feature_row", "x0": 0.14, "y0": 0.40, "x1": 0.76, "y1": 0.52},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.14, "y0": 0.18, "x1": 0.76, "y1": 0.84},
            ],
            "guide_boxes": [
                {"box_id": "zero_line", "box_type": "zero_line", "x0": 0.48, "y0": 0.18, "x1": 0.48, "y1": 0.84},
                {"box_id": "colorbar", "box_type": "colorbar", "x0": 0.82, "y0": 0.22, "x1": 0.90, "y1": 0.80},
            ],
            "metrics": {
                "points": [
                    {"row_box_id": "feature_row_Age", "x": 0.42, "y": 0.28},
                    {"row_box_id": "feature_row_Ki-67", "x": 0.58, "y": 0.46},
                ]
            },
        }
    raise ValueError(f"unsupported template_id `{template_id}` in test layout sidecar helper")


def test_materialize_display_surface_generates_official_shell_outputs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.png").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.csv").exists()

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert figure_catalog["figures"][0]["template_id"] == "cohort_flow_figure"
    assert figure_catalog["figures"][0]["renderer_family"] == "python"
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert table_catalog["tables"][0]["table_id"] == "T1"
    assert table_catalog["tables"][0]["table_shell_id"] == "table1_baseline_characteristics"
    assert table_catalog["tables"][0]["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_registered_evidence_figures(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_evidence=True)
    render_calls: list[dict[str, str]] = []

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(
            {
                "template_id": template_id,
                "display_id": str(display_payload.get("display_id") or ""),
            }
        )

    monkeypatch.setattr(module, "_render_r_evidence_figure", fake_render_r_evidence_figure, raising=False)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F1", "F2", "F3", "F4", "F5", "F6"]
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.png").exists()
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.png").exists()
    assert (paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.pdf").exists()
    assert {item["template_id"] for item in render_calls} == {
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "kaplan_meier_grouped",
    }

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F2"]["template_id"] == "roc_curve_binary"
    assert figures_by_id["F2"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F2"]["input_schema_id"] == "binary_prediction_curve_inputs_v1"
    assert figures_by_id["F5"]["qc_profile"] == "publication_evidence_curve"
    assert figures_by_id["F6"]["template_id"] == "kaplan_meier_grouped"
    assert figures_by_id["F6"]["input_schema_id"] == "time_to_event_grouped_inputs_v1"


def test_materialize_display_surface_generates_full_registered_template_set(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    render_calls: list[tuple[str, str]] = []

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text(f"PNG:{template_id}", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append((template_id, str(display_payload.get("display_id") or "")))

    def fake_render_python_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text(f"PNG:{template_id}", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append((template_id, str(display_payload.get("display_id") or "")))

    monkeypatch.setattr(module, "_render_r_evidence_figure", fake_render_r_evidence_figure, raising=False)
    monkeypatch.setattr(module, "_render_python_evidence_figure", fake_render_python_evidence_figure, raising=False)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == [
        "F1",
        "F2",
        "F3",
        "F4",
        "F5",
        "F6",
        "F7",
        "F8",
        "F9",
        "F10",
        "F11",
        "F12",
        "F13",
    ]
    assert result["tables_materialized"] == ["T1"]
    assert (paper_root / "figures" / "generated" / "F7_cumulative_incidence_grouped.png").exists()
    assert (paper_root / "figures" / "generated" / "F8_umap_scatter_grouped.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F10_heatmap_group_comparison.png").exists()
    assert (paper_root / "figures" / "generated" / "F12_forest_effect_main.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F13_shap_summary_beeswarm.png").exists()
    assert {template_id for template_id, _ in render_calls} == {
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "kaplan_meier_grouped",
        "cumulative_incidence_grouped",
        "umap_scatter_grouped",
        "pca_scatter_grouped",
        "heatmap_group_comparison",
        "correlation_heatmap",
        "forest_effect_main",
        "shap_summary_beeswarm",
    }

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F7"]["template_id"] == "cumulative_incidence_grouped"
    assert figures_by_id["F8"]["input_schema_id"] == "embedding_grouped_inputs_v1"
    assert figures_by_id["F10"]["qc_profile"] == "publication_heatmap"
    assert figures_by_id["F12"]["qc_profile"] == "publication_forest_plot"
    assert figures_by_id["F13"]["renderer_family"] == "python"
    assert figures_by_id["F13"]["input_schema_id"] == "shap_summary_inputs_v1"


def test_materialize_display_surface_writes_layout_sidecar_and_real_qc_result(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text(f"PNG:{template_id}", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )

    def fake_render_python_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text(f"PNG:{template_id}", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )

    monkeypatch.setattr(module, "_render_r_evidence_figure", fake_render_r_evidence_figure, raising=False)
    monkeypatch.setattr(module, "_render_python_evidence_figure", fake_render_python_evidence_figure, raising=False)

    module.materialize_display_surface(paper_root=paper_root)

    layout_sidecar_path = paper_root / "figures" / "generated" / "F8_umap_scatter_grouped.layout.json"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = {item["figure_id"]: item["qc_result"] for item in figure_catalog["figures"]}["F8"]

    assert layout_sidecar_path.exists()
    assert qc_result["status"] == "pass"
    assert qc_result["engine_id"] == "display_layout_qc_v1"
    assert qc_result["qc_profile"] == "publication_embedding_scatter"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")
    assert qc_result["issues"] == []


def test_render_python_evidence_figure_emits_qc_passable_layout_sidecar(tmp_path: Path) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    qc_module = importlib.import_module("med_autoscience.display_layout_qc")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    spec = controller_module.display_registry.get_evidence_figure_spec("shap_summary_beeswarm")
    _, display_payload = controller_module._load_evidence_display_payload(
        paper_root=paper_root,
        spec=spec,
        display_id="Figure13",
    )
    output_png_path = tmp_path / "F13_shap_summary_beeswarm.png"
    output_pdf_path = tmp_path / "F13_shap_summary_beeswarm.pdf"
    layout_sidecar_path = tmp_path / "F13_shap_summary_beeswarm.layout.json"

    controller_module._render_python_evidence_figure(
        template_id=spec.template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    qc_result = qc_module.run_display_layout_qc(
        qc_profile=spec.layout_qc_profile,
        layout_sidecar=json.loads(layout_sidecar_path.read_text(encoding="utf-8")),
    )

    assert qc_result["status"] == "pass"
    assert qc_result["issues"] == []


def test_materialize_display_surface_rejects_incomplete_cohort_flow_input(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "steps": [],
        },
    )

    try:
        module.materialize_display_surface(paper_root=paper_root)
    except ValueError as exc:
        assert "cohort_flow.json" in str(exc)
    else:
        raise AssertionError("expected incomplete cohort flow input to fail")
