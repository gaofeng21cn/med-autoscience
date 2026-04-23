from __future__ import annotations

import math

from .boxes import _check_composite_panel_label_anchors, _panel_label_token
from .core import LayoutSidecar, _issue, _require_numeric


def _check_curve_metrics(metrics: dict[str, object]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    series = metrics.get("series")
    if not isinstance(series, list) or not series:
        issues.append(
            _issue(
                rule_id="series_missing",
                message="curve qc requires at least one series metric",
                target="metrics.series",
            )
        )
        return issues
    for index, item in enumerate(series):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.series[{index}] must be an object")
        x_values = item.get("x")
        y_values = item.get("y")
        if not isinstance(x_values, list) or not isinstance(y_values, list):
            raise ValueError(f"layout_sidecar.metrics.series[{index}] must contain x and y lists")
        if len(x_values) != len(y_values):
            issues.append(
                _issue(
                    rule_id="series_length_mismatch",
                    message="series x/y lengths must match",
                    target=f"metrics.series[{index}]",
                    observed={"x": len(x_values), "y": len(y_values)},
                )
            )
            continue
        for point_index, (x_value, y_value) in enumerate(zip(x_values, y_values, strict=True)):
            x_numeric = _require_numeric(x_value, label=f"layout_sidecar.metrics.series[{index}].x[{point_index}]")
            y_numeric = _require_numeric(y_value, label=f"layout_sidecar.metrics.series[{index}].y[{point_index}]")
            if not math.isfinite(x_numeric) or not math.isfinite(y_numeric):
                issues.append(
                    _issue(
                        rule_id="series_non_finite",
                        message="series coordinates must be finite",
                        target=f"metrics.series[{index}]",
                    )
                )
                break
    reference_line = metrics.get("reference_line")
    if reference_line is None:
        return issues
    if not isinstance(reference_line, dict):
        raise ValueError("layout_sidecar.metrics.reference_line must be an object when present")
    x_values = reference_line.get("x")
    y_values = reference_line.get("y")
    if not isinstance(x_values, list) or not isinstance(y_values, list):
        raise ValueError("layout_sidecar.metrics.reference_line must contain x and y lists")
    if len(x_values) != len(y_values):
        issues.append(
            _issue(
                rule_id="reference_line_length_mismatch",
                message="reference line x/y lengths must match",
                target="metrics.reference_line",
                observed={"x": len(x_values), "y": len(y_values)},
            )
        )
    return issues


def _check_time_to_event_discrimination_calibration_metrics(metrics: dict[str, object]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    discrimination_points = metrics.get("discrimination_points")
    if not isinstance(discrimination_points, list) or not discrimination_points:
        issues.append(
            _issue(
                rule_id="discrimination_points_missing",
                message="time-to-event discrimination/calibration qc requires non-empty discrimination_points",
                target="metrics.discrimination_points",
            )
        )
    else:
        for index, item in enumerate(discrimination_points):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.discrimination_points[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id="discrimination_point_label_missing",
                        message="discrimination point labels must be non-empty",
                        target=f"metrics.discrimination_points[{index}].label",
                    )
                )
            c_index = _require_numeric(
                item.get("c_index"),
                label=f"layout_sidecar.metrics.discrimination_points[{index}].c_index",
            )
            if not 0.0 <= c_index <= 1.0:
                issues.append(
                    _issue(
                        rule_id="discrimination_point_out_of_range",
                        message="discrimination C-index must stay within [0, 1]",
                        target=f"metrics.discrimination_points[{index}].c_index",
                        observed=c_index,
                    )
                )

    calibration_summary = metrics.get("calibration_summary")
    group_labels: set[str] = set()
    previous_group_order = 0
    if not isinstance(calibration_summary, list) or not calibration_summary:
        issues.append(
            _issue(
                rule_id="calibration_summary_missing",
                message="time-to-event discrimination/calibration qc requires non-empty calibration_summary",
                target="metrics.calibration_summary",
            )
        )
    else:
        for index, item in enumerate(calibration_summary):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.calibration_summary[{index}] must be an object")
            group_label = str(item.get("group_label") or "").strip()
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="calibration_group_label_missing",
                        message="calibration summary group labels must be non-empty",
                        target=f"metrics.calibration_summary[{index}].group_label",
                    )
                )
            group_labels.add(group_label)
            group_order = _require_numeric(
                item.get("group_order"),
                label=f"layout_sidecar.metrics.calibration_summary[{index}].group_order",
            )
            if int(group_order) != group_order or group_order <= previous_group_order:
                issues.append(
                    _issue(
                        rule_id="calibration_group_order_invalid",
                        message="calibration summary group_order must be strictly increasing integers",
                        target=f"metrics.calibration_summary[{index}].group_order",
                        observed=group_order,
                    )
                )
            previous_group_order = int(group_order)
            for field_name in ("predicted_risk_5y", "observed_risk_5y"):
                risk_value = _require_numeric(
                    item.get(field_name),
                    label=f"layout_sidecar.metrics.calibration_summary[{index}].{field_name}",
                )
                if not 0.0 <= risk_value <= 1.0:
                    issues.append(
                        _issue(
                            rule_id="calibration_risk_out_of_range",
                            message="calibration summary risks must stay within [0, 1]",
                            target=f"layout_sidecar.metrics.calibration_summary[{index}].{field_name}",
                            observed=risk_value,
                        )
                    )

    calibration_callout = metrics.get("calibration_callout")
    if calibration_callout is not None:
        if not isinstance(calibration_callout, dict):
            raise ValueError("layout_sidecar.metrics.calibration_callout must be an object when present")
        callout_group_label = str(calibration_callout.get("group_label") or "").strip()
        if not callout_group_label or callout_group_label not in group_labels:
            issues.append(
                _issue(
                    rule_id="calibration_callout_group_unknown",
                    message="calibration_callout.group_label must reference calibration_summary",
                    target="metrics.calibration_callout.group_label",
                    observed=callout_group_label,
                )
            )
    return issues


