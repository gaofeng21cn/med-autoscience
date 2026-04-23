from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, _require_probability_value, get_template_short_id, math

def _validate_multicenter_generalizability_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    overview_mode = _require_non_empty_string(
        payload.get("overview_mode"),
        label=f"{path.name} display `{expected_display_id}` overview_mode",
    )
    if overview_mode != "center_support_counts":
        raise ValueError(
            f"{path.name} display `{expected_display_id}` overview_mode must equal `center_support_counts`"
        )
    center_event_y_label = _require_non_empty_string(
        payload.get("center_event_y_label"),
        label=f"{path.name} display `{expected_display_id}` center_event_y_label",
    )
    coverage_y_label = _require_non_empty_string(
        payload.get("coverage_y_label"),
        label=f"{path.name} display `{expected_display_id}` coverage_y_label",
    )
    center_event_counts_payload = payload.get("center_event_counts")
    if not isinstance(center_event_counts_payload, list) or not center_event_counts_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty center_event_counts list")
    normalized_center_event_counts: list[dict[str, Any]] = []
    for index, item in enumerate(center_event_counts_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` center_event_counts[{index}] must be an object"
            )
        split_bucket = _require_non_empty_string(
            item.get("split_bucket"),
            label=f"{path.name} display `{expected_display_id}` center_event_counts[{index}].split_bucket",
        )
        if split_bucket not in {"train", "validation"}:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` center_event_counts[{index}].split_bucket must be `train` or `validation`"
            )
        normalized_center_event_counts.append(
            {
                "center_label": _require_non_empty_string(
                    item.get("center_label"),
                    label=f"{path.name} display `{expected_display_id}` center_event_counts[{index}].center_label",
                ),
                "split_bucket": split_bucket,
                "event_count": _require_non_negative_int(
                    item.get("event_count"),
                    label=f"{path.name} display `{expected_display_id}` center_event_counts[{index}].event_count",
                ),
            }
        )

    coverage_panels_payload = payload.get("coverage_panels")
    if not isinstance(coverage_panels_payload, list) or not coverage_panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty coverage_panels list")
    normalized_coverage_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_layout_roles: set[str] = set()
    for index, panel in enumerate(coverage_panels_payload):
        if not isinstance(panel, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` coverage_panels[{index}] must be an object")
        panel_id = _require_non_empty_string(
            panel.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` coverage_panels[{index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coverage_panels[{index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        layout_role = _require_non_empty_string(
            panel.get("layout_role"),
            label=f"{path.name} display `{expected_display_id}` coverage_panels[{index}].layout_role",
        )
        if layout_role not in {"wide_left", "top_right", "bottom_right"}:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coverage_panels[{index}].layout_role is not supported"
            )
        if layout_role in seen_layout_roles:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coverage_panels layout_role `{layout_role}` must be unique"
            )
        seen_layout_roles.add(layout_role)
        bars_payload = panel.get("bars")
        if not isinstance(bars_payload, list) or not bars_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` coverage_panels[{index}].bars must be a non-empty list"
            )
        normalized_bars: list[dict[str, Any]] = []
        for bar_index, bar in enumerate(bars_payload):
            if not isinstance(bar, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` coverage_panels[{index}].bars[{bar_index}] must be an object"
                )
            normalized_bars.append(
                {
                    "label": _require_non_empty_string(
                        bar.get("label"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"coverage_panels[{index}].bars[{bar_index}].label"
                        ),
                    ),
                    "count": _require_non_negative_int(
                        bar.get("count"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"coverage_panels[{index}].bars[{bar_index}].count"
                        ),
                    ),
                }
            )
        normalized_coverage_panels.append(
            {
                "panel_id": panel_id,
                "title": _require_non_empty_string(
                    panel.get("title"),
                    label=f"{path.name} display `{expected_display_id}` coverage_panels[{index}].title",
                ),
                "layout_role": layout_role,
                "bars": normalized_bars,
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "overview_mode": overview_mode,
        "center_event_y_label": center_event_y_label,
        "coverage_y_label": coverage_y_label,
        "center_event_counts": normalized_center_event_counts,
        "coverage_panels": normalized_coverage_panels,
    }

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

def _validate_center_transportability_governance_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    payload_template_id = str(payload.get("template_id") or "").strip()
    allowed_template_ids = {expected_template_id}
    try:
        allowed_template_ids.add(get_template_short_id(expected_template_id))
    except ValueError:
        pass
    if payload_template_id not in allowed_template_ids:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    metric_family = _require_non_empty_string(
        payload.get("metric_family"),
        label=f"{path.name} display `{expected_display_id}` metric_family",
    )
    supported_metric_families = {"discrimination", "calibration_ratio", "effect_estimate", "utility_delta"}
    if metric_family not in supported_metric_families:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` metric_family must be one of "
            "discrimination, calibration_ratio, effect_estimate, or utility_delta"
        )

    metric_reference_value = _require_numeric_value(
        payload.get("metric_reference_value"),
        label=f"{path.name} display `{expected_display_id}` metric_reference_value",
    )
    if not math.isfinite(metric_reference_value):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` metric_reference_value must be finite"
        )
    batch_shift_threshold = _require_numeric_value(
        payload.get("batch_shift_threshold"),
        label=f"{path.name} display `{expected_display_id}` batch_shift_threshold",
    )
    if not math.isfinite(batch_shift_threshold) or batch_shift_threshold <= 0.0:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` batch_shift_threshold must be positive and finite"
        )
    slope_acceptance_lower = _require_numeric_value(
        payload.get("slope_acceptance_lower"),
        label=f"{path.name} display `{expected_display_id}` slope_acceptance_lower",
    )
    slope_acceptance_upper = _require_numeric_value(
        payload.get("slope_acceptance_upper"),
        label=f"{path.name} display `{expected_display_id}` slope_acceptance_upper",
    )
    if (
        not math.isfinite(slope_acceptance_lower)
        or not math.isfinite(slope_acceptance_upper)
        or slope_acceptance_lower <= 0.0
        or slope_acceptance_upper <= 0.0
        or slope_acceptance_lower >= slope_acceptance_upper
    ):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` slope_acceptance band must be positive, finite, and ordered"
        )
    oe_ratio_acceptance_lower = _require_numeric_value(
        payload.get("oe_ratio_acceptance_lower"),
        label=f"{path.name} display `{expected_display_id}` oe_ratio_acceptance_lower",
    )
    oe_ratio_acceptance_upper = _require_numeric_value(
        payload.get("oe_ratio_acceptance_upper"),
        label=f"{path.name} display `{expected_display_id}` oe_ratio_acceptance_upper",
    )
    if (
        not math.isfinite(oe_ratio_acceptance_lower)
        or not math.isfinite(oe_ratio_acceptance_upper)
        or oe_ratio_acceptance_lower <= 0.0
        or oe_ratio_acceptance_upper <= 0.0
        or oe_ratio_acceptance_lower >= oe_ratio_acceptance_upper
    ):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` oe_ratio_acceptance band must be positive, finite, and ordered"
        )

    centers_payload = payload.get("centers")
    if not isinstance(centers_payload, list) or not centers_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty centers list")
    supported_verdicts = {
        "stable",
        "context_dependent",
        "recalibration_required",
        "insufficient_support",
        "unstable",
    }
    normalized_centers: list[dict[str, Any]] = []
    seen_center_ids: set[str] = set()
    seen_center_labels: set[str] = set()
    for center_index, center_payload in enumerate(centers_payload):
        if not isinstance(center_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` centers[{center_index}] must be an object")
        center_id = _require_non_empty_string(
            center_payload.get("center_id"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].center_id",
        )
        if center_id in seen_center_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].center_id must be unique"
            )
        seen_center_ids.add(center_id)
        center_label = _require_non_empty_string(
            center_payload.get("center_label"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].center_label",
        )
        if center_label in seen_center_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].center_label must be unique"
            )
        seen_center_labels.add(center_label)
        support_count = _require_non_negative_int(
            center_payload.get("support_count"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].support_count",
            allow_zero=False,
        )
        event_count = _require_non_negative_int(
            center_payload.get("event_count"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].event_count",
        )
        if event_count > support_count:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].event_count must not exceed support_count"
            )
        metric_estimate = _require_numeric_value(
            center_payload.get("metric_estimate"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].metric_estimate",
        )
        metric_lower = _require_numeric_value(
            center_payload.get("metric_lower"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].metric_lower",
        )
        metric_upper = _require_numeric_value(
            center_payload.get("metric_upper"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].metric_upper",
        )
        if not all(math.isfinite(value) for value in (metric_estimate, metric_lower, metric_upper)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}] metric values must be finite"
            )
        if not (metric_lower <= metric_estimate <= metric_upper):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}] must satisfy metric_lower <= metric_estimate <= metric_upper"
            )
        max_shift = _require_probability_value(
            center_payload.get("max_shift"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].max_shift",
        )
        slope = _require_numeric_value(
            center_payload.get("slope"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].slope",
        )
        if not math.isfinite(slope) or slope <= 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].slope must be positive and finite"
            )
        oe_ratio = _require_numeric_value(
            center_payload.get("oe_ratio"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].oe_ratio",
        )
        if not math.isfinite(oe_ratio) or oe_ratio <= 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].oe_ratio must be positive and finite"
            )
        verdict = _require_non_empty_string(
            center_payload.get("verdict"),
            label=f"{path.name} display `{expected_display_id}` centers[{center_index}].verdict",
        )
        if verdict not in supported_verdicts:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].verdict must be one of {sorted(supported_verdicts)}"
            )
        normalized_center = {
            "center_id": center_id,
            "center_label": center_label,
            "cohort_role": _require_non_empty_string(
                center_payload.get("cohort_role"),
                label=f"{path.name} display `{expected_display_id}` centers[{center_index}].cohort_role",
            ),
            "support_count": support_count,
            "event_count": event_count,
            "metric_estimate": metric_estimate,
            "metric_lower": metric_lower,
            "metric_upper": metric_upper,
            "max_shift": max_shift,
            "slope": slope,
            "oe_ratio": oe_ratio,
            "verdict": verdict,
            "action": _require_non_empty_string(
                center_payload.get("action"),
                label=f"{path.name} display `{expected_display_id}` centers[{center_index}].action",
            ),
        }
        detail_text = str(center_payload.get("detail") or "").strip()
        if center_payload.get("detail") is not None and not detail_text:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` centers[{center_index}].detail must be non-empty when present"
            )
        if detail_text:
            normalized_center["detail"] = detail_text
        normalized_centers.append(normalized_center)

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "metric_family": metric_family,
        "metric_panel_title": _require_non_empty_string(
            payload.get("metric_panel_title"),
            label=f"{path.name} display `{expected_display_id}` metric_panel_title",
        ),
        "metric_x_label": _require_non_empty_string(
            payload.get("metric_x_label"),
            label=f"{path.name} display `{expected_display_id}` metric_x_label",
        ),
        "metric_reference_value": metric_reference_value,
        "batch_shift_threshold": batch_shift_threshold,
        "slope_acceptance_lower": slope_acceptance_lower,
        "slope_acceptance_upper": slope_acceptance_upper,
        "oe_ratio_acceptance_lower": oe_ratio_acceptance_lower,
        "oe_ratio_acceptance_upper": oe_ratio_acceptance_upper,
        "summary_panel_title": _require_non_empty_string(
            payload.get("summary_panel_title"),
            label=f"{path.name} display `{expected_display_id}` summary_panel_title",
        ),
        "centers": normalized_centers,
    }


__all__ = [
    "_validate_multicenter_generalizability_display_payload",
    "_validate_generalizability_subgroup_composite_display_payload",
    "_validate_center_transportability_governance_summary_panel_display_payload",
]
