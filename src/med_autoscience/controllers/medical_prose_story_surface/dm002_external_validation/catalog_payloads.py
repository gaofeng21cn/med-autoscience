from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def dm002_grouped_calibration_display_payload(
    *,
    values: Mapping[str, Any],
    paper_root: Path,
) -> dict[str, Any]:
    registry_payload = _read_json_object(paper_root / "display_registry.json")
    display_item = _display_item_for_requirement(
        registry_payload,
        requirement_key="time_to_event_risk_group_summary",
    )
    if display_item is None:
        return {}
    display_id = _text(display_item.get("display_id")) or "km_risk_stratification"
    catalog_id = _text(display_item.get("catalog_id")) or "F3"
    rows = []
    for group in values.get("group_rows") or []:
        payload = _mapping(group)
        if not payload:
            continue
        group_number = _format_count(payload.get("group"))
        group_order = _int_value(payload.get("group"))
        rows.append(
            {
                "label": f"Decile {group_number}",
                "cohort_id": "nhanes",
                "cohort_label": "NHANES",
                "risk_group_label": group_number,
                "group_order": group_order,
                "sample_size": _int_value(payload.get("n")),
                "events_5y": _int_value(payload.get("observed_5y_events")),
                "mean_predicted_risk_5y": _float(payload.get("mean_predicted_5y_risk")),
                "observed_km_risk_5y": _float(payload.get("observed_5y_rate")),
                "observed_5y_rate_ci_95": _mapping(payload.get("observed_5y_rate_ci_95")),
            }
        )
    if not rows:
        return {}
    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_grouped_inputs_v1",
        "source_contract_path": "paper/medical_reporting_contract.json",
        "status": "materialized_from_unit_harmonized_external_validation_rerun",
        "displays": [
            {
                "display_id": display_id,
                "template_id": "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
                "catalog_id": catalog_id,
                "paper_role": "main_text",
                "title": "Grouped calibration across NHANES transported-score deciles",
                "caption": (
                    "Mean predicted and observed 5-year mortality risk across within-NHANES deciles of the transported "
                    "China-derived score. Points show group-level estimates and observed-risk 95% confidence intervals. "
                    "Deciles are descriptive validation groups and are not treatment thresholds."
                ),
                "plot_variant": "nhanes_decile_grouped_calibration",
                "panel_a_title": "Grouped calibration across NHANES deciles",
                "x_label": "NHANES predicted-risk decile",
                "y_label": "5-year mortality risk",
                "risk_group_summaries": rows,
            }
        ],
    }


