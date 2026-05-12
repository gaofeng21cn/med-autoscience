from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience import editable_shared_bootstrap as _editable_shared_bootstrap
from med_autoscience.control_plane_command_catalog import (
    build_control_plane_product_entry_mode_schema,
    product_entry_description_modes_text,
)

_editable_shared_bootstrap.ensure_editable_dependency_paths()

from opl_harness_shared.family_action_catalog import (  # noqa: E402
    build_family_action,
    build_family_action_catalog,
    project_family_action_catalog,
    validate_family_action_catalog_parity,
)


TARGET_DOMAIN_ID = "med-autoscience"
MAS_TRUTH_OWNER = "MedAutoScience"
ACTION_CATALOG_ID = "med_autoscience_action_catalog"
ACTION_CATALOG_SCHEMA_REF = "contracts/family-orchestration/family-action-catalog.schema.json"
INPUT_SCHEMA_REF = "contracts/schemas/v1/mas-action.input.schema.json"
OUTPUT_SCHEMA_REF = "contracts/schemas/v1/mas-action.output.schema.json"
PRODUCT_ENTRY_CONTRACT_GAP_TEXT = (
    "If the needed MAS contract is missing, stop and close the contract gap through a controller-authorized/CLI/MCP/product-entry surface before continuing; do not perform ad-hoc execution."
)
MCP_INPUT_SCHEMA_BY_ACTION_ID = {
    "launch_study": {"type": "string", "enum": ["runtime_watch", "study_runtime_status", "ensure_study_runtime"]},
    "study_progress": {"type": "object"},
    "product_entry": "product_entry_mode_schema",
}


def _quote_profile(profile_ref: str | Path | None) -> str:
    if profile_ref is None:
        return "<profile>"
    return str(Path(profile_ref).expanduser().resolve())


def _cli_prefix() -> str:
    return "uv run python -m med_autoscience.cli"


def _command(command: str, *, profile_ref: str | Path | None) -> str:
    profile = _quote_profile(profile_ref)
    return command.format(prefix=_cli_prefix(), profile=profile)


def _authority_boundary(*, helper_owner: str = "one-person-lab") -> dict[str, Any]:
    return {
        "domain_truth_owner": MAS_TRUTH_OWNER,
        "helper_owner": helper_owner,
        "helper_write_policy": "no_domain_truth_writes",
        "authoritative_truth_refs": [
            "/study_runtime_status",
            "/runtime_watch",
            "/publication_eval/latest.json",
            "/controller_decisions/latest.json",
        ],
    }


def _product_entry_mode_schema() -> dict[str, Any]:
    return build_control_plane_product_entry_mode_schema()


def _product_entry_summary() -> str:
    return (
        "Read MedAutoScience product-entry surfaces through one tool: "
        f"{product_entry_description_modes_text()}. migration_audit is dry-run-only; "
        "governance_report is read-only; backfill_apply and cleanup_apply are contract-gated; "
        "safe_cache_cleanup_apply is limited to allowlisted delete-safe-cache actions. "
        "lifecycle_report and continuous_soak_summary are read-only unless a separate controller apply contract authorizes cleanup. "
        f"{PRODUCT_ENTRY_CONTRACT_GAP_TEXT}"
    )


