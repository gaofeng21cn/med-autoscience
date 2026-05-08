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

from med_autoscience.controllers.mainline_status_parts.labels import _non_empty_text
from med_autoscience.controllers.mainline_status_parts.rendering import (
    render_mainline_phase_markdown,
    render_mainline_status_markdown,
)
from med_autoscience.controllers.mainline_status_parts.unified_enhancement import (
    build_unified_enhancement_program_projection,
)


SCHEMA_VERSION = 1
PROGRAM_ID = "research-foundry-medical-mainline"
CURRENT_STAGE_ID = "mas_owner_truth_hardening"
CURRENT_STAGE_STATUS = "in_progress"
CURRENT_PROGRAM_PHASE_ID = "phase_1_mainline_established"
CURRENT_PROGRAM_PHASE_STATUS = "in_progress"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _build_backend_deconstruction_lane(
    *,
    deconstruction_map_ref: str,
    **kwargs: Any,
) -> dict[str, Any]:
    payload = _build_shared_backend_deconstruction_lane(
        **kwargs,
        deconstruction_map_doc=deconstruction_map_ref,
    )
    payload["deconstruction_map_ref"] = str(
        payload.pop("deconstruction_map_doc", deconstruction_map_ref)
    )
    return payload


def _single_project_boundary() -> dict[str, Any]:
    return {
        "surface_kind": "single_project_boundary",
        "summary": (
            "当前 tranche 收口的是 MAS 单项目 owner truth、repo-tracked program truth 与用户可见边界；"
            "MDS no-history absorb 已完成 repo-level closeout，更大的平台/runtime ingest 继续作为后置扩展。"
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
                "summary": "只保留显式 backend audit / legacy diagnostic / oracle reference，不再是默认运行依赖。",
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
            "core:status:program_mainline_boundary_alignment",
            "user-visible wording that MDS is no longer a second long-term owner",
            "MDS no-history physical absorb repo-level closeout and default dependency retirement",
        ],
        "post_gate_only": [
            "runtime core ingest across repos",
            "broader platform/federation restructuring after earlier phases hold",
        ],
        "not_now": [
            "treating MedDeepScientist as a second long-term owner",
            "using monorepo language as shorthand for current tranche completion",
        ],
    }


def _capability_owner_boundary() -> dict[str, Any]:
    return {
        "surface_kind": "mas_capability_owner_boundary",
        "owner": "MedAutoScience",
        "summary": (
            "调用方应把研究入口、task intake、controller outer loop、进度真相、论文质量门控、"
            "runtime recovery 与 program/mainline 解释都读作 MAS-owned capability；"
            "MDS 只保留 optional backend audit / oracle / intake 角色。"
        ),
        "mas_owned_capabilities": [
            {
                "capability_id": "research_entry",
                "owner": "MedAutoScience",
                "truth_surface": "product-entry-status / workspace-cockpit",
                "summary": "正式研究入口与 direct / OPL handoff 语义归 MAS。",
            },
            {
                "capability_id": "study_task_intake",
                "owner": "MedAutoScience",
                "truth_surface": "submit-study-task + artifacts/controller/task_intake/latest.json",
                "summary": "用户任务、研究目标和交付要求先写入 MAS durable task intake。",
            },
            {
                "capability_id": "controller_outer_loop",
                "owner": "MedAutoScience",
                "truth_surface": "controller_decisions/latest.json",
                "summary": "研究续跑、恢复、human gate 与后续动作由 MAS controller 解释。",
            },
            {
                "capability_id": "progress_truth_projection",
                "owner": "MedAutoScience",
                "truth_surface": "study-progress / workspace-cockpit",
                "summary": "当前阶段、阻塞、恢复点、同线路由和质量跟进由 MAS progress surface 投影。",
            },
            {
                "capability_id": "publication_quality_gate",
                "owner": "MedAutoScience",
                "truth_surface": "publication_eval/latest.json + publication_gate",
                "summary": "医学论文质量、同线修复、有限补充分析和投稿前审计归 MAS quality contract。",
            },
            {
                "capability_id": "runtime_recovery",
                "owner": "MedAutoScience",
                "truth_surface": "study_runtime_status / runtime_watch",
                "summary": "运行恢复、supervision freshness 与下一次确认信号由 MAS runtime surfaces 解释。",
            },
            {
                "capability_id": "program_mainline_truth",
                "owner": "MedAutoScience",
                "truth_surface": "mainline-status / mainline-phase",
                "summary": "program 阶段、owner boundary、proof 口径和 post-gate 边界归 MAS mainline surfaces。",
            },
        ],
        "mds_migration_only_roles": [
            {
                "role_id": "research_backend",
                "migration_only": True,
                "summary": "只服务显式 backend audit 与 legacy diagnostic；不拥有默认执行、用户入口或治理判断。",
            },
            {
                "role_id": "behavior_equivalence_oracle",
                "migration_only": True,
                "summary": "作为行为等价与回归 oracle；不替代 MAS durable truth。",
            },
            {
                "role_id": "upstream_intake_buffer",
                "migration_only": True,
                "summary": "承接上游 DeepScientist / MDS 输入，经过 MAS 审计后才吸收。",
            },
        ],
        "proof_and_absorb_boundary": {
            "surface_kind": "proof_and_absorb_boundary",
            "parity_status": "landed_for_retained_mds_capabilities",
            "parity_proof_sources": [
                "behavior_equivalence_oracle",
                "study_progress_projection_contract",
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "docs/references/med-deepscientist/source_provenance.json",
            ],
            "physical_absorb_status": "landed_no_history_default_dependency_retired",
            "physical_absorb_gate": [
                "source provenance recorded",
                "author audit guard enforced",
                "retained capability parity proven",
                "external MDS default dependency retired",
            ],
            "platform_maturation_status": "future_runtime_core_ingest_post_gate",
        },
        "not_authority": [
            "MedDeepScientist product entry",
            "MedDeepScientist long-term governance surface",
            "external MDS checkout as default runtime requirement",
        ],
    }


