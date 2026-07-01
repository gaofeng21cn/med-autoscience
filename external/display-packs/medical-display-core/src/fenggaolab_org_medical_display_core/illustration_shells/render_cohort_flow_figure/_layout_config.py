from __future__ import annotations

from typing import Any

from ...shared_parts.common import _require_non_empty_string


COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}
COHORT_FLOW_LAYOUT_MODES = {"two_panel_flow", "single_panel_cards", "participant_flow"}
COHORT_FLOW_STEP_ROLE_LABELS: dict[str, str] = {
    "historical_reference": "Historical patient reference",
    "current_patient_surface": "Current patient surface",
    "clinician_surface": "Clinician surface",
}


def read_float(mapping: dict[str, Any], key: str, default: float) -> float:
    value = mapping.get(key, default)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return float(default)


def read_ratio(mapping: dict[str, Any], key: str) -> float | None:
    value = mapping.get(key)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        normalized = float(value)
        if 0.0 < normalized < 1.0:
            return normalized
    return None


def role_color(style_roles: dict[str, Any], role_name: str) -> str:
    return _require_non_empty_string(
        style_roles.get(role_name),
        label=f"cohort_flow_figure render_context.style_roles.{role_name}",
    )


__all__ = [
    "COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES",
    "COHORT_FLOW_LAYOUT_MODES",
    "COHORT_FLOW_STEP_ROLE_LABELS",
    "read_float",
    "read_ratio",
    "role_color",
]
