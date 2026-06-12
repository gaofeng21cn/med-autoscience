from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.domain_health_diagnostic_parts.current_ai_reviewer_gate_replay import (
    current_ai_reviewer_gate_replay_fingerprint,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)

from .shared import _mapping_copy, _non_empty_text

SURFACE_KIND = "current_executable_owner_action"
PUBLICATION_HANDOFF_ACTION = "publication_handoff_owner_gate"
READINESS_ACTION = "complete_medical_paper_readiness_surface"
READINESS_BLOCKER = "medical_paper_readiness_not_ready"
READINESS_OWNER = "MedAutoScience"
REPAIR_PROGRESS_SOURCE = "repair_progress_projection.mas_owner_repair_execution_evidence"
AI_REVIEWER_ACTION = "return_to_ai_reviewer_workflow"
AI_REVIEWER_OWNER = "ai_reviewer"
AI_REVIEWER_WORK_UNIT = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
GATE_CLEARING_ACTION = "run_gate_clearing_batch"
GATE_CLEARING_OWNER = "gate_clearing_batch"
GATE_CLEARING_WORK_UNIT = "publication_gate_replay"
QUALITY_REPAIR_ACTION = "run_quality_repair_batch"
TERMINAL_NEXT_FORCED_DELTA_ACTIONS = frozenset(
    {
        GATE_CLEARING_ACTION,
        QUALITY_REPAIR_ACTION,
        "consume_record_only_ai_reviewer_closeout_or_route_next_owner",
    }
)
GATE_CLEARING_FOLLOWTHROUGH_CONSUMED_STATUSES = frozenset(
    {
        "closed",
        "completed",
        "executed",
        "fresh",
        "skipped_duplicate_eval",
        "skipped_stale_gate_replay_closed",
    }
)


def build_current_executable_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if _canonical_current_work_unit_has_terminal_stop_loss(payload):
        return None
    domain_transition_action = _from_domain_transition(payload)
    repair_progress_action = _from_repair_progress_projection(payload)
    if repair_progress_action is not None:
        if not _action_consumed_by_dispatch_receipt(action=repair_progress_action, payload=payload):
            return repair_progress_action
        publication_repair_action = _from_publication_eval_readiness_blocker_repair(payload)
        if publication_repair_action is not None and _consumed_ai_reviewer_followup_routes_to_write_repair(
            payload
        ):
            return publication_repair_action
        gate_followthrough_action = _from_gate_followthrough_current_work_unit(payload)
        next_forced_delta_action = _from_current_next_forced_delta(payload)
        if _next_forced_delta_supersedes_gate_followthrough(
            next_forced_delta_action=next_forced_delta_action,
            gate_followthrough_action=gate_followthrough_action,
        ):
            return next_forced_delta_action
        if gate_followthrough_action is not None:
            return gate_followthrough_action
        if _stage_kernel_readiness_stable_typed_blocker_answer(payload):
            if _next_forced_delta_is_terminal_routeback_action(next_forced_delta_action):
                return next_forced_delta_action
            if publication_repair_action is not None:
                return publication_repair_action
        if next_forced_delta_action is not None:
            return next_forced_delta_action
    gate_followthrough_action = _from_gate_followthrough_current_work_unit(payload)
    next_forced_delta_action = _from_current_next_forced_delta(payload)
    stage_native_action = _from_stage_native_current_owner_action(payload)
    if _next_forced_delta_supersedes_gate_followthrough(
        next_forced_delta_action=next_forced_delta_action,
        gate_followthrough_action=gate_followthrough_action,
    ):
        return next_forced_delta_action
    if _stage_kernel_readiness_stable_typed_blocker_answer(payload):
        publication_repair_action = _from_publication_eval_readiness_blocker_repair(payload)
        if publication_repair_action is not None:
            return publication_repair_action
    if _stage_kernel_owner_answer_recorded_without_next_action(payload):
        if gate_followthrough_action is not None:
            return gate_followthrough_action
        return stage_native_action or domain_transition_action
    if _stage_kernel_readiness_stable_typed_blocker_answer(payload):
        if gate_followthrough_action is not None:
            return gate_followthrough_action
        next_forced_delta_action = _from_current_next_forced_delta(payload)
        if _next_forced_delta_supersedes_stale_readiness_blocker(next_forced_delta_action):
            return next_forced_delta_action
        if _next_forced_delta_is_terminal_routeback_action(next_forced_delta_action):
            return next_forced_delta_action
        publication_repair_action = _from_publication_eval_readiness_blocker_repair(payload)
        if publication_repair_action is not None:
            return publication_repair_action
        return (
            stage_native_action
            or domain_transition_action
            or _from_stage_kernel_readiness_followup(payload)
        )
    readiness_followup = _from_stage_kernel_readiness_followup(payload)
    if readiness_followup is not None:
        return readiness_followup
    if _stage_kernel_readiness_answer_without_followup(payload):
        return stage_native_action or domain_transition_action
    artifact_action = _from_stage_artifact_index(payload)
    if artifact_action is not None and domain_transition_action is None:
        return artifact_action
    if gate_followthrough_action is not None:
        return gate_followthrough_action
    return next_forced_delta_action or domain_transition_action


def _canonical_current_work_unit_has_terminal_stop_loss(payload: Mapping[str, Any]) -> bool:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker":
        return False
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(
        current_work_unit.get("typed_blocker")
    )
    closeout_like = {
        "typed_blocker": typed_blocker,
        "blocked_reason": _non_empty_text(state.get("blocker_type"))
        or _non_empty_text(typed_blocker.get("blocked_reason"))
        or _non_empty_text(typed_blocker.get("blocker_type"))
        or _non_empty_text(typed_blocker.get("blocker_kind"))
        or _non_empty_text(typed_blocker.get("reason")),
        "typed_blocker_reason": _non_empty_text(typed_blocker.get("blocker_type"))
        or _non_empty_text(typed_blocker.get("blocker_kind"))
        or _non_empty_text(typed_blocker.get("reason")),
        "stage_closeout_status": _non_empty_text(typed_blocker.get("terminal_closeout_status")),
        "stage_closeout_outcome": _non_empty_text(typed_blocker.get("terminal_closeout_outcome")),
    }
    return is_anti_loop_stop_loss_closeout(closeout_like)


