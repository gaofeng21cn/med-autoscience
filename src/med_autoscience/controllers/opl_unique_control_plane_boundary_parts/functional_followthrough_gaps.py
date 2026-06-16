from __future__ import annotations

from typing import Any, Mapping, Sequence


FUNCTIONAL_FOLLOWTHROUGH_GATES_OPEN_STATUS = "functional_structure_closed_evidence_gates_remaining"
FUNCTIONAL_FOLLOWTHROUGH_GAPS_OPEN_STATUS = FUNCTIONAL_FOLLOWTHROUGH_GATES_OPEN_STATUS
REMAINING_GAP_CLASSIFICATION = "live_provider_paper_line_evidence_gates"
FUNCTIONAL_STRUCTURE_GAPS_REMAINING_STATUS = "functional_structure_gaps_remaining"
FUNCTIONAL_STRUCTURE_GAP_CLASSIFICATION = "functional_structure_followthrough_gates"
SOURCE_PURITY_CUTOVER_STATUS = "standard_agent_source_shape_landed"
SOURCE_PURITY_WRAPPER_TAIL_MODULE_IDS = (
    "generic_cli_mcp_product_wrappers",
    "owner_route_reconcile_materialize_dispatch_shell",
    "workbench_portal_generic_shell",
)
MEMORY_ARTIFACT_LIFECYCLE_TYPED_BLOCKER_REFS = (
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:03e1b65c724fc91f",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:0a79716a4521d4e7",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:0eddcbbdc5562e85",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:0f60da7b33a944c1",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:19fa86de7ad80bed",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:1c4669a3d231cc2c",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:491c4337a5e681da",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:6bfabaa6003c4b81",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:6fddc0536a914bee",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:7396b830d92bc7dd",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:754b9b392635185d",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:756cc134178fc352",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:77c62f01a68769cb",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:7c79b10711ac8196",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:85eb3bad050dd032",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:89cb33e8b8e7ed40",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:a657c0b52dc8b8f6",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:b2559106748cdf75",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:b35e7e741683d0b2",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:d9ddaca76a5e9922",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:db76ae5f690d9285",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:dbc1de0fecfaf084",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:df7ac9400b641e86",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:e5ccb4e804e5c97f",
    "mas-artifact-lifecycle-typed-blocker:medautoscience:canonical-regeneration-required-before-projection-removal:ee885717be533f07",
)

MEMORY_ARTIFACT_LIFECYCLE_OWNER_FOLLOWTHROUGH = {
    "surface_kind": "mas_memory_artifact_lifecycle_owner_followthrough",
    "status": "typed_blocker_followthrough_recorded_not_ready",
    "source_work_order_ref": (
        "opl:runtime/app-operator-drilldown/memory_artifact_lifecycle/"
        "memory-artifact-lifecycle-owner-decision"
    ),
    "source_lane_id": "memory_artifact_lifecycle_apply",
    "source_readiness_status": "typed_blocker_work_order_required_not_ready",
    "source_projection_policy": (
        "refs_only_counts_from_memory_artifact_package_export_domain_dispatch_"
        "and_lifecycle_surfaces_no_body_or_mutation_authority"
    ),
    "observed_ref_count": 126,
    "source_open_count": 0,
    "open_count_zero_can_claim_ready": False,
    "typed_blocker_reason": "canonical-regeneration-required-before-projection-removal",
    "typed_blocker_ref_count": len(MEMORY_ARTIFACT_LIFECYCLE_TYPED_BLOCKER_REFS),
    "typed_blocker_refs": list(MEMORY_ARTIFACT_LIFECYCLE_TYPED_BLOCKER_REFS),
    "safe_decision_count": 0,
    "blocked_decision_count": len(MEMORY_ARTIFACT_LIFECYCLE_TYPED_BLOCKER_REFS),
    "accepted_owner_result_shape": "typed_blocker_ref",
    "owner_followthrough_kind": "stable_typed_blocker_refs",
    "closes_work_order_followthrough": True,
    "closes_artifact_lifecycle_receipt_scaleout": False,
    "closes_memory_or_artifact_ready": False,
    "domain_repo_physical_delete_authorized": False,
    "ready_claim_authorized": False,
    "forbidden_claims": [
        "memory_body_saved_or_accepted",
        "artifact_body_mutated",
        "artifact_ready",
        "package_ready",
        "export_ready",
        "domain_ready",
        "production_ready",
        "domain_physical_delete_authorization",
    ],
    "authority_boundary": {
        "mas_writes_domain_truth": False,
        "mas_writes_memory_body": False,
        "mas_mutates_artifact_body": False,
        "mas_authorizes_package_readiness": False,
        "mas_authorizes_export_readiness": False,
        "opl_cleanup_apply_can_execute": True,
        "opl_can_claim_domain_ready": False,
        "opl_can_claim_production_ready": False,
    },
}

