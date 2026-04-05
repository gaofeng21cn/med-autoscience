from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
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
            "caption",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    return issues


def _check_publication_evidence_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_curve_like_layout(sidecar)
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_curve_metrics(sidecar.metrics))
    issues.extend(_check_reference_line_within_device(sidecar))
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


def _check_publication_multicenter_overview(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(_all_boxes(sidecar), required_box_types=("title", "y_axis_title", "coverage_bar")))
    issues.extend(_check_legend_panel_overlap(sidecar))

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
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("zero_line", "colorbar", "title", "x_axis_title", "feature_row")))

    row_boxes = _boxes_of_type(sidecar.layout_boxes + sidecar.panel_boxes, "feature_row")
    issues.extend(_check_pairwise_non_overlap(row_boxes, rule_id="feature_row_overlap", target="feature_row"))

    critical_boxes = tuple(
        box for box in all_boxes if box.box_type in {"title", "x_axis_title", "colorbar"}
    )
    issues.extend(_check_pairwise_non_overlap(critical_boxes, rule_id="critical_box_overlap", target="critical_boxes"))

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
    return issues


def _check_publication_illustration_flow(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("main_step",)))

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
    elif normalized_profile == "publication_heatmap":
        layout_issues = _check_publication_heatmap(normalized_sidecar)
    elif normalized_profile == "publication_forest_plot":
        layout_issues = _check_publication_forest_plot(normalized_sidecar)
    elif normalized_profile == "publication_model_complexity_audit":
        layout_issues = _check_publication_model_complexity_audit(normalized_sidecar)
    elif normalized_profile == "publication_multicenter_overview":
        layout_issues = _check_publication_multicenter_overview(normalized_sidecar)
    elif normalized_profile == "publication_shap_summary":
        layout_issues = _check_publication_shap_summary(normalized_sidecar)
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
