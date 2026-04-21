from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from opl_harness_shared.product_entry_program_companions import (
    build_backend_deconstruction_lane as _build_shared_backend_deconstruction_lane,
    build_clearance_lane as _build_shared_clearance_lane,
    build_clearance_target as _build_shared_clearance_target,
    build_platform_target as _build_shared_platform_target,
    build_product_entry_program_step as _build_shared_product_entry_program_step,
    build_product_entry_program_surface as _build_shared_product_entry_program_surface,
    build_program_capability as _build_shared_program_capability,
    build_program_sequence_step as _build_shared_program_sequence_step,
)


SCHEMA_VERSION = 1
PROGRAM_ID = "research-foundry-medical-mainline"
CURRENT_STAGE_ID = "f4_blocker_closeout"
CURRENT_STAGE_STATUS = "in_progress"
CURRENT_PROGRAM_PHASE_ID = "phase_1_mainline_established"
CURRENT_PROGRAM_PHASE_STATUS = "in_progress"

_PHASE_STATUS_LABELS = {
    "in_progress": "进行中",
    "completed": "已完成",
    "pending": "待开始",
    "blocked": "阻塞中",
    "blocked_post_gate": "等待前置门后进入",
}

_ENTRY_POINT_LABELS = {
    "mainline_status": "查看主线状态",
    "workspace_cockpit": "打开 workspace cockpit",
    "study_progress": "查看 study 进度",
    "submit_study_task": "提交 study 任务",
    "launch_study": "启动或续跑 study",
    "doctor": "运行 doctor",
    "hermes_runtime_check": "检查 Hermes runtime",
    "watch": "刷新监管与恢复",
}

_SEQUENCE_SCOPE_LABELS = {
    "monorepo_landing_readiness": "monorepo 落地就绪度",
}

_MONOREPO_STATUS_LABELS = {
    "post_gate_target": "post-gate 目标态",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _phase_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _PHASE_STATUS_LABELS.get(text, text)


def _bool_label(value: object) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return text


def _entry_point_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未命名入口"
    return _ENTRY_POINT_LABELS.get(text, text.replace("_", " "))


def _sequence_scope_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _SEQUENCE_SCOPE_LABELS.get(text, text)


def _monorepo_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _MONOREPO_STATUS_LABELS.get(text, text)


def _single_project_boundary() -> dict[str, Any]:
    return {
        "surface_kind": "single_project_boundary",
        "summary": (
            "当前 tranche 收口的是 MAS 单项目 owner truth、repo-tracked program truth 与用户可见边界；"
            "physical monorepo absorb 继续严格属于 post-gate 工作。"
        ),
        "mas_owner_modules": [
            "controller_charter",
            "runtime",
            "eval_hygiene",
        ],
        "mds_retained_roles": [
            {
                "role_id": "research_backend",
                "title": "Controlled research backend",
                "summary": "继续承接当前 inner research execution 与存量 study 兼容面。",
            },
            {
                "role_id": "behavior_equivalence_oracle",
                "title": "Behavior-equivalence oracle",
                "summary": "继续作为质量判断、自治语义与 durable surface 的行为等价对照线。",
            },
            {
                "role_id": "upstream_intake_buffer",
                "title": "Upstream intake buffer",
                "summary": "继续承接来自 DeepScientist / MDS 的上游输入，审计后再决定是否吸收进 MAS。",
            },
        ],
        "land_now": [
            "MAS 单项目 owner wording and repo-tracked truth",
            "docs/status/program/mainline boundary alignment",
            "user-visible wording that MDS is no longer a second long-term owner",
        ],
        "post_gate_only": [
            "physical monorepo absorb",
            "runtime core ingest across repos",
            "broader platform/federation restructuring after earlier phases hold",
        ],
        "not_now": [
            "treating MedDeepScientist as a second long-term owner",
            "using monorepo language as shorthand for current tranche completion",
        ],
    }


def _phase_single_project_boundary(phase_id: object) -> dict[str, Any] | None:
    if _non_empty_text(phase_id) != "phase_1_mainline_established":
        return None
    return _single_project_boundary()


def _platform_target() -> dict[str, Any]:
    return _build_shared_platform_target(
        summary=(
            "Phase 5 的目标是把 MAS 继续收敛到 federation/platform-ready 形态，包括 post-gate monorepo、"
            "runtime core ingest 和更成熟的 direct product entry；但这些都必须建立在前四阶段真实成立之后。"
        ),
        sequence_scope="monorepo_landing_readiness",
        current_step_id="stabilize_user_product_loop",
        current_readiness_summary=(
            "单项目长线已经完成 gateway/runtime truth 冻结，当前正在推进 user product loop hardening 与边界收紧；"
            "physical absorb 仍然严格属于 post-gate 工作。"
        ),
        north_star_topology={
            "domain_gateway": "Med Auto Science",
            "outer_runtime_substrate_owner": "upstream Hermes-Agent",
            "controlled_research_backend": "MedDeepScientist",
            "monorepo_status": "post_gate_target",
        },
        target_internal_modules=[
            "controller_charter",
            "runtime",
            "eval_hygiene",
        ],
        landing_sequence=[
            _build_shared_program_sequence_step(
                step_id="freeze_gateway_runtime_truth",
                title="Freeze gateway/runtime truth",
                status="completed",
                phase_id="phase_1_mainline_established",
                summary="mainline topology、product-entry companions 与 post-gate platform wording 已冻结成 repo-tracked truth。",
            ),
            _build_shared_program_sequence_step(
                step_id="stabilize_user_product_loop",
                title="Stabilize user product loop",
                status="in_progress",
                phase_id="phase_2_user_product_loop",
                summary="当前活跃步骤：继续收口 F4 blocker，并把启动 / 下任务 / 看进度 / 看恢复建议收成稳定前台回路。",
            ),
            _build_shared_program_sequence_step(
                step_id="clear_multi_workspace_host_gate",
                title="Clear multi-workspace / host gate",
                status="pending",
                phase_id="phase_3_multi_workspace_host_clearance",
                summary="把 runtime/service/recovery proof 扩到更多 workspace / host 后，才具备更大 cutover 资格。",
            ),
            _build_shared_program_sequence_step(
                step_id="freeze_backend_deconstruction_boundary",
                title="Freeze backend deconstruction boundary",
                status="pending",
                phase_id="phase_4_backend_deconstruction",
                summary="先把 substrate 与 backend retained-now 的边界继续收紧，再谈 executor 迁移或 ingest。",
            ),
            _build_shared_program_sequence_step(
                step_id="physical_monorepo_absorb",
                title="Physical monorepo absorb",
                status="blocked_post_gate",
                phase_id="phase_5_federation_platform_maturation",
                summary="只有在前面几步都稳定通过后，controller_charter / runtime / eval_hygiene 才能进入 post-gate 物理 monorepo absorb。",
            ),
        ],
        completed_step_ids=[
            "freeze_gateway_runtime_truth",
        ],
        remaining_step_ids=[
            "clear_multi_workspace_host_gate",
            "freeze_backend_deconstruction_boundary",
            "physical_monorepo_absorb",
        ],
        promotion_gates=[
            "phase_1_mainline_established",
            "phase_2_user_product_loop",
            "phase_3_multi_workspace_host_clearance",
            "phase_4_backend_deconstruction",
        ],
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_5_federation_platform_maturation"
        ),
        land_now=[
            "repo-tracked product-entry shell and family orchestration companions",
            "controller-owned runtime/progress/recovery truth",
            "CLI/MCP/controller entry surfaces that already support real work",
        ],
        not_yet=[
            "physical monorepo absorb",
            "runtime core ingest across repos",
            "mature hosted standalone medical frontend",
        ],
    )


