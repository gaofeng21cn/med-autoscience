from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _centered_offsets,
    _data_box_to_layout_box,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    _wrap_flow_text_to_width,
    dump_json,
)

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

