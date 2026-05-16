from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CONTRACT_VERSION = 1
SCHEMA_VERSION = 1
SURFACE_KIND = "runtime_lifecycle_sqlite_index"
DEFAULT_DB_FILENAME = "runtime_lifecycle.sqlite"

SQLITE_GITIGNORE_PATTERNS = (
    "*.sqlite",
    "*.sqlite-wal",
    "*.sqlite-shm",
    "*.db-wal",
    "*.db-shm",
)

WORKSPACE_CLASSIFICATIONS = (
    "live_active",
    "parked_controller_stop",
    "stopped_cold",
    "pinned_or_unknown_owner",
    "archived_workspace",
)

MIGRATION_RUN_MODES = (
    "inventory",
    "dry_run",
    "apply",
    "verify",
    "export",
    "rollback_plan",
)

COMPATIBILITY_READER_NAMES = (
    "study_progress",
    "runtime_watch_latest",
    "storage_audit_status",
    "cli_product_entry",
    "mcp_product_entry",
    "package_locator",
    "legacy_report_reader",
)

FILE_AUTHORITY_SURFACES = (
    "runtime_binding.yaml",
    ".ds/runtime_state.json",
    "study_runtime_status",
    "runtime_watch/latest.json",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "runtime_escalation_record.json",
    "study_macro_state/latest.json",
    "runtime_supervisor_owner_route",
    "runtime_supervisor_dispatch_receipt",
    "paper_work_unit_outbox_receipt",
    "surface_refs",
    "dataset_manifest",
    "restore_index",
    "paper",
    "manuscript/current_package",
    "current_package.zip",
)

SQLITE_SIDECAR_TABLES = (
    "schema_migrations",
    "runtime_objects",
    "lineage_nodes",
    "lineage_edges",
    "workspace_allocations",
    "runtime_snapshots",
    "snapshot_file_refs",
    "revision_diffs",
    "canvas_projection",
    "runtime_events",
    "run_summaries",
    "bash_exec_sessions",
    "codex_sessions",
    "report_index",
    "storage_audit_runs",
    "retention_actions",
    "archive_refs",
    "study_macro_state_snapshots",
    "owner_route_receipts",
    "dispatch_receipts",
    "turn_receipts",
    "paper_work_unit_receipts",
    "surface_refs",
    "compatibility_exports",
    "migration_runs",
)

SIDECAR_INDEXED_SURFACES = (
    "study_macro_state_snapshot",
    "owner_route_receipt",
    "dispatch_receipt",
    "turn_receipt",
    "paper_work_unit_receipt",
    "surface_ref",
    "lineage_node",
    "lineage_edge",
    "workspace_allocation",
    "runtime_snapshot",
    "snapshot_file_ref",
    "revision_diff",
    "canvas_projection",
)

SIDECAR_AUTHORITY_POLICY = "index_only_authority_remains_file_surfaces"
SIDECAR_ROLE = "mas_domain_sidecar_index_reference_adapter"
GENERIC_PERSISTENCE_OWNER = "one-person-lab"
GENERIC_PERSISTENCE_ENGINE_CLAIM_ALLOWED = False

SQLITE_AUTHORITY_SCOPE = (
    "runtime_lifecycle",
    "runtime_index",
    "runtime_receipt",
    "runtime_retention",
    "runtime_cursor",
)

SQLITE_FORBIDDEN_AUTHORITY_SURFACES = (
    "study_authority",
    "paper_authority",
    "publication_authority",
    "artifact_authority",
    "file_authority",
)

QUEST_LIVE_WRITER_ROOT_POLICY = "workspace_runtime_quests"
QUEST_ALLOWED_LIVE_WRITER_ROOTS = ("runtime/quests",)
QUEST_LEGACY_IMPORT_RESTORE_SOURCES = (
    "quest-local .git",
    ".ds/worktrees",
    "ops/med-deepscientist runtime Git era",
)
QUEST_FORBIDDEN_DAILY_LIFECYCLE_SURFACES = QUEST_LEGACY_IMPORT_RESTORE_SOURCES

