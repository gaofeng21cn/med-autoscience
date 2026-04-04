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
    )


def _all_boxes(sidecar: LayoutSidecar) -> tuple[Box, ...]:
    return sidecar.layout_boxes + sidecar.panel_boxes + sidecar.guide_boxes


def _boxes_of_type(boxes: tuple[Box, ...], box_type: str) -> tuple[Box, ...]:
    return tuple(box for box in boxes if box.box_type == box_type)


def _first_box_of_type(boxes: tuple[Box, ...], box_type: str) -> Box | None:
    matches = _boxes_of_type(boxes, box_type)
    return matches[0] if matches else None


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
    panel = _primary_panel(sidecar)
    legend = _first_box_of_type(sidecar.guide_boxes, "legend")
    if panel is None or legend is None:
        return []
    if not _boxes_overlap(legend, panel):
        return []
    return [
        _issue(
            rule_id="legend_panel_overlap",
            message="legend box must not overlap the main panel",
            target="legend",
            box_refs=(legend.box_id, panel.box_id),
        )
    ]


def _check_colorbar_panel_overlap(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    panel = _primary_panel(sidecar)
    colorbar = _first_box_of_type(sidecar.guide_boxes, "colorbar")
    if panel is None or colorbar is None:
        return []
    if not _boxes_overlap(colorbar, panel):
        return []
    return [
        _issue(
            rule_id="colorbar_panel_overlap",
            message="colorbar must not overlap the main panel",
            target="colorbar",
            box_refs=(colorbar.box_id, panel.box_id),
        )
    ]


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
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("title", "x_axis_title", "y_axis_title")))
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
        if box.box_type in {"title", "x_axis_title", "y_axis_title", "caption"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    return issues


def _check_publication_evidence_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_curve_like_layout(sidecar)
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_curve_metrics(sidecar.metrics))
    issues.extend(_check_reference_line_within_device(sidecar))
    return issues


def _check_publication_survival_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_curve_like_layout(sidecar)
    issues.extend(_check_legend_panel_overlap(sidecar))

    annotation = _first_box_of_type(sidecar.guide_boxes + sidecar.layout_boxes, "annotation_block")
    panel = _primary_panel(sidecar)
    legend = _first_box_of_type(sidecar.guide_boxes, "legend")
    if annotation is not None and panel is not None and _boxes_overlap(annotation, panel):
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


