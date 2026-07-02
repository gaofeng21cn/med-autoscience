from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience import display_registry

from .time_to_event_direct_migration_parts.file_sync import (
    DISCRIMINATION_CALIBRATION_REQUIREMENT_KEY,
    F2_REQUIREMENT_KEYS,
    F3_REQUIREMENT_KEYS,
    MULTICENTER_GENERALIZABILITY_REQUIREMENT_KEY,
    RISK_GROUP_SUMMARY_REQUIREMENT_KEY,
    TRANSPORTABILITY_GOVERNANCE_REQUIREMENT_KEY,
    _REQUIRED_DISPLAY_KEYS,
    _optional_binding,
    _require_binding,
    _require_binding_variant,
    _require_f5_binding_variant,
    _sync_authority_paper_truth,
)
from .time_to_event_direct_migration_parts.submission_graphical_abstract import (
    _build_submission_graphical_abstract_payload,
)
from .time_to_event_direct_migration_parts.shared import (
    _extract_regex_group,
    _load_csv_rows,
    _load_json,
    _load_markdown_table,
    _parse_float,
    _parse_int,
    _row_map_from_markdown_table,
    _slugify,
    _utc_now,
    _write_json,
)
from .time_to_event_direct_migration_parts.transportability_current import (
    current_transportability_layout_available,
    run_current_transportability_layout_migration,
)

_CENTER_SPLIT_BUCKET_ORDER = {"train": 0, "validation": 1}
_REGION_LABEL_TRANSLATIONS = {
    "华东": "East China",
    "华南": "South China",
    "华北": "North China",
    "华中": "Central China",
    "西北": "Northwest China",
    "西南": "Southwest China",
    "东北": "Northeast China",
}

def _format_center_label(raw_value: object) -> str:
    center_id = _parse_int(raw_value, label="center")
    if center_id < 0:
        raise ValueError(f"center must be non-negative: {raw_value!r}")
    return f"Center {center_id:02d}"

def _count_labels_preserving_first_seen_order(labels: list[str]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    first_seen_index: dict[str, int] = {}
    for index, label in enumerate(labels):
        if label not in counts:
            counts[label] = 0
            first_seen_index[label] = index
        counts[label] += 1
    return [
        {"label": label, "count": count}
        for label, count in sorted(counts.items(), key=lambda item: (-item[1], first_seen_index[item[0]]))
    ]

def _count_labels_in_fixed_order(labels: list[str], *, order: tuple[str, ...]) -> list[dict[str, Any]]:
    counts = {label: 0 for label in order}
    extras: dict[str, int] = {}
    for label in labels:
        if label in counts:
            counts[label] += 1
            continue
        extras[label] = extras.get(label, 0) + 1
    ordered = [{"label": label, "count": counts[label]} for label in order if counts[label] > 0]
    ordered.extend({"label": label, "count": extras[label]} for label in extras)
    return ordered

def _normalized_region_label(raw_value: object) -> str:
    raw_label = str(raw_value or "").strip()
    if not raw_label:
        return "Missing"
    return _REGION_LABEL_TRANSLATIONS.get(raw_label, raw_label)

def _normalized_north_south_label(raw_value: object) -> str:
    normalized = str(raw_value or "").strip()
    if normalized == "1":
        return "South"
    if normalized == "0":
        return "North"
    raise ValueError(f"patient_south_flag_raw must be `0` or `1`, got {raw_value!r}")

def _normalized_urban_rural_label(raw_value: object) -> str:
    normalized = str(raw_value or "").strip()
    if normalized == "0":
        return "Urban"
    if normalized == "1":
        return "Rural"
    if normalized == "":
        return "Missing"
    raise ValueError(f"patient_rural_flag_raw must be `0`, `1`, or empty, got {raw_value!r}")

def _load_validation_discrimination_points(path: Path) -> list[dict[str, Any]]:
    header, rows = _load_markdown_table(path)
    normalized_header = {value.strip().casefold(): index for index, value in enumerate(header)}
    required_columns = {"model", "split", "c_index"}
    missing_columns = required_columns - set(normalized_header)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"missing required discrimination_report columns in {path}: {missing}")

    points: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        if len(row) != len(header):
            raise ValueError(f"discrimination_report row length mismatch in {path} at row {row_index + 1}")
        split_value = row[normalized_header["split"]].strip().casefold()
        if split_value != "validation":
            continue
        model_label = row[normalized_header["model"]].strip()
        if not model_label:
            raise ValueError(f"validation discrimination row in {path} is missing model label")
        points.append(
            {
                "label": model_label,
                "c_index": _parse_float(
                    row[normalized_header["c_index"]],
                    label=f"{path.name} validation {model_label} c_index",
                ),
                "annotation": f"{_parse_float(row[normalized_header['c_index']], label=f'{path.name} validation {model_label} c_index'):.3f}",
            }
        )
    if not points:
        raise ValueError(f"no validation discrimination rows found in {path}")
    return points

