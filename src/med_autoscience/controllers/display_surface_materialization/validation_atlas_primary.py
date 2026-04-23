from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, _require_probability_value
from .validation_tables import _validate_labeled_order_payload

def _validate_embedding_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    points = payload.get("points")
    if not isinstance(points, list) or not points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty points list")
    normalized_points: list[dict[str, Any]] = []
    for index, item in enumerate(points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}] must be an object")
        normalized_points.append(
            {
                "x": _require_numeric_value(item.get("x"), label=f"{path.name} display `{expected_display_id}` points[{index}].x"),
                "y": _require_numeric_value(item.get("y"), label=f"{path.name} display `{expected_display_id}` points[{index}].y"),
                "group": _require_non_empty_string(
                    item.get("group"),
                    label=f"{path.name} display `{expected_display_id}` points[{index}].group",
                ),
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "points": normalized_points,
    }

def _validate_celltype_signature_heatmap_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    embedding_panel_title = _require_non_empty_string(
        payload.get("embedding_panel_title"),
        label=f"{path.name} display `{expected_display_id}` embedding_panel_title",
    )
    embedding_x_label = _require_non_empty_string(
        payload.get("embedding_x_label"),
        label=f"{path.name} display `{expected_display_id}` embedding_x_label",
    )
    embedding_y_label = _require_non_empty_string(
        payload.get("embedding_y_label"),
        label=f"{path.name} display `{expected_display_id}` embedding_y_label",
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
    embedding_points = payload.get("embedding_points")
    if not isinstance(embedding_points, list) or not embedding_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty embedding_points list")
    normalized_embedding_points: list[dict[str, Any]] = []
    observed_groups: set[str] = set()
    for index, item in enumerate(embedding_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` embedding_points[{index}] must be an object")
        group_label = _require_non_empty_string(
            item.get("group"),
            label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].group",
        )
        observed_groups.add(group_label)
        normalized_embedding_points.append(
            {
                "x": _require_numeric_value(
                    item.get("x"),
                    label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].x",
                ),
                "y": _require_numeric_value(
                    item.get("y"),
                    label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].y",
                ),
                "group": group_label,
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
    declared_columns = {item["label"] for item in column_order}
    if observed_rows != declared_rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` row_order labels must match cell y labels")
    if observed_columns != declared_columns:
        raise ValueError(f"{path.name} display `{expected_display_id}` column_order labels must match cell x labels")
    if observed_groups != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match embedding point groups"
        )
    expected_coordinates = {(column["label"], row["label"]) for row in row_order for column in column_order}
    if observed_coordinates != expected_coordinates:
        raise ValueError(f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "embedding_panel_title": embedding_panel_title,
        "embedding_x_label": embedding_x_label,
        "embedding_y_label": embedding_y_label,
        "embedding_annotation": str(payload.get("embedding_annotation") or "").strip(),
        "embedding_points": normalized_embedding_points,
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

def _validate_single_cell_atlas_overview_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    embedding_panel_title = _require_non_empty_string(
        payload.get("embedding_panel_title"),
        label=f"{path.name} display `{expected_display_id}` embedding_panel_title",
    )
    embedding_x_label = _require_non_empty_string(
        payload.get("embedding_x_label"),
        label=f"{path.name} display `{expected_display_id}` embedding_x_label",
    )
    embedding_y_label = _require_non_empty_string(
        payload.get("embedding_y_label"),
        label=f"{path.name} display `{expected_display_id}` embedding_y_label",
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

    embedding_points = payload.get("embedding_points")
    if not isinstance(embedding_points, list) or not embedding_points:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty embedding_points list")
    normalized_embedding_points: list[dict[str, Any]] = []
    observed_states: set[str] = set()
    for index, item in enumerate(embedding_points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` embedding_points[{index}] must be an object")
        state_label = _require_non_empty_string(
            item.get("state_label"),
            label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].state_label",
        )
        observed_states.add(state_label)
        normalized_point = {
            "x": _require_numeric_value(
                item.get("x"),
                label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].x",
            ),
            "y": _require_numeric_value(
                item.get("y"),
                label=f"{path.name} display `{expected_display_id}` embedding_points[{index}].y",
            ),
            "state_label": state_label,
        }
        group_label = str(item.get("group_label") or "").strip()
        if group_label:
            normalized_point["group_label"] = group_label
        normalized_embedding_points.append(normalized_point)

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
    if observed_states != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match embedding point state labels"
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
        if seen_state_labels != declared_columns:
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
        raise ValueError(f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once")

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "embedding_panel_title": embedding_panel_title,
        "embedding_x_label": embedding_x_label,
        "embedding_y_label": embedding_y_label,
        "embedding_annotation": str(payload.get("embedding_annotation") or "").strip(),
        "embedding_points": normalized_embedding_points,
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

def _validate_atlas_spatial_bridge_display_payload(
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
        normalized_point = {
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
        group_label = str(item.get("group_label") or "").strip()
        if group_label:
            normalized_point["group_label"] = group_label
        normalized_atlas_points.append(normalized_point)

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
    if observed_atlas_states != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match atlas point state labels"
        )
    if observed_spatial_states != declared_columns:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` column_order labels must match spatial point state labels"
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
        if seen_state_labels != declared_columns:
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
        raise ValueError(f"{path.name} display `{expected_display_id}` must cover every declared row/column coordinate exactly once")

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


__all__ = [
    "_validate_embedding_display_payload",
    "_validate_celltype_signature_heatmap_display_payload",
    "_validate_single_cell_atlas_overview_display_payload",
    "_validate_atlas_spatial_bridge_display_payload",
]
