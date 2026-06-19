from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from med_autoscience import display_registry

from .shared import _load_json, _load_markdown_table, _parse_float, _parse_int, _write_json


TRANSPORTABILITY_LAYOUT_RELATIVE_ROOT = Path("analysis") / "clean_room_execution" / "20_transportability"


def current_transportability_layout_available(*, study_root: Path) -> bool:
    root = Path(study_root) / TRANSPORTABILITY_LAYOUT_RELATIVE_ROOT
    return (
        (root / "metrics_summary.json").exists()
        and (root / "discrimination_report.md").exists()
        and (root / "risk_group_composition_report.md").exists()
    )


def _require_mapping(payload: dict[str, Any], key: str, *, context: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{context} requires non-empty `{key}` metrics")
    return value


def _require_finite_number(payload: dict[str, Any], key: str, *, context: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{context} requires finite numeric `{key}`")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{context} requires finite numeric `{key}`")
    return number


def _require_probability(payload: dict[str, Any], key: str, *, context: str) -> float:
    number = _require_finite_number(payload, key, context=context)
    if number < 0.0 or number > 1.0:
        raise ValueError(f"{context} requires probability `{key}` between 0 and 1")
    return number


def _event_count_from_rate(*, support_count: int, rate: float) -> int:
    return max(0, min(support_count, int(round(support_count * rate))))


def _build_transportability_discrimination_payload(
    *,
    metrics_payload: dict[str, Any],
    display_id: str,
) -> dict[str, Any]:
    context = "current transportability discrimination/calibration layout"
    discrimination = _require_mapping(metrics_payload, "discrimination", context=context)
    calibration = _require_mapping(metrics_payload, "calibration_drift", context=context)
    china_n = _parse_int(discrimination.get("china_n"), label="china_n")
    nhanes_n = _parse_int(discrimination.get("nhanes_n"), label="nhanes_n")
    if china_n <= 0 or nhanes_n <= 0:
        raise ValueError(f"{context} requires positive cohort sizes")
    china_c = _require_probability(discrimination, "china_c_index", context=context)
    nhanes_c = _require_probability(discrimination, "nhanes_c_index", context=context)
    china_predicted = _require_probability(calibration, "china_predicted_mean_5y_risk", context=context)
    nhanes_predicted = _require_probability(calibration, "nhanes_predicted_mean_5y_risk", context=context)
    china_observed = _require_probability(calibration, "china_observed_5y_rate", context=context)
    nhanes_observed = _require_probability(calibration, "nhanes_observed_5y_rate", context=context)
    calibration_summary = [
        {
            "group_label": "China development cohort",
            "group_order": 1,
            "n": china_n,
            "events_5y": _event_count_from_rate(support_count=china_n, rate=china_observed),
            "predicted_risk_5y": china_predicted,
            "observed_risk_5y": china_observed,
        },
        {
            "group_label": "NHANES external cohort",
            "group_order": 2,
            "n": nhanes_n,
            "events_5y": _event_count_from_rate(support_count=nhanes_n, rate=nhanes_observed),
            "predicted_risk_5y": nhanes_predicted,
            "observed_risk_5y": nhanes_observed,
        },
    ]
    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
        "source_contract_path": "paper/medical_reporting_contract.json",
        "status": "materialized_from_current_transportability_layout",
        "displays": [
            {
                "display_id": display_id,
                "template_id": display_registry.get_evidence_figure_spec(
                    "time_to_event_discrimination_calibration_panel"
                ).template_id,
                "title": "External discrimination and cohort-level calibration",
                "caption": (
                    "Discrimination and cohort-level 5-year mortality calibration for the China-derived "
                    "score in the China and NHANES analysis cohorts."
                ),
                "paper_role": "main_text",
                "panel_a_title": "Discrimination",
                "panel_b_title": "Observed versus predicted 5-year risk",
                "discrimination_x_label": "C-index",
                "calibration_x_label": "Analysis cohort",
                "calibration_y_label": "5-year mortality risk",
                "discrimination_points": [
                    {"label": "China", "c_index": china_c, "annotation": "Development cohort"},
                    {"label": "NHANES", "c_index": nhanes_c, "annotation": "External cohort"},
                ],
                "calibration_summary": calibration_summary,
                "calibration_callout": calibration_summary[-1],
            }
        ],
    }


def _normalize_risk_group_label(cohort: str, risk_group: str) -> str:
    normalized_group = risk_group.strip().replace("_", " ")
    if not normalized_group:
        raise ValueError("risk_group_composition_report.md contains an empty risk_group label")
    return f"{cohort.strip()} {normalized_group}"


