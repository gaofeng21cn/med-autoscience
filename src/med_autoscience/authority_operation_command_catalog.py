from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthorityOperationCommand:
    command: str
    cli_command: str
    mcp_mode: str
    surface: str
    description: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    dry_run_only: bool = False
    contract_gated: bool = False
    read_only: bool = True

    def command_contract(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
        }


AUTHORITY_OPERATION_COMMANDS: tuple[AuthorityOperationCommand, ...] = (
    AuthorityOperationCommand(
        command="workspace-authority-migration-audit",
        cli_command="workspace-authority-migration-audit",
        mcp_mode="workspace_authority_migration_audit",
        surface="workspace_authority_migration_audit",
        description="Dry-run migration audit for workspace/study authority and lifecycle readiness.",
        required_fields=("workspace_roots",),
        dry_run_only=True,
    ),
    AuthorityOperationCommand(
        command="storage-governance-report",
        cli_command="storage-governance-report",
        mcp_mode="storage_governance_report",
        surface="storage_governance_report",
        description="Read-only storage governance report covering authority, growth buckets, retention, and backfill plan shape.",
        required_fields=("workspace_roots",),
        optional_fields=("markdown", "deep", "max_files", "max_seconds"),
    ),
    AuthorityOperationCommand(
        command="delivery-authority-backfill-apply",
        cli_command="delivery-authority-backfill-apply",
        mcp_mode="delivery_authority_backfill_apply",
        surface="delivery_authority_backfill_apply",
        description="Controller-gated delivery manifest backfill apply for lifecycle hook, source signature, and publication refs.",
        required_fields=("workspace_roots",),
        optional_fields=("apply", "authority_snapshot"),
        contract_gated=True,
        read_only=False,
    ),
    AuthorityOperationCommand(
        command="artifact-lifecycle-report",
        cli_command="artifact-lifecycle-report",
        mcp_mode="artifact_lifecycle_report",
        surface="artifact_lifecycle_report",
        description="Read-only bounded artifact lifecycle operations report.",
        required_fields=("workspace_roots",),
        optional_fields=("markdown", "deep", "max_files", "max_seconds"),
    ),
    AuthorityOperationCommand(
        command="artifact-lifecycle-continuous-soak-summary",
        cli_command="artifact-lifecycle-continuous-soak-summary",
        mcp_mode="artifact_lifecycle_continuous_soak_summary",
        surface="artifact_lifecycle_continuous_soak_summary",
        description="Read-only installed smoke summary for migration, lifecycle, and storage governance planning.",
        required_fields=("workspace_roots",),
        optional_fields=("deep", "max_files", "max_seconds"),
        dry_run_only=True,
    ),
)

AUTHORITY_OPERATION_COMMANDS_BY_COMMAND = {
    item.command: item for item in AUTHORITY_OPERATION_COMMANDS
}
AUTHORITY_OPERATION_COMMANDS_BY_MCP_MODE = {
    item.mcp_mode: item for item in AUTHORITY_OPERATION_COMMANDS
}
AUTHORITY_OPERATION_CLI_COMMANDS = tuple(item.cli_command for item in AUTHORITY_OPERATION_COMMANDS)
AUTHORITY_OPERATION_MCP_MODES = tuple(item.mcp_mode for item in AUTHORITY_OPERATION_COMMANDS)


def build_authority_operations_command_contracts() -> list[dict[str, Any]]:
    return [item.command_contract() for item in AUTHORITY_OPERATION_COMMANDS]


def build_authority_product_entry_mode_schema() -> dict[str, Any]:
    return {
        "type": "string",
        "enum": list(AUTHORITY_OPERATION_MCP_MODES),
    }


def product_entry_description_modes_text() -> str:
    return ", ".join(AUTHORITY_OPERATION_MCP_MODES)


__all__ = [
    "AUTHORITY_OPERATION_COMMANDS",
    "AUTHORITY_OPERATION_CLI_COMMANDS",
    "AUTHORITY_OPERATION_COMMANDS_BY_COMMAND",
    "AUTHORITY_OPERATION_COMMANDS_BY_MCP_MODE",
    "AUTHORITY_OPERATION_MCP_MODES",
    "AuthorityOperationCommand",
    "build_authority_operations_command_contracts",
    "build_authority_product_entry_mode_schema",
    "product_entry_description_modes_text",
]
