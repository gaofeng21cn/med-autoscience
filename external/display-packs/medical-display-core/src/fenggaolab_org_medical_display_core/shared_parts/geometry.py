from __future__ import annotations

from typing import Any

import matplotlib


def _bbox_to_layout_box(
    *,
    figure,
    bbox,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    x0, y0 = figure.transFigure.inverted().transform((bbox.x0, bbox.y0))
    x1, y1 = figure.transFigure.inverted().transform((bbox.x1, bbox.y1))
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": float(min(x0, x1)),
        "y0": float(min(y0, y1)),
        "x1": float(max(x0, x1)),
        "y1": float(max(y0, y1)),
    }


def _data_box_to_layout_box(
    *,
    axes,
    figure,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    box_id: str,
    box_type: str,
) -> dict[str, Any]:
    left_bottom = axes.transData.transform((x0, y0))
    right_top = axes.transData.transform((x1, y1))
    bbox = matplotlib.transforms.Bbox.from_extents(left_bottom[0], left_bottom[1], right_top[0], right_top[1])
    return _bbox_to_layout_box(figure=figure, bbox=bbox, box_id=box_id, box_type=box_type)


def _data_point_to_figure_xy(*, axes, figure, x: float, y: float) -> tuple[float, float]:
    display_x, display_y = axes.transData.transform((x, y))
    figure_x, figure_y = figure.transFigure.inverted().transform((display_x, display_y))
    return float(figure_x), float(figure_y)


def _clip_line_segment_to_axes_window(
    *,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> tuple[float, float, float, float] | None:
    dx = x1 - x0
    dy = y1 - y0
    t0 = 0.0
    t1 = 1.0
    for p, q in (
        (-dx, x0 - xmin),
        (dx, xmax - x0),
        (-dy, y0 - ymin),
        (dy, ymax - y0),
    ):
        if p == 0.0:
            if q < 0.0:
                return None
            continue
        t = q / p
        if p < 0.0:
            if t > t1:
                return None
            if t > t0:
                t0 = t
        else:
            if t < t0:
                return None
            if t < t1:
                t1 = t
    return (
        x0 + t0 * dx,
        y0 + t0 * dy,
        x0 + t1 * dx,
        y0 + t1 * dy,
    )


def _reference_line_label(reference_line: dict[str, Any]) -> str:
    return str(reference_line.get("label") or "").strip()


def _single_reference_point_in_axes(
    *,
    x_value: float,
    y_value: float,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> bool:
    return xmin <= x_value <= xmax and ymin <= y_value <= ymax


def _append_clipped_reference_segment_points(
    *,
    clipped_points: list[tuple[float, float]],
    clipped_segment: tuple[float, float, float, float],
) -> None:
    clipped_start = (clipped_segment[0], clipped_segment[1])
    clipped_end = (clipped_segment[2], clipped_segment[3])
    if not clipped_points or clipped_points[-1] != clipped_start:
        clipped_points.append(clipped_start)
    if clipped_points[-1] != clipped_end:
        clipped_points.append(clipped_end)


def _clipped_reference_polyline_points(
    *,
    x_values: list[float],
    y_values: list[float],
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
) -> list[tuple[float, float]]:
    clipped_points: list[tuple[float, float]] = []
    for index in range(len(x_values) - 1):
        clipped_segment = _clip_line_segment_to_axes_window(
            x0=x_values[index],
            y0=y_values[index],
            x1=x_values[index + 1],
            y1=y_values[index + 1],
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
        )
        if clipped_segment is not None:
            _append_clipped_reference_segment_points(
                clipped_points=clipped_points,
                clipped_segment=clipped_segment,
            )
    return clipped_points


def _clip_reference_line_to_axes_window(
    *,
    reference_line: dict[str, Any] | None,
    axes,
) -> dict[str, Any] | None:
    if not isinstance(reference_line, dict):
        return None
    x_values = [float(value) for value in reference_line.get("x") or []]
    y_values = [float(value) for value in reference_line.get("y") or []]
    if len(x_values) != len(y_values):
        raise ValueError("reference_line.x and reference_line.y must have the same length")
    xmin, xmax = sorted(float(value) for value in axes.get_xlim())
    ymin, ymax = sorted(float(value) for value in axes.get_ylim())
    if len(x_values) == 1:
        x_value = x_values[0]
        y_value = y_values[0]
        if _single_reference_point_in_axes(
            x_value=x_value,
            y_value=y_value,
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
        ):
            return {
                "x": [x_value],
                "y": [y_value],
                "label": _reference_line_label(reference_line),
            }
        return None

    clipped_points = _clipped_reference_polyline_points(
        x_values=x_values,
        y_values=y_values,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
    )
    if not clipped_points:
        return None
    return {
        "x": [point[0] for point in clipped_points],
        "y": [point[1] for point in clipped_points],
        "label": _reference_line_label(reference_line),
    }


def _normalize_reference_line_to_device_space(
    *,
    reference_line: dict[str, Any] | None,
    axes,
    figure,
    clip_to_axes_window: bool = False,
) -> dict[str, Any] | None:
    if clip_to_axes_window:
        reference_line = _clip_reference_line_to_axes_window(reference_line=reference_line, axes=axes)
    if not isinstance(reference_line, dict):
        return None
    x_values = list(reference_line.get("x") or [])
    y_values = list(reference_line.get("y") or [])
    if len(x_values) != len(y_values):
        raise ValueError("reference_line.x and reference_line.y must have the same length")
    normalized_x: list[float] = []
    normalized_y: list[float] = []
    for x_value, y_value in zip(x_values, y_values, strict=True):
        figure_x, figure_y = _data_point_to_figure_xy(
            axes=axes,
            figure=figure,
            x=float(x_value),
            y=float(y_value),
        )
        normalized_x.append(figure_x)
        normalized_y.append(figure_y)
    return {
        "x": normalized_x,
        "y": normalized_y,
        "label": str(reference_line.get("label") or "").strip(),
    }


def _normalize_reference_line_collection_to_device_space(
    *,
    reference_lines: list[dict[str, Any]] | None,
    axes,
    figure,
) -> list[dict[str, Any]]:
    normalized_lines: list[dict[str, Any]] = []
    for item in reference_lines or []:
        normalized_line = _normalize_reference_line_to_device_space(
            reference_line=item,
            axes=axes,
            figure=figure,
        )
        if normalized_line is not None:
            normalized_lines.append(normalized_line)
    return normalized_lines
