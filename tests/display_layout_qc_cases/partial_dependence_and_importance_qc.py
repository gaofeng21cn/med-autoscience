from .shared import *

def test_run_display_layout_qc_fails_when_partial_dependence_subgroup_estimate_marker_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_partial_dependence_subgroup_comparison_panel",
        layout_sidecar={
            "template_id": "partial_dependence_subgroup_comparison_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.88, x1=0.28, y1=0.91),
                make_box("subgroup_panel_title_C", "subgroup_panel_title", x0=0.16, y0=0.42, x1=0.48, y1=0.45),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.14, y0=0.52, x1=0.26, y1=0.55),
                make_box("subgroup_x_axis_title_C", "subgroup_x_axis_title", x0=0.24, y0=0.08, x1=0.46, y1=0.11),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.58, x1=0.07, y1=0.84),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.82, x1=0.12, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.10, y0=0.38, x1=0.12, y1=0.41),
                make_box("reference_label_A", "pdp_reference_label", x0=0.17, y0=0.77, x1=0.25, y1=0.80),
                make_box("subgroup_row_label_1", "subgroup_row_label", x0=0.12, y0=0.30, x1=0.21, y1=0.33),
                make_box("legend_box", "legend_box", x0=0.62, y0=0.70, x1=0.90, y1=0.78),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.09, y0=0.56, x1=0.30, y1=0.83),
                make_box("panel_C", "subgroup_panel", x0=0.24, y0=0.16, x1=0.62, y1=0.36),
            ],
            "guide_boxes": [
                make_box("reference_line_A", "pdp_reference_line", x0=0.19, y0=0.56, x1=0.191, y1=0.83),
                make_box("subgroup_ci_segment_1", "subgroup_ci_segment", x0=0.33, y0=0.31, x1=0.47, y1=0.315),
                make_box("subgroup_estimate_marker_1", "subgroup_estimate_marker", x0=0.65, y0=0.298, x1=0.665, y1=0.318),
            ],
            "metrics": {
                "legend_labels": ["ICE curves", "PDP mean", "Subgroup interval"],
                "panels": [
                    {
                        "panel_id": "immune_high",
                        "panel_label": "A",
                        "subgroup_label": "Immune-high",
                        "title": "Immune-high subgroup",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_A",
                        "reference_line_box_id": "reference_line_A",
                        "reference_label_box_id": "reference_label_A",
                        "pdp_points": [{"x": 0.12, "y": 0.63}, {"x": 0.17, "y": 0.69}, {"x": 0.19, "y": 0.74}],
                        "ice_curves": [{"curve_id": "immune_high_case_1", "points": [{"x": 0.12, "y": 0.61}, {"x": 0.17, "y": 0.67}, {"x": 0.19, "y": 0.73}]}],
                    },
                ],
                "subgroup_panel": {
                    "panel_label": "C",
                    "title": "Subgroup-level absolute risk contrast",
                    "x_label": "Mean predicted risk difference",
                    "panel_box_id": "panel_C",
                    "rows": [
                        {
                            "row_id": "immune_high_row",
                            "panel_id": "immune_high",
                            "row_label": "Immune-high",
                            "estimate": 0.31,
                            "lower": 0.24,
                            "upper": 0.38,
                            "support_n": 142,
                            "label_box_id": "subgroup_row_label_1",
                            "ci_segment_box_id": "subgroup_ci_segment_1",
                            "estimate_marker_box_id": "subgroup_estimate_marker_1",
                        },
                    ],
                },
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "subgroup_estimate_marker_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_feature_response_support_domain_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_feature_response_support_domain_panel",
        layout_sidecar={
            "template_id": "feature_response_support_domain_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.87, x1=0.28, y1=0.90),
                make_box("panel_title_B", "panel_title", x0=0.49, y0=0.87, x1=0.67, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.28, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.54, y0=0.10, x1=0.69, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.34, x1=0.07, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.81, x1=0.14, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.49, y0=0.81, x1=0.51, y1=0.84),
                make_box("reference_label_A", "support_domain_reference_label", x0=0.20, y0=0.77, x1=0.28, y1=0.80),
                make_box("reference_label_B", "support_domain_reference_label", x0=0.58, y0=0.77, x1=0.68, y1=0.80),
                make_box("support_label_A_1", "support_label", x0=0.12, y0=0.20, x1=0.18, y1=0.23),
                make_box("support_label_A_2", "support_label", x0=0.18, y0=0.20, x1=0.24, y1=0.23),
                make_box("support_label_A_3", "support_label", x0=0.24, y0=0.20, x1=0.28, y1=0.23),
                make_box("support_label_A_4", "support_label", x0=0.28, y0=0.20, x1=0.33, y1=0.23),
                make_box("support_label_B_1", "support_label", x0=0.49, y0=0.20, x1=0.56, y1=0.23),
                make_box("support_label_B_2", "support_label", x0=0.56, y0=0.20, x1=0.61, y1=0.23),
                make_box("support_label_B_3", "support_label", x0=0.61, y0=0.20, x1=0.65, y1=0.23),
                make_box("support_label_B_4", "support_label", x0=0.65, y0=0.20, x1=0.72, y1=0.23),
                make_box("legend_box", "legend_box", x0=0.23, y0=0.02, x1=0.77, y1=0.08),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.11, y0=0.18, x1=0.34, y1=0.82),
                make_box("panel_B", "panel", x0=0.48, y0=0.18, x1=0.73, y1=0.82),
            ],
            "guide_boxes": [
                make_box("reference_line_A", "support_domain_reference_line", x0=0.22, y0=0.18, x1=0.221, y1=0.82),
                make_box("reference_line_B", "support_domain_reference_line", x0=0.60, y0=0.18, x1=0.601, y1=0.82),
                make_box("support_segment_A_1", "support_domain_segment", x0=0.12, y0=0.18, x1=0.18, y1=0.25),
                make_box("support_segment_A_2", "support_domain_segment", x0=0.18, y0=0.18, x1=0.24, y1=0.25),
                make_box("support_segment_A_3", "support_domain_segment", x0=0.24, y0=0.18, x1=0.29, y1=0.25),
                make_box("support_segment_A_4", "support_domain_segment", x0=0.29, y0=0.18, x1=0.33, y1=0.25),
                make_box("support_segment_B_1", "support_domain_segment", x0=0.49, y0=0.18, x1=0.56, y1=0.25),
                make_box("support_segment_B_2", "support_domain_segment", x0=0.56, y0=0.18, x1=0.61, y1=0.25),
                make_box("support_segment_B_3", "support_domain_segment", x0=0.61, y0=0.18, x1=0.66, y1=0.25),
                make_box("support_segment_B_4", "support_domain_segment", x0=0.66, y0=0.18, x1=0.72, y1=0.25),
            ],
            "metrics": {
                "legend_labels": [
                    "Response curve",
                    "Observed support",
                    "Subgroup support",
                    "Bin support",
                    "Extrapolation reminder",
                ],
                "panels": [
                    {
                        "panel_id": "age_support",
                        "panel_label": "A",
                        "title": "Age support domain",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_A",
                        "reference_line_box_id": "reference_line_A",
                        "reference_label_box_id": "reference_label_A",
                        "response_points": [
                            {"x": 0.13, "y": 0.55},
                            {"x": 0.17, "y": 0.60},
                            {"x": 0.22, "y": 0.66},
                            {"x": 0.27, "y": 0.72},
                            {"x": 0.31, "y": 0.77},
                        ],
                        "support_segments": [
                            {"segment_id": "age_observed", "segment_label": "Observed", "support_kind": "observed_support", "segment_box_id": "support_segment_A_1", "label_box_id": "support_label_A_1"},
                            {"segment_id": "age_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "segment_box_id": "support_segment_A_2", "label_box_id": "support_label_A_2"},
                            {"segment_id": "age_bin", "segment_label": "Bin", "support_kind": "bin_support", "segment_box_id": "support_segment_A_3", "label_box_id": "support_label_A_3"},
                            {"segment_id": "age_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "segment_box_id": "support_segment_A_4", "label_box_id": "support_label_A_4"},
                        ],
                    },
                    {
                        "panel_id": "albumin_support",
                        "panel_label": "B",
                        "title": "Albumin support domain",
                        "x_label": "Albumin (g/dL)",
                        "feature": "Albumin",
                        "reference_value": 3.8,
                        "reference_label": "Median albumin",
                        "panel_box_id": "panel_B",
                        "reference_line_box_id": "reference_line_B",
                        "reference_label_box_id": "reference_label_B",
                        "response_points": [
                            {"x": 0.50, "y": 0.76},
                            {"x": 0.55, "y": 0.68},
                            {"x": 0.60, "y": 0.60},
                            {"x": 0.65, "y": 0.51},
                            {"x": 0.69, "y": 0.45},
                            {"x": 0.71, "y": 0.41},
                        ],
                        "support_segments": [
                            {"segment_id": "alb_observed", "segment_label": "Observed", "support_kind": "observed_support", "segment_box_id": "support_segment_B_1", "label_box_id": "support_label_B_1"},
                            {"segment_id": "alb_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "segment_box_id": "support_segment_B_2", "label_box_id": "support_label_B_2"},
                            {"segment_id": "alb_bin", "segment_label": "Bin", "support_kind": "bin_support", "segment_box_id": "support_segment_B_3", "label_box_id": "support_label_B_3"},
                            {"segment_id": "alb_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "segment_box_id": "support_segment_B_4", "label_box_id": "support_label_B_4"},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_feature_response_support_segment_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_feature_response_support_domain_panel",
        layout_sidecar={
            "template_id": "feature_response_support_domain_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.87, x1=0.28, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.28, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.34, x1=0.07, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.81, x1=0.14, y1=0.84),
                make_box("reference_label_A", "support_domain_reference_label", x0=0.20, y0=0.77, x1=0.28, y1=0.80),
                make_box("support_label_A_1", "support_label", x0=0.12, y0=0.20, x1=0.18, y1=0.23),
                make_box("legend_box", "legend_box", x0=0.23, y0=0.02, x1=0.77, y1=0.08),
            ],
            "panel_boxes": [make_box("panel_A", "panel", x0=0.11, y0=0.18, x1=0.34, y1=0.82)],
            "guide_boxes": [
                make_box("reference_line_A", "support_domain_reference_line", x0=0.22, y0=0.18, x1=0.221, y1=0.82),
                make_box("support_segment_A_1", "support_domain_segment", x0=0.12, y0=0.18, x1=0.18, y1=0.25),
                make_box("support_segment_A_2", "support_domain_segment", x0=0.35, y0=0.18, x1=0.40, y1=0.25),
            ],
            "metrics": {
                "legend_labels": [
                    "Response curve",
                    "Observed support",
                    "Subgroup support",
                    "Bin support",
                    "Extrapolation reminder",
                ],
                "panels": [
                    {
                        "panel_id": "age_support",
                        "panel_label": "A",
                        "title": "Age support domain",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_A",
                        "reference_line_box_id": "reference_line_A",
                        "reference_label_box_id": "reference_label_A",
                        "response_points": [{"x": 0.13, "y": 0.55}, {"x": 0.22, "y": 0.66}, {"x": 0.31, "y": 0.77}],
                        "support_segments": [
                            {"segment_id": "age_observed", "segment_label": "Observed", "support_kind": "observed_support", "segment_box_id": "support_segment_A_1", "label_box_id": "support_label_A_1"},
                            {"segment_id": "age_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "segment_box_id": "support_segment_A_2", "label_box_id": "support_label_A_1"},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "support_segment_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_accumulated_local_effects_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_accumulated_local_effects_panel",
        layout_sidecar={
            "template_id": "accumulated_local_effects_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.87, x1=0.22, y1=0.90),
                make_box("panel_title_B", "panel_title", x0=0.47, y0=0.87, x1=0.58, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.28, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.52, y0=0.10, x1=0.67, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.32, x1=0.07, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.81, x1=0.14, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.47, y0=0.81, x1=0.49, y1=0.84),
                make_box("reference_label_A", "ale_reference_label", x0=0.21, y0=0.76, x1=0.28, y1=0.79),
                make_box("reference_label_B", "ale_reference_label", x0=0.56, y0=0.76, x1=0.66, y1=0.79),
                make_box("legend_box", "legend_box", x0=0.28, y0=0.03, x1=0.71, y1=0.08),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.11, y0=0.18, x1=0.34, y1=0.82),
                make_box("panel_B", "panel", x0=0.46, y0=0.18, x1=0.72, y1=0.82),
            ],
            "guide_boxes": [
                make_box("reference_line_A", "ale_reference_line", x0=0.24, y0=0.18, x1=0.241, y1=0.82),
                make_box("reference_line_B", "ale_reference_line", x0=0.59, y0=0.18, x1=0.591, y1=0.82),
                make_box("ale_bin_A_1", "local_effect_bin", x0=0.14, y0=0.46, x1=0.17, y1=0.52),
                make_box("ale_bin_A_2", "local_effect_bin", x0=0.19, y0=0.46, x1=0.22, y1=0.60),
                make_box("ale_bin_A_3", "local_effect_bin", x0=0.24, y0=0.46, x1=0.27, y1=0.57),
                make_box("ale_bin_A_4", "local_effect_bin", x0=0.29, y0=0.46, x1=0.32, y1=0.62),
                make_box("ale_bin_B_1", "local_effect_bin", x0=0.49, y0=0.44, x1=0.52, y1=0.50),
                make_box("ale_bin_B_2", "local_effect_bin", x0=0.55, y0=0.38, x1=0.58, y1=0.44),
                make_box("ale_bin_B_3", "local_effect_bin", x0=0.60, y0=0.33, x1=0.63, y1=0.38),
                make_box("ale_bin_B_4", "local_effect_bin", x0=0.66, y0=0.30, x1=0.69, y1=0.34),
            ],
            "metrics": {
                "legend_labels": ["Accumulated local effect", "Local effect per bin"],
                "panels": [
                    {
                        "panel_id": "age_ale",
                        "panel_label": "A",
                        "title": "Age",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_A",
                        "reference_line_box_id": "reference_line_A",
                        "reference_label_box_id": "reference_label_A",
                        "ale_points": [
                            {"x": 0.15, "y": 0.50},
                            {"x": 0.20, "y": 0.56},
                            {"x": 0.25, "y": 0.61},
                            {"x": 0.30, "y": 0.67},
                        ],
                        "local_effect_bins": [
                            {"bin_id": "age_bin_1", "bin_box_id": "ale_bin_A_1", "bin_center": 45.0, "local_effect": 0.02, "support_count": 84},
                            {"bin_id": "age_bin_2", "bin_box_id": "ale_bin_A_2", "bin_center": 55.0, "local_effect": 0.05, "support_count": 91},
                            {"bin_id": "age_bin_3", "bin_box_id": "ale_bin_A_3", "bin_center": 65.0, "local_effect": 0.04, "support_count": 88},
                            {"bin_id": "age_bin_4", "bin_box_id": "ale_bin_A_4", "bin_center": 75.0, "local_effect": 0.05, "support_count": 73},
                        ],
                    },
                    {
                        "panel_id": "albumin_ale",
                        "panel_label": "B",
                        "title": "Albumin",
                        "x_label": "Albumin (g/dL)",
                        "feature": "Albumin",
                        "reference_value": 3.8,
                        "reference_label": "Median albumin",
                        "panel_box_id": "panel_B",
                        "reference_line_box_id": "reference_line_B",
                        "reference_label_box_id": "reference_label_B",
                        "ale_points": [
                            {"x": 0.50, "y": 0.47},
                            {"x": 0.56, "y": 0.41},
                            {"x": 0.61, "y": 0.36},
                            {"x": 0.67, "y": 0.32},
                        ],
                        "local_effect_bins": [
                            {"bin_id": "alb_bin_1", "bin_box_id": "ale_bin_B_1", "bin_center": 3.0, "local_effect": -0.03, "support_count": 81},
                            {"bin_id": "alb_bin_2", "bin_box_id": "ale_bin_B_2", "bin_center": 3.4, "local_effect": -0.04, "support_count": 87},
                            {"bin_id": "alb_bin_3", "bin_box_id": "ale_bin_B_3", "bin_center": 3.8, "local_effect": -0.03, "support_count": 96},
                            {"bin_id": "alb_bin_4", "bin_box_id": "ale_bin_B_4", "bin_center": 4.2, "local_effect": -0.02, "support_count": 78},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_accumulated_local_effect_bin_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_accumulated_local_effects_panel",
        layout_sidecar={
            "template_id": "accumulated_local_effects_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.87, x1=0.22, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.28, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.32, x1=0.07, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.81, x1=0.14, y1=0.84),
                make_box("reference_label_A", "ale_reference_label", x0=0.21, y0=0.76, x1=0.28, y1=0.79),
                make_box("legend_box", "legend_box", x0=0.28, y0=0.03, x1=0.71, y1=0.08),
            ],
            "panel_boxes": [make_box("panel_A", "panel", x0=0.11, y0=0.18, x1=0.34, y1=0.82)],
            "guide_boxes": [
                make_box("reference_line_A", "ale_reference_line", x0=0.24, y0=0.18, x1=0.241, y1=0.82),
                make_box("ale_bin_A_1", "local_effect_bin", x0=0.14, y0=0.46, x1=0.17, y1=0.52),
                make_box("ale_bin_A_2", "local_effect_bin", x0=0.36, y0=0.46, x1=0.39, y1=0.60),
            ],
            "metrics": {
                "legend_labels": ["Accumulated local effect", "Local effect per bin"],
                "panels": [
                    {
                        "panel_id": "age_ale",
                        "panel_label": "A",
                        "title": "Age",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_A",
                        "reference_line_box_id": "reference_line_A",
                        "reference_label_box_id": "reference_label_A",
                        "ale_points": [{"x": 0.15, "y": 0.50}, {"x": 0.20, "y": 0.56}],
                        "local_effect_bins": [
                            {"bin_id": "age_bin_1", "bin_box_id": "ale_bin_A_1", "bin_center": 45.0, "local_effect": 0.02, "support_count": 84},
                            {"bin_id": "age_bin_2", "bin_box_id": "ale_bin_A_2", "bin_center": 55.0, "local_effect": 0.05, "support_count": 91},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "local_effect_bin_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_bar_importance() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_bar_importance",
        layout_sidecar={
            "template_id": "shap_bar_importance",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.36, y0=0.92, x1=0.64, y1=0.96),
                make_box("feature_label_1", "feature_label", x0=0.05, y0=0.22, x1=0.16, y1=0.27),
                make_box("feature_label_2", "feature_label", x0=0.05, y0=0.34, x1=0.19, y1=0.39),
                make_box("feature_label_3", "feature_label", x0=0.05, y0=0.46, x1=0.21, y1=0.51),
                make_box("feature_label_4", "feature_label", x0=0.05, y0=0.58, x1=0.20, y1=0.63),
                make_box("importance_bar_1", "importance_bar", x0=0.22, y0=0.22, x1=0.78, y1=0.27),
                make_box("importance_bar_2", "importance_bar", x0=0.22, y0=0.34, x1=0.67, y1=0.39),
                make_box("importance_bar_3", "importance_bar", x0=0.22, y0=0.46, x1=0.57, y1=0.51),
                make_box("importance_bar_4", "importance_bar", x0=0.22, y0=0.58, x1=0.49, y1=0.63),
                make_box("value_label_1", "value_label", x0=0.80, y0=0.22, x1=0.86, y1=0.27),
                make_box("value_label_2", "value_label", x0=0.69, y0=0.34, x1=0.75, y1=0.39),
                make_box("value_label_3", "value_label", x0=0.59, y0=0.46, x1=0.65, y1=0.51),
                make_box("value_label_4", "value_label", x0=0.51, y0=0.58, x1=0.57, y1=0.63),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.22, y0=0.18, x1=0.88, y1=0.82),
            ],
            "guide_boxes": [],
            "metrics": {
                "bars": [
                    {
                        "rank": 1,
                        "feature": "Age",
                        "importance_value": 0.184,
                        "bar_box_id": "importance_bar_1",
                        "feature_label_box_id": "feature_label_1",
                        "value_label_box_id": "value_label_1",
                    },
                    {
                        "rank": 2,
                        "feature": "Albumin",
                        "importance_value": 0.133,
                        "bar_box_id": "importance_bar_2",
                        "feature_label_box_id": "feature_label_2",
                        "value_label_box_id": "value_label_2",
                    },
                    {
                        "rank": 3,
                        "feature": "Tumor size",
                        "importance_value": 0.096,
                        "bar_box_id": "importance_bar_3",
                        "feature_label_box_id": "feature_label_3",
                        "value_label_box_id": "value_label_3",
                    },
                    {
                        "rank": 4,
                        "feature": "Platelet count",
                        "importance_value": 0.071,
                        "bar_box_id": "importance_bar_4",
                        "feature_label_box_id": "feature_label_4",
                        "value_label_box_id": "value_label_4",
                    },
                ]
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_shap_bar_importance_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_bar_importance",
        layout_sidecar={
            "template_id": "shap_bar_importance",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.36, y0=0.92, x1=0.64, y1=0.96),
                make_box("feature_label_1", "feature_label", x0=0.05, y0=0.22, x1=0.16, y1=0.27),
                make_box("importance_bar_1", "importance_bar", x0=0.22, y0=0.22, x1=0.92, y1=0.27),
                make_box("value_label_1", "value_label", x0=0.80, y0=0.22, x1=0.86, y1=0.27),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.22, y0=0.18, x1=0.88, y1=0.82),
            ],
            "guide_boxes": [],
            "metrics": {
                "bars": [
                    {
                        "rank": 1,
                        "feature": "Age",
                        "importance_value": 0.184,
                        "bar_box_id": "importance_bar_1",
                        "feature_label_box_id": "feature_label_1",
                        "value_label_box_id": "value_label_1",
                    }
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "importance_bar_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_signed_importance_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_signed_importance_panel",
        layout_sidecar={
            "template_id": "shap_signed_importance_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("negative_direction_label", "negative_direction_label", x0=0.24, y0=0.86, x1=0.38, y1=0.90),
                make_box("positive_direction_label", "positive_direction_label", x0=0.62, y0=0.86, x1=0.75, y1=0.90),
                make_box("x_axis_title", "x_axis_title", x0=0.36, y0=0.92, x1=0.64, y1=0.96),
                make_box("feature_label_1", "feature_label", x0=0.05, y0=0.22, x1=0.16, y1=0.27),
                make_box("feature_label_2", "feature_label", x0=0.05, y0=0.34, x1=0.19, y1=0.39),
                make_box("feature_label_3", "feature_label", x0=0.05, y0=0.46, x1=0.21, y1=0.51),
                make_box("feature_label_4", "feature_label", x0=0.05, y0=0.58, x1=0.20, y1=0.63),
                make_box("importance_bar_1", "importance_bar", x0=0.23, y0=0.22, x1=0.49, y1=0.27),
                make_box("importance_bar_2", "importance_bar", x0=0.50, y0=0.34, x1=0.73, y1=0.39),
                make_box("importance_bar_3", "importance_bar", x0=0.50, y0=0.46, x1=0.68, y1=0.51),
                make_box("importance_bar_4", "importance_bar", x0=0.35, y0=0.58, x1=0.49, y1=0.63),
                make_box("value_label_1", "value_label", x0=0.17, y0=0.22, x1=0.22, y1=0.27),
                make_box("value_label_2", "value_label", x0=0.75, y0=0.34, x1=0.81, y1=0.39),
                make_box("value_label_3", "value_label", x0=0.70, y0=0.46, x1=0.76, y1=0.51),
                make_box("value_label_4", "value_label", x0=0.29, y0=0.58, x1=0.34, y1=0.63),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.22, y0=0.18, x1=0.82, y1=0.82),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.495, y0=0.18, x1=0.505, y1=0.82),
            ],
            "metrics": {
                "bars": [
                    {
                        "rank": 1,
                        "feature": "Albumin",
                        "direction": "negative",
                        "signed_importance_value": -0.118,
                        "bar_box_id": "importance_bar_1",
                        "feature_label_box_id": "feature_label_1",
                        "value_label_box_id": "value_label_1",
                    },
                    {
                        "rank": 2,
                        "feature": "Age",
                        "direction": "positive",
                        "signed_importance_value": 0.104,
                        "bar_box_id": "importance_bar_2",
                        "feature_label_box_id": "feature_label_2",
                        "value_label_box_id": "value_label_2",
                    },
                    {
                        "rank": 3,
                        "feature": "Tumor size",
                        "direction": "positive",
                        "signed_importance_value": 0.081,
                        "bar_box_id": "importance_bar_3",
                        "feature_label_box_id": "feature_label_3",
                        "value_label_box_id": "value_label_3",
                    },
                    {
                        "rank": 4,
                        "feature": "Platelet count",
                        "direction": "negative",
                        "signed_importance_value": -0.064,
                        "bar_box_id": "importance_bar_4",
                        "feature_label_box_id": "feature_label_4",
                        "value_label_box_id": "value_label_4",
                    },
                ]
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_signed_importance_bar_crosses_wrong_side_of_zero_line() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_signed_importance_panel",
        layout_sidecar={
            "template_id": "shap_signed_importance_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("negative_direction_label", "negative_direction_label", x0=0.24, y0=0.86, x1=0.38, y1=0.90),
                make_box("positive_direction_label", "positive_direction_label", x0=0.62, y0=0.86, x1=0.75, y1=0.90),
                make_box("x_axis_title", "x_axis_title", x0=0.36, y0=0.92, x1=0.64, y1=0.96),
                make_box("feature_label_1", "feature_label", x0=0.05, y0=0.22, x1=0.16, y1=0.27),
                make_box("importance_bar_1", "importance_bar", x0=0.52, y0=0.22, x1=0.74, y1=0.27),
                make_box("value_label_1", "value_label", x0=0.76, y0=0.22, x1=0.82, y1=0.27),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.22, y0=0.18, x1=0.82, y1=0.82),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.495, y0=0.18, x1=0.505, y1=0.82),
            ],
            "metrics": {
                "bars": [
                    {
                        "rank": 1,
                        "feature": "Albumin",
                        "direction": "negative",
                        "signed_importance_value": -0.118,
                        "bar_box_id": "importance_bar_1",
                        "feature_label_box_id": "feature_label_1",
                        "value_label_box_id": "value_label_1",
                    }
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "signed_importance_bar_wrong_side_of_zero" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_multicohort_importance_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_multicohort_importance_panel",
        layout_sidecar={
            "template_id": "shap_multicohort_importance_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.16, y0=0.77, x1=0.19, y1=0.81),
                make_box("panel_label_B", "panel_label", x0=0.61, y0=0.77, x1=0.64, y1=0.81),
                make_box("panel_title_A", "panel_title", x0=0.16, y0=0.88, x1=0.34, y1=0.92),
                make_box("panel_title_B", "panel_title", x0=0.61, y0=0.88, x1=0.85, y1=0.92),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.20, y0=0.08, x1=0.39, y1=0.12),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.65, y0=0.08, x1=0.84, y1=0.12),
                make_box("feature_label_A_1", "feature_label", x0=0.05, y0=0.22, x1=0.13, y1=0.27),
                make_box("feature_label_A_2", "feature_label", x0=0.03, y0=0.34, x1=0.14, y1=0.39),
                make_box("feature_label_A_3", "feature_label", x0=0.00, y0=0.46, x1=0.14, y1=0.51),
                make_box("feature_label_A_4", "feature_label", x0=0.00, y0=0.58, x1=0.14, y1=0.63),
                make_box("feature_label_B_1", "feature_label", x0=0.50, y0=0.22, x1=0.58, y1=0.27),
                make_box("feature_label_B_2", "feature_label", x0=0.48, y0=0.34, x1=0.59, y1=0.39),
                make_box("feature_label_B_3", "feature_label", x0=0.45, y0=0.46, x1=0.59, y1=0.51),
                make_box("feature_label_B_4", "feature_label", x0=0.45, y0=0.58, x1=0.59, y1=0.63),
                make_box("importance_bar_A_1", "importance_bar", x0=0.15, y0=0.22, x1=0.41, y1=0.27),
                make_box("importance_bar_A_2", "importance_bar", x0=0.15, y0=0.34, x1=0.35, y1=0.39),
                make_box("importance_bar_A_3", "importance_bar", x0=0.15, y0=0.46, x1=0.29, y1=0.51),
                make_box("importance_bar_A_4", "importance_bar", x0=0.15, y0=0.58, x1=0.25, y1=0.63),
                make_box("importance_bar_B_1", "importance_bar", x0=0.60, y0=0.22, x1=0.84, y1=0.27),
                make_box("importance_bar_B_2", "importance_bar", x0=0.60, y0=0.34, x1=0.77, y1=0.39),
                make_box("importance_bar_B_3", "importance_bar", x0=0.60, y0=0.46, x1=0.72, y1=0.51),
                make_box("importance_bar_B_4", "importance_bar", x0=0.60, y0=0.58, x1=0.69, y1=0.63),
                make_box("value_label_A_1", "value_label", x0=0.42, y0=0.22, x1=0.47, y1=0.27),
                make_box("value_label_A_2", "value_label", x0=0.36, y0=0.34, x1=0.41, y1=0.39),
                make_box("value_label_A_3", "value_label", x0=0.30, y0=0.46, x1=0.35, y1=0.51),
                make_box("value_label_A_4", "value_label", x0=0.26, y0=0.58, x1=0.31, y1=0.63),
                make_box("value_label_B_1", "value_label", x0=0.85, y0=0.22, x1=0.90, y1=0.27),
                make_box("value_label_B_2", "value_label", x0=0.78, y0=0.34, x1=0.83, y1=0.39),
                make_box("value_label_B_3", "value_label", x0=0.73, y0=0.46, x1=0.78, y1=0.51),
                make_box("value_label_B_4", "value_label", x0=0.70, y0=0.58, x1=0.75, y1=0.63),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.15, y0=0.18, x1=0.45, y1=0.82),
                make_box("panel_B", "panel", x0=0.60, y0=0.18, x1=0.88, y1=0.82),
            ],
            "guide_boxes": [],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "derivation",
                        "panel_label": "A",
                        "title": "Derivation cohort",
                        "cohort_label": "Derivation",
                        "panel_box_id": "panel_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "bars": [
                            {"rank": 1, "feature": "Age", "importance_value": 0.184, "bar_box_id": "importance_bar_A_1", "feature_label_box_id": "feature_label_A_1", "value_label_box_id": "value_label_A_1"},
                            {"rank": 2, "feature": "Albumin", "importance_value": 0.133, "bar_box_id": "importance_bar_A_2", "feature_label_box_id": "feature_label_A_2", "value_label_box_id": "value_label_A_2"},
                            {"rank": 3, "feature": "Tumor size", "importance_value": 0.096, "bar_box_id": "importance_bar_A_3", "feature_label_box_id": "feature_label_A_3", "value_label_box_id": "value_label_A_3"},
                            {"rank": 4, "feature": "Platelet count", "importance_value": 0.071, "bar_box_id": "importance_bar_A_4", "feature_label_box_id": "feature_label_A_4", "value_label_box_id": "value_label_A_4"},
                        ],
                    },
                    {
                        "panel_id": "validation",
                        "panel_label": "B",
                        "title": "External validation cohort",
                        "cohort_label": "Validation",
                        "panel_box_id": "panel_B",
                        "x_axis_title_box_id": "x_axis_title_B",
                        "panel_label_box_id": "panel_label_B",
                        "panel_title_box_id": "panel_title_B",
                        "bars": [
                            {"rank": 1, "feature": "Age", "importance_value": 0.171, "bar_box_id": "importance_bar_B_1", "feature_label_box_id": "feature_label_B_1", "value_label_box_id": "value_label_B_1"},
                            {"rank": 2, "feature": "Albumin", "importance_value": 0.121, "bar_box_id": "importance_bar_B_2", "feature_label_box_id": "feature_label_B_2", "value_label_box_id": "value_label_B_2"},
                            {"rank": 3, "feature": "Tumor size", "importance_value": 0.089, "bar_box_id": "importance_bar_B_3", "feature_label_box_id": "feature_label_B_3", "value_label_box_id": "value_label_B_3"},
                            {"rank": 4, "feature": "Platelet count", "importance_value": 0.067, "bar_box_id": "importance_bar_B_4", "feature_label_box_id": "feature_label_B_4", "value_label_box_id": "value_label_B_4"},
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_multicohort_feature_order_drifts() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_multicohort_importance_panel",
        layout_sidecar={
            "template_id": "shap_multicohort_importance_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.16, y0=0.77, x1=0.19, y1=0.81),
                make_box("panel_label_B", "panel_label", x0=0.61, y0=0.77, x1=0.64, y1=0.81),
                make_box("panel_title_A", "panel_title", x0=0.16, y0=0.88, x1=0.34, y1=0.92),
                make_box("panel_title_B", "panel_title", x0=0.61, y0=0.88, x1=0.85, y1=0.92),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.20, y0=0.08, x1=0.39, y1=0.12),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.65, y0=0.08, x1=0.84, y1=0.12),
                make_box("feature_label_A_1", "feature_label", x0=0.05, y0=0.22, x1=0.13, y1=0.27),
                make_box("feature_label_A_2", "feature_label", x0=0.03, y0=0.34, x1=0.14, y1=0.39),
                make_box("feature_label_B_1", "feature_label", x0=0.50, y0=0.22, x1=0.58, y1=0.27),
                make_box("feature_label_B_2", "feature_label", x0=0.48, y0=0.34, x1=0.59, y1=0.39),
                make_box("importance_bar_A_1", "importance_bar", x0=0.15, y0=0.22, x1=0.41, y1=0.27),
                make_box("importance_bar_A_2", "importance_bar", x0=0.15, y0=0.34, x1=0.35, y1=0.39),
                make_box("importance_bar_B_1", "importance_bar", x0=0.60, y0=0.22, x1=0.84, y1=0.27),
                make_box("importance_bar_B_2", "importance_bar", x0=0.60, y0=0.34, x1=0.77, y1=0.39),
                make_box("value_label_A_1", "value_label", x0=0.42, y0=0.22, x1=0.47, y1=0.27),
                make_box("value_label_A_2", "value_label", x0=0.36, y0=0.34, x1=0.41, y1=0.39),
                make_box("value_label_B_1", "value_label", x0=0.85, y0=0.22, x1=0.90, y1=0.27),
                make_box("value_label_B_2", "value_label", x0=0.78, y0=0.34, x1=0.83, y1=0.39),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.15, y0=0.18, x1=0.45, y1=0.82),
                make_box("panel_B", "panel", x0=0.60, y0=0.18, x1=0.88, y1=0.82),
            ],
            "guide_boxes": [],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "derivation",
                        "panel_label": "A",
                        "title": "Derivation cohort",
                        "cohort_label": "Derivation",
                        "panel_box_id": "panel_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "bars": [
                            {"rank": 1, "feature": "Age", "importance_value": 0.184, "bar_box_id": "importance_bar_A_1", "feature_label_box_id": "feature_label_A_1", "value_label_box_id": "value_label_A_1"},
                            {"rank": 2, "feature": "Albumin", "importance_value": 0.133, "bar_box_id": "importance_bar_A_2", "feature_label_box_id": "feature_label_A_2", "value_label_box_id": "value_label_A_2"},
                        ],
                    },
                    {
                        "panel_id": "validation",
                        "panel_label": "B",
                        "title": "External validation cohort",
                        "cohort_label": "Validation",
                        "panel_box_id": "panel_B",
                        "x_axis_title_box_id": "x_axis_title_B",
                        "panel_label_box_id": "panel_label_B",
                        "panel_title_box_id": "panel_title_B",
                        "bars": [
                            {"rank": 1, "feature": "Albumin", "importance_value": 0.171, "bar_box_id": "importance_bar_B_1", "feature_label_box_id": "feature_label_B_1", "value_label_box_id": "value_label_B_1"},
                            {"rank": 2, "feature": "Age", "importance_value": 0.121, "bar_box_id": "importance_bar_B_2", "feature_label_box_id": "feature_label_B_2", "value_label_box_id": "value_label_B_2"},
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "multicohort_feature_order_mismatch" for issue in result["issues"])
