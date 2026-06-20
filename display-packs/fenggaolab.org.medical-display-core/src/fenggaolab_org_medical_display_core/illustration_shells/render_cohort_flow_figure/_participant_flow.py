from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from ...shared_parts.common import dump_json
from ...shared_parts.flow_layout import (
    _flow_box_to_normalized,
    _measure_flow_text_width_pt,
    _wrap_flow_text_to_width,
)


def _participant_text_lines(
    value: str,
    *,
    max_width_pt: float,
    font_size: float,
    font_weight: str = "normal",
    max_chars: int = 42,
) -> tuple[str, ...]:
    return _wrap_flow_text_to_width(
        value,
        max_width_pt=max_width_pt,
        font_size=font_size,
        font_weight=font_weight,
        max_chars=max_chars,
    )


def _participant_box_height(
    *,
    title_lines: tuple[str, ...],
    detail_lines: tuple[str, ...],
    title_size: float,
    detail_size: float,
    padding_pt: float,
    min_height_pt: float,
) -> float:
    title_height = len(title_lines) * title_size * 1.22
    detail_height = len(detail_lines) * detail_size * 1.22
    detail_gap = 9.0 if detail_lines else 0.0
    return max(min_height_pt, padding_pt * 2.0 + title_height + detail_gap + detail_height)


def _draw_participant_node(
    *,
    ax: Any,
    box: dict[str, float],
    title_lines: tuple[str, ...],
    detail_lines: tuple[str, ...],
    title_size: float,
    detail_size: float,
    padding_pt: float,
    fill_color: str,
    edge_color: str,
    title_color: str,
    body_color: str,
    linewidth: float,
    rounding_size: float,
) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (box["x0"], box["y0"]),
            box["x1"] - box["x0"],
            box["y1"] - box["y0"],
            boxstyle=f"round,pad=0.0,rounding_size={rounding_size:.2f}",
            facecolor=fill_color,
            edgecolor=edge_color,
            linewidth=linewidth,
        )
    )
    x_text = box["x0"] + padding_pt
    y_cursor = box["y1"] - padding_pt
    for line in title_lines:
        ax.text(
            x_text,
            y_cursor,
            line,
            fontsize=title_size,
            fontweight="bold",
            color=title_color,
            ha="left",
            va="top",
        )
        y_cursor -= title_size * 1.22
    if detail_lines:
        y_cursor -= 9.0
    for line in detail_lines:
        ax.text(
            x_text,
            y_cursor,
            line,
            fontsize=detail_size,
            fontweight="normal",
            color=body_color,
            ha="left",
            va="top",
        )
        y_cursor -= detail_size * 1.22


def _draw_participant_arrow(
    *,
    ax: Any,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    linewidth: float,
    mutation_scale: float,
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=mutation_scale,
            linewidth=linewidth,
            color=color,
            connectionstyle="arc3,rad=0.0",
        )
    )