def build_phase2_user_product_loop_lane(
    *,
    frontdesk_command: str,
    workspace_cockpit_command: str,
    submit_task_command: str,
    launch_study_command: str,
    study_progress_command: str,
    controller_decisions_ref: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "phase2_user_product_loop_lane",
        "summary": "把启动 MAS、给 study 下任务、续跑、持续看进度、处理恢复建议和人工 gate 收成同一条用户回路。",
        "recommended_step_id": "open_frontdesk",
        "recommended_command": frontdesk_command,
        "single_path": [
            {
                "step_id": "open_frontdesk",
                "title": "先打开 MAS 前台",
                "surface_kind": "product_frontdesk",
                "command": frontdesk_command,
            },
            {
                "step_id": "inspect_workspace_inbox",
                "title": "确认当前 workspace inbox / attention queue",
                "surface_kind": "workspace_cockpit",
                "command": workspace_cockpit_command,
            },
            {
                "step_id": "submit_task",
                "title": "给目标 study 写 durable task intake",
                "surface_kind": "study_task_intake",
                "command": submit_task_command,
            },
            {
                "step_id": "continue_study",
                "title": "启动或续跑当前 study",
                "surface_kind": "launch_study",
                "command": launch_study_command,
            },
            {
                "step_id": "inspect_progress",
                "title": "持续看进度、阻塞和恢复建议",
                "surface_kind": "study_progress",
                "command": study_progress_command,
            },
            {
                "step_id": "handle_human_gate",
                "title": "遇到人工 gate 时回到 progress / cockpit 做决策",
                "surface_kind": "study_progress",
                "command": study_progress_command,
            },
        ],
        "operator_questions": [
            {
                "question": "用户现在怎么启动 MAS？",
                "answer_surface_kind": "product_frontdesk",
                "command": frontdesk_command,
            },
            {
                "question": "用户怎么给 study 下任务？",
                "answer_surface_kind": "study_task_intake",
                "command": submit_task_command,
            },
            {
                "question": "用户怎么持续看进度和恢复建议？",
                "answer_surface_kind": "study_progress",
                "command": study_progress_command,
            },
        ],
        "proof_surfaces": [
            {
                "surface_kind": "product_frontdesk",
                "command": frontdesk_command,
            },
            {
                "surface_kind": "workspace_cockpit",
                "command": workspace_cockpit_command,
            },
            {
                "surface_kind": "study_progress.operator_verdict",
                "command": study_progress_command,
            },
            {
                "surface_kind": "study_progress.recovery_contract",
                "command": study_progress_command,
            },
            {
                "surface_kind": "controller_decisions",
                "ref": controller_decisions_ref,
            },
        ],
    }


