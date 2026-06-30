from __future__ import annotations

from med_autoscience import display_registry
from med_autoscience.display_pack_resolver import get_template_short_id


def _box(box_id: str, box_type: str, x0: float, y0: float, x1: float, y1: float) -> dict[str, object]:
    return {"box_id": box_id, "box_type": box_type, "x0": x0, "y0": y0, "x1": x1, "y1": y1}


def _base_sidecar(template_id: str) -> dict[str, object]:
    return {"template_id": template_id, "device": _box("device", "device", 0.0, 0.0, 1.0, 1.0)}


def _purpose_metrics(template_id: str, purpose: str | None = None) -> dict[str, object]:
    template_short_id = get_template_short_id(template_id) if "::" in template_id else template_id
    return {
        "source_renderer": f"MAS/DisplayPack::{template_short_id}",
        "figure_purpose": purpose or f"purpose_first_{template_short_id}",
        "rendered_title_policy": "figure_title_metadata_only_not_drawn_inside_plot",
    }


def _curve_sidecar(template_id: str, *, time_dependent: bool = False) -> dict[str, object]:
    metrics: dict[str, object] = {
        "series": [{"label": "Model", "x": [0.0, 0.5, 1.0], "y": [0.0, 0.72, 1.0]}],
        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
    }
    if time_dependent:
        metrics["time_horizon_months"] = 24
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("x_axis_title", "x_axis_title", 0.28, 0.92, 0.62, 0.97),
            _box("y_axis_title", "y_axis_title", 0.02, 0.24, 0.06, 0.74),
        ],
        "panel_boxes": [_box("panel", "panel", 0.10, 0.16, 0.74, 0.86)],
        "guide_boxes": [_box("legend", "legend", 0.80, 0.30, 0.96, 0.44)],
        "metrics": {**_purpose_metrics(template_id), **metrics},
    }


def _time_to_event_discrimination_calibration_sidecar(template_id: str) -> dict[str, object]:
    discrimination_points = [{"label": "Model", "c_index": 0.81}]
    calibration_summary = [
        {
            "group_label": "Low risk",
            "group_order": 1,
            "n": 80,
            "events_5y": 5,
            "predicted_risk_5y": 0.07,
            "observed_risk_5y": 0.06,
        },
        {
            "group_label": "High risk",
            "group_order": 2,
            "n": 60,
            "events_5y": 18,
            "predicted_risk_5y": 0.28,
            "observed_risk_5y": 0.30,
        },
    ]
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("panel_label_A", "panel_label", 0.12, 0.78, 0.15, 0.82),
            _box("panel_label_B", "panel_label", 0.58, 0.78, 0.61, 0.82),
            _box("panel_left_x_axis_title", "subplot_x_axis_title", 0.18, 0.09, 0.40, 0.13),
            _box("panel_left_y_axis_title", "subplot_y_axis_title", 0.01, 0.40, 0.05, 0.62),
            _box("calibration_x_axis_title", "subplot_x_axis_title", 0.62, 0.09, 0.86, 0.13),
            _box("calibration_y_axis_title", "subplot_y_axis_title", 0.50, 0.40, 0.54, 0.62),
            _box("discrimination_marker_1", "metric_marker", 0.26, 0.58, 0.28, 0.60),
            _box("calibration_marker_predicted_1", "metric_marker", 0.66, 0.30, 0.68, 0.32),
            _box("calibration_marker_observed_1", "metric_marker", 0.68, 0.31, 0.70, 0.33),
            _box("calibration_marker_predicted_2", "metric_marker", 0.74, 0.54, 0.76, 0.56),
            _box("calibration_marker_observed_2", "metric_marker", 0.76, 0.56, 0.78, 0.58),
        ],
        "panel_boxes": [
            _box("panel_left", "panel", 0.10, 0.16, 0.44, 0.86),
            _box("panel_right", "panel", 0.56, 0.16, 0.90, 0.86),
        ],
        "guide_boxes": [_box("legend", "legend", 0.24, 0.06, 0.76, 0.13)],
        "metrics": {
            **_purpose_metrics(template_id, "time_to_event_discrimination_plus_calibration_summary"),
            "discrimination_points": discrimination_points,
            "calibration_summary": calibration_summary,
            "series": [{"label": "C-index", "x": [0.0, 1.0], "y": [0.5, 0.5]}],
            "reference_line": {"x": [0.0, 1.0], "y": [0.5, 0.5]},
        },
    }


