from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_overlap,
    _check_boxes_within_device,
    _check_pairwise_non_overlap,
    _check_required_box_types,
    _first_box_of_type,
    _issue,
    _layout_override_flag,
    _require_numeric,
)

def _check_publication_generalizability_subgroup_composite_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    required_box_types = [
        "panel_title",
        "subplot_x_axis_title",
        "panel_label",
        "overview_row_label",
        "support_label",
        "overview_metric_marker",
        "subgroup_row_label",
        "estimate_marker",
        "ci_segment",
    ]
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    comparator_label = str(metrics.get("comparator_label") or "").strip()
    if comparator_label:
        required_box_types.append("overview_comparator_marker")
        required_box_types.append("legend")
    if _layout_override_flag(sidecar, "show_figure_title", False):
        required_box_types.insert(0, "title")
    issues.extend(_check_required_box_types(all_boxes, required_box_types=tuple(required_box_types)))

    panel_boxes = tuple(box for box in sidecar.panel_boxes if box.box_type == "panel")
    issues.extend(_check_pairwise_non_overlap(panel_boxes, rule_id="panel_overlap", target="panel"))
    panel_boxes_by_id = {box.box_id: box for box in panel_boxes}
    overview_panel = panel_boxes_by_id.get("overview_panel")
    subgroup_panel = panel_boxes_by_id.get("subgroup_panel")
    if overview_panel is None or subgroup_panel is None:
        issues.append(
            _issue(
                rule_id="panel_missing",
                message="generalizability subgroup composite qc requires overview_panel and subgroup_panel",
                target="panel_boxes",
            )
        )
        return issues

    text_boxes = tuple(
        box for box in sidecar.layout_boxes if box.box_type in {"title", "panel_title", "panel_label", "subplot_x_axis_title"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    legend_box = _first_box_of_type(sidecar.guide_boxes, "legend")

    if comparator_label:
        legend_title = str(metrics.get("legend_title") or "").strip()
        legend_labels = metrics.get("legend_labels")
        if not legend_title:
            issues.append(
                _issue(
                    rule_id="legend_title_invalid",
                    message="composite panel legend_title must be non-empty when comparator_label is declared",
                    target="metrics.legend_title",
                )
            )
        if not isinstance(legend_labels, list) or len([str(item).strip() for item in legend_labels if str(item).strip()]) < 2:
            issues.append(
                _issue(
                    rule_id="legend_labels_missing",
                    message="composite panel legend_labels must contain at least two non-empty labels when comparator_label is declared",
                    target="metrics.legend_labels",
                )
            )
        if legend_box is None:
            issues.append(
                _issue(
                    rule_id="legend_missing",
                    message="composite panel requires a legend when comparator_label is declared",
                    target="guide_boxes.legend",
                )
            )

    overview_rows = metrics.get("overview_rows")
    if not isinstance(overview_rows, list) or not overview_rows:
        issues.append(
            _issue(
                rule_id="overview_rows_missing",
                message="composite qc requires non-empty overview_rows metrics",
                target="metrics.overview_rows",
            )
        )
        return issues
    subgroup_rows = metrics.get("subgroup_rows")
    if not isinstance(subgroup_rows, list) or not subgroup_rows:
        issues.append(
            _issue(
                rule_id="subgroup_rows_missing",
                message="composite qc requires non-empty subgroup_rows metrics",
                target="metrics.subgroup_rows",
            )
        )
        return issues

    for row_index, row in enumerate(overview_rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.overview_rows[{row_index}] must be an object")
        label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
        support_label_box = layout_box_by_id.get(str(row.get("support_label_box_id") or "").strip())
        metric_marker_box = layout_box_by_id.get(str(row.get("metric_marker_box_id") or "").strip())
        comparator_marker_box = layout_box_by_id.get(str(row.get("comparator_marker_box_id") or "").strip())
        if label_box is None or support_label_box is None or metric_marker_box is None:
            issues.append(
                _issue(
                    rule_id="overview_row_box_missing",
                    message="overview rows must reference label, support, and metric marker boxes",
                    target=f"metrics.overview_rows[{row_index}]",
                    box_refs=(overview_panel.box_id,),
                )
            )
            continue
        if _boxes_overlap(label_box, overview_panel):
            issues.append(
                _issue(
                    rule_id="overview_row_label_panel_overlap",
                    message="overview row label must stay outside the overview panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, overview_panel.box_id),
                )
            )
        if not _box_within_box(support_label_box, overview_panel):
            issues.append(
                _issue(
                    rule_id="support_label_outside_panel",
                    message="overview support label must stay within the overview panel",
                    target=f"layout_boxes.{support_label_box.box_id}",
                    box_refs=(support_label_box.box_id, overview_panel.box_id),
                )
            )
        if not _box_within_box(metric_marker_box, overview_panel):
            issues.append(
                _issue(
                    rule_id="overview_metric_marker_outside_panel",
                    message="overview metric marker must stay within the overview panel",
                    target=f"layout_boxes.{metric_marker_box.box_id}",
                    box_refs=(metric_marker_box.box_id, overview_panel.box_id),
                )
            )
        if comparator_label:
            if comparator_marker_box is None:
                issues.append(
                    _issue(
                        rule_id="overview_comparator_marker_missing",
                        message="overview comparator marker must exist when comparator_label is declared",
                        target=f"metrics.overview_rows[{row_index}]",
                        box_refs=(overview_panel.box_id,),
                    )
                )
            elif not _box_within_box(comparator_marker_box, overview_panel):
                issues.append(
                    _issue(
                        rule_id="overview_comparator_marker_outside_panel",
                        message="overview comparator marker must stay within the overview panel",
                        target=f"layout_boxes.{comparator_marker_box.box_id}",
                        box_refs=(comparator_marker_box.box_id, overview_panel.box_id),
                    )
                )

    for row_index, row in enumerate(subgroup_rows):
        if not isinstance(row, dict):
            raise ValueError(f"layout_sidecar.metrics.subgroup_rows[{row_index}] must be an object")
        lower = _require_numeric(row.get("lower"), label=f"layout_sidecar.metrics.subgroup_rows[{row_index}].lower")
        estimate = _require_numeric(
            row.get("estimate"), label=f"layout_sidecar.metrics.subgroup_rows[{row_index}].estimate"
        )
        upper = _require_numeric(row.get("upper"), label=f"layout_sidecar.metrics.subgroup_rows[{row_index}].upper")
        if not (lower <= estimate <= upper):
            issues.append(
                _issue(
                    rule_id="estimate_outside_interval",
                    message="subgroup estimate must lie within the confidence interval",
                    target=f"metrics.subgroup_rows[{row_index}]",
                    observed={"lower": lower, "estimate": estimate, "upper": upper},
                )
            )
        label_box = layout_box_by_id.get(str(row.get("label_box_id") or "").strip())
        estimate_box = layout_box_by_id.get(str(row.get("estimate_box_id") or "").strip())
        ci_box = layout_box_by_id.get(str(row.get("ci_box_id") or "").strip())
        if label_box is None or estimate_box is None or ci_box is None:
            issues.append(
                _issue(
                    rule_id="subgroup_row_box_missing",
                    message="subgroup rows must reference label, estimate, and confidence-interval boxes",
                    target=f"metrics.subgroup_rows[{row_index}]",
                    box_refs=(subgroup_panel.box_id,),
                )
            )
            continue
        if _boxes_overlap(label_box, subgroup_panel):
            issues.append(
                _issue(
                    rule_id="subgroup_row_label_panel_overlap",
                    message="subgroup row label must stay outside the subgroup panel",
                    target=f"layout_boxes.{label_box.box_id}",
                    box_refs=(label_box.box_id, subgroup_panel.box_id),
                )
            )
        if not _box_within_box(estimate_box, subgroup_panel):
            issues.append(
                _issue(
                    rule_id="estimate_marker_outside_panel",
                    message="subgroup estimate marker must stay within the subgroup panel",
                    target=f"layout_boxes.{estimate_box.box_id}",
                    box_refs=(estimate_box.box_id, subgroup_panel.box_id),
                )
            )
        if not _box_within_box(ci_box, subgroup_panel):
            issues.append(
                _issue(
                    rule_id="ci_segment_outside_panel",
                    message="subgroup confidence interval must stay within the subgroup panel",
                    target=f"layout_boxes.{ci_box.box_id}",
                    box_refs=(ci_box.box_id, subgroup_panel.box_id),
                )
            )
    return issues
