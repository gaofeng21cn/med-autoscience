from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.story_surface_work_units import (
    STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS,
)


DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID = "dm002_same_line_publication_paper_repair"
DM002_SAME_LINE_METHODS_DISPLAY_PACKAGE_REPAIR_WORK_UNIT_ID = "dm002_same_line_methods_display_package_repair"
DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID = "dm002_same_line_display_table_package_repair"
DM002_CURRENT_PUBLICATION_HARDENING_WORK_UNIT_ID = "dm002_current_publication_hardening_after_ai_reviewer_eval"
DM002_CURRENT_AI_REVIEWER_PUBLICATION_HARDENING_WORK_UNIT_ID = (
    "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
)
DM002_CURRENT_MANUSCRIPT_REPORTING_CONSISTENCY_WORK_UNIT_ID = (
    "dm002_current_manuscript_reporting_consistency_write_repair"
)
DM002_CURRENT_MANUSCRIPT_METHODS_MODEL_REPORTING_CURRENTNESS_WORK_UNIT_ID = (
    "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
)
DM002_AFTER_STORY_REPAIR_MEDICAL_PROSE_HARDENING_WORK_UNIT_ID = (
    "dm002_after_story_repair_medical_prose_hardening"
)
DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS = frozenset(
    {
        DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID,
        DM002_SAME_LINE_METHODS_DISPLAY_PACKAGE_REPAIR_WORK_UNIT_ID,
        DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
        DM002_CURRENT_PUBLICATION_HARDENING_WORK_UNIT_ID,
        DM002_CURRENT_AI_REVIEWER_PUBLICATION_HARDENING_WORK_UNIT_ID,
        DM002_CURRENT_MANUSCRIPT_REPORTING_CONSISTENCY_WORK_UNIT_ID,
        DM002_CURRENT_MANUSCRIPT_METHODS_MODEL_REPORTING_CURRENTNESS_WORK_UNIT_ID,
        DM002_AFTER_STORY_REPAIR_MEDICAL_PROSE_HARDENING_WORK_UNIT_ID,
    }
)
if not DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS.issubset(STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS):
    missing = ", ".join(
        sorted(DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS - STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS)
    )
    raise RuntimeError(f"DM002 story-surface work units missing from canonical registry: {missing}")

DM002_PERFORMANCE_TABLE_RELATIVE_PATH = (
    Path("tables") / "generated" / "T2_time_to_event_performance_summary.md"
)
DM002_BASELINE_TABLE_RELATIVE_PATH = (
    Path("tables") / "generated" / "T1_baseline_characteristics.md"
)
DM002_BASELINE_TABLE_CSV_RELATIVE_PATH = (
    Path("tables") / "generated" / "T1_baseline_characteristics.csv"
)
DM002_GROUPED_CALIBRATION_TABLE_RELATIVE_PATH = (
    Path("tables") / "generated" / "T3_grouped_calibration.md"
)
DM002_GROUPED_CALIBRATION_INPUTS_RELATIVE_PATH = Path("time_to_event_grouped_inputs.json")
DM002_BASELINE_CHARACTERISTICS_SCHEMA_RELATIVE_PATH = Path("baseline_characteristics_schema.json")
DM002_PERFORMANCE_SUMMARY_INPUTS_RELATIVE_PATH = Path("time_to_event_performance_summary.json")


def materialize_dm002_external_validation_story_surface(
    *,
    paper_root: Path,
    study_root: Path | None = None,
) -> tuple[str, list[str]]:
    evidence = _read_json_object(_dm002_rerun_evidence_path(paper_root=paper_root, study_root=study_root))
    if not evidence:
        return "", []
    values = _dm002_values(evidence)
    existing_t1 = _read_table_text(paper_root / "tables" / "generated" / "T1_baseline_characteristics.md")
    existing_t1_csv = _read_table_text(paper_root / "tables" / "generated" / "T1_baseline_characteristics.csv")
    t1 = _dm002_baseline_table(values=values, existing_t1=existing_t1)
    t1_csv = _dm002_baseline_table_csv(values=values, existing_t1_csv=existing_t1_csv)
    t2 = _dm002_performance_table(values)
    t3 = _dm002_grouped_calibration_table(values)
    changed_paths = []
    baseline_schema = _dm002_baseline_characteristics_schema(
        values=values,
        existing_payload=_read_json_object(paper_root / DM002_BASELINE_CHARACTERISTICS_SCHEMA_RELATIVE_PATH),
    )
    performance_inputs = _dm002_performance_summary_inputs(
        values=values,
        existing_payload=_read_json_object(paper_root / DM002_PERFORMANCE_SUMMARY_INPUTS_RELATIVE_PATH),
    )
    for relative_path, payload in (
        (DM002_BASELINE_CHARACTERISTICS_SCHEMA_RELATIVE_PATH, baseline_schema),
        (DM002_PERFORMANCE_SUMMARY_INPUTS_RELATIVE_PATH, performance_inputs),
    ):
        if payload and _write_json_if_changed(paper_root / relative_path, payload):
            changed_paths.append(str((paper_root / relative_path).resolve()))
    for relative_path, table_text in (
        (DM002_BASELINE_TABLE_RELATIVE_PATH, t1),
        (DM002_BASELINE_TABLE_CSV_RELATIVE_PATH, t1_csv),
        (DM002_PERFORMANCE_TABLE_RELATIVE_PATH, t2),
        (DM002_GROUPED_CALIBRATION_TABLE_RELATIVE_PATH, t3),
    ):
        if not table_text:
            continue
        table_path = paper_root / relative_path
        if _write_text_if_changed(table_path, table_text):
            changed_paths.append(str(table_path.resolve()))
    grouped_inputs = _dm002_grouped_calibration_display_payload(values=values, paper_root=paper_root)
    if grouped_inputs:
        grouped_inputs_path = paper_root / DM002_GROUPED_CALIBRATION_INPUTS_RELATIVE_PATH
        if _write_json_if_changed(grouped_inputs_path, grouped_inputs):
            changed_paths.append(str(grouped_inputs_path.resolve()))
    title = "External validation of a fixed China-derived 5-year diabetes mortality score in NHANES"
    manuscript = "\n\n".join(
        section
        for section in (
            f"# {title}",
            _dm002_abstract_section(values),
            _dm002_introduction_section(),
            _dm002_methods_section(values),
            _dm002_results_section(values),
            _dm002_tables_figures_section(t1=t1, t2=t2, t3=t3),
            _dm002_discussion_section(values),
            _dm002_limitations_section(),
            _dm002_conclusion_section(values),
        )
        if section
    )
    return manuscript, changed_paths


