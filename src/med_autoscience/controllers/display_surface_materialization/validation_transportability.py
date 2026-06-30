from __future__ import annotations

from .shared import Any, Path, _require_namespaced_registry_id, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, math


def _validate_center_transportability_governance_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    _require_namespaced_registry_id(expected_template_id, label=f"{path.name} display `{expected_display_id}` template_id")
    centers_payload = payload.get("centers")
    if not isinstance(centers_payload, list) or len(centers_payload) < 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain at least two centers")

    normalized_centers: list[dict[str, Any]] = []
    seen_center_ids: set[str] = set()
    seen_center_labels: set[str] = set()
    for index, item in enumerate(centers_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` centers[{index}] must be an object")
        center_id = _require_non_empty_string(
            item.get("center_id"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].center_id",
        )
        if center_id in seen_center_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` centers[{index}].center_id must be unique")
        seen_center_ids.add(center_id)
        center_label = _require_non_empty_string(
            item.get("center_label"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].center_label",
        )
        if center_label in seen_center_labels:
            raise ValueError(f"{path.name} display `{expected_display_id}` centers[{index}].center_label must be unique")
        seen_center_labels.add(center_label)

        metric_estimate = _require_numeric_value(
            item.get("metric_estimate"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].metric_estimate",
        )
        metric_lower = _require_numeric_value(
            item.get("metric_lower"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].metric_lower",
        )
        metric_upper = _require_numeric_value(
            item.get("metric_upper"),
            label=f"{path.name} display `{expected_display_id}` centers[{index}].metric_upper",
        )
        if not all(math.isfinite(value) for value in (metric_estimate, metric_lower, metric_upper)):
            raise ValueError(f"{path.name} display `{expected_display_id}` centers[{index}] metric values must be finite")
        if not (metric_lower <= metric_estimate <= metric_upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{index}] must satisfy metric_lower <= metric_estimate <= metric_upper"
            )
        normalized_centers.append(
            {
                "center_id": center_id,
                "center_label": center_label,
                "cohort_role": _require_non_empty_string(
                    item.get("cohort_role"),
                    label=f"{path.name} display `{expected_display_id}` centers[{index}].cohort_role",
                ),
                "support_count": _require_non_negative_int(
                    item.get("support_count"),
                    label=f"{path.name} display `{expected_display_id}` centers[{index}].support_count",
                    allow_zero=False,
                ),
                "event_count": _require_non_negative_int(
                    item.get("event_count"),
                    label=f"{path.name} display `{expected_display_id}` centers[{index}].event_count",
                ),
                "metric_estimate": metric_estimate,
                "metric_lower": metric_lower,
                "metric_upper": metric_upper,
                "max_shift": _require_numeric_value(
                    item.get("max_shift"),
                    label=f"{path.name} display `{expected_display_id}` centers[{index}].max_shift",
                ),
                "slope": _require_numeric_value(
                    item.get("slope"),
                    label=f"{path.name} display `{expected_display_id}` centers[{index}].slope",
                ),
                "oe_ratio": _require_numeric_value(
                    item.get("oe_ratio"),
                    label=f"{path.name} display `{expected_display_id}` centers[{index}].oe_ratio",
                ),
                "verdict": _require_non_empty_string(
                    item.get("verdict"),
                    label=f"{path.name} display `{expected_display_id}` centers[{index}].verdict",
                ),
                "action": _require_non_empty_string(
                    item.get("action"),
                    label=f"{path.name} display `{expected_display_id}` centers[{index}].action",
                ),
                "detail": str(item.get("detail") or "").strip(),
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": str(payload.get("title") or "").strip(),
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "metric_family": _require_non_empty_string(
            payload.get("metric_family"),
            label=f"{path.name} display `{expected_display_id}` metric_family",
        ),
        "metric_panel_title": _require_non_empty_string(
            payload.get("metric_panel_title"),
            label=f"{path.name} display `{expected_display_id}` metric_panel_title",
        ),
        "metric_x_label": _require_non_empty_string(
            payload.get("metric_x_label"),
            label=f"{path.name} display `{expected_display_id}` metric_x_label",
        ),
        "metric_reference_value": _require_numeric_value(
            payload.get("metric_reference_value"),
            label=f"{path.name} display `{expected_display_id}` metric_reference_value",
        ),
        "batch_shift_threshold": _require_numeric_value(
            payload.get("batch_shift_threshold"),
            label=f"{path.name} display `{expected_display_id}` batch_shift_threshold",
        ),
        "slope_acceptance_lower": _require_numeric_value(
            payload.get("slope_acceptance_lower"),
            label=f"{path.name} display `{expected_display_id}` slope_acceptance_lower",
        ),
        "slope_acceptance_upper": _require_numeric_value(
            payload.get("slope_acceptance_upper"),
            label=f"{path.name} display `{expected_display_id}` slope_acceptance_upper",
        ),
        "oe_ratio_acceptance_lower": _require_numeric_value(
            payload.get("oe_ratio_acceptance_lower"),
            label=f"{path.name} display `{expected_display_id}` oe_ratio_acceptance_lower",
        ),
        "oe_ratio_acceptance_upper": _require_numeric_value(
            payload.get("oe_ratio_acceptance_upper"),
            label=f"{path.name} display `{expected_display_id}` oe_ratio_acceptance_upper",
        ),
        "summary_panel_title": _require_non_empty_string(
            payload.get("summary_panel_title"),
            label=f"{path.name} display `{expected_display_id}` summary_panel_title",
        ),
        "centers": normalized_centers,
    }


__all__ = [
    "_validate_center_transportability_governance_summary_panel_display_payload",
]
