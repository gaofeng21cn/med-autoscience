from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch

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


def _render_workflow_fact_sheet_panel(
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

    section_by_role = {
        str(section["layout_role"]): dict(section)
        for section in shell_payload["sections"]
    }
    ordered_roles = ("top_left", "top_right", "bottom_left", "bottom_right")
    ordered_sections = [section_by_role[role] for role in ordered_roles]

    figure_width_pt = 13.2 * 72.0
    figure_height_pt = 8.4 * 72.0
    side_margin_pt = 34.0
    top_margin_pt = 30.0
    bottom_margin_pt = 26.0
    column_gap_pt = 30.0
    row_gap_pt = 26.0
    panel_padding_pt = 18.0
    title_gap_pt = 16.0
    fact_gap_pt = 14.0
    detail_gap_pt = 5.0
    label_title_gap_pt = 12.0
    label_column_ratio = 0.34

    panel_width_pt = (figure_width_pt - side_margin_pt * 2.0 - column_gap_pt) / 2.0
    panel_height_pt = (figure_height_pt - top_margin_pt - bottom_margin_pt - row_gap_pt) / 2.0
    bottom_row_y0 = bottom_margin_pt
    top_row_y0 = bottom_row_y0 + panel_height_pt + row_gap_pt

    panel_regions: dict[str, dict[str, float]] = {
        "top_left": {
            "x0": side_margin_pt,
            "y0": top_row_y0,
            "x1": side_margin_pt + panel_width_pt,
            "y1": top_row_y0 + panel_height_pt,
        },
        "top_right": {
            "x0": side_margin_pt + panel_width_pt + column_gap_pt,
            "y0": top_row_y0,
            "x1": side_margin_pt + panel_width_pt * 2.0 + column_gap_pt,
            "y1": top_row_y0 + panel_height_pt,
        },
        "bottom_left": {
            "x0": side_margin_pt,
            "y0": bottom_row_y0,
            "x1": side_margin_pt + panel_width_pt,
            "y1": bottom_row_y0 + panel_height_pt,
        },
        "bottom_right": {
            "x0": side_margin_pt + panel_width_pt + column_gap_pt,
            "y0": bottom_row_y0,
            "x1": side_margin_pt + panel_width_pt * 2.0 + column_gap_pt,
            "y1": bottom_row_y0 + panel_height_pt,
        },
    }

    role_fill_color = {
        "top_left": palette_color("primary_soft", "#EAF2F5"),
        "top_right": palette_color("secondary_soft", "#F4EEE5"),
        "bottom_left": palette_color("light", "#E7E1D8"),
        "bottom_right": palette_color("contrast_soft", "#F7EBEB"),
    }
    role_accent_color = {
        "top_left": palette_color("primary", "#245A6B"),
        "top_right": palette_color("secondary", "#B89A6D"),
        "bottom_left": palette_color("neutral", "#6B7280"),
        "bottom_right": palette_color("contrast", "#8B3A3A"),
    }
    border_color = palette_color("neutral", "#6B7280")
    title_color = palette_color("primary", "#245A6B")
    body_color = palette_color("neutral", "#374151")
    detail_color = palette_color("neutral", "#6B7280")

    base_section_title_size = max(11.4, read_float(typography, "axis_title_size", 11.0) + 0.8)
    base_fact_label_size = max(9.6, read_float(typography, "tick_size", 10.0))
    base_fact_value_size = max(10.0, read_float(typography, "tick_size", 10.0) + 0.3)
    base_detail_size = max(8.6, read_float(typography, "tick_size", 10.0) - 0.8)
    base_panel_label_size = max(11.4, read_float(typography, "panel_label_size", 11.0) + 0.8)

    def line_height(font_size: float) -> float:
        return font_size * 1.24

    def layout_section(section: dict[str, Any], *, scale: float) -> dict[str, Any]:
        region = panel_regions[str(section["layout_role"])]
        inner_x0 = region["x0"] + panel_padding_pt
        inner_x1 = region["x1"] - panel_padding_pt
        inner_y1 = region["y1"] - panel_padding_pt
        inner_y0 = region["y0"] + panel_padding_pt
        panel_label_size = base_panel_label_size * scale
        section_title_size = base_section_title_size * scale
        fact_label_size = base_fact_label_size * scale
        fact_value_size = base_fact_value_size * scale
        detail_size = base_detail_size * scale

        panel_label_text = str(section["panel_label"])
        label_width_pt = max(
            _measure_flow_text_width_pt(
                panel_label_text,
                font_size=panel_label_size,
                font_weight="bold",
            ),
            panel_label_size * 0.9,
        )
        title_max_width_pt = max(inner_x1 - (inner_x0 + label_width_pt + label_title_gap_pt), 80.0)
        title_lines = _wrap_flow_text_to_width(
            str(section["title"]),
            max_width_pt=title_max_width_pt,
            font_size=section_title_size,
            font_weight="bold",
        )
        title_height_pt = line_height(section_title_size) * max(1, len(title_lines))
        header_height_pt = max(line_height(panel_label_size), title_height_pt)

        facts_layout: list[dict[str, Any]] = []
        label_column_width_pt = max((inner_x1 - inner_x0) * label_column_ratio, 96.0)
        value_column_x0 = inner_x0 + label_column_width_pt + 16.0
        value_column_width_pt = max(inner_x1 - value_column_x0, 80.0)
        total_height_pt = header_height_pt + title_gap_pt

        for fact in section["facts"]:
            label_lines = _wrap_flow_text_to_width(
                str(fact["label"]),
                max_width_pt=label_column_width_pt,
                font_size=fact_label_size,
                font_weight="bold",
            )
            value_lines = _wrap_flow_text_to_width(
                str(fact["value"]),
                max_width_pt=value_column_width_pt,
                font_size=fact_value_size,
                font_weight="bold",
            )
            detail_lines = _wrap_flow_text_to_width(
                str(fact.get("detail") or ""),
                max_width_pt=value_column_width_pt,
                font_size=detail_size,
                font_weight="normal",
            )
            label_height_pt = line_height(fact_label_size) * max(1, len(label_lines))
            value_height_pt = line_height(fact_value_size) * max(1, len(value_lines))
            detail_height_pt = line_height(detail_size) * len(detail_lines) if detail_lines else 0.0
            value_stack_height_pt = value_height_pt + (detail_gap_pt + detail_height_pt if detail_height_pt else 0.0)
            row_height_pt = max(label_height_pt, value_stack_height_pt)
            facts_layout.append(
                {
                    "fact": fact,
                    "label_text": "\n".join(label_lines),
                    "value_text": "\n".join(value_lines),
                    "detail_text": "\n".join(detail_lines),
                    "label_height_pt": label_height_pt,
                    "value_height_pt": value_height_pt,
                    "detail_height_pt": detail_height_pt,
                    "row_height_pt": row_height_pt,
                    "fact_label_size": fact_label_size,
                    "fact_value_size": fact_value_size,
                    "detail_size": detail_size,
                    "label_x": inner_x0,
                    "value_x": value_column_x0,
                }
            )
            total_height_pt += row_height_pt + fact_gap_pt

        if facts_layout:
            total_height_pt -= fact_gap_pt
        return {
            "section": section,
            "region": region,
            "inner_x0": inner_x0,
            "inner_y1": inner_y1,
            "inner_y0": inner_y0,
            "panel_label_text": panel_label_text,
            "panel_label_size": panel_label_size,
            "panel_label_width_pt": label_width_pt,
            "title_text": "\n".join(title_lines),
            "title_size": section_title_size,
            "title_height_pt": title_height_pt,
            "header_height_pt": header_height_pt,
            "facts_layout": facts_layout,
            "total_height_pt": total_height_pt,
        }

    selected_layouts: list[dict[str, Any]] | None = None
    for scale in (1.0, 0.95, 0.90, 0.85, 0.80, 0.75):
        layouts = [layout_section(section, scale=scale) for section in ordered_sections]
        if all(layout["total_height_pt"] <= (layout["region"]["y1"] - layout["region"]["y0"] - panel_padding_pt * 2.0) for layout in layouts):
            selected_layouts = layouts
            break
    if selected_layouts is None:
        raise ValueError("workflow_fact_sheet_panel content does not fit the fixed 2x2 fact-sheet grid")

    fig = plt.figure(figsize=(figure_width_pt / 72.0, figure_height_pt / 72.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, figure_width_pt)
    ax.set_ylim(0.0, figure_height_pt)
    ax.axis("off")

    panel_boxes: list[dict[str, Any]] = []
    layout_boxes: list[dict[str, Any]] = []
    metrics_sections: list[dict[str, Any]] = []
    text_artists: list[tuple[str, str, Any]] = []

    for layout in selected_layouts:
        section = layout["section"]
        region = layout["region"]
        role = str(section["layout_role"])
        panel_label = str(section["panel_label"])
        panel_label_token = panel_label
        panel_box_id = f"panel_{panel_label_token}"
        panel_patch = FancyBboxPatch(
            (region["x0"], region["y0"]),
            region["x1"] - region["x0"],
            region["y1"] - region["y0"],
            boxstyle="round,pad=0.0,rounding_size=18.0",
            linewidth=1.4,
            edgecolor=border_color,
            facecolor=role_fill_color[role],
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
        panel_label_artist = ax.text(
            label_x,
            label_y,
            layout["panel_label_text"],
            fontsize=layout["panel_label_size"],
            fontweight="bold",
            color=role_accent_color[role],
            ha="left",
            va="top",
        )
        text_artists.append((f"panel_label_{panel_label_token}", "panel_label", panel_label_artist))

        title_x = label_x + layout["panel_label_width_pt"] + label_title_gap_pt
        title_artist = ax.text(
            title_x,
            label_y,
            layout["title_text"],
            fontsize=layout["title_size"],
            fontweight="bold",
            color=title_color,
            ha="left",
            va="top",
        )
        text_artists.append((f"section_title_{panel_label_token}", "section_title", title_artist))

        current_y = label_y - layout["header_height_pt"] - title_gap_pt
        section_metric = {
            "section_id": section["section_id"],
            "panel_label": panel_label,
            "layout_role": role,
            "panel_box_id": panel_box_id,
            "title_box_id": f"section_title_{panel_label_token}",
            "panel_label_box_id": f"panel_label_{panel_label_token}",
            "facts": [],
        }
        for fact_index, fact_layout in enumerate(layout["facts_layout"], start=1):
            fact = fact_layout["fact"]
            fact_label_box_id = f"fact_label_{panel_label_token}_{fact_index}"
            fact_value_box_id = f"fact_value_{panel_label_token}_{fact_index}"
            fact_label_artist = ax.text(
                fact_layout["label_x"],
                current_y,
                fact_layout["label_text"],
                fontsize=fact_layout["fact_label_size"],
                fontweight="bold",
                color=body_color,
                ha="left",
                va="top",
            )
            text_artists.append((fact_label_box_id, "fact_label", fact_label_artist))

            fact_value_artist = ax.text(
                fact_layout["value_x"],
                current_y,
                fact_layout["value_text"],
                fontsize=fact_layout["fact_value_size"],
                fontweight="bold",
                color=body_color,
                ha="left",
                va="top",
            )
            text_artists.append((fact_value_box_id, "fact_value", fact_value_artist))

            if fact_layout["detail_text"]:
                detail_y = current_y - fact_layout["value_height_pt"] - detail_gap_pt
                ax.text(
                    fact_layout["value_x"],
                    detail_y,
                    fact_layout["detail_text"],
                    fontsize=fact_layout["detail_size"],
                    fontweight="normal",
                    color=detail_color,
                    ha="left",
                    va="top",
                )

            section_metric["facts"].append(
                {
                    "fact_id": fact["fact_id"],
                    "label_box_id": fact_label_box_id,
                    "value_box_id": fact_value_box_id,
                }
            )
            current_y -= fact_layout["row_height_pt"] + fact_gap_pt
        metrics_sections.append(section_metric)

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
            "template_id": "workflow_fact_sheet_panel",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": [],
            "metrics": {
                "sections": metrics_sections,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=240)
    plt.close(fig)


