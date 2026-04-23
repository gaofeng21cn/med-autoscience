from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _boxes_overlap, _check_boxes_within_device, _check_required_box_types, _issue, _layout_override_flag, _require_numeric, math

def _check_publication_shap_multigroup_decision_path_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = (
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "feature_label",
        "decision_path_line",
        "prediction_label",
        "baseline_reference_line",
        "prediction_marker",
    )
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types = ("title",) + required_box_types
    issues.extend(_check_required_box_types(all_boxes, required_box_types=required_box_types))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    if len(panel_boxes) != 1:
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap multigroup decision path panel requires exactly one panel box",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"panel_boxes": 1},
            )
        )
    panel_box = panel_boxes[0] if panel_boxes else None

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}

    legend_box = layout_box_by_id.get("legend_box")
    if legend_box is None:
        issues.append(
            _issue(
                rule_id="legend_box_missing",
                message="shap multigroup decision path panel requires an explicit legend box",
                target="legend_box",
                expected="present",
            )
        )
    elif panel_box is not None and _boxes_overlap(legend_box, panel_box):
        issues.append(
            _issue(
                rule_id="legend_box_overlaps_panel",
                message="shap multigroup decision path legend must stay outside the main panel region",
                target="legend_box",
                box_refs=(legend_box.box_id, panel_box.box_id),
            )
        )

    legend_title_box = layout_box_by_id.get("legend_title")
    if legend_title_box is None:
        issues.append(
            _issue(
                rule_id="legend_title_missing",
                message="shap multigroup decision path panel requires an explicit legend title",
                target="legend_title",
                expected="present",
            )
        )

    metrics_panel_box_id = str(sidecar.metrics.get("panel_box_id") or "").strip()
    if panel_box is not None and metrics_panel_box_id and metrics_panel_box_id != panel_box.box_id:
        issues.append(
            _issue(
                rule_id="panel_box_mismatch",
                message="shap multigroup decision path metrics must reference the primary panel box",
                target="metrics.panel_box_id",
                observed=metrics_panel_box_id,
                expected=panel_box.box_id,
            )
        )

    baseline_line_box_id = str(sidecar.metrics.get("baseline_line_box_id") or "").strip()
    baseline_line = guide_box_by_id.get(baseline_line_box_id) if baseline_line_box_id else None
    if baseline_line is None:
        issues.append(
            _issue(
                rule_id="baseline_reference_line_missing",
                message="shap multigroup decision path panel requires a baseline reference line",
                target="metrics.baseline_line_box_id",
                observed=baseline_line_box_id or None,
                expected="present",
                box_refs=((panel_box.box_id,) if panel_box is not None else ()),
            )
        )
    elif panel_box is not None and not _box_within_box(baseline_line, panel_box):
        issues.append(
            _issue(
                rule_id="baseline_reference_line_outside_panel",
                message="shap multigroup decision path baseline reference line must stay within the panel region",
                target=f"guide_boxes.{baseline_line.box_id}",
                box_refs=(baseline_line.box_id, panel_box.box_id),
            )
        )

    baseline_value = _require_numeric(sidecar.metrics.get("baseline_value"), label="layout_sidecar.metrics.baseline_value")
    feature_order_payload = sidecar.metrics.get("feature_order")
    if not isinstance(feature_order_payload, list) or not feature_order_payload:
        issues.append(
            _issue(
                rule_id="feature_order_missing",
                message="shap multigroup decision path metrics require a non-empty shared feature order",
                target="metrics.feature_order",
            )
        )
        feature_order: tuple[str, ...] = ()
    else:
        feature_order = tuple(str(item or "").strip() for item in feature_order_payload)
        if any(not item for item in feature_order):
            issues.append(
                _issue(
                    rule_id="feature_order_invalid",
                    message="shap multigroup decision path feature_order entries must be non-empty",
                    target="metrics.feature_order",
                )
            )

    feature_label_box_ids_payload = sidecar.metrics.get("feature_label_box_ids")
    if not isinstance(feature_label_box_ids_payload, list) or len(feature_label_box_ids_payload) != len(feature_order):
        issues.append(
            _issue(
                rule_id="feature_label_count_mismatch",
                message="shap multigroup decision path feature label boxes must match the shared feature order length",
                target="metrics.feature_label_box_ids",
                observed={"feature_label_box_ids": len(feature_label_box_ids_payload or []) if isinstance(feature_label_box_ids_payload, list) else None},
                expected={"feature_order": len(feature_order)},
            )
        )
        feature_label_box_ids: tuple[str, ...] = ()
    else:
        feature_label_box_ids = tuple(str(item or "").strip() for item in feature_label_box_ids_payload)
        for feature_label_box_id in feature_label_box_ids:
            box = layout_box_by_id.get(feature_label_box_id)
            if box is None:
                issues.append(
                    _issue(
                        rule_id="feature_label_missing",
                        message="shap multigroup decision path metrics must reference existing feature label boxes",
                        target="metrics.feature_label_box_ids",
                        observed=feature_label_box_id,
                    )
                )
                continue
            if panel_box is not None and _boxes_overlap(box, panel_box):
                issues.append(
                    _issue(
                        rule_id="feature_label_panel_overlap",
                        message="shap multigroup decision path feature labels must stay outside the panel region",
                        target=f"layout_boxes.{box.box_id}",
                        box_refs=(box.box_id, panel_box.box_id),
                    )
                )

    groups_payload = sidecar.metrics.get("groups")
    if not isinstance(groups_payload, list) or len(groups_payload) != 3:
        issues.append(
            _issue(
                rule_id="group_count_invalid",
                message="shap multigroup decision path metrics require exactly three groups",
                target="metrics.groups",
                observed={"groups": len(groups_payload) if isinstance(groups_payload, list) else None},
                expected={"groups": 3},
            )
        )
        return issues

    seen_group_ids: set[str] = set()
    seen_group_labels: set[str] = set()
    for group_index, group_metric in enumerate(groups_payload):
        if not isinstance(group_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.groups[{group_index}] must be an object")
        group_id = str(group_metric.get("group_id") or "").strip()
        group_label = str(group_metric.get("group_label") or "").strip()
        predicted_value = _require_numeric(
            group_metric.get("predicted_value"),
            label=f"layout_sidecar.metrics.groups[{group_index}].predicted_value",
        )
        if not group_id:
            issues.append(
                _issue(
                    rule_id="group_id_missing",
                    message="shap multigroup decision path groups must declare a non-empty group_id",
                    target=f"metrics.groups[{group_index}].group_id",
                )
            )
        elif group_id in seen_group_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_group_id",
                    message="shap multigroup decision path group_ids must be unique",
                    target=f"metrics.groups[{group_index}].group_id",
                    observed=group_id,
                )
            )
        seen_group_ids.add(group_id)
        if not group_label:
            issues.append(
                _issue(
                    rule_id="group_label_missing",
                    message="shap multigroup decision path groups must declare a non-empty group_label",
                    target=f"metrics.groups[{group_index}].group_label",
                )
            )
        elif group_label in seen_group_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_group_label",
                    message="shap multigroup decision path group_labels must be unique",
                    target=f"metrics.groups[{group_index}].group_label",
                    observed=group_label,
                )
            )
        seen_group_labels.add(group_label)

        line_box_id = str(group_metric.get("line_box_id") or "").strip()
        line_box = layout_box_by_id.get(line_box_id)
        if line_box is None:
            issues.append(
                _issue(
                    rule_id="decision_path_line_missing",
                    message="shap multigroup decision path groups must reference an existing decision-path line box",
                    target=f"metrics.groups[{group_index}].line_box_id",
                    observed=line_box_id or None,
                    box_refs=((panel_box.box_id,) if panel_box is not None else ()),
                )
            )
        elif panel_box is not None and not _box_within_box(line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="decision_path_line_outside_panel",
                    message="shap multigroup decision path lines must stay within the panel region",
                    target=f"layout_boxes.{line_box.box_id}",
                    box_refs=(line_box.box_id, panel_box.box_id),
                )
            )

        prediction_marker_box_id = str(group_metric.get("prediction_marker_box_id") or "").strip()
        prediction_marker = guide_box_by_id.get(prediction_marker_box_id)
        if prediction_marker is None:
            issues.append(
                _issue(
                    rule_id="prediction_marker_missing",
                    message="shap multigroup decision path groups must reference an existing prediction marker box",
                    target=f"metrics.groups[{group_index}].prediction_marker_box_id",
                    observed=prediction_marker_box_id or None,
                    box_refs=((panel_box.box_id,) if panel_box is not None else ()),
                )
            )
        elif panel_box is not None and not _box_within_box(prediction_marker, panel_box):
            issues.append(
                _issue(
                    rule_id="prediction_marker_outside_panel",
                    message="shap multigroup decision path prediction markers must stay within the panel region",
                    target=f"guide_boxes.{prediction_marker.box_id}",
                    box_refs=(prediction_marker.box_id, panel_box.box_id),
                )
            )

        prediction_label_box_id = str(group_metric.get("prediction_label_box_id") or "").strip()
        prediction_label_box = layout_box_by_id.get(prediction_label_box_id)
        if prediction_label_box is None:
            issues.append(
                _issue(
                    rule_id="prediction_label_missing",
                    message="shap multigroup decision path groups must reference an existing prediction label box",
                    target=f"metrics.groups[{group_index}].prediction_label_box_id",
                    observed=prediction_label_box_id or None,
                )
            )

        contributions_payload = group_metric.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            issues.append(
                _issue(
                    rule_id="contributions_missing",
                    message="shap multigroup decision path groups require non-empty contributions",
                    target=f"metrics.groups[{group_index}].contributions",
                )
            )
            continue

        previous_rank = 0
        contribution_sum = 0.0
        group_feature_order: list[str] = []
        for contribution_index, contribution_metric in enumerate(contributions_payload):
            if not isinstance(contribution_metric, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}] must be an object"
                )
            rank = int(
                _require_numeric(
                    contribution_metric.get("rank"),
                    label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].rank",
                )
            )
            if rank <= previous_rank:
                issues.append(
                    _issue(
                        rule_id="contribution_rank_invalid",
                        message="shap multigroup decision path contribution ranks must be strictly increasing",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}].rank",
                    )
                )
            previous_rank = rank
            feature = str(contribution_metric.get("feature") or "").strip()
            if not feature:
                issues.append(
                    _issue(
                        rule_id="contribution_feature_missing",
                        message="shap multigroup decision path contribution features must be non-empty",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}].feature",
                    )
                )
            group_feature_order.append(feature)
            shap_value = _require_numeric(
                contribution_metric.get("shap_value"),
                label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].shap_value",
            )
            if math.isclose(shap_value, 0.0, abs_tol=1e-12):
                issues.append(
                    _issue(
                        rule_id="contribution_value_zero",
                        message="shap multigroup decision path contributions must be non-zero",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}].shap_value",
                    )
                )
            start_value = _require_numeric(
                contribution_metric.get("start_value"),
                label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].start_value",
            )
            end_value = _require_numeric(
                contribution_metric.get("end_value"),
                label=f"layout_sidecar.metrics.groups[{group_index}].contributions[{contribution_index}].end_value",
            )
            if not math.isclose(end_value, start_value + shap_value, rel_tol=1e-9, abs_tol=1e-9):
                issues.append(
                    _issue(
                        rule_id="contribution_path_invalid",
                        message="shap multigroup decision path contribution end_value must equal start_value plus shap_value",
                        target=f"metrics.groups[{group_index}].contributions[{contribution_index}]",
                        observed={"start_value": start_value, "end_value": end_value, "shap_value": shap_value},
                    )
                )
            contribution_sum += shap_value

        if tuple(group_feature_order) != tuple(feature_order):
            issues.append(
                _issue(
                    rule_id="group_feature_order_mismatch",
                    message="all shap multigroup decision path groups must keep the shared feature order",
                    target=f"metrics.groups[{group_index}].contributions",
                    observed={"feature_order": group_feature_order},
                    expected={"feature_order": list(feature_order)},
                )
            )
        if not math.isclose(predicted_value, baseline_value + contribution_sum, rel_tol=1e-9, abs_tol=1e-9):
            issues.append(
                _issue(
                    rule_id="group_prediction_value_mismatch",
                    message="shap multigroup decision path predicted_value must equal baseline_value plus contribution sum",
                    target=f"metrics.groups[{group_index}].predicted_value",
                    observed={"baseline_value": baseline_value, "predicted_value": predicted_value, "contribution_sum": contribution_sum},
                )
            )

    return issues
