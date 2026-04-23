from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, math

def _validate_shap_grouped_decision_path_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    panel_title = _require_non_empty_string(
        payload.get("panel_title"),
        label=f"{path.name} display `{expected_display_id}` panel_title",
    )
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    legend_title = _require_non_empty_string(
        payload.get("legend_title"),
        label=f"{path.name} display `{expected_display_id}` legend_title",
    )
    baseline_value = _require_numeric_value(
        payload.get("baseline_value"),
        label=f"{path.name} display `{expected_display_id}` baseline_value",
    )
    if not math.isfinite(baseline_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` baseline_value must be finite")

    groups_payload = payload.get("groups")
    if not isinstance(groups_payload, list) or not groups_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty groups list")
    if len(groups_payload) != 2:
        raise ValueError(f"{path.name} display `{expected_display_id}` groups must contain exactly two entries")

    normalized_groups: list[dict[str, Any]] = []
    seen_group_ids: set[str] = set()
    seen_group_labels: set[str] = set()
    expected_feature_order: list[str] | None = None
    for group_index, group_payload in enumerate(groups_payload):
        if not isinstance(group_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` groups[{group_index}] must be an object")
        group_id = _require_non_empty_string(
            group_payload.get("group_id"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].group_id",
        )
        if group_id in seen_group_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].group_id must be unique"
            )
        seen_group_ids.add(group_id)
        group_label = _require_non_empty_string(
            group_payload.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        predicted_value = _require_numeric_value(
            group_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value",
        )
        if not math.isfinite(predicted_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value must be finite"
            )

        contributions_payload = group_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions must be a non-empty list"
            )

        normalized_contributions: list[dict[str, Any]] = []
        previous_rank = 0
        contribution_sum = 0.0
        seen_features: set[str] = set()
        feature_order: list[str] = []
        cumulative_value = baseline_value
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}] must be an object"
                )
            rank = _require_non_negative_int(
                contribution_payload.get("rank"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].rank"
                ),
                allow_zero=False,
            )
            if rank <= previous_rank:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}] contribution ranks must be strictly increasing"
                )
            previous_rank = rank
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}].feature must be unique within its group"
                )
            seen_features.add(feature)
            feature_order.append(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            start_value = cumulative_value
            end_value = cumulative_value + shap_value
            cumulative_value = end_value
            contribution_sum += shap_value
            normalized_contributions.append(
                {
                    "rank": rank,
                    "feature": feature,
                    "shap_value": shap_value,
                    "start_value": start_value,
                    "end_value": end_value,
                }
            )

        if expected_feature_order is None:
            expected_feature_order = feature_order
        elif tuple(feature_order) != tuple(expected_feature_order):
            raise ValueError(f"{path.name} display `{expected_display_id}` contribution feature order must match across groups")

        if not math.isclose(
            predicted_value,
            baseline_value + contribution_sum,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value must equal baseline_value plus contribution sum"
            )
        normalized_groups.append(
            {
                "group_id": group_id,
                "group_label": group_label,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "panel_title": panel_title,
        "x_label": x_label,
        "y_label": y_label,
        "legend_title": legend_title,
        "baseline_value": baseline_value,
        "feature_order": list(expected_feature_order or ()),
        "groups": normalized_groups,
    }

def _validate_shap_multigroup_decision_path_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    panel_title = _require_non_empty_string(
        payload.get("panel_title"),
        label=f"{path.name} display `{expected_display_id}` panel_title",
    )
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    y_label = _require_non_empty_string(
        payload.get("y_label"),
        label=f"{path.name} display `{expected_display_id}` y_label",
    )
    legend_title = _require_non_empty_string(
        payload.get("legend_title"),
        label=f"{path.name} display `{expected_display_id}` legend_title",
    )
    baseline_value = _require_numeric_value(
        payload.get("baseline_value"),
        label=f"{path.name} display `{expected_display_id}` baseline_value",
    )
    if not math.isfinite(baseline_value):
        raise ValueError(f"{path.name} display `{expected_display_id}` baseline_value must be finite")

    groups_payload = payload.get("groups")
    if not isinstance(groups_payload, list) or not groups_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty groups list")
    if len(groups_payload) != 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` groups must contain exactly three entries")

    normalized_groups: list[dict[str, Any]] = []
    seen_group_ids: set[str] = set()
    seen_group_labels: set[str] = set()
    expected_feature_order: list[str] | None = None
    for group_index, group_payload in enumerate(groups_payload):
        if not isinstance(group_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` groups[{group_index}] must be an object")
        group_id = _require_non_empty_string(
            group_payload.get("group_id"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].group_id",
        )
        if group_id in seen_group_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].group_id must be unique"
            )
        seen_group_ids.add(group_id)
        group_label = _require_non_empty_string(
            group_payload.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        predicted_value = _require_numeric_value(
            group_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value",
        )
        if not math.isfinite(predicted_value):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value must be finite"
            )

        contributions_payload = group_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions must be a non-empty list"
            )

        normalized_contributions: list[dict[str, Any]] = []
        previous_rank = 0
        contribution_sum = 0.0
        seen_features: set[str] = set()
        feature_order: list[str] = []
        cumulative_value = baseline_value
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}] must be an object"
                )
            rank = _require_non_negative_int(
                contribution_payload.get("rank"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].rank"
                ),
                allow_zero=False,
            )
            if rank <= previous_rank:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}] contribution ranks must be strictly increasing"
                )
            previous_rank = rank
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}].feature must be unique within its group"
                )
            seen_features.add(feature)
            feature_order.append(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"groups[{group_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` groups[{group_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            start_value = cumulative_value
            end_value = cumulative_value + shap_value
            normalized_contributions.append(
                {
                    "rank": rank,
                    "feature": feature,
                    "shap_value": shap_value,
                    "start_value": start_value,
                    "end_value": end_value,
                }
            )
            contribution_sum += shap_value
            cumulative_value = end_value

        if expected_feature_order is None:
            expected_feature_order = feature_order
        elif feature_order != expected_feature_order:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}] feature order must match the first group"
            )
        if not math.isclose(predicted_value, baseline_value + contribution_sum, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` groups[{group_index}].predicted_value must equal baseline_value plus contribution sum"
            )

        normalized_groups.append(
            {
                "group_id": group_id,
                "group_label": group_label,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "panel_title": panel_title,
        "x_label": x_label,
        "y_label": y_label,
        "legend_title": legend_title,
        "baseline_value": baseline_value,
        "feature_order": expected_feature_order or [],
        "groups": normalized_groups,
    }


__all__ = [
    "_validate_shap_grouped_decision_path_panel_display_payload",
    "_validate_shap_multigroup_decision_path_panel_display_payload",
]
