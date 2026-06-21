from __future__ import annotations

from typing import Any


def _distribution_values() -> list[dict[str, Any]]:
    low = [-0.38, -0.24, -0.18, -0.10, -0.06, 0.02, 0.08, 0.14, 0.20, 0.27, 0.36, 0.44]
    high = [0.18, 0.28, 0.36, 0.44, 0.52, 0.61, 0.70, 0.78, 0.86, 0.94, 1.04, 1.16]
    return [
        {"group": "Low-risk", "value": value}
        for value in low
    ] + [
        {"group": "High-risk", "value": value}
        for value in high
    ]


def _correlation_points() -> list[dict[str, Any]]:
    x_values = [-1.8, -1.5, -1.2, -0.9, -0.6, -0.3, 0.0, 0.3, 0.6, 0.9, 1.2, 1.5]
    return [
        {
            "x": x,
            "y": round(0.54 * x + (0.18 if index % 3 == 0 else -0.08 if index % 3 == 1 else 0.04), 3),
            "group": "Derivation" if index < 6 else "Validation",
        }
        for index, x in enumerate(x_values)
    ]


LIDOCAINEQ_R_DISPLAY_PAYLOADS: dict[str, dict[str, Any]] = {
    "distribution_violin_box": {
        "display_id": "Figure29",
        "template_id": "distribution_violin_box",
        "title": "Signature score distribution by risk group",
        "caption": "Student-curated violin, box and jitter grammar adapted for MAS R/ggplot2 evidence rendering.",
        "x_label": "",
        "y_label": "Signature score",
        "annotation": "Wilcoxon P = 0.004",
        "group_order": [{"label": "Low-risk"}, {"label": "High-risk"}],
        "values": _distribution_values(),
    },
    "composition_stacked_bar": {
        "display_id": "Figure30",
        "template_id": "composition_stacked_bar",
        "title": "Response-class composition across cohorts",
        "caption": "Stacked proportions use the shared MAS clinical palette and compact bottom legend.",
        "x_label": "",
        "y_label": "Patients",
        "group_order": [{"label": item} for item in ["Training", "Internal", "External"]],
        "category_order": [{"label": item} for item in ["Class 1", "Class 2", "Class 3"]],
        "segments": [
            {"group": "Training", "category": "Class 1", "value": 0.35},
            {"group": "Training", "category": "Class 2", "value": 0.40},
            {"group": "Training", "category": "Class 3", "value": 0.25},
            {"group": "Internal", "category": "Class 1", "value": 0.31},
            {"group": "Internal", "category": "Class 2", "value": 0.43},
            {"group": "Internal", "category": "Class 3", "value": 0.26},
            {"group": "External", "category": "Class 1", "value": 0.28},
            {"group": "External", "category": "Class 2", "value": 0.36},
            {"group": "External", "category": "Class 3", "value": 0.36},
        ],
    },
    "correlation_scatter": {
        "display_id": "Figure31",
        "template_id": "correlation_scatter",
        "title": "Feature score association with outcome signal",
        "caption": "Correlation scatter seed with model trend and statistical annotation slot.",
        "x_label": "Feature score",
        "y_label": "Outcome-associated score",
        "annotation": "Spearman r = 0.53\nP < 0.001",
        "points": _correlation_points(),
    },
    "alluvial_transition": {
        "display_id": "Figure32",
        "template_id": "alluvial_transition",
        "title": "Subtype transition after treatment",
        "caption": "Alluvial state-transition grammar adapted from the student source project without extra runtime package installs.",
        "source_axis_label": "Baseline subtype",
        "target_axis_label": "Post-treatment state",
        "flows": [
            {"source": "CMS1", "target": "Immune", "value": 18},
            {"source": "CMS1", "target": "Stromal", "value": 9},
            {"source": "CMS2", "target": "Metabolic", "value": 22},
            {"source": "CMS2", "target": "Stromal", "value": 13},
            {"source": "CMS3", "target": "Metabolic", "value": 14},
            {"source": "CMS4", "target": "Immune", "value": 20},
        ],
    },
    "radar_profile": {
        "display_id": "Figure33",
        "template_id": "radar_profile",
        "title": "Immune profile radar overview",
        "caption": "Compact profile comparison seed for few-axis clinical or immune signatures.",
        "axes": [{"label": item} for item in ["CD8", "CD4", "M1", "M2", "TLS", "Ki67"]],
        "profiles": [
            {"label": "Responder", "values": [0.68, 0.63, 0.58, 0.25, 0.66, 0.35]},
            {"label": "Non-responder", "values": [0.42, 0.51, 0.30, 0.65, 0.38, 0.69]},
        ],
    },
    "waterfall_response": {
        "display_id": "Figure34",
        "template_id": "waterfall_response",
        "title": "Best response waterfall",
        "caption": "Ranked individual response plot with response-class palette and optional clinical threshold lines.",
        "x_label": "Patients ordered by response",
        "y_label": "Change from baseline (%)",
        "thresholds": [
            {"label": "Partial response", "value": -30},
            {"label": "Progression", "value": 20},
        ],
        "bars": [
            {"sample": f"P{index:02d}", "value": value, "response": response}
            for index, (value, response) in enumerate(
                [
                    (-72, "Response"),
                    (-61, "Response"),
                    (-55, "Response"),
                    (-48, "Response"),
                    (-39, "Response"),
                    (-31, "Response"),
                    (-24, "Stable"),
                    (-18, "Stable"),
                    (-11, "Stable"),
                    (-6, "Stable"),
                    (4, "Stable"),
                    (9, "Stable"),
                    (16, "Stable"),
                    (23, "Progression"),
                    (31, "Progression"),
                    (44, "Progression"),
                ],
                start=1,
            )
        ],
    },
    "table1_baseline_characteristics": {
        "display_id": "Table1",
        "template_id": "table1_baseline_characteristics",
        "title": "Baseline characteristics",
        "caption": "Aligned columns with restrained journal styling.",
        "overall_header": "Overall\n(n=256)",
        "group_a_header": "Low risk\n(n=128)",
        "group_b_header": "High risk\n(n=128)",
        "p_header": "P value",
        "rows": [
            {"variable": "Age, years", "overall": "63.4 (11.2)", "group_a": "61.8 (10.9)", "group_b": "65.0 (11.3)", "p_value": "0.021"},
            {"variable": "Female sex", "overall": "118 (46.1)", "group_a": "61 (47.7)", "group_b": "57 (44.5)", "p_value": "0.706"},
            {"variable": "Tumor size, mm", "overall": "32.6 (14.8)", "group_a": "27.9 (12.1)", "group_b": "37.3 (15.8)", "p_value": "<0.001"},
            {"variable": "Stage", "row_type": "section", "overall": "", "group_a": "", "group_b": "", "p_value": "0.018"},
            {"variable": "Stage", "level": "I-II", "overall": "142 (55.5)", "group_a": "82 (64.1)", "group_b": "60 (46.9)", "p_value": ""},
            {"variable": "Stage", "level": "III-IV", "overall": "114 (44.5)", "group_a": "46 (35.9)", "group_b": "68 (53.1)", "p_value": ""},
            {"variable": "Albumin, g/L", "overall": "38.1 (4.9)", "group_a": "39.4 (4.4)", "group_b": "36.8 (5.1)", "p_value": "<0.001"},
            {"variable": "Inflammation index", "overall": "2.1 (1.4-3.6)", "group_a": "1.7 (1.1-2.6)", "group_b": "2.8 (1.8-4.5)", "p_value": "<0.001"},
        ],
    },
}


__all__ = ["LIDOCAINEQ_R_DISPLAY_PAYLOADS"]
