from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ...shared import (
    _apply_publication_axes_style,
    _bbox_to_layout_box,
    _centered_offsets,
    _data_box_to_layout_box,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    _wrap_flow_text_to_width,
    dump_json,
)

def _render_python_broader_heterogeneity_summary_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    effect_rows = list(display_payload.get("effect_rows") or [])
    slices = sorted(list(display_payload.get("slices") or []), key=lambda item: int(item["slice_order"]))
    if not effect_rows or not slices:
        raise RuntimeError(f"{template_id} requires non-empty effect_rows and slices")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    typography = dict(render_context.get("typography") or {})
    palette = dict(render_context.get("palette") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    stroke = dict(render_context.get("stroke") or {})
    layout_override = dict(render_context.get("layout_override") or {})

    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.8))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    accent_colors = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("audit") or "#7c3aed").strip() or "#7c3aed",
        str(palette.get("secondary_soft") or "#0f766e").strip() or "#0f766e",
        str(palette.get("primary") or "#b45309").strip() or "#b45309",
    ]
    slice_color_lookup = {
        str(slice_item["slice_id"]): accent_colors[index % len(accent_colors)] for index, slice_item in enumerate(slices)
    }

    reference_value = float(display_payload["reference_value"])
    all_x_values = [reference_value]
    for row in effect_rows:
        for estimate in list(row.get("slice_estimates") or []):
            all_x_values.extend((float(estimate["lower"]), float(estimate["estimate"]), float(estimate["upper"])))
    x_min = min(all_x_values)
    x_max = max(all_x_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.08)
    x_lower = max(0.0, x_min - x_padding) if x_min >= 0.0 else x_min - x_padding
    x_upper = x_max + x_padding
    interval_half_height = 0.030
    marker_half_height = 0.095
    marker_half_width = max((x_upper - x_lower) * 0.010, 0.015)
    reference_half_width = max((x_upper - x_lower) * 0.003, 0.0015)

    row_count = len(effect_rows)
    figure_height = max(5.0, 0.82 * row_count + 2.2)
    fig, (matrix_axes, summary_axes) = plt.subplots(
        1,
        2,
        figsize=(10.8, figure_height),
        gridspec_kw={"width_ratios": [2.75, 1.35]},
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
            color="#13293d",
            y=0.985,
        )

    matrix_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("matrix_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )
    summary_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("summary_panel_title") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.20,
        font_size=axis_title_size,
        font_weight="bold",
    )
    x_axis_title_lines = _wrap_flow_text_to_width(
        str(display_payload.get("x_label") or "").strip(),
        max_width_pt=fig.get_figwidth() * 72.0 * 0.34,
        font_size=axis_title_size,
        font_weight="bold",
    )

    matrix_axes.set_title(
        "\n".join(matrix_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=12.0,
    )
    matrix_axes.set_xlabel(
        "\n".join(x_axis_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    matrix_axes.axvline(reference_value, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    matrix_axes.set_xlim(x_lower, x_upper)
    matrix_axes.set_ylim(-0.6, row_count - 0.4)
    matrix_axes.invert_yaxis()
    matrix_axes.set_yticks([])
    matrix_axes.tick_params(axis="x", labelsize=tick_size, colors="#334155")
    matrix_axes.grid(axis="x", color="#dbe4ee", linewidth=0.70, linestyle=":", zorder=0)
    _apply_publication_axes_style(matrix_axes)

    summary_axes.set_title(
        "\n".join(summary_title_lines),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
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

    row_label_artists: list[Any] = []
    estimate_records: list[dict[str, Any]] = []
    verdict_records: list[dict[str, Any]] = []
    blended_transform = matplotlib.transforms.blended_transform_factory(matrix_axes.transAxes, matrix_axes.transData)
    slice_offsets = _centered_offsets(len(slices), half_span=0.22 if len(slices) <= 3 else 0.27)
    slice_order_lookup = {str(slice_item["slice_id"]): index for index, slice_item in enumerate(slices)}

    summary_text_width_pt = fig.get_figwidth() * 72.0 * 0.18
    row_band_height = 0.56
    for row_index, row in enumerate(effect_rows):
        y_center = float(row_index)
        row_label_artists.append(
            matrix_axes.text(
                -0.03,
                y_center,
                str(row["row_label"]),
                transform=blended_transform,
                ha="right",
                va="center",
                fontsize=max(tick_size - 0.2, 8.8),
                color="#334155",
                clip_on=False,
            )
        )
        ordered_estimates = sorted(
            list(row.get("slice_estimates") or []),
            key=lambda item: slice_order_lookup[str(item["slice_id"])],
        )
        normalized_slice_estimates: list[dict[str, Any]] = []
        for estimate_index, estimate in enumerate(ordered_estimates):
            slice_id = str(estimate["slice_id"])
            plot_y = y_center + slice_offsets[estimate_index]
            slice_color = slice_color_lookup[slice_id]
            matrix_axes.plot(
                [float(estimate["lower"]), float(estimate["upper"])],
                [plot_y, plot_y],
                color=slice_color,
                linewidth=2.1,
                solid_capstyle="round",
                zorder=3,
            )
            matrix_axes.scatter(
                [float(estimate["estimate"])],
                [plot_y],
                s=marker_size**2,
                color=slice_color,
                edgecolors="white",
                linewidths=0.8,
                zorder=4,
            )
            normalized_estimate = {
                "slice_id": slice_id,
                "estimate": float(estimate["estimate"]),
                "lower": float(estimate["lower"]),
                "upper": float(estimate["upper"]),
                "plot_y": float(plot_y),
            }
            if estimate.get("support_n") is not None:
                normalized_estimate["support_n"] = int(estimate["support_n"])
            normalized_slice_estimates.append(normalized_estimate)
        estimate_records.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "verdict": str(row["verdict"]),
                "detail": str(row.get("detail") or "").strip(),
                "slice_estimates": normalized_slice_estimates,
            }
        )

        band_bottom = y_center - row_band_height / 2.0
        band_patch = matplotlib.patches.FancyBboxPatch(
            (0.05, band_bottom),
            0.90,
            row_band_height,
            boxstyle="round,pad=0.010,rounding_size=0.015",
            transform=summary_axes.transData,
            facecolor=str(palette.get("light") or "#f8fafc").strip() or "#f8fafc",
            edgecolor=str(palette.get("secondary_soft") or "#cbd5e1").strip() or "#cbd5e1",
            linewidth=0.95,
            zorder=1,
        )
        summary_axes.add_patch(band_patch)

        verdict_lines = _wrap_flow_text_to_width(
            str(row["verdict"]).replace("_", " "),
            max_width_pt=summary_text_width_pt,
            font_size=max(axis_title_size - 0.8, 9.2),
            font_weight="bold",
        )
        detail_text = str(row.get("detail") or "").strip()
        detail_lines = _wrap_flow_text_to_width(
            detail_text,
            max_width_pt=summary_text_width_pt,
            font_size=max(tick_size - 1.0, 7.8),
            font_weight="normal",
        )
        verdict_artist = summary_axes.text(
            0.10,
            y_center - 0.11,
            "\n".join(verdict_lines),
            transform=summary_axes.transData,
            ha="left",
            va="center",
            fontsize=max(axis_title_size - 0.8, 9.2),
            fontweight="bold",
            color="#13293d",
            zorder=2,
        )
        detail_artist = None
        if detail_lines:
            detail_artist = summary_axes.text(
                0.10,
                y_center + 0.10,
                "\n".join(detail_lines),
                transform=summary_axes.transData,
                ha="left",
                va="center",
                fontsize=max(tick_size - 1.0, 7.8),
                color="#64748b",
                zorder=2,
            )
        verdict_records.append(
            {
                "row_id": str(row["row_id"]),
                "row_label": str(row["row_label"]),
                "verdict": str(row["verdict"]),
                "detail": detail_text,
                "verdict_artist": verdict_artist,
                "detail_artist": detail_artist,
            }
        )

    legend_handles = [
        matplotlib.lines.Line2D(
            [0.0],
            [0.0],
            color=slice_color_lookup[str(slice_item["slice_id"])],
            linewidth=2.0,
            marker="o",
            markersize=max(marker_size + 1.0, 5.5),
            markerfacecolor=slice_color_lookup[str(slice_item["slice_id"])],
            markeredgecolor="white",
            label=str(slice_item["slice_label"]),
        )
        for slice_item in slices
    ]
    legend = matrix_axes.legend(
        handles=legend_handles,
        title=str(display_payload.get("slice_legend_title") or "").strip(),
        frameon=False,
        loc="upper left",
        bbox_to_anchor=(0.0, -0.14),
        ncol=min(len(slices), 3),
        columnspacing=1.2,
        handletextpad=0.6,
        borderaxespad=0.0,
        fontsize=max(tick_size - 0.4, 8.8),
        title_fontsize=max(axis_title_size - 0.6, 9.4),
    )

    top_margin = 0.83 if show_figure_title else 0.90
    top_margin = max(0.72, top_margin - 0.05 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.22, right=0.97, top=top_margin, bottom=0.24, wspace=0.16)
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

    panel_label_a = _add_panel_label(axes_item=matrix_axes, label="A")
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
                bbox=matrix_axes.title.get_window_extent(renderer=renderer),
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
            _bbox_to_layout_box(
                figure=fig,
                bbox=matrix_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    legend_title = legend.get_title()
    if legend_title.get_text().strip():
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_title.get_window_extent(renderer=renderer),
                box_id="slice_legend_title",
                box_type="legend_title",
            )
        )
    legend_texts = list(legend.get_texts())
    normalized_slices: list[dict[str, Any]] = []
    for slice_item, legend_text in zip(slices, legend_texts, strict=True):
        legend_box_id = f"slice_legend_{slice_item['slice_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend_text.get_window_extent(renderer=renderer),
                box_id=legend_box_id,
                box_type="legend_label",
            )
        )
        normalized_slices.append(
            {
                "slice_id": str(slice_item["slice_id"]),
                "slice_label": str(slice_item["slice_label"]),
                "slice_kind": str(slice_item["slice_kind"]),
                "slice_order": int(slice_item["slice_order"]),
                "legend_label_box_id": legend_box_id,
            }
        )

    panel_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=matrix_axes.get_window_extent(renderer=renderer),
            box_id="matrix_panel",
            box_type="panel",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=summary_axes.get_window_extent(renderer=renderer),
            box_id="summary_panel",
            box_type="panel",
        ),
    ]
    guide_boxes = [
        _data_box_to_layout_box(
            axes=matrix_axes,
            figure=fig,
            x0=reference_value - reference_half_width,
            y0=-0.5,
            x1=reference_value + reference_half_width,
            y1=row_count - 0.5,
            box_id="reference_line",
            box_type="reference_line",
        )
    ]

    normalized_effect_rows: list[dict[str, Any]] = []
    for row_record, row_label_artist, verdict_record in zip(
        estimate_records,
        row_label_artists,
        verdict_records,
        strict=True,
    ):
        row_label_box_id = f"row_label_{row_record['row_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=row_label_artist.get_window_extent(renderer=renderer),
                box_id=row_label_box_id,
                box_type="row_label",
            )
        )
        verdict_box_id = f"verdict_{row_record['row_id']}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=verdict_record["verdict_artist"].get_window_extent(renderer=renderer),
                box_id=verdict_box_id,
                box_type="verdict_value",
            )
        )
        detail_box_id = ""
        if verdict_record["detail_artist"] is not None:
            detail_box_id = f"detail_{row_record['row_id']}"
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=verdict_record["detail_artist"].get_window_extent(renderer=renderer),
                    box_id=detail_box_id,
                    box_type="verdict_detail",
                )
            )

        normalized_slice_estimates: list[dict[str, Any]] = []
        for estimate in row_record["slice_estimates"]:
            slice_id = str(estimate["slice_id"])
            marker_box_id = f"estimate_{row_record['row_id']}_{slice_id}"
            interval_box_id = f"ci_{row_record['row_id']}_{slice_id}"
            layout_boxes.extend(
                [
                    _data_box_to_layout_box(
                        axes=matrix_axes,
                        figure=fig,
                        x0=float(estimate["estimate"]) - marker_half_width,
                        y0=float(estimate["plot_y"]) - marker_half_height,
                        x1=float(estimate["estimate"]) + marker_half_width,
                        y1=float(estimate["plot_y"]) + marker_half_height,
                        box_id=marker_box_id,
                        box_type="estimate_marker",
                    ),
                    _data_box_to_layout_box(
                        axes=matrix_axes,
                        figure=fig,
                        x0=float(estimate["lower"]),
                        y0=float(estimate["plot_y"]) - interval_half_height,
                        x1=float(estimate["upper"]),
                        y1=float(estimate["plot_y"]) + interval_half_height,
                        box_id=interval_box_id,
                        box_type="ci_segment",
                    ),
                ]
            )
            normalized_estimate = {
                "slice_id": slice_id,
                "estimate": float(estimate["estimate"]),
                "lower": float(estimate["lower"]),
                "upper": float(estimate["upper"]),
                "marker_box_id": marker_box_id,
                "interval_box_id": interval_box_id,
            }
            if estimate.get("support_n") is not None:
                normalized_estimate["support_n"] = int(estimate["support_n"])
            normalized_slice_estimates.append(normalized_estimate)

        normalized_row = {
            "row_id": str(row_record["row_id"]),
            "row_label": str(row_record["row_label"]),
            "verdict": str(row_record["verdict"]),
            "label_box_id": row_label_box_id,
            "verdict_box_id": verdict_box_id,
            "slice_estimates": normalized_slice_estimates,
        }
        detail_text = str(row_record.get("detail") or "").strip()
        if detail_text:
            normalized_row["detail"] = detail_text
        if detail_box_id:
            normalized_row["detail_box_id"] = detail_box_id
        normalized_effect_rows.append(normalized_row)

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "reference_value": reference_value,
                "matrix_panel": {
                    "panel_box_id": "matrix_panel",
                    "panel_label_box_id": "panel_label_A",
                    "panel_title_box_id": "panel_title_A",
                    "x_axis_title_box_id": "x_axis_title_A",
                    "reference_line_box_id": "reference_line",
                },
                "summary_panel": {
                    "panel_box_id": "summary_panel",
                    "panel_label_box_id": "panel_label_B",
                    "panel_title_box_id": "panel_title_B",
                },
                "slice_legend_title_box_id": "slice_legend_title",
                "slices": normalized_slices,
                "effect_rows": normalized_effect_rows,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

