from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer_parts import (
    repair_progress_currentness,
)


def current_typed_blocker_barrier_for_consumed_transition(
    *,
    study: Mapping[str, Any],
    fresh_action: Mapping[str, Any] | None,
    transition_actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    return current_typed_blocker_barrier_for_actions(
        study=study,
        fresh_action=fresh_action,
        candidate_actions=transition_actions,
    )


def current_typed_blocker_barrier_for_actions(
    *,
    study: Mapping[str, Any],
    fresh_action: Mapping[str, Any] | None,
    candidate_actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not candidate_actions:
        return None
    if fresh_action is not None and (
        _text(fresh_action.get("action_type")) or ""
    ).startswith("current_execution_envelope_"):
        return dict(fresh_action)
    current_action = _mapping(study.get("current_executable_owner_action"))
    envelope = _mapping(study.get("current_execution_envelope"))
    if repair_progress_currentness.typed_blocker_allows_repair_progress_followup(
        envelope=envelope,
        current_action=current_action,
    ):
        return None
    current_work_unit = _mapping(study.get("current_work_unit"))
    work_unit_state = _mapping(current_work_unit.get("state"))
    stale_override = work_unit_state.get("stale_queue_or_handoff_can_override")
    if stale_override is True or _text(stale_override) == "true":
        return None
    work_unit_status = _text(current_work_unit.get("status"))
    state_kind = _text(work_unit_state.get("state_kind"))
    envelope_state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if not (
        work_unit_status == "typed_blocker"
        or state_kind == "typed_blocker"
        or envelope_state_kind == "typed_blocker"
    ):
        return None
    blocker = (
        _mapping(work_unit_state.get("typed_blocker"))
        or _mapping(envelope.get("typed_blocker"))
        or current_work_unit
    )
    reason = (
        _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("reason"))
        or "typed_blocker"
    )
    owner = (
        _text(envelope.get("owner"))
        or _text(current_work_unit.get("owner"))
        or _text(blocker.get("owner"))
        or "MedAutoScience"
    )
    study_id = _text(study.get("study_id"))
    return {
        "study_id": study_id,
        "quest_id": _text(study.get("quest_id")),
        "action_type": "current_execution_envelope_typed_blocker",
        "action_id": f"study-progress-current-execution-envelope::{study_id}::typed_blocker",
        "reason": reason,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": "current_work_unit.typed_blocker",
        "source_surface": "current_work_unit",
        "source_ref": _text(blocker.get("source_ref")),
        "work_unit_id": _text(blocker.get("work_unit_id")) or _text(current_work_unit.get("work_unit_id")),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "current_typed_blocker_barrier_for_actions",
    "current_typed_blocker_barrier_for_consumed_transition",
]