def _action_specs(profile_ref: str | Path | None) -> tuple[dict[str, Any], ...]:
    actions = (
        {
            "action_id": "product_entry_status",
            "title": "Open MAS product entry status",
            "summary": "当前 research product entry status，先暴露当前 product entry、workspace inbox 与 shared handoff 入口。",
            "effect": "read_only",
            "command": "{prefix} product-entry-status --profile {profile}",
            "surface_kind": "product_entry_status",
            "workspace_locator_fields": ["profile_ref"],
            "mcp_public_runtime": False,
        },
        {
            "action_id": "workspace_cockpit",
            "title": "Open MAS workspace cockpit",
            "summary": "当前 workspace 级用户 inbox，聚合 attention queue、监督在线态与研究入口回路。",
            "effect": "read_only",
            "command": "{prefix} workspace-cockpit --profile {profile} --format json",
            "surface_kind": "workspace_cockpit",
            "workspace_locator_fields": ["profile_ref"],
            "mcp_public_runtime": False,
        },
        {
            "action_id": "submit_study_task",
            "title": "Submit durable MAS study task",
            "summary": "先把用户任务写成 durable study task intake，再启动研究执行。",
            "effect": "mutating",
            "command": "{prefix} submit-study-task --profile {profile} --study-id <study_id> --task-intent '<task_intent>'",
            "surface_kind": "study_task_intake",
            "workspace_locator_fields": ["profile_ref", "study_id", "task_intent"],
            "mcp_public_runtime": False,
            "human_gate_ids": ["study_user_decision_gate"],
        },
        {
            "action_id": "launch_study",
            "title": "Launch or continue MAS study runtime",
            "summary": "创建或恢复 study runtime，并进入当前研究主线。",
            "effect": "mutating",
            "command": "{prefix} launch-study --profile {profile} --study-id <study_id>",
            "surface_kind": "launch_study",
            "workspace_locator_fields": ["profile_ref", "study_id"],
            "mcp_tool_name": "study_runtime",
            "mcp_public_runtime": True,
            "human_gate_ids": ["study_user_decision_gate"],
        },
        {
            "action_id": "study_progress",
            "title": "Inspect MAS study progress",
            "summary": "持续读取当前 study 的阶段摘要、阻塞、监督 freshness 与下一步。",
            "effect": "read_only",
            "command": "{prefix} study-progress --profile {profile} --study-id <study_id> --format json",
            "surface_kind": "study_progress",
            "workspace_locator_fields": ["profile_ref", "study_id"],
            "mcp_tool_name": "study_progress",
            "mcp_public_runtime": True,
        },
        {
            "action_id": "mainline_status",
            "title": "Inspect MAS mainline status",
            "summary": "查看 repo 理想形态、当前阶段、剩余缺口与下一步焦点。",
            "effect": "read_only",
            "command": "{prefix} mainline-status",
            "surface_kind": "mainline_status",
            "workspace_locator_fields": [],
            "mcp_public_runtime": False,
        },
        {
            "action_id": "mainline_phase",
            "title": "Inspect MAS mainline phase",
            "summary": "查看某一阶段当前可用入口、退出条件与关键文档。",
            "effect": "read_only",
            "command": "{prefix} mainline-phase --phase <current|next|phase_id>",
            "surface_kind": "mainline_phase",
            "workspace_locator_fields": [],
            "mcp_public_runtime": False,
        },
        {
            "action_id": "product_entry",
            "title": "Read MAS product-entry MCP surfaces",
            "summary": _product_entry_summary(),
            "effect": "read_only",
            "command": "{prefix} product-entry-manifest --profile {profile} --format json",
            "surface_kind": "product_entry_manifest",
            "workspace_locator_fields": ["profile_ref"],
            "mcp_tool_name": "product_entry",
            "mcp_public_runtime": True,
        },
        {
            "action_id": "sidecar_export",
            "title": "Export MAS sidecar bridge projection",
            "summary": "Read-only MAS sidecar export for OPL provider queue discovery; Hermes references are optional diagnostics/provenance only.",
            "effect": "read_only",
            "command": "medautosci sidecar export --profile {profile} --format json",
            "surface_kind": "mas_family_sidecar_export",
            "workspace_locator_fields": ["profile_ref"],
            "mcp_public_runtime": False,
        },
        {
            "action_id": "sidecar_dispatch",
            "title": "Receive MAS sidecar guarded dispatch receipt",
            "summary": (
                "MAS guarded dispatch receipt for OPL provider queue control. "
                "It records a domain control receipt only and does not authorize domain truth, "
                "publication quality, artifact gate, or current package writes; Hermes paths are "
                "optional diagnostics/provenance or retire-after-parity only."
            ),
            "effect": "mutating",
            "command": "medautosci sidecar dispatch --task <task.json> --format json",
            "surface_kind": "mas_family_sidecar_dispatch_receipt",
            "workspace_locator_fields": ["task_path"],
            "mcp_public_runtime": False,
        },
    )
    built: list[dict[str, Any]] = []
    for spec in actions:
        action = build_family_action(
            action_id=str(spec["action_id"]),
            title=str(spec["title"]),
            summary=str(spec["summary"]),
            owner=TARGET_DOMAIN_ID,
            effect=str(spec["effect"]),
            command=_command(str(spec["command"]), profile_ref=profile_ref),
            surface_kind=str(spec["surface_kind"]),
            input_schema_ref=INPUT_SCHEMA_REF,
            output_schema_ref=OUTPUT_SCHEMA_REF,
            workspace_locator_fields=tuple(spec.get("workspace_locator_fields") or ()),
            human_gate_ids=tuple(spec.get("human_gate_ids") or ()),
            mcp_public_runtime=bool(spec.get("mcp_public_runtime", True)),
            authority_boundary=_authority_boundary(),
        )
        mcp_tool_name = str(spec.get("mcp_tool_name") or "").strip()
        if mcp_tool_name:
            action["supported_surfaces"]["mcp"]["tool_name"] = mcp_tool_name
        built.append(action)
    return tuple(built)


