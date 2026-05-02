from __future__ import annotations

from typing import Any, Callable

from ...shared import _FlowNodeSpec, _FlowTextLine, _wrap_flow_text_to_width


def _cohort_flow_block_colors(
    *,
    style_role: str,
    flow_primary_fill: str,
    flow_primary_edge: str,
    flow_context_fill: str,
    flow_context_edge: str,
    flow_audit_fill: str,
    flow_audit_edge: str,
    flow_secondary_fill: str,
    flow_secondary_edge: str,
) -> tuple[str, str]:
    if style_role == "primary":
        return flow_primary_fill, flow_primary_edge
    if style_role == "context":
        return flow_context_fill, flow_context_edge
    if style_role == "audit":
        return flow_audit_fill, flow_audit_edge
    return flow_secondary_fill, flow_secondary_edge


def _build_cohort_flow_step_spec(
    *,
    step: dict[str, Any],
    step_width_pt: float,
    base_card_title_size: float,
    base_detail_size: float,
    base_label_size: float,
    flow_title_text: str,
    flow_body_text: str,
    flow_main_fill: str,
    flow_main_edge: str,
    base_secondary_linewidth: float,
    step_padding_pt: float,
) -> _FlowNodeSpec:
    content_width_pt = step_width_pt - 28.0
    title_lines = _wrap_flow_text_to_width(
        str(step["label"]),
        max_width_pt=content_width_pt,
        font_size=base_card_title_size + 0.5,
        font_weight="bold",
        max_chars=36,
    )
    detail_lines = _wrap_flow_text_to_width(
        str(step.get("detail") or ""),
        max_width_pt=content_width_pt,
        font_size=base_detail_size,
        font_weight="normal",
        max_chars=44,
    )
    lines = [
        *[
            _FlowTextLine(
                text=line,
                font_size=base_card_title_size + 0.5,
                font_weight="bold",
                color=flow_title_text,
            )
            for line in title_lines
        ],
        _FlowTextLine(
            text=f"n = {step['n']}",
            font_size=base_label_size,
            font_weight="normal",
            color=flow_body_text,
            gap_before=14.0,
        ),
    ]
    lines.extend(
        _FlowTextLine(
            text=line,
            font_size=base_detail_size,
            font_weight="normal",
            color=flow_body_text,
            gap_before=12.0 if index == 0 else 0.0,
        )
        for index, line in enumerate(detail_lines)
    )
    return _FlowNodeSpec(
        node_id=f"step_{step['step_id']}",
        box_id=f"step_{step['step_id']}",
        box_type="main_step",
        panel_role="flow",
        fill_color=flow_main_fill,
        edge_color=flow_main_edge,
        linewidth=base_secondary_linewidth,
        lines=tuple(lines),
        width_pt=step_width_pt,
        padding_pt=step_padding_pt,
    )


def _build_cohort_flow_exclusion_spec(
    *,
    exclusion: dict[str, Any],
    exclusion_width_pt: float,
    base_label_size: float,
    base_detail_size: float,
    flow_exclusion_fill: str,
    flow_exclusion_edge: str,
    base_secondary_linewidth: float,
    exclusion_padding_pt: float,
) -> _FlowNodeSpec:
    content_width_pt = exclusion_width_pt - 24.0
    title_lines = _wrap_flow_text_to_width(
        f"{exclusion['label']} (n={exclusion['n']})",
        max_width_pt=content_width_pt,
        font_size=base_label_size,
        font_weight="bold",
        max_chars=40,
    )
    detail_lines = _wrap_flow_text_to_width(
        str(exclusion.get("detail") or ""),
        max_width_pt=content_width_pt,
        font_size=base_detail_size,
        font_weight="normal",
        max_chars=44,
    )
    lines = [
        *[
            _FlowTextLine(
                text=line,
                font_size=base_label_size,
                font_weight="bold",
                color=flow_exclusion_edge,
            )
            for line in title_lines
        ]
    ]
    lines.extend(
        _FlowTextLine(
            text=line,
            font_size=base_detail_size,
            font_weight="normal",
            color=flow_exclusion_edge,
            gap_before=8.0 if index == 0 else 0.0,
        )
        for index, line in enumerate(detail_lines)
    )
    return _FlowNodeSpec(
        node_id=f"exclusion_{exclusion['exclusion_id']}",
        box_id=f"exclusion_{exclusion['exclusion_id']}",
        box_type="exclusion_box",
        panel_role="flow",
        fill_color=flow_exclusion_fill,
        edge_color=flow_exclusion_edge,
        linewidth=max(1.2, base_secondary_linewidth - 0.2),
        lines=tuple(lines),
        width_pt=exclusion_width_pt,
        padding_pt=exclusion_padding_pt,
    )


