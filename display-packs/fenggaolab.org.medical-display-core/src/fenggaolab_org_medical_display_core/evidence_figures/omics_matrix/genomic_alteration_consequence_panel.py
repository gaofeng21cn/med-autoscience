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
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    dump_json,
)

def _render_python_genomic_alteration_consequence_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    gene_order = list(display_payload.get("gene_order") or [])
    sample_order = list(display_payload.get("sample_order") or [])
    annotation_tracks = list(display_payload.get("annotation_tracks") or [])
    alteration_records = list(display_payload.get("alteration_records") or [])
    driver_gene_order = list(display_payload.get("driver_gene_order") or [])
    consequence_panel_order = list(display_payload.get("consequence_panel_order") or [])
    consequence_points = list(display_payload.get("consequence_points") or [])
    if (
        not gene_order
        or not sample_order
        or not annotation_tracks
        or not alteration_records
        or not driver_gene_order
        or not consequence_panel_order
        or not consequence_points
    ):
        raise RuntimeError(
            f"{template_id} requires non-empty gene_order, sample_order, annotation_tracks, alteration_records, "
            "driver_gene_order, consequence_panel_order, and consequence_points"
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
    light_fill = str(palette.get("light") or "#eff6ff").strip() or "#eff6ff"
    primary_soft = str(palette.get("primary_soft") or "#eaf2f5").strip() or "#eaf2f5"
    secondary_soft = str(palette.get("secondary_soft") or "#f4eee5").strip() or "#f4eee5"
    contrast_soft = str(palette.get("contrast_soft") or "#f7ebeb").strip() or "#f7ebeb"
    background_color = str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1"

    gene_labels = [str(item["label"]) for item in gene_order]
    driver_gene_labels = [str(item["label"]) for item in driver_gene_order]
    sample_ids = [str(item["sample_id"]) for item in sample_order]
    sample_index = {sample_id: index for index, sample_id in enumerate(sample_ids)}
    gene_index = {gene_label: index for index, gene_label in enumerate(gene_labels)}

    alteration_lookup = {
        (str(item["sample_id"]), str(item["gene_label"])): {
            "sample_id": str(item["sample_id"]),
            "gene_label": str(item["gene_label"]),
            "mutation_class": str(item.get("mutation_class") or "").strip(),
            "cnv_state": str(item.get("cnv_state") or "").strip(),
        }
        for item in alteration_records
    }
    burden_counts = {
        sample_id: sum(1 for gene_label in gene_labels if (sample_id, gene_label) in alteration_lookup)
        for sample_id in sample_ids
    }
    gene_altered_counts = {
        gene_label: sum(1 for sample_id in sample_ids if (sample_id, gene_label) in alteration_lookup)
        for gene_label in gene_labels
    }
    gene_altered_fractions = {
        gene_label: gene_altered_counts[gene_label] / float(len(sample_ids))
        for gene_label in gene_labels
    }

    mutation_color_map = {
        "missense": primary_color,
        "truncating": "#8b3a3a",
        "fusion": "#475569",
    }
    cnv_color_map = {
        "amplification": secondary_color,
        "gain": "#d97706",
        "loss": "#0f766e",
        "deep_loss": "#111827",
    }
    alteration_label_map = {
        "missense": "Missense",
        "truncating": "Truncating",
        "fusion": "Fusion",
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

    panel_id_order = [str(item["panel_id"]) for item in consequence_panel_order]
    panel_title_lookup = {str(item["panel_id"]): str(item["panel_title"]) for item in consequence_panel_order}
    point_lookup: dict[str, list[dict[str, Any]]] = {panel_id: [] for panel_id in panel_id_order}
    for point in consequence_points:
        point_lookup[str(point["panel_id"])].append(point)

    effect_threshold = float(display_payload.get("effect_threshold") or 0.0)
    significance_threshold = float(display_payload.get("significance_threshold") or 0.0)
    all_effect_values = [float(item["effect_value"]) for item in consequence_points]
    all_significance_values = [float(item["significance_value"]) for item in consequence_points]
    x_limit_core = max(max(abs(value) for value in all_effect_values), effect_threshold, 1e-6)
    x_padding = max(x_limit_core * 0.18, 0.20)
    x_limit_abs = x_limit_core + x_padding
    y_limit_top = max(max(all_significance_values), significance_threshold) * 1.12 + 0.25
    y_limit_top = max(y_limit_top, significance_threshold + 0.50)

    figure_width = max(12.6, 0.52 * len(sample_ids) + 7.6)
    figure_height = max(6.4, 0.60 * len(gene_labels) + 3.2, 2.4 + 1.75 * len(panel_id_order))
    fig = plt.figure(figsize=(figure_width, figure_height))
    fig.patch.set_facecolor("white")

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.92,
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
    top_margin = max(0.74, top_margin - 0.04 * max(title_line_count - 1, 0))
    grid = fig.add_gridspec(
        3,
        3,
        left=0.17,
        right=0.96,
        bottom=0.22,
        top=top_margin,
        width_ratios=(
            max(3.8, 0.60 * len(sample_ids) + 0.8),
            1.45,
            max(2.5, 1.9 + 0.30 * len(driver_gene_labels)),
        ),
        height_ratios=(1.15, max(0.85, 0.52 * len(annotation_tracks)), max(2.8, 0.70 * len(gene_labels))),
        hspace=0.10,
        wspace=0.16,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)
    consequence_grid = grid[:, 2].subgridspec(len(panel_id_order), 1, hspace=0.28)
    consequence_axes_list = [fig.add_subplot(consequence_grid[index, 0]) for index in range(len(panel_id_order))]

    burden_positions = list(range(len(sample_ids)))
    burden_values = [burden_counts[sample_id] for sample_id in sample_ids]
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
    matrix_axes.set_ylim(-0.5, len(gene_labels) - 0.5)
    matrix_axes.invert_yaxis()
    matrix_axes.set_xticks(range(len(sample_ids)))
    matrix_axes.set_xticklabels(
        sample_ids,
        rotation=45,
        ha="right",
        fontsize=max(tick_size - 0.3, 8.6),
        color=neutral_color,
    )
    matrix_axes.set_yticks(range(len(gene_labels)))
    matrix_axes.set_yticklabels(gene_labels, fontsize=max(tick_size - 0.2, 8.8), color=neutral_color)
    matrix_axes.tick_params(axis="x", length=0, colors=neutral_color)
    matrix_axes.tick_params(axis="y", length=0, colors=neutral_color)
    matrix_axes.set_ylabel(
        str(display_payload.get("y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_color,
    )
    _apply_publication_axes_style(matrix_axes)

    max_frequency = max(max(gene_altered_fractions.values()), 1e-6)
    frequency_limit = max(0.35, min(1.0, max_frequency * 1.20 + 0.05))
    frequency_positions = list(range(len(gene_labels)))
    frequency_values = [gene_altered_fractions[gene_label] for gene_label in gene_labels]
    frequency_bars = frequency_axes.barh(
        frequency_positions,
        frequency_values,
        height=0.74,
        color=primary_color,
        alpha=0.92,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )
    frequency_axes.set_xlim(0.0, frequency_limit)
    frequency_axes.set_xlabel(
        str(display_payload.get("frequency_axis_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.8),
        fontweight="bold",
        color=neutral_color,
    )
    frequency_axes.set_yticks(range(len(gene_labels)))
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

    alteration_cell_patches: list[dict[str, Any]] = []
    alteration_overlay_patches: list[dict[str, Any]] = []
    for gene_label in gene_labels:
        for sample_id in sample_ids:
            x_index = sample_index[sample_id]
            y_index = gene_index[gene_label]
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
            alteration = alteration_lookup.get((sample_id, gene_label))
            if alteration is None:
                continue
            mutation_class = str(alteration.get("mutation_class") or "").strip()
            cnv_state = str(alteration.get("cnv_state") or "").strip()
            cell_color = cnv_color_map[cnv_state] if cnv_state else mutation_color_map[mutation_class]
            patch = matplotlib.patches.Rectangle(
                (x_index - 0.5, y_index - 0.5),
                1.0,
                1.0,
                facecolor=cell_color,
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            matrix_axes.add_patch(patch)
            box_id = f"alteration_{gene_label}_{sample_id}"
            overlay_box_id = ""
            if mutation_class and cnv_state:
                overlay_patch = matplotlib.patches.Rectangle(
                    (x_index - 0.21, y_index - 0.32),
                    0.42,
                    0.64,
                    facecolor=mutation_color_map[mutation_class],
                    edgecolor="white",
                    linewidth=0.8,
                    zorder=4,
                )
                matrix_axes.add_patch(overlay_patch)
                overlay_box_id = f"overlay_{gene_label}_{sample_id}"
                alteration_overlay_patches.append({"box_id": overlay_box_id, "patch": overlay_patch})
            alteration_cell_patches.append(
                {
                    "box_id": box_id,
                    "patch": patch,
                    "sample_id": sample_id,
                    "gene_label": gene_label,
                    "mutation_class": mutation_class,
                    "cnv_state": cnv_state,
                    "overlay_box_id": overlay_box_id,
                }
            )

    consequence_records: list[dict[str, Any]] = []
    for axes_item, panel_id in zip(consequence_axes_list, panel_id_order, strict=True):
        panel_points = list(point_lookup.get(panel_id) or [])
        scatter_colors = {
            "upregulated": secondary_color,
            "downregulated": primary_color,
            "background": background_color,
        }
        axes_item.scatter(
            [float(item["effect_value"]) for item in panel_points],
            [float(item["significance_value"]) for item in panel_points],
            s=74.0,
            c=[scatter_colors[str(item["regulation_class"])] for item in panel_points],
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        axes_item.axvline(-effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axvline(effect_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.axhline(significance_threshold, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(-x_limit_abs, x_limit_abs)
        axes_item.set_ylim(0.0, y_limit_top)
        axes_item.set_xlabel(
            str(display_payload.get("consequence_x_label") or "").strip(),
            fontsize=max(axis_title_size - 0.1, 10.0),
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_ylabel("")
        axes_item.set_title(
            panel_title_lookup[panel_id],
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=10.0,
        )
        axes_item.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
        axes_item.tick_params(axis="y", labelsize=tick_size, colors=neutral_color)
        axes_item.grid(axis="both", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        _apply_publication_axes_style(axes_item)

        point_artists: list[dict[str, Any]] = []
        label_artists: list[dict[str, Any]] = []
        for point in panel_points:
            effect_value = float(point["effect_value"])
            significance_value = float(point["significance_value"])
            gene_label = str(point["gene_label"])
            point_box_id = f"consequence_point_{panel_id}_{gene_label}"
            point_artists.append(
                {
                    "point_box_id": point_box_id,
                    "gene_label": gene_label,
                    "effect_value": effect_value,
                    "significance_value": significance_value,
                    "regulation_class": str(point["regulation_class"]),
                }
            )
            offset_x = -8 if effect_value >= 0.0 else 8
            ha = "right" if effect_value >= 0.0 else "left"
            label_artist = axes_item.annotate(
                gene_label,
                xy=(effect_value, significance_value),
                xytext=(offset_x, 6),
                textcoords="offset points",
                fontsize=max(tick_size - 0.6, 8.2),
                color=neutral_color,
                ha=ha,
                va="bottom",
                zorder=4,
                annotation_clip=True,
            )
            label_artists.append(
                {
                    "gene_label": gene_label,
                    "box_id": f"consequence_label_{panel_id}_{gene_label}",
                    "artist": label_artist,
                }
            )

        consequence_records.append(
            {
                "panel_id": panel_id,
                "axes": axes_item,
                "points": point_artists,
                "label_artists": label_artists,
            }
        )

    alteration_legend_handles = [
        matplotlib.patches.Patch(facecolor=mutation_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("missense", "truncating", "fusion")
    ] + [
        matplotlib.patches.Patch(facecolor=cnv_color_map[key], edgecolor="white", label=alteration_label_map[key])
        for key in ("amplification", "gain", "loss", "deep_loss")
    ]
    alteration_legend = fig.legend(
        handles=alteration_legend_handles,
        labels=[handle.get_label() for handle in alteration_legend_handles],
        title=str(display_payload.get("alteration_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.33, 0.02),
        ncol=4,
        frameon=False,
        fontsize=max(tick_size - 1.0, 8.0),
        title_fontsize=max(tick_size - 0.4, 8.6),
        columnspacing=1.2,
    )
    consequence_legend_handles = [
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=secondary_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Upregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=primary_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Downregulated",
        ),
        matplotlib.lines.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=background_color,
            markeredgecolor="white",
            markeredgewidth=0.8,
            markersize=8.0,
            label="Background",
        ),
    ]
    consequence_legend = fig.legend(
        consequence_legend_handles,
        [str(handle.get_label()) for handle in consequence_legend_handles],
        title=str(display_payload.get("consequence_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.80, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.9, 8.0),
        title_fontsize=max(tick_size - 0.4, 8.6),
        columnspacing=1.1,
    )
    fig.add_artist(alteration_legend)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    burden_panel_bbox = burden_axes.get_window_extent(renderer=renderer)
    burden_x0, _ = fig.transFigure.inverted().transform((burden_panel_bbox.x0, burden_panel_bbox.y0))
    _, burden_y1 = fig.transFigure.inverted().transform((burden_panel_bbox.x1, burden_panel_bbox.y1))
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
    annotation_x0, _ = fig.transFigure.inverted().transform((annotation_axes_bbox.x0, annotation_axes_bbox.y0))
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

    consequence_panel_label_artists: list[Any] = []
    for index, record in enumerate(consequence_records, start=1):
        axes_item = record["axes"]
        panel_token = chr(ord("B") + index - 1)
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.060, 0.020), 0.032)
        consequence_panel_label_artists.append(
            fig.text(
                panel_x0 + x_padding,
                panel_y1 - y_padding,
                panel_token,
                transform=fig.transFigure,
                fontsize=max(panel_label_size + 1.4, 13.0),
                fontweight="bold",
                color=neutral_color,
                ha="left",
                va="top",
            )
        )

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
            {
                "sample_id": sample_id,
                "altered_gene_count": int(burden_counts[sample_id]),
                "bar_box_id": box_id,
            }
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
        metric_item = {
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

    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=alteration_legend.get_window_extent(renderer=renderer),
            box_id="legend_alteration",
            box_type="legend",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=consequence_legend.get_window_extent(renderer=renderer),
            box_id="legend_consequence",
            box_type="legend",
        ),
    ]

    consequence_panels_metrics: list[dict[str, Any]] = []
    threshold_half_width = max(x_limit_abs * 0.006, 0.015)
    threshold_half_height = max(y_limit_top * 0.008, 0.04)
    horizontal_threshold_inset = max(x_limit_abs * 0.015, 0.03)
    point_half_width = max(x_limit_abs * 0.03, 0.05)
    point_half_height = max(y_limit_top * 0.035, 0.08)

    def _clip_box_to_panel(
        box: dict[str, Any],
        *,
        panel_box: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            **box,
            "x0": max(float(box["x0"]), float(panel_box["x0"])),
            "y0": max(float(box["y0"]), float(panel_box["y0"])),
            "x1": min(float(box["x1"]), float(panel_box["x1"])),
            "y1": min(float(box["y1"]), float(panel_box["y1"])),
        }

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
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
                    box_id=panel_title_box_id,
                    box_type="panel_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=axes_item.xaxis.label.get_window_extent(renderer=renderer),
                    box_id=x_axis_title_box_id,
                    box_type="subplot_x_axis_title",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=panel_label_artist.get_window_extent(renderer=renderer),
                    box_id=panel_label_box_id,
                    box_type="panel_label",
                ),
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
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=effect_value,
                y=significance_value,
            )
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

