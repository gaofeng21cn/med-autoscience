from __future__ import annotations

from med_autoscience.controllers.domain_slo_scheduler_projection_parts.consumer_migration_active_path_inventory import (
    ACTIVE_PATH_RESIDUE_CLEANUP_GATES,
    PHYSICAL_MORPHOLOGY_LANE_D_CLOSEOUT,
    PHYSICAL_THINNING_EVIDENCE,
)

FUNCTIONAL_SURFACE_CLASSIFICATION = {
    "declarative_pack_generated_surface": [
        "workspace_source_intake_shell", "workbench_portal_generic_shell", "domain_route_scan_materialize_dispatch_shell",
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
    "legacy_cleanup_tombstone_provenance": [
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_without_active_caller",
    ],
    "legacy_cleanup_physical_retired": [
        "local_launchd_scheduler_install_path",
        "runtime_watch_loop_shell",
        "workspace_local_watch_service_wrappers",
    ],
}
REFS_ONLY_ADAPTER_RETIREMENT_GATE_BY_MODULE = {
    "runtime_lifecycle_sqlite_reference_adapter": {
        "active_caller_proof": [
            "study_runtime records runtime events and owner-receipt refs",
            "runtime lifecycle CLI reads lifecycle refs",
            "sidecar/product-entry lifecycle projections consume refs only",
        ],
        "retirement_gate_status": "active_domain_ref_caller_retained_until_opl_lifecycle_index_parity",
        "delete_or_tombstone_after": [
            "active_caller_count=0",
            "opl_runtime_lifecycle_index_parity_proven",
            "domain_owner_receipt_ref_parity_proven",
            "focused_runtime_lifecycle_projection_tests_green",
        ],
        "must_not_emit": [
            "generic_runtime_verdict",
            "generic_persistence_engine_owner",
            "paper_closure_verdict",
        ],
    },
    "paper_work_unit_outbox_index": {
        "active_caller_proof": [
            "paper work-unit controller keeps publication-gate context refs",
            "sidecar dispatch consumes work-unit source refs",
        ],
        "retirement_gate_status": "active_domain_outbox_ref_caller_retained_until_opl_queue_attempt_parity",
        "delete_or_tombstone_after": [
            "active_caller_count=0",
            "opl_queue_attempt_ledger_parity_proven",
            "paper_work_unit_identity_refs_projected_by_opl",
            "focused_queue_stage_attempt_tests_green",
        ],
        "must_not_emit": [
            "generic_queue_owner",
            "attempt_completion_is_publication_ready",
            "paper_closure_verdict",
        ],
    },
    "runtime_storage_maintenance": {
        "active_caller_proof": [
            "runtime storage maintenance CLI reads workspace storage refs",
            "workspace storage reports expose sizes and cleanup receipts only",
        ],
        "retirement_gate_status": "active_diagnostic_ref_caller_retained_until_opl_cleanup_policy_parity",
        "delete_or_tombstone_after": [
            "active_caller_count=0",
            "opl_artifact_lifecycle_storage_audit_shell_parity_proven",
            "artifact_authority_receipt_parity_proven",
            "focused_storage_maintenance_tests_green",
        ],
        "must_not_emit": [
            "generic_cleanup_policy",
            "restore_ready_verdict",
            "paper_closure_verdict",
        ],
    },
    "publication_route_memory_locator_transport_shell": {
        "active_caller_proof": [
            "publication-route memory CLI reads locator refs",
            "stage knowledge packet consumes body-free memory refs",
            "typed closeout memory writeback records receipt refs",
        ],
        "retirement_gate_status": "active_domain_memory_ref_caller_retained_until_opl_memory_locator_parity",
        "delete_or_tombstone_after": [
            "active_caller_count=0",
            "opl_generic_memory_locator_parity_proven",
            "publication_route_memory_body_stays_domain_owned",
            "focused_memory_writeback_chain_tests_green",
        ],
        "must_not_emit": [
            "memory_body_write",
            "memory_accept_reject_verdict_without_ai_first_record",
            "paper_closure_verdict",
        ],
    },
    "artifact_lifecycle_storage_audit_shell": {
        "active_caller_proof": [
            "artifact lifecycle CLI/MCP consumes artifact refs",
            "product-entry artifact projection consumes mutation-authority refs",
        ],
        "retirement_gate_status": "active_domain_artifact_ref_caller_retained_until_opl_artifact_lifecycle_parity",
        "delete_or_tombstone_after": [
            "active_caller_count=0",
            "opl_generic_artifact_lifecycle_parity_proven",
            "artifact_mutation_authority_receipt_parity_proven",
            "focused_artifact_lifecycle_tests_green",
        ],
        "must_not_emit": [
            "generic_artifact_lifecycle_owner",
            "artifact_mutation_authorized_without_mas_receipt",
            "paper_closure_verdict",
        ],
    },
    "terminal_attach_transport": {
        "active_caller_proof": [
            "runtime live-console CLI reads terminal log source refs",
            "Progress Portal links consume read-only terminal projections",
        ],
        "retirement_gate_status": "active_diagnostic_ref_caller_retained_until_opl_terminal_projection_parity",
        "delete_or_tombstone_after": [
            "active_caller_count=0",
            "opl_terminal_attach_transport_parity_proven",
            "terminal_gate_receipt_ref_parity_proven",
            "focused_live_console_parity_tests_green",
        ],
        "must_not_emit": [
            "generic_terminal_runtime_owner",
            "daemon_attach_authority",
            "paper_closure_verdict",
        ],
    },
}
RETIRED_LEGACY_RESIDUE_TOMBSTONES = (
    {
        "residue_id": "mas_generic_workbench_shell",
        "retired_from_classification": "legacy_cleanup_no_active_caller_gate",
        "current_role": "history_tombstone_provenance_only",
        "active_caller_count": 0,
        "active_caller_allowed": False,
        "default_entry_allowed": False,
        "tombstone_refs": [
            "docs/history/runtime/legacy_active_path_tombstones.md",
            "contracts/runtime/legacy-active-path-tombstones.json",
        ],
        "retirement_gate": "no_active_caller_proven_move_to_tombstone",
        "must_not_emit": ["generic_workbench_owner", "paper_closure_verdict"],
    },
    {
        "residue_id": "legacy_scheduler_default_aliases",
        "retired_from_classification": "legacy_cleanup_no_active_caller_gate",
        "current_role": "history_tombstone_provenance_only",
        "active_caller_count": 0,
        "active_caller_allowed": False,
        "default_entry_allowed": False,
        "tombstone_refs": [
            "docs/history/runtime/legacy_active_path_tombstones.md",
            "contracts/runtime/legacy-active-path-tombstones.json",
        ],
        "retirement_gate": "no_active_caller_proven_move_to_tombstone",
        "must_not_emit": ["generic_scheduler_owner", "paper_closure_verdict"],
    },
    {
        "residue_id": "daemonish_terminal_attach_status_as_runtime_owner",
        "retired_from_classification": "legacy_cleanup_no_active_caller_gate",
        "current_role": "history_tombstone_provenance_only",
        "active_caller_count": 0,
        "active_caller_allowed": False,
        "default_entry_allowed": False,
        "tombstone_refs": [
            "docs/history/runtime/legacy_active_path_tombstones.md",
            "contracts/runtime/legacy-active-path-tombstones.json",
        ],
        "retirement_gate": "no_active_caller_proven_move_to_tombstone",
        "must_not_emit": ["generic_terminal_runtime_owner", "paper_closure_verdict"],
    },
    {
        "residue_id": "scheduler_legacy_residue_without_active_caller",
        "retired_from_classification": "legacy_cleanup_no_active_caller_gate",
        "current_role": "history_tombstone_provenance_only",
        "active_caller_count": 0,
        "active_caller_allowed": False,
        "default_entry_allowed": False,
        "tombstone_refs": [
            "docs/history/runtime/legacy_active_path_tombstones.md",
            "contracts/runtime/legacy-active-path-tombstones.json",
        ],
        "retirement_gate": "no_active_caller_proven_move_to_tombstone",
        "must_not_emit": ["generic_scheduler_owner", "paper_closure_verdict"],
    },
)


def _refs_only_retirement_gate(module_id: str, active_caller_status: str) -> dict[str, object]:
    gate = REFS_ONLY_ADAPTER_RETIREMENT_GATE_BY_MODULE[module_id]
    return {
        "module_id": module_id,
        "classification": "refs_only_adapter",
        "active_caller_status": active_caller_status,
        "active_caller_count": len(gate["active_caller_proof"]),
        "active_caller_proof": list(gate["active_caller_proof"]),
        "retirement_gate_status": gate["retirement_gate_status"],
        "delete_or_tombstone_after": list(gate["delete_or_tombstone_after"]),
        "generic_owner_claim_allowed": False,
        "can_emit_paper_closure_verdict": False,
        "can_emit_generic_owner_verdict": False,
        "must_not_emit": list(gate["must_not_emit"]),
    }


def _module_with_retirement_gate(item: dict[str, object]) -> dict[str, object]:
    module_id = str(item["module_id"])
    if item["classification"] != "refs_only_adapter":
        return item
    result = dict(item)
    result["retirement_gate"] = _refs_only_retirement_gate(
        module_id,
        str(item["active_caller_status"]),
    )
    return result


_FUNCTIONAL_MODULE_INVENTORY = (
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
        "authority_boundary": "refs_only_sqlite_lifecycle_index_not_generic_runtime_owner",
        "provenance_boundary": {
            "surface_role": "domain_receipt_locator_and_lifecycle_ref_index",
            "history_role": "runtime_lifecycle_sqlite_migration_provenance",
            "body_policy": "refs_receipts_blockers_only",
            "may_emit": ["owner_receipt_ref", "study_runtime_status_ref", "lifecycle_locator_ref"],
            "must_not_emit": ["generic_runtime_verdict", "generic_restore_verdict", "paper_closure_verdict"],
            "generic_owner_claim_allowed": False,
        },
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
        "provenance_boundary": {
            "surface_role": "workspace_storage_ref_report_and_artifact_authority_receipt_adapter",
            "history_role": "storage_maintenance_provenance",
            "body_policy": "workspace_refs_sizes_receipts_blockers_only",
            "may_emit": ["workspace_artifact_ref", "cleanup_receipt_ref", "typed_blocker"],
            "must_not_emit": ["generic_cleanup_policy", "restore_ready_verdict", "paper_closure_verdict"],
            "generic_owner_claim_allowed": False,
        },
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
            "src/med_autoscience/controllers/runtime_live_console_ui_parts/rendering.py",
        ],
        "active_callers": ["runtime live-console CLI", "Progress Portal links"],
        "active_caller_status": "read_only_terminal_projection_active",
        "authority_boundary": "refs_only_terminal_projection_no_generic_attach_runtime_owner",
        "provenance_boundary": {
            "surface_role": "terminal_log_ref_projection_and_mas_attach_gate_provenance",
            "history_role": "terminal_attach_parity_provenance",
            "body_policy": "terminal_log_source_refs_and_gate_receipts_only",
            "may_emit": ["terminal_status_ref", "terminal_gate_receipt_ref", "typed_blocker"],
            "must_not_emit": ["generic_terminal_runtime_owner", "daemon_attach_authority", "paper_closure_verdict"],
            "generic_owner_claim_allowed": False,
        },
        "migration_action": "keep_read_only_terminal_refs_adapter_for_opl_operator_workbench",
        "retention_reason": "MAS keeps read-only paper progress facts and domain blocker explanations.",
        "opl_expected_primitives": ["terminal_attach_transport", "operator_log_projection"],
        "retained_domain_authority": ["runtime_watch_domain_health", "typed_blocker"],
    },
    {
        "module_id": "domain_route_scan_materialize_dispatch_shell",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/domain_route_scan.py", "src/med_autoscience/controllers/domain_action_request_materializer.py",
            "src/med_autoscience/controllers/domain_owner_action_dispatch.py", "src/med_autoscience/controllers/domain_route_reconcile.py",
        ],
        "active_callers": ["watch-runtime one-shot tick", "runtime reconcile", "sidecar dispatch"],
        "active_caller_status": "opl_runtime_manager_loop_consumed_mas_owner_route_guard_active",
        "migration_action": "declare_domain_route_policy_and_consume_opl_runtime_manager_loop",
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
        "code_paths": [
            "src/med_autoscience/cli.py",
            "src/med_autoscience/mcp_server.py",
            "src/med_autoscience/controllers/product_entry.py",
            "plugins/mas/skills/mas/SKILL.md",
        ],
        "active_callers": ["MAS CLI", "MCP tool handlers", "skill direct domain entry", "product-entry manifest"],
        "active_caller_status": "domain_handlers_active_opl_generated_wrapper_metadata_consumed",
        "migration_action": "derive_wrapper_metadata_from_declarative_pack_and_opl_generated_surfaces",
        "retention_reason": "MAS keeps domain command handlers, direct domain entry, and owner receipts; OPL owns CLI/MCP/Skill/product/status descriptor projection and routing shell.",
        "opl_expected_primitives": [
            "opl_action_catalog_projection",
            "opl_product_entry_shell",
            "opl_mcp_descriptor_projection",
            "opl_skill_descriptor_projection",
            "opl_generated_command_surface",
        ],
        "retained_domain_authority": ["domain_action_handler", "owner_receipt"],
        "authority_boundary": "opl_generates_wrapper_and_skill_metadata_mas_executes_domain_authority_handlers",
        "proof_refs": [
            "declarative_pack_compiler_input.family_action_catalog",
            "generated_surface_handoff.cli",
            "generated_surface_handoff.mcp",
            "generated_surface_handoff.skill",
            "generated_surface_handoff.product_entry",
        ],
    },
    {
        "module_id": "generic_daemon_or_scheduler_lifecycle",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/domain_slo_scheduler_projection.py",
            "src/med_autoscience/controllers/domain_slo_scheduler_projection_parts/",
        ],
        "active_callers": ["runtime-supervision-status default manager=opl"],
        "active_caller_status": "opl_replacement_default_local_tombstone_only",
        "migration_action": "declare_scheduler_requirement_in_pack_and_keep_local_tombstone_provenance_refs",
        "retention_reason": "MAS retains paper-progress SLO semantics and local scheduler tombstone provenance only.",
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
        "classification": "legacy_cleanup_physical_retired",
        "code_paths": [
            "contracts/runtime/legacy-active-path-tombstones.json",
            "docs/history/runtime/legacy_active_path_tombstones.md",
        ],
        "active_callers": [],
        "active_caller_status": "physical_retired_tombstone_only",
        "migration_action": "retain_history_tombstone_provenance_only",
        "retention_reason": (
            "Local LaunchAgent adapter code is retired; provenance remains for history and "
            "no-active-caller proof."
        ),
        "active_caller_allowed": False,
        "default_caller_count": 0,
        "install_allowed": False,
        "status_allowed": False,
        "remove_allowed": False,
        "trigger_allowed": False,
        "write_install_proof_allowed": False,
        "tombstone_required": True,
        "physical_retired": True,
        "no_active_caller_gate": {
            "default_caller_count": 0,
            "active_caller_allowed": False,
            "remaining_physical_delete_blockers": [],
        },
    },
    {
        "module_id": "workspace_local_watch_service_wrappers",
        "owner": "none_active",
        "classification": "legacy_cleanup_physical_retired",
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
        "physical_retired": True,
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
        "module_id": "runtime_watch_loop_shell",
        "owner": "none_active",
        "classification": "legacy_cleanup_physical_retired",
        "code_paths": [
            "src/med_autoscience/controllers/runtime_watch.py",
            "src/med_autoscience/cli_parts/parser.py",
            "src/med_autoscience/controllers/workspace_init_parts/shell_rendering.py",
        ],
        "active_callers": [],
        "active_caller_status": "retired_no_active_caller",
        "migration_action": "remove repo-local runtime watch loop and keep one-shot MAS domain diagnostic tick",
        "retention_reason": "Generic cadence and long-loop ownership belongs to OPL provider/runtime manager; MAS keeps one-shot runtime health and owner-route diagnostic tick only.",
        "active_caller_allowed": False,
        "tombstone_required": True,
        "physical_retired": True,
        "no_active_caller_gate": {
            "default_caller_count": 0,
            "active_caller_allowed": False,
            "replacement_owner": "one-person-lab",
            "replacement_surface": "opl_provider_runtime_manager",
            "no_compat_alias_allowed": True,
            "focused_test_refs": [
                "tests/test_runtime_watch_cases/cli_cases.py",
                "tests/test_cli_cases/public_entry_commands.py",
                "tests/test_workspace_init_cases/workspace_creation.py",
                "tests/test_workspace_init_cases/legacy_entry_upgrades.py",
            ],
        },
    },
)

FUNCTIONAL_MODULE_INVENTORY = tuple(
    _module_with_retirement_gate(dict(item)) for item in _FUNCTIONAL_MODULE_INVENTORY
)


__all__ = [
    "ACTIVE_PATH_RESIDUE_CLEANUP_GATES",
    "PHYSICAL_MORPHOLOGY_LANE_D_CLOSEOUT",
    "FUNCTIONAL_MODULE_INVENTORY",
    "FUNCTIONAL_SURFACE_CLASSIFICATION",
    "PHYSICAL_THINNING_EVIDENCE",
    "REFS_ONLY_ADAPTER_RETIREMENT_GATE_BY_MODULE",
    "RETIRED_LEGACY_RESIDUE_TOMBSTONES",
]
