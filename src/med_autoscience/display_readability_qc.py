from __future__ import annotations

import math
from typing import Any


DEFAULT_MIN_TERMINAL_SEPARATION = 0.01
DEFAULT_MIN_OBSERVED_RISK_SPREAD = 0.01
DEFAULT_MIN_PREDICTED_RISK_SPREAD = 0.005


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

    risk_group_summaries = metrics.get("risk_group_summaries")
    if isinstance(risk_group_summaries, list) and len(risk_group_summaries) >= 2:
        observed_risks: list[float] = []
        predicted_risks: list[float] = []
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
        observed_spread = max(observed_risks) - min(observed_risks)
        predicted_spread = max(predicted_risks) - min(predicted_risks)
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

    return issues


def run_readability_qc(*, qc_profile: str, layout_sidecar: dict[str, object]) -> list[dict[str, Any]]:
    normalized_profile = str(qc_profile or "").strip()
    if normalized_profile == "publication_survival_curve":
        return _check_survival_group_readability(layout_sidecar)
    return []
