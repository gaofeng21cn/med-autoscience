from .shared import *

def test_run_display_layout_qc_fails_when_trajectory_progression_bin_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_trajectory_progression_panel",
        layout_sidecar={
            "template_id": "trajectory_progression_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("trajectory_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.28, y1=0.91),
                make_box("trajectory_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.10, x1=0.24, y1=0.13),
                make_box("trajectory_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.28, x1=0.05, y1=0.76),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.60, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.42, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.26, x1=0.36, y1=0.78),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.85, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_trajectory", "panel", x0=0.07, y0=0.18, x1=0.30, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.11, "y": 0.72, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
                    {"x": 0.17, "y": 0.60, "branch_label": "Branch A", "state_label": "Intermediate", "pseudotime": 0.36},
                    {"x": 0.25, "y": 0.34, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.74},
                    {"x": 0.28, "y": 0.76, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
                    {"x": 0.24, "y": 0.52, "branch_label": "Branch B", "state_label": "Intermediate", "pseudotime": 0.48},
                    {"x": 0.20, "y": 0.26, "branch_label": "Branch B", "state_label": "Terminal", "pseudotime": 0.86},
                ],
                "branch_labels": ["Branch A", "Branch B"],
                "bin_labels": ["Early", "Mid", "Late"],
                "row_labels": ["Interferon module", "EMT module"],
                "progression_bins": [
                    {
                        "bin_label": "Early",
                        "bin_order": 1,
                        "pseudotime_start": 0.0,
                        "pseudotime_end": 0.33,
                        "branch_weights": [
                            {"branch_label": "Branch A", "proportion": 0.56},
                            {"branch_label": "Branch B", "proportion": 0.44},
                        ],
                    },
                    {
                        "bin_label": "Mid",
                        "bin_order": 2,
                        "pseudotime_start": 0.33,
                        "pseudotime_end": 0.67,
                        "branch_weights": [
                            {"branch_label": "Branch A", "proportion": 0.49},
                        ],
                    },
                    {
                        "bin_label": "Late",
                        "bin_order": 3,
                        "pseudotime_start": 0.67,
                        "pseudotime_end": 1.0,
                        "branch_weights": [
                            {"branch_label": "Branch A", "proportion": 0.38},
                            {"branch_label": "Branch B", "proportion": 0.62},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "Early", "y": "Interferon module", "value": 0.72},
                    {"x": "Mid", "y": "Interferon module", "value": 0.28},
                    {"x": "Late", "y": "Interferon module", "value": -0.18},
                    {"x": "Early", "y": "EMT module", "value": -0.31},
                    {"x": "Mid", "y": "EMT module", "value": 0.22},
                    {"x": "Late", "y": "EMT module", "value": 0.68},
                ],
                "score_method": "GSVA",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "progression_bin_branch_set_mismatch" for issue in result["issues"])
    assert any(issue["rule_id"] == "progression_bin_sum_invalid" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_atlas_spatial_trajectory_storyboard_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_trajectory_storyboard_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_trajectory_storyboard_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.95, x1=0.84, y1=0.98),
                make_box("atlas_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.24, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.52, x1=0.22, y1=0.55),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.66, x1=0.05, y1=0.80),
                make_box("spatial_panel_title", "panel_title", x0=0.39, y0=0.88, x1=0.56, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.41, y0=0.52, x1=0.55, y1=0.55),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.62, x1=0.36, y1=0.82),
                make_box("trajectory_panel_title", "panel_title", x0=0.69, y0=0.88, x1=0.87, y1=0.91),
                make_box("trajectory_x_axis_title", "subplot_x_axis_title", x0=0.72, y0=0.52, x1=0.86, y1=0.55),
                make_box("trajectory_y_axis_title", "subplot_y_axis_title", x0=0.63, y0=0.60, x1=0.66, y1=0.82),
                make_box("composition_panel_title", "panel_title", x0=0.18, y0=0.48, x1=0.39, y1=0.51),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.21, y0=0.10, x1=0.37, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.10, y0=0.24, x1=0.13, y1=0.42),
                make_box("heatmap_panel_title", "panel_title", x0=0.58, y0=0.48, x1=0.77, y1=0.51),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.61, y0=0.10, x1=0.75, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.50, y0=0.22, x1=0.53, y1=0.42),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
                make_box("panel_label_D", "panel_label", x0=0.18, y0=0.42, x1=0.20, y1=0.45),
                make_box("panel_label_E", "panel_label", x0=0.58, y0=0.42, x1=0.60, y1=0.45),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.07, y0=0.56, x1=0.30, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.37, y0=0.56, x1=0.60, y1=0.86),
                make_box("panel_trajectory", "panel", x0=0.67, y0=0.56, x1=0.90, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.17, y0=0.18, x1=0.42, y1=0.46),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.57, y0=0.18, x1=0.82, y1=0.46),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.08, y0=0.02, x1=0.42, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.86, y0=0.20, x1=0.90, y1=0.44),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.10, "y": 0.80, "state_label": "Stem-like"},
                    {"x": 0.14, "y": 0.74, "state_label": "Stem-like"},
                    {"x": 0.22, "y": 0.68, "state_label": "Cycling"},
                    {"x": 0.27, "y": 0.61, "state_label": "Effector"},
                ],
                "spatial_points": [
                    {"x": 0.40, "y": 0.81, "state_label": "Stem-like"},
                    {"x": 0.43, "y": 0.75, "state_label": "Stem-like"},
                    {"x": 0.51, "y": 0.69, "state_label": "Cycling"},
                    {"x": 0.57, "y": 0.61, "state_label": "Effector"},
                ],
                "trajectory_points": [
                    {"x": 0.70, "y": 0.81, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
                    {"x": 0.75, "y": 0.73, "branch_label": "Branch A", "state_label": "Cycling", "pseudotime": 0.32},
                    {"x": 0.83, "y": 0.62, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.76},
                    {"x": 0.88, "y": 0.79, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
                    {"x": 0.84, "y": 0.69, "branch_label": "Branch B", "state_label": "Cycling", "pseudotime": 0.51},
                    {"x": 0.78, "y": 0.59, "branch_label": "Branch B", "state_label": "Effector", "pseudotime": 0.88},
                ],
                "state_labels": ["Stem-like", "Cycling", "Effector"],
                "branch_labels": ["Branch A", "Branch B"],
                "bin_labels": ["Early", "Mid", "Late"],
                "row_labels": ["IFN response", "EMT module"],
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
                "score_method": "GSVA",
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_storyboard_trajectory_state_drifts() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_trajectory_storyboard_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_trajectory_storyboard_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.95, x1=0.84, y1=0.98),
                make_box("atlas_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.24, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.52, x1=0.22, y1=0.55),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.66, x1=0.05, y1=0.80),
                make_box("spatial_panel_title", "panel_title", x0=0.39, y0=0.88, x1=0.56, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.41, y0=0.52, x1=0.55, y1=0.55),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.62, x1=0.36, y1=0.82),
                make_box("trajectory_panel_title", "panel_title", x0=0.69, y0=0.88, x1=0.87, y1=0.91),
                make_box("trajectory_x_axis_title", "subplot_x_axis_title", x0=0.72, y0=0.52, x1=0.86, y1=0.55),
                make_box("trajectory_y_axis_title", "subplot_y_axis_title", x0=0.63, y0=0.60, x1=0.66, y1=0.82),
                make_box("composition_panel_title", "panel_title", x0=0.18, y0=0.48, x1=0.39, y1=0.51),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.21, y0=0.10, x1=0.37, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.10, y0=0.24, x1=0.13, y1=0.42),
                make_box("heatmap_panel_title", "panel_title", x0=0.58, y0=0.48, x1=0.77, y1=0.51),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.61, y0=0.10, x1=0.75, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.50, y0=0.22, x1=0.53, y1=0.42),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
                make_box("panel_label_D", "panel_label", x0=0.18, y0=0.42, x1=0.20, y1=0.45),
                make_box("panel_label_E", "panel_label", x0=0.58, y0=0.42, x1=0.60, y1=0.45),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.07, y0=0.56, x1=0.30, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.37, y0=0.56, x1=0.60, y1=0.86),
                make_box("panel_trajectory", "panel", x0=0.67, y0=0.56, x1=0.90, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.17, y0=0.18, x1=0.42, y1=0.46),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.57, y0=0.18, x1=0.82, y1=0.46),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.08, y0=0.02, x1=0.42, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.86, y0=0.20, x1=0.90, y1=0.44),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.10, "y": 0.80, "state_label": "Stem-like"},
                    {"x": 0.14, "y": 0.74, "state_label": "Stem-like"},
                    {"x": 0.22, "y": 0.68, "state_label": "Cycling"},
                    {"x": 0.27, "y": 0.61, "state_label": "Effector"},
                ],
                "spatial_points": [
                    {"x": 0.40, "y": 0.81, "state_label": "Stem-like"},
                    {"x": 0.43, "y": 0.75, "state_label": "Stem-like"},
                    {"x": 0.51, "y": 0.69, "state_label": "Cycling"},
                    {"x": 0.57, "y": 0.61, "state_label": "Effector"},
                ],
                "trajectory_points": [
                    {"x": 0.70, "y": 0.81, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
                    {"x": 0.75, "y": 0.73, "branch_label": "Branch A", "state_label": "Terminal", "pseudotime": 0.32},
                    {"x": 0.83, "y": 0.62, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.76},
                    {"x": 0.88, "y": 0.79, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
                    {"x": 0.84, "y": 0.69, "branch_label": "Branch B", "state_label": "Cycling", "pseudotime": 0.51},
                    {"x": 0.78, "y": 0.59, "branch_label": "Branch B", "state_label": "Effector", "pseudotime": 0.88},
                ],
                "state_labels": ["Stem-like", "Cycling", "Effector"],
                "branch_labels": ["Branch A", "Branch B"],
                "bin_labels": ["Early", "Mid", "Late"],
                "row_labels": ["IFN response", "EMT module"],
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
                "score_method": "GSVA",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "trajectory_point_state_label_unknown" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_atlas_spatial_trajectory_density_coverage_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_trajectory_density_coverage_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_trajectory_density_coverage_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.95, x1=0.84, y1=0.98),
                make_box("atlas_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.24, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.49, x1=0.22, y1=0.52),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.63, x1=0.05, y1=0.80),
                make_box("spatial_panel_title", "panel_title", x0=0.39, y0=0.88, x1=0.56, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.41, y0=0.49, x1=0.55, y1=0.52),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.60, x1=0.36, y1=0.82),
                make_box("trajectory_panel_title", "panel_title", x0=0.69, y0=0.88, x1=0.87, y1=0.91),
                make_box("trajectory_x_axis_title", "subplot_x_axis_title", x0=0.72, y0=0.49, x1=0.86, y1=0.52),
                make_box("trajectory_y_axis_title", "subplot_y_axis_title", x0=0.63, y0=0.60, x1=0.66, y1=0.82),
                make_box("support_panel_title", "panel_title", x0=0.30, y0=0.46, x1=0.54, y1=0.49),
                make_box("support_x_axis_title", "subplot_x_axis_title", x0=0.39, y0=0.10, x1=0.49, y1=0.13),
                make_box("support_y_axis_title", "subplot_y_axis_title", x0=0.22, y0=0.20, x1=0.25, y1=0.40),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
                make_box("panel_label_D", "panel_label", x0=0.29, y0=0.40, x1=0.31, y1=0.43),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.07, y0=0.53, x1=0.30, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.37, y0=0.53, x1=0.60, y1=0.86),
                make_box("panel_trajectory", "panel", x0=0.67, y0=0.53, x1=0.90, y1=0.86),
                make_box("panel_support", "heatmap_tile_region", x0=0.28, y0=0.16, x1=0.70, y1=0.44),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.08, y0=0.02, x1=0.42, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.74, y0=0.18, x1=0.78, y1=0.42),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.10, "y": 0.80, "state_label": "Stem-like"},
                    {"x": 0.14, "y": 0.74, "state_label": "Stem-like"},
                    {"x": 0.22, "y": 0.68, "state_label": "Cycling"},
                    {"x": 0.27, "y": 0.61, "state_label": "Effector"},
                ],
                "spatial_points": [
                    {"x": 0.40, "y": 0.81, "state_label": "Stem-like", "region_label": "Tumor core"},
                    {"x": 0.43, "y": 0.75, "state_label": "Stem-like", "region_label": "Tumor core"},
                    {"x": 0.51, "y": 0.69, "state_label": "Cycling", "region_label": "Invasive margin"},
                    {"x": 0.57, "y": 0.61, "state_label": "Effector", "region_label": "Invasive margin"},
                ],
                "trajectory_points": [
                    {"x": 0.70, "y": 0.81, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
                    {"x": 0.75, "y": 0.73, "branch_label": "Branch A", "state_label": "Cycling", "pseudotime": 0.32},
                    {"x": 0.83, "y": 0.62, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.76},
                    {"x": 0.88, "y": 0.79, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
                    {"x": 0.84, "y": 0.69, "branch_label": "Branch B", "state_label": "Cycling", "pseudotime": 0.51},
                    {"x": 0.78, "y": 0.59, "branch_label": "Branch B", "state_label": "Effector", "pseudotime": 0.88},
                ],
                "state_labels": ["Stem-like", "Cycling", "Effector"],
                "region_labels": ["Tumor core", "Invasive margin"],
                "branch_labels": ["Branch A", "Branch B"],
                "context_labels": ["Atlas density", "Spatial coverage", "Trajectory coverage"],
                "context_kinds": ["atlas_density", "spatial_coverage", "trajectory_coverage"],
                "support_scale_label": "Coverage fraction",
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
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_density_coverage_support_grid_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_trajectory_density_coverage_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_trajectory_density_coverage_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.95, x1=0.84, y1=0.98),
                make_box("atlas_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.24, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.49, x1=0.22, y1=0.52),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.63, x1=0.05, y1=0.80),
                make_box("spatial_panel_title", "panel_title", x0=0.39, y0=0.88, x1=0.56, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.41, y0=0.49, x1=0.55, y1=0.52),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.60, x1=0.36, y1=0.82),
                make_box("trajectory_panel_title", "panel_title", x0=0.69, y0=0.88, x1=0.87, y1=0.91),
                make_box("trajectory_x_axis_title", "subplot_x_axis_title", x0=0.72, y0=0.49, x1=0.86, y1=0.52),
                make_box("trajectory_y_axis_title", "subplot_y_axis_title", x0=0.63, y0=0.60, x1=0.66, y1=0.82),
                make_box("support_panel_title", "panel_title", x0=0.30, y0=0.46, x1=0.54, y1=0.49),
                make_box("support_x_axis_title", "subplot_x_axis_title", x0=0.39, y0=0.10, x1=0.49, y1=0.13),
                make_box("support_y_axis_title", "subplot_y_axis_title", x0=0.22, y0=0.20, x1=0.25, y1=0.40),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
                make_box("panel_label_D", "panel_label", x0=0.29, y0=0.40, x1=0.31, y1=0.43),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.07, y0=0.53, x1=0.30, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.37, y0=0.53, x1=0.60, y1=0.86),
                make_box("panel_trajectory", "panel", x0=0.67, y0=0.53, x1=0.90, y1=0.86),
                make_box("panel_support", "heatmap_tile_region", x0=0.28, y0=0.16, x1=0.70, y1=0.44),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.08, y0=0.02, x1=0.42, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.74, y0=0.18, x1=0.78, y1=0.42),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.10, "y": 0.80, "state_label": "Stem-like"},
                    {"x": 0.14, "y": 0.74, "state_label": "Stem-like"},
                    {"x": 0.22, "y": 0.68, "state_label": "Cycling"},
                    {"x": 0.27, "y": 0.61, "state_label": "Effector"},
                ],
                "spatial_points": [
                    {"x": 0.40, "y": 0.81, "state_label": "Stem-like", "region_label": "Tumor core"},
                    {"x": 0.43, "y": 0.75, "state_label": "Stem-like", "region_label": "Tumor core"},
                    {"x": 0.51, "y": 0.69, "state_label": "Cycling", "region_label": "Invasive margin"},
                    {"x": 0.57, "y": 0.61, "state_label": "Effector", "region_label": "Invasive margin"},
                ],
                "trajectory_points": [
                    {"x": 0.70, "y": 0.81, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
                    {"x": 0.75, "y": 0.73, "branch_label": "Branch A", "state_label": "Cycling", "pseudotime": 0.32},
                    {"x": 0.83, "y": 0.62, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.76},
                    {"x": 0.88, "y": 0.79, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
                    {"x": 0.84, "y": 0.69, "branch_label": "Branch B", "state_label": "Cycling", "pseudotime": 0.51},
                    {"x": 0.78, "y": 0.59, "branch_label": "Branch B", "state_label": "Effector", "pseudotime": 0.88},
                ],
                "state_labels": ["Stem-like", "Cycling", "Effector"],
                "region_labels": ["Tumor core", "Invasive margin"],
                "branch_labels": ["Branch A", "Branch B"],
                "context_labels": ["Atlas density", "Spatial coverage", "Trajectory coverage"],
                "context_kinds": ["atlas_density", "spatial_coverage", "trajectory_coverage"],
                "support_scale_label": "Coverage fraction",
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
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "support_grid_incomplete" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_forest_marker_is_outside_interval() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_forest_plot",
        layout_sidecar={
            "template_id": "forest_effect_main",
            "device": make_device(),
            "layout_boxes": [
                make_box("reference_line", "reference_line", x0=0.52, y0=0.18, x1=0.52, y1=0.86),
                make_box("row_label_1", "row_label", x0=0.02, y0=0.24, x1=0.20, y1=0.30),
                make_box("estimate_marker_1", "estimate_marker", x0=0.84, y0=0.25, x1=0.86, y1=0.29),
                make_box("ci_segment_1", "ci_segment", x0=0.56, y0=0.27, x1=0.74, y1=0.27),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.28, y0=0.16, x1=0.80, y1=0.88),
            ],
            "guide_boxes": [],
            "metrics": {
                "rows": [
                    {"row_id": "1", "label": "Age >= 60", "lower": 0.90, "estimate": 1.50, "upper": 1.20},
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "estimate_outside_interval" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_multicenter_center_events_are_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_multicenter_overview",
        layout_sidecar={
            "template_id": "multicenter_generalizability_overview",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.60, y1=0.08),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.52, x1=0.11, y1=0.56),
                make_box("panel_label_B", "panel_label", x0=0.08, y0=0.94, x1=0.11, y1=0.98),
                make_box("panel_label_C", "panel_label", x0=0.56, y0=0.78, x1=0.59, y1=0.82),
                make_box("center_event_y_axis_title", "y_axis_title", x0=0.01, y0=0.12, x1=0.05, y1=0.52),
                make_box("coverage_y_axis_title", "y_axis_title", x0=0.01, y0=0.58, x1=0.05, y1=0.94),
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
            "guide_boxes": [],
            "metrics": {
                "center_event_counts": [],
                "coverage_panels": [
                    {
                        "panel_id": "region",
                        "title": "Region coverage",
                        "layout_role": "wide_left",
                        "bars": [{"label": "Central", "count": 72}],
                    },
                    {
                        "panel_id": "north_south",
                        "title": "North vs South",
                        "layout_role": "top_right",
                        "bars": [{"label": "North", "count": 84}],
                    },
                    {
                        "panel_id": "urban_rural",
                        "title": "Urban/rural",
                        "layout_role": "bottom_right",
                        "bars": [{"label": "Urban", "count": 101}],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "center_event_counts_missing" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_center_support_generalizability_mode() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_multicenter_overview",
        layout_sidecar={
                "template_id": "multicenter_generalizability_overview",
                "device": make_device(),
                "layout_boxes": [
                    make_box("title", "title", x0=0.08, y0=0.02, x1=0.62, y1=0.08),
                    make_box("panel_label_A", "panel_label", x0=0.09, y0=0.47, x1=0.12, y1=0.51),
                    make_box("panel_label_B", "panel_label", x0=0.09, y0=0.89, x1=0.12, y1=0.93),
                    make_box("panel_label_C", "panel_label", x0=0.57, y0=0.89, x1=0.60, y1=0.93),
                make_box("center_event_y_axis_title", "y_axis_title", x0=0.01, y0=0.12, x1=0.05, y1=0.52),
                make_box("coverage_y_axis_title", "y_axis_title", x0=0.01, y0=0.58, x1=0.05, y1=0.94),
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
                make_box("legend", "legend", x0=0.78, y0=0.02, x1=0.94, y1=0.08),
            ],
            "metrics": {
                "center_event_counts": [
                    {"center_label": "1", "split_bucket": "validation", "event_count": 2},
                    {"center_label": "2", "split_bucket": "validation", "event_count": 1},
                    {"center_label": "25", "split_bucket": "train", "event_count": 3},
                ],
                "coverage_panels": [
                    {
                        "panel_id": "region",
                        "title": "Region coverage",
                        "layout_role": "wide_left",
                        "bars": [{"label": "Central", "count": 72}],
                    },
                    {
                        "panel_id": "north_south",
                        "title": "North vs South",
                        "layout_role": "top_right",
                        "bars": [{"label": "North", "count": 84}],
                    },
                    {
                        "panel_id": "urban_rural",
                        "title": "Urban/rural",
                        "layout_role": "bottom_right",
                        "bars": [{"label": "Urban", "count": 101}],
                    },
                ],
                "legend_title": "Split",
                "legend_labels": ["Train", "Validation"],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_multicenter_panel_labels_are_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_multicenter_overview",
        layout_sidecar={
            "template_id": "multicenter_generalizability_overview",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.08, y0=0.02, x1=0.62, y1=0.08),
                make_box("center_event_y_axis_title", "y_axis_title", x0=0.01, y0=0.12, x1=0.05, y1=0.52),
                make_box("coverage_y_axis_title", "y_axis_title", x0=0.01, y0=0.58, x1=0.05, y1=0.94),
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
                make_box("legend", "legend", x0=0.78, y0=0.02, x1=0.94, y1=0.08),
            ],
            "metrics": {
                "center_event_counts": [
                    {"center_label": "1", "split_bucket": "validation", "event_count": 2},
                    {"center_label": "2", "split_bucket": "validation", "event_count": 1},
                    {"center_label": "25", "split_bucket": "train", "event_count": 3},
                ],
                "coverage_panels": [
                    {
                        "panel_id": "region",
                        "title": "Region coverage",
                        "layout_role": "wide_left",
                        "bars": [{"label": "Central", "count": 72}],
                    },
                    {
                        "panel_id": "north_south",
                        "title": "North vs South",
                        "layout_role": "top_right",
                        "bars": [{"label": "North", "count": 84}],
                    },
                    {
                        "panel_id": "urban_rural",
                        "title": "Urban/rural",
                        "layout_role": "bottom_right",
                        "bars": [{"label": "Urban", "count": 101}],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_panel_label" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_multicenter_panel_label_is_not_top_left_anchored() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_multicenter_overview",
        layout_sidecar={
            "template_id": "multicenter_generalizability_overview",
            "device": make_device(),
            "layout_boxes": [
                make_box("center_event_y_axis_title", "y_axis_title", x0=0.02, y0=0.20, x1=0.05, y1=0.48),
                make_box("coverage_y_axis_title", "y_axis_title", x0=0.02, y0=0.64, x1=0.05, y1=0.92),
                make_box("panel_label_A", "panel_label", x0=0.40, y0=0.30, x1=0.43, y1=0.34),
                make_box("panel_label_B", "panel_label", x0=0.30, y0=0.76, x1=0.33, y1=0.80),
                make_box("panel_label_C", "panel_label", x0=0.80, y0=0.70, x1=0.83, y1=0.74),
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
                make_box("legend", "legend", x0=0.78, y0=0.02, x1=0.94, y1=0.08),
            ],
            "metrics": {
                "center_event_counts": [
                    {"center_label": "1", "split_bucket": "validation", "event_count": 2},
                    {"center_label": "2", "split_bucket": "validation", "event_count": 1},
                    {"center_label": "25", "split_bucket": "train", "event_count": 3},
                ],
                "coverage_panels": [
                    {"panel_id": "region", "title": "Region coverage", "layout_role": "wide_left", "bars": [{"label": "Central", "count": 72}]},
                    {"panel_id": "north_south", "title": "North vs South", "layout_role": "top_right", "bars": [{"label": "North", "count": 84}]},
                    {"panel_id": "urban_rural", "title": "Urban/rural", "layout_role": "bottom_right", "bars": [{"label": "Urban", "count": 101}]},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "panel_label_anchor_drift" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_multicenter_legend_intrudes_into_panel_band() -> None:
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
                make_box("legend", "legend", x0=0.40, y0=0.10, x1=0.62, y1=0.18),
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
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "legend_footer_band_drift" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_multicenter_legend_semantics_are_missing() -> None:
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
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "legend_title_invalid" for issue in result["issues"])
    assert any(issue["rule_id"] == "legend_labels_missing" for issue in result["issues"])
