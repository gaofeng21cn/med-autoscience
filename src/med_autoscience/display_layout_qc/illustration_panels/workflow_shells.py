from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_of_type,
    _check_boxes_within_device,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _issue,
)

def _check_publication_workflow_fact_sheet_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=("panel", "panel_label", "section_title", "fact_label", "fact_value"),
        )
    )

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 4:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="workflow fact sheet requires exactly four panel boxes",
                target="panel_boxes",
                expected={"count": 4},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"panel_label", "section_title", "fact_label", "fact_value"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    sections = sidecar.metrics.get("sections")
    if not isinstance(sections, list) or not sections:
        issues.append(
            _issue(
                rule_id="sections_missing",
                message="workflow fact sheet qc requires non-empty section metrics",
                target="metrics.sections",
            )
        )
        return issues

    if len(sections) != 4:
        issues.append(
            _issue(
                rule_id="section_count_mismatch",
                message="workflow fact sheet requires exactly four declared sections",
                target="metrics.sections",
                expected={"count": 4},
                observed={"count": len(sections)},
            )
        )

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    expected_layout_roles = {"top_left", "top_right", "bottom_left", "bottom_right"}
    seen_section_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_layout_roles: set[str] = set()

    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            raise ValueError(f"layout_sidecar.metrics.sections[{section_index}] must be an object")
        section_target = f"metrics.sections[{section_index}]"
        section_id = str(section.get("section_id") or "").strip()
        panel_label = str(section.get("panel_label") or "").strip()
        layout_role = str(section.get("layout_role") or "").strip()
        panel_box_id = str(section.get("panel_box_id") or "").strip()
        title_box_id = str(section.get("title_box_id") or "").strip()
        panel_label_box_id = str(section.get("panel_label_box_id") or "").strip()

        if not section_id:
            issues.append(
                _issue(
                    rule_id="section_id_missing",
                    message="workflow fact sheet sections require non-empty section_id",
                    target=f"{section_target}.section_id",
                )
            )
        elif section_id in seen_section_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_section_id",
                    message="workflow fact sheet section_id values must be unique",
                    target="metrics.sections",
                    observed=section_id,
                )
            )
        else:
            seen_section_ids.add(section_id)

        if not panel_label:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="workflow fact sheet sections require non-empty panel_label metrics",
                    target=f"{section_target}.panel_label",
                )
            )
        elif panel_label in seen_panel_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_panel_label",
                    message="workflow fact sheet panel labels must be unique",
                    target="metrics.sections",
                    observed=panel_label,
                )
            )
        else:
            seen_panel_labels.add(panel_label)

        if not layout_role:
            issues.append(
                _issue(
                    rule_id="layout_role_missing",
                    message="workflow fact sheet sections require non-empty layout_role",
                    target=f"{section_target}.layout_role",
                )
            )
        elif layout_role not in expected_layout_roles:
            issues.append(
                _issue(
                    rule_id="section_layout_role_invalid",
                    message="workflow fact sheet layout_role must match the fixed four-panel grid",
                    target=f"{section_target}.layout_role",
                    observed=layout_role,
                    expected=sorted(expected_layout_roles),
                )
            )
        elif layout_role in seen_layout_roles:
            issues.append(
                _issue(
                    rule_id="duplicate_layout_role",
                    message="workflow fact sheet layout_role values must be unique",
                    target="metrics.sections",
                    observed=layout_role,
                )
            )
        else:
            seen_layout_roles.add(layout_role)

        parent_panel = panel_boxes_by_id.get(panel_box_id)
        if parent_panel is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="workflow fact sheet sections must reference an existing panel box",
                    target=f"{section_target}.panel_box_id",
                    expected=panel_box_id,
                )
            )

        title_box = layout_boxes_by_id.get(title_box_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="section_title_missing",
                    message="workflow fact sheet sections must reference an existing section_title box",
                    target=f"{section_target}.title_box_id",
                    expected=title_box_id,
                )
            )
        elif parent_panel is not None and not _box_within_box(title_box, parent_panel):
            issues.append(
                _issue(
                    rule_id="section_title_out_of_panel",
                    message="workflow fact sheet section titles must stay within the parent panel",
                    target="section_title",
                    box_refs=(title_box.box_id, parent_panel.box_id),
                )
            )

        label_box = layout_boxes_by_id.get(panel_label_box_id)
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="workflow fact sheet sections must reference an existing panel label box",
                    target=f"{section_target}.panel_label_box_id",
                    expected=panel_label_box_id,
                )
            )
        elif parent_panel is not None:
            panel_width = max(parent_panel.x1 - parent_panel.x0, 1e-9)
            panel_height = max(parent_panel.y1 - parent_panel.y0, 1e-9)
            if not _box_within_box(label_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="panel_label_out_of_panel",
                        message="workflow fact sheet panel labels must stay within the parent panel",
                        target="panel_label",
                        box_refs=(label_box.box_id, parent_panel.box_id),
                    )
                )
            else:
                anchored_near_left = label_box.x0 <= parent_panel.x0 + panel_width * 0.10
                anchored_near_top = (
                    label_box.y0 <= parent_panel.y0 + panel_height * 0.12
                    or label_box.y1 >= parent_panel.y1 - panel_height * 0.10
                )
                if anchored_near_left and anchored_near_top:
                    pass
                else:
                    issues.append(
                        _issue(
                            rule_id="panel_label_anchor_drift",
                            message="workflow fact sheet panel labels must stay near the parent panel top-left anchor",
                            target="panel_label",
                            box_refs=(label_box.box_id, parent_panel.box_id),
                        )
                    )

        facts = section.get("facts")
        if not isinstance(facts, list) or not facts:
            issues.append(
                _issue(
                    rule_id="facts_missing",
                    message="workflow fact sheet sections require a non-empty facts list",
                    target=f"{section_target}.facts",
                )
            )
            continue

        seen_fact_ids: set[str] = set()
        for fact_index, fact in enumerate(facts):
            if not isinstance(fact, dict):
                raise ValueError(f"{section_target}.facts[{fact_index}] must be an object")
            fact_target = f"{section_target}.facts[{fact_index}]"
            fact_id = str(fact.get("fact_id") or "").strip()
            if not fact_id:
                issues.append(
                    _issue(
                        rule_id="fact_id_missing",
                        message="workflow fact sheet facts require non-empty fact_id",
                        target=f"{fact_target}.fact_id",
                    )
                )
            elif fact_id in seen_fact_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_fact_id",
                        message="workflow fact sheet fact_id values must be unique within each section",
                        target=f"{section_target}.facts",
                        observed=fact_id,
                    )
                )
            else:
                seen_fact_ids.add(fact_id)

            label_box_id = str(fact.get("label_box_id") or "").strip()
            value_box_id = str(fact.get("value_box_id") or "").strip()
            fact_label_box = layout_boxes_by_id.get(label_box_id)
            fact_value_box = layout_boxes_by_id.get(value_box_id)

            if fact_label_box is None:
                issues.append(
                    _issue(
                        rule_id="fact_label_missing",
                        message="workflow fact sheet facts must reference an existing fact label box",
                        target=f"{fact_target}.label_box_id",
                        expected=label_box_id,
                    )
                )
            elif parent_panel is not None and not _box_within_box(fact_label_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="fact_box_out_of_panel",
                        message="workflow fact sheet fact labels must stay within the parent panel",
                        target="fact_label",
                        box_refs=(fact_label_box.box_id, parent_panel.box_id),
                    )
                )

            if fact_value_box is None:
                issues.append(
                    _issue(
                        rule_id="fact_value_missing",
                        message="workflow fact sheet facts must reference an existing fact value box",
                        target=f"{fact_target}.value_box_id",
                        expected=value_box_id,
                    )
                )
            elif parent_panel is not None and not _box_within_box(fact_value_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="fact_box_out_of_panel",
                        message="workflow fact sheet fact values must stay within the parent panel",
                        target="fact_value",
                        box_refs=(fact_value_box.box_id, parent_panel.box_id),
                    )
                )

    if seen_layout_roles and seen_layout_roles != expected_layout_roles:
        issues.append(
            _issue(
                rule_id="section_layout_roles_incomplete",
                message="workflow fact sheet must cover the complete fixed four-panel grid",
                target="metrics.sections",
                observed=sorted(seen_layout_roles),
                expected=sorted(expected_layout_roles),
            )
        )

    return issues