GIT_ERA_REPLACEMENT_SURFACES = {
    "quest_lineage": ["lineage_nodes", "lineage_edges"],
    "workspace_checkout_allocation": ["workspace_allocations"],
    "quest_runtime_snapshot": ["runtime_snapshots", "snapshot_file_refs"],
    "revision_comparison": ["revision_diffs"],
    "canvas_projection_index": ["canvas_projection"],
}

Q1_Q6_CUTOVER_CONTRACT = (
    {
        "quarter": "Q1",
        "status": "shared_sqlite_foundation",
        "required_tables": [
            "lineage_nodes",
            "lineage_edges",
            "workspace_allocations",
            "runtime_snapshots",
            "snapshot_file_refs",
            "revision_diffs",
            "canvas_projection",
        ],
        "git_era_surfaces_replaced": [
            "quest-local .git lineage",
            "workspace checkout allocation records",
            "runtime snapshot file manifest indexes",
        ],
    },
    {
        "quarter": "Q2",
        "status": "dual_write_read_parity",
        "required_proof": "sqlite_indexes_match_legacy_git_readers_before_reader_cutover",
    },
    {
        "quarter": "Q3",
        "status": "reader_cutover",
        "required_proof": "runtime_readers_use_sqlite_lifecycle_indexes_for_lineage_and_snapshots",
    },
    {
        "quarter": "Q4",
        "status": "legacy_git_import_freeze",
        "required_proof": "legacy_git_inputs_are_restore_or_audit_sources_only",
    },
    {
        "quarter": "Q5",
        "status": "controlled_retirement",
        "required_proof": "quest_git_daily_lifecycle_paths_are_absent_from_live_writer_roots",
    },
    {
        "quarter": "Q6",
        "status": "post_cutover_verification",
        "required_proof": "sqlite_lifecycle_store_remains_index_only_and_file_truth_surfaces_remain_authoritative",
    },
)

OPL_FAMILY_ADAPTER_SOURCE_TABLES = (
    "lineage_nodes",
    "lineage_edges",
    "workspace_allocations",
    "runtime_snapshots",
    "snapshot_file_refs",
    "revision_diffs",
    "canvas_projection",
    "study_macro_state_snapshots",
    "owner_route_receipts",
    "dispatch_receipts",
    "turn_receipts",
    "paper_work_unit_receipts",
    "surface_refs",
    "archive_refs",
    "report_index",
)

OPL_FAMILY_ADAPTER_SURFACE = {
    "surface_kind": "mas_opl_family_persistence_lifecycle_owner_route_adoption",
    "shape": ["refs", "payload"],
    "authority": "refs_payload_projection_only",
    "maps_to_opl_contracts": {
        "persistence": "opl_family_persistence_contract.v1",
        "lifecycle": "opl_family_lifecycle_contract.v1",
        "owner_route": "opl_family_owner_route_contract.v1",
    },
    "source_tables": list(OPL_FAMILY_ADAPTER_SOURCE_TABLES),
    "forbidden_authority_surfaces": [
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "manuscript/current_package",
        "current_package.zip",
    ],
    "runtime_lifecycle_sqlite_role": {
        "classification": "A_opl_owned_mas_consumes",
        "current_mas_role": SIDECAR_ROLE,
        "owner": GENERIC_PERSISTENCE_OWNER,
        "authority": "refs_payload_projection_only",
        "generic_persistence_engine_claim_allowed": GENERIC_PERSISTENCE_ENGINE_CLAIM_ALLOWED,
        "replacement_expectation_audit_ref": (
            "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough"
        ),
        "replacement_expected_from_opl": [
            "opl_runtime_lifecycle_index_contract",
            "opl_artifact_lifecycle_storage_audit_shell",
            "opl_restore_retention_receipt_shell",
            "opl_provider_attempt_receipt_ledger",
        ],
    },
}

MIGRATION_LEDGER_REQUIRED_FIELDS = (
    "migration_run_id",
    "workspace_root",
    "workspace_id",
    "started_at",
    "finished_at",
    "mode",
    "schema_version",
    "tool_versions",
    "workspace_classification",
    "quest_classifications",
    "bucket_baseline",
    "planned_actions",
    "applied_actions",
    "skipped_items",
    "compatibility_exports",
    "restore_proofs",
    "git_tracking_check",
    "authority_surfaces_checked",
    "errors",
    "next_required_action",
)

