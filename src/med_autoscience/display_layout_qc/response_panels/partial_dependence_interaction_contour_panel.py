from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _check_boxes_within_device, _check_colorbar_panel_overlap, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _point_within_box, _require_numeric, math

def _check_publication_partial_dependence_interaction_contour_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "panel_label",
        "interaction_reference_label",
        "colorbar",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_colorbar_panel_overlap(sidecar))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label", "interaction_reference_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    colorbar_label = str(sidecar.metrics.get("colorbar_label") or "").strip()
    if not colorbar_label:
        issues.append(
            _issue(
                rule_id="colorbar_label_missing",
                message="partial dependence interaction contour qc requires a non-empty colorbar label metric",
                target="metrics.colorbar_label",
            )
        )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="partial dependence interaction contour qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="partial dependence interaction contour panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        x_label = str(panel_metric.get("x_label") or "").strip()
        y_label = str(panel_metric.get("y_label") or "").strip()
        x_feature = str(panel_metric.get("x_feature") or "").strip()
        y_feature = str(panel_metric.get("y_feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        reference_x_value = _require_numeric(
            panel_metric.get("reference_x_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_x_value",
        )
        reference_y_value = _require_numeric(
            panel_metric.get("reference_y_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_y_value",
        )
        if (
            not panel_id
            or not panel_label
            or not title
            or not x_label
            or not y_label
            or not x_feature
            or not y_feature
            or not reference_label
        ):
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="partial dependence interaction contour panel metrics must declare panel metadata and reference labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="partial dependence interaction contour metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        x_grid = panel_metric.get("x_grid")
        y_grid = panel_metric.get("y_grid")
        response_grid = panel_metric.get("response_grid")
        if not isinstance(x_grid, list) or len(x_grid) < 2 or not isinstance(y_grid, list) or len(y_grid) < 2:
            issues.append(
                _issue(
                    rule_id="grid_missing",
                    message="partial dependence interaction contour metrics require non-empty x_grid and y_grid",
                    target=f"metrics.panels[{panel_index}]",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue
        x_values = [_require_numeric(value, label=f"layout_sidecar.metrics.panels[{panel_index}].x_grid[{idx}]") for idx, value in enumerate(x_grid)]
        y_values = [_require_numeric(value, label=f"layout_sidecar.metrics.panels[{panel_index}].y_grid[{idx}]") for idx, value in enumerate(y_grid)]
        if any(right <= left for left, right in zip(x_values, x_values[1:], strict=False)):
            issues.append(
                _issue(
                    rule_id="x_grid_not_increasing",
                    message="partial dependence interaction contour x_grid must be strictly increasing",
                    target=f"metrics.panels[{panel_index}].x_grid",
                    observed={"x_grid": x_values},
                    box_refs=(panel_box.box_id,),
                )
            )
        if any(right <= left for left, right in zip(y_values, y_values[1:], strict=False)):
            issues.append(
                _issue(
                    rule_id="y_grid_not_increasing",
                    message="partial dependence interaction contour y_grid must be strictly increasing",
                    target=f"metrics.panels[{panel_index}].y_grid",
                    observed={"y_grid": y_values},
                    box_refs=(panel_box.box_id,),
                )
            )
        if not isinstance(response_grid, list) or len(response_grid) != len(y_values):
            issues.append(
                _issue(
                    rule_id="response_grid_shape_mismatch",
                    message="response_grid row count must match y_grid length",
                    target=f"metrics.panels[{panel_index}].response_grid",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for row_index, row in enumerate(response_grid):
                if not isinstance(row, list) or len(row) != len(x_values):
                    issues.append(
                        _issue(
                            rule_id="response_grid_shape_mismatch",
                            message="each response_grid row must match x_grid length",
                            target=f"metrics.panels[{panel_index}].response_grid[{row_index}]",
                            box_refs=(panel_box.box_id,),
                        )
                    )
                    continue
                for column_index, value in enumerate(row):
                    numeric_value = _require_numeric(
                        value,
                        label=f"layout_sidecar.metrics.panels[{panel_index}].response_grid[{row_index}][{column_index}]",
                    )
                    if not math.isfinite(numeric_value):
                        issues.append(
                            _issue(
                                rule_id="response_value_not_finite",
                                message="partial dependence interaction contour response values must be finite",
                                target=f"metrics.panels[{panel_index}].response_grid[{row_index}][{column_index}]",
                                box_refs=(panel_box.box_id,),
                            )
                        )

        if not (x_values[0] <= reference_x_value <= x_values[-1]) or not (y_values[0] <= reference_y_value <= y_values[-1]):
            issues.append(
                _issue(
                    rule_id="reference_point_outside_grid",
                    message="partial dependence interaction contour reference point must fall within declared grid range",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"reference_x_value": reference_x_value, "reference_y_value": reference_y_value},
                    box_refs=(panel_box.box_id,),
                )
            )

        observed_points = panel_metric.get("observed_points")
        if not isinstance(observed_points, list) or not observed_points:
            issues.append(
                _issue(
                    rule_id="observed_points_missing",
                    message="partial dependence interaction contour metrics must contain non-empty observed_points",
                    target=f"metrics.panels[{panel_index}].observed_points",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for point_index, point in enumerate(observed_points):
                if not isinstance(point, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].observed_points[{point_index}] must be an object")
                point_x = _require_numeric(
                    point.get("x"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].observed_points[{point_index}].x",
                )
                point_y = _require_numeric(
                    point.get("y"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].observed_points[{point_index}].y",
                )
                if not _point_within_box(panel_box, x=point_x, y=point_y):
                    issues.append(
                        _issue(
                            rule_id="observed_point_outside_panel",
                            message="observed support points must stay within the declared panel region",
                            target=f"metrics.panels[{panel_index}].observed_points[{point_index}]",
                            observed={"x": point_x, "y": point_y},
                            box_refs=(panel_box.box_id,),
                        )
                    )

        reference_vertical_box_id = (
            str(panel_metric.get("reference_vertical_box_id") or "").strip() or f"reference_vertical_{panel_label}"
        )
        reference_vertical_box = guide_box_by_id.get(reference_vertical_box_id)
        if reference_vertical_box is None:
            issues.append(
                _issue(
                    rule_id="reference_vertical_missing",
                    message="partial dependence interaction contour requires one vertical reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_vertical_box_id",
                    observed={"reference_vertical_box_id": reference_vertical_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_vertical_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_vertical_outside_panel",
                    message="vertical reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_vertical_box.box_id}",
                    box_refs=(reference_vertical_box.box_id, panel_box.box_id),
                )
            )

        reference_horizontal_box_id = (
            str(panel_metric.get("reference_horizontal_box_id") or "").strip() or f"reference_horizontal_{panel_label}"
        )
        reference_horizontal_box = guide_box_by_id.get(reference_horizontal_box_id)
        if reference_horizontal_box is None:
            issues.append(
                _issue(
                    rule_id="reference_horizontal_missing",
                    message="partial dependence interaction contour requires one horizontal reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_horizontal_box_id",
                    observed={"reference_horizontal_box_id": reference_horizontal_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_horizontal_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_horizontal_outside_panel",
                    message="horizontal reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_horizontal_box.box_id}",
                    box_refs=(reference_horizontal_box.box_id, panel_box.box_id),
                )
            )

        reference_label_box_id = (
            str(panel_metric.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_label}"
        )
        reference_label_box = layout_box_by_id.get(reference_label_box_id)
        if reference_label_box is None:
            issues.append(
                _issue(
                    rule_id="reference_label_missing",
                    message="partial dependence interaction contour requires one reference label per panel",
                    target=f"metrics.panels[{panel_index}].reference_label_box_id",
                    observed={"reference_label_box_id": reference_label_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_label_outside_panel",
                    message="reference label must stay within the panel region",
                    target=f"layout_boxes.{reference_label_box.box_id}",
                    box_refs=(reference_label_box.box_id, panel_box.box_id),
                )
            )

    return issues
