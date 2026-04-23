from .shared import *

def test_run_display_layout_qc_passes_for_shap_dependence_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_dependence_panel",
        layout_sidecar={
            "template_id": "shap_dependence_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.14, y0=0.86, x1=0.30, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.46, y0=0.86, x1=0.64, y1=0.89),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.18, y0=0.10, x1=0.30, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.50, y0=0.10, x1=0.64, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.06, y0=0.30, x1=0.08, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.14, y0=0.80, x1=0.16, y1=0.83),
                make_box("panel_label_B", "panel_label", x0=0.46, y0=0.80, x1=0.48, y1=0.83),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.12, y0=0.18, x1=0.34, y1=0.82),
                make_box("panel_B", "panel", x0=0.44, y0=0.18, x1=0.68, y1=0.82),
            ],
            "guide_boxes": [
                make_box("zero_line_A", "zero_line", x0=0.12, y0=0.48, x1=0.34, y1=0.49),
                make_box("zero_line_B", "zero_line", x0=0.44, y0=0.48, x1=0.68, y1=0.49),
                make_box("colorbar", "colorbar", x0=0.78, y0=0.22, x1=0.84, y1=0.80),
            ],
            "metrics": {
                "colorbar_label": "Interaction feature value",
                "panels": [
                    {
                        "panel_id": "age_panel",
                        "panel_label": "A",
                        "title": "Age",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "interaction_feature": "Albumin",
                        "points": [
                            {"feature_value": 38.0, "shap_value": -0.22, "interaction_value": 3.1, "x": 0.18, "y": 0.34},
                            {"feature_value": 55.0, "shap_value": 0.04, "interaction_value": 4.2, "x": 0.24, "y": 0.52},
                            {"feature_value": 71.0, "shap_value": 0.31, "interaction_value": 4.8, "x": 0.30, "y": 0.70},
                        ],
                    },
                    {
                        "panel_id": "platelet_panel",
                        "panel_label": "B",
                        "title": "Platelet count",
                        "x_label": "Platelets (10^9/L)",
                        "feature": "Platelet count",
                        "interaction_feature": "Age",
                        "points": [
                            {"feature_value": 85.0, "shap_value": 0.28, "interaction_value": 72.0, "x": 0.50, "y": 0.68},
                            {"feature_value": 142.0, "shap_value": 0.02, "interaction_value": 59.0, "x": 0.58, "y": 0.52},
                            {"feature_value": 210.0, "shap_value": -0.19, "interaction_value": 44.0, "x": 0.64, "y": 0.32},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_shap_dependence_point_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_dependence_panel",
        layout_sidecar={
            "template_id": "shap_dependence_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.14, y0=0.86, x1=0.30, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.46, y0=0.86, x1=0.64, y1=0.89),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.18, y0=0.10, x1=0.30, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.50, y0=0.10, x1=0.64, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.06, y0=0.30, x1=0.08, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.14, y0=0.80, x1=0.16, y1=0.83),
                make_box("panel_label_B", "panel_label", x0=0.46, y0=0.80, x1=0.48, y1=0.83),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.12, y0=0.18, x1=0.34, y1=0.82),
                make_box("panel_B", "panel", x0=0.44, y0=0.18, x1=0.68, y1=0.82),
            ],
            "guide_boxes": [
                make_box("zero_line_A", "zero_line", x0=0.12, y0=0.48, x1=0.34, y1=0.49),
                make_box("zero_line_B", "zero_line", x0=0.44, y0=0.48, x1=0.68, y1=0.49),
                make_box("colorbar", "colorbar", x0=0.78, y0=0.22, x1=0.84, y1=0.80),
            ],
            "metrics": {
                "colorbar_label": "Interaction feature value",
                "panels": [
                    {
                        "panel_id": "age_panel",
                        "panel_label": "A",
                        "title": "Age",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "interaction_feature": "Albumin",
                        "points": [
                            {"feature_value": 38.0, "shap_value": -0.22, "interaction_value": 3.1, "x": 0.18, "y": 0.34},
                        ],
                    },
                    {
                        "panel_id": "platelet_panel",
                        "panel_label": "B",
                        "title": "Platelet count",
                        "x_label": "Platelets (10^9/L)",
                        "feature": "Platelet count",
                        "interaction_feature": "Age",
                        "points": [
                            {"feature_value": 85.0, "shap_value": 0.28, "interaction_value": 72.0, "x": 0.73, "y": 0.68},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "point_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_waterfall_local_explanation_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_waterfall_local_explanation_panel",
        layout_sidecar={
            "template_id": "shap_waterfall_local_explanation_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.87, x1=0.29, y1=0.90),
                make_box("panel_title_B", "panel_title", x0=0.46, y0=0.87, x1=0.67, y1=0.90),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.82, x1=0.12, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.46, y0=0.82, x1=0.48, y1=0.85),
                make_box("case_label_A", "case_label", x0=0.14, y0=0.82, x1=0.28, y1=0.85),
                make_box("case_label_B", "case_label", x0=0.50, y0=0.82, x1=0.66, y1=0.85),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.15, y0=0.10, x1=0.31, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.50, y0=0.10, x1=0.68, y1=0.13),
                make_box("baseline_label_A", "baseline_label", x0=0.14, y0=0.75, x1=0.20, y1=0.78),
                make_box("prediction_label_A", "prediction_label", x0=0.26, y0=0.75, x1=0.33, y1=0.78),
                make_box("baseline_label_B", "baseline_label", x0=0.48, y0=0.75, x1=0.54, y1=0.78),
                make_box("prediction_label_B", "prediction_label", x0=0.60, y0=0.75, x1=0.68, y1=0.78),
                make_box("feature_label_A_1", "feature_label", x0=0.05, y0=0.63, x1=0.12, y1=0.68),
                make_box("feature_label_A_2", "feature_label", x0=0.05, y0=0.48, x1=0.12, y1=0.53),
                make_box("feature_label_B_1", "feature_label", x0=0.40, y0=0.63, x1=0.47, y1=0.68),
                make_box("feature_label_B_2", "feature_label", x0=0.40, y0=0.48, x1=0.47, y1=0.53),
                make_box("contribution_bar_A_1", "contribution_bar", x0=0.16, y0=0.62, x1=0.24, y1=0.68),
                make_box("contribution_bar_A_2", "contribution_bar", x0=0.24, y0=0.47, x1=0.29, y1=0.53),
                make_box("contribution_bar_B_1", "contribution_bar", x0=0.52, y0=0.62, x1=0.60, y1=0.68),
                make_box("contribution_bar_B_2", "contribution_bar", x0=0.60, y0=0.47, x1=0.64, y1=0.53),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.13, y0=0.18, x1=0.34, y1=0.80),
                make_box("panel_B", "panel", x0=0.48, y0=0.18, x1=0.70, y1=0.80),
            ],
            "guide_boxes": [
                make_box("baseline_marker_A", "baseline_marker", x0=0.16, y0=0.18, x1=0.161, y1=0.80),
                make_box("prediction_marker_A", "prediction_marker", x0=0.30, y0=0.18, x1=0.301, y1=0.80),
                make_box("baseline_marker_B", "baseline_marker", x0=0.52, y0=0.18, x1=0.521, y1=0.80),
                make_box("prediction_marker_B", "prediction_marker", x0=0.66, y0=0.18, x1=0.661, y1=0.80),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "case_a",
                        "panel_label": "A",
                        "title": "Representative high-risk case",
                        "case_label": "Case 1",
                        "baseline_value": 0.18,
                        "predicted_value": 0.31,
                        "panel_box_id": "panel_A",
                        "baseline_marker_box_id": "baseline_marker_A",
                        "prediction_marker_box_id": "prediction_marker_A",
                        "contributions": [
                            {
                                "feature": "Age",
                                "shap_value": 0.10,
                                "start_value": 0.18,
                                "end_value": 0.28,
                                "bar_box_id": "contribution_bar_A_1",
                                "label_box_id": "feature_label_A_1",
                            },
                            {
                                "feature": "Albumin",
                                "shap_value": 0.03,
                                "start_value": 0.28,
                                "end_value": 0.31,
                                "bar_box_id": "contribution_bar_A_2",
                                "label_box_id": "feature_label_A_2",
                            },
                        ],
                    },
                    {
                        "panel_id": "case_b",
                        "panel_label": "B",
                        "title": "Representative lower-risk case",
                        "case_label": "Case 2",
                        "baseline_value": 0.42,
                        "predicted_value": 0.35,
                        "panel_box_id": "panel_B",
                        "baseline_marker_box_id": "baseline_marker_B",
                        "prediction_marker_box_id": "prediction_marker_B",
                        "contributions": [
                            {
                                "feature": "Age",
                                "shap_value": -0.08,
                                "start_value": 0.42,
                                "end_value": 0.34,
                                "bar_box_id": "contribution_bar_B_1",
                                "label_box_id": "feature_label_B_1",
                            },
                            {
                                "feature": "Albumin",
                                "shap_value": 0.01,
                                "start_value": 0.34,
                                "end_value": 0.35,
                                "bar_box_id": "contribution_bar_B_2",
                                "label_box_id": "feature_label_B_2",
                            },
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_shap_waterfall_contribution_bar_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_waterfall_local_explanation_panel",
        layout_sidecar={
            "template_id": "shap_waterfall_local_explanation_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.87, x1=0.29, y1=0.90),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.82, x1=0.12, y1=0.85),
                make_box("case_label_A", "case_label", x0=0.14, y0=0.82, x1=0.28, y1=0.85),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.15, y0=0.10, x1=0.31, y1=0.13),
                make_box("baseline_label_A", "baseline_label", x0=0.14, y0=0.75, x1=0.20, y1=0.78),
                make_box("prediction_label_A", "prediction_label", x0=0.26, y0=0.75, x1=0.33, y1=0.78),
                make_box("feature_label_A_1", "feature_label", x0=0.05, y0=0.63, x1=0.12, y1=0.68),
                make_box("contribution_bar_A_1", "contribution_bar", x0=0.16, y0=0.62, x1=0.38, y1=0.68),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.13, y0=0.18, x1=0.34, y1=0.80),
            ],
            "guide_boxes": [
                make_box("baseline_marker_A", "baseline_marker", x0=0.16, y0=0.18, x1=0.161, y1=0.80),
                make_box("prediction_marker_A", "prediction_marker", x0=0.30, y0=0.18, x1=0.301, y1=0.80),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "case_a",
                        "panel_label": "A",
                        "title": "Representative high-risk case",
                        "case_label": "Case 1",
                        "baseline_value": 0.18,
                        "predicted_value": 0.31,
                        "panel_box_id": "panel_A",
                        "baseline_marker_box_id": "baseline_marker_A",
                        "prediction_marker_box_id": "prediction_marker_A",
                        "contributions": [
                            {
                                "feature": "Age",
                                "shap_value": 0.13,
                                "start_value": 0.18,
                                "end_value": 0.31,
                                "bar_box_id": "contribution_bar_A_1",
                                "label_box_id": "feature_label_A_1",
                            },
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "contribution_bar_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_force_like_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_force_like_summary_panel",
        layout_sidecar={
            "template_id": "shap_force_like_summary_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.87, x1=0.31, y1=0.90),
                make_box("panel_title_B", "panel_title", x0=0.48, y0=0.87, x1=0.70, y1=0.90),
                make_box("panel_label_A", "panel_label", x0=0.14, y0=0.80, x1=0.16, y1=0.823),
                make_box("panel_label_B", "panel_label", x0=0.48, y0=0.80, x1=0.50, y1=0.823),
                make_box("case_label_A", "case_label", x0=0.17, y0=0.80, x1=0.30, y1=0.823),
                make_box("case_label_B", "case_label", x0=0.52, y0=0.80, x1=0.68, y1=0.823),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.15, y0=0.10, x1=0.31, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.53, y0=0.10, x1=0.69, y1=0.13),
                make_box("baseline_label_A", "baseline_label", x0=0.18, y0=0.75, x1=0.24, y1=0.78),
                make_box("prediction_label_A", "prediction_label", x0=0.28, y0=0.75, x1=0.34, y1=0.78),
                make_box("baseline_label_B", "baseline_label", x0=0.56, y0=0.75, x1=0.62, y1=0.78),
                make_box("prediction_label_B", "prediction_label", x0=0.47, y0=0.75, x1=0.53, y1=0.78),
                make_box("force_label_A_1", "force_feature_label", x0=0.23, y0=0.51, x1=0.29, y1=0.55),
                make_box("force_label_A_2", "force_feature_label", x0=0.15, y0=0.32, x1=0.20, y1=0.36),
                make_box("force_label_B_1", "force_feature_label", x0=0.59, y0=0.51, x1=0.65, y1=0.55),
                make_box("force_label_B_2", "force_feature_label", x0=0.50, y0=0.32, x1=0.55, y1=0.36),
                make_box("positive_force_segment_A_1", "positive_force_segment", x0=0.21, y0=0.50, x1=0.31, y1=0.56),
                make_box("negative_force_segment_A_2", "negative_force_segment", x0=0.14, y0=0.31, x1=0.21, y1=0.37),
                make_box("positive_force_segment_B_1", "positive_force_segment", x0=0.57, y0=0.50, x1=0.66, y1=0.56),
                make_box("negative_force_segment_B_2", "negative_force_segment", x0=0.48, y0=0.31, x1=0.57, y1=0.37),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.13, y0=0.18, x1=0.35, y1=0.80),
                make_box("panel_B", "panel", x0=0.47, y0=0.18, x1=0.70, y1=0.80),
            ],
            "guide_boxes": [
                make_box("baseline_marker_A", "baseline_marker", x0=0.21, y0=0.22, x1=0.212, y1=0.74),
                make_box("prediction_marker_A", "prediction_marker", x0=0.31, y0=0.22, x1=0.312, y1=0.74),
                make_box("baseline_marker_B", "baseline_marker", x0=0.57, y0=0.22, x1=0.572, y1=0.74),
                make_box("prediction_marker_B", "prediction_marker", x0=0.48, y0=0.22, x1=0.482, y1=0.74),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "case_a",
                        "panel_label": "A",
                        "title": "Representative responder",
                        "case_label": "Case 1",
                        "baseline_value": 0.22,
                        "predicted_value": 0.31,
                        "panel_box_id": "panel_A",
                        "baseline_marker_box_id": "baseline_marker_A",
                        "prediction_marker_box_id": "prediction_marker_A",
                        "contributions": [
                            {
                                "feature": "Age",
                                "feature_value_text": "74 years",
                                "shap_value": 0.13,
                                "direction": "positive",
                                "start_value": 0.22,
                                "end_value": 0.35,
                                "segment_box_id": "positive_force_segment_A_1",
                                "label_box_id": "force_label_A_1",
                            },
                            {
                                "feature": "Albumin",
                                "feature_value_text": "3.1 g/dL",
                                "shap_value": -0.04,
                                "direction": "negative",
                                "start_value": 0.22,
                                "end_value": 0.18,
                                "segment_box_id": "negative_force_segment_A_2",
                                "label_box_id": "force_label_A_2",
                            },
                        ],
                    },
                    {
                        "panel_id": "case_b",
                        "panel_label": "B",
                        "title": "Representative non-responder",
                        "case_label": "Case 2",
                        "baseline_value": 0.57,
                        "predicted_value": 0.48,
                        "panel_box_id": "panel_B",
                        "baseline_marker_box_id": "baseline_marker_B",
                        "prediction_marker_box_id": "prediction_marker_B",
                        "contributions": [
                            {
                                "feature": "Tumor stage",
                                "feature_value_text": "Stage III",
                                "shap_value": 0.09,
                                "direction": "positive",
                                "start_value": 0.57,
                                "end_value": 0.66,
                                "segment_box_id": "positive_force_segment_B_1",
                                "label_box_id": "force_label_B_1",
                            },
                            {
                                "feature": "Albumin",
                                "feature_value_text": "4.6 g/dL",
                                "shap_value": -0.18,
                                "direction": "negative",
                                "start_value": 0.57,
                                "end_value": 0.39,
                                "segment_box_id": "negative_force_segment_B_2",
                                "label_box_id": "force_label_B_2",
                            },
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_passes_for_shap_grouped_local_explanation_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_grouped_local_explanation_panel",
        layout_sidecar={
            "template_id": "shap_grouped_local_explanation_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.11, y0=0.87, x1=0.29, y1=0.90),
                make_box("panel_title_B", "panel_title", x0=0.49, y0=0.87, x1=0.68, y1=0.90),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.81, x1=0.13, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.49, y0=0.81, x1=0.51, y1=0.84),
                make_box("group_label_A", "group_label", x0=0.15, y0=0.81, x1=0.29, y1=0.84),
                make_box("group_label_B", "group_label", x0=0.53, y0=0.81, x1=0.68, y1=0.84),
                make_box("baseline_label_A", "baseline_label", x0=0.15, y0=0.75, x1=0.22, y1=0.78),
                make_box("baseline_label_B", "baseline_label", x0=0.53, y0=0.75, x1=0.60, y1=0.78),
                make_box("prediction_label_A", "prediction_label", x0=0.24, y0=0.75, x1=0.31, y1=0.78),
                make_box("prediction_label_B", "prediction_label", x0=0.61, y0=0.75, x1=0.69, y1=0.78),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.15, y0=0.10, x1=0.33, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.53, y0=0.10, x1=0.71, y1=0.13),
                make_box("feature_label_A_1", "feature_label", x0=0.02, y0=0.62, x1=0.09, y1=0.67),
                make_box("feature_label_A_2", "feature_label", x0=0.01, y0=0.48, x1=0.09, y1=0.53),
                make_box("feature_label_A_3", "feature_label", x0=0.00, y0=0.34, x1=0.09, y1=0.39),
                make_box("feature_label_B_1", "feature_label", x0=0.40, y0=0.62, x1=0.47, y1=0.67),
                make_box("feature_label_B_2", "feature_label", x0=0.39, y0=0.48, x1=0.47, y1=0.53),
                make_box("feature_label_B_3", "feature_label", x0=0.38, y0=0.34, x1=0.47, y1=0.39),
                make_box("contribution_bar_A_1", "contribution_bar", x0=0.22, y0=0.62, x1=0.33, y1=0.67),
                make_box("contribution_bar_A_2", "contribution_bar", x0=0.12, y0=0.48, x1=0.22, y1=0.53),
                make_box("contribution_bar_A_3", "contribution_bar", x0=0.22, y0=0.34, x1=0.25, y1=0.39),
                make_box("contribution_bar_B_1", "contribution_bar", x0=0.44, y0=0.62, x1=0.53, y1=0.67),
                make_box("contribution_bar_B_2", "contribution_bar", x0=0.53, y0=0.48, x1=0.56, y1=0.53),
                make_box("contribution_bar_B_3", "contribution_bar", x0=0.52, y0=0.34, x1=0.53, y1=0.39),
                make_box("value_label_A_1", "value_label", x0=0.34, y0=0.62, x1=0.39, y1=0.67),
                make_box("value_label_A_2", "value_label", x0=0.07, y0=0.48, x1=0.11, y1=0.53),
                make_box("value_label_A_3", "value_label", x0=0.26, y0=0.34, x1=0.31, y1=0.39),
                make_box("value_label_B_1", "value_label", x0=0.39, y0=0.62, x1=0.43, y1=0.67),
                make_box("value_label_B_2", "value_label", x0=0.57, y0=0.48, x1=0.61, y1=0.53),
                make_box("value_label_B_3", "value_label", x0=0.46, y0=0.34, x1=0.51, y1=0.39),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.12, y0=0.18, x1=0.39, y1=0.80),
                make_box("panel_B", "panel", x0=0.50, y0=0.18, x1=0.77, y1=0.80),
            ],
            "guide_boxes": [
                make_box("zero_line_A", "zero_line", x0=0.22, y0=0.18, x1=0.221, y1=0.80),
                make_box("zero_line_B", "zero_line", x0=0.53, y0=0.18, x1=0.531, y1=0.80),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "high_risk",
                        "panel_label": "A",
                        "title": "High-risk phenotype",
                        "group_label": "Phenotype 1",
                        "baseline_value": 0.22,
                        "predicted_value": 0.34,
                        "panel_box_id": "panel_A",
                        "zero_line_box_id": "zero_line_A",
                        "contributions": [
                            {
                                "rank": 1,
                                "feature": "Age",
                                "shap_value": 0.14,
                                "bar_box_id": "contribution_bar_A_1",
                                "feature_label_box_id": "feature_label_A_1",
                                "value_label_box_id": "value_label_A_1",
                            },
                            {
                                "rank": 2,
                                "feature": "Albumin",
                                "shap_value": -0.05,
                                "bar_box_id": "contribution_bar_A_2",
                                "feature_label_box_id": "feature_label_A_2",
                                "value_label_box_id": "value_label_A_2",
                            },
                            {
                                "rank": 3,
                                "feature": "Tumor size",
                                "shap_value": 0.03,
                                "bar_box_id": "contribution_bar_A_3",
                                "feature_label_box_id": "feature_label_A_3",
                                "value_label_box_id": "value_label_A_3",
                            },
                        ],
                    },
                    {
                        "panel_id": "low_risk",
                        "panel_label": "B",
                        "title": "Lower-risk phenotype",
                        "group_label": "Phenotype 2",
                        "baseline_value": 0.18,
                        "predicted_value": 0.12,
                        "panel_box_id": "panel_B",
                        "zero_line_box_id": "zero_line_B",
                        "contributions": [
                            {
                                "rank": 1,
                                "feature": "Age",
                                "shap_value": -0.07,
                                "bar_box_id": "contribution_bar_B_1",
                                "feature_label_box_id": "feature_label_B_1",
                                "value_label_box_id": "value_label_B_1",
                            },
                            {
                                "rank": 2,
                                "feature": "Albumin",
                                "shap_value": 0.02,
                                "bar_box_id": "contribution_bar_B_2",
                                "feature_label_box_id": "feature_label_B_2",
                                "value_label_box_id": "value_label_B_2",
                            },
                            {
                                "rank": 3,
                                "feature": "Tumor size",
                                "shap_value": -0.01,
                                "bar_box_id": "contribution_bar_B_3",
                                "feature_label_box_id": "feature_label_B_3",
                                "value_label_box_id": "value_label_B_3",
                            },
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_grouped_local_positive_bar_crosses_zero() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_grouped_local_explanation_panel",
        layout_sidecar={
            "template_id": "shap_grouped_local_explanation_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.11, y0=0.87, x1=0.29, y1=0.90),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.81, x1=0.13, y1=0.84),
                make_box("group_label_A", "group_label", x0=0.15, y0=0.81, x1=0.29, y1=0.84),
                make_box("baseline_label_A", "baseline_label", x0=0.15, y0=0.75, x1=0.22, y1=0.78),
                make_box("prediction_label_A", "prediction_label", x0=0.24, y0=0.75, x1=0.31, y1=0.78),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.15, y0=0.10, x1=0.33, y1=0.13),
                make_box("feature_label_A_1", "feature_label", x0=0.02, y0=0.62, x1=0.09, y1=0.67),
                make_box("contribution_bar_A_1", "contribution_bar", x0=0.18, y0=0.62, x1=0.33, y1=0.67),
                make_box("value_label_A_1", "value_label", x0=0.34, y0=0.62, x1=0.39, y1=0.67),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.12, y0=0.18, x1=0.39, y1=0.80),
            ],
            "guide_boxes": [
                make_box("zero_line_A", "zero_line", x0=0.22, y0=0.18, x1=0.221, y1=0.80),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "high_risk",
                        "panel_label": "A",
                        "title": "High-risk phenotype",
                        "group_label": "Phenotype 1",
                        "baseline_value": 0.22,
                        "predicted_value": 0.34,
                        "panel_box_id": "panel_A",
                        "zero_line_box_id": "zero_line_A",
                        "contributions": [
                            {
                                "rank": 1,
                                "feature": "Age",
                                "shap_value": 0.14,
                                "bar_box_id": "contribution_bar_A_1",
                                "feature_label_box_id": "feature_label_A_1",
                                "value_label_box_id": "value_label_A_1",
                            },
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "positive_bar_crosses_zero" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_grouped_local_support_domain_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_grouped_local_support_domain_panel",
        layout_sidecar=_make_shap_grouped_local_support_domain_layout_sidecar(),
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_grouped_local_support_domain_support_order_drifts() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")
    layout_sidecar = _make_shap_grouped_local_support_domain_layout_sidecar()
    support_panels = layout_sidecar["metrics"]["support_panels"]
    support_panels[0]["feature"] = "Tumor size"
    support_panels[1]["feature"] = "Age"

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_grouped_local_support_domain_panel",
        layout_sidecar=layout_sidecar,
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "support_feature_order_mismatch" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_multigroup_decision_path_support_domain_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_multigroup_decision_path_support_domain_panel",
        layout_sidecar=_make_shap_multigroup_decision_path_support_domain_layout_sidecar(),
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_multigroup_support_domain_support_order_drifts() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")
    layout_sidecar = _make_shap_multigroup_decision_path_support_domain_layout_sidecar()
    support_panels = layout_sidecar["metrics"]["support_panels"]
    support_panels[0]["feature"] = "Albumin"
    support_panels[1]["feature"] = "Age"

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_multigroup_decision_path_support_domain_panel",
        layout_sidecar=layout_sidecar,
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "support_feature_order_mismatch" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_signed_importance_local_support_domain_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_signed_importance_local_support_domain_panel",
        layout_sidecar=_make_shap_signed_importance_local_support_domain_layout_sidecar(tmp_path),
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_signed_importance_local_support_domain_local_order_drifts(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")
    layout_sidecar = _make_shap_signed_importance_local_support_domain_layout_sidecar(tmp_path)
    contributions = layout_sidecar["metrics"]["local_panel"]["contributions"]
    contributions[0], contributions[1] = contributions[1], contributions[0]

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_signed_importance_local_support_domain_panel",
        layout_sidecar=layout_sidecar,
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "local_feature_order_mismatch" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_signed_importance_local_support_domain_support_order_drifts(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")
    layout_sidecar = _make_shap_signed_importance_local_support_domain_layout_sidecar(tmp_path)
    support_panels = layout_sidecar["metrics"]["support_panels"]
    support_panels[0]["feature"] = "Age"
    support_panels[1]["feature"] = "Albumin"

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_signed_importance_local_support_domain_panel",
        layout_sidecar=layout_sidecar,
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "support_feature_order_mismatch" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_signed_importance_local_support_domain_support_legend_title_box_is_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")
    layout_sidecar = _make_shap_signed_importance_local_support_domain_layout_sidecar(tmp_path)
    layout_sidecar["layout_boxes"] = [
        box for box in layout_sidecar["layout_boxes"] if box.get("box_id") != "support_legend_title"
    ]

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_signed_importance_local_support_domain_panel",
        layout_sidecar=layout_sidecar,
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "support_legend_title_missing" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_grouped_decision_path_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_grouped_decision_path_panel",
        layout_sidecar={
            "template_id": "shap_grouped_decision_path_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title", "panel_title", x0=0.22, y0=0.88, x1=0.62, y1=0.91),
                make_box("x_axis_title", "subplot_x_axis_title", x0=0.33, y0=0.10, x1=0.58, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.06, y0=0.30, x1=0.09, y1=0.76),
                make_box("legend_title", "legend_title", x0=0.71, y0=0.22, x1=0.82, y1=0.25),
                make_box("legend_box", "legend_box", x0=0.69, y0=0.19, x1=0.89, y1=0.33),
                make_box("feature_label_1", "feature_label", x0=0.11, y0=0.67, x1=0.18, y1=0.71),
                make_box("feature_label_2", "feature_label", x0=0.09, y0=0.49, x1=0.18, y1=0.53),
                make_box("feature_label_3", "feature_label", x0=0.08, y0=0.31, x1=0.18, y1=0.35),
                make_box("decision_path_line_immune_inflamed", "decision_path_line", x0=0.31, y0=0.24, x1=0.66, y1=0.72),
                make_box("decision_path_line_stromal_low", "decision_path_line", x0=0.24, y0=0.24, x1=0.56, y1=0.72),
                make_box("prediction_label_immune_inflamed", "prediction_label", x0=0.60, y0=0.21, x1=0.73, y1=0.25),
                make_box("prediction_label_stromal_low", "prediction_label", x0=0.36, y0=0.21, x1=0.50, y1=0.25),
            ],
            "panel_boxes": [
                make_box("panel_decision_path", "panel", x0=0.20, y0=0.18, x1=0.67, y1=0.82),
            ],
            "guide_boxes": [
                make_box("baseline_reference_line", "baseline_reference_line", x0=0.33, y0=0.18, x1=0.331, y1=0.82),
                make_box("prediction_marker_immune_inflamed", "prediction_marker", x0=0.62, y0=0.22, x1=0.628, y1=0.24),
                make_box("prediction_marker_stromal_low", "prediction_marker", x0=0.41, y0=0.22, x1=0.418, y1=0.24),
            ],
            "metrics": {
                "panel_box_id": "panel_decision_path",
                "baseline_line_box_id": "baseline_reference_line",
                "baseline_value": 0.19,
                "legend_title": "Phenotype",
                "feature_order": ["Age", "Albumin", "Tumor size"],
                "feature_label_box_ids": ["feature_label_1", "feature_label_2", "feature_label_3"],
                "groups": [
                    {
                        "group_id": "immune_inflamed",
                        "group_label": "Phenotype 1",
                        "predicted_value": 0.34,
                        "line_box_id": "decision_path_line_immune_inflamed",
                        "prediction_marker_box_id": "prediction_marker_immune_inflamed",
                        "prediction_label_box_id": "prediction_label_immune_inflamed",
                        "contributions": [
                            {"rank": 1, "feature": "Age", "shap_value": 0.10, "start_value": 0.19, "end_value": 0.29},
                            {"rank": 2, "feature": "Albumin", "shap_value": -0.03, "start_value": 0.29, "end_value": 0.26},
                            {"rank": 3, "feature": "Tumor size", "shap_value": 0.08, "start_value": 0.26, "end_value": 0.34},
                        ],
                    },
                    {
                        "group_id": "stromal_low",
                        "group_label": "Phenotype 2",
                        "predicted_value": 0.08,
                        "line_box_id": "decision_path_line_stromal_low",
                        "prediction_marker_box_id": "prediction_marker_stromal_low",
                        "prediction_label_box_id": "prediction_label_stromal_low",
                        "contributions": [
                            {"rank": 1, "feature": "Age", "shap_value": -0.04, "start_value": 0.19, "end_value": 0.15},
                            {"rank": 2, "feature": "Albumin", "shap_value": -0.02, "start_value": 0.15, "end_value": 0.13},
                            {"rank": 3, "feature": "Tumor size", "shap_value": -0.05, "start_value": 0.13, "end_value": 0.08},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_shap_grouped_decision_path_lacks_legend() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_grouped_decision_path_panel",
        layout_sidecar={
            "template_id": "shap_grouped_decision_path_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title", "panel_title", x0=0.22, y0=0.88, x1=0.62, y1=0.91),
                make_box("x_axis_title", "subplot_x_axis_title", x0=0.33, y0=0.10, x1=0.58, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.06, y0=0.30, x1=0.09, y1=0.76),
                make_box("feature_label_1", "feature_label", x0=0.11, y0=0.67, x1=0.18, y1=0.71),
                make_box("feature_label_2", "feature_label", x0=0.09, y0=0.49, x1=0.18, y1=0.53),
                make_box("feature_label_3", "feature_label", x0=0.08, y0=0.31, x1=0.18, y1=0.35),
                make_box("decision_path_line_immune_inflamed", "decision_path_line", x0=0.31, y0=0.24, x1=0.66, y1=0.72),
                make_box("decision_path_line_stromal_low", "decision_path_line", x0=0.24, y0=0.24, x1=0.56, y1=0.72),
                make_box("prediction_label_immune_inflamed", "prediction_label", x0=0.60, y0=0.21, x1=0.73, y1=0.25),
                make_box("prediction_label_stromal_low", "prediction_label", x0=0.36, y0=0.21, x1=0.50, y1=0.25),
            ],
            "panel_boxes": [
                make_box("panel_decision_path", "panel", x0=0.20, y0=0.18, x1=0.67, y1=0.82),
            ],
            "guide_boxes": [
                make_box("baseline_reference_line", "baseline_reference_line", x0=0.33, y0=0.18, x1=0.331, y1=0.82),
                make_box("prediction_marker_immune_inflamed", "prediction_marker", x0=0.62, y0=0.22, x1=0.628, y1=0.24),
                make_box("prediction_marker_stromal_low", "prediction_marker", x0=0.41, y0=0.22, x1=0.418, y1=0.24),
            ],
            "metrics": {
                "panel_box_id": "panel_decision_path",
                "baseline_line_box_id": "baseline_reference_line",
                "baseline_value": 0.19,
                "legend_title": "Phenotype",
                "feature_order": ["Age", "Albumin", "Tumor size"],
                "feature_label_box_ids": ["feature_label_1", "feature_label_2", "feature_label_3"],
                "groups": [
                    {
                        "group_id": "immune_inflamed",
                        "group_label": "Phenotype 1",
                        "predicted_value": 0.34,
                        "line_box_id": "decision_path_line_immune_inflamed",
                        "prediction_marker_box_id": "prediction_marker_immune_inflamed",
                        "prediction_label_box_id": "prediction_label_immune_inflamed",
                        "contributions": [
                            {"rank": 1, "feature": "Age", "shap_value": 0.10, "start_value": 0.19, "end_value": 0.29},
                            {"rank": 2, "feature": "Albumin", "shap_value": -0.03, "start_value": 0.29, "end_value": 0.26},
                            {"rank": 3, "feature": "Tumor size", "shap_value": 0.08, "start_value": 0.26, "end_value": 0.34},
                        ],
                    },
                    {
                        "group_id": "stromal_low",
                        "group_label": "Phenotype 2",
                        "predicted_value": 0.08,
                        "line_box_id": "decision_path_line_stromal_low",
                        "prediction_marker_box_id": "prediction_marker_stromal_low",
                        "prediction_label_box_id": "prediction_label_stromal_low",
                        "contributions": [
                            {"rank": 1, "feature": "Age", "shap_value": -0.04, "start_value": 0.19, "end_value": 0.15},
                            {"rank": 2, "feature": "Albumin", "shap_value": -0.02, "start_value": 0.15, "end_value": 0.13},
                            {"rank": 3, "feature": "Tumor size", "shap_value": -0.05, "start_value": 0.13, "end_value": 0.08},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "legend_box_missing" for issue in result["issues"])
