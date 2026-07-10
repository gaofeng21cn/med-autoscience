from __future__ import annotations

from .shared import (
    Any,
    Path,
    _require_non_empty_string,
    _require_non_negative_int,
    _require_probability_value,
)


def _require_optional_probability_value(value: object, *, label: str) -> float | None:
    if value is None:
        return None
    return _require_probability_value(value, label=label)


def _normalize_common_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    template_id = _require_non_empty_string(
        payload.get("template_id"),
        label=f"{path.name} display `{expected_display_id}` template_id",
    )
    if template_id != expected_template_id:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must declare template_id `{expected_template_id}`"
        )
    display_id = _require_non_empty_string(payload.get("display_id"), label=f"{path.name} display_id")
    if display_id != expected_display_id:
        raise ValueError(f"{path.name} display_id must equal `{expected_display_id}`")

    normalized: dict[str, Any] = {"display_id": display_id, "template_id": template_id}
    for key in (
        "title",
        "composition_panel_title",
        "composition_axis_label",
        "heatmap_panel_title",
        "transition_panel_title",
        "support_panel_title",
        "source_axis_label",
        "target_axis_label",
        "support_axis_label",
        "x_label",
        "y_label",
        "annotation",
        "heatmap_scale_label",
    ):
        value = str(payload.get(key) or "").strip()
        if value:
            normalized[key] = value
    render_context = payload.get("render_context")
    if isinstance(render_context, dict):
        normalized["render_context"] = render_context
    return normalized