def _survival_sidecar(template_id: str) -> dict[str, object]:
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("x_axis_title", "x_axis_title", 0.28, 0.92, 0.62, 0.97),
            _box("y_axis_title", "y_axis_title", 0.02, 0.24, 0.06, 0.74),
        ],
        "panel_boxes": [_box("panel", "panel", 0.10, 0.16, 0.74, 0.86)],
        "guide_boxes": [_box("legend", "legend", 0.80, 0.30, 0.96, 0.44)],
        "metrics": {
            **_purpose_metrics(template_id, "grouped_time_to_event_survival_curve"),
            "groups": [
                {"label": "Low risk", "times": [0.0, 12.0], "values": [1.0, 0.92]},
                {"label": "High risk", "times": [0.0, 12.0], "values": [1.0, 0.76]},
            ],
        },
    }


def _multihorizon_calibration_sidecar(template_id: str) -> dict[str, object]:
    panels = [
        {
            "panel_id": "h36",
            "panel_label": "A",
            "title": "36 months",
            "time_horizon_months": 36,
            "calibration_summary": [
                {"group_label": "Low", "group_order": 1, "n": 120, "events": 6, "predicted_risk": 0.05, "observed_risk": 0.06, "predicted_x": 0.20, "observed_x": 0.26, "y": 0.36},
                {"group_label": "High", "group_order": 2, "n": 90, "events": 24, "predicted_risk": 0.25, "observed_risk": 0.29, "predicted_x": 0.30, "observed_x": 0.36, "y": 0.56},
            ],
        },
        {
            "panel_id": "h60",
            "panel_label": "B",
            "title": "60 months",
            "time_horizon_months": 60,
            "calibration_summary": [
                {"group_label": "Low", "group_order": 1, "n": 120, "events": 8, "predicted_risk": 0.08, "observed_risk": 0.07, "predicted_x": 0.58, "observed_x": 0.64, "y": 0.36},
                {"group_label": "High", "group_order": 2, "n": 90, "events": 31, "predicted_risk": 0.34, "observed_risk": 0.32, "predicted_x": 0.68, "observed_x": 0.74, "y": 0.56},
            ],
        },
    ]
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("panel_label_A", "panel_label", 0.11, 0.82, 0.14, 0.86),
            _box("panel_label_B", "panel_label", 0.55, 0.82, 0.58, 0.86),
            _box("panel_title_A", "panel_title", 0.18, 0.10, 0.34, 0.14),
            _box("panel_title_B", "panel_title", 0.62, 0.10, 0.78, 0.14),
            _box("x_axis_title_A", "subplot_x_axis_title", 0.20, 0.90, 0.36, 0.94),
            _box("x_axis_title_B", "subplot_x_axis_title", 0.64, 0.90, 0.80, 0.94),
        ],
        "panel_boxes": [
            _box("panel_A", "calibration_panel", 0.10, 0.16, 0.44, 0.86),
            _box("panel_B", "calibration_panel", 0.54, 0.16, 0.88, 0.86),
        ],
        "guide_boxes": [_box("legend", "legend", 0.36, 0.02, 0.64, 0.08)],
        "metrics": {**_purpose_metrics(template_id, "multi_horizon_time_to_event_calibration_assessment"), "panels": panels},
    }