def _normalize_cohort_id(cohort: str) -> str:
    normalized = "_".join(cohort.strip().casefold().split())
    if not normalized:
        raise ValueError("risk_group_composition_report.md contains an empty cohort label")
    return normalized


def _risk_group_rows_from_report(path: Path) -> list[dict[str, Any]]:
    header, rows = _load_markdown_table(path)
    normalized_header = {value.strip().casefold(): index for index, value in enumerate(header)}
    required = {"cohort", "risk_group", "n", "observed_5y_event_rate", "predicted_mean_5y_risk"}
    missing = required - set(normalized_header)
    if missing:
        raise ValueError(f"missing required risk_group_composition_report columns in {path}: {', '.join(sorted(missing))}")
    summaries: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        if len(row) != len(header):
            raise ValueError(f"risk_group_composition_report row length mismatch in {path} at row {row_index + 1}")
        cohort = row[normalized_header["cohort"]].strip()
        if not cohort:
            raise ValueError(f"risk_group_composition_report row {row_index + 1} is missing cohort")
        sample_size = _parse_int(row[normalized_header["n"]], label=f"{path.name} row {row_index + 1} n")
        if sample_size < 0:
            raise ValueError(f"{path.name} row {row_index + 1} n must be non-negative")
        if sample_size == 0:
            continue
        observed_rate = _parse_float(
            row[normalized_header["observed_5y_event_rate"]],
            label=f"{path.name} row {row_index + 1} observed_5y_event_rate",
        )
        predicted_rate = _parse_float(
            row[normalized_header["predicted_mean_5y_risk"]],
            label=f"{path.name} row {row_index + 1} predicted_mean_5y_risk",
        )
        if not math.isfinite(observed_rate) or not math.isfinite(predicted_rate):
            raise ValueError(f"{path.name} row {row_index + 1} requires finite observed and predicted risks")
        if observed_rate < 0.0 or predicted_rate < 0.0:
            raise ValueError(f"{path.name} row {row_index + 1} risks must be non-negative")
        risk_group = row[normalized_header["risk_group"]].strip()
        summaries.append(
            {
                "label": _normalize_risk_group_label(cohort, risk_group),
                "cohort_id": _normalize_cohort_id(cohort),
                "cohort_label": cohort,
                "risk_group_label": risk_group,
                "sample_size": sample_size,
                "events_5y": _event_count_from_rate(support_count=sample_size, rate=observed_rate),
                "mean_predicted_risk_5y": predicted_rate,
                "observed_km_risk_5y": observed_rate,
            }
        )
    if not summaries:
        raise ValueError(f"{path} contains no occupied risk-group rows")
    return summaries


def _build_transportability_risk_group_payload(
    *,
    risk_group_report_path: Path,
    display_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_grouped_inputs_v1",
        "source_contract_path": "paper/medical_reporting_contract.json",
        "status": "materialized_from_current_transportability_layout",
        "displays": [
            {
                "display_id": display_id,
                "template_id": display_registry.get_evidence_figure_spec(
                    "time_to_event_risk_group_summary"
                ).template_id,
                "title": "Transported 5-year mortality risk-group summary",
                "caption": (
                    "Observed and predicted 5-year mortality risk across China-derived risk groups "
                    "in the China and NHANES analysis cohorts."
                ),
                "paper_role": "main_text",
                "panel_a_title": "Predicted and observed risk",
                "panel_b_title": "Observed events by group",
                "x_label": "China-derived risk group",
                "y_label": "5-year mortality risk",
                "event_count_y_label": "Observed 5-year events",
                "risk_group_summaries": _risk_group_rows_from_report(risk_group_report_path),
            }
        ],
    }


def _positive_ratio(numerator: float, denominator: float, *, label: str) -> float:
    if denominator <= 0.0:
        raise ValueError(f"{label} requires a positive denominator")
    ratio = numerator / denominator
    if not math.isfinite(ratio) or ratio <= 0.0:
        raise ValueError(f"{label} requires a positive finite ratio")
    return ratio


def _risk_delta_to_batch_value(delta: float) -> float:
    return max(0.0, min(1.0, abs(float(delta))))


