from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .shared_parts.common import (
    _format_percent_1dp,
    _require_namespaced_registry_id,
    _require_non_empty_string,
    _require_non_negative_int,
)


def _validate_baseline_table_payload(path: Path, payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]], bool]:
    groups = payload.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError(f"{path.name} must contain a non-empty groups list")
    group_labels: list[str] = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ValueError(f"{path.name} groups[{index}] must be an object")
        label = str(group.get("label") or "").strip()
        if not label:
            raise ValueError(f"{path.name} groups[{index}] must include label")
        group_labels.append(label)

    variables = payload.get("variables")
    if not isinstance(variables, list) or not variables:
        raise ValueError(f"{path.name} must contain a non-empty variables list")
    normalized_rows: list[dict[str, Any]] = []
    has_p_values = False
    for index, variable in enumerate(variables):
        if not isinstance(variable, dict):
            raise ValueError(f"{path.name} variables[{index}] must be an object")
        label = str(variable.get("label") or "").strip()
        values = variable.get("values")
        if not label or not isinstance(values, list) or len(values) != len(group_labels):
            raise ValueError(
                f"{path.name} variables[{index}] must include label and values matching the number of groups"
            )
        row = {"label": label, "values": [str(item).strip() for item in values]}
        if "p_value" in variable:
            row["p_value"] = str(variable.get("p_value") or "").strip()
            has_p_values = has_p_values or bool(row["p_value"])
        normalized_rows.append(row)
    return group_labels, normalized_rows, has_p_values


def _validate_column_table_payload(path: Path, payload: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    columns = payload.get("columns")
    if not isinstance(columns, list) or not columns:
        raise ValueError(f"{path.name} must contain a non-empty columns list")
    column_labels: list[str] = []
    for index, column in enumerate(columns):
        if not isinstance(column, dict):
            raise ValueError(f"{path.name} columns[{index}] must be an object")
        column_labels.append(
            _require_non_empty_string(column.get("label"), label=f"{path.name} columns[{index}].label")
        )

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} must contain a non-empty rows list")
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} rows[{index}] must be an object")
        label = _require_non_empty_string(row.get("label"), label=f"{path.name} rows[{index}].label")
        values = row.get("values")
        if not isinstance(values, list) or len(values) != len(column_labels):
            raise ValueError(f"{path.name} rows[{index}] must include values matching the number of columns")
        normalized_rows.append({"label": label, "values": [str(item).strip() for item in values]})
    return column_labels, normalized_rows


def _legacy_table_csv_path(payload_path: Path, template_short_id: str) -> Path:
    filename_by_template = {
        "table2_phenotype_gap_summary": "T2_phenotype_gap_summary.csv",
        "table3_transition_site_support_summary": "T3_transition_site_support_summary.csv",
    }
    try:
        filename = filename_by_template[template_short_id]
    except KeyError as exc:
        raise ValueError(f"unsupported DPCC table shell `{template_short_id}`") from exc
    return payload_path.parent / "tables" / filename


def _read_legacy_table_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.exists():
        raise ValueError(f"{path.name} is required to render the DPCC table shell without inventing table values")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2 or not rows[0]:
        raise ValueError(f"{path.name} must contain a header row and at least one data row")
    return [str(item).strip() for item in rows[0]], [[str(item).strip() for item in row] for row in rows[1:]]


def _compact_dpcc_wide_table(
    *,
    headers: list[str],
    rows: list[list[str]],
    group_column_count: int,
) -> tuple[list[str], list[list[str]]]:
    if group_column_count < 1 or group_column_count >= len(headers):
        raise ValueError("DPCC table shell group_column_count must leave at least one measure column")
    compact_headers = [*headers[:group_column_count], "Measure", "Value"]
    compact_rows: list[list[str]] = []
    for row_index, row in enumerate(rows):
        if len(row) != len(headers):
            raise ValueError(f"DPCC table shell row {row_index} has {len(row)} cells for {len(headers)} headers")
        group_values = row[:group_column_count]
        for measure, value in zip(headers[group_column_count:], row[group_column_count:], strict=True):
            compact_rows.append([*group_values, measure, value])
    return compact_headers, compact_rows


