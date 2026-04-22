from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from ..shared import (
    _bbox_to_layout_box,
    _build_submission_graphical_abstract_arrow_lane_spec,
    _choose_shared_submission_graphical_abstract_arrow_lane,
    _flow_box_to_normalized,
    _measure_flow_text_width_pt,
    _prepare_python_illustration_output_paths,
    _wrap_figure_title_to_width,
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


def _render_submission_graphical_abstract(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
) -> None:
    def read_float(mapping: dict[str, Any], key: str, default: float) -> float:
        value = mapping.get(key, default)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return float(default)

    def resolve_color(role_name: str, fallback: str) -> str:
        return str(style_roles.get(role_name) or fallback).strip() or fallback

    def fit_wrapped_text(
        text: str,
        *,
        preferred: float,
        min_size: float,
        max_width_pt: float,
        font_weight: str,
        max_lines: int,
    ) -> tuple[tuple[str, ...], float, bool]:
        normalized = " ".join(str(text or "").split())
        if not normalized:
            return tuple(), preferred, False
        font_size = preferred
        while font_size >= min_size - 1e-6:
            lines = _wrap_flow_text_to_width(
                normalized,
                max_width_pt=max_width_pt,
                font_size=font_size,
                font_weight=font_weight,
            )
            widest_line_pt = max(
                (
                    _measure_flow_text_width_pt(line, font_size=font_size, font_weight=font_weight)
                    for line in lines
                ),
                default=0.0,
            )
            if len(lines) <= max_lines and widest_line_pt <= max_width_pt + 0.1:
                return lines, font_size, False
            font_size -= 0.5
        resolved_font_size = max(min_size, 1.0)
        resolved_lines = _wrap_flow_text_to_width(
            normalized,
            max_width_pt=max_width_pt,
            font_size=resolved_font_size,
            font_weight=font_weight,
        )
        widest_line_pt = max(
            (
                _measure_flow_text_width_pt(line, font_size=resolved_font_size, font_weight=font_weight)
                for line in resolved_lines
            ),
            default=0.0,
        )
        overflowed = len(resolved_lines) > max_lines or widest_line_pt > max_width_pt + 0.1
        return resolved_lines, resolved_font_size, overflowed

    def text_block_height(lines: tuple[str, ...], *, font_size: float, extra_gap: float = 0.0) -> float:
        if not lines:
            return 0.0
        return len(lines) * font_size * 1.22 + extra_gap

    def row_width_weights(cards: list[dict[str, Any]]) -> list[float]:
        if len(cards) <= 1:
            return [1.0]
        first_score = max(
            len(str(cards[0]["title"])),
            len(str(cards[0]["detail"])),
            int(len(str(cards[0]["value"])) * 1.2),
        )
        second_score = max(
            len(str(cards[1]["title"])),
            len(str(cards[1]["detail"])),
            int(len(str(cards[1]["value"])) * 1.2),
        )
        total = max(float(first_score + second_score), 1.0)
        first_ratio = min(0.66, max(0.42, first_score / total))
        return [first_ratio, 1.0 - first_ratio]

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

    neutral_color = resolve_color("reference_line", str(palette.get("neutral") or "#7B8794"))
    primary_color = resolve_color("model_curve", str(palette.get("primary") or "#5F766B"))
    secondary_color = resolve_color("comparator_curve", str(palette.get("secondary") or "#B9AD9C"))
    contrast_color = str(palette.get("contrast") or "#2F5D8A").strip() or "#2F5D8A"
    audit_color = str(palette.get("audit") or "#B57F7F").strip() or "#B57F7F"
    soft_fill_by_role = {
        "neutral": str(palette.get("light") or "#E7E1D8").strip() or "#E7E1D8",
        "primary": str(palette.get("primary_soft") or "#EEF3F1").strip() or "#EEF3F1",
        "secondary": str(palette.get("secondary_soft") or "#F4EFE8").strip() or "#F4EFE8",
        "contrast": str(palette.get("contrast_soft") or "#E6EDF5").strip() or "#E6EDF5",
        "audit": str(palette.get("audit_soft") or "#F5ECE8").strip() or "#F5ECE8",
    }
    edge_by_role = {
        "neutral": neutral_color,
        "primary": primary_color,
        "secondary": secondary_color,
        "contrast": contrast_color,
        "audit": audit_color,
    }

    title_size = read_float(typography, "title_size", 12.5) + 1.0
    panel_title_size = read_float(typography, "axis_title_size", 11.0) + 1.2
    subtitle_size = max(10.0, read_float(typography, "tick_size", 10.0) + 0.1)
    card_title_size = max(10.0, read_float(typography, "tick_size", 10.0) + 0.6)
    card_detail_size = max(8.8, read_float(typography, "tick_size", 10.0) - 0.4)
    panel_label_size = max(11.2, read_float(typography, "panel_label_size", 11.0) + 0.6)
    value_font_preferred = max(20.0, read_float(typography, "title_size", 12.5) * 2.35)
    value_font_min = max(14.0, read_float(typography, "axis_title_size", 11.0) + 3.0)

    figure_width_pt = read_float(layout_override, "figure_width", 15.4) * 72.0
    side_margin_pt = read_float(layout_override, "figure_side_margin_pt", 30.0)
    panel_gap_pt = read_float(layout_override, "panel_gap_pt", 24.0)
    panel_padding_pt = read_float(layout_override, "panel_padding_pt", 18.0)
    card_padding_pt = read_float(layout_override, "card_padding_pt", 14.0)
    card_gap_pt = read_float(layout_override, "card_gap_pt", 12.0)
    row_gap_pt = read_float(layout_override, "row_gap_pt", 12.0)
    footer_gap_pt = read_float(layout_override, "footer_gap_pt", 16.0)
    footer_pill_height_pt = read_float(layout_override, "footer_pill_height_pt", 28.0)
    top_margin_pt = read_float(layout_override, "top_margin_pt", 22.0)
    title_gap_pt = read_float(layout_override, "title_gap_pt", 16.0)
    bottom_margin_pt = read_float(layout_override, "bottom_margin_pt", 22.0)
    panel_line_width = max(0.9, read_float(stroke, "secondary_linewidth", 1.8) * 0.75)
    accent_line_width = max(1.0, read_float(stroke, "primary_linewidth", 2.2) * 0.58)

    panels_payload = list(shell_payload.get("panels") or [])
    footer_pills = list(shell_payload.get("footer_pills") or [])
    panel_width_pt = (figure_width_pt - side_margin_pt * 2.0 - panel_gap_pt * 2.0) / 3.0
    card_full_width_pt = panel_width_pt - panel_padding_pt * 2.0

    def build_card_spec(
        card: dict[str, Any],
        *,
        available_width_pt: float,
        max_value_lines: int,
    ) -> dict[str, Any]:
        inner_width_pt = max(available_width_pt - card_padding_pt * 2.0, 1.0)
        title_lines = _wrap_flow_text_to_width(
            str(card["title"]),
            max_width_pt=inner_width_pt,
            font_size=card_title_size,
            font_weight="normal",
        )
        detail_lines = _wrap_flow_text_to_width(
            str(card.get("detail") or ""),
            max_width_pt=inner_width_pt,
            font_size=card_detail_size,
            font_weight="normal",
        )
        value_lines, value_font_size, value_overflowed = fit_wrapped_text(
            str(card["value"]),
            preferred=value_font_preferred,
            min_size=value_font_min,
            max_width_pt=inner_width_pt,
            font_weight="bold",
            max_lines=max_value_lines,
        )
        title_height_pt = text_block_height(title_lines, font_size=card_title_size, extra_gap=5.0)
        value_height_pt = text_block_height(value_lines, font_size=value_font_size, extra_gap=0.0)
        detail_height_pt = text_block_height(detail_lines, font_size=card_detail_size, extra_gap=0.0)
        card_height_pt = card_padding_pt * 2.0 + title_height_pt + value_height_pt
        if detail_lines:
            card_height_pt += 7.0 + detail_height_pt
        return {
            "card": card,
            "width_pt": available_width_pt,
            "height_pt": card_height_pt,
            "title_lines": title_lines,
            "detail_lines": detail_lines,
            "value_lines": value_lines,
            "value_font_size": value_font_size,
            "overflowed": value_overflowed,
        }

    def build_row_spec(cards: list[dict[str, Any]]) -> dict[str, Any]:
        if len(cards) == 1:
            row_card_specs = [
                build_card_spec(
                    cards[0],
                    available_width_pt=card_full_width_pt,
                    max_value_lines=3,
                )
            ]
            return {
                "layout_mode": "single",
                "cards": row_card_specs,
                "height_pt": row_card_specs[0]["height_pt"],
                "row_internal_gap_pt": 0.0,
            }

        weights = row_width_weights(cards)
        horizontal_widths = [
            card_full_width_pt * weights[index] - card_gap_pt / 2.0
            for index in range(len(cards))
        ]
        horizontal_specs = [
            build_card_spec(card, available_width_pt=horizontal_widths[index], max_value_lines=2)
            for index, card in enumerate(cards)
        ]
        if not any(card_spec["overflowed"] for card_spec in horizontal_specs):
            return {
                "layout_mode": "horizontal",
                "cards": horizontal_specs,
                "height_pt": max(card_spec["height_pt"] for card_spec in horizontal_specs),
                "row_internal_gap_pt": card_gap_pt,
            }

        stacked_specs = [
            build_card_spec(card, available_width_pt=card_full_width_pt, max_value_lines=3)
            for card in cards
        ]
        stacked_overflow_ids = [str(spec["card"]["card_id"]) for spec in stacked_specs if spec["overflowed"]]
        if stacked_overflow_ids:
            joined_ids = ", ".join(stacked_overflow_ids)
            raise ValueError(
                "submission_graphical_abstract could not fit the following card values even after stacked layout: "
                f"{joined_ids}"
            )
        return {
            "layout_mode": "stacked",
            "cards": stacked_specs,
            "height_pt": (
                sum(card_spec["height_pt"] for card_spec in stacked_specs)
                + card_gap_pt * max(0, len(stacked_specs) - 1)
            ),
            "row_internal_gap_pt": card_gap_pt,
        }

    panel_specs: list[dict[str, Any]] = []
    for panel in panels_payload:
        panel_title_lines = _wrap_flow_text_to_width(
            str(panel["title"]),
            max_width_pt=panel_width_pt - panel_padding_pt * 2.0 - 32.0,
            font_size=panel_title_size,
            font_weight="bold",
        )
        subtitle_lines = _wrap_flow_text_to_width(
            str(panel["subtitle"]),
            max_width_pt=panel_width_pt - panel_padding_pt * 2.0,
            font_size=subtitle_size,
            font_weight="normal",
        )
        header_height_pt = text_block_height(panel_title_lines, font_size=panel_title_size, extra_gap=6.0)
        header_height_pt += text_block_height(subtitle_lines, font_size=subtitle_size, extra_gap=10.0)
        row_specs: list[dict[str, Any]] = []
        for row in panel["rows"]:
            row_specs.append(build_row_spec(list(row["cards"])))
        content_height_pt = header_height_pt
        if row_specs:
            content_height_pt += sum(item["height_pt"] for item in row_specs) + row_gap_pt * max(0, len(row_specs) - 1)
        panel_specs.append(
            {
                "panel": panel,
                "panel_title_lines": panel_title_lines,
                "subtitle_lines": subtitle_lines,
                "header_height_pt": header_height_pt,
                "row_specs": row_specs,
                "content_height_pt": content_height_pt,
            }
        )

    panel_height_pt = max(spec["content_height_pt"] for spec in panel_specs) + panel_padding_pt * 2.0
    title_text, title_line_count = _wrap_figure_title_to_width(
        str(shell_payload.get("title") or "").strip(),
        max_width_pt=figure_width_pt - side_margin_pt * 2.0,
        font_size=title_size,
    )
    title_height_pt = max(title_line_count, 1) * title_size * 1.18
    canvas_height_pt = (
        top_margin_pt
        + title_height_pt
        + title_gap_pt
        + panel_height_pt
        + footer_gap_pt
        + footer_pill_height_pt
        + bottom_margin_pt
    )

    fig = plt.figure(figsize=(figure_width_pt / 72.0, canvas_height_pt / 72.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, figure_width_pt)
    ax.set_ylim(0.0, canvas_height_pt)
    ax.axis("off")

    title_artist = ax.text(
        side_margin_pt,
        canvas_height_pt - top_margin_pt,
        title_text,
        fontsize=title_size,
        fontweight="bold",
        color=neutral_color,
        ha="left",
        va="top",
    )

    panel_y0 = bottom_margin_pt + footer_pill_height_pt + footer_gap_pt
    footer_y0 = bottom_margin_pt
    text_layout_records: list[tuple[Any, str, str]] = [(title_artist, "title", "title")]
    layout_boxes: list[dict[str, Any]] = []
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    panel_regions: dict[str, dict[str, float]] = {}
    panel_occupied_regions: dict[str, list[dict[str, float]]] = {}
    arrow_artists: list[tuple[str, Any]] = []

    def add_text_box(artist: Any, *, box_id: str, box_type: str) -> None:
        text_layout_records.append((artist, box_id, box_type))

    def draw_graphical_abstract_card(*, panel_id: str, card_spec: dict[str, Any], card_box: dict[str, float]) -> None:
        card = dict(card_spec["card"])
        accent_role = str(card.get("accent_role") or "neutral").strip().lower()
        ax.add_patch(
            FancyBboxPatch(
                (card_box["x0"], card_box["y0"]),
                card_box["x1"] - card_box["x0"],
                card_box["y1"] - card_box["y0"],
                boxstyle="round,pad=0.0,rounding_size=14",
                linewidth=max(0.9, accent_line_width),
                edgecolor=edge_by_role.get(accent_role, neutral_color),
                facecolor=soft_fill_by_role.get(accent_role, soft_fill_by_role["neutral"]),
            )
        )
        layout_boxes.append(
            _flow_box_to_normalized(
                **card_box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"{panel_id}_{card['card_id']}",
                box_type="card_box",
            )
        )
        text_x = card_box["x0"] + card_padding_pt
        y_cursor = card_box["y1"] - card_padding_pt
        title_artist = ax.text(
            text_x,
            y_cursor,
            "\n".join(card_spec["title_lines"]),
            fontsize=card_title_size,
            fontweight="normal",
            color=neutral_color,
            ha="left",
            va="top",
        )
        add_text_box(title_artist, box_id=f"{panel_id}_{card['card_id']}_title", box_type="card_title")
        y_cursor -= text_block_height(card_spec["title_lines"], font_size=card_title_size, extra_gap=4.0)
        value_artist = ax.text(
            text_x,
            y_cursor,
            "\n".join(card_spec["value_lines"]),
            fontsize=card_spec["value_font_size"],
            fontweight="bold",
            color=edge_by_role.get(accent_role, neutral_color),
            ha="left",
            va="top",
        )
        add_text_box(value_artist, box_id=f"{panel_id}_{card['card_id']}_value", box_type="card_value")
        y_cursor -= text_block_height(card_spec["value_lines"], font_size=card_spec["value_font_size"], extra_gap=0.0)
        if card_spec["detail_lines"]:
            y_cursor -= 7.0
            detail_artist = ax.text(
                text_x,
                y_cursor,
                "\n".join(card_spec["detail_lines"]),
                fontsize=card_detail_size,
                fontweight="normal",
                color=neutral_color,
                ha="left",
                va="top",
            )
            add_text_box(
                detail_artist,
                box_id=f"{panel_id}_{card['card_id']}_detail",
                box_type="card_detail",
            )

    for panel_index, panel_spec in enumerate(panel_specs):
        panel = dict(panel_spec["panel"])
        panel_x0 = side_margin_pt + panel_index * (panel_width_pt + panel_gap_pt)
        panel_box = {
            "x0": panel_x0,
            "y0": panel_y0,
            "x1": panel_x0 + panel_width_pt,
            "y1": panel_y0 + panel_height_pt,
        }
        panel_regions[str(panel["panel_id"])] = panel_box
        panel_occupied_regions[str(panel["panel_id"])] = []
        panel_fill = str(palette.get("secondary_soft") or palette.get("light") or "#F4EFE8").strip() or "#F4EFE8"
        ax.add_patch(
            FancyBboxPatch(
                (panel_box["x0"], panel_box["y0"]),
                panel_width_pt,
                panel_height_pt,
                boxstyle="round,pad=0.0,rounding_size=18",
                linewidth=panel_line_width,
                edgecolor=neutral_color,
                facecolor=panel_fill,
            )
        )
        panel_boxes.append(
            _flow_box_to_normalized(
                **panel_box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"panel_{panel['panel_id']}",
                box_type="panel",
            )
        )

        label_center_x = panel_box["x0"] + panel_padding_pt + 14.0
        label_center_y = panel_box["y1"] - panel_padding_pt - 14.0
        label_radius = 14.0
        ax.add_patch(
            matplotlib.patches.Circle(
                (label_center_x, label_center_y),
                radius=label_radius,
                facecolor="white",
                edgecolor=neutral_color,
                linewidth=max(0.9, panel_line_width * 0.9),
            )
        )
        layout_boxes.append(
            _flow_box_to_normalized(
                x0=label_center_x - label_radius,
                y0=label_center_y - label_radius,
                x1=label_center_x + label_radius,
                y1=label_center_y + label_radius,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"panel_label_{panel['panel_label']}",
                box_type="panel_label",
            )
        )
        label_artist = ax.text(
            label_center_x,
            label_center_y,
            str(panel["panel_label"]),
            fontsize=panel_label_size,
            fontweight="bold",
            color=neutral_color,
            ha="center",
            va="center",
        )
        add_text_box(label_artist, box_id=f"panel_label_text_{panel['panel_label']}", box_type="panel_label_text")

        title_x = label_center_x + label_radius + 10.0
        title_y = panel_box["y1"] - panel_padding_pt
        panel_title_artist = ax.text(
            title_x,
            title_y,
            "\n".join(panel_spec["panel_title_lines"]),
            fontsize=panel_title_size,
            fontweight="bold",
            color=neutral_color,
            ha="left",
            va="top",
        )
        add_text_box(panel_title_artist, box_id=f"{panel['panel_id']}_title", box_type="panel_title")
        panel_title_height_pt = text_block_height(panel_spec["panel_title_lines"], font_size=panel_title_size)
        subtitle_y = title_y - panel_title_height_pt - 4.0
        subtitle_artist = ax.text(
            title_x,
            subtitle_y,
            "\n".join(panel_spec["subtitle_lines"]),
            fontsize=subtitle_size,
            fontweight="normal",
            color=neutral_color,
            ha="left",
            va="top",
        )
        add_text_box(subtitle_artist, box_id=f"{panel['panel_id']}_subtitle", box_type="panel_subtitle")

        current_top = panel_box["y1"] - panel_padding_pt - panel_spec["header_height_pt"]
        panel_occupied_regions[str(panel["panel_id"])].append(
            {
                "x0": panel_box["x0"] + panel_padding_pt,
                "y0": current_top,
                "x1": panel_box["x1"] - panel_padding_pt,
                "y1": panel_box["y1"] - panel_padding_pt,
            }
        )
        for row_index, row_spec in enumerate(panel_spec["row_specs"]):
            row_cards = list(row_spec["cards"])
            layout_mode = str(row_spec.get("layout_mode") or "horizontal")
            if layout_mode == "stacked":
                row_top = current_top
                for card_index, card_spec in enumerate(row_cards):
                    card_y1 = row_top
                    card_y0 = card_y1 - card_spec["height_pt"]
                    card_box = {
                        "x0": panel_box["x0"] + panel_padding_pt,
                        "y0": card_y0,
                        "x1": panel_box["x0"] + panel_padding_pt + card_spec["width_pt"],
                        "y1": card_y1,
                    }
                    draw_graphical_abstract_card(
                        panel_id=str(panel["panel_id"]),
                        card_spec=card_spec,
                        card_box=card_box,
                    )
                    panel_occupied_regions[str(panel["panel_id"])].append(dict(card_box))
                    row_top = card_y0 - (
                        row_spec["row_internal_gap_pt"] if card_index < len(row_cards) - 1 else 0.0
                    )
            else:
                card_y1 = current_top
                card_y0 = card_y1 - row_spec["height_pt"]
                x_cursor = panel_box["x0"] + panel_padding_pt
                for card_index, card_spec in enumerate(row_cards):
                    card_box = {
                        "x0": x_cursor,
                        "y0": card_y0,
                        "x1": x_cursor + card_spec["width_pt"],
                        "y1": card_y1,
                    }
                    draw_graphical_abstract_card(
                        panel_id=str(panel["panel_id"]),
                        card_spec=card_spec,
                        card_box=card_box,
                    )
                    panel_occupied_regions[str(panel["panel_id"])].append(dict(card_box))
                    x_cursor = card_box["x1"] + (
                        row_spec["row_internal_gap_pt"] if card_index < len(row_cards) - 1 else 0.0
                    )
            current_top = card_y0 - (row_gap_pt if row_index < len(panel_spec["row_specs"]) - 1 else 0.0)

    ordered_panels = [panel_regions[str(panel["panel_id"])] for panel in panels_payload]
    arrow_pair_specs: list[tuple[int, dict[str, float], dict[str, float], dict[str, Any]]] = []
    for index, (left_panel, right_panel) in enumerate(zip(ordered_panels, ordered_panels[1:], strict=False), start=1):
        left_panel_id = str(panels_payload[index - 1]["panel_id"])
        right_panel_id = str(panels_payload[index]["panel_id"])
        arrow_half_height_pt = max(12.0, min(16.0, panel_gap_pt * 0.58))
        lane_spec = _build_submission_graphical_abstract_arrow_lane_spec(
            left_panel_box=left_panel,
            right_panel_box=right_panel,
            left_occupied_boxes=tuple(panel_occupied_regions[left_panel_id]),
            right_occupied_boxes=tuple(panel_occupied_regions[right_panel_id]),
            clearance_pt=max(6.0, card_gap_pt * 0.45),
            arrow_half_height_pt=arrow_half_height_pt,
            edge_proximity_pt=max(panel_padding_pt + card_padding_pt * 2.0, panel_width_pt * 0.24),
        )
        arrow_pair_specs.append((index, left_panel, right_panel, lane_spec))

    shared_arrow_y = _choose_shared_submission_graphical_abstract_arrow_lane(
        [lane_spec for _, _, _, lane_spec in arrow_pair_specs]
    )
    for index, left_panel, right_panel, _lane_spec in arrow_pair_specs:
        x_left = left_panel["x1"] + 5.0
        x_right = right_panel["x0"] - 5.0
        arrow_artist = FancyArrowPatch(
            (x_left, shared_arrow_y),
            (x_right, shared_arrow_y),
            arrowstyle="simple",
            mutation_scale=max(24.0, min(34.0, panel_gap_pt * 1.35)),
            linewidth=0.0,
            color=neutral_color,
            alpha=0.72,
        )
        ax.add_patch(arrow_artist)
        arrow_artists.append((f"panel_arrow_{index}", arrow_artist))

    for pill in footer_pills:
        panel_box = panel_regions.get(str(pill["panel_id"]))
        if panel_box is None:
            continue
        label = str(pill["label"])
        style_role = str(pill.get("style_role") or "neutral").strip().lower()
        pill_width_pt = max(146.0, _measure_flow_text_width_pt(label, font_size=subtitle_size, font_weight="normal") + 38.0)
        pill_x0 = ((panel_box["x0"] + panel_box["x1"]) / 2.0) - pill_width_pt / 2.0
        pill_box = {
            "x0": pill_x0,
            "y0": footer_y0,
            "x1": pill_x0 + pill_width_pt,
            "y1": footer_y0 + footer_pill_height_pt,
        }
        ax.add_patch(
            FancyBboxPatch(
                (pill_box["x0"], pill_box["y0"]),
                pill_width_pt,
                footer_pill_height_pt,
                boxstyle="round,pad=0.0,rounding_size=14",
                linewidth=max(0.8, panel_line_width * 0.9),
                edgecolor=edge_by_role.get(style_role, neutral_color),
                facecolor="white",
            )
        )
        layout_boxes.append(
            _flow_box_to_normalized(
                **pill_box,
                canvas_width_pt=figure_width_pt,
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
        add_text_box(pill_artist, box_id=f"footer_pill_text_{pill['pill_id']}", box_type="footer_pill_text")

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for box_id, artist in arrow_artists:
        guide_boxes.append(
            _bbox_to_layout_box(
                figure=fig,
                bbox=artist.get_window_extent(renderer=renderer),
                box_id=box_id,
                box_type="arrow_connector",
            )
        )
    for artist, box_id, box_type in text_layout_records:
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
                "panels": panels_payload,
                "footer_pills": footer_pills,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=240)
    plt.close(fig)


