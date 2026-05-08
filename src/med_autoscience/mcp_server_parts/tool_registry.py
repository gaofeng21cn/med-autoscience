from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class McpToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    metadata: dict[str, Any] | None = None

    def as_manifest_entry(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }
        if self.metadata is not None:
            payload["metadata"] = self.metadata
        return payload


STUDY_RUNTIME_LIVE_GUARD_DESCRIPTION = (
    "If `autonomous_runtime_notice.required = true` or "
    "`execution_owner_guard.supervisor_only = true`, the caller must notify the user, "
    "surface the monitoring entry, and switch into supervisor-only mode. Treat "
    "`publication_supervisor_state.bundle_tasks_downstream_only = true` as a hard block "
    "on bundle/build/proofing actions."
)


def build_tool_registry(
    *,
    product_entry_mode_schema: dict[str, Any],
    product_entry_modes_text: str,
    product_entry_contract_gap_text: str,
    action_catalog_metadata_by_tool: dict[str, dict[str, Any]] | None = None,
) -> tuple[McpToolSpec, ...]:
    metadata_by_tool = action_catalog_metadata_by_tool or {}
    product_entry_action = dict(metadata_by_tool.get("product_entry") or {})
    product_entry_description = str(product_entry_action.get("description") or "").strip()
    if not product_entry_description:
        product_entry_description = (
            "Read MedAutoScience product-entry surfaces through one tool: "
            f"{product_entry_modes_text}. migration_audit is dry-run-only; governance_report is read-only; "
            "backfill_apply and cleanup_apply are contract-gated; safe_cache_cleanup_apply is limited to allowlisted delete-safe-cache actions. "
            "lifecycle_report and continuous_soak_summary are read-only unless a separate controller apply contract authorizes cleanup. "
            f"{product_entry_contract_gap_text}"
        )
    return (
        McpToolSpec(
            name="doctor_audit",
            description=(
                "Run doctor-side MedAutoScience audits through one task tool: "
                "report, profile, overlay_status, backend_audit, or hermes_runtime."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string"},
                    "profile_path": {"type": "string"},
                    "quest_root": {"type": "string"},
                    "refresh": {"type": "boolean"},
                    "hermes_agent_repo_root": {"type": "string"},
                    "hermes_home_root": {"type": "string"},
                },
                "required": ["mode"],
                "additionalProperties": False,
            },
        ),
        McpToolSpec(
            name="workspace_readiness",
            description=(
                "Inspect or initialize workspace readiness through one tool: cockpit, "
                "init_workspace, startup_data_readiness, portfolio_memory_status, "
                "init_portfolio_memory, workspace_literature_status, or init_workspace_literature."
            ),
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
            name="study_runtime",
            description=(
                "Inspect or control study runtime through one task tool: runtime_watch, "
                "study_runtime_status, or ensure_study_runtime. "
                f"{STUDY_RUNTIME_LIVE_GUARD_DESCRIPTION}"
            ),
            metadata=_tool_metadata(metadata_by_tool, "study_runtime"),
            input_schema={
                "type": "object",
                "properties": {
                    "mode": {"type": "string"},
                    "profile_path": {"type": "string"},
                    "quest_root": {"type": "string"},
                    "runtime_root": {"type": "string"},
                    "study_id": {"type": "string"},
                    "study_root": {"type": "string"},
                    "entry_mode": {"type": "string"},
                    "allow_stopped_relaunch": {"type": "boolean"},
                    "explicit_user_wakeup": {"type": "boolean"},
                    "force": {"type": "boolean"},
                },
                "required": ["mode"],
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
            name="product_entry",
            description=product_entry_description,
            metadata=_tool_metadata(metadata_by_tool, "product_entry"),
            input_schema={
                "type": "object",
                "properties": {
                    "mode": product_entry_action.get("input_schema") or product_entry_mode_schema,
                    "profile_path": {"type": "string"},
                    "study_id": {"type": "string"},
                    "study_root": {"type": "string"},
                    "entry_mode": {"type": "string"},
                    "workspace_roots": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "apply": {"type": "boolean"},
                    "control_plane_snapshot": {"type": "object"},
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
    )


def _tool_metadata(metadata_by_tool: dict[str, dict[str, Any]], tool_name: str) -> dict[str, Any] | None:
    payload = metadata_by_tool.get(tool_name)
    if payload is None:
        return None
    return {"action_catalog_projection": dict(payload)}


def manifest_from_registry(registry: tuple[McpToolSpec, ...]) -> list[dict[str, Any]]:
    return [spec.as_manifest_entry() for spec in registry]
