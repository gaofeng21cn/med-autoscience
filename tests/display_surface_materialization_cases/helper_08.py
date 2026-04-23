from __future__ import annotations

from . import shared_base as _shared_base
from . import helper_07 as _helper_prev

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_helper_prev)

def _make_center_transportability_governance_summary_panel_display(
    display_id: str = "Figure50",
) -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "center_transportability_governance_summary_panel",
        "title": "Center transportability governance summary for manuscript-facing multicenter review",
        "caption": (
            "Bounded center-level generalizability evidence aligns per-center performance, support counts, shift "
            "severity, recalibration diagnostics, and manuscript-facing governance verdicts in one auditable summary."
        ),
        "metric_family": "discrimination",
        "metric_panel_title": "Center-level discrimination",
        "metric_x_label": "AUROC",
        "metric_reference_value": 0.80,
        "batch_shift_threshold": 0.20,
        "slope_acceptance_lower": 0.90,
        "slope_acceptance_upper": 1.10,
        "oe_ratio_acceptance_lower": 0.90,
        "oe_ratio_acceptance_upper": 1.10,
        "summary_panel_title": "Transportability governance summary",
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
                "detail": "Internal validation remains inside the acceptance band.",
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
            },
        ],
    }

def _make_time_to_event_threshold_governance_panel_display(display_id: str = "Figure29") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_to_event_threshold_governance_panel",
        "title": "Time-to-event threshold governance panel for deployment-facing operating review",
        "caption": (
            "Structured threshold summary and grouped calibration governance lock the manuscript-facing operating "
            "threshold discussion to explicit audited inputs."
        ),
        "threshold_panel_title": "Operating thresholds",
        "calibration_panel_title": "Grouped calibration at 5 years",
        "calibration_x_label": "Predicted / observed 5-year risk",
        "threshold_summaries": [
            {
                "threshold_label": "Rule-in",
                "threshold": 0.10,
                "sensitivity": 0.88,
                "specificity": 0.52,
                "net_benefit": 0.041,
            },
            {
                "threshold_label": "Actionable",
                "threshold": 0.15,
                "sensitivity": 0.74,
                "specificity": 0.67,
                "net_benefit": 0.058,
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
            },
            {
                "group_label": "Intermediate risk",
                "group_order": 2,
                "n": 146,
                "events": 19,
                "predicted_risk": 0.13,
                "observed_risk": 0.15,
            },
            {
                "group_label": "High risk",
                "group_order": 3,
                "n": 88,
                "events": 27,
                "predicted_risk": 0.31,
                "observed_risk": 0.29,
            },
        ],
    }

def _make_time_to_event_multihorizon_calibration_panel_display(display_id: str = "Figure30") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_to_event_multihorizon_calibration_panel",
        "title": "Multi-horizon grouped survival calibration governance",
        "caption": (
            "Prespecified grouped calibration at 36 and 60 months is locked to explicit audited panel contracts "
            "instead of manuscript-local freehand composition."
        ),
        "x_label": "Predicted / observed risk",
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
                    },
                    {
                        "group_label": "Intermediate risk",
                        "group_order": 2,
                        "n": 146,
                        "events": 13,
                        "predicted_risk": 0.11,
                        "observed_risk": 0.13,
                    },
                    {
                        "group_label": "High risk",
                        "group_order": 3,
                        "n": 88,
                        "events": 22,
                        "predicted_risk": 0.24,
                        "observed_risk": 0.27,
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
                    },
                    {
                        "group_label": "Intermediate risk",
                        "group_order": 2,
                        "n": 146,
                        "events": 19,
                        "predicted_risk": 0.13,
                        "observed_risk": 0.15,
                    },
                    {
                        "group_label": "High risk",
                        "group_order": 3,
                        "n": 88,
                        "events": 27,
                        "predicted_risk": 0.31,
                        "observed_risk": 0.29,
                    },
                ],
            },
        ],
    }
