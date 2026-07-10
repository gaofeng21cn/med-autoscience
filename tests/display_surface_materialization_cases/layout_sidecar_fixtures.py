from __future__ import annotations

from collections.abc import Callable

from med_autoscience.display_pack_resolver import get_template_short_id


def _box(box_id: str, box_type: str, x0: float, y0: float, x1: float, y1: float) -> dict[str, object]:
    return {"box_id": box_id, "box_type": box_type, "x0": x0, "y0": y0, "x1": x1, "y1": y1}


def _sidecar(
    template_id: str,
    *,
    layout_boxes: list[dict[str, object]],
    panel_boxes: list[dict[str, object]],
    guide_boxes: list[dict[str, object]],
    metrics: dict[str, object],
) -> dict[str, object]:
    return {
        "template_id": template_id,
        "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
        "layout_boxes": layout_boxes,
        "panel_boxes": panel_boxes,
        "guide_boxes": guide_boxes,
        "metrics": metrics,
    }


def _curve_sidecar(template_id: str) -> dict[str, object]:
    return _sidecar(
        template_id,
        layout_boxes=[
            _box("title", "title", 0.10, 0.02, 0.62, 0.08),
            _box("x_axis_title", "x_axis_title", 0.28, 0.92, 0.62, 0.97),
            _box("y_axis_title", "y_axis_title", 0.02, 0.24, 0.06, 0.74),
        ],
        panel_boxes=[_box("panel", "panel", 0.10, 0.16, 0.74, 0.86)],
        guide_boxes=[_box("legend", "legend", 0.80, 0.30, 0.96, 0.44)],
        metrics={
            "series": [{"label": "Model", "x": [0.0, 0.5, 1.0], "y": [0.0, 0.72, 1.0]}],
            "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
        },
    )


def _survival_sidecar(template_id: str) -> dict[str, object]:
    payload = _curve_sidecar(template_id)
    payload["metrics"] = {
        "groups": [
            {"label": "Low risk", "times": [0.0, 12.0], "values": [1.0, 0.92]},
            {"label": "High risk", "times": [0.0, 12.0], "values": [1.0, 0.76]},
        ]
    }
    return payload


def _cohort_flow_sidecar(template_id: str) -> dict[str, object]:
    return _sidecar(
        template_id,
        layout_boxes=[
            _box("panel_label_A", "panel_label", 0.08, 0.125, 0.11, 0.155),
            _box("panel_label_B", "panel_label", 0.52, 0.125, 0.55, 0.155),
            _box("step_screened", "main_step", 0.08, 0.40, 0.28, 0.50),
            _box("step_included", "main_step", 0.08, 0.24, 0.28, 0.34),
            _box("exclusion_repeat", "exclusion_box", 0.32, 0.30, 0.46, 0.38),
            _box("participant_endpoint_summary", "summary_panel", 0.54, 0.58, 0.92, 0.76),
            _box("participant_design_summary", "summary_panel", 0.54, 0.32, 0.92, 0.54),
        ],
        panel_boxes=[
            _box("participant_flow_main", "subfigure_panel", 0.06, 0.10, 0.98, 0.84),
            _box("subfigure_panel_A", "subfigure_panel", 0.06, 0.10, 0.48, 0.54),
            _box("subfigure_panel_B", "subfigure_panel", 0.52, 0.10, 0.94, 0.54),
            _box("flow_panel", "flow_panel", 0.08, 0.12, 0.46, 0.50),
            _box("secondary_panel_validation", "secondary_panel", 0.54, 0.42, 0.92, 0.52),
            _box("secondary_panel_core", "secondary_panel", 0.54, 0.28, 0.72, 0.38),
            _box("secondary_panel_primary", "secondary_panel", 0.74, 0.28, 0.92, 0.38),
            _box("secondary_panel_audit", "secondary_panel", 0.54, 0.14, 0.72, 0.24),
            _box("secondary_panel_context", "secondary_panel", 0.74, 0.14, 0.92, 0.24),
        ],
        guide_boxes=[
            _box("flow_spine_screened_to_included", "flow_connector", 0.17, 0.34, 0.19, 0.40),
            _box("flow_branch_repeat", "flow_branch_connector", 0.19, 0.33, 0.32, 0.35),
            _box("hierarchy_root_trunk", "hierarchy_connector", 0.72, 0.38, 0.74, 0.42),
            _box("hierarchy_root_branch", "hierarchy_connector", 0.63, 0.36, 0.83, 0.38),
            _box("hierarchy_left", "hierarchy_connector", 0.63, 0.24, 0.65, 0.28),
            _box("hierarchy_right", "hierarchy_connector", 0.83, 0.24, 0.85, 0.28),
        ],
        metrics={
            "layout_mode": "participant_flow",
            "steps": [{"step_id": "screened"}, {"step_id": "included"}],
            "exclusions": [{"exclusion_id": "repeat", "from_step_id": "screened"}],
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
                    "box_id": box_id,
                    "box_type": box_type,
                    "line_count": 2,
                    "max_line_chars": 24,
                    "rendered_height_pt": 92.0,
                    "rendered_width_pt": 218.0,
                    "padding_pt": 9.0,
                }
                for box_id, box_type in (
                    ("step_screened", "main_step"),
                    ("step_included", "main_step"),
                    ("exclusion_repeat", "exclusion_box"),
                )
            ],
        },
    )