def _decision_curve_sidecar(template_id: str) -> dict[str, object]:
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("x_axis_title", "x_axis_title", 0.16, 0.92, 0.34, 0.97),
            _box("y_axis_title", "y_axis_title", 0.02, 0.20, 0.06, 0.72),
            _box("panel_right_x_axis_title", "subplot_x_axis_title", 0.62, 0.92, 0.80, 0.97),
            _box("panel_right_y_axis_title", "subplot_y_axis_title", 0.54, 0.20, 0.58, 0.72),
            _box("panel_label_A", "panel_label", 0.11, 0.80, 0.14, 0.85),
            _box("panel_label_B", "panel_label", 0.57, 0.80, 0.60, 0.85),
        ],
        "panel_boxes": [
            _box("panel_left", "panel", 0.10, 0.16, 0.44, 0.86),
            _box("panel_right", "panel", 0.56, 0.16, 0.90, 0.86),
        ],
        "guide_boxes": [_box("legend", "legend", 0.34, 0.02, 0.66, 0.08)],
        "metrics": {
            **_purpose_metrics(template_id, "time_to_event_net_benefit_plus_treated_fraction_summary"),
            "series": [{"label": "Model", "x": [0.05, 0.20, 0.40], "y": [0.16, 0.12, 0.06]}],
            "reference_line": {"x": [0.05, 0.40], "y": [0.0, 0.0]},
            "treated_fraction_series": {"label": "Model", "x": [0.05, 0.20, 0.40], "y": [60.0, 30.0, 12.0]},
        },
    }


def _risk_layering_sidecar(template_id: str) -> dict[str, object]:
    bars = [
        {"label": "Low", "cases": 120, "events": 4, "risk": 0.03},
        {"label": "High", "cases": 120, "events": 22, "risk": 0.18},
    ]
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("y_axis_title", "y_axis_title", 0.02, 0.20, 0.06, 0.72),
            _box("risk_bar_left_1", "risk_bar", 0.18, 0.62, 0.24, 0.78),
            _box("risk_bar_left_2", "risk_bar", 0.28, 0.42, 0.34, 0.78),
            _box("risk_bar_right_1", "risk_bar", 0.62, 0.62, 0.68, 0.78),
            _box("risk_bar_right_2", "risk_bar", 0.72, 0.38, 0.78, 0.78),
        ],
        "panel_boxes": [
            _box("panel_left", "panel", 0.10, 0.16, 0.44, 0.86),
            _box("panel_right", "panel", 0.56, 0.16, 0.90, 0.86),
        ],
        "guide_boxes": [],
        "metrics": {**_purpose_metrics(template_id, "risk_stratification_monotonicity_and_event_gradient"), "left_bars": bars, "right_bars": bars},
    }


def _time_to_event_risk_group_sidecar(template_id: str) -> dict[str, object]:
    risk_group_summaries = [
        {
            "label": "Low risk",
            "sample_size": 80,
            "events_5y": 5,
            "mean_predicted_risk_5y": 0.07,
            "observed_km_risk_5y": 0.06,
        },
        {
            "label": "High risk",
            "sample_size": 60,
            "events_5y": 18,
            "mean_predicted_risk_5y": 0.28,
            "observed_km_risk_5y": 0.30,
        },
    ]
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
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
        "panel_boxes": [
            _box("panel_left", "panel", 0.10, 0.16, 0.44, 0.86),
            _box("panel_right", "panel", 0.56, 0.16, 0.90, 0.86),
        ],
        "guide_boxes": [],
        "metrics": {
            **_purpose_metrics(template_id, "time_to_event_risk_group_gradient_plus_event_counts"),
            "risk_group_summaries": risk_group_summaries,
        },
    }

