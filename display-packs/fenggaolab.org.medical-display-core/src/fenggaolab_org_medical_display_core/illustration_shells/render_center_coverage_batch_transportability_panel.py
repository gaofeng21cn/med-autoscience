from __future__ import annotations

from pathlib import Path
import textwrap
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch

from ..shared import (
    _bbox_to_layout_box,
    _prepare_python_illustration_output_paths,
    dump_json,
)


_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}
_COHORT_FLOW_LAYOUT_MODES = {"two_panel_flow", "single_panel_cards"}
_COHORT_FLOW_STEP_ROLE_LABELS: dict[str, str] = {
    "historical_reference": "Historical patient reference",
    "current_patient_surface": "Current patient surface",
    "clinician_surface": "Clinician surface",
}


def _render_center_coverage_batch_transportability_panel(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
) -> None:
    render_context_payload = dict(render_context or {})
    palette = dict(render_context_payload.get("palette") or {})
    style_roles = dict(render_context_payload.get("style_roles") or {})
    typography = dict(render_context_payload.get("typography") or {})

    def resolve_color(style_key: str, palette_key: str, default: str) -> str:
        style_value = str(style_roles.get(style_key) or "").strip()
        if style_value:
            return style_value
        palette_value = str(palette.get(palette_key) or "").strip()
        return palette_value or default

    def read_float(mapping: dict[str, Any], key: str, default: float) -> float:
        value = mapping.get(key, default)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return float(default)

    _prepare_python_illustration_output_paths(
        output_png_path=output_png_path,
        output_svg_path=output_svg_path,
        layout_sidecar_path=output_layout_path,
    )

    neutral_color = resolve_color("reference_line", "neutral", "#475569")
    primary_color = resolve_color("model_curve", "primary", "#245A6B")
    audit_color = str(palette.get("audit") or "#8B3A3A").strip() or "#8B3A3A"
    light_fill = str(palette.get("light") or "#EEF4F7").strip() or "#EEF4F7"
    qc_fill = str(palette.get("primary_soft") or "#EEF3F1").strip() or "#EEF3F1"

    title_size = max(11.6, read_float(typography, "axis_title_size", 11.0) + 0.6)
    tick_size = max(9.2, read_float(typography, "tick_size", 10.0))
    panel_label_size = max(12.0, read_float(typography, "panel_label_size", 11.0) + 1.0)
    card_label_size = max(9.2, tick_size - 0.2)
    card_value_size = max(11.0, tick_size + 0.9)
    card_detail_size = max(8.4, tick_size - 1.0)

    center_rows = list(shell_payload["center_rows"])
    batch_rows = list(shell_payload["batch_rows"])
    batch_columns = list(shell_payload["batch_columns"])
    batch_cells = list(shell_payload["batch_cells"])
    transportability_cards = list(shell_payload["transportability_cards"])

    fig = plt.figure(figsize=(13.6, 8.2))
    fig.patch.set_facecolor("white")
    grid = fig.add_gridspec(2, 2, width_ratios=[1.18, 1.0], height_ratios=[1.0, 0.82])
    coverage_axes = fig.add_subplot(grid[:, 0])
    batch_axes = fig.add_subplot(grid[0, 1])
    transportability_axes = fig.add_subplot(grid[1, 1])
    fig.subplots_adjust(left=0.17, right=0.92, top=0.90, bottom=0.12, wspace=0.34, hspace=0.38)

    ordered_centers = list(reversed(center_rows))
    coverage_labels = [
        textwrap.fill(str(item["center_label"]), width=16, break_long_words=False, break_on_hyphens=False)
        for item in ordered_centers
    ]
    y_positions = list(range(len(ordered_centers)))
    support_counts = [int(item["support_count"]) for item in ordered_centers]
    coverage_xmax = max(max(support_counts) * 1.22, 100.0)
    coverage_axes.barh(y_positions, support_counts, color=primary_color, edgecolor="white", linewidth=0.8)
    for index, item in enumerate(ordered_centers):
        coverage_axes.text(
            min(float(item["support_count"]) + coverage_xmax * 0.018, coverage_xmax * 0.96),
            y_positions[index],
            f"Events {int(item['event_count'])} | {str(item['cohort_role'])}",
            fontsize=max(tick_size - 0.4, 8.6),
            color=neutral_color,
            va="center",
            ha="left",
        )
    coverage_axes.set_title(
        str(shell_payload["coverage_panel_title"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    coverage_axes.set_xlabel(
        str(shell_payload["coverage_x_label"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    coverage_axes.set_yticks(y_positions)
    coverage_axes.set_yticklabels(coverage_labels, fontsize=tick_size, color=neutral_color)
    coverage_axes.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
    coverage_axes.tick_params(axis="y", length=0)
    coverage_axes.set_xlim(0.0, coverage_xmax)
    coverage_axes.set_ylim(-0.55, len(ordered_centers) - 0.45)
    coverage_axes.grid(axis="x", color=light_fill, linewidth=0.8, linestyle=":")
    coverage_axes.grid(axis="y", visible=False)
    coverage_axes.spines["top"].set_visible(False)
    coverage_axes.spines["right"].set_visible(False)

    batch_row_labels = [str(item["label"]) for item in batch_rows]
    batch_column_labels = [str(item["label"]) for item in batch_columns]
    batch_lookup = {(str(item["x"]), str(item["y"])): float(item["value"]) for item in batch_cells}
    batch_matrix = [
        [batch_lookup[(column_label, row_label)] for column_label in batch_column_labels]
        for row_label in batch_row_labels
    ]
    batch_max = max(max((item["value"] for item in batch_cells), default=0.0), float(shell_payload["batch_threshold"]), 0.20)
    heatmap = batch_axes.imshow(
        batch_matrix,
        aspect="auto",
        cmap="YlOrRd",
        vmin=0.0,
        vmax=batch_max,
    )
    batch_axes.set_title(
        str(shell_payload["batch_panel_title"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    batch_axes.set_xlabel(
        str(shell_payload["batch_x_label"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    batch_axes.set_ylabel(
        str(shell_payload["batch_y_label"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    batch_axes.set_xticks(range(len(batch_column_labels)))
    batch_axes.set_xticklabels(
        [textwrap.fill(label, width=12, break_long_words=False, break_on_hyphens=False) for label in batch_column_labels],
        fontsize=tick_size,
        rotation=18,
        ha="right",
        color=neutral_color,
    )
    batch_axes.set_yticks(range(len(batch_row_labels)))
    batch_axes.set_yticklabels(
        [textwrap.fill(label, width=14, break_long_words=False, break_on_hyphens=False) for label in batch_row_labels],
        fontsize=tick_size,
        color=neutral_color,
    )
    batch_axes.tick_params(axis="both", length=0)
    for row_index, row_label in enumerate(batch_row_labels):
        for column_index, column_label in enumerate(batch_column_labels):
            value = batch_lookup[(column_label, row_label)]
            batch_axes.text(
                column_index,
                row_index,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.0, 8.2),
                color="#0f172a",
            )
    batch_axes.spines["top"].set_visible(False)
    batch_axes.spines["right"].set_visible(False)
    colorbar = fig.colorbar(heatmap, ax=batch_axes, fraction=0.046, pad=0.04)
    colorbar.set_label("Shift score", fontsize=max(tick_size - 0.2, 9.0), color=neutral_color)
    colorbar.ax.tick_params(labelsize=max(tick_size - 1.0, 8.4), colors=neutral_color)
    threshold_line_artist = colorbar.ax.axhline(
        float(shell_payload["batch_threshold"]),
        color=audit_color,
        linewidth=1.4,
        linestyle="--",
    )

    transportability_axes.set_title(
        str(shell_payload["transportability_panel_title"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    transportability_axes.set_xlim(0.0, 1.0)
    transportability_axes.set_ylim(0.0, 1.0)
    transportability_axes.axis("off")
    card_artists: list[tuple[str, str, Any]] = []
    card_gap = 0.06
    available_height = 0.74
    card_height = min(0.24, (available_height - card_gap * max(len(transportability_cards) - 1, 0)) / max(len(transportability_cards), 1))
    card_top = 0.84
    for index, card in enumerate(transportability_cards):
        card_y1 = card_top - index * (card_height + card_gap)
        card_y0 = card_y1 - card_height
        card_patch = FancyBboxPatch(
            (0.06, card_y0),
            0.88,
            card_height,
            transform=transportability_axes.transAxes,
            boxstyle="round,pad=0.012,rounding_size=0.03",
            linewidth=1.1,
            edgecolor=neutral_color,
            facecolor=qc_fill,
        )
        transportability_axes.add_patch(card_patch)
        label_artist = transportability_axes.text(
            0.10,
            card_y1 - 0.04,
            str(card["label"]),
            transform=transportability_axes.transAxes,
            fontsize=card_label_size,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )
        value_artist = transportability_axes.text(
            0.10,
            card_y0 + card_height * 0.48,
            str(card["value"]),
            transform=transportability_axes.transAxes,
            fontsize=card_value_size,
            fontweight="bold",
            color=primary_color,
            ha="left",
            va="center",
        )
        card_artists.append((f"transport_card_label_{card['card_id']}", "card_label", label_artist))
        card_artists.append((f"transport_card_value_{card['card_id']}", "card_value", value_artist))
        detail_text = str(card.get("detail") or "").strip()
        if detail_text:
            detail_artist = transportability_axes.text(
                0.42,
                card_y0 + card_height * 0.48,
                textwrap.fill(detail_text, width=28, break_long_words=False, break_on_hyphens=False),
                transform=transportability_axes.transAxes,
                fontsize=card_detail_size,
                color=neutral_color,
                ha="left",
                va="center",
            )
            card_artists.append((f"transport_card_detail_{card['card_id']}", "card_detail", detail_artist))

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    def add_panel_label(*, axes_item: Any, label: str) -> Any:
        panel_bbox = axes_item.get_window_extent(renderer=renderer)
        panel_x0, panel_y0 = fig.transFigure.inverted().transform((panel_bbox.x0, panel_bbox.y0))
        panel_x1, panel_y1 = fig.transFigure.inverted().transform((panel_bbox.x1, panel_bbox.y1))
        panel_width = float(panel_x1 - panel_x0)
        panel_height = float(panel_y1 - panel_y0)
        return fig.text(
            panel_x0 + min(max(panel_width * 0.018, 0.006), 0.014),
            panel_y1 - min(max(panel_height * 0.032, 0.008), 0.016),
            label,
            transform=fig.transFigure,
            fontsize=panel_label_size,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )

    panel_label_a = add_panel_label(axes_item=coverage_axes, label="A")
    panel_label_b = add_panel_label(axes_item=batch_axes, label="B")
    panel_label_c = add_panel_label(axes_item=transportability_axes, label="C")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=coverage_axes.title.get_window_extent(renderer=renderer), box_id="coverage_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=coverage_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="coverage_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=batch_axes.title.get_window_extent(renderer=renderer), box_id="batch_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=batch_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="batch_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=batch_axes.yaxis.label.get_window_extent(renderer=renderer), box_id="batch_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=transportability_axes.title.get_window_extent(renderer=renderer), box_id="transportability_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_a.get_window_extent(renderer=renderer), box_id="panel_label_A", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_b.get_window_extent(renderer=renderer), box_id="panel_label_B", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_c.get_window_extent(renderer=renderer), box_id="panel_label_C", box_type="panel_label"),
    ]
    for box_id, box_type, artist in card_artists:
        layout_boxes.append(_bbox_to_layout_box(figure=fig, bbox=artist.get_window_extent(renderer=renderer), box_id=box_id, box_type=box_type))

    panel_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=coverage_axes.get_window_extent(renderer=renderer), box_id="panel_coverage", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=batch_axes.get_window_extent(renderer=renderer), box_id="panel_batch", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=transportability_axes.get_window_extent(renderer=renderer), box_id="panel_transportability", box_type="panel"),
    ]
    guide_boxes = [
        _bbox_to_layout_box(
            figure=fig,
            bbox=threshold_line_artist.get_window_extent(renderer=renderer),
            box_id="batch_threshold",
            box_type="reference_line",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="batch_colorbar",
            box_type="colorbar",
        ),
    ]

    metrics_transportability_cards: list[dict[str, Any]] = []
    for card in transportability_cards:
        metrics_transportability_cards.append(
            {
                "card_id": str(card["card_id"]),
                "label_box_id": f"transport_card_label_{card['card_id']}",
                "value_box_id": f"transport_card_value_{card['card_id']}",
            }
        )

    dump_json(
        output_layout_path,
        {
            "template_id": "center_coverage_batch_transportability_panel",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "batch_threshold": float(shell_payload["batch_threshold"]),
                "center_rows": list(shell_payload["center_rows"]),
                "batch_rows": list(shell_payload["batch_rows"]),
                "batch_columns": list(shell_payload["batch_columns"]),
                "batch_cells": list(shell_payload["batch_cells"]),
                "transportability_cards": metrics_transportability_cards,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=240)
    plt.close(fig)

