from __future__ import annotations

from typing import Any

from med_autoscience.opl_runtime_contract import OPL_HOSTED_STAGE_RUNTIME_ID, OPL_RUNTIME_OWNER
from med_autoscience.domain_entry_contract import domain_entry_handler_target


def _program_step(*, step_id: str, command: str, surface_kind: str, title: str) -> dict[str, str]:
    return {"step_id": step_id, "command": command, "surface_kind": surface_kind, "title": title}


def _program_surface(*, surface_kind: str, command: str | None = None, ref: str | None = None) -> dict[str, str]:
    payload = {"surface_kind": surface_kind}
    if command:
        payload["command"] = command
    if ref:
        payload["ref"] = ref
    return payload


def _sequence_step(*, step_id: str, title: str, status: str, phase_id: str, summary: str) -> dict[str, str]:
    return {
        "step_id": step_id,
        "title": title,
        "status": status,
        "phase_id": phase_id,
        "summary": summary,
    }


def build_backend_deconstruction_lane(
    *,
    deconstruction_map_ref: str,
    **kwargs: Any,
) -> dict[str, Any]:
    return {
        "surface_kind": "phase4_backend_deconstruction_lane",
        "summary": str(kwargs["summary"]),
        "substrate_targets": list(kwargs["substrate_targets"]),
        "backend_retained_now": list(kwargs["backend_retained_now"]),
        "current_backend_chain": list(kwargs["current_backend_chain"]),
        "optional_executor_proofs": list(kwargs["optional_executor_proofs"]),
        "promotion_rules": list(kwargs["promotion_rules"]),
        "deconstruction_map_ref": deconstruction_map_ref,
        "recommended_phase_command": str(kwargs["recommended_phase_command"]),
    }


def build_platform_target() -> dict[str, Any]:
    return {
        "surface_kind": "phase5_platform_target",
        "summary": (
            "Phase 5 已完成 MAS functional monolith closeout；后续平台工作只剩 optional hosted/stage-runtime "
            "frontend 与 future upstream intake，不再以 external MDS runtime core 为默认运行条件。"
        ),
        "sequence_scope": "monorepo_landing_readiness",
        "current_step_id": "functional_monolith_completion",
        "current_readiness_summary": (
            "MAS 默认研究入口、进度、诊断、artifact/quality parity、workspace helpers 与 OPL handoff 都已切到 MAS-owned domain surfaces；"
            "external MDS 只保留 frozen archive / historical fixture / explicit archive import reference。"
        ),
        "north_star_topology": {
            "domain_agent": "Med Auto Science",
            "runtime_owner": OPL_RUNTIME_OWNER,
            "runtime_substrate": OPL_HOSTED_STAGE_RUNTIME_ID,
            "controlled_research_backend": (
                "MAS domain owner receipts / Artifact authority refs / Quality verdict refs; "
                "generic runtime lifecycle handoff to OPL"
            ),
            "monorepo_status": "functional_monolith_completion_landed",
        },
        "target_internal_modules": [
            "controller_charter",
            "runtime",
            "eval_hygiene",
        ],
        "landing_sequence": [
            _sequence_step(
                step_id="freeze_stage_runtime_truth",
                title="Freeze stage-runtime truth",
                status="completed",
                phase_id="phase_1_mainline_established",
                summary="mainline topology、product-entry companions 与 post-gate platform wording 已冻结成 repo-tracked truth。",
            ),
            _sequence_step(
                step_id="stabilize_user_product_loop",
                title="Stabilize user product loop",
                status="in_progress",
                phase_id="phase_2_user_product_loop",
                summary=(
                    "当前活跃步骤：用 autonomy / quality / single-project owner 三线继续收紧 MAS "
                    "owner truth，并把启动 / 下任务 / 看进度 / 看恢复建议收成稳定前台回路。"
                ),
            ),
            _sequence_step(
                step_id="clear_multi_workspace_host_gate",
                title="Clear multi-workspace / host gate",
                status="pending",
                phase_id="phase_3_multi_workspace_host_clearance",
                summary="把 runtime/service/recovery proof 扩到更多 workspace / host 后，才具备更大 cutover 资格。",
            ),
            _sequence_step(
                step_id="freeze_backend_deconstruction_boundary",
                title="Freeze backend deconstruction boundary",
                status="pending",
                phase_id="phase_4_backend_deconstruction",
                summary="先把 substrate 与 backend retained-now 的边界继续收紧，再谈 executor 迁移或 ingest。",
            ),
            _sequence_step(
                step_id="mds_no_history_absorb",
                title="MDS no-history absorb",
                status="completed",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="MDS retained capability 已通过 no-history provenance、author guard、parity harness 和 external dependency retirement 收口到 MAS。",
            ),
            _sequence_step(
                step_id="runtime_core_ingest",
                title="Runtime core ingest",
                status="completed",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary=(
                    "默认 domain runtime receipts 已由 MAS 承接；external MDS daemon/runtime root "
                    "不再是默认运行或诊断依赖。"
                ),
            ),
            _sequence_step(
                step_id="functional_monolith_completion",
                title="Functional monolith completion",
                status="completed",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="MAS 默认 CLI/MCP/product-entry/workspace helper/OPL hosted workbench handoff 都不要求外部 MDS repo、daemon 或 WebUI。",
            ),
            _sequence_step(
                step_id="optional_hosted_frontend_packaging",
                title="Optional hosted frontend packaging",
                status="pending",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="后续可把 OPL dashboard / hosted frontend 消费 MAS refs-only projection，但不得重解释 MAS study truth。",
            ),
            _sequence_step(
                step_id="future_upstream_source_intake_review",
                title="Future upstream source intake review",
                status="pending",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="未来如需吸收 MDS/DeepScientist 新 snapshot，只能走 no-history provenance、author audit 和 MAS-owned capability proof。",
            ),
        ],
        "completed_step_ids": [
            "freeze_stage_runtime_truth",
            "mds_no_history_absorb",
            "runtime_core_ingest",
            "functional_monolith_completion",
        ],
        "remaining_step_ids": [
            "optional_hosted_frontend_packaging",
            "future_upstream_source_intake_review",
        ],
        "promotion_gates": [
            "phase_1_mainline_established",
            "phase_2_user_product_loop",
            "phase_3_multi_workspace_host_clearance",
            "phase_4_backend_deconstruction",
        ],
        "recommended_phase_command": domain_entry_handler_target("mainline-phase"),
        "land_now": [
            "repo-tracked product-entry shell and family orchestration companions",
            "controller-owned runtime/progress/recovery truth",
            "CLI/MCP/controller entry surfaces that already support real work",
            "MAS refs-only progress projections and OPL hosted workbench handoff refs",
        ],
        "not_yet": [
            "mature hosted standalone medical frontend",
            "future upstream source intake beyond historical fixture/provenance refs",
        ],
    }


