from __future__ import annotations

from pathlib import Path
import re
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ..shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _centered_offsets,
    _data_box_to_layout_box,
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    _wrap_flow_text_to_width,
    dump_json,
)

def _render_python_compact_effect_estimate_panel(
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
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    interval_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    grid_color = str(palette.get("secondary_soft") or "#dbe4ee").strip() or "#dbe4ee"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    reference_value = float(display_payload["reference_value"])
    row_count = max((len(panel.get("rows") or []) for panel in panels), default=1)
    all_x_values = [reference_value]
    for panel in panels:
        for row in panel["rows"]:
            all_x_values.extend((float(row["lower"]), float(row["estimate"]), float(row["upper"])))
    x_min = min(all_x_values)
    x_max = max(all_x_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.16, 0.08)
    x_lower = max(0.0, x_min - x_padding) if x_min >= 0.0 else x_min - x_padding
    x_upper = x_max + x_padding
    reference_half_width = max((x_upper - x_lower) * 0.003, 0.0015)
    estimate_half_width = max((x_upper - x_lower) * 0.010, 0.015)
    estimate_half_height = 0.11
    ci_half_height = 0.028

    figure_width = max(8.8, 3.4 * len(panels) + 1.8)
    figure_height = max(4.8, 0.58 * row_count + 2.6)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, figure_height), squeeze=False)
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
    for axes_item, panel in zip(axes_list, panels, strict=True):
        row_label_artists: list[Any] = []
        blended_transform = matplotlib.transforms.blended_transform_factory(axes_item.transAxes, axes_item.transData)
        for row_index, row in enumerate(panel["rows"]):
            y_pos = float(row_index)
            lower = float(row["lower"])
            estimate = float(row["estimate"])
            upper = float(row["upper"])
            axes_item.plot(
                [lower, upper],
                [y_pos, y_pos],
                color=interval_color,
                linewidth=2.0,
                solid_capstyle="round",
                zorder=2,
            )
            axes_item.scatter(
                [estimate],
                [y_pos],
                s=marker_size**2,
                color=model_color,
                edgecolors="white",
                linewidths=0.8,
                zorder=4,
            )
            row_label_artists.append(
                axes_item.text(
                    -0.06,
                    y_pos,
                    str(row["row_label"]),
                    transform=blended_transform,
                    ha="right",
                    va="center",
                    fontsize=max(tick_size - 0.5, 8.2),
                    color="#334155",
                    clip_on=False,
                )
            )
            if row.get("support_n") is not None:
                axes_item.text(
                    0.98,
                    y_pos,
                    f"n={int(row['support_n'])}",
                    transform=blended_transform,
                    ha="right",
                    va="center",
                    fontsize=max(tick_size - 1.0, 7.8),
                    color="#64748b",
                    clip_on=False,
                )

        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=1,
        )
        axes_item.set_xlim(x_lower, x_upper)
        axes_item.set_ylim(-0.6, row_count - 0.4)
        axes_item.invert_yaxis()
        axes_item.set_yticks([])
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
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
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#334155")
        axes_item.grid(axis="x", linestyle=":", color=grid_color, linewidth=0.65, zorder=0)
        _apply_publication_axes_style(axes_item)

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "panel_title_artist": axes_item.title,
                "row_label_artists": row_label_artists,
            }
        )

    top_margin = 0.82 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.14, right=0.97, top=top_margin, bottom=0.24, wspace=0.42)
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
    guide_boxes: list[dict[str, Any]] = []
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

        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["panel_title_artist"].get_window_extent(renderer=renderer),
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
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
            ]
        )

        reference_line_box_id = f"reference_line_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=reference_value - reference_half_width,
                y0=-0.5,
                x1=reference_value + reference_half_width,
                y1=row_count - 0.5,
                box_id=reference_line_box_id,
                box_type="reference_line",
            )
        )

        normalized_rows: list[dict[str, Any]] = []
        for row_index, (row, row_label_artist) in enumerate(zip(panel["rows"], record["row_label_artists"], strict=True), start=1):
            y_pos = float(row_index - 1)
            label_box_id = f"row_label_{panel_token}_{row_index}"
            estimate_box_id = f"estimate_{panel_token}_{row_index}"
            ci_box_id = f"ci_{panel_token}_{row_index}"
            layout_boxes.extend(
                [
                    _bbox_to_layout_box(
                        figure=fig,
                        bbox=row_label_artist.get_window_extent(renderer=renderer),
                        box_id=label_box_id,
                        box_type="row_label",
                    ),
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=float(row["estimate"]) - estimate_half_width,
                        y0=y_pos - estimate_half_height,
                        x1=float(row["estimate"]) + estimate_half_width,
                        y1=y_pos + estimate_half_height,
                        box_id=estimate_box_id,
                        box_type="estimate_marker",
                    ),
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=float(row["lower"]),
                        y0=y_pos - ci_half_height,
                        x1=float(row["upper"]),
                        y1=y_pos + ci_half_height,
                        box_id=ci_box_id,
                        box_type="ci_segment",
                    ),
                ]
            )
            normalized_row = {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "estimate": float(row["estimate"]),
                "lower": float(row["lower"]),
                "upper": float(row["upper"]),
                "label_box_id": label_box_id,
                "estimate_box_id": estimate_box_id,
                "ci_box_id": ci_box_id,
            }
            if row.get("support_n") is not None:
                normalized_row["support_n"] = int(row["support_n"])
            normalized_rows.append(normalized_row)

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "panel_box_id": panel_box_id,
                "panel_label_box_id": f"panel_label_{panel_token}",
                "panel_title_box_id": f"panel_title_{panel_token}",
                "x_axis_title_box_id": f"x_axis_title_{panel_token}",
                "reference_line_box_id": reference_line_box_id,
                "rows": normalized_rows,
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
                "reference_value": reference_value,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_coefficient_path_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    coefficient_rows = list(display_payload.get("coefficient_rows") or [])
    steps = list(display_payload.get("steps") or [])
    summary_cards = list(display_payload.get("summary_cards") or [])
    if not coefficient_rows or not steps or not summary_cards:
        raise RuntimeError(f"{template_id} requires non-empty coefficient_rows, steps, and summary_cards")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.8))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    accent_colors = [
        comparator_color,
        model_color,
        str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed",
        str(palette.get("secondary_soft") or "#0f766e").strip() or "#0f766e",
        str(palette.get("primary") or "#b45309").strip() or "#b45309",
    ]
    step_color_lookup = {
        str(step["step_id"]): accent_colors[index % len(accent_colors)] for index, step in enumerate(steps)
    }

    reference_value = float(display_payload["reference_value"])
    all_x_values = [reference_value]
    for row in coefficient_rows:
        for point in list(row.get("points") or []):
            all_x_values.extend((float(point["lower"]), float(point["estimate"]), float(point["upper"])))
    x_min = min(all_x_values)
    x_max = max(all_x_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.08)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    interval_half_height = 0.030
    marker_half_height = 0.095
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.015)
    reference_half_width = max((x_upper - x_lower) * 0.003, 0.0015)
    row_count = len(coefficient_rows)
    figure_height = max(5.0, 0.82 * row_count + 2.1)
    fig, (path_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(10.8, figure_height),
        gridspec_kw={"width_ratios": [2.7, 1.25]},
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
            color="#13293d",
            y=0.985,
        )

    path_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("path_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.20,
        font_size=axis_title_size,
        font_weight="bold",
    )
    x_axis_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.36,
        font_size=axis_title_size,
        font_weight="bold",
    )
    path_axes.set_title("\n".join(path_title_lines), fontsize=axis_title_size, fontweight="bold", color="#334155", pad=12.0)
    path_axes.set_xlabel("\n".join(x_axis_title_lines), fontsize=axis_title_size, fontweight="bold", color="#13293d")
    path_axes.axvline(reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    path_axes.set_xlim(x_lower, x_upper)
    path_axes.set_ylim(-0.6, row_count - 0.4)
    path_axes.invert_yaxis()
    path_axes.set_yticks([])
    path_axes.tick_params(axis="x", labelsize=tick_size, colors="#334155")
    path_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(path_axes)

    row_label_artists: list[Any] = []
    point_records: list[dict[str, Any]] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(path_axes.transAxes, path_axes.transData)
    row_offsets = _centered_offsets(len(steps), half_span=0.22 if len(steps) <= 3 else 0.27)
    step_order_lookup = {str(step["step_id"]): index for index, step in enumerate(steps)}
    for row_index, row in enumerate(coefficient_rows):
        y_center = float(row_index)
        row_label_artists.append(
            path_axes.text(
                -0.03,
                y_center,
                str(row["row_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color="#334155",
                clip_on=False,
            )
        )
        ordered_points = sorted(
            list(row.get("points") or []),
            key=lambda item: step_order_lookup[str(item["step_id"])],
        )
        path_x = [float(point["estimate"]) for point in ordered_points]
        path_y = [y_center + row_offsets[index] for index in range(len(ordered_points))]
        path_axes.plot(
            path_x,
            path_y,
            color="#94a3b8",
            linewidth=1.0,
            alpha=0.85,
            zorder=2,
        )
        normalized_points: list[dict[str, Any]] = []
        for point_index, point in enumerate(ordered_points):
            step_id = str(point["step_id"])
            point_y = y_center + row_offsets[point_index]
            point_color = step_color_lookup[step_id]
            path_axes.plot(
                [float(point["lower"]), float(point["upper"])],
                [point_y, point_y],
                color=point_color,
                linewidth=2.1,
                solid_capstyle="round",
                zorder=3,
            )
            path_axes.scatter(
                [float(point["estimate"])],
                [point_y],
                s=marker_size**2,
                color=point_color,
                edgecolors="white",
                linewidths=0.8,
                zorder=4,
            )
            normalized_point = {
                "step_id": step_id,
                "estimate": float(point["estimate"]),
                "lower": float(point["lower"]),
                "upper": float(point["upper"]),
                "plot_y": float(point_y),
            }
            if point.get("support_n") is not None:
                normalized_point["support_n"] = int(point["support_n"])
            normalized_points.append(normalized_point)
        point_records.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "points": normalized_points,
            }
        )

    legend_handles = [
        matplotlib.lines.Line2D(
            [0.0],
            [0.0],
            color=step_color_lookup[str(step["step_id"])],
            linewidth=2.0,
            marker="o",
            markersize=max(marker_size + 1.0, 5.5),
            markerfacecolor=step_color_lookup[str(step["step_id"])],
            markeredgecolor="white",
            label=str(step["step_label"]),
        )
        for step in steps
    ]
    legend = path_axes.legend(
        handles=legend_handles,
        title=str(display_payload.get("step_legend_title") or "").strip(),
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0.0, -0.14),
        ncol=min(len(steps), 3),
        columnspacing=1.2,
        handletextpad=0.6,
        borderaxespad=0.0,
        fontsize=max(tick_size - 0.4, 8.8),
        title_fontsize=max(axis_title_size - 0.6, 9.4),
    )

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=12.0,
    )
    summary_axes.set_xlim(0.0, 1.0)
    summary_axes.set_ylim(0.0, 1.0)
    summary_axes.set_xticks([])
    summary_axes.set_yticks([])
    for spine in summary_axes.spines.values():
        spine.set_visible(False)
    summary_axes.set_facecolor("white")

    summary_card_artists: list[dict[str, Any]] = []
    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18
    top_y = 0.87
    bottom_y = 0.08
    gap = 0.035
    card_height = (top_y - bottom_y - gap * max(len(summary_cards) - 1, 0)) / float(len(summary_cards))
    for card_index, card in enumerate(summary_cards):
        card_top = top_y - card_index * (card_height + gap)
        card_bottom = card_top - card_height
        card_patch = matplotlib.patches.FancyBboxPatch(
            (0.05, card_bottom),
            0.90,
            card_height,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            transform=summary_axes.transAxes,
            facecolor=str(palette.get("light") or "#f8fafc").strip() or "#f8fafc",
            edgecolor=str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1",
            linewidth=1.0,
            zorder=1,
        )
        summary_axes.add_patch(card_patch)

        label_lines = _wrap_flow_text_to_width(
            str(card["label"]),
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 0.2, 8.8),
            font_weight="bold",
        )
        value_lines = _wrap_flow_text_to_width(
            str(card["value"]),
            max_width_pt=summary_text_width_pt,
            font_size=max(axis_title_size - 0.8, 9.2),
            font_weight="bold",
        )
        detail_text = str(card.get("detail") or "").strip()
        detail_lines = _wrap_flow_text_to_width(
            detail_text,
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 1.0, 7.8),
            font_weight="normal",
        )

        label_artist = summary_axes.text(
            0.10,
            card_top - card_height * 0.18,
            "\n".join(label_lines),
            transform=summary_axes.transAxes,
            ha="left",
            va="top",
            fontsize=max(tick_size - 0.2, 8.8),
            fontweight="bold",
            color="#334155",
            zorder=2,
        )
        value_artist = summary_axes.text(
            0.10,
            card_top - card_height * 0.48,
            "\n".join(value_lines),
            transform=summary_axes.transAxes,
            ha="left",
            va="top",
            fontsize=max(axis_title_size - 0.8, 9.2),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        if detail_lines:
            detail_artist = summary_axes.text(
                0.10,
                card_top - card_height * 0.74,
                "\n".join(detail_lines),
                transform=summary_axes.transAxes,
                ha="left",
                va="top",
                fontsize=max(tick_size - 1.0, 7.8),
                color="#64748b",
                zorder=2,
            )
        summary_card_artists.append(
            {
                "card_id": str(card["card_id"]),
                "label": str(card["label"]),
                "value": str(card["value"]),
                "detail": detail_text,
                "label_artist": label_artist,
                "value_artist": value_artist,
                "detail_artist": detail_artist,
            }
        )

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.22, right=0.97, top=top_margin, bottom=0.24, wspace=0.16)
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

    panel_label_a = _add_panel_label(axes_item=path_axes, label="A")
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
                bbox=path_axes.title.get_window_extent(renderer=renderer),
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
            _bbox_to_layout_box(
                figure=fig,
                bbox=path_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    legend_title = legend.get_title()
    if legend_title.get_text().strip():
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_title.get_window_extent(renderer=renderer),
                box_id="step_legend_title",
                box_type="legend_title",
            )
        )
    legend_texts = list(legend.get_texts())
    normalized_steps: list[dict[str, Any]] = []
    for step, legend_text in zip(steps, legend_texts, strict=True):
        legend_box_id = f"step_legend_{step['step_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_text.get_window_extent(renderer=renderer),
                box_id=legend_box_id,
                box_type="legend_label",
            )
        )
        normalized_steps.append(
            {
                "step_id": str(step["step_id"]),
                "step_label": str(step["step_label"]),
                "step_order": int(step["step_order"]),
                "legend_label_box_id": legend_box_id,
            }
        )

    normalized_rows: list[dict[str, Any]] = []
    for row_index, (row, row_label_artist, row_record) in enumerate(
        zip(coefficient_rows, row_label_artists, point_records, strict=True),
        start=1,
    ):
        label_box_id = f"coefficient_row_{row['row_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=row_label_artist.get_window_extent(renderer=renderer),
                box_id=label_box_id,
                box_type="coefficient_row_label",
            )
        )
        normalized_points: list[dict[str, Any]] = []
        for point in row_record["points"]:
            step_id = str(point["step_id"])
            marker_box_id = f"marker_{row['row_id']}_{step_id}"
            interval_box_id = f"interval_{row['row_id']}_{step_id}"
            layout_boxes.extend(
                [
                    _data_box_to_layout_box(
                        axes=path_axes,
                        figure=fig,
                        x0=float(point["estimate"]) - marker_half_width,
                        y0=float(point["plot_y"]) - marker_half_height,
                        x1=float(point["estimate"]) + marker_half_width,
                        y1=float(point["plot_y"]) + marker_half_height,
                        box_id=marker_box_id,
                        box_type="coefficient_marker",
                    ),
                    _data_box_to_layout_box(
                        axes=path_axes,
                        figure=fig,
                        x0=float(point["lower"]),
                        y0=float(point["plot_y"]) - interval_half_height,
                        x1=float(point["upper"]),
                        y1=float(point["plot_y"]) + interval_half_height,
                        box_id=interval_box_id,
                        box_type="coefficient_interval",
                    ),
                ]
            )
            normalized_point = {
                "step_id": step_id,
                "estimate": float(point["estimate"]),
                "lower": float(point["lower"]),
                "upper": float(point["upper"]),
                "marker_box_id": marker_box_id,
                "interval_box_id": interval_box_id,
            }
            if point.get("support_n") is not None:
                normalized_point["support_n"] = int(point["support_n"])
            normalized_points.append(normalized_point)
        normalized_rows.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "label_box_id": label_box_id,
                "points": normalized_points,
            }
        )

    normalized_summary_cards: list[dict[str, Any]] = []
    for artist_record in summary_card_artists:
        label_box_id = f"summary_label_{artist_record['card_id']}"
        value_box_id = f"summary_value_{artist_record['card_id']}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=artist_record["label_artist"].get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="summary_card_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=artist_record["value_artist"].get_window_extent(renderer=renderer),
                    box_id=value_box_id,
                    box_type="summary_card_value",
                ),
            ]
        )
        normalized_card = {
            "card_id": artist_record["card_id"],
            "label": artist_record["label"],
            "value": artist_record["value"],
            "label_box_id": label_box_id,
            "value_box_id": value_box_id,
        }
        detail_artist = artist_record["detail_artist"]
        if detail_artist is not None:
            detail_box_id = f"summary_detail_{artist_record['card_id']}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=detail_artist.get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="summary_card_detail",
                )
            )
            normalized_card["detail"] = artist_record["detail"]
            normalized_card["detail_box_id"] = detail_box_id
        normalized_summary_cards.append(normalized_card)

    reference_line_box_id = "reference_line"
    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=path_axes.get_window_extent(renderer=renderer),
            box_id="path_panel",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="summary_panel",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _data_box_to_layout_box(
            axes=path_axes,
            figure=fig,
            x0=reference_value - reference_half_width,
            y0=-0.5,
            x1=reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id=reference_line_box_id,
            box_type="reference_line",
        )
    ]

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "reference_value": reference_value,
                "path_panel": {
                    "panel_box_id": "path_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": reference_line_box_id,
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "step_legend_title_box_id": "step_legend_title",
                "steps": normalized_steps,
                "coefficient_rows": normalized_rows,
                "summary_cards": normalized_summary_cards,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_broader_heterogeneity_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    effect_rows = list(display_payload.get("effect_rows") or [])
    slices = sorted(list(display_payload.get("slices") or []), key=lambda item: int(item["slice_order"]))
    if not effect_rows or not slices:
        raise RuntimeError(f"{template_id} requires non-empty effect_rows and slices")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.8))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    accent_colors = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed",
        str(palette.get("secondary_soft") or "#0f766e").strip() or "#0f766e",
        str(palette.get("primary") or "#b45309").strip() or "#b45309",
    ]
    slice_color_lookup = {
        str(slice_item["slice_id"]): accent_colors[index % len(accent_colors)] for index, slice_item in enumerate(slices)
    }

    reference_value = float(display_payload["reference_value"])
    all_x_values = [reference_value]
    for row in effect_rows:
        for estimate in list(row.get("slice_estimates") or []):
            all_x_values.extend((float(estimate["lower"]), float(estimate["estimate"]), float(estimate["upper"])))
    x_min = min(all_x_values)
    x_max = max(all_x_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.08)
    x_lower = max(0.0, x_min - x_padding) if x_min >= 0.0 else x_min - x_padding
    x_upper = x_max + x_padding
    interval_half_height = 0.030
    marker_half_height = 0.095
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.015)
    reference_half_width = max((x_upper - x_lower) * 0.003, 0.0015)

    row_count = len(effect_rows)
    figure_height = max(5.0, 0.82 * row_count + 2.2)
    fig, (matrix_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(10.8, figure_height),
        gridspec_kw={"width_ratios": [2.75, 1.35]},
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
            color="#13293d",
            y=0.985,
        )

    matrix_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("matrix_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.20,
        font_size=axis_title_size,
        font_weight="bold",
    )
    x_axis_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )

    matrix_axes.set_title(
        "\n".join(matrix_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=12.0,
    )
    matrix_axes.set_xlabel(
        "\n".join(x_axis_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    matrix_axes.axvline(reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    matrix_axes.set_xlim(x_lower, x_upper)
    matrix_axes.set_ylim(-0.6, row_count - 0.4)
    matrix_axes.invert_yaxis()
    matrix_axes.set_yticks([])
    matrix_axes.tick_params(axis="x", labelsize=tick_size, colors="#334155")
    matrix_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(matrix_axes)

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
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

    row_label_artists: list[Any] = []
    estimate_records: list[dict[str, Any]] = []
    verdict_records: list[dict[str, Any]] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(matrix_axes.transAxes, matrix_axes.transData)
    slice_offsets = _centered_offsets(len(slices), half_span=0.22 if len(slices) <= 3 else 0.27)
    slice_order_lookup = {str(slice_item["slice_id"]): index for index, slice_item in enumerate(slices)}

    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18
    row_band_height = 0.56
    for row_index, row in enumerate(effect_rows):
        y_center = float(row_index)
        row_label_artists.append(
            matrix_axes.text(
                -0.03,
                y_center,
                str(row["row_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color="#334155",
                clip_on=False,
            )
        )
        ordered_estimates = sorted(
            list(row.get("slice_estimates") or []),
            key=lambda item: slice_order_lookup[str(item["slice_id"])],
        )
        normalized_slice_estimates: list[dict[str, Any]] = []
        for estimate_index, estimate in enumerate(ordered_estimates):
            slice_id = str(estimate["slice_id"])
            plot_y = y_center + slice_offsets[estimate_index]
            slice_color = slice_color_lookup[slice_id]
            matrix_axes.plot(
                [float(estimate["lower"]), float(estimate["upper"])],
                [plot_y, plot_y],
                color=slice_color,
                linewidth=2.1,
                solid_capstyle="round",
                zorder=3,
            )
            matrix_axes.scatter(
                [float(estimate["estimate"])],
                [plot_y],
                s=marker_size**2,
                color=slice_color,
                edgecolors="white",
                linewidths=0.8,
                zorder=4,
            )
            normalized_estimate = {
                "slice_id": slice_id,
                "estimate": float(estimate["estimate"]),
                "lower": float(estimate["lower"]),
                "upper": float(estimate["upper"]),
                "plot_y": float(plot_y),
            }
            if estimate.get("support_n") is not None:
                normalized_estimate["support_n"] = int(estimate["support_n"])
            normalized_slice_estimates.append(normalized_estimate)
        estimate_records.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "verdict": str(row["verdict"]),
                "detail": str(row.get("detail") or "").strip(),
                "slice_estimates": normalized_slice_estimates,
            }
        )

        band_bottom = y_center - row_band_height / 2.0
        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.05, band_bottom),
            0.90,
            row_band_height,
            boxstyle="round,pad=0.010,rounding_size=0.015",
            transform=summary_axes.transData,
            facecolor=str(palette.get("light") or "#f8fafc").strip() or "#f8fafc",
            edgecolor=str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1",
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        verdict_lines = _wrap_flow_text_to_width(
            str(row["verdict"]).replace("_", " "),
            max_width_pt=summary_text_width_pt,
            font_size=max(axis_title_size - 0.8, 9.2),
            font_weight="bold",
        )
        detail_text = str(row.get("detail") or "").strip()
        detail_lines = _wrap_flow_text_to_width(
            detail_text,
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 1.0, 7.8),
            font_weight="normal",
        )
        verdict_artist = summary_axes.text(
            0.10,
            y_center - 0.11,
            "\n".join(verdict_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(axis_title_size - 0.8, 9.2),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        if detail_lines:
            detail_artist = summary_axes.text(
                0.10,
                y_center + 0.10,
                "\n".join(detail_lines),
                transform=summary_axes.transData,
                ha="left",
                va="center",
                fontsize=max(tick_size - 1.0, 7.8),
                color="#64748b",
                zorder=2,
            )
        verdict_records.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "verdict": str(row["verdict"]),
                "detail": detail_text,
                "verdict_artist": verdict_artist,
                "detail_artist": detail_artist,
            }
        )

    legend_handles = [
        matplotlib.lines.Line2D(
            [0.0],
            [0.0],
            color=slice_color_lookup[str(slice_item["slice_id"])],
            linewidth=2.0,
            marker="o",
            markersize=max(marker_size + 1.0, 5.5),
            markerfacecolor=slice_color_lookup[str(slice_item["slice_id"])],
            markeredgecolor="white",
            label=str(slice_item["slice_label"]),
        )
        for slice_item in slices
    ]
    legend = matrix_axes.legend(
        handles=legend_handles,
        title=str(display_payload.get("slice_legend_title") or "").strip(),
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0.0, -0.14),
        ncol=min(len(slices), 3),
        columnspacing=1.2,
        handletextpad=0.6,
        borderaxespad=0.0,
        fontsize=max(tick_size - 0.4, 8.8),
        title_fontsize=max(axis_title_size - 0.6, 9.4),
    )

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.22, right=0.97, top=top_margin, bottom=0.24, wspace=0.16)
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

    panel_label_a = _add_panel_label(axes_item=matrix_axes, label="A")
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
                bbox=matrix_axes.title.get_window_extent(renderer=renderer),
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
            _bbox_to_layout_box(
                figure=fig,
                bbox=matrix_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    legend_title = legend.get_title()
    if legend_title.get_text().strip():
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_title.get_window_extent(renderer=renderer),
                box_id="slice_legend_title",
                box_type="legend_title",
            )
        )
    legend_texts = list(legend.get_texts())
    normalized_slices: list[dict[str, Any]] = []
    for slice_item, legend_text in zip(slices, legend_texts, strict=True):
        legend_box_id = f"slice_legend_{slice_item['slice_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_text.get_window_extent(renderer=renderer),
                box_id=legend_box_id,
                box_type="legend_label",
            )
        )
        normalized_slices.append(
            {
                "slice_id": str(slice_item["slice_id"]),
                "slice_label": str(slice_item["slice_label"]),
                "slice_kind": str(slice_item["slice_kind"]),
                "slice_order": int(slice_item["slice_order"]),
                "legend_label_box_id": legend_box_id,
            }
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="matrix_panel",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="summary_panel",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _data_box_to_layout_box(
            axes=matrix_axes,
            figure=fig,
            x0=reference_value - reference_half_width,
            y0=-0.5,
            x1=reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id="reference_line",
            box_type="reference_line",
        )
    ]

    normalized_effect_rows: list[dict[str, Any]] = []
    for row_record, row_label_artist, verdict_record in zip(
        estimate_records,
        row_label_artists,
        verdict_records,
        strict=True,
    ):
        row_label_box_id = f"row_label_{row_record['row_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=row_label_artist.get_window_extent(renderer=renderer),
                box_id=row_label_box_id,
                box_type="row_label",
            )
        )
        verdict_box_id = f"verdict_{row_record['row_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=verdict_record["verdict_artist"].get_window_extent(renderer=renderer),
                box_id=verdict_box_id,
                box_type="verdict_value",
            )
        )
        detail_box_id = ""
        if verdict_record["detail_artist"] is not None:
            detail_box_id = f"detail_{row_record['row_id']}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=verdict_record["detail_artist"].get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="verdict_detail",
                )
            )

        normalized_slice_estimates: list[dict[str, Any]] = []
        for estimate in row_record["slice_estimates"]:
            slice_id = str(estimate["slice_id"])
            marker_box_id = f"estimate_{row_record['row_id']}_{slice_id}"
            interval_box_id = f"ci_{row_record['row_id']}_{slice_id}"
            layout_boxes.extend(
                [
                    _data_box_to_layout_box(
                        axes=matrix_axes,
                        figure=fig,
                        x0=float(estimate["estimate"]) - marker_half_width,
                        y0=float(estimate["plot_y"]) - marker_half_height,
                        x1=float(estimate["estimate"]) + marker_half_width,
                        y1=float(estimate["plot_y"]) + marker_half_height,
                        box_id=marker_box_id,
                        box_type="estimate_marker",
                    ),
                    _data_box_to_layout_box(
                        axes=matrix_axes,
                        figure=fig,
                        x0=float(estimate["lower"]),
                        y0=float(estimate["plot_y"]) - interval_half_height,
                        x1=float(estimate["upper"]),
                        y1=float(estimate["plot_y"]) + interval_half_height,
                        box_id=interval_box_id,
                        box_type="ci_segment",
                    ),
                ]
            )
            normalized_estimate = {
                "slice_id": slice_id,
                "estimate": float(estimate["estimate"]),
                "lower": float(estimate["lower"]),
                "upper": float(estimate["upper"]),
                "marker_box_id": marker_box_id,
                "interval_box_id": interval_box_id,
            }
            if estimate.get("support_n") is not None:
                normalized_estimate["support_n"] = int(estimate["support_n"])
            normalized_slice_estimates.append(normalized_estimate)

        normalized_row = {
            "row_id": str(row_record["row_id"]),
            "row_label": str(row_record["row_label"]),
            "verdict": str(row_record["verdict"]),
            "label_box_id": row_label_box_id,
            "verdict_box_id": verdict_box_id,
            "slice_estimates": normalized_slice_estimates,
        }
        detail_text = str(row_record.get("detail") or "").strip()
        if detail_text:
            normalized_row["detail"] = detail_text
        if detail_box_id:
            normalized_row["detail_box_id"] = detail_box_id
        normalized_effect_rows.append(normalized_row)

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "reference_value": reference_value,
                "matrix_panel": {
                    "panel_box_id": "matrix_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "slice_legend_title_box_id": "slice_legend_title",
                "slices": normalized_slices,
                "effect_rows": normalized_effect_rows,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_interaction_effect_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    modifiers = list(display_payload.get("modifiers") or [])
    if not modifiers:
        raise RuntimeError(f"{template_id} requires non-empty modifiers")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.8))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    light_fill = str(palette.get("light") or "#f8fafc").strip() or "#f8fafc"
    summary_fill = str(palette.get("secondary_soft") or "#e2e8f0").strip() or "#e2e8f0"

    reference_value = float(display_payload["reference_value"])
    all_x_values = [reference_value]
    for modifier in modifiers:
        all_x_values.extend(
            (
                float(modifier["lower"]),
                float(modifier["interaction_estimate"]),
                float(modifier["upper"]),
            )
        )
    x_min = min(all_x_values)
    x_max = max(all_x_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.06)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    interval_half_height = 0.030
    marker_half_height = 0.095
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.015)
    reference_half_width = max((x_upper - x_lower) * 0.003, 0.0015)

    row_count = len(modifiers)
    figure_height = max(4.9, 0.82 * row_count + 2.0)
    fig, (estimate_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(10.6, figure_height),
        gridspec_kw={"width_ratios": [2.70, 1.25]},
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
            color="#13293d",
            y=0.985,
        )

    estimate_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("estimate_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.20,
        font_size=axis_title_size,
        font_weight="bold",
    )
    x_axis_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.36,
        font_size=axis_title_size,
        font_weight="bold",
    )

    estimate_axes.set_title(
        "\n".join(estimate_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=12.0,
    )
    estimate_axes.set_xlabel(
        "\n".join(x_axis_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    estimate_axes.axvline(reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    estimate_axes.set_xlim(x_lower, x_upper)
    estimate_axes.set_ylim(-0.6, row_count - 0.4)
    estimate_axes.invert_yaxis()
    estimate_axes.set_yticks([])
    estimate_axes.tick_params(axis="x", labelsize=tick_size, colors="#334155")
    estimate_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(estimate_axes)

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
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

    verdict_color_lookup = {
        "credible": comparator_color,
        "suggestive": "#b45309",
        "uncertain": "#475569",
    }

    def _format_interaction_p_value(value: float) -> str:
        if value < 0.001:
            return "<0.001"
        return f"{value:.3f}"

    row_label_artists: list[Any] = []
    support_label_artists: list[Any] = []
    verdict_artists: list[Any] = []
    detail_artists: list[Any] = []
    normalized_modifier_records: list[dict[str, Any]] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(estimate_axes.transAxes, estimate_axes.transData)

    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18
    row_band_height = 0.56
    for row_index, modifier in enumerate(modifiers):
        y_center = float(row_index)
        row_label_artists.append(
            estimate_axes.text(
                -0.03,
                y_center,
                str(modifier["modifier_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color="#334155",
                clip_on=False,
            )
        )
        estimate_axes.plot(
            [float(modifier["lower"]), float(modifier["upper"])],
            [y_center, y_center],
            color=comparator_color,
            linewidth=2.1,
            solid_capstyle="round",
            zorder=3,
        )
        estimate_axes.scatter(
            [float(modifier["interaction_estimate"])],
            [y_center],
            s=marker_size**2,
            color=model_color,
            edgecolors="white",
            linewidths=0.8,
            zorder=4,
        )
        support_label_artists.append(
            estimate_axes.text(
                0.98,
                y_center,
                f"n={int(modifier['support_n'])}",
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 1.0, 7.8),
                color="#64748b",
                clip_on=False,
            )
        )

        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.04, y_center - row_band_height / 2.0),
            0.92,
            row_band_height,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            transform=summary_axes.transData,
            facecolor=light_fill,
            edgecolor=summary_fill,
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        verdict_artist = summary_axes.text(
            0.10,
            y_center - 0.10,
            str(modifier["verdict"]).replace("_", " ").title(),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(axis_title_size - 0.9, 9.0),
            fontweight="bold",
            color=verdict_color_lookup.get(str(modifier["verdict"]), "#13293d"),
            zorder=2,
        )
        detail_text = (
            f"{str(modifier['favored_group_label'])}; "
            f"Pinteraction={_format_interaction_p_value(float(modifier['interaction_p_value']))}"
        )
        detail_lines = _wrap_flow_text_to_width(
            detail_text,
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 1.0, 7.8),
            font_weight="normal",
        )
        detail_artist = summary_axes.text(
            0.10,
            y_center + 0.10,
            "\n".join(detail_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 1.0, 7.8),
            color="#64748b",
            zorder=2,
        )
        verdict_artists.append(verdict_artist)
        detail_artists.append(detail_artist)
        normalized_modifier_records.append(
            {
                "modifier_id": str(modifier["modifier_id"]),
                "modifier_label": str(modifier["modifier_label"]),
                "interaction_estimate": float(modifier["interaction_estimate"]),
                "lower": float(modifier["lower"]),
                "upper": float(modifier["upper"]),
                "plot_y": float(y_center),
                "support_n": int(modifier["support_n"]),
                "favored_group_label": str(modifier["favored_group_label"]),
                "interaction_p_value": float(modifier["interaction_p_value"]),
                "verdict": str(modifier["verdict"]),
                "detail": detail_text,
            }
        )

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.74, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.23, right=0.97, top=top_margin, bottom=0.22, wspace=0.17)
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

    panel_label_a = _add_panel_label(axes_item=estimate_axes, label="A")
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
                bbox=estimate_axes.title.get_window_extent(renderer=renderer),
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
            _bbox_to_layout_box(
                figure=fig,
                bbox=estimate_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=estimate_axes.get_window_extent(renderer=renderer),
            box_id="estimate_panel",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="summary_panel",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _data_box_to_layout_box(
            axes=estimate_axes,
            figure=fig,
            x0=reference_value - reference_half_width,
            y0=-0.5,
            x1=reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id="reference_line",
            box_type="reference_line",
        )
    ]

    normalized_modifiers: list[dict[str, Any]] = []
    for modifier, row_label_artist, support_label_artist, verdict_artist, detail_artist in zip(
        normalized_modifier_records,
        row_label_artists,
        support_label_artists,
        verdict_artists,
        detail_artists,
        strict=True,
    ):
        modifier_id = str(modifier["modifier_id"])
        row_label_box_id = f"modifier_label_{modifier_id}"
        support_label_box_id = f"modifier_support_{modifier_id}"
        marker_box_id = f"estimate_{modifier_id}"
        interval_box_id = f"ci_{modifier_id}"
        verdict_box_id = f"verdict_{modifier_id}"
        detail_box_id = f"detail_{modifier_id}"
        plot_y = float(modifier["plot_y"])
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=row_label_artist.get_window_extent(renderer=renderer),
                    box_id=row_label_box_id,
                    box_type="row_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=support_label_artist.get_window_extent(renderer=renderer),
                    box_id=support_label_box_id,
                    box_type="support_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=verdict_artist.get_window_extent(renderer=renderer),
                    box_id=verdict_box_id,
                    box_type="verdict_value",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=detail_artist.get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="verdict_detail",
                ),
                _data_box_to_layout_box(
                    axes=estimate_axes,
                    figure=fig,
                    x0=float(modifier["interaction_estimate"]) - marker_half_width,
                    y0=plot_y - marker_half_height,
                    x1=float(modifier["interaction_estimate"]) + marker_half_width,
                    y1=plot_y + marker_half_height,
                    box_id=marker_box_id,
                    box_type="estimate_marker",
                ),
                _data_box_to_layout_box(
                    axes=estimate_axes,
                    figure=fig,
                    x0=float(modifier["lower"]),
                    y0=plot_y - interval_half_height,
                    x1=float(modifier["upper"]),
                    y1=plot_y + interval_half_height,
                    box_id=interval_box_id,
                    box_type="ci_segment",
                ),
            ]
        )
        normalized_modifiers.append(
            {
                "modifier_id": modifier_id,
                "modifier_label": str(modifier["modifier_label"]),
                "interaction_estimate": float(modifier["interaction_estimate"]),
                "lower": float(modifier["lower"]),
                "upper": float(modifier["upper"]),
                "support_n": int(modifier["support_n"]),
                "favored_group_label": str(modifier["favored_group_label"]),
                "interaction_p_value": float(modifier["interaction_p_value"]),
                "verdict": str(modifier["verdict"]),
                "detail": str(modifier["detail"]),
                "label_box_id": row_label_box_id,
                "support_label_box_id": support_label_box_id,
                "marker_box_id": marker_box_id,
                "interval_box_id": interval_box_id,
                "verdict_box_id": verdict_box_id,
                "detail_box_id": detail_box_id,
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
                "reference_value": reference_value,
                "estimate_panel": {
                    "panel_box_id": "estimate_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "modifiers": normalized_modifiers,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_center_transportability_governance_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    centers = list(display_payload.get("centers") or [])
    if not centers:
        raise RuntimeError(f"{template_id} requires non-empty centers")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    derivation_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    validation_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    light_fill = str(palette.get("light") or "#f8fafc").strip() or "#f8fafc"
    summary_fill = str(palette.get("secondary_soft") or "#e2e8f0").strip() or "#e2e8f0"
    audit_color = str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed"
    primary_fill = str(palette.get("primary_soft") or "#eff6ff").strip() or "#eff6ff"
    neutral_text = "#334155"

    verdict_color_lookup = {
        "stable": derivation_color,
        "context_dependent": audit_color,
        "recalibration_required": audit_color,
        "insufficient_support": reference_color,
        "unstable": "#7f1d1d",
    }

    def _center_color(center_payload: dict[str, Any]) -> str:
        cohort_role = str(center_payload.get("cohort_role") or "").strip().casefold()
        if "derivation" in cohort_role or "train" in cohort_role:
            return derivation_color
        if "validation" in cohort_role:
            return validation_color
        return audit_color

    metric_values = [float(display_payload["metric_reference_value"])]
    for center in centers:
        metric_values.extend(
            (
                float(center["metric_lower"]),
                float(center["metric_estimate"]),
                float(center["metric_upper"]),
            )
        )
    x_min = min(metric_values)
    x_max = max(metric_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.03)
    x_lower = max(0.0, x_min - x_padding) if x_min >= 0.0 else x_min - x_padding
    x_upper = x_max + x_padding
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.010)
    marker_half_height = 0.085
    interval_half_height = 0.028
    reference_half_width = max((x_upper - x_lower) * 0.004, 0.0015)

    row_count = len(centers)
    figure_height = max(5.4, 1.02 * row_count + 2.5)
    fig, (metric_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(11.2, figure_height),
        gridspec_kw={"width_ratios": [2.15, 1.25]},
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
            color="#13293d",
            y=0.985,
        )

    metric_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("metric_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.23,
        font_size=axis_title_size,
        font_weight="bold",
    )
    metric_x_label_lines = _wrap_flow_text_to_width(
        str(display_payload.get("metric_x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.32,
        font_size=axis_title_size,
        font_weight="bold",
    )

    metric_axes.set_title(
        "\n".join(metric_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_text,
        pad=12.0,
    )
    metric_axes.set_xlabel(
        "\n".join(metric_x_label_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    metric_reference_value = float(display_payload["metric_reference_value"])
    metric_axes.axvline(metric_reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    metric_axes.set_xlim(x_lower, x_upper)
    metric_axes.set_ylim(-0.6, row_count - 0.4)
    metric_axes.invert_yaxis()
    metric_axes.set_yticks([])
    metric_axes.tick_params(axis="x", labelsize=tick_size, colors=neutral_text)
    metric_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(metric_axes)

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

    row_label_artists: list[Any] = []
    center_metrics_for_sidecar: list[dict[str, Any]] = []
    verdict_artists: list[Any] = []
    metrics_text_artists: list[Any] = []
    action_artists: list[Any] = []
    detail_artists: list[Any | None] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(metric_axes.transAxes, metric_axes.transData)
    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18

    for row_index, center in enumerate(centers):
        y_center = float(row_index)
        row_label_artists.append(
            metric_axes.text(
                -0.03,
                y_center,
                str(center["center_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color=neutral_text,
                clip_on=False,
            )
        )
        interval_color = _center_color(center)
        metric_axes.plot(
            [float(center["metric_lower"]), float(center["metric_upper"])],
            [y_center, y_center],
            color=interval_color,
            linewidth=2.2,
            solid_capstyle="round",
            zorder=3,
        )
        metric_axes.scatter(
            [float(center["metric_estimate"])],
            [y_center],
            s=marker_size**2,
            color=interval_color,
            edgecolors="white",
            linewidths=0.8,
            zorder=4,
        )

        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.05, y_center - 0.36),
            0.90,
            0.72,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            transform=summary_axes.transData,
            facecolor=primary_fill if row_index % 2 == 0 else light_fill,
            edgecolor=summary_fill,
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        verdict_lines = _wrap_flow_text_to_width(
            str(center["verdict"]).replace("_", " "),
            max_width_pt=summary_text_width_pt,
            font_size=max(axis_title_size - 0.8, 9.2),
            font_weight="bold",
        )
        verdict_artist = summary_axes.text(
            0.08,
            y_center - 0.18,
            "\n".join(verdict_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(axis_title_size - 0.8, 9.2),
            fontweight="bold",
            color=verdict_color_lookup.get(str(center["verdict"]), neutral_text),
            zorder=2,
        )
        metrics_line = (
            f"n={int(center['support_count'])} | events={int(center['event_count'])} | "
            f"shift={float(center['max_shift']):.2f}\n"
            f"slope={float(center['slope']):.2f} | O:E={float(center['oe_ratio']):.2f}"
        )
        metrics_artist = summary_axes.text(
            0.08,
            y_center + 0.00,
            metrics_line,
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 1.0, 7.9),
            color=neutral_text,
            zorder=2,
        )
        action_lines = _wrap_flow_text_to_width(
            str(center["action"]),
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 0.8, 8.1),
            font_weight="bold",
        )
        action_artist = summary_axes.text(
            0.08,
            y_center + 0.18,
            "\n".join(action_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 0.8, 8.1),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        detail_text = str(center.get("detail") or "").strip()
        if detail_text:
            detail_lines = _wrap_flow_text_to_width(
                detail_text,
                max_width_pt=summary_text_width_pt,
                font_size=max(tick_size - 1.2, 7.6),
                font_weight="normal",
            )
            detail_artist = summary_axes.text(
                0.08,
                y_center + 0.33,
                "\n".join(detail_lines),
                transform=summary_axes.transData,
                ha="left",
                va="center",
                fontsize=max(tick_size - 1.2, 7.6),
                color="#64748b",
                zorder=2,
            )

        verdict_artists.append(verdict_artist)
        metrics_text_artists.append(metrics_artist)
        action_artists.append(action_artist)
        detail_artists.append(detail_artist)
        normalized_center = {
            "center_id": str(center["center_id"]),
            "center_label": str(center["center_label"]),
            "cohort_role": str(center["cohort_role"]),
            "support_count": int(center["support_count"]),
            "event_count": int(center["event_count"]),
            "metric_estimate": float(center["metric_estimate"]),
            "metric_lower": float(center["metric_lower"]),
            "metric_upper": float(center["metric_upper"]),
            "max_shift": float(center["max_shift"]),
            "slope": float(center["slope"]),
            "oe_ratio": float(center["oe_ratio"]),
            "verdict": str(center["verdict"]),
            "action": str(center["action"]),
        }
        if detail_text:
            normalized_center["detail"] = detail_text
        center_metrics_for_sidecar.append(normalized_center)

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.23, right=0.97, top=top_margin, bottom=0.18, wspace=0.18)
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

    panel_label_a = _add_panel_label(axes_item=metric_axes, label="A")
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
                bbox=metric_axes.title.get_window_extent(renderer=renderer),
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
            _bbox_to_layout_box(
                figure=fig,
                bbox=metric_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=metric_axes.get_window_extent(renderer=renderer),
            box_id="metric_panel",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="summary_panel",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _data_box_to_layout_box(
            axes=metric_axes,
            figure=fig,
            x0=metric_reference_value - reference_half_width,
            y0=-0.5,
            x1=metric_reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id="reference_line",
            box_type="reference_line",
        )
    ]

    normalized_centers: list[dict[str, Any]] = []
    for row_index, center in enumerate(center_metrics_for_sidecar):
        center_id = str(center["center_id"])
        y_center = float(row_index)
        row_label_box_id = f"row_label_{center_id}"
        metric_box_id = f"metric_{center_id}"
        interval_box_id = f"ci_{center_id}"
        verdict_box_id = f"verdict_{center_id}"
        metrics_box_id = f"metrics_{center_id}"
        action_box_id = f"action_{center_id}"
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
                    bbox=verdict_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=verdict_box_id,
                    box_type="verdict_value",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=metrics_text_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=metrics_box_id,
                    box_type="row_metric",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=action_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=action_box_id,
                    box_type="row_action",
                ),
                _data_box_to_layout_box(
                    axes=metric_axes,
                    figure=fig,
                    x0=float(center["metric_estimate"]) - marker_half_width,
                    y0=y_center - marker_half_height,
                    x1=float(center["metric_estimate"]) + marker_half_width,
                    y1=y_center + marker_half_height,
                    box_id=metric_box_id,
                    box_type="estimate_marker",
                ),
                _data_box_to_layout_box(
                    axes=metric_axes,
                    figure=fig,
                    x0=float(center["metric_lower"]),
                    y0=y_center - interval_half_height,
                    x1=float(center["metric_upper"]),
                    y1=y_center + interval_half_height,
                    box_id=interval_box_id,
                    box_type="ci_segment",
                ),
            ]
        )
        if detail_artists[row_index] is not None:
            detail_box_id = f"detail_{center_id}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=detail_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="verdict_detail",
                )
            )

        normalized_center = dict(center)
        normalized_center.update(
            {
                "label_box_id": row_label_box_id,
                "metric_box_id": metric_box_id,
                "interval_box_id": interval_box_id,
                "verdict_box_id": verdict_box_id,
                "metrics_box_id": metrics_box_id,
                "action_box_id": action_box_id,
            }
        )
        if detail_box_id:
            normalized_center["detail_box_id"] = detail_box_id
        normalized_centers.append(normalized_center)

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "metric_family": str(display_payload.get("metric_family") or "").strip(),
                "metric_reference_value": metric_reference_value,
                "metric_panel": {
                    "panel_box_id": "metric_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "batch_shift_threshold": float(display_payload["batch_shift_threshold"]),
                "slope_acceptance_lower": float(display_payload["slope_acceptance_lower"]),
                "slope_acceptance_upper": float(display_payload["slope_acceptance_upper"]),
                "oe_ratio_acceptance_lower": float(display_payload["oe_ratio_acceptance_lower"]),
                "oe_ratio_acceptance_upper": float(display_payload["oe_ratio_acceptance_upper"]),
                "centers": normalized_centers,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_generalizability_subgroup_composite_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    overview_rows = list(display_payload.get("overview_rows") or [])
    subgroup_rows = list(display_payload.get("subgroup_rows") or [])
    if not overview_rows or not subgroup_rows:
        raise RuntimeError(f"{template_id} requires non-empty overview_rows and subgroup_rows")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    reference_color = _require_non_empty_string(
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
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    primary_label = str(display_payload.get("primary_label") or "").strip()
    comparator_label = str(display_payload.get("comparator_label") or "").strip()

    overview_values = [float(row["metric_value"]) for row in overview_rows]
    if comparator_label:
        overview_values.extend(float(row["comparator_metric_value"]) for row in overview_rows)
    overview_min = min(overview_values)
    overview_max = max(overview_values)
    overview_span = max(overview_max - overview_min, 1e-6)
    overview_padding = max(overview_span * 0.16, 0.03)
    overview_support_margin = max(overview_span * 0.36, 0.08)
    overview_panel_xmin = overview_min - overview_padding
    overview_panel_xmax = overview_max + overview_padding + overview_support_margin
    overview_support_x = overview_max + overview_padding * 0.35

    subgroup_values = [float(display_payload["subgroup_reference_value"])]
    for row in subgroup_rows:
        subgroup_values.extend((float(row["lower"]), float(row["upper"]), float(row["estimate"])))
    subgroup_min = min(subgroup_values)
    subgroup_max = max(subgroup_values)
    subgroup_span = max(subgroup_max - subgroup_min, 1e-6)
    subgroup_padding = max(subgroup_span * 0.16, 0.03)
    subgroup_panel_xmin = subgroup_min - subgroup_padding
    subgroup_panel_xmax = subgroup_max + subgroup_padding
    max_rows = max(len(overview_rows), len(subgroup_rows))
    figure_height = max(4.8, 0.54 * max_rows + 2.6)
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10.8, figure_height),
        gridspec_kw={"width_ratios": [1.18, 1.0]},
        squeeze=False,
    )
    overview_axes, subgroup_axes = axes[0]
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=reference_color,
            y=0.985,
        )

    overview_row_label_specs: list[tuple[str, float]] = []
    overview_support_label_artists: list[Any] = []
    overview_metric_artists: list[Any] = []
    overview_comparator_artists: list[Any] = []
    overview_metrics_for_sidecar: list[dict[str, Any]] = []
    for row_index, row in enumerate(overview_rows):
        y_pos = float(row_index)
        overview_row_label_specs.append((str(row["cohort_label"]), y_pos))
        overview_support_label_artists.append(
            overview_axes.text(
                overview_support_x,
                y_pos,
                f"n={int(row['support_count'])}",
                ha="left",
                va="center",
                fontsize=max(tick_size - 1.1, 7.8),
                color="#475569",
                clip_on=False,
            )
        )
        if comparator_label:
            overview_comparator_artists.append(
                overview_axes.plot(
                    float(row["comparator_metric_value"]),
                    y_pos,
                    marker="o",
                    markersize=marker_size + 1.0,
                    markerfacecolor="white",
                    markeredgecolor=comparator_color,
                    markeredgewidth=1.1,
                    linestyle="None",
                    zorder=3,
                )[0]
            )
        overview_metric_artists.append(
            overview_axes.plot(
                float(row["metric_value"]),
                y_pos,
                marker="o",
                markersize=marker_size + 1.2,
                markerfacecolor=model_color,
                markeredgecolor=model_color,
                linestyle="None",
                zorder=4,
            )[0]
        )
        sidecar_row = {
            "cohort_id": str(row["cohort_id"]),
            "cohort_label": str(row["cohort_label"]),
            "support_count": int(row["support_count"]),
            "metric_value": float(row["metric_value"]),
            "label_box_id": f"overview_row_label_{row_index + 1}",
            "support_label_box_id": f"overview_support_label_{row_index + 1}",
            "metric_marker_box_id": f"overview_metric_marker_{row_index + 1}",
        }
        if row.get("event_count") is not None:
            sidecar_row["event_count"] = int(row["event_count"])
        if comparator_label:
            sidecar_row["comparator_metric_value"] = float(row["comparator_metric_value"])
            sidecar_row["comparator_marker_box_id"] = f"overview_comparator_marker_{row_index + 1}"
        overview_metrics_for_sidecar.append(sidecar_row)

    overview_axes.set_xlim(overview_panel_xmin, overview_panel_xmax)
    overview_axes.set_ylim(-0.7, len(overview_rows) - 0.3)
    overview_axes.invert_yaxis()
    overview_axes.set_yticks([])
    overview_axes.set_xlabel(
        str(display_payload.get("overview_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
    )
    overview_axes.set_title(
        str(display_payload.get("overview_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
        pad=10.0,
    )
    overview_axes.tick_params(axis="x", labelsize=tick_size, colors=reference_color)
    overview_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.65, zorder=0)
    _apply_publication_axes_style(overview_axes)

    subgroup_row_label_specs: list[tuple[str, float]] = []
    subgroup_ci_artists: list[Any] = []
    subgroup_estimate_artists: list[Any] = []
    subgroup_metrics_for_sidecar: list[dict[str, Any]] = []
    for row_index, row in enumerate(subgroup_rows):
        y_pos = float(row_index)
        subgroup_row_label_specs.append((str(row["subgroup_label"]), y_pos))
        subgroup_ci_artists.append(
            subgroup_axes.plot(
                [float(row["lower"]), float(row["upper"])],
                [y_pos, y_pos],
                color=reference_color,
                linewidth=1.4,
                zorder=2,
            )[0]
        )
        subgroup_estimate_artists.append(
            subgroup_axes.plot(
                float(row["estimate"]),
                y_pos,
                marker="s",
                markersize=marker_size + 0.8,
                markerfacecolor=model_color,
                markeredgecolor=model_color,
                linestyle="None",
                zorder=3,
            )[0]
        )
        sidecar_row = {
            "subgroup_id": str(row["subgroup_id"]),
            "subgroup_label": str(row["subgroup_label"]),
            "estimate": float(row["estimate"]),
            "lower": float(row["lower"]),
            "upper": float(row["upper"]),
            "label_box_id": f"subgroup_row_label_{row_index + 1}",
            "ci_box_id": f"subgroup_ci_{row_index + 1}",
            "estimate_box_id": f"subgroup_estimate_{row_index + 1}",
        }
        if row.get("group_n") is not None:
            sidecar_row["group_n"] = int(row["group_n"])
        subgroup_metrics_for_sidecar.append(sidecar_row)

    subgroup_axes.axvline(
        float(display_payload["subgroup_reference_value"]),
        color=comparator_color if comparator_label else reference_color,
        linewidth=1.0,
        linestyle="--",
        zorder=1,
    )
    subgroup_axes.set_xlim(subgroup_panel_xmin, subgroup_panel_xmax)
    subgroup_axes.set_ylim(-0.7, len(subgroup_rows) - 0.3)
    subgroup_axes.invert_yaxis()
    subgroup_axes.set_yticks([])
    subgroup_axes.set_xlabel(
        str(display_payload.get("subgroup_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
    )
    subgroup_axes.set_title(
        str(display_payload.get("subgroup_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
        pad=10.0,
    )
    subgroup_axes.tick_params(axis="x", labelsize=tick_size, colors=reference_color)
    subgroup_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.65, zorder=0)
    _apply_publication_axes_style(subgroup_axes)

    legend = None
    if comparator_label:
        legend = fig.legend(
            handles=[
                matplotlib.lines.Line2D(
                    [], [], marker="o", linestyle="None", markersize=marker_size + 1.2, color=model_color, label=primary_label
                ),
                matplotlib.lines.Line2D(
                    [],
                    [],
                    marker="o",
                    linestyle="None",
                    markersize=marker_size + 1.0,
                    markerfacecolor="white",
                    markeredgecolor=comparator_color,
                    color=comparator_color,
                    label=comparator_label,
                ),
            ],
            title="Model context",
            frameon=False,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.02),
            ncol=2,
            borderaxespad=0.0,
        )

    subplot_top = 0.88 if show_figure_title else 0.94
    subplot_bottom = 0.14 if comparator_label else 0.11
    fig.subplots_adjust(left=0.11, right=0.97, top=subplot_top, bottom=subplot_bottom, wspace=0.36)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    overview_row_label_artists: list[Any] = []
    subgroup_row_label_artists: list[Any] = []

    overview_panel_bbox = overview_axes.get_window_extent(renderer=renderer)
    subgroup_panel_bbox = subgroup_axes.get_window_extent(renderer=renderer)
    overview_panel_x0, _ = fig.transFigure.inverted().transform((overview_panel_bbox.x0, overview_panel_bbox.y0))
    subgroup_panel_x0, _ = fig.transFigure.inverted().transform((subgroup_panel_bbox.x0, subgroup_panel_bbox.y0))
    outboard_gap = 0.008

    for label_text, y_pos in overview_row_label_specs:
        _, label_y = _data_point_to_figure_xy(
            axes=overview_axes,
            figure=fig,
            x=overview_panel_xmin,
            y=y_pos,
        )
        overview_row_label_artists.append(
            fig.text(
                overview_panel_x0 - outboard_gap,
                label_y,
                label_text,
                fontsize=max(tick_size - 0.3, 8.6),
                color=reference_color,
                ha="right",
                va="center",
            )
        )

    for label_text, y_pos in subgroup_row_label_specs:
        _, label_y = _data_point_to_figure_xy(
            axes=subgroup_axes,
            figure=fig,
            x=subgroup_panel_xmin,
            y=y_pos,
        )
        subgroup_row_label_artists.append(
            fig.text(
                subgroup_panel_x0 - outboard_gap,
                label_y,
                label_text,
                fontsize=max(tick_size - 0.3, 8.6),
                color=reference_color,
                ha="right",
                va="center",
            )
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
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.2),
            fontweight="bold",
            color=reference_color,
            ha="left",
            va="top",
        )

    overview_panel_label = _add_panel_label(axes_item=overview_axes, label="A")
    subgroup_panel_label = _add_panel_label(axes_item=subgroup_axes, label="B")
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
                bbox=overview_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_A",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_B",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=overview_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_B",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=overview_panel_label.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_panel_label.get_window_extent(renderer=renderer),
                box_id="panel_label_B",
                box_type="panel_label",
            ),
        ]
    )
    for index, artist in enumerate(overview_row_label_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_row_label_{index}",
                box_type="overview_row_label",
            )
        )
    for index, artist in enumerate(overview_support_label_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_support_label_{index}",
                box_type="support_label",
            )
        )
    for index, artist in enumerate(overview_metric_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_metric_marker_{index}",
                box_type="overview_metric_marker",
            )
        )
    for index, artist in enumerate(overview_comparator_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_comparator_marker_{index}",
                box_type="overview_comparator_marker",
            )
        )
    for index, artist in enumerate(subgroup_row_label_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"subgroup_row_label_{index}",
                box_type="subgroup_row_label",
            )
        )
    for index, artist in enumerate(subgroup_ci_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"subgroup_ci_{index}",
                box_type="ci_segment",
            )
        )
    for index, artist in enumerate(subgroup_estimate_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"subgroup_estimate_{index}",
                box_type="estimate_marker",
            )
        )

    guide_boxes: list[dict[str, Any]] = []
    if legend is not None:
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend",
                box_type="legend",
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
                    bbox=overview_axes.get_window_extent(renderer=renderer),
                    box_id="overview_panel",
                    box_type="panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=subgroup_axes.get_window_extent(renderer=renderer),
                    box_id="subgroup_panel",
                    box_type="panel",
                ),
            ],
            "guide_boxes": guide_boxes,
            "metrics": {
                "metric_family": str(display_payload.get("metric_family") or "").strip(),
                "primary_label": primary_label,
                "comparator_label": comparator_label,
                "legend_title": "Model context" if comparator_label else "",
                "legend_labels": [primary_label, comparator_label] if comparator_label else [],
                "overview_rows": overview_metrics_for_sidecar,
                "subgroup_reference_value": float(display_payload["subgroup_reference_value"]),
                "subgroup_rows": subgroup_metrics_for_sidecar,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

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
