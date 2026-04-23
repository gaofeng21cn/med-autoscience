from __future__ import annotations

from ..shared import (
    Any,
    LayoutSidecar,
    _all_boxes,
    _box_within_box,
    _boxes_of_type,
    _check_boxes_within_device,
    _check_legend_panel_overlap,
    _check_required_box_types,
    _first_box_of_type,
    _issue,
    _require_numeric,
)

def _check_publication_multicenter_overview(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(_check_required_box_types(_all_boxes(sidecar), required_box_types=("y_axis_title", "coverage_bar")))
    issues.extend(_check_legend_panel_overlap(sidecar))
    legend = _first_box_of_type(sidecar.guide_boxes, "legend")
    if legend is None:
        issues.append(
            _issue(
                rule_id="missing_legend",
                message="multicenter overview requires a split legend in the footer band",
                target="legend",
                expected="present",
            )
        )
    elif sidecar.panel_boxes:
        footer_ceiling = min(panel_box.y0 for panel_box in sidecar.panel_boxes)
        if legend.y1 > footer_ceiling - 0.005:
            issues.append(
                _issue(
                    rule_id="legend_footer_band_drift",
                    message="multicenter legend must stay below the panel band in the footer region",
                    target="legend",
                    box_refs=(legend.box_id,),
                    observed={"legend_y1": legend.y1},
                    expected={"maximum_y1": footer_ceiling - 0.005},
                )
            )
    legend_title = str(sidecar.metrics.get("legend_title") or "").strip()
    if legend_title != "Split":
        issues.append(
            _issue(
                rule_id="legend_title_invalid",
                message="multicenter overview legend title must stay `Split`",
                target="metrics.legend_title",
                observed=legend_title,
                expected="Split",
            )
        )
    legend_labels = sidecar.metrics.get("legend_labels")
    if not isinstance(legend_labels, list) or not legend_labels:
        issues.append(
            _issue(
                rule_id="legend_labels_missing",
                message="multicenter overview requires explicit legend labels for split semantics",
                target="metrics.legend_labels",
                expected=["Train", "Validation"],
            )
        )
    else:
        normalized_labels = [str(item or "").strip() for item in legend_labels]
        if normalized_labels != ["Train", "Validation"]:
            issues.append(
                _issue(
                    rule_id="legend_labels_invalid",
                    message="multicenter overview legend labels must stay in `Train`, `Validation` order",
                    target="metrics.legend_labels",
                    observed=normalized_labels,
                    expected=["Train", "Validation"],
                )
            )

    center_event_panel = _first_box_of_type(sidecar.panel_boxes, "center_event_panel")
    if center_event_panel is None:
        issues.append(
            _issue(
                rule_id="center_event_panel_missing",
                message="multicenter overview requires the center-event panel",
                target="panel_boxes",
                expected="center_event_panel",
            )
        )

    coverage_panels_by_box_id = {box.box_id for box in _boxes_of_type(sidecar.panel_boxes, "coverage_panel")}
    required_coverage_box_ids = {
        "coverage_panel_wide_left",
        "coverage_panel_top_right",
        "coverage_panel_bottom_right",
    }
    for missing_box_id in sorted(required_coverage_box_ids - coverage_panels_by_box_id):
        issues.append(
            _issue(
                rule_id="coverage_panel_missing",
                message="multicenter overview requires all three coverage panel regions",
                target="panel_boxes",
                expected=missing_box_id,
            )
        )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    panel_labels = {box.box_id: box for box in _boxes_of_type(sidecar.layout_boxes, "panel_label")}
    required_panel_labels = {
        "panel_label_A": "center_event_panel",
        "panel_label_B": "coverage_panel_wide_left",
        "panel_label_C": "coverage_panel_right_stack",
    }
    for label_box_id, panel_box_id in required_panel_labels.items():
        label_box = panel_labels.get(label_box_id)
        if label_box is None:
            issues.append(
                _issue(
                    rule_id="missing_panel_label",
                    message="multicenter overview requires explicit A/B/C panel labels",
                    target="layout_boxes",
                    expected=label_box_id,
                )
            )
            continue
        parent_panel = panel_boxes_by_id.get(panel_box_id)
        if parent_panel is None and panel_box_id == "coverage_panel_right_stack":
            parent_panel = panel_boxes_by_id.get("coverage_panel_top_right")
        if parent_panel is None:
            continue
        if not _box_within_box(label_box, parent_panel):
            issues.append(
                _issue(
                    rule_id="panel_label_out_of_panel",
                    message="multicenter panel labels must stay within their declared panel region",
                    target="panel_label",
                    box_refs=(label_box.box_id, parent_panel.box_id),
                )
            )
            continue
        panel_width = max(parent_panel.x1 - parent_panel.x0, 1e-9)
        panel_height = max(parent_panel.y1 - parent_panel.y0, 1e-9)
        if (
            label_box.x0 > parent_panel.x0 + panel_width * 0.18
            or label_box.y1 < parent_panel.y1 - panel_height * 0.18
        ):
            issues.append(
                _issue(
                    rule_id="panel_label_anchor_drift",
                    message="multicenter panel labels must stay near the parent panel top-left anchor",
                    target="panel_label",
                    box_refs=(label_box.box_id, parent_panel.box_id),
                )
            )

    center_event_counts = sidecar.metrics.get("center_event_counts")
    if not isinstance(center_event_counts, list) or not center_event_counts:
        issues.append(
            _issue(
                rule_id="center_event_counts_missing",
                message="multicenter overview requires non-empty center_event_counts metrics",
                target="metrics.center_event_counts",
            )
        )
    else:
        seen_labels: set[str] = set()
        for index, item in enumerate(center_event_counts):
            if not isinstance(item, dict):
                raise ValueError(f"layout_sidecar.metrics.center_event_counts[{index}] must be an object")
            label = str(item.get("center_label") or "").strip()
            if not label:
                raise ValueError(f"layout_sidecar.metrics.center_event_counts[{index}].center_label must be non-empty")
            if label in seen_labels:
                issues.append(
                    _issue(
                        rule_id="center_event_label_not_unique",
                        message="center-event labels must be unique",
                        target=f"metrics.center_event_counts[{index}]",
                        observed=label,
                    )
                )
            seen_labels.add(label)
            event_count = _require_numeric(
                item.get("event_count"),
                label=f"layout_sidecar.metrics.center_event_counts[{index}].event_count",
            )
            if event_count < 0:
                issues.append(
                    _issue(
                        rule_id="center_event_count_negative",
                        message="center-event counts must be non-negative",
                        target=f"metrics.center_event_counts[{index}]",
                        observed=event_count,
                    )
                )

    coverage_panels = sidecar.metrics.get("coverage_panels")
    if not isinstance(coverage_panels, list) or not coverage_panels:
        issues.append(
            _issue(
                rule_id="coverage_panels_missing",
                message="multicenter overview requires coverage_panels metrics",
                target="metrics.coverage_panels",
            )
        )
        return issues

    seen_panel_ids: set[str] = set()
    seen_layout_roles: set[str] = set()
    for index, panel in enumerate(coverage_panels):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.coverage_panels[{index}] must be an object")
        panel_id = str(panel.get("panel_id") or "").strip()
        if not panel_id:
            raise ValueError(f"layout_sidecar.metrics.coverage_panels[{index}].panel_id must be non-empty")
        if panel_id in seen_panel_ids:
            issues.append(
                _issue(
                    rule_id="coverage_panel_id_not_unique",
                    message="coverage panel ids must be unique",
                    target=f"metrics.coverage_panels[{index}]",
                    observed=panel_id,
                )
            )
        seen_panel_ids.add(panel_id)
        layout_role = str(panel.get("layout_role") or "").strip()
        if not layout_role:
            raise ValueError(f"layout_sidecar.metrics.coverage_panels[{index}].layout_role must be non-empty")
        seen_layout_roles.add(layout_role)
        bars = panel.get("bars")
        if not isinstance(bars, list) or not bars:
            issues.append(
                _issue(
                    rule_id="coverage_panel_bars_missing",
                    message="coverage panels must contain at least one bar",
                    target=f"metrics.coverage_panels[{index}].bars",
                )
            )
            continue
        for bar_index, bar in enumerate(bars):
            if not isinstance(bar, dict):
                raise ValueError(f"layout_sidecar.metrics.coverage_panels[{index}].bars[{bar_index}] must be an object")
            count = _require_numeric(
                bar.get("count"),
                label=f"layout_sidecar.metrics.coverage_panels[{index}].bars[{bar_index}].count",
            )
            if count < 0:
                issues.append(
                    _issue(
                        rule_id="coverage_bar_count_negative",
                        message="coverage bar counts must be non-negative",
                        target=f"metrics.coverage_panels[{index}].bars[{bar_index}]",
                        observed=count,
                    )
                )

    required_layout_roles = {"wide_left", "top_right", "bottom_right"}
    for missing_role in sorted(required_layout_roles - seen_layout_roles):
        issues.append(
            _issue(
                rule_id="coverage_panel_layout_role_missing",
                message="multicenter overview requires wide_left, top_right, and bottom_right coverage panels",
                target="metrics.coverage_panels",
                expected=missing_role,
            )
        )

    return issues
