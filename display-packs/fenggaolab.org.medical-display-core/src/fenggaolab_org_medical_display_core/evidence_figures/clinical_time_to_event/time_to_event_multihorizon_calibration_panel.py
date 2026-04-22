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
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    dump_json,
)

def _render_python_time_to_event_multihorizon_calibration_panel(
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
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    observed_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    predicted_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    grid_color = str(palette.get("light") or "#E7E1D8").strip() or "#E7E1D8"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    marker_size = max(float(stroke.get("marker_size") or 4.2), 3.8)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    panel_count = len(panels)
    figure_width = max(9.8, 4.1 * panel_count + 0.8)
    fig, axes = plt.subplots(1, panel_count, figsize=(figure_width, 4.7))
    axes_list = list(axes) if hasattr(axes, "__iter__") else [axes]
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )
    x_axis_artist = fig.text(
        0.5,
        0.06,
        str(display_payload.get("x_label") or "").strip(),
        ha="center",
        va="center",
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    fig.subplots_adjust(
        left=0.08,
        right=0.99,
        top=0.82 if show_figure_title else 0.90,
        bottom=0.20,
        wspace=0.28,
    )

    panel_label_artists: list[Any] = []
    panel_title_artists: list[Any] = []
    normalized_panels: list[dict[str, Any]] = []
    for axes_index, (axes_item, panel) in enumerate(zip(axes_list, panels, strict=True), start=1):
        calibration_summary = list(panel.get("calibration_summary") or [])
        if not calibration_summary:
            raise RuntimeError(f"{template_id} panel {axes_index} requires non-empty calibration_summary")
        group_labels = [str(item["group_label"]) for item in calibration_summary]
        y_positions = [float(index) for index in range(1, len(calibration_summary) + 1)]
        predicted_risks = [float(item["predicted_risk"]) for item in calibration_summary]
        observed_risks = [float(item["observed_risk"]) for item in calibration_summary]
        x_upper = min(1.0, max(0.18, max(max(predicted_risks), max(observed_risks)) * 1.22 + 0.02))

        axes_item.set_xlim(0.0, x_upper)
        axes_item.set_ylim(0.5, len(calibration_summary) + 0.5)
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(group_labels, fontsize=tick_size, color=neutral_color)
        axes_item.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
        axes_item.tick_params(axis="x", labelsize=tick_size)
        axes_item.tick_params(axis="y", length=0, pad=6)
        axes_item.grid(axis="x", color=grid_color, linewidth=0.8, linestyle=":")
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)
        axes_item.set_title(
            str(panel.get("title") or "").strip(),
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=12.0,
        )
        panel_label_artists.append(
            axes_item.text(
                0.02,
                0.98,
                str(panel.get("panel_label") or "").strip(),
                transform=axes_item.transAxes,
                fontsize=panel_label_size,
                fontweight="bold",
                color=neutral_color,
                ha="left",
                va="top",
            )
        )
        panel_title_artists.append(axes_item.title)

        normalized_summary: list[dict[str, Any]] = []
        for group_index, (item, y_value, predicted_risk, observed_risk) in enumerate(
            zip(calibration_summary, y_positions, predicted_risks, observed_risks, strict=True),
            start=1,
        ):
            axes_item.hlines(
                y=y_value,
                xmin=min(predicted_risk, observed_risk),
                xmax=max(predicted_risk, observed_risk),
                color=neutral_color,
                linewidth=1.7,
                zorder=1,
            )
            axes_item.scatter(
                [predicted_risk],
                [y_value],
                s=marker_size * 18.0,
                color=predicted_color,
                label="Predicted" if axes_index == 1 and group_index == 1 else None,
                zorder=3,
            )
            axes_item.scatter(
                [observed_risk],
                [y_value],
                s=marker_size * 18.0,
                color=observed_color,
                label="Observed" if axes_index == 1 and group_index == 1 else None,
                zorder=4,
            )
            predicted_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=predicted_risk,
                y=y_value,
            )
            observed_x, _ = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=observed_risk,
                y=y_value,
            )
            normalized_summary.append(
                {
                    "group_label": str(item["group_label"]),
                    "group_order": int(item["group_order"]),
                    "n": int(item["n"]),
                    "events": int(item["events"]),
                    "predicted_risk": predicted_risk,
                    "observed_risk": observed_risk,
                    "predicted_x": predicted_x,
                    "observed_x": observed_x,
                    "y": point_y,
                }
            )
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "time_horizon_months": int(panel["time_horizon_months"]),
                "calibration_summary": normalized_summary,
            }
        )

    legend_handles, legend_labels = axes_list[0].get_legend_handles_labels()
    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=min(2, max(1, len(legend_labels))),
        frameon=False,
        fontsize=tick_size - 0.2,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=x_axis_artist.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="subplot_x_axis_title",
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

    panel_boxes: list[dict[str, Any]] = []
    for axes_item, panel, title_artist_item, label_artist_item in zip(
        axes_list,
        normalized_panels,
        panel_title_artists,
        panel_label_artists,
        strict=True,
    ):
        panel_label_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=axes_item.get_window_extent(renderer=renderer),
                box_id=f"panel_{panel_label_token}",
                box_type="calibration_panel",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=title_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{panel_label_token}",
                box_type="panel_title",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist_item.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{panel_label_token}",
                box_type="panel_label",
            )
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "panels": normalized_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

