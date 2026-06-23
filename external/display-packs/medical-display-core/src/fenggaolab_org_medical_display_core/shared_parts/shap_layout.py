from __future__ import annotations

from typing import Any

from .geometry import _bbox_to_layout_box, _data_box_to_layout_box, _data_point_to_figure_xy


def _build_python_shap_layout_sidecar(
    *,
    figure,
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
