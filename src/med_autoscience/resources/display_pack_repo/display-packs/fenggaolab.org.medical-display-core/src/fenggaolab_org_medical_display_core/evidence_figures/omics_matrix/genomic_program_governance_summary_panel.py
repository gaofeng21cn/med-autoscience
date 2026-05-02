from __future__ import annotations

import math
from pathlib import Path
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
    _wrap_flow_text_to_width,
    dump_json,
)

def _render_python_genomic_program_governance_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    programs = list(display_payload.get("programs") or [])
    layer_order = list(display_payload.get("layer_order") or [])
    if not programs or not layer_order:
        raise RuntimeError(f"{template_id} requires non-empty programs and layer_order")

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
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    light_fill = str(palette.get("light") or "#f8fafc").strip() or "#f8fafc"
    primary_soft = str(palette.get("primary_soft") or "#eff6ff").strip() or "#eff6ff"
    summary_fill = str(palette.get("secondary_soft") or "#e2e8f0").strip() or "#e2e8f0"
    audit_color = str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed"
    neutral_text = "#334155"

    layer_ids = [str(item["layer_id"]) for item in layer_order]
    layer_labels = [str(item["layer_label"]) for item in layer_order]
    layer_index = {layer_id: index for index, layer_id in enumerate(layer_ids)}

    all_effect_values = [
        float(layer_support["effect_value"])
        for program in programs
        for layer_support in list(program.get("layer_supports") or [])
    ]
    all_support_values = [
        float(layer_support["support_fraction"])
        for program in programs
        for layer_support in list(program.get("layer_supports") or [])
    ]
    max_abs_effect = max(max(abs(value) for value in all_effect_values), 1e-6)
    if any(value < 0.0 for value in all_effect_values) and any(value > 0.0 for value in all_effect_values):
        effect_norm: matplotlib.colors.Normalize = matplotlib.colors.TwoSlopeNorm(
            vmin=-max_abs_effect,
            vcenter=0.0,
            vmax=max_abs_effect,
        )
    else:
        min_effect = min(all_effect_values)
        max_effect = max(all_effect_values)
        if math.isclose(min_effect, max_effect, rel_tol=1e-9, abs_tol=1e-9):
            min_effect -= 1.0
            max_effect += 1.0
        effect_norm = matplotlib.colors.Normalize(vmin=min_effect, vmax=max_effect)
    effect_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "genomic_program_governance",
        [primary_color, "#f8fafc", secondary_color],
    )
    support_min = min(all_support_values)
    support_max = max(all_support_values)

    def _support_marker_size(support_fraction: float) -> float:
        if math.isclose(support_min, support_max, rel_tol=1e-9, abs_tol=1e-9):
            return 190.0
        normalized = (support_fraction - support_min) / (support_max - support_min)
        return 105.0 + normalized * 255.0

    row_count = len(programs)
    figure_height = max(5.4, 1.00 * row_count + 2.4)
    fig, (evidence_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(11.6, figure_height),
        gridspec_kw={"width_ratios": [1.48, 1.02]},
    )
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
            color=neutral_text,
            y=0.985,
        )

    evidence_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("evidence_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.24,
        font_size=axis_title_size,
        font_weight="bold",
    )
    evidence_axes.set_title(
        "\n".join(evidence_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_text,
        pad=12.0,
    )
    evidence_axes.set_xlim(-0.6, len(layer_labels) - 0.4)
    evidence_axes.set_ylim(-0.6, row_count - 0.4)
    evidence_axes.invert_yaxis()
    evidence_axes.set_xticks(range(len(layer_labels)))
    evidence_axes.set_xticklabels(
        layer_labels,
        rotation=18,
        ha="right",
        fontsize=max(tick_size - 0.4, 8.4),
        color=neutral_text,
    )
    evidence_axes.set_yticks([])
    evidence_axes.tick_params(axis="x", labelsize=max(tick_size - 0.4, 8.4), colors=neutral_text)
    evidence_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.8, zorder=0)
    evidence_axes.grid(axis="y", linestyle=":", color=light_fill, linewidth=0.6, zorder=0)
    _apply_publication_axes_style(evidence_axes)

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color=neutral_text,
        pad=12.0,
    )
    summary_axes.set_xlim(0.0, 1.0)
    summary_axes.set_ylim(-0.6, row_count - 0.4)
    summary_axes.invert_yaxis()
    summary_axes.set_xticks([])
    summary_axes.set_yticks([])
    for spine in summary_axes.spines.values():
        spine.set_visible(False)
    summary_axes.set_facecolor("white")

    blended_transform = matplotlib.transforms.blended_transform_factory(evidence_axes.transAxes, evidence_axes.transData)
    row_label_artists: list[Any] = []
    priority_artists: list[Any] = []
    verdict_artists: list[Any] = []
    support_artists: list[Any] = []
    action_artists: list[Any] = []
    detail_artists: list[Any | None] = []
    normalized_programs_for_sidecar: list[dict[str, Any]] = []

    priority_color_lookup = {
        "high_priority": secondary_color,
        "monitor": audit_color,
        "watchlist": reference_color,
    }
    verdict_color_lookup = {
        "convergent": secondary_color,
        "layer_specific": audit_color,
        "context_dependent": reference_color,
        "insufficient_support": "#7f1d1d",
    }

    scatter_x: list[float] = []
    scatter_y: list[float] = []
    scatter_sizes: list[float] = []
    scatter_colors: list[float] = []
    scatter_records: list[tuple[int, str, float, float]] = []

    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18
    for row_index, program in enumerate(programs):
        y_center = float(row_index)
        row_label_artists.append(
            evidence_axes.text(
                -0.03,
                y_center,
                str(program["program_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.1, 8.7),
                color=neutral_text,
                clip_on=False,
            )
        )
        for layer_support in list(program.get("layer_supports") or []):
            layer_id = str(layer_support["layer_id"])
            effect_value = float(layer_support["effect_value"])
            support_fraction = float(layer_support["support_fraction"])
            scatter_x.append(float(layer_index[layer_id]))
            scatter_y.append(y_center)
            scatter_sizes.append(_support_marker_size(support_fraction))
            scatter_colors.append(effect_value)
            scatter_records.append((row_index, layer_id, effect_value, support_fraction))

        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.04, y_center - 0.36),
            0.92,
            0.72,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            transform=summary_axes.transData,
            facecolor=primary_soft if row_index % 2 == 0 else light_fill,
            edgecolor=summary_fill,
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        priority_artist = summary_axes.text(
            0.08,
            y_center - 0.19,
            str(program["priority_band"]).replace("_", " ").title(),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 1.1, 7.8),
            fontweight="bold",
            color="white",
            bbox={
                "boxstyle": "round,pad=0.28,rounding_size=0.14",
                "facecolor": priority_color_lookup.get(str(program["priority_band"]), reference_color),
                "edgecolor": "none",
            },
            zorder=2,
        )
        verdict_artist = summary_axes.text(
            0.43,
            y_center - 0.19,
            str(program["verdict"]).replace("_", " "),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 0.6, 8.4),
            fontweight="bold",
            color=verdict_color_lookup.get(str(program["verdict"]), neutral_text),
            zorder=2,
        )
        support_artist = summary_axes.text(
            0.08,
            y_center + 0.01,
            f"{program['lead_driver_label']} | {program['dominant_pathway_label']} | "
            f"h={int(program['pathway_hit_count'])} | r={int(program['priority_rank'])}",
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 1.0, 7.8),
            color=neutral_text,
            zorder=2,
        )
        action_lines = _wrap_flow_text_to_width(
            str(program["action"]),
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 0.9, 7.9),
            font_weight="bold",
        )
        action_artist = summary_axes.text(
            0.08,
            y_center + 0.23,
            "\n".join(action_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(tick_size - 0.9, 7.9),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        detail_text = str(program.get("detail") or "").strip()

        priority_artists.append(priority_artist)
        verdict_artists.append(verdict_artist)
        support_artists.append(support_artist)
        action_artists.append(action_artist)
        detail_artists.append(detail_artist)

        normalized_program = {
            "program_id": str(program["program_id"]),
            "program_label": str(program["program_label"]),
            "lead_driver_label": str(program["lead_driver_label"]),
            "dominant_pathway_label": str(program["dominant_pathway_label"]),
            "pathway_hit_count": int(program["pathway_hit_count"]),
            "priority_rank": int(program["priority_rank"]),
            "priority_band": str(program["priority_band"]),
            "verdict": str(program["verdict"]),
            "action": str(program["action"]),
        }
        if detail_text:
            normalized_program["detail"] = detail_text
        normalized_programs_for_sidecar.append(normalized_program)

    scatter_artist = evidence_axes.scatter(
        scatter_x,
        scatter_y,
        s=scatter_sizes,
        c=scatter_colors,
        cmap=effect_cmap,
        norm=effect_norm,
        alpha=0.94,
        edgecolors="white",
        linewidths=0.9,
        zorder=3,
    )

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.74, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.25, right=0.96, top=top_margin, bottom=0.20, wspace=0.18)

    support_legend_values = sorted(
        {
            round(support_min, 2),
            round((support_min + support_max) / 2.0, 2),
            round(support_max, 2),
        }
    )
    support_legend_handles = [
        plt.scatter([], [], s=_support_marker_size(float(value)), color="#94a3b8", edgecolors="white", linewidths=0.8)
        for value in support_legend_values
    ]
    support_legend = fig.legend(
        support_legend_handles,
        [f"{value:.2f}" for value in support_legend_values],
        title=str(display_payload.get("support_scale_label") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.28, 0.04),
        ncol=len(support_legend_handles),
        frameon=False,
        fontsize=max(tick_size - 1.0, 7.8),
        title_fontsize=max(tick_size - 0.4, 8.4),
        columnspacing=0.9,
    )
    fig.add_artist(support_legend)
    colorbar_axes = evidence_axes.inset_axes([0.94, 0.14, 0.028, 0.72])
    colorbar = fig.colorbar(scatter_artist, cax=colorbar_axes)
    colorbar.set_label(
        str(display_payload.get("effect_scale_label") or "").strip(),
        fontsize=max(axis_title_size - 0.3, 9.6),
        color=neutral_text,
    )
    colorbar.ax.tick_params(labelsize=max(tick_size - 0.7, 8.0), colors=neutral_text)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.026, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.6, 13.2),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    panel_label_a = _add_panel_label(axes_item=evidence_axes, label="A")
    panel_label_b = _add_panel_label(axes_item=summary_axes, label="B")
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
                bbox=evidence_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_A",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=summary_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_B",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_a.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=panel_label_b.get_window_extent(renderer=renderer),
                box_id="panel_label_B",
                box_type="panel_label",
            ),
        ]
    )
    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=evidence_axes.get_window_extent(renderer=renderer),
            box_id="panel_evidence",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="panel_summary",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=support_legend.get_window_extent(renderer=renderer),
            box_id="legend_support",
            box_type="legend",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="colorbar_effect",
            box_type="colorbar",
        ),
    ]

    evidence_box_width = 0.14
    evidence_box_height = 0.10
    scatter_record_index = 0
    for row_index, normalized_program in enumerate(normalized_programs_for_sidecar):
        row_label_box_id = f"row_label_{normalized_program['program_id']}"
        priority_box_id = f"priority_{normalized_program['program_id']}"
        verdict_box_id = f"verdict_{normalized_program['program_id']}"
        support_box_id = f"support_{normalized_program['program_id']}"
        action_box_id = f"action_{normalized_program['program_id']}"
        detail_box_id = ""
        layout_boxes.extend(
            [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=row_label_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=row_label_box_id,
                    box_type="row_label",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=priority_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=priority_box_id,
                    box_type="priority_badge",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=verdict_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=verdict_box_id,
                    box_type="verdict_value",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=support_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=support_box_id,
                    box_type="row_support",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=action_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=action_box_id,
                    box_type="row_action",
                ),
            ]
        )
        if detail_artists[row_index] is not None:
            detail_box_id = f"detail_{normalized_program['program_id']}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=detail_artists[row_index].get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="row_detail",
                )
            )

        normalized_program.update(
            {
                "row_label_box_id": row_label_box_id,
                "priority_box_id": priority_box_id,
                "verdict_box_id": verdict_box_id,
                "support_box_id": support_box_id,
                "action_box_id": action_box_id,
            }
        )
        if detail_box_id:
            normalized_program["detail_box_id"] = detail_box_id
        normalized_layer_supports: list[dict[str, Any]] = []
        for layer_id in layer_ids:
            record_row_index, record_layer_id, effect_value, support_fraction = scatter_records[scatter_record_index]
            assert record_row_index == row_index and record_layer_id == layer_id
            cell_box_id = f"evidence_{normalized_program['program_id']}_{layer_id}"
            layout_boxes.append(
                _data_box_to_layout_box(
                    axes=evidence_axes,
                    figure=fig,
                    x0=float(layer_index[layer_id]) - evidence_box_width / 2.0,
                    y0=float(row_index) - evidence_box_height / 2.0,
                    x1=float(layer_index[layer_id]) + evidence_box_width / 2.0,
                    y1=float(row_index) + evidence_box_height / 2.0,
                    box_id=cell_box_id,
                    box_type="evidence_cell",
                )
            )
            normalized_layer_supports.append(
                {
                    "layer_id": layer_id,
                    "effect_value": effect_value,
                    "support_fraction": support_fraction,
                    "cell_box_id": cell_box_id,
                }
            )
            scatter_record_index += 1
        normalized_program["layer_supports"] = normalized_layer_supports

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "effect_scale_label": str(display_payload.get("effect_scale_label") or "").strip(),
                "support_scale_label": str(display_payload.get("support_scale_label") or "").strip(),
                "layer_labels": layer_labels,
                "programs": normalized_programs_for_sidecar,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

