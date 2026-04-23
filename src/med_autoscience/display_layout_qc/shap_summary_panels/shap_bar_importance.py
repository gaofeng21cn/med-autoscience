from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _boxes_overlap, _check_boxes_within_device, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _primary_panel, _require_non_empty_text, _require_numeric, math

def _check_publication_shap_bar_importance(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["x_axis_title", "feature_label", "importance_bar", "value_label"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))

    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "x_axis_title", "feature_label", "value_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    panel = _primary_panel(sidecar)
    if panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="shap bar importance qc requires a primary panel box",
                target="panel_boxes",
            )
        )
        return issues

    metrics_bars = sidecar.metrics.get("bars")
    if not isinstance(metrics_bars, list) or not metrics_bars:
        issues.append(
            _issue(
                rule_id="bars_missing",
                message="shap bar importance qc requires non-empty bar metrics",
                target="metrics.bars",
            )
        )
        return issues

    bar_box_by_id = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "importance_bar")}
    feature_label_box_by_id = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "feature_label")}
    value_label_box_by_id = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "value_label")}

    previous_rank = 0
    previous_importance = float("inf")
    seen_features: set[str] = set()
    for index, item in enumerate(metrics_bars):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.bars[{index}] must be an object")
        rank_value = _require_numeric(item.get("rank"), label=f"layout_sidecar.metrics.bars[{index}].rank")
        if not math.isclose(rank_value, round(rank_value), rel_tol=0.0, abs_tol=1e-9) or rank_value <= 0.0:
            raise ValueError(f"layout_sidecar.metrics.bars[{index}].rank must be a positive integer")
        rank = int(round(rank_value))
        if rank <= previous_rank:
            issues.append(
                _issue(
                    rule_id="importance_rank_not_increasing",
                    message="shap bar importance ranks must be strictly increasing",
                    target=f"metrics.bars[{index}].rank",
                    observed=rank,
                )
            )
        previous_rank = rank
        feature = _require_non_empty_text(
            item.get("feature"),
            label=f"layout_sidecar.metrics.bars[{index}].feature",
        )
        if feature in seen_features:
            issues.append(
                _issue(
                    rule_id="importance_feature_duplicate",
                    message="shap bar importance features must be unique",
                    target=f"metrics.bars[{index}].feature",
                    observed=feature,
                )
            )
        seen_features.add(feature)
        importance_value = _require_numeric(item.get("importance_value"), label=f"layout_sidecar.metrics.bars[{index}].importance_value")
        if importance_value < 0.0:
            issues.append(
                _issue(
                    rule_id="importance_value_negative",
                    message="shap bar importance values must be non-negative",
                    target=f"metrics.bars[{index}].importance_value",
                    observed=importance_value,
                )
            )
        if importance_value > previous_importance + 1e-12:
            issues.append(
                _issue(
                    rule_id="importance_not_descending",
                    message="shap bar importance values must stay sorted descending by rank",
                    target=f"metrics.bars[{index}].importance_value",
                    observed=importance_value,
                )
            )
        previous_importance = importance_value

        bar_box_id = _require_non_empty_text(
            item.get("bar_box_id"),
            label=f"layout_sidecar.metrics.bars[{index}].bar_box_id",
        )
        feature_label_box_id = _require_non_empty_text(
            item.get("feature_label_box_id"),
            label=f"layout_sidecar.metrics.bars[{index}].feature_label_box_id",
        )
        value_label_box_id = _require_non_empty_text(
            item.get("value_label_box_id"),
            label=f"layout_sidecar.metrics.bars[{index}].value_label_box_id",
        )
        bar_box = bar_box_by_id.get(bar_box_id)
        feature_label_box = feature_label_box_by_id.get(feature_label_box_id)
        value_label_box = value_label_box_by_id.get(value_label_box_id)
        if bar_box is None:
            issues.append(
                _issue(
                    rule_id="importance_bar_missing",
                    message="shap bar importance metrics must reference an existing importance_bar box",
                    target=f"metrics.bars[{index}].bar_box_id",
                    observed=bar_box_id,
                )
            )
            continue
        if not _box_within_box(bar_box, panel):
            issues.append(
                _issue(
                    rule_id="importance_bar_outside_panel",
                    message="shap bar importance bars must stay within the declared panel region",
                    target=f"layout_boxes.{bar_box.box_id}",
                    box_refs=(bar_box.box_id, panel.box_id),
                )
            )
        if feature_label_box is None:
            issues.append(
                _issue(
                    rule_id="feature_label_missing",
                    message="shap bar importance metrics must reference an existing feature_label box",
                    target=f"metrics.bars[{index}].feature_label_box_id",
                    observed=feature_label_box_id,
                )
            )
        elif _boxes_overlap(feature_label_box, panel):
            issues.append(
                _issue(
                    rule_id="feature_label_panel_overlap",
                    message="feature labels must stay outside the shap bar importance panel",
                    target=f"layout_boxes.{feature_label_box.box_id}",
                    box_refs=(feature_label_box.box_id, panel.box_id),
                )
            )
        if value_label_box is None:
            issues.append(
                _issue(
                    rule_id="value_label_missing",
                    message="shap bar importance metrics must reference an existing value_label box",
                    target=f"metrics.bars[{index}].value_label_box_id",
                    observed=value_label_box_id,
                )
            )

    return issues
