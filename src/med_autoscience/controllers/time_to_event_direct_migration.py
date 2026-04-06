from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import re
import shutil
from pathlib import Path
from typing import Any

from med_autoscience.policies import medical_reporting_contract as medical_reporting_contract_policy


_REQUIRED_DISPLAY_KEYS = {
    "time_to_event_discrimination_calibration_panel": ("time_to_event_discrimination_calibration_inputs.json", "time_to_event_discrimination_calibration_inputs_v1"),
    "time_to_event_risk_group_summary": ("time_to_event_grouped_inputs.json", "time_to_event_grouped_inputs_v1"),
    "time_to_event_decision_curve": ("time_to_event_decision_curve_inputs.json", "time_to_event_decision_curve_inputs_v1"),
    "multicenter_generalizability_overview": ("multicenter_generalizability_inputs.json", "multicenter_generalizability_inputs_v1"),
    "table2_time_to_event_performance_summary": ("time_to_event_performance_summary.json", "time_to_event_performance_summary_v1"),
}
_LEGACY_REQUIREMENT_KEY_ALIASES = {
    "time_to_event_risk_group_summary": ("kaplan_meier_grouped",),
}
_AUTHORITY_PAPER_SYNC_RELATIVE_PATHS = (
    "publication_style_profile.json",
    "display_overrides.json",
    "display_registry.json",
    "medical_reporting_contract.json",
    "methods_implementation_manifest.json",
    "results_narrative_map.json",
    "figure_semantics_manifest.json",
    "derived_analysis_manifest.json",
    "manuscript_safe_reproducibility_supplement.json",
    "endpoint_provenance_note.md",
    "draft.md",
    "cohort_flow.json",
    "submission_graphical_abstract.json",
    "tables/table2_performance_summary.md",
)


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


def _resolve_authority_paper_root(*, study_root: Path) -> Path | None:
    candidate = study_root / "paper"
    if not candidate.exists():
        return None
    return candidate


def _same_file_contents(*, source_path: Path, target_path: Path) -> bool:
    if not target_path.exists():
        return False
    return source_path.read_bytes() == target_path.read_bytes()


def _sync_authority_paper_truth(
    *,
    study_root: Path,
    paper_root: Path,
) -> dict[str, Any]:
    authority_paper_root = _resolve_authority_paper_root(study_root=study_root)
    summary: dict[str, Any] = {
        "status": "not_available",
        "source_paper_root": str(authority_paper_root) if authority_paper_root is not None else None,
        "target_paper_root": str(paper_root),
        "synced_files": [],
        "already_aligned": [],
        "missing_authority_files": [],
    }
    if authority_paper_root is None:
        return summary
    if authority_paper_root == paper_root:
        summary["status"] = "same_root"
        return summary

    synced_files: list[str] = []
    already_aligned: list[str] = []
    missing_authority_files: list[str] = []
    for relative_path in _AUTHORITY_PAPER_SYNC_RELATIVE_PATHS:
        source_path = authority_paper_root / relative_path
        if not source_path.exists():
            missing_authority_files.append(relative_path)
            continue
        target_path = paper_root / relative_path
        if _same_file_contents(source_path=source_path, target_path=target_path):
            already_aligned.append(relative_path)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        synced_files.append(str(target_path))

    summary["status"] = "synced" if synced_files else "already_aligned"
    summary["synced_files"] = synced_files
    summary["already_aligned"] = already_aligned
    summary["missing_authority_files"] = missing_authority_files
    return summary


def _normalize_required_display_registry(*, registry_payload: dict[str, Any]) -> bool:
    displays = registry_payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError("display_registry.json missing displays list")
    updated = False
    for item in displays:
        if not isinstance(item, dict):
            continue
        raw_requirement_key = str(item.get("requirement_key") or "").strip()
        if not raw_requirement_key:
            continue
        for canonical_key, aliases in _LEGACY_REQUIREMENT_KEY_ALIASES.items():
            if raw_requirement_key not in aliases:
                continue
            item["requirement_key"] = canonical_key
            updated = True
            break
    return updated


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


