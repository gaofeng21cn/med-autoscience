from __future__ import annotations

from typing import Any

from med_autoscience.controllers.domain_slo_scheduler_projection_parts.consumer_migration_inventory import (
    ACTIVE_PATH_RESIDUE_CLEANUP_GATES,
    PHYSICAL_MORPHOLOGY_LANE_D_CLOSEOUT,
)
from med_autoscience.controllers.domain_slo_scheduler_projection_parts.generated_caller_retirement import (
    build_generated_default_caller_boundary,
    build_physical_retirement_gate_matrix,
)


TARGET_DOMAIN_ID = "medautoscience"
DOMAIN_OWNER = "med-autoscience"
OPL_OWNER = "one-person-lab"
SCHEMA_VERSION = 1

_OPL_REPLACEMENT_SURFACES = [
    "provider_backed_family_runtime",
    "family_runtime_queue",
    "stage_attempt_ledger",
    "retry_dead_letter_transport",
    "generic_transition_runner",
    "worker_residency_manager",
    "runtime_lifecycle_index",
    "memory_locator_writeback_transport",
    "artifact_locator_retention_restore_shell",
    "operator_workbench_projection",
]

_FORBIDDEN_MAS_ROLES = [
    "generic_scheduler_owner",
    "generic_daemon_owner",
    "generic_queue_owner",
    "generic_attempt_ledger_owner",
    "generic_retry_dead_letter_owner",
    "generic_state_machine_runner_owner",
    "generic_worker_residency_owner",
    "generic_persistence_engine_owner",
    "generic_lifecycle_engine_owner",
    "generic_workbench_owner",
]

_ALLOWED_DOMAIN_ACTIONS = [
    "owner_route_decision",
    "domain_receipt",
    "typed_blocker",
    "guarded_apply_authorization",
    "stage_closeout_domain_semantics",
    "publication_gate_verdict",
    "artifact_mutation_authorization",
    "read_only_projection",
    "standalone_diagnostic",
]

_CODE_PATH_ROLES = [
    {
        "path": "src/med_autoscience/runtime_transport/mas_runtime_core.py",
        "current_role": "domain_direct_runtime_bridge_and_standalone_diagnostic",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "domain_owner_receipt_adapter",
    },
    {
        "path": "src/med_autoscience/runtime_transport/mas_runtime_core_turn_runner.py",
        "current_role": "stage_turn_closeout_receipt_adapter",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "stage_closeout_domain_semantics",
    },
    {
        "path": "src/med_autoscience/runtime_transport/mas_runtime_core_worker_leases.py",
        "current_role": "worker_lease_receipt_projection",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "domain_worker_receipt_ref_adapter",
    },
    {
        "path": "src/med_autoscience/controllers/domain_route_scan.py",
        "current_role": "owner_route_source_ref_projection",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "domain_route_and_blocker_projection",
    },
    {
        "path": "src/med_autoscience/controllers/domain_action_request_materializer.py",
        "current_role": "domain_guard_and_owner_receipt_consumer",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "no_forbidden_write_guard_and_receipt_signer",
    },
    {
        "path": "src/med_autoscience/controllers/domain_owner_action_dispatch.py",
        "current_role": "sidecar_domain_dispatch_receipt_writer",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "domain_dispatch_receipt_adapter",
    },
    {
        "path": "src/med_autoscience/controllers/domain_route_reconcile.py",
        "current_role": "domain_safe_reconcile_guard",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "guarded_apply_or_typed_blocker",
    },
    {
        "path": "src/med_autoscience/runtime_protocol/runtime_lifecycle_store.py",
        "current_role": "refs_only_sqlite_sidecar_index",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "owner_receipt_and_locator_ref_index",
    },
]


def build_runtime_transport_handoff_projection() -> dict[str, Any]:
    return {
        "surface_kind": "mas_runtime_transport_handoff_projection",
        "version": "mas-runtime-transport-handoff.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": "opl_generic_runtime_owner_mas_domain_bridge_only",
        "generic_runtime_owner": OPL_OWNER,
        "domain_owner": DOMAIN_OWNER,
        "mas_runtime_core_role": "domain_owner_receipt_adapter_or_standalone_diagnostic",
        "active_domain_allowed_actions": list(_ALLOWED_DOMAIN_ACTIONS),
        "forbidden_mas_roles": list(_FORBIDDEN_MAS_ROLES),
        "opl_replacement_surfaces": list(_OPL_REPLACEMENT_SURFACES),
        "code_path_roles": [dict(item) for item in _CODE_PATH_ROLES],
        "generated_default_caller_boundary": build_generated_default_caller_boundary(
            schema_version=SCHEMA_VERSION,
            replacement_owner=OPL_OWNER,
        ),
        "default_caller_policy": {
            "default_online_runtime_owner": OPL_OWNER,
            "default_provider": "Temporal",
            "mas_default_scheduler_allowed": False,
            "mas_default_queue_allowed": False,
            "mas_default_attempt_ledger_allowed": False,
            "mas_default_worker_residency_allowed": False,
            "mas_default_transition_runner_allowed": False,
            "mas_default_persistence_engine_allowed": False,
            "mas_runtime_transport_active_as_generic_provider": False,
        },
        "physical_retirement_gate_matrix": build_physical_retirement_gate_matrix(
            schema_version=SCHEMA_VERSION,
            replacement_owner=OPL_OWNER,
        ),
        "physical_cleanup_gate": {
            "delete_or_archive_when_no_domain_direct_or_diagnostic_caller": True,
            "requires_opl_replacement_parity": True,
            "requires_no_active_default_caller_proof": True,
            "requires_domain_receipt_parity": True,
            "history_tombstone_required": True,
            "no_alias_facade_compat_wrapper_allowed": True,
            "active_path_residue_cleanup_gates": [
                {
                    key: list(value) if isinstance(value, list) else value
                    for key, value in item.items()
                }
                for item in ACTIVE_PATH_RESIDUE_CLEANUP_GATES
            ],
            "lane_d_closeout": {
                key: list(value) if isinstance(value, list) else value
                for key, value in PHYSICAL_MORPHOLOGY_LANE_D_CLOSEOUT.items()
            },
        },
        "authority_boundary": {
            "opl_owns_runtime_transport": True,
            "opl_writes_domain_truth": False,
            "opl_authorizes_publication_quality": False,
            "opl_writes_artifact_body": False,
            "mas_owns_generic_runtime": False,
            "mas_retains_domain_receipt_authority": True,
            "mas_retains_publication_and_artifact_authority": True,
        },
    }


__all__ = ["build_runtime_transport_handoff_projection"]
