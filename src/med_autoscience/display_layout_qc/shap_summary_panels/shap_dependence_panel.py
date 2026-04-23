from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _check_boxes_within_device, _check_colorbar_panel_overlap, _check_composite_panel_label_anchors, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _point_within_box, _require_numeric

def _check_publication_shap_dependence_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label", "zero_line", "colorbar"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_colorbar_panel_overlap(sidecar))

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="shap dependence qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap dependence panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    zero_lines = _boxes_of_type(sidecar.guide_boxes, "zero_line")
    if len(zero_lines) < len(metrics_panels):
        issues.append(
            _issue(
                rule_id="zero_line_count_mismatch",
                message="shap dependence requires at least one zero line per panel",
                target="guide_boxes.zero_line",
                observed={"count": len(zero_lines)},
                expected={"minimum_count": len(metrics_panels)},
            )
        )

    colorbar_label = str(sidecar.metrics.get("colorbar_label") or "").strip()
    if not colorbar_label:
        issues.append(
            _issue(
                rule_id="colorbar_label_missing",
                message="shap dependence qc requires a non-empty colorbar label metric",
                target="metrics.colorbar_label",
            )
        )

    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    panel_box_by_suffix = {
        box.box_id.removeprefix("panel_"): box
        for box in panel_boxes
        if box.box_id.startswith("panel_")
    }
    label_panel_map: dict[str, str] = {}
    for panel_index, item in enumerate(metrics_panels):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(item.get("panel_id") or "").strip()
        panel_label = str(item.get("panel_label") or "").strip()
        title = str(item.get("title") or "").strip()
        x_label = str(item.get("x_label") or "").strip()
        feature = str(item.get("feature") or "").strip()
        interaction_feature = str(item.get("interaction_feature") or "").strip()
        if not panel_id or not panel_label or not title or not x_label or not feature or not interaction_feature:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="shap dependence panel metrics must declare panel metadata and labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        expected_panel_box_id = f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(expected_panel_box_id)
        if panel_box is None:
            panel_box = panel_box_by_suffix.get(panel_label)
        if panel_box is None and panel_index < len(panel_boxes):
            panel_box = panel_boxes[panel_index]
        if panel_box is not None:
            label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        points = item.get("points")
        if not isinstance(points, list) or not points:
            issues.append(
                _issue(
                    rule_id="panel_points_missing",
                    message="shap dependence panel metrics must carry non-empty normalized points",
                    target=f"metrics.panels[{panel_index}].points",
                )
            )
            continue
        if panel_box is None:
            continue
        for point_index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}] must be an object")
            x_value = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].x",
            )
            y_value = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].y",
            )
            if _point_within_box(panel_box, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="point_outside_panel",
                    message="shap dependence point must stay within its declared panel",
                    target=f"metrics.panels[{panel_index}].points[{point_index}]",
                    observed={"x": x_value, "y": y_value},
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

    for zero_line in zero_lines:
        if any(_box_within_box(zero_line, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="zero_line_outside_panel",
                message="shap dependence zero line must stay within a panel region",
                target="guide_boxes.zero_line",
                box_refs=(zero_line.box_id,),
            )
        )
    return issues
