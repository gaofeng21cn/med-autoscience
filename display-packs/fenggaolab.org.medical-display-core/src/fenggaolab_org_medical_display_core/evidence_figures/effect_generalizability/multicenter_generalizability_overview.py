from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    dump_json,
)

def _render_python_multicenter_generalizability_overview(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    center_event_counts = list(display_payload.get("center_event_counts") or [])
    coverage_panels = list(display_payload.get("coverage_panels") or [])
    if not center_event_counts or not coverage_panels:
        raise RuntimeError(f"{template_id} requires non-empty center_event_counts and coverage_panels")

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
    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    light_fill = str(palette.get("light") or palette.get("secondary_soft") or comparator_color).strip() or comparator_color
    audit_color = str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F"

    def _resolve_center_axis_labels(labels: list[str]) -> tuple[list[str], str, str]:
        if not labels:
            return [], "verbatim", "Anonymous center identifier"
        parsed: list[tuple[str, str]] = []
        for label in labels:
            match = re.fullmatch(r"\s*([^\d]+?)\s*(\d+)\s*", label)
            if match is None:
                return labels, "verbatim", "Anonymous center identifier"
            prefix = re.sub(r"\s+", " ", match.group(1)).strip()
            digits = match.group(2)
            if not prefix:
                return labels, "verbatim", "Anonymous center identifier"
            parsed.append((prefix, digits))
        normalized_prefixes = {prefix.casefold() for prefix, _ in parsed}
        compacted_labels = [digits for _, digits in parsed]
        if len(normalized_prefixes) != 1 or len(set(compacted_labels)) != len(compacted_labels):
            return labels, "verbatim", "Anonymous center identifier"
        shared_prefix = parsed[0][0]
        axis_title = f"{shared_prefix} ID"
        return compacted_labels, "shared_prefix_compacted", axis_title

    figure_height = max(7.0, 0.18 * len(center_event_counts) + 5.8)
    fig = plt.figure(figsize=(10.8, figure_height))
    grid = fig.add_gridspec(2, 2, height_ratios=[2.0, 1.0], hspace=0.38, width_ratios=[1.0, 1.0])
    center_axes = fig.add_subplot(grid[0, :])
    region_axes = fig.add_subplot(grid[1, 0])
    right_grid = grid[1, 1].subgridspec(2, 1, hspace=0.85)
    north_south_axes = fig.add_subplot(right_grid[0, 0])
    urban_rural_axes = fig.add_subplot(right_grid[1, 0])
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
            y=0.985,
        )
    center_colors = {"train": comparator_color, "validation": model_color}
    center_labels = [str(item["center_label"]) for item in center_event_counts]
    center_tick_labels, center_label_mode, center_axis_title = _resolve_center_axis_labels(center_labels)
    if not center_tick_labels:
        center_tick_labels = center_labels
    center_values = [int(item["event_count"]) for item in center_event_counts]
    center_split_buckets = [str(item["split_bucket"]) for item in center_event_counts]
    center_bars = center_axes.bar(
        center_tick_labels,
        center_values,
        color=[center_colors[item] for item in center_split_buckets],
        edgecolor="none",
        linewidth=0,
    )
    center_axes.set_ylabel(
        str(display_payload.get("center_event_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    center_axes.set_xlabel(center_axis_title, fontsize=axis_title_size, fontweight="bold", color=neutral_color)
    center_axes.set_title(
        "Center-level support across the frozen split",
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        pad=10,
    )
    center_axes.grid(axis="y", linestyle=":", color=light_fill, zorder=0)
    center_axes.tick_params(axis="x", rotation=90, labelsize=max(tick_size - 3.0, 6.0), colors=neutral_color)
    center_axes.tick_params(axis="y", labelsize=tick_size, colors=neutral_color)
    _apply_publication_axes_style(center_axes)
    legend = fig.legend(
        handles=[
            matplotlib.patches.Patch(color=center_colors["train"], label="Train"),
            matplotlib.patches.Patch(color=center_colors["validation"], label="Validation"),
        ],
        title="Split",
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=2,
        borderaxespad=0.0,
    )
    coverage_axes_by_role = {
        "wide_left": region_axes,
        "top_right": north_south_axes,
        "bottom_right": urban_rural_axes,
    }
    coverage_bar_artists: list[tuple[str, Any]] = []
    for panel in coverage_panels:
        axes = coverage_axes_by_role[str(panel["layout_role"])]
        labels = [str(bar["label"]) for bar in panel["bars"]]
        counts = [int(bar["count"]) for bar in panel["bars"]]
        if panel["layout_role"] == "wide_left":
            colors = [neutral_color] * len(counts)
        elif panel["layout_role"] == "top_right":
            colors = [neutral_color, comparator_color][: len(counts)] or [neutral_color]
        else:
            default_palette = [model_color, audit_color, light_fill, comparator_color]
            colors = default_palette[: len(counts)]
            if len(colors) < len(counts):
                colors.extend([default_palette[-1]] * (len(counts) - len(colors)))
        bars = axes.bar(labels, counts, color=colors, edgecolor="none")
        axes.set_title(str(panel["title"]), fontsize=max(axis_title_size - 1.0, 9.8), fontweight="bold", color=neutral_color, pad=8)
        axes.set_ylabel(
            str(display_payload.get("coverage_y_label") or "").strip(),
            fontsize=max(axis_title_size - 2.0, 9.0),
            color=neutral_color,
        )
        axes.grid(axis="y", linestyle=":", color=light_fill, zorder=0)
        if panel["layout_role"] == "wide_left":
            axes.tick_params(axis="x", rotation=45, labelsize=max(tick_size - 2.0, 8.0), colors=neutral_color)
        else:
            axes.tick_params(axis="x", labelsize=max(tick_size - 2.0, 8.0), colors=neutral_color)
        axes.tick_params(axis="y", labelsize=max(tick_size - 1.0, 8.5), colors=neutral_color)
        _apply_publication_axes_style(axes)
        upper = max(counts, default=0)
        y_offset = upper * 0.02 if upper > 0 else 0.0
        for idx, value in enumerate(counts):
            axes.text(
                idx,
                value + y_offset,
                f"{value:,}",
                ha="center",
                va="bottom",
                fontsize=max(tick_size - 2.0, 8.0),
                color=neutral_color,
            )
        for idx, artist in enumerate(bars, start=1):
            coverage_bar_artists.append((f"{panel['panel_id']}_{idx}", artist))

    subplot_left = 0.08
    subplot_right = 0.97
    subplot_bottom = 0.10
    subplot_top = 0.90 if show_figure_title else 0.95
    fig.subplots_adjust(top=subplot_top, bottom=subplot_bottom, left=subplot_left, right=subplot_right)
    fig.canvas.draw()
    for _ in range(3):
        renderer = fig.canvas.get_renderer()
        legend_bbox = legend.get_window_extent(renderer=renderer)
        overflow_px = float(legend_bbox.y1 - fig.bbox.height)
        if overflow_px <= 0.0:
            break
        min_top = 0.82 if show_figure_title else 0.88
        top_delta = overflow_px / max(float(fig.bbox.height), 1.0)
        next_top = max(min_top, subplot_top - top_delta - 0.01)
        if next_top >= subplot_top - 1e-6:
            break
        subplot_top = next_top
        fig.subplots_adjust(top=subplot_top, bottom=subplot_bottom, left=subplot_left, right=subplot_right)
        fig.canvas.draw()

    renderer = fig.canvas.get_renderer()
    center_panel_bbox = matplotlib.transforms.Bbox.union(
        [
            center_axes.get_window_extent(renderer=renderer),
            center_axes.title.get_window_extent(renderer=renderer),
        ]
    )
    region_panel_bbox = matplotlib.transforms.Bbox.union(
        [
            region_axes.get_window_extent(renderer=renderer),
            region_axes.title.get_window_extent(renderer=renderer),
        ]
    )
    right_stack_bbox = matplotlib.transforms.Bbox.union(
        [
            north_south_axes.get_window_extent(renderer=renderer),
            urban_rural_axes.get_window_extent(renderer=renderer),
            north_south_axes.title.get_window_extent(renderer=renderer),
        ]
    )

    def _add_figure_panel_label(*, panel_bbox, label: str) -> Any:
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.014, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.008), 0.015)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 2.6, 15.0),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    center_panel_label = _add_figure_panel_label(panel_bbox=center_panel_bbox, label="A")
    wide_left_panel_label = _add_figure_panel_label(panel_bbox=region_panel_bbox, label="B")
    right_stack_panel_label = _add_figure_panel_label(panel_bbox=right_stack_bbox, label="C")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=center_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="center_event_y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=center_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="center_event_x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=region_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="coverage_y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=center_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_A",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=wide_left_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_B",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_stack_panel_label.get_window_extent(renderer=renderer),
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
    for index, artist in enumerate(center_bars, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"center_event_bar_{index}",
                box_type="center_event_bar",
            )
        )
    for box_suffix, artist in coverage_bar_artists:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"coverage_bar_{box_suffix}",
                box_type="coverage_bar",
            )
        )
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=center_panel_bbox,
                    box_id="center_event_panel",
                    box_type="center_event_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=region_panel_bbox,
                    box_id="coverage_panel_wide_left",
                    box_type="coverage_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=north_south_axes.get_window_extent(renderer=renderer),
                    box_id="coverage_panel_top_right",
                    box_type="coverage_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=urban_rural_axes.get_window_extent(renderer=renderer),
                    box_id="coverage_panel_bottom_right",
                    box_type="coverage_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=right_stack_bbox,
                    box_id="coverage_panel_right_stack",
                    box_type="coverage_panel",
                ),
            ],
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "center_event_counts": center_event_counts,
                "coverage_panels": coverage_panels,
                "center_label_mode": center_label_mode,
                "center_tick_labels": center_tick_labels,
                "center_axis_title": center_axis_title,
                "legend_title": "Split",
                "legend_labels": ["Train", "Validation"],
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
