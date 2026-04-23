from __future__ import annotations

from .shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _check_audit_panel_collection_metrics, _check_boxes_within_device, _check_composite_panel_label_anchors, _check_legend_panel_overlap, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _panel_label_token, _point_within_box, _require_numeric, math

def _check_publication_model_complexity_audit(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["metric_marker", "audit_bar"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "subplot_title", "subplot_x_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    metric_panels_issues, total_metric_rows, metric_reference_count = _check_audit_panel_collection_metrics(
        sidecar.metrics.get("metric_panels"),
        target="metrics.metric_panels",
    )
    audit_panels_issues, total_audit_rows, audit_reference_count = _check_audit_panel_collection_metrics(
        sidecar.metrics.get("audit_panels"),
        target="metrics.audit_panels",
    )
    issues.extend(metric_panels_issues)
    issues.extend(audit_panels_issues)

    metric_panel_boxes = _boxes_of_type(sidecar.panel_boxes, "metric_panel")
    audit_panel_boxes = _boxes_of_type(sidecar.panel_boxes, "audit_panel")
    metric_panels = sidecar.metrics.get("metric_panels")
    audit_panels = sidecar.metrics.get("audit_panels")
    if isinstance(metric_panels, list) and len(metric_panel_boxes) != len(metric_panels):
        issues.append(
            _issue(
                rule_id="metric_panel_count_mismatch",
                message="metric panel box count must match metric_panels metrics",
                target="panel_boxes",
                observed={"panel_boxes": len(metric_panel_boxes)},
                expected={"metric_panels": len(metric_panels)},
            )
        )
    if isinstance(audit_panels, list) and len(audit_panel_boxes) != len(audit_panels):
        issues.append(
            _issue(
                rule_id="audit_panel_count_mismatch",
                message="audit panel box count must match audit_panels metrics",
                target="panel_boxes",
                observed={"panel_boxes": len(audit_panel_boxes)},
                expected={"audit_panels": len(audit_panels)},
            )
        )

    metric_marker_count = len(_boxes_of_type(sidecar.layout_boxes, "metric_marker"))
    if total_metric_rows and metric_marker_count < total_metric_rows:
        issues.append(
            _issue(
                rule_id="metric_markers_missing",
                message="metric marker boxes must cover every metric row",
                target="layout_boxes",
                observed={"metric_marker_count": metric_marker_count},
                expected={"minimum_metric_rows": total_metric_rows},
            )
        )
    audit_bar_count = len(_boxes_of_type(sidecar.layout_boxes, "audit_bar"))
    if total_audit_rows and audit_bar_count < total_audit_rows:
        issues.append(
            _issue(
                rule_id="audit_bars_missing",
                message="audit bar boxes must cover every audit row",
                target="layout_boxes",
                observed={"audit_bar_count": audit_bar_count},
                expected={"minimum_audit_rows": total_audit_rows},
            )
        )
    reference_line_count = len(_boxes_of_type(sidecar.guide_boxes, "reference_line"))
    if reference_line_count < metric_reference_count + audit_reference_count:
        issues.append(
            _issue(
                rule_id="reference_lines_missing",
                message="reference-line guide boxes must cover every panel with reference_value",
                target="guide_boxes",
                observed={"reference_line_count": reference_line_count},
                expected={"minimum_reference_lines": metric_reference_count + audit_reference_count},
            )
        )

    return issues

def _check_publication_landmark_performance_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    required_box_types = ["metric_marker", "panel_title", "panel_label", "subplot_x_axis_title", "subplot_y_axis_title"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "panel_label", "subplot_x_axis_title", "subplot_y_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    panel_metrics = sidecar.metrics.get("metric_panels")
    metric_panel_issues, total_metric_rows, metric_reference_count = _check_audit_panel_collection_metrics(
        panel_metrics,
        target="metrics.metric_panels",
    )
    issues.extend(metric_panel_issues)
    if not isinstance(panel_metrics, list) or not panel_metrics:
        return issues
    if len(panel_metrics) != 3:
        issues.append(
            _issue(
                rule_id="metric_panel_count_invalid",
                message="landmark performance panel requires exactly three metric panels",
                target="metrics.metric_panels",
                observed={"count": len(panel_metrics)},
                expected={"count": 3},
            )
        )

    metric_panel_boxes = _boxes_of_type(sidecar.panel_boxes, "metric_panel")
    if len(metric_panel_boxes) != len(panel_metrics):
        issues.append(
            _issue(
                rule_id="metric_panel_count_mismatch",
                message="metric panel box count must match metric_panels metrics",
                target="panel_boxes",
                observed={"panel_boxes": len(metric_panel_boxes)},
                expected={"metric_panels": len(panel_metrics)},
            )
        )

    metric_marker_count = len(_boxes_of_type(sidecar.layout_boxes, "metric_marker"))
    if total_metric_rows and metric_marker_count < total_metric_rows:
        issues.append(
            _issue(
                rule_id="metric_markers_missing",
                message="metric marker boxes must cover every landmark summary row",
                target="layout_boxes",
                observed={"metric_marker_count": metric_marker_count},
                expected={"minimum_metric_rows": total_metric_rows},
            )
        )
    reference_line_count = len(_boxes_of_type(sidecar.guide_boxes, "reference_line"))
    if reference_line_count < metric_reference_count:
        issues.append(
            _issue(
                rule_id="reference_lines_missing",
                message="reference-line guide boxes must cover every panel with reference_value",
                target="guide_boxes",
                observed={"reference_line_count": reference_line_count},
                expected={"minimum_reference_lines": metric_reference_count},
            )
        )

    expected_metric_kinds = ("c_index", "brier_score", "calibration_slope")
    seen_metric_kinds: set[str] = set()
    base_row_labels: tuple[str, ...] | None = None
    base_analysis_labels: tuple[str, ...] | None = None
    label_panel_map: dict[str, str] = {}
    for panel_index, panel in enumerate(panel_metrics):
        if not isinstance(panel, dict):
            raise ValueError(f"metrics.metric_panels[{panel_index}] must be an object")
        panel_label = str(panel.get("panel_label") or "").strip()
        if panel_label:
            label_panel_map[f"panel_label_{_panel_label_token(panel_label)}"] = f"panel_{_panel_label_token(panel_label)}"
        metric_kind = str(panel.get("metric_kind") or "").strip()
        if metric_kind not in expected_metric_kinds:
            issues.append(
                _issue(
                    rule_id="metric_kind_invalid",
                    message="landmark performance panel metric_kind must be c_index, brier_score, or calibration_slope",
                    target=f"metrics.metric_panels[{panel_index}].metric_kind",
                    observed=metric_kind,
                )
            )
            continue
        if metric_kind in seen_metric_kinds:
            issues.append(
                _issue(
                    rule_id="metric_kind_duplicate",
                    message="landmark performance panel metric_kind values must be unique",
                    target="metrics.metric_panels",
                    observed=metric_kind,
                )
            )
        seen_metric_kinds.add(metric_kind)
        rows = panel.get("rows")
        if not isinstance(rows, list):
            raise ValueError(f"metrics.metric_panels[{panel_index}].rows must be a list")
        row_labels: list[str] = []
        analysis_labels: list[str] = []
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"metrics.metric_panels[{panel_index}].rows[{row_index}] must be an object")
            row_label = str(row.get("label") or "").strip()
            analysis_window_label = str(row.get("analysis_window_label") or "").strip()
            landmark_months = _require_numeric(
                row.get("landmark_months"),
                label=f"metrics.metric_panels[{panel_index}].rows[{row_index}].landmark_months",
            )
            prediction_months = _require_numeric(
                row.get("prediction_months"),
                label=f"metrics.metric_panels[{panel_index}].rows[{row_index}].prediction_months",
            )
            value = _require_numeric(
                row.get("value"),
                label=f"metrics.metric_panels[{panel_index}].rows[{row_index}].value",
            )
            if not row_label:
                issues.append(
                    _issue(
                        rule_id="row_label_missing",
                        message="landmark performance rows require non-empty labels",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}].label",
                    )
                )
            if not analysis_window_label:
                issues.append(
                    _issue(
                        rule_id="analysis_window_label_missing",
                        message="landmark performance rows require non-empty analysis_window_label",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}].analysis_window_label",
                    )
                )
            if landmark_months <= 0 or prediction_months <= 0:
                issues.append(
                    _issue(
                        rule_id="non_positive_window_months",
                        message="landmark_months and prediction_months must stay positive",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}]",
                    )
                )
            if prediction_months <= landmark_months:
                issues.append(
                    _issue(
                        rule_id="prediction_window_not_forward",
                        message="prediction_months must exceed landmark_months for landmark windows",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}]",
                    )
                )
            if metric_kind in {"c_index", "brier_score"} and (value < 0.0 or value > 1.0):
                issues.append(
                    _issue(
                        rule_id="probability_metric_out_of_range",
                        message="c_index and brier_score values must stay within [0, 1]",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}].value",
                        observed=value,
                    )
                )
            if metric_kind == "calibration_slope" and not math.isfinite(value):
                issues.append(
                    _issue(
                        rule_id="calibration_slope_non_finite",
                        message="calibration slope values must be finite",
                        target=f"metrics.metric_panels[{panel_index}].rows[{row_index}].value",
                    )
                )
            row_labels.append(row_label)
            analysis_labels.append(analysis_window_label)
        row_labels_tuple = tuple(row_labels)
        analysis_labels_tuple = tuple(analysis_labels)
        if base_row_labels is None:
            base_row_labels = row_labels_tuple
            base_analysis_labels = analysis_labels_tuple
        else:
            if row_labels_tuple != base_row_labels:
                issues.append(
                    _issue(
                        rule_id="row_label_sets_mismatch",
                        message="all landmark metric panels must share the same row-label set and ordering",
                        target=f"metrics.metric_panels[{panel_index}].rows",
                    )
                )
            if analysis_labels_tuple != base_analysis_labels:
                issues.append(
                    _issue(
                        rule_id="analysis_window_sets_mismatch",
                        message="all landmark metric panels must share the same analysis-window set and ordering",
                        target=f"metrics.metric_panels[{panel_index}].rows",
                    )
                )

    if seen_metric_kinds and tuple(sorted(seen_metric_kinds)) != tuple(sorted(expected_metric_kinds)):
        issues.append(
            _issue(
                rule_id="metric_kind_set_mismatch",
                message="landmark performance panel must cover c_index, brier_score, and calibration_slope exactly once",
                target="metrics.metric_panels",
                observed=tuple(sorted(seen_metric_kinds)),
                expected=expected_metric_kinds,
            )
        )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.10,
            max_left_offset_ratio=0.12,
        )
    )
    return issues

