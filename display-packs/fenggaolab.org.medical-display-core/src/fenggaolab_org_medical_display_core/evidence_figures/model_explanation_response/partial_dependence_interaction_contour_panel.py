from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _data_box_to_layout_box,
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    dump_json,
)

def _render_python_partial_dependence_interaction_contour_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    if not panels:
        raise RuntimeError(f"{template_id} requires non-empty panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    support_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    contour_line_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    all_response_values = [
        float(value)
        for panel in panels
        for row in panel["response_grid"]
        for value in row
    ]
    vmin = min(all_response_values)
    vmax = max(all_response_values)
    if abs(vmax - vmin) < 1e-9:
        vmax = vmin + 1e-6

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        f"{template_id}_cmap",
        [
            str(palette.get("light") or "#eff6ff"),
            str(palette.get("secondary_soft") or "#cbd5e1"),
            str(palette.get("primary") or support_color),
        ],
    )

    figure_width = max(9.2, 4.5 * len(panels) + 1.9)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 5.2), squeeze=False)
    axes_list = list(axes[0])
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.88,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    panel_records: list[dict[str, Any]] = []
    contour_handle = None
    for axes_item, panel in zip(axes_list, panels, strict=True):
        x_grid = [float(value) for value in panel["x_grid"]]
        y_grid = [float(value) for value in panel["y_grid"]]
        response_grid = [[float(value) for value in row] for row in panel["response_grid"]]

        contour_handle = axes_item.contourf(
            x_grid,
            y_grid,
            response_grid,
            levels=12,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            antialiased=True,
            zorder=1,
        )
        axes_item.contour(
            x_grid,
            y_grid,
            response_grid,
            levels=6,
            colors=contour_line_color,
            linewidths=0.55,
            alpha=0.7,
            zorder=2,
        )

        support_x = [float(point["x"]) for point in panel["observed_points"]]
        support_y = [float(point["y"]) for point in panel["observed_points"]]
        axes_item.scatter(
            support_x,
            support_y,
            s=18.0,
            color=matplotlib.colors.to_rgba(support_color, alpha=0.32),
            edgecolors="white",
            linewidths=0.45,
            zorder=3,
        )

        axes_item.axvline(
            float(panel["reference_x_value"]),
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=4,
        )
        axes_item.axhline(
            float(panel["reference_y_value"]),
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=4,
        )
        axes_item.scatter(
            [float(panel["reference_x_value"])],
            [float(panel["reference_y_value"])],
            s=28.0,
            color=reference_color,
            edgecolors="white",
            linewidths=0.5,
            zorder=5,
        )

        x_span = max(x_grid[-1] - x_grid[0], 1e-6)
        y_span = max(y_grid[-1] - y_grid[0], 1e-6)
        reference_label_x = min(
            max(float(panel["reference_x_value"]) + x_span * 0.03, x_grid[0] + x_span * 0.08),
            x_grid[-1] - x_span * 0.08,
        )
        reference_label_y = min(
            max(float(panel["reference_y_value"]) + y_span * 0.05, y_grid[0] + y_span * 0.10),
            y_grid[-1] - y_span * 0.08,
        )
        reference_label_artist = axes_item.text(
            reference_label_x,
            reference_label_y,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="bottom",
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": (1.0, 1.0, 1.0, 0.72),
                "edgecolor": reference_color,
                "linewidth": 0.55,
            },
            zorder=6,
        )

        axes_item.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_ylabel(
            str(panel["y_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_title(
            str(panel["title"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#334155",
            pad=10.0,
        )
        axes_item.tick_params(axis="both", labelsize=tick_size, colors="#2F3437")
        axes_item.grid(axis="both", color="#e6edf2", linewidth=0.55, linestyle=":")
        _apply_publication_axes_style(axes_item)

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "reference_label_artist": reference_label_artist,
            }
        )

    top_margin = 0.80 if show_figure_title else 0.88
    top_margin = max(0.73, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.09, right=0.88, top=top_margin, bottom=0.18, wspace=0.28)

    colorbar = fig.colorbar(
        contour_handle,
        ax=axes_list,
        fraction=0.035,
        pad=0.04,
    )
    colorbar.set_label(
        str(display_payload.get("colorbar_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors="#2F3437")

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.6, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]))
        for record in panel_records
    ]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes: list[dict[str, Any]] = []
    if title_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            )
        )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        )
    ]
    normalized_panels: list[dict[str, Any]] = []

    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = str(panel["panel_label"])
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        reference_vertical_box_id = f"reference_vertical_{panel_token}"
        reference_horizontal_box_id = f"reference_horizontal_{panel_token}"
        reference_label_box_id = f"reference_label_{panel_token}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
                    box_id=f"panel_title_{panel_token}",
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.yaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"y_axis_title_{panel_token}",
                    box_type="subplot_y_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=reference_label_box_id,
                    box_type="interaction_reference_label",
                ),
            ]
        )

        x_span = max(float(panel["x_grid"][-1]) - float(panel["x_grid"][0]), 1e-6)
        y_span = max(float(panel["y_grid"][-1]) - float(panel["y_grid"][0]), 1e-6)
        vertical_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_x_value"]) - max(x_span * 0.003, 0.0015),
            y0=float(panel["y_grid"][0]),
            x1=float(panel["reference_x_value"]) + max(x_span * 0.003, 0.0015),
            y1=float(panel["y_grid"][-1]),
            box_id=reference_vertical_box_id,
            box_type="interaction_reference_vertical",
        )
        vertical_box["y0"] = max(float(panel_box["y0"]), float(vertical_box["y0"]))
        vertical_box["y1"] = min(float(panel_box["y1"]), float(vertical_box["y1"]))
        guide_boxes.append(vertical_box)

        horizontal_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["x_grid"][0]),
            y0=float(panel["reference_y_value"]) - max(y_span * 0.003, 0.0015),
            x1=float(panel["x_grid"][-1]),
            y1=float(panel["reference_y_value"]) + max(y_span * 0.003, 0.0015),
            box_id=reference_horizontal_box_id,
            box_type="interaction_reference_horizontal",
        )
        horizontal_box["x0"] = max(float(panel_box["x0"]), float(horizontal_box["x0"]))
        horizontal_box["x1"] = min(float(panel_box["x1"]), float(horizontal_box["x1"]))
        guide_boxes.append(horizontal_box)

        normalized_observed_points: list[dict[str, Any]] = []
        for point in panel["observed_points"]:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(point["x"]),
                y=float(point["y"]),
            )
            normalized_observed_points.append(
                {
                    "point_id": str(point["point_id"]),
                    "feature_x_value": float(point["x"]),
                    "feature_y_value": float(point["y"]),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "y_label": str(panel["y_label"]),
                "x_feature": str(panel["x_feature"]),
                "y_feature": str(panel["y_feature"]),
                "reference_x_value": float(panel["reference_x_value"]),
                "reference_y_value": float(panel["reference_y_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_vertical_box_id": reference_vertical_box_id,
                "reference_horizontal_box_id": reference_horizontal_box_id,
                "reference_label_box_id": reference_label_box_id,
                "x_grid": [float(value) for value in panel["x_grid"]],
                "y_grid": [float(value) for value in panel["y_grid"]],
                "response_grid": [[float(value) for value in row] for row in panel["response_grid"]],
                "observed_points": normalized_observed_points,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "colorbar_label": str(display_payload.get("colorbar_label") or "").strip(),
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

