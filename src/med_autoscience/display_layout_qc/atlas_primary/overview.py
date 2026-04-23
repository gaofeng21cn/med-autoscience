from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _check_boxes_within_device, _check_colorbar_panel_overlap, _check_composite_panel_label_anchors, _check_legend_panel_overlap, _check_pairwise_non_overlap, _check_required_box_types, _first_box_of_type, _issue, _matrix_cell_lookup, _point_within_box, _primary_panel, _require_numeric, math

def _check_publication_embedding_scatter(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("title", "x_axis_title", "y_axis_title", "legend")))
    panel = _primary_panel(sidecar)
    if panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="embedding scatter requires a panel box",
                target="panel",
                expected="present",
            )
        )
        return issues
    issues.extend(_check_legend_panel_overlap(sidecar))

    points = sidecar.metrics.get("points")
    if not isinstance(points, list) or not points:
        issues.append(
            _issue(
                rule_id="points_missing",
                message="embedding scatter requires non-empty point metrics",
                target="metrics.points",
            )
        )
        return issues
    group_labels = sidecar.metrics.get("group_labels")
    if group_labels is not None:
        if not isinstance(group_labels, list):
            raise ValueError("layout_sidecar.metrics.group_labels must be a list when present")
        seen_group_labels: set[str] = set()
        for index, item in enumerate(group_labels):
            group_label = str(item).strip()
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="empty_group_label",
                        message="group labels must be non-empty",
                        target=f"metrics.group_labels[{index}]",
                    )
                )
                continue
            if group_label in seen_group_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_group_label",
                        message=f"group label `{group_label}` must be unique",
                        target="metrics.group_labels",
                        observed=group_label,
                    )
                )
                continue
            seen_group_labels.add(group_label)
    for index, point in enumerate(points):
        if not isinstance(point, dict):
            raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
        group = str(point.get("group") or "").strip()
        if not group:
            issues.append(
                _issue(
                    rule_id="empty_group_label",
                    message="group labels must be non-empty",
                    target=f"metrics.points[{index}].group",
                )
            )
        x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.points[{index}].x")
        y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
        if _point_within_box(panel, x=x_value, y=y_value):
            continue
        issues.append(
            _issue(
                rule_id="point_out_of_panel",
                message="embedding point must stay within the panel domain",
                target=f"metrics.points[{index}]",
                observed={"x": x_value, "y": y_value},
                box_refs=(panel.box_id,),
            )
        )
    return issues
def _check_publication_celltype_signature_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    left_panel = panel_boxes_by_id.get("panel_left") or _first_box_of_type(sidecar.panel_boxes, "panel")
    right_panel = panel_boxes_by_id.get("panel_right") or _first_box_of_type(sidecar.panel_boxes, "heatmap_tile_region")
    if left_panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="celltype-signature panel requires a left embedding panel",
                target="panel_left",
                expected="present",
            )
        )
    if right_panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="celltype-signature panel requires a right heatmap tile region",
                target="panel_right",
                expected="present",
            )
        )
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={"panel_label_A": "panel_left", "panel_label_B": "panel_right"},
        )
    )

    points = sidecar.metrics.get("points")
    if not isinstance(points, list) or not points:
        issues.append(
            _issue(
                rule_id="points_missing",
                message="celltype-signature panel requires non-empty embedding point metrics",
                target="metrics.points",
            )
        )
    elif left_panel is not None:
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
            group = str(point.get("group") or "").strip()
            if not group:
                issues.append(
                    _issue(
                        rule_id="empty_group_label",
                        message="group labels must be non-empty",
                        target=f"metrics.points[{index}].group",
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
            if _point_within_box(left_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="point_out_of_panel",
                    message="embedding point must stay within the left panel domain",
                    target=f"metrics.points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(left_panel.box_id,),
                )
            )

    group_labels = sidecar.metrics.get("group_labels")
    if group_labels is not None:
        if not isinstance(group_labels, list):
            raise ValueError("layout_sidecar.metrics.group_labels must be a list when present")
        seen_group_labels: set[str] = set()
        for index, item in enumerate(group_labels):
            group_label = str(item).strip()
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="empty_group_label",
                        message="group labels must be non-empty",
                        target=f"metrics.group_labels[{index}]",
                    )
                )
                continue
            if group_label in seen_group_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_group_label",
                        message=f"group label `{group_label}` must be unique",
                        target="metrics.group_labels",
                        observed=group_label,
                    )
                )
                continue
            seen_group_labels.add(group_label)

    score_method = str(sidecar.metrics.get("score_method") or "").strip()
    if not score_method:
        issues.append(
            _issue(
                rule_id="score_method_missing",
                message="celltype-signature panel requires a non-empty score_method",
                target="metrics.score_method",
            )
        )
    _matrix_cell_lookup(sidecar.metrics)
    return issues

