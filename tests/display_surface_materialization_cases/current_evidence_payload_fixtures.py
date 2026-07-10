from __future__ import annotations

from typing import Any


PACK_ID = "fenggaolab.org.medical-display-core"


def _full(template_id: str) -> str:
    return f"{PACK_ID}::{template_id}"


def _curve_display(
    display_id: str,
    template_id: str,
    *,
    x_label: str,
    y_label: str,
) -> dict[str, Any]:
    return {
        "display_id": display_id,
        "template_id": _full(template_id),
        "title": f"Representative {template_id}",
        "caption": "Sparse integration fixture for the materialization boundary.",
        "x_label": x_label,
        "y_label": y_label,
        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Reference"},
        "series": [{"label": "Primary model", "x": [0.0, 0.5, 1.0], "y": [0.0, 0.8, 1.0]}],
    }


def _binary_prediction_curve_displays() -> list[dict[str, Any]]:
    return [
        _curve_display("Figure2", "roc_curve_binary", x_label="1 - Specificity", y_label="Sensitivity"),
        _curve_display("Figure3", "pr_curve_binary", x_label="Recall", y_label="Precision"),
        _curve_display(
            "Figure4",
            "calibration_curve_binary",
            x_label="Predicted probability",
            y_label="Observed event rate",
        ),
        _curve_display(
            "Figure5",
            "decision_curve_binary",
            x_label="Threshold probability",
            y_label="Net benefit",
        ),
    ]


def _kaplan_meier_display() -> dict[str, Any]:
    return {
        "display_id": "Figure6",
        "template_id": _full("kaplan_meier_grouped"),
        "title": "Representative Kaplan-Meier risk stratification",
        "caption": "Sparse grouped survival integration fixture.",
        "x_label": "Months from surgery",
        "y_label": "Survival probability",
        "groups": [
            {"label": "Low risk", "times": [0, 12, 24], "values": [1.0, 0.93, 0.88]},
            {"label": "High risk", "times": [0, 12, 24], "values": [1.0, 0.77, 0.62]},
        ],
    }


def _generalizability_display() -> dict[str, Any]:
    return {
        "display_id": "Figure7",
        "template_id": _full("generalizability_subgroup_composite_panel"),
        "title": "Representative generalizability summary",
        "caption": "Sparse external validation and subgroup fixture.",
        "metric_family": "discrimination",
        "primary_label": "Locked model",
        "comparator_label": "Derivation cohort",
        "overview_panel_title": "External cohort discrimination",
        "overview_x_label": "AUROC",
        "overview_rows": [
            {
                "cohort_id": "external",
                "cohort_label": "External cohort",
                "support_count": 184,
                "event_count": 29,
                "metric_value": 0.82,
                "comparator_metric_value": 0.79,
            }
        ],
        "subgroup_panel_title": "Prespecified subgroup stability",
        "subgroup_x_label": "AUROC",
        "subgroup_reference_value": 0.80,
        "subgroup_rows": [
            {
                "subgroup_id": "age_ge_65",
                "subgroup_label": "Age >=65 years",
                "group_n": 201,
                "estimate": 0.82,
                "lower": 0.78,
                "upper": 0.86,
            }
        ],
    }


def _current_evidence_input_envelopes() -> dict[str, dict[str, Any]]:
    return {
        "binary_prediction_curve_inputs.json": {
            "schema_version": 1,
            "input_schema_id": "binary_prediction_curve_inputs_v1",
            "displays": _binary_prediction_curve_displays(),
        },
        "time_to_event_grouped_inputs.json": {
            "schema_version": 1,
            "input_schema_id": "time_to_event_grouped_inputs_v1",
            "displays": [_kaplan_meier_display()],
        },
        "generalizability_subgroup_composite_inputs.json": {
            "schema_version": 1,
            "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
            "displays": [_generalizability_display()],
        },
    }


__all__ = ["_current_evidence_input_envelopes"]