FUNCTIONAL_STRUCTURE_CLOSURE_GATES = (
    {
        "gate_id": "generated_surface_default_owner_cutover",
        "owner": "one-person-lab",
        "mas_role": "provide_pack_input_handoff_refs_and_no_forbidden_write_guard",
        "evidence_required": "OPL generated surfaces own default shells, MAS exposes domain refs/handlers only, focused no-regression lane green",
        "closure_status": "closed",
        "closure_proof_refs": [
            "contracts/generated_surface_handoff.json",
            "contracts/pack_compiler_input.json",
            "opl agents interfaces --repo-dir /Users/gaofeng/workspace/med-autoscience --json",
        ],
        "functional_structure_gap": False,
    },
    {
        "gate_id": "domain_authority_refs_thinning",
        "owner": "med-autoscience",
        "mas_role": "export_body_free_locator_receipt_blocker_refs_only",
        "evidence_required": "SQLite/lifecycle, outbox, storage, source, memory, artifact, portal, and supervisor shells only expose refs/blockers/receipts",
        "closure_status": "closed",
        "closure_proof_refs": [
            "functional_module_inventory.domain_authority_refs",
            "domain_authority_refs_index_role.refs_only_domain_authority_index_not_generic_runtime_lifecycle_engine",
            "opl_functional_harness_consumer_coverage.refs_only_memory_writeback_chain",
        ],
        "functional_structure_gap": False,
    },
    {
        "gate_id": "standard_agent_purity_guard",
        "owner": "med-autoscience",
        "mas_role": "keep_active_default_surfaces_in_standard_opl_agent_shape",
        "evidence_required": "OPL default caller readiness is present; repo-local source shape is reduced to domain handlers, refs-only projections, and workspace read-model carrier boundary without generic owner claims",
        "closure_status": "closed",
        "closure_proof_refs": [
            "functional_consumer_boundary.standard_agent_purity",
            "opl_unique_control_plane_handoff.standard_agent_purity",
            "functional_consumer_boundary.standard_agent_purity_guard.status=standard_agent_purity_cutover_guard",
            "progress_portal_parts.read_model_materializer.read_model_materializer_boundary",
        ],
        "functional_structure_gap": False,
        "former_wrapper_tail_module_ids": list(SOURCE_PURITY_WRAPPER_TAIL_MODULE_IDS),
        "physical_delete_authorized": False,
        "delete_or_tombstone_after": [
            "OPL generated/default caller parity remains green",
            "MAS owner receipt or stable typed blocker authorizes wrapper retirement",
            "no-active-caller proof covers repo-local product/status/workbench/domain-handler/controller/progress shell",
            "tombstone/provenance proof exists before physical deletion",
        ],
    },
    {
        "gate_id": "opl_app_workbench_drilldown",
        "owner": "one-person-lab",
        "mas_role": "provide_domain_route_quality_artifact_memory_and_owner_route_handoff_refs",
        "evidence_required": "OPL App/Workbench displays refs, freshness, blockers, owners, and owner-route handoff routing",
        "closure_status": "closed",
        "closure_proof_refs": [
            "workbench_portal_generic_shell.proof_refs",
            "opl_functional_harness_consumer_coverage.restart_dead_letter_repair_human_gate_state_chain",
            "OPL runtime-app-operator-drilldown read model",
        ],
        "functional_structure_gap": False,
    },
    {
        "gate_id": "lifecycle_locator_retention_restore_ledger_reconciliation",
        "owner": "one-person-lab",
        "mas_role": "return_domain_artifact_authority_receipt_refs_only",
        "evidence_required": "OPL lifecycle/index ledger consumes MAS lifecycle refs without writing MAS truth, memory body, or artifacts",
        "closure_status": "closed",
        "closure_proof_refs": [
            "domain_authority_refs_index_role.mas_consumes_opl_current_control_state_refs=true",
            "artifact_lifecycle_storage_audit_shell.proof_refs",
            "OPL current_control_state read model",
        ],
        "functional_structure_gap": False,
    },
    {
        "gate_id": "domain_ref_consumer_physical_thinning",
        "owner": "med-autoscience",
        "mas_role": "thin_domain_ref_consumers_to_owner_refs_receipts_blockers_and_medical_helpers",
        "evidence_required": "generic locator/index/projection shell is moved to OPL primitives, reduced to refs-only domain adapters, or isolated as delete-gated workspace read-model carrier",
        "closure_status": "closed",
        "closure_proof_refs": [
            "functional_module_inventory.domain_authority_refs",
            "domain_authority_refs_index_role.refs_only_domain_authority_index_not_generic_runtime_lifecycle_engine",
            "workbench_portal_generic_shell.read_model_materializer_boundary",
        ],
        "functional_structure_gap": False,
        "former_wrapper_tail_module_ids": [
            "workbench_portal_generic_shell",
            "owner_route_reconcile_materialize_dispatch_shell",
        ],
        "physical_delete_authorized": False,
        "delete_or_tombstone_after": [
            "body-free owner refs and typed blockers remain available",
            "generic locator/index/projection responsibility has an OPL primitive replacement",
            "MAS retained path is proven minimal authority or domain-native helper",
        ],
    },
)

