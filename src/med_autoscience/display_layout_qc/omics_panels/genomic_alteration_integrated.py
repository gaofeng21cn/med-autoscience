from __future__ import annotations

from ..shared import (
    Any,
    Box,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_composite_panel_label_anchors,
    _check_legend_panel_overlap,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _issue,
    _layout_override_flag,
    _point_within_box,
    _require_non_empty_text,
    _require_numeric,
    math,
)
from .genomic_alteration_landscape import _check_publication_genomic_alteration_consequence_panel

def _check_publication_genomic_alteration_multiomic_consequence_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_publication_genomic_alteration_consequence_panel(
        sidecar,
        max_panel_count=3,
        required_panel_ids=("proteome", "phosphoproteome", "glycoproteome"),
    )
    consequence_panels = sidecar.metrics.get("consequence_panels")
    if isinstance(consequence_panels, list) and len(consequence_panels) != 3:
        issues.append(
            _issue(
                rule_id="consequence_panel_count_invalid",
                message="genomic alteration multiomic consequence panel requires exactly three consequence panels",
                target="metrics.consequence_panels",
                observed=len(consequence_panels),
                expected=3,
            )
        )
    return issues

def _check_publication_genomic_alteration_pathway_integrated_composite_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues = _check_publication_genomic_alteration_multiomic_consequence_panel(sidecar)
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("colorbar",)))

    pathway_effect_scale_label = str(sidecar.metrics.get("pathway_effect_scale_label") or "").strip()
    if not pathway_effect_scale_label:
        issues.append(
            _issue(
                rule_id="pathway_effect_scale_label_missing",
                message="pathway-integrated composite requires a non-empty pathway_effect_scale_label",
                target="metrics.pathway_effect_scale_label",
            )
        )
    pathway_size_scale_label = str(sidecar.metrics.get("pathway_size_scale_label") or "").strip()
    if not pathway_size_scale_label:
        issues.append(
            _issue(
                rule_id="pathway_size_scale_label_missing",
                message="pathway-integrated composite requires a non-empty pathway_size_scale_label",
                target="metrics.pathway_size_scale_label",
            )
        )

    pathway_label_payload = sidecar.metrics.get("pathway_labels")
    if not isinstance(pathway_label_payload, list) or not pathway_label_payload:
        issues.append(
            _issue(
                rule_id="pathway_labels_missing",
                message="pathway-integrated composite requires non-empty pathway_labels metrics",
                target="metrics.pathway_labels",
            )
        )
        return issues
    pathway_labels = [str(item).strip() for item in pathway_label_payload]
    if any(not item for item in pathway_labels):
        issues.append(
            _issue(
                rule_id="pathway_label_invalid",
                message="pathway_labels must be non-empty",
                target="metrics.pathway_labels",
            )
        )
    if len(set(pathway_labels)) != len(pathway_labels):
        issues.append(
            _issue(
                rule_id="pathway_labels_not_unique",
                message="pathway_labels must be unique",
                target="metrics.pathway_labels",
            )
        )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    required_panel_ids = ("proteome", "phosphoproteome", "glycoproteome")
    pathway_panels = sidecar.metrics.get("pathway_panels")
    if not isinstance(pathway_panels, list) or not pathway_panels:
        issues.append(
            _issue(
                rule_id="pathway_panels_missing",
                message="pathway-integrated composite requires non-empty pathway_panels metrics",
                target="metrics.pathway_panels",
            )
        )
        return issues
    if len(pathway_panels) != 3:
        issues.append(
            _issue(
                rule_id="pathway_panel_count_invalid",
                message="pathway-integrated composite requires exactly three pathway panels",
                target="metrics.pathway_panels",
                observed=len(pathway_panels),
                expected=3,
            )
        )

    expected_coordinates = {(panel_id, pathway_label) for panel_id in required_panel_ids for pathway_label in pathway_labels}
    observed_coordinates: set[tuple[str, str]] = set()
    observed_panel_ids: set[str] = set()

    for panel_index, payload in enumerate(pathway_panels):
        if not isinstance(payload, dict):
            raise ValueError(f"layout_sidecar.metrics.pathway_panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_text(
            payload.get("panel_id"),
            label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].panel_id",
        )
        observed_panel_ids.add(panel_id)

        panel_box_id = _require_non_empty_text(
            payload.get("panel_box_id"),
            label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].panel_box_id",
        )
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="pathway_panel_box_missing",
                    message="panel_box_id must resolve to an existing pathway panel box",
                    target=f"metrics.pathway_panels[{panel_index}].panel_box_id",
                    observed=panel_box_id,
                )
            )

        panel_label_box_id = _require_non_empty_text(
            payload.get("panel_label_box_id"),
            label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].panel_label_box_id",
        )
        panel_label_box = layout_boxes_by_id.get(panel_label_box_id)
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="pathway_panel_label_box_missing",
                    message="panel_label_box_id must resolve to an existing layout box",
                    target=f"metrics.pathway_panels[{panel_index}].panel_label_box_id",
                    observed=panel_label_box_id,
                )
            )
        elif panel_box is not None and not _boxes_overlap(panel_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="pathway_panel_label_anchor_drift",
                    message="pathway panel label must stay anchored inside its panel",
                    target=f"metrics.pathway_panels[{panel_index}].panel_label_box_id",
                    box_refs=(panel_label_box.box_id, panel_box.box_id),
                )
            )

        for field_name in ("panel_title_box_id", "x_axis_title_box_id"):
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].{field_name}",
            )
            if box_id not in layout_boxes_by_id:
                issues.append(
                    _issue(
                        rule_id="pathway_layout_box_missing",
                        message=f"{field_name} must resolve to an existing layout box",
                        target=f"metrics.pathway_panels[{panel_index}].{field_name}",
                        observed=box_id,
                    )
                )

        points_payload = payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            issues.append(
                _issue(
                    rule_id="pathway_points_missing",
                    message="every pathway panel must expose non-empty points metrics",
                    target=f"metrics.pathway_panels[{panel_index}].points",
                )
            )
            continue

        seen_pathway_labels: set[str] = set()
        for point_index, point in enumerate(points_payload):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}] must be an object")
            pathway_label = _require_non_empty_text(
                point.get("pathway_label"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].pathway_label",
            )
            if pathway_label in seen_pathway_labels:
                issues.append(
                    _issue(
                        rule_id="pathway_point_label_duplicate",
                        message="pathway_label must be unique within each pathway panel",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}].pathway_label",
                        observed=pathway_label,
                    )
                )
            seen_pathway_labels.add(pathway_label)
            observed_coordinates.add((panel_id, pathway_label))
            if pathway_label not in set(pathway_labels):
                issues.append(
                    _issue(
                        rule_id="pathway_point_label_unknown",
                        message="pathway points must stay inside declared pathway_labels",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}].pathway_label",
                        observed=pathway_label,
                    )
                )

            point_x = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].x",
            )
            point_y = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].y",
            )
            _require_numeric(
                point.get("x_value"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].x_value",
            )
            _require_numeric(
                point.get("effect_value"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].effect_value",
            )
            size_value = _require_numeric(
                point.get("size_value"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].size_value",
            )
            if size_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="pathway_size_value_negative",
                        message="pathway size_value must be non-negative",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}].size_value",
                        observed=size_value,
                    )
                )
            if panel_box is not None and not _point_within_box(panel_box, x=point_x, y=point_y):
                issues.append(
                    _issue(
                        rule_id="pathway_point_outside_panel",
                        message="pathway point coordinates must stay within the panel bounds",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )

            point_box_id = _require_non_empty_text(
                point.get("point_box_id"),
                label=f"layout_sidecar.metrics.pathway_panels[{panel_index}].points[{point_index}].point_box_id",
            )
            point_box = layout_boxes_by_id.get(point_box_id)
            if point_box is None:
                issues.append(
                    _issue(
                        rule_id="pathway_point_box_missing",
                        message="point_box_id must resolve to an existing layout box",
                        target=f"metrics.pathway_panels[{panel_index}].points[{point_index}].point_box_id",
                        observed=point_box_id,
                    )
                )
            elif panel_box is not None and not _box_within_box(point_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="pathway_point_box_outside_panel",
                        message="pathway point boxes must stay within the panel bounds",
                        target=f"layout_boxes.{point_box.box_id}",
                        box_refs=(point_box.box_id, panel_box.box_id),
                    )
                )

    if observed_panel_ids != set(required_panel_ids):
        issues.append(
            _issue(
                rule_id="pathway_panel_ids_invalid",
                message="pathway panel ids must match the declared multiomic layer vocabulary",
                target="metrics.pathway_panels",
                observed=sorted(observed_panel_ids),
                expected=sorted(required_panel_ids),
            )
        )
    if observed_coordinates != expected_coordinates:
        issues.append(
            _issue(
                rule_id="pathway_point_coverage_mismatch",
                message="pathway points must cover every declared panel/pathway coordinate exactly once",
                target="metrics.pathway_panels",
                observed=sorted(observed_coordinates),
                expected=sorted(expected_coordinates),
            )
        )

    return issues

