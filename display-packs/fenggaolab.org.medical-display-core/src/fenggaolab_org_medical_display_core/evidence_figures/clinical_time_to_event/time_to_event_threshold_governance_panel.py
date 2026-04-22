from __future__ import annotations

from pathlib import Path
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

def _render_python_time_to_event_threshold_governance_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    threshold_summaries = list(display_payload.get("threshold_summaries") or [])
    risk_group_summaries = list(display_payload.get("risk_group_summaries") or [])
    if not threshold_summaries or not risk_group_summaries:
        raise RuntimeError(f"{template_id} requires non-empty threshold_summaries and risk_group_summaries")

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
    primary_color = str(palette.get("primary") or observed_color).strip() or observed_color
    threshold_fill = str(palette.get("primary_soft") or "#EAF2F5").strip() or "#EAF2F5"
    threshold_fill_alt = str(palette.get("secondary_soft") or "#F4EEE5").strip() or "#F4EEE5"
    grid_color = str(palette.get("light") or "#E7E1D8").strip() or "#E7E1D8"
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = float(typography.get("panel_label_size") or 11.0)
    marker_size = max(float(stroke.get("marker_size") or 4.2), 3.8)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    figure_height = max(4.4, 3.2 + 0.34 * len(threshold_summaries))
    fig, (left_axes, right_axes) = plt.subplots(1, 2, figsize=(11.2, figure_height))
    fig.patch.set_facecolor("white")
    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
        )

    left_axes.set_axis_off()
    left_axes.set_xlim(0.0, 1.0)
    left_axes.set_ylim(0.0, 1.0)
    left_axes.set_title(
        str(display_payload.get("threshold_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        pad=12.0,
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

    card_top = 0.82
    card_bottom = 0.10
    card_gap = 0.05
    card_x0 = 0.10
    card_x1 = 0.92
    available_height = card_top - card_bottom - card_gap * max(len(threshold_summaries) - 1, 0)
    card_height = available_height / max(len(threshold_summaries), 1)
    threshold_card_patches: list[tuple[str, Any]] = []
    for index, item in enumerate(threshold_summaries, start=1):
        y1 = card_top - (index - 1) * (card_height + card_gap)
        y0 = y1 - card_height
        fill_color = threshold_fill if index % 2 == 1 else threshold_fill_alt
        card_patch = matplotlib.patches.FancyBboxPatch(
            (card_x0, y0),
            card_x1 - card_x0,
            card_height,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            transform=left_axes.transAxes,
            linewidth=1.2,
            facecolor=fill_color,
            edgecolor=neutral_color,
        )
        left_axes.add_patch(card_patch)
        accent_patch = matplotlib.patches.Rectangle(
            (card_x0, y0),
            0.022,
            card_height,
            transform=left_axes.transAxes,
            linewidth=0,
            facecolor=primary_color if index % 2 == 1 else predicted_color,
        )
        left_axes.add_patch(accent_patch)
        left_axes.text(
            card_x0 + 0.05,
            y1 - card_height * 0.26,
            str(item["threshold_label"]),
            transform=left_axes.transAxes,
            fontsize=tick_size + 0.2,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="center",
        )
        left_axes.text(
            card_x0 + 0.05,
            y1 - card_height * 0.49,
            f"Threshold {float(item['threshold']):.0%}",
            transform=left_axes.transAxes,
            fontsize=tick_size - 0.1,
            color=neutral_color,
            ha="left",
            va="center",
        )
        left_axes.text(
            card_x0 + 0.05,
            y0 + card_height * 0.26,
            f"Sens {float(item['sensitivity']):.0%} · Spec {float(item['specificity']):.0%}",
            transform=left_axes.transAxes,
            fontsize=tick_size - 0.4,
            color=neutral_color,
            ha="left",
            va="center",
        )
        left_axes.text(
            card_x1 - 0.04,
            y0 + card_height * 0.26,
            f"NB {float(item['net_benefit']):.3f}",
            transform=left_axes.transAxes,
            fontsize=tick_size - 0.2,
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        threshold_card_patches.append((f"threshold_card_{index}", card_patch))

    right_axes.set_title(
        str(display_payload.get("calibration_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
        pad=12.0,
    )
    right_axes.set_xlabel(
        str(display_payload.get("calibration_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    group_labels = [str(item["group_label"]) for item in risk_group_summaries]
    y_positions = [float(index) for index in range(1, len(risk_group_summaries) + 1)]
    predicted_risks = [float(item["predicted_risk"]) for item in risk_group_summaries]
    observed_risks = [float(item["observed_risk"]) for item in risk_group_summaries]
    x_upper = max(max(predicted_risks), max(observed_risks))
    x_upper = min(1.0, max(0.18, x_upper * 1.22 + 0.02))
    right_axes.set_xlim(0.0, x_upper)
    right_axes.set_ylim(0.5, len(risk_group_summaries) + 0.5)
    right_axes.set_yticks(y_positions)
    right_axes.set_yticklabels(group_labels, fontsize=tick_size, color=neutral_color)
    right_axes.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(xmax=1.0, decimals=0))
    right_axes.tick_params(axis="x", labelsize=tick_size)
    right_axes.tick_params(axis="y", length=0, pad=7)
    right_axes.grid(axis="x", color=grid_color, linewidth=0.8, linestyle=":")
    right_axes.grid(axis="y", visible=False)
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

    normalized_risk_group_summaries: list[dict[str, Any]] = []
    for index, (item, y_value, predicted_risk, observed_risk) in enumerate(
        zip(risk_group_summaries, y_positions, predicted_risks, observed_risks, strict=True),
        start=1,
    ):
        right_axes.hlines(
            y=y_value,
            xmin=min(predicted_risk, observed_risk),
            xmax=max(predicted_risk, observed_risk),
            color=neutral_color,
            linewidth=1.7,
            zorder=1,
        )
        right_axes.scatter(
            [predicted_risk],
            [y_value],
            s=marker_size * 18.0,
            color=predicted_color,
            label="Predicted" if index == 1 else None,
            zorder=3,
        )
        right_axes.scatter(
            [observed_risk],
            [y_value],
            s=marker_size * 18.0,
            color=observed_color,
            label="Observed" if index == 1 else None,
            zorder=4,
        )
        predicted_x, point_y = _data_point_to_figure_xy(
            axes=right_axes,
            figure=fig,
            x=predicted_risk,
            y=y_value,
        )
        observed_x, _ = _data_point_to_figure_xy(
            axes=right_axes,
            figure=fig,
            x=observed_risk,
            y=y_value,
        )
        normalized_risk_group_summaries.append(
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

    legend_handles, legend_labels = right_axes.get_legend_handles_labels()
    legend = fig.legend(
        legend_handles,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.72, 0.03),
        ncol=min(2, max(1, len(legend_labels))),
        frameon=False,
        fontsize=tick_size - 0.2,
    )

    fig.subplots_adjust(
        left=0.07,
        right=0.98,
        top=0.82 if show_figure_title else 0.90,
        bottom=0.18,
        wspace=0.20,
    )
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=left_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_title_A",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.title.get_window_extent(renderer=renderer),
            box_id="panel_title_B",
            box_type="panel_title",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=right_axes.xaxis.label.get_window_extent(renderer=renderer),
            box_id="x_axis_title_B",
            box_type="subplot_x_axis_title",
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
    normalized_threshold_summaries: list[dict[str, Any]] = []
    for index, (card_box_id, card_patch) in enumerate(threshold_card_patches):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=card_patch.get_window_extent(renderer=renderer),
                box_id=card_box_id,
                box_type="threshold_card",
            )
        )
        threshold_item = threshold_summaries[index]
        normalized_threshold_summaries.append(
            {
                "threshold_label": str(threshold_item["threshold_label"]),
                "threshold": float(threshold_item["threshold"]),
                "sensitivity": float(threshold_item["sensitivity"]),
                "specificity": float(threshold_item["specificity"]),
                "net_benefit": float(threshold_item["net_benefit"]),
                "card_box_id": card_box_id,
            }
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
                    box_id="threshold_panel",
                    box_type="threshold_panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=right_axes.get_window_extent(renderer=renderer),
                    box_id="calibration_panel",
                    box_type="calibration_panel",
                ),
            ],
            "guide_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=legend.get_window_extent(renderer=renderer),
                    box_id="legend",
                    box_type="legend",
                )
            ],
            "metrics": {
                "threshold_summaries": normalized_threshold_summaries,
                "risk_group_summaries": normalized_risk_group_summaries,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

