from .shared import *

def test_run_display_layout_qc_passes_for_shap_multigroup_decision_path_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_multigroup_decision_path_panel",
        layout_sidecar={
            "template_id": "shap_multigroup_decision_path_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title", "panel_title", x0=0.20, y0=0.88, x1=0.64, y1=0.91),
                make_box("x_axis_title", "subplot_x_axis_title", x0=0.30, y0=0.10, x1=0.60, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.06, y0=0.28, x1=0.09, y1=0.78),
                make_box("legend_title", "legend_title", x0=0.72, y0=0.23, x1=0.86, y1=0.26),
                make_box("legend_box", "legend_box", x0=0.69, y0=0.18, x1=0.92, y1=0.36),
                make_box("feature_label_1", "feature_label", x0=0.10, y0=0.70, x1=0.18, y1=0.74),
                make_box("feature_label_2", "feature_label", x0=0.08, y0=0.51, x1=0.18, y1=0.55),
                make_box("feature_label_3", "feature_label", x0=0.07, y0=0.32, x1=0.18, y1=0.36),
                make_box("decision_path_line_immune_inflamed", "decision_path_line", x0=0.31, y0=0.24, x1=0.66, y1=0.74),
                make_box("decision_path_line_stromal_low", "decision_path_line", x0=0.24, y0=0.24, x1=0.56, y1=0.74),
                make_box("decision_path_line_immune_excluded", "decision_path_line", x0=0.28, y0=0.24, x1=0.62, y1=0.74),
                make_box("prediction_label_immune_inflamed", "prediction_label", x0=0.61, y0=0.20, x1=0.75, y1=0.24),
                make_box("prediction_label_stromal_low", "prediction_label", x0=0.35, y0=0.20, x1=0.50, y1=0.24),
                make_box("prediction_label_immune_excluded", "prediction_label", x0=0.54, y0=0.20, x1=0.70, y1=0.24),
            ],
            "panel_boxes": [
                make_box("panel_decision_path", "panel", x0=0.19, y0=0.18, x1=0.68, y1=0.82),
            ],
            "guide_boxes": [
                make_box("baseline_reference_line", "baseline_reference_line", x0=0.33, y0=0.18, x1=0.331, y1=0.82),
                make_box("prediction_marker_immune_inflamed", "prediction_marker", x0=0.62, y0=0.22, x1=0.628, y1=0.24),
                make_box("prediction_marker_stromal_low", "prediction_marker", x0=0.41, y0=0.22, x1=0.418, y1=0.24),
                make_box("prediction_marker_immune_excluded", "prediction_marker", x0=0.56, y0=0.22, x1=0.568, y1=0.24),
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
                    {
                        "group_id": "immune_excluded",
                        "group_label": "Phenotype 3",
                        "predicted_value": 0.21,
                        "line_box_id": "decision_path_line_immune_excluded",
                        "prediction_marker_box_id": "prediction_marker_immune_excluded",
                        "prediction_label_box_id": "prediction_label_immune_excluded",
                        "contributions": [
                            {"rank": 1, "feature": "Age", "shap_value": 0.02, "start_value": 0.19, "end_value": 0.21},
                            {"rank": 2, "feature": "Albumin", "shap_value": -0.01, "start_value": 0.21, "end_value": 0.20},
                            {"rank": 3, "feature": "Tumor size", "shap_value": 0.01, "start_value": 0.20, "end_value": 0.21},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_shap_multigroup_decision_path_has_wrong_group_count() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_multigroup_decision_path_panel",
        layout_sidecar={
            "template_id": "shap_multigroup_decision_path_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title", "panel_title", x0=0.20, y0=0.88, x1=0.64, y1=0.91),
                make_box("x_axis_title", "subplot_x_axis_title", x0=0.30, y0=0.10, x1=0.60, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.06, y0=0.28, x1=0.09, y1=0.78),
                make_box("legend_title", "legend_title", x0=0.72, y0=0.23, x1=0.86, y1=0.26),
                make_box("legend_box", "legend_box", x0=0.69, y0=0.18, x1=0.92, y1=0.36),
                make_box("feature_label_1", "feature_label", x0=0.10, y0=0.70, x1=0.18, y1=0.74),
                make_box("feature_label_2", "feature_label", x0=0.08, y0=0.51, x1=0.18, y1=0.55),
                make_box("feature_label_3", "feature_label", x0=0.07, y0=0.32, x1=0.18, y1=0.36),
                make_box("decision_path_line_immune_inflamed", "decision_path_line", x0=0.31, y0=0.24, x1=0.66, y1=0.74),
                make_box("decision_path_line_stromal_low", "decision_path_line", x0=0.24, y0=0.24, x1=0.56, y1=0.74),
                make_box("prediction_label_immune_inflamed", "prediction_label", x0=0.61, y0=0.20, x1=0.75, y1=0.24),
                make_box("prediction_label_stromal_low", "prediction_label", x0=0.35, y0=0.20, x1=0.50, y1=0.24),
            ],
            "panel_boxes": [
                make_box("panel_decision_path", "panel", x0=0.19, y0=0.18, x1=0.68, y1=0.82),
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
    assert any(issue["rule_id"] == "group_count_invalid" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_force_like_positive_segment_crosses_baseline() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_force_like_summary_panel",
        layout_sidecar={
            "template_id": "shap_force_like_summary_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.87, x1=0.31, y1=0.90),
                make_box("panel_label_A", "panel_label", x0=0.14, y0=0.82, x1=0.16, y1=0.85),
                make_box("case_label_A", "case_label", x0=0.14, y0=0.82, x1=0.30, y1=0.85),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.15, y0=0.10, x1=0.31, y1=0.13),
                make_box("baseline_label_A", "baseline_label", x0=0.18, y0=0.75, x1=0.24, y1=0.78),
                make_box("prediction_label_A", "prediction_label", x0=0.28, y0=0.75, x1=0.34, y1=0.78),
                make_box("force_label_A_1", "force_feature_label", x0=0.23, y0=0.51, x1=0.29, y1=0.55),
                make_box("positive_force_segment_A_1", "positive_force_segment", x0=0.16, y0=0.50, x1=0.31, y1=0.56),
            ],
            "panel_boxes": [make_box("panel_A", "panel", x0=0.13, y0=0.18, x1=0.35, y1=0.80)],
            "guide_boxes": [
                make_box("baseline_marker_A", "baseline_marker", x0=0.21, y0=0.22, x1=0.212, y1=0.74),
                make_box("prediction_marker_A", "prediction_marker", x0=0.31, y0=0.22, x1=0.312, y1=0.74),
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
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "positive_segment_crosses_baseline" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_partial_dependence_ice_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_partial_dependence_ice_panel",
        layout_sidecar={
            "template_id": "partial_dependence_ice_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.87, x1=0.28, y1=0.90),
                make_box("panel_title_B", "panel_title", x0=0.46, y0=0.87, x1=0.66, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.30, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.51, y0=0.10, x1=0.68, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.32, x1=0.07, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.81, x1=0.14, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.46, y0=0.81, x1=0.48, y1=0.84),
                make_box("reference_label_A", "pdp_reference_label", x0=0.20, y0=0.76, x1=0.28, y1=0.79),
                make_box("reference_label_B", "pdp_reference_label", x0=0.54, y0=0.76, x1=0.64, y1=0.79),
                make_box("legend_box", "legend_box", x0=0.34, y0=0.03, x1=0.66, y1=0.08),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.11, y0=0.18, x1=0.34, y1=0.82),
                make_box("panel_B", "panel", x0=0.45, y0=0.18, x1=0.70, y1=0.82),
            ],
            "guide_boxes": [
                make_box("reference_line_A", "pdp_reference_line", x0=0.24, y0=0.18, x1=0.241, y1=0.82),
                make_box("reference_line_B", "pdp_reference_line", x0=0.58, y0=0.18, x1=0.581, y1=0.82),
            ],
            "metrics": {
                "legend_labels": ["ICE curves", "PDP mean"],
                "panels": [
                    {
                        "panel_id": "age_panel",
                        "panel_label": "A",
                        "title": "Age",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_A",
                        "reference_line_box_id": "reference_line_A",
                        "reference_label_box_id": "reference_label_A",
                        "pdp_points": [
                            {"x": 0.15, "y": 0.30},
                            {"x": 0.21, "y": 0.39},
                            {"x": 0.24, "y": 0.48},
                            {"x": 0.30, "y": 0.63},
                        ],
                        "ice_curves": [
                            {
                                "curve_id": "age_case_1",
                                "points": [
                                    {"x": 0.15, "y": 0.28},
                                    {"x": 0.21, "y": 0.37},
                                    {"x": 0.24, "y": 0.50},
                                    {"x": 0.30, "y": 0.67},
                                ],
                            },
                            {
                                "curve_id": "age_case_2",
                                "points": [
                                    {"x": 0.15, "y": 0.33},
                                    {"x": 0.21, "y": 0.41},
                                    {"x": 0.24, "y": 0.46},
                                    {"x": 0.30, "y": 0.61},
                                ],
                            },
                        ],
                    },
                    {
                        "panel_id": "albumin_panel",
                        "panel_label": "B",
                        "title": "Albumin",
                        "x_label": "Albumin (g/dL)",
                        "feature": "Albumin",
                        "reference_value": 3.8,
                        "reference_label": "Median albumin",
                        "panel_box_id": "panel_B",
                        "reference_line_box_id": "reference_line_B",
                        "reference_label_box_id": "reference_label_B",
                        "pdp_points": [
                            {"x": 0.49, "y": 0.67},
                            {"x": 0.55, "y": 0.55},
                            {"x": 0.58, "y": 0.46},
                            {"x": 0.65, "y": 0.34},
                        ],
                        "ice_curves": [
                            {
                                "curve_id": "alb_case_1",
                                "points": [
                                    {"x": 0.49, "y": 0.70},
                                    {"x": 0.55, "y": 0.58},
                                    {"x": 0.58, "y": 0.49},
                                    {"x": 0.65, "y": 0.36},
                                ],
                            },
                            {
                                "curve_id": "alb_case_2",
                                "points": [
                                    {"x": 0.49, "y": 0.64},
                                    {"x": 0.55, "y": 0.52},
                                    {"x": 0.58, "y": 0.44},
                                    {"x": 0.65, "y": 0.31},
                                ],
                            },
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_partial_dependence_ice_curve_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_partial_dependence_ice_panel",
        layout_sidecar={
            "template_id": "partial_dependence_ice_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.87, x1=0.28, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.30, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.32, x1=0.07, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.81, x1=0.14, y1=0.84),
                make_box("reference_label_A", "pdp_reference_label", x0=0.20, y0=0.76, x1=0.28, y1=0.79),
                make_box("legend_box", "legend_box", x0=0.34, y0=0.03, x1=0.66, y1=0.08),
            ],
            "panel_boxes": [make_box("panel_A", "panel", x0=0.11, y0=0.18, x1=0.34, y1=0.82)],
            "guide_boxes": [
                make_box("reference_line_A", "pdp_reference_line", x0=0.24, y0=0.18, x1=0.241, y1=0.82),
            ],
            "metrics": {
                "legend_labels": ["ICE curves", "PDP mean"],
                "panels": [
                    {
                        "panel_id": "age_panel",
                        "panel_label": "A",
                        "title": "Age",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_A",
                        "reference_line_box_id": "reference_line_A",
                        "reference_label_box_id": "reference_label_A",
                        "pdp_points": [
                            {"x": 0.15, "y": 0.30},
                            {"x": 0.21, "y": 0.39},
                            {"x": 0.24, "y": 0.48},
                            {"x": 0.30, "y": 0.63},
                        ],
                        "ice_curves": [
                            {
                                "curve_id": "age_case_1",
                                "points": [
                                    {"x": 0.15, "y": 0.28},
                                    {"x": 0.21, "y": 0.37},
                                    {"x": 0.38, "y": 0.50},
                                    {"x": 0.30, "y": 0.67},
                                ],
                            },
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "ice_point_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_partial_dependence_interaction_contour_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_partial_dependence_interaction_contour_panel",
        layout_sidecar={
            "template_id": "partial_dependence_interaction_contour_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.11, y0=0.87, x1=0.30, y1=0.90),
                make_box("panel_title_B", "panel_title", x0=0.47, y0=0.87, x1=0.71, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.30, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.52, y0=0.10, x1=0.69, y1=0.13),
                make_box("y_axis_title_A", "subplot_y_axis_title", x0=0.07, y0=0.33, x1=0.09, y1=0.69),
                make_box("y_axis_title_B", "subplot_y_axis_title", x0=0.43, y0=0.31, x1=0.45, y1=0.70),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.81, x1=0.13, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.47, y0=0.81, x1=0.49, y1=0.84),
                make_box("reference_label_A", "interaction_reference_label", x0=0.21, y0=0.76, x1=0.30, y1=0.79),
                make_box("reference_label_B", "interaction_reference_label", x0=0.58, y0=0.76, x1=0.69, y1=0.79),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.34, y1=0.82),
                make_box("panel_B", "panel", x0=0.46, y0=0.18, x1=0.72, y1=0.82),
            ],
            "guide_boxes": [
                make_box("colorbar", "colorbar", x0=0.82, y0=0.24, x1=0.85, y1=0.76),
                make_box("reference_vertical_A", "interaction_reference_vertical", x0=0.23, y0=0.18, x1=0.231, y1=0.82),
                make_box("reference_horizontal_A", "interaction_reference_horizontal", x0=0.10, y0=0.47, x1=0.34, y1=0.471),
                make_box("reference_vertical_B", "interaction_reference_vertical", x0=0.60, y0=0.18, x1=0.601, y1=0.82),
                make_box("reference_horizontal_B", "interaction_reference_horizontal", x0=0.46, y0=0.49, x1=0.72, y1=0.491),
            ],
            "metrics": {
                "colorbar_label": "Predicted response probability",
                "panels": [
                    {
                        "panel_id": "age_albumin",
                        "panel_label": "A",
                        "title": "Age x Albumin",
                        "x_label": "Age (years)",
                        "y_label": "Albumin (g/dL)",
                        "x_feature": "Age",
                        "y_feature": "Albumin",
                        "reference_x_value": 60.0,
                        "reference_y_value": 3.8,
                        "reference_label": "Median profile",
                        "panel_box_id": "panel_A",
                        "reference_vertical_box_id": "reference_vertical_A",
                        "reference_horizontal_box_id": "reference_horizontal_A",
                        "reference_label_box_id": "reference_label_A",
                        "x_grid": [40.0, 50.0, 60.0, 70.0],
                        "y_grid": [2.8, 3.4, 4.0, 4.6],
                        "response_grid": [
                            [0.44, 0.37, 0.31, 0.27],
                            [0.35, 0.29, 0.24, 0.20],
                            [0.28, 0.23, 0.19, 0.16],
                            [0.24, 0.20, 0.17, 0.14],
                        ],
                        "observed_points": [
                            {"point_id": "case_1", "x": 0.14, "y": 0.28},
                            {"point_id": "case_2", "x": 0.19, "y": 0.40},
                            {"point_id": "case_3", "x": 0.23, "y": 0.47},
                            {"point_id": "case_4", "x": 0.30, "y": 0.61},
                        ],
                    },
                    {
                        "panel_id": "tumor_platelet",
                        "panel_label": "B",
                        "title": "Tumor size x Platelets",
                        "x_label": "Tumor size (cm)",
                        "y_label": "Platelets (10^9/L)",
                        "x_feature": "Tumor size",
                        "y_feature": "Platelet count",
                        "reference_x_value": 6.0,
                        "reference_y_value": 160.0,
                        "reference_label": "Reference profile",
                        "panel_box_id": "panel_B",
                        "reference_vertical_box_id": "reference_vertical_B",
                        "reference_horizontal_box_id": "reference_horizontal_B",
                        "reference_label_box_id": "reference_label_B",
                        "x_grid": [2.0, 4.0, 6.0, 8.0],
                        "y_grid": [80.0, 120.0, 160.0, 200.0],
                        "response_grid": [
                            [0.18, 0.21, 0.25, 0.29],
                            [0.22, 0.27, 0.31, 0.36],
                            [0.27, 0.33, 0.39, 0.45],
                            [0.31, 0.38, 0.45, 0.52],
                        ],
                        "observed_points": [
                            {"point_id": "case_5", "x": 0.50, "y": 0.29},
                            {"point_id": "case_6", "x": 0.56, "y": 0.43},
                            {"point_id": "case_7", "x": 0.60, "y": 0.50},
                            {"point_id": "case_8", "x": 0.67, "y": 0.64},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_partial_dependence_interaction_support_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_partial_dependence_interaction_contour_panel",
        layout_sidecar={
            "template_id": "partial_dependence_interaction_contour_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.11, y0=0.87, x1=0.30, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.30, y1=0.13),
                make_box("y_axis_title_A", "subplot_y_axis_title", x0=0.07, y0=0.33, x1=0.09, y1=0.69),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.81, x1=0.13, y1=0.84),
                make_box("reference_label_A", "interaction_reference_label", x0=0.21, y0=0.76, x1=0.30, y1=0.79),
            ],
            "panel_boxes": [make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.34, y1=0.82)],
            "guide_boxes": [
                make_box("colorbar", "colorbar", x0=0.82, y0=0.24, x1=0.85, y1=0.76),
                make_box("reference_vertical_A", "interaction_reference_vertical", x0=0.23, y0=0.18, x1=0.231, y1=0.82),
                make_box("reference_horizontal_A", "interaction_reference_horizontal", x0=0.10, y0=0.47, x1=0.34, y1=0.471),
            ],
            "metrics": {
                "colorbar_label": "Predicted response probability",
                "panels": [
                    {
                        "panel_id": "age_albumin",
                        "panel_label": "A",
                        "title": "Age x Albumin",
                        "x_label": "Age (years)",
                        "y_label": "Albumin (g/dL)",
                        "x_feature": "Age",
                        "y_feature": "Albumin",
                        "reference_x_value": 60.0,
                        "reference_y_value": 3.8,
                        "reference_label": "Median profile",
                        "panel_box_id": "panel_A",
                        "reference_vertical_box_id": "reference_vertical_A",
                        "reference_horizontal_box_id": "reference_horizontal_A",
                        "reference_label_box_id": "reference_label_A",
                        "x_grid": [40.0, 50.0, 60.0, 70.0],
                        "y_grid": [2.8, 3.4, 4.0, 4.6],
                        "response_grid": [
                            [0.44, 0.37, 0.31, 0.27],
                            [0.35, 0.29, 0.24, 0.20],
                            [0.28, 0.23, 0.19, 0.16],
                            [0.24, 0.20, 0.17, 0.14],
                        ],
                        "observed_points": [
                            {"point_id": "case_1", "x": 0.14, "y": 0.28},
                            {"point_id": "case_2", "x": 0.38, "y": 0.40},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "observed_point_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_partial_dependence_interaction_slice_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_partial_dependence_interaction_slice_panel",
        layout_sidecar={
            "template_id": "partial_dependence_interaction_slice_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.87, x1=0.31, y1=0.90),
                make_box("panel_title_B", "panel_title", x0=0.46, y0=0.87, x1=0.72, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.31, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.52, y0=0.10, x1=0.70, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.32, x1=0.07, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.81, x1=0.14, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.46, y0=0.81, x1=0.48, y1=0.84),
                make_box("reference_label_A", "slice_reference_label", x0=0.23, y0=0.76, x1=0.30, y1=0.79),
                make_box("reference_label_B", "slice_reference_label", x0=0.58, y0=0.76, x1=0.68, y1=0.79),
                make_box("legend_title", "legend_title", x0=0.36, y0=0.05, x1=0.50, y1=0.08),
                make_box("legend_box", "legend_box", x0=0.28, y0=0.02, x1=0.70, y1=0.08),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.11, y0=0.18, x1=0.35, y1=0.82),
                make_box("panel_B", "panel", x0=0.45, y0=0.18, x1=0.72, y1=0.82),
            ],
            "guide_boxes": [
                make_box("reference_line_A", "slice_reference_line", x0=0.24, y0=0.18, x1=0.241, y1=0.82),
                make_box("reference_line_B", "slice_reference_line", x0=0.59, y0=0.18, x1=0.591, y1=0.82),
            ],
            "metrics": {
                "legend_title": "Conditioning profile",
                "legend_labels": ["Low conditioning", "High conditioning"],
                "panels": [
                    {
                        "panel_id": "age_by_albumin",
                        "panel_label": "A",
                        "title": "Age conditioned on albumin",
                        "x_label": "Age (years)",
                        "x_feature": "Age",
                        "slice_feature": "Albumin",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_A",
                        "reference_line_box_id": "reference_line_A",
                        "reference_label_box_id": "reference_label_A",
                        "slice_curves": [
                            {
                                "slice_id": "albumin_low",
                                "slice_label": "Low conditioning",
                                "conditioning_value": 3.2,
                                "points": [
                                    {"x": 0.15, "y": 0.33},
                                    {"x": 0.21, "y": 0.39},
                                    {"x": 0.24, "y": 0.47},
                                    {"x": 0.30, "y": 0.57},
                                ],
                            },
                            {
                                "slice_id": "albumin_high",
                                "slice_label": "High conditioning",
                                "conditioning_value": 4.4,
                                "points": [
                                    {"x": 0.15, "y": 0.26},
                                    {"x": 0.21, "y": 0.32},
                                    {"x": 0.24, "y": 0.39},
                                    {"x": 0.30, "y": 0.49},
                                ],
                            },
                        ],
                    },
                    {
                        "panel_id": "tumor_by_platelet",
                        "panel_label": "B",
                        "title": "Tumor size conditioned on platelets",
                        "x_label": "Tumor size (cm)",
                        "x_feature": "Tumor size",
                        "slice_feature": "Platelet count",
                        "reference_value": 6.0,
                        "reference_label": "Reference tumor size",
                        "panel_box_id": "panel_B",
                        "reference_line_box_id": "reference_line_B",
                        "reference_label_box_id": "reference_label_B",
                        "slice_curves": [
                            {
                                "slice_id": "platelet_low",
                                "slice_label": "Low conditioning",
                                "conditioning_value": 110.0,
                                "points": [
                                    {"x": 0.49, "y": 0.28},
                                    {"x": 0.55, "y": 0.39},
                                    {"x": 0.59, "y": 0.50},
                                    {"x": 0.67, "y": 0.62},
                                ],
                            },
                            {
                                "slice_id": "platelet_high",
                                "slice_label": "High conditioning",
                                "conditioning_value": 210.0,
                                "points": [
                                    {"x": 0.49, "y": 0.22},
                                    {"x": 0.55, "y": 0.31},
                                    {"x": 0.59, "y": 0.40},
                                    {"x": 0.67, "y": 0.49},
                                ],
                            },
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_partial_dependence_interaction_slice_curve_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_partial_dependence_interaction_slice_panel",
        layout_sidecar={
            "template_id": "partial_dependence_interaction_slice_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.87, x1=0.31, y1=0.90),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.10, x1=0.31, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.32, x1=0.07, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.81, x1=0.14, y1=0.84),
                make_box("reference_label_A", "slice_reference_label", x0=0.23, y0=0.76, x1=0.30, y1=0.79),
                make_box("legend_title", "legend_title", x0=0.36, y0=0.05, x1=0.50, y1=0.08),
                make_box("legend_box", "legend_box", x0=0.28, y0=0.02, x1=0.70, y1=0.08),
            ],
            "panel_boxes": [make_box("panel_A", "panel", x0=0.11, y0=0.18, x1=0.35, y1=0.82)],
            "guide_boxes": [make_box("reference_line_A", "slice_reference_line", x0=0.24, y0=0.18, x1=0.241, y1=0.82)],
            "metrics": {
                "legend_title": "Conditioning profile",
                "legend_labels": ["Low conditioning", "High conditioning"],
                "panels": [
                    {
                        "panel_id": "age_by_albumin",
                        "panel_label": "A",
                        "title": "Age conditioned on albumin",
                        "x_label": "Age (years)",
                        "x_feature": "Age",
                        "slice_feature": "Albumin",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_A",
                        "reference_line_box_id": "reference_line_A",
                        "reference_label_box_id": "reference_label_A",
                        "slice_curves": [
                            {
                                "slice_id": "albumin_low",
                                "slice_label": "Low conditioning",
                                "conditioning_value": 3.2,
                                "points": [
                                    {"x": 0.15, "y": 0.33},
                                    {"x": 0.21, "y": 0.39},
                                    {"x": 0.39, "y": 0.47},
                                    {"x": 0.30, "y": 0.57},
                                ],
                            },
                            {
                                "slice_id": "albumin_high",
                                "slice_label": "High conditioning",
                                "conditioning_value": 4.4,
                                "points": [
                                    {"x": 0.15, "y": 0.26},
                                    {"x": 0.21, "y": 0.32},
                                    {"x": 0.24, "y": 0.39},
                                    {"x": 0.30, "y": 0.49},
                                ],
                            },
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "slice_point_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_partial_dependence_subgroup_comparison_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_partial_dependence_subgroup_comparison_panel",
        layout_sidecar={
            "template_id": "partial_dependence_subgroup_comparison_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.88, x1=0.28, y1=0.91),
                make_box("panel_title_B", "panel_title", x0=0.40, y0=0.88, x1=0.58, y1=0.91),
                make_box("subgroup_panel_title_C", "subgroup_panel_title", x0=0.16, y0=0.42, x1=0.48, y1=0.45),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.14, y0=0.52, x1=0.26, y1=0.55),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.44, y0=0.52, x1=0.56, y1=0.55),
                make_box("subgroup_x_axis_title_C", "subgroup_x_axis_title", x0=0.24, y0=0.08, x1=0.46, y1=0.11),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.58, x1=0.07, y1=0.84),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.82, x1=0.12, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.40, y0=0.82, x1=0.42, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.10, y0=0.38, x1=0.12, y1=0.41),
                make_box("reference_label_A", "pdp_reference_label", x0=0.17, y0=0.77, x1=0.25, y1=0.80),
                make_box("reference_label_B", "pdp_reference_label", x0=0.47, y0=0.77, x1=0.55, y1=0.80),
                make_box("subgroup_row_label_1", "subgroup_row_label", x0=0.12, y0=0.30, x1=0.21, y1=0.33),
                make_box("subgroup_row_label_2", "subgroup_row_label", x0=0.12, y0=0.22, x1=0.20, y1=0.25),
                make_box("legend_box", "legend_box", x0=0.62, y0=0.70, x1=0.90, y1=0.78),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.09, y0=0.56, x1=0.30, y1=0.83),
                make_box("panel_B", "panel", x0=0.39, y0=0.56, x1=0.60, y1=0.83),
                make_box("panel_C", "subgroup_panel", x0=0.24, y0=0.16, x1=0.62, y1=0.36),
            ],
            "guide_boxes": [
                make_box("reference_line_A", "pdp_reference_line", x0=0.19, y0=0.56, x1=0.191, y1=0.83),
                make_box("reference_line_B", "pdp_reference_line", x0=0.49, y0=0.56, x1=0.491, y1=0.83),
                make_box("subgroup_ci_segment_1", "subgroup_ci_segment", x0=0.33, y0=0.31, x1=0.47, y1=0.315),
                make_box("subgroup_ci_segment_2", "subgroup_ci_segment", x0=0.29, y0=0.23, x1=0.41, y1=0.235),
                make_box("subgroup_estimate_marker_1", "subgroup_estimate_marker", x0=0.39, y0=0.298, x1=0.405, y1=0.318),
                make_box("subgroup_estimate_marker_2", "subgroup_estimate_marker", x0=0.34, y0=0.218, x1=0.355, y1=0.238),
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
                        "pdp_points": [
                            {"x": 0.12, "y": 0.63},
                            {"x": 0.17, "y": 0.69},
                            {"x": 0.19, "y": 0.74},
                            {"x": 0.25, "y": 0.79},
                        ],
                        "ice_curves": [
                            {"curve_id": "immune_high_case_1", "points": [{"x": 0.12, "y": 0.61}, {"x": 0.17, "y": 0.67}, {"x": 0.19, "y": 0.73}, {"x": 0.25, "y": 0.80}]},
                            {"curve_id": "immune_high_case_2", "points": [{"x": 0.12, "y": 0.64}, {"x": 0.17, "y": 0.70}, {"x": 0.19, "y": 0.76}, {"x": 0.25, "y": 0.81}]},
                        ],
                    },
                    {
                        "panel_id": "immune_low",
                        "panel_label": "B",
                        "subgroup_label": "Immune-low",
                        "title": "Immune-low subgroup",
                        "x_label": "Age (years)",
                        "feature": "Age",
                        "reference_value": 60.0,
                        "reference_label": "Median age",
                        "panel_box_id": "panel_B",
                        "reference_line_box_id": "reference_line_B",
                        "reference_label_box_id": "reference_label_B",
                        "pdp_points": [
                            {"x": 0.42, "y": 0.60},
                            {"x": 0.47, "y": 0.65},
                            {"x": 0.49, "y": 0.69},
                            {"x": 0.55, "y": 0.74},
                        ],
                        "ice_curves": [
                            {"curve_id": "immune_low_case_1", "points": [{"x": 0.42, "y": 0.58}, {"x": 0.47, "y": 0.63}, {"x": 0.49, "y": 0.68}, {"x": 0.55, "y": 0.73}]},
                            {"curve_id": "immune_low_case_2", "points": [{"x": 0.42, "y": 0.61}, {"x": 0.47, "y": 0.66}, {"x": 0.49, "y": 0.70}, {"x": 0.55, "y": 0.75}]},
                        ],
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
                        {
                            "row_id": "immune_low_row",
                            "panel_id": "immune_low",
                            "row_label": "Immune-low",
                            "estimate": 0.22,
                            "lower": 0.16,
                            "upper": 0.28,
                            "support_n": 151,
                            "label_box_id": "subgroup_row_label_2",
                            "ci_segment_box_id": "subgroup_ci_segment_2",
                            "estimate_marker_box_id": "subgroup_estimate_marker_2",
                        },
                    ],
                },
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []
