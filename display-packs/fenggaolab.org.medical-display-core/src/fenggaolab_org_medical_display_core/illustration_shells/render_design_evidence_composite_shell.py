from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from ..shared import (
    _bbox_to_layout_box,
    _flow_box_to_normalized,
    _measure_flow_text_width_pt,
    _wrap_flow_text_to_width,
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


def _render_design_evidence_composite_shell(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
) -> None:
    render_context_payload = dict(render_context or {})
    palette = dict(render_context_payload.get("palette") or {})
    typography = dict(render_context_payload.get("typography") or {})

    def palette_color(key: str, default: str) -> str:
        value = str(palette.get(key) or "").strip()
        return value or default

    def read_float(mapping: dict[str, Any], key: str, default: float) -> float:
        value = mapping.get(key, default)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return float(default)

    workflow_stages = list(shell_payload["workflow_stages"])
    summary_panel_by_role = {
        str(panel["layout_role"]): dict(panel)
        for panel in shell_payload["summary_panels"]
    }
    ordered_summary_roles = ("left", "center", "right")
    ordered_summary_panels = [summary_panel_by_role[role] for role in ordered_summary_roles]

    figure_width_pt = 13.2 * 72.0
    figure_height_pt = 8.2 * 72.0
    side_margin_pt = 34.0
    top_margin_pt = 26.0
    bottom_margin_pt = 26.0
    ribbon_height_pt = 110.0
    ribbon_summary_gap_pt = 28.0
    stage_gap_pt = 24.0
    panel_gap_pt = 24.0
    stage_padding_pt = 14.0
    panel_padding_pt = 16.0
    header_gap_pt = 12.0
    card_gap_pt = 14.0
    detail_gap_pt = 5.0
    label_title_gap_pt = 12.0

    stage_count = len(workflow_stages)
    stage_width_pt = (figure_width_pt - side_margin_pt * 2.0 - stage_gap_pt * (stage_count - 1)) / stage_count
    stage_y0 = figure_height_pt - top_margin_pt - ribbon_height_pt
    stage_y1 = stage_y0 + ribbon_height_pt

    summary_height_pt = stage_y0 - bottom_margin_pt - ribbon_summary_gap_pt
    if summary_height_pt <= 160.0:
        raise ValueError("design_evidence_composite_shell does not leave enough height for the summary panels")
    summary_panel_width_pt = (figure_width_pt - side_margin_pt * 2.0 - panel_gap_pt * 2.0) / 3.0
    summary_y0 = bottom_margin_pt
    summary_y1 = summary_y0 + summary_height_pt

    workflow_stage_regions: list[dict[str, float]] = []
    for stage_index in range(stage_count):
        x0 = side_margin_pt + stage_index * (stage_width_pt + stage_gap_pt)
        workflow_stage_regions.append(
            {
                "x0": x0,
                "y0": stage_y0,
                "x1": x0 + stage_width_pt,
                "y1": stage_y1,
            }
        )

    summary_regions = {
        "left": {
            "x0": side_margin_pt,
            "y0": summary_y0,
            "x1": side_margin_pt + summary_panel_width_pt,
            "y1": summary_y1,
        },
        "center": {
            "x0": side_margin_pt + summary_panel_width_pt + panel_gap_pt,
            "y0": summary_y0,
            "x1": side_margin_pt + summary_panel_width_pt * 2.0 + panel_gap_pt,
            "y1": summary_y1,
        },
        "right": {
            "x0": side_margin_pt + (summary_panel_width_pt + panel_gap_pt) * 2.0,
            "y0": summary_y0,
            "x1": side_margin_pt + summary_panel_width_pt * 3.0 + panel_gap_pt * 2.0,
            "y1": summary_y1,
        },
    }

    stage_fill = palette_color("primary_soft", "#EAF2F5")
    stage_edge = palette_color("primary", "#245A6B")
    stage_title_color = palette_color("primary", "#245A6B")
    stage_detail_color = palette_color("neutral", "#6B7280")
    panel_fill_by_role = {
        "left": palette_color("primary_soft", "#EAF2F5"),
        "center": palette_color("secondary_soft", "#F4EEE5"),
        "right": palette_color("contrast_soft", "#F7EBEB"),
    }
    panel_accent_by_role = {
        "left": palette_color("primary", "#245A6B"),
        "center": palette_color("secondary", "#B89A6D"),
        "right": palette_color("contrast", "#8B3A3A"),
    }
    border_color = palette_color("neutral", "#6B7280")
    body_color = palette_color("neutral", "#374151")

    base_stage_title_size = max(12.0, read_float(typography, "axis_title_size", 11.0) + 1.0)
    base_stage_detail_size = max(9.2, read_float(typography, "tick_size", 10.0) - 0.4)
    base_panel_label_size = max(11.4, read_float(typography, "panel_label_size", 11.0) + 0.8)
    base_summary_title_size = max(11.4, read_float(typography, "axis_title_size", 11.0) + 0.7)
    base_card_label_size = max(9.2, read_float(typography, "tick_size", 10.0) - 0.3)
    base_card_value_size = max(11.2, read_float(typography, "tick_size", 10.0) + 1.2)
    base_card_detail_size = max(8.6, read_float(typography, "tick_size", 10.0) - 0.9)

    def line_height(font_size: float) -> float:
        return font_size * 1.22

    def layout_stage(stage: dict[str, Any], region: dict[str, float], *, scale: float, stage_index: int) -> dict[str, Any]:
        inner_x0 = region["x0"] + stage_padding_pt
        inner_x1 = region["x1"] - stage_padding_pt
        inner_y1 = region["y1"] - stage_padding_pt
        inner_y0 = region["y0"] + stage_padding_pt
        title_size = base_stage_title_size * scale
        detail_size = base_stage_detail_size * scale
        title_lines = _wrap_flow_text_to_width(
            str(stage["title"]),
            max_width_pt=inner_x1 - inner_x0,
            font_size=title_size,
            font_weight="bold",
        )
        detail_lines = _wrap_flow_text_to_width(
            str(stage.get("detail") or ""),
            max_width_pt=inner_x1 - inner_x0,
            font_size=detail_size,
            font_weight="normal",
        )
        title_height_pt = line_height(title_size) * max(1, len(title_lines))
        detail_height_pt = line_height(detail_size) * len(detail_lines) if detail_lines else 0.0
        total_height_pt = title_height_pt + (detail_gap_pt + detail_height_pt if detail_height_pt else 0.0)
        return {
            "stage": stage,
            "stage_index": stage_index,
            "region": region,
            "inner_x0": inner_x0,
            "inner_y1": inner_y1,
            "inner_y0": inner_y0,
            "title_text": "\n".join(title_lines),
            "detail_text": "\n".join(detail_lines),
            "title_size": title_size,
            "detail_size": detail_size,
            "title_height_pt": title_height_pt,
            "detail_height_pt": detail_height_pt,
            "total_height_pt": total_height_pt,
        }

    def layout_summary_panel(panel: dict[str, Any], region: dict[str, float], *, scale: float) -> dict[str, Any]:
        inner_x0 = region["x0"] + panel_padding_pt
        inner_x1 = region["x1"] - panel_padding_pt
        inner_y1 = region["y1"] - panel_padding_pt
        inner_y0 = region["y0"] + panel_padding_pt
        panel_label_size = base_panel_label_size * scale
        summary_title_size = base_summary_title_size * scale
        card_label_size = base_card_label_size * scale
        card_value_size = base_card_value_size * scale
        card_detail_size = base_card_detail_size * scale

        panel_label_text = str(panel["panel_label"])
        label_width_pt = max(
            _measure_flow_text_width_pt(panel_label_text, font_size=panel_label_size, font_weight="bold"),
            panel_label_size * 0.9,
        )
        title_lines = _wrap_flow_text_to_width(
            str(panel["title"]),
            max_width_pt=max(inner_x1 - (inner_x0 + label_width_pt + label_title_gap_pt), 72.0),
            font_size=summary_title_size,
            font_weight="bold",
        )
        title_height_pt = line_height(summary_title_size) * max(1, len(title_lines))
        header_height_pt = max(line_height(panel_label_size), title_height_pt)
        total_height_pt = header_height_pt + header_gap_pt
        cards_layout: list[dict[str, Any]] = []
        for card in panel["cards"]:
            label_lines = _wrap_flow_text_to_width(
                str(card["label"]),
                max_width_pt=inner_x1 - inner_x0,
                font_size=card_label_size,
                font_weight="bold",
            )
            value_lines = _wrap_flow_text_to_width(
                str(card["value"]),
                max_width_pt=inner_x1 - inner_x0,
                font_size=card_value_size,
                font_weight="bold",
            )
            detail_lines = _wrap_flow_text_to_width(
                str(card.get("detail") or ""),
                max_width_pt=inner_x1 - inner_x0,
                font_size=card_detail_size,
                font_weight="normal",
            )
            label_height_pt = line_height(card_label_size) * max(1, len(label_lines))
            value_height_pt = line_height(card_value_size) * max(1, len(value_lines))
            detail_height_pt = line_height(card_detail_size) * len(detail_lines) if detail_lines else 0.0
            card_height_pt = label_height_pt + 4.0 + value_height_pt + (detail_gap_pt + detail_height_pt if detail_height_pt else 0.0)
            cards_layout.append(
                {
                    "card": card,
                    "label_text": "\n".join(label_lines),
                    "value_text": "\n".join(value_lines),
                    "detail_text": "\n".join(detail_lines),
                    "label_height_pt": label_height_pt,
                    "value_height_pt": value_height_pt,
                    "detail_height_pt": detail_height_pt,
                    "card_height_pt": card_height_pt,
                    "card_label_size": card_label_size,
                    "card_value_size": card_value_size,
                    "card_detail_size": card_detail_size,
                }
            )
            total_height_pt += card_height_pt + card_gap_pt
        if cards_layout:
            total_height_pt -= card_gap_pt
        return {
            "panel": panel,
            "region": region,
            "inner_x0": inner_x0,
            "inner_y1": inner_y1,
            "inner_y0": inner_y0,
            "panel_label_text": panel_label_text,
            "panel_label_size": panel_label_size,
            "panel_label_width_pt": label_width_pt,
            "summary_title_text": "\n".join(title_lines),
            "summary_title_size": summary_title_size,
            "summary_title_height_pt": title_height_pt,
            "header_height_pt": header_height_pt,
            "cards_layout": cards_layout,
            "total_height_pt": total_height_pt,
        }

    selected_stage_layouts: list[dict[str, Any]] | None = None
    selected_panel_layouts: list[dict[str, Any]] | None = None
    for scale in (1.0, 0.95, 0.90, 0.86, 0.82, 0.78, 0.74):
        stage_layouts = [
            layout_stage(stage, region, scale=scale, stage_index=index + 1)
            for index, (stage, region) in enumerate(zip(workflow_stages, workflow_stage_regions, strict=True))
        ]
        panel_layouts = [
            layout_summary_panel(panel, summary_regions[str(panel["layout_role"])], scale=scale)
            for panel in ordered_summary_panels
        ]
        stages_fit = all(
            layout["total_height_pt"] <= (layout["region"]["y1"] - layout["region"]["y0"] - stage_padding_pt * 2.0)
            for layout in stage_layouts
        )
        panels_fit = all(
            layout["total_height_pt"] <= (layout["region"]["y1"] - layout["region"]["y0"] - panel_padding_pt * 2.0)
            for layout in panel_layouts
        )
        if stages_fit and panels_fit:
            selected_stage_layouts = stage_layouts
            selected_panel_layouts = panel_layouts
            break
    if selected_stage_layouts is None or selected_panel_layouts is None:
        raise ValueError("design_evidence_composite_shell content does not fit the bounded workflow-summary composite")

    fig = plt.figure(figsize=(figure_width_pt / 72.0, figure_height_pt / 72.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, figure_width_pt)
    ax.set_ylim(0.0, figure_height_pt)
    ax.axis("off")

    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    layout_boxes: list[dict[str, Any]] = []
    metrics_workflow_stages: list[dict[str, Any]] = []
    metrics_summary_panels: list[dict[str, Any]] = []
    text_artists: list[tuple[str, str, Any]] = []

    for layout in selected_stage_layouts:
        region = layout["region"]
        stage_index = int(layout["stage_index"])
        stage_box_id = f"workflow_stage_{stage_index}"
        stage_patch = FancyBboxPatch(
            (region["x0"], region["y0"]),
            region["x1"] - region["x0"],
            region["y1"] - region["y0"],
            boxstyle="round,pad=0.0,rounding_size=18.0",
            linewidth=1.4,
            edgecolor=stage_edge,
            facecolor=stage_fill,
        )
        ax.add_patch(stage_patch)
        panel_boxes.append(
            _flow_box_to_normalized(
                x0=region["x0"],
                y0=region["y0"],
                x1=region["x1"],
                y1=region["y1"],
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=figure_height_pt,
                box_id=stage_box_id,
                box_type="workflow_stage",
            )
        )

        current_y = layout["inner_y1"]
        title_box_id = f"stage_title_{stage_index}"
        title_artist = ax.text(
            layout["inner_x0"],
            current_y,
            layout["title_text"],
            fontsize=layout["title_size"],
            fontweight="bold",
            color=stage_title_color,
            ha="left",
            va="top",
        )
        text_artists.append((title_box_id, "stage_title", title_artist))
        detail_box_id = ""
        if layout["detail_text"]:
            detail_y = current_y - layout["title_height_pt"] - detail_gap_pt
            detail_box_id = f"stage_detail_{stage_index}"
            detail_artist = ax.text(
                layout["inner_x0"],
                detail_y,
                layout["detail_text"],
                fontsize=layout["detail_size"],
                fontweight="normal",
                color=stage_detail_color,
                ha="left",
                va="top",
            )
            text_artists.append((detail_box_id, "stage_detail", detail_artist))

        stage_metric = {
            "stage_id": layout["stage"]["stage_id"],
            "stage_box_id": stage_box_id,
            "title_box_id": title_box_id,
        }
        if detail_box_id:
            stage_metric["detail_box_id"] = detail_box_id
        metrics_workflow_stages.append(stage_metric)

    for arrow_index, (left_region, right_region) in enumerate(
        zip(workflow_stage_regions, workflow_stage_regions[1:], strict=False),
        start=1,
    ):
        start_x = left_region["x1"] + 4.0
        end_x = right_region["x0"] - 4.0
        arrow_y = (left_region["y0"] + left_region["y1"]) / 2.0
        arrow = FancyArrowPatch(
            (start_x, arrow_y),
            (end_x, arrow_y),
            arrowstyle="-|>",
            mutation_scale=14.0,
            linewidth=1.6,
            color=stage_edge,
            shrinkA=0.0,
            shrinkB=0.0,
        )
        ax.add_patch(arrow)
        arrow_height_pt = 18.0
        guide_boxes.append(
            _flow_box_to_normalized(
                x0=start_x,
                y0=arrow_y - arrow_height_pt / 2.0,
                x1=end_x,
                y1=arrow_y + arrow_height_pt / 2.0,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=figure_height_pt,
                box_id=f"stage_arrow_{arrow_index}",
                box_type="arrow_connector",
            )
        )

    for layout in selected_panel_layouts:
        panel = layout["panel"]
        role = str(panel["layout_role"])
        region = layout["region"]
        panel_label = str(panel["panel_label"])
        panel_box_id = f"summary_panel_{panel_label}"
        panel_patch = FancyBboxPatch(
            (region["x0"], region["y0"]),
            region["x1"] - region["x0"],
            region["y1"] - region["y0"],
            boxstyle="round,pad=0.0,rounding_size=18.0",
            linewidth=1.4,
            edgecolor=border_color,
            facecolor=panel_fill_by_role[role],
        )
        ax.add_patch(panel_patch)
        panel_boxes.append(
            _flow_box_to_normalized(
                x0=region["x0"],
                y0=region["y0"],
                x1=region["x1"],
                y1=region["y1"],
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=figure_height_pt,
                box_id=panel_box_id,
                box_type="panel",
            )
        )

        label_x = layout["inner_x0"]
        label_y = layout["inner_y1"]
        panel_label_box_id = f"panel_label_{panel_label}"
        panel_label_artist = ax.text(
            label_x,
            label_y,
            layout["panel_label_text"],
            fontsize=layout["panel_label_size"],
            fontweight="bold",
            color=panel_accent_by_role[role],
            ha="left",
            va="top",
        )
        text_artists.append((panel_label_box_id, "panel_label", panel_label_artist))

        summary_title_box_id = f"summary_title_{panel_label}"
        summary_title_artist = ax.text(
            label_x + layout["panel_label_width_pt"] + label_title_gap_pt,
            label_y,
            layout["summary_title_text"],
            fontsize=layout["summary_title_size"],
            fontweight="bold",
            color=body_color,
            ha="left",
            va="top",
        )
        text_artists.append((summary_title_box_id, "summary_title", summary_title_artist))

        current_y = label_y - layout["header_height_pt"] - header_gap_pt
        panel_metric = {
            "panel_id": panel["panel_id"],
            "panel_label": panel_label,
            "layout_role": role,
            "panel_box_id": panel_box_id,
            "panel_label_box_id": panel_label_box_id,
            "title_box_id": summary_title_box_id,
            "cards": [],
        }
        for card_index, card_layout in enumerate(layout["cards_layout"], start=1):
            card = card_layout["card"]
            label_box_id = f"card_label_{panel_label}_{card_index}"
            value_box_id = f"card_value_{panel_label}_{card_index}"
            label_artist = ax.text(
                layout["inner_x0"],
                current_y,
                card_layout["label_text"],
                fontsize=card_layout["card_label_size"],
                fontweight="bold",
                color=body_color,
                ha="left",
                va="top",
            )
            text_artists.append((label_box_id, "card_label", label_artist))
            value_y = current_y - card_layout["label_height_pt"] - 4.0
            value_artist = ax.text(
                layout["inner_x0"],
                value_y,
                card_layout["value_text"],
                fontsize=card_layout["card_value_size"],
                fontweight="bold",
                color=body_color,
                ha="left",
                va="top",
            )
            text_artists.append((value_box_id, "card_value", value_artist))
            if card_layout["detail_text"]:
                detail_y = value_y - card_layout["value_height_pt"] - detail_gap_pt
                detail_artist = ax.text(
                    layout["inner_x0"],
                    detail_y,
                    card_layout["detail_text"],
                    fontsize=card_layout["card_detail_size"],
                    fontweight="normal",
                    color=stage_detail_color,
                    ha="left",
                    va="top",
                )
                text_artists.append((f"card_detail_{panel_label}_{card_index}", "card_detail", detail_artist))
            panel_metric["cards"].append(
                {
                    "card_id": card["card_id"],
                    "label_box_id": label_box_id,
                    "value_box_id": value_box_id,
                }
            )
            current_y -= card_layout["card_height_pt"] + card_gap_pt
        metrics_summary_panels.append(panel_metric)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for box_id, box_type, artist in text_artists:
        layout_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type=box_type,
            )
        )

    dump_json(
        output_layout_path,
        {
            "template_id": "design_evidence_composite_shell",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "workflow_stages": metrics_workflow_stages,
                "summary_panels": metrics_summary_panels,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=240)
    plt.close(fig)


