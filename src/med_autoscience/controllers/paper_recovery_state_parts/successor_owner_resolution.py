from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.current_work_unit_parts.paper_recovery_successor import (
    paper_recovery_successor_action_ready as _paper_recovery_successor_action_ready,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
)
from .successor_owner_resolution_helpers import (
    _dedupe,
    _first_text,
    _mapping,
    _read_closeout_ref,
    _same_ref_path,
    _strip_ref_fragment,
    _text,
    _text_items,
)
from .typed_blocker_supersession import (
    current_action_supersedes_typed_blocker as _current_action_supersedes_typed_blocker,
)


def current_executable_owner_action(progress: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping(progress.get("current_executable_owner_action"))
    if direct:
        return direct
    return _mapping(_mapping(progress.get("progress_first_monitoring_summary")).get("current_executable_owner_action"))


def successor_owner_action_from_terminal_blocker(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
    blocker_reason: str | None,
) -> dict[str, Any] | None:
    if blocker_reason == "current_owner_route_missing":
        successor = _successor_owner_action_from_repair_progress_gate_replay(
            progress,
            typed_blocker=typed_blocker,
        )
        if successor is not None:
            return successor
    action = current_executable_owner_action(progress)
    if action and _current_action_supersedes_typed_blocker(
        action=action,
        blocker=typed_blocker,
        progress=progress,
    ):
        return successor_owner_action_from_current_action(action)
    if blocker_reason in {
        "ai_reviewer_record_stale_after_current_inputs",
        "ai_reviewer_record_stale_after_current_manuscript",
        "ai_reviewer_record_stale_after_unit_harmonized_rerun",
    }:
        successor = _successor_owner_action_from_current_ai_reviewer_record(
            progress,
            typed_blocker=typed_blocker,
        )
        if successor is not None:
            return successor
    if blocker_reason in {"publication_gate_replay_blocked", "paper_progress_stall_terminal"}:
        return _successor_owner_action_from_gate_followthrough(progress)
    if blocker_reason == "anti_loop_budget_exhausted" or _typed_blocker_is_current_anti_loop_successor_candidate(
        typed_blocker
    ):
        return _successor_owner_action_from_next_forced_delta_after_progress(
            progress,
            typed_blocker=typed_blocker,
        )
    return None


def successor_owner_action_from_current_action(action: Mapping[str, Any]) -> dict[str, Any]:
    action_type = _first_text(action.get("action_type"), *_text_items(action.get("allowed_actions")))
    owner = _first_text(action.get("next_owner"), action.get("owner"), action.get("request_owner"))
    work_unit_id = _first_text(action.get("work_unit_id"), action.get("next_work_unit"))
    fingerprint = _first_text(action.get("work_unit_fingerprint"), action.get("action_fingerprint"))
    source_ref = _first_text(action.get("source_ref"), *_text_items(action.get("acceptance_refs")))
    successor = {
        key: value
        for key, value in {
            "action_type": action_type,
            "owner": owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "source_surface": _first_text(action.get("source_surface"), action.get("source")),
            "source_ref": source_ref,
            "target_surface": _mapping(action.get("target_surface")),
            "owner_route_currentness_basis": _mapping(action.get("owner_route_currentness_basis")),
        }.items()
        if value not in (None, "", [], {})
    }
    action_fingerprint = _first_text(action.get("action_fingerprint"), fingerprint)
    if action_fingerprint is not None and action_fingerprint != fingerprint:
        successor["action_fingerprint"] = action_fingerprint
    source_eval_id = _first_text(
        action.get("source_eval_id"),
        _mapping(action.get("owner_route_currentness_basis")).get("source_eval_id"),
    )
    if source_eval_id is not None:
        successor["source_eval_id"] = source_eval_id
    required_delta_kind = _text(action.get("required_delta_kind"))
    if required_delta_kind is not None and _mapping(action.get("target_surface")):
        successor["required_delta_kind"] = required_delta_kind
    allowed_actions = _text_items(action.get("allowed_actions"))
    if allowed_actions:
        successor["allowed_actions"] = allowed_actions
    if action.get("owner_receipt_required") is True and _mapping(action.get("target_surface")):
        successor["owner_receipt_required"] = True
    return successor


def paper_recovery_successor_action_ready(action: Mapping[str, Any]) -> bool:
    return _paper_recovery_successor_action_ready(action)


def paper_recovery_successor_consumed_by_gate_followthrough(
    progress: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any] | None = None,
    current_action: Mapping[str, Any] | None = None,
) -> bool:
    action = _mapping(current_action)
    if not action:
        recovery_payload = _mapping(recovery) or _mapping(progress.get("paper_recovery_state"))
        action = _mapping(_mapping(recovery_payload.get("next_safe_action")).get("successor_owner_action"))
    if not action:
        return False
    source_surface = _first_text(
        action.get("source_surface"),
        _mapping(action.get("target_surface")).get("source_surface"),
        _mapping(action.get("paper_recovery_successor")).get("source_surface"),
    )
    if source_surface != "study_progress.next_forced_delta.owner_action":
        return False
    return _gate_replay_successor_already_consumed(
        progress,
        action_type=_text(action.get("action_type")),
        work_unit_id=_text(action.get("work_unit_id")),
        source_eval_id=_text(action.get("source_eval_id")),
        target_surface_ref=_first_text(
            _mapping(action.get("target_surface")).get("surface_ref"),
            action.get("source_ref"),
        ),
    )


