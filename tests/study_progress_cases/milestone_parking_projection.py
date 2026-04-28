from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_keeps_human_review_milestone_parking_out_of_runtime_recovery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "schema_version": 1,
            "recorded_at": "2026-04-12T10:16:47+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "health_status": "recovering",
            "summary": "系统正在自动启动或恢复托管运行。",
            "next_action_summary": "等待下一次巡检确认 worker 已重新上线并恢复 live。",
            "active_run_id": None,
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "runtime_liveness_status": "none",
            "runtime_liveness_audit": {
                "status": "none",
                "live_session_count": 0,
                "matching_session_count": 0,
            },
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "complete_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "投稿包里程碑已到达，等待人审或外部投稿元数据。",
            },
            "autonomous_runtime_notice": {},
            "execution_owner_guard": {
                "owner": "manual_finishing",
                "supervisor_only": False,
                "current_required_action": "inspect_progress",
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_publication_gate_state",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "pending_user_interaction": {},
            "interaction_arbitration": None,
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-04-12T10:16:47+00:00",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "auto_runtime_parked"
    assert result["parked_state"] == "package_ready_handoff"
    assert result["legacy_current_stage"] == "manual_finishing"
    assert result["intervention_lane"]["lane_id"] == "auto_runtime_parked"
    assert result["intervention_lane"]["parked_state"] == "package_ready_handoff"
    assert all("恢复失败" not in item for item in result["current_blockers"])
    assert result["operator_status_card"]["handling_state"] == "package_ready_handoff"
    assert result["operator_status_card"]["resource_release_expected"] is True
    assert result["operator_status_card"]["user_visible_verdict"] == (
        "MAS/MDS 已到投稿包/人审包交付节点，当前停驻等待用户审阅或显式恢复。"
    )
    assert "等待用户审阅" in result["next_system_action"]
    assert "显式恢复" in result["next_system_action"]
    assert "worker" not in result["next_system_action"]
    assert "恢复 live" not in result["operator_status_card"]["current_focus"]
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
