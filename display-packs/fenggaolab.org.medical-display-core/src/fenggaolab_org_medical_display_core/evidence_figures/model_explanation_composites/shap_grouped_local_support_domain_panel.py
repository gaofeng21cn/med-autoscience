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
    _data_point_to_figure_xy,
    _prepare_python_render_output_paths,
    _read_bool_override,
    _require_non_empty_string,
    _wrap_figure_title_to_width,
    dump_json,
)

def _render_python_shap_grouped_local_support_domain_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    local_panels = list(display_payload.get("local_panels") or [])
    support_panels = list(display_payload.get("support_panels") or [])
    if not local_panels or not support_panels:
        raise RuntimeError(f"{template_id} requires non-empty local_panels and support_panels")

    _prepare_python_render_output_paths(
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    render_context = dict(display_payload.get("render_context") or {})
    style_roles = dict(render_context.get("style_roles") or {})
    palette = dict(render_context.get("palette") or {})
    typography = dict(render_context.get("typography") or {})
    stroke = dict(render_context.get("stroke") or {})
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
    curve_color = negative_color
    reference_color = zero_line_color
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    observed_fill = str(palette.get("primary") or curve_color).strip() or curve_color
    subgroup_fill = "#0f766e"
    bin_fill = "#b45309"
    extrapolation_fill = "#dc2626"
    support_style_map = {
        "observed_support": {
            "facecolor": matplotlib.colors.to_rgba(observed_fill, alpha=0.20),
            "edgecolor": observed_fill,
            "legend_label": "Observed support",
        },
        "subgroup_support": {
            "facecolor": matplotlib.colors.to_rgba(subgroup_fill, alpha=0.18),
            "edgecolor": subgroup_fill,
            "legend_label": "Subgroup support",
        },
        "bin_support": {
            "facecolor": matplotlib.colors.to_rgba(bin_fill, alpha=0.18),
            "edgecolor": bin_fill,
            "legend_label": "Bin support",
        },
        "extrapolation_warning": {
            "facecolor": matplotlib.colors.to_rgba(extrapolation_fill, alpha=0.14),
            "edgecolor": extrapolation_fill,
            "legend_label": "Extrapolation reminder",
        },
    }
    legend_labels = [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]

    normalized_local_panels: list[dict[str, Any]] = []
    max_abs_value = 0.0
    max_contribution_count = 0
    for panel in local_panels:
        contributions: list[dict[str, Any]] = []
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
        normalized_local_panels.append(
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

    normalized_support_panels: list[dict[str, Any]] = []
    all_curve_y: list[float] = []
    for panel in support_panels:
        curve_x = [float(value) for value in panel["response_curve"]["x"]]
        curve_y = [float(value) for value in panel["response_curve"]["y"]]
        all_curve_y.extend(curve_y)
        normalized_support_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": str(panel["panel_label"]),
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "response_curve": {"x": curve_x, "y": curve_y},
                "support_segments": [
                    {
                        "segment_id": str(segment["segment_id"]),
                        "segment_label": str(segment["segment_label"]),
                        "support_kind": str(segment["support_kind"]),
                        "domain_start": float(segment["domain_start"]),
                        "domain_end": float(segment["domain_end"]),
                    }
                    for segment in panel["support_segments"]
                ],
            }
        )

    x_padding = max(max_abs_value * 0.20, 0.05)
    x_limit = max_abs_value + x_padding
    label_margin = max(x_limit * 0.06, 0.03)

    curve_y_min = min(all_curve_y)
    curve_y_max = max(all_curve_y)
    curve_y_span = max(curve_y_max - curve_y_min, 1e-6)
    support_band_height = max(curve_y_span * 0.18, 0.06)
    support_band_gap = max(curve_y_span * 0.14, 0.05)
    band_y1 = curve_y_min - support_band_gap
    band_y0 = band_y1 - support_band_height
    curve_y_padding = max(curve_y_span * 0.18, 0.05)
    plot_y_lower = band_y0 - max(support_band_height * 0.40, 0.05)
    plot_y_upper = curve_y_max + curve_y_padding
    band_mid_y = (band_y0 + band_y1) / 2.0

    figure_width = max(10.6, 3.5 * max(len(normalized_local_panels), len(normalized_support_panels)) + 2.6)
    local_row_height = max(3.3, 0.62 * max_contribution_count + 1.8)
    support_row_height = 3.8
    figure_height = local_row_height + support_row_height + 0.8

    fig = plt.figure(figsize=(figure_width, figure_height))
    fig.patch.set_facecolor("white")
    root_grid = fig.add_gridspec(2, 1, height_ratios=[local_row_height, support_row_height], hspace=0.46)
    local_grid = root_grid[0].subgridspec(1, len(normalized_local_panels), wspace=0.34)
    support_grid = root_grid[1].subgridspec(1, len(normalized_support_panels), wspace=0.34)
    local_axes = [fig.add_subplot(local_grid[0, index]) for index in range(len(normalized_local_panels))]
    support_axes = [fig.add_subplot(support_grid[0, index]) for index in range(len(normalized_support_panels))]

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

    local_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(local_axes, normalized_local_panels, strict=True):
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
            str(display_payload.get("grouped_local_x_label") or "").strip(),
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

        local_records.append(
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

    support_records: list[dict[str, Any]] = []
    for axes_item, panel in zip(support_axes, normalized_support_panels, strict=True):
        curve_x = [float(value) for value in panel["response_curve"]["x"]]
        curve_y = [float(value) for value in panel["response_curve"]["y"]]
        x_min = min(curve_x)
        x_max = max(curve_x)
        x_span = max(x_max - x_min, 1e-6)
        x_padding_support = max(x_span * 0.08, 0.04)

        support_label_artists: list[Any] = []
        for segment in panel["support_segments"]:
            support_style = support_style_map[str(segment["support_kind"])]
            segment_start = float(segment["domain_start"])
            segment_end = float(segment["domain_end"])
            segment_patch = matplotlib.patches.Rectangle(
                (segment_start, band_y0),
                segment_end - segment_start,
                support_band_height,
                facecolor=support_style["facecolor"],
                edgecolor=support_style["edgecolor"],
                linewidth=1.0,
                zorder=1,
            )
            axes_item.add_patch(segment_patch)
            support_label_artists.append(
                axes_item.text(
                    (segment_start + segment_end) / 2.0,
                    band_mid_y,
                    str(segment["segment_label"]),
                    fontsize=max(tick_size - 1.1, 7.6),
                    color="#334155",
                    ha="center",
                    va="center",
                    zorder=3,
                )
            )

        axes_item.plot(
            curve_x,
            curve_y,
            color=curve_color,
            linewidth=2.4,
            marker="o",
            markersize=marker_size,
            markerfacecolor="white",
            markeredgecolor=curve_color,
            markeredgewidth=1.1,
            zorder=4,
        )
        reference_value = float(panel["reference_value"])
        axes_item.axvline(
            reference_value,
            color=reference_color,
            linewidth=1.0,
            linestyle="--",
            zorder=2,
        )
        reference_label_artist = axes_item.text(
            reference_value,
            plot_y_upper - curve_y_padding * 0.35,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=reference_color,
            ha="center",
            va="top",
            zorder=5,
        )

        axes_item.set_xlim(x_min - x_padding_support, x_max + x_padding_support)
        axes_item.set_ylim(plot_y_lower, plot_y_upper)
        axes_item.set_xlabel(
            str(panel["x_label"]),
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
        axes_item.tick_params(axis="both", labelsize=tick_size, colors="#334155")
        axes_item.grid(axis="y", linestyle=":", color="#e6edf2", linewidth=0.65, zorder=0)
        _apply_publication_axes_style(axes_item)

        support_records.append(
            {
                "axes": axes_item,
                "panel": panel,
                "curve_x": curve_x,
                "curve_y": curve_y,
                "x_span": x_span,
                "panel_title_artist": axes_item.title,
                "reference_label_artist": reference_label_artist,
                "support_label_artists": support_label_artists,
            }
        )

    top_margin = 0.82 if show_figure_title else 0.91
    top_margin = max(0.76, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.26, right=0.97, top=top_margin, bottom=0.17)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    support_bboxes = [record["axes"].get_window_extent(renderer=renderer) for record in support_records]
    support_row_center_y = 0.34
    if support_bboxes:
        support_row_center_y = fig.transFigure.inverted().transform(
            (0.0, (min(item.y0 for item in support_bboxes) + max(item.y1 for item in support_bboxes)) / 2.0)
        )[1]
    support_y_axis_title_artist = fig.text(
        0.045,
        support_row_center_y,
        str(display_payload.get("support_y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
        ha="center",
        va="center",
    )

    legend = fig.legend(
        handles=[
            matplotlib.lines.Line2D(
                [],
                [],
                color=curve_color,
                linewidth=2.4,
                marker="o",
                markersize=5.2,
                markerfacecolor="white",
                label="Response curve",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["observed_support"]["facecolor"],
                edgecolor=support_style_map["observed_support"]["edgecolor"],
                label="Observed support",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["subgroup_support"]["facecolor"],
                edgecolor=support_style_map["subgroup_support"]["edgecolor"],
                label="Subgroup support",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["bin_support"]["facecolor"],
                edgecolor=support_style_map["bin_support"]["edgecolor"],
                label="Bin support",
            ),
            matplotlib.patches.Patch(
                facecolor=support_style_map["extrapolation_warning"]["facecolor"],
                edgecolor=support_style_map["extrapolation_warning"]["edgecolor"],
                label="Extrapolation reminder",
            ),
        ],
        loc="lower center",
        bbox_to_anchor=(0.58, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        handlelength=2.0,
        columnspacing=1.3,
        title=str(display_payload.get("support_legend_title") or "").strip(),
    )

    def _add_panel_label(*, axes_item: Any, label: str, left_of_panel: bool) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, _ = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y1))[1] - fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))[1])
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.018, 0.006), 0.013)
        x_anchor = panel_x0 + (x_padding * 0.55 if left_of_panel else x_padding)
        return fig.text(
            x_anchor,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.5, 13.0),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    local_panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]), left_of_panel=True)
        for record in local_records
    ]
    support_panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]), left_of_panel=False)
        for record in support_records
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
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=support_y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="support_y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_window_extent(renderer=renderer),
                box_id="support_legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=legend.get_title().get_window_extent(renderer=renderer),
                box_id="support_legend_title",
                box_type="legend_title",
            ),
        ]
    )

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    layout_metrics_local_panels: list[dict[str, Any]] = []
    layout_metrics_support_panels: list[dict[str, Any]] = []
    zero_line_half_width = max((x_limit * 2.0) * 0.004, 0.01)

    for record, panel_label_artist in zip(local_records, local_panel_label_artists, strict=True):
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
        layout_metrics_local_panels.append(
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

    for record, panel_label_artist in zip(support_records, support_panel_label_artists, strict=True):
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
                    bbox=record["reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"reference_label_{panel_token}",
                    box_type="support_domain_reference_label",
                ),
            ]
        )

        normalized_response_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(record["curve_x"], record["curve_y"], strict=True):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            normalized_response_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_support_segments: list[dict[str, Any]] = []
        for segment_index, (segment, label_artist) in enumerate(
            zip(panel["support_segments"], record["support_label_artists"], strict=True),
            start=1,
        ):
            segment_box_id = f"support_segment_{panel_token}_{segment_index}"
            label_box_id = f"support_label_{panel_token}_{segment_index}"
            segment_box = _data_box_to_layout_box(
                axes=axes_item,
                figure=fig,
                x0=float(segment["domain_start"]),
                y0=band_y0,
                x1=float(segment["domain_end"]),
                y1=band_y1,
                box_id=segment_box_id,
                box_type="support_domain_segment",
            )
            guide_boxes.append(segment_box)
            layout_boxes.append(
                _bbox_to_layout_box(
                    figure=fig,
                    bbox=label_artist.get_window_extent(renderer=renderer),
                    box_id=label_box_id,
                    box_type="support_label",
                )
            )
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
                "local_shared_feature_order": list(display_payload.get("local_shared_feature_order") or []),
                "local_panels": layout_metrics_local_panels,
                "support_panels": layout_metrics_support_panels,
                "support_legend_labels": legend_labels,
                "support_legend_title": str(display_payload.get("support_legend_title") or "").strip(),
                "support_legend_title_box_id": "support_legend_title",
                "support_y_axis_title_box_id": "support_y_axis_title",
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
