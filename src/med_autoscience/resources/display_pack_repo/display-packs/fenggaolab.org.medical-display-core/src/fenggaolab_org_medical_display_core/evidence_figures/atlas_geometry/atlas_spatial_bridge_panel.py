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

def _render_python_atlas_spatial_bridge_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    atlas_points = list(display_payload.get("atlas_points") or [])
    spatial_points = list(display_payload.get("spatial_points") or [])
    composition_groups = list(display_payload.get("composition_groups") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    if (
        not atlas_points
        or not spatial_points
        or not composition_groups
        or not matrix_cells
        or not row_order
        or not column_order
    ):
        raise RuntimeError(
            f"{template_id} requires non-empty atlas_points, spatial_points, composition_groups, row_order, column_order, and cells"
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

    state_labels = [str(item["label"]) for item in column_order]
    row_labels = [str(item["label"]) for item in row_order]
    state_color_lookup = {
        label: state_palette[index % len(state_palette)] for index, label in enumerate(state_labels)
    }

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(13.8, 8.2),
        gridspec_kw={"height_ratios": [1.0, 0.94], "width_ratios": [1.0, 1.0]},
    )
    atlas_axes, spatial_axes = axes[0]
    composition_axes, heatmap_axes = axes[1]
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

    for state_label in state_labels:
        state_points = [item for item in atlas_points if str(item["state_label"]) == state_label]
        if not state_points:
            continue
        atlas_axes.scatter(
            [float(item["x"]) for item in state_points],
            [float(item["y"]) for item in state_points],
            label=state_label,
            s=38,
            alpha=0.92,
            color=state_color_lookup[state_label],
            edgecolors="white",
            linewidths=0.4,
        )
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
    atlas_annotation_artist = None
    atlas_annotation = str(display_payload.get("atlas_annotation") or "").strip()
    if atlas_annotation:
        atlas_annotation_artist = atlas_axes.text(
            0.03,
            0.05,
            atlas_annotation,
            transform=atlas_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    for state_label in state_labels:
        state_points = [item for item in spatial_points if str(item["state_label"]) == state_label]
        if not state_points:
            continue
        spatial_axes.scatter(
            [float(item["x"]) for item in state_points],
            [float(item["y"]) for item in state_points],
            label=state_label,
            s=42,
            alpha=0.94,
            color=state_color_lookup[state_label],
            edgecolors="white",
            linewidths=0.5,
        )
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
    spatial_annotation_artist = None
    spatial_annotation = str(display_payload.get("spatial_annotation") or "").strip()
    if spatial_annotation:
        spatial_annotation_artist = spatial_axes.text(
            0.03,
            0.05,
            spatial_annotation,
            transform=spatial_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    ordered_composition_groups = sorted(composition_groups, key=lambda item: int(item["group_order"]))
    group_labels = [str(item["group_label"]) for item in ordered_composition_groups]
    y_positions = list(range(len(ordered_composition_groups)))
    cumulative = [0.0] * len(ordered_composition_groups)
    for state_label in state_labels:
        state_values = []
        for group in ordered_composition_groups:
            state_lookup = {
                str(item["state_label"]): float(item["proportion"])
                for item in list(group.get("state_proportions") or [])
            }
            state_values.append(state_lookup[state_label])
        bar_artists = composition_axes.barh(
            y_positions,
            state_values,
            left=cumulative,
            height=0.62,
            color=matplotlib.colors.to_rgba(state_color_lookup[state_label], alpha=0.90),
            edgecolor="white",
            linewidth=0.8,
            label=state_label,
        )
        for bar_artist, value, left_start in zip(bar_artists, state_values, cumulative, strict=True):
            if value < 0.12:
                continue
            composition_axes.text(
                left_start + value / 2.0,
                float(bar_artist.get_y()) + float(bar_artist.get_height()) / 2.0,
                f"{value * 100:.0f}%",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.6, 7.2),
                color="#13293d",
            )
        cumulative = [left_start + value for left_start, value in zip(cumulative, state_values, strict=True)]
    composition_axes.set_xlim(0.0, 1.0)
    composition_axes.set_yticks(y_positions)
    composition_axes.set_yticklabels(group_labels, fontsize=tick_size, color=neutral_color)
    composition_axes.invert_yaxis()
    composition_axes.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
    composition_axes.set_title(
        str(display_payload.get("composition_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.set_xlabel(
        str(display_payload.get("composition_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.set_ylabel(
        str(display_payload.get("composition_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    composition_axes.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
    composition_axes.tick_params(axis="y", length=0, colors=neutral_color)
    composition_axes.grid(axis="x", color=light_fill, linewidth=0.8, linestyle=":")
    composition_axes.grid(axis="y", visible=False)
    _apply_publication_axes_style(composition_axes)
    composition_annotation_artist = None
    composition_annotation = str(display_payload.get("composition_annotation") or "").strip()
    if composition_annotation:
        composition_annotation_artist = composition_axes.text(
            0.03,
            0.05,
            composition_annotation,
            transform=composition_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    matrix_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in matrix_cells}
    matrix_rows = [[matrix_lookup[(state_label, row_label)] for state_label in state_labels] for row_label in row_labels]
    vmax = max(abs(value) for value in matrix_lookup.values()) if matrix_lookup else 1.0
    vmax = max(vmax, 1e-6)
    heatmap_artist = heatmap_axes.imshow(matrix_rows, aspect="auto", cmap="coolwarm", vmin=-vmax, vmax=vmax)
    heatmap_axes.set_title(
        str(display_payload.get("heatmap_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_xlabel(
        str(display_payload.get("heatmap_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_ylabel(
        str(display_payload.get("heatmap_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    heatmap_axes.set_xticks(range(len(state_labels)))
    heatmap_axes.set_xticklabels(state_labels, fontsize=tick_size, rotation=22, ha="right", color=neutral_color)
    heatmap_axes.set_yticks(range(len(row_labels)))
    heatmap_axes.set_yticklabels(row_labels, fontsize=tick_size, color=neutral_color)
    heatmap_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(heatmap_axes)
    for row_index, row_label in enumerate(row_labels):
        for column_index, state_label in enumerate(state_labels):
            value = matrix_lookup[(state_label, row_label)]
            heatmap_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )
    heatmap_annotation_artist = None
    heatmap_annotation = str(display_payload.get("heatmap_annotation") or "").strip()
    if heatmap_annotation:
        heatmap_annotation_artist = heatmap_axes.text(
            0.03,
            0.05,
            heatmap_annotation,
            transform=heatmap_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    title_top = 0.86 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.10,
        right=0.92,
        top=max(0.78, title_top) if show_figure_title else 0.88,
        bottom=0.18,
        hspace=0.34,
        wspace=0.28,
    )

    legend_handles = [
        matplotlib.patches.Patch(color=state_color_lookup[state_label], label=state_label) for state_label in state_labels
    ]
    legend = fig.legend(
        legend_handles,
        state_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.15, 0.02),
        ncol=min(4, max(1, len(state_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=heatmap_axes, fraction=0.050, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("score_method") or "").strip(),
        fontsize=max(axis_title_size - 0.5, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors=neutral_color)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_figure_panel_label(*, axes_item, label: str) -> Any:
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

    panel_label_a = _add_figure_panel_label(axes_item=atlas_axes, label="A")
    panel_label_b = _add_figure_panel_label(axes_item=spatial_axes, label="B")
    panel_label_c = _add_figure_panel_label(axes_item=composition_axes, label="C")
    panel_label_d = _add_figure_panel_label(axes_item=heatmap_axes, label="D")
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
            bbox=composition_axes.title.get_window_extent(renderer=renderer),
            box_id="composition_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="composition_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=composition_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="composition_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.title.get_window_extent(renderer=renderer),
            box_id="heatmap_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_y_axis_title",
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
    for annotation_artist, box_id in (
        (atlas_annotation_artist, "atlas_annotation"),
        (spatial_annotation_artist, "spatial_annotation"),
        (composition_annotation_artist, "composition_annotation"),
        (heatmap_annotation_artist, "heatmap_annotation"),
    ):
        if annotation_artist is None:
            continue
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=annotation_artist.get_window_extent(renderer=renderer),
                box_id=box_id,
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
            bbox=composition_axes.get_window_extent(renderer=renderer),
            box_id="panel_composition",
            box_type="composition_panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=heatmap_axes.get_window_extent(renderer=renderer),
            box_id="panel_heatmap",
            box_type="heatmap_tile_region",
        ),
    ]

    normalized_atlas_points: list[dict[str, Any]] = []
    for item in atlas_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=atlas_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_point = {"x": point_x, "y": point_y, "state_label": str(item["state_label"])}
        group_label = str(item.get("group_label") or "").strip()
        if group_label:
            normalized_point["group_label"] = group_label
        normalized_atlas_points.append(normalized_point)

    normalized_spatial_points: list[dict[str, Any]] = []
    for item in spatial_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=spatial_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_point = {"x": point_x, "y": point_y, "state_label": str(item["state_label"])}
        region_label = str(item.get("region_label") or "").strip()
        if region_label:
            normalized_point["region_label"] = region_label
        normalized_spatial_points.append(normalized_point)

    normalized_composition_groups: list[dict[str, Any]] = []
    for group in ordered_composition_groups:
        normalized_composition_groups.append(
            {
                "group_label": str(group["group_label"]),
                "group_order": int(group["group_order"]),
                "state_proportions": [
                    {"state_label": str(item["state_label"]), "proportion": float(item["proportion"])}
                    for item in list(group.get("state_proportions") or [])
                ],
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
                "atlas_points": normalized_atlas_points,
                "spatial_points": normalized_spatial_points,
                "state_labels": state_labels,
                "row_labels": row_labels,
                "composition_groups": normalized_composition_groups,
                "matrix_cells": matrix_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

