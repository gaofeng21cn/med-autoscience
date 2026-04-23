from __future__ import annotations

from .shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _boxes_overlap, _check_boxes_within_device, _check_composite_panel_label_anchors, _check_curve_like_layout, _check_curve_metrics, _check_curve_series_collection, _check_legend_panel_overlap, _check_pairwise_non_overlap, _check_reference_line_collection_within_device, _check_reference_line_within_device, _check_required_box_types, _check_risk_layering_bar_metrics, _check_time_dependent_roc_comparison_panel_metrics, _check_time_to_event_discrimination_calibration_metrics, _first_box_of_type, _issue, _layout_override_flag, _panel_label_token, _primary_panel, _require_numeric, math

def _check_publication_evidence_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_curve_like_layout(sidecar)
    if not _layout_override_flag(sidecar, "show_figure_title", False):
        issues = [
            issue
            for issue in issues
            if not (issue.get("rule_id") == "missing_box" and issue.get("target") == "title")
        ]
    issues.extend(_check_legend_panel_overlap(sidecar))
    if sidecar.template_id == "time_to_event_discrimination_calibration_panel":
        if len(sidecar.panel_boxes) < 2:
            issues.append(
                _issue(
                    rule_id="composite_panels_missing",
                    message="time-to-event discrimination/calibration panel requires left and right panels",
                    target="panel_boxes",
                    expected={"minimum_count": 2},
                    observed={"count": len(sidecar.panel_boxes)},
                )
            )
        issues.extend(_check_time_to_event_discrimination_calibration_metrics(sidecar.metrics))
        discrimination_points = sidecar.metrics.get("discrimination_points")
        calibration_summary = sidecar.metrics.get("calibration_summary")
        expected_marker_count = 0
        if isinstance(discrimination_points, list):
            expected_marker_count += len(discrimination_points)
        if isinstance(calibration_summary, list):
            expected_marker_count += len(calibration_summary) * 2
        metric_marker_count = len(_boxes_of_type(sidecar.layout_boxes, "metric_marker"))
        if expected_marker_count and metric_marker_count < expected_marker_count:
            issues.append(
                _issue(
                    rule_id="metric_markers_incomplete",
                    message="time-to-event discrimination/calibration panel requires marker boxes for all summary points",
                    target="layout_boxes",
                    observed={"metric_marker_count": metric_marker_count},
                    expected={"minimum_count": expected_marker_count},
                )
            )
        annotation = _first_box_of_type(sidecar.layout_boxes, "annotation_block")
        legend = _first_box_of_type(sidecar.guide_boxes, "legend")
        if annotation is not None:
            panel_titles = _boxes_of_type(sidecar.layout_boxes, "panel_title")
            overlapped_panels = [panel for panel in sidecar.panel_boxes if _boxes_overlap(annotation, panel)]
            containing_panels = [panel for panel in sidecar.panel_boxes if _box_within_box(annotation, panel)]
            expected_callout_panel = next((panel for panel in sidecar.panel_boxes if panel.box_id == "panel_right"), None)
            if len(overlapped_panels) > 1:
                issues.append(
                    _issue(
                        rule_id="annotation_cross_panel_overlap",
                        message="calibration callout must stay within a single blank region rather than spanning multiple panels",
                        target="annotation_block",
                        box_refs=tuple(box.box_id for box in overlapped_panels),
                    )
                )
            if not containing_panels:
                issues.append(
                    _issue(
                        rule_id="annotation_out_of_panel",
                        message="calibration callout must stay fully inside a single panel canvas",
                        target="annotation_block",
                        box_refs=(annotation.box_id,),
                    )
                )
            elif expected_callout_panel is not None and not _box_within_box(annotation, expected_callout_panel):
                issues.append(
                    _issue(
                        rule_id="annotation_wrong_panel",
                        message="calibration callout must stay in Panel B (the grouped-calibration panel)",
                        target="annotation_block",
                        box_refs=(annotation.box_id, expected_callout_panel.box_id),
                    )
                )
            if panel_titles and annotation.y1 > min(panel_title.y0 for panel_title in panel_titles):
                issues.append(
                    _issue(
                        rule_id="annotation_header_band",
                        message="calibration callout must stay below the panel-title header band",
                        target="annotation_block",
                        box_refs=(annotation.box_id,),
                    )
                )
            for panel_title in panel_titles:
                if not _boxes_overlap(annotation, panel_title):
                    continue
                issues.append(
                    _issue(
                        rule_id="annotation_title_overlap",
                        message="calibration callout must not overlap the panel title",
                        target="annotation_block",
                        box_refs=(annotation.box_id, panel_title.box_id),
                    )
                )
            for marker_box in _boxes_of_type(sidecar.layout_boxes, "metric_marker"):
                if not _boxes_overlap(annotation, marker_box):
                    continue
                issues.append(
                    _issue(
                        rule_id="annotation_metric_overlap",
                        message="calibration callout must not overlap evidence markers",
                        target="annotation_block",
                        box_refs=(annotation.box_id, marker_box.box_id),
                    )
                )
            if legend is not None and _boxes_overlap(annotation, legend):
                issues.append(
                    _issue(
                        rule_id="annotation_legend_overlap",
                        message="calibration callout must not overlap the legend",
                        target="annotation_block",
                        box_refs=(annotation.box_id, legend.box_id),
                    )
                )
        return issues

    if sidecar.template_id == "time_dependent_roc_comparison_panel":
        issues.extend(_check_time_dependent_roc_comparison_panel_metrics(sidecar))
        return issues

    issues.extend(_check_curve_metrics(sidecar.metrics))
    issues.extend(_check_reference_line_within_device(sidecar))
    if sidecar.template_id == "time_dependent_roc_horizon":
        time_horizon_months = sidecar.metrics.get("time_horizon_months")
        if time_horizon_months is None:
            issues.append(
                _issue(
                    rule_id="time_horizon_months_missing",
                    message="time-dependent ROC horizon outputs must carry structured time_horizon_months semantics",
                    target="metrics.time_horizon_months",
                )
            )
        else:
            normalized_time_horizon_months = _require_numeric(
                time_horizon_months,
                label="layout_sidecar.metrics.time_horizon_months",
            )
            if not float(normalized_time_horizon_months).is_integer() or int(normalized_time_horizon_months) <= 0:
                issues.append(
                    _issue(
                        rule_id="time_horizon_months_invalid",
                        message="time_horizon_months must be a positive integer",
                        target="metrics.time_horizon_months",
                        observed=time_horizon_months,
                    )
                )
    return issues

