from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_numeric_value
from .validation_tables import _validate_labeled_order_payload


def _require_template(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> tuple[str, str]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    return title, str(payload.get("caption") or "").strip()


def _optional_label_order(*, path: Path, payload: dict[str, Any], key: str, label: str) -> list[dict[str, str]]:
    value = payload.get(key)
    if value is None:
        return []
    return _validate_labeled_order_payload(path=path, payload=value, label=label)


def _validate_distribution_violin_box_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    title, caption = _require_template(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    values = payload.get("values")
    if not isinstance(values, list) or len(values) < 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain at least two values")
    normalized_values: list[dict[str, Any]] = []
    groups: set[str] = set()
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` values[{index}] must be an object")
        group = _require_non_empty_string(
            item.get("group"),
            label=f"{path.name} display `{expected_display_id}` values[{index}].group",
        )
        groups.add(group)
        normalized_values.append(
            {
                "group": group,
                "value": _require_numeric_value(
                    item.get("value"),
                    label=f"{path.name} display `{expected_display_id}` values[{index}].value",
                ),
            }
        )
    if len(groups) < 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain at least two groups")
    group_order = _optional_label_order(
        path=path,
        payload=payload,
        key="group_order",
        label=f"display `{expected_display_id}` group_order",
    )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": str(payload.get("x_label") or "").strip(),
        "y_label": y_label,
        "annotation": str(payload.get("annotation") or "").strip(),
        "group_order": group_order,
        "values": normalized_values,
    }


def _validate_composition_stacked_bar_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    title, caption = _require_template(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    segments = payload.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty segments list")
    normalized_segments: list[dict[str, Any]] = []
    for index, item in enumerate(segments):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` segments[{index}] must be an object")
        value = _require_numeric_value(
            item.get("value"),
            label=f"{path.name} display `{expected_display_id}` segments[{index}].value",
        )
        if value < 0:
            raise ValueError(f"{path.name} display `{expected_display_id}` segments[{index}].value must be non-negative")
        normalized_segments.append(
            {
                "group": _require_non_empty_string(
                    item.get("group"),
                    label=f"{path.name} display `{expected_display_id}` segments[{index}].group",
                ),
                "category": _require_non_empty_string(
                    item.get("category"),
                    label=f"{path.name} display `{expected_display_id}` segments[{index}].category",
                ),
                "value": value,
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": str(payload.get("x_label") or "").strip(),
        "y_label": _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label"),
        "group_order": _optional_label_order(path=path, payload=payload, key="group_order", label=f"display `{expected_display_id}` group_order"),
        "category_order": _optional_label_order(path=path, payload=payload, key="category_order", label=f"display `{expected_display_id}` category_order"),
        "segments": normalized_segments,
    }


def _validate_correlation_scatter_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    title, caption = _require_template(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    points = payload.get("points")
    if not isinstance(points, list) or len(points) < 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain at least three points")
    normalized_points: list[dict[str, Any]] = []
    for index, item in enumerate(points):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` points[{index}] must be an object")
        normalized_points.append(
            {
                "x": _require_numeric_value(item.get("x"), label=f"{path.name} display `{expected_display_id}` points[{index}].x"),
                "y": _require_numeric_value(item.get("y"), label=f"{path.name} display `{expected_display_id}` points[{index}].y"),
                "group": str(item.get("group") or "All").strip() or "All",
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label"),
        "y_label": _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label"),
        "annotation": str(payload.get("annotation") or "").strip(),
        "points": normalized_points,
    }


def _validate_alluvial_transition_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    title, caption = _require_template(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    flows = payload.get("flows")
    if not isinstance(flows, list) or not flows:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty flows list")
    normalized_flows: list[dict[str, Any]] = []
    for index, item in enumerate(flows):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` flows[{index}] must be an object")
        value = _require_numeric_value(item.get("value"), label=f"{path.name} display `{expected_display_id}` flows[{index}].value")
        if value <= 0:
            raise ValueError(f"{path.name} display `{expected_display_id}` flows[{index}].value must be positive")
        normalized_flows.append(
            {
                "source": _require_non_empty_string(item.get("source"), label=f"{path.name} display `{expected_display_id}` flows[{index}].source"),
                "target": _require_non_empty_string(item.get("target"), label=f"{path.name} display `{expected_display_id}` flows[{index}].target"),
                "value": value,
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "source_axis_label": str(payload.get("source_axis_label") or "").strip(),
        "target_axis_label": str(payload.get("target_axis_label") or "").strip(),
        "flows": normalized_flows,
    }


def _validate_radar_profile_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    title, caption = _require_template(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    axes = _validate_labeled_order_payload(
        path=path,
        payload=payload.get("axes"),
        label=f"display `{expected_display_id}` axes",
    )
    if len(axes) < 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` axes must contain at least three labels")
    profiles = payload.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty profiles list")
    normalized_profiles: list[dict[str, Any]] = []
    for profile_index, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` profiles[{profile_index}] must be an object")
        values = profile.get("values")
        if not isinstance(values, list) or len(values) != len(axes):
            raise ValueError(f"{path.name} display `{expected_display_id}` profiles[{profile_index}].values must match axes length")
        normalized_profiles.append(
            {
                "label": _require_non_empty_string(
                    profile.get("label"),
                    label=f"{path.name} display `{expected_display_id}` profiles[{profile_index}].label",
                ),
                "values": [
                    _require_numeric_value(value, label=f"{path.name} display `{expected_display_id}` profiles[{profile_index}].values[{value_index}]")
                    for value_index, value in enumerate(values)
                ],
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "axes": axes,
        "profiles": normalized_profiles,
    }


def _validate_waterfall_response_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    title, caption = _require_template(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    bars = payload.get("bars")
    if not isinstance(bars, list) or not bars:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty bars list")
    normalized_bars: list[dict[str, Any]] = []
    for index, item in enumerate(bars):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` bars[{index}] must be an object")
        normalized_bars.append(
            {
                "sample": _require_non_empty_string(item.get("sample"), label=f"{path.name} display `{expected_display_id}` bars[{index}].sample"),
                "value": _require_numeric_value(item.get("value"), label=f"{path.name} display `{expected_display_id}` bars[{index}].value"),
                "response": _require_non_empty_string(item.get("response"), label=f"{path.name} display `{expected_display_id}` bars[{index}].response"),
            }
        )
    thresholds = payload.get("thresholds") or []
    if not isinstance(thresholds, list):
        raise ValueError(f"{path.name} display `{expected_display_id}` thresholds must be a list when provided")
    normalized_thresholds: list[dict[str, Any]] = []
    for index, item in enumerate(thresholds):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` thresholds[{index}] must be an object")
        normalized_thresholds.append(
            {
                "label": str(item.get("label") or "").strip(),
                "value": _require_numeric_value(item.get("value"), label=f"{path.name} display `{expected_display_id}` thresholds[{index}].value"),
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": str(payload.get("x_label") or "").strip(),
        "y_label": _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label"),
        "bars": normalized_bars,
        "thresholds": normalized_thresholds,
    }

