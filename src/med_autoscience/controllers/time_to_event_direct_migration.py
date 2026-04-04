from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any


_REQUIRED_DISPLAY_KEYS = {
    "time_to_event_discrimination_calibration_panel": ("time_to_event_discrimination_calibration_inputs.json", "time_to_event_discrimination_calibration_inputs_v1"),
    "kaplan_meier_grouped": ("time_to_event_grouped_inputs.json", "time_to_event_grouped_inputs_v1"),
    "time_to_event_decision_curve": ("time_to_event_decision_curve_inputs.json", "time_to_event_decision_curve_inputs_v1"),
    "multicenter_generalizability_overview": ("multicenter_generalizability_inputs.json", "multicenter_generalizability_inputs_v1"),
    "table2_time_to_event_performance_summary": ("time_to_event_performance_summary.json", "time_to_event_performance_summary_v1"),
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"missing required CSV file: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"missing CSV headers: {path}")
        return [dict(row) for row in reader]


def _require_binding(
    *,
    registry_payload: dict[str, Any],
    requirement_key: str,
) -> dict[str, str]:
    displays = registry_payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError("display_registry.json missing displays list")
    for item in displays:
        if not isinstance(item, dict):
            continue
        if str(item.get("requirement_key") or "").strip() != requirement_key:
            continue
        display_id = str(item.get("display_id") or "").strip()
        catalog_id = str(item.get("catalog_id") or "").strip()
        display_kind = str(item.get("display_kind") or "").strip()
        if not display_id or not catalog_id or not display_kind:
            raise ValueError(f"display binding for {requirement_key} is incomplete")
        return {
            "display_id": display_id,
            "catalog_id": catalog_id,
            "display_kind": display_kind,
        }
    raise ValueError(f"missing required display binding: {requirement_key}")


def _parse_float(raw_value: object, *, label: str) -> float:
    try:
        return float(str(raw_value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid numeric value for {label}: {raw_value!r}") from exc


def _parse_int(raw_value: object, *, label: str) -> int:
    try:
        return int(str(raw_value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer value for {label}: {raw_value!r}") from exc


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    normalized = normalized.strip("_")
    return normalized or "item"


def _load_markdown_table(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.exists():
        raise FileNotFoundError(f"missing required markdown table: {path}")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
    if len(table_lines) < 3:
        raise ValueError(f"markdown table not found in {path}")

    def parse_row(line: str) -> list[str]:
        return [cell.strip() for cell in line.strip("|").split("|")]

    header = parse_row(table_lines[0])
    rows = [parse_row(line) for line in table_lines[2:]]
    return header, rows


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


def _build_discrimination_payload(
    *,
    cox_rows: list[dict[str, str]],
    lasso_rows: list[dict[str, str]],
    display_id: str,
) -> dict[str, Any]:
    horizon_years = 5.0
    lasso_score_by_sequence = {
        str(row.get("Sequnece") or "").strip(): _parse_float(row.get("risk_score"), label="lassocox.risk_score")
        for row in lasso_rows
    }
    cox_scores: list[float] = []
    lasso_scores: list[float] = []
    labels: list[int] = []
    for row in cox_rows:
        sequence = str(row.get("Sequnece") or "").strip()
        if not _is_evaluable_fixed_horizon(row, horizon_years=horizon_years):
            continue
        if sequence not in lasso_score_by_sequence:
            raise ValueError(f"lassocox validation predictions missing sequence {sequence}")
        cox_scores.append(_parse_float(row.get("predicted_risk_5y"), label="coxph.predicted_risk_5y"))
        lasso_scores.append(lasso_score_by_sequence[sequence])
        labels.append(1 if _event_by_horizon(row, horizon_years=horizon_years) else 0)

    cox_x, cox_y, cox_auc = _build_roc_curve(cox_scores, labels)
    lasso_x, lasso_y, lasso_auc = _build_roc_curve(lasso_scores, labels)
    calibration_group_rows: dict[str, list[dict[str, str]]] = {"1": [], "5": [], "10": []}
    for row in cox_rows:
        decile = str(row.get("calibration_decile") or "").strip()
        if decile in calibration_group_rows:
            calibration_group_rows[decile].append(row)

    calibration_groups = []
    for decile in ("1", "5", "10"):
        times, values = _build_kaplan_meier_curve(calibration_group_rows[decile], horizon_years=horizon_years)
        calibration_groups.append(
            {
                "label": f"Decile {decile}",
                "times": times,
                "values": values,
            }
        )

    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
        "displays": [
            {
                "display_id": display_id,
                "template_id": "time_to_event_discrimination_calibration_panel",
                "title": "Five-year discrimination and grouped event-free curves",
                "caption": (
                    "Fixed-horizon discrimination for CoxPH and LassoCox with decile-stratified "
                    "event-free survival support in the validation cohort."
                ),
                "discrimination_x_label": "1 - Specificity",
                "discrimination_y_label": "Sensitivity",
                "calibration_x_label": "Follow-up time (years)",
                "calibration_y_label": "Event-free probability",
                "discrimination_reference_line": {
                    "x": [0.0, 1.0],
                    "y": [0.0, 1.0],
                    "label": "Chance",
                },
                "discrimination_series": [
                    {
                        "label": "CoxPH",
                        "x": cox_x,
                        "y": cox_y,
                        "annotation": f"AUC = {cox_auc:.3f}",
                    },
                    {
                        "label": "LassoCox",
                        "x": lasso_x,
                        "y": lasso_y,
                        "annotation": f"AUC = {lasso_auc:.3f}",
                    },
                ],
                "calibration_groups": calibration_groups,
            }
        ],
    }


def _build_grouped_km_payload(
    *,
    cox_rows: list[dict[str, str]],
    display_id: str,
) -> dict[str, Any]:
    horizon_years = 5.0
    group_rows: dict[str, list[dict[str, str]]] = {"low": [], "mid": [], "high": []}
    label_map = {"low": "Low risk", "mid": "Intermediate risk", "high": "High risk"}
    for row in cox_rows:
        key = str(row.get("risk_tertile") or "").strip()
        if key in group_rows:
            group_rows[key].append(row)
    groups = []
    for key in ("low", "mid", "high"):
        times, values = _build_kaplan_meier_curve(group_rows[key], horizon_years=horizon_years)
        groups.append({"label": label_map[key], "times": times, "values": values})
    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_grouped_inputs_v1",
        "displays": [
            {
                "display_id": display_id,
                "template_id": "kaplan_meier_grouped",
                "title": "Risk-group Kaplan-Meier curves",
                "caption": "Five-year event-free survival separation across prespecified validation risk tertiles.",
                "x_label": "Follow-up time (years)",
                "y_label": "Event-free probability",
                "annotation": "Prespecified tertile stratification",
                "groups": groups,
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
    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_decision_curve_inputs_v1",
        "displays": [
            {
                "display_id": display_id,
                "template_id": "time_to_event_decision_curve",
                "title": "Five-year decision curve",
                "caption": "Net-benefit comparison across the prespecified low-threshold clinical decision range.",
                "x_label": "Threshold risk (%)",
                "y_label": "Net benefit",
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
            }
        ],
    }


def _build_table2_payload(
    *,
    table_markdown_path: Path,
    display_id: str,
) -> dict[str, Any]:
    header, rows = _load_markdown_table(table_markdown_path)
    if len(header) < 2:
        raise ValueError(f"table markdown must contain at least one data column: {table_markdown_path}")
    columns = [
        {
            "column_id": _slugify(label),
            "label": label,
        }
        for label in header[1:]
    ]
    normalized_rows = []
    for raw_row in rows:
        if len(raw_row) != len(header):
            raise ValueError(f"row length mismatch in {table_markdown_path}")
        normalized_rows.append(
            {
                "row_id": _slugify(raw_row[0]),
                "label": raw_row[0],
                "values": raw_row[1:],
            }
        )
    return {
        "schema_version": 1,
        "table_shell_id": "table2_time_to_event_performance_summary",
        "display_id": display_id,
        "title": "Fixed-horizon performance summary",
        "columns": columns,
        "rows": normalized_rows,
    }


def run_time_to_event_direct_migration(*, study_root: Path, paper_root: Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    registry_payload = _load_json(resolved_paper_root / "display_registry.json")

    bindings = {
        key: _require_binding(registry_payload=registry_payload, requirement_key=key)
        for key in _REQUIRED_DISPLAY_KEYS
    }

    primary_derived_root = (
        resolved_study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived"
    )
    entry_validation_root = (
        resolved_study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "derived"
    )

    cox_rows = _load_csv_rows(primary_derived_root / "coxph_validation_predictions.csv")
    lasso_rows = _load_csv_rows(primary_derived_root / "lassocox_validation_predictions.csv")
    dca_rows = _load_csv_rows(primary_derived_root / "coxph_dca_5y.csv")
    center_rows = _load_csv_rows(entry_validation_root / "center_event_distribution.csv")
    if not center_rows:
        raise ValueError("center_event_distribution.csv must not be empty")

    written_files: list[str] = []
    blockers: list[str] = []

    discrimination_payload = _build_discrimination_payload(
        cox_rows=cox_rows,
        lasso_rows=lasso_rows,
        display_id=bindings["time_to_event_discrimination_calibration_panel"]["display_id"],
    )
    discrimination_path = resolved_paper_root / "time_to_event_discrimination_calibration_inputs.json"
    _write_json(discrimination_path, discrimination_payload)
    written_files.append(str(discrimination_path))

    grouped_payload = _build_grouped_km_payload(
        cox_rows=cox_rows,
        display_id=bindings["kaplan_meier_grouped"]["display_id"],
    )
    grouped_path = resolved_paper_root / "time_to_event_grouped_inputs.json"
    _write_json(grouped_path, grouped_payload)
    written_files.append(str(grouped_path))

    decision_curve_payload = _build_decision_curve_payload(
        dca_rows=dca_rows,
        display_id=bindings["time_to_event_decision_curve"]["display_id"],
    )
    decision_curve_path = resolved_paper_root / "time_to_event_decision_curve_inputs.json"
    _write_json(decision_curve_path, decision_curve_payload)
    written_files.append(str(decision_curve_path))

    table2_payload = _build_table2_payload(
        table_markdown_path=resolved_paper_root / "tables" / "table2_performance_summary.md",
        display_id=bindings["table2_time_to_event_performance_summary"]["display_id"],
    )
    table2_path = resolved_paper_root / "time_to_event_performance_summary.json"
    _write_json(table2_path, table2_payload)
    written_files.append(str(table2_path))

    blockers.append("multicenter_generalizability_template_gap")
    report_path = resolved_paper_root / "direct_migration" / "time_to_event_direct_migration_report.json"
    report = {
        "status": "blocked" if blockers else "synced",
        "recorded_at": _utc_now(),
        "study_root": str(resolved_study_root),
        "paper_root": str(resolved_paper_root),
        "written_files": written_files,
        "blockers": blockers,
        "source_paths": {
            "coxph_validation_predictions": str(primary_derived_root / "coxph_validation_predictions.csv"),
            "lassocox_validation_predictions": str(primary_derived_root / "lassocox_validation_predictions.csv"),
            "decision_curve_csv": str(primary_derived_root / "coxph_dca_5y.csv"),
            "center_event_distribution": str(entry_validation_root / "center_event_distribution.csv"),
            "table2_markdown": str(resolved_paper_root / "tables" / "table2_performance_summary.md"),
        },
        "notes": {
            "multicenter_generalizability": (
                "Current audited template expects per-center estimate/lower/upper intervals, but the study surface "
                "currently exposes center event-count and geodemography coverage evidence instead of a compatible "
                "interval-based generalizability payload."
            )
        },
    }
    _write_json(report_path, report)
    written_files.append(str(report_path))
    report["written_files"] = written_files
    report["report_path"] = str(report_path)
    return report
