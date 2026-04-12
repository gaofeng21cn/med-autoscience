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


def read_mainline_status() -> dict[str, Any]:
    phase_ladder = [
        {
            "id": "phase_1_mainline_established",
            "title": "Phase 1 mainline established",
            "status": "in_progress",
            "summary": (
                "先证明 MAS -> Hermes-Agent target outer substrate -> controlled MedDeepScientist backend 这条主线诚实成立，"
                "并完成 F4 blocker 收口。"
            ),
            "focus": [
                "close remaining study blockers without reopening seam-only work",
                "keep runtime truth, recovery proof, and product-entry hardening aligned",
            ],
        },
        {
            "id": "phase_2_user_product_loop",
            "title": "Phase 2 user product loop",
            "status": "pending",
            "summary": "把启动、下任务、持续看进度、看告警、看恢复建议收成稳定用户回路。",
            "focus": [
                "stabilize user-facing inbox, attention queue, and progress loop",
                "make stuck-state, recovery suggestions, and supervision freshness continuously visible",
            ],
        },
        {
            "id": "phase_3_multi_workspace_host_clearance",
            "title": "Phase 3 multi-workspace / host clearance",
            "status": "pending",
            "summary": "把当前 proof 从单机/单 workspace 扩到多 workspace、多宿主的真实长期稳定性。",
            "focus": [
                "prove service, recovery, and quality guards across more hosts and workspaces",
                "clear broader external-runtime and workspace-specific blocker classes honestly",
            ],
        },
        {
            "id": "phase_4_backend_deconstruction",
            "title": "Phase 4 backend deconstruction",
            "status": "pending",
            "summary": "在 outer runtime 与产品回路稳定后，再逐步解构 MedDeepScientist 中可迁出的通用能力。",
            "focus": [
                "move reusable runtime capability out of the controlled backend only with proof",
                "keep executor replacement explicit and contract-driven instead of forced rewrites",
            ],
        },
        {
            "id": "phase_5_federation_platform_maturation",
            "title": "Phase 5 federation and platform maturation",
            "status": "pending",
            "summary": "最后再考虑更大平台化工作，如 federation direct entry、monorepo 与 runtime core ingest。",
            "focus": [
                "land broader federation-facing direct entry only after earlier phases hold",
                "treat monorepo and large physical restructures as strictly post-gate work",
            ],
        },
    ]
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


def render_mainline_status_markdown(payload: dict[str, Any]) -> str:
    current_stage = dict(payload.get("current_stage") or {})
    current_program_phase = dict(payload.get("current_program_phase") or {})
    runtime_topology = dict((payload.get("ideal_state") or {}).get("runtime_topology") or {})
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
        "## Program Phases",
        "",
    ]
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
