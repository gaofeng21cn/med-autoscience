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
