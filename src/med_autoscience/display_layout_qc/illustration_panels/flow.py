from __future__ import annotations

from ..shared import (
    Any,
    Box,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_of_type,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _first_box_of_type,
    _issue,
    _require_numeric,
)

def _check_publication_illustration_flow(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("main_step",)))

    flow_nodes = sidecar.metrics.get("flow_nodes")
    if not isinstance(flow_nodes, list) or not flow_nodes:
        issues.append(
            _issue(
                rule_id="flow_nodes_missing",
                message="illustration flow qc requires flow_nodes metrics for node-level readability checks",
                target="metrics.flow_nodes",
            )
        )
    else:
        for index, item in enumerate(flow_nodes):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.flow_nodes[{index}] must be an object")
            box_type = str(item.get("box_type") or "").strip()
            rendered_height_pt = _require_numeric(
                item.get("rendered_height_pt"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].rendered_height_pt",
            )
            rendered_width_pt = _require_numeric(
                item.get("rendered_width_pt"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].rendered_width_pt",
            )
            line_count = _require_numeric(
                item.get("line_count"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].line_count",
            )
            max_line_chars = _require_numeric(
                item.get("max_line_chars"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].max_line_chars",
            )
            padding_pt = _require_numeric(
                item.get("padding_pt"),
                label=f"layout_sidecar.metrics.flow_nodes[{index}].padding_pt",
            )
            minimum_height_pt = 80.0 if box_type == "main_step" else 56.0
            minimum_padding_pt = 8.0 if box_type == "main_step" else 6.0
            if rendered_height_pt < minimum_height_pt:
                issues.append(
                    _issue(
                        rule_id="flow_node_height_too_small",
                        message="flow node height is too small for manuscript-facing readability",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"rendered_height_pt": rendered_height_pt, "box_type": box_type},
                        expected={"minimum_height_pt": minimum_height_pt},
                    )
                )
            if rendered_width_pt < 160.0:
                issues.append(
                    _issue(
                        rule_id="flow_node_width_too_small",
                        message="flow node width is too small for manuscript-facing readability",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"rendered_width_pt": rendered_width_pt, "box_type": box_type},
                        expected={"minimum_width_pt": 160.0},
                    )
                )
            if padding_pt < minimum_padding_pt:
                issues.append(
                    _issue(
                        rule_id="flow_node_padding_too_small",
                        message="flow node padding is too small for manuscript-facing readability",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"padding_pt": padding_pt, "box_type": box_type},
                        expected={"minimum_padding_pt": minimum_padding_pt},
                    )
                )
            if line_count > 0 and max_line_chars > 44:
                issues.append(
                    _issue(
                        rule_id="flow_node_text_density_high",
                        message="flow node line length is too dense for the audited cohort-flow shell",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"line_count": line_count, "max_line_chars": max_line_chars},
                        expected={"maximum_max_line_chars": 44},
                    )
                )

    step_boxes = _boxes_of_type(sidecar.layout_boxes, "main_step")
    sorted_step_boxes = tuple(
        sorted(step_boxes, key=lambda box: (-((box.y0 + box.y1) / 2.0), box.x0, box.box_id))
    )
    issues.extend(_check_pairwise_non_overlap(step_boxes, rule_id="main_step_overlap", target="main_step"))

    exclusion_boxes = _boxes_of_type(sidecar.layout_boxes, "exclusion_box")
    issues.extend(_check_pairwise_non_overlap(exclusion_boxes, rule_id="exclusion_box_overlap", target="exclusion_box"))
    for exclusion_box in exclusion_boxes:
        for step_box in step_boxes:
            if not _boxes_overlap(exclusion_box, step_box):
                continue
            issues.append(
                _issue(
                    rule_id="exclusion_step_overlap",
                    message="exclusion box must not overlap a main cohort step",
                    target="exclusion_box",
                    box_refs=(exclusion_box.box_id, step_box.box_id),
                )
            )

    subfigure_panels = {box.box_id: box for box in _boxes_of_type(sidecar.panel_boxes, "subfigure_panel")}
    for required_box_id in ("subfigure_panel_A", "subfigure_panel_B"):
        if required_box_id in subfigure_panels:
            continue
        issues.append(
            _issue(
                rule_id="missing_subfigure_panel",
                message="illustration flow requires both Panel A and Panel B containers",
                target="panel_boxes",
                expected=required_box_id,
            )
        )

    panel_labels = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "panel_label")}
    for required_box_id in ("panel_label_A", "panel_label_B"):
        if required_box_id in panel_labels:
            continue
        issues.append(
            _issue(
                rule_id="missing_panel_label",
                message="illustration flow requires explicit A/B panel labels",
                target="layout_boxes",
                expected=required_box_id,
            )
        )

    flow_panel = _first_box_of_type(sidecar.panel_boxes, "flow_panel")
    panel_a = subfigure_panels.get("subfigure_panel_A")
    if panel_a is not None:
        if flow_panel is not None and not _box_within_box(flow_panel, panel_a):
            issues.append(
                _issue(
                    rule_id="flow_panel_out_of_subfigure",
                    message="flow panel must stay within Panel A",
                    target="flow_panel",
                    box_refs=(flow_panel.box_id, panel_a.box_id),
                )
            )
        for box in step_boxes + exclusion_boxes:
            if _box_within_box(box, panel_a):
                continue
            issues.append(
                _issue(
                    rule_id="flow_content_out_of_panel_a",
                    message="cohort flow content must stay within Panel A",
                    target=box.box_type,
                    box_refs=(box.box_id, panel_a.box_id),
                )
            )

    secondary_panels = _boxes_of_type(sidecar.panel_boxes, "secondary_panel")
    issues.extend(_check_pairwise_non_overlap(secondary_panels, rule_id="secondary_panel_overlap", target="secondary_panel"))
    panel_b = subfigure_panels.get("subfigure_panel_B")
    for secondary_panel in secondary_panels:
        if panel_b is not None and not _box_within_box(secondary_panel, panel_b):
            issues.append(
                _issue(
                    rule_id="secondary_panel_out_of_subfigure",
                    message="secondary analytic panels must stay within Panel B",
                    target="secondary_panel",
                    box_refs=(secondary_panel.box_id, panel_b.box_id),
                )
            )
        for step_box in step_boxes:
            if not _boxes_overlap(secondary_panel, step_box):
                continue
            issues.append(
                _issue(
                    rule_id="secondary_panel_step_overlap",
                    message="secondary panel must not overlap a main cohort step",
                    target="secondary_panel",
                    box_refs=(secondary_panel.box_id, step_box.box_id),
                )
            )

    for label_box_id, label_box in panel_labels.items():
        suffix = label_box_id.removeprefix("panel_label_")
        parent_panel = subfigure_panels.get(f"subfigure_panel_{suffix}")
        if parent_panel is None or _box_within_box(label_box, parent_panel):
            continue
        issues.append(
            _issue(
                rule_id="panel_label_out_of_subfigure",
                message="panel label must stay within its declared subfigure panel",
                target="panel_label",
                box_refs=(label_box.box_id, parent_panel.box_id),
            )
        )

    flow_connectors = {box.box_id: box for box in _boxes_of_type(sidecar.guide_boxes, "flow_connector")}
    flow_branch_connectors = {box.box_id: box for box in _boxes_of_type(sidecar.guide_boxes, "flow_branch_connector")}
    expected_step_ids = [str(item.get("step_id") or "").strip() for item in sidecar.metrics.get("steps", []) if isinstance(item, dict)]
    expected_step_ids = [item for item in expected_step_ids if item]
    if not expected_step_ids:
        expected_step_ids = [box.box_id.removeprefix("step_") for box in sorted_step_boxes]
    expected_exclusions = [
        str(item.get("exclusion_id") or "").strip()
        for item in sidecar.metrics.get("exclusions", [])
        if isinstance(item, dict) and str(item.get("exclusion_id") or "").strip()
    ]
    if not expected_exclusions:
        expected_exclusions = [box.box_id.removeprefix("exclusion_") for box in exclusion_boxes]

    missing_flow_connectors: list[str] = []
    for upper_step_id, lower_step_id in zip(expected_step_ids, expected_step_ids[1:], strict=False):
        connector_id = f"flow_spine_{upper_step_id}_to_{lower_step_id}"
        if connector_id not in flow_connectors:
            missing_flow_connectors.append(connector_id)
    for exclusion_id in expected_exclusions:
        connector_id = f"flow_branch_{exclusion_id}"
        if connector_id not in flow_branch_connectors:
            missing_flow_connectors.append(connector_id)
    if missing_flow_connectors:
        issues.append(
            _issue(
                rule_id="missing_flow_connector",
                message="illustration flow requires explicit spine and exclusion branch connectors",
                target="guide_boxes",
                expected=missing_flow_connectors,
            )
        )

    def _vertical_center(box: Box) -> float:
        return (box.y0 + box.y1) / 2.0

    def _stage_gap_contains_y(y_value: float) -> bool:
        epsilon = 1e-6
        for upper_step, lower_step in zip(sorted_step_boxes, sorted_step_boxes[1:], strict=False):
            if lower_step.y1 - epsilon <= y_value <= upper_step.y0 + epsilon:
                return True
        return False

    for exclusion_box in exclusion_boxes:
        if len(sorted_step_boxes) < 2 or _stage_gap_contains_y(_vertical_center(exclusion_box)):
            continue
        issues.append(
            _issue(
                rule_id="misanchored_exclusion_box",
                message="exclusion box must be centered on a stage boundary between adjacent main steps",
                target="exclusion_box",
                box_refs=(exclusion_box.box_id,),
            )
        )

    for connector_box in flow_branch_connectors.values():
        if len(sorted_step_boxes) < 2 or _stage_gap_contains_y(_vertical_center(connector_box)):
            continue
        issues.append(
            _issue(
                rule_id="misanchored_flow_branch",
                message="exclusion branch connector must originate from a stage boundary between adjacent main steps",
                target="flow_branch_connector",
                box_refs=(connector_box.box_id,),
            )
        )

    hierarchy_connectors = {box.box_id: box for box in _boxes_of_type(sidecar.guide_boxes, "hierarchy_connector")}
    design_panel_roles = {
        str(item.get("layout_role") or "").strip()
        for item in sidecar.metrics.get("design_panels", [])
        if isinstance(item, dict)
    }
    expected_hierarchy_connectors: list[str] = []
    if "wide_top" in design_panel_roles and (
        ("left_middle" in design_panel_roles or "left_bottom" in design_panel_roles)
        and ("right_middle" in design_panel_roles or "right_bottom" in design_panel_roles)
    ):
        expected_hierarchy_connectors.extend(["hierarchy_root_trunk", "hierarchy_root_branch"])
    if {"left_middle", "left_bottom"} <= design_panel_roles:
        expected_hierarchy_connectors.append("hierarchy_connector_left_middle_to_left_bottom")
    if {"right_middle", "right_bottom"} <= design_panel_roles:
        expected_hierarchy_connectors.append("hierarchy_connector_right_middle_to_right_bottom")
    missing_hierarchy_connectors = [box_id for box_id in expected_hierarchy_connectors if box_id not in hierarchy_connectors]
    if missing_hierarchy_connectors:
        issues.append(
            _issue(
                rule_id="missing_hierarchy_connector",
                message="illustration flow requires rooted hierarchy connectors for Panel B",
                target="guide_boxes",
                expected=missing_hierarchy_connectors,
            )
        )

    return issues