def _transportability_batch_grid(
    *,
    calibration_shift: float,
    risk_separation_shift: float,
    observed_rate_shift: float,
) -> list[dict[str, Any]]:
    rows = ("China", "NHANES")
    columns = (
        ("Calibration drift", 0.0, calibration_shift),
        ("Risk-group support", 0.0, risk_separation_shift),
        ("Absolute-risk shift", 0.0, observed_rate_shift),
    )
    cells: list[dict[str, Any]] = []
    for column_label, china_value, nhanes_value in columns:
        cells.append({"x": column_label, "y": rows[0], "value": _risk_delta_to_batch_value(china_value)})
        cells.append({"x": column_label, "y": rows[1], "value": _risk_delta_to_batch_value(nhanes_value)})
    return cells


def _build_transportability_governance_payload(
    *,
    metrics_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
) -> dict[str, Any]:
    context = "current transportability governance layout"
    discrimination = _require_mapping(metrics_payload, "discrimination", context=context)
    calibration = _require_mapping(metrics_payload, "calibration_drift", context=context)
    risk_group_separation = _require_mapping(metrics_payload, "risk_group_separation", context=context)
    absolute_risk_shift = _require_mapping(metrics_payload, "absolute_risk_shift", context=context)
    china_n = _parse_int(discrimination.get("china_n"), label="china_n")
    nhanes_n = _parse_int(discrimination.get("nhanes_n"), label="nhanes_n")
    if china_n <= 0 or nhanes_n <= 0:
        raise ValueError(f"{context} requires positive cohort sizes")
    china_c = _require_probability(discrimination, "china_c_index", context=context)
    nhanes_c = _require_probability(discrimination, "nhanes_c_index", context=context)
    china_predicted = _require_probability(calibration, "china_predicted_mean_5y_risk", context=context)
    nhanes_predicted = _require_probability(calibration, "nhanes_predicted_mean_5y_risk", context=context)
    china_observed = _require_probability(calibration, "china_observed_5y_rate", context=context)
    nhanes_observed = _require_probability(calibration, "nhanes_observed_5y_rate", context=context)
    calibration_shift = abs(_require_finite_number(calibration, "nhanes_minus_china_gap", context=context))
    china_oe = _positive_ratio(china_observed, china_predicted, label="China observed-to-expected ratio")
    nhanes_oe = _positive_ratio(nhanes_observed, nhanes_predicted, label="NHANES observed-to-expected ratio")
    china_top_bottom = abs(
        _require_finite_number(
            risk_group_separation,
            "china_top_minus_bottom_observed_5y_rate",
            context=context,
        )
    )
    nhanes_top_bottom = abs(
        _require_finite_number(
            risk_group_separation,
            "nhanes_top_minus_bottom_observed_5y_rate",
            context=context,
        )
    )
    separation_ratio = max(0.01, min(10.0, nhanes_top_bottom / china_top_bottom)) if china_top_bottom > 0 else 0.01
    risk_separation_shift = abs(
        _require_finite_number(
            risk_group_separation,
            "nhanes_minus_china",
            context=context,
        )
    )
    observed_rate_shift = abs(
        _require_finite_number(
            absolute_risk_shift,
            "observed_rate_shift_nhanes_minus_china",
            context=context,
        )
    )
    nhanes_verdict = (
        "recalibration_required"
        if nhanes_oe > 1.5 or calibration_shift > 0.05 or separation_ratio < 0.5
        else "context_dependent"
        if nhanes_c < china_c - 0.1
        else "stable"
    )
    template_id = display_registry.get_evidence_figure_spec(
        "generalizability_subgroup_composite_panel"
    ).template_id
    return {
        "schema_version": 1,
        "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
        "source_contract_path": "paper/medical_reporting_contract.json",
        "status": "materialized_from_current_transportability_layout",
        "displays": [
            {
                "display_id": display_id,
                "template_id": template_id,
                "catalog_id": catalog_id,
                "paper_role": "main_text",
                "title": "China-US transportability and recalibration summary",
                "caption": (
                    "External transportability is summarized with cohort-level discrimination, "
                    "observed-to-expected calibration, and risk-separation retention."
                ),
                "metric_family": "discrimination",
                "primary_label": "China-derived score",
                "comparator_label": "China reference",
                "overview_panel_title": "Discrimination transportability",
                "overview_x_label": "C-index",
                "overview_rows": [
                    {
                        "cohort_id": "china_reference",
                        "cohort_label": "China",
                        "support_count": china_n,
                        "event_count": _event_count_from_rate(support_count=china_n, rate=china_observed),
                        "metric_value": china_c,
                        "comparator_metric_value": china_c,
                    },
                    {
                        "cohort_id": "nhanes_external",
                        "cohort_label": "NHANES",
                        "support_count": nhanes_n,
                        "event_count": _event_count_from_rate(support_count=nhanes_n, rate=nhanes_observed),
                        "metric_value": nhanes_c,
                        "comparator_metric_value": china_c,
                    },
                ],
                "subgroup_panel_title": "Recalibration governance metrics",
                "subgroup_x_label": "Ratio or retained separation",
                "subgroup_reference_value": 1.0,
                "subgroup_rows": [
                    {
                        "subgroup_id": "china_oe_ratio",
                        "subgroup_label": "China O:E ratio",
                        "group_n": china_n,
                        "estimate": china_oe,
                        "lower": min(0.90, china_oe),
                        "upper": max(1.10, china_oe),
                    },
                    {
                        "subgroup_id": "nhanes_oe_ratio",
                        "subgroup_label": "NHANES O:E ratio",
                        "group_n": nhanes_n,
                        "estimate": nhanes_oe,
                        "lower": min(0.90, nhanes_oe),
                        "upper": max(1.10, nhanes_oe),
                    },
                    {
                        "subgroup_id": "risk_separation_retention",
                        "subgroup_label": "NHANES/China risk separation",
                        "group_n": nhanes_n,
                        "estimate": separation_ratio,
                        "lower": min(0.50, separation_ratio),
                        "upper": max(1.00, separation_ratio),
                    },
                ],
                "source_context": {
                    "calibration_shift": calibration_shift,
                    "risk_separation_shift": risk_separation_shift,
                    "observed_rate_shift": observed_rate_shift,
                    "transportability_verdict": nhanes_verdict,
                },
            }
        ],
    }


