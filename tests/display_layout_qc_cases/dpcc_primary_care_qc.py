from .shared import *

def test_run_display_layout_qc_passes_for_interaction_effect_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_interaction_effect_summary_panel",
        layout_sidecar={
            "template_id": "interaction_effect_summary_panel",
            "render_context": {"layout_override": {"show_figure_title": False}},
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.18, y0=0.86, x1=0.43, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.73, y0=0.86, x1=0.91, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.18, y0=0.77, x1=0.20, y1=0.80),
                make_box("panel_label_B", "panel_label", x0=0.73, y0=0.77, x1=0.75, y1=0.80),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.31, y0=0.11, x1=0.49, y1=0.14),
                make_box("modifier_label_age", "row_label", x0=0.05, y0=0.61, x1=0.17, y1=0.65),
                make_box("modifier_label_female", "row_label", x0=0.08, y0=0.46, x1=0.17, y1=0.50),
                make_box("estimate_age", "estimate_marker", x0=0.37, y0=0.61, x1=0.38, y1=0.65),
                make_box("estimate_female", "estimate_marker", x0=0.44, y0=0.46, x1=0.45, y1=0.50),
                make_box("ci_age", "ci_segment", x0=0.31, y0=0.625, x1=0.43, y1=0.635),
                make_box("ci_female", "ci_segment", x0=0.38, y0=0.475, x1=0.50, y1=0.485),
                make_box("verdict_age", "verdict_value", x0=0.76, y0=0.62, x1=0.87, y1=0.66),
                make_box("detail_age", "verdict_detail", x0=0.76, y0=0.57, x1=0.92, y1=0.61),
                make_box("verdict_female", "verdict_value", x0=0.76, y0=0.47, x1=0.89, y1=0.51),
                make_box("detail_female", "verdict_detail", x0=0.76, y0=0.42, x1=0.93, y1=0.46),
            ],
            "panel_boxes": [
                make_box("estimate_panel", "panel", x0=0.18, y0=0.22, x1=0.66, y1=0.80),
                make_box("summary_panel", "panel", x0=0.73, y0=0.22, x1=0.94, y1=0.80),
            ],
            "guide_boxes": [
                make_box("reference_line", "reference_line", x0=0.34, y0=0.22, x1=0.35, y1=0.80),
            ],
            "metrics": {
                "reference_value": 0.0,
                "estimate_panel": {
                    "panel_box_id": "estimate_panel",
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
                "modifiers": [
                    {
                        "modifier_id": "age_ge_65",
                        "modifier_label": "Age ≥65 years",
                        "interaction_estimate": 0.18,
                        "lower": 0.05,
                        "upper": 0.31,
                        "support_n": 184,
                        "favored_group_label": "Stronger in age ≥65 years",
                        "interaction_p_value": 0.014,
                        "verdict": "credible",
                        "detail": "Stronger in age ≥65 years; Pinteraction=0.014",
                        "label_box_id": "modifier_label_age",
                        "marker_box_id": "estimate_age",
                        "interval_box_id": "ci_age",
                        "verdict_box_id": "verdict_age",
                        "detail_box_id": "detail_age",
                    },
                    {
                        "modifier_id": "female",
                        "modifier_label": "Female",
                        "interaction_estimate": 0.09,
                        "lower": -0.02,
                        "upper": 0.20,
                        "support_n": 201,
                        "favored_group_label": "More pronounced in female patients",
                        "interaction_p_value": 0.081,
                        "verdict": "suggestive",
                        "detail": "More pronounced in female patients; Pinteraction=0.081",
                        "label_box_id": "modifier_label_female",
                        "marker_box_id": "estimate_female",
                        "interval_box_id": "ci_female",
                        "verdict_box_id": "verdict_female",
                        "detail_box_id": "detail_female",
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_interaction_verdict_leaves_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_interaction_effect_summary_panel",
        layout_sidecar={
            "template_id": "interaction_effect_summary_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.18, y0=0.86, x1=0.43, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.73, y0=0.86, x1=0.91, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.18, y0=0.77, x1=0.20, y1=0.80),
                make_box("panel_label_B", "panel_label", x0=0.73, y0=0.77, x1=0.75, y1=0.80),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.31, y0=0.11, x1=0.49, y1=0.14),
                make_box("modifier_label_age", "row_label", x0=0.05, y0=0.61, x1=0.17, y1=0.65),
                make_box("estimate_age", "estimate_marker", x0=0.37, y0=0.61, x1=0.38, y1=0.65),
                make_box("ci_age", "ci_segment", x0=0.31, y0=0.625, x1=0.43, y1=0.635),
                make_box("verdict_age", "verdict_value", x0=0.95, y0=0.62, x1=0.99, y1=0.66),
                make_box("detail_age", "verdict_detail", x0=0.76, y0=0.57, x1=0.92, y1=0.61),
            ],
            "panel_boxes": [
                make_box("estimate_panel", "panel", x0=0.18, y0=0.22, x1=0.66, y1=0.80),
                make_box("summary_panel", "panel", x0=0.73, y0=0.22, x1=0.94, y1=0.80),
            ],
            "guide_boxes": [
                make_box("reference_line", "reference_line", x0=0.34, y0=0.22, x1=0.35, y1=0.80),
            ],
            "metrics": {
                "reference_value": 0.0,
                "estimate_panel": {
                    "panel_box_id": "estimate_panel",
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
                "modifiers": [
                    {
                        "modifier_id": "age_ge_65",
                        "modifier_label": "Age ≥65 years",
                        "interaction_estimate": 0.18,
                        "lower": 0.05,
                        "upper": 0.31,
                        "support_n": 184,
                        "favored_group_label": "Stronger in age ≥65 years",
                        "interaction_p_value": 0.014,
                        "verdict": "credible",
                        "detail": "Stronger in age ≥65 years; Pinteraction=0.014",
                        "label_box_id": "modifier_label_age",
                        "marker_box_id": "estimate_age",
                        "interval_box_id": "ci_age",
                        "verdict_box_id": "verdict_age",
                        "detail_box_id": "detail_age",
                    }
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "interaction_verdict_outside_summary_panel" for issue in result["issues"])

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
