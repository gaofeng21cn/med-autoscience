from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, math

def _validate_shap_summary_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(payload.get("x_label"), label=f"{path.name} display `{expected_display_id}` x_label")
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty rows list")
    normalized_rows: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` rows[{row_index}] must be an object")
        points = row.get("points")
        if not isinstance(points, list) or not points:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` rows[{row_index}] must contain a non-empty points list"
            )
        normalized_points: list[dict[str, Any]] = []
        for point_index, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` rows[{row_index}].points[{point_index}] must be an object"
                )
            normalized_points.append(
                {
                    "shap_value": _require_numeric_value(
                        point.get("shap_value"),
                        label=(
                            f"{path.name} display `{expected_display_id}` rows[{row_index}].points[{point_index}]."
                            "shap_value"
                        ),
                    ),
                    "feature_value": _require_numeric_value(
                        point.get("feature_value"),
                        label=(
                            f"{path.name} display `{expected_display_id}` rows[{row_index}].points[{point_index}]."
                            "feature_value"
                        ),
                    ),
                }
            )
        normalized_rows.append(
            {
                "feature": _require_non_empty_string(
                    row.get("feature"),
                    label=f"{path.name} display `{expected_display_id}` rows[{row_index}].feature",
                ),
                "points": normalized_points,
            }
        )
    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "rows": normalized_rows,
    }

def _validate_shap_dependence_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    y_label = _require_non_empty_string(payload.get("y_label"), label=f"{path.name} display `{expected_display_id}` y_label")
    colorbar_label = _require_non_empty_string(
        payload.get("colorbar_label"),
        label=f"{path.name} display `{expected_display_id}` colorbar_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_features: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        feature = _require_non_empty_string(
            panel_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].feature must be unique"
            )
        seen_features.add(feature)

        points_payload = panel_payload.get("points")
        if not isinstance(points_payload, list) or not points_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].points must be a non-empty list"
            )
        normalized_points: list[dict[str, float]] = []
        for point_index, point_payload in enumerate(points_payload):
            if not isinstance(point_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].points[{point_index}] must be an object"
                )
            feature_value = _require_numeric_value(
                point_payload.get("feature_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].points[{point_index}].feature_value"
                ),
            )
            shap_value = _require_numeric_value(
                point_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].points[{point_index}].shap_value"
                ),
            )
            interaction_value = _require_numeric_value(
                point_payload.get("interaction_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].points[{point_index}].interaction_value"
                ),
            )
            if not all(math.isfinite(value) for value in (feature_value, shap_value, interaction_value)):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].points[{point_index}] point values must be finite"
                )
            normalized_points.append(
                {
                    "feature_value": feature_value,
                    "shap_value": shap_value,
                    "interaction_value": interaction_value,
                }
            )

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "x_label": _require_non_empty_string(
                    panel_payload.get("x_label"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].x_label",
                ),
                "feature": feature,
                "interaction_feature": _require_non_empty_string(
                    panel_payload.get("interaction_feature"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].interaction_feature",
                ),
                "points": normalized_points,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "y_label": y_label,
        "colorbar_label": colorbar_label,
        "panels": normalized_panels,
    }

def _validate_shap_waterfall_local_explanation_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most three entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_case_labels: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        case_label = _require_non_empty_string(
            panel_payload.get("case_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].case_label",
        )
        if case_label in seen_case_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].case_label must be unique"
            )
        seen_case_labels.add(case_label)
        baseline_value = _require_numeric_value(
            panel_payload.get("baseline_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric_value(
            panel_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].predicted_value",
        )
        if not all(math.isfinite(value) for value in (baseline_value, predicted_value)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] values must be finite"
            )
        contributions_payload = panel_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions must be a non-empty list"
            )
        normalized_contributions: list[dict[str, Any]] = []
        seen_features: set[str] = set()
        contribution_sum = 0.0
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}].feature must be unique within its panel"
                )
            seen_features.add(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, rel_tol=0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            normalized_contributions.append(
                {
                    "feature": feature,
                    "shap_value": shap_value,
                    "feature_value_text": str(contribution_payload.get("feature_value_text") or "").strip(),
                }
            )
            contribution_sum += shap_value
        if not math.isclose(predicted_value, baseline_value + contribution_sum, rel_tol=0.0, abs_tol=1e-6):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].predicted_value must equal baseline_value plus contribution sum"
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "case_label": case_label,
                "baseline_value": baseline_value,
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
        "x_label": x_label,
        "panels": normalized_panels,
    }

def _validate_shap_force_like_summary_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    panels_payload = payload.get("panels")
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty panels list")
    if len(panels_payload) > 3:
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must contain at most three entries")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_case_labels: set[str] = set()
    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique"
            )
        seen_panel_ids.add(panel_id)
        panel_label = _require_non_empty_string(
            panel_payload.get("panel_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label",
        )
        if panel_label in seen_panel_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_label must be unique"
            )
        seen_panel_labels.add(panel_label)
        case_label = _require_non_empty_string(
            panel_payload.get("case_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].case_label",
        )
        if case_label in seen_case_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].case_label must be unique"
            )
        seen_case_labels.add(case_label)
        baseline_value = _require_numeric_value(
            panel_payload.get("baseline_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric_value(
            panel_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].predicted_value",
        )
        if not all(math.isfinite(value) for value in (baseline_value, predicted_value)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] values must be finite"
            )
        contributions_payload = panel_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions must be a non-empty list"
            )

        normalized_contributions: list[dict[str, Any]] = []
        seen_features: set[str] = set()
        contribution_sum = 0.0
        previous_abs_magnitude = float("inf")
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}].feature must be unique within its panel"
                )
            seen_features.add(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"panels[{panel_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            magnitude = abs(shap_value)
            if magnitude > previous_abs_magnitude + 1e-9:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}] contributions must be sorted by descending absolute shap_value within each panel"
                )
            previous_abs_magnitude = magnitude
            contribution_sum += shap_value
            normalized_contributions.append(
                {
                    "feature": feature,
                    "feature_value_text": str(contribution_payload.get("feature_value_text") or "").strip(),
                    "shap_value": shap_value,
                }
            )
        if not math.isclose(
            predicted_value,
            baseline_value + contribution_sum,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].predicted_value must equal baseline_value plus contribution sum"
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
                ),
                "case_label": case_label,
                "baseline_value": baseline_value,
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
        "x_label": x_label,
        "panels": normalized_panels,
    }

def _normalize_shap_grouped_local_panels(
    *,
    path: Path,
    panels_payload: object,
    expected_display_id: str,
    panels_field: str,
    minimum_count: int,
    maximum_count: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(panels_payload, list) or not panels_payload:
        raise ValueError(
            f"{path.name} display `{expected_display_id}` must contain a non-empty {panels_field} list"
        )
    if len(panels_payload) < minimum_count or len(panels_payload) > maximum_count:
        if minimum_count == maximum_count:
            count_description = f"exactly {minimum_count}"
        elif minimum_count == 1:
            count_description = f"at most {maximum_count}"
        else:
            count_description = f"between {minimum_count} and {maximum_count}"
        raise ValueError(
            f"{path.name} display `{expected_display_id}` {panels_field} must contain {count_description} entries"
        )

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_group_labels: set[str] = set()
    expected_feature_order: list[str] | None = None
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
        group_label = _require_non_empty_string(
            panel_payload.get("group_label"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].group_label",
        )
        if group_label in seen_group_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].group_label must be unique"
            )
        seen_group_labels.add(group_label)
        baseline_value = _require_numeric_value(
            panel_payload.get("baseline_value"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].baseline_value",
        )
        predicted_value = _require_numeric_value(
            panel_payload.get("predicted_value"),
            label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].predicted_value",
        )
        if not all(math.isfinite(value) for value in (baseline_value, predicted_value)):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}] values must be finite"
            )
        contributions_payload = panel_payload.get("contributions")
        if not isinstance(contributions_payload, list) or not contributions_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].contributions must be a non-empty list"
            )

        normalized_contributions: list[dict[str, Any]] = []
        seen_features: set[str] = set()
        previous_rank = 0
        contribution_sum = 0.0
        feature_order: list[str] = []
        for contribution_index, contribution_payload in enumerate(contributions_payload):
            if not isinstance(contribution_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].contributions[{contribution_index}] must be an object"
                )
            rank = _require_non_negative_int(
                contribution_payload.get("rank"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].contributions[{contribution_index}].rank"
                ),
                allow_zero=False,
            )
            if rank <= previous_rank:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}] contribution ranks must be strictly increasing"
                )
            previous_rank = rank
            feature = _require_non_empty_string(
                contribution_payload.get("feature"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].contributions[{contribution_index}].feature"
                ),
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].contributions[{contribution_index}].feature must be unique within its panel"
                )
            seen_features.add(feature)
            feature_order.append(feature)
            shap_value = _require_numeric_value(
                contribution_payload.get("shap_value"),
                label=(
                    f"{path.name} display `{expected_display_id}` "
                    f"{panels_field}[{panel_index}].contributions[{contribution_index}].shap_value"
                ),
            )
            if not math.isfinite(shap_value) or math.isclose(shap_value, 0.0, abs_tol=1e-12):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].contributions[{contribution_index}].shap_value must be finite and non-zero"
                )
            contribution_sum += shap_value
            normalized_contributions.append(
                {
                    "rank": rank,
                    "feature": feature,
                    "shap_value": shap_value,
                }
            )

        if expected_feature_order is None:
            expected_feature_order = feature_order
        elif tuple(feature_order) != tuple(expected_feature_order):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` contribution feature order must match across {panels_field}"
            )

        if not math.isclose(
            predicted_value,
            baseline_value + contribution_sum,
            rel_tol=1e-9,
            abs_tol=1e-9,
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].predicted_value must equal baseline_value plus contribution sum"
            )
        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel_payload.get("title"),
                    label=f"{path.name} display `{expected_display_id}` {panels_field}[{panel_index}].title",
                ),
                "group_label": group_label,
                "baseline_value": baseline_value,
                "predicted_value": predicted_value,
                "contributions": normalized_contributions,
            }
        )

    return normalized_panels, list(expected_feature_order or ())

def _validate_shap_grouped_local_explanation_panel_display_payload(
    *,
    path: Path,
    payload: dict[str, Any],
    expected_template_id: str,
    expected_display_id: str,
) -> dict[str, Any]:
    if str(payload.get("template_id") or "").strip() != expected_template_id:
        raise ValueError(f"{path.name} display `{expected_display_id}` must use template_id `{expected_template_id}`")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} display `{expected_display_id}` title")
    x_label = _require_non_empty_string(
        payload.get("x_label"),
        label=f"{path.name} display `{expected_display_id}` x_label",
    )
    normalized_panels, _ = _normalize_shap_grouped_local_panels(
        path=path,
        panels_payload=payload.get("panels"),
        expected_display_id=expected_display_id,
        panels_field="panels",
        minimum_count=1,
        maximum_count=3,
    )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "panels": normalized_panels,
    }


__all__ = [
    "_validate_shap_summary_display_payload",
    "_validate_shap_dependence_panel_display_payload",
    "_validate_shap_waterfall_local_explanation_panel_display_payload",
    "_validate_shap_force_like_summary_panel_display_payload",
    "_normalize_shap_grouped_local_panels",
    "_validate_shap_grouped_local_explanation_panel_display_payload",
]
