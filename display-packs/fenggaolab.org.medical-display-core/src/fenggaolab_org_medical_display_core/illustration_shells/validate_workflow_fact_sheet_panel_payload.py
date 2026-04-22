from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
from med_autoscience import display_registry

matplotlib.use("Agg")

from ..shared import (
    _require_non_empty_string,
)


_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}
_COHORT_FLOW_LAYOUT_MODES = {"two_panel_flow", "single_panel_cards"}
_COHORT_FLOW_STEP_ROLE_LABELS: dict[str, str] = {
    "historical_reference": "Historical patient reference",
    "current_patient_surface": "Current patient surface",
    "clinician_surface": "Clinician surface",
}


def _validate_workflow_fact_sheet_panel_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    expected_shell_id = display_registry.get_illustration_shell_spec("workflow_fact_sheet_panel").shell_id
    shell_id = _require_non_empty_string(payload.get("shell_id"), label=f"{path.name} shell_id")
    if shell_id != expected_shell_id:
        raise ValueError(f"{path.name} shell_id must be `{expected_shell_id}`")
    display_id = _require_non_empty_string(payload.get("display_id"), label=f"{path.name} display_id")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} title")

    sections_payload = payload.get("sections")
    if not isinstance(sections_payload, list) or len(sections_payload) != 4:
        raise ValueError(f"{path.name} must contain exactly four sections")

    expected_layout_roles = {"top_left", "top_right", "bottom_left", "bottom_right"}
    seen_section_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_layout_roles: set[str] = set()
    normalized_sections: list[dict[str, Any]] = []

    for section_index, section in enumerate(sections_payload):
        if not isinstance(section, dict):
            raise ValueError(f"{path.name} sections[{section_index}] must be an object")
        section_id = _require_non_empty_string(
            section.get("section_id"),
            label=f"{path.name} sections[{section_index}].section_id",
        )
        panel_label = _require_non_empty_string(
            section.get("panel_label"),
            label=f"{path.name} sections[{section_index}].panel_label",
        )
        section_title = _require_non_empty_string(
            section.get("title"),
            label=f"{path.name} sections[{section_index}].title",
        )
        layout_role = _require_non_empty_string(
            section.get("layout_role"),
            label=f"{path.name} sections[{section_index}].layout_role",
        )
        if layout_role not in expected_layout_roles:
            raise ValueError(
                f"{path.name} sections[{section_index}].layout_role must be one of {sorted(expected_layout_roles)}"
            )
        if section_id in seen_section_ids:
            raise ValueError(f"{path.name} sections[{section_index}].section_id must be unique")
        if panel_label in seen_panel_labels:
            raise ValueError(f"{path.name} sections[{section_index}].panel_label must be unique")
        if layout_role in seen_layout_roles:
            raise ValueError(f"{path.name} sections[{section_index}].layout_role must be unique")
        seen_section_ids.add(section_id)
        seen_panel_labels.add(panel_label)
        seen_layout_roles.add(layout_role)

        facts_payload = section.get("facts")
        if not isinstance(facts_payload, list) or not facts_payload:
            raise ValueError(f"{path.name} sections[{section_index}].facts must be a non-empty list")
        normalized_facts: list[dict[str, Any]] = []
        seen_fact_ids: set[str] = set()
        for fact_index, fact in enumerate(facts_payload):
            if not isinstance(fact, dict):
                raise ValueError(f"{path.name} sections[{section_index}].facts[{fact_index}] must be an object")
            fact_id = _require_non_empty_string(
                fact.get("fact_id"),
                label=f"{path.name} sections[{section_index}].facts[{fact_index}].fact_id",
            )
            if fact_id in seen_fact_ids:
                raise ValueError(
                    f"{path.name} sections[{section_index}].facts[{fact_index}].fact_id must be unique within the section"
                )
            seen_fact_ids.add(fact_id)
            normalized_facts.append(
                {
                    "fact_id": fact_id,
                    "label": _require_non_empty_string(
                        fact.get("label"),
                        label=f"{path.name} sections[{section_index}].facts[{fact_index}].label",
                    ),
                    "value": _require_non_empty_string(
                        fact.get("value"),
                        label=f"{path.name} sections[{section_index}].facts[{fact_index}].value",
                    ),
                    "detail": str(fact.get("detail") or "").strip(),
                }
            )

        normalized_sections.append(
            {
                "section_id": section_id,
                "panel_label": panel_label,
                "title": section_title,
                "layout_role": layout_role,
                "facts": normalized_facts,
            }
        )

    if seen_layout_roles != expected_layout_roles:
        raise ValueError(f"{path.name} sections must cover the full four-panel fact-sheet grid")

    return {
        "shell_id": shell_id,
        "display_id": display_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "sections": normalized_sections,
    }


