from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import (
    _non_empty_text,
)

OPL_TRANSITION_RUNTIME_OWNER = "one-person-lab"
OPL_TRANSITION_RUNTIME_KIND = "DomainProgressTransitionRuntime"
MAS_TRANSITION_REQUEST_SURFACE = "mas_domain_progress_transition_request"
SOURCE_OF_TRUTH_CHAIN = (
    "DomainIntent",
    "OPL Command/Event/Outbox/StageRun",
    "MAS OwnerAnswer",
    "Derived Projection",
)
SUCCESS_OUTCOME_SOURCE_FAMILIES = (
    "opl_runtime_readback",
    "mas_owner_answer_readback",
    "mas_domain_authority_readback",
)
REQUEST_PROJECTION_SOURCE_FAMILY = "mas_policy_request_projection"
OPL_FOUNDATION_CONSUMED_SURFACES = (
    "RecoveryObligationStore",
    "SupervisorDecisionEngine",
    "HumanGateTransport",
    "StageRunIdentityPacket",
)
ACCEPTED_OBLIGATION_OUTCOME_KINDS = (
    "transition_request_pending",
    "provider_admission_pending",
    "running_provider_attempt",
    "owner_receipt_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "route_back_evidence_ref",
)
ACCEPTED_OUTCOMES_BY_SUPERVISOR_POLICY_LABEL = {
    "execute_current_owner_delta": {
        "transition_request_pending",
        "provider_admission_pending",
        "running_provider_attempt",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    },
    "consume_terminal_closeout": {
        "owner_receipt_ref",
        "typed_blocker_ref",
    },
    "materialize_recovery_action": {
        "transition_request_pending",
        "provider_admission_pending",
        "running_provider_attempt",
        "owner_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    },
    "wait_for_owner_with_resume_token": {
        "human_gate_ref",
        "typed_blocker_ref",
        "route_back_evidence_ref",
    },
    "stop_with_stable_typed_blocker": {
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    },
    "stop_with_owner_receipt": {
        "owner_receipt_ref",
        "typed_blocker_ref",
    },
}
VALIDATOR_AUTHORITY_BOUNDARY = {
    "surface_kind": "obligation_actuator_readback_result_shape_validator",
    "validator_role": "accepted_owner_answer_or_opl_readback_shape_validator",
    "local_allowed_outcome_table_role": (
        "contract_bound_result_shape_validation_not_supervisor_decision_engine"
    ),
    "opl_recovery_obligation_store_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "opl_supervisor_decision_engine_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "mas_can_choose_supervisor_decision": False,
    "mas_can_run_supervisor_decision_engine": False,
    "mas_can_store_recovery_obligation": False,
    "mas_can_replay_obligation": False,
    "mas_can_create_opl_command_event_or_outbox": False,
    "mas_can_generate_human_gate_resume_token": False,
    "request_projection_only_can_satisfy_success": False,
}
CONSUME_ONLY_READBACK_BOUNDARY = {
    "surface_kind": "domain_health_diagnostic_apply_consume_only_readback",
    "consumer": "med-autoscience.domain-health-diagnostic.apply",
    "opl_runtime_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "opl_recovery_obligation_store_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "opl_supervisor_decision_engine_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "opl_human_gate_transport_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "opl_stage_run_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "consumed_opl_foundation_surfaces": list(OPL_FOUNDATION_CONSUMED_SURFACES),
    "mas_role": "policy_and_authority_readback_consumer",
    "mas_can_store_recovery_obligation": False,
    "mas_can_run_supervisor_decision_engine": False,
    "mas_can_run_fixed_point_runtime": False,
    "mas_can_replay_obligation": False,
    "mas_can_persist_obligation_store": False,
    "mas_can_generate_human_gate_resume_token": False,
    "mas_can_authorize_provider_admission": False,
    "success_requires_source_family": list(SUCCESS_OUTCOME_SOURCE_FAMILIES),
    "success_requires_opl_foundation_readback_boundary": True,
    "request_projection_is_success_outcome": False,
    "supervisor_disallowed_outcome_is_success": False,
    "readback_result_validator_boundary": dict(VALIDATOR_AUTHORITY_BOUNDARY),
}
ACTUATOR_AUTHORITY_BOUNDARY = {
    "surface_kind": "mas_obligation_outcome_projection_authority_boundary",
    "authority": "med_autoscience.paper_progress_policy_adapter",
    "authority_role": "paper_policy_and_owner_answer_readback_only",
    "adapter_kind": "mas_policy_adapter",
    "projection_role": "derived_obligation_outcome_readback_projection",
    "source_of_truth_chain": list(SOURCE_OF_TRUTH_CHAIN),
    "opl_transition_runtime_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "opl_transition_runtime_kind": OPL_TRANSITION_RUNTIME_KIND,
    "opl_recovery_obligation_store_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "opl_human_gate_transport_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "opl_stage_run_owner": OPL_TRANSITION_RUNTIME_OWNER,
    "accepts_opl_recovery_obligation_store_readback": True,
    "accepts_opl_human_gate_transport_readback": True,
    "accepts_opl_stage_run_readback": True,
    "accepts_mas_policy_result": True,
    "accepts_mas_owner_answer_result": True,
    "can_authorize_provider_admission": False,
    "can_own_generic_event_log_or_outbox": False,
    "can_create_opl_command_event_or_outbox": False,
    "can_store_recovery_obligation": False,
    "can_run_fixed_point_runtime": False,
    "can_run_supervisor_decision_engine": False,
    "can_write_opl_current_control_state": False,
    "can_apply_non_advancing_transition": False,
    "can_replay_obligation": False,
    "can_persist_obligation_store": False,
    "provider_admission_requires_opl_runtime_result": True,
    "provider_admission_readback_requires_opl_event_or_outbox": True,
    "can_execute_mas_owner_callable": False,
    "can_write_fail_closed_typed_control_blocker": False,
    "fail_closed_typed_blocker_owner": "med-autoscience",
    "fail_closed_typed_blocker_surface": "mas_domain_typed_blocker",
    "actuator_can_write_private_blocker_surface": False,
    "success_outcome_source_families": list(SUCCESS_OUTCOME_SOURCE_FAMILIES),
    "request_projection_outcome_source_family": REQUEST_PROJECTION_SOURCE_FAMILY,
    "request_projection_is_success_outcome": False,
    "success_requires_opl_foundation_readback_boundary": True,
    "readback_result_validator_boundary": dict(VALIDATOR_AUTHORITY_BOUNDARY),
    "consume_only_readback_boundary": dict(CONSUME_ONLY_READBACK_BOUNDARY),
}


def readback_result_validator_boundary() -> dict[str, Any]:
    return dict(VALIDATOR_AUTHORITY_BOUNDARY)


def consume_only_readback_boundary() -> dict[str, Any]:
    return dict(CONSUME_ONLY_READBACK_BOUNDARY)


def allowed_outcomes_for_policy_label(policy_label: str | None) -> set[str]:
    if policy_label in ACCEPTED_OUTCOMES_BY_SUPERVISOR_POLICY_LABEL:
        return set(ACCEPTED_OUTCOMES_BY_SUPERVISOR_POLICY_LABEL[policy_label])
    return set(ACCEPTED_OBLIGATION_OUTCOME_KINDS)


def outcome_source_family(outcome_kind: str) -> str:
    if outcome_kind in {"provider_admission_pending", "running_provider_attempt"}:
        return "opl_runtime_readback"
    if outcome_kind == "owner_receipt_ref":
        return "mas_owner_answer_readback"
    if outcome_kind in {"typed_blocker_ref", "human_gate_ref", "route_back_evidence_ref"}:
        return "mas_domain_authority_readback"
    if outcome_kind == "transition_request_pending":
        return REQUEST_PROJECTION_SOURCE_FAMILY
    return "unknown"


def opl_foundation_readback_boundary(*, source_family: str) -> dict[str, Any]:
    return {
        "surface_kind": "opl_foundation_readback_boundary",
        "source_family": source_family,
        "opl_runtime_owner": OPL_TRANSITION_RUNTIME_OWNER,
        "opl_transition_runtime_kind": OPL_TRANSITION_RUNTIME_KIND,
        "consumed_opl_foundation_surfaces": list(OPL_FOUNDATION_CONSUMED_SURFACES),
        "mas_role": "consume_only_projection",
        "mas_can_store_recovery_obligation": False,
        "mas_can_run_supervisor_decision_engine": False,
        "mas_can_run_fixed_point_runtime": False,
        "mas_can_replay_obligation": False,
        "mas_policy_request_projection_can_satisfy_success": False,
        "readback_result_validator_boundary": dict(VALIDATOR_AUTHORITY_BOUNDARY),
        "success_source_family": (
            source_family if source_family in SUCCESS_OUTCOME_SOURCE_FAMILIES else None
        ),
        "success_source_family_required": source_family in SUCCESS_OUTCOME_SOURCE_FAMILIES,
    }


def outcome_has_required_foundation_readback(
    *,
    source_family: str,
    opl_foundation: Mapping[str, Any],
) -> bool:
    if source_family not in SUCCESS_OUTCOME_SOURCE_FAMILIES:
        return False
    if _non_empty_text(opl_foundation.get("surface_kind")) != "opl_foundation_readback_boundary":
        return False
    validator_boundary = opl_foundation.get("readback_result_validator_boundary")
    if not isinstance(validator_boundary, Mapping):
        return False
    if validator_boundary.get("mas_can_run_supervisor_decision_engine") is not False:
        return False
    if validator_boundary.get("mas_can_store_recovery_obligation") is not False:
        return False
    if validator_boundary.get("mas_can_choose_supervisor_decision") is not False:
        return False
    return _non_empty_text(opl_foundation.get("success_source_family")) == source_family
