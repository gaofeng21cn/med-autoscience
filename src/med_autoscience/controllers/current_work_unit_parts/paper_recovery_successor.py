from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    work_unit_fingerprint,
    work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import mapping, text


PAPER_RECOVERY_SUCCESSOR_SOURCE = "paper_recovery_state.next_safe_action.successor_owner_action"
PAPER_RECOVERY_SUCCESSOR_DELTA_KIND = "paper_recovery_successor_owner_delta_or_typed_blocker"
GATE_FOLLOWTHROUGH_SUCCESSOR_SOURCE = "gate_clearing_batch_followthrough.actionable_current_work_unit"
GATE_FOLLOWTHROUGH_SUCCESSOR_DELTA_KIND = "publication_gate_actionable_repair_delta_or_typed_blocker"
TERMINAL_SELECTOR_RESIDUE_BLOCKERS = frozenset(
    {
        "no_selected_dispatch_for_authorized_stage_packet",
    }
)


SUPERSEDED_RECOVERY_SUCCESSOR_BLOCKERS = frozenset(
    {
        "blocked:unsupported_dispatch_surface",
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "opl_execution_authorization_required",
        "publication_gate_replay_blocked",
    }
)
SUPERSEDED_RECOVERY_SUCCESSOR_TERMINAL_OUTCOMES = frozenset(
    {
        "blocked:unsupported_dispatch_surface",
    }
)


def paper_recovery_successor_supersedes_publication_gate_replay_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
) -> bool:
    blocker_type = (
        text(blocker.get("blocker_type"))
        or text(blocker.get("blocker_id"))
        or text(blocker.get("blocked_reason"))
        or text(blocker.get("reason"))
    )
    if blocker_type not in SUPERSEDED_RECOVERY_SUCCESSOR_BLOCKERS:
        terminal_outcome = text(blocker.get("terminal_closeout_outcome"))
        if terminal_outcome not in SUPERSEDED_RECOVERY_SUCCESSOR_TERMINAL_OUTCOMES:
            return False
    if not paper_recovery_successor_action_ready(action):
        return False
    return True


