from __future__ import annotations

from med_autoscience.controllers.domain_slo_scheduler_projection_parts.active_path_workbench_status_gates import (
    build_workbench_status_active_path_gates,
)

_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER = (
    "active_caller_count=0",
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
        "current_paths": [
            "src/med_autoscience/runtime_transport/mas_runtime_core.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_pause_resume.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_stopped_relaunch.py",
        ],
        "current_role": "domain_owner_receipt_adapter_or_standalone_diagnostic",
        "current_disposition": "retain_with_explicit_cleanup_gate",
        "active_caller_status": "active_domain_or_diagnostic_caller_present",
        "active_caller_count": 2,
        "no_active_caller_proven": False,
        "opl_replacement_parity_status": "projected_not_sufficient_for_physical_delete",
        "domain_receipt_parity_status": "pending_real_paper_line_receipt_parity",
        "physical_delete_permitted": False,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
        "active_caller_proof_refs": [
            "functional_module_inventory.generic_queue_attempt_retry_dead_letter.active_callers",
            "runtime_transport_handoff_projection.code_path_roles.mas_runtime_core",
        ],
        "focused_test_refs": [
            "tests/test_runtime_transport_mas_runtime_core.py",
            "tests/test_study_runtime_transport.py",
        ],
        "no_alias_facade_compat_wrapper_allowed": True,
        "must_not_emit": list(_ACTIVE_PATH_MUST_NOT_EMIT),
    },
    {
        "residue_id": "runtime_turn_runner_closeout_adapter",
        "residue_class": "runtime_transport",
        "current_paths": [
            "src/med_autoscience/runtime_transport/mas_runtime_core_turn_runner.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_turn_completion.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_turn_receipts.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_turn_messages.py",
        ],
        "current_role": "stage_turn_closeout_and_owner_receipt_adapter",
        "current_disposition": "retain_with_explicit_cleanup_gate",
        "active_caller_status": "active_stage_closeout_receipt_caller_present",
        "active_caller_count": 2,
        "no_active_caller_proven": False,
        "opl_replacement_parity_status": "queue_attempt_transport_projected_not_physical_delete_ready",
        "domain_receipt_parity_status": "pending_stage_closeout_receipt_parity",
        "physical_delete_permitted": False,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
        "active_caller_proof_refs": [
            "runtime_transport_handoff_projection.code_path_roles.turn_runner",
            "opl_functional_harness_consumer_coverage.queue_stage_attempt_typed_closeout",
        ],
        "focused_test_refs": [
            "tests/test_runtime_transport_mas_runtime_core.py",
            "tests/test_study_runtime_transport.py",
        ],
        "no_alias_facade_compat_wrapper_allowed": True,
        "must_not_emit": list(_ACTIVE_PATH_MUST_NOT_EMIT),
    },
    {
        "residue_id": "worker_lease_residency_projection",
        "residue_class": "runtime_transport",
        "current_paths": [
            "src/med_autoscience/runtime_transport/mas_runtime_core_worker_leases.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_worker_env.py",
            "src/med_autoscience/runtime_transport/mas_runtime_core_worker_wrapper.py",
        ],
        "current_role": "worker_lease_receipt_ref_projection_not_residency_owner",
        "current_disposition": "retain_with_explicit_cleanup_gate",
        "active_caller_status": "active_runtime_worker_diagnostic_caller_present",
        "active_caller_count": 2,
        "no_active_caller_proven": False,
        "opl_replacement_parity_status": "worker_residency_manager_projected_not_physical_delete_ready",
        "domain_receipt_parity_status": "pending_worker_receipt_ref_parity",
        "physical_delete_permitted": False,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
        "active_caller_proof_refs": [
            "runtime_transport_handoff_projection.code_path_roles.worker_lease",
            "functional_module_inventory.generic_queue_attempt_retry_dead_letter.active_callers",
        ],
        "focused_test_refs": [
            "tests/test_runtime_transport_mas_runtime_core.py",
            "tests/test_runtime_transport_mas_runtime_core_stopped_relaunch.py",
        ],
        "no_alias_facade_compat_wrapper_allowed": True,
        "must_not_emit": list(_ACTIVE_PATH_MUST_NOT_EMIT),
    },
    {
        "residue_id": "lifecycle_refs_sqlite_index",
        "residue_class": "sqlite_refs_index",
        "current_paths": [
            "src/med_autoscience/runtime_protocol/lifecycle_refs_adapter.py",
            "src/med_autoscience/runtime_protocol/lifecycle_refs_adapter_parts/",
            "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
        ],
        "current_role": "refs_only_domain_receipt_locator_and_lifecycle_ref_index",
        "current_disposition": "retain_with_explicit_cleanup_gate",
        "active_caller_status": "active_domain_lifecycle_ref_caller_present",
        "active_caller_count": 3,
        "no_active_caller_proven": False,
        "opl_replacement_parity_status": "lifecycle_index_projected_not_physical_delete_ready",
        "domain_receipt_parity_status": "pending_owner_receipt_ref_parity",
        "physical_delete_permitted": False,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": False,
        "delete_or_tombstone_after": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
        "active_caller_proof_refs": [
            "refs_only_adapter_retirement_gates.lifecycle_refs_adapter",
            "lifecycle_refs_adapter_role.refs_only_index_not_generic_persistence_engine",
        ],
        "focused_test_refs": [
            "tests/test_lifecycle_refs_adapter.py",
            "tests/test_runtime_lifecycle_read_model.py",
            "tests/test_runtime_lifecycle_contract.py",
        ],
        "no_alias_facade_compat_wrapper_allowed": True,
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
        "active_caller_status": "no_active_default_caller_proven",
        "active_caller_count": 0,
        "no_active_caller_proven": True,
        "opl_replacement_parity_status": "replacement_projection_present",
        "domain_receipt_parity_status": "not_required_for_tombstone_provenance_ref",
        "physical_delete_permitted": False,
        "archive_permitted": False,
        "rename_permitted": False,
        "tombstone_permitted": True,
        "delete_or_tombstone_after": [],
        "active_caller_proof_refs": [
            "no_active_caller_proof.default_caller_count=0",
            "legacy_local_scheduler_physical_retirement_proof.status=physical_retired_tombstone_provenance_only",
        ],
        "focused_test_refs": [
            "tests/test_cli_cases/domain_slo_scheduler_projection_commands.py",
            "tests/test_domain_slo_scheduler_projection.py",
        ],
        "no_alias_facade_compat_wrapper_allowed": True,
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
        "no_active_caller_proof",
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
            "current_role": "domain_receipt_adapter_and_transition_spec_only",
            "generic_owner_claim_allowed": False,
            "physical_delete_permitted": False,
            "tombstone_or_parity_refs_required": True,
            "physical_delete_gate": "active_domain_or_diagnostic_caller_count=0 plus OPL parity plus focused tests",
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
                "scheduler_legacy_residue_without_active_caller",
            ],
            "closure_basis": [
                "no_active_default_caller",
                "opl_replacement_parity",
                "tombstone_or_diagnostic_refs",
            ],
            "current_role": "opl_scheduler_projection_and_legacy_tombstone_only",
            "generic_owner_claim_allowed": False,
            "physical_delete_permitted": False,
            "tombstone_or_parity_refs_required": True,
            "physical_delete_gate": "no active default caller already proven; retained refs are tombstone/provenance only",
            "evidence_refs": [
                "no_active_caller_proof.default_caller_count=0",
                "legacy_local_scheduler_physical_retirement_proof.status=physical_retired_tombstone_provenance_only",
                "retired_legacy_residue_tombstones.scheduler_legacy_residue_without_active_caller",
            ],
        },
        {
            "group_id": "workbench_residue",
            "module_ids": [
                "workbench_portal_generic_shell",
                "owner_route_handoff_adapter",
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
                    "active_path_residue_cleanup_gates.owner_route_handoff_adapter."
                    "deletion_readiness_worklist"
                ),
                "retired_legacy_residue_tombstones.mas_generic_workbench_shell",
                "opl_functional_harness_consumer_coverage.restart_dead_letter_repair_human_gate_state_chain",
            ],
        },
        {
            "group_id": "lifecycle_refs_residue",
            "module_ids": [
                "lifecycle_refs_adapter",
            ],
            "closure_basis": [
                "refs_only_adapter",
                "opl_lifecycle_index_parity_gate",
                "domain_receipt_parity_gate",
            ],
            "current_role": "refs_only_domain_receipt_locator_and_lifecycle_ref_index",
            "generic_owner_claim_allowed": False,
            "physical_delete_permitted": False,
            "tombstone_or_parity_refs_required": True,
            "physical_delete_gate": "active_caller_count=0 plus OPL lifecycle index parity plus domain owner receipt ref parity",
            "evidence_refs": [
                "lifecycle_refs_adapter_role.refs_only_index_not_generic_persistence_engine",
                "refs_only_adapter_retirement_gates.lifecycle_refs_adapter",
                "functional_module_inventory.lifecycle_refs_adapter.retirement_gate",
            ],
        },
    ],
    "forbidden_claims": [
        "mas_owned_generic_runner",
        "mas_owned_generic_scheduler",
        "mas_owned_generic_workbench",
        "mas_owned_generic_persistence_engine",
        "active_path_runtime_transport_deleted_without_parity",
        "compat_alias_or_facade_retained_for_retired_runtime_path",
        "physical_delete_already_completed",
        "paper_closure_authorized_by_thinning_evidence",
    ],
}

