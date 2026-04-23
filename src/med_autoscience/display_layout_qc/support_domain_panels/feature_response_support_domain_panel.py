from __future__ import annotations

from ..shared import Any, LayoutSidecar, _all_boxes, _box_within_box, _boxes_of_type, _check_boxes_within_device, _check_composite_panel_label_anchors, _check_pairwise_non_overlap, _check_required_box_types, _issue, _layout_override_flag, _point_within_box, _require_numeric

def _check_publication_feature_response_support_domain_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "subplot_y_axis_title",
        "panel_label",
        "support_domain_reference_label",
        "support_label",
        "legend_box",
        "support_domain_reference_line",
        "support_domain_segment",
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
            "subplot_x_axis_title",
            "subplot_y_axis_title",
            "panel_label",
            "support_domain_reference_label",
            "support_label",
        }
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))

    legend_labels = sidecar.metrics.get("legend_labels")
    expected_legend_labels = [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]
    if legend_labels != expected_legend_labels:
        issues.append(
            _issue(
                rule_id="legend_labels_invalid",
                message=(
                    "feature-response support-domain legend must declare exactly Response curve, "
                    "Observed support, Subgroup support, Bin support, and Extrapolation reminder"
                ),
                target="metrics.legend_labels",
                observed=legend_labels,
                expected=expected_legend_labels,
            )
        )

    metrics_panels = sidecar.metrics.get("panels")
    if not isinstance(metrics_panels, list) or not metrics_panels:
        issues.append(
            _issue(
                rule_id="panels_missing",
                message="feature-response support-domain qc requires non-empty panel metrics",
                target="metrics.panels",
            )
        )
        return issues

    if len(panel_boxes) != len(metrics_panels):
        issues.append(
            _issue(
                rule_id="panel_count_mismatch",
                message="feature-response support-domain panel count must match metrics.panels",
                target="panel_boxes",
                observed={"panel_boxes": len(panel_boxes)},
                expected={"metrics.panels": len(metrics_panels)},
            )
        )

    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    guide_box_by_id = {box.box_id: box for box in sidecar.guide_boxes}
    panel_box_by_id = {box.box_id: box for box in panel_boxes}
    label_panel_map: dict[str, str] = {}
    seen_panel_ids: set[str] = set()
    allowed_support_kinds = {
        "observed_support",
        "subgroup_support",
        "bin_support",
        "extrapolation_warning",
    }

    for panel_index, panel_metric in enumerate(metrics_panels):
        if not isinstance(panel_metric, dict):
            raise ValueError(f"layout_sidecar.metrics.panels[{panel_index}] must be an object")
        panel_id = str(panel_metric.get("panel_id") or "").strip()
        panel_label = str(panel_metric.get("panel_label") or "").strip()
        title = str(panel_metric.get("title") or "").strip()
        x_label = str(panel_metric.get("x_label") or "").strip()
        feature = str(panel_metric.get("feature") or "").strip()
        reference_label = str(panel_metric.get("reference_label") or "").strip()
        _require_numeric(
            panel_metric.get("reference_value"),
            label=f"layout_sidecar.metrics.panels[{panel_index}].reference_value",
        )
        if not panel_id or not panel_label or not title or not x_label or not feature or not reference_label:
            issues.append(
                _issue(
                    rule_id="panel_metric_missing",
                    message="feature-response support-domain panel metrics must declare panel metadata and reference labels",
                    target=f"metrics.panels[{panel_index}]",
                )
            )
            continue
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="duplicate_panel_id",
                    message="feature-response support-domain panel_id values must stay unique",
                    target="metrics.panels",
                    observed=panel_id,
                )
            )
            continue
        seen_panel_ids.add(panel_id)

        panel_box_id = str(panel_metric.get("panel_box_id") or "").strip() or f"panel_{panel_label}"
        panel_box = panel_box_by_id.get(panel_box_id)
        if panel_box is None:
            issues.append(
                _issue(
                    rule_id="panel_box_missing",
                    message="feature-response support-domain metrics must reference an existing panel box",
                    target=f"metrics.panels[{panel_index}]",
                    observed={"panel_box_id": panel_box_id},
                )
            )
            continue
        label_panel_map[f"panel_label_{panel_label}"] = panel_box.box_id

        response_points = panel_metric.get("response_points")
        if not isinstance(response_points, list) or not response_points:
            issues.append(
                _issue(
                    rule_id="response_points_missing",
                    message="feature-response support-domain panels require non-empty response_points",
                    target=f"metrics.panels[{panel_index}].response_points",
                    box_refs=(panel_box.box_id,),
                )
            )
        else:
            for point_index, point in enumerate(response_points):
                if not isinstance(point, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.panels[{panel_index}].response_points[{point_index}] must be an object"
                    )
                x_value = _require_numeric(
                    point.get("x"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].response_points[{point_index}].x",
                )
                y_value = _require_numeric(
                    point.get("y"),
                    label=f"layout_sidecar.metrics.panels[{panel_index}].response_points[{point_index}].y",
                )
                if _point_within_box(panel_box, x=x_value, y=y_value):
                    continue
                issues.append(
                    _issue(
                        rule_id="response_point_outside_panel",
                        message="feature-response support-domain response points must stay within the declared panel region",
                        target=f"metrics.panels[{panel_index}].response_points[{point_index}]",
                        observed={"x": x_value, "y": y_value},
                        box_refs=(panel_box.box_id,),
                    )
                )

        reference_line_box_id = (
            str(panel_metric.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_label}"
        )
        reference_line_box = guide_box_by_id.get(reference_line_box_id)
        if reference_line_box is None:
            issues.append(
                _issue(
                    rule_id="reference_line_missing",
                    message="feature-response support-domain requires one reference line per panel",
                    target=f"metrics.panels[{panel_index}].reference_line_box_id",
                    observed={"reference_line_box_id": reference_line_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_line_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_line_outside_panel",
                    message="feature-response support-domain reference line must stay within the panel region",
                    target=f"guide_boxes.{reference_line_box.box_id}",
                    box_refs=(reference_line_box.box_id, panel_box.box_id),
                )
            )

        reference_label_box_id = (
            str(panel_metric.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_label}"
        )
        reference_label_box = layout_box_by_id.get(reference_label_box_id)
        if reference_label_box is None:
            issues.append(
                _issue(
                    rule_id="reference_label_missing",
                    message="feature-response support-domain requires one reference label per panel",
                    target=f"metrics.panels[{panel_index}].reference_label_box_id",
                    observed={"reference_label_box_id": reference_label_box_id},
                    box_refs=(panel_box.box_id,),
                )
            )
        elif not _box_within_box(reference_label_box, panel_box):
            issues.append(
                _issue(
                    rule_id="reference_label_outside_panel",
                    message="feature-response support-domain reference label must stay within the panel region",
                    target=f"layout_boxes.{reference_label_box.box_id}",
                    box_refs=(reference_label_box.box_id, panel_box.box_id),
                )
            )

        support_segments = panel_metric.get("support_segments")
        if not isinstance(support_segments, list) or not support_segments:
            issues.append(
                _issue(
                    rule_id="support_segments_missing",
                    message="feature-response support-domain panels require non-empty support_segments",
                    target=f"metrics.panels[{panel_index}].support_segments",
                    box_refs=(panel_box.box_id,),
                )
            )
            continue

        seen_segment_ids: set[str] = set()
        for segment_index, segment in enumerate(support_segments):
            if not isinstance(segment, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.panels[{panel_index}].support_segments[{segment_index}] must be an object"
                )
            segment_id = str(segment.get("segment_id") or "").strip()
            support_kind = str(segment.get("support_kind") or "").strip()
            if not segment_id:
                issues.append(
                    _issue(
                        rule_id="support_segment_id_missing",
                        message="feature-response support-domain support segments must declare segment_id",
                        target=f"metrics.panels[{panel_index}].support_segments[{segment_index}]",
                    )
                )
            elif segment_id in seen_segment_ids:
                issues.append(
                    _issue(
                        rule_id="duplicate_support_segment_id",
                        message="feature-response support-domain segment_id values must stay unique within each panel",
                        target=f"metrics.panels[{panel_index}].support_segments",
                        observed=segment_id,
                    )
                )
            else:
                seen_segment_ids.add(segment_id)

            if support_kind not in allowed_support_kinds:
                issues.append(
                    _issue(
                        rule_id="support_kind_invalid",
                        message="feature-response support-domain support_kind must stay within the admitted set",
                        target=f"metrics.panels[{panel_index}].support_segments[{segment_index}].support_kind",
                        observed=support_kind,
                        expected=sorted(allowed_support_kinds),
                    )
                )

            segment_box_id = (
                str(segment.get("segment_box_id") or "").strip() or f"support_segment_{panel_label}_{segment_index + 1}"
            )
            segment_box = guide_box_by_id.get(segment_box_id)
            if segment_box is None:
                issues.append(
                    _issue(
                        rule_id="support_segment_missing",
                        message="feature-response support-domain segments require explicit guide boxes",
                        target=f"metrics.panels[{panel_index}].support_segments[{segment_index}].segment_box_id",
                        observed={"segment_box_id": segment_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif not _box_within_box(segment_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="support_segment_outside_panel",
                        message="feature-response support-domain support segments must stay within the declared panel region",
                        target=f"guide_boxes.{segment_box.box_id}",
                        box_refs=(segment_box.box_id, panel_box.box_id),
                    )
                )

            label_box_id = (
                str(segment.get("label_box_id") or "").strip() or f"support_label_{panel_label}_{segment_index + 1}"
            )
            label_box = layout_box_by_id.get(label_box_id)
            if label_box is None:
                issues.append(
                    _issue(
                        rule_id="support_label_missing",
                        message="feature-response support-domain segments require explicit support labels",
                        target=f"metrics.panels[{panel_index}].support_segments[{segment_index}].label_box_id",
                        observed={"label_box_id": label_box_id},
                        box_refs=(panel_box.box_id,),
                    )
                )
            elif not _box_within_box(label_box, panel_box):
                issues.append(
                    _issue(
                        rule_id="support_label_outside_panel",
                        message="feature-response support-domain support labels must stay within the declared panel region",
                        target=f"layout_boxes.{label_box.box_id}",
                        box_refs=(label_box.box_id, panel_box.box_id),
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
