from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_list, _require_numeric_value, math

def _validate_partial_dependence_interaction_slice_panel_display_payload(
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
    legend_title = _require_non_empty_string(
        payload.get("legend_title"),
        label=f"{path.name} display `{expected_display_id}` legend_title",
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
    expected_slice_labels: tuple[str, ...] | None = None
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
        slice_feature = _require_non_empty_string(
            panel_payload.get("slice_feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_feature",
        )
        feature_pair = (x_feature, slice_feature)
        if feature_pair in seen_feature_pairs:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] feature pair must be unique"
            )
        seen_feature_pairs.add(feature_pair)
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

        slice_curves_payload = panel_payload.get("slice_curves")
        if not isinstance(slice_curves_payload, list) or len(slice_curves_payload) < 2:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves must contain at least two entries"
            )
        normalized_slice_curves: list[dict[str, Any]] = []
        seen_slice_ids: set[str] = set()
        seen_slice_labels: set[str] = set()
        reference_x: list[float] | None = None
        ordered_slice_labels: list[str] = []
        for curve_index, curve_payload in enumerate(slice_curves_payload):
            if not isinstance(curve_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}] must be an object"
                )
            slice_id = _require_non_empty_string(
                curve_payload.get("slice_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].slice_id"
                ),
            )
            if slice_id in seen_slice_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].slice_id must be unique within the panel"
                )
            seen_slice_ids.add(slice_id)
            slice_label = _require_non_empty_string(
                curve_payload.get("slice_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].slice_label"
                ),
            )
            if slice_label in seen_slice_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].slice_label must be unique within the panel"
                )
            seen_slice_labels.add(slice_label)
            ordered_slice_labels.append(slice_label)
            conditioning_value = _require_numeric_value(
                curve_payload.get("conditioning_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].conditioning_value"
                ),
            )
            curve_x = _require_numeric_list(
                curve_payload.get("x"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].x"
                ),
            )
            curve_y = _require_numeric_list(
                curve_payload.get("y"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].slice_curves[{curve_index}].y"
                ),
            )
            if len(curve_x) != len(curve_y):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].x and y must have the same length"
                )
            if not all(math.isfinite(value) for value in (*curve_x, *curve_y)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}] values must be finite"
                )
            if any(right <= left for left, right in zip(curve_x, curve_x[1:], strict=False)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].x must be strictly increasing"
                )
            if reference_x is None:
                reference_x = curve_x
            elif len(curve_x) != len(reference_x) or any(
                not math.isclose(curve_value, reference_value_item, rel_tol=0.0, abs_tol=1e-9)
                for curve_value, reference_value_item in zip(curve_x, reference_x, strict=True)
            ):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].slice_curves[{curve_index}].x must match the first slice x grid within each panel"
                )
            normalized_slice_curves.append(
                {
                    "slice_id": slice_id,
                    "slice_label": slice_label,
                    "conditioning_value": conditioning_value,
                    "x": curve_x,
                    "y": curve_y,
                }
            )
        if reference_x is None or not (reference_x[0] <= reference_value <= reference_x[-1]):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must fall within slice_curve.x range"
            )
        if expected_slice_labels is None:
            expected_slice_labels = tuple(ordered_slice_labels)
        elif tuple(ordered_slice_labels) != expected_slice_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` slice_curves must keep the same ordered slice_label set across panels"
            )
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
                "x_feature": x_feature,
                "slice_feature": slice_feature,
                "reference_value": reference_value,
                "reference_label": reference_label,
                "slice_curves": normalized_slice_curves,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "legend_title": legend_title,
        "legend_labels": list(expected_slice_labels or ()),
        "panels": normalized_panels,
    }

def _validate_partial_dependence_subgroup_comparison_panel_display_payload(
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
    subgroup_panel_label = _require_non_empty_string(
        payload.get("subgroup_panel_label"),
        label=f"{path.name} display `{expected_display_id}` subgroup_panel_label",
    )
    subgroup_panel_title = _require_non_empty_string(
        payload.get("subgroup_panel_title"),
        label=f"{path.name} display `{expected_display_id}` subgroup_panel_title",
    )
    subgroup_x_label = _require_non_empty_string(
        payload.get("subgroup_x_label"),
        label=f"{path.name} display `{expected_display_id}` subgroup_x_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most three entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_subgroup_labels: set[str] = set()
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
        subgroup_label = _require_non_empty_string(
            panel_payload.get("subgroup_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].subgroup_label",
        )
        if subgroup_label in seen_subgroup_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].subgroup_label must be unique"
            )
        seen_subgroup_labels.add(subgroup_label)
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
                "subgroup_label": subgroup_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "feature": _require_non_empty_string(
                    panel_payload.get("feature"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature",
                ),
                "reference_value": reference_value,
                "reference_label": reference_label,
                "pdp_curve": {"x": pdp_x, "y": pdp_y},
                "ice_curves": normalized_ice_curves,
            }
        )

    if subgroup_panel_label in seen_panel_labels:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` subgroup_panel_label must be distinct from top-panel labels"
        )

    subgroup_rows_payload = payload.get("subgroup_rows")
    if not isinstance(subgroup_rows_payload, list) or not subgroup_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty subgroup_rows list")
    normalized_rows: list[dict[str, Any]] = []
    seen_row_ids: set[str] = set()
    seen_row_labels: set[str] = set()
    seen_row_panel_ids: set[str] = set()
    valid_panel_ids = {panel["panel_id"] for panel in normalized_panels}
    for row_index, row_payload in enumerate(subgroup_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] must be an object")
        row_id = _require_non_empty_string(
            row_payload.get("row_id"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].row_id",
        )
        if row_id in seen_row_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].row_id must be unique"
            )
        seen_row_ids.add(row_id)
        panel_id = _require_non_empty_string(
            row_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].panel_id",
        )
        if panel_id not in valid_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].panel_id must match one of the declared panels"
            )
        if panel_id in seen_row_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows must reference each panel_id at most once"
            )
        seen_row_panel_ids.add(panel_id)
        row_label = _require_non_empty_string(
            row_payload.get("row_label"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].row_label",
        )
        if row_label in seen_row_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].row_label must be unique"
            )
        seen_row_labels.add(row_label)
        estimate = _require_numeric_value(
            row_payload.get("estimate"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].estimate",
        )
        lower = _require_numeric_value(
            row_payload.get("lower"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].lower",
        )
        upper = _require_numeric_value(
            row_payload.get("upper"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].upper",
        )
        if not (lower <= estimate <= upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] must satisfy lower <= estimate <= upper"
            )
        support_n = _require_non_negative_int(
            row_payload.get("support_n"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].support_n",
            allow_zero=False,
        )
        normalized_rows.append(
            {
                "row_id": row_id,
                "panel_id": panel_id,
                "row_label": row_label,
                "estimate": estimate,
                "lower": lower,
                "upper": upper,
                "support_n": support_n,
            }
        )
    if seen_row_panel_ids != valid_panel_ids:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` subgroup_rows must reference every declared panel_id exactly once"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "legend_labels": ["ICE curves", "PDP mean", "Subgroup interval"],
        "subgroup_panel_label": subgroup_panel_label,
        "subgroup_panel_title": subgroup_panel_title,
        "subgroup_x_label": subgroup_x_label,
        "panels": normalized_panels,
        "subgroup_rows": normalized_rows,
    }

def _validate_accumulated_local_effects_panel_display_payload(
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

        ale_curve_payload = panel_payload.get("ale_curve")
        if not isinstance(ale_curve_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve must be an object"
            )
        ale_x = _require_numeric_list(
            ale_curve_payload.get("x"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.x",
        )
        ale_y = _require_numeric_list(
            ale_curve_payload.get("y"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.y",
        )
        if len(ale_x) != len(ale_y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.x and ale_curve.y must have the same length"
            )
        if not all(math.isfinite(value) for value in (*ale_x, *ale_y)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve values must be finite"
            )
        if any(right <= left for left, right in zip(ale_x, ale_x[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.x must be strictly increasing"
            )

        bins_payload = panel_payload.get("local_effect_bins")
        if not isinstance(bins_payload, list) or not bins_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins must be a non-empty list"
            )
        normalized_bins: list[dict[str, Any]] = []
        seen_bin_ids: set[str] = set()
        previous_right: float | None = None
        bin_centers: list[float] = []
        cumulative_values: list[float] = []
        running_total = 0.0
        for bin_index, bin_payload in enumerate(bins_payload):
            if not isinstance(bin_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}] must be an object"
                )
            bin_id = _require_non_empty_string(
                bin_payload.get("bin_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].bin_id"
                ),
            )
            if bin_id in seen_bin_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}].bin_id must be unique within the panel"
                )
            seen_bin_ids.add(bin_id)
            bin_left = _require_numeric_value(
                bin_payload.get("bin_left"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].bin_left"
                ),
            )
            bin_right = _require_numeric_value(
                bin_payload.get("bin_right"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].bin_right"
                ),
            )
            if previous_right is not None and bin_left < previous_right:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins must be strictly ordered and non-overlapping"
                )
            if bin_right <= bin_left:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}] must satisfy bin_left < bin_right"
                )
            previous_right = bin_right
            bin_center = _require_numeric_value(
                bin_payload.get("bin_center"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].bin_center"
                ),
            )
            if not (bin_left <= bin_center <= bin_right):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}].bin_center must fall within bin_left/bin_right"
                )
            local_effect = _require_numeric_value(
                bin_payload.get("local_effect"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].local_effect"
                ),
            )
            if not math.isfinite(local_effect):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].local_effect_bins[{bin_index}].local_effect must be finite"
                )
            support_count = _require_non_negative_int(
                bin_payload.get("support_count"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].local_effect_bins[{bin_index}].support_count"
                ),
                allow_zero=False,
            )
            running_total += local_effect
            cumulative_values.append(running_total)
            bin_centers.append(bin_center)
            normalized_bins.append(
                {
                    "bin_id": bin_id,
                    "bin_left": bin_left,
                    "bin_right": bin_right,
                    "bin_center": bin_center,
                    "local_effect": local_effect,
                    "support_count": support_count,
                }
            )
        if len(bin_centers) != len(ale_x) or any(
            not math.isclose(x_value, center_value, rel_tol=0.0, abs_tol=1e-9)
            for x_value, center_value in zip(ale_x, bin_centers, strict=True)
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.x must match local_effect_bins.bin_center"
            )
        if any(
            not math.isclose(curve_value, cumulative_value, rel_tol=1e-9, abs_tol=1e-9)
            for curve_value, cumulative_value in zip(ale_y, cumulative_values, strict=True)
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].ale_curve.y must equal the cumulative sum of local_effect_bins within each panel"
            )
        if reference_value < normalized_bins[0]["bin_left"] or reference_value > normalized_bins[-1]["bin_right"]:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].reference_value must fall within local_effect_bins range"
            )
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
                "ale_curve": {"x": ale_x, "y": ale_y},
                "local_effect_bins": normalized_bins,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "legend_labels": ["Accumulated local effect", "Local effect per bin"],
        "panels": normalized_panels,
    }


__all__ = [
    "_validate_partial_dependence_interaction_slice_panel_display_payload",
    "_validate_partial_dependence_subgroup_comparison_panel_display_payload",
    "_validate_accumulated_local_effects_panel_display_payload",
]
