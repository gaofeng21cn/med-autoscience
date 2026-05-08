from __future__ import annotations

from med_autoscience.controllers import mainline_status

from . import shared as _shared
from . import automation_surfaces as _automation_surfaces
from . import family_lifecycle_surfaces as _family_lifecycle_surfaces
from .guarded_workflow_steps import build_guarded_phase2_workflow_steps

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_automation_surfaces)
_module_reexport(_family_lifecycle_surfaces)

_build_backend_deconstruction_lane = mainline_status._build_backend_deconstruction_lane


def _build_phase5_platform_target() -> dict[str, Any]:
    payload = mainline_status.read_mainline_status()
    source = payload.get("platform_target")
    if not isinstance(source, Mapping):
        source = mainline_status._platform_target()
    source_payload = dict(source)
    source_landing_sequence = [
        dict(item)
        for item in source_payload.get("landing_sequence") or []
        if isinstance(item, Mapping)
    ]
    normalized_landing_sequence = [
        _build_shared_program_sequence_step(
            step_id=str(item.get("step_id") or ""),
            phase_id=str(item.get("phase_id") or ""),
            status=str(item.get("status") or ""),
            summary=str(item.get("summary") or ""),
            title=_non_empty_text(item.get("title")),
        )
        for item in source_landing_sequence
    ]
    build_platform_target = _controller_override("_build_shared_platform_target", _build_shared_platform_target)
    return build_platform_target(
        summary=str(source_payload.get("summary") or ""),
        sequence_scope=str(source_payload.get("sequence_scope") or ""),
        current_step_id=str(source_payload.get("current_step_id") or ""),
        current_readiness_summary=str(source_payload.get("current_readiness_summary") or ""),
        north_star_topology=dict(source_payload.get("north_star_topology") or {}),
        target_internal_modules=list(source_payload.get("target_internal_modules") or []),
        landing_sequence=normalized_landing_sequence,
        completed_step_ids=list(source_payload.get("completed_step_ids") or []),
        remaining_step_ids=list(source_payload.get("remaining_step_ids") or []),
        promotion_gates=list(source_payload.get("promotion_gates") or []),
        recommended_phase_command=str(source_payload.get("recommended_phase_command") or ""),
        land_now=list(_normalized_strings(source_payload.get("land_now") or [])),
        not_yet=list(_normalized_strings(source_payload.get("not_yet") or [])),
    )


def _render_phase5_platform_target_markdown_lines(phase5_platform_target: Mapping[str, Any]) -> list[str]:
    current_step_id = _non_empty_text(phase5_platform_target.get("current_step_id")) or "stabilize_user_product_loop"
    north_star_topology = dict(phase5_platform_target.get("north_star_topology") or {})
    monorepo_status = _non_empty_text(north_star_topology.get("monorepo_status")) or "no_history_absorb_landed"
    lines = [
        "## Platform Target",
        "",
        f"- 当前摘要: {phase5_platform_target.get('summary') or 'none'}",
        f"- 当前序列范围: {_phase5_sequence_scope_label(phase5_platform_target.get('sequence_scope'))}",
        f"- 当前步骤: `{current_step_id}`",
        f"- 当前就绪判断: {phase5_platform_target.get('current_readiness_summary') or 'none'}",
        f"- monorepo 目标状态: {_phase5_monorepo_status_label(monorepo_status)}",
        f"- 推荐 phase 命令: `{phase5_platform_target.get('recommended_phase_command') or 'none'}`",
        "",
        "## Monorepo Sequence",
        "",
    ]
    landing_sequence = list(phase5_platform_target.get("landing_sequence") or [])
    if landing_sequence:
        for item in landing_sequence:
            if not isinstance(item, Mapping):
                continue
            lines.append(
                f"- `{item.get('step_id')}` [{item.get('status')}] / `{item.get('phase_id')}`: {item.get('summary') or 'none'}"
            )
    else:
        lines.append("- none")
    return lines


