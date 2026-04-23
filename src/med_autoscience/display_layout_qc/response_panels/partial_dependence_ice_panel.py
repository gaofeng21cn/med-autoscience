from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _check_boxes_within_device, _check_composite_panel_label_anchors, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _point_within_box, _require_numeric

def _check_publication_partial_dependence_ice_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "panel_label",
        "pdp_reference_label",
        "legend_box",
        "pdp_reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label", "pdp_reference_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    legend_labels = sidecar.metrics.get("legend_labels")
    if legend_labels != ["ICE curves", "PDP mean"]:
        issues.append(
            _issue(
                rule_id="legend_labels_invalid",
                message="partial dependence + ICE legend must declare exactly ICE curves and PDP mean",
                target="metrics.legend_labels",
                observed=legend_labels,
                expected=["ICE curves", "PDP mean"],
            )
        )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="partial dependence + ICE qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="partial dependence + ICE panel count must match metrics.panels",
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
        feature = str(panel_metric.get("feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        reference_value = _require_numeric(
            panel_metric.get("reference_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_value",
        )
        if not panel_id or not panel_label or not title or not x_label or not feature or not reference_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="partial dependence + ICE panel metrics must declare panel metadata and reference labels",
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
                    message="partial dependence + ICE metrics must reference an existing panel box",
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
                    message="partial dependence + ICE panel metrics must contain non-empty PDP points",
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
                        message="PDP curve points must stay within the declared panel region",
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
                    message="partial dependence + ICE panel metrics must contain non-empty ICE curves",
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
                            message="each ICE curve must carry non-empty normalized points",
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
                            message="ICE curve points must stay within the declared panel region",
                            target=(
                                f"metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}]"
                            ),
                            observed={"x": x_value, "y": y_value},
                            box_refs=(panel_box.box_id,),
                        )
                    )

        reference_line_box_id = str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="partial dependence + ICE requires one reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    observed={"reference_value": reference_value},
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
                    message="partial dependence + ICE requires one reference label per panel",
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

        if reference_line_box is not None and reference_label_box is not None:
            reference_line_mid_x = (reference_line_box.x0 + reference_line_box.x1) / 2.0
            reference_label_mid_x = (reference_label_box.x0 + reference_label_box.x1) / 2.0
            alignment_tolerance = max((panel_box.x1 - panel_box.x0) * 0.18, 0.05)
            if abs(reference_line_mid_x - reference_label_mid_x) > alignment_tolerance:
                issues.append(
                    _issue(
                        rule_id="reference_label_misaligned",
                        message="reference label must stay horizontally aligned to its reference line",
                        target=f"layout_boxes.{reference_label_box.box_id}",
                        observed={"label_mid_x": reference_label_mid_x, "line_mid_x": reference_line_mid_x},
                        box_refs=(reference_label_box.box_id, reference_line_box.box_id),
                    )
                )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.30,
            max_left_offset_ratio=0.40,
        )
    )
    return issues
