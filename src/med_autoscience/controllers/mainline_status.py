from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from med_autoscience.opl_runtime_contract import OPL_HOSTED_STAGE_RUNTIME_ID, OPL_RUNTIME_OWNER
from med_autoscience.controllers.mainline_status_parts.labels import _non_empty_text
from med_autoscience.controllers.mainline_status_parts.program_surfaces import (
    build_phase2_user_product_loop,
    build_phase3_clearance_lane,
    build_phase4_backend_deconstruction,
    build_platform_target,
)
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
CURRENT_STAGE = {
    "id": CURRENT_STAGE_ID,
    "status": CURRENT_STAGE_STATUS,
    "title": "MAS owner truth hardening",
    "summary": (
        "repo-side 已完成 MAS functional monolith closeout；当前主线用 autonomy、quality、"
        "single-project owner 三线继续压实 MAS owner truth，而不是回去新增 MDS 第二治理面。"
    ),
}
CURRENT_PROGRAM_PHASE_BASE = {
    "id": CURRENT_PROGRAM_PHASE_ID,
    "status": CURRENT_PROGRAM_PHASE_STATUS,
    "title": "Phase 1 mainline established",
    "summary": (
        "当前总体仍处在第一阶段尾声：主线已成立，正在把自治、质量与单项目 owner "
        "边界继续收成真实 repo-tracked truth。"
    ),
}
CURRENT_REMAINING_GAPS = [
    "mature standalone medical product entry is still not landed; the truthful surface is still the repo-tracked shell plus agent-operated CLI/MCP",
    "OPL stage-runtime handoff is documented and contract-shaped, but not yet a live hosted front door",
    "optional hosted-runtime clearance still needs broader host/workspace proof; current MAS default runtime does not depend on it",
    "active study blockers still need continued closeout at publication / completion / human-gate truth surfaces",
]
CURRENT_NEXT_FOCUS = [
    "autonomy: keep task, progress, supervision, stuck-state, recovery, and human-gate truth visible through MAS durable surfaces",
    "quality: keep publication-grade route truth, same-line repair, bounded analysis, and submission readiness under MAS quality contracts",
    "single-project owner: keep MedDeepScientist pinned to archive / historical fixture / explicit archive import reference roles instead of second-owner language",
    "keep core status and runtime contracts aligned so OPL language, MAS role, and runtime truth do not drift",
    "only move toward hosted/stage-runtime frontend work without changing MAS truth authority",
]
CURRENT_EXPLICITLY_NOT_NOW = [
    "large platform rewrite without a separate owner/proof gate",
    "mixing display or paper-figure assetization into the runtime mainline",
    "claiming the external MedDeepScientist reference repo must be runnable for MAS default operation to work",
    "treating MedDeepScientist as a second long-term owner or parallel product surface",
    "claiming optional hosted runtime owns MAS research truth",
    "claiming a standalone OPL/MAS product frontend is already landed",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
            "domain recovery handoff 与 program/mainline 解释都读作 MAS-owned domain capability；"
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
                "truth_surface": "MAS domain runtime receipts / progress_projection / domain_health_diagnostic",
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
                "owner": "MAS domain controller + OPL runtime manager",
                "summary": (
                    "自治推进、domain recovery handoff、progress freshness 与 human gate 原因继续由 MAS "
                    "domain-authority refs 解释；queue、attempt、provider resume/relaunch 由 OPL 控制面持有。"
                ),
                "truth_surfaces": [
                    "progress_projection",
                    "domain_health_diagnostic",
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


def _phase2_user_product_loop() -> dict[str, Any]:
    return build_phase2_user_product_loop()


def _phase3_clearance_lane() -> dict[str, Any]:
    return build_phase3_clearance_lane()


def _phase4_backend_deconstruction() -> dict[str, Any]:
    return build_phase4_backend_deconstruction()


def _platform_target() -> dict[str, Any]:
    return build_platform_target()


def read_product_entry_mainline_projection() -> dict[str, Any]:
    current_program_phase = dict(CURRENT_PROGRAM_PHASE_BASE)
    current_program_phase.update(
        {
            "active_tranche_owner_truth": _active_tranche_owner_truth(),
            "single_project_boundary": _phase_single_project_boundary(CURRENT_PROGRAM_PHASE_ID),
            "capability_owner_boundary": _phase_capability_owner_boundary(CURRENT_PROGRAM_PHASE_ID),
        }
    )
    return {
        "program_id": PROGRAM_ID,
        "current_stage": dict(CURRENT_STAGE),
        "current_program_phase": current_program_phase,
        "single_project_boundary": _single_project_boundary(),
        "capability_owner_boundary": _capability_owner_boundary(),
        "platform_target": _platform_target(),
        "remaining_gaps": list(CURRENT_REMAINING_GAPS),
        "next_focus": list(CURRENT_NEXT_FOCUS),
        "explicitly_not_now": list(CURRENT_EXPLICITLY_NOT_NOW),
    }


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
                    "command": "uv run python -m med_autoscience.cli doctor mainline-status",
                    "purpose": "先看 repo 主线真相、当前 tranche 和 remaining gaps。",
                },
                {
                    "name": "workspace_cockpit",
                    "command": "uv run python -m med_autoscience.cli workspace cockpit --profile <profile>",
                    "purpose": "看当前 workspace 的监管、attention queue 和用户入口回路。",
                },
                {
                    "name": "study_progress",
                    "command": "uv run python -m med_autoscience.cli study progress --profile <profile> --study-id <study_id>",
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
                    "command": "uv run python -m med_autoscience.cli workspace cockpit --profile <profile>",
                    "purpose": "把 workspace-cockpit 当作当前用户 inbox 入口使用。",
                },
                {
                    "name": "submit_study_task",
                    "command": "uv run python -m med_autoscience.cli study submit-task --profile <profile> --study-id <study_id> --task-intent '<task_intent>'",
                    "purpose": "把任务写成 durable truth，而不是只停在对话里。",
                },
                {
                    "name": "launch_study",
                    "command": "uv run python -m med_autoscience.cli study launch --profile <profile> --study-id <study_id>",
                    "purpose": "正式启动或续跑 study，并立即拿到监督入口。",
                },
                {
                    "name": "study_progress",
                    "command": "uv run python -m med_autoscience.cli study progress --profile <profile> --study-id <study_id>",
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
                    "command": "uv run python -m med_autoscience.cli doctor report --profile <profile>",
                    "purpose": "先看 workspace / MAS domain refs boundary readiness。",
                },
                {
                    "name": "study_progress",
                    "command": "uv run python -m med_autoscience.cli study progress --profile <profile> --format json",
                    "purpose": "读取 MAS domain progress 与 OPL current-control-state handoff refs。",
                },
                {
                    "name": "domain_health_diagnostic",
                    "command": "uv run python -m med_autoscience.cli runtime domain-health-diagnostic --runtime-root <runtime_root> --profile <profile> --request-opl-stage-attempts --dry-run",
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
                    "command": "uv run python -m med_autoscience.cli doctor mainline-phase --phase phase_4_backend_deconstruction",
                    "purpose": "先看 backend deconstruction 的当前边界、入口和退出条件。",
                },
                {
                    "name": "deconstruction_map",
                    "command": "uv run python -m med_autoscience.cli doctor mainline-status",
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
                    "command": "uv run python -m med_autoscience.cli doctor mainline-phase --phase phase_5_stage_runtime_platform_maturation",
                    "purpose": "先看 stage-runtime / platform 这层现在仍然为什么是后置阶段。",
                },
                {
                    "name": "mainline_status",
                    "command": "uv run python -m med_autoscience.cli doctor mainline-status",
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
    product_entry_projection = read_product_entry_mainline_projection()
    phase_ladder = _phase_ladder()
    unified_enhancement_program = build_unified_enhancement_program_projection()
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "program_id": product_entry_projection["program_id"],
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
                "runtime_owner": OPL_RUNTIME_OWNER,
                "runtime_substrate": OPL_HOSTED_STAGE_RUNTIME_ID,
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
        "single_project_boundary": product_entry_projection["single_project_boundary"],
        "capability_owner_boundary": product_entry_projection["capability_owner_boundary"],
        "active_tranche_owner_truth": _active_tranche_owner_truth(),
        "current_stage": product_entry_projection["current_stage"],
        "current_program_phase": product_entry_projection["current_program_phase"],
        "phase2_user_product_loop": _phase2_user_product_loop(),
        "phase3_clearance_lane": _phase3_clearance_lane(),
        "phase4_backend_deconstruction": _phase4_backend_deconstruction(),
        "platform_target": product_entry_projection["platform_target"],
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
        "remaining_gaps": product_entry_projection["remaining_gaps"],
        "next_focus": product_entry_projection["next_focus"],
        "explicitly_not_now": product_entry_projection["explicitly_not_now"],
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
            "mainline_status": "uv run python -m med_autoscience.cli doctor mainline-status",
            "unified_enhancement_program": "uv run python -m med_autoscience.cli doctor mainline-status --format json",
            "workspace_cockpit": "uv run python -m med_autoscience.cli workspace cockpit --profile <profile>",
            "study_progress": "uv run python -m med_autoscience.cli study progress --profile <profile> --study-id <study_id>",
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
