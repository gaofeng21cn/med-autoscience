from __future__ import annotations

from typing import Any


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_supervision_scheduler_consumer_migration"
ACTIVE_PATH_ROLE = "opl_replacement_default"
LOCAL_DIAGNOSTIC_PATH_ROLE = "standalone_local_diagnostic_migration_bridge"
CURRENT_SCHEDULER_OWNER = "opl_provider_runtime_manager"
LEGACY_SCHEDULER_OWNER = "mas_supervision_scheduler"
REPLACEMENT_OWNER = "one-person-lab"
REPLACEMENT_OWNER_SURFACE = "opl_provider_runtime_manager"
REPLACEMENT_STATE = "opl_replacement_contract_active"
RETIREMENT_STATE = "local_legacy_retirement_pending_no_active_caller_proof"

MAS_RETAINED_AFTER_MIGRATION = (
    "paper_progress_slo_semantics",
    "mas_owner_receipt",
    "typed_blocker",
    "safe_action_refs",
    "quality_source_refs",
    "no_forbidden_write_evidence",
)
OPL_REPLACEMENT_EXPECTED_CAPABILITIES = (
    "scheduler_lifecycle",
    "cadence_slo",
    "job_registry_latest_run_projection",
    "provider_slo",
    "wakeup_transport",
    "attempt_queue_retry_dead_letter",
    "operator_projection",
)
RETIREMENT_PROOF_REQUIRED = (
    "opl_replacement_contract_available",
    "replacement_proof",
    "no_active_caller_proof",
    "no_forbidden_write",
    "focused_cli_status_tests",
    "git_diff_check",
)
FORBIDDEN_AUTHORITY_CLAIMS = (
    "provider_completion_is_paper_closure",
    "scheduler_status_is_publication_ready",
    "scheduler_status_authorizes_artifact_mutation",
    "stable_blocker_is_paper_closure",
)
FORBIDDEN_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "paper/current_package",
    "manuscript/current_package",
    "paper/submission_minimal",
    "manuscript/submission_minimal",
    "runtime_lifecycle.sqlite",
)
OPL_CONSUMED_GENERIC_SURFACES = (
    "generic_scheduler",
    "generic_daemon",
    "generic_queue",
    "generic_attempt_ledger",
    "generic_runner",
    "generic_transition_runner",
    "generic_workbench",
    "generic_memory_locator",
    "generic_artifact_lifecycle",
    "generic_observability",
)
MAS_RETAINED_THIN_PROGRAM_SURFACES = (
    "study_truth",
    "publication_quality_verdict",
    "artifact_authority",
    "publication_route_memory_body",
    "memory_writeback_decision",
    "domain_transition_table",
    "owner_receipt",
    "typed_blocker",
    "safe_action_refs",
)


def build_functional_consumer_boundary() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_functional_consumer_boundary",
        "status": "opl_consumes_generic_surfaces_mas_retains_domain_authority_pack",
        "consumer_role": "domain_authority_pack_thin_program_surface",
        "generic_surface_owner": REPLACEMENT_OWNER,
        "generic_surfaces_consumed_from_opl": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_does_not_own": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_retains": list(MAS_RETAINED_THIN_PROGRAM_SURFACES),
        "no_active_caller_required": True,
        "no_active_caller_scope": [
            "cli_default",
            "mcp_default",
            "product_entry_default",
            "sidecar_default",
            "test_lane_default",
        ],
        "proof_surfaces": [
            "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough",
            "runtime-supervision-status default manager=opl",
            "product_entry_manifest.functional_consumer_boundary",
            "sidecar_export.functional_consumer_boundary",
            "legacy_residue_audit.summary.default_caller_count",
        ],
        "forbidden_regressions": [
            "mas_default_generic_scheduler",
            "mas_resident_generic_daemon",
            "mas_owned_generic_queue",
            "mas_owned_attempt_ledger",
            "mas_generic_transition_runner",
            "mas_generic_workbench_shell",
        ],
    }


def build_consumer_migration_contract(
    *,
    adapter_id: str | None = None,
    manager: str | None = None,
) -> dict[str, Any]:
    manager_key = str(manager or "").strip().lower()
    replacement_active = manager_key in {"opl", "opl_provider_runtime_manager"} or adapter_id == "opl_family_runtime_provider"
    active_path_role = ACTIVE_PATH_ROLE if replacement_active else LOCAL_DIAGNOSTIC_PATH_ROLE
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "state": REPLACEMENT_STATE,
        "active_path_role": active_path_role,
        "current_scheduler_owner": CURRENT_SCHEDULER_OWNER if replacement_active else LEGACY_SCHEDULER_OWNER,
        "legacy_scheduler_owner": LEGACY_SCHEDULER_OWNER,
        "local_diagnostic_path_role": LOCAL_DIAGNOSTIC_PATH_ROLE,
        "current_surface_allowed_until_replacement": not replacement_active,
        "replacement_required_before_retirement": not replacement_active,
        "retirement_state": RETIREMENT_STATE,
        "replacement_owner": REPLACEMENT_OWNER,
        "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
        "replacement_contract_expected": {
            "owner": REPLACEMENT_OWNER,
            "surface": REPLACEMENT_OWNER_SURFACE,
            "required_capabilities": list(OPL_REPLACEMENT_EXPECTED_CAPABILITIES),
            "must_not_write_mas_domain_truth": True,
            "status": "active" if replacement_active else "required_before_retirement",
        },
        "functional_consumer_boundary": build_functional_consumer_boundary(),
        "mas_retained_after_migration": list(MAS_RETAINED_AFTER_MIGRATION),
        "retirement_proof_required": list(RETIREMENT_PROOF_REQUIRED),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "adapter_id": adapter_id,
        "manager": manager,
    }


def attach_consumer_migration_contract(
    payload: dict[str, Any],
    *,
    adapter_id: str | None = None,
    manager: str | None = None,
) -> dict[str, Any]:
    result = dict(payload)
    contract = build_consumer_migration_contract(adapter_id=adapter_id, manager=manager)
    result["active_path_role"] = contract["active_path_role"]
    result["consumer_migration"] = contract
    result["replacement_owner"] = REPLACEMENT_OWNER
    result["retirement_state"] = RETIREMENT_STATE
    return result


__all__ = [
    "ACTIVE_PATH_ROLE",
    "CURRENT_SCHEDULER_OWNER",
    "FORBIDDEN_AUTHORITY_CLAIMS",
    "FORBIDDEN_WRITES",
    "MAS_RETAINED_AFTER_MIGRATION",
    "MAS_RETAINED_THIN_PROGRAM_SURFACES",
    "OPL_CONSUMED_GENERIC_SURFACES",
    "OPL_REPLACEMENT_EXPECTED_CAPABILITIES",
    "REPLACEMENT_OWNER",
    "REPLACEMENT_OWNER_SURFACE",
    "REPLACEMENT_STATE",
    "RETIREMENT_PROOF_REQUIRED",
    "RETIREMENT_STATE",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "LEGACY_SCHEDULER_OWNER",
    "LOCAL_DIAGNOSTIC_PATH_ROLE",
    "attach_consumer_migration_contract",
    "build_functional_consumer_boundary",
    "build_consumer_migration_contract",
]