def _check_reference_line_within_device(sidecar: LayoutSidecar) -> list[dict[str, object]]:
    reference_line = sidecar.metrics.get("reference_line")
    if reference_line is None:
        return []
    if not isinstance(reference_line, dict):
        raise ValueError("layout_sidecar.metrics.reference_line must be an object when present")
    x_values = reference_line.get("x")
    y_values = reference_line.get("y")
    if not isinstance(x_values, list) or not isinstance(y_values, list):
        raise ValueError("layout_sidecar.metrics.reference_line must contain x and y lists")
    issues: list[dict[str, object]] = []
    for index, (x_value, y_value) in enumerate(zip(x_values, y_values, strict=False)):
        x_numeric = _require_numeric(x_value, label=f"layout_sidecar.metrics.reference_line.x[{index}]")
        y_numeric = _require_numeric(y_value, label=f"layout_sidecar.metrics.reference_line.y[{index}]")
        if sidecar.device.x0 <= x_numeric <= sidecar.device.x1 and sidecar.device.y0 <= y_numeric <= sidecar.device.y1:
            continue
        issues.append(
            _issue(
                rule_id="reference_line_out_of_device",
                message="reference line coordinates must stay inside the device domain",
                target="reference_line",
                observed={"x": x_numeric, "y": y_numeric},
                expected={
                    "x0": sidecar.device.x0,
                    "y0": sidecar.device.y0,
                    "x1": sidecar.device.x1,
                    "y1": sidecar.device.y1,
                },
            )
        )
    return issues


def _check_curve_series_collection(series: object, *, target: str) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if not isinstance(series, list) or not series:
        issues.append(
            _issue(
                rule_id="series_missing",
                message="curve-series collection must be non-empty",
                target=target,
            )
        )
        return issues
    for index, item in enumerate(series):
        if not isinstance(item, dict):
            raise ValueError(f"{target}[{index}] must be an object")
        x_values = item.get("x")
        y_values = item.get("y")
        if not isinstance(x_values, list) or not isinstance(y_values, list):
            raise ValueError(f"{target}[{index}] must contain x and y lists")
        if len(x_values) != len(y_values):
            issues.append(
                _issue(
                    rule_id="series_length_mismatch",
                    message="curve series x/y lengths must match",
                    target=f"{target}[{index}]",
                    observed={"x": len(x_values), "y": len(y_values)},
                )
            )
            continue
        for point_index, (x_value, y_value) in enumerate(zip(x_values, y_values, strict=True)):
            x_numeric = _require_numeric(x_value, label=f"{target}[{index}].x[{point_index}]")
            y_numeric = _require_numeric(y_value, label=f"{target}[{index}].y[{point_index}]")
            if math.isfinite(x_numeric) and math.isfinite(y_numeric):
                continue
            issues.append(
                _issue(
                    rule_id="series_non_finite",
                    message="curve series coordinates must be finite",
                    target=f"{target}[{index}]",
                )
            )
            break
    return issues