def _dpcc_phenotype_gap_sidecar(template_id: str) -> dict[str, object]:
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("panel_label_A", "panel_label", 0.08, 0.08, 0.11, 0.12),
            _box("panel_label_B", "panel_label", 0.52, 0.08, 0.55, 0.12),
            _box("composition_title", "subplot_title", 0.14, 0.08, 0.38, 0.12),
            _box("gap_title", "subplot_title", 0.58, 0.08, 0.84, 0.12),
            _box("composition_x_axis_title", "x_axis_title", 0.18, 0.90, 0.34, 0.94),
            _box("gap_x_axis_title", "x_axis_title", 0.64, 0.90, 0.80, 0.94),
            _box("colorbar_title", "colorbar_title", 0.88, 0.19, 0.94, 0.23),
        ],
        "panel_boxes": [
            _box("composition_panel", "composition_panel", 0.10, 0.18, 0.42, 0.84),
            _box("gap_heatmap_panel", "gap_heatmap_panel", 0.54, 0.18, 0.84, 0.84),
        ],
        "guide_boxes": [_box("colorbar", "colorbar", 0.88, 0.26, 0.94, 0.80)],
        "metrics": {
            "source_renderer": "MAS/DPCC::phenotype_gap_structure_figure",
            "figure_purpose": "phenotype_composition_plus_treatment_gap_matrix",
            "rendered_title_policy": "figure_title_metadata_only_not_drawn_inside_plot",
            "rows": [{"phenotype_label": "Glycemic-dominant diabetes", "share_of_index_patients": 0.34}],
            "gap_labels": ["Severe glycemia", "Uncontrolled glycemia"],
        },
    }


def _dpcc_transition_site_sidecar(template_id: str) -> dict[str, object]:
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("panel_label_A", "panel_label", 0.08, 0.08, 0.11, 0.12),
            _box("panel_label_B", "panel_label", 0.58, 0.08, 0.61, 0.12),
            _box("transition_title", "subplot_title", 0.16, 0.08, 0.42, 0.12),
            _box("site_title", "subplot_title", 0.66, 0.08, 0.90, 0.12),
            _box("transition_x_axis_title", "x_axis_title", 0.20, 0.90, 0.42, 0.94),
            _box("transition_y_axis_title", "y_axis_title", 0.02, 0.36, 0.06, 0.62),
            _box("site_x_axis_title", "x_axis_title", 0.66, 0.90, 0.84, 0.94),
            _box("site_y_axis_title", "y_axis_title", 0.50, 0.36, 0.54, 0.62),
            _box("colorbar_title", "colorbar_title", 0.90, 0.19, 0.96, 0.23),
        ],
        "panel_boxes": [
            _box("transition_heatmap_panel", "transition_heatmap_panel", 0.10, 0.18, 0.48, 0.84),
            _box("site_support_panel", "site_support_panel", 0.60, 0.18, 0.86, 0.84),
        ],
        "guide_boxes": [_box("colorbar", "colorbar", 0.90, 0.26, 0.96, 0.80)],
        "metrics": {
            "source_renderer": "MAS/DPCC::site_held_out_stability_figure",
            "figure_purpose": "phenotype_transition_stability_plus_site_held_out_support",
            "rendered_title_policy": "figure_title_metadata_only_not_drawn_inside_plot",
            "transition_rows": [
                {
                    "source_phenotype_label": "Lower-burden diabetes",
                    "target_phenotype_label": "Glycemic-dominant diabetes",
                    "patient_count": 180,
                    "share_of_transition_patients": 0.20,
                }
            ],
            "site_fold_rows": [{"fold_id": "site_fold_1", "index_patients": 320, "share_of_index_patients": 0.54}],
        },
    }


