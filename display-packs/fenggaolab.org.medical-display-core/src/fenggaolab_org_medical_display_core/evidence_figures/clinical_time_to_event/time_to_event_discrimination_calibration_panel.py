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
    _wrap_flow_text_to_width,
    dump_json,
)

def _render_python_time_to_event_discrimination_calibration_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    discrimination_points = list(display_payload.get("discrimination_points") or [])
    calibration_summary = list(display_payload.get("calibration_summary") or [])
    if not discrimination_points or not calibration_summary:
        raise RuntimeError(f"{template_id} requires non-empty discrimination_points and calibration_summary")

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
    highlight_color = str(palette.get("light") or palette.get("secondary_soft") or comparator_color).strip() or comparator_color
    marker_size = max(float(stroke.get("marker_size") or 4.5), 3.8)
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.8, 4.3))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )

    c_index_values = [float(item["c_index"]) for item in discrimination_points]
    x_range = max(max(c_index_values) - min(c_index_values), 0.01)
    x_floor = max(0.0, min(c_index_values) - max(0.012, x_range * 0.8))
    x_ceiling = min(1.0, max(c_index_values) + max(0.012, x_range * 1.2))
    y_positions = list(range(len(discrimination_points)))[::-1]
    left_axes.set_xlim(x_floor, x_ceiling)
    left_axes.set_ylim(-0.5, len(discrimination_points) - 0.5)
    left_axes.set_yticks(y_positions)
    left_axes.set_yticklabels(
        [str(item["label"]) for item in discrimination_points],
        fontsize=tick_size,
        color=neutral_color,
    )
    discrimination_marker_boxes: list[dict[str, Any]] = []
    for y_position, item in zip(y_positions, discrimination_points, strict=True):
        label = str(item["label"])
        c_index = float(item["c_index"])
        point_color = comparator_color if "lasso" in label.casefold() else model_color
        left_axes.hlines(
            y=y_position,
            xmin=x_floor,
            xmax=c_index,
            linewidth=2.1,
            color=point_color,
            zorder=2,
        )
        left_axes.scatter([c_index], [y_position], s=(marker_size * 11.0), color=point_color, zorder=3)
        annotation_text = str(item.get("annotation") or f"{c_index:.3f}").strip()
        x_offset = max(x_range * 0.07, 0.0025)
        text_x = c_index + x_offset
        text_ha = "left"
        if text_x > x_ceiling - x_offset * 0.35:
            text_x = c_index - x_offset
            text_ha = "right"
        left_axes.text(
            text_x,
            y_position + 0.02,
            annotation_text,
            fontsize=tick_size - 0.2,
            color=neutral_color,
            va="center",
            ha=text_ha,
        )
        discrimination_marker_boxes.append(
            {
                "label": label,
                "c_index": c_index,
                "y": float(y_position),
            }
        )
    left_axes.set_xlabel(
        str(display_payload.get("discrimination_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_ylabel(
        "Model",
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_title(
        str(display_payload.get("panel_a_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.tick_params(axis="x", labelsize=tick_size)
    left_axes.tick_params(axis="y", length=0, pad=6)
    left_axes.grid(axis="y", visible=False)
    left_axes.grid(axis="x", color=highlight_color, linewidth=0.8, linestyle=":")
    _apply_publication_axes_style(left_axes)
    left_axes.text(
        -0.10,
        1.04,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
    )

    risk_deciles = [int(item["group_order"]) for item in calibration_summary]
    predicted_risk = [float(item["predicted_risk_5y"]) * 100.0 for item in calibration_summary]
    observed_risk = [float(item["observed_risk_5y"]) * 100.0 for item in calibration_summary]
    calibration_marker_boxes: list[dict[str, Any]] = []
    right_axes.plot(
        risk_deciles,
        predicted_risk,
        linewidth=2.2,
        marker="o",
        markersize=marker_size,
        color=comparator_color,
        label="Predicted",
        zorder=2,
    )
    right_axes.plot(
        risk_deciles,
        observed_risk,
        linewidth=2.2,
        marker="o",
        markersize=marker_size,
        color=model_color,
        label="Observed",
        zorder=3,
    )
    y_top = max(max(predicted_risk), max(observed_risk))
    right_axes.set_xlim(0.7, max(risk_deciles) + 0.3)
    right_axes.set_ylim(0.0, max(4.0, y_top * 1.18))
    right_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylabel(
        str(display_payload.get("calibration_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_title(
        str(display_payload.get("panel_b_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_xticks(risk_deciles)
    right_axes.set_xticklabels([str(item) for item in risk_deciles], fontsize=tick_size, color=neutral_color)
    right_axes.tick_params(axis="y", labelsize=tick_size)
    right_axes.grid(axis="y", color=highlight_color, linewidth=0.8, linestyle=":")
    right_axes.grid(axis="x", visible=False)
    _apply_publication_axes_style(right_axes)
    right_axes.text(
        -0.10,
        1.04,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
    )
    legend_handles, legend_labels = right_axes.get_legend_handles_labels()
    for group_order, predicted_value, observed_value in zip(risk_deciles, predicted_risk, observed_risk, strict=True):
        calibration_marker_boxes.append(
            {
                "group_order": group_order,
                "predicted_risk_pct": predicted_value,
                "observed_risk_pct": observed_value,
            }
        )

    calibration_callout = display_payload.get("calibration_callout")
    callout_artist = None
    if isinstance(calibration_callout, dict):
        callout_group_label = str(calibration_callout.get("group_label") or "").strip()
        callout_predicted = float(calibration_callout["predicted_risk_5y"]) * 100.0
        callout_observed = float(calibration_callout["observed_risk_5y"]) * 100.0
        callout_events = int(calibration_callout.get("events_5y") or 0)
        callout_n = int(calibration_callout.get("n") or 0)
        callout_lines = _wrap_flow_text_to_width(
            (
                f"{callout_group_label}: {callout_predicted:.2f}% predicted, "
                f"{callout_observed:.2f}% observed, {callout_events}/{callout_n} events"
            ),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.19,
            font_size=max(tick_size - 0.6, 8.6),
            font_weight="normal",
        )
        callout_artist = right_axes.text(
            0.03,
            0.88,
            "\n".join(callout_lines),
            transform=right_axes.transAxes,
            fontsize=max(tick_size - 0.6, 8.6),
            color=neutral_color,
            ha="left",
            va="top",
            bbox={
                "boxstyle": "round,pad=0.26,rounding_size=0.18",
                "facecolor": matplotlib.colors.to_rgba(highlight_color, alpha=0.94),
                "edgecolor": neutral_color,
                "linewidth": 0.9,
            },
        )

    fig.subplots_adjust(
        left=0.10,
        right=0.96,
        top=0.72 if show_figure_title else 0.78,
        bottom=0.24,
        wspace=0.28,
    )
    legend = fig.legend(
        legend_handles,
        legend_labels,
        frameon=False,
        loc="lower center",
        bbox_to_anchor=(0.50, 0.035),
        ncol=min(2, max(1, len(legend_labels))),
    )
    fig.canvas.draw()
    if callout_artist is not None:
        renderer = fig.canvas.get_renderer()
        right_panel_bbox = right_axes.get_window_extent(renderer=renderer)
        right_title_bbox = right_axes.title.get_window_extent(renderer=renderer)
        callout_bbox = callout_artist.get_window_extent(renderer=renderer)
        horizontal_padding_px = max(right_panel_bbox.width * 0.03, 10.0)
        vertical_padding_px = max(right_panel_bbox.height * 0.08, 12.0)
        target_x0_px = right_panel_bbox.x0 + horizontal_padding_px
        target_y1_px = min(right_panel_bbox.y1 - vertical_padding_px, right_title_bbox.y0 - vertical_padding_px)
        minimum_y1_px = right_panel_bbox.y0 + vertical_padding_px + callout_bbox.height
        target_y1_px = max(target_y1_px, minimum_y1_px)
        target_axes_x, target_axes_y = right_axes.transAxes.inverted().transform((target_x0_px, target_y1_px))
        callout_artist.set_position((float(target_axes_x), float(target_axes_y)))
        fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_left_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_left_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_left_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="calibration_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="calibration_y_axis_title",
            box_type="subplot_y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_right_title",
            box_type="panel_title",
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
    for index, marker in enumerate(discrimination_marker_boxes, start=1):
        marker_width = max((x_ceiling - x_floor) * 0.015, 0.002)
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=left_axes,
                figure=fig,
                x0=float(marker["c_index"]) - marker_width,
                y0=float(marker["y"]) - 0.14,
                x1=float(marker["c_index"]) + marker_width,
                y1=float(marker["y"]) + 0.14,
                box_id=f"discrimination_marker_{index}",
                box_type="metric_marker",
            )
        )
    for index, marker in enumerate(calibration_marker_boxes, start=1):
        marker_half_width = 0.14
        marker_half_height = max(y_top * 0.03, 0.18)
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=right_axes,
                figure=fig,
                x0=float(marker["group_order"]) - marker_half_width,
                y0=float(marker["predicted_risk_pct"]) - marker_half_height,
                x1=float(marker["group_order"]) + marker_half_width,
                y1=float(marker["predicted_risk_pct"]) + marker_half_height,
                box_id=f"predicted_marker_{index}",
                box_type="metric_marker",
            )
        )
        layout_boxes.append(
            _data_box_to_layout_box(
                axes=right_axes,
                figure=fig,
                x0=float(marker["group_order"]) - marker_half_width,
                y0=float(marker["observed_risk_pct"]) - marker_half_height,
                x1=float(marker["group_order"]) + marker_half_width,
                y1=float(marker["observed_risk_pct"]) + marker_half_height,
                box_id=f"observed_marker_{index}",
                box_type="metric_marker",
            )
        )
    if callout_artist is not None:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=callout_artist.get_window_extent(renderer=renderer),
                box_id="annotation_callout",
                box_type="annotation_block",
            )
        )
    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.get_window_extent(renderer=renderer),
            box_id="panel_left",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.get_window_extent(renderer=renderer),
            box_id="panel_right",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=legend.get_window_extent(renderer=renderer),
            box_id="legend",
            box_type="legend",
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
                "discrimination_points": discrimination_points,
                "calibration_summary": calibration_summary,
                "calibration_callout": calibration_callout,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