def _event_by_horizon(row: dict[str, str], *, horizon_years: float) -> bool:
    return _parse_int(row.get("cvd_death"), label="cvd_death") == 1 and _parse_float(
        row.get("os_time"), label="os_time"
    ) <= horizon_years

def _is_evaluable_fixed_horizon(row: dict[str, str], *, horizon_years: float) -> bool:
    time_value = _parse_float(row.get("os_time"), label="os_time")
    event_value = _parse_int(row.get("cvd_death"), label="cvd_death")
    return time_value >= horizon_years or (event_value == 1 and time_value <= horizon_years)

def _build_roc_curve(scores: list[float], labels: list[int]) -> tuple[list[float], list[float], float]:
    positive_count = sum(labels)
    negative_count = len(labels) - positive_count
    if positive_count <= 0 or negative_count <= 0:
        raise ValueError("fixed-horizon ROC requires both positive and negative outcomes")
    thresholds = sorted(set(scores), reverse=True)
    points: list[tuple[float, float]] = [(0.0, 0.0)]
    for threshold in thresholds:
        tp = 0
        fp = 0
        for score, label in zip(scores, labels, strict=True):
            if score >= threshold:
                if label == 1:
                    tp += 1
                else:
                    fp += 1
        points.append((fp / negative_count, tp / positive_count))
    points.append((1.0, 1.0))

    deduped_points: list[tuple[float, float]] = []
    for point in points:
        if not deduped_points or deduped_points[-1] != point:
            deduped_points.append(point)
    area = 0.0
    for left, right in zip(deduped_points, deduped_points[1:]):
        x0, y0 = left
        x1, y1 = right
        area += (x1 - x0) * (y0 + y1) / 2.0
    return [point[0] for point in deduped_points], [point[1] for point in deduped_points], area

def _build_kaplan_meier_curve(
    rows: list[dict[str, str]],
    *,
    horizon_years: float,
) -> tuple[list[float], list[float]]:
    if not rows:
        raise ValueError("Kaplan-Meier curve requires non-empty rows")
    observations: list[tuple[float, int]] = sorted(
        (
            _parse_float(row.get("os_time"), label="os_time"),
            _parse_int(row.get("cvd_death"), label="cvd_death"),
        )
        for row in rows
    )
    at_risk = len(observations)
    if at_risk <= 0:
        raise ValueError("Kaplan-Meier curve requires positive at-risk count")

    times = [0.0]
    values = [1.0]
    survival = 1.0
    index = 0
    while index < len(observations):
        time_value = observations[index][0]
        if time_value > horizon_years:
            break
        event_count = 0
        censor_count = 0
        while index < len(observations) and observations[index][0] == time_value:
            if observations[index][1] == 1:
                event_count += 1
            else:
                censor_count += 1
            index += 1
        if event_count > 0:
            survival *= 1.0 - (event_count / at_risk)
            times.append(time_value)
            values.append(survival)
        at_risk -= event_count + censor_count
        if at_risk <= 0:
            break
    if times[-1] < horizon_years:
        times.append(horizon_years)
        values.append(survival)
    return times, values

