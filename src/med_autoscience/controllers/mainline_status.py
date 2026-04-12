from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = 1
PROGRAM_ID = "research-foundry-medical-mainline"
CURRENT_STAGE_ID = "f4_blocker_closeout"
CURRENT_STAGE_STATUS = "in_progress"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_mainline_status() -> dict[str, Any]:
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
    runtime_topology = dict((payload.get("ideal_state") or {}).get("runtime_topology") or {})
    lines = [
        "# Mainline Status",
        "",
        f"- program_id: `{payload.get('program_id')}`",
        f"- current_stage: `{current_stage.get('id')}`",
        f"- stage_status: `{current_stage.get('status')}`",
        f"- stage_summary: {current_stage.get('summary')}",
        "",
        "## Ideal State",
        "",
        f"- domain_gateway: {runtime_topology.get('domain_gateway')}",
        f"- outer_runtime_substrate_owner: {runtime_topology.get('outer_runtime_substrate_owner')}",
        f"- research_backend: {runtime_topology.get('research_backend')}",
        f"- entry_shape: {runtime_topology.get('entry_shape')}",
        "",
        "## Completed Tranches",
        "",
    ]
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
