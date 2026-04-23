from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_numeric_list, _require_numeric_value, math

def _validate_partial_dependence_ice_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most three entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_features: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        feature = _require_non_empty_string(
            panel_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature must be unique"
            )
        seen_features.add(feature)
        reference_value = _require_numeric_value(
            panel_payload.get("reference_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value",
        )
        if not math.isfinite(reference_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must be finite"
            )
        reference_label = _require_non_empty_string(
            panel_payload.get("reference_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_label",
        )

        pdp_curve_payload = panel_payload.get("pdp_curve")
        if not isinstance(pdp_curve_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve must be an object"
            )
        pdp_x = _require_numeric_list(
            pdp_curve_payload.get("x"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.x",
        )
        pdp_y = _require_numeric_list(
            pdp_curve_payload.get("y"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.y",
        )
        if len(pdp_x) != len(pdp_y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.x and pdp_curve.y must have the same length"
            )
        if not all(math.isfinite(value) for value in (*pdp_x, *pdp_y)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve values must be finite"
            )
        if any(right <= left for left, right in zip(pdp_x, pdp_x[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].pdp_curve.x must be strictly increasing"
            )
        if reference_value < pdp_x[0] or reference_value > pdp_x[-1]:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must fall within pdp_curve.x range"
            )

        ice_curves_payload = panel_payload.get("ice_curves")
        if not isinstance(ice_curves_payload, list) or not ice_curves_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves must be a non-empty list"
            )
        normalized_ice_curves: list[dict[str, Any]] = []
        seen_curve_ids: set[str] = set()
        for curve_index, curve_payload in enumerate(ice_curves_payload):
            if not isinstance(curve_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}] must be an object"
                )
            curve_id = _require_non_empty_string(
                curve_payload.get("curve_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].ice_curves[{curve_index}].curve_id"
                ),
            )
            if curve_id in seen_curve_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}].curve_id must be unique within the panel"
                )
            seen_curve_ids.add(curve_id)
            curve_x = _require_numeric_list(
                curve_payload.get("x"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].ice_curves[{curve_index}].x"
                ),
            )
            curve_y = _require_numeric_list(
                curve_payload.get("y"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].ice_curves[{curve_index}].y"
                ),
            )
            if len(curve_x) != len(curve_y):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}].x and y must have the same length"
                )
            if not all(math.isfinite(value) for value in (*curve_x, *curve_y)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}] values must be finite"
                )
            if len(curve_x) != len(pdp_x) or any(
                not math.isclose(curve_value, pdp_value, rel_tol=0.0, abs_tol=1e-9)
                for curve_value, pdp_value in zip(curve_x, pdp_x, strict=True)
            ):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].ice_curves[{curve_index}].x must match pdp_curve.x within each panel"
                )
            normalized_ice_curves.append({"curve_id": curve_id, "x": curve_x, "y": curve_y})

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "feature": feature,
                "reference_value": reference_value,
                "reference_label": reference_label,
                "pdp_curve": {"x": pdp_x, "y": pdp_y},
                "ice_curves": normalized_ice_curves,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "panels": normalized_panels,
    }

def _validate_partial_dependence_interaction_contour_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    colorbar_label = _require_non_empty_string(
        payload.get("colorbar_label"),
        label=f"{path.name} display `{expected_display_id}` colorbar_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most two entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_feature_pairs: set[tuple[str, str]] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        x_feature = _require_non_empty_string(
            panel_payload.get("x_feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_feature",
        )
        y_feature = _require_non_empty_string(
            panel_payload.get("y_feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].y_feature",
        )
        feature_pair = (x_feature, y_feature)
        if feature_pair in seen_feature_pairs:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] feature pair must be unique"
            )
        seen_feature_pairs.add(feature_pair)
        reference_x_value = _require_numeric_value(
            panel_payload.get("reference_x_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_x_value",
        )
        reference_y_value = _require_numeric_value(
            panel_payload.get("reference_y_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_y_value",
        )
        if not math.isfinite(reference_x_value) or not math.isfinite(reference_y_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] reference values must be finite"
            )
        reference_label = _require_non_empty_string(
            panel_payload.get("reference_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_label",
        )
        x_grid = _require_numeric_list(
            panel_payload.get("x_grid"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_grid",
        )
        y_grid = _require_numeric_list(
            panel_payload.get("y_grid"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].y_grid",
        )
        if any(right <= left for left, right in zip(x_grid, x_grid[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_grid must be strictly increasing"
            )
        if any(right <= left for left, right in zip(y_grid, y_grid[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].y_grid must be strictly increasing"
            )

        response_grid_payload = panel_payload.get("response_grid")
        if not isinstance(response_grid_payload, list) or len(response_grid_payload) != len(y_grid):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].response_grid must match y_grid length"
            )
        normalized_response_grid: list[list[float]] = []
        for row_index, row_payload in enumerate(response_grid_payload):
            if not isinstance(row_payload, list) or len(row_payload) != len(x_grid):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].response_grid[{row_index}] must match x_grid length"
                )
            row_values = [
                _require_numeric_value(
                    value,
                    label=(
                        f"{path.name} display `{expected_display_id}` "
                        f"panels[{panel_index}].response_grid[{row_index}]"
                    ),
                )
                for value in row_payload
            ]
            if not all(math.isfinite(value) for value in row_values):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].response_grid[{row_index}] must be finite"
                )
            normalized_response_grid.append(row_values)

        if not (x_grid[0] <= reference_x_value <= x_grid[-1]):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_x_value must fall within x_grid range"
            )
        if not (y_grid[0] <= reference_y_value <= y_grid[-1]):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_y_value must fall within y_grid range"
            )

        observed_points_payload = panel_payload.get("observed_points")
        if not isinstance(observed_points_payload, list) or not observed_points_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points must be a non-empty list"
            )
        normalized_observed_points: list[dict[str, Any]] = []
        seen_point_ids: set[str] = set()
        for point_index, point_payload in enumerate(observed_points_payload):
            if not isinstance(point_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points[{point_index}] must be an object"
                )
            point_id = _require_non_empty_string(
                point_payload.get("point_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].observed_points[{point_index}].point_id"
                ),
            )
            if point_id in seen_point_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points[{point_index}].point_id must be unique within the panel"
                )
            seen_point_ids.add(point_id)
            point_x = _require_numeric_value(
                point_payload.get("x"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].observed_points[{point_index}].x"
                ),
            )
            point_y = _require_numeric_value(
                point_payload.get("y"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].observed_points[{point_index}].y"
                ),
            )
            if not math.isfinite(point_x) or not math.isfinite(point_y):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points[{point_index}] must be finite"
                )
            if not (x_grid[0] <= point_x <= x_grid[-1]) or not (y_grid[0] <= point_y <= y_grid[-1]):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].observed_points[{point_index}] must fall within declared grid range"
                )
            normalized_observed_points.append({"point_id": point_id, "x": point_x, "y": point_y})

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "y_label": _require_non_empty_string(
                    panel_payload.get("y_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].y_label",
                ),
                "x_feature": x_feature,
                "y_feature": y_feature,
                "reference_x_value": reference_x_value,
                "reference_y_value": reference_y_value,
                "reference_label": reference_label,
                "x_grid": x_grid,
                "y_grid": y_grid,
                "response_grid": normalized_response_grid,
                "observed_points": normalized_observed_points,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "colorbar_label": colorbar_label,
        "panels": normalized_panels,
    }


__all__ = [
    "_validate_partial_dependence_ice_panel_display_payload",
    "_validate_partial_dependence_interaction_contour_panel_display_payload",
]
