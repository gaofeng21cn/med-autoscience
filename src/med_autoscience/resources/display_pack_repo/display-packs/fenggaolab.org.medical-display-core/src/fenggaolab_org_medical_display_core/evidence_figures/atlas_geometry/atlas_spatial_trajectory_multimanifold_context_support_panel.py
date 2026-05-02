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

def _render_python_atlas_spatial_trajectory_multimanifold_context_support_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    atlas_manifold_panels = list(display_payload.get("atlas_manifold_panels") or [])
    spatial_points = list(display_payload.get("spatial_points") or [])
    trajectory_points = list(display_payload.get("trajectory_points") or [])
    composition_groups = list(display_payload.get("composition_groups") or [])
    progression_bins = list(display_payload.get("progression_bins") or [])
    matrix_cells = list(display_payload.get("cells") or [])
    support_cells = list(display_payload.get("support_cells") or [])
    state_order = list(display_payload.get("state_order") or [])
    branch_order = list(display_payload.get("branch_order") or [])
    row_order = list(display_payload.get("row_order") or [])
    column_order = list(display_payload.get("column_order") or [])
    context_order = list(display_payload.get("context_order") or [])
    if (
        len(atlas_manifold_panels) != 2
        or not spatial_points
        or not trajectory_points
        or not composition_groups
        or not progression_bins
        or not matrix_cells
        or not support_cells
        or not state_order
        or not branch_order
        or not row_order
        or not column_order
        or not context_order
    ):
        raise RuntimeError(
            f"{template_id} requires exactly two atlas_manifold_panels plus non-empty spatial_points, "
            "trajectory_points, composition_groups, progression_bins, state_order, branch_order, row_order, "
            "column_order, context_order, support_cells, and cells"
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
    branch_labels = [str(item["label"]) for item in branch_order]
    row_labels = [str(item["label"]) for item in row_order]
    bin_labels = [str(item["label"]) for item in column_order]
    context_labels = [str(item["label"]) for item in context_order]
    context_kinds = [str(item["context_kind"]) for item in context_order]
    state_color_lookup = {
        label: state_palette[index % len(state_palette)] for index, label in enumerate(state_labels)
    }
    support_scale_label = str(display_payload.get("support_scale_label") or "").strip()

    fig = plt.figure(figsize=(18.0, 8.8))
    fig.patch.set_facecolor("white")
    outer_grid = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.98])
    top_grid = outer_grid[0].subgridspec(1, 4, wspace=0.28)
    bottom_grid = outer_grid[1].subgridspec(1, 3, wspace=0.30)
    atlas_axes_a = fig.add_subplot(top_grid[0, 0])
    atlas_axes_b = fig.add_subplot(top_grid[0, 1])
    spatial_axes = fig.add_subplot(top_grid[0, 2])
    trajectory_axes = fig.add_subplot(top_grid[0, 3])
    composition_axes = fig.add_subplot(bottom_grid[0, 0])
    heatmap_axes = fig.add_subplot(bottom_grid[0, 1])
    support_axes = fig.add_subplot(bottom_grid[0, 2])

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
                s=34,
                alpha=0.92,
                color=state_color_lookup[state_label],
                edgecolors="white",
                linewidths=0.4,
            )

    atlas_axes_by_panel = ((atlas_axes_a, atlas_manifold_panels[0]), (atlas_axes_b, atlas_manifold_panels[1]))
    for axes_item, panel in atlas_axes_by_panel:
        _plot_state_scatter(axes_item, list(panel.get("points") or []))
        axes_item.set_title(
            str(panel.get("panel_title") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_xlabel(
            str(panel.get("x_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_ylabel(
            str(panel.get("y_label") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.tick_params(axis="both", labelsize=tick_size, colors=neutral_color)
        axes_item.grid(color=light_fill, linewidth=0.8, linestyle=":")
        _apply_publication_axes_style(axes_item)

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

    ordered_composition_groups = sorted(composition_groups, key=lambda item: int(item["group_order"]))
    group_labels = [str(item["group_label"]) for item in ordered_composition_groups]
    y_positions = list(range(len(ordered_composition_groups)))
    cumulative = [0.0] * len(ordered_composition_groups)
    for state_label in state_labels:
        state_values = []
        for group in ordered_composition_groups:
            state_lookup = {
                str(item["state_label"]): float(item["proportion"]) for item in list(group.get("state_proportions") or [])
            }
            state_values.append(state_lookup[state_label])
        bar_artists = composition_axes.barh(
            y_positions,
            state_values,
            left=cumulative,
            height=0.60,
            color=matplotlib.colors.to_rgba(state_color_lookup[state_label], alpha=0.90),
            edgecolor="white",
            linewidth=0.8,
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

    matrix_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in matrix_cells}
    matrix_rows = [[matrix_lookup[(bin_label, row_label)] for bin_label in bin_labels] for row_label in row_labels]
    vmax = max(abs(value) for value in matrix_lookup.values()) if matrix_lookup else 1.0
    vmax = max(vmax, 1e-6)
    heatmap_axes.imshow(matrix_rows, aspect="auto", cmap="coolwarm", vmin=-vmax, vmax=vmax)
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
    heatmap_axes.set_xticklabels(bin_labels, fontsize=tick_size, rotation=18, ha="right", color=neutral_color)
    heatmap_axes.set_yticks(range(len(row_labels)))
    heatmap_axes.set_yticklabels(row_labels, fontsize=tick_size, color=neutral_color)
    heatmap_axes.tick_params(axis="both", length=0)
    _apply_publication_axes_style(heatmap_axes)
    for row_index, row_label in enumerate(row_labels):
        for column_index, bin_label in enumerate(bin_labels):
            heatmap_axes.text(
                column_index,
                row_index,
                f"{matrix_lookup[(bin_label, row_label)]:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.4, 7.6),
                color="#13293d",
            )

    support_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in support_cells}
    support_rows = [[support_lookup[(context_label, state_label)] for context_label in context_labels] for state_label in state_labels]
    support_artist = support_axes.imshow(support_rows, aspect="auto", cmap="Blues", vmin=0.0, vmax=1.0)
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
            support_axes.text(
                column_index,
                row_index,
                f"{support_lookup[(context_label, state_label)]:.2f}",
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

    spatial_annotation_artist = _optional_annotation(spatial_axes, "spatial_annotation")
    trajectory_annotation_artist = _optional_annotation(trajectory_axes, "trajectory_annotation")
    composition_annotation_artist = _optional_annotation(composition_axes, "composition_annotation")
    heatmap_annotation_artist = _optional_annotation(heatmap_axes, "heatmap_annotation")
    support_annotation_artist = _optional_annotation(support_axes, "support_annotation")

    title_top = 0.82 - 0.05 * max(title_line_count - 1, 0)
    fig.subplots_adjust(
        left=0.12,
        right=0.95,
        top=max(0.72, title_top) if show_figure_title else 0.88,
        bottom=0.20,
        hspace=0.40,
    )

    legend_handles = [
        matplotlib.patches.Patch(color=state_color_lookup[state_label], label=state_label) for state_label in state_labels
    ]
    legend = fig.legend(
        legend_handles,
        state_labels,
        frameon=False,
        loc="lower left",
        bbox_to_anchor=(0.05, 0.02),
        ncol=min(4, max(1, len(state_labels))),
    )
    colorbar = fig.colorbar(support_artist, ax=support_axes, fraction=0.040, pad=0.03)
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

    panel_label_a = _add_panel_label(axes_item=atlas_axes_a, label="A")
    panel_label_b = _add_panel_label(axes_item=atlas_axes_b, label="B")
    panel_label_c = _add_panel_label(axes_item=spatial_axes, label="C")
    panel_label_d = _add_panel_label(axes_item=trajectory_axes, label="D")
    panel_label_e = _add_panel_label(axes_item=composition_axes, label="E")
    panel_label_f = _add_panel_label(axes_item=heatmap_axes, label="F")
    panel_label_g = _add_panel_label(axes_item=support_axes, label="G")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=atlas_axes_a.title.get_window_extent(renderer=renderer), box_id="atlas_A_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=atlas_axes_a.xaxis.label.get_window_extent(renderer=renderer), box_id="atlas_A_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=atlas_axes_a.yaxis.label.get_window_extent(renderer=renderer), box_id="atlas_A_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=atlas_axes_b.title.get_window_extent(renderer=renderer), box_id="atlas_B_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=atlas_axes_b.xaxis.label.get_window_extent(renderer=renderer), box_id="atlas_B_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=atlas_axes_b.yaxis.label.get_window_extent(renderer=renderer), box_id="atlas_B_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=spatial_axes.title.get_window_extent(renderer=renderer), box_id="spatial_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=spatial_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="spatial_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=spatial_axes.yaxis.label.get_window_extent(renderer=renderer), box_id="spatial_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=trajectory_axes.title.get_window_extent(renderer=renderer), box_id="trajectory_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=trajectory_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="trajectory_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=trajectory_axes.yaxis.label.get_window_extent(renderer=renderer), box_id="trajectory_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=composition_axes.title.get_window_extent(renderer=renderer), box_id="composition_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=composition_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="composition_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=composition_axes.yaxis.label.get_window_extent(renderer=renderer), box_id="composition_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=heatmap_axes.title.get_window_extent(renderer=renderer), box_id="heatmap_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=heatmap_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="heatmap_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=heatmap_axes.yaxis.label.get_window_extent(renderer=renderer), box_id="heatmap_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=support_axes.title.get_window_extent(renderer=renderer), box_id="support_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=support_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="support_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=support_axes.yaxis.label.get_window_extent(renderer=renderer), box_id="support_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_a.get_window_extent(renderer=renderer), box_id="panel_label_A", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_b.get_window_extent(renderer=renderer), box_id="panel_label_B", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_c.get_window_extent(renderer=renderer), box_id="panel_label_C", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_d.get_window_extent(renderer=renderer), box_id="panel_label_D", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_e.get_window_extent(renderer=renderer), box_id="panel_label_E", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_f.get_window_extent(renderer=renderer), box_id="panel_label_F", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_g.get_window_extent(renderer=renderer), box_id="panel_label_G", box_type="panel_label"),
    ]
    if title_artist is not None:
        layout_boxes.insert(
            0,
            _bbox_to_layout_box(figure=fig, bbox=title_artist.get_window_extent(renderer=renderer), box_id="title", box_type="title"),
        )
    for annotation_artist, box_id in (
        (spatial_annotation_artist, "spatial_annotation"),
        (trajectory_annotation_artist, "trajectory_annotation"),
        (composition_annotation_artist, "composition_annotation"),
        (heatmap_annotation_artist, "heatmap_annotation"),
        (support_annotation_artist, "support_annotation"),
    ):
        if annotation_artist is None:
            continue
        layout_boxes.append(
            _bbox_to_layout_box(figure=fig, bbox=annotation_artist.get_window_extent(renderer=renderer), box_id=box_id, box_type="annotation_text")
        )

    panel_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=atlas_axes_a.get_window_extent(renderer=renderer), box_id="panel_atlas_A", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=atlas_axes_b.get_window_extent(renderer=renderer), box_id="panel_atlas_B", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=spatial_axes.get_window_extent(renderer=renderer), box_id="panel_spatial", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=trajectory_axes.get_window_extent(renderer=renderer), box_id="panel_trajectory", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=composition_axes.get_window_extent(renderer=renderer), box_id="panel_composition", box_type="composition_panel"),
        _bbox_to_layout_box(figure=fig, bbox=heatmap_axes.get_window_extent(renderer=renderer), box_id="panel_heatmap", box_type="heatmap_tile_region"),
        _bbox_to_layout_box(figure=fig, bbox=support_axes.get_window_extent(renderer=renderer), box_id="panel_support", box_type="heatmap_tile_region"),
    ]

    def _normalize_scatter_points(axes_item: Any, points: list[dict[str, Any]], extra_keys: tuple[str, ...]) -> list[dict[str, Any]]:
        normalized_points: list[dict[str, Any]] = []
        for item in points:
            point_x, point_y = _data_point_to_figure_xy(axes=axes_item, figure=fig, x=float(item["x"]), y=float(item["y"]))
            normalized_point = {"x": point_x, "y": point_y, "state_label": str(item["state_label"])}
            for extra_key in extra_keys:
                if extra_key in item and str(item.get(extra_key) or "").strip():
                    normalized_point[extra_key] = item[extra_key]
            if "pseudotime" in item:
                normalized_point["pseudotime"] = float(item["pseudotime"])
            if "branch_label" in item and str(item.get("branch_label") or "").strip():
                normalized_point["branch_label"] = item["branch_label"]
            normalized_points.append(normalized_point)
        return normalized_points

    normalized_composition_groups = [
        {
            "group_label": str(group["group_label"]),
            "group_order": int(group["group_order"]),
            "state_proportions": [
                {"state_label": str(item["state_label"]), "proportion": float(item["proportion"])}
                for item in list(group.get("state_proportions") or [])
            ],
        }
        for group in ordered_composition_groups
    ]
    normalized_progression_bins = [
        {
            "bin_label": str(item["bin_label"]),
            "bin_order": int(item["bin_order"]),
            "pseudotime_start": float(item["pseudotime_start"]),
            "pseudotime_end": float(item["pseudotime_end"]),
            "branch_weights": [
                {"branch_label": str(branch_item["branch_label"]), "proportion": float(branch_item["proportion"])}
                for branch_item in list(item.get("branch_weights") or [])
            ],
        }
        for item in progression_bins
    ]
    normalized_matrix_cells = [
        {"x": str(item["x"]), "y": str(item["y"]), "value": float(item["value"])} for item in matrix_cells
    ]
    normalized_support_cells = [
        {"x": str(item["x"]), "y": str(item["y"]), "value": float(item["value"])} for item in support_cells
    ]
    normalized_atlas_panels = []
    for axes_item, panel in atlas_axes_by_panel:
        normalized_atlas_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "manifold_method": str(panel["manifold_method"]),
                "points": _normalize_scatter_points(axes_item, list(panel.get("points") or []), ()),
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
                _bbox_to_layout_box(figure=fig, bbox=legend.get_window_extent(renderer=renderer), box_id="legend", box_type="legend"),
                _bbox_to_layout_box(figure=fig, bbox=colorbar.ax.get_window_extent(renderer=renderer), box_id="colorbar", box_type="colorbar"),
            ],
            "metrics": {
                "atlas_manifold_panels": normalized_atlas_panels,
                "atlas_points": list(normalized_atlas_panels[0]["points"]),
                "spatial_points": _normalize_scatter_points(spatial_axes, spatial_points, ("region_label",)),
                "trajectory_points": _normalize_scatter_points(trajectory_axes, trajectory_points, ("branch_label",)),
                "state_labels": state_labels,
                "branch_labels": branch_labels,
                "bin_labels": bin_labels,
                "row_labels": row_labels,
                "context_labels": context_labels,
                "context_kinds": context_kinds,
                "composition_groups": normalized_composition_groups,
                "progression_bins": normalized_progression_bins,
                "matrix_cells": normalized_matrix_cells,
                "support_cells": normalized_support_cells,
                "score_method": str(display_payload.get("score_method") or "").strip(),
                "support_scale_label": support_scale_label,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