def _build_time_dependent_roc_payload(
    *,
    prediction_rows: list[dict[str, str]],
    lasso_rows: list[dict[str, str]],
    display_id: str,
) -> dict[str, Any]:
    lasso_score_by_sequence = {
        str(row.get("Sequnece") or "").strip(): _parse_float(row.get("risk_score"), label="lasso risk_score")
        for row in lasso_rows
    }
    cox_scores: list[float] = []
    lasso_scores: list[float] = []
    labels: list[int] = []
    for row in prediction_rows:
        if not _is_evaluable_fixed_horizon(row, horizon_years=5.0):
            continue
        sequence_id = str(row.get("Sequnece") or "").strip()
        if sequence_id not in lasso_score_by_sequence:
            raise ValueError(f"missing lasso risk score for sequence `{sequence_id}`")
        cox_scores.append(_parse_float(row.get("risk_score"), label="cox risk_score"))
        lasso_scores.append(lasso_score_by_sequence[sequence_id])
        labels.append(1 if _event_by_horizon(row, horizon_years=5.0) else 0)
    cox_x, cox_y, cox_auc = _build_roc_curve(cox_scores, labels)
    lasso_x, lasso_y, lasso_auc = _build_roc_curve(lasso_scores, labels)

    return {
        "schema_version": 1,
        "input_schema_id": "binary_prediction_curve_inputs_v1",
        "displays": [
            {
                "display_id": display_id,
                "template_id": display_registry.get_evidence_figure_spec(
                    "time_dependent_roc_horizon"
                ).template_id,
                "title": "Five-year cardiovascular mortality discrimination",
                "caption": (
                    "Fixed-horizon ROC curves summarize discrimination for the primary Cox model "
                    "and the lasso comparator."
                ),
                "x_label": "1 - Specificity",
                "y_label": "Sensitivity",
                "time_horizon_months": 60,
                "series": [
                    {"label": f"CoxPH AUC {cox_auc:.3f}", "x": cox_x, "y": cox_y},
                    {"label": f"LassoCox AUC {lasso_auc:.3f}", "x": lasso_x, "y": lasso_y},
                ],
                "reference_line": {"label": "Chance", "x": [0.0, 1.0], "y": [0.0, 1.0]},
            }
        ],
    }

def _calibration_summary_from_rows(calibration_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for row in calibration_rows:
        group_order = _parse_int(row.get("decile"), label="calibration decile")
        n = _parse_int(row.get("n"), label=f"decile {group_order} n")
        events_5y = _parse_int(row.get("events_5y"), label=f"decile {group_order} events_5y")
        summaries.append(
            {
                "group_label": f"Decile {group_order}",
                "group_order": group_order,
                "n": n,
                "events_5y": events_5y,
                "predicted_risk_5y": _parse_float(
                    row.get("mean_predicted_risk_5y"),
                    label=f"decile {group_order} mean_predicted_risk_5y",
                ),
                "observed_risk_5y": _parse_float(
                    row.get("observed_km_risk_5y"),
                    label=f"decile {group_order} observed_km_risk_5y",
                ),
            }
        )
    if not summaries:
        raise ValueError("time-to-event discrimination/calibration payload requires non-empty calibration rows")
    return sorted(summaries, key=lambda item: item["group_order"])


def _build_discrimination_calibration_payload(
    *,
    discrimination_points: list[dict[str, Any]],
    calibration_rows: list[dict[str, str]],
    display_id: str,
    catalog_id: str,
) -> dict[str, Any]:
    calibration_summary = _calibration_summary_from_rows(calibration_rows)
    callout = max(
        calibration_summary,
        key=lambda item: abs(item["observed_risk_5y"] - item["predicted_risk_5y"]),
    )
    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
        "source_contract_path": "paper/medical_reporting_contract.json",
        "displays": [
            {
                "display_id": display_id,
                "template_id": DISCRIMINATION_CALIBRATION_REQUIREMENT_KEY,
                "catalog_id": catalog_id,
                "paper_role": "main_text",
                "title": "Time-to-event discrimination and grouped calibration",
                "caption": (
                    "Validation discrimination and grouped five-year calibration summarize the "
                    "current Cox model against its lasso comparator."
                ),
                "panel_a_title": "Validation discrimination",
                "panel_b_title": "Grouped five-year calibration",
                "discrimination_x_label": "Validation C-index",
                "calibration_x_label": "Risk decile",
                "calibration_y_label": "Five-year risk",
                "discrimination_points": discrimination_points,
                "calibration_summary": calibration_summary,
                "calibration_callout": {
                    "group_label": callout["group_label"],
                    "events_5y": callout["events_5y"],
                    "n": callout["n"],
                    "predicted_risk_5y": callout["predicted_risk_5y"],
                    "observed_risk_5y": callout["observed_risk_5y"],
                },
            }
        ],
    }

