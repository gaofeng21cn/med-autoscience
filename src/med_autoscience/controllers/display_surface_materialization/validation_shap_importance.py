from __future__ import annotations

from .shared import Any, Path, _require_non_empty_string, _require_non_negative_int, _require_numeric_value, math

def _validate_shap_bar_importance_display_payload(
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
    bars_payload = payload.get("bars")
    if not isinstance(bars_payload, list) or not bars_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty bars list")

    normalized_bars: list[dict[str, Any]] = []
    seen_features: set[str] = set()
    previous_rank = 0
    previous_importance = float("inf")
    for bar_index, bar_payload in enumerate(bars_payload):
        if not isinstance(bar_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` bars[{bar_index}] must be an object")
        rank = _require_non_negative_int(
            bar_payload.get("rank"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].rank",
            allow_zero=False,
        )
        if rank <= previous_rank:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].rank must be strictly increasing"
            )
        previous_rank = rank
        feature = _require_non_empty_string(
            bar_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].feature must be unique"
            )
        seen_features.add(feature)
        importance_value = _require_numeric_value(
            bar_payload.get("importance_value"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].importance_value",
        )
        if not math.isfinite(importance_value) or importance_value < 0.0:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].importance_value must be finite and non-negative"
            )
        if importance_value > previous_importance + 1e-12:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].importance_value must stay sorted descending by rank"
            )
        previous_importance = importance_value
        normalized_bars.append(
            {
                "rank": rank,
                "feature": feature,
                "importance_value": importance_value,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "bars": normalized_bars,
    }

def _validate_shap_signed_importance_panel_display_payload(
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
    negative_label = _require_non_empty_string(
        payload.get("negative_label"),
        label=f"{path.name} display `{expected_display_id}` negative_label",
    )
    positive_label = _require_non_empty_string(
        payload.get("positive_label"),
        label=f"{path.name} display `{expected_display_id}` positive_label",
    )
    bars_payload = payload.get("bars")
    if not isinstance(bars_payload, list) or not bars_payload:
        raise ValueError(f"{path.name} display `{expected_display_id}` must contain a non-empty bars list")

    normalized_bars: list[dict[str, Any]] = []
    seen_features: set[str] = set()
    previous_rank = 0
    previous_absolute_value = float("inf")
    for bar_index, bar_payload in enumerate(bars_payload):
        if not isinstance(bar_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` bars[{bar_index}] must be an object")
        rank = _require_non_negative_int(
            bar_payload.get("rank"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].rank",
            allow_zero=False,
        )
        if rank <= previous_rank:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].rank must be strictly increasing"
            )
        previous_rank = rank
        feature = _require_non_empty_string(
            bar_payload.get("feature"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].feature",
        )
        if feature in seen_features:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].feature must be unique"
            )
        seen_features.add(feature)
        signed_importance_value = _require_numeric_value(
            bar_payload.get("signed_importance_value"),
            label=f"{path.name} display `{expected_display_id}` bars[{bar_index}].signed_importance_value",
        )
        if not math.isfinite(signed_importance_value) or math.isclose(
            signed_importance_value,
            0.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].signed_importance_value must be finite and non-zero"
            )
        absolute_value = abs(signed_importance_value)
        if absolute_value > previous_absolute_value + 1e-12:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` bars[{bar_index}].signed_importance_value must stay sorted by descending absolute magnitude"
            )
        previous_absolute_value = absolute_value
        normalized_bars.append(
            {
                "rank": rank,
                "feature": feature,
                "signed_importance_value": signed_importance_value,
            }
        )

    return {
        "display_id": expected_display_id,
        "template_id": expected_template_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "paper_role": str(payload.get("paper_role") or "").strip(),
        "x_label": x_label,
        "negative_label": negative_label,
        "positive_label": positive_label,
        "bars": normalized_bars,
    }

def _validate_shap_multicohort_importance_panel_display_payload(
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
        raise ValueError(f"{path.name} display `{expected_display_id}` panels must not exceed three cohorts")

    normalized_panels: list[dict[str, Any]] = []
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_cohort_labels: set[str] = set()
    expected_feature_order: list[str] | None = None

    for panel_index, panel_payload in enumerate(panels_payload):
        if not isinstance(panel_payload, dict):
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel_payload.get("panel_id"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id",
        )
        if panel_id in seen_panel_ids:
            raise ValueError(f"{path.name} display `{expected_display_id}` panels[{panel_index}].panel_id must be unique")
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
        cohort_label = _require_non_empty_string(
            panel_payload.get("cohort_label"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].cohort_label",
        )
        if cohort_label in seen_cohort_labels:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}].cohort_label must be unique"
            )
        seen_cohort_labels.add(cohort_label)
        panel_title = _require_non_empty_string(
            panel_payload.get("title"),
            label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].title",
        )
        bars_payload = panel_payload.get("bars")
        if not isinstance(bars_payload, list) or not bars_payload:
            raise ValueError(
                f"{path.name} display `{expected_display_id}` panels[{panel_index}] must contain a non-empty bars list"
            )

        normalized_bars: list[dict[str, Any]] = []
        seen_features: set[str] = set()
        previous_rank = 0
        previous_importance = float("inf")
        feature_order: list[str] = []
        for bar_index, bar_payload in enumerate(bars_payload):
            if not isinstance(bar_payload, dict):
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}] must be an object"
                )
            rank = _require_non_negative_int(
                bar_payload.get("rank"),
                label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].rank",
                allow_zero=False,
            )
            if rank <= previous_rank:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].rank must be strictly increasing"
                )
            previous_rank = rank
            feature = _require_non_empty_string(
                bar_payload.get("feature"),
                label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].feature",
            )
            if feature in seen_features:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].feature must be unique within each panel"
                )
            seen_features.add(feature)
            feature_order.append(feature)
            importance_value = _require_numeric_value(
                bar_payload.get("importance_value"),
                label=f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].importance_value",
            )
            if not math.isfinite(importance_value) or importance_value < 0.0:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].importance_value must be finite and non-negative"
                )
            if importance_value > previous_importance + 1e-12:
                raise ValueError(
                    f"{path.name} display `{expected_display_id}` panels[{panel_index}].bars[{bar_index}].importance_value must stay sorted descending by rank"
                )
            previous_importance = importance_value
            normalized_bars.append(
                {
                    "rank": rank,
                    "feature": feature,
                    "importance_value": importance_value,
                }
            )

        if expected_feature_order is None:
            expected_feature_order = feature_order
        elif tuple(feature_order) != tuple(expected_feature_order):
            raise ValueError(f"{path.name} display `{expected_display_id}` bars feature order must match across panels")

        normalized_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": panel_title,
                "cohort_label": cohort_label,
                "bars": normalized_bars,
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


__all__ = [
    "_validate_shap_bar_importance_display_payload",
    "_validate_shap_signed_importance_panel_display_payload",
    "_validate_shap_multicohort_importance_panel_display_payload",
]
