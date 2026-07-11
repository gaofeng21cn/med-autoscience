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
        return True
    return (
        canonical_source == "domain_transition.next_action"
        and _optional_text(next_action.get("surface_kind")) == "mas_next_action_envelope"
        and action_family is not None
        and _optional_text(next_action.get("owner")) is not None
        and _optional_text(next_action.get("work_unit_id")) is not None
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
