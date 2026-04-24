from __future__ import annotations

from . import shared as _shared
from . import program_surfaces as _program_surfaces
from . import workspace_surfaces as _workspace_surfaces

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_program_surfaces)
_module_reexport(_workspace_surfaces)

def build_product_entry_manifest(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    mainline_payload = mainline_status.read_mainline_status()
    mainline_snapshot = _mainline_snapshot()
    build_doctor_report_fn = _controller_override("build_doctor_report", build_doctor_report)
    build_gateway_interaction_contract_fn = _controller_override(
        "_build_gateway_interaction_contract",
        _build_gateway_interaction_contract,
    )
    build_family_product_entry_orchestration = _controller_override(
        "_build_shared_family_product_entry_orchestration",
        _build_shared_family_product_entry_orchestration,
    )
    build_family_product_entry_manifest = _controller_override(
        "_build_shared_family_product_entry_manifest",
        _build_shared_family_product_entry_manifest,
    )
    validate_product_entry_manifest_contract = _controller_override(
        "_validate_product_entry_manifest_contract",
        _validate_product_entry_manifest_contract,
    )
    doctor_report = build_doctor_report_fn(profile)
    product_entry_preflight = _build_product_entry_preflight(
        doctor_report=doctor_report,
        profile_ref=profile_ref,
    )
    domain_entry_contract = _build_domain_entry_contract()
    gateway_interaction_contract = build_gateway_interaction_contract_fn()
    _validate_domain_entry_contract_shape(
        domain_entry_contract,
        context="product_entry_manifest.domain_entry_contract",
    )
    _validate_gateway_interaction_contract_shape(
        gateway_interaction_contract,
        context="product_entry_manifest.gateway_interaction_contract",
    )
    profile_arg = _profile_arg(profile_ref)
    prefix = _command_prefix(profile_ref)
    workspace_root = str(profile.workspace_root)
    study_runtime_status_command = _json_surface_command(
        f"{prefix} study-runtime-status --profile {profile_arg} --study-id <study_id>"
    )

    product_entry_shell = _build_shared_product_entry_shell_catalog({
        "product_frontdesk": {
            "command": f"{prefix} product-frontdesk --profile {profile_arg}",
            "purpose": "当前 research product frontdesk，先暴露当前 frontdoor、workspace inbox 与 shared handoff 入口。",
            "surface_kind": PRODUCT_FRONTDESK_KIND,
        },
        "workspace_cockpit": {
            "command": _json_surface_command(f"{prefix} workspace-cockpit --profile {profile_arg}"),
            "purpose": "当前 workspace 级用户 inbox，聚合 attention queue、监督在线态与研究入口回路。",
            "surface_kind": "workspace_cockpit",
        },
        "submit_study_task": {
            "command": (
                f"{prefix} submit-study-task --profile {profile_arg} "
                "--study-id <study_id> --task-intent '<task_intent>'"
            ),
            "purpose": "先把用户任务写成 durable study task intake，再启动研究执行。",
            "surface_kind": "study_task_intake",
        },
        "launch_study": {
            "command": f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
            "purpose": "创建或恢复 study runtime，并进入当前研究主线。",
            "surface_kind": "launch_study",
        },
        "study_progress": {
            "command": _json_surface_command(
                f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>"
            ),
            "purpose": "持续读取当前 study 的阶段摘要、阻塞、监督 freshness 与下一步。",
            "surface_kind": "study_progress",
        },
        "mainline_status": {
            "command": f"{prefix} mainline-status",
            "purpose": "查看 repo 理想形态、当前阶段、剩余缺口与下一步焦点。",
            "surface_kind": "mainline_status",
        },
        "mainline_phase": {
            "command": f"{prefix} mainline-phase --phase <current|next|phase_id>",
            "purpose": "查看某一阶段当前可用入口、退出条件与关键文档。",
            "surface_kind": "mainline_phase",
        },
    })
    shared_handoff = _build_shared_handoff(
        direct_entry_builder_command=(
            f"{prefix} build-product-entry --profile {profile_arg} "
            "--study-id <study_id> --entry-mode direct"
        ),
        opl_handoff_builder_command=(
            f"{prefix} build-product-entry --profile {profile_arg} "
            "--study-id <study_id> --entry-mode opl-handoff"
        ),
    )
    operator_loop_actions = _build_shared_operator_loop_action_catalog({
        "open_loop": {
            "command": product_entry_shell["workspace_cockpit"]["command"],
            "surface_kind": "workspace_cockpit",
            "summary": "先进入当前 workspace 级用户 inbox。",
            "requires": [],
        },
        "submit_task": {
            "command": product_entry_shell["submit_study_task"]["command"],
            "surface_kind": "study_task_intake",
            "summary": "先把新的研究任务写成 durable study task intake。",
            "requires": ["study_id", "task_intent"],
        },
        "continue_study": {
            "command": product_entry_shell["launch_study"]["command"],
            "surface_kind": "launch_study",
            "summary": "创建或恢复某个 study runtime，并回到当前研究主线。",
            "requires": ["study_id"],
        },
        "inspect_progress": {
            "command": product_entry_shell["study_progress"]["command"],
            "surface_kind": "study_progress",
            "summary": "读取某个 study 的当前阶段、阻塞和监督 freshness。",
            "requires": ["study_id"],
        },
    })
    family_orchestration = build_family_product_entry_orchestration(
        graph_id="mas_workspace_frontdoor_study_runtime_graph",
        target_domain_id=TARGET_DOMAIN_ID,
        graph_kind="study_runtime_orchestration",
        graph_version="2026-04-13",
        nodes=[
            {
                "node_id": "step:open_frontdesk",
                "node_kind": "operator_step",
                "title": "Open research frontdesk",
                "surface_kind": PRODUCT_FRONTDESK_KIND,
            },
            {
                "node_id": "step:submit_task",
                "node_kind": "operator_step",
                "title": "Write durable study task",
                "surface_kind": "study_task_intake",
                "produces_checkpoint": True,
            },
            {
                "node_id": "step:continue_study",
                "node_kind": "operator_step",
                "title": "Continue or relaunch a study",
                "surface_kind": "launch_study",
                "produces_checkpoint": True,
            },
            {
                "node_id": "step:inspect_progress",
                "node_kind": "operator_step",
                "title": "Inspect current study progress",
                "surface_kind": "study_progress",
                "produces_checkpoint": True,
            },
        ],
        edges=[
            {
                "from": "step:open_frontdesk",
                "to": "step:submit_task",
                "on": "new_task",
            },
            {
                "from": "step:open_frontdesk",
                "to": "step:continue_study",
                "on": "resume_study",
            },
            {
                "from": "step:open_frontdesk",
                "to": "step:inspect_progress",
                "on": "inspect_status",
            },
            {
                "from": "step:submit_task",
                "to": "step:continue_study",
                "on": "task_written",
            },
            {
                "from": "step:continue_study",
                "to": "step:inspect_progress",
                "on": "progress_refresh",
            },
        ],
        entry_nodes=["step:open_frontdesk"],
        exit_nodes=["step:continue_study", "step:inspect_progress"],
        human_gates=[
            {
                "gate_id": "study_physician_decision_gate",
                "trigger_nodes": ["step:continue_study"],
                "blocking": True,
            },
            {
                "gate_id": "publication_release_gate",
                "trigger_nodes": ["step:inspect_progress"],
                "blocking": True,
            },
        ],
        checkpoint_nodes=[
            "step:submit_task",
            "step:continue_study",
            "step:inspect_progress",
        ],
        human_gate_previews=[
            {
                "gate_id": "study_physician_decision_gate",
                "title": "Study physician decision gate",
            },
            {
                "gate_id": "publication_release_gate",
                "title": "Publication release gate",
            },
        ],
        resume_surface_kind="launch_study",
        session_locator_field="study_id",
        checkpoint_locator_field="controller_decision_path",
        action_graph_ref={
            "ref_kind": "json_pointer",
            "ref": "/family_orchestration/action_graph",
            "label": "mas family action graph",
        },
        event_envelope_surface={
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
            "label": "runtime watch event companion",
        },
        checkpoint_lineage_surface={
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/controller_decisions/latest.json",
            "label": "controller checkpoint lineage companion",
        },
    )
    product_entry_guardrails = _build_product_entry_guardrails(
        profile=profile,
        profile_ref=profile_ref,
    )
    phase2_user_product_loop = _build_phase2_user_product_loop(
        profile=profile,
        profile_ref=profile_ref,
    )
    phase3_clearance_lane = _build_phase3_clearance_lane(
        profile=profile,
        profile_ref=profile_ref,
    )
    phase4_backend_deconstruction = _build_phase4_backend_deconstruction()
    phase5_platform_target = _build_phase5_platform_target()
    product_entry_quickstart = _build_shared_product_entry_quickstart(
        summary=(
            "先从 product frontdesk 进入当前 research frontdoor，"
            "需要新任务时先写 durable study task intake，再继续某个 study 或读取进度。"
        ),
        recommended_step_id="open_frontdesk",
        steps=[
            {
                "step_id": "open_frontdesk",
                "title": "启动 MAS 前台",
                "command": product_entry_shell["product_frontdesk"]["command"],
                "surface_kind": PRODUCT_FRONTDESK_KIND,
                "summary": product_entry_shell["product_frontdesk"]["purpose"],
                "requires": [],
            },
            {
                "step_id": "submit_task",
                "title": "给 study 下 durable 任务",
                "command": product_entry_shell["submit_study_task"]["command"],
                "surface_kind": "study_task_intake",
                "summary": operator_loop_actions["submit_task"]["summary"],
                "requires": list(operator_loop_actions["submit_task"]["requires"]),
            },
            {
                "step_id": "continue_study",
                "title": "启动或续跑 study",
                "command": product_entry_shell["launch_study"]["command"],
                "surface_kind": "launch_study",
                "summary": operator_loop_actions["continue_study"]["summary"],
                "requires": list(operator_loop_actions["continue_study"]["requires"]),
            },
            {
                "step_id": "inspect_progress",
                "title": "持续看研究进度",
                "command": product_entry_shell["study_progress"]["command"],
                "surface_kind": "study_progress",
                "summary": operator_loop_actions["inspect_progress"]["summary"],
                "requires": list(operator_loop_actions["inspect_progress"]["requires"]),
            },
        ],
        resume_contract=dict(family_orchestration["resume_contract"]),
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
    )
    product_entry_start = _build_product_entry_start(
        product_entry_shell=product_entry_shell,
        operator_loop_actions=operator_loop_actions,
        family_orchestration=family_orchestration,
    )
    product_entry_overview = _build_shared_product_entry_overview(
        summary=(
            mainline_snapshot.get("current_stage_summary")
            or mainline_snapshot.get("current_program_phase_summary")
        ),
        frontdesk_command=product_entry_shell["product_frontdesk"]["command"],
        recommended_command=product_entry_shell["workspace_cockpit"]["command"],
        operator_loop_command=product_entry_shell["workspace_cockpit"]["command"],
        progress_surface={
            "surface_kind": "study_progress",
            "command": product_entry_shell["study_progress"]["command"],
            "step_id": "inspect_progress",
        },
        resume_surface=_build_shared_product_entry_resume_surface(
            command=product_entry_shell["launch_study"]["command"],
            resume_contract=family_orchestration["resume_contract"],
        ),
        recommended_step_id=product_entry_quickstart["recommended_step_id"],
        next_focus=list(mainline_snapshot.get("next_focus") or []),
        remaining_gaps_count=len(list(mainline_payload.get("remaining_gaps") or [])),
        human_gate_ids=list(product_entry_quickstart["human_gate_ids"]),
    )
    product_entry_readiness = _build_shared_product_entry_readiness(
        verdict="runtime_ready_not_standalone_product",
        usable_now=True,
        good_to_use_now=False,
        fully_automatic=False,
        summary=(
            "当前可以作为 research frontdesk / CLI 主线使用，并通过稳定的 runtime 回路持续推进研究；"
            "但还不是成熟的独立医学产品前台。"
        ),
        recommended_start_surface=PRODUCT_FRONTDESK_KIND,
        recommended_start_command=product_entry_shell["product_frontdesk"]["command"],
        recommended_loop_surface="workspace_cockpit",
        recommended_loop_command=product_entry_shell["workspace_cockpit"]["command"],
        blocking_gaps=[
            "独立医学前台 / hosted product entry 仍未 landed。",
            "更多 workspace / host 的真实 clearance 与 study-local blocker 收口仍在继续。",
        ],
    )
    managed_runtime_contract = _build_managed_runtime_contract(
        domain_owner=TARGET_DOMAIN_ID,
        executor_owner="med_deepscientist",
        supervision_status_surface="study_progress",
        attention_queue_surface="workspace_cockpit",
        recovery_contract_surface="study_runtime_status",
    )
    runtime = {
        "runtime_owner": "upstream_hermes_agent",
        "domain_owner": TARGET_DOMAIN_ID,
        "executor_owner": "med_deepscientist",
        "runtime_substrate": "external_hermes_agent_target",
        "managed_runtime_backend_id": profile.managed_runtime_backend_id,
        "runtime_root": str(profile.runtime_root),
        "hermes_home_root": str(profile.hermes_home_root),
    }
    frontdesk_surface = _build_shared_product_entry_shell_linked_surface(
        shell_key="product_frontdesk",
        shell_surface=product_entry_shell["product_frontdesk"],
        summary=product_entry_shell["product_frontdesk"]["purpose"],
    )
    operator_loop_surface = _build_shared_product_entry_shell_linked_surface(
        shell_key="workspace_cockpit",
        shell_surface=product_entry_shell["workspace_cockpit"],
        summary=product_entry_shell["workspace_cockpit"]["purpose"],
    )
    repo_mainline = {
        "program_id": mainline_snapshot.get("program_id"),
        "current_stage_id": mainline_snapshot.get("current_stage_id"),
        "current_stage_status": mainline_snapshot.get("current_stage_status"),
        "current_stage_summary": mainline_snapshot.get("current_stage_summary"),
        "current_program_phase_id": mainline_snapshot.get("current_program_phase_id"),
        "current_program_phase_status": mainline_snapshot.get("current_program_phase_status"),
        "current_program_phase_summary": mainline_snapshot.get("current_program_phase_summary"),
        "next_focus": list(mainline_snapshot.get("next_focus") or []),
    }
    single_project_boundary = dict(mainline_snapshot.get("single_project_boundary") or {})
    capability_owner_boundary = dict(mainline_snapshot.get("capability_owner_boundary") or {})
    product_entry_status = {
        "summary": mainline_snapshot.get("current_stage_summary")
        or mainline_snapshot.get("current_program_phase_summary"),
        "next_focus": list(mainline_snapshot.get("next_focus") or []),
        "remaining_gaps_count": len(list(mainline_payload.get("remaining_gaps") or [])),
    }
    runtime_inventory = _build_runtime_inventory_surface(
        profile=profile,
        runtime=runtime,
        managed_runtime_contract=managed_runtime_contract,
        product_entry_preflight=product_entry_preflight,
        operator_loop_surface=operator_loop_surface,
    )
    task_lifecycle = _build_task_lifecycle_surface(
        repo_mainline=repo_mainline,
        product_entry_status=product_entry_status,
        product_entry_readiness=product_entry_readiness,
        family_orchestration=family_orchestration,
        operator_loop_surface=operator_loop_surface,
        product_entry_shell=product_entry_shell,
    )
    session_continuity = _build_session_continuity_surface(
        runtime=runtime,
        product_entry_preflight=product_entry_preflight,
        family_orchestration=family_orchestration,
        product_entry_shell=product_entry_shell,
        task_lifecycle=task_lifecycle,
        study_runtime_status_command=study_runtime_status_command,
    )
    progress_projection = _build_progress_projection_surface(
        profile=profile,
        repo_mainline=repo_mainline,
        product_entry_status=product_entry_status,
        product_entry_preflight=product_entry_preflight,
        product_entry_readiness=product_entry_readiness,
        family_orchestration=family_orchestration,
        operator_loop_surface=operator_loop_surface,
        product_entry_shell=product_entry_shell,
        study_runtime_status_command=study_runtime_status_command,
    )
    artifact_inventory = _build_artifact_inventory_surface(
        profile=profile,
        progress_projection=progress_projection,
        product_entry_shell=product_entry_shell,
        study_runtime_status_command=study_runtime_status_command,
    )
    skill_catalog = _build_skill_catalog_surface(
        runtime=runtime,
        family_orchestration=family_orchestration,
        session_continuity=session_continuity,
        progress_projection=progress_projection,
        artifact_inventory=artifact_inventory,
        product_entry_status=product_entry_status,
        domain_entry_contract=domain_entry_contract,
        product_entry_shell=product_entry_shell,
    )
    automation = _build_automation_surface(
        profile=profile,
        profile_ref=profile_ref,
        product_entry_status=product_entry_status,
    )

    payload = build_family_product_entry_manifest(
        manifest_kind=PRODUCT_ENTRY_MANIFEST_KIND,
        target_domain_id=TARGET_DOMAIN_ID,
        formal_entry={
            "default": "CLI",
            "supported_protocols": ["MCP"],
            "internal_surface": "controller",
        },
        workspace_locator={
            "workspace_surface_kind": "med_autoscience_workspace_profile",
            "profile_name": profile.name,
            "workspace_root": workspace_root,
            "profile_ref": str(Path(profile_ref).expanduser().resolve()) if profile_ref is not None else None,
        },
        runtime=runtime,
        managed_runtime_contract=managed_runtime_contract,
        repo_mainline=repo_mainline,
        product_entry_status=product_entry_status,
        frontdesk_surface=frontdesk_surface,
        operator_loop_surface=operator_loop_surface,
        operator_loop_actions=operator_loop_actions,
        recommended_shell="workspace_cockpit",
        recommended_command=product_entry_shell["workspace_cockpit"]["command"],
        product_entry_shell=product_entry_shell,
        shared_handoff=shared_handoff,
        runtime_inventory=runtime_inventory,
        task_lifecycle=task_lifecycle,
        session_continuity=session_continuity,
        progress_projection=progress_projection,
        artifact_inventory=artifact_inventory,
        skill_catalog=skill_catalog,
        automation=automation,
        product_entry_start=product_entry_start,
        product_entry_overview=product_entry_overview,
        product_entry_preflight=product_entry_preflight,
        product_entry_readiness=product_entry_readiness,
        product_entry_quickstart=product_entry_quickstart,
        family_orchestration=family_orchestration,
        remaining_gaps=list(mainline_payload.get("remaining_gaps") or []),
        schema_ref=PRODUCT_ENTRY_MANIFEST_SCHEMA_REF,
        domain_entry_contract=domain_entry_contract,
        gateway_interaction_contract=gateway_interaction_contract,
        notes=[
            "This manifest freezes the current MAS repo-tracked research product-entry shell only.",
            "It does not include the display / paper-figure asset line.",
            "It does not claim that a mature standalone medical frontend is already landed.",
        ],
        extra_payload={
            "schema_version": SCHEMA_VERSION,
            "single_project_boundary": single_project_boundary,
            "capability_owner_boundary": capability_owner_boundary,
            "executor_defaults": {
                "default_executor_name": "codex_cli",
                "default_executor_mode": "autonomous",
                "default_model": "inherit_local_codex_default",
                "default_reasoning_effort": "inherit_local_codex_default",
                "executor_labels": {
                    "codex_cli": "Codex CLI",
                    "hermes_agent": "Hermes-Agent",
                },
                "executor_statuses": {
                    "codex_cli": "default",
                    "hermes_agent": "experimental",
                },
                "chat_completion_only_executor_forbidden": True,
                "hermes_agent_requires_full_agent_loop": True,
                "current_backend_chain": [
                    "med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist",
                    "med_deepscientist CodexRunner -> codex exec autonomous agent loop",
                ],
                "optional_executor_proofs": [
                    {
                        "executor_kind": "hermes_native_proof",
                        "entrypoint": "MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation",
                        "requires_full_agent_loop": True,
                        "default_model": "inherit_local_hermes_default",
                        "default_reasoning_effort": "inherit_local_hermes_default",
                    }
                ],
            },
            "phase2_user_product_loop": phase2_user_product_loop,
            "product_entry_guardrails": product_entry_guardrails,
            "phase3_clearance_lane": phase3_clearance_lane,
            "phase4_backend_deconstruction": phase4_backend_deconstruction,
            "phase5_platform_target": phase5_platform_target,
        },
    )
    validate_product_entry_manifest_contract(payload)
    return payload


def build_skill_catalog(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    manifest = build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    skill_catalog = dict(manifest.get("skill_catalog") or {})
    if not skill_catalog:
        raise ValueError("product entry manifest 缺少 skill_catalog。")
    recommended_shell = _non_empty_text(manifest.get("recommended_shell"))
    if recommended_shell is not None:
        skill_catalog["recommended_shell"] = recommended_shell
    recommended_command = _non_empty_text(manifest.get("recommended_command"))
    if recommended_command is not None:
        skill_catalog["recommended_command"] = recommended_command
    skill_catalog["manifest_command"] = (
        f"{_command_prefix(profile_ref)} product-entry-manifest --profile {_profile_arg(profile_ref)} --format json"
    )
    return skill_catalog


def render_product_entry_manifest_markdown(payload: dict[str, Any]) -> str:
    workspace_locator = dict(payload.get("workspace_locator") or {})
    repo_mainline = dict(payload.get("repo_mainline") or {})
    product_entry_shell = dict(payload.get("product_entry_shell") or {})
    shared_handoff = dict(payload.get("shared_handoff") or {})
    gateway_interaction_contract = dict(payload.get("gateway_interaction_contract") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    product_entry_guardrails = dict(payload.get("product_entry_guardrails") or {})
    phase3_clearance_lane = dict(payload.get("phase3_clearance_lane") or {})
    phase4_backend_deconstruction = dict(payload.get("phase4_backend_deconstruction") or {})
    phase5_platform_target = dict(payload.get("phase5_platform_target") or {})
    single_project_boundary = dict(payload.get("single_project_boundary") or {})
    capability_owner_boundary = dict(payload.get("capability_owner_boundary") or {})
    lines = [
        "# Product Entry Manifest",
        "",
        f"- manifest 类型: `{payload.get('manifest_kind')}`",
        f"- schema 引用: `{payload.get('schema_ref')}`",
        f"- 目标域: `{payload.get('target_domain_id')}`",
        f"- profile 名称: `{workspace_locator.get('profile_name')}`",
        f"- workspace 根目录: `{workspace_locator.get('workspace_root')}`",
        f"- 当前 program phase: `{repo_mainline.get('current_program_phase_id')}`",
        f"- 当前主线阶段: `{repo_mainline.get('current_stage_id')}`",
        f"- 程序摘要: {repo_mainline.get('summary') or 'none'}",
        f"- 前台入口归属: `{gateway_interaction_contract.get('frontdoor_owner') or 'none'}`",
        f"- 交互模式: {_user_interaction_mode_label(gateway_interaction_contract.get('user_interaction_mode'))}",
        "",
        "## Product Entry Shell",
        "",
    ]
    for name, item in product_entry_shell.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
    lines.extend([""] + _render_single_project_boundary_markdown_lines(single_project_boundary) + [""])
    lines.extend(_render_capability_owner_boundary_markdown_lines(capability_owner_boundary) + [""])
    lines.extend(["", "## Operator Loop Actions", ""])
    for name, item in (payload.get("operator_loop_actions") or {}).items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
    lines.extend(["", "## Shared Handoff", ""])
    for name, item in shared_handoff.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command')}`")
    lines.extend(["", "## Phase 2 User Loop", ""])
    lines.append(f"- program phase 摘要: {phase2_user_product_loop.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 单一路径 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Guardrails", ""])
    lines.append(f"- 当前摘要: {product_entry_guardrails.get('summary') or 'none'}")
    for item in product_entry_guardrails.get("guardrail_classes") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('guardrail_id')}`: `{item.get('recommended_command') or 'none'}`"
        )
    lines.extend(["", "## Phase 3 Clearance", ""])
    lines.append(f"- 清障重点: {phase3_clearance_lane.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase3_clearance_lane.get('recommended_command') or 'none'}`")
    for item in phase3_clearance_lane.get("clearance_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    for item in phase3_clearance_lane.get("clearance_loop") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 清障步骤 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Phase 4 Deconstruction", ""])
    for item in phase4_backend_deconstruction.get("substrate_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    lines.extend([""])
    lines.extend(_render_phase5_platform_target_markdown_lines(phase5_platform_target))
    lines.extend(["", "## Remaining Gaps", ""])
    remaining_gaps = list(payload.get("remaining_gaps") or [])
    if remaining_gaps:
        lines.extend(f"- {item}" for item in remaining_gaps)
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def render_skill_catalog_markdown(payload: dict[str, Any]) -> str:
    skills = [dict(item) for item in (payload.get("skills") or []) if isinstance(item, Mapping)]
    lines = [
        "# Skill Catalog",
        "",
        f"- surface kind: `{payload.get('surface_kind') or 'none'}`",
        f"- summary: {payload.get('summary') or 'none'}",
        "",
        "## Skills",
        "",
    ]
    if not skills:
        lines.append("- 当前没有 skill descriptor。")
    for skill in skills:
        lines.append(f"- `{skill.get('skill_id') or 'unknown'}`: {skill.get('description') or 'none'}")
        lines.append(f"  - target surface: `{skill.get('target_surface_kind') or 'none'}`")
        lines.append(f"  - command: `{skill.get('command') or 'none'}`")
    command_contracts = [dict(item) for item in (payload.get("command_contracts") or []) if isinstance(item, Mapping)]
    lines.extend(["", "## Command Contracts", ""])
    if not command_contracts:
        lines.append("- 当前没有 command contract。")
    for contract in command_contracts:
        required_fields = ", ".join(contract.get("required_fields") or []) or "none"
        optional_fields = ", ".join(contract.get("optional_fields") or []) or "none"
        lines.append(f"- `{contract.get('command') or 'unknown'}`")
        lines.append(f"  - required: {required_fields}")
        lines.append(f"  - optional: {optional_fields}")
    return "\n".join(lines)


def build_product_frontdesk(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_product_entry_manifest_fn = _controller_override("build_product_entry_manifest", build_product_entry_manifest)
    read_workspace_cockpit_fn = _controller_override("read_workspace_cockpit", read_workspace_cockpit)
    build_family_product_frontdesk_from_manifest = _controller_override(
        "_build_shared_family_product_frontdesk_from_manifest",
        _build_shared_family_product_frontdesk_from_manifest,
    )
    validate_product_frontdesk_contract = _controller_override(
        "_validate_product_frontdesk_contract",
        _validate_product_frontdesk_contract,
    )
    manifest = build_product_entry_manifest_fn(
        profile=profile,
        profile_ref=profile_ref,
    )
    workspace_cockpit = read_workspace_cockpit_fn(
        profile=profile,
        profile_ref=profile_ref,
    )
    product_entry_shell = dict(manifest.get("product_entry_shell") or {})
    shared_handoff = dict(manifest.get("shared_handoff") or {})
    product_entry_preflight = dict(manifest.get("product_entry_preflight") or {})
    product_entry_quickstart = dict(manifest.get("product_entry_quickstart") or {})
    workspace_operator_brief = dict(workspace_cockpit.get("operator_brief") or {})
    workspace_attention_queue = list(workspace_cockpit.get("attention_queue") or [])
    top_attention = dict(workspace_attention_queue[0] or {}) if workspace_attention_queue else {}
    top_attention_status_card = dict(top_attention.get("operator_status_card") or {})
    single_project_boundary = _validate_single_project_boundary(
        _single_project_boundary_payload(manifest.get("single_project_boundary")),
        context="product_frontdesk.source.single_project_boundary",
    )
    capability_owner_boundary = _validate_capability_owner_boundary(
        _capability_owner_boundary_payload(manifest.get("capability_owner_boundary")),
        context="product_frontdesk.source.capability_owner_boundary",
    )
    if not bool(product_entry_preflight.get("ready_to_try_now")):
        operator_brief = {
            "surface_kind": "product_frontdesk_operator_brief",
            "verdict": "preflight_blocked",
            "summary": _non_empty_text(product_entry_preflight.get("summary"))
            or "当前还没有通过前置检查，先不要直接进入研究主线。",
            "should_intervene_now": True,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "preflight_check",
            "recommended_command": _non_empty_text(product_entry_preflight.get("recommended_check_command")),
        }
    elif _non_empty_text(workspace_operator_brief.get("verdict")) == "attention_required":
        operator_brief = {
            "surface_kind": "product_frontdesk_operator_brief",
            "verdict": "attention_required",
            "summary": _operator_status_summary(top_attention_status_card)
            or _non_empty_text((top_attention.get("quality_repair_followthrough") or {}).get("summary"))
            or _gate_clearing_followthrough_summary(top_attention.get("gate_clearing_followthrough"))
            or _non_empty_text(workspace_operator_brief.get("summary"))
            or "当前 workspace 已有需要优先处理的 attention item。",
            "should_intervene_now": True,
            "focus_scope": _non_empty_text(workspace_operator_brief.get("focus_scope")) or "workspace",
            "focus_study_id": _non_empty_text(workspace_operator_brief.get("focus_study_id")),
            "recommended_step_id": _non_empty_text(top_attention.get("recommended_step_id"))
            or _non_empty_text(workspace_operator_brief.get("recommended_step_id"))
            or "open_workspace_cockpit",
            "recommended_command": _non_empty_text(top_attention.get("recommended_command"))
            or _non_empty_text(workspace_operator_brief.get("recommended_command"))
            or _non_empty_text((manifest.get("summary") or {}).get("recommended_command")),
        }
        current_focus = _non_empty_text(top_attention_status_card.get("current_focus")) or _non_empty_text(
            workspace_operator_brief.get("current_focus")
        ) or _quality_repair_followthrough_focus(top_attention) or _gate_clearing_followthrough_focus(top_attention) or _same_line_route_focus(top_attention) or _quality_execution_focus(top_attention) or _quality_review_followthrough_focus(top_attention) or _autonomy_soak_focus(top_attention)
        if current_focus is not None:
            operator_brief["current_focus"] = current_focus
        next_confirmation_signal = _non_empty_text(top_attention_status_card.get("next_confirmation_signal")) or _non_empty_text(
            workspace_operator_brief.get("next_confirmation_signal")
        )
        if next_confirmation_signal is not None:
            operator_brief["next_confirmation_signal"] = next_confirmation_signal
    elif _non_empty_text(workspace_operator_brief.get("verdict")) == "ready_for_task":
        operator_brief = {
            "surface_kind": "product_frontdesk_operator_brief",
            "verdict": "ready_for_task",
            "summary": "当前 workspace 已 ready，下一步先给目标 study 下任务，再启动研究。",
            "should_intervene_now": False,
            "focus_scope": "workspace",
            "focus_study_id": None,
            "recommended_step_id": "submit_task",
            "recommended_command": _non_empty_text(workspace_operator_brief.get("recommended_command"))
            or _non_empty_text(
                ((product_entry_quickstart.get("steps") or [None, {}])[1] or {}).get("command")
            ),
        }
    else:
        operator_brief = {
            "surface_kind": "product_frontdesk_operator_brief",
            "verdict": "monitor_only",
            "summary": _non_empty_text(workspace_operator_brief.get("summary"))
            or "当前先进入 workspace cockpit，持续看进度、告警和恢复建议。",
            "should_intervene_now": bool(workspace_operator_brief.get("should_intervene_now")),
            "focus_scope": _non_empty_text(workspace_operator_brief.get("focus_scope")) or "workspace",
            "focus_study_id": _non_empty_text(workspace_operator_brief.get("focus_study_id")),
            "recommended_step_id": "open_workspace_cockpit",
            "recommended_command": _non_empty_text((manifest.get("summary") or {}).get("recommended_command")),
        }
        current_focus = _non_empty_text(workspace_operator_brief.get("current_focus")) or _quality_review_followthrough_focus(
            workspace_operator_brief
        ) or _quality_repair_followthrough_focus(workspace_operator_brief) or _gate_clearing_followthrough_focus(workspace_operator_brief) or _same_line_route_focus(workspace_operator_brief) or _autonomy_soak_focus(workspace_operator_brief)
        if current_focus is not None:
            operator_brief["current_focus"] = current_focus

    payload = build_family_product_frontdesk_from_manifest(
        recommended_action="inspect_or_prepare_research_loop",
        product_entry_manifest=manifest,
        shell_aliases={
            "frontdesk": "product_frontdesk",
            "cockpit": "workspace_cockpit",
            "submit_task": "submit_study_task",
            "launch_study": "launch_study",
            "study_progress": "study_progress",
            "mainline_status": "mainline_status",
            "mainline_phase": "mainline_phase",
        },
        schema_ref=PRODUCT_FRONTDESK_SCHEMA_REF,
        notes=[
            "This frontdesk surface is a controller-owned front door over the current research product-entry shell.",
            "It does not claim that a mature standalone medical frontend is already landed.",
            "It does not include the display / paper-figure asset line.",
        ],
        extra_payload={
            "schema_version": SCHEMA_VERSION,
            "single_project_boundary": single_project_boundary,
            "capability_owner_boundary": capability_owner_boundary,
            "executor_defaults": dict(manifest.get("executor_defaults") or {}),
            "runtime_inventory": dict(manifest.get("runtime_inventory") or {}),
            "task_lifecycle": dict(manifest.get("task_lifecycle") or {}),
            "skill_catalog": dict(manifest.get("skill_catalog") or {}),
            "automation": dict(manifest.get("automation") or {}),
            "phase2_user_product_loop": dict(manifest.get("phase2_user_product_loop") or {}),
            "product_entry_guardrails": dict(manifest.get("product_entry_guardrails") or {}),
            "phase3_clearance_lane": dict(manifest.get("phase3_clearance_lane") or {}),
            "phase4_backend_deconstruction": dict(manifest.get("phase4_backend_deconstruction") or {}),
            "operator_brief": operator_brief,
            "workspace_operator_brief": workspace_operator_brief,
            "workspace_attention_queue_preview": list((workspace_cockpit.get("attention_queue") or []))[:3],
            "phase5_platform_target": dict(manifest.get("phase5_platform_target") or {}),
        },
    )
    validate_product_frontdesk_contract(payload)
    return payload


def render_product_frontdesk_markdown(payload: dict[str, Any]) -> str:
    entry_surfaces = dict(payload.get("entry_surfaces") or {})
    gateway_interaction_contract = dict(payload.get("gateway_interaction_contract") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    product_entry_guardrails = dict(payload.get("product_entry_guardrails") or {})
    phase3_clearance_lane = dict(payload.get("phase3_clearance_lane") or {})
    phase4_backend_deconstruction = dict(payload.get("phase4_backend_deconstruction") or {})
    phase5_platform_target = dict(payload.get("phase5_platform_target") or {})
    single_project_boundary = dict(payload.get("single_project_boundary") or {})
    capability_owner_boundary = dict(payload.get("capability_owner_boundary") or {})
    operator_brief = dict(payload.get("operator_brief") or {})
    quickstart = dict(payload.get("product_entry_quickstart") or {})
    workspace_operator_brief = dict(payload.get("workspace_operator_brief") or {})
    lines = [
        "# Product Frontdesk",
        "",
        f"- 目标域: `{payload.get('target_domain_id')}`",
        f"- 契约引用: `{payload.get('schema_ref') or 'none'}`",
        f"- 前台归属: `{gateway_interaction_contract.get('frontdoor_owner') or 'none'}`",
        f"- 交互模式: `{gateway_interaction_contract.get('user_interaction_mode') or 'none'}`",
        f"- 前台入口命令: `{(payload.get('summary') or {}).get('frontdesk_command') or 'none'}`",
        f"- 推荐继续命令: `{(payload.get('summary') or {}).get('recommended_command') or 'none'}`",
        f"- 当前 loop 命令: `{(payload.get('summary') or {}).get('operator_loop_command') or 'none'}`",
        "",
        "## Now",
        "",
    ]
    if operator_brief:
        lines.append(f"- 当前状态: {_operator_verdict_label(operator_brief.get('verdict'))}")
        lines.append(f"- 当前判断: {operator_brief.get('summary') or 'none'}")
        lines.append(f"- 是否需要立刻介入: {'是' if operator_brief.get('should_intervene_now') else '否'}")
        lines.append(f"- 推荐动作: `{operator_brief.get('recommended_step_id') or 'none'}`")
        lines.append(f"- 推荐命令: `{operator_brief.get('recommended_command') or 'none'}`")
        if operator_brief.get("focus_study_id"):
            lines.append(f"- 聚焦 study: `{operator_brief.get('focus_study_id')}`")
        if operator_brief.get("current_focus"):
            lines.append(f"- 当前清障重点: {operator_brief.get('current_focus')}")
        if operator_brief.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_brief.get('next_confirmation_signal')}")
    else:
        lines.append("- 当前还没有 frontdesk operator brief。")
    lines.extend([""] + _render_single_project_boundary_markdown_lines(single_project_boundary) + [""])
    lines.extend(_render_capability_owner_boundary_markdown_lines(capability_owner_boundary) + [""])
    lines.extend([
        "",
        "## Single Path",
        "",
    ])
    for step in quickstart.get("steps") or []:
        if not isinstance(step, dict):
            continue
        lines.append(
            f"- `{step.get('step_id')}`: `{step.get('command') or 'none'}` {step.get('summary') or ''}"
        )
    lines.extend([
        "",
        "## Product Entry Overview",
        "",
        f"- 总览判断: `{(payload.get('product_entry_overview') or {}).get('summary') or 'none'}`",
        f"- 启动提示: `{(payload.get('product_entry_start') or {}).get('summary') or 'none'}`",
        f"- 启动后恢复命令: `{((payload.get('product_entry_start') or {}).get('resume_surface') or {}).get('command') or 'none'}`",
        f"- 前置检查已通过: `{'是' if (payload.get('product_entry_preflight') or {}).get('ready_to_try_now') else '否'}`",
        f"- 前置检查命令: `{(payload.get('product_entry_preflight') or {}).get('recommended_check_command') or 'none'}`",
        f"- 查看进度命令: `{((payload.get('product_entry_overview') or {}).get('progress_surface') or {}).get('command') or 'none'}`",
        f"- 恢复当前 loop 命令: `{((payload.get('product_entry_overview') or {}).get('resume_surface') or {}).get('command') or 'none'}`",
        "",
        "## Workspace Preview",
        "",
    ])
    if workspace_operator_brief:
        lines.append(
            f"- 当前 workspace 状态: {_operator_verdict_label(workspace_operator_brief.get('verdict'))}"
        )
        lines.append(f"- 当前 workspace 判断: {workspace_operator_brief.get('summary') or 'none'}")
        lines.append(
            f"- 当前 workspace 推荐命令: `{workspace_operator_brief.get('recommended_command') or 'none'}`"
        )
    else:
        lines.append("- 当前没有 workspace preview。")
    for item in payload.get("workspace_attention_queue_preview") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 当前关注项: {item.get('title') or '未命名关注项'}")
        lines.append(f"- 处理命令: `{item.get('recommended_command') or 'none'}`")
        autonomy_contract = dict(item.get("autonomy_contract") or {})
        if autonomy_contract.get("summary"):
            lines.append(f"- 自治合同: {autonomy_contract.get('summary')}")
        autonomy_soak_status = dict(item.get("autonomy_soak_status") or {})
        if autonomy_soak_status.get("summary"):
            lines.append(f"- 自治 Proof / Soak: {autonomy_soak_status.get('summary')}")
        quality_closure_truth = dict(item.get("quality_closure_truth") or {})
        if quality_closure_truth.get("summary"):
            lines.append(f"- 质量闭环: {quality_closure_truth.get('summary')}")
        quality_execution_lane = dict(item.get("quality_execution_lane") or {})
        if quality_execution_lane.get("summary"):
            lines.append(f"- 质量执行线: {quality_execution_lane.get('summary')}")
        same_line_route_truth_preview = _same_line_route_truth_preview(item.get("same_line_route_truth"))
        if same_line_route_truth_preview:
            lines.append(f"- 同线路由: {same_line_route_truth_preview}")
        quality_review_loop_preview = _quality_review_loop_preview(item.get("quality_review_loop"))
        if quality_review_loop_preview:
            lines.append(f"- 质量评审闭环: {quality_review_loop_preview}")
        quality_review_followthrough_preview = _quality_review_followthrough_preview(
            item.get("quality_review_followthrough")
        )
        if quality_review_followthrough_preview:
            lines.append(f"- 质量复评跟进: {quality_review_followthrough_preview}")
        quality_repair_followthrough_preview = _quality_repair_followthrough_preview(
            item.get("quality_repair_followthrough")
        )
        if quality_repair_followthrough_preview:
            lines.append(f"- quality-repair 跟进: {quality_repair_followthrough_preview}")
        gate_clearing_followthrough_preview = _gate_clearing_followthrough_preview(
            item.get("gate_clearing_followthrough")
        )
        if gate_clearing_followthrough_preview:
            lines.append(f"- gate-clearing 跟进: {gate_clearing_followthrough_preview}")
        restore_point = dict(autonomy_contract.get("restore_point") or {})
        if restore_point.get("summary"):
            lines.append(f"- 恢复点: {restore_point.get('summary')}")
        operator_status_card = dict(item.get("operator_status_card") or {})
        if operator_status_card.get("handling_state"):
            lines.append(f"- 处理状态: `{operator_status_card.get('handling_state')}`")
        if operator_status_card.get("user_visible_verdict"):
            lines.append(f"- 当前处理结论: {operator_status_card.get('user_visible_verdict')}")
        if operator_status_card.get("next_confirmation_signal"):
            lines.append(f"- 下一确认信号: {operator_status_card.get('next_confirmation_signal')}")
    lines.extend([
        "",
        "## Phase 2 User Loop",
        "",
    ])
    lines.append(f"- program phase 摘要: {phase2_user_product_loop.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`")
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 单一路径 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend([
        "",
        "## Guardrails",
        "",
    ])
    guardrail_classes = list(product_entry_guardrails.get("guardrail_classes") or [])
    if not guardrail_classes:
        lines.append("- `workspace_supervision_gap`: `none`")
    for item in guardrail_classes:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('guardrail_id')}`: `{item.get('recommended_command') or 'none'}`"
        )
    lines.extend(
        [
            "",
            "## Phase 3 Clearance",
            "",
        ]
    )
    lines.append(f"- 清障重点: {phase3_clearance_lane.get('summary') or 'none'}")
    lines.append(f"- 推荐动作: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`")
    lines.append(f"- 推荐命令: `{phase3_clearance_lane.get('recommended_command') or 'none'}`")
    clearance_targets = list(phase3_clearance_lane.get("clearance_targets") or [])
    if not clearance_targets:
        lines.append("- `external_runtime_contract`: `none`")
    for item in clearance_targets:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    clearance_loop = list(phase3_clearance_lane.get("clearance_loop") or [])
    if not clearance_loop:
        lines.append("- 清障步骤 `refresh_supervision`: `none`")
    for item in clearance_loop:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 清障步骤 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    lines.extend(
        [
            "",
            "## Phase 4 Deconstruction",
            "",
        ]
    )
    substrate_targets = list(phase4_backend_deconstruction.get("substrate_targets") or [])
    if not substrate_targets:
        lines.append("- `session_run_watch_recovery`: none")
    for item in substrate_targets:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    lines.extend([""])
    lines.extend(_render_phase5_platform_target_markdown_lines(phase5_platform_target))
    lines.extend(["", "## Entry Surfaces", ""])
    for name, item in entry_surfaces.items():
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{name}`: `{item.get('command') or 'none'}`")
    lines.append("")
    return "\n".join(lines)


def build_product_entry_preflight(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_doctor_report_fn = _controller_override("build_doctor_report", build_doctor_report)
    doctor_report = build_doctor_report_fn(profile)
    return _build_product_entry_preflight(
        doctor_report=doctor_report,
        profile_ref=profile_ref,
    )


def build_product_entry_start(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    build_product_entry_manifest_fn = _controller_override("build_product_entry_manifest", build_product_entry_manifest)
    manifest = build_product_entry_manifest_fn(
        profile=profile,
        profile_ref=profile_ref,
    )
    return dict(manifest.get("product_entry_start") or {})


def render_product_entry_preflight_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Product Entry Preflight",
        "",
        f"- 当前可直接尝试: {_bool_label(payload.get('ready_to_try_now'))}",
        f"- 当前摘要: {payload.get('summary') or 'none'}",
        f"- 前置检查命令: `{payload.get('recommended_check_command') or 'none'}`",
        f"- 推荐启动命令: `{payload.get('recommended_start_command') or 'none'}`",
        "",
        "## Checks",
        "",
    ]
    checks = list(payload.get("checks") or [])
    if checks:
        for check in checks:
            if not isinstance(check, dict):
                continue
            lines.append(
                "- "
                + f"`{check.get('check_id')}` "
                + f"[{_check_status_label(check.get('status'))}] "
                + f"({'阻塞项' if check.get('blocking') else '非阻塞项'}) "
                + f"{check.get('summary') or ''} "
                + f"`{check.get('command') or 'none'}`"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def render_product_entry_start_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Product Entry Start",
        "",
        f"- 当前摘要: {payload.get('summary') or 'none'}",
        f"- 建议入口: {_start_mode_label(payload.get('recommended_mode_id'))}",
        f"- 恢复入口: {_surface_kind_label(((payload.get('resume_surface') or {}).get('surface_kind')))}",
        "",
        "## 可用入口",
        "",
    ]
    modes = list(payload.get("modes") or [])
    if modes:
        for mode in modes:
            if not isinstance(mode, dict):
                continue
            lines.append(
                "- "
                + f"{_start_mode_label(mode.get('mode_id'))}: "
                + f"`{mode.get('command') or 'none'}` "
                + f"{mode.get('summary') or ''}"
            )
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
