from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .primitives import _mapping, _sequence, _text


def stage_kernel_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "stage_kernel_projection.current_owner_delta"
        and bool(_sequence(action.get("allowed_actions")))
    )


def stage_native_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "stage_native_workspace_next_action"
        and bool(_sequence(action.get("allowed_actions")))
    )


def repair_progress_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "repair_progress_projection.mas_owner_repair_execution_evidence"
        and bool(_sequence(action.get("allowed_actions")))
    )


def repair_progress_consumes_publication_repair(
    *,
    repair_progress_current_action: Mapping[str, Any],
    publication_eval_current_action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if not repair_progress_owner_action(repair_progress_current_action):
        return False
    if not publication_eval_readiness_blocker_repair_action(publication_eval_current_action):
        return False
    progress = _mapping(payload.get("repair_progress_projection"))
    if progress.get("paper_delta_observed") is not True or progress.get("accepted_owner_receipt") is not True:
        return False
    precedence = _mapping(repair_progress_current_action.get("repair_progress_precedence"))
    source_work_unit = _text(precedence.get("source_work_unit_id")) or _text(progress.get("work_unit_id"))
    if source_work_unit is None:
        return False
    return source_work_unit == _text(publication_eval_current_action.get("work_unit_id"))


def repair_progress_consumes_canonical_publication_work_unit(
    *,
    current_action: Mapping[str, Any],
    canonical_current_work_unit: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if not repair_progress_owner_action(current_action):
        return False
    if _text(canonical_current_work_unit.get("status")) != "executable_owner_action":
        return False
    state = _mapping(canonical_current_work_unit.get("state"))
    if _text(state.get("source")) != "publication_eval.recommended_actions.readiness_blocker_repair":
        return False
    progress = _mapping(payload.get("repair_progress_projection"))
    if progress.get("paper_delta_observed") is not True or progress.get("accepted_owner_receipt") is not True:
        return False
    precedence = _mapping(current_action.get("repair_progress_precedence"))
    source_work_unit = _text(precedence.get("source_work_unit_id")) or _text(progress.get("work_unit_id"))
    if source_work_unit is None:
        return False
    return source_work_unit == _text(canonical_current_work_unit.get("work_unit_id"))


def gate_followthrough_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "gate_clearing_batch_followthrough.actionable_current_work_unit"
        and bool(_sequence(action.get("allowed_actions")))
    )


def publication_eval_readiness_blocker_repair_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "publication_eval.recommended_actions.readiness_blocker_repair"
        and bool(_sequence(action.get("allowed_actions")))
    )


def next_forced_delta_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "study_progress.next_forced_delta.owner_action"
        and bool(_sequence(action.get("allowed_actions")))
    )


def canonical_ready_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("surface_kind")) == "current_executable_owner_action"
        and _text(action.get("status")) == "ready"
        and bool(_sequence(action.get("allowed_actions")))
    )


def envelope_typed_blocker_blocks_current_action(
    *,
    execution: Mapping[str, Any],
    raw_typed_blocker: Mapping[str, Any],
    artifact_first_supersedes_blocker: bool,
    current_action: Mapping[str, Any],
) -> bool:
    if artifact_first_supersedes_blocker:
        return False
    if stage_native_owner_action(current_action):
        return False
    if repair_progress_owner_action(current_action):
        return False
    if gate_followthrough_owner_action(current_action):
        return False
    if publication_eval_readiness_blocker_repair_action(current_action):
        return False
    if next_forced_delta_owner_action(current_action):
        return _text(execution.get("state_kind")) == "typed_blocker" and bool(raw_typed_blocker)
    if _text(execution.get("state_kind")) != "typed_blocker":
        return False
    return bool(raw_typed_blocker)


__all__ = [
    "canonical_ready_owner_action",
    "envelope_typed_blocker_blocks_current_action",
    "gate_followthrough_owner_action",
    "next_forced_delta_owner_action",
    "publication_eval_readiness_blocker_repair_action",
    "repair_progress_consumes_canonical_publication_work_unit",
    "repair_progress_consumes_publication_repair",
    "repair_progress_owner_action",
    "stage_kernel_owner_action",
    "stage_native_owner_action",
]
