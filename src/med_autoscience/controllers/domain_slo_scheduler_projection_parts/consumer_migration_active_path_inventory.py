from __future__ import annotations

from med_autoscience.controllers.domain_slo_scheduler_projection_parts.active_path_workbench_status_gates import (
    build_workbench_status_active_path_gates,
)

_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER = (
    "stale_surface_scan_clean",
    "opl_replacement_parity_proven",
    "domain_receipt_parity_proven",
    "focused_tests_green",
    "no_forbidden_write_proof",
    "history_tombstone_refs_recorded",
)
_ACTIVE_PATH_MUST_NOT_EMIT = (
    "generic_scheduler_owner",
    "generic_queue_owner",
    "generic_attempt_ledger_owner",
    "generic_worker_residency_owner",
    "generic_persistence_engine_owner",
    "generic_workbench_owner",
    "paper_closure_verdict",
    "publication_ready_verdict",
    "artifact_mutation_authorization_without_mas_receipt",
)

ACTIVE_PATH_RESIDUE_CLEANUP_GATES = (
    {
        "residue_id": "runtime_transport_core_bridge",
        "residue_class": "runtime_transport",
        "current_paths": [],
        "retired_paths": [
            "src/med_autoscience/runtime_transport/mas_runtime_core.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_pause_resume.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_stopped_relaunch.py",
        ],
        "current_role": "none_physically_retired_no_alias",
        "current_disposition": "physically_retired",
        "retirement_proof_status": "stale_surface_scan_clean",
        "stale_surface_scan_clean": True,
        "no_resurrection_guard": True,
        "opl_replacement_parity_status": "opl_provider_handoff_active",
        "domain_receipt_parity_status": "domain_intent_handoff_blocker_active",
        "physical_delete_permitted": True,
        "physical_delete_completed": True,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
        "retirement_proof_refs": [
            "tests.test_adapter_retirement_boundary.no_runtime_transport_core_resurrection",
            "runtime_backend.no_lazy_mas_runtime_core_backend",
        ],
        "focused_test_refs": [
            "tests/test_opl_runtime_contract.py",
            "tests/test_opl_runtime_contract_no_provider_backend.py",
            "tests/test_adapter_retirement_boundary.py",
        ],
        "resurrection_alias_or_wrapper_allowed": False,
        "must_not_emit": list(_ACTIVE_PATH_MUST_NOT_EMIT),
    },
    {
        "residue_id": "runtime_turn_runner_closeout_adapter",
        "residue_class": "runtime_transport",
        "current_paths": [],
        "retired_paths": [
            "src/med_autoscience/runtime_transport/mas_runtime_core_turn_runner.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_turn_completion.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_turn_receipts.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_turn_messages.py",
        ],
        "current_role": "none_physically_retired_no_alias",
        "current_disposition": "physically_retired",
        "retirement_proof_status": "stale_surface_scan_clean",
        "stale_surface_scan_clean": True,
        "no_resurrection_guard": True,
        "opl_replacement_parity_status": "typed_closeout_owned_by_opl_stage_attempt",
        "domain_receipt_parity_status": "controller_authorization_receipt_helper_active",
        "physical_delete_permitted": True,
        "physical_delete_completed": True,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
        "retirement_proof_refs": [
            "tests.test_adapter_retirement_boundary.no_turn_runner_resurrection",
            "study_runtime_execution_parts.controller_authorization_receipts",
        ],
        "focused_test_refs": [
            "tests/test_study_runtime_execution_evidence_adoption_cases/test_no_resurrection_boundary.py",
            "tests/test_adapter_retirement_boundary.py",
        ],
        "resurrection_alias_or_wrapper_allowed": False,
        "must_not_emit": list(_ACTIVE_PATH_MUST_NOT_EMIT),
    },
    {
        "residue_id": "worker_lease_residency_projection",
        "residue_class": "runtime_transport",
        "current_paths": [],
        "retired_paths": [
            "src/med_autoscience/runtime_transport/mas_runtime_core_turn_residency.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_worker_leases.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_worker_env.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_worker_wrapper.py",
        ],
        "current_role": "none_physically_retired_no_alias",
        "current_disposition": "physically_retired",
        "retirement_proof_status": "stale_surface_scan_clean",
        "stale_surface_scan_clean": True,
        "no_resurrection_guard": True,
        "opl_replacement_parity_status": "provider_liveness_owned_by_opl",
        "domain_receipt_parity_status": "owner_route_handoff_blocker_active",
        "physical_delete_permitted": True,
        "physical_delete_completed": True,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
        "retirement_proof_refs": [
            "tests.test_adapter_retirement_boundary.no_worker_residency_resurrection",
            "owner_route_reconcile.workspace_daemon.opl_provider_liveness_owner_required",
        ],
        "focused_test_refs": [
            "tests/owner_route_reconcile_cases/test_workspace_daemon_lifecycle.py",
            "tests/test_adapter_retirement_boundary.py",
        ],
        "resurrection_alias_or_wrapper_allowed": False,
        "must_not_emit": list(_ACTIVE_PATH_MUST_NOT_EMIT),
    },
    {
        "residue_id": "lifecycle_refs_sqlite_index",
        "residue_class": "sqlite_refs_index",
        "current_paths": [],
        "retired_paths": [
            "src/med_autoscience/runtime_protocol/lifecycle_refs_adapter.py",
            "src/med_autoscience/runtime_protocol/lifecycle_refs_adapter_parts/",
            "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
        ],
        "replacement_paths": [
            "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
            "src/med_autoscience/opl_domain_pack/",
        ],
        "current_role": "none_physically_retired_no_alias",
        "current_disposition": "physically_retired",
        "retirement_proof_status": "stale_surface_scan_clean",
        "stale_surface_scan_clean": True,
        "no_resurrection_guard": True,
        "opl_replacement_parity_status": "current_control_state_and_provider_attempt_ledger_owned_by_opl",
        "domain_receipt_parity_status": "domain_authority_refs_index_active",
        "physical_delete_permitted": True,
        "physical_delete_completed": True,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
        "retirement_proof_refs": [
            "domain_authority_refs_index_role.refs_only_domain_authority_index_not_generic_runtime_lifecycle_engine",
            "runtime_protocol.domain_authority_refs_index",
        ],
        "focused_test_refs": [
            "tests/test_opl_family_persistence_adapter.py",
            "tests/test_cli_cases/runtime_storage_commands.py",
            "tests/test_paper_work_unit_lifecycle_contract.py",
            "tests/test_adapter_retirement_boundary.py",
        ],
        "resurrection_alias_or_wrapper_allowed": False,
        "must_not_emit": list(_ACTIVE_PATH_MUST_NOT_EMIT),
    },
    *build_workbench_status_active_path_gates(
        delete_or_tombstone_after=_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER,
        must_not_emit=_ACTIVE_PATH_MUST_NOT_EMIT,
    ),
    {
        "residue_id": "legacy_supervisor_scheduler_tombstone",
        "residue_class": "supervisor",
        "current_paths": [
            "contracts/runtime/legacy-active-path-tombstones.json",
            "docs/history/runtime/legacy_active_path_tombstones.md",
        ],
        "current_role": "history_tombstone_provenance_only",
        "current_disposition": "tombstone_only",
        "retirement_proof_status": "tombstone_no_resurrection_guard",
        "stale_surface_scan_clean": True,
        "no_resurrection_guard": True,
        "opl_replacement_parity_status": "replacement_projection_present",
        "domain_receipt_parity_status": "not_required_for_tombstone_provenance_ref",
        "physical_delete_permitted": False,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": True,
        "delete_or_tombstone_after": [],
        "retirement_proof_refs": [
            "stale_surface_scan_clean.default_runtime_owner=opl",
            "legacy_local_scheduler_physical_retirement_proof.status=physical_retired_tombstone_provenance_only",
        ],
        "focused_test_refs": [
            "tests/test_cli_cases/domain_slo_scheduler_projection_commands.py",
            "tests/test_domain_slo_scheduler_projection.py",
        ],
        "resurrection_alias_or_wrapper_allowed": False,
        "must_not_emit": list(_ACTIVE_PATH_MUST_NOT_EMIT),
    },
)