def _check_publication_time_to_event_threshold_governance_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    required_box_types = ["panel_title", "subplot_x_axis_title", "panel_label", "threshold_card", "legend"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    threshold_cards = _boxes_of_type(sidecar.layout_boxes, "threshold_card")
    issues.extend(
        _check_pairwise_non_overlap(
            threshold_cards,
            rule_id="threshold_card_overlap",
            target="threshold_card",
        )
    )
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    threshold_panel = panel_boxes_by_id.get("threshold_panel")
    calibration_panel = panel_boxes_by_id.get("calibration_panel")
    if threshold_panel is None:
        issues.append(
            _issue(
                rule_id="threshold_panel_missing",
                message="threshold governance panel requires an explicit threshold_panel region",
                target="panel_boxes",
                expected="threshold_panel",
            )
        )
    if calibration_panel is None:
        issues.append(
            _issue(
                rule_id="calibration_panel_missing",
                message="threshold governance panel requires an explicit calibration_panel region",
                target="panel_boxes",
                expected="calibration_panel",
            )
        )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "threshold_panel",
                "panel_label_B": "calibration_panel",
            },
        )
    )

    threshold_summaries = sidecar.metrics.get("threshold_summaries")
    if not isinstance(threshold_summaries, list) or not threshold_summaries:
        issues.append(
            _issue(
                rule_id="threshold_summaries_missing",
                message="threshold governance qc requires non-empty threshold_summaries metrics",
                target="metrics.threshold_summaries",
            )
        )
    else:
        if threshold_cards and len(threshold_cards) != len(threshold_summaries):
            issues.append(
                _issue(
                    rule_id="threshold_card_count_mismatch",
                    message="threshold governance threshold-card count must match metrics.threshold_summaries",
                    target="layout_boxes.threshold_card",
                    observed={"threshold_cards": len(threshold_cards)},
                    expected={"threshold_summaries": len(threshold_summaries)},
                )
            )
        threshold_card_by_id = {box.box_id: box for box in threshold_cards}
        previous_threshold = -1.0
        for index, item in enumerate(threshold_summaries):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.threshold_summaries[{index}] must be an object")
            threshold_label = str(item.get("threshold_label") or "").strip()
            threshold = _require_numeric(
                item.get("threshold"),
                label=f"layout_sidecar.metrics.threshold_summaries[{index}].threshold",
            )
            sensitivity = _require_numeric(
                item.get("sensitivity"),
                label=f"layout_sidecar.metrics.threshold_summaries[{index}].sensitivity",
            )
            specificity = _require_numeric(
                item.get("specificity"),
                label=f"layout_sidecar.metrics.threshold_summaries[{index}].specificity",
            )
            net_benefit = _require_numeric(
                item.get("net_benefit"),
                label=f"layout_sidecar.metrics.threshold_summaries[{index}].net_benefit",
            )
            if not threshold_label:
                issues.append(
                    _issue(
                        rule_id="threshold_label_missing",
                        message="threshold governance rows require non-empty threshold labels",
                        target=f"metrics.threshold_summaries[{index}].threshold_label",
                    )
                )
            if threshold <= previous_threshold:
                issues.append(
                    _issue(
                        rule_id="threshold_order_not_increasing",
                        message="threshold values must stay strictly increasing",
                        target="metrics.threshold_summaries",
                    )
                )
            previous_threshold = threshold
            if threshold < 0.0 or threshold > 1.0:
                issues.append(
                    _issue(
                        rule_id="threshold_out_of_range",
                        message="threshold values must stay within [0, 1]",
                        target=f"metrics.threshold_summaries[{index}].threshold",
                        observed=threshold,
                    )
                )
            for field_name, value in (("sensitivity", sensitivity), ("specificity", specificity)):
                if 0.0 <= value <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id=f"{field_name}_out_of_range",
                        message=f"{field_name} must stay within [0, 1]",
                        target=f"metrics.threshold_summaries[{index}].{field_name}",
                        observed=value,
                    )
                )
            if not math.isfinite(net_benefit):
                issues.append(
                    _issue(
                        rule_id="net_benefit_non_finite",
                        message="net benefit must be finite",
                        target=f"metrics.threshold_summaries[{index}].net_benefit",
                    )
                )
            card_box_id = str(item.get("card_box_id") or "").strip()
            if not card_box_id:
                issues.append(
                    _issue(
                        rule_id="threshold_card_reference_missing",
                        message="threshold governance metrics must reference the rendered threshold card box",
                        target=f"metrics.threshold_summaries[{index}].card_box_id",
                    )
                )
                continue
            card_box = threshold_card_by_id.get(card_box_id)
            if card_box is None:
                issues.append(
                    _issue(
                        rule_id="threshold_card_reference_missing",
                        message="threshold governance metrics must reference an existing threshold_card box",
                        target=f"metrics.threshold_summaries[{index}].card_box_id",
                        observed=card_box_id,
                    )
                )
                continue
            if threshold_panel is not None and not _box_within_box(card_box, threshold_panel):
                issues.append(
                    _issue(
                        rule_id="threshold_card_outside_panel",
                        message="threshold-card boxes must stay within the threshold_panel region",
                        target=f"layout_boxes.{card_box.box_id}",
                        box_refs=(card_box.box_id, threshold_panel.box_id),
                    )
                )

    risk_group_summaries = sidecar.metrics.get("risk_group_summaries")
    if not isinstance(risk_group_summaries, list) or not risk_group_summaries:
        issues.append(
            _issue(
                rule_id="risk_group_summaries_missing",
                message="threshold governance qc requires non-empty risk_group_summaries metrics",
                target="metrics.risk_group_summaries",
            )
        )
        return issues

    previous_group_order = 0.0
    for index, item in enumerate(risk_group_summaries):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.risk_group_summaries[{index}] must be an object")
        group_label = str(item.get("group_label") or "").strip()
        group_order = _require_numeric(
            item.get("group_order"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].group_order",
        )
        n = _require_numeric(
            item.get("n"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].n",
        )
        events = _require_numeric(
            item.get("events"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].events",
        )
        predicted_risk = _require_numeric(
            item.get("predicted_risk"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].predicted_risk",
        )
        observed_risk = _require_numeric(
            item.get("observed_risk"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].observed_risk",
        )
        predicted_x = _require_numeric(
            item.get("predicted_x"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].predicted_x",
        )
        observed_x = _require_numeric(
            item.get("observed_x"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].observed_x",
        )
        y = _require_numeric(
            item.get("y"),
            label=f"layout_sidecar.metrics.risk_group_summaries[{index}].y",
        )
        if not group_label:
            issues.append(
                _issue(
                    rule_id="risk_group_label_missing",
                    message="risk-group labels must be non-empty",
                    target=f"metrics.risk_group_summaries[{index}].group_label",
                )
            )
        if group_order <= previous_group_order:
            issues.append(
                _issue(
                    rule_id="risk_group_order_not_increasing",
                    message="risk-group order must stay strictly increasing",
                    target="metrics.risk_group_summaries",
                )
            )
        previous_group_order = group_order
        if n <= 0:
            issues.append(
                _issue(
                    rule_id="risk_group_size_non_positive",
                    message="risk-group n must be positive",
                    target=f"metrics.risk_group_summaries[{index}].n",
                )
            )
        if events < 0 or events > n:
            issues.append(
                _issue(
                    rule_id="risk_group_events_invalid",
                    message="risk-group events must stay between 0 and n",
                    target=f"metrics.risk_group_summaries[{index}].events",
                    observed=events,
                    expected={"minimum": 0, "maximum": n},
                )
            )
        for field_name, value in (("predicted_risk", predicted_risk), ("observed_risk", observed_risk)):
            if 0.0 <= value <= 1.0:
                continue
            issues.append(
                _issue(
                    rule_id=f"{field_name}_out_of_range",
                    message=f"{field_name} must stay within [0, 1]",
                    target=f"metrics.risk_group_summaries[{index}].{field_name}",
                    observed=value,
                )
            )
        if calibration_panel is not None:
            if not _point_within_box(calibration_panel, x=predicted_x, y=y):
                issues.append(
                    _issue(
                        rule_id="calibration_point_outside_panel",
                        message="predicted calibration point must stay within calibration_panel",
                        target=f"metrics.risk_group_summaries[{index}].predicted_x",
                        observed={"x": predicted_x, "y": y},
                        box_refs=(calibration_panel.box_id,),
                    )
                )
            if not _point_within_box(calibration_panel, x=observed_x, y=y):
                issues.append(
                    _issue(
                        rule_id="calibration_point_outside_panel",
                        message="observed calibration point must stay within calibration_panel",
                        target=f"metrics.risk_group_summaries[{index}].observed_x",
                        observed={"x": observed_x, "y": y},
                        box_refs=(calibration_panel.box_id,),
                    )
                )

    return issues

