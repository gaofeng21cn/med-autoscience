from __future__ import annotations

from .shared import Any, matplotlib, plt

def _bbox_to_layout_box(
    *,
    figure: plt.Figure,
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
    figure: plt.Figure,
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

def _data_point_to_figure_xy(*, axes, figure: plt.Figure, x: float, y: float) -> tuple[float, float]:
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
        if xmin <= x_value <= xmax and ymin <= y_value <= ymax:
            return {
                "x": [x_value],
                "y": [y_value],
                "label": str(reference_line.get("label") or "").strip(),
            }
        return None

    clipped_points: list[tuple[float, float]] = []
    for index in range(len(x_values) - 1):
        start_x = x_values[index]
        start_y = y_values[index]
        end_x = x_values[index + 1]
        end_y = y_values[index + 1]
        clipped_segment = _clip_line_segment_to_axes_window(
            x0=start_x,
            y0=start_y,
            x1=end_x,
            y1=end_y,
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
        )
        if clipped_segment is None:
            continue
        clipped_start = (clipped_segment[0], clipped_segment[1])
        clipped_end = (clipped_segment[2], clipped_segment[3])
        if not clipped_points or clipped_points[-1] != clipped_start:
            clipped_points.append(clipped_start)
        if clipped_points[-1] != clipped_end:
            clipped_points.append(clipped_end)
    if not clipped_points:
        return None
    return {
        "x": [point[0] for point in clipped_points],
        "y": [point[1] for point in clipped_points],
        "label": str(reference_line.get("label") or "").strip(),
    }

def _normalize_reference_line_to_device_space(
    *,
    reference_line: dict[str, Any] | None,
    axes,
    figure: plt.Figure,
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
    figure: plt.Figure,
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

def _build_python_shap_layout_sidecar(
    *,
    figure: plt.Figure,
    axes,
    colorbar,
    rows: list[dict[str, Any]],
    point_rows: list[dict[str, Any]],
    template_id: str,
) -> dict[str, Any]:
    renderer = figure.canvas.get_renderer()
    layout_boxes = []
    if str(axes.title.get_text() or "").strip():
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=figure,
                bbox=axes.title.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=figure,
            bbox=axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        )
    )
    panel_box = _bbox_to_layout_box(
        figure=figure,
        bbox=axes.get_window_extent(renderer=renderer),
        box_id="panel",
        box_type="panel",
    )
    x_min, x_max = axes.get_xlim()
    for row_index, row in enumerate(rows):
        row_box = _data_box_to_layout_box(
            axes=axes,
            figure=figure,
            x0=x_min,
            y0=row_index - 0.42,
            x1=x_max,
            y1=row_index + 0.42,
            box_id=f"feature_row_{row['feature']}",
            box_type="feature_row",
        )
        row_box["y0"] = max(float(row_box["y0"]), float(panel_box["y0"]))
        row_box["y1"] = min(float(row_box["y1"]), float(panel_box["y1"]))
        layout_boxes.append(row_box)
    zero_line_x, _ = _data_point_to_figure_xy(
        axes=axes,
        figure=figure,
        x=0.0,
        y=0.0,
    )
    guide_boxes = [
        _bbox_to_layout_box(
            figure=figure,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        ),
        {
            "box_id": "zero_line",
            "box_type": "zero_line",
            "x0": zero_line_x,
            "y0": float(panel_box["y0"]),
            "x1": zero_line_x,
            "y1": float(panel_box["y1"]),
        },
    ]
    row_box_id_by_feature = {f"{row['feature']}": f"feature_row_{row['feature']}" for row in rows}
    feature_label_metrics: list[dict[str, Any]] = []
    for row, label_artist in zip(rows, axes.get_yticklabels()):
        label_box_id = f"feature_label_{row['feature']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=figure,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=label_box_id,
                box_type="feature_label",
            )
        )
        feature_label_metrics.append(
            {
                "feature": str(row["feature"]),
                "row_box_id": row_box_id_by_feature[str(row["feature"])],
                "label_box_id": label_box_id,
            }
        )
    point_metrics: list[dict[str, Any]] = []
    for item in point_rows:
        figure_x, figure_y = _data_point_to_figure_xy(
            axes=axes,
            figure=figure,
            x=float(item["shap_value"]),
            y=float(item["row_position"]),
        )
        point_metrics.append(
            {
                "feature": str(item["feature"]),
                "row_box_id": row_box_id_by_feature[str(item["feature"])],
                "x": figure_x,
                "y": figure_y,
            }
        )
    return {
        "template_id": template_id,
        "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
        "layout_boxes": layout_boxes,
        "panel_boxes": [panel_box],
        "guide_boxes": guide_boxes,
        "metrics": {
            "figure_height_inches": float(figure.get_figheight()),
            "figure_width_inches": float(figure.get_figwidth()),
            "feature_labels": feature_label_metrics,
            "points": point_metrics,
        },
    }


__all__ = [
    "_bbox_to_layout_box",
    "_data_box_to_layout_box",
    "_data_point_to_figure_xy",
    "_clip_line_segment_to_axes_window",
    "_clip_reference_line_to_axes_window",
    "_normalize_reference_line_to_device_space",
    "_normalize_reference_line_collection_to_device_space",
    "_build_python_shap_layout_sidecar",
]
