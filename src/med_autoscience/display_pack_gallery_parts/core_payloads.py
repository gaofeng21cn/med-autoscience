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
        "title": "Calibration curve for the primary model",
        "caption": "Observed versus predicted risk across locked probability bins.",
        "x_label": "Predicted probability",
        "y_label": "Observed event rate",
        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Ideal"},
        "series": [
            {
                "label": "Primary model",
                "x": [0.04, 0.11, 0.20, 0.34, 0.52],
                "y": [0.05, 0.10, 0.21, 0.32, 0.50],
                "annotation": "Slope = 0.97",
            },
            {
                "label": "Clinical baseline",
                "x": [0.06, 0.14, 0.24, 0.38, 0.55],
                "y": [0.04, 0.12, 0.18, 0.30, 0.43],
                "annotation": "Slope = 0.83",
            },
        ],
    },
    "time_dependent_roc_horizon": {
        "display_id": "Figure8",
        "template_id": "time_dependent_roc_horizon",
        "title": "Time-dependent ROC at 24 months",
        "caption": "Horizon-specific discrimination of the locked survival model.",
        "time_horizon_months": 24,
        "x_label": "1 - Specificity",
        "y_label": "Sensitivity",
        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Chance"},
        "series": [
            {
                "label": "24-month horizon",
                "x": [0.0, 0.08, 0.18, 0.32, 0.54, 0.78, 1.0],
                "y": [0.0, 0.48, 0.68, 0.82, 0.91, 0.97, 1.0],
                "annotation": "AUC = 0.81",
            },
            {
                "label": "36-month horizon",
                "x": [0.0, 0.11, 0.25, 0.42, 0.63, 0.84, 1.0],
                "y": [0.0, 0.43, 0.62, 0.77, 0.88, 0.95, 1.0],
                "annotation": "AUC = 0.78",
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
            {"label": "Age > 60 years", "estimate": 1.42, "lower": 1.11, "upper": 1.83},
            {"label": "Tumor size > 30 mm", "estimate": 1.89, "lower": 1.35, "upper": 2.62},
            {"label": "Albumin < 35 g/L", "estimate": 0.74, "lower": 0.58, "upper": 0.94},
            {"label": "High-risk imaging grade", "estimate": 1.68, "lower": 1.19, "upper": 2.36},
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
