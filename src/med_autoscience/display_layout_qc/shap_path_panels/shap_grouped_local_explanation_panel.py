from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _boxes_of_type, _boxes_overlap, _check_boxes_within_device, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _panel_label_token, _require_non_empty_text, _require_numeric, math

def _check_publication_shap_grouped_local_explanation_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "panel_label",
        "group_label",
        "baseline_label",
        "prediction_label",
        "feature_label",
        "contribution_bar",
        "value_label",
        "zero_line",
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
        in {
            "title",
            "panel_title",
            "panel_label",
            "group_label",
            "baseline_label",
            "prediction_label",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="shap grouped local explanation qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap grouped local explanation panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    expected_feature_order: tuple[str, ...] | None = None
    seen_group_labels: set[str] = set()

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")

        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        group_label = str(panel_metric.get("group_label") or "").strip()
        baseline_value = _require_numeric(
            panel_metric.get("baseline_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric(
            panel_metric.get("predicted_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].predicted_value",
        )
        panel_token = _panel_label_token(panel_label)
        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_token}"
        zero_line_box_id = str(panel_metric.get("zero_line_box_id") or "").strip() or f"zero_line_{panel_token}"

        if not panel_id or not panel_label or not title or not group_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="shap grouped local explanation metrics must declare panel metadata and group labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue
        if group_label in seen_group_labels:
            issues.append(
                _issue(
                    rule_id="duplicate_group_label",
                    message="shap grouped local explanation group labels must be unique across panels",
                    target=f"metrics.panels[{panel_index}].group_label",
                    observed=group_label,
                )
            )
        seen_group_labels.add(group_label)

        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None and panel_index < len(panel_boxes):
            panel_box = panel_boxes[panel_index]
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="shap grouped local explanation metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}].panel_box_id",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue

        panel_label_box = layout_box_by_id.get(f"panel_label_{panel_token}")
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="missing_panel_label",
                    message="grouped local explanation panels require explicit panel labels",
                    target=f"metrics.panels[{panel_index}].panel_label",
                    expected=f"panel_label_{panel_token}",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            panel_width = max(panel_box.x1 - panel_box.x0, 1e-9)
            panel_height = max(panel_box.y1 - panel_box.y0, 1e-9)
            max_left_gap = max(panel_width * 0.14, 0.018)
            max_top_overhang = max(panel_height * 0.12, 0.03)
            if (
                panel_label_box.x1 < panel_box.x0 - max_left_gap
                or panel_label_box.x0 > panel_box.x0 + panel_width * 0.10
                or panel_label_box.y0 < panel_box.y1 - panel_height * 0.10
                or panel_label_box.y1 > panel_box.y1 + max_top_overhang
            ):
                issues.append(
                    _issue(
                        rule_id="panel_label_anchor_drift",
                        message="grouped local explanation panel labels must stay near the parent panel top-left anchor",
                        target="panel_label",
                        box_refs=(panel_label_box.box_id, panel_box.box_id),
                    )
                )

        for box_id, rule_id, message in (
            (f"panel_title_{panel_token}", "panel_title_missing", "each grouped local panel requires an explicit panel title"),
            (f"group_label_{panel_token}", "group_label_missing", "each grouped local panel requires an explicit group label"),
            (
                f"baseline_label_{panel_token}",
                "baseline_label_missing",
                "each grouped local panel requires an explicit baseline label",
            ),
            (
                f"prediction_label_{panel_token}",
                "prediction_label_missing",
                "each grouped local panel requires an explicit prediction label",
            ),
            (
                f"x_axis_title_{panel_token}",
                "x_axis_title_missing",
                "each grouped local panel requires an explicit subplot x-axis title",
            ),
        ):
            if box_id in layout_box_by_id:
                continue
            issues.append(
                _issue(
                    rule_id=rule_id,
                    message=message,
                    target=f"metrics.panels[{panel_index}]",
                    observed={"box_id": box_id},
                    box_refs=(panel_box.box_id,),
                )
            )

        zero_line = guide_box_by_id.get(zero_line_box_id)
        if zero_line is None:
            issues.append(
                _issue(
                    rule_id="zero_line_missing",
                    message="each grouped local panel requires an explicit zero_line guide box",
                    target=f"metrics.panels[{panel_index}].zero_line_box_id",
                    observed={"zero_line_box_id": zero_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
            zero_mid_x = None
            zero_tolerance = None
        else:
            epsilon = 1e-6
            if not (
                panel_box.x0 - epsilon <= zero_line.x0 <= panel_box.x1 + epsilon
                and panel_box.x0 - epsilon <= zero_line.x1 <= panel_box.x1 + epsilon
                and panel_box.y0 - epsilon <= zero_line.y0 <= panel_box.y1 + epsilon
                and panel_box.y0 - epsilon <= zero_line.y1 <= panel_box.y1 + epsilon
            ):
                issues.append(
                    _issue(
                        rule_id="zero_line_outside_panel",
                        message="grouped local explanation zero line must stay within the panel region",
                        target=f"guide_boxes.{zero_line.box_id}",
                        box_refs=(zero_line.box_id, panel_box.box_id),
                    )
                )
            zero_mid_x = (zero_line.x0 + zero_line.x1) / 2.0
            zero_tolerance = max((zero_line.x1 - zero_line.x0) / 2.0, 0.0025)

        contributions = panel_metric.get("contributions")
        if not isinstance(contributions, list) or not contributions:
            issues.append(
                _issue(
                    rule_id="contributions_missing",
                    message="shap grouped local explanation panel metrics must contain ordered contributions",
                    target=f"metrics.panels[{panel_index}].contributions",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        previous_rank = 0
        seen_features: set[str] = set()
        feature_order: list[str] = []
        contribution_sum = 0.0
        for contribution_index, contribution in enumerate(contributions):
            if not isinstance(contribution, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )

            rank_value = _require_numeric(
                contribution.get("rank"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].rank",
            )
            if not math.isclose(rank_value, round(rank_value), rel_tol=0.0, abs_tol=1e-9) or rank_value <= 0.0:
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].rank must be a positive integer"
                )
            rank = int(round(rank_value))
            if rank <= previous_rank:
                issues.append(
                    _issue(
                        rule_id="grouped_local_rank_not_increasing",
                        message="grouped local explanation contribution ranks must be strictly increasing",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].rank",
                        observed=rank,
                    )
                )
            previous_rank = rank

            feature = _require_non_empty_text(
                contribution.get("feature"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].feature",
            )
            if feature in seen_features:
                issues.append(
                    _issue(
                        rule_id="grouped_local_feature_duplicate",
                        message="grouped local explanation features must be unique within each panel",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].feature",
                        observed=feature,
                    )
                )
            seen_features.add(feature)
            feature_order.append(feature)

            shap_value = _require_numeric(
                contribution.get("shap_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].shap_value",
            )
            contribution_sum += shap_value

            bar_box_id = _require_non_empty_text(
                contribution.get("bar_box_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].bar_box_id",
            )
            feature_label_box_id = _require_non_empty_text(
                contribution.get("feature_label_box_id"),
                label=(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].feature_label_box_id"
                ),
            )
            value_label_box_id = _require_non_empty_text(
                contribution.get("value_label_box_id"),
                label=(
                    f"layout_sidecar.metrics.panels[{panel_index}].contributions[{contribution_index}].value_label_box_id"
                ),
            )

            bar_box = layout_box_by_id.get(bar_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="contribution_bar_missing",
                        message="grouped local explanation contributions must reference an existing contribution bar box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].bar_box_id",
                        observed=bar_box_id,
                        box_refs=(panel_box.box_id,),
                    )
                )
            else:
                panel_width = max(panel_box.x1 - panel_box.x0, 1e-9)
                horizontal_overhang = max(panel_width * 0.25, 0.03)
                epsilon = 1e-6
                if not (
                    panel_box.x0 - horizontal_overhang - epsilon <= bar_box.x0 <= panel_box.x1 + horizontal_overhang + epsilon
                    and panel_box.x0 - horizontal_overhang - epsilon <= bar_box.x1 <= panel_box.x1 + horizontal_overhang + epsilon
                    and panel_box.y0 - epsilon <= bar_box.y0 <= panel_box.y1 + epsilon
                    and panel_box.y0 - epsilon <= bar_box.y1 <= panel_box.y1 + epsilon
                ):
                    issues.append(
                        _issue(
                            rule_id="contribution_bar_outside_panel",
                            message="grouped local explanation contribution bars must stay aligned to the panel row band without drifting far outside the panel",
                            target=f"layout_boxes.{bar_box.box_id}",
                            box_refs=(bar_box.box_id, panel_box.box_id),
                        )
                    )
                if zero_mid_x is not None and zero_tolerance is not None:
                    if shap_value > 0.0 and bar_box.x0 < zero_mid_x - zero_tolerance:
                        issues.append(
                            _issue(
                                rule_id="positive_bar_crosses_zero",
                                message="positive grouped local explanation bars must stay on the right side of the zero line",
                                target=f"layout_boxes.{bar_box.box_id}",
                                box_refs=(bar_box.box_id, zero_line_box_id, panel_box.box_id),
                            )
                        )
                    if shap_value < 0.0 and bar_box.x1 > zero_mid_x + zero_tolerance:
                        issues.append(
                            _issue(
                                rule_id="negative_bar_crosses_zero",
                                message="negative grouped local explanation bars must stay on the left side of the zero line",
                                target=f"layout_boxes.{bar_box.box_id}",
                                box_refs=(bar_box.box_id, zero_line_box_id, panel_box.box_id),
                            )
                        )

            feature_label_box = layout_box_by_id.get(feature_label_box_id)
            if feature_label_box is None:
                issues.append(
                    _issue(
                        rule_id="feature_label_missing",
                        message="grouped local explanation contributions must reference an existing feature label box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].feature_label_box_id",
                        observed=feature_label_box_id,
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif bar_box is not None:
                if _boxes_overlap(feature_label_box, panel_box):
                    issues.append(
                        _issue(
                            rule_id="feature_label_panel_overlap",
                            message="grouped local explanation feature labels must stay outside the panel region",
                            target=f"layout_boxes.{feature_label_box.box_id}",
                            box_refs=(feature_label_box.box_id, panel_box.box_id),
                        )
                    )
                label_center_y = (feature_label_box.y0 + feature_label_box.y1) / 2.0
                if not (bar_box.y0 <= label_center_y <= bar_box.y1):
                    issues.append(
                        _issue(
                            rule_id="feature_label_row_misaligned",
                            message="grouped local explanation feature labels must stay vertically aligned to their bar row",
                            target=f"layout_boxes.{feature_label_box.box_id}",
                            observed={"label_center_y": label_center_y},
                            expected={"row_y0": bar_box.y0, "row_y1": bar_box.y1},
                            box_refs=(feature_label_box.box_id, bar_box.box_id, panel_box.box_id),
                        )
                    )

            value_label_box = layout_box_by_id.get(value_label_box_id)
            if value_label_box is None:
                issues.append(
                    _issue(
                        rule_id="value_label_missing",
                        message="grouped local explanation contributions must reference an existing value label box",
                        target=f"metrics.panels[{panel_index}].contributions[{contribution_index}].value_label_box_id",
                        observed=value_label_box_id,
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif bar_box is not None:
                label_center_y = (value_label_box.y0 + value_label_box.y1) / 2.0
                if not (bar_box.y0 <= label_center_y <= bar_box.y1):
                    issues.append(
                        _issue(
                            rule_id="value_label_row_misaligned",
                            message="grouped local explanation value labels must stay vertically aligned to their bar row",
                            target=f"layout_boxes.{value_label_box.box_id}",
                            observed={"label_center_y": label_center_y},
                            expected={"row_y0": bar_box.y0, "row_y1": bar_box.y1},
                            box_refs=(value_label_box.box_id, bar_box.box_id, panel_box.box_id),
                        )
                    )

        if not math.isclose(
            predicted_value,
            baseline_value + contribution_sum,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            issues.append(
                _issue(
                    rule_id="panel_prediction_value_mismatch",
                    message="grouped local explanation predicted_value must equal baseline_value plus contribution sum",
                    target=f"metrics.panels[{panel_index}].predicted_value",
                    observed={"baseline_value": baseline_value, "predicted_value": predicted_value, "contribution_sum": contribution_sum},
                )
            )

        feature_order_tuple = tuple(feature_order)
        if expected_feature_order is None:
            expected_feature_order = feature_order_tuple
        elif feature_order_tuple != expected_feature_order:
            issues.append(
                _issue(
                    rule_id="grouped_local_feature_order_mismatch",
                    message="all grouped local explanation panels must keep the same feature order",
                    target=f"metrics.panels[{panel_index}].contributions",
                    observed={"feature_order": list(feature_order_tuple)},
                    expected={"feature_order": list(expected_feature_order)},
                    box_refs=(panel_box.box_id,),
                )
            )

    return issues
