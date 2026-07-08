from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer import (
    fresh_progress_arbitration,
    publication_owner_materialization,
    repair_progress_currentness,
)
from med_autoscience.controllers.opl_execution_boundary import (
    OPL_EXECUTION_AUTHORIZATION_BLOCKER,
)
from med_autoscience.profiles import WorkspaceProfile


def fresh_progress_is_repair_progress_followup(
    action: Mapping[str, Any] | None,
) -> bool:
    return action is not None and (
        repair_progress_currentness.generated_action_is_repair_progress_followup(action)
    )


def fresh_progress_is_accepted_owner_gate_decision(
    action: Mapping[str, Any] | None,
) -> bool:
    if action is None:
        return False
    return (
        _text(action.get("authority"))
        == "paper_recovery_state.accepted_owner_gate_decision"
        or _text(action.get("source_surface"))
        == "paper_recovery_state.accepted_owner_gate_decision"
        or _text(action.get("current_action_source"))
        == "paper_recovery_state.accepted_owner_gate_decision"
    )


def fresh_progress_is_current_owner_action(
    action: Mapping[str, Any] | None,
) -> bool:
    if action is None:
        return False
    if _text(action.get("authority")) == "study_progress.current_owner_ticket_weak_identity":
        return False
    if not _is_current_owner_action_projection(action):
        return False
    if _text(action.get("action_type")) not in fresh_progress_arbitration.SUPPORTED_ACTION_TYPES:
        return False
    return _text(action.get("work_unit_id")) is not None and (
        _text(action.get("work_unit_fingerprint")) is not None
        or _text(action.get("action_fingerprint")) is not None
    )


def _is_current_owner_action_projection(action: Mapping[str, Any]) -> bool:
    return "study_progress.current_executable_owner_action" in {
        _text(action.get("authority")),
        _text(action.get("source_surface")),
        _text(action.get("projection_source_surface")),
    }


def fresh_progress_is_current_execution_envelope_barrier(
    action: Mapping[str, Any] | None,
) -> bool:
    return action is not None and (_text(action.get("action_type")) or "").startswith(
        "current_execution_envelope_"
    )


def fresh_progress_is_hard_current_execution_envelope_barrier(
    action: Mapping[str, Any] | None,
) -> bool:
    return fresh_progress_is_current_execution_envelope_barrier(action) and _text(
        action.get("reason")
    ) == OPL_EXECUTION_AUTHORIZATION_BLOCKER


def fresh_progress_is_terminal_current_execution_envelope_barrier(
    action: Mapping[str, Any] | None,
) -> bool:
    return fresh_progress_is_current_execution_envelope_barrier(action) and _text(
        action.get("reason")
    ) == "current_owner_receipt_recorded"


def fresh_progress_materializes_publication_routeback(
    *,
    profile: WorkspaceProfile | None,
    fresh_action: Mapping[str, Any] | None,
) -> bool:
    if profile is None or fresh_action is None:
        return False
    if not fresh_progress_is_current_execution_envelope_barrier(fresh_action):
        return False
    materialized = publication_owner_materialization.materialization_action(
        profile=profile,
        action=fresh_action,
    )
    if materialized is None:
        return False
    return (
        _text(materialized.get("action_type")) == "run_quality_repair_batch"
        and _text(materialized.get("owner")) == "write"
        and _text(materialized.get("next_work_unit"))
        == "medical_prose_write_repair"
    )


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "fresh_progress_is_accepted_owner_gate_decision",
    "fresh_progress_is_current_execution_envelope_barrier",
    "fresh_progress_is_current_owner_action",
    "fresh_progress_is_hard_current_execution_envelope_barrier",
    "fresh_progress_is_repair_progress_followup",
    "fresh_progress_is_terminal_current_execution_envelope_barrier",
    "fresh_progress_materializes_publication_routeback",
]