def _phase_single_project_boundary(phase_id: object) -> dict[str, Any] | None:
    if _non_empty_text(phase_id) != "phase_1_mainline_established":
        return None
    return _single_project_boundary()


def _phase_capability_owner_boundary(phase_id: object) -> dict[str, Any] | None:
    if _non_empty_text(phase_id) != "phase_1_mainline_established":
        return None
    return _capability_owner_boundary()


def _active_tranche_owner_truth() -> dict[str, Any]:
    return {
        "surface_kind": "active_tranche_owner_truth",
        "owner": "MedAutoScience",
        "stage_id": CURRENT_STAGE_ID,
        "summary": (
            "当前 tranche 用 autonomy、quality、single-project owner 三线解释 MAS owner truth；"
            "MedDeepScientist 只保留迁移期 backend、oracle、intake buffer 角色。"
        ),
        "lanes": [
            {
                "lane_id": "autonomy",
                "title": "Autonomy lane",
                "owner": "MAS controller/runtime",
                "summary": (
                    "自治推进、runtime recovery、progress freshness 与 human gate 原因继续由 MAS "
                    "controller-owned durable surfaces 解释。"
                ),
                "truth_surfaces": [
                    "study_runtime_status",
                    "runtime_watch",
                    "study-progress.autonomy_contract",
                    "controller_decisions/latest.json",
                ],
            },
            {
                "lane_id": "quality",
                "title": "Quality lane",
                "owner": "MAS quality contract",
                "summary": (
                    "论文质量、同线修复、有限补充分析与投稿前审计继续落在 MAS study charter、"
                    "evidence/review ledger 和 publication gate truth 上。"
                ),
                "truth_surfaces": [
                    "study_charter",
                    "paper evidence ledger",
                    "review ledger",
                    "publication_eval/latest.json",
                    "publication_gate",
                ],
            },
            {
                "lane_id": "single_project_owner",
                "title": "Single-project owner lane",
                "owner": "MAS single-project program",
                "summary": (
                    "单项目 owner truth 继续由 MAS mainline-status/mainline-phase 暴露；"
                    "MDS 不新增第二治理面或并行产品入口。"
                ),
                "truth_surfaces": [
                    "mainline-status",
                    "mainline-phase",
                    "single_project_boundary",
                ],
            },
        ],
        "mds_retained_roles": list(_single_project_boundary()["mds_retained_roles"]),
        "not_owner_surfaces": [
            "MedDeepScientist product entry",
            "MedDeepScientist long-term governance surface",
            "parallel owner truth outside MAS",
        ],
    }


