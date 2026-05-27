from __future__ import annotations

from med_autoscience import stage_skill_surface_projection
from med_autoscience.controllers import mainline_status
from med_autoscience.controllers.mainline_status_parts import program_surfaces as mainline_program_surfaces

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

_build_backend_deconstruction_lane = mainline_program_surfaces.build_backend_deconstruction_lane


def _build_phase5_platform_target(mainline_payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(mainline_payload) if mainline_payload is not None else mainline_status.read_mainline_status()
    source = payload.get("platform_target")
    if not isinstance(source, Mapping):
        source = mainline_program_surfaces.build_platform_target()
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
    hosted_entry_status_command = _json_surface_command(
        f"opl app product-entry-status --agent med-autoscience --profile {profile_arg}"
    )
    hosted_workbench_command = _json_surface_command(
        f"opl app workbench --agent med-autoscience --profile {profile_arg}"
    )
    lane = mainline_program_surfaces.build_phase2_user_product_loop_lane(
        entry_status_command=hosted_entry_status_command,
        workspace_cockpit_command=hosted_workbench_command,
        submit_task_command=(
            f"{_command(profile_ref, 'submit-study-task', '--profile', profile_arg)} "
            "--study-id <study_id> --task-intent '<task_intent>'"
        ),
        launch_study_command=_command(
            profile_ref,
            "launch-study",
            "--profile",
            profile_arg,
            "--study-id <study_id>",
        ),
        study_progress_command=_json_surface_command(
            _command(
                profile_ref,
                "study-progress",
                "--profile",
                profile_arg,
                "--study-id <study_id>",
            )
        ),
        controller_decisions_ref=str(
            profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"
        ),
    )
    workflow_command = hosted_workbench_command
    lane["workflow_steps"] = build_guarded_phase2_workflow_steps(workflow_command=workflow_command)
    return lane


def _build_phase3_clearance_lane(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    prefix = _command_prefix(profile_ref)
    profile_arg = _profile_arg(profile_ref)
    doctor_command = _command(profile_ref, "doctor", "--profile", profile_arg)
    supervisor_service_command = _command(
        profile_ref,
        "study-progress",
        "--profile",
        profile_arg,
        "--format json",
    )
    refresh_supervision_command = (
        f"{prefix} runtime domain-health-diagnostic --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {profile_arg} --request-opl-stage-attempts --request-opl-owner-route-reconcile --apply"
    )
    launch_study_command = _command(
        profile_ref,
        "launch-study",
        "--profile",
        profile_arg,
        "--study-id <study_id>",
    )
    study_progress_command = _command(
        profile_ref,
        "study-progress",
        "--profile",
        profile_arg,
        "--study-id <study_id>",
    )
    build_clearance_lane = _controller_override("_build_shared_clearance_lane", _build_shared_clearance_lane)
    return build_clearance_lane(
        surface_kind="phase3_host_clearance_lane",
        summary=(
            "Phase 3 只做可选 hosted runtime / 多宿主 proof；MAS 默认研究入口、owner receipt "
            "与 paper-progress SLO 由 MAS surface 承接，generic cadence/provider SLO 归 OPL current_control_state。"
        ),
        recommended_step_id="mas_domain_refs_boundary",
        recommended_command=doctor_command,
        clearance_targets=[
            _build_shared_clearance_target(
                target_id="mas_domain_refs_boundary",
                title="Check MAS domain refs and legacy runtime tombstone boundary",
                commands=[doctor_command],
            ),
            _build_shared_clearance_target(
                target_id="supervisor_service",
                title="Inspect OPL current-control-state refs through MAS progress",
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
                step_id="mas_domain_refs_boundary",
                title="确认 MAS domain refs boundary ready，旧 hosted runtime 仅保留 tombstone/provenance",
                surface_kind="doctor_domain_refs_boundary",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="supervisor_service",
                title="确认 OPL replacement 与 MAS domain projection 在线",
                surface_kind="opl_current_control_state_handoff",
                command=supervisor_service_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="refresh_supervision",
                title="刷新 MAS domain refs projection",
                surface_kind="domain_health_diagnostic_refresh",
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
                surface_kind="doctor.runtime_contract",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="progress_projection.autonomous_runtime_notice",
                command=f"{prefix} study progress-projection --profile {profile_arg} --study-id <study_id>",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="domain_health_diagnostic",
                ref=str(profile.studies_root / "<study_id>" / "artifacts" / "domain_health_diagnostic" / "latest.json"),
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="runtime_supervision_retired_provenance",
                ref="contracts/runtime/legacy-active-path-tombstones.json",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="controller_decisions",
                ref=str(profile.studies_root / "<study_id>" / "artifacts" / "controller_decisions" / "latest.json"),
            ),
        ],
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli doctor mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    )


def _build_phase4_backend_deconstruction() -> dict[str, Any]:
    build_backend_deconstruction_lane = _controller_override(
        "_build_backend_deconstruction_lane",
        mainline_program_surfaces.build_backend_deconstruction_lane,
    )
    return build_backend_deconstruction_lane(
        summary="Phase 4 只保留 future upstream source intake / historical fixture governance；MDS 不再是 runtime substrate。",
        substrate_targets=[
            _build_shared_program_capability(
                capability_id="session_run_watch_recovery",
                owner="MAS domain runtime receipts",
                summary=(
                    "session / run / watch / recovery 的 domain owner receipt、paper-progress blocker "
                    "与 safe action refs 由 MAS surface 承接；generic scheduling / attempt lifecycle 迁往 OPL。"
                ),
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
            "explicit archive import / backend-audit reference",
        ],
        current_backend_chain=[
            "med_autoscience domain surfaces -> MAS owner receipts / artifact authority refs / quality verdict refs",
            "generic runtime/provider context -> OPL current_control_state refs-only handoff",
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
            "uv run python -m med_autoscience.cli doctor mainline-phase --phase phase_4_backend_deconstruction"
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


from .generated_status_projection import (
    _build_artifact_inventory_surface,
    _build_progress_projection_surface,
    _build_runtime_inventory_surface,
    _build_session_continuity_surface,
    _build_skill_runtime_continuity_envelope,
    _build_task_lifecycle_surface,
)


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
            "/skill_catalog/skills/0/domain_projection/opl_stage_runtime_registration/domain_entry_surface",
            "/skill_catalog/skills/0/domain_projection/opl_stage_runtime_registration/registration_surface",
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
                "/progress_projection",
                "/domain_health_diagnostic",
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
            "protocol_ref": "contracts/opl-framework/native-helper-contract.json",
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
            "owner": "one-person-lab",
            "surface_ref": "/automation/automations/0",
            "policy": "opl_owned_scheduler_transport_mas_domain_receipt_projection",
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
    action_catalog: Mapping[str, Any],
) -> dict[str, Any]:
    summary = _non_empty_text(product_entry_status.get("summary")) or "MAS product entry skill catalog."
    command_catalog = {
        **_action_catalog_command_map(action_catalog),
        **{
            key: str(surface.get("command"))
            for key, surface in product_entry_shell.items()
            if isinstance(surface, Mapping) and surface.get("command")
        },
    }
    skill_action_projection = _project_mas_action_catalog("skill", action_catalog)
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
                "action_catalog_projection": skill_action_projection,
                "runtime_continuity": runtime_continuity,
                "stage_skill_surface_projection": (
                    stage_skill_surface_projection.build_stage_skill_surface_projection()
                ),
                "opl_stage_runtime_registration": opl_runtime_manager_registration,
                "opl_runtime_manager_registration": opl_runtime_manager_registration,
            },
        )
        | {
            "descriptor_owner": "one-person-lab",
            "domain_repo_can_own_generated_surface": False,
            "domain_handler_target": "MedAutoScienceDomainEntry",
            "domain_handler_target_owner": "MedAutoScience",
            "descriptor_role": "opl_generated_skill_descriptor_targeting_mas_domain_entry",
        },
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
    ) | {"action_catalog": dict(action_catalog)}


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