COMPATIBILITY_VERIFICATION_REQUIRED_FIELDS = (
    "reader_name",
    "workspace_id",
    "study_id",
    "quest_id",
    "authority_files_checked",
    "sqlite_sidecar_checked",
    "compatibility_fallback_used",
    "export_paths",
    "result",
    "error",
)


def runtime_lifecycle_contract() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "default_db_filename": DEFAULT_DB_FILENAME,
        "sqlite_gitignore_patterns": list(SQLITE_GITIGNORE_PATTERNS),
        "workspace_classifications": list(WORKSPACE_CLASSIFICATIONS),
        "migration_run_modes": list(MIGRATION_RUN_MODES),
        "compatibility_reader_names": list(COMPATIBILITY_READER_NAMES),
        "file_authority_surfaces": list(FILE_AUTHORITY_SURFACES),
        "sqlite_sidecar_tables": list(SQLITE_SIDECAR_TABLES),
        "sidecar_indexed_surfaces": list(SIDECAR_INDEXED_SURFACES),
        "sidecar_authority_policy": SIDECAR_AUTHORITY_POLICY,
        "sidecar_role": SIDECAR_ROLE,
        "generic_persistence_owner": GENERIC_PERSISTENCE_OWNER,
        "generic_persistence_engine_claim_allowed": GENERIC_PERSISTENCE_ENGINE_CLAIM_ALLOWED,
        "sqlite_authority_scope": list(SQLITE_AUTHORITY_SCOPE),
        "sqlite_forbidden_authority_surfaces": list(SQLITE_FORBIDDEN_AUTHORITY_SURFACES),
        "quest_live_writer_root_policy": QUEST_LIVE_WRITER_ROOT_POLICY,
        "quest_git_retirement_policy": {
            "allowed_live_writer_roots": list(QUEST_ALLOWED_LIVE_WRITER_ROOTS),
            "legacy_import_restore_sources": list(QUEST_LEGACY_IMPORT_RESTORE_SOURCES),
            "forbidden_daily_lifecycle_surfaces": list(QUEST_FORBIDDEN_DAILY_LIFECYCLE_SURFACES),
        },
        "git_era_replacement_surfaces": {
            key: list(value) for key, value in GIT_ERA_REPLACEMENT_SURFACES.items()
        },
        "q1_q6_cutover_contract": [
            {key: list(value) if isinstance(value, list) else value for key, value in milestone.items()}
            for milestone in Q1_Q6_CUTOVER_CONTRACT
        ],
        "opl_family_adapter_surface": {
            key: dict(value) if isinstance(value, dict) else list(value) if isinstance(value, list) else value
            for key, value in OPL_FAMILY_ADAPTER_SURFACE.items()
        },
        "migration_ledger_required_fields": list(MIGRATION_LEDGER_REQUIRED_FIELDS),
        "compatibility_verification_required_fields": list(COMPATIBILITY_VERIFICATION_REQUIRED_FIELDS),
    }


def validate_migration_ledger(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field for field in MIGRATION_LEDGER_REQUIRED_FIELDS if field not in payload]
    mode = str(payload.get("mode") or "")
    workspace_classification = str(payload.get("workspace_classification") or "")
    invalid: dict[str, str] = {}
    if mode and mode not in MIGRATION_RUN_MODES:
        invalid["mode"] = mode
    if workspace_classification and workspace_classification not in WORKSPACE_CLASSIFICATIONS:
        invalid["workspace_classification"] = workspace_classification
    schema_version = payload.get("schema_version")
    if schema_version is not None and int(schema_version) != SCHEMA_VERSION:
        invalid["schema_version"] = str(schema_version)
    return {
        "ok": not missing and not invalid,
        "missing_required_fields": missing,
        "invalid_fields": invalid,
    }