def _check_publication_single_cell_atlas_overview_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_embedding",
                "panel_label_B": "panel_composition",
                "panel_label_C": "panel_heatmap",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    embedding_panel = panel_boxes_by_id.get("panel_embedding") or _first_box_of_type(sidecar.panel_boxes, "panel")
    composition_panel = panel_boxes_by_id.get("panel_composition") or _first_box_of_type(
        sidecar.panel_boxes, "composition_panel"
    )
    heatmap_panel = panel_boxes_by_id.get("panel_heatmap") or _first_box_of_type(
        sidecar.panel_boxes, "heatmap_tile_region"
    )
    for panel_box, target, message in (
        (embedding_panel, "panel_embedding", "single-cell atlas overview requires an embedding panel"),
        (composition_panel, "panel_composition", "single-cell atlas overview requires a composition panel"),
        (heatmap_panel, "panel_heatmap", "single-cell atlas overview requires a heatmap panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    state_labels = sidecar.metrics.get("state_labels")
    if not isinstance(state_labels, list) or not state_labels:
        issues.append(
            _issue(
                rule_id="state_labels_missing",
                message="single-cell atlas overview requires explicit non-empty state_labels metrics",
                target="metrics.state_labels",
            )
        )
        normalized_state_labels: list[str] = []
    else:
        normalized_state_labels = []
        seen_state_labels: set[str] = set()
        for index, item in enumerate(state_labels):
            state_label = str(item or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="state labels must be non-empty",
                        target=f"metrics.state_labels[{index}]",
                    )
                )
                continue
            if state_label in seen_state_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_state_label",
                        message=f"state label `{state_label}` must be unique",
                        target="metrics.state_labels",
                        observed=state_label,
                    )
                )
                continue
            seen_state_labels.add(state_label)
            normalized_state_labels.append(state_label)

    row_labels = sidecar.metrics.get("row_labels")
    if not isinstance(row_labels, list) or not row_labels:
        issues.append(
            _issue(
                rule_id="row_labels_missing",
                message="single-cell atlas overview requires explicit non-empty row_labels metrics",
                target="metrics.row_labels",
            )
        )
        normalized_row_labels: list[str] = []
    else:
        normalized_row_labels = []
        seen_row_labels: set[str] = set()
        for index, item in enumerate(row_labels):
            row_label = str(item or "").strip()
            if not row_label:
                issues.append(
                    _issue(
                        rule_id="empty_row_label",
                        message="heatmap row labels must be non-empty",
                        target=f"metrics.row_labels[{index}]",
                    )
                )
                continue
            if row_label in seen_row_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_row_label",
                        message=f"heatmap row label `{row_label}` must be unique",
                        target="metrics.row_labels",
                        observed=row_label,
                    )
                )
                continue
            seen_row_labels.add(row_label)
            normalized_row_labels.append(row_label)

    points = sidecar.metrics.get("points")
    if not isinstance(points, list) or not points:
        issues.append(
            _issue(
                rule_id="points_missing",
                message="single-cell atlas overview requires non-empty embedding point metrics",
                target="metrics.points",
            )
        )
    elif embedding_panel is not None:
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="embedding point state_label must be non-empty",
                        target=f"metrics.points[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id="point_state_label_unknown",
                        message="embedding point state_label must stay inside declared state_labels",
                        target=f"metrics.points[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
            if _point_within_box(embedding_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="point_out_of_panel",
                    message="embedding point must stay within the embedding panel domain",
                    target=f"metrics.points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(embedding_panel.box_id,),
                )
            )

    composition_groups = sidecar.metrics.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        issues.append(
            _issue(
                rule_id="composition_groups_missing",
                message="single-cell atlas overview requires non-empty composition_groups metrics",
                target="metrics.composition_groups",
            )
        )
    else:
        seen_group_labels: set[str] = set()
        previous_group_order = 0.0
        expected_state_set = set(normalized_state_labels)
        for group_index, item in enumerate(composition_groups):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.composition_groups[{group_index}] must be an object")
            group_label = str(item.get("group_label") or "").strip()
            group_order = _require_numeric(
                item.get("group_order"),
                label=f"layout_sidecar.metrics.composition_groups[{group_index}].group_order",
            )
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="composition_group_label_missing",
                        message="composition group_label must be non-empty",
                        target=f"metrics.composition_groups[{group_index}].group_label",
                    )
                )
            elif group_label in seen_group_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_composition_group_label",
                        message=f"composition group label `{group_label}` must be unique",
                        target="metrics.composition_groups",
                        observed=group_label,
                    )
                )
            else:
                seen_group_labels.add(group_label)
            if group_order <= previous_group_order:
                issues.append(
                    _issue(
                        rule_id="composition_group_order_not_increasing",
                        message="composition group_order must stay strictly increasing",
                        target="metrics.composition_groups",
                    )
                )
            previous_group_order = group_order
            state_proportions = item.get("state_proportions")
            if not isinstance(state_proportions, list) or not state_proportions:
                issues.append(
                    _issue(
                        rule_id="composition_group_state_proportions_missing",
                        message="composition groups require non-empty state_proportions",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                    )
                )
                continue
            observed_state_set: set[str] = set()
            total = 0.0
            for state_index, state_item in enumerate(state_proportions):
                if not isinstance(state_item, dict):
                    raise ValueError(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].state_proportions[{state_index}] must be an object"
                    )
                state_label = str(state_item.get("state_label") or "").strip()
                if state_label:
                    observed_state_set.add(state_label)
                proportion = _require_numeric(
                    state_item.get("proportion"),
                    label=(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].state_proportions[{state_index}].proportion"
                    ),
                )
                total += proportion
                if 0.0 <= proportion <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id="composition_proportion_out_of_range",
                        message="composition proportion must stay within [0, 1]",
                        target=f"metrics.composition_groups[{group_index}].state_proportions[{state_index}].proportion",
                        observed=proportion,
                    )
                )
            if expected_state_set and observed_state_set != expected_state_set:
                issues.append(
                    _issue(
                        rule_id="composition_group_state_set_mismatch",
                        message="composition state set must match declared state_labels",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                        observed=sorted(observed_state_set),
                        expected=sorted(expected_state_set),
                    )
                )
            if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                issues.append(
                    _issue(
                        rule_id="composition_group_sum_invalid",
                        message="composition state proportions must sum to 1",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                        observed=total,
                        expected=1.0,
                    )
                )

    matrix_lookup = _matrix_cell_lookup(sidecar.metrics)
    matrix_state_labels = {state_label for state_label, _ in matrix_lookup}
    matrix_row_labels = {row_label for _, row_label in matrix_lookup}
    if normalized_state_labels and matrix_state_labels != set(normalized_state_labels):
        issues.append(
            _issue(
                rule_id="heatmap_state_set_mismatch",
                message="heatmap cell x labels must match declared state_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_state_labels),
                expected=sorted(normalized_state_labels),
            )
        )
    if normalized_row_labels and matrix_row_labels != set(normalized_row_labels):
        issues.append(
            _issue(
                rule_id="heatmap_row_set_mismatch",
                message="heatmap cell y labels must match declared row_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_row_labels),
                expected=sorted(normalized_row_labels),
            )
        )
    expected_cell_count = len(normalized_state_labels) * len(normalized_row_labels)
    if expected_cell_count > 0 and len(matrix_lookup) != expected_cell_count:
        issues.append(
            _issue(
                rule_id="heatmap_grid_incomplete",
                message="heatmap grid must cover every declared state/row coordinate exactly once",
                target="metrics.matrix_cells",
                observed={"cells": len(matrix_lookup)},
                expected={"cells": expected_cell_count},
            )
        )

    return issues
