from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from ..shared_parts.common import dump_json
from ..shared_parts.flow_layout import (
    _flow_box_to_normalized,
    _measure_flow_text_width_pt,
    _wrap_flow_text_to_width,
)
from ..shared_parts.geometry import _bbox_to_layout_box
from ..shared_parts.rendering import _prepare_python_illustration_output_paths


def _read_float(mapping: dict[str, Any], key: str, default: float) -> float:
    value = mapping.get(key, default)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return float(default)


def _resolve_color(style_roles: dict[str, Any], role_name: str, fallback: str) -> str:
    return str(style_roles.get(role_name) or fallback).strip() or fallback


def _fit_lines(
    text: str,
    *,
    max_width_pt: float,
    preferred_size: float,
    min_size: float,
    font_weight: str,
    max_lines: int,
) -> tuple[tuple[str, ...], float]:
    normalized = " ".join(str(text or "").split())
    font_size = preferred_size
    while font_size >= min_size - 1e-6:
        lines = _wrap_flow_text_to_width(
            normalized,
            max_width_pt=max_width_pt,
            font_size=font_size,
            font_weight=font_weight,
            max_chars=38,
        )
        widest = max(
            (
                _measure_flow_text_width_pt(line, font_size=font_size, font_weight=font_weight)
                for line in lines
            ),
            default=0.0,
        )
        if len(lines) <= max_lines and widest <= max_width_pt + 0.1:
            return lines, font_size
        font_size -= 0.5
    return (
        tuple(
            _wrap_flow_text_to_width(
                normalized,
                max_width_pt=max_width_pt,
                font_size=min_size,
                font_weight=font_weight,
                max_chars=38,
            )
        ),
        min_size,
    )


def _text_height(lines: tuple[str, ...], *, font_size: float) -> float:
    return len(lines) * font_size * 1.22 if lines else 0.0


def _first_card(panel: dict[str, Any]) -> dict[str, Any]:
    rows = list(panel.get("rows") or [])
    for row in rows:
        cards = list(row.get("cards") or []) if isinstance(row, dict) else []
        if cards:
            return dict(cards[0])
    return {"card_id": f"{panel['panel_id']}_message", "title": panel["title"], "value": "", "detail": ""}


def _visual_role(panel: dict[str, Any], panel_index: int) -> str:
    role = str(panel.get("visual_role") or "").strip().lower()
    if role:
        return role
    defaults = ("population", "model_signal", "clinical_use")
    return defaults[panel_index] if panel_index < len(defaults) else "generic"


def _evidence_token(panel: dict[str, Any], card: dict[str, Any]) -> str:
    return (
        str(panel.get("evidence_token") or "").strip()
        or str(card.get("evidence_token") or "").strip()
        or str(card.get("value") or "").strip()
    )


