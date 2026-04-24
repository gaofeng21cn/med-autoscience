from __future__ import annotations

from .shared import Any, Path, _require_namespaced_registry_id, _require_non_empty_string, _require_non_negative_int, _require_numeric_list, _require_numeric_value, _require_probability_value, _require_strictly_increasing_numeric_list, math
from .validation_tables import _validate_audit_panel_collection

def _validate_model_complexity_audit_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": _require_non_empty_string(
            payload.get("title"),
            label=f"{path.name} display `{expected_display_id}` title",
        ),
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "metric_panels": _validate_audit_panel_collection(
            path=path,
            payload=payload.get("metric_panels"),
            label=f"display `{expected_display_id}` metric_panels",
        ),
        "audit_panels": _validate_audit_panel_collection(
            path=path,
            payload=payload.get("audit_panels"),
            label=f"display `{expected_display_id}` audit_panels",
        ),
    }

def _validate_time_to_event_landmark_performance_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    summaries_payload = payload.get("landmark_summaries")
    if not isinstance(summaries_payload, list) or not summaries_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty landmark_summaries list")

    normalized_summaries: list[dict[str, Any]] = []
    seen_window_labels: set[str] = set()
    seen_analysis_window_labels: set[str] = set()
    for index, item in enumerate(summaries_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` landmark_summaries[{index}] must be an object")
        window_label = _require_non_empty_string(
            item.get("window_label"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].window_label",
        )
        if window_label in seen_window_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].window_label must be unique"
            )
        analysis_window_label = _require_non_empty_string(
            item.get("analysis_window_label"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].analysis_window_label",
        )
        if analysis_window_label in seen_analysis_window_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].analysis_window_label must be unique"
            )
        landmark_months = _require_non_negative_int(
            item.get("landmark_months"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].landmark_months",
            allow_zero=False,
        )
        prediction_months = _require_non_negative_int(
            item.get("prediction_months"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].prediction_months",
            allow_zero=False,
        )
        if prediction_months <= landmark_months:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].prediction_months must exceed landmark_months"
            )
        c_index = _require_numeric_value(
            item.get("c_index"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].c_index",
        )
        if c_index < 0.0 or c_index > 1.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].c_index must stay within [0, 1]"
            )
        brier_score = _require_numeric_value(
            item.get("brier_score"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].brier_score",
        )
        if brier_score < 0.0 or brier_score > 1.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].brier_score must stay within [0, 1]"
            )
        calibration_slope = _require_numeric_value(
            item.get("calibration_slope"),
            label=f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].calibration_slope",
        )
        if not math.isfinite(calibration_slope):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` landmark_summaries[{index}].calibration_slope must be finite"
            )
        seen_window_labels.add(window_label)
        seen_analysis_window_labels.add(analysis_window_label)
        normalized_summaries.append(
            {
                "window_label": window_label,
                "analysis_window_label": analysis_window_label,
                "landmark_months": landmark_months,
                "prediction_months": prediction_months,
                "c_index": c_index,
                "brier_score": brier_score,
                "calibration_slope": calibration_slope,
                "annotation": str(item.get("annotation") or "").strip(),
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": _require_non_empty_string(
            payload.get("title"),
            label=f"{path.name} display `{expected_display_id}` title",
        ),
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "discrimination_panel_title": _require_non_empty_string(
            payload.get("discrimination_panel_title"),
            label=f"{path.name} display `{expected_display_id}` discrimination_panel_title",
        ),
        "discrimination_x_label": _require_non_empty_string(
            payload.get("discrimination_x_label"),
            label=f"{path.name} display `{expected_display_id}` discrimination_x_label",
        ),
        "error_panel_title": _require_non_empty_string(
            payload.get("error_panel_title"),
            label=f"{path.name} display `{expected_display_id}` error_panel_title",
        ),
        "error_x_label": _require_non_empty_string(
            payload.get("error_x_label"),
            label=f"{path.name} display `{expected_display_id}` error_x_label",
        ),
        "calibration_panel_title": _require_non_empty_string(
            payload.get("calibration_panel_title"),
            label=f"{path.name} display `{expected_display_id}` calibration_panel_title",
        ),
        "calibration_x_label": _require_non_empty_string(
            payload.get("calibration_x_label"),
            label=f"{path.name} display `{expected_display_id}` calibration_x_label",
        ),
        "landmark_summaries": normalized_summaries,
    }

