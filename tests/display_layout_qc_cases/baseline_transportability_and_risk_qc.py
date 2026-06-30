from __future__ import annotations

from .shared import *


@pytest.mark.parametrize(
    "qc_profile",
    [
        "publication_baseline_missingness_qc_panel",
        "publication_center_coverage_batch_transportability_panel",
        "publication_transportability_recalibration_governance_panel",
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


def _center_transportability_governance_sidecar(
    *,
    missing_governance_metric: bool = False,
    governance_metric_outside_panel: bool = False,
    legacy_decision_cells_only: bool = False,
    legacy_card_only: bool = False,
) -> dict[str, object]:
    governance_marks = [
        make_box("china_slope_marker", "calibration_governance_metric", x0=0.65, y0=0.30, x1=0.68, y1=0.34),
        make_box("china_oe_marker", "calibration_governance_metric", x0=0.80, y0=0.30, x1=0.83, y1=0.34),
        make_box("nhanes_slope_marker", "calibration_governance_metric", x0=0.60, y0=0.58, x1=0.63, y1=0.62),
        make_box("nhanes_oe_marker", "calibration_governance_metric", x0=0.90, y0=0.58, x1=0.93, y1=0.62),
        make_box("calibration_reference_line", "calibration_reference_line", x0=0.74, y0=0.24, x1=0.745, y1=0.78),
        make_box("calibration_acceptance_band", "calibration_acceptance_band", x0=0.66, y0=0.24, x1=0.82, y1=0.78),
    ]
    if missing_governance_metric:
        governance_marks = governance_marks[:-3]
    if governance_metric_outside_panel:
        governance_marks[3] = make_box(
            "nhanes_oe_marker",
            "calibration_governance_metric",
            x0=0.47,
            y0=0.61,
            x1=0.49,
            y1=0.64,
        )
    if legacy_decision_cells_only:
        governance_marks = [
            make_box("china_cohort_cell", "governance_decision_cell", x0=0.60, y0=0.30, x1=0.68, y1=0.38),
            make_box("china_calibration_cell", "governance_decision_cell", x0=0.70, y0=0.30, x1=0.82, y1=0.38),
            make_box("china_action_cell", "governance_decision_cell", x0=0.84, y0=0.30, x1=0.92, y1=0.38),
            make_box("nhanes_cohort_cell", "governance_decision_cell", x0=0.60, y0=0.58, x1=0.68, y1=0.66),
            make_box("nhanes_calibration_cell", "governance_decision_cell", x0=0.70, y0=0.58, x1=0.82, y1=0.66),
            make_box("nhanes_action_cell", "governance_decision_cell", x0=0.84, y0=0.58, x1=0.92, y1=0.66),
        ]
    if legacy_card_only:
        governance_marks = [
            make_box("governance_card_1", "governance_card", x0=0.60, y0=0.28, x1=0.90, y1=0.45),
            make_box("governance_card_2", "governance_card", x0=0.60, y0=0.57, x1=0.90, y1=0.74),
        ]
    return {
        "template_id": "center_transportability_governance_summary_panel",
        "device": make_device(),
        "layout_boxes": [
            make_box("panel_label_A", "panel_label", x0=0.10, y0=0.77, x1=0.13, y1=0.81),
            make_box("panel_label_B", "panel_label", x0=0.58, y0=0.77, x1=0.61, y1=0.81),
            make_box("panel_left_title", "panel_title", x0=0.15, y0=0.86, x1=0.42, y1=0.90),
            make_box("panel_right_title", "panel_title", x0=0.63, y0=0.86, x1=0.90, y1=0.90),
            make_box("metric_x_axis_title", "subplot_x_axis_title", x0=0.18, y0=0.09, x1=0.40, y1=0.13),
            make_box("center_marker_1", "metric_marker", x0=0.26, y0=0.37, x1=0.28, y1=0.39),
            make_box("center_marker_2", "metric_marker", x0=0.26, y0=0.62, x1=0.28, y1=0.64),
            *governance_marks,
        ],
        "panel_boxes": [
            make_box("panel_left", "metric_panel", x0=0.08, y0=0.20, x1=0.46, y1=0.82),
            make_box("panel_right", "governance_decision_panel", x0=0.56, y0=0.20, x1=0.94, y1=0.82),
        ],
        "guide_boxes": [
            make_box("legend", "legend", x0=0.24, y0=0.06, x1=0.76, y1=0.13),
        ],
        "metrics": {
            "figure_purpose": "transportability_discrimination_plus_recalibration_governance_decision_matrix",
            "rendered_title_policy": "figure_title_metadata_only_not_drawn_inside_plot",
            "governance_visual_encoding_policy": "numeric_calibration_markers_with_reference_and_acceptance_band",
            "centers": [
                {"center_label": "China", "metric_estimate": 0.76, "slope": 1.0, "oe_ratio": 1.0},
                {"center_label": "NHANES", "metric_estimate": 0.73, "slope": 0.01, "oe_ratio": 5.33},
            ],
            "metric_reference_value": 0.76,
            "slope_acceptance": {"lower": 0.90, "upper": 1.10},
            "oe_ratio_acceptance": {"lower": 0.90, "upper": 1.10},
        },
        "render_context": {"layout_override": {}},
    }


def test_run_display_layout_qc_passes_for_center_transportability_governance_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_center_transportability_governance_summary_panel",
        layout_sidecar=_center_transportability_governance_sidecar(),
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_without_calibration_governance_metrics() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_center_transportability_governance_summary_panel",
        layout_sidecar=_center_transportability_governance_sidecar(missing_governance_metric=True),
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "calibration_governance_metric_count_incomplete" for issue in result["issues"])


def test_run_display_layout_qc_rejects_legacy_governance_cards_as_center_transportability_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_center_transportability_governance_summary_panel",
        layout_sidecar=_center_transportability_governance_sidecar(legacy_card_only=True),
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "retired_governance_text_cells_present" for issue in result["issues"])


def test_run_display_layout_qc_rejects_legacy_decision_cells_as_center_transportability_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_center_transportability_governance_summary_panel",
        layout_sidecar=_center_transportability_governance_sidecar(legacy_decision_cells_only=True),
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "retired_governance_text_cells_present" for issue in result["issues"])


def test_run_display_layout_qc_fails_when_calibration_governance_metric_leaves_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_center_transportability_governance_summary_panel",
        layout_sidecar=_center_transportability_governance_sidecar(governance_metric_outside_panel=True),
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "calibration_governance_metric_outside_panel" for issue in result["issues"])


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
