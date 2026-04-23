from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_of_type,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_composite_panel_label_anchors,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _issue,
    _layout_override_flag,
    _primary_panel,
    _require_non_empty_text,
    _require_numeric,
)

def _check_publication_forest_plot(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("reference_line", "row_label", "estimate_marker", "ci_segment")))
    panel = _primary_panel(sidecar)
    if panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="forest plot requires a panel box",
                target="panel",
                expected="present",
            )
        )
        return issues

    for row_label in _boxes_of_type(sidecar.layout_boxes, "row_label"):
        if not _boxes_overlap(row_label, panel):
            continue
        issues.append(
            _issue(
                rule_id="row_label_panel_overlap",
                message="row label must not overlap the forest panel",
                target="row_label",
                box_refs=(row_label.box_id, panel.box_id),
            )
        )

    rows = sidecar.metrics.get("rows")
    if not isinstance(rows, list) or not rows:
        issues.append(
            _issue(
                rule_id="rows_missing",
                message="forest qc requires non-empty row metrics",
                target="metrics.rows",
            )
        )
        return issues
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.rows[{index}] must be an object")
        lower = _require_numeric(row.get("lower"), label=f"layout_sidecar.metrics.rows[{index}].lower")
        estimate = _require_numeric(row.get("estimate"), label=f"layout_sidecar.metrics.rows[{index}].estimate")
        upper = _require_numeric(row.get("upper"), label=f"layout_sidecar.metrics.rows[{index}].upper")
        if lower <= estimate <= upper:
            continue
        issues.append(
            _issue(
                rule_id="estimate_outside_interval",
                message="estimate must lie within the confidence interval",
                target=f"metrics.rows[{index}]",
                observed={"lower": lower, "estimate": estimate, "upper": upper},
            )
        )
    return issues
def _check_publication_compact_effect_estimate_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "panel_label",
        "subplot_x_axis_title",
        "row_label",
        "estimate_marker",
        "ci_segment",
        "reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}

    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    if metrics.get("reference_value") is None:
        issues.append(
            _issue(
                rule_id="reference_value_missing",
                message="compact effect estimate qc requires a numeric reference_value",
                target="metrics.reference_value",
            )
        )
    else:
        _require_numeric(metrics.get("reference_value"), label="layout_sidecar.metrics.reference_value")

    panels = metrics.get("panels")
    if not isinstance(panels, list) or not panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="compact effect estimate qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues
    if len(panels) < 2 or len(panels) > 4:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="compact effect estimate qc requires between 2 and 4 panels",
                target="metrics.panels",
                observed={"count": len(panels)},
                expected={"minimum": 2, "maximum": 4},
            )
        )

    expected_row_order: tuple[tuple[str, str], ...] | None = None
    label_panel_map: dict[str, str] = {}
    for panel_index, panel_metric in enumerate(panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")

        panel_label = _require_non_empty_text(
            panel_metric.get("panel_label"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].panel_label",
        )
        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_missing",
                    message="compact effect estimate qc requires each metric panel to reference an existing panel box",
                    target=f"metrics.panels[{panel_index}].panel_box_id",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue

        panel_label_box_id = str(panel_metric.get("panel_label_box_id") or "").strip() or f"panel_label_{panel_label}"
        panel_title_box_id = str(panel_metric.get("panel_title_box_id") or "").strip() or f"panel_title_{panel_label}"
        x_axis_title_box_id = str(panel_metric.get("x_axis_title_box_id") or "").strip() or f"x_axis_title_{panel_label}"
        label_panel_map[panel_label_box_id] = panel_box.box_id
        if layout_box_by_id.get(panel_title_box_id) is None or layout_box_by_id.get(x_axis_title_box_id) is None:
            issues.append(
                _issue(
                    rule_id="panel_text_box_missing",
                    message="compact effect estimate panels must reference title and x-axis title boxes",
                    target=f"metrics.panels[{panel_index}]",
                    box_refs=(panel_box.box_id,),
                )
            )

        reference_line_box_id = str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="compact effect estimate panels require one reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="compact effect estimate reference lines must stay within the declared panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    box_refs=(reference_line_box.box_id, panel_box.box_id),
                )
            )

        rows = panel_metric.get("rows")
        if not isinstance(rows, list) or not rows:
            issues.append(
                _issue(
                    rule_id="panel_rows_missing",
                    message="compact effect estimate panels must contain non-empty rows",
                    target=f"metrics.panels[{panel_index}].rows",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        row_order: list[tuple[str, str]] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}] must be an object")
            row_id = _require_non_empty_text(
                row.get("row_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].row_id",
            )
            row_label = _require_non_empty_text(
                row.get("row_label"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].row_label",
            )
            row_order.append((row_id, row_label))

            lower = _require_numeric(
                row.get("lower"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].lower",
            )
            estimate = _require_numeric(
                row.get("estimate"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].estimate",
            )
            upper = _require_numeric(
                row.get("upper"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].upper",
            )
            if not (lower <= estimate <= upper):
                issues.append(
                    _issue(
                        rule_id="estimate_outside_interval",
                        message="panel estimate must lie within the confidence interval",
                        target=f"metrics.panels[{panel_index}].rows[{row_index}]",
                        observed={"lower": lower, "estimate": estimate, "upper": upper},
                    )
                )

            label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
            estimate_box = layout_box_by_id.get(str(row.get("estimate_box_id") or "").strip())
            ci_box = layout_box_by_id.get(str(row.get("ci_box_id") or "").strip())
            if label_box is None or estimate_box is None or ci_box is None:
                issues.append(
                    _issue(
                        rule_id="row_box_missing",
                        message="compact effect estimate rows must reference label, estimate, and ci boxes",
                        target=f"metrics.panels[{panel_index}].rows[{row_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
                continue
            if _boxes_overlap(label_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="row_label_panel_overlap",
                        message="compact effect estimate row labels must stay outside the panel",
                        target=f"layout_boxes.{label_box.box_id}",
                        box_refs=(label_box.box_id, panel_box.box_id),
                    )
                )
            if not _box_within_box(estimate_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="estimate_marker_outside_panel",
                        message="compact effect estimate markers must stay within the panel",
                        target=f"layout_boxes.{estimate_box.box_id}",
                        box_refs=(estimate_box.box_id, panel_box.box_id),
                    )
                )
            if not _box_within_box(ci_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="ci_segment_outside_panel",
                        message="compact effect estimate confidence intervals must stay within the panel",
                        target=f"layout_boxes.{ci_box.box_id}",
                        box_refs=(ci_box.box_id, panel_box.box_id),
                    )
                )

        if expected_row_order is None:
            expected_row_order = tuple(row_order)
        elif tuple(row_order) != expected_row_order:
            issues.append(
                _issue(
                    rule_id="panel_row_order_mismatch",
                    message="compact effect estimate rows must keep the same row order across panels",
                    target=f"metrics.panels[{panel_index}].rows",
                    observed={"row_order": row_order},
                    expected={"row_order": list(expected_row_order)},
                    box_refs=(panel_box.box_id,),
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )
    return issues