def _check_publication_decision_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_publication_evidence_curve(sidecar)
    if sidecar.template_id != "time_to_event_decision_curve":
        return issues

    if len(sidecar.panel_boxes) < 2:
        issues.append(
            _issue(
                rule_id="treated_fraction_panel_missing",
                message="time-to-event decision curve requires a treated-fraction companion panel",
                target="panel_boxes",
                expected={"minimum_count": 2},
                observed={"count": len(sidecar.panel_boxes)},
            )
        )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_left",
                "panel_label_B": "panel_right",
            },
        )
    )

    treated_fraction_series = sidecar.metrics.get("treated_fraction_series")
    if not isinstance(treated_fraction_series, dict):
        issues.append(
            _issue(
                rule_id="treated_fraction_series_missing",
                message="time-to-event decision curve requires treated_fraction_series metrics",
                target="metrics.treated_fraction_series",
            )
        )
        return issues

    x_values = treated_fraction_series.get("x")
    y_values = treated_fraction_series.get("y")
    if not isinstance(x_values, list) or not isinstance(y_values, list):
        raise ValueError("layout_sidecar.metrics.treated_fraction_series must contain x and y lists")
    if len(x_values) != len(y_values):
        issues.append(
            _issue(
                rule_id="treated_fraction_length_mismatch",
                message="treated fraction x/y lengths must match",
                target="metrics.treated_fraction_series",
                observed={"x": len(x_values), "y": len(y_values)},
            )
        )
        return issues

    for index, (x_value, y_value) in enumerate(zip(x_values, y_values, strict=True)):
        x_numeric = _require_numeric(x_value, label=f"layout_sidecar.metrics.treated_fraction_series.x[{index}]")
        y_numeric = _require_numeric(y_value, label=f"layout_sidecar.metrics.treated_fraction_series.y[{index}]")
        if math.isfinite(x_numeric) and math.isfinite(y_numeric):
            continue
        issues.append(
            _issue(
                rule_id="treated_fraction_non_finite",
                message="treated fraction coordinates must be finite",
                target="metrics.treated_fraction_series",
            )
        )
        break

    return issues