def _build_risk_group_summary_payload(
    *,
    risk_group_rows: list[dict[str, str]],
    display_id: str,
) -> dict[str, Any]:
    label_map = {"low": "Low risk", "mid": "Intermediate risk", "high": "High risk"}
    ordered_keys = ("low", "mid", "high")
    predicted_bars: list[dict[str, Any]] = []
    observed_bars: list[dict[str, Any]] = []
    risk_group_rows_by_key = {
        str(row.get("risk_group") or "").strip().casefold(): row for row in risk_group_rows
    }
    for key in ordered_keys:
        row = risk_group_rows_by_key.get(key)
        if row is None:
            raise ValueError(f"missing risk-group summary row for `{key}`")
        cases = _parse_int(row.get("n"), label=f"{key} n")
        observed_events = _parse_int(row.get("events_5y"), label=f"{key} events_5y")
        predicted_risk = _parse_float(
            row.get("mean_predicted_risk_5y"),
            label=f"{key} mean_predicted_risk_5y",
        )
        predicted_events = max(0, min(cases, int(round(predicted_risk * cases))))
        observed_bars.append(
            {"label": label_map[key], "cases": cases, "events": observed_events, "risk": observed_events / cases}
        )
        predicted_bars.append(
            {"label": label_map[key], "cases": cases, "events": predicted_events, "risk": predicted_events / cases}
        )

    for key in ("low", "mid", "high"):
        if key not in risk_group_rows_by_key:
            raise ValueError(f"risk-group summary rows must include `{key}`")
    return {
        "schema_version": 1,
        "input_schema_id": "risk_layering_monotonic_inputs_v1",
        "displays": [
            {
                "display_id": display_id,
                "template_id": display_registry.get_evidence_figure_spec(
                    "risk_layering_monotonic_bars"
                ).template_id,
                "title": "Tertile-based 5-year cardiovascular risk stratification",
                "caption": (
                    "Predicted versus observed 5-year cardiovascular risk and observed event concentration "
                    "across prespecified validation tertiles."
                ),
                "y_label": "5-year risk (%)",
                "left_panel_title": "Predicted risk by tertile",
                "left_x_label": "Predicted risk tertile",
                "left_bars": predicted_bars,
                "right_panel_title": "Observed risk by tertile",
                "right_x_label": "Observed risk tertile",
                "right_bars": observed_bars,
            }
        ],
    }

