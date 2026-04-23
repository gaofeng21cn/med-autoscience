from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_numeric_list, _require_numeric_value, math
from .validation_shap_importance import _validate_shap_signed_importance_panel_display_payload
from .validation_shap_paths import _validate_shap_multigroup_decision_path_panel_display_payload
from .validation_shap_summary import _normalize_shap_grouped_local_panels, _validate_shap_waterfall_local_explanation_panel_display_payload

def _normalize_feature_response_support_panels(
    *,
    path: Path,
    panels_payload: object,
    expected_display_id: str,
    panels_field: str,
    minimum_count: int,
    maximum_count: int,
) -> list[dict[str, Any]]:
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty {panels_field} list"
        )
    if len(panels_payload) < minimum_count or len(panels_payload) > maximum_count:
        if minimum_count == maximum_count:
            count_description = f"exactly {minimum_count}"
        else:
            count_description = f"between {minimum_count} and {maximum_count}"
        raise ValueError(
            f"{path.name} display `{expected_display_id}` {panels_field} must contain {count_description} entries"
        )

    allowed_support_kinds = {
        "observed_support",
        "subgroup_support",
        "bin_support",
        "extrapolation_warning",
    }
    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_features: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}] must be an object"
            )
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        feature = _require_non_empty_string(
            panel_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].feature must be unique"
            )
        seen_features.add(feature)
        reference_value = _require_numeric_value(
            panel_payload.get("reference_value"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].reference_value",
        )
        if not math.isfinite(reference_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].reference_value must be finite"
            )
        reference_label = _require_non_empty_string(
            panel_payload.get("reference_label"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].reference_label",
        )
        response_curve_payload = panel_payload.get("response_curve")
        if not isinstance(response_curve_payload, dict):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve must be an object"
            )
        curve_x = _require_numeric_list(
            response_curve_payload.get("x"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve.x",
        )
        curve_y = _require_numeric_list(
            response_curve_payload.get("y"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve.y",
        )
        if len(curve_x) != len(curve_y):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve.x and response_curve.y must have the same length"
            )
        if not all(math.isfinite(value) for value in (*curve_x, *curve_y)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve values must be finite"
            )
        if any(right <= left for left, right in zip(curve_x, curve_x[1:], strict=False)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].response_curve.x must be strictly increasing"
            )
        if reference_value < curve_x[0] or reference_value > curve_x[-1]:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].reference_value must fall within response_curve.x range"
            )

        support_segments_payload = panel_payload.get("support_segments")
        if not isinstance(support_segments_payload, list) or not support_segments_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments must be a non-empty list"
            )
        normalized_support_segments: list[dict[str, Any]] = []
        seen_segment_ids: set[str] = set()
        previous_domain_end: float | None = None
        curve_start = float(curve_x[0])
        curve_end = float(curve_x[-1])
        for segment_index, segment_payload in enumerate(support_segments_payload):
            if not isinstance(segment_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}] must be an object"
                )
            segment_id = _require_non_empty_string(
                segment_payload.get("segment_id"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].segment_id"
                ),
            )
            if segment_id in seen_segment_ids:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}].segment_id must be unique within the panel"
                )
            seen_segment_ids.add(segment_id)
            segment_label = _require_non_empty_string(
                segment_payload.get("segment_label"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].segment_label"
                ),
            )
            support_kind = _require_non_empty_string(
                segment_payload.get("support_kind"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].support_kind"
                ),
            )
            if support_kind not in allowed_support_kinds:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}].support_kind must be one of {sorted(allowed_support_kinds)}"
                )
            domain_start = _require_numeric_value(
                segment_payload.get("domain_start"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].domain_start"
                ),
            )
            domain_end = _require_numeric_value(
                segment_payload.get("domain_end"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].support_segments[{segment_index}].domain_end"
                ),
            )
            if not math.isfinite(domain_start) or not math.isfinite(domain_end) or domain_end <= domain_start:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}] domain bounds must be finite and strictly increasing"
                )
            if domain_start < curve_start or domain_end > curve_end:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments[{segment_index}] must stay within response_curve.x range"
                )
            if segment_index == 0 and not math.isclose(domain_start, curve_start, rel_tol=0.0, abs_tol=1e-9):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments must cover the full response_curve.x range without gaps"
                )
            if previous_domain_end is not None and not math.isclose(
                domain_start,
                previous_domain_end,
                rel_tol=0.0,
                abs_tol=1e-9,
            ):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments must cover the full response_curve.x range without gaps"
                )
            previous_domain_end = domain_end
            normalized_support_segments.append(
                {
                    "segment_id": segment_id,
                    "segment_label": segment_label,
                    "support_kind": support_kind,
                    "domain_start": domain_start,
                    "domain_end": domain_end,
                }
            )
        if previous_domain_end is None or not math.isclose(previous_domain_end, curve_end, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].support_segments must cover the full response_curve.x range without gaps"
            )

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].x_label",
                ),
                "feature": feature,
                "reference_value": reference_value,
                "reference_label": reference_label,
                "response_curve": {"x": curve_x, "y": curve_y},
                "support_segments": normalized_support_segments,
            }
        )

    return normalized_panels

