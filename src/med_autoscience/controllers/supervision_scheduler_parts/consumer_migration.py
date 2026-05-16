from __future__ import annotations

from typing import Any


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
FUNCTIONAL_SURFACE_CLASSIFICATION = {
    "A_opl_owned_mas_consumes": [
        "runtime_lifecycle_sqlite_reference_adapter",
        "paper_work_unit_outbox_index",
        "runtime_storage_maintenance",
        "workspace_source_intake_shell",
        "publication_route_memory_locator_transport_shell",
        "artifact_lifecycle_storage_audit_shell",
        "workbench_portal_generic_shell",
        "terminal_attach_transport",
        "runtime_supervisor_scan_consume_dispatch_shell",
        "generic_cli_mcp_product_wrappers",
        "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter",
        "generic_transition_runner",
    ],
    "B_mas_domain_authority": [
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
    "C_retire_when_replaced_or_uncalled": [
        "local_launchd_scheduler_install_path",
        "workspace_local_watch_service_wrappers",
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_without_active_caller",
    ],
}
FUNCTIONAL_MODULE_INVENTORY = (
    {
        "module_id": "runtime_lifecycle_sqlite_reference_adapter",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
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
        "migration_action": "consume_opl_family_runtime_lifecycle_index_and_keep_mas_domain_receipt_refs_only",
        "retention_reason": "MAS can index paper-line owner receipts and locators, but the generic SQLite lifecycle index owner is OPL.",
        "opl_expected_primitives": [
            "opl_runtime_lifecycle_index_contract",
            "opl_provider_attempt_receipt_ledger",
            "opl_restore_retention_receipt_shell",
        ],
        "retained_domain_authority": ["owner_receipt", "study_runtime_status"],
    },
    {
        "module_id": "paper_work_unit_outbox_index",
        "owner": "med-autoscience",
        "classification": "domain_thin_adapter",
        "code_paths": ["src/med_autoscience/controllers/paper_work_unit_outbox.py"],
        "active_callers": ["paper work-unit controller and sidecar dispatch source refs"],
        "active_caller_status": "domain_outbox_adapter_active",
        "migration_action": "move generic queue_outbox_retry_attempt semantics to OPL and keep paper work-unit facts as MAS receipt refs",
        "retention_reason": "Paper work-unit identity, publication gate context, and artifact delta obligations are MAS domain facts.",
        "opl_expected_primitives": ["generic_queue", "generic_attempt_ledger", "attempt_retry_dead_letter"],
        "retained_domain_authority": ["paper_work_unit_semantics", "publication_gate", "owner_receipt"],
    },
    {
        "module_id": "runtime_storage_maintenance",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/controllers/runtime_storage_maintenance.py",
            "src/med_autoscience/controllers/runtime_storage_maintenance_parts/",
            "src/med_autoscience/cli_parts/runtime_storage_commands.py",
        ],
        "active_callers": ["runtime storage maintenance CLI", "workspace storage reports"],
        "active_caller_status": "generic_cleanup_shell_active_until_opl_lifecycle_replacement_proof",
        "migration_action": "move storage audit cleanup retention restore-proof shell to OPL lifecycle primitive",
        "retention_reason": "MAS may expose study/workspace refs and artifact authority receipts; generic cleanup policy belongs to OPL.",
        "opl_expected_primitives": ["artifact_lifecycle_storage_audit_shell", "restore_retention_receipt_shell"],
        "retained_domain_authority": ["artifact_authority", "workspace_artifact_refs"],
    },
    {
        "module_id": "workspace_source_intake_shell",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/controllers/workspace_init.py",
            "src/med_autoscience/workspace_contracts.py",
            "src/med_autoscience/controllers/workspace_literature.py",
            "src/med_autoscience/controllers/literature_provider_runtime.py",
        ],
        "active_callers": ["workspace init/readiness CLI", "MCP workspace readiness tools", "product-entry workspace surfaces"],
        "active_caller_status": "domain_source_adapter_active",
        "migration_action": "move generic workspace/source intake shell to OPL and keep MAS medical source readiness verdicts",
        "retention_reason": "Source quality, medical evidence readiness, and literature relevance remain MAS domain authority.",
        "opl_expected_primitives": ["workspace_source_intake_shell", "source_locator_index"],
        "retained_domain_authority": ["source_readiness_verdict", "evidence_ledger_refs"],
    },
    {
        "module_id": "publication_route_memory_locator_transport_shell",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/controllers/stage_knowledge_plane.py",
            "src/med_autoscience/controllers/stage_knowledge_plane_parts/publication_route_memory_inventory.py",
            "src/med_autoscience/controllers/stage_knowledge_plane_parts/publication_route_memory_writeback.py",
        ],
        "active_callers": ["publication-route memory CLI", "stage knowledge packet", "typed closeout memory writeback"],
        "active_caller_status": "body_free_locator_transport_active",
        "migration_action": "move generic locator freshness grouping and writeback transport to OPL memory primitive",
        "retention_reason": "MAS keeps publication-route memory body, recall policy, and accept/reject/blocker writeback verdict.",
        "opl_expected_primitives": ["generic_memory_locator", "memory_writeback_transport", "body_free_memory_projection"],
        "retained_domain_authority": ["publication_route_memory_body", "memory_writeback_decision"],
    },
    {
        "module_id": "artifact_lifecycle_storage_audit_shell",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/controllers/artifact_lifecycle_inventory.py",
            "src/med_autoscience/controllers/artifact_lifecycle_operations_report.py",
            "src/med_autoscience/controllers/artifact_retention_operations_plan.py",
            "src/med_autoscience/controllers/artifact_lifecycle_authority_kernel.py",
        ],
        "active_callers": ["artifact lifecycle CLI/MCP", "product-entry artifact projection"],
        "active_caller_status": "mixed_generic_shell_and_mas_authority_kernel_active",
        "migration_action": "move generic lifecycle inventory retention restore shell to OPL while leaving artifact mutation permission in MAS",
        "retention_reason": "Canonical manuscript/package mutation and rebuild proof are MAS artifact authority.",
        "opl_expected_primitives": ["generic_artifact_lifecycle", "artifact_locator", "restore_retention_receipt_shell"],
        "retained_domain_authority": ["artifact_authority", "current_package_authority"],
    },
    {
        "module_id": "workbench_portal_generic_shell",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/controllers/progress_portal.py",
            "src/med_autoscience/controllers/progress_portal_parts/",
            "src/med_autoscience/controllers/product_entry_parts/workspace_cockpit/",
        ],
        "active_callers": ["progress portal CLI", "workspace cockpit", "product-entry manifest"],
        "active_caller_status": "domain_projection_active_generic_workbench_shell_pending_opl_app_absorption",
        "migration_action": "move generic workbench navigation attention queue and drilldown shell to OPL App",
        "retention_reason": "MAS retains per-study route map, quality/source refs, blockers, and safe action receipt projection.",
        "opl_expected_primitives": ["generic_workbench", "operator_attention_queue", "route_decision_drilldown_shell"],
        "retained_domain_authority": ["study_progress_projection", "safe_action_refs"],
    },
    {
        "module_id": "terminal_attach_transport",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/controllers/runtime_live_console.py",
            "src/med_autoscience/controllers/runtime_live_console_ui.py",
        ],
        "active_callers": ["runtime live-console CLI", "Progress Portal links"],
        "active_caller_status": "read_only_terminal_projection_active",
        "migration_action": "move terminal attach/log tail transport to OPL operator workbench",
        "retention_reason": "MAS keeps read-only paper progress facts and domain blocker explanations.",
        "opl_expected_primitives": ["terminal_attach_transport", "operator_log_projection"],
        "retained_domain_authority": ["runtime_watch_domain_health", "typed_blocker"],
    },
    {
        "module_id": "runtime_supervisor_scan_consume_dispatch_shell",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/controllers/runtime_supervisor_scan.py",
            "src/med_autoscience/controllers/runtime_supervisor_consumer.py",
            "src/med_autoscience/controllers/runtime_supervisor_dispatch_executor.py",
            "src/med_autoscience/controllers/runtime_supervisor_reconcile.py",
        ],
        "active_callers": ["watch-runtime one-shot tick", "runtime reconcile", "sidecar dispatch"],
        "active_caller_status": "domain_guard_active_generic_scan_dispatch_shell_should_move_to_opl",
        "migration_action": "move generic scan consume dispatch reconcile loop to OPL runtime manager",
        "retention_reason": "MAS must keep owner-route facts, publication gate blockers, safe action refs, and no-forbidden-write evidence.",
        "opl_expected_primitives": ["generic_runner", "attempt_retry_dead_letter", "repair_projection"],
        "retained_domain_authority": ["owner_route", "publication_gate", "safe_action_refs"],
    },
    {
        "module_id": "generic_cli_mcp_product_wrappers",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/cli.py",
            "src/med_autoscience/mcp_server.py",
            "src/med_autoscience/controllers/product_entry.py",
        ],
        "active_callers": ["MAS CLI", "MCP tool descriptors", "product-entry manifest"],
        "active_caller_status": "domain_handlers_active_metadata_should_derive_from_opl_catalog",
        "migration_action": "derive generic command metadata and product shell from OPL action/stage catalog",
        "retention_reason": "MAS keeps domain command handlers and owner receipts; OPL can own descriptor projection and routing shell.",
        "opl_expected_primitives": ["action_catalog_projection", "product_entry_shell", "mcp_descriptor_projection"],
        "retained_domain_authority": ["domain_action_handler", "owner_receipt"],
    },
    {
        "module_id": "generic_daemon_or_scheduler_lifecycle",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/controllers/supervision_scheduler.py",
            "src/med_autoscience/controllers/supervision_scheduler_parts/",
        ],
        "active_callers": ["runtime-supervision-status default manager=opl", "legacy --manager local status/remove cleanup"],
        "active_caller_status": "opl_replacement_default_legacy_cleanup_only",
        "migration_action": "keep OPL as default scheduler owner and physically retire local LaunchAgent path after no-active-caller proof",
        "retention_reason": "MAS retains paper-progress SLO semantics and cleanup diagnostics for old local artifacts only.",
        "opl_expected_primitives": ["scheduler_lifecycle", "cadence_slo", "provider_slo"],
        "retained_domain_authority": ["paper_progress_slo_semantics", "typed_blocker"],
    },
    {
        "module_id": "generic_queue_attempt_retry_dead_letter",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/runtime_transport/",
            "src/med_autoscience/controllers/runtime_watch_outer_loop_dispatch.py",
            "src/med_autoscience/controllers/recovery_intent_ledger.py",
        ],
        "active_callers": ["MAS direct/local runtime", "runtime worker activity", "controller recovery intents"],
        "active_caller_status": "direct_runtime_adapter_active_opl_provider_handoff_required",
        "migration_action": "move generic queue attempt retry dead-letter and worker lease transport to OPL provider runtime",
        "retention_reason": "MAS keeps stage closeout semantics, owner receipts, and recovery owner decisions.",
        "opl_expected_primitives": ["generic_queue", "attempt_ledger", "retry_dead_letter", "worker_lifecycle_transport"],
        "retained_domain_authority": ["stage_closeout_domain_semantics", "owner_receipt"],
    },
    {
        "module_id": "generic_transition_runner",
        "owner": REPLACEMENT_OWNER,
        "classification": "A_opl_owned_mas_consumes",
        "code_paths": [
            "src/med_autoscience/controllers/study_domain_transition_table.py",
            "src/med_autoscience/controllers/study_state_matrix.py",
            "src/med_autoscience/controllers/study_domain_transition_guard.py",
        ],
        "active_callers": ["study-state-matrix CLI", "runtime consumer guard", "OPL transition descriptor"],
        "active_caller_status": "domain_transition_spec_active_generic_runner_owned_by_opl",
        "migration_action": "run MAS-declared transition spec through OPL generic transition runner",
        "retention_reason": "MAS owns medical transition semantics and oracle fixtures; OPL executes the generic state-machine transport.",
        "opl_expected_primitives": ["generic_transition_runner", "transition_matrix_runner", "idempotent_tick"],
        "retained_domain_authority": ["domain_transition_table", "publication_quality_verdict", "artifact_authority"],
    },
    {
        "module_id": "study_truth",
        "owner": "med-autoscience",
        "classification": "domain_authority",
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
        "classification": "domain_authority",
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
        "classification": "domain_authority",
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
        "classification": "retire_tombstone",
        "code_paths": ["src/med_autoscience/controllers/supervision_scheduler_parts/local_adapter.py"],
        "active_callers": ["explicit --manager local status/remove cleanup only"],
        "active_caller_status": "cleanup_diagnostic_only_no_default_caller",
        "migration_action": "delete_or_tombstone_after_no_active_caller_and_replacement_proof",
        "retention_reason": "Temporary diagnostic path removes old LaunchAgent and tick script artifacts.",
        "active_caller_allowed": False,
        "tombstone_required": True,
    },
    {
        "module_id": "workspace_local_watch_service_wrappers",
        "owner": "none_active",
        "classification": "retire_tombstone",
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
    },
)
OPL_REPLACEMENT_EXPECTATION_AUDIT = {
    "owner": REPLACEMENT_OWNER,
    "required_before_mas_generic_owner_claim": True,
    "audit_ref": "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough",
    "expected_replacements": [
        "opl_runtime_lifecycle_index_contract",
        "opl_artifact_lifecycle_storage_audit_shell",
        "opl_app_workbench_shell",
        "opl_terminal_attach_transport",
        "opl_provider_scheduler_lifecycle",
        "opl_queue_attempt_retry_dead_letter",
        "opl_generic_transition_runner",
    ],
    "mas_allowed_role_until_replacement": "domain_sidecar_reference_adapter_refs_only",
}


