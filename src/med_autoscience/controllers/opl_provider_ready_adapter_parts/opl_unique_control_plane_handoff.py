from __future__ import annotations

from typing import Any

from med_autoscience.controllers.opl_unique_control_plane_boundary_parts.generated_caller_retirement import (
    build_generated_default_caller_boundary,
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
    "domain_authority_refs_index",
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
        "path": "OPL current_control_state provider/stage runtime",
        "current_role": "fail_closed_domain_intent_handoff_adapter",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "domain_intent_refs_and_typed_blocker_adapter",
    },
    {
        "path": "src/med_autoscience/controllers/owner_route_reconcile.py",
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
        "path": "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
        "current_role": "refs_only_domain_authority_refs_index",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "owner_receipt_and_locator_ref_index",
    },
]

_STANDARD_AGENT_PURITY = {
    "surface_kind": "mas_standard_opl_agent_purity",
    "schema_version": SCHEMA_VERSION,
    "status": "standard_agent_purity_cutover_pending",
    "agent_shape": "declarative_medical_pack_minimal_authority_functions_refs_only_projection",
    "default_runtime_owner": OPL_OWNER,
    "generated_surface_owner": OPL_OWNER,
    "domain_owner": DOMAIN_OWNER,
    "active_generic_owner_claim_allowed": False,
    "source_purity_cutover_status": "physical_wrapper_retirement_pending",
    "repo_local_wrapper_tail_count": 3,
    "repo_local_wrapper_tail_module_ids": [
        "generic_cli_mcp_product_wrappers",
        "owner_route_reconcile_materialize_dispatch_shell",
        "workbench_portal_generic_shell",
    ],
    "default_caller_count": 0,
    "runtime_package_residue_count": 0,
    "retired_alias_residue_refs": [],
    "mas_repo_runtime_role": "domain_authority_target_only",
    "mas_retained_surface_classes": [
        "declarative_medical_pack",
        "minimal_authority_functions",
        "domain_authority_refs",
    ],
    "domain_projection_policy": "refs_receipts_blockers_only_no_body_verdict_or_blob",
    "history_policy": {
        "default_read_model_exposes_history_details": False,
        "history_detail_owner": "docs/history and explicit runtime tombstone contracts",
    },
    "forbidden_active_claims": [
        "mas_generic_runtime_owner",
        "mas_generic_scheduler_owner",
        "mas_generic_queue_owner",
        "mas_generic_attempt_ledger_owner",
        "mas_generic_worker_residency_owner",
        "mas_generic_persistence_engine_owner",
        "mas_generic_lifecycle_engine_owner",
        "mas_generic_workbench_owner",
        "compatibility_alias_for_retired_runtime",
        "provider_completion_is_domain_completion",
    ],
}


def build_opl_unique_control_plane_handoff() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_unique_control_plane_handoff",
        "version": "mas-opl-unique-control-plane-handoff.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": "opl_generic_runtime_owner_mas_domain_bridge_only",
        "generic_runtime_owner": OPL_OWNER,
        "domain_owner": DOMAIN_OWNER,
        "domain_intent_adapter_role": "refs_only_owner_route_typed_blocker_and_owner_receipt_handoff",
        "standard_agent_purity": dict(_STANDARD_AGENT_PURITY),
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
            "default_provider": "temporal",
            "opl_temporal_hosted_autonomy_enabled_by_default": True,
            "persistent_online_control_plane": "opl_temporal",
            "task_start_handoff": "mas_domain_intent_to_opl_stage_attempt",
            "wakeup_retry_resume_owner": OPL_OWNER,
            "codex_app_outer_driver_required": False,
            "mas_default_scheduler_allowed": False,
            "mas_default_daemon_allowed": False,
            "mas_default_queue_allowed": False,
            "mas_default_attempt_ledger_allowed": False,
            "mas_default_attempt_loop_allowed": False,
            "mas_default_worker_residency_allowed": False,
            "mas_default_transition_runner_allowed": False,
            "mas_default_persistence_engine_allowed": False,
            "mas_runtime_transport_active_as_generic_provider": False,
            "mas_runtime_transport_active_contract_surface": False,
            "mas_runtime_transport_package_absent": True,
        },
        "authority_boundary": {
            "opl_owns_runtime_transport": True,
            "opl_owns_unique_control_plane": True,
            "opl_writes_domain_truth": False,
            "opl_authorizes_publication_quality": False,
            "opl_writes_artifact_body": False,
            "mas_owns_generic_runtime": False,
            "mas_retains_domain_receipt_authority": True,
            "mas_retains_publication_and_artifact_authority": True,
        },
    }


__all__ = ["build_opl_unique_control_plane_handoff"]