def _validate_feature_response_support_domain_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    normalized_panels = _normalize_feature_response_support_panels(
        path=path,
        panels_payload=payload.get("panels"),
        expected_display_id=expected_display_id,
        panels_field="panels",
        minimum_count=2,
        maximum_count=3,
    )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "panels": normalized_panels,
    }

def _validate_shap_grouped_local_support_domain_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    grouped_local_x_label = _require_non_empty_string(
        payload.get("grouped_local_x_label"),
        label=f"{path.name} display `{expected_display_id}` grouped_local_x_label",
    )
    support_y_label = _require_non_empty_string(
        payload.get("support_y_label"),
        label=f"{path.name} display `{expected_display_id}` support_y_label",
    )
    support_legend_title = _require_non_empty_string(
        payload.get("support_legend_title"),
        label=f"{path.name} display `{expected_display_id}` support_legend_title",
    )
    local_panels, local_feature_order = _normalize_shap_grouped_local_panels(
        path=path,
        panels_payload=payload.get("local_panels"),
        expected_display_id=expected_display_id,
        panels_field="local_panels",
        minimum_count=2,
        maximum_count=3,
    )
    support_panels = _normalize_feature_response_support_panels(
        path=path,
        panels_payload=payload.get("support_panels"),
        expected_display_id=expected_display_id,
        panels_field="support_panels",
        minimum_count=2,
        maximum_count=2,
    )

    local_panel_labels = {str(panel["panel_label"]) for panel in local_panels}
    support_features = [str(panel["feature"]) for panel in support_panels]
    if any(str(panel["panel_label"]) in local_panel_labels for panel in support_panels):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.panel_label must stay distinct from local_panels.panel_label"
        )
    if not set(support_features).issubset(set(local_feature_order)):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.feature must stay within the shared local feature order"
        )
    expected_support_feature_order = [feature for feature in local_feature_order if feature in set(support_features)]
    if support_features != expected_support_feature_order:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.feature order must follow the shared local feature order"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "grouped_local_x_label": grouped_local_x_label,
        "support_y_label": support_y_label,
        "support_legend_title": support_legend_title,
        "support_legend_labels": [
            "Response curve",
            "Observed support",
            "Subgroup support",
            "Bin support",
            "Extrapolation reminder",
        ],
        "local_shared_feature_order": local_feature_order,
        "local_panels": local_panels,
        "support_panels": support_panels,
    }

