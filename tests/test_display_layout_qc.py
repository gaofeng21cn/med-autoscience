from __future__ import annotations

import importlib


def make_box(
    box_id: str,
    box_type: str,
    *,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> dict[str, object]:
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
    }


def make_device() -> dict[str, float]:
    return {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0}


def test_run_display_layout_qc_fails_for_overlapping_legend_and_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_embedding_scatter",
        layout_sidecar={
            "template_id": "umap_scatter_grouped",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.60, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.32, y0=0.92, x1=0.62, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.25, x1=0.06, y1=0.70),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.10, y0=0.16, x1=0.78, y1=0.88),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.64, y0=0.64, x1=0.92, y1=0.86),
            ],
            "metrics": {
                "points": [
                    {"x": 0.22, "y": 0.32, "group": "A"},
                    {"x": 0.44, "y": 0.54, "group": "B"},
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "legend_panel_overlap" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_valid_embedding_scatter() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_embedding_scatter",
        layout_sidecar={
            "template_id": "pca_scatter_grouped",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.60, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.32, y0=0.92, x1=0.62, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.25, x1=0.06, y1=0.70),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.10, y0=0.16, x1=0.74, y1=0.88),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.78, y0=0.28, x1=0.96, y1=0.46),
            ],
            "metrics": {
                "points": [
                    {"x": 0.22, "y": 0.32, "group": "A"},
                    {"x": 0.44, "y": 0.54, "group": "B"},
                ]
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_curve_text_leaves_device() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "roc_curve_binary",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.08, y0=0.02, x1=1.08, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.24, x1=0.06, y1=0.70),
                make_box("caption", "caption", x0=0.10, y0=0.98, x1=0.60, y1=1.00),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.12, y0=0.16, x1=0.76, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.80, y0=0.30, x1=0.96, y1=0.44),
            ],
            "metrics": {
                "series": [{"label": "Model", "x": [0.0, 0.5, 1.0], "y": [0.0, 0.7, 1.0]}],
                "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "box_out_of_device" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_correlation_matrix_is_not_symmetric() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_heatmap",
        layout_sidecar={
            "template_id": "correlation_heatmap",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.28, y0=0.92, x1=0.64, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.02, y0=0.22, x1=0.06, y1=0.68),
            ],
            "panel_boxes": [
                make_box("panel", "heatmap_tile_region", x0=0.12, y0=0.16, x1=0.74, y1=0.86),
            ],
            "guide_boxes": [
                make_box("colorbar", "colorbar", x0=0.80, y0=0.18, x1=0.90, y1=0.82),
            ],
            "metrics": {
                "matrix_cells": [
                    {"x": "A", "y": "A", "value": 1.0},
                    {"x": "A", "y": "B", "value": 0.42},
                    {"x": "B", "y": "A", "value": 0.31},
                    {"x": "B", "y": "B", "value": 1.0},
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "matrix_not_symmetric" for issue in result["issues"])


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
                "points": [
                    {"feature": "Age", "y": 0.28},
                    {"feature": "Ki-67", "y": 0.39},
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "feature_row_overlap" for issue in result["issues"])
