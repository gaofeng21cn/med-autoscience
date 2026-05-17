from __future__ import annotations

from typing import Any

from .functional_gap_zero import (
    FUNCTIONAL_GAP_ZERO_STATUS,
    OPL_REPLACEMENT_EXPECTATION_AUDIT,
    REMAINING_GAP_CLASSIFICATION,
    build_functional_gap_zero_summary,
)

SCHEMA_VERSION = 1
SURFACE_KIND = "mas_supervision_scheduler_consumer_migration"
ACTIVE_PATH_ROLE = "opl_replacement_default"
LOCAL_DIAGNOSTIC_PATH_ROLE = "standalone_local_diagnostic_migration_bridge"
CURRENT_SCHEDULER_OWNER = "opl_provider_runtime_manager"
LEGACY_SCHEDULER_OWNER = "mas_supervision_scheduler"
REPLACEMENT_OWNER = "one-person-lab"
REPLACEMENT_OWNER_SURFACE = "opl_provider_runtime_manager"
REPLACEMENT_STATE = "opl_replacement_contract_active"
RETIREMENT_STATE = "local_legacy_retirement_pending_no_active_caller_proof"

MAS_RETAINED_AFTER_MIGRATION = (
    "paper_progress_slo_semantics",
    "mas_owner_receipt",
    "typed_blocker",
    "safe_action_refs",
    "quality_source_refs",
    "no_forbidden_write_evidence",
)
OPL_REPLACEMENT_EXPECTED_CAPABILITIES = (
    "scheduler_lifecycle",
    "cadence_slo",
    "job_registry_latest_run_projection",
    "provider_slo",
    "wakeup_transport",
    "attempt_queue_retry_dead_letter",
    "operator_projection",
)
RETIREMENT_PROOF_REQUIRED = (
    "opl_replacement_contract_available",
    "replacement_proof",
    "no_active_caller_proof",
    "no_forbidden_write",
    "focused_cli_status_tests",
    "git_diff_check",
)
FORBIDDEN_AUTHORITY_CLAIMS = (
    "provider_completion_is_paper_closure",
    "scheduler_status_is_publication_ready",
    "scheduler_status_authorizes_artifact_mutation",
    "stable_blocker_is_paper_closure",
)
FORBIDDEN_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "paper/current_package",
    "manuscript/current_package",
    "paper/submission_minimal",
    "manuscript/submission_minimal",
    "runtime_lifecycle.sqlite",
)
OPL_CONSUMED_GENERIC_SURFACES = (
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
)
OPL_FUNCTIONAL_HARNESS_COVERAGE = (
    "refs_only_memory_writeback_chain",
    "queue_stage_attempt_typed_closeout",
    "generic_transition_runner",
    "restart_dead_letter_repair_human_gate_state_chain",
)
NO_ACTIVE_CALLER_PROOF = {
    "status": "default_surfaces_use_opl_cleanup_only_local_path",
    "default_caller_count": 0,
    "default_manager": "opl",
    "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
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
LOCAL_SCHEDULER_CLEANUP_ONLY_PROOF = {
    "surface_kind": "mas_local_scheduler_cleanup_only_proof",
    "install_allowed": False,
    "trigger_allowed": False,
    "write_install_proof_allowed": False,
    "loaded_state_allowed": False,
    "default_cli_exposes_local_install": False,
    "default_bootstrap_exposes_local_install": False,
    "cleanup_status": "retired_legacy_cleanup_required",
    "remaining_physical_delete_blockers": [
        "legacy_launchagent_or_tick_script_may_exist_on_operator_machines",
        "explicit_status_remove_cleanup_path_still_needed_until_artifacts_absent",
        "provenance_and_regression_fixtures_still_assert_tombstone_behavior",
    ],
}
MAS_RETAINED_THIN_PROGRAM_SURFACES = (
    "study_truth",
    "publication_quality_verdict",
    "artifact_authority",
    "publication_route_memory_body",
    "memory_writeback_decision",
    "domain_transition_table",
    "owner_receipt",
    "typed_blocker",
    "safe_action_refs",
)
MINIMAL_AUTHORITY_FUNCTION_IDS = (
    "publication_quality_verdict",
    "ai_reviewer_quality_decision",
    "artifact_mutation_authorization",
    "publication_route_memory_accept_reject",
    "source_readiness_verdict",
    "owner_receipt_signer",
    "medical_helper_implementation",
)
DECLARATIVE_PACK_COMPILER_INPUT = {
    "surface_kind": "mas_declarative_pack_compiler_input",
    "schema_version": SCHEMA_VERSION,
    "owner": "med-autoscience",
    "compiler_owner": REPLACEMENT_OWNER,
    "status": "ready_for_opl_pack_compiler_consumption_generated_surface_migration",
    "pack_id": "mas-medical-research-pack",
    "pack_role": "domain_authority_pack_input_not_generated_shell_owner",
    "input_refs": [
        {
            "input_id": "domain_descriptor",
            "source_ref": "product_entry_manifest.standard_domain_agent_skeleton",
            "body_policy": "descriptor_only",
        },
        {
            "input_id": "stage_graph",
            "source_ref": "product_entry_manifest.family_stage_control_plane_descriptor",
            "body_policy": "descriptor_and_locator_refs",
        },
        {
            "input_id": "action_intents",
            "source_ref": "product_entry_manifest.family_action_catalog",
            "body_policy": "declarative_action_metadata",
        },
        {
            "input_id": "domain_transition_table",
            "source_ref": "study-state-matrix family_transition_spec_descriptor",
            "body_policy": "mas_owned_transition_spec_and_oracle_refs",
        },
        {
            "input_id": "publication_route_memory_policy",
            "source_ref": "product_entry_manifest.domain_memory_descriptor",
            "body_policy": "locator_receipt_refs_only_no_memory_body",
        },
        {
            "input_id": "artifact_authority_policy",
            "source_ref": "product_entry_manifest.lifecycle_guarded_apply_proof",
            "body_policy": "authority_policy_and_receipt_refs",
        },
        {
            "input_id": "source_readiness_policy",
            "source_ref": "workspace/source readiness verdict surfaces",
            "body_policy": "domain_verdict_function_only",
        },
        {
            "input_id": "receipt_schema",
            "source_ref": "product_entry_manifest.domain_owner_receipt_contract",
            "body_policy": "receipt_envelope_schema",
        },
        {
            "input_id": "no_forbidden_write_contract",
            "source_ref": "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough",
            "body_policy": "machine_guard",
        },
    ],
    "compiler_outputs_expected": [
        "cli",
        "mcp",
        "product_entry",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ],
    "mas_long_term_code_owner": "minimal_authority_functions_only",
    "must_not_generate_or_claim_domain_authority": True,
}
GENERATED_SURFACE_HANDOFF = {
    "surface_kind": "mas_generated_surface_handoff",
    "schema_version": SCHEMA_VERSION,
    "generated_surface_owner": REPLACEMENT_OWNER,
    "current_mas_role": "handwritten_migration_bridge",
    "status": "handoff_declared_mas_shells_are_migration_bridges",
    "long_term_mas_owner": False,
    "mas_handwritten_shell_expansion_allowed": False,
    "handoff_surfaces": [
        {
            "surface_id": "cli",
            "current_paths": ["src/med_autoscience/cli.py", "src/med_autoscience/cli_parts/"],
            "current_role": "migration_bridge_thin_wrapper",
            "target_role": "opl_generated_command_surface",
        },
        {
            "surface_id": "mcp",
            "current_paths": ["src/med_autoscience/mcp_server.py"],
            "current_role": "migration_bridge_tool_projection",
            "target_role": "opl_generated_mcp_descriptor_surface",
        },
        {
            "surface_id": "product_entry",
            "current_paths": ["src/med_autoscience/controllers/product_entry.py"],
            "current_role": "migration_bridge_manifest_builder",
            "target_role": "opl_generated_product_entry_surface",
        },
        {
            "surface_id": "sidecar",
            "current_paths": ["src/med_autoscience/controllers/sidecar_family_adapter.py"],
            "current_role": "migration_bridge_export_dispatch_adapter",
            "target_role": "opl_generated_sidecar_handoff_surface",
        },
        {
            "surface_id": "status",
            "current_paths": [
                "src/med_autoscience/controllers/product_entry_parts/",
                "src/med_autoscience/controllers/study_runtime_status.py",
            ],
            "current_role": "domain_truth_plus_migration_bridge_status_wrapper",
            "target_role": "opl_generated_status_wrapper_over_mas_truth_refs",
        },
        {
            "surface_id": "workbench",
            "current_paths": [
                "src/med_autoscience/controllers/progress_portal.py",
                "src/med_autoscience/controllers/product_entry_parts/workspace_cockpit/",
            ],
            "current_role": "migration_bridge_workbench_projection_shell",
            "target_role": "opl_hosted_workbench_shell_consuming_mas_refs",
        },
        {
            "surface_id": "projection_shell",
            "current_paths": [
                "src/med_autoscience/controllers/product_entry_parts/",
                "src/med_autoscience/controllers/progress_portal_parts/",
            ],
            "current_role": "migration_bridge_projection_builder",
            "target_role": "opl_generated_projection_shell",
        },
        {
            "surface_id": "test_lane_harness",
            "current_paths": ["contracts/test-lane-manifest.json", "tests/"],
            "current_role": "migration_bridge_repo_guard",
            "target_role": "opl_generated_harness_consumer_over_mas_pack",
        },
    ],
    "migration_bridge_exit_criteria": [
        "opl_pack_compiler_generated_surface_available",
        "active_callers_migrated",
        "focused_lane_green",
        "no_forbidden_write",
        "history_tombstone_or_delete_unowned_shell",
    ],
}
MINIMAL_AUTHORITY_FUNCTION_MANIFEST = {
    "surface_kind": "mas_minimal_authority_function_manifest",
    "schema_version": SCHEMA_VERSION,
    "owner": "med-autoscience",
    "status": "minimal_authority_functions_only",
    "function_ids": list(MINIMAL_AUTHORITY_FUNCTION_IDS),
    "function_count": len(MINIMAL_AUTHORITY_FUNCTION_IDS),
    "functions": [
        {
            "function_id": "publication_quality_verdict",
            "owner": "med-autoscience",
            "source_refs": [
                "publication_eval/latest.json",
                "publication gate",
                "review ledger",
            ],
            "cannot_absorb_reason": "Medical publication quality and readiness require MAS domain judgment.",
        },
        {
            "function_id": "ai_reviewer_quality_decision",
            "owner": "med-autoscience",
            "source_refs": [
                "AI reviewer workflow",
                "reviewer operating system trace",
                "AI reviewer-backed publication eval",
            ],
            "cannot_absorb_reason": "OPL can transport reviewer work but cannot issue medical reviewer verdicts.",
        },
        {
            "function_id": "artifact_mutation_authorization",
            "owner": "med-autoscience",
            "source_refs": [
                "canonical manuscript",
                "current_package",
                "submission package",
                "artifact rebuild proof",
            ],
            "cannot_absorb_reason": "Artifact mutation changes submission-facing medical deliverables.",
        },
        {
            "function_id": "publication_route_memory_accept_reject",
            "owner": "med-autoscience",
            "source_refs": [
                "publication-route memory body",
                "memory writeback proposal",
                "memory writeback router receipt",
            ],
            "cannot_absorb_reason": "Memory body and accept/reject decisions remain domain-owned.",
        },
        {
            "function_id": "source_readiness_verdict",
            "owner": "med-autoscience",
            "source_refs": [
                "study charter",
                "source readiness checks",
                "evidence ledger",
            ],
            "cannot_absorb_reason": "Medical source sufficiency and study readiness are MAS domain verdicts.",
        },
        {
            "function_id": "owner_receipt_signer",
            "owner": "med-autoscience",
            "source_refs": [
                "MAS owner receipt",
                "typed blocker",
                "safe action receipt",
            ],
            "cannot_absorb_reason": "Only MAS can sign domain receipt, blocker, and safe action authority.",
        },
        {
            "function_id": "medical_helper_implementation",
            "owner": "med-autoscience",
            "source_refs": [
                "medical analysis helpers",
                "reporting guideline helpers",
                "medical display/claim helper functions",
            ],
            "cannot_absorb_reason": "Domain helper code encodes medical research semantics rather than generic runtime shell.",
        },
    ],
    "all_other_program_surfaces": "opl_generated_or_migration_bridge",
    "forbidden_long_term_mas_shell_owners": [
        "cli",
        "mcp",
        "product_entry",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ],
}
FUNCTIONAL_SURFACE_CLASSIFICATION = {
    "declarative_pack_generated_surface": [
        "workspace_source_intake_shell", "workbench_portal_generic_shell", "runtime_supervisor_scan_consume_dispatch_shell",
        "generic_cli_mcp_product_wrappers", "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter", "generic_transition_runner",
    ],
    "refs_only_adapter": [
        "runtime_lifecycle_sqlite_reference_adapter", "paper_work_unit_outbox_index", "runtime_storage_maintenance",
        "publication_route_memory_locator_transport_shell", "artifact_lifecycle_storage_audit_shell",
        "terminal_attach_transport",
    ],
    "minimal_authority_function": [
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
    ],
    "legacy_cleanup_no_active_caller_gate": [
        "local_launchd_scheduler_install_path", "workspace_local_watch_service_wrappers", "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases", "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_without_active_caller",
    ],
}
FUNCTIONAL_MODULE_INVENTORY = (
    {
        "module_id": "runtime_lifecycle_sqlite_reference_adapter",
        "owner": "med-autoscience",
        "classification": "refs_only_adapter",
        "code_paths": [
            "src/med_autoscience/runtime_protocol/runtime_lifecycle_store.py",
            "src/med_autoscience/runtime_protocol/study_runtime.py",
            "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
        ],
        "active_callers": [
            "study_runtime records runtime events and snapshots",
            "runtime lifecycle CLI",
            "sidecar/product-entry lifecycle projections",
        ],
        "active_caller_status": "refs_only_domain_sidecar_adapter_active",
        "migration_action": "keep_runtime_lifecycle_refs_only_adapter_and_consume_opl_lifecycle_index",
        "retention_reason": (
            "MAS can index paper-line owner receipts and locators as a domain sidecar reference adapter; "
            "generic persistence, lifecycle indexing, restore/retention, and receipt ledger ownership stay in OPL."
        ),
        "opl_expected_primitives": [
            "opl_runtime_lifecycle_index_contract",
            "opl_provider_attempt_receipt_ledger",
            "opl_restore_retention_receipt_shell",
        ],
        "forbidden_mas_roles": [
            "generic_persistence_engine",
            "generic_lifecycle_engine",
            "generic_restore_retention_owner",
        ],
        "retained_domain_authority": ["owner_receipt", "study_runtime_status"],
    },
    {
        "module_id": "paper_work_unit_outbox_index",
        "owner": "med-autoscience",
        "classification": "refs_only_adapter",
        "code_paths": ["src/med_autoscience/controllers/paper_work_unit_outbox.py"],
        "active_callers": ["paper work-unit controller and sidecar dispatch source refs"],
        "active_caller_status": "domain_outbox_adapter_active",
        "migration_action": "keep_paper_work_unit_refs_only_adapter_and_declare_queue_attempt_requirements",
        "retention_reason": "Paper work-unit identity, publication gate context, and artifact delta obligations are MAS domain facts.",
        "opl_expected_primitives": ["generic_queue", "generic_attempt_ledger", "attempt_retry_dead_letter"],
        "retained_domain_authority": ["paper_work_unit_semantics", "publication_gate", "owner_receipt"],
    },
    {
        "module_id": "runtime_storage_maintenance",
        "owner": "med-autoscience",
        "classification": "refs_only_adapter",
        "code_paths": [
            "src/med_autoscience/controllers/runtime_storage_maintenance.py",
            "src/med_autoscience/controllers/runtime_storage_maintenance_parts/", "src/med_autoscience/cli_parts/runtime_storage_commands.py",
        ],
        "active_callers": ["runtime storage maintenance CLI", "workspace storage reports"],
        "active_caller_status": "refs_only_storage_audit_adapter_consumes_opl_lifecycle_policy",
        "migration_action": "keep_storage_audit_refs_only_adapter_and_consume_opl_lifecycle_cleanup_policy",
        "retention_reason": "MAS may expose study/workspace refs and artifact authority receipts; generic cleanup policy belongs to OPL.",
        "opl_expected_primitives": ["opl_artifact_lifecycle_storage_audit_shell", "opl_restore_retention_receipt_shell", "opl_runtime_lifecycle_cleanup_policy"],
        "retained_domain_authority": ["artifact_authority", "workspace_artifact_refs"],
        "authority_boundary": "refs_only_adapter_no_generic_cleanup_policy_owner",
        "proof_refs": ["contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough", "runtime_lifecycle_contract.opl_artifact_lifecycle_storage_audit_shell"],
    },
    {
        "module_id": "workspace_source_intake_shell",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/workspace_init.py",
            "src/med_autoscience/workspace_contracts.py",
            "src/med_autoscience/controllers/workspace_literature.py",
            "src/med_autoscience/controllers/literature_provider_runtime.py",
        ],
        "active_callers": ["workspace init/readiness CLI", "MCP workspace readiness tools", "product-entry workspace surfaces"],
        "active_caller_status": "domain_source_adapter_active",
        "migration_action": "declare_source_intake_policy_in_pack_and_keep_mas_source_readiness_verdict",
        "retention_reason": "Source quality, medical evidence readiness, and literature relevance remain MAS domain authority.",
        "opl_expected_primitives": ["workspace_source_intake_shell", "source_locator_index"],
        "retained_domain_authority": ["source_readiness_verdict", "evidence_ledger_refs"],
    },
    {
        "module_id": "publication_route_memory_locator_transport_shell",
        "owner": "med-autoscience",
        "classification": "refs_only_adapter",
        "code_paths": [
            "src/med_autoscience/controllers/stage_knowledge_plane.py",
            "src/med_autoscience/controllers/stage_knowledge_plane_parts/publication_route_memory_inventory.py",
            "src/med_autoscience/controllers/stage_knowledge_plane_parts/publication_route_memory_writeback.py",
        ],
        "active_callers": ["publication-route memory CLI", "stage knowledge packet", "typed closeout memory writeback"],
        "active_caller_status": "body_free_locator_transport_active",
        "migration_action": "keep_publication_route_memory_refs_only_adapter_no_memory_body_transport",
        "retention_reason": "MAS keeps publication-route memory body, recall policy, and accept/reject/blocker writeback verdict.",
        "opl_expected_primitives": ["generic_memory_locator", "memory_writeback_transport", "body_free_memory_projection"],
        "retained_domain_authority": ["publication_route_memory_body", "memory_writeback_decision"],
    },
    {
        "module_id": "artifact_lifecycle_storage_audit_shell",
        "owner": "med-autoscience",
        "classification": "refs_only_adapter",
        "code_paths": [
            "src/med_autoscience/controllers/artifact_lifecycle_inventory.py", "src/med_autoscience/controllers/artifact_lifecycle_operations_report.py",
            "src/med_autoscience/controllers/artifact_retention_operations_plan.py", "src/med_autoscience/controllers/artifact_lifecycle_authority_kernel.py",
        ],
        "active_callers": ["artifact lifecycle CLI/MCP", "product-entry artifact projection"],
        "active_caller_status": "refs_only_artifact_lifecycle_adapter_mas_mutation_authority_active",
        "migration_action": "keep_artifact_refs_only_audit_adapter_and_leave_mutation_authority_in_mas",
        "retention_reason": "Canonical manuscript/package mutation and rebuild proof are MAS artifact authority.",
        "opl_expected_primitives": ["opl_generic_artifact_lifecycle", "opl_artifact_locator", "opl_restore_retention_receipt_shell"],
        "retained_domain_authority": ["artifact_authority", "current_package_authority"],
        "authority_boundary": "opl_owns_lifecycle_shell_mas_authorizes_artifact_mutation",
        "proof_refs": ["contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough", "runtime_lifecycle_contract.opl_artifact_lifecycle_storage_audit_shell"],
    },
    {
        "module_id": "workbench_portal_generic_shell",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/progress_portal.py", "src/med_autoscience/controllers/progress_portal_parts/",
            "src/med_autoscience/controllers/product_entry_parts/workspace_cockpit/",
        ],
        "active_callers": ["progress portal CLI", "workspace cockpit", "product-entry manifest"],
        "active_caller_status": "opl_generated_workbench_surface_consumes_mas_domain_projection_refs",
        "migration_action": "declare_workbench_projection_inputs_for_opl_app_generated_shell",
        "retention_reason": "MAS retains per-study route map, quality/source refs, blockers, and safe action receipt projection.",
        "opl_expected_primitives": ["opl_generic_workbench", "opl_operator_attention_queue", "opl_route_decision_drilldown_shell"],
        "retained_domain_authority": ["study_progress_projection", "safe_action_refs"],
        "authority_boundary": "opl_hosts_workbench_shell_mas_supplies_refs_only_domain_projection",
        "proof_refs": ["product_entry_manifest.functional_consumer_boundary.generated_surface_handoff", "sidecar_export.functional_consumer_boundary.generated_surface_handoff"],
    },
    {
        "module_id": "terminal_attach_transport",
        "owner": "med-autoscience",
        "classification": "refs_only_adapter",
        "code_paths": [
            "src/med_autoscience/controllers/runtime_live_console.py",
            "src/med_autoscience/controllers/runtime_live_console_ui.py",
        ],
        "active_callers": ["runtime live-console CLI", "Progress Portal links"],
        "active_caller_status": "read_only_terminal_projection_active",
        "migration_action": "keep_read_only_terminal_refs_adapter_for_opl_operator_workbench",
        "retention_reason": "MAS keeps read-only paper progress facts and domain blocker explanations.",
        "opl_expected_primitives": ["terminal_attach_transport", "operator_log_projection"],
        "retained_domain_authority": ["runtime_watch_domain_health", "typed_blocker"],
    },
    {
        "module_id": "runtime_supervisor_scan_consume_dispatch_shell",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/runtime_supervisor_scan.py", "src/med_autoscience/controllers/runtime_supervisor_consumer.py",
            "src/med_autoscience/controllers/runtime_supervisor_dispatch_executor.py", "src/med_autoscience/controllers/runtime_supervisor_reconcile.py",
        ],
        "active_callers": ["watch-runtime one-shot tick", "runtime reconcile", "sidecar dispatch"],
        "active_caller_status": "opl_runtime_manager_loop_consumed_mas_owner_route_guard_active",
        "migration_action": "declare_runtime_supervisor_policy_and_consume_opl_runtime_manager_loop",
        "retention_reason": "MAS must keep owner-route facts, publication gate blockers, safe action refs, and no-forbidden-write evidence.",
        "opl_expected_primitives": ["opl_generic_runner", "opl_attempt_retry_dead_letter", "opl_repair_projection", "opl_provider_runtime_manager"],
        "retained_domain_authority": ["owner_route", "publication_gate", "safe_action_refs"],
        "authority_boundary": "opl_scans_and_dispatches_generic_loop_mas_guards_domain_route_and_receipt",
        "proof_refs": ["contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough", "product_entry_manifest.functional_consumer_boundary.opl_functional_harness_consumer_coverage"],
    },
    {
        "module_id": "generic_cli_mcp_product_wrappers",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": ["src/med_autoscience/cli.py", "src/med_autoscience/mcp_server.py", "src/med_autoscience/controllers/product_entry.py"],
        "active_callers": ["MAS CLI", "MCP tool descriptors", "product-entry manifest"],
        "active_caller_status": "domain_handlers_active_opl_generated_wrapper_metadata_consumed",
        "migration_action": "derive_wrapper_metadata_from_declarative_pack_and_opl_generated_surfaces",
        "retention_reason": "MAS keeps domain command handlers and owner receipts; OPL can own descriptor projection and routing shell.",
        "opl_expected_primitives": ["opl_action_catalog_projection", "opl_product_entry_shell", "opl_mcp_descriptor_projection", "opl_generated_command_surface"],
        "retained_domain_authority": ["domain_action_handler", "owner_receipt"],
        "authority_boundary": "opl_generates_wrapper_metadata_mas_executes_domain_authority_handlers",
        "proof_refs": ["declarative_pack_compiler_input.family_action_catalog", "generated_surface_handoff.cli", "generated_surface_handoff.mcp", "generated_surface_handoff.product_entry"],
    },
    {
        "module_id": "generic_daemon_or_scheduler_lifecycle",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/supervision_scheduler.py",
            "src/med_autoscience/controllers/supervision_scheduler_parts/",
        ],
        "active_callers": ["runtime-supervision-status default manager=opl", "legacy --manager local status/remove cleanup"],
        "active_caller_status": "opl_replacement_default_legacy_cleanup_only",
        "migration_action": "declare_scheduler_requirement_in_pack_and_keep_local_cleanup_diagnostic_gate",
        "retention_reason": "MAS retains paper-progress SLO semantics and cleanup diagnostics for old local artifacts only.",
        "opl_expected_primitives": ["scheduler_lifecycle", "cadence_slo", "provider_slo"],
        "retained_domain_authority": ["paper_progress_slo_semantics", "typed_blocker"],
    },
    {
        "module_id": "generic_queue_attempt_retry_dead_letter",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/runtime_transport/", "src/med_autoscience/controllers/runtime_watch_outer_loop_dispatch.py",
            "src/med_autoscience/controllers/recovery_intent_ledger.py",
        ],
        "active_callers": ["MAS direct/local runtime", "runtime worker activity", "controller recovery intents"],
        "active_caller_status": "opl_queue_attempt_transport_consumed_mas_closeout_receipt_adapter_active",
        "migration_action": "declare_queue_attempt_requirements_and_keep_mas_stage_closeout_receipts",
        "retention_reason": "MAS keeps stage closeout semantics, owner receipts, and recovery owner decisions.",
        "opl_expected_primitives": ["opl_generic_queue", "opl_attempt_ledger", "opl_retry_dead_letter", "opl_worker_lifecycle_transport"],
        "retained_domain_authority": ["stage_closeout_domain_semantics", "owner_receipt"],
        "authority_boundary": "opl_owns_queue_attempt_retry_transport_mas_signs_stage_closeout_receipts",
        "proof_refs": ["opl_functional_harness_consumer_coverage.queue_stage_attempt_typed_closeout", "opl_functional_harness_consumer_coverage.restart_dead_letter_repair_human_gate_state_chain"],
    },
    {
        "module_id": "generic_transition_runner",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/study_domain_transition_table.py",
            "src/med_autoscience/controllers/study_state_matrix.py",
            "src/med_autoscience/controllers/study_domain_transition_guard.py",
        ],
        "active_callers": ["study-state-matrix CLI", "runtime consumer guard", "OPL transition descriptor"],
        "active_caller_status": "domain_transition_spec_active_generic_runner_owned_by_opl",
        "migration_action": "declare_domain_transition_spec_for_opl_generic_runner",
        "retention_reason": "MAS owns medical transition semantics and oracle fixtures; OPL executes the generic state-machine transport.",
        "opl_expected_primitives": ["generic_transition_runner", "transition_matrix_runner", "idempotent_tick"],
        "retained_domain_authority": ["domain_transition_table", "publication_quality_verdict", "artifact_authority"],
    },
    {
        "module_id": "study_truth",
        "owner": "med-autoscience",
        "classification": "minimal_authority_function",
        "code_paths": [
            "src/med_autoscience/controllers/study_truth_kernel.py",
            "src/med_autoscience/controllers/study_runtime_status.py",
        ],
        "active_callers": ["MAS controller owner route", "study progress/read models"],
        "active_caller_status": "domain_authority_active",
        "migration_action": "retain_in_mas",
        "cannot_absorb_reason": "Medical study truth and paper route state are domain facts, not framework runtime state.",
        "retained_domain_authority": ["study_truth", "study_runtime_status"],
    },
    {
        "module_id": "publication_quality_verdict",
        "owner": "med-autoscience",
        "classification": "minimal_authority_function",
        "code_paths": [
            "src/med_autoscience/controllers/publication_gate.py",
            "src/med_autoscience/controllers/study_progress_parts/publication_runtime.py",
            "src/med_autoscience/controllers/ai_reviewer_runtime_workflow.py",
            "src/med_autoscience/controllers/ai_reviewer_publication_eval.py",
        ],
        "active_callers": ["AI reviewer workflow", "publication gate", "controller decision"],
        "active_caller_status": "domain_authority_active",
        "migration_action": "retain_in_mas",
        "cannot_absorb_reason": "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts.",
        "retained_domain_authority": ["publication_quality_verdict", "ai_reviewer_workflow", "publication_gate"],
    },
    {
        "module_id": "artifact_authority",
        "owner": "med-autoscience",
        "classification": "minimal_authority_function",
        "code_paths": [
            "src/med_autoscience/controllers/canonical_artifact_contract.py",
            "src/med_autoscience/controllers/study_delivery_sync.py",
            "src/med_autoscience/controllers/submission_minimal.py",
        ],
        "active_callers": ["delivery sync", "package freshness proof", "submission package handoff"],
        "active_caller_status": "domain_authority_active",
        "migration_action": "retain_in_mas",
        "cannot_absorb_reason": "Canonical manuscript/package mutation and submission authority are MAS artifact authority.",
        "retained_domain_authority": ["artifact_authority", "current_package_authority"],
    },
    {
        "module_id": "local_launchd_scheduler_install_path",
        "owner": "none_active",
        "classification": "legacy_cleanup_no_active_caller_gate",
        "code_paths": ["src/med_autoscience/controllers/supervision_scheduler_parts/local_adapter.py"],
        "active_callers": ["explicit --manager local status/remove cleanup only"],
        "active_caller_status": "cleanup_diagnostic_only_no_default_caller",
        "migration_action": "delete_or_tombstone_after_no_active_caller_and_replacement_proof",
        "retention_reason": "Temporary diagnostic path removes old LaunchAgent and tick script artifacts.",
        "active_caller_allowed": False,
        "default_caller_count": 0,
        "install_allowed": False,
        "trigger_allowed": False,
        "write_install_proof_allowed": False,
        "tombstone_required": True,
        "no_active_caller_gate": {
            "default_caller_count": 0,
            "active_caller_allowed": False,
            "delete_or_tombstone_only_after": [
                "opl_replacement_proof",
                "focused_cleanup_test_green",
                "fixture_or_provenance_dependency_absent_or_refs_only",
            ],
        },
    },
    {
        "module_id": "workspace_local_watch_service_wrappers",
        "owner": "none_active",
        "classification": "legacy_cleanup_no_active_caller_gate",
        "code_paths": [
            "src/med_autoscience/controllers/workspace_init_parts/retired_entries.py",
            "src/med_autoscience/controllers/workspace_legacy_physical_cleanup.py",
        ],
        "active_callers": ["legacy cleanup/audit only"],
        "active_caller_status": "retired_wrapper_cleanup_only",
        "migration_action": "remove generated wrappers and keep history/tombstone refs only",
        "retention_reason": "Needed only to detect and clean stale workspace-local service wrappers.",
        "active_caller_allowed": False,
        "tombstone_required": True,
        "no_active_caller_gate": {
            "default_caller_count": 0,
            "active_caller_allowed": False,
            "delete_or_tombstone_only_after": [
                "opl_replacement_proof",
                "focused_cleanup_test_green",
                "fixture_or_provenance_dependency_absent_or_refs_only",
            ],
        },
    },
)

