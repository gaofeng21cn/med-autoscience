from __future__ import annotations

from .feature_response_support_domain_panel import _check_publication_feature_response_support_domain_panel
from ..shap_path_panels import _check_publication_shap_multigroup_decision_path_panel
from ..shared import Any, LayoutSidecar, _issue, _layout_override_flag, _panel_label_token, _require_non_empty_text, _subset_layout_sidecar

def _check_publication_shap_multigroup_decision_path_support_domain_panel(
    sidecar: LayoutSidecar,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    metrics = sidecar.metrics if isinstance(sidecar.metrics, dict) else {}
    decision_panel = metrics.get("decision_panel")
    support_panels = metrics.get("support_panels")
    if not isinstance(decision_panel, dict):
        issues.append(
            _issue(
                rule_id="decision_panel_missing",
                message="multigroup decision-path support-domain composite requires decision_panel metrics",
                target="metrics.decision_panel",
            )
        )
        return issues
    if not isinstance(support_panels, list) or len(support_panels) != 2:
        issues.append(
            _issue(
                rule_id="support_panels_invalid",
                message="multigroup decision-path support-domain composite requires exactly two support_panels metrics",
                target="metrics.support_panels",
                observed={"support_panels": len(support_panels) if isinstance(support_panels, list) else None},
                expected={"support_panels": 2},
            )
        )
        return issues

    show_figure_title = _layout_override_flag(sidecar, "show_figure_title", False)
    decision_layout_box_ids: set[str] = {"title"} if show_figure_title else set()
    decision_layout_box_ids.update({"panel_title", "x_axis_title", "y_axis_title", "legend_title", "legend_box"})
    feature_label_box_ids = decision_panel.get("feature_label_box_ids")
    if isinstance(feature_label_box_ids, list):
        decision_layout_box_ids.update(str(item or "").strip() for item in feature_label_box_ids if str(item or "").strip())

    decision_groups = decision_panel.get("groups")
    decision_panel_box_ids: set[str] = {
        str(decision_panel.get("panel_box_id") or "").strip() or "panel_decision_path"
    }
    decision_guide_box_ids: set[str] = {
        str(decision_panel.get("baseline_line_box_id") or "").strip() or "baseline_reference_line"
    }
    if isinstance(decision_groups, list):
        for group_index, group in enumerate(decision_groups):
            if not isinstance(group, dict):
                raise ValueError(f"layout_sidecar.metrics.decision_panel.groups[{group_index}] must be an object")
            line_box_id = str(group.get("line_box_id") or "").strip()
            prediction_marker_box_id = str(group.get("prediction_marker_box_id") or "").strip()
            prediction_label_box_id = str(group.get("prediction_label_box_id") or "").strip()
            if line_box_id:
                decision_layout_box_ids.add(line_box_id)
            if prediction_label_box_id:
                decision_layout_box_ids.add(prediction_label_box_id)
            if prediction_marker_box_id:
                decision_guide_box_ids.add(prediction_marker_box_id)

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

    decision_sidecar = _subset_layout_sidecar(
        sidecar,
        layout_box_ids=decision_layout_box_ids,
        panel_box_ids=decision_panel_box_ids,
        guide_box_ids=decision_guide_box_ids,
        metrics=dict(decision_panel),
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
    issues.extend(_check_publication_shap_multigroup_decision_path_panel(decision_sidecar))
    issues.extend(_check_publication_feature_response_support_domain_panel(support_sidecar))

    feature_order_payload = decision_panel.get("feature_order")
    if not isinstance(feature_order_payload, list) or not feature_order_payload:
        issues.append(
            _issue(
                rule_id="decision_feature_order_missing",
                message="multigroup decision-path support-domain composite requires a non-empty decision feature order",
                target="metrics.decision_panel.feature_order",
            )
        )
        feature_order: list[str] = []
    else:
        feature_order = [str(item or "").strip() for item in feature_order_payload]
        if any(not item for item in feature_order):
            issues.append(
                _issue(
                    rule_id="decision_feature_order_invalid",
                    message="multigroup decision-path support-domain feature order entries must be non-empty",
                    target="metrics.decision_panel.feature_order",
                )
            )

    if len(set(support_panel_labels)) != len(support_panel_labels):
        issues.append(
            _issue(
                rule_id="panel_label_collision",
                message="multigroup decision-path support-domain support panel labels must stay unique",
                target="metrics.support_panels",
                observed={"support_panel_labels": support_panel_labels},
            )
        )

    if feature_order:
        if not set(support_features).issubset(set(feature_order)):
            issues.append(
                _issue(
                    rule_id="support_feature_outside_decision_order",
                    message="support-domain features must stay within the shared decision-path feature order",
                    target="metrics.support_panels",
                    observed={"support_features": support_features},
                    expected={"feature_order": feature_order},
                )
            )
        expected_support_order = [feature for feature in feature_order if feature in set(support_features)]
        if support_features != expected_support_order:
            issues.append(
                _issue(
                    rule_id="support_feature_order_mismatch",
                    message="support-domain feature order must follow the shared decision-path feature order",
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
                message="multigroup decision-path support-domain composite requires a non-empty support legend title",
                target="metrics.support_legend_title",
            )
        )
    legend_title_box_id = str(metrics.get("support_legend_title_box_id") or "").strip() or "support_legend_title"
    layout_box_by_id = {box.box_id: box for box in sidecar.layout_boxes}
    if legend_title_box_id not in layout_box_by_id:
        issues.append(
            _issue(
                rule_id="support_legend_title_missing",
                message="multigroup decision-path support-domain composite requires an explicit support legend title box",
                target="metrics.support_legend_title_box_id",
                observed=legend_title_box_id,
            )
        )

    return issues
