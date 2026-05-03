from __future__ import annotations

import importlib


def _v2_readiness_payload() -> dict[str, object]:
    return {
        "surface": "medical_paper_readiness",
        "overall_status": "blocked",
        "ready_count": 2,
        "required_count": 8,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "next_action": {
            "action_id": "run_provider_literature_scout",
            "surface_key": "literature_provider_runtime",
            "summary": "运行 provider-backed 文献摄取。",
        },
        "capability_surfaces": [
            {
                "surface_key": "literature_provider_runtime",
                "label": "Literature Provider Runtime",
                "status": "missing",
                "artifact_path": "artifacts/literature/provider_runtime.json",
                "evidence_refs": ["refs/literature_provider_runtime/latest.json"],
                "missing_reason": "missing_provider_provenance",
                "required_for_ready": True,
            },
            {
                "surface_key": "route_decision_orchestrator",
                "label": "Route Decision Orchestrator",
                "status": "blocked",
                "artifact_path": "artifacts/controller/route_decision.json",
                "evidence_refs": ["controller_decisions/latest.json"],
                "missing_reason": "missing_controller_decision",
                "required_for_ready": True,
            },
            {
                "surface_key": "statistical_discipline_operations",
                "label": "Statistical Discipline Operations",
                "status": "partial",
                "artifact_path": "artifacts/statistics/blockers.json",
                "evidence_refs": ["publication_eval/latest.json"],
                "missing_reason": "open_statistical_blockers",
                "required_for_ready": True,
            },
            {
                "surface_key": "revision_rebuttal_loop",
                "label": "Revision / Rebuttal Loop",
                "status": "missing",
                "artifact_path": "artifacts/revision/rebuttal_matrix.json",
                "evidence_refs": ["artifacts/revision/comments.json"],
                "missing_reason": "missing_reviewer_comment_intake",
                "required_for_ready": True,
            },
            {
                "surface_key": "authoring_runtime_authorization",
                "label": "Authoring Runtime Authorization",
                "status": "blocked",
                "artifact_path": "artifacts/writing/authorization.json",
                "evidence_refs": ["artifacts/quality/ai_reviewer.json"],
                "missing_reason": "drafting_not_authorized",
                "required_for_ready": True,
            },
            {
                "surface_key": "real_workspace_soak_monitor",
                "label": "Real Workspace Soak Monitor",
                "status": "partial",
                "artifact_path": "artifacts/runtime/soak_monitor.json",
                "evidence_refs": ["artifacts/runtime/soak/latest.json"],
                "missing_reason": "missing_required_archetype",
                "required_for_ready": True,
            },
        ],
    }


def _progress_payload() -> dict[str, object]:
    return {
        "study_id": "003-dpcc",
        "quest_id": "quest-003",
        "current_stage": "writing",
        "current_stage_summary": "readiness v2 surfaces require attention.",
        "paper_stage": "drafting",
        "paper_stage_summary": "paper automation is blocked on v2 readiness surfaces.",
        "next_system_action": "按 readiness action card 补齐缺口。",
        "medical_paper_readiness": _v2_readiness_payload(),
    }


def test_compact_mcp_progress_projection_preserves_v2_readiness_surface_details() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    compact = module.compact_study_progress_projection(_progress_payload())
    readiness = compact["medical_paper_readiness"]

    assert readiness["quality_claim_authorized"] is False
    assert readiness["mechanical_projection_can_authorize_quality"] is False
    missing = {item["surface_key"]: item for item in readiness["missing_surfaces"]}
    assert missing["literature_provider_runtime"] == {
        "surface_key": "literature_provider_runtime",
        "status": "missing",
        "missing_reason": "missing_provider_provenance",
        "artifact_path": "artifacts/literature/provider_runtime.json",
        "evidence_refs": ["refs/literature_provider_runtime/latest.json"],
        "action_id": "run_provider_literature_scout",
        "action_label": "联网补文献",
        "action_summary": "运行 provider-backed 文献摄取，保留 provider provenance、检索日期和 citation ledger refs。",
    }
    assert missing["route_decision_orchestrator"]["action_label"] == "写入路线裁决"
    assert missing["statistical_discipline_operations"]["action_label"] == "处理统计 blocker"
    assert missing["revision_rebuttal_loop"]["action_label"] == "启动返修"
    assert missing["authoring_runtime_authorization"]["action_label"] == "授权写作"
    assert missing["real_workspace_soak_monitor"]["action_label"] == "运行真实 soak"


def test_mcp_study_progress_markdown_renders_v2_readiness_action_semantics() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    markdown = module.render_mcp_study_progress_markdown(_progress_payload())

    assert "补文献: 运行 provider-backed 文献摄取" in markdown
    assert "路线裁决: 把路线选择、route-back 或 switch-line 决策写入 controller decision 投影。" in markdown
    assert "统计 blocker: 逐项处理缺失值、precision、外部验证、多重性、临床效用和敏感性分析 blocker/waiver。" in markdown
    assert "返修: 摄取 reviewer comments，生成 rebuttal action matrix、analysis repair 和 AI reviewer recheck。" in markdown
    assert "写作授权: 检查目标期刊层、claim/display map、ledger 和 AI reviewer provenance 后再授权 full manuscript drafting。" in markdown
    assert "真实 soak: 从真实或脱敏 study workspace 只读检查多 study soak ready/partial/blocked 状态。" in markdown
    assert "generic 缺失 surface" not in markdown
    assert "- quality_claim_authorized: `False`" in markdown
    assert "- mechanical_projection_can_authorize_quality: `False`" in markdown


def test_study_progress_markdown_renders_v2_readiness_action_semantics() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(_progress_payload())

    assert "补文献: 运行 provider-backed 文献摄取" in markdown
    assert "路线裁决: 把路线选择、route-back 或 switch-line 决策写入 controller decision 投影。" in markdown
    assert "统计 blocker: 逐项处理缺失值、precision、外部验证、多重性、临床效用和敏感性分析 blocker/waiver。" in markdown
    assert "返修: 摄取 reviewer comments，生成 rebuttal action matrix、analysis repair 和 AI reviewer recheck。" in markdown
    assert "写作授权: 检查目标期刊层、claim/display map、ledger 和 AI reviewer provenance 后再授权 full manuscript drafting。" in markdown
    assert "真实 soak: 从真实或脱敏 study workspace 只读检查多 study soak ready/partial/blocked 状态。" in markdown
    assert "- 质量声明授权: `false`" in markdown