def _from_current_next_forced_delta(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    terminal_action = _from_terminal_stage_next_forced_delta(payload)
    if terminal_action is not None:
        return terminal_action
    return _from_next_forced_delta(payload)


def _consumed_ai_reviewer_followup_routes_to_write_repair(payload: Mapping[str, Any]) -> bool:
    terminal = _latest_ai_reviewer_terminal_stage(payload)
    if _non_empty_text(terminal.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    return _terminal_stage_semantically_consumes_ai_reviewer_followup(
        terminal=terminal,
        paper_stage_log=paper_stage_log,
        next_forced_delta=next_forced_delta,
    )


def _from_gate_followthrough_current_work_unit(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    followthrough = _mapping_copy(payload.get("gate_clearing_batch_followthrough"))
    if _non_empty_text(followthrough.get("status")) not in GATE_CLEARING_FOLLOWTHROUGH_CONSUMED_STATUSES:
        return None
    if _non_empty_text(followthrough.get("gate_replay_status")) != "blocked":
        return None
    currentness = _mapping_copy(followthrough.get("work_unit_currentness"))
    if _non_empty_text(currentness.get("current_actionability_status")) != "actionable":
        return None
    if currentness.get("lacks_specific_blocker_object") is True:
        return None
    explicit_work_unit_id = (
        _non_empty_text(currentness.get("explicit_publication_work_unit_id"))
        or _non_empty_text(followthrough.get("work_unit_id"))
        or _non_empty_text(_mapping_copy(followthrough.get("explicit_publication_work_unit")).get("unit_id"))
    )
    current_publication_work_unit = _mapping_copy(followthrough.get("current_publication_work_unit"))
    current_work_unit_id = (
        _non_empty_text(currentness.get("current_publication_work_unit_id"))
        or _non_empty_text(current_publication_work_unit.get("unit_id"))
    )
    if current_work_unit_id is None or current_work_unit_id == explicit_work_unit_id:
        return None
    lane = _non_empty_text(current_publication_work_unit.get("lane"))
    next_owner = lane if lane in {"write", "analysis-campaign", "finalize"} else "write"
    work_unit_fingerprint = _non_empty_text(currentness.get("current_work_unit_fingerprint"))
    source_eval_id = _non_empty_text(followthrough.get("source_eval_id"))
    source_ref = _non_empty_text(followthrough.get("latest_record_path"))
    owner_route_currentness_basis = _compact(
        {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": current_work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "explicit_publication_work_unit_id": explicit_work_unit_id,
        }
    )
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": next_owner,
            "work_unit_id": current_work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "source_eval_id": source_eval_id,
            "owner_route_currentness_basis": owner_route_currentness_basis or None,
            "action_type": QUALITY_REPAIR_ACTION,
            "allowed_actions": [QUALITY_REPAIR_ACTION],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_gate_actionable_repair_delta_or_typed_blocker",
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": next_owner,
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "gate_clearing_batch_ref": source_ref,
                "gate_replay_blockers": _text_items(followthrough.get("gate_replay_blockers")),
                "current_publication_work_unit": current_publication_work_unit or None,
            },
            "target_surface_specificity": "gate_followthrough_actionable_publication_work_unit",
            "acceptance_refs": [ref for ref in [source_ref] if ref],
            "authority_boundary": _authority_boundary(),
        }
    )


def _from_terminal_stage_next_forced_delta(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    terminal = _latest_terminal_stage_with_next_forced_delta(payload)
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    raw_action_type = (
        _non_empty_text(owner_action.get("action_type"))
        or _non_empty_text(next_forced_delta.get("action_type"))
        or _non_empty_text(terminal.get("action_type"))
    )
    action_type = _terminal_next_forced_delta_action_type(raw_action_type)
    if action_type not in TERMINAL_NEXT_FORCED_DELTA_ACTIONS:
        return None
    work_unit_id = (
        _non_empty_text(owner_action.get("work_unit_id"))
        or _non_empty_text(next_forced_delta.get("work_unit_id"))
        or _non_empty_text(paper_stage_log.get("stage_name"))
    )
    owner = (
        _non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
        or _non_empty_text(next_forced_delta.get("next_owner"))
        or _terminal_next_forced_delta_default_owner(raw_action_type)
        or _terminal_next_forced_delta_default_owner(action_type)
    )
    if owner is None and work_unit_id is None:
        return None
    source_ref = _non_empty_text(terminal.get("source_path"))
    required_delta_kind = (
        _non_empty_text(next_forced_delta.get("required_delta_kind"))
        or "paper_progress_delta_or_typed_blocker"
    )
    target_surface = _mapping_copy(next_forced_delta.get("target_surface")) or {
        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
    }
    source_eval_id = _non_empty_text(owner_action.get("source_eval_id")) or _non_empty_text(
        next_forced_delta.get("source_eval_id")
    )
    fingerprint = _terminal_next_forced_delta_fingerprint(
        payload=payload,
        terminal=terminal,
        paper_stage_log=paper_stage_log,
        next_forced_delta=next_forced_delta,
        owner_action=owner_action,
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
    )
    if fingerprint is None and action_type != GATE_CLEARING_ACTION:
        return None
    owner_route_currentness_basis = _compact(
        {
            "source": "study_progress.next_forced_delta.owner_action",
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "terminal_stage_status": _non_empty_text(terminal.get("status")),
            "terminal_stage_action_type": _non_empty_text(terminal.get("action_type")),
        }
    )
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "owner_route_currentness_basis": owner_route_currentness_basis or None,
            "action_type": action_type,
            "allowed_actions": [action_type],
            "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
            "required_delta_kind": required_delta_kind,
            "target_surface": target_surface,
            "target_surface_specificity": _non_empty_text(
                next_forced_delta.get("target_surface_specificity")
            )
            or "terminal_stage_next_forced_delta",
            "terminal_stage_next_forced_delta": True,
            "acceptance_refs": _dedupe_text(
                [source_ref, *_text_items(next_forced_delta.get("acceptance_refs"))]
            ),
            "authority_boundary": _authority_boundary(),
        }
    )


def _terminal_next_forced_delta_default_owner(action_type: str | None) -> str | None:
    if action_type == "return_to_write":
        return "write"
    if action_type == GATE_CLEARING_ACTION:
        return GATE_CLEARING_OWNER
    if action_type == QUALITY_REPAIR_ACTION:
        return "write"
    if action_type == "consume_record_only_ai_reviewer_closeout_or_route_next_owner":
        return "mas_controller"
    return None


def _terminal_next_forced_delta_action_type(action_type: str | None) -> str | None:
    if action_type == "return_to_write":
        return QUALITY_REPAIR_ACTION
    return action_type


def _latest_terminal_stage_with_next_forced_delta(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    progress_first = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        payload.get("latest_terminal_stage"),
        payload.get("latest_terminal_stage_log"),
    ):
        terminal = _mapping_copy(value)
        if not terminal:
            continue
        paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
        next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
            paper_stage_log.get("next_forced_delta")
        )
        owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
        action_type = _terminal_next_forced_delta_action_type(
            _non_empty_text(owner_action.get("action_type"))
            or _non_empty_text(next_forced_delta.get("action_type"))
            or _non_empty_text(terminal.get("action_type"))
        )
        if action_type in TERMINAL_NEXT_FORCED_DELTA_ACTIONS:
            return terminal
    return {}