def validate_compatibility_verification(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field for field in COMPATIBILITY_VERIFICATION_REQUIRED_FIELDS if field not in payload]
    reader_name = str(payload.get("reader_name") or "")
    invalid: dict[str, str] = {}
    if reader_name and reader_name not in COMPATIBILITY_READER_NAMES:
        invalid["reader_name"] = reader_name
    return {
        "ok": not missing and not invalid,
        "missing_required_fields": missing,
        "invalid_fields": invalid,
    }


def validate_sqlite_authority_scope(payload: Mapping[str, Any]) -> dict[str, Any]:
    authority_scope = _string_list(payload.get("authority_scope"))
    authority_surfaces = _string_list(payload.get("authority_surfaces"))
    invalid_scopes = [scope for scope in authority_scope if scope not in SQLITE_AUTHORITY_SCOPE]
    forbidden_authority_surfaces = [
        surface
        for surface in authority_surfaces
        if surface in SQLITE_FORBIDDEN_AUTHORITY_SURFACES or surface in FILE_AUTHORITY_SURFACES
    ]
    return {
        "ok": not invalid_scopes and not forbidden_authority_surfaces,
        "invalid_scopes": invalid_scopes,
        "forbidden_authority_surfaces": forbidden_authority_surfaces,
    }


def validate_quest_git_daily_lifecycle(payload: Mapping[str, Any]) -> dict[str, Any]:
    live_writer_root = str(payload.get("live_writer_root") or "")
    daily_lifecycle_surfaces = _string_list(payload.get("daily_lifecycle_surfaces"))
    legacy_sources = _string_list(payload.get("legacy_sources"))
    invalid_live_writer_root = None
    if live_writer_root and live_writer_root not in QUEST_ALLOWED_LIVE_WRITER_ROOTS:
        invalid_live_writer_root = live_writer_root
    forbidden_daily_lifecycle_surfaces = [
        surface for surface in daily_lifecycle_surfaces if surface in QUEST_FORBIDDEN_DAILY_LIFECYCLE_SURFACES
    ]
    invalid_legacy_sources = [
        source for source in legacy_sources if source not in QUEST_LEGACY_IMPORT_RESTORE_SOURCES
    ]
    return {
        "ok": not invalid_live_writer_root
        and not forbidden_daily_lifecycle_surfaces
        and not invalid_legacy_sources,
        "invalid_live_writer_root": invalid_live_writer_root,
        "forbidden_daily_lifecycle_surfaces": forbidden_daily_lifecycle_surfaces,
        "invalid_legacy_sources": invalid_legacy_sources,
    }


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


__all__ = [
    "COMPATIBILITY_READER_NAMES",
    "COMPATIBILITY_VERIFICATION_REQUIRED_FIELDS",
    "CONTRACT_VERSION",
    "DEFAULT_DB_FILENAME",
    "FILE_AUTHORITY_SURFACES",
    "GIT_ERA_REPLACEMENT_SURFACES",
    "MIGRATION_LEDGER_REQUIRED_FIELDS",
    "MIGRATION_RUN_MODES",
    "QUEST_ALLOWED_LIVE_WRITER_ROOTS",
    "QUEST_FORBIDDEN_DAILY_LIFECYCLE_SURFACES",
    "QUEST_LEGACY_IMPORT_RESTORE_SOURCES",
    "QUEST_LIVE_WRITER_ROOT_POLICY",
    "Q1_Q6_CUTOVER_CONTRACT",
    "SCHEMA_VERSION",
    "SIDECAR_AUTHORITY_POLICY",
    "SIDECAR_INDEXED_SURFACES",
    "SQLITE_AUTHORITY_SCOPE",
    "SQLITE_FORBIDDEN_AUTHORITY_SURFACES",
    "SQLITE_GITIGNORE_PATTERNS",
    "SQLITE_SIDECAR_TABLES",
    "SURFACE_KIND",
    "WORKSPACE_CLASSIFICATIONS",
    "runtime_lifecycle_contract",
    "validate_compatibility_verification",
    "validate_migration_ledger",
    "validate_quest_git_daily_lifecycle",
    "validate_sqlite_authority_scope",
]
