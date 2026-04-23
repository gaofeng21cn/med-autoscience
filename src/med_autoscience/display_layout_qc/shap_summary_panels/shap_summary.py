from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _boxes_overlap, _check_boxes_within_device, _check_colorbar_panel_overlap, _check_pairwise_non_overlap, _check_required_box_types, _first_box_of_type, _issue, _layout_override_flag, _point_within_box, _primary_panel, _require_numeric

def _check_publication_shap_summary(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = ["zero_line", "colorbar", "x_axis_title", "feature_row"]
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(2, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    row_boxes = _boxes_of_type(sidecar.layout_boxes + sidecar.panel_boxes, "feature_row")
    issues.extend(_check_pairwise_non_overlap(row_boxes, rule_id="feature_row_overlap", target="feature_row"))
    feature_label_boxes = _boxes_of_type(sidecar.layout_boxes + sidecar.panel_boxes, "feature_label")
    issues.extend(_check_pairwise_non_overlap(feature_label_boxes, rule_id="feature_label_overlap", target="feature_label"))

    critical_boxes = tuple(
        box for box in all_boxes if box.box_type in {"title", "x_axis_title", "colorbar"}
    )
    issues.extend(_check_pairwise_non_overlap(critical_boxes, rule_id="critical_box_overlap", target="critical_boxes"))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    panel = _primary_panel(sidecar)
    zero_line = _first_box_of_type(sidecar.guide_boxes, "zero_line")
    if panel is not None and zero_line is not None and not _box_within_box(zero_line, panel):
        issues.append(
            _issue(
                rule_id="zero_line_outside_panel",
                message="zero-reference guide must stay within the shap panel region",
                target="guide_boxes.zero_line",
                box_refs=(zero_line.box_id, panel.box_id),
            )
        )
    if panel is not None:
        for row_box in row_boxes:
            if panel.y0 <= row_box.y0 <= panel.y1 and panel.y0 <= row_box.y1 <= panel.y1:
                continue
            issues.append(
                _issue(
                    rule_id="feature_row_outside_panel",
                    message="feature-row band must stay within the shap panel region",
                    target=f"layout_boxes.{row_box.box_id}",
                    box_refs=(row_box.box_id, panel.box_id),
                )
            )

    row_box_by_id = {box.box_id: box for box in row_boxes}
    points = sidecar.metrics.get("points")
    if points is None:
        return issues
    if not isinstance(points, list):
        raise ValueError("layout_sidecar.metrics.points must be a list when present")
    for index, point in enumerate(points):
        if not isinstance(point, dict):
            raise ValueError(f"layout_sidecar.metrics.points[{index}] must be an object")
        row_box_id = str(point.get("row_box_id") or "").strip()
        if not row_box_id:
            continue
        row_box = row_box_by_id.get(row_box_id)
        if row_box is None:
            continue
        y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.points[{index}].y")
        x_value = _require_numeric(point.get("x", row_box.x0), label=f"layout_sidecar.metrics.points[{index}].x")
        if _point_within_box(row_box, x=x_value, y=y_value):
            continue
        issues.append(
            _issue(
                rule_id="point_outside_feature_row",
                message="shap point must stay within its assigned feature row box",
                target=f"metrics.points[{index}]",
                observed={"x": x_value, "y": y_value},
                box_refs=(row_box.box_id,),
            )
        )

    label_box_by_id = {box.box_id: box for box in feature_label_boxes}
    raw_feature_labels = sidecar.metrics.get("feature_labels")
    if raw_feature_labels is None:
        raw_feature_labels = []
    if not isinstance(raw_feature_labels, list):
        raise ValueError("layout_sidecar.metrics.feature_labels must be a list when present")
    label_entry_by_row_box_id: dict[str, dict[str, str]] = {}
    for index, item in enumerate(raw_feature_labels):
        if not isinstance(item, dict):
            raise ValueError(f"layout_sidecar.metrics.feature_labels[{index}] must be an object")
        row_box_id = str(item.get("row_box_id") or "").strip()
        label_box_id = str(item.get("label_box_id") or "").strip()
        if not row_box_id or not label_box_id:
            raise ValueError(
                f"layout_sidecar.metrics.feature_labels[{index}] must include row_box_id and label_box_id"
            )
        label_entry_by_row_box_id[row_box_id] = {
            "label_box_id": label_box_id,
            "feature": str(item.get("feature") or "").strip(),
        }

    for row_box in row_boxes:
        label_entry = label_entry_by_row_box_id.get(row_box.box_id)
        if label_entry is None:
            issues.append(
                _issue(
                    rule_id="feature_label_missing",
                    message="shap summary requires a feature label annotation for every feature row",
                    target=f"metrics.feature_labels.{row_box.box_id}",
                    box_refs=(row_box.box_id,),
                )
            )
            continue
        label_box = label_box_by_id.get(label_entry["label_box_id"])
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="feature_label_missing",
                    message="feature label annotation must reference an existing feature_label box",
                    target=f"metrics.feature_labels.{row_box.box_id}",
                    observed={"label_box_id": label_entry["label_box_id"]},
                    box_refs=(row_box.box_id,),
                )
            )
            continue
        if panel is not None and _boxes_overlap(label_box, panel):
            issues.append(
                _issue(
                    rule_id="feature_label_panel_overlap",
                    message="feature label annotation must stay outside the shap panel region",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(row_box.box_id, label_box.box_id, panel.box_id),
                )
            )
        label_center_y = (label_box.y0 + label_box.y1) / 2.0
        if row_box.y0 <= label_center_y <= row_box.y1:
            continue
        issues.append(
            _issue(
                rule_id="feature_label_row_misaligned",
                message="feature label annotation must stay vertically aligned to its feature row band",
                target=f"layout_boxes.{label_box.box_id}",
                observed={"label_center_y": label_center_y},
                expected={"row_y0": row_box.y0, "row_y1": row_box.y1},
                box_refs=(row_box.box_id, label_box.box_id),
            )
        )
    return issues
