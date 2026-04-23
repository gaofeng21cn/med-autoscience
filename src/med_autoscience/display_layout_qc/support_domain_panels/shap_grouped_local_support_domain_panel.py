from __future__ import annotations

from .feature_response_support_domain_panel import _check_publication_feature_response_support_domain_panel
from ..shap_path_panels import _check_publication_shap_grouped_local_explanation_panel
from ..shared import Any, LayoutSidecar, _issue, _layout_override_flag, _panel_label_token, _require_non_empty_text, _subset_layout_sidecar

def _check_publication_shap_grouped_local_support_domain_panel(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    local_panels = metrics.get("local_panels")
    support_panels = metrics.get("support_panels")
    if not isinstance(local_panels, list) or not local_panels:
        issues.append(
            _issue(
                rule_id="local_panels_missing",
                message="grouped-local support-domain composite requires non-empty local_panels metrics",
                target="metrics.local_panels",
            )
        )
        return issues
    if not isinstance(support_panels, list) or len(support_panels) != 2:
        issues.append(
            _issue(
                rule_id="support_panels_invalid",
                message="grouped-local support-domain composite requires exactly two support_panels metrics",
                target="metrics.support_panels",
                observed={"support_panels": len(support_panels) if isinstance(support_panels, list) else None},
                expected={"support_panels": 2},
            )
        )
        return issues

    show_figure_title = _layout_override_flag(sidecar, "show_figure_title", False)
    local_layout_box_ids: set[str] = {"title"} if show_figure_title else set()
    local_panel_box_ids: set[str] = set()
    local_guide_box_ids: set[str] = set()
    local_panel_labels: list[str] = []
    for panel_index, panel in enumerate(local_panels):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.local_panels[{panel_index}] must be an object")
        panel_label = _require_non_empty_text(
            panel.get("panel_label"),
            label=f"layout_sidecar.metrics.local_panels[{panel_index}].panel_label",
        )
        local_panel_labels.append(panel_label)
        panel_token = _panel_label_token(panel_label)
        local_panel_box_ids.add(str(panel.get("panel_box_id") or "").strip() or f"panel_{panel_token}")
        local_guide_box_ids.add(str(panel.get("zero_line_box_id") or "").strip() or f"zero_line_{panel_token}")
        local_layout_box_ids.update(
            {
                f"panel_title_{panel_token}",
                f"panel_label_{panel_token}",
                f"group_label_{panel_token}",
                f"baseline_label_{panel_token}",
                f"prediction_label_{panel_token}",
                f"x_axis_title_{panel_token}",
            }
        )
        contributions = panel.get("contributions")
        if not isinstance(contributions, list):
            continue
        for contribution_index, contribution in enumerate(contributions):
            if not isinstance(contribution, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.local_panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            for field_name in ("bar_box_id", "feature_label_box_id", "value_label_box_id"):
                box_id = str(contribution.get(field_name) or "").strip()
                if box_id:
                    local_layout_box_ids.add(box_id)

    support_layout_box_ids: set[str] = {"title"} if show_figure_title else set()
    support_layout_box_ids.update(
        {
            str(metrics.get("support_y_axis_title_box_id") or "").strip() or "support_y_axis_title",
            str(metrics.get("support_legend_title_box_id") or "").strip() or "support_legend_title",
            "support_legend_box",
        }
    )
    support_panel_box_ids: set[str] = set()
    support_guide_box_ids: set[str] = set()
    support_panel_labels: list[str] = []
    support_features: list[str] = []
    for panel_index, panel in enumerate(support_panels):
        if not isinstance(panel, dict):
            raise ValueError(f"layout_sidecar.metrics.support_panels[{panel_index}] must be an object")
        panel_label = _require_non_empty_text(
            panel.get("panel_label"),
            label=f"layout_sidecar.metrics.support_panels[{panel_index}].panel_label",
        )
        support_panel_labels.append(panel_label)
        support_features.append(
            _require_non_empty_text(
                panel.get("feature"),
                label=f"layout_sidecar.metrics.support_panels[{panel_index}].feature",
            )
        )
        panel_token = _panel_label_token(panel_label)
        support_panel_box_ids.add(str(panel.get("panel_box_id") or "").strip() or f"panel_{panel_token}")
        support_guide_box_ids.add(
            str(panel.get("reference_line_box_id") or "").strip() or f"reference_line_{panel_token}"
        )
        support_layout_box_ids.update(
            {
                f"panel_title_{panel_token}",
                f"panel_label_{panel_token}",
                f"x_axis_title_{panel_token}",
                str(panel.get("reference_label_box_id") or "").strip() or f"reference_label_{panel_token}",
            }
        )
        segments = panel.get("support_segments")
        if not isinstance(segments, list):
            continue
        for segment_index, segment in enumerate(segments):
            if not isinstance(segment, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.support_panels[{panel_index}].support_segments[{segment_index}] must be an object"
                )
            segment_box_id = str(segment.get("segment_box_id") or "").strip()
            label_box_id = str(segment.get("label_box_id") or "").strip()
            if segment_box_id:
                support_guide_box_ids.add(segment_box_id)
            if label_box_id:
                support_layout_box_ids.add(label_box_id)

    local_sidecar = _subset_layout_sidecar(
        sidecar,
        layout_box_ids=local_layout_box_ids,
        panel_box_ids=local_panel_box_ids,
        guide_box_ids=local_guide_box_ids,
        metrics={"panels": list(local_panels)},
    )
    support_sidecar = _subset_layout_sidecar(
        sidecar,
        layout_box_ids=support_layout_box_ids,
        panel_box_ids=support_panel_box_ids,
        guide_box_ids=support_guide_box_ids,
        metrics={
            "legend_labels": metrics.get("support_legend_labels"),
            "panels": list(support_panels),
        },
    )
    issues.extend(_check_publication_shap_grouped_local_explanation_panel(local_sidecar))
    issues.extend(_check_publication_feature_response_support_domain_panel(support_sidecar))

    local_feature_order_payload = metrics.get("local_shared_feature_order")
    if not isinstance(local_feature_order_payload, list) or not local_feature_order_payload:
        issues.append(
            _issue(
                rule_id="local_feature_order_missing",
                message="grouped-local support-domain composite requires a non-empty local_shared_feature_order",
                target="metrics.local_shared_feature_order",
            )
        )
        local_feature_order: list[str] = []
    else:
        local_feature_order = [str(item or "").strip() for item in local_feature_order_payload]
        if any(not item for item in local_feature_order):
            issues.append(
                _issue(
                    rule_id="local_feature_order_invalid",
                    message="grouped-local support-domain local_shared_feature_order entries must be non-empty",
                    target="metrics.local_shared_feature_order",
                )
            )

    if len(set(local_panel_labels + support_panel_labels)) != len(local_panel_labels) + len(support_panel_labels):
        issues.append(
            _issue(
                rule_id="panel_label_collision",
                message="grouped-local support-domain composite panel labels must stay unique across local and support panels",
                target="metrics",
                observed={"local_panel_labels": local_panel_labels, "support_panel_labels": support_panel_labels},
            )
        )

    if local_feature_order:
        if not set(support_features).issubset(set(local_feature_order)):
            issues.append(
                _issue(
                    rule_id="support_feature_outside_local_order",
                    message="support-domain features must stay within the shared grouped-local feature order",
                    target="metrics.support_panels",
                    observed={"support_features": support_features},
                    expected={"local_shared_feature_order": local_feature_order},
                )
            )
        expected_support_order = [feature for feature in local_feature_order if feature in set(support_features)]
        if support_features != expected_support_order:
            issues.append(
                _issue(
                    rule_id="support_feature_order_mismatch",
                    message="support-domain feature order must follow the shared grouped-local feature order",
                    target="metrics.support_panels",
                    observed={"support_features": support_features},
                    expected={"support_features": expected_support_order},
                )
            )

    support_legend_title = str(metrics.get("support_legend_title") or "").strip()
    if not support_legend_title:
        issues.append(
            _issue(
                rule_id="support_legend_title_invalid",
                message="grouped-local support-domain composite requires a non-empty support legend title",
                target="metrics.support_legend_title",
            )
        )
    legend_title_box_id = str(metrics.get("support_legend_title_box_id") or "").strip() or "support_legend_title"
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    if legend_title_box_id not in layout_box_by_id:
        issues.append(
            _issue(
                rule_id="support_legend_title_missing",
                message="grouped-local support-domain composite requires an explicit support legend title box",
                target="metrics.support_legend_title_box_id",
                observed=legend_title_box_id,
            )
        )

    return issues
