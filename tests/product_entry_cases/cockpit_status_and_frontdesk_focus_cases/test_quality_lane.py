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


def test_workspace_cockpit_projects_quality_execution_lane_into_attention_and_brief(
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
            "current_stage": {"id": "f4_blocker_closeout", "status": "in_progress", "summary": "继续收口 blocker。"},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前还在同线质量修复。",
            "current_blockers": ["当前稿面仍需最小 claim-evidence 修复。"],
            "next_system_action": "继续当前质量修复。",
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "title": "优先处理 claim-evidence 修复",
                "severity": "warning",
                "summary": "当前稿面仍需最小 claim-evidence 修复。",
                "recommended_action_id": "inspect_progress",
            },
            "operator_verdict": {
                "surface_kind": "study_operator_verdict",
                "verdict_id": "study_operator_verdict::001-risk::quality_floor_blocker",
                "study_id": "001-risk",
                "lane_id": "quality_floor_blocker",
                "severity": "warning",
                "decision_mode": "monitor_only",
                "needs_intervention": False,
                "focus_scope": "study",
                "summary": "当前稿面仍需最小 claim-evidence 修复。",
                "reason_summary": "当前稿面仍需最小 claim-evidence 修复。",
                "primary_step_id": "inspect_study_progress",
                "primary_surface_kind": "study_progress",
                "primary_command": (
                    "uv run python -m med_autoscience.cli study-progress --profile "
                    + str(profile_ref.resolve())
                    + " --study-id 001-risk"
                ),
            },
            "operator_status_card": {
                "surface_kind": "study_operator_status_card",
                "handling_state": "scientific_or_quality_repair_in_progress",
                "owner_summary": "MAS 正在处理当前论文线的质量修复。",
                "latest_truth_time": "2026-04-12T09:30:00+00:00",
                "latest_truth_source": "publication_eval",
                "human_surface_freshness": "fresh",
                "next_confirmation_signal": "看 publication_eval/latest.json 是否继续收窄当前修复线。",
                "user_visible_verdict": "MAS 正在处理当前论文线的质量修复。",
            },
            "quality_closure_truth": {
                "summary": "核心科学质量还没有闭环；当前仍需先补齐论文质量缺口。",
            },
            "quality_execution_lane": {
                "lane_id": "claim_evidence",
                "route_key_question": "当前稿面最窄的 claim-evidence 修复动作是什么？",
                "summary": "当前质量执行线聚焦 claim-evidence 修复；先进入 analysis-campaign，回答“当前稿面最窄的 claim-evidence 修复动作是什么？”。",
            },
            "same_line_route_truth": {
                "surface_kind": "same_line_route_truth",
                "same_line_state": "bounded_analysis",
                "same_line_state_label": "有限补充分析",
                "route_mode": "enter",
                "route_target": "analysis-campaign",
                "route_target_label": "补充分析与稳健性验证",
                "summary": "当前论文线仍在同线质量修复；先进入 analysis-campaign 收口当前最窄 claim-evidence 缺口。",
                "current_focus": "当前稿面最窄的 claim-evidence 修复动作是什么？",
            },
            "research_runtime_control_projection": {
                "surface_kind": "research_runtime_control_projection",
                "restore_point_surface": {
                    "surface_kind": "study_progress",
                    "field_path": "autonomy_contract.restore_point",
                },
                "research_gate_surface": {
                    "surface_kind": "study_progress",
                    "approval_gate_field": "needs_user_decision",
                    "interrupt_policy_field": "intervention_lane.recommended_action_id",
                },
            },
            "recommended_command": (
                "uv run python -m med_autoscience.cli study-progress --profile "
                + str(profile_ref.resolve())
                + " --study-id 001-risk"
            ),
            "recommended_commands": [],
            "recovery_contract": {
                "contract_kind": "study_recovery_contract",
                "lane_id": "quality_floor_blocker",
                "action_mode": "inspect_progress",
                "summary": "当前稿面仍需最小 claim-evidence 修复。",
                "recommended_step_id": "inspect_study_progress",
                "steps": [],
            },
            "needs_physician_decision": False,
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
            "progress_freshness": {
                "status": "fresh",
                "summary": "最近 12 小时内仍有明确研究推进记录。",
            },
        },
    )

    payload = module.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    assert payload["attention_queue"][0]["recommended_step_id"] == "inspect_study_progress"
    assert payload["operator_brief"]["recommended_step_id"] == "inspect_study_progress"
    assert payload["attention_queue"][0]["quality_execution_lane"]["route_key_question"] == "当前稿面最窄的 claim-evidence 修复动作是什么？"
    assert payload["attention_queue"][0]["same_line_route_truth"]["route_target"] == "analysis-campaign"
    gate_surface = payload["studies"][0]["research_runtime_control_projection"]["research_gate_surface"]
    assert gate_surface["approval_gate_field"] == "needs_user_decision"
    assert gate_surface["legacy_approval_gate_field"] == "needs_physician_decision"
    assert payload["operator_brief"]["current_focus"] == "当前稿面最窄的 claim-evidence 修复动作是什么？"
