from __future__ import annotations

from ..shared import (
    Any,
    Box,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _check_boxes_within_device,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _issue,
    _layout_override_flag,
    _require_non_empty_text,
    _require_numeric,
    math,
)

def _check_publication_center_transportability_governance_summary_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
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
        "row_metric",
        "row_action",
        "reference_line",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    if len(panel_boxes) != 2:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="center transportability governance summary requires exactly two panels",
                target="panel_boxes",
                expected={"count": 2},
                observed={"count": len(panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    metric_panel = panel_boxes_by_id.get("metric_panel")
    summary_panel = panel_boxes_by_id.get("summary_panel")
    if metric_panel is None or summary_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="center transportability governance summary qc requires metric_panel and summary_panel",
                target="panel_boxes",
            )
        )
        return issues

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}

    def _check_panel_title_alignment(*, title_box_id: str, panel_box: Box) -> None:
        title_box = layout_box_by_id.get(title_box_id)
        if title_box is None:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="center transportability governance summary requires both panel titles",
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

    def _check_panel_label_inside(*, label_box_id: str, panel_box: Box) -> None:
        label_box = layout_box_by_id.get(label_box_id)
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_missing",
                    message="center transportability governance summary requires both panel labels",
                    target="panel_label",
                    expected=label_box_id,
                )
            )
            return
        if not _box_within_box(label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="panel labels must stay within their parent panel",
                    target="panel_label",
                    box_refs=(label_box.box_id, panel_box.box_id),
                )
            )

    _check_panel_title_alignment(title_box_id="panel_title_A", panel_box=metric_panel)
    _check_panel_title_alignment(title_box_id="panel_title_B", panel_box=summary_panel)
    _check_panel_label_inside(label_box_id="panel_label_A", panel_box=metric_panel)
    _check_panel_label_inside(label_box_id="panel_label_B", panel_box=summary_panel)

    x_axis_title_box = layout_box_by_id.get("x_axis_title_A")
    if x_axis_title_box is None:
        issues.append(
            _issue(
                rule_id="x_axis_title_missing",
                message="center transportability governance summary requires the metric x-axis title",
                target="subplot_x_axis_title",
                expected="x_axis_title_A",
            )
        )
    else:
        aligned_with_metric_panel = (
            metric_panel.x0 <= (x_axis_title_box.x0 + x_axis_title_box.x1) / 2.0 <= metric_panel.x1
            and x_axis_title_box.y0 >= metric_panel.y0 - 0.10
            and x_axis_title_box.y1 <= metric_panel.y1 + 0.02
        )
        if not aligned_with_metric_panel:
            issues.append(
                _issue(
                    rule_id="x_axis_title_out_of_alignment",
                    message="metric x-axis title must stay aligned with the metric panel",
                    target="subplot_x_axis_title",
                    box_refs=(x_axis_title_box.box_id, metric_panel.box_id),
                )
            )

    metric_panel_metrics = metrics.get("metric_panel")
    summary_panel_metrics = metrics.get("summary_panel")
    if not isinstance(metric_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="metric_panel_metrics_missing",
                message="metric panel metrics must be present",
                target="metrics.metric_panel",
            )
        )
        return issues
    if not isinstance(summary_panel_metrics, dict):
        issues.append(
            _issue(
                rule_id="summary_panel_metrics_missing",
                message="summary panel metrics must be present",
                target="metrics.summary_panel",
            )
        )
        return issues

    reference_line_box = guide_box_by_id.get(str(metric_panel_metrics.get("reference_line_box_id") or "").strip())
    if reference_line_box is None:
        issues.append(
            _issue(
                rule_id="reference_line_missing",
                message="center transportability governance summary requires one reference line inside the metric panel",
                target="metrics.metric_panel.reference_line_box_id",
                box_refs=(metric_panel.box_id,),
            )
        )
    elif not _box_within_box(reference_line_box, metric_panel):
        issues.append(
            _issue(
                rule_id="reference_line_outside_metric_panel",
                message="reference line must stay within the metric panel",
                target=f"guide_boxes.{reference_line_box.box_id}",
                box_refs=(reference_line_box.box_id, metric_panel.box_id),
            )
        )

    metric_family = _require_non_empty_text(metrics.get("metric_family"), label="layout_sidecar.metrics.metric_family")
    supported_metric_families = {"discrimination", "calibration_ratio", "effect_estimate", "utility_delta"}
    if metric_family not in supported_metric_families:
        issues.append(
            _issue(
                rule_id="metric_family_invalid",
                message="metric_family must be one of discrimination, calibration_ratio, effect_estimate, utility_delta",
                target="metrics.metric_family",
                observed=metric_family,
            )
        )

    metric_reference_value = _require_numeric(
        metrics.get("metric_reference_value"),
        label="layout_sidecar.metrics.metric_reference_value",
    )
    if not math.isfinite(metric_reference_value):
        issues.append(
            _issue(
                rule_id="metric_reference_value_invalid",
                message="metric_reference_value must be finite",
                target="metrics.metric_reference_value",
                observed=metric_reference_value,
            )
        )
    batch_shift_threshold = _require_numeric(
        metrics.get("batch_shift_threshold"),
        label="layout_sidecar.metrics.batch_shift_threshold",
    )
    if not math.isfinite(batch_shift_threshold) or batch_shift_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="batch_shift_threshold_invalid",
                message="batch_shift_threshold must be positive and finite",
                target="metrics.batch_shift_threshold",
                observed=batch_shift_threshold,
            )
        )
    slope_acceptance_lower = _require_numeric(
        metrics.get("slope_acceptance_lower"),
        label="layout_sidecar.metrics.slope_acceptance_lower",
    )
    slope_acceptance_upper = _require_numeric(
        metrics.get("slope_acceptance_upper"),
        label="layout_sidecar.metrics.slope_acceptance_upper",
    )
    if (
        not math.isfinite(slope_acceptance_lower)
        or not math.isfinite(slope_acceptance_upper)
        or slope_acceptance_lower <= 0.0
        or slope_acceptance_upper <= 0.0
        or slope_acceptance_lower >= slope_acceptance_upper
    ):
        issues.append(
            _issue(
                rule_id="slope_acceptance_band_invalid",
                message="slope acceptance band must be positive, finite, and ordered",
                target="metrics.slope_acceptance_lower",
                observed={"lower": slope_acceptance_lower, "upper": slope_acceptance_upper},
            )
        )
    oe_ratio_acceptance_lower = _require_numeric(
        metrics.get("oe_ratio_acceptance_lower"),
        label="layout_sidecar.metrics.oe_ratio_acceptance_lower",
    )
    oe_ratio_acceptance_upper = _require_numeric(
        metrics.get("oe_ratio_acceptance_upper"),
        label="layout_sidecar.metrics.oe_ratio_acceptance_upper",
    )
    if (
        not math.isfinite(oe_ratio_acceptance_lower)
        or not math.isfinite(oe_ratio_acceptance_upper)
        or oe_ratio_acceptance_lower <= 0.0
        or oe_ratio_acceptance_upper <= 0.0
        or oe_ratio_acceptance_lower >= oe_ratio_acceptance_upper
    ):
        issues.append(
            _issue(
                rule_id="oe_ratio_acceptance_band_invalid",
                message="oe_ratio acceptance band must be positive, finite, and ordered",
                target="metrics.oe_ratio_acceptance_lower",
                observed={"lower": oe_ratio_acceptance_lower, "upper": oe_ratio_acceptance_upper},
            )
        )

    centers = metrics.get("centers")
    if not isinstance(centers, list) or not centers:
        issues.append(
            _issue(
                rule_id="centers_missing",
                message="center transportability governance summary requires non-empty center metrics",
                target="metrics.centers",
            )
        )
        return issues

    supported_verdicts = {
        "stable",
        "context_dependent",
        "recalibration_required",
        "insufficient_support",
        "unstable",
    }
    seen_center_ids: set[str] = set()
    seen_center_labels: set[str] = set()
    for index, center in enumerate(centers):
        if not isinstance(center, dict):
            raise ValueError(f"layout_sidecar.metrics.centers[{index}] must be an object")
        center_id = _require_non_empty_text(center.get("center_id"), label=f"layout_sidecar.metrics.centers[{index}].center_id")
        if center_id in seen_center_ids:
            issues.append(
                _issue(
                    rule_id="center_id_duplicate",
                    message="center ids must be unique",
                    target=f"metrics.centers[{index}].center_id",
                    observed=center_id,
                )
            )
        seen_center_ids.add(center_id)
        center_label = _require_non_empty_text(center.get("center_label"), label=f"layout_sidecar.metrics.centers[{index}].center_label")
        if center_label in seen_center_labels:
            issues.append(
                _issue(
                    rule_id="center_label_duplicate",
                    message="center labels must be unique",
                    target=f"metrics.centers[{index}].center_label",
                    observed=center_label,
                )
            )
        seen_center_labels.add(center_label)
        _require_non_empty_text(center.get("cohort_role"), label=f"layout_sidecar.metrics.centers[{index}].cohort_role")
        support_count = _require_numeric(center.get("support_count"), label=f"layout_sidecar.metrics.centers[{index}].support_count")
        event_count = _require_numeric(center.get("event_count"), label=f"layout_sidecar.metrics.centers[{index}].event_count")
        if not float(support_count).is_integer() or support_count <= 0:
            issues.append(
                _issue(
                    rule_id="center_support_count_invalid",
                    message="center support counts must be positive integers",
                    target=f"metrics.centers[{index}].support_count",
                    observed=support_count,
                )
            )
        if not float(event_count).is_integer() or event_count < 0:
            issues.append(
                _issue(
                    rule_id="center_event_count_invalid",
                    message="center event counts must be non-negative integers",
                    target=f"metrics.centers[{index}].event_count",
                    observed=event_count,
                )
            )
        elif event_count > support_count:
            issues.append(
                _issue(
                    rule_id="center_event_count_exceeds_support",
                    message="center event counts must not exceed support counts",
                    target=f"metrics.centers[{index}].event_count",
                    observed={"event_count": event_count, "support_count": support_count},
                )
            )
        metric_estimate = _require_numeric(center.get("metric_estimate"), label=f"layout_sidecar.metrics.centers[{index}].metric_estimate")
        metric_lower = _require_numeric(center.get("metric_lower"), label=f"layout_sidecar.metrics.centers[{index}].metric_lower")
        metric_upper = _require_numeric(center.get("metric_upper"), label=f"layout_sidecar.metrics.centers[{index}].metric_upper")
        if not all(math.isfinite(value) for value in (metric_estimate, metric_lower, metric_upper)):
            issues.append(
                _issue(
                    rule_id="center_metric_value_invalid",
                    message="center metric values must be finite",
                    target=f"metrics.centers[{index}]",
                )
            )
        elif not (metric_lower <= metric_estimate <= metric_upper):
            issues.append(
                _issue(
                    rule_id="center_metric_interval_invalid",
                    message="center metric intervals must satisfy lower <= estimate <= upper",
                    target=f"metrics.centers[{index}]",
                    observed={"lower": metric_lower, "estimate": metric_estimate, "upper": metric_upper},
                )
            )
        max_shift = _require_numeric(center.get("max_shift"), label=f"layout_sidecar.metrics.centers[{index}].max_shift")
        if not math.isfinite(max_shift) or max_shift < 0.0 or max_shift > 1.0:
            issues.append(
                _issue(
                    rule_id="center_max_shift_invalid",
                    message="center max_shift must stay within [0, 1]",
                    target=f"metrics.centers[{index}].max_shift",
                    observed=max_shift,
                )
            )
        slope = _require_numeric(center.get("slope"), label=f"layout_sidecar.metrics.centers[{index}].slope")
        if not math.isfinite(slope) or slope <= 0.0:
            issues.append(
                _issue(
                    rule_id="center_slope_invalid",
                    message="center slopes must be positive and finite",
                    target=f"metrics.centers[{index}].slope",
                    observed=slope,
                )
            )
        oe_ratio = _require_numeric(center.get("oe_ratio"), label=f"layout_sidecar.metrics.centers[{index}].oe_ratio")
        if not math.isfinite(oe_ratio) or oe_ratio <= 0.0:
            issues.append(
                _issue(
                    rule_id="center_oe_ratio_invalid",
                    message="center oe_ratio values must be positive and finite",
                    target=f"metrics.centers[{index}].oe_ratio",
                    observed=oe_ratio,
                )
            )
        verdict = _require_non_empty_text(center.get("verdict"), label=f"layout_sidecar.metrics.centers[{index}].verdict")
        if verdict not in supported_verdicts:
            issues.append(
                _issue(
                    rule_id="center_verdict_invalid",
                    message="center verdicts must be drawn from the audited vocabulary",
                    target=f"metrics.centers[{index}].verdict",
                    observed=verdict,
                )
            )
        _require_non_empty_text(center.get("action"), label=f"layout_sidecar.metrics.centers[{index}].action")
        detail_value = center.get("detail")
        if detail_value is not None:
            _require_non_empty_text(detail_value, label=f"layout_sidecar.metrics.centers[{index}].detail")

        label_box = layout_box_by_id.get(str(center.get("label_box_id") or "").strip())
        metric_box = layout_box_by_id.get(str(center.get("metric_box_id") or "").strip())
        interval_box = layout_box_by_id.get(str(center.get("interval_box_id") or "").strip())
        verdict_box = layout_box_by_id.get(str(center.get("verdict_box_id") or "").strip())
        metrics_box = layout_box_by_id.get(str(center.get("metrics_box_id") or "").strip())
        action_box = layout_box_by_id.get(str(center.get("action_box_id") or "").strip())
        detail_box = layout_box_by_id.get(str(center.get("detail_box_id") or "").strip()) if center.get("detail_box_id") else None

        if label_box is None:
            issues.append(
                _issue(
                    rule_id="row_label_missing",
                    message="each center must reference an existing row_label box",
                    target=f"metrics.centers[{index}].label_box_id",
                )
            )
        if metric_box is None:
            issues.append(
                _issue(
                    rule_id="metric_box_missing",
                    message="each center must reference an existing metric marker box",
                    target=f"metrics.centers[{index}].metric_box_id",
                )
            )
        elif not _box_within_box(metric_box, metric_panel):
            issues.append(
                _issue(
                    rule_id="metric_box_outside_metric_panel",
                    message="metric marker boxes must stay within the metric panel",
                    target="estimate_marker",
                    box_refs=(metric_box.box_id, metric_panel.box_id),
                )
            )
        if interval_box is None:
            issues.append(
                _issue(
                    rule_id="interval_box_missing",
                    message="each center must reference an existing ci_segment box",
                    target=f"metrics.centers[{index}].interval_box_id",
                )
            )
        elif not _box_within_box(interval_box, metric_panel):
            issues.append(
                _issue(
                    rule_id="interval_box_outside_metric_panel",
                    message="interval boxes must stay within the metric panel",
                    target="ci_segment",
                    box_refs=(interval_box.box_id, metric_panel.box_id),
                )
            )
        if verdict_box is None:
            issues.append(
                _issue(
                    rule_id="verdict_box_missing",
                    message="each center must reference an existing verdict box",
                    target=f"metrics.centers[{index}].verdict_box_id",
                )
            )
        elif not _box_within_box(verdict_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="verdict_box_outside_summary_panel",
                    message="verdict boxes must stay within the summary panel",
                    target="verdict_value",
                    box_refs=(verdict_box.box_id, summary_panel.box_id),
                )
            )
        if metrics_box is None:
            issues.append(
                _issue(
                    rule_id="metrics_box_missing",
                    message="each center must reference an existing summary metrics box",
                    target=f"metrics.centers[{index}].metrics_box_id",
                )
            )
        elif not _box_within_box(metrics_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="metrics_box_outside_summary_panel",
                    message="summary metrics boxes must stay within the summary panel",
                    target="row_metric",
                    box_refs=(metrics_box.box_id, summary_panel.box_id),
                )
            )
        if action_box is None:
            issues.append(
                _issue(
                    rule_id="action_box_missing",
                    message="each center must reference an existing action box",
                    target=f"metrics.centers[{index}].action_box_id",
                )
            )
        elif not _box_within_box(action_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="action_box_outside_summary_panel",
                    message="action boxes must stay within the summary panel",
                    target="row_action",
                    box_refs=(action_box.box_id, summary_panel.box_id),
                )
            )
        if detail_box is not None and not _box_within_box(detail_box, summary_panel):
            issues.append(
                _issue(
                    rule_id="detail_box_outside_summary_panel",
                    message="detail boxes must stay within the summary panel",
                    target="verdict_detail",
                    box_refs=(detail_box.box_id, summary_panel.box_id),
                )
            )

    return issues