def _phase2_user_product_loop() -> dict[str, Any]:
    return build_phase2_user_product_loop_lane(
        frontdesk_command="uv run python -m med_autoscience.cli product-frontdesk --profile <profile>",
        workspace_cockpit_command="uv run python -m med_autoscience.cli workspace-cockpit --profile <profile>",
        submit_task_command=(
            "uv run python -m med_autoscience.cli submit-study-task --profile <profile> "
            "--study-id <study_id> --task-intent '<task_intent>'"
        ),
        launch_study_command="uv run python -m med_autoscience.cli launch-study --profile <profile> --study-id <study_id>",
        study_progress_command=(
            "uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>"
        ),
        controller_decisions_ref="studies/<study_id>/artifacts/controller_decisions/latest.json",
    )


def _phase3_clearance_lane() -> dict[str, Any]:
    doctor_command = "uv run python -m med_autoscience.cli doctor --profile <profile>"
    hermes_runtime_check_command = "uv run python -m med_autoscience.cli hermes-runtime-check --profile <profile>"
    supervisor_service_command = "uv run python -m med_autoscience.cli runtime-supervision-status --profile <profile>"
    refresh_supervision_command = (
        "uv run python -m med_autoscience.cli watch --runtime-root <runtime_root> "
        "--profile <profile> --ensure-study-runtimes --apply"
    )
    launch_study_command = (
        "uv run python -m med_autoscience.cli launch-study --profile <profile> --study-id <study_id>"
    )
    study_progress_command = (
        "uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>"
    )
    return _build_shared_clearance_lane(
        surface_kind="phase3_host_clearance_lane",
        summary="Phase 3 把 external runtime、Hermes-hosted workspace supervision 和 study recovery proof 扩到更多 workspace/host，并保持 fail-closed。",
        recommended_step_id="external_runtime_contract",
        recommended_command=doctor_command,
        clearance_targets=[
            _build_shared_clearance_target(
                target_id="external_runtime_contract",
                title="Check external Hermes runtime contract",
                commands=[
                    doctor_command,
                    hermes_runtime_check_command,
                ],
            ),
            _build_shared_clearance_target(
                target_id="supervisor_service",
                title="Keep Hermes-hosted workspace supervision online",
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
                title="先确认 external Hermes runtime contract ready",
                surface_kind="doctor_runtime_contract",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="hermes_runtime_check",
                title="确认 Hermes runtime 绑定证据",
                surface_kind="hermes_runtime_check",
                command=hermes_runtime_check_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="supervisor_service",
                title="确认 workspace 常驻监管在线",
                surface_kind="workspace_supervisor_service",
                command=supervisor_service_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="refresh_supervision",
                title="刷新 Hermes-hosted supervision tick",
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
                command="uv run python -m med_autoscience.cli study-runtime-status --profile <profile> --study-id <study_id>",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="runtime_watch",
                ref="studies/<study_id>/artifacts/runtime_watch/latest.json",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="runtime_supervision",
                ref="studies/<study_id>/artifacts/runtime_supervision/latest.json",
            ),
            _build_shared_product_entry_program_surface(
                surface_kind="controller_decisions",
                ref="studies/<study_id>/artifacts/controller_decisions/latest.json",
            ),
        ],
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    )


