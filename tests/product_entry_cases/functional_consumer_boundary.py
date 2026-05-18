from __future__ import annotations

import importlib
from pathlib import Path

from .shared import make_profile


def test_product_entry_manifest_exposes_functional_consumer_boundary(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    boundary = manifest["functional_consumer_boundary"]

    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["status"] == "opl_consumes_generic_surfaces_mas_retains_domain_authority_pack"
    assert boundary["consumer_role"] == "domain_authority_pack_thin_program_surface"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert boundary["no_active_caller_required"] is True
    assert boundary["mas_does_not_own"] == [
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_transition_runner",
        "generic_workbench",
        "generic_memory_locator",
        "generic_artifact_lifecycle",
        "generic_observability",
    ]
    assert set(boundary["mas_retains"]) == {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "memory_writeback_decision",
        "domain_transition_table",
        "owner_receipt",
        "typed_blocker",
        "safe_action_refs",
    }
    pack_input = boundary["declarative_pack_compiler_input"]
    assert pack_input["surface_kind"] == "mas_declarative_pack_compiler_input"
    assert pack_input["compiler_owner"] == "one-person-lab"
    assert pack_input["pack_id"] == "mas-medical-research-pack"
    assert pack_input["pack_role"] == "domain_authority_pack_input_not_generated_shell_owner"
    assert [item["input_id"] for item in pack_input["input_refs"]] == [
        "domain_descriptor",
        "stage_graph",
        "action_intents",
        "domain_transition_table",
        "publication_route_memory_policy",
        "artifact_authority_policy",
        "source_readiness_policy",
        "receipt_schema",
        "no_forbidden_write_contract",
    ]
    assert pack_input["compiler_outputs_expected"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]
    assert pack_input["mas_long_term_code_owner"] == "minimal_authority_functions_only"
    assert pack_input["must_not_generate_or_claim_domain_authority"] is True
    handoff = boundary["generated_surface_handoff"]
    assert handoff["surface_kind"] == "mas_generated_surface_handoff"
    assert handoff["generated_surface_owner"] == "one-person-lab"
    assert handoff["current_mas_role"] == "handwritten_migration_bridge"
    assert handoff["long_term_mas_owner"] is False
    assert handoff["mas_handwritten_shell_expansion_allowed"] is False
    handoff_by_id = {item["surface_id"]: item for item in handoff["handoff_surfaces"]}
    assert set(handoff_by_id) == set(pack_input["compiler_outputs_expected"])
    assert handoff_by_id["cli"]["target_role"] == "opl_generated_command_surface"
    assert handoff_by_id["mcp"]["target_role"] == "opl_generated_mcp_descriptor_surface"
    assert handoff_by_id["skill"]["target_role"] == "opl_generated_skill_descriptor_surface"
    assert handoff_by_id["product_entry"]["target_role"] == "opl_generated_product_entry_surface"
    assert handoff_by_id["sidecar"]["target_role"] == "opl_generated_sidecar_handoff_surface"
    assert handoff_by_id["status"]["target_role"] == "opl_generated_status_wrapper_over_mas_truth_refs"
    assert handoff_by_id["workbench"]["target_role"] == (
        "opl_hosted_workbench_shell_consuming_mas_refs"
    )
    assert handoff_by_id["projection_shell"]["target_role"] == "opl_generated_projection_shell"
    assert handoff_by_id["test_lane_harness"]["target_role"] == (
        "opl_generated_harness_consumer_over_mas_pack"
    )
    authority = boundary["minimal_authority_function_manifest"]
    assert authority["surface_kind"] == "mas_minimal_authority_function_manifest"
    assert authority["status"] == "minimal_authority_functions_only"
    assert authority["semantic_model"] == (
        "ai_first_stage_quality_gate_boundaries_not_script_function_verdicts"
    )
    assert authority["allowed_judgment_modes"] == [
        "ai_first_stage_gate",
        "ai_first_record_validator",
        "mechanical_guard",
        "refs_only_adapter",
    ]
    assert authority["verdict_function_model_retired"] is True
    assert authority["gate_validator_ref"] == (
        "src/med_autoscience/controllers/ai_first_private_authority.py::"
        "validate_ai_first_private_authority_gate"
    )
    assert authority["runtime_enforcement_status"] == "contract_validator_landed"
    assert authority["program_output_policy"] == (
        "programs_validate_ai_first_stage_gate_records_and_emit_receipts_or_typed_blockers_only"
    )
    assert authority["standard_stage_gate_output_model"] == {
        "executor_output": "stage_work_artifact_source_evidence_refs_and_execution_receipt",
        "reviewer_output": "independent_ai_reviewer_or_auditor_gate_record",
        "program_output": "provenance_currentness_schema_receipt_or_typed_blocker",
        "self_review_closes_gate": False,
    }
    assert authority["requires_ai_first_record"] is True
    assert authority["boundary_ids"] == [
        "publication_quality_stage_gate_boundary",
        "ai_reviewer_quality_stage_gate_boundary",
        "artifact_mutation_stage_gate_boundary",
        "publication_route_memory_accept_reject_stage_gate_boundary",
        "source_readiness_stage_gate_boundary",
    ]
    assert authority["forbidden_mechanical_decision_surfaces"] == [
        "script_exit_code_as_publication_quality_verdict",
        "function_return_value_as_ai_reviewer_quality_decision",
        "test_pass_as_artifact_mutation_authorization",
        "queue_completion_as_publication_route_memory_accept_reject",
        "file_presence_as_source_readiness_verdict",
    ]
    independent_policy = authority["independent_executor_reviewer_agent_policy"]
    assert independent_policy["required"] is True
    assert independent_policy["separate_invocation_required"] is True
    assert independent_policy["separate_context_record_required"] is True
    assert independent_policy["separate_task_record_required"] is True
    assert independent_policy["separate_receipt_required"] is True
    assert independent_policy["self_review_closes_quality_gate"] is False
    assert independent_policy["missing_independent_reviewer_record_policy"] == (
        "fail_closed_or_route_back"
    )
    assert authority["function_ids"] == [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "artifact_mutation_authorization",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
        "owner_receipt_signer",
        "medical_helper_implementation",
    ]
    assert authority["function_count"] == 7
    assert {item["function_id"] for item in authority["functions"]} == set(authority["function_ids"])
    assert {item["owner"] for item in authority["functions"]} == {"med-autoscience"}
    boundary_by_id = {item["boundary_id"]: item for item in authority["stage_quality_gate_boundaries"]}
    assert set(boundary_by_id) == set(authority["boundary_ids"])
    assert {item["program_role"] for item in boundary_by_id.values()} == {
        "validator",
        "materializer",
        "guard",
    }
    for item in boundary_by_id.values():
        assert item["requires_ai_first_record"] is True
        assert item["route_back_semantics"].startswith("route_back_to_")
        assert item["typed_blocker_semantics"].endswith("_blocker")
        assert item["required_record_refs"]
        assert any(
            "stage_quality_pack:" in ref
            or ref in {"AI reviewer workflow", "AI reviewer-backed publication eval"}
            for ref in item["trace_refs"]
        )
    function_by_id = {item["function_id"]: item for item in authority["functions"]}
    for function_id in [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
    ]:
        item = function_by_id[function_id]
        assert item["boundary_id"] in boundary_by_id
        assert item["judgment_mode"] == "ai_first_stage_gate"
        assert item["decision_output_owner"] == "independent_reviewer_auditor_agent"
        assert item["program_may_emit_pass_ready_verdict"] is False
        assert item["missing_ai_first_record_policy"] == "typed_blocker_or_route_back"
        assert item["standard_stage_output"] is True
        assert item["requires_ai_first_record"] is True
        assert item["program_role"] in {"validator", "guard"}
        assert item["route_back_semantics"].startswith("route_back_to_")
        assert item["typed_blocker_semantics"].endswith("_blocker")
        assert set(item["trace_refs"]) <= set(boundary_by_id[item["boundary_id"]]["trace_refs"])
    artifact_auth = function_by_id["artifact_mutation_authorization"]
    assert artifact_auth["judgment_mode"] == "ai_first_record_validator"
    assert artifact_auth["decision_output_owner"] == "independent_reviewer_auditor_agent"
    assert artifact_auth["program_may_emit_pass_ready_verdict"] is False
    assert artifact_auth["requires_ai_first_record"] is True
    assert artifact_auth["program_role"] == "materializer"
    assert function_by_id["owner_receipt_signer"]["judgment_mode"] == "mechanical_guard"
    assert function_by_id["medical_helper_implementation"]["judgment_mode"] == "mechanical_guard"
    assert authority["all_other_program_surfaces"] == "opl_generated_or_migration_bridge"
    assert authority["forbidden_long_term_mas_shell_owners"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]
    classification = boundary["functional_surface_classification"]
    assert classification["declarative_pack_generated_surface"] == [
        "workspace_source_intake_shell",
        "workbench_portal_generic_shell",
        "runtime_supervisor_scan_consume_dispatch_shell",
        "generic_cli_mcp_product_wrappers",
        "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter",
        "generic_transition_runner",
    ]
    assert classification["refs_only_adapter"] == [
        "runtime_lifecycle_sqlite_reference_adapter",
        "paper_work_unit_outbox_index",
        "runtime_storage_maintenance",
        "publication_route_memory_locator_transport_shell",
        "artifact_lifecycle_storage_audit_shell",
        "terminal_attach_transport",
    ]
    assert set(classification["minimal_authority_function"]) == {
        "study_truth",
        "study_runtime_status",
        "runtime_watch_domain_health",
        "publication_quality_verdict",
        "ai_reviewer_workflow",
        "publication_gate",
        "artifact_authority",
        "owner_receipt",
        "domain_transition_table",
        "publication_route_memory_body",
        "memory_writeback_decision",
        "typed_blocker",
        "safe_action_refs",
    }
    assert set(classification["legacy_cleanup_no_active_caller_gate"]) == {
        "local_launchd_scheduler_install_path",
        "workspace_local_watch_service_wrappers",
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_without_active_caller",
    }
    inventory = boundary["functional_module_inventory"]
    assert len(inventory) == 18
    by_id = {item["module_id"]: item for item in inventory}
    lifecycle_item = by_id["runtime_lifecycle_sqlite_reference_adapter"]
    assert lifecycle_item["code_paths"] == [
        "src/med_autoscience/runtime_protocol/runtime_lifecycle_store.py",
        "src/med_autoscience/runtime_protocol/study_runtime.py",
        "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
    ]
    assert lifecycle_item["active_caller_status"] == "refs_only_domain_sidecar_adapter_active"
    assert lifecycle_item["migration_action"] == (
        "keep_runtime_lifecycle_refs_only_adapter_and_consume_opl_lifecycle_index"
    )
    assert set(lifecycle_item["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_restore_retention_owner",
    }
    assert by_id["runtime_supervisor_scan_consume_dispatch_shell"]["migration_action"] == (
        "declare_runtime_supervisor_policy_and_consume_opl_runtime_manager_loop"
    )
    wrapper_item = by_id["generic_cli_mcp_product_wrappers"]
    assert wrapper_item["active_callers"] == [
        "MAS CLI",
        "MCP tool handlers",
        "skill direct domain entry",
        "product-entry manifest",
    ]
    assert wrapper_item["authority_boundary"] == (
        "opl_generates_wrapper_and_skill_metadata_mas_executes_domain_authority_handlers"
    )
    assert "generated_surface_handoff.skill" in wrapper_item["proof_refs"]
    assert by_id["publication_quality_verdict"]["cannot_absorb_reason"] == (
        "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts."
    )
    assert by_id["local_launchd_scheduler_install_path"]["active_caller_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["default_caller_count"] == 0
    assert by_id["local_launchd_scheduler_install_path"]["install_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["trigger_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["write_install_proof_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["classification"] == (
        "legacy_cleanup_no_active_caller_gate"
    )
    assert by_id["local_launchd_scheduler_install_path"]["no_active_caller_gate"][
        "active_caller_allowed"
    ] is False
    assert boundary["functional_module_inventory_summary"]["classification_counts"] == {
        "declarative_pack_generated_surface": 7,
        "refs_only_adapter": 6,
        "minimal_authority_function": 3,
        "legacy_cleanup_no_active_caller_gate": 2,
    }
    assert boundary["functional_module_inventory_summary"]["classification_gap_count"] == 0
    assert boundary["functional_module_inventory_summary"]["functional_structure_gap_count"] == 0
    assert boundary["functional_module_inventory_summary"]["active_private_generic_residue_count"] == 0
    assert (
        boundary["functional_module_inventory_summary"]["remaining_gap_classification"]
        == "live_provider_paper_line_evidence_gates"
    )
    assert boundary["functional_module_inventory_summary"]["long_term_opl_owned_replacement_count"] == 0
    assert boundary["functional_module_inventory_summary"]["retire_tombstone_classification_count"] == 0
    followthrough_summary = boundary["functional_followthrough_gap_summary"]
    assert followthrough_summary["surface_kind"] == "mas_functional_followthrough_gap_summary"
    assert followthrough_summary["status"] == "functional_structure_closed_evidence_gates_remaining"
    assert followthrough_summary["classification_gap_count"] == 0
    assert followthrough_summary["functional_structure_gap_count"] == 0
    assert followthrough_summary["active_private_generic_residue_count"] == 0
    assert followthrough_summary["remaining_gap_classification"] == (
        "live_provider_paper_line_evidence_gates"
    )
    assert followthrough_summary["remaining_items_are_evidence_gates"] is True
    assert followthrough_summary["classification_counts"] == boundary["functional_module_inventory_summary"][
        "classification_counts"
    ]
    assert followthrough_summary["legacy_cleanup_items_are_remaining_active_gaps"] is False
    assert followthrough_summary["legacy_cleanup_items_have_default_entry"] is False
    assert followthrough_summary["legacy_cleanup_items_have_standard_template_refs"] is True
    assert followthrough_summary["remaining_functional_followthrough_gate_ids"] == []
    assert followthrough_summary["remaining_functional_followthrough_gates"] == []
    assert followthrough_summary["closed_functional_structure_gate_ids"] == [
        "generated_surface_active_caller_cutover",
        "refs_only_adapter_thinning",
        "legacy_cleanup_physical_retirement",
        "opl_app_workbench_drilldown",
        "lifecycle_locator_retention_restore_ledger_reconciliation",
    ]
    assert followthrough_summary["does_not_clear"] == (
        followthrough_summary["remaining_evidence_gate_ids"]
    )
    assert followthrough_summary["remaining_evidence_gate_ids"] == [
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    ]
    assert {item["owner"] for item in followthrough_summary["remaining_evidence_gates"]} == {
        "med-autoscience",
        "one-person-lab",
    }
    assert {item["functional_structure_gap"] for item in followthrough_summary["remaining_evidence_gates"]} == {
        False
    }
    assert "mas_owned_generic_queue" in followthrough_summary["forbidden_remaining_functional_gap_claims"]
    assert by_id["workspace_local_watch_service_wrappers"]["tombstone_required"] is True
    lifecycle_role = boundary["runtime_lifecycle_sqlite_role"]
    assert lifecycle_role["classification"] == "refs_only_adapter"
    assert lifecycle_role["current_mas_role"] == "domain_sidecar_index_reference_adapter"
    assert lifecycle_role["authority"] == "refs_only_index_not_generic_persistence_engine"
    assert lifecycle_role["owner"] == "one-person-lab"
    assert lifecycle_role["mas_may_index_domain_receipts"] is True
    assert lifecycle_role["mas_may_claim_generic_persistence_engine"] is False
    assert lifecycle_role["mas_consumes_opl_lifecycle_index_refs"] is True
    assert lifecycle_role["mas_may_write_domain_truth"] is False
    assert set(lifecycle_role["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_restore_retention_owner",
    }
    assert lifecycle_role["replacement_expectation"]["expected_replacements"] == [
        "opl_runtime_lifecycle_index_contract",
        "opl_artifact_lifecycle_storage_audit_shell",
        "opl_app_workbench_shell",
        "opl_terminal_attach_transport",
        "opl_provider_scheduler_lifecycle",
        "opl_queue_attempt_retry_dead_letter",
        "opl_generic_transition_runner",
    ]
    coverage = boundary["opl_functional_harness_consumer_coverage"]
    assert coverage["status"] == "landed_domain_authority_pack_consumer"
    assert coverage["coverage_items"] == [
        "refs_only_memory_writeback_chain",
        "queue_stage_attempt_typed_closeout",
        "generic_transition_runner",
        "restart_dead_letter_repair_human_gate_state_chain",
    ]
    assert coverage["opl_harness_pass_is_paper_closure"] is False
    assert coverage["opl_harness_pass_is_publication_ready"] is False
    assert coverage["mas_owns_generic_runtime"] is False
    assert coverage["refs_only_memory_writeback_chain"]["body_included"] is False
    assert (
        coverage["refs_only_memory_writeback_chain"]["opl_can_accept_or_reject_writeback"]
        is False
    )
    assert coverage["queue_stage_attempt_typed_closeout"]["queue_completion_is_paper_closure"] is False
    assert (
        coverage["generic_transition_runner"]["runner_completion_can_authorize_publication"]
        is False
    )
    assert (
        coverage["restart_dead_letter_repair_human_gate_state_chain"][
            "state_chain_completion_is_publication_ready"
        ]
        is False
    )
    assert "product_entry_manifest.functional_consumer_boundary" in boundary["proof_surfaces"]
    assert "mas_owned_generic_queue" in boundary["forbidden_regressions"]
    assert boundary["no_active_caller_proof"] == {
        "status": "default_surfaces_use_opl_cleanup_only_local_path",
        "default_caller_count": 0,
        "default_manager": "opl",
        "replacement_owner_surface": "opl_provider_runtime_manager",
        "legacy_local_install_path_role": "explicit_cleanup_diagnostic_only",
        "cleanup_only_commands": [
            "runtime-supervision-status --profile <profile> --manager local",
            "runtime-remove-supervision --profile <profile> --manager local",
        ],
        "forbidden_default_callers": [
            "cli_default_local_scheduler_install",
            "workspace_bootstrap_local_scheduler_install",
            "product_entry_local_scheduler_install",
            "sidecar_local_scheduler_install",
            "mcp_local_scheduler_install",
        ],
        "proof_items": [
            "cli_default_manager_is_opl",
            "workspace_bootstrap_manager_is_opl",
            "product_entry_consumes_opl_replacement_projection",
            "sidecar_exports_functional_boundary_no_generic_owner",
            "local_scheduler_ensure_returns_retired_cleanup_only",
            "local_scheduler_remove_is_explicit_cleanup_only",
            "local_scheduler_install_proof_generation_forbidden",
        ],
    }
    cleanup_only = boundary["legacy_local_scheduler_cleanup_only_proof"]
    assert cleanup_only["install_allowed"] is False
    assert cleanup_only["trigger_allowed"] is False
    assert cleanup_only["write_install_proof_allowed"] is False
    assert cleanup_only["default_cli_exposes_local_install"] is False
    assert cleanup_only["default_bootstrap_exposes_local_install"] is False
