from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _check_boxes_within_device, _check_composite_panel_label_anchors, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _require_numeric

def _check_publication_shap_force_like_summary_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "panel_label",
        "case_label",
        "baseline_label",
        "prediction_label",
        "force_feature_label",
        "baseline_marker",
        "prediction_marker",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type
        in {"title", "panel_title", "subplot_x_axis_title", "panel_label", "case_label", "baseline_label", "prediction_label", "force_feature_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="shap force-like summary qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap force-like summary panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        case_label = str(panel_metric.get("case_label") or "").strip()
        baseline_value = _require_numeric(
            panel_metric.get("baseline_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric(
            panel_metric.get("predicted_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].predicted_value",
        )
        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip()
        baseline_marker_box_id = str(panel_metric.get("baseline_marker_box_id") or "").strip()
        prediction_marker_box_id = str(panel_metric.get("prediction_marker_box_id") or "").strip()
        if not panel_id or not panel_label or not title or not case_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="shap force-like summary metrics must declare panel metadata and case labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        if not panel_box_id:
            panel_box_id = f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="shap force-like summary metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        if not baseline_marker_box_id:
            baseline_marker_box_id = f"baseline_marker_{panel_label}"
        if not prediction_marker_box_id:
            prediction_marker_box_id = f"prediction_marker_{panel_label}"

        baseline_marker = guide_box_by_id.get(baseline_marker_box_id)
        prediction_marker = guide_box_by_id.get(prediction_marker_box_id)
        if baseline_marker is None:
            issues.append(
                _issue(
                    rule_id="baseline_marker_missing",
                    message="shap force-like summary requires one baseline marker per panel",
                    target=f"metrics.panels[{panel_index}].baseline_marker_box_id",
                    observed={"baseline_marker_box_id": baseline_marker_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(baseline_marker, panel_box):
            issues.append(
                _issue(
                    rule_id="baseline_marker_outside_panel",
                    message="baseline marker must stay within the panel region",
                    target=f"guide_boxes.{baseline_marker.box_id}",
                    box_refs=(baseline_marker.box_id, panel_box.box_id),
                )
            )

        if prediction_marker is None:
            issues.append(
                _issue(
                    rule_id="prediction_marker_missing",
                    message="shap force-like summary requires one prediction marker per panel",
                    target=f"metrics.panels[{panel_index}].prediction_marker_box_id",
                    observed={"prediction_marker_box_id": prediction_marker_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(prediction_marker, panel_box):
            issues.append(
                _issue(
                    rule_id="prediction_marker_outside_panel",
                    message="prediction marker must stay within the panel region",
                    target=f"guide_boxes.{prediction_marker.box_id}",
                    box_refs=(prediction_marker.box_id, panel_box.box_id),
                )
            )

        if baseline_marker is not None and prediction_marker is not None:
            baseline_mid_x = (baseline_marker.x0 + baseline_marker.x1) / 2.0
            prediction_mid_x = (prediction_marker.x0 + prediction_marker.x1) / 2.0
            if predicted_value > baseline_value and prediction_mid_x <= baseline_mid_x:
                issues.append(
                    _issue(
                        rule_id="prediction_marker_direction_mismatch",
                        message="prediction marker must move right of baseline for net-positive force-like cases",
                        target=f"metrics.panels[{panel_index}].predicted_value",
                        box_refs=(prediction_marker.box_id, baseline_marker.box_id, panel_box.box_id),
                    )
                )
            if predicted_value < baseline_value and prediction_mid_x >= baseline_mid_x:
                issues.append(
                    _issue(
                        rule_id="prediction_marker_direction_mismatch",
                        message="prediction marker must move left of baseline for net-negative force-like cases",
                        target=f"metrics.panels[{panel_index}].predicted_value",
                        box_refs=(prediction_marker.box_id, baseline_marker.box_id, panel_box.box_id),
                    )
                )

        contributions = panel_metric.get("contributions")
        if not isinstance(contributions, list) or not contributions:
            issues.append(
                _issue(
                    rule_id="contributions_missing",
                    message="shap force-like summary panel metrics must contain ordered contributions",
                    target=f"metrics.panels[{panel_index}].contributions",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        for contribution_index, contribution in enumerate(contributions):
            if not isinstance(contribution, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            feature = str(contribution.get("feature") or "").strip()
            direction = str(contribution.get("direction") or "").strip()
            segment_box_id = str(contribution.get("segment_box_id") or "").strip()
            label_box_id = str(contribution.get("label_box_id") or "").strip()
            shap_value = _require_numeric(
                contribution.get("shap_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].shap_value",
            )
            start_value = _require_numeric(
                contribution.get("start_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].start_value",
            )
            end_value = _require_numeric(
                contribution.get("end_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].end_value",
            )
            if not feature or not direction or not segment_box_id or not label_box_id:
                issues.append(
                    _issue(
                        rule_id="contribution_metric_missing",
                        message="each force-like contribution must declare feature, direction, segment_box_id, and label_box_id",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
                continue
            segment_box = layout_box_by_id.get(segment_box_id)
            if segment_box is None:
                issues.append(
                    _issue(
                        rule_id="contribution_segment_missing",
                        message="each force-like contribution must reference an existing segment box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        observed={"segment_box_id": segment_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif not _box_within_box(segment_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="contribution_segment_outside_panel",
                        message="force-like contribution segment must stay within the panel region",
                        target=f"layout_boxes.{segment_box.box_id}",
                        box_refs=(segment_box.box_id, panel_box.box_id),
                    )
                )
            label_box = layout_box_by_id.get(label_box_id)
            if label_box is None:
                issues.append(
                    _issue(
                        rule_id="force_label_missing",
                        message="each force-like contribution must reference an existing feature label box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                        observed={"label_box_id": label_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif not _box_within_box(label_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="force_label_outside_panel",
                        message="force-like feature labels must stay within the panel region",
                        target=f"layout_boxes.{label_box.box_id}",
                        box_refs=(label_box.box_id, panel_box.box_id),
                    )
                )

            if direction == "positive":
                if shap_value <= 0 or end_value <= start_value:
                    issues.append(
                        _issue(
                            rule_id="contribution_direction_mismatch",
                            message="positive force-like contribution must increase from start_value to end_value",
                            target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                            observed={"start_value": start_value, "end_value": end_value, "shap_value": shap_value},
                            box_refs=(panel_box.box_id,),
                        )
                    )
                if baseline_marker is not None and segment_box is not None:
                    if segment_box.x0 < baseline_marker.x0 - 1e-6:
                        issues.append(
                            _issue(
                                rule_id="positive_segment_crosses_baseline",
                                message="positive force-like segment must stay to the right of baseline",
                                target=f"layout_boxes.{segment_box.box_id}",
                                box_refs=(segment_box.box_id, baseline_marker.box_id, panel_box.box_id),
                        )
                    )
            elif direction == "negative":
                if shap_value >= 0 or end_value >= start_value:
                    issues.append(
                        _issue(
                            rule_id="contribution_direction_mismatch",
                            message="negative force-like contribution must decrease from start_value to end_value",
                            target=f"metrics.panels[{panel_index}].contributions[{contribution_index}]",
                            observed={"start_value": start_value, "end_value": end_value, "shap_value": shap_value},
                            box_refs=(panel_box.box_id,),
                        )
                    )
                if baseline_marker is not None and segment_box is not None:
                    if segment_box.x1 > baseline_marker.x1 + 1e-6:
                        issues.append(
                            _issue(
                                rule_id="negative_segment_crosses_baseline",
                                message="negative force-like segment must stay to the left of baseline",
                                target=f"layout_boxes.{segment_box.box_id}",
                                box_refs=(segment_box.box_id, baseline_marker.box_id, panel_box.box_id),
                            )
                        )
            else:
                issues.append(
                    _issue(
                        rule_id="contribution_direction_invalid",
                        message="force-like contribution direction must be positive or negative",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].direction",
                        observed={"direction": direction},
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
