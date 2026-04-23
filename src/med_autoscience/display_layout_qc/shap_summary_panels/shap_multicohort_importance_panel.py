from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _boxes_overlap, _check_boxes_within_device, _check_composite_panel_label_anchors, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _require_non_empty_text, _require_numeric, math

def _check_publication_shap_multicohort_importance_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_label",
        "panel_title",
        "subplot_x_axis_title",
        "feature_label",
        "importance_bar",
        "value_label",
    ]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = _boxes_of_type(sidecar.panel_boxes, "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_label", "panel_title", "subplot_x_axis_title", "feature_label", "value_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="shap multicohort importance qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="shap multicohort importance panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}
    expected_feature_order: tuple[str, ...] | None = None

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        cohort_label = str(panel_metric.get("cohort_label") or "").strip()
        if not panel_id or not panel_label or not title or not cohort_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="shap multicohort importance panel metrics must declare panel metadata and cohort labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None and panel_index < len(panel_boxes):
            panel_box = panel_boxes[panel_index]
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="shap multicohort importance metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue

        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        panel_title_box_id = str(panel_metric.get("panel_title_box_id") or "").strip() or f"panel_title_{panel_label}"
        if panel_title_box_id not in layout_box_by_id:
            issues.append(
                _issue(
                    rule_id="panel_title_missing",
                    message="shap multicohort importance requires an explicit panel title per cohort panel",
                    target=f"metrics.panels[{panel_index}].panel_title_box_id",
                    observed={"panel_title_box_id": panel_title_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )

        x_axis_title_box_id = str(panel_metric.get("x_axis_title_box_id") or "").strip() or f"x_axis_title_{panel_label}"
        if x_axis_title_box_id not in layout_box_by_id:
            issues.append(
                _issue(
                    rule_id="x_axis_title_missing",
                    message="shap multicohort importance requires a subplot x-axis title per cohort panel",
                    target=f"metrics.panels[{panel_index}].x_axis_title_box_id",
                    observed={"x_axis_title_box_id": x_axis_title_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )

        bars = panel_metric.get("bars")
        if not isinstance(bars, list) or not bars:
            issues.append(
                _issue(
                    rule_id="bars_missing",
                    message="shap multicohort importance panel metrics must contain non-empty bars",
                    target=f"metrics.panels[{panel_index}].bars",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        previous_rank = 0
        previous_importance = float("inf")
        seen_features: set[str] = set()
        feature_order: list[str] = []
        for bar_index, item in enumerate(bars):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}] must be an object")
            rank_value = _require_numeric(
                item.get("rank"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].rank",
            )
            if not math.isclose(rank_value, round(rank_value), rel_tol=0.0, abs_tol=1e-9) or rank_value <= 0.0:
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].rank must be a positive integer"
                )
            rank = int(round(rank_value))
            if rank <= previous_rank:
                issues.append(
                    _issue(
                        rule_id="multicohort_rank_not_increasing",
                        message="shap multicohort importance ranks must be strictly increasing within each panel",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].rank",
                        observed=rank,
                    )
                )
            previous_rank = rank

            feature = _require_non_empty_text(
                item.get("feature"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].feature",
            )
            if feature in seen_features:
                issues.append(
                    _issue(
                        rule_id="multicohort_feature_duplicate",
                        message="shap multicohort importance features must be unique within each cohort panel",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].feature",
                        observed=feature,
                    )
                )
            seen_features.add(feature)
            feature_order.append(feature)

            importance_value = _require_numeric(
                item.get("importance_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].importance_value",
            )
            if importance_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="multicohort_importance_negative",
                        message="shap multicohort importance values must be non-negative",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].importance_value",
                        observed=importance_value,
                    )
                )
            if importance_value > previous_importance + 1e-12:
                issues.append(
                    _issue(
                        rule_id="multicohort_importance_not_descending",
                        message="shap multicohort importance values must stay sorted descending by rank",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].importance_value",
                        observed=importance_value,
                    )
                )
            previous_importance = importance_value

            bar_box_id = _require_non_empty_text(
                item.get("bar_box_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].bar_box_id",
            )
            feature_label_box_id = _require_non_empty_text(
                item.get("feature_label_box_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].feature_label_box_id",
            )
            value_label_box_id = _require_non_empty_text(
                item.get("value_label_box_id"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].bars[{bar_index}].value_label_box_id",
            )

            bar_box = layout_box_by_id.get(bar_box_id)
            feature_label_box = layout_box_by_id.get(feature_label_box_id)
            value_label_box = layout_box_by_id.get(value_label_box_id)
            if bar_box is None:
                issues.append(
                    _issue(
                        rule_id="importance_bar_missing",
                        message="shap multicohort importance metrics must reference an existing importance_bar box",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].bar_box_id",
                        observed=bar_box_id,
                    )
                )
                continue
            if not _box_within_box(bar_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="importance_bar_outside_panel",
                        message="shap multicohort importance bars must stay within their declared panel region",
                        target=f"layout_boxes.{bar_box.box_id}",
                        box_refs=(bar_box.box_id, panel_box.box_id),
                    )
                )
            if feature_label_box is None:
                issues.append(
                    _issue(
                        rule_id="feature_label_missing",
                        message="shap multicohort importance metrics must reference an existing feature_label box",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].feature_label_box_id",
                        observed=feature_label_box_id,
                    )
                )
            else:
                if _boxes_overlap(feature_label_box, panel_box):
                    issues.append(
                        _issue(
                            rule_id="feature_label_panel_overlap",
                            message="feature labels must stay outside each shap multicohort panel",
                            target=f"layout_boxes.{feature_label_box.box_id}",
                            box_refs=(feature_label_box.box_id, panel_box.box_id),
                        )
                    )
                label_center_y = (feature_label_box.y0 + feature_label_box.y1) / 2.0
                if not (bar_box.y0 <= label_center_y <= bar_box.y1):
                    issues.append(
                        _issue(
                            rule_id="feature_label_row_misaligned",
                            message="feature label annotation must stay vertically aligned to its cohort row band",
                            target=f"layout_boxes.{feature_label_box.box_id}",
                            observed={"label_center_y": label_center_y},
                            expected={"row_y0": bar_box.y0, "row_y1": bar_box.y1},
                            box_refs=(bar_box.box_id, feature_label_box.box_id),
                        )
                    )
            if value_label_box is None:
                issues.append(
                    _issue(
                        rule_id="value_label_missing",
                        message="shap multicohort importance metrics must reference an existing value_label box",
                        target=f"metrics.panels[{panel_index}].bars[{bar_index}].value_label_box_id",
                        observed=value_label_box_id,
                    )
                )

        feature_order_tuple = tuple(feature_order)
        if expected_feature_order is None:
            expected_feature_order = feature_order_tuple
        elif feature_order_tuple != expected_feature_order:
            issues.append(
                _issue(
                    rule_id="multicohort_feature_order_mismatch",
                    message="all shap multicohort panels must keep the same feature order across cohorts",
                    target=f"metrics.panels[{panel_index}].bars",
                    observed={"feature_order": list(feature_order_tuple)},
                    expected={"feature_order": list(expected_feature_order)},
                    box_refs=(panel_box.box_id,),
                )
            )

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map=label_panel_map,
            allow_top_overhang_ratio=0.04,
            max_left_offset_ratio=0.08,
        )
    )
    return issues
