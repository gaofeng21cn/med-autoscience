from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _data_box_to_layout_box,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
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

