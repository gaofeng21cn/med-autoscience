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


def test_run_display_layout_qc_passes_for_valid_illustration_flow() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.125, x1=0.11, y1=0.155),
                make_box("panel_label_B", "panel_label", x0=0.52, y0=0.125, x1=0.55, y1=0.155),
                make_box("step_screened", "main_step", x0=0.08, y0=0.40, x1=0.28, y1=0.50),
                make_box("step_included", "main_step", x0=0.08, y0=0.24, x1=0.28, y1=0.34),
                make_box("exclusion_repeat", "exclusion_box", x0=0.32, y0=0.30, x1=0.46, y1=0.38),
            ],
            "panel_boxes": [
                make_box("subfigure_panel_A", "subfigure_panel", x0=0.06, y0=0.10, x1=0.48, y1=0.54),
                make_box("subfigure_panel_B", "subfigure_panel", x0=0.52, y0=0.10, x1=0.94, y1=0.54),
                make_box("flow_panel", "flow_panel", x0=0.08, y0=0.12, x1=0.46, y1=0.50),
                make_box("secondary_panel_validation", "secondary_panel", x0=0.54, y0=0.42, x1=0.92, y1=0.52),
                make_box("secondary_panel_core", "secondary_panel", x0=0.54, y0=0.28, x1=0.72, y1=0.38),
                make_box("secondary_panel_primary", "secondary_panel", x0=0.74, y0=0.28, x1=0.92, y1=0.38),
                make_box("secondary_panel_audit", "secondary_panel", x0=0.54, y0=0.14, x1=0.72, y1=0.24),
                make_box("secondary_panel_context", "secondary_panel", x0=0.74, y0=0.14, x1=0.92, y1=0.24),
            ],
            "guide_boxes": [
                make_box("flow_spine_screened_to_included", "flow_connector", x0=0.17, y0=0.34, x1=0.19, y1=0.40),
                make_box("flow_branch_repeat", "flow_branch_connector", x0=0.19, y0=0.33, x1=0.32, y1=0.35),
                make_box("hierarchy_root_trunk", "hierarchy_connector", x0=0.72, y0=0.38, x1=0.74, y1=0.42),
                make_box("hierarchy_root_branch", "hierarchy_connector", x0=0.63, y0=0.36, x1=0.83, y1=0.38),
                make_box("hierarchy_connector_left_middle_to_left_bottom", "hierarchy_connector", x0=0.63, y0=0.24, x1=0.65, y1=0.28),
                make_box("hierarchy_connector_right_middle_to_right_bottom", "hierarchy_connector", x0=0.83, y0=0.24, x1=0.85, y1=0.28),
            ],
            "metrics": {
                "steps": [
                    {"step_id": "screened"},
                    {"step_id": "included"},
                ],
                "exclusions": [
                    {"exclusion_id": "repeat", "from_step_id": "screened"},
                ],
                "endpoint_inventory": [],
                "design_panels": [
                    {"panel_id": "validation", "layout_role": "wide_top"},
                    {"panel_id": "core", "layout_role": "left_middle"},
                    {"panel_id": "primary", "layout_role": "right_middle"},
                    {"panel_id": "audit", "layout_role": "left_bottom"},
                    {"panel_id": "context", "layout_role": "right_bottom"},
                ],
                "flow_nodes": [
                    {
                        "box_id": "step_screened",
                        "box_type": "main_step",
                        "line_count": 3,
                        "max_line_chars": 24,
                        "rendered_height_pt": 92.0,
                        "rendered_width_pt": 218.0,
                        "padding_pt": 9.0,
                    },
                    {
                        "box_id": "step_included",
                        "box_type": "main_step",
                        "line_count": 3,
                        "max_line_chars": 26,
                        "rendered_height_pt": 92.0,
                        "rendered_width_pt": 218.0,
                        "padding_pt": 9.0,
                    },
                    {
                        "box_id": "exclusion_repeat",
                        "box_type": "exclusion_box",
                        "line_count": 2,
                        "max_line_chars": 20,
                        "rendered_height_pt": 62.0,
                        "rendered_width_pt": 176.0,
                        "padding_pt": 8.0,
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_illustration_subfigure_semantics_are_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
            "layout_boxes": [
                make_box("step_screened", "main_step", x0=0.08, y0=0.14, x1=0.46, y1=0.24),
            ],
            "panel_boxes": [
                make_box("flow_panel", "flow_panel", x0=0.08, y0=0.14, x1=0.46, y1=0.30),
                make_box("secondary_panel_validation", "secondary_panel", x0=0.54, y0=0.14, x1=0.92, y1=0.24),
            ],
            "guide_boxes": [],
            "metrics": {
                "steps": [
                    {"step_id": "screened"},
                    {"step_id": "included"},
                    {"step_id": "analysis"},
                ],
                "exclusions": [
                    {"exclusion_id": "repeat", "from_step_id": "screened"},
                ],
                "endpoint_inventory": [],
                "design_panels": [
                    {"panel_id": "validation", "layout_role": "wide_top"},
                    {"panel_id": "core", "layout_role": "left_middle"},
                    {"panel_id": "primary", "layout_role": "right_middle"},
                    {"panel_id": "audit", "layout_role": "left_bottom"},
                    {"panel_id": "context", "layout_role": "right_bottom"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_subfigure_panel" for issue in result["issues"])
    assert any(issue["rule_id"] == "missing_panel_label" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_structure_connectors_are_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
                "layout_boxes": [
                    make_box("panel_label_A", "panel_label", x0=0.08, y0=0.125, x1=0.11, y1=0.155),
                    make_box("panel_label_B", "panel_label", x0=0.52, y0=0.125, x1=0.55, y1=0.155),
                    make_box("step_screened", "main_step", x0=0.08, y0=0.40, x1=0.28, y1=0.50),
                    make_box("step_included", "main_step", x0=0.08, y0=0.24, x1=0.28, y1=0.34),
                    make_box("step_analysis", "main_step", x0=0.08, y0=0.08, x1=0.28, y1=0.18),
                    make_box("exclusion_repeat", "exclusion_box", x0=0.32, y0=0.30, x1=0.46, y1=0.38),
                ],
                "panel_boxes": [
                    make_box("subfigure_panel_A", "subfigure_panel", x0=0.06, y0=0.06, x1=0.48, y1=0.54),
                    make_box("subfigure_panel_B", "subfigure_panel", x0=0.52, y0=0.06, x1=0.94, y1=0.54),
                    make_box("flow_panel", "flow_panel", x0=0.08, y0=0.08, x1=0.46, y1=0.50),
                    make_box("secondary_panel_validation", "secondary_panel", x0=0.54, y0=0.42, x1=0.92, y1=0.52),
                    make_box("secondary_panel_core", "secondary_panel", x0=0.54, y0=0.28, x1=0.72, y1=0.38),
                    make_box("secondary_panel_primary", "secondary_panel", x0=0.74, y0=0.28, x1=0.92, y1=0.38),
                    make_box("secondary_panel_audit", "secondary_panel", x0=0.54, y0=0.14, x1=0.72, y1=0.24),
                    make_box("secondary_panel_context", "secondary_panel", x0=0.74, y0=0.14, x1=0.92, y1=0.24),
                ],
            "guide_boxes": [],
            "metrics": {
                "steps": [
                    {"step_id": "screened"},
                    {"step_id": "included"},
                    {"step_id": "analysis"},
                ],
                "exclusions": [
                    {"exclusion_id": "repeat", "from_step_id": "screened"},
                ],
                "endpoint_inventory": [],
                "design_panels": [
                    {"panel_id": "validation", "layout_role": "wide_top"},
                    {"panel_id": "core", "layout_role": "left_middle"},
                    {"panel_id": "primary", "layout_role": "right_middle"},
                    {"panel_id": "audit", "layout_role": "left_bottom"},
                    {"panel_id": "context", "layout_role": "right_bottom"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_flow_connector" for issue in result["issues"])
    assert any(issue["rule_id"] == "missing_hierarchy_connector" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_illustration_exclusion_overlaps_step() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
            "layout_boxes": [
                make_box("step_screened", "main_step", x0=0.08, y0=0.14, x1=0.46, y1=0.24),
                make_box("exclusion_repeat", "exclusion_box", x0=0.30, y0=0.16, x1=0.70, y1=0.24),
            ],
            "panel_boxes": [
                make_box("flow_panel", "flow_panel", x0=0.08, y0=0.14, x1=0.92, y1=0.30),
            ],
            "guide_boxes": [],
            "metrics": {
                "steps": [],
                "exclusions": [],
                "endpoint_inventory": [],
                "design_panels": [],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "exclusion_step_overlap" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_time_to_event_discrimination_calibration_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_to_event_discrimination_calibration_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.12, y0=0.92, x1=0.64, y1=0.98),
                make_box("panel_left_x_axis_title", "subplot_x_axis_title", x0=0.16, y0=0.08, x1=0.32, y1=0.13),
                make_box("panel_left_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.24, x1=0.06, y1=0.74),
                make_box("panel_left_title", "panel_title", x0=0.12, y0=0.80, x1=0.42, y1=0.85),
                make_box("calibration_x_axis_title", "subplot_x_axis_title", x0=0.62, y0=0.08, x1=0.78, y1=0.13),
                make_box("calibration_y_axis_title", "subplot_y_axis_title", x0=0.52, y0=0.24, x1=0.56, y1=0.74),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.80, x1=0.88, y1=0.85),
                make_box("annotation_callout", "annotation_block", x0=0.58, y0=0.66, x1=0.80, y1=0.73),
                make_box("discrimination_marker_1", "metric_marker", x0=0.24, y0=0.34, x1=0.26, y1=0.38),
                make_box("discrimination_marker_2", "metric_marker", x0=0.28, y0=0.56, x1=0.30, y1=0.60),
                make_box("predicted_marker_1", "metric_marker", x0=0.62, y0=0.46, x1=0.64, y1=0.50),
                make_box("observed_marker_1", "metric_marker", x0=0.62, y0=0.44, x1=0.64, y1=0.48),
                make_box("predicted_marker_2", "metric_marker", x0=0.70, y0=0.52, x1=0.72, y1=0.56),
                make_box("observed_marker_2", "metric_marker", x0=0.70, y0=0.55, x1=0.72, y1=0.59),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.18, x1=0.44, y1=0.84),
                make_box("panel_right", "panel", x0=0.54, y0=0.18, x1=0.88, y1=0.84),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.34, y0=0.02, x1=0.62, y1=0.08),
            ],
            "metrics": {
                "discrimination_points": [
                    {"label": "Ridge Cox", "c_index": 0.83},
                    {"label": "Lasso Cox", "c_index": 0.79},
                ],
                "calibration_summary": [
                    {"group_label": "Decile 1", "group_order": 1, "n": 60, "events_5y": 1, "predicted_risk_5y": 0.012, "observed_risk_5y": 0.010},
                    {"group_label": "Decile 10", "group_order": 10, "n": 60, "events_5y": 8, "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
                ],
                "calibration_callout": {"group_label": "Decile 10", "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_time_to_event_annotation_overlaps_panel_title() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_to_event_discrimination_calibration_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.12, y0=0.92, x1=0.64, y1=0.98),
                make_box("panel_left_x_axis_title", "subplot_x_axis_title", x0=0.16, y0=0.08, x1=0.32, y1=0.13),
                make_box("panel_left_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.24, x1=0.06, y1=0.74),
                make_box("panel_left_title", "panel_title", x0=0.12, y0=0.80, x1=0.42, y1=0.85),
                make_box("calibration_x_axis_title", "subplot_x_axis_title", x0=0.62, y0=0.08, x1=0.78, y1=0.13),
                make_box("calibration_y_axis_title", "subplot_y_axis_title", x0=0.52, y0=0.24, x1=0.56, y1=0.74),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.80, x1=0.88, y1=0.85),
                make_box("annotation_callout", "annotation_block", x0=0.16, y0=0.81, x1=0.42, y1=0.88),
                make_box("discrimination_marker_1", "metric_marker", x0=0.24, y0=0.34, x1=0.26, y1=0.38),
                make_box("discrimination_marker_2", "metric_marker", x0=0.28, y0=0.56, x1=0.30, y1=0.60),
                make_box("predicted_marker_1", "metric_marker", x0=0.62, y0=0.46, x1=0.64, y1=0.50),
                make_box("observed_marker_1", "metric_marker", x0=0.62, y0=0.44, x1=0.64, y1=0.48),
                make_box("predicted_marker_2", "metric_marker", x0=0.70, y0=0.52, x1=0.72, y1=0.56),
                make_box("observed_marker_2", "metric_marker", x0=0.70, y0=0.55, x1=0.72, y1=0.59),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.18, x1=0.44, y1=0.84),
                make_box("panel_right", "panel", x0=0.54, y0=0.18, x1=0.88, y1=0.84),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.34, y0=0.02, x1=0.62, y1=0.08),
            ],
            "metrics": {
                "discrimination_points": [
                    {"label": "Ridge Cox", "c_index": 0.83},
                    {"label": "Lasso Cox", "c_index": 0.79},
                ],
                "calibration_summary": [
                    {"group_label": "Decile 1", "group_order": 1, "n": 60, "events_5y": 1, "predicted_risk_5y": 0.012, "observed_risk_5y": 0.010},
                    {"group_label": "Decile 10", "group_order": 10, "n": 60, "events_5y": 8, "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
                ],
                "calibration_callout": {"group_label": "Decile 10", "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "annotation_title_overlap" for issue in result["issues"])


def test_run_display_layout_qc_allows_time_to_event_annotation_in_right_panel_blank_zone() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_to_event_discrimination_calibration_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_left_x_axis_title", "subplot_x_axis_title", x0=0.16, y0=0.08, x1=0.32, y1=0.13),
                make_box("panel_left_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.24, x1=0.06, y1=0.74),
                make_box("panel_left_title", "panel_title", x0=0.12, y0=0.80, x1=0.42, y1=0.85),
                make_box("calibration_x_axis_title", "subplot_x_axis_title", x0=0.62, y0=0.08, x1=0.78, y1=0.13),
                make_box("calibration_y_axis_title", "subplot_y_axis_title", x0=0.52, y0=0.24, x1=0.56, y1=0.74),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.80, x1=0.88, y1=0.85),
                make_box("annotation_callout", "annotation_block", x0=0.58, y0=0.66, x1=0.80, y1=0.73),
                make_box("discrimination_marker_1", "metric_marker", x0=0.24, y0=0.34, x1=0.26, y1=0.38),
                make_box("discrimination_marker_2", "metric_marker", x0=0.28, y0=0.56, x1=0.30, y1=0.60),
                make_box("predicted_marker_1", "metric_marker", x0=0.62, y0=0.46, x1=0.64, y1=0.50),
                make_box("observed_marker_1", "metric_marker", x0=0.62, y0=0.44, x1=0.64, y1=0.48),
                make_box("predicted_marker_2", "metric_marker", x0=0.70, y0=0.52, x1=0.72, y1=0.56),
                make_box("observed_marker_2", "metric_marker", x0=0.70, y0=0.55, x1=0.72, y1=0.59),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.18, x1=0.44, y1=0.84),
                make_box("panel_right", "panel", x0=0.54, y0=0.18, x1=0.88, y1=0.84),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.34, y0=0.02, x1=0.62, y1=0.08),
            ],
            "metrics": {
                "discrimination_points": [
                    {"label": "Ridge Cox", "c_index": 0.83},
                    {"label": "Lasso Cox", "c_index": 0.79},
                ],
                "calibration_summary": [
                    {"group_label": "Decile 1", "group_order": 1, "n": 60, "events_5y": 1, "predicted_risk_5y": 0.012, "observed_risk_5y": 0.010},
                    {"group_label": "Decile 10", "group_order": 10, "n": 60, "events_5y": 8, "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
                ],
                "calibration_callout": {"group_label": "Decile 10", "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_time_to_event_annotation_stays_in_panel_a() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_to_event_discrimination_calibration_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_left_x_axis_title", "subplot_x_axis_title", x0=0.16, y0=0.08, x1=0.32, y1=0.13),
                make_box("panel_left_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.24, x1=0.06, y1=0.74),
                make_box("panel_left_title", "panel_title", x0=0.12, y0=0.80, x1=0.42, y1=0.85),
                make_box("calibration_x_axis_title", "subplot_x_axis_title", x0=0.62, y0=0.08, x1=0.78, y1=0.13),
                make_box("calibration_y_axis_title", "subplot_y_axis_title", x0=0.52, y0=0.24, x1=0.56, y1=0.74),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.80, x1=0.88, y1=0.85),
                make_box("annotation_callout", "annotation_block", x0=0.12, y0=0.66, x1=0.34, y1=0.73),
                make_box("discrimination_marker_1", "metric_marker", x0=0.24, y0=0.34, x1=0.26, y1=0.38),
                make_box("discrimination_marker_2", "metric_marker", x0=0.28, y0=0.56, x1=0.30, y1=0.60),
                make_box("predicted_marker_1", "metric_marker", x0=0.62, y0=0.46, x1=0.64, y1=0.50),
                make_box("observed_marker_1", "metric_marker", x0=0.62, y0=0.44, x1=0.64, y1=0.48),
                make_box("predicted_marker_2", "metric_marker", x0=0.70, y0=0.52, x1=0.72, y1=0.56),
                make_box("observed_marker_2", "metric_marker", x0=0.70, y0=0.55, x1=0.72, y1=0.59),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.18, x1=0.44, y1=0.84),
                make_box("panel_right", "panel", x0=0.54, y0=0.18, x1=0.88, y1=0.84),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.34, y0=0.02, x1=0.62, y1=0.08),
            ],
            "metrics": {
                "discrimination_points": [
                    {"label": "Ridge Cox", "c_index": 0.83},
                    {"label": "Lasso Cox", "c_index": 0.79},
                ],
                "calibration_summary": [
                    {"group_label": "Decile 1", "group_order": 1, "n": 60, "events_5y": 1, "predicted_risk_5y": 0.012, "observed_risk_5y": 0.010},
                    {"group_label": "Decile 10", "group_order": 10, "n": 60, "events_5y": 8, "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
                ],
                "calibration_callout": {"group_label": "Decile 10", "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "annotation_wrong_panel" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_time_to_event_annotation_leaves_panel_canvas() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_to_event_discrimination_calibration_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_left_x_axis_title", "subplot_x_axis_title", x0=0.16, y0=0.08, x1=0.32, y1=0.13),
                make_box("panel_left_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.24, x1=0.06, y1=0.74),
                make_box("panel_left_title", "panel_title", x0=0.12, y0=0.80, x1=0.42, y1=0.85),
                make_box("calibration_x_axis_title", "subplot_x_axis_title", x0=0.62, y0=0.08, x1=0.78, y1=0.13),
                make_box("calibration_y_axis_title", "subplot_y_axis_title", x0=0.52, y0=0.24, x1=0.56, y1=0.74),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.80, x1=0.88, y1=0.85),
                make_box("annotation_callout", "annotation_block", x0=0.12, y0=0.78, x1=0.34, y1=0.86),
                make_box("discrimination_marker_1", "metric_marker", x0=0.24, y0=0.34, x1=0.26, y1=0.38),
                make_box("discrimination_marker_2", "metric_marker", x0=0.28, y0=0.56, x1=0.30, y1=0.60),
                make_box("predicted_marker_1", "metric_marker", x0=0.62, y0=0.46, x1=0.64, y1=0.50),
                make_box("observed_marker_1", "metric_marker", x0=0.62, y0=0.44, x1=0.64, y1=0.48),
                make_box("predicted_marker_2", "metric_marker", x0=0.70, y0=0.52, x1=0.72, y1=0.56),
                make_box("observed_marker_2", "metric_marker", x0=0.70, y0=0.55, x1=0.72, y1=0.59),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.18, x1=0.44, y1=0.84),
                make_box("panel_right", "panel", x0=0.54, y0=0.18, x1=0.88, y1=0.84),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.34, y0=0.02, x1=0.62, y1=0.08),
            ],
            "metrics": {
                "discrimination_points": [
                    {"label": "Ridge Cox", "c_index": 0.83},
                    {"label": "Lasso Cox", "c_index": 0.79},
                ],
                "calibration_summary": [
                    {"group_label": "Decile 1", "group_order": 1, "n": 60, "events_5y": 1, "predicted_risk_5y": 0.012, "observed_risk_5y": 0.010},
                    {"group_label": "Decile 10", "group_order": 10, "n": 60, "events_5y": 8, "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
                ],
                "calibration_callout": {"group_label": "Decile 10", "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "annotation_out_of_panel" for issue in result["issues"])


def test_run_display_layout_qc_fails_for_legacy_time_to_event_curve_sidecar() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_to_event_discrimination_calibration_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.12, y0=0.02, x1=0.64, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.24, y0=0.90, x1=0.40, y1=0.95),
                make_box("y_axis_title", "y_axis_title", x0=0.02, y0=0.24, x1=0.06, y1=0.74),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.18, x1=0.44, y1=0.84),
                make_box("panel_right", "panel", x0=0.54, y0=0.18, x1=0.88, y1=0.84),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.74, y0=0.08, x1=0.94, y1=0.16),
            ],
            "metrics": {
                "series": [{"label": "Legacy curve", "x": [0.0, 0.5, 1.0], "y": [0.0, 0.7, 1.0]}],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "discrimination_points_missing" for issue in result["issues"])
    assert any(issue["rule_id"] == "calibration_summary_missing" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_submission_graphical_abstract() -> None:
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
                make_box("panel_a_title", "panel_title", x0=0.09, y0=0.12, x1=0.26, y1=0.16),
                make_box("panel_a_subtitle", "panel_subtitle", x0=0.09, y0=0.16, x1=0.27, y1=0.18),
                make_box("panel_b_title", "panel_title", x0=0.42, y0=0.12, x1=0.58, y1=0.16),
                make_box("panel_b_subtitle", "panel_subtitle", x0=0.42, y0=0.16, x1=0.58, y1=0.18),
                make_box("panel_c_title", "panel_title", x0=0.75, y0=0.12, x1=0.90, y1=0.16),
                make_box("panel_c_subtitle", "panel_subtitle", x0=0.75, y0=0.16, x1=0.92, y1=0.18),
                make_box("panel_a_card_1", "card_box", x0=0.08, y0=0.24, x1=0.28, y1=0.40),
                make_box("panel_a_card_2", "card_box", x0=0.08, y0=0.44, x1=0.18, y1=0.58),
                make_box("panel_a_card_3", "card_box", x0=0.19, y0=0.44, x1=0.28, y1=0.58),
                make_box("panel_b_card_1", "card_box", x0=0.41, y0=0.24, x1=0.61, y1=0.40),
                make_box("panel_b_card_2", "card_box", x0=0.41, y0=0.44, x1=0.61, y1=0.58),
                make_box("panel_c_card_1", "card_box", x0=0.74, y0=0.24, x1=0.94, y1=0.40),
                make_box("panel_c_card_2", "card_box", x0=0.74, y0=0.44, x1=0.83, y1=0.58),
                make_box("panel_c_card_3", "card_box", x0=0.85, y0=0.44, x1=0.94, y1=0.58),
                make_box("panel_a_card_1_title", "card_title", x0=0.10, y0=0.25, x1=0.22, y1=0.28),
                make_box("panel_a_card_1_value", "card_value", x0=0.10, y0=0.30, x1=0.20, y1=0.36),
                make_box("panel_a_card_1_detail", "card_detail", x0=0.10, y0=0.36, x1=0.24, y1=0.39),
                make_box("panel_b_card_1_title", "card_title", x0=0.43, y0=0.25, x1=0.55, y1=0.28),
                make_box("panel_b_card_1_value", "card_value", x0=0.43, y0=0.30, x1=0.52, y1=0.36),
                make_box("panel_b_card_1_detail", "card_detail", x0=0.43, y0=0.36, x1=0.59, y1=0.39),
                make_box("panel_c_card_1_title", "card_title", x0=0.76, y0=0.25, x1=0.90, y1=0.28),
                make_box("panel_c_card_1_value", "card_value", x0=0.76, y0=0.30, x1=0.86, y1=0.36),
                make_box("panel_c_card_1_detail", "card_detail", x0=0.76, y0=0.36, x1=0.92, y1=0.39),
                make_box("pill_a", "footer_pill", x0=0.11, y0=0.84, x1=0.25, y1=0.89),
                make_box("pill_b", "footer_pill", x0=0.44, y0=0.84, x1=0.58, y1=0.89),
                make_box("pill_c", "footer_pill", x0=0.77, y0=0.84, x1=0.92, y1=0.89),
            ],
            "panel_boxes": [
                make_box("panel_cohort", "panel", x0=0.04, y0=0.10, x1=0.30, y1=0.80),
                make_box("panel_primary", "panel", x0=0.37, y0=0.10, x1=0.63, y1=0.80),
                make_box("panel_supportive", "panel", x0=0.70, y0=0.10, x1=0.96, y1=0.80),
            ],
            "guide_boxes": [
                make_box("arrow_1", "arrow_connector", x0=0.31, y0=0.46, x1=0.36, y1=0.54),
                make_box("arrow_2", "arrow_connector", x0=0.64, y0=0.46, x1=0.69, y1=0.54),
            ],
            "metrics": {
                "panels": [
                    {"panel_id": "cohort_split"},
                    {"panel_id": "primary_endpoint"},
                    {"panel_id": "supportive_context"},
                ],
                "footer_pills": [
                    {"pill_id": "p1"},
                    {"pill_id": "p2"},
                    {"pill_id": "p3"},
                ],
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_passes_for_workflow_fact_sheet_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_workflow_fact_sheet_panel",
        layout_sidecar={
            "template_id": "workflow_fact_sheet_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.07, y0=0.10, x1=0.10, y1=0.14),
                make_box("panel_label_B", "panel_label", x0=0.55, y0=0.10, x1=0.58, y1=0.14),
                make_box("panel_label_C", "panel_label", x0=0.07, y0=0.54, x1=0.10, y1=0.58),
                make_box("panel_label_D", "panel_label", x0=0.55, y0=0.54, x1=0.58, y1=0.58),
                make_box("section_title_A", "section_title", x0=0.11, y0=0.10, x1=0.34, y1=0.14),
                make_box("section_title_B", "section_title", x0=0.59, y0=0.10, x1=0.82, y1=0.14),
                make_box("section_title_C", "section_title", x0=0.11, y0=0.54, x1=0.34, y1=0.58),
                make_box("section_title_D", "section_title", x0=0.59, y0=0.54, x1=0.82, y1=0.58),
                make_box("fact_label_A_1", "fact_label", x0=0.11, y0=0.18, x1=0.24, y1=0.22),
                make_box("fact_value_A_1", "fact_value", x0=0.26, y0=0.18, x1=0.42, y1=0.22),
                make_box("fact_label_B_1", "fact_label", x0=0.59, y0=0.18, x1=0.72, y1=0.22),
                make_box("fact_value_B_1", "fact_value", x0=0.74, y0=0.18, x1=0.90, y1=0.22),
                make_box("fact_label_C_1", "fact_label", x0=0.11, y0=0.62, x1=0.24, y1=0.66),
                make_box("fact_value_C_1", "fact_value", x0=0.26, y0=0.62, x1=0.42, y1=0.66),
                make_box("fact_label_D_1", "fact_label", x0=0.59, y0=0.62, x1=0.72, y1=0.66),
                make_box("fact_value_D_1", "fact_value", x0=0.74, y0=0.62, x1=0.90, y1=0.66),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.06, y0=0.08, x1=0.46, y1=0.46),
                make_box("panel_B", "panel", x0=0.54, y0=0.08, x1=0.94, y1=0.46),
                make_box("panel_C", "panel", x0=0.06, y0=0.52, x1=0.46, y1=0.90),
                make_box("panel_D", "panel", x0=0.54, y0=0.52, x1=0.94, y1=0.90),
            ],
            "guide_boxes": [],
            "metrics": {
                "sections": [
                    {
                        "section_id": "cohort",
                        "panel_label": "A",
                        "layout_role": "top_left",
                        "panel_box_id": "panel_A",
                        "title_box_id": "section_title_A",
                        "panel_label_box_id": "panel_label_A",
                        "facts": [{"fact_id": "cohort_n", "label_box_id": "fact_label_A_1", "value_box_id": "fact_value_A_1"}],
                    },
                    {
                        "section_id": "endpoint",
                        "panel_label": "B",
                        "layout_role": "top_right",
                        "panel_box_id": "panel_B",
                        "title_box_id": "section_title_B",
                        "panel_label_box_id": "panel_label_B",
                        "facts": [{"fact_id": "endpoint", "label_box_id": "fact_label_B_1", "value_box_id": "fact_value_B_1"}],
                    },
                    {
                        "section_id": "workflow",
                        "panel_label": "C",
                        "layout_role": "bottom_left",
                        "panel_box_id": "panel_C",
                        "title_box_id": "section_title_C",
                        "panel_label_box_id": "panel_label_C",
                        "facts": [{"fact_id": "model_family", "label_box_id": "fact_label_C_1", "value_box_id": "fact_value_C_1"}],
                    },
                    {
                        "section_id": "validation",
                        "panel_label": "D",
                        "layout_role": "bottom_right",
                        "panel_box_id": "panel_D",
                        "title_box_id": "section_title_D",
                        "panel_label_box_id": "panel_label_D",
                        "facts": [{"fact_id": "validation_scheme", "label_box_id": "fact_label_D_1", "value_box_id": "fact_value_D_1"}],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_workflow_fact_sheet_panel_label_is_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_workflow_fact_sheet_panel",
        layout_sidecar={
            "template_id": "workflow_fact_sheet_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.07, y0=0.10, x1=0.10, y1=0.14),
                make_box("panel_label_B", "panel_label", x0=0.55, y0=0.10, x1=0.58, y1=0.14),
                make_box("panel_label_C", "panel_label", x0=0.07, y0=0.54, x1=0.10, y1=0.58),
                make_box("section_title_A", "section_title", x0=0.11, y0=0.10, x1=0.34, y1=0.14),
                make_box("section_title_B", "section_title", x0=0.59, y0=0.10, x1=0.82, y1=0.14),
                make_box("section_title_C", "section_title", x0=0.11, y0=0.54, x1=0.34, y1=0.58),
                make_box("section_title_D", "section_title", x0=0.59, y0=0.54, x1=0.82, y1=0.58),
                make_box("fact_label_A_1", "fact_label", x0=0.11, y0=0.18, x1=0.24, y1=0.22),
                make_box("fact_value_A_1", "fact_value", x0=0.26, y0=0.18, x1=0.42, y1=0.22),
                make_box("fact_label_B_1", "fact_label", x0=0.59, y0=0.18, x1=0.72, y1=0.22),
                make_box("fact_value_B_1", "fact_value", x0=0.74, y0=0.18, x1=0.90, y1=0.22),
                make_box("fact_label_C_1", "fact_label", x0=0.11, y0=0.62, x1=0.24, y1=0.66),
                make_box("fact_value_C_1", "fact_value", x0=0.26, y0=0.62, x1=0.42, y1=0.66),
                make_box("fact_label_D_1", "fact_label", x0=0.59, y0=0.62, x1=0.72, y1=0.66),
                make_box("fact_value_D_1", "fact_value", x0=0.74, y0=0.62, x1=0.90, y1=0.66),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.06, y0=0.08, x1=0.46, y1=0.46),
                make_box("panel_B", "panel", x0=0.54, y0=0.08, x1=0.94, y1=0.46),
                make_box("panel_C", "panel", x0=0.06, y0=0.52, x1=0.46, y1=0.90),
                make_box("panel_D", "panel", x0=0.54, y0=0.52, x1=0.94, y1=0.90),
            ],
            "guide_boxes": [],
            "metrics": {
                "sections": [
                    {
                        "section_id": "cohort",
                        "panel_label": "A",
                        "layout_role": "top_left",
                        "panel_box_id": "panel_A",
                        "title_box_id": "section_title_A",
                        "panel_label_box_id": "panel_label_A",
                        "facts": [{"fact_id": "cohort_n", "label_box_id": "fact_label_A_1", "value_box_id": "fact_value_A_1"}],
                    },
                    {
                        "section_id": "endpoint",
                        "panel_label": "B",
                        "layout_role": "top_right",
                        "panel_box_id": "panel_B",
                        "title_box_id": "section_title_B",
                        "panel_label_box_id": "panel_label_B",
                        "facts": [{"fact_id": "endpoint", "label_box_id": "fact_label_B_1", "value_box_id": "fact_value_B_1"}],
                    },
                    {
                        "section_id": "workflow",
                        "panel_label": "C",
                        "layout_role": "bottom_left",
                        "panel_box_id": "panel_C",
                        "title_box_id": "section_title_C",
                        "panel_label_box_id": "panel_label_C",
                        "facts": [{"fact_id": "model_family", "label_box_id": "fact_label_C_1", "value_box_id": "fact_value_C_1"}],
                    },
                    {
                        "section_id": "validation",
                        "panel_label": "D",
                        "layout_role": "bottom_right",
                        "panel_box_id": "panel_D",
                        "title_box_id": "section_title_D",
                        "panel_label_box_id": "panel_label_D",
                        "facts": [{"fact_id": "validation_scheme", "label_box_id": "fact_label_D_1", "value_box_id": "fact_value_D_1"}],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "panel_label_missing" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_design_evidence_composite_shell() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_design_evidence_composite_shell",
        layout_sidecar={
            "template_id": "design_evidence_composite_shell",
            "device": make_device(),
            "layout_boxes": [
                make_box("stage_title_1", "stage_title", x0=0.08, y0=0.08, x1=0.24, y1=0.12),
                make_box("stage_detail_1", "stage_detail", x0=0.08, y0=0.13, x1=0.24, y1=0.18),
                make_box("stage_title_2", "stage_title", x0=0.39, y0=0.08, x1=0.55, y1=0.12),
                make_box("stage_detail_2", "stage_detail", x0=0.39, y0=0.13, x1=0.55, y1=0.18),
                make_box("stage_title_3", "stage_title", x0=0.70, y0=0.08, x1=0.86, y1=0.12),
                make_box("stage_detail_3", "stage_detail", x0=0.70, y0=0.13, x1=0.86, y1=0.18),
                make_box("panel_label_A", "panel_label", x0=0.07, y0=0.38, x1=0.10, y1=0.42),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.38, x1=0.41, y1=0.42),
                make_box("panel_label_C", "panel_label", x0=0.69, y0=0.38, x1=0.72, y1=0.42),
                make_box("summary_title_A", "summary_title", x0=0.11, y0=0.38, x1=0.28, y1=0.42),
                make_box("summary_title_B", "summary_title", x0=0.42, y0=0.38, x1=0.59, y1=0.42),
                make_box("summary_title_C", "summary_title", x0=0.73, y0=0.38, x1=0.90, y1=0.42),
                make_box("card_label_A_1", "card_label", x0=0.09, y0=0.48, x1=0.18, y1=0.51),
                make_box("card_value_A_1", "card_value", x0=0.09, y0=0.52, x1=0.20, y1=0.57),
                make_box("card_label_B_1", "card_label", x0=0.40, y0=0.48, x1=0.49, y1=0.51),
                make_box("card_value_B_1", "card_value", x0=0.40, y0=0.52, x1=0.51, y1=0.57),
                make_box("card_label_C_1", "card_label", x0=0.71, y0=0.48, x1=0.80, y1=0.51),
                make_box("card_value_C_1", "card_value", x0=0.71, y0=0.52, x1=0.82, y1=0.57),
            ],
            "panel_boxes": [
                make_box("workflow_stage_1", "workflow_stage", x0=0.05, y0=0.05, x1=0.28, y1=0.21),
                make_box("workflow_stage_2", "workflow_stage", x0=0.36, y0=0.05, x1=0.59, y1=0.21),
                make_box("workflow_stage_3", "workflow_stage", x0=0.67, y0=0.05, x1=0.90, y1=0.21),
                make_box("summary_panel_A", "panel", x0=0.05, y0=0.34, x1=0.30, y1=0.88),
                make_box("summary_panel_B", "panel", x0=0.36, y0=0.34, x1=0.61, y1=0.88),
                make_box("summary_panel_C", "panel", x0=0.67, y0=0.34, x1=0.92, y1=0.88),
            ],
            "guide_boxes": [
                make_box("stage_arrow_1", "arrow_connector", x0=0.29, y0=0.11, x1=0.35, y1=0.15),
                make_box("stage_arrow_2", "arrow_connector", x0=0.60, y0=0.11, x1=0.66, y1=0.15),
            ],
            "metrics": {
                "workflow_stages": [
                    {"stage_id": "cohort", "stage_box_id": "workflow_stage_1", "title_box_id": "stage_title_1", "detail_box_id": "stage_detail_1"},
                    {"stage_id": "modeling", "stage_box_id": "workflow_stage_2", "title_box_id": "stage_title_2", "detail_box_id": "stage_detail_2"},
                    {"stage_id": "validation", "stage_box_id": "workflow_stage_3", "title_box_id": "stage_title_3", "detail_box_id": "stage_detail_3"},
                ],
                "summary_panels": [
                    {
                        "panel_id": "cohort_summary",
                        "panel_label": "A",
                        "layout_role": "left",
                        "panel_box_id": "summary_panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "title_box_id": "summary_title_A",
                        "cards": [{"card_id": "train_n", "label_box_id": "card_label_A_1", "value_box_id": "card_value_A_1"}],
                    },
                    {
                        "panel_id": "endpoint_summary",
                        "panel_label": "B",
                        "layout_role": "center",
                        "panel_box_id": "summary_panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "title_box_id": "summary_title_B",
                        "cards": [{"card_id": "endpoint", "label_box_id": "card_label_B_1", "value_box_id": "card_value_B_1"}],
                    },
                    {
                        "panel_id": "evidence_summary",
                        "panel_label": "C",
                        "layout_role": "right",
                        "panel_box_id": "summary_panel_C",
                        "panel_label_box_id": "panel_label_C",
                        "title_box_id": "summary_title_C",
                        "cards": [{"card_id": "auc", "label_box_id": "card_label_C_1", "value_box_id": "card_value_C_1"}],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_design_evidence_composite_shell_panel_label_is_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_design_evidence_composite_shell",
        layout_sidecar={
            "template_id": "design_evidence_composite_shell",
            "device": make_device(),
            "layout_boxes": [
                make_box("stage_title_1", "stage_title", x0=0.08, y0=0.08, x1=0.24, y1=0.12),
                make_box("stage_title_2", "stage_title", x0=0.39, y0=0.08, x1=0.55, y1=0.12),
                make_box("stage_title_3", "stage_title", x0=0.70, y0=0.08, x1=0.86, y1=0.12),
                make_box("panel_label_A", "panel_label", x0=0.07, y0=0.38, x1=0.10, y1=0.42),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.38, x1=0.41, y1=0.42),
                make_box("summary_title_A", "summary_title", x0=0.11, y0=0.38, x1=0.28, y1=0.42),
                make_box("summary_title_B", "summary_title", x0=0.42, y0=0.38, x1=0.59, y1=0.42),
                make_box("summary_title_C", "summary_title", x0=0.73, y0=0.38, x1=0.90, y1=0.42),
                make_box("card_label_A_1", "card_label", x0=0.09, y0=0.48, x1=0.18, y1=0.51),
                make_box("card_value_A_1", "card_value", x0=0.09, y0=0.52, x1=0.20, y1=0.57),
                make_box("card_label_B_1", "card_label", x0=0.40, y0=0.48, x1=0.49, y1=0.51),
                make_box("card_value_B_1", "card_value", x0=0.40, y0=0.52, x1=0.51, y1=0.57),
                make_box("card_label_C_1", "card_label", x0=0.71, y0=0.48, x1=0.80, y1=0.51),
                make_box("card_value_C_1", "card_value", x0=0.71, y0=0.52, x1=0.82, y1=0.57),
            ],
            "panel_boxes": [
                make_box("workflow_stage_1", "workflow_stage", x0=0.05, y0=0.05, x1=0.28, y1=0.21),
                make_box("workflow_stage_2", "workflow_stage", x0=0.36, y0=0.05, x1=0.59, y1=0.21),
                make_box("workflow_stage_3", "workflow_stage", x0=0.67, y0=0.05, x1=0.90, y1=0.21),
                make_box("summary_panel_A", "panel", x0=0.05, y0=0.34, x1=0.30, y1=0.88),
                make_box("summary_panel_B", "panel", x0=0.36, y0=0.34, x1=0.61, y1=0.88),
                make_box("summary_panel_C", "panel", x0=0.67, y0=0.34, x1=0.92, y1=0.88),
            ],
            "guide_boxes": [],
            "metrics": {
                "workflow_stages": [
                    {"stage_id": "cohort", "stage_box_id": "workflow_stage_1", "title_box_id": "stage_title_1"},
                    {"stage_id": "modeling", "stage_box_id": "workflow_stage_2", "title_box_id": "stage_title_2"},
                    {"stage_id": "validation", "stage_box_id": "workflow_stage_3", "title_box_id": "stage_title_3"},
                ],
                "summary_panels": [
                    {
                        "panel_id": "cohort_summary",
                        "panel_label": "A",
                        "layout_role": "left",
                        "panel_box_id": "summary_panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "title_box_id": "summary_title_A",
                        "cards": [{"card_id": "train_n", "label_box_id": "card_label_A_1", "value_box_id": "card_value_A_1"}],
                    },
                    {
                        "panel_id": "endpoint_summary",
                        "panel_label": "B",
                        "layout_role": "center",
                        "panel_box_id": "summary_panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "title_box_id": "summary_title_B",
                        "cards": [{"card_id": "endpoint", "label_box_id": "card_label_B_1", "value_box_id": "card_value_B_1"}],
                    },
                    {
                        "panel_id": "evidence_summary",
                        "panel_label": "C",
                        "layout_role": "right",
                        "panel_box_id": "summary_panel_C",
                        "panel_label_box_id": "panel_label_C",
                        "title_box_id": "summary_title_C",
                        "cards": [{"card_id": "auc", "label_box_id": "card_label_C_1", "value_box_id": "card_value_C_1"}],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "panel_label_missing" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_baseline_missingness_qc_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_baseline_missingness_qc_panel",
        layout_sidecar={
            "template_id": "baseline_missingness_qc_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.06, y0=0.08, x1=0.09, y1=0.12),
                make_box("panel_label_B", "panel_label", x0=0.58, y0=0.08, x1=0.61, y1=0.12),
                make_box("panel_label_C", "panel_label", x0=0.58, y0=0.58, x1=0.61, y1=0.62),
                make_box("balance_panel_title", "panel_title", x0=0.10, y0=0.08, x1=0.33, y1=0.12),
                make_box("balance_x_axis_title", "subplot_x_axis_title", x0=0.14, y0=0.84, x1=0.40, y1=0.88),
                make_box("missingness_panel_title", "panel_title", x0=0.63, y0=0.08, x1=0.86, y1=0.12),
                make_box("missingness_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.44, x1=0.88, y1=0.48),
                make_box("missingness_y_axis_title", "subplot_y_axis_title", x0=0.56, y0=0.18, x1=0.60, y1=0.38),
                make_box("qc_panel_title", "panel_title", x0=0.63, y0=0.58, x1=0.82, y1=0.62),
                make_box("qc_card_label_retained", "card_label", x0=0.63, y0=0.68, x1=0.74, y1=0.71),
                make_box("qc_card_value_retained", "card_value", x0=0.63, y0=0.72, x1=0.74, y1=0.77),
                make_box("qc_card_label_missing", "card_label", x0=0.77, y0=0.68, x1=0.89, y1=0.71),
                make_box("qc_card_value_missing", "card_value", x0=0.77, y0=0.72, x1=0.89, y1=0.77),
            ],
            "panel_boxes": [
                make_box("panel_balance", "panel", x0=0.04, y0=0.06, x1=0.48, y1=0.90),
                make_box("panel_missingness", "panel", x0=0.56, y0=0.06, x1=0.94, y1=0.50),
                make_box("panel_qc", "panel", x0=0.56, y0=0.56, x1=0.94, y1=0.90),
            ],
            "guide_boxes": [
                make_box("balance_threshold", "reference_line", x0=0.24, y0=0.16, x1=0.25, y1=0.82),
                make_box("missingness_colorbar", "colorbar", x0=0.90, y0=0.14, x1=0.92, y1=0.42),
            ],
            "metrics": {
                "primary_balance_label": "Pre-adjustment SMD",
                "secondary_balance_label": "Post-adjustment SMD",
                "balance_threshold": 0.10,
                "balance_variables": [
                    {"variable_id": "age", "label": "Age", "primary_value": 0.24, "secondary_value": 0.08},
                    {"variable_id": "sex", "label": "Female sex", "primary_value": 0.11, "secondary_value": 0.04},
                ],
                "missingness_rows": [{"label": "Age"}, {"label": "HbA1c"}],
                "missingness_columns": [{"label": "Train"}, {"label": "Validation"}],
                "missingness_cells": [
                    {"x": "Train", "y": "Age", "value": 0.01},
                    {"x": "Validation", "y": "Age", "value": 0.03},
                    {"x": "Train", "y": "HbA1c", "value": 0.08},
                    {"x": "Validation", "y": "HbA1c", "value": 0.11},
                ],
                "qc_cards": [
                    {"card_id": "retained", "label_box_id": "qc_card_label_retained", "value_box_id": "qc_card_value_retained"},
                    {"card_id": "max_missing", "label_box_id": "qc_card_label_missing", "value_box_id": "qc_card_value_missing"},
                ],
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_baseline_missingness_qc_grid_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_baseline_missingness_qc_panel",
        layout_sidecar={
            "template_id": "baseline_missingness_qc_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.06, y0=0.08, x1=0.09, y1=0.12),
                make_box("panel_label_B", "panel_label", x0=0.58, y0=0.08, x1=0.61, y1=0.12),
                make_box("panel_label_C", "panel_label", x0=0.58, y0=0.58, x1=0.61, y1=0.62),
                make_box("balance_panel_title", "panel_title", x0=0.10, y0=0.08, x1=0.33, y1=0.12),
                make_box("balance_x_axis_title", "subplot_x_axis_title", x0=0.14, y0=0.84, x1=0.40, y1=0.88),
                make_box("missingness_panel_title", "panel_title", x0=0.63, y0=0.08, x1=0.86, y1=0.12),
                make_box("missingness_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.44, x1=0.88, y1=0.48),
                make_box("missingness_y_axis_title", "subplot_y_axis_title", x0=0.56, y0=0.18, x1=0.60, y1=0.38),
                make_box("qc_panel_title", "panel_title", x0=0.63, y0=0.58, x1=0.82, y1=0.62),
                make_box("qc_card_label_retained", "card_label", x0=0.63, y0=0.68, x1=0.74, y1=0.71),
                make_box("qc_card_value_retained", "card_value", x0=0.63, y0=0.72, x1=0.74, y1=0.77),
            ],
            "panel_boxes": [
                make_box("panel_balance", "panel", x0=0.04, y0=0.06, x1=0.48, y1=0.90),
                make_box("panel_missingness", "panel", x0=0.56, y0=0.06, x1=0.94, y1=0.50),
                make_box("panel_qc", "panel", x0=0.56, y0=0.56, x1=0.94, y1=0.90),
            ],
            "guide_boxes": [
                make_box("balance_threshold", "reference_line", x0=0.24, y0=0.16, x1=0.25, y1=0.82),
            ],
            "metrics": {
                "primary_balance_label": "Pre-adjustment SMD",
                "balance_threshold": 0.10,
                "balance_variables": [
                    {"variable_id": "age", "label": "Age", "primary_value": 0.24},
                    {"variable_id": "sex", "label": "Female sex", "primary_value": 0.11},
                ],
                "missingness_rows": [{"label": "Age"}, {"label": "HbA1c"}],
                "missingness_columns": [{"label": "Train"}, {"label": "Validation"}],
                "missingness_cells": [
                    {"x": "Train", "y": "Age", "value": 0.01},
                    {"x": "Validation", "y": "Age", "value": 0.03},
                    {"x": "Train", "y": "HbA1c", "value": 0.08},
                ],
                "qc_cards": [
                    {"card_id": "retained", "label_box_id": "qc_card_label_retained", "value_box_id": "qc_card_value_retained"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "declared_missingness_grid_incomplete" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_center_coverage_batch_transportability_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_center_coverage_batch_transportability_panel",
        layout_sidecar={
            "template_id": "center_coverage_batch_transportability_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.06, y0=0.08, x1=0.09, y1=0.12),
                make_box("panel_label_B", "panel_label", x0=0.58, y0=0.08, x1=0.61, y1=0.12),
                make_box("panel_label_C", "panel_label", x0=0.58, y0=0.58, x1=0.61, y1=0.62),
                make_box("coverage_panel_title", "panel_title", x0=0.10, y0=0.08, x1=0.34, y1=0.12),
                make_box("coverage_x_axis_title", "subplot_x_axis_title", x0=0.15, y0=0.84, x1=0.41, y1=0.88),
                make_box("batch_panel_title", "panel_title", x0=0.63, y0=0.08, x1=0.86, y1=0.12),
                make_box("batch_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.44, x1=0.88, y1=0.48),
                make_box("batch_y_axis_title", "subplot_y_axis_title", x0=0.56, y0=0.18, x1=0.60, y1=0.38),
                make_box("transportability_panel_title", "panel_title", x0=0.63, y0=0.58, x1=0.86, y1=0.62),
                make_box("transport_card_label_centers", "card_label", x0=0.63, y0=0.68, x1=0.77, y1=0.71),
                make_box("transport_card_value_centers", "card_value", x0=0.63, y0=0.72, x1=0.77, y1=0.77),
                make_box("transport_card_label_shift", "card_label", x0=0.63, y0=0.79, x1=0.77, y1=0.82),
                make_box("transport_card_value_shift", "card_value", x0=0.63, y0=0.83, x1=0.77, y1=0.88),
            ],
            "panel_boxes": [
                make_box("panel_coverage", "panel", x0=0.04, y0=0.06, x1=0.48, y1=0.90),
                make_box("panel_batch", "panel", x0=0.56, y0=0.06, x1=0.94, y1=0.50),
                make_box("panel_transportability", "panel", x0=0.56, y0=0.56, x1=0.94, y1=0.90),
            ],
            "guide_boxes": [
                make_box("batch_threshold", "reference_line", x0=0.88, y0=0.14, x1=0.89, y1=0.42),
                make_box("batch_colorbar", "colorbar", x0=0.90, y0=0.14, x1=0.92, y1=0.42),
            ],
            "metrics": {
                "batch_threshold": 0.20,
                "center_rows": [
                    {
                        "center_id": "train_a",
                        "center_label": "Train A",
                        "cohort_role": "Derivation",
                        "support_count": 412,
                        "event_count": 63,
                    },
                    {
                        "center_id": "external_b",
                        "center_label": "External B",
                        "cohort_role": "External",
                        "support_count": 188,
                        "event_count": 29,
                    },
                ],
                "batch_rows": [{"label": "Train A"}, {"label": "External B"}],
                "batch_columns": [{"label": "Specimen drift"}, {"label": "Scanner drift"}],
                "batch_cells": [
                    {"x": "Specimen drift", "y": "Train A", "value": 0.08},
                    {"x": "Scanner drift", "y": "Train A", "value": 0.11},
                    {"x": "Specimen drift", "y": "External B", "value": 0.14},
                    {"x": "Scanner drift", "y": "External B", "value": 0.18},
                ],
                "transportability_cards": [
                    {
                        "card_id": "covered_centers",
                        "label_box_id": "transport_card_label_centers",
                        "value_box_id": "transport_card_value_centers",
                    },
                    {
                        "card_id": "largest_shift",
                        "label_box_id": "transport_card_label_shift",
                        "value_box_id": "transport_card_value_shift",
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_center_coverage_batch_grid_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_center_coverage_batch_transportability_panel",
        layout_sidecar={
            "template_id": "center_coverage_batch_transportability_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.06, y0=0.08, x1=0.09, y1=0.12),
                make_box("panel_label_B", "panel_label", x0=0.58, y0=0.08, x1=0.61, y1=0.12),
                make_box("panel_label_C", "panel_label", x0=0.58, y0=0.58, x1=0.61, y1=0.62),
                make_box("coverage_panel_title", "panel_title", x0=0.10, y0=0.08, x1=0.34, y1=0.12),
                make_box("coverage_x_axis_title", "subplot_x_axis_title", x0=0.15, y0=0.84, x1=0.41, y1=0.88),
                make_box("batch_panel_title", "panel_title", x0=0.63, y0=0.08, x1=0.86, y1=0.12),
                make_box("batch_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.44, x1=0.88, y1=0.48),
                make_box("batch_y_axis_title", "subplot_y_axis_title", x0=0.56, y0=0.18, x1=0.60, y1=0.38),
                make_box("transportability_panel_title", "panel_title", x0=0.63, y0=0.58, x1=0.86, y1=0.62),
                make_box("transport_card_label_centers", "card_label", x0=0.63, y0=0.68, x1=0.77, y1=0.71),
                make_box("transport_card_value_centers", "card_value", x0=0.63, y0=0.72, x1=0.77, y1=0.77),
            ],
            "panel_boxes": [
                make_box("panel_coverage", "panel", x0=0.04, y0=0.06, x1=0.48, y1=0.90),
                make_box("panel_batch", "panel", x0=0.56, y0=0.06, x1=0.94, y1=0.50),
                make_box("panel_transportability", "panel", x0=0.56, y0=0.56, x1=0.94, y1=0.90),
            ],
            "guide_boxes": [
                make_box("batch_threshold", "reference_line", x0=0.88, y0=0.14, x1=0.89, y1=0.42),
            ],
            "metrics": {
                "batch_threshold": 0.20,
                "center_rows": [
                    {
                        "center_id": "train_a",
                        "center_label": "Train A",
                        "cohort_role": "Derivation",
                        "support_count": 412,
                        "event_count": 63,
                    },
                ],
                "batch_rows": [{"label": "Train A"}, {"label": "External B"}],
                "batch_columns": [{"label": "Specimen drift"}, {"label": "Scanner drift"}],
                "batch_cells": [
                    {"x": "Specimen drift", "y": "Train A", "value": 0.08},
                    {"x": "Scanner drift", "y": "Train A", "value": 0.11},
                    {"x": "Specimen drift", "y": "External B", "value": 0.14},
                ],
                "transportability_cards": [
                    {
                        "card_id": "covered_centers",
                        "label_box_id": "transport_card_label_centers",
                        "value_box_id": "transport_card_value_centers",
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "declared_batch_grid_incomplete" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_transportability_recalibration_governance_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_transportability_recalibration_governance_panel",
        layout_sidecar={
            "template_id": "transportability_recalibration_governance_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.06, y0=0.08, x1=0.09, y1=0.12),
                make_box("panel_label_B", "panel_label", x0=0.58, y0=0.08, x1=0.61, y1=0.12),
                make_box("panel_label_C", "panel_label", x0=0.58, y0=0.58, x1=0.61, y1=0.62),
                make_box("coverage_panel_title", "panel_title", x0=0.10, y0=0.08, x1=0.34, y1=0.12),
                make_box("coverage_x_axis_title", "subplot_x_axis_title", x0=0.15, y0=0.84, x1=0.41, y1=0.88),
                make_box("batch_panel_title", "panel_title", x0=0.63, y0=0.08, x1=0.86, y1=0.12),
                make_box("batch_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.44, x1=0.88, y1=0.48),
                make_box("batch_y_axis_title", "subplot_y_axis_title", x0=0.56, y0=0.18, x1=0.60, y1=0.38),
                make_box("recalibration_panel_title", "panel_title", x0=0.62, y0=0.58, x1=0.88, y1=0.62),
                make_box("recalibration_row_label_train_a", "row_label", x0=0.62, y0=0.68, x1=0.72, y1=0.72),
                make_box("recalibration_row_slope_train_a", "row_metric", x0=0.62, y0=0.73, x1=0.71, y1=0.77),
                make_box("recalibration_row_oe_train_a", "row_metric", x0=0.73, y0=0.73, x1=0.82, y1=0.77),
                make_box("recalibration_row_action_train_a", "row_action", x0=0.83, y0=0.71, x1=0.92, y1=0.77),
                make_box("recalibration_row_label_external_b", "row_label", x0=0.62, y0=0.80, x1=0.75, y1=0.84),
                make_box("recalibration_row_slope_external_b", "row_metric", x0=0.62, y0=0.85, x1=0.71, y1=0.89),
                make_box("recalibration_row_oe_external_b", "row_metric", x0=0.73, y0=0.85, x1=0.82, y1=0.89),
                make_box("recalibration_row_action_external_b", "row_action", x0=0.83, y0=0.83, x1=0.92, y1=0.89),
            ],
            "panel_boxes": [
                make_box("panel_coverage", "panel", x0=0.04, y0=0.06, x1=0.48, y1=0.90),
                make_box("panel_batch", "panel", x0=0.56, y0=0.06, x1=0.94, y1=0.50),
                make_box("panel_recalibration", "panel", x0=0.56, y0=0.56, x1=0.94, y1=0.90),
            ],
            "guide_boxes": [
                make_box("batch_threshold", "reference_line", x0=0.88, y0=0.14, x1=0.89, y1=0.42),
                make_box("batch_colorbar", "colorbar", x0=0.90, y0=0.14, x1=0.92, y1=0.42),
            ],
            "metrics": {
                "batch_threshold": 0.20,
                "slope_acceptance_lower": 0.90,
                "slope_acceptance_upper": 1.10,
                "oe_ratio_acceptance_lower": 0.90,
                "oe_ratio_acceptance_upper": 1.10,
                "center_rows": [
                    {
                        "center_id": "train_a",
                        "center_label": "Train A",
                        "cohort_role": "Derivation",
                        "support_count": 412,
                        "event_count": 63,
                    },
                    {
                        "center_id": "external_b",
                        "center_label": "External B",
                        "cohort_role": "External",
                        "support_count": 188,
                        "event_count": 29,
                    },
                ],
                "batch_rows": [{"label": "Train A"}, {"label": "External B"}],
                "batch_columns": [{"label": "Specimen drift"}, {"label": "Scanner drift"}],
                "batch_cells": [
                    {"x": "Specimen drift", "y": "Train A", "value": 0.08},
                    {"x": "Scanner drift", "y": "Train A", "value": 0.11},
                    {"x": "Specimen drift", "y": "External B", "value": 0.14},
                    {"x": "Scanner drift", "y": "External B", "value": 0.18},
                ],
                "recalibration_rows": [
                    {
                        "center_id": "train_a",
                        "label_box_id": "recalibration_row_label_train_a",
                        "slope_box_id": "recalibration_row_slope_train_a",
                        "oe_ratio_box_id": "recalibration_row_oe_train_a",
                        "action_box_id": "recalibration_row_action_train_a",
                        "slope": 1.00,
                        "oe_ratio": 1.00,
                    },
                    {
                        "center_id": "external_b",
                        "label_box_id": "recalibration_row_label_external_b",
                        "slope_box_id": "recalibration_row_slope_external_b",
                        "oe_ratio_box_id": "recalibration_row_oe_external_b",
                        "action_box_id": "recalibration_row_action_external_b",
                        "slope": 0.84,
                        "oe_ratio": 1.18,
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_recalibration_center_coverage_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_transportability_recalibration_governance_panel",
        layout_sidecar={
            "template_id": "transportability_recalibration_governance_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.06, y0=0.08, x1=0.09, y1=0.12),
                make_box("panel_label_B", "panel_label", x0=0.58, y0=0.08, x1=0.61, y1=0.12),
                make_box("panel_label_C", "panel_label", x0=0.58, y0=0.58, x1=0.61, y1=0.62),
                make_box("coverage_panel_title", "panel_title", x0=0.10, y0=0.08, x1=0.34, y1=0.12),
                make_box("coverage_x_axis_title", "subplot_x_axis_title", x0=0.15, y0=0.84, x1=0.41, y1=0.88),
                make_box("batch_panel_title", "panel_title", x0=0.63, y0=0.08, x1=0.86, y1=0.12),
                make_box("batch_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.44, x1=0.88, y1=0.48),
                make_box("batch_y_axis_title", "subplot_y_axis_title", x0=0.56, y0=0.18, x1=0.60, y1=0.38),
                make_box("recalibration_panel_title", "panel_title", x0=0.62, y0=0.58, x1=0.88, y1=0.62),
                make_box("recalibration_row_label_train_a", "row_label", x0=0.62, y0=0.68, x1=0.72, y1=0.72),
                make_box("recalibration_row_slope_train_a", "row_metric", x0=0.62, y0=0.73, x1=0.71, y1=0.77),
                make_box("recalibration_row_oe_train_a", "row_metric", x0=0.73, y0=0.73, x1=0.82, y1=0.77),
                make_box("recalibration_row_action_train_a", "row_action", x0=0.83, y0=0.71, x1=0.92, y1=0.77),
            ],
            "panel_boxes": [
                make_box("panel_coverage", "panel", x0=0.04, y0=0.06, x1=0.48, y1=0.90),
                make_box("panel_batch", "panel", x0=0.56, y0=0.06, x1=0.94, y1=0.50),
                make_box("panel_recalibration", "panel", x0=0.56, y0=0.56, x1=0.94, y1=0.90),
            ],
            "guide_boxes": [
                make_box("batch_threshold", "reference_line", x0=0.88, y0=0.14, x1=0.89, y1=0.42),
                make_box("batch_colorbar", "colorbar", x0=0.90, y0=0.14, x1=0.92, y1=0.42),
            ],
            "metrics": {
                "batch_threshold": 0.20,
                "slope_acceptance_lower": 0.90,
                "slope_acceptance_upper": 1.10,
                "oe_ratio_acceptance_lower": 0.90,
                "oe_ratio_acceptance_upper": 1.10,
                "center_rows": [
                    {
                        "center_id": "train_a",
                        "center_label": "Train A",
                        "cohort_role": "Derivation",
                        "support_count": 412,
                        "event_count": 63,
                    },
                    {
                        "center_id": "external_b",
                        "center_label": "External B",
                        "cohort_role": "External",
                        "support_count": 188,
                        "event_count": 29,
                    },
                ],
                "batch_rows": [{"label": "Train A"}, {"label": "External B"}],
                "batch_columns": [{"label": "Specimen drift"}, {"label": "Scanner drift"}],
                "batch_cells": [
                    {"x": "Specimen drift", "y": "Train A", "value": 0.08},
                    {"x": "Scanner drift", "y": "Train A", "value": 0.11},
                    {"x": "Specimen drift", "y": "External B", "value": 0.14},
                    {"x": "Scanner drift", "y": "External B", "value": 0.18},
                ],
                "recalibration_rows": [
                    {
                        "center_id": "train_a",
                        "label_box_id": "recalibration_row_label_train_a",
                        "slope_box_id": "recalibration_row_slope_train_a",
                        "oe_ratio_box_id": "recalibration_row_oe_train_a",
                        "action_box_id": "recalibration_row_action_train_a",
                        "slope": 1.00,
                        "oe_ratio": 1.00,
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "recalibration_rows_incomplete" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_center_transportability_governance_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_center_transportability_governance_summary_panel",
        layout_sidecar={
            "template_id": "center_transportability_governance_summary_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.16, y0=0.86, x1=0.46, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.69, y0=0.86, x1=0.92, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.16, y0=0.78, x1=0.18, y1=0.81),
                make_box("panel_label_B", "panel_label", x0=0.69, y0=0.78, x1=0.71, y1=0.81),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.28, y0=0.10, x1=0.42, y1=0.13),
                make_box("row_label_train_a", "row_label", x0=0.04, y0=0.63, x1=0.15, y1=0.67),
                make_box("row_label_validation_c", "row_label", x0=0.02, y0=0.48, x1=0.15, y1=0.52),
                make_box("row_label_external_b", "row_label", x0=0.04, y0=0.33, x1=0.15, y1=0.37),
                make_box("metric_train_a", "estimate_marker", x0=0.34, y0=0.63, x1=0.35, y1=0.67),
                make_box("metric_validation_c", "estimate_marker", x0=0.31, y0=0.48, x1=0.32, y1=0.52),
                make_box("metric_external_b", "estimate_marker", x0=0.27, y0=0.33, x1=0.28, y1=0.37),
                make_box("ci_train_a", "ci_segment", x0=0.30, y0=0.645, x1=0.39, y1=0.655),
                make_box("ci_validation_c", "ci_segment", x0=0.27, y0=0.495, x1=0.36, y1=0.505),
                make_box("ci_external_b", "ci_segment", x0=0.23, y0=0.345, x1=0.32, y1=0.355),
                make_box("verdict_train_a", "verdict_value", x0=0.73, y0=0.64, x1=0.83, y1=0.68),
                make_box("metrics_train_a", "row_metric", x0=0.73, y0=0.59, x1=0.91, y1=0.63),
                make_box("action_train_a", "row_action", x0=0.73, y0=0.54, x1=0.88, y1=0.58),
                make_box("detail_train_a", "verdict_detail", x0=0.73, y0=0.49, x1=0.92, y1=0.53),
                make_box("verdict_validation_c", "verdict_value", x0=0.73, y0=0.49, x1=0.83, y1=0.53),
                make_box("metrics_validation_c", "row_metric", x0=0.73, y0=0.44, x1=0.91, y1=0.48),
                make_box("action_validation_c", "row_action", x0=0.73, y0=0.39, x1=0.88, y1=0.43),
                make_box("detail_validation_c", "verdict_detail", x0=0.73, y0=0.34, x1=0.92, y1=0.38),
                make_box("verdict_external_b", "verdict_value", x0=0.73, y0=0.34, x1=0.86, y1=0.38),
                make_box("metrics_external_b", "row_metric", x0=0.73, y0=0.29, x1=0.91, y1=0.33),
                make_box("action_external_b", "row_action", x0=0.73, y0=0.24, x1=0.93, y1=0.28),
                make_box("detail_external_b", "verdict_detail", x0=0.73, y0=0.19, x1=0.92, y1=0.23),
            ],
            "panel_boxes": [
                make_box("metric_panel", "panel", x0=0.16, y0=0.18, x1=0.62, y1=0.82),
                make_box("summary_panel", "panel", x0=0.69, y0=0.18, x1=0.95, y1=0.82),
            ],
            "guide_boxes": [
                make_box("reference_line", "reference_line", x0=0.31, y0=0.18, x1=0.32, y1=0.82),
            ],
            "metrics": {
                "metric_family": "discrimination",
                "metric_reference_value": 0.80,
                "metric_panel": {
                    "panel_box_id": "metric_panel",
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
                "batch_shift_threshold": 0.20,
                "slope_acceptance_lower": 0.90,
                "slope_acceptance_upper": 1.10,
                "oe_ratio_acceptance_lower": 0.90,
                "oe_ratio_acceptance_upper": 1.10,
                "centers": [
                    {
                        "center_id": "train_a",
                        "center_label": "Train A",
                        "cohort_role": "Derivation",
                        "support_count": 412,
                        "event_count": 63,
                        "metric_estimate": 0.84,
                        "metric_lower": 0.80,
                        "metric_upper": 0.88,
                        "max_shift": 0.11,
                        "slope": 1.00,
                        "oe_ratio": 1.00,
                        "verdict": "stable",
                        "action": "Reference fit",
                        "detail": "Derivation center remains inside every declared governance band.",
                        "label_box_id": "row_label_train_a",
                        "metric_box_id": "metric_train_a",
                        "interval_box_id": "ci_train_a",
                        "verdict_box_id": "verdict_train_a",
                        "metrics_box_id": "metrics_train_a",
                        "action_box_id": "action_train_a",
                        "detail_box_id": "detail_train_a",
                    },
                    {
                        "center_id": "validation_c",
                        "center_label": "Validation C",
                        "cohort_role": "Internal validation",
                        "support_count": 236,
                        "event_count": 34,
                        "metric_estimate": 0.82,
                        "metric_lower": 0.78,
                        "metric_upper": 0.86,
                        "max_shift": 0.16,
                        "slope": 0.96,
                        "oe_ratio": 1.04,
                        "verdict": "stable",
                        "action": "Monitor only",
                        "detail": "Internal validation remains within the acceptance band.",
                        "label_box_id": "row_label_validation_c",
                        "metric_box_id": "metric_validation_c",
                        "interval_box_id": "ci_validation_c",
                        "verdict_box_id": "verdict_validation_c",
                        "metrics_box_id": "metrics_validation_c",
                        "action_box_id": "action_validation_c",
                        "detail_box_id": "detail_validation_c",
                    },
                    {
                        "center_id": "external_b",
                        "center_label": "External B",
                        "cohort_role": "External",
                        "support_count": 188,
                        "event_count": 29,
                        "metric_estimate": 0.78,
                        "metric_lower": 0.73,
                        "metric_upper": 0.83,
                        "max_shift": 0.18,
                        "slope": 0.84,
                        "oe_ratio": 1.18,
                        "verdict": "context_dependent",
                        "action": "Recalibrate before deployment",
                        "detail": "External center needs recalibration before any manuscript-facing transportability claim.",
                        "label_box_id": "row_label_external_b",
                        "metric_box_id": "metric_external_b",
                        "interval_box_id": "ci_external_b",
                        "verdict_box_id": "verdict_external_b",
                        "metrics_box_id": "metrics_external_b",
                        "action_box_id": "action_external_b",
                        "detail_box_id": "detail_external_b",
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_center_transportability_action_leaves_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_center_transportability_governance_summary_panel",
        layout_sidecar={
            "template_id": "center_transportability_governance_summary_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.16, y0=0.86, x1=0.46, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.69, y0=0.86, x1=0.92, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.16, y0=0.78, x1=0.18, y1=0.81),
                make_box("panel_label_B", "panel_label", x0=0.69, y0=0.78, x1=0.71, y1=0.81),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.28, y0=0.10, x1=0.42, y1=0.13),
                make_box("row_label_train_a", "row_label", x0=0.04, y0=0.63, x1=0.15, y1=0.67),
                make_box("metric_train_a", "estimate_marker", x0=0.34, y0=0.63, x1=0.35, y1=0.67),
                make_box("ci_train_a", "ci_segment", x0=0.30, y0=0.645, x1=0.39, y1=0.655),
                make_box("verdict_train_a", "verdict_value", x0=0.73, y0=0.64, x1=0.83, y1=0.68),
                make_box("metrics_train_a", "row_metric", x0=0.73, y0=0.59, x1=0.91, y1=0.63),
                make_box("action_train_a", "row_action", x0=0.96, y0=0.54, x1=0.99, y1=0.58),
                make_box("detail_train_a", "verdict_detail", x0=0.73, y0=0.49, x1=0.92, y1=0.53),
            ],
            "panel_boxes": [
                make_box("metric_panel", "panel", x0=0.16, y0=0.18, x1=0.62, y1=0.82),
                make_box("summary_panel", "panel", x0=0.69, y0=0.18, x1=0.95, y1=0.82),
            ],
            "guide_boxes": [
                make_box("reference_line", "reference_line", x0=0.31, y0=0.18, x1=0.32, y1=0.82),
            ],
            "metrics": {
                "metric_family": "discrimination",
                "metric_reference_value": 0.80,
                "metric_panel": {
                    "panel_box_id": "metric_panel",
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
                "batch_shift_threshold": 0.20,
                "slope_acceptance_lower": 0.90,
                "slope_acceptance_upper": 1.10,
                "oe_ratio_acceptance_lower": 0.90,
                "oe_ratio_acceptance_upper": 1.10,
                "centers": [
                    {
                        "center_id": "train_a",
                        "center_label": "Train A",
                        "cohort_role": "Derivation",
                        "support_count": 412,
                        "event_count": 63,
                        "metric_estimate": 0.84,
                        "metric_lower": 0.80,
                        "metric_upper": 0.88,
                        "max_shift": 0.11,
                        "slope": 1.00,
                        "oe_ratio": 1.00,
                        "verdict": "stable",
                        "action": "Reference fit",
                        "detail": "Derivation center remains inside every declared governance band.",
                        "label_box_id": "row_label_train_a",
                        "metric_box_id": "metric_train_a",
                        "interval_box_id": "ci_train_a",
                        "verdict_box_id": "verdict_train_a",
                        "metrics_box_id": "metrics_train_a",
                        "action_box_id": "action_train_a",
                        "detail_box_id": "detail_train_a",
                    }
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "action_box_outside_summary_panel" for issue in result["issues"])


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


def test_run_display_layout_qc_flags_unreadable_risk_separation() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "kaplan_meier_grouped",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.60, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.24, x1=0.06, y1=0.70),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.10, y0=0.16, x1=0.74, y1=0.88),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.78, y0=0.28, x1=0.96, y1=0.46),
            ],
            "metrics": {
                "groups": [
                    {"label": "Low risk", "times": [0.0, 5.0], "values": [1.0, 0.9980]},
                    {"label": "High risk", "times": [0.0, 5.0], "values": [1.0, 0.9975]},
                ]
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "risk_separation_not_readable" for issue in result["issues"])


def test_run_display_layout_qc_flags_non_monotonic_grouped_risk_summary() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "time_to_event_risk_group_summary",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.18, y0=0.92, x1=0.34, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.02, y0=0.20, x1=0.06, y1=0.72),
                make_box("panel_right_x_axis_title", "subplot_x_axis_title", x0=0.60, y0=0.92, x1=0.76, y1=0.97),
                make_box("panel_right_y_axis_title", "subplot_y_axis_title", x0=0.50, y0=0.20, x1=0.54, y1=0.72),
                make_box("panel_left_title", "panel_title", x0=0.16, y0=0.11, x1=0.34, y1=0.15),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.11, x1=0.80, y1=0.15),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.80, x1=0.14, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.55, y0=0.80, x1=0.58, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.16, x1=0.44, y1=0.86),
                make_box("panel_right", "panel", x0=0.54, y0=0.16, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [],
            "metrics": {
                "risk_group_summaries": [
                    {
                        "label": "Low risk",
                        "sample_size": 80,
                        "events_5y": 2,
                        "mean_predicted_risk_5y": 0.04,
                        "observed_km_risk_5y": 0.02,
                    },
                    {
                        "label": "Intermediate risk",
                        "sample_size": 80,
                        "events_5y": 7,
                        "mean_predicted_risk_5y": 0.11,
                        "observed_km_risk_5y": 0.09,
                    },
                    {
                        "label": "High risk",
                        "sample_size": 80,
                        "events_5y": 5,
                        "mean_predicted_risk_5y": 0.10,
                        "observed_km_risk_5y": 0.07,
                    },
                ],
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "predicted_risk_order_not_monotonic" for issue in result["issues"])
    assert any(issue["rule_id"] == "observed_risk_order_not_monotonic" for issue in result["issues"])
    assert any(issue["rule_id"] == "event_count_order_not_monotonic" for issue in result["issues"])


def test_run_display_layout_qc_flags_compressed_event_count_spread_for_grouped_risk_summary() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "time_to_event_risk_group_summary",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.18, y0=0.92, x1=0.34, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.02, y0=0.20, x1=0.06, y1=0.72),
                make_box("panel_right_x_axis_title", "subplot_x_axis_title", x0=0.60, y0=0.92, x1=0.76, y1=0.97),
                make_box("panel_right_y_axis_title", "subplot_y_axis_title", x0=0.50, y0=0.20, x1=0.54, y1=0.72),
                make_box("panel_left_title", "panel_title", x0=0.16, y0=0.11, x1=0.34, y1=0.15),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.11, x1=0.80, y1=0.15),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.80, x1=0.14, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.55, y0=0.80, x1=0.58, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.16, x1=0.44, y1=0.86),
                make_box("panel_right", "panel", x0=0.54, y0=0.16, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [],
            "metrics": {
                "risk_group_summaries": [
                    {
                        "label": "Low risk",
                        "sample_size": 60,
                        "events_5y": 3,
                        "mean_predicted_risk_5y": 0.04,
                        "observed_km_risk_5y": 0.02,
                    },
                    {
                        "label": "Intermediate risk",
                        "sample_size": 60,
                        "events_5y": 3,
                        "mean_predicted_risk_5y": 0.06,
                        "observed_km_risk_5y": 0.03,
                    },
                    {
                        "label": "High risk",
                        "sample_size": 60,
                        "events_5y": 3,
                        "mean_predicted_risk_5y": 0.08,
                        "observed_km_risk_5y": 0.05,
                    },
                ],
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "event_count_spread_not_readable" for issue in result["issues"])


def test_run_display_layout_qc_flags_compressed_observed_risk_spread_for_grouped_risk_summary() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "time_to_event_risk_group_summary",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.18, y0=0.92, x1=0.34, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.02, y0=0.20, x1=0.06, y1=0.72),
                make_box("panel_right_x_axis_title", "subplot_x_axis_title", x0=0.60, y0=0.92, x1=0.76, y1=0.97),
                make_box("panel_right_y_axis_title", "subplot_y_axis_title", x0=0.50, y0=0.20, x1=0.54, y1=0.72),
                make_box("panel_left_title", "panel_title", x0=0.16, y0=0.11, x1=0.34, y1=0.15),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.11, x1=0.80, y1=0.15),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.80, x1=0.14, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.55, y0=0.80, x1=0.58, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.16, x1=0.44, y1=0.86),
                make_box("panel_right", "panel", x0=0.54, y0=0.16, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [],
            "metrics": {
                "risk_group_summaries": [
                    {
                        "label": "Low risk",
                        "sample_size": 80,
                        "events_5y": 2,
                        "mean_predicted_risk_5y": 0.02,
                        "observed_km_risk_5y": 0.020,
                    },
                    {
                        "label": "Intermediate risk",
                        "sample_size": 80,
                        "events_5y": 6,
                        "mean_predicted_risk_5y": 0.03,
                        "observed_km_risk_5y": 0.024,
                    },
                    {
                        "label": "High risk",
                        "sample_size": 80,
                        "events_5y": 10,
                        "mean_predicted_risk_5y": 0.04,
                        "observed_km_risk_5y": 0.028,
                    },
                ],
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "observed_risk_spread_not_readable" for issue in result["issues"])


def test_run_display_layout_qc_flags_compressed_predicted_risk_spread_for_grouped_risk_summary() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "time_to_event_risk_group_summary",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.18, y0=0.92, x1=0.34, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.02, y0=0.20, x1=0.06, y1=0.72),
                make_box("panel_right_x_axis_title", "subplot_x_axis_title", x0=0.60, y0=0.92, x1=0.76, y1=0.97),
                make_box("panel_right_y_axis_title", "subplot_y_axis_title", x0=0.50, y0=0.20, x1=0.54, y1=0.72),
                make_box("panel_left_title", "panel_title", x0=0.16, y0=0.11, x1=0.34, y1=0.15),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.11, x1=0.80, y1=0.15),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.80, x1=0.14, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.55, y0=0.80, x1=0.58, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.16, x1=0.44, y1=0.86),
                make_box("panel_right", "panel", x0=0.54, y0=0.16, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [],
            "metrics": {
                "risk_group_summaries": [
                    {
                        "label": "Low risk",
                        "sample_size": 80,
                        "events_5y": 2,
                        "mean_predicted_risk_5y": 0.040,
                        "observed_km_risk_5y": 0.01,
                    },
                    {
                        "label": "Intermediate risk",
                        "sample_size": 80,
                        "events_5y": 6,
                        "mean_predicted_risk_5y": 0.042,
                        "observed_km_risk_5y": 0.03,
                    },
                    {
                        "label": "High risk",
                        "sample_size": 80,
                        "events_5y": 10,
                        "mean_predicted_risk_5y": 0.044,
                        "observed_km_risk_5y": 0.05,
                    },
                ],
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "predicted_risk_spread_not_readable" for issue in result["issues"])


def test_run_display_layout_qc_honors_readability_override_for_grouped_risk_summary() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "time_to_event_risk_group_summary",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.18, y0=0.92, x1=0.34, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.02, y0=0.20, x1=0.06, y1=0.72),
                make_box("panel_right_x_axis_title", "subplot_x_axis_title", x0=0.60, y0=0.92, x1=0.76, y1=0.97),
                make_box("panel_right_y_axis_title", "subplot_y_axis_title", x0=0.50, y0=0.20, x1=0.54, y1=0.72),
                make_box("panel_left_title", "panel_title", x0=0.16, y0=0.11, x1=0.34, y1=0.15),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.11, x1=0.80, y1=0.15),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.80, x1=0.14, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.55, y0=0.80, x1=0.58, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.16, x1=0.44, y1=0.86),
                make_box("panel_right", "panel", x0=0.54, y0=0.16, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [],
            "metrics": {
                "risk_group_summaries": [
                    {
                        "label": "Low risk",
                        "sample_size": 80,
                        "events_5y": 2,
                        "mean_predicted_risk_5y": 0.020,
                        "observed_km_risk_5y": 0.010,
                    },
                    {
                        "label": "Intermediate risk",
                        "sample_size": 80,
                        "events_5y": 6,
                        "mean_predicted_risk_5y": 0.026,
                        "observed_km_risk_5y": 0.030,
                    },
                    {
                        "label": "High risk",
                        "sample_size": 80,
                        "events_5y": 10,
                        "mean_predicted_risk_5y": 0.032,
                        "observed_km_risk_5y": 0.050,
                    },
                ],
            },
            "render_context": {
                "readability_override": {
                    "minimum_predicted_risk_spread": 0.02,
                }
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "predicted_risk_spread_not_readable" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_decision_curve_series_lengths_mismatch() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_decision_curve",
        layout_sidecar={
            "template_id": "time_to_event_decision_curve",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.60, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.32, y0=0.92, x1=0.62, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.24, x1=0.06, y1=0.70),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.10, y0=0.16, x1=0.74, y1=0.88),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.78, y0=0.28, x1=0.96, y1=0.46),
            ],
            "metrics": {
                "series": [{"label": "24-month horizon", "x": [0.05, 0.20, 0.40], "y": [0.16, 0.12]}],
                "reference_line": {"x": [0.05, 0.45], "y": [0.0, 0.0]},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "series_length_mismatch" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_decision_curve_treated_fraction_panel_is_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_decision_curve",
        layout_sidecar={
            "template_id": "time_to_event_decision_curve",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.60, y1=0.08),
                make_box("panel_a_x_axis_title", "x_axis_title", x0=0.18, y0=0.88, x1=0.36, y1=0.92),
                make_box("panel_a_y_axis_title", "y_axis_title", x0=0.01, y0=0.24, x1=0.06, y1=0.70),
            ],
            "panel_boxes": [
                make_box("panel_a", "panel", x0=0.10, y0=0.16, x1=0.46, y1=0.82),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.72, y0=0.10, x1=0.94, y1=0.16),
            ],
            "metrics": {
                "series": [{"label": "Model", "x": [0.5, 1.0, 2.0], "y": [0.03, 0.02, 0.01]}],
                "reference_line": {"x": [0.5, 2.0], "y": [0.0, 0.0]},
                "treated_fraction_series": {"label": "Model", "x": [0.5, 1.0, 2.0], "y": [40.0, 20.0, 5.0]},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "treated_fraction_panel_missing" for issue in result["issues"])


def test_run_display_layout_qc_requires_structured_time_horizon_for_time_dependent_roc() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_dependent_roc_horizon",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.30, y0=0.92, x1=0.62, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.24, x1=0.06, y1=0.70),
            ],
            "panel_boxes": [
                make_box("panel", "panel", x0=0.10, y0=0.16, x1=0.74, y1=0.88),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.78, y0=0.28, x1=0.96, y1=0.46),
            ],
            "metrics": {
                "title": "Time-dependent ROC at 24 months",
                "caption": "Horizon-specific discrimination of the locked survival model at 24 months.",
                "series": [{"label": "24-month horizon", "x": [0.0, 0.25, 1.0], "y": [0.0, 0.80, 1.0]}],
                "reference_line": {"label": "Chance", "x": [0.0, 1.0], "y": [0.0, 1.0]},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "time_horizon_months_missing" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_time_dependent_roc_comparison_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_dependent_roc_comparison_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.02, x1=0.82, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.36, y0=0.93, x1=0.64, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.22, x1=0.05, y1=0.74),
                make_box("panel_title_A", "panel_title", x0=0.14, y0=0.10, x1=0.34, y1=0.14),
                make_box("panel_title_B", "panel_title", x0=0.56, y0=0.10, x1=0.80, y1=0.14),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.79, x1=0.14, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.53, y0=0.79, x1=0.56, y1=0.84),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.22, x1=0.43, y1=0.86),
                make_box("panel_B", "panel", x0=0.52, y0=0.22, x1=0.85, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.28, y0=0.03, x1=0.67, y1=0.12),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "overall_followup",
                        "panel_label": "A",
                        "title": "Overall follow-up",
                        "analysis_window_label": "Overall follow-up",
                        "series": [
                            {"label": "Locked model", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.74, 0.88, 1.0]},
                            {"label": "Clinical baseline", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.67, 0.82, 1.0]},
                        ],
                        "reference_line": {"label": "Chance", "x": [0.0, 1.0], "y": [0.0, 1.0]},
                    },
                    {
                        "panel_id": "first_15_years",
                        "panel_label": "B",
                        "title": "First 15 years of follow-up",
                        "analysis_window_label": "First 15 years of follow-up",
                        "time_horizon_months": 180,
                        "series": [
                            {"label": "Locked model", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.78, 0.90, 1.0]},
                            {"label": "Clinical baseline", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.70, 0.84, 1.0]},
                        ],
                        "reference_line": {"label": "Chance", "x": [0.0, 1.0], "y": [0.0, 1.0]},
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result


def test_run_display_layout_qc_uses_sanitized_panel_label_tokens_for_time_dependent_roc_comparison_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_dependent_roc_comparison_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.02, x1=0.82, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.36, y0=0.93, x1=0.64, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.22, x1=0.05, y1=0.74),
                make_box("panel_title_A_1", "panel_title", x0=0.14, y0=0.10, x1=0.34, y1=0.14),
                make_box("panel_title_B_2", "panel_title", x0=0.56, y0=0.10, x1=0.80, y1=0.14),
                make_box("panel_label_A_1", "panel_label", x0=0.11, y0=0.79, x1=0.14, y1=0.84),
                make_box("panel_label_B_2", "panel_label", x0=0.53, y0=0.79, x1=0.56, y1=0.84),
            ],
            "panel_boxes": [
                make_box("panel_A_1", "panel", x0=0.10, y0=0.22, x1=0.43, y1=0.86),
                make_box("panel_B_2", "panel", x0=0.52, y0=0.22, x1=0.85, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.28, y0=0.03, x1=0.67, y1=0.12),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "overall_followup",
                        "panel_label": "A-1",
                        "title": "Overall follow-up",
                        "analysis_window_label": "Overall follow-up",
                        "series": [
                            {"label": "Locked model", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.74, 0.88, 1.0]},
                            {"label": "Clinical baseline", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.67, 0.82, 1.0]},
                        ],
                    },
                    {
                        "panel_id": "first_15_years",
                        "panel_label": "B 2",
                        "title": "First 15 years of follow-up",
                        "analysis_window_label": "First 15 years of follow-up",
                        "time_horizon_months": 180,
                        "series": [
                            {"label": "Locked model", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.78, 0.90, 1.0]},
                            {"label": "Clinical baseline", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.70, 0.84, 1.0]},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result


def test_run_display_layout_qc_uses_sanitized_panel_label_tokens_for_stratified_cumulative_incidence_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "time_to_event_stratified_cumulative_incidence_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.02, x1=0.82, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.34, y0=0.94, x1=0.66, y1=0.98),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.22, x1=0.05, y1=0.74),
                make_box("panel_title_A_1", "panel_title", x0=0.12, y0=0.10, x1=0.28, y1=0.14),
                make_box("panel_title_B_2", "panel_title", x0=0.41, y0=0.10, x1=0.57, y1=0.14),
                make_box("panel_title_C_3", "panel_title", x0=0.70, y0=0.10, x1=0.86, y1=0.14),
                make_box("panel_label_A_1", "panel_label", x0=0.09, y0=0.79, x1=0.12, y1=0.84),
                make_box("panel_label_B_2", "panel_label", x0=0.38, y0=0.79, x1=0.41, y1=0.84),
                make_box("panel_label_C_3", "panel_label", x0=0.67, y0=0.79, x1=0.70, y1=0.84),
            ],
            "panel_boxes": [
                make_box("panel_A_1", "panel", x0=0.08, y0=0.22, x1=0.31, y1=0.86),
                make_box("panel_B_2", "panel", x0=0.37, y0=0.22, x1=0.60, y1=0.86),
                make_box("panel_C_3", "panel", x0=0.66, y0=0.22, x1=0.89, y1=0.86),
            ],
            "guide_boxes": [],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "baseline_htn",
                        "panel_label": "A-1",
                        "title": "Baseline hypertension status",
                        "groups": [
                            {"label": "HTN-AI+", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.08, 0.18]},
                            {"label": "HTN-AI−", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.03, 0.08]},
                        ],
                    },
                    {
                        "panel_id": "age_band",
                        "panel_label": "B 2",
                        "title": "Age band",
                        "groups": [
                            {"label": "Older", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.10, 0.22]},
                            {"label": "Younger", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.02, 0.06]},
                        ],
                    },
                    {
                        "panel_id": "htn_ai_quintile",
                        "panel_label": "C/3",
                        "title": "HTN-AI quintile",
                        "groups": [
                            {"label": "Q1", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.01, 0.04]},
                            {"label": "Q5", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.10, 0.24]},
                        ],
                    },
                ],
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "pass", result


def test_run_display_layout_qc_fails_when_time_dependent_roc_comparison_panel_horizon_is_invalid() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_evidence_curve",
        layout_sidecar={
            "template_id": "time_dependent_roc_comparison_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.02, x1=0.82, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.36, y0=0.93, x1=0.64, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.22, x1=0.05, y1=0.74),
                make_box("panel_title_A", "panel_title", x0=0.14, y0=0.10, x1=0.34, y1=0.14),
                make_box("panel_title_B", "panel_title", x0=0.56, y0=0.10, x1=0.80, y1=0.14),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.79, x1=0.14, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.53, y0=0.79, x1=0.56, y1=0.84),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.22, x1=0.43, y1=0.86),
                make_box("panel_B", "panel", x0=0.52, y0=0.22, x1=0.85, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.28, y0=0.03, x1=0.67, y1=0.12),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "overall_followup",
                        "panel_label": "A",
                        "title": "Overall follow-up",
                        "analysis_window_label": "Overall follow-up",
                        "series": [
                            {"label": "Locked model", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.74, 0.88, 1.0]},
                            {"label": "Clinical baseline", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.67, 0.82, 1.0]},
                        ],
                        "reference_line": {"label": "Chance", "x": [0.0, 1.0], "y": [0.0, 1.0]},
                    },
                    {
                        "panel_id": "first_15_years",
                        "panel_label": "B",
                        "title": "First 15 years of follow-up",
                        "analysis_window_label": "First 15 years of follow-up",
                        "time_horizon_months": 0,
                        "series": [
                            {"label": "Locked model", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.78, 0.90, 1.0]},
                            {"label": "Clinical baseline", "x": [0.0, 0.2, 0.5, 1.0], "y": [0.0, 0.70, 0.84, 1.0]},
                        ],
                        "reference_line": {"label": "Chance", "x": [0.0, 1.0], "y": [0.0, 1.0]},
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "panel_time_horizon_months_invalid" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_risk_group_summary_panel_labels_are_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "time_to_event_risk_group_summary",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "x_axis_title", x0=0.18, y0=0.92, x1=0.34, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.02, y0=0.20, x1=0.06, y1=0.72),
                make_box("panel_right_x_axis_title", "subplot_x_axis_title", x0=0.60, y0=0.92, x1=0.76, y1=0.97),
                make_box("panel_right_y_axis_title", "subplot_y_axis_title", x0=0.50, y0=0.20, x1=0.54, y1=0.72),
                make_box("panel_left_title", "panel_title", x0=0.16, y0=0.11, x1=0.34, y1=0.15),
                make_box("panel_right_title", "panel_title", x0=0.58, y0=0.11, x1=0.80, y1=0.15),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.16, x1=0.44, y1=0.86),
                make_box("panel_right", "panel", x0=0.54, y0=0.16, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [],
            "metrics": {
                "risk_group_summaries": [
                    {
                        "label": "Low risk",
                        "sample_size": 72,
                        "events_5y": 4,
                        "mean_predicted_risk_5y": 0.08,
                        "observed_km_risk_5y": 0.06,
                    },
                    {
                        "label": "High risk",
                        "sample_size": 48,
                        "events_5y": 19,
                        "mean_predicted_risk_5y": 0.31,
                        "observed_km_risk_5y": 0.35,
                    },
                ],
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_panel_label" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_stratified_cumulative_incidence_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "time_to_event_stratified_cumulative_incidence_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.02, x1=0.82, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.34, y0=0.94, x1=0.66, y1=0.98),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.22, x1=0.05, y1=0.74),
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.10, x1=0.28, y1=0.14),
                make_box("panel_title_B", "panel_title", x0=0.41, y0=0.10, x1=0.57, y1=0.14),
                make_box("panel_title_C", "panel_title", x0=0.70, y0=0.10, x1=0.86, y1=0.14),
                make_box("panel_label_A", "panel_label", x0=0.09, y0=0.79, x1=0.12, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.79, x1=0.41, y1=0.84),
                make_box("panel_label_C", "panel_label", x0=0.67, y0=0.79, x1=0.70, y1=0.84),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.08, y0=0.22, x1=0.31, y1=0.86),
                make_box("panel_B", "panel", x0=0.37, y0=0.22, x1=0.60, y1=0.86),
                make_box("panel_C", "panel", x0=0.66, y0=0.22, x1=0.89, y1=0.86),
            ],
            "guide_boxes": [],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "baseline_htn",
                        "panel_label": "A",
                        "title": "Baseline hypertension status",
                        "groups": [
                            {"label": "HTN-AI+", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.08, 0.18]},
                            {"label": "HTN-AI−", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.03, 0.08]},
                        ],
                    },
                    {
                        "panel_id": "age_band",
                        "panel_label": "B",
                        "title": "Age band",
                        "groups": [
                            {"label": "Older", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.10, 0.22]},
                            {"label": "Younger", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.02, 0.06]},
                        ],
                    },
                    {
                        "panel_id": "htn_ai_quintile",
                        "panel_label": "C",
                        "title": "HTN-AI quintile",
                        "groups": [
                            {"label": "Q1", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.01, 0.04]},
                            {"label": "Q5", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.10, 0.24]},
                        ],
                    },
                ],
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "pass", result