def _dpcc_treatment_gap_sidecar(template_id: str) -> dict[str, object]:
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("panel_label_A", "panel_label", 0.08, 0.08, 0.11, 0.12),
            _box("panel_label_B", "panel_label", 0.52, 0.08, 0.55, 0.12),
            _box("panel_label_C", "panel_label", 0.08, 0.50, 0.11, 0.54),
            _box("panel_label_D", "panel_label", 0.52, 0.50, 0.55, 0.54),
            _box("gap_title_A", "subplot_title", 0.14, 0.08, 0.38, 0.12),
            _box("gap_title_B", "subplot_title", 0.58, 0.08, 0.84, 0.12),
            _box("gap_title_C", "subplot_title", 0.14, 0.50, 0.38, 0.54),
            _box("gap_title_D", "subplot_title", 0.58, 0.50, 0.84, 0.54),
            _box("shared_y_axis_title", "y_axis_title", 0.02, 0.34, 0.06, 0.64),
        ],
        "panel_boxes": [
            _box("gap_count_panel_A", "gap_count_panel", 0.10, 0.16, 0.44, 0.42),
            _box("gap_count_panel_B", "gap_count_panel", 0.56, 0.16, 0.90, 0.42),
            _box("gap_count_panel_C", "gap_count_panel", 0.10, 0.58, 0.44, 0.84),
            _box("gap_count_panel_D", "gap_count_panel", 0.56, 0.58, 0.90, 0.84),
        ],
        "guide_boxes": [],
        "metrics": {
            "source_renderer": "MAS/DPCC::treatment_gap_alignment_figure",
            "figure_purpose": "guideline_linked_treatment_gap_burden_small_multiples",
            "rendered_title_policy": "figure_title_metadata_only_not_drawn_inside_plot",
            "rows": [{"phenotype_label": "Glycemic-dominant diabetes", "index_patients": 1000}],
            "panels": [
                {"gap_field": "severe_glycemia_low_intensity_gap_patients"},
                {"gap_field": "uncontrolled_glycemia_no_drug_gap_patients"},
                {"gap_field": "hypertension_no_antihypertensive_gap_patients"},
                {"gap_field": "dyslipidemia_no_lipid_lowering_gap_patients"},
            ],
        },
    }


def _forest_sidecar(template_id: str) -> dict[str, object]:
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("row_label_1", "row_label", 0.02, 0.24, 0.20, 0.30),
            _box("estimate_marker_1", "estimate_marker", 0.62, 0.25, 0.64, 0.29),
            _box("ci_segment_1", "ci_segment", 0.56, 0.27, 0.74, 0.27),
        ],
        "panel_boxes": [_box("panel", "panel", 0.28, 0.16, 0.80, 0.88)],
        "guide_boxes": [_box("reference_line", "reference_line", 0.52, 0.18, 0.52, 0.86)],
        "metrics": {"rows": [{"row_id": "1", "label": "Age >= 60", "lower": 0.90, "estimate": 1.05, "upper": 1.20}]},
    }


def _heatmap_sidecar(template_id: str, *, confusion: bool = False) -> dict[str, object]:
    metrics: dict[str, object] = {"matrix_cells": [{"x": "A", "y": "A", "value": 0.85}]}
    if confusion:
        metrics = {
            "metric_name": "Observed proportion",
            "normalization": "row_fraction",
            "matrix_cells": [
                {"x": "Predicted negative", "y": "Observed negative", "value": 0.88},
                {"x": "Predicted positive", "y": "Observed negative", "value": 0.12},
                {"x": "Predicted negative", "y": "Observed positive", "value": 0.19},
                {"x": "Predicted positive", "y": "Observed positive", "value": 0.81},
            ],
        }
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("x_axis_title", "x_axis_title", 0.28, 0.92, 0.60, 0.97),
            _box("y_axis_title", "y_axis_title", 0.02, 0.24, 0.06, 0.74),
        ],
        "panel_boxes": [_box("panel", "heatmap_tile_region", 0.12, 0.16, 0.72, 0.84)],
        "guide_boxes": [_box("colorbar", "colorbar", 0.80, 0.22, 0.90, 0.80)],
        "metrics": metrics,
    }


def _embedding_sidecar(template_id: str) -> dict[str, object]:
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [
            _box("x_axis_title", "x_axis_title", 0.30, 0.92, 0.60, 0.97),
            _box("y_axis_title", "y_axis_title", 0.02, 0.24, 0.06, 0.74),
        ],
        "panel_boxes": [_box("panel", "panel", 0.10, 0.16, 0.74, 0.86)],
        "guide_boxes": [_box("legend", "legend", 0.80, 0.30, 0.96, 0.44)],
        "metrics": {"points": [{"x": 0.22, "y": 0.32, "group": "A"}, {"x": 0.44, "y": 0.54, "group": "B"}]},
    }