def run_current_transportability_layout_migration(
    *,
    study_root: Path,
    paper_root: Path,
    bindings: dict[str, dict[str, str]],
    f5_binding: dict[str, str],
) -> dict[str, Any]:
    transportability_root = Path(study_root) / TRANSPORTABILITY_LAYOUT_RELATIVE_ROOT
    metrics_path = transportability_root / "metrics_summary.json"
    discrimination_report_path = transportability_root / "discrimination_report.md"
    risk_group_report_path = transportability_root / "risk_group_composition_report.md"
    for path in (metrics_path, discrimination_report_path, risk_group_report_path):
        if not path.exists():
            raise FileNotFoundError(f"missing required current transportability layout file: {path}")
    metrics_payload = _load_json(metrics_path)
    written_files: list[str] = []

    discrimination_path = Path(paper_root) / "time_to_event_discrimination_calibration_inputs.json"
    _write_json(
        discrimination_path,
        _build_transportability_discrimination_payload(
            metrics_payload=metrics_payload,
            display_id=bindings["time_to_event_discrimination_calibration_panel"]["display_id"],
        ),
    )
    written_files.append(str(discrimination_path))

    grouped_path = Path(paper_root) / "time_to_event_grouped_inputs.json"
    _write_json(
        grouped_path,
        _build_transportability_risk_group_payload(
            risk_group_report_path=risk_group_report_path,
            display_id=bindings["time_to_event_risk_group_summary"]["display_id"],
        ),
    )
    written_files.append(str(grouped_path))

    governance_path = Path(paper_root) / "generalizability_subgroup_composite_inputs.json"
    _write_json(
        governance_path,
        _build_transportability_governance_payload(
            metrics_payload=metrics_payload,
            display_id=f5_binding["display_id"],
            catalog_id=f5_binding["catalog_id"],
        ),
    )
    written_files.append(str(governance_path))
    retired_governance_path = Path(paper_root) / "transportability_recalibration_governance_panel.json"
    if retired_governance_path.exists():
        retired_governance_path.unlink()

    notes: dict[str, Any] = {
        "analysis_layout": "transportability_current_layout",
        "f5_template": "generalizability_subgroup_composite_panel",
    }
    decision_curve_path = Path(paper_root) / "time_to_event_decision_curve_inputs.json"
    if decision_curve_path.exists():
        notes["decision_curve_payload"] = "preserved_existing_current_payload"
    else:
        raise FileNotFoundError(
            "current transportability layout requires an existing decision-curve payload; "
            f"missing {decision_curve_path}"
        )
    table2_path = Path(paper_root) / "time_to_event_performance_summary.json"
    if table2_path.exists():
        notes["time_to_event_performance_summary"] = "preserved_existing_current_payload"
    else:
        raise FileNotFoundError(
            "current transportability layout requires an existing performance-summary payload; "
            f"missing {table2_path}"
        )

    return {
        "written_files": written_files,
        "source_paths": {
            "metrics_summary": str(metrics_path),
            "discrimination_report": str(discrimination_report_path),
            "risk_group_composition_report": str(risk_group_report_path),
        },
        "notes": notes,
    }
