from __future__ import annotations

from ..shared import Any, Box, LayoutSidecar, _all_boxes, _check_boxes_within_device, _check_colorbar_panel_overlap, _check_composite_panel_label_anchors, _check_legend_panel_overlap, _check_pairwise_non_overlap, _check_required_box_types, _issue, _matrix_cell_lookup, _point_within_box, _require_numeric, math

def _check_publication_atlas_spatial_trajectory_storyboard_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
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
                "panel_label_A": "panel_atlas",
                "panel_label_B": "panel_spatial",
                "panel_label_C": "panel_trajectory",
                "panel_label_D": "panel_composition",
                "panel_label_E": "panel_heatmap",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    atlas_panel = panel_boxes_by_id.get("panel_atlas")
    spatial_panel = panel_boxes_by_id.get("panel_spatial")
    trajectory_panel = panel_boxes_by_id.get("panel_trajectory")
    composition_panel = panel_boxes_by_id.get("panel_composition")
    heatmap_panel = panel_boxes_by_id.get("panel_heatmap")
    for panel_box, target, message in (
        (atlas_panel, "panel_atlas", "storyboard panel requires an atlas panel"),
        (spatial_panel, "panel_spatial", "storyboard panel requires a spatial panel"),
        (trajectory_panel, "panel_trajectory", "storyboard panel requires a trajectory panel"),
        (composition_panel, "panel_composition", "storyboard panel requires a composition panel"),
        (heatmap_panel, "panel_heatmap", "storyboard panel requires a heatmap panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    def _normalize_unique_labels(metric_key: str, missing_rule: str, empty_rule: str, duplicate_rule: str, message: str) -> list[str]:
        labels = sidecar.metrics.get(metric_key)
        if not isinstance(labels, list) or not labels:
            issues.append(
                _issue(
                    rule_id=missing_rule,
                    message=message,
                    target=f"metrics.{metric_key}",
                )
            )
            return []
        normalized: list[str] = []
        seen: set[str] = set()
        for index, item in enumerate(labels):
            label = str(item or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id=empty_rule,
                        message=f"{metric_key} labels must be non-empty",
                        target=f"metrics.{metric_key}[{index}]",
                    )
                )
                continue
            if label in seen:
                issues.append(
                    _issue(
                        rule_id=duplicate_rule,
                        message=f"{metric_key} label `{label}` must be unique",
                        target=f"metrics.{metric_key}",
                        observed=label,
                    )
                )
                continue
            seen.add(label)
            normalized.append(label)
        return normalized

    normalized_state_labels = _normalize_unique_labels(
        "state_labels",
        "state_labels_missing",
        "empty_state_label",
        "duplicate_state_label",
        "storyboard panel requires explicit non-empty state_labels metrics",
    )
    normalized_branch_labels = _normalize_unique_labels(
        "branch_labels",
        "branch_labels_missing",
        "empty_branch_label",
        "duplicate_branch_label",
        "storyboard panel requires explicit non-empty branch_labels metrics",
    )
    normalized_bin_labels = _normalize_unique_labels(
        "bin_labels",
        "bin_labels_missing",
        "empty_bin_label",
        "duplicate_bin_label",
        "storyboard panel requires explicit non-empty bin_labels metrics",
    )
    normalized_row_labels = _normalize_unique_labels(
        "row_labels",
        "row_labels_missing",
        "empty_row_label",
        "duplicate_row_label",
        "storyboard panel requires explicit non-empty row_labels metrics",
    )

    def _check_state_points(points_key: str, panel_box: Box | None, unknown_rule: str, out_rule: str, human_name: str) -> None:
        points = sidecar.metrics.get(points_key)
        if not isinstance(points, list) or not points:
            issues.append(
                _issue(
                    rule_id=f"{points_key}_missing",
                    message=f"storyboard panel requires non-empty {points_key} metrics",
                    target=f"metrics.{points_key}",
                )
            )
            return
        if panel_box is None:
            return
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.{points_key}[{index}] must be an object")
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message=f"{human_name} state_label must be non-empty",
                        target=f"metrics.{points_key}[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id=unknown_rule,
                        message=f"{human_name} state_label must stay inside declared state_labels",
                        target=f"metrics.{points_key}[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.{points_key}[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.{points_key}[{index}].y")
            if _point_within_box(panel_box, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id=out_rule,
                    message=f"{human_name} must stay within its panel domain",
                    target=f"metrics.{points_key}[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(panel_box.box_id,),
                )
            )

    _check_state_points("atlas_points", atlas_panel, "atlas_point_state_label_unknown", "atlas_point_out_of_panel", "atlas point")
    _check_state_points(
        "spatial_points",
        spatial_panel,
        "spatial_point_state_label_unknown",
        "spatial_point_out_of_panel",
        "spatial point",
    )

    trajectory_points = sidecar.metrics.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        issues.append(
            _issue(
                rule_id="trajectory_points_missing",
                message="storyboard panel requires non-empty trajectory_points metrics",
                target="metrics.trajectory_points",
            )
        )
    elif trajectory_panel is not None:
        for index, point in enumerate(trajectory_points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.trajectory_points[{index}] must be an object")
            branch_label = str(point.get("branch_label") or "").strip()
            if not branch_label:
                issues.append(
                    _issue(
                        rule_id="empty_branch_label",
                        message="trajectory point branch_label must be non-empty",
                        target=f"metrics.trajectory_points[{index}].branch_label",
                    )
                )
            elif normalized_branch_labels and branch_label not in normalized_branch_labels:
                issues.append(
                    _issue(
                        rule_id="trajectory_point_branch_label_unknown",
                        message="trajectory point branch_label must stay inside declared branch_labels",
                        target=f"metrics.trajectory_points[{index}].branch_label",
                        observed=branch_label,
                        expected=normalized_branch_labels,
                    )
                )
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="trajectory point state_label must be non-empty",
                        target=f"metrics.trajectory_points[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id="trajectory_point_state_label_unknown",
                        message="trajectory point state_label must stay inside declared state_labels",
                        target=f"metrics.trajectory_points[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            _require_numeric(point.get("pseudotime"), label=f"layout_sidecar.metrics.trajectory_points[{index}].pseudotime")
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.trajectory_points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.trajectory_points[{index}].y")
            if _point_within_box(trajectory_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="trajectory_point_out_of_panel",
                    message="trajectory point must stay within the trajectory panel domain",
                    target=f"metrics.trajectory_points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(trajectory_panel.box_id,),
                )
            )

    composition_groups = sidecar.metrics.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        issues.append(
            _issue(
                rule_id="composition_groups_missing",
                message="storyboard panel requires non-empty composition_groups metrics",
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
                        target=(
                            "metrics.composition_groups"
                            f"[{group_index}].state_proportions[{state_index}].proportion"
                        ),
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

    progression_bins = sidecar.metrics.get("progression_bins")
    if not isinstance(progression_bins, list) or not progression_bins:
        issues.append(
            _issue(
                rule_id="progression_bins_missing",
                message="storyboard panel requires non-empty progression_bins metrics",
                target="metrics.progression_bins",
            )
        )
    else:
        seen_bin_labels_set: set[str] = set()
        previous_bin_order = 0.0
        previous_end = -1.0
        expected_branch_set = set(normalized_branch_labels)
        for bin_index, item in enumerate(progression_bins):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.progression_bins[{bin_index}] must be an object")
            bin_label = str(item.get("bin_label") or "").strip()
            bin_order = _require_numeric(
                item.get("bin_order"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].bin_order",
            )
            if not bin_label:
                issues.append(
                    _issue(
                        rule_id="progression_bin_label_missing",
                        message="progression bin label must be non-empty",
                        target=f"metrics.progression_bins[{bin_index}].bin_label",
                    )
                )
            elif bin_label in seen_bin_labels_set:
                issues.append(
                    _issue(
                        rule_id="duplicate_bin_label",
                        message=f"progression bin label `{bin_label}` must be unique",
                        target="metrics.progression_bins",
                        observed=bin_label,
                    )
                )
            else:
                seen_bin_labels_set.add(bin_label)
            if bin_order <= previous_bin_order:
                issues.append(
                    _issue(
                        rule_id="progression_bin_order_not_increasing",
                        message="progression bin_order must stay strictly increasing",
                        target="metrics.progression_bins",
                    )
                )
            previous_bin_order = bin_order
            start = _require_numeric(
                item.get("pseudotime_start"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].pseudotime_start",
            )
            end = _require_numeric(
                item.get("pseudotime_end"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].pseudotime_end",
            )
            if end <= start:
                issues.append(
                    _issue(
                        rule_id="progression_bin_interval_invalid",
                        message="progression bin must satisfy pseudotime_start < pseudotime_end",
                        target=f"metrics.progression_bins[{bin_index}]",
                    )
                )
            if start < previous_end - 1e-9:
                issues.append(
                    _issue(
                        rule_id="progression_bin_interval_not_increasing",
                        message="progression bin intervals must stay strictly increasing",
                        target="metrics.progression_bins",
                    )
                )
            previous_end = end
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
            seen_weight_branches: set[str] = set()
            total = 0.0
            for branch_index, branch_item in enumerate(branch_weights):
                if not isinstance(branch_item, dict):
                    raise ValueError(
                        "layout_sidecar.metrics.progression_bins"
                        f"[{bin_index}].branch_weights[{branch_index}] must be an object"
                    )
                branch_label = str(branch_item.get("branch_label") or "").strip()
                if branch_label:
                    seen_weight_branches.add(branch_label)
                proportion = _require_numeric(
                    branch_item.get("proportion"),
                    label=(
                        "layout_sidecar.metrics.progression_bins"
                        f"[{bin_index}].branch_weights[{branch_index}].proportion"
                    ),
                )
                total += proportion
                if 0.0 <= proportion <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id="progression_bin_branch_proportion_out_of_range",
                        message="progression bin branch proportion must stay within [0, 1]",
                        target=(
                            "metrics.progression_bins"
                            f"[{bin_index}].branch_weights[{branch_index}].proportion"
                        ),
                        observed=proportion,
                    )
                )
            if expected_branch_set and seen_weight_branches != expected_branch_set:
                issues.append(
                    _issue(
                        rule_id="progression_bin_branch_set_mismatch",
                        message="progression bin branch set must match declared branch_labels",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                        observed=sorted(seen_weight_branches),
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
        if normalized_bin_labels and seen_bin_labels_set != set(normalized_bin_labels):
            issues.append(
                _issue(
                    rule_id="progression_bin_label_set_mismatch",
                    message="progression bin labels must match declared bin_labels",
                    target="metrics.progression_bins",
                    observed=sorted(seen_bin_labels_set),
                    expected=sorted(normalized_bin_labels),
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