def _draw_visual_glyph(
    *,
    ax: Any,
    glyph_box: dict[str, float],
    visual_role: str,
    accent: str,
    neutral: str,
    soft_fill: str,
    line_width: float,
    canvas_width_pt: float,
    canvas_height_pt: float,
    layout_boxes: list[dict[str, Any]],
    box_id: str,
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (glyph_box["x0"], glyph_box["y0"]),
            glyph_box["x1"] - glyph_box["x0"],
            glyph_box["y1"] - glyph_box["y0"],
            boxstyle="round,pad=0.0,rounding_size=12",
            linewidth=max(0.8, line_width * 0.86),
            edgecolor=accent,
            facecolor="white",
        )
    )
    layout_boxes.append(
        _flow_box_to_normalized(
            **glyph_box,
            canvas_width_pt=canvas_width_pt,
            canvas_height_pt=canvas_height_pt,
            box_id=box_id,
            box_type="visual_glyph",
        )
    )

    x0 = glyph_box["x0"]
    x1 = glyph_box["x1"]
    y0 = glyph_box["y0"]
    y1 = glyph_box["y1"]
    width = x1 - x0
    height = y1 - y0
    cx = (x0 + x1) / 2.0
    cy = (y0 + y1) / 2.0

    if visual_role in {"population", "source_data", "cohort"}:
        record_x = x0 + width * 0.13
        record_y = y0 + height * 0.18
        record_w = width * 0.34
        record_h = height * 0.52
        ax.add_patch(
            FancyBboxPatch(
                (record_x, record_y),
                record_w,
                record_h,
                boxstyle="round,pad=0.0,rounding_size=7",
                linewidth=line_width,
                edgecolor=neutral,
                facecolor=soft_fill,
            )
        )
        for offset in (0.70, 0.54, 0.38):
            ax.plot(
                [record_x + record_w * 0.18, record_x + record_w * 0.82],
                [record_y + record_h * offset, record_y + record_h * offset],
                color=neutral,
                linewidth=max(0.8, line_width * 0.72),
            )
        person_centers = (
            (x0 + width * 0.64, y0 + height * 0.61),
            (x0 + width * 0.77, y0 + height * 0.54),
            (x0 + width * 0.59, y0 + height * 0.42),
            (x0 + width * 0.72, y0 + height * 0.34),
        )
        for person_x, person_y in person_centers:
            ax.add_patch(
                matplotlib.patches.Circle(
                    (person_x, person_y + height * 0.045),
                    radius=height * 0.035,
                    facecolor=accent,
                    edgecolor=accent,
                    linewidth=0.0,
                    alpha=0.92,
                )
            )
            ax.plot(
                [person_x, person_x],
                [person_y - height * 0.035, person_y + height * 0.015],
                color=accent,
                linewidth=max(1.2, line_width * 1.2),
            )
    elif visual_role in {"model_signal", "model", "mechanism", "algorithm"}:
        plot_x0 = x0 + width * 0.16
        plot_y0 = y0 + height * 0.22
        plot_x1 = x1 - width * 0.15
        plot_y1 = y1 - height * 0.22
        ax.plot([plot_x0, plot_x0], [plot_y0, plot_y1], color=neutral, linewidth=line_width)
        ax.plot([plot_x0, plot_x1], [plot_y0, plot_y0], color=neutral, linewidth=line_width)
        curve_x = [plot_x0, plot_x0 + width * 0.18, plot_x0 + width * 0.34, plot_x0 + width * 0.52]
        curve_y = [plot_y0 + height * 0.07, plot_y0 + height * 0.20, plot_y0 + height * 0.34, plot_y0 + height * 0.50]
        ax.plot(curve_x, curve_y, color=accent, linewidth=max(1.4, line_width * 1.55))
        node_y = y0 + height * 0.70
        for node_index, label in enumerate(("X", "f", "Y")):
            node_x = x0 + width * (0.26 + node_index * 0.23)
            ax.add_patch(
                FancyBboxPatch(
                    (node_x - width * 0.055, node_y - height * 0.045),
                    width * 0.11,
                    height * 0.09,
                    boxstyle="round,pad=0.0,rounding_size=5",
                    linewidth=max(0.8, line_width * 0.82),
                    edgecolor=accent,
                    facecolor=soft_fill,
                )
            )
            ax.text(node_x, node_y, label, fontsize=8.8, fontweight="bold", color=accent, ha="center", va="center")
            if node_index < 2:
                ax.add_patch(
                    FancyArrowPatch(
                        (node_x + width * 0.065, node_y),
                        (node_x + width * 0.175, node_y),
                        arrowstyle="-|>",
                        mutation_scale=8.0,
                        linewidth=max(0.8, line_width * 0.82),
                        color=neutral,
                    )
                )
    elif visual_role in {"clinical_use", "decision", "action", "care_path"}:
        center_box = {
            "x0": x0 + width * 0.27,
            "x1": x0 + width * 0.73,
            "y0": y0 + height * 0.50,
            "y1": y0 + height * 0.70,
        }
        ax.add_patch(
            FancyBboxPatch(
                (center_box["x0"], center_box["y0"]),
                center_box["x1"] - center_box["x0"],
                center_box["y1"] - center_box["y0"],
                boxstyle="round,pad=0.0,rounding_size=7",
                linewidth=line_width,
                edgecolor=accent,
                facecolor=soft_fill,
            )
        )
        ax.text(cx, (center_box["y0"] + center_box["y1"]) / 2.0, "Risk", fontsize=8.8, fontweight="bold", color=accent, ha="center", va="center")
        branch_targets = (
            (x0 + width * 0.25, y0 + height * 0.30, "Low"),
            (x0 + width * 0.75, y0 + height * 0.30, "High"),
        )
        for target_x, target_y, label in branch_targets:
            ax.add_patch(
                FancyArrowPatch(
                    (cx, center_box["y0"]),
                    (target_x, target_y + height * 0.07),
                    arrowstyle="-|>",
                    mutation_scale=9.5,
                    linewidth=max(0.9, line_width),
                    color=neutral,
                )
            )
            ax.add_patch(
                FancyBboxPatch(
                    (target_x - width * 0.12, target_y - height * 0.055),
                    width * 0.24,
                    height * 0.11,
                    boxstyle="round,pad=0.0,rounding_size=6",
                    linewidth=max(0.8, line_width * 0.78),
                    edgecolor=accent,
                    facecolor="white",
                )
            )
            ax.text(target_x, target_y, label, fontsize=8.0, color=neutral, ha="center", va="center")
    else:
        node_centers = (
            (x0 + width * 0.25, cy),
            (x0 + width * 0.50, cy),
            (x0 + width * 0.75, cy),
        )
        for index, (node_x, node_y) in enumerate(node_centers):
            ax.add_patch(
                matplotlib.patches.Circle(
                    (node_x, node_y),
                    radius=height * 0.085,
                    facecolor=soft_fill if index != 1 else accent,
                    edgecolor=accent,
                    linewidth=line_width,
                )
            )
            if index < 2:
                ax.add_patch(
                    FancyArrowPatch(
                        (node_x + height * 0.09, node_y),
                        (node_centers[index + 1][0] - height * 0.09, node_y),
                        arrowstyle="-|>",
                        mutation_scale=9.0,
                        linewidth=max(0.9, line_width),
                        color=neutral,
                    )
                )


