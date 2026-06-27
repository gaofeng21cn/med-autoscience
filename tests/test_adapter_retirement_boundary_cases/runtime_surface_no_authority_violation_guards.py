from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_runtime_surface_retirement_no_authority_audit_violation_guards() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    bad_inventory = json.loads(json.dumps(inventory))
    refs_surface = next(
        surface
        for surface in bad_inventory["surfaces"]
        if surface["surface_id"] == "domain_authority_refs_index"
    )
    refs_surface["active_caller_boundary"]["active_caller_retains_authority"] = True
    refs_surface["retirement_gate"]["active_caller_alone_retains_surface"] = True
    refs_surface["authority_boundary"]["can_authorize_provider_admission"] = True
    refs_surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"][
        "active_callers"
    ] = ["paper_progress_transition_refs.record_paper_progress_transition_ref::legacy_sqlite"]
    refs_surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"][
        "retired_callers"
    ] = []
    refs_surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"][
        "physical_delete_allowed"
    ] = True
    del refs_surface["tombstone_or_provenance_ref"]

    violations = retirement.validate_runtime_surface_retirement_inventory(bad_inventory)

    assert {
        ("domain_authority_refs_index", "truthy_authority_flag:active_caller_boundary.active_caller_retains_authority"),
        ("domain_authority_refs_index", "truthy_authority_flag:authority_boundary.can_authorize_provider_admission"),
        (
            "domain_authority_refs_index",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}

    materializer_bad_inventory = json.loads(json.dumps(inventory))
    materializer_surfaces = {
        surface["surface_id"]: surface for surface in materializer_bad_inventory["surfaces"]
    }
    retired_owner_adapter = materializer_surfaces[
        "domain_action_request_materializer_owner_callable_adapter_projection"
    ]
    retired_owner_adapter["legacy_projection_boundary"][
        "owner_callable_adapter_counts_authority"
    ] = True
    del retired_owner_adapter["tombstone_or_provenance_ref"]
    request_tasks = materializer_surfaces[
        "domain_action_request_materializer_request_tasks_projection"
    ]
    request_tasks["projection_boundary"]["body_authority"] = True
    del request_tasks["tombstone_or_provenance_ref"]
    transition_request = materializer_surfaces[
        "domain_action_request_materializer_canonical_transition_request_body_projection"
    ]
    transition_request["projection_boundary"]["transition_request_projection_body_authority"] = True
    del transition_request["tombstone_or_provenance_ref"]

    materializer_violations = retirement.validate_runtime_surface_retirement_inventory(
        materializer_bad_inventory
    )

    assert {
        (
            "domain_action_request_materializer_owner_callable_adapter_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
        (
            "domain_action_request_materializer_request_tasks_projection",
            "truthy_authority_flag:projection_boundary.body_authority",
        ),
        (
            "domain_action_request_materializer_canonical_transition_request_body_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
        (
            "domain_action_request_materializer_canonical_transition_request_body_projection",
            "truthy_authority_flag:projection_boundary.transition_request_projection_body_authority",
        ),
        (
            "domain_action_request_materializer_request_tasks_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in materializer_violations}

    legacy_bad_inventory = json.loads(json.dumps(inventory))
    legacy_latest = next(
        surface
        for surface in legacy_bad_inventory["surfaces"]
        if surface["surface_id"] == "default_executor_execution_latest_wire_projection"
    )
    legacy_latest["legacy_wire_default_reader_fallback_allowed"] = True
    legacy_latest["current_reader_boundary"][
        "default_executor_execution_candidates_reads_legacy_wire_by_default"
    ] = True
    legacy_latest["history_replay_boundary"].pop(
        "default_executor_receipt_consumption_requires_allow_legacy_fallback"
    )
    del legacy_latest["tombstone_or_provenance_ref"]

    legacy_violations = retirement.validate_runtime_surface_retirement_inventory(legacy_bad_inventory)

    assert {
        (
            "default_executor_execution_latest_wire_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in legacy_violations}

    legacy_stage_run_bad_inventory = json.loads(json.dumps(inventory))
    legacy_stage_run = next(
        surface
        for surface in legacy_stage_run_bad_inventory["surfaces"]
        if surface["surface_id"] == "default_executor_execution_latest_wire_projection"
    )
    legacy_stage_run["legacy_stage_run_abi_boundary"][
        "stage_closeout_packets_can_authorize_provider_admission"
    ] = True
    legacy_stage_run["legacy_stage_run_abi_boundary"][
        "stage_closeout_packets_can_authorize_execution"
    ] = True
    legacy_stage_run["legacy_stage_run_abi_boundary"][
        "terminal_closeout_consumption_requires_owner_result_or_typed_blocker"
    ] = False
    legacy_stage_run_scan = legacy_stage_run["legacy_stage_run_abi_boundary"][
        "active_stage_run_abi_caller_scan"
    ]
    legacy_stage_run_scan["no_active_stage_run_abi_caller_proven"] = True
    legacy_stage_run_scan["physical_delete_allowed"] = True
    del legacy_stage_run["tombstone_or_provenance_ref"]

    legacy_stage_run_violations = retirement.validate_runtime_surface_retirement_inventory(
        legacy_stage_run_bad_inventory
    )

    assert {
        (
            "default_executor_execution_latest_wire_projection",
            (
                "truthy_authority_flag:legacy_stage_run_abi_boundary."
                "stage_closeout_packets_can_authorize_provider_admission"
            ),
        ),
        (
            "default_executor_execution_latest_wire_projection",
            (
                "truthy_authority_flag:legacy_stage_run_abi_boundary."
                "stage_closeout_packets_can_authorize_execution"
            ),
        ),
        (
            "default_executor_execution_latest_wire_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in legacy_stage_run_violations}

    carrier_bad_inventory = json.loads(json.dumps(inventory))
    legacy_carrier = next(
        surface
        for surface in carrier_bad_inventory["surfaces"]
        if surface["surface_id"] == "default_executor_dispatch_request"
    )
    legacy_carrier["active_caller_boundary"]["provider_admission_pending"] = True
    legacy_carrier["legacy_stage_run_abi_provenance_boundary"]["mas_can_create_stage_run"] = True
    legacy_carrier["legacy_stage_run_abi_provenance_boundary"][
        "requires_opl_domain_progress_transition_runtime_intake"
    ] = False
    legacy_carrier["legacy_source_contamination_boundary"][
        "source_dispatch_claims_are_diagnostic_only"
    ] = False
    legacy_carrier["legacy_source_contamination_boundary"][
        "polluted_source_payload_can_authorize_provider_admission"
    ] = True
    legacy_carrier["legacy_source_contamination_boundary"]["forbidden_source_claims"].remove(
        "provider_admission_pending"
    )
    legacy_carrier["opl_default_executor_carrier_tail_readback"][
        "tail_readback_proven"
    ] = True
    legacy_carrier["opl_default_executor_carrier_tail_readback"][
        "transition_request_pending_can_satisfy_readback"
    ] = True
    legacy_carrier["opl_default_executor_carrier_tail_readback"][
        "request_only_carrier_can_authorize_provider_admission"
    ] = True
    legacy_carrier["opl_default_executor_carrier_tail_readback"][
        "forbidden_completion_claims"
    ].remove("transition_request_pending_as_opl_live_readback")
    del legacy_carrier["tombstone_or_provenance_ref"]

    carrier_violations = retirement.validate_runtime_surface_retirement_inventory(
        carrier_bad_inventory
    )

    assert {
        (
            "default_executor_dispatch_request",
            "truthy_authority_flag:active_caller_boundary.provider_admission_pending",
        ),
        (
            "default_executor_dispatch_request",
            "truthy_authority_flag:legacy_stage_run_abi_provenance_boundary.mas_can_create_stage_run",
        ),
        (
            "default_executor_dispatch_request",
            "truthy_authority_flag:legacy_source_contamination_boundary.polluted_source_payload_can_authorize_provider_admission",
        ),
        (
            "default_executor_dispatch_request",
            "truthy_authority_flag:opl_default_executor_carrier_tail_readback.request_only_carrier_can_authorize_provider_admission",
        ),
        (
            "default_executor_dispatch_request",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in carrier_violations}

    runtime_health_bad_inventory = json.loads(json.dumps(inventory))
    runtime_health = next(
        surface
        for surface in runtime_health_bad_inventory["surfaces"]
        if surface["surface_id"] == "runtime_health_kernel"
    )
    runtime_health["local_event_log_append_from_status_payload"] = True
    runtime_health["active_caller_boundary"]["active_caller_retains_runtime_authority"] = True
    runtime_health["active_caller_boundary"][
        "runtime_health_epoch_is_currentness_authority"
    ] = True
    runtime_health["active_caller_boundary"][
        "canonical_runtime_action_is_next_action_authority"
    ] = True
    runtime_health["active_caller_boundary"]["attempt_liveness_owner"] = "med-autoscience"
    runtime_health["diagnostic_projection_boundary"]["can_authorize_provider_admission"] = True
    runtime_health["diagnostic_projection_boundary"]["can_claim_paper_progress"] = True
    runtime_health["diagnostic_projection_boundary"][
        "canonical_runtime_action_is_diagnostic_hint"
    ] = False
    runtime_health["diagnostic_consumer_gate_boundary"][
        "unbound_opl_ref_can_authorize_decision"
    ] = True
    runtime_health["diagnostic_consumer_gate_boundary"][
        "identity_bound_opl_readback_required"
    ] = False
    runtime_health["diagnostic_consumer_gate_boundary"][
        "canonical_runtime_action_hint_can_authorize_recovery"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "tail_readback_proven"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "no_active_diagnostic_projection_caller_proven"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "physical_delete_allowed"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "mas_runtime_health_snapshot_can_satisfy_readback"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "required_tail_readback_families_must_match_same_runtime_identity"
    ] = False
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "current_control_or_stage_run_readback_alone_can_satisfy_tail"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "forbidden_completion_claims"
    ] = []
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "active_diagnostic_projection_caller_scan"
    ]["no_active_diagnostic_projection_caller_proven"] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "active_diagnostic_projection_caller_scan"
    ]["physical_delete_allowed"] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "active_diagnostic_projection_caller_scan"
    ]["allowed_consumption"] = []
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "active_diagnostic_projection_caller_scan"
    ]["forbidden_completion_claims"] = []
    runtime_health["retirement_gate"][
        "runtime_health_live_opl_observability_readback_required"
    ] = False

    runtime_health_violations = retirement.validate_runtime_surface_retirement_inventory(
        runtime_health_bad_inventory
    )

    assert {
        (
            "runtime_health_kernel",
            "runtime_health_status_payload_can_append_event_log",
        ),
        (
            "runtime_health_kernel",
            (
                "truthy_authority_flag:active_caller_boundary."
                "active_caller_retains_runtime_authority"
            ),
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_boundary_forbidden:active_caller_retains_runtime_authority",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_boundary_forbidden:runtime_health_epoch_is_currentness_authority",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_boundary_forbidden:canonical_runtime_action_is_next_action_authority",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_attempt_liveness_owner_not_opl",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_projection_forbidden:can_authorize_provider_admission",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_projection_forbidden:can_claim_paper_progress",
        ),
        (
            "runtime_health_kernel",
            (
                "runtime_health_missing_diagnostic_hint_boundary:"
                "canonical_runtime_action_is_diagnostic_hint"
            ),
        ),
        (
            "runtime_health_kernel",
            (
                "runtime_health_consumer_gate_forbidden:"
                "unbound_opl_ref_can_authorize_decision"
            ),
        ),
        (
            "runtime_health_kernel",
            (
                "runtime_health_consumer_gate_missing:"
                "identity_bound_opl_readback_required"
            ),
        ),
        (
            "runtime_health_kernel",
            (
                "runtime_health_consumer_gate_forbidden:"
                "canonical_runtime_action_hint_can_authorize_recovery"
            ),
        ),
        (
            "runtime_health_kernel",
            "runtime_health_missing_live_opl_observability_gate",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_must_not_claim_readback_proven",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_must_not_claim_no_active_caller",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_must_not_allow_physical_delete",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_forbidden:mas_runtime_health_snapshot_can_satisfy_readback",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_missing_same_identity_family_gate",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_allows_generic_readback_as_tail",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_missing_false_completion_guards",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_scan_must_not_claim_no_active",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_scan_blocks_physical_delete",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_no_active_claim_contradicts_callers",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_callers_block_physical_delete",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_scan_allowed_consumption_incomplete",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_scan_missing_false_completion_guard",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in runtime_health_violations}

    maintenance_bad_inventory = json.loads(json.dumps(inventory))
    maintenance_surfaces = {
        surface["surface_id"]: surface for surface in maintenance_bad_inventory["surfaces"]
    }
    lifecycle_retention = maintenance_surfaces["runtime_lifecycle_payload_retention"]
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "tail_readback_proven"
    ] = True
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "no_active_lifecycle_maintenance_adapter_caller_proven"
    ] = True
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "physical_delete_allowed"
    ] = True
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "apply_authorization_can_satisfy_live_takeover"
    ] = True
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "forbidden_completion_claims"
    ] = []
    storage_maintenance = maintenance_surfaces["runtime_storage_maintenance"]
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "tail_readback_proven"
    ] = True
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "no_active_storage_maintenance_adapter_caller_proven"
    ] = True
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "physical_delete_allowed"
    ] = True
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "dry_run_projection_can_satisfy_live_takeover"
    ] = True
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "forbidden_completion_claims"
    ] = []

    maintenance_violations = retirement.validate_runtime_surface_retirement_inventory(
        maintenance_bad_inventory
    )

    assert {
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_must_not_claim_readback_proven",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_must_not_claim_no_active_caller",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_must_not_allow_physical_delete",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_forbidden:apply_authorization_can_satisfy_live_takeover",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_missing_false_completion_guards",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_must_not_claim_readback_proven",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_must_not_claim_no_active_caller",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_must_not_allow_physical_delete",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_forbidden:dry_run_projection_can_satisfy_live_takeover",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_missing_false_completion_guards",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in maintenance_violations}

    owner_dispatch_bad_inventory = json.loads(json.dumps(inventory))
    owner_dispatch = next(
        surface
        for surface in owner_dispatch_bad_inventory["surfaces"]
        if surface["surface_id"] == "domain_owner_action_dispatch"
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
        "domain_owner_action_dispatch.execute_dispatch"
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
            "domain_owner_action_dispatch",
            (
                "truthy_authority_flag:execution_authorization_boundary."
                "closeout_binding_authorizes_execution"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_closeout_binding_authorizes_execution",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_repo_authorization_coverage_not_complete",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_missing_authorization_outcome_not_typed_blocker",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_running_attempt_selector_allows_no_proof",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_soak_active_caller_families_incomplete",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_soak_must_not_claim_live_every_active_caller",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_soak_must_not_claim_no_active_caller",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_soak_must_not_allow_physical_delete",
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_soak_forbidden:"
                "repo_authorization_coverage_can_satisfy_live_soak"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_soak_forbidden:"
                "current_execution_running_proof_can_satisfy_live_soak"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_soak_forbidden:"
                "study_progress_running_proof_can_satisfy_live_soak"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_soak_forbidden:"
                "provider_completion_can_satisfy_dispatch_retirement"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_soak_forbidden:"
                "owner_callable_receipt_projection_can_satisfy_opl_readback"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_soak_forbidden:"
                "opl_execution_authorization_required_blocker_can_satisfy_live_soak"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_soak_forbidden:"
                "provider_handoff_or_completion_can_satisfy_physical_delete"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_soak_missing_physical_delete_ref",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_soak_physical_delete_refs_incomplete",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_soak_active_readbacks_incomplete",
        ),
        (
            "domain_owner_action_dispatch",
            "owner_dispatch_soak_missing_false_completion_guards",
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_consumer_boundary_forbidden:"
                "inline_default_executor_dispatch_request_candidate_allowed"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_consumer_boundary_forbidden:"
                "can_create_opl_event_outbox_or_stage_run"
            ),
        ),
        (
            "domain_owner_action_dispatch",
            (
                "owner_dispatch_stage_native_boundary_invalid:"
                "candidate_without_opl_proof_can_authorize_execution"
            ),
        ),
        (
            "domain_owner_action_dispatch",
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

    workbench_bad_inventory = json.loads(json.dumps(inventory))
    workbench = next(
        surface
        for surface in workbench_bad_inventory["surfaces"]
        if surface["surface_id"]
        == "progress_portal_study_workbench_overview_action_projection"
    )
    workbench["projection_boundary"]["can_transport_operator_action"] = True
    workbench["projection_boundary"]["can_generate_action"] = True
    workbench["projection_boundary"][
        "operator_intent_refs_are_inert"
    ] = False
    workbench["opl_workbench_shell_readback_tail"]["tail_readback_proven"] = True
    workbench["opl_workbench_shell_readback_tail"][
        "no_active_workbench_projection_action_caller_proven"
    ] = True
    workbench["opl_workbench_shell_readback_tail"]["physical_delete_allowed"] = True
    workbench["opl_workbench_shell_readback_tail"][
        "mas_portal_projection_can_satisfy_readback"
    ] = True
    workbench["opl_workbench_shell_readback_tail"][
        "current_owner_delta_projection_can_satisfy_workbench_shell_readback"
    ] = True
    workbench["opl_workbench_shell_readback_tail"][
        "domain_progress_transition_runtime_readback_can_satisfy_action_transport"
    ] = True
    workbench["opl_workbench_shell_readback_tail"][
        "operator_intent_refs_can_satisfy_action_transport"
    ] = True
    workbench["opl_workbench_shell_readback_tail"]["forbidden_completion_claims"] = []
    workbench["retirement_gate"]["opl_workbench_shell_readback_required"] = False

    workbench_violations = retirement.validate_runtime_surface_retirement_inventory(
        workbench_bad_inventory
    )

    assert {
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_boundary_forbidden:can_generate_action",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_boundary_forbidden:can_transport_operator_action",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_boundary_mismatch:operator_intent_refs_are_inert",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_must_not_claim_readback_proven",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_must_not_claim_no_active_caller",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_must_not_allow_physical_delete",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_forbidden:mas_portal_projection_can_satisfy_readback",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            (
                "workbench_projection_tail_forbidden:"
                "current_owner_delta_projection_can_satisfy_workbench_shell_readback"
            ),
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            (
                "workbench_projection_tail_forbidden:"
                "domain_progress_transition_runtime_readback_can_satisfy_action_transport"
            ),
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_forbidden:operator_intent_refs_can_satisfy_action_transport",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_missing_false_completion_guards",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_missing_opl_workbench_readback_gate",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in workbench_violations}

    capability_bad_inventory = json.loads(json.dumps(inventory))
    capability = next(
        surface
        for surface in capability_bad_inventory["surfaces"]
        if surface["surface_id"] == "agent_tool_arsenal_scientific_capability_registry"
    )
    capability["authority_boundary"]["mas_selector_authority"] = True
    capability["authority_boundary"]["selection_runtime_owner"] = "med-autoscience"
    capability["wildcard_action_trigger_boundary"]["wildcard_action_triggers_auto_select"] = True
    capability["wildcard_action_trigger_boundary"][
        "requires_explicit_capability_request"
    ] = False
    capability["wildcard_action_trigger_boundary"][
        "wildcard_action_triggers_can_select_without_explicit_capability_request"
    ] = True
    capability["wildcard_action_trigger_boundary"][
        "missing_explicit_capability_request_can_auto_select_wildcard_sidecar"
    ] = True
    capability["wildcard_action_trigger_boundary"][
        "wildcard_sidecar_can_block_current_owner_action"
    ] = True
    capability["retirement_gate"]["live_owner_consumption_soak_required"] = False
    capability["live_owner_consumption_soak_boundary"][
        "live_owner_consumption_soak_proven"
    ] = True
    capability["live_owner_consumption_soak_boundary"][
        "direct_hosted_parity_proven"
    ] = True
    capability["live_owner_consumption_soak_boundary"]["physical_delete_allowed"] = True
    capability["live_owner_consumption_soak_boundary"][
        "required_before_physical_delete"
    ] = "repo_tests_green_ref"
    capability["live_owner_consumption_soak_boundary"]["physical_delete_requires"] = [
        "repo_tests_green_ref"
    ]
    capability["live_owner_consumption_soak_boundary"][
        "required_active_caller_readbacks"
    ] = ["mcp_or_cli_mode_coverage"]
    capability["live_owner_consumption_soak_boundary"][
        "forbidden_completion_claims"
    ] = ["repo_tests_green_as_physical_delete"]

    capability_violations = retirement.validate_runtime_surface_retirement_inventory(
        capability_bad_inventory
    )

    assert {
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "truthy_authority_flag:authority_boundary.mas_selector_authority",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            (
                "truthy_authority_flag:wildcard_action_trigger_boundary."
                "wildcard_action_triggers_auto_select"
            ),
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_authority_forbidden:mas_selector_authority",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_selection_owner_not_opl",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_auto_select_enabled",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_missing_explicit_request_gate",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_can_select_without_explicit_request",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_missing_request_can_auto_select",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_sidecar_can_block_owner_action",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_missing_live_owner_soak_gate",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_claimed:live_owner_consumption_soak_proven",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_claimed:direct_hosted_parity_proven",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_claimed:physical_delete_allowed",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_missing_physical_delete_ref",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_physical_delete_requires_incomplete",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_required_readbacks_incomplete",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_missing_false_completion_guard",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in capability_violations}
