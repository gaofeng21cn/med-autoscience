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

def _render_python_trajectory_progression_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    trajectory_points = list(display_payload.get("trajectory_points") or [])
    branch_order = list(display_payload.get("branch_order") or [])
    progression_bins = list(display_payload.get("progression_bins") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    if not trajectory_points or not branch_order or not progression_bins or not matrix_cells or not row_order or not column_order:
        raise RuntimeError(
            f"{template_id} requires non-empty trajectory_points, branch_order, progression_bins, row_order, column_order, and cells"
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
    branch_palette = [
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

    branch_labels = [str(item["label"]) for item in branch_order]
    ordered_progression_bins = sorted(progression_bins, key=lambda item: int(item["bin_order"]))
    bin_labels = [str(item["bin_label"]) for item in ordered_progression_bins]
    row_labels = [str(item["label"]) for item in row_order]
    branch_color_lookup = {
        label: branch_palette[index % len(branch_palette)] for index, label in enumerate(branch_labels)
    }

    fig, (trajectory_axes, composition_axes, heatmap_axes) = plt.subplots(
        1,
        3,
        figsize=(13.8, 5.0),
        gridspec_kw={"width_ratios": [1.04, 0.96, 1.00]},
    )
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

    for branch_label in branch_labels:
        branch_points = sorted(
            [item for item in trajectory_points if str(item["branch_label"]) == branch_label],
            key=lambda item: float(item["pseudotime"]),
        )
        if not branch_points:
            continue
        branch_x = [float(item["x"]) for item in branch_points]
        branch_y = [float(item["y"]) for item in branch_points]
        trajectory_axes.plot(
            branch_x,
            branch_y,
            color=branch_color_lookup[branch_label],
            linewidth=2.1,
            alpha=0.92,
            zorder=2,
        )
        trajectory_axes.scatter(
            branch_x,
            branch_y,
            label=branch_label,
            s=42,
            alpha=0.96,
            color=branch_color_lookup[branch_label],
            edgecolors="white",
            linewidths=0.4,
            zorder=3,
        )
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
    trajectory_annotation = str(display_payload.get("trajectory_annotation") or "").strip()
    trajectory_annotation_artist = None
    if trajectory_annotation:
        trajectory_annotation_artist = trajectory_axes.text(
            0.03,
            0.05,
            trajectory_annotation,
            transform=trajectory_axes.transAxes,
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="left",
            va="bottom",
        )

    y_positions = list(range(len(ordered_progression_bins)))
    cumulative = [0.0] * len(ordered_progression_bins)
    for branch_label in branch_labels:
        branch_values = []
        for progression_bin in ordered_progression_bins:
            branch_lookup = {
                str(item["branch_label"]): float(item["proportion"])
                for item in list(progression_bin.get("branch_weights") or [])
            }
            branch_values.append(branch_lookup[branch_label])
        bar_artists = composition_axes.barh(
            y_positions,
            branch_values,
            left=cumulative,
            height=0.62,
            color=matplotlib.colors.to_rgba(branch_color_lookup[branch_label], alpha=0.90),
            edgecolor="white",
            linewidth=0.8,
            label=branch_label,
        )
        for bar_artist, value, left_start in zip(bar_artists, branch_values, cumulative, strict=True):
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
        cumulative = [left_start + value for left_start, value in zip(cumulative, branch_values, strict=True)]
    composition_axes.set_xlim(0.0, 1.0)
    composition_axes.set_yticks(y_positions)
    composition_axes.set_yticklabels(bin_labels, fontsize=tick_size, color=neutral_color)
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
    composition_annotation = str(display_payload.get("composition_annotation") or "").strip()
    composition_annotation_artist = None
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
    matrix_rows = [[matrix_lookup[(bin_label, row_label)] for bin_label in bin_labels] for row_label in row_labels]
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
    heatmap_axes.set_xticks(range(len(bin_labels)))
    heatmap_axes.set_xticklabels(bin_labels, fontsize=tick_size, rotation=22, ha="right", color=neutral_color)
    heatmap_axes.set_yticks(range(len(row_labels)))
    heatmap_axes.set_yticklabels(row_labels, fontsize=tick_size, color=neutral_color)
    heatmap_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(heatmap_axes)
    for row_index, row_label in enumerate(row_labels):
        for column_index, bin_label in enumerate(bin_labels):
            value = matrix_lookup[(bin_label, row_label)]
            heatmap_axes.text(
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

    title_top = 0.80 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.06,
        right=0.92,
        top=max(0.72, title_top) if show_figure_title else 0.86,
        bottom=0.24,
        wspace=0.32,
    )

    legend_handles = [
        matplotlib.lines.Line2D(
            [0],
            [0],
            color=branch_color_lookup[branch_label],
            marker="o",
            markersize=6.4,
            linewidth=2.0,
            label=branch_label,
        )
        for branch_label in branch_labels
    ]
    legend = fig.legend(
        legend_handles,
        branch_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.07, 0.02),
        ncol=min(4, max(1, len(branch_labels))),
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

    panel_label_a = _add_figure_panel_label(axes_item=trajectory_axes, label="A")
    panel_label_b = _add_figure_panel_label(axes_item=composition_axes, label="B")
    panel_label_c = _add_figure_panel_label(axes_item=heatmap_axes, label="C")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
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
        (trajectory_annotation_artist, "trajectory_annotation"),
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
            bbox=trajectory_axes.get_window_extent(renderer=renderer),
            box_id="panel_trajectory",
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

    normalized_points: list[dict[str, Any]] = []
    for item in trajectory_points:
        point_x, point_y = _data_point_to_figure_xy(
            axes=trajectory_axes,
            figure=fig,
            x=float(item["x"]),
            y=float(item["y"]),
        )
        normalized_points.append(
            {
                "x": point_x,
                "y": point_y,
                "branch_label": str(item["branch_label"]),
                "state_label": str(item["state_label"]),
                "pseudotime": float(item["pseudotime"]),
            }
        )

    normalized_progression_bins: list[dict[str, Any]] = []
    for progression_bin in ordered_progression_bins:
        normalized_progression_bins.append(
            {
                "bin_label": str(progression_bin["bin_label"]),
                "bin_order": int(progression_bin["bin_order"]),
                "pseudotime_start": float(progression_bin["pseudotime_start"]),
                "pseudotime_end": float(progression_bin["pseudotime_end"]),
                "branch_weights": [
                    {
                        "branch_label": str(item["branch_label"]),
                        "proportion": float(item["proportion"]),
                    }
                    for item in list(progression_bin.get("branch_weights") or [])
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
                "points": normalized_points,
                "branch_labels": branch_labels,
                "bin_labels": bin_labels,
                "row_labels": row_labels,
                "progression_bins": normalized_progression_bins,
                "matrix_cells": matrix_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