def _build_discrimination_payload(
    *,
    discrimination_points: list[dict[str, Any]],
    calibration_rows: list[dict[str, str]],
    display_id: str,
) -> dict[str, Any]:
    calibration_summary: list[dict[str, Any]] = []
    for row in calibration_rows:
        decile = _parse_int(row.get("decile"), label="decile")
        calibration_summary.append(
            {
                "group_label": f"Decile {decile}",
                "group_order": decile,
                "n": _parse_int(row.get("n"), label=f"calibration decile {decile} n"),
                "events_5y": _parse_int(
                    row.get("events_5y"),
                    label=f"calibration decile {decile} events_5y",
                ),
                "predicted_risk_5y": _parse_float(
                    row.get("mean_predicted_risk_5y"),
                    label=f"calibration decile {decile} mean_predicted_risk_5y",
                ),
                "observed_risk_5y": _parse_float(
                    row.get("observed_km_risk_5y"),
                    label=f"calibration decile {decile} observed_km_risk_5y",
                ),
            }
        )
    calibration_summary.sort(key=lambda item: int(item["group_order"]))
    if not calibration_summary:
        raise ValueError("grouped calibration summary requires non-empty calibration rows")
    highest_decile = calibration_summary[-1]

    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
        "displays": [
            {
                "display_id": display_id,
                "template_id": "time_to_event_discrimination_calibration_panel",
                "title": "Validation discrimination and grouped calibration for 5-year cardiovascular mortality",
                "caption": (
                    "Validation discrimination remained strong, and grouped 5-year calibration showed "
                    "underprediction in the highest risk decile."
                ),
                "panel_a_title": "Validation discrimination",
                "panel_b_title": "Grouped 5-year calibration",
                "discrimination_x_label": "Validation C-index",
                "calibration_x_label": "Risk decile",
                "calibration_y_label": "5-year risk (%)",
                "discrimination_points": discrimination_points,
                "calibration_summary": calibration_summary,
                "calibration_callout": {
                    "group_label": highest_decile["group_label"],
                    "predicted_risk_5y": highest_decile["predicted_risk_5y"],
                    "observed_risk_5y": highest_decile["observed_risk_5y"],
                    "events_5y": highest_decile["events_5y"],
                    "n": highest_decile["n"],
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
    risk_group_summaries: list[dict[str, Any]] = []
    risk_group_rows_by_key = {
        str(row.get("risk_group") or "").strip().casefold(): row for row in risk_group_rows
    }
    for key in ordered_keys:
        row = risk_group_rows_by_key.get(key)
        if row is None:
            raise ValueError(f"missing risk-group summary row for `{key}`")
        risk_group_summaries.append(
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

    for key in ("low", "mid", "high"):
        if key not in risk_group_rows_by_key:
            raise ValueError(f"risk-group summary rows must include `{key}`")
    return {
        "schema_version": 1,
        "input_schema_id": "time_to_event_grouped_inputs_v1",
        "displays": [
            {
                "display_id": display_id,
                "template_id": "time_to_event_risk_group_summary",
                "title": "Tertile-based 5-year cardiovascular risk stratification",
                "caption": (
                    "Predicted versus observed 5-year cardiovascular risk and observed event concentration "
                    "across prespecified validation tertiles."
                ),
                "panel_a_title": "Predicted and observed risk by tertile",
                "panel_b_title": "Event concentration across tertiles",
                "x_label": "Risk tertile",
                "y_label": "5-year risk (%)",
                "event_count_y_label": "Observed 5-year events",
                "risk_group_summaries": risk_group_summaries,
            }
        ],
    }


def _row_map_from_markdown_table(*, header: list[str], rows: list[list[str]], label_column: str) -> dict[str, dict[str, str]]:
    normalized_header = {value.strip().casefold(): index for index, value in enumerate(header)}
    if label_column.casefold() not in normalized_header:
        raise ValueError(f"missing required markdown table column `{label_column}`")
    label_index = normalized_header[label_column.casefold()]
    row_map: dict[str, dict[str, str]] = {}
    for row_index, row in enumerate(rows):
        if len(row) != len(header):
            raise ValueError(f"markdown table row length mismatch at row {row_index + 1}")
        key = row[label_index].strip()
        if not key:
            raise ValueError(f"markdown table row {row_index + 1} missing `{label_column}` value")
        row_map[key] = {header[column_index].strip(): value.strip() for column_index, value in enumerate(row)}
    return row_map


def _extract_regex_group(*, text: str, pattern: str, label: str) -> tuple[str, ...]:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        raise ValueError(f"unable to parse `{label}` from markdown row: {text}")
    return tuple(group.strip() for group in match.groups())


def _build_submission_graphical_abstract_payload(
    *,
    cohort_flow_payload: dict[str, Any],
    table2_header: list[str],
    table2_rows: list[list[str]],
) -> dict[str, Any]:
    def endpoint_count(endpoint: dict[str, Any]) -> int:
        raw_value = endpoint.get("n")
        if raw_value is None:
            raw_value = endpoint.get("event_n")
        return int(raw_value)

    steps = list(cohort_flow_payload.get("steps") or [])
    endpoint_inventory = list(cohort_flow_payload.get("endpoint_inventory") or [])
    if len(steps) < 3:
        raise ValueError("submission graphical abstract requires at least three cohort flow steps")

    analytic_cohort = steps[-3]
    derivation_split = steps[-2]
    validation_split = steps[-1]

    endpoint_by_label = {
        str(item.get("label") or "").strip().casefold(): item
        for item in endpoint_inventory
        if isinstance(item, dict) and str(item.get("label") or "").strip()
    }
    cvd_endpoint = next(
        (
            item
            for label, item in endpoint_by_label.items()
            if "cardiovascular" in label and "mortality" in label
        ),
        None,
    )
    all_cause_endpoint = next(
        (
            item
            for label, item in endpoint_by_label.items()
            if "all-cause" in label and "mortality" in label
        ),
        None,
    )
    if cvd_endpoint is None or all_cause_endpoint is None:
        raise ValueError("submission graphical abstract requires cardiovascular and all-cause endpoint inventory rows")

    table_rows = _row_map_from_markdown_table(header=table2_header, rows=table2_rows, label_column="Endpoint")
    primary_row = table_rows.get("Cardiovascular mortality")
    supportive_row = table_rows.get("All-cause mortality")
    if primary_row is None or supportive_row is None:
        raise ValueError("submission graphical abstract requires cardiovascular and all-cause rows in table2")

    primary_cindex_ridge, primary_cindex_lasso = _extract_regex_group(
        text=str(primary_row.get("C-index") or ""),
        pattern=r"Ridge\s+([0-9.]+).*?lasso\s+([0-9.]+)",
        label="primary C-index pair",
    )
    primary_high_risk_events, primary_observed_events, primary_dca_window = _extract_regex_group(
        text=str(primary_row.get("Stratification / utility") or ""),
        pattern=r"High-risk tertile:\s*([0-9]+)\s*/\s*([0-9]+)\s*events.*?positive DCA at\s*([0-9.\-%]+)\s*thresholds",
        label="primary stratification summary",
    )
    supportive_cindex = _extract_regex_group(
        text=str(supportive_row.get("C-index") or ""),
        pattern=r"Supportive Cox line\s+([0-9.]+)",
        label="supportive C-index",
    )[0]
    supportive_tertiles = _extract_regex_group(
        text=str(supportive_row.get("Stratification / utility") or ""),
        pattern=r"Observed 5-year risk across tertiles:\s*([0-9.]+%)\s*,\s*([0-9.]+%)\s*,\s*([0-9.]+%)",
        label="supportive tertile summary",
    )

    return {
        "schema_version": 1,
        "shell_id": "submission_graphical_abstract",
        "display_id": "submission_graphical_abstract",
        "catalog_id": "GA1",
        "paper_role": "submission_companion",
        "title": "Graphical abstract for internal cardiovascular mortality risk stratification",
        "caption": (
            "A submission-companion overview summarizes cohort assembly, the primary 5-year cardiovascular "
            "mortality result, the supportive all-cause endpoint, and the internal multicenter applicability "
            "boundary without adding new evidence."
        ),
        "panels": [
            {
                "panel_id": "cohort_split",
                "panel_label": "A",
                "title": "Cohort and split",
                "subtitle": "Chinese multicenter diabetes cohort",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "analytic_cohort",
                                "title": "Analytic cohort",
                                "value": f"{int(analytic_cohort['n']):,}",
                                "detail": "Formal modeling cohort after endpoint-completeness screening",
                                "accent_role": "neutral",
                            }
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "cvd_deaths",
                                "title": "Cardiovascular deaths",
                                "value": f"{endpoint_count(cvd_endpoint):,}",
                                "detail": "Primary endpoint",
                                "accent_role": "primary",
                            },
                            {
                                "card_id": "all_cause_deaths",
                                "title": "All-cause deaths",
                                "value": f"{endpoint_count(all_cause_endpoint):,}",
                                "detail": "Supportive endpoint",
                                "accent_role": "secondary",
                            },
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "derivation_split",
                                "title": "Derivation",
                                "value": f"{int(derivation_split['n']):,}",
                                "detail": str(derivation_split.get("detail") or ""),
                                "accent_role": "neutral",
                            },
                            {
                                "card_id": "validation_split",
                                "title": "Validation",
                                "value": f"{int(validation_split['n']):,}",
                                "detail": str(validation_split.get("detail") or ""),
                                "accent_role": "neutral",
                            },
                        ]
                    },
                ],
            },
            {
                "panel_id": "primary_endpoint",
                "panel_label": "B",
                "title": "Primary 5-year endpoint",
                "subtitle": "Cardiovascular mortality",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "ridge_cindex",
                                "title": "Ridge Cox validation C-index",
                                "value": primary_cindex_ridge,
                                "detail": f"Lasso comparator {primary_cindex_lasso}",
                                "accent_role": "primary",
                            },
                            {
                                "card_id": "lasso_cindex",
                                "title": "Lasso Cox",
                                "value": primary_cindex_lasso,
                                "detail": "Same frozen validation split",
                                "accent_role": "secondary",
                            },
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "high_risk_events",
                                "title": "Observed 5-year events in the high-risk tertile",
                                "value": f"{primary_high_risk_events} / {primary_observed_events}",
                                "detail": "Marked event concentration in the highest tertile",
                                "accent_role": "primary",
                            }
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "decision_curve_window",
                                "title": "Decision-curve net-benefit range",
                                "value": primary_dca_window,
                                "detail": "Clinically relevant low-threshold window",
                                "accent_role": "audit",
                            }
                        ]
                    },
                ],
            },
            {
                "panel_id": "supportive_context",
                "panel_label": "C",
                "title": "Supportive context",
                "subtitle": "All-cause endpoint and internal applicability",
                "rows": [
                    {
                        "cards": [
                            {
                                "card_id": "supportive_cindex",
                                "title": "Supportive all-cause Cox C-index",
                                "value": supportive_cindex,
                                "detail": f"Observed 5-year tertiles {' | '.join(supportive_tertiles)}",
                                "accent_role": "secondary",
                            }
                        ]
                    },
                    {
                        "cards": [
                            {
                                "card_id": "internal_boundary",
                                "title": "Applicability boundary",
                                "value": "Internal validation only",
                                "detail": "Multicenter support inside the current cohort",
                                "accent_role": "contrast",
                            },
                            {
                                "card_id": "transportability_boundary",
                                "title": "Transportability boundary",
                                "value": "No external validation",
                                "detail": "Do not expand beyond the audited cohort",
                                "accent_role": "audit",
                            },
                        ]
                    },
                ],
            },
        ],
        "footer_pills": [
            {
                "pill_id": "internal_validation_only",
                "panel_id": "cohort_split",
                "label": "Internal validation only",
                "style_role": "neutral",
            },
            {
                "pill_id": "supportive_endpoint_only",
                "panel_id": "primary_endpoint",
                "label": "All-cause endpoint is supportive",
                "style_role": "secondary",
            },
            {
                "pill_id": "no_external_validation",
                "panel_id": "supportive_context",
                "label": "No external validation",
                "style_role": "audit",
            },
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
                "template_id": "time_to_event_decision_curve",
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
    authority_sync = _sync_authority_paper_truth(
        study_root=resolved_study_root,
        paper_root=resolved_paper_root,
    )
    written_files: list[str] = list(authority_sync.get("synced_files") or [])
    medical_reporting_contract_path = resolved_paper_root / "medical_reporting_contract.json"
    if medical_reporting_contract_path.exists():
        medical_reporting_contract_payload = _load_json(medical_reporting_contract_path)
        medical_reporting_contract_updated = medical_reporting_contract_policy.normalize_legacy_requirement_keys(
            medical_reporting_contract_payload
        )
        if medical_reporting_contract_updated:
            _write_json(medical_reporting_contract_path, medical_reporting_contract_payload)
            written_files.append(str(medical_reporting_contract_path))
    registry_payload = _load_json(resolved_paper_root / "display_registry.json")
    registry_updated = _normalize_required_display_registry(registry_payload=registry_payload)
    if registry_updated:
        _write_json(resolved_paper_root / "display_registry.json", registry_payload)
        written_files.append(str(resolved_paper_root / "display_registry.json"))

    bindings = {
        key: _require_binding(registry_payload=registry_payload, requirement_key=key)
        for key in _REQUIRED_DISPLAY_KEYS
    }

    primary_derived_root = (
        resolved_study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint" / "derived"
    )
    primary_endpoint_root = resolved_study_root / "analysis" / "clean_room_execution" / "10_china_primary_endpoint"
    entry_validation_root = (
        resolved_study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "derived"
    )

    discrimination_points = _load_validation_discrimination_points(primary_endpoint_root / "discrimination_report.md")
    calibration_rows = _load_csv_rows(primary_derived_root / "coxph_calibration_5y.csv")
    risk_group_rows = _load_csv_rows(primary_derived_root / "coxph_km_risk_groups_5y.csv")
    dca_rows = _load_csv_rows(primary_derived_root / "coxph_dca_5y.csv")
    center_rows = _load_csv_rows(entry_validation_root / "center_event_distribution.csv")
    if not center_rows:
        raise ValueError("center_event_distribution.csv must not be empty")

    blockers: list[str] = []

    discrimination_payload = _build_discrimination_payload(
        discrimination_points=discrimination_points,
        calibration_rows=calibration_rows,
        display_id=bindings["time_to_event_discrimination_calibration_panel"]["display_id"],
    )
    discrimination_path = resolved_paper_root / "time_to_event_discrimination_calibration_inputs.json"
    _write_json(discrimination_path, discrimination_payload)
    written_files.append(str(discrimination_path))

    grouped_payload = _build_risk_group_summary_payload(
        risk_group_rows=risk_group_rows,
        display_id=bindings["time_to_event_risk_group_summary"]["display_id"],
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

    blockers.append("multicenter_generalizability_template_gap")
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
            "center_event_distribution": str(entry_validation_root / "center_event_distribution.csv"),
            "cohort_flow": str(resolved_paper_root / "cohort_flow.json"),
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
