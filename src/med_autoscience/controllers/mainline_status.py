from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from opl_harness_shared.product_entry_program_companions import (
    build_clearance_lane as _build_shared_clearance_lane,
    build_clearance_target as _build_shared_clearance_target,
    build_platform_target as _build_shared_platform_target,
    build_product_entry_program_step as _build_shared_product_entry_program_step,
    build_product_entry_program_surface as _build_shared_product_entry_program_surface,
    build_program_capability as _build_shared_program_capability,
    build_program_sequence_step as _build_shared_program_sequence_step,
    build_source_provenance_surface as _build_shared_source_provenance_surface,
)

from med_autoscience.runtime_backend import MAS_RUNTIME_OWNER, MAS_RUNTIME_SUBSTRATE
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
    _build_shared_source_provenance_surface(
        summary=str(kwargs["summary"]),
        source_provenance_ref={
            "surface_kind": "source_provenance",
            "ref": deconstruction_map_ref,
        },
        historical_fixture_ref={
            "surface_kind": "historical_fixture_ref",
            "ref": "fixtures/med-deepscientist/parity/",
        },
        explicit_archive_import_ref={
            "surface_kind": "explicit_archive_import_ref",
            "command": "uv run python -m med_autoscience.cli backend-audit --mode archive-import",
        },
        parity_oracle_ref={
            "surface_kind": "parity_oracle_ref",
            "ref": "program:med_deepscientist_retained_capability_parity",
        },
        authority_boundary=[
            "opl_provider_runtime_is_default_generic_owner",
            "source_refs_do_not_define_runtime_dependency",
            "archive_import_is_explicit_one_way_provenance",
        ],
        capability_classification="source_provenance_only",
        recommended_audit_command="uv run python -m med_autoscience.cli backend-audit",
    )
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


def _single_project_boundary() -> dict[str, Any]:
    return {
        "surface_kind": "single_project_boundary",
        "summary": (
            "MAS functional monolith completion 已落地：默认运行、诊断、进度可视化、"
            "artifact/quality/status/progress/cockpit/OPL handoff 都由 MAS-owned surface 承接。"
        ),
        "mas_owner_modules": [
            "controller_charter",
            "runtime",
            "eval_hygiene",
        ],
        "mds_retained_roles": [
            {
                "role_id": "external_source_archive",
                "title": "Frozen source archive",
                "summary": "只保留 source provenance、hash、license refs 和 historical audit context；不作为 runnable dependency。",
            },
            {
                "role_id": "historical_fixture_ref",
                "title": "Historical fixture reference",
                "summary": "只作为 retained capability parity fixture；不能运行成默认 daemon、WebUI 或研究执行后端。",
            },
            {
                "role_id": "explicit_archive_import_ref",
                "title": "Explicit archive import reference",
                "summary": "仅限显式 archive import 或 backend audit 读取；默认 MAS 诊断不要求外部 MDS checkout。",
            },
        ],
        "land_now": [
            "MAS functional monolith completion landed",
            "MAS domain owner receipts and progress truth surfaces are the default research authority",
            "MAS Progress Portal is the default visual status surface",
            "OPL handoff consumes MAS payload refs/freshness/source refs/artifact locators only",
            "external MDS repo, daemon, runtime root, and WebUI are no longer required for default or diagnostic operation",
        ],
        "post_gate_only": [
            "new upstream intake from future MDS/DeepScientist snapshots",
            "optional hosted/stage-runtime frontend work outside MAS truth authority",
        ],
        "not_now": [
            "treating MedDeepScientist as a second long-term owner",
            "restoring external MDS as hidden runnable substitute",
            "importing upstream git history or contributor footprint",
        ],
    }


