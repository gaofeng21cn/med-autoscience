from __future__ import annotations

from ..shared import Any, Box, LayoutSidecar, _all_boxes, _check_boxes_within_device, _check_colorbar_panel_overlap, _check_composite_panel_label_anchors, _check_legend_panel_overlap, _check_pairwise_non_overlap, _check_required_box_types, _issue, _point_within_box, _require_numeric
from .context_support import _check_publication_atlas_spatial_trajectory_context_support_panel

def _check_publication_atlas_spatial_trajectory_multimanifold_context_support_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    all_boxes = _all_boxes(sidecar)
    issues.extend(_check_boxes_within_device(sidecar))
    issues.extend(
        _check_required_box_types(
            all_boxes,
            required_box_types=(
                "panel_title",
                "subplot_x_axis_title",
                "subplot_y_axis_title",
                "panel_label",
                "legend",
                "colorbar",
            ),
        )
    )
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    text_boxes = tuple(
        box
        for box in sidecar.layout_boxes
        if box.box_type in {"title", "panel_title", "subplot_x_axis_title", "subplot_y_axis_title", "panel_label"}
    )
    issues.extend(_check_pairwise_non_overlap(text_boxes, rule_id="text_box_overlap", target="text"))
    issues.extend(_check_legend_panel_overlap(sidecar))
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(
        _check_composite_panel_label_anchors(
            sidecar,
            label_panel_map={
                "panel_label_A": "panel_atlas_A",
                "panel_label_B": "panel_atlas_B",
                "panel_label_C": "panel_spatial",
                "panel_label_D": "panel_trajectory",
                "panel_label_E": "panel_composition",
                "panel_label_F": "panel_heatmap",
                "panel_label_G": "panel_support",
            },
        )
    )

    panel_boxes_by_id = {box.box_id: box for box in sidecar.panel_boxes}
    for panel_box_id, message in (
        ("panel_atlas_A", "multimanifold context-support panel requires atlas panel A"),
        ("panel_atlas_B", "multimanifold context-support panel requires atlas panel B"),
        ("panel_spatial", "multimanifold context-support panel requires a spatial panel"),
        ("panel_trajectory", "multimanifold context-support panel requires a trajectory panel"),
        ("panel_composition", "multimanifold context-support panel requires a composition panel"),
        ("panel_heatmap", "multimanifold context-support panel requires a heatmap panel"),
        ("panel_support", "multimanifold context-support panel requires a support panel"),
    ):
        if panel_box_id in panel_boxes_by_id:
            continue
        issues.append(_issue(rule_id="missing_box", message=message, target=panel_box_id, expected="present"))

    layout_boxes_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    for box_id in (
        "atlas_A_panel_title",
        "atlas_A_x_axis_title",
        "atlas_A_y_axis_title",
        "atlas_B_panel_title",
        "atlas_B_x_axis_title",
        "atlas_B_y_axis_title",
        "panel_label_G",
    ):
        if box_id in layout_boxes_by_id:
            continue
        issues.append(_issue(rule_id="missing_box", message=f"multimanifold context-support panel requires {box_id}", target=box_id, expected="present"))

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
                issues.append(_issue(rule_id=empty_rule, message=f"{metric_key} labels must be non-empty", target=f"metrics.{metric_key}[{index}]"))
                continue
            if label in seen:
                issues.append(_issue(rule_id=duplicate_rule, message=f"{metric_key} label `{label}` must be unique", target=f"metrics.{metric_key}", observed=label))
                continue
            seen.add(label)
            normalized.append(label)
        return normalized

    normalized_state_labels = _normalize_unique_labels(
        "state_labels",
        "state_labels_missing",
        "empty_state_label",
        "duplicate_state_label",
        "multimanifold context-support panel requires explicit non-empty state_labels metrics",
    )
    _normalize_unique_labels(
        "branch_labels",
        "branch_labels_missing",
        "empty_branch_label",
        "duplicate_branch_label",
        "multimanifold context-support panel requires explicit non-empty branch_labels metrics",
    )
    _normalize_unique_labels(
        "bin_labels",
        "bin_labels_missing",
        "empty_bin_label",
        "duplicate_bin_label",
        "multimanifold context-support panel requires explicit non-empty bin_labels metrics",
    )
    _normalize_unique_labels(
        "row_labels",
        "row_labels_missing",
        "empty_row_label",
        "duplicate_row_label",
        "multimanifold context-support panel requires explicit non-empty row_labels metrics",
    )
    normalized_context_labels = _normalize_unique_labels(
        "context_labels",
        "context_labels_missing",
        "empty_context_label",
        "duplicate_context_label",
        "multimanifold context-support panel requires explicit non-empty context_labels metrics",
    )
    normalized_context_kinds = _normalize_unique_labels(
        "context_kinds",
        "context_kinds_missing",
        "empty_context_kind",
        "duplicate_context_kind",
        "multimanifold context-support panel requires explicit non-empty context_kinds metrics",
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
        issues.append(_issue(rule_id="support_scale_label_missing", message="multimanifold context-support panel requires a non-empty support_scale_label", target="metrics.support_scale_label"))

    atlas_manifold_panels = sidecar.metrics.get("atlas_manifold_panels")
    if not isinstance(atlas_manifold_panels, list) or len(atlas_manifold_panels) != 2:
        issues.append(
            _issue(
                rule_id="atlas_manifold_panels_invalid",
                message="multimanifold context-support panel requires exactly two atlas_manifold_panels metrics",
                target="metrics.atlas_manifold_panels",
            )
        )
    else:
        seen_panel_ids: set[str] = set()
        seen_panel_labels: set[str] = set()
        seen_methods: set[str] = set()
        for panel_index, panel in enumerate(atlas_manifold_panels):
            if not isinstance(panel, dict):
                raise ValueError(f"layout_sidecar.metrics.atlas_manifold_panels[{panel_index}] must be an object")
            panel_id = str(panel.get("panel_id") or "").strip()
            panel_label = str(panel.get("panel_label") or "").strip()
            method = str(panel.get("manifold_method") or "").strip().lower()
            if not panel_id:
                issues.append(_issue(rule_id="atlas_manifold_panel_id_missing", message="atlas manifold panel_id must be non-empty", target=f"metrics.atlas_manifold_panels[{panel_index}].panel_id"))
            elif panel_id in seen_panel_ids:
                issues.append(_issue(rule_id="duplicate_atlas_manifold_panel_id", message=f"atlas manifold panel_id `{panel_id}` must be unique", target="metrics.atlas_manifold_panels", observed=panel_id))
            else:
                seen_panel_ids.add(panel_id)
            if not panel_label:
                issues.append(_issue(rule_id="atlas_manifold_panel_label_missing", message="atlas manifold panel_label must be non-empty", target=f"metrics.atlas_manifold_panels[{panel_index}].panel_label"))
            elif panel_label in seen_panel_labels:
                issues.append(_issue(rule_id="duplicate_atlas_manifold_panel_label", message=f"atlas manifold panel_label `{panel_label}` must be unique", target="metrics.atlas_manifold_panels", observed=panel_label))
            else:
                seen_panel_labels.add(panel_label)
            if method not in {"pca", "phate", "tsne", "umap"}:
                issues.append(_issue(rule_id="atlas_manifold_method_invalid", message="atlas manifold_method must be one of pca, phate, tsne, umap", target=f"metrics.atlas_manifold_panels[{panel_index}].manifold_method", observed=method))
            elif method in seen_methods:
                issues.append(_issue(rule_id="duplicate_atlas_manifold_method", message=f"atlas manifold_method `{method}` must be unique", target="metrics.atlas_manifold_panels", observed=method))
            else:
                seen_methods.add(method)
            points = panel.get("points")
            panel_box = panel_boxes_by_id.get("panel_atlas_A" if panel_index == 0 else "panel_atlas_B")
            if not isinstance(points, list) or not points:
                issues.append(_issue(rule_id="atlas_manifold_points_missing", message="atlas manifold points must be non-empty", target=f"metrics.atlas_manifold_panels[{panel_index}].points"))
                continue
            for point_index, point in enumerate(points):
                if not isinstance(point, dict):
                    raise ValueError(f"layout_sidecar.metrics.atlas_manifold_panels[{panel_index}].points[{point_index}] must be an object")
                state_label = str(point.get("state_label") or "").strip()
                if not state_label:
                    issues.append(_issue(rule_id="empty_state_label", message="atlas manifold point state_label must be non-empty", target=f"metrics.atlas_manifold_panels[{panel_index}].points[{point_index}].state_label"))
                elif normalized_state_labels and state_label not in normalized_state_labels:
                    issues.append(_issue(rule_id="atlas_manifold_point_state_label_unknown", message="atlas manifold point state_label must stay inside declared state_labels", target=f"metrics.atlas_manifold_panels[{panel_index}].points[{point_index}].state_label", observed=state_label, expected=normalized_state_labels))
                x_value = _require_numeric(point.get("x"), label=f"layout_sidecar.metrics.atlas_manifold_panels[{panel_index}].points[{point_index}].x")
                y_value = _require_numeric(point.get("y"), label=f"layout_sidecar.metrics.atlas_manifold_panels[{panel_index}].points[{point_index}].y")
                if panel_box is not None and not _point_within_box(panel_box, x=x_value, y=y_value):
                    issues.append(_issue(rule_id="atlas_manifold_point_out_of_panel", message="atlas manifold point must stay within its panel domain", target=f"metrics.atlas_manifold_panels[{panel_index}].points[{point_index}]", observed={"x": x_value, "y": y_value}, box_refs=(panel_box.box_id,)))

    synthetic_layout_boxes = []
    layout_box_id_map = {
        "atlas_A_panel_title": "atlas_panel_title",
        "atlas_A_x_axis_title": "atlas_x_axis_title",
        "atlas_A_y_axis_title": "atlas_y_axis_title",
        "panel_label_C": "panel_label_B",
        "panel_label_D": "panel_label_C",
        "panel_label_E": "panel_label_D",
        "panel_label_F": "panel_label_E",
        "panel_label_G": "panel_label_F",
    }
    for box in sidecar.layout_boxes:
        if box.box_id in {"atlas_B_panel_title", "atlas_B_x_axis_title", "atlas_B_y_axis_title", "panel_label_B"}:
            continue
        synthetic_layout_boxes.append(
            Box(
                box_id=layout_box_id_map.get(box.box_id, box.box_id),
                box_type=box.box_type,
                x0=box.x0,
                y0=box.y0,
                x1=box.x1,
                y1=box.y1,
            )
        )
    synthetic_panel_boxes = []
    for box in sidecar.panel_boxes:
        if box.box_id == "panel_atlas_B":
            continue
        synthetic_panel_boxes.append(
            Box(
                box_id="panel_atlas" if box.box_id == "panel_atlas_A" else box.box_id,
                box_type=box.box_type,
                x0=box.x0,
                y0=box.y0,
                x1=box.x1,
                y1=box.y1,
            )
        )
    synthetic_metrics = dict(sidecar.metrics)
    if isinstance(atlas_manifold_panels, list) and atlas_manifold_panels:
        synthetic_metrics["atlas_points"] = list(atlas_manifold_panels[0].get("points") or [])
    synthetic_sidecar = LayoutSidecar(
        template_id=sidecar.template_id,
        device=sidecar.device,
        layout_boxes=tuple(synthetic_layout_boxes),
        panel_boxes=tuple(synthetic_panel_boxes),
        guide_boxes=sidecar.guide_boxes,
        metrics=synthetic_metrics,
        render_context=sidecar.render_context,
    )
    issues.extend(_check_publication_atlas_spatial_trajectory_context_support_panel(synthetic_sidecar))
    return issues