PHYSICAL_THINNING_EVIDENCE = {
    "surface_kind": "mas_physical_thinning_evidence",
    "version": "mas-physical-thinning-evidence.v1",
    "status": "generic_runtime_residue_closed_as_boundary_evidence_physical_delete_gated",
    "body_included": False,
    "does_not_claim_physical_delete": True,
    "does_not_claim_paper_closure": True,
    "evidence_contract_ref": "contracts/evidence/mas-evidence-lane.json#/physical_thinning_evidence",
    "physical_delete_requires_all_gates": [
        "stale_surface_scan_clean",
        "opl_replacement_parity",
        "domain_receipt_parity",
        "focused_tests",
        "no_forbidden_write_proof",
        "history_tombstone_refs",
    ],
    "active_path_residue_cleanup_gates_ref": (
        "functional_consumer_boundary.active_path_residue_cleanup_gates"
    ),
    "residue_groups": [
        {
            "group_id": "runner_residue",
            "module_ids": [
                "generic_queue_attempt_retry_dead_letter",
                "generic_transition_runner",
            ],
            "closure_basis": [
                "opl_replacement_parity",
                "domain_receipt_parity",
                "no_generic_owner_claim",
            ],
            "current_role": "domain_receipt_and_transition_spec_refs_only",
            "generic_owner_claim_allowed": False,
            "physical_delete_permitted": False,
            "tombstone_or_parity_refs_required": True,
            "physical_delete_gate": "OPL parity plus focused tests; MAS keeps domain receipt refs only",
            "evidence_refs": [
                "functional_module_inventory.generic_queue_attempt_retry_dead_letter",
                "functional_module_inventory.generic_transition_runner",
                "opl_functional_harness_consumer_coverage.queue_stage_attempt_typed_closeout",
                "opl_functional_harness_consumer_coverage.generic_transition_runner",
            ],
        },
        {
            "group_id": "supervisor_residue",
            "module_ids": [
                "generic_daemon_or_scheduler_lifecycle",
                "local_launchd_scheduler_install_path",
                "legacy_scheduler_default_aliases",
                "scheduler_legacy_residue_tombstone_provenance",
            ],
            "closure_basis": [
                "no_resurrection_guard",
                "opl_replacement_parity",
                "tombstone_or_diagnostic_refs",
            ],
            "current_role": "opl_scheduler_projection_and_legacy_tombstone_only",
            "generic_owner_claim_allowed": False,
            "physical_delete_permitted": False,
            "tombstone_or_parity_refs_required": True,
            "physical_delete_gate": "stale default caller scan clean; refs are tombstone/provenance only",
            "evidence_refs": [
                "stale_surface_scan_clean.default_runtime_owner=opl",
                "legacy_local_scheduler_physical_retirement_proof.status=physical_retired_tombstone_provenance_only",
                "retired_legacy_residue_tombstones.scheduler_legacy_residue_tombstone_provenance",
            ],
        },
        {
            "group_id": "workbench_residue",
            "module_ids": [
                "workbench_portal_generic_shell",
                "owner_route_handoff_domain_ref_entry",
                "mas_generic_workbench_shell",
            ],
            "closure_basis": [
                "opl_replacement_parity",
                "domain_projection_refs_only",
                "tombstone_or_diagnostic_refs",
            ],
            "current_role": "mas_domain_projection_refs_for_opl_hosted_workbench",
            "generic_owner_claim_allowed": False,
            "physical_delete_permitted": False,
            "tombstone_or_parity_refs_required": True,
            "physical_delete_gate": "OPL default workbench caller plus no MAS generic workbench default entry",
            "evidence_refs": [
                "workbench_portal_generic_shell.proof_refs",
                (
                    "active_path_residue_cleanup_gates.owner_route_handoff_domain_ref_entry."
                    "deletion_readiness_worklist"
                ),
                "retired_legacy_residue_tombstones.mas_generic_workbench_shell",
                "opl_functional_harness_consumer_coverage.restart_dead_letter_repair_human_gate_state_chain",
            ],
        },
        {
            "group_id": "lifecycle_refs_residue",
            "module_ids": [
                "domain_authority_refs_index",
            ],
            "closure_basis": [
                "domain_authority_refs",
                "opl_current_control_state_gate",
                "domain_authority_receipt_ref_gate",
            ],
            "current_role": "refs_only_domain_authority_receipt_locator_index",
            "generic_owner_claim_allowed": False,
            "physical_delete_permitted": True,
            "runtime_lifecycle_adapter_physical_delete_completed": True,
            "tombstone_or_parity_refs_required": True,
            "physical_delete_gate": "retired runtime lifecycle path is stale-surface clean; MAS replacement is domain_authority_refs_index only",
            "evidence_refs": [
                "domain_authority_refs_index_role.refs_only_domain_authority_index_not_generic_runtime_lifecycle_engine",
                "functional_module_inventory.domain_authority_refs_index.retirement_gate",
            ],
        },
    ],
    "forbidden_claims": [
        "mas_owned_generic_runner",
        "mas_owned_generic_scheduler",
        "mas_owned_generic_workbench",
        "mas_owned_generic_persistence_engine",
        "active_path_runtime_transport_deleted_without_parity",
        "resurrection_alias_or_wrapper_for_retired_runtime_path",
        "physical_delete_claim_without_replacement_proof",
        "paper_closure_authorized_by_thinning_evidence",
    ],
}

