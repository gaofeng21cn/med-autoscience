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


def _render_transportability_recalibration_governance_panel(
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
    audit_soft = str(palette.get("audit_soft") or "#FAEFED").strip() or "#FAEFED"
    light_fill = str(palette.get("light") or "#EEF4F7").strip() or "#EEF4F7"
    qc_fill = str(palette.get("primary_soft") or "#EEF3F1").strip() or "#EEF3F1"

    title_size = max(11.6, read_float(typography, "axis_title_size", 11.0) + 0.6)
    tick_size = max(9.2, read_float(typography, "tick_size", 10.0))
    panel_label_size = max(12.0, read_float(typography, "panel_label_size", 11.0) + 1.0)
    row_label_size = max(8.8, tick_size - 0.1)
    row_metric_size = max(9.0, tick_size - 0.2)
    row_action_size = max(8.8, tick_size - 0.3)
    row_detail_size = max(8.0, tick_size - 1.1)

    center_rows = list(shell_payload["center_rows"])
    batch_rows = list(shell_payload["batch_rows"])
    batch_columns = list(shell_payload["batch_columns"])
    batch_cells = list(shell_payload["batch_cells"])
    recalibration_rows_by_center_id = {
        str(item["center_id"]): dict(item) for item in shell_payload["recalibration_rows"]
    }
    ordered_recalibration_rows = [
        recalibration_rows_by_center_id[str(center["center_id"])]
        for center in center_rows
    ]
    center_rows_by_id = {
        str(item["center_id"]): dict(item) for item in center_rows
    }

    fig = plt.figure(figsize=(13.6, 8.2))
    fig.patch.set_facecolor("white")
    grid = fig.add_gridspec(2, 2, width_ratios=[1.18, 1.0], height_ratios=[1.0, 0.82])
    coverage_axes = fig.add_subplot(grid[:, 0])
    batch_axes = fig.add_subplot(grid[0, 1])
    recalibration_axes = fig.add_subplot(grid[1, 1])
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

    recalibration_axes.set_title(
        str(shell_payload["recalibration_panel_title"]),
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
    )
    recalibration_axes.set_xlim(0.0, 1.0)
    recalibration_axes.set_ylim(0.0, 1.0)
    recalibration_axes.axis("off")

    slope_acceptance_lower = float(shell_payload["slope_acceptance_lower"])
    slope_acceptance_upper = float(shell_payload["slope_acceptance_upper"])
    oe_ratio_acceptance_lower = float(shell_payload["oe_ratio_acceptance_lower"])
    oe_ratio_acceptance_upper = float(shell_payload["oe_ratio_acceptance_upper"])
    row_artists: list[tuple[str, str, Any]] = []
    metrics_recalibration_rows: list[dict[str, Any]] = []
    row_gap = 0.045
    available_height = 0.70
    row_height = min(0.215, (available_height - row_gap * max(len(ordered_recalibration_rows) - 1, 0)) / max(len(ordered_recalibration_rows), 1))
    row_top = 0.86
    for index, row in enumerate(ordered_recalibration_rows):
        center = center_rows_by_id[str(row["center_id"])]
        row_y1 = row_top - index * (row_height + row_gap)
        row_y0 = row_y1 - row_height
        slope = float(row["slope"])
        oe_ratio = float(row["oe_ratio"])
        within_band = (
            slope_acceptance_lower <= slope <= slope_acceptance_upper
            and oe_ratio_acceptance_lower <= oe_ratio <= oe_ratio_acceptance_upper
        )
        row_fill = qc_fill if within_band else audit_soft
        row_edge = neutral_color if within_band else audit_color
        row_patch = FancyBboxPatch(
            (0.05, row_y0),
            0.90,
            row_height,
            transform=recalibration_axes.transAxes,
            boxstyle="round,pad=0.010,rounding_size=0.028",
            linewidth=1.1,
            edgecolor=row_edge,
            facecolor=row_fill,
        )
        recalibration_axes.add_patch(row_patch)
        label_artist = recalibration_axes.text(
            0.09,
            row_y1 - 0.035,
            textwrap.fill(str(center["center_label"]), width=18, break_long_words=False, break_on_hyphens=False),
            transform=recalibration_axes.transAxes,
            fontsize=row_label_size,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )
        slope_artist = recalibration_axes.text(
            0.09,
            row_y0 + row_height * 0.44,
            f"Slope {slope:.2f}",
            transform=recalibration_axes.transAxes,
            fontsize=row_metric_size,
            color=neutral_color,
            ha="left",
            va="center",
        )
        oe_artist = recalibration_axes.text(
            0.36,
            row_y0 + row_height * 0.44,
            f"O:E {oe_ratio:.2f}",
            transform=recalibration_axes.transAxes,
            fontsize=row_metric_size,
            color=neutral_color,
            ha="left",
            va="center",
        )
        action_artist = recalibration_axes.text(
            0.91,
            row_y0 + row_height * 0.50,
            textwrap.fill(str(row["action"]), width=16, break_long_words=False, break_on_hyphens=False),
            transform=recalibration_axes.transAxes,
            fontsize=row_action_size,
            fontweight="bold",
            color=primary_color if within_band else audit_color,
            ha="right",
            va="center",
        )
        detail_text = str(row.get("detail") or "").strip()
        if detail_text:
            detail_artist = recalibration_axes.text(
                0.09,
                row_y0 + row_height * 0.13,
                textwrap.fill(detail_text, width=44, break_long_words=False, break_on_hyphens=False),
                transform=recalibration_axes.transAxes,
                fontsize=row_detail_size,
                color=neutral_color,
                ha="left",
                va="bottom",
            )
            row_artists.append((f"recalibration_row_detail_{row['center_id']}", "row_detail", detail_artist))
        row_artists.extend(
            [
                (f"recalibration_row_label_{row['center_id']}", "row_label", label_artist),
                (f"recalibration_row_slope_{row['center_id']}", "row_metric", slope_artist),
                (f"recalibration_row_oe_{row['center_id']}", "row_metric", oe_artist),
                (f"recalibration_row_action_{row['center_id']}", "row_action", action_artist),
            ]
        )
        metrics_recalibration_rows.append(
            {
                "center_id": str(row["center_id"]),
                "label_box_id": f"recalibration_row_label_{row['center_id']}",
                "slope_box_id": f"recalibration_row_slope_{row['center_id']}",
                "oe_ratio_box_id": f"recalibration_row_oe_{row['center_id']}",
                "action_box_id": f"recalibration_row_action_{row['center_id']}",
                "slope": slope,
                "oe_ratio": oe_ratio,
            }
        )

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
    panel_label_c = add_panel_label(axes_item=recalibration_axes, label="C")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    layout_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=coverage_axes.title.get_window_extent(renderer=renderer), box_id="coverage_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=coverage_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="coverage_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=batch_axes.title.get_window_extent(renderer=renderer), box_id="batch_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=batch_axes.xaxis.label.get_window_extent(renderer=renderer), box_id="batch_x_axis_title", box_type="subplot_x_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=batch_axes.yaxis.label.get_window_extent(renderer=renderer), box_id="batch_y_axis_title", box_type="subplot_y_axis_title"),
        _bbox_to_layout_box(figure=fig, bbox=recalibration_axes.title.get_window_extent(renderer=renderer), box_id="recalibration_panel_title", box_type="panel_title"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_a.get_window_extent(renderer=renderer), box_id="panel_label_A", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_b.get_window_extent(renderer=renderer), box_id="panel_label_B", box_type="panel_label"),
        _bbox_to_layout_box(figure=fig, bbox=panel_label_c.get_window_extent(renderer=renderer), box_id="panel_label_C", box_type="panel_label"),
    ]
    for box_id, box_type, artist in row_artists:
        layout_boxes.append(_bbox_to_layout_box(figure=fig, bbox=artist.get_window_extent(renderer=renderer), box_id=box_id, box_type=box_type))

    panel_boxes = [
        _bbox_to_layout_box(figure=fig, bbox=coverage_axes.get_window_extent(renderer=renderer), box_id="panel_coverage", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=batch_axes.get_window_extent(renderer=renderer), box_id="panel_batch", box_type="panel"),
        _bbox_to_layout_box(figure=fig, bbox=recalibration_axes.get_window_extent(renderer=renderer), box_id="panel_recalibration", box_type="panel"),
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

    dump_json(
        output_layout_path,
        {
            "template_id": "transportability_recalibration_governance_panel",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "batch_threshold": float(shell_payload["batch_threshold"]),
                "slope_acceptance_lower": slope_acceptance_lower,
                "slope_acceptance_upper": slope_acceptance_upper,
                "oe_ratio_acceptance_lower": oe_ratio_acceptance_lower,
                "oe_ratio_acceptance_upper": oe_ratio_acceptance_upper,
                "center_rows": list(shell_payload["center_rows"]),
                "batch_rows": list(shell_payload["batch_rows"]),
                "batch_columns": list(shell_payload["batch_columns"]),
                "batch_cells": list(shell_payload["batch_cells"]),
                "recalibration_rows": metrics_recalibration_rows,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=240)
    plt.close(fig)

