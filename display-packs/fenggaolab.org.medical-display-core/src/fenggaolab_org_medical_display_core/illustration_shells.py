from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
from med_autoscience import display_registry

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from .shared import (
    _FlowNodeSpec,
    _FlowTextLine,
    _GraphvizNodeBox,
    _bbox_to_layout_box,
    _build_submission_graphical_abstract_arrow_lane_spec,
    _choose_shared_submission_graphical_abstract_arrow_lane,
    _flow_box_to_normalized,
    _flow_html_label_for_node,
    _flow_union_box,
    _measure_flow_text_width_pt,
    _prepare_python_illustration_output_paths,
    _require_namespaced_registry_id,
    _require_non_empty_string,
    _run_graphviz_layout,
    _wrap_figure_title_to_width,
    _wrap_flow_text_to_width,
    dump_json,
)


_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}


def _validate_cohort_flow_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    steps = payload.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"{path.name} must contain a non-empty steps list")
    normalized_steps: list[dict[str, Any]] = []
    step_ids: set[str] = set()
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            raise ValueError(f"{path.name} steps[{index}] must be an object")
        step_id = str(step.get("step_id") or "").strip()
        label = str(step.get("label") or "").strip()
        detail = str(step.get("detail") or "").strip()
        if not step_id or not label:
            raise ValueError(f"{path.name} steps[{index}] must include step_id and label")
        if step_id in step_ids:
            raise ValueError(f"{path.name} steps[{index}].step_id must be unique")
        step_ids.add(step_id)
        raw_n = step.get("n")
        if not isinstance(raw_n, int):
            raise ValueError(f"{path.name} steps[{index}].n must be an integer")
        normalized_steps.append({"step_id": step_id, "label": label, "detail": detail, "n": raw_n})

    exclusions_payload = payload.get("exclusions")
    if exclusions_payload is None:
        exclusions_payload = payload.get("exclusion_branches") or []
    if not isinstance(exclusions_payload, list):
        raise ValueError(f"{path.name} exclusions must be a list when provided")
    normalized_exclusions: list[dict[str, Any]] = []
    exclusion_branch_ids: set[str] = set()
    for index, branch in enumerate(exclusions_payload):
        if not isinstance(branch, dict):
            raise ValueError(f"{path.name} exclusions[{index}] must be an object")
        branch_id = str(branch.get("exclusion_id") or branch.get("branch_id") or "").strip()
        from_step_id = str(branch.get("from_step_id") or "").strip()
        label = str(branch.get("label") or "").strip()
        detail = str(branch.get("detail") or "").strip()
        if not branch_id or not from_step_id or not label:
            raise ValueError(
                f"{path.name} exclusions[{index}] must include exclusion_id/branch_id, from_step_id, and label"
            )
        if branch_id in exclusion_branch_ids:
            raise ValueError(f"{path.name} exclusions[{index}].exclusion_id must be unique")
        if from_step_id not in step_ids:
            raise ValueError(f"{path.name} exclusions[{index}].from_step_id must reference a declared step")
        raw_n = branch.get("n")
        if not isinstance(raw_n, int):
            raise ValueError(f"{path.name} exclusions[{index}].n must be an integer")
        exclusion_branch_ids.add(branch_id)
        normalized_exclusions.append(
            {
                "exclusion_id": branch_id,
                "from_step_id": from_step_id,
                "label": label,
                "detail": detail,
                "n": raw_n,
            }
        )

    endpoint_inventory_payload = payload.get("endpoint_inventory") or []
    if not isinstance(endpoint_inventory_payload, list):
        raise ValueError(f"{path.name} endpoint_inventory must be a list when provided")
    normalized_endpoint_inventory: list[dict[str, Any]] = []
    endpoint_ids: set[str] = set()
    for index, endpoint in enumerate(endpoint_inventory_payload):
        if not isinstance(endpoint, dict):
            raise ValueError(f"{path.name} endpoint_inventory[{index}] must be an object")
        endpoint_id = str(endpoint.get("endpoint_id") or "").strip()
        label = str(endpoint.get("label") or "").strip()
        detail = str(endpoint.get("detail") or "").strip()
        if not endpoint_id or not label:
            raise ValueError(f"{path.name} endpoint_inventory[{index}] must include endpoint_id and label")
        if endpoint_id in endpoint_ids:
            raise ValueError(f"{path.name} endpoint_inventory[{index}].endpoint_id must be unique")
        raw_n = endpoint.get("n")
        if raw_n is None:
            raw_n = endpoint.get("event_n")
        if raw_n is not None and not isinstance(raw_n, int):
            raise ValueError(f"{path.name} endpoint_inventory[{index}].n must be an integer when provided")
        endpoint_ids.add(endpoint_id)
        normalized_endpoint_inventory.append(
            {
                "endpoint_id": endpoint_id,
                "label": label,
                "detail": detail,
                "n": raw_n,
            }
        )

    design_panels_payload = payload.get("design_panels")
    if design_panels_payload is None:
        design_panels_payload = payload.get("sidecar_blocks") or []
    if not isinstance(design_panels_payload, list):
        raise ValueError(f"{path.name} design_panels must be a list when provided")
    normalized_design_panels: list[dict[str, Any]] = []
    sidecar_block_ids: set[str] = set()
    for index, block in enumerate(design_panels_payload):
        if not isinstance(block, dict):
            raise ValueError(f"{path.name} design_panels[{index}] must be an object")
        block_id = str(block.get("panel_id") or block.get("block_id") or "").strip()
        raw_block_type = str(block.get("layout_role") or block.get("block_type") or "").strip()
        block_type = _COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES.get(raw_block_type, raw_block_type)
        style_role = str(block.get("style_role") or "secondary").strip().lower()
        title = str(block.get("title") or "").strip()
        items = block.get("lines")
        if items is None:
            items = block.get("items")
        if not block_id or not block_type or not title:
            raise ValueError(f"{path.name} design_panels[{index}] must include panel_id/block_id, layout_role/block_type, and title")
        if style_role not in {"primary", "secondary", "context", "audit"}:
            raise ValueError(
                f"{path.name} design_panels[{index}].style_role must be one of primary, secondary, context, audit"
            )
        if block_id in sidecar_block_ids:
            raise ValueError(f"{path.name} design_panels[{index}].panel_id must be unique")
        if not isinstance(items, list) or not items:
            raise ValueError(f"{path.name} design_panels[{index}].lines/items must be a non-empty list")
        normalized_items: list[dict[str, Any]] = []
        for item_index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"{path.name} design_panels[{index}].lines[{item_index}] must be an object")
            label = str(item.get("label") or "").strip()
            detail = str(item.get("detail") or "").strip()
            if not label:
                raise ValueError(f"{path.name} design_panels[{index}].lines[{item_index}].label must be non-empty")
            normalized_items.append({"label": label, "detail": detail})
        sidecar_block_ids.add(block_id)
        normalized_design_panels.append(
            {
                "panel_id": block_id,
                "layout_role": block_type,
                "style_role": style_role,
                "title": title,
                "lines": normalized_items,
            }
        )

    return {
        "display_id": str(payload.get("display_id") or "").strip(),
        "title": str(payload.get("title") or "").strip(),
        "caption": str(payload.get("caption") or "").strip(),
        "steps": normalized_steps,
        "exclusions": normalized_exclusions,
        "endpoint_inventory": normalized_endpoint_inventory,
        "design_panels": normalized_design_panels,
    }

