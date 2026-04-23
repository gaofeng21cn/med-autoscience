from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _check_boxes_within_device, _check_colorbar_panel_overlap, _check_composite_panel_label_anchors, _check_legend_panel_overlap, _check_pairwise_non_overlap, _check_required_box_types, _first_box_of_type, _issue, _matrix_cell_lookup, _point_within_box, _require_numeric, math

def _check_publication_trajectory_progression_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
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
                "panel_label_A": "panel_trajectory",
                "panel_label_B": "panel_composition",
                "panel_label_C": "panel_heatmap",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    trajectory_panel = panel_boxes_by_id.get("panel_trajectory") or _first_box_of_type(sidecar.panel_boxes, "panel")
    composition_panel = panel_boxes_by_id.get("panel_composition") or _first_box_of_type(
        sidecar.panel_boxes, "composition_panel"
    )
    heatmap_panel = panel_boxes_by_id.get("panel_heatmap") or _first_box_of_type(
        sidecar.panel_boxes, "heatmap_tile_region"
    )
    for panel_box, target, message in (
        (trajectory_panel, "panel_trajectory", "trajectory progression panel requires a trajectory panel"),
        (composition_panel, "panel_composition", "trajectory progression panel requires a composition panel"),
        (heatmap_panel, "panel_heatmap", "trajectory progression panel requires a heatmap panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    branch_labels = sidecar.metrics.get("branch_labels")
    if not isinstance(branch_labels, list) or not branch_labels:
        issues.append(
            _issue(
                rule_id="branch_labels_missing",
                message="trajectory progression panel requires explicit non-empty branch_labels metrics",
                target="metrics.branch_labels",
            )
        )
        normalized_branch_labels: list[str] = []
    else:
        normalized_branch_labels = []
        seen_branch_labels: set[str] = set()
        for index, item in enumerate(branch_labels):
            branch_label = str(item or "").strip()
            if not branch_label:
                issues.append(
                    _issue(
                        rule_id="empty_branch_label",
                        message="branch labels must be non-empty",
                        target=f"metrics.branch_labels[{index}]",
                    )
                )
                continue
            if branch_label in seen_branch_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_branch_label",
                        message=f"branch label `{branch_label}` must be unique",
                        target="metrics.branch_labels",
                        observed=branch_label,
                    )
                )
                continue
            seen_branch_labels.add(branch_label)
            normalized_branch_labels.append(branch_label)

    bin_labels = sidecar.metrics.get("bin_labels")
    if not isinstance(bin_labels, list) or not bin_labels:
        issues.append(
            _issue(
                rule_id="bin_labels_missing",
                message="trajectory progression panel requires explicit non-empty bin_labels metrics",
                target="metrics.bin_labels",
            )
        )
        normalized_bin_labels: list[str] = []
    else:
        normalized_bin_labels = []
        seen_bin_labels: set[str] = set()
        for index, item in enumerate(bin_labels):
            bin_label = str(item or "").strip()
            if not bin_label:
                issues.append(
                    _issue(
                        rule_id="empty_bin_label",
                        message="progression bin labels must be non-empty",
                        target=f"metrics.bin_labels[{index}]",
                    )
                )
                continue
            if bin_label in seen_bin_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_bin_label",
                        message=f"progression bin label `{bin_label}` must be unique",
                        target="metrics.bin_labels",
                        observed=bin_label,
                    )
                )
                continue
            seen_bin_labels.add(bin_label)
            normalized_bin_labels.append(bin_label)

    row_labels = sidecar.metrics.get("row_labels")
    if not isinstance(row_labels, list) or not row_labels:
        issues.append(
            _issue(
                rule_id="row_labels_missing",
                message="trajectory progression panel requires explicit non-empty row_labels metrics",
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
                message="trajectory progression panel requires non-empty trajectory point metrics",
                target="metrics.points",
            )
        )
    elif trajectory_panel is not None:
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
            branch_label = str(point.get("branch_label") or "").strip()
            if not branch_label:
                issues.append(
                    _issue(
                        rule_id="empty_branch_label",
                        message="trajectory point branch_label must be non-empty",
                        target=f"metrics.points[{index}].branch_label",
                    )
                )
            elif normalized_branch_labels and branch_label not in normalized_branch_labels:
                issues.append(
                    _issue(
                        rule_id="point_branch_label_unknown",
                        message="trajectory point branch_label must stay inside declared branch_labels",
                        target=f"metrics.points[{index}].branch_label",
                        observed=branch_label,
                        expected=normalized_branch_labels,
                    )
                )
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="point_state_label_missing",
                        message="trajectory point state_label must be non-empty",
                        target=f"metrics.points[{index}].state_label",
                    )
                )
            pseudotime = _require_numeric(point.get("pseudotime"), label=f"layout_sidecar.metrics.points[{index}].pseudotime")
            if not 0.0 <= pseudotime <= 1.0:
                issues.append(
                    _issue(
                        rule_id="point_pseudotime_out_of_range",
                        message="trajectory point pseudotime must stay within [0, 1]",
                        target=f"metrics.points[{index}].pseudotime",
                        observed=pseudotime,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
            if _point_within_box(trajectory_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="point_out_of_panel",
                    message="trajectory point must stay within the trajectory panel domain",
                    target=f"metrics.points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(trajectory_panel.box_id,),
                )
            )

    progression_bins = sidecar.metrics.get("progression_bins")
    if not isinstance(progression_bins, list) or not progression_bins:
        issues.append(
            _issue(
                rule_id="progression_bins_missing",
                message="trajectory progression panel requires non-empty progression_bins metrics",
                target="metrics.progression_bins",
            )
        )
    else:
        expected_branch_set = set(normalized_branch_labels)
        expected_bin_set = set(normalized_bin_labels)
        seen_bin_labels = set()
        previous_bin_order = 0.0
        previous_end = -1.0
        for bin_index, item in enumerate(progression_bins):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.progression_bins[{bin_index}] must be an object")
            bin_label = str(item.get("bin_label") or "").strip()
            if not bin_label:
                issues.append(
                    _issue(
                        rule_id="progression_bin_label_missing",
                        message="progression bin label must be non-empty",
                        target=f"metrics.progression_bins[{bin_index}].bin_label",
                    )
                )
            elif bin_label in seen_bin_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_progression_bin_label",
                        message=f"progression bin label `{bin_label}` must be unique",
                        target="metrics.progression_bins",
                        observed=bin_label,
                    )
                )
            else:
                seen_bin_labels.add(bin_label)

            bin_order = _require_numeric(
                item.get("bin_order"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].bin_order",
            )
            if bin_order <= previous_bin_order:
                issues.append(
                    _issue(
                        rule_id="progression_bin_order_not_increasing",
                        message="progression bin_order must stay strictly increasing",
                        target="metrics.progression_bins",
                    )
                )
            previous_bin_order = bin_order

            pseudotime_start = _require_numeric(
                item.get("pseudotime_start"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].pseudotime_start",
            )
            pseudotime_end = _require_numeric(
                item.get("pseudotime_end"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].pseudotime_end",
            )
            if not (0.0 <= pseudotime_start < pseudotime_end <= 1.0) or pseudotime_start < previous_end - 1e-9:
                issues.append(
                    _issue(
                        rule_id="progression_bin_interval_invalid",
                        message="progression bin intervals must advance monotonically within [0, 1]",
                        target=f"metrics.progression_bins[{bin_index}]",
                        observed={"start": pseudotime_start, "end": pseudotime_end},
                    )
                )
            previous_end = max(previous_end, pseudotime_end)

            branch_weights = item.get("branch_weights")
            if not isinstance(branch_weights, list) or not branch_weights:
                issues.append(
                    _issue(
                        rule_id="progression_bin_branch_weights_missing",
                        message="progression bins require non-empty branch_weights",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                    )
                )
                continue
            observed_branch_set: set[str] = set()
            total = 0.0
            for branch_index, branch_item in enumerate(branch_weights):
                if not isinstance(branch_item, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.progression_bins[{bin_index}].branch_weights[{branch_index}] must be an object"
                    )
                branch_label = str(branch_item.get("branch_label") or "").strip()
                if branch_label:
                    observed_branch_set.add(branch_label)
                proportion = _require_numeric(
                    branch_item.get("proportion"),
                    label=(
                        f"layout_sidecar.metrics.progression_bins[{bin_index}]."
                        f"branch_weights[{branch_index}].proportion"
                    ),
                )
                total += proportion
                if 0.0 <= proportion <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id="progression_bin_proportion_out_of_range",
                        message="progression bin branch proportions must stay within [0, 1]",
                        target=(
                            f"metrics.progression_bins[{bin_index}].branch_weights[{branch_index}].proportion"
                        ),
                        observed=proportion,
                    )
                )
            if expected_branch_set and observed_branch_set != expected_branch_set:
                issues.append(
                    _issue(
                        rule_id="progression_bin_branch_set_mismatch",
                        message="progression bin branch set must match declared branch_labels",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                        observed=sorted(observed_branch_set),
                        expected=sorted(expected_branch_set),
                    )
                )
            if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                issues.append(
                    _issue(
                        rule_id="progression_bin_sum_invalid",
                        message="progression bin branch weights must sum to 1",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                        observed=total,
                        expected=1.0,
                    )
                )

        if expected_bin_set and seen_bin_labels != expected_bin_set:
            issues.append(
                _issue(
                    rule_id="progression_bin_label_set_mismatch",
                    message="progression bin labels must match declared bin_labels",
                    target="metrics.progression_bins",
                    observed=sorted(seen_bin_labels),
                    expected=sorted(expected_bin_set),
                )
            )

    matrix_lookup = _matrix_cell_lookup(sidecar.metrics)
    matrix_bin_labels = {bin_label for bin_label, _ in matrix_lookup}
    matrix_row_labels = {row_label for _, row_label in matrix_lookup}
    if normalized_bin_labels and matrix_bin_labels != set(normalized_bin_labels):
        issues.append(
            _issue(
                rule_id="heatmap_bin_set_mismatch",
                message="heatmap cell x labels must match declared bin_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_bin_labels),
                expected=sorted(normalized_bin_labels),
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
    expected_cell_count = len(normalized_bin_labels) * len(normalized_row_labels)
    if expected_cell_count > 0 and len(matrix_lookup) != expected_cell_count:
        issues.append(
            _issue(
                rule_id="heatmap_grid_incomplete",
                message="heatmap grid must cover every declared bin/row coordinate exactly once",
                target="metrics.matrix_cells",
                observed={"cells": len(matrix_lookup)},
                expected={"cells": expected_cell_count},
            )
        )

    return issues