def test_run_display_layout_qc_fails_when_stratified_cumulative_incidence_panel_labels_are_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_survival_curve",
        layout_sidecar={
            "template_id": "time_to_event_stratified_cumulative_incidence_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.18, y0=0.02, x1=0.82, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.34, y0=0.94, x1=0.66, y1=0.98),
                make_box("y_axis_title", "y_axis_title", x0=0.01, y0=0.22, x1=0.05, y1=0.74),
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.10, x1=0.28, y1=0.14),
                make_box("panel_title_B", "panel_title", x0=0.41, y0=0.10, x1=0.57, y1=0.14),
                make_box("panel_title_C", "panel_title", x0=0.70, y0=0.10, x1=0.86, y1=0.14),
                make_box("panel_label_A", "panel_label", x0=0.09, y0=0.79, x1=0.12, y1=0.84),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.79, x1=0.41, y1=0.84),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.08, y0=0.22, x1=0.31, y1=0.86),
                make_box("panel_B", "panel", x0=0.37, y0=0.22, x1=0.60, y1=0.86),
                make_box("panel_C", "panel", x0=0.66, y0=0.22, x1=0.89, y1=0.86),
            ],
            "guide_boxes": [],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "baseline_htn",
                        "panel_label": "A",
                        "title": "Baseline hypertension status",
                        "groups": [
                            {"label": "HTN-AI+", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.08, 0.18]},
                            {"label": "HTN-AI−", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.03, 0.08]},
                        ],
                    },
                    {
                        "panel_id": "age_band",
                        "panel_label": "B",
                        "title": "Age band",
                        "groups": [
                            {"label": "Older", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.10, 0.22]},
                            {"label": "Younger", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.02, 0.06]},
                        ],
                    },
                    {
                        "panel_id": "htn_ai_quintile",
                        "panel_label": "C",
                        "title": "HTN-AI quintile",
                        "groups": [
                            {"label": "Q1", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.01, 0.04]},
                            {"label": "Q5", "times": [0.0, 1.0, 2.0], "values": [0.0, 0.10, 0.24]},
                        ],
                    },
                ],
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_panel_label" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_decision_curve_panel_label_anchor_drifts() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_decision_curve",
        layout_sidecar={
            "template_id": "time_to_event_decision_curve",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.10, y0=0.02, x1=0.60, y1=0.08),
                make_box("x_axis_title", "x_axis_title", x0=0.16, y0=0.92, x1=0.34, y1=0.97),
                make_box("y_axis_title", "y_axis_title", x0=0.02, y0=0.20, x1=0.06, y1=0.72),
                make_box("panel_right_x_axis_title", "subplot_x_axis_title", x0=0.62, y0=0.92, x1=0.80, y1=0.97),
                make_box("panel_right_y_axis_title", "subplot_y_axis_title", x0=0.54, y0=0.20, x1=0.58, y1=0.72),
                make_box("panel_left_title", "panel_title", x0=0.18, y0=0.11, x1=0.34, y1=0.15),
                make_box("panel_right_title", "panel_title", x0=0.62, y0=0.11, x1=0.80, y1=0.15),
                make_box("panel_label_A", "panel_label", x0=0.11, y0=0.80, x1=0.14, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.74, y0=0.64, x1=0.77, y1=0.69),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.16, x1=0.44, y1=0.86),
                make_box("panel_right", "panel", x0=0.56, y0=0.16, x1=0.90, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.34, y0=0.02, x1=0.66, y1=0.08),
            ],
            "metrics": {
                "series": [{"label": "Model", "x": [0.5, 1.0, 2.0], "y": [0.03, 0.02, 0.01]}],
                "reference_line": {"x": [0.5, 2.0], "y": [0.0, 0.0]},
                "treated_fraction_series": {"label": "Model", "x": [0.5, 1.0, 2.0], "y": [40.0, 20.0, 5.0]},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "panel_label_anchor_drift" for issue in result["issues"])


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


