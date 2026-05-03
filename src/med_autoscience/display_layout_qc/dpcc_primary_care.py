from __future__ import annotations

from .shared import Any, LayoutSidecar, _all_boxes, _boxes_of_type, _check_boxes_within_device, _check_colorbar_panel_overlap, _check_pairwise_non_overlap, _check_required_box_types, _issue


def _check_required_metric_list(
    metrics: dict[str, Any],
    *,
    key: str,
    minimum_count: int = 1,
) -> list[dict[str, Any]]:
    value = metrics.get(key)
    if isinstance(value, list) and len(value) >= minimum_count:
        return []
    observed_count = len(value) if isinstance(value, list) else 0
    return [
        _issue(
            rule_id=f"{key}_missing",
            message=f"DPCC primary-care display requires non-empty metrics.{key}",
            target=f"metrics.{key}",
            observed={"count": observed_count},
            expected={"minimum_count": minimum_count},
        )
    ]


def _check_exact_panel_count(
    sidecar: LayoutSidecar,
    *,
    expected_count: int,
    rule_id: str,
    message: str,
) -> list[dict[str, Any]]:
    if len(sidecar.panel_boxes) == expected_count:
        return []
    return [
        _issue(
            rule_id=rule_id,
            message=message,
            target="panel_boxes",
            observed={"count": len(sidecar.panel_boxes)},
            expected={"count": expected_count},
        )
    ]


def _check_dpcc_common_layout(
    sidecar: LayoutSidecar,
    *,
    required_box_types: tuple[str, ...],
) -> list[dict[str, Any]]:
    issues = _check_boxes_within_device(sidecar)
    issues.extend(_check_required_box_types(_all_boxes(sidecar), required_box_types=required_box_types))
    issues.extend(_check_pairwise_non_overlap(sidecar.panel_boxes, rule_id="panel_overlap", target="panel"))
    return issues


def _check_publication_dpcc_phenotype_gap_structure(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_dpcc_common_layout(
        sidecar,
        required_box_types=(
            "title",
            "panel_label",
            "subplot_title",
            "x_axis_title",
            "composition_panel",
            "gap_heatmap_panel",
            "colorbar",
            "colorbar_title",
        ),
    )
    issues.extend(
        _check_exact_panel_count(
            sidecar,
            expected_count=2,
            rule_id="dpcc_phenotype_gap_panel_count_mismatch",
            message="DPCC phenotype-gap structure figure requires composition and gap-heatmap panels",
        )
    )
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(_check_required_metric_list(sidecar.metrics, key="rows"))
    issues.extend(_check_required_metric_list(sidecar.metrics, key="gap_labels"))
    return issues


def _check_publication_dpcc_transition_site_support(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_dpcc_common_layout(
        sidecar,
        required_box_types=(
            "title",
            "panel_label",
            "subplot_title",
            "x_axis_title",
            "y_axis_title",
            "transition_heatmap_panel",
            "site_support_panel",
            "colorbar",
            "colorbar_title",
        ),
    )
    issues.extend(
        _check_exact_panel_count(
            sidecar,
            expected_count=2,
            rule_id="dpcc_transition_site_panel_count_mismatch",
            message="DPCC transition/site-support figure requires transition heatmap and site-support panels",
        )
    )
    issues.extend(_check_colorbar_panel_overlap(sidecar))
    issues.extend(_check_required_metric_list(sidecar.metrics, key="transition_rows"))
    issues.extend(_check_required_metric_list(sidecar.metrics, key="site_fold_rows"))
    return issues


def _check_publication_dpcc_treatment_gap_alignment(sidecar: LayoutSidecar) -> list[dict[str, Any]]:
    issues = _check_dpcc_common_layout(
        sidecar,
        required_box_types=(
            "title",
            "panel_label",
            "subplot_title",
            "y_axis_title",
            "gap_count_panel",
        ),
    )
    issues.extend(
        _check_exact_panel_count(
            sidecar,
            expected_count=4,
            rule_id="dpcc_treatment_gap_panel_count_mismatch",
            message="DPCC treatment-gap alignment figure requires four gap-count panels",
        )
    )
    issues.extend(_check_required_metric_list(sidecar.metrics, key="rows"))
    issues.extend(_check_required_metric_list(sidecar.metrics, key="panels", minimum_count=4))
    return issues
