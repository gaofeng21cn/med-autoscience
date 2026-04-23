from __future__ import annotations

from ..shared import Any, Box, LayoutSidecar, _all_boxes, _check_boxes_within_device, _check_colorbar_panel_overlap, _check_composite_panel_label_anchors, _check_legend_panel_overlap, _check_pairwise_non_overlap, _check_required_box_types, _issue, _point_within_box, _require_numeric

def _check_publication_atlas_spatial_trajectory_density_coverage_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
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
                "panel_label_D": "panel_support",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    atlas_panel = panel_boxes_by_id.get("panel_atlas")
    spatial_panel = panel_boxes_by_id.get("panel_spatial")
    trajectory_panel = panel_boxes_by_id.get("panel_trajectory")
    support_panel = panel_boxes_by_id.get("panel_support")
    for panel_box, target, message in (
        (atlas_panel, "panel_atlas", "density-coverage panel requires an atlas panel"),
        (spatial_panel, "panel_spatial", "density-coverage panel requires a spatial panel"),
        (trajectory_panel, "panel_trajectory", "density-coverage panel requires a trajectory panel"),
        (support_panel, "panel_support", "density-coverage panel requires a support panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    def _normalize_unique_labels(
        metric_key: str,
        missing_rule: str,
        empty_rule: str,
        duplicate_rule: str,
        message: str,
    ) -> list[str]:
        labels = sidecar.metrics.get(metric_key)
        if not isinstance(labels, list) or not labels:
            issues.append(_issue(rule_id=missing_rule, message=message, target=f"metrics.{metric_key}"))
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
        "density-coverage panel requires explicit non-empty state_labels metrics",
    )
    normalized_region_labels = _normalize_unique_labels(
        "region_labels",
        "region_labels_missing",
        "empty_region_label",
        "duplicate_region_label",
        "density-coverage panel requires explicit non-empty region_labels metrics",
    )
    normalized_branch_labels = _normalize_unique_labels(
        "branch_labels",
        "branch_labels_missing",
        "empty_branch_label",
        "duplicate_branch_label",
        "density-coverage panel requires explicit non-empty branch_labels metrics",
    )
    normalized_context_labels = _normalize_unique_labels(
        "context_labels",
        "context_labels_missing",
        "empty_context_label",
        "duplicate_context_label",
        "density-coverage panel requires explicit non-empty context_labels metrics",
    )
    normalized_context_kinds = _normalize_unique_labels(
        "context_kinds",
        "context_kinds_missing",
        "empty_context_kind",
        "duplicate_context_kind",
        "density-coverage panel requires explicit non-empty context_kinds metrics",
    )
    required_context_kinds = {"atlas_density", "spatial_coverage", "trajectory_coverage"}
    if normalized_context_kinds and set(normalized_context_kinds) != required_context_kinds:
        issues.append(
            _issue(
                rule_id="context_kind_set_mismatch",
                message="context_kinds must cover atlas_density, spatial_coverage, and trajectory_coverage",
                target="metrics.context_kinds",
                observed=sorted(normalized_context_kinds),
                expected=sorted(required_context_kinds),
            )
        )
    if normalized_context_labels and normalized_context_kinds and len(normalized_context_labels) != len(normalized_context_kinds):
        issues.append(
            _issue(
                rule_id="context_label_kind_count_mismatch",
                message="context_labels and context_kinds must stay aligned one-to-one",
                target="metrics.context_kinds",
                observed=len(normalized_context_kinds),
                expected=len(normalized_context_labels),
            )
        )
    support_scale_label = str(sidecar.metrics.get("support_scale_label") or "").strip()
    if not support_scale_label:
        issues.append(
            _issue(
                rule_id="support_scale_label_missing",
                message="density-coverage panel requires a non-empty support_scale_label",
                target="metrics.support_scale_label",
            )
        )

    def _check_state_points(points_key: str, panel_box: Box | None, unknown_rule: str, out_rule: str, human_name: str) -> None:
        points = sidecar.metrics.get(points_key)
        if not isinstance(points, list) or not points:
            issues.append(
                _issue(
                    rule_id=f"{points_key}_missing",
                    message=f"density-coverage panel requires non-empty {points_key} metrics",
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

    spatial_points = sidecar.metrics.get("spatial_points")
    if isinstance(spatial_points, list):
        for index, point in enumerate(spatial_points):
            if not isinstance(point, dict):
                continue
            region_label = str(point.get("region_label") or "").strip()
            if not region_label:
                issues.append(
                    _issue(
                        rule_id="empty_region_label",
                        message="spatial point region_label must be non-empty",
                        target=f"metrics.spatial_points[{index}].region_label",
                    )
                )
            elif normalized_region_labels and region_label not in normalized_region_labels:
                issues.append(
                    _issue(
                        rule_id="spatial_point_region_label_unknown",
                        message="spatial point region_label must stay inside declared region_labels",
                        target=f"metrics.spatial_points[{index}].region_label",
                        observed=region_label,
                        expected=normalized_region_labels,
                    )
                )

    trajectory_points = sidecar.metrics.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        issues.append(
            _issue(
                rule_id="trajectory_points_missing",
                message="density-coverage panel requires non-empty trajectory_points metrics",
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
            pseudotime = _require_numeric(
                point.get("pseudotime"),
                label=f"layout_sidecar.metrics.trajectory_points[{index}].pseudotime",
            )
            if not (0.0 <= pseudotime <= 1.0):
                issues.append(
                    _issue(
                        rule_id="trajectory_point_pseudotime_out_of_range",
                        message="trajectory point pseudotime must stay within [0, 1]",
                        target=f"metrics.trajectory_points[{index}].pseudotime",
                        observed=pseudotime,
                    )
                )
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

    support_cells = sidecar.metrics.get("support_cells")
    if not isinstance(support_cells, list) or not support_cells:
        issues.append(
            _issue(
                rule_id="support_cells_missing",
                message="density-coverage panel requires non-empty support_cells metrics",
                target="metrics.support_cells",
            )
        )
    else:
        observed_contexts: set[str] = set()
        observed_states: set[str] = set()
        seen_coordinates: set[tuple[str, str]] = set()
        for index, cell in enumerate(support_cells):
            if not isinstance(cell, dict):
                raise ValueError(f"layout_sidecar.metrics.support_cells[{index}] must be an object")
            context_label = str(cell.get("x") or "").strip()
            state_label = str(cell.get("y") or "").strip()
            if not context_label or not state_label:
                issues.append(
                    _issue(
                        rule_id="support_cell_coordinate_missing",
                        message="support cell must include non-empty x and y labels",
                        target=f"metrics.support_cells[{index}]",
                    )
                )
                continue
            if normalized_context_labels and context_label not in normalized_context_labels:
                issues.append(
                    _issue(
                        rule_id="support_cell_context_unknown",
                        message="support cell x labels must stay inside declared context_labels",
                        target=f"metrics.support_cells[{index}].x",
                        observed=context_label,
                        expected=normalized_context_labels,
                    )
                )
            if normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id="support_cell_state_unknown",
                        message="support cell y labels must stay inside declared state_labels",
                        target=f"metrics.support_cells[{index}].y",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            coordinate = (context_label, state_label)
            if coordinate in seen_coordinates:
                issues.append(
                    _issue(
                        rule_id="duplicate_support_cell",
                        message="support cell coordinates must be unique",
                        target=f"metrics.support_cells[{index}]",
                        observed={"x": context_label, "y": state_label},
                    )
                )
                continue
            seen_coordinates.add(coordinate)
            observed_contexts.add(context_label)
            observed_states.add(state_label)
            value = _require_numeric(
                cell.get("value"),
                label=f"layout_sidecar.metrics.support_cells[{index}].value",
            )
            if 0.0 <= value <= 1.0:
                continue
            issues.append(
                _issue(
                    rule_id="support_value_out_of_range",
                    message="support cell values must stay within [0, 1]",
                    target=f"metrics.support_cells[{index}].value",
                    observed=value,
                )
            )
        expected_coordinates = {(context_label, state_label) for state_label in normalized_state_labels for context_label in normalized_context_labels}
        if (
            normalized_context_labels
            and normalized_state_labels
            and (
                observed_contexts != set(normalized_context_labels)
                or observed_states != set(normalized_state_labels)
                or seen_coordinates != expected_coordinates
            )
        ):
            issues.append(
                _issue(
                    rule_id="support_grid_incomplete",
                    message="support grid must cover every declared context/state coordinate exactly once",
                    target="metrics.support_cells",
                    observed={"cells": len(seen_coordinates)},
                    expected={"cells": len(expected_coordinates)},
                )
            )

    return issues
