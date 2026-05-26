from __future__ import annotations

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
DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS = frozenset(
    {
        DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID,
        DM002_SAME_LINE_METHODS_DISPLAY_PACKAGE_REPAIR_WORK_UNIT_ID,
        DM002_SAME_LINE_DISPLAY_TABLE_PACKAGE_REPAIR_WORK_UNIT_ID,
        DM002_CURRENT_PUBLICATION_HARDENING_WORK_UNIT_ID,
        DM002_CURRENT_AI_REVIEWER_PUBLICATION_HARDENING_WORK_UNIT_ID,
        DM002_CURRENT_MANUSCRIPT_REPORTING_CONSISTENCY_WORK_UNIT_ID,
        DM002_CURRENT_MANUSCRIPT_METHODS_MODEL_REPORTING_CURRENTNESS_WORK_UNIT_ID,
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


def materialize_dm002_external_validation_story_surface(*, paper_root: Path) -> tuple[str, list[str]]:
    evidence = _read_json_object(
        paper_root.parent
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    if not evidence:
        return "", []
    values = _dm002_values(evidence)
    t1 = _read_table_text(paper_root / "tables" / "generated" / "T1_baseline_characteristics.md")
    t2 = _dm002_performance_table(values)
    changed_paths = []
    table_path = paper_root / DM002_PERFORMANCE_TABLE_RELATIVE_PATH
    if _write_text_if_changed(table_path, t2):
        changed_paths.append(str(table_path.resolve()))
    title = "External validation of a China-derived diabetes mortality score in NHANES"
    manuscript = "\n\n".join(
        section
        for section in (
            f"# {title}",
            _dm002_abstract_section(values),
            _dm002_introduction_section(),
            _dm002_methods_section(values),
            _dm002_results_section(values),
            _dm002_tables_figures_section(t1=t1, t2=t2),
            _dm002_discussion_section(values),
            _dm002_limitations_section(),
            _dm002_conclusion_section(values),
        )
        if section
    )
    return manuscript, changed_paths


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
    return {
        "china_n": _count_value(china.get("n"), china_cohort.get("n")),
        "china_events": _count_value(china.get("events"), china_cohort.get("events")),
        "china_5y_events": _count_value(china.get("events_within_horizon"), china.get("events")),
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
        "feature_order": _dm002_predictor_list(model.get("feature_order")),
        "baseline_survival": _metric_value(model.get("baseline_survival_at_5y"), digits=6),
        "hdl_factor": _metric_value(hdl.get("mg_dl_to_mmol_l_factor"), digits=5),
        "bootstrap_replicates": _format_count(_mapping(evidence.get("uncertainty")).get("replicates") or 200),
        "bootstrap_seed": str(_mapping(evidence.get("uncertainty")).get("random_seed") or "20260521"),
        "lifelines_version": _text(software.get("lifelines")) or "0.30.3",
        "numpy_version": _text(software.get("numpy")) or "2.4.4",
        "pandas_version": _text(software.get("pandas")) or "2.3.3",
        "first_group": groups[0] if groups else {},
        "last_group": groups[-1] if groups else {},
        "group_count": _format_count(grouped.get("group_count") or len(groups) or 10),
    }


def _dm002_performance_table(values: Mapping[str, Any]) -> str:
    rows = [
        ("Analysis n", values["china_n"], values["nhanes_n"]),
        (
            "5-year all-cause mortality events",
            f"{values['china_events']} in analysis data; {values['china_5y_events']} within 5-year horizon",
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
        (
            "Metrics not available from current analysis files",
            "C-index interval, integrated calibration index, and threshold-specific net benefit",
            "Integrated calibration index, threshold-specific net benefit, and survey-weighted estimate",
        ),
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


def _dm002_abstract_section(values: Mapping[str, Any]) -> str:
    return (
        "## Abstract\n\n"
        "**Background:** Mortality prediction models developed in one diabetes population require external validation "
        "before their absolute-risk estimates can inform clinical interpretation in another population.\n\n"
        "**Objective:** To evaluate discrimination and calibration of a fixed China-derived 5-year all-cause mortality "
        "score in adults with diabetes from NHANES.\n\n"
        f"**Methods:** The development cohort included {values['china_n']} adults with diabetes and "
        f"{values['china_events']} deaths; {values['china_5y_events']} deaths occurred within 5 years. External "
        f"validation used {values['nhanes_n']} NHANES adults with diagnosed diabetes and {values['nhanes_events']} "
        "deaths within 5 years. The fixed Cox model used age, sex, smoking status, HbA1c, HDL cholesterol, systolic "
        "blood pressure, and diastolic blood pressure. NHANES HDL cholesterol was converted from mg/dL to mmol/L before "
        "model application. Discrimination, mean predicted 5-year risk, observed 5-year mortality, observed-to-expected "
        f"ratio, Brier score, logistic calibration, and {values['group_count']} risk groups were reported with bootstrap "
        "or Wilson 95% confidence intervals where applicable.\n\n"
        f"**Results:** The China cohort c-index was {values['china_c_index']}. In NHANES, the c-index was "
        f"{values['nhanes_c_index_ci']}. Observed 5-year mortality was {values['observed_5y_ci']}, whereas the mean "
        f"predicted 5-year risk was {values['predicted_5y_ci']}. The O:E ratio was {values['oe_ci']}, the Brier score "
        f"was {values['brier_ci']}, the calibration intercept was {values['calibration_intercept_ci']}, and the "
        f"calibration slope was {values['calibration_slope_ci']}. The cohort-level residual calibration gap was "
        f"{values['absolute_gap']} percentage points, indicating substantial underprediction of absolute mortality risk.\n\n"
        "**Conclusions:** The China-derived score retained moderate mortality risk ordering in NHANES adults with "
        "diabetes but substantially underestimated absolute 5-year mortality. The model should be interpreted as an "
        "externally validated ranking signal that requires population-specific recalibration before absolute-risk use."
    )


def _dm002_introduction_section() -> str:
    return (
        "## Introduction\n\n"
        "Diabetes is associated with heterogeneous mortality risk across age, cardiometabolic status, treatment context, "
        "and health-system setting. Prediction models can summarize this risk, but a model that performs acceptably in "
        "its development population may still miscalibrate in a clinically distinct validation cohort. External validation "
        "therefore needs to report discrimination and absolute calibration separately.\n\n"
        "This study evaluated whether a fixed seven-predictor China-derived Cox score for 5-year all-cause mortality "
        "retained useful risk ordering in a US diabetes cohort from NHANES, and whether its absolute risk estimates were "
        "calibrated for that cohort."
    )


def _dm002_methods_section(values: Mapping[str, Any]) -> str:
    return (
        "## Methods\n\n"
        "### Study design and data sources\n\n"
        "We conducted an external-validation study of a fixed time-to-event prediction score for 5-year all-cause "
        "mortality among adults with diabetes. The development source was a China diabetes cohort. The validation source "
        "was NHANES adults with diagnosed diabetes. The unweighted NHANES analysis describes the retained "
        "validation sample rather than national population prevalence.\n\n"
        "### Participants and predictors\n\n"
        f"The China cohort contained {values['china_n']} adults and {values['china_events']} deaths, including "
        f"{values['china_5y_events']} deaths within 5 years. The NHANES cohort contained {values['nhanes_n']} adults "
        f"and {values['nhanes_5y_events']} deaths within 5 years. The fixed predictor set was {values['feature_order']}. "
        "Analyses used complete records for the seven shared predictors, survival time, and event indicator; no imputation "
        "was applied. HDL cholesterol was represented on the model scale in mmol/L. HDL cholesterol was converted from "
        f"mg/dL to mmol/L using {values['hdl_factor']} for NHANES before applying the fixed model.\n\n"
        "### Prediction model and validation metrics\n\n"
        f"The model was a Cox proportional hazards model with fixed coefficients and baseline survival at 5 years of "
        f"{values['baseline_survival']}. The primary endpoint was 5-year all-cause mortality. Discrimination was assessed "
        "with the concordance index. Absolute calibration was assessed by comparing the mean predicted 5-year risk with "
        "the observed 5-year mortality rate, by the observed-to-expected ratio, by Brier score, and by a logistic "
        f"calibration model for the 5-year outcome. Grouped calibration used {values['group_count']} quantile groups of "
        "predicted risk with Wilson confidence intervals for observed event rates.\n\n"
        "### Statistical analysis\n\n"
        f"Uncertainty intervals for validation metrics used {values['bootstrap_replicates']} nonparametric bootstrap "
        f"replicates with random seed {values['bootstrap_seed']}. Reported confidence intervals are 95% intervals. "
        f"Analyses used lifelines {values['lifelines_version']}, numpy {values['numpy_version']}, and pandas "
        f"{values['pandas_version']}."
    )


def _dm002_results_section(values: Mapping[str, Any]) -> str:
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
        f"{values['nhanes_c_index_ci']}, indicating preserved but not definitive risk ordering. Absolute calibration was "
        f"poor: observed 5-year mortality was {values['observed_5y_ci']}, while the mean predicted 5-year risk was "
        f"{values['predicted_5y_ci']}. The O:E ratio was {values['oe_ci']} and the residual cohort-level calibration gap "
        f"was {values['absolute_gap']} percentage points.\n\n"
        "### Error and grouped calibration\n\n"
        f"The Brier score was {values['brier_ci']}. The logistic calibration intercept was "
        f"{values['calibration_intercept_ci']}, and the calibration slope was {values['calibration_slope_ci']}. "
        f"{grouped_sentence} These results indicate that the score ranked patients by mortality risk, but its absolute "
        "risk scale was too low for NHANES without recalibration."
    )


def _dm002_tables_figures_section(*, t1: str, t2: str) -> str:
    sections = [
        "## Tables and figures\n\n"
        "Table 1 reports cohort characteristics for the China and NHANES diabetes cohorts. Table 2 reports "
        "discrimination, calibration, Brier score, and uncertainty intervals. Figure 1 contains the cohort flow and "
        "shared predictor set; Figure 2 contains discrimination and calibration results; Figure 3 contains grouped "
        "calibration; Figure 4 contains clinical-impact context; and Figure 5 contains center or source-governance "
        "context where available."
    ]
    if t1:
        sections.append("### Table 1. Baseline characteristics\n\n" + _strip_table_heading(t1))
    if t2:
        sections.append("### Table 2. Prediction performance and calibration\n\n" + _strip_table_heading(t2))
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
        "Such underprediction is compatible with differences in cohort age, follow-up structure, mortality ascertainment, "
        "case mix, and health-system context. The slope estimate also indicates that recalibration cannot be reduced to "
        "a simple intercept shift without further evaluation.\n\n"
        "These findings support a restrained interpretation. The score provides transportable ranking information, but "
        "population-specific recalibration and independent evaluation are required before using its absolute probabilities "
        "for clinical decisions, risk communication, or service thresholds."
    )


def _dm002_limitations_section() -> str:
    return (
        "## Limitations\n\n"
        "The NHANES analysis was unweighted and should not be interpreted as a national prevalence estimate. Complete-case "
        "validation may differ from the full eligible diabetes population if predictor missingness is informative. The "
        "analysis used shared predictors available in both sources and did not evaluate additional biomarkers, treatments, "
        "competing risks, cause-specific mortality, or model updating. Calibration was evaluated at a fixed 5-year horizon; "
        "additional time horizons and external cohorts would be needed before broader clinical deployment."
    )


def _dm002_conclusion_section(values: Mapping[str, Any]) -> str:
    return (
        "## Conclusion\n\n"
        f"A fixed China-derived seven-predictor Cox score achieved a NHANES c-index of {values['nhanes_c_index_ci']} but "
        f"underpredicted 5-year mortality by {values['absolute_gap']} percentage points at the cohort level. The score "
        "should be treated as a transportable ranking model that needs recalibration before absolute-risk interpretation "
        "in NHANES-like diabetes populations."
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


def _dm002_predictor_list(value: object) -> str:
    labels = {
        "Age": "age",
        "Sex": "sex",
        "Smoke": "smoking status",
        "HbA1c": "HbA1c",
        "hdl_mmol_l": "HDL cholesterol",
        "SBP": "systolic blood pressure",
        "DBP": "diastolic blood pressure",
    }
    items = [labels.get(str(item), str(item)) for item in value or []]
    if not items:
        return "age, sex, smoking status, HbA1c, HDL cholesterol, systolic blood pressure, and diastolic blood pressure"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "DM002_EXTERNAL_VALIDATION_STORY_SURFACE_WORK_UNIT_IDS",
    "DM002_PERFORMANCE_TABLE_RELATIVE_PATH",
    "DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID",
    "materialize_dm002_external_validation_story_surface",
]