def current_owner_successor_action(
    progress: Mapping[str, Any],
    *,
    current_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    action = _mapping(current_action) or current_executable_owner_action(progress)
    source = _text(action.get("source")) or _text(action.get("source_surface"))
    if source != "gate_clearing_batch_followthrough.actionable_current_work_unit":
        return None
    if not _gate_followthrough_has_consumed_repair_progress(progress, action=action):
        return None
    successor = successor_owner_action_from_current_action(action)
    if (
        _text(successor.get("action_type")) is None
        or _text(successor.get("owner")) is None
        or _text(successor.get("work_unit_id")) is None
        or _text(successor.get("work_unit_fingerprint")) is None
    ):
        return None
    return successor


def successor_owner_action_from_gate_followthrough(
    progress: Mapping[str, Any],
) -> dict[str, Any] | None:
    return _successor_owner_action_from_gate_followthrough(progress)


def successor_owner_action_from_domain_transition(
    progress: Mapping[str, Any],
    *,
    owner_receipt_ref: str | None = None,
) -> dict[str, Any] | None:
    transition = _mapping(progress.get("domain_transition"))
    decision_type = _text(transition.get("decision_type"))
    action_type = _text(transition.get("controller_action"))
    next_work_unit = _mapping(transition.get("next_work_unit"))
    work_unit_id = _first_text(
        next_work_unit.get("unit_id"),
        next_work_unit.get("work_unit_id"),
        transition.get("work_unit_id"),
        transition.get("next_work_unit"),
    )
    owner = _first_text(transition.get("owner"), transition.get("route_target"))
    if decision_type is None or action_type is None or work_unit_id is None or owner is None:
        return None
    if action_type not in {
        "request_opl_stage_attempt",
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
        "run_quality_repair_batch",
    }:
        return None
    fingerprint = _first_text(
        next_work_unit.get("work_unit_fingerprint"),
        next_work_unit.get("action_fingerprint"),
        transition.get("work_unit_fingerprint"),
        transition.get("action_fingerprint"),
    )
    if fingerprint is None:
        fingerprint = f"domain-transition::{decision_type}::{work_unit_id}"
    return {
        "action_type": action_type,
        "owner": owner,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "domain_transition_decision_type": decision_type,
        "domain_transition_controller_action": action_type,
        "source_surface": "domain_transition",
        "source_ref": owner_receipt_ref,
    }


def executable_action_is_gate_followthrough_successor(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    source = _text(current_action.get("source")) or _text(
        _mapping(current_work_unit.get("state")).get("source")
    )
    if source != "paper_recovery_state.next_safe_action.successor_owner_action":
        return False
    source_surface = _text(current_action.get("source_surface")) or _text(
        _mapping(_mapping(current_work_unit.get("required_output_contract")).get("target_surface")).get(
            "source_surface"
        )
    )
    if source_surface != "gate_clearing_batch_followthrough.actionable_current_work_unit":
        return False
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    currentness = _mapping(followthrough.get("work_unit_currentness"))
    if _text(currentness.get("current_actionability_status")) != "actionable":
        return False
    successor_work_unit = _text(followthrough.get("work_unit_id")) or _text(
        _mapping(followthrough.get("current_publication_work_unit")).get("unit_id")
    )
    if successor_work_unit is None or successor_work_unit != _text(current_work_unit.get("work_unit_id")):
        return False
    successor_fingerprint = _text(followthrough.get("work_unit_fingerprint")) or _text(
        currentness.get("current_work_unit_fingerprint")
    )
    current_fingerprint = _text(current_work_unit.get("work_unit_fingerprint")) or _text(
        current_work_unit.get("action_fingerprint")
    )
    if successor_fingerprint is not None and current_fingerprint is not None:
        return successor_fingerprint == current_fingerprint
    return True


def _gate_followthrough_has_consumed_repair_progress(
    progress: Mapping[str, Any],
    *,
    action: Mapping[str, Any],
) -> bool:
    repair = _mapping(progress.get("repair_progress_projection"))
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return False
    if repair.get("accepted_owner_receipt") is not True:
        return False
    if repair.get("gate_replay_done") is not True:
        return False
    action_work_unit = _text(action.get("work_unit_id"))
    repair_work_unit = _text(repair.get("work_unit_id"))
    if action_work_unit is None or repair_work_unit != action_work_unit:
        return False
    action_eval = _text(action.get("source_eval_id"))
    repair_eval = _text(repair.get("source_eval_id"))
    if action_eval is not None and repair_eval is not None and action_eval != repair_eval:
        return False
    action_fingerprint = _first_text(action.get("work_unit_fingerprint"), action.get("action_fingerprint"))
    repair_fingerprint = _first_text(
        repair.get("work_unit_fingerprint"),
        repair.get("action_fingerprint"),
        repair.get("source_fingerprint"),
    )
    if action_fingerprint is None or repair_fingerprint != action_fingerprint:
        return False
    return bool(
        _text(repair.get("repair_execution_evidence_ref"))
        or _text(repair.get("owner_receipt_ref"))
        or _text_items(repair.get("gate_replay_refs"))
    )


def _successor_owner_action_from_repair_progress_gate_replay(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _text(typed_blocker.get("action_type")) != "run_gate_clearing_batch":
        return None
    if _text(typed_blocker.get("work_unit_id")) != "publication_gate_replay":
        return None
    repair = _mapping(progress.get("repair_progress_projection"))
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return None
    if repair.get("paper_delta_observed") is not True:
        return None
    if repair.get("accepted_owner_receipt") is not True:
        return None
    if repair.get("gate_replay_done") is not True:
        return None
    fingerprint = _text(repair.get("source_fingerprint"))
    if fingerprint is None or fingerprint != _text(typed_blocker.get("work_unit_fingerprint")):
        return None
    blocker_eval = _typed_blocker_source_eval_id(typed_blocker)
    repair_eval = _text(repair.get("source_eval_id"))
    if blocker_eval is not None and repair_eval is not None and blocker_eval != repair_eval:
        return None
    source_ref = (
        _text(repair.get("repair_execution_evidence_ref"))
        or _text(repair.get("owner_receipt_ref"))
        or _first_text(*_text_items(repair.get("gate_replay_refs")))
    )
    if source_ref is None:
        return None
    return {
        "action_type": "run_gate_clearing_batch",
        "owner": "gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": fingerprint,
        "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "source_ref": source_ref,
    }


def _successor_owner_action_from_current_ai_reviewer_record(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
) -> dict[str, Any] | None:
    lifecycle = _mapping(progress.get("ai_reviewer_request_lifecycle"))
    if _text(lifecycle.get("state")) != "assessment_written":
        return None
    if lifecycle.get("assessment_written") is not True:
        return None
    consumption = _mapping(lifecycle.get("owner_output_consumption"))
    if _text(consumption.get("status")) != "consumed":
        return None
    record_ref = _first_text(
        consumption.get("record_ref"),
        lifecycle.get("publication_eval_record_ref"),
        lifecycle.get("assessment_ref"),
    )
    if record_ref is None:
        return None
    publication_eval = _mapping(progress.get("publication_eval"))
    recommended_action = _current_ai_reviewer_gate_replay_action(publication_eval)
    if recommended_action is None:
        return None
    next_work_unit = _mapping(recommended_action.get("next_work_unit"))
    work_unit_id = _first_text(
        next_work_unit.get("unit_id"),
        recommended_action.get("work_unit_id"),
        recommended_action.get("next_work_unit"),
    )
    if work_unit_id not in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return None
    source_eval_id = _first_text(
        consumption.get("eval_id"),
        publication_eval.get("eval_id"),
        _typed_blocker_source_eval_id(typed_blocker),
    )
    target_surface_ref = "artifacts/controller/gate_clearing_batch/latest.json"
    if _gate_replay_successor_already_consumed(
        progress,
        action_type="run_gate_clearing_batch",
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
        target_surface_ref=target_surface_ref,
    ):
        return None
    fingerprint = _first_text(
        recommended_action.get("work_unit_fingerprint"),
        f"domain-transition::route_back_same_line::{work_unit_id}",
    )
    route_target = _first_text(
        recommended_action.get("route_target"),
        next_work_unit.get("lane"),
        "publication_gate",
    )
    return {
        "action_type": "run_gate_clearing_batch",
        "owner": "gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "domain_transition_decision_type": "route_back_same_line",
        "domain_transition_controller_action": "run_gate_clearing_batch",
        "route_target": route_target,
        "source_surface": "ai_reviewer_request_lifecycle.owner_output_consumption",
        "source_ref": record_ref,
        "source_eval_id": source_eval_id,
        "target_surface": {"surface_ref": target_surface_ref},
        "owner_route_currentness_basis": {
            "source": "ai_reviewer_request_lifecycle.owner_output_consumption",
            "source_eval_id": source_eval_id,
            "record_ref": record_ref,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
    }


def _current_ai_reviewer_gate_replay_action(publication_eval: Mapping[str, Any]) -> dict[str, Any] | None:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer":
        return None
    if provenance.get("ai_reviewer_required") is not False:
        return None
    actions = publication_eval.get("recommended_actions")
    if not isinstance(actions, list):
        return None
    for item in actions:
        action = _mapping(item)
        if not action:
            continue
        if action.get("requires_controller_decision") is not True:
            continue
        if _text(action.get("action_type")) != "route_back_same_line":
            continue
        next_work_unit = _mapping(action.get("next_work_unit"))
        work_unit_id = _first_text(
            next_work_unit.get("unit_id"),
            action.get("work_unit_id"),
            action.get("next_work_unit"),
        )
        if work_unit_id in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
            return action
    return None


def successor_owner_gate_from_terminal_blocker(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
    blocker_reason: str | None,
    owner: str,
) -> dict[str, Any] | None:
    if not _terminal_owner_answer_present(typed_blocker):
        return None
    if blocker_reason != "anti_loop_budget_exhausted":
        return None
    obligation = {
        "action_type": _text(typed_blocker.get("action_type")),
        "work_unit_id": _text(typed_blocker.get("work_unit_id")),
        "work_unit_fingerprint": _text(typed_blocker.get("work_unit_fingerprint")),
    }
    closeout = _matching_terminal_closeout(progress, obligation=obligation)
    closeout_from_ref = _matching_terminal_closeout_from_typed_blocker_refs(
        progress,
        typed_blocker=typed_blocker,
        obligation=obligation,
    )
    if _next_forced_delta_from_closeout(closeout_from_ref):
        closeout = closeout_from_ref
    next_forced_delta = _next_forced_delta_from_closeout(closeout) or _next_forced_delta_from_progress(progress)
    required_input = _first_text(
        _mapping(next_forced_delta).get("required_delta_kind"),
        _mapping(next_forced_delta).get("required_delta"),
        _mapping(next_forced_delta).get("reason"),
        _text(typed_blocker.get("required_owner_action")),
    )
    if required_input is None:
        required_input = "successor_work_unit_or_owner_gate_after_terminal_stop_loss"
    return {
        "owner": owner,
        "required_input": required_input,
        "work_unit_id": _text(typed_blocker.get("work_unit_id")),
        "work_unit_fingerprint": _text(typed_blocker.get("work_unit_fingerprint")),
        "source_surface": "terminal_typed_blocker.next_forced_delta",
        "evidence_refs": _dedupe(
            [
                *_text_items(typed_blocker.get("closeout_refs")),
                _text(typed_blocker.get("typed_blocker_ref")),
                _text(typed_blocker.get("latest_owner_answer_ref")),
                *_closeout_refs(closeout or {}),
            ]
        ),
    }


def _successor_owner_action_from_gate_followthrough(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    if not followthrough:
        return None
    currentness = _mapping(followthrough.get("work_unit_currentness"))
    if _text(followthrough.get("gate_replay_status")) != "blocked":
        return None
    if _text(currentness.get("current_actionability_status")) != "actionable":
        return None
    if currentness.get("lacks_specific_blocker_object") is True:
        return None
    work_unit = (
        _mapping(followthrough.get("current_publication_work_unit"))
        or _mapping(followthrough.get("explicit_publication_work_unit"))
        or _mapping(followthrough.get("selected_publication_work_unit"))
    )
    work_unit_id = _first_text(
        followthrough.get("work_unit_id"),
        currentness.get("current_publication_work_unit_id"),
        currentness.get("explicit_publication_work_unit_id"),
        currentness.get("selected_publication_work_unit_id"),
        work_unit.get("unit_id"),
        work_unit.get("work_unit_id"),
    )
    fingerprint = _first_text(
        followthrough.get("work_unit_fingerprint"),
        currentness.get("current_work_unit_fingerprint"),
        currentness.get("explicit_work_unit_fingerprint"),
    )
    lane = _first_text(work_unit.get("lane"), followthrough.get("lane"))
    if work_unit_id is None or fingerprint is None or lane != "write":
        return None
    return {
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "source_ref": _text(followthrough.get("latest_record_path")),
    }


def _successor_owner_action_from_next_forced_delta_after_progress(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
) -> dict[str, Any] | None:
    next_delta = _next_forced_delta_from_progress(progress)
    owner_action = _mapping(next_delta.get("owner_action"))
    repair = _mapping(progress.get("repair_progress_projection"))
    if not _repair_progress_proves_safe_successor_delta(repair):
        return None
    if not _owner_action_has_executable_identity(owner_action, next_delta=next_delta):
        return _successor_owner_action_from_repair_progress_after_anti_loop(
            progress,
            repair=repair,
            typed_blocker=typed_blocker,
        )
    if _text(next_delta.get("reason")) != "paper_progress_delta_observed":
        return None
    if _text(next_delta.get("required_delta_kind")) != "review_current_paper_delta":
        return None
    action_type = _first_text(owner_action.get("action_type"), *_text_items(owner_action.get("allowed_actions")))
    owner = _first_text(owner_action.get("next_owner"), owner_action.get("owner"))
    work_unit_id = _first_text(
        owner_action.get("work_unit_id"),
        owner_action.get("next_work_unit"),
        next_delta.get("work_unit_id"),
    )
    blocker_work_unit = _text(typed_blocker.get("work_unit_id"))
    if action_type != "run_gate_clearing_batch":
        return None
    if work_unit_id is None or work_unit_id != blocker_work_unit:
        return None
    if work_unit_id != _text(next_delta.get("work_unit_id")):
        return None
    if owner is None:
        return None
    target_surface = _mapping(next_delta.get("target_surface"))
    source_eval_id = _first_text(next_delta.get("eval_id"), next_delta.get("source_eval_id"))
    if _gate_replay_successor_already_consumed(
        progress,
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
        target_surface_ref=_text(target_surface.get("surface_ref")),
    ):
        return None
    fingerprint = control_identity.stable_route_currentness_fingerprint(
        study_id=_text(progress.get("study_id")),
        source="study_progress.next_forced_delta.owner_action",
        work_unit_id=work_unit_id,
        action_type=action_type,
        next_owner=owner,
        source_eval_id=source_eval_id,
        target_surface_ref=_text(target_surface.get("surface_ref")),
        required_delta_kind=_text(next_delta.get("required_delta_kind")),
    )
    if fingerprint is None:
        return None
    source_ref = (
        _text(repair.get("repair_execution_evidence_ref"))
        or _text(repair.get("owner_receipt_ref"))
        or _first_text(*_text_items(repair.get("gate_replay_refs")))
    )
    return {
        "action_type": action_type,
        "owner": owner,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_surface": "study_progress.next_forced_delta.owner_action",
        "source_eval_id": source_eval_id,
        "source_ref": source_ref,
        "owner_route_currentness_basis": {
            "source": "study_progress.next_forced_delta.owner_action",
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
    }


def _successor_owner_action_from_repair_progress_after_anti_loop(
    progress: Mapping[str, Any],
    *,
    repair: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not _typed_blocker_is_current_anti_loop_successor_candidate(typed_blocker):
        return None
    action_type = _text(typed_blocker.get("action_type"))
    work_unit_id = _text(typed_blocker.get("work_unit_id"))
    owner = _first_text(
        typed_blocker.get("required_next_owner"),
        typed_blocker.get("next_owner"),
        typed_blocker.get("owner"),
    )
    if action_type != "run_gate_clearing_batch" or work_unit_id is None or owner is None:
        return None
    source_eval_id = _first_text(repair.get("source_eval_id"), _typed_blocker_source_eval_id(typed_blocker))
    blocker_eval_id = _typed_blocker_source_eval_id(typed_blocker)
    repair_eval_id = _text(repair.get("source_eval_id"))
    if blocker_eval_id is not None and repair_eval_id is not None and blocker_eval_id != repair_eval_id:
        return None
    source_ref = _repair_progress_successor_source_ref(repair)
    if source_ref is None:
        return None
    if _gate_replay_successor_already_consumed(
        progress,
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
        target_surface_ref="artifacts/controller/gate_clearing_batch/latest.json",
    ):
        return None
    fingerprint = control_identity.stable_route_currentness_fingerprint(
        study_id=_text(progress.get("study_id")),
        source="repair_progress_projection.mas_owner_repair_execution_evidence",
        work_unit_id=work_unit_id,
        action_type=action_type,
        next_owner=owner,
        source_eval_id=source_eval_id,
        target_surface_ref="artifacts/controller/gate_clearing_batch/latest.json",
        required_delta_kind="review_current_paper_delta",
    )
    if fingerprint is None:
        return None
    return {
        "action_type": action_type,
        "owner": owner,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "source_eval_id": source_eval_id,
        "source_ref": source_ref,
        "owner_route_currentness_basis": {
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
    }


def _repair_progress_proves_safe_successor_delta(repair: Mapping[str, Any]) -> bool:
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return False
    if repair.get("paper_delta_observed") is not True:
        return False
    if not (
        repair.get("accepted_owner_receipt") is True
        or (
            repair.get("progress_delta_candidate") is True
            and repair.get("gate_replay_done") is True
        )
    ):
        return False
    if repair.get("gate_replay_done") is not True:
        return False
    return _repair_progress_successor_source_ref(repair) is not None


def _typed_blocker_is_current_anti_loop_successor_candidate(
    typed_blocker: Mapping[str, Any],
) -> bool:
    blocker_markers = {
        _text(typed_blocker.get("reason")),
        _text(typed_blocker.get("blocker_id")),
        _text(typed_blocker.get("blocker_kind")),
        _text(typed_blocker.get("blocked_reason")),
        _text(typed_blocker.get("blocker_type")),
    }
    if not (
        "anti_loop_budget_exhausted" in blocker_markers
        or "repeat_suppressed_after_opl_execution_authorization_required" in blocker_markers
    ):
        return False
    if _text(typed_blocker.get("action_type")) != "run_gate_clearing_batch":
        return False
    return _text(typed_blocker.get("work_unit_id")) is not None


def _repair_progress_successor_source_ref(repair: Mapping[str, Any]) -> str | None:
    return (
        _text(repair.get("repair_execution_evidence_ref"))
        or _text(repair.get("owner_receipt_ref"))
        or _first_text(*_text_items(repair.get("gate_replay_refs")))
    )


def _owner_action_has_executable_identity(
    owner_action: Mapping[str, Any],
    *,
    next_delta: Mapping[str, Any],
) -> bool:
    action_type = _first_text(owner_action.get("action_type"), *_text_items(owner_action.get("allowed_actions")))
    owner = _first_text(owner_action.get("next_owner"), owner_action.get("owner"))
    work_unit_id = _first_text(
        owner_action.get("work_unit_id"),
        owner_action.get("next_work_unit"),
        next_delta.get("work_unit_id"),
    )
    return action_type is not None and owner is not None and work_unit_id is not None


def _gate_replay_successor_already_consumed(
    progress: Mapping[str, Any],
    *,
    action_type: str | None,
    work_unit_id: str | None,
    source_eval_id: str | None,
    target_surface_ref: str | None,
) -> bool:
    if action_type != "run_gate_clearing_batch" or work_unit_id is None:
        return False
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    if not followthrough:
        return False
    if _text(followthrough.get("status")) != "executed":
        return False
    if _text(followthrough.get("gate_replay_status")) != "blocked":
        return False
    followthrough_eval = _text(followthrough.get("source_eval_id"))
    if source_eval_id is not None and followthrough_eval != source_eval_id:
        return False
    followthrough_work_unit = _first_text(
        followthrough.get("work_unit_id"),
        _mapping(followthrough.get("explicit_publication_work_unit")).get("unit_id"),
        _mapping(followthrough.get("current_publication_work_unit")).get("unit_id"),
    )
    if followthrough_work_unit is not None and followthrough_work_unit != work_unit_id:
        return False
    latest_record_path = _text(followthrough.get("latest_record_path"))
    if target_surface_ref is not None and latest_record_path is not None:
        if not _same_ref_path(latest_record_path, target_surface_ref):
            return False
    return True


def _matching_terminal_closeout(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    for key in (
        "terminal_closeout_precedence_evidence",
        "terminal_closeout",
        "accepted_closeout_evidence",
    ):
        value = progress.get(key)
        if isinstance(value, list):
            for item in value:
                candidate = _mapping(item)
                if candidate and _closeout_matches_obligation(candidate, obligation=obligation):
                    return dict(candidate)
        else:
            candidate = _mapping(value)
            if candidate and _closeout_matches_obligation(candidate, obligation=obligation):
                return dict(candidate)
    return None


def _matching_terminal_closeout_from_typed_blocker_refs(
    progress: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    for ref in _terminal_closeout_ref_candidates(typed_blocker):
        closeout = _read_closeout_ref(progress, ref)
        if closeout and _closeout_matches_obligation(closeout, obligation=obligation):
            closeout.setdefault("source_path", _strip_ref_fragment(ref))
            return closeout
    return None


def _closeout_matches_obligation(
    closeout: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    action_type = _text(obligation.get("action_type"))
    work_unit_id = _text(obligation.get("work_unit_id"))
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if action_type and _text(closeout.get("action_type")) not in {None, action_type}:
        return False
    if work_unit_id and _text(closeout.get("work_unit_id")) not in {None, work_unit_id}:
        return False
    if fingerprint:
        closeout_fingerprints = {
            value
            for value in (
                _text(closeout.get("work_unit_fingerprint")),
                _text(closeout.get("action_fingerprint")),
            )
            if value is not None
        }
        if closeout_fingerprints and fingerprint not in closeout_fingerprints:
            return False
    return bool(
        _text(closeout.get("stage_attempt_id"))
        or _text(closeout.get("active_stage_attempt_id"))
        or _closeout_refs(closeout)
    )


def _closeout_refs(closeout: Mapping[str, Any]) -> list[str]:
    refs = [
        _text(closeout.get("closeout_ref")),
        _text(closeout.get("source_path")),
        *_text_items(closeout.get("closeout_refs")),
    ]
    return _dedupe(refs)


def _terminal_owner_answer_present(typed_blocker: Mapping[str, Any]) -> bool:
    return any(
        _text(value) is not None
        for value in (
            typed_blocker.get("latest_owner_answer_ref"),
            typed_blocker.get("typed_blocker_ref"),
            typed_blocker.get("source_ref"),
        )
    )


def _terminal_closeout_ref_candidates(typed_blocker: Mapping[str, Any]) -> list[str]:
    return _dedupe(
        [
            *_text_items(typed_blocker.get("closeout_refs")),
            _text(typed_blocker.get("typed_blocker_ref")),
            _text(typed_blocker.get("latest_owner_answer_ref")),
            _text(typed_blocker.get("source_ref")),
        ]
    )


def _typed_blocker_source_eval_id(typed_blocker: Mapping[str, Any]) -> str | None:
    return _first_text(
        typed_blocker.get("source_eval_id"),
        _mapping(typed_blocker.get("currentness_basis")).get("source_eval_id"),
        _mapping(typed_blocker.get("owner_route_currentness_basis")).get("source_eval_id"),
    )


def _next_forced_delta_from_closeout(closeout: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(closeout)
    if not payload:
        return {}
    paper_log = _mapping(payload.get("paper_stage_log"))
    return _mapping(payload.get("next_forced_delta")) or _mapping(paper_log.get("next_forced_delta"))


def _next_forced_delta_from_progress(progress: Mapping[str, Any]) -> dict[str, Any]:
    for candidate in (
        progress.get("next_forced_delta"),
        _mapping(progress.get("progress_first_monitoring_summary")).get("next_forced_delta"),
        _mapping(progress.get("progress_first_monitoring_summary")).get("latest_terminal_stage"),
        _mapping(progress.get("progress_first_monitoring_summary")).get("latest_terminal_stage_log"),
    ):
        payload = _mapping(candidate)
        if not payload:
            continue
        next_delta = _mapping(payload.get("next_forced_delta")) or payload
        if next_delta:
            return next_delta
    return {}


__all__ = [
    "current_executable_owner_action",
    "current_owner_successor_action",
    "executable_action_is_gate_followthrough_successor",
    "paper_recovery_successor_action_ready",
    "paper_recovery_successor_consumed_by_gate_followthrough",
    "successor_owner_action_from_domain_transition",
    "successor_owner_action_from_current_action",
    "successor_owner_action_from_terminal_blocker",
    "successor_owner_gate_from_terminal_blocker",
]