def build_phase2_user_product_loop_lane(
    *,
    entry_status_command: str,
    submit_task_command: str,
    launch_study_command: str,
    study_progress_command: str,
    controller_decisions_ref: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "phase2_user_product_loop_lane",
        "summary": "把启动 MAS、给 study 下任务、续跑、持续看进度、处理恢复建议和人工 gate 收成同一条用户回路。",
        "recommended_step_id": "open_product_entry",
        "recommended_command": entry_status_command,
        "recommended_command_ref": _command_ref(entry_status_command),
        "command_role": "entry_point_metadata",
        "authority": False,
        "can_generate_action": False,
        "can_execute": False,
        "single_path": [
            {
                "step_id": "open_product_entry",
                "title": "先打开 MAS 产品入口",
                "surface_kind": "product_entry_status",
                "command": entry_status_command,
                "command_ref": _command_ref(entry_status_command),
            },
            {
                "step_id": "submit_task",
                "title": "给目标 study 写 durable task intake",
                "surface_kind": "study_task_intake",
                "command": submit_task_command,
                "command_ref": _command_ref(submit_task_command),
            },
            {
                "step_id": "continue_study",
                "title": "启动或续跑当前 study",
                "surface_kind": "launch_study",
                "command": launch_study_command,
                "command_ref": _command_ref(launch_study_command),
            },
            {
                "step_id": "inspect_progress",
                "title": "持续看进度、阻塞和恢复建议",
                "surface_kind": "study_progress",
                "command": study_progress_command,
                "command_ref": _command_ref(study_progress_command),
            },
            {
                "step_id": "handle_human_gate",
                "title": "遇到人工 gate 时通过 study progress 做决策",
                "surface_kind": "study_progress",
                "command": study_progress_command,
                "command_ref": _command_ref(study_progress_command),
            },
        ],
        "operator_questions": [
            {
                "question": "用户现在怎么启动 MAS？",
                "answer_surface_kind": "product_entry_status",
                "command": entry_status_command,
                "command_ref": _command_ref(entry_status_command),
            },
            {
                "question": "用户怎么给 study 下任务？",
                "answer_surface_kind": "study_task_intake",
                "command": submit_task_command,
                "command_ref": _command_ref(submit_task_command),
            },
            {
                "question": "用户怎么持续看进度、恢复建议和人工 gate？",
                "answer_surface_kind": "study_progress",
                "command": study_progress_command,
                "command_ref": _command_ref(study_progress_command),
            },
        ],
        "proof_surfaces": [
            {
                "surface_kind": "product_entry_status",
                "command": entry_status_command,
                "command_ref": _command_ref(entry_status_command),
            },
            {
                "surface_kind": "study_progress.operator_verdict",
                "command": study_progress_command,
                "command_ref": _command_ref(study_progress_command),
            },
            {
                "surface_kind": "study_progress.recovery_contract",
                "command": study_progress_command,
                "command_ref": _command_ref(study_progress_command),
            },
            {
                "surface_kind": "controller_decisions",
                "ref": controller_decisions_ref,
            },
        ],
    }


