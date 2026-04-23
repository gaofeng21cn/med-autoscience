from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, _require_probability_value
from .validation_tables import _validate_labeled_order_payload

def _validate_atlas_spatial_trajectory_storyboard_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    atlas_panel_title = _require_non_empty_string(
        payload.get("atlas_panel_title"),
        label=f"{path.name} display `{expected_display_id}` atlas_panel_title",
    )
    atlas_x_label = _require_non_empty_string(
        payload.get("atlas_x_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_x_label",
    )
    atlas_y_label = _require_non_empty_string(
        payload.get("atlas_y_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_y_label",
    )
    spatial_panel_title = _require_non_empty_string(
        payload.get("spatial_panel_title"),
        label=f"{path.name} display `{expected_display_id}` spatial_panel_title",
    )
    spatial_x_label = _require_non_empty_string(
        payload.get("spatial_x_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_x_label",
    )
    spatial_y_label = _require_non_empty_string(
        payload.get("spatial_y_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_y_label",
    )
    trajectory_panel_title = _require_non_empty_string(
        payload.get("trajectory_panel_title"),
        label=f"{path.name} display `{expected_display_id}` trajectory_panel_title",
    )
    trajectory_x_label = _require_non_empty_string(
        payload.get("trajectory_x_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_x_label",
    )
    trajectory_y_label = _require_non_empty_string(
        payload.get("trajectory_y_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_y_label",
    )
    composition_panel_title = _require_non_empty_string(
        payload.get("composition_panel_title"),
        label=f"{path.name} display `{expected_display_id}` composition_panel_title",
    )
    composition_x_label = _require_non_empty_string(
        payload.get("composition_x_label"),
        label=f"{path.name} display `{expected_display_id}` composition_x_label",
    )
    composition_y_label = _require_non_empty_string(
        payload.get("composition_y_label"),
        label=f"{path.name} display `{expected_display_id}` composition_y_label",
    )
    heatmap_panel_title = _require_non_empty_string(
        payload.get("heatmap_panel_title"),
        label=f"{path.name} display `{expected_display_id}` heatmap_panel_title",
    )
    heatmap_x_label = _require_non_empty_string(
        payload.get("heatmap_x_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_x_label",
    )
    heatmap_y_label = _require_non_empty_string(
        payload.get("heatmap_y_label"),
        label=f"{path.name} display `{expected_display_id}` heatmap_y_label",
    )

    atlas_points = payload.get("atlas_points")
    if not isinstance(atlas_points, list) or not atlas_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty atlas_points list")
    normalized_atlas_points: list[dict[str, Any]] = []
    observed_atlas_states: set[str] = set()
    for index, item in enumerate(atlas_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` atlas_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].state_label",
        )
        observed_atlas_states.add(state_label)
        normalized_atlas_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].y",
                ),
                "state_label": state_label,
            }
        )

    spatial_points = payload.get("spatial_points")
    if not isinstance(spatial_points, list) or not spatial_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty spatial_points list")
    normalized_spatial_points: list[dict[str, Any]] = []
    observed_spatial_states: set[str] = set()
    for index, item in enumerate(spatial_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` spatial_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].state_label",
        )
        observed_spatial_states.add(state_label)
        normalized_point = {
            "x": _require_numeric_value(
                item.get("x"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].x",
            ),
            "y": _require_numeric_value(
                item.get("y"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].y",
            ),
            "state_label": state_label,
        }
        region_label = str(item.get("region_label") or "").strip()
        if region_label:
            normalized_point["region_label"] = region_label
        normalized_spatial_points.append(normalized_point)

    trajectory_points = payload.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty trajectory_points list")
    normalized_trajectory_points: list[dict[str, Any]] = []
    observed_trajectory_states: set[str] = set()
    observed_branch_labels: set[str] = set()
    for index, item in enumerate(trajectory_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` trajectory_points[{index}] must be an object")
        branch_label = _require_non_empty_string(
            item.get("branch_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].branch_label",
        )
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].state_label",
        )
        observed_branch_labels.add(branch_label)
        observed_trajectory_states.add(state_label)
        normalized_trajectory_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].y",
                ),
                "branch_label": branch_label,
                "state_label": state_label,
                "pseudotime": _require_probability_value(
                    item.get("pseudotime"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].pseudotime",
                ),
            }
        )

    state_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("state_order"),
        label=f"display `{expected_display_id}` state_order",
    )
    declared_state_labels = {item["label"] for item in state_order}
    if observed_atlas_states != declared_state_labels:
        raise ValueError(f"{path.name} display `{expected_display_id}` state_order labels must match atlas point state labels")
    if observed_spatial_states != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` state_order labels must match spatial point state labels"
        )
    if observed_trajectory_states != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` state_order labels must match trajectory point state labels"
        )

    branch_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("branch_order"),
        label=f"display `{expected_display_id}` branch_order",
    )
    declared_branch_labels = {item["label"] for item in branch_order}
    if observed_branch_labels != declared_branch_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` branch_order labels must match trajectory point branch labels"
        )

    progression_bins = payload.get("progression_bins")
    if not isinstance(progression_bins, list) or not progression_bins:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty progression_bins list")
    normalized_progression_bins: list[dict[str, Any]] = []
    seen_bin_labels: set[str] = set()
    previous_bin_order = 0
    previous_end = -1.0
    for index, item in enumerate(progression_bins):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` progression_bins[{index}] must be an object")
        bin_label = _require_non_empty_string(
            item.get("bin_label"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].bin_label",
        )
        if bin_label in seen_bin_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}].bin_label must be unique"
            )
        seen_bin_labels.add(bin_label)
        bin_order = _require_non_negative_int(
            item.get("bin_order"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].bin_order",
            allow_zero=False,
        )
        if bin_order <= previous_bin_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins bin_order must be strictly increasing"
            )
        previous_bin_order = bin_order
        pseudotime_start = _require_probability_value(
            item.get("pseudotime_start"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].pseudotime_start",
        )
        pseudotime_end = _require_probability_value(
            item.get("pseudotime_end"),
            label=f"{path.name} display `{expected_display_id}` progression_bins[{index}].pseudotime_end",
        )
        if pseudotime_end <= pseudotime_start:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}] must satisfy pseudotime_start < pseudotime_end"
            )
        if pseudotime_start < previous_end - 1e-9:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins intervals must be strictly increasing"
            )
        previous_end = pseudotime_end

        branch_weights = item.get("branch_weights")
        if not isinstance(branch_weights, list) or not branch_weights:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}].branch_weights must be non-empty"
            )
        normalized_branch_weights: list[dict[str, Any]] = []
        seen_weight_branches: set[str] = set()
        weight_sum = 0.0
        for branch_index, branch_item in enumerate(branch_weights):
            if not isinstance(branch_item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}].branch_weights[{branch_index}] must be an object"
                )
            branch_label = _require_non_empty_string(
                branch_item.get("branch_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}]."
                    f"branch_weights[{branch_index}].branch_label"
                ),
            )
            if branch_label in seen_weight_branches:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}] must cover the declared branch labels exactly once"
                )
            seen_weight_branches.add(branch_label)
            proportion = _require_probability_value(
                branch_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}]."
                    f"branch_weights[{branch_index}].proportion"
                ),
            )
            weight_sum += proportion
            normalized_branch_weights.append({"branch_label": branch_label, "proportion": proportion})
        if seen_weight_branches != declared_branch_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}] must cover the declared branch labels exactly once"
            )
        if abs(weight_sum - 1.0) > 1e-6:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` progression_bins[{index}] branch weights must sum to 1"
            )
        normalized_progression_bins.append(
            {
                "bin_label": bin_label,
                "bin_order": bin_order,
                "pseudotime_start": pseudotime_start,
                "pseudotime_end": pseudotime_end,
                "branch_weights": normalized_branch_weights,
            }
        )

    row_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("row_order"),
        label=f"display `{expected_display_id}` row_order",
    )
    column_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("column_order"),
        label=f"display `{expected_display_id}` column_order",
    )
    declared_columns = {item["label"] for item in column_order}
    if seen_bin_labels != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match progression bin labels"
        )

    composition_groups = payload.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty composition_groups list")
    normalized_composition_groups: list[dict[str, Any]] = []
    seen_group_labels: set[str] = set()
    previous_group_order = 0
    for index, item in enumerate(composition_groups):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` composition_groups[{index}] must be an object")
        group_label = _require_non_empty_string(
            item.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        group_order = _require_non_negative_int(
            item.get("group_order"),
            label=f"{path.name} display `{expected_display_id}` composition_groups[{index}].group_order",
            allow_zero=False,
        )
        if group_order <= previous_group_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups group_order must be strictly increasing"
            )
        previous_group_order = group_order
        state_proportions = item.get("state_proportions")
        if not isinstance(state_proportions, list) or not state_proportions:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].state_proportions must be non-empty"
            )
        normalized_state_proportions: list[dict[str, Any]] = []
        seen_state_labels: set[str] = set()
        proportion_sum = 0.0
        for state_index, state_item in enumerate(state_proportions):
            if not isinstance(state_item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}].state_proportions[{state_index}] must be an object"
                )
            state_label = _require_non_empty_string(
                state_item.get("state_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"state_proportions[{state_index}].state_label"
                ),
            )
            if state_label in seen_state_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared state labels exactly once"
                )
            seen_state_labels.add(state_label)
            proportion = _require_probability_value(
                state_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"state_proportions[{state_index}].proportion"
                ),
            )
            proportion_sum += proportion
            normalized_state_proportions.append({"state_label": state_label, "proportion": proportion})
        if seen_state_labels != declared_state_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared state labels exactly once"
            )
        if abs(proportion_sum - 1.0) > 1e-6:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] proportions must sum to 1"
            )
        normalized_composition_groups.append(
            {
                "group_label": group_label,
                "group_order": group_order,
                "state_proportions": normalized_state_proportions,
            }
        )

    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty cells list")
    normalized_cells: list[dict[str, Any]] = []
    observed_rows: set[str] = set()
    observed_columns: set[str] = set()
    observed_coordinates: set[tuple[str, str]] = set()
    for index, item in enumerate(cells):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` cells[{index}] must be an object")
        column_label = _require_non_empty_string(
            item.get("x"),
            label=f"{path.name} display `{expected_display_id}` cells[{index}].x",
        )
        row_label = _require_non_empty_string(
            item.get("y"),
            label=f"{path.name} display `{expected_display_id}` cells[{index}].y",
        )
        coordinate = (column_label, row_label)
        if coordinate in observed_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once"
            )
        observed_coordinates.add(coordinate)
        observed_columns.add(column_label)
        observed_rows.add(row_label)
        normalized_cells.append(
            {
                "x": column_label,
                "y": row_label,
                "value": _require_numeric_value(
                    item.get("value"),
                    label=f"{path.name} display `{expected_display_id}` cells[{index}].value",
                ),
            }
        )

    declared_rows = {item["label"] for item in row_order}
    if observed_rows != declared_rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` row_order labels must match cell y labels")
    if observed_columns != declared_columns:
        raise ValueError(f"{path.name} display `{expected_display_id}` column_order labels must match cell x labels")
    expected_coordinates = {(column["label"], row["label"]) for row in row_order for column in column_order}
    if observed_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "atlas_panel_title": atlas_panel_title,
        "atlas_x_label": atlas_x_label,
        "atlas_y_label": atlas_y_label,
        "atlas_annotation": str(payload.get("atlas_annotation") or "").strip(),
        "atlas_points": normalized_atlas_points,
        "spatial_panel_title": spatial_panel_title,
        "spatial_x_label": spatial_x_label,
        "spatial_y_label": spatial_y_label,
        "spatial_annotation": str(payload.get("spatial_annotation") or "").strip(),
        "spatial_points": normalized_spatial_points,
        "trajectory_panel_title": trajectory_panel_title,
        "trajectory_x_label": trajectory_x_label,
        "trajectory_y_label": trajectory_y_label,
        "trajectory_annotation": str(payload.get("trajectory_annotation") or "").strip(),
        "trajectory_points": normalized_trajectory_points,
        "composition_panel_title": composition_panel_title,
        "composition_x_label": composition_x_label,
        "composition_y_label": composition_y_label,
        "composition_annotation": str(payload.get("composition_annotation") or "").strip(),
        "composition_groups": normalized_composition_groups,
        "heatmap_panel_title": heatmap_panel_title,
        "heatmap_x_label": heatmap_x_label,
        "heatmap_y_label": heatmap_y_label,
        "heatmap_annotation": str(payload.get("heatmap_annotation") or "").strip(),
        "score_method": _require_non_empty_string(
            payload.get("score_method"),
            label=f"{path.name} display `{expected_display_id}` score_method",
        ),
        "state_order": state_order,
        "branch_order": branch_order,
        "progression_bins": normalized_progression_bins,
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }

def _validate_atlas_spatial_trajectory_density_coverage_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    atlas_panel_title = _require_non_empty_string(
        payload.get("atlas_panel_title"),
        label=f"{path.name} display `{expected_display_id}` atlas_panel_title",
    )
    atlas_x_label = _require_non_empty_string(
        payload.get("atlas_x_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_x_label",
    )
    atlas_y_label = _require_non_empty_string(
        payload.get("atlas_y_label"),
        label=f"{path.name} display `{expected_display_id}` atlas_y_label",
    )
    spatial_panel_title = _require_non_empty_string(
        payload.get("spatial_panel_title"),
        label=f"{path.name} display `{expected_display_id}` spatial_panel_title",
    )
    spatial_x_label = _require_non_empty_string(
        payload.get("spatial_x_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_x_label",
    )
    spatial_y_label = _require_non_empty_string(
        payload.get("spatial_y_label"),
        label=f"{path.name} display `{expected_display_id}` spatial_y_label",
    )
    trajectory_panel_title = _require_non_empty_string(
        payload.get("trajectory_panel_title"),
        label=f"{path.name} display `{expected_display_id}` trajectory_panel_title",
    )
    trajectory_x_label = _require_non_empty_string(
        payload.get("trajectory_x_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_x_label",
    )
    trajectory_y_label = _require_non_empty_string(
        payload.get("trajectory_y_label"),
        label=f"{path.name} display `{expected_display_id}` trajectory_y_label",
    )
    support_panel_title = _require_non_empty_string(
        payload.get("support_panel_title"),
        label=f"{path.name} display `{expected_display_id}` support_panel_title",
    )
    support_x_label = _require_non_empty_string(
        payload.get("support_x_label"),
        label=f"{path.name} display `{expected_display_id}` support_x_label",
    )
    support_y_label = _require_non_empty_string(
        payload.get("support_y_label"),
        label=f"{path.name} display `{expected_display_id}` support_y_label",
    )
    support_scale_label = _require_non_empty_string(
        payload.get("support_scale_label"),
        label=f"{path.name} display `{expected_display_id}` support_scale_label",
    )

    atlas_points = payload.get("atlas_points")
    if not isinstance(atlas_points, list) or not atlas_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty atlas_points list")
    normalized_atlas_points: list[dict[str, Any]] = []
    observed_atlas_states: set[str] = set()
    for index, item in enumerate(atlas_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` atlas_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].state_label",
        )
        observed_atlas_states.add(state_label)
        normalized_atlas_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` atlas_points[{index}].y",
                ),
                "state_label": state_label,
            }
        )

    spatial_points = payload.get("spatial_points")
    if not isinstance(spatial_points, list) or not spatial_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty spatial_points list")
    normalized_spatial_points: list[dict[str, Any]] = []
    observed_spatial_states: set[str] = set()
    for index, item in enumerate(spatial_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` spatial_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].state_label",
        )
        region_label = _require_non_empty_string(
            item.get("region_label"),
            label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].region_label",
        )
        observed_spatial_states.add(state_label)
        normalized_spatial_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].y",
                ),
                "state_label": state_label,
                "region_label": region_label,
            }
        )

    trajectory_points = payload.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty trajectory_points list")
    normalized_trajectory_points: list[dict[str, Any]] = []
    observed_trajectory_states: set[str] = set()
    observed_branch_labels: set[str] = set()
    for index, item in enumerate(trajectory_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` trajectory_points[{index}] must be an object")
        branch_label = _require_non_empty_string(
            item.get("branch_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].branch_label",
        )
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].state_label",
        )
        observed_branch_labels.add(branch_label)
        observed_trajectory_states.add(state_label)
        normalized_trajectory_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].y",
                ),
                "branch_label": branch_label,
                "state_label": state_label,
                "pseudotime": _require_probability_value(
                    item.get("pseudotime"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].pseudotime",
                ),
            }
        )

    state_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("state_order"),
        label=f"display `{expected_display_id}` state_order",
    )
    declared_state_labels = {item["label"] for item in state_order}
    if observed_atlas_states != declared_state_labels:
        raise ValueError(f"{path.name} display `{expected_display_id}` state_order labels must match atlas point state labels")
    if observed_spatial_states != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` state_order labels must match spatial point state labels"
        )
    if observed_trajectory_states != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` state_order labels must match trajectory point state labels"
        )

    context_order = payload.get("context_order")
    if not isinstance(context_order, list) or not context_order:
        raise ValueError(f"{path.name} display `{expected_display_id}` context_order must contain a non-empty list")
    normalized_context_order: list[dict[str, str]] = []
    seen_context_labels: set[str] = set()
    seen_context_kinds: set[str] = set()
    required_context_kinds = {"atlas_density", "spatial_coverage", "trajectory_coverage"}
    for index, item in enumerate(context_order):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` context_order[{index}] must be an object")
        context_label = _require_non_empty_string(
            item.get("label"),
            label=f"{path.name} display `{expected_display_id}` context_order[{index}].label",
        )
        if context_label in seen_context_labels:
            raise ValueError(f"{path.name} display `{expected_display_id}` context_order[{index}].label must be unique")
        seen_context_labels.add(context_label)
        context_kind = _require_non_empty_string(
            item.get("context_kind"),
            label=f"{path.name} display `{expected_display_id}` context_order[{index}].context_kind",
        )
        if context_kind not in required_context_kinds:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` context_order[{index}].context_kind must be one of atlas_density, spatial_coverage, trajectory_coverage"
            )
        if context_kind in seen_context_kinds:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` context_order[{index}].context_kind must be unique"
            )
        seen_context_kinds.add(context_kind)
        normalized_context_order.append({"label": context_label, "context_kind": context_kind})
    if seen_context_kinds != required_context_kinds:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` context_order must cover atlas_density, spatial_coverage, and trajectory_coverage exactly once"
        )

    support_cells = payload.get("support_cells")
    if not isinstance(support_cells, list) or not support_cells:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty support_cells list")
    normalized_support_cells: list[dict[str, Any]] = []
    observed_support_rows: set[str] = set()
    observed_support_columns: set[str] = set()
    observed_support_coordinates: set[tuple[str, str]] = set()
    for index, item in enumerate(support_cells):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` support_cells[{index}] must be an object")
        context_label = _require_non_empty_string(
            item.get("x"),
            label=f"{path.name} display `{expected_display_id}` support_cells[{index}].x",
        )
        state_label = _require_non_empty_string(
            item.get("y"),
            label=f"{path.name} display `{expected_display_id}` support_cells[{index}].y",
        )
        coordinate = (context_label, state_label)
        if coordinate in observed_support_coordinates:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` support_cells must cover the declared state-context grid exactly once"
            )
        observed_support_coordinates.add(coordinate)
        observed_support_columns.add(context_label)
        observed_support_rows.add(state_label)
        normalized_support_cells.append(
            {
                "x": context_label,
                "y": state_label,
                "value": _require_probability_value(
                    item.get("value"),
                    label=f"{path.name} display `{expected_display_id}` support_cells[{index}].value",
                ),
            }
        )

    declared_context_labels = {item["label"] for item in normalized_context_order}
    if observed_support_rows != declared_state_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_cells must cover the declared state-context grid exactly once"
        )
    if observed_support_columns != declared_context_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_cells must cover the declared state-context grid exactly once"
        )
    expected_coordinates = {(context["label"], state["label"]) for state in state_order for context in normalized_context_order}
    if observed_support_coordinates != expected_coordinates:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_cells must cover the declared state-context grid exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "atlas_panel_title": atlas_panel_title,
        "atlas_x_label": atlas_x_label,
        "atlas_y_label": atlas_y_label,
        "atlas_annotation": str(payload.get("atlas_annotation") or "").strip(),
        "atlas_points": normalized_atlas_points,
        "spatial_panel_title": spatial_panel_title,
        "spatial_x_label": spatial_x_label,
        "spatial_y_label": spatial_y_label,
        "spatial_annotation": str(payload.get("spatial_annotation") or "").strip(),
        "spatial_points": normalized_spatial_points,
        "trajectory_panel_title": trajectory_panel_title,
        "trajectory_x_label": trajectory_x_label,
        "trajectory_y_label": trajectory_y_label,
        "trajectory_annotation": str(payload.get("trajectory_annotation") or "").strip(),
        "trajectory_points": normalized_trajectory_points,
        "support_panel_title": support_panel_title,
        "support_x_label": support_x_label,
        "support_y_label": support_y_label,
        "support_scale_label": support_scale_label,
        "support_annotation": str(payload.get("support_annotation") or "").strip(),
        "state_order": state_order,
        "context_order": normalized_context_order,
        "support_cells": normalized_support_cells,
    }

def _validate_atlas_spatial_trajectory_context_support_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    storyboard_payload = _validate_atlas_spatial_trajectory_storyboard_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    support_payload = _validate_atlas_spatial_trajectory_density_coverage_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    return {
        **storyboard_payload,
        "support_panel_title": support_payload["support_panel_title"],
        "support_x_label": support_payload["support_x_label"],
        "support_y_label": support_payload["support_y_label"],
        "support_annotation": support_payload["support_annotation"],
        "support_scale_label": support_payload["support_scale_label"],
        "context_order": support_payload["context_order"],
        "support_cells": support_payload["support_cells"],
    }

def _validate_atlas_manifold_panels_payload(
    *,
    path: Path,
    payload: object,
    expected_display_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` atlas_manifold_panels must contain exactly two panels")
    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_methods: set[str] = set()
    allowed_methods = {"pca", "phate", "tsne", "umap"}
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}] must be an object")
        panel_id = _require_non_empty_string(
            item.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            item.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        manifold_method = _require_non_empty_string(
            item.get("manifold_method"),
            label=f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].manifold_method",
        ).lower()
        if manifold_method not in allowed_methods:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].manifold_method must be one of pca, phate, tsne, umap"
            )
        if manifold_method in seen_methods:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].manifold_method must be unique"
            )
        seen_methods.add(manifold_method)
        points = item.get("points")
        if not isinstance(points, list) or not points:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].points must contain a non-empty list"
            )
        normalized_points: list[dict[str, Any]] = []
        for point_index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].points[{point_index}] must be an object"
                )
            normalized_points.append(
                {
                    "x": _require_numeric_value(
                        point.get("x"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"atlas_manifold_panels[{index}].points[{point_index}].x"
                        ),
                    ),
                    "y": _require_numeric_value(
                        point.get("y"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"atlas_manifold_panels[{index}].points[{point_index}].y"
                        ),
                    ),
                    "state_label": _require_non_empty_string(
                        point.get("state_label"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"atlas_manifold_panels[{index}].points[{point_index}].state_label"
                        ),
                    ),
                }
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "panel_title": _require_non_empty_string(
                    item.get("panel_title"),
                    label=f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].panel_title",
                ),
                "manifold_method": manifold_method,
                "x_label": _require_non_empty_string(
                    item.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].x_label",
                ),
                "y_label": _require_non_empty_string(
                    item.get("y_label"),
                    label=f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{index}].y_label",
                ),
                "points": normalized_points,
            }
        )
    return normalized_panels

