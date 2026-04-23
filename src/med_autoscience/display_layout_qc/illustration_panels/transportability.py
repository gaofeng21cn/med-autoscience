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

def _check_publication_center_coverage_batch_transportability_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
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
                message="center coverage batch transportability panel requires exactly three panel boxes",
                target="panel_boxes",
                expected={"count": 3},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    panel_label_to_panel_id = {
        "A": "panel_coverage",
        "B": "panel_batch",
        "C": "panel_transportability",
    }
    title_boxes = {
        "coverage_panel_title": "panel_coverage",
        "batch_panel_title": "panel_batch",
        "transportability_panel_title": "panel_transportability",
    }
    for panel_label, panel_id in panel_label_to_panel_id.items():
        label_box = layout_boxes_by_id.get(f"panel_label_{panel_label}")
        panel_box = panel_boxes_by_id.get(panel_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="center coverage batch transportability panel requires the fixed three-panel layout",
                    target="panel_boxes",
                    expected=panel_id,
                )
            )
            continue
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="center coverage batch transportability panel labels must be present for every panel",
                    target="panel_label",
                    expected=f"panel_label_{panel_label}",
                )
            )
            continue
        if not _box_within_box(label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="center coverage batch transportability panel labels must stay within their parent panel",
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
                    message="center coverage batch transportability panel requires all three panel titles",
                    target="panel_title",
                    expected=title_box_id,
                )
            )
            continue
        if panel_box is not None:
            aligned_horizontally = title_box.x0 >= panel_box.x0 - 0.02 and title_box.x1 <= panel_box.x1 + 0.02
            close_to_panel_top = title_box.y0 >= panel_box.y0 - 0.02 and title_box.y1 <= panel_box.y1 + 0.08
            if not (aligned_horizontally and close_to_panel_top):
                issues.append(
                    _issue(
                        rule_id="panel_title_out_of_panel",
                        message="center coverage batch transportability panel titles must stay tightly aligned with their parent panel",
                        target="panel_title",
                        box_refs=(title_box.box_id, panel_box.box_id),
                    )
                )

    axis_title_pairs = (
        ("coverage_x_axis_title", "panel_coverage"),
        ("batch_x_axis_title", "panel_batch"),
        ("batch_y_axis_title", "panel_batch"),
    )
    for axis_box_id, panel_id in axis_title_pairs:
        axis_box = layout_boxes_by_id.get(axis_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if axis_box is None:
            issues.append(
                _issue(
                    rule_id="axis_title_missing",
                    message="center coverage batch transportability panel must expose the bounded axis-title surface",
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
                        message="center coverage batch transportability panel axis titles must stay tightly aligned with their parent panel",
                        target=axis_box.box_type,
                        box_refs=(axis_box.box_id, panel_box.box_id),
                    )
                )

    if not _boxes_of_type(sidecar.guide_boxes, "reference_line"):
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="center coverage batch transportability panel requires a batch threshold reference line",
                target="reference_line",
            )
        )
    if not _boxes_of_type(sidecar.guide_boxes, "colorbar"):
        issues.append(
            _issue(
                rule_id="colorbar_missing",
                message="center coverage batch transportability panel requires a batch colorbar guide box",
                target="colorbar",
            )
        )

    batch_threshold = _require_numeric(sidecar.metrics.get("batch_threshold"), label="layout_sidecar.metrics.batch_threshold")
    if not math.isfinite(batch_threshold) or batch_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="batch_threshold_invalid",
                message="batch_threshold must be positive and finite",
                target="metrics.batch_threshold",
                observed=batch_threshold,
            )
        )

    center_rows = sidecar.metrics.get("center_rows")
    if not isinstance(center_rows, list) or not center_rows:
        issues.append(
            _issue(
                rule_id="center_rows_missing",
                message="center_rows must be non-empty",
                target="metrics.center_rows",
            )
        )
    else:
        seen_center_ids: set[str] = set()
        seen_center_labels: set[str] = set()
        for index, item in enumerate(center_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.center_rows[{index}] must be an object")
            center_id = str(item.get("center_id") or "").strip()
            center_label = str(item.get("center_label") or "").strip()
            cohort_role = str(item.get("cohort_role") or "").strip()
            if not center_id:
                issues.append(_issue(rule_id="center_row_id_missing", message="center row ids must be non-empty", target=f"metrics.center_rows[{index}].center_id"))
            elif center_id in seen_center_ids:
                issues.append(_issue(rule_id="duplicate_center_row_id", message="center row ids must be unique", target="metrics.center_rows", observed=center_id))
            else:
                seen_center_ids.add(center_id)
            if not center_label:
                issues.append(_issue(rule_id="center_row_label_missing", message="center row labels must be non-empty", target=f"metrics.center_rows[{index}].center_label"))
            elif center_label in seen_center_labels:
                issues.append(_issue(rule_id="duplicate_center_row_label", message="center row labels must be unique", target="metrics.center_rows", observed=center_label))
            else:
                seen_center_labels.add(center_label)
            if not cohort_role:
                issues.append(_issue(rule_id="center_row_cohort_role_missing", message="center row cohort roles must be non-empty", target=f"metrics.center_rows[{index}].cohort_role"))
            support_count = _require_numeric(item.get("support_count"), label=f"layout_sidecar.metrics.center_rows[{index}].support_count")
            event_count = _require_numeric(item.get("event_count"), label=f"layout_sidecar.metrics.center_rows[{index}].event_count")
            if not float(support_count).is_integer() or support_count <= 0:
                issues.append(_issue(rule_id="center_support_count_invalid", message="center support counts must be positive integers", target=f"metrics.center_rows[{index}].support_count", observed=support_count))
            if not float(event_count).is_integer() or event_count < 0:
                issues.append(_issue(rule_id="center_event_count_invalid", message="center event counts must be non-negative integers", target=f"metrics.center_rows[{index}].event_count", observed=event_count))
            elif event_count > support_count:
                issues.append(_issue(rule_id="center_event_count_exceeds_support", message="center event counts must not exceed support counts", target=f"metrics.center_rows[{index}].event_count", observed={"event_count": event_count, "support_count": support_count}))

    batch_rows = sidecar.metrics.get("batch_rows")
    batch_columns = sidecar.metrics.get("batch_columns")
    batch_cells = sidecar.metrics.get("batch_cells")
    normalized_row_labels: list[str] = []
    normalized_column_labels: list[str] = []
    if not isinstance(batch_rows, list) or not batch_rows:
        issues.append(_issue(rule_id="batch_rows_missing", message="batch_rows must be non-empty", target="metrics.batch_rows"))
    else:
        seen_row_labels: set[str] = set()
        for index, item in enumerate(batch_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_rows[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(_issue(rule_id="batch_row_label_missing", message="batch row labels must be non-empty", target=f"metrics.batch_rows[{index}].label"))
                continue
            if label in seen_row_labels:
                issues.append(_issue(rule_id="duplicate_batch_row_label", message="batch row labels must be unique", target="metrics.batch_rows", observed=label))
            else:
                seen_row_labels.add(label)
                normalized_row_labels.append(label)
    if not isinstance(batch_columns, list) or not batch_columns:
        issues.append(_issue(rule_id="batch_columns_missing", message="batch_columns must be non-empty", target="metrics.batch_columns"))
    else:
        seen_column_labels: set[str] = set()
        for index, item in enumerate(batch_columns):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_columns[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(_issue(rule_id="batch_column_label_missing", message="batch column labels must be non-empty", target=f"metrics.batch_columns[{index}].label"))
                continue
            if label in seen_column_labels:
                issues.append(_issue(rule_id="duplicate_batch_column_label", message="batch column labels must be unique", target="metrics.batch_columns", observed=label))
            else:
                seen_column_labels.add(label)
                normalized_column_labels.append(label)
    if not isinstance(batch_cells, list) or not batch_cells:
        issues.append(_issue(rule_id="batch_cells_missing", message="batch_cells must be non-empty", target="metrics.batch_cells"))
    else:
        expected_rows = set(normalized_row_labels)
        expected_columns = set(normalized_column_labels)
        seen_coordinates: set[tuple[str, str]] = set()
        observed_rows: set[str] = set()
        observed_columns: set[str] = set()
        for index, item in enumerate(batch_cells):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_cells[{index}] must be an object")
            column_label = str(item.get("x") or "").strip()
            row_label = str(item.get("y") or "").strip()
            if not column_label or not row_label:
                issues.append(_issue(rule_id="batch_cell_coordinate_missing", message="batch cells must declare x and y labels", target=f"metrics.batch_cells[{index}]"))
                continue
            if expected_columns and column_label not in expected_columns:
                issues.append(_issue(rule_id="batch_cell_unknown_column", message="batch cells must reference declared batch columns", target=f"metrics.batch_cells[{index}].x", observed=column_label))
            if expected_rows and row_label not in expected_rows:
                issues.append(_issue(rule_id="batch_cell_unknown_row", message="batch cells must reference declared batch rows", target=f"metrics.batch_cells[{index}].y", observed=row_label))
            coordinate = (column_label, row_label)
            if coordinate in seen_coordinates:
                issues.append(_issue(rule_id="duplicate_batch_cell_coordinate", message="batch grid coordinates must be unique", target="metrics.batch_cells", observed={"x": column_label, "y": row_label}))
            else:
                seen_coordinates.add(coordinate)
            observed_rows.add(row_label)
            observed_columns.add(column_label)
            value = _require_numeric(item.get("value"), label=f"layout_sidecar.metrics.batch_cells[{index}].value")
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                issues.append(_issue(rule_id="batch_cell_value_invalid", message="batch cell values must stay within [0, 1]", target=f"metrics.batch_cells[{index}].value", observed=value))
        if expected_rows and observed_rows != expected_rows:
            issues.append(_issue(rule_id="declared_batch_rows_mismatch", message="declared batch rows must match observed cell rows", target="metrics.batch_rows", expected=sorted(expected_rows), observed=sorted(observed_rows)))
        if expected_columns and observed_columns != expected_columns:
            issues.append(_issue(rule_id="declared_batch_columns_mismatch", message="declared batch columns must match observed cell columns", target="metrics.batch_columns", expected=sorted(expected_columns), observed=sorted(observed_columns)))
        if expected_rows and expected_columns and len(seen_coordinates) != len(expected_rows) * len(expected_columns):
            issues.append(_issue(rule_id="declared_batch_grid_incomplete", message="declared batch grid must be complete", target="metrics.batch_cells", expected={"count": len(expected_rows) * len(expected_columns)}, observed={"count": len(seen_coordinates)}))

    transportability_cards = sidecar.metrics.get("transportability_cards")
    transport_panel = panel_boxes_by_id.get("panel_transportability")
    if not isinstance(transportability_cards, list) or not transportability_cards:
        issues.append(_issue(rule_id="transportability_cards_missing", message="transportability_cards must be non-empty", target="metrics.transportability_cards"))
    else:
        seen_card_ids: set[str] = set()
        for index, item in enumerate(transportability_cards):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.transportability_cards[{index}] must be an object")
            card_id = str(item.get("card_id") or "").strip()
            label_box_id = str(item.get("label_box_id") or "").strip()
            value_box_id = str(item.get("value_box_id") or "").strip()
            if not card_id:
                issues.append(_issue(rule_id="transportability_card_id_missing", message="transportability card ids must be non-empty", target=f"metrics.transportability_cards[{index}].card_id"))
            elif card_id in seen_card_ids:
                issues.append(_issue(rule_id="duplicate_transportability_card_id", message="transportability card ids must be unique", target="metrics.transportability_cards", observed=card_id))
            else:
                seen_card_ids.add(card_id)
            label_box = layout_boxes_by_id.get(label_box_id)
            value_box = layout_boxes_by_id.get(value_box_id)
            if label_box is None:
                issues.append(_issue(rule_id="transportability_card_label_missing", message="transportability cards must reference an existing card_label box", target=f"metrics.transportability_cards[{index}].label_box_id", expected=label_box_id))
            elif transport_panel is not None and not _box_within_box(label_box, transport_panel):
                issues.append(_issue(rule_id="transportability_card_out_of_panel", message="transportability card labels must stay within the transportability panel", target="card_label", box_refs=(label_box.box_id, transport_panel.box_id)))
            if value_box is None:
                issues.append(_issue(rule_id="transportability_card_value_missing", message="transportability cards must reference an existing card_value box", target=f"metrics.transportability_cards[{index}].value_box_id", expected=value_box_id))
            elif transport_panel is not None and not _box_within_box(value_box, transport_panel):
                issues.append(_issue(rule_id="transportability_card_out_of_panel", message="transportability card values must stay within the transportability panel", target="card_value", box_refs=(value_box.box_id, transport_panel.box_id)))

    return issues
def _check_publication_transportability_recalibration_governance_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel",
                "panel_label",
                "panel_title",
                "subplot_x_axis_title",
                "row_label",
                "row_metric",
                "row_action",
            ),
        )
    )

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 3:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="transportability recalibration governance panel requires exactly three panel boxes",
                target="panel_boxes",
                expected={"count": 3},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    panel_label_to_panel_id = {
        "A": "panel_coverage",
        "B": "panel_batch",
        "C": "panel_recalibration",
    }
    title_boxes = {
        "coverage_panel_title": "panel_coverage",
        "batch_panel_title": "panel_batch",
        "recalibration_panel_title": "panel_recalibration",
    }
    for panel_label, panel_id in panel_label_to_panel_id.items():
        label_box = layout_boxes_by_id.get(f"panel_label_{panel_label}")
        panel_box = panel_boxes_by_id.get(panel_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="transportability recalibration governance panel requires the fixed three-panel layout",
                    target="panel_boxes",
                    expected=panel_id,
                )
            )
            continue
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="transportability recalibration governance panel labels must be present for every panel",
                    target="panel_label",
                    expected=f"panel_label_{panel_label}",
                )
            )
            continue
        if not _box_within_box(label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="transportability recalibration governance panel labels must stay within their parent panel",
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
                    message="transportability recalibration governance panel requires all three panel titles",
                    target="panel_title",
                    expected=title_box_id,
                )
            )
            continue
        if panel_box is not None:
            aligned_horizontally = title_box.x0 >= panel_box.x0 - 0.02 and title_box.x1 <= panel_box.x1 + 0.02
            close_to_panel_top = title_box.y0 >= panel_box.y0 - 0.02 and title_box.y1 <= panel_box.y1 + 0.08
            if not (aligned_horizontally and close_to_panel_top):
                issues.append(
                    _issue(
                        rule_id="panel_title_out_of_panel",
                        message="transportability recalibration governance panel titles must stay tightly aligned with their parent panel",
                        target="panel_title",
                        box_refs=(title_box.box_id, panel_box.box_id),
                    )
                )

    axis_title_pairs = (
        ("coverage_x_axis_title", "panel_coverage"),
        ("batch_x_axis_title", "panel_batch"),
        ("batch_y_axis_title", "panel_batch"),
    )
    for axis_box_id, panel_id in axis_title_pairs:
        axis_box = layout_boxes_by_id.get(axis_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if axis_box is None:
            issues.append(
                _issue(
                    rule_id="axis_title_missing",
                    message="transportability recalibration governance panel must expose the bounded axis-title surface",
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
                        message="transportability recalibration governance panel axis titles must stay tightly aligned with their parent panel",
                        target=axis_box.box_type,
                        box_refs=(axis_box.box_id, panel_box.box_id),
                    )
                )

    if not _boxes_of_type(sidecar.guide_boxes, "reference_line"):
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="transportability recalibration governance panel requires a batch threshold reference line",
                target="reference_line",
            )
        )
    if not _boxes_of_type(sidecar.guide_boxes, "colorbar"):
        issues.append(
            _issue(
                rule_id="colorbar_missing",
                message="transportability recalibration governance panel requires a batch colorbar guide box",
                target="colorbar",
            )
        )

    batch_threshold = _require_numeric(sidecar.metrics.get("batch_threshold"), label="layout_sidecar.metrics.batch_threshold")
    if not math.isfinite(batch_threshold) or batch_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="batch_threshold_invalid",
                message="batch_threshold must be positive and finite",
                target="metrics.batch_threshold",
                observed=batch_threshold,
            )
        )

    center_rows = sidecar.metrics.get("center_rows")
    expected_center_ids: set[str] = set()
    if not isinstance(center_rows, list) or not center_rows:
        issues.append(
            _issue(
                rule_id="center_rows_missing",
                message="center_rows must be non-empty",
                target="metrics.center_rows",
            )
        )
    else:
        seen_center_ids: set[str] = set()
        seen_center_labels: set[str] = set()
        for index, item in enumerate(center_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.center_rows[{index}] must be an object")
            center_id = str(item.get("center_id") or "").strip()
            center_label = str(item.get("center_label") or "").strip()
            cohort_role = str(item.get("cohort_role") or "").strip()
            if not center_id:
                issues.append(_issue(rule_id="center_row_id_missing", message="center row ids must be non-empty", target=f"metrics.center_rows[{index}].center_id"))
            elif center_id in seen_center_ids:
                issues.append(_issue(rule_id="duplicate_center_row_id", message="center row ids must be unique", target="metrics.center_rows", observed=center_id))
            else:
                seen_center_ids.add(center_id)
                expected_center_ids.add(center_id)
            if not center_label:
                issues.append(_issue(rule_id="center_row_label_missing", message="center row labels must be non-empty", target=f"metrics.center_rows[{index}].center_label"))
            elif center_label in seen_center_labels:
                issues.append(_issue(rule_id="duplicate_center_row_label", message="center row labels must be unique", target="metrics.center_rows", observed=center_label))
            else:
                seen_center_labels.add(center_label)
            if not cohort_role:
                issues.append(_issue(rule_id="center_row_cohort_role_missing", message="center row cohort roles must be non-empty", target=f"metrics.center_rows[{index}].cohort_role"))
            support_count = _require_numeric(item.get("support_count"), label=f"layout_sidecar.metrics.center_rows[{index}].support_count")
            event_count = _require_numeric(item.get("event_count"), label=f"layout_sidecar.metrics.center_rows[{index}].event_count")
            if not float(support_count).is_integer() or support_count <= 0:
                issues.append(_issue(rule_id="center_support_count_invalid", message="center support counts must be positive integers", target=f"metrics.center_rows[{index}].support_count", observed=support_count))
            if not float(event_count).is_integer() or event_count < 0:
                issues.append(_issue(rule_id="center_event_count_invalid", message="center event counts must be non-negative integers", target=f"metrics.center_rows[{index}].event_count", observed=event_count))
            elif event_count > support_count:
                issues.append(_issue(rule_id="center_event_count_exceeds_support", message="center event counts must not exceed support counts", target=f"metrics.center_rows[{index}].event_count", observed={"event_count": event_count, "support_count": support_count}))

    batch_rows = sidecar.metrics.get("batch_rows")
    batch_columns = sidecar.metrics.get("batch_columns")
    batch_cells = sidecar.metrics.get("batch_cells")
    normalized_row_labels: list[str] = []
    normalized_column_labels: list[str] = []
    if not isinstance(batch_rows, list) or not batch_rows:
        issues.append(_issue(rule_id="batch_rows_missing", message="batch_rows must be non-empty", target="metrics.batch_rows"))
    else:
        seen_row_labels: set[str] = set()
        for index, item in enumerate(batch_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_rows[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(_issue(rule_id="batch_row_label_missing", message="batch row labels must be non-empty", target=f"metrics.batch_rows[{index}].label"))
                continue
            if label in seen_row_labels:
                issues.append(_issue(rule_id="duplicate_batch_row_label", message="batch row labels must be unique", target="metrics.batch_rows", observed=label))
            else:
                seen_row_labels.add(label)
                normalized_row_labels.append(label)
    if not isinstance(batch_columns, list) or not batch_columns:
        issues.append(_issue(rule_id="batch_columns_missing", message="batch_columns must be non-empty", target="metrics.batch_columns"))
    else:
        seen_column_labels: set[str] = set()
        for index, item in enumerate(batch_columns):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_columns[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(_issue(rule_id="batch_column_label_missing", message="batch column labels must be non-empty", target=f"metrics.batch_columns[{index}].label"))
                continue
            if label in seen_column_labels:
                issues.append(_issue(rule_id="duplicate_batch_column_label", message="batch column labels must be unique", target="metrics.batch_columns", observed=label))
            else:
                seen_column_labels.add(label)
                normalized_column_labels.append(label)
    if not isinstance(batch_cells, list) or not batch_cells:
        issues.append(_issue(rule_id="batch_cells_missing", message="batch_cells must be non-empty", target="metrics.batch_cells"))
    else:
        expected_rows = set(normalized_row_labels)
        expected_columns = set(normalized_column_labels)
        seen_coordinates: set[tuple[str, str]] = set()
        observed_rows: set[str] = set()
        observed_columns: set[str] = set()
        for index, item in enumerate(batch_cells):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_cells[{index}] must be an object")
            column_label = str(item.get("x") or "").strip()
            row_label = str(item.get("y") or "").strip()
            if not column_label or not row_label:
                issues.append(_issue(rule_id="batch_cell_coordinate_missing", message="batch cells must declare x and y labels", target=f"metrics.batch_cells[{index}]"))
                continue
            if expected_columns and column_label not in expected_columns:
                issues.append(_issue(rule_id="batch_cell_unknown_column", message="batch cells must reference declared batch columns", target=f"metrics.batch_cells[{index}].x", observed=column_label))
            if expected_rows and row_label not in expected_rows:
                issues.append(_issue(rule_id="batch_cell_unknown_row", message="batch cells must reference declared batch rows", target=f"metrics.batch_cells[{index}].y", observed=row_label))
            coordinate = (column_label, row_label)
            if coordinate in seen_coordinates:
                issues.append(_issue(rule_id="duplicate_batch_cell_coordinate", message="batch grid coordinates must be unique", target="metrics.batch_cells", observed={"x": column_label, "y": row_label}))
            else:
                seen_coordinates.add(coordinate)
            observed_rows.add(row_label)
            observed_columns.add(column_label)
            value = _require_numeric(item.get("value"), label=f"layout_sidecar.metrics.batch_cells[{index}].value")
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                issues.append(_issue(rule_id="batch_cell_value_invalid", message="batch cell values must stay within [0, 1]", target=f"metrics.batch_cells[{index}].value", observed=value))
        if expected_rows and observed_rows != expected_rows:
            issues.append(_issue(rule_id="declared_batch_rows_mismatch", message="declared batch rows must match observed cell rows", target="metrics.batch_rows", expected=sorted(expected_rows), observed=sorted(observed_rows)))
        if expected_columns and observed_columns != expected_columns:
            issues.append(_issue(rule_id="declared_batch_columns_mismatch", message="declared batch columns must match observed cell columns", target="metrics.batch_columns", expected=sorted(expected_columns), observed=sorted(observed_columns)))
        if expected_rows and expected_columns and len(seen_coordinates) != len(expected_rows) * len(expected_columns):
            issues.append(_issue(rule_id="declared_batch_grid_incomplete", message="declared batch grid must be complete", target="metrics.batch_cells", expected={"count": len(expected_rows) * len(expected_columns)}, observed={"count": len(seen_coordinates)}))

    slope_acceptance_lower = _require_numeric(
        sidecar.metrics.get("slope_acceptance_lower"),
        label="layout_sidecar.metrics.slope_acceptance_lower",
    )
    slope_acceptance_upper = _require_numeric(
        sidecar.metrics.get("slope_acceptance_upper"),
        label="layout_sidecar.metrics.slope_acceptance_upper",
    )
    if (
        not math.isfinite(slope_acceptance_lower)
        or not math.isfinite(slope_acceptance_upper)
        or slope_acceptance_lower <= 0.0
        or slope_acceptance_upper <= 0.0
        or slope_acceptance_lower >= slope_acceptance_upper
    ):
        issues.append(
            _issue(
                rule_id="slope_acceptance_band_invalid",
                message="slope acceptance band must be positive, finite, and ordered",
                target="metrics.slope_acceptance_lower",
                observed={"lower": slope_acceptance_lower, "upper": slope_acceptance_upper},
            )
        )
    oe_ratio_acceptance_lower = _require_numeric(
        sidecar.metrics.get("oe_ratio_acceptance_lower"),
        label="layout_sidecar.metrics.oe_ratio_acceptance_lower",
    )
    oe_ratio_acceptance_upper = _require_numeric(
        sidecar.metrics.get("oe_ratio_acceptance_upper"),
        label="layout_sidecar.metrics.oe_ratio_acceptance_upper",
    )
    if (
        not math.isfinite(oe_ratio_acceptance_lower)
        or not math.isfinite(oe_ratio_acceptance_upper)
        or oe_ratio_acceptance_lower <= 0.0
        or oe_ratio_acceptance_upper <= 0.0
        or oe_ratio_acceptance_lower >= oe_ratio_acceptance_upper
    ):
        issues.append(
            _issue(
                rule_id="oe_ratio_acceptance_band_invalid",
                message="oe_ratio acceptance band must be positive, finite, and ordered",
                target="metrics.oe_ratio_acceptance_lower",
                observed={"lower": oe_ratio_acceptance_lower, "upper": oe_ratio_acceptance_upper},
            )
        )

    recalibration_rows = sidecar.metrics.get("recalibration_rows")
    recalibration_panel = panel_boxes_by_id.get("panel_recalibration")
    if not isinstance(recalibration_rows, list) or not recalibration_rows:
        issues.append(
            _issue(
                rule_id="recalibration_rows_missing",
                message="recalibration_rows must be non-empty",
                target="metrics.recalibration_rows",
            )
        )
    else:
        seen_center_ids: set[str] = set()
        for index, item in enumerate(recalibration_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.recalibration_rows[{index}] must be an object")
            center_id = str(item.get("center_id") or "").strip()
            if not center_id:
                issues.append(_issue(rule_id="recalibration_center_id_missing", message="recalibration center ids must be non-empty", target=f"metrics.recalibration_rows[{index}].center_id"))
            elif center_id in seen_center_ids:
                issues.append(_issue(rule_id="duplicate_recalibration_center_id", message="recalibration center ids must be unique", target="metrics.recalibration_rows", observed=center_id))
            else:
                seen_center_ids.add(center_id)
            if expected_center_ids and center_id not in expected_center_ids:
                issues.append(_issue(rule_id="recalibration_center_unknown", message="recalibration rows must reference declared centers", target=f"metrics.recalibration_rows[{index}].center_id", observed=center_id))
            slope = _require_numeric(item.get("slope"), label=f"layout_sidecar.metrics.recalibration_rows[{index}].slope")
            oe_ratio = _require_numeric(item.get("oe_ratio"), label=f"layout_sidecar.metrics.recalibration_rows[{index}].oe_ratio")
            if not math.isfinite(slope) or slope <= 0.0:
                issues.append(_issue(rule_id="recalibration_slope_invalid", message="recalibration slopes must be positive and finite", target=f"metrics.recalibration_rows[{index}].slope", observed=slope))
            if not math.isfinite(oe_ratio) or oe_ratio <= 0.0:
                issues.append(_issue(rule_id="recalibration_oe_ratio_invalid", message="recalibration oe ratios must be positive and finite", target=f"metrics.recalibration_rows[{index}].oe_ratio", observed=oe_ratio))
            label_box_id = str(item.get("label_box_id") or "").strip()
            slope_box_id = str(item.get("slope_box_id") or "").strip()
            oe_ratio_box_id = str(item.get("oe_ratio_box_id") or "").strip()
            action_box_id = str(item.get("action_box_id") or "").strip()
            row_boxes = (
                ("row_label", label_box_id),
                ("row_metric", slope_box_id),
                ("row_metric", oe_ratio_box_id),
                ("row_action", action_box_id),
            )
            for box_type, box_id in row_boxes:
                box = layout_boxes_by_id.get(box_id)
                if box is None:
                    issues.append(_issue(rule_id="recalibration_row_box_missing", message="recalibration rows must reference existing layout boxes", target=f"metrics.recalibration_rows[{index}]", expected=box_id))
                elif recalibration_panel is not None and not _box_within_box(box, recalibration_panel):
                    issues.append(_issue(rule_id="recalibration_row_out_of_panel", message="recalibration row boxes must stay within the recalibration panel", target=box_type, box_refs=(box.box_id, recalibration_panel.box_id)))
        if expected_center_ids and seen_center_ids != expected_center_ids:
            issues.append(
                _issue(
                    rule_id="recalibration_rows_incomplete",
                    message="recalibration rows must cover every declared center exactly once",
                    target="metrics.recalibration_rows",
                    expected=sorted(expected_center_ids),
                    observed=sorted(seen_center_ids),
                )
            )

    return issues
