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

def _render_python_shap_grouped_local_explanation_panel(
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

    negative_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    positive_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    zero_line_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_panels: list[dict[str, Any]] = []
    max_abs_value = 0.0
    max_contribution_count = 0
    for panel in panels:
        contributions = []
        for contribution in panel["contributions"]:
            shap_value = float(contribution["shap_value"])
            max_abs_value = max(max_abs_value, abs(shap_value))
            contributions.append(
                {
                    "rank": int(contribution["rank"]),
                    "feature": str(contribution["feature"]),
                    "shap_value": shap_value,
                }
            )
        max_contribution_count = max(max_contribution_count, len(contributions))
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "group_label": str(panel["group_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "contributions": contributions,
            }
        )

    x_padding = max(max_abs_value * 0.20, 0.05)
    x_limit = max_abs_value + x_padding
    label_margin = max(x_limit * 0.06, 0.03)

    figure_width = max(8.8, 3.8 * len(normalized_panels) + 1.7)
    figure_height = max(4.8, 0.58 * max_contribution_count + 2.2)
    fig, axes = plt.subplots(1, len(normalized_panels), figsize=(figure_width, figure_height), squeeze=False)
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
    for axes_item, panel in zip(axes_list, normalized_panels, strict=True):
        contributions = list(panel["contributions"])
        row_positions = list(range(len(contributions)))
        values = [float(item["shap_value"]) for item in contributions]
        feature_labels = [str(item["feature"]) for item in contributions]
        colors = [
            matplotlib.colors.to_rgba(positive_color if value > 0 else negative_color, alpha=0.92)
            for value in values
        ]
        edge_colors = [positive_color if value > 0 else negative_color for value in values]

        bar_artists = axes_item.barh(
            row_positions,
            values,
            height=0.58,
            color=colors,
            edgecolor=edge_colors,
            linewidth=0.9,
            zorder=3,
        )
        value_label_artists: list[Any] = []
        for row_position, value in zip(row_positions, values, strict=True):
            text_x = value + label_margin if value > 0 else value - label_margin
            text_x = min(max(text_x, -x_limit + label_margin), x_limit - label_margin)
            value_label_artists.append(
                axes_item.text(
                    text_x,
                    row_position,
                    f"{value:+.2f}",
                    fontsize=max(tick_size - 0.6, 8.3),
                    color="#334155",
                    va="center",
                    ha="left" if value > 0 else "right",
                )
            )

        axes_item.axvline(0.0, color=zero_line_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit, x_limit)
        axes_item.set_ylim(-0.7, len(contributions) - 0.35)
        axes_item.set_yticks(row_positions)
        axes_item.set_yticklabels(feature_labels, fontsize=max(tick_size - 0.4, 8.5))
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(display_payload.get("x_label") or "").strip(),
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
        axes_item.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
        axes_item.tick_params(axis="y", length=0, pad=8)
        _apply_publication_axes_style(axes_item)
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")

        group_label_artist = axes_item.text(
            0.5,
            0.965,
            str(panel["group_label"]),
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.4, 8.8),
            color="#475569",
            ha="center",
            va="top",
        )
        baseline_label_artist = axes_item.text(
            0.02,
            0.885,
            f"Baseline {float(panel['baseline_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#475569",
            ha="left",
            va="top",
        )
        prediction_label_artist = axes_item.text(
            0.98,
            0.885,
            f"Prediction {float(panel['predicted_value']):.2f}",
            transform=axes_item.transAxes,
            fontsize=max(tick_size - 0.6, 8.2),
            color="#13293d",
            ha="right",
            va="top",
        )

        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "bar_artists": list(bar_artists),
                "value_label_artists": value_label_artists,
                "group_label_artist": group_label_artist,
                "baseline_label_artist": baseline_label_artist,
                "prediction_label_artist": prediction_label_artist,
                "panel_title_artist": axes_item.title,
            }
        )

    top_margin = 0.78 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.28, right=0.95, top=top_margin, bottom=0.18, wspace=0.32)
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
            max(0.01, panel_x0 - x_padding * 1.3),
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
    guide_boxes: list[dict[str, Any]] = []
    layout_metrics_panels: list[dict[str, Any]] = []
    zero_line_half_width = max((x_limit * 2.0) * 0.004, 0.01)

    for record, panel_label_artist in zip(panel_records, panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
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
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=f"panel_label_{panel_token}",
                    box_type="panel_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["group_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"group_label_{panel_token}",
                    box_type="group_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["baseline_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"baseline_label_{panel_token}",
                    box_type="baseline_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"prediction_label_{panel_token}",
                    box_type="prediction_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=f"x_axis_title_{panel_token}",
                    box_type="subplot_x_axis_title",
                ),
            ]
        )

        feature_label_box_ids: list[str] = []
        for label_index, tick_label in enumerate(axes_item.get_yticklabels(), start=1):
            if not str(tick_label.get_text() or "").strip():
                continue
            box_id = f"feature_label_{panel_token}_{label_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=tick_label.get_window_extent(renderer=renderer),
                    box_id=box_id,
                    box_type="feature_label",
                )
            )
            feature_label_box_ids.append(box_id)

        contribution_metrics: list[dict[str, Any]] = []
        for contribution_index, (contribution, bar_artist, value_label_artist) in enumerate(
            zip(panel["contributions"], record["bar_artists"], record["value_label_artists"], strict=True),
            start=1,
        ):
            bar_box_id = f"contribution_bar_{panel_token}_{contribution_index}"
            value_label_box_id = f"value_label_{panel_token}_{contribution_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=bar_artist.get_window_extent(renderer=renderer),
                    box_id=bar_box_id,
                    box_type="contribution_bar",
                )
            )
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=value_label_artist.get_window_extent(renderer=renderer),
                    box_id=value_label_box_id,
                    box_type="value_label",
                )
            )
            contribution_metrics.append(
                {
                    "rank": int(contribution["rank"]),
                    "feature": str(contribution["feature"]),
                    "shap_value": float(contribution["shap_value"]),
                    "bar_box_id": bar_box_id,
                    "feature_label_box_id": feature_label_box_ids[contribution_index - 1],
                    "value_label_box_id": value_label_box_id,
                }
            )

        zero_line_box_id = f"zero_line_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=-zero_line_half_width,
                y0=-0.7,
                x1=zero_line_half_width,
                y1=len(panel["contributions"]) - 0.35,
                box_id=zero_line_box_id,
                box_type="zero_line",
            )
        )
        layout_metrics_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "group_label": str(panel["group_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "panel_box_id": panel_box_id,
                "zero_line_box_id": zero_line_box_id,
                "contributions": contribution_metrics,
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
                "panels": layout_metrics_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