def _validate_time_to_event_threshold_governance_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    threshold_summaries_payload = payload.get("threshold_summaries")
    if not isinstance(threshold_summaries_payload, list) or not threshold_summaries_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty threshold_summaries list"
        )
    normalized_threshold_summaries: list[dict[str, Any]] = []
    seen_threshold_labels: set[str] = set()
    previous_threshold = -1.0
    for index, item in enumerate(threshold_summaries_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` threshold_summaries[{index}] must be an object"
            )
        threshold_label = _require_non_empty_string(
            item.get("threshold_label"),
            label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].threshold_label",
        )
        if threshold_label in seen_threshold_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].threshold_label must be unique"
            )
        threshold = _require_probability_value(
            item.get("threshold"),
            label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].threshold",
        )
        if threshold <= previous_threshold:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].threshold must be strictly increasing"
            )
        previous_threshold = threshold
        seen_threshold_labels.add(threshold_label)
        normalized_threshold_summaries.append(
            {
                "threshold_label": threshold_label,
                "threshold": threshold,
                "sensitivity": _require_probability_value(
                    item.get("sensitivity"),
                    label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].sensitivity",
                ),
                "specificity": _require_probability_value(
                    item.get("specificity"),
                    label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].specificity",
                ),
                "net_benefit": _require_numeric_value(
                    item.get("net_benefit"),
                    label=f"{path.name} display `{expected_display_id}` threshold_summaries[{index}].net_benefit",
                ),
            }
        )

    risk_group_summaries_payload = payload.get("risk_group_summaries")
    if not isinstance(risk_group_summaries_payload, list) or not risk_group_summaries_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty risk_group_summaries list"
        )
    normalized_risk_group_summaries: list[dict[str, Any]] = []
    previous_group_order = 0
    for index, item in enumerate(risk_group_summaries_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}] must be an object"
            )
        group_order = _require_non_negative_int(
            item.get("group_order"),
            label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].group_order",
            allow_zero=False,
        )
        if group_order <= previous_group_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].group_order must be strictly increasing"
            )
        previous_group_order = group_order
        n = _require_non_negative_int(
            item.get("n"),
            label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].n",
            allow_zero=False,
        )
        events = _require_non_negative_int(
            item.get("events"),
            label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].events",
        )
        if events > n:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].events must not exceed .n"
            )
        normalized_risk_group_summaries.append(
            {
                "group_label": _require_non_empty_string(
                    item.get("group_label"),
                    label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].group_label",
                ),
                "group_order": group_order,
                "n": n,
                "events": events,
                "predicted_risk": _require_probability_value(
                    item.get("predicted_risk"),
                    label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].predicted_risk",
                ),
                "observed_risk": _require_probability_value(
                    item.get("observed_risk"),
                    label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].observed_risk",
                ),
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": _require_non_empty_string(
            payload.get("title"),
            label=f"{path.name} display `{expected_display_id}` title",
        ),
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "threshold_panel_title": _require_non_empty_string(
            payload.get("threshold_panel_title"),
            label=f"{path.name} display `{expected_display_id}` threshold_panel_title",
        ),
        "calibration_panel_title": _require_non_empty_string(
            payload.get("calibration_panel_title"),
            label=f"{path.name} display `{expected_display_id}` calibration_panel_title",
        ),
        "calibration_x_label": _require_non_empty_string(
            payload.get("calibration_x_label"),
            label=f"{path.name} display `{expected_display_id}` calibration_x_label",
        ),
        "threshold_summaries": normalized_threshold_summaries,
        "risk_group_summaries": normalized_risk_group_summaries,
    }

def _validate_time_to_event_multihorizon_calibration_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    previous_time_horizon = 0
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique")
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
        time_horizon_months = _require_non_negative_int(
            panel_payload.get("time_horizon_months"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].time_horizon_months",
            allow_zero=False,
        )
        if time_horizon_months <= previous_time_horizon:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].time_horizon_months must be strictly increasing"
            )
        previous_time_horizon = time_horizon_months

        calibration_summary_payload = panel_payload.get("calibration_summary")
        if not isinstance(calibration_summary_payload, list) or not calibration_summary_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary must be a non-empty list"
            )
        normalized_summary: list[dict[str, Any]] = []
        previous_group_order = 0
        for group_index, item in enumerate(calibration_summary_payload):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}] must be an object"
                )
            group_order = _require_non_negative_int(
                item.get("group_order"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}]."
                    f"calibration_summary[{group_index}].group_order"
                ),
                allow_zero=False,
            )
            if group_order <= previous_group_order:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}].group_order must be strictly increasing"
                )
            previous_group_order = group_order
            n = _require_non_negative_int(
                item.get("n"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}].n"
                ),
                allow_zero=False,
            )
            events = _require_non_negative_int(
                item.get("events"),
                label=(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}].events"
                ),
            )
            if events > n:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].calibration_summary[{group_index}].events must not exceed .n"
                )
            normalized_summary.append(
                {
                    "group_label": _require_non_empty_string(
                        item.get("group_label"),
                        label=(
                            f"{path.name} display `{expected_display_id}` panels[{panel_index}]."
                            f"calibration_summary[{group_index}].group_label"
                        ),
                    ),
                    "group_order": group_order,
                    "n": n,
                    "events": events,
                    "predicted_risk": _require_probability_value(
                        item.get("predicted_risk"),
                        label=(
                            f"{path.name} display `{expected_display_id}` panels[{panel_index}]."
                            f"calibration_summary[{group_index}].predicted_risk"
                        ),
                    ),
                    "observed_risk": _require_probability_value(
                        item.get("observed_risk"),
                        label=(
                            f"{path.name} display `{expected_display_id}` panels[{panel_index}]."
                            f"calibration_summary[{group_index}].observed_risk"
                        ),
                    ),
                }
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "time_horizon_months": time_horizon_months,
                "calibration_summary": normalized_summary,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": _require_non_empty_string(
            payload.get("title"),
            label=f"{path.name} display `{expected_display_id}` title",
        ),
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": _require_non_empty_string(
            payload.get("x_label"),
            label=f"{path.name} display `{expected_display_id}` x_label",
        ),
        "panels": normalized_panels,
    }

def _validate_time_to_event_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    raw_template_id = str(payload.get("template_id") or "").strip()
    template_id = raw_template_id
    if raw_template_id != expected_template_id:
        _, expected_short_id = _require_namespaced_registry_id(
            expected_template_id,
            label=f"{path.name} display `{expected_display_id}` expected template_id",
        )
        _, raw_short_id = _require_namespaced_registry_id(
            raw_template_id,
            label=f"{path.name} display `{expected_display_id}` template_id",
        )
        if not (
            expected_short_id == "time_to_event_risk_group_summary"
            and raw_short_id == "cumulative_incidence_grouped"
        ):
            raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
        template_id = raw_template_id
    if template_id != expected_template_id:
        expected_template_id = template_id
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    _, expected_template_short_id = _require_namespaced_registry_id(
        expected_template_id,
        label=f"{path.name} display `{expected_display_id}` template_id",
    )
    if expected_template_short_id == "time_to_event_risk_group_summary":
        summaries_payload = payload.get("risk_group_summaries")
        if not isinstance(summaries_payload, list) or not summaries_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` must contain a non-empty risk_group_summaries list"
            )
        normalized_summaries: list[dict[str, Any]] = []
        for index, item in enumerate(summaries_payload):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}] must be an object"
                )
            sample_size = _require_non_negative_int(
                item.get("sample_size"),
                label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].sample_size",
                allow_zero=False,
            )
            events_5y = _require_non_negative_int(
                item.get("events_5y"),
                label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].events_5y",
            )
            if events_5y > sample_size:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].events_5y must not exceed .sample_size"
                )
            normalized_summaries.append(
                {
                    "label": _require_non_empty_string(
                        item.get("label"),
                        label=f"{path.name} display `{expected_display_id}` risk_group_summaries[{index}].label",
                    ),
                    "sample_size": sample_size,
                    "events_5y": events_5y,
                    "mean_predicted_risk_5y": _require_numeric_value(
                        item.get("mean_predicted_risk_5y"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"risk_group_summaries[{index}].mean_predicted_risk_5y"
                        ),
                    ),
                    "observed_km_risk_5y": _require_numeric_value(
                        item.get("observed_km_risk_5y"),
                        label=(
                            f"{path.name} display `{expected_display_id}` "
                            f"risk_group_summaries[{index}].observed_km_risk_5y"
                        ),
                    ),
                }
            )
        return {
            "display_id": expected_display_id,
            "template_id": expected_template_id,
            "title": title,
            "caption": str(payload.get("caption") or "").strip(),
            "paper_role": str(payload.get("paper_role") or "").strip(),
            "panel_a_title": _require_non_empty_string(
                payload.get("panel_a_title"),
                label=f"{path.name} display `{expected_display_id}` panel_a_title",
            ),
            "panel_b_title": _require_non_empty_string(
                payload.get("panel_b_title"),
                label=f"{path.name} display `{expected_display_id}` panel_b_title",
            ),
            "x_label": x_label,
            "y_label": y_label,
            "event_count_y_label": _require_non_empty_string(
                payload.get("event_count_y_label"),
                label=f"{path.name} display `{expected_display_id}` event_count_y_label",
            ),
            "risk_group_summaries": normalized_summaries,
        }
    groups = payload.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty groups list")
    normalized_groups: list[dict[str, Any]] = []
    for index, item in enumerate(groups):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` groups[{index}] must be an object")
        label = _require_non_empty_string(
            item.get("label"), label=f"{path.name} display `{expected_display_id}` groups[{index}].label"
        )
        times = _require_numeric_list(
            item.get("times"), label=f"{path.name} display `{expected_display_id}` groups[{index}].times"
        )
        values = _require_numeric_list(
            item.get("values"), label=f"{path.name} display `{expected_display_id}` groups[{index}].values"
        )
        if len(times) != len(values):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{index}].times and .values must have the same length"
            )
        normalized_groups.append({"label": label, "times": times, "values": values})
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "groups": normalized_groups,
        "annotation": str(payload.get("annotation") or "").strip(),
    }

def _validate_time_to_event_stratified_cumulative_incidence_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
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
        groups_payload = panel_payload.get("groups")
        if not isinstance(groups_payload, list) or not groups_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups must be a non-empty list"
            )
        normalized_groups: list[dict[str, Any]] = []
        seen_group_labels: set[str] = set()
        for group_index, group_payload in enumerate(groups_payload):
            if not isinstance(group_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups[{group_index}] must be an object"
                )
            group_label = _require_non_empty_string(
                group_payload.get("label"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].groups[{group_index}].label"
                ),
            )
            if group_label in seen_group_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups[{group_index}].label must be unique within the panel"
                )
            seen_group_labels.add(group_label)
            times = _require_strictly_increasing_numeric_list(
                group_payload.get("times"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].groups[{group_index}].times"
                ),
            )
            values = _require_numeric_list(
                group_payload.get("values"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].groups[{group_index}].values"
                ),
            )
            if len(times) != len(values):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups[{group_index}].times and .values must have the same length"
                )
            normalized_values: list[float] = []
            previous_value: float | None = None
            for point_index, raw_value in enumerate(values):
                probability = _require_probability_value(
                    raw_value,
                    label=(
                        f"{path.name} display `{expected_display_id}` "
                        f"panels[{panel_index}].groups[{group_index}].values[{point_index}]"
                    ),
                )
                if previous_value is not None and probability + 1e-12 < previous_value:
                    raise ValueError(
                        f"{path.name} display `{expected_display_id}` panels[{panel_index}].groups[{group_index}].values must be monotonic non-decreasing"
                    )
                normalized_values.append(probability)
                previous_value = probability
            normalized_groups.append({"label": group_label, "times": times, "values": normalized_values})
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "annotation": str(panel_payload.get("annotation") or "").strip(),
                "groups": normalized_groups,
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
        "panels": normalized_panels,
    }

def _validate_time_to_event_discrimination_calibration_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    panel_a_title = _require_non_empty_string(
        payload.get("panel_a_title"),
        label=f"{path.name} display `{expected_display_id}` panel_a_title",
    )
    panel_b_title = _require_non_empty_string(
        payload.get("panel_b_title"),
        label=f"{path.name} display `{expected_display_id}` panel_b_title",
    )
    discrimination_x_label = _require_non_empty_string(
        payload.get("discrimination_x_label"),
        label=f"{path.name} display `{expected_display_id}` discrimination_x_label",
    )
    calibration_x_label = _require_non_empty_string(
        payload.get("calibration_x_label"),
        label=f"{path.name} display `{expected_display_id}` calibration_x_label",
    )
    calibration_y_label = _require_non_empty_string(
        payload.get("calibration_y_label"),
        label=f"{path.name} display `{expected_display_id}` calibration_y_label",
    )
    discrimination_points_payload = payload.get("discrimination_points")
    if not isinstance(discrimination_points_payload, list) or not discrimination_points_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty discrimination_points list"
        )
    normalized_points: list[dict[str, Any]] = []
    for index, item in enumerate(discrimination_points_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` discrimination_points[{index}] must be an object"
            )
        normalized_points.append(
            {
                "label": _require_non_empty_string(
                    item.get("label"),
                    label=f"{path.name} display `{expected_display_id}` discrimination_points[{index}].label",
                ),
                "c_index": _require_numeric_value(
                    item.get("c_index"),
                    label=f"{path.name} display `{expected_display_id}` discrimination_points[{index}].c_index",
                ),
                "annotation": str(item.get("annotation") or "").strip(),
            }
        )

    calibration_summary_payload = payload.get("calibration_summary")
    if not isinstance(calibration_summary_payload, list) or not calibration_summary_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty calibration_summary list"
        )
    normalized_summary: list[dict[str, Any]] = []
    previous_order = 0
    for index, item in enumerate(calibration_summary_payload):
        if not isinstance(item, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_summary[{index}] must be an object"
            )
        group_order = _require_non_negative_int(
            item.get("group_order"),
            label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].group_order",
            allow_zero=False,
        )
        if group_order <= previous_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_summary[{index}].group_order "
                "must be strictly increasing"
            )
        previous_order = group_order
        n = _require_non_negative_int(
            item.get("n"),
            label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].n",
            allow_zero=False,
        )
        events_5y = _require_non_negative_int(
            item.get("events_5y"),
            label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].events_5y",
        )
        if events_5y > n:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_summary[{index}].events_5y must not exceed .n"
            )
        normalized_summary.append(
            {
                "group_label": _require_non_empty_string(
                    item.get("group_label"),
                    label=f"{path.name} display `{expected_display_id}` calibration_summary[{index}].group_label",
                ),
                "group_order": group_order,
                "n": n,
                "events_5y": events_5y,
                "predicted_risk_5y": _require_probability_value(
                    item.get("predicted_risk_5y"),
                    label=(
                        f"{path.name} display `{expected_display_id}` calibration_summary[{index}].predicted_risk_5y"
                    ),
                ),
                "observed_risk_5y": _require_probability_value(
                    item.get("observed_risk_5y"),
                    label=(
                        f"{path.name} display `{expected_display_id}` calibration_summary[{index}].observed_risk_5y"
                    ),
                ),
            }
        )

    calibration_callout_payload = payload.get("calibration_callout")
    normalized_callout: dict[str, Any] | None = None
    if calibration_callout_payload is not None:
        if not isinstance(calibration_callout_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_callout must be an object when provided"
            )
        normalized_callout = {
            "group_label": _require_non_empty_string(
                calibration_callout_payload.get("group_label"),
                label=f"{path.name} display `{expected_display_id}` calibration_callout.group_label",
            ),
            "predicted_risk_5y": _require_probability_value(
                calibration_callout_payload.get("predicted_risk_5y"),
                label=f"{path.name} display `{expected_display_id}` calibration_callout.predicted_risk_5y",
            ),
            "observed_risk_5y": _require_probability_value(
                calibration_callout_payload.get("observed_risk_5y"),
                label=f"{path.name} display `{expected_display_id}` calibration_callout.observed_risk_5y",
            ),
            "events_5y": (
                _require_non_negative_int(
                    calibration_callout_payload.get("events_5y"),
                    label=f"{path.name} display `{expected_display_id}` calibration_callout.events_5y",
                )
                if calibration_callout_payload.get("events_5y") is not None
                else None
            ),
            "n": (
                _require_non_negative_int(
                    calibration_callout_payload.get("n"),
                    label=f"{path.name} display `{expected_display_id}` calibration_callout.n",
                    allow_zero=False,
                )
                if calibration_callout_payload.get("n") is not None
                else None
            ),
        }
        matched_summary = next(
            (
                item
                for item in normalized_summary
                if str(item.get("group_label") or "").strip() == str(normalized_callout.get("group_label") or "").strip()
            ),
            None,
        )
        if matched_summary is None:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_callout.group_label must match calibration_summary"
            )
        if (
            abs(float(normalized_callout["predicted_risk_5y"]) - float(matched_summary["predicted_risk_5y"])) > 1e-12
            or abs(float(normalized_callout["observed_risk_5y"]) - float(matched_summary["observed_risk_5y"])) > 1e-12
            or (
                normalized_callout.get("events_5y") is not None
                and int(normalized_callout["events_5y"]) != int(matched_summary["events_5y"])
            )
            or (normalized_callout.get("n") is not None and int(normalized_callout["n"]) != int(matched_summary["n"]))
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` calibration_callout must match the referenced calibration_summary row"
            )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "panel_a_title": panel_a_title,
        "panel_b_title": panel_b_title,
        "discrimination_x_label": discrimination_x_label,
        "calibration_x_label": calibration_x_label,
        "calibration_y_label": calibration_y_label,
        "discrimination_points": normalized_points,
        "calibration_summary": normalized_summary,
        "calibration_callout": normalized_callout,
    }


__all__ = [
    "_validate_model_complexity_audit_display_payload",
    "_validate_time_to_event_landmark_performance_display_payload",
    "_validate_time_to_event_threshold_governance_display_payload",
    "_validate_time_to_event_multihorizon_calibration_display_payload",
    "_validate_time_to_event_display_payload",
    "_validate_time_to_event_stratified_cumulative_incidence_display_payload",
    "_validate_time_to_event_discrimination_calibration_display_payload",
]