FUNCTIONAL_FOLLOWTHROUGH_GATES = FUNCTIONAL_STRUCTURE_CLOSURE_GATES

REMAINING_EVIDENCE_GATES = (
    {
        "gate_id": "live_provider_paper_apply_scaleout",
        "owner": "med-autoscience",
        "mas_role": "return_owner_receipt_artifact_delta_gate_replay_human_gate_stop_loss_or_typed_blocker",
        "evidence_required": "multi paper-line OPL provider attempts leave MAS owner receipts and no-forbidden-write proof",
        "functional_structure_gap": False,
    },
    {
        "gate_id": "publication_route_memory_receipt_scaleout",
        "owner": "med-autoscience",
        "mas_role": "accept_reject_or_block_publication_route_memory_writeback_in_workspace_owner_surface",
        "evidence_required": "more real paper-line accepted/rejected/blocked router receipts and body-free inventory refs",
        "functional_structure_gap": False,
    },
    {
        "gate_id": "artifact_lifecycle_receipt_scaleout",
        "owner": "med-autoscience",
        "mas_role": "authorize_artifact_mutation_and_surface_refs_only_cleanup_restore_retention_receipts",
        "evidence_required": "real workspace cleanup, restore, retention, rebuild, and artifact-authority receipt instances",
        "functional_structure_gap": False,
    },
    {
        "gate_id": "provider_slo_long_soak",
        "owner": "one-person-lab",
        "mas_role": "consume_provider_attempt_receipts_without_claiming_paper_closure",
        "evidence_required": "long provider SLO, restart/re-query, retry/dead-letter, and domain activity soak evidence",
        "functional_structure_gap": False,
    },
)

