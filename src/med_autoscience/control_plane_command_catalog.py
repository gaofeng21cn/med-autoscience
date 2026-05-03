from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ControlPlaneOperationsCommand:
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


CONTROL_PLANE_OPERATIONS_COMMANDS: tuple[ControlPlaneOperationsCommand, ...] = (
    ControlPlaneOperationsCommand(
        command="control-plane-migration-audit",
        cli_command="control-plane-migration-audit",
        mcp_mode="migration_audit",
        surface="control_plane_migration_audit",
        description="Dry-run migration audit for workspace/study authority and lifecycle readiness.",
        required_fields=("workspace_roots",),
        dry_run_only=True,
    ),
    ControlPlaneOperationsCommand(
        command="control-plane-cleanup-apply",
        cli_command="control-plane-cleanup-apply",
        mcp_mode="cleanup_apply",
        surface="control_plane_cleanup_apply",
        description="Contract-gated cleanup apply plan and allowlisted delete-safe-cache execution.",
        required_fields=("workspace_roots",),
        optional_fields=("apply",),
        contract_gated=True,
        read_only=False,
    ),
    ControlPlaneOperationsCommand(
        command="control-plane-lifecycle-report",
        cli_command="control-plane-lifecycle-report",
        mcp_mode="lifecycle_report",
        surface="control_plane_lifecycle_report",
        description="Read-only bounded artifact lifecycle operations report.",
        required_fields=("workspace_roots",),
        optional_fields=("markdown", "deep", "max_files", "max_seconds"),
    ),
)

CONTROL_PLANE_OPERATION_COMMANDS_BY_COMMAND = {
    item.command: item for item in CONTROL_PLANE_OPERATIONS_COMMANDS
}
CONTROL_PLANE_OPERATION_COMMANDS_BY_MCP_MODE = {
    item.mcp_mode: item for item in CONTROL_PLANE_OPERATIONS_COMMANDS
}
CONTROL_PLANE_OPERATION_CLI_COMMANDS = tuple(item.cli_command for item in CONTROL_PLANE_OPERATIONS_COMMANDS)
CONTROL_PLANE_OPERATION_MCP_MODES = tuple(item.mcp_mode for item in CONTROL_PLANE_OPERATIONS_COMMANDS)


def build_control_plane_operations_command_contracts() -> list[dict[str, Any]]:
    return [item.command_contract() for item in CONTROL_PLANE_OPERATIONS_COMMANDS]


def build_control_plane_product_entry_mode_schema() -> dict[str, Any]:
    return {
        "type": "string",
        "enum": [
            "product_frontdesk",
            "product_preflight",
            "product_start",
            "product_entry_manifest",
            "build_product_entry",
            *CONTROL_PLANE_OPERATION_MCP_MODES,
        ],
    }


def product_entry_description_modes_text() -> str:
    return ", ".join(
        [
            "product_frontdesk",
            "product_preflight",
            "product_start",
            "product_entry_manifest",
            "build_product_entry",
            *CONTROL_PLANE_OPERATION_MCP_MODES,
        ]
    )


__all__ = [
    "CONTROL_PLANE_OPERATIONS_COMMANDS",
    "CONTROL_PLANE_OPERATION_CLI_COMMANDS",
    "CONTROL_PLANE_OPERATION_COMMANDS_BY_COMMAND",
    "CONTROL_PLANE_OPERATION_COMMANDS_BY_MCP_MODE",
    "CONTROL_PLANE_OPERATION_MCP_MODES",
    "ControlPlaneOperationsCommand",
    "build_control_plane_operations_command_contracts",
    "build_control_plane_product_entry_mode_schema",
    "product_entry_description_modes_text",
]
