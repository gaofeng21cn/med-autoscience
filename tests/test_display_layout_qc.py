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
