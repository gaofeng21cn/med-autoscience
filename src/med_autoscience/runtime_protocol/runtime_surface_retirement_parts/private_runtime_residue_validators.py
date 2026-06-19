from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def validate_domain_owner_action_dispatch(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "opl_authorized_owner_callable_adapter":
        violations.append(_violation(surface_id, "owner_dispatch_not_opl_authorized_adapter"))
    if surface.get("retained_mas_role") != "owner_callable_adapter_policy_boundary_and_typed_blocker_projection":
        violations.append(_violation(surface_id, "owner_dispatch_retained_role_not_minimal_adapter"))

    execution_boundary = surface.get("execution_authorization_boundary")
    if not isinstance(execution_boundary, Mapping):
        violations.append(_violation(surface_id, "owner_dispatch_missing_execution_authorization_boundary"))
    else:
        required_sources = {
            "trusted_opl_execution_authorization",
            "exact_provider_hosted_stage_attempt",
            "active_opl_provider_attempt_or_lease",
            "bound_opl_domain_progress_transition_runtime_readback",
        }
        sources = execution_boundary.get("execution_authorization_sources")
        if not isinstance(sources, list) or not required_sources <= {str(item) for item in sources}:
            violations.append(_violation(surface_id, "owner_dispatch_missing_opl_authorization_sources"))
        if execution_boundary.get("closeout_binding_authorizes_execution") is not False:
            violations.append(_violation(surface_id, "owner_dispatch_closeout_binding_authorizes_execution"))
        if execution_boundary.get("repo_level_authorization_coverage_complete") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_repo_authorization_coverage_not_complete"))
        if execution_boundary.get("live_every_active_caller_soak_required") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_missing_live_every_active_caller_soak_gate"))
        if execution_boundary.get("missing_authorization_outcome") != "opl_execution_authorization_required_typed_blocker":
            violations.append(_violation(surface_id, "owner_dispatch_missing_authorization_outcome_not_typed_blocker"))
        if execution_boundary.get("provider_attempt_or_lease_required_when_blocked") is not False:
            violations.append(_violation(surface_id, "owner_dispatch_provider_attempt_required_when_blocked"))
        selector = execution_boundary.get("running_provider_attempt_selector_boundary")
        if isinstance(selector, Mapping):
            if selector.get("running_provider_attempt_without_opl_proof_can_select_route") is not False:
                violations.append(_violation(surface_id, "owner_dispatch_running_attempt_selector_allows_no_proof"))
            accepted_proofs = selector.get("accepted_proofs")
            required_proofs = {
                "trusted_opl_execution_authorization",
                "exact_provider_hosted_stage_attempt",
                "bound_opl_domain_progress_transition_runtime_readback",
            }
            if not isinstance(accepted_proofs, list) or not required_proofs <= {
                str(item) for item in accepted_proofs
            }:
                violations.append(_violation(surface_id, "owner_dispatch_running_attempt_selector_missing_proofs"))
        else:
            violations.append(_violation(surface_id, "owner_dispatch_missing_running_attempt_selector_boundary"))

    coverage = surface.get("execution_authorization_coverage")
    if not isinstance(coverage, Mapping):
        violations.append(_violation(surface_id, "owner_dispatch_missing_execution_authorization_coverage"))
    else:
        if coverage.get("coverage_status") != "repo_fail_closed_all_supported_actions_live_readback_tail_open":
            violations.append(_violation(surface_id, "owner_dispatch_coverage_status_not_fail_closed"))
        if coverage.get("request_projection_without_opl_proof_outcome") != "opl_execution_authorization_required":
            violations.append(_violation(surface_id, "owner_dispatch_request_without_proof_not_blocked"))
        if coverage.get("live_readback_required_before_retirement") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_missing_live_readback_retirement_gate"))
        if coverage.get("live_tail") != "live_every_active_caller_soak_or_no_active_caller_proof":
            violations.append(_violation(surface_id, "owner_dispatch_live_tail_not_explicit"))

    consumer = surface.get("consumer_input_boundary")
    if not isinstance(consumer, Mapping):
        violations.append(_violation(surface_id, "owner_dispatch_missing_consumer_input_boundary"))
    else:
        if consumer.get("canonical_current_surface") != "domain_progress_transition_requests":
            violations.append(_violation(surface_id, "owner_dispatch_canonical_surface_not_transition_requests"))
        for key in (
            "inline_default_executor_dispatch_request_candidate_allowed",
            "owner_callable_adapters_candidate_allowed",
            "can_authorize_provider_admission",
            "can_create_provider_attempt",
            "can_create_opl_event_outbox_or_stage_run",
        ):
            if consumer.get(key, False) is not False:
                violations.append(_violation(surface_id, f"owner_dispatch_consumer_boundary_forbidden:{key}"))
        if consumer.get("explicit_action_pending_request_outcome") != "opl_execution_authorization_required":
            violations.append(_violation(surface_id, "owner_dispatch_explicit_action_pending_not_blocked"))

    stage_native = surface.get("stage_native_next_action_selector_boundary")
    if isinstance(stage_native, Mapping):
        for key in (
            "candidate_without_opl_proof_can_score_current",
            "candidate_without_opl_proof_can_be_selected_by_default",
            "candidate_without_opl_proof_can_preempt_other_current_dispatch",
            "candidate_without_opl_proof_can_authorize_execution",
            "candidate_without_opl_proof_owner_route_basis_is_authority",
            "provider_admission_pending",
            "provider_attempt_or_lease_required",
            "mas_private_attempt_loop_forbidden",
        ):
            expected = True if key == "mas_private_attempt_loop_forbidden" else False
            if stage_native.get(key, False) is not expected:
                violations.append(_violation(surface_id, f"owner_dispatch_stage_native_boundary_invalid:{key}"))
        required_proofs = {
            "trusted_opl_execution_authorization",
            "exact_provider_hosted_stage_attempt",
            "bound_opl_domain_progress_transition_runtime_readback",
        }
        proofs = stage_native.get("required_execution_proofs")
        if not isinstance(proofs, list) or not required_proofs <= {str(item) for item in proofs}:
            violations.append(_violation(surface_id, "owner_dispatch_stage_native_missing_execution_proofs"))
    else:
        violations.append(_violation(surface_id, "owner_dispatch_missing_stage_native_selector_boundary"))

    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        if gate.get("live_every_active_caller_soak_required") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_retirement_missing_live_soak"))
        if gate.get("no_active_caller_required_before_physical_delete") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_retirement_missing_no_active_caller_gate"))
        if gate.get("no_forbidden_write_proof_required") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_retirement_missing_no_forbidden_write_proof"))
    return violations


def validate_domain_health_diagnostic_obligation_actuator(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "obligation_readback_projection_consumer":
        violations.append(_violation(surface_id, "obligation_actuator_not_readback_projection_consumer"))
    if surface.get("retained_mas_role") != "consume_only_obligation_outcome_projection_and_mas_typed_blocker_authority_result":
        violations.append(_violation(surface_id, "obligation_actuator_retained_role_not_consume_only"))
    if surface.get("validator_role") != "accepted_owner_answer_or_opl_readback_shape_validator":
        violations.append(_violation(surface_id, "obligation_actuator_validator_role_not_readback_shape_validator"))
    if surface.get("local_allowed_outcome_table_role") != "contract_bound_result_shape_validation_not_supervisor_decision_engine":
        violations.append(_violation(surface_id, "obligation_actuator_local_outcome_table_is_decision_engine"))
    for key in (
        "mas_can_choose_supervisor_decision",
        "mas_can_mutate_recovery_obligation_store",
        "mas_can_run_supervisor_decision_engine",
        "study_progress_supervisor_projection_can_build_decision",
        "paper_recovery_state_can_build_decision",
        "read_model_can_run_supervisor_decision_engine",
        "mas_can_create_opl_command_event_or_outbox",
        "can_write_fail_closed_typed_control_blocker",
        "actuator_can_write_private_blocker_surface",
    ):
        if surface.get(key, False) is not False:
            violations.append(_violation(surface_id, f"obligation_actuator_forbidden:{key}"))
    if surface.get("actuator_direct_filesystem_write_retired") is not True:
        violations.append(_violation(surface_id, "obligation_actuator_direct_filesystem_write_not_retired"))
    if surface.get("transition_request_pending_can_close_physical_tail") is not False:
        violations.append(_violation(surface_id, "obligation_actuator_transition_request_can_close_physical_tail"))

    active_boundary = surface.get("active_caller_boundary")
    if not isinstance(active_boundary, Mapping):
        violations.append(_violation(surface_id, "obligation_actuator_missing_active_caller_boundary"))
    else:
        if active_boundary.get("active_caller_effect") != "consume_only_readback_projection_with_success_proof_gated_postcondition":
            violations.append(_violation(surface_id, "obligation_actuator_active_effect_not_consume_only"))
        if active_boundary.get("active_caller_retains_surface") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_active_surface_tail_not_explicit"))
        if active_boundary.get("active_caller_retains_runtime_authority") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_active_caller_retains_runtime_authority"))
        if active_boundary.get("request_projection_only_can_satisfy_success") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_request_projection_can_satisfy_success"))
        required_physical_delete = {
            "opl_recovery_obligation_store_active_caller",
            "opl_supervisor_decision_engine_active_caller",
            "no_active_caller_scan",
            "replacement_parity_ref",
            "owner_retirement_decision_ref",
            "tombstone_or_provenance_ref",
        }
        physical_delete_requires = active_boundary.get("physical_delete_requires")
        if not isinstance(physical_delete_requires, list) or not required_physical_delete <= set(physical_delete_requires):
            violations.append(_violation(surface_id, "obligation_actuator_physical_delete_gate_incomplete"))

    readback = surface.get("obligation_readback_boundary")
    if not isinstance(readback, Mapping):
        violations.append(_violation(surface_id, "obligation_actuator_missing_readback_boundary"))
    else:
        if readback.get("request_projection_is_success_outcome") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_request_projection_is_success"))
        if readback.get("success_proof_required_for_postcondition_ok") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_success_proof_gate"))
        if readback.get("success_proof_requires_consumed_readback_identity") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_consumed_identity_gate"))
        if readback.get("success_proof_forbidden_when_request_projection_only") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_request_projection_can_emit_success_proof"))
        if readback.get("supervisor_disallowed_outcome_is_success") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_disallowed_supervisor_outcome_is_success"))
        if readback.get("readback_result_validator_boundary_required") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_validator_boundary_requirement"))
        if readback.get("local_allowed_outcome_table_role") != "contract_bound_result_shape_validation_not_supervisor_decision_engine":
            violations.append(_violation(surface_id, "obligation_actuator_readback_table_is_decision_engine"))
        if readback.get("actuator_can_write_private_blocker_surface") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_readback_can_write_private_blocker"))
        source_families = readback.get("success_outcome_source_families")
        required_families = {
            "opl_runtime_readback",
            "mas_owner_answer_readback",
            "mas_domain_authority_readback",
        }
        if not isinstance(source_families, list) or not required_families <= {str(item) for item in source_families}:
            violations.append(_violation(surface_id, "obligation_actuator_missing_success_source_families"))

    typed_boundary = surface.get("typed_blocker_authority_result_adapter_boundary")
    if not isinstance(typed_boundary, Mapping):
        violations.append(_violation(surface_id, "obligation_actuator_missing_typed_blocker_adapter_boundary"))
    else:
        if typed_boundary.get("surface_kind") != "mas_domain_typed_blocker_authority_result_boundary":
            violations.append(_violation(surface_id, "obligation_actuator_typed_blocker_boundary_kind_invalid"))
        if typed_boundary.get("authority_owner") != "med-autoscience":
            violations.append(_violation(surface_id, "obligation_actuator_typed_blocker_owner_not_mas"))
        if typed_boundary.get("authority_result_surface") != "mas_domain_typed_blocker":
            violations.append(_violation(surface_id, "obligation_actuator_typed_blocker_surface_invalid"))
        for key in (
            "actuator_private_write_authority",
            "can_create_opl_command",
            "can_create_opl_event",
            "can_create_opl_outbox",
            "can_create_opl_stage_run",
            "can_store_recovery_obligation",
            "can_run_supervisor_decision_engine",
            "can_authorize_provider_admission",
            "can_claim_paper_progress",
            "can_write_publication_eval",
            "can_write_controller_decision",
        ):
            if typed_boundary.get(key, False) is not False:
                violations.append(_violation(surface_id, f"obligation_actuator_typed_blocker_boundary_forbidden:{key}"))

    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        if gate.get("owner_retirement_decision_required") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_owner_retirement_decision_gate"))
        if gate.get("no_active_caller_required_before_physical_delete") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_no_active_caller_gate"))
        if gate.get("no_forbidden_write_proof_required") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_no_forbidden_write_proof"))
    return violations


def _violation(surface_id: str, reason: str) -> dict[str, str]:
    return {"surface_id": surface_id, "reason": reason}


__all__ = [
    "validate_domain_health_diagnostic_obligation_actuator",
    "validate_domain_owner_action_dispatch",
]
