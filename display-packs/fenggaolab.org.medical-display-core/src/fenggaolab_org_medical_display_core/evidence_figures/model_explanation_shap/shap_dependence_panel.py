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

def _render_python_shap_dependence_panel(
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
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = float(stroke.get("marker_size") or 4.5)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    interaction_values = [float(point["interaction_value"]) for panel in panels for point in panel["points"]]
    interaction_min = min(interaction_values)
    interaction_max = max(interaction_values)
    if interaction_max <= interaction_min:
        interaction_max = interaction_min + 1.0
    color_norm = matplotlib.colors.Normalize(vmin=interaction_min, vmax=interaction_max)
    cmap = plt.get_cmap("coolwarm")

    shap_values = [float(point["shap_value"]) for panel in panels for point in panel["points"]]
    y_min = min(min(shap_values), 0.0)
    y_max = max(max(shap_values), 0.0)
    y_span = max(y_max - y_min, 1e-6)
    y_padding = max(y_span * 0.16, 0.08)
    y_lower = y_min - y_padding
    y_upper = y_max + y_padding
    if y_upper <= y_lower:
        y_upper = y_lower + 0.25

    figure_width = max(8.8, 3.7 * len(panels) + 1.8)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 4.9), squeeze=False)
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

    panel_title_artists: list[Any] = []
    for axes_item, panel in zip(axes_list, panels, strict=True):
        feature_values = [float(point["feature_value"]) for point in panel["points"]]
        x_min = min(feature_values)
        x_max = max(feature_values)
        x_span = x_max - x_min
        if x_span <= 0.0:
            x_padding = max(abs(x_min) * 0.15, 1.0)
        else:
            x_padding = max(x_span * 0.14, x_span * 0.06)
        axes_item.scatter(
            feature_values,
            [float(point["shap_value"]) for point in panel["points"]],
            c=[float(point["interaction_value"]) for point in panel["points"]],
            cmap=cmap,
            norm=color_norm,
            s=marker_size**2,
            alpha=0.94,
            edgecolors="white",
            linewidths=0.5,
            zorder=3,
        )
        axes_item.axhline(0.0, color=neutral_color, linewidth=1.0, linestyle="--", zorder=1)
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
        panel_title_artists.append(axes_item.title)

    top_margin = 0.78 if show_figure_title else 0.86
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.11, right=0.88, top=top_margin, bottom=0.22, wspace=0.26)

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

    scalar_mappable = plt.cm.ScalarMappable(norm=color_norm, cmap=cmap)
    scalar_mappable.set_array([])
    colorbar = fig.colorbar(scalar_mappable, ax=axes_list, fraction=0.048, pad=0.04)
    colorbar.set_label(
        str(display_payload.get("colorbar_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        color="#13293d",
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.4), colors="#2F3437")

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
        _add_panel_label(axes_item=axes_item, label=str(panel["panel_label"]))
        for axes_item, panel in zip(axes_list, panels, strict=True)
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
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        )
    ]
    normalized_panels: list[dict[str, Any]] = []

    for axes_item, panel_title_artist, panel_label_artist, panel in zip(
        axes_list,
        panel_title_artists,
        panel_label_artists,
        panels,
        strict=True,
    ):
        panel_token = str(panel["panel_label"])
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_title_artist.get_window_extent(renderer=renderer),
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
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=f"panel_{panel_token}",
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        x_lower, x_upper = axes_item.get_xlim()
        y_thickness = max((axes_item.get_ylim()[1] - axes_item.get_ylim()[0]) * 0.012, 0.01)
        zero_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(x_lower),
            y0=-y_thickness / 2.0,
            x1=float(x_upper),
            y1=y_thickness / 2.0,
            box_id=f"zero_line_{panel_token}",
            box_type="zero_line",
        )
        zero_line_box["x0"] = float(panel_box["x0"])
        zero_line_box["x1"] = float(panel_box["x1"])
        zero_line_box["y0"] = max(float(panel_box["y0"]), float(zero_line_box["y0"]))
        zero_line_box["y1"] = min(float(panel_box["y1"]), float(zero_line_box["y1"]))
        guide_boxes.append(
            zero_line_box
        )

        normalized_points: list[dict[str, Any]] = []
        for point in panel["points"]:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(point["feature_value"]),
                y=float(point["shap_value"]),
            )
            normalized_points.append(
                {
                    "feature_value": float(point["feature_value"]),
                    "shap_value": float(point["shap_value"]),
                    "interaction_value": float(point["interaction_value"]),
                    "x": point_x,
                    "y": point_y,
                }
            )
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "interaction_feature": str(panel["interaction_feature"]),
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
                "figure_height_inches": float(fig.get_figheight()),
                "figure_width_inches": float(fig.get_figwidth()),
                "colorbar_label": str(display_payload.get("colorbar_label") or "").strip(),
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

