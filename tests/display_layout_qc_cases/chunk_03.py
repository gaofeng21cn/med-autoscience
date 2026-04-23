from .shared import *

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

def test_run_display_layout_qc_fails_when_confusion_matrix_row_fraction_does_not_sum_to_one() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_heatmap",
        layout_sidecar={
            "template_id": "confusion_matrix_heatmap_binary",
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
                "metric_name": "Observed proportion",
                "normalization": "row_fraction",
                "matrix_cells": [
                    {"x": "Predicted negative", "y": "Observed negative", "value": 0.81},
                    {"x": "Predicted positive", "y": "Observed negative", "value": 0.12},
                    {"x": "Predicted negative", "y": "Observed positive", "value": 0.21},
                    {"x": "Predicted positive", "y": "Observed positive", "value": 0.83},
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "confusion_row_sum_invalid" for issue in result["issues"])

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
