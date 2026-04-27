from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from ...shared import (
    _FlowNodeSpec,
    _GraphvizNodeBox,
    _flow_box_to_normalized,
    _flow_html_label_for_node,
    _flow_union_box,
    _measure_flow_text_width_pt,
    _require_non_empty_string,
    _run_graphviz_layout,
)

from ._single_panel import _render_single_panel_cards
from ._specs import (
    _build_cohort_flow_design_panel_specs,
    _build_cohort_flow_exclusion_spec,
    _build_cohort_flow_step_spec,
    _cohort_flow_block_colors,
    _cohort_flow_spec_base_height,
)
from ._write_outputs import _write_multi_panel_outputs

_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}
_COHORT_FLOW_LAYOUT_MODES = {"two_panel_flow", "single_panel_cards"}
_COHORT_FLOW_STEP_ROLE_LABELS: dict[str, str] = {
    "historical_reference": "Historical patient reference",
    "current_patient_surface": "Current patient surface",
    "clinician_surface": "Clinician surface",
}


def _render_cohort_flow_figure(
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
    layout_mode: str,
    comparison_summary: dict[str, Any],
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

    if layout_mode == "single_panel_cards":
        _render_single_panel_cards(
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            output_layout_path=output_layout_path,
            steps=steps,
            exclusions=exclusions,
            endpoint_inventory=endpoint_inventory,
            design_panels=design_panels,
            comparison_summary=comparison_summary,
            layout_override=layout_override,
            side_margin_pt=side_margin_pt,
            figure_width_pt=figure_width_pt,
            flow_main_fill=flow_main_fill,
            flow_main_edge=flow_main_edge,
            flow_secondary_fill=flow_secondary_fill,
            flow_secondary_edge=flow_secondary_edge,
            flow_context_fill=flow_context_fill,
            flow_primary_edge=flow_primary_edge,
            flow_title_text=flow_title_text,
            flow_body_text=flow_body_text,
            flow_connector=flow_connector,
            base_card_title_size=base_card_title_size,
            base_label_size=base_label_size,
            base_detail_size=base_detail_size,
            base_secondary_linewidth=base_secondary_linewidth,
            base_connector_linewidth=base_connector_linewidth,
            render_context_payload=render_context_payload,
            read_float=read_float,
        )
        return

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
        return _cohort_flow_block_colors(
            style_role=style_role,
            flow_primary_fill=flow_primary_fill,
            flow_primary_edge=flow_primary_edge,
            flow_context_fill=flow_context_fill,
            flow_context_edge=flow_context_edge,
            flow_audit_fill=flow_audit_fill,
            flow_audit_edge=flow_audit_edge,
            flow_secondary_fill=flow_secondary_fill,
            flow_secondary_edge=flow_secondary_edge,
        )

    def build_step_spec(step: dict[str, Any]) -> _FlowNodeSpec:
        return _build_cohort_flow_step_spec(
            step=step,
            step_width_pt=step_width_pt,
            base_card_title_size=base_card_title_size,
            base_detail_size=base_detail_size,
            base_label_size=base_label_size,
            flow_title_text=flow_title_text,
            flow_body_text=flow_body_text,
            flow_main_fill=flow_main_fill,
            flow_main_edge=flow_main_edge,
            base_secondary_linewidth=base_secondary_linewidth,
            step_padding_pt=step_padding_pt,
        )

    def build_exclusion_spec(exclusion: dict[str, Any]) -> _FlowNodeSpec:
        return _build_cohort_flow_exclusion_spec(
            exclusion=exclusion,
            exclusion_width_pt=exclusion_width_pt,
            base_label_size=base_label_size,
            base_detail_size=base_detail_size,
            flow_exclusion_fill=flow_exclusion_fill,
            flow_exclusion_edge=flow_exclusion_edge,
            base_secondary_linewidth=base_secondary_linewidth,
            exclusion_padding_pt=exclusion_padding_pt,
        )

    step_specs = [build_step_spec(step) for step in steps]
    exclusion_specs = {str(item["exclusion_id"]): build_exclusion_spec(item) for item in exclusions}
    design_specs = _build_cohort_flow_design_panel_specs(
        design_panels=design_panels,
        endpoint_inventory=endpoint_inventory,
        block_colors=block_colors,
        sparse_modern_layout=sparse_modern_layout,
        wide_block_width_pt=wide_block_width_pt,
        standard_block_width_pt=standard_block_width_pt,
        footer_block_width_pt=footer_block_width_pt,
        base_card_title_size=base_card_title_size,
        base_label_size=base_label_size,
        base_detail_size=base_detail_size,
        flow_title_text=flow_title_text,
        flow_body_text=flow_body_text,
        base_primary_linewidth=base_primary_linewidth,
        base_secondary_linewidth=base_secondary_linewidth,
        hierarchy_padding_pt=hierarchy_padding_pt,
    )


    exclusions_by_step: dict[str, list[dict[str, Any]]] = {}
    for exclusion in exclusions:
        exclusions_by_step.setdefault(str(exclusion["from_step_id"]), []).append(exclusion)
    step_heights_pt = {spec.node_id: _cohort_flow_spec_base_height(spec) for spec in step_specs}
    exclusion_heights_pt = {spec.node_id: _cohort_flow_spec_base_height(spec) for spec in exclusion_specs.values()}
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
        footer_stack_base_height = sum(_cohort_flow_spec_base_height(spec) for spec in footer_specs) + footer_gap_pt * max(0, len(footer_specs) - 1)
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
        sum(_cohort_flow_spec_base_height(spec) for spec in sparse_stack_specs) + sparse_stack_gap_pt * max(0, len(sparse_stack_specs) - 1)
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
            box_height_pt = _cohort_flow_spec_base_height(spec) * scale
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
            footer_height_pt = _cohort_flow_spec_base_height(spec) * scale
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

    _write_multi_panel_outputs(
        output_svg_path=output_svg_path,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        output_layout_path=output_layout_path,
        step_specs=step_specs,
        exclusion_specs=exclusion_specs,
        step_boxes_by_id=step_boxes_by_id,
        exclusion_boxes_by_id=exclusion_boxes_by_id,
        rendered_padding_for_spec=rendered_padding_for_spec,
        layout_boxes=layout_boxes,
        panel_boxes=panel_boxes,
        guide_boxes=guide_boxes,
        steps=steps,
        exclusions=exclusions,
        endpoint_inventory=endpoint_inventory,
        design_panels=design_panels,
        render_context_payload=render_context_payload,
        fig=fig,
    )
