from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience import editable_shared_bootstrap as _editable_shared_bootstrap
from med_autoscience.authority_operation_command_catalog import (
    build_authority_product_entry_mode_schema,
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
    "If the needed MAS contract is missing, stop and close the contract gap through a controller-authorized domain handler surface exposed by CLI/MCP/Skill/product-entry before continuing; do not perform ad-hoc execution."
)
MCP_INPUT_SCHEMA_BY_ACTION_ID = {
    "launch_study": {"type": "string", "enum": ["owner_route_handoff", "stage_attempt", "request_opl_stage_attempt"]},
    "study_progress": {"type": "object"},
    "authority_operations": "authority_operation_mode_schema",
    "display_pack_capability_discover": {
        "type": "object",
        "properties": {
            "repo_root": {"type": "string"},
            "paper_root": {"type": "string"},
            "include_templates": {"type": "boolean"},
        },
    },
    "display_pack_figure_plan": {
        "type": "object",
        "required": ["figure_request"],
        "properties": {
            "repo_root": {"type": "string"},
            "paper_root": {"type": "string"},
            "figure_request": {"type": "object"},
            "max_recommendations": {"type": "integer"},
        },
    },
    "display_pack_preflight": {
        "type": "object",
        "properties": {
            "repo_root": {"type": "string"},
            "paper_root": {"type": "string"},
            "template_id": {"type": "string"},
            "figure_request": {"type": "object"},
            "check_runtime_dependencies": {"type": "boolean"},
        },
    },
    "display_pack_render": {
        "type": "object",
        "required": ["paper_root"],
        "properties": {
            "repo_root": {"type": "string"},
            "paper_root": {"type": "string"},
            "figure_request": {"type": "object"},
            "visual_audit_review": {"type": "object"},
        },
    },
}
AUTHORITATIVE_TRUTH_REFS = [
    "/progress_projection",
    "/owner_route/latest.json",
    "/publication_eval/latest.json",
    "/controller_decisions/latest.json",
]


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
        "descriptor_projection_owner": "one-person-lab",
        "domain_handler_target_owner": MAS_TRUTH_OWNER,
        "helper_write_policy": "no_domain_truth_writes",
        "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
    }


def _authority_operation_mode_schema() -> dict[str, Any]:
    return build_authority_product_entry_mode_schema()


def _authority_operations_summary() -> str:
    return (
        "Call MAS authority-operation domain handlers through one tool: "
        f"{product_entry_description_modes_text()}. workspace_authority_migration_audit is dry-run-only; "
        "storage_governance_report and artifact_lifecycle_report are read-only; "
        "delivery_authority_backfill_apply is MAS delivery-authority gated. "
        "Physical cleanup and safe-cache deletion are owned by OPL current-control-state, not MAS. "
        f"{PRODUCT_ENTRY_CONTRACT_GAP_TEXT}"
    )