def _check_publication_genomic_program_governance_summary_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    required_box_types = [
        "panel_title",
        "panel_label",
        "row_label",
        "evidence_cell",
        "priority_badge",
        "verdict_value",
        "row_support",
        "row_action",
        "legend",
        "colorbar",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(
        _check_pairwise_non_overlap(
            tuple(
                box
                for box in sidecar.layout_boxes
                if box.box_type
                in {
                    "title",
                    "panel_title",
                    "panel_label",
                    "row_label",
                    "priority_badge",
                    "verdict_value",
                    "row_support",
                    "row_action",
                    "row_detail",
                }
            ),
            rule_id="text_box_overlap",
            target="text",
        )
    )

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    if len(panel_boxes) != 2:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="genomic program governance summary requires exactly two panels",
                target="panel_boxes",
                expected={"count": 2},
                observed={"count": len(panel_boxes)},
            )
        )
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    evidence_panel = panel_boxes_by_id.get("panel_evidence")
    summary_panel = panel_boxes_by_id.get("panel_summary")
    if evidence_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="genomic program governance summary qc requires panel_evidence and panel_summary",
                target="panel_boxes",
            )
        )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_evidence",
                "panel_label_B": "panel_summary",
            },
            allow_top_overhang_ratio=0.10,
            allow_left_overhang_ratio=0.12,
        )
    )

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_boxes_by_id = {box.box_id: box for box in sidecar.guide_boxes}

    def _check_panel_title_alignment(*, title_box_id: str, panel_box: Box) -> None:
        title_box = layout_boxes_by_id.get(title_box_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="genomic program governance summary requires both panel titles",
                    target="panel_title",
                    expected=title_box_id,
                )
            )
            return
        aligned_horizontally = title_box.x0 >= panel_box.x0 - 0.02 and title_box.x1 <= panel_box.x1 + 0.02
        close_to_panel_top = title_box.y0 >= panel_box.y0 - 0.02 and title_box.y1 <= panel_box.y1 + 0.10
        if not (aligned_horizontally and close_to_panel_top):
            issues.append(
                _issue(
                    rule_id="panel_title_out_of_alignment",
                    message="panel titles must stay tightly aligned with their parent panel",
                    target="panel_title",
                    box_refs=(title_box.box_id, panel_box.box_id),
                )
            )

    if evidence_panel is not None:
        _check_panel_title_alignment(title_box_id="panel_title_A", panel_box=evidence_panel)
    if summary_panel is not None:
        _check_panel_title_alignment(title_box_id="panel_title_B", panel_box=summary_panel)

    colorbar_box = guide_boxes_by_id.get("colorbar_effect")
    if colorbar_box is None:
        issues.append(
            _issue(
                rule_id="colorbar_missing",
                message="genomic program governance summary requires a colorbar for effect encoding",
                target="guide_boxes",
                expected="colorbar_effect",
            )
        )
    elif evidence_panel is not None and not _box_within_box(colorbar_box, evidence_panel):
        issues.append(
            _issue(
                rule_id="colorbar_out_of_panel",
                message="effect colorbar must stay within the evidence panel region",
                target="colorbar",
                box_refs=(colorbar_box.box_id, evidence_panel.box_id),
            )
        )

    legend_box = guide_boxes_by_id.get("legend_support")
    if legend_box is None:
        issues.append(
            _issue(
                rule_id="legend_missing",
                message="genomic program governance summary requires a support legend",
                target="guide_boxes",
                expected="legend_support",
            )
        )

    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    _require_non_empty_text(metrics.get("effect_scale_label"), label="layout_sidecar.metrics.effect_scale_label")
    _require_non_empty_text(metrics.get("support_scale_label"), label="layout_sidecar.metrics.support_scale_label")

    expected_layer_ids = (
        "alteration",
        "proteome",
        "phosphoproteome",
        "glycoproteome",
        "pathway",
    )
    expected_layer_labels = (
        "Alteration",
        "Proteome",
        "Phosphoproteome",
        "Glycoproteome",
        "Pathway",
    )
    layer_labels = metrics.get("layer_labels")
    if not isinstance(layer_labels, list) or not layer_labels:
        issues.append(
            _issue(
                rule_id="layer_labels_missing",
                message="genomic program governance summary requires non-empty layer_labels",
                target="metrics.layer_labels",
            )
        )
    else:
        observed_layer_labels = tuple(_require_non_empty_text(item, label=f"layout_sidecar.metrics.layer_labels[{index}]") for index, item in enumerate(layer_labels))
        if observed_layer_labels != expected_layer_labels:
            issues.append(
                _issue(
                    rule_id="layer_labels_invalid",
                    message="layer_labels must stay aligned to the fixed five-layer governance contract",
                    target="metrics.layer_labels",
                    observed=observed_layer_labels,
                    expected=expected_layer_labels,
                )
            )

    programs = metrics.get("programs")
    if not isinstance(programs, list) or not programs:
        issues.append(
            _issue(
                rule_id="programs_missing",
                message="genomic program governance summary requires non-empty program metrics",
                target="metrics.programs",
            )
        )
        return issues

    supported_priority_bands = {"high_priority", "monitor", "watchlist"}
    supported_verdicts = {"convergent", "layer_specific", "context_dependent", "insufficient_support"}
    seen_program_ids: set[str] = set()
    seen_program_labels: set[str] = set()
    seen_priority_ranks: set[int] = set()
    for index, item in enumerate(programs):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.programs[{index}] must be an object")

        program_id = _require_non_empty_text(
            item.get("program_id"),
            label=f"layout_sidecar.metrics.programs[{index}].program_id",
        )
        if program_id in seen_program_ids:
            issues.append(
                _issue(
                    rule_id="program_id_duplicate",
                    message="program ids must stay unique",
                    target=f"metrics.programs[{index}].program_id",
                    observed=program_id,
                )
            )
        seen_program_ids.add(program_id)

        program_label = _require_non_empty_text(
            item.get("program_label"),
            label=f"layout_sidecar.metrics.programs[{index}].program_label",
        )
        if program_label in seen_program_labels:
            issues.append(
                _issue(
                    rule_id="program_label_duplicate",
                    message="program labels must stay unique",
                    target=f"metrics.programs[{index}].program_label",
                    observed=program_label,
                )
            )
        seen_program_labels.add(program_label)

        _require_non_empty_text(
            item.get("lead_driver_label"),
            label=f"layout_sidecar.metrics.programs[{index}].lead_driver_label",
        )
        _require_non_empty_text(
            item.get("dominant_pathway_label"),
            label=f"layout_sidecar.metrics.programs[{index}].dominant_pathway_label",
        )
        _require_non_empty_text(
            item.get("action"),
            label=f"layout_sidecar.metrics.programs[{index}].action",
        )

        pathway_hit_count = _require_numeric(
            item.get("pathway_hit_count"),
            label=f"layout_sidecar.metrics.programs[{index}].pathway_hit_count",
        )
        if not float(pathway_hit_count).is_integer() or pathway_hit_count <= 0:
            issues.append(
                _issue(
                    rule_id="pathway_hit_count_invalid",
                    message="pathway_hit_count must stay a positive integer",
                    target=f"metrics.programs[{index}].pathway_hit_count",
                    observed=pathway_hit_count,
                )
            )

        priority_rank = _require_numeric(
            item.get("priority_rank"),
            label=f"layout_sidecar.metrics.programs[{index}].priority_rank",
        )
        if not float(priority_rank).is_integer() or priority_rank <= 0:
            issues.append(
                _issue(
                    rule_id="priority_rank_invalid",
                    message="priority_rank must stay a positive integer",
                    target=f"metrics.programs[{index}].priority_rank",
                    observed=priority_rank,
                )
            )
        else:
            normalized_priority_rank = int(priority_rank)
            if normalized_priority_rank in seen_priority_ranks:
                issues.append(
                    _issue(
                        rule_id="priority_rank_duplicate",
                        message="priority_rank values must stay unique",
                        target=f"metrics.programs[{index}].priority_rank",
                        observed=normalized_priority_rank,
                    )
                )
            seen_priority_ranks.add(normalized_priority_rank)

        priority_band = _require_non_empty_text(
            item.get("priority_band"),
            label=f"layout_sidecar.metrics.programs[{index}].priority_band",
        )
        if priority_band not in supported_priority_bands:
            issues.append(
                _issue(
                    rule_id="priority_band_invalid",
                    message="priority_band must stay within the fixed governance vocabulary",
                    target=f"metrics.programs[{index}].priority_band",
                    observed=priority_band,
                    expected=sorted(supported_priority_bands),
                )
            )

        verdict = _require_non_empty_text(
            item.get("verdict"),
            label=f"layout_sidecar.metrics.programs[{index}].verdict",
        )
        if verdict not in supported_verdicts:
            issues.append(
                _issue(
                    rule_id="verdict_invalid",
                    message="verdict must stay within the fixed governance vocabulary",
                    target=f"metrics.programs[{index}].verdict",
                    observed=verdict,
                    expected=sorted(supported_verdicts),
                )
            )

        for field_name, panel_box, box_type, rule_id in (
            ("priority_box_id", summary_panel, "priority_badge", "priority_box_missing"),
            ("verdict_box_id", summary_panel, "verdict_value", "verdict_box_missing"),
            ("support_box_id", summary_panel, "row_support", "support_box_missing"),
            ("action_box_id", summary_panel, "row_action", "action_box_missing"),
        ):
            box_id = str(item.get(field_name) or "").strip()
            if not box_id:
                issues.append(
                    _issue(
                        rule_id=rule_id,
                        message=f"{field_name} must reference an audited {box_type} box",
                        target=f"metrics.programs[{index}].{field_name}",
                    )
                )
                continue
            box = layout_boxes_by_id.get(box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id=rule_id,
                        message=f"{field_name} must reference an existing {box_type} box",
                        target=f"metrics.programs[{index}].{field_name}",
                        expected=box_id,
                    )
                )
                continue
            if panel_box is not None and not _box_within_box(box, panel_box):
                issues.append(
                    _issue(
                        rule_id="summary_box_out_of_panel",
                        message="summary governance boxes must stay inside the summary panel",
                        target=box_type,
                        box_refs=(box.box_id, panel_box.box_id),
                    )
                )

        row_label_box_id = str(item.get("row_label_box_id") or "").strip()
        if row_label_box_id:
            if layout_boxes_by_id.get(row_label_box_id) is None:
                issues.append(
                    _issue(
                        rule_id="row_label_box_missing",
                        message="row_label_box_id must reference an existing row_label box",
                        target=f"metrics.programs[{index}].row_label_box_id",
                        expected=row_label_box_id,
                    )
                )

        layer_supports = item.get("layer_supports")
        if not isinstance(layer_supports, list) or not layer_supports:
            issues.append(
                _issue(
                    rule_id="program_layer_support_coverage_mismatch",
                    message="each program must cover the fixed five-layer governance grid exactly once",
                    target=f"metrics.programs[{index}].layer_supports",
                    observed={"layers": 0},
                    expected={"layer_ids": expected_layer_ids},
                )
            )
            continue

        observed_layer_ids: list[str] = []
        for layer_index, layer_support in enumerate(layer_supports):
            if not isinstance(layer_support, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.programs[{index}].layer_supports[{layer_index}] must be an object"
                )
            layer_id = _require_non_empty_text(
                layer_support.get("layer_id"),
                label=f"layout_sidecar.metrics.programs[{index}].layer_supports[{layer_index}].layer_id",
            )
            observed_layer_ids.append(layer_id)

            effect_value = _require_numeric(
                layer_support.get("effect_value"),
                label=f"layout_sidecar.metrics.programs[{index}].layer_supports[{layer_index}].effect_value",
            )
            support_fraction = _require_numeric(
                layer_support.get("support_fraction"),
                label=f"layout_sidecar.metrics.programs[{index}].layer_supports[{layer_index}].support_fraction",
            )
            if not math.isfinite(effect_value):
                issues.append(
                    _issue(
                        rule_id="layer_effect_non_finite",
                        message="effect_value must stay finite",
                        target=f"metrics.programs[{index}].layer_supports[{layer_index}].effect_value",
                    )
                )
            if support_fraction < 0.0 or support_fraction > 1.0:
                issues.append(
                    _issue(
                        rule_id="layer_support_fraction_out_of_range",
                        message="support_fraction must stay within [0, 1]",
                        target=f"metrics.programs[{index}].layer_supports[{layer_index}].support_fraction",
                        observed=support_fraction,
                    )
                )

            cell_box_id = str(layer_support.get("cell_box_id") or "").strip()
            if not cell_box_id:
                issues.append(
                    _issue(
                        rule_id="evidence_cell_box_missing",
                        message="layer supports must reference an audited evidence_cell box",
                        target=f"metrics.programs[{index}].layer_supports[{layer_index}].cell_box_id",
                    )
                )
                continue
            cell_box = layout_boxes_by_id.get(cell_box_id)
            if cell_box is None:
                issues.append(
                    _issue(
                        rule_id="evidence_cell_box_missing",
                        message="layer supports must reference an existing evidence_cell box",
                        target=f"metrics.programs[{index}].layer_supports[{layer_index}].cell_box_id",
                        expected=cell_box_id,
                    )
                )
                continue
            if evidence_panel is not None and not _box_within_box(cell_box, evidence_panel):
                issues.append(
                    _issue(
                        rule_id="evidence_cell_out_of_panel",
                        message="evidence cells must stay within the evidence panel",
                        target="evidence_cell",
                        box_refs=(cell_box.box_id, evidence_panel.box_id),
                    )
                )

        if tuple(observed_layer_ids) != expected_layer_ids:
            issues.append(
                _issue(
                    rule_id="program_layer_support_coverage_mismatch",
                    message="each program must cover the fixed five-layer governance grid exactly once",
                    target=f"metrics.programs[{index}].layer_supports",
                    observed={"layer_ids": tuple(observed_layer_ids)},
                    expected={"layer_ids": expected_layer_ids},
                )
            )

    return issues
