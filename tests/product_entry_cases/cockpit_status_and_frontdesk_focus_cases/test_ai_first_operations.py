from __future__ import annotations

from tests.product_entry_cases import shared as _shared
from tests.product_entry_cases import attention_queue_and_cockpit_base as _attention_queue_and_cockpit_base
from tests.product_entry_cases import frontdesk_focus_cases as _frontdesk_focus_cases


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)
_module_reexport(_attention_queue_and_cockpit_base)
_module_reexport(_frontdesk_focus_cases)


def test_workspace_cockpit_projects_ai_first_operations_state_from_study_progress(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.product_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    monkeypatch.setattr(
        module,
        "build_doctor_report",
        lambda profile: SimpleNamespace(
            workspace_exists=True,
            runtime_exists=True,
            studies_exists=True,
            portfolio_exists=True,
            med_deepscientist_runtime_exists=True,
            medical_overlay_ready=True,
            external_runtime_contract={"ready": True},
            workspace_supervision_contract={
                "status": "loaded",
                "loaded": True,
                "summary": "Hermes-hosted runtime supervision 已在线。",
                "drift_reasons": [],
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "_inspect_workspace_supervision",
        lambda profile: {
            "manager": "launchd",
            "status": "loaded",
            "loaded": True,
            "job_exists": True,
            "summary": "Hermes-hosted runtime supervision 已在线。",
            "drift_reasons": [],
        },
    )
    monkeypatch.setattr(
        module.mainline_status,
        "read_mainline_status",
        lambda: {
            "program_id": "research-foundry-medical-mainline",
            "current_stage": {"id": "quality_os_runtime", "status": "in_progress", "summary": "质量运行面已接入。"},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "AI-first operations 已接入当前 study。",
            "current_blockers": ["AI reviewer trace 还未闭环。"],
            "next_system_action": "回到 AI reviewer workflow 补齐质量授权。",
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "title": "补齐 AI reviewer trace",
                "summary": "质量授权还没有闭环。",
            },
            "operator_verdict": {"decision_mode": "monitor_only", "summary": "质量授权还没有闭环。"},
            "operator_status_card": {
                "handling_state": "scientific_or_quality_repair_in_progress",
                "user_visible_verdict": "当前需要 AI reviewer 复核后才能继续。",
            },
            "ai_first_default_entry_state": {
                "surface": "ai_first_default_entry_state",
                "current_stage": "pre_submission_default_entry",
                "pre_draft": {"summary": "pre-draft 已完成结构化初稿。"},
                "ai_reviewer_workflow": {
                    "summary": "AI reviewer workflow 正在补齐质量授权。",
                    "trace_complete": False,
                    "prompt": "internal prompt must stay hidden",
                    "token_count": 1234,
                },
                "artifact_proof": {
                    "summary": "artifact proof 等待 current_package 从 canonical source 刷新。",
                    "refresh_pending_count": 2,
                    "current_package_from_canonical_source": False,
                    "log_path": "/tmp/internal.log",
                },
                "route_back": {
                    "summary": "route-back 指向 analysis-campaign。",
                    "active": True,
                    "target": "analysis-campaign",
                },
                "next_step": "先补齐 AI reviewer workflow，再刷新 artifact proof。",
                "human_judgment": {"summary": "等待人工判断是否释放投稿包。", "required": True},
                "blockers": ["AI reviewer trace 还未闭环。"],
            },
            "ai_first_operations_dashboard": {
                "surface": "ai_first_operations_dashboard_summary",
                "read_model": "ai_first_operations_dashboard_read_model",
                "user_view": {
                    "current_stage": "publication_supervision",
                    "blockers": ["AI reviewer trace 还未闭环。"],
                    "next_step": "回到 AI reviewer workflow 补齐质量授权。",
                    "human_review_required": True,
                },
                "maintainer_view": {
                    "ai_reviewer_trace": {"complete": False},
                    "route_back": {"count": 1, "target": "analysis-campaign"},
                    "artifact_stale": {
                        "stale_artifact_count": 2,
                        "current_package_from_canonical_source": False,
                    },
                    "quality_toil": {"toil_count": 1},
                },
                "authority": {
                    "observability_can_authorize_quality": False,
                    "observability_can_mutate_runtime": False,
                },
            },
            "ai_first_feedback_state": {
                "surface": "ai_first_feedback_state",
                "read_model": "ai_first_feedback_read_model",
                "authority": "observability_only",
                "status": "attention_required",
                "summary": "3 个 AI-first 运行反馈信号需要处理。",
                "primary_feedback": {
                    "category": "ai_reviewer_trace_gap",
                    "reason": "当前质量判断仍是机械投影。",
                },
                "primary_action": {
                    "action_id": "return_to_ai_reviewer_workflow",
                    "target_surface": "ai_reviewer_runtime_workflow",
                    "summary": "补齐 AI reviewer workflow、publication eval 与 medical prose review。",
                    "authority": "observability_only",
                    "can_authorize_quality": False,
                    "can_authorize_submission": False,
                },
                "user_view": {
                    "current_stage": "publication_supervision",
                    "primary_feedback_reason": "当前质量判断仍是机械投影。",
                    "next_step": "先补齐 AI reviewer workflow，再刷新 artifact proof。",
                    "next_action": "补齐 AI reviewer workflow、publication eval 与 medical prose review。",
                    "human_review_required": True,
                    "prompt": "internal prompt must stay hidden",
                    "token_count": 1234,
                },
                "counts": {
                    "open_feedback_count": 3,
                    "repeat_toil_count": 1,
                    "open_route_back_count": 1,
                    "artifact_rebuild_pending_count": 1,
                    "ai_reviewer_trace_incomplete_count": 1,
                    "manual_judgment_pending_count": 1,
                },
                "quality_learning_operations_report": {
                    "surface": "ai_first_quality_learning_operations_report",
                    "read_model": "ai_first_quality_learning_operations_report_read_model",
                    "authority": "maintainer_operations_only",
                    "summary": "1 个 open feedback 维护优先项；1 个 repeat-toil 系统改进优先项。",
                    "open_feedback_priorities": [
                        {
                            "priority_rank": 1,
                            "priority_type": "open_feedback",
                            "category": "ai_reviewer_trace_gap",
                            "reason": "当前质量判断仍是机械投影。",
                            "frequency": 3,
                            "impact_entry": "ai_reviewer_runtime_workflow",
                            "suggested_fix_layer": "AI reviewer trace contract",
                            "maintenance_priority": (
                                "当前质量判断仍是机械投影。 | frequency=3 | "
                                "impact=ai_reviewer_runtime_workflow | fix_layer=AI reviewer trace contract"
                            ),
                            "source_surface": "ai_reviewer_runtime_workflow",
                            "is_open_blocker": True,
                            "is_quality_gate": False,
                            "prompt": "COCKPIT_PROMPT_CANARY",
                            "token_count": 1234,
                        }
                    ],
                    "system_improvement_priorities": [
                        {
                            "priority_rank": 1,
                            "priority_type": "system_improvement",
                            "category": "artifact_rebuild_pending",
                            "reason": "canonical_artifact_rebuild_pending",
                            "frequency": 5,
                            "impact_entry": "artifact_runtime_proof",
                            "suggested_fix_layer": "artifact rebuild proof layer",
                            "maintenance_priority": (
                                "canonical_artifact_rebuild_pending | frequency=5 | "
                                "impact=artifact_runtime_proof | fix_layer=artifact rebuild proof layer"
                            ),
                            "source_surface": "artifact_runtime_proof",
                            "is_open_blocker": False,
                            "is_quality_gate": False,
                            "raw_terminal_log": "COCKPIT_RAW_LOG_CANARY",
                        }
                    ],
                    "counts": {
                        "open_feedback_priority_count": 1,
                        "open_feedback_frequency": 3,
                        "system_improvement_priority_count": 1,
                        "system_improvement_frequency": 5,
                    },
                    "authority_contract": {
                        "report_can_authorize_quality": False,
                        "report_can_authorize_submission": False,
                        "repeat_toil_is_quality_gate": False,
                    },
                },
            },
            "ai_first_action_dispatch_lifecycle": {
                "surface": "ai_first_action_dispatch_lifecycle",
                "read_model": "operator_action_lifecycle_read_model",
                "authority": "operations_governance_only",
                "status": "blocked",
                "counts": {
                    "open": 1,
                    "accepted": 1,
                    "in_progress": 1,
                    "blocked": 1,
                    "closed": 2,
                    "active": 4,
                    "total": 6,
                },
                "primary_action": {
                    "action_id": "return_to_ai_reviewer_workflow",
                    "target_surface": "ai_reviewer_runtime_workflow",
                    "summary": "补齐 AI reviewer workflow、publication eval 与 medical prose review。",
                    "status": "blocked",
                    "prompt": "internal prompt must stay hidden",
                    "token_count": 1234,
                },
                "user_view": {
                    "current_blocker": "补齐 AI reviewer workflow、publication eval 与 medical prose review。",
                    "next_step": "补齐 AI reviewer workflow、publication eval 与 medical prose review。",
                    "human_review_required": True,
                    "primary_action_status": "blocked",
                    "active_action_count": 4,
                },
            },
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [],
            "recovery_contract": {"action_mode": "inspect_progress"},
            "needs_physician_decision": False,
            "needs_user_decision": False,
            "supervision": {
                "browser_url": "http://127.0.0.1:20999",
                "quest_session_api_url": "http://127.0.0.1:20999/api/quests/001-risk/session",
                "active_run_id": "run-001",
                "health_status": "live",
                "supervisor_tick_status": "fresh",
            },
            "task_intake": {
                "task_intent": "推进 001-risk 到可投稿状态。",
                "journal_target": "BMC Medicine",
            },
            "progress_freshness": {"status": "fresh"},
        },
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
    markdown = module.render_workspace_cockpit_markdown(payload)

    state = payload["ai_first_operations_state"]
    assert payload["studies"][0]["ai_first_default_entry_state"]["surface"] == "ai_first_default_entry_state"
    assert payload["studies"][0]["ai_first_operations_dashboard"]["surface"] == "ai_first_operations_dashboard_summary"
    assert state["authority"] == "observability_only"
    assert state["read_model"] == "ai_first_default_entry_state_read_model"
    assert state["status"] == "attention_required"
    assert state["counts"]["dashboard_count"] == 1
    assert state["counts"]["default_entry_state_count"] == 1
    assert state["counts"]["ai_reviewer_trace_incomplete"] == 1
    assert state["counts"]["route_back_active"] == 1
    assert state["counts"]["artifact_refresh_pending"] == 1
    assert state["counts"]["human_review_required"] == 1
    assert state["counts"]["feedback_state_count"] == 1
    assert state["counts"]["open_feedback_count"] == 3
    assert state["counts"]["repeat_toil_count"] == 1
    assert state["counts"]["manual_judgment_pending"] == 1
    assert state["counts"]["action_lifecycle_count"] == 1
    assert state["counts"]["action_open"] == 1
    assert state["counts"]["action_accepted"] == 1
    assert state["counts"]["action_in_progress"] == 1
    assert state["counts"]["action_blocked"] == 1
    assert state["counts"]["action_closed"] == 2
    assert state["counts"]["action_active"] == 4
    assert state["counts"]["quality_learning_open_priority_count"] == 1
    assert state["counts"]["quality_learning_system_improvement_count"] == 1
    assert state["study_dashboards"][0]["route_back_target"] == "analysis-campaign"
    assert state["study_dashboards"][0]["feedback_primary_category"] == "ai_reviewer_trace_gap"
    assert state["study_dashboards"][0]["feedback_primary_reason"] == "当前质量判断仍是机械投影。"
    assert state["study_dashboards"][0]["feedback_action_id"] == "return_to_ai_reviewer_workflow"
    assert state["study_dashboards"][0]["feedback_action_summary"] == "补齐 AI reviewer workflow、publication eval 与 medical prose review。"
    assert state["study_dashboards"][0]["feedback_action_target_surface"] == "ai_reviewer_runtime_workflow"
    assert state["study_dashboards"][0]["action_primary_status"] == "blocked"
    assert state["study_dashboards"][0]["action_primary_id"] == "return_to_ai_reviewer_workflow"
    assert state["study_dashboards"][0]["action_primary_summary"] == "补齐 AI reviewer workflow、publication eval 与 medical prose review。"
    assert state["study_dashboards"][0]["quality_learning_operations_report_summary"] == "1 个 open feedback 维护优先项；1 个 repeat-toil 系统改进优先项。"
    assert state["study_dashboards"][0]["quality_learning_top_open_priority"]["reason"] == "当前质量判断仍是机械投影。"
    assert state["study_dashboards"][0]["quality_learning_top_system_improvement"]["reason"] == "canonical_artifact_rebuild_pending"
    assert state["study_dashboards"][0]["authority"] == "observability_only"
    assert "AI-first Operations" in markdown
    assert "pre-draft: pre-draft 已完成结构化初稿。" in markdown
    assert "AI reviewer workflow: AI reviewer workflow 正在补齐质量授权。" in markdown
    assert "artifact proof: artifact proof 等待 current_package 从 canonical source 刷新。" in markdown
    assert "route-back: route-back 指向 analysis-campaign。" in markdown
    assert "下一步: 先补齐 AI reviewer workflow，再刷新 artifact proof。" in markdown
    assert "人工判断: 等待人工判断是否释放投稿包。" in markdown
    assert "AI reviewer trace 不完整 1" in markdown
    assert "route-back 未闭环 1" in markdown
    assert "产物待刷新 1" in markdown
    assert "运行反馈 3" in markdown
    assert "重复返工 1" in markdown
    assert "动作未闭合 4" in markdown
    assert "动作阻塞 1" in markdown
    assert "反馈原因: 当前质量判断仍是机械投影。" in markdown
    assert "建议动作: 补齐 AI reviewer workflow、publication eval 与 medical prose review。" in markdown
    assert "动作生命周期: blocked；补齐 AI reviewer workflow、publication eval 与 medical prose review。" in markdown
    assert "quality learning open priorities 1" in markdown
    assert "system improvements 1" in markdown
    assert "反馈原因: 当前质量判断仍是机械投影。" in markdown
    assert "建议动作: 补齐 AI reviewer workflow、publication eval 与 medical prose review。" in markdown
    assert "Quality learning operations: 1 个 open feedback 维护优先项；1 个 repeat-toil 系统改进优先项。" in markdown
    assert "Maintainer priority: 当前质量判断仍是机械投影。 | frequency=3 | impact=ai_reviewer_runtime_workflow | fix_layer=AI reviewer trace contract" in markdown
    assert "System improvement priority: canonical_artifact_rebuild_pending | frequency=5 | impact=artifact_runtime_proof | fix_layer=artifact rebuild proof layer" in markdown
    assert "internal prompt" not in markdown
    assert "token_count" not in markdown
    assert "COCKPIT_PROMPT_CANARY" not in markdown
    assert "COCKPIT_RAW_LOG_CANARY" not in markdown
    assert "/tmp/internal.log" not in markdown