def build_functional_consumer_boundary() -> dict[str, Any]:
    classification_counts: dict[str, int] = {}
    for item in FUNCTIONAL_MODULE_INVENTORY:
        classification = str(item["classification"])
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
    legacy_cleanup_items = [
        item["module_id"]
        for item in FUNCTIONAL_MODULE_INVENTORY
        if item["classification"] == "legacy_cleanup_no_active_caller_gate"
    ]
    functional_gap_zero_summary = build_functional_gap_zero_summary(
        classification_counts=classification_counts,
        legacy_cleanup_items=legacy_cleanup_items,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_functional_consumer_boundary",
        "status": "opl_consumes_generic_surfaces_mas_retains_domain_authority_pack",
        "consumer_role": "domain_authority_pack_thin_program_surface",
        "generic_surface_owner": REPLACEMENT_OWNER,
        "generic_surfaces_consumed_from_opl": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_does_not_own": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_retains": list(MAS_RETAINED_THIN_PROGRAM_SURFACES),
        "declarative_pack_compiler_input": dict(DECLARATIVE_PACK_COMPILER_INPUT),
        "generated_surface_handoff": {
            key: [dict(item) if isinstance(item, dict) else item for item in value]
            if isinstance(value, list)
            else value
            for key, value in GENERATED_SURFACE_HANDOFF.items()
        },
        "minimal_authority_function_manifest": {
            key: [dict(item) if isinstance(item, dict) else item for item in value]
            if isinstance(value, list)
            else value
            for key, value in MINIMAL_AUTHORITY_FUNCTION_MANIFEST.items()
        },
        "functional_surface_classification": {
            key: list(value) for key, value in FUNCTIONAL_SURFACE_CLASSIFICATION.items()
        },
        "functional_module_inventory": [
            {
                key: list(value) if isinstance(value, list) else value
                for key, value in item.items()
            }
            for item in FUNCTIONAL_MODULE_INVENTORY
        ],
        "functional_module_inventory_summary": {
            "total_count": len(FUNCTIONAL_MODULE_INVENTORY),
            "classification_counts": classification_counts,
            "long_term_opl_owned_replacement_count": 0,
            "retire_tombstone_classification_count": 0,
            "functional_structure_gap_count": 0,
            "active_private_generic_residue_count": 0,
            "remaining_gap_classification": REMAINING_GAP_CLASSIFICATION,
            "legacy_cleanup_items_require_no_active_caller_gate": legacy_cleanup_items,
            "legacy_cleanup_items_are_diagnostic_provenance_guards": True,
            "legacy_cleanup_item_role": "cleanup_diagnostic_provenance_drift_guard_no_active_default_caller",
            "legacy_cleanup_items_are_remaining_active_gaps": False,
            "legacy_cleanup_items_have_default_entry": False,
            "legacy_cleanup_items_have_standard_template_refs": False,
        },
        "functional_gap_zero_summary": functional_gap_zero_summary,
        "runtime_lifecycle_sqlite_role": {
            "classification": "refs_only_adapter",
            "current_mas_role": "domain_sidecar_index_reference_adapter",
            "authority": "refs_only_index_not_generic_persistence_engine",
            "owner": REPLACEMENT_OWNER,
            "mas_may_index_domain_receipts": True,
            "mas_may_claim_generic_persistence_engine": False,
            "mas_consumes_opl_lifecycle_index_refs": True,
            "mas_may_write_domain_truth": False,
            "forbidden_mas_roles": [
                "generic_persistence_engine",
                "generic_lifecycle_engine",
                "generic_restore_retention_owner",
            ],
            "replacement_expectation": dict(OPL_REPLACEMENT_EXPECTATION_AUDIT),
        },
        "opl_functional_harness_consumer_coverage": {
            "surface_kind": "opl_functional_harness_consumer_coverage",
            "status": "landed_domain_authority_pack_consumer",
            "coverage_items": list(OPL_FUNCTIONAL_HARNESS_COVERAGE),
            "opl_harness_pass_is_paper_closure": False,
            "opl_harness_pass_is_publication_ready": False,
            "mas_owns_generic_runtime": False,
            "mas_retains_domain_authority_pack": list(MAS_RETAINED_THIN_PROGRAM_SURFACES),
            "refs_only_memory_writeback_chain": {
                "opl_consumes": [
                    "consumed_publication_route_memory_refs",
                    "typed_closeout_proposal_refs",
                    "memory_write_router_receipt_refs",
                    "workspace_writeback_receipt_refs",
                    "opl_aion_display_receipt_refs",
                ],
                "mas_retains": [
                    "publication_route_memory_body",
                    "memory_writeback_decision",
                    "accepted_rejected_blocked_writeback_verdict",
                ],
                "body_included": False,
                "opl_can_accept_or_reject_writeback": False,
            },
            "queue_stage_attempt_typed_closeout": {
                "opl_owns": [
                    "family_queue",
                    "stage_attempt_ledger",
                    "attempt_start_query_signal",
                    "framework_typed_closeout_transport",
                ],
                "mas_retains": [
                    "stage_closeout_domain_semantics",
                    "owner_receipt",
                    "typed_blocker",
                    "safe_action_refs",
                ],
                "queue_completion_is_paper_closure": False,
            },
            "generic_transition_runner": {
                "opl_owns": [
                    "generic_transition_runner",
                    "transition_matrix_runner",
                    "idempotent_tick",
                    "retry_dead_letter_transport",
                ],
                "mas_retains": [
                    "domain_transition_table",
                    "publication_quality_verdict",
                    "artifact_authority",
                    "owner_receipt",
                ],
                "runner_completion_can_authorize_publication": False,
            },
            "restart_dead_letter_repair_human_gate_state_chain": {
                "opl_owns": [
                    "restart_requery",
                    "dead_letter_state",
                    "repair_transport",
                    "human_gate_signal_transport",
                ],
                "mas_retains": [
                    "human_gate_domain_receipt",
                    "repair_owner_receipt",
                    "stop_loss_receipt",
                    "typed_blocker",
                ],
                "state_chain_completion_is_publication_ready": False,
            },
        },
        "no_active_caller_required": True,
        "no_active_caller_proof": dict(NO_ACTIVE_CALLER_PROOF),
        "legacy_local_scheduler_cleanup_only_proof": dict(LOCAL_SCHEDULER_CLEANUP_ONLY_PROOF),
        "no_active_caller_scope": [
            "cli_default",
            "mcp_default",
            "product_entry_default",
            "sidecar_default",
            "test_lane_default",
        ],
        "proof_surfaces": [
            "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough",
            "runtime-supervision-status default manager=opl",
            "product_entry_manifest.functional_consumer_boundary",
            "sidecar_export.functional_consumer_boundary",
            "legacy_residue_audit.summary.default_caller_count",
        ],
        "forbidden_regressions": [
            "mas_default_generic_scheduler",
            "mas_resident_generic_daemon",
            "mas_owned_generic_queue",
            "mas_owned_attempt_ledger",
            "mas_generic_transition_runner",
            "mas_generic_workbench_shell",
        ],
    }