def dm002_figure_catalog_payload(*, existing_payload: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(existing_payload)
    existing_by_id = {
        _text(item.get("figure_id")): dict(item)
        for item in payload.get("figures") or []
        if isinstance(item, Mapping) and _text(item.get("figure_id"))
    }
    figures = []
    for figure_id, title, caption, template_id, export_paths, source_paths in (
        (
            "F1",
            "Fixed-score external-validation design",
            "China model derivation and NHANES external validation used the same seven-predictor score and 5-year "
            "all-cause mortality endpoint; NHANES predictions were generated after HDL unit harmonization without "
            "coefficient updating, baseline-hazard updating, refitting, or recalibration.",
            "fenggaolab.org.medical-display-core::cohort_flow_figure",
            [
                "paper/figures/generated/F1_cohort_flow.png",
                "paper/figures/generated/F1_cohort_flow.pdf",
            ],
            ["paper/cohort_flow.json"],
        ),
        (
            "F2",
            "External discrimination and cohort-level calibration",
            "Cohort-level overview of discrimination and 5-year mortality calibration for the China-derived score in "
            "the China cohort and the NHANES external-validation cohort after unit harmonization. Grouped calibration "
            "in Figure 3 is the primary calibration display.",
            "fenggaolab.org.medical-display-core::time_to_event_discrimination_calibration_panel",
            [
                "paper/figures/generated/F2_time_to_event_discrimination_calibration_panel.png",
                "paper/figures/generated/F2_time_to_event_discrimination_calibration_panel.pdf",
            ],
            ["paper/time_to_event_discrimination_calibration_inputs.json"],
        ),
        (
            "F3",
            "Grouped calibration across NHANES transported-score deciles",
            "Mean predicted and observed 5-year mortality risk across within-NHANES deciles of the transported "
            "China-derived score. Deciles are descriptive validation groups and are not treatment thresholds.",
            "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
            [
                "paper/figures/generated/F3_time_to_event_risk_group_summary.png",
                "paper/figures/generated/F3_time_to_event_risk_group_summary.pdf",
            ],
            ["paper/time_to_event_grouped_inputs.json"],
        ),
    ):
        item = existing_by_id.get(figure_id, {})
        item["figure_id"] = figure_id
        item["title"] = title
        item["caption"] = caption
        item["template_id"] = _text(item.get("template_id")) or template_id
        item["paper_role"] = "main_text"
        item["export_paths"] = export_paths
        item["source_paths"] = source_paths
        if figure_id == "F2":
            item["direct_message"] = (
                "The score retains moderate risk ordering in NHANES, but Figure 2 is a cohort-level overview; "
                "Figure 3 carries the grouped calibration evidence."
            )
            item["interpretation_boundary"] = (
                "The display supports a high-level discrimination and calibration summary, but it is not a "
                "replacement for grouped calibration or a deployable risk-threshold display."
            )
            item["panel_level_messages"] = [
                {
                    "panel": "A",
                    "message": "Risk ordering is evaluated separately from absolute-risk calibration.",
                },
                {
                    "panel": "B",
                    "message": "The cohort-level calibration point is an overview summary; grouped calibration is shown in Figure 3.",
                },
            ]
        figures.append(item)
    payload["schema_version"] = 1
    payload["figures"] = figures
    payload.pop("deferred_figures", None)
    return payload


def dm002_table_catalog_payload(*, existing_payload: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(existing_payload)
    existing_by_id = {
        _text(item.get("table_id")): dict(item)
        for item in payload.get("tables") or []
        if isinstance(item, Mapping) and _text(item.get("table_id"))
    }
    tables = []
    for table_id, title, caption, table_shell_id, input_schema_id, qc_profile, asset_paths, source_paths in (
        (
            "T1",
            "Baseline characteristics of the China and NHANES diabetes cohorts",
            "Continuous variables are reported as mean (SD), and binary variables are reported as n (%). "
            "The table is descriptive and does not present a statistical test or causal comparison.",
            "fenggaolab.org.medical-display-core::table1_baseline_characteristics",
            "baseline_characteristics_schema_v1",
            "publication_table_baseline",
            [
                "paper/tables/generated/T1_baseline_characteristics.csv",
                "paper/tables/generated/T1_baseline_characteristics.md",
            ],
            ["paper/baseline_characteristics_schema.json"],
        ),
        (
            "T2",
            "Prediction performance and calibration summary",
            "The China-derived 5-year all-cause mortality score is summarized in the China cohort and the NHANES "
            "external-validation cohort. Discrimination and cohort-level calibration are interpreted separately.",
            "fenggaolab.org.medical-display-core::table2_time_to_event_performance_summary",
            "time_to_event_performance_summary_v1",
            "publication_table_performance",
            ["paper/tables/generated/T2_time_to_event_performance_summary.md"],
            ["paper/time_to_event_performance_summary.json"],
        ),
        (
            "T3",
            "Grouped calibration in NHANES by transported-score decile",
            "Mean predicted and observed 5-year mortality risk across within-NHANES transported-score deciles. "
            "Deciles are descriptive validation groups and are not treatment thresholds.",
            "fenggaolab.org.medical-display-core::table3_grouped_calibration",
            "time_to_event_grouped_inputs_v1",
            "publication_table_calibration",
            ["paper/tables/generated/T3_grouped_calibration.md"],
            ["paper/time_to_event_grouped_inputs.json"],
        ),
    ):
        item = existing_by_id.get(table_id, {})
        item["table_id"] = table_id
        item["title"] = title
        item["caption"] = caption
        item["table_shell_id"] = _text(item.get("table_shell_id")) or table_shell_id
        item["paper_role"] = "main_text"
        item["input_schema_id"] = _text(item.get("input_schema_id")) or input_schema_id
        item["qc_profile"] = _text(item.get("qc_profile")) or qc_profile
        item["asset_paths"] = asset_paths
        item["source_paths"] = source_paths
        tables.append(item)
    payload["schema_version"] = 1
    payload["tables"] = tables
    return payload


def _display_item_for_requirement(
    payload: Mapping[str, Any],
    *,
    requirement_key: str,
) -> dict[str, Any] | None:
    displays = payload.get("displays")
    if not isinstance(displays, list):
        return None
    for item in displays:
        if not isinstance(item, Mapping):
            continue
        if str(item.get("requirement_key") or "").strip() == requirement_key:
            return dict(item)
    return None


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _format_count(value: object) -> str:
    numeric = _int_value(value)
    if numeric is None:
        text = _text(value)
        return text or "NA"
    return f"{numeric:,}"


def _int_value(value: object) -> int | None:
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return None


def _float(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