def _platform_target() -> dict[str, Any]:
    return _build_shared_platform_target(
        summary=(
            "Phase 5 的目标是把 MAS 继续收敛到 federation/platform-ready 形态，包括 runtime core ingest、"
            "更成熟的 direct product entry 和外部 runtime substrate 选择；这些必须建立在前四阶段真实成立之后。"
        ),
        sequence_scope="monorepo_landing_readiness",
        current_step_id="stabilize_user_product_loop",
        current_readiness_summary=(
            "单项目长线已经完成 gateway/runtime truth 冻结，当前正在推进 user product loop hardening 与边界收紧；"
            "MDS no-history absorb 已关闭为默认依赖退役，后续平台化不再以 external MDS 为默认运行条件。"
        ),
        north_star_topology={
            "domain_gateway": "Med Auto Science",
            "outer_runtime_substrate_owner": "upstream Hermes-Agent",
            "controlled_research_backend": "MAS-owned runtime/artifact/quality surfaces plus optional MDS oracle",
            "monorepo_status": "no_history_absorb_landed",
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
                summary=(
                    "当前活跃步骤：用 autonomy / quality / single-project owner 三线继续收紧 MAS "
                    "owner truth，并把启动 / 下任务 / 看进度 / 看恢复建议收成稳定前台回路。"
                ),
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
                step_id="mds_no_history_absorb",
                title="MDS no-history absorb",
                status="completed",
                phase_id="phase_5_federation_platform_maturation",
                summary="MDS retained capability 已通过 no-history provenance、author guard、parity harness 和 external dependency retirement 收口到 MAS。",
            ),
            _build_shared_program_sequence_step(
                step_id="runtime_core_ingest",
                title="Runtime core ingest",
                status="pending",
                phase_id="phase_5_federation_platform_maturation",
                summary="更大的 runtime core ingest / platform maturation 仍需独立 gate，且不得把 external MDS 恢复为默认依赖。",
            ),
        ],
        completed_step_ids=[
            "freeze_gateway_runtime_truth",
            "mds_no_history_absorb",
        ],
        remaining_step_ids=[
            "clear_multi_workspace_host_gate",
            "freeze_backend_deconstruction_boundary",
            "runtime_core_ingest",
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
            "runtime core ingest across repos",
            "mature hosted standalone medical frontend",
        ],
    )