def _phase4_backend_deconstruction() -> dict[str, Any]:
    return _build_shared_backend_deconstruction_lane(
        summary="Phase 4 把可迁出的通用 runtime 能力继续迁向 substrate，同时诚实保留 controlled backend executor；这一步仍不是物理 monorepo absorb。",
        substrate_targets=[
            _build_shared_program_capability(
                capability_id="session_run_watch_recovery",
                owner="upstream Hermes-Agent",
                summary="session / run / watch / recovery / scheduling / interruption 继续收归 outer runtime substrate。",
            ),
            _build_shared_program_capability(
                capability_id="backend_generic_runtime_contract",
                owner="MedAutoScience controller boundary",
                summary="controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            ),
        ],
        backend_retained_now=[
            "MedDeepScientist CodexRunner autonomous executor chain",
            "backend-local agent/tool routing and Codex skills",
            "quest-local research execution, paper worktree, and daemon side effects",
        ],
        current_backend_chain=[
            "med_autoscience.runtime_transport.hermes -> med_autoscience.runtime_transport.med_deepscientist",
            "med_deepscientist CodexRunner -> codex exec autonomous agent loop",
        ],
        optional_executor_proofs=[
            {
                "executor_kind": "hermes_native_proof",
                "entrypoint": "MedDeepScientist HermesNativeProofRunner -> run_agent.AIAgent.run_conversation",
                "default_model": "inherit_local_hermes_default",
                "default_reasoning_effort": "inherit_local_hermes_default",
            }
        ],
        promotion_rules=[
            "no claim of backend retirement without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "no physical monorepo absorb before the external gate is cleared",
        ],
        deconstruction_map_doc="docs/program/med_deepscientist_deconstruction_map.md",
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_4_backend_deconstruction"
        ),
    )


