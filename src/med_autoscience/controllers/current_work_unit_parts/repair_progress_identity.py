from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    action_type,
    work_unit_fingerprint,
    work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import mapping, text, text_items


def repair_progress_matches_action(
    *,
    repair: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    current_action_type = action_type(action)
    if current_action_type is not None and current_action_type != "run_quality_repair_batch":
        return False
    repair_work_unit = work_unit_id(repair.get("work_unit_id"))
    action_work_unit = work_unit_id(action.get("work_unit_id")) or work_unit_id(
        action.get("next_work_unit")
    )
    if repair_work_unit is None or action_work_unit is None or repair_work_unit != action_work_unit:
        return False
    action_fingerprint = work_unit_fingerprint(
        action,
        currentness_basis=mapping(action.get("owner_route_currentness_basis"))
        or mapping(action.get("currentness_basis")),
    )
    repair_fingerprint = (
        text(repair.get("work_unit_fingerprint"))
        or text(repair.get("action_fingerprint"))
        or text(repair.get("source_fingerprint"))
    )
    if action_fingerprint is None or repair_fingerprint != action_fingerprint:
        return False
    action_eval = text(action.get("source_eval_id"))
    repair_eval = text(repair.get("source_eval_id"))
    if action_eval is not None and repair_eval is not None and action_eval != repair_eval:
        return False
    return True


def repair_progress_gate_replay_receipt_ref(repair: Mapping[str, Any]) -> str | None:
    for ref in text_items(repair.get("gate_replay_refs")):
        if "gate_clearing_batch" in ref:
            return ref
    return None


def progress_has_gate_followthrough_actionable_repair(progress: Mapping[str, Any]) -> bool:
    followthrough = mapping(progress.get("gate_clearing_batch_followthrough"))
    if text(followthrough.get("status")) != "executed":
        return False
    work_unit_currentness = mapping(followthrough.get("work_unit_currentness"))
    if text(work_unit_currentness.get("current_actionability_status")) != "actionable":
        return False
    publication_work_unit = mapping(followthrough.get("current_publication_work_unit"))
    unit_id = work_unit_id(publication_work_unit.get("unit_id")) or work_unit_id(
        followthrough.get("work_unit_id")
    )
    if unit_id in {None, "publication_gate_replay", "complete_medical_paper_readiness_surface"}:
        return False
    return True


__all__ = [
    "progress_has_gate_followthrough_actionable_repair",
    "repair_progress_gate_replay_receipt_ref",
    "repair_progress_matches_action",
]