def _risk_group_sidecar(template_id: str) -> dict[str, object]:
    return _sidecar(
        template_id,
        layout_boxes=[
            _box("panel_label_A", "panel_label", 0.12, 0.78, 0.15, 0.82),
            _box("panel_label_B", "panel_label", 0.58, 0.78, 0.61, 0.82),
            _box("x_axis_title", "x_axis_title", 0.18, 0.09, 0.40, 0.13),
            _box("y_axis_title", "y_axis_title", 0.01, 0.40, 0.05, 0.62),
            _box("panel_right_x_axis_title", "subplot_x_axis_title", 0.62, 0.09, 0.86, 0.13),
            _box("panel_right_y_axis_title", "subplot_y_axis_title", 0.50, 0.40, 0.54, 0.62),
            _box("predicted_risk_bar_1", "risk_bar", 0.18, 0.54, 0.22, 0.68),
            _box("predicted_risk_bar_2", "risk_bar", 0.28, 0.34, 0.32, 0.68),
            _box("observed_event_bar_1", "risk_bar", 0.64, 0.54, 0.68, 0.68),
            _box("observed_event_bar_2", "risk_bar", 0.74, 0.30, 0.78, 0.68),
        ],
        panel_boxes=[
            _box("panel_left", "panel", 0.10, 0.16, 0.44, 0.86),
            _box("panel_right", "panel", 0.56, 0.16, 0.90, 0.86),
        ],
        guide_boxes=[],
        metrics={
            "risk_group_summaries": [
                {"label": "Low risk", "sample_size": 80, "events_5y": 5, "mean_predicted_risk_5y": 0.07, "observed_km_risk_5y": 0.06},
                {"label": "High risk", "sample_size": 60, "events_5y": 18, "mean_predicted_risk_5y": 0.28, "observed_km_risk_5y": 0.30},
            ]
        },
    )


def _discrimination_calibration_sidecar(template_id: str) -> dict[str, object]:
    return _sidecar(
        template_id,
        layout_boxes=[
            _box("panel_label_A", "panel_label", 0.12, 0.78, 0.15, 0.82),
            _box("panel_label_B", "panel_label", 0.58, 0.78, 0.61, 0.82),
            _box("panel_left_x_axis_title", "subplot_x_axis_title", 0.18, 0.09, 0.40, 0.13),
            _box("panel_left_y_axis_title", "subplot_y_axis_title", 0.01, 0.40, 0.05, 0.62),
            _box("calibration_x_axis_title", "subplot_x_axis_title", 0.62, 0.09, 0.86, 0.13),
            _box("calibration_y_axis_title", "subplot_y_axis_title", 0.50, 0.40, 0.54, 0.62),
            _box("discrimination_marker_1", "metric_marker", 0.26, 0.58, 0.28, 0.60),
            _box("calibration_marker_predicted_1", "metric_marker", 0.66, 0.30, 0.68, 0.32),
            _box("calibration_marker_observed_1", "metric_marker", 0.68, 0.31, 0.70, 0.33),
        ],
        panel_boxes=[
            _box("panel_left", "panel", 0.10, 0.16, 0.44, 0.86),
            _box("panel_right", "panel", 0.56, 0.16, 0.90, 0.86),
        ],
        guide_boxes=[_box("legend", "legend", 0.24, 0.06, 0.76, 0.13)],
        metrics={
            "discrimination_points": [{"label": "Model", "c_index": 0.81}],
            "calibration_summary": [
                {"group_label": "Low", "group_order": 1, "n": 80, "events_5y": 5, "predicted_risk_5y": 0.07, "observed_risk_5y": 0.06},
                {"group_label": "High", "group_order": 2, "n": 60, "events_5y": 18, "predicted_risk_5y": 0.28, "observed_risk_5y": 0.30},
            ],
            "series": [{"label": "C-index", "x": [0.0, 1.0], "y": [0.5, 0.5]}],
            "reference_line": {"x": [0.0, 1.0], "y": [0.5, 0.5]},
        },
    )


