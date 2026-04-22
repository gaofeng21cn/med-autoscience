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
    _data_box_to_layout_box,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    dump_json,
)

def _render_python_shap_multigroup_decision_path_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    groups = list(display_payload.get("groups") or [])
    if len(groups) != 3:
        raise RuntimeError(f"{template_id} requires exactly three groups")

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

    group_colors = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("contrast") or palette.get("secondary") or "#2F5D8A").strip() or "#2F5D8A",
    ]
    baseline_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    feature_order = list(display_payload.get("feature_order") or [])
    if not feature_order:
        feature_order = [str(item["feature"]) for item in groups[0]["contributions"]]
    baseline_value = float(display_payload["baseline_value"])
    all_values = [baseline_value]
    for group in groups:
        all_values.append(float(group["predicted_value"]))
        for contribution in group["contributions"]:
            all_values.extend((float(contribution["start_value"]), float(contribution["end_value"])))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    y_start = -0.55
    row_positions = list(range(len(feature_order)))
    y_lower = row_positions[-1] + 0.55
    y_upper = y_start - 0.25

    fig = plt.figure(figsize=(9.0, max(4.8, 2.9 + 0.35 * len(feature_order))))
    ax = fig.add_subplot(1, 1, 1)
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.82,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    ax.set_xlim(x_lower, x_upper)
    ax.set_ylim(y_lower, y_upper)
    ax.set_yticks(row_positions)
    ax.set_yticklabels(feature_order, fontsize=max(tick_size - 0.2, 8.6))
    ax.set_xlabel(
        str(display_payload.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    ax.set_title(
        str(display_payload.get("panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=10.0,
    )
    ax.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    ax.tick_params(axis="y", length=0, pad=8, colors="#2F3437")
    ax.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
    ax.grid(axis="y", visible=False)
    _apply_publication_axes_style(ax)

    ax.axvline(baseline_value, color=baseline_color, linewidth=1.1, linestyle="--", zorder=1)

    line_records: list[dict[str, Any]] = []
    legend_handles: list[Any] = []
    label_padding = max(x_span * 0.04, 0.03)
    for group, color in zip(groups, group_colors, strict=True):
        x_values = [baseline_value] + [float(item["end_value"]) for item in group["contributions"]]
        y_values = [y_start] + row_positions
        line_artist = ax.plot(
            x_values,
            y_values,
            color=color,
            linewidth=2.1,
            marker="o",
            markersize=4.8,
            markeredgecolor="white",
            markeredgewidth=0.6,
            zorder=3,
        )[0]
        prediction_x = x_values[-1]
        prediction_y = y_values[-1]
        prediction_marker_artist = ax.scatter(
            [prediction_x],
            [prediction_y],
            s=42,
            color=color,
            edgecolors="white",
            linewidths=0.7,
            zorder=4,
        )
        if prediction_x >= baseline_value:
            label_x = min(x_upper - label_padding * 0.3, prediction_x + label_padding)
            ha = "left"
        else:
            label_x = max(x_lower + label_padding * 0.3, prediction_x - label_padding)
            ha = "right"
        prediction_label_artist = ax.text(
            label_x,
            prediction_y,
            f"{float(group['predicted_value']):.2f}",
            fontsize=max(tick_size - 0.6, 8.2),
            color="#334155",
            ha=ha,
            va="center",
            zorder=4,
        )
        legend_handles.append(
            matplotlib.lines.Line2D(
                [0],
                [0],
                color=color,
                linewidth=2.1,
                marker="o",
                markersize=5.0,
                markeredgecolor="white",
                markeredgewidth=0.6,
                label=str(group["group_label"]),
            )
        )
        line_records.append(
            {
                "group": group,
                "line_artist": line_artist,
                "prediction_marker_artist": prediction_marker_artist,
                "prediction_label_artist": prediction_label_artist,
            }
        )

    top_margin = 0.79 if show_figure_title else 0.89
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.26, right=0.56, top=top_margin, bottom=0.16)
    legend = fig.legend(
        handles=legend_handles,
        title=str(display_payload.get("legend_title") or "").strip(),
        loc="center left",
        bbox_to_anchor=(0.64, 0.54),
        bbox_transform=fig.transFigure,
        frameon=True,
        framealpha=1.0,
        edgecolor="#d7dee7",
        fontsize=max(tick_size - 0.5, 8.2),
        title_fontsize=max(tick_size - 0.1, 8.6),
    )
    legend.get_frame().set_facecolor("white")

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

    panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=ax.get_window_extent(renderer=renderer),
        box_id="panel_decision_path",
        box_type="panel",
    )
    panel_boxes = [panel_box]
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.title.get_window_extent(renderer=renderer),
                box_id="panel_title",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=ax.yaxis.label.get_window_extent(renderer=renderer),
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

    feature_label_box_ids: list[str] = []
    for index, tick_label in enumerate(ax.get_yticklabels(), start=1):
        if not str(tick_label.get_text() or "").strip():
            continue
        box_id = f"feature_label_{index}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=tick_label.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="feature_label",
            )
        )
        feature_label_box_ids.append(box_id)

    line_half_width = max((x_upper - x_lower) * 0.004, 0.003)
    marker_half_width = max((x_upper - x_lower) * 0.007, 0.004)
    marker_half_height = 0.10
    guide_boxes: list[dict[str, Any]] = [
        _data_box_to_layout_box(
            axes=ax,
            figure=fig,
            x0=baseline_value - line_half_width,
            y0=y_start,
            x1=baseline_value + line_half_width,
            y1=row_positions[-1],
            box_id="baseline_reference_line",
            box_type="baseline_reference_line",
        )
    ]

    metrics_groups: list[dict[str, Any]] = []
    for record in line_records:
        group = record["group"]
        group_token = re.sub(r"[^A-Za-z0-9]+", "_", str(group["group_id"])) or "group"
        line_box_id = f"decision_path_line_{group_token}"
        prediction_marker_box_id = f"prediction_marker_{group_token}"
        prediction_label_box_id = f"prediction_label_{group_token}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["line_artist"].get_window_extent(renderer=renderer),
                box_id=line_box_id,
                box_type="decision_path_line",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                box_id=prediction_label_box_id,
                box_type="prediction_label",
            )
        )
        prediction_x = float(group["contributions"][-1]["end_value"])
        prediction_y = row_positions[-1]
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=ax,
                figure=fig,
                x0=prediction_x - marker_half_width,
                y0=prediction_y - marker_half_height,
                x1=prediction_x + marker_half_width,
                y1=prediction_y + marker_half_height,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        metrics_groups.append(
            {
                "group_id": str(group["group_id"]),
                "group_label": str(group["group_label"]),
                "predicted_value": float(group["predicted_value"]),
                "line_box_id": line_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "prediction_label_box_id": prediction_label_box_id,
                "contributions": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "shap_value": float(item["shap_value"]),
                        "start_value": float(item["start_value"]),
                        "end_value": float(item["end_value"]),
                    }
                    for item in group["contributions"]
                ],
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
                "panel_box_id": "panel_decision_path",
                "baseline_line_box_id": "baseline_reference_line",
                "baseline_value": baseline_value,
                "legend_title": str(display_payload.get("legend_title") or "").strip(),
                "feature_order": [str(item) for item in feature_order],
                "feature_label_box_ids": feature_label_box_ids,
                "groups": metrics_groups,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
