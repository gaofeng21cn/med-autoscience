from __future__ import annotations

from pathlib import Path
from typing import Any

from matplotlib import pyplot as plt

from ....shared import (
    _bbox_to_layout_box,
    _data_box_to_layout_box,
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    dump_json,
)
from ._draw import _build_genomic_alteration_consequence_figure
from ._prepare import _prepare_genomic_alteration_consequence_data


def _render_python_genomic_alteration_consequence_panel(
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
    data = _prepare_genomic_alteration_consequence_data(
        template_id=template_id,
        display_payload=display_payload,
    )
    state = _build_genomic_alteration_consequence_figure(
        display_payload=display_payload,
        data=data,
    )

    fig = state["fig"]
    renderer = fig.canvas.get_renderer()
    title_artist = state["title_artist"]
    matrix_axes = state["matrix_axes"]
    panel_label_a = state["panel_label_a"]
    track_label_artists = state["track_label_artists"]
    burden_bars = state["burden_bars"]
    frequency_bars = state["frequency_bars"]
    annotation_cell_patches = state["annotation_cell_patches"]
    alteration_overlay_patches = state["alteration_overlay_patches"]
    alteration_cell_patches = state["alteration_cell_patches"]
    burden_axes = state["burden_axes"]
    annotation_axes = state["annotation_axes"]
    frequency_axes = state["frequency_axes"]
    consequence_legend = state["consequence_legend"]
    consequence_records = state["consequence_records"]
    consequence_panel_label_artists = state["consequence_panel_label_artists"]
    alteration_legend = state["alteration_legend"]

    sample_ids = data["sample_ids"]
    gene_labels = data["gene_labels"]
    driver_gene_labels = data["driver_gene_labels"]
    annotation_tracks = data["annotation_tracks"]
    gene_altered_fractions = data["gene_altered_fractions"]
    panel_title_lookup = data["panel_title_lookup"]
    effect_threshold = data["effect_threshold"]
    significance_threshold = data["significance_threshold"]
    x_limit_abs = data["x_limit_abs"]
    y_limit_top = data["y_limit_top"]

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
                bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
        ]
    )

    track_label_box_id_by_track_id: dict[str, str] = {}
    for item in track_label_artists:
        box_id = f"annotation_track_label_{item['track_id']}"
        track_label_box_id_by_track_id[str(item["track_id"])] = box_id
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["artist"].get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="annotation_track_label",
            )
        )

    sample_burdens_metrics: list[dict[str, Any]] = []
    for sample_id, bar in zip(sample_ids, burden_bars, strict=True):
        box_id = f"burden_bar_{sample_id}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        sample_burdens_metrics.append(
            {"sample_id": sample_id, "altered_gene_count": int(data["burden_counts"][sample_id]), "bar_box_id": box_id}
        )

    gene_frequency_metrics: list[dict[str, Any]] = []
    for gene_label, bar in zip(gene_labels, frequency_bars, strict=True):
        box_id = f"freq_bar_{gene_label}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=bar.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="bar",
            )
        )
        gene_frequency_metrics.append(
            {
                "gene_label": gene_label,
                "altered_fraction": float(gene_altered_fractions[gene_label]),
                "bar_box_id": box_id,
            }
        )

    annotation_tracks_metrics: list[dict[str, Any]] = []
    annotation_cells_by_track_id: dict[str, list[dict[str, Any]]] = {str(track["track_id"]): [] for track in annotation_tracks}
    for item in annotation_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="annotation_cell",
            )
        )
        annotation_cells_by_track_id[str(item["track_id"])].append(
            {
                "sample_id": str(item["sample_id"]),
                "category_label": str(item["category_label"]),
                "box_id": str(item["box_id"]),
            }
        )
    for track in annotation_tracks:
        track_id = str(track["track_id"])
        annotation_tracks_metrics.append(
            {
                "track_id": track_id,
                "track_label": str(track["track_label"]),
                "track_label_box_id": track_label_box_id_by_track_id[track_id],
                "cells": annotation_cells_by_track_id[track_id],
            }
        )

    overlay_box_id_by_alteration_id: dict[str, str] = {}
    for item in alteration_overlay_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_overlay",
            )
        )
        overlay_box_id_by_alteration_id[str(item["box_id"])] = str(item["box_id"])

    alteration_cells_metrics: list[dict[str, Any]] = []
    for item in alteration_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="alteration_cell",
            )
        )
        metric_item: dict[str, Any] = {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "box_id": str(item["box_id"]),
        }
        mutation_class = str(item["mutation_class"])
        cnv_state = str(item["cnv_state"])
        if mutation_class:
            metric_item["mutation_class"] = mutation_class
        if cnv_state:
            metric_item["cnv_state"] = cnv_state
        overlay_box_id = str(item["overlay_box_id"])
        if overlay_box_id:
            metric_item["overlay_box_id"] = overlay_box_id_by_alteration_id[overlay_box_id]
        alteration_cells_metrics.append(metric_item)

    panel_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=burden_axes.get_window_extent(renderer=renderer), box_id="panel_burden", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=annotation_axes.get_window_extent(renderer=renderer), box_id="panel_annotations", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=matrix_axes.get_window_extent(renderer=renderer), box_id="panel_matrix", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=frequency_axes.get_window_extent(renderer=renderer), box_id="panel_frequency", box_type="panel"),
    ]

    guide_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=alteration_legend.get_window_extent(renderer=renderer), box_id="legend_alteration", box_type="legend"),
        _bbox_to_layout_box(figure=fig, bbox=consequence_legend.get_window_extent(renderer=renderer), box_id="legend_consequence", box_type="legend"),
    ]

    threshold_half_width = max(x_limit_abs * 0.006, 0.015)
    threshold_half_height = max(y_limit_top * 0.008, 0.04)
    horizontal_threshold_inset = max(x_limit_abs * 0.015, 0.03)
    point_half_width = max(x_limit_abs * 0.03, 0.05)
    point_half_height = max(y_limit_top * 0.035, 0.08)

    def _clip_box_to_panel(box: dict[str, Any], *, panel_box: dict[str, Any]) -> dict[str, Any]:
        return {
            **box,
            "x0": max(float(box["x0"]), float(panel_box["x0"])),
            "y0": max(float(box["y0"]), float(panel_box["y0"])),
            "x1": min(float(box["x1"]), float(panel_box["x1"])),
            "y1": min(float(box["y1"]), float(panel_box["y1"])),
        }

    consequence_panels_metrics: list[dict[str, Any]] = []
    for index, (record, panel_label_artist) in enumerate(zip(consequence_records, consequence_panel_label_artists, strict=True), start=1):
        axes_item = record["axes"]
        panel_label_token = chr(ord("A") + index)
        panel_token = chr(ord("A") + index - 1)
        panel_box_id = f"panel_consequence_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)
        panel_title_box_id = f"consequence_title_{panel_token}"
        panel_label_box_id = f"panel_label_{panel_label_token}"
        x_axis_title_box_id = f"consequence_x_axis_title_{panel_token}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(figure=fig, bbox=axes_item.title.get_window_extent(renderer=renderer), box_id=panel_title_box_id, box_type="panel_title"),
                _bbox_to_layout_box(figure=fig, bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer), box_id=x_axis_title_box_id, box_type="subplot_x_axis_title"),
                _bbox_to_layout_box(figure=fig, bbox=panel_label_artist.get_window_extent(renderer=renderer), box_id=panel_label_box_id, box_type="panel_label"),
            ]
        )
        threshold_left_box_id = f"{record['panel_id']}_threshold_left"
        threshold_right_box_id = f"{record['panel_id']}_threshold_right"
        threshold_significance_box_id = f"{record['panel_id']}_significance_threshold"
        guide_boxes.extend(
            [
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=-effect_threshold - threshold_half_width,
                        y0=0.0,
                        x1=-effect_threshold + threshold_half_width,
                        y1=y_limit_top,
                        box_id=threshold_left_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=effect_threshold - threshold_half_width,
                        y0=0.0,
                        x1=effect_threshold + threshold_half_width,
                        y1=y_limit_top,
                        box_id=threshold_right_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
                _clip_box_to_panel(
                    _data_box_to_layout_box(
                        axes=axes_item,
                        figure=fig,
                        x0=-x_limit_abs + horizontal_threshold_inset,
                        y0=significance_threshold - threshold_half_height,
                        x1=x_limit_abs - horizontal_threshold_inset,
                        y1=significance_threshold + threshold_half_height,
                        box_id=threshold_significance_box_id,
                        box_type="reference_line",
                    ),
                    panel_box=panel_box,
                ),
            ]
        )

        label_box_lookup: dict[str, str] = {}
        for label_item in record["label_artists"]:
            label_box_id = str(label_item["box_id"])
            label_box_lookup[str(label_item["gene_label"])] = label_box_id
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_item["artist"].get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="annotation_label",
                )
            )

        normalized_points: list[dict[str, Any]] = []
        for point in record["points"]:
            gene_label = str(point["gene_label"])
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            point_box_id = str(point["point_box_id"])
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=effect_value - point_half_width,
                    y0=significance_value - point_half_height,
                    x1=effect_value + point_half_width,
                    y1=significance_value + point_half_height,
                    box_id=point_box_id,
                    box_type="scatter_point",
                )
            )
            point_x, point_y = _data_point_to_figure_xy(axes=axes_item, figure=fig, x=effect_value, y=significance_value)
            normalized_points.append(
                {
                    "gene_label": gene_label,
                    "x": point_x,
                    "y": point_y,
                    "effect_value": effect_value,
                    "significance_value": significance_value,
                    "regulation_class": str(point["regulation_class"]),
                    "point_box_id": point_box_id,
                    "label_box_id": label_box_lookup[gene_label],
                }
            )

        consequence_panels_metrics.append(
            {
                "panel_id": str(record["panel_id"]),
                "panel_title": panel_title_lookup[str(record["panel_id"])],
                "panel_label": panel_label_token,
                "panel_box_id": panel_box_id,
                "panel_label_box_id": panel_label_box_id,
                "panel_title_box_id": panel_title_box_id,
                "x_axis_title_box_id": x_axis_title_box_id,
                "effect_threshold_left_box_id": threshold_left_box_id,
                "effect_threshold_right_box_id": threshold_right_box_id,
                "significance_threshold_box_id": threshold_significance_box_id,
                "points": normalized_points,
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
                "alteration_legend_title": str(display_payload.get("alteration_legend_title") or "").strip(),
                "consequence_legend_title": str(display_payload.get("consequence_legend_title") or "").strip(),
                "effect_threshold": effect_threshold,
                "significance_threshold": significance_threshold,
                "sample_ids": sample_ids,
                "gene_labels": gene_labels,
                "driver_gene_labels": driver_gene_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "gene_alteration_frequencies": gene_frequency_metrics,
                "alteration_cells": alteration_cells_metrics,
                "consequence_panels": consequence_panels_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
