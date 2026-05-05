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
    "dataset_manifest",
    "restore_index",
    "paper",
    "manuscript/current_package",
    "current_package.zip",
)

SQLITE_SIDECAR_TABLES = (
    "schema_migrations",
    "runtime_objects",
    "runtime_events",
    "run_summaries",
    "bash_exec_sessions",
    "codex_sessions",
    "report_index",
    "storage_audit_runs",
    "retention_actions",
    "archive_refs",
    "compatibility_exports",
    "migration_runs",
)

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


__all__ = [
    "COMPATIBILITY_READER_NAMES",
    "COMPATIBILITY_VERIFICATION_REQUIRED_FIELDS",
    "CONTRACT_VERSION",
    "DEFAULT_DB_FILENAME",
    "FILE_AUTHORITY_SURFACES",
    "MIGRATION_LEDGER_REQUIRED_FIELDS",
    "MIGRATION_RUN_MODES",
    "SCHEMA_VERSION",
    "SQLITE_GITIGNORE_PATTERNS",
    "SQLITE_SIDECAR_TABLES",
    "SURFACE_KIND",
    "WORKSPACE_CLASSIFICATIONS",
    "runtime_lifecycle_contract",
    "validate_compatibility_verification",
    "validate_migration_ledger",
]
