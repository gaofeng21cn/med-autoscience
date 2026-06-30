from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_of_type,
    _check_boxes_within_device,
    _check_composite_panel_label_anchors,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _issue,
    _layout_override_flag,
    _require_numeric,
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
        "metric_marker",
        "calibration_governance_metric",
        "legend",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    metric_panel = panel_by_id.get("panel_left")
    governance_panel = panel_by_id.get("panel_right")
    if metric_panel is None or governance_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="center transportability governance qc requires panel_left and panel_right",
                target="panel_boxes",
            )
        )
        return issues

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_left",
                "panel_label_B": "panel_right",
            },
        )
    )

    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    centers = metrics.get("centers")
    if not isinstance(centers, list) or len(centers) < 2:
        issues.append(
            _issue(
                rule_id="centers_missing",
                message="center transportability governance qc requires at least two center metrics",
                target="metrics.centers",
            )
        )
        return issues

    metric_reference_value = metrics.get("metric_reference_value")
    if metric_reference_value is None:
        issues.append(
            _issue(
                rule_id="metric_reference_value_missing",
                message="center transportability governance qc requires a metric reference value",
                target="metrics.metric_reference_value",
            )
        )
    else:
        _require_numeric(metric_reference_value, label="layout_sidecar.metrics.metric_reference_value")

    for range_key in ("slope_acceptance", "oe_ratio_acceptance"):
        range_payload = metrics.get(range_key)
        if not isinstance(range_payload, dict):
            issues.append(
                _issue(
                    rule_id=f"{range_key}_missing",
                    message=f"center transportability governance qc requires {range_key} lower/upper bounds",
                    target=f"metrics.{range_key}",
                )
            )
            continue
        lower = _require_numeric(range_payload.get("lower"), label=f"layout_sidecar.metrics.{range_key}.lower")
        upper = _require_numeric(range_payload.get("upper"), label=f"layout_sidecar.metrics.{range_key}.upper")
        if lower >= upper:
            issues.append(
                _issue(
                    rule_id=f"{range_key}_invalid",
                    message=f"{range_key} lower bound must be less than the upper bound",
                    target=f"metrics.{range_key}",
                    observed={"lower": lower, "upper": upper},
                )
            )

    marker_boxes = _boxes_of_type(sidecar.layout_boxes, "metric_marker")
    if len(marker_boxes) < len(centers):
        issues.append(
            _issue(
                rule_id="metric_marker_count_incomplete",
                message="center transportability governance qc requires one metric marker per center",
                target="layout_boxes.metric_marker",
                observed={"metric_marker_count": len(marker_boxes), "center_count": len(centers)},
            )
        )
    for marker_box in marker_boxes:
        if _box_within_box(marker_box, metric_panel):
            continue
        issues.append(
            _issue(
                rule_id="metric_marker_outside_panel",
                message="center metric markers must stay within the metric panel",
                target=f"layout_boxes.{marker_box.box_id}",
                box_refs=(marker_box.box_id, metric_panel.box_id),
            )
        )

    governance_markers = _boxes_of_type(sidecar.layout_boxes, "calibration_governance_metric")
    expected_governance_markers = len(centers) * 2
    if len(governance_markers) < expected_governance_markers:
        issues.append(
            _issue(
                rule_id="calibration_governance_metric_count_incomplete",
                message="center transportability governance qc requires slope and O/E markers for each center",
                target="layout_boxes.calibration_governance_metric",
                observed={
                    "calibration_governance_metric_count": len(governance_markers),
                    "expected_count": expected_governance_markers,
                },
            )
        )
    for marker_box in governance_markers:
        if _box_within_box(marker_box, governance_panel):
            continue
        issues.append(
            _issue(
                rule_id="calibration_governance_metric_outside_panel",
                message="calibration governance markers must stay within the governance panel",
                target=f"layout_boxes.{marker_box.box_id}",
                box_refs=(marker_box.box_id, governance_panel.box_id),
            )
        )

    for index, center in enumerate(centers):
        if not isinstance(center, dict):
            issues.append(
                _issue(
                    rule_id="center_metric_invalid",
                    message="center metrics must be objects",
                    target=f"metrics.centers[{index}]",
                )
            )
            continue
        for metric_key in ("slope", "oe_ratio"):
            try:
                _require_numeric(center.get(metric_key), label=f"layout_sidecar.metrics.centers[{index}].{metric_key}")
            except ValueError:
                issues.append(
                    _issue(
                        rule_id=f"{metric_key}_missing",
                        message=f"center transportability governance qc requires numeric {metric_key} for every center",
                        target=f"metrics.centers[{index}].{metric_key}",
                    )
                )

    return issues


__all__ = ["_check_publication_center_transportability_governance_summary_panel"]
