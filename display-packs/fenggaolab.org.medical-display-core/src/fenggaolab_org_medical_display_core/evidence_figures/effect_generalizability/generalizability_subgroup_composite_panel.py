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
    dump_json,
)

def _render_python_generalizability_subgroup_composite_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    overview_rows = list(display_payload.get("overview_rows") or [])
    subgroup_rows = list(display_payload.get("subgroup_rows") or [])
    if not overview_rows or not subgroup_rows:
        raise RuntimeError(f"{template_id} requires non-empty overview_rows and subgroup_rows")

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

    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    model_color = _require_non_empty_string(
        style_roles.get("model_curve"),
        label=f"{template_id} render_context.style_roles.model_curve",
    )
    comparator_color = _require_non_empty_string(
        style_roles.get("comparator_curve"),
        label=f"{template_id} render_context.style_roles.comparator_curve",
    )
    light_fill = str(palette.get("light") or palette.get("secondary_soft") or comparator_color).strip() or comparator_color
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    primary_label = str(display_payload.get("primary_label") or "").strip()
    comparator_label = str(display_payload.get("comparator_label") or "").strip()

    overview_values = [float(row["metric_value"]) for row in overview_rows]
    if comparator_label:
        overview_values.extend(float(row["comparator_metric_value"]) for row in overview_rows)
    overview_min = min(overview_values)
    overview_max = max(overview_values)
    overview_span = max(overview_max - overview_min, 1e-6)
    overview_padding = max(overview_span * 0.16, 0.03)
    overview_support_margin = max(overview_span * 0.36, 0.08)
    overview_panel_xmin = overview_min - overview_padding
    overview_panel_xmax = overview_max + overview_padding + overview_support_margin
    overview_support_x = overview_max + overview_padding * 0.35

    subgroup_values = [float(display_payload["subgroup_reference_value"])]
    for row in subgroup_rows:
        subgroup_values.extend((float(row["lower"]), float(row["upper"]), float(row["estimate"])))
    subgroup_min = min(subgroup_values)
    subgroup_max = max(subgroup_values)
    subgroup_span = max(subgroup_max - subgroup_min, 1e-6)
    subgroup_padding = max(subgroup_span * 0.16, 0.03)
    subgroup_panel_xmin = subgroup_min - subgroup_padding
    subgroup_panel_xmax = subgroup_max + subgroup_padding
    max_rows = max(len(overview_rows), len(subgroup_rows))
    figure_height = max(4.8, 0.54 * max_rows + 2.6)
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10.8, figure_height),
        gridspec_kw={"width_ratios": [1.18, 1.0]},
        squeeze=False,
    )
    overview_axes, subgroup_axes = axes[0]
    fig.patch.set_facecolor("white")

    title_artist = None
    if show_figure_title:
        title_artist = fig.suptitle(
            str(display_payload.get("title") or "").strip(),
            fontsize=title_size,
            fontweight="bold",
            color=reference_color,
            y=0.985,
        )

    overview_row_label_specs: list[tuple[str, float]] = []
    overview_support_label_artists: list[Any] = []
    overview_metric_artists: list[Any] = []
    overview_comparator_artists: list[Any] = []
    overview_metrics_for_sidecar: list[dict[str, Any]] = []
    for row_index, row in enumerate(overview_rows):
        y_pos = float(row_index)
        overview_row_label_specs.append((str(row["cohort_label"]), y_pos))
        overview_support_label_artists.append(
            overview_axes.text(
                overview_support_x,
                y_pos,
                f"n={int(row['support_count'])}",
                ha="left",
                va="center",
                fontsize=max(tick_size - 1.1, 7.8),
                color="#475569",
                clip_on=False,
            )
        )
        if comparator_label:
            overview_comparator_artists.append(
                overview_axes.plot(
                    float(row["comparator_metric_value"]),
                    y_pos,
                    marker="o",
                    markersize=marker_size + 1.0,
                    markerfacecolor="white",
                    markeredgecolor=comparator_color,
                    markeredgewidth=1.1,
                    linestyle="None",
                    zorder=3,
                )[0]
            )
        overview_metric_artists.append(
            overview_axes.plot(
                float(row["metric_value"]),
                y_pos,
                marker="o",
                markersize=marker_size + 1.2,
                markerfacecolor=model_color,
                markeredgecolor=model_color,
                linestyle="None",
                zorder=4,
            )[0]
        )
        sidecar_row = {
            "cohort_id": str(row["cohort_id"]),
            "cohort_label": str(row["cohort_label"]),
            "support_count": int(row["support_count"]),
            "metric_value": float(row["metric_value"]),
            "label_box_id": f"overview_row_label_{row_index + 1}",
            "support_label_box_id": f"overview_support_label_{row_index + 1}",
            "metric_marker_box_id": f"overview_metric_marker_{row_index + 1}",
        }
        if row.get("event_count") is not None:
            sidecar_row["event_count"] = int(row["event_count"])
        if comparator_label:
            sidecar_row["comparator_metric_value"] = float(row["comparator_metric_value"])
            sidecar_row["comparator_marker_box_id"] = f"overview_comparator_marker_{row_index + 1}"
        overview_metrics_for_sidecar.append(sidecar_row)

    overview_axes.set_xlim(overview_panel_xmin, overview_panel_xmax)
    overview_axes.set_ylim(-0.7, len(overview_rows) - 0.3)
    overview_axes.invert_yaxis()
    overview_axes.set_yticks([])
    overview_axes.set_xlabel(
        str(display_payload.get("overview_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
    )
    overview_axes.set_title(
        str(display_payload.get("overview_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
        pad=10.0,
    )
    overview_axes.tick_params(axis="x", labelsize=tick_size, colors=reference_color)
    overview_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.65, zorder=0)
    _apply_publication_axes_style(overview_axes)

    subgroup_row_label_specs: list[tuple[str, float]] = []
    subgroup_ci_artists: list[Any] = []
    subgroup_estimate_artists: list[Any] = []
    subgroup_metrics_for_sidecar: list[dict[str, Any]] = []
    for row_index, row in enumerate(subgroup_rows):
        y_pos = float(row_index)
        subgroup_row_label_specs.append((str(row["subgroup_label"]), y_pos))
        subgroup_ci_artists.append(
            subgroup_axes.plot(
                [float(row["lower"]), float(row["upper"])],
                [y_pos, y_pos],
                color=reference_color,
                linewidth=1.4,
                zorder=2,
            )[0]
        )
        subgroup_estimate_artists.append(
            subgroup_axes.plot(
                float(row["estimate"]),
                y_pos,
                marker="s",
                markersize=marker_size + 0.8,
                markerfacecolor=model_color,
                markeredgecolor=model_color,
                linestyle="None",
                zorder=3,
            )[0]
        )
        sidecar_row = {
            "subgroup_id": str(row["subgroup_id"]),
            "subgroup_label": str(row["subgroup_label"]),
            "estimate": float(row["estimate"]),
            "lower": float(row["lower"]),
            "upper": float(row["upper"]),
            "label_box_id": f"subgroup_row_label_{row_index + 1}",
            "ci_box_id": f"subgroup_ci_{row_index + 1}",
            "estimate_box_id": f"subgroup_estimate_{row_index + 1}",
        }
        if row.get("group_n") is not None:
            sidecar_row["group_n"] = int(row["group_n"])
        subgroup_metrics_for_sidecar.append(sidecar_row)

    subgroup_axes.axvline(
        float(display_payload["subgroup_reference_value"]),
        color=comparator_color if comparator_label else reference_color,
        linewidth=1.0,
        linestyle="--",
        zorder=1,
    )
    subgroup_axes.set_xlim(subgroup_panel_xmin, subgroup_panel_xmax)
    subgroup_axes.set_ylim(-0.7, len(subgroup_rows) - 0.3)
    subgroup_axes.invert_yaxis()
    subgroup_axes.set_yticks([])
    subgroup_axes.set_xlabel(
        str(display_payload.get("subgroup_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
    )
    subgroup_axes.set_title(
        str(display_payload.get("subgroup_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color=reference_color,
        pad=10.0,
    )
    subgroup_axes.tick_params(axis="x", labelsize=tick_size, colors=reference_color)
    subgroup_axes.grid(axis="x", linestyle=":", color=light_fill, linewidth=0.65, zorder=0)
    _apply_publication_axes_style(subgroup_axes)

    legend = None
    if comparator_label:
        legend = fig.legend(
            handles=[
                matplotlib.lines.Line2D(
                    [], [], marker="o", linestyle="None", markersize=marker_size + 1.2, color=model_color, label=primary_label
                ),
                matplotlib.lines.Line2D(
                    [],
                    [],
                    marker="o",
                    linestyle="None",
                    markersize=marker_size + 1.0,
                    markerfacecolor="white",
                    markeredgecolor=comparator_color,
                    color=comparator_color,
                    label=comparator_label,
                ),
            ],
            title="Model context",
            frameon=False,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.02),
            ncol=2,
            borderaxespad=0.0,
        )

    subplot_top = 0.88 if show_figure_title else 0.94
    subplot_bottom = 0.14 if comparator_label else 0.11
    fig.subplots_adjust(left=0.11, right=0.97, top=subplot_top, bottom=subplot_bottom, wspace=0.36)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    overview_row_label_artists: list[Any] = []
    subgroup_row_label_artists: list[Any] = []

    overview_panel_bbox = overview_axes.get_window_extent(renderer=renderer)
    subgroup_panel_bbox = subgroup_axes.get_window_extent(renderer=renderer)
    overview_panel_x0, _ = fig.transFigure.inverted().transform((overview_panel_bbox.x0, overview_panel_bbox.y0))
    subgroup_panel_x0, _ = fig.transFigure.inverted().transform((subgroup_panel_bbox.x0, subgroup_panel_bbox.y0))
    outboard_gap = 0.008

    for label_text, y_pos in overview_row_label_specs:
        _, label_y = _data_point_to_figure_xy(
            axes=overview_axes,
            figure=fig,
            x=overview_panel_xmin,
            y=y_pos,
        )
        overview_row_label_artists.append(
            fig.text(
                overview_panel_x0 - outboard_gap,
                label_y,
                label_text,
                fontsize=max(tick_size - 0.3, 8.6),
                color=reference_color,
                ha="right",
                va="center",
            )
        )

    for label_text, y_pos in subgroup_row_label_specs:
        _, label_y = _data_point_to_figure_xy(
            axes=subgroup_axes,
            figure=fig,
            x=subgroup_panel_xmin,
            y=y_pos,
        )
        subgroup_row_label_artists.append(
            fig.text(
                subgroup_panel_x0 - outboard_gap,
                label_y,
                label_text,
                fontsize=max(tick_size - 0.3, 8.6),
                color=reference_color,
                ha="right",
                va="center",
            )
        )

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
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.8, 13.2),
            fontweight="bold",
            color=reference_color,
            ha="left",
            va="top",
        )

    overview_panel_label = _add_panel_label(axes_item=overview_axes, label="A")
    subgroup_panel_label = _add_panel_label(axes_item=subgroup_axes, label="B")
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
                bbox=overview_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_A",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_axes.title.get_window_extent(renderer=renderer),
                box_id="panel_title_B",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=overview_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_A",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_axes.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title_B",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=overview_panel_label.get_window_extent(renderer=renderer),
                box_id="panel_label_A",
                box_type="panel_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=subgroup_panel_label.get_window_extent(renderer=renderer),
                box_id="panel_label_B",
                box_type="panel_label",
            ),
        ]
    )
    for index, artist in enumerate(overview_row_label_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_row_label_{index}",
                box_type="overview_row_label",
            )
        )
    for index, artist in enumerate(overview_support_label_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_support_label_{index}",
                box_type="support_label",
            )
        )
    for index, artist in enumerate(overview_metric_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_metric_marker_{index}",
                box_type="overview_metric_marker",
            )
        )
    for index, artist in enumerate(overview_comparator_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"overview_comparator_marker_{index}",
                box_type="overview_comparator_marker",
            )
        )
    for index, artist in enumerate(subgroup_row_label_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"subgroup_row_label_{index}",
                box_type="subgroup_row_label",
            )
        )
    for index, artist in enumerate(subgroup_ci_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"subgroup_ci_{index}",
                box_type="ci_segment",
            )
        )
    for index, artist in enumerate(subgroup_estimate_artists, start=1):
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=f"subgroup_estimate_{index}",
                box_type="estimate_marker",
            )
        )

    guide_boxes: list[dict[str, Any]] = []
    if legend is not None:
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="legend",
                box_type="legend",
            )
        )

    dump_json(
        layout_sidecar_path,
        {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": [
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=overview_axes.get_window_extent(renderer=renderer),
                    box_id="overview_panel",
                    box_type="panel",
                ),
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=subgroup_axes.get_window_extent(renderer=renderer),
                    box_id="subgroup_panel",
                    box_type="panel",
                ),
            ],
            "guide_boxes": guide_boxes,
            "metrics": {
                "metric_family": str(display_payload.get("metric_family") or "").strip(),
                "primary_label": primary_label,
                "comparator_label": comparator_label,
                "legend_title": "Model context" if comparator_label else "",
                "legend_labels": [primary_label, comparator_label] if comparator_label else [],
                "overview_rows": overview_metrics_for_sidecar,
                "subgroup_reference_value": float(display_payload["subgroup_reference_value"]),
                "subgroup_rows": subgroup_metrics_for_sidecar,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