def _phase_ladder() -> list[dict[str, Any]]:
    return [
        {
            "id": "phase_1_mainline_established",
            "title": "Phase 1 mainline established",
            "status": "in_progress",
            "usable_now": True,
            "summary": (
                "先证明 MAS -> Hermes-Agent target outer substrate -> controlled MedDeepScientist backend 这条主线诚实成立，"
                "并完成 F4 blocker 收口与单项目 owner 边界收紧。"
            ),
            "focus": [
                "close remaining study blockers without reopening seam-only work",
                "keep runtime truth, recovery proof, and product-entry hardening aligned",
            ],
            "entry_points": [
                {
                    "name": "mainline_status",
                    "command": "uv run python -m med_autoscience.cli mainline-status",
                    "purpose": "先看 repo 主线真相、当前 tranche 和 remaining gaps。",
                },
                {
                    "name": "workspace_cockpit",
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile <profile>",
                    "purpose": "看当前 workspace 的监管、attention queue 和用户入口回路。",
                },
                {
                    "name": "study_progress",
                    "command": "uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>",
                    "purpose": "确认 active study 当前卡在哪、下一步是什么、是否需要人工决策。",
                },
            ],
            "exit_criteria": [
                "F4 blocker closeout 不再主要停留在 repo-side seam 或 host compatibility。",
                "当前活跃 study 的主要阻塞继续前移到 publication / completion / human-gate truth。",
                "用户已经能稳定看到主线状态、workspace attention 和 study progress。",
            ],
            "phase_docs": [
                "docs/status.md",
                "docs/project.md",
                "docs/architecture.md",
            ],
            "single_project_boundary": _phase_single_project_boundary("phase_1_mainline_established"),
        },
        {
            "id": "phase_2_user_product_loop",
            "title": "Phase 2 user product loop",
            "status": "pending",
            "usable_now": True,
            "summary": "把启动、下任务、持续看进度、看告警、看恢复建议收成稳定用户回路，并把 MDS 压回 backend/oracle/intake buffer 语义。",
            "focus": [
                "stabilize user-facing inbox, attention queue, and progress loop",
                "make stuck-state, recovery suggestions, and supervision freshness continuously visible",
            ],
            "entry_points": [
                {
                    "name": "workspace_cockpit",
                    "command": "uv run python -m med_autoscience.cli workspace-cockpit --profile <profile>",
                    "purpose": "把 workspace-cockpit 当作当前用户 inbox 入口使用。",
                },
                {
                    "name": "submit_study_task",
                    "command": "uv run python -m med_autoscience.cli submit-study-task --profile <profile> --study-id <study_id> --task-intent '<task_intent>'",
                    "purpose": "把任务写成 durable truth，而不是只停在对话里。",
                },
                {
                    "name": "launch_study",
                    "command": "uv run python -m med_autoscience.cli launch-study --profile <profile> --study-id <study_id>",
                    "purpose": "正式启动或续跑 study，并立即拿到监督入口。",
                },
                {
                    "name": "study_progress",
                    "command": "uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>",
                    "purpose": "持续轮询人话进度、阻塞、下一步和最新监督入口。",
                },
            ],
            "exit_criteria": [
                "用户不再需要自己拼 controller surface 才能完成 start / submit / watch。",
                "attention queue、progress freshness、recovery suggestion 已经稳定可见。",
                "当前 repo-tracked shell 已足够像真实 user loop，而不是命令散点集合。",
            ],
            "phase_docs": [
                "docs/README.md",
                "docs/runtime/agent_runtime_interface.md",
                "docs/references/lightweight_product_entry_and_opl_handoff.md",
            ],
        },
        {
            "id": "phase_3_multi_workspace_host_clearance",
            "title": "Phase 3 multi-workspace / host clearance",
            "status": "pending",
            "usable_now": True,
            "summary": "把当前 proof 从单机/单 workspace 扩到多 workspace、多宿主的真实长期稳定性。",
            "focus": [
                "prove service, recovery, and quality guards across more hosts and workspaces",
                "clear broader external-runtime and workspace-specific blocker classes honestly",
            ],
            "entry_points": [
                {
                    "name": "doctor",
                    "command": "uv run python -m med_autoscience.cli doctor --profile <profile>",
                    "purpose": "先看 workspace / runtime / external Hermes contract readiness。",
                },
                {
                    "name": "hermes_runtime_check",
                    "command": "uv run python -m med_autoscience.cli hermes-runtime-check --profile <profile>",
                    "purpose": "检查 external Hermes runtime 证据和 fail-closed gate。",
                },
                {
                    "name": "watch",
                    "command": "uv run python -m med_autoscience.cli watch --runtime-root <runtime_root> --profile <profile> --ensure-study-runtimes --apply",
                    "purpose": "验证 supervisor tick、恢复动作和 runtime reconciliation。",
                },
            ],
            "exit_criteria": [
                "external-runtime clearance 不再只依赖当前开发宿主。",
                "更多 workspace / host 的 service、watch、recovery 已有真实 proof。",
                "host/env compatibility 不再反复成为主阻塞类别。",
            ],
            "phase_docs": [
                "docs/README.md",
                "docs/status.md",
                "docs/program/external_runtime_dependency_gate.md",
                "docs/program/upstream_hermes_agent_fast_cutover_board.md",
            ],
        },
        {
            "id": "phase_4_backend_deconstruction",
            "title": "Phase 4 backend deconstruction",
            "status": "pending",
            "usable_now": True,
            "summary": "在 outer runtime 与产品回路稳定后，再逐步解构 MedDeepScientist 中可迁出的通用能力；这一步先冻结 retained-now 边界，不提前做 physical absorb。",
            "focus": [
                "move reusable runtime capability out of the controlled backend only with proof",
                "keep executor replacement explicit and contract-driven instead of forced rewrites",
            ],
            "entry_points": [
                {
                    "name": "mainline_phase",
                    "command": "uv run python -m med_autoscience.cli mainline-phase --phase phase_4_backend_deconstruction",
                    "purpose": "先看 backend deconstruction 的当前边界、入口和退出条件。",
                },
                {
                    "name": "deconstruction_map",
                    "command": "open docs/program/med_deepscientist_deconstruction_map.md",
                    "purpose": "核对哪些能力属于 substrate、backend、后续替换。",
                },
            ],
            "exit_criteria": [
                "迁出的能力有明确 owner、contract、tests 和 proof surface。",
                "MedDeepScientist 更接近 controlled executor，而不是 hidden runtime authority。",
                "executor replacement 不依赖一次性重写或 truth rewrite。",
            ],
            "phase_docs": [
                "docs/README.md",
                "docs/project.md",
                "docs/program/med_deepscientist_deconstruction_map.md",
            ],
        },
        {
            "id": "phase_5_federation_platform_maturation",
            "title": "Phase 5 federation and platform maturation",
            "status": "pending",
            "usable_now": True,
            "summary": "最后再考虑更大平台化工作，如 federation direct entry、monorepo 与 runtime core ingest。",
            "focus": [
                "land broader federation-facing direct entry only after earlier phases hold",
                "treat monorepo and large physical restructures as strictly post-gate work",
            ],
            "entry_points": [
                {
                    "name": "mainline_phase",
                    "command": "uv run python -m med_autoscience.cli mainline-phase --phase phase_5_federation_platform_maturation",
                    "purpose": "先看 federation / platform 这层现在仍然为什么是后置阶段。",
                },
                {
                    "name": "mainline_status",
                    "command": "uv run python -m med_autoscience.cli mainline-status",
                    "purpose": "回到当前主线，确认更大平台化工作是否已经到了诚实时机。",
                },
            ],
            "exit_criteria": [
                "前四阶段已经稳定成立，不再靠少量 proof 支撑整体口径。",
                "更大物理结构调整不会制造 truth drift。",
                "OPL family entry 与 MAS domain entry 已能自然衔接。",
            ],
            "phase_docs": [
                "docs/README.md",
                "docs/project.md",
                "docs/program/research_foundry_medical_mainline.md",
            ],
        },
    ]