def _validate_submission_graphical_abstract_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    expected_shell_id = display_registry.get_illustration_shell_spec("submission_graphical_abstract").shell_id
    shell_id = _require_non_empty_string(payload.get("shell_id"), label=f"{path.name} shell_id")
    if shell_id != expected_shell_id:
        raise ValueError(f"{path.name} shell_id must be `{expected_shell_id}`")
    display_id = _require_non_empty_string(payload.get("display_id"), label=f"{path.name} display_id")
    catalog_id = _require_non_empty_string(payload.get("catalog_id"), label=f"{path.name} catalog_id")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} title")
    caption = _require_non_empty_string(payload.get("caption"), label=f"{path.name} caption")

    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} must contain a non-empty panels list")
    normalized_panels: list[dict[str, Any]] = []
    panel_ids: set[str] = set()
    for panel_index, panel in enumerate(panels_payload):
        if not isinstance(panel, dict):
            raise ValueError(f"{path.name} panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel.get("panel_id"),
            label=f"{path.name} panels[{panel_index}].panel_id",
        )
        if panel_id in panel_ids:
            raise ValueError(f"{path.name} panels[{panel_index}].panel_id must be unique")
        panel_ids.add(panel_id)
        rows_payload = panel.get("rows")
        if not isinstance(rows_payload, list) or not rows_payload:
            raise ValueError(f"{path.name} panels[{panel_index}].rows must be a non-empty list")
        normalized_rows: list[dict[str, Any]] = []
        for row_index, row in enumerate(rows_payload):
            if not isinstance(row, dict):
                raise ValueError(f"{path.name} panels[{panel_index}].rows[{row_index}] must be an object")
            cards_payload = row.get("cards")
            if not isinstance(cards_payload, list) or not cards_payload:
                raise ValueError(
                    f"{path.name} panels[{panel_index}].rows[{row_index}].cards must be a non-empty list"
                )
            if len(cards_payload) > 2:
                raise ValueError(
                    f"{path.name} panels[{panel_index}].rows[{row_index}] supports at most two cards"
                )
            normalized_cards: list[dict[str, Any]] = []
            card_ids: set[str] = set()
            for card_index, card in enumerate(cards_payload):
                if not isinstance(card, dict):
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}] must be an object"
                    )
                card_id = _require_non_empty_string(
                    card.get("card_id"),
                    label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].card_id",
                )
                if card_id in card_ids:
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].card_id must be unique within the row"
                    )
                card_ids.add(card_id)
                accent_role = str(card.get("accent_role") or "neutral").strip().lower()
                if accent_role not in {"neutral", "primary", "secondary", "contrast", "audit"}:
                    raise ValueError(
                        f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].accent_role "
                        "must be one of neutral, primary, secondary, contrast, audit"
                    )
                normalized_cards.append(
                    {
                        "card_id": card_id,
                        "title": _require_non_empty_string(
                            card.get("title"),
                            label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].title",
                        ),
                        "value": _require_non_empty_string(
                            card.get("value"),
                            label=f"{path.name} panels[{panel_index}].rows[{row_index}].cards[{card_index}].value",
                        ),
                        "detail": str(card.get("detail") or "").strip(),
                        "accent_role": accent_role,
                    }
                )
            normalized_rows.append({"cards": normalized_cards})
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": _require_non_empty_string(
                    panel.get("panel_label"),
                    label=f"{path.name} panels[{panel_index}].panel_label",
                ),
                "title": _require_non_empty_string(
                    panel.get("title"),
                    label=f"{path.name} panels[{panel_index}].title",
                ),
                "subtitle": _require_non_empty_string(
                    panel.get("subtitle"),
                    label=f"{path.name} panels[{panel_index}].subtitle",
                ),
                "rows": normalized_rows,
            }
        )

    footer_pills_payload = payload.get("footer_pills") or []
    if not isinstance(footer_pills_payload, list):
        raise ValueError(f"{path.name} footer_pills must be a list when provided")
    normalized_footer_pills: list[dict[str, Any]] = []
    pill_ids: set[str] = set()
    for pill_index, pill in enumerate(footer_pills_payload):
        if not isinstance(pill, dict):
            raise ValueError(f"{path.name} footer_pills[{pill_index}] must be an object")
        pill_id = _require_non_empty_string(
            pill.get("pill_id"),
            label=f"{path.name} footer_pills[{pill_index}].pill_id",
        )
        if pill_id in pill_ids:
            raise ValueError(f"{path.name} footer_pills[{pill_index}].pill_id must be unique")
        pill_ids.add(pill_id)
        panel_id = _require_non_empty_string(
            pill.get("panel_id"),
            label=f"{path.name} footer_pills[{pill_index}].panel_id",
        )
        if panel_id not in panel_ids:
            raise ValueError(
                f"{path.name} footer_pills[{pill_index}].panel_id must reference a declared panel"
            )
        style_role = str(pill.get("style_role") or "secondary").strip().lower()
        if style_role not in {"primary", "secondary", "contrast", "audit", "neutral"}:
            raise ValueError(
                f"{path.name} footer_pills[{pill_index}].style_role must be one of primary, secondary, contrast, audit, neutral"
            )
        normalized_footer_pills.append(
            {
                "pill_id": pill_id,
                "panel_id": panel_id,
                "label": _require_non_empty_string(
                    pill.get("label"),
                    label=f"{path.name} footer_pills[{pill_index}].label",
                ),
                "style_role": style_role,
            }
        )

    return {
        "shell_id": shell_id,
        "display_id": display_id,
        "catalog_id": catalog_id,
        "title": title,
        "caption": caption,
        "paper_role": str(payload.get("paper_role") or "submission_companion").strip() or "submission_companion",
        "panels": normalized_panels,
        "footer_pills": normalized_footer_pills,
    }

