from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class McpToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    metadata: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None
    annotations: dict[str, Any] | None = None

    def as_manifest_entry(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }
        if self.output_schema is not None:
            payload["outputSchema"] = self.output_schema
        if self.annotations is not None:
            payload["annotations"] = self.annotations
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        return payload


def build_tool_registry(
    *,
    authority_operation_mode_schema: dict[str, Any],
    authority_operation_modes_text: str,
    authority_operation_contract_gap_text: str,
    action_catalog_metadata_by_tool: dict[str, dict[str, Any]] | None = None,
) -> tuple[McpToolSpec, ...]:
    metadata_by_tool = action_catalog_metadata_by_tool or {}
    authority_action = dict(metadata_by_tool.get("authority_operations") or {})
    authority_description = str(authority_action.get("description") or "").strip()
    if not authority_description:
        authority_description = (
            "Call MAS authority-operation domain handlers through one tool: "
            f"{authority_operation_modes_text}. workspace_authority_migration_audit is dry-run-only; "
            "storage_governance_report and artifact_lifecycle_report are read-only; "
            "delivery_authority_backfill_apply is MAS delivery-authority gated. "
            "Physical cleanup and safe-cache deletion are owned by OPL current-control-state. "
            f"{authority_operation_contract_gap_text}"
        )
    return (
        McpToolSpec(
            name="doctor_audit",
            description=(
                "Run doctor-side MedAutoScience audits through one task tool: "
                "report, profile, overlay_status, or backend_audit."
            ),
            output_schema=_result_envelope_schema(),
            annotations=_annotations(read_only=False),
            input_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string"},
                    "profile_path": {"type": "string"},
                    "quest_root": {"type": "string"},
                    "refresh": {"type": "boolean"},
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
        ),
        McpToolSpec(
            name="workspace_readiness",
            description=(
                "Inspect or initialize workspace readiness through one tool: "
                "init_workspace, startup_data_readiness, portfolio_memory_status, "
                "init_portfolio_memory, workspace_literature_status, or init_workspace_literature."
            ),
            output_schema=_result_envelope_schema(),
            annotations=_annotations(read_only=False),
            input_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string"},
                    "profile_path": {"type": "string"},
                    "workspace_root": {"type": "string"},
                    "workspace_name": {"type": "string"},
                    "default_publication_profile": {"type": "string"},
                    "default_citation_style": {"type": "string"},
                    "dry_run": {"type": "boolean"},
                    "force": {"type": "boolean"},
                    "initialize_git": {"type": "boolean"},
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
        ),
        McpToolSpec(
            name="research_assets",
            description=(
                "Read or prepare research-side assets through one tool: data_assets_status, "
                "external_research_status, or prepare_external_research."
            ),
            output_schema=_result_envelope_schema(),
            annotations=_annotations(read_only=False),
            input_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string"},
                    "workspace_root": {"type": "string"},
                    "as_of_date": {"type": "string"},
                },
                "required": ["mode", "workspace_root"],
                "additionalProperties": False,
            },
        ),
        McpToolSpec(
            name="study_progress",
            description=(
                "Read a physician-friendly, read-only study progress projection built from "
                "canonical durable surfaces. It summarizes current stage, paper progress, "
                "blockers, and supervision links without becoming a second runtime authority."
            ),
            metadata=_tool_metadata(metadata_by_tool, "study_progress"),
            output_schema=_result_envelope_schema(),
            annotations=_annotations(read_only=True),
            input_schema={
                "type": "object",
                "properties": {
                    "profile_path": {"type": "string"},
                    "study_id": {"type": "string"},
                    "study_root": {"type": "string"},
                    "entry_mode": {"type": "string"},
                },
                "required": ["profile_path"],
                "additionalProperties": False,
            },
        ),
        McpToolSpec(
            name="open_auto_research_soak",
            description=(
                "Read DM002/Open Auto Research soak status as a compact read-only MCP surface. "
                "Set allow_controller_writes only when a separate controller-authorized contract "
                "allows controller writes; this tool never authorizes publication quality or "
                "ad-hoc artifact mutation."
            ),
            output_schema=_result_envelope_schema(),
            annotations=_annotations(read_only=False),
            input_schema={
                "type": "object",
                "properties": {
                    "profile_path": {"type": "string"},
                    "study_id": {"type": "string"},
                    "study_root": {"type": "string"},
                    "entry_mode": {"type": "string"},
                    "allow_controller_writes": {"type": "boolean"},
                },
                "required": ["profile_path"],
                "additionalProperties": False,
            },
        ),
        McpToolSpec(
            name="publication_status",
            description=(
                "Read publication-side controller status through one task tool: "
                "medical_literature_audit or medical_reporting_audit."
            ),
            output_schema=_result_envelope_schema(),
            annotations=_annotations(read_only=False),
            input_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string"},
                    "quest_root": {"type": "string"},
                    "apply": {"type": "boolean"},
                },
                "required": ["mode", "quest_root"],
                "additionalProperties": False,
            },
        ),
        McpToolSpec(
            name="authority_operations",
            description=authority_description,
            metadata=_tool_metadata(metadata_by_tool, "authority_operations"),
            output_schema=_result_envelope_schema(),
            annotations=_annotations(read_only=False),
            input_schema={
                "type": "object",
                "properties": {
                    "mode": authority_action.get("input_schema") or authority_operation_mode_schema,
                    "workspace_roots": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "apply": {"type": "boolean"},
                    "authority_snapshot": {"type": "object"},
                    "retention_report": {"type": "object"},
                    "markdown": {"type": "boolean"},
                    "deep": {"type": "boolean"},
                    "max_files": {"type": "integer", "minimum": 1},
                    "max_seconds": {"type": "number", "exclusiveMinimum": 0},
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
        ),
        McpToolSpec(
            name="agent_tool_arsenal",
            description=(
                "Read the MAS Agent Tool Arsenal / Capability Invocation OS index, cards, "
                "current_owner_delta invocation plan, or result envelope schema for autonomous agents."
            ),
            metadata={
                "surface_kind": "mas_agent_tool_arsenal_mcp_surface",
                "contract_ref": "contracts/agent_tool_arsenal.json",
            },
            output_schema=_result_envelope_schema(),
            annotations=_annotations(read_only=True),
            input_schema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": [
                            "index",
                            "card",
                            "plan",
                            "result_envelope_schema",
                        ],
                    },
                    "tool_id": {"type": "string"},
                    "current_owner_delta": {"type": "object"},
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
        ),
    )


def _tool_metadata(metadata_by_tool: dict[str, dict[str, Any]], tool_name: str) -> dict[str, Any] | None:
    payload = metadata_by_tool.get(tool_name)
    if payload is None:
        return None
    return {"action_catalog_projection": dict(payload)}


def manifest_from_registry(registry: tuple[McpToolSpec, ...]) -> list[dict[str, Any]]:
    return [spec.as_manifest_entry() for spec in registry]


def _result_envelope_schema() -> dict[str, Any]:
    from med_autoscience.agent_tool_arsenal import build_tool_result_envelope_schema

    return build_tool_result_envelope_schema()


def _annotations(*, read_only: bool) -> dict[str, Any]:
    from med_autoscience.agent_tool_arsenal import mcp_tool_annotations

    return mcp_tool_annotations("", read_only=read_only)
