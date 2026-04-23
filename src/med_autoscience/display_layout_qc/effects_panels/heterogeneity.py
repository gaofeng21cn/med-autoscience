from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_composite_panel_label_anchors,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _issue,
    _layout_override_flag,
    _require_non_empty_text,
    _require_numeric,
)

def _check_publication_broader_heterogeneity_summary_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "panel_label",
        "subplot_x_axis_title",
        "legend_title",
        "legend_label",
        "row_label",
        "estimate_marker",
        "ci_segment",
        "verdict_value",
        "reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    matrix_panel = panel_boxes_by_id.get("matrix_panel")
    summary_panel = panel_boxes_by_id.get("summary_panel")
    if matrix_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="broader heterogeneity summary qc requires matrix_panel and summary_panel",
                target="panel_boxes",
            )
        )
        return issues

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}

    if metrics.get("reference_value") is None:
        issues.append(
            _issue(
                rule_id="reference_value_missing",
                message="broader heterogeneity summary qc requires a numeric reference_value",
                target="metrics.reference_value",
            )
        )
    else:
        _require_numeric(metrics.get("reference_value"), label="layout_sidecar.metrics.reference_value")

    matrix_panel_metrics = metrics.get("matrix_panel")
    if not isinstance(matrix_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="matrix_panel_metrics_missing",
                message="broader heterogeneity summary qc requires matrix_panel metrics",
                target="metrics.matrix_panel",
            )
        )
        return issues
    summary_panel_metrics = metrics.get("summary_panel")
    if not isinstance(summary_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="summary_panel_metrics_missing",
                message="broader heterogeneity summary qc requires summary_panel metrics",
                target="metrics.summary_panel",
            )
        )
        return issues

    reference_line_box = guide_box_by_id.get(str(matrix_panel_metrics.get("reference_line_box_id") or "").strip())
    if reference_line_box is None:
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="broader heterogeneity summary qc requires one reference line inside the matrix panel",
                target="metrics.matrix_panel.reference_line_box_id",
                box_refs=(matrix_panel.box_id,),
            )
        )
    elif not _box_within_box(reference_line_box, matrix_panel):
        issues.append(
            _issue(
                rule_id="reference_line_outside_matrix_panel",
                message="broader heterogeneity summary reference line must stay within the matrix panel",
                target=f"guide_boxes.{reference_line_box.box_id}",
                box_refs=(reference_line_box.box_id, matrix_panel.box_id),
            )
        )

    legend_title_box = layout_box_by_id.get(str(metrics.get("slice_legend_title_box_id") or "").strip())
    if legend_title_box is None:
        issues.append(
            _issue(
                rule_id="slice_legend_title_missing",
                message="broader heterogeneity summary qc requires one slice legend title box",
                target="metrics.slice_legend_title_box_id",
            )
        )

    slices = metrics.get("slices")
    if not isinstance(slices, list) or not slices:
        issues.append(
            _issue(
                rule_id="slices_missing",
                message="broader heterogeneity summary qc requires non-empty slice metrics",
                target="metrics.slices",
            )
        )
        return issues
    if len(slices) < 2 or len(slices) > 5:
        issues.append(
            _issue(
                rule_id="slice_count_invalid",
                message="broader heterogeneity summary qc requires between 2 and 5 slices",
                target="metrics.slices",
                observed={"count": len(slices)},
                expected={"minimum": 2, "maximum": 5},
            )
        )

    supported_slice_kinds = {"cohort", "subgroup", "adjustment", "sensitivity"}
    declared_slice_ids: list[str] = []
    seen_slice_ids: set[str] = set()
    seen_slice_labels: set[str] = set()
    previous_slice_order: int | None = None
    for slice_index, slice_metric in enumerate(slices):
        if not isinstance(slice_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.slices[{slice_index}] must be an object")
        slice_id = _require_non_empty_text(
            slice_metric.get("slice_id"),
            label=f"layout_sidecar.metrics.slices[{slice_index}].slice_id",
        )
        if slice_id in seen_slice_ids:
            issues.append(
                _issue(
                    rule_id="slice_id_duplicate",
                    message="broader heterogeneity summary slice_id values must be unique",
                    target=f"metrics.slices[{slice_index}].slice_id",
                )
            )
        seen_slice_ids.add(slice_id)
        slice_label = _require_non_empty_text(
            slice_metric.get("slice_label"),
            label=f"layout_sidecar.metrics.slices[{slice_index}].slice_label",
        )
        if slice_label in seen_slice_labels:
            issues.append(
                _issue(
                    rule_id="slice_label_duplicate",
                    message="broader heterogeneity summary slice_label values must be unique",
                    target=f"metrics.slices[{slice_index}].slice_label",
                )
            )
        seen_slice_labels.add(slice_label)
        slice_kind = _require_non_empty_text(
            slice_metric.get("slice_kind"),
            label=f"layout_sidecar.metrics.slices[{slice_index}].slice_kind",
        )
        if slice_kind not in supported_slice_kinds:
            issues.append(
                _issue(
                    rule_id="slice_kind_invalid",
                    message="broader heterogeneity summary slice_kind must be one of cohort, subgroup, adjustment, sensitivity",
                    target=f"metrics.slices[{slice_index}].slice_kind",
                    observed=slice_kind,
                )
            )
        slice_order = int(_require_numeric(slice_metric.get("slice_order"), label=f"layout_sidecar.metrics.slices[{slice_index}].slice_order"))
        if previous_slice_order is not None and slice_order <= previous_slice_order:
            issues.append(
                _issue(
                    rule_id="slice_order_invalid",
                    message="broader heterogeneity summary slices must have strictly increasing slice_order",
                    target=f"metrics.slices[{slice_index}].slice_order",
                )
            )
        previous_slice_order = slice_order
        legend_label_box = layout_box_by_id.get(str(slice_metric.get("legend_label_box_id") or "").strip())
        if legend_label_box is None:
            issues.append(
                _issue(
                    rule_id="slice_legend_label_missing",
                    message="every broader heterogeneity slice must reference a legend label box",
                    target=f"metrics.slices[{slice_index}].legend_label_box_id",
                )
            )
        declared_slice_ids.append(slice_id)

    effect_rows = metrics.get("effect_rows")
    if not isinstance(effect_rows, list) or not effect_rows:
        issues.append(
            _issue(
                rule_id="effect_rows_missing",
                message="broader heterogeneity summary qc requires non-empty effect_rows metrics",
                target="metrics.effect_rows",
            )
        )
        return issues

    supported_verdicts = {"stable", "attenuated", "context_dependent", "unstable"}
    declared_slice_id_set = set(declared_slice_ids)
    label_panel_map = {
        str(matrix_panel_metrics.get("panel_label_box_id") or "").strip() or "panel_label_A": matrix_panel.box_id,
        str(summary_panel_metrics.get("panel_label_box_id") or "").strip() or "panel_label_B": summary_panel.box_id,
    }
    summary_panel_height = summary_panel.y1 - summary_panel.y0
    alignment_tolerance = max(summary_panel_height * 0.08, 0.025)
    for row_index, row in enumerate(effect_rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.effect_rows[{row_index}] must be an object")
        verdict = _require_non_empty_text(
            row.get("verdict"),
            label=f"layout_sidecar.metrics.effect_rows[{row_index}].verdict",
        )
        if verdict not in supported_verdicts:
            issues.append(
                _issue(
                    rule_id="effect_row_verdict_invalid",
                    message="broader heterogeneity summary verdicts must use the supported state vocabulary",
                    target=f"metrics.effect_rows[{row_index}].verdict",
                    observed=verdict,
                )
            )

        label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="effect_row_label_missing",
                    message="broader heterogeneity summary rows must reference a row label box",
                    target=f"metrics.effect_rows[{row_index}].label_box_id",
                    box_refs=(matrix_panel.box_id,),
                )
            )
        elif _boxes_overlap(label_box, matrix_panel):
            issues.append(
                _issue(
                    rule_id="effect_row_label_matrix_overlap",
                    message="broader heterogeneity summary row labels must stay outside the matrix panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, matrix_panel.box_id),
                )
            )

        verdict_box = layout_box_by_id.get(str(row.get("verdict_box_id") or "").strip())
        if verdict_box is None:
            issues.append(
                _issue(
                    rule_id="verdict_box_missing",
                    message="broader heterogeneity summary rows must reference a verdict box",
                    target=f"metrics.effect_rows[{row_index}].verdict_box_id",
                    box_refs=(summary_panel.box_id,),
                )
            )
        elif not _box_within_box(verdict_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="verdict_box_outside_summary_panel",
                    message="broader heterogeneity summary verdict boxes must stay within the summary panel",
                    target=f"layout_boxes.{verdict_box.box_id}",
                    box_refs=(verdict_box.box_id, summary_panel.box_id),
                )
            )

        detail_box_id = str(row.get("detail_box_id") or "").strip()
        detail_box = layout_box_by_id.get(detail_box_id) if detail_box_id else None
        if detail_box is not None and not _box_within_box(detail_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="detail_box_outside_summary_panel",
                    message="broader heterogeneity summary detail boxes must stay within the summary panel",
                    target=f"layout_boxes.{detail_box.box_id}",
                    box_refs=(detail_box.box_id, summary_panel.box_id),
                )
            )

        if label_box is not None and verdict_box is not None:
            label_center_y = (label_box.y0 + label_box.y1) / 2.0
            verdict_center_y = (verdict_box.y0 + verdict_box.y1) / 2.0
            if abs(label_center_y - verdict_center_y) > alignment_tolerance:
                issues.append(
                    _issue(
                        rule_id="verdict_row_misaligned",
                        message="broader heterogeneity summary verdicts must stay vertically aligned to their effect row",
                        target=f"metrics.effect_rows[{row_index}].verdict_box_id",
                        observed={"label_center_y": label_center_y, "verdict_center_y": verdict_center_y},
                    )
                )

        slice_estimates = row.get("slice_estimates")
        if not isinstance(slice_estimates, list) or not slice_estimates:
            issues.append(
                _issue(
                    rule_id="slice_estimates_missing",
                    message="every broader heterogeneity summary row must provide non-empty slice_estimates",
                    target=f"metrics.effect_rows[{row_index}].slice_estimates",
                )
            )
            continue

        seen_row_slice_ids: set[str] = set()
        for estimate_index, estimate in enumerate(slice_estimates):
            if not isinstance(estimate, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}] must be an object"
                )
            slice_id = _require_non_empty_text(
                estimate.get("slice_id"),
                label=f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}].slice_id",
            )
            seen_row_slice_ids.add(slice_id)
            lower = _require_numeric(
                estimate.get("lower"),
                label=f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}].lower",
            )
            point_estimate = _require_numeric(
                estimate.get("estimate"),
                label=f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}].estimate",
            )
            upper = _require_numeric(
                estimate.get("upper"),
                label=f"layout_sidecar.metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}].upper",
            )
            if not (lower <= point_estimate <= upper):
                issues.append(
                    _issue(
                        rule_id="estimate_outside_interval",
                        message="broader heterogeneity summary estimates must lie within their confidence interval",
                        target=f"metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}]",
                        observed={"lower": lower, "estimate": point_estimate, "upper": upper},
                    )
                )
            marker_box = layout_box_by_id.get(str(estimate.get("marker_box_id") or "").strip())
            interval_box = layout_box_by_id.get(str(estimate.get("interval_box_id") or "").strip())
            if marker_box is None or interval_box is None:
                issues.append(
                    _issue(
                        rule_id="slice_estimate_box_missing",
                        message="broader heterogeneity summary slice estimates must reference marker and interval boxes",
                        target=f"metrics.effect_rows[{row_index}].slice_estimates[{estimate_index}]",
                        box_refs=(matrix_panel.box_id,),
                    )
                )
                continue
            if not _box_within_box(marker_box, matrix_panel):
                issues.append(
                    _issue(
                        rule_id="estimate_marker_outside_matrix_panel",
                        message="broader heterogeneity summary markers must stay within the matrix panel",
                        target=f"layout_boxes.{marker_box.box_id}",
                        box_refs=(marker_box.box_id, matrix_panel.box_id),
                    )
                )
            if not _box_within_box(interval_box, matrix_panel):
                issues.append(
                    _issue(
                        rule_id="ci_segment_outside_matrix_panel",
                        message="broader heterogeneity summary confidence intervals must stay within the matrix panel",
                        target=f"layout_boxes.{interval_box.box_id}",
                        box_refs=(interval_box.box_id, matrix_panel.box_id),
                    )
                )

        if seen_row_slice_ids != declared_slice_id_set:
            issues.append(
                _issue(
                    rule_id="slice_coverage_mismatch",
                    message="broader heterogeneity summary rows must cover every declared slice exactly once",
                    target=f"metrics.effect_rows[{row_index}].slice_estimates",
                    observed={"slice_ids": sorted(seen_row_slice_ids)},
                    expected={"slice_ids": sorted(declared_slice_id_set)},
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )
    return issues
def _check_publication_interaction_effect_summary_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "panel_label",
        "subplot_x_axis_title",
        "row_label",
        "estimate_marker",
        "ci_segment",
        "verdict_value",
        "verdict_detail",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    estimate_panel = panel_boxes_by_id.get("estimate_panel")
    summary_panel = panel_boxes_by_id.get("summary_panel")
    if estimate_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="interaction effect summary qc requires estimate_panel and summary_panel",
                target="panel_boxes",
            )
        )
        return issues

    text_boxes = tuple(
        box for box in sidecar.layout_boxes if box.box_type in {"title", "panel_title", "panel_label", "subplot_x_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}

    if metrics.get("reference_value") is None:
        issues.append(
            _issue(
                rule_id="reference_value_missing",
                message="interaction effect summary qc requires a numeric reference_value",
                target="metrics.reference_value",
            )
        )
    else:
        _require_numeric(metrics.get("reference_value"), label="layout_sidecar.metrics.reference_value")

    estimate_panel_metrics = metrics.get("estimate_panel")
    if not isinstance(estimate_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="estimate_panel_metrics_missing",
                message="interaction effect summary qc requires estimate_panel metrics",
                target="metrics.estimate_panel",
            )
        )
        return issues
    summary_panel_metrics = metrics.get("summary_panel")
    if not isinstance(summary_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="summary_panel_metrics_missing",
                message="interaction effect summary qc requires summary_panel metrics",
                target="metrics.summary_panel",
            )
        )
        return issues

    panel_title_box = layout_box_by_id.get(str(estimate_panel_metrics.get("panel_title_box_id") or "").strip())
    x_axis_title_box = layout_box_by_id.get(str(estimate_panel_metrics.get("x_axis_title_box_id") or "").strip())
    if panel_title_box is None or x_axis_title_box is None:
        issues.append(
            _issue(
                rule_id="estimate_panel_text_box_missing",
                message="interaction effect estimate panel requires title and x-axis title boxes",
                target="metrics.estimate_panel",
                box_refs=(estimate_panel.box_id,),
            )
        )
    summary_panel_title_box = layout_box_by_id.get(str(summary_panel_metrics.get("panel_title_box_id") or "").strip())
    if summary_panel_title_box is None:
        issues.append(
            _issue(
                rule_id="summary_panel_title_missing",
                message="interaction effect summary panel requires a title box",
                target="metrics.summary_panel.panel_title_box_id",
                box_refs=(summary_panel.box_id,),
            )
        )

    reference_line_box = guide_box_by_id.get(str(estimate_panel_metrics.get("reference_line_box_id") or "").strip())
    if reference_line_box is None:
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="interaction effect summary qc requires one reference line inside the estimate panel",
                target="metrics.estimate_panel.reference_line_box_id",
                box_refs=(estimate_panel.box_id,),
            )
        )
    elif not _box_within_box(reference_line_box, estimate_panel):
        issues.append(
            _issue(
                rule_id="reference_line_outside_estimate_panel",
                message="interaction effect reference line must stay within the estimate panel",
                target=f"guide_boxes.{reference_line_box.box_id}",
                box_refs=(reference_line_box.box_id, estimate_panel.box_id),
            )
        )

    modifiers = metrics.get("modifiers")
    if not isinstance(modifiers, list) or not modifiers:
        issues.append(
            _issue(
                rule_id="modifiers_missing",
                message="interaction effect summary qc requires non-empty modifier metrics",
                target="metrics.modifiers",
            )
        )
        return issues
    if len(modifiers) < 2 or len(modifiers) > 6:
        issues.append(
            _issue(
                rule_id="modifier_count_invalid",
                message="interaction effect summary qc requires between 2 and 6 modifiers",
                target="metrics.modifiers",
                observed={"count": len(modifiers)},
                expected={"minimum": 2, "maximum": 6},
            )
        )

    supported_verdicts = {"credible", "suggestive", "uncertain"}
    seen_modifier_ids: set[str] = set()
    seen_modifier_labels: set[str] = set()
    label_panel_map = {
        str(estimate_panel_metrics.get("panel_label_box_id") or "").strip() or "panel_label_A": estimate_panel.box_id,
        str(summary_panel_metrics.get("panel_label_box_id") or "").strip() or "panel_label_B": summary_panel.box_id,
    }
    summary_panel_height = summary_panel.y1 - summary_panel.y0
    alignment_tolerance = max(summary_panel_height * 0.08, 0.025)
    for modifier_index, modifier in enumerate(modifiers):
        if not isinstance(modifier, dict):
            raise ValueError(f"layout_sidecar.metrics.modifiers[{modifier_index}] must be an object")

        modifier_id = _require_non_empty_text(
            modifier.get("modifier_id"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].modifier_id",
        )
        if modifier_id in seen_modifier_ids:
            issues.append(
                _issue(
                    rule_id="modifier_id_duplicate",
                    message="interaction effect summary modifier_id values must be unique",
                    target=f"metrics.modifiers[{modifier_index}].modifier_id",
                    observed=modifier_id,
                )
            )
        seen_modifier_ids.add(modifier_id)

        modifier_label = _require_non_empty_text(
            modifier.get("modifier_label"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].modifier_label",
        )
        if modifier_label in seen_modifier_labels:
            issues.append(
                _issue(
                    rule_id="modifier_label_duplicate",
                    message="interaction effect summary modifier labels must be unique",
                    target=f"metrics.modifiers[{modifier_index}].modifier_label",
                    observed=modifier_label,
                )
            )
        seen_modifier_labels.add(modifier_label)

        lower = _require_numeric(
            modifier.get("lower"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].lower",
        )
        interaction_estimate = _require_numeric(
            modifier.get("interaction_estimate"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].interaction_estimate",
        )
        upper = _require_numeric(
            modifier.get("upper"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].upper",
        )
        if not (lower <= interaction_estimate <= upper):
            issues.append(
                _issue(
                    rule_id="interaction_estimate_outside_interval",
                    message="interaction effect estimate must lie within the confidence interval",
                    target=f"metrics.modifiers[{modifier_index}]",
                    observed={"lower": lower, "interaction_estimate": interaction_estimate, "upper": upper},
                )
            )

        interaction_p_value = _require_numeric(
            modifier.get("interaction_p_value"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].interaction_p_value",
        )
        if interaction_p_value < 0.0 or interaction_p_value > 1.0:
            issues.append(
                _issue(
                    rule_id="interaction_p_value_invalid",
                    message="interaction effect summary p values must stay within [0.0, 1.0]",
                    target=f"metrics.modifiers[{modifier_index}].interaction_p_value",
                    observed=interaction_p_value,
                )
            )

        verdict = _require_non_empty_text(
            modifier.get("verdict"),
            label=f"layout_sidecar.metrics.modifiers[{modifier_index}].verdict",
        )
        if verdict not in supported_verdicts:
            issues.append(
                _issue(
                    rule_id="interaction_verdict_invalid",
                    message="interaction effect summary verdicts must use the supported vocabulary",
                    target=f"metrics.modifiers[{modifier_index}].verdict",
                    observed=verdict,
                )
            )

        label_box = layout_box_by_id.get(str(modifier.get("label_box_id") or "").strip())
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="modifier_label_missing",
                    message="interaction effect summary rows must reference a modifier label box",
                    target=f"metrics.modifiers[{modifier_index}].label_box_id",
                    box_refs=(estimate_panel.box_id,),
                )
            )
        elif _boxes_overlap(label_box, estimate_panel):
            issues.append(
                _issue(
                    rule_id="modifier_label_estimate_panel_overlap",
                    message="interaction modifier labels must stay outside the estimate panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, estimate_panel.box_id),
                )
            )

        support_label_box_id = str(modifier.get("support_label_box_id") or "").strip()
        support_label_box = layout_box_by_id.get(support_label_box_id) if support_label_box_id else None
        if support_label_box is not None and not _box_within_box(support_label_box, estimate_panel):
            issues.append(
                _issue(
                    rule_id="support_label_outside_estimate_panel",
                    message="interaction support labels must stay within the estimate panel",
                    target=f"layout_boxes.{support_label_box.box_id}",
                    box_refs=(support_label_box.box_id, estimate_panel.box_id),
                )
            )

        marker_box = layout_box_by_id.get(str(modifier.get("marker_box_id") or "").strip())
        interval_box = layout_box_by_id.get(str(modifier.get("interval_box_id") or "").strip())
        if marker_box is None or interval_box is None:
            issues.append(
                _issue(
                    rule_id="interaction_estimate_box_missing",
                    message="interaction effect rows must reference marker and interval boxes",
                    target=f"metrics.modifiers[{modifier_index}]",
                    box_refs=(estimate_panel.box_id,),
                )
            )
        else:
            if not _box_within_box(marker_box, estimate_panel):
                issues.append(
                    _issue(
                        rule_id="interaction_marker_outside_estimate_panel",
                        message="interaction markers must stay within the estimate panel",
                        target=f"layout_boxes.{marker_box.box_id}",
                        box_refs=(marker_box.box_id, estimate_panel.box_id),
                    )
                )
            if not _box_within_box(interval_box, estimate_panel):
                issues.append(
                    _issue(
                        rule_id="interaction_interval_outside_estimate_panel",
                        message="interaction confidence intervals must stay within the estimate panel",
                        target=f"layout_boxes.{interval_box.box_id}",
                        box_refs=(interval_box.box_id, estimate_panel.box_id),
                    )
                )

        verdict_box = layout_box_by_id.get(str(modifier.get("verdict_box_id") or "").strip())
        if verdict_box is None:
            issues.append(
                _issue(
                    rule_id="interaction_verdict_missing",
                    message="interaction effect rows must reference a verdict box",
                    target=f"metrics.modifiers[{modifier_index}].verdict_box_id",
                    box_refs=(summary_panel.box_id,),
                )
            )
        elif not _box_within_box(verdict_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="interaction_verdict_outside_summary_panel",
                    message="interaction verdict boxes must stay within the summary panel",
                    target=f"layout_boxes.{verdict_box.box_id}",
                    box_refs=(verdict_box.box_id, summary_panel.box_id),
                )
            )

        detail_box = layout_box_by_id.get(str(modifier.get("detail_box_id") or "").strip())
        if detail_box is None:
            issues.append(
                _issue(
                    rule_id="interaction_detail_missing",
                    message="interaction effect rows must reference a detail box",
                    target=f"metrics.modifiers[{modifier_index}].detail_box_id",
                    box_refs=(summary_panel.box_id,),
                )
            )
        elif not _box_within_box(detail_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="interaction_detail_outside_summary_panel",
                    message="interaction detail boxes must stay within the summary panel",
                    target=f"layout_boxes.{detail_box.box_id}",
                    box_refs=(detail_box.box_id, summary_panel.box_id),
                )
            )

        if label_box is not None and verdict_box is not None:
            label_center_y = (label_box.y0 + label_box.y1) / 2.0
            verdict_center_y = (verdict_box.y0 + verdict_box.y1) / 2.0
            if abs(label_center_y - verdict_center_y) > alignment_tolerance:
                issues.append(
                    _issue(
                        rule_id="interaction_verdict_row_misaligned",
                        message="interaction verdicts must stay vertically aligned to their modifier row",
                        target=f"metrics.modifiers[{modifier_index}].verdict_box_id",
                        observed={"label_center_y": label_center_y, "verdict_center_y": verdict_center_y},
                    )
                )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.12,
        )
    )
    return issues
