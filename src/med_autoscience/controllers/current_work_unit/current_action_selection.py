from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers.current_work_unit.primitives import (
    mapping,
    text,
    text_items,
)
from med_autoscience.controllers.current_work_unit.policy_constants import (
    PROVIDER_ADMISSION_AUTHORITIES,
)
from med_autoscience.controllers.stage_route_currentness_identity import (
    currentness_identities_match,
)

ALLOWED_CURRENT_OWNER_ACTION_SOURCES = frozenset(
    {
        "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "paper_recovery_state.accepted_owner_gate_decision",
        "paper_recovery_state.next_safe_action.owner_callable",
        "paper_recovery_state.next_safe_action.successor_owner_action",
        "publication_eval.recommended_actions.readiness_blocker_repair",
        "repair_progress_projection.mas_owner_repair_execution_evidence",
        "stage_kernel_projection.current_owner_delta",
        "study_progress.next_forced_delta.owner_action",
    }
)


def selected_current_action(
    *,
    actions: Sequence[Mapping[str, Any]] | None,
    current_executable_owner_action: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    current_action = action_from_current_action(current_executable_owner_action)
    queued_action = allowed_action(actions)
    if current_action is None:
        return queued_action
    if queued_action is None:
        return current_action
    if currentness_identities_match(current_action, queued_action):
        return {**queued_action, **current_action}
    return current_action


def action_from_current_action(
    current_executable_owner_action: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    current = mapping(current_executable_owner_action)
    if text(current.get("surface_kind")) != "current_executable_owner_action":
        return None
    allowed_actions = text_items(current.get("allowed_actions"))
    action_type = text(current.get("action_type")) or (allowed_actions[0] if allowed_actions else None)
    owner = text(current.get("next_owner")) or text(current.get("owner"))
    current_work_unit_id = text(current.get("work_unit_id"))
    if action_type is None and owner is None and current_work_unit_id is None:
        return None
    source = text(current.get("source_surface")) or text(current.get("source"))
    authority = text(current.get("authority"))
    if source not in ALLOWED_CURRENT_OWNER_ACTION_SOURCES and authority not in PROVIDER_ADMISSION_AUTHORITIES:
        return None
    return {
        **current,
        "action_type": action_type,
        "owner": owner,
        "recommended_owner": text(current.get("recommended_owner")) or owner,
        "next_owner": owner,
        "next_work_unit": current_work_unit_id or action_type,
        "work_unit_id": current_work_unit_id,
        "source_surface": source,
    }


def provider_admission_action(actions: Sequence[Mapping[str, Any]] | None) -> dict[str, Any] | None:
    return allowed_action(actions)


def allowed_action(actions: Sequence[Mapping[str, Any]] | None) -> dict[str, Any] | None:
    for item in actions or []:
        action = mapping(item)
        source = text(action.get("source_surface")) or text(action.get("source"))
        authority = text(action.get("authority"))
        if source in ALLOWED_CURRENT_OWNER_ACTION_SOURCES or authority in PROVIDER_ADMISSION_AUTHORITIES:
            return dict(action)
    return None


__all__ = [
    "ALLOWED_CURRENT_OWNER_ACTION_SOURCES",
    "allowed_action",
    "action_from_current_action",
    "provider_admission_action",
    "selected_current_action",
]