def _risk_group_summaries_from_rows(risk_group_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    label_map = {"low": "Low risk", "mid": "Intermediate risk", "high": "High risk"}
    ordered_keys = ("low", "mid", "high")
    risk_group_rows_by_key = {
        str(row.get("risk_group") or "").strip().casefold(): row for row in risk_group_rows
    }
    summaries: list[dict[str, Any]] = []
    for key in ordered_keys:
        row = risk_group_rows_by_key.get(key)
        if row is None:
            raise ValueError(f"missing risk-group summary row for `{key}`")
        summaries.append(
            {
                "label": label_map[key],
                "sample_size": _parse_int(row.get("n"), label=f"{key} n"),
                "events_5y": _parse_int(row.get("events_5y"), label=f"{key} events_5y"),
                "mean_predicted_risk_5y": _parse_float(
                    row.get("mean_predicted_risk_5y"),
                    label=f"{key} mean_predicted_risk_5y",
                ),
                "observed_km_risk_5y": _parse_float(
                    row.get("observed_km_risk_5y"),
                    label=f"{key} observed_km_risk_5y",
                ),
            }
        )
    return summaries


def _build_time_to_event_risk_group_summary_payload(
    *,
    risk_group_rows: list[dict[str, str]],
    display_id: str,
    catalog_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_grouped_inputs_v1",
        "source_contract_path": "paper/medical_reporting_contract.json",
        "displays": [
            {
                "display_id": display_id,
                "template_id": RISK_GROUP_SUMMARY_REQUIREMENT_KEY,
                "catalog_id": catalog_id,
                "paper_role": "main_text",
                "title": "Five-year risk-group summary",
                "caption": (
                    "Predicted versus observed five-year cardiovascular mortality risk across "
                    "prespecified validation risk groups."
                ),
                "panel_a_title": "Predicted and observed five-year risk",
                "panel_b_title": "Observed five-year events",
                "x_label": "Risk group",
                "y_label": "Five-year risk",
                "event_count_y_label": "Observed five-year events",
                "risk_group_summaries": _risk_group_summaries_from_rows(risk_group_rows),
            }
        ],
    }

def _build_decision_curve_payload(
    *,
    dca_rows: list[dict[str, str]],
    display_id: str,
) -> dict[str, Any]:
    thresholds = [_parse_float(row.get("threshold"), label="threshold") * 100.0 for row in dca_rows]
    model_values = [_parse_float(row.get("net_benefit_model"), label="net_benefit_model") for row in dca_rows]
    treat_all_values = [_parse_float(row.get("net_benefit_treat_all"), label="net_benefit_treat_all") for row in dca_rows]
    treated_fraction_values = [
        _parse_float(row.get("treated_fraction_model"), label="treated_fraction_model") * 100.0 for row in dca_rows
    ]
    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_decision_curve_inputs_v1",
        "displays": [
            {
                "display_id": display_id,
                "template_id": display_registry.get_evidence_figure_spec("time_to_event_decision_curve").template_id,
                "title": "Five-year decision curve",
                "caption": "Net-benefit comparison across the prespecified low-threshold clinical decision range.",
                "panel_a_title": "Decision-curve net benefit",
                "panel_b_title": "Model-treated fraction",
                "x_label": "Threshold risk (%)",
                "y_label": "Net benefit",
                "treated_fraction_y_label": "Patients classified above threshold (%)",
                "reference_line": {
                    "x": [min(thresholds), max(thresholds)],
                    "y": [0.0, 0.0],
                    "label": "Treat none",
                },
                "series": [
                    {
                        "label": "Model",
                        "x": thresholds,
                        "y": model_values,
                    },
                    {
                        "label": "Treat all",
                        "x": thresholds,
                        "y": treat_all_values,
                    },
                ],
                "treated_fraction_series": {
                    "label": "Model",
                    "x": thresholds,
                    "y": treated_fraction_values,
                },
            }
        ],
    }