def _build_phase2_user_product_loop(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    prefix = _command_prefix(profile_ref)
    profile_arg = _profile_arg(profile_ref)
    lane = mainline_status.build_phase2_user_product_loop_lane(
        entry_status_command=f"{prefix} product-entry-status --profile {profile_arg}",
        workspace_cockpit_command=_json_surface_command(
            f"{prefix} workspace-cockpit --profile {profile_arg}"
        ),
        submit_task_command=(
            f"{prefix} submit-study-task --profile {profile_arg} "
            "--study-id <study_id> --task-intent '<task_intent>'"
        ),
        launch_study_command=f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
        study_progress_command=_json_surface_command(
            f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>"
        ),
        controller_decisions_ref=str(
            profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"
        ),
    )
    workflow_command = _json_surface_command(f"{prefix} workspace-cockpit --profile {profile_arg}")
    lane["workflow_steps"] = build_guarded_phase2_workflow_steps(workflow_command=workflow_command)
    return lane


def _build_phase3_clearance_lane(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    prefix = _command_prefix(profile_ref)
    profile_arg = _profile_arg(profile_ref)
    doctor_command = f"{prefix} doctor --profile {profile_arg}"
    hermes_runtime_check_command = f"{prefix} hermes-runtime-check --profile {profile_arg}"
    supervisor_service_command = f"{prefix} runtime-supervision-status --profile {profile_arg}"
    refresh_supervision_command = (
        f"{prefix} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {profile_arg} --ensure-study-runtimes --apply"
    )
    launch_study_command = f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>"
    study_progress_command = f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>"
    build_clearance_lane = _controller_override("_build_shared_clearance_lane", _build_shared_clearance_lane)
    return build_clearance_lane(
        surface_kind="phase3_host_clearance_lane",
        summary="Phase 3 只做可选 hosted runtime / 多宿主 proof；MAS 默认运行和诊断已经由 MAS Runtime OS 承接。",
        recommended_step_id="mas_runtime_contract",
        recommended_command=doctor_command,
        clearance_targets=[
            _build_shared_clearance_target(
                target_id="external_runtime_contract",
                title="Check optional hosted runtime contract",
                commands=[
                    doctor_command,
                    hermes_runtime_check_command,
                ],
            ),
            _build_shared_clearance_target(
                target_id="supervisor_service",
                title="Keep MAS workspace supervision online",
                commands=[
                    supervisor_service_command,
                    refresh_supervision_command,
                ],
            ),
            _build_shared_clearance_target(
                target_id="study_recovery_proof",
                title="Prove live study recovery and supervision",
                commands=[
                    launch_study_command,
                    study_progress_command,
                ],
            ),
        ],
        clearance_loop=[
            _build_shared_product_entry_program_step(
                step_id="external_runtime_contract",
                title="确认 optional hosted runtime contract 或 MAS runtime contract ready",
                surface_kind="doctor_runtime_contract",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="hermes_runtime_check",
                title="显式检查 optional Hermes runtime 绑定证据",
                surface_kind="hermes_runtime_check",
                command=hermes_runtime_check_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="supervisor_service",
                title="确认 workspace 定时监管在线",
                surface_kind="workspace_supervisor_service",
                command=supervisor_service_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="refresh_supervision",
                title="刷新 MAS runtime supervision tick",
                surface_kind="runtime_watch_refresh",
                command=refresh_supervision_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="study_recovery_proof",
                title="证明 live study recovery / progress supervision 成立",
                surface_kind="launch_study",
                command=launch_study_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="inspect_study_progress",
                title="读取 study-progress proof",
                surface_kind="study_progress",
                command=study_progress_command,
            ),
        ],
        proof_surfaces=[
            _build_shared_product_entry_program_surface(
                surface_kind="doctor.external_runtime_contract",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="study_runtime_status.autonomous_runtime_notice",
                command=f"{prefix} study-runtime-status --profile {profile_arg} --study-id <study_id>",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="runtime_watch",
                ref=str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_watch" / "latest.json"),
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="runtime_supervision",
                ref=str(profile.studies_root / "<study_id>" / "artifacts" / "runtime_supervision" / "latest.json"),
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="controller_decisions",
                ref=str(profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"),
            ),
        ],
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    )


def _build_phase4_backend_deconstruction() -> dict[str, Any]:
    build_backend_deconstruction_lane = _controller_override(
        "_build_backend_deconstruction_lane",
        mainline_status._build_backend_deconstruction_lane,
    )
    return build_backend_deconstruction_lane(
        summary="Phase 4 只保留 future upstream source intake / historical fixture governance；MDS 不再是 runtime substrate。",
        substrate_targets=[
            _build_shared_program_capability(
                capability_id="session_run_watch_recovery",
                owner="MAS Runtime OS",
                summary="session / run / watch / recovery / scheduling / interruption 默认由 MAS Runtime OS 承接。",
            ),
            _build_shared_program_capability(
                capability_id="backend_generic_runtime_contract",
                owner="MedAutoScience controller boundary",
                summary="controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            ),
        ],
        backend_retained_now=[
            "frozen MedDeepScientist source archive",
            "historical oracle fixtures",
            "explicit legacy restore/import/backend-audit diagnostic",
        ],
        current_backend_chain=[
            "med_autoscience runtime surfaces -> MAS-owned Runtime OS / Artifact OS / Quality OS",
            "historical med_deepscientist fixture/provenance refs only",
        ],
        optional_executor_proofs=[
            {
                "executor_kind": "hermes_agent",
                "entrypoint": "optional hosted runtime adapter",
                "default_model": "inherit_local_hermes_default",
                "default_reasoning_effort": "inherit_local_hermes_default",
            }
        ],
        promotion_rules=[
            "no claim of platform runtime ingest without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "do not restore external MDS as a default runtime dependency",
        ],
        deconstruction_map_ref="program:med_deepscientist_deconstruction_map",
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_4_backend_deconstruction"
        ),
    )


def _build_product_entry_start(
    *,
    product_entry_shell: dict[str, Any],
    operator_loop_actions: dict[str, Any],
    family_orchestration: dict[str, Any],
) -> dict[str, Any]:
    return _build_shared_product_entry_start(
        summary=(
            "先从 MAS research entry_status 进入当前 workspace product entry；"
            "需要新任务时先写 durable study task intake，已有 study 时直接恢复研究运行。"
        ),
        recommended_mode_id="open_product_entry",
        modes=[
            {
                "mode_id": "open_product_entry",
                "title": "打开 MAS 入口状态",
                "command": product_entry_shell["product_entry_status"]["command"],
                "surface_kind": PRODUCT_ENTRY_STATUS_KIND,
                "summary": product_entry_shell["product_entry_status"]["purpose"],
                "requires": [],
            },
            {
                "mode_id": "submit_task",
                "title": "给 study 下 durable 任务",
                "command": product_entry_shell["submit_study_task"]["command"],
                "surface_kind": "study_task_intake",
                "summary": operator_loop_actions["submit_task"]["summary"],
                "requires": list(operator_loop_actions["submit_task"]["requires"]),
            },
            {
                "mode_id": "continue_study",
                "title": "启动或续跑 study",
                "command": product_entry_shell["launch_study"]["command"],
                "surface_kind": "launch_study",
                "summary": operator_loop_actions["continue_study"]["summary"],
                "requires": list(operator_loop_actions["continue_study"]["requires"]),
            },
        ],
        resume_surface=dict(family_orchestration["resume_contract"]),
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
    )


def _build_runtime_inventory_surface(
    *,
    profile: WorkspaceProfile,
    runtime: Mapping[str, Any],
    managed_runtime_contract: Mapping[str, Any],
    product_entry_preflight: Mapping[str, Any],
    operator_loop_surface: Mapping[str, Any],
) -> dict[str, Any]:
    blocking_check_ids = list(product_entry_preflight.get("blocking_check_ids") or [])
    ready_to_try_now = bool(product_entry_preflight.get("ready_to_try_now")) and not blocking_check_ids
    availability = "ready" if ready_to_try_now else "blocked"
    health_status = "healthy" if ready_to_try_now else "attention_required"
    summary = (
        "MAS runtime inventory 已连接 external Hermes runtime，当前可通过 workspace cockpit 持续监管并续跑 study。"
        if ready_to_try_now
        else "MAS runtime inventory 当前存在 blocking preflight，需要先恢复 runtime/监督前置状态。"
    )
    return _build_shared_runtime_inventory(
        summary=summary,
        runtime_owner=str(runtime.get("runtime_owner") or ""),
        domain_owner=str(runtime.get("domain_owner") or ""),
        executor_owner=str(runtime.get("executor_owner") or ""),
        substrate=str(runtime.get("runtime_substrate") or ""),
        availability=availability,
        health_status=health_status,
        status_surface={
            "ref_kind": "workspace_locator",
            "ref": "studies/<study_id>/artifacts/runtime_watch/latest.json",
            "label": "runtime watch event companion",
        },
        attention_surface={
            "ref_kind": "json_pointer",
            "ref": "/operator_loop_surface",
            "label": "workspace cockpit attention surface",
        },
        recovery_surface={
            "ref_kind": "json_pointer",
            "ref": "/managed_runtime_contract/recovery_contract_surface",
            "label": "managed runtime recovery contract surface",
        },
        workspace_binding={
            "workspace_root": str(profile.workspace_root),
            "profile_name": profile.name,
        },
        domain_projection={
            "managed_runtime_backend_id": runtime.get("managed_runtime_backend_id"),
            "managed_runtime_contract": dict(managed_runtime_contract),
            "recommended_loop_surface": operator_loop_surface.get("surface_kind"),
        },
    )


def _build_task_lifecycle_surface(
    *,
    repo_mainline: Mapping[str, Any],
    product_entry_status: Mapping[str, Any],
    product_entry_readiness: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    operator_loop_surface: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
) -> dict[str, Any]:
    program_id = _non_empty_text(repo_mainline.get("program_id")) or TARGET_DOMAIN_ID
    stage_id = _non_empty_text(repo_mainline.get("current_stage_id")) or _non_empty_text(
        repo_mainline.get("current_program_phase_id")
    ) or "unknown-stage"
    lifecycle_status = _non_empty_text(repo_mainline.get("current_stage_status")) or _non_empty_text(
        repo_mainline.get("current_program_phase_status")
    ) or "unknown"
    lifecycle_summary = _non_empty_text(product_entry_status.get("summary")) or "MAS product entry lane is active."
    checkpoint_summary = _build_shared_checkpoint_summary(
        status="ready" if bool(product_entry_readiness.get("good_to_use_now")) else "monitoring_required",
        summary=(
            "当前 lane 已进入可执行状态，继续通过 workspace cockpit 和 study progress 维持监督与恢复闭环。"
            if bool(product_entry_readiness.get("usable_now"))
            else "当前 lane 需要先完成 blocking preflight 后再恢复常规执行。"
        ),
        checkpoint_id=f"{program_id}:{stage_id}",
        lineage_ref=dict(family_orchestration.get("checkpoint_lineage_surface") or {}),
        verification_ref=dict(family_orchestration.get("event_envelope_surface") or {}),
    )
    return _build_shared_task_lifecycle(
        task_kind="mas_product_entry_mainline",
        task_id=f"{program_id}:{stage_id}",
        status=lifecycle_status,
        summary=lifecycle_summary,
        progress_surface={
            "surface_kind": "workspace_cockpit",
            "summary": "读取 workspace attention queue、监督在线态与研究入口回路。",
            "command": str(operator_loop_surface.get("command") or ""),
            "step_id": "inspect_workspace_inbox",
            "locator_fields": ["profile_ref"],
        },
        resume_surface={
            "surface_kind": "launch_study",
            "summary": "按 study_id 启动或续跑当前研究。",
            "command": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            "step_id": "continue_study",
            "locator_fields": ["study_id"],
        },
        checkpoint_summary=checkpoint_summary,
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
        domain_projection={
            "current_program_phase_id": repo_mainline.get("current_program_phase_id"),
            "recommended_loop_surface": operator_loop_surface.get("surface_kind"),
            "recommended_loop_command": operator_loop_surface.get("command"),
        },
    )


def _build_session_continuity_surface(
    *,
    runtime: Mapping[str, Any],
    product_entry_preflight: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
    task_lifecycle: Mapping[str, Any],
    study_runtime_status_command: str,
) -> dict[str, Any]:
    blocking_check_ids = list(product_entry_preflight.get("blocking_check_ids") or [])
    ready_to_try_now = bool(product_entry_preflight.get("ready_to_try_now")) and not blocking_check_ids
    checkpoint_summary = dict(task_lifecycle.get("checkpoint_summary") or {})
    return _build_shared_session_continuity(
        summary=(
            "MAS session continuity 指针已就绪；恢复入口与进度/工件真相仍以 study-local durable surfaces 为 authority。"
            if ready_to_try_now
            else "MAS session continuity 当前被 preflight blocking；仍可按指针定位 durable truth，但恢复前先清障。"
        ),
        domain_agent_id="mas",
        runtime_owner=str(runtime.get("runtime_owner") or ""),
        domain_owner=str(runtime.get("domain_owner") or ""),
        executor_owner=str(runtime.get("executor_owner") or ""),
        status="ready" if ready_to_try_now else "blocked",
        progress_surface={
            "surface_kind": "study_progress",
            "summary": "读取 study progress projection（只读投影，不替代 runtime/controller 真相）。",
            "command": str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
            "step_id": "inspect_progress",
            "locator_fields": ["profile_ref", "study_id"],
        },
        artifact_surface={
            "surface_kind": "study_runtime_status",
            "summary": "读取 runtime 恢复合同与运行态，必要时决定接管/重启。",
            "command": study_runtime_status_command,
            "step_id": "inspect_runtime_status",
            "locator_fields": ["profile_ref", "study_id"],
        },
        restore_surface={
            "surface_kind": "launch_study",
            "summary": "按 study_id 启动或续跑当前研究运行（restore 指针）。",
            "command": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            "step_id": "continue_study",
            "locator_fields": ["profile_ref", "study_id"],
        },
        checkpoint_summary=checkpoint_summary if checkpoint_summary else None,
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
        domain_projection={
            "runtime_supervision_path_template": "studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json",
            "publication_eval_path_template": "studies/<study_id>/artifacts/publication_eval/latest.json",
            "controller_decision_path_template": "studies/<study_id>/artifacts/controller_decisions/latest.json",
        },
    )


def _build_progress_projection_surface(
    *,
    profile: WorkspaceProfile,
    repo_mainline: Mapping[str, Any],
    product_entry_status: Mapping[str, Any],
    product_entry_preflight: Mapping[str, Any],
    product_entry_readiness: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    operator_loop_surface: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
    study_runtime_status_command: str,
) -> dict[str, Any]:
    headline = _non_empty_text(product_entry_status.get("summary")) or "MAS 当前保持 repo-owned product entry continuity。"
    next_step = _non_empty_text(operator_loop_surface.get("command")) or "none"
    latest_update = _non_empty_text(repo_mainline.get("current_stage_summary")) or _non_empty_text(
        repo_mainline.get("current_program_phase_summary")
    ) or headline
    blocking_check_ids = list(product_entry_preflight.get("blocking_check_ids") or [])
    attention_items = list(product_entry_status.get("next_focus") or [])
    if blocking_check_ids:
        attention_items.extend(f"preflight_blocking::{item}" for item in blocking_check_ids)
    return _build_shared_progress_projection(
        headline=headline,
        latest_update=latest_update,
        next_step=next_step,
        status_summary=_non_empty_text(product_entry_readiness.get("summary")) or "none",
        current_status=_non_empty_text(product_entry_readiness.get("verdict")) or "runtime_ready_not_standalone_product",
        runtime_status="ready" if bool(product_entry_preflight.get("ready_to_try_now")) and not blocking_check_ids else "blocked",
        progress_surface={
            "surface_kind": "workspace_cockpit",
            "summary": "读取 workspace attention queue 与监督在线态（progress 指针）。",
            "command": next_step,
            "step_id": "open_loop",
            "locator_fields": ["profile_ref"],
        },
        artifact_surface={
            "surface_kind": "study_runtime_status",
            "summary": "按 study_id 读取 runtime 恢复合同与运行态（artifact/restore 辅助指针）。",
            "command": study_runtime_status_command,
            "step_id": "inspect_runtime_status",
            "locator_fields": ["profile_ref", "study_id"],
        },
        inspect_paths=[str(profile.workspace_root), str(profile.runtime_root), "studies/<study_id>/artifacts"],
        attention_items=attention_items,
        human_gate_ids=_collect_family_human_gate_ids(family_orchestration),
        domain_projection={
            "recommended_restore_command": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            "recommended_progress_command": str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
            "research_runtime_control_projection": _build_research_runtime_control_projection(
                resume_command=str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
                check_progress_command=str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
                check_runtime_status_command=study_runtime_status_command,
                surface_kind="research_runtime_control_projection",
            ),
        },
    )


from .program_runtime_surfaces import _build_research_runtime_control_projection


def _build_artifact_inventory_surface(
    *,
    profile: WorkspaceProfile,
    progress_projection: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
    study_runtime_status_command: str,
) -> dict[str, Any]:
    supporting_files = [
        {
            "file_id": "artifact_runtime_proof",
            "label": "Artifact runtime proof",
            "path": "studies/<study_id>/manuscript/delivery_manifest.json",
            "summary": "canonical-source rebuild proof consumed by study_progress artifact_runtime_proof.",
        },
        {
            "file_id": "submission_hygiene_truth",
            "label": "Submission hygiene truth",
            "path": "study_progress.submission_hygiene_truth",
            "summary": "aggregates submission minimal, publication surface QC, internal language leakage, citation/numeric/display gates, and artifact proof.",
        },
        {
            "file_id": "task_intake_latest",
            "label": "Study task intake (latest)",
            "path": "studies/<study_id>/artifacts/controller/task_intake/latest.json",
            "summary": "durable task intake truth (task_id/intent/entry_mode/return_surface_contract).",
        },
        {
            "file_id": "runtime_watch_latest",
            "label": "Runtime watch (latest)",
            "path": "studies/<study_id>/artifacts/runtime_watch/latest.json",
            "summary": "runtime watch event companion for supervision freshness.",
        },
        {
            "file_id": "runtime_supervision_latest",
            "label": "Runtime supervision (latest)",
            "path": "studies/<study_id>/artifacts/runtime/runtime_supervision/latest.json",
            "summary": "runtime supervision truth owned by MAS runtime/progress durable surfaces.",
        },
        {
            "file_id": "publication_eval_latest",
            "label": "Publication eval (latest)",
            "path": "studies/<study_id>/artifacts/publication_eval/latest.json",
            "summary": "publication eval truth (publishability/quality closure state).",
        },
        {
            "file_id": "medical_manuscript_blueprint",
            "label": "Medical manuscript blueprint",
            "path": "studies/<study_id>/paper/medical_manuscript_blueprint.json",
            "summary": "pre-draft clinical argument blueprint for medical-journal prose generation.",
        },
        {
            "file_id": "medical_journal_style_corpus",
            "label": "Medical journal style corpus",
            "path": "studies/<study_id>/paper/medical_journal_style_corpus.json",
            "summary": "reusable style principles and short paraphrased exemplars for medical original-research voice.",
        },
        {
            "file_id": "medical_prose_review_request",
            "label": "AI medical prose review request",
            "path": "studies/<study_id>/artifacts/publication_eval/medical_prose_review_request.json",
            "summary": "AI reviewer input bundle; mechanical flags are evidence snippets only.",
        },
        {
            "file_id": "medical_prose_review",
            "label": "AI medical prose review",
            "path": "studies/<study_id>/artifacts/publication_eval/medical_prose_review.json",
            "summary": "AI-owned subjective manuscript prose verdict and representative rewrites.",
        },
        {
            "file_id": "retrospective_medical_prose_audit",
            "label": "Retrospective medical prose audit",
            "path": "studies/<study_id>/artifacts/publication_eval/retrospective_medical_prose_audit.json",
            "summary": "NF-PitNET 003 / DPCC 003 / DPCC 004 replay audit fixture for prose-quality regression.",
        },
        {
            "file_id": "controller_decisions_latest",
            "label": "Controller decisions (latest)",
            "path": "studies/<study_id>/artifacts/controller_decisions/latest.json",
            "summary": "controller decision truth (gate decisions / interventions / followthrough).",
        },
    ]
    return _build_shared_artifact_inventory(
        deliverable_files=[],
        supporting_files=supporting_files,
        workspace_path=str(profile.workspace_root),
        progress_headline=_non_empty_text(progress_projection.get("headline")) or None,
        artifact_surface={
            "surface_kind": "study_runtime_status",
            "summary": "按 study_id 读取 runtime 恢复合同与运行态。",
            "command": study_runtime_status_command,
            "step_id": "inspect_runtime_status",
            "locator_fields": ["profile_ref", "study_id"],
        },
        inspect_paths=[str(profile.workspace_root), "studies/<study_id>/artifacts", str(profile.runtime_root)],
        domain_projection={
            "recommended_restore_command": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
            "recommended_progress_command": str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
        },
    )


def _build_skill_runtime_continuity_envelope(
    *,
    runtime: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    session_continuity: Mapping[str, Any],
    progress_projection: Mapping[str, Any],
    artifact_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    resume_contract = dict(family_orchestration.get("resume_contract") or {})
    restore_surface = dict(session_continuity.get("restore_surface") or {})
    session_progress_surface = dict(session_continuity.get("progress_surface") or {})
    artifact_surface = dict(artifact_inventory.get("artifact_surface") or {})
    progress_domain_projection = dict(progress_projection.get("domain_projection") or {})
    restore_point_surface_ref = "/session_continuity/restore_surface"
    if isinstance(progress_domain_projection.get("research_runtime_control_projection"), Mapping):
        restore_point_surface_ref = (
            "/progress_projection/domain_projection/research_runtime_control_projection/restore_point_surface"
        )
    return {
        "surface_kind": "skill_runtime_continuity",
        "runtime_owner": str(runtime.get("runtime_owner") or ""),
        "domain_owner": str(runtime.get("domain_owner") or ""),
        "executor_owner": str(runtime.get("executor_owner") or ""),
        "session_locator_field": str(resume_contract.get("session_locator_field") or ""),
        "session_surface_ref": "/session_continuity",
        "progress_surface_ref": "/progress_projection/progress_surface",
        "artifact_surface_ref": "/artifact_inventory/artifact_surface",
        "restore_point_surface_ref": restore_point_surface_ref,
        "recommended_resume_command": str(restore_surface.get("command") or ""),
        "recommended_progress_command": str(session_progress_surface.get("command") or ""),
        "recommended_artifact_command": str(artifact_surface.get("command") or ""),
    }


def _build_opl_native_helper_proof_surface() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_native_helper_indexing_proof",
        "proof_id": "mas.opl_native_helper.indexing_proof.v1",
        "allowed_operation": "index_only",
        "runtime_surface_refs": [
            "/skill_catalog/skills/0/domain_projection/runtime_continuity",
            "/progress_projection/domain_projection/research_runtime_control_projection",
            "/runtime_inventory",
        ],
        "product_entry_surface_refs": [
            "/skill_catalog/skills/0/domain_projection/opl_runtime_manager_registration/domain_entry_surface",
            "/skill_catalog/skills/0/domain_projection/opl_runtime_manager_registration/registration_surface",
            "/artifact_inventory/artifact_surface",
            "/automation/automations/0",
        ],
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "helper_owner": "one-person-lab",
            "helper_write_policy": "no_domain_truth_writes",
            "authoritative_truth_refs": [
                "/study_runtime_status",
                "/runtime_watch",
                "/publication_eval/latest.json",
                "/controller_decisions/latest.json",
            ],
        },
        "non_goals": [
            "not_domain_logic",
            "not_a_hermes_agent_implementation",
            "not_an_rca_surface",
        ],
    }


def _build_opl_runtime_manager_registration(
    *,
    runtime: Mapping[str, Any],
    runtime_continuity: Mapping[str, Any],
    command_catalog: Mapping[str, str],
    skill_catalog_command: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "opl_runtime_manager_domain_registration",
        "version": "v1",
        "registration_id": "mas.opl_runtime_manager.registration.v1",
        "manager_surface_id": "opl_runtime_manager",
        "domain_id": "medautoscience",
        "domain_owner": TARGET_DOMAIN_ID,
        "runtime_owner": str(runtime.get("runtime_owner") or ""),
        "executor_owner": str(runtime.get("executor_owner") or ""),
        "domain_entry_surface": {
            "surface_kind": PRODUCT_ENTRY_STATUS_KIND,
            "command": command_catalog["product_entry_status"],
            "manifest_command": command_catalog["workspace_cockpit"],
        },
        "registration_surface": {
            "surface_kind": "skill_catalog",
            "ref": "/skill_catalog/skills/0/domain_projection/opl_runtime_manager_registration",
            "command": skill_catalog_command,
        },
        "consumable_projection_refs": [
            "/skill_catalog/skills/0/domain_projection/runtime_continuity",
            "/progress_projection/domain_projection/research_runtime_control_projection",
            "/artifact_inventory/artifact_surface",
            "/automation/automations/0",
            "/runtime_inventory",
        ],
        "state_index_inputs": {
            "workspace_registry_index": "/workspace_locator",
            "managed_session_ledger_index": "/session_continuity",
            "artifact_projection_index": "/artifact_inventory",
            "attention_queue_index": "/automation/automations/0",
            "runtime_health_snapshot_index": "/runtime_inventory",
        },
        "native_helper_consumption": {
            "protocol_ref": "contracts/opl-gateway/native-helper-contract.json",
            "language": "rust",
            "managed_by": "one-person-lab",
            "source_of_truth_rule": (
                "Rust helpers may index MAS workspace, session, artifact, attention, and runtime-health "
                "surfaces, but MAS durable study truth remains authoritative."
            ),
            "indexes": {
                "workspace_registry_index": {
                    "input_ref": "/workspace_locator",
                    "backing_helper_id": "opl-state-indexer",
                },
                "managed_session_ledger_index": {
                    "input_ref": "/session_continuity",
                    "backing_helper_id": "opl-state-indexer",
                },
                "artifact_projection_index": {
                    "input_ref": "/artifact_inventory",
                    "backing_helper_id": "opl-artifact-indexer",
                },
                "attention_queue_index": {
                    "input_ref": "/automation/automations/0",
                    "backing_helper_id": "opl-state-indexer",
                },
                "runtime_health_snapshot_index": {
                    "input_ref": "/runtime_inventory",
                    "backing_helper_id": "opl-runtime-watch",
                },
            },
            "proof_surface": _build_opl_native_helper_proof_surface(),
        },
        "resume_contract": {
            "session_locator_field": str(runtime_continuity.get("session_locator_field") or ""),
            "recommended_resume_command": str(runtime_continuity.get("recommended_resume_command") or ""),
            "recommended_progress_command": str(runtime_continuity.get("recommended_progress_command") or ""),
        },
        "wakeup_boundary": {
            "owner": TARGET_DOMAIN_ID,
            "surface_ref": "/automation/automations/0",
            "policy": "domain_owned_runtime_supervision_loop",
        },
        "non_goals": [
            "not_a_study_truth_owner",
            "not_a_publication_gate",
            "not_an_evidence_or_review_ledger",
            "not_a_concrete_executor",
        ],
    }


def _build_skill_catalog_surface(
    *,
    runtime: Mapping[str, Any],
    family_orchestration: Mapping[str, Any],
    session_continuity: Mapping[str, Any],
    progress_projection: Mapping[str, Any],
    artifact_inventory: Mapping[str, Any],
    product_entry_status: Mapping[str, Any],
    domain_entry_contract: Mapping[str, Any],
    product_entry_shell: Mapping[str, Any],
    skill_catalog_command: str,
) -> dict[str, Any]:
    summary = _non_empty_text(product_entry_status.get("summary")) or "MAS product entry skill catalog."
    command_catalog = {
        "product_entry_status": str((product_entry_shell.get("product_entry_status") or {}).get("command") or ""),
        "workspace_cockpit": str((product_entry_shell.get("workspace_cockpit") or {}).get("command") or ""),
        "submit_study_task": str((product_entry_shell.get("submit_study_task") or {}).get("command") or ""),
        "launch_study": str((product_entry_shell.get("launch_study") or {}).get("command") or ""),
        "study_progress": str((product_entry_shell.get("study_progress") or {}).get("command") or ""),
    }
    runtime_continuity = _build_skill_runtime_continuity_envelope(
        runtime=runtime,
        family_orchestration=family_orchestration,
        session_continuity=session_continuity,
        progress_projection=progress_projection,
        artifact_inventory=artifact_inventory,
    )
    opl_runtime_manager_registration = _build_opl_runtime_manager_registration(
        runtime=runtime,
        runtime_continuity=runtime_continuity,
        command_catalog=command_catalog,
        skill_catalog_command=skill_catalog_command,
    )
    skills = [
        _build_shared_skill_descriptor(
            skill_id="mas",
            title="Med Auto Science",
            owner=TARGET_DOMAIN_ID,
            distribution_mode="repo_tracked",
            surface_kind=PRODUCT_ENTRY_STATUS_KIND,
            description="作为单一 domain app skill 启动 MAS，并通过既有 workspace/controller contracts 驱动完整医学研究工作流。",
            command=command_catalog["product_entry_status"],
            readiness="landed",
            tags=["domain-app", "medical-research", "study"],
            domain_projection={
                "plugin_name": "mas",
                "skill_entry": "mas",
                "recommended_shell": "workspace_cockpit",
                "skill_semantics": "domain_app",
                "entry_shell_key": "product_entry_status",
                "entry_command": command_catalog["product_entry_status"],
                "supporting_shell_keys": [
                    "workspace_cockpit",
                    "submit_study_task",
                    "launch_study",
                    "study_progress",
                ],
                "shell_commands": command_catalog,
                "runtime_continuity": runtime_continuity,
                "opl_runtime_manager_registration": opl_runtime_manager_registration,
            },
        ),
    ]
    return _build_shared_skill_catalog(
        summary=summary,
        skills=skills,
        supported_commands=list(domain_entry_contract.get("supported_commands") or []),
        command_contracts=[
            dict(item)
            for item in (domain_entry_contract.get("command_contracts") or [])
            if isinstance(item, Mapping)
        ],
    )


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
