from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_domain.common import (
    _mapping,
    _optional_text,
)


def _stage_closure_next_action_should_own_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None = None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None = None,
    include_delivery_sync_actions: bool = True,
) -> bool:
    action = _mapping(next_action)
    if not action:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if (
        _mapping(domain_transition_next_action)
        and outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind") == "route_back_candidate_checkpoint"
    ):
        if _receipt_owner_consumed_route_checkpoint(receipt_owner_consumption_readback):
            return not _owner_consumed_route_checkpoint_yields_to_domain_transition(
                stage_closure_decision=stage_closure_decision,
                domain_transition_next_action=domain_transition_next_action,
            )
        return _route_checkpoint_matches_domain_transition(
            stage_closure_decision=stage_closure_decision,
            outcome=outcome,
            domain_transition_next_action=domain_transition_next_action,
        )
    if _optional_text(action.get("action_family")) == (
        "paper.stage_closure.owner_consumption"
    ):
        return True
    if include_delivery_sync_actions and _optional_text(action.get("action_family")) in {
        "paper.delivery.sync",
        "paper.delivery_sync",
    }:
        return True
    return (
        outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind")
        in {"route_back_candidate_checkpoint", "current_package_mirror_sync"}
    )


def _stage_closure_owner_receipt_suppresses_transaction_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action_override: Mapping[str, Any] | None,
) -> bool:
    if next_action_override is not None:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if _optional_text(outcome.get("kind")) != "owner_receipt":
        return False
    if (
        _optional_text(outcome.get("package_kind")) == "submission_ready_package"
        and outcome.get("can_submit") is True
    ):
        return False
    return True


def suppress_consumed_route_checkpoint_transaction_next_action(
    *,
    transaction_output_fields: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not _receipt_owner_consumed_route_checkpoint(receipt_owner_consumption_readback):
        return dict(transaction_output_fields)
    action = _mapping(transaction_output_fields.get("next_action"))
    if _optional_text(action.get("action_family")) != (
        "paper.stage_closure.owner_consumption"
    ):
        return dict(transaction_output_fields)
    suppressed = dict(transaction_output_fields)
    suppressed.pop("next_action", None)
    suppressed.pop("canonical_next_action_source", None)
    nested = _mapping(suppressed.get("paper_mission_transaction_readback"))
    if nested:
        nested = dict(nested)
        nested.pop("next_action", None)
        suppressed["paper_mission_transaction_readback"] = nested
    return suppressed


def _receipt_owner_consumed_route_checkpoint(
    readback: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping(readback)
    if _optional_text(payload.get("status")) != "owner_consumption_applied":
        return False
    consumption = _mapping(payload.get("mas_receipt_consumption"))
    return _optional_text(consumption.get("status")) == "owner_consumed_route_checkpoint"


def _route_checkpoint_matches_domain_transition(
    *,
    stage_closure_decision: Mapping[str, Any],
    outcome: Mapping[str, Any],
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    if not _route_checkpoint_identity_matches_domain_transition(
        stage_closure_decision=stage_closure_decision,
        domain_transition_next_action=domain_transition_next_action,
    ):
        return False
    return (
        stage_closure_decision.get("authority_materialized") is True
        or _optional_text(outcome.get("route_checkpoint_evidence_ref")) is not None
        or _optional_text(
            _mapping(stage_closure_decision.get("opl_closeout")).get("stage_attempt_id")
        )
        is not None
    )


def _owner_consumed_route_checkpoint_yields_to_domain_transition(
    *,
    stage_closure_decision: Mapping[str, Any],
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    if _route_checkpoint_identity_matches_domain_transition(
        stage_closure_decision=stage_closure_decision,
        domain_transition_next_action=domain_transition_next_action,
    ):
        return True
    action = _mapping(domain_transition_next_action)
    if not _domain_transition_next_action_requests_stage_attempt(action):
        return False
    decision_stage = _optional_text(stage_closure_decision.get("stage_id"))
    action_stage = _optional_text(action.get("stage_id"))
    action_work_unit = _optional_text(action.get("work_unit_id"))
    if action_stage is None or action_work_unit is None:
        return False
    return decision_stage in {action_stage, "submission_milestone_candidate"}


def _route_checkpoint_identity_matches_domain_transition(
    *,
    stage_closure_decision: Mapping[str, Any],
    domain_transition_next_action: Mapping[str, Any] | None,
) -> bool:
    action = _mapping(domain_transition_next_action)
    if not action:
        return False
    decision_work_unit = _optional_text(stage_closure_decision.get("work_unit_id"))
    action_work_unit = _optional_text(action.get("work_unit_id"))
    if (
        decision_work_unit is not None
        and action_work_unit is not None
        and decision_work_unit != action_work_unit
    ):
        return False
    decision_stage = _optional_text(stage_closure_decision.get("stage_id"))
    action_stage = _optional_text(action.get("stage_id"))
    if (
        decision_stage is not None
        and action_stage is not None
        and decision_stage != action_stage
    ):
        return False
    return True


def _stage_closure_suppresses_domain_transition_next_action(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
    domain_transition_next_action: Mapping[str, Any] | None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None = None,
) -> bool:
    action_override = _mapping(next_action)
    if _stage_closure_next_action_should_own_next_action(
        stage_closure_decision=stage_closure_decision,
        next_action=action_override,
        domain_transition_next_action=domain_transition_next_action,
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
    ):
        return False
    action = _mapping(domain_transition_next_action)
    if not action:
        return False
    outcome = _mapping(stage_closure_decision.get("outcome"))
    if outcome.get("kind") != "owner_receipt":
        return False
    if (
        outcome.get("can_submit") is True
        and outcome.get("package_kind") == "submission_ready_package"
    ):
        return False
    decision_work_unit = _optional_text(stage_closure_decision.get("work_unit_id"))
    action_work_unit = _optional_text(action.get("work_unit_id"))
    if decision_work_unit is None or action_work_unit != decision_work_unit:
        return False
    decision_stage = _optional_text(stage_closure_decision.get("stage_id"))
    action_stage = _optional_text(action.get("stage_id"))
    return (
        decision_stage is None
        or action_stage is None
        or decision_stage == action_stage
    )


def _domain_transition_next_action_requests_stage_attempt(
    next_action: Mapping[str, Any] | None,
) -> bool:
    action = _mapping(next_action)
    if _optional_text(action.get("surface_kind")) != "mas_next_action_envelope":
        return False
    if _optional_text(action.get("action_type")) == "request_opl_stage_attempt":
        return True
    return (
        _optional_text(action.get("action_family")) is not None
        and _optional_text(action.get("owner")) is not None
        and _optional_text(action.get("work_unit_id")) is not None
    )
