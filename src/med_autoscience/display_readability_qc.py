from __future__ import annotations

import math
from typing import Any


DEFAULT_MIN_TERMINAL_SEPARATION = 0.01
DEFAULT_MIN_OBSERVED_RISK_SPREAD = 0.01
DEFAULT_MIN_PREDICTED_RISK_SPREAD = 0.005
DEFAULT_MIN_EVENT_COUNT_SPREAD = 1.0
DEFAULT_MIN_SHAP_FEATURE_ROW_HEIGHT_INCHES = 0.5
DEFAULT_MIN_SHAP_FEATURE_ROW_GAP_INCHES = 0.08
DEFAULT_MIN_SHAP_FEATURE_LABEL_PANEL_GAP_INCHES = 0.08


def _issue(
    *,
    rule_id: str,
    message: str,
    target: str,
    observed: object | None = None,
    expected: object | None = None,
) -> dict[str, Any]:
    issue: dict[str, Any] = {
        "audit_class": "readability",
        "rule_id": rule_id,
        "severity": "error",
        "message": message,
        "target": target,
    }
    if observed is not None:
        issue["observed"] = observed
    if expected is not None:
        issue["expected"] = expected
    return issue


def _require_mapping(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return dict(value)


def _require_numeric(value: object, *, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{label} must be finite")
    return normalized


def _readability_override(layout_sidecar: dict[str, object]) -> dict[str, Any]:
    render_context = layout_sidecar.get("render_context")
    if render_context is None:
        return {}
    render_context_mapping = _require_mapping(render_context, label="layout_sidecar.render_context")
    override = render_context_mapping.get("readability_override")
    if override is None:
        return {}
    return _require_mapping(override, label="layout_sidecar.render_context.readability_override")


def _resolve_threshold(
    override: dict[str, Any],
    *,
    field_name: str,
    default_value: float,
) -> float:
    raw_value = override.get(field_name, default_value)
    threshold = _require_numeric(raw_value, label=f"readability_override.{field_name}")
    if threshold < 0:
        raise ValueError(f"readability_override.{field_name} must be >= 0")
    return threshold


def _check_survival_group_readability(layout_sidecar: dict[str, object]) -> list[dict[str, Any]]:
    metrics = _require_mapping(layout_sidecar.get("metrics"), label="layout_sidecar.metrics")
    override = _readability_override(layout_sidecar)
    issues: list[dict[str, Any]] = []

    groups = metrics.get("groups")
    if isinstance(groups, list) and len(groups) >= 2:
        terminal_values: list[float] = []
        for index, group in enumerate(groups):
            group_mapping = _require_mapping(group, label=f"layout_sidecar.metrics.groups[{index}]")
            values = group_mapping.get("values")
            if not isinstance(values, list) or not values:
                raise ValueError(f"layout_sidecar.metrics.groups[{index}].values must be a non-empty list")
            terminal_values.append(
                _require_numeric(
                    values[-1],
                    label=f"layout_sidecar.metrics.groups[{index}].values[-1]",
                )
            )
        minimum_terminal_separation = _resolve_threshold(
            override,
            field_name="minimum_terminal_separation",
            default_value=DEFAULT_MIN_TERMINAL_SEPARATION,
        )
        terminal_spread = max(terminal_values) - min(terminal_values)
        if terminal_spread < minimum_terminal_separation:
            issues.append(
                _issue(
                    rule_id="risk_separation_not_readable",
                    message="survival groups are too compressed to convey the intended separation",
                    target="metrics.groups",
                    observed={"terminal_spread": terminal_spread},
                    expected={"minimum_terminal_separation": minimum_terminal_separation},
                )
            )

    panels = metrics.get("panels")
    if isinstance(panels, list):
        minimum_terminal_separation = _resolve_threshold(
            override,
            field_name="minimum_terminal_separation",
            default_value=DEFAULT_MIN_TERMINAL_SEPARATION,
        )
        for panel_index, panel in enumerate(panels):
            panel_mapping = _require_mapping(panel, label=f"layout_sidecar.metrics.panels[{panel_index}]")
            panel_groups = panel_mapping.get("groups")
            if not isinstance(panel_groups, list) or len(panel_groups) < 2:
                continue
            terminal_values = []
            for group_index, group in enumerate(panel_groups):
                group_mapping = _require_mapping(
                    group,
                    label=f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}]",
                )
                values = group_mapping.get("values")
                if not isinstance(values, list) or not values:
                    raise ValueError(
                        f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}].values must be a non-empty list"
                    )
                terminal_values.append(
                    _require_numeric(
                        values[-1],
                        label=f"layout_sidecar.metrics.panels[{panel_index}].groups[{group_index}].values[-1]",
                    )
                )
            terminal_spread = max(terminal_values) - min(terminal_values)
            if terminal_spread < minimum_terminal_separation:
                issues.append(
                    _issue(
                        rule_id="risk_separation_not_readable",
                        message="stratified cumulative-incidence panel is too compressed to convey the intended separation",
                        target=f"metrics.panels[{panel_index}].groups",
                        observed={
                            "panel_label": str(panel_mapping.get("panel_label") or ""),
                            "terminal_spread": terminal_spread,
                        },
                        expected={"minimum_terminal_separation": minimum_terminal_separation},
                    )
                )

    risk_group_summaries = metrics.get("risk_group_summaries")
    if isinstance(risk_group_summaries, list) and len(risk_group_summaries) >= 2:
        observed_risks: list[float] = []
        predicted_risks: list[float] = []
        event_counts: list[float] = []
        for index, item in enumerate(risk_group_summaries):
            summary = _require_mapping(item, label=f"layout_sidecar.metrics.risk_group_summaries[{index}]")
            observed_risks.append(
                _require_numeric(
                    summary.get("observed_km_risk_5y"),
                    label=f"layout_sidecar.metrics.risk_group_summaries[{index}].observed_km_risk_5y",
                )
            )
            predicted_risks.append(
                _require_numeric(
                    summary.get("mean_predicted_risk_5y"),
                    label=f"layout_sidecar.metrics.risk_group_summaries[{index}].mean_predicted_risk_5y",
                )
            )
            event_counts.append(
                _require_numeric(
                    summary.get("events_5y"),
                    label=f"layout_sidecar.metrics.risk_group_summaries[{index}].events_5y",
                )
            )
        minimum_observed_risk_spread = _resolve_threshold(
            override,
            field_name="minimum_observed_risk_spread",
            default_value=DEFAULT_MIN_OBSERVED_RISK_SPREAD,
        )
        minimum_predicted_risk_spread = _resolve_threshold(
            override,
            field_name="minimum_predicted_risk_spread",
            default_value=DEFAULT_MIN_PREDICTED_RISK_SPREAD,
        )
        minimum_event_count_spread = _resolve_threshold(
            override,
            field_name="minimum_event_count_spread",
            default_value=DEFAULT_MIN_EVENT_COUNT_SPREAD,
        )
        observed_spread = max(observed_risks) - min(observed_risks)
        predicted_spread = max(predicted_risks) - min(predicted_risks)
        event_count_spread = max(event_counts) - min(event_counts)
        if observed_spread < minimum_observed_risk_spread:
            issues.append(
                _issue(
                    rule_id="observed_risk_spread_not_readable",
                    message="observed risk spread is too compressed to support manuscript-facing stratification",
                    target="metrics.risk_group_summaries",
                    observed={"observed_risk_spread": observed_spread},
                    expected={"minimum_observed_risk_spread": minimum_observed_risk_spread},
                )
            )
        if predicted_spread < minimum_predicted_risk_spread:
            issues.append(
                _issue(
                    rule_id="predicted_risk_spread_not_readable",
                    message="predicted risk spread is too compressed to support manuscript-facing stratification",
                    target="metrics.risk_group_summaries",
                    observed={"predicted_risk_spread": predicted_spread},
                    expected={"minimum_predicted_risk_spread": minimum_predicted_risk_spread},
                )
            )
        if event_count_spread < minimum_event_count_spread:
            issues.append(
                _issue(
                    rule_id="event_count_spread_not_readable",
                    message="event-count spread is too compressed to support manuscript-facing stratification",
                    target="metrics.risk_group_summaries",
                    observed={"event_count_spread": event_count_spread},
                    expected={"minimum_event_count_spread": minimum_event_count_spread},
                )
            )
        for previous_value, current_value in zip(
            predicted_risks[:-1], predicted_risks[1:], strict=True
        ):
            if current_value + 1e-12 >= previous_value:
                continue
            issues.append(
                _issue(
                    rule_id="predicted_risk_order_not_monotonic",
                    message="predicted risk must remain monotonic non-decreasing across ordered risk groups",
                    target="metrics.risk_group_summaries",
                    observed={"predicted_risks": predicted_risks},
                )
            )
            break
        for previous_value, current_value in zip(
            observed_risks[:-1], observed_risks[1:], strict=True
        ):
            if current_value + 1e-12 >= previous_value:
                continue
            issues.append(
                _issue(
                    rule_id="observed_risk_order_not_monotonic",
                    message="observed risk must remain monotonic non-decreasing across ordered risk groups",
                    target="metrics.risk_group_summaries",
                    observed={"observed_risks": observed_risks},
                )
            )
            break
        for previous_value, current_value in zip(
            event_counts[:-1], event_counts[1:], strict=True
        ):
            if current_value + 1e-12 >= previous_value:
                continue
            issues.append(
                _issue(
                    rule_id="event_count_order_not_monotonic",
                    message="event counts must remain monotonic non-decreasing across ordered risk groups",
                    target="metrics.risk_group_summaries",
                    observed={"event_counts": event_counts},
                )
            )
            break

    return issues