def build_consumer_migration_contract(
    *,
    adapter_id: str | None = None,
    manager: str | None = None,
) -> dict[str, Any]:
    manager_key = str(manager or "").strip().lower()
    replacement_active = manager_key in {"opl", "opl_provider_runtime_manager"} or adapter_id == "opl_family_runtime_provider"
    active_path_role = ACTIVE_PATH_ROLE if replacement_active else LOCAL_DIAGNOSTIC_PATH_ROLE
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "state": REPLACEMENT_STATE,
        "active_path_role": active_path_role,
        "current_scheduler_owner": CURRENT_SCHEDULER_OWNER if replacement_active else LEGACY_SCHEDULER_OWNER,
        "legacy_scheduler_owner": LEGACY_SCHEDULER_OWNER,
        "local_diagnostic_path_role": LOCAL_DIAGNOSTIC_PATH_ROLE,
        "current_surface_allowed_until_replacement": not replacement_active,
        "replacement_required_before_retirement": not replacement_active,
        "retirement_state": RETIREMENT_STATE,
        "replacement_owner": REPLACEMENT_OWNER,
        "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
        "replacement_contract_expected": {
            "owner": REPLACEMENT_OWNER,
            "surface": REPLACEMENT_OWNER_SURFACE,
            "required_capabilities": list(OPL_REPLACEMENT_EXPECTED_CAPABILITIES),
            "must_not_write_mas_domain_truth": True,
            "status": "active" if replacement_active else "required_before_retirement",
        },
        "functional_consumer_boundary": build_functional_consumer_boundary(),
        "mas_retained_after_migration": list(MAS_RETAINED_AFTER_MIGRATION),
        "retirement_proof_required": list(RETIREMENT_PROOF_REQUIRED),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "adapter_id": adapter_id,
        "manager": manager,
    }


