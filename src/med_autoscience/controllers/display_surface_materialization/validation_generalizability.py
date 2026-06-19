from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, math

def _validate_generalizability_subgroup_composite_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    metric_family = _require_non_empty_string(
        payload.get("metric_family"),
        label=f"{path.name} display `{expected_display_id}` metric_family",
    )
    if metric_family not in {"discrimination", "calibration_ratio", "effect_estimate", "utility_delta"}:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` metric_family must be one of discrimination, calibration_ratio, effect_estimate, or utility_delta"
        )
    primary_label = _require_non_empty_string(
        payload.get("primary_label"),
        label=f"{path.name} display `{expected_display_id}` primary_label",
    )
    comparator_label = str(payload.get("comparator_label") or "").strip()
    overview_rows_payload = payload.get("overview_rows")
    if not isinstance(overview_rows_payload, list) or not overview_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty overview_rows list")
    normalized_overview_rows: list[dict[str, Any]] = []
    seen_cohort_ids: set[str] = set()
    seen_cohort_labels: set[str] = set()
    for row_index, row_payload in enumerate(overview_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` overview_rows[{row_index}] must be an object")
        cohort_id = _require_non_empty_string(
            row_payload.get("cohort_id"),
            label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].cohort_id",
        )
        if cohort_id in seen_cohort_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].cohort_id must be unique"
            )
        seen_cohort_ids.add(cohort_id)
        cohort_label = _require_non_empty_string(
            row_payload.get("cohort_label"),
            label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].cohort_label",
        )
        if cohort_label in seen_cohort_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].cohort_label must be unique"
            )
        seen_cohort_labels.add(cohort_label)
        metric_value = _require_numeric_value(
            row_payload.get("metric_value"),
            label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].metric_value",
        )
        if not math.isfinite(metric_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].metric_value must be finite"
            )
        comparator_metric_raw = row_payload.get("comparator_metric_value")
        if comparator_label:
            if comparator_metric_raw is None:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].comparator_metric_value must be provided for every overview row when comparator_label is declared"
                )
            comparator_metric_value = _require_numeric_value(
                comparator_metric_raw,
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"overview_rows[{row_index}].comparator_metric_value"
                ),
            )
            if not math.isfinite(comparator_metric_value):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].comparator_metric_value must be finite"
                )
        else:
            if comparator_metric_raw is not None:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].comparator_metric_value must be absent unless comparator_label is declared"
                )
            comparator_metric_value = None
        normalized_row: dict[str, Any] = {
            "cohort_id": cohort_id,
            "cohort_label": cohort_label,
            "support_count": _require_non_negative_int(
                row_payload.get("support_count"),
                label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].support_count",
            ),
            "metric_value": metric_value,
        }
        if comparator_metric_value is not None:
            normalized_row["comparator_metric_value"] = comparator_metric_value
        if row_payload.get("event_count") is not None:
            normalized_row["event_count"] = _require_non_negative_int(
                row_payload.get("event_count"),
                label=f"{path.name} display `{expected_display_id}` overview_rows[{row_index}].event_count",
            )
        normalized_overview_rows.append(normalized_row)

    subgroup_rows_payload = payload.get("subgroup_rows")
    if not isinstance(subgroup_rows_payload, list) or not subgroup_rows_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty subgroup_rows list")
    normalized_subgroup_rows: list[dict[str, Any]] = []
    seen_subgroup_ids: set[str] = set()
    seen_subgroup_labels: set[str] = set()
    for row_index, row_payload in enumerate(subgroup_rows_payload):
        if not isinstance(row_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] must be an object")
        subgroup_id = _require_non_empty_string(
            row_payload.get("subgroup_id"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].subgroup_id",
        )
        if subgroup_id in seen_subgroup_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].subgroup_id must be unique"
            )
        seen_subgroup_ids.add(subgroup_id)
        subgroup_label = _require_non_empty_string(
            row_payload.get("subgroup_label"),
            label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].subgroup_label",
        )
        if subgroup_label in seen_subgroup_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].subgroup_label must be unique"
            )
        seen_subgroup_labels.add(subgroup_label)
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
        if not all(math.isfinite(value) for value in (estimate, lower, upper)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] values must be finite"
            )
        if not (lower <= estimate <= upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}] must satisfy lower <= estimate <= upper"
            )
        normalized_row = {
            "subgroup_id": subgroup_id,
            "subgroup_label": subgroup_label,
            "estimate": estimate,
            "lower": lower,
            "upper": upper,
        }
        if row_payload.get("group_n") is not None:
            normalized_row["group_n"] = _require_non_negative_int(
                row_payload.get("group_n"),
                label=f"{path.name} display `{expected_display_id}` subgroup_rows[{row_index}].group_n",
            )
        normalized_subgroup_rows.append(normalized_row)

    subgroup_reference_value = _require_numeric_value(
        payload.get("subgroup_reference_value"),
        label=f"{path.name} display `{expected_display_id}` subgroup_reference_value",
    )
    if not math.isfinite(subgroup_reference_value):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` subgroup_reference_value must be finite"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "metric_family": metric_family,
        "primary_label": primary_label,
        "comparator_label": comparator_label,
        "overview_panel_title": _require_non_empty_string(
            payload.get("overview_panel_title"),
            label=f"{path.name} display `{expected_display_id}` overview_panel_title",
        ),
        "overview_x_label": _require_non_empty_string(
            payload.get("overview_x_label"),
            label=f"{path.name} display `{expected_display_id}` overview_x_label",
        ),
        "overview_rows": normalized_overview_rows,
        "subgroup_panel_title": _require_non_empty_string(
            payload.get("subgroup_panel_title"),
            label=f"{path.name} display `{expected_display_id}` subgroup_panel_title",
        ),
        "subgroup_x_label": _require_non_empty_string(
            payload.get("subgroup_x_label"),
            label=f"{path.name} display `{expected_display_id}` subgroup_x_label",
        ),
        "subgroup_reference_value": subgroup_reference_value,
        "subgroup_rows": normalized_subgroup_rows,
    }

__all__ = [
    "_validate_generalizability_subgroup_composite_display_payload",
]