def _capability_owner_boundary() -> dict[str, Any]:
    return {
        "surface_kind": "mas_capability_owner_boundary",
        "owner": "MedAutoScience",
        "summary": (
            "调用方应把研究入口、task intake、controller outer loop、进度真相、论文质量门控、"
            "runtime recovery 与 program/mainline 解释都读作 MAS-owned capability；"
            "MDS 只保留 frozen archive / historical fixture / explicit archive import reference 角色。"
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
                "truth_surface": "MAS domain runtime receipts / study_runtime_status / runtime_watch",
                "summary": (
                    "运行恢复、supervision freshness、worker/session replay 与下一次确认信号由 MAS "
                    "domain owner surface 解释；generic cadence/provider SLO 迁往 OPL runtime manager。"
                ),
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
                "role_id": "external_source_archive",
                "migration_only": True,
                "summary": "只服务 provenance、license refs、source hash 和历史审计；不拥有默认执行或诊断入口。",
            },
            {
                "role_id": "historical_fixture_ref",
                "migration_only": True,
                "summary": "只作为 historical fixture / parity proof input；不替代 MAS durable truth。",
            },
            {
                "role_id": "explicit_archive_import_ref",
                "migration_only": True,
                "summary": "只在操作者显式 archive import / backend audit 时读取；不作为 hidden runnable substitute。",
            },
        ],
        "proof_and_absorb_boundary": {
            "surface_kind": "proof_and_absorb_boundary",
            "parity_status": "landed_for_retained_mds_capabilities",
            "parity_proof_sources": [
                "historical_fixture_ref",
                "study_progress_projection_contract",
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "docs/references/med-deepscientist/source_provenance.json",
            ],
            "physical_absorb_status": "landed_no_history_functional_monolith",
            "physical_absorb_gate": [
                "source provenance recorded",
                "author audit guard enforced",
                "retained capability parity proven",
                "external MDS default dependency retired",
                "external MDS diagnostic dependency retired",
                "old MDS WebUI default path retired",
            ],
            "platform_maturation_status": "functional_monolith_landed_platform_frontend_optional",
        },
        "not_authority": [
            "MedDeepScientist product entry",
            "MedDeepScientist long-term governance surface",
            "external MDS checkout as default runtime or diagnostic requirement",
            "external MDS daemon or WebUI as default progress surface",
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
            "MedDeepScientist 只保留 archive、historical fixture、explicit archive import reference 角色。"
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
            "Phase 5 已完成 MAS functional monolith closeout；后续平台工作只剩 optional hosted/stage-runtime "
            "frontend 与 future upstream intake，不再以 external MDS runtime core 为默认运行条件。"
        ),
        sequence_scope="monorepo_landing_readiness",
        current_step_id="functional_monolith_completion",
        current_readiness_summary=(
            "MAS 默认研究入口、进度、诊断、artifact/quality parity、workspace helpers 与 OPL handoff 都已切到 MAS-owned domain surfaces；"
            "external MDS 只保留 frozen archive / historical fixture / explicit archive import reference。"
        ),
        north_star_topology={
            "domain_agent": "Med Auto Science",
            "runtime_owner": MAS_RUNTIME_OWNER,
            "runtime_substrate": MAS_RUNTIME_SUBSTRATE,
            "controlled_research_backend": (
                "MAS domain owner receipts / Artifact authority refs / Quality verdict refs; "
                "generic runtime lifecycle handoff to OPL"
            ),
            "monorepo_status": "functional_monolith_completion_landed",
        },
        target_internal_modules=[
            "controller_charter",
            "runtime",
            "eval_hygiene",
        ],
        landing_sequence=[
            _build_shared_program_sequence_step(
                step_id="freeze_stage_runtime_truth",
                title="Freeze stage-runtime truth",
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
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="MDS retained capability 已通过 no-history provenance、author guard、parity harness 和 external dependency retirement 收口到 MAS。",
            ),
            _build_shared_program_sequence_step(
                step_id="runtime_core_ingest",
                title="Runtime core ingest",
                status="completed",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary=(
                    "默认 domain runtime receipts 已由 MAS 承接；external MDS daemon/runtime root "
                    "不再是默认运行或诊断依赖。"
                ),
            ),
            _build_shared_program_sequence_step(
                step_id="functional_monolith_completion",
                title="Functional monolith completion",
                status="completed",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="MAS 默认 CLI/MCP/product-entry/workspace helper/Progress Portal/OPL handoff 都不要求外部 MDS repo、daemon 或 WebUI。",
            ),
            _build_shared_program_sequence_step(
                step_id="optional_hosted_frontend_packaging",
                title="Optional hosted frontend packaging",
                status="pending",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="后续可把 MAS Progress Portal / OPL dashboard 打包成 hosted frontend，但不得重解释 MAS study truth。",
            ),
            _build_shared_program_sequence_step(
                step_id="future_upstream_source_intake_review",
                title="Future upstream source intake review",
                status="pending",
                phase_id="phase_5_stage_runtime_platform_maturation",
                summary="未来如需吸收 MDS/DeepScientist 新 snapshot，只能走 no-history provenance、author audit 和 MAS-owned capability proof。",
            ),
        ],
        completed_step_ids=[
            "freeze_stage_runtime_truth",
            "mds_no_history_absorb",
            "runtime_core_ingest",
            "functional_monolith_completion",
        ],
        remaining_step_ids=[
            "optional_hosted_frontend_packaging",
            "future_upstream_source_intake_review",
        ],
        promotion_gates=[
            "phase_1_mainline_established",
            "phase_2_user_product_loop",
            "phase_3_multi_workspace_host_clearance",
            "phase_4_backend_deconstruction",
        ],
        recommended_phase_command=(
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_5_stage_runtime_platform_maturation"
        ),
        land_now=[
            "repo-tracked product-entry shell and family orchestration companions",
            "controller-owned runtime/progress/recovery truth",
            "CLI/MCP/controller entry surfaces that already support real work",
            "MAS-owned Progress Portal and OPL handoff refs",
        ],
        not_yet=[
            "mature hosted standalone medical frontend",
            "future upstream source intake beyond historical fixture/provenance refs",
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
    supervisor_service_command = "uv run python -m med_autoscience.cli runtime-supervision-status --profile <profile>"
    refresh_supervision_command = (
        "uv run python -m med_autoscience.cli watch --runtime-root <runtime_root> "
        "--profile <profile> --ensure-study-runtimes --apply-supervisor-platform-repair --apply"
    )
    launch_study_command = (
        "uv run python -m med_autoscience.cli launch-study --profile <profile> --study-id <study_id>"
    )
    study_progress_command = (
        "uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>"
    )
    return _build_shared_clearance_lane(
        surface_kind="phase3_host_clearance_lane",
        summary=(
            "Phase 3 只做可选 hosted runtime / 多宿主 proof；MAS 默认研究入口、owner receipt "
            "与 paper-progress SLO 由 MAS surface 承接，generic cadence/provider SLO 归 OPL runtime manager。"
        ),
        recommended_step_id="mas_runtime_contract",
        recommended_command=doctor_command,
        clearance_targets=[
            _build_shared_clearance_target(
                target_id="mas_runtime_contract",
                title="Check MAS runtime and legacy hosted-runtime tombstone contract",
                commands=[doctor_command],
            ),
            _build_shared_clearance_target(
                target_id="supervisor_service",
                title="Inspect OPL-owned supervision projection",
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
                step_id="mas_runtime_contract",
                title="确认 MAS runtime contract ready，旧 hosted runtime 仅保留 tombstone/provenance",
                surface_kind="doctor_runtime_contract",
                command=doctor_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="supervisor_service",
                title="确认 OPL replacement 与 MAS domain projection 在线",
                surface_kind="workspace_supervisor_service",
                command=supervisor_service_command,
            ),
            _build_shared_product_entry_program_step(
                step_id="refresh_supervision",
                title="刷新 MAS domain runtime projection",
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
                surface_kind="doctor.runtime_contract",
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
            "generic runtime/provider context -> OPL runtime manager handoff refs",
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


def _phase_ladder() -> list[dict[str, Any]]:
    return [
        {
            "id": "phase_1_mainline_established",
            "title": "Phase 1 mainline established",
            "status": "in_progress",
            "usable_now": True,
            "summary": (
                "MAS domain owner receipts / artifact authority refs / quality verdict refs 已承接默认研究进度真相，"
                "并把当前 owner truth 显式收成 autonomy、quality、single-project owner 三线。"
            ),
            "focus": [
                "autonomy: keep runtime truth, recovery proof, and progress freshness controller-owned",
                "quality: keep publication-grade quality route truth under MAS study contracts",
                "single-project owner: keep MDS retained as frozen archive / historical fixture / explicit archive import reference only",
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
                "clear broader optional hosted-runtime and workspace-specific blocker classes honestly",
            ],
            "entry_points": [
                {
                    "name": "doctor",
                    "command": "uv run python -m med_autoscience.cli doctor --profile <profile>",
                    "purpose": "先看 workspace / MAS runtime contract readiness。",
                },
                {
                    "name": "runtime_supervision_status",
                    "command": "uv run python -m med_autoscience.cli runtime-supervision-status --profile <profile>",
                    "purpose": "读取 OPL-owned supervision projection 与 legacy runtime tombstone。",
                },
                {
                    "name": "watch",
                    "command": "uv run python -m med_autoscience.cli watch --runtime-root <runtime_root> --profile <profile> --ensure-study-runtimes --apply-supervisor-platform-repair --apply",
                    "purpose": "验证 supervisor tick、恢复动作和 runtime reconciliation。",
                },
            ],
            "exit_criteria": [
                "optional hosted-runtime clearance 不再只依赖当前开发宿主。",
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
            "summary": (
                "在 MAS domain owner receipts、产品回路和 OPL scheduler replacement 证据稳定后，继续把 MDS "
                "保持为 archive/fixture/explicit archive import reference，并只对新的可迁能力走 no-history provenance 与 parity gate。"
            ),
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
                "MedDeepScientist 保持 frozen archive / historical fixture / explicit archive import reference，而不是 hidden runtime authority。",
                "executor replacement 不依赖一次性重写或 truth rewrite。",
            ],
            "phase_refs": [
                "docs:index",
                "core:project",
                "program:med_deepscientist_deconstruction_map",
            ],
        },
        {
            "id": "phase_5_stage_runtime_platform_maturation",
            "title": "Phase 5 stage-runtime integration and platform maturation",
            "status": "pending",
            "usable_now": True,
            "summary": "MAS functional monolith 已落地；后续只考虑 optional hosted frontend、stage-runtime direct entry 和 future upstream intake。",
            "focus": [
                "land broader stage-runtime-facing direct entry only after earlier phases hold",
                "keep future source intake and hosted frontend work outside MAS truth authority",
            ],
            "entry_points": [
                {
                    "name": "mainline_phase",
                    "command": "uv run python -m med_autoscience.cli mainline-phase --phase phase_5_stage_runtime_platform_maturation",
                    "purpose": "先看 stage-runtime / platform 这层现在仍然为什么是后置阶段。",
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
        "framework_position": {
            "opl": "Codex-first stage-led agent runtime framework",
            "research_foundry": "generic Research Ops framework layer",
            "med_autoscience": "independent medical research domain agent",
        },
        "ideal_state": {
            "north_star": (
                "把医学研究稳定推进成 publication-grade evidence chain、稿件、交付与长期可监管运行。"
            ),
            "runtime_topology": {
                "domain_agent": "Med Auto Science",
                "runtime_owner": MAS_RUNTIME_OWNER,
                "runtime_substrate": MAS_RUNTIME_SUBSTRATE,
                "research_backend": (
                    "MAS domain owner receipts / artifact authority refs / quality verdict refs; "
                    "generic runtime lifecycle handoff to OPL"
                ),
                "entry_shape": (
                    "Med Auto Science direct skill path plus OPL stage handoff over the same MAS-owned "
                    "stage/controller/durable truth surfaces, without replacing domain authority"
                ),
            },
            "product_shape": [
                "用户能直接启动、下任务、看进度、看监管在线态",
                "OPL 可把 domain handoff 送进 MAS，而不吞掉 MAS authority",
                "MAS 持续做 domain entry / outer-loop / publication judgment owner",
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
                "repo-side 已完成 MAS functional monolith closeout；当前主线用 autonomy、quality、"
                "single-project owner 三线继续压实 MAS owner truth，而不是回去新增 MDS 第二治理面。"
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
                "summary": "MAS 已收口为 Research Foundry 的独立医学 domain agent 与 Domain Harness OS。",
            },
            {
                "id": "f1_external_hermes_runtime_truth",
                "title": "F1 optional hosted runtime truth",
                "summary": "repo-side contract、doctor 与 runtime-check 已能 fail-closed 识别 optional hosted runtime evidence。",
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
            "OPL stage-runtime handoff is documented and contract-shaped, but not yet a live hosted front door",
            "optional hosted-runtime clearance still needs broader host/workspace proof; current MAS default runtime does not depend on it",
            "active study blockers still need continued closeout at publication / completion / human-gate truth surfaces",
        ],
        "next_focus": [
            "autonomy: keep task, progress, supervision, stuck-state, recovery, and human-gate truth visible through MAS durable surfaces",
            "quality: keep publication-grade route truth, same-line repair, bounded analysis, and submission readiness under MAS quality contracts",
            "single-project owner: keep MedDeepScientist pinned to archive / historical fixture / explicit archive import reference roles instead of second-owner language",
            "keep core status and runtime contracts aligned so OPL language, MAS role, and runtime truth do not drift",
            "only move toward hosted/stage-runtime frontend work without changing MAS truth authority",
        ],
        "explicitly_not_now": [
            "large platform rewrite without a separate owner/proof gate",
            "mixing display or paper-figure assetization into the runtime mainline",
            "claiming the external MedDeepScientist reference repo must be runnable for MAS default operation to work",
            "treating MedDeepScientist as a second long-term owner or parallel product surface",
            "claiming optional hosted runtime owns MAS research truth",
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
    selected_phase = _select_mainline_phase(
        phase_ladder=phase_ladder,
        current_phase_id=str(((payload.get("current_program_phase") or {}).get("id")) or "").strip(),
        selector=selector,
    )

    return _mainline_phase_status_payload(payload=payload, selected_phase=selected_phase)


def _select_mainline_phase(
    *,
    phase_ladder: list[dict[str, Any]],
    current_phase_id: str,
    selector: str,
) -> dict[str, Any]:
    normalized_selector = str(selector or "current").strip() or "current"
    if normalized_selector == "current":
        selected_phase = next((item for item in phase_ladder if item.get("id") == current_phase_id), None)
    elif normalized_selector == "next":
        selected_phase = _next_mainline_phase(phase_ladder=phase_ladder, current_phase_id=current_phase_id)
    else:
        selected_phase = next((item for item in phase_ladder if item.get("id") == normalized_selector), None)
    if selected_phase is None:
        raise ValueError(f"unknown mainline phase selector: {normalized_selector}")
    return selected_phase


def _next_mainline_phase(*, phase_ladder: list[dict[str, Any]], current_phase_id: str) -> dict[str, Any] | None:
    current_index = next((index for index, item in enumerate(phase_ladder) if item.get("id") == current_phase_id), -1)
    if 0 <= current_index < len(phase_ladder) - 1:
        return phase_ladder[current_index + 1]
    return None


def _mainline_phase_status_payload(*, payload: dict[str, Any], selected_phase: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": payload.get("schema_version"),
        "generated_at": payload.get("generated_at"),
        "program_id": payload.get("program_id"),
        "current_stage": dict(payload.get("current_stage") or {}),
        "current_program_phase": dict(payload.get("current_program_phase") or {}),
        "phase": selected_phase,
        "source_refs": list(payload.get("source_refs") or []),
    }
