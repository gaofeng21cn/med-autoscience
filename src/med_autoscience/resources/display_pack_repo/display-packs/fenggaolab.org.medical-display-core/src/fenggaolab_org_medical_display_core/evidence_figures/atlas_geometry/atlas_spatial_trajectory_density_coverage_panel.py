from __future__ import annotations

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

def _render_python_atlas_spatial_trajectory_density_coverage_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    atlas_points = list(display_payload.get("atlas_points") or [])
    spatial_points = list(display_payload.get("spatial_points") or [])
    trajectory_points = list(display_payload.get("trajectory_points") or [])
    state_order = list(display_payload.get("state_order") or [])
    context_order = list(display_payload.get("context_order") or [])
    support_cells = list(display_payload.get("support_cells") or [])
    if not atlas_points or not spatial_points or not trajectory_points or not state_order or not context_order or not support_cells:
        raise RuntimeError(
            f"{template_id} requires non-empty atlas_points, spatial_points, trajectory_points, "
            "state_order, context_order, and support_cells"
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

    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    state_palette = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#9467bd").strip() or "#9467bd",
        str(palette.get("secondary_soft") or "#17becf").strip() or "#17becf",
    ]
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"

    state_labels = [str(item["label"]) for item in state_order]
    context_labels = [str(item["label"]) for item in context_order]
    context_kinds = [str(item["context_kind"]) for item in context_order]
    region_labels = list(
        dict.fromkeys(
            str(item.get("region_label") or "").strip()
            for item in spatial_points
            if str(item.get("region_label") or "").strip()
        )
    )
    branch_labels = list(
        dict.fromkeys(
            str(item.get("branch_label") or "").strip()
            for item in trajectory_points
            if str(item.get("branch_label") or "").strip()
        )
    )
    state_color_lookup = {
        label: state_palette[index % len(state_palette)] for index, label in enumerate(state_labels)
    }
    support_scale_label = str(display_payload.get("support_scale_label") or "").strip()

    fig = plt.figure(figsize=(13.8, 8.0))
    fig.patch.set_facecolor("white")
    grid = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.92], width_ratios=[1.0, 1.0, 1.0])
    atlas_axes = fig.add_subplot(grid[0, 0])
    spatial_axes = fig.add_subplot(grid[0, 1])
    trajectory_axes = fig.add_subplot(grid[0, 2])
    support_axes = fig.add_subplot(grid[1, :])

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

    def _plot_state_scatter(axes_item: Any, points: list[dict[str, Any]]) -> None:
        for state_label in state_labels:
            filtered_points = [item for item in points if str(item["state_label"]) == state_label]
            if not filtered_points:
                continue
            axes_item.scatter(
                [float(item["x"]) for item in filtered_points],
                [float(item["y"]) for item in filtered_points],
                label=state_label,
                s=36,
                alpha=0.92,
                color=state_color_lookup[state_label],
                edgecolors="white",
                linewidths=0.4,
            )

    _plot_state_scatter(atlas_axes, atlas_points)
    atlas_axes.set_title(
        str(display_payload.get("atlas_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_xlabel(
        str(display_payload.get("atlas_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.set_ylabel(
        str(display_payload.get("atlas_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    atlas_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    atlas_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(atlas_axes)

    _plot_state_scatter(spatial_axes, spatial_points)
    spatial_axes.set_title(
        str(display_payload.get("spatial_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    spatial_axes.set_xlabel(
        str(display_payload.get("spatial_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    spatial_axes.set_ylabel(
        str(display_payload.get("spatial_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    spatial_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    spatial_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(spatial_axes)

    for branch_label in branch_labels:
        branch_points = sorted(
            [item for item in trajectory_points if str(item["branch_label"]) == branch_label],
            key=lambda item: float(item["pseudotime"]),
        )
        if len(branch_points) >= 2:
            trajectory_axes.plot(
                [float(item["x"]) for item in branch_points],
                [float(item["y"]) for item in branch_points],
                color=neutral_color,
                linewidth=1.4,
                alpha=0.45,
            )
    _plot_state_scatter(trajectory_axes, trajectory_points)
    trajectory_axes.set_title(
        str(display_payload.get("trajectory_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    trajectory_axes.set_xlabel(
        str(display_payload.get("trajectory_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    trajectory_axes.set_ylabel(
        str(display_payload.get("trajectory_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    trajectory_axes.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
    trajectory_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(trajectory_axes)

    support_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in support_cells}
    support_matrix = [[support_lookup[(context_label, state_label)] for context_label in context_labels] for state_label in state_labels]
    heatmap_artist = support_axes.imshow(support_matrix, aspect="auto", cmap="Blues", vmin=0.0, vmax=1.0)
    support_axes.set_title(
        str(display_payload.get("support_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    support_axes.set_xlabel(
        str(display_payload.get("support_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    support_axes.set_ylabel(
        str(display_payload.get("support_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    support_axes.set_xticks(range(len(context_labels)))
    support_axes.set_xticklabels(context_labels, fontsize=tick_size, rotation=18, ha="right", color=neutral_color)
    support_axes.set_yticks(range(len(state_labels)))
    support_axes.set_yticklabels(state_labels, fontsize=tick_size, color=neutral_color)
    support_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(support_axes)
    for row_index, state_label in enumerate(state_labels):
        for column_index, context_label in enumerate(context_labels):
            value = support_lookup[(context_label, state_label)]
            support_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )

    def _optional_annotation(axes_item: Any, key: str) -> Any:
        annotation = str(display_payload.get(key) or "").strip()
        if not annotation:
            return None
        return axes_item.text(
            0.03,
            0.05,
            annotation,
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    atlas_annotation_artist = _optional_annotation(atlas_axes, "atlas_annotation")
    spatial_annotation_artist = _optional_annotation(spatial_axes, "spatial_annotation")
    trajectory_annotation_artist = _optional_annotation(trajectory_axes, "trajectory_annotation")
    support_annotation_artist = _optional_annotation(support_axes, "support_annotation")

    title_top = 0.80 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.08,
        right=0.90,
        top=max(0.70, title_top) if show_figure_title else 0.88,
        bottom=0.20,
        wspace=0.32,
        hspace=0.38,
    )

    legend_handles = [
        matplotlib.patches.Patch(color=state_color_lookup[state_label], label=state_label) for state_label in state_labels
    ]
    legend = fig.legend(
        legend_handles,
        state_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.06, 0.02),
        ncol=min(4, max(1, len(state_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=support_axes, fraction=0.034, pad=0.03)
    colorbar.set_label(
        support_scale_label,
        fontsize=max(axis_title_size - 0.5, 9.8),
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
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.025, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.6),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_a = _add_panel_label(axes_item=atlas_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=spatial_axes, label="B")
    panel_label_c = _add_panel_label(axes_item=trajectory_axes, label="C")
    panel_label_d = _add_panel_label(axes_item=support_axes, label="D")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.title.get_window_extent(renderer=renderer),
            box_id="atlas_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="atlas_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.title.get_window_extent(renderer=renderer),
            box_id="spatial_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="spatial_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="spatial_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=trajectory_axes.title.get_window_extent(renderer=renderer),
            box_id="trajectory_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=trajectory_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="trajectory_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=trajectory_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="trajectory_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.title.get_window_extent(renderer=renderer),
            box_id="support_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="support_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="support_y_axis_title",
            box_type="subplot_y_axis_title",
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
        _bbox_to_layout_box(
            figure=fig,
            bbox=panel_label_c.get_window_extent(renderer=renderer),
            box_id="panel_label_C",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=panel_label_d.get_window_extent(renderer=renderer),
            box_id="panel_label_D",
            box_type="panel_label",
        ),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist.get_window_extent(renderer=renderer),
                box_id="title",
                box_type="title",
            ),
        )
    if atlas_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=atlas_annotation_artist.get_window_extent(renderer=renderer),
                box_id="atlas_annotation",
                box_type="annotation_text",
            )
        )
    if spatial_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=spatial_annotation_artist.get_window_extent(renderer=renderer),
                box_id="spatial_annotation",
                box_type="annotation_text",
            )
        )
    if trajectory_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=trajectory_annotation_artist.get_window_extent(renderer=renderer),
                box_id="trajectory_annotation",
                box_type="annotation_text",
            )
        )
    if support_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=support_annotation_artist.get_window_extent(renderer=renderer),
                box_id="support_annotation",
                box_type="annotation_text",
            )
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=atlas_axes.get_window_extent(renderer=renderer),
            box_id="panel_atlas",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=spatial_axes.get_window_extent(renderer=renderer),
            box_id="panel_spatial",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=trajectory_axes.get_window_extent(renderer=renderer),
            box_id="panel_trajectory",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_axes.get_window_extent(renderer=renderer),
            box_id="panel_support",
            box_type="heatmap_tile_region",
        ),
    ]

    def _normalize_scatter_points(axes_item: Any, points: list[dict[str, Any]], extra_keys: tuple[str, ...]) -> list[dict[str, Any]]:
        normalized_points: list[dict[str, Any]] = []
        for item in points:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(item["x"]),
                y=float(item["y"]),
            )
            normalized_point = {
                "x": point_x,
                "y": point_y,
                "state_label": str(item["state_label"]),
            }
            for extra_key in extra_keys:
                if extra_key in item and str(item.get(extra_key) or "").strip():
                    normalized_point[extra_key] = item[extra_key]
            if "pseudotime" in item:
                normalized_point["pseudotime"] = float(item["pseudotime"])
            normalized_points.append(normalized_point)
        return normalized_points

    normalized_support_cells = [
        {
            "x": str(item["x"]),
            "y": str(item["y"]),
            "value": float(item["value"]),
        }
        for item in support_cells
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
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=colorbar.ax.get_window_extent(renderer=renderer),
                    box_id="colorbar",
                    box_type="colorbar",
                ),
            ],
            "metrics": {
                "atlas_points": _normalize_scatter_points(atlas_axes, atlas_points, ()),
                "spatial_points": _normalize_scatter_points(spatial_axes, spatial_points, ("region_label",)),
                "trajectory_points": _normalize_scatter_points(trajectory_axes, trajectory_points, ("branch_label",)),
                "state_labels": state_labels,
                "region_labels": region_labels,
                "branch_labels": branch_labels,
                "context_labels": context_labels,
                "context_kinds": context_kinds,
                "support_scale_label": support_scale_label,
                "support_cells": normalized_support_cells,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

