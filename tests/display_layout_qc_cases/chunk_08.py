from .shared import *

def test_run_display_layout_qc_fails_when_multicenter_legend_labels_are_not_split_order() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_multicenter_overview",
        layout_sidecar={
            "template_id": "multicenter_generalizability_overview",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.09, y0=0.47, x1=0.12, y1=0.51),
                make_box("panel_label_B", "panel_label", x0=0.09, y0=0.89, x1=0.12, y1=0.93),
                make_box("panel_label_C", "panel_label", x0=0.57, y0=0.89, x1=0.60, y1=0.93),
                make_box("center_event_y_axis_title", "y_axis_title", x0=0.02, y0=0.20, x1=0.05, y1=0.48),
                make_box("coverage_y_axis_title", "y_axis_title", x0=0.02, y0=0.64, x1=0.05, y1=0.92),
                make_box("center_event_bar_1", "center_event_bar", x0=0.10, y0=0.20, x1=0.12, y1=0.42),
                make_box("coverage_bar_region_1", "coverage_bar", x0=0.08, y0=0.64, x1=0.16, y1=0.92),
                make_box("coverage_bar_ns_1", "coverage_bar", x0=0.60, y0=0.64, x1=0.70, y1=0.78),
                make_box("coverage_bar_ur_1", "coverage_bar", x0=0.60, y0=0.82, x1=0.70, y1=0.94),
            ],
            "panel_boxes": [
                make_box("center_event_panel", "center_event_panel", x0=0.08, y0=0.14, x1=0.92, y1=0.52),
                make_box("coverage_panel_wide_left", "coverage_panel", x0=0.08, y0=0.64, x1=0.44, y1=0.94),
                make_box("coverage_panel_top_right", "coverage_panel", x0=0.56, y0=0.58, x1=0.92, y1=0.78),
                make_box("coverage_panel_bottom_right", "coverage_panel", x0=0.56, y0=0.82, x1=0.92, y1=0.94),
                make_box("coverage_panel_right_stack", "coverage_panel", x0=0.56, y0=0.58, x1=0.92, y1=0.94),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.40, y0=0.02, x1=0.62, y1=0.08),
            ],
            "metrics": {
                "center_event_counts": [
                    {"center_label": "Center 01", "split_bucket": "validation", "event_count": 2},
                    {"center_label": "Center 02", "split_bucket": "validation", "event_count": 1},
                    {"center_label": "Center 25", "split_bucket": "train", "event_count": 3},
                ],
                "coverage_panels": [
                    {"panel_id": "region", "title": "Region coverage", "layout_role": "wide_left", "bars": [{"label": "Central", "count": 72}]},
                    {"panel_id": "north_south", "title": "North vs South", "layout_role": "top_right", "bars": [{"label": "North", "count": 84}]},
                    {"panel_id": "urban_rural", "title": "Urban/rural", "layout_role": "bottom_right", "bars": [{"label": "Urban", "count": 101}]},
                ],
                "legend_title": "Split",
                "legend_labels": ["Validation", "Train"],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "legend_labels_invalid" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_binary_calibration_axis_window_is_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_binary_calibration_decision_curve",
        layout_sidecar={
            "template_id": "binary_calibration_decision_curve_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.94, x1=0.90, y1=0.98),
                make_box("calibration_subplot_title", "subplot_title", x0=0.20, y0=0.86, x1=0.38, y1=0.89),
                make_box("decision_subplot_title", "subplot_title", x0=0.62, y0=0.86, x1=0.82, y1=0.89),
                make_box("calibration_x_axis_title", "subplot_x_axis_title", x0=0.18, y0=0.12, x1=0.42, y1=0.16),
                make_box("calibration_y_axis_title", "subplot_y_axis_title", x0=0.04, y0=0.28, x1=0.07, y1=0.74),
                make_box("decision_x_axis_title", "subplot_x_axis_title", x0=0.64, y0=0.12, x1=0.86, y1=0.16),
                make_box("decision_y_axis_title", "subplot_y_axis_title", x0=0.54, y0=0.34, x1=0.57, y1=0.68),
            ],
            "panel_boxes": [
                make_box("calibration_panel", "calibration_panel", x0=0.10, y0=0.22, x1=0.48, y1=0.84),
                make_box("decision_panel", "decision_panel", x0=0.58, y0=0.22, x1=0.96, y1=0.84),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.18, y0=0.03, x1=0.82, y1=0.14),
                make_box("decision_focus_window", "focus_window", x0=0.60, y0=0.22, x1=0.92, y1=0.84),
            ],
            "metrics": {
                "calibration_series": [{"label": "Core", "x": [0.1, 0.2], "y": [0.05, 0.10]}],
                "calibration_reference_line": {"label": "Ideal", "x": [0.0, 0.5], "y": [0.0, 0.5]},
                "decision_series": [{"label": "Core", "x": [0.15, 0.20], "y": [0.01, 0.0]}],
                "decision_reference_lines": [{"label": "Treat none", "x": [0.15, 0.20], "y": [0.0, 0.0]}],
                "decision_focus_window": {"xmin": 0.15, "xmax": 0.35},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "calibration_axis_window_missing" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_graphical_abstract_arrow_is_far_above_midline() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="submission_graphical_abstract",
        layout_sidecar={
            "template_id": "submission_graphical_abstract",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.70, y1=0.08),
                make_box("panel_label_A", "panel_label", x0=0.05, y0=0.18, x1=0.08, y1=0.22),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.18, x1=0.41, y1=0.22),
                make_box("panel_label_C", "panel_label", x0=0.71, y0=0.18, x1=0.74, y1=0.22),
                make_box("panel_a_title", "panel_title", x0=0.09, y0=0.18, x1=0.23, y1=0.22),
                make_box("panel_b_title", "panel_title", x0=0.42, y0=0.18, x1=0.56, y1=0.22),
                make_box("panel_c_title", "panel_title", x0=0.75, y0=0.18, x1=0.89, y1=0.22),
                make_box("card_a", "card_box", x0=0.07, y0=0.28, x1=0.29, y1=0.70),
                make_box("card_b", "card_box", x0=0.40, y0=0.28, x1=0.62, y1=0.70),
                make_box("card_c", "card_box", x0=0.73, y0=0.28, x1=0.95, y1=0.70),
                make_box("pill_a", "footer_pill", x0=0.11, y0=0.84, x1=0.25, y1=0.89),
                make_box("pill_b", "footer_pill", x0=0.44, y0=0.84, x1=0.58, y1=0.89),
                make_box("pill_c", "footer_pill", x0=0.77, y0=0.84, x1=0.92, y1=0.89),
            ],
            "panel_boxes": [
                make_box("panel_a", "panel", x0=0.03, y0=0.12, x1=0.31, y1=0.80),
                make_box("panel_b", "panel", x0=0.36, y0=0.12, x1=0.64, y1=0.80),
                make_box("panel_c", "panel", x0=0.69, y0=0.12, x1=0.97, y1=0.80),
            ],
            "guide_boxes": [
                make_box("arrow_1", "arrow_connector", x0=0.31, y0=0.10, x1=0.36, y1=0.14),
                make_box("arrow_2", "arrow_connector", x0=0.64, y0=0.10, x1=0.69, y1=0.14),
            ],
            "metrics": {
                "panels": [{"panel_id": "A"}, {"panel_id": "B"}, {"panel_id": "C"}],
                "footer_pills": [
                    {"pill_id": "p1", "panel_id": "A", "label": "Internal validation only"},
                    {"pill_id": "p2", "panel_id": "B", "label": "Supportive endpoint retained"},
                    {"pill_id": "p3", "panel_id": "C", "label": "No external validation"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "arrow_midline_alignment" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_graphical_abstract_arrow_pairs_use_different_horizontal_lanes() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="submission_graphical_abstract",
        layout_sidecar={
            "template_id": "submission_graphical_abstract",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.70, y1=0.08),
                make_box("panel_label_A", "panel_label", x0=0.05, y0=0.18, x1=0.08, y1=0.22),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.18, x1=0.41, y1=0.22),
                make_box("panel_label_C", "panel_label", x0=0.71, y0=0.18, x1=0.74, y1=0.22),
                make_box("panel_a_title", "panel_title", x0=0.09, y0=0.18, x1=0.23, y1=0.22),
                make_box("panel_b_title", "panel_title", x0=0.42, y0=0.18, x1=0.56, y1=0.22),
                make_box("panel_c_title", "panel_title", x0=0.75, y0=0.18, x1=0.89, y1=0.22),
                make_box("card_a", "card_box", x0=0.07, y0=0.28, x1=0.29, y1=0.70),
                make_box("card_b", "card_box", x0=0.40, y0=0.28, x1=0.62, y1=0.70),
                make_box("card_c", "card_box", x0=0.73, y0=0.28, x1=0.95, y1=0.70),
                make_box("pill_a", "footer_pill", x0=0.11, y0=0.84, x1=0.25, y1=0.89),
                make_box("pill_b", "footer_pill", x0=0.44, y0=0.84, x1=0.58, y1=0.89),
                make_box("pill_c", "footer_pill", x0=0.77, y0=0.84, x1=0.92, y1=0.89),
            ],
            "panel_boxes": [
                make_box("panel_a", "panel", x0=0.03, y0=0.12, x1=0.31, y1=0.80),
                make_box("panel_b", "panel", x0=0.36, y0=0.12, x1=0.64, y1=0.80),
                make_box("panel_c", "panel", x0=0.69, y0=0.12, x1=0.97, y1=0.80),
            ],
            "guide_boxes": [
                make_box("arrow_1", "arrow_connector", x0=0.31, y0=0.43, x1=0.36, y1=0.47),
                make_box("arrow_2", "arrow_connector", x0=0.64, y0=0.54, x1=0.69, y1=0.58),
            ],
            "metrics": {
                "panels": [{"panel_id": "A"}, {"panel_id": "B"}, {"panel_id": "C"}],
                "footer_pills": [
                    {"pill_id": "p1", "panel_id": "A", "label": "Internal validation only"},
                    {"pill_id": "p2", "panel_id": "B", "label": "Supportive endpoint retained"},
                    {"pill_id": "p3", "panel_id": "C", "label": "No external validation"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "arrow_cross_pair_misalignment" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_shap_feature_rows_overlap() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.56, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.03, y0=0.25, x1=0.12, y1=0.31),
                make_box("feature_label_ki67", "feature_label", x0=0.03, y0=0.36, x1=0.12, y1=0.42),
                make_box("zero_line", "zero_line", x0=0.48, y0=0.18, x1=0.48, y1=0.84),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.24, x1=0.76, y1=0.36),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.33, x1=0.76, y1=0.45),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("colorbar", "colorbar", x0=0.82, y0=0.22, x1=0.90, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "points": [
                    {"feature": "Age", "y": 0.28},
                    {"feature": "Ki-67", "y": 0.39},
                ],
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_ki67", "label_box_id": "feature_label_ki67"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "feature_row_overlap" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_atlas_spatial_trajectory_context_support_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_trajectory_context_support_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_trajectory_context_support_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.16, y0=0.95, x1=0.84, y1=0.98),
                make_box("atlas_panel_title", "panel_title", x0=0.06, y0=0.88, x1=0.23, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.10, y0=0.52, x1=0.20, y1=0.55),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.01, y0=0.65, x1=0.04, y1=0.79),
                make_box("spatial_panel_title", "panel_title", x0=0.37, y0=0.88, x1=0.54, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.40, y0=0.52, x1=0.54, y1=0.55),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.31, y0=0.62, x1=0.34, y1=0.80),
                make_box("trajectory_panel_title", "panel_title", x0=0.67, y0=0.88, x1=0.85, y1=0.91),
                make_box("trajectory_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.52, x1=0.84, y1=0.55),
                make_box("trajectory_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.62, x1=0.65, y1=0.80),
                make_box("composition_panel_title", "panel_title", x0=0.06, y0=0.46, x1=0.25, y1=0.49),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.08, y0=0.10, x1=0.23, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.01, y0=0.20, x1=0.04, y1=0.39),
                make_box("heatmap_panel_title", "panel_title", x0=0.36, y0=0.46, x1=0.56, y1=0.49),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.39, y0=0.10, x1=0.53, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.30, y0=0.20, x1=0.33, y1=0.39),
                make_box("support_panel_title", "panel_title", x0=0.68, y0=0.46, x1=0.88, y1=0.49),
                make_box("support_x_axis_title", "subplot_x_axis_title", x0=0.74, y0=0.10, x1=0.84, y1=0.13),
                make_box("support_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.20, x1=0.65, y1=0.39),
                make_box("panel_label_A", "panel_label", x0=0.05, y0=0.82, x1=0.07, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.35, y0=0.82, x1=0.37, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.65, y0=0.82, x1=0.67, y1=0.85),
                make_box("panel_label_D", "panel_label", x0=0.05, y0=0.40, x1=0.07, y1=0.43),
                make_box("panel_label_E", "panel_label", x0=0.35, y0=0.40, x1=0.37, y1=0.43),
                make_box("panel_label_F", "panel_label", x0=0.65, y0=0.40, x1=0.67, y1=0.43),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.05, y0=0.56, x1=0.28, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.35, y0=0.56, x1=0.58, y1=0.86),
                make_box("panel_trajectory", "panel", x0=0.65, y0=0.56, x1=0.88, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.05, y0=0.16, x1=0.28, y1=0.44),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.35, y0=0.16, x1=0.58, y1=0.44),
                make_box("panel_support", "heatmap_tile_region", x0=0.67, y0=0.16, x1=0.90, y1=0.44),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.06, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.60, y0=0.18, x1=0.63, y1=0.42),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.09, "y": 0.80, "state_label": "Stem-like"},
                    {"x": 0.13, "y": 0.74, "state_label": "Stem-like"},
                    {"x": 0.20, "y": 0.68, "state_label": "Cycling"},
                    {"x": 0.25, "y": 0.61, "state_label": "Effector"},
                ],
                "spatial_points": [
                    {"x": 0.38, "y": 0.80, "state_label": "Stem-like"},
                    {"x": 0.42, "y": 0.75, "state_label": "Stem-like"},
                    {"x": 0.50, "y": 0.68, "state_label": "Cycling"},
                    {"x": 0.55, "y": 0.61, "state_label": "Effector"},
                ],
                "trajectory_points": [
                    {"x": 0.69, "y": 0.80, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
                    {"x": 0.74, "y": 0.73, "branch_label": "Branch A", "state_label": "Cycling", "pseudotime": 0.34},
                    {"x": 0.82, "y": 0.61, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.76},
                    {"x": 0.86, "y": 0.79, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
                    {"x": 0.82, "y": 0.70, "branch_label": "Branch B", "state_label": "Cycling", "pseudotime": 0.52},
                    {"x": 0.76, "y": 0.59, "branch_label": "Branch B", "state_label": "Effector", "pseudotime": 0.88},
                ],
                "state_labels": ["Stem-like", "Cycling", "Effector"],
                "branch_labels": ["Branch A", "Branch B"],
                "bin_labels": ["Early", "Mid", "Late"],
                "row_labels": ["IFN response", "EMT module"],
                "context_labels": ["Atlas density", "Spatial coverage", "Trajectory coverage"],
                "context_kinds": ["atlas_density", "spatial_coverage", "trajectory_coverage"],
                "composition_groups": [
                    {
                        "group_label": "Tumor core",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "Stem-like", "proportion": 0.48},
                            {"state_label": "Cycling", "proportion": 0.32},
                            {"state_label": "Effector", "proportion": 0.20},
                        ],
                    },
                    {
                        "group_label": "Invasive margin",
                        "group_order": 2,
                        "state_proportions": [
                            {"state_label": "Stem-like", "proportion": 0.18},
                            {"state_label": "Cycling", "proportion": 0.34},
                            {"state_label": "Effector", "proportion": 0.48},
                        ],
                    },
                ],
                "progression_bins": [
                    {
                        "bin_label": "Early",
                        "bin_order": 1,
                        "pseudotime_start": 0.0,
                        "pseudotime_end": 0.33,
                        "branch_weights": [
                            {"branch_label": "Branch A", "proportion": 0.58},
                            {"branch_label": "Branch B", "proportion": 0.42},
                        ],
                    },
                    {
                        "bin_label": "Mid",
                        "bin_order": 2,
                        "pseudotime_start": 0.33,
                        "pseudotime_end": 0.67,
                        "branch_weights": [
                            {"branch_label": "Branch A", "proportion": 0.46},
                            {"branch_label": "Branch B", "proportion": 0.54},
                        ],
                    },
                    {
                        "bin_label": "Late",
                        "bin_order": 3,
                        "pseudotime_start": 0.67,
                        "pseudotime_end": 1.0,
                        "branch_weights": [
                            {"branch_label": "Branch A", "proportion": 0.39},
                            {"branch_label": "Branch B", "proportion": 0.61},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "Early", "y": "IFN response", "value": 0.74},
                    {"x": "Mid", "y": "IFN response", "value": 0.26},
                    {"x": "Late", "y": "IFN response", "value": -0.14},
                    {"x": "Early", "y": "EMT module", "value": -0.28},
                    {"x": "Mid", "y": "EMT module", "value": 0.18},
                    {"x": "Late", "y": "EMT module", "value": 0.72},
                ],
                "support_cells": [
                    {"x": "Atlas density", "y": "Stem-like", "value": 0.84},
                    {"x": "Spatial coverage", "y": "Stem-like", "value": 0.73},
                    {"x": "Trajectory coverage", "y": "Stem-like", "value": 0.58},
                    {"x": "Atlas density", "y": "Cycling", "value": 0.49},
                    {"x": "Spatial coverage", "y": "Cycling", "value": 0.61},
                    {"x": "Trajectory coverage", "y": "Cycling", "value": 0.66},
                    {"x": "Atlas density", "y": "Effector", "value": 0.31},
                    {"x": "Spatial coverage", "y": "Effector", "value": 0.54},
                    {"x": "Trajectory coverage", "y": "Effector", "value": 0.81},
                ],
                "score_method": "GSVA",
                "support_scale_label": "Coverage fraction",
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_context_support_grid_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_trajectory_context_support_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_trajectory_context_support_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.16, y0=0.95, x1=0.84, y1=0.98),
                make_box("atlas_panel_title", "panel_title", x0=0.06, y0=0.88, x1=0.23, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.10, y0=0.52, x1=0.20, y1=0.55),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.01, y0=0.65, x1=0.04, y1=0.79),
                make_box("spatial_panel_title", "panel_title", x0=0.37, y0=0.88, x1=0.54, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.40, y0=0.52, x1=0.54, y1=0.55),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.31, y0=0.62, x1=0.34, y1=0.80),
                make_box("trajectory_panel_title", "panel_title", x0=0.67, y0=0.88, x1=0.85, y1=0.91),
                make_box("trajectory_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.52, x1=0.84, y1=0.55),
                make_box("trajectory_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.62, x1=0.65, y1=0.80),
                make_box("composition_panel_title", "panel_title", x0=0.06, y0=0.46, x1=0.25, y1=0.49),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.08, y0=0.10, x1=0.23, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.01, y0=0.20, x1=0.04, y1=0.39),
                make_box("heatmap_panel_title", "panel_title", x0=0.36, y0=0.46, x1=0.56, y1=0.49),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.39, y0=0.10, x1=0.53, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.30, y0=0.20, x1=0.33, y1=0.39),
                make_box("support_panel_title", "panel_title", x0=0.68, y0=0.46, x1=0.88, y1=0.49),
                make_box("support_x_axis_title", "subplot_x_axis_title", x0=0.74, y0=0.10, x1=0.84, y1=0.13),
                make_box("support_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.20, x1=0.65, y1=0.39),
                make_box("panel_label_A", "panel_label", x0=0.05, y0=0.82, x1=0.07, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.35, y0=0.82, x1=0.37, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.65, y0=0.82, x1=0.67, y1=0.85),
                make_box("panel_label_D", "panel_label", x0=0.05, y0=0.40, x1=0.07, y1=0.43),
                make_box("panel_label_E", "panel_label", x0=0.35, y0=0.40, x1=0.37, y1=0.43),
                make_box("panel_label_F", "panel_label", x0=0.65, y0=0.40, x1=0.67, y1=0.43),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.05, y0=0.56, x1=0.28, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.35, y0=0.56, x1=0.58, y1=0.86),
                make_box("panel_trajectory", "panel", x0=0.65, y0=0.56, x1=0.88, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.05, y0=0.16, x1=0.28, y1=0.44),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.35, y0=0.16, x1=0.58, y1=0.44),
                make_box("panel_support", "heatmap_tile_region", x0=0.67, y0=0.16, x1=0.90, y1=0.44),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.06, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.60, y0=0.18, x1=0.63, y1=0.42),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.09, "y": 0.80, "state_label": "Stem-like"},
                    {"x": 0.13, "y": 0.74, "state_label": "Stem-like"},
                    {"x": 0.20, "y": 0.68, "state_label": "Cycling"},
                    {"x": 0.25, "y": 0.61, "state_label": "Effector"},
                ],
                "spatial_points": [
                    {"x": 0.38, "y": 0.80, "state_label": "Stem-like"},
                    {"x": 0.42, "y": 0.75, "state_label": "Stem-like"},
                    {"x": 0.50, "y": 0.68, "state_label": "Cycling"},
                    {"x": 0.55, "y": 0.61, "state_label": "Effector"},
                ],
                "trajectory_points": [
                    {"x": 0.69, "y": 0.80, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
                    {"x": 0.74, "y": 0.73, "branch_label": "Branch A", "state_label": "Cycling", "pseudotime": 0.34},
                    {"x": 0.82, "y": 0.61, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.76},
                    {"x": 0.86, "y": 0.79, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
                    {"x": 0.82, "y": 0.70, "branch_label": "Branch B", "state_label": "Cycling", "pseudotime": 0.52},
                    {"x": 0.76, "y": 0.59, "branch_label": "Branch B", "state_label": "Effector", "pseudotime": 0.88},
                ],
                "state_labels": ["Stem-like", "Cycling", "Effector"],
                "branch_labels": ["Branch A", "Branch B"],
                "bin_labels": ["Early", "Mid", "Late"],
                "row_labels": ["IFN response", "EMT module"],
                "context_labels": ["Atlas density", "Spatial coverage", "Trajectory coverage"],
                "context_kinds": ["atlas_density", "spatial_coverage", "trajectory_coverage"],
                "composition_groups": [
                    {
                        "group_label": "Tumor core",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "Stem-like", "proportion": 0.48},
                            {"state_label": "Cycling", "proportion": 0.32},
                            {"state_label": "Effector", "proportion": 0.20},
                        ],
                    },
                    {
                        "group_label": "Invasive margin",
                        "group_order": 2,
                        "state_proportions": [
                            {"state_label": "Stem-like", "proportion": 0.18},
                            {"state_label": "Cycling", "proportion": 0.34},
                            {"state_label": "Effector", "proportion": 0.48},
                        ],
                    },
                ],
                "progression_bins": [
                    {
                        "bin_label": "Early",
                        "bin_order": 1,
                        "pseudotime_start": 0.0,
                        "pseudotime_end": 0.33,
                        "branch_weights": [
                            {"branch_label": "Branch A", "proportion": 0.58},
                            {"branch_label": "Branch B", "proportion": 0.42},
                        ],
                    },
                    {
                        "bin_label": "Mid",
                        "bin_order": 2,
                        "pseudotime_start": 0.33,
                        "pseudotime_end": 0.67,
                        "branch_weights": [
                            {"branch_label": "Branch A", "proportion": 0.46},
                            {"branch_label": "Branch B", "proportion": 0.54},
                        ],
                    },
                    {
                        "bin_label": "Late",
                        "bin_order": 3,
                        "pseudotime_start": 0.67,
                        "pseudotime_end": 1.0,
                        "branch_weights": [
                            {"branch_label": "Branch A", "proportion": 0.39},
                            {"branch_label": "Branch B", "proportion": 0.61},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "Early", "y": "IFN response", "value": 0.74},
                    {"x": "Mid", "y": "IFN response", "value": 0.26},
                    {"x": "Late", "y": "IFN response", "value": -0.14},
                    {"x": "Early", "y": "EMT module", "value": -0.28},
                    {"x": "Mid", "y": "EMT module", "value": 0.18},
                    {"x": "Late", "y": "EMT module", "value": 0.72},
                ],
                "support_cells": [
                    {"x": "Atlas density", "y": "Stem-like", "value": 0.84},
                    {"x": "Spatial coverage", "y": "Stem-like", "value": 0.73},
                    {"x": "Trajectory coverage", "y": "Stem-like", "value": 0.58},
                    {"x": "Atlas density", "y": "Cycling", "value": 0.49},
                    {"x": "Spatial coverage", "y": "Cycling", "value": 0.61},
                    {"x": "Trajectory coverage", "y": "Cycling", "value": 0.66},
                    {"x": "Atlas density", "y": "Effector", "value": 0.31},
                    {"x": "Spatial coverage", "y": "Effector", "value": 0.54},
                ],
                "score_method": "GSVA",
                "support_scale_label": "Coverage fraction",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "support_grid_incomplete" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_shap_summary_without_figure_title_by_default() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.03, y0=0.25, x1=0.12, y1=0.31),
                make_box("feature_label_ki67", "feature_label", x0=0.03, y0=0.41, x1=0.12, y1=0.47),
                make_box("zero_line", "zero_line", x0=0.48, y0=0.18, x1=0.48, y1=0.84),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.24, x1=0.76, y1=0.36),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.40, x1=0.76, y1=0.52),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("colorbar", "colorbar", x0=0.82, y0=0.22, x1=0.90, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "points": [
                    {"row_box_id": "feature_row_age", "x": 0.42, "y": 0.28},
                    {"row_box_id": "feature_row_ki67", "x": 0.58, "y": 0.46},
                ],
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_ki67", "label_box_id": "feature_label_ki67"},
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_shap_feature_label_overlaps_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.56, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.08, y0=0.25, x1=0.18, y1=0.31),
                make_box("feature_label_ki67", "feature_label", x0=0.08, y0=0.43, x1=0.18, y1=0.49),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.24, x1=0.76, y1=0.36),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.40, x1=0.76, y1=0.52),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.48, y0=0.18, x1=0.48, y1=0.84),
                make_box("colorbar", "colorbar", x0=0.82, y0=0.22, x1=0.90, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_ki67", "label_box_id": "feature_label_ki67"},
                ],
                "points": [
                    {"row_box_id": "feature_row_age", "x": 0.42, "y": 0.28},
                    {"row_box_id": "feature_row_ki67", "x": 0.58, "y": 0.46},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "feature_label_panel_overlap" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_shap_feature_label_panel_gap_is_not_readable() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.56, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.10, y0=0.25, x1=0.135, y1=0.31),
                make_box("feature_label_ki67", "feature_label", x0=0.10, y0=0.43, x1=0.135, y1=0.49),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.24, x1=0.76, y1=0.36),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.40, x1=0.76, y1=0.52),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.48, y0=0.18, x1=0.48, y1=0.84),
                make_box("colorbar", "colorbar", x0=0.82, y0=0.22, x1=0.90, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_ki67", "label_box_id": "feature_label_ki67"},
                ],
                "points": [
                    {"row_box_id": "feature_row_age", "x": 0.42, "y": 0.28},
                    {"row_box_id": "feature_row_ki67", "x": 0.58, "y": 0.46},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "feature_label_panel_gap_not_readable" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_shap_colorbar_overlaps_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.56, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.03, y0=0.25, x1=0.12, y1=0.31),
                make_box("feature_label_ki67", "feature_label", x0=0.03, y0=0.43, x1=0.12, y1=0.49),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.24, x1=0.76, y1=0.36),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.40, x1=0.76, y1=0.52),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.48, y0=0.18, x1=0.48, y1=0.84),
                make_box("colorbar", "colorbar", x0=0.72, y0=0.22, x1=0.82, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_ki67", "label_box_id": "feature_label_ki67"},
                ],
                "points": [
                    {"row_box_id": "feature_row_age", "x": 0.42, "y": 0.28},
                    {"row_box_id": "feature_row_ki67", "x": 0.58, "y": 0.46},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "colorbar_panel_overlap" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_shap_zero_line_leaves_panel_band() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.56, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.03, y0=0.25, x1=0.12, y1=0.31),
                make_box("feature_label_ki67", "feature_label", x0=0.03, y0=0.43, x1=0.12, y1=0.49),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.24, x1=0.76, y1=0.36),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.40, x1=0.76, y1=0.52),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.48, y0=0.12, x1=0.48, y1=0.90),
                make_box("colorbar", "colorbar", x0=0.82, y0=0.22, x1=0.90, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_ki67", "label_box_id": "feature_label_ki67"},
                ],
                "points": [
                    {"row_box_id": "feature_row_age", "x": 0.42, "y": 0.28},
                    {"row_box_id": "feature_row_ki67", "x": 0.58, "y": 0.46},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "zero_line_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_shap_feature_row_leaves_panel_band() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.56, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.03, y0=0.25, x1=0.12, y1=0.31),
                make_box("feature_label_ki67", "feature_label", x0=0.03, y0=0.43, x1=0.12, y1=0.49),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.12, x1=0.76, y1=0.36),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.40, x1=0.76, y1=0.90),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.48, y0=0.18, x1=0.48, y1=0.84),
                make_box("colorbar", "colorbar", x0=0.82, y0=0.22, x1=0.90, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_ki67", "label_box_id": "feature_label_ki67"},
                ],
                "points": [
                    {"row_box_id": "feature_row_age", "x": 0.42, "y": 0.28},
                    {"row_box_id": "feature_row_ki67", "x": 0.58, "y": 0.46},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "feature_row_outside_panel" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_shap_feature_rows_are_too_dense_for_readability() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.56, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.03, y0=0.25, x1=0.12, y1=0.31),
                make_box("feature_label_ki67", "feature_label", x0=0.03, y0=0.34, x1=0.12, y1=0.40),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.24, x1=0.76, y1=0.32),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.33, x1=0.76, y1=0.41),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.48, y0=0.18, x1=0.48, y1=0.84),
                make_box("colorbar", "colorbar", x0=0.82, y0=0.22, x1=0.90, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "points": [
                    {"row_box_id": "feature_row_age", "x": 0.42, "y": 0.28},
                    {"row_box_id": "feature_row_ki67", "x": 0.58, "y": 0.37},
                ],
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_ki67", "label_box_id": "feature_label_ki67"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "feature_row_height_not_readable" for issue in result["issues"])
    assert any(issue["rule_id"] == "feature_row_gap_not_readable" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_shap_feature_label_is_missing_for_row() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.56, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.03, y0=0.25, x1=0.12, y1=0.31),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.24, x1=0.76, y1=0.36),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.40, x1=0.76, y1=0.52),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.48, y0=0.18, x1=0.48, y1=0.84),
                make_box("colorbar", "colorbar", x0=0.82, y0=0.22, x1=0.90, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "points": [
                    {"row_box_id": "feature_row_age", "x": 0.42, "y": 0.30},
                    {"row_box_id": "feature_row_ki67", "x": 0.58, "y": 0.46},
                ],
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "feature_label_missing" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_shap_feature_label_leaves_its_row_band() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_shap_summary",
        layout_sidecar={
            "template_id": "shap_summary_beeswarm",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.56, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("feature_label_age", "feature_label", x0=0.03, y0=0.09, x1=0.12, y1=0.15),
                make_box("feature_label_ki67", "feature_label", x0=0.03, y0=0.41, x1=0.12, y1=0.47),
                make_box("feature_row_age", "feature_row", x0=0.14, y0=0.24, x1=0.76, y1=0.36),
                make_box("feature_row_ki67", "feature_row", x0=0.14, y0=0.40, x1=0.76, y1=0.52),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.14, y0=0.18, x1=0.76, y1=0.84),
            ],
            "guide_boxes": [
                make_box("zero_line", "zero_line", x0=0.48, y0=0.18, x1=0.48, y1=0.84),
                make_box("colorbar", "colorbar", x0=0.82, y0=0.22, x1=0.90, y1=0.80),
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "points": [
                    {"row_box_id": "feature_row_age", "x": 0.42, "y": 0.30},
                    {"row_box_id": "feature_row_ki67", "x": 0.58, "y": 0.46},
                ],
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_age", "label_box_id": "feature_label_age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_ki67", "label_box_id": "feature_label_ki67"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "feature_label_row_misaligned" for issue in result["issues"])
