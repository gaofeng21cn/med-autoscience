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
    if str(sidecar.metrics.get("layout_mode") or "").strip() == "source_layer_accounting":
        issues.extend(_check_source_layer_accounting_flow(sidecar))
        return issues
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("main_step",)))
    if str(sidecar.metrics.get("layout_mode") or "").strip() == "participant_flow":
        issues.extend(_check_participant_reporting_flow(sidecar))
        return issues

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


def _check_source_layer_accounting_flow(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    is_v2_layout = (
        str(sidecar.metrics.get("layout_generation") or "").strip() == "scholarskills_cohort_flow_v2"
        and str(sidecar.metrics.get("flow_visual_policy") or "").strip()
        == "purpose_first_reporting_flow_no_legacy_card_shell"
    )
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                ("main_step", "source_layer_box", "coverage_step", "section_label")
                if is_v2_layout
                else ("main_step", "source_layer_box", "coverage_bar", "panel_label")
            ),
        )
    )
    panel_boxes = {box.box_id: box for box in _boxes_of_type(sidecar.panel_boxes, "subfigure_panel")}
    for panel_id in ("subfigure_panel_A", "subfigure_panel_B"):
        if panel_id in panel_boxes:
            continue
        issues.append(
            _issue(
                rule_id="missing_subfigure_panel",
                message="source-layer accounting requires both Panel A and Panel B containers",
                target="panel_boxes",
                expected=panel_id,
            )
        )

    source_boxes = _boxes_of_type(sidecar.layout_boxes, "source_layer_box")
    coverage_box_type = "coverage_step" if is_v2_layout else "coverage_bar"
    coverage_bars = _boxes_of_type(sidecar.layout_boxes, coverage_box_type)
    coverage_labels = _boxes_of_type(sidecar.layout_boxes, "coverage_label")
    coverage_values = _boxes_of_type(sidecar.layout_boxes, "coverage_value")
    main_steps = _boxes_of_type(sidecar.layout_boxes, "main_step")
    issues.extend(_check_pairwise_non_overlap(source_boxes, rule_id="source_layer_box_overlap", target="source_layer_box"))
    issues.extend(_check_pairwise_non_overlap(coverage_bars, rule_id="coverage_bar_overlap", target="coverage_bar"))
    issues.extend(_check_pairwise_non_overlap(coverage_labels, rule_id="coverage_label_overlap", target="coverage_label"))
    issues.extend(_check_pairwise_non_overlap(coverage_values, rule_id="coverage_value_overlap", target="coverage_value"))

    if not is_v2_layout:
        panel_a = panel_boxes.get("subfigure_panel_A")
        if panel_a is not None:
            for box in main_steps + source_boxes:
                if _box_within_box(box, panel_a):
                    continue
                issues.append(
                    _issue(
                        rule_id="source_layer_content_out_of_panel_a",
                        message="denominator and source-layer boxes must stay within Panel A",
                        target=box.box_type,
                        box_refs=(box.box_id, panel_a.box_id),
                    )
                )
        panel_b = panel_boxes.get("subfigure_panel_B")
        if panel_b is not None:
            for box in coverage_bars + coverage_labels + coverage_values:
                if _box_within_box(box, panel_b):
                    continue
                issues.append(
                    _issue(
                        rule_id="coverage_content_out_of_panel_b",
                        message="subcohort coverage marks must stay within Panel B",
                        target=box.box_type,
                        box_refs=(box.box_id, panel_b.box_id),
                    )
                )

    source_layers = [
        item
        for item in sidecar.metrics.get("source_layers", [])
        if isinstance(item, dict) and str(item.get("layer_id") or "").strip()
    ]
    if not source_layers:
        issues.append(
            _issue(
                rule_id="source_layers_missing",
                message="source-layer accounting sidecar requires metrics.source_layers",
                target="metrics.source_layers",
            )
        )
    for layer in source_layers:
        layer_id = str(layer.get("layer_id") or "").strip()
        expected_box_id = f"source_layer_{layer_id}"
        if not any(box.box_id == expected_box_id for box in source_boxes):
            issues.append(
                _issue(
                    rule_id="missing_source_layer_box",
                    message="each metrics.source_layers item must have a rendered source-layer box",
                    target="layout_boxes",
                    expected=expected_box_id,
                )
            )

    coverage_items = [
        item
        for item in sidecar.metrics.get("subcohort_coverage", [])
        if isinstance(item, dict) and str(item.get("coverage_id") or "").strip()
    ]
    if not coverage_items:
        issues.append(
            _issue(
                rule_id="subcohort_coverage_missing",
                message="source-layer accounting sidecar requires metrics.subcohort_coverage",
                target="metrics.subcohort_coverage",
            )
        )
    for item in coverage_items:
        coverage_id = str(item.get("coverage_id") or "").strip()
        expected_box_id = f"coverage_bar_{coverage_id}"
        if not any(box.box_id == expected_box_id for box in coverage_bars):
            issues.append(
                _issue(
                    rule_id=f"missing_{coverage_box_type}",
                    message=f"each metrics.subcohort_coverage item must have a rendered {coverage_box_type}",
                    target="layout_boxes",
                    expected=expected_box_id,
                )
            )

    flow_nodes = sidecar.metrics.get("flow_nodes")
    if not isinstance(flow_nodes, list) or not flow_nodes:
        issues.append(
            _issue(
                rule_id="flow_nodes_missing",
                message="source-layer accounting qc requires flow_nodes metrics for readability checks",
                target="metrics.flow_nodes",
            )
        )
        return issues
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
        padding_pt = _require_numeric(
            item.get("padding_pt"),
            label=f"layout_sidecar.metrics.flow_nodes[{index}].padding_pt",
        )
        minimum_height_pt = 70.0 if box_type in {"main_step", "source_layer_box"} else 48.0
        minimum_width_pt = 160.0 if box_type != "coverage_bar" else 120.0
        minimum_padding_pt = 8.0 if box_type in {"main_step", "source_layer_box"} else 6.0
        if rendered_height_pt < minimum_height_pt:
            issues.append(
                _issue(
                    rule_id="flow_node_height_too_small",
                    message="source-layer accounting node height is too small for readability",
                    target=f"metrics.flow_nodes[{index}]",
                    observed={"rendered_height_pt": rendered_height_pt, "box_type": box_type},
                    expected={"minimum_height_pt": minimum_height_pt},
                )
            )
        if rendered_width_pt < minimum_width_pt:
            issues.append(
                _issue(
                    rule_id="flow_node_width_too_small",
                    message="source-layer accounting node width is too small for readability",
                    target=f"metrics.flow_nodes[{index}]",
                    observed={"rendered_width_pt": rendered_width_pt, "box_type": box_type},
                    expected={"minimum_width_pt": minimum_width_pt},
                )
            )
        if padding_pt < minimum_padding_pt:
            issues.append(
                _issue(
                    rule_id="flow_node_padding_too_small",
                    message="source-layer accounting node padding is too small for readability",
                    target=f"metrics.flow_nodes[{index}]",
                    observed={"padding_pt": padding_pt, "box_type": box_type},
                    expected={"minimum_padding_pt": minimum_padding_pt},
                )
            )
    return issues


