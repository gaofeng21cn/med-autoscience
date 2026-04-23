from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from matplotlib import pyplot as plt

from ....shared import (
    _bbox_to_layout_box,
    _data_box_to_layout_box,
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    dump_json,
)
from ._draw import _build_shap_signed_importance_local_support_domain_figure
from ._prepare import _prepare_shap_signed_importance_local_support_domain_data


def _render_python_shap_signed_importance_local_support_domain_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )
    data = _prepare_shap_signed_importance_local_support_domain_data(
        template_id=template_id,
        display_payload=display_payload,
    )
    state = _build_shap_signed_importance_local_support_domain_figure(
        display_payload=display_payload,
        data=data,
    )

    fig = state["fig"]
    renderer = fig.canvas.get_renderer()
    title_artist = state["title_artist"]
    importance_ax = state["importance_ax"]
    local_ax = state["local_ax"]
    support_legend = state["support_legend"]
    support_y_axis_title_artist = state["support_y_axis_title_artist"]
    support_records = state["support_records"]
    support_panel_label_artists = state["support_panel_label_artists"]
    importance_panel_label_artist = state["importance_panel_label_artist"]
    local_panel_label_artist = state["local_panel_label_artist"]
    negative_direction_artist = state["negative_direction_artist"]
    positive_direction_artist = state["positive_direction_artist"]
    importance_bar_artists = state["importance_bar_artists"]
    importance_value_label_artists = state["importance_value_label_artists"]
    local_bar_artists = state["local_bar_artists"]
    local_value_label_artists = state["local_value_label_artists"]
    case_label_artist = state["case_label_artist"]
    baseline_label_artist = state["baseline_label_artist"]
    prediction_label_artist = state["prediction_label_artist"]

    importance_panel = data["importance_panel"]
    local_panel = data["local_panel"]
    normalized_importance_bars = data["normalized_importance_bars"]
    normalized_local_contributions = data["normalized_local_contributions"]
    importance_zero_line_half_width = data["importance_zero_line_half_width"]
    local_marker_half_width = data["local_marker_half_width"]
    plot_y_lower = data["plot_y_lower"]
    plot_y_upper = data["plot_y_upper"]
    band_y0 = data["band_y0"]
    band_y1 = data["band_y1"]
    support_legend_labels = data["support_legend_labels"]

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

    importance_panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(importance_panel["panel_label"])) or "A"
    importance_panel_box_id = f"panel_{importance_panel_token}"
    importance_panel_box = _bbox_to_layout_box(figure=fig, bbox=importance_ax.get_window_extent(renderer=renderer), box_id=importance_panel_box_id, box_type="panel")
    panel_boxes.append(importance_panel_box)
    layout_boxes.extend(
        [
            _bbox_to_layout_box(figure=fig, bbox=importance_ax.title.get_window_extent(renderer=renderer), box_id=f"panel_title_{importance_panel_token}", box_type="panel_title"),
            _bbox_to_layout_box(figure=fig, bbox=importance_panel_label_artist.get_window_extent(renderer=renderer), box_id=f"panel_label_{importance_panel_token}", box_type="panel_label"),
            _bbox_to_layout_box(figure=fig, bbox=negative_direction_artist.get_window_extent(renderer=renderer), box_id="negative_direction_label", box_type="negative_direction_label"),
            _bbox_to_layout_box(figure=fig, bbox=positive_direction_artist.get_window_extent(renderer=renderer), box_id="positive_direction_label", box_type="positive_direction_label"),
            _bbox_to_layout_box(figure=fig, bbox=importance_ax.xaxis.label.get_window_extent(renderer=renderer), box_id="x_axis_title", box_type="x_axis_title"),
        ]
    )

    importance_feature_label_ids: list[str] = []
    importance_bar_ids: list[str] = []
    importance_value_label_ids: list[str] = []
    for index, tick_label in enumerate(importance_ax.get_yticklabels(), start=1):
        box_id = f"feature_label_{index}"
        importance_feature_label_ids.append(box_id)
        layout_boxes.append(_bbox_to_layout_box(figure=fig, bbox=tick_label.get_window_extent(renderer=renderer), box_id=box_id, box_type="feature_label"))
    for index, artist in enumerate(importance_bar_artists, start=1):
        box_id = f"importance_bar_{index}"
        importance_bar_ids.append(box_id)
        layout_boxes.append(_bbox_to_layout_box(figure=fig, bbox=artist.get_window_extent(renderer=renderer), box_id=box_id, box_type="importance_bar"))
    for index, label_artist in enumerate(importance_value_label_artists, start=1):
        box_id = f"value_label_{index}"
        importance_value_label_ids.append(box_id)
        layout_boxes.append(_bbox_to_layout_box(figure=fig, bbox=label_artist.get_window_extent(renderer=renderer), box_id=box_id, box_type="value_label"))
    importance_zero_line_box_id = "zero_line"
    guide_boxes.append(
        _data_box_to_layout_box(
            axes=importance_ax,
            figure=fig,
            x0=-importance_zero_line_half_width,
            y0=-0.55,
            x1=importance_zero_line_half_width,
            y1=len(normalized_importance_bars) - 0.45,
            box_id=importance_zero_line_box_id,
            box_type="zero_line",
        )
    )

    local_panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(local_panel["panel_label"])) or "B"
    local_panel_box_id = f"panel_{local_panel_token}"
    local_panel_box = _bbox_to_layout_box(figure=fig, bbox=local_ax.get_window_extent(renderer=renderer), box_id=local_panel_box_id, box_type="panel")
    panel_boxes.append(local_panel_box)
    layout_boxes.extend(
        [
            _bbox_to_layout_box(figure=fig, bbox=local_ax.title.get_window_extent(renderer=renderer), box_id=f"panel_title_{local_panel_token}", box_type="panel_title"),
            _bbox_to_layout_box(figure=fig, bbox=local_panel_label_artist.get_window_extent(renderer=renderer), box_id=f"panel_label_{local_panel_token}", box_type="panel_label"),
            _bbox_to_layout_box(figure=fig, bbox=case_label_artist.get_window_extent(renderer=renderer), box_id=f"case_label_{local_panel_token}", box_type="case_label"),
            _bbox_to_layout_box(figure=fig, bbox=baseline_label_artist.get_window_extent(renderer=renderer), box_id=f"baseline_label_{local_panel_token}", box_type="baseline_label"),
            _bbox_to_layout_box(figure=fig, bbox=prediction_label_artist.get_window_extent(renderer=renderer), box_id=f"prediction_label_{local_panel_token}", box_type="prediction_label"),
            _bbox_to_layout_box(figure=fig, bbox=local_ax.xaxis.label.get_window_extent(renderer=renderer), box_id=f"x_axis_title_{local_panel_token}", box_type="subplot_x_axis_title"),
        ]
    )

    local_feature_label_ids: list[str] = []
    local_contribution_metrics: list[dict[str, Any]] = []
    for index, tick_label in enumerate(local_ax.get_yticklabels(), start=1):
        if not str(tick_label.get_text() or "").strip():
            continue
        box_id = f"feature_label_{local_panel_token}_{index}"
        local_feature_label_ids.append(box_id)
        layout_boxes.append(_bbox_to_layout_box(figure=fig, bbox=tick_label.get_window_extent(renderer=renderer), box_id=box_id, box_type="feature_label"))
    for contribution_index, (contribution, bar_artist, value_label_artist) in enumerate(zip(normalized_local_contributions, local_bar_artists, local_value_label_artists, strict=True), start=1):
        bar_box_id = f"contribution_bar_{local_panel_token}_{contribution_index}"
        value_label_box_id = f"contribution_label_{local_panel_token}_{contribution_index}"
        layout_boxes.append(_bbox_to_layout_box(figure=fig, bbox=bar_artist.get_window_extent(renderer=renderer), box_id=bar_box_id, box_type="contribution_bar"))
        layout_boxes.append(_bbox_to_layout_box(figure=fig, bbox=value_label_artist.get_window_extent(renderer=renderer), box_id=value_label_box_id, box_type="contribution_label"))
        local_contribution_metrics.append(
            {
                "feature": str(contribution["feature"]),
                "feature_value_text": str(contribution["feature_value_text"]),
                "shap_value": float(contribution["shap_value"]),
                "start_value": float(contribution["start_value"]),
                "end_value": float(contribution["end_value"]),
                "bar_box_id": bar_box_id,
                "label_box_id": local_feature_label_ids[contribution_index - 1],
            }
        )

    local_baseline_marker_box_id = f"baseline_marker_{local_panel_token}"
    local_prediction_marker_box_id = f"prediction_marker_{local_panel_token}"
    guide_boxes.append(_data_box_to_layout_box(axes=local_ax, figure=fig, x0=float(local_panel["baseline_value"]) - local_marker_half_width, y0=-0.95, x1=float(local_panel["baseline_value"]) + local_marker_half_width, y1=len(normalized_local_contributions) - 0.45, box_id=local_baseline_marker_box_id, box_type="baseline_marker"))
    guide_boxes.append(_data_box_to_layout_box(axes=local_ax, figure=fig, x0=float(local_panel["predicted_value"]) - local_marker_half_width, y0=-0.95, x1=float(local_panel["predicted_value"]) + local_marker_half_width, y1=len(normalized_local_contributions) - 0.45, box_id=local_prediction_marker_box_id, box_type="prediction_marker"))

    layout_boxes.extend(
        [
            _bbox_to_layout_box(figure=fig, bbox=support_y_axis_title_artist.get_window_extent(renderer=renderer), box_id="support_y_axis_title", box_type="subplot_y_axis_title"),
            _bbox_to_layout_box(figure=fig, bbox=support_legend.get_window_extent(renderer=renderer), box_id="support_legend_box", box_type="legend_box"),
            _bbox_to_layout_box(figure=fig, bbox=support_legend.get_title().get_window_extent(renderer=renderer), box_id="support_legend_title", box_type="legend_title"),
        ]
    )

    layout_metrics_support_panels: list[dict[str, Any]] = []
    for record, panel_label_artist in zip(support_records, support_panel_label_artists, strict=True):
        axes_item = record["axes"]
        panel = record["panel"]
        panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(panel["panel_label"])) or "panel"
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(figure=fig, bbox=axes_item.get_window_extent(renderer=renderer), box_id=panel_box_id, box_type="panel")
        panel_boxes.append(panel_box)

        reference_line_box_id = f"reference_line_{panel_token}"
        reference_half_width = max(record["x_span"] * 0.003, 0.0015)
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(panel["reference_value"]) - reference_half_width,
                y0=plot_y_lower,
                x1=float(panel["reference_value"]) + reference_half_width,
                y1=plot_y_upper,
                box_id=reference_line_box_id,
                box_type="support_domain_reference_line",
            )
        )

        layout_boxes.extend(
            [
                _bbox_to_layout_box(figure=fig, bbox=record["panel_title_artist"].get_window_extent(renderer=renderer), box_id=f"panel_title_{panel_token}", box_type="panel_title"),
                _bbox_to_layout_box(figure=fig, bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer), box_id=f"x_axis_title_{panel_token}", box_type="subplot_x_axis_title"),
                _bbox_to_layout_box(figure=fig, bbox=panel_label_artist.get_window_extent(renderer=renderer), box_id=f"panel_label_{panel_token}", box_type="panel_label"),
                _bbox_to_layout_box(figure=fig, bbox=record["reference_label_artist"].get_window_extent(renderer=renderer), box_id=f"reference_label_{panel_token}", box_type="support_domain_reference_label"),
            ]
        )

        normalized_response_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(record["curve_x"], record["curve_y"], strict=True):
            point_x, point_y = _data_point_to_figure_xy(axes=axes_item, figure=fig, x=float(feature_value), y=float(response_value))
            normalized_response_points.append({"feature_value": float(feature_value), "response_value": float(response_value), "x": point_x, "y": point_y})

        normalized_support_segments: list[dict[str, Any]] = []
        for segment_index, (segment, label_artist) in enumerate(zip(panel["support_segments"], record["support_label_artists"], strict=True), start=1):
            segment_box_id = f"support_segment_{panel_token}_{segment_index}"
            label_box_id = f"support_label_{panel_token}_{segment_index}"
            guide_boxes.append(_data_box_to_layout_box(axes=axes_item, figure=fig, x0=float(segment["domain_start"]), y0=band_y0, x1=float(segment["domain_end"]), y1=band_y1, box_id=segment_box_id, box_type="support_domain_segment"))
            layout_boxes.append(_bbox_to_layout_box(figure=fig, bbox=label_artist.get_window_extent(renderer=renderer), box_id=label_box_id, box_type="support_label"))
            normalized_support_segments.append(
                {
                    "segment_id": str(segment["segment_id"]),
                    "segment_label": str(segment["segment_label"]),
                    "support_kind": str(segment["support_kind"]),
                    "domain_start": float(segment["domain_start"]),
                    "domain_end": float(segment["domain_end"]),
                    "segment_box_id": segment_box_id,
                    "label_box_id": label_box_id,
                }
            )

        layout_metrics_support_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": f"reference_label_{panel_token}",
                "response_points": normalized_response_points,
                "support_segments": normalized_support_segments,
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
                "global_feature_order": [str(item) for item in list(display_payload.get("global_feature_order") or [])],
                "local_feature_order": [str(item) for item in list(display_payload.get("local_feature_order") or [])],
                "importance_panel": {
                    "panel_id": str(importance_panel["panel_id"]),
                    "panel_label": str(importance_panel["panel_label"]),
                    "title": str(importance_panel["title"]),
                    "panel_box_id": importance_panel_box_id,
                    "zero_line_box_id": importance_zero_line_box_id,
                    "bars": [
                        {
                            "rank": int(item["rank"]),
                            "feature": str(item["feature"]),
                            "direction": "positive" if float(item["signed_importance_value"]) > 0.0 else "negative",
                            "signed_importance_value": float(item["signed_importance_value"]),
                            "bar_box_id": importance_bar_ids[index],
                            "feature_label_box_id": importance_feature_label_ids[index],
                            "value_label_box_id": importance_value_label_ids[index],
                        }
                        for index, item in enumerate(normalized_importance_bars)
                    ],
                },
                "local_panel": {
                    "panel_id": str(local_panel["panel_id"]),
                    "panel_label": str(local_panel["panel_label"]),
                    "title": str(local_panel["title"]),
                    "case_label": str(local_panel["case_label"]),
                    "baseline_value": float(local_panel["baseline_value"]),
                    "predicted_value": float(local_panel["predicted_value"]),
                    "panel_box_id": local_panel_box_id,
                    "baseline_marker_box_id": local_baseline_marker_box_id,
                    "prediction_marker_box_id": local_prediction_marker_box_id,
                    "contributions": local_contribution_metrics,
                },
                "support_panels": layout_metrics_support_panels,
                "support_legend_labels": support_legend_labels,
                "support_legend_title": str(display_payload.get("support_legend_title") or "").strip(),
                "support_legend_title_box_id": "support_legend_title",
                "support_y_axis_title_box_id": "support_y_axis_title",
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
