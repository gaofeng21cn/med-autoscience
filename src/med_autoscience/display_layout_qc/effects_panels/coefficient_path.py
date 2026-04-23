from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _issue,
    _layout_override_flag,
    _require_non_empty_text,
    _require_numeric,
)

def _check_publication_coefficient_path_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "panel_label",
        "subplot_x_axis_title",
        "legend_title",
        "legend_label",
        "coefficient_row_label",
        "coefficient_marker",
        "coefficient_interval",
        "summary_card_label",
        "summary_card_value",
        "reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    path_panel = panel_boxes_by_id.get("path_panel")
    summary_panel = panel_boxes_by_id.get("summary_panel")
    if path_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="coefficient path qc requires path_panel and summary_panel",
                target="panel_boxes",
            )
        )
        return issues

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}

    if metrics.get("reference_value") is None:
        issues.append(
            _issue(
                rule_id="reference_value_missing",
                message="coefficient path qc requires a numeric reference_value",
                target="metrics.reference_value",
            )
        )
    else:
        _require_numeric(metrics.get("reference_value"), label="layout_sidecar.metrics.reference_value")

    path_panel_metrics = metrics.get("path_panel")
    if not isinstance(path_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="path_panel_metrics_missing",
                message="coefficient path qc requires path_panel metrics",
                target="metrics.path_panel",
            )
        )
        return issues
    summary_panel_metrics = metrics.get("summary_panel")
    if not isinstance(summary_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="summary_panel_metrics_missing",
                message="coefficient path qc requires summary_panel metrics",
                target="metrics.summary_panel",
            )
        )
        return issues

    reference_line_box = guide_box_by_id.get(str(path_panel_metrics.get("reference_line_box_id") or "").strip())
    if reference_line_box is None:
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="coefficient path qc requires one reference line inside the path panel",
                target="metrics.path_panel.reference_line_box_id",
                box_refs=(path_panel.box_id,),
            )
        )
    elif not _box_within_box(reference_line_box, path_panel):
        issues.append(
            _issue(
                rule_id="reference_line_outside_path_panel",
                message="coefficient path reference line must stay within the path panel",
                target=f"guide_boxes.{reference_line_box.box_id}",
                box_refs=(reference_line_box.box_id, path_panel.box_id),
            )
        )

    legend_title_box = layout_box_by_id.get(str(metrics.get("step_legend_title_box_id") or "").strip())
    if legend_title_box is None:
        issues.append(
            _issue(
                rule_id="step_legend_title_missing",
                message="coefficient path qc requires one step legend title box",
                target="metrics.step_legend_title_box_id",
            )
        )

    steps = metrics.get("steps")
    if not isinstance(steps, list) or not steps:
        issues.append(
            _issue(
                rule_id="steps_missing",
                message="coefficient path qc requires non-empty step metrics",
                target="metrics.steps",
            )
        )
        return issues
    if len(steps) < 2 or len(steps) > 5:
        issues.append(
            _issue(
                rule_id="step_count_invalid",
                message="coefficient path qc requires between 2 and 5 steps",
                target="metrics.steps",
                observed={"count": len(steps)},
                expected={"minimum": 2, "maximum": 5},
            )
        )

    expected_step_ids: list[str] = []
    seen_step_ids: set[str] = set()
    previous_step_order: int | None = None
    for step_index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"layout_sidecar.metrics.steps[{step_index}] must be an object")
        step_id = _require_non_empty_text(step.get("step_id"), label=f"layout_sidecar.metrics.steps[{step_index}].step_id")
        if step_id in seen_step_ids:
            issues.append(
                _issue(
                    rule_id="step_id_duplicate",
                    message="coefficient path step_id values must be unique",
                    target=f"metrics.steps[{step_index}].step_id",
                )
            )
        seen_step_ids.add(step_id)
        step_order = int(_require_numeric(step.get("step_order"), label=f"layout_sidecar.metrics.steps[{step_index}].step_order"))
        if previous_step_order is not None and step_order <= previous_step_order:
            issues.append(
                _issue(
                    rule_id="step_order_invalid",
                    message="coefficient path steps must have strictly increasing step_order",
                    target=f"metrics.steps[{step_index}].step_order",
                )
            )
        previous_step_order = step_order
        legend_label_box = layout_box_by_id.get(str(step.get("legend_label_box_id") or "").strip())
        if legend_label_box is None:
            issues.append(
                _issue(
                    rule_id="step_legend_label_missing",
                    message="every coefficient path step must reference a legend label box",
                    target=f"metrics.steps[{step_index}].legend_label_box_id",
                )
            )
        expected_step_ids.append(step_id)

    coefficient_rows = metrics.get("coefficient_rows")
    if not isinstance(coefficient_rows, list) or not coefficient_rows:
        issues.append(
            _issue(
                rule_id="coefficient_rows_missing",
                message="coefficient path qc requires non-empty coefficient_rows metrics",
                target="metrics.coefficient_rows",
            )
        )
        return issues

    declared_step_id_set = set(expected_step_ids)
    for row_index, row in enumerate(coefficient_rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.coefficient_rows[{row_index}] must be an object")
        label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="coefficient_row_label_missing",
                    message="coefficient path rows must reference a label box",
                    target=f"metrics.coefficient_rows[{row_index}].label_box_id",
                    box_refs=(path_panel.box_id,),
                )
            )
        elif _boxes_overlap(label_box, path_panel):
            issues.append(
                _issue(
                    rule_id="coefficient_row_label_panel_overlap",
                    message="coefficient row label must stay outside the path panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, path_panel.box_id),
                )
            )

        points = row.get("points")
        if not isinstance(points, list) or not points:
            issues.append(
                _issue(
                    rule_id="coefficient_points_missing",
                    message="every coefficient row must provide non-empty points",
                    target=f"metrics.coefficient_rows[{row_index}].points",
                )
            )
            continue

        seen_row_step_ids: set[str] = set()
        for point_index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.coefficient_rows[{row_index}].points[{point_index}] must be an object"
                )
            step_id = _require_non_empty_text(
                point.get("step_id"),
                label=f"layout_sidecar.metrics.coefficient_rows[{row_index}].points[{point_index}].step_id",
            )
            seen_row_step_ids.add(step_id)
            marker_box = layout_box_by_id.get(str(point.get("marker_box_id") or "").strip())
            interval_box = layout_box_by_id.get(str(point.get("interval_box_id") or "").strip())
            if marker_box is None or interval_box is None:
                issues.append(
                    _issue(
                        rule_id="coefficient_point_box_missing",
                        message="coefficient path points must reference marker and interval boxes",
                        target=f"metrics.coefficient_rows[{row_index}].points[{point_index}]",
                        box_refs=(path_panel.box_id,),
                    )
                )
                continue
            if not _box_within_box(marker_box, path_panel):
                issues.append(
                    _issue(
                        rule_id="coefficient_marker_outside_path_panel",
                        message="coefficient marker must stay within the path panel",
                        target=f"layout_boxes.{marker_box.box_id}",
                        box_refs=(marker_box.box_id, path_panel.box_id),
                    )
                )
            if not _box_within_box(interval_box, path_panel):
                issues.append(
                    _issue(
                        rule_id="coefficient_interval_outside_path_panel",
                        message="coefficient interval must stay within the path panel",
                        target=f"layout_boxes.{interval_box.box_id}",
                        box_refs=(interval_box.box_id, path_panel.box_id),
                    )
                )
        if seen_row_step_ids != declared_step_id_set:
            issues.append(
                _issue(
                    rule_id="coefficient_step_coverage_mismatch",
                    message="coefficient path rows must cover every declared step exactly once",
                    target=f"metrics.coefficient_rows[{row_index}].points",
                    observed={"step_ids": sorted(seen_row_step_ids)},
                    expected={"step_ids": sorted(declared_step_id_set)},
                )
            )

    summary_cards = metrics.get("summary_cards")
    if not isinstance(summary_cards, list) or not summary_cards:
        issues.append(
            _issue(
                rule_id="summary_cards_missing",
                message="coefficient path qc requires non-empty summary_cards metrics",
                target="metrics.summary_cards",
            )
        )
        return issues

    for card_index, card in enumerate(summary_cards):
        if not isinstance(card, dict):
            raise ValueError(f"layout_sidecar.metrics.summary_cards[{card_index}] must be an object")
        label_box = layout_box_by_id.get(str(card.get("label_box_id") or "").strip())
        value_box = layout_box_by_id.get(str(card.get("value_box_id") or "").strip())
        detail_box_id = str(card.get("detail_box_id") or "").strip()
        detail_box = layout_box_by_id.get(detail_box_id) if detail_box_id else None
        if label_box is None or value_box is None:
            issues.append(
                _issue(
                    rule_id="summary_card_box_missing",
                    message="coefficient path summary cards must reference label and value boxes",
                    target=f"metrics.summary_cards[{card_index}]",
                    box_refs=(summary_panel.box_id,),
                )
            )
            continue
        if not _box_within_box(label_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="summary_card_label_outside_panel",
                    message="summary card label must stay within the summary panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, summary_panel.box_id),
                )
            )
        if not _box_within_box(value_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="summary_card_value_outside_panel",
                    message="summary card value must stay within the summary panel",
                    target=f"layout_boxes.{value_box.box_id}",
                    box_refs=(value_box.box_id, summary_panel.box_id),
                )
            )
        if detail_box is not None and not _box_within_box(detail_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="summary_card_detail_outside_panel",
                    message="summary card detail must stay within the summary panel",
                    target=f"layout_boxes.{detail_box.box_id}",
                    box_refs=(detail_box.box_id, summary_panel.box_id),
                )
            )

    return issues
