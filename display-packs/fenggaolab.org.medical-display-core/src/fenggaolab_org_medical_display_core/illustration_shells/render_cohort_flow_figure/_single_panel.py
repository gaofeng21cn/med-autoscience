from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

from ...shared import _flow_box_to_normalized, _flow_union_box, _wrap_flow_text_to_width, dump_json


def _render_single_panel_cards(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    output_pdf_path: Path | None = None,
    steps: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    endpoint_inventory: list[dict[str, Any]],
    design_panels: list[dict[str, Any]],
    comparison_summary: dict[str, Any],
    layout_override: dict[str, Any],
    side_margin_pt: float,
    figure_width_pt: float,
    flow_main_fill: str,
    flow_main_edge: str,
    flow_secondary_fill: str,
    flow_secondary_edge: str,
    flow_context_fill: str,
    flow_primary_edge: str,
    flow_title_text: str,
    flow_body_text: str,
    flow_connector: str,
    base_card_title_size: float,
    base_label_size: float,
    base_detail_size: float,
    base_secondary_linewidth: float,
    base_connector_linewidth: float,
    render_context_payload: dict[str, Any],
    read_float: Callable[[dict[str, Any], str, float], float],
) -> None:
    comparison_title = str(comparison_summary.get("title") or "Shared descriptive comparison").strip()
    comparison_body = str(
        comparison_summary.get("body")
        or "The three surveys define the historical patient, contemporary patient, and contemporary clinician surfaces used throughout the main manuscript displays."
    ).strip()
    top_margin_pt = read_float(layout_override, "single_panel_top_margin_pt", 56.0)
    bottom_margin_single_panel_pt = read_float(layout_override, "single_panel_bottom_margin_pt", 28.0)
    card_gap_pt = read_float(layout_override, "single_panel_card_gap_pt", 32.0)
    card_height_pt = read_float(layout_override, "single_panel_card_height_pt", 212.0)
    header_height_pt = read_float(layout_override, "single_panel_card_header_height_pt", 54.0)
    summary_gap_pt = read_float(layout_override, "single_panel_summary_gap_pt", 38.0)
    summary_height_pt = read_float(layout_override, "single_panel_summary_height_pt", 132.0)
    summary_header_height_pt = read_float(layout_override, "single_panel_summary_header_height_pt", 42.0)
    step_count = max(1, len(steps))
    available_width_pt = max(420.0, figure_width_pt - side_margin_pt * 2.0)
    default_card_width_pt = (available_width_pt - max(0, step_count - 1) * card_gap_pt) / step_count
    card_width_pt = read_float(layout_override, "single_panel_card_width_pt", default_card_width_pt)
    card_width_pt = min(card_width_pt, default_card_width_pt)
    cards_total_width_pt = card_width_pt * step_count + max(0, step_count - 1) * card_gap_pt
    card_start_x = (figure_width_pt - cards_total_width_pt) / 2.0
    comparison_width_pt = min(
        read_float(layout_override, "single_panel_summary_width_pt", min(available_width_pt, 520.0)),
        available_width_pt,
    )
    comparison_x0 = (figure_width_pt - comparison_width_pt) / 2.0
    comparison_y0 = bottom_margin_single_panel_pt
    card_y0 = comparison_y0 + summary_height_pt + summary_gap_pt
    canvas_height_pt = card_y0 + card_height_pt + top_margin_pt

    figure_width_in = figure_width_pt / 72.0
    figure_height_in = canvas_height_pt / 72.0
    fig, ax = plt.subplots(figsize=(figure_width_in, figure_height_in))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0.0, figure_width_pt)
    ax.set_ylim(0.0, canvas_height_pt)
    ax.axis("off")

    layout_boxes: list[dict[str, Any]] = []
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []
    flow_nodes: list[dict[str, Any]] = []
    card_boxes: list[dict[str, float]] = []

    body_number_size = max(base_card_title_size + 17.0, 27.0)
    body_label_size = max(base_label_size + 2.5, 13.0)
    role_label_size = max(base_detail_size + 2.2, 11.5)

    for index, step in enumerate(steps):
        x0 = card_start_x + index * (card_width_pt + card_gap_pt)
        x1 = x0 + card_width_pt
        y1 = card_y0 + card_height_pt
        y0 = card_y0
        outer_patch = FancyBboxPatch(
            (x0, y0),
            card_width_pt,
            card_height_pt,
            boxstyle="round,pad=0.0,rounding_size=20",
            facecolor=flow_main_fill,
            edgecolor=flow_main_edge,
            linewidth=max(1.2, base_secondary_linewidth),
        )
        ax.add_patch(outer_patch)
        ax.add_patch(
            Rectangle(
                (x0, y1 - header_height_pt),
                card_width_pt,
                header_height_pt,
                facecolor=flow_context_fill,
                edgecolor="none",
            )
        )
        title_lines = _wrap_flow_text_to_width(
            str(step["label"]),
            max_width_pt=card_width_pt - 28.0,
            font_size=max(base_card_title_size + 0.6, 13.0),
            font_weight="bold",
            max_chars=24,
        )
        ax.text(
            (x0 + x1) / 2.0,
            y1 - header_height_pt / 2.0,
            "\n".join(title_lines),
            fontsize=max(base_card_title_size + 0.6, 13.0),
            fontweight="bold",
            color=flow_title_text,
            ha="center",
            va="center",
        )
        ax.text(
            (x0 + x1) / 2.0,
            y0 + card_height_pt * 0.58,
            f"n={step['n']}",
            fontsize=body_number_size,
            fontweight="bold",
            color=flow_primary_edge,
            ha="center",
            va="center",
        )
        columns = step.get("columns")
        if isinstance(columns, int):
            ax.text(
                (x0 + x1) / 2.0,
                y0 + card_height_pt * 0.40,
                f"{columns} columns",
                fontsize=body_label_size,
                color=flow_body_text,
                ha="center",
                va="center",
            )
        role_label = str(step.get("role_label") or step.get("detail") or "").strip()
        if role_label:
            role_lines = _wrap_flow_text_to_width(
                role_label,
                max_width_pt=card_width_pt - 34.0,
                font_size=role_label_size,
                font_weight="normal",
                max_chars=28,
            )
            ax.text(
                (x0 + x1) / 2.0,
                y0 + 26.0,
                "\n".join(role_lines),
                fontsize=role_label_size,
                color=flow_body_text,
                ha="center",
                va="bottom",
            )
        card_box = {"x0": x0, "y0": y0, "x1": x1, "y1": y1}
        card_boxes.append(card_box)
        layout_boxes.append(
            _flow_box_to_normalized(
                **card_box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"survey_card_{step['step_id']}",
                box_type="survey_card",
            )
        )
        flow_nodes.append(
            {
                "box_id": f"survey_card_{step['step_id']}",
                "box_type": "survey_card",
                "line_count": len(title_lines) + (1 if role_label else 0) + (1 if isinstance(columns, int) else 0) + 1,
                "max_line_chars": max(
                    [len(str(step["label"])), len(f"n={step['n']}"), len(str(columns) + " columns") if isinstance(columns, int) else 0]
                    + [len(role_label)]
                ),
                "rendered_height_pt": card_height_pt,
                "rendered_width_pt": card_width_pt,
                "padding_pt": 18.0,
            }
        )

    comparison_box = {
        "x0": comparison_x0,
        "y0": comparison_y0,
        "x1": comparison_x0 + comparison_width_pt,
        "y1": comparison_y0 + summary_height_pt,
    }
    ax.add_patch(
        FancyBboxPatch(
            (comparison_box["x0"], comparison_box["y0"]),
            comparison_width_pt,
            summary_height_pt,
            boxstyle="round,pad=0.0,rounding_size=18",
            facecolor=flow_secondary_fill,
            edgecolor=flow_secondary_edge,
            linewidth=max(1.2, base_secondary_linewidth),
        )
    )
    ax.add_patch(
        Rectangle(
            (comparison_box["x0"], comparison_box["y1"] - summary_header_height_pt),
            comparison_width_pt,
            summary_header_height_pt,
            facecolor=flow_context_fill,
            edgecolor="none",
        )
    )
    ax.text(
        (comparison_box["x0"] + comparison_box["x1"]) / 2.0,
        comparison_box["y1"] - summary_header_height_pt / 2.0,
        comparison_title,
        fontsize=max(base_card_title_size + 0.8, 13.0),
        fontweight="bold",
        color=flow_title_text,
        ha="center",
        va="center",
    )
    comparison_lines = _wrap_flow_text_to_width(
        comparison_body,
        max_width_pt=comparison_width_pt - 36.0,
        font_size=max(base_label_size + 1.4, 11.5),
        font_weight="normal",
        max_chars=56,
    )
    ax.text(
        (comparison_box["x0"] + comparison_box["x1"]) / 2.0,
        comparison_box["y0"] + (summary_height_pt - summary_header_height_pt) / 2.0,
        "\n".join(comparison_lines),
        fontsize=max(base_label_size + 1.4, 11.5),
        color=flow_body_text,
        ha="center",
        va="center",
    )
    layout_boxes.append(
        _flow_box_to_normalized(
            **comparison_box,
            canvas_width_pt=figure_width_pt,
            canvas_height_pt=canvas_height_pt,
            box_id="comparison_box",
            box_type="comparison_summary",
        )
    )
    flow_nodes.append(
        {
            "box_id": "comparison_box",
            "box_type": "comparison_summary",
            "line_count": len(comparison_lines) + 1,
            "max_line_chars": max([len(comparison_title)] + [len(line) for line in comparison_lines]),
            "rendered_height_pt": summary_height_pt,
            "rendered_width_pt": comparison_width_pt,
            "padding_pt": 18.0,
        }
    )

    arrow_targets = (
        comparison_box["x0"] + comparison_width_pt * 0.18,
        (comparison_box["x0"] + comparison_box["x1"]) / 2.0,
        comparison_box["x1"] - comparison_width_pt * 0.18,
    )
    for card_box, arrow_x in zip(card_boxes, arrow_targets, strict=False):
        start_x = (card_box["x0"] + card_box["x1"]) / 2.0
        start_y = card_box["y0"] - 8.0
        end_y = comparison_box["y1"] + 8.0
        ax.add_patch(
            FancyArrowPatch(
                (start_x, start_y),
                (arrow_x, end_y),
                arrowstyle="-|>",
                mutation_scale=12.0,
                linewidth=max(1.0, base_connector_linewidth),
                color=flow_connector,
                connectionstyle="arc3,rad=0.0",
            )
        )
        guide_boxes.append(
            _flow_box_to_normalized(
                x0=min(start_x, arrow_x) - 6.0,
                y0=min(start_y, end_y) - 6.0,
                x1=max(start_x, arrow_x) + 6.0,
                y1=max(start_y, end_y) + 6.0,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"comparison_connector_{len(guide_boxes) + 1}",
                box_type="flow_connector",
            )
        )

    panel_union = _flow_union_box(
        boxes=[*card_boxes, comparison_box],
        box_id="subfigure_panel_main",
        box_type="subfigure_panel",
    )
    panel_boxes.append(
        _flow_box_to_normalized(
            **panel_union,
            canvas_width_pt=figure_width_pt,
            canvas_height_pt=canvas_height_pt,
            box_id="subfigure_panel_main",
            box_type="subfigure_panel",
        )
    )
    dump_json(
        output_layout_path,
        {
            "template_id": "cohort_flow_figure",
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": layout_boxes,
            "panel_boxes": panel_boxes,
            "guide_boxes": guide_boxes,
            "metrics": {
                "layout_mode": "single_panel_cards",
                "steps": steps,
                "exclusions": exclusions,
                "endpoint_inventory": endpoint_inventory,
                "design_panels": design_panels,
                "comparison_summary": {"title": comparison_title, "body": comparison_body},
                "flow_nodes": flow_nodes,
            },
            "render_context": render_context_payload,
        },
    )
    fig.savefig(
        output_svg_path,
        format="svg",
        metadata={"Creator": "FenggaoLab medical display core"},
    )
    fig.savefig(output_png_path, format="png", dpi=220)
    if output_pdf_path is not None:
        fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
    return
