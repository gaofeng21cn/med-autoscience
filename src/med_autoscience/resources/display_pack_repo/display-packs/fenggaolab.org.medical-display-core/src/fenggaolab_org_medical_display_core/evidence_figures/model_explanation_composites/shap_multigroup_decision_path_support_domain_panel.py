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

def _render_python_shap_multigroup_decision_path_support_domain_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    groups = list(display_payload.get("groups") or [])
    support_panels = list(display_payload.get("support_panels") or [])
    if len(groups) != 3:
        raise RuntimeError(f"{template_id} requires exactly three groups")
    if len(support_panels) != 2:
        raise RuntimeError(f"{template_id} requires exactly two support panels")

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

    group_colors = [
        _require_non_empty_string(
            style_roles.get("model_curve"),
            label=f"{template_id} render_context.style_roles.model_curve",
        ),
        _require_non_empty_string(
            style_roles.get("comparator_curve"),
            label=f"{template_id} render_context.style_roles.comparator_curve",
        ),
        str(palette.get("contrast") or palette.get("secondary") or "#2F5D8A").strip() or "#2F5D8A",
    ]
    baseline_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    curve_color = group_colors[0]
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    feature_order = list(display_payload.get("feature_order") or [])
    if not feature_order:
        feature_order = [str(item["feature"]) for item in groups[0]["contributions"]]
    baseline_value = float(display_payload["baseline_value"])
    all_values = [baseline_value]
    for group in groups:
        all_values.append(float(group["predicted_value"]))
        for contribution in group["contributions"]:
            all_values.extend((float(contribution["start_value"]), float(contribution["end_value"])))

    x_min = min(all_values)
    x_max = max(all_values)
    x_span = max(x_max - x_min, 1e-6)
    x_padding = max(x_span * 0.18, 0.05)
    x_lower = x_min - x_padding
    x_upper = x_max + x_padding
    y_start = -0.55
    row_positions = list(range(len(feature_order)))
    y_lower = row_positions[-1] + 0.55
    y_upper = y_start - 0.25

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
    support_legend_labels = [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]

    all_curve_y = [
        float(value)
        for panel in support_panels
        for value in panel["response_curve"]["y"]
    ]
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
    figure_height = max(7.2, 5.8 + 0.35 * len(feature_order))
    fig = plt.figure(figsize=(10.8, figure_height))
    fig.patch.set_facecolor("white")
    root_grid = fig.add_gridspec(2, 1, height_ratios=[3.0, 2.4], hspace=0.44)
    decision_ax = fig.add_subplot(root_grid[0, 0])
    support_grid = root_grid[1, 0].subgridspec(1, len(support_panels), wspace=0.34)
    support_axes = [fig.add_subplot(support_grid[0, index]) for index in range(len(support_panels))]

    title_artist = None
    title_line_count = 0
    if show_figure_title:
        wrapped_title, title_line_count = _wrap_figure_title_to_width(
            str(display_payload.get("title") or "").strip(),
            max_width_pt=fig.get_figwidth() * 72.0 * 0.84,
            font_size=title_size,
        )
        title_artist = fig.suptitle(
            wrapped_title,
            fontsize=title_size,
            fontweight="bold",
            color="#13293d",
            y=0.985,
        )

    decision_ax.set_xlim(x_lower, x_upper)
    decision_ax.set_ylim(y_lower, y_upper)
    decision_ax.set_yticks(row_positions)
    decision_ax.set_yticklabels(feature_order, fontsize=max(tick_size - 0.2, 8.6))
    decision_ax.set_xlabel(
        str(display_payload.get("decision_x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    decision_ax.set_ylabel(
        str(display_payload.get("decision_y_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    decision_ax.set_title(
        str(display_payload.get("decision_panel_title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=10.0,
    )
    decision_ax.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    decision_ax.tick_params(axis="y", length=0, pad=8, colors="#2F3437")
    decision_ax.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
    decision_ax.grid(axis="y", visible=False)
    _apply_publication_axes_style(decision_ax)
    decision_ax.axvline(baseline_value, color=baseline_color, linewidth=1.1, linestyle="--", zorder=1)

    line_records: list[dict[str, Any]] = []
    legend_handles: list[Any] = []
    label_padding = max(x_span * 0.04, 0.03)
    for group, color in zip(groups, group_colors, strict=True):
        x_values = [baseline_value] + [float(item["end_value"]) for item in group["contributions"]]
        y_values = [y_start] + row_positions
        line_artist = decision_ax.plot(
            x_values,
            y_values,
            color=color,
            linewidth=2.1,
            marker="o",
            markersize=4.8,
            markeredgecolor="white",
            markeredgewidth=0.6,
            zorder=3,
        )[0]
        prediction_x = x_values[-1]
        prediction_y = y_values[-1]
        prediction_marker_artist = decision_ax.scatter(
            [prediction_x],
            [prediction_y],
            s=42,
            color=color,
            edgecolors="white",
            linewidths=0.7,
            zorder=4,
        )
        if prediction_x >= baseline_value:
            label_x = min(x_upper - label_padding * 0.3, prediction_x + label_padding)
            ha = "left"
        else:
            label_x = max(x_lower + label_padding * 0.3, prediction_x - label_padding)
            ha = "right"
        prediction_label_artist = decision_ax.text(
            label_x,
            prediction_y,
            f"{float(group['predicted_value']):.2f}",
            fontsize=max(tick_size - 0.6, 8.2),
            color="#334155",
            ha=ha,
            va="center",
            zorder=4,
        )
        legend_handles.append(
            matplotlib.lines.Line2D(
                [0],
                [0],
                color=color,
                linewidth=2.1,
                marker="o",
                markersize=5.0,
                markeredgecolor="white",
                markeredgewidth=0.6,
                label=str(group["group_label"]),
            )
        )
        line_records.append(
            {
                "group": group,
                "line_artist": line_artist,
                "prediction_marker_artist": prediction_marker_artist,
                "prediction_label_artist": prediction_label_artist,
            }
        )

    for axes_item, panel in zip(support_axes, support_panels, strict=True):
        curve_x = [float(value) for value in panel["response_curve"]["x"]]
        curve_y = [float(value) for value in panel["response_curve"]["y"]]
        x_min_panel = min(curve_x)
        x_max_panel = max(curve_x)
        x_span_panel = max(x_max_panel - x_min_panel, 1e-6)
        x_padding_panel = max(x_span_panel * 0.10, 0.04)
        support_label_artists: list[Any] = []

        for segment_index, segment in enumerate(panel["support_segments"], start=1):
            style = support_style_map[str(segment["support_kind"])]
            segment_start = float(segment["domain_start"])
            segment_end = float(segment["domain_end"])
            axes_item.axvspan(
                segment_start,
                segment_end,
                ymin=0.0,
                ymax=(band_y1 - plot_y_lower) / (plot_y_upper - plot_y_lower),
                facecolor=style["facecolor"],
                edgecolor=style["edgecolor"],
                linewidth=0.8,
                zorder=1,
            )
            segment_label = str(segment["segment_label"])
            label_y = band_y1 + support_band_height * 0.28 if segment_index % 2 == 1 else band_y0 + support_band_height * 0.24
            label_font_size = max(tick_size - (2.0 if len(segment_label) > 8 else 1.1), 6.6)
            support_label_artists.append(
                axes_item.text(
                    (segment_start + segment_end) / 2.0,
                    label_y,
                    segment_label,
                    fontsize=label_font_size,
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
            color=baseline_color,
            linewidth=1.0,
            linestyle="--",
            zorder=2,
        )
        reference_label_artist = axes_item.text(
            reference_value,
            plot_y_upper - curve_y_padding * 0.35,
            str(panel["reference_label"]),
            fontsize=max(tick_size - 1.0, 8.0),
            color=baseline_color,
            ha="center",
            va="top",
            zorder=5,
        )

        axes_item.set_xlim(x_min_panel - x_padding_panel, x_max_panel + x_padding_panel)
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
        panel["__curve_x"] = curve_x
        panel["__curve_y"] = curve_y
        panel["__reference_label_artist"] = reference_label_artist
        panel["__x_span"] = x_span_panel
        panel["__support_label_artists"] = support_label_artists

    top_margin = 0.90 if show_figure_title else 0.94
    top_margin = max(0.78, top_margin - 0.04 * max(title_line_count - 1, 0))
    fig.subplots_adjust(left=0.23, right=0.72, top=top_margin, bottom=0.15)

    decision_legend = fig.legend(
        handles=legend_handles,
        title=str(display_payload.get("decision_legend_title") or "").strip(),
        loc="center left",
        bbox_to_anchor=(0.74, 0.78),
        bbox_transform=fig.transFigure,
        frameon=True,
        framealpha=1.0,
        edgecolor="#d7dee7",
        fontsize=max(tick_size - 0.5, 8.2),
        title_fontsize=max(tick_size - 0.1, 8.6),
    )
    decision_legend.get_frame().set_facecolor("white")
    fig.add_artist(decision_legend)

    support_y_axis_title_artist = fig.text(
        0.045,
        0.25,
        str(display_payload.get("support_y_label") or "").strip(),
        rotation=90,
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
        ha="center",
        va="center",
    )
    support_legend = fig.legend(
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
        title=str(display_payload.get("support_legend_title") or "").strip(),
        loc="lower center",
        bbox_to_anchor=(0.46, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        title_fontsize=max(tick_size - 0.2, 8.6),
        handlelength=2.0,
        columnspacing=1.3,
    )
    fig.add_artist(support_legend)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def _add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.015, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.028, 0.009), 0.017)
        return fig.text(
            panel_x0 + x_padding,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.4, 13.0),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    support_panel_label_artists = [
        _add_panel_label(axes_item=axes_item, label=str(panel["panel_label"]))
        for axes_item, panel in zip(support_axes, support_panels, strict=True)
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

    decision_panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=decision_ax.get_window_extent(renderer=renderer),
        box_id="panel_decision_path",
        box_type="panel",
    )
    panel_boxes = [decision_panel_box]
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=decision_ax.title.get_window_extent(renderer=renderer),
                box_id="panel_title",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=decision_ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title",
                box_type="subplot_x_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=decision_ax.yaxis.label.get_window_extent(renderer=renderer),
                box_id="y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=decision_legend.get_window_extent(renderer=renderer),
                box_id="legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=decision_legend.get_title().get_window_extent(renderer=renderer),
                box_id="legend_title",
                box_type="legend_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=support_y_axis_title_artist.get_window_extent(renderer=renderer),
                box_id="support_y_axis_title",
                box_type="subplot_y_axis_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=support_legend.get_window_extent(renderer=renderer),
                box_id="support_legend_box",
                box_type="legend_box",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=support_legend.get_title().get_window_extent(renderer=renderer),
                box_id="support_legend_title",
                box_type="legend_title",
            ),
        ]
    )

    feature_label_box_ids: list[str] = []
    for index, tick_label in enumerate(decision_ax.get_yticklabels(), start=1):
        if not str(tick_label.get_text() or "").strip():
            continue
        box_id = f"feature_label_{index}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=tick_label.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="feature_label",
            )
        )
        feature_label_box_ids.append(box_id)

    line_half_width = max((x_upper - x_lower) * 0.004, 0.003)
    marker_half_width = max((x_upper - x_lower) * 0.007, 0.004)
    marker_half_height = 0.10
    guide_boxes: list[dict[str, Any]] = [
        _data_box_to_layout_box(
            axes=decision_ax,
            figure=fig,
            x0=baseline_value - line_half_width,
            y0=y_start,
            x1=baseline_value + line_half_width,
            y1=row_positions[-1],
            box_id="baseline_reference_line",
            box_type="baseline_reference_line",
        )
    ]

    decision_metrics_groups: list[dict[str, Any]] = []
    for record in line_records:
        group = record["group"]
        group_token = re.sub(r"[^A-Za-z0-9]+", "_", str(group["group_id"])) or "group"
        line_box_id = f"decision_path_line_{group_token}"
        prediction_marker_box_id = f"prediction_marker_{group_token}"
        prediction_label_box_id = f"prediction_label_{group_token}"
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["line_artist"].get_window_extent(renderer=renderer),
                box_id=line_box_id,
                box_type="decision_path_line",
            )
        )
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=record["prediction_label_artist"].get_window_extent(renderer=renderer),
                box_id=prediction_label_box_id,
                box_type="prediction_label",
            )
        )
        prediction_x = float(group["contributions"][-1]["end_value"])
        prediction_y = row_positions[-1]
        guide_boxes.append(
            _data_box_to_layout_box(
                axes=decision_ax,
                figure=fig,
                x0=prediction_x - marker_half_width,
                y0=prediction_y - marker_half_height,
                x1=prediction_x + marker_half_width,
                y1=prediction_y + marker_half_height,
                box_id=prediction_marker_box_id,
                box_type="prediction_marker",
            )
        )
        decision_metrics_groups.append(
            {
                "group_id": str(group["group_id"]),
                "group_label": str(group["group_label"]),
                "predicted_value": float(group["predicted_value"]),
                "line_box_id": line_box_id,
                "prediction_marker_box_id": prediction_marker_box_id,
                "prediction_label_box_id": prediction_label_box_id,
                "contributions": [
                    {
                        "rank": int(item["rank"]),
                        "feature": str(item["feature"]),
                        "shap_value": float(item["shap_value"]),
                        "start_value": float(item["start_value"]),
                        "end_value": float(item["end_value"]),
                    }
                    for item in group["contributions"]
                ],
            }
        )

    support_metrics_panels: list[dict[str, Any]] = []
    for axes_item, panel, panel_label_artist in zip(support_axes, support_panels, support_panel_label_artists, strict=True):
        panel_token = str(panel["panel_label"])
        panel_box_id = f"panel_{panel_token}"
        panel_box = _bbox_to_layout_box(
            figure=fig,
            bbox=axes_item.get_window_extent(renderer=renderer),
            box_id=panel_box_id,
            box_type="panel",
        )
        panel_boxes.append(panel_box)

        reference_line_box_id = f"reference_line_{panel_token}"
        reference_half_width = max(float(panel["__x_span"]) * 0.003, 0.0015)
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
                    bbox=axes_item.title.get_window_extent(renderer=renderer),
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
                    bbox=panel["__reference_label_artist"].get_window_extent(renderer=renderer),
                    box_id=f"reference_label_{panel_token}",
                    box_type="support_domain_reference_label",
                ),
            ]
        )

        response_points: list[dict[str, Any]] = []
        for feature_value, response_value in zip(panel["__curve_x"], panel["__curve_y"], strict=True):
            point_x, point_y = _data_point_to_figure_xy(
                axes=axes_item,
                figure=fig,
                x=float(feature_value),
                y=float(response_value),
            )
            response_points.append(
                {
                    "feature_value": float(feature_value),
                    "response_value": float(response_value),
                    "x": point_x,
                    "y": point_y,
                }
            )

        normalized_support_segments: list[dict[str, Any]] = []
        for segment_index, (segment, label_artist) in enumerate(
            zip(panel["support_segments"], panel["__support_label_artists"], strict=True),
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

        support_metrics_panels.append(
            {
                "panel_id": str(panel["panel_id"]),
                "panel_label": panel_token,
                "title": str(panel["title"]),
                "x_label": str(panel["x_label"]),
                "feature": str(panel["feature"]),
                "reference_value": float(panel["reference_value"]),
                "reference_label": str(panel["reference_label"]),
                "panel_box_id": panel_box_id,
                "reference_line_box_id": reference_line_box_id,
                "reference_label_box_id": f"reference_label_{panel_token}",
                "response_points": response_points,
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
                "decision_panel": {
                    "panel_box_id": "panel_decision_path",
                    "baseline_line_box_id": "baseline_reference_line",
                    "baseline_value": baseline_value,
                    "legend_title": str(display_payload.get("decision_legend_title") or "").strip(),
                    "feature_order": [str(item) for item in feature_order],
                    "feature_label_box_ids": feature_label_box_ids,
                    "groups": decision_metrics_groups,
                },
                "support_y_label": str(display_payload.get("support_y_label") or "").strip(),
                "support_legend_title": str(display_payload.get("support_legend_title") or "").strip(),
                "support_legend_labels": support_legend_labels,
                "support_y_axis_title_box_id": "support_y_axis_title",
                "support_legend_title_box_id": "support_legend_title",
                "support_panels": support_metrics_panels,
            },
        },
    )
    fig.savefig(output_png_path, format="png", dpi=320)
    fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)