def _time_to_event_decision_sidecar(template_id: str) -> dict[str, object]:
    payload = _risk_group_sidecar(template_id)
    payload["metrics"] = {
        "series": [{"label": "Model", "x": [0.05, 0.20, 0.40], "y": [0.16, 0.12, 0.06]}],
        "reference_line": {"x": [0.05, 0.40], "y": [0.0, 0.0]},
        "treated_fraction_series": {"label": "Model", "x": [0.05, 0.20, 0.40], "y": [60.0, 30.0, 12.0]},
    }
    return payload


def _generalizability_sidecar(template_id: str) -> dict[str, object]:
    return _sidecar(
        template_id,
        layout_boxes=[
            _box("panel_label_A", "panel_label", 0.08, 0.08, 0.11, 0.12),
            _box("panel_label_B", "panel_label", 0.08, 0.51, 0.11, 0.55),
            _box("overview_title", "panel_title", 0.30, 0.08, 0.58, 0.12),
            _box("subgroup_title", "panel_title", 0.30, 0.51, 0.58, 0.55),
            _box("overview_x_axis_title", "subplot_x_axis_title", 0.42, 0.47, 0.68, 0.51),
            _box("subgroup_x_axis_title", "subplot_x_axis_title", 0.42, 0.91, 0.68, 0.95),
            _box("overview_row_1_label", "overview_row_label", 0.08, 0.22, 0.26, 0.27),
            _box("overview_support_1", "support_label", 0.32, 0.22, 0.42, 0.27),
            _box("overview_primary_1", "overview_metric_marker", 0.56, 0.22, 0.58, 0.27),
            _box("overview_comparator_1", "overview_comparator_marker", 0.51, 0.22, 0.53, 0.27),
            _box("subgroup_row_1_label", "subgroup_row_label", 0.08, 0.66, 0.26, 0.71),
            _box("subgroup_estimate_1", "estimate_marker", 0.57, 0.66, 0.59, 0.71),
            _box("subgroup_ci_1", "ci_segment", 0.51, 0.685, 0.64, 0.695),
        ],
        panel_boxes=[
            _box("overview_panel", "panel", 0.30, 0.14, 0.84, 0.46),
            _box("subgroup_panel", "panel", 0.30, 0.57, 0.84, 0.90),
        ],
        guide_boxes=[
            _box("legend", "legend", 0.70, 0.02, 0.92, 0.08),
            _box("subgroup_reference_line", "reference_line", 0.54, 0.57, 0.54, 0.90),
        ],
        metrics={
            "metric_family": "discrimination",
            "primary_label": "Locked model",
            "comparator_label": "Derivation cohort",
            "legend_title": "Cohort",
            "legend_labels": ["Locked model", "Derivation cohort"],
            "overview_rows": [
                {
                    "cohort_id": "external",
                    "cohort_label": "External",
                    "support_count": 184,
                    "event_count": 29,
                    "metric_value": 0.82,
                    "comparator_metric_value": 0.79,
                    "label_box_id": "overview_row_1_label",
                    "support_label_box_id": "overview_support_1",
                    "metric_marker_box_id": "overview_primary_1",
                    "comparator_marker_box_id": "overview_comparator_1",
                }
            ],
            "subgroup_reference_value": 0.80,
            "subgroup_rows": [
                {
                    "subgroup_id": "age",
                    "subgroup_label": "Age >=65 years",
                    "group_n": 201,
                    "estimate": 0.82,
                    "lower": 0.78,
                    "upper": 0.86,
                    "label_box_id": "subgroup_row_1_label",
                    "estimate_box_id": "subgroup_estimate_1",
                    "ci_box_id": "subgroup_ci_1",
                }
            ],
        },
    )


_BUILDERS: dict[str, Callable[[str], dict[str, object]]] = {
    "cohort_flow_figure": _cohort_flow_sidecar,
    "roc_curve_binary": _curve_sidecar,
    "pr_curve_binary": _curve_sidecar,
    "calibration_curve_binary": _curve_sidecar,
    "decision_curve_binary": _curve_sidecar,
    "kaplan_meier_grouped": _survival_sidecar,
    "time_to_event_risk_group_summary": _risk_group_sidecar,
    "time_to_event_discrimination_calibration_panel": _discrimination_calibration_sidecar,
    "time_to_event_decision_curve": _time_to_event_decision_sidecar,
    "generalizability_subgroup_composite_panel": _generalizability_sidecar,
}


def _minimal_layout_sidecar_for_template(
    template_id: str,
    display_payload: dict[str, object] | None = None,
) -> dict[str, object]:
    del display_payload
    short_id = get_template_short_id(template_id) if "::" in template_id else template_id
    try:
        return _BUILDERS[short_id](template_id)
    except KeyError as exc:
        raise ValueError(f"unsupported template_id `{template_id}` in sparse test layout fixture") from exc


__all__ = ["_minimal_layout_sidecar_for_template"]
