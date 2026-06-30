from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.paper_recovery_successor import (
    paper_recovery_successor_supersedes_publication_gate_replay_blocker,
    paper_recovery_successor_supersedes_terminal_selector_residue,
)
from med_autoscience.controllers.current_work_unit_parts.terminal_routeback_currentness import (
    gate_followthrough_action_supersedes_transport_or_execution_residue,
)


AI_REVIEWER_STALE_BLOCKERS = frozenset(
    {
        "ai_reviewer_record_stale_after_current_inputs",
        "ai_reviewer_record_stale_after_current_manuscript",
        "ai_reviewer_record_stale_after_unit_harmonized_rerun",
    }
)
AI_REVIEWER_GATE_REPLAY_SOURCE = "publication_eval.recommended_actions.readiness_blocker_repair"
AI_REVIEWER_GATE_REPLAY_DELTA_KIND = "publication_eval_gate_replay_delta_or_typed_blocker"


def current_action_supersedes_typed_blocker(
    *,
    action: Mapping[str, Any] | None,
    blocker: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
) -> bool:
    action_payload = _mapping(action)
    blocker_payload = _mapping(blocker)
    if not blocker_payload:
        return True
    if not action_payload:
        return False
    if paper_recovery_successor_supersedes_terminal_selector_residue(
        action=action_payload,
        blocker=blocker_payload,
        progress=progress,
    ):
        return True
    if paper_recovery_successor_supersedes_publication_gate_replay_blocker(
        action=action_payload,
        blocker=blocker_payload,
    ):
        return True
    if gate_followthrough_action_supersedes_transport_or_execution_residue(
        action=action_payload,
        blocker=blocker_payload,
        progress=progress,
    ):
        return True
    return _ai_reviewer_gate_replay_action_supersedes_stale_blocker(
        action=action_payload,
        blocker=blocker_payload,
    )


def _ai_reviewer_gate_replay_action_supersedes_stale_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
) -> bool:
    if _blocker_reason(blocker) not in AI_REVIEWER_STALE_BLOCKERS:
        return False
    source = _text(action.get("source")) or _text(action.get("source_surface"))
    if source != AI_REVIEWER_GATE_REPLAY_SOURCE:
        return False
    if _text(action.get("action_type")) != "run_gate_clearing_batch":
        return False
    if action.get("owner_receipt_required") is not True:
        return False
    if _text(action.get("required_delta_kind")) != AI_REVIEWER_GATE_REPLAY_DELTA_KIND:
        return False
    return _same_currentness_identity(action, blocker)


def _same_currentness_identity(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_fingerprint = _fingerprint(left)
    right_fingerprint = _fingerprint(right)
    if left_fingerprint is not None and right_fingerprint is not None:
        return left_fingerprint == right_fingerprint
    left_work_unit = _text(left.get("work_unit_id")) or _text(left.get("next_work_unit"))
    right_work_unit = _text(right.get("work_unit_id")) or _text(right.get("next_work_unit"))
    return left_work_unit is not None and left_work_unit == right_work_unit


def _fingerprint(payload: Mapping[str, Any]) -> str | None:
    basis = _mapping(payload.get("owner_route_currentness_basis")) or _mapping(
        payload.get("currentness_basis")
    )
    return (
        _text(payload.get("work_unit_fingerprint"))
        or _text(payload.get("action_fingerprint"))
        or _text(payload.get("fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )


def _blocker_reason(blocker: Mapping[str, Any]) -> str | None:
    return (
        _text(blocker.get("blocked_reason"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocker_kind"))
        or _text(blocker.get("reason"))
        or _text(blocker.get("blocker_id"))
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


__all__ = ["current_action_supersedes_typed_blocker"]