def _render_cohort_flow_figure(
    *,
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    title: str,
    steps: list[dict[str, Any]],
    exclusions: list[dict[str, Any]],
    endpoint_inventory: list[dict[str, Any]],
    design_panels: list[dict[str, Any]],
    render_context: dict[str, Any],
) -> None:
    def read_float(mapping: dict[str, Any], key: str, default: float) -> float:
        value = mapping.get(key, default)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return float(default)

    def read_ratio(mapping: dict[str, Any], key: str) -> float | None:
        value = mapping.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            normalized = float(value)
            if 0.0 < normalized < 1.0:
                return normalized
        return None

    render_context_payload = dict(render_context or {})
    style_roles = dict(render_context_payload.get("style_roles") or {})
    layout_override = dict(render_context_payload.get("layout_override") or {})
    typography = dict(render_context_payload.get("typography") or {})
    stroke = dict(render_context_payload.get("stroke") or {})

    def role_color(role_name: str) -> str:
        return _require_non_empty_string(
            style_roles.get(role_name),
            label=f"cohort_flow_figure render_context.style_roles.{role_name}",
        )

    flow_main_fill = role_color("flow_main_fill")
    flow_main_edge = role_color("flow_main_edge")
    flow_exclusion_fill = role_color("flow_exclusion_fill")
    flow_exclusion_edge = role_color("flow_exclusion_edge")
    flow_primary_fill = role_color("flow_primary_fill")
    flow_primary_edge = role_color("flow_primary_edge")
    flow_secondary_fill = role_color("flow_secondary_fill")
    flow_secondary_edge = role_color("flow_secondary_edge")
    flow_context_fill = role_color("flow_context_fill")
    flow_context_edge = role_color("flow_context_edge")
    flow_audit_fill = role_color("flow_audit_fill")
    flow_audit_edge = role_color("flow_audit_edge")
    flow_title_text = role_color("flow_title_text")
    flow_body_text = role_color("flow_body_text")
    flow_panel_label = role_color("flow_panel_label")
    flow_connector = role_color("flow_connector")

    base_card_title_size = max(11.8, read_float(typography, "axis_title_size", 11.0) + 0.8)
    base_label_size = max(10.4, read_float(typography, "tick_size", 10.0) + 0.4)
    base_detail_size = max(9.5, read_float(typography, "tick_size", 10.0) - 0.5)
    base_panel_label_size = max(11.2, read_float(typography, "panel_label_size", 11.0) + 0.6)

    base_primary_linewidth = read_float(stroke, "primary_linewidth", 2.2)
    base_secondary_linewidth = read_float(stroke, "secondary_linewidth", 1.8)
    base_connector_linewidth = read_float(stroke, "reference_linewidth", 1.0)

    figure_width_pt = read_float(layout_override, "figure_width", 13.6) * 72.0
    legacy_panel_gap_ratio = read_ratio(layout_override, "panel_gap")
    legacy_card_gap_ratio = read_ratio(layout_override, "card_gap_y")

    step_width_pt = read_float(layout_override, "flow_step_width_pt", 280.0)
    exclusion_width_pt = read_float(layout_override, "flow_exclusion_width_pt", 220.0)
    wide_block_width_pt = read_float(layout_override, "hierarchy_wide_width_pt", 344.0)
    standard_block_width_pt = read_float(layout_override, "hierarchy_block_width_pt", 208.0)
    footer_block_width_pt = read_float(layout_override, "hierarchy_footer_width_pt", 316.0)
    panel_gap_pt = read_float(
        layout_override,
        "panel_gap_pt",
        figure_width_pt * legacy_panel_gap_ratio if legacy_panel_gap_ratio is not None else 36.0,
    )
    branch_gap_pt = read_float(layout_override, "flow_branch_gap_pt", 18.0)
    side_margin_pt = read_float(layout_override, "figure_side_margin_pt", 34.0)
    heading_band_pt = read_float(layout_override, "heading_band_pt", 36.0)
    bottom_margin_pt = read_float(layout_override, "bottom_margin_pt", 24.0)
    footer_gap_pt = read_float(layout_override, "footer_gap_pt", 22.0)
    flow_step_gap_pt = read_float(
        layout_override,
        "flow_step_gap_pt",
        figure_width_pt * legacy_card_gap_ratio if legacy_card_gap_ratio is not None else 26.0,
    )
    flow_exclusion_stack_gap_pt = read_float(layout_override, "flow_exclusion_stack_gap_pt", 10.0)
    flow_split_clearance_pt = read_float(layout_override, "flow_split_clearance_pt", 12.0)
    hierarchy_nodesep = read_float(layout_override, "graphviz_hierarchy_nodesep", 0.60)
    hierarchy_ranksep = read_float(layout_override, "graphviz_hierarchy_ranksep", 0.82)
    sparse_stack_gap_pt = read_float(layout_override, "hierarchy_sparse_stack_gap_pt", 18.0)
    step_padding_pt = read_float(layout_override, "flow_step_padding_pt", 11.0)
    exclusion_padding_pt = read_float(layout_override, "flow_exclusion_padding_pt", 8.0)
    hierarchy_padding_pt = read_float(layout_override, "hierarchy_panel_padding_pt", 9.0)
    step_min_rendered_height_pt = read_float(layout_override, "flow_step_min_rendered_height_pt", 82.0)
    exclusion_min_rendered_height_pt = read_float(layout_override, "flow_exclusion_min_rendered_height_pt", 58.0)
    step_min_rendered_padding_pt = read_float(layout_override, "flow_step_min_rendered_padding_pt", 8.0)
    exclusion_min_rendered_padding_pt = read_float(layout_override, "flow_exclusion_min_rendered_padding_pt", 6.0)

    modern_roles = {"wide_top", "wide_bottom", "left_middle", "right_middle", "left_bottom", "right_bottom"}
    legacy_roles = {"wide_left", "top_right", "bottom_right"}
    declared_design_panel_roles = {
        str(item.get("layout_role") or "").strip()
        for item in design_panels
        if isinstance(item, dict) and str(item.get("layout_role") or "").strip()
    }
    if declared_design_panel_roles and not (
        declared_design_panel_roles.issubset(modern_roles) or declared_design_panel_roles.issubset(legacy_roles)
    ):
        unknown_roles = ", ".join(sorted(declared_design_panel_roles))
        raise ValueError(f"cohort_flow_figure received unsupported design panel layout roles: {unknown_roles}")
    declared_modern_layout = not declared_design_panel_roles or declared_design_panel_roles.issubset(modern_roles)
    declared_left_branch = bool({"left_middle", "left_bottom"} & declared_design_panel_roles)
    declared_right_branch = bool({"right_middle", "right_bottom"} & declared_design_panel_roles)
    sparse_modern_layout = bool(
        declared_modern_layout and declared_design_panel_roles and not (declared_left_branch and declared_right_branch)
    )

    def block_colors(style_role: str) -> tuple[str, str]:
        if style_role == "primary":
            return flow_primary_fill, flow_primary_edge
        if style_role == "context":
            return flow_context_fill, flow_context_edge
        if style_role == "audit":
            return flow_audit_fill, flow_audit_edge
        return flow_secondary_fill, flow_secondary_edge

    def build_step_spec(step: dict[str, Any]) -> _FlowNodeSpec:
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

    def build_exclusion_spec(exclusion: dict[str, Any]) -> _FlowNodeSpec:
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

    def spec_base_height(spec: _FlowNodeSpec) -> float:
        height = spec.padding_pt * 2.0
        for line in spec.lines:
            height += line.gap_before
            height += line.font_size * 1.24
        return height

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

    step_specs = [build_step_spec(step) for step in steps]
    exclusion_specs = {str(item["exclusion_id"]): build_exclusion_spec(item) for item in exclusions}
    design_specs = [build_design_panel_spec(block) for block in right_blocks]

    exclusions_by_step: dict[str, list[dict[str, Any]]] = {}
    for exclusion in exclusions:
        exclusions_by_step.setdefault(str(exclusion["from_step_id"]), []).append(exclusion)
    step_heights_pt = {spec.node_id: spec_base_height(spec) for spec in step_specs}
    exclusion_heights_pt = {spec.node_id: spec_base_height(spec) for spec in exclusion_specs.values()}
    step_stack_gap_pt: dict[str, float] = {}
    stage_cluster_heights_pt: dict[str, float] = {}
    panel_a_base_height_pt = 0.0
    for index, step in enumerate(steps):
        step_id = str(step["step_id"])
        panel_a_base_height_pt += step_heights_pt[f"step_{step_id}"]
        if index == len(steps) - 1:
            continue
        related_exclusions = exclusions_by_step.get(step_id, [])
        cluster_height_pt = 0.0
        if related_exclusions:
            cluster_height_pt = sum(
                exclusion_heights_pt[f"exclusion_{item['exclusion_id']}"] for item in related_exclusions
            ) + flow_exclusion_stack_gap_pt * max(0, len(related_exclusions) - 1)
        gap_height_pt = max(flow_step_gap_pt, cluster_height_pt + flow_split_clearance_pt * 2.0)
        step_stack_gap_pt[step_id] = gap_height_pt
        stage_cluster_heights_pt[step_id] = cluster_height_pt
        panel_a_base_height_pt += gap_height_pt
    flow_panel_base_width_pt = step_width_pt
    if exclusions:
        flow_panel_base_width_pt = max(flow_panel_base_width_pt, step_width_pt + branch_gap_pt + exclusion_width_pt)

    footer_specs = [spec for spec in design_specs if spec.panel_role == "footer_stack"]
    main_panel_specs = [spec for spec in design_specs if spec.panel_role != "footer_stack"]
    main_role_set = {spec.panel_role for spec in main_panel_specs}
    if main_role_set and not (main_role_set.issubset(modern_roles) or main_role_set.issubset(legacy_roles)):
        unknown_roles = ", ".join(sorted(main_role_set))
        raise ValueError(f"cohort_flow_figure received unsupported design panel layout roles: {unknown_roles}")
    modern_layout = not main_role_set or main_role_set.issubset(modern_roles)
    has_left_branch = bool({"left_middle", "left_bottom"} & main_role_set)
    has_right_branch = bool({"right_middle", "right_bottom"} & main_role_set)
    sparse_modern_layout = bool(modern_layout and main_role_set and not (has_left_branch and has_right_branch))

    hierarchy_dot_lines = [
        "digraph CohortFlowPanelB {",
        (
            f'graph [rankdir=TB, splines=ortho, nodesep="{hierarchy_nodesep}", '
            f'ranksep="{hierarchy_ranksep}", margin="0.12", bgcolor="white"];'
        ),
        'node [shape=plain, fontname="DejaVu Sans"];',
        f'edge [color="{flow_connector}", penwidth="{base_connector_linewidth}", arrowhead=none];',
    ]
    for spec in main_panel_specs:
        hierarchy_dot_lines.append(f'{spec.node_id} [label={_flow_html_label_for_node(spec)}];')
    blocks_by_role = {spec.panel_role: spec for spec in main_panel_specs}
    if modern_layout:
        if "left_middle" in blocks_by_role and "right_middle" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{{ rank=same; {blocks_by_role['left_middle'].node_id}; {blocks_by_role['right_middle'].node_id}; }}"
            )
        if "left_bottom" in blocks_by_role and "right_bottom" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{{ rank=same; {blocks_by_role['left_bottom'].node_id}; {blocks_by_role['right_bottom'].node_id}; }}"
            )
        if (
            "wide_top" in blocks_by_role
            and ("left_middle" in blocks_by_role or "left_bottom" in blocks_by_role)
            and ("right_middle" in blocks_by_role or "right_bottom" in blocks_by_role)
        ):
            left_target = blocks_by_role.get("left_middle") or blocks_by_role.get("left_bottom")
            right_target = blocks_by_role.get("right_middle") or blocks_by_role.get("right_bottom")
            hierarchy_dot_lines.extend(
                [
                    'hierarchy_root_branch [shape=point, width=0.01, label="", style=invis];',
                    'hierarchy_left_drop [shape=point, width=0.01, label="", style=invis];',
                    'hierarchy_right_drop [shape=point, width=0.01, label="", style=invis];',
                    "{ rank=same; hierarchy_left_drop; hierarchy_right_drop; }",
                    f"{blocks_by_role['wide_top'].node_id} -> hierarchy_root_branch [weight=14];",
                    "hierarchy_root_branch -> hierarchy_left_drop [weight=14];",
                    "hierarchy_root_branch -> hierarchy_right_drop [weight=14];",
                    f"hierarchy_left_drop -> {left_target.node_id} [weight=14];",
                    f"hierarchy_right_drop -> {right_target.node_id} [weight=14];",
                ]
            )
        if "left_middle" in blocks_by_role and "left_bottom" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{blocks_by_role['left_middle'].node_id} -> {blocks_by_role['left_bottom'].node_id} [weight=14];"
            )
        if "right_middle" in blocks_by_role and "right_bottom" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{blocks_by_role['right_middle'].node_id} -> {blocks_by_role['right_bottom'].node_id} [weight=14];"
            )
    else:
        if "wide_left" in blocks_by_role and "top_right" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{{ rank=same; {blocks_by_role['wide_left'].node_id}; {blocks_by_role['top_right'].node_id}; }}"
            )
            hierarchy_dot_lines.append(
                f"{blocks_by_role['wide_left'].node_id} -> {blocks_by_role['top_right'].node_id} [style=invis, weight=4];"
            )
        if "top_right" in blocks_by_role and "bottom_right" in blocks_by_role:
            hierarchy_dot_lines.append(
                f"{blocks_by_role['top_right'].node_id} -> {blocks_by_role['bottom_right'].node_id} [style=invis, weight=18];"
            )
    hierarchy_dot_lines.append("}")
    hierarchy_layout = _run_graphviz_layout(graph_name="cohort-flow-panel-b", dot_source="\n".join(hierarchy_dot_lines))

    footer_stack_base_height = 0.0
    if footer_specs:
        footer_stack_base_height = sum(spec_base_height(spec) for spec in footer_specs) + footer_gap_pt * max(0, len(footer_specs) - 1)
    sparse_stack_specs = (
        [
            blocks_by_role[role]
            for role in ("wide_top", "left_middle", "right_middle", "left_bottom", "right_bottom", "wide_bottom")
            if role in blocks_by_role
        ]
        if sparse_modern_layout
        else []
    )
    panel_b_main_base_height = (
        sum(spec_base_height(spec) for spec in sparse_stack_specs) + sparse_stack_gap_pt * max(0, len(sparse_stack_specs) - 1)
        if sparse_modern_layout
        else hierarchy_layout.height_pt
    )
    panel_b_main_base_width = (
        max((spec.width_pt for spec in sparse_stack_specs), default=0.0)
        if sparse_modern_layout
        else hierarchy_layout.width_pt
    )

    panel_b_total_base_height = panel_b_main_base_height + (footer_stack_base_height + footer_gap_pt if footer_specs else 0.0)
    available_width_pt = figure_width_pt - side_margin_pt * 2.0 - panel_gap_pt
    total_base_width = flow_panel_base_width_pt + max(panel_b_main_base_width, max((spec.width_pt for spec in footer_specs), default=0.0))
    scale = available_width_pt / total_base_width if total_base_width > 0 else 1.0

    def rendered_padding_for_spec(spec: _FlowNodeSpec) -> float:
        scaled_padding = spec.padding_pt * scale
        if spec.box_type == "main_step":
            return max(scaled_padding, step_min_rendered_padding_pt)
        if spec.box_type == "exclusion_box":
            return max(scaled_padding, exclusion_min_rendered_padding_pt)
        return scaled_padding

    def rendered_height_for_spec(spec: _FlowNodeSpec) -> float:
        height = rendered_padding_for_spec(spec) * 2.0
        for line in spec.lines:
            height += line.gap_before * scale
            height += line.font_size * scale * 1.24
        if spec.box_type == "main_step":
            return max(height, step_min_rendered_height_pt)
        if spec.box_type == "exclusion_box":
            return max(height, exclusion_min_rendered_height_pt)
        return height

    rendered_step_heights_pt = {spec.node_id: rendered_height_for_spec(spec) for spec in step_specs}
    rendered_exclusion_heights_pt = {
        spec.node_id: rendered_height_for_spec(spec) for spec in exclusion_specs.values()
    }
    rendered_step_stack_gap_pt: dict[str, float] = {}
    rendered_stage_cluster_heights_pt: dict[str, float] = {}
    panel_a_rendered_height_pt = 0.0
    rendered_flow_step_gap_pt = flow_step_gap_pt * scale
    rendered_flow_exclusion_stack_gap_pt = flow_exclusion_stack_gap_pt * scale
    rendered_flow_split_clearance_pt = flow_split_clearance_pt * scale
    for index, step in enumerate(steps):
        step_id = str(step["step_id"])
        panel_a_rendered_height_pt += rendered_step_heights_pt[f"step_{step_id}"]
        if index == len(steps) - 1:
            continue
        related_exclusions = exclusions_by_step.get(step_id, [])
        cluster_height_pt = 0.0
        if related_exclusions:
            cluster_height_pt = sum(
                rendered_exclusion_heights_pt[f"exclusion_{item['exclusion_id']}"] for item in related_exclusions
            ) + rendered_flow_exclusion_stack_gap_pt * max(0, len(related_exclusions) - 1)
        gap_height_pt = max(
            rendered_flow_step_gap_pt,
            cluster_height_pt + rendered_flow_split_clearance_pt * 2.0,
        )
        rendered_step_stack_gap_pt[step_id] = gap_height_pt
        rendered_stage_cluster_heights_pt[step_id] = cluster_height_pt
        panel_a_rendered_height_pt += gap_height_pt

    content_height_pt = max(panel_a_rendered_height_pt, panel_b_total_base_height * scale)
    canvas_height_pt = bottom_margin_pt + content_height_pt + heading_band_pt

    fig = plt.figure(figsize=(figure_width_pt / 72.0, canvas_height_pt / 72.0))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0.0, figure_width_pt)
    ax.set_ylim(0.0, canvas_height_pt)
    ax.axis("off")

    panel_a_x0 = side_margin_pt
    panel_a_y0 = bottom_margin_pt + content_height_pt - panel_a_rendered_height_pt
    panel_a_width_pt = flow_panel_base_width_pt * scale
    panel_b_x0 = panel_a_x0 + panel_a_width_pt + panel_gap_pt
    panel_b_total_y0 = bottom_margin_pt + content_height_pt - panel_b_total_base_height * scale
    footer_stack_height_scaled = footer_stack_base_height * scale
    panel_b_main_y0 = panel_b_total_y0 + footer_stack_height_scaled + (footer_gap_pt * scale if footer_specs else 0.0)
    panel_b_width_pt = max(panel_b_main_base_width, max((spec.width_pt for spec in footer_specs), default=0.0)) * scale
    panel_b_main_width_pt = panel_b_main_base_width * scale

    def transform_graphviz_box(box: _GraphvizNodeBox, *, panel_x0: float, panel_y0: float) -> dict[str, float]:
        return {
            "x0": panel_x0 + box.x0 * scale,
            "y0": panel_y0 + box.y0 * scale,
            "x1": panel_x0 + box.x1 * scale,
            "y1": panel_y0 + box.y1 * scale,
        }

    def draw_node(spec: _FlowNodeSpec, box: dict[str, float]) -> None:
        ax.add_patch(
            FancyBboxPatch(
                (box["x0"], box["y0"]),
                box["x1"] - box["x0"],
                box["y1"] - box["y0"],
                boxstyle=f"round,pad=0.0,rounding_size={max(8.0, 14.0 * scale):.2f}",
                linewidth=max(0.9, spec.linewidth * scale),
                edgecolor=spec.edge_color,
                facecolor=spec.fill_color,
            )
        )
        rendered_padding_pt = rendered_padding_for_spec(spec)
        x_text = box["x0"] + rendered_padding_pt
        y_cursor = box["y1"] - rendered_padding_pt
        for line in spec.lines:
            y_cursor -= line.gap_before * scale
            ax.text(
                x_text,
                y_cursor,
                line.text,
                fontsize=line.font_size * scale,
                fontweight=line.font_weight,
                color=line.color,
                ha="left",
                va="top",
            )
            y_cursor -= line.font_size * scale * 1.22

    def draw_vertical_connector(
        *,
        box_id: str,
        x: float,
        y_top: float,
        y_bottom: float,
        box_type: str,
        arrow: bool,
        record_box: bool = True,
    ) -> None:
        half_width = max(1.4, base_connector_linewidth * scale * 2.0)
        if record_box:
            guide_boxes.append(
                _flow_box_to_normalized(
                    x0=x - half_width,
                    y0=y_bottom,
                    x1=x + half_width,
                    y1=y_top,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=box_id,
                    box_type=box_type,
                )
            )
        if y_top < y_bottom:
            y_top, y_bottom = y_bottom, y_top
        if arrow:
            ax.add_patch(
                FancyArrowPatch(
                    (x, y_top),
                    (x, y_bottom),
                    arrowstyle="-|>",
                    mutation_scale=max(10.0, 12.0 * scale),
                    linewidth=max(0.9, base_connector_linewidth * scale),
                    color=flow_connector,
                )
            )
            return
        ax.plot([x, x], [y_top, y_bottom], color=flow_connector, linewidth=max(0.9, base_connector_linewidth * scale))

    def draw_horizontal_connector(
        *,
        box_id: str,
        x_left: float,
        x_right: float,
        y: float,
        box_type: str,
        arrow: bool,
        record_box: bool = True,
    ) -> None:
        half_height = max(1.4, base_connector_linewidth * scale * 2.0)
        if record_box:
            guide_boxes.append(
                _flow_box_to_normalized(
                    x0=x_left,
                    y0=y - half_height,
                    x1=x_right,
                    y1=y + half_height,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=box_id,
                    box_type=box_type,
                )
            )
        if x_left > x_right:
            x_left, x_right = x_right, x_left
        if arrow:
            ax.add_patch(
                FancyArrowPatch(
                    (x_left, y),
                    (x_right, y),
                    arrowstyle="-|>",
                    mutation_scale=max(9.0, 11.0 * scale),
                    linewidth=max(0.9, base_connector_linewidth * scale),
                    color=flow_connector,
                )
            )
            return
        ax.plot([x_left, x_right], [y, y], color=flow_connector, linewidth=max(0.9, base_connector_linewidth * scale))

    guide_boxes: list[dict[str, Any]] = []
    layout_boxes: list[dict[str, Any]] = []
    panel_boxes: list[dict[str, Any]] = []

    next_step_by_id = {
        str(step["step_id"]): str(steps[index + 1]["step_id"])
        for index, step in enumerate(steps[:-1])
    }
    step_boxes_by_id: dict[str, dict[str, float]] = {}
    exclusion_boxes_by_id: dict[str, dict[str, float]] = {}
    stage_split_y_by_step: dict[str, float] = {}
    panel_a_top = panel_a_y0 + panel_a_rendered_height_pt
    current_top = panel_a_top
    exclusion_x0 = panel_a_x0 + (step_width_pt + branch_gap_pt) * scale

    for index, spec in enumerate(step_specs):
        step_height_pt = rendered_step_heights_pt[spec.node_id]
        box = {
            "x0": panel_a_x0,
            "y0": current_top - step_height_pt,
            "x1": panel_a_x0 + spec.width_pt * scale,
            "y1": current_top,
        }
        draw_node(spec, box)
        step_boxes_by_id[spec.node_id] = box
        layout_boxes.append(
            _flow_box_to_normalized(
                **box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=spec.box_id,
                box_type=spec.box_type,
            )
        )
        if index == len(steps) - 1:
            continue
        step_id = str(steps[index]["step_id"])
        stage_gap_pt = rendered_step_stack_gap_pt[step_id]
        stage_split_y = box["y0"] - stage_gap_pt / 2.0
        stage_split_y_by_step[step_id] = stage_split_y
        related_exclusions = exclusions_by_step.get(step_id, [])
        if related_exclusions:
            cluster_height_pt = rendered_stage_cluster_heights_pt[step_id]
            cluster_top = stage_split_y + cluster_height_pt / 2.0
            for exclusion in related_exclusions:
                exclusion_spec = exclusion_specs[str(exclusion["exclusion_id"])]
                exclusion_height_pt = rendered_exclusion_heights_pt[exclusion_spec.node_id]
                exclusion_box = {
                    "x0": exclusion_x0,
                    "y0": cluster_top - exclusion_height_pt,
                    "x1": exclusion_x0 + exclusion_spec.width_pt * scale,
                    "y1": cluster_top,
                }
                cluster_top = exclusion_box["y0"] - rendered_flow_exclusion_stack_gap_pt
                draw_node(exclusion_spec, exclusion_box)
                exclusion_boxes_by_id[exclusion_spec.node_id] = exclusion_box
                layout_boxes.append(
                    _flow_box_to_normalized(
                        **exclusion_box,
                        canvas_width_pt=figure_width_pt,
                        canvas_height_pt=canvas_height_pt,
                        box_id=exclusion_spec.box_id,
                        box_type=exclusion_spec.box_type,
                    )
                )
        current_top = box["y0"] - stage_gap_pt

    flow_panel_union_boxes = [*step_boxes_by_id.values(), *exclusion_boxes_by_id.values()]
    if flow_panel_union_boxes:
        union_box = _flow_union_box(boxes=flow_panel_union_boxes, box_id="flow_panel", box_type="flow_panel")
        panel_boxes.append(
            _flow_box_to_normalized(
                **union_box,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
            )
        )

    for upper_step, lower_step in zip(steps, steps[1:], strict=False):
        upper_box = step_boxes_by_id[f"step_{upper_step['step_id']}"]
        lower_box = step_boxes_by_id[f"step_{lower_step['step_id']}"]
        spine_x = (upper_box["x0"] + upper_box["x1"]) / 2.0
        spine_box_id = f"flow_spine_{upper_step['step_id']}_to_{lower_step['step_id']}"
        related_exclusions = exclusions_by_step.get(str(upper_step["step_id"]), [])
        if related_exclusions:
            half_width = max(1.4, base_connector_linewidth * scale * 2.0)
            guide_boxes.append(
                _flow_box_to_normalized(
                    x0=spine_x - half_width,
                    y0=lower_box["y1"],
                    x1=spine_x + half_width,
                    y1=upper_box["y0"],
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=spine_box_id,
                    box_type="flow_connector",
                )
            )
            split_y = stage_split_y_by_step[str(upper_step["step_id"])]
            draw_vertical_connector(
                box_id=f"{spine_box_id}_upper",
                x=spine_x,
                y_top=upper_box["y0"],
                y_bottom=split_y,
                box_type="flow_connector",
                arrow=False,
                record_box=False,
            )
            draw_vertical_connector(
                box_id=f"{spine_box_id}_lower",
                x=spine_x,
                y_top=split_y,
                y_bottom=lower_box["y1"],
                box_type="flow_connector",
                arrow=True,
                record_box=False,
            )
            continue
        draw_vertical_connector(
            box_id=spine_box_id,
            x=spine_x,
            y_top=upper_box["y0"],
            y_bottom=lower_box["y1"],
            box_type="flow_connector",
            arrow=True,
        )

    for exclusion in exclusions:
        source_step_id = str(exclusion["from_step_id"])
        next_step_id = next_step_by_id.get(source_step_id)
        if next_step_id is None:
            continue
        source_box = step_boxes_by_id[f"step_{source_step_id}"]
        exclusion_box = exclusion_boxes_by_id[f"exclusion_{exclusion['exclusion_id']}"]
        spine_x = (source_box["x0"] + source_box["x1"]) / 2.0
        split_y = stage_split_y_by_step.get(source_step_id)
        exclusion_center_y = (exclusion_box["y0"] + exclusion_box["y1"]) / 2.0
        if split_y is not None and abs(exclusion_center_y - split_y) > 0.5:
            draw_vertical_connector(
                box_id=f"flow_branch_stem_{exclusion['exclusion_id']}",
                x=spine_x,
                y_top=max(split_y, exclusion_center_y),
                y_bottom=min(split_y, exclusion_center_y),
                box_type="flow_branch_connector",
                arrow=False,
            )
        draw_horizontal_connector(
            box_id=f"flow_branch_{exclusion['exclusion_id']}",
            x_left=spine_x,
            x_right=exclusion_box["x0"],
            y=exclusion_center_y,
            box_type="flow_branch_connector",
            arrow=True,
        )

    secondary_panel_regions: dict[str, dict[str, float]] = {}
    if sparse_modern_layout:
        current_top = panel_b_main_y0 + panel_b_main_base_height * scale
        for spec in sparse_stack_specs:
            box_height_pt = spec_base_height(spec) * scale
            box_width_pt = spec.width_pt * scale
            box = {
                "x0": panel_b_x0 + (panel_b_main_width_pt - box_width_pt) / 2.0,
                "y0": current_top - box_height_pt,
                "x1": panel_b_x0 + (panel_b_main_width_pt - box_width_pt) / 2.0 + box_width_pt,
                "y1": current_top,
            }
            draw_node(spec, box)
            secondary_panel_regions[spec.panel_role] = box
            panel_boxes.append(
                _flow_box_to_normalized(
                    **box,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=spec.box_id,
                    box_type=spec.box_type,
                )
            )
            current_top = box["y0"] - sparse_stack_gap_pt * scale
    else:
        for spec in main_panel_specs:
            box = transform_graphviz_box(hierarchy_layout.nodes[spec.node_id], panel_x0=panel_b_x0, panel_y0=panel_b_main_y0)
            if modern_layout and spec.panel_role == "wide_top":
                box = {
                    "x0": panel_b_x0 - 1.0,
                    "y0": box["y0"],
                    "x1": panel_b_x0 + panel_b_main_width_pt + 1.0,
                    "y1": box["y1"],
                }
            draw_node(spec, box)
            secondary_panel_regions[spec.panel_role] = box
            panel_boxes.append(
                _flow_box_to_normalized(
                    **box,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=spec.box_id,
                    box_type=spec.box_type,
                )
            )

    if footer_specs:
        footer_cursor_y = panel_b_total_y0
        for spec in footer_specs:
            footer_height_pt = spec_base_height(spec) * scale
            footer_x0 = panel_b_x0 + (panel_b_width_pt - spec.width_pt * scale) / 2.0
            footer_box = {
                "x0": footer_x0,
                "y0": footer_cursor_y,
                "x1": footer_x0 + spec.width_pt * scale,
                "y1": footer_cursor_y + footer_height_pt,
            }
            draw_node(spec, footer_box)
            secondary_panel_regions[spec.panel_role] = footer_box
            panel_boxes.append(
                _flow_box_to_normalized(
                    **footer_box,
                    canvas_width_pt=figure_width_pt,
                    canvas_height_pt=canvas_height_pt,
                    box_id=spec.box_id,
                    box_type=spec.box_type,
                )
            )
            footer_cursor_y = footer_box["y1"] + footer_gap_pt * scale

    if modern_layout:
        if sparse_modern_layout:
            sparse_stack_roles = [spec.panel_role for spec in sparse_stack_specs]
            for upper_role, lower_role in zip(sparse_stack_roles, sparse_stack_roles[1:], strict=False):
                upper_region = secondary_panel_regions.get(upper_role)
                lower_region = secondary_panel_regions.get(lower_role)
                if upper_region is None or lower_region is None:
                    continue
                draw_vertical_connector(
                    box_id=f"hierarchy_connector_{upper_role}_to_{lower_role}",
                    x=(upper_region["x0"] + upper_region["x1"]) / 2.0,
                    y_top=upper_region["y0"],
                    y_bottom=lower_region["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )
        else:
            validation_region = secondary_panel_regions.get("wide_top")
            left_middle_region = secondary_panel_regions.get("left_middle")
            right_middle_region = secondary_panel_regions.get("right_middle")
            left_bottom_region = secondary_panel_regions.get("left_bottom")
            right_bottom_region = secondary_panel_regions.get("right_bottom")
            left_branch_target = left_middle_region or left_bottom_region
            right_branch_target = right_middle_region or right_bottom_region
            branch_root = hierarchy_layout.nodes.get("hierarchy_root_branch")
            left_drop = hierarchy_layout.nodes.get("hierarchy_left_drop")
            right_drop = hierarchy_layout.nodes.get("hierarchy_right_drop")
            if (
                validation_region is not None
                and left_branch_target is not None
                and right_branch_target is not None
                and branch_root is not None
                and left_drop is not None
                and right_drop is not None
            ):
                branch_y = panel_b_main_y0 + branch_root.cy * scale
                validation_center_x = (validation_region["x0"] + validation_region["x1"]) / 2.0
                left_branch_center_x = (left_branch_target["x0"] + left_branch_target["x1"]) / 2.0
                right_branch_center_x = (right_branch_target["x0"] + right_branch_target["x1"]) / 2.0
                draw_vertical_connector(
                    box_id="hierarchy_root_trunk",
                    x=validation_center_x,
                    y_top=validation_region["y0"],
                    y_bottom=branch_y,
                    box_type="hierarchy_connector",
                    arrow=False,
                )
                draw_horizontal_connector(
                    box_id="hierarchy_root_branch",
                    x_left=left_branch_center_x,
                    x_right=right_branch_center_x,
                    y=branch_y,
                    box_type="hierarchy_connector",
                    arrow=False,
                )
                draw_vertical_connector(
                    box_id="hierarchy_connector_branch_to_left",
                    x=left_branch_center_x,
                    y_top=branch_y,
                    y_bottom=left_branch_target["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )
                draw_vertical_connector(
                    box_id="hierarchy_connector_branch_to_right",
                    x=right_branch_center_x,
                    y_top=branch_y,
                    y_bottom=right_branch_target["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )
            if left_middle_region is not None and left_bottom_region is not None:
                draw_vertical_connector(
                    box_id="hierarchy_connector_left_middle_to_left_bottom",
                    x=(left_middle_region["x0"] + left_middle_region["x1"]) / 2.0,
                    y_top=left_middle_region["y0"],
                    y_bottom=left_bottom_region["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )
            if right_middle_region is not None and right_bottom_region is not None:
                draw_vertical_connector(
                    box_id="hierarchy_connector_right_middle_to_right_bottom",
                    x=(right_middle_region["x0"] + right_middle_region["x1"]) / 2.0,
                    y_top=right_middle_region["y0"],
                    y_bottom=right_bottom_region["y1"],
                    box_type="hierarchy_connector",
                    arrow=False,
                )

    panel_a_outer = {
        "x0": max(0.0, panel_a_x0 - 10.0 * scale),
        "y0": max(0.0, bottom_margin_pt - 4.0),
        "x1": min(figure_width_pt, panel_a_x0 + panel_a_width_pt + 10.0 * scale),
        "y1": min(canvas_height_pt, canvas_height_pt - 6.0),
    }
    panel_b_outer = {
        "x0": max(0.0, panel_b_x0 - 10.0 * scale),
        "y0": max(0.0, bottom_margin_pt - 4.0),
        "x1": min(figure_width_pt, panel_b_x0 + panel_b_width_pt + 10.0 * scale),
        "y1": min(canvas_height_pt, canvas_height_pt - 6.0),
    }
    panel_boxes.insert(
        0,
        _flow_box_to_normalized(
            **panel_b_outer,
            canvas_width_pt=figure_width_pt,
            canvas_height_pt=canvas_height_pt,
            box_id="subfigure_panel_B",
            box_type="subfigure_panel",
        ),
    )
    panel_boxes.insert(
        0,
        _flow_box_to_normalized(
            **panel_a_outer,
            canvas_width_pt=figure_width_pt,
            canvas_height_pt=canvas_height_pt,
            box_id="subfigure_panel_A",
            box_type="subfigure_panel",
        ),
    )

    heading_y = canvas_height_pt - 12.0
    for panel_id, x0, heading in (
        ("A", panel_a_x0, "Cohort assembly"),
        ("B", panel_b_x0, "Validation and model hierarchy"),
    ):
        ax.text(
            x0,
            heading_y,
            panel_id,
            fontsize=base_panel_label_size * scale,
            fontweight="bold",
            color=flow_panel_label,
            ha="left",
            va="top",
        )
        label_width = _measure_flow_text_width_pt(panel_id, font_size=base_panel_label_size * scale, font_weight="bold")
        layout_boxes.append(
            _flow_box_to_normalized(
                x0=x0,
                y0=heading_y - base_panel_label_size * scale * 1.2,
                x1=x0 + label_width,
                y1=heading_y,
                canvas_width_pt=figure_width_pt,
                canvas_height_pt=canvas_height_pt,
                box_id=f"panel_label_{panel_id}",
                box_type="panel_label",
            )
        )
        ax.text(
            x0 + label_width + 12.0 * scale,
            heading_y - 1.0,
            heading,
            fontsize=base_card_title_size * scale,
            fontweight="bold",
            color=flow_title_text,
            ha="left",
            va="top",
        )

    output_svg_path.parent.mkdir(parents=True, exist_ok=True)
    flow_nodes = []
    for spec in step_specs:
        box = step_boxes_by_id.get(spec.node_id)
        if box is None:
            continue
        flow_nodes.append(
            {
                "box_id": spec.box_id,
                "box_type": spec.box_type,
                "line_count": len(spec.lines),
                "max_line_chars": max((len(line.text) for line in spec.lines), default=0),
                "rendered_height_pt": box["y1"] - box["y0"],
                "rendered_width_pt": box["x1"] - box["x0"],
                "padding_pt": rendered_padding_for_spec(spec),
            }
        )
    for spec in exclusion_specs.values():
        box = exclusion_boxes_by_id.get(spec.node_id)
        if box is None:
            continue
        flow_nodes.append(
            {
                "box_id": spec.box_id,
                "box_type": spec.box_type,
                "line_count": len(spec.lines),
                "max_line_chars": max((len(line.text) for line in spec.lines), default=0),
                "rendered_height_pt": box["y1"] - box["y0"],
                "rendered_width_pt": box["x1"] - box["x0"],
                "padding_pt": rendered_padding_for_spec(spec),
            }
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
                "steps": steps,
                "exclusions": exclusions,
                "endpoint_inventory": endpoint_inventory,
                "design_panels": design_panels,
                "flow_nodes": flow_nodes,
            },
            "render_context": render_context_payload,
        },
    )

    fig.savefig(output_svg_path, format="svg")
    fig.savefig(output_png_path, format="png", dpi=220)
    plt.close(fig)

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


def render_illustration_shell(
    *,
    template_id: str,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
    output_svg_path: Path,
    output_png_path: Path,
    output_layout_path: Path,
    payload_path: Path | None = None,
) -> dict[str, str]:
    _, template_short_id = _require_namespaced_registry_id(template_id, label="template_id")
    resolved_payload_path = payload_path or Path(f"<inline:{template_short_id}>")
    if template_short_id == "cohort_flow_figure":
        normalized_shell_payload = _validate_cohort_flow_payload(resolved_payload_path, shell_payload)
        title = str(normalized_shell_payload.get("title") or "Cohort flow").strip() or "Cohort flow"
        _render_cohort_flow_figure(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            title=title,
            steps=list(normalized_shell_payload["steps"]),
            exclusions=list(normalized_shell_payload["exclusions"]),
            endpoint_inventory=list(normalized_shell_payload["endpoint_inventory"]),
            design_panels=list(normalized_shell_payload["design_panels"]),
            render_context=render_context,
        )
        return {
            "title": title,
            "caption": str(
                normalized_shell_payload.get("caption") or "Study cohort flow and analysis population accounting."
            ).strip(),
        }
    if template_short_id == "submission_graphical_abstract":
        normalized_shell_payload = _validate_submission_graphical_abstract_payload(resolved_payload_path, shell_payload)
        _render_submission_graphical_abstract(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
            shell_payload=normalized_shell_payload,
            render_context=render_context,
        )
        return {
            "title": str(normalized_shell_payload.get("title") or "").strip(),
            "caption": str(normalized_shell_payload.get("caption") or "").strip(),
        }
    raise RuntimeError(f"unsupported illustration shell `{template_id}`")
