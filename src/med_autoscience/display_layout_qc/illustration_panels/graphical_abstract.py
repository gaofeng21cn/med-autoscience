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
    layout_style = str(sidecar.metrics.get("layout_style") or "").strip()
    required_box_types = ["title", "panel_label"]
    clinical_storyline_styles = {"clinical_storyline"}
    reference_guided_styles = {"reference_guided_flow", "reference_guided_single_canvas"}
    if layout_style not in clinical_storyline_styles:
        required_box_types.extend(("card_box", "footer_pill"))
    if layout_style in {"square_storyline", *reference_guided_styles}:
        required_box_types.append("visual_glyph")
    if layout_style in clinical_storyline_styles:
        required_box_types.extend(("visual_glyph", "stage_callout"))
    if layout_style in reference_guided_styles:
        required_box_types.append("evidence_cue")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

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
    visual_glyphs = _boxes_of_type(sidecar.layout_boxes, "visual_glyph")
    evidence_cues = _boxes_of_type(sidecar.layout_boxes, "evidence_cue")
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {
            "panel_title",
            "panel_subtitle",
            "card_title",
            "card_value",
            "card_detail",
            "evidence_cue",
            "stage_callout",
        }
    )

    issues.extend(_check_pairwise_non_overlap(card_boxes, rule_id="graphical_abstract_card_overlap", target="card_box"))
    issues.extend(_check_pairwise_non_overlap(footer_pills, rule_id="graphical_abstract_footer_overlap", target="footer_pill"))
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="graphical_abstract_text_overlap", target="text"))
    issues.extend(_check_pairwise_non_overlap(visual_glyphs, rule_id="graphical_abstract_visual_glyph_overlap", target="visual_glyph"))

    if layout_style in {"square_storyline", *reference_guided_styles, *clinical_storyline_styles}:
        if len(visual_glyphs) < len(panel_boxes):
            issues.append(
                _issue(
                    rule_id="graphical_abstract_visual_glyphs_missing",
                    message="graphical abstract requires one visual glyph per panel",
                    target="layout_boxes",
                    expected={"minimum_count": len(panel_boxes)},
                    observed={"count": len(visual_glyphs)},
                )
            )
        if len(arrow_boxes) < max(0, len(panel_boxes) - 1):
            issues.append(
                _issue(
                    rule_id="graphical_abstract_story_arrows_missing",
                    message="graphical abstract requires arrows between adjacent storyline panels",
                    target="guide_boxes",
                    expected={"minimum_count": max(0, len(panel_boxes) - 1)},
                    observed={"count": len(arrow_boxes)},
                )
            )
        if layout_style in reference_guided_styles and len(evidence_cues) < len(panel_boxes):
            issues.append(
                _issue(
                    rule_id="graphical_abstract_evidence_cues_missing",
                    message="reference-guided graphical abstract requires one evidence cue per panel",
                    target="layout_boxes",
                    expected={"minimum_count": len(panel_boxes)},
                    observed={"count": len(evidence_cues)},
                )
            )

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
    for visual_glyph in visual_glyphs:
        if any(_box_within_box(visual_glyph, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="visual_glyph_out_of_panel",
                message="graphical-abstract visual glyphs must stay within a panel",
                target="visual_glyph",
                box_refs=(visual_glyph.box_id,),
            )
        )
    for evidence_cue in evidence_cues:
        if any(_box_within_box(evidence_cue, panel_box) for panel_box in panel_boxes):
            continue
        issues.append(
            _issue(
                rule_id="evidence_cue_out_of_panel",
                message="graphical-abstract evidence cues must stay within a panel",
                target="evidence_cue",
                box_refs=(evidence_cue.box_id,),
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
        for visual_glyph in visual_glyphs:
            if not _boxes_overlap(arrow_box, visual_glyph):
                continue
            issues.append(
                _issue(
                    rule_id="arrow_visual_glyph_overlap",
                    message="graphical-abstract arrows must not overlap visual glyphs",
                    target="arrow_connector",
                    box_refs=(arrow_box.box_id, visual_glyph.box_id),
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