def _action_specs(profile_ref: str | Path | None) -> tuple[dict[str, Any], ...]:
    actions = (
        {
            "action_id": "submit_study_task",
            "title": "Submit durable MAS study task",
            "summary": "先把用户任务写成 durable study task intake，再启动研究执行。",
            "effect": "mutating",
            "command": "{prefix} study submit-task --profile {profile} --study-id <study_id> --task-intent '<task_intent>'",
            "surface_kind": "study_task_intake",
            "workspace_locator_fields": ["profile_ref", "study_id", "task_intent"],
            "mcp_public_runtime": False,
            "human_gate_ids": ["study_user_decision_gate"],
        },
        {
            "action_id": "launch_study",
            "title": "Submit MAS study launch handoff",
            "summary": "写入 MAS domain handoff，由 OPL 唯一控制面 hydrate 成 stage attempt。",
            "effect": "mutating",
            "command": "{prefix} study launch --profile {profile} --study-id <study_id>",
            "surface_kind": "launch_study",
            "workspace_locator_fields": ["profile_ref", "study_id"],
            "mcp_public_runtime": False,
            "human_gate_ids": ["study_user_decision_gate"],
        },
        {
            "action_id": "study_progress",
            "title": "Inspect MAS study progress",
            "summary": "持续读取当前 study 的阶段摘要、阻塞、监督 freshness 与下一步。",
            "effect": "read_only",
            "command": "{prefix} study progress --profile {profile} --study-id <study_id> --format json",
            "surface_kind": "study_progress",
            "workspace_locator_fields": ["profile_ref", "study_id"],
            "mcp_tool_name": "study_progress",
            "mcp_public_runtime": True,
        },
        {
            "action_id": "study_state_matrix",
            "title": "Materialize MAS study state matrix",
            "summary": (
                "只读物化 MAS-owned study_state_matrix，包括 domain_transition_table、"
                "family_transition_spec 和 family_transition_matrix_cases，供 OPL generic "
                "transition runner 消费；不写 study truth、不执行 domain action、不授权论文质量或投稿就绪。"
            ),
            "effect": "read_only",
            "command": "{prefix} study-state-matrix --profile {profile} --format json",
            "surface_kind": "study_state_matrix",
            "workspace_locator_fields": ["profile_ref"],
            "mcp_public_runtime": False,
            "authority_boundary": {
                "domain_truth_owner": MAS_TRUTH_OWNER,
                "helper_owner": "MedAutoScience",
                "descriptor_projection_owner": "one-person-lab",
                "domain_handler_target_owner": MAS_TRUTH_OWNER,
                "helper_write_policy": "no_domain_truth_writes",
                "surface_authority": "domain_transition_read_model_materialization",
                "runner_owner": "OPL Framework",
                "domain_transition_owner": MAS_TRUTH_OWNER,
                "can_write_domain_truth": False,
                "can_execute_domain_action": False,
                "can_authorize_publication_quality": False,
                "can_authorize_submission_readiness": False,
                "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
            },
        },
        {
            "action_id": "export_inspection_package",
            "title": "Export human inspection package",
            "summary": (
                "Export a human inspection only paper snapshot for writing-style review. "
                "It is not current_package, not submission_minimal authority, and cannot authorize "
                "publication quality or submission readiness."
            ),
            "effect": "read_only",
            "command": "{prefix} publication export-inspection-package --profile {profile} --study-id <study_id>",
            "surface_kind": "publication_inspection_package_export",
            "workspace_locator_fields": ["profile_ref", "study_id"],
            "mcp_public_runtime": False,
            "authority_boundary": {
                "domain_truth_owner": MAS_TRUTH_OWNER,
                "helper_owner": "one-person-lab",
                "helper_write_policy": "no_domain_truth_writes",
                "surface_authority": "human_inspection_only",
                "can_write_current_package": False,
                "can_write_submission_minimal": False,
                "can_authorize_publication_quality": False,
                "can_authorize_submission_readiness": False,
                "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
            },
        },
        {
            "action_id": "publication_aftercare_plan",
            "title": "Plan publication aftercare progression",
            "summary": (
                "Read a refs-only publication aftercare control surface for resubmission, talk package, "
                "Overleaf sync, ARIS research-pipeline / auto-review-loop / experiment queue absorption, "
                "and reviewer refresh. It can only emit MAS owner-route task refs or typed blockers; it "
                "does not write publication_eval, controller_decisions, current_package, paper package, "
                "or submission authority."
            ),
            "effect": "read_only",
            "command": "{prefix} publication aftercare-plan --study-root <study_root> --quest-root <quest_root>",
            "surface_kind": "mas_publication_aftercare_plan",
            "workspace_locator_fields": ["study_root", "quest_root"],
            "mcp_public_runtime": False,
            "authority_boundary": {
                "domain_truth_owner": MAS_TRUTH_OWNER,
                "helper_owner": "MedAutoScience",
                "helper_write_policy": "no_domain_truth_writes",
                "surface_authority": "publication_aftercare_refs_only_owner_route_control",
                "can_write_publication_eval": False,
                "can_write_controller_decisions": False,
                "can_write_current_package": False,
                "can_authorize_publication_quality": False,
                "can_authorize_submission_readiness": False,
                "can_dispatch_runtime_owner_task": False,
                "can_emit_owner_route_task_refs": True,
                "runtime_owner_task_dispatch_policy": "forbidden_mas_emits_refs_or_typed_blockers_only",
                "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
            },
        },
        {
            "action_id": "external_learning_adoption_closure",
            "title": "Inspect external learning adoption closure",
            "summary": (
                "Read the MAS-owned closure surface for Co-Scientist, Nature-skills, ARS, AutoSci, "
                "EvoScientist/EvoSkills, ARK, ARIS, PaperSpine, and Open Auto Research learning. "
                "It distinguishes owner-surface landed work from contract-only or not-landed gaps, and "
                "declares the nonblocking external-learning sidecar execution slot."
            ),
            "effect": "read_only",
            "command": "medautosci domain-handler export --profile {profile} --format json",
            "surface_kind": "mas_external_learning_adoption_closure",
            "workspace_locator_fields": ["profile_ref"],
            "mcp_public_runtime": False,
            "authority_boundary": {
                "domain_truth_owner": MAS_TRUTH_OWNER,
                "helper_owner": "MedAutoScience",
                "helper_write_policy": "no_domain_truth_writes",
                "surface_authority": "external_learning_adoption_closure_read_model",
                "can_write_publication_eval": False,
                "can_write_controller_decisions": False,
                "can_write_current_package": False,
                "can_authorize_publication_quality": False,
                "can_authorize_submission_readiness": False,
                "can_block_current_owner_action": False,
                "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
            },
        },
        {
            "action_id": "display_pack_capability_discover",
            "title": "Discover MAS Display Pack capability",
            "summary": (
                "Return the agent-facing Display Pack inventory, callable actions, expected receipt refs, "
                "and forbidden authority boundary. This is the low-friction discovery entry for MAS agents; "
                "humans manage assets, agents consume this structured capability surface."
            ),
            "effect": "read_only",
            "command": "{prefix} publication display-pack-agent-discover --repo-root <mas_repo>",
            "surface_kind": "display_pack_agent_capability",
            "workspace_locator_fields": ["repo_root", "paper_root"],
            "mcp_tool_name": "display_pack_agent",
            "mcp_tool_mode": "discover",
            "mcp_public_runtime": True,
            "authority_boundary": {
                "domain_truth_owner": MAS_TRUTH_OWNER,
                "helper_owner": MAS_TRUTH_OWNER,
                "helper_write_policy": "no_domain_truth_writes",
                "surface_authority": "display_pack_agent_capability_discovery",
                "can_mutate_data_or_statistics": False,
                "can_authorize_publication_readiness": False,
                "can_replace_visual_audit": False,
                "can_replace_owner_receipt": False,
                "can_emit_display_refs_and_receipts": True,
                "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
            },
        },
        {
            "action_id": "display_pack_figure_plan",
            "title": "Plan a Display Pack figure",
            "summary": (
                "Given a structured figure_request, rank Display Pack templates and choose the next "
                "preflight target. It prefers R/ggplot2 where the pack declares that renderer, and emits "
                "typed blockers instead of asking an agent to manually browse templates."
            ),
            "effect": "read_only",
            "command": (
                "{prefix} publication display-pack-agent-plan --repo-root <mas_repo> "
                "--figure-request-json '<figure_request_json>'"
            ),
            "surface_kind": "display_pack_agent_figure_plan",
            "workspace_locator_fields": ["repo_root", "paper_root", "figure_request"],
            "mcp_tool_name": "display_pack_agent",
            "mcp_tool_mode": "plan",
            "mcp_public_runtime": True,
            "authority_boundary": {
                "domain_truth_owner": MAS_TRUTH_OWNER,
                "helper_owner": MAS_TRUTH_OWNER,
                "helper_write_policy": "no_domain_truth_writes",
                "surface_authority": "display_pack_template_selection_advisory",
                "can_mutate_data_or_statistics": False,
                "can_authorize_publication_readiness": False,
                "can_replace_visual_audit": False,
                "can_replace_owner_receipt": False,
                "can_emit_display_refs_and_receipts": True,
                "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
            },
        },
        {
            "action_id": "display_pack_preflight",
            "title": "Preflight a Display Pack figure",
            "summary": (
                "Check selected template assets, QC profile, R runtime dependencies, style profile lock, "
                "and golden coverage before render. Findings route to style/profile/runtime/template repair "
                "without mutating data, statistics, evidence marks, or publication verdicts."
            ),
            "effect": "read_only",
            "command": (
                "{prefix} publication display-pack-agent-preflight --repo-root <mas_repo> "
                "--paper-root <paper_root> --figure-request-json '<figure_request_json>'"
            ),
            "surface_kind": "display_pack_agent_preflight",
            "workspace_locator_fields": ["repo_root", "paper_root", "template_id", "figure_request"],
            "mcp_tool_name": "display_pack_agent",
            "mcp_tool_mode": "preflight",
            "mcp_public_runtime": True,
            "authority_boundary": {
                "domain_truth_owner": MAS_TRUTH_OWNER,
                "helper_owner": MAS_TRUTH_OWNER,
                "helper_write_policy": "no_domain_truth_writes",
                "surface_authority": "display_pack_pre_render_readiness_check",
                "can_mutate_data_or_statistics": False,
                "can_authorize_publication_readiness": False,
                "can_replace_visual_audit": False,
                "can_replace_owner_receipt": False,
                "can_emit_display_refs_and_receipts": True,
                "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
            },
        },
        {
            "action_id": "display_pack_render",
            "title": "Render a Display Pack figure receipt",
            "summary": (
                "Materialize Display Pack figure artifacts and paper-level display refs from a prepared "
                "paper_root or frozen data payload. This writes display artifacts, visual-audit receipt, "
                "polish lifecycle, display_pack_lock, and publication manifest refs only; it cannot sign "
                "publication readiness or owner receipt."
            ),
            "effect": "mutating",
            "command": (
                "{prefix} publication display-pack-agent-render --repo-root <mas_repo> "
                "--paper-root <paper_root> --figure-request-json '<figure_request_json>'"
            ),
            "surface_kind": "display_pack_agent_render_receipt",
            "workspace_locator_fields": ["repo_root", "paper_root", "figure_request", "visual_audit_review"],
            "mcp_tool_name": "display_pack_agent",
            "mcp_tool_mode": "render",
            "mcp_public_runtime": True,
            "authority_boundary": {
                "domain_truth_owner": MAS_TRUTH_OWNER,
                "helper_owner": MAS_TRUTH_OWNER,
                "helper_write_policy": "display_artifacts_and_refs_only",
                "surface_authority": "display_pack_render_receipt",
                "can_mutate_data_or_statistics": False,
                "can_authorize_publication_readiness": False,
                "can_replace_visual_audit": False,
                "can_replace_owner_receipt": False,
                "can_write_publication_eval": False,
                "can_write_controller_decisions": False,
                "can_write_current_package": False,
                "can_emit_display_refs_and_receipts": True,
                "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
            },
        },
        {
            "action_id": "lightweight_executor_receipt",
            "title": "Inspect lightweight executor receipt contract",
            "summary": (
                "Read the MAS/OPL lightweight executor receipt contract. It records command "
                "evidence refs for Codex/uv/local executor attempts without executing commands, "
                "starting Docker, mounting the Docker socket, or introducing OpenHands as a default runtime."
            ),
            "effect": "read_only",
            "command": "medautosci domain-handler export --profile {profile} --format json",
            "surface_kind": "mas_lightweight_executor_receipt_contract",
            "workspace_locator_fields": ["profile_ref"],
            "mcp_public_runtime": False,
            "authority_boundary": {
                "domain_truth_owner": MAS_TRUTH_OWNER,
                "helper_owner": "MedAutoScience",
                "helper_write_policy": "no_domain_truth_writes",
                "surface_authority": "executor_receipt_contract_read_model",
                "can_execute_command": False,
                "can_start_docker": False,
                "can_mount_docker_socket": False,
                "can_write_publication_eval": False,
                "can_write_controller_decisions": False,
                "can_write_current_package": False,
                "can_write_owner_receipt": False,
                "can_write_typed_blocker": False,
                "can_authorize_publication_quality": False,
                "can_authorize_submission_readiness": False,
                "can_block_current_owner_action": False,
                "authoritative_truth_refs": list(AUTHORITATIVE_TRUTH_REFS),
            },
        },
        {
            "action_id": "mainline_status",
            "title": "Inspect MAS mainline status",
            "summary": "查看 repo 理想形态、当前阶段、剩余缺口与下一步焦点。",
            "effect": "read_only",
            "command": "{prefix} doctor mainline-status",
            "surface_kind": "mainline_status",
            "workspace_locator_fields": [],
            "mcp_public_runtime": False,
        },
        {
            "action_id": "mainline_phase",
            "title": "Inspect MAS mainline phase",
            "summary": "查看某一阶段当前可用入口、退出条件与关键文档。",
            "effect": "read_only",
            "command": "{prefix} doctor mainline-phase --phase <current|next|phase_id>",
            "surface_kind": "mainline_phase",
            "workspace_locator_fields": [],
            "mcp_public_runtime": False,
        },
        {
            "action_id": "domain_handler_export",
            "title": "Export MAS domain-handler projection",
            "summary": (
                "Export MAS-owned read-only projection, pending OPL family tasks, source refs, "
                "owner receipt contract and substrate refs for OPL generated/hosted surfaces. "
                "It does not authorize study truth, publication quality, artifact gate or current package writes."
            ),
            "effect": "read_only",
            "command": "medautosci domain-handler export --profile {profile} --format json",
            "surface_kind": "mas_family_domain_handler_export",
            "workspace_locator_fields": ["profile_ref"],
            "mcp_tool_name": "domain_handler_export",
            "mcp_public_runtime": False,
            "authority_boundary": _authority_boundary(),
        },
        {
            "action_id": "domain_handler_dispatch",
            "title": "Dispatch MAS domain-handler task",
            "summary": (
                "Consume an OPL typed queue task and return a MAS owner-route dispatch receipt, "
                "owner receipt, typed blocker, or explicit OPL opt-in executor/proof refs only; "
                "it does not authorize domain truth, publication quality, artifact gate or current package writes."
            ),
            "effect": "mutating",
            "command": "medautosci domain-handler dispatch --task <task.json> --format json",
            "surface_kind": "mas_family_domain_handler_dispatch_receipt",
            "workspace_locator_fields": ["task_ref"],
            "mcp_tool_name": "domain_handler_dispatch",
            "mcp_public_runtime": False,
            "authority_boundary": _authority_boundary(helper_owner=MAS_TRUTH_OWNER),
        },
        {
            "action_id": "authority_operations",
            "title": "Call MAS authority operation handlers",
            "summary": _authority_operations_summary(),
            "effect": "read_only",
            "command": "{prefix} product governance-report --workspace-root <workspace_root>",
            "surface_kind": "mas_authority_operation_handlers",
            "workspace_locator_fields": ["workspace_roots"],
            "mcp_tool_name": "authority_operations",
            "mcp_public_runtime": True,
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
            authority_boundary=dict(spec.get("authority_boundary") or _authority_boundary()),
        )
        mcp_tool_name = str(spec.get("mcp_tool_name") or "").strip()
        if mcp_tool_name:
            action["supported_surfaces"]["mcp"]["tool_name"] = mcp_tool_name
        mcp_tool_mode = str(spec.get("mcp_tool_mode") or "").strip()
        if mcp_tool_mode:
            action["supported_surfaces"]["mcp"]["mode"] = mcp_tool_mode
        built.append(action)
    return tuple(built)


def build_mas_action_catalog(*, profile_ref: str | Path | None = None) -> dict[str, Any]:
    catalog = build_family_action_catalog(
        catalog_id=ACTION_CATALOG_ID,
        target_domain_id=TARGET_DOMAIN_ID,
        owner=MAS_TRUTH_OWNER,
        actions=_action_specs(profile_ref),
        notes=[
            "MAS owns domain action intents, handler targets, runtime/controller/publication/quality truth, and owner receipts.",
            "OPL owns generated CLI/MCP/Skill/product/status/workbench descriptor projections and does not write MAS durable study truth.",
        ],
    )
    catalog["catalog_role"] = "domain_action_intent_and_handler_target_input_for_opl_generated_descriptors"
    catalog["descriptor_projection_owner"] = "one-person-lab"
    catalog["domain_handler_target_owner"] = MAS_TRUTH_OWNER
    catalog["domain_repo_can_own_generated_surface"] = False
    catalog["authority_boundary"] = {
        **dict(catalog.get("authority_boundary") or {}),
        "descriptor_projection_owner": "one-person-lab",
        "domain_handler_target_owner": MAS_TRUTH_OWNER,
    }
    return catalog


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
    payload = {
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
    authority_boundary = action.get("authority_boundary")
    if isinstance(authority_boundary, Mapping):
        payload["authority_boundary"] = dict(authority_boundary)
    return payload


def _with_input_schema(projection: dict[str, Any], action: object) -> dict[str, Any]:
    if not isinstance(action, Mapping):
        return projection
    action_id = str(action.get("action_id") or "")
    schema = MCP_INPUT_SCHEMA_BY_ACTION_ID.get(action_id)
    if schema == "authority_operation_mode_schema":
        return {**projection, "input_schema": _authority_operation_mode_schema()}
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
            **(
                {"authority_boundary": dict(item["authority_boundary"])}
                if isinstance(item.get("authority_boundary"), Mapping)
                else {}
            ),
        }
        for index, item in enumerate(project_mas_action_catalog("product_entry", catalog))
    }


def action_catalog_command_map(catalog: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(item["action_id"]): str(item["command"])
        for item in project_mas_action_catalog("cli", catalog)
    }


def action_catalog_metadata_by_mcp_tool(catalog: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in project_mas_action_catalog("mcp", catalog):
        name = str(item["name"])
        if name not in grouped:
            grouped[name] = item
            continue
        existing = grouped[name]
        if existing.get("surface_kind") != "mas_mcp_tool_group_projection":
            grouped[name] = {
                "name": name,
                "description": (
                    "Grouped MAS MCP tool projection. Use the mode field to select the "
                    "underlying action catalog surface."
                ),
                "surface_kind": "mas_mcp_tool_group_projection",
                "descriptor_only": False,
                "public_runtime": True,
                "actions": [existing],
            }
            existing = grouped[name]
        existing.setdefault("actions", []).append(item)
    return grouped


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