def read_mainline_status() -> dict[str, Any]:
    phase_ladder = _phase_ladder()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "program_id": PROGRAM_ID,
        "federation_position": {
            "opl": "top-level federation and gateway language",
            "research_foundry": "generic Research Ops framework layer",
            "med_autoscience": "medical domain gateway plus Domain Harness OS",
        },
        "ideal_state": {
            "north_star": (
                "把医学研究稳定推进成 publication-grade evidence chain、稿件、交付与长期可监管运行。"
            ),
            "runtime_topology": {
                "domain_gateway": "Med Auto Science",
                "outer_runtime_substrate_owner": "upstream Hermes-Agent",
                "research_backend": "MedDeepScientist (controlled backend)",
                "entry_shape": (
                    "compatible Med Auto Science product entry plus OPL handoff over the same substrate, "
                    "without replacing domain authority"
                ),
            },
            "product_shape": [
                "用户能直接启动、下任务、看进度、看监管在线态",
                "OPL 可把 domain handoff 送进 MAS，而不吞掉 MAS authority",
                "MAS 持续做 gateway / outer-loop / publication judgment owner",
            ],
        },
        "single_project_boundary": _single_project_boundary(),
        "current_stage": {
            "id": CURRENT_STAGE_ID,
            "status": CURRENT_STAGE_STATUS,
            "title": "F4 blocker closeout",
            "summary": (
                "repo-side 已拿到 external Hermes runtime truth、real adapter cutover 和至少一条真实 study "
                "recovery/proof；当前主线进入 blocker 收口、product-entry hardening 与单项目边界收紧，而不是回去继续做 seam-only 包装。"
            ),
        },
        "current_program_phase": {
            "id": CURRENT_PROGRAM_PHASE_ID,
            "status": CURRENT_PROGRAM_PHASE_STATUS,
            "title": "Phase 1 mainline established",
            "summary": (
                "当前总体仍处在第一阶段尾声：主线已成立，正在把 F4 blocker 收口干净，并把用户可见入口与单项目边界继续收成真实 repo-tracked truth。"
            ),
            "single_project_boundary": _phase_single_project_boundary(CURRENT_PROGRAM_PHASE_ID),
        },
        "phase2_user_product_loop": _phase2_user_product_loop(),
        "phase3_clearance_lane": _phase3_clearance_lane(),
        "phase4_backend_deconstruction": _phase4_backend_deconstruction(),
        "platform_target": _platform_target(),
        "phase_ladder": phase_ladder,
        "completed_tranches": [
            {
                "id": "positioning_frozen",
                "title": "OPL / Research Foundry / MAS positioning frozen",
                "summary": "MAS 已收口为 Research Foundry 的医学实现、domain gateway 与 Domain Harness OS。",
            },
            {
                "id": "f1_external_hermes_runtime_truth",
                "title": "F1 external Hermes runtime truth",
                "summary": "repo-side contract、doctor 与 runtime-check 已能 fail-closed 识别 external Hermes evidence。",
            },
            {
                "id": "f2_real_adapter_cutover",
                "title": "F2 real adapter cutover",
                "summary": "repo-side seam 已收紧为真实 adapter，而不是 consumer-only seam。",
            },
            {
                "id": "f3_real_study_soak_recovery_proof",
                "title": "F3 real study soak / recovery proof",
                "summary": "至少一条真实 study 路径已经证明 watch / recovery / progress proof 成立。",
            },
            {
                "id": "repo_tracked_product_entry_shell",
                "title": "Repo-tracked product-entry shell",
                "summary": "workspace-cockpit / submit-study-task / launch-study / study-progress 已构成真实用户入口壳。",
            },
        ],
        "remaining_gaps": [
            "mature standalone medical product entry is still not landed; the truthful surface is still the repo-tracked shell plus agent-operated CLI/MCP",
            "OPL -> MAS handoff is documented and contract-shaped, but not yet a live federation front door",
            "external-runtime clearance still needs broader host/workspace proof; current proof is real but not universal",
            "active study blockers still need continued closeout at publication / completion / human-gate truth surfaces",
        ],
        "next_focus": [
            "keep the mainline on F4 blocker closeout instead of reopening seam-only work",
            "continue hardening user-visible product-entry surfaces so task, progress, supervision, and stuck-state truth stay visible",
            "keep MedDeepScientist wording pinned to research backend / oracle / intake buffer instead of second-owner language",
            "keep docs/status/runtime contracts aligned so OPL language, MAS role, and runtime truth do not drift",
            "only move toward broader cutover or monorepo work after the external gate is honestly cleared",
        ],
        "explicitly_not_now": [
            "physical migration or cross-repo rewrite",
            "mixing display or paper-figure assetization into the runtime mainline",
            "claiming MedDeepScientist has already exited",
            "treating MedDeepScientist as a second long-term owner or parallel product surface",
            "claiming upstream Hermes already fully replaces the research executor",
            "claiming a standalone OPL/MAS product frontend is already landed",
        ],
        "source_docs": [
            "README.md",
            "docs/README.md",
            "docs/project.md",
            "docs/architecture.md",
            "docs/status.md",
            "docs/runtime/agent_runtime_interface.md",
            "docs/references/lightweight_product_entry_and_opl_handoff.md",
        ],
        "commands": {
            "mainline_status": "uv run python -m med_autoscience.cli mainline-status",
            "workspace_cockpit": "uv run python -m med_autoscience.cli workspace-cockpit --profile <profile>",
            "study_progress": "uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>",
        },
    }


