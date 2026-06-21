from __future__ import annotations


def assert_runtime_inventory_core(surfaces: dict[str, dict]) -> None:
    carrier_persistence = surfaces["domain_action_request_materializer_local_carrier_persistence_api"]
    assert carrier_persistence["retained_mas_role"] == "none_physically_retired_no_alias"
    assert carrier_persistence["replacement_surface"] == (
        "domain_progress_transition_requests plus OPL DomainProgressTransitionRuntime durable carrier"
    )
    assert set(carrier_persistence["retired_symbols"]) == {
        "persist_default_executor_dispatches",
        "persist_request_packets",
        "persist_consumer_payload",
        "request_packet_for_persistence",
        "medical_paper_readiness_packet_for_persistence",
        "source_workflow_ref_for_ai_reviewer_request",
    }
    assert "mas_local_dispatch_carrier_persistence" in carrier_persistence["forbidden_claims"]
    assert "mas_local_request_packet_persistence" in carrier_persistence["forbidden_claims"]

    default_dispatch = surfaces["default_executor_dispatch_request"]
    assert default_dispatch["legacy_carrier_fallback_only"] is True
    assert (
        default_dispatch["priority_boundary"]
        == "current_control_transition_request_precedes_legacy_dispatch_carrier"
    )
    assert default_dispatch["active_caller_boundary"] == {
        "active_caller_effect": "opl_domain_progress_transition_runtime_intake_only",
        "active_caller_retains_authority": False,
        "active_caller_retains_runtime_authority": False,
        "active_caller_retains_surface": False,
        "completion_claim_requires_live_owner_or_opl_readback": True,
        "provider_admission_pending": False,
        "provider_attempt_or_lease_required": False,
        "transition_request_pending_only": True,
    }
    assert default_dispatch["legacy_residue_cleanup_surface"] == {
        "active_cli_command_retired": True,
        "active_compat_test_retired": True,
        "active_controller_module_retired": True,
        "current_entry_allowed": False,
        "historical_receipt_ref": (
            "contracts/standard_agent_completion_evidence_status.json#/"
            "historical_default_executor_dispatch_residue_cleanup_receipt"
        ),
        "retired_command": "default-executor-dispatch-residue-cleanup",
        "retired_module": "med_autoscience.controllers.default_executor_dispatch_residue_cleanup",
    }
    assert default_dispatch["legacy_stage_run_abi_provenance_boundary"] == {
        "carrier_kind": "opl_domain_progress_transition_request_carrier",
        "legacy_surface": "default_executor_dispatch_request",
        "mas_can_create_stage_run": False,
        "mas_can_mark_provider_admission": False,
        "mas_can_mark_provider_running": False,
        "provider_admission_pending": False,
        "running_provider_attempt_provenance_without_opl_live_readback": "observability_only",
        "provenance_only_until_opl_readback": True,
        "requires_opl_domain_progress_transition_runtime_intake": True,
        "task_kind_retained_for_opl_stage_run_abi": "domain_owner/default-executor-dispatch",
        "transition_request_pending_only": True,
    }
    assert default_dispatch["opl_default_executor_carrier_tail_readback"] == {
        "surface_kind": "opl_default_executor_carrier_tail_readback_requirement",
        "status": "tail_open",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime/TransactionalOutbox/StageRun",
        "required_active_caller_readbacks": [
            "opl_domain_progress_transition_runtime_live_readback",
            "opl_command_event_outbox_live_readback",
            "opl_stagerun_owner_callable_adapter_live_readback",
        ],
        "required_before_physical_delete": (
            "default_executor_dispatch_request_opl_default_executor_carrier_tail_readback_ref"
        ),
        "physical_delete_requires": [
            "opl_domain_progress_transition_runtime_live_readback",
            "opl_command_event_outbox_live_readback",
            "opl_stagerun_owner_callable_adapter_live_readback",
            "no_active_default_executor_carrier_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "owner_retirement_decision_ref",
            "tombstone_or_provenance_ref",
        ],
        "tail_readback_proven": False,
        "no_active_default_executor_carrier_caller_proven": False,
        "physical_delete_allowed": False,
        "legacy_carrier_provenance_can_satisfy_readback": False,
        "transition_request_pending_can_satisfy_readback": False,
        "repo_no_authority_guard_can_satisfy_readback": False,
        "focused_tests_can_satisfy_readback": False,
        "request_only_carrier_can_authorize_provider_admission": False,
        "request_only_carrier_can_claim_running_or_progress": False,
        "forbidden_completion_claims": [
            "legacy_carrier_provenance_as_default_executor_carrier_tail_readback",
            "transition_request_pending_as_opl_live_readback",
            "repo_no_authority_guard_as_default_executor_carrier_tail_readback",
            "focused_tests_green_as_no_active_default_executor_carrier_caller",
            "request_only_carrier_as_provider_admission",
            "request_only_carrier_as_running_or_progress",
        ],
    }
    assert default_dispatch["retirement_gate"] == {
        "active_caller_alone_retains_surface": False,
        "live_runtime_readiness_required_for_repo_source_delete": False,
        "no_forbidden_write_proof_proven": True,
        "replacement_parity_proven": True,
        "repo_source_physical_retirement_authorized": True,
        "tombstone_or_provenance_proven": True,
    }
    assert default_dispatch["projection_counting_boundary"] == {
        "opl_live_readback_candidates_count_as": "provider_admission_pending",
        "request_only_candidates_count_as": "transition_request_pending",
        "opl_log_derived_readback_candidates_count_as": "deprecated_diagnostic_only",
        "mutually_exclusive_pending_counts": True,
        "forbidden_double_count": (
            "same_identity_transition_request_pending_and_provider_admission_pending"
        ),
    }
    assert default_dispatch["arbiter_authority_boundary"] == {
        "provider_admission_readback_requires_opl_live_readback": True,
        "event_or_outbox_fragment_is_provider_admission_authority": False,
        "request_without_live_readback_effect": "transition_request_pending_non_advancing_apply_required",
        "missing_live_readback_no_progress_signal": "transition_request_waits_for_opl_runtime",
        "anti_loop_classification": "non_advancing_apply_required",
        "mas_can_authorize_provider_admission": False,
        "mas_can_create_opl_outbox_event_or_stage_run": False,
        "running_provider_attempt_without_opl_live_readback_is_observability_only": True,
        "running_provider_attempt_can_consume_provider_admission_only_with_same_identity_opl_live_readback": True,
        "matching_provider_admission_candidate_may_supply_running_proof_readback": True,
        "non_matching_provider_admission_candidate_can_supply_running_proof_readback": False,
    }

    legacy_alias = surfaces["owner_callable_adapter_legacy_dispatch_projection_alias"]
    assert legacy_alias["retained_mas_role"] == "none_physically_retired_no_alias"
    assert legacy_alias["replacement_surface"] == (
        "explicit domain_progress_transition_requests projection plus OPL DomainProgressTransitionRuntime readback"
    )
    assert legacy_alias["retired_symbols"] == [
        "default_executor_dispatches owner_callable_adapters fallback alias"
    ]
    assert "legacy_default_executor_dispatches_as_owner_callable_adapters" in legacy_alias["forbidden_claims"]

    current_default_preview = surfaces["domain_action_request_materializer_current_default_executor_dispatches_api"]
    assert current_default_preview["retained_mas_role"] == "none_physically_retired_no_alias"
    assert current_default_preview["replacement_surface"] == (
        "current_owner_callable_adapters projection plus OPL DomainProgressTransitionRuntime readback"
    )
    assert set(current_default_preview["retired_symbols"]) == {
        "current_default_executor_dispatches",
        "domain_action_request_materializer_parts.current_default_executor_dispatches",
    }
    assert "legacy_current_default_executor_dispatches_preview_api" in current_default_preview["forbidden_claims"]

    owner_callable_projection = surfaces["domain_action_request_materializer_owner_callable_adapter_projection"]
    assert owner_callable_projection["active_caller_migrated"] is True
    assert owner_callable_projection["current_disposition"] == "physically_retired"
    assert owner_callable_projection["retained_mas_role"] == "none_physically_retired_no_alias"
    assert owner_callable_projection["canonical_surface"] == "domain_progress_transition_requests"
    assert owner_callable_projection["retirement_gate"] == {
        "active_caller_alone_retains_surface": False,
        "live_runtime_readiness_required_for_repo_source_delete": False,
        "no_forbidden_write_proof_proven": True,
        "replacement_parity_proven": True,
        "repo_source_physical_retirement_authorized": True,
        "tombstone_or_provenance_proven": True,
    }
    materializer_projection_tail = owner_callable_projection[
        "opl_materializer_projection_tail_readback"
    ]
    assert materializer_projection_tail == {
        "surface_kind": "opl_materializer_projection_tail_readback_requirement",
        "status": "tail_open",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "OPL DomainProgressTransitionRuntime/StageRun",
        "required_active_caller_readbacks": [
            "opl_domain_progress_transition_runtime_live_readback",
            "opl_stagerun_owner_callable_adapter_readback",
        ],
        "required_before_physical_delete": (
            "domain_action_request_materializer_projection_"
            "opl_runtime_tail_readback_or_no_active_caller_ref"
        ),
        "physical_delete_requires": [
            "opl_domain_progress_transition_runtime_live_readback",
            "opl_stagerun_owner_callable_adapter_readback",
            "no_active_materializer_projection_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        ],
        "tail_readback_proven": False,
        "no_active_materializer_projection_caller_proven": False,
        "physical_delete_allowed": False,
        "projection_demoted_can_satisfy_live_readback": False,
        "legacy_alias_retired_can_satisfy_live_readback": False,
        "refs_only_projection_can_satisfy_live_readback": False,
        "focused_tests_can_satisfy_live_readback": False,
        "repo_no_authority_guard_can_satisfy_live_readback": False,
        "forbidden_completion_claims": [
            "materializer_projection_demoted_as_opl_transition_readback",
            "request_tasks_alias_retired_as_no_active_caller",
            "refs_only_transition_projection_as_physical_delete",
            "repo_no_authority_guard_as_live_materializer_tail_readback",
            "focused_tests_green_as_materializer_physical_delete",
        ],
    }
    assert owner_callable_projection["legacy_projection_boundary"] == {
        "canonical_transition_request_surface": "domain_progress_transition_requests",
        "legacy_diagnostic_ref_helper": (
            "owner_callable_adapter_projection.legacy_owner_callable_adapter_refs"
        ),
        "legacy_public_body_reader_returns_active_carriers": False,
        "legacy_public_body_reader_status": "retired_returns_empty",
        "legacy_raw_body_reader_scope": "internal_projection_to_refs_only_diagnostics",
        "owner_callable_adapter_counts_authority": False,
        "owner_callable_adapter_item_can_create_success_outcome": False,
        "owner_callable_adapter_item_diagnostic_only": True,
        "owner_callable_adapter_item_readiness_authority": False,
        "owner_callable_adapter_list_can_create_success_outcome": False,
        "owner_callable_adapter_list_diagnostic_only": True,
        "owner_callable_adapter_readiness_authority": False,
        "refs_only_diagnostics_body_omitted": True,
    }
    assert "ready_owner_callable_adapter_count_as_provider_admission" in owner_callable_projection[
        "forbidden_claims"
    ]
    assert "owner_callable_adapters_as_success_outcome" in owner_callable_projection[
        "forbidden_claims"
    ]
    assert owner_callable_projection["verified_by"] == [
        (
            "tests/test_adapter_retirement_boundary.py::"
            "test_public_owner_callable_adapter_reader_is_not_active_carrier"
        ),
        (
            "tests/test_adapter_retirement_boundary.py::"
            "test_transition_request_counts_are_canonical_not_legacy_adapter_counts"
        ),
        (
            "tests/test_domain_action_request_materializer.py::"
            "test_materialize_domain_action_requests_only_writes_current_owner_dispatch_for_route_epoch"
        ),
        (
            "tests/domain_action_request_materializer_cases/test_canonical_request_surface.py::"
            "test_materialize_domain_action_requests_writes_quality_repair_request_to_canonical_requests_surface"
        ),
        (
            "tests/domain_action_request_materializer_cases/test_canonical_request_surface.py::"
            "test_canonical_transition_request_projection_carries_dispatcher_boundary_fields"
        ),
        (
            "tests/domain_action_request_materializer_cases/test_ai_reviewer_record_handoff.py::"
            "test_materialize_ai_reviewer_dispatch_uses_record_handoff_when_latest_is_forbidden_by_owner_reason"
        ),
        (
            "tests/domain_action_request_materializer_cases/test_ai_reviewer_record_handoff.py::"
            "test_materialize_ai_reviewer_record_handoff_suppresses_ready_dispatch_after_current_record"
        ),
    ]

    for surface_id in (
        "domain_action_request_materializer_request_tasks_projection",
        "domain_action_request_materializer_canonical_transition_request_body_projection",
    ):
        materializer_projection = surfaces[surface_id]
        assert materializer_projection["retirement_gate"][
            "repo_source_physical_retirement_authorized"
        ] is True
        assert materializer_projection["retirement_gate"][
            "live_runtime_readiness_required_for_repo_source_delete"
        ] is False
        assert (
            materializer_projection["opl_materializer_projection_tail_readback"]
            == materializer_projection_tail
        )
