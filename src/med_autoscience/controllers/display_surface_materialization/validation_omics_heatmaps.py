from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_numeric_value, math
from .validation_tables import _validate_labeled_order_payload

def _validate_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty cells list")
    normalized_cells: list[dict[str, Any]] = []
    for index, item in enumerate(cells):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` cells[{index}] must be an object")
        normalized_cells.append(
            {
                "x": _require_non_empty_string(item.get("x"), label=f"{path.name} display `{expected_display_id}` cells[{index}].x"),
                "y": _require_non_empty_string(item.get("y"), label=f"{path.name} display `{expected_display_id}` cells[{index}].y"),
                "value": _require_numeric_value(
                    item.get("value"),
                    label=f"{path.name} display `{expected_display_id}` cells[{index}].value",
                ),
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "cells": normalized_cells,
    }

def _validate_performance_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized_payload = _validate_clustered_heatmap_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    normalized_payload["metric_name"] = _require_non_empty_string(
        payload.get("metric_name"),
        label=f"{path.name} display `{expected_display_id}` metric_name",
    )
    for index, cell in enumerate(normalized_payload["cells"]):
        value = float(cell["value"])
        if 0.0 <= value <= 1.0:
            continue
        raise ValueError(
            f"{path.name} display `{expected_display_id}` cells[{index}].value must stay within [0, 1]"
        )
    return normalized_payload

def _validate_confusion_matrix_heatmap_binary_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized_payload = _validate_clustered_heatmap_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    normalized_payload["metric_name"] = _require_non_empty_string(
        payload.get("metric_name"),
        label=f"{path.name} display `{expected_display_id}` metric_name",
    )
    normalization = _require_non_empty_string(
        payload.get("normalization"),
        label=f"{path.name} display `{expected_display_id}` normalization",
    )
    if normalization not in {"row_fraction", "column_fraction", "overall_fraction"}:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` normalization must be one of row_fraction, column_fraction, overall_fraction"
        )
    if len(normalized_payload["row_order"]) != 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` row_order must declare exactly two labels")
    if len(normalized_payload["column_order"]) != 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` column_order must declare exactly two labels")
    matrix_lookup: dict[tuple[str, str], float] = {}
    for index, cell in enumerate(normalized_payload["cells"]):
        value = float(cell["value"])
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` cells[{index}].value must stay within [0, 1]"
            )
        matrix_lookup[(str(cell["x"]), str(cell["y"]))] = value

    row_labels = [str(item["label"]) for item in normalized_payload["row_order"]]
    column_labels = [str(item["label"]) for item in normalized_payload["column_order"]]
    tolerance = 1e-6
    if normalization == "row_fraction":
        for row_label in row_labels:
            total = sum(matrix_lookup[(column_label, row_label)] for column_label in column_labels)
            if math.isclose(total, 1.0, rel_tol=0.0, abs_tol=tolerance):
                continue
            raise ValueError(
                f"{path.name} display `{expected_display_id}` row `{row_label}` must sum to 1.0 when normalization=row_fraction"
            )
    elif normalization == "column_fraction":
        for column_label in column_labels:
            total = sum(matrix_lookup[(column_label, row_label)] for row_label in row_labels)
            if math.isclose(total, 1.0, rel_tol=0.0, abs_tol=tolerance):
                continue
            raise ValueError(
                f"{path.name} display `{expected_display_id}` column `{column_label}` must sum to 1.0 when normalization=column_fraction"
            )
    else:
        total = sum(matrix_lookup.values())
        if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=tolerance):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` all confusion-matrix cells must sum to 1.0 when normalization=overall_fraction"
            )
    normalized_payload["normalization"] = normalization
    return normalized_payload

def _validate_clustered_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    row_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("row_order"),
        label=f"display `{expected_display_id}` row_order",
    )
    column_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("column_order"),
        label=f"display `{expected_display_id}` column_order",
    )
    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty cells list")
    normalized_cells: list[dict[str, Any]] = []
    observed_rows: set[str] = set()
    observed_columns: set[str] = set()
    observed_coordinates: set[tuple[str, str]] = set()
    for index, item in enumerate(cells):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` cells[{index}] must be an object")
        column_label = _require_non_empty_string(
            item.get("x"),
            label=f"{path.name} display `{expected_display_id}` cells[{index}].x",
        )
        row_label = _require_non_empty_string(
            item.get("y"),
            label=f"{path.name} display `{expected_display_id}` cells[{index}].y",
        )
        coordinate = (column_label, row_label)
        if coordinate in observed_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once"
            )
        observed_coordinates.add(coordinate)
        observed_columns.add(column_label)
        observed_rows.add(row_label)
        normalized_cells.append(
            {
                "x": column_label,
                "y": row_label,
                "value": _require_numeric_value(
                    item.get("value"),
                    label=f"{path.name} display `{expected_display_id}` cells[{index}].value",
                ),
            }
        )

    declared_rows = {item["label"] for item in row_order}
    declared_columns = {item["label"] for item in column_order}
    if observed_rows != declared_rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` row_order labels must match cell y labels")
    if observed_columns != declared_columns:
        raise ValueError(f"{path.name} display `{expected_display_id}` column_order labels must match cell x labels")
    expected_coordinates = {(column["label"], row["label"]) for row in row_order for column in column_order}
    if observed_coordinates != expected_coordinates:
        raise ValueError(f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }

def _validate_gsva_ssgsea_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    normalized_payload = _validate_clustered_heatmap_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    normalized_payload["score_method"] = _require_non_empty_string(
        payload.get("score_method"),
        label=f"{path.name} display `{expected_display_id}` score_method",
    )
    return normalized_payload


__all__ = [
    "_validate_heatmap_display_payload",
    "_validate_performance_heatmap_display_payload",
    "_validate_confusion_matrix_heatmap_binary_display_payload",
    "_validate_clustered_heatmap_display_payload",
    "_validate_gsva_ssgsea_heatmap_display_payload",
]