def _validate_shap_multigroup_decision_path_support_domain_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    decision_panel_title = _require_non_empty_string(
        payload.get("decision_panel_title"),
        label=f"{path.name} display `{expected_display_id}` decision_panel_title",
    )
    decision_x_label = _require_non_empty_string(
        payload.get("decision_x_label"),
        label=f"{path.name} display `{expected_display_id}` decision_x_label",
    )
    decision_y_label = _require_non_empty_string(
        payload.get("decision_y_label"),
        label=f"{path.name} display `{expected_display_id}` decision_y_label",
    )
    decision_legend_title = _require_non_empty_string(
        payload.get("decision_legend_title"),
        label=f"{path.name} display `{expected_display_id}` decision_legend_title",
    )
    support_y_label = _require_non_empty_string(
        payload.get("support_y_label"),
        label=f"{path.name} display `{expected_display_id}` support_y_label",
    )
    support_legend_title = _require_non_empty_string(
        payload.get("support_legend_title"),
        label=f"{path.name} display `{expected_display_id}` support_legend_title",
    )

    normalized_decision_panel = _validate_shap_multigroup_decision_path_panel_display_payload(
        path=path,
        payload={
            "template_id": expected_template_id,
            "title": title,
            "caption": payload.get("caption"),
            "paper_role": payload.get("paper_role"),
            "panel_title": decision_panel_title,
            "x_label": decision_x_label,
            "y_label": decision_y_label,
            "legend_title": decision_legend_title,
            "baseline_value": payload.get("baseline_value"),
            "groups": payload.get("groups"),
        },
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    support_panels = _normalize_feature_response_support_panels(
        path=path,
        panels_payload=payload.get("support_panels"),
        expected_display_id=expected_display_id,
        panels_field="support_panels",
        minimum_count=2,
        maximum_count=2,
    )

    feature_order = [str(item) for item in normalized_decision_panel["feature_order"]]
    support_features = [str(panel["feature"]) for panel in support_panels]
    if not set(support_features).issubset(set(feature_order)):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.feature must stay within the shared group feature order"
        )
    expected_support_order = [feature for feature in feature_order if feature in set(support_features)]
    if support_features != expected_support_order:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.feature order must follow the shared group feature order"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "decision_panel_title": decision_panel_title,
        "decision_x_label": decision_x_label,
        "decision_y_label": decision_y_label,
        "decision_legend_title": decision_legend_title,
        "support_y_label": support_y_label,
        "support_legend_title": support_legend_title,
        "support_legend_labels": [
            "Response curve",
            "Observed support",
            "Subgroup support",
            "Bin support",
            "Extrapolation reminder",
        ],
        "baseline_value": float(normalized_decision_panel["baseline_value"]),
        "feature_order": feature_order,
        "groups": list(normalized_decision_panel["groups"]),
        "support_panels": support_panels,
    }