def _require_object_list(value: object, *, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{label}[{index}] must be an object")
        normalized.append(item)
    return normalized


def _normalize_metric_definitions(*, path: Path, payload: dict[str, Any]) -> list[dict[str, str]]:
    definitions = _require_object_list(
        payload.get("metric_definitions"),
        label=f"{path.name} metric_definitions",
    )
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(definitions):
        metric_id = _require_non_empty_string(
            item.get("metric_id"),
            label=f"{path.name} metric_definitions[{index}].metric_id",
        )
        if metric_id in seen:
            raise ValueError(f"{path.name} metric_definitions contains duplicate metric_id `{metric_id}`")
        seen.add(metric_id)
        normalized.append(
            {
                "metric_id": metric_id,
                "metric_label": _require_non_empty_string(
                    item.get("metric_label"),
                    label=f"{path.name} metric_definitions[{index}].metric_label",
                ),
            }
        )
    return normalized


def _normalize_row_metrics(
    *,
    path: Path,
    metrics: object,
    metric_ids: tuple[str, ...],
    row_index: int,
    burden: bool,
    group_size: int | None = None,
) -> list[dict[str, Any]]:
    raw_metrics = _require_object_list(metrics, label=f"{path.name} rows[{row_index}].metrics")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for metric_index, item in enumerate(raw_metrics):
        metric_id = _require_non_empty_string(
            item.get("metric_id"),
            label=f"{path.name} rows[{row_index}].metrics[{metric_index}].metric_id",
        )
        if metric_id in seen:
            raise ValueError(f"{path.name} rows[{row_index}] contains duplicate metric_id `{metric_id}`")
        if metric_id not in metric_ids:
            raise ValueError(f"{path.name} rows[{row_index}] contains undeclared metric_id `{metric_id}`")
        seen.add(metric_id)
        if not burden:
            normalized.append(
                {
                    "metric_id": metric_id,
                    "value": _require_optional_probability_value(
                        item.get("value"),
                        label=f"{path.name} rows[{row_index}].metrics[{metric_index}].value",
                    ),
                }
            )
            continue

        event_count = _require_non_negative_int(
            item.get("event_count"),
            label=f"{path.name} rows[{row_index}].metrics[{metric_index}].event_count",
        )
        denominator = _require_non_negative_int(
            item.get("denominator"),
            label=f"{path.name} rows[{row_index}].metrics[{metric_index}].denominator",
            allow_zero=False,
        )
        if event_count > denominator:
            raise ValueError(f"{path.name} rows[{row_index}] event_count must not exceed denominator")
        if group_size is not None and denominator > group_size:
            raise ValueError(f"{path.name} rows[{row_index}] denominator must not exceed group_size")
        metric: dict[str, Any] = {
            "metric_id": metric_id,
            "event_count": event_count,
            "denominator": denominator,
        }
        if "rate" in item:
            rate = _require_probability_value(
                item.get("rate"),
                label=f"{path.name} rows[{row_index}].metrics[{metric_index}].rate",
            )
            expected_rate = event_count / denominator
            if abs(rate - expected_rate) > 1e-6:
                raise ValueError(f"{path.name} rows[{row_index}] rate must equal event_count/denominator")
            metric["rate"] = rate
        normalized.append(metric)
    missing = sorted(set(metric_ids) - seen)
    if missing:
        raise ValueError(f"{path.name} rows[{row_index}] missing declared metrics: {', '.join(missing)}")
    return normalized


def _validate_stratified_mismatch_matrix_display_payload(
    *, path: Path, payload: dict[str, Any], expected_template_id: str, expected_display_id: str
) -> dict[str, Any]:
    normalized = _normalize_common_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    definitions = _normalize_metric_definitions(path=path, payload=payload)
    metric_ids = tuple(item["metric_id"] for item in definitions)
    rows = _require_object_list(payload.get("rows"), label=f"{path.name} rows")
    normalized["metric_definitions"] = definitions
    normalized["rows"] = [
        {
            "group_label": _require_non_empty_string(
                row.get("group_label"), label=f"{path.name} rows[{index}].group_label"
            ),
            "group_share": _require_probability_value(
                row.get("group_share"), label=f"{path.name} rows[{index}].group_share"
            ),
            "metrics": _normalize_row_metrics(
                path=path,
                metrics=row.get("metrics"),
                metric_ids=metric_ids,
                row_index=index,
                burden=False,
            ),
        }
        for index, row in enumerate(rows)
    ]
    return normalized


def _validate_transition_support_matrix_display_payload(
    *, path: Path, payload: dict[str, Any], expected_template_id: str, expected_display_id: str
) -> dict[str, Any]:
    normalized = _normalize_common_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    transition_rows = _require_object_list(payload.get("transition_rows"), label=f"{path.name} transition_rows")
    support_rows = _require_object_list(payload.get("support_rows"), label=f"{path.name} support_rows")
    normalized["transition_rows"] = [
        {
            "source_group_label": _require_non_empty_string(
                row.get("source_group_label"), label=f"{path.name} transition_rows[{index}].source_group_label"
            ),
            "target_group_label": _require_non_empty_string(
                row.get("target_group_label"), label=f"{path.name} transition_rows[{index}].target_group_label"
            ),
            "unit_count": _require_non_negative_int(
                row.get("unit_count"), label=f"{path.name} transition_rows[{index}].unit_count"
            ),
            "transition_share": _require_probability_value(
                row.get("transition_share"), label=f"{path.name} transition_rows[{index}].transition_share"
            ),
        }
        for index, row in enumerate(transition_rows)
    ]
    normalized["support_rows"] = [
        {
            "support_label": _require_non_empty_string(
                row.get("support_label"), label=f"{path.name} support_rows[{index}].support_label"
            ),
            "unit_count": _require_non_negative_int(
                row.get("unit_count"), label=f"{path.name} support_rows[{index}].unit_count"
            ),
            "support_share": _require_probability_value(
                row.get("support_share"), label=f"{path.name} support_rows[{index}].support_share"
            ),
        }
        for index, row in enumerate(support_rows)
    ]
    return normalized


def _validate_stratified_mismatch_burden_display_payload(
    *, path: Path, payload: dict[str, Any], expected_template_id: str, expected_display_id: str
) -> dict[str, Any]:
    normalized = _normalize_common_display_payload(
        path=path,
        payload=payload,
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    definitions = _normalize_metric_definitions(path=path, payload=payload)
    if len(definitions) > 4:
        raise ValueError(f"{path.name} supports at most four mismatch metrics")
    metric_ids = tuple(item["metric_id"] for item in definitions)
    rows = _require_object_list(payload.get("rows"), label=f"{path.name} rows")
    normalized["metric_definitions"] = definitions
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        group_size = _require_non_negative_int(
            row.get("group_size"), label=f"{path.name} rows[{index}].group_size", allow_zero=False
        )
        normalized_rows.append(
            {
                "group_label": _require_non_empty_string(
                    row.get("group_label"), label=f"{path.name} rows[{index}].group_label"
                ),
                "group_size": group_size,
                "metrics": _normalize_row_metrics(
                    path=path,
                    metrics=row.get("metrics"),
                    metric_ids=metric_ids,
                    row_index=index,
                    burden=True,
                    group_size=group_size,
                ),
            }
        )
    normalized["rows"] = normalized_rows
    return normalized


__all__ = [
    "_validate_stratified_mismatch_matrix_display_payload",
    "_validate_transition_support_matrix_display_payload",
    "_validate_stratified_mismatch_burden_display_payload",
]
