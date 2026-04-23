from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_legend_panel_overlap,
    _check_required_box_types,
    _issue,
    _point_within_box,
    _require_non_empty_text,
    _require_numeric,
)

def _check_publication_omics_volcano_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(all_boxes, required_box_types=("legend", "subplot_y_axis_title")))
    issues.extend(_check_legend_panel_overlap(sidecar))

    legend_title = str(sidecar.metrics.get("legend_title") or "").strip()
    if not legend_title:
        issues.append(
            _issue(
                rule_id="legend_title_missing",
                message="omics volcano panel requires a non-empty legend_title",
                target="metrics.legend_title",
            )
        )

    effect_threshold = _require_numeric(sidecar.metrics.get("effect_threshold"), label="layout_sidecar.metrics.effect_threshold")
    if effect_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="effect_threshold_invalid",
                message="effect_threshold must be positive",
                target="metrics.effect_threshold",
                observed=effect_threshold,
            )
        )
    significance_threshold = _require_numeric(
        sidecar.metrics.get("significance_threshold"),
        label="layout_sidecar.metrics.significance_threshold",
    )
    if significance_threshold <= 0.0:
        issues.append(
            _issue(
                rule_id="significance_threshold_invalid",
                message="significance_threshold must be positive",
                target="metrics.significance_threshold",
                observed=significance_threshold,
            )
        )

    panels_payload = sidecar.metrics.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="omics volcano panel requires non-empty panels metrics",
                target="metrics.panels",
            )
        )
        return issues
    if len(panels_payload) > 2:
        issues.append(
            _issue(
                rule_id="panel_count_invalid",
                message="omics volcano panel supports at most two panels",
                target="metrics.panels",
                observed=len(panels_payload),
            )
        )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_boxes_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    supported_regulation_classes = {"upregulated", "downregulated", "background"}
    seen_panel_ids: set[str] = set()

    for panel_index, payload in enumerate(panels_payload):
        if not isinstance(payload, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_text(
            payload.get("panel_id"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="panel_id_not_unique",
                    message="panel_id must be unique across panels",
                    target=f"metrics.panels[{panel_index}].panel_id",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)

        panel_box_id = _require_non_empty_text(
            payload.get("panel_box_id"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].panel_box_id",
        )
        panel_box = panel_boxes_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="panel_box_id must resolve to an existing panel box",
                    target=f"metrics.panels[{panel_index}].panel_box_id",
                    observed=panel_box_id,
                )
            )

        panel_label_box_id = _require_non_empty_text(
            payload.get("panel_label_box_id"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].panel_label_box_id",
        )
        panel_label_box = layout_boxes_by_id.get(panel_label_box_id)
        if panel_label_box is None:
            issues.append(
                _issue(
                    rule_id="panel_label_box_missing",
                    message="panel_label_box_id must resolve to an existing layout box",
                    target=f"metrics.panels[{panel_index}].panel_label_box_id",
                    observed=panel_label_box_id,
                )
            )
        elif panel_box is not None and not _boxes_overlap(panel_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="panel_label_anchor_drift",
                    message="panel label must stay anchored inside its panel",
                    target=f"metrics.panels[{panel_index}].panel_label_box_id",
                    box_refs=(panel_label_box.box_id, panel_box.box_id),
                )
            )

        for field_name in ("panel_title_box_id", "x_axis_title_box_id"):
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.panels[{panel_index}].{field_name}",
            )
            if box_id in layout_boxes_by_id:
                continue
            issues.append(
                _issue(
                    rule_id="layout_box_missing",
                    message=f"{field_name} must resolve to an existing layout box",
                    target=f"metrics.panels[{panel_index}].{field_name}",
                    observed=box_id,
                )
            )

        threshold_pairs = (
            ("effect_threshold_left_box_id", "effect_threshold_box_missing", "effect_threshold_outside_panel"),
            ("effect_threshold_right_box_id", "effect_threshold_box_missing", "effect_threshold_outside_panel"),
            ("significance_threshold_box_id", "significance_threshold_box_missing", "significance_threshold_outside_panel"),
        )
        for field_name, missing_rule_id, outside_rule_id in threshold_pairs:
            box_id = _require_non_empty_text(
                payload.get(field_name),
                label=f"layout_sidecar.metrics.panels[{panel_index}].{field_name}",
            )
            threshold_box = guide_boxes_by_id.get(box_id)
            if threshold_box is None:
                issues.append(
                    _issue(
                        rule_id=missing_rule_id,
                        message=f"{field_name} must resolve to an existing guide box",
                        target=f"metrics.panels[{panel_index}].{field_name}",
                        observed=box_id,
                    )
                )
                continue
            if panel_box is not None and not _box_within_box(threshold_box, panel_box):
                issues.append(
                    _issue(
                        rule_id=outside_rule_id,
                        message=f"{field_name} must stay within its panel bounds",
                        target=f"guide_boxes.{threshold_box.box_id}",
                        box_refs=(threshold_box.box_id, panel_box.box_id),
                    )
                )

        points_payload = payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            issues.append(
                _issue(
                    rule_id="panel_points_missing",
                    message="every panel must expose non-empty points metrics",
                    target=f"metrics.panels[{panel_index}].points",
                )
            )
            continue

        seen_feature_labels: set[str] = set()
        for point_index, point in enumerate(points_payload):
            if not isinstance(point, dict):
                raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}] must be an object")
            feature_label = _require_non_empty_text(
                point.get("feature_label"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].feature_label",
            )
            if feature_label in seen_feature_labels:
                issues.append(
                    _issue(
                        rule_id="point_feature_label_not_unique",
                        message="feature_label must be unique within each panel",
                        target=f"metrics.panels[{panel_index}].points[{point_index}].feature_label",
                        observed=feature_label,
                    )
                )
            seen_feature_labels.add(feature_label)
            point_x = _require_numeric(
                point.get("x"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].x",
            )
            point_y = _require_numeric(
                point.get("y"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].y",
            )
            _require_numeric(
                point.get("effect_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].effect_value",
            )
            significance_value = _require_numeric(
                point.get("significance_value"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].significance_value",
            )
            if significance_value < 0.0:
                issues.append(
                    _issue(
                        rule_id="significance_value_negative",
                        message="significance_value must be non-negative",
                        target=f"metrics.panels[{panel_index}].points[{point_index}].significance_value",
                        observed=significance_value,
                    )
                )
            regulation_class = _require_non_empty_text(
                point.get("regulation_class"),
                label=f"layout_sidecar.metrics.panels[{panel_index}].points[{point_index}].regulation_class",
            )
            if regulation_class not in supported_regulation_classes:
                issues.append(
                    _issue(
                        rule_id="regulation_class_invalid",
                        message="regulation_class must use the supported vocabulary",
                        target=f"metrics.panels[{panel_index}].points[{point_index}].regulation_class",
                        observed=regulation_class,
                        expected=sorted(supported_regulation_classes),
                    )
                )
            if panel_box is not None and not _point_within_box(panel_box, x=point_x, y=point_y):
                issues.append(
                    _issue(
                        rule_id="point_outside_panel",
                        message="point coordinates must stay within the panel bounds",
                        target=f"metrics.panels[{panel_index}].points[{point_index}]",
                        box_refs=(panel_box.box_id,),
                    )
                )
            label_text = str(point.get("label_text") or "").strip()
            label_box_id = str(point.get("label_box_id") or "").strip()
            if label_text and not label_box_id:
                issues.append(
                    _issue(
                        rule_id="label_box_missing",
                        message="labeled volcano points must reference label_box_id",
                        target=f"metrics.panels[{panel_index}].points[{point_index}].label_box_id",
                    )
                )
                continue
            if label_box_id:
                label_box = layout_boxes_by_id.get(label_box_id)
                if label_box is None:
                    issues.append(
                        _issue(
                            rule_id="label_box_missing",
                            message="label_box_id must resolve to an existing layout box",
                            target=f"metrics.panels[{panel_index}].points[{point_index}].label_box_id",
                            observed=label_box_id,
                        )
                    )
                elif panel_box is not None and not _box_within_box(label_box, panel_box):
                    issues.append(
                        _issue(
                            rule_id="label_box_outside_panel",
                            message="label box must stay within the panel bounds",
                            target=f"layout_boxes.{label_box.box_id}",
                            box_refs=(label_box.box_id, panel_box.box_id),
                        )
                    )

    return issues