OPL_REPLACEMENT_EXPECTATION_AUDIT = {
    "owner": "one-person-lab",
    "required_before_mas_generic_owner_claim": True,
    "audit_ref": "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough",
    "expected_replacements": [
        "opl_runtime_lifecycle_index_contract",
        "opl_artifact_lifecycle_storage_audit_shell",
        "opl_app_workbench_shell",
        "opl_provider_scheduler_lifecycle",
        "opl_queue_attempt_retry_dead_letter",
        "opl_generic_transition_runner",
    ],
    "mas_allowed_role_until_replacement": "domain_authority_refs_index_refs_only",
}

PRIVATE_SURFACE_RETIREMENT_GATE_CHECKLIST = {
    "surface_kind": "mas_private_surface_retirement_gate_checklist",
    "completion_percent_policy": (
        "do_not_report_100_percent_without_fresh_live_owner_or_OPL_readback_"
        "evidence_for_each_open_gate"
    ),
    "gate_items": [
        {
            "gate_id": "no_active_caller",
            "required_evidence": (
                "repo scan or OPL generated default-caller report proves the "
                "legacy MAS surface has no default/runtime caller"
            ),
            "status": "required_before_physical_delete",
        },
        {
            "gate_id": "replacement_parity",
            "required_evidence": (
                "OPL primitive or generated surface consumes the same refs and "
                "preserves MAS owner-answer boundary"
            ),
            "status": "required_before_physical_delete",
        },
        {
            "gate_id": "no_forbidden_write_proof",
            "required_evidence": (
                "proof shows the replacement/projection did not write study truth, "
                "memory body, artifact body, publication eval, controller decision, "
                "current package, owner receipt, or typed blocker"
            ),
            "status": "required_before_physical_delete",
        },
        {
            "gate_id": "tombstone_or_provenance",
            "required_evidence": (
                "history/tombstone/provenance ref exists before removing legacy "
                "entrypoint or wrapper"
            ),
            "status": "required_before_physical_delete",
        },
        {
            "gate_id": "live_owner_or_stable_blocker",
            "required_evidence": (
                "fresh MAS owner receipt, stable typed blocker, human gate, "
                "route-back evidence, or same-current-identity OPL StageRun readback "
                "exists when claiming runtime completion"
            ),
            "status": "required_before_completion_claim",
        },
    ],
}

PRIVATE_SURFACE_RETIREMENT_GATE_POLICY = {
    "surface_kind": "mas_private_surface_retirement_gate_policy",
    "active_caller_alone_retains_surface": False,
    "allowed_dispositions": [
        "opl_primitive",
        "temporary_refs_projection",
        "retained_minimal_authority_function",
        "tombstone_only",
    ],
    "forbidden_retention_reasons": [
        "current_tests_green",
        "legacy_caller_exists",
        "read_model_projection_needed",
        "operator_ui_uses_path",
        "docs_reference_exists",
    ],
    "must_not_claim": [
        "live_runtime_ready",
        "publication_ready",
        "domain_ready",
        "production_ready",
        "physical_delete_authorized",
        "100_percent_complete_without_live_proof",
    ],
    "required_fields": [
        "disposition",
        "replacement_owner",
        "no_active_caller",
        "replacement_parity",
        "no_forbidden_write_proof",
        "tombstone_or_provenance",
        "retirement_gate",
    ],
}

