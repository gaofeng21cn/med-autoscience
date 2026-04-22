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
    _data_box_to_layout_box,
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


def _render_baseline_missingness_qc_panel(
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
    secondary_color = resolve_color("comparator_curve", "secondary", "#B89A6D")
    audit_color = str(palette.get("audit") or "#8B3A3A").strip() or "#8B3A3A"
    light_fill = str(palette.get("light") or "#EEF4F7").strip() or "#EEF4F7"
    qc_fill = str(palette.get("primary_soft") or "#EEF3F1").strip() or "#EEF3F1"

    title_size = max(11.6, read_float(typography, "axis_title_size", 11.0) + 0.6)
    tick_size = max(9.2, read_float(typography, "tick_size", 10.0))
    panel_label_size = max(12.0, read_float(typography, "panel_label_size", 11.0) + 1.0)
    card_label_size = max(9.2, tick_size - 0.2)
    card_value_size = max(11.0, tick_size + 0.9)
    card_detail_size = max(8.4, tick_size - 1.0)

    balance_variables = list(shell_payload["balance_variables"])
    missingness_rows = list(shell_payload["missingness_rows"])
    missingness_columns = list(shell_payload["missingness_columns"])
    missingness_cells = list(shell_payload["missingness_cells"])
    qc_cards = list(shell_payload["qc_cards"])
    has_secondary = any(item.get("secondary_value") is not None for item in balance_variables)

    fig = plt.figure(figsize=(13.6, 8.2))
    fig.patch.set_facecolor("white")
    grid = fig.add_gridspec(2, 2, width_ratios=[1.18, 1.0], height_ratios=[1.0, 0.82])
    balance_axes = fig.add_subplot(grid[:, 0])
    missingness_axes = fig.add_subplot(grid[0, 1])
    qc_axes = fig.add_subplot(grid[1, 1])
    fig.subplots_adjust(left=0.17, right=0.92, top=0.90, bottom=0.12, wspace=0.34, hspace=0.38)

    ordered_balance = list(reversed(balance_variables))
    wrapped_balance_labels = [
        textwrap.fill(str(item["label"]), width=18, break_long_words=False, break_on_hyphens=False)
        for item in ordered_balance
    ]
    y_positions = list(range(len(ordered_balance)))
    primary_values = [float(item["primary_value"]) for item in ordered_balance]
    secondary_values = [
        float(item["secondary_value"])
        for item in ordered_balance
        if item.get("secondary_value") is not None
    ]
    threshold = float(shell_payload["balance_threshold"])
    max_balance_value = max(primary_values + secondary_values + [threshold, 0.10])
    balance_xmax = max(0.25, max_balance_value * 1.22 + 0.02)
    primary_y_positions = [float(index) + (0.11 if has_secondary else 0.0) for index in y_positions]
    secondary_y_positions = [float(index) - 0.11 for index in y_positions]

    threshold_line = balance_axes.axvline(
        threshold,
        color=audit_color,
        linewidth=1.5,
        linestyle="--",
        alpha=0.9,
    )
    for index, item in enumerate(ordered_balance):
        if item.get("secondary_value") is None:
            continue
        balance_axes.plot(
            [float(item["secondary_value"]), float(item["primary_value"])],
            [secondary_y_positions[index], primary_y_positions[index]],
            color=neutral_color,
            linewidth=1.1,
            alpha=0.45,
            zorder=2,
        )
    primary_scatter = balance_axes.scatter(
        primary_values,
        primary_y_positions,
        s=74,
        color=primary_color,
        edgecolors="white",
        linewidths=0.8,
        label=str(shell_payload["primary_balance_label"]),
        zorder=3,
    )
    secondary_scatter = None
    if has_secondary:
        secondary_scatter = balance_axes.scatter(
            [float(item.get("secondary_value") or 0.0) for item in ordered_balance],
            secondary_y_positions,
            s=66,
            color=secondary_color,
            edgecolors="white",
            linewidths=0.8,
            label=str(shell_payload["secondary_balance_label"]),
            zorder=3,
        )
    balance_axes.set_title(str(shell_payload["balance_panel_title"]), fontsize=title_size, fontweight="bold", color=neutral_color)
    balance_axes.set_xlabel(str(shell_payload["balance_x_label"]), fontsize=title_size, fontweight="bold", color=neutral_color)
    balance_axes.set_yticks(y_positions)
    balance_axes.set_yticklabels(wrapped_balance_labels, fontsize=tick_size, color=neutral_color)
    balance_axes.tick_params(axis="x", labelsize=tick_size, colors=neutral_color)
    balance_axes.tick_params(axis="y", length=0)
    balance_axes.set_xlim(0.0, balance_xmax)
    balance_axes.set_ylim(-0.55, len(ordered_balance) - 0.45)
    balance_axes.grid(axis="x", color=light_fill, linewidth=0.8, linestyle=":")
    balance_axes.grid(axis="y", visible=False)
    balance_axes.spines["top"].set_visible(False)
    balance_axes.spines["right"].set_visible(False)
    if has_secondary and secondary_scatter is not None:
        balance_axes.legend(
            handles=[primary_scatter, secondary_scatter, threshold_line],
            labels=[
                str(shell_payload["primary_balance_label"]),
                str(shell_payload["secondary_balance_label"]),
                f"Threshold = {threshold:.2f}",
            ],
            loc="lower right",
            frameon=False,
            fontsize=max(tick_size - 0.4, 8.8),
        )
    else:
        balance_axes.legend(
            handles=[primary_scatter, threshold_line],
            labels=[
                str(shell_payload["primary_balance_label"]),
                f"Threshold = {threshold:.2f}",
            ],
            loc="lower right",
            frameon=False,
            fontsize=max(tick_size - 0.4, 8.8),
        )

    missingness_row_labels = [str(item["label"]) for item in missingness_rows]
    missingness_column_labels = [str(item["label"]) for item in missingness_columns]
    missingness_lookup = {
        (str(item["x"]), str(item["y"])): float(item["value"]) for item in missingness_cells
    }
    missingness_matrix = [
        [missingness_lookup[(column_label, row_label)] for column_label in missingness_column_labels]
        for row_label in missingness_row_labels
    ]
    heatmap = missingness_axes.imshow(
        missingness_matrix,
        aspect="auto",
        cmap="Blues",
        vmin=0.0,
        vmax=max(max((item["value"] for item in missingness_cells), default=0.0), 0.12),
    )
    missingness_axes.set_title(
        str(shell_payload["missingness_panel_title"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    missingness_axes.set_xlabel(
        str(shell_payload["missingness_x_label"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    missingness_axes.set_ylabel(
        str(shell_payload["missingness_y_label"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    missingness_axes.set_xticks(range(len(missingness_column_labels)))
    missingness_axes.set_xticklabels(
        [textwrap.fill(label, width=12, break_long_words=False, break_on_hyphens=False) for label in missingness_column_labels],
        fontsize=tick_size,
        rotation=18,
        ha="right",
        color=neutral_color,
    )
    missingness_axes.set_yticks(range(len(missingness_row_labels)))
    missingness_axes.set_yticklabels(
        [textwrap.fill(label, width=14, break_long_words=False, break_on_hyphens=False) for label in missingness_row_labels],
        fontsize=tick_size,
        color=neutral_color,
    )
    missingness_axes.tick_params(axis="both", length=0)
    for row_index, row_label in enumerate(missingness_row_labels):
        for column_index, column_label in enumerate(missingness_column_labels):
            value = missingness_lookup[(column_label, row_label)]
            missingness_axes.text(
                column_index,
                row_index,
                f"{value * 100:.0f}%",
                ha="center",
                va="center",
                fontsize=max(tick_size - 1.0, 8.2),
                color="#0f172a",
            )
    missingness_axes.spines["top"].set_visible(False)
    missingness_axes.spines["right"].set_visible(False)
    colorbar = fig.colorbar(heatmap, ax=missingness_axes, fraction=0.046, pad=0.04)
    colorbar.set_label("Missing rate", fontsize=max(tick_size - 0.2, 9.0), color=neutral_color)
    colorbar.ax.tick_params(labelsize=max(tick_size - 1.0, 8.4), colors=neutral_color)

    qc_axes.set_title(str(shell_payload["qc_panel_title"]), fontsize=title_size, fontweight="bold", color=neutral_color)
    qc_axes.set_xlim(0.0, 1.0)
    qc_axes.set_ylim(0.0, 1.0)
    qc_axes.axis("off")
    card_artists: list[tuple[str, str, Any]] = []
    card_gap = 0.06
    available_height = 0.74
    card_height = min(0.24, (available_height - card_gap * max(len(qc_cards) - 1, 0)) / max(len(qc_cards), 1))
    card_top = 0.84
    for index, card in enumerate(qc_cards):
        card_y1 = card_top - index * (card_height + card_gap)
        card_y0 = card_y1 - card_height
        card_patch = FancyBboxPatch(
            (0.06, card_y0),
            0.88,
            card_height,
            transform=qc_axes.transAxes,
            boxstyle="round,pad=0.012,rounding_size=0.03",
            linewidth=1.1,
            edgecolor=neutral_color,
            facecolor=qc_fill,
        )
        qc_axes.add_patch(card_patch)
        label_artist = qc_axes.text(
            0.10,
            card_y1 - 0.04,
            str(card["label"]),
            transform=qc_axes.transAxes,
            fontsize=card_label_size,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )
        value_artist = qc_axes.text(
            0.10,
            card_y0 + card_height * 0.48,
            str(card["value"]),
            transform=qc_axes.transAxes,
            fontsize=card_value_size,
            fontweight="bold",
            color=primary_color,
            ha="left",
            va="center",
        )
        card_artists.append((f"qc_card_label_{card['card_id']}", "card_label", label_artist))
        card_artists.append((f"qc_card_value_{card['card_id']}", "card_value", value_artist))
        detail_text = str(card.get("detail") or "").strip()
        if detail_text:
            detail_artist = qc_axes.text(
                0.42,
                card_y0 + card_height * 0.48,
                textwrap.fill(detail_text, width=28, break_long_words=False, break_on_hyphens=False),
                transform=qc_axes.transAxes,
                fontsize=card_detail_size,
                color=neutral_color,
                ha="left",
                va="center",
            )
            card_artists.append((f"qc_card_detail_{card['card_id']}", "card_detail", detail_artist))

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

    panel_label_a = add_panel_label(axes_item=balance_axes, label="A")
    panel_label_b = add_panel_label(axes_item=missingness_axes, label="B")
    panel_label_c = add_panel_label(axes_item=qc_axes, label="C")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=balance_axes.title.get_window_extent(renderer=renderer), box_id="balance_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=balance_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="balance_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=missingness_axes.title.get_window_extent(renderer=renderer), box_id="missingness_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=missingness_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="missingness_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=missingness_axes.yaxis.label.get_window_extent(renderer=renderer), box_id="missingness_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=qc_axes.title.get_window_extent(renderer=renderer), box_id="qc_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_a.get_window_extent(renderer=renderer), box_id="panel_label_A", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_b.get_window_extent(renderer=renderer), box_id="panel_label_B", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_c.get_window_extent(renderer=renderer), box_id="panel_label_C", box_type="panel_label"),
    ]
    for box_id, box_type, artist in card_artists:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type=box_type,
            )
        )

    panel_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=balance_axes.get_window_extent(renderer=renderer), box_id="panel_balance", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=missingness_axes.get_window_extent(renderer=renderer), box_id="panel_missingness", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=qc_axes.get_window_extent(renderer=renderer), box_id="panel_qc", box_type="panel"),
    ]
    threshold_half_width = max(balance_xmax * 0.003, 0.0015)
    guide_boxes = [
        _data_box_to_layout_box(
            axes=balance_axes,
            figure=fig,
            x0=threshold - threshold_half_width,
            y0=-0.45,
            x1=threshold + threshold_half_width,
            y1=max(len(ordered_balance) - 0.55, 0.45),
            box_id="balance_threshold",
            box_type="reference_line",
        ),
        _bbox_to_layout_box(
            figure=fig,
            bbox=colorbar.ax.get_window_extent(renderer=renderer),
            box_id="missingness_colorbar",
            box_type="colorbar",
        ),
    ]

    metrics_qc_cards: list[dict[str, Any]] = []
    for card in qc_cards:
        metrics_qc_cards.append(
            {
                "card_id": str(card["card_id"]),
                "label_box_id": f"qc_card_label_{card['card_id']}",
                "value_box_id": f"qc_card_value_{card['card_id']}",
            }
        )

    dump_json(
        output_layout_path,
        {
            "template_id": "baseline_missingness_qc_panel",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "primary_balance_label": str(shell_payload["primary_balance_label"]),
                "secondary_balance_label": str(shell_payload.get("secondary_balance_label") or "").strip(),
                "balance_threshold": float(shell_payload["balance_threshold"]),
                "balance_variables": list(shell_payload["balance_variables"]),
                "missingness_rows": list(shell_payload["missingness_rows"]),
                "missingness_columns": list(shell_payload["missingness_columns"]),
                "missingness_cells": list(shell_payload["missingness_cells"]),
                "qc_cards": metrics_qc_cards,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=240)
    plt.close(fig)


