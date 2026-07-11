from __future__ import annotations

from typing import Any


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_runtime_control_retirement_consumer_projection"
ACTIVE_PATH_ROLE = "opl_replacement_default"
LOCAL_TOMBSTONE_PATH_ROLE = "history_tombstone_provenance_only"
OPTIONAL_ADAPTER_PATH_ROLE = "history_tombstone_provenance_only"
CURRENT_SCHEDULER_OWNER = "opl_provider_runtime_manager"
LEGACY_SCHEDULER_OWNER = "retired_provenance_only"
REPLACEMENT_OWNER = "one-person-lab"
REPLACEMENT_OWNER_SURFACE = "opl_provider_runtime_manager"
REPLACEMENT_STATE = "opl_replacement_contract_active"
RETIREMENT_STATE = "retired_runtime_tombstone_requires_opl_contract_readback"
LOCAL_TOMBSTONE_RETIREMENT_STATE = "local_legacy_history_tombstone_provenance_only"

MAS_DOMAIN_AUTHORITY_AFTER_MIGRATION = (
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
    "functional_privatization_audit_readback",
    "no_forbidden_write",
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


def build_consumer_migration_contract(
    *,
    adapter_id: str | None = None,
    manager: str | None = None,
) -> dict[str, Any]:
    manager_key = str(manager or "").strip().lower()
    replacement_active = (
        manager_key in {"opl", "opl_provider_runtime_manager"}
        or adapter_id == "opl_family_runtime_provider"
    )
    legacy_runtime_surface = bool(manager_key or adapter_id) and not replacement_active
    active_path_role = (
        ACTIVE_PATH_ROLE
        if replacement_active
        else LOCAL_TOMBSTONE_PATH_ROLE
        if legacy_runtime_surface
        else OPTIONAL_ADAPTER_PATH_ROLE
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "state": REPLACEMENT_STATE,
        "active_path_role": active_path_role,
        "current_scheduler_owner": (
            CURRENT_SCHEDULER_OWNER if replacement_active else LEGACY_SCHEDULER_OWNER
        ),
        "legacy_scheduler_owner": LEGACY_SCHEDULER_OWNER,
        "current_surface_allowed_until_replacement": False,
        "replacement_required_before_retirement": not replacement_active,
        "forbidden_operations": [
            "status",
            "remove_legacy_jobs",
            "ensure",
            "create",
            "edit",
            "resume",
            "trigger_run",
            "write_tick_script",
        ],
        "retirement_state": (
            LOCAL_TOMBSTONE_RETIREMENT_STATE if legacy_runtime_surface else RETIREMENT_STATE
        ),
        "replacement_owner": REPLACEMENT_OWNER,
        "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
        "replacement_contract_expected": {
            "owner": REPLACEMENT_OWNER,
            "surface": REPLACEMENT_OWNER_SURFACE,
            "required_capabilities": list(OPL_REPLACEMENT_EXPECTED_CAPABILITIES),
            "must_not_write_mas_domain_truth": True,
            "status": (
                "active"
                if replacement_active
                else "history_tombstone_provenance_only"
                if legacy_runtime_surface
                else "required_before_retirement"
            ),
        },
        "functional_privatization_audit_ref": "contracts/functional_privatization_audit.json",
        "mas_domain_authority_after_migration": list(MAS_DOMAIN_AUTHORITY_AFTER_MIGRATION),
        "retirement_proof_required": list(RETIREMENT_PROOF_REQUIRED),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "adapter_id": adapter_id,
        "manager": manager,
    }


__all__ = [
    "ACTIVE_PATH_ROLE",
    "CURRENT_SCHEDULER_OWNER",
    "FORBIDDEN_AUTHORITY_CLAIMS",
    "FORBIDDEN_WRITES",
    "LEGACY_SCHEDULER_OWNER",
    "LOCAL_TOMBSTONE_PATH_ROLE",
    "OPTIONAL_ADAPTER_PATH_ROLE",
    "REPLACEMENT_OWNER",
    "REPLACEMENT_OWNER_SURFACE",
    "REPLACEMENT_STATE",
    "RETIREMENT_STATE",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_consumer_migration_contract",
]