def paper_recovery_successor_supersedes_terminal_selector_residue(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    if not paper_recovery_successor_action_ready(action):
        return False
    return _action_with_gate_followthrough_currentness_supersedes_terminal_selector_residue(
        action=action,
        blocker=blocker,
        progress=progress,
    )


def action_supersedes_terminal_selector_residue(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    if not (
        paper_recovery_successor_action_ready(action)
        or gate_followthrough_successor_action_ready(action)
    ):
        return False
    return _action_with_gate_followthrough_currentness_supersedes_terminal_selector_residue(
        action=action,
        blocker=blocker,
        progress=progress,
    )


def _action_with_gate_followthrough_currentness_supersedes_terminal_selector_residue(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    if _blocker_reason(blocker) not in TERMINAL_SELECTOR_RESIDUE_BLOCKERS:
        return False
    if not _same_work_unit_identity(blocker, action):
        return False
    if not _gate_followthrough_successor_current(action=action, progress=progress):
        return False
    return True


def paper_recovery_successor_action_ready(action: Mapping[str, Any]) -> bool:
    if text(action.get("source")) != PAPER_RECOVERY_SUCCESSOR_SOURCE:
        return False
    if action.get("owner_receipt_required") is not True:
        return False
    if text(action.get("required_delta_kind")) != PAPER_RECOVERY_SUCCESSOR_DELTA_KIND:
        return False
    successor = mapping(action.get("paper_recovery_successor"))
    if (
        successor
        and text(successor.get("source_next_safe_action_kind"))
        not in {None, "materialize_successor_owner_action"}
    ):
        return False
    currentness_basis = mapping(action.get("owner_route_currentness_basis"))
    return (
        text(action.get("action_type")) is not None
        and work_unit_id(action.get("work_unit_id")) is not None
        and work_unit_fingerprint(action, currentness_basis=currentness_basis) is not None
    )


def gate_followthrough_successor_action_ready(action: Mapping[str, Any]) -> bool:
    if text(action.get("source")) != GATE_FOLLOWTHROUGH_SUCCESSOR_SOURCE:
        return False
    if action.get("owner_receipt_required") is not True:
        return False
    if text(action.get("required_delta_kind")) != GATE_FOLLOWTHROUGH_SUCCESSOR_DELTA_KIND:
        return False
    currentness_basis = mapping(action.get("owner_route_currentness_basis")) or mapping(
        action.get("currentness_basis")
    )
    return (
        text(action.get("action_type")) == "run_quality_repair_batch"
        and work_unit_id(action.get("work_unit_id")) is not None
        and work_unit_fingerprint(action, currentness_basis=currentness_basis) is not None
    )


def _blocker_reason(blocker: Mapping[str, Any]) -> str | None:
    return (
        text(blocker.get("blocker_type"))
        or text(blocker.get("blocker_id"))
        or text(blocker.get("blocked_reason"))
        or text(blocker.get("reason"))
    )


def _same_work_unit_identity(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_work_unit = work_unit_id(left.get("work_unit_id")) or work_unit_id(left.get("next_work_unit"))
    right_work_unit = work_unit_id(right.get("work_unit_id")) or work_unit_id(right.get("next_work_unit"))
    if left_work_unit is not None and right_work_unit is not None and left_work_unit != right_work_unit:
        return False
    left_fingerprint = text(left.get("work_unit_fingerprint")) or text(left.get("action_fingerprint"))
    right_basis = mapping(right.get("owner_route_currentness_basis")) or mapping(
        right.get("currentness_basis")
    )
    right_fingerprint = (
        text(right.get("work_unit_fingerprint"))
        or text(right.get("action_fingerprint"))
        or text(right.get("fingerprint"))
        or text(right_basis.get("work_unit_fingerprint"))
        or text(right_basis.get("source_fingerprint"))
    )
    if left_fingerprint is not None and right_fingerprint is not None:
        return left_fingerprint == right_fingerprint
    return left_work_unit is not None and left_work_unit == right_work_unit


def _gate_followthrough_successor_current(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    source = (
        text(action.get("source_surface"))
        or text(action.get("source"))
        or text(mapping(action.get("paper_recovery_successor")).get("source_surface"))
    )
    if source != GATE_FOLLOWTHROUGH_SUCCESSOR_SOURCE:
        return False
    followthrough = mapping(progress.get("gate_clearing_batch_followthrough"))
    currentness = mapping(followthrough.get("work_unit_currentness"))
    if (
        not followthrough
        or text(followthrough.get("gate_replay_status")) != "blocked"
        or text(currentness.get("current_actionability_status")) != "actionable"
        or currentness.get("lacks_specific_blocker_object") is True
    ):
        return False
    action_work_unit = work_unit_id(action.get("work_unit_id")) or work_unit_id(
        action.get("next_work_unit")
    )
    followthrough_work_unit = (
        work_unit_id(followthrough.get("work_unit_id"))
        or work_unit_id(currentness.get("current_publication_work_unit_id"))
        or work_unit_id(mapping(followthrough.get("current_publication_work_unit")).get("unit_id"))
    )
    if action_work_unit is None or followthrough_work_unit != action_work_unit:
        return False
    action_basis = mapping(action.get("owner_route_currentness_basis")) or mapping(
        action.get("currentness_basis")
    )
    action_fingerprint = (
        text(action.get("work_unit_fingerprint"))
        or text(action.get("action_fingerprint"))
        or text(action_basis.get("work_unit_fingerprint"))
        or text(action_basis.get("source_fingerprint"))
    )
    followthrough_fingerprint = (
        text(followthrough.get("work_unit_fingerprint"))
        or text(currentness.get("current_work_unit_fingerprint"))
        or text(currentness.get("explicit_work_unit_fingerprint"))
    )
    return not (
        action_fingerprint is not None
        and followthrough_fingerprint is not None
        and action_fingerprint != followthrough_fingerprint
    )


__all__ = [
    "action_supersedes_terminal_selector_residue",
    "gate_followthrough_successor_action_ready",
    "paper_recovery_successor_action_ready",
    "paper_recovery_successor_supersedes_terminal_selector_residue",
    "paper_recovery_successor_supersedes_publication_gate_replay_blocker",
]