PHYSICAL_MORPHOLOGY_LANE_D_CLOSEOUT = {
    "surface_kind": "mas_physical_morphology_lane_d_closeout",
    "lane_id": "mas_physical_thinning_closeout",
    "status": "gated_retained_refs_only_or_diagnostic_residue",
    "delete_or_archive_authorized": False,
    "tombstone_new_active_residue_authorized": False,
    "decision": "retain_with_explicit_cleanup_gate",
    "required_before_delete_archive_or_tombstone": list(_ACTIVE_PATH_DELETE_OR_TOMBSTONE_AFTER),
    "no_alias_facade_compat_wrapper_allowed": True,
    "retained_residue_ids": [
        item["residue_id"]
        for item in ACTIVE_PATH_RESIDUE_CLEANUP_GATES
        if not item["no_active_caller_proven"]
    ],
    "tombstone_only_residue_ids": [
        item["residue_id"]
        for item in ACTIVE_PATH_RESIDUE_CLEANUP_GATES
        if item["no_active_caller_proven"]
    ],
    "retained_residue_reasons": {
        item["residue_id"]: {
            "current_role": item["current_role"],
            "current_disposition": item["current_disposition"],
            "active_caller_status": item["active_caller_status"],
            "active_caller_count": item["active_caller_count"],
            "opl_replacement_parity_status": item["opl_replacement_parity_status"],
            "domain_receipt_parity_status": item["domain_receipt_parity_status"],
            "physical_delete_permitted": item["physical_delete_permitted"],
            "archive_permitted": item["archive_permitted"],
            "rename_permitted": item["rename_permitted"],
            "tombstone_permitted": item["tombstone_permitted"],
            "focused_test_refs": list(item["focused_test_refs"]),
        }
        for item in ACTIVE_PATH_RESIDUE_CLEANUP_GATES
        if not item["no_active_caller_proven"]
    },
}

__all__ = [
    "ACTIVE_PATH_RESIDUE_CLEANUP_GATES",
    "PHYSICAL_MORPHOLOGY_LANE_D_CLOSEOUT",
    "PHYSICAL_THINNING_EVIDENCE",
]