def _check_time_dependent_roc_comparison_panel_metrics(sidecar: LayoutSidecar) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    panel_metrics = sidecar.metrics.get("panels")
    if not isinstance(panel_metrics, list) or not panel_metrics:
        issues.append(
            _issue(
                rule_id="panel_metrics_missing",
                message="time-dependent ROC comparison qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(sidecar.panel_boxes) != len(panel_metrics):
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="time-dependent ROC comparison qc requires one panel box per declared panel",
                target="panel_boxes",
                expected={"count": len(panel_metrics)},
                observed={"count": len(sidecar.panel_boxes)},
            )
        )

    label_panel_map: dict[str, str] = {}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    seen_panel_labels: set[str] = set()
    baseline_series_labels: tuple[str, ...] | None = None
    for panel_index, panel in enumerate(panel_metrics):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_label = str(panel.get("panel_label") or "").strip()
        if not panel_label:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="time-dependent ROC comparison panels require non-empty panel_label metrics",
                    target=f"metrics.panels[{panel_index}].panel_label",
                )
            )
            continue
        if panel_label in seen_panel_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_panel_label",
                    message="time-dependent ROC comparison panel labels must be unique",
                    target="metrics.panels",
                    observed=panel_label,
                )
            )
            continue
        seen_panel_labels.add(panel_label)
        panel_label_token = _panel_label_token(panel_label)
        label_panel_map[f"panel_label_{panel_label_token}"] = f"panel_{panel_label_token}"
        if f"panel_title_{panel_label_token}" not in layout_boxes_by_id:
            issues.append(
                _issue(
                    rule_id="missing_panel_title",
                    message="time-dependent ROC comparison panels require explicit panel titles",
                    target="layout_boxes",
                    expected=f"panel_title_{panel_label_token}",
                )
            )
        analysis_window_label = str(panel.get("analysis_window_label") or "").strip()
        if not analysis_window_label:
            issues.append(
                _issue(
                    rule_id="analysis_window_label_missing",
                    message="time-dependent ROC comparison panels require non-empty analysis_window_label semantics",
                    target=f"metrics.panels[{panel_index}].analysis_window_label",
                )
            )
        time_horizon_months = panel.get("time_horizon_months")
        if time_horizon_months is not None:
            normalized_time_horizon_months = _require_numeric(
                time_horizon_months,
                label=f"layout_sidecar.metrics.panels[{panel_index}].time_horizon_months",
            )
            if not float(normalized_time_horizon_months).is_integer() or int(normalized_time_horizon_months) <= 0:
                issues.append(
                    _issue(
                        rule_id="panel_time_horizon_months_invalid",
                        message="time-dependent ROC comparison panel time_horizon_months must be a positive integer",
                        target=f"metrics.panels[{panel_index}].time_horizon_months",
                        observed=time_horizon_months,
                    )
                )

        panel_series = panel.get("series")
        issues.extend(_check_curve_series_collection(panel_series, target=f"metrics.panels[{panel_index}].series"))
        if isinstance(panel_series, list):
            seen_series_labels: set[str] = set()
            panel_series_labels: list[str] = []
            for series in panel_series:
                if not isinstance(series, dict):
                    continue
                series_label = str(series.get("label") or "").strip()
                if not series_label:
                    continue
                if series_label in seen_series_labels:
                    issues.append(
                        _issue(
                            rule_id="duplicate_series_label",
                            message="time-dependent ROC comparison series labels must be unique within each panel",
                            target=f"metrics.panels[{panel_index}].series",
                            observed=series_label,
                        )
                    )
                    break
                seen_series_labels.add(series_label)
                panel_series_labels.append(series_label)
            normalized_panel_series_labels = tuple(panel_series_labels)
            if baseline_series_labels is None:
                baseline_series_labels = normalized_panel_series_labels
            elif normalized_panel_series_labels != baseline_series_labels:
                issues.append(
                    _issue(
                        rule_id="panel_series_label_set_mismatch",
                        message="time-dependent ROC comparison panels must compare the same ordered series labels",
                        target=f"metrics.panels[{panel_index}].series",
                        observed={"series_labels": list(normalized_panel_series_labels)},
                        expected={"series_labels": list(baseline_series_labels)},
                    )
                )

        reference_line = panel.get("reference_line")
        if reference_line is not None:
            issues.extend(
                _check_reference_line_collection_within_device(
                    [reference_line],
                    sidecar=sidecar,
                    target=f"metrics.panels[{panel_index}].reference_line",
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.10,
            max_left_offset_ratio=0.12,
        )
    )
    return issues


