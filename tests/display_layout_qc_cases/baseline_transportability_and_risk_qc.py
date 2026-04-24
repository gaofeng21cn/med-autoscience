from .shared import *

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