def test_run_display_layout_qc_fails_when_performance_heatmap_value_is_out_of_range() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_heatmap",
        layout_sidecar={
            "template_id": "performance_heatmap",
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
                "metric_name": "AUC",
                "matrix_cells": [
                    {"x": "All participants", "y": "Clinical baseline", "value": 0.72},
                    {"x": "All participants", "y": "Integrated model", "value": 1.04},
                    {"x": "APOE4 carriers", "y": "Clinical baseline", "value": 0.68},
                    {"x": "APOE4 carriers", "y": "Integrated model", "value": 0.81},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "performance_value_out_of_range" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_pathway_enrichment_dotplot_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_pathway_enrichment_dotplot_panel",
        layout_sidecar={
            "template_id": "pathway_enrichment_dotplot_panel",
            "device": make_device(),
                "layout_boxes": [
                    make_box("panel_title_A", "panel_title", x0=0.10, y0=0.86, x1=0.28, y1=0.89),
                    make_box("panel_title_B", "panel_title", x0=0.52, y0=0.86, x1=0.68, y1=0.89),
                    make_box("panel_label_A", "panel_label", x0=0.10, y0=0.76, x1=0.12, y1=0.79),
                    make_box("panel_label_B", "panel_label", x0=0.52, y0=0.76, x1=0.54, y1=0.79),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.14, y0=0.10, x1=0.30, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.56, y0=0.10, x1=0.72, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.36, x1=0.06, y1=0.66),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.80),
                make_box("panel_B", "panel", x0=0.52, y0=0.18, x1=0.84, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.26, y0=0.02, x1=0.56, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.88, y0=0.20, x1=0.92, y1=0.76),
            ],
            "metrics": {
                "effect_scale_label": "Directionality score",
                "size_scale_label": "Gene count",
                "pathway_labels": ["IFN response", "EMT signaling", "Cell cycle"],
                "panels": [
                    {
                        "panel_id": "transcriptome",
                        "panel_title": "Transcriptome",
                        "panel_label": "A",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "points": [
                            {"pathway_label": "IFN response", "x": 0.28, "y": 0.68, "size_value": 34.0, "effect_value": 0.91},
                            {"pathway_label": "EMT signaling", "x": 0.22, "y": 0.50, "size_value": 22.0, "effect_value": 0.42},
                            {"pathway_label": "Cell cycle", "x": 0.31, "y": 0.32, "size_value": 29.0, "effect_value": 0.76},
                        ],
                    },
                    {
                        "panel_id": "proteome",
                        "panel_title": "Proteome",
                        "panel_label": "B",
                        "panel_box_id": "panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "panel_title_box_id": "panel_title_B",
                        "x_axis_title_box_id": "x_axis_title_B",
                        "points": [
                            {"pathway_label": "IFN response", "x": 0.64, "y": 0.68, "size_value": 26.0, "effect_value": 0.64},
                            {"pathway_label": "EMT signaling", "x": 0.72, "y": 0.50, "size_value": 31.0, "effect_value": 0.88},
                            {"pathway_label": "Cell cycle", "x": 0.61, "y": 0.32, "size_value": 19.0, "effect_value": 0.37},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_pathway_enrichment_dotplot_scale_label_is_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_pathway_enrichment_dotplot_panel",
        layout_sidecar={
            "template_id": "pathway_enrichment_dotplot_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.86, x1=0.28, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.80, x1=0.12, y1=0.83),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.14, y0=0.10, x1=0.30, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.36, x1=0.06, y1=0.66),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.26, y0=0.02, x1=0.56, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.88, y0=0.20, x1=0.92, y1=0.76),
            ],
            "metrics": {
                "effect_scale_label": "Directionality score",
                "size_scale_label": "",
                "pathway_labels": ["IFN response", "EMT signaling"],
                "panels": [
                    {
                        "panel_id": "transcriptome",
                        "panel_title": "Transcriptome",
                        "panel_label": "A",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "points": [
                            {"pathway_label": "IFN response", "x": 0.28, "y": 0.62, "size_value": 34.0, "effect_value": 0.91},
                            {"pathway_label": "EMT signaling", "x": 0.22, "y": 0.38, "size_value": 22.0, "effect_value": 0.42},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "size_scale_label_missing" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_omics_volcano_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_omics_volcano_panel",
        layout_sidecar={
            "template_id": "omics_volcano_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.86, x1=0.30, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.52, y0=0.86, x1=0.70, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.76, x1=0.12, y1=0.79),
                make_box("panel_label_B", "panel_label", x0=0.52, y0=0.76, x1=0.54, y1=0.79),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.18, y0=0.10, x1=0.30, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.60, y0=0.10, x1=0.72, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.36, x1=0.06, y1=0.66),
                make_box("label_A_0", "annotation_label", x0=0.31, y0=0.63, x1=0.39, y1=0.67),
                make_box("label_B_0", "annotation_label", x0=0.73, y0=0.59, x1=0.81, y1=0.63),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.80),
                make_box("panel_B", "panel", x0=0.52, y0=0.18, x1=0.84, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.26, y0=0.02, x1=0.56, y1=0.08),
                make_box("panel_A_threshold_left", "reference_line", x0=0.17, y0=0.18, x1=0.171, y1=0.80),
                make_box("panel_A_threshold_right", "reference_line", x0=0.35, y0=0.18, x1=0.351, y1=0.80),
                make_box("panel_A_significance_threshold", "reference_line", x0=0.10, y0=0.50, x1=0.42, y1=0.501),
                make_box("panel_B_threshold_left", "reference_line", x0=0.59, y0=0.18, x1=0.591, y1=0.80),
                make_box("panel_B_threshold_right", "reference_line", x0=0.77, y0=0.18, x1=0.771, y1=0.80),
                make_box("panel_B_significance_threshold", "reference_line", x0=0.52, y0=0.50, x1=0.84, y1=0.501),
            ],
            "metrics": {
                "legend_title": "Regulation",
                "effect_threshold": 1.0,
                "significance_threshold": 2.0,
                "panels": [
                    {
                        "panel_id": "transcriptome",
                        "panel_title": "Transcriptome",
                        "panel_label": "A",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "effect_threshold_left_box_id": "panel_A_threshold_left",
                        "effect_threshold_right_box_id": "panel_A_threshold_right",
                        "significance_threshold_box_id": "panel_A_significance_threshold",
                        "points": [
                            {
                                "feature_label": "CXCL9",
                                "x": 0.33,
                                "y": 0.65,
                                "effect_value": 1.72,
                                "significance_value": 4.41,
                                "regulation_class": "upregulated",
                                "label_text": "CXCL9",
                                "label_box_id": "label_A_0",
                            },
                            {
                                "feature_label": "MKI67",
                                "x": 0.31,
                                "y": 0.57,
                                "effect_value": 1.19,
                                "significance_value": 3.28,
                                "regulation_class": "upregulated",
                            },
                            {
                                "feature_label": "COL1A1",
                                "x": 0.21,
                                "y": 0.61,
                                "effect_value": -1.34,
                                "significance_value": 3.92,
                                "regulation_class": "downregulated",
                            },
                            {
                                "feature_label": "GAPDH",
                                "x": 0.27,
                                "y": 0.29,
                                "effect_value": 0.14,
                                "significance_value": 0.52,
                                "regulation_class": "background",
                            },
                        ],
                    },
                    {
                        "panel_id": "proteome",
                        "panel_title": "Proteome",
                        "panel_label": "B",
                        "panel_box_id": "panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "panel_title_box_id": "panel_title_B",
                        "x_axis_title_box_id": "x_axis_title_B",
                        "effect_threshold_left_box_id": "panel_B_threshold_left",
                        "effect_threshold_right_box_id": "panel_B_threshold_right",
                        "significance_threshold_box_id": "panel_B_significance_threshold",
                        "points": [
                            {
                                "feature_label": "CXCL9",
                                "x": 0.75,
                                "y": 0.61,
                                "effect_value": 1.26,
                                "significance_value": 3.36,
                                "regulation_class": "upregulated",
                                "label_text": "CXCL9",
                                "label_box_id": "label_B_0",
                            },
                            {
                                "feature_label": "STAT1",
                                "x": 0.73,
                                "y": 0.56,
                                "effect_value": 1.08,
                                "significance_value": 2.91,
                                "regulation_class": "upregulated",
                            },
                            {
                                "feature_label": "COL1A1",
                                "x": 0.61,
                                "y": 0.57,
                                "effect_value": -1.11,
                                "significance_value": 3.07,
                                "regulation_class": "downregulated",
                            },
                            {
                                "feature_label": "ACTB",
                                "x": 0.68,
                                "y": 0.30,
                                "effect_value": 0.11,
                                "significance_value": 0.61,
                                "regulation_class": "background",
                            },
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_omics_volcano_threshold_box_is_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_omics_volcano_panel",
        layout_sidecar={
            "template_id": "omics_volcano_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.86, x1=0.30, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.76, x1=0.12, y1=0.79),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.18, y0=0.10, x1=0.30, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.36, x1=0.06, y1=0.66),
                make_box("label_A_0", "annotation_label", x0=0.31, y0=0.63, x1=0.39, y1=0.67),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.26, y0=0.02, x1=0.56, y1=0.08),
                make_box("panel_A_threshold_left", "reference_line", x0=0.17, y0=0.18, x1=0.171, y1=0.80),
                make_box("panel_A_significance_threshold", "reference_line", x0=0.10, y0=0.50, x1=0.42, y1=0.501),
            ],
            "metrics": {
                "legend_title": "Regulation",
                "effect_threshold": 1.0,
                "significance_threshold": 2.0,
                "panels": [
                    {
                        "panel_id": "transcriptome",
                        "panel_title": "Transcriptome",
                        "panel_label": "A",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "effect_threshold_left_box_id": "panel_A_threshold_left",
                        "effect_threshold_right_box_id": "panel_A_threshold_right",
                        "significance_threshold_box_id": "panel_A_significance_threshold",
                        "points": [
                            {
                                "feature_label": "CXCL9",
                                "x": 0.33,
                                "y": 0.65,
                                "effect_value": 1.72,
                                "significance_value": 4.41,
                                "regulation_class": "upregulated",
                                "label_text": "CXCL9",
                                "label_box_id": "label_A_0",
                            },
                            {
                                "feature_label": "COL1A1",
                                "x": 0.21,
                                "y": 0.61,
                                "effect_value": -1.34,
                                "significance_value": 3.92,
                                "regulation_class": "downregulated",
                            },
                        ],
                    }
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "effect_threshold_box_missing" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_oncoplot_mutation_landscape_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_oncoplot_mutation_landscape_panel",
        layout_sidecar={
            "template_id": "oncoplot_mutation_landscape_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.91, x1=0.10, y1=0.94),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.26, x1=0.05, y1=0.60),
                make_box("annotation_track_label_cohort", "annotation_track_label", x0=0.08, y0=0.71, x1=0.18, y1=0.74),
                make_box("annotation_track_label_response", "annotation_track_label", x0=0.08, y0=0.65, x1=0.20, y1=0.68),
                make_box("burden_bar_D1", "bar", x0=0.18, y0=0.82, x1=0.22, y1=0.88),
                make_box("burden_bar_D2", "bar", x0=0.23, y0=0.82, x1=0.27, y1=0.86),
                make_box("burden_bar_V1", "bar", x0=0.28, y0=0.82, x1=0.32, y1=0.88),
                make_box("burden_bar_V2", "bar", x0=0.33, y0=0.82, x1=0.37, y1=0.86),
                make_box("freq_bar_TP53", "bar", x0=0.74, y0=0.47, x1=0.82, y1=0.53),
                make_box("freq_bar_KRAS", "bar", x0=0.74, y0=0.38, x1=0.78, y1=0.44),
                make_box("freq_bar_EGFR", "bar", x0=0.74, y0=0.29, x1=0.78, y1=0.35),
                make_box("annotation_cohort_D1", "annotation_cell", x0=0.18, y0=0.70, x1=0.22, y1=0.74),
                make_box("annotation_cohort_D2", "annotation_cell", x0=0.23, y0=0.70, x1=0.27, y1=0.74),
                make_box("annotation_cohort_V1", "annotation_cell", x0=0.28, y0=0.70, x1=0.32, y1=0.74),
                make_box("annotation_cohort_V2", "annotation_cell", x0=0.33, y0=0.70, x1=0.37, y1=0.74),
                make_box("annotation_response_D1", "annotation_cell", x0=0.18, y0=0.64, x1=0.22, y1=0.68),
                make_box("annotation_response_D2", "annotation_cell", x0=0.23, y0=0.64, x1=0.27, y1=0.68),
                make_box("annotation_response_V1", "annotation_cell", x0=0.28, y0=0.64, x1=0.32, y1=0.68),
                make_box("annotation_response_V2", "annotation_cell", x0=0.33, y0=0.64, x1=0.37, y1=0.68),
                make_box("mutation_TP53_D1", "mutation_cell", x0=0.18, y0=0.47, x1=0.22, y1=0.53),
                make_box("mutation_KRAS_D2", "mutation_cell", x0=0.23, y0=0.38, x1=0.27, y1=0.44),
                make_box("mutation_TP53_V1", "mutation_cell", x0=0.28, y0=0.47, x1=0.32, y1=0.53),
                make_box("mutation_EGFR_V2", "mutation_cell", x0=0.33, y0=0.29, x1=0.37, y1=0.35),
            ],
            "panel_boxes": [
                make_box("panel_burden", "panel", x0=0.18, y0=0.80, x1=0.37, y1=0.89),
                make_box("panel_annotations", "panel", x0=0.18, y0=0.62, x1=0.37, y1=0.75),
                make_box("panel_matrix", "panel", x0=0.18, y0=0.26, x1=0.37, y1=0.56),
                make_box("panel_frequency", "panel", x0=0.74, y0=0.26, x1=0.84, y1=0.56),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.44, y0=0.02, x1=0.82, y1=0.10),
            ],
            "metrics": {
                "mutation_legend_title": "Alteration",
                "sample_ids": ["D1", "D2", "V1", "V2"],
                "gene_labels": ["TP53", "KRAS", "EGFR"],
                "annotation_tracks": [
                    {
                        "track_id": "cohort",
                        "track_label": "Cohort",
                        "track_label_box_id": "annotation_track_label_cohort",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Discovery", "box_id": "annotation_cohort_D1"},
                            {"sample_id": "D2", "category_label": "Discovery", "box_id": "annotation_cohort_D2"},
                            {"sample_id": "V1", "category_label": "Validation", "box_id": "annotation_cohort_V1"},
                            {"sample_id": "V2", "category_label": "Validation", "box_id": "annotation_cohort_V2"},
                        ],
                    },
                    {
                        "track_id": "response",
                        "track_label": "Response",
                        "track_label_box_id": "annotation_track_label_response",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Responder", "box_id": "annotation_response_D1"},
                            {"sample_id": "D2", "category_label": "Non-responder", "box_id": "annotation_response_D2"},
                            {"sample_id": "V1", "category_label": "Responder", "box_id": "annotation_response_V1"},
                            {"sample_id": "V2", "category_label": "Non-responder", "box_id": "annotation_response_V2"},
                        ],
                    },
                ],
                "sample_burdens": [
                    {"sample_id": "D1", "altered_gene_count": 1, "bar_box_id": "burden_bar_D1"},
                    {"sample_id": "D2", "altered_gene_count": 1, "bar_box_id": "burden_bar_D2"},
                    {"sample_id": "V1", "altered_gene_count": 1, "bar_box_id": "burden_bar_V1"},
                    {"sample_id": "V2", "altered_gene_count": 1, "bar_box_id": "burden_bar_V2"},
                ],
                "gene_altered_frequencies": [
                    {"gene_label": "TP53", "altered_fraction": 0.5, "bar_box_id": "freq_bar_TP53"},
                    {"gene_label": "KRAS", "altered_fraction": 0.25, "bar_box_id": "freq_bar_KRAS"},
                    {"gene_label": "EGFR", "altered_fraction": 0.25, "bar_box_id": "freq_bar_EGFR"},
                ],
                "altered_cells": [
                    {"sample_id": "D1", "gene_label": "TP53", "alteration_class": "missense", "box_id": "mutation_TP53_D1"},
                    {"sample_id": "D2", "gene_label": "KRAS", "alteration_class": "amplification", "box_id": "mutation_KRAS_D2"},
                    {"sample_id": "V1", "gene_label": "TP53", "alteration_class": "truncating", "box_id": "mutation_TP53_V1"},
                    {"sample_id": "V2", "gene_label": "EGFR", "alteration_class": "fusion", "box_id": "mutation_EGFR_V2"},
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_passes_for_cnv_recurrence_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_cnv_recurrence_summary_panel",
        layout_sidecar={
            "template_id": "cnv_recurrence_summary_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.91, x1=0.10, y1=0.94),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.26, x1=0.05, y1=0.60),
                make_box("annotation_track_label_cohort", "annotation_track_label", x0=0.08, y0=0.71, x1=0.18, y1=0.74),
                make_box("annotation_track_label_response", "annotation_track_label", x0=0.08, y0=0.65, x1=0.20, y1=0.68),
                make_box("burden_bar_D1", "bar", x0=0.18, y0=0.82, x1=0.22, y1=0.88),
                make_box("burden_bar_D2", "bar", x0=0.23, y0=0.82, x1=0.27, y1=0.88),
                make_box("burden_bar_V1", "bar", x0=0.28, y0=0.82, x1=0.32, y1=0.88),
                make_box("burden_bar_V2", "bar", x0=0.33, y0=0.82, x1=0.37, y1=0.88),
                make_box("freq_gain_TP53", "bar", x0=0.74, y0=0.50, x1=0.80, y1=0.55),
                make_box("freq_loss_TP53", "bar", x0=0.68, y0=0.50, x1=0.74, y1=0.55),
                make_box("freq_gain_MYC", "bar", x0=0.74, y0=0.42, x1=0.80, y1=0.47),
                make_box("freq_loss_MYC", "bar", x0=0.68, y0=0.42, x1=0.74, y1=0.47),
                make_box("freq_gain_EGFR", "bar", x0=0.74, y0=0.34, x1=0.80, y1=0.39),
                make_box("freq_loss_EGFR", "bar", x0=0.68, y0=0.34, x1=0.74, y1=0.39),
                make_box("freq_gain_CDKN2A", "bar", x0=0.74, y0=0.26, x1=0.80, y1=0.31),
                make_box("freq_loss_CDKN2A", "bar", x0=0.68, y0=0.26, x1=0.74, y1=0.31),
                make_box("annotation_cohort_D1", "annotation_cell", x0=0.18, y0=0.70, x1=0.22, y1=0.74),
                make_box("annotation_cohort_D2", "annotation_cell", x0=0.23, y0=0.70, x1=0.27, y1=0.74),
                make_box("annotation_cohort_V1", "annotation_cell", x0=0.28, y0=0.70, x1=0.32, y1=0.74),
                make_box("annotation_cohort_V2", "annotation_cell", x0=0.33, y0=0.70, x1=0.37, y1=0.74),
                make_box("annotation_response_D1", "annotation_cell", x0=0.18, y0=0.64, x1=0.22, y1=0.68),
                make_box("annotation_response_D2", "annotation_cell", x0=0.23, y0=0.64, x1=0.27, y1=0.68),
                make_box("annotation_response_V1", "annotation_cell", x0=0.28, y0=0.64, x1=0.32, y1=0.68),
                make_box("annotation_response_V2", "annotation_cell", x0=0.33, y0=0.64, x1=0.37, y1=0.68),
                make_box("cnv_TP53_D1", "cnv_cell", x0=0.18, y0=0.50, x1=0.22, y1=0.55),
                make_box("cnv_TP53_D2", "cnv_cell", x0=0.23, y0=0.50, x1=0.27, y1=0.55),
                make_box("cnv_MYC_D1", "cnv_cell", x0=0.18, y0=0.42, x1=0.22, y1=0.47),
                make_box("cnv_MYC_V1", "cnv_cell", x0=0.28, y0=0.42, x1=0.32, y1=0.47),
                make_box("cnv_EGFR_D2", "cnv_cell", x0=0.23, y0=0.34, x1=0.27, y1=0.39),
                make_box("cnv_EGFR_V2", "cnv_cell", x0=0.33, y0=0.34, x1=0.37, y1=0.39),
                make_box("cnv_CDKN2A_V1", "cnv_cell", x0=0.28, y0=0.26, x1=0.32, y1=0.31),
                make_box("cnv_CDKN2A_V2", "cnv_cell", x0=0.33, y0=0.26, x1=0.37, y1=0.31),
            ],
            "panel_boxes": [
                make_box("panel_burden", "panel", x0=0.18, y0=0.80, x1=0.37, y1=0.89),
                make_box("panel_annotations", "panel", x0=0.18, y0=0.62, x1=0.37, y1=0.75),
                make_box("panel_matrix", "panel", x0=0.18, y0=0.24, x1=0.37, y1=0.58),
                make_box("panel_frequency", "panel", x0=0.68, y0=0.24, x1=0.82, y1=0.58),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.42, y0=0.02, x1=0.86, y1=0.10),
            ],
            "metrics": {
                "cnv_legend_title": "CNV state",
                "sample_ids": ["D1", "D2", "V1", "V2"],
                "region_labels": ["TP53", "MYC", "EGFR", "CDKN2A"],
                "annotation_tracks": [
                    {
                        "track_id": "cohort",
                        "track_label": "Cohort",
                        "track_label_box_id": "annotation_track_label_cohort",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Discovery", "box_id": "annotation_cohort_D1"},
                            {"sample_id": "D2", "category_label": "Discovery", "box_id": "annotation_cohort_D2"},
                            {"sample_id": "V1", "category_label": "Validation", "box_id": "annotation_cohort_V1"},
                            {"sample_id": "V2", "category_label": "Validation", "box_id": "annotation_cohort_V2"},
                        ],
                    },
                    {
                        "track_id": "response",
                        "track_label": "Response",
                        "track_label_box_id": "annotation_track_label_response",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Responder", "box_id": "annotation_response_D1"},
                            {"sample_id": "D2", "category_label": "Non-responder", "box_id": "annotation_response_D2"},
                            {"sample_id": "V1", "category_label": "Responder", "box_id": "annotation_response_V1"},
                            {"sample_id": "V2", "category_label": "Non-responder", "box_id": "annotation_response_V2"},
                        ],
                    },
                ],
                "sample_burdens": [
                    {"sample_id": "D1", "altered_region_count": 2, "bar_box_id": "burden_bar_D1"},
                    {"sample_id": "D2", "altered_region_count": 2, "bar_box_id": "burden_bar_D2"},
                    {"sample_id": "V1", "altered_region_count": 2, "bar_box_id": "burden_bar_V1"},
                    {"sample_id": "V2", "altered_region_count": 2, "bar_box_id": "burden_bar_V2"},
                ],
                "region_gain_loss_frequencies": [
                    {
                        "region_label": "TP53",
                        "gain_fraction": 0.25,
                        "loss_fraction": 0.25,
                        "gain_bar_box_id": "freq_gain_TP53",
                        "loss_bar_box_id": "freq_loss_TP53",
                    },
                    {
                        "region_label": "MYC",
                        "gain_fraction": 0.25,
                        "loss_fraction": 0.25,
                        "gain_bar_box_id": "freq_gain_MYC",
                        "loss_bar_box_id": "freq_loss_MYC",
                    },
                    {
                        "region_label": "EGFR",
                        "gain_fraction": 0.25,
                        "loss_fraction": 0.25,
                        "gain_bar_box_id": "freq_gain_EGFR",
                        "loss_bar_box_id": "freq_loss_EGFR",
                    },
                    {
                        "region_label": "CDKN2A",
                        "gain_fraction": 0.25,
                        "loss_fraction": 0.25,
                        "gain_bar_box_id": "freq_gain_CDKN2A",
                        "loss_bar_box_id": "freq_loss_CDKN2A",
                    },
                ],
                "cnv_cells": [
                    {"sample_id": "D1", "region_label": "TP53", "cnv_state": "amplification", "box_id": "cnv_TP53_D1"},
                    {"sample_id": "D2", "region_label": "TP53", "cnv_state": "loss", "box_id": "cnv_TP53_D2"},
                    {"sample_id": "D1", "region_label": "MYC", "cnv_state": "gain", "box_id": "cnv_MYC_D1"},
                    {"sample_id": "V1", "region_label": "MYC", "cnv_state": "loss", "box_id": "cnv_MYC_V1"},
                    {"sample_id": "D2", "region_label": "EGFR", "cnv_state": "gain", "box_id": "cnv_EGFR_D2"},
                    {"sample_id": "V2", "region_label": "EGFR", "cnv_state": "loss", "box_id": "cnv_EGFR_V2"},
                    {"sample_id": "V1", "region_label": "CDKN2A", "cnv_state": "deep_loss", "box_id": "cnv_CDKN2A_V1"},
                    {"sample_id": "V2", "region_label": "CDKN2A", "cnv_state": "gain", "box_id": "cnv_CDKN2A_V2"},
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_oncoplot_annotation_track_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_oncoplot_mutation_landscape_panel",
        layout_sidecar={
            "template_id": "oncoplot_mutation_landscape_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.91, x1=0.10, y1=0.94),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.26, x1=0.05, y1=0.60),
                make_box("annotation_track_label_cohort", "annotation_track_label", x0=0.08, y0=0.71, x1=0.18, y1=0.74),
                make_box("burden_bar_D1", "bar", x0=0.18, y0=0.82, x1=0.22, y1=0.88),
                make_box("burden_bar_D2", "bar", x0=0.23, y0=0.82, x1=0.27, y1=0.86),
                make_box("burden_bar_V1", "bar", x0=0.28, y0=0.82, x1=0.32, y1=0.88),
                make_box("burden_bar_V2", "bar", x0=0.33, y0=0.82, x1=0.37, y1=0.86),
                make_box("freq_bar_TP53", "bar", x0=0.74, y0=0.47, x1=0.82, y1=0.53),
                make_box("freq_bar_KRAS", "bar", x0=0.74, y0=0.38, x1=0.78, y1=0.44),
                make_box("freq_bar_EGFR", "bar", x0=0.74, y0=0.29, x1=0.78, y1=0.35),
                make_box("annotation_cohort_D1", "annotation_cell", x0=0.18, y0=0.70, x1=0.22, y1=0.74),
                make_box("annotation_cohort_D2", "annotation_cell", x0=0.23, y0=0.70, x1=0.27, y1=0.74),
                make_box("annotation_cohort_V1", "annotation_cell", x0=0.28, y0=0.70, x1=0.32, y1=0.74),
                make_box("mutation_TP53_D1", "mutation_cell", x0=0.18, y0=0.47, x1=0.22, y1=0.53),
                make_box("mutation_KRAS_D2", "mutation_cell", x0=0.23, y0=0.38, x1=0.27, y1=0.44),
                make_box("mutation_TP53_V1", "mutation_cell", x0=0.28, y0=0.47, x1=0.32, y1=0.53),
                make_box("mutation_EGFR_V2", "mutation_cell", x0=0.33, y0=0.29, x1=0.37, y1=0.35),
            ],
            "panel_boxes": [
                make_box("panel_burden", "panel", x0=0.18, y0=0.80, x1=0.37, y1=0.89),
                make_box("panel_annotations", "panel", x0=0.18, y0=0.62, x1=0.37, y1=0.75),
                make_box("panel_matrix", "panel", x0=0.18, y0=0.26, x1=0.37, y1=0.56),
                make_box("panel_frequency", "panel", x0=0.74, y0=0.26, x1=0.84, y1=0.56),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.44, y0=0.02, x1=0.82, y1=0.10),
            ],
            "metrics": {
                "mutation_legend_title": "Alteration",
                "sample_ids": ["D1", "D2", "V1", "V2"],
                "gene_labels": ["TP53", "KRAS", "EGFR"],
                "annotation_tracks": [
                    {
                        "track_id": "cohort",
                        "track_label": "Cohort",
                        "track_label_box_id": "annotation_track_label_cohort",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Discovery", "box_id": "annotation_cohort_D1"},
                            {"sample_id": "D2", "category_label": "Discovery", "box_id": "annotation_cohort_D2"},
                            {"sample_id": "V1", "category_label": "Validation", "box_id": "annotation_cohort_V1"},
                        ],
                    },
                ],
                "sample_burdens": [
                    {"sample_id": "D1", "altered_gene_count": 1, "bar_box_id": "burden_bar_D1"},
                    {"sample_id": "D2", "altered_gene_count": 1, "bar_box_id": "burden_bar_D2"},
                    {"sample_id": "V1", "altered_gene_count": 1, "bar_box_id": "burden_bar_V1"},
                    {"sample_id": "V2", "altered_gene_count": 1, "bar_box_id": "burden_bar_V2"},
                ],
                "gene_altered_frequencies": [
                    {"gene_label": "TP53", "altered_fraction": 0.5, "bar_box_id": "freq_bar_TP53"},
                    {"gene_label": "KRAS", "altered_fraction": 0.25, "bar_box_id": "freq_bar_KRAS"},
                    {"gene_label": "EGFR", "altered_fraction": 0.25, "bar_box_id": "freq_bar_EGFR"},
                ],
                "altered_cells": [
                    {"sample_id": "D1", "gene_label": "TP53", "alteration_class": "missense", "box_id": "mutation_TP53_D1"},
                    {"sample_id": "D2", "gene_label": "KRAS", "alteration_class": "amplification", "box_id": "mutation_KRAS_D2"},
                    {"sample_id": "V1", "gene_label": "TP53", "alteration_class": "truncating", "box_id": "mutation_TP53_V1"},
                    {"sample_id": "V2", "gene_label": "EGFR", "alteration_class": "fusion", "box_id": "mutation_EGFR_V2"},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "annotation_track_coverage_mismatch" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_celltype_signature_panel_is_missing_colorbar() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_celltype_signature_panel",
        layout_sidecar={
            "template_id": "celltype_signature_heatmap",
            "device": make_device(),
            "layout_boxes": [
                make_box("embedding_panel_title", "panel_title", x0=0.12, y0=0.12, x1=0.32, y1=0.16),
                make_box("heatmap_panel_title", "panel_title", x0=0.52, y0=0.12, x1=0.82, y1=0.16),
                make_box("embedding_x_axis_title", "subplot_x_axis_title", x0=0.16, y0=0.92, x1=0.30, y1=0.96),
                make_box("embedding_y_axis_title", "subplot_y_axis_title", x0=0.04, y0=0.24, x1=0.07, y1=0.74),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.58, y0=0.92, x1=0.76, y1=0.96),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.46, y0=0.24, x1=0.49, y1=0.74),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.82, x1=0.13, y1=0.86),
                make_box("panel_label_B", "panel_label", x0=0.50, y0=0.82, x1=0.53, y1=0.86),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.86),
                make_box("panel_right", "heatmap_tile_region", x0=0.50, y0=0.18, x1=0.82, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.14, y0=0.02, x1=0.34, y1=0.08),
            ],
            "metrics": {
                "points": [
                    {"x": 0.18, "y": 0.70, "group": "T cells"},
                    {"x": 0.34, "y": 0.30, "group": "Myeloid"},
                ],
                "group_labels": ["T cells", "Myeloid"],
                "matrix_cells": [
                    {"x": "T cells", "y": "IFN response", "value": 0.72},
                    {"x": "Myeloid", "y": "IFN response", "value": -0.18},
                    {"x": "T cells", "y": "TGF-beta", "value": -0.21},
                    {"x": "Myeloid", "y": "TGF-beta", "value": 0.64},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_box" and issue["target"] == "colorbar" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_single_cell_atlas_overview_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_single_cell_atlas_overview_panel",
        layout_sidecar={
            "template_id": "single_cell_atlas_overview_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("embedding_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.24, y1=0.91),
                make_box("embedding_x_axis_title", "subplot_x_axis_title", x0=0.10, y0=0.10, x1=0.22, y1=0.13),
                make_box("embedding_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.30, x1=0.05, y1=0.74),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.58, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.43, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.28, x1=0.36, y1=0.76),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.86, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_embedding", "panel", x0=0.07, y0=0.18, x1=0.29, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.14, "y": 0.70, "state_label": "T cells"},
                    {"x": 0.23, "y": 0.34, "state_label": "Myeloid"},
                ],
                "state_labels": ["T cells", "Myeloid"],
                "row_labels": ["IFN response", "TGF-beta signaling"],
                "composition_groups": [
                    {
                        "group_label": "Tumor",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.62},
                            {"state_label": "Myeloid", "proportion": 0.38},
                        ],
                    },
                    {
                        "group_label": "Adjacent",
                        "group_order": 2,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.41},
                            {"state_label": "Myeloid", "proportion": 0.59},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "T cells", "y": "IFN response", "value": 0.72},
                    {"x": "Myeloid", "y": "IFN response", "value": -0.14},
                    {"x": "T cells", "y": "TGF-beta signaling", "value": -0.21},
                    {"x": "Myeloid", "y": "TGF-beta signaling", "value": 0.67},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_single_cell_atlas_overview_composition_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_single_cell_atlas_overview_panel",
        layout_sidecar={
            "template_id": "single_cell_atlas_overview_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("embedding_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.24, y1=0.91),
                make_box("embedding_x_axis_title", "subplot_x_axis_title", x0=0.10, y0=0.10, x1=0.22, y1=0.13),
                make_box("embedding_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.30, x1=0.05, y1=0.74),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.58, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.43, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.28, x1=0.36, y1=0.76),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.86, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_embedding", "panel", x0=0.07, y0=0.18, x1=0.29, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.14, "y": 0.70, "state_label": "T cells"},
                    {"x": 0.23, "y": 0.34, "state_label": "Myeloid"},
                ],
                "state_labels": ["T cells", "Myeloid"],
                "row_labels": ["IFN response", "TGF-beta signaling"],
                "composition_groups": [
                    {
                        "group_label": "Tumor",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.62},
                        ],
                    },
                    {
                        "group_label": "Adjacent",
                        "group_order": 2,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.41},
                            {"state_label": "Myeloid", "proportion": 0.52},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "T cells", "y": "IFN response", "value": 0.72},
                    {"x": "Myeloid", "y": "IFN response", "value": -0.14},
                    {"x": "T cells", "y": "TGF-beta signaling", "value": -0.21},
                    {"x": "Myeloid", "y": "TGF-beta signaling", "value": 0.67},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "composition_group_state_set_mismatch" for issue in result["issues"])
    assert any(issue["rule_id"] == "composition_group_sum_invalid" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_atlas_spatial_bridge_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_bridge_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_bridge_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("atlas_panel_title", "panel_title", x0=0.20, y0=0.88, x1=0.30, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.22, y0=0.52, x1=0.28, y1=0.54),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.68, x1=0.05, y1=0.77),
                make_box("spatial_panel_title", "panel_title", x0=0.65, y0=0.88, x1=0.81, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.52, x1=0.79, y1=0.54),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.51, y0=0.62, x1=0.53, y1=0.83),
                make_box("composition_panel_title", "panel_title", x0=0.15, y0=0.47, x1=0.35, y1=0.50),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.18, y0=0.12, x1=0.32, y1=0.15),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.29, x1=0.05, y1=0.36),
                make_box("heatmap_panel_title", "panel_title", x0=0.63, y0=0.47, x1=0.80, y1=0.50),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.68, y0=0.11, x1=0.75, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.43, y0=0.23, x1=0.45, y1=0.42),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.83, x1=0.09, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.54, y0=0.83, x1=0.55, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.08, y0=0.40, x1=0.09, y1=0.42),
                make_box("panel_label_D", "panel_label", x0=0.54, y0=0.40, x1=0.55, y1=0.42),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.07, y0=0.54, x1=0.44, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.53, y0=0.54, x1=0.88, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.07, y0=0.18, x1=0.44, y1=0.44),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.53, y0=0.18, x1=0.88, y1=0.44),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.16, y0=0.02, x1=0.42, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.18, x1=0.94, y1=0.44),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.14, "y": 0.74, "state_label": "T cells"},
                    {"x": 0.29, "y": 0.62, "state_label": "Myeloid"},
                ],
                "spatial_points": [
                    {"x": 0.60, "y": 0.76, "state_label": "T cells"},
                    {"x": 0.78, "y": 0.62, "state_label": "Myeloid"},
                ],
                "state_labels": ["T cells", "Myeloid"],
                "row_labels": ["CXCL13 program", "TGF-beta program"],
                "composition_groups": [
                    {
                        "group_label": "Tumor core",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.64},
                            {"state_label": "Myeloid", "proportion": 0.36},
                        ],
                    },
                    {
                        "group_label": "Invasive margin",
                        "group_order": 2,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.42},
                            {"state_label": "Myeloid", "proportion": 0.58},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "T cells", "y": "CXCL13 program", "value": 0.74},
                    {"x": "Myeloid", "y": "CXCL13 program", "value": -0.16},
                    {"x": "T cells", "y": "TGF-beta program", "value": -0.19},
                    {"x": "Myeloid", "y": "TGF-beta program", "value": 0.69},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_atlas_spatial_bridge_spatial_states_drift() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_bridge_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_bridge_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("atlas_panel_title", "panel_title", x0=0.20, y0=0.88, x1=0.30, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.22, y0=0.52, x1=0.28, y1=0.54),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.68, x1=0.05, y1=0.77),
                make_box("spatial_panel_title", "panel_title", x0=0.65, y0=0.88, x1=0.81, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.52, x1=0.79, y1=0.54),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.51, y0=0.62, x1=0.53, y1=0.83),
                make_box("composition_panel_title", "panel_title", x0=0.15, y0=0.47, x1=0.35, y1=0.50),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.18, y0=0.12, x1=0.32, y1=0.15),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.29, x1=0.05, y1=0.36),
                make_box("heatmap_panel_title", "panel_title", x0=0.63, y0=0.47, x1=0.80, y1=0.50),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.68, y0=0.11, x1=0.75, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.43, y0=0.23, x1=0.45, y1=0.42),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.83, x1=0.09, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.54, y0=0.83, x1=0.55, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.08, y0=0.40, x1=0.09, y1=0.42),
                make_box("panel_label_D", "panel_label", x0=0.54, y0=0.40, x1=0.55, y1=0.42),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.07, y0=0.54, x1=0.44, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.53, y0=0.54, x1=0.88, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.07, y0=0.18, x1=0.44, y1=0.44),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.53, y0=0.18, x1=0.88, y1=0.44),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.16, y0=0.02, x1=0.42, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.18, x1=0.94, y1=0.44),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.14, "y": 0.74, "state_label": "T cells"},
                    {"x": 0.29, "y": 0.62, "state_label": "Myeloid"},
                ],
                "spatial_points": [
                    {"x": 0.60, "y": 0.76, "state_label": "T cells"},
                    {"x": 0.78, "y": 0.62, "state_label": "Fibroblast"},
                ],
                "state_labels": ["T cells", "Myeloid"],
                "row_labels": ["CXCL13 program", "TGF-beta program"],
                "composition_groups": [
                    {
                        "group_label": "Tumor core",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.64},
                            {"state_label": "Myeloid", "proportion": 0.36},
                        ],
                    }
                ],
                "matrix_cells": [
                    {"x": "T cells", "y": "CXCL13 program", "value": 0.74},
                    {"x": "Myeloid", "y": "CXCL13 program", "value": -0.16},
                    {"x": "T cells", "y": "TGF-beta program", "value": -0.19},
                    {"x": "Myeloid", "y": "TGF-beta program", "value": 0.69},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "spatial_point_state_label_unknown" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_spatial_niche_map_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_spatial_niche_map_panel",
        layout_sidecar={
            "template_id": "spatial_niche_map_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("spatial_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.26, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.10, x1=0.23, y1=0.13),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.30, x1=0.05, y1=0.74),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.58, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.43, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.28, x1=0.36, y1=0.76),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.86, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_spatial", "panel", x0=0.07, y0=0.18, x1=0.29, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.14, "y": 0.70, "niche_label": "Immune niche"},
                    {"x": 0.23, "y": 0.34, "niche_label": "Stromal niche"},
                ],
                "niche_labels": ["Immune niche", "Stromal niche"],
                "row_labels": ["CXCL13 program", "TGF-beta program"],
                "composition_groups": [
                    {
                        "group_label": "Tumor core",
                        "group_order": 1,
                        "niche_proportions": [
                            {"niche_label": "Immune niche", "proportion": 0.64},
                            {"niche_label": "Stromal niche", "proportion": 0.36},
                        ],
                    },
                    {
                        "group_label": "Invasive margin",
                        "group_order": 2,
                        "niche_proportions": [
                            {"niche_label": "Immune niche", "proportion": 0.42},
                            {"niche_label": "Stromal niche", "proportion": 0.58},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "Immune niche", "y": "CXCL13 program", "value": 0.74},
                    {"x": "Stromal niche", "y": "CXCL13 program", "value": -0.16},
                    {"x": "Immune niche", "y": "TGF-beta program", "value": -0.19},
                    {"x": "Stromal niche", "y": "TGF-beta program", "value": 0.69},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_spatial_niche_map_composition_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_spatial_niche_map_panel",
        layout_sidecar={
            "template_id": "spatial_niche_map_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("spatial_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.26, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.10, x1=0.23, y1=0.13),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.30, x1=0.05, y1=0.74),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.58, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.43, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.28, x1=0.36, y1=0.76),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.86, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_spatial", "panel", x0=0.07, y0=0.18, x1=0.29, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.14, "y": 0.70, "niche_label": "Immune niche"},
                    {"x": 0.23, "y": 0.34, "niche_label": "Stromal niche"},
                ],
                "niche_labels": ["Immune niche", "Stromal niche"],
                "row_labels": ["CXCL13 program", "TGF-beta program"],
                "composition_groups": [
                    {
                        "group_label": "Tumor core",
                        "group_order": 1,
                        "niche_proportions": [
                            {"niche_label": "Immune niche", "proportion": 0.64},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "Immune niche", "y": "CXCL13 program", "value": 0.74},
                    {"x": "Stromal niche", "y": "CXCL13 program", "value": -0.16},
                    {"x": "Immune niche", "y": "TGF-beta program", "value": -0.19},
                    {"x": "Stromal niche", "y": "TGF-beta program", "value": 0.69},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "composition_group_niche_set_mismatch" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_trajectory_progression_panel() -> None:
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
                            {"branch_label": "Branch B", "proportion": 0.51},
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

    assert result["status"] == "pass", result
    assert result["issues"] == []


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


def _make_shap_grouped_local_support_domain_layout_sidecar() -> dict[str, object]:
    return {
        "template_id": "shap_grouped_local_support_domain_panel",
        "device": make_device(),
        "render_context": {"layout_override": {"show_figure_title": False}},
        "layout_boxes": [
            make_box("panel_title_A", "panel_title", x0=0.12, y0=0.89, x1=0.29, y1=0.92),
            make_box("panel_title_B", "panel_title", x0=0.51, y0=0.89, x1=0.71, y1=0.92),
            make_box("panel_label_A", "panel_label", x0=0.11, y0=0.82, x1=0.13, y1=0.85),
            make_box("panel_label_B", "panel_label", x0=0.50, y0=0.82, x1=0.52, y1=0.85),
            make_box("group_label_A", "group_label", x0=0.16, y0=0.83, x1=0.31, y1=0.86),
            make_box("group_label_B", "group_label", x0=0.55, y0=0.83, x1=0.71, y1=0.86),
            make_box("baseline_label_A", "baseline_label", x0=0.16, y0=0.77, x1=0.23, y1=0.80),
            make_box("baseline_label_B", "baseline_label", x0=0.55, y0=0.77, x1=0.62, y1=0.80),
            make_box("prediction_label_A", "prediction_label", x0=0.25, y0=0.77, x1=0.32, y1=0.80),
            make_box("prediction_label_B", "prediction_label", x0=0.63, y0=0.77, x1=0.71, y1=0.80),
            make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.18, y0=0.50, x1=0.35, y1=0.53),
            make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.57, y0=0.50, x1=0.74, y1=0.53),
            make_box("feature_label_A_1", "feature_label", x0=0.02, y0=0.72, x1=0.09, y1=0.77),
            make_box("feature_label_A_2", "feature_label", x0=0.01, y0=0.63, x1=0.09, y1=0.68),
            make_box("feature_label_A_3", "feature_label", x0=0.00, y0=0.58, x1=0.09, y1=0.63),
            make_box("feature_label_B_1", "feature_label", x0=0.40, y0=0.72, x1=0.47, y1=0.77),
            make_box("feature_label_B_2", "feature_label", x0=0.39, y0=0.63, x1=0.47, y1=0.68),
            make_box("feature_label_B_3", "feature_label", x0=0.38, y0=0.58, x1=0.47, y1=0.63),
            make_box("contribution_bar_A_1", "contribution_bar", x0=0.22, y0=0.72, x1=0.34, y1=0.77),
            make_box("contribution_bar_A_2", "contribution_bar", x0=0.12, y0=0.63, x1=0.22, y1=0.68),
            make_box("contribution_bar_A_3", "contribution_bar", x0=0.22, y0=0.58, x1=0.25, y1=0.63),
            make_box("contribution_bar_B_1", "contribution_bar", x0=0.45, y0=0.72, x1=0.54, y1=0.77),
            make_box("contribution_bar_B_2", "contribution_bar", x0=0.54, y0=0.63, x1=0.57, y1=0.68),
            make_box("contribution_bar_B_3", "contribution_bar", x0=0.53, y0=0.58, x1=0.54, y1=0.63),
            make_box("value_label_A_1", "value_label", x0=0.35, y0=0.72, x1=0.40, y1=0.77),
            make_box("value_label_A_2", "value_label", x0=0.07, y0=0.63, x1=0.11, y1=0.68),
            make_box("value_label_A_3", "value_label", x0=0.26, y0=0.58, x1=0.31, y1=0.63),
            make_box("value_label_B_1", "value_label", x0=0.40, y0=0.72, x1=0.44, y1=0.77),
            make_box("value_label_B_2", "value_label", x0=0.58, y0=0.63, x1=0.62, y1=0.68),
            make_box("value_label_B_3", "value_label", x0=0.47, y0=0.58, x1=0.52, y1=0.63),
            make_box("panel_title_C", "panel_title", x0=0.12, y0=0.45, x1=0.30, y1=0.48),
            make_box("panel_title_D", "panel_title", x0=0.49, y0=0.45, x1=0.69, y1=0.48),
            make_box("panel_label_C", "panel_label", x0=0.12, y0=0.34, x1=0.14, y1=0.37),
            make_box("panel_label_D", "panel_label", x0=0.49, y0=0.34, x1=0.51, y1=0.37),
            make_box("x_axis_title_C", "subplot_x_axis_title", x0=0.16, y0=0.02, x1=0.29, y1=0.05),
            make_box("x_axis_title_D", "subplot_x_axis_title", x0=0.54, y0=0.02, x1=0.69, y1=0.05),
            make_box("support_y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.15, x1=0.07, y1=0.35),
            make_box("reference_label_C", "support_domain_reference_label", x0=0.20, y0=0.35, x1=0.28, y1=0.38),
            make_box("reference_label_D", "support_domain_reference_label", x0=0.58, y0=0.35, x1=0.68, y1=0.38),
            make_box("support_label_C_1", "support_label", x0=0.12, y0=0.10, x1=0.18, y1=0.13),
            make_box("support_label_C_2", "support_label", x0=0.18, y0=0.10, x1=0.24, y1=0.13),
            make_box("support_label_C_3", "support_label", x0=0.24, y0=0.10, x1=0.28, y1=0.13),
            make_box("support_label_C_4", "support_label", x0=0.28, y0=0.10, x1=0.33, y1=0.13),
            make_box("support_label_D_1", "support_label", x0=0.49, y0=0.10, x1=0.56, y1=0.13),
            make_box("support_label_D_2", "support_label", x0=0.56, y0=0.10, x1=0.61, y1=0.13),
            make_box("support_label_D_3", "support_label", x0=0.61, y0=0.10, x1=0.65, y1=0.13),
            make_box("support_label_D_4", "support_label", x0=0.65, y0=0.10, x1=0.72, y1=0.13),
            make_box("support_legend_title", "legend_title", x0=0.32, y0=0.01, x1=0.46, y1=0.04),
            make_box("support_legend_box", "legend_box", x0=0.23, y0=0.00, x1=0.77, y1=0.08),
        ],
        "panel_boxes": [
            make_box("panel_A", "panel", x0=0.12, y0=0.56, x1=0.40, y1=0.82),
            make_box("panel_B", "panel", x0=0.51, y0=0.56, x1=0.78, y1=0.82),
            make_box("panel_C", "panel", x0=0.11, y0=0.08, x1=0.34, y1=0.38),
            make_box("panel_D", "panel", x0=0.48, y0=0.08, x1=0.73, y1=0.38),
        ],
        "guide_boxes": [
            make_box("zero_line_A", "zero_line", x0=0.22, y0=0.56, x1=0.221, y1=0.82),
            make_box("zero_line_B", "zero_line", x0=0.54, y0=0.56, x1=0.541, y1=0.82),
            make_box("reference_line_C", "support_domain_reference_line", x0=0.22, y0=0.08, x1=0.221, y1=0.38),
            make_box("reference_line_D", "support_domain_reference_line", x0=0.60, y0=0.08, x1=0.601, y1=0.38),
            make_box("support_segment_C_1", "support_domain_segment", x0=0.12, y0=0.08, x1=0.18, y1=0.15),
            make_box("support_segment_C_2", "support_domain_segment", x0=0.18, y0=0.08, x1=0.24, y1=0.15),
            make_box("support_segment_C_3", "support_domain_segment", x0=0.24, y0=0.08, x1=0.29, y1=0.15),
            make_box("support_segment_C_4", "support_domain_segment", x0=0.29, y0=0.08, x1=0.33, y1=0.15),
            make_box("support_segment_D_1", "support_domain_segment", x0=0.49, y0=0.08, x1=0.56, y1=0.15),
            make_box("support_segment_D_2", "support_domain_segment", x0=0.56, y0=0.08, x1=0.61, y1=0.15),
            make_box("support_segment_D_3", "support_domain_segment", x0=0.61, y0=0.08, x1=0.66, y1=0.15),
            make_box("support_segment_D_4", "support_domain_segment", x0=0.66, y0=0.08, x1=0.72, y1=0.15),
        ],
        "metrics": {
            "local_shared_feature_order": ["Age", "Albumin", "Tumor size"],
            "support_y_label": "Predicted response probability",
            "support_legend_title": "Support domain",
            "support_legend_labels": [
                "Response curve",
                "Observed support",
                "Subgroup support",
                "Bin support",
                "Extrapolation reminder",
            ],
            "local_panels": [
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
            ],
            "support_panels": [
                {
                    "panel_id": "age_support",
                    "panel_label": "C",
                    "title": "Age support",
                    "x_label": "Age (years)",
                    "feature": "Age",
                    "reference_value": 60.0,
                    "reference_label": "Median age",
                    "panel_box_id": "panel_C",
                    "reference_line_box_id": "reference_line_C",
                    "reference_label_box_id": "reference_label_C",
                    "response_points": [{"x": 0.13, "y": 0.25}, {"x": 0.22, "y": 0.31}, {"x": 0.31, "y": 0.36}],
                    "support_segments": [
                        {
                            "segment_id": "age_observed",
                            "segment_label": "Observed",
                            "support_kind": "observed_support",
                            "segment_box_id": "support_segment_C_1",
                            "label_box_id": "support_label_C_1",
                        },
                        {
                            "segment_id": "age_subgroup",
                            "segment_label": "Subgroup",
                            "support_kind": "subgroup_support",
                            "segment_box_id": "support_segment_C_2",
                            "label_box_id": "support_label_C_2",
                        },
                        {
                            "segment_id": "age_bin",
                            "segment_label": "Bin",
                            "support_kind": "bin_support",
                            "segment_box_id": "support_segment_C_3",
                            "label_box_id": "support_label_C_3",
                        },
                        {
                            "segment_id": "age_extrapolation",
                            "segment_label": "Extrapolation",
                            "support_kind": "extrapolation_warning",
                            "segment_box_id": "support_segment_C_4",
                            "label_box_id": "support_label_C_4",
                        },
                    ],
                },
                {
                    "panel_id": "albumin_support",
                    "panel_label": "D",
                    "title": "Albumin support",
                    "x_label": "Albumin (g/dL)",
                    "feature": "Albumin",
                    "reference_value": 3.8,
                    "reference_label": "Median albumin",
                    "panel_box_id": "panel_D",
                    "reference_line_box_id": "reference_line_D",
                    "reference_label_box_id": "reference_label_D",
                    "response_points": [{"x": 0.50, "y": 0.35}, {"x": 0.60, "y": 0.27}, {"x": 0.71, "y": 0.18}],
                    "support_segments": [
                        {
                            "segment_id": "alb_observed",
                            "segment_label": "Observed",
                            "support_kind": "observed_support",
                            "segment_box_id": "support_segment_D_1",
                            "label_box_id": "support_label_D_1",
                        },
                        {
                            "segment_id": "alb_subgroup",
                            "segment_label": "Subgroup",
                            "support_kind": "subgroup_support",
                            "segment_box_id": "support_segment_D_2",
                            "label_box_id": "support_label_D_2",
                        },
                        {
                            "segment_id": "alb_bin",
                            "segment_label": "Bin",
                            "support_kind": "bin_support",
                            "segment_box_id": "support_segment_D_3",
                            "label_box_id": "support_label_D_3",
                        },
                        {
                            "segment_id": "alb_extrapolation",
                            "segment_label": "Extrapolation",
                            "support_kind": "extrapolation_warning",
                            "segment_box_id": "support_segment_D_4",
                            "label_box_id": "support_label_D_4",
                        },
                    ],
                },
            ],
        },
    }


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


def test_run_display_layout_qc_fails_when_generalizability_overview_marker_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_generalizability_subgroup_composite_panel",
        layout_sidecar={
            "template_id": "generalizability_subgroup_composite_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.12, y0=0.86, x1=0.34, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.58, y0=0.86, x1=0.84, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.82, x1=0.14, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.58, y0=0.82, x1=0.60, y1=0.85),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.20, y0=0.10, x1=0.32, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.67, y0=0.10, x1=0.76, y1=0.13),
                make_box("overview_row_label_1", "overview_row_label", x0=0.03, y0=0.63, x1=0.11, y1=0.67),
                make_box("overview_support_label_1", "support_label", x0=0.37, y0=0.63, x1=0.44, y1=0.67),
                make_box("overview_metric_marker_1", "overview_metric_marker", x0=0.46, y0=0.63, x1=0.47, y1=0.67),
                make_box("overview_comparator_marker_1", "overview_comparator_marker", x0=0.23, y0=0.63, x1=0.24, y1=0.67),
                make_box("subgroup_row_label_1", "subgroup_row_label", x0=0.46, y0=0.63, x1=0.56, y1=0.67),
                make_box("subgroup_ci_1", "ci_segment", x0=0.69, y0=0.645, x1=0.79, y1=0.655),
                make_box("subgroup_estimate_1", "estimate_marker", x0=0.74, y0=0.63, x1=0.75, y1=0.67),
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
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "overview_metric_marker_outside_panel" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_time_to_event_threshold_governance_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_time_to_event_threshold_governance_panel",
        layout_sidecar={
            "template_id": "time_to_event_threshold_governance_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.15, y0=0.86, x1=0.31, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.54, y0=0.86, x1=0.72, y1=0.89),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.54, y0=0.10, x1=0.72, y1=0.13),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.79, x1=0.14, y1=0.82),
                make_box("panel_label_B", "panel_label", x0=0.46, y0=0.79, x1=0.48, y1=0.82),
                make_box("threshold_card_1", "threshold_card", x0=0.14, y0=0.50, x1=0.34, y1=0.70),
                make_box("threshold_card_2", "threshold_card", x0=0.14, y0=0.24, x1=0.34, y1=0.44),
            ],
            "panel_boxes": [
                make_box("threshold_panel", "threshold_panel", x0=0.10, y0=0.18, x1=0.38, y1=0.82),
                make_box("calibration_panel", "calibration_panel", x0=0.46, y0=0.18, x1=0.82, y1=0.82),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.57, y0=0.03, x1=0.79, y1=0.10),
            ],
            "metrics": {
                "threshold_summaries": [
                    {
                        "threshold_label": "Rule-in",
                        "threshold": 0.10,
                        "sensitivity": 0.88,
                        "specificity": 0.52,
                        "net_benefit": 0.041,
                        "card_box_id": "threshold_card_1",
                    },
                    {
                        "threshold_label": "Actionable",
                        "threshold": 0.15,
                        "sensitivity": 0.74,
                        "specificity": 0.67,
                        "net_benefit": 0.058,
                        "card_box_id": "threshold_card_2",
                    },
                ],
                "risk_group_summaries": [
                    {
                        "group_label": "Low risk",
                        "group_order": 1,
                        "n": 182,
                        "events": 8,
                        "predicted_risk": 0.04,
                        "observed_risk": 0.05,
                        "predicted_x": 0.52,
                        "observed_x": 0.55,
                        "y": 0.30,
                    },
                    {
                        "group_label": "Intermediate risk",
                        "group_order": 2,
                        "n": 146,
                        "events": 19,
                        "predicted_risk": 0.13,
                        "observed_risk": 0.15,
                        "predicted_x": 0.61,
                        "observed_x": 0.65,
                        "y": 0.50,
                    },
                    {
                        "group_label": "High risk",
                        "group_order": 3,
                        "n": 88,
                        "events": 27,
                        "predicted_risk": 0.31,
                        "observed_risk": 0.29,
                        "predicted_x": 0.76,
                        "observed_x": 0.73,
                        "y": 0.70,
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_threshold_governance_point_leaves_calibration_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_time_to_event_threshold_governance_panel",
        layout_sidecar={
            "template_id": "time_to_event_threshold_governance_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.15, y0=0.86, x1=0.31, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.54, y0=0.86, x1=0.72, y1=0.89),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.54, y0=0.10, x1=0.72, y1=0.13),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.79, x1=0.14, y1=0.82),
                make_box("panel_label_B", "panel_label", x0=0.46, y0=0.79, x1=0.48, y1=0.82),
                make_box("threshold_card_1", "threshold_card", x0=0.14, y0=0.50, x1=0.34, y1=0.70),
                make_box("threshold_card_2", "threshold_card", x0=0.14, y0=0.24, x1=0.34, y1=0.44),
            ],
            "panel_boxes": [
                make_box("threshold_panel", "threshold_panel", x0=0.10, y0=0.18, x1=0.38, y1=0.82),
                make_box("calibration_panel", "calibration_panel", x0=0.46, y0=0.18, x1=0.82, y1=0.82),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.57, y0=0.03, x1=0.79, y1=0.10),
            ],
            "metrics": {
                "threshold_summaries": [
                    {
                        "threshold_label": "Rule-in",
                        "threshold": 0.10,
                        "sensitivity": 0.88,
                        "specificity": 0.52,
                        "net_benefit": 0.041,
                        "card_box_id": "threshold_card_1",
                    },
                    {
                        "threshold_label": "Actionable",
                        "threshold": 0.15,
                        "sensitivity": 0.74,
                        "specificity": 0.67,
                        "net_benefit": 0.058,
                        "card_box_id": "threshold_card_2",
                    },
                ],
                "risk_group_summaries": [
                    {
                        "group_label": "Low risk",
                        "group_order": 1,
                        "n": 182,
                        "events": 8,
                        "predicted_risk": 0.04,
                        "observed_risk": 0.05,
                        "predicted_x": 0.52,
                        "observed_x": 0.55,
                        "y": 0.30,
                    },
                    {
                        "group_label": "Intermediate risk",
                        "group_order": 2,
                        "n": 146,
                        "events": 19,
                        "predicted_risk": 0.13,
                        "observed_risk": 0.15,
                        "predicted_x": 0.61,
                        "observed_x": 0.89,
                        "y": 0.50,
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "calibration_point_outside_panel" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_time_to_event_multihorizon_calibration_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_time_to_event_multihorizon_calibration_panel",
        layout_sidecar={
            "template_id": "time_to_event_multihorizon_calibration_panel",
            "device": make_device(),
            "render_context": {"layout_override": {"show_figure_title": False}},
            "layout_boxes": [
                make_box("x_axis_title", "subplot_x_axis_title", x0=0.34, y0=0.08, x1=0.58, y1=0.12),
                make_box("panel_title_A", "panel_title", x0=0.16, y0=0.86, x1=0.34, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.57, y0=0.86, x1=0.76, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.79, x1=0.14, y1=0.82),
                make_box("panel_label_B", "panel_label", x0=0.53, y0=0.79, x1=0.55, y1=0.82),
            ],
            "panel_boxes": [
                make_box("panel_A", "calibration_panel", x0=0.10, y0=0.18, x1=0.42, y1=0.82),
                make_box("panel_B", "calibration_panel", x0=0.51, y0=0.18, x1=0.83, y1=0.82),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.33, y0=0.02, x1=0.60, y1=0.08),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "h36",
                        "panel_label": "A",
                        "title": "36-month calibration",
                        "time_horizon_months": 36,
                        "calibration_summary": [
                            {
                                "group_label": "Low risk",
                                "group_order": 1,
                                "n": 182,
                                "events": 5,
                                "predicted_risk": 0.03,
                                "observed_risk": 0.04,
                                "predicted_x": 0.16,
                                "observed_x": 0.18,
                                "y": 0.30,
                            },
                            {
                                "group_label": "Intermediate risk",
                                "group_order": 2,
                                "n": 146,
                                "events": 13,
                                "predicted_risk": 0.11,
                                "observed_risk": 0.13,
                                "predicted_x": 0.24,
                                "observed_x": 0.27,
                                "y": 0.50,
                            },
                            {
                                "group_label": "High risk",
                                "group_order": 3,
                                "n": 88,
                                "events": 22,
                                "predicted_risk": 0.24,
                                "observed_risk": 0.27,
                                "predicted_x": 0.35,
                                "observed_x": 0.38,
                                "y": 0.70,
                            },
                        ],
                    },
                    {
                        "panel_id": "h60",
                        "panel_label": "B",
                        "title": "60-month calibration",
                        "time_horizon_months": 60,
                        "calibration_summary": [
                            {
                                "group_label": "Low risk",
                                "group_order": 1,
                                "n": 182,
                                "events": 8,
                                "predicted_risk": 0.04,
                                "observed_risk": 0.05,
                                "predicted_x": 0.57,
                                "observed_x": 0.60,
                                "y": 0.30,
                            },
                            {
                                "group_label": "Intermediate risk",
                                "group_order": 2,
                                "n": 146,
                                "events": 19,
                                "predicted_risk": 0.13,
                                "observed_risk": 0.15,
                                "predicted_x": 0.66,
                                "observed_x": 0.69,
                                "y": 0.50,
                            },
                            {
                                "group_label": "High risk",
                                "group_order": 3,
                                "n": 88,
                                "events": 27,
                                "predicted_risk": 0.31,
                                "observed_risk": 0.29,
                                "predicted_x": 0.77,
                                "observed_x": 0.74,
                                "y": 0.70,
                            },
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []


def test_run_display_layout_qc_fails_when_multihorizon_calibration_point_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_time_to_event_multihorizon_calibration_panel",
        layout_sidecar={
            "template_id": "time_to_event_multihorizon_calibration_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("x_axis_title", "subplot_x_axis_title", x0=0.34, y0=0.08, x1=0.58, y1=0.12),
                make_box("panel_title_A", "panel_title", x0=0.16, y0=0.86, x1=0.34, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.57, y0=0.86, x1=0.76, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.12, y0=0.79, x1=0.14, y1=0.82),
                make_box("panel_label_B", "panel_label", x0=0.53, y0=0.79, x1=0.55, y1=0.82),
            ],
            "panel_boxes": [
                make_box("panel_A", "calibration_panel", x0=0.10, y0=0.18, x1=0.42, y1=0.82),
                make_box("panel_B", "calibration_panel", x0=0.51, y0=0.18, x1=0.83, y1=0.82),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.33, y0=0.02, x1=0.60, y1=0.08),
            ],
            "metrics": {
                "panels": [
                    {
                        "panel_id": "h36",
                        "panel_label": "A",
                        "title": "36-month calibration",
                        "time_horizon_months": 36,
                        "calibration_summary": [
                            {
                                "group_label": "Low risk",
                                "group_order": 1,
                                "n": 182,
                                "events": 5,
                                "predicted_risk": 0.03,
                                "observed_risk": 0.04,
                                "predicted_x": 0.16,
                                "observed_x": 0.18,
                                "y": 0.30,
                            },
                            {
                                "group_label": "Intermediate risk",
                                "group_order": 2,
                                "n": 146,
                                "events": 13,
                                "predicted_risk": 0.11,
                                "observed_risk": 0.13,
                                "predicted_x": 0.24,
                                "observed_x": 0.27,
                                "y": 0.50,
                            },
                        ],
                    },
                    {
                        "panel_id": "h60",
                        "panel_label": "B",
                        "title": "60-month calibration",
                        "time_horizon_months": 60,
                        "calibration_summary": [
                            {
                                "group_label": "Low risk",
                                "group_order": 1,
                                "n": 182,
                                "events": 8,
                                "predicted_risk": 0.04,
                                "observed_risk": 0.05,
                                "predicted_x": 0.57,
                                "observed_x": 0.60,
                                "y": 0.30,
                            },
                            {
                                "group_label": "Intermediate risk",
                                "group_order": 2,
                                "n": 146,
                                "events": 19,
                                "predicted_risk": 0.13,
                                "observed_risk": 0.15,
                                "predicted_x": 0.66,
                                "observed_x": 0.89,
                                "y": 0.50,
                            },
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "calibration_point_outside_panel" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_binary_calibration_focus_window_leaves_panel() -> None:
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
                make_box("decision_focus_window", "focus_window", x0=0.58, y0=0.22, x1=0.99, y1=0.84),
            ],
            "metrics": {
                "calibration_series": [{"label": "Core", "x": [0.1, 0.2], "y": [0.05, 0.10]}],
                "calibration_reference_line": {"label": "Ideal", "x": [0.0, 1.0], "y": [0.0, 1.0]},
                "decision_series": [{"label": "Core", "x": [0.15, 0.20], "y": [0.01, 0.0]}],
                "decision_reference_lines": [{"label": "Treat none", "x": [0.15, 0.20], "y": [0.0, 0.0]}],
                "decision_focus_window": {"xmin": 0.15, "xmax": 0.35},
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "focus_window_outside_panel" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_model_complexity_audit_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_model_complexity_audit",
        layout_sidecar={
            "template_id": "model_complexity_audit_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.08, y0=0.95, x1=0.92, y1=0.985),
                make_box("metric_panel_title_1", "subplot_title", x0=0.20, y0=0.89, x1=0.38, y1=0.92),
                make_box("metric_panel_title_2", "subplot_title", x0=0.20, y0=0.59, x1=0.38, y1=0.62),
                make_box("metric_panel_title_3", "subplot_title", x0=0.20, y0=0.29, x1=0.38, y1=0.32),
                make_box("audit_panel_title_1", "subplot_title", x0=0.68, y0=0.89, x1=0.86, y1=0.92),
                make_box("audit_panel_title_2", "subplot_title", x0=0.68, y0=0.44, x1=0.86, y1=0.47),
                make_box("metric_marker_1", "metric_marker", x0=0.26, y0=0.83, x1=0.28, y1=0.85),
                make_box("metric_marker_2", "metric_marker", x0=0.30, y0=0.77, x1=0.32, y1=0.79),
                make_box("metric_marker_3", "metric_marker", x0=0.34, y0=0.71, x1=0.36, y1=0.73),
                make_box("metric_marker_4", "metric_marker", x0=0.24, y0=0.53, x1=0.26, y1=0.55),
                make_box("metric_marker_5", "metric_marker", x0=0.28, y0=0.47, x1=0.30, y1=0.49),
                make_box("metric_marker_6", "metric_marker", x0=0.32, y0=0.41, x1=0.34, y1=0.43),
                make_box("metric_marker_7", "metric_marker", x0=0.22, y0=0.23, x1=0.24, y1=0.25),
                make_box("metric_marker_8", "metric_marker", x0=0.27, y0=0.17, x1=0.29, y1=0.19),
                make_box("metric_marker_9", "metric_marker", x0=0.31, y0=0.11, x1=0.33, y1=0.13),
                make_box("audit_bar_1", "audit_bar", x0=0.66, y0=0.82, x1=0.86, y1=0.85),
                make_box("audit_bar_2", "audit_bar", x0=0.66, y0=0.76, x1=0.90, y1=0.79),
                make_box("audit_bar_3", "audit_bar", x0=0.66, y0=0.70, x1=0.83, y1=0.73),
                make_box("audit_bar_4", "audit_bar", x0=0.66, y0=0.30, x1=0.82, y1=0.33),
                make_box("audit_bar_5", "audit_bar", x0=0.66, y0=0.24, x1=0.78, y1=0.27),
            ],
            "panel_boxes": [
                make_box("metric_panel_1", "metric_panel", x0=0.12, y0=0.68, x1=0.54, y1=0.88),
                make_box("metric_panel_2", "metric_panel", x0=0.12, y0=0.38, x1=0.54, y1=0.58),
                make_box("metric_panel_3", "metric_panel", x0=0.12, y0=0.08, x1=0.54, y1=0.28),
                make_box("audit_panel_1", "audit_panel", x0=0.66, y0=0.56, x1=0.96, y1=0.88),
                make_box("audit_panel_2", "audit_panel", x0=0.66, y0=0.08, x1=0.96, y1=0.40),
            ],
            "guide_boxes": [
                make_box("reference_line_1", "reference_line", x0=0.29, y0=0.08, x1=0.30, y1=0.88),
                make_box("reference_line_2", "reference_line", x0=0.80, y0=0.56, x1=0.81, y1=0.88),
            ],
            "metrics": {
                "metric_panels": [
                    {
                        "panel_id": "auroc_panel",
                        "panel_label": "A",
                        "title": "Discrimination",
                        "x_label": "AUROC",
                        "rows": [
                            {"label": "Core", "value": 0.80},
                            {"label": "Clinical", "value": 0.82},
                            {"label": "RF", "value": 0.84},
                        ],
                    },
                    {
                        "panel_id": "brier_panel",
                        "panel_label": "B",
                        "title": "Overall error",
                        "x_label": "Brier score",
                        "rows": [
                            {"label": "Core", "value": 0.14},
                            {"label": "Clinical", "value": 0.11},
                            {"label": "RF", "value": 0.10},
                        ],
                    },
                    {
                        "panel_id": "slope_panel",
                        "panel_label": "C",
                        "title": "Calibration",
                        "x_label": "Calibration slope",
                        "reference_value": 1.0,
                        "rows": [
                            {"label": "Core", "value": 2.4},
                            {"label": "Clinical", "value": 1.04},
                            {"label": "RF", "value": 0.80},
                        ],
                    },
                ],
                "audit_panels": [
                    {
                        "panel_id": "coefficient_panel",
                        "panel_label": "D",
                        "title": "Coefficient stability",
                        "x_label": "Mean odds ratio",
                        "reference_value": 1.0,
                        "rows": [
                            {"label": "Age", "value": 0.91},
                            {"label": "Tumor diameter", "value": 1.44},
                            {"label": "Knosp grade", "value": 1.13},
                        ],
                    },
                    {
                        "panel_id": "domain_panel",
                        "panel_label": "E",
                        "title": "Domain stability",
                        "x_label": "Mean absolute coefficient",
                        "rows": [
                            {"label": "Tumor burden", "value": 0.34},
                            {"label": "Endocrine impairment", "value": 0.11},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_passes_for_time_to_event_landmark_performance_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_landmark_performance_panel",
        layout_sidecar={
            "template_id": "time_to_event_landmark_performance_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("title", "title", x0=0.08, y0=0.95, x1=0.92, y1=0.985),
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
                make_box("metric_marker_2", "metric_marker", x0=0.24, y0=0.52, x1=0.26, y1=0.54),
                make_box("metric_marker_3", "metric_marker", x0=0.26, y0=0.32, x1=0.28, y1=0.34),
                make_box("metric_marker_4", "metric_marker", x0=0.48, y0=0.72, x1=0.50, y1=0.74),
                make_box("metric_marker_5", "metric_marker", x0=0.46, y0=0.52, x1=0.48, y1=0.54),
                make_box("metric_marker_6", "metric_marker", x0=0.44, y0=0.32, x1=0.46, y1=0.34),
                make_box("metric_marker_7", "metric_marker", x0=0.78, y0=0.72, x1=0.80, y1=0.74),
                make_box("metric_marker_8", "metric_marker", x0=0.76, y0=0.52, x1=0.78, y1=0.54),
                make_box("metric_marker_9", "metric_marker", x0=0.74, y0=0.32, x1=0.76, y1=0.34),
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
                                "label": "3→12 months",
                                "analysis_window_label": "3-month landmark predicting 12-month recurrence",
                                "landmark_months": 3,
                                "prediction_months": 12,
                                "value": 0.78,
                            },
                            {
                                "label": "6→15 months",
                                "analysis_window_label": "6-month landmark predicting 15-month recurrence",
                                "landmark_months": 6,
                                "prediction_months": 15,
                                "value": 0.81,
                            },
                            {
                                "label": "9→18 months",
                                "analysis_window_label": "9-month landmark predicting 18-month recurrence",
                                "landmark_months": 9,
                                "prediction_months": 18,
                                "value": 0.84,
                            },
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
                                "label": "3→12 months",
                                "analysis_window_label": "3-month landmark predicting 12-month recurrence",
                                "landmark_months": 3,
                                "prediction_months": 12,
                                "value": 0.18,
                            },
                            {
                                "label": "6→15 months",
                                "analysis_window_label": "6-month landmark predicting 15-month recurrence",
                                "landmark_months": 6,
                                "prediction_months": 15,
                                "value": 0.15,
                            },
                            {
                                "label": "9→18 months",
                                "analysis_window_label": "9-month landmark predicting 18-month recurrence",
                                "landmark_months": 9,
                                "prediction_months": 18,
                                "value": 0.12,
                            },
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
                                "label": "3→12 months",
                                "analysis_window_label": "3-month landmark predicting 12-month recurrence",
                                "landmark_months": 3,
                                "prediction_months": 12,
                                "value": 1.06,
                            },
                            {
                                "label": "6→15 months",
                                "analysis_window_label": "6-month landmark predicting 15-month recurrence",
                                "landmark_months": 6,
                                "prediction_months": 15,
                                "value": 0.98,
                            },
                            {
                                "label": "9→18 months",
                                "analysis_window_label": "9-month landmark predicting 18-month recurrence",
                                "landmark_months": 9,
                                "prediction_months": 18,
                                "value": 0.93,
                            },
                        ],
                    },
                ]
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


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