def _check_publication_design_evidence_composite_shell(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=("workflow_stage", "stage_title", "panel", "panel_label", "summary_title", "card_label", "card_value"),
        )
    )

    workflow_stage_boxes = _boxes_of_type(sidecar.panel_boxes, "workflow_stage")
    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(workflow_stage_boxes) not in {3, 4}:
        issues.append(
            _issue(
                rule_id="workflow_stage_count_mismatch",
                message="design evidence composite requires three or four workflow stage boxes",
                target="panel_boxes",
                expected={"count": [3, 4]},
                observed={"count": len(workflow_stage_boxes)},
            )
        )
    if len(panel_boxes) != 3:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="design evidence composite requires exactly three summary panels",
                target="panel_boxes",
                expected={"count": 3},
                observed={"count": len(panel_boxes)},
            )
        )

    issues.extend(_check_pairwise_non_overlap(workflow_stage_boxes, rule_id="workflow_stage_overlap", target="workflow_stage"))
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))

    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"stage_title", "stage_detail", "panel_label", "summary_title", "card_label", "card_value"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    workflow_stage_boxes_by_id = {box.box_id: box for box in workflow_stage_boxes}
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}

    workflow_stages = sidecar.metrics.get("workflow_stages")
    if not isinstance(workflow_stages, list) or not workflow_stages:
        issues.append(
            _issue(
                rule_id="workflow_stages_missing",
                message="design evidence composite qc requires non-empty workflow stage metrics",
                target="metrics.workflow_stages",
            )
        )
    else:
        if len(workflow_stages) not in {3, 4}:
            issues.append(
                _issue(
                    rule_id="workflow_stage_metrics_count_mismatch",
                    message="design evidence composite requires three or four declared workflow stages",
                    target="metrics.workflow_stages",
                    expected={"count": [3, 4]},
                    observed={"count": len(workflow_stages)},
                )
            )
        seen_stage_ids: set[str] = set()
        for stage_index, stage in enumerate(workflow_stages):
            if not isinstance(stage, dict):
                raise ValueError(f"layout_sidecar.metrics.workflow_stages[{stage_index}] must be an object")
            stage_target = f"metrics.workflow_stages[{stage_index}]"
            stage_id = str(stage.get("stage_id") or "").strip()
            stage_box_id = str(stage.get("stage_box_id") or "").strip()
            title_box_id = str(stage.get("title_box_id") or "").strip()
            detail_box_id = str(stage.get("detail_box_id") or "").strip()

            if not stage_id:
                issues.append(
                    _issue(
                        rule_id="workflow_stage_id_missing",
                        message="design evidence composite workflow stages require non-empty stage_id",
                        target=f"{stage_target}.stage_id",
                    )
                )
            elif stage_id in seen_stage_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_workflow_stage_id",
                        message="design evidence composite workflow stage ids must be unique",
                        target="metrics.workflow_stages",
                        observed=stage_id,
                    )
                )
            else:
                seen_stage_ids.add(stage_id)

            stage_box = workflow_stage_boxes_by_id.get(stage_box_id)
            if stage_box is None:
                issues.append(
                    _issue(
                        rule_id="workflow_stage_box_missing",
                        message="design evidence composite workflow stages must reference an existing workflow_stage box",
                        target=f"{stage_target}.stage_box_id",
                        expected=stage_box_id,
                    )
                )

            title_box = layout_boxes_by_id.get(title_box_id)
            if title_box is None:
                issues.append(
                    _issue(
                        rule_id="workflow_stage_title_missing",
                        message="design evidence composite workflow stages must reference an existing stage_title box",
                        target=f"{stage_target}.title_box_id",
                        expected=title_box_id,
                    )
                )
            elif stage_box is not None and not _box_within_box(title_box, stage_box):
                issues.append(
                    _issue(
                        rule_id="workflow_stage_title_out_of_stage",
                        message="design evidence composite workflow stage titles must stay within the parent stage box",
                        target="stage_title",
                        box_refs=(title_box.box_id, stage_box.box_id),
                    )
                )

            if detail_box_id:
                detail_box = layout_boxes_by_id.get(detail_box_id)
                if detail_box is None:
                    issues.append(
                        _issue(
                            rule_id="workflow_stage_detail_missing",
                            message="design evidence composite workflow stages must reference an existing stage_detail box when declared",
                            target=f"{stage_target}.detail_box_id",
                            expected=detail_box_id,
                        )
                    )
                elif stage_box is not None and not _box_within_box(detail_box, stage_box):
                    issues.append(
                        _issue(
                            rule_id="workflow_stage_detail_out_of_stage",
                            message="design evidence composite workflow stage detail must stay within the parent stage box",
                            target="stage_detail",
                            box_refs=(detail_box.box_id, stage_box.box_id),
                        )
                    )

    summary_panels = sidecar.metrics.get("summary_panels")
    if not isinstance(summary_panels, list) or not summary_panels:
        issues.append(
            _issue(
                rule_id="summary_panels_missing",
                message="design evidence composite qc requires non-empty summary panel metrics",
                target="metrics.summary_panels",
            )
        )
        return issues

    if len(summary_panels) != 3:
        issues.append(
            _issue(
                rule_id="summary_panel_count_mismatch",
                message="design evidence composite requires exactly three declared summary panels",
                target="metrics.summary_panels",
                expected={"count": 3},
                observed={"count": len(summary_panels)},
            )
        )

    expected_layout_roles = {"left", "center", "right"}
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_layout_roles: set[str] = set()
    for panel_index, panel in enumerate(summary_panels):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.summary_panels[{panel_index}] must be an object")
        panel_target = f"metrics.summary_panels[{panel_index}]"
        panel_id = str(panel.get("panel_id") or "").strip()
        panel_label = str(panel.get("panel_label") or "").strip()
        layout_role = str(panel.get("layout_role") or "").strip()
        panel_box_id = str(panel.get("panel_box_id") or "").strip()
        panel_label_box_id = str(panel.get("panel_label_box_id") or "").strip()
        title_box_id = str(panel.get("title_box_id") or "").strip()

        if not panel_id:
            issues.append(
                _issue(
                    rule_id="summary_panel_id_missing",
                    message="design evidence composite summary panels require non-empty panel_id",
                    target=f"{panel_target}.panel_id",
                )
            )
        elif panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_summary_panel_id",
                    message="design evidence composite summary panel ids must be unique",
                    target="metrics.summary_panels",
                    observed=panel_id,
                )
            )
        else:
            seen_panel_ids.add(panel_id)

        if not panel_label:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="design evidence composite summary panels require non-empty panel_label metrics",
                    target=f"{panel_target}.panel_label",
                )
            )
        elif panel_label in seen_panel_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_panel_label",
                    message="design evidence composite panel labels must be unique",
                    target="metrics.summary_panels",
                    observed=panel_label,
                )
            )
        else:
            seen_panel_labels.add(panel_label)

        if not layout_role:
            issues.append(
                _issue(
                    rule_id="layout_role_missing",
                    message="design evidence composite summary panels require non-empty layout_role",
                    target=f"{panel_target}.layout_role",
                )
            )
        elif layout_role not in expected_layout_roles:
            issues.append(
                _issue(
                    rule_id="summary_panel_layout_role_invalid",
                    message="design evidence composite layout_role must match the fixed three-panel composite",
                    target=f"{panel_target}.layout_role",
                    observed=layout_role,
                    expected=sorted(expected_layout_roles),
                )
            )
        elif layout_role in seen_layout_roles:
            issues.append(
                _issue(
                    rule_id="duplicate_layout_role",
                    message="design evidence composite layout_role values must be unique",
                    target="metrics.summary_panels",
                    observed=layout_role,
                )
            )
        else:
            seen_layout_roles.add(layout_role)

        parent_panel = panel_boxes_by_id.get(panel_box_id)
        if parent_panel is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="design evidence composite summary panels must reference an existing panel box",
                    target=f"{panel_target}.panel_box_id",
                    expected=panel_box_id,
                )
            )

        title_box = layout_boxes_by_id.get(title_box_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="summary_title_missing",
                    message="design evidence composite summary panels must reference an existing summary_title box",
                    target=f"{panel_target}.title_box_id",
                    expected=title_box_id,
                )
            )
        elif parent_panel is not None and not _box_within_box(title_box, parent_panel):
            issues.append(
                _issue(
                    rule_id="summary_title_out_of_panel",
                    message="design evidence composite summary titles must stay within the parent panel",
                    target="summary_title",
                    box_refs=(title_box.box_id, parent_panel.box_id),
                )
            )

        label_box = layout_boxes_by_id.get(panel_label_box_id)
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="design evidence composite summary panels must reference an existing panel label box",
                    target=f"{panel_target}.panel_label_box_id",
                    expected=panel_label_box_id,
                )
            )
        elif parent_panel is not None:
            panel_width = max(parent_panel.x1 - parent_panel.x0, 1e-9)
            panel_height = max(parent_panel.y1 - parent_panel.y0, 1e-9)
            if not _box_within_box(label_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="panel_label_out_of_panel",
                        message="design evidence composite panel labels must stay within the parent panel",
                        target="panel_label",
                        box_refs=(label_box.box_id, parent_panel.box_id),
                    )
                )
            else:
                anchored_near_left = label_box.x0 <= parent_panel.x0 + panel_width * 0.10
                anchored_near_top = (
                    label_box.y0 <= parent_panel.y0 + panel_height * 0.12
                    or label_box.y1 >= parent_panel.y1 - panel_height * 0.10
                )
                if not (anchored_near_left and anchored_near_top):
                    issues.append(
                        _issue(
                            rule_id="panel_label_anchor_drift",
                            message="design evidence composite panel labels must stay near the parent panel top-left anchor",
                            target="panel_label",
                            box_refs=(label_box.box_id, parent_panel.box_id),
                        )
                    )

        cards = panel.get("cards")
        if not isinstance(cards, list) or not cards:
            issues.append(
                _issue(
                    rule_id="cards_missing",
                    message="design evidence composite summary panels require a non-empty cards list",
                    target=f"{panel_target}.cards",
                )
            )
            continue

        seen_card_ids: set[str] = set()
        for card_index, card in enumerate(cards):
            if not isinstance(card, dict):
                raise ValueError(f"{panel_target}.cards[{card_index}] must be an object")
            card_target = f"{panel_target}.cards[{card_index}]"
            card_id = str(card.get("card_id") or "").strip()
            if not card_id:
                issues.append(
                    _issue(
                        rule_id="card_id_missing",
                        message="design evidence composite cards require non-empty card_id",
                        target=f"{card_target}.card_id",
                    )
                )
            elif card_id in seen_card_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_card_id",
                        message="design evidence composite card ids must be unique within each summary panel",
                        target=f"{panel_target}.cards",
                        observed=card_id,
                    )
                )
            else:
                seen_card_ids.add(card_id)

            label_box_id = str(card.get("label_box_id") or "").strip()
            value_box_id = str(card.get("value_box_id") or "").strip()
            label_box = layout_boxes_by_id.get(label_box_id)
            value_box = layout_boxes_by_id.get(value_box_id)
            if label_box is None:
                issues.append(
                    _issue(
                        rule_id="card_label_missing",
                        message="design evidence composite cards must reference an existing card label box",
                        target=f"{card_target}.label_box_id",
                        expected=label_box_id,
                    )
                )
            elif parent_panel is not None and not _box_within_box(label_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="card_box_out_of_panel",
                        message="design evidence composite card labels must stay within the parent panel",
                        target="card_label",
                        box_refs=(label_box.box_id, parent_panel.box_id),
                    )
                )
            if value_box is None:
                issues.append(
                    _issue(
                        rule_id="card_value_missing",
                        message="design evidence composite cards must reference an existing card value box",
                        target=f"{card_target}.value_box_id",
                        expected=value_box_id,
                    )
                )
            elif parent_panel is not None and not _box_within_box(value_box, parent_panel):
                issues.append(
                    _issue(
                        rule_id="card_box_out_of_panel",
                        message="design evidence composite card values must stay within the parent panel",
                        target="card_value",
                        box_refs=(value_box.box_id, parent_panel.box_id),
                    )
                )

    if seen_layout_roles and seen_layout_roles != expected_layout_roles:
        issues.append(
            _issue(
                rule_id="summary_panel_layout_roles_incomplete",
                message="design evidence composite must cover the complete fixed three-panel layout",
                target="metrics.summary_panels",
                observed=sorted(seen_layout_roles),
                expected=sorted(expected_layout_roles),
            )
        )

    return issues
