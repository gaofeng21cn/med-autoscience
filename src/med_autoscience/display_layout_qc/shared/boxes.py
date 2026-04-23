from __future__ import annotations

from .core import Box, Device, LayoutSidecar, _issue


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


def _check_boxes_within_device(sidecar: LayoutSidecar) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for box in _all_boxes(sidecar):
        if _box_within_device(box, sidecar.device):
            continue
        issues.append(
            _issue(
                rule_id="box_out_of_device",
                message=f"box `{box.box_id}` must lie within the device bounds",
                target=box.box_type,
                observed={"x0": box.x0, "y0": box.y0, "x1": box.x1, "y1": box.y1},
                expected={
                    "x0": sidecar.device.x0,
                    "y0": sidecar.device.y0,
                    "x1": sidecar.device.x1,
                    "y1": sidecar.device.y1,
                },
                box_refs=(box.box_id,),
            )
        )
    return issues


def _check_required_box_types(boxes: tuple[Box, ...], *, required_box_types: tuple[str, ...]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
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


def _check_pairwise_non_overlap(boxes: tuple[Box, ...], *, rule_id: str, target: str) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
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


def _check_legend_panel_overlap(sidecar: LayoutSidecar) -> list[dict[str, object]]:
    legend = _first_box_of_type(sidecar.guide_boxes, "legend")
    panels = sidecar.panel_boxes
    if not panels:
        primary_panel = _primary_panel(sidecar)
        panels = (primary_panel,) if primary_panel is not None else ()
    if not panels or legend is None:
        return []
    issues: list[dict[str, object]] = []
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


def _check_colorbar_panel_overlap(sidecar: LayoutSidecar) -> list[dict[str, object]]:
    colorbar = _first_box_of_type(sidecar.guide_boxes, "colorbar")
    panels = sidecar.panel_boxes
    if not panels:
        primary_panel = _primary_panel(sidecar)
        panels = (primary_panel,) if primary_panel is not None else ()
    if not panels or colorbar is None:
        return []
    issues: list[dict[str, object]] = []
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


def _check_curve_like_layout(sidecar: LayoutSidecar) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
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
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
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
    import re

    return re.sub(r"[^A-Za-z0-9]+", "_", str(panel_label)) or "panel"
