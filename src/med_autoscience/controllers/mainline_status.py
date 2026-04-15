from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = 1
PROGRAM_ID = "research-foundry-medical-mainline"
CURRENT_STAGE_ID = "f4_blocker_closeout"
CURRENT_STAGE_STATUS = "in_progress"
CURRENT_PROGRAM_PHASE_ID = "phase_1_mainline_established"
CURRENT_PROGRAM_PHASE_STATUS = "in_progress"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _platform_target() -> dict[str, Any]:
    return {
        "surface_kind": "phase5_platform_target",
        "summary": (
            "Phase 5 的目标是把 MAS 继续收敛到 federation/platform-ready 形态，包括 monorepo、"
            "runtime core ingest 和更成熟的 direct product entry；但这些都必须建立在前四阶段真实成立之后。"
        ),
        "north_star_topology": {
            "domain_gateway": "Med Auto Science",
            "outer_runtime_substrate_owner": "upstream Hermes-Agent",
            "controlled_research_backend": "MedDeepScientist",
            "monorepo_status": "post_gate_target",
        },
        "promotion_gates": [
            "phase_1_mainline_established",
            "phase_2_user_product_loop",
            "phase_3_multi_workspace_host_clearance",
            "phase_4_backend_deconstruction",
        ],
        "land_now": [
            "repo-tracked product-entry shell and family orchestration companions",
            "controller-owned runtime/progress/recovery truth",
            "CLI/MCP/controller entry surfaces that already support real work",
        ],
        "not_yet": [
            "physical monorepo absorb",
            "runtime core ingest across repos",
            "mature hosted standalone medical frontend",
        ],
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_5_federation_platform_maturation"
        ),
    }


def _phase3_clearance_lane() -> dict[str, Any]:
    return {
        "surface_kind": "phase3_host_clearance_lane",
        "summary": "Phase 3 把 external runtime、workspace supervisor service 和 study recovery proof 扩到更多 workspace/host，并保持 fail-closed。",
        "clearance_targets": [
            {
                "target_id": "external_runtime_contract",
                "title": "Check external Hermes runtime contract",
                "commands": [
                    "uv run python -m med_autoscience.cli doctor --profile <profile>",
                    "uv run python -m med_autoscience.cli hermes-runtime-check --profile <profile>",
                ],
            },
            {
                "target_id": "supervisor_service",
                "title": "Keep workspace supervisor service online",
                "commands": [
                    "ops/medautoscience/bin/watch-runtime-service-status",
                    "uv run python -m med_autoscience.cli watch --runtime-root <runtime_root> --profile <profile> --ensure-study-runtimes --apply",
                ],
            },
            {
                "target_id": "study_recovery_proof",
                "title": "Prove live study recovery and supervision",
                "commands": [
                    "uv run python -m med_autoscience.cli launch-study --profile <profile> --study-id <study_id>",
                    "uv run python -m med_autoscience.cli study-progress --profile <profile> --study-id <study_id>",
                ],
            },
        ],
        "proof_surfaces": [
            "doctor.external_runtime_contract",
            "study_runtime_status.autonomous_runtime_notice",
            "runtime_watch/latest.json",
            "runtime_supervision/latest.json",
            "controller_decisions/latest.json",
        ],
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_3_multi_workspace_host_clearance"
        ),
    }


def _phase4_backend_deconstruction() -> dict[str, Any]:
    return {
        "surface_kind": "phase4_backend_deconstruction_lane",
        "summary": "Phase 4 把可迁出的通用 runtime 能力继续迁向 substrate，同时诚实保留 controlled backend executor。",
        "substrate_targets": [
            {
                "capability_id": "session_run_watch_recovery",
                "owner": "upstream Hermes-Agent",
                "summary": "session / run / watch / recovery / scheduling / interruption 继续收归 outer runtime substrate。",
            },
            {
                "capability_id": "backend_generic_runtime_contract",
                "owner": "MedAutoScience controller boundary",
                "summary": "controller / transport / durable surface 只认 backend-generic contract 与 explicit runtime handle。",
            },
        ],
        "backend_retained_now": [
            "MedDeepScientist CodexRunner autonomous executor chain",
            "backend-local agent/tool routing and Codex skills",
            "quest-local research execution, paper worktree, and daemon side effects",
        ],
        "promotion_rules": [
            "no claim of backend retirement without owner + contract + tests + proof",
            "executor replacement must be explicit and proof-backed",
            "no physical monorepo absorb before the external gate is cleared",
        ],
        "deconstruction_map_doc": "docs/program/med_deepscientist_deconstruction_map.md",
        "recommended_phase_command": (
            "uv run python -m med_autoscience.cli mainline-phase --phase phase_4_backend_deconstruction"
        ),
    }