def _validate_shap_signed_importance_local_support_domain_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")

    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    support_y_label = _require_non_empty_string(
        payload.get("support_y_label"),
        label=f"{path.name} display `{expected_display_id}` support_y_label",
    )
    support_legend_title = _require_non_empty_string(
        payload.get("support_legend_title"),
        label=f"{path.name} display `{expected_display_id}` support_legend_title",
    )

    importance_panel_payload = payload.get("importance_panel")
    if not isinstance(importance_panel_payload, dict):
        raise ValueError(f"{path.name} display `{expected_display_id}` importance_panel must be an object")
    importance_panel_id = _require_non_empty_string(
        importance_panel_payload.get("panel_id"),
        label=f"{path.name} display `{expected_display_id}` importance_panel.panel_id",
    )
    importance_panel_label = _require_non_empty_string(
        importance_panel_payload.get("panel_label"),
        label=f"{path.name} display `{expected_display_id}` importance_panel.panel_label",
    )
    importance_panel_title = _require_non_empty_string(
        importance_panel_payload.get("title"),
        label=f"{path.name} display `{expected_display_id}` importance_panel.title",
    )
    normalized_importance_panel = _validate_shap_signed_importance_panel_display_payload(
        path=path,
        payload={
            "template_id": expected_template_id,
            "title": title,
            "caption": payload.get("caption"),
            "paper_role": payload.get("paper_role"),
            "x_label": importance_panel_payload.get("x_label"),
            "negative_label": importance_panel_payload.get("negative_label"),
            "positive_label": importance_panel_payload.get("positive_label"),
            "bars": importance_panel_payload.get("bars"),
        },
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )

    local_panel_payload = payload.get("local_panel")
    if not isinstance(local_panel_payload, dict):
        raise ValueError(f"{path.name} display `{expected_display_id}` local_panel must be an object")
    normalized_local_payload = _validate_shap_waterfall_local_explanation_panel_display_payload(
        path=path,
        payload={
            "template_id": expected_template_id,
            "title": title,
            "caption": payload.get("caption"),
            "paper_role": payload.get("paper_role"),
            "x_label": local_panel_payload.get("x_label"),
            "panels": [local_panel_payload],
        },
        expected_template_id=expected_template_id,
        expected_display_id=expected_display_id,
    )
    normalized_local_panel = dict(normalized_local_payload["panels"][0])

    support_panels = _normalize_feature_response_support_panels(
        path=path,
        panels_payload=payload.get("support_panels"),
        expected_display_id=expected_display_id,
        panels_field="support_panels",
        minimum_count=2,
        maximum_count=2,
    )

    global_feature_order = [str(item["feature"]) for item in normalized_importance_panel["bars"]]
    local_feature_order = [str(item["feature"]) for item in normalized_local_panel["contributions"]]
    if not set(local_feature_order).issubset(set(global_feature_order)):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` local_panel.contributions.feature must stay within the global signed-importance feature order"
        )
    expected_local_feature_order = [feature for feature in global_feature_order if feature in set(local_feature_order)]
    if local_feature_order != expected_local_feature_order:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` local_panel.contributions.feature order must follow the global signed-importance feature order"
        )

    support_features = [str(panel["feature"]) for panel in support_panels]
    if not set(support_features).issubset(set(global_feature_order)):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.feature must stay within the global signed-importance feature order"
        )
    expected_support_feature_order = [feature for feature in global_feature_order if feature in set(support_features)]
    if support_features != expected_support_feature_order:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` support_panels.feature order must follow the global signed-importance feature order"
        )

    panel_labels = [importance_panel_label, str(normalized_local_panel["panel_label"])] + [
        str(panel["panel_label"]) for panel in support_panels
    ]
    if len(set(panel_labels)) != len(panel_labels):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` panel_label values must stay globally unique across importance_panel, local_panel, and support_panels"
        )

    panel_ids = [importance_panel_id, str(normalized_local_panel["panel_id"])] + [str(panel["panel_id"]) for panel in support_panels]
    if len(set(panel_ids)) != len(panel_ids):
        raise ValueError(
            f"{path.name} display `{expected_display_id}` panel_id values must stay globally unique across importance_panel, local_panel, and support_panels"
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "support_y_label": support_y_label,
        "support_legend_title": support_legend_title,
        "support_legend_labels": [
            "Response curve",
            "Observed support",
            "Subgroup support",
            "Bin support",
            "Extrapolation reminder",
        ],
        "global_feature_order": global_feature_order,
        "local_feature_order": local_feature_order,
        "importance_panel": {
            "panel_id": importance_panel_id,
            "panel_label": importance_panel_label,
            "title": importance_panel_title,
            "x_label": str(normalized_importance_panel["x_label"]),
            "negative_label": str(normalized_importance_panel["negative_label"]),
            "positive_label": str(normalized_importance_panel["positive_label"]),
            "bars": list(normalized_importance_panel["bars"]),
        },
        "local_panel": normalized_local_panel,
        "support_panels": support_panels,
    }


__all__ = [
    "_normalize_feature_response_support_panels",
    "_validate_feature_response_support_domain_panel_display_payload",
    "_validate_shap_grouped_local_support_domain_panel_display_payload",
    "_validate_shap_multigroup_decision_path_support_domain_panel_display_payload",
    "_validate_shap_signed_importance_local_support_domain_panel_display_payload",
]
