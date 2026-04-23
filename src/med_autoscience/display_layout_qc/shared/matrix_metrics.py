from __future__ import annotations

import math
from typing import Any

from .core import _issue, _require_numeric


def _matrix_cell_lookup(metrics: dict[str, Any]) -> dict[tuple[str, str], float]:
    cells = metrics.get("matrix_cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("layout_sidecar.metrics.matrix_cells must be a non-empty list for heatmap qc")
    lookup: dict[tuple[str, str], float] = {}
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            raise ValueError(f"layout_sidecar.metrics.matrix_cells[{index}] must be an object")
        x_key = str(cell.get("x") or "").strip()
        y_key = str(cell.get("y") or "").strip()
        if not x_key or not y_key:
            raise ValueError(f"layout_sidecar.metrics.matrix_cells[{index}] must include x and y")
        lookup[(x_key, y_key)] = _require_numeric(
            cell.get("value"),
            label=f"layout_sidecar.metrics.matrix_cells[{index}].value",
        )
    return lookup


def _check_audit_panel_collection_metrics(
    panels: object,
    *,
    target: str,
) -> tuple[list[dict[str, object]], int, int]:
    issues: list[dict[str, object]] = []
    if not isinstance(panels, list) or not panels:
        issues.append(
            _issue(
                rule_id="audit_panels_missing",
                message="audit-panel collection must be non-empty",
                target=target,
            )
        )
        return issues, 0, 0
    seen_panel_ids: set[str] = set()
    total_rows = 0
    reference_count = 0
    for index, panel in enumerate(panels):
        if not isinstance(panel, dict):
            raise ValueError(f"{target}[{index}] must be an object")
        panel_id = str(panel.get("panel_id") or "").strip()
        if not panel_id:
            issues.append(
                _issue(
                    rule_id="panel_id_missing",
                    message="audit panels must declare a non-empty panel_id",
                    target=f"{target}[{index}].panel_id",
                )
            )
        elif panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="panel_id_not_unique",
                    message="audit panel ids must be unique",
                    target=f"{target}[{index}].panel_id",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)
        rows = panel.get("rows")
        if not isinstance(rows, list) or not rows:
            issues.append(
                _issue(
                    rule_id="panel_rows_missing",
                    message="audit panels must contain non-empty rows",
                    target=f"{target}[{index}].rows",
                )
            )
            continue
        total_rows += len(rows)
        if panel.get("reference_value") is not None:
            _require_numeric(panel.get("reference_value"), label=f"{target}[{index}].reference_value")
            reference_count += 1
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"{target}[{index}].rows[{row_index}] must be an object")
            row_label = str(row.get("label") or "").strip()
            if not row_label:
                issues.append(
                    _issue(
                        rule_id="row_label_missing",
                        message="audit-panel rows require non-empty labels",
                        target=f"{target}[{index}].rows[{row_index}].label",
                    )
                )
            row_value = _require_numeric(row.get("value"), label=f"{target}[{index}].rows[{row_index}].value")
            if not math.isfinite(row_value):
                issues.append(
                    _issue(
                        rule_id="row_value_non_finite",
                        message="audit-panel row values must be finite",
                        target=f"{target}[{index}].rows[{row_index}]",
                    )
                )
    return issues, total_rows, reference_count
