from __future__ import annotations

from ..shared import Any, LayoutSidecar, _check_composite_panel_label_anchors, _issue, _require_numeric
from .storyboard import _check_publication_atlas_spatial_trajectory_storyboard_panel

def _check_publication_atlas_spatial_trajectory_context_support_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_publication_atlas_spatial_trajectory_storyboard_panel(sidecar)

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    if "panel_support" not in panel_boxes_by_id:
        issues.append(
            _issue(
                rule_id="missing_box",
                message="context-support panel requires a support panel",
                target="panel_support",
                expected="present",
            )
        )
    for box_id, message in (
        ("support_panel_title", "context-support panel requires a support panel title"),
        ("support_x_axis_title", "context-support panel requires a support x-axis title"),
        ("support_y_axis_title", "context-support panel requires a support y-axis title"),
        ("panel_label_F", "context-support panel requires a panel label F"),
    ):
        if box_id in layout_boxes_by_id:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=box_id, expected="present"))

    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={"panel_label_F": "panel_support"},
            allow_left_overhang_ratio=0.10,
        )
    )

    def _normalize_unique_labels(
        metric_key: str,
        missing_rule: str,
        empty_rule: str,
        duplicate_rule: str,
        message: str,
    ) -> list[str]:
        labels = sidecar.metrics.get(metric_key)
        if not isinstance(labels, list) or not labels:
            issues.append(_issue(rule_id=missing_rule, message=message, target=f"metrics.{metric_key}"))
            return []
        normalized: list[str] = []
        seen: set[str] = set()
        for index, item in enumerate(labels):
            label = str(item or "").strip()
            if not label:
                issues.append(
                    _issue(
                        rule_id=empty_rule,
                        message=f"{metric_key} labels must be non-empty",
                        target=f"metrics.{metric_key}[{index}]",
                    )
                )
                continue
            if label in seen:
                issues.append(
                    _issue(
                        rule_id=duplicate_rule,
                        message=f"{metric_key} label `{label}` must be unique",
                        target=f"metrics.{metric_key}",
                        observed=label,
                    )
                )
                continue
            seen.add(label)
            normalized.append(label)
        return normalized

    normalized_state_labels = _normalize_unique_labels(
        "state_labels",
        "state_labels_missing",
        "empty_state_label",
        "duplicate_state_label",
        "context-support panel requires explicit non-empty state_labels metrics",
    )
    normalized_context_labels = _normalize_unique_labels(
        "context_labels",
        "context_labels_missing",
        "empty_context_label",
        "duplicate_context_label",
        "context-support panel requires explicit non-empty context_labels metrics",
    )
    normalized_context_kinds = _normalize_unique_labels(
        "context_kinds",
        "context_kinds_missing",
        "empty_context_kind",
        "duplicate_context_kind",
        "context-support panel requires explicit non-empty context_kinds metrics",
    )
    required_context_kinds = {"atlas_density", "spatial_coverage", "trajectory_coverage"}
    if normalized_context_kinds and set(normalized_context_kinds) != required_context_kinds:
        issues.append(
            _issue(
                rule_id="support_context_kind_set_mismatch",
                message="context_kinds must cover atlas_density, spatial_coverage, and trajectory_coverage",
                target="metrics.context_kinds",
                observed=sorted(normalized_context_kinds),
                expected=sorted(required_context_kinds),
            )
        )
    if normalized_context_labels and normalized_context_kinds and len(normalized_context_labels) != len(normalized_context_kinds):
        issues.append(
            _issue(
                rule_id="support_context_label_kind_count_mismatch",
                message="context_labels and context_kinds must stay aligned one-to-one",
                target="metrics.context_kinds",
                observed=len(normalized_context_kinds),
                expected=len(normalized_context_labels),
            )
        )

    support_scale_label = str(sidecar.metrics.get("support_scale_label") or "").strip()
    if not support_scale_label:
        issues.append(
            _issue(
                rule_id="support_scale_label_missing",
                message="context-support panel requires a non-empty support_scale_label",
                target="metrics.support_scale_label",
            )
        )

    support_cells = sidecar.metrics.get("support_cells")
    if not isinstance(support_cells, list) or not support_cells:
        issues.append(
            _issue(
                rule_id="support_cells_missing",
                message="context-support panel requires non-empty support_cells metrics",
                target="metrics.support_cells",
            )
        )
        return issues

    observed_contexts: set[str] = set()
    observed_states: set[str] = set()
    seen_coordinates: set[tuple[str, str]] = set()
    for index, cell in enumerate(support_cells):
        if not isinstance(cell, dict):
            raise ValueError(f"layout_sidecar.metrics.support_cells[{index}] must be an object")
        context_label = str(cell.get("x") or "").strip()
        state_label = str(cell.get("y") or "").strip()
        if not context_label or not state_label:
            issues.append(
                _issue(
                    rule_id="support_cell_coordinate_missing",
                    message="support cell must include non-empty x and y labels",
                    target=f"metrics.support_cells[{index}]",
                )
            )
            continue
        if normalized_context_labels and context_label not in normalized_context_labels:
            issues.append(
                _issue(
                    rule_id="support_cell_context_unknown",
                    message="support cell x labels must stay inside declared context_labels",
                    target=f"metrics.support_cells[{index}].x",
                    observed=context_label,
                    expected=normalized_context_labels,
                )
            )
        if normalized_state_labels and state_label not in normalized_state_labels:
            issues.append(
                _issue(
                    rule_id="support_cell_state_unknown",
                    message="support cell y labels must stay inside declared state_labels",
                    target=f"metrics.support_cells[{index}].y",
                    observed=state_label,
                    expected=normalized_state_labels,
                )
            )
        coordinate = (context_label, state_label)
        if coordinate in seen_coordinates:
            issues.append(
                _issue(
                    rule_id="duplicate_support_cell",
                    message="support cell coordinates must be unique",
                    target=f"metrics.support_cells[{index}]",
                    observed={"x": context_label, "y": state_label},
                )
            )
            continue
        seen_coordinates.add(coordinate)
        observed_contexts.add(context_label)
        observed_states.add(state_label)
        value = _require_numeric(
            cell.get("value"),
            label=f"layout_sidecar.metrics.support_cells[{index}].value",
        )
        if 0.0 <= value <= 1.0:
            continue
        issues.append(
            _issue(
                rule_id="support_value_out_of_range",
                message="support cell values must stay within [0, 1]",
                target=f"metrics.support_cells[{index}].value",
                observed=value,
            )
        )
    expected_coordinates = {
        (context_label, state_label) for state_label in normalized_state_labels for context_label in normalized_context_labels
    }
    if (
        normalized_context_labels
        and normalized_state_labels
        and (
            observed_contexts != set(normalized_context_labels)
            or observed_states != set(normalized_state_labels)
            or seen_coordinates != expected_coordinates
        )
    ):
        issues.append(
            _issue(
                rule_id="support_grid_incomplete",
                message="support grid must cover every declared context/state coordinate exactly once",
                target="metrics.support_cells",
                observed={"cells": len(seen_coordinates)},
                expected={"cells": len(expected_coordinates)},
            )
        )

    return issues
