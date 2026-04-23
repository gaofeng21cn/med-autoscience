from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_colorbar_panel_overlap,
    _check_legend_panel_overlap,
    _check_required_box_types,
    _first_box_of_type,
    _issue,
    _matrix_cell_lookup,
    _point_within_box,
    _primary_panel,
    _require_numeric,
    math,
)

def _check_publication_heatmap(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    panel = _first_box_of_type(sidecar.panel_boxes, "heatmap_tile_region") or _primary_panel(sidecar)
    if panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="heatmap qc requires a heatmap tile region",
                target="heatmap_tile_region",
                expected="present",
            )
        )
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("colorbar",)))
    issues.extend(_check_colorbar_panel_overlap(sidecar))

    annotation_bindings = sidecar.metrics.get("annotation_bindings")
    if annotation_bindings is not None:
        if not isinstance(annotation_bindings, list):
            raise ValueError("layout_sidecar.metrics.annotation_bindings must be a list when present")
        tile_boxes = {box.box_id: box for box in sidecar.panel_boxes + sidecar.layout_boxes if box.box_type == "heatmap_tile"}
        annotation_boxes = {box.box_id: box for box in sidecar.layout_boxes if box.box_type == "annotation_text"}
        for index, binding in enumerate(annotation_bindings):
            if not isinstance(binding, dict):
                raise ValueError(f"layout_sidecar.metrics.annotation_bindings[{index}] must be an object")
            tile_box_id = str(binding.get("tile_box_id") or "").strip()
            annotation_box_id = str(binding.get("annotation_box_id") or "").strip()
            tile_box = tile_boxes.get(tile_box_id)
            annotation_box = annotation_boxes.get(annotation_box_id)
            if tile_box is None or annotation_box is None:
                continue
            if (
                tile_box.x0 <= annotation_box.x0 <= tile_box.x1
                and tile_box.x0 <= annotation_box.x1 <= tile_box.x1
                and tile_box.y0 <= annotation_box.y0 <= tile_box.y1
                and tile_box.y0 <= annotation_box.y1 <= tile_box.y1
            ):
                continue
            issues.append(
                _issue(
                    rule_id="annotation_outside_tile",
                    message="annotation text must stay inside its tile box",
                    target="annotation_text",
                    box_refs=(annotation_box.box_id, tile_box.box_id),
                )
            )

    if sidecar.template_id == "performance_heatmap":
        metric_name = str(sidecar.metrics.get("metric_name") or "").strip()
        if not metric_name:
            issues.append(
                _issue(
                    rule_id="metric_name_missing",
                    message="performance heatmap qc requires a non-empty metric_name",
                    target="metrics.metric_name",
                )
            )
            return issues
        cell_lookup = _matrix_cell_lookup(sidecar.metrics)
        for (x_key, y_key), value in sorted(cell_lookup.items()):
            if 0.0 <= value <= 1.0:
                continue
            issues.append(
                _issue(
                    rule_id="performance_value_out_of_range",
                    message="performance heatmap values must stay within [0, 1]",
                    target="metrics.matrix_cells",
                    observed={"x": x_key, "y": y_key, "value": value},
                )
            )
        return issues

    if sidecar.template_id == "confusion_matrix_heatmap_binary":
        metric_name = str(sidecar.metrics.get("metric_name") or "").strip()
        normalization = str(sidecar.metrics.get("normalization") or "").strip()
        if not metric_name:
            issues.append(
                _issue(
                    rule_id="metric_name_missing",
                    message="confusion-matrix heatmap qc requires a non-empty metric_name",
                    target="metrics.metric_name",
                )
            )
        if normalization not in {"row_fraction", "column_fraction", "overall_fraction"}:
            issues.append(
                _issue(
                    rule_id="confusion_normalization_invalid",
                    message="confusion-matrix heatmap normalization must be row_fraction, column_fraction, or overall_fraction",
                    target="metrics.normalization",
                    observed=normalization or None,
                )
            )
        cell_lookup = _matrix_cell_lookup(sidecar.metrics)
        x_labels = sorted({x_key for x_key, _ in cell_lookup})
        y_labels = sorted({y_key for _, y_key in cell_lookup})
        if len(x_labels) != 2 or len(y_labels) != 2 or len(cell_lookup) != 4:
            issues.append(
                _issue(
                    rule_id="confusion_matrix_not_binary_2x2",
                    message="binary confusion-matrix heatmap must contain a complete 2x2 grid",
                    target="metrics.matrix_cells",
                    observed={"x_labels": x_labels, "y_labels": y_labels, "cell_count": len(cell_lookup)},
                )
            )
            return issues
        for (x_key, y_key), value in sorted(cell_lookup.items()):
            if 0.0 <= value <= 1.0:
                continue
            issues.append(
                _issue(
                    rule_id="confusion_value_out_of_range",
                    message="confusion-matrix heatmap values must stay within [0, 1]",
                    target="metrics.matrix_cells",
                    observed={"x": x_key, "y": y_key, "value": value},
                )
            )
        tolerance = 1e-6
        if normalization == "row_fraction":
            for y_key in y_labels:
                total = sum(cell_lookup[(x_key, y_key)] for x_key in x_labels)
                if math.isclose(total, 1.0, rel_tol=0.0, abs_tol=tolerance):
                    continue
                issues.append(
                    _issue(
                        rule_id="confusion_row_sum_invalid",
                        message="each confusion-matrix row must sum to 1.0 when normalization=row_fraction",
                        target="metrics.matrix_cells",
                        observed={"row_label": y_key, "row_sum": total},
                    )
                )
        elif normalization == "column_fraction":
            for x_key in x_labels:
                total = sum(cell_lookup[(x_key, y_key)] for y_key in y_labels)
                if math.isclose(total, 1.0, rel_tol=0.0, abs_tol=tolerance):
                    continue
                issues.append(
                    _issue(
                        rule_id="confusion_column_sum_invalid",
                        message="each confusion-matrix column must sum to 1.0 when normalization=column_fraction",
                        target="metrics.matrix_cells",
                        observed={"column_label": x_key, "column_sum": total},
                    )
                )
        elif normalization == "overall_fraction":
            total = sum(cell_lookup.values())
            if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=tolerance):
                issues.append(
                    _issue(
                        rule_id="confusion_matrix_sum_invalid",
                        message="all confusion-matrix cells must sum to 1.0 when normalization=overall_fraction",
                        target="metrics.matrix_cells",
                        observed={"matrix_sum": total},
                    )
                )
        return issues

    if sidecar.template_id != "correlation_heatmap":
        return issues

    cell_lookup = _matrix_cell_lookup(sidecar.metrics)
    x_labels = {x_key for x_key, _ in cell_lookup}
    y_labels = {y_key for _, y_key in cell_lookup}
    if x_labels != y_labels:
        issues.append(
            _issue(
                rule_id="matrix_not_square",
                message="correlation heatmap must form a square matrix",
                target="metrics.matrix_cells",
                observed={"x_labels": sorted(x_labels), "y_labels": sorted(y_labels)},
            )
        )
    for label in sorted(x_labels | y_labels):
        if (label, label) in cell_lookup:
            continue
        issues.append(
            _issue(
                rule_id="matrix_missing_diagonal",
                message=f"diagonal cell for `{label}` is missing",
                target="metrics.matrix_cells",
                observed=label,
            )
        )
    for left in sorted(x_labels):
        for right in sorted(y_labels):
            forward = cell_lookup.get((left, right))
            reverse = cell_lookup.get((right, left))
            if forward is None or reverse is None:
                continue
            if math.isclose(forward, reverse, rel_tol=1e-9, abs_tol=1e-9):
                continue
            issues.append(
                _issue(
                    rule_id="matrix_not_symmetric",
                    message=f"matrix cells ({left}, {right}) and ({right}, {left}) must match",
                    target="metrics.matrix_cells",
                    observed={"forward": forward, "reverse": reverse},
                )
            )
            return issues
    return issues