def _build_multicenter_generalizability_payload(
    *,
    center_rows: list[dict[str, str]],
    geodemography_rows: list[dict[str, str]],
    display_id: str,
    catalog_id: str,
) -> dict[str, Any]:
    if not center_rows:
        raise ValueError("multicenter generalizability requires non-empty center rows")
    if not geodemography_rows:
        raise ValueError("multicenter generalizability requires non-empty geodemography rows")

    sorted_center_rows = sorted(
        center_rows,
        key=lambda row: (
            _CENTER_SPLIT_BUCKET_ORDER.get(str(row.get("split_bucket") or "").strip(), 99),
            _parse_int(row.get("center"), label="center"),
        ),
    )
    overview_rows: list[dict[str, Any]] = []
    for row in sorted_center_rows:
        split_bucket = str(row.get("split_bucket") or "").strip()
        if split_bucket not in _CENTER_SPLIT_BUCKET_ORDER:
            raise ValueError(
                f"center_event_distribution split_bucket must be `train` or `validation`, got {split_bucket!r}"
            )
        event_count = _parse_int(row.get("n_cvd_events"), label="n_cvd_events")
        support_count = _parse_int(
            row.get("n_total")
            or row.get("n_patients")
            or row.get("n")
            or row.get("count")
            or row.get("support_count")
            or event_count,
            label="center support_count",
        )
        metric_denominator = max(support_count, 1)
        overview_rows.append(
            {
                "cohort_id": _slugify(f"center_{row.get('center')}"),
                "cohort_label": _format_center_label(row.get("center")),
                "support_count": support_count,
                "event_count": event_count,
                "metric_value": round(event_count / metric_denominator, 4),
            }
        )

    region_labels = [_normalized_region_label(row.get("patient_region_raw")) for row in geodemography_rows]
    north_south_labels = [_normalized_north_south_label(row.get("patient_south_flag_raw")) for row in geodemography_rows]
    urban_rural_labels = [_normalized_urban_rural_label(row.get("patient_rural_flag_raw")) for row in geodemography_rows]
    subgroup_rows = [
        {
            "subgroup_id": _slugify(f"region_{item['label']}"),
            "subgroup_label": f"Region: {item['label']}",
            "group_n": item["count"],
            "estimate": round(item["count"] / max(len(geodemography_rows), 1), 4),
            "lower": max(round((item["count"] - 1) / max(len(geodemography_rows), 1), 4), 0.0),
            "upper": min(round((item["count"] + 1) / max(len(geodemography_rows), 1), 4), 1.0),
        }
        for item in _count_labels_preserving_first_seen_order(region_labels)[:4]
    ]

    return {
        "schema_version": 1,
        "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
        "source_contract_path": "paper/medical_reporting_contract.json",
        "displays": [
            {
                "display_id": display_id,
                "template_id": display_registry.get_evidence_figure_spec(
                    "generalizability_subgroup_composite_panel"
                ).template_id,
                "catalog_id": catalog_id,
                "paper_role": "main_text",
                "title": "Internal multicenter heterogeneity summary",
                "caption": "Center-level event support with coverage context under the frozen split.",
                "metric_family": "effect_estimate",
                "primary_label": "Center event fraction",
                "overview_panel_title": "Center-level event support",
                "overview_x_label": "Observed event fraction",
                "overview_rows": overview_rows,
                "subgroup_panel_title": "Geodemographic support distribution",
                "subgroup_x_label": "Cohort fraction",
                "subgroup_reference_value": round(1 / max(len(set(region_labels)), 1), 4),
                "subgroup_rows": subgroup_rows,
                "source_context": {
                    "region_counts": _count_labels_preserving_first_seen_order(region_labels),
                    "north_south_counts": _count_labels_in_fixed_order(
                        north_south_labels,
                        order=("South", "North"),
                    ),
                    "urban_rural_counts": _count_labels_in_fixed_order(
                        urban_rural_labels,
                        order=("Urban", "Missing", "Rural"),
                    ),
                },
            }
        ],
    }