def build_mas_action_catalog(*, profile_ref: str | Path | None = None) -> dict[str, Any]:
    return build_family_action_catalog(
        catalog_id=ACTION_CATALOG_ID,
        target_domain_id=TARGET_DOMAIN_ID,
        owner=MAS_TRUTH_OWNER,
        actions=_action_specs(profile_ref),
        notes=[
            "MAS owns the action metadata and runtime/controller/publication/quality truth.",
            "OPL consumes projections only and does not write MAS durable study truth.",
        ],
    )


def project_mas_action_catalog(
    export_format: str,
    catalog: Mapping[str, Any] | None = None,
    *,
    profile_ref: str | Path | None = None,
) -> list[dict[str, Any]]:
    payload = catalog if catalog is not None else build_mas_action_catalog(profile_ref=profile_ref)
    if export_format == "product_entry":
        return [_product_entry_projection(action) for action in _catalog_actions(payload)]
    return [
        _with_input_schema(action_projection, action)
        for action_projection, action in zip(
            project_family_action_catalog(payload, export_format),
            _catalog_actions(payload),
        )
    ]


def _catalog_actions(catalog: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [action for action in list(catalog.get("actions") or []) if isinstance(action, Mapping)]


def _surface_descriptor(action: Mapping[str, Any], surface: str) -> Mapping[str, Any]:
    surfaces = action.get("supported_surfaces")
    if not isinstance(surfaces, Mapping) or not isinstance(surfaces.get(surface), Mapping):
        return {}
    return surfaces[surface]  # type: ignore[return-value]


def _required_text(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"MAS action catalog 缺少字段: {field}")
    return text


def _product_entry_projection(action: Mapping[str, Any]) -> dict[str, Any]:
    descriptor = _surface_descriptor(action, "product_entry")
    source_command = action.get("source_command")
    if not isinstance(source_command, Mapping):
        raise ValueError("MAS action catalog action 缺少 source_command")
    return {
        "action_key": _required_text(descriptor.get("action_key") or action.get("action_id"), "action_key"),
        "command": _required_text(descriptor.get("command") or source_command.get("command"), "command"),
        "surface_kind": _required_text(
            descriptor.get("surface_kind") or source_command.get("surface_kind"),
            "surface_kind",
        ),
        "summary": _required_text(action.get("summary"), "summary"),
        "requires": [
            _required_text(item, "workspace_locator_fields[]")
            for item in list(action.get("workspace_locator_fields") or [])
        ],
    }


def _with_input_schema(projection: dict[str, Any], action: object) -> dict[str, Any]:
    if not isinstance(action, Mapping):
        return projection
    action_id = str(action.get("action_id") or "")
    schema = MCP_INPUT_SCHEMA_BY_ACTION_ID.get(action_id)
    if schema == "product_entry_mode_schema":
        return {**projection, "input_schema": _product_entry_mode_schema()}
    if not isinstance(schema, Mapping):
        return projection
    return {**projection, "input_schema": dict(schema)}


def product_entry_shell_from_action_catalog(catalog: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["action_key"]): {
            "command": str(item["command"]),
            "purpose": str(item["summary"]),
            "surface_kind": str(item["surface_kind"]),
            "action_catalog_ref": f"/action_catalog/actions/{index}",
        }
        for index, item in enumerate(project_mas_action_catalog("product_entry", catalog))
    }


def action_catalog_command_map(catalog: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(item["action_id"]): str(item["command"])
        for item in project_mas_action_catalog("cli", catalog)
    }


def action_catalog_metadata_by_mcp_tool(catalog: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item["name"]): item
        for item in project_mas_action_catalog("mcp", catalog)
    }


def validate_mas_action_catalog_parity(catalog: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return validate_family_action_catalog_parity(catalog or build_mas_action_catalog())


__all__ = [
    "ACTION_CATALOG_ID",
    "ACTION_CATALOG_SCHEMA_REF",
    "INPUT_SCHEMA_REF",
    "MAS_TRUTH_OWNER",
    "OUTPUT_SCHEMA_REF",
    "PRODUCT_ENTRY_CONTRACT_GAP_TEXT",
    "TARGET_DOMAIN_ID",
    "action_catalog_command_map",
    "action_catalog_metadata_by_mcp_tool",
    "build_mas_action_catalog",
    "product_entry_shell_from_action_catalog",
    "project_mas_action_catalog",
    "validate_mas_action_catalog_parity",
]
