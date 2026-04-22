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
    dump_json,
)

def _render_python_celltype_signature_heatmap(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    embedding_points = list(display_payload.get("embedding_points") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    if not embedding_points or not matrix_cells or not row_order or not column_order:
        raise RuntimeError(f"{template_id} requires non-empty embedding_points, row_order, column_order, and cells")

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
    fallback_palette = [
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

    fig, (left_axes, right_axes) = plt.subplots(
        1,
        2,
        figsize=(11.2, 4.8),
        gridspec_kw={"width_ratios": [1.0, 0.92]},
    )
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )

    group_labels = [str(item["label"]) for item in column_order]
    palette_lookup = {
        label: fallback_palette[index % len(fallback_palette)] for index, label in enumerate(group_labels)
    }
    for group_label in group_labels:
        group_points = [item for item in embedding_points if str(item["group"]) == group_label]
        if not group_points:
            continue
        left_axes.scatter(
            [float(item["x"]) for item in group_points],
            [float(item["y"]) for item in group_points],
            label=group_label,
            s=38,
            alpha=0.92,
            color=palette_lookup[group_label],
            edgecolors="white",
            linewidths=0.4,
        )
    left_axes.set_title(
        str(display_payload.get("embedding_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_xlabel(
        str(display_payload.get("embedding_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_ylabel(
        str(display_payload.get("embedding_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.tick_params(axis="both", labelsize=tick_size)
    left_axes.grid(color=light_fill, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(left_axes)

    embedding_annotation = str(display_payload.get("embedding_annotation") or "").strip()
    embedding_annotation_artist = None
    if embedding_annotation:
        embedding_annotation_artist = left_axes.text(
            0.03,
            0.05,
            embedding_annotation,
            transform=left_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    row_labels = [str(item["label"]) for item in row_order]
    matrix_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in matrix_cells}
    matrix_rows = [[matrix_lookup[(column_label, row_label)] for column_label in group_labels] for row_label in row_labels]
    vmax = max(abs(value) for value in matrix_lookup.values()) if matrix_lookup else 1.0
    vmax = max(vmax, 1e-6)
    heatmap_artist = right_axes.imshow(matrix_rows, aspect="auto", cmap="coolwarm", vmin=-vmax, vmax=vmax)
    right_axes.set_title(
        str(display_payload.get("heatmap_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_xlabel(
        str(display_payload.get("heatmap_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylabel(
        str(display_payload.get("heatmap_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_xticks(range(len(group_labels)))
    right_axes.set_xticklabels(group_labels, fontsize=tick_size, rotation=22, ha="right", color=neutral_color)
    right_axes.set_yticks(range(len(row_labels)))
    right_axes.set_yticklabels(row_labels, fontsize=tick_size, color=neutral_color)
    right_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(right_axes)
    for row_index, row_label in enumerate(row_labels):
        for column_index, column_label in enumerate(group_labels):
            value = matrix_lookup[(column_label, row_label)]
            right_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )

    heatmap_annotation = str(display_payload.get("heatmap_annotation") or "").strip()
    heatmap_annotation_artist = None
    if heatmap_annotation:
        heatmap_annotation_artist = right_axes.text(
            0.03,
            0.05,
            heatmap_annotation,
            transform=right_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    fig.subplots_adjust(
        left=0.08,
        right=0.90,
        top=0.76 if show_figure_title else 0.82,
        bottom=0.24,
        wspace=0.24,
    )
    legend_handles, legend_labels = left_axes.get_legend_handles_labels()
    legend = fig.legend(
        legend_handles,
        legend_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.09, 0.02),
        ncol=min(3, max(1, len(legend_labels))),
    )
    colorbar = fig.colorbar(heatmap_artist, ax=right_axes, fraction=0.050, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("score_method") or "").strip(),
        fontsize=max(axis_title_size - 0.5, 9.8),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_figure_panel_label(*, axes, label: str) -> Any:
        panel_bbox = axes.get_window_extent(renderer=renderer)
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

    panel_label_a = _add_figure_panel_label(axes=left_axes, label="A")
    panel_label_b = _add_figure_panel_label(axes=right_axes, label="B")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="embedding_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="embedding_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="embedding_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="heatmap_panel_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="heatmap_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
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
    if embedding_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=embedding_annotation_artist.get_window_extent(renderer=renderer),
                box_id="embedding_annotation",
                box_type="annotation_text",
            )
        )
    if heatmap_annotation_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=heatmap_annotation_artist.get_window_extent(renderer=renderer),
                box_id="heatmap_annotation",
                box_type="annotation_text",
            )
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.get_window_extent(renderer=renderer),
            box_id="panel_left",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.get_window_extent(renderer=renderer),
            box_id="panel_right",
            box_type="heatmap_tile_region",
        ),
    ]
    guide_boxes = [
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
    ]

    normalized_points = []
    for item in embedding_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=left_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_points.append({"x": point_x, "y": point_y, "group": str(item["group"])})

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "points": normalized_points,
                "group_labels": group_labels,
                "matrix_cells": matrix_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