def attach_consumer_migration_contract(
    payload: dict[str, Any],
    *,
    adapter_id: str | None = None,
    manager: str | None = None,
) -> dict[str, Any]:
    result = dict(payload)
    contract = build_consumer_migration_contract(adapter_id=adapter_id, manager=manager)
    result["active_path_role"] = contract["active_path_role"]
    result["consumer_migration"] = contract
    result["replacement_owner"] = REPLACEMENT_OWNER
    result["retirement_state"] = RETIREMENT_STATE
    return result


__all__ = [
    "ACTIVE_PATH_ROLE",
    "CURRENT_SCHEDULER_OWNER",
    "DECLARATIVE_PACK_COMPILER_INPUT",
    "FORBIDDEN_AUTHORITY_CLAIMS",
    "FORBIDDEN_WRITES",
    "FUNCTIONAL_MODULE_INVENTORY",
    "FUNCTIONAL_SURFACE_CLASSIFICATION",
    "FUNCTIONAL_GAP_ZERO_STATUS",
    "GENERATED_SURFACE_HANDOFF",
    "MAS_RETAINED_AFTER_MIGRATION",
    "MAS_RETAINED_THIN_PROGRAM_SURFACES",
    "MINIMAL_AUTHORITY_FUNCTION_IDS",
    "MINIMAL_AUTHORITY_FUNCTION_MANIFEST",
    "NO_ACTIVE_CALLER_PROOF",
    "LOCAL_SCHEDULER_CLEANUP_ONLY_PROOF",
    "OPL_CONSUMED_GENERIC_SURFACES",
    "OPL_FUNCTIONAL_HARNESS_COVERAGE",
    "OPL_REPLACEMENT_EXPECTATION_AUDIT",
    "OPL_REPLACEMENT_EXPECTED_CAPABILITIES",
    "REPLACEMENT_OWNER",
    "REPLACEMENT_OWNER_SURFACE",
    "REPLACEMENT_STATE",
    "REMAINING_GAP_CLASSIFICATION",
    "RETIREMENT_PROOF_REQUIRED",
    "RETIREMENT_STATE",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "LEGACY_SCHEDULER_OWNER",
    "LOCAL_DIAGNOSTIC_PATH_ROLE",
    "attach_consumer_migration_contract",
    "build_functional_consumer_boundary",
    "build_consumer_migration_contract",
]
