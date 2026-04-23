from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, _require_probability_value
from .validation_tables import _validate_labeled_order_payload

def _validate_spatial_niche_map_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
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

    spatial_points = payload.get("spatial_points")
    if not isinstance(spatial_points, list) or not spatial_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty spatial_points list")
    normalized_spatial_points: list[dict[str, Any]] = []
    observed_niches: set[str] = set()
    for index, item in enumerate(spatial_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` spatial_points[{index}] must be an object")
        niche_label = _require_non_empty_string(
            item.get("niche_label"),
            label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].niche_label",
        )
        observed_niches.add(niche_label)
        normalized_point = {
            "x": _require_numeric_value(
                item.get("x"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].x",
            ),
            "y": _require_numeric_value(
                item.get("y"),
                label=f"{path.name} display `{expected_display_id}` spatial_points[{index}].y",
            ),
            "niche_label": niche_label,
        }
        region_label = str(item.get("region_label") or "").strip()
        if region_label:
            normalized_point["region_label"] = region_label
        normalized_spatial_points.append(normalized_point)

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
    if observed_niches != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match spatial point niche labels"
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
        niche_proportions = item.get("niche_proportions")
        if not isinstance(niche_proportions, list) or not niche_proportions:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}].niche_proportions must be non-empty"
            )
        normalized_niche_proportions: list[dict[str, Any]] = []
        seen_niche_labels: set[str] = set()
        proportion_sum = 0.0
        for niche_index, niche_item in enumerate(niche_proportions):
            if not isinstance(niche_item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}].niche_proportions[{niche_index}] must be an object"
                )
            niche_label = _require_non_empty_string(
                niche_item.get("niche_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"niche_proportions[{niche_index}].niche_label"
                ),
            )
            if niche_label in seen_niche_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared niche labels exactly once"
                )
            seen_niche_labels.add(niche_label)
            proportion = _require_probability_value(
                niche_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` composition_groups[{index}]."
                    f"niche_proportions[{niche_index}].proportion"
                ),
            )
            proportion_sum += proportion
            normalized_niche_proportions.append({"niche_label": niche_label, "proportion": proportion})
        if seen_niche_labels != declared_columns:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] must cover the declared niche labels exactly once"
            )
        if abs(proportion_sum - 1.0) > 1e-6:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` composition_groups[{index}] proportions must sum to 1"
            )
        normalized_composition_groups.append(
            {
                "group_label": group_label,
                "group_order": group_order,
                "niche_proportions": normalized_niche_proportions,
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
        raise ValueError(f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "spatial_panel_title": spatial_panel_title,
        "spatial_x_label": spatial_x_label,
        "spatial_y_label": spatial_y_label,
        "spatial_annotation": str(payload.get("spatial_annotation") or "").strip(),
        "spatial_points": normalized_spatial_points,
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
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }

def _validate_trajectory_progression_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
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

    trajectory_points = payload.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty trajectory_points list")
    normalized_trajectory_points: list[dict[str, Any]] = []
    observed_branches: set[str] = set()
    for index, item in enumerate(trajectory_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` trajectory_points[{index}] must be an object")
        branch_label = _require_non_empty_string(
            item.get("branch_label"),
            label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].branch_label",
        )
        observed_branches.add(branch_label)
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
                "state_label": _require_non_empty_string(
                    item.get("state_label"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].state_label",
                ),
                "pseudotime": _require_probability_value(
                    item.get("pseudotime"),
                    label=f"{path.name} display `{expected_display_id}` trajectory_points[{index}].pseudotime",
                ),
            }
        )

    branch_order = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("branch_order"),
        label=f"display `{expected_display_id}` branch_order",
    )
    declared_branch_labels = {item["label"] for item in branch_order}
    if observed_branches != declared_branch_labels:
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
        seen_branch_labels: set[str] = set()
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
            if branch_label in seen_branch_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}] must cover the declared branch labels exactly once"
                )
            seen_branch_labels.add(branch_label)
            proportion = _require_probability_value(
                branch_item.get("proportion"),
                label=(
                    f"{path.name} display `{expected_display_id}` progression_bins[{index}]."
                    f"branch_weights[{branch_index}].proportion"
                ),
            )
            weight_sum += proportion
            normalized_branch_weights.append({"branch_label": branch_label, "proportion": proportion})
        if seen_branch_labels != declared_branch_labels:
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
        "trajectory_panel_title": trajectory_panel_title,
        "trajectory_x_label": trajectory_x_label,
        "trajectory_y_label": trajectory_y_label,
        "trajectory_annotation": str(payload.get("trajectory_annotation") or "").strip(),
        "trajectory_points": normalized_trajectory_points,
        "composition_panel_title": composition_panel_title,
        "composition_x_label": composition_x_label,
        "composition_y_label": composition_y_label,
        "composition_annotation": str(payload.get("composition_annotation") or "").strip(),
        "branch_order": branch_order,
        "progression_bins": normalized_progression_bins,
        "heatmap_panel_title": heatmap_panel_title,
        "heatmap_x_label": heatmap_x_label,
        "heatmap_y_label": heatmap_y_label,
        "heatmap_annotation": str(payload.get("heatmap_annotation") or "").strip(),
        "score_method": _require_non_empty_string(
            payload.get("score_method"),
            label=f"{path.name} display `{expected_display_id}` score_method",
        ),
        "row_order": row_order,
        "column_order": column_order,
        "cells": normalized_cells,
    }


__all__ = [
    "_validate_spatial_niche_map_display_payload",
    "_validate_trajectory_progression_display_payload",
]
