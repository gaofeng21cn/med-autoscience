from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib
from med_autoscience import display_registry

matplotlib.use("Agg")

from ..shared import (
    _require_numeric_value,
    _require_non_empty_string,
)


_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}
_COHORT_FLOW_LAYOUT_MODES = {"two_panel_flow", "single_panel_cards"}
_COHORT_FLOW_STEP_ROLE_LABELS: dict[str, str] = {
    "historical_reference": "Historical patient reference",
    "current_patient_surface": "Current patient surface",
    "clinician_surface": "Clinician surface",
}


def _validate_transportability_recalibration_governance_panel_payload(
    path: Path,
    payload: dict[str, Any],
) -> dict[str, Any]:
    expected_shell_id = display_registry.get_illustration_shell_spec(
        "transportability_recalibration_governance_panel"
    ).shell_id
    shell_id = _require_non_empty_string(payload.get("shell_id"), label=f"{path.name} shell_id")
    if shell_id != expected_shell_id:
        raise ValueError(f"{path.name} shell_id must be `{expected_shell_id}`")
    display_id = _require_non_empty_string(payload.get("display_id"), label=f"{path.name} display_id")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} title")
    coverage_panel_title = _require_non_empty_string(
        payload.get("coverage_panel_title"),
        label=f"{path.name} coverage_panel_title",
    )
    coverage_x_label = _require_non_empty_string(
        payload.get("coverage_x_label"),
        label=f"{path.name} coverage_x_label",
    )
    center_rows_payload = payload.get("center_rows")
    if not isinstance(center_rows_payload, list) or not center_rows_payload:
        raise ValueError(f"{path.name} center_rows must be a non-empty list")
    seen_center_ids: set[str] = set()
    seen_center_labels: set[str] = set()
    normalized_center_rows: list[dict[str, Any]] = []
    for index, item in enumerate(center_rows_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} center_rows[{index}] must be an object")
        center_id = _require_non_empty_string(item.get("center_id"), label=f"{path.name} center_rows[{index}].center_id")
        center_label = _require_non_empty_string(
            item.get("center_label"),
            label=f"{path.name} center_rows[{index}].center_label",
        )
        cohort_role = _require_non_empty_string(
            item.get("cohort_role"),
            label=f"{path.name} center_rows[{index}].cohort_role",
        )
        if center_id in seen_center_ids:
            raise ValueError(f"{path.name} center_rows[{index}].center_id must be unique")
        if center_label in seen_center_labels:
            raise ValueError(f"{path.name} center_rows[{index}].center_label must be unique")
        seen_center_ids.add(center_id)
        seen_center_labels.add(center_label)
        support_count = item.get("support_count")
        event_count = item.get("event_count")
        if not isinstance(support_count, int) or support_count <= 0:
            raise ValueError(f"{path.name} center_rows[{index}].support_count must be a positive integer")
        if not isinstance(event_count, int) or event_count < 0:
            raise ValueError(f"{path.name} center_rows[{index}].event_count must be a non-negative integer")
        if event_count > support_count:
            raise ValueError(f"{path.name} center_rows[{index}].event_count must not exceed support_count")
        normalized_center_rows.append(
            {
                "center_id": center_id,
                "center_label": center_label,
                "cohort_role": cohort_role,
                "support_count": support_count,
                "event_count": event_count,
            }
        )

    batch_panel_title = _require_non_empty_string(
        payload.get("batch_panel_title"),
        label=f"{path.name} batch_panel_title",
    )
    batch_x_label = _require_non_empty_string(payload.get("batch_x_label"), label=f"{path.name} batch_x_label")
    batch_y_label = _require_non_empty_string(payload.get("batch_y_label"), label=f"{path.name} batch_y_label")
    batch_threshold = _require_numeric_value(payload.get("batch_threshold"), label=f"{path.name} batch_threshold")
    if not math.isfinite(batch_threshold) or batch_threshold <= 0.0:
        raise ValueError(f"{path.name} batch_threshold must be positive and finite")

    batch_rows_payload = payload.get("batch_rows")
    if not isinstance(batch_rows_payload, list) or not batch_rows_payload:
        raise ValueError(f"{path.name} batch_rows must be a non-empty list")
    batch_row_labels: list[str] = []
    seen_batch_row_labels: set[str] = set()
    for index, row in enumerate(batch_rows_payload):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} batch_rows[{index}] must be an object")
        label = _require_non_empty_string(row.get("label"), label=f"{path.name} batch_rows[{index}].label")
        if label in seen_batch_row_labels:
            raise ValueError(f"{path.name} batch_rows[{index}].label must be unique")
        seen_batch_row_labels.add(label)
        batch_row_labels.append(label)

    batch_columns_payload = payload.get("batch_columns")
    if not isinstance(batch_columns_payload, list) or not batch_columns_payload:
        raise ValueError(f"{path.name} batch_columns must be a non-empty list")
    batch_column_labels: list[str] = []
    seen_batch_column_labels: set[str] = set()
    for index, column in enumerate(batch_columns_payload):
        if not isinstance(column, dict):
            raise ValueError(f"{path.name} batch_columns[{index}] must be an object")
        label = _require_non_empty_string(
            column.get("label"),
            label=f"{path.name} batch_columns[{index}].label",
        )
        if label in seen_batch_column_labels:
            raise ValueError(f"{path.name} batch_columns[{index}].label must be unique")
        seen_batch_column_labels.add(label)
        batch_column_labels.append(label)

    batch_cells_payload = payload.get("batch_cells")
    if not isinstance(batch_cells_payload, list) or not batch_cells_payload:
        raise ValueError(f"{path.name} batch_cells must be a non-empty list")
    normalized_batch_cells: list[dict[str, Any]] = []
    seen_coordinates: set[tuple[str, str]] = set()
    expected_rows = set(batch_row_labels)
    expected_columns = set(batch_column_labels)
    observed_rows: set[str] = set()
    observed_columns: set[str] = set()
    for index, cell in enumerate(batch_cells_payload):
        if not isinstance(cell, dict):
            raise ValueError(f"{path.name} batch_cells[{index}] must be an object")
        column_label = _require_non_empty_string(cell.get("x"), label=f"{path.name} batch_cells[{index}].x")
        row_label = _require_non_empty_string(cell.get("y"), label=f"{path.name} batch_cells[{index}].y")
        if column_label not in expected_columns:
            raise ValueError(f"{path.name} batch_cells[{index}].x must reference a declared batch column")
        if row_label not in expected_rows:
            raise ValueError(f"{path.name} batch_cells[{index}].y must reference a declared batch row")
        coordinate = (column_label, row_label)
        if coordinate in seen_coordinates:
            raise ValueError(f"{path.name} batch_cells[{index}] duplicates coordinate {coordinate}")
        seen_coordinates.add(coordinate)
        observed_rows.add(row_label)
        observed_columns.add(column_label)
        value = _require_numeric_value(cell.get("value"), label=f"{path.name} batch_cells[{index}].value")
        if not math.isfinite(value) or value < 0.0 or value > 1.0:
            raise ValueError(f"{path.name} batch_cells[{index}].value must stay within [0, 1]")
        normalized_batch_cells.append({"x": column_label, "y": row_label, "value": float(value)})
    if observed_rows != expected_rows or observed_columns != expected_columns:
        raise ValueError(f"{path.name} batch_cells must cover the declared row/column labels")
    if len(seen_coordinates) != len(batch_row_labels) * len(batch_column_labels):
        raise ValueError(f"{path.name} batch_cells must provide a complete batch grid")

    recalibration_panel_title = _require_non_empty_string(
        payload.get("recalibration_panel_title"),
        label=f"{path.name} recalibration_panel_title",
    )
    slope_acceptance_lower = _require_numeric_value(
        payload.get("slope_acceptance_lower"),
        label=f"{path.name} slope_acceptance_lower",
    )
    slope_acceptance_upper = _require_numeric_value(
        payload.get("slope_acceptance_upper"),
        label=f"{path.name} slope_acceptance_upper",
    )
    if (
        not math.isfinite(slope_acceptance_lower)
        or not math.isfinite(slope_acceptance_upper)
        or slope_acceptance_lower <= 0.0
        or slope_acceptance_upper <= 0.0
        or slope_acceptance_lower >= slope_acceptance_upper
    ):
        raise ValueError(f"{path.name} slope acceptance band must be positive, finite, and ordered")
    oe_ratio_acceptance_lower = _require_numeric_value(
        payload.get("oe_ratio_acceptance_lower"),
        label=f"{path.name} oe_ratio_acceptance_lower",
    )
    oe_ratio_acceptance_upper = _require_numeric_value(
        payload.get("oe_ratio_acceptance_upper"),
        label=f"{path.name} oe_ratio_acceptance_upper",
    )
    if (
        not math.isfinite(oe_ratio_acceptance_lower)
        or not math.isfinite(oe_ratio_acceptance_upper)
        or oe_ratio_acceptance_lower <= 0.0
        or oe_ratio_acceptance_upper <= 0.0
        or oe_ratio_acceptance_lower >= oe_ratio_acceptance_upper
    ):
        raise ValueError(f"{path.name} oe_ratio acceptance band must be positive, finite, and ordered")

    recalibration_rows_payload = payload.get("recalibration_rows")
    if not isinstance(recalibration_rows_payload, list) or not recalibration_rows_payload:
        raise ValueError(f"{path.name} recalibration_rows must be a non-empty list")
    seen_recalibration_center_ids: set[str] = set()
    normalized_recalibration_rows: list[dict[str, Any]] = []
    for index, row in enumerate(recalibration_rows_payload):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} recalibration_rows[{index}] must be an object")
        center_id = _require_non_empty_string(
            row.get("center_id"),
            label=f"{path.name} recalibration_rows[{index}].center_id",
        )
        if center_id in seen_recalibration_center_ids:
            raise ValueError(f"{path.name} recalibration_rows[{index}].center_id must be unique")
        if center_id not in seen_center_ids:
            raise ValueError(f"{path.name} recalibration_rows[{index}].center_id must reference a declared center")
        seen_recalibration_center_ids.add(center_id)
        slope = _require_numeric_value(row.get("slope"), label=f"{path.name} recalibration_rows[{index}].slope")
        oe_ratio = _require_numeric_value(
            row.get("oe_ratio"),
            label=f"{path.name} recalibration_rows[{index}].oe_ratio",
        )
        if not math.isfinite(slope) or slope <= 0.0:
            raise ValueError(f"{path.name} recalibration_rows[{index}].slope must be positive and finite")
        if not math.isfinite(oe_ratio) or oe_ratio <= 0.0:
            raise ValueError(f"{path.name} recalibration_rows[{index}].oe_ratio must be positive and finite")
        normalized_recalibration_rows.append(
            {
                "center_id": center_id,
                "slope": float(slope),
                "oe_ratio": float(oe_ratio),
                "action": _require_non_empty_string(
                    row.get("action"),
                    label=f"{path.name} recalibration_rows[{index}].action",
                ),
                "detail": str(row.get("detail") or "").strip(),
            }
        )
    if seen_recalibration_center_ids != seen_center_ids:
        raise ValueError(f"{path.name} recalibration_rows must cover the declared centers exactly once")

    return {
        "shell_id": shell_id,
        "display_id": display_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "coverage_panel_title": coverage_panel_title,
        "coverage_x_label": coverage_x_label,
        "center_rows": normalized_center_rows,
        "batch_panel_title": batch_panel_title,
        "batch_x_label": batch_x_label,
        "batch_y_label": batch_y_label,
        "batch_threshold": float(batch_threshold),
        "batch_rows": [{"label": label} for label in batch_row_labels],
        "batch_columns": [{"label": label} for label in batch_column_labels],
        "batch_cells": normalized_batch_cells,
        "recalibration_panel_title": recalibration_panel_title,
        "slope_acceptance_lower": float(slope_acceptance_lower),
        "slope_acceptance_upper": float(slope_acceptance_upper),
        "oe_ratio_acceptance_lower": float(oe_ratio_acceptance_lower),
        "oe_ratio_acceptance_upper": float(oe_ratio_acceptance_upper),
        "recalibration_rows": normalized_recalibration_rows,
    }