def read_mainline_phase_status(selector: str = "current") -> dict[str, Any]:
    payload = read_mainline_status()
    phase_ladder = [dict(item) for item in payload.get("phase_ladder") or [] if isinstance(item, dict)]
    if not phase_ladder:
        raise ValueError("mainline phase ladder is empty")
    current_phase_id = str(((payload.get("current_program_phase") or {}).get("id")) or "").strip()

    selected_phase: dict[str, Any] | None = None
    normalized_selector = str(selector or "current").strip() or "current"
    if normalized_selector == "current":
        selected_phase = next((item for item in phase_ladder if item.get("id") == current_phase_id), None)
    elif normalized_selector == "next":
        current_index = next((index for index, item in enumerate(phase_ladder) if item.get("id") == current_phase_id), -1)
        if 0 <= current_index < len(phase_ladder) - 1:
            selected_phase = phase_ladder[current_index + 1]
    else:
        selected_phase = next((item for item in phase_ladder if item.get("id") == normalized_selector), None)
    if selected_phase is None:
        raise ValueError(f"unknown mainline phase selector: {normalized_selector}")

    return {
        "schema_version": payload.get("schema_version"),
        "generated_at": payload.get("generated_at"),
        "program_id": payload.get("program_id"),
        "current_stage": dict(payload.get("current_stage") or {}),
        "current_program_phase": dict(payload.get("current_program_phase") or {}),
        "phase": selected_phase,
        "source_docs": list(payload.get("source_docs") or []),
    }


