from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_owner_dispatch_and_obligation_violation_guards() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    owner_dispatch_bad_inventory = json.loads(json.dumps(inventory))
    owner_dispatch = next(
        surface
        for surface in owner_dispatch_bad_inventory["surfaces"]
        if surface["surface_id"] == "stage_outcome_authority"
    )
    owner_dispatch["execution_authorization_boundary"][
        "closeout_binding_authorizes_execution"
    ] = True
    owner_dispatch["execution_authorization_boundary"][
        "repo_level_authorization_coverage_complete"
    ] = False
    owner_dispatch["execution_authorization_boundary"][
        "missing_authorization_outcome"
    ] = "execute_anyway"
    owner_dispatch["execution_authorization_boundary"][
        "running_provider_attempt_selector_boundary"
    ]["running_provider_attempt_without_opl_proof_can_select_route"] = True
    owner_dispatch["active_caller_soak_boundary"][
        "live_every_active_caller_soak_proven"
    ] = True
    owner_dispatch["active_caller_soak_boundary"]["no_active_caller_proven"] = True
    owner_dispatch["active_caller_soak_boundary"]["physical_delete_allowed"] = True
    owner_dispatch["active_caller_soak_boundary"][
        "repo_authorization_coverage_can_satisfy_live_soak"
    ] = True
    owner_dispatch["active_caller_soak_boundary"][
        "current_execution_running_proof_can_satisfy_live_soak"
    ] = True
    owner_dispatch["active_caller_soak_boundary"][
        "study_progress_running_proof_can_satisfy_live_soak"
    ] = True
    owner_dispatch["active_caller_soak_boundary"][
        "provider_completion_can_satisfy_dispatch_retirement"
    ] = True
    owner_dispatch["active_caller_soak_boundary"][
        "owner_callable_receipt_projection_can_satisfy_opl_readback"
    ] = True
    owner_dispatch["active_caller_soak_boundary"][
        "opl_execution_authorization_required_blocker_can_satisfy_live_soak"
    ] = True
    owner_dispatch["active_caller_soak_boundary"][
        "provider_handoff_or_completion_can_satisfy_physical_delete"
    ] = True
    owner_dispatch["active_caller_soak_boundary"][
        "required_before_physical_delete"
    ] = "repo_tests_green"
    owner_dispatch["active_caller_soak_boundary"]["physical_delete_requires"] = [
        "repo_tests_green_ref"
    ]
    owner_dispatch["active_caller_soak_boundary"]["required_active_caller_readbacks"] = [
        "repo_authorization_coverage"
    ]
    owner_dispatch["active_caller_soak_boundary"]["active_caller_families"] = [
        "stage_outcome_authority.execute_dispatch"
    ]
    owner_dispatch["active_caller_soak_boundary"]["forbidden_completion_claims"].remove(
        "repo_authorization_coverage_as_live_every_active_caller_soak"
    )
    owner_dispatch["active_caller_soak_boundary"]["forbidden_completion_claims"].remove(
        "owner_callable_adapter_receipt_projection_as_opl_stage_run_readback"
    )
    owner_dispatch["consumer_input_boundary"][
        "inline_default_executor_dispatch_request_candidate_allowed"
    ] = True
    owner_dispatch["consumer_input_boundary"][
        "can_create_opl_event_outbox_or_stage_run"
    ] = True
    owner_dispatch["stage_native_next_action_selector_boundary"][
        "candidate_without_opl_proof_can_authorize_execution"
    ] = True
    owner_dispatch["retirement_gate"]["live_every_active_caller_soak_required"] = False

    owner_dispatch_violations = retirement.validate_runtime_surface_retirement_inventory(
        owner_dispatch_bad_inventory
    )

    assert {
        (
            "stage_outcome_authority",
            (
                "truthy_authority_flag:execution_authorization_boundary."
                "closeout_binding_authorizes_execution"
            ),
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_closeout_binding_authorizes_execution",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_repo_authorization_coverage_not_complete",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_missing_authorization_outcome_not_typed_blocker",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_running_attempt_selector_allows_no_proof",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_soak_active_caller_families_incomplete",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_soak_must_not_claim_live_every_active_caller",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_soak_must_not_claim_no_active_caller",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_soak_must_not_allow_physical_delete",
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_soak_forbidden:"
                "repo_authorization_coverage_can_satisfy_live_soak"
            ),
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_soak_forbidden:"
                "current_execution_running_proof_can_satisfy_live_soak"
            ),
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_soak_forbidden:"
                "study_progress_running_proof_can_satisfy_live_soak"
            ),
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_soak_forbidden:"
                "provider_completion_can_satisfy_dispatch_retirement"
            ),
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_soak_forbidden:"
                "owner_callable_receipt_projection_can_satisfy_opl_readback"
            ),
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_soak_forbidden:"
                "opl_execution_authorization_required_blocker_can_satisfy_live_soak"
            ),
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_soak_forbidden:"
                "provider_handoff_or_completion_can_satisfy_physical_delete"
            ),
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_soak_missing_physical_delete_ref",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_soak_physical_delete_refs_incomplete",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_soak_active_readbacks_incomplete",
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_soak_missing_false_completion_guards",
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_consumer_boundary_forbidden:"
                "inline_default_executor_dispatch_request_candidate_allowed"
            ),
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_consumer_boundary_forbidden:"
                "can_create_opl_event_outbox_or_stage_run"
            ),
        ),
        (
            "stage_outcome_authority",
            (
                "owner_dispatch_stage_native_boundary_invalid:"
                "candidate_without_opl_proof_can_authorize_execution"
            ),
        ),
        (
            "stage_outcome_authority",
            "owner_dispatch_retirement_missing_live_soak",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in owner_dispatch_violations}

    obligation_bad_inventory = json.loads(json.dumps(inventory))
    obligation = next(
        surface
        for surface in obligation_bad_inventory["surfaces"]
        if surface["surface_id"] == "domain_health_diagnostic_obligation_actuator"
    )
    obligation["mas_can_run_supervisor_decision_engine"] = True
    obligation["mas_can_mutate_recovery_obligation_store"] = True
    obligation["active_caller_boundary"][
        "request_projection_only_can_satisfy_success"
    ] = True
    obligation["obligation_readback_boundary"][
        "request_projection_is_success_outcome"
    ] = True
    obligation["obligation_readback_boundary"][
        "success_proof_requires_consumed_readback_identity"
    ] = False
    obligation["obligation_readback_boundary"][
        "mas_domain_authority_readback_requires_authority_boundary"
    ] = False
    obligation["obligation_readback_boundary"][
        "read_model_evidence_refs_can_satisfy_success"
    ] = True
    obligation["obligation_readback_boundary"][
        "opl_obligation_actuator_tail_readback_requirement"
    ]["repo_no_authority_guard_can_satisfy_readback"] = True
    obligation["obligation_readback_boundary"][
        "opl_obligation_actuator_tail_readback_requirement"
    ]["mas_request_projection_can_satisfy_readback"] = True
    obligation["opl_obligation_actuator_tail_readback"]["tail_readback_proven"] = True
    obligation["opl_obligation_actuator_tail_readback"][
        "no_active_mas_obligation_actuator_caller_proven"
    ] = True
    obligation["opl_obligation_actuator_tail_readback"]["physical_delete_allowed"] = True
    obligation["opl_obligation_actuator_tail_readback"][
        "mas_policy_projection_can_satisfy_readback"
    ] = True
    obligation["opl_obligation_actuator_tail_readback"]["forbidden_completion_claims"] = []
    obligation["typed_blocker_authority_result_adapter_boundary"][
        "actuator_private_write_authority"
    ] = True
    obligation["typed_blocker_authority_result_adapter_boundary"][
        "can_authorize_provider_admission"
    ] = True
    obligation["actuator_direct_filesystem_write_retired"] = False
    obligation["retirement_gate"]["owner_retirement_decision_required"] = False

    obligation_violations = retirement.validate_runtime_surface_retirement_inventory(
        obligation_bad_inventory
    )

    assert {
        (
            "domain_health_diagnostic_obligation_actuator",
            "truthy_authority_flag:mas_can_mutate_recovery_obligation_store",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "truthy_authority_flag:mas_can_run_supervisor_decision_engine",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_forbidden:mas_can_mutate_recovery_obligation_store",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_forbidden:mas_can_run_supervisor_decision_engine",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "request_projection_can_satisfy_success",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_request_projection_can_satisfy_success",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_request_projection_is_success",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_missing_consumed_identity_gate",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_missing_domain_authority_boundary_gate",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_read_model_refs_can_satisfy_success",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_readback_tail_forbidden:repo_no_authority_guard_can_satisfy_readback",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_must_not_claim_readback_proven",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_must_not_claim_no_active_caller",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_must_not_allow_physical_delete",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_forbidden:mas_policy_projection_can_satisfy_readback",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_missing_false_completion_guards",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            (
                "truthy_authority_flag:typed_blocker_authority_result_adapter_boundary."
                "actuator_private_write_authority"
            ),
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            (
                "obligation_actuator_typed_blocker_boundary_forbidden:"
                "actuator_private_write_authority"
            ),
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            (
                "obligation_actuator_typed_blocker_boundary_forbidden:"
                "can_authorize_provider_admission"
            ),
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_direct_filesystem_write_not_retired",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_must_not_claim_readback_proven",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_must_not_claim_no_active_caller",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_must_not_allow_physical_delete",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_forbidden:mas_policy_projection_can_satisfy_readback",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_tail_missing_false_completion_guards",
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            (
                "obligation_actuator_readback_tail_forbidden:"
                "mas_request_projection_can_satisfy_readback"
            ),
        ),
        (
            "domain_health_diagnostic_obligation_actuator",
            "obligation_actuator_missing_owner_retirement_decision_gate",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in obligation_violations}
