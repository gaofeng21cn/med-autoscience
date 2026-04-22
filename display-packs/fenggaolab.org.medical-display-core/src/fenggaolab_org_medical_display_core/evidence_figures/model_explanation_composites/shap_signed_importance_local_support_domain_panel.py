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

def _render_python_shap_signed_importance_local_support_domain_panel(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> None:
    importance_panel = dict(display_payload.get("importance_panel") or {})
    local_panel = dict(display_payload.get("local_panel") or {})
    support_panels = list(display_payload.get("support_panels") or [])
    if not importance_panel or not local_panel or len(support_panels) != 2:
        raise RuntimeError(
            f"{template_id} requires one importance_panel, one local_panel, and exactly two support_panels"
        )

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
    reference_color = _require_non_empty_string(
        style_roles.get("reference_line"),
        label=f"{template_id} render_context.style_roles.reference_line",
    )
    curve_color = negative_color
    title_size = float(typography.get("title_size") or 12.5)
    axis_title_size = float(typography.get("axis_title_size") or 11.0)
    tick_size = float(typography.get("tick_size") or 10.0)
    panel_label_size = max(12.0, float(typography.get("panel_label_size") or 11.0))
    marker_size = max(4.0, float(stroke.get("marker_size") or 4.5))
    show_figure_title = _read_bool_override(layout_override, "show_figure_title", False)

    normalized_importance_bars = [
        {
            "rank": int(item["rank"]),
            "feature": str(item["feature"]),
            "signed_importance_value": float(item["signed_importance_value"]),
        }
        for item in list(importance_panel.get("bars") or [])
    ]
    if not normalized_importance_bars:
        raise RuntimeError(f"{template_id} importance_panel requires non-empty bars")

    raw_local_contributions = list(local_panel.get("contributions") or [])
    normalized_local_contributions: list[dict[str, Any]] = []
    local_running_value = float(local_panel["baseline_value"])
    for contribution_index, item in enumerate(raw_local_contributions):
        shap_value = float(item["shap_value"])
        start_value = local_running_value
        end_value = local_running_value + shap_value
        if contribution_index == len(raw_local_contributions) - 1:
            end_value = float(local_panel["predicted_value"])
        normalized_local_contributions.append(
            {
                "feature": str(item["feature"]),
                "feature_value_text": str(item.get("feature_value_text") or "").strip(),
                "shap_value": shap_value,
                "start_value": start_value,
                "end_value": end_value,
            }
        )
        local_running_value = end_value
    if not normalized_local_contributions:
        raise RuntimeError(f"{template_id} local_panel requires non-empty contributions")

    all_local_values = [float(local_panel["baseline_value"]), float(local_panel["predicted_value"])]
    for contribution in normalized_local_contributions:
        all_local_values.extend((float(contribution["start_value"]), float(contribution["end_value"])))
    local_x_min = min(all_local_values)
    local_x_max = max(all_local_values)
    local_x_span = max(local_x_max - local_x_min, 1e-6)
    local_x_padding = max(local_x_span * 0.12, 0.05)
    local_x_lower = local_x_min - local_x_padding
    local_x_upper = local_x_max + local_x_padding
    local_marker_half_width = max(local_x_span * 0.004, 0.0025)

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

    importance_values = [float(item["signed_importance_value"]) for item in normalized_importance_bars]
    importance_max_abs_value = max(abs(value) for value in importance_values)
    importance_padding = max(importance_max_abs_value * 0.18, 0.02)
    importance_core_limit = importance_max_abs_value + importance_padding
    importance_label_padding = max(importance_core_limit * 0.03, 0.018)
    importance_axis_limit = importance_core_limit + importance_label_padding * 3.2
    importance_zero_line_half_width = max(importance_core_limit * 0.008, 0.0025)

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
    support_legend_labels = list(display_payload.get("support_legend_labels") or []) or [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]

    importance_panel_height = max(4.9, 0.58 * len(normalized_importance_bars) + 1.8)
    local_panel_height = max(4.9, 0.62 * len(normalized_local_contributions) + 2.0)
    top_row_height = max(importance_panel_height, local_panel_height)
    support_row_height = 3.9
    figure_height = top_row_height + support_row_height + 1.2
    figure_width = 11.8

    fig = plt.figure(figsize=(figure_width, figure_height))
    fig.patch.set_facecolor("white")
    root_grid = fig.add_gridspec(2, 2, height_ratios=[top_row_height, support_row_height], hspace=0.48, wspace=0.34)
    importance_ax = fig.add_subplot(root_grid[0, 0])
    local_ax = fig.add_subplot(root_grid[0, 1])
    support_axes = [
        fig.add_subplot(root_grid[1, 0]),
        fig.add_subplot(root_grid[1, 1]),
    ]

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

    importance_row_positions = list(range(len(normalized_importance_bars)))
    importance_bar_artists: list[Any] = []
    importance_value_label_artists: list[Any] = []
    for row_position, item in zip(importance_row_positions, normalized_importance_bars, strict=True):
        signed_value = float(item["signed_importance_value"])
        color = positive_color if signed_value > 0.0 else negative_color
        importance_bar_artists.append(
            importance_ax.barh(
                row_position,
                signed_value,
                height=0.58,
                color=matplotlib.colors.to_rgba(color, alpha=0.92),
                edgecolor=color,
                linewidth=0.9,
                zorder=3,
            )[0]
        )
        importance_value_label_artists.append(
            importance_ax.text(
                signed_value + (importance_label_padding if signed_value > 0.0 else -importance_label_padding),
                row_position,
                f"{signed_value:+.3f}",
                fontsize=max(tick_size - 0.6, 8.4),
                color="#334155",
                va="center",
                ha="left" if signed_value > 0.0 else "right",
            )
        )

    importance_ax.axvline(0.0, color=reference_color, linewidth=1.1, linestyle="--", zorder=1)
    importance_ax.set_xlim(-importance_axis_limit, importance_axis_limit)
    importance_ax.set_ylim(-0.6, len(normalized_importance_bars) - 0.4)
    importance_ax.set_yticks(importance_row_positions)
    importance_ax.set_yticklabels(
        [str(item["feature"]) for item in normalized_importance_bars],
        fontsize=max(tick_size - 0.3, 8.6),
    )
    importance_ax.invert_yaxis()
    importance_ax.set_xlabel(
        str(importance_panel.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    importance_ax.set_title(
        str(importance_panel.get("title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=18.0,
    )
    importance_ax.tick_params(axis="x", labelsize=tick_size)
    importance_ax.tick_params(axis="y", length=0, pad=8)
    importance_ax.grid(axis="x", color="#e6edf2", linewidth=0.45, linestyle=":")
    _apply_publication_axes_style(importance_ax)

    negative_direction_artist = importance_ax.text(
        0.18,
        1.03,
        str(importance_panel.get("negative_label") or "").strip(),
        transform=importance_ax.transAxes,
        fontsize=max(tick_size - 0.3, 8.8),
        color=negative_color,
        fontweight="bold",
        ha="center",
        va="bottom",
    )
    positive_direction_artist = importance_ax.text(
        0.82,
        1.03,
        str(importance_panel.get("positive_label") or "").strip(),
        transform=importance_ax.transAxes,
        fontsize=max(tick_size - 0.3, 8.8),
        color=positive_color,
        fontweight="bold",
        ha="center",
        va="bottom",
    )

    local_feature_labels = [
        (
            f"{item['feature']} = {item['feature_value_text']}"
            if item["feature_value_text"]
            else str(item["feature"])
        )
        for item in normalized_local_contributions
    ]
    local_bar_artists: list[Any] = []
    local_value_label_artists: list[Any] = []
    for row_index, contribution in enumerate(normalized_local_contributions):
        start_value = float(contribution["start_value"])
        end_value = float(contribution["end_value"])
        shap_value = float(contribution["shap_value"])
        left_value = min(start_value, end_value)
        bar_width = abs(end_value - start_value)
        local_bar_artists.append(
            local_ax.barh(
                row_index,
                bar_width,
                left=left_value,
                height=0.6,
                color=matplotlib.colors.to_rgba(positive_color if shap_value > 0.0 else negative_color, alpha=0.92),
                edgecolor=positive_color if shap_value > 0.0 else negative_color,
                linewidth=0.95,
                zorder=3,
            )[0]
        )
        local_value_label_artists.append(
            local_ax.annotate(
                f"{shap_value:+.2f}",
                xy=(end_value, row_index),
                xytext=(6 if shap_value > 0.0 else -6, 0),
                textcoords="offset points",
                ha="left" if shap_value > 0.0 else "right",
                va="center",
                fontsize=max(tick_size - 0.7, 8.2),
                color="#13293d",
            )
        )

    local_ax.axvline(float(local_panel["baseline_value"]), color=reference_color, linewidth=1.0, linestyle="--", zorder=1)
    local_ax.axvline(float(local_panel["predicted_value"]), color="#13293d", linewidth=1.1, linestyle="-", zorder=1)
    local_ax.set_xlim(local_x_lower, local_x_upper)
    local_ax.set_ylim(-1.1, len(normalized_local_contributions) - 0.4)
    local_ax.set_yticks(list(range(len(normalized_local_contributions))))
    local_ax.set_yticklabels(local_feature_labels, fontsize=max(tick_size - 0.6, 8.4))
    local_ax.invert_yaxis()
    local_ax.set_xlabel(
        str(local_panel.get("x_label") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#13293d",
    )
    local_ax.set_title(
        str(local_panel.get("title") or "").strip(),
        fontsize=axis_title_size,
        fontweight="bold",
        color="#334155",
        pad=10.0,
    )
    local_ax.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    local_ax.tick_params(axis="y", length=0, pad=6)
    local_ax.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
    _apply_publication_axes_style(local_ax)

    case_label_artist = local_ax.text(
        0.16,
        0.965,
        str(local_panel.get("case_label") or "").strip(),
        transform=local_ax.transAxes,
        fontsize=max(tick_size - 0.4, 8.8),
        color="#475569",
        ha="left",
        va="top",
    )
    baseline_label_artist = local_ax.text(
        0.02,
        0.885,
        f"Baseline {float(local_panel['baseline_value']):.2f}",
        transform=local_ax.transAxes,
        fontsize=max(tick_size - 0.6, 8.2),
        color="#475569",
        ha="left",
        va="top",
    )
    prediction_label_artist = local_ax.text(
        0.98,
        0.885,
        f"Prediction {float(local_panel['predicted_value']):.2f}",
        transform=local_ax.transAxes,
        fontsize=max(tick_size - 0.6, 8.2),
        color="#13293d",
        ha="right",
        va="top",
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
        for segment_index, segment in enumerate(panel["support_segments"], start=1):
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
        axes_item.axvline(reference_value, color=reference_color, linewidth=1.0, linestyle="--", zorder=2)
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
    fig.subplots_adjust(left=0.28, right=0.97, top=top_margin, bottom=0.17)
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
        loc="lower center",
        bbox_to_anchor=(0.58, 0.02),
        ncol=3,
        frameon=False,
        fontsize=max(tick_size - 0.8, 8.2),
        handlelength=2.0,
        columnspacing=1.3,
        title=str(display_payload.get("support_legend_title") or "").strip(),
    )

    def _add_panel_label(*, axes_item: Any, label: str, inset_ratio: float = 1.0) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        x_padding = min(max(panel_width * 0.012, 0.006), 0.014)
        y_padding = min(max(panel_height * 0.022, 0.007), 0.015)
        return fig.text(
            panel_x0 + x_padding * inset_ratio,
            panel_y1 - y_padding,
            label,
            transform=fig.transFigure,
            fontsize=max(panel_label_size + 1.5, 13.0),
            fontweight="bold",
            color="#2F3437",
            ha="left",
            va="top",
        )

    importance_panel_label_artist = _add_panel_label(
        axes_item=importance_ax,
        label=str(importance_panel.get("panel_label") or "").strip(),
        inset_ratio=0.85,
    )
    local_panel_label_artist = _add_panel_label(
        axes_item=local_ax,
        label=str(local_panel.get("panel_label") or "").strip(),
        inset_ratio=0.85,
    )
    support_panel_label_artists = [
        _add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]), inset_ratio=1.0)
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

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []

    importance_panel_token = re.sub(r"[^A-Za-z0-9]+", "_", str(importance_panel["panel_label"])) or "A"
    importance_panel_box_id = f"panel_{importance_panel_token}"
    importance_panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=importance_ax.get_window_extent(renderer=renderer),
        box_id=importance_panel_box_id,
        box_type="panel",
    )
    panel_boxes.append(importance_panel_box)
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=importance_ax.title.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{importance_panel_token}",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=importance_panel_label_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{importance_panel_token}",
                box_type="panel_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=negative_direction_artist.get_window_extent(renderer=renderer),
                box_id="negative_direction_label",
                box_type="negative_direction_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=positive_direction_artist.get_window_extent(renderer=renderer),
                box_id="positive_direction_label",
                box_type="positive_direction_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=importance_ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id="x_axis_title",
                box_type="x_axis_title",
            ),
        ]
    )

    importance_feature_label_ids: list[str] = []
    importance_bar_ids: list[str] = []
    importance_value_label_ids: list[str] = []
    for index, tick_label in enumerate(importance_ax.get_yticklabels(), start=1):
        box_id = f"feature_label_{index}"
        importance_feature_label_ids.append(box_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=tick_label.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="feature_label",
            )
        )
    for index, artist in enumerate(importance_bar_artists, start=1):
        box_id = f"importance_bar_{index}"
        importance_bar_ids.append(box_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="importance_bar",
            )
        )
    for index, label_artist in enumerate(importance_value_label_artists, start=1):
        box_id = f"value_label_{index}"
        importance_value_label_ids.append(box_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=label_artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="value_label",
            )
        )
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
    local_panel_box = _bbox_to_layout_box(
        figure=fig,
        bbox=local_ax.get_window_extent(renderer=renderer),
        box_id=local_panel_box_id,
        box_type="panel",
    )
    panel_boxes.append(local_panel_box)
    layout_boxes.extend(
        [
            _bbox_to_layout_box(
                figure=fig,
                bbox=local_ax.title.get_window_extent(renderer=renderer),
                box_id=f"panel_title_{local_panel_token}",
                box_type="panel_title",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=local_panel_label_artist.get_window_extent(renderer=renderer),
                box_id=f"panel_label_{local_panel_token}",
                box_type="panel_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=case_label_artist.get_window_extent(renderer=renderer),
                box_id=f"case_label_{local_panel_token}",
                box_type="case_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=baseline_label_artist.get_window_extent(renderer=renderer),
                box_id=f"baseline_label_{local_panel_token}",
                box_type="baseline_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=prediction_label_artist.get_window_extent(renderer=renderer),
                box_id=f"prediction_label_{local_panel_token}",
                box_type="prediction_label",
            ),
            _bbox_to_layout_box(
                figure=fig,
                bbox=local_ax.xaxis.label.get_window_extent(renderer=renderer),
                box_id=f"x_axis_title_{local_panel_token}",
                box_type="subplot_x_axis_title",
            ),
        ]
    )

    local_feature_label_ids: list[str] = []
    local_contribution_metrics: list[dict[str, Any]] = []
    for index, tick_label in enumerate(local_ax.get_yticklabels(), start=1):
        if not str(tick_label.get_text() or "").strip():
            continue
        box_id = f"feature_label_{local_panel_token}_{index}"
        local_feature_label_ids.append(box_id)
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=tick_label.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="feature_label",
            )
        )
    for contribution_index, (contribution, bar_artist, value_label_artist) in enumerate(
        zip(normalized_local_contributions, local_bar_artists, local_value_label_artists, strict=True),
        start=1,
    ):
        bar_box_id = f"contribution_bar_{local_panel_token}_{contribution_index}"
        value_label_box_id = f"contribution_label_{local_panel_token}_{contribution_index}"
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
                box_type="contribution_label",
            )
        )
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
    guide_boxes.append(
        _data_box_to_layout_box(
            axes=local_ax,
            figure=fig,
            x0=float(local_panel["baseline_value"]) - local_marker_half_width,
            y0=-0.95,
            x1=float(local_panel["baseline_value"]) + local_marker_half_width,
            y1=len(normalized_local_contributions) - 0.45,
            box_id=local_baseline_marker_box_id,
            box_type="baseline_marker",
        )
    )
    guide_boxes.append(
        _data_box_to_layout_box(
            axes=local_ax,
            figure=fig,
            x0=float(local_panel["predicted_value"]) - local_marker_half_width,
            y0=-0.95,
            x1=float(local_panel["predicted_value"]) + local_marker_half_width,
            y1=len(normalized_local_contributions) - 0.45,
            box_id=local_prediction_marker_box_id,
            box_type="prediction_marker",
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

    layout_metrics_support_panels: list[dict[str, Any]] = []
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
            guide_boxes.append(
                _data_box_to_layout_box(
                    axes=axes_item,
                    figure=fig,
                    x0=float(segment["domain_start"]),
                    y0=band_y0,
                    x1=float(segment["domain_end"]),
                    y1=band_y1,
                    box_id=segment_box_id,
                    box_type="support_domain_segment",
                )
            )
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