def _check_publication_pathway_enrichment_dotplot_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "colorbar", "subplot_y_axis_title")))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))

    effect_scale_label = str(sidecar.metrics.get("effect_scale_label") or "").strip()
    if not effect_scale_label:
        issues.append(
            _issue(
                rule_id="effect_scale_label_missing",
                message="pathway enrichment dotplot requires a non-empty effect_scale_label",
                target="metrics.effect_scale_label",
            )
        )
    size_scale_label = str(sidecar.metrics.get("size_scale_label") or "").strip()
    if not size_scale_label:
        issues.append(
            _issue(
                rule_id="size_scale_label_missing",
                message="pathway enrichment dotplot requires a non-empty size_scale_label",
                target="metrics.size_scale_label",
            )
        )

    pathway_payload = sidecar.metrics.get("pathway_labels")
    if not isinstance(pathway_payload, list) or not pathway_payload:
        issues.append(
            _issue(
                rule_id="pathway_labels_missing",
                message="pathway enrichment dotplot requires non-empty pathway_labels metrics",
                target="metrics.pathway_labels",
            )
        )
        return issues
    pathway_labels = [str(label).strip() for label in pathway_payload]
    if any(not label for label in pathway_labels):
        issues.append(
            _issue(
                rule_id="pathway_label_empty",
                message="pathway_labels must be non-empty",
                target="metrics.pathway_labels",
            )
        )
    if len(set(pathway_labels)) != len(pathway_labels):
        issues.append(
            _issue(
                rule_id="pathway_labels_not_unique",
                message="pathway_labels must be unique",
                target="metrics.pathway_labels",
            )
        )

    panels_payload = sidecar.metrics.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="pathway enrichment dotplot requires non-empty panels metrics",
                target="metrics.panels",
            )
        )
        return issues
    if len(panels_payload) > 2:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="pathway enrichment dotplot supports at most two panels",
                target="metrics.panels",
                observed=len(panels_payload),
            )
        )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    declared_pathways = set(pathway_labels)
    seen_panel_ids: set[str] = set()

    for index, payload in enumerate(panels_payload):
        if not isinstance(payload, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{index}] must be an object")
        panel_id = str(payload.get("panel_id") or "").strip()
        if not panel_id:
            raise ValueError(f"layout_sidecar.metrics.panels[{index}].panel_id must be non-empty")
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="panel_id_not_unique",
                    message="panel_id must be unique across panels",
                    target=f"metrics.panels[{index}].panel_id",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)

        panel_box_id = str(payload.get("panel_box_id") or "").strip()
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="panel_box_id must resolve to an existing panel box",
                    target=f"metrics.panels[{index}].panel_box_id",
                    observed=panel_box_id,
                )
            )
        panel_label_box_id = str(payload.get("panel_label_box_id") or "").strip()
        panel_label_box = layout_boxes_by_id.get(panel_label_box_id)
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_box_missing",
                    message="panel_label_box_id must resolve to an existing layout box",
                    target=f"metrics.panels[{index}].panel_label_box_id",
                    observed=panel_label_box_id,
                )
            )
        elif panel_box is not None and not _boxes_overlap(panel_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_anchor_drift",
                    message="panel label must stay anchored inside its panel",
                    target=f"metrics.panels[{index}].panel_label_box_id",
                    box_refs=(panel_label_box.box_id, panel_box.box_id),
                )
            )
        for field_name in ("panel_title_box_id", "x_axis_title_box_id"):
            box_id = str(payload.get(field_name) or "").strip()
            if box_id and box_id in layout_boxes_by_id:
                continue
            issues.append(
                _issue(
                    rule_id="layout_box_missing",
                    message=f"{field_name} must resolve to an existing layout box",
                    target=f"metrics.panels[{index}].{field_name}",
                    observed=box_id,
                )
            )

        points_payload = payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            issues.append(
                _issue(
                    rule_id="panel_points_missing",
                    message="every panel must expose non-empty points metrics",
                    target=f"metrics.panels[{index}].points",
                )
            )
            continue

        observed_pathways: set[str] = set()
        for point_index, point in enumerate(points_payload):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{index}].points[{point_index}] must be an object")
            pathway_label = str(point.get("pathway_label") or "").strip()
            if not pathway_label:
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{index}].points[{point_index}].pathway_label must be non-empty"
                )
            if pathway_label not in declared_pathways:
                issues.append(
                    _issue(
                        rule_id="point_pathway_unknown",
                        message="point pathway_label must stay inside declared pathway_labels",
                        target=f"metrics.panels[{index}].points[{point_index}].pathway_label",
                        observed=pathway_label,
                    )
                )
            observed_pathways.add(pathway_label)
            x_value = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].x",
            )
            y_value = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].y",
            )
            _require_numeric(
                point.get("effect_value"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].effect_value",
            )
            size_value = _require_numeric(
                point.get("size_value"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].size_value",
            )
            if size_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="point_size_negative",
                        message="point size_value must be non-negative",
                        target=f"metrics.panels[{index}].points[{point_index}].size_value",
                        observed=size_value,
                    )
                )
            if panel_box is not None and not _point_within_box(panel_box, x=x_value, y=y_value):
                issues.append(
                    _issue(
                        rule_id="dot_out_of_panel",
                        message="dot center must stay within its panel domain",
                        target=f"metrics.panels[{index}].points[{point_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
        if observed_pathways != declared_pathways:
            issues.append(
                _issue(
                    rule_id="panel_pathway_coverage_mismatch",
                    message="each panel must cover every declared pathway exactly once",
                    target=f"metrics.panels[{index}].points",
                    observed=sorted(observed_pathways),
                    expected=sorted(declared_pathways),
                )
            )

    return issues

def _check_publication_celltype_marker_dotplot_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "colorbar", "subplot_y_axis_title")))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))

    effect_scale_label = str(sidecar.metrics.get("effect_scale_label") or "").strip()
    if not effect_scale_label:
        issues.append(
            _issue(
                rule_id="effect_scale_label_missing",
                message="cell-type marker dotplot requires a non-empty effect_scale_label",
                target="metrics.effect_scale_label",
            )
        )
    size_scale_label = str(sidecar.metrics.get("size_scale_label") or "").strip()
    if not size_scale_label:
        issues.append(
            _issue(
                rule_id="size_scale_label_missing",
                message="cell-type marker dotplot requires a non-empty size_scale_label",
                target="metrics.size_scale_label",
            )
        )

    celltype_payload = sidecar.metrics.get("celltype_labels")
    if not isinstance(celltype_payload, list) or not celltype_payload:
        issues.append(
            _issue(
                rule_id="celltype_labels_missing",
                message="cell-type marker dotplot requires non-empty celltype_labels metrics",
                target="metrics.celltype_labels",
            )
        )
        return issues
    celltype_labels = [str(label).strip() for label in celltype_payload]
    if any(not label for label in celltype_labels):
        issues.append(
            _issue(
                rule_id="celltype_label_empty",
                message="celltype_labels must be non-empty",
                target="metrics.celltype_labels",
            )
        )
    if len(set(celltype_labels)) != len(celltype_labels):
        issues.append(
            _issue(
                rule_id="celltype_labels_not_unique",
                message="celltype_labels must be unique",
                target="metrics.celltype_labels",
            )
        )

    marker_payload = sidecar.metrics.get("marker_labels")
    if not isinstance(marker_payload, list) or not marker_payload:
        issues.append(
            _issue(
                rule_id="marker_labels_missing",
                message="cell-type marker dotplot requires non-empty marker_labels metrics",
                target="metrics.marker_labels",
            )
        )
        return issues
    marker_labels = [str(label).strip() for label in marker_payload]
    if any(not label for label in marker_labels):
        issues.append(
            _issue(
                rule_id="marker_label_empty",
                message="marker_labels must be non-empty",
                target="metrics.marker_labels",
            )
        )
    if len(set(marker_labels)) != len(marker_labels):
        issues.append(
            _issue(
                rule_id="marker_labels_not_unique",
                message="marker_labels must be unique",
                target="metrics.marker_labels",
            )
        )

    panels_payload = sidecar.metrics.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="cell-type marker dotplot requires non-empty panels metrics",
                target="metrics.panels",
            )
        )
        return issues
    if len(panels_payload) > 2:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="cell-type marker dotplot supports at most two panels",
                target="metrics.panels",
                observed=len(panels_payload),
            )
        )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    declared_celltypes = set(celltype_labels)
    declared_markers = set(marker_labels)
    expected_panel_coordinates = {(celltype_label, marker_label) for celltype_label in celltype_labels for marker_label in marker_labels}
    seen_panel_ids: set[str] = set()

    for index, payload in enumerate(panels_payload):
        if not isinstance(payload, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{index}] must be an object")
        panel_id = str(payload.get("panel_id") or "").strip()
        if not panel_id:
            raise ValueError(f"layout_sidecar.metrics.panels[{index}].panel_id must be non-empty")
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="panel_id_not_unique",
                    message="panel_id must be unique across panels",
                    target=f"metrics.panels[{index}].panel_id",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)

        panel_box_id = str(payload.get("panel_box_id") or "").strip()
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="panel_box_id must resolve to an existing panel box",
                    target=f"metrics.panels[{index}].panel_box_id",
                    observed=panel_box_id,
                )
            )
        panel_label_box_id = str(payload.get("panel_label_box_id") or "").strip()
        panel_label_box = layout_boxes_by_id.get(panel_label_box_id)
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_box_missing",
                    message="panel_label_box_id must resolve to an existing layout box",
                    target=f"metrics.panels[{index}].panel_label_box_id",
                    observed=panel_label_box_id,
                )
            )
        elif panel_box is not None and not _boxes_overlap(panel_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_anchor_drift",
                    message="panel label must stay anchored inside its panel",
                    target=f"metrics.panels[{index}].panel_label_box_id",
                    box_refs=(panel_label_box.box_id, panel_box.box_id),
                )
            )
        for field_name in ("panel_title_box_id", "x_axis_title_box_id"):
            box_id = str(payload.get(field_name) or "").strip()
            if box_id and box_id in layout_boxes_by_id:
                continue
            issues.append(
                _issue(
                    rule_id="layout_box_missing",
                    message=f"{field_name} must resolve to an existing layout box",
                    target=f"metrics.panels[{index}].{field_name}",
                    observed=box_id,
                )
            )

        points_payload = payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            issues.append(
                _issue(
                    rule_id="panel_points_missing",
                    message="every panel must expose non-empty points metrics",
                    target=f"metrics.panels[{index}].points",
                )
            )
            continue

        observed_coordinates: set[tuple[str, str]] = set()
        for point_index, point in enumerate(points_payload):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{index}].points[{point_index}] must be an object")
            celltype_label = str(point.get("celltype_label") or "").strip()
            if not celltype_label:
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{index}].points[{point_index}].celltype_label must be non-empty"
                )
            if celltype_label not in declared_celltypes:
                issues.append(
                    _issue(
                        rule_id="point_celltype_unknown",
                        message="point celltype_label must stay inside declared celltype_labels",
                        target=f"metrics.panels[{index}].points[{point_index}].celltype_label",
                        observed=celltype_label,
                    )
                )
            marker_label = str(point.get("marker_label") or "").strip()
            if not marker_label:
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{index}].points[{point_index}].marker_label must be non-empty"
                )
            if marker_label not in declared_markers:
                issues.append(
                    _issue(
                        rule_id="point_marker_unknown",
                        message="point marker_label must stay inside declared marker_labels",
                        target=f"metrics.panels[{index}].points[{point_index}].marker_label",
                        observed=marker_label,
                    )
                )
            observed_coordinates.add((celltype_label, marker_label))
            x_value = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].x",
            )
            y_value = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].y",
            )
            _require_numeric(
                point.get("effect_value"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].effect_value",
            )
            size_value = _require_numeric(
                point.get("size_value"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].size_value",
            )
            if size_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="point_size_negative",
                        message="point size_value must be non-negative",
                        target=f"metrics.panels[{index}].points[{point_index}].size_value",
                        observed=size_value,
                    )
                )
            if panel_box is not None and not _point_within_box(panel_box, x=x_value, y=y_value):
                issues.append(
                    _issue(
                        rule_id="dot_out_of_panel",
                        message="dot center must stay within its panel domain",
                        target=f"metrics.panels[{index}].points[{point_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
        if observed_coordinates != expected_panel_coordinates:
            issues.append(
                _issue(
                    rule_id="panel_celltype_marker_coverage_mismatch",
                    message="each panel must cover every declared celltype-marker coordinate exactly once",
                    target=f"metrics.panels[{index}].points",
                    observed=sorted(observed_coordinates),
                    expected=sorted(expected_panel_coordinates),
                )
            )

    return issues
