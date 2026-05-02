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


def _validate_design_evidence_composite_shell_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    expected_shell_id = display_registry.get_illustration_shell_spec("design_evidence_composite_shell").shell_id
    shell_id = _require_non_empty_string(payload.get("shell_id"), label=f"{path.name} shell_id")
    if shell_id != expected_shell_id:
        raise ValueError(f"{path.name} shell_id must be `{expected_shell_id}`")
    display_id = _require_non_empty_string(payload.get("display_id"), label=f"{path.name} display_id")
    title = _require_non_empty_string(payload.get("title"), label=f"{path.name} title")

    workflow_stages_payload = payload.get("workflow_stages")
    if not isinstance(workflow_stages_payload, list) or len(workflow_stages_payload) not in {3, 4}:
        raise ValueError(f"{path.name} must contain three or four workflow_stages items")
    seen_stage_ids: set[str] = set()
    normalized_workflow_stages: list[dict[str, Any]] = []
    for stage_index, stage in enumerate(workflow_stages_payload):
        if not isinstance(stage, dict):
            raise ValueError(f"{path.name} workflow_stages[{stage_index}] must be an object")
        stage_id = _require_non_empty_string(
            stage.get("stage_id"),
            label=f"{path.name} workflow_stages[{stage_index}].stage_id",
        )
        if stage_id in seen_stage_ids:
            raise ValueError(f"{path.name} workflow_stages[{stage_index}].stage_id must be unique")
        seen_stage_ids.add(stage_id)
        normalized_workflow_stages.append(
            {
                "stage_id": stage_id,
                "title": _require_non_empty_string(
                    stage.get("title"),
                    label=f"{path.name} workflow_stages[{stage_index}].title",
                ),
                "detail": str(stage.get("detail") or "").strip(),
            }
        )

    summary_panels_payload = payload.get("summary_panels")
    if not isinstance(summary_panels_payload, list) or len(summary_panels_payload) != 3:
        raise ValueError(f"{path.name} must contain exactly three summary_panels items")
    expected_layout_roles = {"left", "center", "right"}
    seen_panel_ids: set[str] = set()
    seen_panel_labels: set[str] = set()
    seen_layout_roles: set[str] = set()
    normalized_summary_panels: list[dict[str, Any]] = []
    for panel_index, panel in enumerate(summary_panels_payload):
        if not isinstance(panel, dict):
            raise ValueError(f"{path.name} summary_panels[{panel_index}] must be an object")
        panel_id = _require_non_empty_string(
            panel.get("panel_id"),
            label=f"{path.name} summary_panels[{panel_index}].panel_id",
        )
        panel_label = _require_non_empty_string(
            panel.get("panel_label"),
            label=f"{path.name} summary_panels[{panel_index}].panel_label",
        )
        layout_role = _require_non_empty_string(
            panel.get("layout_role"),
            label=f"{path.name} summary_panels[{panel_index}].layout_role",
        ).lower()
        if layout_role not in expected_layout_roles:
            raise ValueError(
                f"{path.name} summary_panels[{panel_index}].layout_role must be one of {sorted(expected_layout_roles)}"
            )
        if panel_id in seen_panel_ids:
            raise ValueError(f"{path.name} summary_panels[{panel_index}].panel_id must be unique")
        if panel_label in seen_panel_labels:
            raise ValueError(f"{path.name} summary_panels[{panel_index}].panel_label must be unique")
        if layout_role in seen_layout_roles:
            raise ValueError(f"{path.name} summary_panels[{panel_index}].layout_role must be unique")
        seen_panel_ids.add(panel_id)
        seen_panel_labels.add(panel_label)
        seen_layout_roles.add(layout_role)

        cards_payload = panel.get("cards")
        if not isinstance(cards_payload, list) or not cards_payload:
            raise ValueError(f"{path.name} summary_panels[{panel_index}].cards must be a non-empty list")
        normalized_cards: list[dict[str, Any]] = []
        seen_card_ids: set[str] = set()
        for card_index, card in enumerate(cards_payload):
            if not isinstance(card, dict):
                raise ValueError(f"{path.name} summary_panels[{panel_index}].cards[{card_index}] must be an object")
            card_id = _require_non_empty_string(
                card.get("card_id"),
                label=f"{path.name} summary_panels[{panel_index}].cards[{card_index}].card_id",
            )
            if card_id in seen_card_ids:
                raise ValueError(
                    f"{path.name} summary_panels[{panel_index}].cards[{card_index}].card_id must be unique within the panel"
                )
            seen_card_ids.add(card_id)
            normalized_cards.append(
                {
                    "card_id": card_id,
                    "label": _require_non_empty_string(
                        card.get("label"),
                        label=f"{path.name} summary_panels[{panel_index}].cards[{card_index}].label",
                    ),
                    "value": _require_non_empty_string(
                        card.get("value"),
                        label=f"{path.name} summary_panels[{panel_index}].cards[{card_index}].value",
                    ),
                    "detail": str(card.get("detail") or "").strip(),
                }
            )

        normalized_summary_panels.append(
            {
                "panel_id": panel_id,
                "panel_label": panel_label,
                "title": _require_non_empty_string(
                    panel.get("title"),
                    label=f"{path.name} summary_panels[{panel_index}].title",
                ),
                "layout_role": layout_role,
                "cards": normalized_cards,
            }
        )

    if seen_layout_roles != expected_layout_roles:
        raise ValueError(f"{path.name} summary_panels must cover the complete three-panel composite layout")

    return {
        "shell_id": shell_id,
        "display_id": display_id,
        "title": title,
        "caption": str(payload.get("caption") or "").strip(),
        "workflow_stages": normalized_workflow_stages,
        "summary_panels": normalized_summary_panels,
    }


