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


def _validate_baseline_missingness_qc_panel_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    expected_shell_id = display_registry.get_illustration_shell_spec("baseline_missingness_qc_panel").shell_id
    shell_id = _require_non_empty_string(payload.get("shell_id"), label=f"{path.name} shell_id")
    if shell_id != expected_shell_id:
        raise ValueError(f"{path.name} shell_id must be `{expected_shell_id}`")
    display_id = _require_non_empty_string(payload.get("display_id"), label=f"{path.name} display_id")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} title")
    balance_panel_title = _require_non_empty_string(
        payload.get("balance_panel_title"),
        label=f"{path.name} balance_panel_title",
    )
    balance_x_label = _require_non_empty_string(
        payload.get("balance_x_label"),
        label=f"{path.name} balance_x_label",
    )
    balance_threshold = _require_numeric_value(
        payload.get("balance_threshold"),
        label=f"{path.name} balance_threshold",
    )
    if not math.isfinite(balance_threshold) or balance_threshold <= 0.0:
        raise ValueError(f"{path.name} balance_threshold must be positive and finite")
    primary_balance_label = _require_non_empty_string(
        payload.get("primary_balance_label"),
        label=f"{path.name} primary_balance_label",
    )
    secondary_balance_label = str(payload.get("secondary_balance_label") or "").strip()

    balance_payload = payload.get("balance_variables")
    if not isinstance(balance_payload, list) or not balance_payload:
        raise ValueError(f"{path.name} balance_variables must be a non-empty list")
    seen_balance_ids: set[str] = set()
    seen_balance_labels: set[str] = set()
    normalized_balance_variables: list[dict[str, Any]] = []
    saw_secondary_values = False
    for index, item in enumerate(balance_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} balance_variables[{index}] must be an object")
        variable_id = _require_non_empty_string(
            item.get("variable_id"),
            label=f"{path.name} balance_variables[{index}].variable_id",
        )
        label = _require_non_empty_string(
            item.get("label"),
            label=f"{path.name} balance_variables[{index}].label",
        )
        if variable_id in seen_balance_ids:
            raise ValueError(f"{path.name} balance_variables[{index}].variable_id must be unique")
        if label in seen_balance_labels:
            raise ValueError(f"{path.name} balance_variables[{index}].label must be unique")
        seen_balance_ids.add(variable_id)
        seen_balance_labels.add(label)
        primary_value = _require_numeric_value(
            item.get("primary_value"),
            label=f"{path.name} balance_variables[{index}].primary_value",
        )
        if not math.isfinite(primary_value) or primary_value < 0.0:
            raise ValueError(f"{path.name} balance_variables[{index}].primary_value must be finite and non-negative")
        normalized_item = {
            "variable_id": variable_id,
            "label": label,
            "primary_value": float(primary_value),
        }
        if item.get("secondary_value") is not None:
            secondary_value = _require_numeric_value(
                item.get("secondary_value"),
                label=f"{path.name} balance_variables[{index}].secondary_value",
            )
            if not secondary_balance_label:
                raise ValueError(f"{path.name} secondary_balance_label is required when secondary_value is present")
            if not math.isfinite(secondary_value) or secondary_value < 0.0:
                raise ValueError(
                    f"{path.name} balance_variables[{index}].secondary_value must be finite and non-negative"
                )
            normalized_item["secondary_value"] = float(secondary_value)
            saw_secondary_values = True
        normalized_balance_variables.append(normalized_item)
    if secondary_balance_label and not saw_secondary_values:
        secondary_balance_label = ""

    missingness_panel_title = _require_non_empty_string(
        payload.get("missingness_panel_title"),
        label=f"{path.name} missingness_panel_title",
    )
    missingness_x_label = _require_non_empty_string(
        payload.get("missingness_x_label"),
        label=f"{path.name} missingness_x_label",
    )
    missingness_y_label = _require_non_empty_string(
        payload.get("missingness_y_label"),
        label=f"{path.name} missingness_y_label",
    )
    rows_payload = payload.get("missingness_rows")
    if not isinstance(rows_payload, list) or not rows_payload:
        raise ValueError(f"{path.name} missingness_rows must be a non-empty list")
    row_labels: list[str] = []
    seen_row_labels: set[str] = set()
    for index, row in enumerate(rows_payload):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} missingness_rows[{index}] must be an object")
        label = _require_non_empty_string(
            row.get("label"),
            label=f"{path.name} missingness_rows[{index}].label",
        )
        if label in seen_row_labels:
            raise ValueError(f"{path.name} missingness_rows[{index}].label must be unique")
        seen_row_labels.add(label)
        row_labels.append(label)

    columns_payload = payload.get("missingness_columns")
    if not isinstance(columns_payload, list) or not columns_payload:
        raise ValueError(f"{path.name} missingness_columns must be a non-empty list")
    column_labels: list[str] = []
    seen_column_labels: set[str] = set()
    for index, column in enumerate(columns_payload):
        if not isinstance(column, dict):
            raise ValueError(f"{path.name} missingness_columns[{index}] must be an object")
        label = _require_non_empty_string(
            column.get("label"),
            label=f"{path.name} missingness_columns[{index}].label",
        )
        if label in seen_column_labels:
            raise ValueError(f"{path.name} missingness_columns[{index}].label must be unique")
        seen_column_labels.add(label)
        column_labels.append(label)

    cells_payload = payload.get("missingness_cells")
    if not isinstance(cells_payload, list) or not cells_payload:
        raise ValueError(f"{path.name} missingness_cells must be a non-empty list")
    normalized_cells: list[dict[str, Any]] = []
    seen_coordinates: set[tuple[str, str]] = set()
    expected_rows = set(row_labels)
    expected_columns = set(column_labels)
    observed_rows: set[str] = set()
    observed_columns: set[str] = set()
    for index, cell in enumerate(cells_payload):
        if not isinstance(cell, dict):
            raise ValueError(f"{path.name} missingness_cells[{index}] must be an object")
        column_label = _require_non_empty_string(
            cell.get("x"),
            label=f"{path.name} missingness_cells[{index}].x",
        )
        row_label = _require_non_empty_string(
            cell.get("y"),
            label=f"{path.name} missingness_cells[{index}].y",
        )
        if column_label not in expected_columns:
            raise ValueError(f"{path.name} missingness_cells[{index}].x must reference a declared missingness column")
        if row_label not in expected_rows:
            raise ValueError(f"{path.name} missingness_cells[{index}].y must reference a declared missingness row")
        coordinate = (column_label, row_label)
        if coordinate in seen_coordinates:
            raise ValueError(f"{path.name} missingness_cells[{index}] duplicates coordinate {coordinate}")
        seen_coordinates.add(coordinate)
        observed_rows.add(row_label)
        observed_columns.add(column_label)
        value = _require_numeric_value(
            cell.get("value"),
            label=f"{path.name} missingness_cells[{index}].value",
        )
        if not math.isfinite(value) or value < 0.0 or value > 1.0:
            raise ValueError(f"{path.name} missingness_cells[{index}].value must stay within [0, 1]")
        normalized_cells.append({"x": column_label, "y": row_label, "value": float(value)})
    if observed_rows != expected_rows or observed_columns != expected_columns:
        raise ValueError(f"{path.name} missingness_cells must cover the declared row/column labels")
    if len(seen_coordinates) != len(row_labels) * len(column_labels):
        raise ValueError(f"{path.name} missingness_cells must provide a complete missingness grid")

    qc_panel_title = _require_non_empty_string(
        payload.get("qc_panel_title"),
        label=f"{path.name} qc_panel_title",
    )
    qc_cards_payload = payload.get("qc_cards")
    if not isinstance(qc_cards_payload, list) or not qc_cards_payload:
        raise ValueError(f"{path.name} qc_cards must be a non-empty list")
    seen_card_ids: set[str] = set()
    normalized_qc_cards: list[dict[str, Any]] = []
    for index, card in enumerate(qc_cards_payload):
        if not isinstance(card, dict):
            raise ValueError(f"{path.name} qc_cards[{index}] must be an object")
        card_id = _require_non_empty_string(
            card.get("card_id"),
            label=f"{path.name} qc_cards[{index}].card_id",
        )
        if card_id in seen_card_ids:
            raise ValueError(f"{path.name} qc_cards[{index}].card_id must be unique")
        seen_card_ids.add(card_id)
        normalized_qc_cards.append(
            {
                "card_id": card_id,
                "label": _require_non_empty_string(
                    card.get("label"),
                    label=f"{path.name} qc_cards[{index}].label",
                ),
                "value": _require_non_empty_string(
                    card.get("value"),
                    label=f"{path.name} qc_cards[{index}].value",
                ),
                "detail": str(card.get("detail") or "").strip(),
            }
        )

    return {
        "shell_id": shell_id,
        "display_id": display_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "balance_panel_title": balance_panel_title,
        "balance_x_label": balance_x_label,
        "balance_threshold": float(balance_threshold),
        "primary_balance_label": primary_balance_label,
        "secondary_balance_label": secondary_balance_label,
        "balance_variables": normalized_balance_variables,
        "missingness_panel_title": missingness_panel_title,
        "missingness_x_label": missingness_x_label,
        "missingness_y_label": missingness_y_label,
        "missingness_rows": [{"label": label} for label in row_labels],
        "missingness_columns": [{"label": label} for label in column_labels],
        "missingness_cells": normalized_cells,
        "qc_panel_title": qc_panel_title,
        "qc_cards": normalized_qc_cards,
    }


