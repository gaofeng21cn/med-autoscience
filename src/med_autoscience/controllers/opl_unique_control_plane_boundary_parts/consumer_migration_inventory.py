from __future__ import annotations

FUNCTIONAL_SURFACE_CLASSIFICATION = {
    "declarative_pack_generated_surface": [
        "workspace_source_intake_shell", "workbench_portal_generic_shell", "owner_route_reconcile_materialize_dispatch_shell",
        "generic_cli_mcp_product_wrappers", "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter", "generic_transition_runner",
    ],
    "domain_authority_refs": [
        "domain_authority_refs_index", "paper_work_unit_outbox_index", "runtime_storage_maintenance",
        "publication_route_memory_locator_transport_shell", "artifact_lifecycle_storage_audit_shell",
    ],
    "minimal_authority_function": [
        "study_truth",
        "progress_projection",
        "domain_health_diagnostic",
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
}
DEFAULT_CALLER_DELETION_BRIDGE_MODULE_IDS = {
    "generic_cli_mcp_product_wrappers",
    "owner_route_reconcile_materialize_dispatch_shell",
    "workbench_portal_generic_shell",
}
DOMAIN_AUTHORITY_REFS_RETIREMENT_GATE_BY_MODULE = {
    "domain_authority_refs_index": {
        "domain_ref_consumer_refs": [
            "owner-route handoff records owner-receipt refs",
            "domain-handler/product-entry projections consume domain authority refs only",
            "workspace maintenance records archive/source/artifact locator refs only",
        ],
        "retirement_gate_status": "active_domain_authority_ref_index_not_runtime_lifecycle_owner",
        "delete_or_tombstone_after": [
            "domain_authority_refs_replaced_by_opl_generated_ref_index",
            "owner_receipt_ref_parity_proven",
            "no_forbidden_write_proof_recorded",
            "focused_domain_authority_refs_tests_green",
        ],
        "must_not_emit": [
            "generic_runtime_verdict",
            "generic_persistence_engine_owner",
            "generic_runtime_lifecycle_owner",
            "paper_closure_verdict",
        ],
    },
    "paper_work_unit_outbox_index": {
        "domain_ref_consumer_refs": [
            "paper work-unit controller keeps publication-gate context refs",
            "domain-handler dispatch consumes work-unit source refs",
        ],
        "retirement_gate_status": "domain_outbox_refs_until_opl_queue_attempt_parity",
        "delete_or_tombstone_after": [
            "opl_queue_attempt_ledger_consumes_domain_refs",
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
        "domain_ref_consumer_refs": [
            "runtime grouped storage audit commands read workspace storage refs",
            "workspace storage reports expose sizes and cleanup receipts only",
        ],
        "retirement_gate_status": "storage_refs_until_opl_cleanup_policy_parity",
        "delete_or_tombstone_after": [
            "opl_cleanup_policy_consumes_storage_refs",
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
        "domain_ref_consumer_refs": [
            "publication-route memory CLI reads locator refs",
            "stage knowledge packet consumes body-free memory refs",
            "typed closeout memory writeback records receipt refs",
        ],
        "retirement_gate_status": "domain_memory_refs_until_opl_memory_locator_parity",
        "delete_or_tombstone_after": [
            "opl_memory_locator_consumes_body_free_refs",
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
        "domain_ref_consumer_refs": [
            "artifact lifecycle CLI/MCP consumes artifact refs",
            "product-entry artifact projection consumes mutation-authority refs",
        ],
        "retirement_gate_status": "domain_artifact_refs_until_opl_artifact_lifecycle_parity",
        "delete_or_tombstone_after": [
            "opl_artifact_lifecycle_consumes_artifact_refs",
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
}
def _domain_authority_refs_retirement_gate(module_id: str, current_ref_status: str) -> dict[str, object]:
    gate = DOMAIN_AUTHORITY_REFS_RETIREMENT_GATE_BY_MODULE[module_id]
    return {
        "module_id": module_id,
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "current_ref_status": current_ref_status,
        "domain_ref_consumer_count": len(gate["domain_ref_consumer_refs"]),
        "domain_ref_consumer_refs": list(gate["domain_ref_consumer_refs"]),
        "retirement_gate_status": gate["retirement_gate_status"],
        "delete_or_tombstone_after": list(gate["delete_or_tombstone_after"]),
        "generic_owner_claim_allowed": False,
        "can_emit_paper_closure_verdict": False,
        "can_emit_generic_owner_verdict": False,
        "must_not_emit": list(gate["must_not_emit"]),
    }


def _default_caller_deletion_bridge_exit_gate(
    item: dict[str, object],
) -> dict[str, object]:
    module_id = str(item["module_id"])
    classification = str(item["classification"])
    domain_authority_refs = list(item.get("mas_domain_authority_refs", []))
    current_surface_refs = list(item.get("current_surface_refs", []))
    is_authority = classification == "minimal_authority_function"
    return {
        "surface_kind": "mas_default_caller_deletion_domain_ref_exit_gate",
        "gate_id": f"mas.default_caller_deletion.{module_id}.domain_ref_exit.v1",
        "domain_ref_owner": "med-autoscience",
        "replacement_owner": "one-person-lab",
        "current_status": (
            "mas_domain_authority_refs_active"
            if is_authority
            else "domain_refs_until_explicit_owner_receipt_authorizes_physical_delete"
        ),
        "required_before_retire": [] if is_authority else [
            "domain_authority_refs_preserved",
            "no_forbidden_write_proof_recorded",
            "explicit_owner_receipt_authorizes_physical_delete",
        ],
        "current_surface_refs": current_surface_refs,
        "mas_domain_authority_refs": domain_authority_refs,
        "default_caller_deletion_evidence_scope": (
            "domain_owned_typed_blocker_and_no_forbidden_write_refs_only_no_physical_delete_authorization"
        ),
        "typed_blocker_refs": [
            (
                "typed-blocker:mas/default-caller-deletion/"
                f"{module_id}/physical-delete-requires-explicit-owner-receipt"
            )
        ],
        "no_forbidden_write_refs": [
            f"no-forbidden-write:mas/default-caller-deletion/{module_id}/refs-only-boundary"
        ],
        "no_forbidden_write_evidence_refs": [
            f"no-forbidden-write:mas/default-caller-deletion/{module_id}/refs-only-boundary"
        ],
        "provenance_refs": current_surface_refs,
        "domain_repo_physical_delete_authorized": False,
        "physical_delete_authorized_by_refs": False,
        "mas_can_write_generic_runtime": False,
        "mas_can_own_generated_default_caller": False,
        "opl_can_write_study_truth": False,
        "opl_can_declare_publication_quality_or_export_verdict": False,
        "opl_can_issue_mas_owner_receipt": False,
    }


def _module_with_retirement_gate(item: dict[str, object]) -> dict[str, object]:
    module_id = str(item["module_id"])
    result = dict(item)
    if item["classification"] == "domain_authority_refs":
        result["retirement_gate"] = _domain_authority_refs_retirement_gate(
            module_id,
            str(item["current_ref_status"]),
        )
    if module_id in DEFAULT_CALLER_DELETION_BRIDGE_MODULE_IDS:
        result["bridge_exit_gate"] = _default_caller_deletion_bridge_exit_gate(result)
    return result


_FUNCTIONAL_MODULE_INVENTORY = (
    {
        "module_id": "domain_authority_refs_index",
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "code_paths": [
            "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
            "src/med_autoscience/opl_domain_pack/",
            "src/med_autoscience/controllers/owner_route_handoff_parts/substrate_adapter.py",
        ],
        "domain_ref_consumers": [
            "owner-route handoff domain authority refs",
            "paper work-unit and dispatch owner receipt refs",
            "domain-handler/product-entry domain authority refs projections",
        ],
        "current_ref_status": "domain_authority_refs_index_no_runtime_lifecycle_owner",
        "authority_boundary": "refs_only_owner_receipt_locator_index_not_generic_runtime_owner",
        "provenance_boundary": {
            "surface_role": "domain_authority_receipt_locator_and_ref_index",
            "history_role": "retired_runtime_lifecycle_sqlite_provenance",
            "body_policy": "refs_receipts_blockers_only",
            "may_emit": ["owner_receipt_ref", "typed_blocker_ref", "progress_projection_ref", "domain_authority_locator_ref"],
            "must_not_emit": [
                "generic_runtime_verdict",
                "generic_runtime_lifecycle_owner",
                "generic_restore_verdict",
                "paper_closure_verdict",
            ],
            "generic_owner_claim_allowed": False,
        },
        "migration_action": "declare_domain_authority_refs_index_and_consume_opl_current_control_state",
        "retention_reason": (
            "MAS can index paper-line owner receipts, typed blockers, and locators as domain authority refs; "
            "generic persistence, runtime lifecycle indexing, restore/retention, queue, and receipt ledger ownership stay in OPL."
        ),
        "opl_expected_primitives": [
            "opl_current_control_state_projection",
            "opl_provider_attempt_receipt_ledger",
            "opl_restore_retention_receipt_shell",
        ],
        "forbidden_mas_roles": [
            "generic_persistence_engine",
            "generic_lifecycle_engine",
            "generic_runtime_lifecycle_owner",
            "generic_restore_retention_owner",
        ],
        "mas_domain_authority_refs": ["owner_receipt", "progress_projection"],
    },
    {
        "module_id": "paper_work_unit_outbox_index",
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "code_paths": ["src/med_autoscience/controllers/paper_work_unit_outbox.py"],
        "domain_ref_consumers": ["paper work-unit controller and domain-handler dispatch source refs"],
        "current_ref_status": "domain_outbox_refs_no_queue_attempt_owner",
        "migration_action": "declare_paper_work_unit_refs_and_queue_attempt_requirements",
        "retention_reason": "Paper work-unit identity, publication gate context, and artifact delta obligations are MAS domain facts.",
        "opl_expected_primitives": ["generic_queue", "generic_attempt_ledger", "attempt_retry_dead_letter"],
        "mas_domain_authority_refs": ["paper_work_unit_semantics", "publication_gate", "owner_receipt"],
    },
    {
        "module_id": "runtime_storage_maintenance",
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "code_paths": [
            "src/med_autoscience/controllers/runtime_storage_maintenance.py",
            "src/med_autoscience/controllers/runtime_storage_maintenance_parts/",
            "src/med_autoscience/controllers/runtime_storage_maintenance_parts/authority_boundary.py",
            "src/med_autoscience/controllers/runtime_storage_maintenance_parts/cache_cleanup.py",
        ],
        "domain_ref_consumers": ["runtime grouped storage audit commands", "workspace storage reports"],
        "current_ref_status": "refs_only_storage_audit_adapter_consumes_opl_lifecycle_policy",
        "migration_action": "declare_storage_audit_refs_and_consume_opl_lifecycle_cleanup_policy",
        "retention_reason": "MAS may expose study/workspace refs and artifact authority receipts; generic cleanup policy belongs to OPL.",
        "opl_expected_primitives": ["opl_artifact_lifecycle_storage_audit_shell", "opl_restore_retention_receipt_shell", "opl_runtime_lifecycle_cleanup_policy"],
        "mas_domain_authority_refs": ["artifact_authority", "workspace_artifact_refs"],
        "authority_boundary": "domain_authority_refs_no_generic_cleanup_policy_owner",
        "provenance_boundary": {
            "surface_role": "workspace_storage_ref_report_and_artifact_authority_receipt_adapter",
            "history_role": "storage_maintenance_provenance",
            "body_policy": "workspace_refs_sizes_receipts_blockers_only",
            "may_emit": [
                "workspace_artifact_ref",
                "cleanup_receipt_ref",
                "restore_proof_ref",
                "typed_blocker",
                "storage_size_ref",
            ],
            "must_not_emit": [
                "generic_cleanup_policy",
                "restore_ready_verdict",
                "paper_closure_verdict",
                "publication_ready_verdict",
                "artifact_mutation_authorization",
            ],
            "generic_owner_claim_allowed": False,
        },
        "latest_thinning_evidence": {
            "status": "runtime_storage_live_report_boundary_payload_landed",
            "scope": "workspace_study_orphan_runtime_storage_reports_emit_refs_only_boundary",
            "extracted_paths": [
                "src/med_autoscience/controllers/runtime_storage_maintenance_parts/authority_boundary.py",
                "src/med_autoscience/controllers/runtime_storage_maintenance_parts/cache_cleanup.py",
            ],
            "domain_refs_entry_shell": "src/med_autoscience/controllers/runtime_storage_maintenance.py",
            "domain_refs_entry_role": "workspace_storage_refs_and_runtime_audit_entry",
            "live_report_boundary_payload": {
                "surface_kind": "mas_runtime_storage_refs_only_adapter_boundary",
                "report_modes": [
                    "workspace_storage_audit",
                    "study_runtime_storage_maintenance",
                    "orphan_quest_runtime_storage_maintenance",
                ],
                "body_policy": "workspace_refs_sizes_receipts_blockers_only",
                "must_not_emit": [
                    "generic_cleanup_policy",
                    "restore_ready_verdict",
                    "paper_closure_verdict",
                    "publication_ready_verdict",
                    "artifact_mutation_authorization",
                ],
                "can_write_domain_truth": False,
                "can_write_publication_eval": False,
                "can_write_controller_decision": False,
                "can_write_current_package": False,
            },
            "does_not_claim_physical_delete": True,
            "does_not_claim_opl_default_caller": True,
            "does_not_claim_generic_cleanup_policy_owner": True,
            "does_not_touch_publication_or_package_authority": True,
        },
        "proof_refs": ["contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough", "domain_authority_refs_index_contract.opl_artifact_lifecycle_storage_audit_shell"],
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
        "domain_ref_consumers": ["workspace init/readiness CLI", "MCP workspace readiness tools", "product-entry workspace surfaces"],
        "current_ref_status": "domain_source_adapter_active",
        "migration_action": "declare_source_intake_policy_in_pack_and_keep_mas_source_readiness_verdict",
        "retention_reason": "Source quality, medical evidence readiness, and literature relevance remain MAS domain authority.",
        "opl_expected_primitives": ["workspace_source_intake_shell", "source_locator_index"],
        "mas_domain_authority_refs": ["source_readiness_verdict", "evidence_ledger_refs"],
    },
    {
        "module_id": "publication_route_memory_locator_transport_shell",
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "code_paths": [
            "src/med_autoscience/controllers/stage_knowledge_plane.py",
            "src/med_autoscience/controllers/stage_knowledge_plane_parts/publication_route_memory_inventory.py",
            "src/med_autoscience/controllers/stage_knowledge_plane_parts/publication_route_memory_writeback.py",
        ],
        "domain_ref_consumers": ["publication-route memory CLI", "stage knowledge packet", "typed closeout memory writeback"],
        "current_ref_status": "body_free_locator_transport_active",
        "migration_action": "declare_publication_route_memory_refs_no_memory_body_transport",
        "retention_reason": "MAS keeps publication-route memory body, recall policy, and accept/reject/blocker writeback verdict.",
        "opl_expected_primitives": ["generic_memory_locator", "memory_writeback_transport", "body_free_memory_projection"],
        "mas_domain_authority_refs": ["publication_route_memory_body", "memory_writeback_decision"],
    },
    {
        "module_id": "artifact_lifecycle_storage_audit_shell",
        "owner": "med-autoscience",
        "classification": "domain_authority_refs",
        "migration_class": "refs_only_domain_adapter",
        "code_paths": [
            "src/med_autoscience/controllers/artifact_lifecycle_inventory.py", "src/med_autoscience/controllers/artifact_lifecycle_operations_report.py",
            "src/med_autoscience/controllers/artifact_retention_operations_plan.py", "src/med_autoscience/controllers/artifact_lifecycle_authority_kernel.py",
        ],
        "domain_ref_consumers": ["artifact lifecycle CLI/MCP", "product-entry artifact projection"],
        "current_ref_status": "refs_only_artifact_lifecycle_adapter_mas_mutation_authority_active",
        "migration_action": "declare_artifact_refs_audit_and_leave_mutation_authority_in_mas",
        "retention_reason": "Canonical manuscript/package mutation and rebuild proof are MAS artifact authority.",
        "opl_expected_primitives": ["opl_generic_artifact_lifecycle", "opl_artifact_locator", "opl_restore_retention_receipt_shell"],
        "mas_domain_authority_refs": ["artifact_authority", "current_package_authority"],
        "authority_boundary": "opl_owns_lifecycle_shell_mas_authorizes_artifact_mutation",
        "proof_refs": ["contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough", "domain_authority_refs_index_contract.opl_artifact_lifecycle_storage_audit_shell"],
    },
    {
        "module_id": "workbench_portal_generic_shell",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/progress_portal.py", "src/med_autoscience/controllers/progress_portal_parts/",
            "src/med_autoscience/controllers/product_entry_parts/workspace_cockpit/",
            "src/med_autoscience/controllers/product_entry_parts/attention_projection.py",
            "src/med_autoscience/controllers/product_entry_parts/generated_status_projection.py",
        ],
        "domain_ref_consumers": [
            "progress portal read-model materializer",
            "workspace cockpit",
            "product-entry manifest",
        ],
        "current_ref_status": "opl_generated_workbench_surface_consumes_mas_domain_projection_refs",
        "migration_action": "declare_workbench_projection_inputs_for_opl_app_generated_shell",
        "retention_reason": (
            "MAS supplies per-study route map, quality/source refs, blockers, domain-handler owner-route handoff refs, "
            "plus the domain-owned Progress Portal payload/static HTML materializer consumed by OPL hosted workbench refs."
        ),
        "current_surface_refs": [
            "product_status",
            "status_read_model",
            "workbench",
            "workbench_drilldown",
            "portal",
            "cockpit",
        ],
        "opl_expected_primitives": ["opl_generic_workbench", "opl_operator_attention_queue", "opl_route_decision_drilldown_shell"],
        "mas_domain_authority_refs": ["study_progress_projection", "safe_action_refs"],
        "authority_boundary": "opl_hosts_workbench_shell_mas_supplies_refs_only_domain_projection",
        "latest_thinning_evidence": {
            "status": "opl_hosted_workbench_projection_and_read_model_materializer_landed",
            "extracted_paths": [
                "src/med_autoscience/controllers/product_entry_parts/generated_status_projection.py",
                "src/med_autoscience/controllers/product_entry_parts/attention_projection.py",
            ],
            "read_model_materializer_boundary": {
                "status": "domain_owned_read_model_materializer_no_active_workspace_helper",
                "physical_module": (
                    "src/med_autoscience/controllers/progress_portal_parts/"
                    "read_model_materializer.py"
                ),
                "materializer_scope": (
                    "domain_owned_payload_html_and_hosted_package_projection"
                ),
                "active_callers": [],
                "writes_only": [
                    "artifacts/runtime/progress_portal/latest.json",
                    "artifacts/runtime/progress_portal/hosted_package.json",
                    "artifacts/runtime/progress_portal/studies/<study_id>/latest.json",
                    "ops/mas/progress/index.html",
                    "ops/mas/progress/studies/<study_id>/index.html",
                ],
                "does_not_claim": [
                    "workspace_workbench_owner",
                    "status_wrapper_owner",
                    "generic_runtime_owner",
                    "local_http_service_owner",
                    "runtime_control_owner",
                ],
                "domain_repo_physical_delete_authorized": False,
                "retention_reason": (
                    "The retained module materializes MAS-owned read-model evidence and hosted package refs; "
                    "it is not a workspace helper, service wrapper, or runtime control owner."
                ),
                "does_not_write": [
                    "study_truth",
                    "publication_eval/latest.json",
                    "controller_decisions/latest.json",
                    "current_package",
                    "runtime_state",
                ],
            },
            "retired_combined_portal_runtime_soak_provenance": {
                "status": "physically_retired_no_alias",
                "scope": "retired_read_model_evidence_shell_provenance",
                "retired_paths": [
                    "retired_combined_portal_runtime_soak_entry_removed_no_alias",
                    "retired_combined_portal_runtime_soak_parts_removed_no_alias",
                ],
                "domain_ref_consumer_count": 0,
                "replacement_owner": "one-person-lab",
                "replacement_surface": "opl_current_control_state_or_app_workbench_soak",
                "does_not_claim_active_entry": True,
                "does_not_touch_publication_or_package_authority": True,
            },
            "domain_projection_entry_shells": [
                "src/med_autoscience/controllers/product_entry_parts/program_surfaces.py",
                "src/med_autoscience/controllers/product_entry_parts/workspace_attention.py",
                "src/med_autoscience/controllers/product_entry_parts/manifest_surfaces.py",
            ],
            "does_not_claim_physical_delete": True,
            "does_not_claim_opl_default_caller": True,
            "does_not_touch_publication_or_package_authority": True,
        },
        "proof_refs": ["product_entry_manifest.functional_consumer_boundary.generated_surface_handoff", "domain_handler_export.functional_consumer_boundary.generated_surface_handoff"],
    },
    {
        "module_id": "owner_route_reconcile_materialize_dispatch_shell",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/owner_route_reconcile.py", "src/med_autoscience/controllers/domain_action_request_materializer.py",
            "src/med_autoscience/controllers/domain_owner_action_dispatch.py",
            "src/med_autoscience/controllers/default_executor_action_policy.py",
        ],
        "retired_code_paths": ["src/med_autoscience/controllers/domain_route_reconcile.py"],
        "domain_ref_consumers": ["owner-route one-shot tick", "runtime owner-route reconcile", "domain-handler dispatch"],
        "current_ref_status": "opl_runtime_manager_loop_consumed_mas_owner_route_guard_active",
        "migration_action": "declare_owner_route_policy_and_consume_opl_runtime_manager_loop",
        "retention_reason": "MAS must keep owner-route facts, publication gate blockers, safe action refs, and no-forbidden-write evidence.",
        "current_surface_refs": [
            "domain_handler",
            "domain_handler_export",
            "domain_handler_dispatch",
        ],
        "opl_expected_primitives": ["opl_generic_runner", "opl_attempt_retry_dead_letter", "opl_repair_projection", "opl_provider_runtime_manager"],
        "mas_domain_authority_refs": ["owner_route", "publication_gate", "safe_action_refs"],
        "authority_boundary": "opl_scans_and_dispatches_generic_loop_mas_guards_domain_route_and_receipt",
        "latest_thinning_evidence": {
            "status": "default_executor_action_policy_single_source_landed",
            "policy_module": "src/med_autoscience/controllers/default_executor_action_policy.py",
            "thin_entrypoints": [
                "src/med_autoscience/controllers/domain_action_request_materializer.py",
                "src/med_autoscience/controllers/domain_owner_action_dispatch.py",
            ],
            "single_source_fields": [
                "supported_action_types",
                "forbidden_surfaces",
                "retired_absent_surfaces",
                "allowed_write_surfaces",
                "source_action_ref_fields",
                "source_handoff_ref_fields",
                "request_owner_by_action_type",
                "request_output_surface_by_action_type",
                "request_packet_ref_by_action_type",
            ],
            "domain_repo_physical_delete_authorized": False,
            "does_not_write": [
                "study_truth",
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "memory_body",
                "artifact_body",
            ],
            "does_not_claim": [
                "owner_chain_closed",
                "domain_ready",
                "production_ready",
                "publication_ready",
                "artifact_mutation_authorized",
            ],
        },
        "proof_refs": ["contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough", "product_entry_manifest.functional_consumer_boundary.opl_functional_harness_consumer_coverage"],
    },
    {
        "module_id": "generic_cli_mcp_product_wrappers",
        "owner": "med-autoscience",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/domain_entry.py",
            "src/med_autoscience/controllers/product_entry.py",
            "src/med_autoscience/controllers/owner_route_handoff.py",
            "plugins/mas/skills/mas/SKILL.md",
        ],
        "domain_ref_consumers": ["MAS CLI", "MCP tool handlers", "skill direct domain entry", "product-entry manifest"],
        "current_ref_status": "domain_handlers_active_opl_generated_wrapper_metadata_consumed",
        "migration_action": "derive_wrapper_metadata_from_declarative_pack_and_opl_generated_surfaces",
        "retention_reason": "MAS keeps domain command handlers, direct domain entry, and owner receipts; OPL owns CLI/MCP/Skill/product/status descriptor projection and routing shell.",
        "current_surface_refs": [
            "cli",
            "mcp",
            "skill",
            "product_entry",
            "product_entry_manifest",
            "product_session",
        ],
        "opl_expected_primitives": [
            "opl_action_catalog_projection",
            "opl_product_entry_shell",
            "opl_mcp_descriptor_projection",
            "opl_skill_descriptor_projection",
            "opl_generated_command_surface",
        ],
        "mas_domain_authority_refs": ["domain_action_handler", "owner_receipt"],
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
            "src/med_autoscience/controllers/opl_unique_control_plane_boundary_parts/",
        ],
        "domain_ref_consumers": ["opl_current_control_state owner refs"],
        "current_ref_status": "opl_replacement_default_local_tombstone_only",
        "migration_action": "declare_scheduler_requirement_in_pack_and_keep_retired_provenance_refs",
        "retention_reason": "MAS supplies paper-progress domain SLO semantics and retired scheduler provenance refs only; OPL owns lifecycle, cadence, queue, attempt, and control.",
        "opl_expected_primitives": ["scheduler_lifecycle", "cadence_slo", "provider_slo"],
        "mas_domain_authority_refs": ["paper_progress_slo_semantics", "typed_blocker"],
    },
    {
        "module_id": "generic_queue_attempt_retry_dead_letter",
        "owner": "one-person-lab",
        "classification": "declarative_pack_generated_surface",
        "code_paths": [
            "src/med_autoscience/controllers/study_runtime_execution_parts/controller_authorization_receipts.py",
        ],
        "domain_ref_consumers": ["OPL provider stage runtime", "MAS owner receipt / typed blocker consumers"],
        "current_ref_status": "opl_owned_runtime_control_mas_consumes_closeout_refs",
        "migration_action": "declare_queue_attempt_requirements_and_return_mas_stage_closeout_receipts",
        "retention_reason": "OPL owns queue/attempt/retry/dead-letter; MAS keeps stage closeout semantics, owner receipts, and typed blockers.",
        "opl_expected_primitives": ["opl_generic_queue", "opl_attempt_ledger", "opl_retry_dead_letter", "opl_worker_lifecycle_transport"],
        "mas_domain_authority_refs": ["stage_closeout_domain_semantics", "owner_receipt"],
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
        "domain_ref_consumers": ["study-state-matrix CLI", "runtime consumer guard", "OPL transition descriptor"],
        "current_ref_status": "domain_transition_spec_active_generic_runner_owned_by_opl",
        "migration_action": "declare_domain_transition_spec_for_opl_generic_runner",
        "retention_reason": "MAS owns medical transition semantics and oracle fixtures; OPL executes the generic state-machine transport.",
        "opl_expected_primitives": ["generic_transition_runner", "transition_matrix_runner", "idempotent_tick"],
        "mas_domain_authority_refs": ["domain_transition_table", "publication_quality_verdict", "artifact_authority"],
    },
    {
        "module_id": "study_truth",
        "owner": "med-autoscience",
        "classification": "minimal_authority_function",
        "code_paths": [
            "src/med_autoscience/controllers/study_truth_kernel.py",
            "src/med_autoscience/controllers/progress_projection.py",
        ],
        "domain_ref_consumers": ["MAS controller owner route", "study progress/read models"],
        "current_ref_status": "domain_authority_active",
        "migration_action": "authority_stays_in_mas",
        "cannot_absorb_reason": "Medical study truth and paper route state are domain facts, not framework runtime state.",
        "mas_domain_authority_refs": ["study_truth", "progress_projection"],
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
        "domain_ref_consumers": ["AI reviewer workflow", "publication gate", "controller decision"],
        "current_ref_status": "domain_authority_active",
        "migration_action": "authority_stays_in_mas",
        "cannot_absorb_reason": "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts.",
        "mas_domain_authority_refs": ["publication_quality_verdict", "ai_reviewer_workflow", "publication_gate"],
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
        "domain_ref_consumers": ["delivery sync", "package freshness proof", "submission package handoff"],
        "current_ref_status": "domain_authority_active",
        "migration_action": "authority_stays_in_mas",
        "cannot_absorb_reason": "Canonical manuscript/package mutation and submission authority are MAS artifact authority.",
        "mas_domain_authority_refs": ["artifact_authority", "current_package_authority"],
    },
)

FUNCTIONAL_MODULE_INVENTORY = tuple(
    _module_with_retirement_gate(dict(item)) for item in _FUNCTIONAL_MODULE_INVENTORY
)


__all__ = [
    "FUNCTIONAL_MODULE_INVENTORY",
    "FUNCTIONAL_SURFACE_CLASSIFICATION",
    "DOMAIN_AUTHORITY_REFS_RETIREMENT_GATE_BY_MODULE",
]