def _simple_panel_sidecar(template_id: str, *, box_type: str = "panel") -> dict[str, object]:
    return {
        **_base_sidecar(template_id),
        "layout_boxes": [_box("x_axis_title", "x_axis_title", 0.28, 0.92, 0.62, 0.97)],
        "panel_boxes": [_box("panel", box_type, 0.14, 0.18, 0.78, 0.84)],
        "guide_boxes": [_box("legend", "legend", 0.82, 0.20, 0.96, 0.36), _box("colorbar", "colorbar", 0.82, 0.44, 0.92, 0.76)],
        "metrics": {},
    }


def minimal_current_layout_sidecar(template_id: str) -> dict[str, object] | None:
    short_id = get_template_short_id(template_id) if "::" in template_id else template_id
    try:
        display_registry.get_evidence_figure_spec(short_id)
    except (KeyError, ValueError):
        return None

    if short_id == "time_to_event_discrimination_calibration_panel":
        return _time_to_event_discrimination_calibration_sidecar(template_id)
    if short_id == "time_to_event_risk_group_summary":
        return _time_to_event_risk_group_sidecar(template_id)
    if short_id in {"roc_curve_binary", "pr_curve_binary", "calibration_curve_binary", "decision_curve_binary"}:
        return _curve_sidecar(template_id)
    if short_id == "time_dependent_roc_horizon":
        if template_id.endswith("::time_to_event_discrimination_calibration_panel"):
            sidecar = _curve_sidecar(template_id, time_dependent=True)
            sidecar["metrics"].update(
                _purpose_metrics(template_id, "time_to_event_discrimination_plus_calibration_summary")
            )
            return sidecar
        return _curve_sidecar(template_id, time_dependent=True)
    if short_id in {"kaplan_meier_grouped", "cumulative_incidence_grouped"}:
        return _survival_sidecar(template_id)
    if short_id == "time_to_event_multihorizon_calibration_panel":
        return _multihorizon_calibration_sidecar(template_id)
    if short_id == "time_to_event_decision_curve":
        return _decision_curve_sidecar(template_id)
    if short_id == "risk_layering_monotonic_bars":
        if template_id.endswith("::time_to_event_risk_group_summary"):
            sidecar = _risk_layering_sidecar(template_id)
            sidecar["metrics"].update(
                _purpose_metrics(template_id, "time_to_event_risk_group_gradient_plus_event_counts")
            )
            return sidecar
        return _risk_layering_sidecar(template_id)
    if short_id == "phenotype_gap_structure_figure":
        return _dpcc_phenotype_gap_sidecar(template_id)
    if short_id == "site_held_out_stability_figure":
        return _dpcc_transition_site_sidecar(template_id)
    if short_id == "treatment_gap_alignment_figure":
        return _dpcc_treatment_gap_sidecar(template_id)
    if short_id == "forest_effect_main":
        return _forest_sidecar(template_id)
    if short_id in {"pca_scatter_grouped", "tsne_scatter_grouped", "umap_scatter_grouped"}:
        return _embedding_sidecar(template_id)
    if short_id == "heatmap_group_comparison":
        return _heatmap_sidecar(template_id)
    if short_id == "confusion_matrix_heatmap_binary":
        return _heatmap_sidecar(template_id, confusion=True)
    if short_id in {
        "coefficient_path_panel",
        "genomic_alteration_landscape_panel",
        "cnv_recurrence_summary_panel",
        "genomic_alteration_consequence_panel",
        "pathway_enrichment_dotplot_panel",
        "celltype_marker_dotplot_panel",
        "omics_volcano_panel",
        "shap_dependence_panel",
        "shap_waterfall_local_explanation_panel",
        "model_complexity_audit_panel",
    }:
        return _simple_panel_sidecar(template_id)
    return None


__all__ = ["minimal_current_layout_sidecar"]
