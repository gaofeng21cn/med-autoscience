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
    _wrap_figure_title_to_width,
    dump_json,
)

def _render_python_cnv_recurrence_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    region_order = list(display_payload.get("region_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    cnv_records = list(display_payload.get("cnv_records") or [])
    if not region_order or not sample_order or not annotation_tracks or not cnv_records:
        raise RuntimeError(
            f"{template_id} requires non-empty region_order, sample_order, annotation_tracks, and cnv_records"
        )

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    primary_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    secondary_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    neutral_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    contrast_color = str(palette.get("contrast") or "#d97706").strip() or "#d97706"
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#fef3c7").strip() or "#fef3c7"

    region_labels = [str(item["label"]) for item in region_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    region_index = {region_label: index for index, region_label in enumerate(region_labels)}

    cnv_lookup = {
        (str(item["sample_id"]), str(item["region_label"])): str(item["cnv_state"])
        for item in cnv_records
    }
    sample_burdens = {
        sample_id: sum(1 for region_label in region_labels if (sample_id, region_label) in cnv_lookup)
        for sample_id in sample_ids
    }
    gain_like_states = {"amplification", "gain"}
    loss_like_states = {"loss", "deep_loss"}
    region_gain_counts = {
        region_label: sum(
            1 for sample_id in sample_ids if cnv_lookup.get((sample_id, region_label)) in gain_like_states
        )
        for region_label in region_labels
    }
    region_loss_counts = {
        region_label: sum(
            1 for sample_id in sample_ids if cnv_lookup.get((sample_id, region_label)) in loss_like_states
        )
        for region_label in region_labels
    }
    region_gain_fractions = {
        region_label: region_gain_counts[region_label] / float(len(sample_ids))
        for region_label in region_labels
    }
    region_loss_fractions = {
        region_label: region_loss_counts[region_label] / float(len(sample_ids))
        for region_label in region_labels
    }

    cnv_color_map = {
        "amplification": secondary_color,
        "gain": contrast_color,
        "loss": primary_color,
        "deep_loss": neutral_color,
    }
    cnv_label_map = {
        "amplification": "Amplification",
        "gain": "Gain",
        "loss": "Loss",
        "deep_loss": "Deep loss",
    }
    track_palette_cycle = (
        primary_soft,
        secondary_soft,
        contrast_soft,
        "#eef2ff",
        "#f8fafc",
        "#ecfccb",
    )
    track_fill_by_id: dict[str, dict[str, str]] = {}
    for track in annotation_tracks:
        category_labels = [str(item["category_label"]) for item in track["values"]]
        ordered_categories = list(dict.fromkeys(category_labels))
        track_fill_by_id[str(track["track_id"])] = {
            category_label: track_palette_cycle[index % len(track_palette_cycle)]
            for index, category_label in enumerate(ordered_categories)
        }

    figure_width = max(8.4, 0.52 * len(sample_ids) + 4.6)
    figure_height = max(5.8, 0.58 * len(region_labels) + 0.42 * len(annotation_tracks) + 2.9)
    fig = plt.figure(figsize=(figure_width, figure_height))
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.90,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color=neutral_color,
            y=0.985,
        )

    top_margin = 0.86 if show_figure_title else 0.90
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        2,
        left=0.20,
        right=0.93,
        bottom=0.22,
        top=top_margin,
        width_ratios=(max(3.8, 0.60 * len(sample_ids) + 0.8), 1.70),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.66 * len(region_labels))),
        hspace=0.10,
        wspace=0.14,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)

    burden_positions = list(range(len(sample_ids)))
    burden_values = [sample_burdens[sample_id] for sample_id in sample_ids]
    burden_bars = burden_axes.bar(
        burden_positions,
        burden_values,
        width=0.74,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    burden_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    burden_axes.set_xticks([])
    burden_axes.set_ylabel(
        str(display_payload.get("burden_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    burden_axes.tick_params(axis="x", bottom=False, labelbottom=False)
    burden_axes.tick_params(axis="y", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    burden_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(burden_axes)
    burden_axes.spines["bottom"].set_visible(False)

    annotation_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    annotation_axes.set_ylim(-0.5, len(annotation_tracks) - 0.5)
    annotation_axes.invert_yaxis()
    annotation_axes.set_xticks([])
    annotation_axes.set_yticks([])
    annotation_axes.tick_params(axis="x", bottom=False, labelbottom=False, length=0)
    annotation_axes.tick_params(axis="y", left=False, labelleft=False, length=0)
    annotation_axes.set_facecolor("white")
    for spine in annotation_axes.spines.values():
        spine.set_color("#e2e8f0")
        spine.set_linewidth(0.8)

    matrix_axes.set_xlim(-0.5, len(sample_ids) - 0.5)
    matrix_axes.set_ylim(-0.5, len(region_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(sample_ids, rotation=45, ha="right", fontsize=max(tick_size - 0.3, 8.6), color=neutral_color)
    matrix_axes.set_yticks(range(len(region_labels)))
    matrix_axes.set_yticklabels(region_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(
        max(region_gain_fractions.values(), default=0.0),
        max(region_loss_fractions.values(), default=0.0),
        1e-6,
    )
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(region_labels)))
    gain_values = [region_gain_fractions[region_label] for region_label in region_labels]
    loss_values = [-region_loss_fractions[region_label] for region_label in region_labels]
    gain_bars = frequency_axes.barh(
        frequency_positions,
        gain_values,
        height=0.32,
        color=secondary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    loss_bars = frequency_axes.barh(
        frequency_positions,
        loss_values,
        height=0.32,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.axvline(0.0, color=neutral_color, linewidth=0.9, alpha=0.9, zorder=2)
    frequency_axes.set_xlim(-frequency_limit, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(region_labels)))
    frequency_axes.tick_params(axis="y", left=False, labelleft=False)
    frequency_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.6), colors=neutral_color)
    frequency_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    _apply_publication_axes_style(frequency_axes)
    frequency_axes.spines["left"].set_visible(False)

    annotation_cell_patches: list[dict[str, Any]] = []
    for track_index, track in enumerate(annotation_tracks):
        track_id = str(track["track_id"])
        fill_lookup = track_fill_by_id[track_id]
        for value in track["values"]:
            sample_id = str(value["sample_id"])
            category_label = str(value["category_label"])
            sample_position = sample_index[sample_id]
            patch = matplotlib.patches.Rectangle(
                (sample_position - 0.5, track_index - 0.5),
                1.0,
                1.0,
                facecolor=fill_lookup[category_label],
                edgecolor="white",
                linewidth=1.0,
                zorder=3,
            )
            annotation_axes.add_patch(patch)
            annotation_cell_patches.append(
                {
                    "box_id": f"annotation_{track_id}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "category_label": category_label,
                    "track_id": track_id,
                }
            )
    annotation_axes.set_axisbelow(True)

    cnv_cell_patches: list[dict[str, Any]] = []
    for region_label in region_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = region_index[region_label]
            background_patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor="#ffffff",
                edgecolor="#d7e0ea",
                linewidth=0.9,
                zorder=1,
            )
            matrix_axes.add_patch(background_patch)
            cnv_state = cnv_lookup.get((sample_id, region_label))
            if not cnv_state:
                continue
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=cnv_color_map[cnv_state],
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            cnv_cell_patches.append(
                {
                    "box_id": f"cnv_{region_label}_{sample_id}",
                    "patch": patch,
                    "sample_id": sample_id,
                    "region_label": region_label,
                    "cnv_state": cnv_state,
                }
            )

    legend_handles = [
        matplotlib.patches.Patch(facecolor=cnv_color_map[key], edgecolor="white", label=cnv_label_map[key])
        for key in ("amplification", "gain", "loss", "deep_loss")
    ]
    legend = fig.legend(
        handles=legend_handles,
        labels=[handle.get_label() for handle in legend_handles],
        title=str(display_payload.get("cnv_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.53, 0.02),
        ncol=min(4, len(legend_handles)),
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.3, 8.8),
        columnspacing=1.4,
    )

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, burden_y0 = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    burden_x1, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
    panel_label_a = fig.text(
        burden_x0 + 0.007,
        burden_y1 - 0.010,
        "A",
        transform=fig.transFigure,
        fontsize=max(panel_label_size + 1.2, 13.0),
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    track_label_artists: list[dict[str, Any]] = []
    annotation_axes_bbox = annotation_axes.get_window_extent(renderer=renderer)
    annotation_x0, annotation_y0 = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
    label_anchor_x = max(0.06, annotation_x0 - 0.014)
    for track_index, track in enumerate(annotation_tracks):
        _, track_y = _data_point_to_figure_xy(
            axes=annotation_axes,
            figure=fig,
            x=0.0,
            y=float(track_index),
        )
        artist = fig.text(
            label_anchor_x,
            track_y,
            str(track["track_label"]),
            fontsize=max(tick_size - 0.2, 8.6),
            fontweight="bold",
            color=neutral_color,
            ha="right",
            va="center",
        )
        track_label_artists.append({"track_id": str(track["track_id"]), "artist": artist})

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
    y_axis_title_box = _bbox_to_layout_box(
        figure=fig,
        bbox=matrix_axes.yaxis.label.get_window_extent(renderer=renderer),
        box_id="y_axis_title",
        box_type="subplot_y_axis_title",
    )
    layout_boxes.extend(
        [
            y_axis_title_box,
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
            {
                "sample_id": sample_id,
                "altered_region_count": int(sample_burdens[sample_id]),
                "bar_box_id": box_id,
            }
        )

    region_frequency_metrics: list[dict[str, Any]] = []
    for region_label, gain_bar, loss_bar in zip(region_labels, gain_bars, loss_bars, strict=True):
        gain_box_id = f"freq_gain_{region_label}"
        loss_box_id = f"freq_loss_{region_label}"
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=gain_bar.get_window_extent(renderer=renderer),
                    box_id=gain_box_id,
                    box_type="bar",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=loss_bar.get_window_extent(renderer=renderer),
                    box_id=loss_box_id,
                    box_type="bar",
                ),
            ]
        )
        region_frequency_metrics.append(
            {
                "region_label": region_label,
                "gain_fraction": float(region_gain_fractions[region_label]),
                "loss_fraction": float(region_loss_fractions[region_label]),
                "gain_bar_box_id": gain_box_id,
                "loss_bar_box_id": loss_box_id,
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

    cnv_cells_metrics: list[dict[str, Any]] = []
    for item in cnv_cell_patches:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=item["patch"].get_window_extent(renderer=renderer),
                box_id=str(item["box_id"]),
                box_type="cnv_cell",
            )
        )
        cnv_cells_metrics.append(
            {
                "sample_id": str(item["sample_id"]),
                "region_label": str(item["region_label"]),
                "cnv_state": str(item["cnv_state"]),
                "box_id": str(item["box_id"]),
            }
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=burden_axes.get_window_extent(renderer=renderer),
            box_id="panel_burden",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=annotation_axes.get_window_extent(renderer=renderer),
            box_id="panel_annotations",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="panel_matrix",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=frequency_axes.get_window_extent(renderer=renderer),
            box_id="panel_frequency",
            box_type="panel",
        ),
    ]

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
                "cnv_legend_title": str(display_payload.get("cnv_legend_title") or "").strip(),
                "sample_ids": sample_ids,
                "region_labels": region_labels,
                "annotation_tracks": annotation_tracks_metrics,
                "sample_burdens": sample_burdens_metrics,
                "region_gain_loss_frequencies": region_frequency_metrics,
                "cnv_cells": cnv_cells_metrics,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