def _build_cohort_flow_design_panel_specs(
    *,
    design_panels: list[dict[str, Any]],
    endpoint_inventory: list[dict[str, Any]],
    block_colors: Callable[[str], tuple[str, str]],
    sparse_modern_layout: bool,
    wide_block_width_pt: float,
    standard_block_width_pt: float,
    footer_block_width_pt: float,
    base_card_title_size: float,
    base_label_size: float,
    base_detail_size: float,
    flow_title_text: str,
    flow_body_text: str,
    base_primary_linewidth: float,
    base_secondary_linewidth: float,
    hierarchy_padding_pt: float,
) -> list[_FlowNodeSpec]:
    def build_design_panel_spec(block: dict[str, Any]) -> _FlowNodeSpec:
        style_role = str(block.get("style_role") or "secondary")
        panel_role = str(block["layout_role"])
        fill_color, edge_color = block_colors(style_role)
        is_wide = panel_role in {"wide_top", "wide_bottom", "wide_left", "footer_stack"}
        width_pt = wide_block_width_pt if is_wide else standard_block_width_pt
        if sparse_modern_layout and panel_role in {"left_middle", "right_middle", "left_bottom", "right_bottom"}:
            width_pt = wide_block_width_pt
        if panel_role == "footer_stack":
            width_pt = footer_block_width_pt
        content_width_pt = width_pt - 26.0
        title_lines = _wrap_flow_text_to_width(
            str(block["title"]),
            max_width_pt=content_width_pt,
            font_size=base_card_title_size,
            font_weight="bold",
        )
        lines: list[_FlowTextLine] = [
            *[
                _FlowTextLine(
                    text=line,
                    font_size=base_card_title_size,
                    font_weight="bold",
                    color=flow_title_text,
                )
                for line in title_lines
            ]
        ]
        for item_index, item in enumerate(block["lines"]):
            label_lines = _wrap_flow_text_to_width(
                str(item["label"]),
                max_width_pt=content_width_pt,
                font_size=base_label_size,
                font_weight="bold",
            )
            detail_lines = _wrap_flow_text_to_width(
                str(item.get("detail") or ""),
                max_width_pt=content_width_pt,
                font_size=base_detail_size,
                font_weight="normal",
            )
            item_gap = 8.0 if item_index == 0 else 10.0
            for label_index, line in enumerate(label_lines):
                lines.append(
                    _FlowTextLine(
                        text=line,
                        font_size=base_label_size,
                        font_weight="bold",
                        color=flow_title_text,
                        gap_before=item_gap if label_index == 0 else 0.0,
                    )
                )
            for detail_index, line in enumerate(detail_lines):
                lines.append(
                    _FlowTextLine(
                        text=line,
                        font_size=base_detail_size,
                        font_weight="normal",
                        color=flow_body_text,
                        gap_before=4.0 if detail_index == 0 else 0.0,
                    )
                )
        return _FlowNodeSpec(
            node_id=f"secondary_panel_{block['panel_id']}",
            box_id=f"secondary_panel_{block['panel_id']}",
            box_type="secondary_panel",
            panel_role=panel_role,
            fill_color=fill_color,
            edge_color=edge_color,
            linewidth=base_primary_linewidth if style_role == "primary" else base_secondary_linewidth,
            lines=tuple(lines),
            width_pt=width_pt,
            padding_pt=hierarchy_padding_pt,
        )
    right_blocks: list[dict[str, Any]] = [*design_panels]
    if endpoint_inventory:
        right_blocks.append(
            {
                "panel_id": "endpoint_inventory",
                "layout_role": "footer_stack",
                "style_role": "audit",
                "title": "Endpoint inventory",
                "lines": [
                    {
                        "label": (
                            f"{item['label']} (n={item['n']})"
                            if isinstance(item.get("n"), int)
                            else str(item["label"])
                        ),
                        "detail": str(item.get("detail") or "").strip(),
                    }
                    for item in endpoint_inventory
                ],
            }
        )
    return [build_design_panel_spec(block) for block in right_blocks]


def _cohort_flow_spec_base_height(spec: _FlowNodeSpec) -> float:
    height = spec.padding_pt * 2.0
    for line in spec.lines:
        height += line.gap_before
        height += line.font_size * 1.24
    return height