def _terminal_next_forced_delta_fingerprint(
    *,
    payload: Mapping[str, Any],
    terminal: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
    owner_action: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
    source_eval_id: str | None,
) -> str | None:
    explicit_fingerprint = (
        _non_empty_text(owner_action.get("work_unit_fingerprint"))
        or _non_empty_text(owner_action.get("action_fingerprint"))
        or _non_empty_text(owner_action.get("fingerprint"))
        or _non_empty_text(next_forced_delta.get("work_unit_fingerprint"))
        or _non_empty_text(next_forced_delta.get("action_fingerprint"))
        or _non_empty_text(next_forced_delta.get("fingerprint"))
    )
    if explicit_fingerprint is not None:
        return explicit_fingerprint
    if work_unit_id == _non_empty_text(paper_stage_log.get("work_unit_id")):
        paper_stage_fingerprint = (
            _non_empty_text(paper_stage_log.get("work_unit_fingerprint"))
            or _non_empty_text(paper_stage_log.get("action_fingerprint"))
            or _non_empty_text(paper_stage_log.get("fingerprint"))
        )
        if paper_stage_fingerprint is not None:
            return paper_stage_fingerprint
    if work_unit_id == _non_empty_text(terminal.get("work_unit_id")):
        terminal_fingerprint = (
            _non_empty_text(terminal.get("work_unit_fingerprint"))
            or _non_empty_text(terminal.get("action_fingerprint"))
            or _non_empty_text(terminal.get("fingerprint"))
        )
        if terminal_fingerprint is not None:
            return terminal_fingerprint
    if action_type != GATE_CLEARING_ACTION:
        raw_action_type = (
            _non_empty_text(owner_action.get("action_type"))
            or _non_empty_text(next_forced_delta.get("action_type"))
            or _non_empty_text(terminal.get("action_type"))
        )
        return _terminal_closeout_next_forced_delta_fingerprint(
            payload=payload,
            terminal=terminal,
            next_forced_delta=next_forced_delta,
            owner_action=owner_action,
            action_type=action_type,
            work_unit_id=work_unit_id,
            source_eval_id=source_eval_id,
        )
    study_id = _non_empty_text(payload.get("study_id"))
    return current_ai_reviewer_gate_replay_fingerprint(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
    )


def _terminal_closeout_next_forced_delta_fingerprint(
    *,
    payload: Mapping[str, Any],
    terminal: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
    owner_action: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
    source_eval_id: str | None,
) -> str | None:
    terminal_ref = (
        _non_empty_text(terminal.get("source_path"))
        or _non_empty_text(terminal.get("source_ref"))
        or _non_empty_text(terminal.get("closeout_ref"))
    )
    stage_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    reviewer_record_ref = _non_empty_text(next_forced_delta.get("reviewer_record_ref")) or _non_empty_text(
        owner_action.get("reviewer_record_ref")
    )
    publication_eval_ref = _non_empty_text(_mapping_copy(next_forced_delta.get("target_surface")).get("publication_eval_latest_ref"))
    if not any((terminal_ref, stage_attempt_id, reviewer_record_ref, publication_eval_ref, source_eval_id)):
        return None
    return control_identity.stable_route_currentness_fingerprint(
        study_id=_non_empty_text(payload.get("study_id")),
        source="study_progress.next_forced_delta.owner_action",
        work_unit_id=work_unit_id,
        action_type=action_type,
        next_owner=_non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
        or _terminal_next_forced_delta_default_owner(action_type),
        source_eval_id=source_eval_id,
        target_surface_ref=publication_eval_ref or reviewer_record_ref or terminal_ref,
        required_delta_kind=_non_empty_text(next_forced_delta.get("required_delta_kind")),
    )


