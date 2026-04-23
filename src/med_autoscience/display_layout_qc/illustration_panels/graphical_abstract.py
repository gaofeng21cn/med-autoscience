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
    _issue,
)

def _check_submission_graphical_abstract(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("title", "panel_label", "card_box", "footer_pill")))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    if len(panel_boxes) < 3:
        issues.append(
            _issue(
                rule_id="graphical_abstract_panels_missing",
                message="submission graphical abstract requires three panels",
                target="panel_boxes",
                expected={"minimum_count": 3},
                observed={"count": len(panel_boxes)},
            )
        )

    card_boxes = _boxes_of_type(sidecar.layout_boxes, "card_box")
    footer_pills = _boxes_of_type(sidecar.layout_boxes, "footer_pill")
    panel_labels = _boxes_of_type(sidecar.layout_boxes, "panel_label")
    arrow_boxes = _boxes_of_type(sidecar.guide_boxes, "arrow_connector")
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"panel_title", "panel_subtitle", "card_title", "card_value", "card_detail"}
    )

    issues.extend(_check_pairwise_non_overlap(card_boxes, rule_id="graphical_abstract_card_overlap", target="card_box"))
    issues.extend(_check_pairwise_non_overlap(footer_pills, rule_id="graphical_abstract_footer_overlap", target="footer_pill"))
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="graphical_abstract_text_overlap", target="text"))

    for card_box in card_boxes:
        if any(_box_within_box(card_box, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="card_out_of_panel",
                message="graphical-abstract cards must stay within a panel",
                target="card_box",
                box_refs=(card_box.box_id,),
            )
        )
    for panel_label in panel_labels:
        if any(_box_within_box(panel_label, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="panel_label_out_of_panel",
                message="graphical-abstract panel labels must stay within their panels",
                target="panel_label",
                box_refs=(panel_label.box_id,),
            )
        )
    for text_box in text_boxes:
        if any(_box_within_box(text_box, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="panel_text_out_of_panel",
                message="graphical-abstract panel text must stay within a panel",
                target=text_box.box_type,
                box_refs=(text_box.box_id,),
            )
        )
    for footer_pill in footer_pills:
        for panel_box in panel_boxes:
            if not _boxes_overlap(footer_pill, panel_box):
                continue
            issues.append(
                _issue(
                    rule_id="footer_pill_panel_overlap",
                    message="graphical-abstract footer pills must stay outside the panels",
                    target="footer_pill",
                    box_refs=(footer_pill.box_id, panel_box.box_id),
                )
            )
        for arrow_box in arrow_boxes:
            if not _boxes_overlap(footer_pill, arrow_box):
                continue
            issues.append(
                _issue(
                    rule_id="footer_pill_arrow_overlap",
                    message="graphical-abstract footer pills must not overlap arrow connectors",
                    target="footer_pill",
                    box_refs=(footer_pill.box_id, arrow_box.box_id),
                )
            )
    for arrow_box in arrow_boxes:
        for panel_box in panel_boxes:
            if _boxes_overlap(arrow_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="arrow_panel_overlap",
                        message="graphical-abstract arrows must stay between panels",
                        target="arrow_connector",
                        box_refs=(arrow_box.box_id, panel_box.box_id),
                    )
                )
        for text_box in text_boxes:
            if not _boxes_overlap(arrow_box, text_box):
                continue
            issues.append(
                _issue(
                    rule_id="arrow_text_overlap",
                    message="graphical-abstract arrows must not overlap panel text",
                    target="arrow_connector",
                    box_refs=(arrow_box.box_id, text_box.box_id),
                )
            )
    sorted_panels = tuple(sorted(panel_boxes, key=lambda box: (box.x0, box.y0, box.box_id)))
    sorted_arrows = tuple(sorted(arrow_boxes, key=lambda box: (box.x0, box.y0, box.box_id)))
    if len(sorted_arrows) >= 2:
        arrow_mid_ys = [((arrow_box.y0 + arrow_box.y1) / 2.0) for arrow_box in sorted_arrows]
        arrow_heights = [(arrow_box.y1 - arrow_box.y0) for arrow_box in sorted_arrows]
        alignment_tolerance = max(max(arrow_heights, default=0.0) * 1.5, 0.03)
        if max(arrow_mid_ys) - min(arrow_mid_ys) > alignment_tolerance:
            issues.append(
                _issue(
                    rule_id="arrow_cross_pair_misalignment",
                    message="graphical-abstract arrows between adjacent panels must share the same horizontal lane",
                    target="arrow_connector",
                    box_refs=tuple(arrow_box.box_id for arrow_box in sorted_arrows),
                )
            )
    for arrow_box in sorted_arrows:
        arrow_mid_x = (arrow_box.x0 + arrow_box.x1) / 2.0
        arrow_mid_y = (arrow_box.y0 + arrow_box.y1) / 2.0
        parent_pair: tuple[Box, Box] | None = None
        for left_panel, right_panel in zip(sorted_panels, sorted_panels[1:], strict=False):
            if left_panel.x1 <= arrow_mid_x <= right_panel.x0:
                parent_pair = (left_panel, right_panel)
                break
        if parent_pair is None:
            continue
        shared_y0 = max(parent_pair[0].y0, parent_pair[1].y0)
        shared_y1 = min(parent_pair[0].y1, parent_pair[1].y1)
        shared_height = max(shared_y1 - shared_y0, 1e-9)
        shared_mid_y = (shared_y0 + shared_y1) / 2.0
        if abs(arrow_mid_y - shared_mid_y) <= max(shared_height * 0.18, (arrow_box.y1 - arrow_box.y0) * 1.5):
            continue
        issues.append(
            _issue(
                rule_id="arrow_midline_alignment",
                message="graphical-abstract arrows must stay near the shared vertical midline between adjacent panels",
                target="arrow_connector",
                box_refs=(arrow_box.box_id, parent_pair[0].box_id, parent_pair[1].box_id),
            )
        )
    return issues
