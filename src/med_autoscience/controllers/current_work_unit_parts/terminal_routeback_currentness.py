from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    acceptance_refs as _acceptance_refs,
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
    text_items as _text_items,
)


def terminal_routeback_action_supersedes_gate_replay_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
    gate_replay_work_units: Collection[str],
) -> bool:
    action_source = _text(action.get("source_surface")) or _text(action.get("source"))
    if action_source != "study_progress.next_forced_delta.owner_action":
        return False
    if action.get("terminal_stage_next_forced_delta") is not True:
        return False
    if _text(action.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(action.get("next_owner")) != "write" and _text(action.get("owner")) != "write":
        return False
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    if action_work_unit in {None, "publication_gate_replay", "complete_medical_paper_readiness_surface"}:
        return False
    blocker_work_unit = _work_unit_id(blocker.get("work_unit_id")) or _work_unit_id(
        blocker.get("next_work_unit")
    )
    blocker_type = (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocked_reason"))
    )
    blocker_action_type = _text(blocker.get("action_type"))
    if blocker_action_type != "run_gate_clearing_batch":
        return False
    source_ref = _text(blocker.get("source_ref"))
    if source_ref is None:
        return False
    if not _terminal_gate_closeout_routes_to_action(
        progress=progress,
        action=action,
        source_ref=source_ref,
        gate_replay_work_units=gate_replay_work_units,
    ):
        return False
    if blocker_work_unit in gate_replay_work_units:
        return True
    if blocker_work_unit == action_work_unit and blocker_type in {
        "publication_gate_replay_blocked",
        "medical_publication_surface_blocked",
    }:
        return True
    return blocker_type == "publication_gate_replay_blocked"


def terminal_routeback_action_from_gate_closeout(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
    gate_replay_work_units: Collection[str],
) -> bool:
    action_source = _text(action.get("source_surface")) or _text(action.get("source"))
    if action_source != "study_progress.next_forced_delta.owner_action":
        return False
    if action.get("terminal_stage_next_forced_delta") is not True:
        return False
    if _text(action.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(action.get("next_owner")) != "write" and _text(action.get("owner")) != "write":
        return False
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    if action_work_unit in {None, "publication_gate_replay", "complete_medical_paper_readiness_surface"}:
        return False
    for ref in _acceptance_refs(action):
        if _terminal_gate_closeout_routes_to_action(
            progress=progress,
            action=action,
            source_ref=ref,
            gate_replay_work_units=gate_replay_work_units,
        ):
            return True
    return False


def gate_followthrough_action_supersedes_publication_gate_replay_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    blocker_type = (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocked_reason"))
        or _text(blocker.get("reason"))
    )
    if blocker_type != "publication_gate_replay_blocked" or not gate_followthrough_actionable_repair_action(action):
        return False
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    currentness = _mapping(followthrough.get("work_unit_currentness"))
    if (
        not followthrough
        or _text(followthrough.get("gate_replay_status")) != "blocked"
        or _text(currentness.get("current_actionability_status")) != "actionable"
        or currentness.get("lacks_specific_blocker_object") is True
    ):
        return False
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    followthrough_work_unit = _work_unit_id(currentness.get("current_publication_work_unit_id")) or _work_unit_id(
        _mapping(followthrough.get("current_publication_work_unit")).get("unit_id")
    )
    if action_work_unit is None or followthrough_work_unit != action_work_unit:
        return False
    action_fingerprint = (
        _text(action.get("work_unit_fingerprint"))
        or _text(action.get("action_fingerprint"))
        or _text(_mapping(action.get("owner_route_currentness_basis")).get("work_unit_fingerprint"))
    )
    followthrough_fingerprint = _text(currentness.get("current_work_unit_fingerprint"))
    if action_fingerprint is not None and followthrough_fingerprint is not None and action_fingerprint != followthrough_fingerprint:
        return False
    action_source_eval = _text(action.get("source_eval_id")) or _text(
        _mapping(action.get("owner_route_currentness_basis")).get("source_eval_id")
    )
    followthrough_source_eval = _text(followthrough.get("source_eval_id"))
    return not (
        action_source_eval is not None
        and followthrough_source_eval is not None
        and action_source_eval != followthrough_source_eval
    )


def _terminal_gate_closeout_routes_to_action(
    *,
    progress: Mapping[str, Any],
    action: Mapping[str, Any],
    source_ref: str,
    gate_replay_work_units: Collection[str],
) -> bool:
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    if action_work_unit is None:
        return False
    action_refs = set(_acceptance_refs(action))
    for terminal in _terminal_stage_candidates(progress):
        if _text(terminal.get("action_type")) != "run_gate_clearing_batch":
            continue
        paper_stage_log = _mapping(terminal.get("paper_stage_log"))
        next_delta = _mapping(terminal.get("next_forced_delta")) or _mapping(
            paper_stage_log.get("next_forced_delta")
        )
        terminal_work_unit = (
            _work_unit_id(terminal.get("work_unit_id"))
            or _work_unit_id(terminal.get("next_work_unit"))
            or _work_unit_id(next_delta.get("work_unit_id"))
        )
        if terminal_work_unit not in gate_replay_work_units:
            continue
        terminal_ref = _text(terminal.get("source_path")) or _text(terminal.get("record_path"))
        terminal_refs = set(_text_items(terminal.get("closeout_refs")))
        if (
            source_ref != terminal_ref
            and source_ref not in terminal_refs
            and terminal_ref not in action_refs
            and not bool(action_refs.intersection(terminal_refs))
        ):
            continue
        owner_action = _mapping(next_delta.get("owner_action"))
        next_owner = _text(owner_action.get("next_owner")) or _text(owner_action.get("owner"))
        raw_action_type = _text(owner_action.get("action_type")) or _text(next_delta.get("action_type"))
        next_work_unit = _work_unit_id(owner_action.get("work_unit_id")) or _work_unit_id(
            next_delta.get("work_unit_id")
        )
        if next_owner != "write":
            continue
        if raw_action_type not in {"return_to_write", "run_quality_repair_batch"}:
            continue
        if next_work_unit != action_work_unit:
            continue
        return True
    return False


def gate_followthrough_actionable_repair_action(action: Mapping[str, Any]) -> bool:
    if (_text(action.get("source_surface")) or _text(action.get("source"))) != (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    ):
        return False
    work_unit = _work_unit_id(action.get("work_unit_id"))
    if work_unit in {None, "complete_medical_paper_readiness_surface"}:
        return False
    target = _mapping(action.get("target_surface"))
    if _text(target.get("target_surface_specificity")) == "stage_kernel_typed_blocker_followup":
        return False
    return _text(target.get("ref_kind")) == "publication_work_unit"


def _terminal_stage_candidates(progress: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    progress_first = _mapping(progress.get("progress_first_monitoring_summary"))
    handoff = _mapping(progress.get("opl_current_control_state_handoff"))
    candidates: list[dict[str, Any]] = []
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        progress.get("latest_terminal_stage"),
        progress.get("latest_terminal_stage_log"),
    ):
        terminal = _mapping(value)
        if terminal:
            candidates.append(terminal)
    return tuple(candidates)


__all__ = [
    "gate_followthrough_actionable_repair_action",
    "gate_followthrough_action_supersedes_publication_gate_replay_blocker",
    "terminal_routeback_action_from_gate_closeout",
    "terminal_routeback_action_supersedes_gate_replay_blocker",
]
