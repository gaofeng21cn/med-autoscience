from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ....shared import (
    _apply_publication_axes_style,
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _wrap_figure_title_to_width,
)
from ._layout import _write_layout_and_outputs
from ._prepare import _prepare_render_state


def _render_python_genomic_alteration_pathway_integrated_composite_panel(
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

    state = _prepare_render_state(template_id=template_id, display_payload=display_payload)

    title_size = float(state["title_size"])
    axis_title_size = float(state["axis_title_size"])
    tick_size = float(state["tick_size"])
    panel_label_size = float(state["panel_label_size"])
    show_figure_title = bool(state["show_figure_title"])
    primary_color = str(state["primary_color"])
    secondary_color = str(state["secondary_color"])
    neutral_color = str(state["neutral_color"])
    light_fill = str(state["light_fill"])
    background_color = str(state["background_color"])
    gene_labels = list(state["gene_labels"])
    driver_gene_labels = list(state["driver_gene_labels"])
    sample_ids = list(state["sample_ids"])
    pathway_labels = list(state["pathway_labels"])
    sample_index = dict(state["sample_index"])
    gene_index = dict(state["gene_index"])
    pathway_index = dict(state["pathway_index"])
    alteration_lookup = dict(state["alteration_lookup"])
    burden_counts = dict(state["burden_counts"])
    gene_altered_fractions = dict(state["gene_altered_fractions"])
    mutation_color_map = dict(state["mutation_color_map"])
    cnv_color_map = dict(state["cnv_color_map"])
    alteration_label_map = dict(state["alteration_label_map"])
    track_fill_by_id = dict(state["track_fill_by_id"])
    annotation_tracks = list(state["annotation_tracks"])
    consequence_panel_ids = list(state["consequence_panel_ids"])
    consequence_title_lookup = dict(state["consequence_title_lookup"])
    consequence_point_lookup = dict(state["consequence_point_lookup"])
    pathway_panel_ids = list(state["pathway_panel_ids"])
    pathway_title_lookup = dict(state["pathway_title_lookup"])
    pathway_point_lookup = dict(state["pathway_point_lookup"])
    effect_threshold = float(state["effect_threshold"])
    significance_threshold = float(state["significance_threshold"])
    x_limit_abs = float(state["x_limit_abs"])
    y_limit_top = float(state["y_limit_top"])
    pathway_x_min = float(state["pathway_x_min"])
    pathway_x_max = float(state["pathway_x_max"])
    pathway_x_padding = float(state["pathway_x_padding"])
    pathway_size_min = float(state["pathway_size_min"])
    pathway_size_max = float(state["pathway_size_max"])
    pathway_color_norm = state["pathway_color_norm"]
    pathway_effect_cmap = state["pathway_effect_cmap"]
    pathway_marker_size = state["pathway_marker_size"]

    figure_width = max(13.4, 0.52 * len(sample_ids) + 8.8)
    figure_height = max(9.2, 0.62 * len(gene_labels) + 5.1)
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
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
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
            max(2.7, 2.0 + 0.32 * len(driver_gene_labels)),
        ),
        height_ratios=(1.10, max(0.90, 0.52 * len(annotation_tracks)), max(3.0, 0.72 * len(gene_labels))),
        hspace=0.10,
        wspace=0.16,
    )
    burden_axes = fig.add_subplot(grid[0, 0])
    annotation_axes = fig.add_subplot(grid[1, 0], sharex=burden_axes)
    matrix_axes = fig.add_subplot(grid[2, 0], sharex=burden_axes)
    frequency_axes = fig.add_subplot(grid[2, 1], sharey=matrix_axes)
    right_grid = grid[:, 2].subgridspec(2, 1, hspace=0.16, height_ratios=(1.75, 1.15))
    consequence_grid = right_grid[0].subgridspec(len(consequence_panel_ids), 1, hspace=0.26)
    pathway_grid = right_grid[1].subgridspec(len(pathway_panel_ids), 1, hspace=0.20)
    consequence_axes_list = [fig.add_subplot(consequence_grid[index, 0]) for index in range(len(consequence_panel_ids))]
    pathway_axes_list = [fig.add_subplot(pathway_grid[index, 0]) for index in range(len(pathway_panel_ids))]

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
    for axes_item, panel_id in zip(consequence_axes_list, consequence_panel_ids, strict=True):
        panel_points = list(consequence_point_lookup.get(panel_id) or [])
        scatter_color_lookup = {
            "upregulated": secondary_color,
            "downregulated": primary_color,
            "background": background_color,
        }
        axes_item.scatter(
            [float(item["effect_value"]) for item in panel_points],
            [float(item["significance_value"]) for item in panel_points],
            s=72.0,
            c=[scatter_color_lookup[str(item["regulation_class"])] for item in panel_points],
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
            consequence_title_lookup[panel_id],
            fontsize=axis_title_size,
            fontweight="bold",
            color=neutral_color,
            pad=9.0,
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
            place_label_below = significance_value >= y_limit_top * 0.82
            label_artist = axes_item.annotate(
                gene_label,
                xy=(effect_value, significance_value),
                xytext=(offset_x, -6 if place_label_below else 6),
                textcoords="offset points",
                fontsize=max(tick_size - 0.6, 8.2),
                color=neutral_color,
                ha=ha,
                va="top" if place_label_below else "bottom",
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

    scatter_artist = None
    pathway_records: list[dict[str, Any]] = []
    y_positions = list(range(len(pathway_labels)))
    for axes_item, panel_id in zip(pathway_axes_list, pathway_panel_ids, strict=True):
        panel_points = list(pathway_point_lookup.get(panel_id) or [])
        scatter_artist = axes_item.scatter(
            [float(item["x_value"]) for item in panel_points],
            [pathway_index[str(item["pathway_label"])] for item in panel_points],
            s=[pathway_marker_size(float(item["size_value"])) for item in panel_points],
            c=[float(item["effect_value"]) for item in panel_points],
            cmap=pathway_effect_cmap,
            norm=pathway_color_norm,
            alpha=0.92,
            edgecolors="white",
            linewidths=0.9,
            zorder=3,
        )
        if pathway_x_min < 0.0 < pathway_x_max:
            axes_item.axvline(0.0, color=neutral_color, linewidth=0.9, linestyle="--", zorder=1)
        axes_item.set_xlim(pathway_x_min - pathway_x_padding, pathway_x_max + pathway_x_padding)
        axes_item.set_ylim(-0.5, len(pathway_labels) - 0.5)
        axes_item.set_yticks(y_positions)
        axes_item.set_yticklabels(pathway_labels, fontsize=max(tick_size - 0.2, 8.2), color=neutral_color)
        axes_item.invert_yaxis()
        axes_item.set_xlabel(
            str(display_payload.get("pathway_x_label") or "").strip(),
            fontsize=max(axis_title_size - 0.2, 9.8),
            fontweight="bold",
            color=neutral_color,
        )
        axes_item.set_ylabel("")
        axes_item.set_title(
            pathway_title_lookup[panel_id],
            fontsize=max(axis_title_size - 0.1, 10.0),
            fontweight="bold",
            color=neutral_color,
            pad=8.0,
        )
        axes_item.tick_params(axis="x", labelsize=max(tick_size - 0.2, 8.2), colors=neutral_color)
        axes_item.tick_params(axis="y", length=0, colors=neutral_color)
        axes_item.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
        axes_item.grid(axis="y", visible=False)
        _apply_publication_axes_style(axes_item)
        pathway_records.append({"panel_id": panel_id, "axes": axes_item, "points": panel_points})

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
        bbox_to_anchor=(0.32, 0.03),
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
        bbox_to_anchor=(0.72, 0.03),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.9, 8.0),
        title_fontsize=max(tick_size - 0.4, 8.6),
        columnspacing=1.1,
    )
    pathway_legend_values = sorted(
        {
            round(pathway_size_min, 2),
            round((pathway_size_min + pathway_size_max) / 2.0, 2),
            round(pathway_size_max, 2),
        }
    )
    pathway_legend_handles = [
        plt.scatter([], [], s=pathway_marker_size(float(value)), color="#94a3b8", edgecolors="white", linewidths=0.8)
        for value in pathway_legend_values
    ]
    pathway_legend = fig.legend(
        pathway_legend_handles,
        [f"{value:g}" for value in pathway_legend_values],
        title=str(display_payload.get("pathway_size_scale_label") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.90, 0.03),
        ncol=len(pathway_legend_handles),
        frameon=False,
        fontsize=max(tick_size - 1.0, 7.8),
        title_fontsize=max(tick_size - 0.5, 8.4),
        columnspacing=0.9,
    )
    fig.add_artist(alteration_legend)
    fig.add_artist(consequence_legend)
    if scatter_artist is None:
        raise RuntimeError(f"{template_id} failed to render pathway scatter artist")
    colorbar = fig.colorbar(scatter_artist, ax=pathway_axes_list, fraction=0.050, pad=0.03)
    colorbar.set_label(
        str(display_payload.get("pathway_effect_scale_label") or "").strip(),
        fontsize=max(axis_title_size - 0.4, 9.6),
        color=neutral_color,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.6, 8.4), colors=neutral_color)

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

    pathway_y_axis_title_artist = fig.text(
        0.64,
        0.31,
        str(display_payload.get("pathway_y_label") or "").strip(),
        rotation=90,
        fontsize=max(axis_title_size - 0.2, 9.6),
        fontweight="bold",
        color=neutral_color,
        ha="center",
        va="center",
    )

    def _make_panel_label_artist(axes_item: Any, label_token: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.055, 0.016), 0.030)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label_token,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.4, 13.0),
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    consequence_panel_label_artists = [
        _make_panel_label_artist(axes_item, chr(ord("B") + index))
        for index, axes_item in enumerate(consequence_axes_list)
    ]
    pathway_panel_label_artists = [
        _make_panel_label_artist(axes_item, chr(ord("E") + index))
        for index, axes_item in enumerate(pathway_axes_list)
    ]

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    _write_layout_and_outputs(
        template_id=template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
        context={
            "fig": fig,
            "renderer": renderer,
            "title_artist": title_artist,
            "matrix_axes": matrix_axes,
            "pathway_y_axis_title_artist": pathway_y_axis_title_artist,
            "panel_label_a": panel_label_a,
            "track_label_artists": track_label_artists,
            "sample_ids": sample_ids,
            "burden_bars": burden_bars,
            "burden_counts": burden_counts,
            "gene_labels": gene_labels,
            "frequency_bars": frequency_bars,
            "gene_altered_fractions": gene_altered_fractions,
            "annotation_tracks": annotation_tracks,
            "annotation_cell_patches": annotation_cell_patches,
            "alteration_overlay_patches": alteration_overlay_patches,
            "alteration_cell_patches": alteration_cell_patches,
            "burden_axes": burden_axes,
            "annotation_axes": annotation_axes,
            "frequency_axes": frequency_axes,
            "alteration_legend": alteration_legend,
            "consequence_legend": consequence_legend,
            "pathway_legend": pathway_legend,
            "colorbar": colorbar,
            "x_limit_abs": x_limit_abs,
            "y_limit_top": y_limit_top,
            "pathway_x_max": pathway_x_max,
            "pathway_x_min": pathway_x_min,
            "pathway_x_padding": pathway_x_padding,
            "pathway_labels": pathway_labels,
            "effect_threshold": effect_threshold,
            "significance_threshold": significance_threshold,
            "consequence_records": consequence_records,
            "consequence_panel_label_artists": consequence_panel_label_artists,
            "consequence_title_lookup": consequence_title_lookup,
            "pathway_records": pathway_records,
            "pathway_panel_label_artists": pathway_panel_label_artists,
            "pathway_title_lookup": pathway_title_lookup,
            "pathway_index": pathway_index,
            "driver_gene_labels": driver_gene_labels,
        },
    )