def render_mainline_phase_markdown(payload: dict[str, Any]) -> str:
    phase = dict(payload.get("phase") or {})
    single_project_boundary = dict(phase.get("single_project_boundary") or {})
    lines = [
        "# Mainline Phase",
        "",
        f"- 当前 program: `{payload.get('program_id')}`",
        f"- 当前阶段: `{phase.get('id')}`",
        f"- 当前状态: {_phase_status_label(phase.get('status'))}",
        f"- 当前可用性: {_bool_label(phase.get('usable_now'))}",
        f"- 当前摘要: {phase.get('summary') or 'none'}",
    ]
    if single_project_boundary:
        lines.extend(
            [
                "",
                "## 当前 tranche 边界",
                "",
                f"- 当前摘要: {single_project_boundary.get('summary') or 'none'}",
                f"- MAS owner modules: `{', '.join(single_project_boundary.get('mas_owner_modules') or []) or 'none'}`",
            ]
        )
        for item in single_project_boundary.get("land_now") or []:
            lines.append(f"- 当前 tranche 收口: {item}")
        for item in single_project_boundary.get("mds_retained_roles") or []:
            if not isinstance(item, dict):
                continue
            lines.append(f"- MDS 保留 `{item.get('role_id')}`: {item.get('summary') or 'none'}")
        for item in single_project_boundary.get("post_gate_only") or []:
            lines.append(f"- post-gate only: {item}")
        for item in single_project_boundary.get("not_now") or []:
            lines.append(f"- 当前不允许: {item}")
    lines.extend(["", "## 可用入口", ""])
    entry_points = list(phase.get("entry_points") or [])
    if entry_points:
        for item in entry_points:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {_entry_point_label(item.get('name'))}: `{item.get('command') or 'none'}`")
            purpose = str(item.get("purpose") or "").strip()
            if purpose:
                lines.append(f"  入口说明: {purpose}")
    else:
        lines.append("- none")
    lines.extend(["", "## 退出条件", ""])
    exit_criteria = list(phase.get("exit_criteria") or [])
    if exit_criteria:
        for item in exit_criteria:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## 相关文档", ""])
    phase_docs = list(phase.get("phase_docs") or [])
    if phase_docs:
        for item in phase_docs:
            lines.append(f"- `{item}`")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def render_mainline_status_markdown(payload: dict[str, Any]) -> str:
    current_stage = dict(payload.get("current_stage") or {})
    current_program_phase = dict(payload.get("current_program_phase") or {})
    runtime_topology = dict((payload.get("ideal_state") or {}).get("runtime_topology") or {})
    single_project_boundary = dict(payload.get("single_project_boundary") or {})
    phase2_user_product_loop = dict(payload.get("phase2_user_product_loop") or {})
    phase3_clearance_lane = dict(payload.get("phase3_clearance_lane") or {})
    phase4_backend_deconstruction = dict(payload.get("phase4_backend_deconstruction") or {})
    platform_target = dict(payload.get("platform_target") or {})
    lines = [
        "# Mainline Status",
        "",
        f"- 当前 program: `{payload.get('program_id')}`",
        f"- 当前主线阶段: `{current_stage.get('id')}`",
        f"- 当前状态: {_phase_status_label(current_stage.get('status'))}",
        f"- 当前判断: {current_stage.get('summary') or 'none'}",
        f"- 当前 program phase: `{current_program_phase.get('id')}`",
        f"- program phase 状态: {_phase_status_label(current_program_phase.get('status'))}",
        "",
        "## 理想目标",
        "",
        f"- 域入口归属: {runtime_topology.get('domain_gateway') or 'none'}",
        f"- 外环运行基座: {runtime_topology.get('outer_runtime_substrate_owner') or 'none'}",
        f"- 研究后端: {runtime_topology.get('research_backend') or 'none'}",
        f"- 入口形态: {runtime_topology.get('entry_shape') or 'none'}",
        "",
        "## Single-Project Boundary",
        "",
        f"- 当前摘要: {single_project_boundary.get('summary') or 'none'}",
        f"- MAS owner modules: `{', '.join(single_project_boundary.get('mas_owner_modules') or []) or 'none'}`",
        "",
        "## Phase 2 User Loop",
        "",
        f"- program phase 摘要: {phase2_user_product_loop.get('summary') or 'none'}",
        f"- 推荐动作: `{phase2_user_product_loop.get('recommended_step_id') or 'none'}`",
        f"- 推荐命令: `{phase2_user_product_loop.get('recommended_command') or 'none'}`",
        "",
        "## Phase 3 Clearance",
        "",
        f"- 清障重点: {phase3_clearance_lane.get('summary') or 'none'}",
        f"- 推荐动作: `{phase3_clearance_lane.get('recommended_step_id') or 'none'}`",
        f"- 推荐命令: `{phase3_clearance_lane.get('recommended_command') or 'none'}`",
    ]
    for item in phase2_user_product_loop.get("single_path") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 单一路径 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    for item in phase3_clearance_lane.get("clearance_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    for item in phase3_clearance_lane.get("clearance_loop") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- 清障步骤 `{item.get('step_id')}`: `{item.get('command') or 'none'}`")
    for item in single_project_boundary.get("mds_retained_roles") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- MDS retained `{item.get('role_id')}`: {item.get('summary') or 'none'}")
    for item in single_project_boundary.get("land_now") or []:
        lines.append(f"- 当前 tranche 落点: {item}")
    for item in single_project_boundary.get("post_gate_only") or []:
        lines.append(f"- post-gate only: {item}")
    for item in single_project_boundary.get("not_now") or []:
        lines.append(f"- 当前不允许: {item}")
    lines.extend(
        [
            "",
            "## Phase 4 Deconstruction",
            "",
            f"- 当前摘要: {phase4_backend_deconstruction.get('summary') or 'none'}",
        ]
    )
    for item in phase4_backend_deconstruction.get("substrate_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('capability_id')}`: {item.get('summary') or 'none'}")
    lines.extend(
        [
            "",
            "## Platform Target",
            "",
            f"- 当前平台目标: `{platform_target.get('surface_kind') or 'none'}`",
            f"- 当前摘要: {platform_target.get('summary') or 'none'}",
            f"- 当前序列范围: {_sequence_scope_label(platform_target.get('sequence_scope'))}",
            f"- 当前步骤: `{platform_target.get('current_step_id') or 'none'}`",
            f"- 当前就绪判断: {platform_target.get('current_readiness_summary') or 'none'}",
            f"- monorepo 目标状态: {_monorepo_status_label((platform_target.get('north_star_topology') or {}).get('monorepo_status'))}",
            f"- 推荐 phase 命令: `{platform_target.get('recommended_phase_command') or 'none'}`",
            "",
            "## Monorepo Sequence",
            "",
        ]
    )
    landing_sequence = list(platform_target.get("landing_sequence") or [])
    if landing_sequence:
        for item in landing_sequence:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('step_id')}` [{_phase_status_label(item.get('status'))}] / `{item.get('phase_id')}`: {item.get('summary') or 'none'}"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Program Phases", ""])
    for item in payload.get("phase_ladder") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('id')}` [{_phase_status_label(item.get('status'))}]: {item.get('summary')}")
    lines.extend([
        "",
        "## Completed Tranches",
        "",
    ])
    for item in payload.get("completed_tranches") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('id')}`: {item.get('summary')}")
    lines.extend(["", "## Remaining Gaps", ""])
    for item in payload.get("remaining_gaps") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Next Focus", ""])
    for item in payload.get("next_focus") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Not Now", ""])
    for item in payload.get("explicitly_not_now") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Key Docs", ""])
    for item in payload.get("source_docs") or []:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"