def _render_dpcc_summary_table(
    *,
    template_short_id: str,
    payload_path: Path,
    payload: dict[str, Any],
    output_md_path: Path,
    output_csv_path: Path | None,
    title: str,
    caption: str,
) -> dict[str, str]:
    if output_csv_path is None:
        raise ValueError(f"{template_short_id} requires output_csv_path")
    group_columns = payload.get("group_columns")
    if not isinstance(group_columns, list) or not group_columns:
        raise ValueError(f"{payload_path.name} must contain a non-empty group_columns list")
    source_csv_path = _legacy_table_csv_path(payload_path, template_short_id)
    headers, rows = _read_legacy_table_csv(source_csv_path)
    compact_headers, compact_rows = _compact_dpcc_wide_table(
        headers=headers,
        rows=rows,
        group_column_count=len(group_columns),
    )
    _write_rectangular_table_outputs(
        output_md_path=output_md_path,
        title=title,
        headers=compact_headers,
        table_rows=compact_rows,
        output_csv_path=output_csv_path,
    )
    return {
        "title": title,
        "caption": caption,
        "source_table_path": str(source_csv_path),
        "table_layout_policy": "long_measure_value_table_to_avoid_pdf_header_overlap",
    }


def _validate_performance_summary_table_generic_payload(
    path: Path,
    payload: dict[str, Any],
) -> tuple[str, list[str], list[dict[str, Any]]]:
    row_header_label = _require_non_empty_string(
        payload.get("row_header_label"),
        label=f"{path.name} row_header_label",
    )
    column_labels, rows = _validate_column_table_payload(path, payload)
    return row_header_label, column_labels, rows


def _validate_grouped_risk_event_summary_table_payload(
    path: Path,
    payload: dict[str, Any],
) -> tuple[list[str], list[list[str]]]:
    headers = [
        _require_non_empty_string(payload.get("surface_column_label"), label=f"{path.name} surface_column_label"),
        _require_non_empty_string(payload.get("stratum_column_label"), label=f"{path.name} stratum_column_label"),
        _require_non_empty_string(payload.get("cases_column_label"), label=f"{path.name} cases_column_label"),
        _require_non_empty_string(payload.get("events_column_label"), label=f"{path.name} events_column_label"),
        _require_non_empty_string(payload.get("risk_column_label"), label=f"{path.name} risk_column_label"),
    ]
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} must contain a non-empty rows list")
    normalized_rows: list[list[str]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} rows[{index}] must be an object")
        surface = _require_non_empty_string(row.get("surface"), label=f"{path.name} rows[{index}].surface")
        stratum = _require_non_empty_string(row.get("stratum"), label=f"{path.name} rows[{index}].stratum")
        cases = _require_non_negative_int(row.get("cases"), label=f"{path.name} rows[{index}].cases", allow_zero=False)
        events = _require_non_negative_int(row.get("events"), label=f"{path.name} rows[{index}].events")
        if events > cases:
            raise ValueError(f"{path.name} rows[{index}].events must not exceed cases")
        risk_display = _require_non_empty_string(
            row.get("risk_display"),
            label=f"{path.name} rows[{index}].risk_display",
        )
        expected_risk_display = _format_percent_1dp(numerator=events, denominator=cases)
        if risk_display != expected_risk_display:
            raise ValueError(
                f"{path.name} rows[{index}].risk_display must equal {expected_risk_display} for {events}/{cases}"
            )
        normalized_rows.append([surface, stratum, str(cases), str(events), risk_display])
    return headers, normalized_rows


