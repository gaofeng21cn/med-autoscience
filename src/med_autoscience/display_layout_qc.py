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
        if (
            label_box.x0 < parent_panel.x0
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
            allow_top_overhang_ratio=0.04,
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
            allow_top_overhang_ratio=0.04,
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
            alignment_tolerance = max((panel_box.x1 - panel_box.x0) * 0.08, 0.02)
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
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
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
    elif normalized_profile == "publication_spatial_niche_map_panel":
        layout_issues = _check_publication_spatial_niche_map_panel(normalized_sidecar)
    elif normalized_profile == "publication_trajectory_progression_panel":
        layout_issues = _check_publication_trajectory_progression_panel(normalized_sidecar)
    elif normalized_profile == "publication_heatmap":
        layout_issues = _check_publication_heatmap(normalized_sidecar)
    elif normalized_profile == "publication_forest_plot":
        layout_issues = _check_publication_forest_plot(normalized_sidecar)
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
    elif normalized_profile == "publication_partial_dependence_ice_panel":
        layout_issues = _check_publication_partial_dependence_ice_panel(normalized_sidecar)
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
