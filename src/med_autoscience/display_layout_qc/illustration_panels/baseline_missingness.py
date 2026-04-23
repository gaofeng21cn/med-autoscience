from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_of_type,
    _check_boxes_within_device,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _issue,
    _require_numeric,
    math,
)

def _check_publication_baseline_missingness_qc_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=("panel", "panel_label", "panel_title", "subplot_x_axis_title", "card_label", "card_value"),
        )
    )

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 3:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="baseline missingness QC panel requires exactly three panel boxes",
                target="panel_boxes",
                expected={"count": 3},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    panel_label_to_panel_id = {
        "A": "panel_balance",
        "B": "panel_missingness",
        "C": "panel_qc",
    }
    title_boxes = {
        "balance_panel_title": "panel_balance",
        "missingness_panel_title": "panel_missingness",
        "qc_panel_title": "panel_qc",
    }
    for panel_label, panel_id in panel_label_to_panel_id.items():
        label_box = layout_boxes_by_id.get(f"panel_label_{panel_label}")
        panel_box = panel_boxes_by_id.get(panel_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="baseline missingness QC panel requires the fixed three-panel layout",
                    target="panel_boxes",
                    expected=panel_id,
                )
            )
            continue
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="baseline missingness QC panel labels must be present for every panel",
                    target="panel_label",
                    expected=f"panel_label_{panel_label}",
                )
            )
            continue
        if not _box_within_box(label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="baseline missingness QC panel labels must stay within their parent panel",
                    target="panel_label",
                    box_refs=(label_box.box_id, panel_box.box_id),
                )
            )
        else:
            panel_width = max(panel_box.x1 - panel_box.x0, 1e-9)
            panel_height = max(panel_box.y1 - panel_box.y0, 1e-9)
            anchored_near_left = label_box.x0 <= panel_box.x0 + panel_width * 0.10
            anchored_near_top = (
                label_box.y0 <= panel_box.y0 + panel_height * 0.12
                or label_box.y1 >= panel_box.y1 - panel_height * 0.10
            )
            if not (anchored_near_left and anchored_near_top):
                issues.append(
                    _issue(
                        rule_id="panel_label_anchor_drift",
                        message="baseline missingness QC panel labels must stay near the parent panel top-left anchor",
                        target="panel_label",
                        box_refs=(label_box.box_id, panel_box.box_id),
                    )
                )

    for title_box_id, panel_id in title_boxes.items():
        title_box = layout_boxes_by_id.get(title_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="baseline missingness QC panel requires all three panel titles",
                    target="panel_title",
                    expected=title_box_id,
                )
            )
            continue
        if panel_box is not None:
            aligned_horizontally = (
                title_box.x0 >= panel_box.x0 - 0.02 and title_box.x1 <= panel_box.x1 + 0.02
            )
            close_to_panel_top = (
                title_box.y0 >= panel_box.y0 - 0.02 and title_box.y1 <= panel_box.y1 + 0.08
            )
            if aligned_horizontally and close_to_panel_top:
                continue
            issues.append(
                _issue(
                    rule_id="panel_title_out_of_panel",
                    message="baseline missingness QC panel titles must stay tightly aligned with their parent panel",
                    target="panel_title",
                    box_refs=(title_box.box_id, panel_box.box_id),
                )
            )

    axis_title_pairs = (
        ("balance_x_axis_title", "panel_balance"),
        ("missingness_x_axis_title", "panel_missingness"),
        ("missingness_y_axis_title", "panel_missingness"),
    )
    for axis_box_id, panel_id in axis_title_pairs:
        axis_box = layout_boxes_by_id.get(axis_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if axis_box is None:
            issues.append(
                _issue(
                    rule_id="axis_title_missing",
                    message="baseline missingness QC panel must expose the bounded axis-title surface",
                    target="subplot_axis_title",
                    expected=axis_box_id,
                )
            )
            continue
        if panel_box is not None:
            if axis_box.box_id.endswith("_y_axis_title"):
                axis_center_y = (axis_box.y0 + axis_box.y1) / 2.0
                aligned_with_panel = (
                    panel_box.y0 <= axis_center_y <= panel_box.y1
                    and axis_box.x0 >= panel_box.x0 - 0.12
                    and axis_box.x1 <= panel_box.x1 + 0.02
                )
            else:
                axis_center_x = (axis_box.x0 + axis_box.x1) / 2.0
                aligned_with_panel = (
                    panel_box.x0 <= axis_center_x <= panel_box.x1
                    and axis_box.y0 >= panel_box.y0 - 0.10
                    and axis_box.y1 <= panel_box.y1 + 0.02
                )
            if not aligned_with_panel:
                issues.append(
                    _issue(
                        rule_id="axis_title_out_of_panel",
                        message="baseline missingness QC axis titles must stay tightly aligned with their parent panel",
                        target=axis_box.box_type,
                        box_refs=(axis_box.box_id, panel_box.box_id),
                    )
                )

    if not _boxes_of_type(sidecar.guide_boxes, "reference_line"):
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="baseline missingness QC panel requires a balance threshold reference line",
                target="reference_line",
            )
        )
    if not _boxes_of_type(sidecar.guide_boxes, "colorbar"):
        issues.append(
            _issue(
                rule_id="colorbar_missing",
                message="baseline missingness QC panel requires a missingness colorbar guide box",
                target="colorbar",
            )
        )

    balance_threshold = _require_numeric(sidecar.metrics.get("balance_threshold"), label="layout_sidecar.metrics.balance_threshold")
    if not math.isfinite(balance_threshold) or balance_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="balance_threshold_invalid",
                message="balance_threshold must be positive and finite",
                target="metrics.balance_threshold",
                observed=balance_threshold,
            )
        )
    primary_balance_label = str(sidecar.metrics.get("primary_balance_label") or "").strip()
    if not primary_balance_label:
        issues.append(
            _issue(
                rule_id="primary_balance_label_missing",
                message="primary_balance_label must be non-empty",
                target="metrics.primary_balance_label",
            )
        )
    secondary_balance_label = str(sidecar.metrics.get("secondary_balance_label") or "").strip()
    balance_variables = sidecar.metrics.get("balance_variables")
    if not isinstance(balance_variables, list) or not balance_variables:
        issues.append(
            _issue(
                rule_id="balance_variables_missing",
                message="baseline missingness QC panel requires non-empty balance_variables metrics",
                target="metrics.balance_variables",
            )
        )
    else:
        seen_variable_ids: set[str] = set()
        seen_variable_labels: set[str] = set()
        saw_secondary_values = False
        for index, item in enumerate(balance_variables):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.balance_variables[{index}] must be an object")
            variable_id = str(item.get("variable_id") or "").strip()
            label = str(item.get("label") or "").strip()
            if not variable_id:
                issues.append(
                    _issue(
                        rule_id="balance_variable_id_missing",
                        message="balance variable ids must be non-empty",
                        target=f"metrics.balance_variables[{index}].variable_id",
                    )
                )
            elif variable_id in seen_variable_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_balance_variable_id",
                        message="balance variable ids must be unique",
                        target="metrics.balance_variables",
                        observed=variable_id,
                    )
                )
            else:
                seen_variable_ids.add(variable_id)
            if not label:
                issues.append(
                    _issue(
                        rule_id="balance_variable_label_missing",
                        message="balance variable labels must be non-empty",
                        target=f"metrics.balance_variables[{index}].label",
                    )
                )
            elif label in seen_variable_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_balance_variable_label",
                        message="balance variable labels must be unique",
                        target="metrics.balance_variables",
                        observed=label,
                    )
                )
            else:
                seen_variable_labels.add(label)
            primary_value = _require_numeric(
                item.get("primary_value"),
                label=f"layout_sidecar.metrics.balance_variables[{index}].primary_value",
            )
            if not math.isfinite(primary_value) or primary_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="balance_primary_value_invalid",
                        message="primary balance values must be finite and non-negative",
                        target=f"metrics.balance_variables[{index}].primary_value",
                        observed=primary_value,
                    )
                )
            if item.get("secondary_value") is not None:
                saw_secondary_values = True
                secondary_value = _require_numeric(
                    item.get("secondary_value"),
                    label=f"layout_sidecar.metrics.balance_variables[{index}].secondary_value",
                )
                if not math.isfinite(secondary_value) or secondary_value < 0.0:
                    issues.append(
                        _issue(
                            rule_id="balance_secondary_value_invalid",
                            message="secondary balance values must be finite and non-negative",
                            target=f"metrics.balance_variables[{index}].secondary_value",
                            observed=secondary_value,
                        )
                    )
        if saw_secondary_values and not secondary_balance_label:
            issues.append(
                _issue(
                    rule_id="balance_secondary_label_missing",
                    message="secondary balance values require a non-empty secondary_balance_label",
                    target="metrics.secondary_balance_label",
                )
            )

    missingness_rows = sidecar.metrics.get("missingness_rows")
    missingness_columns = sidecar.metrics.get("missingness_columns")
    missingness_cells = sidecar.metrics.get("missingness_cells")
    normalized_row_labels: list[str] = []
    normalized_column_labels: list[str] = []
    if not isinstance(missingness_rows, list) or not missingness_rows:
        issues.append(
            _issue(
                rule_id="missingness_rows_missing",
                message="missingness_rows must be non-empty",
                target="metrics.missingness_rows",
            )
        )
    else:
        seen_row_labels: set[str] = set()
        for index, item in enumerate(missingness_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.missingness_rows[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id="missingness_row_label_missing",
                        message="missingness row labels must be non-empty",
                        target=f"metrics.missingness_rows[{index}].label",
                    )
                )
                continue
            if label in seen_row_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_missingness_row_label",
                        message="missingness row labels must be unique",
                        target="metrics.missingness_rows",
                        observed=label,
                    )
                )
                continue
            seen_row_labels.add(label)
            normalized_row_labels.append(label)
    if not isinstance(missingness_columns, list) or not missingness_columns:
        issues.append(
            _issue(
                rule_id="missingness_columns_missing",
                message="missingness_columns must be non-empty",
                target="metrics.missingness_columns",
            )
        )
    else:
        seen_column_labels: set[str] = set()
        for index, item in enumerate(missingness_columns):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.missingness_columns[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id="missingness_column_label_missing",
                        message="missingness column labels must be non-empty",
                        target=f"metrics.missingness_columns[{index}].label",
                    )
                )
                continue
            if label in seen_column_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_missingness_column_label",
                        message="missingness column labels must be unique",
                        target="metrics.missingness_columns",
                        observed=label,
                    )
                )
                continue
            seen_column_labels.add(label)
            normalized_column_labels.append(label)
    if not isinstance(missingness_cells, list) or not missingness_cells:
        issues.append(
            _issue(
                rule_id="missingness_cells_missing",
                message="missingness_cells must be non-empty",
                target="metrics.missingness_cells",
            )
        )
    else:
        observed_rows: set[str] = set()
        observed_columns: set[str] = set()
        seen_coordinates: set[tuple[str, str]] = set()
        for index, item in enumerate(missingness_cells):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.missingness_cells[{index}] must be an object")
            column_label = str(item.get("x") or "").strip()
            row_label = str(item.get("y") or "").strip()
            coordinate = (column_label, row_label)
            if coordinate in seen_coordinates:
                issues.append(
                    _issue(
                        rule_id="duplicate_missingness_coordinate",
                        message="missingness cells must not repeat coordinates",
                        target="metrics.missingness_cells",
                        observed={"x": column_label, "y": row_label},
                    )
                )
            else:
                seen_coordinates.add(coordinate)
            observed_rows.add(row_label)
            observed_columns.add(column_label)
            value = _require_numeric(
                item.get("value"),
                label=f"layout_sidecar.metrics.missingness_cells[{index}].value",
            )
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                issues.append(
                    _issue(
                        rule_id="missingness_value_out_of_range",
                        message="missingness cell values must stay within [0, 1]",
                        target=f"metrics.missingness_cells[{index}].value",
                        observed=value,
                    )
                )
        expected_rows = set(normalized_row_labels)
        expected_columns = set(normalized_column_labels)
        if normalized_row_labels and observed_rows != expected_rows:
            issues.append(
                _issue(
                    rule_id="missingness_row_set_mismatch",
                    message="missingness cells must match the declared row labels",
                    target="metrics.missingness_cells",
                    observed=sorted(observed_rows),
                    expected=sorted(expected_rows),
                )
            )
        if normalized_column_labels and observed_columns != expected_columns:
            issues.append(
                _issue(
                    rule_id="missingness_column_set_mismatch",
                    message="missingness cells must match the declared column labels",
                    target="metrics.missingness_cells",
                    observed=sorted(observed_columns),
                    expected=sorted(expected_columns),
                )
            )
        expected_cell_count = len(normalized_row_labels) * len(normalized_column_labels)
        if expected_cell_count > 0 and len(seen_coordinates) != expected_cell_count:
            issues.append(
                _issue(
                    rule_id="declared_missingness_grid_incomplete",
                    message="missingness cells must cover the declared row-column grid exactly once",
                    target="metrics.missingness_cells",
                    observed={"cells": len(seen_coordinates)},
                    expected={"cells": expected_cell_count},
                )
            )

    qc_panel = panel_boxes_by_id.get("panel_qc")
    qc_cards = sidecar.metrics.get("qc_cards")
    if not isinstance(qc_cards, list) or not qc_cards:
        issues.append(
            _issue(
                rule_id="qc_cards_missing",
                message="qc_cards must be non-empty",
                target="metrics.qc_cards",
            )
        )
    else:
        seen_card_ids: set[str] = set()
        for index, item in enumerate(qc_cards):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.qc_cards[{index}] must be an object")
            card_id = str(item.get("card_id") or "").strip()
            if not card_id:
                issues.append(
                    _issue(
                        rule_id="qc_card_id_missing",
                        message="qc card ids must be non-empty",
                        target=f"metrics.qc_cards[{index}].card_id",
                    )
                )
            elif card_id in seen_card_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_qc_card_id",
                        message="qc card ids must be unique",
                        target="metrics.qc_cards",
                        observed=card_id,
                    )
                )
            else:
                seen_card_ids.add(card_id)
            label_box_id = str(item.get("label_box_id") or "").strip()
            value_box_id = str(item.get("value_box_id") or "").strip()
            label_box = layout_boxes_by_id.get(label_box_id)
            value_box = layout_boxes_by_id.get(value_box_id)
            if label_box is None:
                issues.append(
                    _issue(
                        rule_id="qc_card_label_missing",
                        message="qc cards must reference an existing card_label box",
                        target=f"metrics.qc_cards[{index}].label_box_id",
                        expected=label_box_id,
                    )
                )
            elif qc_panel is not None and not _box_within_box(label_box, qc_panel):
                issues.append(
                    _issue(
                        rule_id="qc_card_out_of_panel",
                        message="qc card labels must stay within the qc panel",
                        target="card_label",
                        box_refs=(label_box.box_id, qc_panel.box_id),
                    )
                )
            if value_box is None:
                issues.append(
                    _issue(
                        rule_id="qc_card_value_missing",
                        message="qc cards must reference an existing card_value box",
                        target=f"metrics.qc_cards[{index}].value_box_id",
                        expected=value_box_id,
                    )
                )
            elif qc_panel is not None and not _box_within_box(value_box, qc_panel):
                issues.append(
                    _issue(
                        rule_id="qc_card_out_of_panel",
                        message="qc card values must stay within the qc panel",
                        target="card_value",
                        box_refs=(value_box.box_id, qc_panel.box_id),
                    )
                )

    return issues
