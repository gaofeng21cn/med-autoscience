from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ..shared import (
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

def _render_python_partial_dependence_ice_panel(
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
    layout_override = dict(render_context.get("layout_override") or {})

    ice_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    pdp_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
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
        for value in (
            list(panel["pdp_curve"]["y"])
            + [point for curve in panel["ice_curves"] for point in curve["y"]]
        )
    ]
    y_min = min(all_y_values)
    y_max = max(all_y_values)
    y_span = max(y_max - y_min, 1e-6)
    y_padding = max(y_span * 0.18, 0.04)
    y_lower = y_min - y_padding
    y_upper = y_max + y_padding

    figure_width = max(8.8, 3.8 * len(panels) + 1.6)
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

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, panels, strict=True):
        pdp_x = [float(value) for value in panel["pdp_curve"]["x"]]
        pdp_y = [float(value) for value in panel["pdp_curve"]["y"]]
        x_min = min(pdp_x)
        x_max = max(pdp_x)
        x_span = max(x_max - x_min, 1e-6)
        x_padding = max(x_span * 0.10, 0.04)

        ice_line_artists: list[Any] = []
        normalized_ice_curves: list[dict[str, Any]] = []
        for curve in panel["ice_curves"]:
            curve_x = [float(value) for value in curve["x"]]
            curve_y = [float(value) for value in curve["y"]]
            line_artist = axes_item.plot(
                curve_x,
                curve_y,
                color=ice_color,
                linewidth=1.1,
                alpha=0.24,
                zorder=2,
            )[0]
            ice_line_artists.append(line_artist)
            normalized_ice_curves.append(
                {
                    "curve_id": str(curve["curve_id"]),
                    "x": curve_x,
                    "y": curve_y,
                }
            )

        pdp_line_artist = axes_item.plot(
            pdp_x,
            pdp_y,
            color=pdp_color,
            linewidth=2.4,
            zorder=3,
        )[0]
        reference_line_artist = axes_item.axvline(
            float(panel["reference_value"]),
            color=neutral_color,
            linewidth=1.1,
            linestyle="--",
            zorder=1,
        )
        reference_label_artist = axes_item.text(
            float(panel["reference_value"]),
            y_upper - y_span * 0.05,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=neutral_color,
            ha="center",
            va="top",
            zorder=4,
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
                "ice_line_artists": ice_line_artists,
                "pdp_line_artist": pdp_line_artist,
                "reference_line_artist": reference_line_artist,
                "reference_label_artist": reference_label_artist,
                "normalized_pdp": {"x": pdp_x, "y": pdp_y},
                "normalized_ice_curves": normalized_ice_curves,
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
        handles=[
            matplotlib.lines.Line2D([], [], color=ice_color, linewidth=1.4, alpha=0.30),
            matplotlib.lines.Line2D([], [], color=pdp_color, linewidth=2.4),
        ],
        labels=["ICE curves", "PDP mean"],
        loc="lower center",
        bbox_to_anchor=(0.5, 0.05),
        ncol=2,
        frameon=False,
        fontsize=max(tick_size - 1.0, 8.2),
        handlelength=2.4,
        columnspacing=1.6,
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
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=fig,
            bbox=y_axis_title_artist.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="subplot_y_axis_title",
        )
    )
    layout_boxes.append(
        _bbox_to_layout_box(
            figure=fig,
            bbox=legend.get_window_extent(renderer=renderer),
            box_id="legend_box",
            box_type="legend_box",
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
                    box_type="pdp_reference_label",
                ),
            ]
        )
        x_span = max(record["normalized_pdp"]["x"][-1] - record["normalized_pdp"]["x"][0], 1e-6)
        reference_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_value"]) - max(x_span * 0.003, 0.0015),
            y0=float(y_lower),
            x1=float(panel["reference_value"]) + max(x_span * 0.003, 0.0015),
            y1=float(y_upper),
            box_id=reference_line_box_id,
            box_type="pdp_reference_line",
        )
        reference_line_box["y0"] = max(float(panel_box["y0"]), float(reference_line_box["y0"]))
        reference_line_box["y1"] = min(float(panel_box["y1"]), float(reference_line_box["y1"]))
        guide_boxes.append(reference_line_box)

        normalized_pdp_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(
            record["normalized_pdp"]["x"],
            record["normalized_pdp"]["y"],
            strict=True,
        ):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            normalized_pdp_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_ice_curve_metrics: list[dict[str, Any]] = []
        for curve in record["normalized_ice_curves"]:
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
            normalized_ice_curve_metrics.append({"curve_id": str(curve["curve_id"]), "points": normalized_points})

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": reference_label_box_id,
                "pdp_points": normalized_pdp_points,
                "ice_curves": normalized_ice_curve_metrics,
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
                "legend_labels": ["ICE curves", "PDP mean"],
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_partial_dependence_interaction_contour_panel(
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

    support_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    contour_line_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    all_response_values = [
        float(value)
        for panel in panels
        for row in panel["response_grid"]
        for value in row
    ]
    vmin = min(all_response_values)
    vmax = max(all_response_values)
    if abs(vmax - vmin) < 1e-9:
        vmax = vmin + 1e-6

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        f"{template_id}_cmap",
        [
            str(palette.get("light") or "#eff6ff"),
            str(palette.get("secondary_soft") or "#cbd5e1"),
            str(palette.get("primary") or support_color),
        ],
    )

    figure_width = max(9.2, 4.5 * len(panels) + 1.9)
    fig, axes = plt.subplots(1, len(panels), figsize=(figure_width, 5.2), squeeze=False)
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
    contour_handle = None
    for axes_item, panel in zip(axes_list, panels, strict=True):
        x_grid = [float(value) for value in panel["x_grid"]]
        y_grid = [float(value) for value in panel["y_grid"]]
        response_grid = [[float(value) for value in row] for row in panel["response_grid"]]

        contour_handle = axes_item.contourf(
            x_grid,
            y_grid,
            response_grid,
            levels=12,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            antialiased=True,
            zorder=1,
        )
        axes_item.contour(
            x_grid,
            y_grid,
            response_grid,
            levels=6,
            colors=contour_line_color,
            linewidths=0.55,
            alpha=0.7,
            zorder=2,
        )

        support_x = [float(point["x"]) for point in panel["observed_points"]]
        support_y = [float(point["y"]) for point in panel["observed_points"]]
        axes_item.scatter(
            support_x,
            support_y,
            s=18.0,
            color=matplotlib.colors.to_rgba(support_color, alpha=0.32),
            edgecolors="white",
            linewidths=0.45,
            zorder=3,
        )

        axes_item.axvline(
            float(panel["reference_x_value"]),
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=4,
        )
        axes_item.axhline(
            float(panel["reference_y_value"]),
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=4,
        )
        axes_item.scatter(
            [float(panel["reference_x_value"])],
            [float(panel["reference_y_value"])],
            s=28.0,
            color=reference_color,
            edgecolors="white",
            linewidths=0.5,
            zorder=5,
        )

        x_span = max(x_grid[-1] - x_grid[0], 1e-6)
        y_span = max(y_grid[-1] - y_grid[0], 1e-6)
        reference_label_x = min(
            max(float(panel["reference_x_value"]) + x_span * 0.03, x_grid[0] + x_span * 0.08),
            x_grid[-1] - x_span * 0.08,
        )
        reference_label_y = min(
            max(float(panel["reference_y_value"]) + y_span * 0.05, y_grid[0] + y_span * 0.10),
            y_grid[-1] - y_span * 0.08,
        )
        reference_label_artist = axes_item.text(
            reference_label_x,
            reference_label_y,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="bottom",
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": (1.0, 1.0, 1.0, 0.72),
                "edgecolor": reference_color,
                "linewidth": 0.55,
            },
            zorder=6,
        )

        axes_item.set_xlabel(
            str(panel["x_label"]),
            fontsize=axis_title_size,
            fontweight="bold",
            color="#13293d",
        )
        axes_item.set_ylabel(
            str(panel["y_label"]),
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
                "reference_label_artist": reference_label_artist,
            }
        )

    top_margin = 0.80 if show_figure_title else 0.88
    top_margin = max(0.73, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.09, right=0.88, top=top_margin, bottom=0.18, wspace=0.28)

    colorbar = fig.colorbar(
        contour_handle,
        ax=axes_list,
        fraction=0.035,
        pad=0.04,
    )
    colorbar.set_label(
        str(display_payload.get("colorbar_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.6), colors="#2F3437")

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

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar",
            box_type="colorbar",
        )
    ]
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

        reference_vertical_box_id = f"reference_vertical_{panel_token}"
        reference_horizontal_box_id = f"reference_horizontal_{panel_token}"
        reference_label_box_id = f"reference_label_{panel_token}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
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
                    bbox=axes_item.yaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"y_axis_title_{panel_token}",
                    box_type="subplot_y_axis_title",
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
                    box_type="interaction_reference_label",
                ),
            ]
        )

        x_span = max(float(panel["x_grid"][-1]) - float(panel["x_grid"][0]), 1e-6)
        y_span = max(float(panel["y_grid"][-1]) - float(panel["y_grid"][0]), 1e-6)
        vertical_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_x_value"]) - max(x_span * 0.003, 0.0015),
            y0=float(panel["y_grid"][0]),
            x1=float(panel["reference_x_value"]) + max(x_span * 0.003, 0.0015),
            y1=float(panel["y_grid"][-1]),
            box_id=reference_vertical_box_id,
            box_type="interaction_reference_vertical",
        )
        vertical_box["y0"] = max(float(panel_box["y0"]), float(vertical_box["y0"]))
        vertical_box["y1"] = min(float(panel_box["y1"]), float(vertical_box["y1"]))
        guide_boxes.append(vertical_box)

        horizontal_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["x_grid"][0]),
            y0=float(panel["reference_y_value"]) - max(y_span * 0.003, 0.0015),
            x1=float(panel["x_grid"][-1]),
            y1=float(panel["reference_y_value"]) + max(y_span * 0.003, 0.0015),
            box_id=reference_horizontal_box_id,
            box_type="interaction_reference_horizontal",
        )
        horizontal_box["x0"] = max(float(panel_box["x0"]), float(horizontal_box["x0"]))
        horizontal_box["x1"] = min(float(panel_box["x1"]), float(horizontal_box["x1"]))
        guide_boxes.append(horizontal_box)

        normalized_observed_points: list[dict[str, Any]] = []
        for point in panel["observed_points"]:
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(point["x"]),
                y=float(point["y"]),
            )
            normalized_observed_points.append(
                {
                    "point_id": str(point["point_id"]),
                    "feature_x_value": float(point["x"]),
                    "feature_y_value": float(point["y"]),
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
                "y_label": str(panel["y_label"]),
                "x_feature": str(panel["x_feature"]),
                "y_feature": str(panel["y_feature"]),
                "reference_x_value": float(panel["reference_x_value"]),
                "reference_y_value": float(panel["reference_y_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_vertical_box_id": reference_vertical_box_id,
                "reference_horizontal_box_id": reference_horizontal_box_id,
                "reference_label_box_id": reference_label_box_id,
                "x_grid": [float(value) for value in panel["x_grid"]],
                "y_grid": [float(value) for value in panel["y_grid"]],
                "response_grid": [[float(value) for value in row] for row in panel["response_grid"]],
                "observed_points": normalized_observed_points,
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

def _render_python_partial_dependence_subgroup_comparison_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    panels = list(display_payload.get("panels") or [])
    subgroup_rows = list(display_payload.get("subgroup_rows") or [])
    if not panels or not subgroup_rows:
        raise RuntimeError(f"{template_id} requires non-empty panels and subgroup_rows")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    ice_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    pdp_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    interval_fill = str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    top_y_values = [
        float(value)
        for panel in panels
        for value in (
            list(panel["pdp_curve"]["y"])
            + [point for curve in panel["ice_curves"] for point in curve["y"]]
        )
    ]
    top_y_min = min(top_y_values)
    top_y_max = max(top_y_values)
    top_y_span = max(top_y_max - top_y_min, 1e-6)
    top_y_padding = max(top_y_span * 0.18, 0.04)
    top_y_lower = top_y_min - top_y_padding
    top_y_upper = top_y_max + top_y_padding

    subgroup_values = [float(item["estimate"]) for item in subgroup_rows]
    subgroup_values.extend(float(item["lower"]) for item in subgroup_rows)
    subgroup_values.extend(float(item["upper"]) for item in subgroup_rows)
    subgroup_x_min = min(subgroup_values)
    subgroup_x_max = max(subgroup_values)
    subgroup_x_span = max(subgroup_x_max - subgroup_x_min, 1e-6)
    subgroup_x_padding = max(subgroup_x_span * 0.18, 0.04)

    figure_width = max(9.8, 3.8 * len(panels) + 2.8)
    fig = plt.figure(figsize=(figure_width, 6.2))
    grid = fig.add_gridspec(2, len(panels), height_ratios=[1.0, 0.78], hspace=0.56, wspace=0.34)
    top_axes = [fig.add_subplot(grid[0, index]) for index in range(len(panels))]
    subgroup_axes = fig.add_subplot(grid[1, :])
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

    top_panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(top_axes, panels, strict=True):
        pdp_x = [float(value) for value in panel["pdp_curve"]["x"]]
        pdp_y = [float(value) for value in panel["pdp_curve"]["y"]]
        x_min = min(pdp_x)
        x_max = max(pdp_x)
        x_span = max(x_max - x_min, 1e-6)
        x_padding = max(x_span * 0.10, 0.04)

        raw_ice_curves: list[dict[str, Any]] = []
        for curve in panel["ice_curves"]:
            curve_x = [float(value) for value in curve["x"]]
            curve_y = [float(value) for value in curve["y"]]
            axes_item.plot(
                curve_x,
                curve_y,
                color=ice_color,
                linewidth=1.1,
                alpha=0.24,
                zorder=2,
            )
            raw_ice_curves.append(
                {
                    "curve_id": str(curve["curve_id"]),
                    "x": curve_x,
                    "y": curve_y,
                }
            )

        axes_item.plot(
            pdp_x,
            pdp_y,
            color=pdp_color,
            linewidth=2.4,
            zorder=3,
        )
        reference_value = float(panel["reference_value"])
        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=1,
        )
        reference_label_artist = axes_item.text(
            reference_value,
            top_y_upper - top_y_span * 0.05,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="top",
            zorder=4,
        )

        axes_item.set_xlim(x_min - x_padding, x_max + x_padding)
        axes_item.set_ylim(top_y_lower, top_y_upper)
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

        top_panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "panel_title_artist": axes_item.title,
                "reference_label_artist": reference_label_artist,
                "normalized_pdp": {"x": pdp_x, "y": pdp_y},
                "raw_ice_curves": raw_ice_curves,
                "x_span": x_span,
            }
        )

    subgroup_row_records: list[dict[str, Any]] = []
    ci_line_artists: list[Any] = []
    estimate_artists: list[Any] = []
    for row_index, row in enumerate(subgroup_rows):
        y_pos = float(row_index)
        ci_artist = subgroup_axes.plot(
            [float(row["lower"]), float(row["upper"])],
            [y_pos, y_pos],
            color=reference_color,
            linewidth=1.5,
            zorder=2,
        )[0]
        marker_artist = subgroup_axes.plot(
            float(row["estimate"]),
            y_pos,
            marker="s",
            markersize=marker_size + 0.8,
            markerfacecolor=matplotlib.colors.to_rgba(pdp_color, alpha=0.95),
            markeredgecolor=pdp_color,
            linestyle="None",
            zorder=3,
        )[0]
        ci_line_artists.append(ci_artist)
        estimate_artists.append(marker_artist)
        subgroup_row_records.append(
            {
                "row": row,
                "y_pos": y_pos,
            }
        )

    subgroup_axes.set_xlim(subgroup_x_min - subgroup_x_padding, subgroup_x_max + subgroup_x_padding)
    subgroup_axes.set_ylim(-0.7, len(subgroup_rows) - 0.3)
    subgroup_axes.invert_yaxis()
    subgroup_axes.set_yticks([])
    subgroup_axes.set_xlabel(
        str(display_payload.get("subgroup_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    subgroup_axes.set_title(
        str(display_payload.get("subgroup_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=10.0,
    )
    subgroup_axes.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    subgroup_axes.grid(axis="x", color=interval_fill, linewidth=0.55, linestyle=":")
    _apply_publication_axes_style(subgroup_axes)

    top_margin = 0.79 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.12, right=0.80, top=top_margin, bottom=0.14, wspace=0.36, hspace=0.56)

    y_axis_title_artist = fig.text(
        0.040,
        0.62,
        str(display_payload.get("y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
        ha="center",
        va="center",
    )

    legend = fig.legend(
        handles=[
            matplotlib.lines.Line2D([], [], color=ice_color, linewidth=1.4, alpha=0.30, label="ICE curves"),
            matplotlib.lines.Line2D([], [], color=pdp_color, linewidth=2.4, label="PDP mean"),
            matplotlib.lines.Line2D([], [], color=reference_color, linewidth=1.5, label="Subgroup interval"),
        ],
        loc="center right",
        bbox_to_anchor=(0.95, 0.72),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        handlelength=2.2,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_top_panel_label(*, axes_item: Any, label: str) -> Any:
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
            fontsize=max(panel_label_size + 1.6, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    top_panel_label_artists = [
        _add_top_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]))
        for record in top_panel_records
    ]

    subgroup_panel_bbox = subgroup_axes.get_window_extent(renderer=renderer)
    subgroup_panel_x0, subgroup_panel_y0 = fig.transFigure.inverted().transform(
        (subgroup_panel_bbox.x0, subgroup_panel_bbox.y0)
    )
    subgroup_panel_x1, subgroup_panel_y1 = fig.transFigure.inverted().transform(
        (subgroup_panel_bbox.x1, subgroup_panel_bbox.y1)
    )
    subgroup_panel_label_artist = fig.text(
        max(0.01, subgroup_panel_x0 - 0.018),
        subgroup_panel_y1 + 0.010,
        str(display_payload.get("subgroup_panel_label") or "").strip(),
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.6, 13.2),
        fontweight="bold",
        color="#2F3437",
        ha="left",
        va="bottom",
    )

    row_label_artists: list[Any] = []
    row_label_anchor_x = max(0.04, subgroup_panel_x0 - 0.012)
    for row_record in subgroup_row_records:
        _, label_y = _data_point_to_figure_xy(
            axes=subgroup_axes,
            figure=fig,
            x=float(subgroup_x_min - subgroup_x_padding),
            y=float(row_record["y_pos"]),
        )
        row_label_artists.append(
            fig.text(
                row_label_anchor_x,
                label_y,
                str(row_record["row"]["row_label"]),
                fontsize=max(tick_size - 0.3, 8.4),
                color="#334155",
                ha="right",
                va="center",
            )
        )

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
                bbox=subgroup_axes.title.get_window_extent(renderer=renderer),
                box_id=f"subgroup_panel_title_{str(display_payload.get('subgroup_panel_label') or '').strip()}",
                box_type="subgroup_panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"subgroup_x_axis_title_{str(display_payload.get('subgroup_panel_label') or '').strip()}",
                box_type="subgroup_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_panel_label_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{str(display_payload.get('subgroup_panel_label') or '').strip()}",
                box_type="panel_label",
            ),
        ]
    )
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    normalized_top_panels: list[dict[str, Any]] = []

    for record, panel_label_artist in zip(top_panel_records, top_panel_label_artists, strict=True):
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
                    box_type="pdp_reference_label",
                ),
            ]
        )

        reference_half_width = max(record["x_span"] * 0.003, 0.0015)
        reference_line_box = _data_box_to_layout_box(
            axes=axes_item,
            figure=fig,
            x0=float(panel["reference_value"]) - reference_half_width,
            y0=float(top_y_lower),
            x1=float(panel["reference_value"]) + reference_half_width,
            y1=float(top_y_upper),
            box_id=reference_line_box_id,
            box_type="pdp_reference_line",
        )
        reference_line_box["y0"] = max(float(panel_box["y0"]), float(reference_line_box["y0"]))
        reference_line_box["y1"] = min(float(panel_box["y1"]), float(reference_line_box["y1"]))
        guide_boxes.append(reference_line_box)

        normalized_pdp_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(
            record["normalized_pdp"]["x"],
            record["normalized_pdp"]["y"],
            strict=True,
        ):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            normalized_pdp_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_ice_curves: list[dict[str, Any]] = []
        for curve in record["raw_ice_curves"]:
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
            normalized_ice_curves.append({"curve_id": str(curve["curve_id"]), "points": normalized_points})

        normalized_top_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "subgroup_label": str(panel["subgroup_label"]),
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": reference_label_box_id,
                "pdp_points": normalized_pdp_points,
                "ice_curves": normalized_ice_curves,
            }
        )

    subgroup_panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=subgroup_axes.get_window_extent(renderer=renderer),
        box_id=f"panel_{str(display_payload.get('subgroup_panel_label') or '').strip()}",
        box_type="subgroup_panel",
    )
    panel_boxes.append(subgroup_panel_box)

    normalized_subgroup_rows: list[dict[str, Any]] = []
    row_band_half_height = 0.11
    marker_half_width = max((subgroup_x_max - subgroup_x_min) * 0.010, 0.006)
    for row_index, (row_record, row_label_artist, ci_artist, estimate_artist) in enumerate(
        zip(subgroup_row_records, row_label_artists, ci_line_artists, estimate_artists, strict=True),
        start=1,
    ):
        row = row_record["row"]
        label_box_id = f"subgroup_row_label_{row_index}"
        ci_box_id = f"subgroup_ci_segment_{row_index}"
        estimate_box_id = f"subgroup_estimate_marker_{row_index}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=row_label_artist.get_window_extent(renderer=renderer),
                box_id=label_box_id,
                box_type="subgroup_row_label",
            )
        )
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=subgroup_axes,
                figure=fig,
                x0=float(row["lower"]),
                y0=float(row_record["y_pos"]) - 0.012,
                x1=float(row["upper"]),
                y1=float(row_record["y_pos"]) + 0.012,
                box_id=ci_box_id,
                box_type="subgroup_ci_segment",
            )
        )
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=subgroup_axes,
                figure=fig,
                x0=float(row["estimate"]) - marker_half_width,
                y0=float(row_record["y_pos"]) - row_band_half_height,
                x1=float(row["estimate"]) + marker_half_width,
                y1=float(row_record["y_pos"]) + row_band_half_height,
                box_id=estimate_box_id,
                box_type="subgroup_estimate_marker",
            )
        )
        normalized_subgroup_rows.append(
            {
                "row_id": str(row["row_id"]),
                "panel_id": str(row["panel_id"]),
                "row_label": str(row["row_label"]),
                "estimate": float(row["estimate"]),
                "lower": float(row["lower"]),
                "upper": float(row["upper"]),
                "support_n": int(row["support_n"]),
                "label_box_id": label_box_id,
                "ci_segment_box_id": ci_box_id,
                "estimate_marker_box_id": estimate_box_id,
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
                "legend_labels": ["ICE curves", "PDP mean", "Subgroup interval"],
                "panels": normalized_top_panels,
                "subgroup_panel": {
                    "panel_label": str(display_payload.get("subgroup_panel_label") or "").strip(),
                    "title": str(display_payload.get("subgroup_panel_title") or "").strip(),
                    "x_label": str(display_payload.get("subgroup_x_label") or "").strip(),
                    "panel_box_id": subgroup_panel_box["box_id"],
                    "rows": normalized_subgroup_rows,
                },
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

def _render_python_accumulated_local_effects_panel(
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

    curve_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    bin_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    bar_fill = str(palette.get("secondary_soft") or bin_color).strip() or bin_color
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    all_y_values = [0.0]
    for panel in panels:
        all_y_values.extend(float(value) for value in panel["ale_curve"]["y"])
        all_y_values.extend(float(item["local_effect"]) for item in panel["local_effect_bins"])
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

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, panels, strict=True):
        ale_x = [float(value) for value in panel["ale_curve"]["x"]]
        ale_y = [float(value) for value in panel["ale_curve"]["y"]]
        panel_bins = list(panel["local_effect_bins"])
        x_candidates = ale_x + [float(item["bin_left"]) for item in panel_bins] + [float(item["bin_right"]) for item in panel_bins]
        x_min = min(x_candidates)
        x_max = max(x_candidates)
        x_span = max(x_max - x_min, 1e-6)
        x_padding = max(x_span * 0.10, 0.04)

        raw_bin_metrics: list[dict[str, Any]] = []
        for bin_item in panel_bins:
            bin_left = float(bin_item["bin_left"])
            bin_right = float(bin_item["bin_right"])
            bin_center = float(bin_item["bin_center"])
            local_effect = float(bin_item["local_effect"])
            axes_item.bar(
                [bin_center],
                [local_effect],
                width=(bin_right - bin_left) * 0.88,
                color=matplotlib.colors.to_rgba(bar_fill, alpha=0.55),
                edgecolor=bin_color,
                linewidth=0.8,
                zorder=2,
            )
            raw_bin_metrics.append(
                {
                    "bin_id": str(bin_item["bin_id"]),
                    "bin_left": bin_left,
                    "bin_right": bin_right,
                    "bin_center": bin_center,
                    "local_effect": local_effect,
                    "support_count": int(bin_item["support_count"]),
                }
            )

        axes_item.plot(
            ale_x,
            ale_y,
            color=curve_color,
            linewidth=2.4,
            zorder=4,
        )
        axes_item.axhline(0.0, color=reference_color, linewidth=0.8, linestyle=":", zorder=1)
        reference_value = float(panel["reference_value"])
        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=3,
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
                "ale_curve": {"x": ale_x, "y": ale_y},
                "raw_bin_metrics": raw_bin_metrics,
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
        handles=[
            matplotlib.lines.Line2D([], [], color=curve_color, linewidth=2.4, label="Accumulated local effect"),
            matplotlib.patches.Patch(
                facecolor=matplotlib.colors.to_rgba(bar_fill, alpha=0.55),
                edgecolor=bin_color,
                label="Local effect per bin",
            ),
        ],
        loc="lower center",
        bbox_to_anchor=(0.50, 0.045),
        ncol=2,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
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
                    box_type="ale_reference_label",
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
            box_type="ale_reference_line",
        )
        reference_line_box["y0"] = max(float(panel_box["y0"]), float(reference_line_box["y0"]))
        reference_line_box["y1"] = min(float(panel_box["y1"]), float(reference_line_box["y1"]))
        guide_boxes.append(reference_line_box)

        normalized_ale_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(
            record["ale_curve"]["x"],
            record["ale_curve"]["y"],
            strict=True,
        ):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            normalized_ale_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_bins: list[dict[str, Any]] = []
        for bin_index, bin_metric in enumerate(record["raw_bin_metrics"], start=1):
            bin_box_id = f"ale_bin_{panel_token}_{bin_index}"
            guide_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=float(bin_metric["bin_left"]),
                    y0=min(0.0, float(bin_metric["local_effect"])),
                    x1=float(bin_metric["bin_right"]),
                    y1=max(0.0, float(bin_metric["local_effect"])),
                    box_id=bin_box_id,
                    box_type="local_effect_bin",
                )
            )
            normalized_bins.append(
                {
                    "bin_id": str(bin_metric["bin_id"]),
                    "bin_box_id": bin_box_id,
                    "bin_center": float(bin_metric["bin_center"]),
                    "local_effect": float(bin_metric["local_effect"]),
                    "support_count": int(bin_metric["support_count"]),
                }
            )

        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": reference_label_box_id,
                "ale_points": normalized_ale_points,
                "local_effect_bins": normalized_bins,
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
                "legend_labels": ["Accumulated local effect", "Local effect per bin"],
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
