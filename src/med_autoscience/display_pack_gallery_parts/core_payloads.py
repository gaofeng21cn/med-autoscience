from __future__ import annotations

from typing import Any


CORE_R_DISPLAY_PAYLOADS: dict[str, dict[str, Any]] = {
    "roc_curve_binary": {
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
                "x": [0.0, 0.05, 0.12, 0.24, 0.42, 0.70, 1.0],
                "y": [0.0, 0.42, 0.63, 0.78, 0.88, 0.96, 1.0],
                "annotation": "AUC = 0.84",
            },
            {
                "label": "Clinical baseline",
                "x": [0.0, 0.10, 0.22, 0.39, 0.62, 0.82, 1.0],
                "y": [0.0, 0.31, 0.52, 0.69, 0.82, 0.91, 1.0],
                "annotation": "AUC = 0.76",
            },
        ],
    },
    "pr_curve_binary": {
        "display_id": "Figure3",
        "template_id": "pr_curve_binary",
        "title": "Precision-recall curve for the primary model",
        "caption": "Positive predictive yield across recall levels.",
        "x_label": "Recall",
        "y_label": "Precision",
        "reference_line": {"x": [0.0, 1.0], "y": [0.28, 0.28], "label": "Prevalence"},
        "series": [
            {
                "label": "Primary model",
                "x": [0.0, 0.18, 0.35, 0.58, 0.78, 1.0],
                "y": [1.0, 0.90, 0.79, 0.65, 0.49, 0.28],
                "annotation": "AP = 0.73",
            },
            {
                "label": "Clinical baseline",
                "x": [0.0, 0.22, 0.46, 0.68, 0.86, 1.0],
                "y": [0.92, 0.76, 0.58, 0.44, 0.34, 0.28],
                "annotation": "AP = 0.56",
            },
        ],
    },
    "calibration_curve_binary": {
        "display_id": "Figure4",
        "template_id": "calibration_curve_binary",
        "title": "Calibration curve",
        "caption": "Predicted probability vs observed risk.",
        "x_label": "Predicted risk",
        "y_label": "Observed risk",
        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Ideal"},
        "points": [
            {"predicted": 0.05, "observed": 0.03, "lower": 0.00, "upper": 0.13},
            {"predicted": 0.15, "observed": 0.16, "lower": 0.07, "upper": 0.23},
            {"predicted": 0.25, "observed": 0.28, "lower": 0.17, "upper": 0.33},
            {"predicted": 0.35, "observed": 0.34, "lower": 0.27, "upper": 0.43},
            {"predicted": 0.45, "observed": 0.47, "lower": 0.37, "upper": 0.53},
            {"predicted": 0.55, "observed": 0.55, "lower": 0.47, "upper": 0.63},
            {"predicted": 0.65, "observed": 0.69, "lower": 0.57, "upper": 0.73},
            {"predicted": 0.75, "observed": 0.73, "lower": 0.67, "upper": 0.83},
            {"predicted": 0.85, "observed": 0.86, "lower": 0.77, "upper": 0.93},
            {"predicted": 0.95, "observed": 0.98, "lower": 0.87, "upper": 1.00},
        ],
    },
    "time_dependent_roc_horizon": {
        "display_id": "Figure8",
        "template_id": "time_dependent_roc_horizon",
        "title": "Time-dependent ROC",
        "caption": "AUC by landmark horizon.",
        "x_label": "1 - Specificity",
        "y_label": "Sensitivity",
        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Chance"},
        "series": [
            {
                "label": "12 months",
                "x": [round(i / 69, 4) for i in range(70)],
                "y": [round(1 - (1 - i / 69) ** 2.1, 4) for i in range(70)],
                "annotation": "AUC = 0.80",
            },
            {
                "label": "36 months",
                "x": [round(i / 69, 4) for i in range(70)],
                "y": [round(1 - (1 - i / 69) ** 2.5, 4) for i in range(70)],
                "annotation": "AUC = 0.83",
            },
            {
                "label": "60 months",
                "x": [round(i / 69, 4) for i in range(70)],
                "y": [round(1 - (1 - i / 69) ** 2.0, 4) for i in range(70)],
                "annotation": "AUC = 0.79",
            },
        ],
    },
    "cumulative_incidence_grouped": {
        "display_id": "Figure7",
        "template_id": "cumulative_incidence_grouped",
        "title": "Cumulative incidence by risk group",
        "caption": "Event accumulation across prespecified risk strata.",
        "x_label": "Months from surgery",
        "y_label": "Cumulative incidence",
        "groups": [
            {"label": "Low risk", "times": [0, 6, 12, 18, 24], "values": [0.00, 0.04, 0.07, 0.09, 0.12]},
            {"label": "High risk", "times": [0, 6, 12, 18, 24], "values": [0.00, 0.12, 0.23, 0.31, 0.38]},
        ],
        "risk_table_title": "Number at risk",
        "risk_table": [
            {"label": "Low risk", "times": [0, 6, 12, 18, 24], "at_risk": [132, 126, 116, 102, 88]},
            {"label": "High risk", "times": [0, 6, 12, 18, 24], "at_risk": [124, 110, 91, 72, 54]},
        ],
        "annotation": "Gray test P = .002",
    },
    "forest_effect_main": {
        "display_id": "Figure12",
        "template_id": "forest_effect_main",
        "title": "Main-effect forest plot",
        "caption": "Adjusted effect estimates for prespecified predictors.",
        "x_label": "Adjusted odds ratio",
        "reference_value": 1.0,
        "rows": [
            {"label": "Age > 60 years", "estimate": 1.42, "lower": 1.11, "upper": 1.83, "p_value": "0.006"},
            {"label": "Tumor size > 30 mm", "estimate": 1.89, "lower": 1.35, "upper": 2.62, "p_value": "0.001"},
            {"label": "Albumin < 35 g/L", "estimate": 0.74, "lower": 0.58, "upper": 0.94, "p_value": "0.018"},
            {"label": "High-risk imaging grade", "estimate": 1.68, "lower": 1.19, "upper": 2.36, "p_value": "0.004"},
        ],
    },
    "heatmap_group_comparison": {
        "display_id": "Figure18",
        "template_id": "heatmap_group_comparison",
        "title": "Group comparison heatmap",
        "caption": "Standardized feature contrast across prespecified clinical groups.",
        "x_label": "Group",
        "y_label": "Feature",
        "metric_name": "Standardized difference",
        "row_order": [{"label": item} for item in ["Age", "Tumor size", "Inflammation", "Albumin", "Risk score"]],
        "column_order": [{"label": item} for item in ["Low risk", "Intermediate", "High risk"]],
        "cells": [
            {"x": group, "y": feature, "value": value}
            for feature, values in [
                ("Age", [-0.58, -0.10, 0.72]),
                ("Tumor size", [-0.42, 0.05, 0.81]),
                ("Inflammation", [-0.36, 0.12, 0.66]),
                ("Albumin", [0.44, 0.08, -0.62]),
                ("Risk score", [-0.74, 0.02, 0.88]),
            ]
            for group, value in zip(["Low risk", "Intermediate", "High risk"], values, strict=True)
        ],
    },
}


__all__ = ["CORE_R_DISPLAY_PAYLOADS"]
