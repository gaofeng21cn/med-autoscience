from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.paper_recovery_state.state_diagnostics import (
    current_work_unit_status as _current_work_unit_status,
    first_text as _first_text,
    mapping as _mapping,
    text as _text,
    text_items as _text_items,
)
from med_autoscience.controllers.paper_recovery_state.successor_owner_resolution import (
    executable_action_is_gate_followthrough_successor as _executable_action_is_gate_followthrough_successor,
    successor_owner_action_from_gate_followthrough as _successor_owner_action_from_gate_followthrough,
)
from med_autoscience.controllers.paper_recovery_state.typed_blocker_payload import (
    current_typed_blocker as _current_typed_blocker,
    typed_blocker_reason as _typed_blocker_reason,
)


def same_work_unit_owner_receipt(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    current_status = _current_work_unit_status(current_work_unit)
    typed_blocker = _current_typed_blocker(current_work_unit)
    if current_status == "typed_blocker" and _typed_blocker_reason(typed_blocker) not in {
        "no_selected_dispatch_for_authorized_stage_packet",
        "stage_packet_not_current_selected_dispatch",
    }:
        return None
    if current_status not in {"executable_owner_action", "typed_blocker"}:
        return None
    if _executable_action_is_gate_followthrough_successor(
        progress,
        current_work_unit=current_work_unit,
        current_action=current_action,
    ) and not _gate_followthrough_successor_receipt_matches_current_action(
        progress,
        current_work_unit=current_work_unit,
        current_action=current_action,
    ):
        return None
    repair = _mapping(progress.get("repair_progress_projection"))
    if not repair:
        return None
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return None
    if repair.get("paper_delta_observed") is not True:
        return None
    if repair.get("accepted_owner_receipt") is not True:
        return None
    owner_receipt_ref = _text(repair.get("owner_receipt_ref"))
    if owner_receipt_ref is None:
        return None
    if _same_work_unit_owner_receipt_matches_obligation(
        repair,
        current_work_unit=current_work_unit,
        current_action=current_action,
        obligation=obligation,
    ):
        if _route_back_successor_consumes_prior_owner_receipt(
            progress,
            repair=repair,
            current_work_unit=current_work_unit,
            current_action=current_action,
        ):
            return None
        return {
            "condition": "same_work_unit_owner_receipt_recorded",
            "owner_receipt_ref": owner_receipt_ref,
        }
    if _repair_progress_followup_owner_receipt_matches_obligation(
        repair,
        current_work_unit=current_work_unit,
        current_action=current_action,
        obligation=obligation,
    ):
        followup_receipt_ref = _repair_progress_followup_owner_receipt_ref(repair)
        if followup_receipt_ref is None:
            return None
        return {
            "condition": "repair_progress_followup_owner_receipt_recorded",
            "owner_receipt_ref": followup_receipt_ref,
        }
    return None


def repair_progress_owner_receipt_superseding_terminal_stop_loss(
    progress: Mapping[str, Any],
    *,
    closeout: Mapping[str, Any],
) -> dict[str, Any] | None:
    typed_blocker = _mapping(closeout.get("typed_blocker"))
    blocker_reason = _typed_blocker_reason({**typed_blocker, **_mapping(closeout)})
    if blocker_reason not in {
        "anti_loop_budget_exhausted",
        "repeat_suppressed_after_opl_execution_authorization_required",
    }:
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
    if repair.get("ai_reviewer_recheck_done") is not True:
        return None
    owner_receipt_ref = _text(repair.get("owner_receipt_ref"))
    if owner_receipt_ref is None:
        return None
    if _text(repair.get("work_unit_id")) is None:
        return None
    if _text(closeout.get("stage_attempt_id")) is None and not _closeout_refs(closeout):
        return None
    if _repair_progress_receipt_already_consumed_by_same_gate_replay(
        progress,
        repair=repair,
        closeout=closeout,
    ):
        return None
    return {
        "condition": "repair_progress_owner_receipt_supersedes_terminal_stop_loss",
        "owner_receipt_ref": owner_receipt_ref,
    }


def owner_receipt_recorded_current_work_unit(
    current_work_unit: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _current_work_unit_status(current_work_unit) != "owner_receipt_recorded":
        return None
    owner_receipt_ref = _first_text(
        _mapping(current_work_unit.get("state")).get("owner_receipt_ref"),
        _mapping(current_work_unit.get("required_output_contract")).get("owner_receipt_ref"),
        *_text_items(current_work_unit.get("acceptance_refs")),
    )
    if owner_receipt_ref is None:
        return None
    return {
        "condition": "current_work_unit_owner_receipt_recorded",
        "owner_receipt_ref": owner_receipt_ref,
        "action_type": _text(current_work_unit.get("action_type")) or _text(obligation.get("action_type")),
    }


def successor_owner_action_from_consumed_owner_receipt(
    progress: Mapping[str, Any],
    *,
    owner_receipt: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not _owner_receipt_has_consumed_successor(progress, owner_receipt=owner_receipt):
        return None
    successor = _successor_owner_action_from_gate_followthrough(progress)
    if successor is None:
        return None
    if _owner_receipt_has_consumed_gate_followthrough(progress, owner_receipt=owner_receipt):
        return successor
    transition = _mapping(progress.get("domain_transition"))
    next_work_unit = _first_text(
        _mapping(transition.get("next_work_unit")).get("unit_id"),
        _mapping(transition.get("next_work_unit")).get("work_unit_id"),
    )
    successor_work_unit = _text(successor.get("work_unit_id"))
    if next_work_unit is None or successor_work_unit != next_work_unit:
        return None
    transition_owner = _first_text(transition.get("owner"), transition.get("route_target"))
    successor_owner = _first_text(successor.get("owner"), successor.get("next_owner"))
    if transition_owner is not None and successor_owner is not None and successor_owner != transition_owner:
        return None
    return successor


def _repair_progress_receipt_already_consumed_by_same_gate_replay(
    progress: Mapping[str, Any],
    *,
    repair: Mapping[str, Any],
    closeout: Mapping[str, Any],
) -> bool:
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    if _text(followthrough.get("status")) != "executed":
        return False
    if _text(followthrough.get("gate_replay_status")) != "blocked":
        return False
    currentness = _mapping(followthrough.get("work_unit_currentness"))
    if _text(currentness.get("current_actionability_status")) == "actionable":
        current_work_unit = _first_text(
            currentness.get("current_publication_work_unit_id"),
            _mapping(followthrough.get("current_publication_work_unit")).get("unit_id"),
        )
        closeout_work_unit = _text(closeout.get("work_unit_id"))
        if current_work_unit is not None and current_work_unit != closeout_work_unit:
            return False
    followthrough_work_unit = _text(followthrough.get("work_unit_id"))
    closeout_work_unit = _text(closeout.get("work_unit_id"))
    if closeout_work_unit is not None and followthrough_work_unit not in {None, closeout_work_unit}:
        return False
    latest_record = _text(followthrough.get("latest_record_path"))
    if latest_record is None:
        return True
    return latest_record in set(_text_items(repair.get("gate_replay_refs")))


def _owner_receipt_has_consumed_successor(
    progress: Mapping[str, Any],
    *,
    owner_receipt: Mapping[str, Any],
) -> bool:
    return _owner_receipt_has_consumed_routeback(
        progress,
        owner_receipt=owner_receipt,
    ) or _owner_receipt_has_consumed_gate_followthrough(
        progress,
        owner_receipt=owner_receipt,
    )


def _owner_receipt_has_consumed_routeback(
    progress: Mapping[str, Any],
    *,
    owner_receipt: Mapping[str, Any],
) -> bool:
    if _text(owner_receipt.get("owner_receipt_ref")) is None:
        return False
    transition = _mapping(progress.get("domain_transition"))
    if _text(transition.get("decision_type")) != "route_back_same_line":
        return False
    if _text(transition.get("controller_action")) != "request_opl_stage_attempt":
        return False
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    return _text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"


def _owner_receipt_has_consumed_gate_followthrough(
    progress: Mapping[str, Any],
    *,
    owner_receipt: Mapping[str, Any],
) -> bool:
    if _text(owner_receipt.get("owner_receipt_ref")) is None:
        return False
    current_work_unit = _mapping(progress.get("current_work_unit"))
    if _text(current_work_unit.get("action_type")) != "run_gate_clearing_batch":
        return False
    if _text(current_work_unit.get("work_unit_id")) != "publication_gate_replay":
        return False
    contract = _mapping(current_work_unit.get("required_output_contract"))
    if contract.get("owner_receipt_consumed") is not True:
        return False
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    if _text(followthrough.get("status")) != "executed":
        return False
    if _text(followthrough.get("gate_replay_status")) != "blocked":
        return False
    currentness = _mapping(followthrough.get("work_unit_currentness"))
    if _text(currentness.get("current_actionability_status")) != "actionable":
        return False
    if currentness.get("lacks_specific_blocker_object") is True:
        return False
    if _text(followthrough.get("latest_record_path")) != _text(owner_receipt.get("owner_receipt_ref")):
        return False
    successor_work_unit = _first_text(
        followthrough.get("work_unit_id"),
        currentness.get("current_publication_work_unit_id"),
        currentness.get("explicit_publication_work_unit_id"),
        _mapping(followthrough.get("current_publication_work_unit")).get("unit_id"),
    )
    if successor_work_unit in {None, "publication_gate_replay"}:
        return False
    successor_fingerprint = _first_text(
        followthrough.get("work_unit_fingerprint"),
        currentness.get("current_work_unit_fingerprint"),
        currentness.get("explicit_work_unit_fingerprint"),
    )
    return successor_fingerprint is not None


def _same_work_unit_owner_receipt_matches_obligation(
    repair: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    obligation: Mapping[str, Any],
) -> bool:
    obligation_action_type = _text(obligation.get("action_type"))
    if obligation_action_type and _text(current_work_unit.get("action_type")) != obligation_action_type:
        return False
    obligation_work_unit = _text(obligation.get("work_unit_id"))
    repair_work_unit = _text(repair.get("work_unit_id"))
    if obligation_work_unit is None or repair_work_unit != obligation_work_unit:
        return False
    obligation_fingerprint = _text(obligation.get("work_unit_fingerprint"))
    repair_fingerprint = _first_text(
        repair.get("work_unit_fingerprint"),
        repair.get("action_fingerprint"),
        repair.get("source_fingerprint"),
    )
    if obligation_fingerprint is not None and repair_fingerprint != obligation_fingerprint:
        return False
    action_eval = _text(current_action.get("source_eval_id"))
    repair_eval = _text(repair.get("source_eval_id"))
    if action_eval is not None and repair_eval is not None and action_eval != repair_eval:
        return False
    return True


def _gate_followthrough_successor_receipt_matches_current_action(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    repair = _mapping(progress.get("repair_progress_projection"))
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return False
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    if _text(followthrough.get("status")) != "executed":
        return False
    currentness = _mapping(followthrough.get("work_unit_currentness"))
    if _text(currentness.get("current_actionability_status")) != "actionable":
        return False
    if currentness.get("lacks_specific_blocker_object") is True:
        return False
    repair_work_unit = _text(repair.get("work_unit_id"))
    current_work_unit_id = _text(current_work_unit.get("work_unit_id"))
    action_work_unit_id = _text(current_action.get("work_unit_id"))
    followthrough_work_unit = _first_text(
        followthrough.get("work_unit_id"),
        currentness.get("current_publication_work_unit_id"),
        _mapping(followthrough.get("current_publication_work_unit")).get("unit_id"),
    )
    if (
        repair_work_unit is None
        or current_work_unit_id != repair_work_unit
        or action_work_unit_id != repair_work_unit
        or followthrough_work_unit != repair_work_unit
    ):
        return False
    current_fingerprint = _first_text(
        current_work_unit.get("work_unit_fingerprint"),
        current_work_unit.get("action_fingerprint"),
        current_action.get("work_unit_fingerprint"),
        current_action.get("action_fingerprint"),
    )
    followthrough_fingerprint = _first_text(
        followthrough.get("work_unit_fingerprint"),
        currentness.get("current_work_unit_fingerprint"),
        currentness.get("explicit_work_unit_fingerprint"),
    )
    if current_fingerprint is None or followthrough_fingerprint != current_fingerprint:
        return False
    repair_fingerprint = _first_text(
        repair.get("work_unit_fingerprint"),
        repair.get("action_fingerprint"),
        repair.get("source_fingerprint"),
    )
    if repair_fingerprint is None or repair_fingerprint != current_fingerprint:
        return False
    repair_eval = _text(repair.get("source_eval_id"))
    action_eval = _text(current_action.get("source_eval_id"))
    followthrough_eval = _text(followthrough.get("source_eval_id"))
    if action_eval is None or followthrough_eval is None:
        return False
    if repair_eval is not None and repair_eval != action_eval:
        return False
    if repair_eval is not None and repair_eval != followthrough_eval:
        return False
    return True


def _route_back_successor_consumes_prior_owner_receipt(
    progress: Mapping[str, Any],
    *,
    repair: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    transition = _mapping(progress.get("domain_transition"))
    if _text(transition.get("decision_type")) != "route_back_same_line":
        return False
    if _text(transition.get("owner")) not in {None, "write", "analysis-campaign", "finalize"}:
        return False
    controller_action = _text(transition.get("controller_action"))
    if controller_action not in {None, "request_opl_stage_attempt"}:
        return False
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if _text(completion.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return False
    if _text(current_action.get("action_type")) != "run_quality_repair_batch":
        return False
    next_work_unit = _first_text(
        _mapping(transition.get("next_work_unit")).get("unit_id"),
        _mapping(transition.get("next_work_unit")).get("work_unit_id"),
    )
    action_work_unit = _text(current_action.get("work_unit_id"))
    current_work_unit_id = _text(current_work_unit.get("work_unit_id"))
    repair_work_unit = _text(repair.get("work_unit_id"))
    if (
        next_work_unit is None
        or action_work_unit != next_work_unit
        or current_work_unit_id != next_work_unit
        or repair_work_unit != next_work_unit
    ):
        return False
    action_owner = _first_text(current_action.get("next_owner"), current_action.get("owner"))
    transition_owner = _first_text(transition.get("owner"), transition.get("route_target"))
    if action_owner is not None and transition_owner is not None and action_owner != transition_owner:
        return False
    action_fingerprint = _first_text(
        current_action.get("work_unit_fingerprint"),
        current_action.get("action_fingerprint"),
        current_work_unit.get("work_unit_fingerprint"),
        current_work_unit.get("action_fingerprint"),
    )
    repair_fingerprint = _first_text(
        repair.get("work_unit_fingerprint"),
        repair.get("action_fingerprint"),
        repair.get("source_fingerprint"),
    )
    if action_fingerprint is None or repair_fingerprint != action_fingerprint:
        return False
    action_eval = _text(current_action.get("source_eval_id"))
    repair_eval = _text(repair.get("source_eval_id"))
    if action_eval is not None and repair_eval is not None and action_eval != repair_eval:
        return False
    return True


def _repair_progress_followup_owner_receipt_matches_obligation(
    repair: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    obligation: Mapping[str, Any],
) -> bool:
    repair_precedence = _mapping(current_action.get("repair_progress_precedence"))
    if not repair_precedence:
        return False
    obligation_action_type = _text(obligation.get("action_type"))
    if obligation_action_type and _text(current_work_unit.get("action_type")) != obligation_action_type:
        return False
    if obligation_action_type and _text(current_action.get("action_type")) != obligation_action_type:
        return False
    obligation_work_unit = _text(obligation.get("work_unit_id"))
    if obligation_work_unit and _text(current_work_unit.get("work_unit_id")) != obligation_work_unit:
        return False
    if obligation_work_unit and _text(current_action.get("work_unit_id")) != obligation_work_unit:
        return False
    source_work_unit = _text(repair_precedence.get("source_work_unit_id"))
    if source_work_unit is None or source_work_unit != _text(repair.get("work_unit_id")):
        return False
    source_fingerprint = _first_text(
        repair_precedence.get("work_unit_fingerprint"),
        repair_precedence.get("action_fingerprint"),
        repair_precedence.get("source_fingerprint"),
    )
    repair_fingerprint = _first_text(
        repair.get("work_unit_fingerprint"),
        repair.get("action_fingerprint"),
        repair.get("source_fingerprint"),
    )
    if source_fingerprint is None or repair_fingerprint != source_fingerprint:
        return False
    obligation_fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if obligation_fingerprint is not None and source_fingerprint != obligation_fingerprint:
        return False
    action_eval = _text(current_action.get("source_eval_id"))
    repair_eval = _text(repair.get("source_eval_id"))
    if action_eval is not None and repair_eval is not None and action_eval != repair_eval:
        return False
    return True


def _repair_progress_followup_owner_receipt_ref(repair: Mapping[str, Any]) -> str | None:
    gate_replay_refs = _text_items(repair.get("gate_replay_refs"))
    for ref in gate_replay_refs:
        if "gate_clearing_batch" in ref:
            return ref
    for ref in gate_replay_refs:
        if "publishability_gate" in ref or "receipt" in ref:
            return ref
    return None


def _closeout_refs(closeout: Mapping[str, Any]) -> list[str]:
    refs = [
        _text(closeout.get("closeout_ref")),
        _text(closeout.get("source_path")),
        _text(closeout.get("typed_blocker_ref")),
        *_text_items(closeout.get("closeout_refs")),
    ]
    return list(dict.fromkeys(ref for ref in refs if ref is not None))


__all__ = [
    "owner_receipt_recorded_current_work_unit",
    "repair_progress_owner_receipt_superseding_terminal_stop_loss",
    "same_work_unit_owner_receipt",
    "successor_owner_action_from_consumed_owner_receipt",
]
