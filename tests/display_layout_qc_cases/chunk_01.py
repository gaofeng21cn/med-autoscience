from .shared import *

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
