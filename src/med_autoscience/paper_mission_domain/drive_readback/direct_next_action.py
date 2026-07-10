from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_domain.common import (
    _mapping,
    _optional_text,
)
from med_autoscience.paper_mission_domain.direct_next_action_handoff import (
    build_direct_next_action_handoff,
)


def drive_should_submit_direct_next_action(
    inspect_readback: Mapping[str, Any] | None,
) -> bool:
    readback = _mapping(inspect_readback)
    next_action = _mapping(readback.get("next_action"))
    action_family = _optional_text(next_action.get("action_family"))
    canonical_source = _optional_text(readback.get("canonical_next_action_source"))
    if action_family in {
        "paper.package.submission_minimal",
        "paper.stage_closure.owner_consumption",
    }:
        return False
    authority_boundary = _mapping(next_action.get("authority_boundary"))
    if (
        action_family == "runtime.opl_route"
        and _optional_text(next_action.get("action_kind")) == "submit_to_opl_runtime"
        and authority_boundary.get("can_submit_to_opl_runtime") is True
        and _optional_text(next_action.get("owner")) is not None
        and _optional_text(next_action.get("work_unit_id")) is not None
        and not drive_direct_next_action_already_owner_consumed(readback, next_action)
        and (
            canonical_source == "paper_mission_next_action_envelope"
            or bool(_mapping(readback.get("terminal_owner_gate")))
            or (
                drive_readback_has_submission_route_checkpoint(readback)
                and drive_next_action_has_submit_authority(
                    next_action=next_action,
                    authority_boundary=authority_boundary,
                )
            )
        )
    ):
        return True
    if _optional_text(next_action.get("action_type")) == "request_opl_stage_attempt":
        if drive_direct_next_action_already_owner_consumed(readback, next_action):
            return False
        return True
    return (
        canonical_source == "domain_transition.next_action"
        and _optional_text(next_action.get("surface_kind")) == "mas_next_action_envelope"
        and action_family is not None
        and _optional_text(next_action.get("owner")) is not None
        and _optional_text(next_action.get("work_unit_id")) is not None
        and not drive_direct_next_action_already_owner_consumed(readback, next_action)
    )


def drive_next_action_has_submit_authority(
    *,
    next_action: Mapping[str, Any],
    authority_boundary: Mapping[str, Any],
) -> bool:
    if authority_boundary.get("can_submit_to_opl_runtime") is not True:
        return False
    return _optional_text(next_action.get("authority_source")) == "mas_next_action_compiler"


def drive_readback_has_submission_route_checkpoint(
    readback: Mapping[str, Any],
) -> bool:
    transaction_state = _optional_text(readback.get("transaction_state"))
    consume_status = _optional_text(readback.get("consume_candidate_status"))
    selected_outcome = _optional_text(readback.get("selected_outcome"))
    if "accepted_submission_milestone_candidate" not in {
        transaction_state,
        consume_status,
        selected_outcome,
    }:
        return False
    outcome = _mapping(_mapping(readback.get("stage_closure_decision")).get("outcome"))
    return _optional_text(outcome.get("transition_kind")) == "route_back_candidate_checkpoint"


