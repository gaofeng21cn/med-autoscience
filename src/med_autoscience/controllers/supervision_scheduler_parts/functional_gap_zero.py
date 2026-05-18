from __future__ import annotations

from typing import Any, Mapping, Sequence


FUNCTIONAL_GAP_ZERO_STATUS = "classification_closed_followthrough_gaps_open"
REMAINING_GAP_CLASSIFICATION = "functional_followthrough_and_test_evidence_gates"

FUNCTIONAL_FOLLOWTHROUGH_GATES = (
    {
        "gate_id": "generated_surface_active_caller_cutover",
        "owner": "one-person-lab",
        "mas_role": "provide_pack_input_handoff_refs_and_no_forbidden_write_guard",
        "evidence_required": "OPL generated surfaces available, active callers migrated, focused no-regression lane green",
        "functional_structure_gap": True,
    },
    {
        "gate_id": "refs_only_adapter_thinning",
        "owner": "med-autoscience",
        "mas_role": "export_body_free_locator_receipt_blocker_refs_only",
        "evidence_required": "SQLite/lifecycle, outbox, storage, source, memory, artifact, portal, and supervisor shells only expose refs/blockers/receipts",
        "functional_structure_gap": True,
    },
    {
        "gate_id": "legacy_cleanup_physical_retirement",
        "owner": "med-autoscience",
        "mas_role": "remove_or_tombstone_legacy_launchagent_and_workspace_local_wrapper_surfaces",
        "evidence_required": "no-active-caller scan, old generated artifact absent/remove proof, provenance retained, focused cleanup tests green",
        "functional_structure_gap": True,
    },
    {
        "gate_id": "opl_app_workbench_drilldown",
        "owner": "one-person-lab",
        "mas_role": "provide_domain_route_quality_artifact_memory_and_safe_action_refs",
        "evidence_required": "OPL App/Workbench displays refs, freshness, blockers, owners, and action receipt routing",
        "functional_structure_gap": True,
    },
    {
        "gate_id": "lifecycle_locator_retention_restore_ledger_reconciliation",
        "owner": "one-person-lab",
        "mas_role": "return_domain_artifact_authority_receipt_refs_only",
        "evidence_required": "OPL lifecycle/index ledger consumes MAS lifecycle refs without writing MAS truth, memory body, or artifacts",
        "functional_structure_gap": True,
    },
)

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
        "opl_terminal_attach_transport",
        "opl_provider_scheduler_lifecycle",
        "opl_queue_attempt_retry_dead_letter",
        "opl_generic_transition_runner",
    ],
    "mas_allowed_role_until_replacement": "domain_sidecar_reference_adapter_refs_only",
}


def build_functional_followthrough_gap_summary(
    *,
    classification_counts: Mapping[str, int],
    legacy_cleanup_items: Sequence[str],
) -> dict[str, Any]:
    followthrough_gate_ids = [str(item["gate_id"]) for item in FUNCTIONAL_FOLLOWTHROUGH_GATES]
    evidence_gate_ids = [str(item["gate_id"]) for item in REMAINING_EVIDENCE_GATES]
    return {
        "surface_kind": "mas_functional_followthrough_gap_summary",
        "status": FUNCTIONAL_GAP_ZERO_STATUS,
        "classification_gap_count": 0,
        "functional_structure_gap_count": len(FUNCTIONAL_FOLLOWTHROUGH_GATES),
        "active_private_generic_residue_count": 0,
        "remaining_gap_classification": REMAINING_GAP_CLASSIFICATION,
        "remaining_items_are_evidence_gates": False,
        "remaining_functional_followthrough_gate_ids": followthrough_gate_ids,
        "remaining_functional_followthrough_gates": [
            dict(item) for item in FUNCTIONAL_FOLLOWTHROUGH_GATES
        ],
        "classification_counts": dict(classification_counts),
        "legacy_cleanup_items_require_no_active_caller_gate": list(legacy_cleanup_items),
        "legacy_cleanup_items_are_diagnostic_provenance_guards": True,
        "legacy_cleanup_item_role": "cleanup_diagnostic_provenance_drift_guard_no_active_default_caller",
        "legacy_cleanup_items_are_remaining_active_gaps": True,
        "legacy_cleanup_items_have_default_entry": False,
        "legacy_cleanup_items_have_standard_template_refs": False,
        "remaining_evidence_gate_ids": evidence_gate_ids,
        "remaining_evidence_gates": [dict(item) for item in REMAINING_EVIDENCE_GATES],
        "cleared_by_surfaces": [
            "functional_module_inventory",
            "declarative_pack_compiler_input",
            "generated_surface_handoff",
            "minimal_authority_function_manifest",
            "no_active_caller_proof",
            "opl_functional_harness_consumer_coverage",
        ],
        "clears_only": "classification_and_long_term_generic_owner_claims",
        "does_not_clear": [
            "generated_surface_active_caller_cutover",
            "refs_only_adapter_thinning",
            "legacy_cleanup_physical_retirement",
            "opl_app_workbench_drilldown",
            "lifecycle_locator_retention_restore_ledger_reconciliation",
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