def _command_ref(command: str) -> dict[str, Any]:
    return {
        "command": command,
        "command_role": "entry_point_metadata",
        "authority": False,
        "can_generate_action": False,
        "can_execute": False,
    }


def build_phase2_user_product_loop() -> dict[str, Any]:
    return build_phase2_user_product_loop_lane(
        entry_status_command=domain_entry_handler_target("mainline-status"),
        submit_task_command=domain_entry_handler_target("submit-study-task"),
        launch_study_command=domain_entry_handler_target("launch-study"),
        study_progress_command=domain_entry_handler_target("study-progress"),
        controller_decisions_ref="studies/<study_id>/artifacts/controller_decisions/latest.json",
    )


def build_phase3_clearance_lane() -> dict[str, Any]:
    doctor_command = domain_entry_handler_target("mainline-status")
    supervisor_service_command = domain_entry_handler_target("study-progress")
    refresh_supervision_command = domain_entry_handler_target("paper-mission")
    launch_study_command = domain_entry_handler_target("launch-study")
    study_progress_command = domain_entry_handler_target("study-progress")
    return {
        "surface_kind": "phase3_host_clearance_lane",
        "summary": (
            "Phase 3 只做可选 hosted runtime / 多宿主 proof；MAS 默认研究入口、owner receipt "
            "与 paper-progress SLO 由 MAS surface 承接，generic cadence/provider SLO 归 OPL runtime manager。"
        ),
        "recommended_step_id": "mas_domain_refs_boundary",
        "recommended_command": doctor_command,
        "clearance_targets": [
            {
                "target_id": "mas_domain_refs_boundary",
                "title": "Check MAS domain refs and legacy runtime tombstone boundary",
                "commands": [doctor_command],
            },
            {
                "target_id": "supervisor_service",
                "title": "Inspect OPL-owned supervision projection",
                "commands": [
                    supervisor_service_command,
                    refresh_supervision_command,
                ],
            },
            {
                "target_id": "study_recovery_proof",
                "title": "Prove live study recovery and supervision",
                "commands": [
                    launch_study_command,
                    study_progress_command,
                ],
            },
        ],
        "clearance_loop": [
            _program_step(
                step_id="mas_domain_refs_boundary",
                title="确认 MAS domain refs boundary ready，旧 hosted runtime 仅保留 tombstone/provenance",
                surface_kind="doctor_domain_refs_boundary",
                command=doctor_command,
            ),
            _program_step(
                step_id="supervisor_service",
                title="确认 OPL replacement 与 MAS domain projection 在线",
                surface_kind="workspace_supervisor_service",
                command=supervisor_service_command,
            ),
            _program_step(
                step_id="refresh_supervision",
                title="读取 PaperMission / StageOutcome readback",
                surface_kind="paper_mission_readback_refresh",
                command=refresh_supervision_command,
            ),
            _program_step(
                step_id="study_recovery_proof",
                title="证明 live study recovery / progress supervision 成立",
                surface_kind="launch_study",
                command=launch_study_command,
            ),
            _program_step(
                step_id="inspect_study_progress",
                title="读取 study-progress proof",
                surface_kind="study_progress",
                command=study_progress_command,
            ),
        ],
        "proof_surfaces": [
            _program_surface(
                surface_kind="doctor.runtime_contract",
                command=doctor_command,
            ),
            _program_surface(
                surface_kind="progress_projection.autonomous_runtime_notice",
                command=domain_entry_handler_target("study-progress"),
            ),
            _program_surface(
                surface_kind="paper_mission_readback",
                command=refresh_supervision_command,
            ),
            _program_surface(
                surface_kind="opl_runtime_owner_handoff",
                ref="studies/<study_id>/artifacts/supervision/opl_runtime_owner_handoff/latest.json",
            ),
            _program_surface(
                surface_kind="controller_decisions",
                ref="studies/<study_id>/artifacts/controller_decisions/latest.json",
            ),
        ],
        "recommended_phase_command": domain_entry_handler_target("mainline-phase"),
    }


def build_phase4_backend_deconstruction() -> dict[str, Any]:
    return build_backend_deconstruction_lane(
        summary="Phase 4 只保留 future upstream source intake / historical fixture governance；MDS 不再是 runtime substrate。",
        substrate_targets=[
            {
                "capability_id": "session_run_watch_recovery",
                "owner": "MAS domain runtime receipts",
                "summary": (
                    "session / run / watch / recovery 的 domain owner receipt、paper-progress blocker "
                    "与 safe action refs 由 MAS surface 承接；generic scheduling / attempt lifecycle 迁往 OPL。"
                ),
            },
            {
                "capability_id": "backend_generic_runtime_contract",
                "owner": "MedAutoScience controller boundary",
                "summary": "controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            },
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
        recommended_phase_command=domain_entry_handler_target("mainline-phase"),
    )
