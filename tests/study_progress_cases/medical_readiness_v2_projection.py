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
    literature_missing = missing["literature_provider_runtime"]
    assert {
        key: literature_missing[key]
        for key in (
            "surface_key",
            "status",
            "missing_reason",
            "artifact_path",
            "evidence_refs",
            "action_id",
            "action_label",
            "action_summary",
            "semantic_label",
            "next_action_summary",
            "authority_contract",
        )
    } == {
        "surface_key": "literature_provider_runtime",
        "status": "missing",
        "missing_reason": "missing_provider_provenance",
        "artifact_path": "artifacts/literature/provider_runtime.json",
        "evidence_refs": ["refs/literature_provider_runtime/latest.json"],
        "action_id": "run_provider_literature_scout",
        "action_label": "联网补文献",
        "action_summary": "运行 provider-backed 文献摄取，保留 provider provenance、检索日期和 citation ledger refs。",
        "semantic_label": "补文献",
        "next_action_summary": "运行 provider-backed 文献摄取，保留 provider provenance、检索日期和 citation ledger refs。",
        "authority_contract": {
            "can_mutate_runtime": False,
            "can_authorize_quality": False,
            "can_authorize_submission": False,
            "can_authorize_finalize": False,
            "mechanical_projection_can_authorize_quality": False,
        },
    }
    command = literature_missing["guarded_operator_command"]
    assert command["surface"] == "medical_paper_v3_guarded_operator_command"
    assert command["schema_version"] == 1
    assert command["action_id"] == "run_provider_literature_scout"
    assert command["surface_key"] == "literature_provider_runtime"
    assert command["entrypoint"] == "product_entry.dispatch_guarded_medical_paper_operator_action"
    assert command["guard"] == "existing_product_entry_controller_guard"
    assert command["requires"] == ["profile_ref", "study_id", "operator_payload"]
    assert command["status"] == "guarded_pending"
    assert command["action_instance_id"].startswith("guarded-operator-action::")
    assert command["idempotency_key"].startswith("guarded-operator-action::sha256:")
    assert command["input_digest"].startswith("sha256:")
    assert readiness["v3_action_truth"][0]["surface_key"] == "literature_provider_runtime"
    assert readiness["v3_action_truth"][0]["guarded_operator_command"]["status"] == "guarded_pending"
    assert readiness["v3_action_truth"][0]["authority_contract"]["can_mutate_runtime"] is False
    assert readiness["v4_operations"]["surface"] == "medical_paper_v4_operations_dashboard"
    assert readiness["v4_operations"]["overall_status"] == "blocked"
    assert readiness["v4_operations"]["health"]["provider_health"]["status"] == "missing"
    assert readiness["v4_operations"]["health"]["operator_action_health"]["pending_action_count"] == 1
    assert readiness["v4_operations"]["health"]["operator_action_health"]["action_ids"] == [
        "run_provider_literature_scout"
    ]
    assert readiness["v4_operations"]["health"]["statistical_blocker_health"]["status"] == "partial"
    assert readiness["v4_operations"]["health"]["soak_monitor_health"]["status"] == "partial"
    assert readiness["v4_operations"]["health"]["ai_reviewer_calibration_health"]["status"] == "blocked"
    assert readiness["v4_operations"]["authority_contract"]["can_authorize_quality"] is False
    assert readiness["v4_operations"]["authority_contract"]["can_authorize_submission"] is False
    assert readiness["v4_operations"]["authority_contract"]["can_authorize_finalize"] is False
    assert set(missing) == {"literature_provider_runtime"}


