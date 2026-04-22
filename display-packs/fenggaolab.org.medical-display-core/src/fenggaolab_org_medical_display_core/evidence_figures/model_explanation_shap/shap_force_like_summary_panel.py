from __future__ import annotations

from pathlib import Path
import re
import textwrap
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

def _render_python_shap_force_like_summary_panel(
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
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_panels: list[dict[str, Any]] = []
    all_values: list[float] = []
    max_contribution_count = 0
    for panel in panels:
        baseline_value = float(panel["baseline_value"])
        predicted_value = float(panel["predicted_value"])
        positive_cursor = baseline_value
        negative_cursor = baseline_value
        normalized_contributions: list[dict[str, Any]] = []
        for contribution in list(panel["contributions"]):
            shap_value = float(contribution["shap_value"])
            direction = "positive" if shap_value > 0 else "negative"
            if direction == "positive":
                start_value = positive_cursor
                end_value = positive_cursor + shap_value
                positive_cursor = end_value
            else:
                start_value = negative_cursor
                end_value = negative_cursor + shap_value
                negative_cursor = end_value
            normalized_contributions.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution.get("feature_value_text") or "").strip(),
                    "shap_value": shap_value,
                    "direction": direction,
                    "start_value": start_value,
                    "end_value": end_value,
                }
            )
            all_values.extend((start_value, end_value))
        normalized_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": baseline_value,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )
        all_values.extend((baseline_value, predicted_value))
        max_contribution_count = max(max_contribution_count, len(normalized_contributions))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.14, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    x_marker_half_width = max(x_span * 0.004, 0.0025)

    figure_width = max(8.8, 3.7 * len(normalized_panels) + 1.8)
    figure_height = max(4.9, 0.35 * max_contribution_count + 3.2)
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

    positive_band = (0.49, 0.57)
    negative_band = (0.30, 0.38)
    marker_y0 = 0.20
    marker_y1 = 0.74

    panel_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(axes_list, normalized_panels, strict=True):
        axes_item.set_xlim(x_lower, x_upper)
        axes_item.set_ylim(0.14, 0.84)
        axes_item.set_yticks([])
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
        axes_item.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)

        case_label_artist = axes_item.text(
            0.5,
            0.965,
            str(panel["case_label"]),
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

        segment_artists: list[dict[str, Any]] = []
        label_artists: list[Any] = []
        for contribution in panel["contributions"]:
            direction = str(contribution["direction"])
            start_value = float(contribution["start_value"])
            end_value = float(contribution["end_value"])
            left_value = min(start_value, end_value)
            right_value = max(start_value, end_value)
            width = max(right_value - left_value, 1e-9)
            tip_width = min(max(x_span * 0.018, width * 0.22), width * 0.45)
            y0, y1 = positive_band if direction == "positive" else negative_band
            y_mid = (y0 + y1) / 2.0
            if direction == "positive":
                polygon_points = [
                    (left_value, y0),
                    (right_value - tip_width, y0),
                    (right_value, y_mid),
                    (right_value - tip_width, y1),
                    (left_value, y1),
                    (left_value + tip_width * 0.35, y_mid),
                ]
                face_color = matplotlib.colors.to_rgba(positive_color, alpha=0.92)
                edge_color = positive_color
            else:
                polygon_points = [
                    (right_value, y0),
                    (left_value + tip_width, y0),
                    (left_value, y_mid),
                    (left_value + tip_width, y1),
                    (right_value, y1),
                    (right_value - tip_width * 0.35, y_mid),
                ]
                face_color = matplotlib.colors.to_rgba(negative_color, alpha=0.92)
                edge_color = negative_color
            segment_artist = matplotlib.patches.Polygon(
                polygon_points,
                closed=True,
                facecolor=face_color,
                edgecolor=edge_color,
                linewidth=0.85,
                zorder=3,
            )
            axes_item.add_patch(segment_artist)
            segment_artists.append({"artist": segment_artist, "contribution": contribution})

            label_text = (
                f"{contribution['feature']} = {contribution['feature_value_text']}"
                if contribution["feature_value_text"]
                else str(contribution["feature"])
            )
            label_artists.append(
                axes_item.text(
                    (left_value + right_value) / 2.0,
                    y_mid,
                    textwrap.fill(label_text, width=16),
                    fontsize=max(tick_size - 1.6, 7.0),
                    color="white",
                    ha="center",
                    va="center",
                    zorder=4,
                )
            )

        axes_item.axvline(float(panel["baseline_value"]), color=neutral_color, linewidth=1.0, linestyle="--", zorder=1)
        axes_item.axvline(float(panel["predicted_value"]), color="#13293d", linewidth=1.15, linestyle="-", zorder=1)
        panel_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "segment_artists": segment_artists,
                "label_artists": label_artists,
                "case_label_artist": case_label_artist,
                "baseline_label_artist": baseline_label_artist,
                "prediction_label_artist": prediction_label_artist,
                "panel_title_artist": axes_item.title,
            }
        )

    top_margin = 0.79 if show_figure_title else 0.87
    top_margin = max(0.72, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.10, right=0.95, top=top_margin, bottom=0.19, wspace=0.28)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
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
            fontsize=max(panel_label_size + 1.8, 13.2),
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
    normalized_layout_panels: list[dict[str, Any]] = []

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
                    bbox=record["case_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"case_label_{panel_token}",
                    box_type="case_label",
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
            ]
        )

        contribution_metrics: list[dict[str, Any]] = []
        for contribution_index, (segment_record, label_artist) in enumerate(
            zip(record["segment_artists"], record["label_artists"], strict=True),
            start=1,
        ):
            contribution = segment_record["contribution"]
            direction = str(contribution["direction"])
            segment_box_id = f"{direction}_force_segment_{panel_token}_{contribution_index}"
            label_box_id = f"force_label_{panel_token}_{contribution_index}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=segment_record["artist"].get_window_extent(renderer=renderer),
                    box_id=segment_box_id,
                    box_type=f"{direction}_force_segment",
                )
            )
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="force_feature_label",
                )
            )
            contribution_metrics.append(
                {
                    "feature": str(contribution["feature"]),
                    "feature_value_text": str(contribution["feature_value_text"]),
                    "shap_value": float(contribution["shap_value"]),
                    "direction": direction,
                    "start_value": float(contribution["start_value"]),
                    "end_value": float(contribution["end_value"]),
                    "segment_box_id": segment_box_id,
                    "label_box_id": label_box_id,
                }
            )

        baseline_marker_box_id = f"baseline_marker_{panel_token}"
        prediction_marker_box_id = f"prediction_marker_{panel_token}"
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["baseline_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["baseline_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=baseline_marker_box_id,
                box_type="baseline_marker",
            )
        )
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["predicted_value"]) - x_marker_half_width,
                y0=marker_y0,
                x1=float(panel["predicted_value"]) + x_marker_half_width,
                y1=marker_y1,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        normalized_layout_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "case_label": str(panel["case_label"]),
                "baseline_value": float(panel["baseline_value"]),
                "predicted_value": float(panel["predicted_value"]),
                "panel_box_id": panel_box_id,
                "baseline_marker_box_id": baseline_marker_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
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
                "panels": normalized_layout_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