def _phase_ladder() -> list[dict[str, Any]]:
    return [
        {
            "id": "phase_1_mainline_established",
            "title": "Phase 1 mainline established",
            "status": "in_progress",
            "usable_now": True,
            "summary": (
                "先证明 MAS -> Hermes-Agent target outer substrate -> controlled MedDeepScientist backend 这条主线诚实成立，"
                "并完成 F4 blocker 收口。"
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
                "docs/program/upstream_hermes_agent_fast_cutover_board.md",
                "docs/program/research_foundry_medical_mainline.md",
                "docs/program/research_foundry_medical_phase_ladder.md",
            ],
        },
        {
            "id": "phase_2_user_product_loop",
            "title": "Phase 2 user product loop",
            "status": "pending",
            "usable_now": True,
            "summary": "把启动、下任务、持续看进度、看告警、看恢复建议收成稳定用户回路。",
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
                "docs/program/research_foundry_medical_phase_ladder.md",
                "docs/references/lightweight_product_entry_and_opl_handoff.md",
                "docs/runtime/agent_runtime_interface.md",
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
                "docs/program/external_runtime_dependency_gate.md",
                "docs/program/upstream_hermes_agent_fast_cutover_board.md",
                "docs/program/research_foundry_medical_phase_ladder.md",
            ],
        },
        {
            "id": "phase_4_backend_deconstruction",
            "title": "Phase 4 backend deconstruction",
            "status": "pending",
            "usable_now": True,
            "summary": "在 outer runtime 与产品回路稳定后，再逐步解构 MedDeepScientist 中可迁出的通用能力。",
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
                "docs/program/med_deepscientist_deconstruction_map.md",
                "docs/program/research_foundry_medical_phase_ladder.md",
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
                "docs/program/research_foundry_medical_phase_ladder.md",
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
        "current_stage": {
            "id": CURRENT_STAGE_ID,
            "status": CURRENT_STAGE_STATUS,
            "title": "F4 blocker closeout",
            "summary": (
                "repo-side 已拿到 external Hermes runtime truth、real adapter cutover 和至少一条真实 study "
                "recovery/proof；当前主线进入 blocker 收口与 product-entry hardening，而不是回去继续做 seam-only 包装。"
            ),
        },
        "current_program_phase": {
            "id": CURRENT_PROGRAM_PHASE_ID,
            "status": CURRENT_PROGRAM_PHASE_STATUS,
            "title": "Phase 1 mainline established",
            "summary": (
                "当前总体仍处在第一阶段尾声：主线已成立，正在把 F4 blocker 收口干净，并把用户可见入口继续收成真实产品回路。"
            ),
        },
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
            "keep docs/status/runtime contracts aligned so OPL language, MAS role, and runtime truth do not drift",
            "only move toward broader cutover or monorepo work after the external gate is honestly cleared",
        ],
        "explicitly_not_now": [
            "physical migration or cross-repo rewrite",
            "mixing display or paper-figure assetization into the runtime mainline",
            "claiming MedDeepScientist has already exited",
            "claiming upstream Hermes already fully replaces the research executor",
            "claiming a standalone OPL/MAS product frontend is already landed",
        ],
        "source_docs": [
            "README.md",
            "docs/project.md",
            "docs/architecture.md",
            "docs/status.md",
            "docs/program/upstream_hermes_agent_fast_cutover_board.md",
            "docs/program/research_foundry_medical_mainline.md",
            "docs/program/research_foundry_medical_phase_ladder.md",
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
    lines = [
        "# Mainline Phase",
        "",
        f"- program_id: `{payload.get('program_id')}`",
        f"- phase_id: `{phase.get('id')}`",
        f"- phase_status: `{phase.get('status')}`",
        f"- usable_now: `{phase.get('usable_now')}`",
        f"- summary: {phase.get('summary')}",
        "",
        "## Entry Points",
        "",
    ]
    entry_points = list(phase.get("entry_points") or [])
    if entry_points:
        for item in entry_points:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('name')}`: `{item.get('command')}`"
            )
            purpose = str(item.get("purpose") or "").strip()
            if purpose:
                lines.append(f"  purpose: {purpose}")
    else:
        lines.append("- none")
    lines.extend(["", "## Exit Criteria", ""])
    exit_criteria = list(phase.get("exit_criteria") or [])
    if exit_criteria:
        for item in exit_criteria:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Key Docs", ""])
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
    phase3_clearance_lane = dict(payload.get("phase3_clearance_lane") or {})
    phase4_backend_deconstruction = dict(payload.get("phase4_backend_deconstruction") or {})
    platform_target = dict(payload.get("platform_target") or {})
    lines = [
        "# Mainline Status",
        "",
        f"- program_id: `{payload.get('program_id')}`",
        f"- current_stage: `{current_stage.get('id')}`",
        f"- stage_status: `{current_stage.get('status')}`",
        f"- stage_summary: {current_stage.get('summary')}",
        f"- current_program_phase: `{current_program_phase.get('id')}`",
        f"- phase_status: `{current_program_phase.get('status')}`",
        "",
        "## Ideal State",
        "",
        f"- domain_gateway: {runtime_topology.get('domain_gateway')}",
        f"- outer_runtime_substrate_owner: {runtime_topology.get('outer_runtime_substrate_owner')}",
        f"- research_backend: {runtime_topology.get('research_backend')}",
        f"- entry_shape: {runtime_topology.get('entry_shape')}",
        "",
        "## Phase 3 Clearance",
        "",
        f"- summary: {phase3_clearance_lane.get('summary') or 'none'}",
    ]
    for item in phase3_clearance_lane.get("clearance_targets") or []:
        if not isinstance(item, dict):
            continue
        lines.append(f"- `{item.get('target_id')}`: `{((item.get('commands') or ['none'])[0])}`")
    lines.extend(
        [
            "",
            "## Phase 4 Deconstruction",
            "",
            f"- summary: {phase4_backend_deconstruction.get('summary') or 'none'}",
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
        f"- surface_kind: `{platform_target.get('surface_kind') or 'none'}`",
        f"- summary: {platform_target.get('summary') or 'none'}",
        f"- monorepo_status: `{((platform_target.get('north_star_topology') or {}).get('monorepo_status') or 'none')}`",
        f"- recommended_phase_command: `{platform_target.get('recommended_phase_command') or 'none'}`",
        "",
        "## Program Phases",
        "",
        ]
    )
    for item in payload.get("phase_ladder") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- `{item.get('id')}` [{item.get('status')}]: {item.get('summary')}"
        )
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
