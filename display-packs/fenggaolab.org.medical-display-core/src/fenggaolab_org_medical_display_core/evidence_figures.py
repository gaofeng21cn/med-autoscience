from __future__ import annotations

from pathlib import Path
from typing import Any

from matplotlib import pyplot as plt

from med_autoscience.controllers.display_surface_materialization import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    dump_json,
)


def render_time_to_event_risk_group_summary(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    risk_group_summaries = list(display_payload.get("risk_group_summaries") or [])
    if not risk_group_summaries:
        raise RuntimeError(f"{template_id} requires non-empty risk_group_summaries")

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
    group_colors = (
        str(palette.get("light") or palette.get("secondary_soft") or predicted_color).strip() or predicted_color,
        str(palette.get("secondary") or predicted_color).strip() or predicted_color,
        str(palette.get("primary") or observed_color).strip() or observed_color,
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)
    show_legend = _read_bool_override(layout_override, "show_legend", False)

    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )
    x_positions = list(range(len(risk_group_summaries)))
    group_labels = [str(item["label"]) for item in risk_group_summaries]
    predicted_risk = [float(item["mean_predicted_risk_5y"]) * 100.0 for item in risk_group_summaries]
    observed_risk = [float(item["observed_km_risk_5y"]) * 100.0 for item in risk_group_summaries]
    event_counts = [int(item["events_5y"]) for item in risk_group_summaries]
    bar_width = 0.34

    left_axes.bar(
        [position - bar_width / 2.0 for position in x_positions],
        predicted_risk,
        width=bar_width,
        color=predicted_color,
        label="Predicted",
    )
    left_axes.bar(
        [position + bar_width / 2.0 for position in x_positions],
        observed_risk,
        width=bar_width,
        color=observed_color,
        label="Observed",
    )
    left_axes.set_xticks(x_positions)
    left_axes.set_xticklabels(group_labels)
    left_axes.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    left_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
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
    left_axes.grid(axis="y", color=str(palette.get("light") or "#E7E1D8"), linewidth=0.8, linestyle=":")
    left_axes.grid(axis="x", visible=False)
    _apply_publication_axes_style(left_axes)
    legend = None
    if show_legend:
        legend = fig.legend(
            *left_axes.get_legend_handles_labels(),
            loc="lower center",
            bbox_to_anchor=(0.28, 0.02),
            ncol=2,
            frameon=False,
        )
    left_panel_label = left_axes.text(
        0.02,
        0.98,
        "A",
        transform=left_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    right_axes.bar(
        x_positions,
        event_counts,
        width=0.58,
        color=[group_colors[index % len(group_colors)] for index in x_positions],
    )
    upper_margin = max(max(event_counts) * 0.08, 1.2)
    for index, value in enumerate(event_counts):
        right_axes.text(
            index,
            float(value) + upper_margin * 0.35,
            str(value),
            ha="center",
            va="bottom",
            fontsize=tick_size - 1.0,
            color=neutral_color,
        )
    right_axes.set_xticks(x_positions)
    right_axes.set_xticklabels(group_labels)
    right_axes.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    right_axes.set_ylabel(
        str(display_payload.get("event_count_y_label") or "").strip(),
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
    right_axes.set_ylim(0.0, max(event_counts) + upper_margin)
    right_axes.grid(axis="y", color=str(palette.get("light") or "#E7E1D8"), linewidth=0.8, linestyle=":")
    right_axes.grid(axis="x", visible=False)
    _apply_publication_axes_style(right_axes)
    right_panel_label = right_axes.text(
        0.02,
        0.98,
        "B",
        transform=right_axes.transAxes,
        fontsize=panel_label_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    fig.subplots_adjust(
        left=0.09,
        right=0.98,
        top=0.82 if show_figure_title else 0.90,
        bottom=0.21 if show_legend else 0.12,
        wspace=0.26,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title",
            box_type="x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="y_axis_title",
            box_type="y_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_x_axis_title",
            box_type="subplot_x_axis_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.yaxis.label.get_window_extent(renderer=renderer),
            box_id="panel_right_y_axis_title",
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
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_right_title",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_A",
            box_type="panel_label",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_panel_label.get_window_extent(renderer=renderer),
            box_id="panel_label_B",
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
    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
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
            ],
            "guide_boxes": []
            if legend is None
            else [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "risk_group_summaries": risk_group_summaries,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
