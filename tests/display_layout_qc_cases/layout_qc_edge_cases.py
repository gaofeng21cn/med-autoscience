from .shared import *

def test_run_display_layout_qc_fails_when_landmark_panel_window_is_not_forward() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_landmark_performance_panel",
        layout_sidecar={
            "template_id": "time_to_event_landmark_performance_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.86, x1=0.28, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.40, y0=0.86, x1=0.56, y1=0.89),
                make_box("panel_title_C", "panel_title", x0=0.68, y0=0.86, x1=0.84, y1=0.89),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.14, y0=0.08, x1=0.28, y1=0.11),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.42, y0=0.08, x1=0.56, y1=0.11),
                make_box("x_axis_title_C", "subplot_x_axis_title", x0=0.70, y0=0.08, x1=0.84, y1=0.11),
                make_box("y_axis_title_A", "subplot_y_axis_title", x0=0.06, y0=0.34, x1=0.08, y1=0.72),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.82, x1=0.14, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.40, y0=0.82, x1=0.42, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
                make_box("metric_marker_1", "metric_marker", x0=0.22, y0=0.72, x1=0.24, y1=0.74),
                make_box("metric_marker_2", "metric_marker", x0=0.48, y0=0.72, x1=0.50, y1=0.74),
                make_box("metric_marker_3", "metric_marker", x0=0.78, y0=0.72, x1=0.80, y1=0.74),
            ],
            "panel_boxes": [
                make_box("panel_A", "metric_panel", x0=0.10, y0=0.20, x1=0.30, y1=0.84),
                make_box("panel_B", "metric_panel", x0=0.38, y0=0.20, x1=0.58, y1=0.84),
                make_box("panel_C", "metric_panel", x0=0.66, y0=0.20, x1=0.86, y1=0.84),
            ],
            "guide_boxes": [
                make_box("reference_line_1", "reference_line", x0=0.77, y0=0.20, x1=0.78, y1=0.84),
            ],
            "metrics": {
                "metric_panels": [
                    {
                        "panel_id": "discrimination_panel",
                        "panel_label": "A",
                        "metric_kind": "c_index",
                        "title": "Discrimination",
                        "x_label": "Validation C-index",
                        "rows": [
                            {
                                "label": "8→8 months",
                                "analysis_window_label": "8-month landmark predicting 8-month recurrence",
                                "landmark_months": 8,
                                "prediction_months": 8,
                                "value": 0.78,
                            }
                        ],
                    },
                    {
                        "panel_id": "error_panel",
                        "panel_label": "B",
                        "metric_kind": "brier_score",
                        "title": "Prediction error",
                        "x_label": "Brier score",
                        "rows": [
                            {
                                "label": "8→8 months",
                                "analysis_window_label": "8-month landmark predicting 8-month recurrence",
                                "landmark_months": 8,
                                "prediction_months": 8,
                                "value": 0.18,
                            }
                        ],
                    },
                    {
                        "panel_id": "calibration_panel",
                        "panel_label": "C",
                        "metric_kind": "calibration_slope",
                        "title": "Calibration",
                        "x_label": "Calibration slope",
                        "reference_value": 1.0,
                        "rows": [
                            {
                                "label": "8→8 months",
                                "analysis_window_label": "8-month landmark predicting 8-month recurrence",
                                "landmark_months": 8,
                                "prediction_months": 8,
                                "value": 0.97,
                            }
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "prediction_window_not_forward" for issue in result["issues"])
