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

def _render_python_partial_dependence_interaction_slice_panel(
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
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    slice_palette = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#2F5D8A").strip() or "#2F5D8A",
        str(palette.get("secondary_soft") or "#94a3b8").strip() or "#94a3b8",
    ]
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    all_y_values = [
        float(value)
        for panel in panels
        for curve in panel["slice_curves"]
        for value in curve["y"]
    ]
    y_min = min(all_y_values)
    y_max = max(all_y_values)
    y_span = max(y_max - y_min, 1e-6)
    y_padding = max(y_span * 0.18, 0.04)
    y_lower = y_min - y_padding
    y_upper = y_max + y_padding

    figure_width = max(8.8, 3.8 * len(panels) + 1.8)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 5.0), squeeze=False)
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

    legend_labels = [str(item) for item in list(display_payload.get("legend_labels") or [])]
    legend_handles: list[Any] = []
    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, panels, strict=True):
        raw_slice_curves: list[dict[str, Any]] = []
        first_curve_x = [float(value) for value in panel["slice_curves"][0]["x"]]
        x_min = min(first_curve_x)
        x_max = max(first_curve_x)
        x_span = max(x_max - x_min, 1e-6)
        x_padding = max(x_span * 0.10, 0.04)

        for curve_index, curve in enumerate(panel["slice_curves"]):
            curve_x = [float(value) for value in curve["x"]]
            curve_y = [float(value) for value in curve["y"]]
            curve_color = slice_palette[curve_index % len(slice_palette)]
            axes_item.plot(
                curve_x,
                curve_y,
                color=curve_color,
                linewidth=2.2,
                alpha=0.95,
                zorder=3 + curve_index,
            )
            raw_slice_curves.append(
                {
                    "slice_id": str(curve["slice_id"]),
                    "slice_label": str(curve["slice_label"]),
                    "conditioning_value": float(curve["conditioning_value"]),
                    "x": curve_x,
                    "y": curve_y,
                    "color": curve_color,
                }
            )
            if not legend_handles:
                legend_handles.append(
                    matplotlib.lines.Line2D(
                        [], [], color=curve_color, linewidth=2.2, label=str(curve["slice_label"])
                    )
                )

        reference_value = float(panel["reference_value"])
        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.1,
            linestyle="--",
            zorder=2,
        )
        reference_label_artist = axes_item.text(
            reference_value,
            y_upper - y_span * 0.05,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="top",
            zorder=5,
        )

        axes_item.set_xlim(x_min - x_padding, x_max + x_padding)
        axes_item.set_ylim(y_lower, y_upper)
        axes_item.set_xlabel(
            str(panel["x_label"]),
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
        axes_item.tick_params(axis="both", labelsize=tick_size, colors="#2F3437")
        axes_item.grid(axis="both", color="#e6edf2", linewidth=0.55, linestyle=":")
        _apply_publication_axes_style(axes_item)

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "panel_title_artist": axes_item.title,
                "reference_label_artist": reference_label_artist,
                "raw_slice_curves": raw_slice_curves,
                "x_span": x_span,
            }
        )

    top_margin = 0.78 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.11, right=0.95, top=top_margin, bottom=0.25, wspace=0.28)

    y_axis_title_artist = fig.text(
        0.035,
        0.51,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
        ha="center",
        va="center",
    )

    legend = fig.legend(
        handles=legend_handles,
        title=str(display_payload.get("legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.50, 0.045),
        ncol=min(max(len(legend_handles), 1), 3),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.1, 8.7),
        handlelength=2.2,
        columnspacing=1.5,
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
            fontsize=max(panel_label_size + 1.6, 13.2),
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
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_title().get_window_extent(renderer=renderer),
                box_id="legend_title",
                box_type="legend_title",
            ),
        ]
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

        reference_line_box_id = f"reference_line_{panel_token}"
        reference_label_box_id = f"reference_label_{panel_token}"
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
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=reference_label_box_id,
                    box_type="slice_reference_label",
                ),
            ]
        )

        reference_half_width = max(record["x_span"] * 0.003, 0.0015)
        reference_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_value"]) - reference_half_width,
            y0=float(y_lower),
            x1=float(panel["reference_value"]) + reference_half_width,
            y1=float(y_upper),
            box_id=reference_line_box_id,
            box_type="slice_reference_line",
        )
        reference_line_box["y0"] = max(float(panel_box["y0"]), float(reference_line_box["y0"]))
        reference_line_box["y1"] = min(float(panel_box["y1"]), float(reference_line_box["y1"]))
        guide_boxes.append(reference_line_box)

        normalized_slice_curves: list[dict[str, Any]] = []
        for curve in record["raw_slice_curves"]:
            normalized_points: list[dict[str, Any]] = []
            for feature_value, response_value in zip(curve["x"], curve["y"], strict=True):
                point_x, point_y = _data_point_to_figure_xy(
                    axes=axes_item,
                    figure=fig,
                    x=float(feature_value),
                    y=float(response_value),
                )
                normalized_points.append(
                    {
                        "feature_value": float(feature_value),
                        "response_value": float(response_value),
                        "x": point_x,
                        "y": point_y,
                    }
                )
            normalized_slice_curves.append(
                {
                    "slice_id": str(curve["slice_id"]),
                    "slice_label": str(curve["slice_label"]),
                    "conditioning_value": float(curve["conditioning_value"]),
                    "points": normalized_points,
                }
            )

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "x_feature": str(panel["x_feature"]),
                "slice_feature": str(panel["slice_feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": reference_label_box_id,
                "slice_curves": normalized_slice_curves,
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
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "legend_title": str(display_payload.get("legend_title") or "").strip(),
                "legend_labels": legend_labels,
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