def _check_publication_time_to_event_multihorizon_calibration_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    required_box_types = ["panel_title", "panel_label", "subplot_x_axis_title", "legend"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box for box in sidecar.layout_boxes if box.box_type in {"title", "panel_title", "panel_label", "subplot_x_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))

    panel_metrics = sidecar.metrics.get("panels")
    if not isinstance(panel_metrics, list) or not panel_metrics:
        issues.append(
            _issue(
                rule_id="panel_metrics_missing",
                message="multihorizon calibration qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues
    calibration_panels = _boxes_of_type(sidecar.panel_boxes, "calibration_panel")
    if len(calibration_panels) != len(panel_metrics):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="multihorizon calibration panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(calibration_panels)},
                expected={"metrics.panels": len(panel_metrics)},
            )
        )
    label_panel_map: dict[str, str] = {}
    previous_horizon = 0.0
    for panel_index, item in enumerate(panel_metrics):
        if not isinstance(item, dict):
            raise ValueError(f"metrics.panels[{panel_index}] must be an object")
        panel_label = str(item.get("panel_label") or "").strip()
        panel_title = str(item.get("title") or "").strip()
        panel_id = str(item.get("panel_id") or "").strip()
        if panel_label:
            label_panel_map[f"panel_label_{_panel_label_token(panel_label)}"] = f"panel_{_panel_label_token(panel_label)}"
        if not panel_id or not panel_label or not panel_title:
            issues.append(
                _issue(
                    rule_id="panel_metadata_missing",
                    message="multihorizon calibration panels must declare panel_id, panel_label, and title",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
        time_horizon_months = _require_numeric(
            item.get("time_horizon_months"),
            label=f"metrics.panels[{panel_index}].time_horizon_months",
        )
        if time_horizon_months <= 0:
            issues.append(
                _issue(
                    rule_id="time_horizon_non_positive",
                    message="time_horizon_months must stay positive",
                    target=f"metrics.panels[{panel_index}].time_horizon_months",
                )
            )
        if time_horizon_months <= previous_horizon:
            issues.append(
                _issue(
                    rule_id="time_horizon_not_increasing",
                    message="time_horizon_months must stay strictly increasing across panels",
                    target="metrics.panels",
                )
            )
        previous_horizon = time_horizon_months

        calibration_summary = item.get("calibration_summary")
        if not isinstance(calibration_summary, list) or not calibration_summary:
            issues.append(
                _issue(
                    rule_id="calibration_summary_missing",
                    message="every multihorizon calibration panel requires non-empty calibration_summary",
                    target=f"metrics.panels[{panel_index}].calibration_summary",
                )
            )
            continue
        target_panel = next(
            (box for box in calibration_panels if box.box_id == f"panel_{_panel_label_token(panel_label)}"),
            None,
        )
        previous_group_order = 0.0
        for group_index, summary in enumerate(calibration_summary):
            if not isinstance(summary, dict):
                raise ValueError(f"metrics.panels[{panel_index}].calibration_summary[{group_index}] must be an object")
            group_label = str(summary.get("group_label") or "").strip()
            group_order = _require_numeric(
                summary.get("group_order"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].group_order",
            )
            n = _require_numeric(
                summary.get("n"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].n",
            )
            events = _require_numeric(
                summary.get("events"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].events",
            )
            predicted_risk = _require_numeric(
                summary.get("predicted_risk"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].predicted_risk",
            )
            observed_risk = _require_numeric(
                summary.get("observed_risk"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].observed_risk",
            )
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="group_label_missing",
                        message="multihorizon calibration groups require non-empty labels",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].group_label",
                    )
                )
            if group_order <= previous_group_order:
                issues.append(
                    _issue(
                        rule_id="group_order_not_increasing",
                        message="calibration group_order must stay strictly increasing within each panel",
                        target=f"metrics.panels[{panel_index}].calibration_summary",
                    )
                )
            previous_group_order = group_order
            if n <= 0:
                issues.append(
                    _issue(
                        rule_id="group_size_non_positive",
                        message="calibration group size n must be positive",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].n",
                    )
                )
            if events < 0 or events > n:
                issues.append(
                    _issue(
                        rule_id="events_invalid",
                        message="calibration events must stay between 0 and n",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].events",
                        observed=events,
                        expected={"minimum": 0, "maximum": n},
                    )
                )
            for field_name, value in (("predicted_risk", predicted_risk), ("observed_risk", observed_risk)):
                if 0.0 <= value <= 1.0:
                    continue
                issues.append(
                    _issue(
                        rule_id=f"{field_name}_out_of_range",
                        message=f"{field_name} must stay within [0, 1]",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].{field_name}",
                        observed=value,
                    )
                )
            if target_panel is None:
                continue
            predicted_x = _require_numeric(
                summary.get("predicted_x"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].predicted_x",
            )
            observed_x = _require_numeric(
                summary.get("observed_x"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].observed_x",
            )
            y = _require_numeric(
                summary.get("y"),
                label=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].y",
            )
            if not _point_within_box(target_panel, x=predicted_x, y=y):
                issues.append(
                    _issue(
                        rule_id="calibration_point_outside_panel",
                        message="predicted calibration point must stay within its panel",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].predicted_x",
                        observed={"x": predicted_x, "y": y},
                        box_refs=(target_panel.box_id,),
                    )
                )
            if not _point_within_box(target_panel, x=observed_x, y=y):
                issues.append(
                    _issue(
                        rule_id="calibration_point_outside_panel",
                        message="observed calibration point must stay within its panel",
                        target=f"metrics.panels[{panel_index}].calibration_summary[{group_index}].observed_x",
                        observed={"x": observed_x, "y": y},
                        box_refs=(target_panel.box_id,),
                    )
                )

    issues.extend(_check_composite_panel_label_anchors(sidecar, label_panel_map=label_panel_map))
    return issues
