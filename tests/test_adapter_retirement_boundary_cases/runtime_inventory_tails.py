from __future__ import annotations

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
)


def assert_runtime_inventory_tails(surfaces: dict[str, dict]) -> None:
    execution_latest = surfaces["default_executor_execution_latest_wire_projection"]
    assert execution_latest["active_caller_migrated"] is True
    assert execution_latest["current_disposition"] == "physically_retired"
    assert execution_latest["retained_mas_role"] == "none_physically_retired_no_alias"
    assert execution_latest["canonical_surface"] == "owner_callable_adapter_receipt_study_latest"
    assert execution_latest["canonical_wire_path"] == (
        "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    )
    assert execution_latest["legacy_wire_surface"] == "default_executor_dispatch_execution_study_latest"
    assert execution_latest["legacy_wire_path"] == "artifacts/supervision/consumer/default_executor_execution/latest.json"
    assert execution_latest["legacy_wire_readers_tail_open"] == []
    assert execution_latest["legacy_wire_default_reader_fallback_allowed"] is False
    assert execution_latest["legacy_wire_current_reader_fallback_allowed"] is False
    assert execution_latest["legacy_wire_history_replay_fallback_requires_explicit_opt_in"] is True
    assert execution_latest["legacy_wire_history_merge_requires_explicit_opt_in"] is True
    assert execution_latest["current_reader_boundary"] == {
        "current_provider_admission_reads_legacy_wire": False,
        "current_provider_handoff_export_reads_legacy_wire": False,
        "current_recovery_action_reads_legacy_wire": False,
        "default_execution_latest_payload_reads_legacy_wire_by_default": False,
        "default_executor_execution_candidates_reads_legacy_wire_by_default": False,
        "default_executor_receipt_consumption_reads_legacy_wire_by_default": False,
        "default_executor_nonconsumable_closeout_reads_legacy_wire_by_default": False,
        "canonical_missing_outcome": "no_current_owner_callable_receipt",
        "legacy_wire_role": "history_replay_and_provenance_only",
    }
    assert execution_latest["history_replay_boundary"] == {
        "default_executor_execution_candidates_requires_allow_legacy_fallback": True,
        "default_executor_receipt_consumption_requires_allow_legacy_fallback": True,
        "default_executor_nonconsumable_closeout_requires_allow_legacy_fallback": True,
        "execution_latest_payload_requires_allow_legacy_fallback": True,
        "legacy_latest_payload_helper_requires_allow_legacy_fallback": True,
        "can_authorize_provider_admission": False,
        "can_generate_current_handoff": False,
        "can_satisfy_current_recovery_action": False,
    }
    assert set(execution_latest["canonical_first_readers"]) == {
        "provider_admission_parts.provider_admission.persisted_provider_admission_candidates",
        "owner_route_handoff_parts.export_study_projection._current_provider_handoff_execution",
        "owner_route_reconcile_parts.recovery_actions._latest_clean_migration_rehydrate_execution",
    }
    assert "mas_local_execution_ledger_authority" in execution_latest["forbidden_claims"]
    assert "legacy_wire_latest_as_current_provider_admission" in execution_latest["forbidden_claims"]
    assert "legacy_wire_latest_as_current_owner_handoff" in execution_latest["forbidden_claims"]
    assert "legacy_wire_latest_as_current_recovery_action" in execution_latest["forbidden_claims"]
    assert "legacy_stage_closeout_packet_as_provider_admission_authority" in execution_latest[
        "forbidden_claims"
    ]
    assert "legacy_stage_closeout_packet_as_execution_authority" in execution_latest[
        "forbidden_claims"
    ]
    assert "legacy_stage_closeout_packet_as_attempt_lifecycle_authority" in execution_latest[
        "forbidden_claims"
    ]
    assert "dispatch_ref_stage_packet_identity_recovery_as_authority" in execution_latest[
        "forbidden_claims"
    ]
    assert execution_latest["legacy_stage_run_abi_boundary"] == {
        "abi_role": "opl_stagerun_closeout_provenance_identity_recovery_only",
        "stage_id": "domain_owner/default-executor-dispatch",
        "closeout_packet_roots": [
            "artifacts/supervision/consumer/default_executor_execution/*.closeout.json",
            "artifacts/supervision/consumer/stage_attempt_closeouts/*.json",
            "paper/review/*.json",
            "paper/review/default_executor_closeouts/*.json",
        ],
        "allowed_consumption": [
            "terminal_closeout_consumption",
            "typed_blocker_consumption",
            "owner_route_currentness_identity_recovery",
            "paper_stage_log_delta_projection",
        ],
        "latest_wire_surface_is_stage_run_abi": False,
        "stage_closeout_packets_are_latest_wire_fallback": False,
        "stage_closeout_packets_can_authorize_provider_admission": False,
        "stage_closeout_packets_can_authorize_execution": False,
        "stage_closeout_packets_can_create_provider_attempt": False,
        "stage_closeout_packets_can_create_opl_event_outbox_or_stage_run": False,
        "stage_closeout_packets_can_claim_running_or_progress": False,
        "stage_closeout_packets_can_satisfy_current_receipt_without_owner_result": False,
        "dispatch_ref_stage_packet_identity_recovery_is_authority": False,
        "terminal_closeout_consumption_requires_owner_result_or_typed_blocker": True,
        "physical_delete_requires_no_active_stage_run_abi_caller_scan": True,
        "active_stage_run_abi_caller_scan": {
            "status": "active_callers_present_tail_open",
            "no_active_stage_run_abi_caller_proven": False,
            "physical_delete_allowed": False,
            "required_before_physical_delete": (
                "legacy_default_executor_carrier_no_active_stage_run_abi_caller_physical_delete_ref"
            ),
            "active_callers": [
                (
                    "study_transition_receipt_consumption_parts.default_executor_candidates."
                    "default_executor_execution_candidates::_stage_closeout_candidates"
                ),
                "study_transition_receipt_consumption.default_executor_execution_receipt_consumption",
                "study_transition_receipt_consumption.default_executor_execution_nonconsumable_closeout",
                (
                    "study_transition_receipt_consumption_parts.default_executor_followthrough."
                    "default_executor_execution_followthrough_receipt_consumption"
                ),
                "provider_admission_parts.provider_admission_report_closeout_scan",
                "study_outer_loop_work_units",
                "study_progress_parts.opl_current_control_state_terminal_logs",
            ],
            "allowed_consumption": [
                "terminal_closeout_consumption",
                "typed_blocker_consumption",
                "owner_route_currentness_identity_recovery",
                "paper_stage_log_delta_projection",
            ],
            "forbidden_completion_claims": [
                "stage_closeout_provenance_only_as_physical_delete",
                "legacy_stage_run_abi_candidate_as_no_active_caller",
                "stage_closeout_candidate_scan_as_provider_admission_authority",
                "focused_tests_green_as_physical_delete",
            ],
        },
        }
    assert execution_latest["retirement_gate"] == {
        "active_caller_alone_retains_surface": False,
        "live_runtime_readiness_required_for_repo_source_delete": False,
        "no_forbidden_write_proof_proven": True,
        "replacement_parity_proven": True,
        "repo_source_physical_retirement_authorized": True,
        "tombstone_or_provenance_proven": True,
    }

    owner_dispatch = surfaces["domain_owner_action_dispatch"]
    assert owner_dispatch["active_caller_migrated"] is True
    assert owner_dispatch["current_disposition"] == "opl_authorized_owner_callable_adapter"
    assert (
        owner_dispatch["retained_mas_role"]
        == "owner_callable_adapter_policy_boundary_and_typed_blocker_projection"
    )
    assert owner_dispatch["retention_reason"] == (
        "temporary owner callable adapter until OPL DomainProgressTransitionRuntime "
        "provides live authorization and callable execution readback for every active caller"
    )
    assert owner_dispatch["retirement_gate"] == {
        "active_caller_alone_retains_surface": False,
        "completion_claim_requires_live_owner_or_opl_readback": True,
        "live_every_active_caller_soak_required": True,
        "no_active_caller_required_before_physical_delete": True,
        "no_forbidden_write_proof_required": True,
        "replacement_parity_required": True,
        "tombstone_or_provenance_required": True,
    }
    assert owner_dispatch["execution_authorization_boundary"] == {
        "execution_authorization_sources": [
            "trusted_opl_execution_authorization",
            "exact_provider_hosted_stage_attempt",
            "active_opl_provider_attempt_or_lease",
            "bound_opl_domain_progress_transition_runtime_readback",
        ],
        "closeout_binding_authorizes_execution": False,
        "repo_level_authorization_coverage_complete": True,
        "live_every_active_caller_soak_required": True,
        "missing_authorization_outcome": "opl_execution_authorization_required_typed_blocker",
        "provider_attempt_or_lease_required_when_blocked": False,
        "running_provider_attempt_selector_boundary": {
            "selector": "scan_route_currentness.live_provider_attempt_owner_route_from_scan_payload",
            "running_provider_attempt_without_opl_proof_can_select_route": False,
            "running_provider_attempt_without_opl_live_readback_can_select_current_execution": False,
            "weak_running_handoff_role": "observability_only",
            "accepted_proofs": [
                "trusted_opl_execution_authorization",
                "exact_provider_hosted_stage_attempt",
                "bound_opl_domain_progress_transition_runtime_readback",
            ],
            "missing_proof_outcome": "no_current_owner_route_selection",
        },
    }
    assert owner_dispatch["execution_authorization_coverage"] == {
        "coverage_status": "repo_fail_closed_all_supported_actions_live_readback_tail_open",
        "supported_action_types_ref": (
            "src/med_autoscience/controllers/default_executor_action_policy.py#SUPPORTED_ACTION_TYPES"
        ),
        "repo_fail_closed_test_ref": (
            "tests/test_domain_owner_action_dispatch_contract.py::"
            "test_transition_request_projection_requires_opl_execution_authorization_for_every_supported_action"
        ),
        "request_projection_without_opl_proof_outcome": "opl_execution_authorization_required",
        "current_execution_running_proof_requires_opl_live_readback": True,
        "repo_covered_action_families": sorted(SUPPORTED_ACTION_TYPES),
        "live_readback_required_before_retirement": True,
        "live_tail": "live_every_active_caller_soak_or_no_active_caller_proof",
    }
    assert owner_dispatch["active_caller_soak_boundary"] == {
        "status": "live_every_active_caller_soak_tail_open",
        "live_every_active_caller_soak_proven": False,
        "no_active_caller_proven": False,
        "physical_delete_allowed": False,
        "repo_authorization_coverage_can_satisfy_live_soak": False,
        "current_execution_running_proof_can_satisfy_live_soak": False,
        "study_progress_running_proof_can_satisfy_live_soak": False,
        "provider_completion_can_satisfy_dispatch_retirement": False,
        "owner_callable_receipt_projection_can_satisfy_opl_readback": False,
        "opl_execution_authorization_required_blocker_can_satisfy_live_soak": False,
        "provider_handoff_or_completion_can_satisfy_physical_delete": False,
        "required_before_physical_delete": (
            "domain_owner_action_dispatch_live_every_active_caller_soak_or_no_active_caller_ref"
        ),
        "physical_delete_requires": [
            "domain_owner_action_dispatch_execute_dispatch_live_readback_ref",
            "domain_owner_action_dispatch_stage_native_owner_action_live_readback_ref",
            "domain_owner_action_dispatch_provider_hosted_stage_packet_live_readback_ref",
            "domain_owner_action_dispatch_ai_reviewer_authorization_live_readback_ref",
            "domain_owner_action_dispatch_gate_clearing_authorization_live_readback_ref",
            "domain_owner_action_dispatch_current_execution_running_proof_live_readback_ref",
            "domain_owner_action_dispatch_study_progress_running_proof_live_readback_ref",
            "domain_owner_action_dispatch_no_active_owner_callable_adapter_caller_scan_ref",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        ],
        "required_active_caller_readbacks": [
            "execute_dispatch_live_readback",
            "stage_native_owner_action_live_readback",
            "provider_hosted_stage_packet_selection_live_readback",
            "ai_reviewer_provider_hosted_authorization_live_readback",
            "gate_clearing_authorization_live_readback",
            "current_execution_running_proof_live_readback",
            "study_progress_provider_admission_running_proof_live_readback",
        ],
        "active_caller_families": [
            "domain_owner_action_dispatch.execute_dispatch",
            "domain_owner_action_dispatch.stage_native_owner_action",
            "domain_owner_action_dispatch.provider_hosted_exact_stage_packet_selection",
            "domain_owner_action_dispatch.ai_reviewer_provider_hosted_authorization",
            "domain_owner_action_dispatch.gate_clearing_authorization",
            "current_execution_envelope.running_provider_attempt_priority",
            "study_progress.provider_admission_running_proof",
        ],
        "allowed_effect": "execute_only_with_trusted_opl_authorization_or_bound_readback",
        "forbidden_completion_claims": [
            "repo_authorization_coverage_as_live_every_active_caller_soak",
            "active_caller_migrated_as_no_active_caller_proof",
            "focused_tests_green_as_physical_delete",
            "provider_completion_as_dispatch_retirement",
            "current_execution_running_proof_without_opl_readback_as_soak",
            "study_progress_running_proof_without_opl_readback_as_soak",
            "owner_callable_adapter_receipt_projection_as_opl_stage_run_readback",
            "opl_execution_authorization_required_blocker_as_live_soak",
            "provider_handoff_or_completion_as_physical_delete",
        ],
    }
    assert "tests/test_domain_owner_action_dispatch_cases/opl_authorization_boundary.py" in owner_dispatch[
        "verified_by"
    ]
    assert "mas_local_dispatch_authority" in owner_dispatch["forbidden_claims"]
    assert "closeout_binding_as_execution_authorization" in owner_dispatch["forbidden_claims"]
    assert "legacy_caller_exists" not in owner_dispatch["retention_reason"]

    runtime_health = surfaces["runtime_health_kernel"]
    assert runtime_health["current_disposition"] == "read_only_diagnostic_publisher"
    assert runtime_health["active_caller_migrated"] is True
    assert runtime_health["local_event_log_append_from_status_payload"] is False
    assert runtime_health["mas_local_event_append_api_retired"] is True
    assert runtime_health["historical_event_log_role"] == (
        "legacy_fixture_and_explicit_archive_import_provenance_input_only"
    )
    assert runtime_health["retired_code_symbols"] == [
        "runtime_health_kernel.append_runtime_health_event",
        "runtime_health_kernel_parts.event_log.append_runtime_health_event",
    ]
    assert runtime_health["active_caller_boundary"]["active_caller_effect"] == (
        "body_free_runtime_health_diagnostic_projection"
    )
    assert runtime_health["diagnostic_projection_boundary"]["authority"] is False
    assert runtime_health["diagnostic_projection_boundary"][
        "canonical_runtime_action_is_diagnostic_hint"
    ] is True
    assert runtime_health["diagnostic_consumer_gate_boundary"] == {
        "consumer_gate": "runtime_health_decision_gate",
        "decision_authority_owner": "one-person-lab",
        "mas_role": "read_only_diagnostic_consumer",
        "identity_bound_opl_readback_required": True,
        "unbound_opl_ref_can_authorize_decision": False,
        "runtime_health_snapshot_authority_can_authorize_decision": False,
        "canonical_runtime_action_hint_can_authorize_recovery": False,
        "worker_liveness_hint_can_authorize_recovery": False,
        "allowed_decision_source": "opl_runtime_readback",
        "missing_or_cross_identity_readback_outcome": (
            "opl_runtime_readback_required_for_runtime_health_decision"
        ),
    }
    runtime_health_tail = runtime_health["opl_runtime_health_observability_tail_readback"]
    assert runtime_health_tail == {
        "surface_kind": "opl_runtime_health_observability_tail_readback_requirement",
        "status": "tail_open",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "OPL Observability/StageRun/RouteReconciler",
        "required_active_caller_readbacks": [
            "opl_observability_live_readback",
            "opl_route_reconciler_live_readback",
        ],
        "required_tail_readback_families_must_match_same_runtime_identity": True,
        "current_control_or_stage_run_readback_alone_can_satisfy_tail": False,
        "required_before_physical_delete": (
            "runtime_health_kernel_opl_runtime_health_observability_tail_readback_ref"
        ),
        "physical_delete_requires": [
            "opl_observability_live_readback",
            "opl_route_reconciler_live_readback",
            "no_active_diagnostic_projection_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        ],
        "tail_readback_proven": False,
        "no_active_diagnostic_projection_caller_proven": False,
        "physical_delete_allowed": False,
        "mas_diagnostic_projection_can_satisfy_readback": False,
        "mas_runtime_health_snapshot_can_satisfy_readback": False,
        "repo_no_authority_guard_can_satisfy_readback": False,
        "focused_tests_can_satisfy_readback": False,
        "active_diagnostic_projection_caller_scan": {
            "status": "active_diagnostic_projection_callers_present_tail_open",
            "no_active_diagnostic_projection_caller_proven": False,
            "physical_delete_allowed": False,
            "required_before_physical_delete": (
                "runtime_health_kernel_no_active_diagnostic_projection_caller_physical_delete_ref"
            ),
            "active_callers": [
                (
                    "paper_repair_executor_parts.ai_reviewer_currentness::"
                    "runtime_health_snapshot_path_read"
                ),
                (
                    "study_runtime_decision_parts.runtime_health_dominance::"
                    "runtime_health_decision_gate_projection"
                ),
                "runtime_health_kernel.run_runtime_health_kernel::read_runtime_status_projection",
            ],
            "allowed_consumption": [
                "read_runtime_status",
                "open_monitoring_entry",
                "identity_bound_opl_readback_requirement_projection",
            ],
            "forbidden_completion_claims": [
                "diagnostic_projection_active_callers_as_no_active_caller",
                "runtime_health_decision_gate_as_no_active_caller",
                "runtime_health_snapshot_reader_as_opl_observability_readback",
                "active_diagnostic_projection_scan_as_physical_delete",
            ],
        },
        "forbidden_completion_claims": [
            "repo_no_authority_guard_as_runtime_health_tail_readback",
            "mas_runtime_health_snapshot_as_opl_observability_readback",
            "mas_diagnostic_projection_as_route_reconciler_readback",
            "focused_tests_green_as_no_active_runtime_health_caller",
            "runtime_health_decision_gate_as_opl_runtime_readback",
            "current_control_readback_alone_as_runtime_health_tail",
            "stage_run_readback_alone_as_runtime_health_tail",
        ],
    }
    assert runtime_health["retirement_gate"][
        "runtime_health_live_opl_observability_readback_required"
    ] is True
    assert "tests/test_adapter_retirement_boundary.py" in runtime_health["verified_by"]
    assert "mas_owned_attempt_ledger" in runtime_health["forbidden_claims"]

    obligation_actuator = surfaces["domain_health_diagnostic_obligation_actuator"]
    assert obligation_actuator["current_disposition"] == "obligation_readback_projection_consumer"
    assert obligation_actuator["retained_mas_role"] == (
        "consume_only_obligation_outcome_projection_and_mas_typed_blocker_authority_result"
    )
    assert obligation_actuator["validator_role"] == (
        "accepted_owner_answer_or_opl_readback_shape_validator"
    )
    assert obligation_actuator["local_allowed_outcome_table_role"] == (
        "contract_bound_result_shape_validation_not_supervisor_decision_engine"
    )
    assert obligation_actuator["mas_can_choose_supervisor_decision"] is False
    assert obligation_actuator["mas_can_mutate_recovery_obligation_store"] is False
    assert obligation_actuator["mas_can_run_supervisor_decision_engine"] is False
    assert obligation_actuator["mas_can_create_opl_command_event_or_outbox"] is False
    assert obligation_actuator["obligation_readback_boundary"] == {
        "request_projection_is_success_outcome": False,
        "success_outcome_source_families": [
            "opl_runtime_readback",
            "mas_owner_answer_readback",
            "mas_domain_authority_readback",
        ],
        "success_proof_required_for_postcondition_ok": True,
        "success_proof_surface_kind": "dhd_apply_success_proof",
        "success_proof_requires_consumed_readback_identity": True,
        "consumed_readback_identity_surface_kind": "consumed_obligation_readback_identity",
        "mas_domain_authority_readback_requires_authority_boundary": True,
        "read_model_evidence_refs_can_satisfy_success": False,
        "success_proof_forbidden_when_request_projection_only": True,
        "supervisor_disallowed_outcome_is_success": False,
        "readback_result_validator_boundary_required": True,
        "validator_role": "accepted_owner_answer_or_opl_readback_shape_validator",
        "local_allowed_outcome_table_role": (
            "contract_bound_result_shape_validation_not_supervisor_decision_engine"
        ),
        "fail_closed_typed_blocker_surface": "mas_domain_typed_blocker",
        "actuator_can_write_private_blocker_surface": False,
        "opl_obligation_actuator_tail_readback_requirement": obligation_actuator[
            "obligation_readback_boundary"
        ]["opl_obligation_actuator_tail_readback_requirement"],
    }
    tail = obligation_actuator["opl_obligation_actuator_tail_readback"]
    assert tail["status"] == "tail_open"
    assert tail["tail_readback_proven"] is False
    assert tail["no_active_mas_obligation_actuator_caller_proven"] is False
    assert tail["physical_delete_allowed"] is False
    assert tail["mas_policy_projection_can_satisfy_readback"] is False
    assert tail["mas_request_projection_can_satisfy_readback"] is False
    assert obligation_actuator["obligation_readback_boundary"][
        "opl_obligation_actuator_tail_readback_requirement"
    ]["physical_delete_allowed_without_tail_proof"] is False
    assert obligation_actuator["mas_typed_blocker_authority_result_adapter"] == (
        "med_autoscience.controllers.provider_admission_parts."
        "obligation_actuator_parts.mas_domain_typed_blocker_authority_result"
    )
    assert obligation_actuator["typed_blocker_authority_result_adapter_surface"] == (
        "mas_domain_typed_blocker_authority_result_adapter"
    )
    assert obligation_actuator["typed_blocker_authority_result_adapter_boundary"] == {
        "actuator_private_write_authority": False,
        "adapter_role": "persist_mas_domain_typed_blocker_authority_result",
        "authority_owner": "med-autoscience",
        "authority_result_surface": "mas_domain_typed_blocker",
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_run_supervisor_decision_engine": False,
        "can_store_recovery_obligation": False,
        "can_write_controller_decision": False,
        "can_write_publication_eval": False,
        "surface_kind": "mas_domain_typed_blocker_authority_result_boundary",
    }
    assert obligation_actuator["active_caller_boundary"] == {
        "active_caller_effect": "consume_only_readback_projection_with_success_proof_gated_postcondition",
        "active_caller_retains_runtime_authority": False,
        "active_caller_retains_surface": True,
        "completion_claim_requires_live_owner_or_opl_readback": True,
        "physical_delete_requires": [
            "opl_recovery_obligation_store_active_caller",
            "opl_supervisor_decision_engine_active_caller",
            "no_active_caller_scan",
            "replacement_parity_ref",
            "owner_retirement_decision_ref",
            "tombstone_or_provenance_ref",
        ],
        "request_projection_only_can_satisfy_success": False,
    }
    assert "mas_owned_recovery_obligation_store" in obligation_actuator["forbidden_claims"]
    assert "mas_owned_supervisor_decision_engine" in obligation_actuator["forbidden_claims"]
    assert "mas_policy_request_projection_as_success_outcome" in obligation_actuator["forbidden_claims"]
    assert obligation_actuator["can_write_fail_closed_typed_control_blocker"] is False
    assert obligation_actuator["actuator_direct_filesystem_write_retired"] is True
    assert obligation_actuator["actuator_can_write_private_blocker_surface"] is False

    workbench_projection = surfaces[
        "progress_portal_study_workbench_overview_action_projection"
    ]
    assert workbench_projection["current_disposition"] == "read_only_workbench_projection"
    assert workbench_projection["retained_mas_role"] == (
        "body_free_workbench_read_model_projection"
    )
    assert workbench_projection["projection_boundary"] == {
        "can_authorize_provider_admission": False,
        "can_authorize_worker_attempt": False,
        "can_execute": False,
        "can_emit_runtime_command": False,
        "can_generate_action": False,
        "can_open_runtime_endpoint": False,
        "can_transport_operator_action": False,
        "legacy_operator_focus_role": "diagnostic_legacy_projection_input",
        "legacy_next_system_action_role": "diagnostic_legacy_projection_input",
        "must_not_be_used_as_next_action_authority": True,
        "must_not_be_used_as_paper_progress": True,
        "must_not_be_used_as_provider_admission": True,
        "must_not_be_used_as_publication_ready": True,
        "next_system_action_role": "read_only_owner_delta_summary",
        "operator_intent_refs_are_inert": True,
        "projection_only": True,
        "requires_opl_current_control_readback": True,
    }
    workbench_tail = workbench_projection["opl_workbench_shell_readback_tail"]
    assert workbench_tail == {
        "surface_kind": "opl_workbench_shell_readback_tail_requirement",
        "status": "tail_open",
        "runtime_owner": "one-person-lab",
        "runtime_kind": (
            "OPL Workbench Shell/current-control/DomainProgressTransitionRuntime readback"
        ),
        "required_active_caller_readbacks": [
            "opl_workbench_shell_action_transport_readback",
            "opl_current_control_readback",
            "opl_domain_progress_transition_runtime_readback",
        ],
        "required_before_physical_delete": (
            "progress_portal_study_workbench_overview_action_projection_"
            "opl_workbench_shell_readback_tail_ref"
        ),
        "physical_delete_requires": [
            "opl_workbench_shell_action_transport_readback",
            "opl_current_control_readback",
            "opl_domain_progress_transition_runtime_readback",
            "no_active_workbench_projection_action_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        ],
        "tail_readback_proven": False,
        "no_active_workbench_projection_action_caller_proven": False,
        "physical_delete_allowed": False,
        "current_owner_delta_projection_can_satisfy_workbench_shell_readback": False,
        "domain_progress_transition_runtime_readback_can_satisfy_action_transport": False,
        "mas_portal_projection_can_satisfy_readback": False,
        "mas_next_system_action_summary_can_satisfy_readback": False,
        "operator_intent_refs_can_satisfy_action_transport": False,
        "repo_no_authority_guard_can_satisfy_readback": False,
        "focused_tests_can_satisfy_readback": False,
        "forbidden_completion_claims": [
            "mas_portal_projection_as_opl_workbench_shell_readback",
            "mas_next_system_action_summary_as_action_transport_readback",
            "operator_intent_refs_as_workbench_action_transport",
            "current_owner_delta_summary_as_current_control_readback",
            "domain_progress_transition_runtime_readback_as_workbench_action_transport",
            "current_owner_delta_projection_as_workbench_shell_readback",
            "repo_no_authority_guard_as_workbench_tail_readback",
            "focused_tests_green_as_no_active_workbench_projection_caller",
        ],
    }
    assert workbench_projection["retirement_gate"][
        "opl_workbench_shell_readback_required"
    ] is True
    assert "workbench_projection_clean_as_runtime_ready" in workbench_projection[
        "forbidden_claims"
    ]

    capability_registry = surfaces["agent_tool_arsenal_scientific_capability_registry"]
    assert capability_registry["active_caller_migrated"] is True
    assert capability_registry["current_disposition"] == "opl_capability_runtime_projection"
    assert capability_registry["retained_mas_role"] == (
        "capability_planning_projection_and_owner_consumption_evidence_shape"
    )
    assert capability_registry["replacement_surface"] == (
        "OPL Capability Runtime / Tool Arsenal selector and invocation runtime"
    )
    assert capability_registry["authority_boundary"] == {
        "selection_runtime_owner": "one-person-lab",
        "capability_runtime_owner": "one-person-lab",
        "capability_runtime_kind": "OPL Capability Runtime",
        "hosted_opl_capability_runtime_required": True,
        "mas_selector_authority": False,
        "mas_tool_invocation_runtime_authority": False,
        "can_create_default_selector": False,
        "can_start_always_on_sidecar": False,
        "can_authorize_provider_admission": False,
        "can_authorize_worker_attempt": False,
        "can_authorize_publication_ready": False,
        "can_claim_paper_progress": False,
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
        "missing_refs_trigger_mutating_invocation": False,
        "stores_body": False,
    }
    assert capability_registry["wildcard_action_trigger_boundary"] == {
        "wildcard_action_triggers_auto_select": False,
        "requires_explicit_capability_request": True,
        "wildcard_action_triggers_can_select_without_explicit_capability_request": False,
        "missing_explicit_capability_request_can_auto_select_wildcard_sidecar": False,
        "wildcard_sidecar_can_block_current_owner_action": False,
        "explicit_request_fields": [
            "capability_families",
            "capability_family",
            "route_required_ref_families",
            "route_required_ref_family",
        ],
        "wildcard_capabilities": [
            "evo_scientist_progress_sidecar",
            "light_external_skill_content_advisory",
        ],
        "wildcard_policy_ref": (
            "contracts/agent_tool_arsenal.json#/scientific_capability_registry.default_policy"
        ),
    }
    assert "mas_owned_tool_selector" in capability_registry["forbidden_claims"]
    assert "wildcard_action_trigger_as_default_selector" in capability_registry[
        "forbidden_claims"
    ]
    assert capability_registry["live_owner_consumption_soak_boundary"] == {
        "status": "live_owner_consumption_soak_and_direct_hosted_parity_tail_open",
        "live_owner_consumption_soak_proven": False,
        "direct_hosted_parity_proven": False,
        "no_active_caller_proven": False,
        "physical_delete_allowed": False,
        "required_before_physical_delete": (
            "agent_tool_arsenal_live_owner_consumption_soak_and_direct_hosted_parity_ref"
        ),
        "physical_delete_requires": [
            "agent_tool_arsenal_live_owner_consumption_soak_current_owner_delta_readback_ref",
            "agent_tool_arsenal_explicit_capability_request_resolution_live_readback_ref",
            "agent_tool_arsenal_direct_hosted_tool_invocation_runtime_parity_ref",
            "agent_tool_arsenal_no_active_registry_projection_caller_scan_ref",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        ],
        "required_active_caller_readbacks": [
            "current_owner_delta_bound_capability_consumption_live_readback",
            "explicit_capability_request_resolution_live_readback",
            "direct_hosted_tool_invocation_runtime_parity_readback",
        ],
        "allowed_consumption": [
            "current_owner_delta_bound_capability_projection",
            "explicit_capability_request_resolution_evidence",
        ],
        "forbidden_completion_claims": [
            "capability_registry_contract_as_live_owner_consumption_soak",
            "hosted_opl_runtime_requirement_as_direct_hosted_parity",
            "mcp_or_cli_mode_coverage_as_direct_hosted_parity",
            "wildcard_guard_as_live_owner_consumption_soak",
            "capability_request_projection_as_paper_progress",
            "registry_projection_no_active_scan_as_physical_delete",
            "repo_tests_green_as_physical_delete",
        ],
    }
    assert capability_registry["retirement_gate"]["live_owner_consumption_soak_required"] is True
    assert capability_registry["retirement_gate"]["direct_hosted_parity_required"] is True

    runtime_storage = surfaces["runtime_storage_maintenance"]
    assert runtime_storage["generic_runtime_owner"] == "one-person-lab"
    assert runtime_storage["mas_owner_claim_allowed"] is False
    assert runtime_storage["compatibility_alias_allowed"] is False
    assert (
        runtime_storage["current_disposition"]
        == "opl_authorized_storage_maintenance_callable_adapter_live_takeover_tail_open"
    )
    assert runtime_storage["authority_boundary"] == {
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_claim_runtime_currentness": False,
        "can_claim_paper_progress": False,
        "can_authorize_generic_cleanup_policy": False,
        "can_authorize_artifact_mutation": False,
        "can_authorize_publication_ready": False,
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
        "stores_body": False,
        "dry_run_projection_only": True,
        "mutates_runtime_storage_payload_only_when_opl_authorized": True,
    }
    assert runtime_storage["apply_gate"] == {
        "required_authorization_surface": "opl_runtime_storage_maintenance_authorization",
        "proof_surface": "opl_runtime_storage_maintenance_authorization_proof",
        "required_for_workspace_apply": True,
        "required_for_direct_quest_physical_apply": True,
        "dry_run_requires_authorization": False,
        "restore_proof_canary_requires_authorization": False,
        "refs_only_state_index_only_requires_authorization": False,
        "planned_retention_projection_requires_authorization": False,
        "must_bind": [
            "operation",
            "maintenance_surface",
            "workspace_root_or_quest_root",
            "outcome",
            "authorization_ref",
        ],
        "accepted_operations": [
            "workspace_storage_apply",
            "quest_runtime_storage_apply",
        ],
        "accepted_maintenance_surfaces": [
            "workspace_runtime_storage_maintenance",
            "quest_runtime_storage_maintenance",
        ],
        "missing_or_invalid_authorization_status": (
            "blocked_opl_runtime_storage_maintenance_authorization_required"
        ),
        "typed_blocker": "opl_runtime_storage_maintenance_authorization_required",
        "applies_to_operations": [
            "workspace_storage_apply",
            "quest_runtime_storage_backend_apply",
            "runtime_oversized_jsonl_slimming_apply",
            "restore_proof_compaction_apply",
            "archive_retention_apply",
            "report_retention_apply",
            "semantic_process_retention_apply",
            "git_temp_garbage_delete_apply",
            "workspace_root_git_reinitialize_apply",
            "workspace_root_git_retirement_apply",
            "delete_safe_cache_apply",
        ],
    }
    assert "mas_owned_generic_runtime" in runtime_storage["forbidden_claims"]
    assert "runtime_storage_apply_as_paper_progress" in runtime_storage["forbidden_claims"]
    assert "provider_completion_as_domain_ready" in runtime_storage["forbidden_claims"]
    storage_tail = runtime_storage["opl_runtime_storage_maintenance_tail_readback"]
    assert storage_tail == {
        "surface_kind": "opl_runtime_storage_maintenance_tail_readback_requirement",
        "status": "tail_open",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "OPL RuntimeStorageMaintenance/RestoreRetentionShell/StateIndex",
        "required_active_caller_readbacks": [
            "opl_runtime_storage_policy_live_readback",
            "opl_restore_retention_shell_live_readback",
            "opl_state_index_storage_ref_readback",
        ],
        "required_before_physical_delete": (
            "runtime_storage_maintenance_opl_runtime_storage_maintenance_tail_readback_ref"
        ),
        "physical_delete_requires": [
            "opl_runtime_storage_policy_live_readback",
            "opl_restore_retention_shell_live_readback",
            "opl_state_index_storage_ref_readback",
            "no_active_storage_maintenance_adapter_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        ],
        "tail_readback_proven": False,
        "no_active_storage_maintenance_adapter_caller_proven": False,
        "physical_delete_allowed": False,
        "apply_authorization_can_satisfy_live_takeover": False,
        "dry_run_projection_can_satisfy_live_takeover": False,
        "restore_canary_can_satisfy_live_takeover": False,
        "refs_only_index_projection_can_satisfy_live_takeover": False,
        "archive_report_retention_plan_can_satisfy_live_takeover": False,
        "attempt_evidence_capsule_can_satisfy_live_takeover": False,
        "planned_retention_projection_can_satisfy_live_takeover": False,
        "workspace_root_git_retirement_receipt_can_satisfy_live_takeover": False,
        "repo_tests_can_satisfy_live_takeover": False,
        "forbidden_completion_claims": [
            "opl_storage_maintenance_authorization_as_live_storage_policy_takeover",
            "runtime_storage_apply_gate_as_live_takeover",
            "runtime_storage_dry_run_projection_as_live_takeover",
            "restore_proof_canary_as_live_takeover",
            "refs_only_state_index_projection_as_storage_takeover",
            "archive_retention_plan_as_live_takeover",
            "report_retention_plan_as_live_takeover",
            "attempt_evidence_capsule_plan_as_storage_takeover",
            "semantic_process_retention_plan_as_live_takeover",
            "workspace_root_git_retirement_receipt_as_physical_delete",
            "storage_maintenance_receipt_as_physical_delete",
            "repo_tests_green_as_runtime_storage_physical_delete",
        ],
    }
    assert runtime_storage["retirement_gate"]["active_caller_alone_retains_surface"] is False

    lifecycle_retention = surfaces["runtime_lifecycle_payload_retention"]
    lifecycle_tail = lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"]
    assert lifecycle_tail == {
        "surface_kind": "opl_runtime_lifecycle_maintenance_tail_readback_requirement",
        "status": "tail_open",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "OPL RuntimeLifecycleCleanup/RetentionPolicy",
        "required_active_caller_readbacks": [
            "opl_runtime_lifecycle_cleanup_policy_live_readback",
            "opl_runtime_retention_policy_live_readback",
        ],
        "required_before_physical_delete": (
            "runtime_lifecycle_payload_retention_opl_runtime_lifecycle_maintenance_tail_readback_ref"
        ),
        "physical_delete_requires": [
            "opl_runtime_lifecycle_cleanup_policy_live_readback",
            "opl_runtime_retention_policy_live_readback",
            "no_active_lifecycle_maintenance_adapter_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        ],
        "tail_readback_proven": False,
        "no_active_lifecycle_maintenance_adapter_caller_proven": False,
        "physical_delete_allowed": False,
        "apply_authorization_can_satisfy_live_takeover": False,
        "dry_run_plan_can_satisfy_live_takeover": False,
        "maintenance_receipt_can_satisfy_live_takeover": False,
        "sqlite_sidecar_repair_receipt_can_satisfy_live_takeover": False,
        "cold_payload_externalization_receipt_can_satisfy_live_takeover": False,
        "repo_tests_can_satisfy_live_takeover": False,
        "forbidden_completion_claims": [
            "opl_maintenance_authorization_as_live_cleanup_policy_takeover",
            "runtime_lifecycle_apply_gate_as_live_takeover",
            "runtime_lifecycle_dry_run_plan_as_live_takeover",
            "runtime_lifecycle_receipt_as_physical_delete",
            "sqlite_sidecar_repair_receipt_as_live_takeover",
            "cold_payload_externalization_receipt_as_physical_delete",
            "payload_retention_plan_as_live_takeover",
            "repo_tests_green_as_runtime_lifecycle_physical_delete",
        ],
    }
    assert lifecycle_retention["retirement_gate"]["active_caller_alone_retains_surface"] is False
