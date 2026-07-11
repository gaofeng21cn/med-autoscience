from __future__ import annotations

from typing import Any

TARGET_DOMAIN_ID = "mas"
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
    "state_index_kernel",
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
        "path": "src/med_autoscience/controllers/paper_mission_owner_surface/__init__.py",
        "current_role": "owner_route_source_ref_projection",
        "long_term_owner": DOMAIN_OWNER,
        "allowed_mas_role": "domain_route_and_blocker_projection",
    },
    {
        "path": "src/med_autoscience/controllers/next_action_envelope.py",
        "current_role": "canonical_next_action_compiler",
        "long_term_owner": DOMAIN_OWNER,
        "allowed_mas_role": "domain_next_action_authority_compiler",
    },
    {
        "path": "src/med_autoscience/controllers/stage_outcome_authority/__init__.py",
        "current_role": "domain_handler_dispatch_receipt_writer",
        "long_term_owner": DOMAIN_OWNER,
        "allowed_mas_role": "domain_dispatch_receipt_adapter",
    },
    {
        "path": "src/med_autoscience/runtime_protocol/opl_state_index_source_adapter.py",
        "current_role": "body_free_state_index_source_adapter",
        "long_term_owner": OPL_OWNER,
        "allowed_mas_role": "owner_receipt_and_locator_ref_index",
    },
]

def build_opl_unique_control_plane_handoff() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_unique_control_plane_handoff",
        "version": "mas-opl-unique-control-plane-handoff.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "status": "opl_generic_runtime_owner_mas_domain_bridge_only",
        "generic_runtime_owner": OPL_OWNER,
        "domain_owner": DOMAIN_OWNER,
        "domain_intent_adapter_role": "refs_only_owner_route_typed_blocker_and_owner_receipt_handoff",
        "active_domain_allowed_actions": list(_ALLOWED_DOMAIN_ACTIONS),
        "forbidden_mas_roles": list(_FORBIDDEN_MAS_ROLES),
        "opl_replacement_surfaces": list(_OPL_REPLACEMENT_SURFACES),
        "code_path_roles": [dict(item) for item in _CODE_PATH_ROLES],
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