def _render_participant_flow(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    output_pdf_path: Path | None = None,
    title: str,
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
    flow_exclusion_fill: str,
    flow_exclusion_edge: str,
    flow_primary_fill: str,
    flow_primary_edge: str,
    flow_secondary_fill: str,
    flow_secondary_edge: str,
    flow_context_fill: str,
    flow_context_edge: str,
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
    top_margin_pt = read_float(layout_override, "participant_top_margin_pt", 30.0)
    bottom_margin_pt = read_float(layout_override, "participant_bottom_margin_pt", 26.0)
    title_gap_pt = read_float(layout_override, "participant_title_gap_pt", 18.0)
    step_gap_pt = read_float(layout_override, "participant_step_gap_pt", 24.0)
    summary_gap_pt = read_float(layout_override, "participant_summary_gap_pt", 24.0)
    branch_gap_pt = read_float(layout_override, "participant_branch_gap_pt", 30.0)
    step_width_pt = read_float(layout_override, "participant_step_width_pt", 380.0)
    exclusion_width_pt = read_float(layout_override, "participant_exclusion_width_pt", 270.0)
    summary_width_pt = read_float(layout_override, "participant_summary_width_pt", 305.0)
    padding_pt = read_float(layout_override, "participant_padding_pt", 14.0)
    min_step_height_pt = read_float(layout_override, "participant_min_step_height_pt", 74.0)
    min_exclusion_height_pt = read_float(layout_override, "participant_min_exclusion_height_pt", 58.0)
    summary_height_pt = read_float(layout_override, "participant_summary_height_pt", 98.0)
    title_size = max(base_card_title_size + 1.3, 14.0)
    step_title_size = max(base_card_title_size + 0.8, 12.8)
    detail_size = max(base_detail_size + 0.2, 9.8)
    label_size = max(base_label_size + 0.1, 10.8)
    linewidth = max(1.1, base_secondary_linewidth)
    connector_width = max(1.0, base_connector_linewidth)

    content_width_pt = figure_width_pt - side_margin_pt * 2.0
    if step_width_pt + branch_gap_pt + exclusion_width_pt > content_width_pt:
        scale = content_width_pt / (step_width_pt + branch_gap_pt + exclusion_width_pt)
        step_width_pt *= scale
        exclusion_width_pt *= scale
        branch_gap_pt *= scale
        summary_width_pt = min(summary_width_pt, step_width_pt)

    title_lines = _participant_text_lines(
        title or "Participant flow",
        max_width_pt=content_width_pt,
        font_size=title_size,
        font_weight="bold",
        max_chars=72,
    )
    title_height_pt = max(1, len(title_lines)) * title_size * 1.2
    step_specs: list[dict[str, Any]] = []
    for step in steps:
        node_title = f"{step['label']} (n={step['n']:,})"
        title_line_set = _participant_text_lines(
            node_title,
            max_width_pt=step_width_pt - padding_pt * 2.0,
            font_size=step_title_size,
            font_weight="bold",
            max_chars=48,
        )
        detail_line_set = _participant_text_lines(
            str(step.get("detail") or ""),
            max_width_pt=step_width_pt - padding_pt * 2.0,
            font_size=detail_size,
            max_chars=52,
        )
        step_specs.append(
            {
                "step": step,
                "title_lines": title_line_set,
                "detail_lines": detail_line_set,
                "height_pt": _participant_box_height(
                    title_lines=title_line_set,
                    detail_lines=detail_line_set,
                    title_size=step_title_size,
                    detail_size=detail_size,
                    padding_pt=padding_pt,
                    min_height_pt=min_step_height_pt,
                ),
            }
        )

    exclusion_specs: dict[str, dict[str, Any]] = {}
    for exclusion in exclusions:
        node_title = f"{exclusion['label']} (n={exclusion['n']:,})"
        title_line_set = _participant_text_lines(
            node_title,
            max_width_pt=exclusion_width_pt - padding_pt * 2.0,
            font_size=label_size,
            font_weight="bold",
            max_chars=42,
        )
        detail_line_set = _participant_text_lines(
            str(exclusion.get("detail") or ""),
            max_width_pt=exclusion_width_pt - padding_pt * 2.0,
            font_size=detail_size,
            max_chars=44,
        )
        exclusion_specs[str(exclusion["exclusion_id"])] = {
            "exclusion": exclusion,
            "title_lines": title_line_set,
            "detail_lines": detail_line_set,
            "height_pt": _participant_box_height(
                title_lines=title_line_set,
                detail_lines=detail_line_set,
                title_size=label_size,
                detail_size=detail_size,
                padding_pt=padding_pt,
                min_height_pt=min_exclusion_height_pt,
            ),
        }

    main_stack_height_pt = sum(spec["height_pt"] for spec in step_specs) + step_gap_pt * max(0, len(step_specs) - 1)
    summary_row_height_pt = summary_height_pt if endpoint_inventory or design_panels or comparison_summary else 0.0
    canvas_height_pt = (
        top_margin_pt
        + title_height_pt
        + title_gap_pt
        + main_stack_height_pt
        + (summary_gap_pt + summary_row_height_pt if summary_row_height_pt else 0.0)
        + bottom_margin_pt
    )

    fig = plt.figure(figsize=(figure_width_pt / 72.0, canvas_height_pt / 72.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, figure_width_pt)
    ax.set_ylim(0.0, canvas_height_pt)
    ax.axis("off")

    layout_boxes: list[dict[str, Any]] = []
    panel_boxes: list[dict[str, Any]] = []
    guide_boxes: list[dict[str, Any]] = []

    title_y = canvas_height_pt - top_margin_pt
    ax.text(
        side_margin_pt,
        title_y,
        "\n".join(title_lines),
        fontsize=title_size,
        fontweight="bold",
        color=flow_title_text,
        ha="left",
        va="top",
    )
    layout_boxes.append(
        _flow_box_to_normalized(
            x0=side_margin_pt,
            y0=title_y - title_height_pt,
            x1=side_margin_pt + min(content_width_pt, _measure_flow_text_width_pt(title_lines[0], font_size=title_size, font_weight="bold")),
            y1=title_y,
            canvas_width_pt=figure_width_pt,
            canvas_height_pt=canvas_height_pt,
            box_id="participant_flow_title",
            box_type="title",
        )
    )

    step_x0 = side_margin_pt + (content_width_pt - (step_width_pt + branch_gap_pt + exclusion_width_pt)) / 2.0
    exclusion_x0 = step_x0 + step_width_pt + branch_gap_pt
    current_y = title_y - title_height_pt - title_gap_pt
    step_boxes: dict[str, dict[str, float]] = {}
    exclusion_boxes: dict[str, dict[str, float]] = {}
    exclusions_by_step: dict[str, list[dict[str, Any]]] = {}
    for exclusion in exclusions:
        exclusions_by_step.setdefault(str(exclusion["from_step_id"]), []).append(exclusion)

    for index, step_spec in enumerate(step_specs):
        step = step_spec["step"]
        box = {
            "x0": step_x0,
            "y0": current_y - step_spec["height_pt"],
            "x1": step_x0 + step_width_pt,
            "y1": current_y,
        }
        _draw_participant_node(
            ax=ax,
            box=box,
            title_lines=step_spec["title_lines"],
            detail_lines=step_spec["detail_lines"],
            title_size=step_title_size,
            detail_size=detail_size,
            padding_pt=padding_pt,
            fill_color=flow_main_fill,
            edge_color=flow_main_edge,
            title_color=flow_title_text,
            body_color=flow_body_text,
            linewidth=linewidth,
            rounding_size=12.0,
        )
        step_key = str(step["step_id"])
        step_boxes[step_key] = box
        layout_boxes.append(
            _flow_box_to_normalized(
                **box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"participant_step_{step_key}",
                box_type="main_step",
            )
        )

        related_exclusions = exclusions_by_step.get(step_key, [])
        if related_exclusions:
            cluster_height = sum(exclusion_specs[str(item["exclusion_id"])]["height_pt"] for item in related_exclusions)
            cluster_height += 10.0 * max(0, len(related_exclusions) - 1)
            cluster_top = (box["y0"] + box["y1"]) / 2.0 + cluster_height / 2.0
            for exclusion in related_exclusions:
                exclusion_id = str(exclusion["exclusion_id"])
                spec = exclusion_specs[exclusion_id]
                exclusion_box = {
                    "x0": exclusion_x0,
                    "y0": cluster_top - spec["height_pt"],
                    "x1": exclusion_x0 + exclusion_width_pt,
                    "y1": cluster_top,
                }
                cluster_top = exclusion_box["y0"] - 10.0
                _draw_participant_node(
                    ax=ax,
                    box=exclusion_box,
                    title_lines=spec["title_lines"],
                    detail_lines=spec["detail_lines"],
                    title_size=label_size,
                    detail_size=detail_size,
                    padding_pt=padding_pt,
                    fill_color=flow_exclusion_fill,
                    edge_color=flow_exclusion_edge,
                    title_color=flow_exclusion_edge,
                    body_color=flow_exclusion_edge,
                    linewidth=max(1.0, linewidth * 0.86),
                    rounding_size=10.0,
                )
                exclusion_boxes[exclusion_id] = exclusion_box
                layout_boxes.append(
                    _flow_box_to_normalized(
                        **exclusion_box,
                        canvas_width_pt=figure_width_pt,
                        canvas_height_pt=canvas_height_pt,
                        box_id=f"participant_exclusion_{exclusion_id}",
                        box_type="exclusion_box",
                    )
                )
                branch_y = (exclusion_box["y0"] + exclusion_box["y1"]) / 2.0
                _draw_participant_arrow(
                    ax=ax,
                    start=(box["x1"], branch_y),
                    end=(exclusion_box["x0"] - 4.0, branch_y),
                    color=flow_connector,
                    linewidth=connector_width,
                    mutation_scale=11.0,
                )
                guide_boxes.append(
                    _flow_box_to_normalized(
                        x0=box["x1"],
                        y0=branch_y - 3.5,
                        x1=exclusion_box["x0"],
                        y1=branch_y + 3.5,
                        canvas_width_pt=figure_width_pt,
                        canvas_height_pt=canvas_height_pt,
                        box_id=f"participant_branch_{exclusion_id}",
                        box_type="flow_branch_connector",
                    )
                )

        if index < len(step_specs) - 1:
            next_height = step_specs[index + 1]["height_pt"]
            start = ((box["x0"] + box["x1"]) / 2.0, box["y0"] - 4.0)
            end = ((box["x0"] + box["x1"]) / 2.0, box["y0"] - step_gap_pt + 4.0)
            _draw_participant_arrow(
                ax=ax,
                start=start,
                end=end,
                color=flow_connector,
                linewidth=connector_width,
                mutation_scale=12.0,
            )
            guide_boxes.append(
                _flow_box_to_normalized(
                    x0=start[0] - 4.0,
                    y0=end[1],
                    x1=start[0] + 4.0,
                    y1=start[1],
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=f"participant_spine_{step_key}",
                    box_type="flow_connector",
                )
            )
            current_y = box["y0"] - step_gap_pt
        else:
            current_y = box["y0"]

    if summary_row_height_pt:
        summary_y0 = bottom_margin_pt
        summary_cards: list[tuple[str, tuple[str, ...], tuple[str, ...], str, str]] = []
        if design_panels:
            split_lines: list[str] = []
            for panel in design_panels[:1]:
                split_lines.extend(f"{line['label']}: {line.get('detail') or ''}".strip(": ") for line in panel.get("lines", [])[:2])
            summary_cards.append(
                (
                    "Analysis plan",
                    _participant_text_lines("Analysis plan", max_width_pt=summary_width_pt - padding_pt * 2.0, font_size=label_size, font_weight="bold"),
                    _participant_text_lines("; ".join(split_lines), max_width_pt=summary_width_pt - padding_pt * 2.0, font_size=detail_size, max_chars=52),
                    flow_context_fill,
                    flow_context_edge,
                )
            )
        if endpoint_inventory:
            endpoint_text = "; ".join(
                f"{item['label']} n={item['n']}" if item.get("n") is not None else str(item["label"])
                for item in endpoint_inventory[:3]
            )
            summary_cards.append(
                (
                    "Endpoint inventory",
                    _participant_text_lines("Endpoint inventory", max_width_pt=summary_width_pt - padding_pt * 2.0, font_size=label_size, font_weight="bold"),
                    _participant_text_lines(endpoint_text, max_width_pt=summary_width_pt - padding_pt * 2.0, font_size=detail_size, max_chars=52),
                    flow_secondary_fill,
                    flow_secondary_edge,
                )
            )
        if comparison_summary.get("body"):
            summary_cards.append(
                (
                    "Evidence boundary",
                    _participant_text_lines("Evidence boundary", max_width_pt=summary_width_pt - padding_pt * 2.0, font_size=label_size, font_weight="bold"),
                    _participant_text_lines(str(comparison_summary["body"]), max_width_pt=summary_width_pt - padding_pt * 2.0, font_size=detail_size, max_chars=52),
                    flow_primary_fill,
                    flow_primary_edge,
                )
            )
        card_count = max(1, len(summary_cards))
        summary_gap = 14.0
        summary_width = min(summary_width_pt, (content_width_pt - summary_gap * max(0, card_count - 1)) / card_count)
        summary_total_width = summary_width * card_count + summary_gap * max(0, card_count - 1)
        summary_x = side_margin_pt + (content_width_pt - summary_total_width) / 2.0
        for index, (_label, title_line_set, detail_line_set, fill, edge) in enumerate(summary_cards):
            summary_box = {
                "x0": summary_x + index * (summary_width + summary_gap),
                "y0": summary_y0,
                "x1": summary_x + index * (summary_width + summary_gap) + summary_width,
                "y1": summary_y0 + summary_height_pt,
            }
            _draw_participant_node(
                ax=ax,
                box=summary_box,
                title_lines=title_line_set,
                detail_lines=detail_line_set,
                title_size=label_size,
                detail_size=detail_size,
                padding_pt=padding_pt,
                fill_color=fill,
                edge_color=edge,
                title_color=flow_title_text,
                body_color=flow_body_text,
                linewidth=max(0.9, linewidth * 0.82),
                rounding_size=10.0,
            )
            layout_boxes.append(
                _flow_box_to_normalized(
                    **summary_box,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=f"participant_summary_{index + 1}",
                    box_type="summary_panel",
                )
            )

    all_boxes = [*step_boxes.values(), *exclusion_boxes.values()]
    if all_boxes:
        panel_boxes.append(
            _flow_box_to_normalized(
                x0=min(box["x0"] for box in all_boxes),
                y0=min(box["y0"] for box in all_boxes),
                x1=max(box["x1"] for box in all_boxes),
                y1=max(box["y1"] for box in all_boxes),
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id="participant_flow_main",
                box_type="subfigure_panel",
            )
        )

    flow_nodes = [
        {
            "box_id": f"participant_step_{step_id}",
            "box_type": "main_step",
            "line_count": len(spec["title_lines"]) + len(spec["detail_lines"]),
            "max_line_chars": max((len(line) for line in [*spec["title_lines"], *spec["detail_lines"]]), default=0),
            "rendered_height_pt": box["y1"] - box["y0"],
            "rendered_width_pt": box["x1"] - box["x0"],
            "padding_pt": padding_pt,
        }
        for step_id, box in step_boxes.items()
        for spec in [next(item for item in step_specs if str(item["step"]["step_id"]) == step_id)]
    ]
    flow_nodes.extend(
        {
            "box_id": f"participant_exclusion_{exclusion_id}",
            "box_type": "exclusion_box",
            "line_count": len(spec["title_lines"]) + len(spec["detail_lines"]),
            "max_line_chars": max((len(line) for line in [*spec["title_lines"], *spec["detail_lines"]]), default=0),
            "rendered_height_pt": box["y1"] - box["y0"],
            "rendered_width_pt": box["x1"] - box["x0"],
            "padding_pt": padding_pt,
        }
        for exclusion_id, box in exclusion_boxes.items()
        for spec in [exclusion_specs[exclusion_id]]
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
                "layout_mode": "participant_flow",
                "steps": steps,
                "exclusions": exclusions,
                "endpoint_inventory": endpoint_inventory,
                "design_panels": design_panels,
                "comparison_summary": comparison_summary,
                "flow_nodes": flow_nodes,
            },
            "render_context": render_context_payload,
        },
    )
    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output_svg_path,
        format="svg",
        metadata={"Creator": "FenggaoLab medical display core"},
    )
    fig.savefig(output_png_path, format="png", dpi=240)
    if output_pdf_path is not None:
        fig.savefig(output_pdf_path, format="pdf")
    plt.close(fig)