def _write_rectangular_table_outputs(
    *,
    output_md_path: Path,
    title: str,
    headers: list[str],
    table_rows: list[list[str]],
    output_csv_path: Path | None = None,
) -> None:
    if output_csv_path is not None:
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with output_csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(table_rows)

    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_lines = [
        f"# {title}",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in table_rows:
        markdown_lines.append("| " + " | ".join(row) + " |")
    output_md_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")


def _write_table_outputs(
    *,
    output_md_path: Path,
    title: str,
    column_labels: list[str],
    rows: list[dict[str, Any]],
    stub_header: str,
    output_csv_path: Path | None = None,
) -> None:
    headers = [stub_header, *column_labels]
    table_rows = [[row["label"], *row["values"]] for row in rows]
    _write_rectangular_table_outputs(
        output_md_path=output_md_path,
        title=title,
        headers=headers,
        table_rows=table_rows,
        output_csv_path=output_csv_path,
    )


def render_table_shell(
    *,
    template_id: str,
    payload_path: Path,
    payload: dict[str, Any],
    output_md_path: Path,
    output_csv_path: Path | None = None,
) -> dict[str, str]:
    _, template_short_id = _require_namespaced_registry_id(template_id, label="template_id")

    if template_short_id == "table1_baseline_characteristics":
        if output_csv_path is None:
            raise ValueError("table1_baseline_characteristics requires output_csv_path")
        group_labels, rows, has_p_values = _validate_baseline_table_payload(payload_path, payload)
        title = str(payload.get("title") or "Baseline characteristics").strip() or "Baseline characteristics"
        if has_p_values:
            headers = ["Characteristic", *group_labels, "P value"]
            table_rows = [[row["label"], *row["values"], str(row.get("p_value") or "")] for row in rows]
            _write_rectangular_table_outputs(
                output_md_path=output_md_path,
                title=title,
                headers=headers,
                table_rows=table_rows,
                output_csv_path=output_csv_path,
            )
        else:
            _write_table_outputs(
                output_md_path=output_md_path,
                title=title,
                column_labels=group_labels,
                rows=rows,
                stub_header="Characteristic",
                output_csv_path=output_csv_path,
            )
        return {
            "title": title,
            "caption": str(payload.get("caption") or "Baseline characteristics across prespecified groups.").strip(),
        }

    if template_short_id == "table2_time_to_event_performance_summary":
        column_labels, rows = _validate_column_table_payload(payload_path, payload)
        title = (
            str(payload.get("title") or "Time-to-event model performance summary").strip()
            or "Time-to-event model performance summary"
        )
        _write_table_outputs(
            output_md_path=output_md_path,
            title=title,
            column_labels=column_labels,
            rows=rows,
            stub_header="Metric",
        )
        return {
            "title": title,
            "caption": str(
                payload.get("caption") or "Time-to-event discrimination and error metrics across analysis cohorts."
            ).strip(),
        }

    if template_short_id == "table3_clinical_interpretation_summary":
        column_labels, rows = _validate_column_table_payload(payload_path, payload)
        title = str(payload.get("title") or "Clinical interpretation summary").strip() or "Clinical interpretation summary"
        _write_table_outputs(
            output_md_path=output_md_path,
            title=title,
            column_labels=column_labels,
            rows=rows,
            stub_header="Clinical Item",
        )
        return {
            "title": title,
            "caption": str(
                payload.get("caption") or "Clinical interpretation anchors for prespecified risk groups and use cases."
            ).strip(),
        }

    if template_short_id == "table2_phenotype_gap_summary":
        return _render_dpcc_summary_table(
            template_short_id=template_short_id,
            payload_path=payload_path,
            payload=payload,
            output_md_path=output_md_path,
            output_csv_path=output_csv_path,
            title=(
                str(payload.get("title") or "Phenotype-level clinical characteristics and treatment-gap rates").strip()
                or "Phenotype-level clinical characteristics and treatment-gap rates"
            ),
            caption=str(
                payload.get("caption")
                or "Phenotype-level clinical characteristics and treatment-gap rates rendered as a compact measure-value table."
            ).strip(),
        )

    if template_short_id == "table3_transition_site_support_summary":
        return _render_dpcc_summary_table(
            template_short_id=template_short_id,
            payload_path=payload_path,
            payload=payload,
            output_md_path=output_md_path,
            output_csv_path=output_csv_path,
            title=(
                str(payload.get("title") or "Transition stability and site-held-out support summary").strip()
                or "Transition stability and site-held-out support summary"
            ),
            caption=str(
                payload.get("caption")
                or "Transition and held-out-site support rendered as a compact measure-value table."
            ).strip(),
        )

    if template_short_id == "performance_summary_table_generic":
        if output_csv_path is None:
            raise ValueError("performance_summary_table_generic requires output_csv_path")
        row_header_label, column_labels, rows = _validate_performance_summary_table_generic_payload(
            payload_path,
            payload,
        )
        title = str(payload.get("title") or "Performance summary").strip() or "Performance summary"
        _write_table_outputs(
            output_md_path=output_md_path,
            title=title,
            column_labels=column_labels,
            rows=rows,
            stub_header=row_header_label,
            output_csv_path=output_csv_path,
        )
        return {
            "title": title,
            "caption": str(
                payload.get("caption") or "Structured repeated-validation performance summaries across candidate packages."
            ).strip(),
        }

    if template_short_id == "grouped_risk_event_summary_table":
        if output_csv_path is None:
            raise ValueError("grouped_risk_event_summary_table requires output_csv_path")
        headers, table_rows = _validate_grouped_risk_event_summary_table_payload(payload_path, payload)
        title = str(payload.get("title") or "Grouped risk event summary").strip() or "Grouped risk event summary"
        _write_rectangular_table_outputs(
            output_md_path=output_md_path,
            title=title,
            headers=headers,
            table_rows=table_rows,
            output_csv_path=output_csv_path,
        )
        return {
            "title": title,
            "caption": str(
                payload.get("caption") or "Observed case counts, event counts, and absolute risks across grouped-risk strata."
            ).strip(),
        }

    raise RuntimeError(f"unsupported table shell `{template_id}`")