PHYSICAL_MORPHOLOGY_LANE_D_CLOSEOUT = {
    "surface_kind": "mas_physical_morphology_lane_d_closeout",
    "lane_id": "mas_physical_thinning_closeout",
    "status": "retired_runtime_control_surfaces_plus_domain_refs_boundary",
    "delete_or_archive_authorized": False,
    "tombstone_new_active_residue_authorized": False,
    "decision": "retire_legacy_runtime_control_surfaces_no_alias",
    "required_before_delete_archive_or_tombstone": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
    "resurrection_alias_or_wrapper_allowed": False,
    "opl_owned_gap_or_domain_ref_residue_ids": [
        item["residue_id"]
        for item in ACTIVE_PATH_RESIDUE_CLEANUP_GATES
        if not item.get("stale_surface_scan_clean", False)
    ],
    "tombstone_only_residue_ids": [
        item["residue_id"]
        for item in ACTIVE_PATH_RESIDUE_CLEANUP_GATES
        if item.get("stale_surface_scan_clean", False)
    ],
    "opl_owned_gap_or_domain_ref_residue_reasons": {
        item["residue_id"]: {
            "current_role": item["current_role"],
            "current_disposition": item["current_disposition"],
            "retirement_proof_status": item.get("retirement_proof_status"),
            "stale_surface_scan_clean": item.get("stale_surface_scan_clean", False),
            "no_resurrection_guard": item.get("no_resurrection_guard", False),
            "opl_replacement_parity_status": item["opl_replacement_parity_status"],
            "domain_receipt_parity_status": item["domain_receipt_parity_status"],
            "physical_delete_permitted": item["physical_delete_permitted"],
            "archive_permitted": item["archive_permitted"],
            "rename_permitted": item["rename_permitted"],
            "tombstone_permitted": item["tombstone_permitted"],
            "focused_test_refs": list(item["focused_test_refs"]),
        }
        for item in ACTIVE_PATH_RESIDUE_CLEANUP_GATES
        if not item.get("stale_surface_scan_clean", False)
    },
}

__all__ = [
    "ACTIVE_PATH_RESIDUE_CLEANUP_GATES",
    "PHYSICAL_MORPHOLOGY_LANE_D_CLOSEOUT",
    "PHYSICAL_THINNING_EVIDENCE",
]
