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
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    dump_json,
)

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
