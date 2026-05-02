from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    dump_json,
)

def _render_python_celltype_marker_dotplot_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panel_order = list(display_payload.get("panel_order") or [])
    celltype_order = list(display_payload.get("celltype_order") or [])
    marker_order = list(display_payload.get("marker_order") or [])
    points = list(display_payload.get("points") or [])
    if not panel_order or not celltype_order or not marker_order or not points:
        raise RuntimeError(f"{template_id} requires non-empty panel_order, celltype_order, marker_order, and points")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"

    celltype_labels = [str(item["label"]) for item in celltype_order]
    marker_labels = [str(item["label"]) for item in marker_order]
    panel_id_order = [str(item["panel_id"]) for item in panel_order]
    panel_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in panel_order}
    point_lookup = {
        (str(item["panel_id"]), str(item["celltype_label"]), str(item["marker_label"])): item
        for item in points
    }
    marker_position_lookup = {label: index for index, label in enumerate(marker_labels)}
    celltype_position_lookup = {label: index for index, label in enumerate(celltype_labels)}

    all_effect_values = [float(item["effect_value"]) for item in points]
    all_size_values = [float(item["size_value"]) for item in points]
    size_min = min(all_size_values)
    size_max = max(all_size_values)
    max_abs_effect = max(abs(value) for value in all_effect_values)
    max_abs_effect = max(max_abs_effect, 1e-6)

    if any(value < 0.0 for value in all_effect_values) and any(value > 0.0 for value in all_effect_values):
        color_norm: matplotlib.colors.Normalize = matplotlib.colors.TwoSlopeNorm(
            vmin=-max_abs_effect,
            vcenter=0.0,
            vmax=max_abs_effect,
        )
    else:
        min_effect = min(all_effect_values)
        max_effect = max(all_effect_values)
        if math.isclose(min_effect, max_effect, rel_tol=1e-9, abs_tol=1e-9):
            min_effect -= 1.0
            max_effect += 1.0
        color_norm = matplotlib.colors.Normalize(vmin=min_effect, vmax=max_effect)
    effect_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "celltype_marker_dotplot",
        [negative_color, "#f8fafc", positive_color],
    )

    def _marker_size(size_value: float) -> float:
        if math.isclose(size_min, size_max, rel_tol=1e-9, abs_tol=1e-9):
            return 220.0
        normalized = (size_value - size_min) / (size_max - size_min)
        return 110.0 + normalized * 250.0

    figure_width = max(8.6, 4.4 * len(panel_id_order) + 1.8)
    fig, axes = plt.subplots(1, len(panel_id_order), figsize=(figure_width, 6.2), squeeze=False)
    axes_list = list(axes[0])
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.90,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
            y=0.985,
        )

    scatter_artist = None
    panel_records: list[dict[str, Any]] = []
    marker_positions = list(range(len(marker_labels)))
    celltype_positions = list(range(len(celltype_labels)))
    for axes_item, panel_id in zip(axes_list, panel_id_order, strict=True):
        panel_points = [
            point_lookup[(panel_id, celltype_label, marker_label)]
            for celltype_label in celltype_labels
            for marker_label in marker_labels
        ]
        scatter_x = [marker_position_lookup[str(item["marker_label"])] for item in panel_points]
        scatter_y = [celltype_position_lookup[str(item["celltype_label"])] for item in panel_points]
        scatter_sizes = [_marker_size(float(item["size_value"])) for item in panel_points]
        scatter_colors = [float(item["effect_value"]) for item in panel_points]
        scatter_artist = axes_item.scatter(
            scatter_x,
            scatter_y,
            s=scatter_sizes,
            c=scatter_colors,
            cmap=effect_cmap,
            norm=color_norm,
            alpha=0.94,
            edgecolors="white",
            linewidths=0.8,
            zorder=3,
        )
        axes_item.set_xlim(-0.5, len(marker_labels) - 0.5)
        axes_item.set_ylim(-0.5, len(celltype_labels) - 0.5)
        axes_item.set_xticks(marker_positions)
        axes_item.set_xticklabels(marker_labels, rotation=24, ha="right", fontsize=tick_size, color=neutral_color)
        axes_item.set_yticks(celltype_positions)
        axes_item.set_yticklabels(celltype_labels, fontsize=tick_size, color=neutral_color)
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_title(
            panel_title_lookup[panel_id],
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=10.0,
        )
        axes_item.tick_params(axis="x", colors=neutral_color)
        axes_item.tick_params(axis="y", length=0, colors=neutral_color)
        axes_item.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        axes_item.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        _apply_publication_axes_style(axes_item)
        panel_records.append({"panel_id": panel_id, "axes": axes_item, "points": panel_points})

    top_margin = 0.84 if show_figure_title else 0.88
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.18, right=0.86, top=top_margin, bottom=0.28, wspace=0.24)

    y_axis_title_artist = fig.text(
        0.07,
        0.54,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        ha="center",
        va="center",
    )

    legend_value_candidates = sorted({round(size_min, 2), round((size_min + size_max) / 2.0, 2), round(size_max, 2)})
    legend_handles = [
        plt.scatter([], [], s=_marker_size(float(value)), color="#94a3b8", edgecolors="white", linewidths=0.8)
        for value in legend_value_candidates
    ]
    legend = fig.legend(
        legend_handles,
        [f"{value:g}" for value in legend_value_candidates],
        title=str(display_payload.get("size_scale_label") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.50, 0.02),
        ncol=len(legend_handles),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.4),
        title_fontsize=max(tick_size - 0.4, 8.8),
        columnspacing=1.4,
    )
    if scatter_artist is None:
        raise RuntimeError(f"{template_id} failed to render scatter artist")
    colorbar = fig.colorbar(scatter_artist, ax=axes_list, fraction=0.040, pad=0.03)
    colorbar.set_label(
        str(display_payload.get("effect_scale_label") or "").strip(),
        fontsize=max(axis_title_size - 0.4, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors=neutral_color)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.015, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.4, 13.0),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=chr(ord("A") + index))
        for index, record in enumerate(panel_records)
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
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=fig,
            bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="subplot_y_axis_title",
        )
    )
    panel_boxes: list[dict[str, Any]] = []
    normalized_panels: list[dict[str, Any]] = []
    for index, (record, panel_label_artist) in enumerate(zip(panel_records, panel_label_artists, strict=True), start=1):
        axes_item = record["axes"]
        panel_box_id = f"panel_{chr(ord('A') + index - 1)}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        panel_title_box_id = f"panel_title_{chr(ord('A') + index - 1)}"
        x_axis_title_box_id = f"x_axis_title_{chr(ord('A') + index - 1)}"
        panel_label_box_id = f"panel_label_{chr(ord('A') + index - 1)}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
                    box_id=panel_title_box_id,
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=x_axis_title_box_id,
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=panel_label_box_id,
                    box_type="panel_label",
                ),
            ]
        )
        normalized_points: list[dict[str, Any]] = []
        for point in record["points"]:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(marker_position_lookup[str(point["marker_label"])]),
                y=float(celltype_position_lookup[str(point["celltype_label"])]),
            )
            normalized_points.append(
                {
                    "celltype_label": str(point["celltype_label"]),
                    "marker_label": str(point["marker_label"]),
                    "x": point_x,
                    "y": point_y,
                    "effect_value": float(point["effect_value"]),
                    "size_value": float(point["size_value"]),
                }
            )
        normalized_panels.append(
            {
                "panel_id": str(record["panel_id"]),
                "panel_title": panel_title_lookup[str(record["panel_id"])],
                "panel_label": chr(ord("A") + index - 1),
                "panel_box_id": panel_box_id,
                "panel_label_box_id": panel_label_box_id,
                "panel_title_box_id": panel_title_box_id,
                "x_axis_title_box_id": x_axis_title_box_id,
                "points": normalized_points,
            }
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=colorbar.ax.get_window_extent(renderer=renderer),
                    box_id="colorbar",
                    box_type="colorbar",
                ),
            ],
            "metrics": {
                "effect_scale_label": str(display_payload.get("effect_scale_label") or "").strip(),
                "size_scale_label": str(display_payload.get("size_scale_label") or "").strip(),
                "celltype_labels": celltype_labels,
                "marker_labels": marker_labels,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

