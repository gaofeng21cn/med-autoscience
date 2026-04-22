from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ..shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _data_box_to_layout_box,
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    _wrap_flow_text_to_width,
    dump_json,
)

def _render_python_pathway_enrichment_dotplot_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panel_order = list(display_payload.get("panel_order") or [])
    pathway_order = list(display_payload.get("pathway_order") or [])
    points = list(display_payload.get("points") or [])
    if not panel_order or not pathway_order or not points:
        raise RuntimeError(f"{template_id} requires non-empty panel_order, pathway_order, and points")

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

    pathway_labels = [str(item["label"]) for item in pathway_order]
    panel_id_order = [str(item["panel_id"]) for item in panel_order]
    panel_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in panel_order}
    point_lookup = {(str(item["panel_id"]), str(item["pathway_label"])): item for item in points}

    all_x_values = [float(item["x_value"]) for item in points]
    all_effect_values = [float(item["effect_value"]) for item in points]
    all_size_values = [float(item["size_value"]) for item in points]
    global_x_min = min(all_x_values)
    global_x_max = max(all_x_values)
    global_x_span = max(global_x_max - global_x_min, 1e-6)
    x_padding = max(global_x_span * 0.08, 0.12)
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
        "pathway_enrichment_dotplot",
        [negative_color, "#f8fafc", positive_color],
    )

    def _marker_size(size_value: float) -> float:
        if math.isclose(size_min, size_max, rel_tol=1e-9, abs_tol=1e-9):
            return 220.0
        normalized = (size_value - size_min) / (size_max - size_min)
        return 120.0 + normalized * 260.0

    figure_width = max(8.8, 4.2 * len(panel_id_order) + 1.8)
    fig, axes = plt.subplots(1, len(panel_id_order), figsize=(figure_width, 5.8), squeeze=False)
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
    y_positions = list(range(len(pathway_labels)))
    pathway_position_lookup = {label: index for index, label in enumerate(pathway_labels)}
    for axes_item, panel_id in zip(axes_list, panel_id_order, strict=True):
        panel_points = [point_lookup[(panel_id, pathway_label)] for pathway_label in pathway_labels]
        scatter_x = [float(item["x_value"]) for item in panel_points]
        scatter_y = [pathway_position_lookup[str(item["pathway_label"])] for item in panel_points]
        scatter_sizes = [_marker_size(float(item["size_value"])) for item in panel_points]
        scatter_colors = [float(item["effect_value"]) for item in panel_points]
        scatter_artist = axes_item.scatter(
            scatter_x,
            scatter_y,
            s=scatter_sizes,
            c=scatter_colors,
            cmap=effect_cmap,
            norm=color_norm,
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        if global_x_min < 0.0 < global_x_max:
            axes_item.axvline(0.0, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(global_x_min - x_padding, global_x_max + x_padding)
        axes_item.set_ylim(-0.5, len(pathway_labels) - 0.5)
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(pathway_labels, fontsize=tick_size, color=neutral_color)
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
        axes_item.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
        axes_item.tick_params(axis="y", length=0, colors=neutral_color)
        axes_item.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)
        panel_records.append({"panel_id": panel_id, "axes": axes_item, "points": panel_points})

    top_margin = 0.84 if show_figure_title else 0.88
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.20, right=0.86, top=top_margin, bottom=0.22, wspace=0.24)

    y_axis_title_artist = fig.text(
        0.07,
        0.52,
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
                x=float(point["x_value"]),
                y=float(pathway_position_lookup[str(point["pathway_label"])]),
            )
            normalized_points.append(
                {
                    "pathway_label": str(point["pathway_label"]),
                    "x": point_x,
                    "y": point_y,
                    "x_value": float(point["x_value"]),
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
                "pathway_labels": pathway_labels,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

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

def _render_python_oncoplot_mutation_landscape_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    gene_order = list(display_payload.get("gene_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    mutation_records = list(display_payload.get("mutation_records") or [])
    if not gene_order or not sample_order or not annotation_tracks or not mutation_records:
        raise RuntimeError(
            f"{template_id} requires non-empty gene_order, sample_order, annotation_tracks, and mutation_records"
        )

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

    primary_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    secondary_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    contrast_color = str(palette.get("contrast") or "#8b3a3a").strip() or "#8b3a3a"
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#f7ebeb").strip() or "#f7ebeb"

    gene_labels = [str(item["label"]) for item in gene_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    gene_index = {gene_label: index for index, gene_label in enumerate(gene_labels)}

    mutation_lookup = {
        (str(item["sample_id"]), str(item["gene_label"])): str(item["alteration_class"])
        for item in mutation_records
    }
    burden_counts = {
        sample_id: sum(1 for gene_label in gene_labels if (sample_id, gene_label) in mutation_lookup)
        for sample_id in sample_ids
    }
    gene_altered_counts = {
        gene_label: sum(1 for sample_id in sample_ids if (sample_id, gene_label) in mutation_lookup)
        for gene_label in gene_labels
    }
    gene_altered_fractions = {
        gene_label: gene_altered_counts[gene_label] / float(len(sample_ids))
        for gene_label in gene_labels
    }

    alteration_color_map = {
        "missense": primary_color,
        "truncating": contrast_color,
        "amplification": secondary_color,
        "fusion": neutral_color,
    }
    alteration_label_map = {
        "missense": "Missense",
        "truncating": "Truncating",
        "amplification": "Amplification",
        "fusion": "Fusion",
    }
    track_palette_cycle = (
        primary_soft,
        secondary_soft,
        contrast_soft,
        "#eef2ff",
        "#f8fafc",
        "#ecfccb",
    )
    track_fill_by_id: dict[str, dict[str, str]] = {}
    for track in annotation_tracks:
        category_labels = [str(item["category_label"]) for item in track["values"]]
        ordered_categories = list(dict.fromkeys(category_labels))
        track_fill_by_id[str(track["track_id"])] = {
            category_label: track_palette_cycle[index % len(track_palette_cycle)]
            for index, category_label in enumerate(ordered_categories)
        }

    figure_width = max(8.4, 0.52 * len(sample_ids) + 4.4)
    figure_height = max(5.6, 0.60 * len(gene_labels) + 0.42 * len(annotation_tracks) + 2.8)
    fig = plt.figure(figsize=(figure_width, figure_height))
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

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        2,
        left=0.20,
        right=0.92,
        bottom=0.22,
        top=top_margin,
        width_ratios=(max(3.8, 0.60 * len(sample_ids) + 0.8), 1.55),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.70 * len(gene_labels))),
        hspace=0.10,
        wspace=0.14,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)

    burden_positions = list(range(len(sample_ids)))
    burden_values = [burden_counts[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(gene_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(sample_ids, rotation=45, ha="right", fontsize=max(tick_size - 0.3, 8.6), color=neutral_color)
    matrix_axes.set_yticks(range(len(gene_labels)))
    matrix_axes.set_yticklabels(gene_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(max(gene_altered_fractions.values()), 1e-6)
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(gene_labels)))
    frequency_values = [gene_altered_fractions[gene_label] for gene_label in gene_labels]
    frequency_bars = frequency_axes.barh(
        frequency_positions,
        frequency_values,
        height=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.set_xlim(0.0, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(gene_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    matrix_background_color = "#ffffff"
    altered_cell_patches: list[dict[str, Any]] = []
    for gene_label in gene_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = gene_index[gene_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=matrix_background_color,
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            alteration_class = mutation_lookup.get((sample_id, gene_label))
            if not alteration_class:
                continue
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=alteration_color_map[alteration_class],
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            altered_cell_patches.append(
                {
                    "box_id": f"mutation_{gene_label}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "gene_label": gene_label,
                    "alteration_class": alteration_class,
                }
            )

    legend_handles = [
        matplotlib.patches.Patch(facecolor=alteration_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("missense", "truncating", "amplification", "fusion")
    ]
    legend = fig.legend(
        handles=legend_handles,
        labels=[handle.get_label() for handle in legend_handles],
        title=str(display_payload.get("mutation_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.53, 0.02),
        ncol=min(4, len(legend_handles)),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.3, 8.8),
        columnspacing=1.4,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, burden_y0 = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    burden_x1, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, annotation_y0 = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

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
    y_axis_title_box = _bbox_to_layout_box(
        figure=fig,
        bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
        box_id="y_axis_title",
        box_type="subplot_y_axis_title",
    )
    layout_boxes.extend(
        [
            y_axis_title_box,
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {
                "sample_id": sample_id,
                "altered_gene_count": int(burden_counts[sample_id]),
                "bar_box_id": box_id,
            }
        )

    gene_frequency_metrics: list[dict[str, Any]] = []
    for gene_label, bar in zip(gene_labels, frequency_bars, strict=True):
        box_id = f"freq_bar_{gene_label}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        gene_frequency_metrics.append(
            {
                "gene_label": gene_label,
                "altered_fraction": float(gene_altered_fractions[gene_label]),
                "bar_box_id": box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    altered_cells_metrics: list[dict[str, Any]] = []
    for item in altered_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="mutation_cell",
            )
        )
        altered_cells_metrics.append(
            {
                "sample_id": str(item["sample_id"]),
                "gene_label": str(item["gene_label"]),
                "alteration_class": str(item["alteration_class"]),
                "box_id": str(item["box_id"]),
            }
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

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
                )
            ],
            "metrics": {
                "mutation_legend_title": str(display_payload.get("mutation_legend_title") or "").strip(),
                "sample_ids": sample_ids,
                "gene_labels": gene_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "gene_altered_frequencies": gene_frequency_metrics,
                "altered_cells": altered_cells_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_cnv_recurrence_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    region_order = list(display_payload.get("region_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    cnv_records = list(display_payload.get("cnv_records") or [])
    if not region_order or not sample_order or not annotation_tracks or not cnv_records:
        raise RuntimeError(
            f"{template_id} requires non-empty region_order, sample_order, annotation_tracks, and cnv_records"
        )

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

    primary_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    secondary_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    contrast_color = str(palette.get("contrast") or "#d97706").strip() or "#d97706"
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#fef3c7").strip() or "#fef3c7"

    region_labels = [str(item["label"]) for item in region_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    region_index = {region_label: index for index, region_label in enumerate(region_labels)}

    cnv_lookup = {
        (str(item["sample_id"]), str(item["region_label"])): str(item["cnv_state"])
        for item in cnv_records
    }
    sample_burdens = {
        sample_id: sum(1 for region_label in region_labels if (sample_id, region_label) in cnv_lookup)
        for sample_id in sample_ids
    }
    gain_like_states = {"amplification", "gain"}
    loss_like_states = {"loss", "deep_loss"}
    region_gain_counts = {
        region_label: sum(
            1 for sample_id in sample_ids if cnv_lookup.get((sample_id, region_label)) in gain_like_states
        )
        for region_label in region_labels
    }
    region_loss_counts = {
        region_label: sum(
            1 for sample_id in sample_ids if cnv_lookup.get((sample_id, region_label)) in loss_like_states
        )
        for region_label in region_labels
    }
    region_gain_fractions = {
        region_label: region_gain_counts[region_label] / float(len(sample_ids))
        for region_label in region_labels
    }
    region_loss_fractions = {
        region_label: region_loss_counts[region_label] / float(len(sample_ids))
        for region_label in region_labels
    }

    cnv_color_map = {
        "amplification": secondary_color,
        "gain": contrast_color,
        "loss": primary_color,
        "deep_loss": neutral_color,
    }
    cnv_label_map = {
        "amplification": "Amplification",
        "gain": "Gain",
        "loss": "Loss",
        "deep_loss": "Deep loss",
    }
    track_palette_cycle = (
        primary_soft,
        secondary_soft,
        contrast_soft,
        "#eef2ff",
        "#f8fafc",
        "#ecfccb",
    )
    track_fill_by_id: dict[str, dict[str, str]] = {}
    for track in annotation_tracks:
        category_labels = [str(item["category_label"]) for item in track["values"]]
        ordered_categories = list(dict.fromkeys(category_labels))
        track_fill_by_id[str(track["track_id"])] = {
            category_label: track_palette_cycle[index % len(track_palette_cycle)]
            for index, category_label in enumerate(ordered_categories)
        }

    figure_width = max(8.4, 0.52 * len(sample_ids) + 4.6)
    figure_height = max(5.8, 0.58 * len(region_labels) + 0.42 * len(annotation_tracks) + 2.9)
    fig = plt.figure(figsize=(figure_width, figure_height))
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

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        2,
        left=0.20,
        right=0.93,
        bottom=0.22,
        top=top_margin,
        width_ratios=(max(3.8, 0.60 * len(sample_ids) + 0.8), 1.70),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.66 * len(region_labels))),
        hspace=0.10,
        wspace=0.14,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)

    burden_positions = list(range(len(sample_ids)))
    burden_values = [sample_burdens[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(region_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(sample_ids, rotation=45, ha="right", fontsize=max(tick_size - 0.3, 8.6), color=neutral_color)
    matrix_axes.set_yticks(range(len(region_labels)))
    matrix_axes.set_yticklabels(region_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(
        max(region_gain_fractions.values(), default=0.0),
        max(region_loss_fractions.values(), default=0.0),
        1e-6,
    )
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(region_labels)))
    gain_values = [region_gain_fractions[region_label] for region_label in region_labels]
    loss_values = [-region_loss_fractions[region_label] for region_label in region_labels]
    gain_bars = frequency_axes.barh(
        frequency_positions,
        gain_values,
        height=0.32,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    loss_bars = frequency_axes.barh(
        frequency_positions,
        loss_values,
        height=0.32,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.axvline(0.0, color=neutral_color, linewidth=0.9, alpha=0.9, zorder=2)
    frequency_axes.set_xlim(-frequency_limit, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(region_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    cnv_cell_patches: list[dict[str, Any]] = []
    for region_label in region_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = region_index[region_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor="#ffffff",
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            cnv_state = cnv_lookup.get((sample_id, region_label))
            if not cnv_state:
                continue
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=cnv_color_map[cnv_state],
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            cnv_cell_patches.append(
                {
                    "box_id": f"cnv_{region_label}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "region_label": region_label,
                    "cnv_state": cnv_state,
                }
            )

    legend_handles = [
        matplotlib.patches.Patch(facecolor=cnv_color_map[key], edgecolor="white", label=cnv_label_map[key])
        for key in ("amplification", "gain", "loss", "deep_loss")
    ]
    legend = fig.legend(
        handles=legend_handles,
        labels=[handle.get_label() for handle in legend_handles],
        title=str(display_payload.get("cnv_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.53, 0.02),
        ncol=min(4, len(legend_handles)),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.3, 8.8),
        columnspacing=1.4,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, burden_y0 = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    burden_x1, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, annotation_y0 = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

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
    y_axis_title_box = _bbox_to_layout_box(
        figure=fig,
        bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
        box_id="y_axis_title",
        box_type="subplot_y_axis_title",
    )
    layout_boxes.extend(
        [
            y_axis_title_box,
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {
                "sample_id": sample_id,
                "altered_region_count": int(sample_burdens[sample_id]),
                "bar_box_id": box_id,
            }
        )

    region_frequency_metrics: list[dict[str, Any]] = []
    for region_label, gain_bar, loss_bar in zip(region_labels, gain_bars, loss_bars, strict=True):
        gain_box_id = f"freq_gain_{region_label}"
        loss_box_id = f"freq_loss_{region_label}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=gain_bar.get_window_extent(renderer=renderer),
                    box_id=gain_box_id,
                    box_type="bar",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=loss_bar.get_window_extent(renderer=renderer),
                    box_id=loss_box_id,
                    box_type="bar",
                ),
            ]
        )
        region_frequency_metrics.append(
            {
                "region_label": region_label,
                "gain_fraction": float(region_gain_fractions[region_label]),
                "loss_fraction": float(region_loss_fractions[region_label]),
                "gain_bar_box_id": gain_box_id,
                "loss_bar_box_id": loss_box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    cnv_cells_metrics: list[dict[str, Any]] = []
    for item in cnv_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="cnv_cell",
            )
        )
        cnv_cells_metrics.append(
            {
                "sample_id": str(item["sample_id"]),
                "region_label": str(item["region_label"]),
                "cnv_state": str(item["cnv_state"]),
                "box_id": str(item["box_id"]),
            }
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

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
                )
            ],
            "metrics": {
                "cnv_legend_title": str(display_payload.get("cnv_legend_title") or "").strip(),
                "sample_ids": sample_ids,
                "region_labels": region_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "region_gain_loss_frequencies": region_frequency_metrics,
                "cnv_cells": cnv_cells_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_genomic_alteration_landscape_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    gene_order = list(display_payload.get("gene_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    alteration_records = list(display_payload.get("alteration_records") or [])
    if not gene_order or not sample_order or not annotation_tracks or not alteration_records:
        raise RuntimeError(
            f"{template_id} requires non-empty gene_order, sample_order, annotation_tracks, and alteration_records"
        )

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

    primary_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    secondary_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#f7ebeb").strip() or "#f7ebeb"

    gene_labels = [str(item["label"]) for item in gene_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    gene_index = {gene_label: index for index, gene_label in enumerate(gene_labels)}

    alteration_lookup = {
        (str(item["sample_id"]), str(item["gene_label"])): {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "mutation_class": str(item.get("mutation_class") or "").strip(),
            "cnv_state": str(item.get("cnv_state") or "").strip(),
        }
        for item in alteration_records
    }
    burden_counts = {
        sample_id: sum(1 for gene_label in gene_labels if (sample_id, gene_label) in alteration_lookup)
        for sample_id in sample_ids
    }
    gene_altered_counts = {
        gene_label: sum(1 for sample_id in sample_ids if (sample_id, gene_label) in alteration_lookup)
        for gene_label in gene_labels
    }
    gene_altered_fractions = {
        gene_label: gene_altered_counts[gene_label] / float(len(sample_ids))
        for gene_label in gene_labels
    }

    mutation_color_map = {
        "missense": primary_color,
        "truncating": "#8b3a3a",
        "fusion": "#475569",
    }
    cnv_color_map = {
        "amplification": secondary_color,
        "gain": "#d97706",
        "loss": "#0f766e",
        "deep_loss": "#111827",
    }
    alteration_label_map = {
        "missense": "Missense",
        "truncating": "Truncating",
        "fusion": "Fusion",
        "amplification": "Amplification",
        "gain": "Gain",
        "loss": "Loss",
        "deep_loss": "Deep loss",
    }
    track_palette_cycle = (
        primary_soft,
        secondary_soft,
        contrast_soft,
        "#eef2ff",
        "#f8fafc",
        "#ecfccb",
    )
    track_fill_by_id: dict[str, dict[str, str]] = {}
    for track in annotation_tracks:
        category_labels = [str(item["category_label"]) for item in track["values"]]
        ordered_categories = list(dict.fromkeys(category_labels))
        track_fill_by_id[str(track["track_id"])] = {
            category_label: track_palette_cycle[index % len(track_palette_cycle)]
            for index, category_label in enumerate(ordered_categories)
        }

    figure_width = max(8.8, 0.52 * len(sample_ids) + 4.8)
    figure_height = max(5.8, 0.60 * len(gene_labels) + 0.42 * len(annotation_tracks) + 3.0)
    fig = plt.figure(figsize=(figure_width, figure_height))
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

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        2,
        left=0.20,
        right=0.93,
        bottom=0.22,
        top=top_margin,
        width_ratios=(max(3.8, 0.60 * len(sample_ids) + 0.8), 1.55),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.70 * len(gene_labels))),
        hspace=0.10,
        wspace=0.14,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)

    burden_positions = list(range(len(sample_ids)))
    burden_values = [burden_counts[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(gene_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(
        sample_ids,
        rotation=45,
        ha="right",
        fontsize=max(tick_size - 0.3, 8.6),
        color=neutral_color,
    )
    matrix_axes.set_yticks(range(len(gene_labels)))
    matrix_axes.set_yticklabels(gene_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(max(gene_altered_fractions.values()), 1e-6)
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(gene_labels)))
    frequency_values = [gene_altered_fractions[gene_label] for gene_label in gene_labels]
    frequency_bars = frequency_axes.barh(
        frequency_positions,
        frequency_values,
        height=0.74,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.set_xlim(0.0, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(gene_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    alteration_cell_patches: list[dict[str, Any]] = []
    alteration_overlay_patches: list[dict[str, Any]] = []
    for gene_label in gene_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = gene_index[gene_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor="#ffffff",
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            alteration = alteration_lookup.get((sample_id, gene_label))
            if alteration is None:
                continue
            mutation_class = str(alteration.get("mutation_class") or "").strip()
            cnv_state = str(alteration.get("cnv_state") or "").strip()
            cell_color = cnv_color_map[cnv_state] if cnv_state else mutation_color_map[mutation_class]
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=cell_color,
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            box_id = f"alteration_{gene_label}_{sample_id}"
            overlay_box_id = ""
            if mutation_class and cnv_state:
                overlay_patch = matplotlib.patches.Rectangle(
                    (x_index - 0.21, y_index - 0.32),
                    0.42,
                    0.64,
                    facecolor=mutation_color_map[mutation_class],
                    edgecolor="white",
                    linewidth=0.8,
                    zorder=4,
                )
                matrix_axes.add_patch(overlay_patch)
                overlay_box_id = f"overlay_{gene_label}_{sample_id}"
                alteration_overlay_patches.append(
                    {
                        "box_id": overlay_box_id,
                        "patch": overlay_patch,
                    }
                )
            alteration_cell_patches.append(
                {
                    "box_id": box_id,
                    "patch": patch,
                    "sample_id": sample_id,
                    "gene_label": gene_label,
                    "mutation_class": mutation_class,
                    "cnv_state": cnv_state,
                    "overlay_box_id": overlay_box_id,
                }
            )

    legend_handles = [
        matplotlib.patches.Patch(facecolor=mutation_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("missense", "truncating", "fusion")
    ] + [
        matplotlib.patches.Patch(facecolor=cnv_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("amplification", "gain", "loss", "deep_loss")
    ]
    legend = fig.legend(
        handles=legend_handles,
        labels=[handle.get_label() for handle in legend_handles],
        title=str(display_payload.get("alteration_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.54, 0.02),
        ncol=4,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.3, 8.8),
        columnspacing=1.4,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, _ = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    _, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, _ = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

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
    y_axis_title_box = _bbox_to_layout_box(
        figure=fig,
        bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
        box_id="y_axis_title",
        box_type="subplot_y_axis_title",
    )
    layout_boxes.extend(
        [
            y_axis_title_box,
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {
                "sample_id": sample_id,
                "altered_gene_count": int(burden_counts[sample_id]),
                "bar_box_id": box_id,
            }
        )

    gene_frequency_metrics: list[dict[str, Any]] = []
    for gene_label, bar in zip(gene_labels, frequency_bars, strict=True):
        box_id = f"freq_bar_{gene_label}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        gene_frequency_metrics.append(
            {
                "gene_label": gene_label,
                "altered_fraction": float(gene_altered_fractions[gene_label]),
                "bar_box_id": box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    overlay_box_id_by_alteration_id: dict[str, str] = {}
    for item in alteration_overlay_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_overlay",
            )
        )
        overlay_box_id_by_alteration_id[str(item["box_id"])] = str(item["box_id"])

    alteration_cells_metrics: list[dict[str, Any]] = []
    for item in alteration_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_cell",
            )
        )
        metric_item = {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "box_id": str(item["box_id"]),
        }
        mutation_class = str(item["mutation_class"])
        cnv_state = str(item["cnv_state"])
        if mutation_class:
            metric_item["mutation_class"] = mutation_class
        if cnv_state:
            metric_item["cnv_state"] = cnv_state
        overlay_box_id = str(item["overlay_box_id"])
        if overlay_box_id:
            metric_item["overlay_box_id"] = overlay_box_id_by_alteration_id[overlay_box_id]
        alteration_cells_metrics.append(metric_item)

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

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
                )
            ],
            "metrics": {
                "alteration_legend_title": str(display_payload.get("alteration_legend_title") or "").strip(),
                "sample_ids": sample_ids,
                "gene_labels": gene_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "gene_alteration_frequencies": gene_frequency_metrics,
                "alteration_cells": alteration_cells_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_genomic_alteration_consequence_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    gene_order = list(display_payload.get("gene_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    alteration_records = list(display_payload.get("alteration_records") or [])
    driver_gene_order = list(display_payload.get("driver_gene_order") or [])
    consequence_panel_order = list(display_payload.get("consequence_panel_order") or [])
    consequence_points = list(display_payload.get("consequence_points") or [])
    if (
        not gene_order
        or not sample_order
        or not annotation_tracks
        or not alteration_records
        or not driver_gene_order
        or not consequence_panel_order
        or not consequence_points
    ):
        raise RuntimeError(
            f"{template_id} requires non-empty gene_order, sample_order, annotation_tracks, alteration_records, "
            "driver_gene_order, consequence_panel_order, and consequence_points"
        )

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

    primary_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    secondary_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#f7ebeb").strip() or "#f7ebeb"
    background_color = str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1"

    gene_labels = [str(item["label"]) for item in gene_order]
    driver_gene_labels = [str(item["label"]) for item in driver_gene_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    gene_index = {gene_label: index for index, gene_label in enumerate(gene_labels)}

    alteration_lookup = {
        (str(item["sample_id"]), str(item["gene_label"])): {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "mutation_class": str(item.get("mutation_class") or "").strip(),
            "cnv_state": str(item.get("cnv_state") or "").strip(),
        }
        for item in alteration_records
    }
    burden_counts = {
        sample_id: sum(1 for gene_label in gene_labels if (sample_id, gene_label) in alteration_lookup)
        for sample_id in sample_ids
    }
    gene_altered_counts = {
        gene_label: sum(1 for sample_id in sample_ids if (sample_id, gene_label) in alteration_lookup)
        for gene_label in gene_labels
    }
    gene_altered_fractions = {
        gene_label: gene_altered_counts[gene_label] / float(len(sample_ids))
        for gene_label in gene_labels
    }

    mutation_color_map = {
        "missense": primary_color,
        "truncating": "#8b3a3a",
        "fusion": "#475569",
    }
    cnv_color_map = {
        "amplification": secondary_color,
        "gain": "#d97706",
        "loss": "#0f766e",
        "deep_loss": "#111827",
    }
    alteration_label_map = {
        "missense": "Missense",
        "truncating": "Truncating",
        "fusion": "Fusion",
        "amplification": "Amplification",
        "gain": "Gain",
        "loss": "Loss",
        "deep_loss": "Deep loss",
    }
    track_palette_cycle = (
        primary_soft,
        secondary_soft,
        contrast_soft,
        "#eef2ff",
        "#f8fafc",
        "#ecfccb",
    )
    track_fill_by_id: dict[str, dict[str, str]] = {}
    for track in annotation_tracks:
        category_labels = [str(item["category_label"]) for item in track["values"]]
        ordered_categories = list(dict.fromkeys(category_labels))
        track_fill_by_id[str(track["track_id"])] = {
            category_label: track_palette_cycle[index % len(track_palette_cycle)]
            for index, category_label in enumerate(ordered_categories)
        }

    panel_id_order = [str(item["panel_id"]) for item in consequence_panel_order]
    panel_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in consequence_panel_order}
    point_lookup: dict[str, list[dict[str, Any]]] = {panel_id: [] for panel_id in panel_id_order}
    for point in consequence_points:
        point_lookup[str(point["panel_id"])].append(point)

    effect_threshold = float(display_payload.get("effect_threshold") or 0.0)
    significance_threshold = float(display_payload.get("significance_threshold") or 0.0)
    all_effect_values = [float(item["effect_value"]) for item in consequence_points]
    all_significance_values = [float(item["significance_value"]) for item in consequence_points]
    x_limit_core = max(max(abs(value) for value in all_effect_values), effect_threshold, 1e-6)
    x_padding = max(x_limit_core * 0.18, 0.20)
    x_limit_abs = x_limit_core + x_padding
    y_limit_top = max(max(all_significance_values), significance_threshold) * 1.12 + 0.25
    y_limit_top = max(y_limit_top, significance_threshold + 0.50)

    figure_width = max(12.6, 0.52 * len(sample_ids) + 7.6)
    figure_height = max(6.4, 0.60 * len(gene_labels) + 3.2, 2.4 + 1.75 * len(panel_id_order))
    fig = plt.figure(figsize=(figure_width, figure_height))
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.92,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
            y=0.985,
        )

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        3,
        left=0.17,
        right=0.96,
        bottom=0.22,
        top=top_margin,
        width_ratios=(
            max(3.8, 0.60 * len(sample_ids) + 0.8),
            1.45,
            max(2.5, 1.9 + 0.30 * len(driver_gene_labels)),
        ),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.70 * len(gene_labels))),
        hspace=0.10,
        wspace=0.16,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)
    consequence_grid = grid[:, 2].subgridspec(len(panel_id_order), 1, hspace=0.28)
    consequence_axes_list = [fig.add_subplot(consequence_grid[index, 0]) for index in range(len(panel_id_order))]

    burden_positions = list(range(len(sample_ids)))
    burden_values = [burden_counts[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(gene_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(
        sample_ids,
        rotation=45,
        ha="right",
        fontsize=max(tick_size - 0.3, 8.6),
        color=neutral_color,
    )
    matrix_axes.set_yticks(range(len(gene_labels)))
    matrix_axes.set_yticklabels(gene_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(max(gene_altered_fractions.values()), 1e-6)
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(gene_labels)))
    frequency_values = [gene_altered_fractions[gene_label] for gene_label in gene_labels]
    frequency_bars = frequency_axes.barh(
        frequency_positions,
        frequency_values,
        height=0.74,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.set_xlim(0.0, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(gene_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    alteration_cell_patches: list[dict[str, Any]] = []
    alteration_overlay_patches: list[dict[str, Any]] = []
    for gene_label in gene_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = gene_index[gene_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor="#ffffff",
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            alteration = alteration_lookup.get((sample_id, gene_label))
            if alteration is None:
                continue
            mutation_class = str(alteration.get("mutation_class") or "").strip()
            cnv_state = str(alteration.get("cnv_state") or "").strip()
            cell_color = cnv_color_map[cnv_state] if cnv_state else mutation_color_map[mutation_class]
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=cell_color,
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            box_id = f"alteration_{gene_label}_{sample_id}"
            overlay_box_id = ""
            if mutation_class and cnv_state:
                overlay_patch = matplotlib.patches.Rectangle(
                    (x_index - 0.21, y_index - 0.32),
                    0.42,
                    0.64,
                    facecolor=mutation_color_map[mutation_class],
                    edgecolor="white",
                    linewidth=0.8,
                    zorder=4,
                )
                matrix_axes.add_patch(overlay_patch)
                overlay_box_id = f"overlay_{gene_label}_{sample_id}"
                alteration_overlay_patches.append({"box_id": overlay_box_id, "patch": overlay_patch})
            alteration_cell_patches.append(
                {
                    "box_id": box_id,
                    "patch": patch,
                    "sample_id": sample_id,
                    "gene_label": gene_label,
                    "mutation_class": mutation_class,
                    "cnv_state": cnv_state,
                    "overlay_box_id": overlay_box_id,
                }
            )

    consequence_records: list[dict[str, Any]] = []
    for axes_item, panel_id in zip(consequence_axes_list, panel_id_order, strict=True):
        panel_points = list(point_lookup.get(panel_id) or [])
        scatter_colors = {
            "upregulated": secondary_color,
            "downregulated": primary_color,
            "background": background_color,
        }
        axes_item.scatter(
            [float(item["effect_value"]) for item in panel_points],
            [float(item["significance_value"]) for item in panel_points],
            s=74.0,
            c=[scatter_colors[str(item["regulation_class"])] for item in panel_points],
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        axes_item.axvline(-effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axvline(effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axhline(significance_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit_abs, x_limit_abs)
        axes_item.set_ylim(0.0, y_limit_top)
        axes_item.set_xlabel(
            str(display_payload.get("consequence_x_label") or "").strip(),
            fontsize=max(axis_title_size - 0.1, 10.0),
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_ylabel("")
        axes_item.set_title(
            panel_title_lookup[panel_id],
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
        axes_item.tick_params(axis="y", labelsize=tick_size, colors=neutral_color)
        axes_item.grid(axis="both", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        _apply_publication_axes_style(axes_item)

        point_artists: list[dict[str, Any]] = []
        label_artists: list[dict[str, Any]] = []
        for point in panel_points:
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            gene_label = str(point["gene_label"])
            point_box_id = f"consequence_point_{panel_id}_{gene_label}"
            point_artists.append(
                {
                    "point_box_id": point_box_id,
                    "gene_label": gene_label,
                    "effect_value": effect_value,
                    "significance_value": significance_value,
                    "regulation_class": str(point["regulation_class"]),
                }
            )
            offset_x = -8 if effect_value >= 0.0 else 8
            ha = "right" if effect_value >= 0.0 else "left"
            label_artist = axes_item.annotate(
                gene_label,
                xy=(effect_value, significance_value),
                xytext=(offset_x, 6),
                textcoords="offset points",
                fontsize=max(tick_size - 0.6, 8.2),
                color=neutral_color,
                ha=ha,
                va="bottom",
                zorder=4,
                annotation_clip=True,
            )
            label_artists.append(
                {
                    "gene_label": gene_label,
                    "box_id": f"consequence_label_{panel_id}_{gene_label}",
                    "artist": label_artist,
                }
            )

        consequence_records.append(
            {
                "panel_id": panel_id,
                "axes": axes_item,
                "points": point_artists,
                "label_artists": label_artists,
            }
        )

    alteration_legend_handles = [
        matplotlib.patches.Patch(facecolor=mutation_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("missense", "truncating", "fusion")
    ] + [
        matplotlib.patches.Patch(facecolor=cnv_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("amplification", "gain", "loss", "deep_loss")
    ]
    alteration_legend = fig.legend(
        handles=alteration_legend_handles,
        labels=[handle.get_label() for handle in alteration_legend_handles],
        title=str(display_payload.get("alteration_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.33, 0.02),
        ncol=4,
        frameon=False,
        fontsize=max(tick_size - 1.0, 8.0),
        title_fontsize=max(tick_size - 0.4, 8.6),
        columnspacing=1.2,
    )
    consequence_legend_handles = [
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=secondary_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Upregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=primary_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Downregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=background_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Background",
        ),
    ]
    consequence_legend = fig.legend(
        consequence_legend_handles,
        [str(handle.get_label()) for handle in consequence_legend_handles],
        title=str(display_payload.get("consequence_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.80, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.9, 8.0),
        title_fontsize=max(tick_size - 0.4, 8.6),
        columnspacing=1.1,
    )
    fig.add_artist(alteration_legend)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, _ = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    _, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, _ = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

    consequence_panel_label_artists: list[Any] = []
    for index, record in enumerate(consequence_records, start=1):
        axes_item = record["axes"]
        panel_token = chr(ord("B") + index - 1)
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.060, 0.020), 0.032)
        consequence_panel_label_artists.append(
            fig.text(
                panel_x0 + x_padding,
                panel_y1 - y_padding,
                panel_token,
                transform=fig.transFigure,
                fontsize=max(panel_label_size + 1.4, 13.0),
                fontweight="bold",
                color=neutral_color,
                ha="left",
                va="top",
            )
        )

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
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {
                "sample_id": sample_id,
                "altered_gene_count": int(burden_counts[sample_id]),
                "bar_box_id": box_id,
            }
        )

    gene_frequency_metrics: list[dict[str, Any]] = []
    for gene_label, bar in zip(gene_labels, frequency_bars, strict=True):
        box_id = f"freq_bar_{gene_label}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        gene_frequency_metrics.append(
            {
                "gene_label": gene_label,
                "altered_fraction": float(gene_altered_fractions[gene_label]),
                "bar_box_id": box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    overlay_box_id_by_alteration_id: dict[str, str] = {}
    for item in alteration_overlay_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_overlay",
            )
        )
        overlay_box_id_by_alteration_id[str(item["box_id"])] = str(item["box_id"])

    alteration_cells_metrics: list[dict[str, Any]] = []
    for item in alteration_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_cell",
            )
        )
        metric_item = {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "box_id": str(item["box_id"]),
        }
        mutation_class = str(item["mutation_class"])
        cnv_state = str(item["cnv_state"])
        if mutation_class:
            metric_item["mutation_class"] = mutation_class
        if cnv_state:
            metric_item["cnv_state"] = cnv_state
        overlay_box_id = str(item["overlay_box_id"])
        if overlay_box_id:
            metric_item["overlay_box_id"] = overlay_box_id_by_alteration_id[overlay_box_id]
        alteration_cells_metrics.append(metric_item)

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=alteration_legend.get_window_extent(renderer=renderer),
            box_id="legend_alteration",
            box_type="legend",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=consequence_legend.get_window_extent(renderer=renderer),
            box_id="legend_consequence",
            box_type="legend",
        ),
    ]

    consequence_panels_metrics: list[dict[str, Any]] = []
    threshold_half_width = max(x_limit_abs * 0.006, 0.015)
    threshold_half_height = max(y_limit_top * 0.008, 0.04)
    horizontal_threshold_inset = max(x_limit_abs * 0.015, 0.03)
    point_half_width = max(x_limit_abs * 0.03, 0.05)
    point_half_height = max(y_limit_top * 0.035, 0.08)

    def _clip_box_to_panel(
        box: dict[str, Any],
        *,
        panel_box: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            **box,
            "x0": max(float(box["x0"]), float(panel_box["x0"])),
            "y0": max(float(box["y0"]), float(panel_box["y0"])),
            "x1": min(float(box["x1"]), float(panel_box["x1"])),
            "y1": min(float(box["y1"]), float(panel_box["y1"])),
        }

    for index, (record, panel_label_artist) in enumerate(zip(consequence_records, consequence_panel_label_artists, strict=True), start=1):
        axes_item = record["axes"]
        panel_label_token = chr(ord("A") + index)
        panel_token = chr(ord("A") + index - 1)
        panel_box_id = f"panel_consequence_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        panel_title_box_id = f"consequence_title_{panel_token}"
        panel_label_box_id = f"panel_label_{panel_label_token}"
        x_axis_title_box_id = f"consequence_x_axis_title_{panel_token}"
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
        threshold_left_box_id = f"{record['panel_id']}_threshold_left"
        threshold_right_box_id = f"{record['panel_id']}_threshold_right"
        threshold_significance_box_id = f"{record['panel_id']}_significance_threshold"
        guide_boxes.extend(
            [
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=-effect_threshold - threshold_half_width,
                        y0=0.0,
                        x1=-effect_threshold + threshold_half_width,
                        y1=y_limit_top,
                        box_id=threshold_left_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=effect_threshold - threshold_half_width,
                        y0=0.0,
                        x1=effect_threshold + threshold_half_width,
                        y1=y_limit_top,
                        box_id=threshold_right_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=-x_limit_abs + horizontal_threshold_inset,
                        y0=significance_threshold - threshold_half_height,
                        x1=x_limit_abs - horizontal_threshold_inset,
                        y1=significance_threshold + threshold_half_height,
                        box_id=threshold_significance_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
            ]
        )

        label_box_lookup: dict[str, str] = {}
        for label_item in record["label_artists"]:
            label_box_id = str(label_item["box_id"])
            label_box_lookup[str(label_item["gene_label"])] = label_box_id
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_item["artist"].get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="annotation_label",
                )
            )

        normalized_points: list[dict[str, Any]] = []
        for point in record["points"]:
            gene_label = str(point["gene_label"])
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            point_box_id = str(point["point_box_id"])
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=effect_value - point_half_width,
                    y0=significance_value - point_half_height,
                    x1=effect_value + point_half_width,
                    y1=significance_value + point_half_height,
                    box_id=point_box_id,
                    box_type="scatter_point",
                )
            )
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=effect_value,
                y=significance_value,
            )
            normalized_points.append(
                {
                    "gene_label": gene_label,
                    "x": point_x,
                    "y": point_y,
                    "effect_value": effect_value,
                    "significance_value": significance_value,
                    "regulation_class": str(point["regulation_class"]),
                    "point_box_id": point_box_id,
                    "label_box_id": label_box_lookup[gene_label],
                }
            )

        consequence_panels_metrics.append(
            {
                "panel_id": str(record["panel_id"]),
                "panel_title": panel_title_lookup[str(record["panel_id"])],
                "panel_label": panel_label_token,
                "panel_box_id": panel_box_id,
                "panel_label_box_id": panel_label_box_id,
                "panel_title_box_id": panel_title_box_id,
                "x_axis_title_box_id": x_axis_title_box_id,
                "effect_threshold_left_box_id": threshold_left_box_id,
                "effect_threshold_right_box_id": threshold_right_box_id,
                "significance_threshold_box_id": threshold_significance_box_id,
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
            "guide_boxes": guide_boxes,
            "metrics": {
                "alteration_legend_title": str(display_payload.get("alteration_legend_title") or "").strip(),
                "consequence_legend_title": str(display_payload.get("consequence_legend_title") or "").strip(),
                "effect_threshold": effect_threshold,
                "significance_threshold": significance_threshold,
                "sample_ids": sample_ids,
                "gene_labels": gene_labels,
                "driver_gene_labels": driver_gene_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "gene_alteration_frequencies": gene_frequency_metrics,
                "alteration_cells": alteration_cells_metrics,
                "consequence_panels": consequence_panels_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_genomic_alteration_pathway_integrated_composite_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    gene_order = list(display_payload.get("gene_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    alteration_records = list(display_payload.get("alteration_records") or [])
    driver_gene_order = list(display_payload.get("driver_gene_order") or [])
    consequence_panel_order = list(display_payload.get("consequence_panel_order") or [])
    consequence_points = list(display_payload.get("consequence_points") or [])
    pathway_order = list(display_payload.get("pathway_order") or [])
    pathway_panel_order = list(display_payload.get("pathway_panel_order") or [])
    pathway_points = list(display_payload.get("pathway_points") or [])
    if (
        not gene_order
        or not sample_order
        or not annotation_tracks
        or not alteration_records
        or not driver_gene_order
        or not consequence_panel_order
        or not consequence_points
        or not pathway_order
        or not pathway_panel_order
        or not pathway_points
    ):
        raise RuntimeError(
            f"{template_id} requires non-empty gene_order, sample_order, annotation_tracks, alteration_records, "
            "driver_gene_order, consequence_panel_order, consequence_points, pathway_order, pathway_panel_order, and pathway_points"
        )

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

    primary_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    secondary_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#f7ebeb").strip() or "#f7ebeb"
    background_color = str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1"

    gene_labels = [str(item["label"]) for item in gene_order]
    driver_gene_labels = [str(item["label"]) for item in driver_gene_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    pathway_labels = [str(item["label"]) for item in pathway_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    gene_index = {gene_label: index for index, gene_label in enumerate(gene_labels)}
    pathway_index = {pathway_label: index for index, pathway_label in enumerate(pathway_labels)}

    alteration_lookup = {
        (str(item["sample_id"]), str(item["gene_label"])): {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "mutation_class": str(item.get("mutation_class") or "").strip(),
            "cnv_state": str(item.get("cnv_state") or "").strip(),
        }
        for item in alteration_records
    }
    burden_counts = {
        sample_id: sum(1 for gene_label in gene_labels if (sample_id, gene_label) in alteration_lookup)
        for sample_id in sample_ids
    }
    gene_altered_counts = {
        gene_label: sum(1 for sample_id in sample_ids if (sample_id, gene_label) in alteration_lookup)
        for gene_label in gene_labels
    }
    gene_altered_fractions = {
        gene_label: gene_altered_counts[gene_label] / float(len(sample_ids))
        for gene_label in gene_labels
    }

    mutation_color_map = {
        "missense": primary_color,
        "truncating": "#8b3a3a",
        "fusion": "#475569",
    }
    cnv_color_map = {
        "amplification": secondary_color,
        "gain": "#d97706",
        "loss": "#0f766e",
        "deep_loss": "#111827",
    }
    alteration_label_map = {
        "missense": "Missense",
        "truncating": "Truncating",
        "fusion": "Fusion",
        "amplification": "Amplification",
        "gain": "Gain",
        "loss": "Loss",
        "deep_loss": "Deep loss",
    }
    track_palette_cycle = (
        primary_soft,
        secondary_soft,
        contrast_soft,
        "#eef2ff",
        "#f8fafc",
        "#ecfccb",
    )
    track_fill_by_id: dict[str, dict[str, str]] = {}
    for track in annotation_tracks:
        category_labels = [str(item["category_label"]) for item in track["values"]]
        ordered_categories = list(dict.fromkeys(category_labels))
        track_fill_by_id[str(track["track_id"])] = {
            category_label: track_palette_cycle[index % len(track_palette_cycle)]
            for index, category_label in enumerate(ordered_categories)
        }

    consequence_panel_ids = [str(item["panel_id"]) for item in consequence_panel_order]
    consequence_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in consequence_panel_order}
    consequence_point_lookup: dict[str, list[dict[str, Any]]] = {panel_id: [] for panel_id in consequence_panel_ids}
    for point in consequence_points:
        consequence_point_lookup[str(point["panel_id"])].append(point)

    pathway_panel_ids = [str(item["panel_id"]) for item in pathway_panel_order]
    pathway_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in pathway_panel_order}
    pathway_point_lookup: dict[str, list[dict[str, Any]]] = {panel_id: [] for panel_id in pathway_panel_ids}
    for point in pathway_points:
        pathway_point_lookup[str(point["panel_id"])].append(point)

    effect_threshold = float(display_payload.get("effect_threshold") or 0.0)
    significance_threshold = float(display_payload.get("significance_threshold") or 0.0)
    all_effect_values = [float(item["effect_value"]) for item in consequence_points]
    all_significance_values = [float(item["significance_value"]) for item in consequence_points]
    x_limit_core = max(max(abs(value) for value in all_effect_values), effect_threshold, 1e-6)
    x_padding = max(x_limit_core * 0.18, 0.20)
    x_limit_abs = x_limit_core + x_padding
    y_limit_top = max(max(all_significance_values), significance_threshold) * 1.12 + 0.25
    y_limit_top = max(y_limit_top, significance_threshold + 0.50)

    pathway_x_values = [float(item["x_value"]) for item in pathway_points]
    pathway_effect_values = [float(item["effect_value"]) for item in pathway_points]
    pathway_size_values = [float(item["size_value"]) for item in pathway_points]
    pathway_x_min = min(pathway_x_values)
    pathway_x_max = max(pathway_x_values)
    pathway_x_span = max(pathway_x_max - pathway_x_min, 1e-6)
    pathway_x_padding = max(pathway_x_span * 0.08, 0.12)
    pathway_size_min = min(pathway_size_values)
    pathway_size_max = max(pathway_size_values)
    pathway_max_abs_effect = max(max(abs(value) for value in pathway_effect_values), 1e-6)
    if any(value < 0.0 for value in pathway_effect_values) and any(value > 0.0 for value in pathway_effect_values):
        pathway_color_norm: matplotlib.colors.Normalize = matplotlib.colors.TwoSlopeNorm(
            vmin=-pathway_max_abs_effect,
            vcenter=0.0,
            vmax=pathway_max_abs_effect,
        )
    else:
        min_effect = min(pathway_effect_values)
        max_effect = max(pathway_effect_values)
        if math.isclose(min_effect, max_effect, rel_tol=1e-9, abs_tol=1e-9):
            min_effect -= 1.0
            max_effect += 1.0
        pathway_color_norm = matplotlib.colors.Normalize(vmin=min_effect, vmax=max_effect)
    pathway_effect_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "pathway_integrated_composite",
        [primary_color, "#f8fafc", secondary_color],
    )

    def _pathway_marker_size(size_value: float) -> float:
        if math.isclose(pathway_size_min, pathway_size_max, rel_tol=1e-9, abs_tol=1e-9):
            return 200.0
        normalized = (size_value - pathway_size_min) / (pathway_size_max - pathway_size_min)
        return 110.0 + normalized * 250.0

    figure_width = max(13.4, 0.52 * len(sample_ids) + 8.8)
    figure_height = max(9.2, 0.62 * len(gene_labels) + 5.1)
    fig = plt.figure(figsize=(figure_width, figure_height))
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.92,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
            y=0.985,
        )

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        3,
        left=0.17,
        right=0.96,
        bottom=0.22,
        top=top_margin,
        width_ratios=(
            max(3.8, 0.60 * len(sample_ids) + 0.8),
            1.45,
            max(2.7, 2.0 + 0.32 * len(driver_gene_labels)),
        ),
        height_ratios=(1.10, max(0.90, 0.52 * len(annotation_tracks)), max(3.0, 0.72 * len(gene_labels))),
        hspace=0.10,
        wspace=0.16,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)
    right_grid = grid[:, 2].subgridspec(2, 1, hspace=0.16, height_ratios=(1.75, 1.15))
    consequence_grid = right_grid[0].subgridspec(len(consequence_panel_ids), 1, hspace=0.26)
    pathway_grid = right_grid[1].subgridspec(len(pathway_panel_ids), 1, hspace=0.20)
    consequence_axes_list = [fig.add_subplot(consequence_grid[index, 0]) for index in range(len(consequence_panel_ids))]
    pathway_axes_list = [fig.add_subplot(pathway_grid[index, 0]) for index in range(len(pathway_panel_ids))]

    burden_positions = list(range(len(sample_ids)))
    burden_values = [burden_counts[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(gene_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(
        sample_ids,
        rotation=45,
        ha="right",
        fontsize=max(tick_size - 0.3, 8.6),
        color=neutral_color,
    )
    matrix_axes.set_yticks(range(len(gene_labels)))
    matrix_axes.set_yticklabels(gene_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(max(gene_altered_fractions.values()), 1e-6)
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(gene_labels)))
    frequency_values = [gene_altered_fractions[gene_label] for gene_label in gene_labels]
    frequency_bars = frequency_axes.barh(
        frequency_positions,
        frequency_values,
        height=0.74,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.set_xlim(0.0, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(gene_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    alteration_cell_patches: list[dict[str, Any]] = []
    alteration_overlay_patches: list[dict[str, Any]] = []
    for gene_label in gene_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = gene_index[gene_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor="#ffffff",
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            alteration = alteration_lookup.get((sample_id, gene_label))
            if alteration is None:
                continue
            mutation_class = str(alteration.get("mutation_class") or "").strip()
            cnv_state = str(alteration.get("cnv_state") or "").strip()
            cell_color = cnv_color_map[cnv_state] if cnv_state else mutation_color_map[mutation_class]
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=cell_color,
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            box_id = f"alteration_{gene_label}_{sample_id}"
            overlay_box_id = ""
            if mutation_class and cnv_state:
                overlay_patch = matplotlib.patches.Rectangle(
                    (x_index - 0.21, y_index - 0.32),
                    0.42,
                    0.64,
                    facecolor=mutation_color_map[mutation_class],
                    edgecolor="white",
                    linewidth=0.8,
                    zorder=4,
                )
                matrix_axes.add_patch(overlay_patch)
                overlay_box_id = f"overlay_{gene_label}_{sample_id}"
                alteration_overlay_patches.append({"box_id": overlay_box_id, "patch": overlay_patch})
            alteration_cell_patches.append(
                {
                    "box_id": box_id,
                    "patch": patch,
                    "sample_id": sample_id,
                    "gene_label": gene_label,
                    "mutation_class": mutation_class,
                    "cnv_state": cnv_state,
                    "overlay_box_id": overlay_box_id,
                }
            )

    consequence_records: list[dict[str, Any]] = []
    for axes_item, panel_id in zip(consequence_axes_list, consequence_panel_ids, strict=True):
        panel_points = list(consequence_point_lookup.get(panel_id) or [])
        scatter_color_lookup = {
            "upregulated": secondary_color,
            "downregulated": primary_color,
            "background": background_color,
        }
        axes_item.scatter(
            [float(item["effect_value"]) for item in panel_points],
            [float(item["significance_value"]) for item in panel_points],
            s=72.0,
            c=[scatter_color_lookup[str(item["regulation_class"])] for item in panel_points],
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        axes_item.axvline(-effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axvline(effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axhline(significance_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit_abs, x_limit_abs)
        axes_item.set_ylim(0.0, y_limit_top)
        axes_item.set_xlabel(
            str(display_payload.get("consequence_x_label") or "").strip(),
            fontsize=max(axis_title_size - 0.1, 10.0),
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_ylabel("")
        axes_item.set_title(
            consequence_title_lookup[panel_id],
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=9.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
        axes_item.tick_params(axis="y", labelsize=tick_size, colors=neutral_color)
        axes_item.grid(axis="both", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        _apply_publication_axes_style(axes_item)

        point_artists: list[dict[str, Any]] = []
        label_artists: list[dict[str, Any]] = []
        for point in panel_points:
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            gene_label = str(point["gene_label"])
            point_box_id = f"consequence_point_{panel_id}_{gene_label}"
            point_artists.append(
                {
                    "point_box_id": point_box_id,
                    "gene_label": gene_label,
                    "effect_value": effect_value,
                    "significance_value": significance_value,
                    "regulation_class": str(point["regulation_class"]),
                }
            )
            offset_x = -8 if effect_value >= 0.0 else 8
            ha = "right" if effect_value >= 0.0 else "left"
            place_label_below = significance_value >= y_limit_top * 0.82
            label_artist = axes_item.annotate(
                gene_label,
                xy=(effect_value, significance_value),
                xytext=(offset_x, -6 if place_label_below else 6),
                textcoords="offset points",
                fontsize=max(tick_size - 0.6, 8.2),
                color=neutral_color,
                ha=ha,
                va="top" if place_label_below else "bottom",
                zorder=4,
                annotation_clip=True,
            )
            label_artists.append(
                {
                    "gene_label": gene_label,
                    "box_id": f"consequence_label_{panel_id}_{gene_label}",
                    "artist": label_artist,
                }
            )
        consequence_records.append(
            {
                "panel_id": panel_id,
                "axes": axes_item,
                "points": point_artists,
                "label_artists": label_artists,
            }
        )

    scatter_artist = None
    pathway_records: list[dict[str, Any]] = []
    y_positions = list(range(len(pathway_labels)))
    for axes_item, panel_id in zip(pathway_axes_list, pathway_panel_ids, strict=True):
        panel_points = list(pathway_point_lookup.get(panel_id) or [])
        scatter_artist = axes_item.scatter(
            [float(item["x_value"]) for item in panel_points],
            [pathway_index[str(item["pathway_label"])] for item in panel_points],
            s=[_pathway_marker_size(float(item["size_value"])) for item in panel_points],
            c=[float(item["effect_value"]) for item in panel_points],
            cmap=pathway_effect_cmap,
            norm=pathway_color_norm,
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        if pathway_x_min < 0.0 < pathway_x_max:
            axes_item.axvline(0.0, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(pathway_x_min - pathway_x_padding, pathway_x_max + pathway_x_padding)
        axes_item.set_ylim(-0.5, len(pathway_labels) - 0.5)
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(pathway_labels, fontsize=max(tick_size - 0.2, 8.2), color=neutral_color)
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(display_payload.get("pathway_x_label") or "").strip(),
            fontsize=max(axis_title_size - 0.2, 9.8),
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_ylabel("")
        axes_item.set_title(
            pathway_title_lookup[panel_id],
            fontsize=max(axis_title_size - 0.1, 10.0),
            fontweight="bold",
            color=neutral_color,
            pad=8.0,
        )
        axes_item.tick_params(axis="x", labelsize=max(tick_size - 0.2, 8.2), colors=neutral_color)
        axes_item.tick_params(axis="y", length=0, colors=neutral_color)
        axes_item.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)
        pathway_records.append({"panel_id": panel_id, "axes": axes_item, "points": panel_points})

    alteration_legend_handles = [
        matplotlib.patches.Patch(facecolor=mutation_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("missense", "truncating", "fusion")
    ] + [
        matplotlib.patches.Patch(facecolor=cnv_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("amplification", "gain", "loss", "deep_loss")
    ]
    alteration_legend = fig.legend(
        handles=alteration_legend_handles,
        labels=[handle.get_label() for handle in alteration_legend_handles],
        title=str(display_payload.get("alteration_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.32, 0.03),
        ncol=4,
        frameon=False,
        fontsize=max(tick_size - 1.0, 8.0),
        title_fontsize=max(tick_size - 0.4, 8.6),
        columnspacing=1.2,
    )
    consequence_legend_handles = [
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=secondary_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Upregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=primary_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Downregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=background_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Background",
        ),
    ]
    consequence_legend = fig.legend(
        consequence_legend_handles,
        [str(handle.get_label()) for handle in consequence_legend_handles],
        title=str(display_payload.get("consequence_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.72, 0.03),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.9, 8.0),
        title_fontsize=max(tick_size - 0.4, 8.6),
        columnspacing=1.1,
    )
    pathway_legend_values = sorted(
        {
            round(pathway_size_min, 2),
            round((pathway_size_min + pathway_size_max) / 2.0, 2),
            round(pathway_size_max, 2),
        }
    )
    pathway_legend_handles = [
        plt.scatter([], [], s=_pathway_marker_size(float(value)), color="#94a3b8", edgecolors="white", linewidths=0.8)
        for value in pathway_legend_values
    ]
    pathway_legend = fig.legend(
        pathway_legend_handles,
        [f"{value:g}" for value in pathway_legend_values],
        title=str(display_payload.get("pathway_size_scale_label") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.90, 0.03),
        ncol=len(pathway_legend_handles),
        frameon=False,
        fontsize=max(tick_size - 1.0, 7.8),
        title_fontsize=max(tick_size - 0.5, 8.4),
        columnspacing=0.9,
    )
    fig.add_artist(alteration_legend)
    fig.add_artist(consequence_legend)
    if scatter_artist is None:
        raise RuntimeError(f"{template_id} failed to render pathway scatter artist")
    colorbar = fig.colorbar(scatter_artist, ax=pathway_axes_list, fraction=0.050, pad=0.03)
    colorbar.set_label(
        str(display_payload.get("pathway_effect_scale_label") or "").strip(),
        fontsize=max(axis_title_size - 0.4, 9.6),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.4), colors=neutral_color)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, _ = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    _, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, _ = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

    pathway_y_axis_title_artist = fig.text(
        0.64,
        0.31,
        str(display_payload.get("pathway_y_label") or "").strip(),
        rotation=90,
        fontsize=max(axis_title_size - 0.2, 9.6),
        fontweight="bold",
        color=neutral_color,
        ha="center",
        va="center",
    )

    def _make_panel_label_artist(axes_item: Any, label_token: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.055, 0.016), 0.030)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label_token,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.4, 13.0),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    consequence_panel_label_artists = [
        _make_panel_label_artist(axes_item, chr(ord("B") + index))
        for index, axes_item in enumerate(consequence_axes_list)
    ]
    pathway_panel_label_artists = [
        _make_panel_label_artist(axes_item, chr(ord("E") + index))
        for index, axes_item in enumerate(pathway_axes_list)
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
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=pathway_y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="pathway_y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {
                "sample_id": sample_id,
                "altered_gene_count": int(burden_counts[sample_id]),
                "bar_box_id": box_id,
            }
        )

    gene_frequency_metrics: list[dict[str, Any]] = []
    for gene_label, bar in zip(gene_labels, frequency_bars, strict=True):
        box_id = f"freq_bar_{gene_label}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        gene_frequency_metrics.append(
            {
                "gene_label": gene_label,
                "altered_fraction": float(gene_altered_fractions[gene_label]),
                "bar_box_id": box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    overlay_box_id_by_alteration_id: dict[str, str] = {}
    for item in alteration_overlay_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_overlay",
            )
        )
        overlay_box_id_by_alteration_id[str(item["box_id"])] = str(item["box_id"])

    alteration_cells_metrics: list[dict[str, Any]] = []
    for item in alteration_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_cell",
            )
        )
        metric_item: dict[str, Any] = {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "box_id": str(item["box_id"]),
        }
        mutation_class = str(item["mutation_class"])
        cnv_state = str(item["cnv_state"])
        if mutation_class:
            metric_item["mutation_class"] = mutation_class
        if cnv_state:
            metric_item["cnv_state"] = cnv_state
        overlay_box_id = str(item["overlay_box_id"])
        if overlay_box_id:
            metric_item["overlay_box_id"] = overlay_box_id_by_alteration_id[overlay_box_id]
        alteration_cells_metrics.append(metric_item)

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=alteration_legend.get_window_extent(renderer=renderer),
            box_id="legend_alteration",
            box_type="legend",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=consequence_legend.get_window_extent(renderer=renderer),
            box_id="legend_consequence",
            box_type="legend",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=pathway_legend.get_window_extent(renderer=renderer),
            box_id="legend_pathway",
            box_type="legend",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar_pathway",
            box_type="colorbar",
        ),
    ]

    threshold_half_width = max(x_limit_abs * 0.006, 0.015)
    threshold_half_height = max(y_limit_top * 0.008, 0.04)
    horizontal_threshold_inset = max(x_limit_abs * 0.015, 0.03)
    point_half_width = max(x_limit_abs * 0.03, 0.05)
    point_half_height = max(y_limit_top * 0.035, 0.08)
    pathway_point_half_width = max((pathway_x_max - pathway_x_min + 2 * pathway_x_padding) * 0.025, 0.05)
    pathway_point_half_height = max(len(pathway_labels) * 0.018, 0.08)

    def _clip_box_to_panel(
        box: dict[str, Any],
        *,
        panel_box: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            **box,
            "x0": max(float(box["x0"]), float(panel_box["x0"])),
            "y0": max(float(box["y0"]), float(panel_box["y0"])),
            "x1": min(float(box["x1"]), float(panel_box["x1"])),
            "y1": min(float(box["y1"]), float(panel_box["y1"])),
        }

    consequence_panels_metrics: list[dict[str, Any]] = []
    for index, (record, panel_label_artist) in enumerate(zip(consequence_records, consequence_panel_label_artists, strict=True), start=1):
        axes_item = record["axes"]
        panel_label_token = chr(ord("A") + index)
        panel_token = chr(ord("A") + index - 1)
        panel_box_id = f"panel_consequence_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        panel_title_box_id = f"consequence_title_{panel_token}"
        panel_label_box_id = f"panel_label_{panel_label_token}"
        x_axis_title_box_id = f"consequence_x_axis_title_{panel_token}"
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
        threshold_left_box_id = f"{record['panel_id']}_threshold_left"
        threshold_right_box_id = f"{record['panel_id']}_threshold_right"
        threshold_significance_box_id = f"{record['panel_id']}_significance_threshold"
        guide_boxes.extend(
            [
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=-effect_threshold - threshold_half_width,
                        y0=0.0,
                        x1=-effect_threshold + threshold_half_width,
                        y1=y_limit_top,
                        box_id=threshold_left_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=effect_threshold - threshold_half_width,
                        y0=0.0,
                        x1=effect_threshold + threshold_half_width,
                        y1=y_limit_top,
                        box_id=threshold_right_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=-x_limit_abs + horizontal_threshold_inset,
                        y0=significance_threshold - threshold_half_height,
                        x1=x_limit_abs - horizontal_threshold_inset,
                        y1=significance_threshold + threshold_half_height,
                        box_id=threshold_significance_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
            ]
        )

        label_box_lookup: dict[str, str] = {}
        for label_item in record["label_artists"]:
            label_box_id = str(label_item["box_id"])
            label_box_lookup[str(label_item["gene_label"])] = label_box_id
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_item["artist"].get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="annotation_label",
                )
            )

        normalized_points: list[dict[str, Any]] = []
        for point in record["points"]:
            gene_label = str(point["gene_label"])
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            point_box_id = str(point["point_box_id"])
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=effect_value - point_half_width,
                    y0=significance_value - point_half_height,
                    x1=effect_value + point_half_width,
                    y1=significance_value + point_half_height,
                    box_id=point_box_id,
                    box_type="scatter_point",
                )
            )
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=effect_value,
                y=significance_value,
            )
            normalized_points.append(
                {
                    "gene_label": gene_label,
                    "x": point_x,
                    "y": point_y,
                    "effect_value": effect_value,
                    "significance_value": significance_value,
                    "regulation_class": str(point["regulation_class"]),
                    "point_box_id": point_box_id,
                    "label_box_id": label_box_lookup[gene_label],
                }
            )

        consequence_panels_metrics.append(
            {
                "panel_id": str(record["panel_id"]),
                "panel_title": consequence_title_lookup[str(record["panel_id"])],
                "panel_label": panel_label_token,
                "panel_box_id": panel_box_id,
                "panel_label_box_id": panel_label_box_id,
                "panel_title_box_id": panel_title_box_id,
                "x_axis_title_box_id": x_axis_title_box_id,
                "effect_threshold_left_box_id": threshold_left_box_id,
                "effect_threshold_right_box_id": threshold_right_box_id,
                "significance_threshold_box_id": threshold_significance_box_id,
                "points": normalized_points,
            }
        )

    pathway_panels_metrics: list[dict[str, Any]] = []
    for index, (record, panel_label_artist) in enumerate(zip(pathway_records, pathway_panel_label_artists, strict=True), start=1):
        axes_item = record["axes"]
        panel_label_token = chr(ord("D") + index)
        panel_token = chr(ord("A") + index - 1)
        panel_box_id = f"panel_pathway_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        panel_title_box_id = f"pathway_title_{panel_token}"
        panel_label_box_id = f"panel_label_{panel_label_token}"
        x_axis_title_box_id = f"pathway_x_axis_title_{panel_token}"
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
            pathway_label = str(point["pathway_label"])
            x_value = float(point["x_value"])
            y_value = float(pathway_index[pathway_label])
            point_box_id = f"pathway_point_{record['panel_id']}_{pathway_label}"
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=x_value - pathway_point_half_width,
                    y0=y_value - pathway_point_half_height,
                    x1=x_value + pathway_point_half_width,
                    y1=y_value + pathway_point_half_height,
                    box_id=point_box_id,
                    box_type="scatter_point",
                )
            )
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=x_value,
                y=y_value,
            )
            normalized_points.append(
                {
                    "pathway_label": pathway_label,
                    "x": point_x,
                    "y": point_y,
                    "x_value": x_value,
                    "effect_value": float(point["effect_value"]),
                    "size_value": float(point["size_value"]),
                    "point_box_id": point_box_id,
                }
            )

        pathway_panels_metrics.append(
            {
                "panel_id": str(record["panel_id"]),
                "panel_title": pathway_title_lookup[str(record["panel_id"])],
                "panel_label": panel_label_token,
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
            "guide_boxes": guide_boxes,
            "metrics": {
                "alteration_legend_title": str(display_payload.get("alteration_legend_title") or "").strip(),
                "consequence_legend_title": str(display_payload.get("consequence_legend_title") or "").strip(),
                "pathway_effect_scale_label": str(display_payload.get("pathway_effect_scale_label") or "").strip(),
                "pathway_size_scale_label": str(display_payload.get("pathway_size_scale_label") or "").strip(),
                "effect_threshold": effect_threshold,
                "significance_threshold": significance_threshold,
                "sample_ids": sample_ids,
                "gene_labels": gene_labels,
                "driver_gene_labels": driver_gene_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "gene_alteration_frequencies": gene_frequency_metrics,
                "alteration_cells": alteration_cells_metrics,
                "consequence_panels": consequence_panels_metrics,
                "pathway_labels": pathway_labels,
                "pathway_panels": pathway_panels_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_genomic_program_governance_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    programs = list(display_payload.get("programs") or [])
    layer_order = list(display_payload.get("layer_order") or [])
    if not programs or not layer_order:
        raise RuntimeError(f"{template_id} requires non-empty programs and layer_order")

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

    primary_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    secondary_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    light_fill = str(palette.get("light") or "#f8fafc").strip() or "#f8fafc"
    primary_soft = str(palette.get("primary_soft") or "#eff6ff").strip() or "#eff6ff"
    summary_fill = str(palette.get("secondary_soft") or "#e2e8f0").strip() or "#e2e8f0"
    audit_color = str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed"
    neutral_text = "#334155"

    layer_ids = [str(item["layer_id"]) for item in layer_order]
    layer_labels = [str(item["layer_label"]) for item in layer_order]
    layer_index = {layer_id: index for index, layer_id in enumerate(layer_ids)}

    all_effect_values = [
        float(layer_support["effect_value"])
        for program in programs
        for layer_support in list(program.get("layer_supports") or [])
    ]
    all_support_values = [
        float(layer_support["support_fraction"])
        for program in programs
        for layer_support in list(program.get("layer_supports") or [])
    ]
    max_abs_effect = max(max(abs(value) for value in all_effect_values), 1e-6)
    if any(value < 0.0 for value in all_effect_values) and any(value > 0.0 for value in all_effect_values):
        effect_norm: matplotlib.colors.Normalize = matplotlib.colors.TwoSlopeNorm(
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
        effect_norm = matplotlib.colors.Normalize(vmin=min_effect, vmax=max_effect)
    effect_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "genomic_program_governance",
        [primary_color, "#f8fafc", secondary_color],
    )
    support_min = min(all_support_values)
    support_max = max(all_support_values)

    def _support_marker_size(support_fraction: float) -> float:
        if math.isclose(support_min, support_max, rel_tol=1e-9, abs_tol=1e-9):
            return 190.0
        normalized = (support_fraction - support_min) / (support_max - support_min)
        return 105.0 + normalized * 255.0

    row_count = len(programs)
    figure_height = max(5.4, 1.00 * row_count + 2.4)
    fig, (evidence_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(11.6, figure_height),
        gridspec_kw={"width_ratios": [1.48, 1.02]},
    )
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
            color=neutral_text,
            y=0.985,
        )

    evidence_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("evidence_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.24,
        font_size=axis_title_size,
        font_weight="bold",
    )
    evidence_axes.set_title(
        "\n".join(evidence_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_text,
        pad=12.0,
    )
    evidence_axes.set_xlim(-0.6, len(layer_labels) - 0.4)
    evidence_axes.set_ylim(-0.6, row_count - 0.4)
    evidence_axes.invert_yaxis()
    evidence_axes.set_xticks(range(len(layer_labels)))
    evidence_axes.set_xticklabels(
        layer_labels,
        rotation=18,
        ha="right",
        fontsize=max(tick_size - 0.4, 8.4),
        color=neutral_text,
    )
    evidence_axes.set_yticks([])
    evidence_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.4), colors=neutral_text)
    evidence_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    evidence_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.6, zorder=0)
    _apply_publication_axes_style(evidence_axes)

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_text,
        pad=12.0,
    )
    summary_axes.set_xlim(0.0, 1.0)
    summary_axes.set_ylim(-0.6, row_count - 0.4)
    summary_axes.invert_yaxis()
    summary_axes.set_xticks([])
    summary_axes.set_yticks([])
    for spine in summary_axes.spines.values():
        spine.set_visible(False)
    summary_axes.set_facecolor("white")

    blended_transform = matplotlib.transforms.blended_transform_factory(evidence_axes.transAxes, evidence_axes.transData)
    row_label_artists: list[Any] = []
    priority_artists: list[Any] = []
    verdict_artists: list[Any] = []
    support_artists: list[Any] = []
    action_artists: list[Any] = []
    detail_artists: list[Any | None] = []
    normalized_programs_for_sidecar: list[dict[str, Any]] = []

    priority_color_lookup = {
        "high_priority": secondary_color,
        "monitor": audit_color,
        "watchlist": reference_color,
    }
    verdict_color_lookup = {
        "convergent": secondary_color,
        "layer_specific": audit_color,
        "context_dependent": reference_color,
        "insufficient_support": "#7f1d1d",
    }

    scatter_x: list[float] = []
    scatter_y: list[float] = []
    scatter_sizes: list[float] = []
    scatter_colors: list[float] = []
    scatter_records: list[tuple[int, str, float, float]] = []

    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18
    for row_index, program in enumerate(programs):
        y_center = float(row_index)
        row_label_artists.append(
            evidence_axes.text(
                -0.03,
                y_center,
                str(program["program_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.1, 8.7),
                color=neutral_text,
                clip_on=False,
            )
        )
        for layer_support in list(program.get("layer_supports") or []):
            layer_id = str(layer_support["layer_id"])
            effect_value = float(layer_support["effect_value"])
            support_fraction = float(layer_support["support_fraction"])
            scatter_x.append(float(layer_index[layer_id]))
            scatter_y.append(y_center)
            scatter_sizes.append(_support_marker_size(support_fraction))
            scatter_colors.append(effect_value)
            scatter_records.append((row_index, layer_id, effect_value, support_fraction))

        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.04, y_center - 0.36),
            0.92,
            0.72,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            transform=summary_axes.transData,
            facecolor=primary_soft if row_index % 2 == 0 else light_fill,
            edgecolor=summary_fill,
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        priority_artist = summary_axes.text(
            0.08,
            y_center - 0.19,
            str(program["priority_band"]).replace("_", " ").title(),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 1.1, 7.8),
            fontweight="bold",
            color="white",
            bbox={
                "boxstyle": "round,pad=0.28,rounding_size=0.14",
                "facecolor": priority_color_lookup.get(str(program["priority_band"]), reference_color),
                "edgecolor": "none",
            },
            zorder=2,
        )
        verdict_artist = summary_axes.text(
            0.43,
            y_center - 0.19,
            str(program["verdict"]).replace("_", " "),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 0.6, 8.4),
            fontweight="bold",
            color=verdict_color_lookup.get(str(program["verdict"]), neutral_text),
            zorder=2,
        )
        support_artist = summary_axes.text(
            0.08,
            y_center + 0.01,
            f"{program['lead_driver_label']} | {program['dominant_pathway_label']} | "
            f"h={int(program['pathway_hit_count'])} | r={int(program['priority_rank'])}",
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 1.0, 7.8),
            color=neutral_text,
            zorder=2,
        )
        action_lines = _wrap_flow_text_to_width(
            str(program["action"]),
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 0.9, 7.9),
            font_weight="bold",
        )
        action_artist = summary_axes.text(
            0.08,
            y_center + 0.23,
            "\n".join(action_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 0.9, 7.9),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        detail_text = str(program.get("detail") or "").strip()

        priority_artists.append(priority_artist)
        verdict_artists.append(verdict_artist)
        support_artists.append(support_artist)
        action_artists.append(action_artist)
        detail_artists.append(detail_artist)

        normalized_program = {
            "program_id": str(program["program_id"]),
            "program_label": str(program["program_label"]),
            "lead_driver_label": str(program["lead_driver_label"]),
            "dominant_pathway_label": str(program["dominant_pathway_label"]),
            "pathway_hit_count": int(program["pathway_hit_count"]),
            "priority_rank": int(program["priority_rank"]),
            "priority_band": str(program["priority_band"]),
            "verdict": str(program["verdict"]),
            "action": str(program["action"]),
        }
        if detail_text:
            normalized_program["detail"] = detail_text
        normalized_programs_for_sidecar.append(normalized_program)

    scatter_artist = evidence_axes.scatter(
        scatter_x,
        scatter_y,
        s=scatter_sizes,
        c=scatter_colors,
        cmap=effect_cmap,
        norm=effect_norm,
        alpha=0.94,
        edgecolors="white",
        linewidths=0.9,
        zorder=3,
    )

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.74, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.25, right=0.96, top=top_margin, bottom=0.20, wspace=0.18)

    support_legend_values = sorted(
        {
            round(support_min, 2),
            round((support_min + support_max) / 2.0, 2),
            round(support_max, 2),
        }
    )
    support_legend_handles = [
        plt.scatter([], [], s=_support_marker_size(float(value)), color="#94a3b8", edgecolors="white", linewidths=0.8)
        for value in support_legend_values
    ]
    support_legend = fig.legend(
        support_legend_handles,
        [f"{value:.2f}" for value in support_legend_values],
        title=str(display_payload.get("support_scale_label") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.28, 0.04),
        ncol=len(support_legend_handles),
        frameon=False,
        fontsize=max(tick_size - 1.0, 7.8),
        title_fontsize=max(tick_size - 0.4, 8.4),
        columnspacing=0.9,
    )
    fig.add_artist(support_legend)
    colorbar_axes = evidence_axes.inset_axes([0.94, 0.14, 0.028, 0.72])
    colorbar = fig.colorbar(scatter_artist, cax=colorbar_axes)
    colorbar.set_label(
        str(display_payload.get("effect_scale_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.6),
        color=neutral_text,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.7, 8.0), colors=neutral_text)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.026, 0.009), 0.017)
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

    panel_label_a = _add_panel_label(axes_item=evidence_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=summary_axes, label="B")
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
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=evidence_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_A",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=summary_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_B",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_b.get_window_extent(renderer=renderer),
                box_id="panel_label_B",
                box_type="panel_label",
            ),
        ]
    )
    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=evidence_axes.get_window_extent(renderer=renderer),
            box_id="panel_evidence",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="panel_summary",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_legend.get_window_extent(renderer=renderer),
            box_id="legend_support",
            box_type="legend",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar_effect",
            box_type="colorbar",
        ),
    ]

    evidence_box_width = 0.14
    evidence_box_height = 0.10
    scatter_record_index = 0
    for row_index, normalized_program in enumerate(normalized_programs_for_sidecar):
        row_label_box_id = f"row_label_{normalized_program['program_id']}"
        priority_box_id = f"priority_{normalized_program['program_id']}"
        verdict_box_id = f"verdict_{normalized_program['program_id']}"
        support_box_id = f"support_{normalized_program['program_id']}"
        action_box_id = f"action_{normalized_program['program_id']}"
        detail_box_id = ""
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=row_label_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=row_label_box_id,
                    box_type="row_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=priority_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=priority_box_id,
                    box_type="priority_badge",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=verdict_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=verdict_box_id,
                    box_type="verdict_value",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=support_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=support_box_id,
                    box_type="row_support",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=action_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=action_box_id,
                    box_type="row_action",
                ),
            ]
        )
        if detail_artists[row_index] is not None:
            detail_box_id = f"detail_{normalized_program['program_id']}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=detail_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="row_detail",
                )
            )

        normalized_program.update(
            {
                "row_label_box_id": row_label_box_id,
                "priority_box_id": priority_box_id,
                "verdict_box_id": verdict_box_id,
                "support_box_id": support_box_id,
                "action_box_id": action_box_id,
            }
        )
        if detail_box_id:
            normalized_program["detail_box_id"] = detail_box_id
        normalized_layer_supports: list[dict[str, Any]] = []
        for layer_id in layer_ids:
            record_row_index, record_layer_id, effect_value, support_fraction = scatter_records[scatter_record_index]
            assert record_row_index == row_index and record_layer_id == layer_id
            cell_box_id = f"evidence_{normalized_program['program_id']}_{layer_id}"
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=evidence_axes,
                    figure=fig,
                    x0=float(layer_index[layer_id]) - evidence_box_width / 2.0,
                    y0=float(row_index) - evidence_box_height / 2.0,
                    x1=float(layer_index[layer_id]) + evidence_box_width / 2.0,
                    y1=float(row_index) + evidence_box_height / 2.0,
                    box_id=cell_box_id,
                    box_type="evidence_cell",
                )
            )
            normalized_layer_supports.append(
                {
                    "layer_id": layer_id,
                    "effect_value": effect_value,
                    "support_fraction": support_fraction,
                    "cell_box_id": cell_box_id,
                }
            )
            scatter_record_index += 1
        normalized_program["layer_supports"] = normalized_layer_supports

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "effect_scale_label": str(display_payload.get("effect_scale_label") or "").strip(),
                "support_scale_label": str(display_payload.get("support_scale_label") or "").strip(),
                "layer_labels": layer_labels,
                "programs": normalized_programs_for_sidecar,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_omics_volcano_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panel_order = list(display_payload.get("panel_order") or [])
    points = list(display_payload.get("points") or [])
    if not panel_order or not points:
        raise RuntimeError(f"{template_id} requires non-empty panel_order and points")

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

    downregulated_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    upregulated_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    background_color = str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1"
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"

    panel_id_order = [str(item["panel_id"]) for item in panel_order]
    panel_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in panel_order}
    point_lookup: dict[str, list[dict[str, Any]]] = {panel_id: [] for panel_id in panel_id_order}
    for point in points:
        point_lookup[str(point["panel_id"])].append(point)

    effect_threshold = float(display_payload.get("effect_threshold") or 0.0)
    significance_threshold = float(display_payload.get("significance_threshold") or 0.0)
    all_effect_values = [float(item["effect_value"]) for item in points]
    all_significance_values = [float(item["significance_value"]) for item in points]
    x_limit_core = max(max(abs(value) for value in all_effect_values), effect_threshold, 1e-6)
    x_padding = max(x_limit_core * 0.18, 0.20)
    x_limit_abs = x_limit_core + x_padding
    y_limit_top = max(max(all_significance_values), significance_threshold) * 1.12 + 0.25
    y_limit_top = max(y_limit_top, significance_threshold + 0.50)

    figure_width = max(8.6, 4.2 * len(panel_id_order) + 1.4)
    fig, axes = plt.subplots(1, len(panel_id_order), figsize=(figure_width, 5.7), squeeze=False)
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

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel_id in zip(axes_list, panel_id_order, strict=True):
        panel_points = list(point_lookup.get(panel_id) or [])
        color_lookup = {
            "upregulated": upregulated_color,
            "downregulated": downregulated_color,
            "background": background_color,
        }
        scatter = axes_item.scatter(
            [float(item["effect_value"]) for item in panel_points],
            [float(item["significance_value"]) for item in panel_points],
            s=70.0,
            c=[color_lookup[str(item["regulation_class"])] for item in panel_points],
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        _ = scatter
        axes_item.axvline(-effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axvline(effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axhline(significance_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit_abs, x_limit_abs)
        axes_item.set_ylim(0.0, y_limit_top)
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_ylabel("")
        axes_item.set_title(
            panel_title_lookup[panel_id],
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
        axes_item.tick_params(axis="y", labelsize=tick_size, colors=neutral_color)
        axes_item.grid(axis="both", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        _apply_publication_axes_style(axes_item)

        annotation_artists: list[dict[str, Any]] = []
        for label_index, point in enumerate((item for item in panel_points if str(item.get("label_text") or "").strip())):
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            label_text = str(point.get("label_text") or "").strip()
            offset_x = -8 if effect_value >= 0.0 else 8
            ha = "right" if effect_value >= 0.0 else "left"
            artist = axes_item.annotate(
                label_text,
                xy=(effect_value, significance_value),
                xytext=(offset_x, 6),
                textcoords="offset points",
                fontsize=max(tick_size - 0.5, 8.2),
                color=neutral_color,
                ha=ha,
                va="bottom",
                zorder=4,
                annotation_clip=True,
            )
            annotation_artists.append(
                {
                    "box_id": f"label_{chr(ord('A') + len(panel_records))}_{label_index}",
                    "artist": artist,
                    "feature_label": str(point["feature_label"]),
                    "label_text": label_text,
                }
            )

        panel_records.append(
            {
                "panel_id": panel_id,
                "axes": axes_item,
                "points": panel_points,
                "annotation_artists": annotation_artists,
            }
        )

    top_margin = 0.84 if show_figure_title else 0.88
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.10, right=0.96, top=top_margin, bottom=0.22, wspace=0.24)

    y_axis_title_artist = fig.text(
        0.03,
        0.52,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        ha="center",
        va="center",
    )

    legend_handles = [
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=upregulated_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Upregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=downregulated_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Downregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=background_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Background",
        ),
    ]
    legend = fig.legend(
        legend_handles,
        [str(handle.get_label()) for handle in legend_handles],
        title=str(display_payload.get("legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.50, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.4),
        title_fontsize=max(tick_size - 0.4, 8.8),
        columnspacing=1.4,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.025, 0.008), 0.015)
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
    guide_boxes: list[dict[str, Any]] = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=legend.get_window_extent(renderer=renderer),
            box_id="legend",
            box_type="legend",
        )
    ]
    normalized_panels: list[dict[str, Any]] = []
    threshold_half_width = max(x_limit_abs * 0.006, 0.015)
    threshold_half_height = max(y_limit_top * 0.008, 0.04)
    horizontal_threshold_inset = max(x_limit_abs * 0.015, 0.03)

    for index, (record, panel_label_artist) in enumerate(zip(panel_records, panel_label_artists, strict=True), start=1):
        axes_item = record["axes"]
        panel_token = chr(ord("A") + index - 1)
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        panel_title_box_id = f"panel_title_{panel_token}"
        panel_label_box_id = f"panel_label_{panel_token}"
        x_axis_title_box_id = f"x_axis_title_{panel_token}"
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
        guide_boxes.extend(
            [
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=-effect_threshold - threshold_half_width,
                    y0=0.0,
                    x1=-effect_threshold + threshold_half_width,
                    y1=y_limit_top,
                    box_id=f"panel_{panel_token}_threshold_left",
                    box_type="reference_line",
                ),
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=effect_threshold - threshold_half_width,
                    y0=0.0,
                    x1=effect_threshold + threshold_half_width,
                    y1=y_limit_top,
                    box_id=f"panel_{panel_token}_threshold_right",
                    box_type="reference_line",
                ),
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=-x_limit_abs + horizontal_threshold_inset,
                    y0=significance_threshold - threshold_half_height,
                    x1=x_limit_abs - horizontal_threshold_inset,
                    y1=significance_threshold + threshold_half_height,
                    box_id=f"panel_{panel_token}_significance_threshold",
                    box_type="reference_line",
                ),
            ]
        )

        normalized_points: list[dict[str, Any]] = []
        label_box_lookup = {item["feature_label"]: item["box_id"] for item in record["annotation_artists"]}
        for annotation in record["annotation_artists"]:
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=annotation["artist"].get_window_extent(renderer=renderer),
                    box_id=str(annotation["box_id"]),
                    box_type="annotation_label",
                )
            )
        for point in record["points"]:
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=effect_value,
                y=significance_value,
            )
            normalized_point = {
                "feature_label": str(point["feature_label"]),
                "x": point_x,
                "y": point_y,
                "effect_value": effect_value,
                "significance_value": significance_value,
                "regulation_class": str(point["regulation_class"]),
            }
            label_text = str(point.get("label_text") or "").strip()
            if label_text:
                normalized_point["label_text"] = label_text
                normalized_point["label_box_id"] = label_box_lookup[str(point["feature_label"])]
            normalized_points.append(normalized_point)

        normalized_panels.append(
            {
                "panel_id": str(record["panel_id"]),
                "panel_title": panel_title_lookup[str(record["panel_id"])],
                "panel_label": panel_token,
                "panel_box_id": panel_box_id,
                "panel_label_box_id": panel_label_box_id,
                "panel_title_box_id": panel_title_box_id,
                "x_axis_title_box_id": x_axis_title_box_id,
                "effect_threshold_left_box_id": f"panel_{panel_token}_threshold_left",
                "effect_threshold_right_box_id": f"panel_{panel_token}_threshold_right",
                "significance_threshold_box_id": f"panel_{panel_token}_significance_threshold",
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
            "guide_boxes": guide_boxes,
            "metrics": {
                "legend_title": str(display_payload.get("legend_title") or "").strip(),
                "effect_threshold": effect_threshold,
                "significance_threshold": significance_threshold,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
