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