def _render_square_submission_graphical_abstract(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
) -> None:
    render_context_payload = dict(render_context or {})
    style_roles = dict(render_context_payload.get("style_roles") or {})
    palette = dict(render_context_payload.get("palette") or {})
    typography = dict(render_context_payload.get("typography") or {})
    layout_override = dict(render_context_payload.get("layout_override") or {})
    stroke = dict(render_context_payload.get("stroke") or {})

    _prepare_python_illustration_output_paths(
        output_png_path=output_png_path,
        output_svg_path=output_svg_path,
        layout_sidecar_path=output_layout_path,
    )

    neutral_color = _resolve_color(style_roles, "reference_line", str(palette.get("neutral") or "#667078"))
    primary_color = _resolve_color(style_roles, "model_curve", str(palette.get("primary") or "#1F6F8B"))
    secondary_color = _resolve_color(style_roles, "comparator_curve", str(palette.get("secondary") or "#6C8C7D"))
    contrast_color = str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A"
    soft_panel = str(palette.get("primary_soft") or "#E6F3EF").strip() or "#E6F3EF"
    soft_card = str(palette.get("contrast_soft") or "#E8EEF6").strip() or "#E8EEF6"
    soft_alt = str(palette.get("secondary_soft") or "#F2EEE8").strip() or "#F2EEE8"

    title_size = _read_float(typography, "title_size", 12.5) + 1.8
    panel_title_size = _read_float(typography, "axis_title_size", 11.0) + 1.0
    subtitle_size = max(8.8, _read_float(typography, "tick_size", 10.0) - 0.4)
    card_title_size = max(8.4, _read_float(typography, "tick_size", 10.0) - 0.5)
    card_detail_size = max(7.8, _read_float(typography, "tick_size", 10.0) - 1.0)
    value_size = max(16.0, title_size * 1.35)
    line_width = max(0.9, _read_float(stroke, "secondary_linewidth", 1.8) * 0.66)
    accent_width = max(1.0, _read_float(stroke, "primary_linewidth", 2.2) * 0.62)

    figure_width_pt = _read_float(layout_override, "graphical_abstract_square_width", 7.2) * 72.0
    canvas_width_pt = figure_width_pt
    canvas_height_pt = figure_width_pt
    margin_pt = _read_float(layout_override, "graphical_abstract_square_margin_pt", 26.0)
    panel_gap_pt = _read_float(layout_override, "graphical_abstract_square_panel_gap_pt", 16.0)
    footer_gap_pt = _read_float(layout_override, "graphical_abstract_square_footer_gap_pt", 16.0)
    footer_height_pt = _read_float(layout_override, "graphical_abstract_square_footer_height_pt", 28.0)
    title_gap_pt = _read_float(layout_override, "graphical_abstract_square_title_gap_pt", 16.0)
    panel_padding_pt = _read_float(layout_override, "graphical_abstract_square_panel_padding_pt", 14.0)
    card_padding_pt = _read_float(layout_override, "graphical_abstract_square_card_padding_pt", 10.0)

    panels = list(shell_payload.get("panels") or [])
    footer_pills = list(shell_payload.get("footer_pills") or [])
    panel_count = max(1, len(panels))
    title_lines, title_font_size = _fit_lines(
        str(shell_payload.get("title") or "Graphical abstract"),
        max_width_pt=canvas_width_pt - margin_pt * 2.0,
        preferred_size=title_size,
        min_size=11.0,
        font_weight="bold",
        max_lines=2,
    )
    title_height_pt = _text_height(title_lines, font_size=title_font_size)
    content_top_pt = canvas_height_pt - margin_pt - title_height_pt - title_gap_pt
    content_bottom_pt = margin_pt + footer_height_pt + footer_gap_pt
    panel_height_pt = content_top_pt - content_bottom_pt
    panel_width_pt = (
        canvas_width_pt - margin_pt * 2.0 - panel_gap_pt * max(0, panel_count - 1)
    ) / panel_count

    fig = plt.figure(figsize=(canvas_width_pt / 72.0, canvas_height_pt / 72.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, canvas_width_pt)
    ax.set_ylim(0.0, canvas_height_pt)
    ax.axis("off")

    text_records: list[tuple[Any, str, str]] = []
    layout_boxes: list[dict[str, Any]] = []
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []

    title_artist = ax.text(
        margin_pt,
        canvas_height_pt - margin_pt,
        "\n".join(title_lines),
        fontsize=title_font_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )
    text_records.append((title_artist, "title", "title"))

    panel_fills = (soft_panel, soft_alt, soft_panel)
    soft_glyph_fills = (soft_panel, soft_card, soft_alt)
    accent_colors = (primary_color, contrast_color, secondary_color)
    panel_regions: dict[str, dict[str, float]] = {}

    for panel_index, raw_panel in enumerate(panels):
        panel = dict(raw_panel)
        panel_id = str(panel["panel_id"])
        panel_x0 = margin_pt + panel_index * (panel_width_pt + panel_gap_pt)
        panel_box = {
            "x0": panel_x0,
            "y0": content_bottom_pt,
            "x1": panel_x0 + panel_width_pt,
            "y1": content_top_pt,
        }
        panel_regions[panel_id] = panel_box
        panel_fill = panel_fills[panel_index % len(panel_fills)]
        glyph_fill = soft_glyph_fills[panel_index % len(soft_glyph_fills)]
        accent = accent_colors[panel_index % len(accent_colors)]
        ax.add_patch(
            FancyBboxPatch(
                (panel_box["x0"], panel_box["y0"]),
                panel_width_pt,
                panel_height_pt,
                boxstyle="round,pad=0.0,rounding_size=14",
                linewidth=line_width,
                edgecolor=neutral_color,
                facecolor=panel_fill,
            )
        )
        panel_boxes.append(
            _flow_box_to_normalized(
                **panel_box,
                canvas_width_pt=canvas_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"panel_{panel_id}",
                box_type="panel",
            )
        )

        label_radius = 11.0
        label_center = (
            panel_box["x0"] + panel_padding_pt + label_radius,
            panel_box["y1"] - panel_padding_pt - label_radius,
        )
        ax.add_patch(
            matplotlib.patches.Circle(
                label_center,
                radius=label_radius,
                facecolor="white",
                edgecolor=neutral_color,
                linewidth=line_width,
            )
        )
        layout_boxes.append(
            _flow_box_to_normalized(
                x0=label_center[0] - label_radius,
                y0=label_center[1] - label_radius,
                x1=label_center[0] + label_radius,
                y1=label_center[1] + label_radius,
                canvas_width_pt=canvas_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"panel_label_{panel['panel_label']}",
                box_type="panel_label",
            )
        )
        label_artist = ax.text(
            label_center[0],
            label_center[1],
            str(panel["panel_label"]),
            fontsize=9.5,
            fontweight="bold",
            color=neutral_color,
            ha="center",
            va="center",
        )
        text_records.append((label_artist, f"panel_label_text_{panel['panel_label']}", "panel_label_text"))

        header_x = label_center[0] + label_radius + 8.0
        header_width = max(1.0, panel_box["x1"] - panel_padding_pt - header_x)
        panel_title_lines, panel_title_font = _fit_lines(
            str(panel["title"]),
            max_width_pt=header_width,
            preferred_size=panel_title_size,
            min_size=8.8,
            font_weight="bold",
            max_lines=2,
        )
        subtitle_lines, subtitle_font = _fit_lines(
            str(panel["subtitle"]),
            max_width_pt=panel_width_pt - panel_padding_pt * 2.0,
            preferred_size=subtitle_size,
            min_size=7.8,
            font_weight="normal",
            max_lines=2,
        )
        title_artist = ax.text(
            header_x,
            panel_box["y1"] - panel_padding_pt,
            "\n".join(panel_title_lines),
            fontsize=panel_title_font,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )
        text_records.append((title_artist, f"{panel_id}_title", "panel_title"))
        subtitle_artist = ax.text(
            panel_box["x0"] + panel_padding_pt,
            panel_box["y1"] - panel_padding_pt - label_radius * 2.0 - 7.0,
            "\n".join(subtitle_lines),
            fontsize=subtitle_font,
            fontweight="normal",
            color=neutral_color,
            ha="left",
            va="top",
        )
        text_records.append((subtitle_artist, f"{panel_id}_subtitle", "panel_subtitle"))

        card = _first_card(panel)
        card_height = min(max(panel_height_pt * 0.24, 74.0), 96.0)
        card_box = {
            "x0": panel_box["x0"] + panel_padding_pt,
            "y0": panel_box["y0"] + panel_padding_pt,
            "x1": panel_box["x1"] - panel_padding_pt,
            "y1": panel_box["y0"] + panel_padding_pt + card_height,
        }
        glyph_box = {
            "x0": panel_box["x0"] + panel_padding_pt,
            "y0": card_box["y1"] + 13.0,
            "x1": panel_box["x1"] - panel_padding_pt,
            "y1": panel_box["y1"] - panel_padding_pt - 72.0,
        }
        if glyph_box["y1"] - glyph_box["y0"] < 80.0:
            glyph_box["y0"] = card_box["y1"] + 10.0
            glyph_box["y1"] = min(panel_box["y1"] - panel_padding_pt - 54.0, glyph_box["y0"] + 96.0)
        _draw_visual_glyph(
            ax=ax,
            glyph_box=glyph_box,
            visual_role=_visual_role(panel, panel_index),
            accent=accent,
            neutral=neutral_color,
            soft_fill=glyph_fill,
            line_width=line_width,
            canvas_width_pt=canvas_width_pt,
            canvas_height_pt=canvas_height_pt,
            layout_boxes=layout_boxes,
            box_id=f"{panel_id}_visual_glyph",
        )

        ax.add_patch(
            FancyBboxPatch(
                (card_box["x0"], card_box["y0"]),
                card_box["x1"] - card_box["x0"],
                card_box["y1"] - card_box["y0"],
                boxstyle="round,pad=0.0,rounding_size=10",
                linewidth=accent_width,
                edgecolor=accent,
                facecolor="white",
            )
        )
        layout_boxes.append(
            _flow_box_to_normalized(
                **card_box,
                canvas_width_pt=canvas_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"{panel_id}_{card['card_id']}",
                box_type="card_box",
            )
        )
        card_inner_width = card_box["x1"] - card_box["x0"] - card_padding_pt * 2.0
        card_title_lines, card_title_font = _fit_lines(
            str(card["title"]),
            max_width_pt=card_inner_width,
            preferred_size=card_title_size,
            min_size=7.4,
            font_weight="normal",
            max_lines=2,
        )
        token_lines, token_font = _fit_lines(
            _evidence_token(panel, card),
            max_width_pt=card_inner_width,
            preferred_size=value_size,
            min_size=10.8,
            font_weight="bold",
            max_lines=2,
        )
        detail_lines, detail_font = _fit_lines(
            str(card.get("detail") or ""),
            max_width_pt=card_inner_width,
            preferred_size=card_detail_size,
            min_size=7.0,
            font_weight="normal",
            max_lines=2,
        )
        y_cursor = card_box["y1"] - card_padding_pt
        card_title_artist = ax.text(
            card_box["x0"] + card_padding_pt,
            y_cursor,
            "\n".join(card_title_lines),
            fontsize=card_title_font,
            fontweight="normal",
            color=neutral_color,
            ha="left",
            va="top",
        )
        text_records.append((card_title_artist, f"{panel_id}_{card['card_id']}_title", "card_title"))
        y_cursor -= _text_height(card_title_lines, font_size=card_title_font) + 4.0
        value_artist = ax.text(
            card_box["x0"] + card_padding_pt,
            y_cursor,
            "\n".join(token_lines),
            fontsize=token_font,
            fontweight="bold",
            color=accent,
            ha="left",
            va="top",
        )
        text_records.append((value_artist, f"{panel_id}_{card['card_id']}_value", "card_value"))
        y_cursor -= _text_height(token_lines, font_size=token_font) + 3.0
        if detail_lines and y_cursor > card_box["y0"] + card_padding_pt:
            detail_artist = ax.text(
                card_box["x0"] + card_padding_pt,
                y_cursor,
                "\n".join(detail_lines),
                fontsize=detail_font,
                fontweight="normal",
                color=neutral_color,
                ha="left",
                va="top",
            )
            text_records.append((detail_artist, f"{panel_id}_{card['card_id']}_detail", "card_detail"))

    for panel_index in range(panel_count - 1):
        start_x = margin_pt + (panel_index + 1) * panel_width_pt + panel_index * panel_gap_pt + 2.0
        end_x = start_x + panel_gap_pt - 4.0
        arrow_y = content_bottom_pt + panel_height_pt * 0.52
        arrow_artist = FancyArrowPatch(
            (start_x, arrow_y),
            (end_x, arrow_y),
            arrowstyle="simple",
            mutation_scale=19.0,
            linewidth=0.0,
            color=neutral_color,
            alpha=0.74,
        )
        ax.add_patch(arrow_artist)
        guide_boxes.append(
            _flow_box_to_normalized(
                x0=start_x,
                y0=arrow_y - 8.0,
                x1=end_x,
                y1=arrow_y + 8.0,
                canvas_width_pt=canvas_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"panel_arrow_{panel_index + 1}",
                box_type="arrow_connector",
            )
        )

    footer_y0 = margin_pt
    footer_count = max(1, len(footer_pills))
    footer_slot_width = (canvas_width_pt - margin_pt * 2.0) / footer_count
    for pill_index, pill in enumerate(footer_pills):
        label = str(pill["label"])
        pill_width = min(
            footer_slot_width - 8.0,
            max(86.0, _measure_flow_text_width_pt(label, font_size=subtitle_size, font_weight="normal") + 26.0),
        )
        pill_center_x = margin_pt + footer_slot_width * (pill_index + 0.5)
        pill_x0 = pill_center_x - pill_width / 2.0
        pill_box = {"x0": pill_x0, "y0": footer_y0, "x1": pill_x0 + pill_width, "y1": footer_y0 + footer_height_pt}
        style_role = str(pill.get("style_role") or "neutral").strip().lower()
        edge = {"primary": primary_color, "contrast": contrast_color, "secondary": secondary_color}.get(style_role, neutral_color)
        ax.add_patch(
            FancyBboxPatch(
                (pill_box["x0"], pill_box["y0"]),
                pill_width,
                footer_height_pt,
                boxstyle="round,pad=0.0,rounding_size=13",
                linewidth=max(0.9, line_width),
                edgecolor=edge,
                facecolor="white",
            )
        )
        layout_boxes.append(
            _flow_box_to_normalized(
                **pill_box,
                canvas_width_pt=canvas_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"footer_pill_{pill['pill_id']}",
                box_type="footer_pill",
            )
        )
        pill_artist = ax.text(
            (pill_box["x0"] + pill_box["x1"]) / 2.0,
            (pill_box["y0"] + pill_box["y1"]) / 2.0,
            label,
            fontsize=subtitle_size,
            fontweight="normal",
            color=neutral_color,
            ha="center",
            va="center",
        )
        text_records.append((pill_artist, f"footer_pill_text_{pill['pill_id']}", "footer_pill_text"))

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for artist, box_id, box_type in text_records:
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
            "template_id": "submission_graphical_abstract",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "layout_style": "square_storyline",
                "panel_count": panel_count,
                "panels": panels,
                "footer_pills": footer_pills,
                "visual_roles": [_visual_role(dict(panel), index) for index, panel in enumerate(panels)],
            },
            "render_context": render_context_payload,
        },
    )
    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=240)
    plt.close(fig)