def _from_stage_kernel_readiness_followup(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    readiness = _mapping_copy(payload.get("medical_paper_readiness"))
    if _non_empty_text(readiness.get("overall_status")) == "ready":
        return None
    delta = _current_owner_delta(payload)
    if _readiness_action(delta) != READINESS_ACTION:
        return None
    if not _is_stage_kernel_typed_blocker_followup(delta):
        return None
    source_ref = _non_empty_text(delta.get("source_ref"))
    next_action = _readiness_next_action(readiness=readiness, delta=delta)
    surface_key = _readiness_surface_key(next_action=next_action, delta=delta)
    if not _readiness_next_action_identifies_followup(
        next_action=next_action,
        surface_key=surface_key,
    ):
        return None
    target_surface = {
        "ref_kind": "mas_owner_surface",
        "surface_ref": _non_empty_text(delta.get("required_input")) or READINESS_ACTION,
        "blocked_surface": _non_empty_text(delta.get("blocked_surface"))
        or PUBLICATION_HANDOFF_ACTION,
    }
    if surface_key is not None:
        target_surface["surface_key"] = surface_key
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "stage_kernel_projection.current_owner_delta",
            "next_owner": _non_empty_text(delta.get("owner")) or READINESS_OWNER,
            "work_unit_id": READINESS_ACTION,
            "allowed_actions": [READINESS_ACTION],
            "owner_receipt_required": True,
            "required_delta_kind": "medical_paper_readiness_surface_or_typed_blocker",
            "target_surface": target_surface,
            "target_surface_specificity": "stage_kernel_typed_blocker_followup",
            "surface_key": surface_key,
            "next_action": next_action or None,
            "acceptance_refs": _text_items(delta.get("acceptance_refs")),
            "blocked_surface": _non_empty_text(delta.get("blocked_surface")) or PUBLICATION_HANDOFF_ACTION,
            "source_ref": source_ref,
            "latest_owner_answer_ref": _non_empty_text(delta.get("latest_owner_answer_ref")) or source_ref,
            "latest_owner_answer_kind": _non_empty_text(delta.get("latest_owner_answer_kind"))
            or _non_empty_text(delta.get("source_kind")),
            "artifact_first_precedence": {
                "superseded_stage_artifact_action": PUBLICATION_HANDOFF_ACTION,
                "reason": _non_empty_text(delta.get("reason")) or READINESS_BLOCKER,
                "typed_blocker_followup_takes_precedence": True,
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _from_repair_progress_projection(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    repair_progress = _mapping_copy(payload.get("repair_progress_projection"))
    if repair_progress.get("paper_delta_observed") is not True:
        return None
    if repair_progress.get("accepted_owner_receipt") is not True:
        return None
    source_ref = _non_empty_text(repair_progress.get("repair_execution_evidence_ref")) or _non_empty_text(
        repair_progress.get("owner_receipt_ref")
    )
    ai_reviewer_request_ref = _non_empty_text(repair_progress.get("ai_reviewer_recheck_request_ref"))
    gate_replay_refs = _text_items(repair_progress.get("gate_replay_refs"))
    if gate_replay_refs and repair_progress.get("ai_reviewer_recheck_done") is True:
        return _repair_followup_action(
            repair_progress=repair_progress,
            source_ref=source_ref,
            next_owner=GATE_CLEARING_OWNER,
            work_unit_id=GATE_CLEARING_WORK_UNIT,
            action_type=GATE_CLEARING_ACTION,
            required_delta_kind="publication_gate_replay_delta_or_typed_blocker",
            target_surface={
                "ref_kind": "route_obligation",
                "route_target": "finalize",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "request_ref": gate_replay_refs[0],
            },
            acceptance_refs=gate_replay_refs,
        )
    if ai_reviewer_request_ref is not None:
        return _repair_followup_action(
            repair_progress=repair_progress,
            source_ref=source_ref,
            next_owner=AI_REVIEWER_OWNER,
            work_unit_id=AI_REVIEWER_WORK_UNIT,
            action_type=AI_REVIEWER_ACTION,
            required_delta_kind="ai_reviewer_publication_eval_delta_or_typed_blocker",
            target_surface={
                "ref_kind": "route_obligation",
                "route_target": "review",
                "surface_ref": "artifacts/publication_eval/latest.json",
                "request_ref": ai_reviewer_request_ref,
                "gate_replay_request_ref": gate_replay_refs[0] if gate_replay_refs else None,
            },
            acceptance_refs=[ai_reviewer_request_ref, *gate_replay_refs],
        )
    if gate_replay_refs:
        return _repair_followup_action(
            repair_progress=repair_progress,
            source_ref=source_ref,
            next_owner=GATE_CLEARING_OWNER,
            work_unit_id=GATE_CLEARING_WORK_UNIT,
            action_type=GATE_CLEARING_ACTION,
            required_delta_kind="publication_gate_replay_delta_or_typed_blocker",
            target_surface={
                "ref_kind": "route_obligation",
                "route_target": "finalize",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "request_ref": gate_replay_refs[0],
            },
            acceptance_refs=gate_replay_refs,
        )
    return None


def _from_publication_eval_readiness_blocker_repair(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    publication_eval = _mapping_copy(payload.get("publication_eval"))
    action = _publication_eval_route_back_action(publication_eval)
    if not action:
        source_publication_eval = _mapping_copy(publication_eval.get("source_publication_eval"))
        action = _publication_eval_route_back_action(source_publication_eval)
        if action:
            publication_eval = source_publication_eval
    if not action:
        return None
    current_owner_delta = _current_owner_delta(payload)
    next_work_unit = _mapping_copy(action.get("next_work_unit"))
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    lane = _non_empty_text(next_work_unit.get("lane")) or _non_empty_text(action.get("route_target"))
    if work_unit_id is None or lane not in {"write", "analysis-campaign"}:
        return None
    action_type = QUALITY_REPAIR_ACTION
    source_ref = _text_items(action.get("evidence_refs"))[0] if _text_items(action.get("evidence_refs")) else None
    work_unit_fingerprint = _non_empty_text(action.get("work_unit_fingerprint"))
    stage_typed_blocker_ref = (
        _non_empty_text(current_owner_delta.get("source_ref"))
        or _non_empty_text(_mapping_copy(current_owner_delta.get("hard_gate")).get("owner_answer_ref"))
    )
    publication_eval_id = (
        _non_empty_text(publication_eval.get("eval_id"))
        or _non_empty_text(publication_eval.get("publication_eval_id"))
        or _non_empty_text(action.get("source_eval_id"))
    )
    gaps = [
        _compact(
            {
                "gap_id": _non_empty_text(gap.get("gap_id")),
                "gap_type": _non_empty_text(gap.get("gap_type")),
                "severity": _non_empty_text(gap.get("severity")),
                "summary": _non_empty_text(gap.get("summary")),
            }
        )
        for gap in _mapping_items(publication_eval.get("gaps"))
    ]
    gap_ids = [gap["gap_id"] for gap in gaps if _non_empty_text(gap.get("gap_id")) is not None]
    required_output_contract = {
        "accepted_outputs_any": [
            "canonical_manuscript_story_surface_delta",
            "claim_evidence_semantic_delta",
            "review_ledger_delta",
            "publication_gate_delta",
            "stage_owner_receipt_ref",
            "stable_typed_blocker_for_the_specific_repair_work_unit",
        ],
        "forbidden_outputs": [
            "publication_ready_claim",
            "submission_ready_claim",
            "current_package_authority",
            "publication_eval_latest_manual_write",
            "controller_decision_manual_write",
        ],
    }
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "publication_eval.recommended_actions.readiness_blocker_repair",
            "next_owner": lane,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "action_type": action_type,
            "allowed_actions": [action_type],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_eval_recommended_repair_delta_or_typed_blocker",
            "required_output_contract": required_output_contract,
            "stage_typed_blocker_ref": stage_typed_blocker_ref,
            "publication_eval_id": publication_eval_id,
            "gap_ids": gap_ids,
            "target_surface": {
                "ref_kind": "publication_eval_recommended_action",
                "route_target": lane,
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "recommended_action_id": _non_empty_text(action.get("action_id")),
                "route_key_question": _non_empty_text(action.get("route_key_question")),
                "route_rationale": _non_empty_text(action.get("route_rationale")),
                "stage_typed_blocker_ref": stage_typed_blocker_ref,
                "publication_eval_id": publication_eval_id,
                "gap_ids": gap_ids,
                "required_output_contract": required_output_contract,
                "next_work_unit": next_work_unit or None,
                "blocking_work_units": _mapping_items(action.get("blocking_work_units")),
                "gaps": [gap for gap in gaps if gap],
            },
            "target_surface_specificity": "publication_eval_readiness_blocker_derived_repair",
            "source_ref": source_ref,
            "acceptance_refs": _dedupe_text(_text_items(action.get("evidence_refs"))),
            "readiness_blocker_precedence": {
                "superseded_readiness_action": READINESS_ACTION,
                "reason": "superseded_by_readiness_blocker_derived_repair",
                "publication_eval_verdict": _non_empty_text(
                    _mapping_copy(publication_eval.get("verdict")).get("overall_verdict")
                ),
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _publication_eval_route_back_action(publication_eval: Mapping[str, Any]) -> dict[str, Any]:
    for action in _mapping_items(publication_eval.get("recommended_actions")):
        if _non_empty_text(action.get("action_type")) != "route_back_same_line":
            continue
        if _non_empty_text(action.get("priority")) not in {"now", "high", "required"}:
            continue
        if not _mapping_copy(action.get("next_work_unit")):
            continue
        return action
    return {}


def _repair_followup_action(
    *,
    repair_progress: Mapping[str, Any],
    source_ref: str | None,
    next_owner: str,
    work_unit_id: str,
    action_type: str,
    required_delta_kind: str,
    target_surface: Mapping[str, Any],
    acceptance_refs: list[str],
) -> dict[str, Any]:
    owner_receipt_ref = _non_empty_text(repair_progress.get("owner_receipt_ref"))
    repair_evidence_ref = _non_empty_text(repair_progress.get("repair_execution_evidence_ref"))
    work_unit_fingerprint = _non_empty_text(repair_progress.get("source_fingerprint"))
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": REPAIR_PROGRESS_SOURCE,
            "next_owner": next_owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "action_type": action_type,
            "allowed_actions": [action_type],
            "owner_receipt_required": True,
            "required_delta_kind": required_delta_kind,
            "target_surface": _compact(target_surface),
            "target_surface_specificity": "repair_progress_followup_owner_surface",
            "source_ref": source_ref,
            "acceptance_refs": _dedupe_text(
                [
                    repair_evidence_ref,
                    owner_receipt_ref,
                    *acceptance_refs,
                ]
            ),
            "repair_progress_precedence": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "superseded_stage_native_action": "run_quality_repair_batch",
                "superseded_readiness_action": READINESS_ACTION,
                "source_work_unit_id": _non_empty_text(repair_progress.get("work_unit_id")),
                "source_fingerprint": _non_empty_text(repair_progress.get("source_fingerprint")),
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _from_next_forced_delta(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    next_forced_delta = _mapping_copy(payload.get("next_forced_delta"))
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    study_id = _non_empty_text(payload.get("study_id"))
    owner = _non_empty_text(owner_action.get("next_owner")) or _non_empty_text(
        next_forced_delta.get("next_owner")
    )
    work_unit_id = _non_empty_text(owner_action.get("work_unit_id")) or _non_empty_text(
        next_forced_delta.get("work_unit_id")
    )
    allowed_actions = _text_items(owner_action.get("allowed_actions")) or _text_items(
        next_forced_delta.get("allowed_actions")
    )
    action_type = (
        _non_empty_text(owner_action.get("action_type"))
        or _non_empty_text(next_forced_delta.get("action_type"))
        or (allowed_actions[0] if len(allowed_actions) == 1 else None)
    )
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    source_eval_id = _next_forced_delta_source_eval_id(
        next_forced_delta=next_forced_delta,
        owner_action=owner_action,
        payload=payload,
    )
    eval_bound_fingerprint = current_ai_reviewer_gate_replay_fingerprint(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
    )
    if (
        action_type == GATE_CLEARING_ACTION
        and eval_bound_fingerprint is None
        and not _consumed_repair_followup_allows_unbound_gate_replay(payload)
    ):
        return None
    owner_route_currentness_basis = (
        _compact(
            {
                "source_eval_id": source_eval_id,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": eval_bound_fingerprint,
                "source": "study_progress.next_forced_delta.owner_action",
            }
        )
        if eval_bound_fingerprint is not None
        else {}
    )
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": eval_bound_fingerprint,
            "action_fingerprint": eval_bound_fingerprint,
            "source_eval_id": source_eval_id,
            "owner_route_currentness_basis": owner_route_currentness_basis or None,
            "action_type": action_type,
            "allowed_actions": allowed_actions,
            "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
            "required_delta_kind": _non_empty_text(next_forced_delta.get("required_delta_kind")),
            "target_surface": _mapping_copy(next_forced_delta.get("target_surface")) or None,
            "target_surface_specificity": _non_empty_text(
                next_forced_delta.get("target_surface_specificity")
            ),
            "acceptance_refs": _text_items(next_forced_delta.get("acceptance_refs")),
            "authority_boundary": _authority_boundary(),
        }
    )


def _next_forced_delta_source_eval_id(
    *,
    next_forced_delta: Mapping[str, Any],
    owner_action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> str | None:
    publication_eval = _mapping_copy(payload.get("publication_eval"))
    progress_first = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    dispatch_consumption = _mapping_copy(progress_first.get("dispatch_consumption"))
    canonical_identity = _mapping_copy(dispatch_consumption.get("canonical_work_unit_identity"))
    owner_route_basis = _mapping_copy(dispatch_consumption.get("owner_route_currentness_basis"))
    canonical_owner_route_basis = _mapping_copy(canonical_identity.get("owner_route_currentness_basis"))
    return (
        _non_empty_text(owner_action.get("source_eval_id"))
        or _non_empty_text(owner_action.get("eval_id"))
        or _non_empty_text(next_forced_delta.get("source_eval_id"))
        or _non_empty_text(next_forced_delta.get("eval_id"))
        or _non_empty_text(publication_eval.get("eval_id"))
        or _non_empty_text(dispatch_consumption.get("source_eval_id"))
        or _non_empty_text(canonical_identity.get("source_eval_id"))
        or _non_empty_text(owner_route_basis.get("source_eval_id"))
        or _non_empty_text(canonical_owner_route_basis.get("source_eval_id"))
    )


def _consumed_repair_followup_allows_unbound_gate_replay(payload: Mapping[str, Any]) -> bool:
    repair_progress_action = _from_repair_progress_projection(payload)
    return repair_progress_action is not None and _action_consumed_by_dispatch_receipt(
        action=repair_progress_action,
        payload=payload,
    )


def _next_forced_delta_supersedes_stale_readiness_blocker(
    action: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping_copy(action)
    if _non_empty_text(payload.get("source")) != "study_progress.next_forced_delta.owner_action":
        return False
    if _non_empty_text(payload.get("required_delta_kind")) != "review_current_paper_delta":
        return False
    values = {
        _non_empty_text(payload.get("action_type")),
        _non_empty_text(payload.get("work_unit_id")),
        *_text_items(payload.get("allowed_actions")),
    }
    if READINESS_ACTION in values:
        return False
    return bool(
        values.intersection(
            {
                "return_to_ai_reviewer_workflow",
                "run_gate_clearing_batch",
                "run_quality_repair_batch",
            }
        )
    )


def _next_forced_delta_is_terminal_routeback_action(
    action: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping_copy(action)
    if _non_empty_text(payload.get("source")) != "study_progress.next_forced_delta.owner_action":
        return False
    if payload.get("terminal_stage_next_forced_delta") is not True:
        return False
    if _non_empty_text(payload.get("action_type")) != QUALITY_REPAIR_ACTION:
        return False
    if _non_empty_text(payload.get("next_owner")) != "write":
        return False
    return _non_empty_text(payload.get("work_unit_id")) is not None


def _next_forced_delta_supersedes_gate_followthrough(
    *,
    next_forced_delta_action: Mapping[str, Any] | None,
    gate_followthrough_action: Mapping[str, Any] | None,
) -> bool:
    next_action = _mapping_copy(next_forced_delta_action)
    gate_action = _mapping_copy(gate_followthrough_action)
    if not next_action or not gate_action:
        return False
    if _non_empty_text(gate_action.get("source")) != "gate_clearing_batch_followthrough.actionable_current_work_unit":
        return False
    if _non_empty_text(next_action.get("source")) != "study_progress.next_forced_delta.owner_action":
        return False
    next_action_type = _non_empty_text(next_action.get("action_type"))
    if next_action_type not in TERMINAL_NEXT_FORCED_DELTA_ACTIONS:
        return False
    if _non_empty_text(gate_action.get("action_type")) != QUALITY_REPAIR_ACTION:
        return False
    next_source_eval_id = _non_empty_text(next_action.get("source_eval_id"))
    gate_source_eval_id = _non_empty_text(gate_action.get("source_eval_id"))
    if next_action.get("terminal_stage_next_forced_delta") is True:
        return _terminal_stage_next_delta_supersedes_gate_followthrough(
            next_action=next_action,
            gate_action=gate_action,
        )
    if next_action_type != GATE_CLEARING_ACTION:
        return False
    if next_source_eval_id is None or gate_source_eval_id is None:
        return False
    if next_source_eval_id == gate_source_eval_id:
        return False
    if _non_empty_text(next_action.get("work_unit_id")) == _non_empty_text(gate_action.get("work_unit_id")):
        return False
    return True


def _terminal_stage_next_delta_supersedes_gate_followthrough(
    *,
    next_action: Mapping[str, Any],
    gate_action: Mapping[str, Any],
) -> bool:
    next_work_unit = _non_empty_text(next_action.get("work_unit_id"))
    if next_work_unit is None:
        return False
    if next_work_unit == _non_empty_text(gate_action.get("work_unit_id")):
        return False
    if _non_empty_text(next_action.get("action_type")) == QUALITY_REPAIR_ACTION:
        return True
    gate_basis = _mapping_copy(gate_action.get("owner_route_currentness_basis"))
    explicit_publication_work_unit = _non_empty_text(
        gate_basis.get("explicit_publication_work_unit_id")
    )
    return next_work_unit == explicit_publication_work_unit


def _action_consumed_by_dispatch_receipt(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if _terminal_stage_closeout_consumes_repair_followup(action=action, payload=payload):
        return True
    if _terminal_gate_closeout_consumes_repair_followup(action=action, payload=payload):
        return True
    consumption = _mapping_copy(_mapping_copy(payload.get("progress_first_monitoring_summary")).get("dispatch_consumption"))
    if not consumption:
        consumption = _mapping_copy(_mapping_copy(payload.get("domain_transition")).get("completion_receipt_consumption"))
    if not consumption:
        consumption = _mapping_copy(
            _mapping_copy(payload.get("domain_transition")).get("default_executor_execution_receipt_consumption")
        )
    consumption_status = _non_empty_text(consumption.get("consumption_status")) or _non_empty_text(
        consumption.get("status")
    )
    if consumption_status != "consumed":
        return False
    action_work_unit = _non_empty_text(action.get("work_unit_id"))
    consumed_work_unit = _non_empty_text(consumption.get("work_unit_id"))
    if action_work_unit is None or consumed_work_unit != action_work_unit:
        return False
    action_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint"))
    )
    consumed_fingerprint = (
        _non_empty_text(consumption.get("work_unit_fingerprint"))
        or _non_empty_text(consumption.get("action_fingerprint"))
        or _non_empty_text(_mapping_copy(consumption.get("canonical_work_unit_identity")).get("work_unit_fingerprint"))
    )
    if action_fingerprint is not None and action_fingerprint == consumed_fingerprint:
        return True
    return _ai_reviewer_eval_receipt_consumes_repair_followup(
        action=action,
        consumption=consumption,
    )


def _terminal_gate_closeout_consumes_repair_followup(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != GATE_CLEARING_ACTION:
        return False
    action_work_unit = _non_empty_text(action.get("work_unit_id"))
    if action_work_unit != GATE_CLEARING_WORK_UNIT:
        return False
    terminal = _latest_gate_replay_terminal_stage(payload)
    if not terminal:
        return False
    if _non_empty_text(terminal.get("action_type")) != GATE_CLEARING_ACTION:
        return False
    if _non_empty_text(terminal.get("status")) not in {
        "blocked",
        "closed",
        "completed",
        "executed",
        "typed_blocked",
    }:
        return False
    terminal_work_unit = _non_empty_text(terminal.get("work_unit_id"))
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    terminal_work_unit = terminal_work_unit or _non_empty_text(next_forced_delta.get("work_unit_id"))
    if terminal_work_unit != action_work_unit:
        return False
    action_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(_mapping_copy(action.get("repair_progress_precedence")).get("source_fingerprint"))
    )
    terminal_fingerprint = (
        _non_empty_text(terminal.get("work_unit_fingerprint"))
        or _non_empty_text(terminal.get("action_fingerprint"))
        or _non_empty_text(paper_stage_log.get("work_unit_fingerprint"))
        or _non_empty_text(paper_stage_log.get("action_fingerprint"))
    )
    if action_fingerprint is not None and action_fingerprint == terminal_fingerprint:
        return True
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker":
        return False
    if _non_empty_text(current_work_unit.get("work_unit_id")) != action_work_unit:
        return False
    current_fingerprint = (
        _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
        or _non_empty_text(current_work_unit.get("action_fingerprint"))
    )
    if action_fingerprint is not None and action_fingerprint == current_fingerprint:
        return True
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(
        current_work_unit.get("typed_blocker")
    )
    blocker_fingerprint = (
        _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
        or _non_empty_text(typed_blocker.get("action_fingerprint"))
    )
    return action_fingerprint is not None and action_fingerprint == blocker_fingerprint


def _terminal_stage_closeout_consumes_repair_followup(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    if _non_empty_text(action.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    terminal = _latest_ai_reviewer_terminal_stage(payload)
    if _non_empty_text(terminal.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    status = _non_empty_text(terminal.get("status"))
    outcome = _non_empty_text(terminal.get("outcome"))
    if status not in {
        "closed_with_domain_owner_refs",
        "completed_with_domain_owner_record_only_archive",
        "completed_with_record_only_artifact_delta",
        "executed",
        "executed_record_only",
        "executed_record_only_archive_materialized",
        "executed_with_owner_receipt",
        "record_only_archive_materialized",
    } and outcome not in {"owner_receipt", "closed_with_domain_owner_refs"}:
        return False
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    next_owner = (
        _non_empty_text(next_forced_delta.get("owner"))
        or _non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
    )
    next_action_type = _non_empty_text(owner_action.get("action_type")) or _non_empty_text(
        next_forced_delta.get("action_type")
    )
    if _terminal_stage_semantically_consumes_ai_reviewer_followup(
        terminal=terminal,
        paper_stage_log=paper_stage_log,
        next_forced_delta=next_forced_delta,
    ):
        return next_action_type in TERMINAL_NEXT_FORCED_DELTA_ACTIONS or next_action_type in {
            "return_to_write",
        }
    if next_owner != "mas_controller":
        return False
    if next_action_type not in {
        "consume_record_only_ai_reviewer_closeout_or_route_next_owner",
        "return_to_write",
    }:
        return False
    action_stage_attempt = _stage_attempt_id_from_refs(action.get("acceptance_refs"))
    terminal_stage_attempt = _non_empty_text(terminal.get("stage_attempt_id")) or _stage_attempt_id_from_refs(
        [terminal.get("source_path")]
    )
    if action_stage_attempt is not None and terminal_stage_attempt is not None:
        return action_stage_attempt == terminal_stage_attempt
    source_eval_id = _non_empty_text(next_forced_delta.get("source_eval_id"))
    if terminal_stage_attempt is not None and source_eval_id is not None:
        return terminal_stage_attempt in source_eval_id
    action_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(_mapping_copy(action.get("repair_progress_precedence")).get("source_fingerprint"))
    )
    terminal_refs = [terminal.get("source_path"), *_text_items(terminal.get("closeout_refs"))]
    return action_fingerprint is not None and any(
        action_fingerprint in ref for ref in terminal_refs if isinstance(ref, str)
    )


def _terminal_stage_semantically_consumes_ai_reviewer_followup(
    *,
    terminal: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
) -> bool:
    required_delta_kind = _non_empty_text(next_forced_delta.get("required_delta_kind"))
    if required_delta_kind not in {
        "same_line_write_repair_or_gate_replay_route",
        "same_line_write_repair_or_typed_blocker_consumption",
    }:
        return False
    next_work_unit = _non_empty_text(next_forced_delta.get("work_unit_id"))
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    if _non_empty_text(owner_action.get("work_unit_id")) not in {next_work_unit, None}:
        return False
    if next_work_unit in {None, AI_REVIEWER_WORK_UNIT}:
        return False
    progress_delta_classification = (
        _non_empty_text(paper_stage_log.get("progress_delta_classification"))
        or _non_empty_text(terminal.get("progress_delta_classification"))
    )
    if progress_delta_classification not in {"deliverable_progress", "paper_progress", "mixed"}:
        return False
    refs = _dedupe_text(
        [
            terminal.get("source_path"),
            *list(terminal.get("closeout_refs") or []),
            *list(terminal.get("changed_paper_surfaces") or []),
            *list(paper_stage_log.get("changed_paper_surfaces") or []),
            _mapping_copy(next_forced_delta.get("target_surface")).get("surface_ref"),
            _mapping_copy(next_forced_delta.get("target_surface")).get("publication_eval_latest_ref"),
        ]
    )
    return any("publication_eval/ai_reviewer_responses" in ref for ref in refs)


def _latest_ai_reviewer_terminal_stage(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    progress_first = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        payload.get("latest_terminal_stage"),
        payload.get("latest_terminal_stage_log"),
    ):
        terminal = _mapping_copy(value)
        if _non_empty_text(terminal.get("action_type")) == AI_REVIEWER_ACTION:
            return terminal
    return {}


def _latest_gate_replay_terminal_stage(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    progress_first = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        payload.get("latest_terminal_stage"),
        payload.get("latest_terminal_stage_log"),
    ):
        terminal = _mapping_copy(value)
        if _non_empty_text(terminal.get("action_type")) == GATE_CLEARING_ACTION:
            return terminal
    return {}


def _stage_attempt_id_from_refs(value: object) -> str | None:
    for ref in _text_items(value):
        for part in ref.replace("#", "/").replace(".", "/").split("/"):
            if part.startswith("sat_"):
                return part
    return None


def _ai_reviewer_eval_receipt_consumes_repair_followup(
    *,
    action: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    if _non_empty_text(action.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    if _non_empty_text(consumption.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return False
    receipt_ref = _non_empty_text(consumption.get("receipt_ref"))
    if receipt_ref is None or "publication_eval" not in receipt_ref:
        return False
    if _non_empty_text(consumption.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    return _ai_reviewer_eval_receipt_binds_repair_followup(
        action=action,
        consumption=consumption,
    )


def _ai_reviewer_eval_receipt_binds_repair_followup(
    *,
    action: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> bool:
    repair_precedence = _mapping_copy(action.get("repair_progress_precedence"))
    target_surface = _mapping_copy(action.get("target_surface"))
    expected_source_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(repair_precedence.get("source_fingerprint"))
    )
    binding_mappings = _ai_reviewer_consumption_binding_mappings(consumption)
    if expected_source_fingerprint is not None:
        explicit_fingerprints = {
            text
            for mapping in binding_mappings
            for key in (
                "repair_source_fingerprint",
                "repair_progress_source_fingerprint",
                "repair_execution_source_fingerprint",
            )
            if (text := _non_empty_text(mapping.get(key))) is not None
        }
        if expected_source_fingerprint in explicit_fingerprints:
            return True
    expected_refs = set(
        _dedupe_text(
            [
                action.get("source_ref"),
                target_surface.get("request_ref"),
                target_surface.get("gate_replay_request_ref"),
                *list(action.get("acceptance_refs") or []),
            ]
        )
    )
    if expected_refs:
        explicit_refs = {
            text
            for mapping in binding_mappings
            for key in (
                "repair_execution_evidence_ref",
                "owner_receipt_ref",
                "ai_reviewer_recheck_request_ref",
                "request_ref",
                "gate_replay_request_ref",
            )
            if (text := _non_empty_text(mapping.get(key))) is not None
        }
        if expected_refs.intersection(explicit_refs):
            return True
    expected_source_eval_id = _non_empty_text(repair_precedence.get("source_eval_id"))
    if expected_source_eval_id is not None:
        explicit_source_eval_ids = {
            text
            for mapping in binding_mappings
            for key in ("repair_source_eval_id", "repair_progress_source_eval_id")
            if (text := _non_empty_text(mapping.get(key))) is not None
        }
        if expected_source_eval_id in explicit_source_eval_ids:
            return True
    return False


def _ai_reviewer_consumption_binding_mappings(consumption: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    canonical = _mapping_copy(consumption.get("canonical_work_unit_identity"))
    owner_route_basis = _mapping_copy(consumption.get("owner_route_currentness_basis"))
    canonical_owner_route_basis = _mapping_copy(canonical.get("owner_route_currentness_basis"))
    source_refs = _mapping_copy(consumption.get("source_refs"))
    source_refs_basis = _mapping_copy(source_refs.get("owner_route_currentness_basis"))
    return [
        consumption,
        canonical,
        owner_route_basis,
        canonical_owner_route_basis,
        source_refs,
        source_refs_basis,
    ]


def owner_action_next_step(action: Mapping[str, Any]) -> str | None:
    owner = _non_empty_text(action.get("next_owner"))
    actions = _text_items(action.get("allowed_actions"))
    work_unit_id = _non_empty_text(action.get("work_unit_id"))
    if owner is None and not actions and work_unit_id is None:
        return None
    owner_text = f"{owner} owner" if owner is not None else "当前 owner"
    action_text = f"执行 {actions[0]}" if actions else "处理当前 owner action"
    work_unit_text = f"，处理 work unit {work_unit_id}" if work_unit_id is not None else ""
    return f"等待 {owner_text} {action_text}{work_unit_text}，产出 owner receipt、typed blocker 或下一 owner handoff。"


def _from_stage_artifact_index(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    index = _mapping_copy(payload.get("stage_artifact_index"))
    if _non_empty_text(index.get("surface_kind")) != "stage_artifact_index":
        return None
    owner_action = _mapping_copy(index.get("next_owner_action"))
    owner = _non_empty_text(owner_action.get("next_owner"))
    work_unit_id = _non_empty_text(owner_action.get("work_unit_id"))
    allowed_actions = _text_items(owner_action.get("allowed_actions"))
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    stale_platform_repairs = _mapping_items(index.get("stale_platform_repairs"))
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "stage_artifact_index.next_owner_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "allowed_actions": allowed_actions,
            "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
            "required_delta_kind": _non_empty_text(owner_action.get("required_delta_kind")),
            "target_surface": _mapping_copy(owner_action.get("target_surface")) or None,
            "target_surface_specificity": _non_empty_text(
                owner_action.get("target_surface_specificity")
            ),
            "acceptance_refs": _text_items(owner_action.get("acceptance_refs")),
            "artifact_first_precedence": {
                "surface_kind": "stage_artifact_index",
                "current_stage": _non_empty_text(index.get("current_stage")),
                "stale_platform_repairs_superseded": bool(stale_platform_repairs),
                "stale_platform_repairs": stale_platform_repairs,
                "stage_count": len(_mapping_items(index.get("stages"))),
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _from_stage_native_current_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    action = _mapping_copy(payload.get("stage_native_current_owner_action"))
    if _non_empty_text(action.get("source")) != "stage_native_workspace_next_action":
        return None
    owner = _non_empty_text(action.get("next_owner"))
    work_unit_id = _non_empty_text(action.get("work_unit_id"))
    allowed_actions = _text_items(action.get("allowed_actions"))
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "stage_native_workspace_next_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "action_type": _non_empty_text(action.get("action_type")),
            "allowed_actions": allowed_actions,
            "owner_receipt_required": action.get("owner_receipt_required") is not False,
            "required_delta_kind": _non_empty_text(action.get("required_delta_kind")),
            "target_surface": _mapping_copy(action.get("target_surface")) or None,
            "source_ref": _non_empty_text(action.get("source_ref")),
            "authority_boundary": _mapping_copy(action.get("authority_boundary"))
            or _authority_boundary(),
        }
    )


def _from_domain_transition(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    transition = _mapping_copy(payload.get("domain_transition"))
    next_work_unit = _mapping_copy(transition.get("next_work_unit"))
    owner = _non_empty_text(transition.get("owner")) or _non_empty_text(transition.get("route_target"))
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    action = _non_empty_text(transition.get("controller_action"))
    if owner is None and work_unit_id is None and action is None:
        return None
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "domain_transition",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "allowed_actions": [action] if action is not None else [],
            "owner_receipt_required": True,
            "authority_boundary": _authority_boundary(),
        }
    )


def _current_owner_delta(payload: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping_copy(payload.get("current_owner_delta"))
    if direct:
        return direct
    stage_kernel = _mapping_copy(payload.get("stage_kernel_projection"))
    delta = _mapping_copy(stage_kernel.get("current_owner_delta"))
    if delta:
        return delta
    stage_run_kernel = _mapping_copy(stage_kernel.get("stage_run_kernel"))
    return _mapping_copy(stage_run_kernel.get("current_owner_delta"))


def _readiness_next_action(*, readiness: Mapping[str, Any], delta: Mapping[str, Any]) -> dict[str, Any]:
    next_action = _mapping_copy(delta.get("next_action")) or _mapping_copy(readiness.get("next_action"))
    if not next_action:
        return {}
    return {
        key: value
        for key, value in next_action.items()
        if value not in (None, "", [], {})
    }


def _readiness_surface_key(*, next_action: Mapping[str, Any], delta: Mapping[str, Any]) -> str | None:
    return (
        _non_empty_text(delta.get("surface_key"))
        or _non_empty_text(next_action.get("surface_key"))
    )


def _readiness_next_action_identifies_followup(
    *,
    next_action: Mapping[str, Any],
    surface_key: str | None,
) -> bool:
    if not next_action:
        return False
    if surface_key is not None:
        return True
    action = _non_empty_text(next_action.get("action_id")) or _non_empty_text(
        next_action.get("action_type")
    )
    if action is not None and action not in {READINESS_ACTION, "continue_managed_execution"}:
        return True
    if _non_empty_text(next_action.get("route_target")) or _non_empty_text(
        next_action.get("next_owner")
    ):
        return True
    if _non_empty_text(next_action.get("work_unit_id")):
        return True
    return bool(_mapping_copy(next_action.get("target_surface")))


def _readiness_action(delta: Mapping[str, Any]) -> str | None:
    return _non_empty_text(delta.get("action")) or _non_empty_text(delta.get("action_type"))


def _stage_kernel_readiness_answer_without_followup(payload: Mapping[str, Any]) -> bool:
    readiness = _mapping_copy(payload.get("medical_paper_readiness"))
    if _non_empty_text(readiness.get("overall_status")) == "ready":
        return False
    delta = _current_owner_delta(payload)
    if _readiness_action(delta) != READINESS_ACTION:
        return False
    if not _is_stage_kernel_typed_blocker_followup(delta):
        return False
    next_action = _readiness_next_action(readiness=readiness, delta=delta)
    surface_key = _readiness_surface_key(next_action=next_action, delta=delta)
    return not _readiness_next_action_identifies_followup(
        next_action=next_action,
        surface_key=surface_key,
    )


def _stage_kernel_readiness_stable_typed_blocker_answer(payload: Mapping[str, Any]) -> bool:
    delta = _current_owner_delta(payload)
    if _readiness_action(delta) != READINESS_ACTION:
        return False
    if not _is_stage_kernel_typed_blocker_followup(delta):
        return False
    return _non_empty_text(delta.get("reason")) == "medical_paper_readiness_missing"


def _stage_kernel_owner_answer_recorded_without_next_action(payload: Mapping[str, Any]) -> bool:
    delta = _current_owner_delta(payload)
    hard_gate = _mapping_copy(delta.get("hard_gate"))
    if _non_empty_text(hard_gate.get("state")) == "domain_owner_answer_recorded":
        owner_answer_kind = (
            _non_empty_text(hard_gate.get("owner_answer_kind"))
            or _non_empty_text(delta.get("latest_owner_answer_kind"))
            or _non_empty_text(delta.get("source_kind"))
        )
        if owner_answer_kind not in {"typed_blocker", "owner_receipt"}:
            return False
        return not _stage_kernel_has_explicit_next_owner_action(payload)
    if not _stage_kernel_has_manifest_backed_typed_blocker_answer(payload):
        return False
    return not _stage_kernel_has_explicit_next_owner_action(payload)


def _stage_kernel_has_explicit_next_owner_action(payload: Mapping[str, Any]) -> bool:
    candidates = (
        _mapping_copy(delta_next_action) if (delta_next_action := _current_owner_delta(payload).get("next_owner_action")) else {},
    )
    for candidate in candidates:
        if (
            _non_empty_text(candidate.get("next_owner"))
            or _non_empty_text(candidate.get("owner"))
            or _non_empty_text(candidate.get("work_unit_id"))
            or _non_empty_text(candidate.get("action_type"))
            or _text_items(candidate.get("allowed_actions"))
        ):
            return True
    return False


def _stage_kernel_has_manifest_backed_typed_blocker_answer(payload: Mapping[str, Any]) -> bool:
    stage_kernel = _mapping_copy(payload.get("stage_kernel_projection"))
    stage_run_kernel = _mapping_copy(stage_kernel.get("stage_run_kernel"))
    delta = _current_owner_delta(payload)
    return (
        _non_empty_text(stage_run_kernel.get("status")) == "TypedBlocked"
        and _non_empty_text(delta.get("source_kind")) == "typed_blocker"
        and _non_empty_text(delta.get("source_ref")) is not None
    )


def _is_stage_kernel_typed_blocker_followup(delta: Mapping[str, Any]) -> bool:
    if _non_empty_text(delta.get("source_kind")) == "typed_blocker":
        return True
    if _non_empty_text(delta.get("required_input")) == READINESS_ACTION:
        return True
    if _non_empty_text(delta.get("blocked_surface")) == PUBLICATION_HANDOFF_ACTION:
        return True
    if _non_empty_text(delta.get("latest_owner_answer_kind")) == "typed_blocker":
        return True
    return bool(_text_items(delta.get("typed_blocker_refs")))


def _mapping_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _dedupe_text(items: list[str | None]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = [
    "SURFACE_KIND",
    "build_current_executable_owner_action",
    "owner_action_next_step",
]
