from __future__ import annotations

from .feature_response_support_domain_panel import _check_publication_feature_response_support_domain_panel
from ..shap_summary_panels import _check_publication_shap_signed_importance_panel, _check_publication_shap_waterfall_local_explanation_panel
from ..shared import Any, LayoutSidecar, _issue, _layout_override_flag, _panel_label_token, _require_non_empty_text, _subset_layout_sidecar

def _check_publication_shap_signed_importance_local_support_domain_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    importance_panel = metrics.get("importance_panel")
    local_panel = metrics.get("local_panel")
    support_panels = metrics.get("support_panels")
    if not isinstance(importance_panel, dict):
        issues.append(
            _issue(
                rule_id="importance_panel_missing",
                message="signed-importance local support-domain composite requires importance_panel metrics",
                target="metrics.importance_panel",
            )
        )
        return issues
    if not isinstance(local_panel, dict):
        issues.append(
            _issue(
                rule_id="local_panel_missing",
                message="signed-importance local support-domain composite requires local_panel metrics",
                target="metrics.local_panel",
            )
        )
        return issues
    if not isinstance(support_panels, list) or len(support_panels) != 2:
        issues.append(
            _issue(
                rule_id="support_panels_invalid",
                message="signed-importance local support-domain composite requires exactly two support_panels metrics",
                target="metrics.support_panels",
                observed={"support_panels": len(support_panels) if isinstance(support_panels, list) else None},
                expected={"support_panels": 2},
            )
        )
        return issues

    show_figure_title = _layout_override_flag(sidecar, "show_figure_title", False)

    importance_panel_label = _require_non_empty_text(
        importance_panel.get("panel_label"),
        label="layout_sidecar.metrics.importance_panel.panel_label",
    )
    importance_panel_token = _panel_label_token(importance_panel_label)
    importance_panel_box_id = str(importance_panel.get("panel_box_id") or "").strip() or f"panel_{importance_panel_token}"
    importance_layout_box_ids: set[str] = {"title"} if show_figure_title else set()
    importance_layout_box_ids.update(
        {
            f"panel_title_{importance_panel_token}",
            f"panel_label_{importance_panel_token}",
            "negative_direction_label",
            "positive_direction_label",
            "x_axis_title",
        }
    )
    importance_panel_box_ids = {importance_panel_box_id}
    importance_guide_box_ids = {str(importance_panel.get("zero_line_box_id") or "").strip() or "zero_line"}
    bars = importance_panel.get("bars")
    if isinstance(bars, list):
        for bar_index, bar in enumerate(bars):
            if not isinstance(bar, dict):
                raise ValueError(f"layout_sidecar.metrics.importance_panel.bars[{bar_index}] must be an object")
            importance_layout_box_ids.add(
                str(bar.get("feature_label_box_id") or "").strip() or f"feature_label_{bar_index + 1}"
            )
            importance_layout_box_ids.add(
                str(bar.get("bar_box_id") or "").strip() or f"importance_bar_{bar_index + 1}"
            )
            importance_layout_box_ids.add(
                str(bar.get("value_label_box_id") or "").strip() or f"value_label_{bar_index + 1}"
            )

    local_panel_label = _require_non_empty_text(
        local_panel.get("panel_label"),
        label="layout_sidecar.metrics.local_panel.panel_label",
    )
    local_panel_token = _panel_label_token(local_panel_label)
    local_panel_box_id = str(local_panel.get("panel_box_id") or "").strip() or f"panel_{local_panel_token}"
    local_layout_box_ids: set[str] = {"title"} if show_figure_title else set()
    local_layout_box_ids.update(
        {
            f"panel_title_{local_panel_token}",
            f"panel_label_{local_panel_token}",
            f"case_label_{local_panel_token}",
            f"baseline_label_{local_panel_token}",
            f"prediction_label_{local_panel_token}",
            f"x_axis_title_{local_panel_token}",
        }
    )
    local_panel_box_ids = {local_panel_box_id}
    local_guide_box_ids = {
        str(local_panel.get("baseline_marker_box_id") or "").strip() or f"baseline_marker_{local_panel_token}",
        str(local_panel.get("prediction_marker_box_id") or "").strip() or f"prediction_marker_{local_panel_token}",
    }
    local_contributions = local_panel.get("contributions")
    if isinstance(local_contributions, list):
        for contribution_index, contribution in enumerate(local_contributions):
            if not isinstance(contribution, dict):
                raise ValueError(
                    f"layout_sidecar.metrics.local_panel.contributions[{contribution_index}] must be an object"
                )
            local_layout_box_ids.add(
                str(contribution.get("label_box_id") or "").strip()
                or f"feature_label_{local_panel_token}_{contribution_index + 1}"
            )
            local_layout_box_ids.add(
                str(contribution.get("bar_box_id") or "").strip()
                or f"contribution_bar_{local_panel_token}_{contribution_index + 1}"
            )

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
        if isinstance(segments, list):
            for segment_index, segment in enumerate(segments):
                if not isinstance(segment, dict):
                    raise ValueError(
                        f"layout_sidecar.metrics.support_panels[{panel_index}].support_segments[{segment_index}] must be an object"
                    )
                support_guide_box_ids.add(
                    str(segment.get("segment_box_id") or "").strip()
                    or f"support_segment_{panel_token}_{segment_index + 1}"
                )
                support_layout_box_ids.add(
                    str(segment.get("label_box_id") or "").strip()
                    or f"support_label_{panel_token}_{segment_index + 1}"
                )

    importance_sidecar = _subset_layout_sidecar(
        sidecar,
        layout_box_ids=importance_layout_box_ids,
        panel_box_ids=importance_panel_box_ids,
        guide_box_ids=importance_guide_box_ids,
        metrics={"bars": list(bars) if isinstance(bars, list) else []},
    )
    local_sidecar = _subset_layout_sidecar(
        sidecar,
        layout_box_ids=local_layout_box_ids,
        panel_box_ids=local_panel_box_ids,
        guide_box_ids=local_guide_box_ids,
        metrics={"panels": [dict(local_panel)]},
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
    issues.extend(_check_publication_shap_signed_importance_panel(importance_sidecar))
    issues.extend(_check_publication_shap_waterfall_local_explanation_panel(local_sidecar))
    issues.extend(_check_publication_feature_response_support_domain_panel(support_sidecar))

    panel_labels = [importance_panel_label, local_panel_label, *support_panel_labels]
    if len(set(panel_labels)) != len(panel_labels):
        issues.append(
            _issue(
                rule_id="panel_label_collision",
                message="signed-importance local support-domain composite panel labels must stay globally unique",
                target="metrics",
                observed={"panel_labels": panel_labels},
            )
        )

    global_feature_order_payload = metrics.get("global_feature_order")
    if not isinstance(global_feature_order_payload, list) or not global_feature_order_payload:
        issues.append(
            _issue(
                rule_id="global_feature_order_missing",
                message="signed-importance local support-domain composite requires a non-empty global feature order",
                target="metrics.global_feature_order",
            )
        )
        global_feature_order: list[str] = []
    else:
        global_feature_order = [str(item or "").strip() for item in global_feature_order_payload]
        if any(not item for item in global_feature_order):
            issues.append(
                _issue(
                    rule_id="global_feature_order_invalid",
                    message="global feature order entries must be non-empty",
                    target="metrics.global_feature_order",
                )
            )

    local_features = []
    if isinstance(local_contributions, list):
        local_features = [
            _require_non_empty_text(
                contribution.get("feature"),
                label=f"layout_sidecar.metrics.local_panel.contributions[{index}].feature",
            )
            for index, contribution in enumerate(local_contributions)
            if isinstance(contribution, dict)
        ]
    if global_feature_order:
        if not set(local_features).issubset(set(global_feature_order)):
            issues.append(
                _issue(
                    rule_id="local_feature_outside_global_order",
                    message="local explanation features must stay within the global signed-importance feature order",
                    target="metrics.local_panel.contributions",
                    observed={"local_features": local_features},
                    expected={"global_feature_order": global_feature_order},
                )
            )
        expected_local_order = [feature for feature in global_feature_order if feature in set(local_features)]
        if local_features != expected_local_order:
            issues.append(
                _issue(
                    rule_id="local_feature_order_mismatch",
                    message="local explanation feature order must follow the global signed-importance feature order",
                    target="metrics.local_panel.contributions",
                    observed={"local_features": local_features},
                    expected={"local_features": expected_local_order},
                )
            )
        if not set(support_features).issubset(set(global_feature_order)):
            issues.append(
                _issue(
                    rule_id="support_feature_outside_global_order",
                    message="support-domain features must stay within the global signed-importance feature order",
                    target="metrics.support_panels",
                    observed={"support_features": support_features},
                    expected={"global_feature_order": global_feature_order},
                )
            )
        expected_support_order = [feature for feature in global_feature_order if feature in set(support_features)]
        if support_features != expected_support_order:
            issues.append(
                _issue(
                    rule_id="support_feature_order_mismatch",
                    message="support-domain feature order must follow the global signed-importance feature order",
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
                message="signed-importance local support-domain composite requires a non-empty support legend title",
                target="metrics.support_legend_title",
            )
        )
    legend_title_box_id = str(metrics.get("support_legend_title_box_id") or "").strip() or "support_legend_title"
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    if legend_title_box_id not in layout_box_by_id:
        issues.append(
            _issue(
                rule_id="support_legend_title_missing",
                message="signed-importance local support-domain composite requires an explicit support legend title box",
                target="metrics.support_legend_title_box_id",
                observed=legend_title_box_id,
            )
        )

    return issues