def _validate_atlas_spatial_trajectory_multimanifold_context_support_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    atlas_manifold_panels = _validate_atlas_manifold_panels_payload(
        path=path,
        payload=payload.get("atlas_manifold_panels"),
        expected_display_id=expected_display_id,
    )
    first_manifold_panel = atlas_manifold_panels[0]
    normalized_payload = _validate_atlas_spatial_trajectory_context_support_display_payload(
        path=path,
        payload={
            **payload,
            "atlas_panel_title": first_manifold_panel["panel_title"],
            "atlas_x_label": first_manifold_panel["x_label"],
            "atlas_y_label": first_manifold_panel["y_label"],
            "atlas_points": first_manifold_panel["points"],
        },
        expected_template_id=str(payload.get("template_id") or expected_template_id).strip(),
        expected_display_id=expected_display_id,
    )
    declared_state_labels = {item["label"] for item in normalized_payload["state_order"]}
    for panel_index, panel in enumerate(atlas_manifold_panels):
        observed_state_labels = {str(point["state_label"]) for point in panel["points"]}
        if observed_state_labels != declared_state_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` atlas_manifold_panels[{panel_index}].points state_label set must match state_order"
            )
    return {
        **normalized_payload,
        "atlas_manifold_panels": atlas_manifold_panels,
    }


__all__ = [
    "_validate_atlas_spatial_trajectory_storyboard_display_payload",
    "_validate_atlas_spatial_trajectory_density_coverage_display_payload",
    "_validate_atlas_spatial_trajectory_context_support_display_payload",
    "_validate_atlas_manifold_panels_payload",
    "_validate_atlas_spatial_trajectory_multimanifold_context_support_display_payload",
]