def _check_publication_binary_calibration_decision_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["subplot_x_axis_title", "subplot_y_axis_title"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    calibration_panel = _first_box_of_type(sidecar.panel_boxes, "calibration_panel")
    decision_panel = _first_box_of_type(sidecar.panel_boxes, "decision_panel")
    if calibration_panel is None:
        issues.append(
            _issue(
                rule_id="calibration_panel_missing",
                message="binary calibration/decision panel requires a calibration panel box",
                target="panel_boxes",
                expected="calibration_panel",
            )
        )
    if decision_panel is None:
        issues.append(
            _issue(
                rule_id="decision_panel_missing",
                message="binary calibration/decision panel requires a decision panel box",
                target="panel_boxes",
                expected="decision_panel",
            )
        )
    if len(sidecar.panel_boxes) < 2:
        issues.append(
            _issue(
                rule_id="composite_panels_missing",
                message="binary calibration/decision panel requires two panel boxes",
                target="panel_boxes",
                observed={"count": len(sidecar.panel_boxes)},
                expected={"minimum_count": 2},
            )
        )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "subplot_title", "subplot_x_axis_title", "subplot_y_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    calibration_axis_window = sidecar.metrics.get("calibration_axis_window")
    if not isinstance(calibration_axis_window, dict):
        issues.append(
            _issue(
                rule_id="calibration_axis_window_missing",
                message="binary calibration/decision panel requires an explicit calibration_axis_window metric",
                target="metrics.calibration_axis_window",
            )
        )
    else:
        xmin = _require_numeric(calibration_axis_window.get("xmin"), label="metrics.calibration_axis_window.xmin")
        xmax = _require_numeric(calibration_axis_window.get("xmax"), label="metrics.calibration_axis_window.xmax")
        ymin = _require_numeric(calibration_axis_window.get("ymin"), label="metrics.calibration_axis_window.ymin")
        ymax = _require_numeric(calibration_axis_window.get("ymax"), label="metrics.calibration_axis_window.ymax")
        if xmin >= xmax or ymin >= ymax:
            issues.append(
                _issue(
                    rule_id="calibration_axis_window_invalid",
                    message="calibration axis window must be strictly increasing on both axes",
                    target="metrics.calibration_axis_window",
                    observed={"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
                )
            )
        else:
            calibration_series = sidecar.metrics.get("calibration_series")
            if isinstance(calibration_series, list):
                for series_index, series in enumerate(calibration_series):
                    if not isinstance(series, dict):
                        continue
                    x_values = series.get("x")
                    y_values = series.get("y")
                    if not isinstance(x_values, list) or not isinstance(y_values, list):
                        continue
                    for point_index, (x_value, y_value) in enumerate(zip(x_values, y_values, strict=True)):
                        x_numeric = _require_numeric(
                            x_value,
                            label=f"metrics.calibration_series[{series_index}].x[{point_index}]",
                        )
                        y_numeric = _require_numeric(
                            y_value,
                            label=f"metrics.calibration_series[{series_index}].y[{point_index}]",
                        )
                        if xmin <= x_numeric <= xmax and ymin <= y_numeric <= ymax:
                            continue
                        issues.append(
                            _issue(
                                rule_id="calibration_axis_window_excludes_data",
                                message="calibration axis window must cover every audited calibration point",
                                target=f"metrics.calibration_series[{series_index}]",
                                observed={"x": x_numeric, "y": y_numeric},
                                expected={"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
                            )
                        )
                        break
    issues.extend(_check_curve_series_collection(sidecar.metrics.get("calibration_series"), target="metrics.calibration_series"))
    issues.extend(_check_curve_series_collection(sidecar.metrics.get("decision_series"), target="metrics.decision_series"))

    calibration_reference_line = sidecar.metrics.get("calibration_reference_line")
    if calibration_reference_line is not None:
        issues.extend(
            _check_reference_line_collection_within_device(
                [calibration_reference_line],
                sidecar=sidecar,
                target="metrics.calibration_reference_line",
            )
        )
    issues.extend(
        _check_reference_line_collection_within_device(
            sidecar.metrics.get("decision_reference_lines"),
            sidecar=sidecar,
            target="metrics.decision_reference_lines",
        )
    )

    focus_window = sidecar.metrics.get("decision_focus_window")
    if not isinstance(focus_window, dict):
        issues.append(
            _issue(
                rule_id="focus_window_missing",
                message="decision focus window metrics are required",
                target="metrics.decision_focus_window",
            )
        )
    else:
        xmin = _require_numeric(focus_window.get("xmin"), label="metrics.decision_focus_window.xmin")
        xmax = _require_numeric(focus_window.get("xmax"), label="metrics.decision_focus_window.xmax")
        if xmin >= xmax:
            issues.append(
                _issue(
                    rule_id="focus_window_invalid",
                    message="decision focus window xmin must be < xmax",
                    target="metrics.decision_focus_window",
                    observed={"xmin": xmin, "xmax": xmax},
                )
            )

    focus_window_box = _first_box_of_type(sidecar.guide_boxes, "focus_window")
    if focus_window_box is None:
        issues.append(
            _issue(
                rule_id="focus_window_box_missing",
                message="decision focus window guide box is required",
                target="guide_boxes",
                expected="focus_window",
            )
        )
    elif decision_panel is not None:
        epsilon = 1e-9
        focus_within_panel = (
            decision_panel.x0 - epsilon <= focus_window_box.x0 <= decision_panel.x1 + epsilon
            and decision_panel.x0 - epsilon <= focus_window_box.x1 <= decision_panel.x1 + epsilon
            and decision_panel.y0 - epsilon <= focus_window_box.y0 <= decision_panel.y1 + epsilon
            and decision_panel.y0 - epsilon <= focus_window_box.y1 <= decision_panel.y1 + epsilon
        )
        if not focus_within_panel:
            issues.append(
                _issue(
                    rule_id="focus_window_outside_panel",
                    message="decision focus window must stay within the decision panel",
                    target="focus_window",
                    box_refs=(focus_window_box.box_id, decision_panel.box_id),
                )
            )

    return issues

def _check_publication_risk_layering_bars(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["y_axis_title", "panel", "risk_bar"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    if len(sidecar.panel_boxes) < 2:
        issues.append(
            _issue(
                rule_id="risk_layering_panel_missing",
                message="risk layering bars require left and right panels",
                target="panel_boxes",
                expected={"minimum_count": 2},
                observed={"count": len(sidecar.panel_boxes)},
            )
        )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    issues.extend(
        _check_risk_layering_bar_metrics(sidecar.metrics.get("left_bars"), target="metrics.left_bars")
    )
    issues.extend(
        _check_risk_layering_bar_metrics(sidecar.metrics.get("right_bars"), target="metrics.right_bars")
    )
    return issues

def _check_publication_survival_curve(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_curve_like_layout(sidecar)
    if not _layout_override_flag(sidecar, "show_figure_title", False):
        issues = [
            issue
            for issue in issues
            if not (issue.get("rule_id") == "missing_box" and issue.get("target") == "title")
        ]
    issues.extend(_check_legend_panel_overlap(sidecar))

    annotation = _first_box_of_type(sidecar.guide_boxes + sidecar.layout_boxes, "annotation_block")
    legend = _first_box_of_type(sidecar.guide_boxes, "legend")
    panels = sidecar.panel_boxes
    if not panels:
        primary_panel = _primary_panel(sidecar)
        panels = (primary_panel,) if primary_panel is not None else ()
    if annotation is not None:
        for panel in panels:
            if panel is None or not _boxes_overlap(annotation, panel):
                continue
            issues.append(
                _issue(
                    rule_id="annotation_panel_overlap",
                    message="annotation block must not overlap the panel",
                    target="annotation_block",
                    box_refs=(annotation.box_id, panel.box_id),
                )
            )
    if annotation is not None and legend is not None and _boxes_overlap(annotation, legend):
        issues.append(
            _issue(
                rule_id="annotation_legend_overlap",
                message="annotation block must not overlap the legend",
                target="annotation_block",
                box_refs=(annotation.box_id, legend.box_id),
            )
        )

    if sidecar.template_id == "time_to_event_risk_group_summary":
        if len(sidecar.panel_boxes) < 2:
            issues.append(
                _issue(
                    rule_id="composite_panels_missing",
                    message="time-to-event risk-group summary requires two panel boxes",
                    target="panel_boxes",
                    expected={"minimum_count": 2},
                    observed={"count": len(sidecar.panel_boxes)},
                )
            )
        issues.extend(
            _check_composite_panel_label_anchors(
                sidecar,
                label_panel_map={
                    "panel_label_A": "panel_left",
                    "panel_label_B": "panel_right",
                },
            )
        )
        risk_group_summaries = sidecar.metrics.get("risk_group_summaries")
        if not isinstance(risk_group_summaries, list) or not risk_group_summaries:
            issues.append(
                _issue(
                    rule_id="risk_group_summaries_missing",
                    message="risk-group summary qc requires non-empty risk_group_summaries metrics",
                    target="metrics.risk_group_summaries",
                )
            )
            return issues
        for index, item in enumerate(risk_group_summaries):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.risk_group_summaries[{index}] must be an object")
            group_label = str(item.get("label") or "").strip()
            if not group_label:
                issues.append(
                    _issue(
                        rule_id="risk_group_label_missing",
                        message="risk-group summary labels must be non-empty",
                        target=f"metrics.risk_group_summaries[{index}].label",
                    )
                )
            sample_size = _require_numeric(
                item.get("sample_size"),
                label=f"layout_sidecar.metrics.risk_group_summaries[{index}].sample_size",
            )
            event_count = _require_numeric(
                item.get("events_5y"),
                label=f"layout_sidecar.metrics.risk_group_summaries[{index}].events_5y",
            )
            predicted_risk = _require_numeric(
                item.get("mean_predicted_risk_5y"),
                label=f"layout_sidecar.metrics.risk_group_summaries[{index}].mean_predicted_risk_5y",
            )
            observed_risk = _require_numeric(
                item.get("observed_km_risk_5y"),
                label=f"layout_sidecar.metrics.risk_group_summaries[{index}].observed_km_risk_5y",
            )
            if sample_size <= 0:
                issues.append(
                    _issue(
                        rule_id="risk_group_sample_size_non_positive",
                        message="risk-group sample_size must be positive",
                        target=f"metrics.risk_group_summaries[{index}].sample_size",
                    )
                )
            if event_count < 0:
                issues.append(
                    _issue(
                        rule_id="risk_group_event_count_negative",
                        message="risk-group events_5y must be non-negative",
                        target=f"metrics.risk_group_summaries[{index}].events_5y",
                    )
                )
            if not math.isfinite(predicted_risk) or not math.isfinite(observed_risk):
                issues.append(
                    _issue(
                        rule_id="risk_group_risk_non_finite",
                        message="risk-group summary risks must be finite",
                        target=f"metrics.risk_group_summaries[{index}]",
                    )
                )
        return issues

    if sidecar.template_id == "time_to_event_stratified_cumulative_incidence_panel":
        panel_metrics = sidecar.metrics.get("panels")
        if not isinstance(panel_metrics, list) or not panel_metrics:
            issues.append(
                _issue(
                    rule_id="panel_metrics_missing",
                    message="stratified cumulative-incidence qc requires non-empty panel metrics",
                    target="metrics.panels",
                )
            )
            return issues
        if len(sidecar.panel_boxes) != len(panel_metrics):
            issues.append(
                _issue(
                    rule_id="composite_panels_missing",
                    message="stratified cumulative-incidence qc requires one panel box per declared panel",
                    target="panel_boxes",
                    expected={"count": len(panel_metrics)},
                    observed={"count": len(sidecar.panel_boxes)},
                )
            )
        label_panel_map: dict[str, str] = {}
        layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
        seen_panel_labels: set[str] = set()
        for panel_index, panel in enumerate(panel_metrics):
            if not isinstance(panel, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
            panel_label = str(panel.get("panel_label") or "").strip()
            if not panel_label:
                issues.append(
                    _issue(
                        rule_id="panel_label_missing",
                        message="stratified cumulative-incidence panels require non-empty panel_label metrics",
                        target=f"metrics.panels[{panel_index}].panel_label",
                    )
                )
                continue
            if panel_label in seen_panel_labels:
                issues.append(
                    _issue(
                        rule_id="duplicate_panel_label",
                        message="stratified cumulative-incidence panel labels must be unique",
                        target="metrics.panels",
                        observed=panel_label,
                    )
                )
                continue
            seen_panel_labels.add(panel_label)
            panel_label_token = _panel_label_token(panel_label)
            label_panel_map[f"panel_label_{panel_label_token}"] = f"panel_{panel_label_token}"
            if f"panel_title_{panel_label_token}" not in layout_boxes_by_id:
                issues.append(
                    _issue(
                        rule_id="missing_panel_title",
                        message="stratified cumulative-incidence panels require explicit panel titles",
                        target="layout_boxes",
                        expected=f"panel_title_{panel_label_token}",
                    )
                )
            groups = panel.get("groups")
            if not isinstance(groups, list) or not groups:
                issues.append(
                    _issue(
                        rule_id="groups_missing",
                        message="stratified cumulative-incidence panel requires non-empty groups",
                        target=f"metrics.panels[{panel_index}].groups",
                    )
                )
                continue
            seen_group_labels: set[str] = set()
            for group_index, group in enumerate(groups):
                if not isinstance(group, dict):
                    raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}] must be an object")
                group_label = str(group.get("label") or "").strip()
                if not group_label:
                    issues.append(
                        _issue(
                            rule_id="group_label_missing",
                            message="panel group labels must be non-empty",
                            target=f"metrics.panels[{panel_index}].groups[{group_index}].label",
                        )
                    )
                elif group_label in seen_group_labels:
                    issues.append(
                        _issue(
                            rule_id="duplicate_group_label",
                            message="panel group labels must be unique within each panel",
                            target=f"metrics.panels[{panel_index}].groups",
                            observed=group_label,
                        )
                    )
                else:
                    seen_group_labels.add(group_label)
                times = group.get("times")
                values = group.get("values")
                if not isinstance(times, list) or not isinstance(values, list):
                    raise ValueError(
                        f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}] must contain times and values lists"
                    )
                if len(times) != len(values):
                    issues.append(
                        _issue(
                            rule_id="group_length_mismatch",
                            message="panel group times/values lengths must match",
                            target=f"metrics.panels[{panel_index}].groups[{group_index}]",
                            observed={"times": len(times), "values": len(values)},
                        )
                    )
                    continue
                previous_time: float | None = None
                previous_value: float | None = None
                for point_index, (time_value, probability_value) in enumerate(zip(times, values, strict=True)):
                    time_numeric = _require_numeric(
                        time_value,
                        label=f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}].times[{point_index}]",
                    )
                    probability_numeric = _require_numeric(
                        probability_value,
                        label=f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}].values[{point_index}]",
                    )
                    if previous_time is not None and time_numeric <= previous_time:
                        issues.append(
                            _issue(
                                rule_id="group_times_not_strictly_increasing",
                                message="panel group times must be strictly increasing",
                                target=f"metrics.panels[{panel_index}].groups[{group_index}].times",
                            )
                        )
                        break
                    if probability_numeric < 0.0 or probability_numeric > 1.0:
                        issues.append(
                            _issue(
                                rule_id="group_probability_out_of_range",
                                message="panel group cumulative incidence must stay within [0, 1]",
                                target=f"metrics.panels[{panel_index}].groups[{group_index}].values[{point_index}]",
                                observed=probability_numeric,
                            )
                        )
                        break
                    if previous_value is not None and probability_numeric + 1e-12 < previous_value:
                        issues.append(
                            _issue(
                                rule_id="group_values_not_monotonic",
                                message="panel group cumulative incidence must be monotonic non-decreasing",
                                target=f"metrics.panels[{panel_index}].groups[{group_index}].values",
                            )
                        )
                        break
                    previous_time = time_numeric
                    previous_value = probability_numeric
        issues.extend(_check_composite_panel_label_anchors(sidecar, label_panel_map=label_panel_map))
        return issues

    groups = sidecar.metrics.get("groups")
    if not isinstance(groups, list) or not groups:
        issues.append(
            _issue(
                rule_id="groups_missing",
                message="survival qc requires at least one group",
                target="metrics.groups",
            )
        )
        return issues
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ValueError(f"layout_sidecar.metrics.groups[{index}] must be an object")
        times = group.get("times")
        values = group.get("values")
        if not isinstance(times, list) or not isinstance(values, list):
            raise ValueError(f"layout_sidecar.metrics.groups[{index}] must contain times and values lists")
        if len(times) != len(values):
            issues.append(
                _issue(
                    rule_id="group_length_mismatch",
                    message="group times/values lengths must match",
                    target=f"metrics.groups[{index}]",
                    observed={"times": len(times), "values": len(values)},
                )
            )
            continue
        for point_index, (time_value, probability_value) in enumerate(zip(times, values, strict=True)):
            _require_numeric(time_value, label=f"layout_sidecar.metrics.groups[{index}].times[{point_index}]")
            _require_numeric(probability_value, label=f"layout_sidecar.metrics.groups[{index}].values[{point_index}]")
    return issues