def _check_reference_line_collection_within_device(
    reference_lines: object,
    *,
    sidecar: LayoutSidecar,
    target: str,
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if reference_lines is None:
        return issues
    if not isinstance(reference_lines, list) or not reference_lines:
        issues.append(
            _issue(
                rule_id="reference_lines_missing",
                message="reference-line collection must be non-empty when declared",
                target=target,
            )
        )
        return issues
    for index, item in enumerate(reference_lines):
        if not isinstance(item, dict):
            raise ValueError(f"{target}[{index}] must be an object")
        x_values = item.get("x")
        y_values = item.get("y")
        if not isinstance(x_values, list) or not isinstance(y_values, list):
            raise ValueError(f"{target}[{index}] must contain x and y lists")
        if len(x_values) != len(y_values):
            issues.append(
                _issue(
                    rule_id="reference_line_length_mismatch",
                    message="reference-line x/y lengths must match",
                    target=f"{target}[{index}]",
                    observed={"x": len(x_values), "y": len(y_values)},
                )
            )
            continue
        for point_index, (x_value, y_value) in enumerate(zip(x_values, y_values, strict=True)):
            x_numeric = _require_numeric(x_value, label=f"{target}[{index}].x[{point_index}]")
            y_numeric = _require_numeric(y_value, label=f"{target}[{index}].y[{point_index}]")
            if sidecar.device.x0 <= x_numeric <= sidecar.device.x1 and sidecar.device.y0 <= y_numeric <= sidecar.device.y1:
                continue
            issues.append(
                _issue(
                    rule_id="reference_line_out_of_device",
                    message="reference-line coordinates must stay inside the device domain",
                    target=f"{target}[{index}]",
                    observed={"x": x_numeric, "y": y_numeric},
                    expected={
                        "x0": sidecar.device.x0,
                        "y0": sidecar.device.y0,
                        "x1": sidecar.device.x1,
                        "y1": sidecar.device.y1,
                    },
                )
            )
    return issues


def _check_risk_layering_bar_metrics(bars: object, *, target: str) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if not isinstance(bars, list) or not bars:
        issues.append(
            _issue(
                rule_id="bars_missing",
                message="risk layering qc requires a non-empty bar list",
                target=target,
            )
        )
        return issues

    previous_risk: float | None = None
    for index, item in enumerate(bars):
        if not isinstance(item, dict):
            raise ValueError(f"{target}[{index}] must be an object")
        cases = item.get("cases")
        events = item.get("events")
        risk = item.get("risk")
        if not isinstance(cases, int) or cases <= 0:
            raise ValueError(f"{target}[{index}].cases must be a positive integer")
        if not isinstance(events, int) or events < 0:
            raise ValueError(f"{target}[{index}].events must be a non-negative integer")
        risk_value = _require_numeric(risk, label=f"{target}[{index}].risk")
        if events > cases:
            issues.append(
                _issue(
                    rule_id="bar_events_exceed_cases",
                    message="bar events must not exceed cases",
                    target=f"{target}[{index}]",
                    observed={"cases": cases, "events": events},
                )
            )
        if not 0.0 <= risk_value <= 1.0:
            issues.append(
                _issue(
                    rule_id="bar_risk_out_of_range",
                    message="bar risk must lie within [0, 1]",
                    target=f"{target}[{index}]",
                    observed={"risk": risk_value},
                )
            )
        expected_risk = float(events) / float(cases)
        if abs(risk_value - expected_risk) > 1e-3:
            issues.append(
                _issue(
                    rule_id="bar_risk_mismatch",
                    message="bar risk must match events/cases",
                    target=f"{target}[{index}]",
                    observed={"risk": risk_value},
                    expected={"events_over_cases": expected_risk},
                )
            )
        if previous_risk is not None and risk_value < previous_risk:
            issues.append(
                _issue(
                    rule_id="bar_risk_non_monotonic",
                    message="risk layering bars must be monotonic non-decreasing",
                    target=f"{target}[{index}]",
                    observed={"risk": risk_value},
                    expected={"minimum_previous_risk": previous_risk},
                )
            )
        previous_risk = risk_value
    return issues