def _check_publication_multicenter_overview(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=("title", "x_axis_title", "row_label", "sample_bar", "estimate_marker", "ci_segment"),
        )
    )

    sample_panel = _first_box_of_type(sidecar.panel_boxes, "sample_panel")
    estimate_panel = _first_box_of_type(sidecar.panel_boxes, "estimate_panel")
    if sample_panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="multicenter overview requires a sample-size panel",
                target="sample_panel",
                expected="present",
            )
        )
    if estimate_panel is None:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="multicenter overview requires an estimate panel",
                target="estimate_panel",
                expected="present",
            )
        )

    for row_label in _boxes_of_type(sidecar.layout_boxes, "row_label"):
        if sample_panel is not None and _boxes_overlap(row_label, sample_panel):
            issues.append(
                _issue(
                    rule_id="row_label_panel_overlap",
                    message="row label must not overlap the sample-size panel",
                    target="row_label",
                    box_refs=(row_label.box_id, sample_panel.box_id),
                )
            )
        if estimate_panel is not None and _boxes_overlap(row_label, estimate_panel):
            issues.append(
                _issue(
                    rule_id="row_label_panel_overlap",
                    message="row label must not overlap the estimate panel",
                    target="row_label",
                    box_refs=(row_label.box_id, estimate_panel.box_id),
                )
            )
    if sample_panel is not None:
        for sample_bar in _boxes_of_type(sidecar.layout_boxes, "sample_bar"):
            if _box_within_box(sample_bar, sample_panel):
                continue
            issues.append(
                _issue(
                    rule_id="sample_bar_outside_panel",
                    message="sample-size bar must stay within the sample-size panel",
                    target="sample_bar",
                    box_refs=(sample_bar.box_id, sample_panel.box_id),
                )
            )
        reference_line = _first_box_of_type(sidecar.guide_boxes, "reference_line")
        if reference_line is not None and estimate_panel is not None and not _box_within_box(reference_line, estimate_panel):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="reference line must stay within the estimate panel",
                    target="reference_line",
                    box_refs=(reference_line.box_id, estimate_panel.box_id),
                )
            )
    if estimate_panel is not None:
        for estimate_marker in _boxes_of_type(sidecar.layout_boxes, "estimate_marker"):
            if _box_within_box(estimate_marker, estimate_panel):
                continue
            issues.append(
                _issue(
                    rule_id="estimate_marker_outside_panel",
                    message="estimate marker must stay within the estimate panel",
                    target="estimate_marker",
                    box_refs=(estimate_marker.box_id, estimate_panel.box_id),
                )
            )
        for ci_segment in _boxes_of_type(sidecar.layout_boxes, "ci_segment"):
            if _box_within_box(ci_segment, estimate_panel):
                continue
            issues.append(
                _issue(
                    rule_id="ci_segment_outside_panel",
                    message="confidence-interval segment must stay within the estimate panel",
                    target="ci_segment",
                    box_refs=(ci_segment.box_id, estimate_panel.box_id),
                )
            )

    centers = sidecar.metrics.get("centers")
    if not isinstance(centers, list) or not centers:
        issues.append(
            _issue(
                rule_id="centers_missing",
                message="multicenter overview requires non-empty center metrics",
                target="metrics.centers",
            )
        )
        return issues
    for index, center in enumerate(centers):
        if not isinstance(center, dict):
            raise ValueError(f"layout_sidecar.metrics.centers[{index}] must be an object")
        sample_size = _require_numeric(center.get("sample_size"), label=f"layout_sidecar.metrics.centers[{index}].sample_size")
        lower = _require_numeric(center.get("lower"), label=f"layout_sidecar.metrics.centers[{index}].lower")
        estimate = _require_numeric(center.get("estimate"), label=f"layout_sidecar.metrics.centers[{index}].estimate")
        upper = _require_numeric(center.get("upper"), label=f"layout_sidecar.metrics.centers[{index}].upper")
        if sample_size <= 0:
            issues.append(
                _issue(
                    rule_id="sample_size_non_positive",
                    message="sample size must be positive",
                    target=f"metrics.centers[{index}]",
                    observed=sample_size,
                )
            )
        if lower <= estimate <= upper:
            continue
        issues.append(
            _issue(
                rule_id="estimate_outside_interval",
                message="estimate must lie within the confidence interval",
                target=f"metrics.centers[{index}]",
                observed={"lower": lower, "estimate": estimate, "upper": upper},
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


def run_display_layout_qc(*, qc_profile: str, layout_sidecar: dict[str, object]) -> dict[str, object]:
    normalized_sidecar = _normalize_layout_sidecar(layout_sidecar)
    normalized_profile = str(qc_profile or "").strip()
    if normalized_profile == "publication_evidence_curve":
        layout_issues = _check_publication_evidence_curve(normalized_sidecar)
    elif normalized_profile == "publication_decision_curve":
        layout_issues = _check_publication_evidence_curve(normalized_sidecar)
    elif normalized_profile == "publication_survival_curve":
        layout_issues = _check_publication_survival_curve(normalized_sidecar)
    elif normalized_profile == "publication_embedding_scatter":
        layout_issues = _check_publication_embedding_scatter(normalized_sidecar)
    elif normalized_profile == "publication_heatmap":
        layout_issues = _check_publication_heatmap(normalized_sidecar)
    elif normalized_profile == "publication_forest_plot":
        layout_issues = _check_publication_forest_plot(normalized_sidecar)
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