def test_mcp_progress_projection_uses_canonical_user_visible_projection() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    payload = {
        **_progress_payload(),
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "details": {"package_delivered": False, "paper_stage": "canonical_paper_stage"},
            "conditions": [],
        },
        "user_visible_projection": {
            "surface": "study_progress_user_visible_projection",
            "schema_version": 2,
            "authority": "truth_projection",
            "projection_only": True,
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "state": "queued/repair/quality",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "package_delivered": False,
            "actual_write_active": False,
            "user_action_required": False,
            "state_label": "质量修复/复审中",
            "state_summary": "质量修复/复审中；质量、artifact 或 runtime 有明确修复 owner。",
            "current_stage": "queued",
            "current_stage_label": "质量修复/复审中",
            "current_stage_summary": "canonical user summary",
            "paper_stage": "canonical_paper_stage",
            "paper_stage_summary": "canonical paper summary",
            "current_blockers": ["canonical blocker"],
            "next_system_action": "canonical next action",
            "evidence": {
                "latest_events": [
                    {
                        "timestamp": "2026-05-04T01:00:00+00:00",
                        "category": "controller_decision",
                        "title": "Controller decision",
                        "summary": "controller evidence",
                        "source": "controller",
                    }
                ],
                "refs": {"controller_decision_path": "controller/latest.json"},
            },
            "conditions": [
                {
                    "type": "stage_known",
                    "status": "true",
                    "reason": "stage_present",
                    "message": "canonical user summary",
                }
            ],
        },
    }

    compact = module.compact_study_progress_projection(payload)
    markdown = module.render_mcp_study_progress_markdown(payload)

    assert compact["writer_state"] == "queued"
    assert compact["state_label"] == "质量修复/复审中"
    assert compact["current_stage"] == "queued"
    assert compact["current_stage_summary"] == "canonical user summary"
    assert compact["paper_stage"] == "canonical_paper_stage"
    assert compact["paper_stage_summary"] == "canonical paper summary"
    assert compact["current_blockers"] == ["canonical blocker"]
    assert compact["next_system_action"] == "canonical next action"
    assert compact["latest_events"][0]["summary"] == "controller evidence"
    assert compact["user_visible_projection"]["authority"] == "truth_projection"
    assert "- 用户可见状态: 质量修复/复审中" in markdown
    assert "- writer_state: `queued`" in markdown
    assert "- 下一步: canonical next action" in markdown
    assert "- canonical blocker" in markdown


def test_mcp_study_progress_markdown_renders_v2_readiness_action_semantics() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")

    markdown = module.render_mcp_study_progress_markdown(_progress_payload())

    assert "补文献: 运行 provider-backed 文献摄取" in markdown
    assert "路线裁决: 把路线选择、route-back 或 switch-line 决策写入 controller decision 投影。" not in markdown
    assert "统计 blocker: 逐项处理缺失值、precision、外部验证、多重性、临床效用和敏感性分析 blocker/waiver。" not in markdown
    assert "返修: 摄取 reviewer comments，生成 rebuttal action matrix、analysis repair 和 AI reviewer recheck。" not in markdown
    assert "写作授权: 检查目标期刊层、claim/display map、ledger 和 AI reviewer provenance 后再授权 full manuscript drafting。" not in markdown
    assert "真实 soak: 从真实或脱敏 study workspace 只读检查多 study soak ready/partial/blocked 状态。" not in markdown
    assert "guarded action: `run_provider_literature_scout`" in markdown
    assert "authority: product-entry/controller guarded; quality authorization: false" in markdown
    assert "generic 缺失 surface" not in markdown
    assert "- quality_claim_authorized: `False`" in markdown
    assert "- mechanical_projection_can_authorize_quality: `False`" in markdown
    assert "## Medical Paper v4 Operations" in markdown
    assert "- provider_health: `missing` (missing_provider_provenance)" in markdown
    assert "- operator_action_health: `blocked` (guarded_operator_actions_pending)" in markdown
    assert "- quality/submission/finalize authority: `False/False/False`" in markdown


def test_study_progress_markdown_renders_v2_readiness_action_semantics() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    markdown = module.render_study_progress_markdown(_progress_payload())

    assert "补文献: 运行 provider-backed 文献摄取" in markdown
    assert "路线裁决: 把路线选择、route-back 或 switch-line 决策写入 controller decision 投影。" not in markdown
    assert "统计 blocker: 逐项处理缺失值、precision、外部验证、多重性、临床效用和敏感性分析 blocker/waiver。" not in markdown
    assert "返修: 摄取 reviewer comments，生成 rebuttal action matrix、analysis repair 和 AI reviewer recheck。" not in markdown
    assert "写作授权: 检查目标期刊层、claim/display map、ledger 和 AI reviewer provenance 后再授权 full manuscript drafting。" not in markdown
    assert "真实 soak: 从真实或脱敏 study workspace 只读检查多 study soak ready/partial/blocked 状态。" not in markdown
    assert "- 质量声明授权: `false`" in markdown
    assert "## v4 生产运行面 / Medical Paper Operations" in markdown
    assert "- provider_health: `missing`（missing_provider_provenance）" in markdown
    assert "- authority: projection-only；quality/submission/finalize authorization: `False/False/False`" in markdown
