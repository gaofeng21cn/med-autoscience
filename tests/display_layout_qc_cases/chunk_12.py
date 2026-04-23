from .shared import *

def test_run_display_layout_qc_passes_for_generalizability_subgroup_composite_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_generalizability_subgroup_composite_panel",
        layout_sidecar={
            "template_id": "generalizability_subgroup_composite_panel",
            "render_context": {"layout_override": {"show_figure_title": False}},
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.86, x1=0.34, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.58, y0=0.86, x1=0.84, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.82, x1=0.14, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.58, y0=0.82, x1=0.60, y1=0.85),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.20, y0=0.10, x1=0.32, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.67, y0=0.10, x1=0.76, y1=0.13),
                make_box("overview_row_label_1", "overview_row_label", x0=0.03, y0=0.63, x1=0.11, y1=0.67),
                make_box("overview_row_label_2", "overview_row_label", x0=0.03, y0=0.48, x1=0.11, y1=0.52),
                make_box("overview_row_label_3", "overview_row_label", x0=0.03, y0=0.33, x1=0.11, y1=0.37),
                make_box("overview_support_label_1", "support_label", x0=0.37, y0=0.63, x1=0.44, y1=0.67),
                make_box("overview_support_label_2", "support_label", x0=0.37, y0=0.48, x1=0.44, y1=0.52),
                make_box("overview_support_label_3", "support_label", x0=0.37, y0=0.33, x1=0.44, y1=0.37),
                make_box("overview_metric_marker_1", "overview_metric_marker", x0=0.28, y0=0.63, x1=0.29, y1=0.67),
                make_box("overview_metric_marker_2", "overview_metric_marker", x0=0.25, y0=0.48, x1=0.26, y1=0.52),
                make_box("overview_metric_marker_3", "overview_metric_marker", x0=0.27, y0=0.33, x1=0.28, y1=0.37),
                make_box("overview_comparator_marker_1", "overview_comparator_marker", x0=0.23, y0=0.63, x1=0.24, y1=0.67),
                make_box("overview_comparator_marker_2", "overview_comparator_marker", x0=0.23, y0=0.48, x1=0.24, y1=0.52),
                make_box("overview_comparator_marker_3", "overview_comparator_marker", x0=0.23, y0=0.33, x1=0.24, y1=0.37),
                make_box("subgroup_row_label_1", "subgroup_row_label", x0=0.46, y0=0.63, x1=0.56, y1=0.67),
                make_box("subgroup_row_label_2", "subgroup_row_label", x0=0.46, y0=0.48, x1=0.56, y1=0.52),
                make_box("subgroup_row_label_3", "subgroup_row_label", x0=0.46, y0=0.33, x1=0.57, y1=0.37),
                make_box("subgroup_ci_1", "ci_segment", x0=0.69, y0=0.645, x1=0.79, y1=0.655),
                make_box("subgroup_ci_2", "ci_segment", x0=0.66, y0=0.495, x1=0.75, y1=0.505),
                make_box("subgroup_ci_3", "ci_segment", x0=0.72, y0=0.345, x1=0.84, y1=0.355),
                make_box("subgroup_estimate_1", "estimate_marker", x0=0.74, y0=0.63, x1=0.75, y1=0.67),
                make_box("subgroup_estimate_2", "estimate_marker", x0=0.70, y0=0.48, x1=0.71, y1=0.52),
                make_box("subgroup_estimate_3", "estimate_marker", x0=0.77, y0=0.33, x1=0.78, y1=0.37),
            ],
            "panel_boxes": [
                make_box("overview_panel", "panel", x0=0.12, y0=0.18, x1=0.45, y1=0.80),
                make_box("subgroup_panel", "panel", x0=0.58, y0=0.18, x1=0.88, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.32, y0=0.02, x1=0.58, y1=0.08),
            ],
            "metrics": {
                "metric_family": "discrimination",
                "primary_label": "Locked model",
                "comparator_label": "Derivation cohort",
                "legend_title": "Model context",
                "legend_labels": ["Locked model", "Derivation cohort"],
                "overview_rows": [
                    {
                        "cohort_id": "external_a",
                        "cohort_label": "External A",
                        "support_count": 184,
                        "metric_value": 0.82,
                        "comparator_metric_value": 0.79,
                        "label_box_id": "overview_row_label_1",
                        "support_label_box_id": "overview_support_label_1",
                        "metric_marker_box_id": "overview_metric_marker_1",
                        "comparator_marker_box_id": "overview_comparator_marker_1",
                    },
                    {
                        "cohort_id": "external_b",
                        "cohort_label": "External B",
                        "support_count": 163,
                        "metric_value": 0.78,
                        "comparator_metric_value": 0.79,
                        "label_box_id": "overview_row_label_2",
                        "support_label_box_id": "overview_support_label_2",
                        "metric_marker_box_id": "overview_metric_marker_2",
                        "comparator_marker_box_id": "overview_comparator_marker_2",
                    },
                    {
                        "cohort_id": "temporal",
                        "cohort_label": "Temporal",
                        "support_count": 142,
                        "metric_value": 0.80,
                        "comparator_metric_value": 0.79,
                        "label_box_id": "overview_row_label_3",
                        "support_label_box_id": "overview_support_label_3",
                        "metric_marker_box_id": "overview_metric_marker_3",
                        "comparator_marker_box_id": "overview_comparator_marker_3",
                    },
                ],
                "subgroup_reference_value": 0.80,
                "subgroup_rows": [
                    {
                        "subgroup_id": "age_ge_65",
                        "subgroup_label": "Age ≥65 years",
                        "estimate": 0.82,
                        "lower": 0.78,
                        "upper": 0.86,
                        "label_box_id": "subgroup_row_label_1",
                        "estimate_box_id": "subgroup_estimate_1",
                        "ci_box_id": "subgroup_ci_1",
                    },
                    {
                        "subgroup_id": "female",
                        "subgroup_label": "Female",
                        "estimate": 0.79,
                        "lower": 0.75,
                        "upper": 0.83,
                        "label_box_id": "subgroup_row_label_2",
                        "estimate_box_id": "subgroup_estimate_2",
                        "ci_box_id": "subgroup_ci_2",
                    },
                    {
                        "subgroup_id": "high_risk",
                        "subgroup_label": "High-risk surgery",
                        "estimate": 0.84,
                        "lower": 0.79,
                        "upper": 0.89,
                        "label_box_id": "subgroup_row_label_3",
                        "estimate_box_id": "subgroup_estimate_3",
                        "ci_box_id": "subgroup_ci_3",
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_passes_for_compact_effect_estimate_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_compact_effect_estimate_panel",
        layout_sidecar={
            "template_id": "compact_effect_estimate_panel",
            "render_context": {"layout_override": {"show_figure_title": False}},
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.86, x1=0.31, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.56, y0=0.86, x1=0.75, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.76, x1=0.14, y1=0.79),
                make_box("panel_label_B", "panel_label", x0=0.56, y0=0.76, x1=0.58, y1=0.79),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.17, y0=0.10, x1=0.31, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.61, y0=0.10, x1=0.75, y1=0.13),
                make_box("row_label_A_1", "row_label", x0=0.03, y0=0.61, x1=0.11, y1=0.65),
                make_box("row_label_A_2", "row_label", x0=0.03, y0=0.46, x1=0.11, y1=0.50),
                make_box("estimate_A_1", "estimate_marker", x0=0.22, y0=0.61, x1=0.23, y1=0.65),
                make_box("estimate_A_2", "estimate_marker", x0=0.25, y0=0.46, x1=0.26, y1=0.50),
                make_box("ci_A_1", "ci_segment", x0=0.19, y0=0.625, x1=0.29, y1=0.635),
                make_box("ci_A_2", "ci_segment", x0=0.21, y0=0.475, x1=0.32, y1=0.485),
                make_box("row_label_B_1", "row_label", x0=0.47, y0=0.61, x1=0.55, y1=0.65),
                make_box("row_label_B_2", "row_label", x0=0.47, y0=0.46, x1=0.55, y1=0.50),
                make_box("estimate_B_1", "estimate_marker", x0=0.66, y0=0.61, x1=0.67, y1=0.65),
                make_box("estimate_B_2", "estimate_marker", x0=0.69, y0=0.46, x1=0.70, y1=0.50),
                make_box("ci_B_1", "ci_segment", x0=0.63, y0=0.625, x1=0.73, y1=0.635),
                make_box("ci_B_2", "ci_segment", x0=0.65, y0=0.475, x1=0.76, y1=0.485),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.12, y0=0.18, x1=0.40, y1=0.80),
                make_box("panel_B", "panel", x0=0.56, y0=0.18, x1=0.84, y1=0.80),
            ],
            "guide_boxes": [
                make_box("reference_line_A", "reference_line", x0=0.27, y0=0.18, x1=0.28, y1=0.80),
                make_box("reference_line_B", "reference_line", x0=0.71, y0=0.18, x1=0.72, y1=0.80),
            ],
            "metrics": {
                "reference_value": 1.0,
                "panels": [
                    {
                        "panel_id": "overall",
                        "panel_label": "A",
                        "title": "Overall cohort",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "reference_line_box_id": "reference_line_A",
                        "rows": [
                            {
                                "row_id": "age_ge_65",
                                "row_label": "Age ≥65 years",
                                "estimate": 1.18,
                                "lower": 1.04,
                                "upper": 1.34,
                                "label_box_id": "row_label_A_1",
                                "estimate_box_id": "estimate_A_1",
                                "ci_box_id": "ci_A_1",
                            },
                            {
                                "row_id": "female",
                                "row_label": "Female",
                                "estimate": 1.26,
                                "lower": 1.10,
                                "upper": 1.44,
                                "label_box_id": "row_label_A_2",
                                "estimate_box_id": "estimate_A_2",
                                "ci_box_id": "ci_A_2",
                            },
                        ],
                    },
                    {
                        "panel_id": "adjusted",
                        "panel_label": "B",
                        "title": "Covariate-adjusted model",
                        "panel_box_id": "panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "panel_title_box_id": "panel_title_B",
                        "x_axis_title_box_id": "x_axis_title_B",
                        "reference_line_box_id": "reference_line_B",
                        "rows": [
                            {
                                "row_id": "age_ge_65",
                                "row_label": "Age ≥65 years",
                                "estimate": 1.11,
                                "lower": 0.98,
                                "upper": 1.28,
                                "label_box_id": "row_label_B_1",
                                "estimate_box_id": "estimate_B_1",
                                "ci_box_id": "ci_B_1",
                            },
                            {
                                "row_id": "female",
                                "row_label": "Female",
                                "estimate": 1.22,
                                "lower": 1.05,
                                "upper": 1.40,
                                "label_box_id": "row_label_B_2",
                                "estimate_box_id": "estimate_B_2",
                                "ci_box_id": "ci_B_2",
                            },
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_compact_effect_estimate_panel_row_order_drifts() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_compact_effect_estimate_panel",
        layout_sidecar={
            "template_id": "compact_effect_estimate_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.86, x1=0.31, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.56, y0=0.86, x1=0.75, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.76, x1=0.14, y1=0.79),
                make_box("panel_label_B", "panel_label", x0=0.56, y0=0.76, x1=0.58, y1=0.79),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.17, y0=0.10, x1=0.31, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.61, y0=0.10, x1=0.75, y1=0.13),
                make_box("row_label_A_1", "row_label", x0=0.03, y0=0.61, x1=0.11, y1=0.65),
                make_box("row_label_A_2", "row_label", x0=0.03, y0=0.46, x1=0.11, y1=0.50),
                make_box("estimate_A_1", "estimate_marker", x0=0.22, y0=0.61, x1=0.23, y1=0.65),
                make_box("estimate_A_2", "estimate_marker", x0=0.25, y0=0.46, x1=0.26, y1=0.50),
                make_box("ci_A_1", "ci_segment", x0=0.19, y0=0.625, x1=0.29, y1=0.635),
                make_box("ci_A_2", "ci_segment", x0=0.21, y0=0.475, x1=0.32, y1=0.485),
                make_box("row_label_B_1", "row_label", x0=0.47, y0=0.61, x1=0.55, y1=0.65),
                make_box("row_label_B_2", "row_label", x0=0.47, y0=0.46, x1=0.55, y1=0.50),
                make_box("estimate_B_1", "estimate_marker", x0=0.66, y0=0.61, x1=0.67, y1=0.65),
                make_box("estimate_B_2", "estimate_marker", x0=0.69, y0=0.46, x1=0.70, y1=0.50),
                make_box("ci_B_1", "ci_segment", x0=0.63, y0=0.625, x1=0.73, y1=0.635),
                make_box("ci_B_2", "ci_segment", x0=0.65, y0=0.475, x1=0.76, y1=0.485),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.12, y0=0.18, x1=0.40, y1=0.80),
                make_box("panel_B", "panel", x0=0.56, y0=0.18, x1=0.84, y1=0.80),
            ],
            "guide_boxes": [
                make_box("reference_line_A", "reference_line", x0=0.27, y0=0.18, x1=0.28, y1=0.80),
                make_box("reference_line_B", "reference_line", x0=0.71, y0=0.18, x1=0.72, y1=0.80),
            ],
            "metrics": {
                "reference_value": 1.0,
                "panels": [
                    {
                        "panel_id": "overall",
                        "panel_label": "A",
                        "title": "Overall cohort",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "reference_line_box_id": "reference_line_A",
                        "rows": [
                            {
                                "row_id": "age_ge_65",
                                "row_label": "Age ≥65 years",
                                "estimate": 1.18,
                                "lower": 1.04,
                                "upper": 1.34,
                                "label_box_id": "row_label_A_1",
                                "estimate_box_id": "estimate_A_1",
                                "ci_box_id": "ci_A_1",
                            },
                            {
                                "row_id": "female",
                                "row_label": "Female",
                                "estimate": 1.26,
                                "lower": 1.10,
                                "upper": 1.44,
                                "label_box_id": "row_label_A_2",
                                "estimate_box_id": "estimate_A_2",
                                "ci_box_id": "ci_A_2",
                            },
                        ],
                    },
                    {
                        "panel_id": "adjusted",
                        "panel_label": "B",
                        "title": "Covariate-adjusted model",
                        "panel_box_id": "panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "panel_title_box_id": "panel_title_B",
                        "x_axis_title_box_id": "x_axis_title_B",
                        "reference_line_box_id": "reference_line_B",
                        "rows": [
                            {
                                "row_id": "female",
                                "row_label": "Female",
                                "estimate": 1.22,
                                "lower": 1.05,
                                "upper": 1.40,
                                "label_box_id": "row_label_B_1",
                                "estimate_box_id": "estimate_B_1",
                                "ci_box_id": "ci_B_1",
                            },
                            {
                                "row_id": "age_ge_65",
                                "row_label": "Age ≥65 years",
                                "estimate": 1.11,
                                "lower": 0.98,
                                "upper": 1.28,
                                "label_box_id": "row_label_B_2",
                                "estimate_box_id": "estimate_B_2",
                                "ci_box_id": "ci_B_2",
                            },
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "panel_row_order_mismatch" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_coefficient_path_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_coefficient_path_panel",
        layout_sidecar={
            "template_id": "coefficient_path_panel",
            "render_context": {"layout_override": {"show_figure_title": False}},
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.16, y0=0.86, x1=0.44, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.73, y0=0.86, x1=0.90, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.16, y0=0.77, x1=0.18, y1=0.80),
                make_box("panel_label_B", "panel_label", x0=0.73, y0=0.77, x1=0.75, y1=0.80),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.30, y0=0.12, x1=0.47, y1=0.15),
                make_box("step_legend_title", "legend_title", x0=0.22, y0=0.17, x1=0.31, y1=0.20),
                make_box("step_legend_unadjusted", "legend_label", x0=0.33, y0=0.17, x1=0.40, y1=0.20),
                make_box("step_legend_adjusted", "legend_label", x0=0.42, y0=0.17, x1=0.49, y1=0.20),
                make_box("step_legend_sensitivity", "legend_label", x0=0.51, y0=0.17, x1=0.60, y1=0.20),
                make_box("coefficient_row_age_ge_65", "coefficient_row_label", x0=0.03, y0=0.61, x1=0.15, y1=0.65),
                make_box("coefficient_row_female", "coefficient_row_label", x0=0.06, y0=0.46, x1=0.15, y1=0.50),
                make_box("marker_age_ge_65_unadjusted", "coefficient_marker", x0=0.31, y0=0.61, x1=0.32, y1=0.65),
                make_box("marker_age_ge_65_adjusted", "coefficient_marker", x0=0.35, y0=0.61, x1=0.36, y1=0.65),
                make_box("marker_age_ge_65_sensitivity", "coefficient_marker", x0=0.39, y0=0.61, x1=0.40, y1=0.65),
                make_box("marker_female_unadjusted", "coefficient_marker", x0=0.41, y0=0.46, x1=0.42, y1=0.50),
                make_box("marker_female_adjusted", "coefficient_marker", x0=0.44, y0=0.46, x1=0.45, y1=0.50),
                make_box("marker_female_sensitivity", "coefficient_marker", x0=0.48, y0=0.46, x1=0.49, y1=0.50),
                make_box("interval_age_ge_65_unadjusted", "coefficient_interval", x0=0.28, y0=0.625, x1=0.35, y1=0.635),
                make_box("interval_age_ge_65_adjusted", "coefficient_interval", x0=0.32, y0=0.625, x1=0.39, y1=0.635),
                make_box("interval_age_ge_65_sensitivity", "coefficient_interval", x0=0.36, y0=0.625, x1=0.43, y1=0.635),
                make_box("interval_female_unadjusted", "coefficient_interval", x0=0.38, y0=0.475, x1=0.45, y1=0.485),
                make_box("interval_female_adjusted", "coefficient_interval", x0=0.41, y0=0.475, x1=0.48, y1=0.485),
                make_box("interval_female_sensitivity", "coefficient_interval", x0=0.45, y0=0.475, x1=0.52, y1=0.485),
                make_box("summary_label_age", "summary_card_label", x0=0.75, y0=0.61, x1=0.84, y1=0.65),
                make_box("summary_value_age", "summary_card_value", x0=0.75, y0=0.56, x1=0.90, y1=0.60),
                make_box("summary_label_female", "summary_card_label", x0=0.75, y0=0.41, x1=0.84, y1=0.45),
                make_box("summary_value_female", "summary_card_value", x0=0.75, y0=0.36, x1=0.90, y1=0.40),
            ],
            "panel_boxes": [
                make_box("path_panel", "panel", x0=0.16, y0=0.22, x1=0.66, y1=0.80),
                make_box("summary_panel", "panel", x0=0.73, y0=0.22, x1=0.94, y1=0.80),
            ],
            "guide_boxes": [
                make_box("reference_line", "reference_line", x0=0.34, y0=0.22, x1=0.35, y1=0.80),
            ],
            "metrics": {
                "reference_value": 0.0,
                "path_panel": {
                    "panel_box_id": "path_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "step_legend_title_box_id": "step_legend_title",
                "steps": [
                    {
                        "step_id": "unadjusted",
                        "step_label": "Unadjusted",
                        "step_order": 1,
                        "legend_label_box_id": "step_legend_unadjusted",
                    },
                    {
                        "step_id": "adjusted",
                        "step_label": "Adjusted",
                        "step_order": 2,
                        "legend_label_box_id": "step_legend_adjusted",
                    },
                    {
                        "step_id": "sensitivity",
                        "step_label": "Sensitivity",
                        "step_order": 3,
                        "legend_label_box_id": "step_legend_sensitivity",
                    },
                ],
                "coefficient_rows": [
                    {
                        "row_id": "age_ge_65",
                        "row_label": "Age ≥65 years",
                        "label_box_id": "coefficient_row_age_ge_65",
                        "points": [
                            {
                                "step_id": "unadjusted",
                                "estimate": 0.18,
                                "lower": 0.04,
                                "upper": 0.32,
                                "marker_box_id": "marker_age_ge_65_unadjusted",
                                "interval_box_id": "interval_age_ge_65_unadjusted",
                            },
                            {
                                "step_id": "adjusted",
                                "estimate": 0.11,
                                "lower": -0.01,
                                "upper": 0.24,
                                "marker_box_id": "marker_age_ge_65_adjusted",
                                "interval_box_id": "interval_age_ge_65_adjusted",
                            },
                            {
                                "step_id": "sensitivity",
                                "estimate": 0.08,
                                "lower": -0.05,
                                "upper": 0.20,
                                "marker_box_id": "marker_age_ge_65_sensitivity",
                                "interval_box_id": "interval_age_ge_65_sensitivity",
                            },
                        ],
                    },
                    {
                        "row_id": "female",
                        "row_label": "Female",
                        "label_box_id": "coefficient_row_female",
                        "points": [
                            {
                                "step_id": "unadjusted",
                                "estimate": 0.34,
                                "lower": 0.19,
                                "upper": 0.49,
                                "marker_box_id": "marker_female_unadjusted",
                                "interval_box_id": "interval_female_unadjusted",
                            },
                            {
                                "step_id": "adjusted",
                                "estimate": 0.27,
                                "lower": 0.12,
                                "upper": 0.41,
                                "marker_box_id": "marker_female_adjusted",
                                "interval_box_id": "interval_female_adjusted",
                            },
                            {
                                "step_id": "sensitivity",
                                "estimate": 0.22,
                                "lower": 0.08,
                                "upper": 0.36,
                                "marker_box_id": "marker_female_sensitivity",
                                "interval_box_id": "interval_female_sensitivity",
                            },
                        ],
                    },
                ],
                "summary_cards": [
                    {
                        "card_id": "age",
                        "label": "Age ≥65 years",
                        "value": "Stable positive",
                        "label_box_id": "summary_label_age",
                        "value_box_id": "summary_value_age",
                    },
                    {
                        "card_id": "female",
                        "label": "Female",
                        "value": "Attenuated after adjustment",
                        "label_box_id": "summary_label_female",
                        "value_box_id": "summary_value_female",
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_coefficient_path_marker_leaves_path_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_coefficient_path_panel",
        layout_sidecar={
            "template_id": "coefficient_path_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.16, y0=0.86, x1=0.44, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.73, y0=0.86, x1=0.90, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.16, y0=0.77, x1=0.18, y1=0.80),
                make_box("panel_label_B", "panel_label", x0=0.73, y0=0.77, x1=0.75, y1=0.80),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.30, y0=0.12, x1=0.47, y1=0.15),
                make_box("step_legend_title", "legend_title", x0=0.22, y0=0.17, x1=0.31, y1=0.20),
                make_box("step_legend_unadjusted", "legend_label", x0=0.33, y0=0.17, x1=0.40, y1=0.20),
                make_box("step_legend_adjusted", "legend_label", x0=0.42, y0=0.17, x1=0.49, y1=0.20),
                make_box("coefficient_row_age_ge_65", "coefficient_row_label", x0=0.03, y0=0.61, x1=0.15, y1=0.65),
                make_box("marker_age_ge_65_unadjusted", "coefficient_marker", x0=0.68, y0=0.61, x1=0.70, y1=0.65),
                make_box("marker_age_ge_65_adjusted", "coefficient_marker", x0=0.35, y0=0.61, x1=0.36, y1=0.65),
                make_box("interval_age_ge_65_unadjusted", "coefficient_interval", x0=0.28, y0=0.625, x1=0.35, y1=0.635),
                make_box("interval_age_ge_65_adjusted", "coefficient_interval", x0=0.32, y0=0.625, x1=0.39, y1=0.635),
                make_box("summary_label_age", "summary_card_label", x0=0.75, y0=0.61, x1=0.84, y1=0.65),
                make_box("summary_value_age", "summary_card_value", x0=0.75, y0=0.56, x1=0.90, y1=0.60),
            ],
            "panel_boxes": [
                make_box("path_panel", "panel", x0=0.16, y0=0.22, x1=0.66, y1=0.80),
                make_box("summary_panel", "panel", x0=0.73, y0=0.22, x1=0.94, y1=0.80),
            ],
            "guide_boxes": [
                make_box("reference_line", "reference_line", x0=0.34, y0=0.22, x1=0.35, y1=0.80),
            ],
            "metrics": {
                "reference_value": 0.0,
                "path_panel": {
                    "panel_box_id": "path_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "step_legend_title_box_id": "step_legend_title",
                "steps": [
                    {
                        "step_id": "unadjusted",
                        "step_label": "Unadjusted",
                        "step_order": 1,
                        "legend_label_box_id": "step_legend_unadjusted",
                    },
                    {
                        "step_id": "adjusted",
                        "step_label": "Adjusted",
                        "step_order": 2,
                        "legend_label_box_id": "step_legend_adjusted",
                    },
                ],
                "coefficient_rows": [
                    {
                        "row_id": "age_ge_65",
                        "row_label": "Age ≥65 years",
                        "label_box_id": "coefficient_row_age_ge_65",
                        "points": [
                            {
                                "step_id": "unadjusted",
                                "estimate": 0.18,
                                "lower": 0.04,
                                "upper": 0.32,
                                "marker_box_id": "marker_age_ge_65_unadjusted",
                                "interval_box_id": "interval_age_ge_65_unadjusted",
                            },
                            {
                                "step_id": "adjusted",
                                "estimate": 0.11,
                                "lower": -0.01,
                                "upper": 0.24,
                                "marker_box_id": "marker_age_ge_65_adjusted",
                                "interval_box_id": "interval_age_ge_65_adjusted",
                            },
                        ],
                    }
                ],
                "summary_cards": [
                    {
                        "card_id": "age",
                        "label": "Age ≥65 years",
                        "value": "Stable positive",
                        "label_box_id": "summary_label_age",
                        "value_box_id": "summary_value_age",
                    }
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "coefficient_marker_outside_path_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_broader_heterogeneity_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_broader_heterogeneity_summary_panel",
        layout_sidecar={
            "template_id": "broader_heterogeneity_summary_panel",
            "render_context": {"layout_override": {"show_figure_title": False}},
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.18, y0=0.86, x1=0.44, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.73, y0=0.86, x1=0.91, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.18, y0=0.77, x1=0.20, y1=0.80),
                make_box("panel_label_B", "panel_label", x0=0.73, y0=0.77, x1=0.75, y1=0.80),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.31, y0=0.11, x1=0.47, y1=0.14),
                make_box("slice_legend_title", "legend_title", x0=0.21, y0=0.17, x1=0.30, y1=0.20),
                make_box("slice_legend_overall", "legend_label", x0=0.32, y0=0.17, x1=0.41, y1=0.20),
                make_box("slice_legend_subgroup", "legend_label", x0=0.43, y0=0.17, x1=0.53, y1=0.20),
                make_box("slice_legend_adjusted", "legend_label", x0=0.55, y0=0.17, x1=0.64, y1=0.20),
                make_box("row_label_age", "row_label", x0=0.04, y0=0.61, x1=0.16, y1=0.65),
                make_box("row_label_female", "row_label", x0=0.07, y0=0.46, x1=0.16, y1=0.50),
                make_box("estimate_age_overall", "estimate_marker", x0=0.30, y0=0.61, x1=0.31, y1=0.65),
                make_box("estimate_age_subgroup", "estimate_marker", x0=0.35, y0=0.58, x1=0.36, y1=0.62),
                make_box("estimate_age_adjusted", "estimate_marker", x0=0.39, y0=0.64, x1=0.40, y1=0.68),
                make_box("estimate_female_overall", "estimate_marker", x0=0.41, y0=0.46, x1=0.42, y1=0.50),
                make_box("estimate_female_subgroup", "estimate_marker", x0=0.45, y0=0.43, x1=0.46, y1=0.47),
                make_box("estimate_female_adjusted", "estimate_marker", x0=0.49, y0=0.49, x1=0.50, y1=0.53),
                make_box("ci_age_overall", "ci_segment", x0=0.27, y0=0.625, x1=0.34, y1=0.635),
                make_box("ci_age_subgroup", "ci_segment", x0=0.32, y0=0.595, x1=0.39, y1=0.605),
                make_box("ci_age_adjusted", "ci_segment", x0=0.36, y0=0.655, x1=0.43, y1=0.665),
                make_box("ci_female_overall", "ci_segment", x0=0.38, y0=0.475, x1=0.45, y1=0.485),
                make_box("ci_female_subgroup", "ci_segment", x0=0.42, y0=0.445, x1=0.49, y1=0.455),
                make_box("ci_female_adjusted", "ci_segment", x0=0.46, y0=0.505, x1=0.53, y1=0.515),
                make_box("verdict_age", "verdict_value", x0=0.76, y0=0.61, x1=0.86, y1=0.65),
                make_box("detail_age", "verdict_detail", x0=0.76, y0=0.56, x1=0.92, y1=0.60),
                make_box("verdict_female", "verdict_value", x0=0.76, y0=0.46, x1=0.88, y1=0.50),
                make_box("detail_female", "verdict_detail", x0=0.76, y0=0.41, x1=0.93, y1=0.45),
            ],
            "panel_boxes": [
                make_box("matrix_panel", "panel", x0=0.18, y0=0.22, x1=0.66, y1=0.80),
                make_box("summary_panel", "panel", x0=0.73, y0=0.22, x1=0.94, y1=0.80),
            ],
            "guide_boxes": [
                make_box("reference_line", "reference_line", x0=0.34, y0=0.22, x1=0.35, y1=0.80),
            ],
            "metrics": {
                "reference_value": 1.0,
                "matrix_panel": {
                    "panel_box_id": "matrix_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "slice_legend_title_box_id": "slice_legend_title",
                "slices": [
                    {
                        "slice_id": "overall",
                        "slice_label": "Overall cohort",
                        "slice_kind": "cohort",
                        "slice_order": 1,
                        "legend_label_box_id": "slice_legend_overall",
                    },
                    {
                        "slice_id": "subgroup",
                        "slice_label": "Prespecified subgroup",
                        "slice_kind": "subgroup",
                        "slice_order": 2,
                        "legend_label_box_id": "slice_legend_subgroup",
                    },
                    {
                        "slice_id": "adjusted",
                        "slice_label": "Adjusted model",
                        "slice_kind": "adjustment",
                        "slice_order": 3,
                        "legend_label_box_id": "slice_legend_adjusted",
                    },
                ],
                "effect_rows": [
                    {
                        "row_id": "age_ge_65",
                        "row_label": "Age ≥65 years",
                        "verdict": "stable",
                        "detail": "Positive direction stays preserved across every declared slice.",
                        "label_box_id": "row_label_age",
                        "verdict_box_id": "verdict_age",
                        "detail_box_id": "detail_age",
                        "slice_estimates": [
                            {
                                "slice_id": "overall",
                                "estimate": 1.18,
                                "lower": 1.04,
                                "upper": 1.34,
                                "marker_box_id": "estimate_age_overall",
                                "interval_box_id": "ci_age_overall",
                            },
                            {
                                "slice_id": "subgroup",
                                "estimate": 1.16,
                                "lower": 1.01,
                                "upper": 1.33,
                                "marker_box_id": "estimate_age_subgroup",
                                "interval_box_id": "ci_age_subgroup",
                            },
                            {
                                "slice_id": "adjusted",
                                "estimate": 1.11,
                                "lower": 0.98,
                                "upper": 1.28,
                                "marker_box_id": "estimate_age_adjusted",
                                "interval_box_id": "ci_age_adjusted",
                            },
                        ],
                    },
                    {
                        "row_id": "female",
                        "row_label": "Female",
                        "verdict": "attenuated",
                        "detail": "Magnitude shrinks after adjustment while retaining a positive point estimate.",
                        "label_box_id": "row_label_female",
                        "verdict_box_id": "verdict_female",
                        "detail_box_id": "detail_female",
                        "slice_estimates": [
                            {
                                "slice_id": "overall",
                                "estimate": 1.26,
                                "lower": 1.10,
                                "upper": 1.44,
                                "marker_box_id": "estimate_female_overall",
                                "interval_box_id": "ci_female_overall",
                            },
                            {
                                "slice_id": "subgroup",
                                "estimate": 1.22,
                                "lower": 1.05,
                                "upper": 1.41,
                                "marker_box_id": "estimate_female_subgroup",
                                "interval_box_id": "ci_female_subgroup",
                            },
                            {
                                "slice_id": "adjusted",
                                "estimate": 1.08,
                                "lower": 0.94,
                                "upper": 1.24,
                                "marker_box_id": "estimate_female_adjusted",
                                "interval_box_id": "ci_female_adjusted",
                            },
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_broader_heterogeneity_verdict_leaves_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_broader_heterogeneity_summary_panel",
        layout_sidecar={
            "template_id": "broader_heterogeneity_summary_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.18, y0=0.86, x1=0.44, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.73, y0=0.86, x1=0.91, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.18, y0=0.77, x1=0.20, y1=0.80),
                make_box("panel_label_B", "panel_label", x0=0.73, y0=0.77, x1=0.75, y1=0.80),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.31, y0=0.11, x1=0.47, y1=0.14),
                make_box("slice_legend_title", "legend_title", x0=0.21, y0=0.17, x1=0.30, y1=0.20),
                make_box("slice_legend_overall", "legend_label", x0=0.32, y0=0.17, x1=0.41, y1=0.20),
                make_box("slice_legend_adjusted", "legend_label", x0=0.43, y0=0.17, x1=0.52, y1=0.20),
                make_box("row_label_age", "row_label", x0=0.04, y0=0.61, x1=0.16, y1=0.65),
                make_box("estimate_age_overall", "estimate_marker", x0=0.30, y0=0.61, x1=0.31, y1=0.65),
                make_box("estimate_age_adjusted", "estimate_marker", x0=0.39, y0=0.64, x1=0.40, y1=0.68),
                make_box("ci_age_overall", "ci_segment", x0=0.27, y0=0.625, x1=0.34, y1=0.635),
                make_box("ci_age_adjusted", "ci_segment", x0=0.36, y0=0.655, x1=0.43, y1=0.665),
                make_box("verdict_age", "verdict_value", x0=0.95, y0=0.61, x1=0.99, y1=0.65),
                make_box("detail_age", "verdict_detail", x0=0.76, y0=0.56, x1=0.92, y1=0.60),
            ],
            "panel_boxes": [
                make_box("matrix_panel", "panel", x0=0.18, y0=0.22, x1=0.66, y1=0.80),
                make_box("summary_panel", "panel", x0=0.73, y0=0.22, x1=0.94, y1=0.80),
            ],
            "guide_boxes": [
                make_box("reference_line", "reference_line", x0=0.34, y0=0.22, x1=0.35, y1=0.80),
            ],
            "metrics": {
                "reference_value": 1.0,
                "matrix_panel": {
                    "panel_box_id": "matrix_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "slice_legend_title_box_id": "slice_legend_title",
                "slices": [
                    {
                        "slice_id": "overall",
                        "slice_label": "Overall cohort",
                        "slice_kind": "cohort",
                        "slice_order": 1,
                        "legend_label_box_id": "slice_legend_overall",
                    },
                    {
                        "slice_id": "adjusted",
                        "slice_label": "Adjusted model",
                        "slice_kind": "adjustment",
                        "slice_order": 2,
                        "legend_label_box_id": "slice_legend_adjusted",
                    },
                ],
                "effect_rows": [
                    {
                        "row_id": "age_ge_65",
                        "row_label": "Age ≥65 years",
                        "verdict": "stable",
                        "detail": "Positive direction stays preserved across every declared slice.",
                        "label_box_id": "row_label_age",
                        "verdict_box_id": "verdict_age",
                        "detail_box_id": "detail_age",
                        "slice_estimates": [
                            {
                                "slice_id": "overall",
                                "estimate": 1.18,
                                "lower": 1.04,
                                "upper": 1.34,
                                "marker_box_id": "estimate_age_overall",
                                "interval_box_id": "ci_age_overall",
                            },
                            {
                                "slice_id": "adjusted",
                                "estimate": 1.11,
                                "lower": 0.98,
                                "upper": 1.28,
                                "marker_box_id": "estimate_age_adjusted",
                                "interval_box_id": "ci_age_adjusted",
                            },
                        ],
                    }
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "verdict_box_outside_summary_panel" for issue in result["issues"])
