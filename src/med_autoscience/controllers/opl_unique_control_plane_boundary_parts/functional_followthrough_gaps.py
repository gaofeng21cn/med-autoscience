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
            "progress_portal_parts.workspace_carrier.hosted_runtime_carrier_contract",
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
            "workbench_portal_generic_shell.workspace_carrier_boundary",
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
