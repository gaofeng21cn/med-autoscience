from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _check_boxes_within_device, _check_composite_panel_label_anchors, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _point_within_box, _require_numeric

def _check_publication_partial_dependence_subgroup_comparison_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subgroup_panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "subgroup_x_axis_title",
        "panel_label",
        "pdp_reference_label",
        "subgroup_row_label",
        "legend_box",
        "pdp_reference_line",
        "subgroup_ci_segment",
        "subgroup_estimate_marker",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {
            "title",
            "panel_title",
            "subgroup_panel_title",
            "subplot_x_axis_title",
            "subplot_y_axis_title",
            "subgroup_x_axis_title",
            "panel_label",
            "pdp_reference_label",
            "subgroup_row_label",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    legend_labels = sidecar.metrics.get("legend_labels")
    expected_legend_labels = ["ICE curves", "PDP mean", "Subgroup interval"]
    if legend_labels != expected_legend_labels:
        issues.append(
            _issue(
                rule_id="legend_labels_invalid",
                message="subgroup comparison legend must declare exactly ICE curves, PDP mean, and Subgroup interval",
                target="metrics.legend_labels",
                observed=legend_labels,
                expected=expected_legend_labels,
            )
        )

    top_panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    subgroup_panels = _boxes_of_type(sidecar.panel_boxes, "subgroup_panel")
    if len(subgroup_panels) != 1:
        issues.append(
            _issue(
                rule_id="subgroup_panel_missing",
                message="subgroup comparison qc requires exactly one subgroup_panel box",
                target="panel_boxes",
                observed={"subgroup_panel_count": len(subgroup_panels)},
                expected={"subgroup_panel_count": 1},
            )
        )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="subgroup comparison qc requires non-empty top-panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    subgroup_panel_metric = sidecar.metrics.get("subgroup_panel")
    if not isinstance(subgroup_panel_metric, dict):
        issues.append(
            _issue(
                rule_id="subgroup_panel_metrics_missing",
                message="subgroup comparison qc requires subgroup_panel metrics",
                target="metrics.subgroup_panel",
            )
        )
        return issues

    if len(top_panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="subgroup comparison top-panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(top_panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    label_panel_map: dict[str, str] = {}
    seen_panel_ids: set[str] = set()

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        subgroup_label = str(panel_metric.get("subgroup_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        x_label = str(panel_metric.get("x_label") or "").strip()
        feature = str(panel_metric.get("feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        _require_numeric(
            panel_metric.get("reference_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_value",
        )
        if not panel_id or not panel_label or not subgroup_label or not title or not x_label or not feature or not reference_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="subgroup comparison top-panel metrics must declare panel metadata and reference labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_panel_id",
                    message="subgroup comparison panel_id values must stay unique",
                    target="metrics.panels",
                    observed=panel_id,
                )
            )
            continue
        seen_panel_ids.add(panel_id)

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="subgroup comparison metrics must reference an existing top panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        pdp_points = panel_metric.get("pdp_points")
        if not isinstance(pdp_points, list) or not pdp_points:
            issues.append(
                _issue(
                    rule_id="pdp_points_missing",
                    message="subgroup comparison panels require non-empty pdp_points",
                    target=f"metrics.panels[{panel_index}].pdp_points",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for point_index, point in enumerate(pdp_points):
                if not isinstance(point, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].pdp_points[{point_index}] must be an object")
                x_value = _require_numeric(
                    point.get("x"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].pdp_points[{point_index}].x",
                )
                y_value = _require_numeric(
                    point.get("y"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].pdp_points[{point_index}].y",
                )
                if _point_within_box(panel_box, x=x_value, y=y_value):
                    continue
                issues.append(
                    _issue(
                        rule_id="pdp_point_outside_panel",
                        message="subgroup comparison PDP points must stay within the declared panel region",
                        target=f"metrics.panels[{panel_index}].pdp_points[{point_index}]",
                        observed={"x": x_value, "y": y_value},
                        box_refs=(panel_box.box_id,),
                    )
                )

        ice_curves = panel_metric.get("ice_curves")
        if not isinstance(ice_curves, list) or not ice_curves:
            issues.append(
                _issue(
                    rule_id="ice_curves_missing",
                    message="subgroup comparison panels require non-empty ice_curves",
                    target=f"metrics.panels[{panel_index}].ice_curves",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for curve_index, curve in enumerate(ice_curves):
                if not isinstance(curve, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}] must be an object")
                points = curve.get("points")
                if not isinstance(points, list) or not points:
                    issues.append(
                        _issue(
                            rule_id="ice_curve_points_missing",
                            message="subgroup comparison ICE curves must carry non-empty normalized points",
                            target=f"metrics.panels[{panel_index}].ice_curves[{curve_index}]",
                            box_refs=(panel_box.box_id,),
                        )
                    )
                    continue
                for point_index, point in enumerate(points):
                    if not isinstance(point, dict):
                        raise ValueError(
                            f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}] must be an object"
                        )
                    x_value = _require_numeric(
                        point.get("x"),
                        label=(
                            f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}].x"
                        ),
                    )
                    y_value = _require_numeric(
                        point.get("y"),
                        label=(
                            f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}].y"
                        ),
                    )
                    if _point_within_box(panel_box, x=x_value, y=y_value):
                        continue
                    issues.append(
                        _issue(
                            rule_id="ice_point_outside_panel",
                            message="subgroup comparison ICE points must stay within the declared panel region",
                            target=(
                                f"metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}]"
                            ),
                            observed={"x": x_value, "y": y_value},
                            box_refs=(panel_box.box_id,),
                        )
                    )

        reference_line_box_id = (
            str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        )
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="subgroup comparison requires one PDP reference line per top panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="subgroup comparison reference line must stay within the top panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    box_refs=(reference_line_box.box_id, panel_box.box_id),
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
                    message="subgroup comparison requires one reference label per top panel",
                    target=f"metrics.panels[{panel_index}].reference_label_box_id",
                    observed={"reference_label_box_id": reference_label_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_label_outside_panel",
                    message="subgroup comparison reference label must stay within the top panel region",
                    target=f"layout_boxes.{reference_label_box.box_id}",
                    box_refs=(reference_label_box.box_id, panel_box.box_id),
                )
            )

    subgroup_panel_label = str(subgroup_panel_metric.get("panel_label") or "").strip()
    subgroup_panel_title = str(subgroup_panel_metric.get("title") or "").strip()
    subgroup_x_label = str(subgroup_panel_metric.get("x_label") or "").strip()
    subgroup_panel_box_id = str(subgroup_panel_metric.get("panel_box_id") or "").strip() or "panel_C"
    subgroup_panel_box = panel_box_by_id.get(subgroup_panel_box_id)
    if not subgroup_panel_label or not subgroup_panel_title or not subgroup_x_label:
        issues.append(
            _issue(
                rule_id="subgroup_panel_metric_missing",
                message="subgroup comparison subgroup_panel metrics must declare panel metadata",
                target="metrics.subgroup_panel",
            )
        )
    if subgroup_panel_box is None:
        issues.append(
            _issue(
                rule_id="subgroup_panel_box_missing",
                message="subgroup comparison subgroup_panel must reference an existing subgroup_panel box",
                target="metrics.subgroup_panel.panel_box_id",
                observed={"panel_box_id": subgroup_panel_box_id},
            )
        )

    subgroup_rows = subgroup_panel_metric.get("rows")
    if not isinstance(subgroup_rows, list) or not subgroup_rows:
        issues.append(
            _issue(
                rule_id="subgroup_rows_missing",
                message="subgroup comparison subgroup_panel must contain non-empty rows",
                target="metrics.subgroup_panel.rows",
            )
        )
    elif subgroup_panel_box is not None:
        seen_row_panel_ids: set[str] = set()
        for row_index, row in enumerate(subgroup_rows):
            if not isinstance(row, dict):
                raise ValueError(f"layout_sidecar.metrics.subgroup_panel.rows[{row_index}] must be an object")
            row_panel_id = str(row.get("panel_id") or "").strip()
            if row_panel_id:
                seen_row_panel_ids.add(row_panel_id)
            label_box_id = str(row.get("label_box_id") or "").strip() or f"subgroup_row_label_{row_index + 1}"
            ci_segment_box_id = str(row.get("ci_segment_box_id") or "").strip() or f"subgroup_ci_segment_{row_index + 1}"
            estimate_marker_box_id = (
                str(row.get("estimate_marker_box_id") or "").strip() or f"subgroup_estimate_marker_{row_index + 1}"
            )

            if layout_box_by_id.get(label_box_id) is None:
                issues.append(
                    _issue(
                        rule_id="subgroup_row_label_missing",
                        message="subgroup comparison rows require explicit row labels",
                        target=f"metrics.subgroup_panel.rows[{row_index}].label_box_id",
                        observed={"label_box_id": label_box_id},
                    )
                )
            ci_segment_box = guide_box_by_id.get(ci_segment_box_id)
            if ci_segment_box is None:
                issues.append(
                    _issue(
                        rule_id="subgroup_ci_segment_missing",
                        message="subgroup comparison rows require a CI segment guide box",
                        target=f"metrics.subgroup_panel.rows[{row_index}].ci_segment_box_id",
                        observed={"ci_segment_box_id": ci_segment_box_id},
                        box_refs=(subgroup_panel_box.box_id,),
                    )
                )
            elif not _box_within_box(ci_segment_box, subgroup_panel_box):
                issues.append(
                    _issue(
                        rule_id="subgroup_ci_segment_outside_panel",
                        message="subgroup comparison CI segments must stay within the subgroup panel region",
                        target=f"guide_boxes.{ci_segment_box.box_id}",
                        box_refs=(ci_segment_box.box_id, subgroup_panel_box.box_id),
                    )
                )
            estimate_marker_box = guide_box_by_id.get(estimate_marker_box_id)
            if estimate_marker_box is None:
                issues.append(
                    _issue(
                        rule_id="subgroup_estimate_marker_missing",
                        message="subgroup comparison rows require an estimate marker guide box",
                        target=f"metrics.subgroup_panel.rows[{row_index}].estimate_marker_box_id",
                        observed={"estimate_marker_box_id": estimate_marker_box_id},
                        box_refs=(subgroup_panel_box.box_id,),
                    )
                )
            elif not _box_within_box(estimate_marker_box, subgroup_panel_box):
                issues.append(
                    _issue(
                        rule_id="subgroup_estimate_marker_outside_panel",
                        message="subgroup comparison estimate markers must stay within the subgroup panel region",
                        target=f"guide_boxes.{estimate_marker_box.box_id}",
                        box_refs=(estimate_marker_box.box_id, subgroup_panel_box.box_id),
                    )
                )

        if seen_panel_ids and seen_row_panel_ids and seen_row_panel_ids != seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="subgroup_row_panel_mismatch",
                    message="subgroup comparison subgroup rows must reference each declared top panel exactly once",
                    target="metrics.subgroup_panel.rows",
                    observed=sorted(seen_row_panel_ids),
                    expected=sorted(seen_panel_ids),
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.10,
            max_left_offset_ratio=0.12,
        )
    )
    return issues