def run_time_to_event_direct_migration(*, study_root: Path, paper_root: Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    authority_sync = _sync_authority_paper_truth(
        study_root=resolved_study_root,
        paper_root=resolved_paper_root,
    )
    written_files: list[str] = list(authority_sync.get("synced_files") or [])
    registry_payload = _load_json(resolved_paper_root / "display_registry.json")
    f1_binding = _optional_binding(
        registry_payload=registry_payload,
        requirement_key="cohort_flow_figure",
    )

    f2_requirement_key, f2_binding = _require_binding_variant(
        registry_payload=registry_payload,
        requirement_keys=F2_REQUIREMENT_KEYS,
    )
    f3_requirement_key, f3_binding = _require_binding_variant(
        registry_payload=registry_payload,
        requirement_keys=F3_REQUIREMENT_KEYS,
    )
    decision_curve_binding = _require_binding(
        registry_payload=registry_payload,
        requirement_key="time_to_event_decision_curve",
    )
    bindings = {
        "f2": f2_binding,
        "f3": f3_binding,
        "time_to_event_decision_curve": decision_curve_binding,
    }
    f5_requirement_key, f5_binding = _require_f5_binding_variant(registry_payload=registry_payload)
    if (
        f5_requirement_key == TRANSPORTABILITY_GOVERNANCE_REQUIREMENT_KEY
        and current_transportability_layout_available(study_root=resolved_study_root)
    ) or (
        f5_requirement_key == "center_transportability_governance_summary_panel"
        and current_transportability_layout_available(study_root=resolved_study_root)
    ):
        blockers: list[str] = []
        current_layout_result = run_current_transportability_layout_migration(
            study_root=resolved_study_root,
            paper_root=resolved_paper_root,
            bindings=bindings,
            binding_requirement_keys={
                "f2": f2_requirement_key,
                "f3": f3_requirement_key,
            },
            f5_binding=f5_binding,
            f5_requirement_key=f5_requirement_key,
            f1_binding=f1_binding,
        )
        written_files.extend(current_layout_result["written_files"])
        report_path = resolved_paper_root / "direct_migration" / "time_to_event_direct_migration_report.json"
        report = {
            "status": "blocked" if blockers else "synced",
            "recorded_at": _utc_now(),
            "study_root": str(resolved_study_root),
            "paper_root": str(resolved_paper_root),
            "written_files": written_files,
            "blockers": blockers,
            "authority_sync": authority_sync,
            "source_paths": current_layout_result["source_paths"],
            "notes": current_layout_result["notes"],
        }
        _write_json(report_path, report)
        written_files.append(str(report_path))
        report["written_files"] = written_files
        report["report_path"] = str(report_path)
        return report

    primary_derived_root = (
        resolved_study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived"
    )
    primary_endpoint_root = resolved_study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint"
    entry_validation_root = (
        resolved_study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "derived"
    )

    discrimination_points = _load_validation_discrimination_points(primary_endpoint_root / "discrimination_report.md")
    prediction_rows = _load_csv_rows(primary_derived_root / "coxph_validation_predictions.csv")
    lasso_rows = _load_csv_rows(primary_derived_root / "lassocox_validation_predictions.csv")
    calibration_rows = _load_csv_rows(primary_derived_root / "coxph_calibration_5y.csv")
    risk_group_rows = _load_csv_rows(primary_derived_root / "coxph_km_risk_groups_5y.csv")
    dca_rows = _load_csv_rows(primary_derived_root / "coxph_dca_5y.csv")
    center_rows: list[dict[str, str]] = []
    geodemography_rows: list[dict[str, str]] = []
    if f5_requirement_key == MULTICENTER_GENERALIZABILITY_REQUIREMENT_KEY:
        center_rows = _load_csv_rows(entry_validation_root / "center_event_distribution.csv")
        geodemography_rows = _load_csv_rows(entry_validation_root / "formal_modeling_geodemography_support.csv")
        if not center_rows:
            raise ValueError("center_event_distribution.csv must not be empty")

    blockers: list[str] = []

    if f2_requirement_key == DISCRIMINATION_CALIBRATION_REQUIREMENT_KEY:
        discrimination_payload = _build_discrimination_calibration_payload(
            discrimination_points=discrimination_points,
            calibration_rows=calibration_rows,
            display_id=f2_binding["display_id"],
            catalog_id=f2_binding["catalog_id"],
        )
        discrimination_path = resolved_paper_root / "time_to_event_discrimination_calibration_inputs.json"
    else:
        discrimination_payload = _build_time_dependent_roc_payload(
            prediction_rows=prediction_rows,
            lasso_rows=lasso_rows,
            display_id=f2_binding["display_id"],
        )
        discrimination_path = resolved_paper_root / "binary_prediction_curve_inputs.json"
    _write_json(discrimination_path, discrimination_payload)
    written_files.append(str(discrimination_path))

    if f3_requirement_key == RISK_GROUP_SUMMARY_REQUIREMENT_KEY:
        grouped_payload = _build_time_to_event_risk_group_summary_payload(
            risk_group_rows=risk_group_rows,
            display_id=f3_binding["display_id"],
            catalog_id=f3_binding["catalog_id"],
        )
        grouped_path = resolved_paper_root / "time_to_event_grouped_inputs.json"
    else:
        grouped_payload = _build_risk_group_summary_payload(
            risk_group_rows=risk_group_rows,
            display_id=f3_binding["display_id"],
        )
        grouped_path = resolved_paper_root / "risk_layering_monotonic_inputs.json"
    _write_json(grouped_path, grouped_payload)
    written_files.append(str(grouped_path))

    decision_curve_payload = _build_decision_curve_payload(
        dca_rows=dca_rows,
        display_id=decision_curve_binding["display_id"],
    )
    decision_curve_path = resolved_paper_root / "time_to_event_decision_curve_inputs.json"
    _write_json(decision_curve_path, decision_curve_payload)
    written_files.append(str(decision_curve_path))

    report_notes: dict[str, Any] = {}
    if f5_requirement_key == MULTICENTER_GENERALIZABILITY_REQUIREMENT_KEY:
        multicenter_generalizability_payload = _build_multicenter_generalizability_payload(
            center_rows=center_rows,
            geodemography_rows=geodemography_rows,
            display_id=f5_binding["display_id"],
            catalog_id=f5_binding["catalog_id"],
        )
        multicenter_generalizability_path = resolved_paper_root / "generalizability_subgroup_composite_inputs.json"
        _write_json(multicenter_generalizability_path, multicenter_generalizability_payload)
        written_files.append(str(multicenter_generalizability_path))
    else:
        report_notes["transportability_governance_binding"] = "current_contract_preserved"
    report_notes["f2_requirement_key"] = f2_requirement_key
    report_notes["f3_requirement_key"] = f3_requirement_key
    report_notes["f5_requirement_key"] = f5_requirement_key

    cohort_flow_payload = _load_json(resolved_paper_root / "cohort_flow.json")
    table2_header, table2_rows = _load_markdown_table(resolved_paper_root / "tables" / "table2_performance_summary.md")
    submission_graphical_abstract_payload = _build_submission_graphical_abstract_payload(
        cohort_flow_payload=cohort_flow_payload,
        table2_header=table2_header,
        table2_rows=table2_rows,
    )
    submission_graphical_abstract_path = resolved_paper_root / "submission_graphical_abstract.json"
    _write_json(submission_graphical_abstract_path, submission_graphical_abstract_payload)
    written_files.append(str(submission_graphical_abstract_path))

    report_path = resolved_paper_root / "direct_migration" / "time_to_event_direct_migration_report.json"
    report = {
        "status": "blocked" if blockers else "synced",
        "recorded_at": _utc_now(),
        "study_root": str(resolved_study_root),
        "paper_root": str(resolved_paper_root),
        "written_files": written_files,
        "blockers": blockers,
        "authority_sync": authority_sync,
        "source_paths": {
            "discrimination_report": str(primary_endpoint_root / "discrimination_report.md"),
            "coxph_calibration_5y": str(primary_derived_root / "coxph_calibration_5y.csv"),
            "coxph_km_risk_groups_5y": str(primary_derived_root / "coxph_km_risk_groups_5y.csv"),
            "decision_curve_csv": str(primary_derived_root / "coxph_dca_5y.csv"),
            "center_event_distribution": (
                str(entry_validation_root / "center_event_distribution.csv")
                if f5_requirement_key == MULTICENTER_GENERALIZABILITY_REQUIREMENT_KEY
                else None
            ),
            "formal_modeling_geodemography_support": (
                str(entry_validation_root / "formal_modeling_geodemography_support.csv")
                if f5_requirement_key == MULTICENTER_GENERALIZABILITY_REQUIREMENT_KEY
                else None
            ),
            "cohort_flow": str(resolved_paper_root / "cohort_flow.json"),
            "table2_markdown": str(resolved_paper_root / "tables" / "table2_performance_summary.md"),
        },
        "notes": report_notes,
    }
    _write_json(report_path, report)
    written_files.append(str(report_path))
    report["written_files"] = written_files
    report["report_path"] = str(report_path)
    return report
