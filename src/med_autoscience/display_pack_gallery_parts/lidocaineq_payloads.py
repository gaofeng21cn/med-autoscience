from __future__ import annotations

import random

from typing import Any


def _distribution_values() -> list[dict[str, Any]]:
    responder = [-0.38, -0.24, -0.18, -0.10, -0.06, 0.02, 0.08, 0.14, 0.20, 0.27, 0.36, 0.44]
    non_responder = [0.18, 0.28, 0.36, 0.44, 0.52, 0.61, 0.70, 0.78, 0.86, 0.94, 1.04, 1.16]
    return [
        {"group": "Responder", "value": value}
        for value in responder
    ] + [
        {"group": "Non-responder", "value": value}
        for value in non_responder
    ]


def _correlation_points() -> list[dict[str, Any]]:
    rng = random.Random(5)
    points: list[dict[str, Any]] = []
    for index in range(120):
        group = "A" if index < 60 else "B"
        x = rng.gauss(0, 1)
        y = 0.58 * x + rng.gauss(0, 0.72) + (0.25 if group == "B" else 0.0)
        points.append({"x": round(x, 3), "y": round(y, 3), "group": group})
    return points


LIDOCAINEQ_R_DISPLAY_PAYLOADS: dict[str, dict[str, Any]] = {
    "distribution_violin_box": {
        "display_id": "Figure29",
        "template_id": "distribution_violin_box",
        "title": "Distribution comparison",
        "caption": "Violin + box + jitter.",
        "x_label": "",
        "y_label": "Signature score",
        "annotation": "Wilcoxon P = 0.004",
        "group_order": [{"label": "Responder"}, {"label": "Non-responder"}],
        "values": _distribution_values(),
    },
    "composition_stacked_bar": {
        "display_id": "Figure30",
        "template_id": "composition_stacked_bar",
        "title": "Stacked cohort composition",
        "caption": "Stable legend and percent scale.",
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
        "title": "Correlation scatter",
        "caption": "Regression line with statistic slot.",
        "x_label": "Feature score",
        "y_label": "Outcome-associated score",
        "annotation": "Spearman r = 0.53\nP < 0.001",
        "points": _correlation_points(),
    },
    "alluvial_transition": {
        "display_id": "Figure32",
        "template_id": "alluvial_transition",
        "title": "Subtype transition after treatment",
        "caption": "ggalluvial composition without manual left-packing.",
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
        "title": "Radar immune profile",
        "caption": "ggradar source-project template.",
        "axes": [{"label": item} for item in ["CD8", "CD4", "M1", "M2", "TLS", "Ki67"]],
        "profiles": [
            {"label": "Responder", "values": [0.68, 0.63, 0.58, 0.25, 0.66, 0.35]},
            {"label": "Non-responder", "values": [0.42, 0.51, 0.30, 0.65, 0.38, 0.69]},
        ],
    },
    "waterfall_response": {
        "display_id": "Figure34",
        "template_id": "waterfall_response",
        "title": "Risk-score waterfall",
        "caption": "Ranked individual predictions.",
        "x_label": "Patients ordered by score",
        "y_label": "Risk score",
        "bars": [
            {"sample": f"P{index:02d}", "value": value, "response": response}
            for index, (value, response) in enumerate(
                [
                    (-2.65, "Response"),
                    (-2.20, "Response"),
                    (-1.85, "Response"),
                    (-1.52, "Response"),
                    (-1.21, "Response"),
                    (-0.91, "Response"),
                    (-0.62, "Response"),
                    (-0.41, "Response"),
                    (-0.24, "Stable"),
                    (-0.08, "Stable"),
                    (0.06, "Stable"),
                    (0.18, "Stable"),
                    (0.31, "Stable"),
                    (0.46, "Stable"),
                    (0.61, "Progression"),
                    (0.77, "Progression"),
                    (0.96, "Progression"),
                    (1.14, "Progression"),
                    (1.33, "Progression"),
                    (1.58, "Progression"),
                ],
                start=1,
            )
        ],
    },
    "table1_baseline_characteristics": {
        "display_id": "Table1",
        "template_id": "table1_baseline_characteristics",
        "title": "Baseline characteristics table",
        "caption": "Table shell rendered as visual reference",
        "variable_header": "Variable",
        "overall_header": "Overall",
        "group_a_header": "LowRisk",
        "group_b_header": "HighRisk",
        "p_header": "P",
        "rows": [
            {"variable": "Age, median (IQR)", "overall": "61 (54-68)", "group_a": "59 (52-67)", "group_b": "63 (56-70)", "p_value": "0.041"},
            {"variable": "Male sex", "overall": "186 (58%)", "group_a": "78 (55%)", "group_b": "108 (60%)", "p_value": "0.42"},
            {"variable": "cT3-4", "overall": "248 (77%)", "group_a": "101 (71%)", "group_b": "147 (82%)", "p_value": "0.028"},
            {"variable": "N positive", "overall": "210 (65%)", "group_a": "84 (59%)", "group_b": "126 (70%)", "p_value": "0.037"},
            {"variable": "pCR", "overall": "72 (22%)", "group_a": "45 (32%)", "group_b": "27 (15%)", "p_value": "<0.001"},
        ],
        "render_context": {
            "layout_override": {"output_width_in": 5.7, "output_height_in": 3.2},
            "typography": {
                "title_size": 12.5,
                "subtitle_size": 9.5,
                "tick_size": 9.0
            },
        },
    },
}


__all__ = ["LIDOCAINEQ_R_DISPLAY_PAYLOADS"]