def _check_shap_summary_readability(layout_sidecar: dict[str, object]) -> list[dict[str, Any]]:
    metrics = _require_mapping(layout_sidecar.get("metrics"), label="layout_sidecar.metrics")
    override = _readability_override(layout_sidecar)
    figure_height_inches = _require_numeric(
        metrics.get("figure_height_inches"),
        label="layout_sidecar.metrics.figure_height_inches",
    )
    figure_width_inches = _require_numeric(
        metrics.get("figure_width_inches"),
        label="layout_sidecar.metrics.figure_width_inches",
    )
    if figure_height_inches <= 0:
        raise ValueError("layout_sidecar.metrics.figure_height_inches must be > 0")
    if figure_width_inches <= 0:
        raise ValueError("layout_sidecar.metrics.figure_width_inches must be > 0")
    minimum_feature_row_height_inches = _resolve_threshold(
        override,
        field_name="minimum_feature_row_height_inches",
        default_value=DEFAULT_MIN_SHAP_FEATURE_ROW_HEIGHT_INCHES,
    )
    minimum_feature_row_gap_inches = _resolve_threshold(
        override,
        field_name="minimum_feature_row_gap_inches",
        default_value=DEFAULT_MIN_SHAP_FEATURE_ROW_GAP_INCHES,
    )
    minimum_feature_label_panel_gap_inches = _resolve_threshold(
        override,
        field_name="minimum_feature_label_panel_gap_inches",
        default_value=DEFAULT_MIN_SHAP_FEATURE_LABEL_PANEL_GAP_INCHES,
    )

    raw_layout_boxes = layout_sidecar.get("layout_boxes")
    if not isinstance(raw_layout_boxes, list):
        raise ValueError("layout_sidecar.layout_boxes must be a list")
    raw_panel_boxes = layout_sidecar.get("panel_boxes")
    if not isinstance(raw_panel_boxes, list):
        raise ValueError("layout_sidecar.panel_boxes must be a list")

    feature_rows: list[dict[str, float | str]] = []
    feature_labels: dict[str, dict[str, float | str]] = {}
    for index, item in enumerate(raw_layout_boxes):
        box = _require_mapping(item, label=f"layout_sidecar.layout_boxes[{index}]")
        box_type = str(box.get("box_type") or "").strip()
        y0 = _require_numeric(box.get("y0"), label=f"layout_sidecar.layout_boxes[{index}].y0")
        y1 = _require_numeric(box.get("y1"), label=f"layout_sidecar.layout_boxes[{index}].y1")
        if y1 < y0:
            raise ValueError(f"layout_sidecar.layout_boxes[{index}] must satisfy y1 >= y0")
        if box_type == "feature_row":
            feature_rows.append(
                {
                    "box_id": str(box.get("box_id") or f"feature_row_{index}").strip(),
                    "y0": y0,
                    "y1": y1,
                }
            )
            continue
        if box_type == "feature_label":
            x0 = _require_numeric(box.get("x0"), label=f"layout_sidecar.layout_boxes[{index}].x0")
            x1 = _require_numeric(box.get("x1"), label=f"layout_sidecar.layout_boxes[{index}].x1")
            if x1 < x0:
                raise ValueError(f"layout_sidecar.layout_boxes[{index}] must satisfy x1 >= x0")
            feature_labels[str(box.get("box_id") or f"feature_label_{index}").strip()] = {
                "x0": x0,
                "x1": x1,
            }

    primary_panel = _require_mapping(raw_panel_boxes[0], label="layout_sidecar.panel_boxes[0]") if raw_panel_boxes else None
    panel_x0 = None
    if primary_panel is not None:
        panel_x0 = _require_numeric(primary_panel.get("x0"), label="layout_sidecar.panel_boxes[0].x0")

    issues: list[dict[str, Any]] = []
    for row in feature_rows:
        row_height_inches = (float(row["y1"]) - float(row["y0"])) * figure_height_inches
        if row_height_inches < minimum_feature_row_height_inches:
            issues.append(
                _issue(
                    rule_id="feature_row_height_not_readable",
                    message="feature row height is too small for manuscript-facing SHAP readability",
                    target=f"layout_boxes.{row['box_id']}",
                    observed={"feature_row_height_inches": row_height_inches},
                    expected={"minimum_feature_row_height_inches": minimum_feature_row_height_inches},
                )
            )

    sorted_rows = sorted(feature_rows, key=lambda item: float(item["y0"]))
    for previous_row, current_row in zip(sorted_rows, sorted_rows[1:]):
        row_gap_inches = (float(current_row["y0"]) - float(previous_row["y1"])) * figure_height_inches
        if row_gap_inches < minimum_feature_row_gap_inches:
            issues.append(
                _issue(
                    rule_id="feature_row_gap_not_readable",
                    message="feature-row gap is too small for manuscript-facing SHAP readability",
                    target=f"layout_boxes.{previous_row['box_id']}->{current_row['box_id']}",
                    observed={"feature_row_gap_inches": row_gap_inches},
                    expected={"minimum_feature_row_gap_inches": minimum_feature_row_gap_inches},
                )
            )

    raw_feature_labels = metrics.get("feature_labels")
    if raw_feature_labels is None:
        raw_feature_labels = []
    if not isinstance(raw_feature_labels, list):
        raise ValueError("layout_sidecar.metrics.feature_labels must be a list when present")
    if panel_x0 is not None:
        for index, item in enumerate(raw_feature_labels):
            entry = _require_mapping(item, label=f"layout_sidecar.metrics.feature_labels[{index}]")
            label_box_id = str(entry.get("label_box_id") or "").strip()
            if not label_box_id:
                raise ValueError(
                    f"layout_sidecar.metrics.feature_labels[{index}].label_box_id must be non-empty"
                )
            label_box = feature_labels.get(label_box_id)
            if label_box is None:
                continue
            label_panel_gap_inches = (panel_x0 - float(label_box["x1"])) * figure_width_inches
            if label_panel_gap_inches < minimum_feature_label_panel_gap_inches:
                issues.append(
                    _issue(
                        rule_id="feature_label_panel_gap_not_readable",
                        message="feature-label gap to the shap panel is too small for manuscript-facing readability",
                        target=f"layout_boxes.{label_box_id}",
                        observed={"feature_label_panel_gap_inches": label_panel_gap_inches},
                        expected={"minimum_feature_label_panel_gap_inches": minimum_feature_label_panel_gap_inches},
                    )
                )

    return issues


def run_readability_qc(*, qc_profile: str, layout_sidecar: dict[str, object]) -> list[dict[str, Any]]:
    normalized_profile = str(qc_profile or "").strip()
    if normalized_profile == "publication_survival_curve":
        return _check_survival_group_readability(layout_sidecar)
    if normalized_profile == "publication_shap_summary":
        return _check_shap_summary_readability(layout_sidecar)
    return []