PRIVATE_SURFACE_RETIREMENT_DISPOSITION_MATRIX = {
    "surface_kind": "mas_private_surface_retirement_disposition_matrix",
    "classification_source": "functional_consumer_boundary.functional_module_inventory",
    "source_of_truth_chain": (
        "DomainIntent -> OPL Command/Event/Outbox/StageRun -> MAS OwnerAnswer -> "
        "Derived Projection"
    ),
    "completion_claim_policy": {
        "contracts_or_tests_alone_can_claim_100_percent": False,
        "live_proof_required_before_100_percent": True,
        "ready_claim_authorized": False,
    },
    "required_retirement_gate_fields": [
        "no_active_caller",
        "no_forbidden_write_proof",
        "replacement_parity",
        "retirement_gate",
        "tombstone_or_provenance",
    ],
    "surface_dispositions": [
        {
            "disposition": "tombstone_only",
            "module_ids": ["generic_daemon_or_scheduler_lifecycle"],
            "no_active_caller": "required_before_physical_delete_or_removed_from_default_caller",
            "no_forbidden_write_proof": "required",
            "replacement_parity": "opl_scheduler_provider_lifecycle_or_retired_provenance_only",
            "retirement_gate": "tombstone_or_provenance_only_no_runtime_owner_resurrection",
            "tombstone_or_provenance": "required",
        },
        {
            "disposition": "opl_primitive_replacement",
            "module_ids": [
                "generic_queue_attempt_retry_dead_letter",
                "generic_transition_runner",
            ],
            "no_active_caller": "required_before_mas_physical_delete",
            "no_forbidden_write_proof": "required",
            "replacement_parity": (
                "OPL queue_attempt_retry_dead_letter_and_transition_runtime_readback"
            ),
            "retirement_gate": "OPL primitive parity plus MAS owner-answer consumption",
            "tombstone_or_provenance": "required",
        },
        {
            "disposition": "temporary_refs_projection",
            "module_ids": [
                "domain_authority_refs_index",
                "paper_progress_transition_refs",
                "runtime_storage_maintenance",
                "publication_route_memory_locator_transport_shell",
                "artifact_lifecycle_storage_audit_shell",
                "workspace_source_intake_shell",
                "workbench_portal_generic_shell",
                "owner_route_reconcile_materialize_dispatch_shell",
                "generic_cli_mcp_product_wrappers",
            ],
            "no_active_caller": (
                "required_before_physical_delete_not_required_for_refs_projection_retention"
            ),
            "no_forbidden_write_proof": "required",
            "replacement_parity": (
                "OPL generated_or_hosted_surface_consumes_same_refs_without_MAS_"
                "generic_owner_claim"
            ),
            "retirement_gate": (
                "retain_only_as_refs_receipts_blockers_locators_or_body_free_"
                "diagnostic_projection_until_parity"
            ),
            "tombstone_or_provenance": "required_before_removing_legacy_entrypoint",
        },
        {
            "disposition": "retained_minimal_authority_function",
            "module_ids": [
                "study_truth",
                "publication_quality_verdict",
                "artifact_authority",
                "owner_receipt",
                "typed_blocker",
                "safe_action_refs",
                "domain_transition_table",
                "publication_route_memory_body",
                "memory_writeback_decision",
            ],
            "no_active_caller": "not_required_for_retention_required_before_retirement",
            "no_forbidden_write_proof": "required",
            "replacement_parity": "not_replaceable_by_OPL_generic_runtime_only_refs_transport_allowed",
            "retirement_gate": (
                "retained_until_MAS_owner_answer_or_authority_record_supersedes_surface"
            ),
            "tombstone_or_provenance": "required_if_surface_is_later_retired",
        },
    ],
}


def _closure_gate_is_closed(gate: Mapping[str, Any]) -> bool:
    proof_refs = gate.get("closure_proof_refs")
    return (
        gate.get("closure_status") == "closed"
        and gate.get("functional_structure_gap") is False
        and isinstance(proof_refs, Sequence)
        and not isinstance(proof_refs, (str, bytes))
        and len(proof_refs) > 0
    )