def _check_participant_reporting_flow(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    is_v2_layout = (
        str(sidecar.metrics.get("layout_generation") or "").strip() == "scholarskills_cohort_flow_v2"
        and str(sidecar.metrics.get("flow_visual_policy") or "").strip()
        == "purpose_first_reporting_flow_no_legacy_card_shell"
    )
    flow_nodes = sidecar.metrics.get("flow_nodes")
    if not isinstance(flow_nodes, list) or not flow_nodes:
        issues.append(
            _issue(
                rule_id="flow_nodes_missing",
                message="participant flow qc requires flow_nodes metrics for readability checks",
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
            is_context_note = box_type in {"context_note", "design_context_note"}
            minimum_height_pt = 70.0 if box_type == "main_step" else 52.0
            minimum_padding_pt = 8.0 if box_type == "main_step" else 6.0
            minimum_width_pt = 380.0 if is_v2_layout and box_type == "main_step" else 160.0
            if is_v2_layout and is_context_note:
                issues.append(
                    _issue(
                        rule_id="participant_flow_context_card_shell",
                        message=(
                            "ScholarSkills cohort-flow v2 participant layouts must keep explanatory context "
                            "in captions or legends instead of rendering large prose cards inside Figure 1"
                        ),
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"box_id": item.get("box_id"), "box_type": box_type},
                        expected={"allowed_box_types": ["main_step", "exclusion_box"]},
                    )
                )
            if rendered_height_pt < minimum_height_pt:
                issues.append(
                    _issue(
                        rule_id="flow_node_height_too_small",
                        message="participant flow node height is too small for manuscript-facing readability",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"rendered_height_pt": rendered_height_pt, "box_type": box_type},
                        expected={"minimum_height_pt": minimum_height_pt},
                    )
                )
            if rendered_width_pt < minimum_width_pt:
                issues.append(
                    _issue(
                        rule_id="flow_node_width_too_small",
                        message="participant flow node width is too small for manuscript-facing readability",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"rendered_width_pt": rendered_width_pt, "box_type": box_type},
                        expected={"minimum_width_pt": minimum_width_pt},
                    )
                )
            if padding_pt < minimum_padding_pt:
                issues.append(
                    _issue(
                        rule_id="flow_node_padding_too_small",
                        message="participant flow node padding is too small for manuscript-facing readability",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"padding_pt": padding_pt, "box_type": box_type},
                        expected={"minimum_padding_pt": minimum_padding_pt},
                    )
                )
            maximum_max_line_chars = 82.0 if is_v2_layout and is_context_note else 48.0
            if line_count > 0 and max_line_chars > maximum_max_line_chars:
                issues.append(
                    _issue(
                        rule_id="flow_node_text_density_high",
                        message="participant flow node line length is too dense",
                        target=f"metrics.flow_nodes[{index}]",
                        observed={"line_count": line_count, "max_line_chars": max_line_chars},
                        expected={"maximum_max_line_chars": maximum_max_line_chars},
                    )
                )

    step_boxes = _boxes_of_type(sidecar.layout_boxes, "main_step")
    exclusion_boxes = _boxes_of_type(sidecar.layout_boxes, "exclusion_box")
    summary_boxes = _boxes_of_type(sidecar.layout_boxes, "summary_panel")
    context_note_boxes = _boxes_of_type(sidecar.layout_boxes, "context_note") + _boxes_of_type(
        sidecar.layout_boxes, "design_context_note"
    )
    issues.extend(_check_pairwise_non_overlap(step_boxes, rule_id="main_step_overlap", target="main_step"))
    issues.extend(_check_pairwise_non_overlap(exclusion_boxes, rule_id="exclusion_box_overlap", target="exclusion_box"))
    issues.extend(_check_pairwise_non_overlap(summary_boxes, rule_id="summary_panel_overlap", target="summary_panel"))
    if is_v2_layout and summary_boxes:
        issues.append(
            _issue(
                rule_id="participant_flow_legacy_summary_panel_shell",
                message=(
                    "ScholarSkills cohort-flow v2 participant layouts must not use legacy right-side "
                    "summary_panel cards; use a full-width flow with a lightweight context note instead"
                ),
                target="layout_boxes",
                observed={"summary_panel_box_ids": [box.box_id for box in summary_boxes]},
                expected={"allowed_context_box_types": ["context_note", "design_context_note"]},
                box_refs=tuple(box.box_id for box in summary_boxes),
            )
        )
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
    for summary_box in summary_boxes:
        for step_box in step_boxes:
            if not _boxes_overlap(summary_box, step_box):
                continue
            issues.append(
                _issue(
                    rule_id="summary_step_overlap",
                    message="summary panel must not overlap the participant flow stack",
                    target="summary_panel",
                    box_refs=(summary_box.box_id, step_box.box_id),
                )
            )

    participant_panels = {
        box.box_id: box for box in _boxes_of_type(sidecar.panel_boxes, "subfigure_panel")
    }
    participant_panel = participant_panels.get("participant_flow_main")
    if participant_panel is None:
        issues.append(
            _issue(
                rule_id="missing_participant_flow_panel",
                message="participant flow requires one main panel container around flow nodes",
                target="panel_boxes",
                expected="participant_flow_main",
            )
        )
    else:
        for box in step_boxes + exclusion_boxes:
            if _box_within_box(box, participant_panel):
                continue
            issues.append(
                _issue(
                    rule_id="participant_flow_content_out_of_panel",
                    message="participant flow content must stay within the main flow panel",
                    target=box.box_type,
                    box_refs=(box.box_id, participant_panel.box_id),
                )
            )
        if step_boxes and (is_v2_layout or (not summary_boxes and not exclusion_boxes)):
            content_x0 = min(box.x0 for box in step_boxes)
            content_x1 = max(box.x1 for box in step_boxes)
            panel_width = max(0.0, participant_panel.x1 - participant_panel.x0)
            content_width = max(0.0, content_x1 - content_x0)
            coverage = content_width / panel_width if panel_width > 0 else 0.0
            content_center = (content_x0 + content_x1) / 2.0
            panel_center = (participant_panel.x0 + participant_panel.x1) / 2.0
            center_offset = abs(content_center - panel_center) / panel_width if panel_width > 0 else 1.0
            minimum_coverage = 0.66 if is_v2_layout else 0.60
            maximum_center_offset = 0.10 if is_v2_layout else 0.12
            if coverage < minimum_coverage or center_offset > maximum_center_offset:
                issues.append(
                    _issue(
                        rule_id="participant_flow_content_horizontally_compressed",
                        message=(
                            "participant flow must use and center the main flow panel rather than compressing "
                            "the cohort accounting into a narrow side lane"
                        ),
                        target="main_step",
                        observed={
                            "content_width_fraction": round(coverage, 3),
                            "center_offset_fraction": round(center_offset, 3),
                        },
                        expected={
                            "minimum_content_width_fraction": minimum_coverage,
                            "maximum_center_offset_fraction": maximum_center_offset,
                        },
                        box_refs=tuple(box.box_id for box in step_boxes),
                    )
                )
        if is_v2_layout and context_note_boxes:
            for note_box in context_note_boxes:
                issues.append(
                    _issue(
                        rule_id="participant_flow_context_card_shell",
                        message=(
                            "ScholarSkills cohort-flow v2 participant layouts must not render prose context "
                            "cards; keep study-frame and endpoint explanation in captions or legends"
                        ),
                        target=note_box.box_type,
                        observed={"box_id": note_box.box_id, "width_fraction": round(note_box.x1 - note_box.x0, 3)},
                        expected={"allowed_box_types": ["main_step", "exclusion_box"]},
                        box_refs=(note_box.box_id,),
                    )
                )

    flow_connectors = {box.box_id: box for box in _boxes_of_type(sidecar.guide_boxes, "flow_connector")}
    flow_branch_connectors = {box.box_id: box for box in _boxes_of_type(sidecar.guide_boxes, "flow_branch_connector")}
    expected_step_ids = [
        str(item.get("step_id") or "").strip()
        for item in sidecar.metrics.get("steps", [])
        if isinstance(item, dict)
    ]
    expected_step_ids = [item for item in expected_step_ids if item]
    if not expected_step_ids:
        sorted_step_boxes = sorted(step_boxes, key=lambda box: (-((box.y0 + box.y1) / 2.0), box.x0, box.box_id))
        expected_step_ids = [
            box.box_id.removeprefix("participant_step_").removeprefix("step_")
            for box in sorted_step_boxes
        ]
    expected_exclusions = [
        str(item.get("exclusion_id") or "").strip()
        for item in sidecar.metrics.get("exclusions", [])
        if isinstance(item, dict) and str(item.get("exclusion_id") or "").strip()
    ]
    if not expected_exclusions:
        expected_exclusions = [
            box.box_id.removeprefix("participant_exclusion_").removeprefix("exclusion_")
            for box in exclusion_boxes
        ]

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
                message="participant flow requires explicit spine and exclusion branch connectors",
                target="guide_boxes",
                expected=missing_flow_connectors,
            )
        )

    return issues
