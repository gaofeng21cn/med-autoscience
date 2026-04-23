from __future__ import annotations

from .shared import Any, Path, _require_namespaced_registry_id, _require_non_empty_string, _require_non_negative_int, _require_numeric_list, _require_numeric_value
from .validation_tables import _validate_axis_window_payload, _validate_curve_series_payload, _validate_reference_line_payload, _validate_single_curve_series_payload

def _validate_time_to_event_decision_curve_display_payload(
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
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    treated_fraction_y_label = _require_non_empty_string(
        payload.get("treated_fraction_y_label"),
        label=f"{path.name} display `{expected_display_id}` treated_fraction_y_label",
    )
    series_payload = payload.get("series")
    if not isinstance(series_payload, list) or not series_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty series list")
    normalized_series: list[dict[str, Any]] = []
    for index, item in enumerate(series_payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` series[{index}] must be an object")
        label = _require_non_empty_string(
            item.get("label"), label=f"{path.name} display `{expected_display_id}` series[{index}].label"
        )
        x = _require_numeric_list(
            item.get("x"), label=f"{path.name} display `{expected_display_id}` series[{index}].x"
        )
        y = _require_numeric_list(
            item.get("y"), label=f"{path.name} display `{expected_display_id}` series[{index}].y"
        )
        if len(x) != len(y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` series[{index}].x and .y must have the same length"
            )
        normalized_series.append({"label": label, "x": x, "y": y, "annotation": str(item.get("annotation") or "").strip()})

    treated_fraction_payload = payload.get("treated_fraction_series")
    if not isinstance(treated_fraction_payload, dict):
        raise ValueError(f"{path.name} display `{expected_display_id}` treated_fraction_series must be an object")
    treated_fraction_label = _require_non_empty_string(
        treated_fraction_payload.get("label"),
        label=f"{path.name} display `{expected_display_id}` treated_fraction_series.label",
    )
    treated_fraction_x = _require_numeric_list(
        treated_fraction_payload.get("x"),
        label=f"{path.name} display `{expected_display_id}` treated_fraction_series.x",
    )
    treated_fraction_y = _require_numeric_list(
        treated_fraction_payload.get("y"),
        label=f"{path.name} display `{expected_display_id}` treated_fraction_series.y",
    )
    if len(treated_fraction_x) != len(treated_fraction_y):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` treated_fraction_series.x and .y must have the same length"
        )
    time_horizon_months = payload.get("time_horizon_months")
    normalized_time_horizon_months = (
        _require_non_negative_int(
            time_horizon_months,
            label=f"{path.name} display `{expected_display_id}` time_horizon_months",
            allow_zero=False,
        )
        if time_horizon_months is not None
        else None
    )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "panel_a_title": panel_a_title,
        "panel_b_title": panel_b_title,
        "x_label": x_label,
        "y_label": y_label,
        "treated_fraction_y_label": treated_fraction_y_label,
        "reference_line": _validate_reference_line_payload(
            path=path,
            payload=payload.get("reference_line"),
            label=f"display `{expected_display_id}` reference_line",
        ),
        "series": normalized_series,
        "treated_fraction_series": {
            "label": treated_fraction_label,
            "x": treated_fraction_x,
            "y": treated_fraction_y,
        },
        "time_horizon_months": normalized_time_horizon_months,
    }

def _validate_binary_curve_display_payload(
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
    normalized_series = _validate_curve_series_payload(
        path=path,
        payload=payload.get("series"),
        label=f"display `{expected_display_id}` series",
    )
    reference_line = payload.get("reference_line")
    normalized_reference_line: dict[str, Any] | None = None
    if reference_line is not None:
        if not isinstance(reference_line, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` reference_line must be an object")
        ref_x = _require_numeric_list(
            reference_line.get("x"),
            label=f"{path.name} display `{expected_display_id}` reference_line.x",
        )
        ref_y = _require_numeric_list(
            reference_line.get("y"),
            label=f"{path.name} display `{expected_display_id}` reference_line.y",
        )
        if len(ref_x) != len(ref_y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` reference_line.x and .y must have the same length"
            )
        normalized_reference_line = {
            "x": ref_x,
            "y": ref_y,
            "label": str(reference_line.get("label") or "").strip(),
        }
    time_horizon_months = payload.get("time_horizon_months")
    normalized_time_horizon_months = (
        _require_non_negative_int(
            time_horizon_months,
            label=f"{path.name} display `{expected_display_id}` time_horizon_months",
            allow_zero=False,
        )
        if time_horizon_months is not None
        else None
    )
    _, expected_template_short_id = _require_namespaced_registry_id(
        expected_template_id,
        label=f"{path.name} display `{expected_display_id}` template_id",
    )
    if expected_template_short_id == "time_to_event_decision_curve":
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
            "treated_fraction_y_label": _require_non_empty_string(
                payload.get("treated_fraction_y_label"),
                label=f"{path.name} display `{expected_display_id}` treated_fraction_y_label",
            ),
            "reference_line": normalized_reference_line,
            "series": normalized_series,
            "treated_fraction_series": _validate_single_curve_series_payload(
                path=path,
                payload=payload.get("treated_fraction_series"),
                label=f"display `{expected_display_id}` treated_fraction_series",
            ),
            "time_horizon_months": normalized_time_horizon_months,
        }
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "y_label": y_label,
        "reference_line": normalized_reference_line,
        "series": normalized_series,
        "time_horizon_months": normalized_time_horizon_months,
    }

def _validate_time_dependent_roc_comparison_display_payload(
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

        analysis_window_label = _require_non_empty_string(
            panel_payload.get("analysis_window_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].analysis_window_label",
        )
        normalized_series = _validate_curve_series_payload(
            path=path,
            payload=panel_payload.get("series"),
            label=f"display `{expected_display_id}` panels[{panel_index}].series",
        )
        seen_series_labels: set[str] = set()
        for series_index, series_payload in enumerate(normalized_series):
            series_label = str(series_payload["label"])
            if series_label in seen_series_labels:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].series[{series_index}].label must be unique within the panel"
                )
            seen_series_labels.add(series_label)
        time_horizon_months = panel_payload.get("time_horizon_months")
        normalized_time_horizon_months = (
            _require_non_negative_int(
                time_horizon_months,
                label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].time_horizon_months",
                allow_zero=False,
            )
            if time_horizon_months is not None
            else None
        )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "analysis_window_label": analysis_window_label,
                "time_horizon_months": normalized_time_horizon_months,
                "annotation": str(panel_payload.get("annotation") or "").strip(),
                "series": normalized_series,
                "reference_line": _validate_reference_line_payload(
                    path=path,
                    payload=panel_payload.get("reference_line"),
                    label=f"display `{expected_display_id}` panels[{panel_index}].reference_line",
                ),
            }
        )

    if normalized_panels:
        expected_series_labels = tuple(series["label"] for series in normalized_panels[0]["series"])
        for panel_index, panel in enumerate(normalized_panels[1:], start=1):
            observed_series_labels = tuple(series["label"] for series in panel["series"])
            if observed_series_labels == expected_series_labels:
                continue
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].series labels must match the first panel"
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

def _validate_risk_layering_bar_payload(
    *,
    path: Path,
    payload: object,
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"{path.name} {label} must contain a non-empty list")
    normalized_bars: list[dict[str, Any]] = []
    previous_risk: float | None = None
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"{path.name} {label}[{index}] must be an object")
        bar_label = _require_non_empty_string(item.get("label"), label=f"{path.name} {label}[{index}].label")
        cases = _require_non_negative_int(item.get("cases"), label=f"{path.name} {label}[{index}].cases", allow_zero=False)
        events = _require_non_negative_int(item.get("events"), label=f"{path.name} {label}[{index}].events")
        if events > cases:
            raise ValueError(f"{path.name} {label}[{index}].events must not exceed .cases")
        risk = _require_numeric_value(item.get("risk"), label=f"{path.name} {label}[{index}].risk")
        if not 0.0 <= risk <= 1.0:
            raise ValueError(f"{path.name} {label}[{index}].risk must lie within [0, 1]")
        expected_risk = float(events) / float(cases)
        if abs(risk - expected_risk) > 1e-3:
            raise ValueError(
                f"{path.name} {label}[{index}].risk must match events/cases within tolerance 1e-3"
            )
        if previous_risk is not None and risk < previous_risk:
            raise ValueError(f"{path.name} {label}[{index}].risk must be monotonic non-decreasing")
        previous_risk = risk
        normalized_bars.append(
            {
                "label": bar_label,
                "cases": cases,
                "events": events,
                "risk": risk,
            }
        )
    return normalized_bars

def _validate_risk_layering_display_payload(
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
        "y_label": _require_non_empty_string(
            payload.get("y_label"),
            label=f"{path.name} display `{expected_display_id}` y_label",
        ),
        "left_panel_title": _require_non_empty_string(
            payload.get("left_panel_title"),
            label=f"{path.name} display `{expected_display_id}` left_panel_title",
        ),
        "left_x_label": _require_non_empty_string(
            payload.get("left_x_label"),
            label=f"{path.name} display `{expected_display_id}` left_x_label",
        ),
        "left_bars": _validate_risk_layering_bar_payload(
            path=path,
            payload=payload.get("left_bars"),
            label=f"display `{expected_display_id}` left_bars",
        ),
        "right_panel_title": _require_non_empty_string(
            payload.get("right_panel_title"),
            label=f"{path.name} display `{expected_display_id}` right_panel_title",
        ),
        "right_x_label": _require_non_empty_string(
            payload.get("right_x_label"),
            label=f"{path.name} display `{expected_display_id}` right_x_label",
        ),
        "right_bars": _validate_risk_layering_bar_payload(
            path=path,
            payload=payload.get("right_bars"),
            label=f"display `{expected_display_id}` right_bars",
        ),
    }

def _validate_binary_calibration_decision_curve_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    calibration_series = _validate_curve_series_payload(
        path=path,
        payload=payload.get("calibration_series"),
        label=f"display `{expected_display_id}` calibration_series",
    )
    decision_series = _validate_curve_series_payload(
        path=path,
        payload=payload.get("decision_series"),
        label=f"display `{expected_display_id}` decision_series",
    )
    decision_reference_lines = _validate_curve_series_payload(
        path=path,
        payload=payload.get("decision_reference_lines"),
        label=f"display `{expected_display_id}` decision_reference_lines",
    )
    calibration_axis_window = _validate_axis_window_payload(
        path=path,
        payload=payload.get("calibration_axis_window"),
        label=f"display `{expected_display_id}` calibration_axis_window",
        require_probability_bounds=True,
    )
    if calibration_axis_window is None:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` calibration_axis_window must be declared for audited binary calibration panels"
        )
    decision_focus_window = payload.get("decision_focus_window")
    if not isinstance(decision_focus_window, dict):
        raise ValueError(f"{path.name} display `{expected_display_id}` decision_focus_window must be an object")
    xmin = _require_numeric_value(
        decision_focus_window.get("xmin"),
        label=f"{path.name} display `{expected_display_id}` decision_focus_window.xmin",
    )
    xmax = _require_numeric_value(
        decision_focus_window.get("xmax"),
        label=f"{path.name} display `{expected_display_id}` decision_focus_window.xmax",
    )
    if xmin >= xmax:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` decision_focus_window.xmin must be < .xmax"
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
        "calibration_x_label": _require_non_empty_string(
            payload.get("calibration_x_label"),
            label=f"{path.name} display `{expected_display_id}` calibration_x_label",
        ),
        "calibration_y_label": _require_non_empty_string(
            payload.get("calibration_y_label"),
            label=f"{path.name} display `{expected_display_id}` calibration_y_label",
        ),
        "decision_x_label": _require_non_empty_string(
            payload.get("decision_x_label"),
            label=f"{path.name} display `{expected_display_id}` decision_x_label",
        ),
        "decision_y_label": _require_non_empty_string(
            payload.get("decision_y_label"),
            label=f"{path.name} display `{expected_display_id}` decision_y_label",
        ),
        "calibration_axis_window": calibration_axis_window,
        "calibration_reference_line": _validate_reference_line_payload(
            path=path,
            payload=payload.get("calibration_reference_line"),
            label=f"display `{expected_display_id}` calibration_reference_line",
        ),
        "calibration_series": calibration_series,
        "decision_series": decision_series,
        "decision_reference_lines": decision_reference_lines,
        "decision_focus_window": {"xmin": xmin, "xmax": xmax},
    }


__all__ = [
    "_validate_time_to_event_decision_curve_display_payload",
    "_validate_binary_curve_display_payload",
    "_validate_time_dependent_roc_comparison_display_payload",
    "_validate_risk_layering_bar_payload",
    "_validate_risk_layering_display_payload",
    "_validate_binary_calibration_decision_curve_display_payload",
]