def drive_direct_next_action_already_owner_consumed(
    readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> bool:
    if _current_terminal_closeout_consumed_for_next_action(readback, next_action):
        return True
    return any(
        _carrier_owner_consumed_same_next_action(current, next_action)
        for current in _runtime_carrier_readbacks(readback)
    )


def _carrier_owner_consumed_same_next_action(
    current: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> bool:
    consumption = _mapping(current.get("mas_receipt_consumption"))
    status = _optional_text(consumption.get("status")) or ""
    if not status.startswith("owner_consumed_"):
        return False
    if status == "owner_consumed_route_checkpoint":
        return _terminal_closeout_matches_next_action(current, next_action)
    next_work_unit = _optional_text(next_action.get("work_unit_id"))
    current_work_unit = (
        _optional_text(_mapping(current.get("opl_transition_receipt")).get("work_unit_id"))
        or _optional_text(_mapping(current.get("terminal_closeout")).get("work_unit_id"))
        or _optional_text(_mapping(current.get("terminal_closeout")).get("stage_id"))
        or _optional_text(consumption.get("work_unit_id"))
        or _optional_text(current.get("work_unit_id"))
    )
    return (
        next_work_unit is not None
        and current_work_unit is not None
        and next_work_unit == current_work_unit
    )


def _terminal_closeout_matches_next_action(
    current: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> bool:
    next_work_unit = _optional_text(next_action.get("work_unit_id"))
    next_fingerprint = _optional_text(next_action.get("work_unit_fingerprint"))
    terminal_closeout = _mapping(current.get("terminal_closeout"))
    current_work_unit = _optional_text(
        terminal_closeout.get("work_unit_id")
    ) or _optional_text(terminal_closeout.get("stage_id"))
    if next_fingerprint is not None:
        current_fingerprint = _optional_text(
            terminal_closeout.get("work_unit_fingerprint")
        ) or _optional_text(current.get("work_unit_fingerprint"))
        return current_fingerprint == next_fingerprint
    return next_work_unit is not None and current_work_unit == next_work_unit


def _current_terminal_closeout_consumed_for_next_action(
    readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> bool:
    for current in _runtime_carrier_readbacks(readback):
        current_consumption = _mapping(current.get("mas_receipt_consumption"))
        if (
            _optional_text(current_consumption.get("status"))
            != "requires_mas_owner_consumption"
        ):
            continue
        next_work_unit = _optional_text(next_action.get("work_unit_id"))
        next_fingerprint = _optional_text(next_action.get("work_unit_fingerprint"))
        current_fingerprint = _optional_text(
            _mapping(current.get("terminal_closeout")).get("work_unit_fingerprint")
        ) or _optional_text(current.get("work_unit_fingerprint"))
        if next_fingerprint is not None and current_fingerprint != next_fingerprint:
            continue
        current_work_unit = (
            _optional_text(_mapping(current.get("terminal_closeout")).get("work_unit_id"))
            or _optional_text(_mapping(current.get("terminal_closeout")).get("stage_id"))
            or _optional_text(
                _mapping(current.get("opl_transition_receipt")).get("work_unit_id")
            )
            or _optional_text(current_consumption.get("work_unit_id"))
        )
        if (
            next_work_unit is None
            or current_work_unit is None
            or next_work_unit != current_work_unit
        ):
            continue
        for applied in _applied_owner_consumptions(readback):
            if _optional_text(applied.get("status")) != "owner_consumed_route_checkpoint":
                continue
            if _consumption_identity_matches(current=current_consumption, applied=applied):
                return True
    return False


def _runtime_carrier_readbacks(
    readback: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    carriers = (
        _mapping(readback.get("current_opl_runtime_carrier_readback")),
        _mapping(readback.get("opl_runtime_carrier_readback")),
    )
    return tuple(carrier for carrier in carriers if carrier)


def _applied_owner_consumptions(
    readback: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    receipt_readback = _mapping(readback.get("receipt_owner_consumption_readback"))
    candidates = (
        _mapping(receipt_readback.get("mas_receipt_consumption")),
        _mapping(readback.get("mas_receipt_consumption")),
    )
    return tuple(
        candidate
        for candidate in candidates
        if _optional_text(candidate.get("surface_kind"))
        == "mas_receipt_consumption_projection"
    )


def _consumption_identity_matches(
    *,
    current: Mapping[str, Any],
    applied: Mapping[str, Any],
) -> bool:
    for key in (
        "route_back_evidence_ref",
        "typed_runtime_blocker_ref",
        "receipt_evidence_ref",
        "route_checkpoint_evidence_ref",
    ):
        current_value = _optional_text(current.get(key))
        applied_value = _optional_text(applied.get(key))
        if current_value is not None and applied_value is not None:
            return current_value == applied_value
    return False


def drive_direct_next_action_handoff(
    *,
    profile: Any,
    study_id: str,
    inspect_readback: Mapping[str, Any],
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    return build_direct_next_action_handoff(
        profile=profile,
        study_id=study_id,
        inspect_readback=inspect_readback,
        next_action=next_action,
    )


def drive_direct_next_action_result(
    *,
    handoff: Mapping[str, Any],
    opl_runtime_submission: Mapping[str, Any],
    carrier_readback: Mapping[str, Any],
) -> dict[str, Any]:
    carrier_status = _optional_text(carrier_readback.get("carrier_status"))
    submission_status = _optional_text(opl_runtime_submission.get("status"))
    status = (
        "opl_stage_route_running"
        if carrier_status == "opl_runtime_attempt_running_observed"
        else "opl_terminal_closeout_observed"
        if carrier_status == "opl_runtime_terminal_readback_observed"
        else "submitted_to_opl_runtime"
        if submission_status in {"submitted", "idempotent_noop"}
        else "opl_runtime_submission_pending"
        if submission_status == "not_requested"
        else "opl_runtime_submission_failed"
    )
    return {
        "surface_kind": "paper_mission_drive_result",
        "status": status,
        "reason": "domain_transition_direct_stage_attempt",
        "route_target": _optional_text(handoff.get("route_target")),
        "work_unit_id": _optional_text(handoff.get("work_unit_id")),
        "work_unit_fingerprint": _optional_text(handoff.get("work_unit_fingerprint")),
        "can_submit_to_opl_runtime": handoff.get("can_submit_to_opl_runtime") is True,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
    }
