from __future__ import annotations

from .shared import *


@pytest.mark.parametrize(
    "qc_profile",
    [
        "publication_baseline_missingness_qc_panel",
        "publication_center_coverage_batch_transportability_panel",
        "publication_transportability_recalibration_governance_panel",
        "publication_center_transportability_governance_summary_panel",
    ],
)
def test_run_display_layout_qc_rejects_retired_python_data_shell_profiles(qc_profile: str) -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    with pytest.raises(ValueError, match="unsupported qc_profile"):
        module.run_display_layout_qc(
            qc_profile=qc_profile,
            layout_sidecar={
                "template_id": "retired_python_data_shell",
                "device": make_device(),
                "layout_boxes": [],
                "panel_boxes": [],
                "guide_boxes": [],
                "metrics": {},
            },
        )


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


def test_run_display_layout_qc_checks_grouped_risk_order_within_each_cohort() -> None:
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
                        "label": "China Q1 low",
                        "cohort_id": "china",
                        "sample_size": 3948,
                        "events_5y": 16,
                        "mean_predicted_risk_5y": 0.0157,
                        "observed_km_risk_5y": 0.0041,
                    },
                    {
                        "label": "China Q2",
                        "cohort_id": "china",
                        "sample_size": 3947,
                        "events_5y": 39,
                        "mean_predicted_risk_5y": 0.0184,
                        "observed_km_risk_5y": 0.0099,
                    },
                    {
                        "label": "China Q3",
                        "cohort_id": "china",
                        "sample_size": 3947,
                        "events_5y": 67,
                        "mean_predicted_risk_5y": 0.0204,
                        "observed_km_risk_5y": 0.017,
                    },
                    {
                        "label": "China Q4 high",
                        "cohort_id": "china",
                        "sample_size": 3947,
                        "events_5y": 199,
                        "mean_predicted_risk_5y": 0.0239,
                        "observed_km_risk_5y": 0.0504,
                    },
                    {
                        "label": "NHANES Q1 low",
                        "cohort_id": "nhanes",
                        "sample_size": 5659,
                        "events_5y": 704,
                        "mean_predicted_risk_5y": 0.0011,
                        "observed_km_risk_5y": 0.1244,
                    },
                ],
            },
            "render_context": {"readability_override": {}},
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


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