def build_functional_followthrough_gap_summary(
    *,
    classification_counts: Mapping[str, int],
) -> dict[str, Any]:
    closure_gates = [dict(item) for item in FUNCTIONAL_STRUCTURE_CLOSURE_GATES]
    closed_functional_structure_gates = [
        item for item in closure_gates if _closure_gate_is_closed(item)
    ]
    remaining_functional_followthrough_gates = [
        item for item in closure_gates if not _closure_gate_is_closed(item)
    ]
    closure_gate_ids = [str(item["gate_id"]) for item in closed_functional_structure_gates]
    remaining_functional_followthrough_gate_ids = [
        str(item["gate_id"]) for item in remaining_functional_followthrough_gates
    ]
    evidence_gate_ids = [str(item["gate_id"]) for item in REMAINING_EVIDENCE_GATES]
    functional_structure_gap_count = len(remaining_functional_followthrough_gates)
    remaining_items_are_evidence_gates = functional_structure_gap_count == 0
    return {
        "surface_kind": "mas_functional_followthrough_gap_summary",
        "status": (
            FUNCTIONAL_FOLLOWTHROUGH_GATES_OPEN_STATUS
            if remaining_items_are_evidence_gates
            else FUNCTIONAL_STRUCTURE_GAPS_REMAINING_STATUS
        ),
        "classification_gap_count": 0,
        "functional_structure_gap_count": functional_structure_gap_count,
        "active_private_generic_residue_count": 0,
        "repo_local_wrapper_tail_count": 0,
        "repo_local_wrapper_tail_module_ids": [],
        "former_repo_local_wrapper_tail_module_ids": list(SOURCE_PURITY_WRAPPER_TAIL_MODULE_IDS),
        "default_caller_readiness_status": "opl_generated_default_caller_ready",
        "source_purity_cutover_status": SOURCE_PURITY_CUTOVER_STATUS,
        "domain_repo_physical_delete_authorized": False,
        "remaining_gap_classification": (
            REMAINING_GAP_CLASSIFICATION
            if remaining_items_are_evidence_gates
            else FUNCTIONAL_STRUCTURE_GAP_CLASSIFICATION
        ),
        "remaining_items_are_evidence_gates": remaining_items_are_evidence_gates,
        "remaining_functional_followthrough_gate_ids": remaining_functional_followthrough_gate_ids,
        "remaining_functional_followthrough_gates": remaining_functional_followthrough_gates,
        "closed_functional_structure_gate_ids": closure_gate_ids,
        "closed_functional_structure_gates": closed_functional_structure_gates,
        "classification_counts": dict(classification_counts),
        "remaining_evidence_gate_ids": evidence_gate_ids,
        "remaining_evidence_gates": [dict(item) for item in REMAINING_EVIDENCE_GATES],
        "owner_followthrough_evidence": [
            dict(MEMORY_ARTIFACT_LIFECYCLE_OWNER_FOLLOWTHROUGH),
        ],
        "retirement_gate_checklist": {
            key: [dict(item) for item in value] if isinstance(value, list) else value
            for key, value in PRIVATE_SURFACE_RETIREMENT_GATE_CHECKLIST.items()
        },
        "cleared_by_surfaces": [
            "functional_module_inventory",
            "declarative_pack_compiler_input",
            "generated_surface_handoff",
            "minimal_authority_function_manifest",
            "stale_surface_scan_clean",
            "opl_functional_harness_consumer_coverage",
            "opl_generated_interface_default_owner_target_proof",
            "opl_app_operator_workbench_drilldown",
            "opl_lifecycle_index_cleanup_restore_ledger",
        ],
        "clears_only": "functional_structure_closure_not_live_paper_soak_or_publication_ready",
        "does_not_clear": [
            *evidence_gate_ids,
        ],
        "forbidden_remaining_functional_gap_claims": [
            "mas_owned_generic_scheduler",
            "mas_owned_generic_queue",
            "mas_owned_attempt_ledger",
            "mas_owned_generic_transition_runner",
            "mas_owned_generic_workbench",
            "mas_owned_generic_memory_locator",
            "mas_owned_generic_artifact_lifecycle",
            "mas_owned_generic_observability",
        ],
    }