def build_functional_consumer_boundary() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_functional_consumer_boundary",
        "status": "opl_consumes_generic_surfaces_mas_retains_domain_authority_pack",
        "consumer_role": "domain_authority_pack_thin_program_surface",
        "generic_surface_owner": REPLACEMENT_OWNER,
        "generic_surfaces_consumed_from_opl": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_does_not_own": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_retains": list(MAS_RETAINED_THIN_PROGRAM_SURFACES),
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
        "runtime_lifecycle_sqlite_role": {
            "classification": "A_opl_owned_mas_consumes",
            "current_mas_role": "domain_sidecar_index_reference_adapter",
            "authority": "refs_only_index_not_generic_persistence_engine",
            "owner": REPLACEMENT_OWNER,
            "mas_may_index_domain_receipts": True,
            "mas_may_claim_generic_persistence_engine": False,
            "replacement_expectation": dict(OPL_REPLACEMENT_EXPECTATION_AUDIT),
        },
        "opl_functional_harness_consumer_coverage": {
            "surface_kind": "opl_functional_harness_consumer_coverage",
            "status": "landed_domain_authority_pack_consumer",
            "coverage_items": list(OPL_FUNCTIONAL_HARNESS_COVERAGE),
            "opl_harness_pass_is_paper_closure": False,
            "opl_harness_pass_is_publication_ready": False,
            "mas_owns_generic_runtime": False,
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
    "FORBIDDEN_AUTHORITY_CLAIMS",
    "FORBIDDEN_WRITES",
    "FUNCTIONAL_MODULE_INVENTORY",
    "FUNCTIONAL_SURFACE_CLASSIFICATION",
    "MAS_RETAINED_AFTER_MIGRATION",
    "MAS_RETAINED_THIN_PROGRAM_SURFACES",
    "OPL_CONSUMED_GENERIC_SURFACES",
    "OPL_FUNCTIONAL_HARNESS_COVERAGE",
    "OPL_REPLACEMENT_EXPECTATION_AUDIT",
    "OPL_REPLACEMENT_EXPECTED_CAPABILITIES",
    "REPLACEMENT_OWNER",
    "REPLACEMENT_OWNER_SURFACE",
    "REPLACEMENT_STATE",
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