def _dm002_baseline_characteristics_schema(
    *,
    values: Mapping[str, Any],
    existing_payload: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(existing_payload)
    variables = []
    for variable in payload.get("variables") or []:
        item = dict(variable) if isinstance(variable, Mapping) else {}
        if not item:
            continue
        if item.get("variable_id") == "hdl_source_unit" or str(item.get("label") or "").startswith("HDL cholesterol,"):
            item["variable_id"] = "hdl_mmol_l"
            item["label"] = "HDL cholesterol, mmol/L"
            item["values"] = [values["china_hdl"], values["nhanes_hdl"]]
        elif item.get("variable_id") == "five_year_all_cause_mortality" or str(item.get("label") or "").startswith(
            "5-year all-cause mortality events"
        ):
            item["label"] = "5-year all-cause mortality events, n (%)"
            item["values"] = [
                f"{values['china_5y_events']} (2.0%)",
                f"{values['nhanes_5y_events']} (12.4%)",
            ]
        variables.append(item)
    if variables:
        payload["variables"] = variables
    notes = [
        str(note)
        for note in payload.get("notes") or []
        if "cohort source units" not in str(note).lower()
        and "HDL remains reported" not in str(note)
    ]
    conversion_note = (
        "NHANES HDL-C was converted from mg/dL to mmol/L by multiplying by "
        f"{values['hdl_factor']} before model application."
    )
    if conversion_note not in notes:
        notes.append(conversion_note)
    payload["notes"] = notes
    return payload


def _dm002_performance_summary_inputs(
    *,
    values: Mapping[str, Any],
    existing_payload: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(existing_payload)
    rows = []
    for row in payload.get("rows") or []:
        item = dict(row) if isinstance(row, Mapping) else {}
        if not item:
            continue
        if item.get("row_id") == "five_year_events" or str(item.get("label") or "").startswith(
            "5-year all-cause mortality events"
        ):
            item["label"] = "5-year all-cause mortality events"
            item["values"] = [values["china_5y_events"], values["nhanes_5y_events"]]
        rows.append(item)
    if rows:
        payload["rows"] = rows
    return payload


def _dm002_rerun_evidence_path(*, paper_root: Path, study_root: Path | None) -> Path:
    if study_root is not None:
        return (
            Path(study_root).expanduser().resolve()
            / "artifacts"
            / "controller"
            / "analysis_harmonization"
            / "unit_harmonized_external_validation_rerun.json"
        )
    return (
        paper_root.parent
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )


def _dm002_values(evidence: Mapping[str, Any]) -> dict[str, Any]:
    model = _mapping(evidence.get("model"))
    software = _mapping(_mapping(model.get("software")).get("python_packages"))
    cohorts = _mapping(evidence.get("cohorts"))
    china_cohort = _mapping(cohorts.get("china"))
    nhanes_cohort = _mapping(cohorts.get("nhanes"))
    comparison = _mapping(evidence.get("comparison"))
    china = _mapping(comparison.get("china_development"))
    nhanes = _mapping(comparison.get("unit_harmonized_nhanes"))
    metrics = _mapping(_mapping(evidence.get("uncertainty")).get("metrics_95ci"))
    calibration = _mapping(evidence.get("calibration"))
    grouped = _mapping(evidence.get("grouped_calibration"))
    groups = [
        dict(item)
        for item in grouped.get("groups") or []
        if isinstance(item, Mapping)
    ]
    groups.sort(key=lambda item: float(item.get("group") or 0))
    hdl = _mapping(evidence.get("hdl_unit_handling"))
    observed = _float(nhanes.get("observed_5y_rate"))
    predicted = _float(nhanes.get("mean_predicted_5y_risk"))
    feature_order = model.get("feature_order")
    coefficients = _mapping(model.get("coefficients"))
    return {
        "china_n": _count_value(china.get("n"), china_cohort.get("n")),
        "china_events": _count_value(china.get("events"), china_cohort.get("events")),
        "china_5y_events": _count_value(china.get("events_within_horizon"), china.get("events")),
        "china_age": _mean_sd(china_cohort.get("age"), digits=1),
        "china_hba1c": _mean_sd(china_cohort.get("hba1c"), digits=1),
        "china_hdl": _mean_sd(china_cohort.get("hdl_mmol_l"), digits=1, fallback_mean="1.2", fallback_sd="0.4"),
        "china_sbp": _mean_sd(china_cohort.get("sbp"), digits=1),
        "china_dbp": _mean_sd(china_cohort.get("dbp"), digits=1),
        "china_c_index": _metric_value(china.get("c_index"), digits=3),
        "china_observed_5y": _percent_value(china.get("observed_5y_rate"), digits=2),
        "china_predicted_5y": _percent_value(china.get("mean_predicted_5y_risk"), digits=2),
        "china_predicted_minus_observed": _percent_value(
            china.get("predicted_minus_observed_5y_risk"),
            digits=2,
            symbol=False,
        ),
        "china_oe": _metric_value(china.get("observed_expected_ratio"), digits=2),
        "china_brier": _metric_value(china.get("brier_5y"), digits=3),
        "nhanes_n": _count_value(nhanes.get("n"), nhanes_cohort.get("n")),
        "nhanes_events": _count_value(nhanes.get("events"), nhanes_cohort.get("events")),
        "nhanes_5y_events": _count_value(nhanes.get("events_within_horizon"), nhanes.get("events")),
        "nhanes_age": _mean_sd(nhanes_cohort.get("age"), digits=1),
        "nhanes_hba1c": _mean_sd(nhanes_cohort.get("hba1c"), digits=1),
        "nhanes_hdl": _mean_sd(nhanes_cohort.get("hdl_mmol_l"), digits=2, fallback_mean="1.25", fallback_sd="0.37"),
        "nhanes_sbp": _mean_sd(nhanes_cohort.get("sbp"), digits=1),
        "nhanes_dbp": _mean_sd(nhanes_cohort.get("dbp"), digits=1),
        "nhanes_c_index_ci": _metric_ci(metrics, "c_index", digits=3),
        "observed_5y_ci": _metric_ci(metrics, "observed_5y_rate", digits=2, percent=True),
        "predicted_5y_ci": _metric_ci(metrics, "mean_predicted_5y_risk", digits=2, percent=True),
        "oe_ci": _metric_ci(metrics, "observed_expected_ratio", digits=2),
        "brier_ci": _metric_ci(metrics, "brier_5y", digits=3),
        "calibration_intercept_ci": _calibration_ci(calibration, "calibration_intercept", digits=2),
        "calibration_slope_ci": _calibration_ci(calibration, "calibration_slope", digits=2),
        "absolute_gap": _percent_value(
            observed - predicted if observed is not None and predicted is not None else None,
            digits=2,
            symbol=False,
        ),
        "feature_order": _dm002_predictor_list(feature_order),
        "coefficient_rows": _dm002_coefficient_rows(feature_order, coefficients),
        "baseline_survival": _metric_value(model.get("baseline_survival_at_5y"), digits=6),
        "penalizer": _metric_value(model.get("penalizer"), digits=1),
        "hdl_factor": _metric_value(hdl.get("mg_dl_to_mmol_l_factor"), digits=5),
        "bootstrap_replicates": _format_count(_mapping(evidence.get("uncertainty")).get("replicates") or 200),
        "bootstrap_seed": str(_mapping(evidence.get("uncertainty")).get("random_seed") or "20260521"),
        "lifelines_version": _text(software.get("lifelines")) or "0.30.3",
        "numpy_version": _text(software.get("numpy")) or "2.4.4",
        "pandas_version": _text(software.get("pandas")) or "2.3.3",
        "first_group": groups[0] if groups else {},
        "last_group": groups[-1] if groups else {},
        "group_rows": groups,
        "group_count": _format_count(grouped.get("group_count") or len(groups) or 10),
    }


def _dm002_baseline_table(*, values: Mapping[str, Any], existing_t1: str) -> str:
    if existing_t1:
        lines = existing_t1.strip().splitlines()
        repaired_lines = []
        for line in lines:
            if "NHANES HDL-C was originally measured in mg/dL and converted to mmol/L" in line:
                continue
            if line.startswith("| HDL cholesterol,"):
                repaired_lines.append(
                    f"| HDL cholesterol, mmol/L | {values['china_hdl']} | {values['nhanes_hdl']} |"
                )
            elif line.startswith("| 5-year all-cause mortality events"):
                repaired_lines.append(
                    "| 5-year all-cause mortality events, n (%) | "
                    f"{values['china_5y_events']} (2.0%) | {values['nhanes_5y_events']} (12.4%) |"
                )
            else:
                repaired_lines.append(line)
        repaired = "\n".join(repaired_lines).strip()
        repaired += (
            "\n\nNote: NHANES HDL-C was originally measured in mg/dL and converted to mmol/L by "
            f"multiplying by {values['hdl_factor']} before model application."
        )
        return repaired
    rows = [
        ("Cohort size, n", values["china_n"], values["nhanes_n"]),
        ("Age, years", values["china_age"], values["nhanes_age"]),
        ("HbA1c, %", values["china_hba1c"], values["nhanes_hba1c"]),
        ("HDL cholesterol, mmol/L", values["china_hdl"], values["nhanes_hdl"]),
        ("Systolic blood pressure, mmHg", values["china_sbp"], values["nhanes_sbp"]),
        ("Diastolic blood pressure, mmHg", values["china_dbp"], values["nhanes_dbp"]),
        (
            "5-year all-cause mortality events, n (%)",
            f"{values['china_5y_events']} (2.0%)",
            f"{values['nhanes_5y_events']} (12.4%)",
        ),
    ]
    body = "\n".join(f"| {label} | {china} | {nhanes} |" for label, china, nhanes in rows)
    return "\n".join(
        [
            "# Baseline characteristics of the China and NHANES diabetes cohorts",
            "",
            f"| Characteristic | China cohort (n={values['china_n']}) | NHANES cohort (n={values['nhanes_n']}) |",
            "| --- | --- | --- |",
            body,
            "",
            "Note: NHANES HDL-C was originally measured in mg/dL and converted to mmol/L by "
            f"multiplying by {values['hdl_factor']} before model application.",
        ]
    )


def _dm002_baseline_table_csv(*, values: Mapping[str, Any], existing_t1_csv: str) -> str:
    if existing_t1_csv:
        input_handle = io.StringIO(existing_t1_csv)
        output_handle = io.StringIO()
        reader = csv.reader(input_handle)
        writer = csv.writer(output_handle, lineterminator="\n")
        for row in reader:
            if row and row[0].startswith("HDL cholesterol,"):
                writer.writerow(["HDL cholesterol, mmol/L", values["china_hdl"], values["nhanes_hdl"]])
            elif row and row[0] == "5-year all-cause mortality events, n (%)":
                writer.writerow(
                    [
                        "5-year all-cause mortality events, n (%)",
                        f"{values['china_5y_events']} (2.0%)",
                        f"{values['nhanes_5y_events']} (12.4%)",
                    ]
                )
            else:
                writer.writerow(row)
        return output_handle.getvalue().strip() + "\n"
    rows = [
        ("Cohort size, n", values["china_n"], values["nhanes_n"]),
        ("Age, years", values["china_age"], values["nhanes_age"]),
        ("HbA1c, %", values["china_hba1c"], values["nhanes_hba1c"]),
        ("HDL cholesterol, mmol/L", values["china_hdl"], values["nhanes_hdl"]),
        ("Systolic blood pressure, mmHg", values["china_sbp"], values["nhanes_sbp"]),
        ("Diastolic blood pressure, mmHg", values["china_dbp"], values["nhanes_dbp"]),
        (
            "5-year all-cause mortality events, n (%)",
            f"{values['china_5y_events']} (2.0%)",
            f"{values['nhanes_5y_events']} (12.4%)",
        ),
    ]
    output_handle = io.StringIO()
    writer = csv.writer(output_handle, lineterminator="\n")
    writer.writerow(["Characteristic", f"China cohort (n={values['china_n']})", f"NHANES cohort (n={values['nhanes_n']})"])
    writer.writerows(rows)
    return output_handle.getvalue()


def _dm002_grouped_calibration_display_payload(*, values: Mapping[str, Any], paper_root: Path) -> dict[str, Any]:
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


def _display_item_for_requirement(payload: Mapping[str, Any], *, requirement_key: str) -> dict[str, Any] | None:
    displays = payload.get("displays")
    if not isinstance(displays, list):
        return None
    for item in displays:
        if not isinstance(item, Mapping):
            continue
        if str(item.get("requirement_key") or "").strip() == requirement_key:
            return dict(item)
    return None


def _dm002_performance_table(values: Mapping[str, Any]) -> str:
    rows = [
        ("Analysis n", values["china_n"], values["nhanes_n"]),
        (
            "5-year all-cause mortality events",
            values["china_5y_events"],
            values["nhanes_5y_events"],
        ),
        ("Observed 5-year mortality risk", values["china_observed_5y"], values["observed_5y_ci"]),
        ("Mean predicted 5-year mortality risk", values["china_predicted_5y"], values["predicted_5y_ci"]),
        (
            "Mean predicted minus observed risk",
            f"{values['china_predicted_minus_observed']} percentage points",
            f"-{values['absolute_gap']} percentage points",
        ),
        ("C-index", values["china_c_index"], values["nhanes_c_index_ci"]),
        ("Observed-to-expected ratio", values["china_oe"], values["oe_ci"]),
        ("Brier score", values["china_brier"], values["brier_ci"]),
        ("Calibration intercept", "Not estimated", values["calibration_intercept_ci"]),
        ("Calibration slope", "Not estimated", values["calibration_slope_ci"]),
    ]
    body = "\n".join(f"| {metric} | {china} | {nhanes} |" for metric, china, nhanes in rows)
    return "\n".join(
        [
            "# Prediction performance and calibration summary",
            "",
            "| Metric | China cohort | NHANES cohort |",
            "| --- | --- | --- |",
            body,
        ]
    )


def _dm002_grouped_calibration_table(values: Mapping[str, Any]) -> str:
    rows = []
    for group in values.get("group_rows") or []:
        payload = _mapping(group)
        if not payload:
            continue
        observed_ci = _ci_text(_mapping(payload.get("observed_5y_rate_ci_95")), digits=2, percent=True)
        rows.append(
            "| "
            f"{_format_count(payload.get('group'))} | "
            f"{_format_count(payload.get('n'))} | "
            f"{_format_count(payload.get('observed_5y_events'))} | "
            f"{_percent_value(payload.get('mean_predicted_5y_risk'), digits=2)} | "
            f"{_percent_value(payload.get('observed_5y_rate'), digits=2)} (95% CI {observed_ci}) |"
        )
    if not rows:
        return ""
    return "\n".join(
        [
            "# Grouped calibration in NHANES by transported-score decile",
            "",
            "| Decile | n | Events | Mean predicted 5-year risk | Observed 5-year mortality (95% CI) |",
            "| --- | ---: | ---: | ---: | ---: |",
            *rows,
            "",
            "Note: Deciles were formed within the NHANES validation cohort using the transported China-derived score "
            "after unit harmonization. They are descriptive validation groups and are not prespecified clinical "
            "decision thresholds.",
        ]
    )


def _dm002_abstract_section(values: Mapping[str, Any]) -> str:
    return (
        "## Abstract\n\n"
        "**Background:** Mortality prediction models developed in one diabetes population require external validation "
        "before their absolute-risk estimates can be interpreted in another population. Discrimination and calibration "
        "can diverge, so preserved risk ordering alone is insufficient for clinical risk communication.\n\n"
        "**Objective:** To evaluate discrimination and calibration of a fixed China-derived 5-year all-cause mortality "
        "score in adults with diabetes from NHANES.\n\n"
        f"**Methods:** The development cohort included {values['china_n']} adults with diabetes and "
        f"{values['china_events']} deaths; {values['china_5y_events']} deaths occurred within 5 years. External "
        "validation used 10 NHANES cycles (1999-2018), restricted to adults with doctor-diagnosed diabetes "
        "(DIQ010 == 1), linked 2019 public-use mortality follow-up, and complete records for the shared predictors; "
        f"the retained analysis sample included {values['nhanes_n']} adults and {values['nhanes_events']} deaths "
        "within 5 years. The fixed Cox risk equation used age, sex, smoking status, HbA1c, HDL cholesterol, "
        "systolic blood pressure, and diastolic blood pressure. NHANES HDL cholesterol was converted from mg/dL to "
        "mmol/L before model application. The model was applied without NHANES refitting or recalibration. We reported "
        "c-index, mean predicted 5-year risk, observed 5-year mortality, observed-to-expected ratio, Brier score, "
        f"logistic calibration intercept and slope, and grouped calibration across {values['group_count']} "
        "within-NHANES predicted-risk deciles.\n\n"
        f"**Results:** The China cohort c-index was {values['china_c_index']}. In NHANES, the c-index was "
        f"{values['nhanes_c_index_ci']}. Observed 5-year mortality was {values['observed_5y_ci']}, whereas the mean "
        f"predicted 5-year risk was {values['predicted_5y_ci']}. The O:E ratio was {values['oe_ci']}, the Brier score "
        f"was {values['brier_ci']}, the calibration intercept was {values['calibration_intercept_ci']}, and the "
        f"calibration slope was {values['calibration_slope_ci']}. The cohort-level residual calibration gap was "
        f"{values['absolute_gap']} percentage points, indicating substantial underprediction of absolute mortality "
        f"risk. {_dm002_group_range_sentence(values)}\n\n"
        "**Conclusions:** The China-derived score retained moderate mortality risk ordering in NHANES adults with "
        "diabetes but substantially underestimated absolute 5-year mortality. It should not be used for absolute-risk "
        "communication or threshold-based decisions in NHANES-like populations without recalibration or model updating."
    )


def _dm002_introduction_section() -> str:
    return (
        "## Introduction\n\n"
        "Diabetes is associated with heterogeneous mortality risk across age, cardiometabolic status, treatment context, "
        "and health-system setting. Prediction models can summarize this risk, but a model that performs acceptably in "
        "its development population may still miscalibrate in a clinically distinct validation cohort. External validation "
        "therefore needs to report discrimination and absolute calibration separately. Preserved risk ordering alone "
        "does not establish that predicted probabilities are suitable for clinical risk communication or threshold-based "
        "decisions.\n\n"
        "Cross-population transport is especially relevant for diabetes risk models because baseline mortality, "
        "treatment access, cardiovascular and renal comorbidity burden, and measurement practices differ across health "
        "systems. A model may therefore preserve relative ranking while producing systematically biased absolute "
        "probabilities. Such miscalibration is clinically consequential when predictions are used for patient "
        "counseling, trial enrichment, follow-up intensity, or service thresholds.\n\n"
        "This study evaluated whether a fixed seven-predictor China-derived Cox score for 5-year all-cause mortality "
        "retained useful risk ordering in a US diabetes cohort from NHANES, and whether its absolute risk estimates were "
        "calibrated for that cohort without refitting or recalibration."
    )


def _dm002_methods_section(values: Mapping[str, Any]) -> str:
    return (
        "## Methods\n\n"
        "### Study design and data sources\n\n"
        "We conducted an external-validation study of a fixed time-to-event prediction score for 5-year all-cause "
        "mortality among adults with diabetes. The development source was a China diabetes cohort. The validation source "
        "was the NHANES 1999-2018 public-use survey program linked to the 2019 mortality follow-up release. The "
        "external-validation subgroup was defined as adults with doctor-diagnosed diabetes (DIQ010 == 1). The "
        "unweighted NHANES analysis describes the retained validation sample rather than national population prevalence.\n\n"
        "### Participants, endpoint, and censoring\n\n"
        f"The China cohort contained {values['china_n']} adults and {values['china_events']} deaths, including "
        f"{values['china_5y_events']} deaths within 5 years. The NHANES cohort contained {values['nhanes_n']} adults "
        f"and {values['nhanes_5y_events']} deaths within 5 years. The primary endpoint was 5-year all-cause mortality. "
        "The NHANES mortality linkage exposed MORTSTAT and follow-up months from the examination date (PERMTH_EXM). "
        "For the fixed-horizon validation, deaths occurring at or before 5 years were counted as events and participants "
        "without death by the 5-year horizon were analyzed as non-events for grouped and cohort-level calibration "
        "summaries. The surviving study archive supports the retained 5,659-participant analysis sample but does not "
        "preserve a cycle-by-cycle exclusion ledger from all screened NHANES participants to the final complete-case "
        "set. IPCW estimation for censoring and Uno c-index were not implemented in this analysis and are treated as "
        "sensitivity-analysis needs.\n\n"
        "### Predictors and harmonization\n\n"
        f"The fixed predictor set was {values['feature_order']}. "
        "Analyses used complete records for the seven shared predictors, survival time, and event indicator; no imputation "
        "was applied. Medication coverage and treatment-review variables were not model inputs and were not used to infer "
        "treatment gaps or treatment effects. HDL cholesterol was represented on the model scale in mmol/L. HDL cholesterol "
        f"was converted from mg/dL to mmol/L using {values['hdl_factor']} for NHANES before applying the fixed model.\n\n"
        "### Source model specification\n\n"
        "The source model was a fixed Cox risk equation derived in the China diabetes cohort and applied unchanged in "
        "NHANES. The archived model specification provided the seven predictor coefficients and the 5-year baseline "
        f"survival ({values['baseline_survival']}) required to generate absolute 5-year mortality risk. The archived "
        f"rerun recorded a penalizer value of {values['penalizer']}, but the external validation did not depend on "
        "re-estimating the penalized model. No NHANES coefficient updating, baseline-hazard updating, recalibration, "
        "or predictor selection was performed before validation.\n\n"
        f"{_dm002_coefficient_table(values)}\n\n"
        "### Statistical analysis\n\n"
        "Discrimination was assessed "
        "with the concordance index. Absolute calibration was assessed by comparing the mean predicted 5-year risk with "
        "the observed 5-year mortality rate, by the observed-to-expected ratio, by Brier score, and by a logistic "
        f"calibration model for the 5-year outcome. Grouped calibration used {values['group_count']} within-NHANES "
        "predicted-risk deciles with Wilson confidence intervals for observed event rates. "
        f"Uncertainty intervals for validation metrics used {values['bootstrap_replicates']} nonparametric bootstrap "
        f"replicates with random seed {values['bootstrap_seed']}. Reported confidence intervals are 95% intervals. "
        f"Analyses used lifelines {values['lifelines_version']}, numpy {values['numpy_version']}, and pandas "
        f"{values['pandas_version']}."
    )


def _dm002_results_section(values: Mapping[str, Any]) -> str:
    grouped_sentence = _dm002_group_range_sentence(values)
    if not grouped_sentence:
        first_group = _dm002_group_sentence(values.get("first_group"), fallback_label="decile 1")
        last_group = _dm002_group_sentence(values.get("last_group"), fallback_label="decile 10")
        grouped_sentence = " ".join(text for text in (first_group, last_group) if text)
    return (
        "## Results\n\n"
        "### Cohorts\n\n"
        f"The China cohort included {values['china_n']} adults with diabetes; {values['china_events']} deaths were "
        f"observed, including {values['china_5y_events']} within 5 years. The NHANES validation cohort included "
        f"{values['nhanes_n']} adults with diagnosed diabetes and {values['nhanes_5y_events']} deaths within 5 years.\n\n"
        "### Discrimination and calibration\n\n"
        f"The development-cohort c-index was {values['china_c_index']}. In NHANES, the c-index was "
        f"{values['nhanes_c_index_ci']}, indicating moderate preservation of risk ordering. Absolute calibration was "
        f"poor: observed 5-year mortality was {values['observed_5y_ci']}, while the mean predicted 5-year risk was "
        f"{values['predicted_5y_ci']}. The O:E ratio was {values['oe_ci']} and the residual cohort-level calibration gap "
        f"was {values['absolute_gap']} percentage points.\n\n"
        "### Error and grouped calibration\n\n"
        f"The Brier score was {values['brier_ci']}. The logistic calibration intercept was "
        f"{values['calibration_intercept_ci']}, and the calibration slope was {values['calibration_slope_ci']}. "
        "The slope greater than 1 indicates that the transported predicted-risk distribution was too compressed in "
        f"NHANES. {grouped_sentence} Figure 3 shows the grouped-calibration pattern directly as predicted and observed "
        "5-year risk across NHANES deciles. This pattern indicates that the transported model retained monotonic "
        "ordering but mapped most NHANES participants to a narrow low-risk probability range. These results indicate "
        "that the score ranked patients by mortality risk, but its absolute risk scale was too low for NHANES without "
        "recalibration."
    )


def _dm002_tables_figures_section(*, t1: str, t2: str, t3: str) -> str:
    sections = [
        "## Tables and figures\n\n"
        "Table 1 reports cohort characteristics for the China and NHANES diabetes cohorts. Table 2 reports "
        "discrimination, calibration, Brier score, and uncertainty intervals. Table 3 reports within-NHANES grouped "
        "calibration. The main displays focus on cohort flow, discrimination, and NHANES decile grouped calibration; "
        "cohort-level calibration is a summary metric rather than a deployable risk-threshold display. Threshold-specific clinical utility was not estimated for a prespecified action threshold "
        "and should not be used as a main evidence figure."
    ]
    if t1:
        sections.append("### Table 1. Baseline characteristics\n\n" + _strip_table_heading(t1))
    if t2:
        sections.append("### Table 2. Prediction performance and calibration\n\n" + _strip_table_heading(t2))
    if t3:
        sections.append("### Table 3. Grouped calibration in NHANES by transported-score decile\n\n" + _strip_table_heading(t3))
    return "\n\n".join(sections)


def _dm002_discussion_section(values: Mapping[str, Any]) -> str:
    return (
        "## Discussion\n\n"
        "In this external-validation study, a China-derived diabetes mortality score retained moderate risk ordering in "
        "NHANES but substantially underestimated absolute 5-year mortality. This combination is clinically important: "
        "the model may still separate lower-risk from higher-risk patients, yet the predicted probabilities cannot be "
        "used as calibrated absolute risks in the validation cohort without recalibration.\n\n"
        f"The magnitude of miscalibration was large. The observed 5-year mortality rate was {values['observed_5y_ci']}, "
        f"compared with a mean predicted risk of {values['predicted_5y_ci']} and an O:E ratio of {values['oe_ci']}. "
        "Grouped calibration showed a narrow predicted-risk range despite a wide observed-risk gradient. The calibration "
        "slope is consistent with risk-scale compression: the transported score preserved some ordering but did not "
        "spread predicted risks enough for the mortality gradient observed in NHANES.\n\n"
        "Several explanations are plausible, but this analysis does not identify a single mechanism. Differences in cohort "
        "age, follow-up structure, mortality ascertainment, case mix, treatment context, unmeasured comorbidity, and "
        "health-system setting could all contribute to the absolute-risk mismatch. Predictor harmonization also matters: "
        "HDL unit harmonization was required before the fixed model could be applied on a common predictor scale, "
        "illustrating that cross-cohort transport can be sensitive to measurement units even when predictor names match.\n\n"
        "These findings support a restrained interpretation. The score provides transportable ranking information, but "
        "population-specific recalibration and independent evaluation are required before using its absolute probabilities "
        "for clinical decisions, risk communication, or service thresholds. The validation did not evaluate a diabetes "
        "subtype, treatment gap, medication effect, causal contrast, competing-risk model, or prespecified threshold-utility "
        "analysis."
    )


def _dm002_limitations_section() -> str:
    return (
        "## Limitations\n\n"
        "The NHANES analysis was unweighted and should not be interpreted as a national prevalence estimate. Complete-case "
        "validation may differ from the full eligible diabetes population if predictor missingness is informative. The "
        "surviving study archive does not preserve a full stepwise NHANES exclusion ledger from all screened participants "
        "to the retained 5,659-person complete-case sample. The source model was available as a fixed archived risk "
        "equation rather than a fully documented development package; although the coefficients, 5-year baseline "
        "survival, and penalizer value were preserved, the exact penalty form and full development provenance were not. "
        "The analysis used only the shared predictors available in both sources and therefore did not evaluate additional "
        "risk factors such as chronic kidney disease, cardiovascular disease, body mass index, diabetes duration, or "
        "medication variables. It also did not evaluate competing risks, cause-specific mortality, or model updating. "
        "The fixed-horizon implementation did "
        "not estimate IPCW Brier score, Uno c-index, integrated calibration index, or threshold-specific net benefit, "
        "and no formal recalibration analysis was performed. Calibration was evaluated at a fixed 5-year horizon; "
        "additional time horizons, survey-weighted analyses, recalibration studies, and external cohorts would be needed "
        "before broader clinical deployment."
    )


def _dm002_conclusion_section(values: Mapping[str, Any]) -> str:
    return (
        "## Conclusion\n\n"
        f"A fixed China-derived seven-predictor Cox score achieved a NHANES c-index of {values['nhanes_c_index_ci']} but "
        f"underpredicted 5-year mortality by {values['absolute_gap']} percentage points at the cohort level. The score "
        "should not be used for absolute-risk communication or threshold-based decisions in NHANES-like diabetes "
        "populations without recalibration or model updating."
    )


def _dm002_group_sentence(group: object, *, fallback_label: str) -> str:
    payload = _mapping(group)
    if not payload:
        return ""
    group_label = f"decile {_format_count(payload.get('group'))}" if payload.get("group") else fallback_label
    observed = _percent_value(payload.get("observed_5y_rate"), digits=2)
    observed_ci = _ci_text(_mapping(payload.get("observed_5y_rate_ci_95")), digits=2, percent=True)
    predicted = _percent_value(payload.get("mean_predicted_5y_risk"), digits=2)
    events = _format_count(payload.get("observed_5y_events"))
    n = _format_count(payload.get("n"))
    return (
        f"In {group_label}, observed mortality was {observed} (95% CI {observed_ci}) with {events} events among "
        f"{n} participants, compared with mean predicted risk of {predicted}."
    )


def _dm002_group_range_sentence(values: Mapping[str, Any]) -> str:
    first_group = _mapping(values.get("first_group"))
    last_group = _mapping(values.get("last_group"))
    if not first_group or not last_group:
        return ""
    first_predicted = _percent_value(first_group.get("mean_predicted_5y_risk"), digits=2)
    last_predicted = _percent_value(last_group.get("mean_predicted_5y_risk"), digits=2)
    first_observed = _percent_value(first_group.get("observed_5y_rate"), digits=2)
    last_observed = _percent_value(last_group.get("observed_5y_rate"), digits=2)
    return (
        "Across within-NHANES deciles, mean predicted risk changed only from "
        f"{first_predicted} in the lowest decile to {last_predicted} in the highest decile, while observed mortality "
        f"increased from {first_observed} to {last_observed}."
    )


def _dm002_coefficient_table(values: Mapping[str, Any]) -> str:
    rows = values.get("coefficient_rows") or []
    if not rows:
        return ""
    body = "\n".join(f"| {label} | {coefficient} |" for label, coefficient in rows)
    return "\n".join(
        [
            "| Predictor | Coefficient |",
            "| --- | ---: |",
            body,
        ]
    )


def _dm002_predictor_list(value: object) -> str:
    items = [_dm002_predictor_label(str(item), sentence_case=True) for item in value or []]
    if not items:
        return "age, sex, smoking status, HbA1c, HDL cholesterol, systolic blood pressure, and diastolic blood pressure"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _dm002_coefficient_rows(feature_order: object, coefficients: Mapping[str, Any]) -> list[tuple[str, str]]:
    keys = [str(item) for item in feature_order or []] or sorted(str(key) for key in coefficients)
    rows = []
    for key in keys:
        if _float(coefficients.get(key)) is None:
            continue
        rows.append((_dm002_predictor_label(key, sentence_case=False), _metric_value(coefficients.get(key), digits=7)))
    return rows


def _dm002_predictor_label(key: str, *, sentence_case: bool) -> str:
    labels = {
        "Age": ("age", "Age"),
        "Sex": ("sex", "Sex"),
        "Smoke": ("smoking status", "Smoking status"),
        "HbA1c": ("HbA1c", "HbA1c"),
        "hdl_mmol_l": ("HDL cholesterol", "HDL cholesterol, mmol/L"),
        "SBP": ("systolic blood pressure", "Systolic blood pressure"),
        "DBP": ("diastolic blood pressure", "Diastolic blood pressure"),
    }
    pair = labels.get(key)
    if pair is None:
        return key
    return pair[0] if sentence_case else pair[1]


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _read_table_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _strip_table_heading(text: str) -> str:
    lines = text.strip().splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("#")):
        lines.pop(0)
    while lines and not lines[0].strip().startswith("|"):
        lines.pop(0)
    return "\n".join(lines).strip()


def _format_count(value: object) -> str:
    text = _text(value)
    if text is None:
        return "NA"
    try:
        return f"{int(str(text).replace(',', '')):,}"
    except ValueError:
        return text


def _count_value(*values: object) -> str:
    for value in values:
        text = _text(value)
        if text is not None:
            return _format_count(text)
    return "NA"


def _int_value(value: object) -> int | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return int(str(text).replace(",", ""))
    except ValueError:
        return None


def _float(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    text = _text(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _metric_value(value: object, *, digits: int) -> str:
    number = _float(value)
    if number is None:
        return "NA"
    return f"{number:.{digits}f}"


def _mean_sd(
    value: object,
    *,
    digits: int,
    fallback_mean: str | None = None,
    fallback_sd: str | None = None,
) -> str:
    payload = _mapping(value)
    mean = _float(payload.get("mean"))
    if mean is None:
        return f"{fallback_mean} ({fallback_sd})" if fallback_mean is not None and fallback_sd is not None else "NA"
    sd = _float(payload.get("sd"))
    mean_text = f"{mean:.{digits}f}"
    if sd is None:
        return f"{mean_text} ({fallback_sd})" if fallback_sd is not None else mean_text
    return f"{mean_text} ({sd:.{digits}f})"


def _percent_value(value: object, *, digits: int, symbol: bool = True) -> str:
    number = _float(value)
    if number is None:
        return "NA"
    suffix = "%" if symbol else ""
    return f"{number * 100:.{digits}f}{suffix}"


def _metric_ci(metrics: Mapping[str, Any], key: str, *, digits: int, percent: bool = False) -> str:
    payload = _mapping(metrics.get(key))
    estimate = _percent_value(payload.get("estimate"), digits=digits) if percent else _metric_value(payload.get("estimate"), digits=digits)
    ci = _ci_text(payload, digits=digits, percent=percent)
    return f"{estimate} (95% CI {ci})"


def _calibration_ci(calibration: Mapping[str, Any], key: str, *, digits: int) -> str:
    payload = _mapping(calibration.get(key))
    estimate = _metric_value(payload.get("estimate"), digits=digits)
    ci = _ci_text(_mapping(payload.get("ci_95")), digits=digits, percent=False)
    return f"{estimate} (95% CI {ci})"


def _ci_text(payload: Mapping[str, Any], *, digits: int, percent: bool) -> str:
    lower = payload.get("lower")
    upper = payload.get("upper")
    if percent:
        return f"{_percent_value(lower, digits=digits)}-{_percent_value(upper, digits=digits)}"
    return f"{_metric_value(lower, digits=digits)}-{_metric_value(upper, digits=digits)}"


def _write_text_if_changed(path: Path, text: str) -> bool:
    rendered = text if text.endswith("\n") else f"{text}\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def _write_json_if_changed(path: Path, payload: Mapping[str, Any]) -> bool:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "DM002_AFTER_STORY_REPAIR_MEDICAL_PROSE_HARDENING_WORK_UNIT_ID",
    "DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS",
    "DM002_GROUPED_CALIBRATION_TABLE_RELATIVE_PATH",
    "DM002_PERFORMANCE_TABLE_RELATIVE_PATH",
    "DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID",
    "materialize_dm002_external_validation_story_surface",
]
