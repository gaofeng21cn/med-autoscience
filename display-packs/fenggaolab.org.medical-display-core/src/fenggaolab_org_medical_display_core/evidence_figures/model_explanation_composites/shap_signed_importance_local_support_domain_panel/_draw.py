from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from ....shared import _apply_publication_axes_style, _wrap_figure_title_to_width


def _build_shap_signed_importance_local_support_domain_figure(
    *,
    display_payload: dict[str, Any],
    data: dict[str, Any],
) -> dict[str, Any]:
    importance_panel = data["importance_panel"]
    local_panel = data["local_panel"]
    normalized_importance_bars = data["normalized_importance_bars"]
    normalized_local_contributions = data["normalized_local_contributions"]
    normalized_support_panels = data["normalized_support_panels"]
    negative_color = data["negative_color"]
    positive_color = data["positive_color"]
    reference_color = data["reference_color"]
    curve_color = data["curve_color"]
    title_size = data["title_size"]
    axis_title_size = data["axis_title_size"]
    tick_size = data["tick_size"]
    panel_label_size = data["panel_label_size"]
    marker_size = data["marker_size"]
    show_figure_title = data["show_figure_title"]
    importance_axis_limit = data["importance_axis_limit"]
    local_x_lower = data["local_x_lower"]
    local_x_upper = data["local_x_upper"]
    plot_y_lower = data["plot_y_lower"]
    plot_y_upper = data["plot_y_upper"]
    support_style_map = data["support_style_map"]
    figure_height = data["figure_height"]
    figure_width = data["figure_width"]

    fig = plt.figure(figsize=(figure_width, figure_height))
    fig.patch.set_facecolor("white")
    root_grid = fig.add_gridspec(
        2,
        2,
        height_ratios=[data["top_row_height"], data["support_row_height"]],
        hspace=0.48,
        wspace=0.34,
    )
    importance_ax = fig.add_subplot(root_grid[0, 0])
    local_ax = fig.add_subplot(root_grid[0, 1])
    support_axes = [fig.add_subplot(root_grid[1, 0]), fig.add_subplot(root_grid[1, 1])]

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
                signed_value + (max(abs(signed_value) * 0.03, 0.018) if signed_value > 0.0 else -max(abs(signed_value) * 0.03, 0.018)),
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
    importance_ax.set_yticklabels([str(item["feature"]) for item in normalized_importance_bars], fontsize=max(tick_size - 0.3, 8.6))
    importance_ax.invert_yaxis()
    importance_ax.set_xlabel(str(importance_panel.get("x_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color="#13293d")
    importance_ax.set_title(str(importance_panel.get("title") or "").strip(), fontsize=axis_title_size, fontweight="bold", color="#334155", pad=18.0)
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
        f"{item['feature']} = {item['feature_value_text']}" if item["feature_value_text"] else str(item["feature"])
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
    local_ax.set_xlabel(str(local_panel.get("x_label") or "").strip(), fontsize=axis_title_size, fontweight="bold", color="#13293d")
    local_ax.set_title(str(local_panel.get("title") or "").strip(), fontsize=axis_title_size, fontweight="bold", color="#334155", pad=10.0)
    local_ax.tick_params(axis="x", labelsize=tick_size, colors="#2F3437")
    local_ax.tick_params(axis="y", length=0, pad=6)
    local_ax.grid(axis="x", color="#e6edf2", linewidth=0.55, linestyle=":")
    _apply_publication_axes_style(local_ax)

    case_label_artist = local_ax.text(0.16, 0.965, str(local_panel.get("case_label") or "").strip(), transform=local_ax.transAxes, fontsize=max(tick_size - 0.4, 8.8), color="#475569", ha="left", va="top")
    baseline_label_artist = local_ax.text(0.02, 0.885, f"Baseline {float(local_panel['baseline_value']):.2f}", transform=local_ax.transAxes, fontsize=max(tick_size - 0.6, 8.2), color="#475569", ha="left", va="top")
    prediction_label_artist = local_ax.text(0.98, 0.885, f"Prediction {float(local_panel['predicted_value']):.2f}", transform=local_ax.transAxes, fontsize=max(tick_size - 0.6, 8.2), color="#13293d", ha="right", va="top")

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
                (segment_start, data["band_y0"]),
                segment_end - segment_start,
                data["support_band_height"],
                facecolor=support_style["facecolor"],
                edgecolor=support_style["edgecolor"],
                linewidth=1.0,
                zorder=1,
            )
            axes_item.add_patch(segment_patch)
            segment_label = str(segment["segment_label"])
            label_y = data["band_y1"] + data["support_band_height"] * 0.28 if segment_index % 2 == 1 else data["band_y0"] + data["support_band_height"] * 0.24
            label_font_size = max(tick_size - (2.0 if len(segment_label) > 8 else 1.1), 6.6)
            support_label_artists.append(
                axes_item.text((segment_start + segment_end) / 2.0, label_y, segment_label, fontsize=label_font_size, color="#334155", ha="center", va="center", zorder=3)
            )

        axes_item.plot(curve_x, curve_y, color=curve_color, linewidth=2.4, marker="o", markersize=marker_size, markerfacecolor="white", markeredgecolor=curve_color, markeredgewidth=1.1, zorder=4)
        reference_value = float(panel["reference_value"])
        axes_item.axvline(reference_value, color=reference_color, linewidth=1.0, linestyle="--", zorder=2)
        reference_label_artist = axes_item.text(reference_value, plot_y_upper - (plot_y_upper - plot_y_lower) * 0.08, str(panel["reference_label"]), fontsize=max(tick_size - 1.0, 8.0), color=reference_color, ha="center", va="top", zorder=5)

        axes_item.set_xlim(x_min - x_padding_support, x_max + x_padding_support)
        axes_item.set_ylim(plot_y_lower, plot_y_upper)
        axes_item.set_xlabel(str(panel["x_label"]), fontsize=axis_title_size, fontweight="bold", color="#13293d")
        axes_item.set_title(str(panel["title"]), fontsize=axis_title_size, fontweight="bold", color="#334155", pad=10.0)
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
        support_row_center_y = fig.transFigure.inverted().transform((0.0, (min(item.y0 for item in support_bboxes) + max(item.y1 for item in support_bboxes)) / 2.0))[1]
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
            matplotlib.lines.Line2D([], [], color=curve_color, linewidth=2.4, marker="o", markersize=5.2, markerfacecolor="white", label="Response curve"),
            matplotlib.patches.Patch(facecolor=support_style_map["observed_support"]["facecolor"], edgecolor=support_style_map["observed_support"]["edgecolor"], label="Observed support"),
            matplotlib.patches.Patch(facecolor=support_style_map["subgroup_support"]["facecolor"], edgecolor=support_style_map["subgroup_support"]["edgecolor"], label="Subgroup support"),
            matplotlib.patches.Patch(facecolor=support_style_map["bin_support"]["facecolor"], edgecolor=support_style_map["bin_support"]["edgecolor"], label="Bin support"),
            matplotlib.patches.Patch(facecolor=support_style_map["extrapolation_warning"]["facecolor"], edgecolor=support_style_map["extrapolation_warning"]["edgecolor"], label="Extrapolation reminder"),
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
        return fig.text(panel_x0 + x_padding * inset_ratio, panel_y1 - y_padding, label, transform=fig.transFigure, fontsize=max(panel_label_size + 1.5, 13.0), fontweight="bold", color="#2F3437", ha="left", va="top")

    importance_panel_label_artist = _add_panel_label(axes_item=importance_ax, label=str(importance_panel.get("panel_label") or "").strip(), inset_ratio=0.85)
    local_panel_label_artist = _add_panel_label(axes_item=local_ax, label=str(local_panel.get("panel_label") or "").strip(), inset_ratio=0.85)
    support_panel_label_artists = [_add_panel_label(axes_item=record["axes"], label=str(record["panel"]["panel_label"]), inset_ratio=1.0) for record in support_records]

    fig.canvas.draw()
    return {
        "case_label_artist": case_label_artist,
        "fig": fig,
        "importance_ax": importance_ax,
        "importance_bar_artists": importance_bar_artists,
        "importance_panel_label_artist": importance_panel_label_artist,
        "importance_value_label_artists": importance_value_label_artists,
        "local_ax": local_ax,
        "local_bar_artists": local_bar_artists,
        "local_panel_label_artist": local_panel_label_artist,
        "local_value_label_artists": local_value_label_artists,
        "negative_direction_artist": negative_direction_artist,
        "positive_direction_artist": positive_direction_artist,
        "baseline_label_artist": baseline_label_artist,
        "prediction_label_artist": prediction_label_artist,
        "support_axes": support_axes,
        "support_legend": support_legend,
        "support_panel_label_artists": support_panel_label_artists,
        "support_records": support_records,
        "support_y_axis_title_artist": support_y_axis_title_artist,
        "title_artist": title_artist,
    }
