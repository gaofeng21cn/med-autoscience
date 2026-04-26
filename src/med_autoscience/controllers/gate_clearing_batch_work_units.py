from __future__ import annotations

from importlib import import_module
from typing import Any


PUBLICATION_WORK_UNIT_REPAIR_IDS = {
    "analysis_claim_evidence_repair": frozenset(
        {
            "freeze_scientific_anchor_fields",
            "repair_paper_live_paths",
            "workspace_display_repair_script",
            "materialize_display_surface",
        }
    ),
    "manuscript_story_repair": frozenset(
        {
            "repair_paper_live_paths",
            "workspace_display_repair_script",
            "materialize_display_surface",
        }
    ),
    "figure_results_trace_repair": frozenset(
        {
            "repair_paper_live_paths",
            "workspace_display_repair_script",
            "materialize_display_surface",
        }
    ),
    "treatment_gap_reporting_repair": frozenset(
        {
            "repair_paper_live_paths",
            "workspace_display_repair_script",
            "materialize_display_surface",
        }
    ),
    "submission_minimal_refresh": frozenset(
        {
            "create_submission_minimal_package",
            "sync_submission_minimal_delivery",
        }
    ),
    "display_reporting_contract_repair": frozenset(
        {
            "repair_paper_live_paths",
            "workspace_display_repair_script",
            "materialize_display_surface",
        }
    ),
    "local_architecture_overview_repair": frozenset(
        {
            "workspace_display_repair_script",
            "materialize_display_surface",
        }
    ),
}


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _compact_work_unit_payload(value: object) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    unit_id = _non_empty_text(value.get("unit_id"))
    if unit_id is None:
        return None
    payload = {"unit_id": unit_id}
    lane = _non_empty_text(value.get("lane"))
    summary = _non_empty_text(value.get("summary"))
    if lane is not None:
        payload["lane"] = lane
    if summary is not None:
        payload["summary"] = summary
    return payload


def explicit_next_publication_work_unit(publication_eval_payload: dict[str, Any]) -> dict[str, str] | None:
    recommended_actions = publication_eval_payload.get("recommended_actions") or []
    if not isinstance(recommended_actions, list):
        return None
    for action in recommended_actions:
        if not isinstance(action, dict):
            continue
        payload = _compact_work_unit_payload(action.get("next_work_unit"))
        if payload is not None:
            return payload
    return None


def derived_next_publication_work_unit(gate_report: dict[str, Any]) -> dict[str, str] | None:
    publication_work_units = import_module("med_autoscience.controllers.publication_work_units")
    payload = publication_work_units.derive_publication_work_units(gate_report)
    return _compact_work_unit_payload(payload.get("next_work_unit"))


def filter_repair_units_for_publication_work_unit(
    repair_units: list[Any],
    *,
    next_work_unit: dict[str, str] | None,
) -> list[Any]:
    if next_work_unit is None:
        return repair_units
    unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    if unit_id is None:
        return repair_units
    allowed_unit_ids = PUBLICATION_WORK_UNIT_REPAIR_IDS.get(unit_id)
    if allowed_unit_ids is None:
        return repair_units
    units_by_id = {unit.unit_id: unit for unit in repair_units}
    selected_unit_ids = set(allowed_unit_ids)
    pending_unit_ids = list(allowed_unit_ids)
    while pending_unit_ids:
        selected_unit_id = pending_unit_ids.pop()
        unit = units_by_id.get(selected_unit_id)
        if unit is None:
            continue
        for dependency_id in getattr(unit, "depends_on", ()):
            if dependency_id in selected_unit_ids:
                continue
            selected_unit_ids.add(dependency_id)
            pending_unit_ids.append(dependency_id)
    return [unit for unit in repair_units if unit.unit_id in selected_unit_ids]
