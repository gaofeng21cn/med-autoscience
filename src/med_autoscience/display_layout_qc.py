from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import re
from typing import Any

from med_autoscience import display_readability_qc


ENGINE_ID = "display_layout_qc_v1"


@dataclass(frozen=True)
class Box:
    box_id: str
    box_type: str
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True)
class Device:
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True)
class LayoutSidecar:
    template_id: str
    device: Device
    layout_boxes: tuple[Box, ...]
    panel_boxes: tuple[Box, ...]
    guide_boxes: tuple[Box, ...]
    metrics: dict[str, Any]
    render_context: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _issue(
    *,
    rule_id: str,
    message: str,
    target: str,
    observed: object | None = None,
    expected: object | None = None,
    box_refs: tuple[str, ...] = (),
    severity: str = "error",
    audit_class: str = "layout",
) -> dict[str, Any]:
    issue: dict[str, Any] = {
        "audit_class": audit_class,
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "target": target,
    }
    if observed is not None:
        issue["observed"] = observed
    if expected is not None:
        issue["expected"] = expected
    if box_refs:
        issue["box_refs"] = list(box_refs)
    return issue


def _require_mapping(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return dict(value)


def _require_numeric(value: object, *, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{label} must be finite")
    return normalized


def _require_non_empty_text(value: object, *, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{label} must be non-empty")
    return normalized


def _normalize_device(payload: object) -> Device:
    data = _require_mapping(payload, label="layout_sidecar.device")
    if {"x0", "y0", "x1", "y1"} <= data.keys():
        device = Device(
            x0=_require_numeric(data["x0"], label="layout_sidecar.device.x0"),
            y0=_require_numeric(data["y0"], label="layout_sidecar.device.y0"),
            x1=_require_numeric(data["x1"], label="layout_sidecar.device.x1"),
            y1=_require_numeric(data["y1"], label="layout_sidecar.device.y1"),
        )
    elif {"width", "height"} <= data.keys():
        device = Device(
            x0=0.0,
            y0=0.0,
            x1=_require_numeric(data["width"], label="layout_sidecar.device.width"),
            y1=_require_numeric(data["height"], label="layout_sidecar.device.height"),
        )
    else:
        raise ValueError("layout_sidecar.device must provide either x0/y0/x1/y1 or width/height")
    if device.x1 <= device.x0 or device.y1 <= device.y0:
        raise ValueError("layout_sidecar.device must define a positive-area device")
    return device


def _normalize_box(payload: object, *, label: str) -> Box:
    data = _require_mapping(payload, label=label)
    box_id = str(data.get("box_id") or "").strip()
    box_type = str(data.get("box_type") or box_id).strip()
    if not box_id:
        raise ValueError(f"{label}.box_id must be non-empty")
    if not box_type:
        raise ValueError(f"{label}.box_type must be non-empty")
    x0 = _require_numeric(data.get("x0"), label=f"{label}.x0")
    y0 = _require_numeric(data.get("y0"), label=f"{label}.y0")
    x1 = _require_numeric(data.get("x1"), label=f"{label}.x1")
    y1 = _require_numeric(data.get("y1"), label=f"{label}.y1")
    if x1 < x0 or y1 < y0:
        raise ValueError(f"{label} must satisfy x0 <= x1 and y0 <= y1")
    return Box(box_id=box_id, box_type=box_type, x0=x0, y0=y0, x1=x1, y1=y1)


def _normalize_box_list(payload: object, *, label: str) -> tuple[Box, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, list):
        raise ValueError(f"{label} must be a list")
    return tuple(_normalize_box(item, label=f"{label}[{index}]") for index, item in enumerate(payload))


def _normalize_layout_sidecar(layout_sidecar: dict[str, object]) -> LayoutSidecar:
    data = _require_mapping(layout_sidecar, label="layout_sidecar")
    template_id = str(data.get("template_id") or "").strip()
    metrics = data.get("metrics")
    if not template_id:
        raise ValueError("layout_sidecar.template_id must be non-empty")
    return LayoutSidecar(
        template_id=template_id,
        device=_normalize_device(data.get("device")),
        layout_boxes=_normalize_box_list(data.get("layout_boxes"), label="layout_sidecar.layout_boxes"),
        panel_boxes=_normalize_box_list(data.get("panel_boxes"), label="layout_sidecar.panel_boxes"),
        guide_boxes=_normalize_box_list(data.get("guide_boxes"), label="layout_sidecar.guide_boxes"),
        metrics=_require_mapping(metrics, label="layout_sidecar.metrics"),
        render_context=_require_mapping(data.get("render_context") or {}, label="layout_sidecar.render_context"),
    )


def _all_boxes(sidecar: LayoutSidecar) -> tuple[Box, ...]:
    return sidecar.layout_boxes + sidecar.panel_boxes + sidecar.guide_boxes


def _boxes_of_type(boxes: tuple[Box, ...], box_type: str) -> tuple[Box, ...]:
    return tuple(box for box in boxes if box.box_type == box_type)


def _first_box_of_type(boxes: tuple[Box, ...], box_type: str) -> Box | None:
    matches = _boxes_of_type(boxes, box_type)
    return matches[0] if matches else None


def _curve_x_axis_titles(sidecar: LayoutSidecar) -> tuple[Box, ...]:
    return _boxes_of_type(sidecar.layout_boxes, "x_axis_title") + _boxes_of_type(
        sidecar.layout_boxes,
        "subplot_x_axis_title",
    )


def _curve_y_axis_titles(sidecar: LayoutSidecar) -> tuple[Box, ...]:
    return _boxes_of_type(sidecar.layout_boxes, "y_axis_title") + _boxes_of_type(
        sidecar.layout_boxes,
        "subplot_y_axis_title",
    )


def _layout_override_flag(sidecar: LayoutSidecar, key: str, default: bool = True) -> bool:
    render_context = sidecar.render_context
    layout_override = render_context.get("layout_override")
    if not isinstance(layout_override, dict):
        return default
    value = layout_override.get(key)
    if isinstance(value, bool):
        return value
    return default


def _primary_panel(sidecar: LayoutSidecar) -> Box | None:
    preferred = ("panel", "heatmap_tile_region")
    for box_type in preferred:
        box = _first_box_of_type(sidecar.panel_boxes, box_type)
        if box is not None:
            return box
    return sidecar.panel_boxes[0] if sidecar.panel_boxes else None


def _boxes_overlap(left: Box, right: Box) -> bool:
    return min(left.x1, right.x1) > max(left.x0, right.x0) and min(left.y1, right.y1) > max(left.y0, right.y0)


def _point_within_box(box: Box, *, x: float, y: float) -> bool:
    return box.x0 <= x <= box.x1 and box.y0 <= y <= box.y1


def _box_within_device(box: Box, device: Device) -> bool:
    return (
        device.x0 <= box.x0 <= device.x1
        and device.x0 <= box.x1 <= device.x1
        and device.y0 <= box.y0 <= device.y1
        and device.y0 <= box.y1 <= device.y1
    )


def _box_within_box(inner: Box, outer: Box) -> bool:
    return (
        outer.x0 <= inner.x0 <= outer.x1
        and outer.x0 <= inner.x1 <= outer.x1
        and outer.y0 <= inner.y0 <= outer.y1
        and outer.y0 <= inner.y1 <= outer.y1
    )


def _check_boxes_within_device(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for box in _all_boxes(sidecar):
        if _box_within_device(box, sidecar.device):
            continue
        issues.append(
            _issue(
                rule_id="box_out_of_device",
                message=f"box `{box.box_id}` must lie within the device bounds",
                target=box.box_type,
                observed={"x0": box.x0, "y0": box.y0, "x1": box.x1, "y1": box.y1},
                expected={"x0": sidecar.device.x0, "y0": sidecar.device.y0, "x1": sidecar.device.x1, "y1": sidecar.device.y1},
                box_refs=(box.box_id,),
            )
        )
    return issues


def _check_required_box_types(boxes: tuple[Box, ...], *, required_box_types: tuple[str, ...]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for box_type in required_box_types:
        if _boxes_of_type(boxes, box_type):
            continue
        issues.append(
            _issue(
                rule_id="missing_box",
                message=f"required box type `{box_type}` is missing",
                target=box_type,
                expected="present",
            )
        )
    return issues


def _check_pairwise_non_overlap(boxes: tuple[Box, ...], *, rule_id: str, target: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for index, left in enumerate(boxes):
        for right in boxes[index + 1 :]:
            if not _boxes_overlap(left, right):
                continue
            issues.append(
                _issue(
                    rule_id=rule_id,
                    message=f"`{left.box_id}` overlaps `{right.box_id}`",
                    target=target,
                    box_refs=(left.box_id, right.box_id),
                )
            )
    return issues


def _check_legend_panel_overlap(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    legend = _first_box_of_type(sidecar.guide_boxes, "legend")
    panels = sidecar.panel_boxes
    if not panels:
        primary_panel = _primary_panel(sidecar)
        panels = (primary_panel,) if primary_panel is not None else ()
    if not panels or legend is None:
        return []
    issues: list[dict[str, Any]] = []
    for panel in panels:
        if panel is None or not _boxes_overlap(legend, panel):
            continue
        issues.append(
            _issue(
                rule_id="legend_panel_overlap",
                message="legend box must not overlap the main panel",
                target="legend",
                box_refs=(legend.box_id, panel.box_id),
            )
        )
    return issues


def _check_colorbar_panel_overlap(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    colorbar = _first_box_of_type(sidecar.guide_boxes, "colorbar")
    panels = sidecar.panel_boxes
    if not panels:
        primary_panel = _primary_panel(sidecar)
        panels = (primary_panel,) if primary_panel is not None else ()
    if not panels or colorbar is None:
        return []
    issues: list[dict[str, Any]] = []
    for panel in panels:
        if panel is None or not _boxes_overlap(colorbar, panel):
            continue
        issues.append(
            _issue(
                rule_id="colorbar_panel_overlap",
                message="colorbar must not overlap the main panel",
                target="colorbar",
                box_refs=(colorbar.box_id, panel.box_id),
            )
        )
    return issues


def _check_curve_metrics(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
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


def _check_time_to_event_discrimination_calibration_metrics(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
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
                            target=f"metrics.calibration_summary[{index}].{field_name}",
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


def _check_reference_line_within_device(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    reference_line = sidecar.metrics.get("reference_line")
    if reference_line is None:
        return []
    if not isinstance(reference_line, dict):
        raise ValueError("layout_sidecar.metrics.reference_line must be an object when present")
    x_values = reference_line.get("x")
    y_values = reference_line.get("y")
    if not isinstance(x_values, list) or not isinstance(y_values, list):
        raise ValueError("layout_sidecar.metrics.reference_line must contain x and y lists")
    issues: list[dict[str, Any]] = []
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
                expected={"x0": sidecar.device.x0, "y0": sidecar.device.y0, "x1": sidecar.device.x1, "y1": sidecar.device.y1},
            )
        )
    return issues


def _check_curve_like_layout(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    issues.extend(_check_boxes_within_device(sidecar))
    if not _boxes_of_type(_all_boxes(sidecar), "title"):
        issues.append(
            _issue(
                rule_id="missing_box",
                message="required box type `title` is missing",
                target="title",
                expected="present",
            )
        )
    if not _curve_x_axis_titles(sidecar):
        issues.append(
            _issue(
                rule_id="missing_box",
                message="curve layout requires at least one x-axis title box",
                target="x_axis_title",
                expected="present",
            )
        )
    if not _curve_y_axis_titles(sidecar):
        issues.append(
            _issue(
                rule_id="missing_box",
                message="curve layout requires at least one y-axis title box",
                target="y_axis_title",
                expected="present",
            )
        )
    if _primary_panel(sidecar) is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="main panel box is required",
                target="panel",
                expected="present",
            )
        )
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {
            "title",
            "x_axis_title",
            "y_axis_title",
            "subplot_x_axis_title",
            "subplot_y_axis_title",
            "panel_title",
            "panel_label",
            "caption",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    return issues


def _check_composite_panel_label_anchors(
    sidecar: LayoutSidecar,
    *,
    label_panel_map: dict[str, str],
    allow_top_overhang_ratio: float = 0.0,
    allow_left_overhang_ratio: float = 0.0,
    max_left_offset_ratio: float = 0.08,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}

    for label_box_id, panel_box_id in label_panel_map.items():
        label_box = layout_boxes_by_id.get(label_box_id)
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="missing_panel_label",
                    message="composite audited panels require explicit panel labels",
                    target="layout_boxes",
                    expected=label_box_id,
                )
            )
            continue

        parent_panel = panel_boxes_by_id.get(panel_box_id)
        if parent_panel is None:
            continue

        panel_width = max(parent_panel.x1 - parent_panel.x0, 1e-9)
        panel_height = max(parent_panel.y1 - parent_panel.y0, 1e-9)
        allow_top_overhang = max(0.0, allow_top_overhang_ratio) * panel_height
        allow_left_overhang = max(0.0, allow_left_overhang_ratio) * panel_width
        if (
            label_box.x0 < parent_panel.x0 - allow_left_overhang
            or label_box.x1 > parent_panel.x1
            or label_box.y0 < parent_panel.y0
            or label_box.y1 > parent_panel.y1 + allow_top_overhang
        ):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="composite panel labels must stay within their declared panel region",
                    target="panel_label",
                    box_refs=(label_box.box_id, parent_panel.box_id),
                )
            )
            continue

        if (
            label_box.x0 > parent_panel.x0 + panel_width * max(0.0, max_left_offset_ratio)
            or label_box.y1 < parent_panel.y1 - panel_height * 0.10
        ):
            issues.append(
                _issue(
                    rule_id="panel_label_anchor_drift",
                    message="composite panel labels must stay near the parent panel top-left anchor",
                    target="panel_label",
                    box_refs=(label_box.box_id, parent_panel.box_id),
                )
            )

    return issues


def _panel_label_token(panel_label: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(panel_label)) or "panel"


def _check_publication_evidence_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_curve_like_layout(sidecar)
    if not _layout_override_flag(sidecar, "show_figure_title", False):
        issues = [
            issue
            for issue in issues
            if not (issue.get("rule_id") == "missing_box" and issue.get("target") == "title")
        ]
    issues.extend(_check_legend_panel_overlap(sidecar))
    if sidecar.template_id == "time_to_event_discrimination_calibration_panel":
        if len(sidecar.panel_boxes) < 2:
            issues.append(
                _issue(
                    rule_id="composite_panels_missing",
                    message="time-to-event discrimination/calibration panel requires left and right panels",
                    target="panel_boxes",
                    expected={"minimum_count": 2},
                    observed={"count": len(sidecar.panel_boxes)},
                )
            )
        issues.extend(_check_time_to_event_discrimination_calibration_metrics(sidecar.metrics))
        discrimination_points = sidecar.metrics.get("discrimination_points")
        calibration_summary = sidecar.metrics.get("calibration_summary")
        expected_marker_count = 0
        if isinstance(discrimination_points, list):
            expected_marker_count += len(discrimination_points)
        if isinstance(calibration_summary, list):
            expected_marker_count += len(calibration_summary) * 2
        metric_marker_count = len(_boxes_of_type(sidecar.layout_boxes, "metric_marker"))
        if expected_marker_count and metric_marker_count < expected_marker_count:
            issues.append(
                _issue(
                    rule_id="metric_markers_incomplete",
                    message="time-to-event discrimination/calibration panel requires marker boxes for all summary points",
                    target="layout_boxes",
                    observed={"metric_marker_count": metric_marker_count},
                    expected={"minimum_count": expected_marker_count},
                )
            )
        annotation = _first_box_of_type(sidecar.layout_boxes, "annotation_block")
        legend = _first_box_of_type(sidecar.guide_boxes, "legend")
        if annotation is not None:
            panel_titles = _boxes_of_type(sidecar.layout_boxes, "panel_title")
            overlapped_panels = [panel for panel in sidecar.panel_boxes if _boxes_overlap(annotation, panel)]
            containing_panels = [panel for panel in sidecar.panel_boxes if _box_within_box(annotation, panel)]
            expected_callout_panel = next((panel for panel in sidecar.panel_boxes if panel.box_id == "panel_right"), None)
            if len(overlapped_panels) > 1:
                issues.append(
                    _issue(
                        rule_id="annotation_cross_panel_overlap",
                        message="calibration callout must stay within a single blank region rather than spanning multiple panels",
                        target="annotation_block",
                        box_refs=tuple(box.box_id for box in overlapped_panels),
                    )
                )
            if not containing_panels:
                issues.append(
                    _issue(
                        rule_id="annotation_out_of_panel",
                        message="calibration callout must stay fully inside a single panel canvas",
                        target="annotation_block",
                        box_refs=(annotation.box_id,),
                    )
                )
            elif expected_callout_panel is not None and not _box_within_box(annotation, expected_callout_panel):
                issues.append(
                    _issue(
                        rule_id="annotation_wrong_panel",
                        message="calibration callout must stay in Panel B (the grouped-calibration panel)",
                        target="annotation_block",
                        box_refs=(annotation.box_id, expected_callout_panel.box_id),
                    )
                )
            if panel_titles and annotation.y1 > min(panel_title.y0 for panel_title in panel_titles):
                issues.append(
                    _issue(
                        rule_id="annotation_header_band",
                        message="calibration callout must stay below the panel-title header band",
                        target="annotation_block",
                        box_refs=(annotation.box_id,),
                    )
                )
            for panel_title in panel_titles:
                if not _boxes_overlap(annotation, panel_title):
                    continue
                issues.append(
                    _issue(
                        rule_id="annotation_title_overlap",
                        message="calibration callout must not overlap the panel title",
                        target="annotation_block",
                        box_refs=(annotation.box_id, panel_title.box_id),
                    )
                )
            for marker_box in _boxes_of_type(sidecar.layout_boxes, "metric_marker"):
                if not _boxes_overlap(annotation, marker_box):
                    continue
                issues.append(
                    _issue(
                        rule_id="annotation_metric_overlap",
                        message="calibration callout must not overlap evidence markers",
                        target="annotation_block",
                        box_refs=(annotation.box_id, marker_box.box_id),
                    )
                )
            if legend is not None and _boxes_overlap(annotation, legend):
                issues.append(
                    _issue(
                        rule_id="annotation_legend_overlap",
                        message="calibration callout must not overlap the legend",
                        target="annotation_block",
                        box_refs=(annotation.box_id, legend.box_id),
                    )
                )
        return issues

    if sidecar.template_id == "time_dependent_roc_comparison_panel":
        issues.extend(_check_time_dependent_roc_comparison_panel_metrics(sidecar))
        return issues

    issues.extend(_check_curve_metrics(sidecar.metrics))
    issues.extend(_check_reference_line_within_device(sidecar))
    if sidecar.template_id == "time_dependent_roc_horizon":
        time_horizon_months = sidecar.metrics.get("time_horizon_months")
        if time_horizon_months is None:
            issues.append(
                _issue(
                    rule_id="time_horizon_months_missing",
                    message="time-dependent ROC horizon outputs must carry structured time_horizon_months semantics",
                    target="metrics.time_horizon_months",
                )
            )
        else:
            normalized_time_horizon_months = _require_numeric(
                time_horizon_months,
                label="layout_sidecar.metrics.time_horizon_months",
            )
            if not float(normalized_time_horizon_months).is_integer() or int(normalized_time_horizon_months) <= 0:
                issues.append(
                    _issue(
                        rule_id="time_horizon_months_invalid",
                        message="time_horizon_months must be a positive integer",
                        target="metrics.time_horizon_months",
                        observed=time_horizon_months,
                    )
                )
    return issues


def _check_publication_decision_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_publication_evidence_curve(sidecar)
    if sidecar.template_id != "time_to_event_decision_curve":
        return issues

    if len(sidecar.panel_boxes) < 2:
        issues.append(
            _issue(
                rule_id="treated_fraction_panel_missing",
                message="time-to-event decision curve requires a treated-fraction companion panel",
                target="panel_boxes",
                expected={"minimum_count": 2},
                observed={"count": len(sidecar.panel_boxes)},
            )
        )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_left",
                "panel_label_B": "panel_right",
            },
        )
    )

    treated_fraction_series = sidecar.metrics.get("treated_fraction_series")
    if not isinstance(treated_fraction_series, dict):
        issues.append(
            _issue(
                rule_id="treated_fraction_series_missing",
                message="time-to-event decision curve requires treated_fraction_series metrics",
                target="metrics.treated_fraction_series",
            )
        )
        return issues

    x_values = treated_fraction_series.get("x")
    y_values = treated_fraction_series.get("y")
    if not isinstance(x_values, list) or not isinstance(y_values, list):
        raise ValueError("layout_sidecar.metrics.treated_fraction_series must contain x and y lists")
    if len(x_values) != len(y_values):
        issues.append(
            _issue(
                rule_id="treated_fraction_length_mismatch",
                message="treated fraction x/y lengths must match",
                target="metrics.treated_fraction_series",
                observed={"x": len(x_values), "y": len(y_values)},
            )
        )
        return issues

    for index, (x_value, y_value) in enumerate(zip(x_values, y_values, strict=True)):
        x_numeric = _require_numeric(x_value, label=f"layout_sidecar.metrics.treated_fraction_series.x[{index}]")
        y_numeric = _require_numeric(y_value, label=f"layout_sidecar.metrics.treated_fraction_series.y[{index}]")
        if math.isfinite(x_numeric) and math.isfinite(y_numeric):
            continue
        issues.append(
            _issue(
                rule_id="treated_fraction_non_finite",
                message="treated fraction coordinates must be finite",
                target="metrics.treated_fraction_series",
            )
        )
        break

    return issues


def _check_curve_series_collection(series: object, *, target: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
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


def _check_time_dependent_roc_comparison_panel_metrics(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
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
        issues.extend(
            _check_curve_series_collection(
                panel_series,
                target=f"metrics.panels[{panel_index}].series",
            )
        )
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
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
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


def _check_publication_binary_calibration_decision_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["subplot_x_axis_title", "subplot_y_axis_title"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    calibration_panel = _first_box_of_type(sidecar.panel_boxes, "calibration_panel")
    decision_panel = _first_box_of_type(sidecar.panel_boxes, "decision_panel")
    if calibration_panel is None:
        issues.append(
            _issue(
                rule_id="calibration_panel_missing",
                message="binary calibration/decision panel requires a calibration panel box",
                target="panel_boxes",
                expected="calibration_panel",
            )
        )
    if decision_panel is None:
        issues.append(
            _issue(
                rule_id="decision_panel_missing",
                message="binary calibration/decision panel requires a decision panel box",
                target="panel_boxes",
                expected="decision_panel",
            )
        )
    if len(sidecar.panel_boxes) < 2:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="binary calibration/decision panel requires two panel boxes",
                target="panel_boxes",
                observed={"count": len(sidecar.panel_boxes)},
                expected={"minimum_count": 2},
            )
        )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "subplot_title", "subplot_x_axis_title", "subplot_y_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    calibration_axis_window = sidecar.metrics.get("calibration_axis_window")
    if not isinstance(calibration_axis_window, dict):
        issues.append(
            _issue(
                rule_id="calibration_axis_window_missing",
                message="binary calibration/decision panel requires an explicit calibration_axis_window metric",
                target="metrics.calibration_axis_window",
            )
        )
    else:
        xmin = _require_numeric(calibration_axis_window.get("xmin"), label="metrics.calibration_axis_window.xmin")
        xmax = _require_numeric(calibration_axis_window.get("xmax"), label="metrics.calibration_axis_window.xmax")
        ymin = _require_numeric(calibration_axis_window.get("ymin"), label="metrics.calibration_axis_window.ymin")
        ymax = _require_numeric(calibration_axis_window.get("ymax"), label="metrics.calibration_axis_window.ymax")
        if xmin >= xmax or ymin >= ymax:
            issues.append(
                _issue(
                    rule_id="calibration_axis_window_invalid",
                    message="calibration axis window must be strictly increasing on both axes",
                    target="metrics.calibration_axis_window",
                    observed={"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
                )
            )
        else:
            calibration_series = sidecar.metrics.get("calibration_series")
            if isinstance(calibration_series, list):
                for series_index, series in enumerate(calibration_series):
                    if not isinstance(series, dict):
                        continue
                    x_values = series.get("x")
                    y_values = series.get("y")
                    if not isinstance(x_values, list) or not isinstance(y_values, list):
                        continue
                    for point_index, (x_value, y_value) in enumerate(zip(x_values, y_values, strict=True)):
                        x_numeric = _require_numeric(
                            x_value,
                            label=f"metrics.calibration_series[{series_index}].x[{point_index}]",
                        )
                        y_numeric = _require_numeric(
                            y_value,
                            label=f"metrics.calibration_series[{series_index}].y[{point_index}]",
                        )
                        if xmin <= x_numeric <= xmax and ymin <= y_numeric <= ymax:
                            continue
                        issues.append(
                            _issue(
                                rule_id="calibration_axis_window_excludes_data",
                                message="calibration axis window must cover every audited calibration point",
                                target=f"metrics.calibration_series[{series_index}]",
                                observed={"x": x_numeric, "y": y_numeric},
                                expected={"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
                            )
                        )
                        break
    issues.extend(_check_curve_series_collection(sidecar.metrics.get("calibration_series"), target="metrics.calibration_series"))
    issues.extend(_check_curve_series_collection(sidecar.metrics.get("decision_series"), target="metrics.decision_series"))

    calibration_reference_line = sidecar.metrics.get("calibration_reference_line")
    if calibration_reference_line is not None:
        issues.extend(
            _check_reference_line_collection_within_device(
                [calibration_reference_line],
                sidecar=sidecar,
                target="metrics.calibration_reference_line",
            )
        )
    issues.extend(
        _check_reference_line_collection_within_device(
            sidecar.metrics.get("decision_reference_lines"),
            sidecar=sidecar,
            target="metrics.decision_reference_lines",
        )
    )

    focus_window = sidecar.metrics.get("decision_focus_window")
    if not isinstance(focus_window, dict):
        issues.append(
            _issue(
                rule_id="focus_window_missing",
                message="decision focus window metrics are required",
                target="metrics.decision_focus_window",
            )
        )
    else:
        xmin = _require_numeric(focus_window.get("xmin"), label="metrics.decision_focus_window.xmin")
        xmax = _require_numeric(focus_window.get("xmax"), label="metrics.decision_focus_window.xmax")
        if xmin >= xmax:
            issues.append(
                _issue(
                    rule_id="focus_window_invalid",
                    message="decision focus window xmin must be < xmax",
                    target="metrics.decision_focus_window",
                    observed={"xmin": xmin, "xmax": xmax},
                )
            )

    focus_window_box = _first_box_of_type(sidecar.guide_boxes, "focus_window")
    if focus_window_box is None:
        issues.append(
            _issue(
                rule_id="focus_window_box_missing",
                message="decision focus window guide box is required",
                target="guide_boxes",
                expected="focus_window",
            )
        )
    elif decision_panel is not None:
        epsilon = 1e-9
        focus_within_panel = (
            decision_panel.x0 - epsilon <= focus_window_box.x0 <= decision_panel.x1 + epsilon
            and decision_panel.x0 - epsilon <= focus_window_box.x1 <= decision_panel.x1 + epsilon
            and decision_panel.y0 - epsilon <= focus_window_box.y0 <= decision_panel.y1 + epsilon
            and decision_panel.y0 - epsilon <= focus_window_box.y1 <= decision_panel.y1 + epsilon
        )
        if not focus_within_panel:
            issues.append(
                _issue(
                    rule_id="focus_window_outside_panel",
                    message="decision focus window must stay within the decision panel",
                    target="focus_window",
                    box_refs=(focus_window_box.box_id, decision_panel.box_id),
                )
            )

    return issues


def _check_risk_layering_bar_metrics(
    bars: object,
    *,
    target: str,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
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


def _check_publication_risk_layering_bars(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["y_axis_title", "panel", "risk_bar"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    if len(sidecar.panel_boxes) < 2:
        issues.append(
            _issue(
                rule_id="risk_layering_panel_missing",
                message="risk layering bars require left and right panels",
                target="panel_boxes",
                expected={"minimum_count": 2},
                observed={"count": len(sidecar.panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    issues.extend(
        _check_risk_layering_bar_metrics(sidecar.metrics.get("left_bars"), target="metrics.left_bars")
    )
    issues.extend(
        _check_risk_layering_bar_metrics(sidecar.metrics.get("right_bars"), target="metrics.right_bars")
    )
    return issues


def _check_publication_survival_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_curve_like_layout(sidecar)
    if not _layout_override_flag(sidecar, "show_figure_title", False):
        issues = [
            issue
            for issue in issues
            if not (issue.get("rule_id") == "missing_box" and issue.get("target") == "title")
        ]
    issues.extend(_check_legend_panel_overlap(sidecar))

    annotation = _first_box_of_type(sidecar.guide_boxes + sidecar.layout_boxes, "annotation_block")
    legend = _first_box_of_type(sidecar.guide_boxes, "legend")
    panels = sidecar.panel_boxes
    if not panels:
        primary_panel = _primary_panel(sidecar)
        panels = (primary_panel,) if primary_panel is not None else ()
    if annotation is not None:
        for panel in panels:
            if panel is None or not _boxes_overlap(annotation, panel):
                continue
            issues.append(
                _issue(
                    rule_id="annotation_panel_overlap",
                    message="annotation block must not overlap the panel",
                    target="annotation_block",
                    box_refs=(annotation.box_id, panel.box_id),
                )
            )
    if annotation is not None and legend is not None and _boxes_overlap(annotation, legend):
        issues.append(
            _issue(
                rule_id="annotation_legend_overlap",
                message="annotation block must not overlap the legend",
                target="annotation_block",
                box_refs=(annotation.box_id, legend.box_id),
            )
        )

    if sidecar.template_id == "time_to_event_risk_group_summary":
        if len(sidecar.panel_boxes) < 2:
            issues.append(
                _issue(
                    rule_id="composite_panels_missing",
                    message="time-to-event risk-group summary requires two panel boxes",
                    target="panel_boxes",
                    expected={"minimum_count": 2},
                    observed={"count": len(sidecar.panel_boxes)},
                )
            )
        issues.extend(
            _check_composite_panel_label_anchors(
                sidecar,
                label_panel_map={
                    "panel_label_A": "panel_left",
                    "panel_label_B": "panel_right",
                },
            )
        )
        risk_group_summaries = sidecar.metrics.get("risk_group_summaries")
        if not isinstance(risk_group_summaries, list) or not risk_group_summaries:
            issues.append(
                _issue(
                    rule_id="risk_group_summaries_missing",
                    message="risk-group summary qc requires non-empty risk_group_summaries metrics",
                    target="metrics.risk_group_summaries",
                )
            )
            return issues
        for index, item in enumerate(risk_group_summaries):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.risk_group_summaries[{index}] must be an object")
            group_label = str(item.get("label") or "").strip()
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="risk_group_label_missing",
                        message="risk-group summary labels must be non-empty",
                        target=f"metrics.risk_group_summaries[{index}].label",
                    )
                )
            sample_size = _require_numeric(
                item.get("sample_size"),
                label=f"layout_sidecar.metrics.risk_group_summaries[{index}].sample_size",
            )
            event_count = _require_numeric(
                item.get("events_5y"),
                label=f"layout_sidecar.metrics.risk_group_summaries[{index}].events_5y",
            )
            predicted_risk = _require_numeric(
                item.get("mean_predicted_risk_5y"),
                label=f"layout_sidecar.metrics.risk_group_summaries[{index}].mean_predicted_risk_5y",
            )
            observed_risk = _require_numeric(
                item.get("observed_km_risk_5y"),
                label=f"layout_sidecar.metrics.risk_group_summaries[{index}].observed_km_risk_5y",
            )
            if sample_size <= 0:
                issues.append(
                    _issue(
                        rule_id="risk_group_sample_size_non_positive",
                        message="risk-group sample_size must be positive",
                        target=f"metrics.risk_group_summaries[{index}].sample_size",
                    )
                )
            if event_count < 0:
                issues.append(
                    _issue(
                        rule_id="risk_group_event_count_negative",
                        message="risk-group events_5y must be non-negative",
                        target=f"metrics.risk_group_summaries[{index}].events_5y",
                    )
                )
            if not math.isfinite(predicted_risk) or not math.isfinite(observed_risk):
                issues.append(
                    _issue(
                        rule_id="risk_group_risk_non_finite",
                        message="risk-group summary risks must be finite",
                        target=f"metrics.risk_group_summaries[{index}]",
                    )
                )
        return issues

    if sidecar.template_id == "time_to_event_stratified_cumulative_incidence_panel":
        panel_metrics = sidecar.metrics.get("panels")
        if not isinstance(panel_metrics, list) or not panel_metrics:
            issues.append(
                _issue(
                    rule_id="panel_metrics_missing",
                    message="stratified cumulative-incidence qc requires non-empty panel metrics",
                    target="metrics.panels",
                )
            )
            return issues
        if len(sidecar.panel_boxes) != len(panel_metrics):
            issues.append(
                _issue(
                    rule_id="composite_panels_missing",
                    message="stratified cumulative-incidence qc requires one panel box per declared panel",
                    target="panel_boxes",
                    expected={"count": len(panel_metrics)},
                    observed={"count": len(sidecar.panel_boxes)},
                )
            )
        label_panel_map: dict[str, str] = {}
        layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
        seen_panel_labels: set[str] = set()
        for panel_index, panel in enumerate(panel_metrics):
            if not isinstance(panel, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
            panel_label = str(panel.get("panel_label") or "").strip()
            if not panel_label:
                issues.append(
                    _issue(
                        rule_id="panel_label_missing",
                        message="stratified cumulative-incidence panels require non-empty panel_label metrics",
                        target=f"metrics.panels[{panel_index}].panel_label",
                    )
                )
                continue
            if panel_label in seen_panel_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_panel_label",
                        message="stratified cumulative-incidence panel labels must be unique",
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
                        message="stratified cumulative-incidence panels require explicit panel titles",
                        target="layout_boxes",
                        expected=f"panel_title_{panel_label_token}",
                    )
                )
            groups = panel.get("groups")
            if not isinstance(groups, list) or not groups:
                issues.append(
                    _issue(
                        rule_id="groups_missing",
                        message="stratified cumulative-incidence panel requires non-empty groups",
                        target=f"metrics.panels[{panel_index}].groups",
                    )
                )
                continue
            seen_group_labels: set[str] = set()
            for group_index, group in enumerate(groups):
                if not isinstance(group, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}] must be an object")
                group_label = str(group.get("label") or "").strip()
                if not group_label:
                    issues.append(
                        _issue(
                            rule_id="group_label_missing",
                            message="panel group labels must be non-empty",
                            target=f"metrics.panels[{panel_index}].groups[{group_index}].label",
                        )
                    )
                elif group_label in seen_group_labels:
                    issues.append(
                        _issue(
                            rule_id="duplicate_group_label",
                            message="panel group labels must be unique within each panel",
                            target=f"metrics.panels[{panel_index}].groups",
                            observed=group_label,
                        )
                    )
                else:
                    seen_group_labels.add(group_label)
                times = group.get("times")
                values = group.get("values")
                if not isinstance(times, list) or not isinstance(values, list):
                    raise ValueError(
                        f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}] must contain times and values lists"
                    )
                if len(times) != len(values):
                    issues.append(
                        _issue(
                            rule_id="group_length_mismatch",
                            message="panel group times/values lengths must match",
                            target=f"metrics.panels[{panel_index}].groups[{group_index}]",
                            observed={"times": len(times), "values": len(values)},
                        )
                    )
                    continue
                previous_time: float | None = None
                previous_value: float | None = None
                for point_index, (time_value, probability_value) in enumerate(zip(times, values, strict=True)):
                    time_numeric = _require_numeric(
                        time_value,
                        label=f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}].times[{point_index}]",
                    )
                    probability_numeric = _require_numeric(
                        probability_value,
                        label=f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}].values[{point_index}]",
                    )
                    if previous_time is not None and time_numeric <= previous_time:
                        issues.append(
                            _issue(
                                rule_id="group_times_not_strictly_increasing",
                                message="panel group times must be strictly increasing",
                                target=f"metrics.panels[{panel_index}].groups[{group_index}].times",
                            )
                        )
                        break
                    if probability_numeric < 0.0 or probability_numeric > 1.0:
                        issues.append(
                            _issue(
                                rule_id="group_probability_out_of_range",
                                message="panel group cumulative incidence must stay within [0, 1]",
                                target=f"metrics.panels[{panel_index}].groups[{group_index}].values[{point_index}]",
                                observed=probability_numeric,
                            )
                        )
                        break
                    if previous_value is not None and probability_numeric + 1e-12 < previous_value:
                        issues.append(
                            _issue(
                                rule_id="group_values_not_monotonic",
                                message="panel group cumulative incidence must be monotonic non-decreasing",
                                target=f"metrics.panels[{panel_index}].groups[{group_index}].values",
                            )
                        )
                        break
                    previous_time = time_numeric
                    previous_value = probability_numeric
        issues.extend(_check_composite_panel_label_anchors(sidecar, label_panel_map=label_panel_map))
        return issues

    groups = sidecar.metrics.get("groups")
    if not isinstance(groups, list) or not groups:
        issues.append(
            _issue(
                rule_id="groups_missing",
                message="survival qc requires at least one group",
                target="metrics.groups",
            )
        )
        return issues
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ValueError(f"layout_sidecar.metrics.groups[{index}] must be an object")
        times = group.get("times")
        values = group.get("values")
        if not isinstance(times, list) or not isinstance(values, list):
            raise ValueError(f"layout_sidecar.metrics.groups[{index}] must contain times and values lists")
        if len(times) != len(values):
            issues.append(
                _issue(
                    rule_id="group_length_mismatch",
                    message="group times/values lengths must match",
                    target=f"metrics.groups[{index}]",
                    observed={"times": len(times), "values": len(values)},
                )
            )
            continue
        for point_index, (time_value, probability_value) in enumerate(zip(times, values, strict=True)):
            _require_numeric(time_value, label=f"layout_sidecar.metrics.groups[{index}].times[{point_index}]")
            _require_numeric(probability_value, label=f"layout_sidecar.metrics.groups[{index}].values[{point_index}]")
    return issues


def _check_publication_embedding_scatter(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("title", "x_axis_title", "y_axis_title", "legend")))
    panel = _primary_panel(sidecar)
    if panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="embedding scatter requires a panel box",
                target="panel",
                expected="present",
            )
        )
        return issues
    issues.extend(_check_legend_panel_overlap(sidecar))

    points = sidecar.metrics.get("points")
    if not isinstance(points, list) or not points:
        issues.append(
            _issue(
                rule_id="points_missing",
                message="embedding scatter requires non-empty point metrics",
                target="metrics.points",
            )
        )
        return issues
    group_labels = sidecar.metrics.get("group_labels")
    if group_labels is not None:
        if not isinstance(group_labels, list):
            raise ValueError("layout_sidecar.metrics.group_labels must be a list when present")
        seen_group_labels: set[str] = set()
        for index, item in enumerate(group_labels):
            group_label = str(item).strip()
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="empty_group_label",
                        message="group labels must be non-empty",
                        target=f"metrics.group_labels[{index}]",
                    )
                )
                continue
            if group_label in seen_group_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_group_label",
                        message=f"group label `{group_label}` must be unique",
                        target="metrics.group_labels",
                        observed=group_label,
                    )
                )
                continue
            seen_group_labels.add(group_label)
    for index, point in enumerate(points):
        if not isinstance(point, dict):
            raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
        group = str(point.get("group") or "").strip()
        if not group:
            issues.append(
                _issue(
                    rule_id="empty_group_label",
                    message="group labels must be non-empty",
                    target=f"metrics.points[{index}].group",
                )
            )
        x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.points[{index}].x")
        y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
        if _point_within_box(panel, x=x_value, y=y_value):
            continue
        issues.append(
            _issue(
                rule_id="point_out_of_panel",
                message="embedding point must stay within the panel domain",
                target=f"metrics.points[{index}]",
                observed={"x": x_value, "y": y_value},
                box_refs=(panel.box_id,),
            )
        )
    return issues


def _check_publication_celltype_signature_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    left_panel = panel_boxes_by_id.get("panel_left") or _first_box_of_type(sidecar.panel_boxes, "panel")
    right_panel = panel_boxes_by_id.get("panel_right") or _first_box_of_type(sidecar.panel_boxes, "heatmap_tile_region")
    if left_panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="celltype-signature panel requires a left embedding panel",
                target="panel_left",
                expected="present",
            )
        )
    if right_panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="celltype-signature panel requires a right heatmap tile region",
                target="panel_right",
                expected="present",
            )
        )
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={"panel_label_A": "panel_left", "panel_label_B": "panel_right"},
        )
    )

    points = sidecar.metrics.get("points")
    if not isinstance(points, list) or not points:
        issues.append(
            _issue(
                rule_id="points_missing",
                message="celltype-signature panel requires non-empty embedding point metrics",
                target="metrics.points",
            )
        )
    elif left_panel is not None:
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
            group = str(point.get("group") or "").strip()
            if not group:
                issues.append(
                    _issue(
                        rule_id="empty_group_label",
                        message="group labels must be non-empty",
                        target=f"metrics.points[{index}].group",
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
            if _point_within_box(left_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="point_out_of_panel",
                    message="embedding point must stay within the left panel domain",
                    target=f"metrics.points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(left_panel.box_id,),
                )
            )

    group_labels = sidecar.metrics.get("group_labels")
    if group_labels is not None:
        if not isinstance(group_labels, list):
            raise ValueError("layout_sidecar.metrics.group_labels must be a list when present")
        seen_group_labels: set[str] = set()
        for index, item in enumerate(group_labels):
            group_label = str(item).strip()
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="empty_group_label",
                        message="group labels must be non-empty",
                        target=f"metrics.group_labels[{index}]",
                    )
                )
                continue
            if group_label in seen_group_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_group_label",
                        message=f"group label `{group_label}` must be unique",
                        target="metrics.group_labels",
                        observed=group_label,
                    )
                )
                continue
            seen_group_labels.add(group_label)

    score_method = str(sidecar.metrics.get("score_method") or "").strip()
    if not score_method:
        issues.append(
            _issue(
                rule_id="score_method_missing",
                message="celltype-signature panel requires a non-empty score_method",
                target="metrics.score_method",
            )
        )
    _matrix_cell_lookup(sidecar.metrics)
    return issues


def _check_publication_single_cell_atlas_overview_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_embedding",
                "panel_label_B": "panel_composition",
                "panel_label_C": "panel_heatmap",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    embedding_panel = panel_boxes_by_id.get("panel_embedding") or _first_box_of_type(sidecar.panel_boxes, "panel")
    composition_panel = panel_boxes_by_id.get("panel_composition") or _first_box_of_type(
        sidecar.panel_boxes, "composition_panel"
    )
    heatmap_panel = panel_boxes_by_id.get("panel_heatmap") or _first_box_of_type(
        sidecar.panel_boxes, "heatmap_tile_region"
    )
    for panel_box, target, message in (
        (embedding_panel, "panel_embedding", "single-cell atlas overview requires an embedding panel"),
        (composition_panel, "panel_composition", "single-cell atlas overview requires a composition panel"),
        (heatmap_panel, "panel_heatmap", "single-cell atlas overview requires a heatmap panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    state_labels = sidecar.metrics.get("state_labels")
    if not isinstance(state_labels, list) or not state_labels:
        issues.append(
            _issue(
                rule_id="state_labels_missing",
                message="single-cell atlas overview requires explicit non-empty state_labels metrics",
                target="metrics.state_labels",
            )
        )
        normalized_state_labels: list[str] = []
    else:
        normalized_state_labels = []
        seen_state_labels: set[str] = set()
        for index, item in enumerate(state_labels):
            state_label = str(item or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="state labels must be non-empty",
                        target=f"metrics.state_labels[{index}]",
                    )
                )
                continue
            if state_label in seen_state_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_state_label",
                        message=f"state label `{state_label}` must be unique",
                        target="metrics.state_labels",
                        observed=state_label,
                    )
                )
                continue
            seen_state_labels.add(state_label)
            normalized_state_labels.append(state_label)

    row_labels = sidecar.metrics.get("row_labels")
    if not isinstance(row_labels, list) or not row_labels:
        issues.append(
            _issue(
                rule_id="row_labels_missing",
                message="single-cell atlas overview requires explicit non-empty row_labels metrics",
                target="metrics.row_labels",
            )
        )
        normalized_row_labels: list[str] = []
    else:
        normalized_row_labels = []
        seen_row_labels: set[str] = set()
        for index, item in enumerate(row_labels):
            row_label = str(item or "").strip()
            if not row_label:
                issues.append(
                    _issue(
                        rule_id="empty_row_label",
                        message="heatmap row labels must be non-empty",
                        target=f"metrics.row_labels[{index}]",
                    )
                )
                continue
            if row_label in seen_row_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_row_label",
                        message=f"heatmap row label `{row_label}` must be unique",
                        target="metrics.row_labels",
                        observed=row_label,
                    )
                )
                continue
            seen_row_labels.add(row_label)
            normalized_row_labels.append(row_label)

    points = sidecar.metrics.get("points")
    if not isinstance(points, list) or not points:
        issues.append(
            _issue(
                rule_id="points_missing",
                message="single-cell atlas overview requires non-empty embedding point metrics",
                target="metrics.points",
            )
        )
    elif embedding_panel is not None:
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="embedding point state_label must be non-empty",
                        target=f"metrics.points[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id="point_state_label_unknown",
                        message="embedding point state_label must stay inside declared state_labels",
                        target=f"metrics.points[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
            if _point_within_box(embedding_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="point_out_of_panel",
                    message="embedding point must stay within the embedding panel domain",
                    target=f"metrics.points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(embedding_panel.box_id,),
                )
            )

    composition_groups = sidecar.metrics.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        issues.append(
            _issue(
                rule_id="composition_groups_missing",
                message="single-cell atlas overview requires non-empty composition_groups metrics",
                target="metrics.composition_groups",
            )
        )
    else:
        seen_group_labels: set[str] = set()
        previous_group_order = 0.0
        expected_state_set = set(normalized_state_labels)
        for group_index, item in enumerate(composition_groups):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.composition_groups[{group_index}] must be an object")
            group_label = str(item.get("group_label") or "").strip()
            group_order = _require_numeric(
                item.get("group_order"),
                label=f"layout_sidecar.metrics.composition_groups[{group_index}].group_order",
            )
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="composition_group_label_missing",
                        message="composition group_label must be non-empty",
                        target=f"metrics.composition_groups[{group_index}].group_label",
                    )
                )
            elif group_label in seen_group_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_composition_group_label",
                        message=f"composition group label `{group_label}` must be unique",
                        target="metrics.composition_groups",
                        observed=group_label,
                    )
                )
            else:
                seen_group_labels.add(group_label)
            if group_order <= previous_group_order:
                issues.append(
                    _issue(
                        rule_id="composition_group_order_not_increasing",
                        message="composition group_order must stay strictly increasing",
                        target="metrics.composition_groups",
                    )
                )
            previous_group_order = group_order
            state_proportions = item.get("state_proportions")
            if not isinstance(state_proportions, list) or not state_proportions:
                issues.append(
                    _issue(
                        rule_id="composition_group_state_proportions_missing",
                        message="composition groups require non-empty state_proportions",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                    )
                )
                continue
            observed_state_set: set[str] = set()
            total = 0.0
            for state_index, state_item in enumerate(state_proportions):
                if not isinstance(state_item, dict):
                    raise ValueError(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].state_proportions[{state_index}] must be an object"
                    )
                state_label = str(state_item.get("state_label") or "").strip()
                if state_label:
                    observed_state_set.add(state_label)
                proportion = _require_numeric(
                    state_item.get("proportion"),
                    label=(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].state_proportions[{state_index}].proportion"
                    ),
                )
                total += proportion
                if 0.0 <= proportion <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id="composition_proportion_out_of_range",
                        message="composition proportion must stay within [0, 1]",
                        target=f"metrics.composition_groups[{group_index}].state_proportions[{state_index}].proportion",
                        observed=proportion,
                    )
                )
            if expected_state_set and observed_state_set != expected_state_set:
                issues.append(
                    _issue(
                        rule_id="composition_group_state_set_mismatch",
                        message="composition state set must match declared state_labels",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                        observed=sorted(observed_state_set),
                        expected=sorted(expected_state_set),
                    )
                )
            if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                issues.append(
                    _issue(
                        rule_id="composition_group_sum_invalid",
                        message="composition state proportions must sum to 1",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                        observed=total,
                        expected=1.0,
                    )
                )

    matrix_lookup = _matrix_cell_lookup(sidecar.metrics)
    matrix_state_labels = {state_label for state_label, _ in matrix_lookup}
    matrix_row_labels = {row_label for _, row_label in matrix_lookup}
    if normalized_state_labels and matrix_state_labels != set(normalized_state_labels):
        issues.append(
            _issue(
                rule_id="heatmap_state_set_mismatch",
                message="heatmap cell x labels must match declared state_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_state_labels),
                expected=sorted(normalized_state_labels),
            )
        )
    if normalized_row_labels and matrix_row_labels != set(normalized_row_labels):
        issues.append(
            _issue(
                rule_id="heatmap_row_set_mismatch",
                message="heatmap cell y labels must match declared row_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_row_labels),
                expected=sorted(normalized_row_labels),
            )
        )
    expected_cell_count = len(normalized_state_labels) * len(normalized_row_labels)
    if expected_cell_count > 0 and len(matrix_lookup) != expected_cell_count:
        issues.append(
            _issue(
                rule_id="heatmap_grid_incomplete",
                message="heatmap grid must cover every declared state/row coordinate exactly once",
                target="metrics.matrix_cells",
                observed={"cells": len(matrix_lookup)},
                expected={"cells": expected_cell_count},
            )
        )

    return issues


def _check_publication_atlas_spatial_bridge_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_atlas",
                "panel_label_B": "panel_spatial",
                "panel_label_C": "panel_composition",
                "panel_label_D": "panel_heatmap",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    atlas_panel = panel_boxes_by_id.get("panel_atlas") or _first_box_of_type(sidecar.panel_boxes, "panel")
    spatial_panel = panel_boxes_by_id.get("panel_spatial") or _first_box_of_type(sidecar.panel_boxes, "panel")
    composition_panel = panel_boxes_by_id.get("panel_composition") or _first_box_of_type(
        sidecar.panel_boxes, "composition_panel"
    )
    heatmap_panel = panel_boxes_by_id.get("panel_heatmap") or _first_box_of_type(
        sidecar.panel_boxes, "heatmap_tile_region"
    )
    for panel_box, target, message in (
        (atlas_panel, "panel_atlas", "atlas-spatial bridge panel requires an atlas panel"),
        (spatial_panel, "panel_spatial", "atlas-spatial bridge panel requires a spatial panel"),
        (composition_panel, "panel_composition", "atlas-spatial bridge panel requires a composition panel"),
        (heatmap_panel, "panel_heatmap", "atlas-spatial bridge panel requires a heatmap panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    state_labels = sidecar.metrics.get("state_labels")
    if not isinstance(state_labels, list) or not state_labels:
        issues.append(
            _issue(
                rule_id="state_labels_missing",
                message="atlas-spatial bridge panel requires explicit non-empty state_labels metrics",
                target="metrics.state_labels",
            )
        )
        normalized_state_labels: list[str] = []
    else:
        normalized_state_labels = []
        seen_state_labels: set[str] = set()
        for index, item in enumerate(state_labels):
            state_label = str(item or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="state labels must be non-empty",
                        target=f"metrics.state_labels[{index}]",
                    )
                )
                continue
            if state_label in seen_state_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_state_label",
                        message=f"state label `{state_label}` must be unique",
                        target="metrics.state_labels",
                        observed=state_label,
                    )
                )
                continue
            seen_state_labels.add(state_label)
            normalized_state_labels.append(state_label)

    row_labels = sidecar.metrics.get("row_labels")
    if not isinstance(row_labels, list) or not row_labels:
        issues.append(
            _issue(
                rule_id="row_labels_missing",
                message="atlas-spatial bridge panel requires explicit non-empty row_labels metrics",
                target="metrics.row_labels",
            )
        )
        normalized_row_labels: list[str] = []
    else:
        normalized_row_labels = []
        seen_row_labels: set[str] = set()
        for index, item in enumerate(row_labels):
            row_label = str(item or "").strip()
            if not row_label:
                issues.append(
                    _issue(
                        rule_id="empty_row_label",
                        message="heatmap row labels must be non-empty",
                        target=f"metrics.row_labels[{index}]",
                    )
                )
                continue
            if row_label in seen_row_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_row_label",
                        message=f"heatmap row label `{row_label}` must be unique",
                        target="metrics.row_labels",
                        observed=row_label,
                    )
                )
                continue
            seen_row_labels.add(row_label)
            normalized_row_labels.append(row_label)

    atlas_points = sidecar.metrics.get("atlas_points")
    if not isinstance(atlas_points, list) or not atlas_points:
        issues.append(
            _issue(
                rule_id="atlas_points_missing",
                message="atlas-spatial bridge panel requires non-empty atlas point metrics",
                target="metrics.atlas_points",
            )
        )
    elif atlas_panel is not None:
        for index, point in enumerate(atlas_points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.atlas_points[{index}] must be an object")
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="atlas point state_label must be non-empty",
                        target=f"metrics.atlas_points[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id="atlas_point_state_label_unknown",
                        message="atlas point state_label must stay inside declared state_labels",
                        target=f"metrics.atlas_points[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.atlas_points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.atlas_points[{index}].y")
            if _point_within_box(atlas_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="atlas_point_out_of_panel",
                    message="atlas point must stay within the atlas panel domain",
                    target=f"metrics.atlas_points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(atlas_panel.box_id,),
                )
            )

    spatial_points = sidecar.metrics.get("spatial_points")
    if not isinstance(spatial_points, list) or not spatial_points:
        issues.append(
            _issue(
                rule_id="spatial_points_missing",
                message="atlas-spatial bridge panel requires non-empty spatial point metrics",
                target="metrics.spatial_points",
            )
        )
    elif spatial_panel is not None:
        for index, point in enumerate(spatial_points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.spatial_points[{index}] must be an object")
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="spatial point state_label must be non-empty",
                        target=f"metrics.spatial_points[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id="spatial_point_state_label_unknown",
                        message="spatial point state_label must stay inside declared state_labels",
                        target=f"metrics.spatial_points[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.spatial_points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.spatial_points[{index}].y")
            if _point_within_box(spatial_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="spatial_point_out_of_panel",
                    message="spatial point must stay within the spatial panel domain",
                    target=f"metrics.spatial_points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(spatial_panel.box_id,),
                )
            )

    composition_groups = sidecar.metrics.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        issues.append(
            _issue(
                rule_id="composition_groups_missing",
                message="atlas-spatial bridge panel requires non-empty composition_groups metrics",
                target="metrics.composition_groups",
            )
        )
    else:
        seen_group_labels: set[str] = set()
        previous_group_order = 0.0
        expected_state_set = set(normalized_state_labels)
        for group_index, item in enumerate(composition_groups):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.composition_groups[{group_index}] must be an object")
            group_label = str(item.get("group_label") or "").strip()
            group_order = _require_numeric(
                item.get("group_order"),
                label=f"layout_sidecar.metrics.composition_groups[{group_index}].group_order",
            )
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="composition_group_label_missing",
                        message="composition group_label must be non-empty",
                        target=f"metrics.composition_groups[{group_index}].group_label",
                    )
                )
            elif group_label in seen_group_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_composition_group_label",
                        message=f"composition group label `{group_label}` must be unique",
                        target="metrics.composition_groups",
                        observed=group_label,
                    )
                )
            else:
                seen_group_labels.add(group_label)
            if group_order <= previous_group_order:
                issues.append(
                    _issue(
                        rule_id="composition_group_order_not_increasing",
                        message="composition group_order must stay strictly increasing",
                        target="metrics.composition_groups",
                    )
                )
            previous_group_order = group_order
            state_proportions = item.get("state_proportions")
            if not isinstance(state_proportions, list) or not state_proportions:
                issues.append(
                    _issue(
                        rule_id="composition_group_state_proportions_missing",
                        message="composition groups require non-empty state_proportions",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                    )
                )
                continue
            observed_state_set: set[str] = set()
            total = 0.0
            for state_index, state_item in enumerate(state_proportions):
                if not isinstance(state_item, dict):
                    raise ValueError(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].state_proportions[{state_index}] must be an object"
                    )
                state_label = str(state_item.get("state_label") or "").strip()
                if state_label:
                    observed_state_set.add(state_label)
                proportion = _require_numeric(
                    state_item.get("proportion"),
                    label=(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].state_proportions[{state_index}].proportion"
                    ),
                )
                total += proportion
                if 0.0 <= proportion <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id="composition_proportion_out_of_range",
                        message="composition proportion must stay within [0, 1]",
                        target=f"metrics.composition_groups[{group_index}].state_proportions[{state_index}].proportion",
                        observed=proportion,
                    )
                )
            if expected_state_set and observed_state_set != expected_state_set:
                issues.append(
                    _issue(
                        rule_id="composition_group_state_set_mismatch",
                        message="composition state set must match declared state_labels",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                        observed=sorted(observed_state_set),
                        expected=sorted(expected_state_set),
                    )
                )
            if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                issues.append(
                    _issue(
                        rule_id="composition_group_sum_invalid",
                        message="composition state proportions must sum to 1",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                        observed=total,
                        expected=1.0,
                    )
                )

    matrix_lookup = _matrix_cell_lookup(sidecar.metrics)
    matrix_state_labels = {state_label for state_label, _ in matrix_lookup}
    matrix_row_labels = {row_label for _, row_label in matrix_lookup}
    if normalized_state_labels and matrix_state_labels != set(normalized_state_labels):
        issues.append(
            _issue(
                rule_id="heatmap_state_set_mismatch",
                message="heatmap cell x labels must match declared state_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_state_labels),
                expected=sorted(normalized_state_labels),
            )
        )
    if normalized_row_labels and matrix_row_labels != set(normalized_row_labels):
        issues.append(
            _issue(
                rule_id="heatmap_row_set_mismatch",
                message="heatmap cell y labels must match declared row_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_row_labels),
                expected=sorted(normalized_row_labels),
            )
        )
    expected_cell_count = len(normalized_state_labels) * len(normalized_row_labels)
    if expected_cell_count > 0 and len(matrix_lookup) != expected_cell_count:
        issues.append(
            _issue(
                rule_id="heatmap_grid_incomplete",
                message="heatmap grid must cover every declared state/row coordinate exactly once",
                target="metrics.matrix_cells",
                observed={"cells": len(matrix_lookup)},
                expected={"cells": expected_cell_count},
            )
        )

    return issues


def _check_publication_spatial_niche_map_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_spatial",
                "panel_label_B": "panel_composition",
                "panel_label_C": "panel_heatmap",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    spatial_panel = panel_boxes_by_id.get("panel_spatial") or _first_box_of_type(sidecar.panel_boxes, "panel")
    composition_panel = panel_boxes_by_id.get("panel_composition") or _first_box_of_type(
        sidecar.panel_boxes, "composition_panel"
    )
    heatmap_panel = panel_boxes_by_id.get("panel_heatmap") or _first_box_of_type(
        sidecar.panel_boxes, "heatmap_tile_region"
    )
    for panel_box, target, message in (
        (spatial_panel, "panel_spatial", "spatial niche map requires a spatial panel"),
        (composition_panel, "panel_composition", "spatial niche map requires a composition panel"),
        (heatmap_panel, "panel_heatmap", "spatial niche map requires a heatmap panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    niche_labels = sidecar.metrics.get("niche_labels")
    if not isinstance(niche_labels, list) or not niche_labels:
        issues.append(
            _issue(
                rule_id="niche_labels_missing",
                message="spatial niche map requires explicit non-empty niche_labels metrics",
                target="metrics.niche_labels",
            )
        )
        normalized_niche_labels: list[str] = []
    else:
        normalized_niche_labels = []
        seen_niche_labels: set[str] = set()
        for index, item in enumerate(niche_labels):
            niche_label = str(item or "").strip()
            if not niche_label:
                issues.append(
                    _issue(
                        rule_id="empty_niche_label",
                        message="niche labels must be non-empty",
                        target=f"metrics.niche_labels[{index}]",
                    )
                )
                continue
            if niche_label in seen_niche_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_niche_label",
                        message=f"niche label `{niche_label}` must be unique",
                        target="metrics.niche_labels",
                        observed=niche_label,
                    )
                )
                continue
            seen_niche_labels.add(niche_label)
            normalized_niche_labels.append(niche_label)

    row_labels = sidecar.metrics.get("row_labels")
    if not isinstance(row_labels, list) or not row_labels:
        issues.append(
            _issue(
                rule_id="row_labels_missing",
                message="spatial niche map requires explicit non-empty row_labels metrics",
                target="metrics.row_labels",
            )
        )
        normalized_row_labels: list[str] = []
    else:
        normalized_row_labels = []
        seen_row_labels: set[str] = set()
        for index, item in enumerate(row_labels):
            row_label = str(item or "").strip()
            if not row_label:
                issues.append(
                    _issue(
                        rule_id="empty_row_label",
                        message="heatmap row labels must be non-empty",
                        target=f"metrics.row_labels[{index}]",
                    )
                )
                continue
            if row_label in seen_row_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_row_label",
                        message=f"heatmap row label `{row_label}` must be unique",
                        target="metrics.row_labels",
                        observed=row_label,
                    )
                )
                continue
            seen_row_labels.add(row_label)
            normalized_row_labels.append(row_label)

    points = sidecar.metrics.get("points")
    if not isinstance(points, list) or not points:
        issues.append(
            _issue(
                rule_id="points_missing",
                message="spatial niche map requires non-empty spatial point metrics",
                target="metrics.points",
            )
        )
    elif spatial_panel is not None:
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
            niche_label = str(point.get("niche_label") or "").strip()
            if not niche_label:
                issues.append(
                    _issue(
                        rule_id="empty_niche_label",
                        message="spatial point niche_label must be non-empty",
                        target=f"metrics.points[{index}].niche_label",
                    )
                )
            elif normalized_niche_labels and niche_label not in normalized_niche_labels:
                issues.append(
                    _issue(
                        rule_id="point_niche_label_unknown",
                        message="spatial point niche_label must stay inside declared niche_labels",
                        target=f"metrics.points[{index}].niche_label",
                        observed=niche_label,
                        expected=normalized_niche_labels,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
            if _point_within_box(spatial_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="point_out_of_panel",
                    message="spatial point must stay within the spatial panel domain",
                    target=f"metrics.points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(spatial_panel.box_id,),
                )
            )

    composition_groups = sidecar.metrics.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        issues.append(
            _issue(
                rule_id="composition_groups_missing",
                message="spatial niche map requires non-empty composition_groups metrics",
                target="metrics.composition_groups",
            )
        )
    else:
        seen_group_labels: set[str] = set()
        previous_group_order = 0.0
        expected_niche_set = set(normalized_niche_labels)
        for group_index, item in enumerate(composition_groups):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.composition_groups[{group_index}] must be an object")
            group_label = str(item.get("group_label") or "").strip()
            group_order = _require_numeric(
                item.get("group_order"),
                label=f"layout_sidecar.metrics.composition_groups[{group_index}].group_order",
            )
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="composition_group_label_missing",
                        message="composition group_label must be non-empty",
                        target=f"metrics.composition_groups[{group_index}].group_label",
                    )
                )
            elif group_label in seen_group_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_composition_group_label",
                        message=f"composition group label `{group_label}` must be unique",
                        target="metrics.composition_groups",
                        observed=group_label,
                    )
                )
            else:
                seen_group_labels.add(group_label)
            if group_order <= previous_group_order:
                issues.append(
                    _issue(
                        rule_id="composition_group_order_not_increasing",
                        message="composition group_order must stay strictly increasing",
                        target="metrics.composition_groups",
                    )
                )
            previous_group_order = group_order
            niche_proportions = item.get("niche_proportions")
            if not isinstance(niche_proportions, list) or not niche_proportions:
                issues.append(
                    _issue(
                        rule_id="composition_group_niche_proportions_missing",
                        message="composition groups require non-empty niche_proportions",
                        target=f"metrics.composition_groups[{group_index}].niche_proportions",
                    )
                )
                continue
            observed_niche_set: set[str] = set()
            total = 0.0
            for niche_index, niche_item in enumerate(niche_proportions):
                if not isinstance(niche_item, dict):
                    raise ValueError(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].niche_proportions[{niche_index}] must be an object"
                    )
                niche_label = str(niche_item.get("niche_label") or "").strip()
                if niche_label:
                    observed_niche_set.add(niche_label)
                proportion = _require_numeric(
                    niche_item.get("proportion"),
                    label=(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].niche_proportions[{niche_index}].proportion"
                    ),
                )
                total += proportion
                if 0.0 <= proportion <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id="composition_proportion_out_of_range",
                        message="composition proportion must stay within [0, 1]",
                        target=f"metrics.composition_groups[{group_index}].niche_proportions[{niche_index}].proportion",
                        observed=proportion,
                    )
                )
            if expected_niche_set and observed_niche_set != expected_niche_set:
                issues.append(
                    _issue(
                        rule_id="composition_group_niche_set_mismatch",
                        message="composition niche set must match declared niche_labels",
                        target=f"metrics.composition_groups[{group_index}].niche_proportions",
                        observed=sorted(observed_niche_set),
                        expected=sorted(expected_niche_set),
                    )
                )
            if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                issues.append(
                    _issue(
                        rule_id="composition_group_sum_invalid",
                        message="composition niche proportions must sum to 1",
                        target=f"metrics.composition_groups[{group_index}].niche_proportions",
                        observed=total,
                        expected=1.0,
                    )
                )

    matrix_lookup = _matrix_cell_lookup(sidecar.metrics)
    matrix_niche_labels = {niche_label for niche_label, _ in matrix_lookup}
    matrix_row_labels = {row_label for _, row_label in matrix_lookup}
    if normalized_niche_labels and matrix_niche_labels != set(normalized_niche_labels):
        issues.append(
            _issue(
                rule_id="heatmap_niche_set_mismatch",
                message="heatmap cell x labels must match declared niche_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_niche_labels),
                expected=sorted(normalized_niche_labels),
            )
        )
    if normalized_row_labels and matrix_row_labels != set(normalized_row_labels):
        issues.append(
            _issue(
                rule_id="heatmap_row_set_mismatch",
                message="heatmap cell y labels must match declared row_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_row_labels),
                expected=sorted(normalized_row_labels),
            )
        )
    expected_cell_count = len(normalized_niche_labels) * len(normalized_row_labels)
    if expected_cell_count > 0 and len(matrix_lookup) != expected_cell_count:
        issues.append(
            _issue(
                rule_id="heatmap_grid_incomplete",
                message="heatmap grid must cover every declared niche/row coordinate exactly once",
                target="metrics.matrix_cells",
                observed={"cells": len(matrix_lookup)},
                expected={"cells": expected_cell_count},
            )
        )

    return issues


def _check_publication_trajectory_progression_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_trajectory",
                "panel_label_B": "panel_composition",
                "panel_label_C": "panel_heatmap",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    trajectory_panel = panel_boxes_by_id.get("panel_trajectory") or _first_box_of_type(sidecar.panel_boxes, "panel")
    composition_panel = panel_boxes_by_id.get("panel_composition") or _first_box_of_type(
        sidecar.panel_boxes, "composition_panel"
    )
    heatmap_panel = panel_boxes_by_id.get("panel_heatmap") or _first_box_of_type(
        sidecar.panel_boxes, "heatmap_tile_region"
    )
    for panel_box, target, message in (
        (trajectory_panel, "panel_trajectory", "trajectory progression panel requires a trajectory panel"),
        (composition_panel, "panel_composition", "trajectory progression panel requires a composition panel"),
        (heatmap_panel, "panel_heatmap", "trajectory progression panel requires a heatmap panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    branch_labels = sidecar.metrics.get("branch_labels")
    if not isinstance(branch_labels, list) or not branch_labels:
        issues.append(
            _issue(
                rule_id="branch_labels_missing",
                message="trajectory progression panel requires explicit non-empty branch_labels metrics",
                target="metrics.branch_labels",
            )
        )
        normalized_branch_labels: list[str] = []
    else:
        normalized_branch_labels = []
        seen_branch_labels: set[str] = set()
        for index, item in enumerate(branch_labels):
            branch_label = str(item or "").strip()
            if not branch_label:
                issues.append(
                    _issue(
                        rule_id="empty_branch_label",
                        message="branch labels must be non-empty",
                        target=f"metrics.branch_labels[{index}]",
                    )
                )
                continue
            if branch_label in seen_branch_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_branch_label",
                        message=f"branch label `{branch_label}` must be unique",
                        target="metrics.branch_labels",
                        observed=branch_label,
                    )
                )
                continue
            seen_branch_labels.add(branch_label)
            normalized_branch_labels.append(branch_label)

    bin_labels = sidecar.metrics.get("bin_labels")
    if not isinstance(bin_labels, list) or not bin_labels:
        issues.append(
            _issue(
                rule_id="bin_labels_missing",
                message="trajectory progression panel requires explicit non-empty bin_labels metrics",
                target="metrics.bin_labels",
            )
        )
        normalized_bin_labels: list[str] = []
    else:
        normalized_bin_labels = []
        seen_bin_labels: set[str] = set()
        for index, item in enumerate(bin_labels):
            bin_label = str(item or "").strip()
            if not bin_label:
                issues.append(
                    _issue(
                        rule_id="empty_bin_label",
                        message="progression bin labels must be non-empty",
                        target=f"metrics.bin_labels[{index}]",
                    )
                )
                continue
            if bin_label in seen_bin_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_bin_label",
                        message=f"progression bin label `{bin_label}` must be unique",
                        target="metrics.bin_labels",
                        observed=bin_label,
                    )
                )
                continue
            seen_bin_labels.add(bin_label)
            normalized_bin_labels.append(bin_label)

    row_labels = sidecar.metrics.get("row_labels")
    if not isinstance(row_labels, list) or not row_labels:
        issues.append(
            _issue(
                rule_id="row_labels_missing",
                message="trajectory progression panel requires explicit non-empty row_labels metrics",
                target="metrics.row_labels",
            )
        )
        normalized_row_labels: list[str] = []
    else:
        normalized_row_labels = []
        seen_row_labels: set[str] = set()
        for index, item in enumerate(row_labels):
            row_label = str(item or "").strip()
            if not row_label:
                issues.append(
                    _issue(
                        rule_id="empty_row_label",
                        message="heatmap row labels must be non-empty",
                        target=f"metrics.row_labels[{index}]",
                    )
                )
                continue
            if row_label in seen_row_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_row_label",
                        message=f"heatmap row label `{row_label}` must be unique",
                        target="metrics.row_labels",
                        observed=row_label,
                    )
                )
                continue
            seen_row_labels.add(row_label)
            normalized_row_labels.append(row_label)

    points = sidecar.metrics.get("points")
    if not isinstance(points, list) or not points:
        issues.append(
            _issue(
                rule_id="points_missing",
                message="trajectory progression panel requires non-empty trajectory point metrics",
                target="metrics.points",
            )
        )
    elif trajectory_panel is not None:
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
            branch_label = str(point.get("branch_label") or "").strip()
            if not branch_label:
                issues.append(
                    _issue(
                        rule_id="empty_branch_label",
                        message="trajectory point branch_label must be non-empty",
                        target=f"metrics.points[{index}].branch_label",
                    )
                )
            elif normalized_branch_labels and branch_label not in normalized_branch_labels:
                issues.append(
                    _issue(
                        rule_id="point_branch_label_unknown",
                        message="trajectory point branch_label must stay inside declared branch_labels",
                        target=f"metrics.points[{index}].branch_label",
                        observed=branch_label,
                        expected=normalized_branch_labels,
                    )
                )
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="point_state_label_missing",
                        message="trajectory point state_label must be non-empty",
                        target=f"metrics.points[{index}].state_label",
                    )
                )
            pseudotime = _require_numeric(point.get("pseudotime"), label=f"layout_sidecar.metrics.points[{index}].pseudotime")
            if not 0.0 <= pseudotime <= 1.0:
                issues.append(
                    _issue(
                        rule_id="point_pseudotime_out_of_range",
                        message="trajectory point pseudotime must stay within [0, 1]",
                        target=f"metrics.points[{index}].pseudotime",
                        observed=pseudotime,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
            if _point_within_box(trajectory_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="point_out_of_panel",
                    message="trajectory point must stay within the trajectory panel domain",
                    target=f"metrics.points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(trajectory_panel.box_id,),
                )
            )

    progression_bins = sidecar.metrics.get("progression_bins")
    if not isinstance(progression_bins, list) or not progression_bins:
        issues.append(
            _issue(
                rule_id="progression_bins_missing",
                message="trajectory progression panel requires non-empty progression_bins metrics",
                target="metrics.progression_bins",
            )
        )
    else:
        expected_branch_set = set(normalized_branch_labels)
        expected_bin_set = set(normalized_bin_labels)
        seen_bin_labels = set()
        previous_bin_order = 0.0
        previous_end = -1.0
        for bin_index, item in enumerate(progression_bins):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.progression_bins[{bin_index}] must be an object")
            bin_label = str(item.get("bin_label") or "").strip()
            if not bin_label:
                issues.append(
                    _issue(
                        rule_id="progression_bin_label_missing",
                        message="progression bin label must be non-empty",
                        target=f"metrics.progression_bins[{bin_index}].bin_label",
                    )
                )
            elif bin_label in seen_bin_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_progression_bin_label",
                        message=f"progression bin label `{bin_label}` must be unique",
                        target="metrics.progression_bins",
                        observed=bin_label,
                    )
                )
            else:
                seen_bin_labels.add(bin_label)

            bin_order = _require_numeric(
                item.get("bin_order"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].bin_order",
            )
            if bin_order <= previous_bin_order:
                issues.append(
                    _issue(
                        rule_id="progression_bin_order_not_increasing",
                        message="progression bin_order must stay strictly increasing",
                        target="metrics.progression_bins",
                    )
                )
            previous_bin_order = bin_order

            pseudotime_start = _require_numeric(
                item.get("pseudotime_start"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].pseudotime_start",
            )
            pseudotime_end = _require_numeric(
                item.get("pseudotime_end"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].pseudotime_end",
            )
            if not (0.0 <= pseudotime_start < pseudotime_end <= 1.0) or pseudotime_start < previous_end - 1e-9:
                issues.append(
                    _issue(
                        rule_id="progression_bin_interval_invalid",
                        message="progression bin intervals must advance monotonically within [0, 1]",
                        target=f"metrics.progression_bins[{bin_index}]",
                        observed={"start": pseudotime_start, "end": pseudotime_end},
                    )
                )
            previous_end = max(previous_end, pseudotime_end)

            branch_weights = item.get("branch_weights")
            if not isinstance(branch_weights, list) or not branch_weights:
                issues.append(
                    _issue(
                        rule_id="progression_bin_branch_weights_missing",
                        message="progression bins require non-empty branch_weights",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                    )
                )
                continue
            observed_branch_set: set[str] = set()
            total = 0.0
            for branch_index, branch_item in enumerate(branch_weights):
                if not isinstance(branch_item, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.progression_bins[{bin_index}].branch_weights[{branch_index}] must be an object"
                    )
                branch_label = str(branch_item.get("branch_label") or "").strip()
                if branch_label:
                    observed_branch_set.add(branch_label)
                proportion = _require_numeric(
                    branch_item.get("proportion"),
                    label=(
                        f"layout_sidecar.metrics.progression_bins[{bin_index}]."
                        f"branch_weights[{branch_index}].proportion"
                    ),
                )
                total += proportion
                if 0.0 <= proportion <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id="progression_bin_proportion_out_of_range",
                        message="progression bin branch proportions must stay within [0, 1]",
                        target=(
                            f"metrics.progression_bins[{bin_index}].branch_weights[{branch_index}].proportion"
                        ),
                        observed=proportion,
                    )
                )
            if expected_branch_set and observed_branch_set != expected_branch_set:
                issues.append(
                    _issue(
                        rule_id="progression_bin_branch_set_mismatch",
                        message="progression bin branch set must match declared branch_labels",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                        observed=sorted(observed_branch_set),
                        expected=sorted(expected_branch_set),
                    )
                )
            if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                issues.append(
                    _issue(
                        rule_id="progression_bin_sum_invalid",
                        message="progression bin branch weights must sum to 1",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                        observed=total,
                        expected=1.0,
                    )
                )

        if expected_bin_set and seen_bin_labels != expected_bin_set:
            issues.append(
                _issue(
                    rule_id="progression_bin_label_set_mismatch",
                    message="progression bin labels must match declared bin_labels",
                    target="metrics.progression_bins",
                    observed=sorted(seen_bin_labels),
                    expected=sorted(expected_bin_set),
                )
            )

    matrix_lookup = _matrix_cell_lookup(sidecar.metrics)
    matrix_bin_labels = {bin_label for bin_label, _ in matrix_lookup}
    matrix_row_labels = {row_label for _, row_label in matrix_lookup}
    if normalized_bin_labels and matrix_bin_labels != set(normalized_bin_labels):
        issues.append(
            _issue(
                rule_id="heatmap_bin_set_mismatch",
                message="heatmap cell x labels must match declared bin_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_bin_labels),
                expected=sorted(normalized_bin_labels),
            )
        )
    if normalized_row_labels and matrix_row_labels != set(normalized_row_labels):
        issues.append(
            _issue(
                rule_id="heatmap_row_set_mismatch",
                message="heatmap cell y labels must match declared row_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_row_labels),
                expected=sorted(normalized_row_labels),
            )
        )
    expected_cell_count = len(normalized_bin_labels) * len(normalized_row_labels)
    if expected_cell_count > 0 and len(matrix_lookup) != expected_cell_count:
        issues.append(
            _issue(
                rule_id="heatmap_grid_incomplete",
                message="heatmap grid must cover every declared bin/row coordinate exactly once",
                target="metrics.matrix_cells",
                observed={"cells": len(matrix_lookup)},
                expected={"cells": expected_cell_count},
            )
        )

    return issues


def _check_publication_atlas_spatial_trajectory_storyboard_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_atlas",
                "panel_label_B": "panel_spatial",
                "panel_label_C": "panel_trajectory",
                "panel_label_D": "panel_composition",
                "panel_label_E": "panel_heatmap",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    atlas_panel = panel_boxes_by_id.get("panel_atlas")
    spatial_panel = panel_boxes_by_id.get("panel_spatial")
    trajectory_panel = panel_boxes_by_id.get("panel_trajectory")
    composition_panel = panel_boxes_by_id.get("panel_composition")
    heatmap_panel = panel_boxes_by_id.get("panel_heatmap")
    for panel_box, target, message in (
        (atlas_panel, "panel_atlas", "storyboard panel requires an atlas panel"),
        (spatial_panel, "panel_spatial", "storyboard panel requires a spatial panel"),
        (trajectory_panel, "panel_trajectory", "storyboard panel requires a trajectory panel"),
        (composition_panel, "panel_composition", "storyboard panel requires a composition panel"),
        (heatmap_panel, "panel_heatmap", "storyboard panel requires a heatmap panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    def _normalize_unique_labels(metric_key: str, missing_rule: str, empty_rule: str, duplicate_rule: str, message: str) -> list[str]:
        labels = sidecar.metrics.get(metric_key)
        if not isinstance(labels, list) or not labels:
            issues.append(
                _issue(
                    rule_id=missing_rule,
                    message=message,
                    target=f"metrics.{metric_key}",
                )
            )
            return []
        normalized: list[str] = []
        seen: set[str] = set()
        for index, item in enumerate(labels):
            label = str(item or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id=empty_rule,
                        message=f"{metric_key} labels must be non-empty",
                        target=f"metrics.{metric_key}[{index}]",
                    )
                )
                continue
            if label in seen:
                issues.append(
                    _issue(
                        rule_id=duplicate_rule,
                        message=f"{metric_key} label `{label}` must be unique",
                        target=f"metrics.{metric_key}",
                        observed=label,
                    )
                )
                continue
            seen.add(label)
            normalized.append(label)
        return normalized

    normalized_state_labels = _normalize_unique_labels(
        "state_labels",
        "state_labels_missing",
        "empty_state_label",
        "duplicate_state_label",
        "storyboard panel requires explicit non-empty state_labels metrics",
    )
    normalized_branch_labels = _normalize_unique_labels(
        "branch_labels",
        "branch_labels_missing",
        "empty_branch_label",
        "duplicate_branch_label",
        "storyboard panel requires explicit non-empty branch_labels metrics",
    )
    normalized_bin_labels = _normalize_unique_labels(
        "bin_labels",
        "bin_labels_missing",
        "empty_bin_label",
        "duplicate_bin_label",
        "storyboard panel requires explicit non-empty bin_labels metrics",
    )
    normalized_row_labels = _normalize_unique_labels(
        "row_labels",
        "row_labels_missing",
        "empty_row_label",
        "duplicate_row_label",
        "storyboard panel requires explicit non-empty row_labels metrics",
    )

    def _check_state_points(points_key: str, panel_box: Box | None, unknown_rule: str, out_rule: str, human_name: str) -> None:
        points = sidecar.metrics.get(points_key)
        if not isinstance(points, list) or not points:
            issues.append(
                _issue(
                    rule_id=f"{points_key}_missing",
                    message=f"storyboard panel requires non-empty {points_key} metrics",
                    target=f"metrics.{points_key}",
                )
            )
            return
        if panel_box is None:
            return
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.{points_key}[{index}] must be an object")
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message=f"{human_name} state_label must be non-empty",
                        target=f"metrics.{points_key}[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id=unknown_rule,
                        message=f"{human_name} state_label must stay inside declared state_labels",
                        target=f"metrics.{points_key}[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.{points_key}[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.{points_key}[{index}].y")
            if _point_within_box(panel_box, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id=out_rule,
                    message=f"{human_name} must stay within its panel domain",
                    target=f"metrics.{points_key}[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(panel_box.box_id,),
                )
            )

    _check_state_points("atlas_points", atlas_panel, "atlas_point_state_label_unknown", "atlas_point_out_of_panel", "atlas point")
    _check_state_points(
        "spatial_points",
        spatial_panel,
        "spatial_point_state_label_unknown",
        "spatial_point_out_of_panel",
        "spatial point",
    )

    trajectory_points = sidecar.metrics.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        issues.append(
            _issue(
                rule_id="trajectory_points_missing",
                message="storyboard panel requires non-empty trajectory_points metrics",
                target="metrics.trajectory_points",
            )
        )
    elif trajectory_panel is not None:
        for index, point in enumerate(trajectory_points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.trajectory_points[{index}] must be an object")
            branch_label = str(point.get("branch_label") or "").strip()
            if not branch_label:
                issues.append(
                    _issue(
                        rule_id="empty_branch_label",
                        message="trajectory point branch_label must be non-empty",
                        target=f"metrics.trajectory_points[{index}].branch_label",
                    )
                )
            elif normalized_branch_labels and branch_label not in normalized_branch_labels:
                issues.append(
                    _issue(
                        rule_id="trajectory_point_branch_label_unknown",
                        message="trajectory point branch_label must stay inside declared branch_labels",
                        target=f"metrics.trajectory_points[{index}].branch_label",
                        observed=branch_label,
                        expected=normalized_branch_labels,
                    )
                )
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="trajectory point state_label must be non-empty",
                        target=f"metrics.trajectory_points[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id="trajectory_point_state_label_unknown",
                        message="trajectory point state_label must stay inside declared state_labels",
                        target=f"metrics.trajectory_points[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            _require_numeric(point.get("pseudotime"), label=f"layout_sidecar.metrics.trajectory_points[{index}].pseudotime")
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.trajectory_points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.trajectory_points[{index}].y")
            if _point_within_box(trajectory_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="trajectory_point_out_of_panel",
                    message="trajectory point must stay within the trajectory panel domain",
                    target=f"metrics.trajectory_points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(trajectory_panel.box_id,),
                )
            )

    composition_groups = sidecar.metrics.get("composition_groups")
    if not isinstance(composition_groups, list) or not composition_groups:
        issues.append(
            _issue(
                rule_id="composition_groups_missing",
                message="storyboard panel requires non-empty composition_groups metrics",
                target="metrics.composition_groups",
            )
        )
    else:
        seen_group_labels: set[str] = set()
        previous_group_order = 0.0
        expected_state_set = set(normalized_state_labels)
        for group_index, item in enumerate(composition_groups):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.composition_groups[{group_index}] must be an object")
            group_label = str(item.get("group_label") or "").strip()
            group_order = _require_numeric(
                item.get("group_order"),
                label=f"layout_sidecar.metrics.composition_groups[{group_index}].group_order",
            )
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="composition_group_label_missing",
                        message="composition group_label must be non-empty",
                        target=f"metrics.composition_groups[{group_index}].group_label",
                    )
                )
            elif group_label in seen_group_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_composition_group_label",
                        message=f"composition group label `{group_label}` must be unique",
                        target="metrics.composition_groups",
                        observed=group_label,
                    )
                )
            else:
                seen_group_labels.add(group_label)
            if group_order <= previous_group_order:
                issues.append(
                    _issue(
                        rule_id="composition_group_order_not_increasing",
                        message="composition group_order must stay strictly increasing",
                        target="metrics.composition_groups",
                    )
                )
            previous_group_order = group_order
            state_proportions = item.get("state_proportions")
            if not isinstance(state_proportions, list) or not state_proportions:
                issues.append(
                    _issue(
                        rule_id="composition_group_state_proportions_missing",
                        message="composition groups require non-empty state_proportions",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                    )
                )
                continue
            observed_state_set: set[str] = set()
            total = 0.0
            for state_index, state_item in enumerate(state_proportions):
                if not isinstance(state_item, dict):
                    raise ValueError(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].state_proportions[{state_index}] must be an object"
                    )
                state_label = str(state_item.get("state_label") or "").strip()
                if state_label:
                    observed_state_set.add(state_label)
                proportion = _require_numeric(
                    state_item.get("proportion"),
                    label=(
                        "layout_sidecar.metrics.composition_groups"
                        f"[{group_index}].state_proportions[{state_index}].proportion"
                    ),
                )
                total += proportion
                if 0.0 <= proportion <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id="composition_proportion_out_of_range",
                        message="composition proportion must stay within [0, 1]",
                        target=(
                            "metrics.composition_groups"
                            f"[{group_index}].state_proportions[{state_index}].proportion"
                        ),
                        observed=proportion,
                    )
                )
            if expected_state_set and observed_state_set != expected_state_set:
                issues.append(
                    _issue(
                        rule_id="composition_group_state_set_mismatch",
                        message="composition state set must match declared state_labels",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                        observed=sorted(observed_state_set),
                        expected=sorted(expected_state_set),
                    )
                )
            if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                issues.append(
                    _issue(
                        rule_id="composition_group_sum_invalid",
                        message="composition state proportions must sum to 1",
                        target=f"metrics.composition_groups[{group_index}].state_proportions",
                        observed=total,
                        expected=1.0,
                    )
                )

    progression_bins = sidecar.metrics.get("progression_bins")
    if not isinstance(progression_bins, list) or not progression_bins:
        issues.append(
            _issue(
                rule_id="progression_bins_missing",
                message="storyboard panel requires non-empty progression_bins metrics",
                target="metrics.progression_bins",
            )
        )
    else:
        seen_bin_labels_set: set[str] = set()
        previous_bin_order = 0.0
        previous_end = -1.0
        expected_branch_set = set(normalized_branch_labels)
        for bin_index, item in enumerate(progression_bins):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.progression_bins[{bin_index}] must be an object")
            bin_label = str(item.get("bin_label") or "").strip()
            bin_order = _require_numeric(
                item.get("bin_order"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].bin_order",
            )
            if not bin_label:
                issues.append(
                    _issue(
                        rule_id="progression_bin_label_missing",
                        message="progression bin label must be non-empty",
                        target=f"metrics.progression_bins[{bin_index}].bin_label",
                    )
                )
            elif bin_label in seen_bin_labels_set:
                issues.append(
                    _issue(
                        rule_id="duplicate_bin_label",
                        message=f"progression bin label `{bin_label}` must be unique",
                        target="metrics.progression_bins",
                        observed=bin_label,
                    )
                )
            else:
                seen_bin_labels_set.add(bin_label)
            if bin_order <= previous_bin_order:
                issues.append(
                    _issue(
                        rule_id="progression_bin_order_not_increasing",
                        message="progression bin_order must stay strictly increasing",
                        target="metrics.progression_bins",
                    )
                )
            previous_bin_order = bin_order
            start = _require_numeric(
                item.get("pseudotime_start"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].pseudotime_start",
            )
            end = _require_numeric(
                item.get("pseudotime_end"),
                label=f"layout_sidecar.metrics.progression_bins[{bin_index}].pseudotime_end",
            )
            if end <= start:
                issues.append(
                    _issue(
                        rule_id="progression_bin_interval_invalid",
                        message="progression bin must satisfy pseudotime_start < pseudotime_end",
                        target=f"metrics.progression_bins[{bin_index}]",
                    )
                )
            if start < previous_end - 1e-9:
                issues.append(
                    _issue(
                        rule_id="progression_bin_interval_not_increasing",
                        message="progression bin intervals must stay strictly increasing",
                        target="metrics.progression_bins",
                    )
                )
            previous_end = end
            branch_weights = item.get("branch_weights")
            if not isinstance(branch_weights, list) or not branch_weights:
                issues.append(
                    _issue(
                        rule_id="progression_bin_branch_weights_missing",
                        message="progression bins require non-empty branch_weights",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                    )
                )
                continue
            seen_weight_branches: set[str] = set()
            total = 0.0
            for branch_index, branch_item in enumerate(branch_weights):
                if not isinstance(branch_item, dict):
                    raise ValueError(
                        "layout_sidecar.metrics.progression_bins"
                        f"[{bin_index}].branch_weights[{branch_index}] must be an object"
                    )
                branch_label = str(branch_item.get("branch_label") or "").strip()
                if branch_label:
                    seen_weight_branches.add(branch_label)
                proportion = _require_numeric(
                    branch_item.get("proportion"),
                    label=(
                        "layout_sidecar.metrics.progression_bins"
                        f"[{bin_index}].branch_weights[{branch_index}].proportion"
                    ),
                )
                total += proportion
                if 0.0 <= proportion <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id="progression_bin_branch_proportion_out_of_range",
                        message="progression bin branch proportion must stay within [0, 1]",
                        target=(
                            "metrics.progression_bins"
                            f"[{bin_index}].branch_weights[{branch_index}].proportion"
                        ),
                        observed=proportion,
                    )
                )
            if expected_branch_set and seen_weight_branches != expected_branch_set:
                issues.append(
                    _issue(
                        rule_id="progression_bin_branch_set_mismatch",
                        message="progression bin branch set must match declared branch_labels",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                        observed=sorted(seen_weight_branches),
                        expected=sorted(expected_branch_set),
                    )
                )
            if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
                issues.append(
                    _issue(
                        rule_id="progression_bin_sum_invalid",
                        message="progression bin branch weights must sum to 1",
                        target=f"metrics.progression_bins[{bin_index}].branch_weights",
                        observed=total,
                        expected=1.0,
                    )
                )
        if normalized_bin_labels and seen_bin_labels_set != set(normalized_bin_labels):
            issues.append(
                _issue(
                    rule_id="progression_bin_label_set_mismatch",
                    message="progression bin labels must match declared bin_labels",
                    target="metrics.progression_bins",
                    observed=sorted(seen_bin_labels_set),
                    expected=sorted(normalized_bin_labels),
                )
            )

    matrix_lookup = _matrix_cell_lookup(sidecar.metrics)
    matrix_bin_labels = {bin_label for bin_label, _ in matrix_lookup}
    matrix_row_labels = {row_label for _, row_label in matrix_lookup}
    if normalized_bin_labels and matrix_bin_labels != set(normalized_bin_labels):
        issues.append(
            _issue(
                rule_id="heatmap_bin_set_mismatch",
                message="heatmap cell x labels must match declared bin_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_bin_labels),
                expected=sorted(normalized_bin_labels),
            )
        )
    if normalized_row_labels and matrix_row_labels != set(normalized_row_labels):
        issues.append(
            _issue(
                rule_id="heatmap_row_set_mismatch",
                message="heatmap cell y labels must match declared row_labels",
                target="metrics.matrix_cells",
                observed=sorted(matrix_row_labels),
                expected=sorted(normalized_row_labels),
            )
        )
    expected_cell_count = len(normalized_bin_labels) * len(normalized_row_labels)
    if expected_cell_count > 0 and len(matrix_lookup) != expected_cell_count:
        issues.append(
            _issue(
                rule_id="heatmap_grid_incomplete",
                message="heatmap grid must cover every declared bin/row coordinate exactly once",
                target="metrics.matrix_cells",
                observed={"cells": len(matrix_lookup)},
                expected={"cells": expected_cell_count},
            )
        )

    return issues


def _check_publication_atlas_spatial_trajectory_density_coverage_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_atlas",
                "panel_label_B": "panel_spatial",
                "panel_label_C": "panel_trajectory",
                "panel_label_D": "panel_support",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    atlas_panel = panel_boxes_by_id.get("panel_atlas")
    spatial_panel = panel_boxes_by_id.get("panel_spatial")
    trajectory_panel = panel_boxes_by_id.get("panel_trajectory")
    support_panel = panel_boxes_by_id.get("panel_support")
    for panel_box, target, message in (
        (atlas_panel, "panel_atlas", "density-coverage panel requires an atlas panel"),
        (spatial_panel, "panel_spatial", "density-coverage panel requires a spatial panel"),
        (trajectory_panel, "panel_trajectory", "density-coverage panel requires a trajectory panel"),
        (support_panel, "panel_support", "density-coverage panel requires a support panel"),
    ):
        if panel_box is not None:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=target, expected="present"))

    def _normalize_unique_labels(
        metric_key: str,
        missing_rule: str,
        empty_rule: str,
        duplicate_rule: str,
        message: str,
    ) -> list[str]:
        labels = sidecar.metrics.get(metric_key)
        if not isinstance(labels, list) or not labels:
            issues.append(_issue(rule_id=missing_rule, message=message, target=f"metrics.{metric_key}"))
            return []
        normalized: list[str] = []
        seen: set[str] = set()
        for index, item in enumerate(labels):
            label = str(item or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id=empty_rule,
                        message=f"{metric_key} labels must be non-empty",
                        target=f"metrics.{metric_key}[{index}]",
                    )
                )
                continue
            if label in seen:
                issues.append(
                    _issue(
                        rule_id=duplicate_rule,
                        message=f"{metric_key} label `{label}` must be unique",
                        target=f"metrics.{metric_key}",
                        observed=label,
                    )
                )
                continue
            seen.add(label)
            normalized.append(label)
        return normalized

    normalized_state_labels = _normalize_unique_labels(
        "state_labels",
        "state_labels_missing",
        "empty_state_label",
        "duplicate_state_label",
        "density-coverage panel requires explicit non-empty state_labels metrics",
    )
    normalized_region_labels = _normalize_unique_labels(
        "region_labels",
        "region_labels_missing",
        "empty_region_label",
        "duplicate_region_label",
        "density-coverage panel requires explicit non-empty region_labels metrics",
    )
    normalized_branch_labels = _normalize_unique_labels(
        "branch_labels",
        "branch_labels_missing",
        "empty_branch_label",
        "duplicate_branch_label",
        "density-coverage panel requires explicit non-empty branch_labels metrics",
    )
    normalized_context_labels = _normalize_unique_labels(
        "context_labels",
        "context_labels_missing",
        "empty_context_label",
        "duplicate_context_label",
        "density-coverage panel requires explicit non-empty context_labels metrics",
    )
    normalized_context_kinds = _normalize_unique_labels(
        "context_kinds",
        "context_kinds_missing",
        "empty_context_kind",
        "duplicate_context_kind",
        "density-coverage panel requires explicit non-empty context_kinds metrics",
    )
    required_context_kinds = {"atlas_density", "spatial_coverage", "trajectory_coverage"}
    if normalized_context_kinds and set(normalized_context_kinds) != required_context_kinds:
        issues.append(
            _issue(
                rule_id="context_kind_set_mismatch",
                message="context_kinds must cover atlas_density, spatial_coverage, and trajectory_coverage",
                target="metrics.context_kinds",
                observed=sorted(normalized_context_kinds),
                expected=sorted(required_context_kinds),
            )
        )
    if normalized_context_labels and normalized_context_kinds and len(normalized_context_labels) != len(normalized_context_kinds):
        issues.append(
            _issue(
                rule_id="context_label_kind_count_mismatch",
                message="context_labels and context_kinds must stay aligned one-to-one",
                target="metrics.context_kinds",
                observed=len(normalized_context_kinds),
                expected=len(normalized_context_labels),
            )
        )
    support_scale_label = str(sidecar.metrics.get("support_scale_label") or "").strip()
    if not support_scale_label:
        issues.append(
            _issue(
                rule_id="support_scale_label_missing",
                message="density-coverage panel requires a non-empty support_scale_label",
                target="metrics.support_scale_label",
            )
        )

    def _check_state_points(points_key: str, panel_box: Box | None, unknown_rule: str, out_rule: str, human_name: str) -> None:
        points = sidecar.metrics.get(points_key)
        if not isinstance(points, list) or not points:
            issues.append(
                _issue(
                    rule_id=f"{points_key}_missing",
                    message=f"density-coverage panel requires non-empty {points_key} metrics",
                    target=f"metrics.{points_key}",
                )
            )
            return
        if panel_box is None:
            return
        for index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.{points_key}[{index}] must be an object")
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message=f"{human_name} state_label must be non-empty",
                        target=f"metrics.{points_key}[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id=unknown_rule,
                        message=f"{human_name} state_label must stay inside declared state_labels",
                        target=f"metrics.{points_key}[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.{points_key}[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.{points_key}[{index}].y")
            if _point_within_box(panel_box, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id=out_rule,
                    message=f"{human_name} must stay within its panel domain",
                    target=f"metrics.{points_key}[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(panel_box.box_id,),
                )
            )

    _check_state_points("atlas_points", atlas_panel, "atlas_point_state_label_unknown", "atlas_point_out_of_panel", "atlas point")
    _check_state_points(
        "spatial_points",
        spatial_panel,
        "spatial_point_state_label_unknown",
        "spatial_point_out_of_panel",
        "spatial point",
    )

    spatial_points = sidecar.metrics.get("spatial_points")
    if isinstance(spatial_points, list):
        for index, point in enumerate(spatial_points):
            if not isinstance(point, dict):
                continue
            region_label = str(point.get("region_label") or "").strip()
            if not region_label:
                issues.append(
                    _issue(
                        rule_id="empty_region_label",
                        message="spatial point region_label must be non-empty",
                        target=f"metrics.spatial_points[{index}].region_label",
                    )
                )
            elif normalized_region_labels and region_label not in normalized_region_labels:
                issues.append(
                    _issue(
                        rule_id="spatial_point_region_label_unknown",
                        message="spatial point region_label must stay inside declared region_labels",
                        target=f"metrics.spatial_points[{index}].region_label",
                        observed=region_label,
                        expected=normalized_region_labels,
                    )
                )

    trajectory_points = sidecar.metrics.get("trajectory_points")
    if not isinstance(trajectory_points, list) or not trajectory_points:
        issues.append(
            _issue(
                rule_id="trajectory_points_missing",
                message="density-coverage panel requires non-empty trajectory_points metrics",
                target="metrics.trajectory_points",
            )
        )
    elif trajectory_panel is not None:
        for index, point in enumerate(trajectory_points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.trajectory_points[{index}] must be an object")
            branch_label = str(point.get("branch_label") or "").strip()
            if not branch_label:
                issues.append(
                    _issue(
                        rule_id="empty_branch_label",
                        message="trajectory point branch_label must be non-empty",
                        target=f"metrics.trajectory_points[{index}].branch_label",
                    )
                )
            elif normalized_branch_labels and branch_label not in normalized_branch_labels:
                issues.append(
                    _issue(
                        rule_id="trajectory_point_branch_label_unknown",
                        message="trajectory point branch_label must stay inside declared branch_labels",
                        target=f"metrics.trajectory_points[{index}].branch_label",
                        observed=branch_label,
                        expected=normalized_branch_labels,
                    )
                )
            state_label = str(point.get("state_label") or "").strip()
            if not state_label:
                issues.append(
                    _issue(
                        rule_id="empty_state_label",
                        message="trajectory point state_label must be non-empty",
                        target=f"metrics.trajectory_points[{index}].state_label",
                    )
                )
            elif normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id="trajectory_point_state_label_unknown",
                        message="trajectory point state_label must stay inside declared state_labels",
                        target=f"metrics.trajectory_points[{index}].state_label",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            pseudotime = _require_numeric(
                point.get("pseudotime"),
                label=f"layout_sidecar.metrics.trajectory_points[{index}].pseudotime",
            )
            if not (0.0 <= pseudotime <= 1.0):
                issues.append(
                    _issue(
                        rule_id="trajectory_point_pseudotime_out_of_range",
                        message="trajectory point pseudotime must stay within [0, 1]",
                        target=f"metrics.trajectory_points[{index}].pseudotime",
                        observed=pseudotime,
                    )
                )
            x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.trajectory_points[{index}].x")
            y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.trajectory_points[{index}].y")
            if _point_within_box(trajectory_panel, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="trajectory_point_out_of_panel",
                    message="trajectory point must stay within the trajectory panel domain",
                    target=f"metrics.trajectory_points[{index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(trajectory_panel.box_id,),
                )
            )

    support_cells = sidecar.metrics.get("support_cells")
    if not isinstance(support_cells, list) or not support_cells:
        issues.append(
            _issue(
                rule_id="support_cells_missing",
                message="density-coverage panel requires non-empty support_cells metrics",
                target="metrics.support_cells",
            )
        )
    else:
        observed_contexts: set[str] = set()
        observed_states: set[str] = set()
        seen_coordinates: set[tuple[str, str]] = set()
        for index, cell in enumerate(support_cells):
            if not isinstance(cell, dict):
                raise ValueError(f"layout_sidecar.metrics.support_cells[{index}] must be an object")
            context_label = str(cell.get("x") or "").strip()
            state_label = str(cell.get("y") or "").strip()
            if not context_label or not state_label:
                issues.append(
                    _issue(
                        rule_id="support_cell_coordinate_missing",
                        message="support cell must include non-empty x and y labels",
                        target=f"metrics.support_cells[{index}]",
                    )
                )
                continue
            if normalized_context_labels and context_label not in normalized_context_labels:
                issues.append(
                    _issue(
                        rule_id="support_cell_context_unknown",
                        message="support cell x labels must stay inside declared context_labels",
                        target=f"metrics.support_cells[{index}].x",
                        observed=context_label,
                        expected=normalized_context_labels,
                    )
                )
            if normalized_state_labels and state_label not in normalized_state_labels:
                issues.append(
                    _issue(
                        rule_id="support_cell_state_unknown",
                        message="support cell y labels must stay inside declared state_labels",
                        target=f"metrics.support_cells[{index}].y",
                        observed=state_label,
                        expected=normalized_state_labels,
                    )
                )
            coordinate = (context_label, state_label)
            if coordinate in seen_coordinates:
                issues.append(
                    _issue(
                        rule_id="duplicate_support_cell",
                        message="support cell coordinates must be unique",
                        target=f"metrics.support_cells[{index}]",
                        observed={"x": context_label, "y": state_label},
                    )
                )
                continue
            seen_coordinates.add(coordinate)
            observed_contexts.add(context_label)
            observed_states.add(state_label)
            value = _require_numeric(
                cell.get("value"),
                label=f"layout_sidecar.metrics.support_cells[{index}].value",
            )
            if 0.0 <= value <= 1.0:
                continue
            issues.append(
                _issue(
                    rule_id="support_value_out_of_range",
                    message="support cell values must stay within [0, 1]",
                    target=f"metrics.support_cells[{index}].value",
                    observed=value,
                )
            )
        expected_coordinates = {(context_label, state_label) for state_label in normalized_state_labels for context_label in normalized_context_labels}
        if (
            normalized_context_labels
            and normalized_state_labels
            and (
                observed_contexts != set(normalized_context_labels)
                or observed_states != set(normalized_state_labels)
                or seen_coordinates != expected_coordinates
            )
        ):
            issues.append(
                _issue(
                    rule_id="support_grid_incomplete",
                    message="support grid must cover every declared context/state coordinate exactly once",
                    target="metrics.support_cells",
                    observed={"cells": len(seen_coordinates)},
                    expected={"cells": len(expected_coordinates)},
                )
            )

    return issues


def _check_publication_atlas_spatial_trajectory_context_support_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_publication_atlas_spatial_trajectory_storyboard_panel(sidecar)

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    if "panel_support" not in panel_boxes_by_id:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="context-support panel requires a support panel",
                target="panel_support",
                expected="present",
            )
        )
    for box_id, message in (
        ("support_panel_title", "context-support panel requires a support panel title"),
        ("support_x_axis_title", "context-support panel requires a support x-axis title"),
        ("support_y_axis_title", "context-support panel requires a support y-axis title"),
        ("panel_label_F", "context-support panel requires a panel label F"),
    ):
        if box_id in layout_boxes_by_id:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=box_id, expected="present"))

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={"panel_label_F": "panel_support"},
            allow_left_overhang_ratio=0.10,
        )
    )

    def _normalize_unique_labels(
        metric_key: str,
        missing_rule: str,
        empty_rule: str,
        duplicate_rule: str,
        message: str,
    ) -> list[str]:
        labels = sidecar.metrics.get(metric_key)
        if not isinstance(labels, list) or not labels:
            issues.append(_issue(rule_id=missing_rule, message=message, target=f"metrics.{metric_key}"))
            return []
        normalized: list[str] = []
        seen: set[str] = set()
        for index, item in enumerate(labels):
            label = str(item or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id=empty_rule,
                        message=f"{metric_key} labels must be non-empty",
                        target=f"metrics.{metric_key}[{index}]",
                    )
                )
                continue
            if label in seen:
                issues.append(
                    _issue(
                        rule_id=duplicate_rule,
                        message=f"{metric_key} label `{label}` must be unique",
                        target=f"metrics.{metric_key}",
                        observed=label,
                    )
                )
                continue
            seen.add(label)
            normalized.append(label)
        return normalized

    normalized_state_labels = _normalize_unique_labels(
        "state_labels",
        "state_labels_missing",
        "empty_state_label",
        "duplicate_state_label",
        "context-support panel requires explicit non-empty state_labels metrics",
    )
    normalized_context_labels = _normalize_unique_labels(
        "context_labels",
        "context_labels_missing",
        "empty_context_label",
        "duplicate_context_label",
        "context-support panel requires explicit non-empty context_labels metrics",
    )
    normalized_context_kinds = _normalize_unique_labels(
        "context_kinds",
        "context_kinds_missing",
        "empty_context_kind",
        "duplicate_context_kind",
        "context-support panel requires explicit non-empty context_kinds metrics",
    )
    required_context_kinds = {"atlas_density", "spatial_coverage", "trajectory_coverage"}
    if normalized_context_kinds and set(normalized_context_kinds) != required_context_kinds:
        issues.append(
            _issue(
                rule_id="support_context_kind_set_mismatch",
                message="context_kinds must cover atlas_density, spatial_coverage, and trajectory_coverage",
                target="metrics.context_kinds",
                observed=sorted(normalized_context_kinds),
                expected=sorted(required_context_kinds),
            )
        )
    if normalized_context_labels and normalized_context_kinds and len(normalized_context_labels) != len(normalized_context_kinds):
        issues.append(
            _issue(
                rule_id="support_context_label_kind_count_mismatch",
                message="context_labels and context_kinds must stay aligned one-to-one",
                target="metrics.context_kinds",
                observed=len(normalized_context_kinds),
                expected=len(normalized_context_labels),
            )
        )

    support_scale_label = str(sidecar.metrics.get("support_scale_label") or "").strip()
    if not support_scale_label:
        issues.append(
            _issue(
                rule_id="support_scale_label_missing",
                message="context-support panel requires a non-empty support_scale_label",
                target="metrics.support_scale_label",
            )
        )

    support_cells = sidecar.metrics.get("support_cells")
    if not isinstance(support_cells, list) or not support_cells:
        issues.append(
            _issue(
                rule_id="support_cells_missing",
                message="context-support panel requires non-empty support_cells metrics",
                target="metrics.support_cells",
            )
        )
        return issues

    observed_contexts: set[str] = set()
    observed_states: set[str] = set()
    seen_coordinates: set[tuple[str, str]] = set()
    for index, cell in enumerate(support_cells):
        if not isinstance(cell, dict):
            raise ValueError(f"layout_sidecar.metrics.support_cells[{index}] must be an object")
        context_label = str(cell.get("x") or "").strip()
        state_label = str(cell.get("y") or "").strip()
        if not context_label or not state_label:
            issues.append(
                _issue(
                    rule_id="support_cell_coordinate_missing",
                    message="support cell must include non-empty x and y labels",
                    target=f"metrics.support_cells[{index}]",
                )
            )
            continue
        if normalized_context_labels and context_label not in normalized_context_labels:
            issues.append(
                _issue(
                    rule_id="support_cell_context_unknown",
                    message="support cell x labels must stay inside declared context_labels",
                    target=f"metrics.support_cells[{index}].x",
                    observed=context_label,
                    expected=normalized_context_labels,
                )
            )
        if normalized_state_labels and state_label not in normalized_state_labels:
            issues.append(
                _issue(
                    rule_id="support_cell_state_unknown",
                    message="support cell y labels must stay inside declared state_labels",
                    target=f"metrics.support_cells[{index}].y",
                    observed=state_label,
                    expected=normalized_state_labels,
                )
            )
        coordinate = (context_label, state_label)
        if coordinate in seen_coordinates:
            issues.append(
                _issue(
                    rule_id="duplicate_support_cell",
                    message="support cell coordinates must be unique",
                    target=f"metrics.support_cells[{index}]",
                    observed={"x": context_label, "y": state_label},
                )
            )
            continue
        seen_coordinates.add(coordinate)
        observed_contexts.add(context_label)
        observed_states.add(state_label)
        value = _require_numeric(
            cell.get("value"),
            label=f"layout_sidecar.metrics.support_cells[{index}].value",
        )
        if 0.0 <= value <= 1.0:
            continue
        issues.append(
            _issue(
                rule_id="support_value_out_of_range",
                message="support cell values must stay within [0, 1]",
                target=f"metrics.support_cells[{index}].value",
                observed=value,
            )
        )
    expected_coordinates = {
        (context_label, state_label) for state_label in normalized_state_labels for context_label in normalized_context_labels
    }
    if (
        normalized_context_labels
        and normalized_state_labels
        and (
            observed_contexts != set(normalized_context_labels)
            or observed_states != set(normalized_state_labels)
            or seen_coordinates != expected_coordinates
        )
    ):
        issues.append(
            _issue(
                rule_id="support_grid_incomplete",
                message="support grid must cover every declared context/state coordinate exactly once",
                target="metrics.support_cells",
                observed={"cells": len(seen_coordinates)},
                expected={"cells": len(expected_coordinates)},
            )
        )

    return issues


def _matrix_cell_lookup(metrics: dict[str, Any]) -> dict[tuple[str, str], float]:
    cells = metrics.get("matrix_cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError("layout_sidecar.metrics.matrix_cells must be a non-empty list for heatmap qc")
    lookup: dict[tuple[str, str], float] = {}
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            raise ValueError(f"layout_sidecar.metrics.matrix_cells[{index}] must be an object")
        x_key = str(cell.get("x") or "").strip()
        y_key = str(cell.get("y") or "").strip()
        if not x_key or not y_key:
            raise ValueError(f"layout_sidecar.metrics.matrix_cells[{index}] must include x and y")
        lookup[(x_key, y_key)] = _require_numeric(cell.get("value"), label=f"layout_sidecar.metrics.matrix_cells[{index}].value")
    return lookup


def _check_publication_heatmap(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    panel = _first_box_of_type(sidecar.panel_boxes, "heatmap_tile_region") or _primary_panel(sidecar)
    if panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="heatmap qc requires a heatmap tile region",
                target="heatmap_tile_region",
                expected="present",
            )
        )
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("colorbar",)))
    issues.extend(_check_colorbar_panel_overlap(sidecar))

    annotation_bindings = sidecar.metrics.get("annotation_bindings")
    if annotation_bindings is not None:
        if not isinstance(annotation_bindings, list):
            raise ValueError("layout_sidecar.metrics.annotation_bindings must be a list when present")
        tile_boxes = {box.box_id: box for box in sidecar.panel_boxes + sidecar.layout_boxes if box.box_type == "heatmap_tile"}
        annotation_boxes = {box.box_id: box for box in sidecar.layout_boxes if box.box_type == "annotation_text"}
        for index, binding in enumerate(annotation_bindings):
            if not isinstance(binding, dict):
                raise ValueError(f"layout_sidecar.metrics.annotation_bindings[{index}] must be an object")
            tile_box_id = str(binding.get("tile_box_id") or "").strip()
            annotation_box_id = str(binding.get("annotation_box_id") or "").strip()
            tile_box = tile_boxes.get(tile_box_id)
            annotation_box = annotation_boxes.get(annotation_box_id)
            if tile_box is None or annotation_box is None:
                continue
            if (
                tile_box.x0 <= annotation_box.x0 <= tile_box.x1
                and tile_box.x0 <= annotation_box.x1 <= tile_box.x1
                and tile_box.y0 <= annotation_box.y0 <= tile_box.y1
                and tile_box.y0 <= annotation_box.y1 <= tile_box.y1
            ):
                continue
            issues.append(
                _issue(
                    rule_id="annotation_outside_tile",
                    message="annotation text must stay inside its tile box",
                    target="annotation_text",
                    box_refs=(annotation_box.box_id, tile_box.box_id),
                )
            )

    if sidecar.template_id == "performance_heatmap":
        metric_name = str(sidecar.metrics.get("metric_name") or "").strip()
        if not metric_name:
            issues.append(
                _issue(
                    rule_id="metric_name_missing",
                    message="performance heatmap qc requires a non-empty metric_name",
                    target="metrics.metric_name",
                )
            )
            return issues
        cell_lookup = _matrix_cell_lookup(sidecar.metrics)
        for (x_key, y_key), value in sorted(cell_lookup.items()):
            if 0.0 <= value <= 1.0:
                continue
            issues.append(
                _issue(
                    rule_id="performance_value_out_of_range",
                    message="performance heatmap values must stay within [0, 1]",
                    target="metrics.matrix_cells",
                    observed={"x": x_key, "y": y_key, "value": value},
                )
            )
        return issues

    if sidecar.template_id != "correlation_heatmap":
        return issues

    cell_lookup = _matrix_cell_lookup(sidecar.metrics)
    x_labels = {x_key for x_key, _ in cell_lookup}
    y_labels = {y_key for _, y_key in cell_lookup}
    if x_labels != y_labels:
        issues.append(
            _issue(
                rule_id="matrix_not_square",
                message="correlation heatmap must form a square matrix",
                target="metrics.matrix_cells",
                observed={"x_labels": sorted(x_labels), "y_labels": sorted(y_labels)},
            )
        )
    for label in sorted(x_labels | y_labels):
        if (label, label) in cell_lookup:
            continue
        issues.append(
            _issue(
                rule_id="matrix_missing_diagonal",
                message=f"diagonal cell for `{label}` is missing",
                target="metrics.matrix_cells",
                observed=label,
            )
        )
    for left in sorted(x_labels):
        for right in sorted(y_labels):
            forward = cell_lookup.get((left, right))
            reverse = cell_lookup.get((right, left))
            if forward is None or reverse is None:
                continue
            if math.isclose(forward, reverse, rel_tol=1e-9, abs_tol=1e-9):
                continue
            issues.append(
                _issue(
                    rule_id="matrix_not_symmetric",
                    message=f"matrix cells ({left}, {right}) and ({right}, {left}) must match",
                    target="metrics.matrix_cells",
                    observed={"forward": forward, "reverse": reverse},
                )
            )
            return issues
    return issues


def _check_publication_pathway_enrichment_dotplot_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "colorbar", "subplot_y_axis_title")))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))

    effect_scale_label = str(sidecar.metrics.get("effect_scale_label") or "").strip()
    if not effect_scale_label:
        issues.append(
            _issue(
                rule_id="effect_scale_label_missing",
                message="pathway enrichment dotplot requires a non-empty effect_scale_label",
                target="metrics.effect_scale_label",
            )
        )
    size_scale_label = str(sidecar.metrics.get("size_scale_label") or "").strip()
    if not size_scale_label:
        issues.append(
            _issue(
                rule_id="size_scale_label_missing",
                message="pathway enrichment dotplot requires a non-empty size_scale_label",
                target="metrics.size_scale_label",
            )
        )

    pathway_payload = sidecar.metrics.get("pathway_labels")
    if not isinstance(pathway_payload, list) or not pathway_payload:
        issues.append(
            _issue(
                rule_id="pathway_labels_missing",
                message="pathway enrichment dotplot requires non-empty pathway_labels metrics",
                target="metrics.pathway_labels",
            )
        )
        return issues
    pathway_labels = [str(label).strip() for label in pathway_payload]
    if any(not label for label in pathway_labels):
        issues.append(
            _issue(
                rule_id="pathway_label_empty",
                message="pathway_labels must be non-empty",
                target="metrics.pathway_labels",
            )
        )
    if len(set(pathway_labels)) != len(pathway_labels):
        issues.append(
            _issue(
                rule_id="pathway_labels_not_unique",
                message="pathway_labels must be unique",
                target="metrics.pathway_labels",
            )
        )

    panels_payload = sidecar.metrics.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="pathway enrichment dotplot requires non-empty panels metrics",
                target="metrics.panels",
            )
        )
        return issues
    if len(panels_payload) > 2:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="pathway enrichment dotplot supports at most two panels",
                target="metrics.panels",
                observed=len(panels_payload),
            )
        )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    declared_pathways = set(pathway_labels)
    seen_panel_ids: set[str] = set()

    for index, payload in enumerate(panels_payload):
        if not isinstance(payload, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{index}] must be an object")
        panel_id = str(payload.get("panel_id") or "").strip()
        if not panel_id:
            raise ValueError(f"layout_sidecar.metrics.panels[{index}].panel_id must be non-empty")
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="panel_id_not_unique",
                    message="panel_id must be unique across panels",
                    target=f"metrics.panels[{index}].panel_id",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)

        panel_box_id = str(payload.get("panel_box_id") or "").strip()
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="panel_box_id must resolve to an existing panel box",
                    target=f"metrics.panels[{index}].panel_box_id",
                    observed=panel_box_id,
                )
            )
        panel_label_box_id = str(payload.get("panel_label_box_id") or "").strip()
        panel_label_box = layout_boxes_by_id.get(panel_label_box_id)
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_box_missing",
                    message="panel_label_box_id must resolve to an existing layout box",
                    target=f"metrics.panels[{index}].panel_label_box_id",
                    observed=panel_label_box_id,
                )
            )
        elif panel_box is not None and not _boxes_overlap(panel_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_anchor_drift",
                    message="panel label must stay anchored inside its panel",
                    target=f"metrics.panels[{index}].panel_label_box_id",
                    box_refs=(panel_label_box.box_id, panel_box.box_id),
                )
            )
        for field_name in ("panel_title_box_id", "x_axis_title_box_id"):
            box_id = str(payload.get(field_name) or "").strip()
            if box_id and box_id in layout_boxes_by_id:
                continue
            issues.append(
                _issue(
                    rule_id="layout_box_missing",
                    message=f"{field_name} must resolve to an existing layout box",
                    target=f"metrics.panels[{index}].{field_name}",
                    observed=box_id,
                )
            )

        points_payload = payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            issues.append(
                _issue(
                    rule_id="panel_points_missing",
                    message="every panel must expose non-empty points metrics",
                    target=f"metrics.panels[{index}].points",
                )
            )
            continue

        observed_pathways: set[str] = set()
        for point_index, point in enumerate(points_payload):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{index}].points[{point_index}] must be an object")
            pathway_label = str(point.get("pathway_label") or "").strip()
            if not pathway_label:
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{index}].points[{point_index}].pathway_label must be non-empty"
                )
            if pathway_label not in declared_pathways:
                issues.append(
                    _issue(
                        rule_id="point_pathway_unknown",
                        message="point pathway_label must stay inside declared pathway_labels",
                        target=f"metrics.panels[{index}].points[{point_index}].pathway_label",
                        observed=pathway_label,
                    )
                )
            observed_pathways.add(pathway_label)
            x_value = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].x",
            )
            y_value = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].y",
            )
            _require_numeric(
                point.get("effect_value"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].effect_value",
            )
            size_value = _require_numeric(
                point.get("size_value"),
                label=f"layout_sidecar.metrics.panels[{index}].points[{point_index}].size_value",
            )
            if size_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="point_size_negative",
                        message="point size_value must be non-negative",
                        target=f"metrics.panels[{index}].points[{point_index}].size_value",
                        observed=size_value,
                    )
                )
            if panel_box is not None and not _point_within_box(panel_box, x=x_value, y=y_value):
                issues.append(
                    _issue(
                        rule_id="dot_out_of_panel",
                        message="dot center must stay within its panel domain",
                        target=f"metrics.panels[{index}].points[{point_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
        if observed_pathways != declared_pathways:
            issues.append(
                _issue(
                    rule_id="panel_pathway_coverage_mismatch",
                    message="each panel must cover every declared pathway exactly once",
                    target=f"metrics.panels[{index}].points",
                    observed=sorted(observed_pathways),
                    expected=sorted(declared_pathways),
                )
            )

    return issues


def _check_publication_oncoplot_mutation_landscape_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "subplot_y_axis_title", "panel_label")))
    issues.extend(_check_legend_panel_overlap(sidecar))

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    required_panel_ids = ("panel_burden", "panel_annotations", "panel_matrix", "panel_frequency")
    for panel_id in required_panel_ids:
        if panel_id not in panel_boxes_by_id:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message=f"oncoplot mutation landscape requires `{panel_id}` panel box",
                    target=f"panel_boxes.{panel_id}",
                    observed=sorted(panel_boxes_by_id),
                )
            )

    label_box = layout_boxes_by_id.get("panel_label_A")
    burden_panel_box = panel_boxes_by_id.get("panel_burden")
    if label_box is None:
        issues.append(
            _issue(
                rule_id="missing_panel_label",
                message="oncoplot mutation landscape requires panel_label_A",
                target="layout_boxes.panel_label_A",
            )
        )

    mutation_legend_title = str(sidecar.metrics.get("mutation_legend_title") or "").strip()
    if not mutation_legend_title:
        issues.append(
            _issue(
                rule_id="mutation_legend_title_missing",
                message="oncoplot mutation landscape requires a non-empty mutation_legend_title",
                target="metrics.mutation_legend_title",
            )
        )

    sample_payload = sidecar.metrics.get("sample_ids")
    if not isinstance(sample_payload, list) or not sample_payload:
        issues.append(
            _issue(
                rule_id="sample_ids_missing",
                message="oncoplot mutation landscape requires non-empty sample_ids metrics",
                target="metrics.sample_ids",
            )
        )
        return issues
    sample_ids = [str(item).strip() for item in sample_payload]
    if any(not item for item in sample_ids):
        issues.append(
            _issue(
                rule_id="sample_id_empty",
                message="sample_ids must be non-empty",
                target="metrics.sample_ids",
            )
        )
    if len(set(sample_ids)) != len(sample_ids):
        issues.append(
            _issue(
                rule_id="sample_ids_not_unique",
                message="sample_ids must be unique",
                target="metrics.sample_ids",
            )
        )
    declared_sample_ids = set(sample_ids)

    gene_payload = sidecar.metrics.get("gene_labels")
    if not isinstance(gene_payload, list) or not gene_payload:
        issues.append(
            _issue(
                rule_id="gene_labels_missing",
                message="oncoplot mutation landscape requires non-empty gene_labels metrics",
                target="metrics.gene_labels",
            )
        )
        return issues
    gene_labels = [str(item).strip() for item in gene_payload]
    if any(not item for item in gene_labels):
        issues.append(
            _issue(
                rule_id="gene_label_empty",
                message="gene_labels must be non-empty",
                target="metrics.gene_labels",
            )
        )
    if len(set(gene_labels)) != len(gene_labels):
        issues.append(
            _issue(
                rule_id="gene_labels_not_unique",
                message="gene_labels must be unique",
                target="metrics.gene_labels",
            )
        )
    declared_gene_labels = set(gene_labels)

    supported_alteration_classes = {"missense", "truncating", "amplification", "fusion"}

    sample_burdens = sidecar.metrics.get("sample_burdens")
    if not isinstance(sample_burdens, list) or not sample_burdens:
        issues.append(
            _issue(
                rule_id="sample_burdens_missing",
                message="oncoplot mutation landscape requires non-empty sample_burdens metrics",
                target="metrics.sample_burdens",
            )
        )
    else:
        observed_burden_samples: set[str] = set()
        for index, item in enumerate(sample_burdens):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.sample_burdens[{index}] must be an object")
            sample_id = str(item.get("sample_id") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="sample_burden_sample_unknown",
                        message="sample_burdens must stay inside declared sample_ids",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if sample_id in observed_burden_samples:
                issues.append(
                    _issue(
                        rule_id="sample_burden_duplicate",
                        message="sample_burdens must cover each declared sample exactly once",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            observed_burden_samples.add(sample_id)
            _require_numeric(
                item.get("altered_gene_count"),
                label=f"layout_sidecar.metrics.sample_burdens[{index}].altered_gene_count",
            )
            bar_box_id = str(item.get("bar_box_id") or "").strip()
            bar_box = layout_boxes_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="sample_burden_box_missing",
                        message="sample_burdens bar_box_id must resolve to an existing layout box",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
            elif burden_panel_box is not None and not _boxes_overlap(bar_box, burden_panel_box):
                issues.append(
                    _issue(
                        rule_id="sample_burden_out_of_panel",
                        message="sample burden bars must stay inside panel_burden",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        box_refs=(bar_box.box_id, burden_panel_box.box_id),
                    )
                )
        if observed_burden_samples != declared_sample_ids:
            issues.append(
                _issue(
                    rule_id="sample_burden_coverage_mismatch",
                    message="sample_burdens must cover every declared sample exactly once",
                    target="metrics.sample_burdens",
                    observed=sorted(observed_burden_samples),
                    expected=sorted(declared_sample_ids),
                )
            )

    gene_frequencies = sidecar.metrics.get("gene_altered_frequencies")
    frequency_panel_box = panel_boxes_by_id.get("panel_frequency")
    if not isinstance(gene_frequencies, list) or not gene_frequencies:
        issues.append(
            _issue(
                rule_id="gene_altered_frequencies_missing",
                message="oncoplot mutation landscape requires non-empty gene_altered_frequencies metrics",
                target="metrics.gene_altered_frequencies",
            )
        )
    else:
        observed_frequency_genes: set[str] = set()
        for index, item in enumerate(gene_frequencies):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.gene_altered_frequencies[{index}] must be an object")
            gene_label = str(item.get("gene_label") or "").strip()
            if gene_label not in declared_gene_labels:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_gene_unknown",
                        message="gene_altered_frequencies must stay inside declared gene_labels",
                        target=f"metrics.gene_altered_frequencies[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            if gene_label in observed_frequency_genes:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_duplicate",
                        message="gene_altered_frequencies must cover each declared gene exactly once",
                        target=f"metrics.gene_altered_frequencies[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            observed_frequency_genes.add(gene_label)
            altered_fraction = _require_numeric(
                item.get("altered_fraction"),
                label=f"layout_sidecar.metrics.gene_altered_frequencies[{index}].altered_fraction",
            )
            if altered_fraction < 0.0 or altered_fraction > 1.0:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_fraction_invalid",
                        message="altered_fraction must stay within [0, 1]",
                        target=f"metrics.gene_altered_frequencies[{index}].altered_fraction",
                        observed=altered_fraction,
                    )
                )
            bar_box_id = str(item.get("bar_box_id") or "").strip()
            bar_box = layout_boxes_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_box_missing",
                        message="gene_altered_frequencies bar_box_id must resolve to an existing layout box",
                        target=f"metrics.gene_altered_frequencies[{index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
            elif frequency_panel_box is not None and not _boxes_overlap(bar_box, frequency_panel_box):
                issues.append(
                    _issue(
                        rule_id="gene_frequency_out_of_panel",
                        message="gene altered-frequency bars must stay inside panel_frequency",
                        target=f"metrics.gene_altered_frequencies[{index}].bar_box_id",
                        box_refs=(bar_box.box_id, frequency_panel_box.box_id),
                    )
                )
        if observed_frequency_genes != declared_gene_labels:
            issues.append(
                _issue(
                    rule_id="gene_frequency_coverage_mismatch",
                    message="gene_altered_frequencies must cover every declared gene exactly once",
                    target="metrics.gene_altered_frequencies",
                    observed=sorted(observed_frequency_genes),
                    expected=sorted(declared_gene_labels),
                )
            )

    annotation_panel_box = panel_boxes_by_id.get("panel_annotations")
    annotation_tracks = sidecar.metrics.get("annotation_tracks")
    if not isinstance(annotation_tracks, list) or not annotation_tracks:
        issues.append(
            _issue(
                rule_id="annotation_tracks_missing",
                message="oncoplot mutation landscape requires non-empty annotation_tracks metrics",
                target="metrics.annotation_tracks",
            )
        )
    else:
        if len(annotation_tracks) > 3:
            issues.append(
                _issue(
                    rule_id="annotation_track_count_invalid",
                    message="oncoplot mutation landscape supports at most three annotation tracks",
                    target="metrics.annotation_tracks",
                    observed=len(annotation_tracks),
                )
            )
        seen_track_ids: set[str] = set()
        for index, track in enumerate(annotation_tracks):
            if not isinstance(track, dict):
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}] must be an object")
            track_id = str(track.get("track_id") or "").strip()
            if not track_id:
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}].track_id must be non-empty")
            if track_id in seen_track_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_id_not_unique",
                        message="annotation track ids must be unique",
                        target=f"metrics.annotation_tracks[{index}].track_id",
                        observed=track_id,
                    )
                )
            seen_track_ids.add(track_id)
            if not str(track.get("track_label") or "").strip():
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_invalid",
                        message="annotation track labels must be non-empty",
                        target=f"metrics.annotation_tracks[{index}].track_label",
                    )
                )
            track_label_box_id = str(track.get("track_label_box_id") or "").strip()
            track_label_box = layout_boxes_by_id.get(track_label_box_id)
            if track_label_box is None:
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_box_missing",
                        message="annotation track label box must resolve to an existing layout box",
                        target=f"metrics.annotation_tracks[{index}].track_label_box_id",
                        observed=track_label_box_id,
                    )
                )
            cells = track.get("cells")
            if not isinstance(cells, list) or not cells:
                issues.append(
                    _issue(
                        rule_id="annotation_track_cells_missing",
                        message="annotation track must expose non-empty cells metrics",
                        target=f"metrics.annotation_tracks[{index}].cells",
                    )
                )
                continue
            observed_track_samples: set[str] = set()
            for cell_index, cell in enumerate(cells):
                if not isinstance(cell, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.annotation_tracks[{index}].cells[{cell_index}] must be an object"
                    )
                sample_id = str(cell.get("sample_id") or "").strip()
                if sample_id not in declared_sample_ids:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_unknown",
                            message="annotation track cells must stay inside declared sample_ids",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                if sample_id in observed_track_samples:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_duplicate",
                            message="annotation track cells must cover each sample exactly once",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                observed_track_samples.add(sample_id)
                if not str(cell.get("category_label") or "").strip():
                    issues.append(
                        _issue(
                            rule_id="annotation_track_category_invalid",
                            message="annotation track category labels must be non-empty",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].category_label",
                        )
                    )
                box_id = str(cell.get("box_id") or "").strip()
                box = layout_boxes_by_id.get(box_id)
                if box is None:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_missing",
                            message="annotation track cell box_id must resolve to an existing layout box",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            observed=box_id,
                        )
                    )
                elif annotation_panel_box is not None and not _boxes_overlap(box, annotation_panel_box):
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_out_of_panel",
                            message="annotation track cells must stay inside panel_annotations",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            box_refs=(box.box_id, annotation_panel_box.box_id),
                        )
                    )
            if observed_track_samples != declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_coverage_mismatch",
                        message="each annotation track must cover every declared sample exactly once",
                        target=f"metrics.annotation_tracks[{index}].cells",
                        observed=sorted(observed_track_samples),
                        expected=sorted(declared_sample_ids),
                    )
                )

    matrix_panel_box = panel_boxes_by_id.get("panel_matrix")
    altered_cells = sidecar.metrics.get("altered_cells")
    if not isinstance(altered_cells, list) or not altered_cells:
        issues.append(
            _issue(
                rule_id="altered_cells_missing",
                message="oncoplot mutation landscape requires non-empty altered_cells metrics",
                target="metrics.altered_cells",
            )
        )
    else:
        observed_coordinates: set[tuple[str, str]] = set()
        for index, cell in enumerate(altered_cells):
            if not isinstance(cell, dict):
                raise ValueError(f"layout_sidecar.metrics.altered_cells[{index}] must be an object")
            sample_id = str(cell.get("sample_id") or "").strip()
            gene_label = str(cell.get("gene_label") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="altered_cell_sample_unknown",
                        message="altered_cells sample ids must stay inside declared sample_ids",
                        target=f"metrics.altered_cells[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if gene_label not in declared_gene_labels:
                issues.append(
                    _issue(
                        rule_id="altered_cell_gene_unknown",
                        message="altered_cells gene labels must stay inside declared gene_labels",
                        target=f"metrics.altered_cells[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            coordinate = (sample_id, gene_label)
            if coordinate in observed_coordinates:
                issues.append(
                    _issue(
                        rule_id="altered_cell_coordinate_duplicate",
                        message="altered_cells must keep sample/gene coordinates unique",
                        target=f"metrics.altered_cells[{index}]",
                        observed={"sample_id": sample_id, "gene_label": gene_label},
                    )
                )
            observed_coordinates.add(coordinate)
            alteration_class = str(cell.get("alteration_class") or "").strip()
            if alteration_class not in supported_alteration_classes:
                issues.append(
                    _issue(
                        rule_id="alteration_class_invalid",
                        message="altered_cells must use the supported alteration vocabulary",
                        target=f"metrics.altered_cells[{index}].alteration_class",
                        observed=alteration_class,
                    )
                )
            box_id = str(cell.get("box_id") or "").strip()
            box = layout_boxes_by_id.get(box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id="altered_cell_box_missing",
                        message="altered_cells box_id must resolve to an existing layout box",
                        target=f"metrics.altered_cells[{index}].box_id",
                        observed=box_id,
                    )
                )
            elif matrix_panel_box is not None and not _boxes_overlap(box, matrix_panel_box):
                issues.append(
                    _issue(
                        rule_id="altered_cell_box_out_of_panel",
                        message="altered mutation cells must stay inside panel_matrix",
                        target=f"metrics.altered_cells[{index}].box_id",
                        box_refs=(box.box_id, matrix_panel_box.box_id),
                    )
                )

    return issues


def _check_publication_cnv_recurrence_summary_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "subplot_y_axis_title", "panel_label")))
    issues.extend(_check_legend_panel_overlap(sidecar))

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    required_panel_ids = ("panel_burden", "panel_annotations", "panel_matrix", "panel_frequency")
    for panel_id in required_panel_ids:
        if panel_id not in panel_boxes_by_id:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message=f"cnv recurrence summary requires `{panel_id}` panel box",
                    target=f"panel_boxes.{panel_id}",
                    observed=sorted(panel_boxes_by_id),
                )
            )

    label_box = layout_boxes_by_id.get("panel_label_A")
    burden_panel_box = panel_boxes_by_id.get("panel_burden")
    if label_box is None:
        issues.append(
            _issue(
                rule_id="missing_panel_label",
                message="cnv recurrence summary requires panel_label_A",
                target="layout_boxes.panel_label_A",
            )
        )

    cnv_legend_title = str(sidecar.metrics.get("cnv_legend_title") or "").strip()
    if not cnv_legend_title:
        issues.append(
            _issue(
                rule_id="cnv_legend_title_missing",
                message="cnv recurrence summary requires a non-empty cnv_legend_title",
                target="metrics.cnv_legend_title",
            )
        )

    sample_payload = sidecar.metrics.get("sample_ids")
    if not isinstance(sample_payload, list) or not sample_payload:
        issues.append(
            _issue(
                rule_id="sample_ids_missing",
                message="cnv recurrence summary requires non-empty sample_ids metrics",
                target="metrics.sample_ids",
            )
        )
        return issues
    sample_ids = [str(item).strip() for item in sample_payload]
    if any(not item for item in sample_ids):
        issues.append(
            _issue(
                rule_id="sample_id_empty",
                message="sample_ids must be non-empty",
                target="metrics.sample_ids",
            )
        )
    if len(set(sample_ids)) != len(sample_ids):
        issues.append(
            _issue(
                rule_id="sample_ids_not_unique",
                message="sample_ids must be unique",
                target="metrics.sample_ids",
            )
        )
    declared_sample_ids = set(sample_ids)

    region_payload = sidecar.metrics.get("region_labels")
    if not isinstance(region_payload, list) or not region_payload:
        issues.append(
            _issue(
                rule_id="region_labels_missing",
                message="cnv recurrence summary requires non-empty region_labels metrics",
                target="metrics.region_labels",
            )
        )
        return issues
    region_labels = [str(item).strip() for item in region_payload]
    if any(not item for item in region_labels):
        issues.append(
            _issue(
                rule_id="region_label_empty",
                message="region_labels must be non-empty",
                target="metrics.region_labels",
            )
        )
    if len(set(region_labels)) != len(region_labels):
        issues.append(
            _issue(
                rule_id="region_labels_not_unique",
                message="region_labels must be unique",
                target="metrics.region_labels",
            )
        )
    declared_region_labels = set(region_labels)

    supported_cnv_states = {"amplification", "gain", "loss", "deep_loss"}

    sample_burdens = sidecar.metrics.get("sample_burdens")
    if not isinstance(sample_burdens, list) or not sample_burdens:
        issues.append(
            _issue(
                rule_id="sample_burdens_missing",
                message="cnv recurrence summary requires non-empty sample_burdens metrics",
                target="metrics.sample_burdens",
            )
        )
    else:
        observed_burden_samples: set[str] = set()
        for index, item in enumerate(sample_burdens):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.sample_burdens[{index}] must be an object")
            sample_id = str(item.get("sample_id") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="sample_burden_sample_unknown",
                        message="sample_burdens must stay inside declared sample_ids",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if sample_id in observed_burden_samples:
                issues.append(
                    _issue(
                        rule_id="sample_burden_duplicate",
                        message="sample_burdens must cover each declared sample exactly once",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            observed_burden_samples.add(sample_id)
            _require_numeric(
                item.get("altered_region_count"),
                label=f"layout_sidecar.metrics.sample_burdens[{index}].altered_region_count",
            )
            bar_box_id = str(item.get("bar_box_id") or "").strip()
            bar_box = layout_boxes_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="sample_burden_box_missing",
                        message="sample_burdens bar_box_id must resolve to an existing layout box",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
            elif burden_panel_box is not None and not _boxes_overlap(bar_box, burden_panel_box):
                issues.append(
                    _issue(
                        rule_id="sample_burden_out_of_panel",
                        message="sample burden bars must stay inside panel_burden",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        box_refs=(bar_box.box_id, burden_panel_box.box_id),
                    )
                )
        if observed_burden_samples != declared_sample_ids:
            issues.append(
                _issue(
                    rule_id="sample_burden_coverage_mismatch",
                    message="sample_burdens must cover every declared sample exactly once",
                    target="metrics.sample_burdens",
                    observed=sorted(observed_burden_samples),
                    expected=sorted(declared_sample_ids),
                )
            )

    region_frequencies = sidecar.metrics.get("region_gain_loss_frequencies")
    frequency_panel_box = panel_boxes_by_id.get("panel_frequency")
    if not isinstance(region_frequencies, list) or not region_frequencies:
        issues.append(
            _issue(
                rule_id="region_gain_loss_frequencies_missing",
                message="cnv recurrence summary requires non-empty region_gain_loss_frequencies metrics",
                target="metrics.region_gain_loss_frequencies",
            )
        )
    else:
        observed_frequency_regions: set[str] = set()
        for index, item in enumerate(region_frequencies):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.region_gain_loss_frequencies[{index}] must be an object")
            region_label = str(item.get("region_label") or "").strip()
            if region_label not in declared_region_labels:
                issues.append(
                    _issue(
                        rule_id="region_frequency_region_unknown",
                        message="region_gain_loss_frequencies must stay inside declared region_labels",
                        target=f"metrics.region_gain_loss_frequencies[{index}].region_label",
                        observed=region_label,
                    )
                )
            if region_label in observed_frequency_regions:
                issues.append(
                    _issue(
                        rule_id="region_frequency_duplicate",
                        message="region_gain_loss_frequencies must cover each declared region exactly once",
                        target=f"metrics.region_gain_loss_frequencies[{index}].region_label",
                        observed=region_label,
                    )
                )
            observed_frequency_regions.add(region_label)
            for field_name in ("gain_fraction", "loss_fraction"):
                fraction_value = _require_numeric(
                    item.get(field_name),
                    label=f"layout_sidecar.metrics.region_gain_loss_frequencies[{index}].{field_name}",
                )
                if fraction_value < 0.0 or fraction_value > 1.0:
                    issues.append(
                        _issue(
                            rule_id="region_frequency_fraction_invalid",
                            message=f"{field_name} must stay within [0, 1]",
                            target=f"metrics.region_gain_loss_frequencies[{index}].{field_name}",
                            observed=fraction_value,
                        )
                    )
            for field_name in ("gain_bar_box_id", "loss_bar_box_id"):
                bar_box_id = str(item.get(field_name) or "").strip()
                bar_box = layout_boxes_by_id.get(bar_box_id)
                if bar_box is None:
                    issues.append(
                        _issue(
                            rule_id="region_frequency_box_missing",
                            message="region gain/loss bar boxes must resolve to existing layout boxes",
                            target=f"metrics.region_gain_loss_frequencies[{index}].{field_name}",
                            observed=bar_box_id,
                        )
                    )
                elif frequency_panel_box is not None and not _boxes_overlap(bar_box, frequency_panel_box):
                    issues.append(
                        _issue(
                            rule_id="region_frequency_out_of_panel",
                            message="region gain/loss frequency bars must stay inside panel_frequency",
                            target=f"metrics.region_gain_loss_frequencies[{index}].{field_name}",
                            box_refs=(bar_box.box_id, frequency_panel_box.box_id),
                        )
                    )
        if observed_frequency_regions != declared_region_labels:
            issues.append(
                _issue(
                    rule_id="region_frequency_coverage_mismatch",
                    message="region_gain_loss_frequencies must cover every declared region exactly once",
                    target="metrics.region_gain_loss_frequencies",
                    observed=sorted(observed_frequency_regions),
                    expected=sorted(declared_region_labels),
                )
            )

    annotation_panel_box = panel_boxes_by_id.get("panel_annotations")
    annotation_tracks = sidecar.metrics.get("annotation_tracks")
    if not isinstance(annotation_tracks, list) or not annotation_tracks:
        issues.append(
            _issue(
                rule_id="annotation_tracks_missing",
                message="cnv recurrence summary requires non-empty annotation_tracks metrics",
                target="metrics.annotation_tracks",
            )
        )
    else:
        if len(annotation_tracks) > 3:
            issues.append(
                _issue(
                    rule_id="annotation_track_count_invalid",
                    message="cnv recurrence summary supports at most three annotation tracks",
                    target="metrics.annotation_tracks",
                    observed=len(annotation_tracks),
                )
            )
        seen_track_ids: set[str] = set()
        for index, track in enumerate(annotation_tracks):
            if not isinstance(track, dict):
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}] must be an object")
            track_id = str(track.get("track_id") or "").strip()
            if not track_id:
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}].track_id must be non-empty")
            if track_id in seen_track_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_id_not_unique",
                        message="annotation track ids must be unique",
                        target=f"metrics.annotation_tracks[{index}].track_id",
                        observed=track_id,
                    )
                )
            seen_track_ids.add(track_id)
            if not str(track.get("track_label") or "").strip():
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_invalid",
                        message="annotation track labels must be non-empty",
                        target=f"metrics.annotation_tracks[{index}].track_label",
                    )
                )
            track_label_box_id = str(track.get("track_label_box_id") or "").strip()
            track_label_box = layout_boxes_by_id.get(track_label_box_id)
            if track_label_box is None:
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_box_missing",
                        message="annotation track label box must resolve to an existing layout box",
                        target=f"metrics.annotation_tracks[{index}].track_label_box_id",
                        observed=track_label_box_id,
                    )
                )
            cells = track.get("cells")
            if not isinstance(cells, list) or not cells:
                issues.append(
                    _issue(
                        rule_id="annotation_track_cells_missing",
                        message="annotation track must expose non-empty cells metrics",
                        target=f"metrics.annotation_tracks[{index}].cells",
                    )
                )
                continue
            observed_track_samples: set[str] = set()
            for cell_index, cell in enumerate(cells):
                if not isinstance(cell, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.annotation_tracks[{index}].cells[{cell_index}] must be an object"
                    )
                sample_id = str(cell.get("sample_id") or "").strip()
                if sample_id not in declared_sample_ids:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_unknown",
                            message="annotation track cells must stay inside declared sample_ids",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                if sample_id in observed_track_samples:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_duplicate",
                            message="annotation track cells must cover each sample exactly once",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                observed_track_samples.add(sample_id)
                if not str(cell.get("category_label") or "").strip():
                    issues.append(
                        _issue(
                            rule_id="annotation_track_category_invalid",
                            message="annotation track category labels must be non-empty",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].category_label",
                        )
                    )
                box_id = str(cell.get("box_id") or "").strip()
                box = layout_boxes_by_id.get(box_id)
                if box is None:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_missing",
                            message="annotation track cell box_id must resolve to an existing layout box",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            observed=box_id,
                        )
                    )
                elif annotation_panel_box is not None and not _boxes_overlap(box, annotation_panel_box):
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_out_of_panel",
                            message="annotation track cells must stay inside panel_annotations",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            box_refs=(box.box_id, annotation_panel_box.box_id),
                        )
                    )
            if observed_track_samples != declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_coverage_mismatch",
                        message="each annotation track must cover every declared sample exactly once",
                        target=f"metrics.annotation_tracks[{index}].cells",
                        observed=sorted(observed_track_samples),
                        expected=sorted(declared_sample_ids),
                    )
                )

    matrix_panel_box = panel_boxes_by_id.get("panel_matrix")
    cnv_cells = sidecar.metrics.get("cnv_cells")
    if not isinstance(cnv_cells, list) or not cnv_cells:
        issues.append(
            _issue(
                rule_id="cnv_cells_missing",
                message="cnv recurrence summary requires non-empty cnv_cells metrics",
                target="metrics.cnv_cells",
            )
        )
    else:
        observed_coordinates: set[tuple[str, str]] = set()
        for index, cell in enumerate(cnv_cells):
            if not isinstance(cell, dict):
                raise ValueError(f"layout_sidecar.metrics.cnv_cells[{index}] must be an object")
            sample_id = str(cell.get("sample_id") or "").strip()
            region_label = str(cell.get("region_label") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="cnv_cell_sample_unknown",
                        message="cnv_cells sample ids must stay inside declared sample_ids",
                        target=f"metrics.cnv_cells[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if region_label not in declared_region_labels:
                issues.append(
                    _issue(
                        rule_id="cnv_cell_region_unknown",
                        message="cnv_cells region labels must stay inside declared region_labels",
                        target=f"metrics.cnv_cells[{index}].region_label",
                        observed=region_label,
                    )
                )
            coordinate = (sample_id, region_label)
            if coordinate in observed_coordinates:
                issues.append(
                    _issue(
                        rule_id="cnv_cell_coordinate_duplicate",
                        message="cnv_cells must keep sample/region coordinates unique",
                        target=f"metrics.cnv_cells[{index}]",
                        observed={"sample_id": sample_id, "region_label": region_label},
                    )
                )
            observed_coordinates.add(coordinate)
            cnv_state = str(cell.get("cnv_state") or "").strip()
            if cnv_state not in supported_cnv_states:
                issues.append(
                    _issue(
                        rule_id="cnv_state_invalid",
                        message="cnv_cells must use the supported cnv_state vocabulary",
                        target=f"metrics.cnv_cells[{index}].cnv_state",
                        observed=cnv_state,
                    )
                )
            box_id = str(cell.get("box_id") or "").strip()
            box = layout_boxes_by_id.get(box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id="cnv_cell_box_missing",
                        message="cnv_cells box_id must resolve to an existing layout box",
                        target=f"metrics.cnv_cells[{index}].box_id",
                        observed=box_id,
                    )
                )
            elif matrix_panel_box is not None and not _boxes_overlap(box, matrix_panel_box):
                issues.append(
                    _issue(
                        rule_id="cnv_cell_box_out_of_panel",
                        message="cnv cells must stay inside panel_matrix",
                        target=f"metrics.cnv_cells[{index}].box_id",
                        box_refs=(box.box_id, matrix_panel_box.box_id),
                    )
                )

    return issues


def _check_publication_genomic_alteration_landscape_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "subplot_y_axis_title", "panel_label")))
    issues.extend(_check_legend_panel_overlap(sidecar))

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    required_panel_ids = ("panel_burden", "panel_annotations", "panel_matrix", "panel_frequency")
    for panel_id in required_panel_ids:
        if panel_id not in panel_boxes_by_id:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message=f"genomic alteration landscape requires `{panel_id}` panel box",
                    target=f"panel_boxes.{panel_id}",
                    observed=sorted(panel_boxes_by_id),
                )
            )

    if layout_boxes_by_id.get("panel_label_A") is None:
        issues.append(
            _issue(
                rule_id="missing_panel_label",
                message="genomic alteration landscape requires panel_label_A",
                target="layout_boxes.panel_label_A",
            )
        )

    alteration_legend_title = str(sidecar.metrics.get("alteration_legend_title") or "").strip()
    if not alteration_legend_title:
        issues.append(
            _issue(
                rule_id="alteration_legend_title_missing",
                message="genomic alteration landscape requires a non-empty alteration_legend_title",
                target="metrics.alteration_legend_title",
            )
        )

    sample_payload = sidecar.metrics.get("sample_ids")
    if not isinstance(sample_payload, list) or not sample_payload:
        issues.append(
            _issue(
                rule_id="sample_ids_missing",
                message="genomic alteration landscape requires non-empty sample_ids metrics",
                target="metrics.sample_ids",
            )
        )
        return issues
    sample_ids = [str(item).strip() for item in sample_payload]
    if any(not item for item in sample_ids):
        issues.append(
            _issue(
                rule_id="sample_id_empty",
                message="sample_ids must be non-empty",
                target="metrics.sample_ids",
            )
        )
    if len(set(sample_ids)) != len(sample_ids):
        issues.append(
            _issue(
                rule_id="sample_ids_not_unique",
                message="sample_ids must be unique",
                target="metrics.sample_ids",
            )
        )
    declared_sample_ids = set(sample_ids)

    gene_payload = sidecar.metrics.get("gene_labels")
    if not isinstance(gene_payload, list) or not gene_payload:
        issues.append(
            _issue(
                rule_id="gene_labels_missing",
                message="genomic alteration landscape requires non-empty gene_labels metrics",
                target="metrics.gene_labels",
            )
        )
        return issues
    gene_labels = [str(item).strip() for item in gene_payload]
    if any(not item for item in gene_labels):
        issues.append(
            _issue(
                rule_id="gene_label_empty",
                message="gene_labels must be non-empty",
                target="metrics.gene_labels",
            )
        )
    if len(set(gene_labels)) != len(gene_labels):
        issues.append(
            _issue(
                rule_id="gene_labels_not_unique",
                message="gene_labels must be unique",
                target="metrics.gene_labels",
            )
        )
    declared_gene_labels = set(gene_labels)

    burden_panel_box = panel_boxes_by_id.get("panel_burden")
    sample_burdens = sidecar.metrics.get("sample_burdens")
    if not isinstance(sample_burdens, list) or not sample_burdens:
        issues.append(
            _issue(
                rule_id="sample_burdens_missing",
                message="genomic alteration landscape requires non-empty sample_burdens metrics",
                target="metrics.sample_burdens",
            )
        )
    else:
        observed_burden_samples: set[str] = set()
        for index, item in enumerate(sample_burdens):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.sample_burdens[{index}] must be an object")
            sample_id = str(item.get("sample_id") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="sample_burden_sample_unknown",
                        message="sample_burdens must stay inside declared sample_ids",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if sample_id in observed_burden_samples:
                issues.append(
                    _issue(
                        rule_id="sample_burden_duplicate",
                        message="sample_burdens must cover each declared sample exactly once",
                        target=f"metrics.sample_burdens[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            observed_burden_samples.add(sample_id)
            _require_numeric(
                item.get("altered_gene_count"),
                label=f"layout_sidecar.metrics.sample_burdens[{index}].altered_gene_count",
            )
            bar_box_id = str(item.get("bar_box_id") or "").strip()
            bar_box = layout_boxes_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="sample_burden_box_missing",
                        message="sample_burdens bar_box_id must resolve to an existing layout box",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
            elif burden_panel_box is not None and not _boxes_overlap(bar_box, burden_panel_box):
                issues.append(
                    _issue(
                        rule_id="sample_burden_out_of_panel",
                        message="sample burden bars must stay inside panel_burden",
                        target=f"metrics.sample_burdens[{index}].bar_box_id",
                        box_refs=(bar_box.box_id, burden_panel_box.box_id),
                    )
                )
        if observed_burden_samples != declared_sample_ids:
            issues.append(
                _issue(
                    rule_id="sample_burden_coverage_mismatch",
                    message="sample_burdens must cover every declared sample exactly once",
                    target="metrics.sample_burdens",
                    observed=sorted(observed_burden_samples),
                    expected=sorted(declared_sample_ids),
                )
            )

    frequency_panel_box = panel_boxes_by_id.get("panel_frequency")
    gene_frequencies = sidecar.metrics.get("gene_alteration_frequencies")
    if not isinstance(gene_frequencies, list) or not gene_frequencies:
        issues.append(
            _issue(
                rule_id="gene_alteration_frequencies_missing",
                message="genomic alteration landscape requires non-empty gene_alteration_frequencies metrics",
                target="metrics.gene_alteration_frequencies",
            )
        )
    else:
        observed_frequency_genes: set[str] = set()
        for index, item in enumerate(gene_frequencies):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.gene_alteration_frequencies[{index}] must be an object")
            gene_label = str(item.get("gene_label") or "").strip()
            if gene_label not in declared_gene_labels:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_gene_unknown",
                        message="gene_alteration_frequencies must stay inside declared gene_labels",
                        target=f"metrics.gene_alteration_frequencies[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            if gene_label in observed_frequency_genes:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_duplicate",
                        message="gene_alteration_frequencies must cover each declared gene exactly once",
                        target=f"metrics.gene_alteration_frequencies[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            observed_frequency_genes.add(gene_label)
            altered_fraction = _require_numeric(
                item.get("altered_fraction"),
                label=f"layout_sidecar.metrics.gene_alteration_frequencies[{index}].altered_fraction",
            )
            if altered_fraction < 0.0 or altered_fraction > 1.0:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_fraction_invalid",
                        message="altered_fraction must stay within [0, 1]",
                        target=f"metrics.gene_alteration_frequencies[{index}].altered_fraction",
                        observed=altered_fraction,
                    )
                )
            bar_box_id = str(item.get("bar_box_id") or "").strip()
            bar_box = layout_boxes_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="gene_frequency_box_missing",
                        message="gene_alteration_frequencies bar_box_id must resolve to an existing layout box",
                        target=f"metrics.gene_alteration_frequencies[{index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
            elif frequency_panel_box is not None and not _boxes_overlap(bar_box, frequency_panel_box):
                issues.append(
                    _issue(
                        rule_id="gene_frequency_out_of_panel",
                        message="gene alteration-frequency bars must stay inside panel_frequency",
                        target=f"metrics.gene_alteration_frequencies[{index}].bar_box_id",
                        box_refs=(bar_box.box_id, frequency_panel_box.box_id),
                    )
                )
        if observed_frequency_genes != declared_gene_labels:
            issues.append(
                _issue(
                    rule_id="gene_frequency_coverage_mismatch",
                    message="gene_alteration_frequencies must cover every declared gene exactly once",
                    target="metrics.gene_alteration_frequencies",
                    observed=sorted(observed_frequency_genes),
                    expected=sorted(declared_gene_labels),
                )
            )

    annotation_panel_box = panel_boxes_by_id.get("panel_annotations")
    annotation_tracks = sidecar.metrics.get("annotation_tracks")
    if not isinstance(annotation_tracks, list) or not annotation_tracks:
        issues.append(
            _issue(
                rule_id="annotation_tracks_missing",
                message="genomic alteration landscape requires non-empty annotation_tracks metrics",
                target="metrics.annotation_tracks",
            )
        )
    else:
        if len(annotation_tracks) > 3:
            issues.append(
                _issue(
                    rule_id="annotation_track_count_invalid",
                    message="genomic alteration landscape supports at most three annotation tracks",
                    target="metrics.annotation_tracks",
                    observed=len(annotation_tracks),
                )
            )
        seen_track_ids: set[str] = set()
        for index, track in enumerate(annotation_tracks):
            if not isinstance(track, dict):
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}] must be an object")
            track_id = str(track.get("track_id") or "").strip()
            if not track_id:
                raise ValueError(f"layout_sidecar.metrics.annotation_tracks[{index}].track_id must be non-empty")
            if track_id in seen_track_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_id_not_unique",
                        message="annotation track ids must be unique",
                        target=f"metrics.annotation_tracks[{index}].track_id",
                        observed=track_id,
                    )
                )
            seen_track_ids.add(track_id)
            if not str(track.get("track_label") or "").strip():
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_invalid",
                        message="annotation track labels must be non-empty",
                        target=f"metrics.annotation_tracks[{index}].track_label",
                    )
                )
            track_label_box_id = str(track.get("track_label_box_id") or "").strip()
            track_label_box = layout_boxes_by_id.get(track_label_box_id)
            if track_label_box is None:
                issues.append(
                    _issue(
                        rule_id="annotation_track_label_box_missing",
                        message="annotation track label box must resolve to an existing layout box",
                        target=f"metrics.annotation_tracks[{index}].track_label_box_id",
                        observed=track_label_box_id,
                    )
                )
            cells = track.get("cells")
            if not isinstance(cells, list) or not cells:
                issues.append(
                    _issue(
                        rule_id="annotation_track_cells_missing",
                        message="annotation track must expose non-empty cells metrics",
                        target=f"metrics.annotation_tracks[{index}].cells",
                    )
                )
                continue
            observed_track_samples: set[str] = set()
            for cell_index, cell in enumerate(cells):
                if not isinstance(cell, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.annotation_tracks[{index}].cells[{cell_index}] must be an object"
                    )
                sample_id = str(cell.get("sample_id") or "").strip()
                if sample_id not in declared_sample_ids:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_unknown",
                            message="annotation track cells must stay inside declared sample_ids",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                if sample_id in observed_track_samples:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_sample_duplicate",
                            message="annotation track cells must cover each sample exactly once",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].sample_id",
                            observed=sample_id,
                        )
                    )
                observed_track_samples.add(sample_id)
                if not str(cell.get("category_label") or "").strip():
                    issues.append(
                        _issue(
                            rule_id="annotation_track_category_invalid",
                            message="annotation track category labels must be non-empty",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].category_label",
                        )
                    )
                box_id = str(cell.get("box_id") or "").strip()
                box = layout_boxes_by_id.get(box_id)
                if box is None:
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_missing",
                            message="annotation track cell box_id must resolve to an existing layout box",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            observed=box_id,
                        )
                    )
                elif annotation_panel_box is not None and not _boxes_overlap(box, annotation_panel_box):
                    issues.append(
                        _issue(
                            rule_id="annotation_track_box_out_of_panel",
                            message="annotation track cells must stay inside panel_annotations",
                            target=f"metrics.annotation_tracks[{index}].cells[{cell_index}].box_id",
                            box_refs=(box.box_id, annotation_panel_box.box_id),
                        )
                    )
            if observed_track_samples != declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="annotation_track_coverage_mismatch",
                        message="each annotation track must cover every declared sample exactly once",
                        target=f"metrics.annotation_tracks[{index}].cells",
                        observed=sorted(observed_track_samples),
                        expected=sorted(declared_sample_ids),
                    )
                )

    matrix_panel_box = panel_boxes_by_id.get("panel_matrix")
    alteration_cells = sidecar.metrics.get("alteration_cells")
    if not isinstance(alteration_cells, list) or not alteration_cells:
        issues.append(
            _issue(
                rule_id="alteration_cells_missing",
                message="genomic alteration landscape requires non-empty alteration_cells metrics",
                target="metrics.alteration_cells",
            )
        )
    else:
        supported_mutation_classes = {"missense", "truncating", "fusion"}
        supported_cnv_states = {"amplification", "gain", "loss", "deep_loss"}
        observed_coordinates: set[tuple[str, str]] = set()
        for index, cell in enumerate(alteration_cells):
            if not isinstance(cell, dict):
                raise ValueError(f"layout_sidecar.metrics.alteration_cells[{index}] must be an object")
            sample_id = str(cell.get("sample_id") or "").strip()
            gene_label = str(cell.get("gene_label") or "").strip()
            if sample_id not in declared_sample_ids:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_sample_unknown",
                        message="alteration_cells sample ids must stay inside declared sample_ids",
                        target=f"metrics.alteration_cells[{index}].sample_id",
                        observed=sample_id,
                    )
                )
            if gene_label not in declared_gene_labels:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_gene_unknown",
                        message="alteration_cells gene labels must stay inside declared gene_labels",
                        target=f"metrics.alteration_cells[{index}].gene_label",
                        observed=gene_label,
                    )
                )
            coordinate = (sample_id, gene_label)
            if coordinate in observed_coordinates:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_coordinate_duplicate",
                        message="alteration_cells must keep sample/gene coordinates unique",
                        target=f"metrics.alteration_cells[{index}]",
                        observed={"sample_id": sample_id, "gene_label": gene_label},
                    )
                )
            observed_coordinates.add(coordinate)

            mutation_class = str(cell.get("mutation_class") or "").strip()
            cnv_state = str(cell.get("cnv_state") or "").strip()
            if not mutation_class and not cnv_state:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_state_missing",
                        message="alteration_cells must define mutation_class or cnv_state",
                        target=f"metrics.alteration_cells[{index}]",
                    )
                )
            if mutation_class and mutation_class not in supported_mutation_classes:
                issues.append(
                    _issue(
                        rule_id="mutation_class_invalid",
                        message="alteration_cells mutation_class must use the supported mutation vocabulary",
                        target=f"metrics.alteration_cells[{index}].mutation_class",
                        observed=mutation_class,
                    )
                )
            if cnv_state and cnv_state not in supported_cnv_states:
                issues.append(
                    _issue(
                        rule_id="cnv_state_invalid",
                        message="alteration_cells cnv_state must use the supported cnv vocabulary",
                        target=f"metrics.alteration_cells[{index}].cnv_state",
                        observed=cnv_state,
                    )
                )
            box_id = str(cell.get("box_id") or "").strip()
            box = layout_boxes_by_id.get(box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id="alteration_cell_box_missing",
                        message="alteration_cells box_id must resolve to an existing layout box",
                        target=f"metrics.alteration_cells[{index}].box_id",
                        observed=box_id,
                    )
                )
            elif matrix_panel_box is not None and not _boxes_overlap(box, matrix_panel_box):
                issues.append(
                    _issue(
                        rule_id="alteration_cell_box_out_of_panel",
                        message="alteration cells must stay inside panel_matrix",
                        target=f"metrics.alteration_cells[{index}].box_id",
                        box_refs=(box.box_id, matrix_panel_box.box_id),
                    )
                )
            overlay_box_id = str(cell.get("overlay_box_id") or "").strip()
            if overlay_box_id:
                overlay_box = layout_boxes_by_id.get(overlay_box_id)
                if overlay_box is None:
                    issues.append(
                        _issue(
                            rule_id="alteration_overlay_box_missing",
                            message="overlay_box_id must resolve to an existing layout box",
                            target=f"metrics.alteration_cells[{index}].overlay_box_id",
                            observed=overlay_box_id,
                        )
                    )
                else:
                    if matrix_panel_box is not None and not _boxes_overlap(overlay_box, matrix_panel_box):
                        issues.append(
                            _issue(
                                rule_id="alteration_overlay_out_of_panel",
                                message="alteration overlays must stay inside panel_matrix",
                                target=f"metrics.alteration_cells[{index}].overlay_box_id",
                                box_refs=(overlay_box.box_id, matrix_panel_box.box_id),
                            )
                        )
                    if box is not None and not _boxes_overlap(overlay_box, box):
                        issues.append(
                            _issue(
                                rule_id="alteration_overlay_detached",
                                message="alteration overlays must stay attached to their parent alteration cell",
                                target=f"metrics.alteration_cells[{index}].overlay_box_id",
                                box_refs=(overlay_box.box_id, box.box_id),
                            )
                        )

    return issues


def _check_publication_genomic_alteration_consequence_panel(
    sidecar: LayoutSidecar,
    *,
    max_panel_count: int = 2,
    required_panel_ids: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    issues = _check_publication_genomic_alteration_landscape_panel(sidecar)
    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_boxes_by_id = {box.box_id: box for box in sidecar.guide_boxes}

    legend_boxes = [box for box in sidecar.guide_boxes if box.box_type == "legend"]
    if len(legend_boxes) < 2:
        issues.append(
            _issue(
                rule_id="legend_count_invalid",
                message="genomic alteration consequence panel requires separate alteration and consequence legends",
                target="guide_boxes",
                observed=len(legend_boxes),
                expected=">= 2",
            )
        )

    consequence_legend_title = str(sidecar.metrics.get("consequence_legend_title") or "").strip()
    if not consequence_legend_title:
        issues.append(
            _issue(
                rule_id="consequence_legend_title_missing",
                message="genomic alteration consequence panel requires a non-empty consequence_legend_title",
                target="metrics.consequence_legend_title",
            )
        )

    effect_threshold = _require_numeric(sidecar.metrics.get("effect_threshold"), label="layout_sidecar.metrics.effect_threshold")
    if effect_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="effect_threshold_invalid",
                message="effect_threshold must be positive",
                target="metrics.effect_threshold",
                observed=effect_threshold,
            )
        )
    significance_threshold = _require_numeric(
        sidecar.metrics.get("significance_threshold"),
        label="layout_sidecar.metrics.significance_threshold",
    )
    if significance_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="significance_threshold_invalid",
                message="significance_threshold must be positive",
                target="metrics.significance_threshold",
                observed=significance_threshold,
            )
        )

    gene_payload = sidecar.metrics.get("gene_labels")
    declared_gene_labels = {
        str(item).strip()
        for item in gene_payload
        if isinstance(gene_payload, list) and str(item).strip()
    }
    driver_gene_payload = sidecar.metrics.get("driver_gene_labels")
    if not isinstance(driver_gene_payload, list) or not driver_gene_payload:
        issues.append(
            _issue(
                rule_id="driver_gene_labels_missing",
                message="genomic alteration consequence panel requires non-empty driver_gene_labels metrics",
                target="metrics.driver_gene_labels",
            )
        )
        return issues
    driver_gene_labels = [str(item).strip() for item in driver_gene_payload]
    if any(not item for item in driver_gene_labels):
        issues.append(
            _issue(
                rule_id="driver_gene_label_invalid",
                message="driver_gene_labels must be non-empty",
                target="metrics.driver_gene_labels",
            )
        )
    if len(set(driver_gene_labels)) != len(driver_gene_labels):
        issues.append(
            _issue(
                rule_id="driver_gene_labels_not_unique",
                message="driver_gene_labels must be unique",
                target="metrics.driver_gene_labels",
            )
        )
    if declared_gene_labels and not set(driver_gene_labels).issubset(declared_gene_labels):
        issues.append(
            _issue(
                rule_id="driver_gene_labels_outside_gene_order",
                message="driver_gene_labels must stay inside gene_labels",
                target="metrics.driver_gene_labels",
                observed=sorted(set(driver_gene_labels) - declared_gene_labels),
            )
        )

    consequence_panels = sidecar.metrics.get("consequence_panels")
    if not isinstance(consequence_panels, list) or not consequence_panels:
        issues.append(
            _issue(
                rule_id="consequence_panels_missing",
                message="genomic alteration consequence panel requires non-empty consequence_panels metrics",
                target="metrics.consequence_panels",
            )
        )
        return issues
    if len(consequence_panels) > max_panel_count:
        issues.append(
            _issue(
                rule_id="consequence_panel_count_invalid",
                message=f"genomic alteration consequence panel supports at most {max_panel_count} consequence panels",
                target="metrics.consequence_panels",
                observed=len(consequence_panels),
            )
        )

    supported_regulation_classes = {"upregulated", "downregulated", "background"}
    seen_panel_ids: set[str] = set()
    expected_coordinates: set[tuple[str, str]] = set()
    observed_coordinates: set[tuple[str, str]] = set()

    for panel_index, payload in enumerate(consequence_panels):
        if not isinstance(payload, dict):
            raise ValueError(f"layout_sidecar.metrics.consequence_panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_text(
            payload.get("panel_id"),
            label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="consequence_panel_id_not_unique",
                    message="consequence panel ids must be unique",
                    target=f"metrics.consequence_panels[{panel_index}].panel_id",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)
        expected_coordinates.update((panel_id, gene_label) for gene_label in driver_gene_labels)

        panel_box_id = _require_non_empty_text(
            payload.get("panel_box_id"),
            label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].panel_box_id",
        )
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="consequence_panel_box_missing",
                    message="panel_box_id must resolve to an existing consequence panel box",
                    target=f"metrics.consequence_panels[{panel_index}].panel_box_id",
                    observed=panel_box_id,
                )
            )

        panel_label_box_id = _require_non_empty_text(
            payload.get("panel_label_box_id"),
            label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].panel_label_box_id",
        )
        panel_label_box = layout_boxes_by_id.get(panel_label_box_id)
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="consequence_panel_label_box_missing",
                    message="panel_label_box_id must resolve to an existing layout box",
                    target=f"metrics.consequence_panels[{panel_index}].panel_label_box_id",
                    observed=panel_label_box_id,
                )
            )
        elif panel_box is not None and not _boxes_overlap(panel_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="consequence_panel_label_anchor_drift",
                    message="consequence panel label must stay anchored inside its panel",
                    target=f"metrics.consequence_panels[{panel_index}].panel_label_box_id",
                    box_refs=(panel_label_box.box_id, panel_box.box_id),
                )
            )

        for field_name in ("panel_title_box_id", "x_axis_title_box_id"):
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].{field_name}",
            )
            if box_id not in layout_boxes_by_id:
                issues.append(
                    _issue(
                        rule_id="consequence_layout_box_missing",
                        message=f"{field_name} must resolve to an existing layout box",
                        target=f"metrics.consequence_panels[{panel_index}].{field_name}",
                        observed=box_id,
                    )
                )

        threshold_pairs = (
            ("effect_threshold_left_box_id", "consequence_threshold_box_missing", "consequence_threshold_outside_panel"),
            ("effect_threshold_right_box_id", "consequence_threshold_box_missing", "consequence_threshold_outside_panel"),
            (
                "significance_threshold_box_id",
                "consequence_significance_box_missing",
                "consequence_significance_outside_panel",
            ),
        )
        for field_name, missing_rule_id, outside_rule_id in threshold_pairs:
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].{field_name}",
            )
            threshold_box = guide_boxes_by_id.get(box_id)
            if threshold_box is None:
                issues.append(
                    _issue(
                        rule_id=missing_rule_id,
                        message=f"{field_name} must resolve to an existing guide box",
                        target=f"metrics.consequence_panels[{panel_index}].{field_name}",
                        observed=box_id,
                    )
                )
                continue
            if panel_box is not None and not _box_within_box(threshold_box, panel_box):
                issues.append(
                    _issue(
                        rule_id=outside_rule_id,
                        message=f"{field_name} must stay within its consequence panel",
                        target=f"guide_boxes.{threshold_box.box_id}",
                        box_refs=(threshold_box.box_id, panel_box.box_id),
                    )
                )

        points_payload = payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            issues.append(
                _issue(
                    rule_id="consequence_points_missing",
                    message="every consequence panel must expose non-empty points metrics",
                    target=f"metrics.consequence_panels[{panel_index}].points",
                )
            )
            continue

        seen_panel_gene_labels: set[str] = set()
        for point_index, point in enumerate(points_payload):
            if not isinstance(point, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}] must be an object"
                )
            gene_label = _require_non_empty_text(
                point.get("gene_label"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].gene_label",
            )
            if gene_label in seen_panel_gene_labels:
                issues.append(
                    _issue(
                        rule_id="consequence_point_gene_label_duplicate",
                        message="gene_label must be unique within each consequence panel",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].gene_label",
                        observed=gene_label,
                    )
                )
            seen_panel_gene_labels.add(gene_label)
            observed_coordinates.add((panel_id, gene_label))
            if gene_label not in set(driver_gene_labels):
                issues.append(
                    _issue(
                        rule_id="consequence_point_gene_unknown",
                        message="consequence points must stay inside declared driver_gene_labels",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].gene_label",
                        observed=gene_label,
                    )
                )
            point_x = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].x",
            )
            point_y = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].y",
            )
            _require_numeric(
                point.get("effect_value"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].effect_value",
            )
            significance_value = _require_numeric(
                point.get("significance_value"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].significance_value",
            )
            if significance_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="consequence_significance_value_negative",
                        message="consequence significance_value must be non-negative",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].significance_value",
                        observed=significance_value,
                    )
                )
            regulation_class = _require_non_empty_text(
                point.get("regulation_class"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].regulation_class",
            )
            if regulation_class not in supported_regulation_classes:
                issues.append(
                    _issue(
                        rule_id="consequence_regulation_class_invalid",
                        message="consequence regulation_class must use the supported vocabulary",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].regulation_class",
                        observed=regulation_class,
                        expected=sorted(supported_regulation_classes),
                    )
                )
            if panel_box is not None and not _point_within_box(panel_box, x=point_x, y=point_y):
                issues.append(
                    _issue(
                        rule_id="consequence_point_outside_panel",
                        message="consequence point coordinates must stay within the panel bounds",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )

            point_box_id = _require_non_empty_text(
                point.get("point_box_id"),
                label=f"layout_sidecar.metrics.consequence_panels[{panel_index}].points[{point_index}].point_box_id",
            )
            point_box = layout_boxes_by_id.get(point_box_id)
            if point_box is None:
                issues.append(
                    _issue(
                        rule_id="consequence_point_box_missing",
                        message="point_box_id must resolve to an existing layout box",
                        target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].point_box_id",
                        observed=point_box_id,
                    )
                )
            elif panel_box is not None and not _box_within_box(point_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="consequence_point_box_outside_panel",
                        message="consequence point boxes must stay within the panel bounds",
                        target=f"layout_boxes.{point_box.box_id}",
                        box_refs=(point_box.box_id, panel_box.box_id),
                    )
                )

            label_box_id = str(point.get("label_box_id") or "").strip()
            if label_box_id:
                label_box = layout_boxes_by_id.get(label_box_id)
                if label_box is None:
                    issues.append(
                        _issue(
                            rule_id="consequence_label_box_missing",
                            message="label_box_id must resolve to an existing layout box",
                            target=f"metrics.consequence_panels[{panel_index}].points[{point_index}].label_box_id",
                            observed=label_box_id,
                        )
                    )
                elif panel_box is not None and not _box_within_box(label_box, panel_box):
                    issues.append(
                        _issue(
                            rule_id="consequence_label_box_outside_panel",
                            message="consequence label boxes must stay within the panel bounds",
                            target=f"layout_boxes.{label_box.box_id}",
                            box_refs=(label_box.box_id, panel_box.box_id),
                        )
                    )

    if observed_coordinates != expected_coordinates:
        issues.append(
            _issue(
                rule_id="consequence_point_coverage_mismatch",
                message="consequence points must cover every declared panel/driver gene coordinate exactly once",
                target="metrics.consequence_panels",
                observed=sorted(observed_coordinates),
                expected=sorted(expected_coordinates),
            )
        )

    if required_panel_ids is not None and seen_panel_ids != set(required_panel_ids):
        issues.append(
            _issue(
                rule_id="consequence_panel_ids_invalid",
                message="consequence panel ids must match the declared multiomic layer vocabulary",
                target="metrics.consequence_panels",
                observed=sorted(seen_panel_ids),
                expected=sorted(required_panel_ids),
            )
        )

    return issues


def _check_publication_genomic_alteration_multiomic_consequence_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_publication_genomic_alteration_consequence_panel(
        sidecar,
        max_panel_count=3,
        required_panel_ids=("proteome", "phosphoproteome", "glycoproteome"),
    )
    consequence_panels = sidecar.metrics.get("consequence_panels")
    if isinstance(consequence_panels, list) and len(consequence_panels) != 3:
        issues.append(
            _issue(
                rule_id="consequence_panel_count_invalid",
                message="genomic alteration multiomic consequence panel requires exactly three consequence panels",
                target="metrics.consequence_panels",
                observed=len(consequence_panels),
                expected=3,
            )
        )
    return issues


def _check_publication_genomic_alteration_pathway_integrated_composite_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues = _check_publication_genomic_alteration_multiomic_consequence_panel(sidecar)
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("colorbar",)))

    pathway_effect_scale_label = str(sidecar.metrics.get("pathway_effect_scale_label") or "").strip()
    if not pathway_effect_scale_label:
        issues.append(
            _issue(
                rule_id="pathway_effect_scale_label_missing",
                message="pathway-integrated composite requires a non-empty pathway_effect_scale_label",
                target="metrics.pathway_effect_scale_label",
            )
        )
    pathway_size_scale_label = str(sidecar.metrics.get("pathway_size_scale_label") or "").strip()
    if not pathway_size_scale_label:
        issues.append(
            _issue(
                rule_id="pathway_size_scale_label_missing",
                message="pathway-integrated composite requires a non-empty pathway_size_scale_label",
                target="metrics.pathway_size_scale_label",
            )
        )

    pathway_label_payload = sidecar.metrics.get("pathway_labels")
    if not isinstance(pathway_label_payload, list) or not pathway_label_payload:
        issues.append(
            _issue(
                rule_id="pathway_labels_missing",
                message="pathway-integrated composite requires non-empty pathway_labels metrics",
                target="metrics.pathway_labels",
            )
        )
        return issues
    pathway_labels = [str(item).strip() for item in pathway_label_payload]
    if any(not item for item in pathway_labels):
        issues.append(
            _issue(
                rule_id="pathway_label_invalid",
                message="pathway_labels must be non-empty",
                target="metrics.pathway_labels",
            )
        )
    if len(set(pathway_labels)) != len(pathway_labels):
        issues.append(
            _issue(
                rule_id="pathway_labels_not_unique",
                message="pathway_labels must be unique",
                target="metrics.pathway_labels",
            )
        )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_boxes_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    required_panel_ids = ("proteome", "phosphoproteome", "glycoproteome")
    pathway_panels = sidecar.metrics.get("pathway_panels")
    if not isinstance(pathway_panels, list) or not pathway_panels:
        issues.append(
            _issue(
                rule_id="pathway_panels_missing",
                message="pathway-integrated composite requires non-empty pathway_panels metrics",
                target="metrics.pathway_panels",
            )
        )
        return issues
    if len(pathway_panels) != 3:
        issues.append(
            _issue(
                rule_id="pathway_panel_count_invalid",
                message="pathway-integrated composite requires exactly three pathway panels",
                target="metrics.pathway_panels",
                observed=len(pathway_panels),
                expected=3,
            )
        )

    expected_coordinates = {(panel_id, pathway_label) for panel_id in required_panel_ids for pathway_label in pathway_labels}
    observed_coordinates: set[tuple[str, str]] = set()
    observed_panel_ids: set[str] = set()

    for panel_index, payload in enumerate(pathway_panels):
        if not isinstance(payload, dict):
            raise ValueError(f"layout_sidecar.metrics.pathway_panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_text(
            payload.get("panel_id"),
            label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].panel_id",
        )
        observed_panel_ids.add(panel_id)

        panel_box_id = _require_non_empty_text(
            payload.get("panel_box_id"),
            label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].panel_box_id",
        )
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="pathway_panel_box_missing",
                    message="panel_box_id must resolve to an existing pathway panel box",
                    target=f"metrics.pathway_panels[{panel_index}].panel_box_id",
                    observed=panel_box_id,
                )
            )

        panel_label_box_id = _require_non_empty_text(
            payload.get("panel_label_box_id"),
            label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].panel_label_box_id",
        )
        panel_label_box = layout_boxes_by_id.get(panel_label_box_id)
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="pathway_panel_label_box_missing",
                    message="panel_label_box_id must resolve to an existing layout box",
                    target=f"metrics.pathway_panels[{panel_index}].panel_label_box_id",
                    observed=panel_label_box_id,
                )
            )
        elif panel_box is not None and not _boxes_overlap(panel_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="pathway_panel_label_anchor_drift",
                    message="pathway panel label must stay anchored inside its panel",
                    target=f"metrics.pathway_panels[{panel_index}].panel_label_box_id",
                    box_refs=(panel_label_box.box_id, panel_box.box_id),
                )
            )

        for field_name in ("panel_title_box_id", "x_axis_title_box_id"):
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].{field_name}",
            )
            if box_id not in layout_boxes_by_id:
                issues.append(
                    _issue(
                        rule_id="pathway_layout_box_missing",
                        message=f"{field_name} must resolve to an existing layout box",
                        target=f"metrics.pathway_panels[{panel_index}].{field_name}",
                        observed=box_id,
                    )
                )

        points_payload = payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            issues.append(
                _issue(
                    rule_id="pathway_points_missing",
                    message="every pathway panel must expose non-empty points metrics",
                    target=f"metrics.pathway_panels[{panel_index}].points",
                )
            )
            continue

        seen_pathway_labels: set[str] = set()
        for point_index, point in enumerate(points_payload):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}] must be an object")
            pathway_label = _require_non_empty_text(
                point.get("pathway_label"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].pathway_label",
            )
            if pathway_label in seen_pathway_labels:
                issues.append(
                    _issue(
                        rule_id="pathway_point_label_duplicate",
                        message="pathway_label must be unique within each pathway panel",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}].pathway_label",
                        observed=pathway_label,
                    )
                )
            seen_pathway_labels.add(pathway_label)
            observed_coordinates.add((panel_id, pathway_label))
            if pathway_label not in set(pathway_labels):
                issues.append(
                    _issue(
                        rule_id="pathway_point_label_unknown",
                        message="pathway points must stay inside declared pathway_labels",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}].pathway_label",
                        observed=pathway_label,
                    )
                )

            point_x = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].x",
            )
            point_y = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].y",
            )
            _require_numeric(
                point.get("x_value"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].x_value",
            )
            _require_numeric(
                point.get("effect_value"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].effect_value",
            )
            size_value = _require_numeric(
                point.get("size_value"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].size_value",
            )
            if size_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="pathway_size_value_negative",
                        message="pathway size_value must be non-negative",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}].size_value",
                        observed=size_value,
                    )
                )
            if panel_box is not None and not _point_within_box(panel_box, x=point_x, y=point_y):
                issues.append(
                    _issue(
                        rule_id="pathway_point_outside_panel",
                        message="pathway point coordinates must stay within the panel bounds",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )

            point_box_id = _require_non_empty_text(
                point.get("point_box_id"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].point_box_id",
            )
            point_box = layout_boxes_by_id.get(point_box_id)
            if point_box is None:
                issues.append(
                    _issue(
                        rule_id="pathway_point_box_missing",
                        message="point_box_id must resolve to an existing layout box",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}].point_box_id",
                        observed=point_box_id,
                    )
                )
            elif panel_box is not None and not _box_within_box(point_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="pathway_point_box_outside_panel",
                        message="pathway point boxes must stay within the panel bounds",
                        target=f"layout_boxes.{point_box.box_id}",
                        box_refs=(point_box.box_id, panel_box.box_id),
                    )
                )

    if observed_panel_ids != set(required_panel_ids):
        issues.append(
            _issue(
                rule_id="pathway_panel_ids_invalid",
                message="pathway panel ids must match the declared multiomic layer vocabulary",
                target="metrics.pathway_panels",
                observed=sorted(observed_panel_ids),
                expected=sorted(required_panel_ids),
            )
        )
    if observed_coordinates != expected_coordinates:
        issues.append(
            _issue(
                rule_id="pathway_point_coverage_mismatch",
                message="pathway points must cover every declared panel/pathway coordinate exactly once",
                target="metrics.pathway_panels",
                observed=sorted(observed_coordinates),
                expected=sorted(expected_coordinates),
            )
        )

    return issues


def _check_publication_omics_volcano_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "subplot_y_axis_title")))
    issues.extend(_check_legend_panel_overlap(sidecar))

    legend_title = str(sidecar.metrics.get("legend_title") or "").strip()
    if not legend_title:
        issues.append(
            _issue(
                rule_id="legend_title_missing",
                message="omics volcano panel requires a non-empty legend_title",
                target="metrics.legend_title",
            )
        )

    effect_threshold = _require_numeric(sidecar.metrics.get("effect_threshold"), label="layout_sidecar.metrics.effect_threshold")
    if effect_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="effect_threshold_invalid",
                message="effect_threshold must be positive",
                target="metrics.effect_threshold",
                observed=effect_threshold,
            )
        )
    significance_threshold = _require_numeric(
        sidecar.metrics.get("significance_threshold"),
        label="layout_sidecar.metrics.significance_threshold",
    )
    if significance_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="significance_threshold_invalid",
                message="significance_threshold must be positive",
                target="metrics.significance_threshold",
                observed=significance_threshold,
            )
        )

    panels_payload = sidecar.metrics.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="omics volcano panel requires non-empty panels metrics",
                target="metrics.panels",
            )
        )
        return issues
    if len(panels_payload) > 2:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="omics volcano panel supports at most two panels",
                target="metrics.panels",
                observed=len(panels_payload),
            )
        )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_boxes_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    supported_regulation_classes = {"upregulated", "downregulated", "background"}
    seen_panel_ids: set[str] = set()

    for panel_index, payload in enumerate(panels_payload):
        if not isinstance(payload, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_text(
            payload.get("panel_id"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="panel_id_not_unique",
                    message="panel_id must be unique across panels",
                    target=f"metrics.panels[{panel_index}].panel_id",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)

        panel_box_id = _require_non_empty_text(
            payload.get("panel_box_id"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].panel_box_id",
        )
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="panel_box_id must resolve to an existing panel box",
                    target=f"metrics.panels[{panel_index}].panel_box_id",
                    observed=panel_box_id,
                )
            )

        panel_label_box_id = _require_non_empty_text(
            payload.get("panel_label_box_id"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].panel_label_box_id",
        )
        panel_label_box = layout_boxes_by_id.get(panel_label_box_id)
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_box_missing",
                    message="panel_label_box_id must resolve to an existing layout box",
                    target=f"metrics.panels[{panel_index}].panel_label_box_id",
                    observed=panel_label_box_id,
                )
            )
        elif panel_box is not None and not _boxes_overlap(panel_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_anchor_drift",
                    message="panel label must stay anchored inside its panel",
                    target=f"metrics.panels[{panel_index}].panel_label_box_id",
                    box_refs=(panel_label_box.box_id, panel_box.box_id),
                )
            )

        for field_name in ("panel_title_box_id", "x_axis_title_box_id"):
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.panels[{panel_index}].{field_name}",
            )
            if box_id in layout_boxes_by_id:
                continue
            issues.append(
                _issue(
                    rule_id="layout_box_missing",
                    message=f"{field_name} must resolve to an existing layout box",
                    target=f"metrics.panels[{panel_index}].{field_name}",
                    observed=box_id,
                )
            )

        threshold_pairs = (
            ("effect_threshold_left_box_id", "effect_threshold_box_missing", "effect_threshold_outside_panel"),
            ("effect_threshold_right_box_id", "effect_threshold_box_missing", "effect_threshold_outside_panel"),
            ("significance_threshold_box_id", "significance_threshold_box_missing", "significance_threshold_outside_panel"),
        )
        for field_name, missing_rule_id, outside_rule_id in threshold_pairs:
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.panels[{panel_index}].{field_name}",
            )
            threshold_box = guide_boxes_by_id.get(box_id)
            if threshold_box is None:
                issues.append(
                    _issue(
                        rule_id=missing_rule_id,
                        message=f"{field_name} must resolve to an existing guide box",
                        target=f"metrics.panels[{panel_index}].{field_name}",
                        observed=box_id,
                    )
                )
                continue
            if panel_box is not None and not _box_within_box(threshold_box, panel_box):
                issues.append(
                    _issue(
                        rule_id=outside_rule_id,
                        message=f"{field_name} must stay within its panel bounds",
                        target=f"guide_boxes.{threshold_box.box_id}",
                        box_refs=(threshold_box.box_id, panel_box.box_id),
                    )
                )

        points_payload = payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            issues.append(
                _issue(
                    rule_id="panel_points_missing",
                    message="every panel must expose non-empty points metrics",
                    target=f"metrics.panels[{panel_index}].points",
                )
            )
            continue

        seen_feature_labels: set[str] = set()
        for point_index, point in enumerate(points_payload):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}] must be an object")
            feature_label = _require_non_empty_text(
                point.get("feature_label"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].feature_label",
            )
            if feature_label in seen_feature_labels:
                issues.append(
                    _issue(
                        rule_id="point_feature_label_not_unique",
                        message="feature_label must be unique within each panel",
                        target=f"metrics.panels[{panel_index}].points[{point_index}].feature_label",
                        observed=feature_label,
                    )
                )
            seen_feature_labels.add(feature_label)
            point_x = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].x",
            )
            point_y = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].y",
            )
            _require_numeric(
                point.get("effect_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].effect_value",
            )
            significance_value = _require_numeric(
                point.get("significance_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].significance_value",
            )
            if significance_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="significance_value_negative",
                        message="significance_value must be non-negative",
                        target=f"metrics.panels[{panel_index}].points[{point_index}].significance_value",
                        observed=significance_value,
                    )
                )
            regulation_class = _require_non_empty_text(
                point.get("regulation_class"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].regulation_class",
            )
            if regulation_class not in supported_regulation_classes:
                issues.append(
                    _issue(
                        rule_id="regulation_class_invalid",
                        message="regulation_class must use the supported vocabulary",
                        target=f"metrics.panels[{panel_index}].points[{point_index}].regulation_class",
                        observed=regulation_class,
                        expected=sorted(supported_regulation_classes),
                    )
                )
            if panel_box is not None and not _point_within_box(panel_box, x=point_x, y=point_y):
                issues.append(
                    _issue(
                        rule_id="point_outside_panel",
                        message="point coordinates must stay within the panel bounds",
                        target=f"metrics.panels[{panel_index}].points[{point_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
            label_text = str(point.get("label_text") or "").strip()
            label_box_id = str(point.get("label_box_id") or "").strip()
            if label_text and not label_box_id:
                issues.append(
                    _issue(
                        rule_id="label_box_missing",
                        message="labeled volcano points must reference label_box_id",
                        target=f"metrics.panels[{panel_index}].points[{point_index}].label_box_id",
                    )
                )
                continue
            if label_box_id:
                label_box = layout_boxes_by_id.get(label_box_id)
                if label_box is None:
                    issues.append(
                        _issue(
                            rule_id="label_box_missing",
                            message="label_box_id must resolve to an existing layout box",
                            target=f"metrics.panels[{panel_index}].points[{point_index}].label_box_id",
                            observed=label_box_id,
                        )
                    )
                elif panel_box is not None and not _box_within_box(label_box, panel_box):
                    issues.append(
                        _issue(
                            rule_id="label_box_outside_panel",
                            message="label box must stay within the panel bounds",
                            target=f"layout_boxes.{label_box.box_id}",
                            box_refs=(label_box.box_id, panel_box.box_id),
                        )
                    )

    return issues


def _check_publication_forest_plot(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("reference_line", "row_label", "estimate_marker", "ci_segment")))
    panel = _primary_panel(sidecar)
    if panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="forest plot requires a panel box",
                target="panel",
                expected="present",
            )
        )
        return issues

    for row_label in _boxes_of_type(sidecar.layout_boxes, "row_label"):
        if not _boxes_overlap(row_label, panel):
            continue
        issues.append(
            _issue(
                rule_id="row_label_panel_overlap",
                message="row label must not overlap the forest panel",
                target="row_label",
                box_refs=(row_label.box_id, panel.box_id),
            )
        )

    rows = sidecar.metrics.get("rows")
    if not isinstance(rows, list) or not rows:
        issues.append(
            _issue(
                rule_id="rows_missing",
                message="forest qc requires non-empty row metrics",
                target="metrics.rows",
            )
        )
        return issues
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.rows[{index}] must be an object")
        lower = _require_numeric(row.get("lower"), label=f"layout_sidecar.metrics.rows[{index}].lower")
        estimate = _require_numeric(row.get("estimate"), label=f"layout_sidecar.metrics.rows[{index}].estimate")
        upper = _require_numeric(row.get("upper"), label=f"layout_sidecar.metrics.rows[{index}].upper")
        if lower <= estimate <= upper:
            continue
        issues.append(
            _issue(
                rule_id="estimate_outside_interval",
                message="estimate must lie within the confidence interval",
                target=f"metrics.rows[{index}]",
                observed={"lower": lower, "estimate": estimate, "upper": upper},
            )
        )
    return issues


def _check_publication_compact_effect_estimate_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "panel_label",
        "subplot_x_axis_title",
        "row_label",
        "estimate_marker",
        "ci_segment",
        "reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}

    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    if metrics.get("reference_value") is None:
        issues.append(
            _issue(
                rule_id="reference_value_missing",
                message="compact effect estimate qc requires a numeric reference_value",
                target="metrics.reference_value",
            )
        )
    else:
        _require_numeric(metrics.get("reference_value"), label="layout_sidecar.metrics.reference_value")

    panels = metrics.get("panels")
    if not isinstance(panels, list) or not panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="compact effect estimate qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues
    if len(panels) < 2 or len(panels) > 4:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="compact effect estimate qc requires between 2 and 4 panels",
                target="metrics.panels",
                observed={"count": len(panels)},
                expected={"minimum": 2, "maximum": 4},
            )
        )

    expected_row_order: tuple[tuple[str, str], ...] | None = None
    label_panel_map: dict[str, str] = {}
    for panel_index, panel_metric in enumerate(panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")

        panel_label = _require_non_empty_text(
            panel_metric.get("panel_label"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].panel_label",
        )
        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_missing",
                    message="compact effect estimate qc requires each metric panel to reference an existing panel box",
                    target=f"metrics.panels[{panel_index}].panel_box_id",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue

        panel_label_box_id = str(panel_metric.get("panel_label_box_id") or "").strip() or f"panel_label_{panel_label}"
        panel_title_box_id = str(panel_metric.get("panel_title_box_id") or "").strip() or f"panel_title_{panel_label}"
        x_axis_title_box_id = str(panel_metric.get("x_axis_title_box_id") or "").strip() or f"x_axis_title_{panel_label}"
        label_panel_map[panel_label_box_id] = panel_box.box_id
        if layout_box_by_id.get(panel_title_box_id) is None or layout_box_by_id.get(x_axis_title_box_id) is None:
            issues.append(
                _issue(
                    rule_id="panel_text_box_missing",
                    message="compact effect estimate panels must reference title and x-axis title boxes",
                    target=f"metrics.panels[{panel_index}]",
                    box_refs=(panel_box.box_id,),
                )
            )

        reference_line_box_id = str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="compact effect estimate panels require one reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="compact effect estimate reference lines must stay within the declared panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    box_refs=(reference_line_box.box_id, panel_box.box_id),
                )
            )

        rows = panel_metric.get("rows")
        if not isinstance(rows, list) or not rows:
            issues.append(
                _issue(
                    rule_id="panel_rows_missing",
                    message="compact effect estimate panels must contain non-empty rows",
                    target=f"metrics.panels[{panel_index}].rows",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        row_order: list[tuple[str, str]] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}] must be an object")
            row_id = _require_non_empty_text(
                row.get("row_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].row_id",
            )
            row_label = _require_non_empty_text(
                row.get("row_label"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].row_label",
            )
            row_order.append((row_id, row_label))

            lower = _require_numeric(
                row.get("lower"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].lower",
            )
            estimate = _require_numeric(
                row.get("estimate"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].estimate",
            )
            upper = _require_numeric(
                row.get("upper"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].rows[{row_index}].upper",
            )
            if not (lower <= estimate <= upper):
                issues.append(
                    _issue(
                        rule_id="estimate_outside_interval",
                        message="panel estimate must lie within the confidence interval",
                        target=f"metrics.panels[{panel_index}].rows[{row_index}]",
                        observed={"lower": lower, "estimate": estimate, "upper": upper},
                    )
                )

            label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
            estimate_box = layout_box_by_id.get(str(row.get("estimate_box_id") or "").strip())
            ci_box = layout_box_by_id.get(str(row.get("ci_box_id") or "").strip())
            if label_box is None or estimate_box is None or ci_box is None:
                issues.append(
                    _issue(
                        rule_id="row_box_missing",
                        message="compact effect estimate rows must reference label, estimate, and ci boxes",
                        target=f"metrics.panels[{panel_index}].rows[{row_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
                continue
            if _boxes_overlap(label_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="row_label_panel_overlap",
                        message="compact effect estimate row labels must stay outside the panel",
                        target=f"layout_boxes.{label_box.box_id}",
                        box_refs=(label_box.box_id, panel_box.box_id),
                    )
                )
            if not _box_within_box(estimate_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="estimate_marker_outside_panel",
                        message="compact effect estimate markers must stay within the panel",
                        target=f"layout_boxes.{estimate_box.box_id}",
                        box_refs=(estimate_box.box_id, panel_box.box_id),
                    )
                )
            if not _box_within_box(ci_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="ci_segment_outside_panel",
                        message="compact effect estimate confidence intervals must stay within the panel",
                        target=f"layout_boxes.{ci_box.box_id}",
                        box_refs=(ci_box.box_id, panel_box.box_id),
                    )
                )

        if expected_row_order is None:
            expected_row_order = tuple(row_order)
        elif tuple(row_order) != expected_row_order:
            issues.append(
                _issue(
                    rule_id="panel_row_order_mismatch",
                    message="compact effect estimate rows must keep the same row order across panels",
                    target=f"metrics.panels[{panel_index}].rows",
                    observed={"row_order": row_order},
                    expected={"row_order": list(expected_row_order)},
                    box_refs=(panel_box.box_id,),
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )
    return issues


def _check_publication_coefficient_path_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "panel_label",
        "subplot_x_axis_title",
        "legend_title",
        "legend_label",
        "coefficient_row_label",
        "coefficient_marker",
        "coefficient_interval",
        "summary_card_label",
        "summary_card_value",
        "reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    path_panel = panel_boxes_by_id.get("path_panel")
    summary_panel = panel_boxes_by_id.get("summary_panel")
    if path_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="coefficient path qc requires path_panel and summary_panel",
                target="panel_boxes",
            )
        )
        return issues

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}

    if metrics.get("reference_value") is None:
        issues.append(
            _issue(
                rule_id="reference_value_missing",
                message="coefficient path qc requires a numeric reference_value",
                target="metrics.reference_value",
            )
        )
    else:
        _require_numeric(metrics.get("reference_value"), label="layout_sidecar.metrics.reference_value")

    path_panel_metrics = metrics.get("path_panel")
    if not isinstance(path_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="path_panel_metrics_missing",
                message="coefficient path qc requires path_panel metrics",
                target="metrics.path_panel",
            )
        )
        return issues
    summary_panel_metrics = metrics.get("summary_panel")
    if not isinstance(summary_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="summary_panel_metrics_missing",
                message="coefficient path qc requires summary_panel metrics",
                target="metrics.summary_panel",
            )
        )
        return issues

    reference_line_box = guide_box_by_id.get(str(path_panel_metrics.get("reference_line_box_id") or "").strip())
    if reference_line_box is None:
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="coefficient path qc requires one reference line inside the path panel",
                target="metrics.path_panel.reference_line_box_id",
                box_refs=(path_panel.box_id,),
            )
        )
    elif not _box_within_box(reference_line_box, path_panel):
        issues.append(
            _issue(
                rule_id="reference_line_outside_path_panel",
                message="coefficient path reference line must stay within the path panel",
                target=f"guide_boxes.{reference_line_box.box_id}",
                box_refs=(reference_line_box.box_id, path_panel.box_id),
            )
        )

    legend_title_box = layout_box_by_id.get(str(metrics.get("step_legend_title_box_id") or "").strip())
    if legend_title_box is None:
        issues.append(
            _issue(
                rule_id="step_legend_title_missing",
                message="coefficient path qc requires one step legend title box",
                target="metrics.step_legend_title_box_id",
            )
        )

    steps = metrics.get("steps")
    if not isinstance(steps, list) or not steps:
        issues.append(
            _issue(
                rule_id="steps_missing",
                message="coefficient path qc requires non-empty step metrics",
                target="metrics.steps",
            )
        )
        return issues
    if len(steps) < 2 or len(steps) > 5:
        issues.append(
            _issue(
                rule_id="step_count_invalid",
                message="coefficient path qc requires between 2 and 5 steps",
                target="metrics.steps",
                observed={"count": len(steps)},
                expected={"minimum": 2, "maximum": 5},
            )
        )

    expected_step_ids: list[str] = []
    seen_step_ids: set[str] = set()
    previous_step_order: int | None = None
    for step_index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"layout_sidecar.metrics.steps[{step_index}] must be an object")
        step_id = _require_non_empty_text(step.get("step_id"), label=f"layout_sidecar.metrics.steps[{step_index}].step_id")
        if step_id in seen_step_ids:
            issues.append(
                _issue(
                    rule_id="step_id_duplicate",
                    message="coefficient path step_id values must be unique",
                    target=f"metrics.steps[{step_index}].step_id",
                )
            )
        seen_step_ids.add(step_id)
        step_order = int(_require_numeric(step.get("step_order"), label=f"layout_sidecar.metrics.steps[{step_index}].step_order"))
        if previous_step_order is not None and step_order <= previous_step_order:
            issues.append(
                _issue(
                    rule_id="step_order_invalid",
                    message="coefficient path steps must have strictly increasing step_order",
                    target=f"metrics.steps[{step_index}].step_order",
                )
            )
        previous_step_order = step_order
        legend_label_box = layout_box_by_id.get(str(step.get("legend_label_box_id") or "").strip())
        if legend_label_box is None:
            issues.append(
                _issue(
                    rule_id="step_legend_label_missing",
                    message="every coefficient path step must reference a legend label box",
                    target=f"metrics.steps[{step_index}].legend_label_box_id",
                )
            )
        expected_step_ids.append(step_id)

    coefficient_rows = metrics.get("coefficient_rows")
    if not isinstance(coefficient_rows, list) or not coefficient_rows:
        issues.append(
            _issue(
                rule_id="coefficient_rows_missing",
                message="coefficient path qc requires non-empty coefficient_rows metrics",
                target="metrics.coefficient_rows",
            )
        )
        return issues

    declared_step_id_set = set(expected_step_ids)
    for row_index, row in enumerate(coefficient_rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.coefficient_rows[{row_index}] must be an object")
        label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="coefficient_row_label_missing",
                    message="coefficient path rows must reference a label box",
                    target=f"metrics.coefficient_rows[{row_index}].label_box_id",
                    box_refs=(path_panel.box_id,),
                )
            )
        elif _boxes_overlap(label_box, path_panel):
            issues.append(
                _issue(
                    rule_id="coefficient_row_label_panel_overlap",
                    message="coefficient row label must stay outside the path panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, path_panel.box_id),
                )
            )

        points = row.get("points")
        if not isinstance(points, list) or not points:
            issues.append(
                _issue(
                    rule_id="coefficient_points_missing",
                    message="every coefficient row must provide non-empty points",
                    target=f"metrics.coefficient_rows[{row_index}].points",
                )
            )
            continue

        seen_row_step_ids: set[str] = set()
        for point_index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.coefficient_rows[{row_index}].points[{point_index}] must be an object"
                )
            step_id = _require_non_empty_text(
                point.get("step_id"),
                label=f"layout_sidecar.metrics.coefficient_rows[{row_index}].points[{point_index}].step_id",
            )
            seen_row_step_ids.add(step_id)
            marker_box = layout_box_by_id.get(str(point.get("marker_box_id") or "").strip())
            interval_box = layout_box_by_id.get(str(point.get("interval_box_id") or "").strip())
            if marker_box is None or interval_box is None:
                issues.append(
                    _issue(
                        rule_id="coefficient_point_box_missing",
                        message="coefficient path points must reference marker and interval boxes",
                        target=f"metrics.coefficient_rows[{row_index}].points[{point_index}]",
                        box_refs=(path_panel.box_id,),
                    )
                )
                continue
            if not _box_within_box(marker_box, path_panel):
                issues.append(
                    _issue(
                        rule_id="coefficient_marker_outside_path_panel",
                        message="coefficient marker must stay within the path panel",
                        target=f"layout_boxes.{marker_box.box_id}",
                        box_refs=(marker_box.box_id, path_panel.box_id),
                    )
                )
            if not _box_within_box(interval_box, path_panel):
                issues.append(
                    _issue(
                        rule_id="coefficient_interval_outside_path_panel",
                        message="coefficient interval must stay within the path panel",
                        target=f"layout_boxes.{interval_box.box_id}",
                        box_refs=(interval_box.box_id, path_panel.box_id),
                    )
                )
        if seen_row_step_ids != declared_step_id_set:
            issues.append(
                _issue(
                    rule_id="coefficient_step_coverage_mismatch",
                    message="coefficient path rows must cover every declared step exactly once",
                    target=f"metrics.coefficient_rows[{row_index}].points",
                    observed={"step_ids": sorted(seen_row_step_ids)},
                    expected={"step_ids": sorted(declared_step_id_set)},
                )
            )

    summary_cards = metrics.get("summary_cards")
    if not isinstance(summary_cards, list) or not summary_cards:
        issues.append(
            _issue(
                rule_id="summary_cards_missing",
                message="coefficient path qc requires non-empty summary_cards metrics",
                target="metrics.summary_cards",
            )
        )
        return issues

    for card_index, card in enumerate(summary_cards):
        if not isinstance(card, dict):
            raise ValueError(f"layout_sidecar.metrics.summary_cards[{card_index}] must be an object")
        label_box = layout_box_by_id.get(str(card.get("label_box_id") or "").strip())
        value_box = layout_box_by_id.get(str(card.get("value_box_id") or "").strip())
        detail_box_id = str(card.get("detail_box_id") or "").strip()
        detail_box = layout_box_by_id.get(detail_box_id) if detail_box_id else None
        if label_box is None or value_box is None:
            issues.append(
                _issue(
                    rule_id="summary_card_box_missing",
                    message="coefficient path summary cards must reference label and value boxes",
                    target=f"metrics.summary_cards[{card_index}]",
                    box_refs=(summary_panel.box_id,),
                )
            )
            continue
        if not _box_within_box(label_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="summary_card_label_outside_panel",
                    message="summary card label must stay within the summary panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, summary_panel.box_id),
                )
            )
        if not _box_within_box(value_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="summary_card_value_outside_panel",
                    message="summary card value must stay within the summary panel",
                    target=f"layout_boxes.{value_box.box_id}",
                    box_refs=(value_box.box_id, summary_panel.box_id),
                )
            )
        if detail_box is not None and not _box_within_box(detail_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="summary_card_detail_outside_panel",
                    message="summary card detail must stay within the summary panel",
                    target=f"layout_boxes.{detail_box.box_id}",
                    box_refs=(detail_box.box_id, summary_panel.box_id),
                )
            )

    return issues


def _check_publication_broader_heterogeneity_summary_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "panel_label",
        "subplot_x_axis_title",
        "legend_title",
        "legend_label",
        "row_label",
        "estimate_marker",
        "ci_segment",
        "verdict_value",
        "reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    matrix_panel = panel_boxes_by_id.get("matrix_panel")
    summary_panel = panel_boxes_by_id.get("summary_panel")
    if matrix_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="broader heterogeneity summary qc requires matrix_panel and summary_panel",
                target="panel_boxes",
            )
        )
        return issues

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}

    if metrics.get("reference_value") is None:
        issues.append(
            _issue(
                rule_id="reference_value_missing",
                message="broader heterogeneity summary qc requires a numeric reference_value",
                target="metrics.reference_value",
            )
        )
    else:
        _require_numeric(metrics.get("reference_value"), label="layout_sidecar.metrics.reference_value")

    matrix_panel_metrics = metrics.get("matrix_panel")
    if not isinstance(matrix_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="matrix_panel_metrics_missing",
                message="broader heterogeneity summary qc requires matrix_panel metrics",
                target="metrics.matrix_panel",
            )
        )
        return issues
    summary_panel_metrics = metrics.get("summary_panel")
    if not isinstance(summary_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="summary_panel_metrics_missing",
                message="broader heterogeneity summary qc requires summary_panel metrics",
                target="metrics.summary_panel",
            )
        )
        return issues

    reference_line_box = guide_box_by_id.get(str(matrix_panel_metrics.get("reference_line_box_id") or "").strip())
    if reference_line_box is None:
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="broader heterogeneity summary qc requires one reference line inside the matrix panel",
                target="metrics.matrix_panel.reference_line_box_id",
                box_refs=(matrix_panel.box_id,),
            )
        )
    elif not _box_within_box(reference_line_box, matrix_panel):
        issues.append(
            _issue(
                rule_id="reference_line_outside_matrix_panel",
                message="broader heterogeneity summary reference line must stay within the matrix panel",
                target=f"guide_boxes.{reference_line_box.box_id}",
                box_refs=(reference_line_box.box_id, matrix_panel.box_id),
            )
        )

    legend_title_box = layout_box_by_id.get(str(metrics.get("slice_legend_title_box_id") or "").strip())
    if legend_title_box is None:
        issues.append(
            _issue(
                rule_id="slice_legend_title_missing",
                message="broader heterogeneity summary qc requires one slice legend title box",
                target="metrics.slice_legend_title_box_id",
            )
        )

    slices = metrics.get("slices")
    if not isinstance(slices, list) or not slices:
        issues.append(
            _issue(
                rule_id="slices_missing",
                message="broader heterogeneity summary qc requires non-empty slice metrics",
                target="metrics.slices",
            )
        )
        return issues
    if len(slices) < 2 or len(slices) > 5:
        issues.append(
            _issue(
                rule_id="slice_count_invalid",
                message="broader heterogeneity summary qc requires between 2 and 5 slices",
                target="metrics.slices",
                observed={"count": len(slices)},
                expected={"minimum": 2, "maximum": 5},
            )
        )

    supported_slice_kinds = {"cohort", "subgroup", "adjustment", "sensitivity"}
    declared_slice_ids: list[str] = []
    seen_slice_ids: set[str] = set()
    seen_slice_labels: set[str] = set()
    previous_slice_order: int | None = None
    for slice_index, slice_metric in enumerate(slices):
        if not isinstance(slice_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.slices[{slice_index}] must be an object")
        slice_id = _require_non_empty_text(
            slice_metric.get("slice_id"),
            label=f"layout_sidecar.metrics.slices[{slice_index}].slice_id",
        )
        if slice_id in seen_slice_ids:
            issues.append(
                _issue(
                    rule_id="slice_id_duplicate",
                    message="broader heterogeneity summary slice_id values must be unique",
                    target=f"metrics.slices[{slice_index}].slice_id",
                )
            )
        seen_slice_ids.add(slice_id)
        slice_label = _require_non_empty_text(
            slice_metric.get("slice_label"),
            label=f"layout_sidecar.metrics.slices[{slice_index}].slice_label",
        )
        if slice_label in seen_slice_labels:
            issues.append(
                _issue(
                    rule_id="slice_label_duplicate",
                    message="broader heterogeneity summary slice_label values must be unique",
                    target=f"metrics.slices[{slice_index}].slice_label",
                )
            )
        seen_slice_labels.add(slice_label)
        slice_kind = _require_non_empty_text(
            slice_metric.get("slice_kind"),
            label=f"layout_sidecar.metrics.slices[{slice_index}].slice_kind",
        )
        if slice_kind not in supported_slice_kinds:
            issues.append(
                _issue(
                    rule_id="slice_kind_invalid",
                    message="broader heterogeneity summary slice_kind must be one of cohort, subgroup, adjustment, sensitivity",
                    target=f"metrics.slices[{slice_index}].slice_kind",
                    observed=slice_kind,
                )
            )
        slice_order = int(_require_numeric(slice_metric.get("slice_order"), label=f"layout_sidecar.metrics.slices[{slice_index}].slice_order"))
        if previous_slice_order is not None and slice_order <= previous_slice_order:
            issues.append(
                _issue(
                    rule_id="slice_order_invalid",
                    message="broader heterogeneity summary slices must have strictly increasing slice_order",
                    target=f"metrics.slices[{slice_index}].slice_order",
                )
            )
        previous_slice_order = slice_order
        legend_label_box = layout_box_by_id.get(str(slice_metric.get("legend_label_box_id") or "").strip())
        if legend_label_box is None:
            issues.append(
                _issue(
                    rule_id="slice_legend_label_missing",
                    message="every broader heterogeneity slice must reference a legend label box",
                    target=f"metrics.slices[{slice_index}].legend_label_box_id",
                )
            )
        declared_slice_ids.append(slice_id)

    effect_rows = metrics.get("effect_rows")
    if not isinstance(effect_rows, list) or not effect_rows:
        issues.append(
            _issue(
                rule_id="effect_rows_missing",
                message="broader heterogeneity summary qc requires non-empty effect_rows metrics",
                target="metrics.effect_rows",
            )
        )
        return issues

    supported_verdicts = {"stable", "attenuated", "context_dependent", "unstable"}
    declared_slice_id_set = set(declared_slice_ids)
    label_panel_map = {
        str(matrix_panel_metrics.get("panel_label_box_id") or "").strip() or "panel_label_A": matrix_panel.box_id,
        str(summary_panel_metrics.get("panel_label_box_id") or "").strip() or "panel_label_B": summary_panel.box_id,
    }
    summary_panel_height = summary_panel.y1 - summary_panel.y0
    alignment_tolerance = max(summary_panel_height * 0.08, 0.025)
    for row_index, row in enumerate(effect_rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.effect_rows[{row_index}] must be an object")
        verdict = _require_non_empty_text(
            row.get("verdict"),
            label=f"layout_sidecar.metrics.effect_rows[{row_index}].verdict",
        )
        if verdict not in supported_verdicts:
            issues.append(
                _issue(
                    rule_id="effect_row_verdict_invalid",
                    message="broader heterogeneity summary verdicts must use the supported state vocabulary",
                    target=f"metrics.effect_rows[{row_index}].verdict",
                    observed=verdict,
                )
            )

        label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="effect_row_label_missing",
                    message="broader heterogeneity summary rows must reference a row label box",
                    target=f"metrics.effect_rows[{row_index}].label_box_id",
                    box_refs=(matrix_panel.box_id,),
                )
            )
        elif _boxes_overlap(label_box, matrix_panel):
            issues.append(
                _issue(
                    rule_id="effect_row_label_matrix_overlap",
                    message="broader heterogeneity summary row labels must stay outside the matrix panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, matrix_panel.box_id),
                )
            )

        verdict_box = layout_box_by_id.get(str(row.get("verdict_box_id") or "").strip())
        if verdict_box is None:
            issues.append(
                _issue(
                    rule_id="verdict_box_missing",
                    message="broader heterogeneity summary rows must reference a verdict box",
                    target=f"metrics.effect_rows[{row_index}].verdict_box_id",
                    box_refs=(summary_panel.box_id,),
                )
            )
        elif not _box_within_box(verdict_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="verdict_box_outside_summary_panel",
                    message="broader heterogeneity summary verdict boxes must stay within the summary panel",
                    target=f"layout_boxes.{verdict_box.box_id}",
                    box_refs=(verdict_box.box_id, summary_panel.box_id),
                )
            )

        detail_box_id = str(row.get("detail_box_id") or "").strip()
        detail_box = layout_box_by_id.get(detail_box_id) if detail_box_id else None
        if detail_box is not None and not _box_within_box(detail_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="detail_box_outside_summary_panel",
                    message="broader heterogeneity summary detail boxes must stay within the summary panel",
                    target=f"layout_boxes.{detail_box.box_id}",
                    box_refs=(detail_box.box_id, summary_panel.box_id),
                )
            )

        if label_box is not None and verdict_box is not None:
            label_center_y = (label_box.y0 + label_box.y1) / 2.0
            verdict_center_y = (verdict_box.y0 + verdict_box.y1) / 2.0
            if abs(label_center_y - verdict_center_y) > alignment_tolerance:
                issues.append(
                    _issue(
                        rule_id="verdict_row_misaligned",
                        message="broader heterogeneity summary verdicts must stay vertically aligned to their effect row",
                        target=f"metrics.effect_rows[{row_index}].verdict_box_id",
                        observed={"label_center_y": label_center_y, "verdict_center_y": verdict_center_y},
                    )
                )

        slice_estimates = row.get("slice_estimates")
        if not isinstance(slice_estimates, list) or not slice_estimates:
            issues.append(
                _issue(
                    rule_id="slice_estimates_missing",
                    message="every broader heterogeneity summary row must provide non-empty slice_estimates",
                    target=f"metrics.effect_rows[{row_index}].slice_estimates",
                )
            )
            continue

        seen_row_slice_ids: set[str] = set()
        for estimate_index, estimate in enumerate(slice_estimates):
            if not isinstance(estimate, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}] must be an object"
                )
            slice_id = _require_non_empty_text(
                estimate.get("slice_id"),
                label=f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}].slice_id",
            )
            seen_row_slice_ids.add(slice_id)
            lower = _require_numeric(
                estimate.get("lower"),
                label=f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}].lower",
            )
            point_estimate = _require_numeric(
                estimate.get("estimate"),
                label=f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}].estimate",
            )
            upper = _require_numeric(
                estimate.get("upper"),
                label=f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}].upper",
            )
            if not (lower <= point_estimate <= upper):
                issues.append(
                    _issue(
                        rule_id="estimate_outside_interval",
                        message="broader heterogeneity summary estimates must lie within their confidence interval",
                        target=f"metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}]",
                        observed={"lower": lower, "estimate": point_estimate, "upper": upper},
                    )
                )
            marker_box = layout_box_by_id.get(str(estimate.get("marker_box_id") or "").strip())
            interval_box = layout_box_by_id.get(str(estimate.get("interval_box_id") or "").strip())
            if marker_box is None or interval_box is None:
                issues.append(
                    _issue(
                        rule_id="slice_estimate_box_missing",
                        message="broader heterogeneity summary slice estimates must reference marker and interval boxes",
                        target=f"metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}]",
                        box_refs=(matrix_panel.box_id,),
                    )
                )
                continue
            if not _box_within_box(marker_box, matrix_panel):
                issues.append(
                    _issue(
                        rule_id="estimate_marker_outside_matrix_panel",
                        message="broader heterogeneity summary markers must stay within the matrix panel",
                        target=f"layout_boxes.{marker_box.box_id}",
                        box_refs=(marker_box.box_id, matrix_panel.box_id),
                    )
                )
            if not _box_within_box(interval_box, matrix_panel):
                issues.append(
                    _issue(
                        rule_id="ci_segment_outside_matrix_panel",
                        message="broader heterogeneity summary confidence intervals must stay within the matrix panel",
                        target=f"layout_boxes.{interval_box.box_id}",
                        box_refs=(interval_box.box_id, matrix_panel.box_id),
                    )
                )

        if seen_row_slice_ids != declared_slice_id_set:
            issues.append(
                _issue(
                    rule_id="slice_coverage_mismatch",
                    message="broader heterogeneity summary rows must cover every declared slice exactly once",
                    target=f"metrics.effect_rows[{row_index}].slice_estimates",
                    observed={"slice_ids": sorted(seen_row_slice_ids)},
                    expected={"slice_ids": sorted(declared_slice_id_set)},
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )
    return issues


def _check_publication_interaction_effect_summary_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "panel_label",
        "subplot_x_axis_title",
        "row_label",
        "estimate_marker",
        "ci_segment",
        "verdict_value",
        "verdict_detail",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    estimate_panel = panel_boxes_by_id.get("estimate_panel")
    summary_panel = panel_boxes_by_id.get("summary_panel")
    if estimate_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="interaction effect summary qc requires estimate_panel and summary_panel",
                target="panel_boxes",
            )
        )
        return issues

    text_boxes = tuple(
        box for box in sidecar.layout_boxes if box.box_type in {"title", "panel_title", "panel_label", "subplot_x_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}

    if metrics.get("reference_value") is None:
        issues.append(
            _issue(
                rule_id="reference_value_missing",
                message="interaction effect summary qc requires a numeric reference_value",
                target="metrics.reference_value",
            )
        )
    else:
        _require_numeric(metrics.get("reference_value"), label="layout_sidecar.metrics.reference_value")

    estimate_panel_metrics = metrics.get("estimate_panel")
    if not isinstance(estimate_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="estimate_panel_metrics_missing",
                message="interaction effect summary qc requires estimate_panel metrics",
                target="metrics.estimate_panel",
            )
        )
        return issues
    summary_panel_metrics = metrics.get("summary_panel")
    if not isinstance(summary_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="summary_panel_metrics_missing",
                message="interaction effect summary qc requires summary_panel metrics",
                target="metrics.summary_panel",
            )
        )
        return issues

    panel_title_box = layout_box_by_id.get(str(estimate_panel_metrics.get("panel_title_box_id") or "").strip())
    x_axis_title_box = layout_box_by_id.get(str(estimate_panel_metrics.get("x_axis_title_box_id") or "").strip())
    if panel_title_box is None or x_axis_title_box is None:
        issues.append(
            _issue(
                rule_id="estimate_panel_text_box_missing",
                message="interaction effect estimate panel requires title and x-axis title boxes",
                target="metrics.estimate_panel",
                box_refs=(estimate_panel.box_id,),
            )
        )
    summary_panel_title_box = layout_box_by_id.get(str(summary_panel_metrics.get("panel_title_box_id") or "").strip())
    if summary_panel_title_box is None:
        issues.append(
            _issue(
                rule_id="summary_panel_title_missing",
                message="interaction effect summary panel requires a title box",
                target="metrics.summary_panel.panel_title_box_id",
                box_refs=(summary_panel.box_id,),
            )
        )

    reference_line_box = guide_box_by_id.get(str(estimate_panel_metrics.get("reference_line_box_id") or "").strip())
    if reference_line_box is None:
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="interaction effect summary qc requires one reference line inside the estimate panel",
                target="metrics.estimate_panel.reference_line_box_id",
                box_refs=(estimate_panel.box_id,),
            )
        )
    elif not _box_within_box(reference_line_box, estimate_panel):
        issues.append(
            _issue(
                rule_id="reference_line_outside_estimate_panel",
                message="interaction effect reference line must stay within the estimate panel",
                target=f"guide_boxes.{reference_line_box.box_id}",
                box_refs=(reference_line_box.box_id, estimate_panel.box_id),
            )
        )

    modifiers = metrics.get("modifiers")
    if not isinstance(modifiers, list) or not modifiers:
        issues.append(
            _issue(
                rule_id="modifiers_missing",
                message="interaction effect summary qc requires non-empty modifier metrics",
                target="metrics.modifiers",
            )
        )
        return issues
    if len(modifiers) < 2 or len(modifiers) > 6:
        issues.append(
            _issue(
                rule_id="modifier_count_invalid",
                message="interaction effect summary qc requires between 2 and 6 modifiers",
                target="metrics.modifiers",
                observed={"count": len(modifiers)},
                expected={"minimum": 2, "maximum": 6},
            )
        )

    supported_verdicts = {"credible", "suggestive", "uncertain"}
    seen_modifier_ids: set[str] = set()
    seen_modifier_labels: set[str] = set()
    label_panel_map = {
        str(estimate_panel_metrics.get("panel_label_box_id") or "").strip() or "panel_label_A": estimate_panel.box_id,
        str(summary_panel_metrics.get("panel_label_box_id") or "").strip() or "panel_label_B": summary_panel.box_id,
    }
    summary_panel_height = summary_panel.y1 - summary_panel.y0
    alignment_tolerance = max(summary_panel_height * 0.08, 0.025)
    for modifier_index, modifier in enumerate(modifiers):
        if not isinstance(modifier, dict):
            raise ValueError(f"layout_sidecar.metrics.modifiers[{modifier_index}] must be an object")

        modifier_id = _require_non_empty_text(
            modifier.get("modifier_id"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].modifier_id",
        )
        if modifier_id in seen_modifier_ids:
            issues.append(
                _issue(
                    rule_id="modifier_id_duplicate",
                    message="interaction effect summary modifier_id values must be unique",
                    target=f"metrics.modifiers[{modifier_index}].modifier_id",
                    observed=modifier_id,
                )
            )
        seen_modifier_ids.add(modifier_id)

        modifier_label = _require_non_empty_text(
            modifier.get("modifier_label"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].modifier_label",
        )
        if modifier_label in seen_modifier_labels:
            issues.append(
                _issue(
                    rule_id="modifier_label_duplicate",
                    message="interaction effect summary modifier labels must be unique",
                    target=f"metrics.modifiers[{modifier_index}].modifier_label",
                    observed=modifier_label,
                )
            )
        seen_modifier_labels.add(modifier_label)

        lower = _require_numeric(
            modifier.get("lower"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].lower",
        )
        interaction_estimate = _require_numeric(
            modifier.get("interaction_estimate"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].interaction_estimate",
        )
        upper = _require_numeric(
            modifier.get("upper"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].upper",
        )
        if not (lower <= interaction_estimate <= upper):
            issues.append(
                _issue(
                    rule_id="interaction_estimate_outside_interval",
                    message="interaction effect estimate must lie within the confidence interval",
                    target=f"metrics.modifiers[{modifier_index}]",
                    observed={"lower": lower, "interaction_estimate": interaction_estimate, "upper": upper},
                )
            )

        interaction_p_value = _require_numeric(
            modifier.get("interaction_p_value"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].interaction_p_value",
        )
        if interaction_p_value < 0.0 or interaction_p_value > 1.0:
            issues.append(
                _issue(
                    rule_id="interaction_p_value_invalid",
                    message="interaction effect summary p values must stay within [0.0, 1.0]",
                    target=f"metrics.modifiers[{modifier_index}].interaction_p_value",
                    observed=interaction_p_value,
                )
            )

        verdict = _require_non_empty_text(
            modifier.get("verdict"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].verdict",
        )
        if verdict not in supported_verdicts:
            issues.append(
                _issue(
                    rule_id="interaction_verdict_invalid",
                    message="interaction effect summary verdicts must use the supported vocabulary",
                    target=f"metrics.modifiers[{modifier_index}].verdict",
                    observed=verdict,
                )
            )

        label_box = layout_box_by_id.get(str(modifier.get("label_box_id") or "").strip())
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="modifier_label_missing",
                    message="interaction effect summary rows must reference a modifier label box",
                    target=f"metrics.modifiers[{modifier_index}].label_box_id",
                    box_refs=(estimate_panel.box_id,),
                )
            )
        elif _boxes_overlap(label_box, estimate_panel):
            issues.append(
                _issue(
                    rule_id="modifier_label_estimate_panel_overlap",
                    message="interaction modifier labels must stay outside the estimate panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, estimate_panel.box_id),
                )
            )

        support_label_box_id = str(modifier.get("support_label_box_id") or "").strip()
        support_label_box = layout_box_by_id.get(support_label_box_id) if support_label_box_id else None
        if support_label_box is not None and not _box_within_box(support_label_box, estimate_panel):
            issues.append(
                _issue(
                    rule_id="support_label_outside_estimate_panel",
                    message="interaction support labels must stay within the estimate panel",
                    target=f"layout_boxes.{support_label_box.box_id}",
                    box_refs=(support_label_box.box_id, estimate_panel.box_id),
                )
            )

        marker_box = layout_box_by_id.get(str(modifier.get("marker_box_id") or "").strip())
        interval_box = layout_box_by_id.get(str(modifier.get("interval_box_id") or "").strip())
        if marker_box is None or interval_box is None:
            issues.append(
                _issue(
                    rule_id="interaction_estimate_box_missing",
                    message="interaction effect rows must reference marker and interval boxes",
                    target=f"metrics.modifiers[{modifier_index}]",
                    box_refs=(estimate_panel.box_id,),
                )
            )
        else:
            if not _box_within_box(marker_box, estimate_panel):
                issues.append(
                    _issue(
                        rule_id="interaction_marker_outside_estimate_panel",
                        message="interaction markers must stay within the estimate panel",
                        target=f"layout_boxes.{marker_box.box_id}",
                        box_refs=(marker_box.box_id, estimate_panel.box_id),
                    )
                )
            if not _box_within_box(interval_box, estimate_panel):
                issues.append(
                    _issue(
                        rule_id="interaction_interval_outside_estimate_panel",
                        message="interaction confidence intervals must stay within the estimate panel",
                        target=f"layout_boxes.{interval_box.box_id}",
                        box_refs=(interval_box.box_id, estimate_panel.box_id),
                    )
                )

        verdict_box = layout_box_by_id.get(str(modifier.get("verdict_box_id") or "").strip())
        if verdict_box is None:
            issues.append(
                _issue(
                    rule_id="interaction_verdict_missing",
                    message="interaction effect rows must reference a verdict box",
                    target=f"metrics.modifiers[{modifier_index}].verdict_box_id",
                    box_refs=(summary_panel.box_id,),
                )
            )
        elif not _box_within_box(verdict_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="interaction_verdict_outside_summary_panel",
                    message="interaction verdict boxes must stay within the summary panel",
                    target=f"layout_boxes.{verdict_box.box_id}",
                    box_refs=(verdict_box.box_id, summary_panel.box_id),
                )
            )

        detail_box = layout_box_by_id.get(str(modifier.get("detail_box_id") or "").strip())
        if detail_box is None:
            issues.append(
                _issue(
                    rule_id="interaction_detail_missing",
                    message="interaction effect rows must reference a detail box",
                    target=f"metrics.modifiers[{modifier_index}].detail_box_id",
                    box_refs=(summary_panel.box_id,),
                )
            )
        elif not _box_within_box(detail_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="interaction_detail_outside_summary_panel",
                    message="interaction detail boxes must stay within the summary panel",
                    target=f"layout_boxes.{detail_box.box_id}",
                    box_refs=(detail_box.box_id, summary_panel.box_id),
                )
            )

        if label_box is not None and verdict_box is not None:
            label_center_y = (label_box.y0 + label_box.y1) / 2.0
            verdict_center_y = (verdict_box.y0 + verdict_box.y1) / 2.0
            if abs(label_center_y - verdict_center_y) > alignment_tolerance:
                issues.append(
                    _issue(
                        rule_id="interaction_verdict_row_misaligned",
                        message="interaction verdicts must stay vertically aligned to their modifier row",
                        target=f"metrics.modifiers[{modifier_index}].verdict_box_id",
                        observed={"label_center_y": label_center_y, "verdict_center_y": verdict_center_y},
                    )
                )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )
    return issues


def _check_audit_panel_collection_metrics(
    panels: object,
    *,
    target: str,
) -> tuple[list[dict[str, Any]], int, int]:
    issues: list[dict[str, Any]] = []
    if not isinstance(panels, list) or not panels:
        issues.append(
            _issue(
                rule_id="audit_panels_missing",
                message="audit-panel collection must be non-empty",
                target=target,
            )
        )
        return issues, 0, 0
    seen_panel_ids: set[str] = set()
    total_rows = 0
    reference_count = 0
    for index, panel in enumerate(panels):
        if not isinstance(panel, dict):
            raise ValueError(f"{target}[{index}] must be an object")
        panel_id = str(panel.get("panel_id") or "").strip()
        if not panel_id:
            issues.append(
                _issue(
                    rule_id="panel_id_missing",
                    message="audit panels must declare a non-empty panel_id",
                    target=f"{target}[{index}].panel_id",
                )
            )
        elif panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="panel_id_not_unique",
                    message="audit panel ids must be unique",
                    target=f"{target}[{index}].panel_id",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)
        rows = panel.get("rows")
        if not isinstance(rows, list) or not rows:
            issues.append(
                _issue(
                    rule_id="panel_rows_missing",
                    message="audit panels must contain non-empty rows",
                    target=f"{target}[{index}].rows",
                )
            )
            continue
        total_rows += len(rows)
        if panel.get("reference_value") is not None:
            _require_numeric(panel.get("reference_value"), label=f"{target}[{index}].reference_value")
            reference_count += 1
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"{target}[{index}].rows[{row_index}] must be an object")
            row_label = str(row.get("label") or "").strip()
            if not row_label:
                issues.append(
                    _issue(
                        rule_id="row_label_missing",
                        message="audit-panel rows require non-empty labels",
                        target=f"{target}[{index}].rows[{row_index}].label",
                    )
                )
            row_value = _require_numeric(row.get("value"), label=f"{target}[{index}].rows[{row_index}].value")
            if not math.isfinite(row_value):
                issues.append(
                    _issue(
                        rule_id="row_value_non_finite",
                        message="audit-panel row values must be finite",
                        target=f"{target}[{index}].rows[{row_index}]",
                    )
                )
    return issues, total_rows, reference_count


def _check_publication_model_complexity_audit(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["metric_marker", "audit_bar"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "subplot_title", "subplot_x_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    metric_panels_issues, total_metric_rows, metric_reference_count = _check_audit_panel_collection_metrics(
        sidecar.metrics.get("metric_panels"),
        target="metrics.metric_panels",
    )
    audit_panels_issues, total_audit_rows, audit_reference_count = _check_audit_panel_collection_metrics(
        sidecar.metrics.get("audit_panels"),
        target="metrics.audit_panels",
    )
    issues.extend(metric_panels_issues)
    issues.extend(audit_panels_issues)

    metric_panel_boxes = _boxes_of_type(sidecar.panel_boxes, "metric_panel")
    audit_panel_boxes = _boxes_of_type(sidecar.panel_boxes, "audit_panel")
    metric_panels = sidecar.metrics.get("metric_panels")
    audit_panels = sidecar.metrics.get("audit_panels")
    if isinstance(metric_panels, list) and len(metric_panel_boxes) != len(metric_panels):
        issues.append(
            _issue(
                rule_id="metric_panel_count_mismatch",
                message="metric panel box count must match metric_panels metrics",
                target="panel_boxes",
                observed={"panel_boxes": len(metric_panel_boxes)},
                expected={"metric_panels": len(metric_panels)},
            )
        )
    if isinstance(audit_panels, list) and len(audit_panel_boxes) != len(audit_panels):
        issues.append(
            _issue(
                rule_id="audit_panel_count_mismatch",
                message="audit panel box count must match audit_panels metrics",
                target="panel_boxes",
                observed={"panel_boxes": len(audit_panel_boxes)},
                expected={"audit_panels": len(audit_panels)},
            )
        )

    metric_marker_count = len(_boxes_of_type(sidecar.layout_boxes, "metric_marker"))
    if total_metric_rows and metric_marker_count < total_metric_rows:
        issues.append(
            _issue(
                rule_id="metric_markers_missing",
                message="metric marker boxes must cover every metric row",
                target="layout_boxes",
                observed={"metric_marker_count": metric_marker_count},
                expected={"minimum_metric_rows": total_metric_rows},
            )
        )
    audit_bar_count = len(_boxes_of_type(sidecar.layout_boxes, "audit_bar"))
    if total_audit_rows and audit_bar_count < total_audit_rows:
        issues.append(
            _issue(
                rule_id="audit_bars_missing",
                message="audit bar boxes must cover every audit row",
                target="layout_boxes",
                observed={"audit_bar_count": audit_bar_count},
                expected={"minimum_audit_rows": total_audit_rows},
            )
        )
    reference_line_count = len(_boxes_of_type(sidecar.guide_boxes, "reference_line"))
    if reference_line_count < metric_reference_count + audit_reference_count:
        issues.append(
            _issue(
                rule_id="reference_lines_missing",
                message="reference-line guide boxes must cover every panel with reference_value",
                target="guide_boxes",
                observed={"reference_line_count": reference_line_count},
                expected={"minimum_reference_lines": metric_reference_count + audit_reference_count},
            )
        )

    return issues


def _check_publication_landmark_performance_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    required_box_types = ["metric_marker", "panel_title", "panel_label", "subplot_x_axis_title", "subplot_y_axis_title"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "panel_label", "subplot_x_axis_title", "subplot_y_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    panel_metrics = sidecar.metrics.get("metric_panels")
    metric_panel_issues, total_metric_rows, metric_reference_count = _check_audit_panel_collection_metrics(
        panel_metrics,
        target="metrics.metric_panels",
    )
    issues.extend(metric_panel_issues)
    if not isinstance(panel_metrics, list) or not panel_metrics:
        return issues
    if len(panel_metrics) != 3:
        issues.append(
            _issue(
                rule_id="metric_panel_count_invalid",
                message="landmark performance panel requires exactly three metric panels",
                target="metrics.metric_panels",
                observed={"count": len(panel_metrics)},
                expected={"count": 3},
            )
        )

    metric_panel_boxes = _boxes_of_type(sidecar.panel_boxes, "metric_panel")
    if len(metric_panel_boxes) != len(panel_metrics):
        issues.append(
            _issue(
                rule_id="metric_panel_count_mismatch",
                message="metric panel box count must match metric_panels metrics",
                target="panel_boxes",
                observed={"panel_boxes": len(metric_panel_boxes)},
                expected={"metric_panels": len(panel_metrics)},
            )
        )

    metric_marker_count = len(_boxes_of_type(sidecar.layout_boxes, "metric_marker"))
    if total_metric_rows and metric_marker_count < total_metric_rows:
        issues.append(
            _issue(
                rule_id="metric_markers_missing",
                message="metric marker boxes must cover every landmark summary row",
                target="layout_boxes",
                observed={"metric_marker_count": metric_marker_count},
                expected={"minimum_metric_rows": total_metric_rows},
            )
        )
    reference_line_count = len(_boxes_of_type(sidecar.guide_boxes, "reference_line"))
    if reference_line_count < metric_reference_count:
        issues.append(
            _issue(
                rule_id="reference_lines_missing",
                message="reference-line guide boxes must cover every panel with reference_value",
                target="guide_boxes",
                observed={"reference_line_count": reference_line_count},
                expected={"minimum_reference_lines": metric_reference_count},
            )
        )

    expected_metric_kinds = ("c_index", "brier_score", "calibration_slope")
    seen_metric_kinds: set[str] = set()
    base_row_labels: tuple[str, ...] | None = None
    base_analysis_labels: tuple[str, ...] | None = None
    label_panel_map: dict[str, str] = {}
    for panel_index, panel in enumerate(panel_metrics):
        if not isinstance(panel, dict):
            raise ValueError(f"metrics.metric_panels[{panel_index}] must be an object")
        panel_label = str(panel.get("panel_label") or "").strip()
        if panel_label:
            label_panel_map[f"panel_label_{_panel_label_token(panel_label)}"] = f"panel_{_panel_label_token(panel_label)}"
        metric_kind = str(panel.get("metric_kind") or "").strip()
        if metric_kind not in expected_metric_kinds:
            issues.append(
                _issue(
                    rule_id="metric_kind_invalid",
                    message="landmark performance panel metric_kind must be c_index, brier_score, or calibration_slope",
                    target=f"metrics.metric_panels[{panel_index}].metric_kind",
                    observed=metric_kind,
                )
            )
            continue
        if metric_kind in seen_metric_kinds:
            issues.append(
                _issue(
                    rule_id="metric_kind_duplicate",
                    message="landmark performance panel metric_kind values must be unique",
                    target="metrics.metric_panels",
                    observed=metric_kind,
                )
            )
        seen_metric_kinds.add(metric_kind)
        rows = panel.get("rows")
        if not isinstance(rows, list):
            raise ValueError(f"metrics.metric_panels[{panel_index}].rows must be a list")
        row_labels: list[str] = []
        analysis_labels: list[str] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"metrics.metric_panels[{panel_index}].rows[{row_index}] must be an object")
            row_label = str(row.get("label") or "").strip()
            analysis_window_label = str(row.get("analysis_window_label") or "").strip()
            landmark_months = _require_numeric(
                row.get("landmark_months"),
                label=f"metrics.metric_panels[{panel_index}].rows[{row_index}].landmark_months",
            )
            prediction_months = _require_numeric(
                row.get("prediction_months"),
                label=f"metrics.metric_panels[{panel_index}].rows[{row_index}].prediction_months",
            )
            value = _require_numeric(
                row.get("value"),
                label=f"metrics.metric_panels[{panel_index}].rows[{row_index}].value",
            )
            if not row_label:
                issues.append(
                    _issue(
                        rule_id="row_label_missing",
                        message="landmark performance rows require non-empty labels",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}].label",
                    )
                )
            if not analysis_window_label:
                issues.append(
                    _issue(
                        rule_id="analysis_window_label_missing",
                        message="landmark performance rows require non-empty analysis_window_label",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}].analysis_window_label",
                    )
                )
            if landmark_months <= 0 or prediction_months <= 0:
                issues.append(
                    _issue(
                        rule_id="non_positive_window_months",
                        message="landmark_months and prediction_months must stay positive",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}]",
                    )
                )
            if prediction_months <= landmark_months:
                issues.append(
                    _issue(
                        rule_id="prediction_window_not_forward",
                        message="prediction_months must exceed landmark_months for landmark windows",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}]",
                    )
                )
            if metric_kind in {"c_index", "brier_score"} and (value < 0.0 or value > 1.0):
                issues.append(
                    _issue(
                        rule_id="probability_metric_out_of_range",
                        message="c_index and brier_score values must stay within [0, 1]",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}].value",
                        observed=value,
                    )
                )
            if metric_kind == "calibration_slope" and not math.isfinite(value):
                issues.append(
                    _issue(
                        rule_id="calibration_slope_non_finite",
                        message="calibration slope values must be finite",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}].value",
                    )
                )
            row_labels.append(row_label)
            analysis_labels.append(analysis_window_label)
        row_labels_tuple = tuple(row_labels)
        analysis_labels_tuple = tuple(analysis_labels)
        if base_row_labels is None:
            base_row_labels = row_labels_tuple
            base_analysis_labels = analysis_labels_tuple
        else:
            if row_labels_tuple != base_row_labels:
                issues.append(
                    _issue(
                        rule_id="row_label_sets_mismatch",
                        message="all landmark metric panels must share the same row-label set and ordering",
                        target=f"metrics.metric_panels[{panel_index}].rows",
                    )
                )
            if analysis_labels_tuple != base_analysis_labels:
                issues.append(
                    _issue(
                        rule_id="analysis_window_sets_mismatch",
                        message="all landmark metric panels must share the same analysis-window set and ordering",
                        target=f"metrics.metric_panels[{panel_index}].rows",
                    )
                )

    if seen_metric_kinds and tuple(sorted(seen_metric_kinds)) != tuple(sorted(expected_metric_kinds)):
        issues.append(
            _issue(
                rule_id="metric_kind_set_mismatch",
                message="landmark performance panel must cover c_index, brier_score, and calibration_slope exactly once",
                target="metrics.metric_panels",
                observed=tuple(sorted(seen_metric_kinds)),
                expected=expected_metric_kinds,
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


def _check_publication_time_to_event_threshold_governance_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    required_box_types = ["panel_title", "subplot_x_axis_title", "panel_label", "threshold_card", "legend"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    threshold_cards = _boxes_of_type(sidecar.layout_boxes, "threshold_card")
    issues.extend(
        _check_pairwise_non_overlap(
            threshold_cards,
            rule_id="threshold_card_overlap",
            target="threshold_card",
        )
    )
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    threshold_panel = panel_boxes_by_id.get("threshold_panel")
    calibration_panel = panel_boxes_by_id.get("calibration_panel")
    if threshold_panel is None:
        issues.append(
            _issue(
                rule_id="threshold_panel_missing",
                message="threshold governance panel requires an explicit threshold_panel region",
                target="panel_boxes",
                expected="threshold_panel",
            )
        )
    if calibration_panel is None:
        issues.append(
            _issue(
                rule_id="calibration_panel_missing",
                message="threshold governance panel requires an explicit calibration_panel region",
                target="panel_boxes",
                expected="calibration_panel",
            )
        )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "threshold_panel",
                "panel_label_B": "calibration_panel",
            },
        )
    )

    threshold_summaries = sidecar.metrics.get("threshold_summaries")
    if not isinstance(threshold_summaries, list) or not threshold_summaries:
        issues.append(
            _issue(
                rule_id="threshold_summaries_missing",
                message="threshold governance qc requires non-empty threshold_summaries metrics",
                target="metrics.threshold_summaries",
            )
        )
    else:
        if threshold_cards and len(threshold_cards) != len(threshold_summaries):
            issues.append(
                _issue(
                    rule_id="threshold_card_count_mismatch",
                    message="threshold governance threshold-card count must match metrics.threshold_summaries",
                    target="layout_boxes.threshold_card",
                    observed={"threshold_cards": len(threshold_cards)},
                    expected={"threshold_summaries": len(threshold_summaries)},
                )
            )
        threshold_card_by_id = {box.box_id: box for box in threshold_cards}
        previous_threshold = -1.0
        for index, item in enumerate(threshold_summaries):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.threshold_summaries[{index}] must be an object")
            threshold_label = str(item.get("threshold_label") or "").strip()
            threshold = _require_numeric(
                item.get("threshold"),
                label=f"layout_sidecar.metrics.threshold_summaries[{index}].threshold",
            )
            sensitivity = _require_numeric(
                item.get("sensitivity"),
                label=f"layout_sidecar.metrics.threshold_summaries[{index}].sensitivity",
            )
            specificity = _require_numeric(
                item.get("specificity"),
                label=f"layout_sidecar.metrics.threshold_summaries[{index}].specificity",
            )
            net_benefit = _require_numeric(
                item.get("net_benefit"),
                label=f"layout_sidecar.metrics.threshold_summaries[{index}].net_benefit",
            )
            if not threshold_label:
                issues.append(
                    _issue(
                        rule_id="threshold_label_missing",
                        message="threshold governance rows require non-empty threshold labels",
                        target=f"metrics.threshold_summaries[{index}].threshold_label",
                    )
                )
            if threshold <= previous_threshold:
                issues.append(
                    _issue(
                        rule_id="threshold_order_not_increasing",
                        message="threshold values must stay strictly increasing",
                        target="metrics.threshold_summaries",
                    )
                )
            previous_threshold = threshold
            if threshold < 0.0 or threshold > 1.0:
                issues.append(
                    _issue(
                        rule_id="threshold_out_of_range",
                        message="threshold values must stay within [0, 1]",
                        target=f"metrics.threshold_summaries[{index}].threshold",
                        observed=threshold,
                    )
                )
            for field_name, value in (("sensitivity", sensitivity), ("specificity", specificity)):
                if 0.0 <= value <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id=f"{field_name}_out_of_range",
                        message=f"{field_name} must stay within [0, 1]",
                        target=f"metrics.threshold_summaries[{index}].{field_name}",
                        observed=value,
                    )
                )
            if not math.isfinite(net_benefit):
                issues.append(
                    _issue(
                        rule_id="net_benefit_non_finite",
                        message="net benefit must be finite",
                        target=f"metrics.threshold_summaries[{index}].net_benefit",
                    )
                )
            card_box_id = str(item.get("card_box_id") or "").strip()
            if not card_box_id:
                issues.append(
                    _issue(
                        rule_id="threshold_card_reference_missing",
                        message="threshold governance metrics must reference the rendered threshold card box",
                        target=f"metrics.threshold_summaries[{index}].card_box_id",
                    )
                )
                continue
            card_box = threshold_card_by_id.get(card_box_id)
            if card_box is None:
                issues.append(
                    _issue(
                        rule_id="threshold_card_reference_missing",
                        message="threshold governance metrics must reference an existing threshold_card box",
                        target=f"metrics.threshold_summaries[{index}].card_box_id",
                        observed=card_box_id,
                    )
                )
                continue
            if threshold_panel is not None and not _box_within_box(card_box, threshold_panel):
                issues.append(
                    _issue(
                        rule_id="threshold_card_outside_panel",
                        message="threshold-card boxes must stay within the threshold_panel region",
                        target=f"layout_boxes.{card_box.box_id}",
                        box_refs=(card_box.box_id, threshold_panel.box_id),
                    )
                )

    risk_group_summaries = sidecar.metrics.get("risk_group_summaries")
    if not isinstance(risk_group_summaries, list) or not risk_group_summaries:
        issues.append(
            _issue(
                rule_id="risk_group_summaries_missing",
                message="threshold governance qc requires non-empty risk_group_summaries metrics",
                target="metrics.risk_group_summaries",
            )
        )
        return issues

    previous_group_order = 0.0
    for index, item in enumerate(risk_group_summaries):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.risk_group_summaries[{index}] must be an object")
        group_label = str(item.get("group_label") or "").strip()
        group_order = _require_numeric(
            item.get("group_order"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].group_order",
        )
        n = _require_numeric(
            item.get("n"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].n",
        )
        events = _require_numeric(
            item.get("events"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].events",
        )
        predicted_risk = _require_numeric(
            item.get("predicted_risk"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].predicted_risk",
        )
        observed_risk = _require_numeric(
            item.get("observed_risk"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].observed_risk",
        )
        predicted_x = _require_numeric(
            item.get("predicted_x"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].predicted_x",
        )
        observed_x = _require_numeric(
            item.get("observed_x"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].observed_x",
        )
        y = _require_numeric(
            item.get("y"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].y",
        )
        if not group_label:
            issues.append(
                _issue(
                    rule_id="risk_group_label_missing",
                    message="risk-group labels must be non-empty",
                    target=f"metrics.risk_group_summaries[{index}].group_label",
                )
            )
        if group_order <= previous_group_order:
            issues.append(
                _issue(
                    rule_id="risk_group_order_not_increasing",
                    message="risk-group order must stay strictly increasing",
                    target="metrics.risk_group_summaries",
                )
            )
        previous_group_order = group_order
        if n <= 0:
            issues.append(
                _issue(
                    rule_id="risk_group_size_non_positive",
                    message="risk-group n must be positive",
                    target=f"metrics.risk_group_summaries[{index}].n",
                )
            )
        if events < 0 or events > n:
            issues.append(
                _issue(
                    rule_id="risk_group_events_invalid",
                    message="risk-group events must stay between 0 and n",
                    target=f"metrics.risk_group_summaries[{index}].events",
                    observed=events,
                    expected={"minimum": 0, "maximum": n},
                )
            )
        for field_name, value in (("predicted_risk", predicted_risk), ("observed_risk", observed_risk)):
            if 0.0 <= value <= 1.0:
                continue
            issues.append(
                _issue(
                    rule_id=f"{field_name}_out_of_range",
                    message=f"{field_name} must stay within [0, 1]",
                    target=f"metrics.risk_group_summaries[{index}].{field_name}",
                    observed=value,
                )
            )
        if calibration_panel is not None:
            if not _point_within_box(calibration_panel, x=predicted_x, y=y):
                issues.append(
                    _issue(
                        rule_id="calibration_point_outside_panel",
                        message="predicted calibration point must stay within calibration_panel",
                        target=f"metrics.risk_group_summaries[{index}].predicted_x",
                        observed={"x": predicted_x, "y": y},
                        box_refs=(calibration_panel.box_id,),
                    )
                )
            if not _point_within_box(calibration_panel, x=observed_x, y=y):
                issues.append(
                    _issue(
                        rule_id="calibration_point_outside_panel",
                        message="observed calibration point must stay within calibration_panel",
                        target=f"metrics.risk_group_summaries[{index}].observed_x",
                        observed={"x": observed_x, "y": y},
                        box_refs=(calibration_panel.box_id,),
                    )
                )

    return issues


def _check_publication_time_to_event_multihorizon_calibration_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    required_box_types = ["panel_title", "panel_label", "subplot_x_axis_title", "legend"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box for box in sidecar.layout_boxes if box.box_type in {"title", "panel_title", "panel_label", "subplot_x_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))

    panel_metrics = sidecar.metrics.get("panels")
    if not isinstance(panel_metrics, list) or not panel_metrics:
        issues.append(
            _issue(
                rule_id="panel_metrics_missing",
                message="multihorizon calibration qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues
    calibration_panels = _boxes_of_type(sidecar.panel_boxes, "calibration_panel")
    if len(calibration_panels) != len(panel_metrics):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="multihorizon calibration panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(calibration_panels)},
                expected={"metrics.panels": len(panel_metrics)},
            )
        )
    label_panel_map: dict[str, str] = {}
    previous_horizon = 0.0
    for panel_index, item in enumerate(panel_metrics):
        if not isinstance(item, dict):
            raise ValueError(f"metrics.panels[{panel_index}] must be an object")
        panel_label = str(item.get("panel_label") or "").strip()
        panel_title = str(item.get("title") or "").strip()
        panel_id = str(item.get("panel_id") or "").strip()
        if panel_label:
            label_panel_map[f"panel_label_{_panel_label_token(panel_label)}"] = f"panel_{_panel_label_token(panel_label)}"
        if not panel_id or not panel_label or not panel_title:
            issues.append(
                _issue(
                    rule_id="panel_metadata_missing",
                    message="multihorizon calibration panels must declare panel_id, panel_label, and title",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
        time_horizon_months = _require_numeric(
            item.get("time_horizon_months"),
            label=f"metrics.panels[{panel_index}].time_horizon_months",
        )
        if time_horizon_months <= 0:
            issues.append(
                _issue(
                    rule_id="time_horizon_non_positive",
                    message="time_horizon_months must stay positive",
                    target=f"metrics.panels[{panel_index}].time_horizon_months",
                )
            )
        if time_horizon_months <= previous_horizon:
            issues.append(
                _issue(
                    rule_id="time_horizon_not_increasing",
                    message="time_horizon_months must stay strictly increasing across panels",
                    target="metrics.panels",
                )
            )
        previous_horizon = time_horizon_months

        calibration_summary = item.get("calibration_summary")
        if not isinstance(calibration_summary, list) or not calibration_summary:
            issues.append(
                _issue(
                    rule_id="calibration_summary_missing",
                    message="every multihorizon calibration panel requires non-empty calibration_summary",
                    target=f"metrics.panels[{panel_index}].calibration_summary",
                )
            )
            continue
        target_panel = next(
            (box for box in calibration_panels if box.box_id == f"panel_{_panel_label_token(panel_label)}"),
            None,
        )
        previous_group_order = 0.0
        for group_index, summary in enumerate(calibration_summary):
            if not isinstance(summary, dict):
                raise ValueError(f"metrics.panels[{panel_index}].calibration_summary[{group_index}] must be an object")
            group_label = str(summary.get("group_label") or "").strip()
            group_order = _require_numeric(
                summary.get("group_order"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].group_order",
            )
            n = _require_numeric(
                summary.get("n"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].n",
            )
            events = _require_numeric(
                summary.get("events"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].events",
            )
            predicted_risk = _require_numeric(
                summary.get("predicted_risk"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].predicted_risk",
            )
            observed_risk = _require_numeric(
                summary.get("observed_risk"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].observed_risk",
            )
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="group_label_missing",
                        message="multihorizon calibration groups require non-empty labels",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].group_label",
                    )
                )
            if group_order <= previous_group_order:
                issues.append(
                    _issue(
                        rule_id="group_order_not_increasing",
                        message="calibration group_order must stay strictly increasing within each panel",
                        target=f"metrics.panels[{panel_index}].calibration_summary",
                    )
                )
            previous_group_order = group_order
            if n <= 0:
                issues.append(
                    _issue(
                        rule_id="group_size_non_positive",
                        message="calibration group size n must be positive",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].n",
                    )
                )
            if events < 0 or events > n:
                issues.append(
                    _issue(
                        rule_id="events_invalid",
                        message="calibration events must stay between 0 and n",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].events",
                        observed=events,
                        expected={"minimum": 0, "maximum": n},
                    )
                )
            for field_name, value in (("predicted_risk", predicted_risk), ("observed_risk", observed_risk)):
                if 0.0 <= value <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id=f"{field_name}_out_of_range",
                        message=f"{field_name} must stay within [0, 1]",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].{field_name}",
                        observed=value,
                    )
                )
            if target_panel is None:
                continue
            predicted_x = _require_numeric(
                summary.get("predicted_x"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].predicted_x",
            )
            observed_x = _require_numeric(
                summary.get("observed_x"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].observed_x",
            )
            y = _require_numeric(
                summary.get("y"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].y",
            )
            if not _point_within_box(target_panel, x=predicted_x, y=y):
                issues.append(
                    _issue(
                        rule_id="calibration_point_outside_panel",
                        message="predicted calibration point must stay within its panel",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].predicted_x",
                        observed={"x": predicted_x, "y": y},
                        box_refs=(target_panel.box_id,),
                    )
                )
            if not _point_within_box(target_panel, x=observed_x, y=y):
                issues.append(
                    _issue(
                        rule_id="calibration_point_outside_panel",
                        message="observed calibration point must stay within its panel",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].observed_x",
                        observed={"x": observed_x, "y": y},
                        box_refs=(target_panel.box_id,),
                    )
                )

    issues.extend(_check_composite_panel_label_anchors(sidecar, label_panel_map=label_panel_map))
    return issues


def _check_publication_multicenter_overview(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(_all_boxes(sidecar), required_box_types=("y_axis_title", "coverage_bar")))
    issues.extend(_check_legend_panel_overlap(sidecar))
    legend = _first_box_of_type(sidecar.guide_boxes, "legend")
    if legend is None:
        issues.append(
            _issue(
                rule_id="missing_legend",
                message="multicenter overview requires a split legend in the footer band",
                target="legend",
                expected="present",
            )
        )
    elif sidecar.panel_boxes:
        footer_ceiling = min(panel_box.y0 for panel_box in sidecar.panel_boxes)
        if legend.y1 > footer_ceiling - 0.005:
            issues.append(
                _issue(
                    rule_id="legend_footer_band_drift",
                    message="multicenter legend must stay below the panel band in the footer region",
                    target="legend",
                    box_refs=(legend.box_id,),
                    observed={"legend_y1": legend.y1},
                    expected={"maximum_y1": footer_ceiling - 0.005},
                )
            )
    legend_title = str(sidecar.metrics.get("legend_title") or "").strip()
    if legend_title != "Split":
        issues.append(
            _issue(
                rule_id="legend_title_invalid",
                message="multicenter overview legend title must stay `Split`",
                target="metrics.legend_title",
                observed=legend_title,
                expected="Split",
            )
        )
    legend_labels = sidecar.metrics.get("legend_labels")
    if not isinstance(legend_labels, list) or not legend_labels:
        issues.append(
            _issue(
                rule_id="legend_labels_missing",
                message="multicenter overview requires explicit legend labels for split semantics",
                target="metrics.legend_labels",
                expected=["Train", "Validation"],
            )
        )
    else:
        normalized_labels = [str(item or "").strip() for item in legend_labels]
        if normalized_labels != ["Train", "Validation"]:
            issues.append(
                _issue(
                    rule_id="legend_labels_invalid",
                    message="multicenter overview legend labels must stay in `Train`, `Validation` order",
                    target="metrics.legend_labels",
                    observed=normalized_labels,
                    expected=["Train", "Validation"],
                )
            )

    center_event_panel = _first_box_of_type(sidecar.panel_boxes, "center_event_panel")
    if center_event_panel is None:
        issues.append(
            _issue(
                rule_id="center_event_panel_missing",
                message="multicenter overview requires the center-event panel",
                target="panel_boxes",
                expected="center_event_panel",
            )
        )

    coverage_panels_by_box_id = {box.box_id for box in _boxes_of_type(sidecar.panel_boxes, "coverage_panel")}
    required_coverage_box_ids = {
        "coverage_panel_wide_left",
        "coverage_panel_top_right",
        "coverage_panel_bottom_right",
    }
    for missing_box_id in sorted(required_coverage_box_ids - coverage_panels_by_box_id):
        issues.append(
            _issue(
                rule_id="coverage_panel_missing",
                message="multicenter overview requires all three coverage panel regions",
                target="panel_boxes",
                expected=missing_box_id,
            )
        )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    panel_labels = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "panel_label")}
    required_panel_labels = {
        "panel_label_A": "center_event_panel",
        "panel_label_B": "coverage_panel_wide_left",
        "panel_label_C": "coverage_panel_right_stack",
    }
    for label_box_id, panel_box_id in required_panel_labels.items():
        label_box = panel_labels.get(label_box_id)
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="missing_panel_label",
                    message="multicenter overview requires explicit A/B/C panel labels",
                    target="layout_boxes",
                    expected=label_box_id,
                )
            )
            continue
        parent_panel = panel_boxes_by_id.get(panel_box_id)
        if parent_panel is None and panel_box_id == "coverage_panel_right_stack":
            parent_panel = panel_boxes_by_id.get("coverage_panel_top_right")
        if parent_panel is None:
            continue
        if not _box_within_box(label_box, parent_panel):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="multicenter panel labels must stay within their declared panel region",
                    target="panel_label",
                    box_refs=(label_box.box_id, parent_panel.box_id),
                )
            )
            continue
        panel_width = max(parent_panel.x1 - parent_panel.x0, 1e-9)
        panel_height = max(parent_panel.y1 - parent_panel.y0, 1e-9)
        if (
            label_box.x0 > parent_panel.x0 + panel_width * 0.18
            or label_box.y1 < parent_panel.y1 - panel_height * 0.18
        ):
            issues.append(
                _issue(
                    rule_id="panel_label_anchor_drift",
                    message="multicenter panel labels must stay near the parent panel top-left anchor",
                    target="panel_label",
                    box_refs=(label_box.box_id, parent_panel.box_id),
                )
            )

    center_event_counts = sidecar.metrics.get("center_event_counts")
    if not isinstance(center_event_counts, list) or not center_event_counts:
        issues.append(
            _issue(
                rule_id="center_event_counts_missing",
                message="multicenter overview requires non-empty center_event_counts metrics",
                target="metrics.center_event_counts",
            )
        )
    else:
        seen_labels: set[str] = set()
        for index, item in enumerate(center_event_counts):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.center_event_counts[{index}] must be an object")
            label = str(item.get("center_label") or "").strip()
            if not label:
                raise ValueError(f"layout_sidecar.metrics.center_event_counts[{index}].center_label must be non-empty")
            if label in seen_labels:
                issues.append(
                    _issue(
                        rule_id="center_event_label_not_unique",
                        message="center-event labels must be unique",
                        target=f"metrics.center_event_counts[{index}]",
                        observed=label,
                    )
                )
            seen_labels.add(label)
            event_count = _require_numeric(
                item.get("event_count"),
                label=f"layout_sidecar.metrics.center_event_counts[{index}].event_count",
            )
            if event_count < 0:
                issues.append(
                    _issue(
                        rule_id="center_event_count_negative",
                        message="center-event counts must be non-negative",
                        target=f"metrics.center_event_counts[{index}]",
                        observed=event_count,
                    )
                )

    coverage_panels = sidecar.metrics.get("coverage_panels")
    if not isinstance(coverage_panels, list) or not coverage_panels:
        issues.append(
            _issue(
                rule_id="coverage_panels_missing",
                message="multicenter overview requires coverage_panels metrics",
                target="metrics.coverage_panels",
            )
        )
        return issues

    seen_panel_ids: set[str] = set()
    seen_layout_roles: set[str] = set()
    for index, panel in enumerate(coverage_panels):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.coverage_panels[{index}] must be an object")
        panel_id = str(panel.get("panel_id") or "").strip()
        if not panel_id:
            raise ValueError(f"layout_sidecar.metrics.coverage_panels[{index}].panel_id must be non-empty")
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="coverage_panel_id_not_unique",
                    message="coverage panel ids must be unique",
                    target=f"metrics.coverage_panels[{index}]",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)
        layout_role = str(panel.get("layout_role") or "").strip()
        if not layout_role:
            raise ValueError(f"layout_sidecar.metrics.coverage_panels[{index}].layout_role must be non-empty")
        seen_layout_roles.add(layout_role)
        bars = panel.get("bars")
        if not isinstance(bars, list) or not bars:
            issues.append(
                _issue(
                    rule_id="coverage_panel_bars_missing",
                    message="coverage panels must contain at least one bar",
                    target=f"metrics.coverage_panels[{index}].bars",
                )
            )
            continue
        for bar_index, bar in enumerate(bars):
            if not isinstance(bar, dict):
                raise ValueError(f"layout_sidecar.metrics.coverage_panels[{index}].bars[{bar_index}] must be an object")
            count = _require_numeric(
                bar.get("count"),
                label=f"layout_sidecar.metrics.coverage_panels[{index}].bars[{bar_index}].count",
            )
            if count < 0:
                issues.append(
                    _issue(
                        rule_id="coverage_bar_count_negative",
                        message="coverage bar counts must be non-negative",
                        target=f"metrics.coverage_panels[{index}].bars[{bar_index}]",
                        observed=count,
                    )
                )

    required_layout_roles = {"wide_left", "top_right", "bottom_right"}
    for missing_role in sorted(required_layout_roles - seen_layout_roles):
        issues.append(
            _issue(
                rule_id="coverage_panel_layout_role_missing",
                message="multicenter overview requires wide_left, top_right, and bottom_right coverage panels",
                target="metrics.coverage_panels",
                expected=missing_role,
            )
        )

    return issues


def _check_publication_shap_summary(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["zero_line", "colorbar", "x_axis_title", "feature_row"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(2, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    row_boxes = _boxes_of_type(sidecar.layout_boxes + sidecar.panel_boxes, "feature_row")
    issues.extend(_check_pairwise_non_overlap(row_boxes, rule_id="feature_row_overlap", target="feature_row"))
    feature_label_boxes = _boxes_of_type(sidecar.layout_boxes + sidecar.panel_boxes, "feature_label")
    issues.extend(_check_pairwise_non_overlap(feature_label_boxes, rule_id="feature_label_overlap", target="feature_label"))

    critical_boxes = tuple(
        box for box in all_boxes if box.box_type in {"title", "x_axis_title", "colorbar"}
    )
    issues.extend(_check_pairwise_non_overlap(critical_boxes, rule_id="critical_box_overlap", target="critical_boxes"))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    panel = _primary_panel(sidecar)
    zero_line = _first_box_of_type(sidecar.guide_boxes, "zero_line")
    if panel is not None and zero_line is not None and not _box_within_box(zero_line, panel):
        issues.append(
            _issue(
                rule_id="zero_line_outside_panel",
                message="zero-reference guide must stay within the shap panel region",
                target="guide_boxes.zero_line",
                box_refs=(zero_line.box_id, panel.box_id),
            )
        )
    if panel is not None:
        for row_box in row_boxes:
            if panel.y0 <= row_box.y0 <= panel.y1 and panel.y0 <= row_box.y1 <= panel.y1:
                continue
            issues.append(
                _issue(
                    rule_id="feature_row_outside_panel",
                    message="feature-row band must stay within the shap panel region",
                    target=f"layout_boxes.{row_box.box_id}",
                    box_refs=(row_box.box_id, panel.box_id),
                )
            )

    row_box_by_id = {box.box_id: box for box in row_boxes}
    points = sidecar.metrics.get("points")
    if points is None:
        return issues
    if not isinstance(points, list):
        raise ValueError("layout_sidecar.metrics.points must be a list when present")
    for index, point in enumerate(points):
        if not isinstance(point, dict):
            raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
        row_box_id = str(point.get("row_box_id") or "").strip()
        if not row_box_id:
            continue
        row_box = row_box_by_id.get(row_box_id)
        if row_box is None:
            continue
        y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
        x_value = _require_numeric(point.get("x", row_box.x0), label=f"layout_sidecar.metrics.points[{index}].x")
        if _point_within_box(row_box, x=x_value, y=y_value):
            continue
        issues.append(
            _issue(
                rule_id="point_outside_feature_row",
                message="shap point must stay within its assigned feature row box",
                target=f"metrics.points[{index}]",
                observed={"x": x_value, "y": y_value},
                box_refs=(row_box.box_id,),
            )
        )

    label_box_by_id = {box.box_id: box for box in feature_label_boxes}
    raw_feature_labels = sidecar.metrics.get("feature_labels")
    if raw_feature_labels is None:
        raw_feature_labels = []
    if not isinstance(raw_feature_labels, list):
        raise ValueError("layout_sidecar.metrics.feature_labels must be a list when present")
    label_entry_by_row_box_id: dict[str, dict[str, str]] = {}
    for index, item in enumerate(raw_feature_labels):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.feature_labels[{index}] must be an object")
        row_box_id = str(item.get("row_box_id") or "").strip()
        label_box_id = str(item.get("label_box_id") or "").strip()
        if not row_box_id or not label_box_id:
            raise ValueError(
                f"layout_sidecar.metrics.feature_labels[{index}] must include row_box_id and label_box_id"
            )
        label_entry_by_row_box_id[row_box_id] = {
            "label_box_id": label_box_id,
            "feature": str(item.get("feature") or "").strip(),
        }

    for row_box in row_boxes:
        label_entry = label_entry_by_row_box_id.get(row_box.box_id)
        if label_entry is None:
            issues.append(
                _issue(
                    rule_id="feature_label_missing",
                    message="shap summary requires a feature label annotation for every feature row",
                    target=f"metrics.feature_labels.{row_box.box_id}",
                    box_refs=(row_box.box_id,),
                )
            )
            continue
        label_box = label_box_by_id.get(label_entry["label_box_id"])
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="feature_label_missing",
                    message="feature label annotation must reference an existing feature_label box",
                    target=f"metrics.feature_labels.{row_box.box_id}",
                    observed={"label_box_id": label_entry["label_box_id"]},
                    box_refs=(row_box.box_id,),
                )
            )
            continue
        if panel is not None and _boxes_overlap(label_box, panel):
            issues.append(
                _issue(
                    rule_id="feature_label_panel_overlap",
                    message="feature label annotation must stay outside the shap panel region",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(row_box.box_id, label_box.box_id, panel.box_id),
                )
            )
        label_center_y = (label_box.y0 + label_box.y1) / 2.0
        if row_box.y0 <= label_center_y <= row_box.y1:
            continue
        issues.append(
            _issue(
                rule_id="feature_label_row_misaligned",
                message="feature label annotation must stay vertically aligned to its feature row band",
                target=f"layout_boxes.{label_box.box_id}",
                observed={"label_center_y": label_center_y},
                expected={"row_y0": row_box.y0, "row_y1": row_box.y1},
                box_refs=(row_box.box_id, label_box.box_id),
            )
        )
    return issues


def _check_publication_shap_bar_importance(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["x_axis_title", "feature_label", "importance_bar", "value_label"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))

    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "x_axis_title", "feature_label", "value_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    panel = _primary_panel(sidecar)
    if panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="shap bar importance qc requires a primary panel box",
                target="panel_boxes",
            )
        )
        return issues

    metrics_bars = sidecar.metrics.get("bars")
    if not isinstance(metrics_bars, list) or not metrics_bars:
        issues.append(
            _issue(
                rule_id="bars_missing",
                message="shap bar importance qc requires non-empty bar metrics",
                target="metrics.bars",
            )
        )
        return issues

    bar_box_by_id = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "importance_bar")}
    feature_label_box_by_id = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "feature_label")}
    value_label_box_by_id = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "value_label")}

    previous_rank = 0
    previous_importance = float("inf")
    seen_features: set[str] = set()
    for index, item in enumerate(metrics_bars):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.bars[{index}] must be an object")
        rank_value = _require_numeric(item.get("rank"), label=f"layout_sidecar.metrics.bars[{index}].rank")
        if not math.isclose(rank_value, round(rank_value), rel_tol=0.0, abs_tol=1e-9) or rank_value <= 0.0:
            raise ValueError(f"layout_sidecar.metrics.bars[{index}].rank must be a positive integer")
        rank = int(round(rank_value))
        if rank <= previous_rank:
            issues.append(
                _issue(
                    rule_id="importance_rank_not_increasing",
                    message="shap bar importance ranks must be strictly increasing",
                    target=f"metrics.bars[{index}].rank",
                    observed=rank,
                )
            )
        previous_rank = rank
        feature = _require_non_empty_text(
            item.get("feature"),
            label=f"layout_sidecar.metrics.bars[{index}].feature",
        )
        if feature in seen_features:
            issues.append(
                _issue(
                    rule_id="importance_feature_duplicate",
                    message="shap bar importance features must be unique",
                    target=f"metrics.bars[{index}].feature",
                    observed=feature,
                )
            )
        seen_features.add(feature)
        importance_value = _require_numeric(item.get("importance_value"), label=f"layout_sidecar.metrics.bars[{index}].importance_value")
        if importance_value < 0.0:
            issues.append(
                _issue(
                    rule_id="importance_value_negative",
                    message="shap bar importance values must be non-negative",
                    target=f"metrics.bars[{index}].importance_value",
                    observed=importance_value,
                )
            )
        if importance_value > previous_importance + 1e-12:
            issues.append(
                _issue(
                    rule_id="importance_not_descending",
                    message="shap bar importance values must stay sorted descending by rank",
                    target=f"metrics.bars[{index}].importance_value",
                    observed=importance_value,
                )
            )
        previous_importance = importance_value

        bar_box_id = _require_non_empty_text(
            item.get("bar_box_id"),
            label=f"layout_sidecar.metrics.bars[{index}].bar_box_id",
        )
        feature_label_box_id = _require_non_empty_text(
            item.get("feature_label_box_id"),
            label=f"layout_sidecar.metrics.bars[{index}].feature_label_box_id",
        )
        value_label_box_id = _require_non_empty_text(
            item.get("value_label_box_id"),
            label=f"layout_sidecar.metrics.bars[{index}].value_label_box_id",
        )
        bar_box = bar_box_by_id.get(bar_box_id)
        feature_label_box = feature_label_box_by_id.get(feature_label_box_id)
        value_label_box = value_label_box_by_id.get(value_label_box_id)
        if bar_box is None:
            issues.append(
                _issue(
                    rule_id="importance_bar_missing",
                    message="shap bar importance metrics must reference an existing importance_bar box",
                    target=f"metrics.bars[{index}].bar_box_id",
                    observed=bar_box_id,
                )
            )
            continue
        if not _box_within_box(bar_box, panel):
            issues.append(
                _issue(
                    rule_id="importance_bar_outside_panel",
                    message="shap bar importance bars must stay within the declared panel region",
                    target=f"layout_boxes.{bar_box.box_id}",
                    box_refs=(bar_box.box_id, panel.box_id),
                )
            )
        if feature_label_box is None:
            issues.append(
                _issue(
                    rule_id="feature_label_missing",
                    message="shap bar importance metrics must reference an existing feature_label box",
                    target=f"metrics.bars[{index}].feature_label_box_id",
                    observed=feature_label_box_id,
                )
            )
        elif _boxes_overlap(feature_label_box, panel):
            issues.append(
                _issue(
                    rule_id="feature_label_panel_overlap",
                    message="feature labels must stay outside the shap bar importance panel",
                    target=f"layout_boxes.{feature_label_box.box_id}",
                    box_refs=(feature_label_box.box_id, panel.box_id),
                )
            )
        if value_label_box is None:
            issues.append(
                _issue(
                    rule_id="value_label_missing",
                    message="shap bar importance metrics must reference an existing value_label box",
                    target=f"metrics.bars[{index}].value_label_box_id",
                    observed=value_label_box_id,
                )
            )

    return issues


def _check_publication_shap_signed_importance_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "negative_direction_label",
        "positive_direction_label",
        "x_axis_title",
        "feature_label",
        "importance_bar",
        "value_label",
        "zero_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))

    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {"title", "negative_direction_label", "positive_direction_label", "x_axis_title", "feature_label", "value_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    panel = _primary_panel(sidecar)
    if panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="shap signed importance qc requires a primary panel box",
                target="panel_boxes",
            )
        )
        return issues

    zero_line = _first_box_of_type(sidecar.guide_boxes, "zero_line")
    if zero_line is None:
        issues.append(
            _issue(
                rule_id="zero_line_missing",
                message="shap signed importance qc requires a zero_line guide box",
                target="guide_boxes.zero_line",
            )
        )
        return issues
    if not _box_within_box(zero_line, panel):
        issues.append(
            _issue(
                rule_id="zero_line_outside_panel",
                message="shap signed importance zero line must stay within the declared panel region",
                target="guide_boxes.zero_line",
                box_refs=(zero_line.box_id, panel.box_id),
            )
        )
    zero_mid_x = (zero_line.x0 + zero_line.x1) / 2.0
    tolerance = max((zero_line.x1 - zero_line.x0) / 2.0, 0.0025)

    metrics_bars = sidecar.metrics.get("bars")
    if not isinstance(metrics_bars, list) or not metrics_bars:
        issues.append(
            _issue(
                rule_id="bars_missing",
                message="shap signed importance qc requires non-empty bar metrics",
                target="metrics.bars",
            )
        )
        return issues

    bar_box_by_id = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "importance_bar")}
    feature_label_box_by_id = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "feature_label")}
    value_label_box_by_id = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "value_label")}

    previous_rank = 0
    previous_absolute_value = float("inf")
    seen_features: set[str] = set()
    for index, item in enumerate(metrics_bars):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.bars[{index}] must be an object")
        rank_value = _require_numeric(item.get("rank"), label=f"layout_sidecar.metrics.bars[{index}].rank")
        if not math.isclose(rank_value, round(rank_value), rel_tol=0.0, abs_tol=1e-9) or rank_value <= 0.0:
            raise ValueError(f"layout_sidecar.metrics.bars[{index}].rank must be a positive integer")
        rank = int(round(rank_value))
        if rank <= previous_rank:
            issues.append(
                _issue(
                    rule_id="signed_importance_rank_not_increasing",
                    message="shap signed importance ranks must be strictly increasing",
                    target=f"metrics.bars[{index}].rank",
                    observed=rank,
                )
            )
        previous_rank = rank

        feature = _require_non_empty_text(
            item.get("feature"),
            label=f"layout_sidecar.metrics.bars[{index}].feature",
        )
        if feature in seen_features:
            issues.append(
                _issue(
                    rule_id="signed_importance_feature_duplicate",
                    message="shap signed importance features must be unique",
                    target=f"metrics.bars[{index}].feature",
                    observed=feature,
                )
            )
        seen_features.add(feature)

        direction = _require_non_empty_text(
            item.get("direction"),
            label=f"layout_sidecar.metrics.bars[{index}].direction",
        )
        if direction not in {"negative", "positive"}:
            raise ValueError(f"layout_sidecar.metrics.bars[{index}].direction must be `negative` or `positive`")

        signed_importance_value = _require_numeric(
            item.get("signed_importance_value"),
            label=f"layout_sidecar.metrics.bars[{index}].signed_importance_value",
        )
        if not math.isfinite(signed_importance_value) or math.isclose(
            signed_importance_value,
            0.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            issues.append(
                _issue(
                    rule_id="signed_importance_value_invalid",
                    message="shap signed importance values must be finite and non-zero",
                    target=f"metrics.bars[{index}].signed_importance_value",
                    observed=signed_importance_value,
                )
            )
        absolute_value = abs(signed_importance_value)
        if absolute_value > previous_absolute_value + 1e-12:
            issues.append(
                _issue(
                    rule_id="signed_importance_not_sorted_by_absolute_magnitude",
                    message="shap signed importance values must stay sorted by descending absolute magnitude",
                    target=f"metrics.bars[{index}].signed_importance_value",
                    observed=signed_importance_value,
                )
            )
        previous_absolute_value = absolute_value

        expected_direction = "positive" if signed_importance_value > 0.0 else "negative"
        if direction != expected_direction:
            issues.append(
                _issue(
                    rule_id="signed_importance_direction_mismatch",
                    message="shap signed importance direction must match the sign of signed_importance_value",
                    target=f"metrics.bars[{index}].direction",
                    observed=direction,
                    expected={"direction": expected_direction},
                )
            )

        bar_box_id = _require_non_empty_text(
            item.get("bar_box_id"),
            label=f"layout_sidecar.metrics.bars[{index}].bar_box_id",
        )
        feature_label_box_id = _require_non_empty_text(
            item.get("feature_label_box_id"),
            label=f"layout_sidecar.metrics.bars[{index}].feature_label_box_id",
        )
        value_label_box_id = _require_non_empty_text(
            item.get("value_label_box_id"),
            label=f"layout_sidecar.metrics.bars[{index}].value_label_box_id",
        )
        bar_box = bar_box_by_id.get(bar_box_id)
        feature_label_box = feature_label_box_by_id.get(feature_label_box_id)
        value_label_box = value_label_box_by_id.get(value_label_box_id)
        if bar_box is None:
            issues.append(
                _issue(
                    rule_id="signed_importance_bar_missing",
                    message="shap signed importance metrics must reference an existing importance_bar box",
                    target=f"metrics.bars[{index}].bar_box_id",
                    observed=bar_box_id,
                )
            )
            continue
        if not _box_within_box(bar_box, panel):
            issues.append(
                _issue(
                    rule_id="importance_bar_outside_panel",
                    message="shap signed importance bars must stay within the declared panel region",
                    target=f"layout_boxes.{bar_box.box_id}",
                    box_refs=(bar_box.box_id, panel.box_id),
                )
            )
        elif direction == "negative" and bar_box.x1 > zero_mid_x + tolerance:
            issues.append(
                _issue(
                    rule_id="signed_importance_bar_wrong_side_of_zero",
                    message="negative shap signed importance bars must stay on the left side of the zero line",
                    target=f"layout_boxes.{bar_box.box_id}",
                    box_refs=(bar_box.box_id, zero_line.box_id),
                )
            )
        elif direction == "positive" and bar_box.x0 < zero_mid_x - tolerance:
            issues.append(
                _issue(
                    rule_id="signed_importance_bar_wrong_side_of_zero",
                    message="positive shap signed importance bars must stay on the right side of the zero line",
                    target=f"layout_boxes.{bar_box.box_id}",
                    box_refs=(bar_box.box_id, zero_line.box_id),
                )
            )

        if feature_label_box is None:
            issues.append(
                _issue(
                    rule_id="feature_label_missing",
                    message="shap signed importance metrics must reference an existing feature_label box",
                    target=f"metrics.bars[{index}].feature_label_box_id",
                    observed=feature_label_box_id,
                )
            )
        elif _boxes_overlap(feature_label_box, panel):
            issues.append(
                _issue(
                    rule_id="feature_label_panel_overlap",
                    message="feature labels must stay outside the shap signed importance panel",
                    target=f"layout_boxes.{feature_label_box.box_id}",
                    box_refs=(feature_label_box.box_id, panel.box_id),
                )
            )

        if value_label_box is None:
            issues.append(
                _issue(
                    rule_id="value_label_missing",
                    message="shap signed importance metrics must reference an existing value_label box",
                    target=f"metrics.bars[{index}].value_label_box_id",
                    observed=value_label_box_id,
                )
            )

    return issues


def _check_publication_shap_multicohort_importance_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_label",
        "panel_title",
        "subplot_x_axis_title",
        "feature_label",
        "importance_bar",
        "value_label",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_label", "panel_title", "subplot_x_axis_title", "feature_label", "value_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="shap multicohort importance qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap multicohort importance panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}
    expected_feature_order: tuple[str, ...] | None = None

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        cohort_label = str(panel_metric.get("cohort_label") or "").strip()
        if not panel_id or not panel_label or not title or not cohort_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="shap multicohort importance panel metrics must declare panel metadata and cohort labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None and panel_index < len(panel_boxes):
            panel_box = panel_boxes[panel_index]
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="shap multicohort importance metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue

        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        panel_title_box_id = str(panel_metric.get("panel_title_box_id") or "").strip() or f"panel_title_{panel_label}"
        if panel_title_box_id not in layout_box_by_id:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="shap multicohort importance requires an explicit panel title per cohort panel",
                    target=f"metrics.panels[{panel_index}].panel_title_box_id",
                    observed={"panel_title_box_id": panel_title_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )

        x_axis_title_box_id = str(panel_metric.get("x_axis_title_box_id") or "").strip() or f"x_axis_title_{panel_label}"
        if x_axis_title_box_id not in layout_box_by_id:
            issues.append(
                _issue(
                    rule_id="x_axis_title_missing",
                    message="shap multicohort importance requires a subplot x-axis title per cohort panel",
                    target=f"metrics.panels[{panel_index}].x_axis_title_box_id",
                    observed={"x_axis_title_box_id": x_axis_title_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )

        bars = panel_metric.get("bars")
        if not isinstance(bars, list) or not bars:
            issues.append(
                _issue(
                    rule_id="bars_missing",
                    message="shap multicohort importance panel metrics must contain non-empty bars",
                    target=f"metrics.panels[{panel_index}].bars",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        previous_rank = 0
        previous_importance = float("inf")
        seen_features: set[str] = set()
        feature_order: list[str] = []
        for bar_index, item in enumerate(bars):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}] must be an object")
            rank_value = _require_numeric(
                item.get("rank"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].rank",
            )
            if not math.isclose(rank_value, round(rank_value), rel_tol=0.0, abs_tol=1e-9) or rank_value <= 0.0:
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].rank must be a positive integer"
                )
            rank = int(round(rank_value))
            if rank <= previous_rank:
                issues.append(
                    _issue(
                        rule_id="multicohort_rank_not_increasing",
                        message="shap multicohort importance ranks must be strictly increasing within each panel",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].rank",
                        observed=rank,
                    )
                )
            previous_rank = rank

            feature = _require_non_empty_text(
                item.get("feature"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].feature",
            )
            if feature in seen_features:
                issues.append(
                    _issue(
                        rule_id="multicohort_feature_duplicate",
                        message="shap multicohort importance features must be unique within each cohort panel",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].feature",
                        observed=feature,
                    )
                )
            seen_features.add(feature)
            feature_order.append(feature)

            importance_value = _require_numeric(
                item.get("importance_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].importance_value",
            )
            if importance_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="multicohort_importance_negative",
                        message="shap multicohort importance values must be non-negative",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].importance_value",
                        observed=importance_value,
                    )
                )
            if importance_value > previous_importance + 1e-12:
                issues.append(
                    _issue(
                        rule_id="multicohort_importance_not_descending",
                        message="shap multicohort importance values must stay sorted descending by rank",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].importance_value",
                        observed=importance_value,
                    )
                )
            previous_importance = importance_value

            bar_box_id = _require_non_empty_text(
                item.get("bar_box_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].bar_box_id",
            )
            feature_label_box_id = _require_non_empty_text(
                item.get("feature_label_box_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].feature_label_box_id",
            )
            value_label_box_id = _require_non_empty_text(
                item.get("value_label_box_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].value_label_box_id",
            )

            bar_box = layout_box_by_id.get(bar_box_id)
            feature_label_box = layout_box_by_id.get(feature_label_box_id)
            value_label_box = layout_box_by_id.get(value_label_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="importance_bar_missing",
                        message="shap multicohort importance metrics must reference an existing importance_bar box",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
                continue
            if not _box_within_box(bar_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="importance_bar_outside_panel",
                        message="shap multicohort importance bars must stay within their declared panel region",
                        target=f"layout_boxes.{bar_box.box_id}",
                        box_refs=(bar_box.box_id, panel_box.box_id),
                    )
                )
            if feature_label_box is None:
                issues.append(
                    _issue(
                        rule_id="feature_label_missing",
                        message="shap multicohort importance metrics must reference an existing feature_label box",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].feature_label_box_id",
                        observed=feature_label_box_id,
                    )
                )
            else:
                if _boxes_overlap(feature_label_box, panel_box):
                    issues.append(
                        _issue(
                            rule_id="feature_label_panel_overlap",
                            message="feature labels must stay outside each shap multicohort panel",
                            target=f"layout_boxes.{feature_label_box.box_id}",
                            box_refs=(feature_label_box.box_id, panel_box.box_id),
                        )
                    )
                label_center_y = (feature_label_box.y0 + feature_label_box.y1) / 2.0
                if not (bar_box.y0 <= label_center_y <= bar_box.y1):
                    issues.append(
                        _issue(
                            rule_id="feature_label_row_misaligned",
                            message="feature label annotation must stay vertically aligned to its cohort row band",
                            target=f"layout_boxes.{feature_label_box.box_id}",
                            observed={"label_center_y": label_center_y},
                            expected={"row_y0": bar_box.y0, "row_y1": bar_box.y1},
                            box_refs=(bar_box.box_id, feature_label_box.box_id),
                        )
                    )
            if value_label_box is None:
                issues.append(
                    _issue(
                        rule_id="value_label_missing",
                        message="shap multicohort importance metrics must reference an existing value_label box",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].value_label_box_id",
                        observed=value_label_box_id,
                    )
                )

        feature_order_tuple = tuple(feature_order)
        if expected_feature_order is None:
            expected_feature_order = feature_order_tuple
        elif feature_order_tuple != expected_feature_order:
            issues.append(
                _issue(
                    rule_id="multicohort_feature_order_mismatch",
                    message="all shap multicohort panels must keep the same feature order across cohorts",
                    target=f"metrics.panels[{panel_index}].bars",
                    observed={"feature_order": list(feature_order_tuple)},
                    expected={"feature_order": list(expected_feature_order)},
                    box_refs=(panel_box.box_id,),
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.08,
        )
    )
    return issues


def _check_publication_shap_dependence_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label", "zero_line", "colorbar"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_colorbar_panel_overlap(sidecar))

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="shap dependence qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap dependence panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    zero_lines = _boxes_of_type(sidecar.guide_boxes, "zero_line")
    if len(zero_lines) < len(metrics_panels):
        issues.append(
            _issue(
                rule_id="zero_line_count_mismatch",
                message="shap dependence requires at least one zero line per panel",
                target="guide_boxes.zero_line",
                observed={"count": len(zero_lines)},
                expected={"minimum_count": len(metrics_panels)},
            )
        )

    colorbar_label = str(sidecar.metrics.get("colorbar_label") or "").strip()
    if not colorbar_label:
        issues.append(
            _issue(
                rule_id="colorbar_label_missing",
                message="shap dependence qc requires a non-empty colorbar label metric",
                target="metrics.colorbar_label",
            )
        )

    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    panel_box_by_suffix = {
        box.box_id.removeprefix("panel_"): box
        for box in panel_boxes
        if box.box_id.startswith("panel_")
    }
    label_panel_map: dict[str, str] = {}
    for panel_index, item in enumerate(metrics_panels):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(item.get("panel_id") or "").strip()
        panel_label = str(item.get("panel_label") or "").strip()
        title = str(item.get("title") or "").strip()
        x_label = str(item.get("x_label") or "").strip()
        feature = str(item.get("feature") or "").strip()
        interaction_feature = str(item.get("interaction_feature") or "").strip()
        if not panel_id or not panel_label or not title or not x_label or not feature or not interaction_feature:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="shap dependence panel metrics must declare panel metadata and labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        expected_panel_box_id = f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(expected_panel_box_id)
        if panel_box is None:
            panel_box = panel_box_by_suffix.get(panel_label)
        if panel_box is None and panel_index < len(panel_boxes):
            panel_box = panel_boxes[panel_index]
        if panel_box is not None:
            label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        points = item.get("points")
        if not isinstance(points, list) or not points:
            issues.append(
                _issue(
                    rule_id="panel_points_missing",
                    message="shap dependence panel metrics must carry non-empty normalized points",
                    target=f"metrics.panels[{panel_index}].points",
                )
            )
            continue
        if panel_box is None:
            continue
        for point_index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}] must be an object")
            x_value = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].x",
            )
            y_value = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].y",
            )
            if _point_within_box(panel_box, x=x_value, y=y_value):
                continue
            issues.append(
                _issue(
                    rule_id="point_outside_panel",
                    message="shap dependence point must stay within its declared panel",
                    target=f"metrics.panels[{panel_index}].points[{point_index}]",
                    observed={"x": x_value, "y": y_value},
                    box_refs=(panel_box.box_id,),
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )

    for zero_line in zero_lines:
        if any(_box_within_box(zero_line, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="zero_line_outside_panel",
                message="shap dependence zero line must stay within a panel region",
                target="guide_boxes.zero_line",
                box_refs=(zero_line.box_id,),
            )
        )
    return issues


def _check_publication_illustration_flow(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("main_step",)))

    flow_nodes = sidecar.metrics.get("flow_nodes")
    if not isinstance(flow_nodes, list) or not flow_nodes:
        issues.append(
            _issue(
                rule_id="flow_nodes_missing",
                message="illustration flow qc requires flow_nodes metrics for node-level readability checks",
                target="metrics.flow_nodes",
            )
        )
    else:
        for index, item in enumerate(flow_nodes):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.flow_nodes[{index}] must be an object")
            box_type = str(item.get("box_type") or "").strip()
            rendered_height_pt = _require_numeric(
                item.get("rendered_height_pt"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].rendered_height_pt",
            )
            rendered_width_pt = _require_numeric(
                item.get("rendered_width_pt"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].rendered_width_pt",
            )
            line_count = _require_numeric(
                item.get("line_count"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].line_count",
            )
            max_line_chars = _require_numeric(
                item.get("max_line_chars"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].max_line_chars",
            )
            padding_pt = _require_numeric(
                item.get("padding_pt"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].padding_pt",
            )
            minimum_height_pt = 80.0 if box_type == "main_step" else 56.0
            minimum_padding_pt = 8.0 if box_type == "main_step" else 6.0
            if rendered_height_pt < minimum_height_pt:
                issues.append(
                    _issue(
                        rule_id="flow_node_height_too_small",
                        message="flow node height is too small for manuscript-facing readability",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"rendered_height_pt": rendered_height_pt, "box_type": box_type},
                        expected={"minimum_height_pt": minimum_height_pt},
                    )
                )
            if rendered_width_pt < 160.0:
                issues.append(
                    _issue(
                        rule_id="flow_node_width_too_small",
                        message="flow node width is too small for manuscript-facing readability",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"rendered_width_pt": rendered_width_pt, "box_type": box_type},
                        expected={"minimum_width_pt": 160.0},
                    )
                )
            if padding_pt < minimum_padding_pt:
                issues.append(
                    _issue(
                        rule_id="flow_node_padding_too_small",
                        message="flow node padding is too small for manuscript-facing readability",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"padding_pt": padding_pt, "box_type": box_type},
                        expected={"minimum_padding_pt": minimum_padding_pt},
                    )
                )
            if line_count > 0 and max_line_chars > 44:
                issues.append(
                    _issue(
                        rule_id="flow_node_text_density_high",
                        message="flow node line length is too dense for the audited cohort-flow shell",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"line_count": line_count, "max_line_chars": max_line_chars},
                        expected={"maximum_max_line_chars": 44},
                    )
                )

    step_boxes = _boxes_of_type(sidecar.layout_boxes, "main_step")
    sorted_step_boxes = tuple(
        sorted(step_boxes, key=lambda box: (-((box.y0 + box.y1) / 2.0), box.x0, box.box_id))
    )
    issues.extend(_check_pairwise_non_overlap(step_boxes, rule_id="main_step_overlap", target="main_step"))

    exclusion_boxes = _boxes_of_type(sidecar.layout_boxes, "exclusion_box")
    issues.extend(_check_pairwise_non_overlap(exclusion_boxes, rule_id="exclusion_box_overlap", target="exclusion_box"))
    for exclusion_box in exclusion_boxes:
        for step_box in step_boxes:
            if not _boxes_overlap(exclusion_box, step_box):
                continue
            issues.append(
                _issue(
                    rule_id="exclusion_step_overlap",
                    message="exclusion box must not overlap a main cohort step",
                    target="exclusion_box",
                    box_refs=(exclusion_box.box_id, step_box.box_id),
                )
            )

    subfigure_panels = {box.box_id: box for box in _boxes_of_type(sidecar.panel_boxes, "subfigure_panel")}
    for required_box_id in ("subfigure_panel_A", "subfigure_panel_B"):
        if required_box_id in subfigure_panels:
            continue
        issues.append(
            _issue(
                rule_id="missing_subfigure_panel",
                message="illustration flow requires both Panel A and Panel B containers",
                target="panel_boxes",
                expected=required_box_id,
            )
        )

    panel_labels = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "panel_label")}
    for required_box_id in ("panel_label_A", "panel_label_B"):
        if required_box_id in panel_labels:
            continue
        issues.append(
            _issue(
                rule_id="missing_panel_label",
                message="illustration flow requires explicit A/B panel labels",
                target="layout_boxes",
                expected=required_box_id,
            )
        )

    flow_panel = _first_box_of_type(sidecar.panel_boxes, "flow_panel")
    panel_a = subfigure_panels.get("subfigure_panel_A")
    if panel_a is not None:
        if flow_panel is not None and not _box_within_box(flow_panel, panel_a):
            issues.append(
                _issue(
                    rule_id="flow_panel_out_of_subfigure",
                    message="flow panel must stay within Panel A",
                    target="flow_panel",
                    box_refs=(flow_panel.box_id, panel_a.box_id),
                )
            )
        for box in step_boxes + exclusion_boxes:
            if _box_within_box(box, panel_a):
                continue
            issues.append(
                _issue(
                    rule_id="flow_content_out_of_panel_a",
                    message="cohort flow content must stay within Panel A",
                    target=box.box_type,
                    box_refs=(box.box_id, panel_a.box_id),
                )
            )

    secondary_panels = _boxes_of_type(sidecar.panel_boxes, "secondary_panel")
    issues.extend(_check_pairwise_non_overlap(secondary_panels, rule_id="secondary_panel_overlap", target="secondary_panel"))
    panel_b = subfigure_panels.get("subfigure_panel_B")
    for secondary_panel in secondary_panels:
        if panel_b is not None and not _box_within_box(secondary_panel, panel_b):
            issues.append(
                _issue(
                    rule_id="secondary_panel_out_of_subfigure",
                    message="secondary analytic panels must stay within Panel B",
                    target="secondary_panel",
                    box_refs=(secondary_panel.box_id, panel_b.box_id),
                )
            )
        for step_box in step_boxes:
            if not _boxes_overlap(secondary_panel, step_box):
                continue
            issues.append(
                _issue(
                    rule_id="secondary_panel_step_overlap",
                    message="secondary panel must not overlap a main cohort step",
                    target="secondary_panel",
                    box_refs=(secondary_panel.box_id, step_box.box_id),
                )
            )

    for label_box_id, label_box in panel_labels.items():
        suffix = label_box_id.removeprefix("panel_label_")
        parent_panel = subfigure_panels.get(f"subfigure_panel_{suffix}")
        if parent_panel is None or _box_within_box(label_box, parent_panel):
            continue
        issues.append(
            _issue(
                rule_id="panel_label_out_of_subfigure",
                message="panel label must stay within its declared subfigure panel",
                target="panel_label",
                box_refs=(label_box.box_id, parent_panel.box_id),
            )
        )

    flow_connectors = {box.box_id: box for box in _boxes_of_type(sidecar.guide_boxes, "flow_connector")}
    flow_branch_connectors = {box.box_id: box for box in _boxes_of_type(sidecar.guide_boxes, "flow_branch_connector")}
    expected_step_ids = [str(item.get("step_id") or "").strip() for item in sidecar.metrics.get("steps", []) if isinstance(item, dict)]
    expected_step_ids = [item for item in expected_step_ids if item]
    if not expected_step_ids:
        expected_step_ids = [box.box_id.removeprefix("step_") for box in sorted_step_boxes]
    expected_exclusions = [
        str(item.get("exclusion_id") or "").strip()
        for item in sidecar.metrics.get("exclusions", [])
        if isinstance(item, dict) and str(item.get("exclusion_id") or "").strip()
    ]
    if not expected_exclusions:
        expected_exclusions = [box.box_id.removeprefix("exclusion_") for box in exclusion_boxes]

    missing_flow_connectors: list[str] = []
    for upper_step_id, lower_step_id in zip(expected_step_ids, expected_step_ids[1:], strict=False):
        connector_id = f"flow_spine_{upper_step_id}_to_{lower_step_id}"
        if connector_id not in flow_connectors:
            missing_flow_connectors.append(connector_id)
    for exclusion_id in expected_exclusions:
        connector_id = f"flow_branch_{exclusion_id}"
        if connector_id not in flow_branch_connectors:
            missing_flow_connectors.append(connector_id)
    if missing_flow_connectors:
        issues.append(
            _issue(
                rule_id="missing_flow_connector",
                message="illustration flow requires explicit spine and exclusion branch connectors",
                target="guide_boxes",
                expected=missing_flow_connectors,
            )
        )

    def _vertical_center(box: Box) -> float:
        return (box.y0 + box.y1) / 2.0

    def _stage_gap_contains_y(y_value: float) -> bool:
        epsilon = 1e-6
        for upper_step, lower_step in zip(sorted_step_boxes, sorted_step_boxes[1:], strict=False):
            if lower_step.y1 - epsilon <= y_value <= upper_step.y0 + epsilon:
                return True
        return False

    for exclusion_box in exclusion_boxes:
        if len(sorted_step_boxes) < 2 or _stage_gap_contains_y(_vertical_center(exclusion_box)):
            continue
        issues.append(
            _issue(
                rule_id="misanchored_exclusion_box",
                message="exclusion box must be centered on a stage boundary between adjacent main steps",
                target="exclusion_box",
                box_refs=(exclusion_box.box_id,),
            )
        )

    for connector_box in flow_branch_connectors.values():
        if len(sorted_step_boxes) < 2 or _stage_gap_contains_y(_vertical_center(connector_box)):
            continue
        issues.append(
            _issue(
                rule_id="misanchored_flow_branch",
                message="exclusion branch connector must originate from a stage boundary between adjacent main steps",
                target="flow_branch_connector",
                box_refs=(connector_box.box_id,),
            )
        )

    hierarchy_connectors = {box.box_id: box for box in _boxes_of_type(sidecar.guide_boxes, "hierarchy_connector")}
    design_panel_roles = {
        str(item.get("layout_role") or "").strip()
        for item in sidecar.metrics.get("design_panels", [])
        if isinstance(item, dict)
    }
    expected_hierarchy_connectors: list[str] = []
    if "wide_top" in design_panel_roles and (
        ("left_middle" in design_panel_roles or "left_bottom" in design_panel_roles)
        and ("right_middle" in design_panel_roles or "right_bottom" in design_panel_roles)
    ):
        expected_hierarchy_connectors.extend(["hierarchy_root_trunk", "hierarchy_root_branch"])
    if {"left_middle", "left_bottom"} <= design_panel_roles:
        expected_hierarchy_connectors.append("hierarchy_connector_left_middle_to_left_bottom")
    if {"right_middle", "right_bottom"} <= design_panel_roles:
        expected_hierarchy_connectors.append("hierarchy_connector_right_middle_to_right_bottom")
    missing_hierarchy_connectors = [box_id for box_id in expected_hierarchy_connectors if box_id not in hierarchy_connectors]
    if missing_hierarchy_connectors:
        issues.append(
            _issue(
                rule_id="missing_hierarchy_connector",
                message="illustration flow requires rooted hierarchy connectors for Panel B",
                target="guide_boxes",
                expected=missing_hierarchy_connectors,
            )
        )

    return issues


def _check_submission_graphical_abstract(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("title", "panel_label", "card_box", "footer_pill")))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    if len(panel_boxes) < 3:
        issues.append(
            _issue(
                rule_id="graphical_abstract_panels_missing",
                message="submission graphical abstract requires three panels",
                target="panel_boxes",
                expected={"minimum_count": 3},
                observed={"count": len(panel_boxes)},
            )
        )

    card_boxes = _boxes_of_type(sidecar.layout_boxes, "card_box")
    footer_pills = _boxes_of_type(sidecar.layout_boxes, "footer_pill")
    panel_labels = _boxes_of_type(sidecar.layout_boxes, "panel_label")
    arrow_boxes = _boxes_of_type(sidecar.guide_boxes, "arrow_connector")
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"panel_title", "panel_subtitle", "card_title", "card_value", "card_detail"}
    )

    issues.extend(_check_pairwise_non_overlap(card_boxes, rule_id="graphical_abstract_card_overlap", target="card_box"))
    issues.extend(_check_pairwise_non_overlap(footer_pills, rule_id="graphical_abstract_footer_overlap", target="footer_pill"))
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="graphical_abstract_text_overlap", target="text"))

    for card_box in card_boxes:
        if any(_box_within_box(card_box, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="card_out_of_panel",
                message="graphical-abstract cards must stay within a panel",
                target="card_box",
                box_refs=(card_box.box_id,),
            )
        )
    for panel_label in panel_labels:
        if any(_box_within_box(panel_label, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="panel_label_out_of_panel",
                message="graphical-abstract panel labels must stay within their panels",
                target="panel_label",
                box_refs=(panel_label.box_id,),
            )
        )
    for text_box in text_boxes:
        if any(_box_within_box(text_box, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="panel_text_out_of_panel",
                message="graphical-abstract panel text must stay within a panel",
                target=text_box.box_type,
                box_refs=(text_box.box_id,),
            )
        )
    for footer_pill in footer_pills:
        for panel_box in panel_boxes:
            if not _boxes_overlap(footer_pill, panel_box):
                continue
            issues.append(
                _issue(
                    rule_id="footer_pill_panel_overlap",
                    message="graphical-abstract footer pills must stay outside the panels",
                    target="footer_pill",
                    box_refs=(footer_pill.box_id, panel_box.box_id),
                )
            )
        for arrow_box in arrow_boxes:
            if not _boxes_overlap(footer_pill, arrow_box):
                continue
            issues.append(
                _issue(
                    rule_id="footer_pill_arrow_overlap",
                    message="graphical-abstract footer pills must not overlap arrow connectors",
                    target="footer_pill",
                    box_refs=(footer_pill.box_id, arrow_box.box_id),
                )
            )
    for arrow_box in arrow_boxes:
        for panel_box in panel_boxes:
            if _boxes_overlap(arrow_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="arrow_panel_overlap",
                        message="graphical-abstract arrows must stay between panels",
                        target="arrow_connector",
                        box_refs=(arrow_box.box_id, panel_box.box_id),
                    )
                )
        for text_box in text_boxes:
            if not _boxes_overlap(arrow_box, text_box):
                continue
            issues.append(
                _issue(
                    rule_id="arrow_text_overlap",
                    message="graphical-abstract arrows must not overlap panel text",
                    target="arrow_connector",
                    box_refs=(arrow_box.box_id, text_box.box_id),
                )
            )
    sorted_panels = tuple(sorted(panel_boxes, key=lambda box: (box.x0, box.y0, box.box_id)))
    sorted_arrows = tuple(sorted(arrow_boxes, key=lambda box: (box.x0, box.y0, box.box_id)))
    if len(sorted_arrows) >= 2:
        arrow_mid_ys = [((arrow_box.y0 + arrow_box.y1) / 2.0) for arrow_box in sorted_arrows]
        arrow_heights = [(arrow_box.y1 - arrow_box.y0) for arrow_box in sorted_arrows]
        alignment_tolerance = max(max(arrow_heights, default=0.0) * 1.5, 0.03)
        if max(arrow_mid_ys) - min(arrow_mid_ys) > alignment_tolerance:
            issues.append(
                _issue(
                    rule_id="arrow_cross_pair_misalignment",
                    message="graphical-abstract arrows between adjacent panels must share the same horizontal lane",
                    target="arrow_connector",
                    box_refs=tuple(arrow_box.box_id for arrow_box in sorted_arrows),
                )
            )
    for arrow_box in sorted_arrows:
        arrow_mid_x = (arrow_box.x0 + arrow_box.x1) / 2.0
        arrow_mid_y = (arrow_box.y0 + arrow_box.y1) / 2.0
        parent_pair: tuple[Box, Box] | None = None
        for left_panel, right_panel in zip(sorted_panels, sorted_panels[1:], strict=False):
            if left_panel.x1 <= arrow_mid_x <= right_panel.x0:
                parent_pair = (left_panel, right_panel)
                break
        if parent_pair is None:
            continue
        shared_y0 = max(parent_pair[0].y0, parent_pair[1].y0)
        shared_y1 = min(parent_pair[0].y1, parent_pair[1].y1)
        shared_height = max(shared_y1 - shared_y0, 1e-9)
        shared_mid_y = (shared_y0 + shared_y1) / 2.0
        if abs(arrow_mid_y - shared_mid_y) <= max(shared_height * 0.18, (arrow_box.y1 - arrow_box.y0) * 1.5):
            continue
        issues.append(
            _issue(
                rule_id="arrow_midline_alignment",
                message="graphical-abstract arrows must stay near the shared vertical midline between adjacent panels",
                target="arrow_connector",
                box_refs=(arrow_box.box_id, parent_pair[0].box_id, parent_pair[1].box_id),
            )
        )
    return issues


def _check_publication_baseline_missingness_qc_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=("panel", "panel_label", "panel_title", "subplot_x_axis_title", "card_label", "card_value"),
        )
    )

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 3:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="baseline missingness QC panel requires exactly three panel boxes",
                target="panel_boxes",
                expected={"count": 3},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    panel_label_to_panel_id = {
        "A": "panel_balance",
        "B": "panel_missingness",
        "C": "panel_qc",
    }
    title_boxes = {
        "balance_panel_title": "panel_balance",
        "missingness_panel_title": "panel_missingness",
        "qc_panel_title": "panel_qc",
    }
    for panel_label, panel_id in panel_label_to_panel_id.items():
        label_box = layout_boxes_by_id.get(f"panel_label_{panel_label}")
        panel_box = panel_boxes_by_id.get(panel_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="baseline missingness QC panel requires the fixed three-panel layout",
                    target="panel_boxes",
                    expected=panel_id,
                )
            )
            continue
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="baseline missingness QC panel labels must be present for every panel",
                    target="panel_label",
                    expected=f"panel_label_{panel_label}",
                )
            )
            continue
        if not _box_within_box(label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="baseline missingness QC panel labels must stay within their parent panel",
                    target="panel_label",
                    box_refs=(label_box.box_id, panel_box.box_id),
                )
            )
        else:
            panel_width = max(panel_box.x1 - panel_box.x0, 1e-9)
            panel_height = max(panel_box.y1 - panel_box.y0, 1e-9)
            anchored_near_left = label_box.x0 <= panel_box.x0 + panel_width * 0.10
            anchored_near_top = (
                label_box.y0 <= panel_box.y0 + panel_height * 0.12
                or label_box.y1 >= panel_box.y1 - panel_height * 0.10
            )
            if not (anchored_near_left and anchored_near_top):
                issues.append(
                    _issue(
                        rule_id="panel_label_anchor_drift",
                        message="baseline missingness QC panel labels must stay near the parent panel top-left anchor",
                        target="panel_label",
                        box_refs=(label_box.box_id, panel_box.box_id),
                    )
                )

    for title_box_id, panel_id in title_boxes.items():
        title_box = layout_boxes_by_id.get(title_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="baseline missingness QC panel requires all three panel titles",
                    target="panel_title",
                    expected=title_box_id,
                )
            )
            continue
        if panel_box is not None:
            aligned_horizontally = (
                title_box.x0 >= panel_box.x0 - 0.02 and title_box.x1 <= panel_box.x1 + 0.02
            )
            close_to_panel_top = (
                title_box.y0 >= panel_box.y0 - 0.02 and title_box.y1 <= panel_box.y1 + 0.08
            )
            if aligned_horizontally and close_to_panel_top:
                continue
            issues.append(
                _issue(
                    rule_id="panel_title_out_of_panel",
                    message="baseline missingness QC panel titles must stay tightly aligned with their parent panel",
                    target="panel_title",
                    box_refs=(title_box.box_id, panel_box.box_id),
                )
            )

    axis_title_pairs = (
        ("balance_x_axis_title", "panel_balance"),
        ("missingness_x_axis_title", "panel_missingness"),
        ("missingness_y_axis_title", "panel_missingness"),
    )
    for axis_box_id, panel_id in axis_title_pairs:
        axis_box = layout_boxes_by_id.get(axis_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if axis_box is None:
            issues.append(
                _issue(
                    rule_id="axis_title_missing",
                    message="baseline missingness QC panel must expose the bounded axis-title surface",
                    target="subplot_axis_title",
                    expected=axis_box_id,
                )
            )
            continue
        if panel_box is not None:
            if axis_box.box_id.endswith("_y_axis_title"):
                axis_center_y = (axis_box.y0 + axis_box.y1) / 2.0
                aligned_with_panel = (
                    panel_box.y0 <= axis_center_y <= panel_box.y1
                    and axis_box.x0 >= panel_box.x0 - 0.12
                    and axis_box.x1 <= panel_box.x1 + 0.02
                )
            else:
                axis_center_x = (axis_box.x0 + axis_box.x1) / 2.0
                aligned_with_panel = (
                    panel_box.x0 <= axis_center_x <= panel_box.x1
                    and axis_box.y0 >= panel_box.y0 - 0.10
                    and axis_box.y1 <= panel_box.y1 + 0.02
                )
            if not aligned_with_panel:
                issues.append(
                    _issue(
                        rule_id="axis_title_out_of_panel",
                        message="baseline missingness QC axis titles must stay tightly aligned with their parent panel",
                        target=axis_box.box_type,
                        box_refs=(axis_box.box_id, panel_box.box_id),
                    )
                )

    if not _boxes_of_type(sidecar.guide_boxes, "reference_line"):
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="baseline missingness QC panel requires a balance threshold reference line",
                target="reference_line",
            )
        )
    if not _boxes_of_type(sidecar.guide_boxes, "colorbar"):
        issues.append(
            _issue(
                rule_id="colorbar_missing",
                message="baseline missingness QC panel requires a missingness colorbar guide box",
                target="colorbar",
            )
        )

    balance_threshold = _require_numeric(sidecar.metrics.get("balance_threshold"), label="layout_sidecar.metrics.balance_threshold")
    if not math.isfinite(balance_threshold) or balance_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="balance_threshold_invalid",
                message="balance_threshold must be positive and finite",
                target="metrics.balance_threshold",
                observed=balance_threshold,
            )
        )
    primary_balance_label = str(sidecar.metrics.get("primary_balance_label") or "").strip()
    if not primary_balance_label:
        issues.append(
            _issue(
                rule_id="primary_balance_label_missing",
                message="primary_balance_label must be non-empty",
                target="metrics.primary_balance_label",
            )
        )
    secondary_balance_label = str(sidecar.metrics.get("secondary_balance_label") or "").strip()
    balance_variables = sidecar.metrics.get("balance_variables")
    if not isinstance(balance_variables, list) or not balance_variables:
        issues.append(
            _issue(
                rule_id="balance_variables_missing",
                message="baseline missingness QC panel requires non-empty balance_variables metrics",
                target="metrics.balance_variables",
            )
        )
    else:
        seen_variable_ids: set[str] = set()
        seen_variable_labels: set[str] = set()
        saw_secondary_values = False
        for index, item in enumerate(balance_variables):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.balance_variables[{index}] must be an object")
            variable_id = str(item.get("variable_id") or "").strip()
            label = str(item.get("label") or "").strip()
            if not variable_id:
                issues.append(
                    _issue(
                        rule_id="balance_variable_id_missing",
                        message="balance variable ids must be non-empty",
                        target=f"metrics.balance_variables[{index}].variable_id",
                    )
                )
            elif variable_id in seen_variable_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_balance_variable_id",
                        message="balance variable ids must be unique",
                        target="metrics.balance_variables",
                        observed=variable_id,
                    )
                )
            else:
                seen_variable_ids.add(variable_id)
            if not label:
                issues.append(
                    _issue(
                        rule_id="balance_variable_label_missing",
                        message="balance variable labels must be non-empty",
                        target=f"metrics.balance_variables[{index}].label",
                    )
                )
            elif label in seen_variable_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_balance_variable_label",
                        message="balance variable labels must be unique",
                        target="metrics.balance_variables",
                        observed=label,
                    )
                )
            else:
                seen_variable_labels.add(label)
            primary_value = _require_numeric(
                item.get("primary_value"),
                label=f"layout_sidecar.metrics.balance_variables[{index}].primary_value",
            )
            if not math.isfinite(primary_value) or primary_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="balance_primary_value_invalid",
                        message="primary balance values must be finite and non-negative",
                        target=f"metrics.balance_variables[{index}].primary_value",
                        observed=primary_value,
                    )
                )
            if item.get("secondary_value") is not None:
                saw_secondary_values = True
                secondary_value = _require_numeric(
                    item.get("secondary_value"),
                    label=f"layout_sidecar.metrics.balance_variables[{index}].secondary_value",
                )
                if not math.isfinite(secondary_value) or secondary_value < 0.0:
                    issues.append(
                        _issue(
                            rule_id="balance_secondary_value_invalid",
                            message="secondary balance values must be finite and non-negative",
                            target=f"metrics.balance_variables[{index}].secondary_value",
                            observed=secondary_value,
                        )
                    )
        if saw_secondary_values and not secondary_balance_label:
            issues.append(
                _issue(
                    rule_id="balance_secondary_label_missing",
                    message="secondary balance values require a non-empty secondary_balance_label",
                    target="metrics.secondary_balance_label",
                )
            )

    missingness_rows = sidecar.metrics.get("missingness_rows")
    missingness_columns = sidecar.metrics.get("missingness_columns")
    missingness_cells = sidecar.metrics.get("missingness_cells")
    normalized_row_labels: list[str] = []
    normalized_column_labels: list[str] = []
    if not isinstance(missingness_rows, list) or not missingness_rows:
        issues.append(
            _issue(
                rule_id="missingness_rows_missing",
                message="missingness_rows must be non-empty",
                target="metrics.missingness_rows",
            )
        )
    else:
        seen_row_labels: set[str] = set()
        for index, item in enumerate(missingness_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.missingness_rows[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id="missingness_row_label_missing",
                        message="missingness row labels must be non-empty",
                        target=f"metrics.missingness_rows[{index}].label",
                    )
                )
                continue
            if label in seen_row_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_missingness_row_label",
                        message="missingness row labels must be unique",
                        target="metrics.missingness_rows",
                        observed=label,
                    )
                )
                continue
            seen_row_labels.add(label)
            normalized_row_labels.append(label)
    if not isinstance(missingness_columns, list) or not missingness_columns:
        issues.append(
            _issue(
                rule_id="missingness_columns_missing",
                message="missingness_columns must be non-empty",
                target="metrics.missingness_columns",
            )
        )
    else:
        seen_column_labels: set[str] = set()
        for index, item in enumerate(missingness_columns):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.missingness_columns[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id="missingness_column_label_missing",
                        message="missingness column labels must be non-empty",
                        target=f"metrics.missingness_columns[{index}].label",
                    )
                )
                continue
            if label in seen_column_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_missingness_column_label",
                        message="missingness column labels must be unique",
                        target="metrics.missingness_columns",
                        observed=label,
                    )
                )
                continue
            seen_column_labels.add(label)
            normalized_column_labels.append(label)
    if not isinstance(missingness_cells, list) or not missingness_cells:
        issues.append(
            _issue(
                rule_id="missingness_cells_missing",
                message="missingness_cells must be non-empty",
                target="metrics.missingness_cells",
            )
        )
    else:
        observed_rows: set[str] = set()
        observed_columns: set[str] = set()
        seen_coordinates: set[tuple[str, str]] = set()
        for index, item in enumerate(missingness_cells):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.missingness_cells[{index}] must be an object")
            column_label = str(item.get("x") or "").strip()
            row_label = str(item.get("y") or "").strip()
            coordinate = (column_label, row_label)
            if coordinate in seen_coordinates:
                issues.append(
                    _issue(
                        rule_id="duplicate_missingness_coordinate",
                        message="missingness cells must not repeat coordinates",
                        target="metrics.missingness_cells",
                        observed={"x": column_label, "y": row_label},
                    )
                )
            else:
                seen_coordinates.add(coordinate)
            observed_rows.add(row_label)
            observed_columns.add(column_label)
            value = _require_numeric(
                item.get("value"),
                label=f"layout_sidecar.metrics.missingness_cells[{index}].value",
            )
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                issues.append(
                    _issue(
                        rule_id="missingness_value_out_of_range",
                        message="missingness cell values must stay within [0, 1]",
                        target=f"metrics.missingness_cells[{index}].value",
                        observed=value,
                    )
                )
        expected_rows = set(normalized_row_labels)
        expected_columns = set(normalized_column_labels)
        if normalized_row_labels and observed_rows != expected_rows:
            issues.append(
                _issue(
                    rule_id="missingness_row_set_mismatch",
                    message="missingness cells must match the declared row labels",
                    target="metrics.missingness_cells",
                    observed=sorted(observed_rows),
                    expected=sorted(expected_rows),
                )
            )
        if normalized_column_labels and observed_columns != expected_columns:
            issues.append(
                _issue(
                    rule_id="missingness_column_set_mismatch",
                    message="missingness cells must match the declared column labels",
                    target="metrics.missingness_cells",
                    observed=sorted(observed_columns),
                    expected=sorted(expected_columns),
                )
            )
        expected_cell_count = len(normalized_row_labels) * len(normalized_column_labels)
        if expected_cell_count > 0 and len(seen_coordinates) != expected_cell_count:
            issues.append(
                _issue(
                    rule_id="declared_missingness_grid_incomplete",
                    message="missingness cells must cover the declared row-column grid exactly once",
                    target="metrics.missingness_cells",
                    observed={"cells": len(seen_coordinates)},
                    expected={"cells": expected_cell_count},
                )
            )

    qc_panel = panel_boxes_by_id.get("panel_qc")
    qc_cards = sidecar.metrics.get("qc_cards")
    if not isinstance(qc_cards, list) or not qc_cards:
        issues.append(
            _issue(
                rule_id="qc_cards_missing",
                message="qc_cards must be non-empty",
                target="metrics.qc_cards",
            )
        )
    else:
        seen_card_ids: set[str] = set()
        for index, item in enumerate(qc_cards):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.qc_cards[{index}] must be an object")
            card_id = str(item.get("card_id") or "").strip()
            if not card_id:
                issues.append(
                    _issue(
                        rule_id="qc_card_id_missing",
                        message="qc card ids must be non-empty",
                        target=f"metrics.qc_cards[{index}].card_id",
                    )
                )
            elif card_id in seen_card_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_qc_card_id",
                        message="qc card ids must be unique",
                        target="metrics.qc_cards",
                        observed=card_id,
                    )
                )
            else:
                seen_card_ids.add(card_id)
            label_box_id = str(item.get("label_box_id") or "").strip()
            value_box_id = str(item.get("value_box_id") or "").strip()
            label_box = layout_boxes_by_id.get(label_box_id)
            value_box = layout_boxes_by_id.get(value_box_id)
            if label_box is None:
                issues.append(
                    _issue(
                        rule_id="qc_card_label_missing",
                        message="qc cards must reference an existing card_label box",
                        target=f"metrics.qc_cards[{index}].label_box_id",
                        expected=label_box_id,
                    )
                )
            elif qc_panel is not None and not _box_within_box(label_box, qc_panel):
                issues.append(
                    _issue(
                        rule_id="qc_card_out_of_panel",
                        message="qc card labels must stay within the qc panel",
                        target="card_label",
                        box_refs=(label_box.box_id, qc_panel.box_id),
                    )
                )
            if value_box is None:
                issues.append(
                    _issue(
                        rule_id="qc_card_value_missing",
                        message="qc cards must reference an existing card_value box",
                        target=f"metrics.qc_cards[{index}].value_box_id",
                        expected=value_box_id,
                    )
                )
            elif qc_panel is not None and not _box_within_box(value_box, qc_panel):
                issues.append(
                    _issue(
                        rule_id="qc_card_out_of_panel",
                        message="qc card values must stay within the qc panel",
                        target="card_value",
                        box_refs=(value_box.box_id, qc_panel.box_id),
                    )
                )

    return issues


def _check_publication_center_transportability_governance_summary_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "panel_label",
        "subplot_x_axis_title",
        "row_label",
        "estimate_marker",
        "ci_segment",
        "verdict_value",
        "row_metric",
        "row_action",
        "reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    if len(panel_boxes) != 2:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="center transportability governance summary requires exactly two panels",
                target="panel_boxes",
                expected={"count": 2},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    metric_panel = panel_boxes_by_id.get("metric_panel")
    summary_panel = panel_boxes_by_id.get("summary_panel")
    if metric_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="center transportability governance summary qc requires metric_panel and summary_panel",
                target="panel_boxes",
            )
        )
        return issues

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}

    def _check_panel_title_alignment(*, title_box_id: str, panel_box: Box) -> None:
        title_box = layout_box_by_id.get(title_box_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="center transportability governance summary requires both panel titles",
                    target="panel_title",
                    expected=title_box_id,
                )
            )
            return
        aligned_horizontally = title_box.x0 >= panel_box.x0 - 0.02 and title_box.x1 <= panel_box.x1 + 0.02
        close_to_panel_top = title_box.y0 >= panel_box.y0 - 0.02 and title_box.y1 <= panel_box.y1 + 0.10
        if not (aligned_horizontally and close_to_panel_top):
            issues.append(
                _issue(
                    rule_id="panel_title_out_of_alignment",
                    message="panel titles must stay tightly aligned with their parent panel",
                    target="panel_title",
                    box_refs=(title_box.box_id, panel_box.box_id),
                )
            )

    def _check_panel_label_inside(*, label_box_id: str, panel_box: Box) -> None:
        label_box = layout_box_by_id.get(label_box_id)
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="center transportability governance summary requires both panel labels",
                    target="panel_label",
                    expected=label_box_id,
                )
            )
            return
        if not _box_within_box(label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="panel labels must stay within their parent panel",
                    target="panel_label",
                    box_refs=(label_box.box_id, panel_box.box_id),
                )
            )

    _check_panel_title_alignment(title_box_id="panel_title_A", panel_box=metric_panel)
    _check_panel_title_alignment(title_box_id="panel_title_B", panel_box=summary_panel)
    _check_panel_label_inside(label_box_id="panel_label_A", panel_box=metric_panel)
    _check_panel_label_inside(label_box_id="panel_label_B", panel_box=summary_panel)

    x_axis_title_box = layout_box_by_id.get("x_axis_title_A")
    if x_axis_title_box is None:
        issues.append(
            _issue(
                rule_id="x_axis_title_missing",
                message="center transportability governance summary requires the metric x-axis title",
                target="subplot_x_axis_title",
                expected="x_axis_title_A",
            )
        )
    else:
        aligned_with_metric_panel = (
            metric_panel.x0 <= (x_axis_title_box.x0 + x_axis_title_box.x1) / 2.0 <= metric_panel.x1
            and x_axis_title_box.y0 >= metric_panel.y0 - 0.10
            and x_axis_title_box.y1 <= metric_panel.y1 + 0.02
        )
        if not aligned_with_metric_panel:
            issues.append(
                _issue(
                    rule_id="x_axis_title_out_of_alignment",
                    message="metric x-axis title must stay aligned with the metric panel",
                    target="subplot_x_axis_title",
                    box_refs=(x_axis_title_box.box_id, metric_panel.box_id),
                )
            )

    metric_panel_metrics = metrics.get("metric_panel")
    summary_panel_metrics = metrics.get("summary_panel")
    if not isinstance(metric_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="metric_panel_metrics_missing",
                message="metric panel metrics must be present",
                target="metrics.metric_panel",
            )
        )
        return issues
    if not isinstance(summary_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="summary_panel_metrics_missing",
                message="summary panel metrics must be present",
                target="metrics.summary_panel",
            )
        )
        return issues

    reference_line_box = guide_box_by_id.get(str(metric_panel_metrics.get("reference_line_box_id") or "").strip())
    if reference_line_box is None:
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="center transportability governance summary requires one reference line inside the metric panel",
                target="metrics.metric_panel.reference_line_box_id",
                box_refs=(metric_panel.box_id,),
            )
        )
    elif not _box_within_box(reference_line_box, metric_panel):
        issues.append(
            _issue(
                rule_id="reference_line_outside_metric_panel",
                message="reference line must stay within the metric panel",
                target=f"guide_boxes.{reference_line_box.box_id}",
                box_refs=(reference_line_box.box_id, metric_panel.box_id),
            )
        )

    metric_family = _require_non_empty_text(metrics.get("metric_family"), label="layout_sidecar.metrics.metric_family")
    supported_metric_families = {"discrimination", "calibration_ratio", "effect_estimate", "utility_delta"}
    if metric_family not in supported_metric_families:
        issues.append(
            _issue(
                rule_id="metric_family_invalid",
                message="metric_family must be one of discrimination, calibration_ratio, effect_estimate, utility_delta",
                target="metrics.metric_family",
                observed=metric_family,
            )
        )

    metric_reference_value = _require_numeric(
        metrics.get("metric_reference_value"),
        label="layout_sidecar.metrics.metric_reference_value",
    )
    if not math.isfinite(metric_reference_value):
        issues.append(
            _issue(
                rule_id="metric_reference_value_invalid",
                message="metric_reference_value must be finite",
                target="metrics.metric_reference_value",
                observed=metric_reference_value,
            )
        )
    batch_shift_threshold = _require_numeric(
        metrics.get("batch_shift_threshold"),
        label="layout_sidecar.metrics.batch_shift_threshold",
    )
    if not math.isfinite(batch_shift_threshold) or batch_shift_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="batch_shift_threshold_invalid",
                message="batch_shift_threshold must be positive and finite",
                target="metrics.batch_shift_threshold",
                observed=batch_shift_threshold,
            )
        )
    slope_acceptance_lower = _require_numeric(
        metrics.get("slope_acceptance_lower"),
        label="layout_sidecar.metrics.slope_acceptance_lower",
    )
    slope_acceptance_upper = _require_numeric(
        metrics.get("slope_acceptance_upper"),
        label="layout_sidecar.metrics.slope_acceptance_upper",
    )
    if (
        not math.isfinite(slope_acceptance_lower)
        or not math.isfinite(slope_acceptance_upper)
        or slope_acceptance_lower <= 0.0
        or slope_acceptance_upper <= 0.0
        or slope_acceptance_lower >= slope_acceptance_upper
    ):
        issues.append(
            _issue(
                rule_id="slope_acceptance_band_invalid",
                message="slope acceptance band must be positive, finite, and ordered",
                target="metrics.slope_acceptance_lower",
                observed={"lower": slope_acceptance_lower, "upper": slope_acceptance_upper},
            )
        )
    oe_ratio_acceptance_lower = _require_numeric(
        metrics.get("oe_ratio_acceptance_lower"),
        label="layout_sidecar.metrics.oe_ratio_acceptance_lower",
    )
    oe_ratio_acceptance_upper = _require_numeric(
        metrics.get("oe_ratio_acceptance_upper"),
        label="layout_sidecar.metrics.oe_ratio_acceptance_upper",
    )
    if (
        not math.isfinite(oe_ratio_acceptance_lower)
        or not math.isfinite(oe_ratio_acceptance_upper)
        or oe_ratio_acceptance_lower <= 0.0
        or oe_ratio_acceptance_upper <= 0.0
        or oe_ratio_acceptance_lower >= oe_ratio_acceptance_upper
    ):
        issues.append(
            _issue(
                rule_id="oe_ratio_acceptance_band_invalid",
                message="oe_ratio acceptance band must be positive, finite, and ordered",
                target="metrics.oe_ratio_acceptance_lower",
                observed={"lower": oe_ratio_acceptance_lower, "upper": oe_ratio_acceptance_upper},
            )
        )

    centers = metrics.get("centers")
    if not isinstance(centers, list) or not centers:
        issues.append(
            _issue(
                rule_id="centers_missing",
                message="center transportability governance summary requires non-empty center metrics",
                target="metrics.centers",
            )
        )
        return issues

    supported_verdicts = {
        "stable",
        "context_dependent",
        "recalibration_required",
        "insufficient_support",
        "unstable",
    }
    seen_center_ids: set[str] = set()
    seen_center_labels: set[str] = set()
    for index, center in enumerate(centers):
        if not isinstance(center, dict):
            raise ValueError(f"layout_sidecar.metrics.centers[{index}] must be an object")
        center_id = _require_non_empty_text(center.get("center_id"), label=f"layout_sidecar.metrics.centers[{index}].center_id")
        if center_id in seen_center_ids:
            issues.append(
                _issue(
                    rule_id="center_id_duplicate",
                    message="center ids must be unique",
                    target=f"metrics.centers[{index}].center_id",
                    observed=center_id,
                )
            )
        seen_center_ids.add(center_id)
        center_label = _require_non_empty_text(center.get("center_label"), label=f"layout_sidecar.metrics.centers[{index}].center_label")
        if center_label in seen_center_labels:
            issues.append(
                _issue(
                    rule_id="center_label_duplicate",
                    message="center labels must be unique",
                    target=f"metrics.centers[{index}].center_label",
                    observed=center_label,
                )
            )
        seen_center_labels.add(center_label)
        _require_non_empty_text(center.get("cohort_role"), label=f"layout_sidecar.metrics.centers[{index}].cohort_role")
        support_count = _require_numeric(center.get("support_count"), label=f"layout_sidecar.metrics.centers[{index}].support_count")
        event_count = _require_numeric(center.get("event_count"), label=f"layout_sidecar.metrics.centers[{index}].event_count")
        if not float(support_count).is_integer() or support_count <= 0:
            issues.append(
                _issue(
                    rule_id="center_support_count_invalid",
                    message="center support counts must be positive integers",
                    target=f"metrics.centers[{index}].support_count",
                    observed=support_count,
                )
            )
        if not float(event_count).is_integer() or event_count < 0:
            issues.append(
                _issue(
                    rule_id="center_event_count_invalid",
                    message="center event counts must be non-negative integers",
                    target=f"metrics.centers[{index}].event_count",
                    observed=event_count,
                )
            )
        elif event_count > support_count:
            issues.append(
                _issue(
                    rule_id="center_event_count_exceeds_support",
                    message="center event counts must not exceed support counts",
                    target=f"metrics.centers[{index}].event_count",
                    observed={"event_count": event_count, "support_count": support_count},
                )
            )
        metric_estimate = _require_numeric(center.get("metric_estimate"), label=f"layout_sidecar.metrics.centers[{index}].metric_estimate")
        metric_lower = _require_numeric(center.get("metric_lower"), label=f"layout_sidecar.metrics.centers[{index}].metric_lower")
        metric_upper = _require_numeric(center.get("metric_upper"), label=f"layout_sidecar.metrics.centers[{index}].metric_upper")
        if not all(math.isfinite(value) for value in (metric_estimate, metric_lower, metric_upper)):
            issues.append(
                _issue(
                    rule_id="center_metric_value_invalid",
                    message="center metric values must be finite",
                    target=f"metrics.centers[{index}]",
                )
            )
        elif not (metric_lower <= metric_estimate <= metric_upper):
            issues.append(
                _issue(
                    rule_id="center_metric_interval_invalid",
                    message="center metric intervals must satisfy lower <= estimate <= upper",
                    target=f"metrics.centers[{index}]",
                    observed={"lower": metric_lower, "estimate": metric_estimate, "upper": metric_upper},
                )
            )
        max_shift = _require_numeric(center.get("max_shift"), label=f"layout_sidecar.metrics.centers[{index}].max_shift")
        if not math.isfinite(max_shift) or max_shift < 0.0 or max_shift > 1.0:
            issues.append(
                _issue(
                    rule_id="center_max_shift_invalid",
                    message="center max_shift must stay within [0, 1]",
                    target=f"metrics.centers[{index}].max_shift",
                    observed=max_shift,
                )
            )
        slope = _require_numeric(center.get("slope"), label=f"layout_sidecar.metrics.centers[{index}].slope")
        if not math.isfinite(slope) or slope <= 0.0:
            issues.append(
                _issue(
                    rule_id="center_slope_invalid",
                    message="center slopes must be positive and finite",
                    target=f"metrics.centers[{index}].slope",
                    observed=slope,
                )
            )
        oe_ratio = _require_numeric(center.get("oe_ratio"), label=f"layout_sidecar.metrics.centers[{index}].oe_ratio")
        if not math.isfinite(oe_ratio) or oe_ratio <= 0.0:
            issues.append(
                _issue(
                    rule_id="center_oe_ratio_invalid",
                    message="center oe_ratio values must be positive and finite",
                    target=f"metrics.centers[{index}].oe_ratio",
                    observed=oe_ratio,
                )
            )
        verdict = _require_non_empty_text(center.get("verdict"), label=f"layout_sidecar.metrics.centers[{index}].verdict")
        if verdict not in supported_verdicts:
            issues.append(
                _issue(
                    rule_id="center_verdict_invalid",
                    message="center verdicts must be drawn from the audited vocabulary",
                    target=f"metrics.centers[{index}].verdict",
                    observed=verdict,
                )
            )
        _require_non_empty_text(center.get("action"), label=f"layout_sidecar.metrics.centers[{index}].action")
        detail_value = center.get("detail")
        if detail_value is not None:
            _require_non_empty_text(detail_value, label=f"layout_sidecar.metrics.centers[{index}].detail")

        label_box = layout_box_by_id.get(str(center.get("label_box_id") or "").strip())
        metric_box = layout_box_by_id.get(str(center.get("metric_box_id") or "").strip())
        interval_box = layout_box_by_id.get(str(center.get("interval_box_id") or "").strip())
        verdict_box = layout_box_by_id.get(str(center.get("verdict_box_id") or "").strip())
        metrics_box = layout_box_by_id.get(str(center.get("metrics_box_id") or "").strip())
        action_box = layout_box_by_id.get(str(center.get("action_box_id") or "").strip())
        detail_box = layout_box_by_id.get(str(center.get("detail_box_id") or "").strip()) if center.get("detail_box_id") else None

        if label_box is None:
            issues.append(
                _issue(
                    rule_id="row_label_missing",
                    message="each center must reference an existing row_label box",
                    target=f"metrics.centers[{index}].label_box_id",
                )
            )
        if metric_box is None:
            issues.append(
                _issue(
                    rule_id="metric_box_missing",
                    message="each center must reference an existing metric marker box",
                    target=f"metrics.centers[{index}].metric_box_id",
                )
            )
        elif not _box_within_box(metric_box, metric_panel):
            issues.append(
                _issue(
                    rule_id="metric_box_outside_metric_panel",
                    message="metric marker boxes must stay within the metric panel",
                    target="estimate_marker",
                    box_refs=(metric_box.box_id, metric_panel.box_id),
                )
            )
        if interval_box is None:
            issues.append(
                _issue(
                    rule_id="interval_box_missing",
                    message="each center must reference an existing ci_segment box",
                    target=f"metrics.centers[{index}].interval_box_id",
                )
            )
        elif not _box_within_box(interval_box, metric_panel):
            issues.append(
                _issue(
                    rule_id="interval_box_outside_metric_panel",
                    message="interval boxes must stay within the metric panel",
                    target="ci_segment",
                    box_refs=(interval_box.box_id, metric_panel.box_id),
                )
            )
        if verdict_box is None:
            issues.append(
                _issue(
                    rule_id="verdict_box_missing",
                    message="each center must reference an existing verdict box",
                    target=f"metrics.centers[{index}].verdict_box_id",
                )
            )
        elif not _box_within_box(verdict_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="verdict_box_outside_summary_panel",
                    message="verdict boxes must stay within the summary panel",
                    target="verdict_value",
                    box_refs=(verdict_box.box_id, summary_panel.box_id),
                )
            )
        if metrics_box is None:
            issues.append(
                _issue(
                    rule_id="metrics_box_missing",
                    message="each center must reference an existing summary metrics box",
                    target=f"metrics.centers[{index}].metrics_box_id",
                )
            )
        elif not _box_within_box(metrics_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="metrics_box_outside_summary_panel",
                    message="summary metrics boxes must stay within the summary panel",
                    target="row_metric",
                    box_refs=(metrics_box.box_id, summary_panel.box_id),
                )
            )
        if action_box is None:
            issues.append(
                _issue(
                    rule_id="action_box_missing",
                    message="each center must reference an existing action box",
                    target=f"metrics.centers[{index}].action_box_id",
                )
            )
        elif not _box_within_box(action_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="action_box_outside_summary_panel",
                    message="action boxes must stay within the summary panel",
                    target="row_action",
                    box_refs=(action_box.box_id, summary_panel.box_id),
                )
            )
        if detail_box is not None and not _box_within_box(detail_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="detail_box_outside_summary_panel",
                    message="detail boxes must stay within the summary panel",
                    target="verdict_detail",
                    box_refs=(detail_box.box_id, summary_panel.box_id),
                )
            )

    return issues


def _check_publication_genomic_program_governance_summary_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    required_box_types = [
        "panel_title",
        "panel_label",
        "row_label",
        "evidence_cell",
        "priority_badge",
        "verdict_value",
        "row_support",
        "row_action",
        "legend",
        "colorbar",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(
        _check_pairwise_non_overlap(
            tuple(
                box
                for box in sidecar.layout_boxes
                if box.box_type
                in {
                    "title",
                    "panel_title",
                    "panel_label",
                    "row_label",
                    "priority_badge",
                    "verdict_value",
                    "row_support",
                    "row_action",
                    "row_detail",
                }
            ),
            rule_id="text_box_overlap",
            target="text",
        )
    )

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    if len(panel_boxes) != 2:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="genomic program governance summary requires exactly two panels",
                target="panel_boxes",
                expected={"count": 2},
                observed={"count": len(panel_boxes)},
            )
        )
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    evidence_panel = panel_boxes_by_id.get("panel_evidence")
    summary_panel = panel_boxes_by_id.get("panel_summary")
    if evidence_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="genomic program governance summary qc requires panel_evidence and panel_summary",
                target="panel_boxes",
            )
        )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_evidence",
                "panel_label_B": "panel_summary",
            },
            allow_top_overhang_ratio=0.10,
            allow_left_overhang_ratio=0.12,
        )
    )

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_boxes_by_id = {box.box_id: box for box in sidecar.guide_boxes}

    def _check_panel_title_alignment(*, title_box_id: str, panel_box: Box) -> None:
        title_box = layout_boxes_by_id.get(title_box_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="genomic program governance summary requires both panel titles",
                    target="panel_title",
                    expected=title_box_id,
                )
            )
            return
        aligned_horizontally = title_box.x0 >= panel_box.x0 - 0.02 and title_box.x1 <= panel_box.x1 + 0.02
        close_to_panel_top = title_box.y0 >= panel_box.y0 - 0.02 and title_box.y1 <= panel_box.y1 + 0.10
        if not (aligned_horizontally and close_to_panel_top):
            issues.append(
                _issue(
                    rule_id="panel_title_out_of_alignment",
                    message="panel titles must stay tightly aligned with their parent panel",
                    target="panel_title",
                    box_refs=(title_box.box_id, panel_box.box_id),
                )
            )

    if evidence_panel is not None:
        _check_panel_title_alignment(title_box_id="panel_title_A", panel_box=evidence_panel)
    if summary_panel is not None:
        _check_panel_title_alignment(title_box_id="panel_title_B", panel_box=summary_panel)

    colorbar_box = guide_boxes_by_id.get("colorbar_effect")
    if colorbar_box is None:
        issues.append(
            _issue(
                rule_id="colorbar_missing",
                message="genomic program governance summary requires a colorbar for effect encoding",
                target="guide_boxes",
                expected="colorbar_effect",
            )
        )
    elif evidence_panel is not None and not _box_within_box(colorbar_box, evidence_panel):
        issues.append(
            _issue(
                rule_id="colorbar_out_of_panel",
                message="effect colorbar must stay within the evidence panel region",
                target="colorbar",
                box_refs=(colorbar_box.box_id, evidence_panel.box_id),
            )
        )

    legend_box = guide_boxes_by_id.get("legend_support")
    if legend_box is None:
        issues.append(
            _issue(
                rule_id="legend_missing",
                message="genomic program governance summary requires a support legend",
                target="guide_boxes",
                expected="legend_support",
            )
        )

    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    _require_non_empty_text(metrics.get("effect_scale_label"), label="layout_sidecar.metrics.effect_scale_label")
    _require_non_empty_text(metrics.get("support_scale_label"), label="layout_sidecar.metrics.support_scale_label")

    expected_layer_ids = (
        "alteration",
        "proteome",
        "phosphoproteome",
        "glycoproteome",
        "pathway",
    )
    expected_layer_labels = (
        "Alteration",
        "Proteome",
        "Phosphoproteome",
        "Glycoproteome",
        "Pathway",
    )
    layer_labels = metrics.get("layer_labels")
    if not isinstance(layer_labels, list) or not layer_labels:
        issues.append(
            _issue(
                rule_id="layer_labels_missing",
                message="genomic program governance summary requires non-empty layer_labels",
                target="metrics.layer_labels",
            )
        )
    else:
        observed_layer_labels = tuple(_require_non_empty_text(item, label=f"layout_sidecar.metrics.layer_labels[{index}]") for index, item in enumerate(layer_labels))
        if observed_layer_labels != expected_layer_labels:
            issues.append(
                _issue(
                    rule_id="layer_labels_invalid",
                    message="layer_labels must stay aligned to the fixed five-layer governance contract",
                    target="metrics.layer_labels",
                    observed=observed_layer_labels,
                    expected=expected_layer_labels,
                )
            )

    programs = metrics.get("programs")
    if not isinstance(programs, list) or not programs:
        issues.append(
            _issue(
                rule_id="programs_missing",
                message="genomic program governance summary requires non-empty program metrics",
                target="metrics.programs",
            )
        )
        return issues

    supported_priority_bands = {"high_priority", "monitor", "watchlist"}
    supported_verdicts = {"convergent", "layer_specific", "context_dependent", "insufficient_support"}
    seen_program_ids: set[str] = set()
    seen_program_labels: set[str] = set()
    seen_priority_ranks: set[int] = set()
    for index, item in enumerate(programs):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.programs[{index}] must be an object")

        program_id = _require_non_empty_text(
            item.get("program_id"),
            label=f"layout_sidecar.metrics.programs[{index}].program_id",
        )
        if program_id in seen_program_ids:
            issues.append(
                _issue(
                    rule_id="program_id_duplicate",
                    message="program ids must stay unique",
                    target=f"metrics.programs[{index}].program_id",
                    observed=program_id,
                )
            )
        seen_program_ids.add(program_id)

        program_label = _require_non_empty_text(
            item.get("program_label"),
            label=f"layout_sidecar.metrics.programs[{index}].program_label",
        )
        if program_label in seen_program_labels:
            issues.append(
                _issue(
                    rule_id="program_label_duplicate",
                    message="program labels must stay unique",
                    target=f"metrics.programs[{index}].program_label",
                    observed=program_label,
                )
            )
        seen_program_labels.add(program_label)

        _require_non_empty_text(
            item.get("lead_driver_label"),
            label=f"layout_sidecar.metrics.programs[{index}].lead_driver_label",
        )
        _require_non_empty_text(
            item.get("dominant_pathway_label"),
            label=f"layout_sidecar.metrics.programs[{index}].dominant_pathway_label",
        )
        _require_non_empty_text(
            item.get("action"),
            label=f"layout_sidecar.metrics.programs[{index}].action",
        )

        pathway_hit_count = _require_numeric(
            item.get("pathway_hit_count"),
            label=f"layout_sidecar.metrics.programs[{index}].pathway_hit_count",
        )
        if not float(pathway_hit_count).is_integer() or pathway_hit_count <= 0:
            issues.append(
                _issue(
                    rule_id="pathway_hit_count_invalid",
                    message="pathway_hit_count must stay a positive integer",
                    target=f"metrics.programs[{index}].pathway_hit_count",
                    observed=pathway_hit_count,
                )
            )

        priority_rank = _require_numeric(
            item.get("priority_rank"),
            label=f"layout_sidecar.metrics.programs[{index}].priority_rank",
        )
        if not float(priority_rank).is_integer() or priority_rank <= 0:
            issues.append(
                _issue(
                    rule_id="priority_rank_invalid",
                    message="priority_rank must stay a positive integer",
                    target=f"metrics.programs[{index}].priority_rank",
                    observed=priority_rank,
                )
            )
        else:
            normalized_priority_rank = int(priority_rank)
            if normalized_priority_rank in seen_priority_ranks:
                issues.append(
                    _issue(
                        rule_id="priority_rank_duplicate",
                        message="priority_rank values must stay unique",
                        target=f"metrics.programs[{index}].priority_rank",
                        observed=normalized_priority_rank,
                    )
                )
            seen_priority_ranks.add(normalized_priority_rank)

        priority_band = _require_non_empty_text(
            item.get("priority_band"),
            label=f"layout_sidecar.metrics.programs[{index}].priority_band",
        )
        if priority_band not in supported_priority_bands:
            issues.append(
                _issue(
                    rule_id="priority_band_invalid",
                    message="priority_band must stay within the fixed governance vocabulary",
                    target=f"metrics.programs[{index}].priority_band",
                    observed=priority_band,
                    expected=sorted(supported_priority_bands),
                )
            )

        verdict = _require_non_empty_text(
            item.get("verdict"),
            label=f"layout_sidecar.metrics.programs[{index}].verdict",
        )
        if verdict not in supported_verdicts:
            issues.append(
                _issue(
                    rule_id="verdict_invalid",
                    message="verdict must stay within the fixed governance vocabulary",
                    target=f"metrics.programs[{index}].verdict",
                    observed=verdict,
                    expected=sorted(supported_verdicts),
                )
            )

        for field_name, panel_box, box_type, rule_id in (
            ("priority_box_id", summary_panel, "priority_badge", "priority_box_missing"),
            ("verdict_box_id", summary_panel, "verdict_value", "verdict_box_missing"),
            ("support_box_id", summary_panel, "row_support", "support_box_missing"),
            ("action_box_id", summary_panel, "row_action", "action_box_missing"),
        ):
            box_id = str(item.get(field_name) or "").strip()
            if not box_id:
                issues.append(
                    _issue(
                        rule_id=rule_id,
                        message=f"{field_name} must reference an audited {box_type} box",
                        target=f"metrics.programs[{index}].{field_name}",
                    )
                )
                continue
            box = layout_boxes_by_id.get(box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id=rule_id,
                        message=f"{field_name} must reference an existing {box_type} box",
                        target=f"metrics.programs[{index}].{field_name}",
                        expected=box_id,
                    )
                )
                continue
            if panel_box is not None and not _box_within_box(box, panel_box):
                issues.append(
                    _issue(
                        rule_id="summary_box_out_of_panel",
                        message="summary governance boxes must stay inside the summary panel",
                        target=box_type,
                        box_refs=(box.box_id, panel_box.box_id),
                    )
                )

        row_label_box_id = str(item.get("row_label_box_id") or "").strip()
        if row_label_box_id:
            if layout_boxes_by_id.get(row_label_box_id) is None:
                issues.append(
                    _issue(
                        rule_id="row_label_box_missing",
                        message="row_label_box_id must reference an existing row_label box",
                        target=f"metrics.programs[{index}].row_label_box_id",
                        expected=row_label_box_id,
                    )
                )

        layer_supports = item.get("layer_supports")
        if not isinstance(layer_supports, list) or not layer_supports:
            issues.append(
                _issue(
                    rule_id="program_layer_support_coverage_mismatch",
                    message="each program must cover the fixed five-layer governance grid exactly once",
                    target=f"metrics.programs[{index}].layer_supports",
                    observed={"layers": 0},
                    expected={"layer_ids": expected_layer_ids},
                )
            )
            continue

        observed_layer_ids: list[str] = []
        for layer_index, layer_support in enumerate(layer_supports):
            if not isinstance(layer_support, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.programs[{index}].layer_supports[{layer_index}] must be an object"
                )
            layer_id = _require_non_empty_text(
                layer_support.get("layer_id"),
                label=f"layout_sidecar.metrics.programs[{index}].layer_supports[{layer_index}].layer_id",
            )
            observed_layer_ids.append(layer_id)

            effect_value = _require_numeric(
                layer_support.get("effect_value"),
                label=f"layout_sidecar.metrics.programs[{index}].layer_supports[{layer_index}].effect_value",
            )
            support_fraction = _require_numeric(
                layer_support.get("support_fraction"),
                label=f"layout_sidecar.metrics.programs[{index}].layer_supports[{layer_index}].support_fraction",
            )
            if not math.isfinite(effect_value):
                issues.append(
                    _issue(
                        rule_id="layer_effect_non_finite",
                        message="effect_value must stay finite",
                        target=f"metrics.programs[{index}].layer_supports[{layer_index}].effect_value",
                    )
                )
            if support_fraction < 0.0 or support_fraction > 1.0:
                issues.append(
                    _issue(
                        rule_id="layer_support_fraction_out_of_range",
                        message="support_fraction must stay within [0, 1]",
                        target=f"metrics.programs[{index}].layer_supports[{layer_index}].support_fraction",
                        observed=support_fraction,
                    )
                )

            cell_box_id = str(layer_support.get("cell_box_id") or "").strip()
            if not cell_box_id:
                issues.append(
                    _issue(
                        rule_id="evidence_cell_box_missing",
                        message="layer supports must reference an audited evidence_cell box",
                        target=f"metrics.programs[{index}].layer_supports[{layer_index}].cell_box_id",
                    )
                )
                continue
            cell_box = layout_boxes_by_id.get(cell_box_id)
            if cell_box is None:
                issues.append(
                    _issue(
                        rule_id="evidence_cell_box_missing",
                        message="layer supports must reference an existing evidence_cell box",
                        target=f"metrics.programs[{index}].layer_supports[{layer_index}].cell_box_id",
                        expected=cell_box_id,
                    )
                )
                continue
            if evidence_panel is not None and not _box_within_box(cell_box, evidence_panel):
                issues.append(
                    _issue(
                        rule_id="evidence_cell_out_of_panel",
                        message="evidence cells must stay within the evidence panel",
                        target="evidence_cell",
                        box_refs=(cell_box.box_id, evidence_panel.box_id),
                    )
                )

        if tuple(observed_layer_ids) != expected_layer_ids:
            issues.append(
                _issue(
                    rule_id="program_layer_support_coverage_mismatch",
                    message="each program must cover the fixed five-layer governance grid exactly once",
                    target=f"metrics.programs[{index}].layer_supports",
                    observed={"layer_ids": tuple(observed_layer_ids)},
                    expected={"layer_ids": expected_layer_ids},
                )
            )

    return issues


def _check_publication_center_coverage_batch_transportability_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=("panel", "panel_label", "panel_title", "subplot_x_axis_title", "card_label", "card_value"),
        )
    )

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 3:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="center coverage batch transportability panel requires exactly three panel boxes",
                target="panel_boxes",
                expected={"count": 3},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    panel_label_to_panel_id = {
        "A": "panel_coverage",
        "B": "panel_batch",
        "C": "panel_transportability",
    }
    title_boxes = {
        "coverage_panel_title": "panel_coverage",
        "batch_panel_title": "panel_batch",
        "transportability_panel_title": "panel_transportability",
    }
    for panel_label, panel_id in panel_label_to_panel_id.items():
        label_box = layout_boxes_by_id.get(f"panel_label_{panel_label}")
        panel_box = panel_boxes_by_id.get(panel_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="center coverage batch transportability panel requires the fixed three-panel layout",
                    target="panel_boxes",
                    expected=panel_id,
                )
            )
            continue
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="center coverage batch transportability panel labels must be present for every panel",
                    target="panel_label",
                    expected=f"panel_label_{panel_label}",
                )
            )
            continue
        if not _box_within_box(label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="center coverage batch transportability panel labels must stay within their parent panel",
                    target="panel_label",
                    box_refs=(label_box.box_id, panel_box.box_id),
                )
            )

    for title_box_id, panel_id in title_boxes.items():
        title_box = layout_boxes_by_id.get(title_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="center coverage batch transportability panel requires all three panel titles",
                    target="panel_title",
                    expected=title_box_id,
                )
            )
            continue
        if panel_box is not None:
            aligned_horizontally = title_box.x0 >= panel_box.x0 - 0.02 and title_box.x1 <= panel_box.x1 + 0.02
            close_to_panel_top = title_box.y0 >= panel_box.y0 - 0.02 and title_box.y1 <= panel_box.y1 + 0.08
            if not (aligned_horizontally and close_to_panel_top):
                issues.append(
                    _issue(
                        rule_id="panel_title_out_of_panel",
                        message="center coverage batch transportability panel titles must stay tightly aligned with their parent panel",
                        target="panel_title",
                        box_refs=(title_box.box_id, panel_box.box_id),
                    )
                )

    axis_title_pairs = (
        ("coverage_x_axis_title", "panel_coverage"),
        ("batch_x_axis_title", "panel_batch"),
        ("batch_y_axis_title", "panel_batch"),
    )
    for axis_box_id, panel_id in axis_title_pairs:
        axis_box = layout_boxes_by_id.get(axis_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if axis_box is None:
            issues.append(
                _issue(
                    rule_id="axis_title_missing",
                    message="center coverage batch transportability panel must expose the bounded axis-title surface",
                    target="subplot_axis_title",
                    expected=axis_box_id,
                )
            )
            continue
        if panel_box is not None:
            if axis_box.box_id.endswith("_y_axis_title"):
                axis_center_y = (axis_box.y0 + axis_box.y1) / 2.0
                aligned_with_panel = (
                    panel_box.y0 <= axis_center_y <= panel_box.y1
                    and axis_box.x0 >= panel_box.x0 - 0.12
                    and axis_box.x1 <= panel_box.x1 + 0.02
                )
            else:
                axis_center_x = (axis_box.x0 + axis_box.x1) / 2.0
                aligned_with_panel = (
                    panel_box.x0 <= axis_center_x <= panel_box.x1
                    and axis_box.y0 >= panel_box.y0 - 0.10
                    and axis_box.y1 <= panel_box.y1 + 0.02
                )
            if not aligned_with_panel:
                issues.append(
                    _issue(
                        rule_id="axis_title_out_of_panel",
                        message="center coverage batch transportability panel axis titles must stay tightly aligned with their parent panel",
                        target=axis_box.box_type,
                        box_refs=(axis_box.box_id, panel_box.box_id),
                    )
                )

    if not _boxes_of_type(sidecar.guide_boxes, "reference_line"):
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="center coverage batch transportability panel requires a batch threshold reference line",
                target="reference_line",
            )
        )
    if not _boxes_of_type(sidecar.guide_boxes, "colorbar"):
        issues.append(
            _issue(
                rule_id="colorbar_missing",
                message="center coverage batch transportability panel requires a batch colorbar guide box",
                target="colorbar",
            )
        )

    batch_threshold = _require_numeric(sidecar.metrics.get("batch_threshold"), label="layout_sidecar.metrics.batch_threshold")
    if not math.isfinite(batch_threshold) or batch_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="batch_threshold_invalid",
                message="batch_threshold must be positive and finite",
                target="metrics.batch_threshold",
                observed=batch_threshold,
            )
        )

    center_rows = sidecar.metrics.get("center_rows")
    if not isinstance(center_rows, list) or not center_rows:
        issues.append(
            _issue(
                rule_id="center_rows_missing",
                message="center_rows must be non-empty",
                target="metrics.center_rows",
            )
        )
    else:
        seen_center_ids: set[str] = set()
        seen_center_labels: set[str] = set()
        for index, item in enumerate(center_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.center_rows[{index}] must be an object")
            center_id = str(item.get("center_id") or "").strip()
            center_label = str(item.get("center_label") or "").strip()
            cohort_role = str(item.get("cohort_role") or "").strip()
            if not center_id:
                issues.append(_issue(rule_id="center_row_id_missing", message="center row ids must be non-empty", target=f"metrics.center_rows[{index}].center_id"))
            elif center_id in seen_center_ids:
                issues.append(_issue(rule_id="duplicate_center_row_id", message="center row ids must be unique", target="metrics.center_rows", observed=center_id))
            else:
                seen_center_ids.add(center_id)
            if not center_label:
                issues.append(_issue(rule_id="center_row_label_missing", message="center row labels must be non-empty", target=f"metrics.center_rows[{index}].center_label"))
            elif center_label in seen_center_labels:
                issues.append(_issue(rule_id="duplicate_center_row_label", message="center row labels must be unique", target="metrics.center_rows", observed=center_label))
            else:
                seen_center_labels.add(center_label)
            if not cohort_role:
                issues.append(_issue(rule_id="center_row_cohort_role_missing", message="center row cohort roles must be non-empty", target=f"metrics.center_rows[{index}].cohort_role"))
            support_count = _require_numeric(item.get("support_count"), label=f"layout_sidecar.metrics.center_rows[{index}].support_count")
            event_count = _require_numeric(item.get("event_count"), label=f"layout_sidecar.metrics.center_rows[{index}].event_count")
            if not float(support_count).is_integer() or support_count <= 0:
                issues.append(_issue(rule_id="center_support_count_invalid", message="center support counts must be positive integers", target=f"metrics.center_rows[{index}].support_count", observed=support_count))
            if not float(event_count).is_integer() or event_count < 0:
                issues.append(_issue(rule_id="center_event_count_invalid", message="center event counts must be non-negative integers", target=f"metrics.center_rows[{index}].event_count", observed=event_count))
            elif event_count > support_count:
                issues.append(_issue(rule_id="center_event_count_exceeds_support", message="center event counts must not exceed support counts", target=f"metrics.center_rows[{index}].event_count", observed={"event_count": event_count, "support_count": support_count}))

    batch_rows = sidecar.metrics.get("batch_rows")
    batch_columns = sidecar.metrics.get("batch_columns")
    batch_cells = sidecar.metrics.get("batch_cells")
    normalized_row_labels: list[str] = []
    normalized_column_labels: list[str] = []
    if not isinstance(batch_rows, list) or not batch_rows:
        issues.append(_issue(rule_id="batch_rows_missing", message="batch_rows must be non-empty", target="metrics.batch_rows"))
    else:
        seen_row_labels: set[str] = set()
        for index, item in enumerate(batch_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_rows[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(_issue(rule_id="batch_row_label_missing", message="batch row labels must be non-empty", target=f"metrics.batch_rows[{index}].label"))
                continue
            if label in seen_row_labels:
                issues.append(_issue(rule_id="duplicate_batch_row_label", message="batch row labels must be unique", target="metrics.batch_rows", observed=label))
            else:
                seen_row_labels.add(label)
                normalized_row_labels.append(label)
    if not isinstance(batch_columns, list) or not batch_columns:
        issues.append(_issue(rule_id="batch_columns_missing", message="batch_columns must be non-empty", target="metrics.batch_columns"))
    else:
        seen_column_labels: set[str] = set()
        for index, item in enumerate(batch_columns):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_columns[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(_issue(rule_id="batch_column_label_missing", message="batch column labels must be non-empty", target=f"metrics.batch_columns[{index}].label"))
                continue
            if label in seen_column_labels:
                issues.append(_issue(rule_id="duplicate_batch_column_label", message="batch column labels must be unique", target="metrics.batch_columns", observed=label))
            else:
                seen_column_labels.add(label)
                normalized_column_labels.append(label)
    if not isinstance(batch_cells, list) or not batch_cells:
        issues.append(_issue(rule_id="batch_cells_missing", message="batch_cells must be non-empty", target="metrics.batch_cells"))
    else:
        expected_rows = set(normalized_row_labels)
        expected_columns = set(normalized_column_labels)
        seen_coordinates: set[tuple[str, str]] = set()
        observed_rows: set[str] = set()
        observed_columns: set[str] = set()
        for index, item in enumerate(batch_cells):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_cells[{index}] must be an object")
            column_label = str(item.get("x") or "").strip()
            row_label = str(item.get("y") or "").strip()
            if not column_label or not row_label:
                issues.append(_issue(rule_id="batch_cell_coordinate_missing", message="batch cells must declare x and y labels", target=f"metrics.batch_cells[{index}]"))
                continue
            if expected_columns and column_label not in expected_columns:
                issues.append(_issue(rule_id="batch_cell_unknown_column", message="batch cells must reference declared batch columns", target=f"metrics.batch_cells[{index}].x", observed=column_label))
            if expected_rows and row_label not in expected_rows:
                issues.append(_issue(rule_id="batch_cell_unknown_row", message="batch cells must reference declared batch rows", target=f"metrics.batch_cells[{index}].y", observed=row_label))
            coordinate = (column_label, row_label)
            if coordinate in seen_coordinates:
                issues.append(_issue(rule_id="duplicate_batch_cell_coordinate", message="batch grid coordinates must be unique", target="metrics.batch_cells", observed={"x": column_label, "y": row_label}))
            else:
                seen_coordinates.add(coordinate)
            observed_rows.add(row_label)
            observed_columns.add(column_label)
            value = _require_numeric(item.get("value"), label=f"layout_sidecar.metrics.batch_cells[{index}].value")
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                issues.append(_issue(rule_id="batch_cell_value_invalid", message="batch cell values must stay within [0, 1]", target=f"metrics.batch_cells[{index}].value", observed=value))
        if expected_rows and observed_rows != expected_rows:
            issues.append(_issue(rule_id="declared_batch_rows_mismatch", message="declared batch rows must match observed cell rows", target="metrics.batch_rows", expected=sorted(expected_rows), observed=sorted(observed_rows)))
        if expected_columns and observed_columns != expected_columns:
            issues.append(_issue(rule_id="declared_batch_columns_mismatch", message="declared batch columns must match observed cell columns", target="metrics.batch_columns", expected=sorted(expected_columns), observed=sorted(observed_columns)))
        if expected_rows and expected_columns and len(seen_coordinates) != len(expected_rows) * len(expected_columns):
            issues.append(_issue(rule_id="declared_batch_grid_incomplete", message="declared batch grid must be complete", target="metrics.batch_cells", expected={"count": len(expected_rows) * len(expected_columns)}, observed={"count": len(seen_coordinates)}))

    transportability_cards = sidecar.metrics.get("transportability_cards")
    transport_panel = panel_boxes_by_id.get("panel_transportability")
    if not isinstance(transportability_cards, list) or not transportability_cards:
        issues.append(_issue(rule_id="transportability_cards_missing", message="transportability_cards must be non-empty", target="metrics.transportability_cards"))
    else:
        seen_card_ids: set[str] = set()
        for index, item in enumerate(transportability_cards):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.transportability_cards[{index}] must be an object")
            card_id = str(item.get("card_id") or "").strip()
            label_box_id = str(item.get("label_box_id") or "").strip()
            value_box_id = str(item.get("value_box_id") or "").strip()
            if not card_id:
                issues.append(_issue(rule_id="transportability_card_id_missing", message="transportability card ids must be non-empty", target=f"metrics.transportability_cards[{index}].card_id"))
            elif card_id in seen_card_ids:
                issues.append(_issue(rule_id="duplicate_transportability_card_id", message="transportability card ids must be unique", target="metrics.transportability_cards", observed=card_id))
            else:
                seen_card_ids.add(card_id)
            label_box = layout_boxes_by_id.get(label_box_id)
            value_box = layout_boxes_by_id.get(value_box_id)
            if label_box is None:
                issues.append(_issue(rule_id="transportability_card_label_missing", message="transportability cards must reference an existing card_label box", target=f"metrics.transportability_cards[{index}].label_box_id", expected=label_box_id))
            elif transport_panel is not None and not _box_within_box(label_box, transport_panel):
                issues.append(_issue(rule_id="transportability_card_out_of_panel", message="transportability card labels must stay within the transportability panel", target="card_label", box_refs=(label_box.box_id, transport_panel.box_id)))
            if value_box is None:
                issues.append(_issue(rule_id="transportability_card_value_missing", message="transportability cards must reference an existing card_value box", target=f"metrics.transportability_cards[{index}].value_box_id", expected=value_box_id))
            elif transport_panel is not None and not _box_within_box(value_box, transport_panel):
                issues.append(_issue(rule_id="transportability_card_out_of_panel", message="transportability card values must stay within the transportability panel", target="card_value", box_refs=(value_box.box_id, transport_panel.box_id)))

    return issues


def _check_publication_transportability_recalibration_governance_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel",
                "panel_label",
                "panel_title",
                "subplot_x_axis_title",
                "row_label",
                "row_metric",
                "row_action",
            ),
        )
    )

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 3:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="transportability recalibration governance panel requires exactly three panel boxes",
                target="panel_boxes",
                expected={"count": 3},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    panel_label_to_panel_id = {
        "A": "panel_coverage",
        "B": "panel_batch",
        "C": "panel_recalibration",
    }
    title_boxes = {
        "coverage_panel_title": "panel_coverage",
        "batch_panel_title": "panel_batch",
        "recalibration_panel_title": "panel_recalibration",
    }
    for panel_label, panel_id in panel_label_to_panel_id.items():
        label_box = layout_boxes_by_id.get(f"panel_label_{panel_label}")
        panel_box = panel_boxes_by_id.get(panel_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="transportability recalibration governance panel requires the fixed three-panel layout",
                    target="panel_boxes",
                    expected=panel_id,
                )
            )
            continue
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="transportability recalibration governance panel labels must be present for every panel",
                    target="panel_label",
                    expected=f"panel_label_{panel_label}",
                )
            )
            continue
        if not _box_within_box(label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="transportability recalibration governance panel labels must stay within their parent panel",
                    target="panel_label",
                    box_refs=(label_box.box_id, panel_box.box_id),
                )
            )

    for title_box_id, panel_id in title_boxes.items():
        title_box = layout_boxes_by_id.get(title_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="transportability recalibration governance panel requires all three panel titles",
                    target="panel_title",
                    expected=title_box_id,
                )
            )
            continue
        if panel_box is not None:
            aligned_horizontally = title_box.x0 >= panel_box.x0 - 0.02 and title_box.x1 <= panel_box.x1 + 0.02
            close_to_panel_top = title_box.y0 >= panel_box.y0 - 0.02 and title_box.y1 <= panel_box.y1 + 0.08
            if not (aligned_horizontally and close_to_panel_top):
                issues.append(
                    _issue(
                        rule_id="panel_title_out_of_panel",
                        message="transportability recalibration governance panel titles must stay tightly aligned with their parent panel",
                        target="panel_title",
                        box_refs=(title_box.box_id, panel_box.box_id),
                    )
                )

    axis_title_pairs = (
        ("coverage_x_axis_title", "panel_coverage"),
        ("batch_x_axis_title", "panel_batch"),
        ("batch_y_axis_title", "panel_batch"),
    )
    for axis_box_id, panel_id in axis_title_pairs:
        axis_box = layout_boxes_by_id.get(axis_box_id)
        panel_box = panel_boxes_by_id.get(panel_id)
        if axis_box is None:
            issues.append(
                _issue(
                    rule_id="axis_title_missing",
                    message="transportability recalibration governance panel must expose the bounded axis-title surface",
                    target="subplot_axis_title",
                    expected=axis_box_id,
                )
            )
            continue
        if panel_box is not None:
            if axis_box.box_id.endswith("_y_axis_title"):
                axis_center_y = (axis_box.y0 + axis_box.y1) / 2.0
                aligned_with_panel = (
                    panel_box.y0 <= axis_center_y <= panel_box.y1
                    and axis_box.x0 >= panel_box.x0 - 0.12
                    and axis_box.x1 <= panel_box.x1 + 0.02
                )
            else:
                axis_center_x = (axis_box.x0 + axis_box.x1) / 2.0
                aligned_with_panel = (
                    panel_box.x0 <= axis_center_x <= panel_box.x1
                    and axis_box.y0 >= panel_box.y0 - 0.10
                    and axis_box.y1 <= panel_box.y1 + 0.02
                )
            if not aligned_with_panel:
                issues.append(
                    _issue(
                        rule_id="axis_title_out_of_panel",
                        message="transportability recalibration governance panel axis titles must stay tightly aligned with their parent panel",
                        target=axis_box.box_type,
                        box_refs=(axis_box.box_id, panel_box.box_id),
                    )
                )

    if not _boxes_of_type(sidecar.guide_boxes, "reference_line"):
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="transportability recalibration governance panel requires a batch threshold reference line",
                target="reference_line",
            )
        )
    if not _boxes_of_type(sidecar.guide_boxes, "colorbar"):
        issues.append(
            _issue(
                rule_id="colorbar_missing",
                message="transportability recalibration governance panel requires a batch colorbar guide box",
                target="colorbar",
            )
        )

    batch_threshold = _require_numeric(sidecar.metrics.get("batch_threshold"), label="layout_sidecar.metrics.batch_threshold")
    if not math.isfinite(batch_threshold) or batch_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="batch_threshold_invalid",
                message="batch_threshold must be positive and finite",
                target="metrics.batch_threshold",
                observed=batch_threshold,
            )
        )

    center_rows = sidecar.metrics.get("center_rows")
    expected_center_ids: set[str] = set()
    if not isinstance(center_rows, list) or not center_rows:
        issues.append(
            _issue(
                rule_id="center_rows_missing",
                message="center_rows must be non-empty",
                target="metrics.center_rows",
            )
        )
    else:
        seen_center_ids: set[str] = set()
        seen_center_labels: set[str] = set()
        for index, item in enumerate(center_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.center_rows[{index}] must be an object")
            center_id = str(item.get("center_id") or "").strip()
            center_label = str(item.get("center_label") or "").strip()
            cohort_role = str(item.get("cohort_role") or "").strip()
            if not center_id:
                issues.append(_issue(rule_id="center_row_id_missing", message="center row ids must be non-empty", target=f"metrics.center_rows[{index}].center_id"))
            elif center_id in seen_center_ids:
                issues.append(_issue(rule_id="duplicate_center_row_id", message="center row ids must be unique", target="metrics.center_rows", observed=center_id))
            else:
                seen_center_ids.add(center_id)
                expected_center_ids.add(center_id)
            if not center_label:
                issues.append(_issue(rule_id="center_row_label_missing", message="center row labels must be non-empty", target=f"metrics.center_rows[{index}].center_label"))
            elif center_label in seen_center_labels:
                issues.append(_issue(rule_id="duplicate_center_row_label", message="center row labels must be unique", target="metrics.center_rows", observed=center_label))
            else:
                seen_center_labels.add(center_label)
            if not cohort_role:
                issues.append(_issue(rule_id="center_row_cohort_role_missing", message="center row cohort roles must be non-empty", target=f"metrics.center_rows[{index}].cohort_role"))
            support_count = _require_numeric(item.get("support_count"), label=f"layout_sidecar.metrics.center_rows[{index}].support_count")
            event_count = _require_numeric(item.get("event_count"), label=f"layout_sidecar.metrics.center_rows[{index}].event_count")
            if not float(support_count).is_integer() or support_count <= 0:
                issues.append(_issue(rule_id="center_support_count_invalid", message="center support counts must be positive integers", target=f"metrics.center_rows[{index}].support_count", observed=support_count))
            if not float(event_count).is_integer() or event_count < 0:
                issues.append(_issue(rule_id="center_event_count_invalid", message="center event counts must be non-negative integers", target=f"metrics.center_rows[{index}].event_count", observed=event_count))
            elif event_count > support_count:
                issues.append(_issue(rule_id="center_event_count_exceeds_support", message="center event counts must not exceed support counts", target=f"metrics.center_rows[{index}].event_count", observed={"event_count": event_count, "support_count": support_count}))

    batch_rows = sidecar.metrics.get("batch_rows")
    batch_columns = sidecar.metrics.get("batch_columns")
    batch_cells = sidecar.metrics.get("batch_cells")
    normalized_row_labels: list[str] = []
    normalized_column_labels: list[str] = []
    if not isinstance(batch_rows, list) or not batch_rows:
        issues.append(_issue(rule_id="batch_rows_missing", message="batch_rows must be non-empty", target="metrics.batch_rows"))
    else:
        seen_row_labels: set[str] = set()
        for index, item in enumerate(batch_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_rows[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(_issue(rule_id="batch_row_label_missing", message="batch row labels must be non-empty", target=f"metrics.batch_rows[{index}].label"))
                continue
            if label in seen_row_labels:
                issues.append(_issue(rule_id="duplicate_batch_row_label", message="batch row labels must be unique", target="metrics.batch_rows", observed=label))
            else:
                seen_row_labels.add(label)
                normalized_row_labels.append(label)
    if not isinstance(batch_columns, list) or not batch_columns:
        issues.append(_issue(rule_id="batch_columns_missing", message="batch_columns must be non-empty", target="metrics.batch_columns"))
    else:
        seen_column_labels: set[str] = set()
        for index, item in enumerate(batch_columns):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_columns[{index}] must be an object")
            label = str(item.get("label") or "").strip()
            if not label:
                issues.append(_issue(rule_id="batch_column_label_missing", message="batch column labels must be non-empty", target=f"metrics.batch_columns[{index}].label"))
                continue
            if label in seen_column_labels:
                issues.append(_issue(rule_id="duplicate_batch_column_label", message="batch column labels must be unique", target="metrics.batch_columns", observed=label))
            else:
                seen_column_labels.add(label)
                normalized_column_labels.append(label)
    if not isinstance(batch_cells, list) or not batch_cells:
        issues.append(_issue(rule_id="batch_cells_missing", message="batch_cells must be non-empty", target="metrics.batch_cells"))
    else:
        expected_rows = set(normalized_row_labels)
        expected_columns = set(normalized_column_labels)
        seen_coordinates: set[tuple[str, str]] = set()
        observed_rows: set[str] = set()
        observed_columns: set[str] = set()
        for index, item in enumerate(batch_cells):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.batch_cells[{index}] must be an object")
            column_label = str(item.get("x") or "").strip()
            row_label = str(item.get("y") or "").strip()
            if not column_label or not row_label:
                issues.append(_issue(rule_id="batch_cell_coordinate_missing", message="batch cells must declare x and y labels", target=f"metrics.batch_cells[{index}]"))
                continue
            if expected_columns and column_label not in expected_columns:
                issues.append(_issue(rule_id="batch_cell_unknown_column", message="batch cells must reference declared batch columns", target=f"metrics.batch_cells[{index}].x", observed=column_label))
            if expected_rows and row_label not in expected_rows:
                issues.append(_issue(rule_id="batch_cell_unknown_row", message="batch cells must reference declared batch rows", target=f"metrics.batch_cells[{index}].y", observed=row_label))
            coordinate = (column_label, row_label)
            if coordinate in seen_coordinates:
                issues.append(_issue(rule_id="duplicate_batch_cell_coordinate", message="batch grid coordinates must be unique", target="metrics.batch_cells", observed={"x": column_label, "y": row_label}))
            else:
                seen_coordinates.add(coordinate)
            observed_rows.add(row_label)
            observed_columns.add(column_label)
            value = _require_numeric(item.get("value"), label=f"layout_sidecar.metrics.batch_cells[{index}].value")
            if not math.isfinite(value) or value < 0.0 or value > 1.0:
                issues.append(_issue(rule_id="batch_cell_value_invalid", message="batch cell values must stay within [0, 1]", target=f"metrics.batch_cells[{index}].value", observed=value))
        if expected_rows and observed_rows != expected_rows:
            issues.append(_issue(rule_id="declared_batch_rows_mismatch", message="declared batch rows must match observed cell rows", target="metrics.batch_rows", expected=sorted(expected_rows), observed=sorted(observed_rows)))
        if expected_columns and observed_columns != expected_columns:
            issues.append(_issue(rule_id="declared_batch_columns_mismatch", message="declared batch columns must match observed cell columns", target="metrics.batch_columns", expected=sorted(expected_columns), observed=sorted(observed_columns)))
        if expected_rows and expected_columns and len(seen_coordinates) != len(expected_rows) * len(expected_columns):
            issues.append(_issue(rule_id="declared_batch_grid_incomplete", message="declared batch grid must be complete", target="metrics.batch_cells", expected={"count": len(expected_rows) * len(expected_columns)}, observed={"count": len(seen_coordinates)}))

    slope_acceptance_lower = _require_numeric(
        sidecar.metrics.get("slope_acceptance_lower"),
        label="layout_sidecar.metrics.slope_acceptance_lower",
    )
    slope_acceptance_upper = _require_numeric(
        sidecar.metrics.get("slope_acceptance_upper"),
        label="layout_sidecar.metrics.slope_acceptance_upper",
    )
    if (
        not math.isfinite(slope_acceptance_lower)
        or not math.isfinite(slope_acceptance_upper)
        or slope_acceptance_lower <= 0.0
        or slope_acceptance_upper <= 0.0
        or slope_acceptance_lower >= slope_acceptance_upper
    ):
        issues.append(
            _issue(
                rule_id="slope_acceptance_band_invalid",
                message="slope acceptance band must be positive, finite, and ordered",
                target="metrics.slope_acceptance_lower",
                observed={"lower": slope_acceptance_lower, "upper": slope_acceptance_upper},
            )
        )
    oe_ratio_acceptance_lower = _require_numeric(
        sidecar.metrics.get("oe_ratio_acceptance_lower"),
        label="layout_sidecar.metrics.oe_ratio_acceptance_lower",
    )
    oe_ratio_acceptance_upper = _require_numeric(
        sidecar.metrics.get("oe_ratio_acceptance_upper"),
        label="layout_sidecar.metrics.oe_ratio_acceptance_upper",
    )
    if (
        not math.isfinite(oe_ratio_acceptance_lower)
        or not math.isfinite(oe_ratio_acceptance_upper)
        or oe_ratio_acceptance_lower <= 0.0
        or oe_ratio_acceptance_upper <= 0.0
        or oe_ratio_acceptance_lower >= oe_ratio_acceptance_upper
    ):
        issues.append(
            _issue(
                rule_id="oe_ratio_acceptance_band_invalid",
                message="oe_ratio acceptance band must be positive, finite, and ordered",
                target="metrics.oe_ratio_acceptance_lower",
                observed={"lower": oe_ratio_acceptance_lower, "upper": oe_ratio_acceptance_upper},
            )
        )

    recalibration_rows = sidecar.metrics.get("recalibration_rows")
    recalibration_panel = panel_boxes_by_id.get("panel_recalibration")
    if not isinstance(recalibration_rows, list) or not recalibration_rows:
        issues.append(
            _issue(
                rule_id="recalibration_rows_missing",
                message="recalibration_rows must be non-empty",
                target="metrics.recalibration_rows",
            )
        )
    else:
        seen_center_ids: set[str] = set()
        for index, item in enumerate(recalibration_rows):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.recalibration_rows[{index}] must be an object")
            center_id = str(item.get("center_id") or "").strip()
            if not center_id:
                issues.append(_issue(rule_id="recalibration_center_id_missing", message="recalibration center ids must be non-empty", target=f"metrics.recalibration_rows[{index}].center_id"))
            elif center_id in seen_center_ids:
                issues.append(_issue(rule_id="duplicate_recalibration_center_id", message="recalibration center ids must be unique", target="metrics.recalibration_rows", observed=center_id))
            else:
                seen_center_ids.add(center_id)
            if expected_center_ids and center_id not in expected_center_ids:
                issues.append(_issue(rule_id="recalibration_center_unknown", message="recalibration rows must reference declared centers", target=f"metrics.recalibration_rows[{index}].center_id", observed=center_id))
            slope = _require_numeric(item.get("slope"), label=f"layout_sidecar.metrics.recalibration_rows[{index}].slope")
            oe_ratio = _require_numeric(item.get("oe_ratio"), label=f"layout_sidecar.metrics.recalibration_rows[{index}].oe_ratio")
            if not math.isfinite(slope) or slope <= 0.0:
                issues.append(_issue(rule_id="recalibration_slope_invalid", message="recalibration slopes must be positive and finite", target=f"metrics.recalibration_rows[{index}].slope", observed=slope))
            if not math.isfinite(oe_ratio) or oe_ratio <= 0.0:
                issues.append(_issue(rule_id="recalibration_oe_ratio_invalid", message="recalibration oe ratios must be positive and finite", target=f"metrics.recalibration_rows[{index}].oe_ratio", observed=oe_ratio))
            label_box_id = str(item.get("label_box_id") or "").strip()
            slope_box_id = str(item.get("slope_box_id") or "").strip()
            oe_ratio_box_id = str(item.get("oe_ratio_box_id") or "").strip()
            action_box_id = str(item.get("action_box_id") or "").strip()
            row_boxes = (
                ("row_label", label_box_id),
                ("row_metric", slope_box_id),
                ("row_metric", oe_ratio_box_id),
                ("row_action", action_box_id),
            )
            for box_type, box_id in row_boxes:
                box = layout_boxes_by_id.get(box_id)
                if box is None:
                    issues.append(_issue(rule_id="recalibration_row_box_missing", message="recalibration rows must reference existing layout boxes", target=f"metrics.recalibration_rows[{index}]", expected=box_id))
                elif recalibration_panel is not None and not _box_within_box(box, recalibration_panel):
                    issues.append(_issue(rule_id="recalibration_row_out_of_panel", message="recalibration row boxes must stay within the recalibration panel", target=box_type, box_refs=(box.box_id, recalibration_panel.box_id)))
        if expected_center_ids and seen_center_ids != expected_center_ids:
            issues.append(
                _issue(
                    rule_id="recalibration_rows_incomplete",
                    message="recalibration rows must cover every declared center exactly once",
                    target="metrics.recalibration_rows",
                    expected=sorted(expected_center_ids),
                    observed=sorted(seen_center_ids),
                )
            )

    return issues


def _check_publication_workflow_fact_sheet_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=("panel", "panel_label", "section_title", "fact_label", "fact_value"),
        )
    )

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 4:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="workflow fact sheet requires exactly four panel boxes",
                target="panel_boxes",
                expected={"count": 4},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"panel_label", "section_title", "fact_label", "fact_value"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    sections = sidecar.metrics.get("sections")
    if not isinstance(sections, list) or not sections:
        issues.append(
            _issue(
                rule_id="sections_missing",
                message="workflow fact sheet qc requires non-empty section metrics",
                target="metrics.sections",
            )
        )
        return issues

    if len(sections) != 4:
        issues.append(
            _issue(
                rule_id="section_count_mismatch",
                message="workflow fact sheet requires exactly four declared sections",
                target="metrics.sections",
                expected={"count": 4},
                observed={"count": len(sections)},
            )
        )

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    expected_layout_roles = {"top_left", "top_right", "bottom_left", "bottom_right"}
    seen_section_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_layout_roles: set[str] = set()

    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"layout_sidecar.metrics.sections[{section_index}] must be an object")
        section_target = f"metrics.sections[{section_index}]"
        section_id = str(section.get("section_id") or "").strip()
        panel_label = str(section.get("panel_label") or "").strip()
        layout_role = str(section.get("layout_role") or "").strip()
        panel_box_id = str(section.get("panel_box_id") or "").strip()
        title_box_id = str(section.get("title_box_id") or "").strip()
        panel_label_box_id = str(section.get("panel_label_box_id") or "").strip()

        if not section_id:
            issues.append(
                _issue(
                    rule_id="section_id_missing",
                    message="workflow fact sheet sections require non-empty section_id",
                    target=f"{section_target}.section_id",
                )
            )
        elif section_id in seen_section_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_section_id",
                    message="workflow fact sheet section_id values must be unique",
                    target="metrics.sections",
                    observed=section_id,
                )
            )
        else:
            seen_section_ids.add(section_id)

        if not panel_label:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="workflow fact sheet sections require non-empty panel_label metrics",
                    target=f"{section_target}.panel_label",
                )
            )
        elif panel_label in seen_panel_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_panel_label",
                    message="workflow fact sheet panel labels must be unique",
                    target="metrics.sections",
                    observed=panel_label,
                )
            )
        else:
            seen_panel_labels.add(panel_label)

        if not layout_role:
            issues.append(
                _issue(
                    rule_id="layout_role_missing",
                    message="workflow fact sheet sections require non-empty layout_role",
                    target=f"{section_target}.layout_role",
                )
            )
        elif layout_role not in expected_layout_roles:
            issues.append(
                _issue(
                    rule_id="section_layout_role_invalid",
                    message="workflow fact sheet layout_role must match the fixed four-panel grid",
                    target=f"{section_target}.layout_role",
                    observed=layout_role,
                    expected=sorted(expected_layout_roles),
                )
            )
        elif layout_role in seen_layout_roles:
            issues.append(
                _issue(
                    rule_id="duplicate_layout_role",
                    message="workflow fact sheet layout_role values must be unique",
                    target="metrics.sections",
                    observed=layout_role,
                )
            )
        else:
            seen_layout_roles.add(layout_role)

        parent_panel = panel_boxes_by_id.get(panel_box_id)
        if parent_panel is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="workflow fact sheet sections must reference an existing panel box",
                    target=f"{section_target}.panel_box_id",
                    expected=panel_box_id,
                )
            )

        title_box = layout_boxes_by_id.get(title_box_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="section_title_missing",
                    message="workflow fact sheet sections must reference an existing section_title box",
                    target=f"{section_target}.title_box_id",
                    expected=title_box_id,
                )
            )
        elif parent_panel is not None and not _box_within_box(title_box, parent_panel):
            issues.append(
                _issue(
                    rule_id="section_title_out_of_panel",
                    message="workflow fact sheet section titles must stay within the parent panel",
                    target="section_title",
                    box_refs=(title_box.box_id, parent_panel.box_id),
                )
            )

        label_box = layout_boxes_by_id.get(panel_label_box_id)
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="workflow fact sheet sections must reference an existing panel label box",
                    target=f"{section_target}.panel_label_box_id",
                    expected=panel_label_box_id,
                )
            )
        elif parent_panel is not None:
            panel_width = max(parent_panel.x1 - parent_panel.x0, 1e-9)
            panel_height = max(parent_panel.y1 - parent_panel.y0, 1e-9)
            if not _box_within_box(label_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="panel_label_out_of_panel",
                        message="workflow fact sheet panel labels must stay within the parent panel",
                        target="panel_label",
                        box_refs=(label_box.box_id, parent_panel.box_id),
                    )
                )
            else:
                anchored_near_left = label_box.x0 <= parent_panel.x0 + panel_width * 0.10
                anchored_near_top = (
                    label_box.y0 <= parent_panel.y0 + panel_height * 0.12
                    or label_box.y1 >= parent_panel.y1 - panel_height * 0.10
                )
                if anchored_near_left and anchored_near_top:
                    pass
                else:
                    issues.append(
                        _issue(
                            rule_id="panel_label_anchor_drift",
                            message="workflow fact sheet panel labels must stay near the parent panel top-left anchor",
                            target="panel_label",
                            box_refs=(label_box.box_id, parent_panel.box_id),
                        )
                    )

        facts = section.get("facts")
        if not isinstance(facts, list) or not facts:
            issues.append(
                _issue(
                    rule_id="facts_missing",
                    message="workflow fact sheet sections require a non-empty facts list",
                    target=f"{section_target}.facts",
                )
            )
            continue

        seen_fact_ids: set[str] = set()
        for fact_index, fact in enumerate(facts):
            if not isinstance(fact, dict):
                raise ValueError(f"{section_target}.facts[{fact_index}] must be an object")
            fact_target = f"{section_target}.facts[{fact_index}]"
            fact_id = str(fact.get("fact_id") or "").strip()
            if not fact_id:
                issues.append(
                    _issue(
                        rule_id="fact_id_missing",
                        message="workflow fact sheet facts require non-empty fact_id",
                        target=f"{fact_target}.fact_id",
                    )
                )
            elif fact_id in seen_fact_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_fact_id",
                        message="workflow fact sheet fact_id values must be unique within each section",
                        target=f"{section_target}.facts",
                        observed=fact_id,
                    )
                )
            else:
                seen_fact_ids.add(fact_id)

            label_box_id = str(fact.get("label_box_id") or "").strip()
            value_box_id = str(fact.get("value_box_id") or "").strip()
            fact_label_box = layout_boxes_by_id.get(label_box_id)
            fact_value_box = layout_boxes_by_id.get(value_box_id)

            if fact_label_box is None:
                issues.append(
                    _issue(
                        rule_id="fact_label_missing",
                        message="workflow fact sheet facts must reference an existing fact label box",
                        target=f"{fact_target}.label_box_id",
                        expected=label_box_id,
                    )
                )
            elif parent_panel is not None and not _box_within_box(fact_label_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="fact_box_out_of_panel",
                        message="workflow fact sheet fact labels must stay within the parent panel",
                        target="fact_label",
                        box_refs=(fact_label_box.box_id, parent_panel.box_id),
                    )
                )

            if fact_value_box is None:
                issues.append(
                    _issue(
                        rule_id="fact_value_missing",
                        message="workflow fact sheet facts must reference an existing fact value box",
                        target=f"{fact_target}.value_box_id",
                        expected=value_box_id,
                    )
                )
            elif parent_panel is not None and not _box_within_box(fact_value_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="fact_box_out_of_panel",
                        message="workflow fact sheet fact values must stay within the parent panel",
                        target="fact_value",
                        box_refs=(fact_value_box.box_id, parent_panel.box_id),
                    )
                )

    if seen_layout_roles and seen_layout_roles != expected_layout_roles:
        issues.append(
            _issue(
                rule_id="section_layout_roles_incomplete",
                message="workflow fact sheet must cover the complete fixed four-panel grid",
                target="metrics.sections",
                observed=sorted(seen_layout_roles),
                expected=sorted(expected_layout_roles),
            )
        )

    return issues


def _check_publication_design_evidence_composite_shell(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=("workflow_stage", "stage_title", "panel", "panel_label", "summary_title", "card_label", "card_value"),
        )
    )

    workflow_stage_boxes = _boxes_of_type(sidecar.panel_boxes, "workflow_stage")
    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(workflow_stage_boxes) not in {3, 4}:
        issues.append(
            _issue(
                rule_id="workflow_stage_count_mismatch",
                message="design evidence composite requires three or four workflow stage boxes",
                target="panel_boxes",
                expected={"count": [3, 4]},
                observed={"count": len(workflow_stage_boxes)},
            )
        )
    if len(panel_boxes) != 3:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="design evidence composite requires exactly three summary panels",
                target="panel_boxes",
                expected={"count": 3},
                observed={"count": len(panel_boxes)},
            )
        )

    issues.extend(_check_pairwise_non_overlap(workflow_stage_boxes, rule_id="workflow_stage_overlap", target="workflow_stage"))
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"stage_title", "stage_detail", "panel_label", "summary_title", "card_label", "card_value"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    workflow_stage_boxes_by_id = {box.box_id: box for box in workflow_stage_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}

    workflow_stages = sidecar.metrics.get("workflow_stages")
    if not isinstance(workflow_stages, list) or not workflow_stages:
        issues.append(
            _issue(
                rule_id="workflow_stages_missing",
                message="design evidence composite qc requires non-empty workflow stage metrics",
                target="metrics.workflow_stages",
            )
        )
    else:
        if len(workflow_stages) not in {3, 4}:
            issues.append(
                _issue(
                    rule_id="workflow_stage_metrics_count_mismatch",
                    message="design evidence composite requires three or four declared workflow stages",
                    target="metrics.workflow_stages",
                    expected={"count": [3, 4]},
                    observed={"count": len(workflow_stages)},
                )
            )
        seen_stage_ids: set[str] = set()
        for stage_index, stage in enumerate(workflow_stages):
            if not isinstance(stage, dict):
                raise ValueError(f"layout_sidecar.metrics.workflow_stages[{stage_index}] must be an object")
            stage_target = f"metrics.workflow_stages[{stage_index}]"
            stage_id = str(stage.get("stage_id") or "").strip()
            stage_box_id = str(stage.get("stage_box_id") or "").strip()
            title_box_id = str(stage.get("title_box_id") or "").strip()
            detail_box_id = str(stage.get("detail_box_id") or "").strip()

            if not stage_id:
                issues.append(
                    _issue(
                        rule_id="workflow_stage_id_missing",
                        message="design evidence composite workflow stages require non-empty stage_id",
                        target=f"{stage_target}.stage_id",
                    )
                )
            elif stage_id in seen_stage_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_workflow_stage_id",
                        message="design evidence composite workflow stage ids must be unique",
                        target="metrics.workflow_stages",
                        observed=stage_id,
                    )
                )
            else:
                seen_stage_ids.add(stage_id)

            stage_box = workflow_stage_boxes_by_id.get(stage_box_id)
            if stage_box is None:
                issues.append(
                    _issue(
                        rule_id="workflow_stage_box_missing",
                        message="design evidence composite workflow stages must reference an existing workflow_stage box",
                        target=f"{stage_target}.stage_box_id",
                        expected=stage_box_id,
                    )
                )

            title_box = layout_boxes_by_id.get(title_box_id)
            if title_box is None:
                issues.append(
                    _issue(
                        rule_id="workflow_stage_title_missing",
                        message="design evidence composite workflow stages must reference an existing stage_title box",
                        target=f"{stage_target}.title_box_id",
                        expected=title_box_id,
                    )
                )
            elif stage_box is not None and not _box_within_box(title_box, stage_box):
                issues.append(
                    _issue(
                        rule_id="workflow_stage_title_out_of_stage",
                        message="design evidence composite workflow stage titles must stay within the parent stage box",
                        target="stage_title",
                        box_refs=(title_box.box_id, stage_box.box_id),
                    )
                )

            if detail_box_id:
                detail_box = layout_boxes_by_id.get(detail_box_id)
                if detail_box is None:
                    issues.append(
                        _issue(
                            rule_id="workflow_stage_detail_missing",
                            message="design evidence composite workflow stages must reference an existing stage_detail box when declared",
                            target=f"{stage_target}.detail_box_id",
                            expected=detail_box_id,
                        )
                    )
                elif stage_box is not None and not _box_within_box(detail_box, stage_box):
                    issues.append(
                        _issue(
                            rule_id="workflow_stage_detail_out_of_stage",
                            message="design evidence composite workflow stage detail must stay within the parent stage box",
                            target="stage_detail",
                            box_refs=(detail_box.box_id, stage_box.box_id),
                        )
                    )

    summary_panels = sidecar.metrics.get("summary_panels")
    if not isinstance(summary_panels, list) or not summary_panels:
        issues.append(
            _issue(
                rule_id="summary_panels_missing",
                message="design evidence composite qc requires non-empty summary panel metrics",
                target="metrics.summary_panels",
            )
        )
        return issues

    if len(summary_panels) != 3:
        issues.append(
            _issue(
                rule_id="summary_panel_count_mismatch",
                message="design evidence composite requires exactly three declared summary panels",
                target="metrics.summary_panels",
                expected={"count": 3},
                observed={"count": len(summary_panels)},
            )
        )

    expected_layout_roles = {"left", "center", "right"}
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_layout_roles: set[str] = set()
    for panel_index, panel in enumerate(summary_panels):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.summary_panels[{panel_index}] must be an object")
        panel_target = f"metrics.summary_panels[{panel_index}]"
        panel_id = str(panel.get("panel_id") or "").strip()
        panel_label = str(panel.get("panel_label") or "").strip()
        layout_role = str(panel.get("layout_role") or "").strip()
        panel_box_id = str(panel.get("panel_box_id") or "").strip()
        panel_label_box_id = str(panel.get("panel_label_box_id") or "").strip()
        title_box_id = str(panel.get("title_box_id") or "").strip()

        if not panel_id:
            issues.append(
                _issue(
                    rule_id="summary_panel_id_missing",
                    message="design evidence composite summary panels require non-empty panel_id",
                    target=f"{panel_target}.panel_id",
                )
            )
        elif panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_summary_panel_id",
                    message="design evidence composite summary panel ids must be unique",
                    target="metrics.summary_panels",
                    observed=panel_id,
                )
            )
        else:
            seen_panel_ids.add(panel_id)

        if not panel_label:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="design evidence composite summary panels require non-empty panel_label metrics",
                    target=f"{panel_target}.panel_label",
                )
            )
        elif panel_label in seen_panel_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_panel_label",
                    message="design evidence composite panel labels must be unique",
                    target="metrics.summary_panels",
                    observed=panel_label,
                )
            )
        else:
            seen_panel_labels.add(panel_label)

        if not layout_role:
            issues.append(
                _issue(
                    rule_id="layout_role_missing",
                    message="design evidence composite summary panels require non-empty layout_role",
                    target=f"{panel_target}.layout_role",
                )
            )
        elif layout_role not in expected_layout_roles:
            issues.append(
                _issue(
                    rule_id="summary_panel_layout_role_invalid",
                    message="design evidence composite layout_role must match the fixed three-panel composite",
                    target=f"{panel_target}.layout_role",
                    observed=layout_role,
                    expected=sorted(expected_layout_roles),
                )
            )
        elif layout_role in seen_layout_roles:
            issues.append(
                _issue(
                    rule_id="duplicate_layout_role",
                    message="design evidence composite layout_role values must be unique",
                    target="metrics.summary_panels",
                    observed=layout_role,
                )
            )
        else:
            seen_layout_roles.add(layout_role)

        parent_panel = panel_boxes_by_id.get(panel_box_id)
        if parent_panel is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="design evidence composite summary panels must reference an existing panel box",
                    target=f"{panel_target}.panel_box_id",
                    expected=panel_box_id,
                )
            )

        title_box = layout_boxes_by_id.get(title_box_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="summary_title_missing",
                    message="design evidence composite summary panels must reference an existing summary_title box",
                    target=f"{panel_target}.title_box_id",
                    expected=title_box_id,
                )
            )
        elif parent_panel is not None and not _box_within_box(title_box, parent_panel):
            issues.append(
                _issue(
                    rule_id="summary_title_out_of_panel",
                    message="design evidence composite summary titles must stay within the parent panel",
                    target="summary_title",
                    box_refs=(title_box.box_id, parent_panel.box_id),
                )
            )

        label_box = layout_boxes_by_id.get(panel_label_box_id)
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="design evidence composite summary panels must reference an existing panel label box",
                    target=f"{panel_target}.panel_label_box_id",
                    expected=panel_label_box_id,
                )
            )
        elif parent_panel is not None:
            panel_width = max(parent_panel.x1 - parent_panel.x0, 1e-9)
            panel_height = max(parent_panel.y1 - parent_panel.y0, 1e-9)
            if not _box_within_box(label_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="panel_label_out_of_panel",
                        message="design evidence composite panel labels must stay within the parent panel",
                        target="panel_label",
                        box_refs=(label_box.box_id, parent_panel.box_id),
                    )
                )
            else:
                anchored_near_left = label_box.x0 <= parent_panel.x0 + panel_width * 0.10
                anchored_near_top = (
                    label_box.y0 <= parent_panel.y0 + panel_height * 0.12
                    or label_box.y1 >= parent_panel.y1 - panel_height * 0.10
                )
                if not (anchored_near_left and anchored_near_top):
                    issues.append(
                        _issue(
                            rule_id="panel_label_anchor_drift",
                            message="design evidence composite panel labels must stay near the parent panel top-left anchor",
                            target="panel_label",
                            box_refs=(label_box.box_id, parent_panel.box_id),
                        )
                    )

        cards = panel.get("cards")
        if not isinstance(cards, list) or not cards:
            issues.append(
                _issue(
                    rule_id="cards_missing",
                    message="design evidence composite summary panels require a non-empty cards list",
                    target=f"{panel_target}.cards",
                )
            )
            continue

        seen_card_ids: set[str] = set()
        for card_index, card in enumerate(cards):
            if not isinstance(card, dict):
                raise ValueError(f"{panel_target}.cards[{card_index}] must be an object")
            card_target = f"{panel_target}.cards[{card_index}]"
            card_id = str(card.get("card_id") or "").strip()
            if not card_id:
                issues.append(
                    _issue(
                        rule_id="card_id_missing",
                        message="design evidence composite cards require non-empty card_id",
                        target=f"{card_target}.card_id",
                    )
                )
            elif card_id in seen_card_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_card_id",
                        message="design evidence composite card ids must be unique within each summary panel",
                        target=f"{panel_target}.cards",
                        observed=card_id,
                    )
                )
            else:
                seen_card_ids.add(card_id)

            label_box_id = str(card.get("label_box_id") or "").strip()
            value_box_id = str(card.get("value_box_id") or "").strip()
            label_box = layout_boxes_by_id.get(label_box_id)
            value_box = layout_boxes_by_id.get(value_box_id)
            if label_box is None:
                issues.append(
                    _issue(
                        rule_id="card_label_missing",
                        message="design evidence composite cards must reference an existing card label box",
                        target=f"{card_target}.label_box_id",
                        expected=label_box_id,
                    )
                )
            elif parent_panel is not None and not _box_within_box(label_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="card_box_out_of_panel",
                        message="design evidence composite card labels must stay within the parent panel",
                        target="card_label",
                        box_refs=(label_box.box_id, parent_panel.box_id),
                    )
                )
            if value_box is None:
                issues.append(
                    _issue(
                        rule_id="card_value_missing",
                        message="design evidence composite cards must reference an existing card value box",
                        target=f"{card_target}.value_box_id",
                        expected=value_box_id,
                    )
                )
            elif parent_panel is not None and not _box_within_box(value_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="card_box_out_of_panel",
                        message="design evidence composite card values must stay within the parent panel",
                        target="card_value",
                        box_refs=(value_box.box_id, parent_panel.box_id),
                    )
                )

    if seen_layout_roles and seen_layout_roles != expected_layout_roles:
        issues.append(
            _issue(
                rule_id="summary_panel_layout_roles_incomplete",
                message="design evidence composite must cover the complete fixed three-panel layout",
                target="metrics.summary_panels",
                observed=sorted(seen_layout_roles),
                expected=sorted(expected_layout_roles),
            )
        )

    return issues


def _check_publication_shap_waterfall_local_explanation_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "panel_label",
        "case_label",
        "baseline_label",
        "prediction_label",
        "feature_label",
        "contribution_bar",
        "baseline_marker",
        "prediction_marker",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {"title", "panel_title", "subplot_x_axis_title", "panel_label", "case_label", "baseline_label", "prediction_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="shap waterfall qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap waterfall panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        case_label = str(panel_metric.get("case_label") or "").strip()
        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip()
        baseline_marker_box_id = str(panel_metric.get("baseline_marker_box_id") or "").strip()
        prediction_marker_box_id = str(panel_metric.get("prediction_marker_box_id") or "").strip()
        if not panel_id or not panel_label or not title or not case_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="shap waterfall panel metrics must declare panel metadata and case labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        if not panel_box_id:
            panel_box_id = f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="shap waterfall metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue

        if not baseline_marker_box_id:
            baseline_marker_box_id = f"baseline_marker_{panel_label}"
        if not prediction_marker_box_id:
            prediction_marker_box_id = f"prediction_marker_{panel_label}"

        baseline_marker = guide_box_by_id.get(baseline_marker_box_id)
        if baseline_marker is None:
            issues.append(
                _issue(
                    rule_id="baseline_marker_missing",
                    message="shap waterfall requires one baseline marker per panel",
                    target=f"metrics.panels[{panel_index}].baseline_marker_box_id",
                    observed={"baseline_marker_box_id": baseline_marker_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(baseline_marker, panel_box):
            issues.append(
                _issue(
                    rule_id="baseline_marker_outside_panel",
                    message="baseline marker must stay within the panel region",
                    target=f"guide_boxes.{baseline_marker.box_id}",
                    box_refs=(baseline_marker.box_id, panel_box.box_id),
                )
            )

        prediction_marker = guide_box_by_id.get(prediction_marker_box_id)
        if prediction_marker is None:
            issues.append(
                _issue(
                    rule_id="prediction_marker_missing",
                    message="shap waterfall requires one prediction marker per panel",
                    target=f"metrics.panels[{panel_index}].prediction_marker_box_id",
                    observed={"prediction_marker_box_id": prediction_marker_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(prediction_marker, panel_box):
            issues.append(
                _issue(
                    rule_id="prediction_marker_outside_panel",
                    message="prediction marker must stay within the panel region",
                    target=f"guide_boxes.{prediction_marker.box_id}",
                    box_refs=(prediction_marker.box_id, panel_box.box_id),
                )
            )

        contributions = panel_metric.get("contributions")
        if not isinstance(contributions, list) or not contributions:
            issues.append(
                _issue(
                    rule_id="contributions_missing",
                    message="shap waterfall panel metrics must contain ordered contributions",
                    target=f"metrics.panels[{panel_index}].contributions",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        for contribution_index, contribution in enumerate(contributions):
            if not isinstance(contribution, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            feature = str(contribution.get("feature") or "").strip()
            bar_box_id = str(contribution.get("bar_box_id") or "").strip()
            label_box_id = str(contribution.get("label_box_id") or "").strip()
            shap_value = _require_numeric(
                contribution.get("shap_value"),
                label=(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            start_value = _require_numeric(
                contribution.get("start_value"),
                label=(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].start_value"
                ),
            )
            end_value = _require_numeric(
                contribution.get("end_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].end_value",
            )
            if not feature or not bar_box_id or not label_box_id:
                issues.append(
                    _issue(
                        rule_id="contribution_metric_missing",
                        message="each shap waterfall contribution must declare feature, bar_box_id, and label_box_id",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
                continue
            if shap_value > 0 and end_value <= start_value:
                issues.append(
                    _issue(
                        rule_id="contribution_direction_mismatch",
                        message="positive SHAP contribution must increase from start_value to end_value",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        observed={"start_value": start_value, "end_value": end_value, "shap_value": shap_value},
                        box_refs=(panel_box.box_id,),
                    )
                )
            if shap_value < 0 and end_value >= start_value:
                issues.append(
                    _issue(
                        rule_id="contribution_direction_mismatch",
                        message="negative SHAP contribution must decrease from start_value to end_value",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        observed={"start_value": start_value, "end_value": end_value, "shap_value": shap_value},
                        box_refs=(panel_box.box_id,),
                    )
                )
            bar_box = layout_box_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="contribution_bar_missing",
                        message="each shap waterfall contribution must reference an existing contribution bar box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        observed={"bar_box_id": bar_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif not _box_within_box(bar_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="contribution_bar_outside_panel",
                        message="contribution bar must stay within the panel region",
                        target=f"layout_boxes.{bar_box.box_id}",
                        box_refs=(bar_box.box_id, panel_box.box_id),
                    )
                )
            label_box = layout_box_by_id.get(label_box_id)
            if label_box is None:
                issues.append(
                    _issue(
                        rule_id="feature_label_missing",
                        message="each shap waterfall contribution must reference an existing feature label box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        observed={"label_box_id": label_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif _boxes_overlap(label_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="feature_label_panel_overlap",
                        message="feature label annotation must stay outside the waterfall panel region",
                        target=f"layout_boxes.{label_box.box_id}",
                        box_refs=(label_box.box_id, panel_box.box_id),
                )
            )
    return issues


def _check_publication_shap_force_like_summary_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "panel_label",
        "case_label",
        "baseline_label",
        "prediction_label",
        "force_feature_label",
        "baseline_marker",
        "prediction_marker",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {"title", "panel_title", "subplot_x_axis_title", "panel_label", "case_label", "baseline_label", "prediction_label", "force_feature_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="shap force-like summary qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap force-like summary panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        case_label = str(panel_metric.get("case_label") or "").strip()
        baseline_value = _require_numeric(
            panel_metric.get("baseline_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric(
            panel_metric.get("predicted_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].predicted_value",
        )
        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip()
        baseline_marker_box_id = str(panel_metric.get("baseline_marker_box_id") or "").strip()
        prediction_marker_box_id = str(panel_metric.get("prediction_marker_box_id") or "").strip()
        if not panel_id or not panel_label or not title or not case_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="shap force-like summary metrics must declare panel metadata and case labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        if not panel_box_id:
            panel_box_id = f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="shap force-like summary metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        if not baseline_marker_box_id:
            baseline_marker_box_id = f"baseline_marker_{panel_label}"
        if not prediction_marker_box_id:
            prediction_marker_box_id = f"prediction_marker_{panel_label}"

        baseline_marker = guide_box_by_id.get(baseline_marker_box_id)
        prediction_marker = guide_box_by_id.get(prediction_marker_box_id)
        if baseline_marker is None:
            issues.append(
                _issue(
                    rule_id="baseline_marker_missing",
                    message="shap force-like summary requires one baseline marker per panel",
                    target=f"metrics.panels[{panel_index}].baseline_marker_box_id",
                    observed={"baseline_marker_box_id": baseline_marker_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(baseline_marker, panel_box):
            issues.append(
                _issue(
                    rule_id="baseline_marker_outside_panel",
                    message="baseline marker must stay within the panel region",
                    target=f"guide_boxes.{baseline_marker.box_id}",
                    box_refs=(baseline_marker.box_id, panel_box.box_id),
                )
            )

        if prediction_marker is None:
            issues.append(
                _issue(
                    rule_id="prediction_marker_missing",
                    message="shap force-like summary requires one prediction marker per panel",
                    target=f"metrics.panels[{panel_index}].prediction_marker_box_id",
                    observed={"prediction_marker_box_id": prediction_marker_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(prediction_marker, panel_box):
            issues.append(
                _issue(
                    rule_id="prediction_marker_outside_panel",
                    message="prediction marker must stay within the panel region",
                    target=f"guide_boxes.{prediction_marker.box_id}",
                    box_refs=(prediction_marker.box_id, panel_box.box_id),
                )
            )

        if baseline_marker is not None and prediction_marker is not None:
            baseline_mid_x = (baseline_marker.x0 + baseline_marker.x1) / 2.0
            prediction_mid_x = (prediction_marker.x0 + prediction_marker.x1) / 2.0
            if predicted_value > baseline_value and prediction_mid_x <= baseline_mid_x:
                issues.append(
                    _issue(
                        rule_id="prediction_marker_direction_mismatch",
                        message="prediction marker must move right of baseline for net-positive force-like cases",
                        target=f"metrics.panels[{panel_index}].predicted_value",
                        box_refs=(prediction_marker.box_id, baseline_marker.box_id, panel_box.box_id),
                    )
                )
            if predicted_value < baseline_value and prediction_mid_x >= baseline_mid_x:
                issues.append(
                    _issue(
                        rule_id="prediction_marker_direction_mismatch",
                        message="prediction marker must move left of baseline for net-negative force-like cases",
                        target=f"metrics.panels[{panel_index}].predicted_value",
                        box_refs=(prediction_marker.box_id, baseline_marker.box_id, panel_box.box_id),
                    )
                )

        contributions = panel_metric.get("contributions")
        if not isinstance(contributions, list) or not contributions:
            issues.append(
                _issue(
                    rule_id="contributions_missing",
                    message="shap force-like summary panel metrics must contain ordered contributions",
                    target=f"metrics.panels[{panel_index}].contributions",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        for contribution_index, contribution in enumerate(contributions):
            if not isinstance(contribution, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            feature = str(contribution.get("feature") or "").strip()
            direction = str(contribution.get("direction") or "").strip()
            segment_box_id = str(contribution.get("segment_box_id") or "").strip()
            label_box_id = str(contribution.get("label_box_id") or "").strip()
            shap_value = _require_numeric(
                contribution.get("shap_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].shap_value",
            )
            start_value = _require_numeric(
                contribution.get("start_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].start_value",
            )
            end_value = _require_numeric(
                contribution.get("end_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].end_value",
            )
            if not feature or not direction or not segment_box_id or not label_box_id:
                issues.append(
                    _issue(
                        rule_id="contribution_metric_missing",
                        message="each force-like contribution must declare feature, direction, segment_box_id, and label_box_id",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
                continue
            segment_box = layout_box_by_id.get(segment_box_id)
            if segment_box is None:
                issues.append(
                    _issue(
                        rule_id="contribution_segment_missing",
                        message="each force-like contribution must reference an existing segment box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        observed={"segment_box_id": segment_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif not _box_within_box(segment_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="contribution_segment_outside_panel",
                        message="force-like contribution segment must stay within the panel region",
                        target=f"layout_boxes.{segment_box.box_id}",
                        box_refs=(segment_box.box_id, panel_box.box_id),
                    )
                )
            label_box = layout_box_by_id.get(label_box_id)
            if label_box is None:
                issues.append(
                    _issue(
                        rule_id="force_label_missing",
                        message="each force-like contribution must reference an existing feature label box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        observed={"label_box_id": label_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif not _box_within_box(label_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="force_label_outside_panel",
                        message="force-like feature labels must stay within the panel region",
                        target=f"layout_boxes.{label_box.box_id}",
                        box_refs=(label_box.box_id, panel_box.box_id),
                    )
                )

            if direction == "positive":
                if shap_value <= 0 or end_value <= start_value:
                    issues.append(
                        _issue(
                            rule_id="contribution_direction_mismatch",
                            message="positive force-like contribution must increase from start_value to end_value",
                            target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                            observed={"start_value": start_value, "end_value": end_value, "shap_value": shap_value},
                            box_refs=(panel_box.box_id,),
                        )
                    )
                if baseline_marker is not None and segment_box is not None:
                    if segment_box.x0 < baseline_marker.x0 - 1e-6:
                        issues.append(
                            _issue(
                                rule_id="positive_segment_crosses_baseline",
                                message="positive force-like segment must stay to the right of baseline",
                                target=f"layout_boxes.{segment_box.box_id}",
                                box_refs=(segment_box.box_id, baseline_marker.box_id, panel_box.box_id),
                        )
                    )
            elif direction == "negative":
                if shap_value >= 0 or end_value >= start_value:
                    issues.append(
                        _issue(
                            rule_id="contribution_direction_mismatch",
                            message="negative force-like contribution must decrease from start_value to end_value",
                            target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                            observed={"start_value": start_value, "end_value": end_value, "shap_value": shap_value},
                            box_refs=(panel_box.box_id,),
                        )
                    )
                if baseline_marker is not None and segment_box is not None:
                    if segment_box.x1 > baseline_marker.x1 + 1e-6:
                        issues.append(
                            _issue(
                                rule_id="negative_segment_crosses_baseline",
                                message="negative force-like segment must stay to the left of baseline",
                                target=f"layout_boxes.{segment_box.box_id}",
                                box_refs=(segment_box.box_id, baseline_marker.box_id, panel_box.box_id),
                            )
                        )
            else:
                issues.append(
                    _issue(
                        rule_id="contribution_direction_invalid",
                        message="force-like contribution direction must be positive or negative",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].direction",
                        observed={"direction": direction},
                    )
                )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )
    return issues


def _check_publication_shap_grouped_local_explanation_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "panel_label",
        "group_label",
        "baseline_label",
        "prediction_label",
        "feature_label",
        "contribution_bar",
        "value_label",
        "zero_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {
            "title",
            "panel_title",
            "panel_label",
            "group_label",
            "baseline_label",
            "prediction_label",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="shap grouped local explanation qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap grouped local explanation panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    expected_feature_order: tuple[str, ...] | None = None
    seen_group_labels: set[str] = set()

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")

        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        group_label = str(panel_metric.get("group_label") or "").strip()
        baseline_value = _require_numeric(
            panel_metric.get("baseline_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric(
            panel_metric.get("predicted_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].predicted_value",
        )
        panel_token = _panel_label_token(panel_label)
        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_token}"
        zero_line_box_id = str(panel_metric.get("zero_line_box_id") or "").strip() or f"zero_line_{panel_token}"

        if not panel_id or not panel_label or not title or not group_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="shap grouped local explanation metrics must declare panel metadata and group labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue
        if group_label in seen_group_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_group_label",
                    message="shap grouped local explanation group labels must be unique across panels",
                    target=f"metrics.panels[{panel_index}].group_label",
                    observed=group_label,
                )
            )
        seen_group_labels.add(group_label)

        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None and panel_index < len(panel_boxes):
            panel_box = panel_boxes[panel_index]
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="shap grouped local explanation metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}].panel_box_id",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue

        panel_label_box = layout_box_by_id.get(f"panel_label_{panel_token}")
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="missing_panel_label",
                    message="grouped local explanation panels require explicit panel labels",
                    target=f"metrics.panels[{panel_index}].panel_label",
                    expected=f"panel_label_{panel_token}",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            panel_width = max(panel_box.x1 - panel_box.x0, 1e-9)
            panel_height = max(panel_box.y1 - panel_box.y0, 1e-9)
            max_left_gap = max(panel_width * 0.14, 0.018)
            max_top_overhang = max(panel_height * 0.12, 0.03)
            if (
                panel_label_box.x1 < panel_box.x0 - max_left_gap
                or panel_label_box.x0 > panel_box.x0 + panel_width * 0.10
                or panel_label_box.y0 < panel_box.y1 - panel_height * 0.10
                or panel_label_box.y1 > panel_box.y1 + max_top_overhang
            ):
                issues.append(
                    _issue(
                        rule_id="panel_label_anchor_drift",
                        message="grouped local explanation panel labels must stay near the parent panel top-left anchor",
                        target="panel_label",
                        box_refs=(panel_label_box.box_id, panel_box.box_id),
                    )
                )

        for box_id, rule_id, message in (
            (f"panel_title_{panel_token}", "panel_title_missing", "each grouped local panel requires an explicit panel title"),
            (f"group_label_{panel_token}", "group_label_missing", "each grouped local panel requires an explicit group label"),
            (
                f"baseline_label_{panel_token}",
                "baseline_label_missing",
                "each grouped local panel requires an explicit baseline label",
            ),
            (
                f"prediction_label_{panel_token}",
                "prediction_label_missing",
                "each grouped local panel requires an explicit prediction label",
            ),
            (
                f"x_axis_title_{panel_token}",
                "x_axis_title_missing",
                "each grouped local panel requires an explicit subplot x-axis title",
            ),
        ):
            if box_id in layout_box_by_id:
                continue
            issues.append(
                _issue(
                    rule_id=rule_id,
                    message=message,
                    target=f"metrics.panels[{panel_index}]",
                    observed={"box_id": box_id},
                    box_refs=(panel_box.box_id,),
                )
            )

        zero_line = guide_box_by_id.get(zero_line_box_id)
        if zero_line is None:
            issues.append(
                _issue(
                    rule_id="zero_line_missing",
                    message="each grouped local panel requires an explicit zero_line guide box",
                    target=f"metrics.panels[{panel_index}].zero_line_box_id",
                    observed={"zero_line_box_id": zero_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
            zero_mid_x = None
            zero_tolerance = None
        else:
            epsilon = 1e-6
            if not (
                panel_box.x0 - epsilon <= zero_line.x0 <= panel_box.x1 + epsilon
                and panel_box.x0 - epsilon <= zero_line.x1 <= panel_box.x1 + epsilon
                and panel_box.y0 - epsilon <= zero_line.y0 <= panel_box.y1 + epsilon
                and panel_box.y0 - epsilon <= zero_line.y1 <= panel_box.y1 + epsilon
            ):
                issues.append(
                    _issue(
                        rule_id="zero_line_outside_panel",
                        message="grouped local explanation zero line must stay within the panel region",
                        target=f"guide_boxes.{zero_line.box_id}",
                        box_refs=(zero_line.box_id, panel_box.box_id),
                    )
                )
            zero_mid_x = (zero_line.x0 + zero_line.x1) / 2.0
            zero_tolerance = max((zero_line.x1 - zero_line.x0) / 2.0, 0.0025)

        contributions = panel_metric.get("contributions")
        if not isinstance(contributions, list) or not contributions:
            issues.append(
                _issue(
                    rule_id="contributions_missing",
                    message="shap grouped local explanation panel metrics must contain ordered contributions",
                    target=f"metrics.panels[{panel_index}].contributions",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        previous_rank = 0
        seen_features: set[str] = set()
        feature_order: list[str] = []
        contribution_sum = 0.0
        for contribution_index, contribution in enumerate(contributions):
            if not isinstance(contribution, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )

            rank_value = _require_numeric(
                contribution.get("rank"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].rank",
            )
            if not math.isclose(rank_value, round(rank_value), rel_tol=0.0, abs_tol=1e-9) or rank_value <= 0.0:
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].rank must be a positive integer"
                )
            rank = int(round(rank_value))
            if rank <= previous_rank:
                issues.append(
                    _issue(
                        rule_id="grouped_local_rank_not_increasing",
                        message="grouped local explanation contribution ranks must be strictly increasing",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].rank",
                        observed=rank,
                    )
                )
            previous_rank = rank

            feature = _require_non_empty_text(
                contribution.get("feature"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].feature",
            )
            if feature in seen_features:
                issues.append(
                    _issue(
                        rule_id="grouped_local_feature_duplicate",
                        message="grouped local explanation features must be unique within each panel",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].feature",
                        observed=feature,
                    )
                )
            seen_features.add(feature)
            feature_order.append(feature)

            shap_value = _require_numeric(
                contribution.get("shap_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].shap_value",
            )
            contribution_sum += shap_value

            bar_box_id = _require_non_empty_text(
                contribution.get("bar_box_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].bar_box_id",
            )
            feature_label_box_id = _require_non_empty_text(
                contribution.get("feature_label_box_id"),
                label=(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].feature_label_box_id"
                ),
            )
            value_label_box_id = _require_non_empty_text(
                contribution.get("value_label_box_id"),
                label=(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].value_label_box_id"
                ),
            )

            bar_box = layout_box_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="contribution_bar_missing",
                        message="grouped local explanation contributions must reference an existing contribution bar box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].bar_box_id",
                        observed=bar_box_id,
                        box_refs=(panel_box.box_id,),
                    )
                )
            else:
                panel_width = max(panel_box.x1 - panel_box.x0, 1e-9)
                horizontal_overhang = max(panel_width * 0.25, 0.03)
                epsilon = 1e-6
                if not (
                    panel_box.x0 - horizontal_overhang - epsilon <= bar_box.x0 <= panel_box.x1 + horizontal_overhang + epsilon
                    and panel_box.x0 - horizontal_overhang - epsilon <= bar_box.x1 <= panel_box.x1 + horizontal_overhang + epsilon
                    and panel_box.y0 - epsilon <= bar_box.y0 <= panel_box.y1 + epsilon
                    and panel_box.y0 - epsilon <= bar_box.y1 <= panel_box.y1 + epsilon
                ):
                    issues.append(
                        _issue(
                            rule_id="contribution_bar_outside_panel",
                            message="grouped local explanation contribution bars must stay aligned to the panel row band without drifting far outside the panel",
                            target=f"layout_boxes.{bar_box.box_id}",
                            box_refs=(bar_box.box_id, panel_box.box_id),
                        )
                    )
                if zero_mid_x is not None and zero_tolerance is not None:
                    if shap_value > 0.0 and bar_box.x0 < zero_mid_x - zero_tolerance:
                        issues.append(
                            _issue(
                                rule_id="positive_bar_crosses_zero",
                                message="positive grouped local explanation bars must stay on the right side of the zero line",
                                target=f"layout_boxes.{bar_box.box_id}",
                                box_refs=(bar_box.box_id, zero_line_box_id, panel_box.box_id),
                            )
                        )
                    if shap_value < 0.0 and bar_box.x1 > zero_mid_x + zero_tolerance:
                        issues.append(
                            _issue(
                                rule_id="negative_bar_crosses_zero",
                                message="negative grouped local explanation bars must stay on the left side of the zero line",
                                target=f"layout_boxes.{bar_box.box_id}",
                                box_refs=(bar_box.box_id, zero_line_box_id, panel_box.box_id),
                            )
                        )

            feature_label_box = layout_box_by_id.get(feature_label_box_id)
            if feature_label_box is None:
                issues.append(
                    _issue(
                        rule_id="feature_label_missing",
                        message="grouped local explanation contributions must reference an existing feature label box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].feature_label_box_id",
                        observed=feature_label_box_id,
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif bar_box is not None:
                if _boxes_overlap(feature_label_box, panel_box):
                    issues.append(
                        _issue(
                            rule_id="feature_label_panel_overlap",
                            message="grouped local explanation feature labels must stay outside the panel region",
                            target=f"layout_boxes.{feature_label_box.box_id}",
                            box_refs=(feature_label_box.box_id, panel_box.box_id),
                        )
                    )
                label_center_y = (feature_label_box.y0 + feature_label_box.y1) / 2.0
                if not (bar_box.y0 <= label_center_y <= bar_box.y1):
                    issues.append(
                        _issue(
                            rule_id="feature_label_row_misaligned",
                            message="grouped local explanation feature labels must stay vertically aligned to their bar row",
                            target=f"layout_boxes.{feature_label_box.box_id}",
                            observed={"label_center_y": label_center_y},
                            expected={"row_y0": bar_box.y0, "row_y1": bar_box.y1},
                            box_refs=(feature_label_box.box_id, bar_box.box_id, panel_box.box_id),
                        )
                    )

            value_label_box = layout_box_by_id.get(value_label_box_id)
            if value_label_box is None:
                issues.append(
                    _issue(
                        rule_id="value_label_missing",
                        message="grouped local explanation contributions must reference an existing value label box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].value_label_box_id",
                        observed=value_label_box_id,
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif bar_box is not None:
                label_center_y = (value_label_box.y0 + value_label_box.y1) / 2.0
                if not (bar_box.y0 <= label_center_y <= bar_box.y1):
                    issues.append(
                        _issue(
                            rule_id="value_label_row_misaligned",
                            message="grouped local explanation value labels must stay vertically aligned to their bar row",
                            target=f"layout_boxes.{value_label_box.box_id}",
                            observed={"label_center_y": label_center_y},
                            expected={"row_y0": bar_box.y0, "row_y1": bar_box.y1},
                            box_refs=(value_label_box.box_id, bar_box.box_id, panel_box.box_id),
                        )
                    )

        if not math.isclose(
            predicted_value,
            baseline_value + contribution_sum,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            issues.append(
                _issue(
                    rule_id="panel_prediction_value_mismatch",
                    message="grouped local explanation predicted_value must equal baseline_value plus contribution sum",
                    target=f"metrics.panels[{panel_index}].predicted_value",
                    observed={"baseline_value": baseline_value, "predicted_value": predicted_value, "contribution_sum": contribution_sum},
                )
            )

        feature_order_tuple = tuple(feature_order)
        if expected_feature_order is None:
            expected_feature_order = feature_order_tuple
        elif feature_order_tuple != expected_feature_order:
            issues.append(
                _issue(
                    rule_id="grouped_local_feature_order_mismatch",
                    message="all grouped local explanation panels must keep the same feature order",
                    target=f"metrics.panels[{panel_index}].contributions",
                    observed={"feature_order": list(feature_order_tuple)},
                    expected={"feature_order": list(expected_feature_order)},
                    box_refs=(panel_box.box_id,),
                )
            )

    return issues


def _check_publication_shap_grouped_decision_path_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = (
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "feature_label",
        "decision_path_line",
        "prediction_label",
        "baseline_reference_line",
        "prediction_marker",
    )
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types = ("title",) + required_box_types
    issues.extend(_check_required_box_types(all_boxes, required_box_types=required_box_types))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 1:
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap grouped decision path panel requires exactly one panel box",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"panel_boxes": 1},
            )
        )
    panel_box = panel_boxes[0] if panel_boxes else None

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}

    legend_box = layout_box_by_id.get("legend_box")
    if legend_box is None:
        issues.append(
            _issue(
                rule_id="legend_box_missing",
                message="shap grouped decision path panel requires an explicit legend box",
                target="legend_box",
                expected="present",
            )
        )
    elif panel_box is not None and _boxes_overlap(legend_box, panel_box):
        issues.append(
            _issue(
                rule_id="legend_box_overlaps_panel",
                message="shap grouped decision path legend must stay outside the main panel region",
                target="legend_box",
                box_refs=(legend_box.box_id, panel_box.box_id),
            )
        )

    legend_title_box = layout_box_by_id.get("legend_title")
    if legend_title_box is None:
        issues.append(
            _issue(
                rule_id="legend_title_missing",
                message="shap grouped decision path panel requires an explicit legend title",
                target="legend_title",
                expected="present",
            )
        )

    metrics_panel_box_id = str(sidecar.metrics.get("panel_box_id") or "").strip()
    if panel_box is not None and metrics_panel_box_id and metrics_panel_box_id != panel_box.box_id:
        issues.append(
            _issue(
                rule_id="panel_box_mismatch",
                message="shap grouped decision path metrics must reference the primary panel box",
                target="metrics.panel_box_id",
                observed=metrics_panel_box_id,
                expected=panel_box.box_id,
            )
        )

    baseline_line_box_id = str(sidecar.metrics.get("baseline_line_box_id") or "").strip()
    baseline_line = guide_box_by_id.get(baseline_line_box_id) if baseline_line_box_id else None
    if baseline_line is None:
        issues.append(
            _issue(
                rule_id="baseline_reference_line_missing",
                message="shap grouped decision path panel requires a baseline reference line",
                target="metrics.baseline_line_box_id",
                observed=baseline_line_box_id or None,
                expected="present",
                box_refs=((panel_box.box_id,) if panel_box is not None else ()),
            )
        )
    elif panel_box is not None and not _box_within_box(baseline_line, panel_box):
        issues.append(
            _issue(
                rule_id="baseline_reference_line_outside_panel",
                message="shap grouped decision path baseline reference line must stay within the panel region",
                target=f"guide_boxes.{baseline_line.box_id}",
                box_refs=(baseline_line.box_id, panel_box.box_id),
            )
        )

    baseline_value = _require_numeric(sidecar.metrics.get("baseline_value"), label="layout_sidecar.metrics.baseline_value")
    feature_order_payload = sidecar.metrics.get("feature_order")
    if not isinstance(feature_order_payload, list) or not feature_order_payload:
        issues.append(
            _issue(
                rule_id="feature_order_missing",
                message="shap grouped decision path metrics require a non-empty shared feature order",
                target="metrics.feature_order",
            )
        )
        feature_order: tuple[str, ...] = ()
    else:
        feature_order = tuple(str(item or "").strip() for item in feature_order_payload)
        if any(not item for item in feature_order):
            issues.append(
                _issue(
                    rule_id="feature_order_invalid",
                    message="shap grouped decision path feature_order entries must be non-empty",
                    target="metrics.feature_order",
                )
            )

    feature_label_box_ids_payload = sidecar.metrics.get("feature_label_box_ids")
    if not isinstance(feature_label_box_ids_payload, list) or len(feature_label_box_ids_payload) != len(feature_order):
        issues.append(
            _issue(
                rule_id="feature_label_count_mismatch",
                message="shap grouped decision path feature label boxes must match the shared feature order length",
                target="metrics.feature_label_box_ids",
                observed={"feature_label_box_ids": len(feature_label_box_ids_payload or []) if isinstance(feature_label_box_ids_payload, list) else None},
                expected={"feature_order": len(feature_order)},
            )
        )
        feature_label_box_ids: tuple[str, ...] = ()
    else:
        feature_label_box_ids = tuple(str(item or "").strip() for item in feature_label_box_ids_payload)
        for feature_label_box_id in feature_label_box_ids:
            box = layout_box_by_id.get(feature_label_box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id="feature_label_missing",
                        message="shap grouped decision path metrics must reference existing feature label boxes",
                        target="metrics.feature_label_box_ids",
                        observed=feature_label_box_id,
                    )
                )
                continue
            if panel_box is not None and _boxes_overlap(box, panel_box):
                issues.append(
                    _issue(
                        rule_id="feature_label_panel_overlap",
                        message="shap grouped decision path feature labels must stay outside the panel region",
                        target=f"layout_boxes.{box.box_id}",
                        box_refs=(box.box_id, panel_box.box_id),
                    )
                )

    groups_payload = sidecar.metrics.get("groups")
    if not isinstance(groups_payload, list) or len(groups_payload) != 2:
        issues.append(
            _issue(
                rule_id="group_count_invalid",
                message="shap grouped decision path metrics require exactly two groups",
                target="metrics.groups",
                observed={"groups": len(groups_payload) if isinstance(groups_payload, list) else None},
                expected={"groups": 2},
            )
        )
        return issues

    seen_group_ids: set[str] = set()
    seen_group_labels: set[str] = set()
    for group_index, group_metric in enumerate(groups_payload):
        if not isinstance(group_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.groups[{group_index}] must be an object")
        group_id = str(group_metric.get("group_id") or "").strip()
        group_label = str(group_metric.get("group_label") or "").strip()
        predicted_value = _require_numeric(
            group_metric.get("predicted_value"),
            label=f"layout_sidecar.metrics.groups[{group_index}].predicted_value",
        )
        if not group_id:
            issues.append(
                _issue(
                    rule_id="group_id_missing",
                    message="shap grouped decision path groups must declare a non-empty group_id",
                    target=f"metrics.groups[{group_index}].group_id",
                )
            )
        elif group_id in seen_group_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_group_id",
                    message="shap grouped decision path group_ids must be unique",
                    target=f"metrics.groups[{group_index}].group_id",
                    observed=group_id,
                )
            )
        seen_group_ids.add(group_id)
        if not group_label:
            issues.append(
                _issue(
                    rule_id="group_label_missing",
                    message="shap grouped decision path groups must declare a non-empty group_label",
                    target=f"metrics.groups[{group_index}].group_label",
                )
            )
        elif group_label in seen_group_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_group_label",
                    message="shap grouped decision path group_labels must be unique",
                    target=f"metrics.groups[{group_index}].group_label",
                    observed=group_label,
                )
            )
        seen_group_labels.add(group_label)

        line_box_id = str(group_metric.get("line_box_id") or "").strip()
        line_box = layout_box_by_id.get(line_box_id)
        if line_box is None:
            issues.append(
                _issue(
                    rule_id="decision_path_line_missing",
                    message="shap grouped decision path groups must reference an existing decision-path line box",
                    target=f"metrics.groups[{group_index}].line_box_id",
                    observed=line_box_id or None,
                    box_refs=((panel_box.box_id,) if panel_box is not None else ()),
                )
            )
        elif panel_box is not None and not _box_within_box(line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="decision_path_line_outside_panel",
                    message="shap grouped decision path lines must stay within the panel region",
                    target=f"layout_boxes.{line_box.box_id}",
                    box_refs=(line_box.box_id, panel_box.box_id),
                )
            )

        prediction_marker_box_id = str(group_metric.get("prediction_marker_box_id") or "").strip()
        prediction_marker = guide_box_by_id.get(prediction_marker_box_id)
        if prediction_marker is None:
            issues.append(
                _issue(
                    rule_id="prediction_marker_missing",
                    message="shap grouped decision path groups must reference an existing prediction marker box",
                    target=f"metrics.groups[{group_index}].prediction_marker_box_id",
                    observed=prediction_marker_box_id or None,
                    box_refs=((panel_box.box_id,) if panel_box is not None else ()),
                )
            )
        elif panel_box is not None and not _box_within_box(prediction_marker, panel_box):
            issues.append(
                _issue(
                    rule_id="prediction_marker_outside_panel",
                    message="shap grouped decision path prediction markers must stay within the panel region",
                    target=f"guide_boxes.{prediction_marker.box_id}",
                    box_refs=(prediction_marker.box_id, panel_box.box_id),
                )
            )

        prediction_label_box_id = str(group_metric.get("prediction_label_box_id") or "").strip()
        prediction_label_box = layout_box_by_id.get(prediction_label_box_id)
        if prediction_label_box is None:
            issues.append(
                _issue(
                    rule_id="prediction_label_missing",
                    message="shap grouped decision path groups must reference an existing prediction label box",
                    target=f"metrics.groups[{group_index}].prediction_label_box_id",
                    observed=prediction_label_box_id or None,
                )
            )

        contributions_payload = group_metric.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            issues.append(
                _issue(
                    rule_id="contributions_missing",
                    message="shap grouped decision path groups require non-empty contributions",
                    target=f"metrics.groups[{group_index}].contributions",
                )
            )
            continue

        previous_rank = 0
        contribution_sum = 0.0
        group_feature_order: list[str] = []
        for contribution_index, contribution_metric in enumerate(contributions_payload):
            if not isinstance(contribution_metric, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}] must be an object"
                )
            rank = int(
                _require_numeric(
                    contribution_metric.get("rank"),
                    label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].rank",
                )
            )
            if rank <= previous_rank:
                issues.append(
                    _issue(
                        rule_id="contribution_rank_invalid",
                        message="shap grouped decision path contribution ranks must be strictly increasing",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}].rank",
                    )
                )
            previous_rank = rank
            feature = str(contribution_metric.get("feature") or "").strip()
            if not feature:
                issues.append(
                    _issue(
                        rule_id="contribution_feature_missing",
                        message="shap grouped decision path contribution features must be non-empty",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}].feature",
                    )
                )
            group_feature_order.append(feature)
            shap_value = _require_numeric(
                contribution_metric.get("shap_value"),
                label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].shap_value",
            )
            if math.isclose(shap_value, 0.0, abs_tol=1e-12):
                issues.append(
                    _issue(
                        rule_id="contribution_value_zero",
                        message="shap grouped decision path contributions must be non-zero",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}].shap_value",
                    )
                )
            start_value = _require_numeric(
                contribution_metric.get("start_value"),
                label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].start_value",
            )
            end_value = _require_numeric(
                contribution_metric.get("end_value"),
                label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].end_value",
            )
            if not math.isclose(end_value, start_value + shap_value, rel_tol=1e-9, abs_tol=1e-9):
                issues.append(
                    _issue(
                        rule_id="contribution_path_invalid",
                        message="shap grouped decision path contribution end_value must equal start_value plus shap_value",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}]",
                        observed={"start_value": start_value, "end_value": end_value, "shap_value": shap_value},
                    )
                )
            contribution_sum += shap_value

        if tuple(group_feature_order) != tuple(feature_order):
            issues.append(
                _issue(
                    rule_id="group_feature_order_mismatch",
                    message="all shap grouped decision path groups must keep the shared feature order",
                    target=f"metrics.groups[{group_index}].contributions",
                    observed={"feature_order": group_feature_order},
                    expected={"feature_order": list(feature_order)},
                )
            )
        if not math.isclose(predicted_value, baseline_value + contribution_sum, rel_tol=1e-9, abs_tol=1e-9):
            issues.append(
                _issue(
                    rule_id="group_prediction_value_mismatch",
                    message="shap grouped decision path predicted_value must equal baseline_value plus contribution sum",
                    target=f"metrics.groups[{group_index}].predicted_value",
                    observed={"baseline_value": baseline_value, "predicted_value": predicted_value, "contribution_sum": contribution_sum},
                )
            )

    return issues


def _check_publication_shap_multigroup_decision_path_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = (
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "feature_label",
        "decision_path_line",
        "prediction_label",
        "baseline_reference_line",
        "prediction_marker",
    )
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types = ("title",) + required_box_types
    issues.extend(_check_required_box_types(all_boxes, required_box_types=required_box_types))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 1:
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap multigroup decision path panel requires exactly one panel box",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"panel_boxes": 1},
            )
        )
    panel_box = panel_boxes[0] if panel_boxes else None

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}

    legend_box = layout_box_by_id.get("legend_box")
    if legend_box is None:
        issues.append(
            _issue(
                rule_id="legend_box_missing",
                message="shap multigroup decision path panel requires an explicit legend box",
                target="legend_box",
                expected="present",
            )
        )
    elif panel_box is not None and _boxes_overlap(legend_box, panel_box):
        issues.append(
            _issue(
                rule_id="legend_box_overlaps_panel",
                message="shap multigroup decision path legend must stay outside the main panel region",
                target="legend_box",
                box_refs=(legend_box.box_id, panel_box.box_id),
            )
        )

    legend_title_box = layout_box_by_id.get("legend_title")
    if legend_title_box is None:
        issues.append(
            _issue(
                rule_id="legend_title_missing",
                message="shap multigroup decision path panel requires an explicit legend title",
                target="legend_title",
                expected="present",
            )
        )

    metrics_panel_box_id = str(sidecar.metrics.get("panel_box_id") or "").strip()
    if panel_box is not None and metrics_panel_box_id and metrics_panel_box_id != panel_box.box_id:
        issues.append(
            _issue(
                rule_id="panel_box_mismatch",
                message="shap multigroup decision path metrics must reference the primary panel box",
                target="metrics.panel_box_id",
                observed=metrics_panel_box_id,
                expected=panel_box.box_id,
            )
        )

    baseline_line_box_id = str(sidecar.metrics.get("baseline_line_box_id") or "").strip()
    baseline_line = guide_box_by_id.get(baseline_line_box_id) if baseline_line_box_id else None
    if baseline_line is None:
        issues.append(
            _issue(
                rule_id="baseline_reference_line_missing",
                message="shap multigroup decision path panel requires a baseline reference line",
                target="metrics.baseline_line_box_id",
                observed=baseline_line_box_id or None,
                expected="present",
                box_refs=((panel_box.box_id,) if panel_box is not None else ()),
            )
        )
    elif panel_box is not None and not _box_within_box(baseline_line, panel_box):
        issues.append(
            _issue(
                rule_id="baseline_reference_line_outside_panel",
                message="shap multigroup decision path baseline reference line must stay within the panel region",
                target=f"guide_boxes.{baseline_line.box_id}",
                box_refs=(baseline_line.box_id, panel_box.box_id),
            )
        )

    baseline_value = _require_numeric(sidecar.metrics.get("baseline_value"), label="layout_sidecar.metrics.baseline_value")
    feature_order_payload = sidecar.metrics.get("feature_order")
    if not isinstance(feature_order_payload, list) or not feature_order_payload:
        issues.append(
            _issue(
                rule_id="feature_order_missing",
                message="shap multigroup decision path metrics require a non-empty shared feature order",
                target="metrics.feature_order",
            )
        )
        feature_order: tuple[str, ...] = ()
    else:
        feature_order = tuple(str(item or "").strip() for item in feature_order_payload)
        if any(not item for item in feature_order):
            issues.append(
                _issue(
                    rule_id="feature_order_invalid",
                    message="shap multigroup decision path feature_order entries must be non-empty",
                    target="metrics.feature_order",
                )
            )

    feature_label_box_ids_payload = sidecar.metrics.get("feature_label_box_ids")
    if not isinstance(feature_label_box_ids_payload, list) or len(feature_label_box_ids_payload) != len(feature_order):
        issues.append(
            _issue(
                rule_id="feature_label_count_mismatch",
                message="shap multigroup decision path feature label boxes must match the shared feature order length",
                target="metrics.feature_label_box_ids",
                observed={"feature_label_box_ids": len(feature_label_box_ids_payload or []) if isinstance(feature_label_box_ids_payload, list) else None},
                expected={"feature_order": len(feature_order)},
            )
        )
        feature_label_box_ids: tuple[str, ...] = ()
    else:
        feature_label_box_ids = tuple(str(item or "").strip() for item in feature_label_box_ids_payload)
        for feature_label_box_id in feature_label_box_ids:
            box = layout_box_by_id.get(feature_label_box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id="feature_label_missing",
                        message="shap multigroup decision path metrics must reference existing feature label boxes",
                        target="metrics.feature_label_box_ids",
                        observed=feature_label_box_id,
                    )
                )
                continue
            if panel_box is not None and _boxes_overlap(box, panel_box):
                issues.append(
                    _issue(
                        rule_id="feature_label_panel_overlap",
                        message="shap multigroup decision path feature labels must stay outside the panel region",
                        target=f"layout_boxes.{box.box_id}",
                        box_refs=(box.box_id, panel_box.box_id),
                    )
                )

    groups_payload = sidecar.metrics.get("groups")
    if not isinstance(groups_payload, list) or len(groups_payload) != 3:
        issues.append(
            _issue(
                rule_id="group_count_invalid",
                message="shap multigroup decision path metrics require exactly three groups",
                target="metrics.groups",
                observed={"groups": len(groups_payload) if isinstance(groups_payload, list) else None},
                expected={"groups": 3},
            )
        )
        return issues

    seen_group_ids: set[str] = set()
    seen_group_labels: set[str] = set()
    for group_index, group_metric in enumerate(groups_payload):
        if not isinstance(group_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.groups[{group_index}] must be an object")
        group_id = str(group_metric.get("group_id") or "").strip()
        group_label = str(group_metric.get("group_label") or "").strip()
        predicted_value = _require_numeric(
            group_metric.get("predicted_value"),
            label=f"layout_sidecar.metrics.groups[{group_index}].predicted_value",
        )
        if not group_id:
            issues.append(
                _issue(
                    rule_id="group_id_missing",
                    message="shap multigroup decision path groups must declare a non-empty group_id",
                    target=f"metrics.groups[{group_index}].group_id",
                )
            )
        elif group_id in seen_group_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_group_id",
                    message="shap multigroup decision path group_ids must be unique",
                    target=f"metrics.groups[{group_index}].group_id",
                    observed=group_id,
                )
            )
        seen_group_ids.add(group_id)
        if not group_label:
            issues.append(
                _issue(
                    rule_id="group_label_missing",
                    message="shap multigroup decision path groups must declare a non-empty group_label",
                    target=f"metrics.groups[{group_index}].group_label",
                )
            )
        elif group_label in seen_group_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_group_label",
                    message="shap multigroup decision path group_labels must be unique",
                    target=f"metrics.groups[{group_index}].group_label",
                    observed=group_label,
                )
            )
        seen_group_labels.add(group_label)

        line_box_id = str(group_metric.get("line_box_id") or "").strip()
        line_box = layout_box_by_id.get(line_box_id)
        if line_box is None:
            issues.append(
                _issue(
                    rule_id="decision_path_line_missing",
                    message="shap multigroup decision path groups must reference an existing decision-path line box",
                    target=f"metrics.groups[{group_index}].line_box_id",
                    observed=line_box_id or None,
                    box_refs=((panel_box.box_id,) if panel_box is not None else ()),
                )
            )
        elif panel_box is not None and not _box_within_box(line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="decision_path_line_outside_panel",
                    message="shap multigroup decision path lines must stay within the panel region",
                    target=f"layout_boxes.{line_box.box_id}",
                    box_refs=(line_box.box_id, panel_box.box_id),
                )
            )

        prediction_marker_box_id = str(group_metric.get("prediction_marker_box_id") or "").strip()
        prediction_marker = guide_box_by_id.get(prediction_marker_box_id)
        if prediction_marker is None:
            issues.append(
                _issue(
                    rule_id="prediction_marker_missing",
                    message="shap multigroup decision path groups must reference an existing prediction marker box",
                    target=f"metrics.groups[{group_index}].prediction_marker_box_id",
                    observed=prediction_marker_box_id or None,
                    box_refs=((panel_box.box_id,) if panel_box is not None else ()),
                )
            )
        elif panel_box is not None and not _box_within_box(prediction_marker, panel_box):
            issues.append(
                _issue(
                    rule_id="prediction_marker_outside_panel",
                    message="shap multigroup decision path prediction markers must stay within the panel region",
                    target=f"guide_boxes.{prediction_marker.box_id}",
                    box_refs=(prediction_marker.box_id, panel_box.box_id),
                )
            )

        prediction_label_box_id = str(group_metric.get("prediction_label_box_id") or "").strip()
        prediction_label_box = layout_box_by_id.get(prediction_label_box_id)
        if prediction_label_box is None:
            issues.append(
                _issue(
                    rule_id="prediction_label_missing",
                    message="shap multigroup decision path groups must reference an existing prediction label box",
                    target=f"metrics.groups[{group_index}].prediction_label_box_id",
                    observed=prediction_label_box_id or None,
                )
            )

        contributions_payload = group_metric.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            issues.append(
                _issue(
                    rule_id="contributions_missing",
                    message="shap multigroup decision path groups require non-empty contributions",
                    target=f"metrics.groups[{group_index}].contributions",
                )
            )
            continue

        previous_rank = 0
        contribution_sum = 0.0
        group_feature_order: list[str] = []
        for contribution_index, contribution_metric in enumerate(contributions_payload):
            if not isinstance(contribution_metric, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}] must be an object"
                )
            rank = int(
                _require_numeric(
                    contribution_metric.get("rank"),
                    label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].rank",
                )
            )
            if rank <= previous_rank:
                issues.append(
                    _issue(
                        rule_id="contribution_rank_invalid",
                        message="shap multigroup decision path contribution ranks must be strictly increasing",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}].rank",
                    )
                )
            previous_rank = rank
            feature = str(contribution_metric.get("feature") or "").strip()
            if not feature:
                issues.append(
                    _issue(
                        rule_id="contribution_feature_missing",
                        message="shap multigroup decision path contribution features must be non-empty",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}].feature",
                    )
                )
            group_feature_order.append(feature)
            shap_value = _require_numeric(
                contribution_metric.get("shap_value"),
                label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].shap_value",
            )
            if math.isclose(shap_value, 0.0, abs_tol=1e-12):
                issues.append(
                    _issue(
                        rule_id="contribution_value_zero",
                        message="shap multigroup decision path contributions must be non-zero",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}].shap_value",
                    )
                )
            start_value = _require_numeric(
                contribution_metric.get("start_value"),
                label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].start_value",
            )
            end_value = _require_numeric(
                contribution_metric.get("end_value"),
                label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].end_value",
            )
            if not math.isclose(end_value, start_value + shap_value, rel_tol=1e-9, abs_tol=1e-9):
                issues.append(
                    _issue(
                        rule_id="contribution_path_invalid",
                        message="shap multigroup decision path contribution end_value must equal start_value plus shap_value",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}]",
                        observed={"start_value": start_value, "end_value": end_value, "shap_value": shap_value},
                    )
                )
            contribution_sum += shap_value

        if tuple(group_feature_order) != tuple(feature_order):
            issues.append(
                _issue(
                    rule_id="group_feature_order_mismatch",
                    message="all shap multigroup decision path groups must keep the shared feature order",
                    target=f"metrics.groups[{group_index}].contributions",
                    observed={"feature_order": group_feature_order},
                    expected={"feature_order": list(feature_order)},
                )
            )
        if not math.isclose(predicted_value, baseline_value + contribution_sum, rel_tol=1e-9, abs_tol=1e-9):
            issues.append(
                _issue(
                    rule_id="group_prediction_value_mismatch",
                    message="shap multigroup decision path predicted_value must equal baseline_value plus contribution sum",
                    target=f"metrics.groups[{group_index}].predicted_value",
                    observed={"baseline_value": baseline_value, "predicted_value": predicted_value, "contribution_sum": contribution_sum},
                )
            )

    return issues


def _check_publication_partial_dependence_ice_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "panel_label",
        "pdp_reference_label",
        "legend_box",
        "pdp_reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label", "pdp_reference_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    legend_labels = sidecar.metrics.get("legend_labels")
    if legend_labels != ["ICE curves", "PDP mean"]:
        issues.append(
            _issue(
                rule_id="legend_labels_invalid",
                message="partial dependence + ICE legend must declare exactly ICE curves and PDP mean",
                target="metrics.legend_labels",
                observed=legend_labels,
                expected=["ICE curves", "PDP mean"],
            )
        )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="partial dependence + ICE qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="partial dependence + ICE panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        x_label = str(panel_metric.get("x_label") or "").strip()
        feature = str(panel_metric.get("feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        reference_value = _require_numeric(
            panel_metric.get("reference_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_value",
        )
        if not panel_id or not panel_label or not title or not x_label or not feature or not reference_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="partial dependence + ICE panel metrics must declare panel metadata and reference labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="partial dependence + ICE metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        pdp_points = panel_metric.get("pdp_points")
        if not isinstance(pdp_points, list) or not pdp_points:
            issues.append(
                _issue(
                    rule_id="pdp_points_missing",
                    message="partial dependence + ICE panel metrics must contain non-empty PDP points",
                    target=f"metrics.panels[{panel_index}].pdp_points",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for point_index, point in enumerate(pdp_points):
                if not isinstance(point, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].pdp_points[{point_index}] must be an object")
                x_value = _require_numeric(
                    point.get("x"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].pdp_points[{point_index}].x",
                )
                y_value = _require_numeric(
                    point.get("y"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].pdp_points[{point_index}].y",
                )
                if _point_within_box(panel_box, x=x_value, y=y_value):
                    continue
                issues.append(
                    _issue(
                        rule_id="pdp_point_outside_panel",
                        message="PDP curve points must stay within the declared panel region",
                        target=f"metrics.panels[{panel_index}].pdp_points[{point_index}]",
                        observed={"x": x_value, "y": y_value},
                        box_refs=(panel_box.box_id,),
                    )
                )

        ice_curves = panel_metric.get("ice_curves")
        if not isinstance(ice_curves, list) or not ice_curves:
            issues.append(
                _issue(
                    rule_id="ice_curves_missing",
                    message="partial dependence + ICE panel metrics must contain non-empty ICE curves",
                    target=f"metrics.panels[{panel_index}].ice_curves",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for curve_index, curve in enumerate(ice_curves):
                if not isinstance(curve, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}] must be an object")
                points = curve.get("points")
                if not isinstance(points, list) or not points:
                    issues.append(
                        _issue(
                            rule_id="ice_curve_points_missing",
                            message="each ICE curve must carry non-empty normalized points",
                            target=f"metrics.panels[{panel_index}].ice_curves[{curve_index}]",
                            box_refs=(panel_box.box_id,),
                        )
                    )
                    continue
                for point_index, point in enumerate(points):
                    if not isinstance(point, dict):
                        raise ValueError(
                            f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}] must be an object"
                        )
                    x_value = _require_numeric(
                        point.get("x"),
                        label=(
                            f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}].x"
                        ),
                    )
                    y_value = _require_numeric(
                        point.get("y"),
                        label=(
                            f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}].y"
                        ),
                    )
                    if _point_within_box(panel_box, x=x_value, y=y_value):
                        continue
                    issues.append(
                        _issue(
                            rule_id="ice_point_outside_panel",
                            message="ICE curve points must stay within the declared panel region",
                            target=(
                                f"metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}]"
                            ),
                            observed={"x": x_value, "y": y_value},
                            box_refs=(panel_box.box_id,),
                        )
                    )

        reference_line_box_id = str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="partial dependence + ICE requires one reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    observed={"reference_value": reference_value},
                    box_refs=(reference_line_box.box_id, panel_box.box_id),
                )
            )

        reference_label_box_id = (
            str(panel_metric.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_label}"
        )
        reference_label_box = layout_box_by_id.get(reference_label_box_id)
        if reference_label_box is None:
            issues.append(
                _issue(
                    rule_id="reference_label_missing",
                    message="partial dependence + ICE requires one reference label per panel",
                    target=f"metrics.panels[{panel_index}].reference_label_box_id",
                    observed={"reference_label_box_id": reference_label_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_label_outside_panel",
                    message="reference label must stay within the panel region",
                    target=f"layout_boxes.{reference_label_box.box_id}",
                    box_refs=(reference_label_box.box_id, panel_box.box_id),
                )
            )

        if reference_line_box is not None and reference_label_box is not None:
            reference_line_mid_x = (reference_line_box.x0 + reference_line_box.x1) / 2.0
            reference_label_mid_x = (reference_label_box.x0 + reference_label_box.x1) / 2.0
            alignment_tolerance = max((panel_box.x1 - panel_box.x0) * 0.18, 0.05)
            if abs(reference_line_mid_x - reference_label_mid_x) > alignment_tolerance:
                issues.append(
                    _issue(
                        rule_id="reference_label_misaligned",
                        message="reference label must stay horizontally aligned to its reference line",
                        target=f"layout_boxes.{reference_label_box.box_id}",
                        observed={"label_mid_x": reference_label_mid_x, "line_mid_x": reference_line_mid_x},
                        box_refs=(reference_label_box.box_id, reference_line_box.box_id),
                    )
                )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.30,
            max_left_offset_ratio=0.40,
        )
    )
    return issues


def _check_publication_partial_dependence_interaction_contour_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "panel_label",
        "interaction_reference_label",
        "colorbar",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_colorbar_panel_overlap(sidecar))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label", "interaction_reference_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    colorbar_label = str(sidecar.metrics.get("colorbar_label") or "").strip()
    if not colorbar_label:
        issues.append(
            _issue(
                rule_id="colorbar_label_missing",
                message="partial dependence interaction contour qc requires a non-empty colorbar label metric",
                target="metrics.colorbar_label",
            )
        )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="partial dependence interaction contour qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="partial dependence interaction contour panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        x_label = str(panel_metric.get("x_label") or "").strip()
        y_label = str(panel_metric.get("y_label") or "").strip()
        x_feature = str(panel_metric.get("x_feature") or "").strip()
        y_feature = str(panel_metric.get("y_feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        reference_x_value = _require_numeric(
            panel_metric.get("reference_x_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_x_value",
        )
        reference_y_value = _require_numeric(
            panel_metric.get("reference_y_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_y_value",
        )
        if (
            not panel_id
            or not panel_label
            or not title
            or not x_label
            or not y_label
            or not x_feature
            or not y_feature
            or not reference_label
        ):
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="partial dependence interaction contour panel metrics must declare panel metadata and reference labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="partial dependence interaction contour metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        x_grid = panel_metric.get("x_grid")
        y_grid = panel_metric.get("y_grid")
        response_grid = panel_metric.get("response_grid")
        if not isinstance(x_grid, list) or len(x_grid) < 2 or not isinstance(y_grid, list) or len(y_grid) < 2:
            issues.append(
                _issue(
                    rule_id="grid_missing",
                    message="partial dependence interaction contour metrics require non-empty x_grid and y_grid",
                    target=f"metrics.panels[{panel_index}]",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue
        x_values = [_require_numeric(value, label=f"layout_sidecar.metrics.panels[{panel_index}].x_grid[{idx}]") for idx, value in enumerate(x_grid)]
        y_values = [_require_numeric(value, label=f"layout_sidecar.metrics.panels[{panel_index}].y_grid[{idx}]") for idx, value in enumerate(y_grid)]
        if any(right <= left for left, right in zip(x_values, x_values[1:], strict=False)):
            issues.append(
                _issue(
                    rule_id="x_grid_not_increasing",
                    message="partial dependence interaction contour x_grid must be strictly increasing",
                    target=f"metrics.panels[{panel_index}].x_grid",
                    observed={"x_grid": x_values},
                    box_refs=(panel_box.box_id,),
                )
            )
        if any(right <= left for left, right in zip(y_values, y_values[1:], strict=False)):
            issues.append(
                _issue(
                    rule_id="y_grid_not_increasing",
                    message="partial dependence interaction contour y_grid must be strictly increasing",
                    target=f"metrics.panels[{panel_index}].y_grid",
                    observed={"y_grid": y_values},
                    box_refs=(panel_box.box_id,),
                )
            )
        if not isinstance(response_grid, list) or len(response_grid) != len(y_values):
            issues.append(
                _issue(
                    rule_id="response_grid_shape_mismatch",
                    message="response_grid row count must match y_grid length",
                    target=f"metrics.panels[{panel_index}].response_grid",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for row_index, row in enumerate(response_grid):
                if not isinstance(row, list) or len(row) != len(x_values):
                    issues.append(
                        _issue(
                            rule_id="response_grid_shape_mismatch",
                            message="each response_grid row must match x_grid length",
                            target=f"metrics.panels[{panel_index}].response_grid[{row_index}]",
                            box_refs=(panel_box.box_id,),
                        )
                    )
                    continue
                for column_index, value in enumerate(row):
                    numeric_value = _require_numeric(
                        value,
                        label=f"layout_sidecar.metrics.panels[{panel_index}].response_grid[{row_index}][{column_index}]",
                    )
                    if not math.isfinite(numeric_value):
                        issues.append(
                            _issue(
                                rule_id="response_value_not_finite",
                                message="partial dependence interaction contour response values must be finite",
                                target=f"metrics.panels[{panel_index}].response_grid[{row_index}][{column_index}]",
                                box_refs=(panel_box.box_id,),
                            )
                        )

        if not (x_values[0] <= reference_x_value <= x_values[-1]) or not (y_values[0] <= reference_y_value <= y_values[-1]):
            issues.append(
                _issue(
                    rule_id="reference_point_outside_grid",
                    message="partial dependence interaction contour reference point must fall within declared grid range",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"reference_x_value": reference_x_value, "reference_y_value": reference_y_value},
                    box_refs=(panel_box.box_id,),
                )
            )

        observed_points = panel_metric.get("observed_points")
        if not isinstance(observed_points, list) or not observed_points:
            issues.append(
                _issue(
                    rule_id="observed_points_missing",
                    message="partial dependence interaction contour metrics must contain non-empty observed_points",
                    target=f"metrics.panels[{panel_index}].observed_points",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for point_index, point in enumerate(observed_points):
                if not isinstance(point, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].observed_points[{point_index}] must be an object")
                point_x = _require_numeric(
                    point.get("x"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].observed_points[{point_index}].x",
                )
                point_y = _require_numeric(
                    point.get("y"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].observed_points[{point_index}].y",
                )
                if not _point_within_box(panel_box, x=point_x, y=point_y):
                    issues.append(
                        _issue(
                            rule_id="observed_point_outside_panel",
                            message="observed support points must stay within the declared panel region",
                            target=f"metrics.panels[{panel_index}].observed_points[{point_index}]",
                            observed={"x": point_x, "y": point_y},
                            box_refs=(panel_box.box_id,),
                        )
                    )

        reference_vertical_box_id = (
            str(panel_metric.get("reference_vertical_box_id") or "").strip() or f"reference_vertical_{panel_label}"
        )
        reference_vertical_box = guide_box_by_id.get(reference_vertical_box_id)
        if reference_vertical_box is None:
            issues.append(
                _issue(
                    rule_id="reference_vertical_missing",
                    message="partial dependence interaction contour requires one vertical reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_vertical_box_id",
                    observed={"reference_vertical_box_id": reference_vertical_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_vertical_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_vertical_outside_panel",
                    message="vertical reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_vertical_box.box_id}",
                    box_refs=(reference_vertical_box.box_id, panel_box.box_id),
                )
            )

        reference_horizontal_box_id = (
            str(panel_metric.get("reference_horizontal_box_id") or "").strip() or f"reference_horizontal_{panel_label}"
        )
        reference_horizontal_box = guide_box_by_id.get(reference_horizontal_box_id)
        if reference_horizontal_box is None:
            issues.append(
                _issue(
                    rule_id="reference_horizontal_missing",
                    message="partial dependence interaction contour requires one horizontal reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_horizontal_box_id",
                    observed={"reference_horizontal_box_id": reference_horizontal_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_horizontal_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_horizontal_outside_panel",
                    message="horizontal reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_horizontal_box.box_id}",
                    box_refs=(reference_horizontal_box.box_id, panel_box.box_id),
                )
            )

        reference_label_box_id = (
            str(panel_metric.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_label}"
        )
        reference_label_box = layout_box_by_id.get(reference_label_box_id)
        if reference_label_box is None:
            issues.append(
                _issue(
                    rule_id="reference_label_missing",
                    message="partial dependence interaction contour requires one reference label per panel",
                    target=f"metrics.panels[{panel_index}].reference_label_box_id",
                    observed={"reference_label_box_id": reference_label_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_label_outside_panel",
                    message="reference label must stay within the panel region",
                    target=f"layout_boxes.{reference_label_box.box_id}",
                    box_refs=(reference_label_box.box_id, panel_box.box_id),
                )
            )

    return issues


def _check_publication_partial_dependence_interaction_slice_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "panel_label",
        "slice_reference_label",
        "legend_title",
        "legend_box",
        "slice_reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {
            "title",
            "panel_title",
            "subplot_x_axis_title",
            "subplot_y_axis_title",
            "panel_label",
            "slice_reference_label",
            "legend_title",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    legend_title = str(sidecar.metrics.get("legend_title") or "").strip()
    if legend_title != "Conditioning profile":
        issues.append(
            _issue(
                rule_id="legend_title_invalid",
                message="interaction slice legend_title must be exactly `Conditioning profile`",
                target="metrics.legend_title",
                observed=legend_title,
                expected="Conditioning profile",
            )
        )

    legend_labels = sidecar.metrics.get("legend_labels")
    if not isinstance(legend_labels, list) or len(legend_labels) < 2:
        issues.append(
            _issue(
                rule_id="legend_labels_missing",
                message="interaction slice legend_labels must contain at least two ordered labels",
                target="metrics.legend_labels",
            )
        )
        legend_label_list: list[str] = []
    else:
        legend_label_list = [str(item or "").strip() for item in legend_labels]
        if any(not item for item in legend_label_list) or len(set(legend_label_list)) != len(legend_label_list):
            issues.append(
                _issue(
                    rule_id="legend_labels_invalid",
                    message="interaction slice legend_labels must be non-empty and unique",
                    target="metrics.legend_labels",
                    observed=legend_labels,
                )
            )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="interaction slice qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="interaction slice panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}
    expected_slice_labels: tuple[str, ...] | None = None

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        x_label = str(panel_metric.get("x_label") or "").strip()
        x_feature = str(panel_metric.get("x_feature") or "").strip()
        slice_feature = str(panel_metric.get("slice_feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        _require_numeric(
            panel_metric.get("reference_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_value",
        )
        if not panel_id or not panel_label or not title or not x_label or not x_feature or not slice_feature or not reference_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="interaction slice panel metrics must declare panel metadata and reference labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="interaction slice metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        slice_curves = panel_metric.get("slice_curves")
        if not isinstance(slice_curves, list) or len(slice_curves) < 2:
            issues.append(
                _issue(
                    rule_id="slice_curves_missing",
                    message="interaction slice panels require at least two slice curves",
                    target=f"metrics.panels[{panel_index}].slice_curves",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        current_slice_labels: list[str] = []
        for curve_index, curve in enumerate(slice_curves):
            if not isinstance(curve, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].slice_curves[{curve_index}] must be an object")
            slice_label = str(curve.get("slice_label") or "").strip()
            if not slice_label:
                issues.append(
                    _issue(
                        rule_id="slice_label_missing",
                        message="interaction slice curves must carry non-empty slice_label values",
                        target=f"metrics.panels[{panel_index}].slice_curves[{curve_index}].slice_label",
                    )
                )
            else:
                current_slice_labels.append(slice_label)
            points = curve.get("points")
            if not isinstance(points, list) or not points:
                issues.append(
                    _issue(
                        rule_id="slice_curve_points_missing",
                        message="interaction slice curves must carry non-empty normalized points",
                        target=f"metrics.panels[{panel_index}].slice_curves[{curve_index}].points",
                        box_refs=(panel_box.box_id,),
                    )
                )
                continue
            for point_index, point in enumerate(points):
                if not isinstance(point, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.panels[{panel_index}].slice_curves[{curve_index}].points[{point_index}] must be an object"
                    )
                x_value = _require_numeric(
                    point.get("x"),
                    label=(
                        f"layout_sidecar.metrics.panels[{panel_index}].slice_curves[{curve_index}].points[{point_index}].x"
                    ),
                )
                y_value = _require_numeric(
                    point.get("y"),
                    label=(
                        f"layout_sidecar.metrics.panels[{panel_index}].slice_curves[{curve_index}].points[{point_index}].y"
                    ),
                )
                if _point_within_box(panel_box, x=x_value, y=y_value):
                    continue
                issues.append(
                    _issue(
                        rule_id="slice_point_outside_panel",
                        message="interaction slice points must stay within the declared panel region",
                        target=f"metrics.panels[{panel_index}].slice_curves[{curve_index}].points[{point_index}]",
                        observed={"x": x_value, "y": y_value},
                        box_refs=(panel_box.box_id,),
                    )
                )

        if expected_slice_labels is None:
            expected_slice_labels = tuple(current_slice_labels)
        elif tuple(current_slice_labels) != expected_slice_labels:
            issues.append(
                _issue(
                    rule_id="legend_labels_invalid",
                    message="interaction slice panels must keep the same ordered slice labels across panels",
                    target=f"metrics.panels[{panel_index}].slice_curves",
                    observed=current_slice_labels,
                    expected=list(expected_slice_labels),
                )
            )
        if legend_label_list and current_slice_labels and current_slice_labels != legend_label_list:
            issues.append(
                _issue(
                    rule_id="legend_labels_invalid",
                    message="interaction slice legend_labels must match the ordered slice_label set in each panel",
                    target=f"metrics.panels[{panel_index}].slice_curves",
                    observed=current_slice_labels,
                    expected=legend_label_list,
                )
            )

        reference_line_box_id = (
            str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        )
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="interaction slice requires one reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="interaction slice reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    box_refs=(reference_line_box.box_id, panel_box.box_id),
                )
            )

        reference_label_box_id = (
            str(panel_metric.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_label}"
        )
        reference_label_box = layout_box_by_id.get(reference_label_box_id)
        if reference_label_box is None:
            issues.append(
                _issue(
                    rule_id="reference_label_missing",
                    message="interaction slice requires one reference label per panel",
                    target=f"metrics.panels[{panel_index}].reference_label_box_id",
                    observed={"reference_label_box_id": reference_label_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_label_outside_panel",
                    message="interaction slice reference label must stay within the panel region",
                    target=f"layout_boxes.{reference_label_box.box_id}",
                    box_refs=(reference_label_box.box_id, panel_box.box_id),
                )
            )

        if reference_line_box is not None and reference_label_box is not None:
            reference_line_mid_x = (reference_line_box.x0 + reference_line_box.x1) / 2.0
            reference_label_mid_x = (reference_label_box.x0 + reference_label_box.x1) / 2.0
            alignment_tolerance = max((panel_box.x1 - panel_box.x0) * 0.18, 0.05)
            if abs(reference_line_mid_x - reference_label_mid_x) > alignment_tolerance:
                issues.append(
                    _issue(
                        rule_id="reference_label_misaligned",
                        message="interaction slice reference labels must stay horizontally aligned to their reference line",
                        target=f"layout_boxes.{reference_label_box.box_id}",
                        observed={"label_mid_x": reference_label_mid_x, "line_mid_x": reference_line_mid_x},
                        box_refs=(reference_label_box.box_id, reference_line_box.box_id),
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


def _check_publication_partial_dependence_subgroup_comparison_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subgroup_panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "subgroup_x_axis_title",
        "panel_label",
        "pdp_reference_label",
        "subgroup_row_label",
        "legend_box",
        "pdp_reference_line",
        "subgroup_ci_segment",
        "subgroup_estimate_marker",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {
            "title",
            "panel_title",
            "subgroup_panel_title",
            "subplot_x_axis_title",
            "subplot_y_axis_title",
            "subgroup_x_axis_title",
            "panel_label",
            "pdp_reference_label",
            "subgroup_row_label",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    legend_labels = sidecar.metrics.get("legend_labels")
    expected_legend_labels = ["ICE curves", "PDP mean", "Subgroup interval"]
    if legend_labels != expected_legend_labels:
        issues.append(
            _issue(
                rule_id="legend_labels_invalid",
                message="subgroup comparison legend must declare exactly ICE curves, PDP mean, and Subgroup interval",
                target="metrics.legend_labels",
                observed=legend_labels,
                expected=expected_legend_labels,
            )
        )

    top_panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    subgroup_panels = _boxes_of_type(sidecar.panel_boxes, "subgroup_panel")
    if len(subgroup_panels) != 1:
        issues.append(
            _issue(
                rule_id="subgroup_panel_missing",
                message="subgroup comparison qc requires exactly one subgroup_panel box",
                target="panel_boxes",
                observed={"subgroup_panel_count": len(subgroup_panels)},
                expected={"subgroup_panel_count": 1},
            )
        )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="subgroup comparison qc requires non-empty top-panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    subgroup_panel_metric = sidecar.metrics.get("subgroup_panel")
    if not isinstance(subgroup_panel_metric, dict):
        issues.append(
            _issue(
                rule_id="subgroup_panel_metrics_missing",
                message="subgroup comparison qc requires subgroup_panel metrics",
                target="metrics.subgroup_panel",
            )
        )
        return issues

    if len(top_panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="subgroup comparison top-panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(top_panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    label_panel_map: dict[str, str] = {}
    seen_panel_ids: set[str] = set()

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        subgroup_label = str(panel_metric.get("subgroup_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        x_label = str(panel_metric.get("x_label") or "").strip()
        feature = str(panel_metric.get("feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        _require_numeric(
            panel_metric.get("reference_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_value",
        )
        if not panel_id or not panel_label or not subgroup_label or not title or not x_label or not feature or not reference_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="subgroup comparison top-panel metrics must declare panel metadata and reference labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_panel_id",
                    message="subgroup comparison panel_id values must stay unique",
                    target="metrics.panels",
                    observed=panel_id,
                )
            )
            continue
        seen_panel_ids.add(panel_id)

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="subgroup comparison metrics must reference an existing top panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        pdp_points = panel_metric.get("pdp_points")
        if not isinstance(pdp_points, list) or not pdp_points:
            issues.append(
                _issue(
                    rule_id="pdp_points_missing",
                    message="subgroup comparison panels require non-empty pdp_points",
                    target=f"metrics.panels[{panel_index}].pdp_points",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for point_index, point in enumerate(pdp_points):
                if not isinstance(point, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].pdp_points[{point_index}] must be an object")
                x_value = _require_numeric(
                    point.get("x"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].pdp_points[{point_index}].x",
                )
                y_value = _require_numeric(
                    point.get("y"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].pdp_points[{point_index}].y",
                )
                if _point_within_box(panel_box, x=x_value, y=y_value):
                    continue
                issues.append(
                    _issue(
                        rule_id="pdp_point_outside_panel",
                        message="subgroup comparison PDP points must stay within the declared panel region",
                        target=f"metrics.panels[{panel_index}].pdp_points[{point_index}]",
                        observed={"x": x_value, "y": y_value},
                        box_refs=(panel_box.box_id,),
                    )
                )

        ice_curves = panel_metric.get("ice_curves")
        if not isinstance(ice_curves, list) or not ice_curves:
            issues.append(
                _issue(
                    rule_id="ice_curves_missing",
                    message="subgroup comparison panels require non-empty ice_curves",
                    target=f"metrics.panels[{panel_index}].ice_curves",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for curve_index, curve in enumerate(ice_curves):
                if not isinstance(curve, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}] must be an object")
                points = curve.get("points")
                if not isinstance(points, list) or not points:
                    issues.append(
                        _issue(
                            rule_id="ice_curve_points_missing",
                            message="subgroup comparison ICE curves must carry non-empty normalized points",
                            target=f"metrics.panels[{panel_index}].ice_curves[{curve_index}]",
                            box_refs=(panel_box.box_id,),
                        )
                    )
                    continue
                for point_index, point in enumerate(points):
                    if not isinstance(point, dict):
                        raise ValueError(
                            f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}] must be an object"
                        )
                    x_value = _require_numeric(
                        point.get("x"),
                        label=(
                            f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}].x"
                        ),
                    )
                    y_value = _require_numeric(
                        point.get("y"),
                        label=(
                            f"layout_sidecar.metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}].y"
                        ),
                    )
                    if _point_within_box(panel_box, x=x_value, y=y_value):
                        continue
                    issues.append(
                        _issue(
                            rule_id="ice_point_outside_panel",
                            message="subgroup comparison ICE points must stay within the declared panel region",
                            target=(
                                f"metrics.panels[{panel_index}].ice_curves[{curve_index}].points[{point_index}]"
                            ),
                            observed={"x": x_value, "y": y_value},
                            box_refs=(panel_box.box_id,),
                        )
                    )

        reference_line_box_id = (
            str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        )
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="subgroup comparison requires one PDP reference line per top panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="subgroup comparison reference line must stay within the top panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    box_refs=(reference_line_box.box_id, panel_box.box_id),
                )
            )

        reference_label_box_id = (
            str(panel_metric.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_label}"
        )
        reference_label_box = layout_box_by_id.get(reference_label_box_id)
        if reference_label_box is None:
            issues.append(
                _issue(
                    rule_id="reference_label_missing",
                    message="subgroup comparison requires one reference label per top panel",
                    target=f"metrics.panels[{panel_index}].reference_label_box_id",
                    observed={"reference_label_box_id": reference_label_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_label_outside_panel",
                    message="subgroup comparison reference label must stay within the top panel region",
                    target=f"layout_boxes.{reference_label_box.box_id}",
                    box_refs=(reference_label_box.box_id, panel_box.box_id),
                )
            )

    subgroup_panel_label = str(subgroup_panel_metric.get("panel_label") or "").strip()
    subgroup_panel_title = str(subgroup_panel_metric.get("title") or "").strip()
    subgroup_x_label = str(subgroup_panel_metric.get("x_label") or "").strip()
    subgroup_panel_box_id = str(subgroup_panel_metric.get("panel_box_id") or "").strip() or "panel_C"
    subgroup_panel_box = panel_box_by_id.get(subgroup_panel_box_id)
    if not subgroup_panel_label or not subgroup_panel_title or not subgroup_x_label:
        issues.append(
            _issue(
                rule_id="subgroup_panel_metric_missing",
                message="subgroup comparison subgroup_panel metrics must declare panel metadata",
                target="metrics.subgroup_panel",
            )
        )
    if subgroup_panel_box is None:
        issues.append(
            _issue(
                rule_id="subgroup_panel_box_missing",
                message="subgroup comparison subgroup_panel must reference an existing subgroup_panel box",
                target="metrics.subgroup_panel.panel_box_id",
                observed={"panel_box_id": subgroup_panel_box_id},
            )
        )

    subgroup_rows = subgroup_panel_metric.get("rows")
    if not isinstance(subgroup_rows, list) or not subgroup_rows:
        issues.append(
            _issue(
                rule_id="subgroup_rows_missing",
                message="subgroup comparison subgroup_panel must contain non-empty rows",
                target="metrics.subgroup_panel.rows",
            )
        )
    elif subgroup_panel_box is not None:
        seen_row_panel_ids: set[str] = set()
        for row_index, row in enumerate(subgroup_rows):
            if not isinstance(row, dict):
                raise ValueError(f"layout_sidecar.metrics.subgroup_panel.rows[{row_index}] must be an object")
            row_panel_id = str(row.get("panel_id") or "").strip()
            if row_panel_id:
                seen_row_panel_ids.add(row_panel_id)
            label_box_id = str(row.get("label_box_id") or "").strip() or f"subgroup_row_label_{row_index + 1}"
            ci_segment_box_id = str(row.get("ci_segment_box_id") or "").strip() or f"subgroup_ci_segment_{row_index + 1}"
            estimate_marker_box_id = (
                str(row.get("estimate_marker_box_id") or "").strip() or f"subgroup_estimate_marker_{row_index + 1}"
            )

            if layout_box_by_id.get(label_box_id) is None:
                issues.append(
                    _issue(
                        rule_id="subgroup_row_label_missing",
                        message="subgroup comparison rows require explicit row labels",
                        target=f"metrics.subgroup_panel.rows[{row_index}].label_box_id",
                        observed={"label_box_id": label_box_id},
                    )
                )
            ci_segment_box = guide_box_by_id.get(ci_segment_box_id)
            if ci_segment_box is None:
                issues.append(
                    _issue(
                        rule_id="subgroup_ci_segment_missing",
                        message="subgroup comparison rows require a CI segment guide box",
                        target=f"metrics.subgroup_panel.rows[{row_index}].ci_segment_box_id",
                        observed={"ci_segment_box_id": ci_segment_box_id},
                        box_refs=(subgroup_panel_box.box_id,),
                    )
                )
            elif not _box_within_box(ci_segment_box, subgroup_panel_box):
                issues.append(
                    _issue(
                        rule_id="subgroup_ci_segment_outside_panel",
                        message="subgroup comparison CI segments must stay within the subgroup panel region",
                        target=f"guide_boxes.{ci_segment_box.box_id}",
                        box_refs=(ci_segment_box.box_id, subgroup_panel_box.box_id),
                    )
                )
            estimate_marker_box = guide_box_by_id.get(estimate_marker_box_id)
            if estimate_marker_box is None:
                issues.append(
                    _issue(
                        rule_id="subgroup_estimate_marker_missing",
                        message="subgroup comparison rows require an estimate marker guide box",
                        target=f"metrics.subgroup_panel.rows[{row_index}].estimate_marker_box_id",
                        observed={"estimate_marker_box_id": estimate_marker_box_id},
                        box_refs=(subgroup_panel_box.box_id,),
                    )
                )
            elif not _box_within_box(estimate_marker_box, subgroup_panel_box):
                issues.append(
                    _issue(
                        rule_id="subgroup_estimate_marker_outside_panel",
                        message="subgroup comparison estimate markers must stay within the subgroup panel region",
                        target=f"guide_boxes.{estimate_marker_box.box_id}",
                        box_refs=(estimate_marker_box.box_id, subgroup_panel_box.box_id),
                    )
                )

        if seen_panel_ids and seen_row_panel_ids and seen_row_panel_ids != seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="subgroup_row_panel_mismatch",
                    message="subgroup comparison subgroup rows must reference each declared top panel exactly once",
                    target="metrics.subgroup_panel.rows",
                    observed=sorted(seen_row_panel_ids),
                    expected=sorted(seen_panel_ids),
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


def _check_publication_accumulated_local_effects_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "panel_label",
        "ale_reference_label",
        "legend_box",
        "ale_reference_line",
        "local_effect_bin",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {
            "title",
            "panel_title",
            "subplot_x_axis_title",
            "subplot_y_axis_title",
            "panel_label",
            "ale_reference_label",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    legend_labels = sidecar.metrics.get("legend_labels")
    expected_legend_labels = ["Accumulated local effect", "Local effect per bin"]
    if legend_labels != expected_legend_labels:
        issues.append(
            _issue(
                rule_id="legend_labels_invalid",
                message="ALE legend must declare exactly Accumulated local effect and Local effect per bin",
                target="metrics.legend_labels",
                observed=legend_labels,
                expected=expected_legend_labels,
            )
        )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="ALE qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="ALE panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        x_label = str(panel_metric.get("x_label") or "").strip()
        feature = str(panel_metric.get("feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        _require_numeric(
            panel_metric.get("reference_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_value",
        )
        if not panel_id or not panel_label or not title or not x_label or not feature or not reference_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="ALE panel metrics must declare panel metadata and reference labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="ALE metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        ale_points = panel_metric.get("ale_points")
        if not isinstance(ale_points, list) or not ale_points:
            issues.append(
                _issue(
                    rule_id="ale_points_missing",
                    message="ALE panels require non-empty ale_points",
                    target=f"metrics.panels[{panel_index}].ale_points",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for point_index, point in enumerate(ale_points):
                if not isinstance(point, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].ale_points[{point_index}] must be an object")
                x_value = _require_numeric(
                    point.get("x"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].ale_points[{point_index}].x",
                )
                y_value = _require_numeric(
                    point.get("y"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].ale_points[{point_index}].y",
                )
                if _point_within_box(panel_box, x=x_value, y=y_value):
                    continue
                issues.append(
                    _issue(
                        rule_id="ale_point_outside_panel",
                        message="ALE curve points must stay within the declared panel region",
                        target=f"metrics.panels[{panel_index}].ale_points[{point_index}]",
                        observed={"x": x_value, "y": y_value},
                        box_refs=(panel_box.box_id,),
                    )
                )

        local_effect_bins = panel_metric.get("local_effect_bins")
        if not isinstance(local_effect_bins, list) or not local_effect_bins:
            issues.append(
                _issue(
                    rule_id="local_effect_bins_missing",
                    message="ALE panels require non-empty local_effect_bins",
                    target=f"metrics.panels[{panel_index}].local_effect_bins",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for bin_index, bin_metric in enumerate(local_effect_bins):
                if not isinstance(bin_metric, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.panels[{panel_index}].local_effect_bins[{bin_index}] must be an object"
                    )
                bin_box_id = str(bin_metric.get("bin_box_id") or "").strip()
                if not bin_box_id:
                    issues.append(
                        _issue(
                            rule_id="local_effect_bin_missing",
                            message="ALE bins must reference a local_effect_bin guide box",
                            target=f"metrics.panels[{panel_index}].local_effect_bins[{bin_index}].bin_box_id",
                            box_refs=(panel_box.box_id,),
                        )
                    )
                    continue
                bin_box = guide_box_by_id.get(bin_box_id)
                if bin_box is None:
                    issues.append(
                        _issue(
                            rule_id="local_effect_bin_missing",
                            message="ALE bins must reference an existing local_effect_bin guide box",
                            target=f"metrics.panels[{panel_index}].local_effect_bins[{bin_index}].bin_box_id",
                            observed={"bin_box_id": bin_box_id},
                            box_refs=(panel_box.box_id,),
                        )
                    )
                    continue
                if not _box_within_box(bin_box, panel_box):
                    issues.append(
                        _issue(
                            rule_id="local_effect_bin_outside_panel",
                            message="ALE local-effect bins must stay within the declared panel region",
                            target=f"guide_boxes.{bin_box.box_id}",
                            box_refs=(bin_box.box_id, panel_box.box_id),
                        )
                    )

        reference_line_box_id = (
            str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        )
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="ALE requires one reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="ALE reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    box_refs=(reference_line_box.box_id, panel_box.box_id),
                )
            )

        reference_label_box_id = (
            str(panel_metric.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_label}"
        )
        reference_label_box = layout_box_by_id.get(reference_label_box_id)
        if reference_label_box is None:
            issues.append(
                _issue(
                    rule_id="reference_label_missing",
                    message="ALE requires one reference label per panel",
                    target=f"metrics.panels[{panel_index}].reference_label_box_id",
                    observed={"reference_label_box_id": reference_label_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_label_outside_panel",
                    message="ALE reference label must stay within the panel region",
                    target=f"layout_boxes.{reference_label_box.box_id}",
                    box_refs=(reference_label_box.box_id, panel_box.box_id),
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )
    return issues


def _check_publication_feature_response_support_domain_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "panel_label",
        "support_domain_reference_label",
        "support_label",
        "legend_box",
        "support_domain_reference_line",
        "support_domain_segment",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {
            "title",
            "panel_title",
            "subplot_x_axis_title",
            "subplot_y_axis_title",
            "panel_label",
            "support_domain_reference_label",
            "support_label",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    legend_labels = sidecar.metrics.get("legend_labels")
    expected_legend_labels = [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]
    if legend_labels != expected_legend_labels:
        issues.append(
            _issue(
                rule_id="legend_labels_invalid",
                message=(
                    "feature-response support-domain legend must declare exactly Response curve, "
                    "Observed support, Subgroup support, Bin support, and Extrapolation reminder"
                ),
                target="metrics.legend_labels",
                observed=legend_labels,
                expected=expected_legend_labels,
            )
        )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="feature-response support-domain qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="feature-response support-domain panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}
    seen_panel_ids: set[str] = set()
    allowed_support_kinds = {
        "observed_support",
        "subgroup_support",
        "bin_support",
        "extrapolation_warning",
    }

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        x_label = str(panel_metric.get("x_label") or "").strip()
        feature = str(panel_metric.get("feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        _require_numeric(
            panel_metric.get("reference_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_value",
        )
        if not panel_id or not panel_label or not title or not x_label or not feature or not reference_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="feature-response support-domain panel metrics must declare panel metadata and reference labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_panel_id",
                    message="feature-response support-domain panel_id values must stay unique",
                    target="metrics.panels",
                    observed=panel_id,
                )
            )
            continue
        seen_panel_ids.add(panel_id)

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="feature-response support-domain metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        response_points = panel_metric.get("response_points")
        if not isinstance(response_points, list) or not response_points:
            issues.append(
                _issue(
                    rule_id="response_points_missing",
                    message="feature-response support-domain panels require non-empty response_points",
                    target=f"metrics.panels[{panel_index}].response_points",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for point_index, point in enumerate(response_points):
                if not isinstance(point, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.panels[{panel_index}].response_points[{point_index}] must be an object"
                    )
                x_value = _require_numeric(
                    point.get("x"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].response_points[{point_index}].x",
                )
                y_value = _require_numeric(
                    point.get("y"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].response_points[{point_index}].y",
                )
                if _point_within_box(panel_box, x=x_value, y=y_value):
                    continue
                issues.append(
                    _issue(
                        rule_id="response_point_outside_panel",
                        message="feature-response support-domain response points must stay within the declared panel region",
                        target=f"metrics.panels[{panel_index}].response_points[{point_index}]",
                        observed={"x": x_value, "y": y_value},
                        box_refs=(panel_box.box_id,),
                    )
                )

        reference_line_box_id = (
            str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        )
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="feature-response support-domain requires one reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="feature-response support-domain reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    box_refs=(reference_line_box.box_id, panel_box.box_id),
                )
            )

        reference_label_box_id = (
            str(panel_metric.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_label}"
        )
        reference_label_box = layout_box_by_id.get(reference_label_box_id)
        if reference_label_box is None:
            issues.append(
                _issue(
                    rule_id="reference_label_missing",
                    message="feature-response support-domain requires one reference label per panel",
                    target=f"metrics.panels[{panel_index}].reference_label_box_id",
                    observed={"reference_label_box_id": reference_label_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_label_outside_panel",
                    message="feature-response support-domain reference label must stay within the panel region",
                    target=f"layout_boxes.{reference_label_box.box_id}",
                    box_refs=(reference_label_box.box_id, panel_box.box_id),
                )
            )

        support_segments = panel_metric.get("support_segments")
        if not isinstance(support_segments, list) or not support_segments:
            issues.append(
                _issue(
                    rule_id="support_segments_missing",
                    message="feature-response support-domain panels require non-empty support_segments",
                    target=f"metrics.panels[{panel_index}].support_segments",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        seen_segment_ids: set[str] = set()
        for segment_index, segment in enumerate(support_segments):
            if not isinstance(segment, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].support_segments[{segment_index}] must be an object"
                )
            segment_id = str(segment.get("segment_id") or "").strip()
            support_kind = str(segment.get("support_kind") or "").strip()
            if not segment_id:
                issues.append(
                    _issue(
                        rule_id="support_segment_id_missing",
                        message="feature-response support-domain support segments must declare segment_id",
                        target=f"metrics.panels[{panel_index}].support_segments[{segment_index}]",
                    )
                )
            elif segment_id in seen_segment_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_support_segment_id",
                        message="feature-response support-domain segment_id values must stay unique within each panel",
                        target=f"metrics.panels[{panel_index}].support_segments",
                        observed=segment_id,
                    )
                )
            else:
                seen_segment_ids.add(segment_id)

            if support_kind not in allowed_support_kinds:
                issues.append(
                    _issue(
                        rule_id="support_kind_invalid",
                        message="feature-response support-domain support_kind must stay within the admitted set",
                        target=f"metrics.panels[{panel_index}].support_segments[{segment_index}].support_kind",
                        observed=support_kind,
                        expected=sorted(allowed_support_kinds),
                    )
                )

            segment_box_id = (
                str(segment.get("segment_box_id") or "").strip() or f"support_segment_{panel_label}_{segment_index + 1}"
            )
            segment_box = guide_box_by_id.get(segment_box_id)
            if segment_box is None:
                issues.append(
                    _issue(
                        rule_id="support_segment_missing",
                        message="feature-response support-domain segments require explicit guide boxes",
                        target=f"metrics.panels[{panel_index}].support_segments[{segment_index}].segment_box_id",
                        observed={"segment_box_id": segment_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif not _box_within_box(segment_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="support_segment_outside_panel",
                        message="feature-response support-domain support segments must stay within the declared panel region",
                        target=f"guide_boxes.{segment_box.box_id}",
                        box_refs=(segment_box.box_id, panel_box.box_id),
                    )
                )

            label_box_id = (
                str(segment.get("label_box_id") or "").strip() or f"support_label_{panel_label}_{segment_index + 1}"
            )
            label_box = layout_box_by_id.get(label_box_id)
            if label_box is None:
                issues.append(
                    _issue(
                        rule_id="support_label_missing",
                        message="feature-response support-domain segments require explicit support labels",
                        target=f"metrics.panels[{panel_index}].support_segments[{segment_index}].label_box_id",
                        observed={"label_box_id": label_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif not _box_within_box(label_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="support_label_outside_panel",
                        message="feature-response support-domain support labels must stay within the declared panel region",
                        target=f"layout_boxes.{label_box.box_id}",
                        box_refs=(label_box.box_id, panel_box.box_id),
                    )
                )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )
    return issues


def _subset_layout_sidecar(
    sidecar: LayoutSidecar,
    *,
    layout_box_ids: set[str],
    panel_box_ids: set[str],
    guide_box_ids: set[str],
    metrics: dict[str, Any],
) -> LayoutSidecar:
    return LayoutSidecar(
        template_id=sidecar.template_id,
        device=sidecar.device,
        layout_boxes=tuple(box for box in sidecar.layout_boxes if box.box_id in layout_box_ids),
        panel_boxes=tuple(box for box in sidecar.panel_boxes if box.box_id in panel_box_ids),
        guide_boxes=tuple(box for box in sidecar.guide_boxes if box.box_id in guide_box_ids),
        metrics=metrics,
        render_context=sidecar.render_context,
    )


def _check_publication_shap_grouped_local_support_domain_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    local_panels = metrics.get("local_panels")
    support_panels = metrics.get("support_panels")
    if not isinstance(local_panels, list) or not local_panels:
        issues.append(
            _issue(
                rule_id="local_panels_missing",
                message="grouped-local support-domain composite requires non-empty local_panels metrics",
                target="metrics.local_panels",
            )
        )
        return issues
    if not isinstance(support_panels, list) or len(support_panels) != 2:
        issues.append(
            _issue(
                rule_id="support_panels_invalid",
                message="grouped-local support-domain composite requires exactly two support_panels metrics",
                target="metrics.support_panels",
                observed={"support_panels": len(support_panels) if isinstance(support_panels, list) else None},
                expected={"support_panels": 2},
            )
        )
        return issues

    show_figure_title = _layout_override_flag(sidecar, "show_figure_title", False)
    local_layout_box_ids: set[str] = {"title"} if show_figure_title else set()
    local_panel_box_ids: set[str] = set()
    local_guide_box_ids: set[str] = set()
    local_panel_labels: list[str] = []
    for panel_index, panel in enumerate(local_panels):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.local_panels[{panel_index}] must be an object")
        panel_label = _require_non_empty_text(
            panel.get("panel_label"),
            label=f"layout_sidecar.metrics.local_panels[{panel_index}].panel_label",
        )
        local_panel_labels.append(panel_label)
        panel_token = _panel_label_token(panel_label)
        local_panel_box_ids.add(str(panel.get("panel_box_id") or "").strip() or f"panel_{panel_token}")
        local_guide_box_ids.add(str(panel.get("zero_line_box_id") or "").strip() or f"zero_line_{panel_token}")
        local_layout_box_ids.update(
            {
                f"panel_title_{panel_token}",
                f"panel_label_{panel_token}",
                f"group_label_{panel_token}",
                f"baseline_label_{panel_token}",
                f"prediction_label_{panel_token}",
                f"x_axis_title_{panel_token}",
            }
        )
        contributions = panel.get("contributions")
        if not isinstance(contributions, list):
            continue
        for contribution_index, contribution in enumerate(contributions):
            if not isinstance(contribution, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.local_panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            for field_name in ("bar_box_id", "feature_label_box_id", "value_label_box_id"):
                box_id = str(contribution.get(field_name) or "").strip()
                if box_id:
                    local_layout_box_ids.add(box_id)

    support_layout_box_ids: set[str] = {"title"} if show_figure_title else set()
    support_layout_box_ids.update(
        {
            str(metrics.get("support_y_axis_title_box_id") or "").strip() or "support_y_axis_title",
            str(metrics.get("support_legend_title_box_id") or "").strip() or "support_legend_title",
            "support_legend_box",
        }
    )
    support_panel_box_ids: set[str] = set()
    support_guide_box_ids: set[str] = set()
    support_panel_labels: list[str] = []
    support_features: list[str] = []
    for panel_index, panel in enumerate(support_panels):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.support_panels[{panel_index}] must be an object")
        panel_label = _require_non_empty_text(
            panel.get("panel_label"),
            label=f"layout_sidecar.metrics.support_panels[{panel_index}].panel_label",
        )
        support_panel_labels.append(panel_label)
        support_features.append(
            _require_non_empty_text(
                panel.get("feature"),
                label=f"layout_sidecar.metrics.support_panels[{panel_index}].feature",
            )
        )
        panel_token = _panel_label_token(panel_label)
        support_panel_box_ids.add(str(panel.get("panel_box_id") or "").strip() or f"panel_{panel_token}")
        support_guide_box_ids.add(
            str(panel.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_token}"
        )
        support_layout_box_ids.update(
            {
                f"panel_title_{panel_token}",
                f"panel_label_{panel_token}",
                f"x_axis_title_{panel_token}",
                str(panel.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_token}",
            }
        )
        segments = panel.get("support_segments")
        if not isinstance(segments, list):
            continue
        for segment_index, segment in enumerate(segments):
            if not isinstance(segment, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.support_panels[{panel_index}].support_segments[{segment_index}] must be an object"
                )
            segment_box_id = str(segment.get("segment_box_id") or "").strip()
            label_box_id = str(segment.get("label_box_id") or "").strip()
            if segment_box_id:
                support_guide_box_ids.add(segment_box_id)
            if label_box_id:
                support_layout_box_ids.add(label_box_id)

    local_sidecar = _subset_layout_sidecar(
        sidecar,
        layout_box_ids=local_layout_box_ids,
        panel_box_ids=local_panel_box_ids,
        guide_box_ids=local_guide_box_ids,
        metrics={"panels": list(local_panels)},
    )
    support_sidecar = _subset_layout_sidecar(
        sidecar,
        layout_box_ids=support_layout_box_ids,
        panel_box_ids=support_panel_box_ids,
        guide_box_ids=support_guide_box_ids,
        metrics={
            "legend_labels": metrics.get("support_legend_labels"),
            "panels": list(support_panels),
        },
    )
    issues.extend(_check_publication_shap_grouped_local_explanation_panel(local_sidecar))
    issues.extend(_check_publication_feature_response_support_domain_panel(support_sidecar))

    local_feature_order_payload = metrics.get("local_shared_feature_order")
    if not isinstance(local_feature_order_payload, list) or not local_feature_order_payload:
        issues.append(
            _issue(
                rule_id="local_feature_order_missing",
                message="grouped-local support-domain composite requires a non-empty local_shared_feature_order",
                target="metrics.local_shared_feature_order",
            )
        )
        local_feature_order: list[str] = []
    else:
        local_feature_order = [str(item or "").strip() for item in local_feature_order_payload]
        if any(not item for item in local_feature_order):
            issues.append(
                _issue(
                    rule_id="local_feature_order_invalid",
                    message="grouped-local support-domain local_shared_feature_order entries must be non-empty",
                    target="metrics.local_shared_feature_order",
                )
            )

    if len(set(local_panel_labels + support_panel_labels)) != len(local_panel_labels) + len(support_panel_labels):
        issues.append(
            _issue(
                rule_id="panel_label_collision",
                message="grouped-local support-domain composite panel labels must stay unique across local and support panels",
                target="metrics",
                observed={"local_panel_labels": local_panel_labels, "support_panel_labels": support_panel_labels},
            )
        )

    if local_feature_order:
        if not set(support_features).issubset(set(local_feature_order)):
            issues.append(
                _issue(
                    rule_id="support_feature_outside_local_order",
                    message="support-domain features must stay within the shared grouped-local feature order",
                    target="metrics.support_panels",
                    observed={"support_features": support_features},
                    expected={"local_shared_feature_order": local_feature_order},
                )
            )
        expected_support_order = [feature for feature in local_feature_order if feature in set(support_features)]
        if support_features != expected_support_order:
            issues.append(
                _issue(
                    rule_id="support_feature_order_mismatch",
                    message="support-domain feature order must follow the shared grouped-local feature order",
                    target="metrics.support_panels",
                    observed={"support_features": support_features},
                    expected={"support_features": expected_support_order},
                )
            )

    support_legend_title = str(metrics.get("support_legend_title") or "").strip()
    if not support_legend_title:
        issues.append(
            _issue(
                rule_id="support_legend_title_invalid",
                message="grouped-local support-domain composite requires a non-empty support legend title",
                target="metrics.support_legend_title",
            )
        )
    legend_title_box_id = str(metrics.get("support_legend_title_box_id") or "").strip() or "support_legend_title"
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    if legend_title_box_id not in layout_box_by_id:
        issues.append(
            _issue(
                rule_id="support_legend_title_missing",
                message="grouped-local support-domain composite requires an explicit support legend title box",
                target="metrics.support_legend_title_box_id",
                observed=legend_title_box_id,
            )
        )

    return issues


def _check_publication_shap_multigroup_decision_path_support_domain_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    decision_panel = metrics.get("decision_panel")
    support_panels = metrics.get("support_panels")
    if not isinstance(decision_panel, dict):
        issues.append(
            _issue(
                rule_id="decision_panel_missing",
                message="multigroup decision-path support-domain composite requires decision_panel metrics",
                target="metrics.decision_panel",
            )
        )
        return issues
    if not isinstance(support_panels, list) or len(support_panels) != 2:
        issues.append(
            _issue(
                rule_id="support_panels_invalid",
                message="multigroup decision-path support-domain composite requires exactly two support_panels metrics",
                target="metrics.support_panels",
                observed={"support_panels": len(support_panels) if isinstance(support_panels, list) else None},
                expected={"support_panels": 2},
            )
        )
        return issues

    show_figure_title = _layout_override_flag(sidecar, "show_figure_title", False)
    decision_layout_box_ids: set[str] = {"title"} if show_figure_title else set()
    decision_layout_box_ids.update({"panel_title", "x_axis_title", "y_axis_title", "legend_title", "legend_box"})
    feature_label_box_ids = decision_panel.get("feature_label_box_ids")
    if isinstance(feature_label_box_ids, list):
        decision_layout_box_ids.update(str(item or "").strip() for item in feature_label_box_ids if str(item or "").strip())

    decision_groups = decision_panel.get("groups")
    decision_panel_box_ids: set[str] = {
        str(decision_panel.get("panel_box_id") or "").strip() or "panel_decision_path"
    }
    decision_guide_box_ids: set[str] = {
        str(decision_panel.get("baseline_line_box_id") or "").strip() or "baseline_reference_line"
    }
    if isinstance(decision_groups, list):
        for group_index, group in enumerate(decision_groups):
            if not isinstance(group, dict):
                raise ValueError(f"layout_sidecar.metrics.decision_panel.groups[{group_index}] must be an object")
            line_box_id = str(group.get("line_box_id") or "").strip()
            prediction_marker_box_id = str(group.get("prediction_marker_box_id") or "").strip()
            prediction_label_box_id = str(group.get("prediction_label_box_id") or "").strip()
            if line_box_id:
                decision_layout_box_ids.add(line_box_id)
            if prediction_label_box_id:
                decision_layout_box_ids.add(prediction_label_box_id)
            if prediction_marker_box_id:
                decision_guide_box_ids.add(prediction_marker_box_id)

    support_layout_box_ids: set[str] = {"title"} if show_figure_title else set()
    support_layout_box_ids.update(
        {
            str(metrics.get("support_y_axis_title_box_id") or "").strip() or "support_y_axis_title",
            str(metrics.get("support_legend_title_box_id") or "").strip() or "support_legend_title",
            "support_legend_box",
        }
    )
    support_panel_box_ids: set[str] = set()
    support_guide_box_ids: set[str] = set()
    support_panel_labels: list[str] = []
    support_features: list[str] = []
    for panel_index, panel in enumerate(support_panels):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.support_panels[{panel_index}] must be an object")
        panel_label = _require_non_empty_text(
            panel.get("panel_label"),
            label=f"layout_sidecar.metrics.support_panels[{panel_index}].panel_label",
        )
        support_panel_labels.append(panel_label)
        support_features.append(
            _require_non_empty_text(
                panel.get("feature"),
                label=f"layout_sidecar.metrics.support_panels[{panel_index}].feature",
            )
        )
        panel_token = _panel_label_token(panel_label)
        support_panel_box_ids.add(str(panel.get("panel_box_id") or "").strip() or f"panel_{panel_token}")
        support_guide_box_ids.add(
            str(panel.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_token}"
        )
        support_layout_box_ids.update(
            {
                f"panel_title_{panel_token}",
                f"panel_label_{panel_token}",
                f"x_axis_title_{panel_token}",
                str(panel.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_token}",
            }
        )
        segments = panel.get("support_segments")
        if not isinstance(segments, list):
            continue
        for segment_index, segment in enumerate(segments):
            if not isinstance(segment, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.support_panels[{panel_index}].support_segments[{segment_index}] must be an object"
                )
            segment_box_id = str(segment.get("segment_box_id") or "").strip()
            label_box_id = str(segment.get("label_box_id") or "").strip()
            if segment_box_id:
                support_guide_box_ids.add(segment_box_id)
            if label_box_id:
                support_layout_box_ids.add(label_box_id)

    decision_sidecar = _subset_layout_sidecar(
        sidecar,
        layout_box_ids=decision_layout_box_ids,
        panel_box_ids=decision_panel_box_ids,
        guide_box_ids=decision_guide_box_ids,
        metrics=dict(decision_panel),
    )
    support_sidecar = _subset_layout_sidecar(
        sidecar,
        layout_box_ids=support_layout_box_ids,
        panel_box_ids=support_panel_box_ids,
        guide_box_ids=support_guide_box_ids,
        metrics={
            "legend_labels": metrics.get("support_legend_labels"),
            "panels": list(support_panels),
        },
    )
    issues.extend(_check_publication_shap_multigroup_decision_path_panel(decision_sidecar))
    issues.extend(_check_publication_feature_response_support_domain_panel(support_sidecar))

    feature_order_payload = decision_panel.get("feature_order")
    if not isinstance(feature_order_payload, list) or not feature_order_payload:
        issues.append(
            _issue(
                rule_id="decision_feature_order_missing",
                message="multigroup decision-path support-domain composite requires a non-empty decision feature order",
                target="metrics.decision_panel.feature_order",
            )
        )
        feature_order: list[str] = []
    else:
        feature_order = [str(item or "").strip() for item in feature_order_payload]
        if any(not item for item in feature_order):
            issues.append(
                _issue(
                    rule_id="decision_feature_order_invalid",
                    message="multigroup decision-path support-domain feature order entries must be non-empty",
                    target="metrics.decision_panel.feature_order",
                )
            )

    if len(set(support_panel_labels)) != len(support_panel_labels):
        issues.append(
            _issue(
                rule_id="panel_label_collision",
                message="multigroup decision-path support-domain support panel labels must stay unique",
                target="metrics.support_panels",
                observed={"support_panel_labels": support_panel_labels},
            )
        )

    if feature_order:
        if not set(support_features).issubset(set(feature_order)):
            issues.append(
                _issue(
                    rule_id="support_feature_outside_decision_order",
                    message="support-domain features must stay within the shared decision-path feature order",
                    target="metrics.support_panels",
                    observed={"support_features": support_features},
                    expected={"feature_order": feature_order},
                )
            )
        expected_support_order = [feature for feature in feature_order if feature in set(support_features)]
        if support_features != expected_support_order:
            issues.append(
                _issue(
                    rule_id="support_feature_order_mismatch",
                    message="support-domain feature order must follow the shared decision-path feature order",
                    target="metrics.support_panels",
                    observed={"support_features": support_features},
                    expected={"support_features": expected_support_order},
                )
            )

    support_legend_title = str(metrics.get("support_legend_title") or "").strip()
    if not support_legend_title:
        issues.append(
            _issue(
                rule_id="support_legend_title_invalid",
                message="multigroup decision-path support-domain composite requires a non-empty support legend title",
                target="metrics.support_legend_title",
            )
        )
    legend_title_box_id = str(metrics.get("support_legend_title_box_id") or "").strip() or "support_legend_title"
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    if legend_title_box_id not in layout_box_by_id:
        issues.append(
            _issue(
                rule_id="support_legend_title_missing",
                message="multigroup decision-path support-domain composite requires an explicit support legend title box",
                target="metrics.support_legend_title_box_id",
                observed=legend_title_box_id,
            )
        )

    return issues


def _check_publication_generalizability_subgroup_composite_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "panel_label",
        "overview_row_label",
        "support_label",
        "overview_metric_marker",
        "subgroup_row_label",
        "estimate_marker",
        "ci_segment",
    ]
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    comparator_label = str(metrics.get("comparator_label") or "").strip()
    if comparator_label:
        required_box_types.append("overview_comparator_marker")
        required_box_types.append("legend")
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    overview_panel = panel_boxes_by_id.get("overview_panel")
    subgroup_panel = panel_boxes_by_id.get("subgroup_panel")
    if overview_panel is None or subgroup_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="generalizability subgroup composite qc requires overview_panel and subgroup_panel",
                target="panel_boxes",
            )
        )
        return issues

    text_boxes = tuple(
        box for box in sidecar.layout_boxes if box.box_type in {"title", "panel_title", "panel_label", "subplot_x_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    legend_box = _first_box_of_type(sidecar.guide_boxes, "legend")

    if comparator_label:
        legend_title = str(metrics.get("legend_title") or "").strip()
        legend_labels = metrics.get("legend_labels")
        if not legend_title:
            issues.append(
                _issue(
                    rule_id="legend_title_invalid",
                    message="composite panel legend_title must be non-empty when comparator_label is declared",
                    target="metrics.legend_title",
                )
            )
        if not isinstance(legend_labels, list) or len([str(item).strip() for item in legend_labels if str(item).strip()]) < 2:
            issues.append(
                _issue(
                    rule_id="legend_labels_missing",
                    message="composite panel legend_labels must contain at least two non-empty labels when comparator_label is declared",
                    target="metrics.legend_labels",
                )
            )
        if legend_box is None:
            issues.append(
                _issue(
                    rule_id="legend_missing",
                    message="composite panel requires a legend when comparator_label is declared",
                    target="guide_boxes.legend",
                )
            )

    overview_rows = metrics.get("overview_rows")
    if not isinstance(overview_rows, list) or not overview_rows:
        issues.append(
            _issue(
                rule_id="overview_rows_missing",
                message="composite qc requires non-empty overview_rows metrics",
                target="metrics.overview_rows",
            )
        )
        return issues
    subgroup_rows = metrics.get("subgroup_rows")
    if not isinstance(subgroup_rows, list) or not subgroup_rows:
        issues.append(
            _issue(
                rule_id="subgroup_rows_missing",
                message="composite qc requires non-empty subgroup_rows metrics",
                target="metrics.subgroup_rows",
            )
        )
        return issues

    for row_index, row in enumerate(overview_rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.overview_rows[{row_index}] must be an object")
        label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
        support_label_box = layout_box_by_id.get(str(row.get("support_label_box_id") or "").strip())
        metric_marker_box = layout_box_by_id.get(str(row.get("metric_marker_box_id") or "").strip())
        comparator_marker_box = layout_box_by_id.get(str(row.get("comparator_marker_box_id") or "").strip())
        if label_box is None or support_label_box is None or metric_marker_box is None:
            issues.append(
                _issue(
                    rule_id="overview_row_box_missing",
                    message="overview rows must reference label, support, and metric marker boxes",
                    target=f"metrics.overview_rows[{row_index}]",
                    box_refs=(overview_panel.box_id,),
                )
            )
            continue
        if _boxes_overlap(label_box, overview_panel):
            issues.append(
                _issue(
                    rule_id="overview_row_label_panel_overlap",
                    message="overview row label must stay outside the overview panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, overview_panel.box_id),
                )
            )
        if not _box_within_box(support_label_box, overview_panel):
            issues.append(
                _issue(
                    rule_id="support_label_outside_panel",
                    message="overview support label must stay within the overview panel",
                    target=f"layout_boxes.{support_label_box.box_id}",
                    box_refs=(support_label_box.box_id, overview_panel.box_id),
                )
            )
        if not _box_within_box(metric_marker_box, overview_panel):
            issues.append(
                _issue(
                    rule_id="overview_metric_marker_outside_panel",
                    message="overview metric marker must stay within the overview panel",
                    target=f"layout_boxes.{metric_marker_box.box_id}",
                    box_refs=(metric_marker_box.box_id, overview_panel.box_id),
                )
            )
        if comparator_label:
            if comparator_marker_box is None:
                issues.append(
                    _issue(
                        rule_id="overview_comparator_marker_missing",
                        message="overview comparator marker must exist when comparator_label is declared",
                        target=f"metrics.overview_rows[{row_index}]",
                        box_refs=(overview_panel.box_id,),
                    )
                )
            elif not _box_within_box(comparator_marker_box, overview_panel):
                issues.append(
                    _issue(
                        rule_id="overview_comparator_marker_outside_panel",
                        message="overview comparator marker must stay within the overview panel",
                        target=f"layout_boxes.{comparator_marker_box.box_id}",
                        box_refs=(comparator_marker_box.box_id, overview_panel.box_id),
                    )
                )

    for row_index, row in enumerate(subgroup_rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.subgroup_rows[{row_index}] must be an object")
        lower = _require_numeric(row.get("lower"), label=f"layout_sidecar.metrics.subgroup_rows[{row_index}].lower")
        estimate = _require_numeric(
            row.get("estimate"), label=f"layout_sidecar.metrics.subgroup_rows[{row_index}].estimate"
        )
        upper = _require_numeric(row.get("upper"), label=f"layout_sidecar.metrics.subgroup_rows[{row_index}].upper")
        if not (lower <= estimate <= upper):
            issues.append(
                _issue(
                    rule_id="estimate_outside_interval",
                    message="subgroup estimate must lie within the confidence interval",
                    target=f"metrics.subgroup_rows[{row_index}]",
                    observed={"lower": lower, "estimate": estimate, "upper": upper},
                )
            )
        label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
        estimate_box = layout_box_by_id.get(str(row.get("estimate_box_id") or "").strip())
        ci_box = layout_box_by_id.get(str(row.get("ci_box_id") or "").strip())
        if label_box is None or estimate_box is None or ci_box is None:
            issues.append(
                _issue(
                    rule_id="subgroup_row_box_missing",
                    message="subgroup rows must reference label, estimate, and confidence-interval boxes",
                    target=f"metrics.subgroup_rows[{row_index}]",
                    box_refs=(subgroup_panel.box_id,),
                )
            )
            continue
        if _boxes_overlap(label_box, subgroup_panel):
            issues.append(
                _issue(
                    rule_id="subgroup_row_label_panel_overlap",
                    message="subgroup row label must stay outside the subgroup panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, subgroup_panel.box_id),
                )
            )
        if not _box_within_box(estimate_box, subgroup_panel):
            issues.append(
                _issue(
                    rule_id="estimate_marker_outside_panel",
                    message="subgroup estimate marker must stay within the subgroup panel",
                    target=f"layout_boxes.{estimate_box.box_id}",
                    box_refs=(estimate_box.box_id, subgroup_panel.box_id),
                )
            )
        if not _box_within_box(ci_box, subgroup_panel):
            issues.append(
                _issue(
                    rule_id="ci_segment_outside_panel",
                    message="subgroup confidence interval must stay within the subgroup panel",
                    target=f"layout_boxes.{ci_box.box_id}",
                    box_refs=(ci_box.box_id, subgroup_panel.box_id),
                )
            )
    return issues


def run_display_layout_qc(*, qc_profile: str, layout_sidecar: dict[str, object]) -> dict[str, object]:
    normalized_sidecar = _normalize_layout_sidecar(layout_sidecar)
    normalized_profile = str(qc_profile or "").strip()
    if normalized_profile == "publication_illustration_flow":
        layout_issues = _check_publication_illustration_flow(normalized_sidecar)
    elif normalized_profile == "publication_risk_layering_bars":
        layout_issues = _check_publication_risk_layering_bars(normalized_sidecar)
    elif normalized_profile == "publication_evidence_curve":
        layout_issues = _check_publication_evidence_curve(normalized_sidecar)
    elif normalized_profile == "publication_binary_calibration_decision_curve":
        layout_issues = _check_publication_binary_calibration_decision_curve(normalized_sidecar)
    elif normalized_profile == "publication_decision_curve":
        layout_issues = _check_publication_decision_curve(normalized_sidecar)
    elif normalized_profile == "publication_survival_curve":
        layout_issues = _check_publication_survival_curve(normalized_sidecar)
    elif normalized_profile == "publication_embedding_scatter":
        layout_issues = _check_publication_embedding_scatter(normalized_sidecar)
    elif normalized_profile == "publication_celltype_signature_panel":
        layout_issues = _check_publication_celltype_signature_panel(normalized_sidecar)
    elif normalized_profile == "publication_single_cell_atlas_overview_panel":
        layout_issues = _check_publication_single_cell_atlas_overview_panel(normalized_sidecar)
    elif normalized_profile == "publication_atlas_spatial_bridge_panel":
        layout_issues = _check_publication_atlas_spatial_bridge_panel(normalized_sidecar)
    elif normalized_profile == "publication_spatial_niche_map_panel":
        layout_issues = _check_publication_spatial_niche_map_panel(normalized_sidecar)
    elif normalized_profile == "publication_trajectory_progression_panel":
        layout_issues = _check_publication_trajectory_progression_panel(normalized_sidecar)
    elif normalized_profile == "publication_atlas_spatial_trajectory_storyboard_panel":
        layout_issues = _check_publication_atlas_spatial_trajectory_storyboard_panel(normalized_sidecar)
    elif normalized_profile == "publication_atlas_spatial_trajectory_density_coverage_panel":
        layout_issues = _check_publication_atlas_spatial_trajectory_density_coverage_panel(normalized_sidecar)
    elif normalized_profile == "publication_atlas_spatial_trajectory_context_support_panel":
        layout_issues = _check_publication_atlas_spatial_trajectory_context_support_panel(normalized_sidecar)
    elif normalized_profile == "publication_heatmap":
        layout_issues = _check_publication_heatmap(normalized_sidecar)
    elif normalized_profile == "publication_pathway_enrichment_dotplot_panel":
        layout_issues = _check_publication_pathway_enrichment_dotplot_panel(normalized_sidecar)
    elif normalized_profile == "publication_oncoplot_mutation_landscape_panel":
        layout_issues = _check_publication_oncoplot_mutation_landscape_panel(normalized_sidecar)
    elif normalized_profile == "publication_cnv_recurrence_summary_panel":
        layout_issues = _check_publication_cnv_recurrence_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_alteration_landscape_panel":
        layout_issues = _check_publication_genomic_alteration_landscape_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_alteration_consequence_panel":
        layout_issues = _check_publication_genomic_alteration_consequence_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_alteration_multiomic_consequence_panel":
        layout_issues = _check_publication_genomic_alteration_multiomic_consequence_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_alteration_pathway_integrated_composite_panel":
        layout_issues = _check_publication_genomic_alteration_pathway_integrated_composite_panel(normalized_sidecar)
    elif normalized_profile == "publication_genomic_program_governance_summary_panel":
        layout_issues = _check_publication_genomic_program_governance_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_omics_volcano_panel":
        layout_issues = _check_publication_omics_volcano_panel(normalized_sidecar)
    elif normalized_profile == "publication_forest_plot":
        layout_issues = _check_publication_forest_plot(normalized_sidecar)
    elif normalized_profile == "publication_compact_effect_estimate_panel":
        layout_issues = _check_publication_compact_effect_estimate_panel(normalized_sidecar)
    elif normalized_profile == "publication_coefficient_path_panel":
        layout_issues = _check_publication_coefficient_path_panel(normalized_sidecar)
    elif normalized_profile == "publication_broader_heterogeneity_summary_panel":
        layout_issues = _check_publication_broader_heterogeneity_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_interaction_effect_summary_panel":
        layout_issues = _check_publication_interaction_effect_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_center_transportability_governance_summary_panel":
        layout_issues = _check_publication_center_transportability_governance_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_model_complexity_audit":
        layout_issues = _check_publication_model_complexity_audit(normalized_sidecar)
    elif normalized_profile == "publication_landmark_performance_panel":
        layout_issues = _check_publication_landmark_performance_panel(normalized_sidecar)
    elif normalized_profile == "publication_time_to_event_threshold_governance_panel":
        layout_issues = _check_publication_time_to_event_threshold_governance_panel(normalized_sidecar)
    elif normalized_profile == "publication_time_to_event_multihorizon_calibration_panel":
        layout_issues = _check_publication_time_to_event_multihorizon_calibration_panel(normalized_sidecar)
    elif normalized_profile == "publication_multicenter_overview":
        layout_issues = _check_publication_multicenter_overview(normalized_sidecar)
    elif normalized_profile == "publication_generalizability_subgroup_composite_panel":
        layout_issues = _check_publication_generalizability_subgroup_composite_panel(normalized_sidecar)
    elif normalized_profile == "submission_graphical_abstract":
        layout_issues = _check_submission_graphical_abstract(normalized_sidecar)
    elif normalized_profile == "publication_workflow_fact_sheet_panel":
        layout_issues = _check_publication_workflow_fact_sheet_panel(normalized_sidecar)
    elif normalized_profile == "publication_design_evidence_composite_shell":
        layout_issues = _check_publication_design_evidence_composite_shell(normalized_sidecar)
    elif normalized_profile == "publication_baseline_missingness_qc_panel":
        layout_issues = _check_publication_baseline_missingness_qc_panel(normalized_sidecar)
    elif normalized_profile == "publication_center_coverage_batch_transportability_panel":
        layout_issues = _check_publication_center_coverage_batch_transportability_panel(normalized_sidecar)
    elif normalized_profile == "publication_transportability_recalibration_governance_panel":
        layout_issues = _check_publication_transportability_recalibration_governance_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_summary":
        layout_issues = _check_publication_shap_summary(normalized_sidecar)
    elif normalized_profile == "publication_shap_bar_importance":
        layout_issues = _check_publication_shap_bar_importance(normalized_sidecar)
    elif normalized_profile == "publication_shap_signed_importance_panel":
        layout_issues = _check_publication_shap_signed_importance_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_multicohort_importance_panel":
        layout_issues = _check_publication_shap_multicohort_importance_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_dependence_panel":
        layout_issues = _check_publication_shap_dependence_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_waterfall_local_explanation_panel":
        layout_issues = _check_publication_shap_waterfall_local_explanation_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_force_like_summary_panel":
        layout_issues = _check_publication_shap_force_like_summary_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_grouped_local_explanation_panel":
        layout_issues = _check_publication_shap_grouped_local_explanation_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_grouped_decision_path_panel":
        layout_issues = _check_publication_shap_grouped_decision_path_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_multigroup_decision_path_panel":
        layout_issues = _check_publication_shap_multigroup_decision_path_panel(normalized_sidecar)
    elif normalized_profile == "publication_partial_dependence_ice_panel":
        layout_issues = _check_publication_partial_dependence_ice_panel(normalized_sidecar)
    elif normalized_profile == "publication_partial_dependence_interaction_contour_panel":
        layout_issues = _check_publication_partial_dependence_interaction_contour_panel(normalized_sidecar)
    elif normalized_profile == "publication_partial_dependence_interaction_slice_panel":
        layout_issues = _check_publication_partial_dependence_interaction_slice_panel(normalized_sidecar)
    elif normalized_profile == "publication_partial_dependence_subgroup_comparison_panel":
        layout_issues = _check_publication_partial_dependence_subgroup_comparison_panel(normalized_sidecar)
    elif normalized_profile == "publication_accumulated_local_effects_panel":
        layout_issues = _check_publication_accumulated_local_effects_panel(normalized_sidecar)
    elif normalized_profile == "publication_feature_response_support_domain_panel":
        layout_issues = _check_publication_feature_response_support_domain_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_grouped_local_support_domain_panel":
        layout_issues = _check_publication_shap_grouped_local_support_domain_panel(normalized_sidecar)
    elif normalized_profile == "publication_shap_multigroup_decision_path_support_domain_panel":
        layout_issues = _check_publication_shap_multigroup_decision_path_support_domain_panel(normalized_sidecar)
    else:
        raise ValueError(f"unsupported qc_profile `{qc_profile}`")
    readability_issues = display_readability_qc.run_readability_qc(
        qc_profile=normalized_profile,
        layout_sidecar=layout_sidecar,
    )
    issues = layout_issues + readability_issues
    audit_classes = sorted(
        {
            str(issue.get("audit_class") or "layout").strip()
            for issue in issues
            if str(issue.get("audit_class") or "layout").strip()
        }
    )
    readability_findings = [issue for issue in issues if str(issue.get("audit_class") or "").strip() == "readability"]
    failure_reason = str(issues[0].get("rule_id") or "").strip() if issues else ""

    return {
        "status": "fail" if issues else "pass",
        "checked_at": _utc_now(),
        "engine_id": ENGINE_ID,
        "qc_profile": normalized_profile,
        "issues": issues,
        "audit_classes": audit_classes,
        "failure_reason": failure_reason,
        "readability_findings": readability_findings,
        "revision_note": "",
        "metrics": normalized_sidecar.metrics,
    }