def build_phase2_user_product_loop_lane(
    *,
    entry_status_command: str,
    workspace_cockpit_command: str,
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
        "single_path": [
            {
                "step_id": "open_product_entry",
                "title": "先打开 MAS 产品入口",
                "surface_kind": "product_entry_status",
                "command": entry_status_command,
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
                "answer_surface_kind": "product_entry_status",
                "command": entry_status_command,
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
                "surface_kind": "product_entry_status",
                "command": entry_status_command,
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
        entry_status_command="uv run python -m med_autoscience.cli product-entry-status --profile <profile>",
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
    return _build_backend_deconstruction_lane(
        summary="Phase 4 把可迁出的通用 runtime 能力继续迁向 substrate，同时把 MDS 保持为 optional oracle / intake / diagnostic reference。",
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
            "optional MedDeepScientist backend audit",
            "legacy restore/import diagnostic",
            "behavior-equivalence oracle fixtures",
        ],
        current_backend_chain=[
            "med_autoscience runtime surfaces -> MAS-owned Runtime OS / Artifact OS / Quality OS",
            "optional med_deepscientist oracle/intake/audit reference",
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
            "no claim of platform runtime ingest without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "do not restore external MDS as a default runtime dependency",
        ],
        deconstruction_map_ref="program:med_deepscientist_deconstruction_map",
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
                "并把当前 owner truth 显式收成 autonomy、quality、single-project owner 三线；MDS no-history absorb 已关闭默认依赖。"
            ),
            "focus": [
                "autonomy: keep runtime truth, recovery proof, and progress freshness controller-owned",
                "quality: keep publication-grade quality route truth under MAS study contracts",
                "single-project owner: keep MDS retained as optional audit/oracle/intake reference only",
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
                "autonomy / quality / single-project owner 三线都能从 mainline-status 与 mainline-phase 直接读出。",
                "当前活跃 study 的主要阻塞继续前移到 publication / completion / human-gate truth。",
                "用户已经能稳定看到主线状态、workspace attention 和 study progress，且不会被引向 MDS 第二治理面。",
            ],
            "phase_refs": [
                "core:status",
                "core:project",
                "core:architecture",
            ],
            "active_tranche_owner_truth": _active_tranche_owner_truth(),
            "single_project_boundary": _phase_single_project_boundary("phase_1_mainline_established"),
            "capability_owner_boundary": _phase_capability_owner_boundary("phase_1_mainline_established"),
        },
        {
            "id": "phase_2_user_product_loop",
            "title": "Phase 2 user product loop",
            "status": "pending",
            "usable_now": True,
            "summary": "把启动、下任务、持续看进度、看告警、看恢复建议收成稳定用户回路，并把 MDS 压回 optional backend-audit/oracle/intake 语义。",
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
            "phase_refs": [
                "docs:index",
                "runtime:agent_interface",
                "reference:opl_handoff",
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
            "phase_refs": [
                "docs:index",
                "core:status",
                "program:external_runtime_dependency_gate",
                "program:upstream_hermes_agent_fast_cutover_board",
            ],
        },
        {
            "id": "phase_4_backend_deconstruction",
            "title": "Phase 4 backend deconstruction",
            "status": "pending",
            "usable_now": True,
            "summary": "在 outer runtime 与产品回路稳定后，继续把 MDS 保持为 optional oracle/intake/diagnostic reference，并只对新的可迁能力走 no-history provenance 与 parity gate。",
            "focus": [
                "move any newly reusable runtime capability into MAS-owned surfaces only with provenance and proof",
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
                    "command": "uv run python -m med_autoscience.cli mainline-status",
                    "purpose": "核对 backend deconstruction 的 program reference 与后续替换边界。",
                },
            ],
            "exit_criteria": [
                "迁出的能力有明确 owner、contract、tests 和 proof surface。",
                "MedDeepScientist 保持 optional oracle / intake / diagnostic reference，而不是 hidden runtime authority。",
                "executor replacement 不依赖一次性重写或 truth rewrite。",
            ],
            "phase_refs": [
                "docs:index",
                "core:project",
                "program:med_deepscientist_deconstruction_map",
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
                "treat runtime core ingest and large platform restructures as independent post-gate work",
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
            "phase_refs": [
                "docs:index",
                "core:project",
                "program:research_foundry_medical_mainline",
            ],
        },
    ]


def read_mainline_status() -> dict[str, Any]:
    phase_ladder = _phase_ladder()
    unified_enhancement_program = build_unified_enhancement_program_projection()
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
                "research_backend": "MAS-owned runtime/artifact/quality surfaces plus optional MDS oracle",
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
        "capability_owner_boundary": _capability_owner_boundary(),
        "active_tranche_owner_truth": _active_tranche_owner_truth(),
        "current_stage": {
            "id": CURRENT_STAGE_ID,
            "status": CURRENT_STAGE_STATUS,
            "title": "MAS owner truth hardening",
            "summary": (
                "repo-side 已拿到 external Hermes runtime truth、real adapter cutover 和至少一条真实 study "
                "recovery/proof；当前主线用 autonomy、quality、single-project owner 三线继续压实 MAS owner truth，"
                "而不是回去继续做 seam-only 包装或新增 MDS 第二治理面。"
            ),
        },
        "current_program_phase": {
            "id": CURRENT_PROGRAM_PHASE_ID,
            "status": CURRENT_PROGRAM_PHASE_STATUS,
            "title": "Phase 1 mainline established",
            "summary": (
                "当前总体仍处在第一阶段尾声：主线已成立，正在把自治、质量与单项目 owner "
                "边界继续收成真实 repo-tracked truth。"
            ),
            "active_tranche_owner_truth": _active_tranche_owner_truth(),
            "single_project_boundary": _phase_single_project_boundary(CURRENT_PROGRAM_PHASE_ID),
            "capability_owner_boundary": _phase_capability_owner_boundary(CURRENT_PROGRAM_PHASE_ID),
        },
        "phase2_user_product_loop": _phase2_user_product_loop(),
        "phase3_clearance_lane": _phase3_clearance_lane(),
        "phase4_backend_deconstruction": _phase4_backend_deconstruction(),
        "platform_target": _platform_target(),
        "unified_enhancement_program": unified_enhancement_program,
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
            "autonomy: keep task, progress, supervision, stuck-state, recovery, and human-gate truth visible through MAS durable surfaces",
            "quality: keep publication-grade route truth, same-line repair, bounded analysis, and submission readiness under MAS quality contracts",
            "single-project owner: keep MedDeepScientist pinned to optional audit / oracle / intake roles instead of second-owner language",
            "keep core status and runtime contracts aligned so OPL language, MAS role, and runtime truth do not drift",
            "only move toward broader runtime core ingest or platform work after the external gate is honestly cleared",
        ],
        "explicitly_not_now": [
            "large platform rewrite without a separate owner/proof gate",
            "mixing display or paper-figure assetization into the runtime mainline",
            "claiming the external MedDeepScientist reference repo must be deleted for MAS default operation to work",
            "treating MedDeepScientist as a second long-term owner or parallel product surface",
            "claiming upstream Hermes already fully replaces the research executor",
            "claiming a standalone OPL/MAS product frontend is already landed",
        ],
        "source_refs": [
            "readme:root",
            "docs:index",
            "core:project",
            "core:architecture",
            "core:status",
            "runtime:agent_interface",
            "program:mas_mds_unified_enhancement_program",
            "reference:opl_handoff",
        ],
        "commands": {
            "mainline_status": "uv run python -m med_autoscience.cli mainline-status",
            "unified_enhancement_program": "uv run python -m med_autoscience.cli mainline-status --format json",
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
        "source_refs": list(payload.get("source_refs") or []),
    }
