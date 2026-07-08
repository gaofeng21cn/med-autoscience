from __future__ import annotations

from med_autoscience.controllers.study_progress.markdown_projection_rendering import render_study_progress_markdown

from tests.study_progress_cases.shared import *  # noqa: F403,F401


def test_study_progress_projects_stale_progress_signal_for_active_runtime(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"

    _write_publication_eval(study_root, quest_root)
    _write_runtime_readback_report(quest_root)
    _write_bash_summary(quest_root)
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="持续推进论文主线，并在卡住时及时暴露给用户。",
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
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
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_id": "quest-001",
                "quest_status": "running",
                "active_run_id": "run-001",
                "browser_url": "http://127.0.0.1:21999/quests/quest-001",
                "quest_session_api_url": "http://127.0.0.1:21999/api/sessions/run-001",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "active_run_id": "run-001",
                "current_required_action": "supervise_runtime_only",
                "publication_gate_allows_direct_write": False,
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "latest_recorded_at": "2026-04-12T09:50:00+00:00",
            },
        },
    )
    monkeypatch.setattr(
        importlib.import_module("med_autoscience.controllers.study_progress.shared"),
        "_progress_freshness_now",
        lambda: datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "publication_supervision"
    assert result["progress_freshness"]["status"] == "stale"
    assert "超过 12 小时" in result["progress_freshness"]["summary"]
    assert any("超过 12 小时" in item for item in result["current_blockers"])


def test_study_progress_prioritizes_runtime_supervision_alerts_over_paper_stage_when_runtime_is_escalated(
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_publication_eval(study_root, quest_root)
    _write_runtime_readback_report(quest_root)
    opl_runtime_owner_handoff_path = study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
    _write_json(
        opl_runtime_owner_handoff_path,
        {
            "schema_version": 1,
            "surface_kind": "opl_runtime_owner_handoff",
            "recorded_at": "2026-04-10T09:13:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "summary": "OPL owner handoff recorded; runtime health is derived from OPL/status refs.",
            "mas_materializes_runtime_supervision": False,
            "mas_runtime_read_model_retired": True,
        },
    )
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "blocked",
            "reason": "resume_request_failed",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-escalated-001",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "worker_liveness_state": {"state": "missing_live_session"},
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "quest_status": "running",
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
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
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "resume_request_failed",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-escalated-001",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "worker_liveness_state": {"state": "missing_live_session"},
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": ["submission_minimal"],
                "controller_stage_note": "论文还没有通过可写门控，bundle 打包仍然属于后续步骤。",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "managed_runtime_audit_unhealthy",
                "active_run_id": "run-001",
                "current_required_action": "inspect_runtime_health_and_decide_intervention",
                "allowed_actions": ["read_status", "monitor_runtime"],
                "forbidden_actions": ["write_runtime_owned_roots"],
                "runtime_owned_roots": [str(quest_root / ".ds")],
                "takeover_required": True,
                "takeover_action": "pause_before_takeover",
                "publication_gate_allows_direct_write": False,
                "controller_stage_note": "当前只能做监管，不能直接越过托管运行时写入其拥有的表面。",
            },
        },
    )

    profile_ref = tmp_path / "profile.local.toml"

    result = module.read_study_progress(profile=profile, study_id="001-risk", profile_ref=profile_ref)

    assert result["current_stage"] == "managed_runtime_escalated"
    assert "OPL runtime refs" in result["current_stage_summary"]
    assert result["intervention_lane"]["lane_id"] == "runtime_recovery_required"
    assert result["intervention_lane"]["recommended_action_id"] == "continue_or_relaunch"
    assert result["operator_verdict"]["surface_kind"] == "study_operator_verdict"
    assert result["operator_verdict"]["lane_id"] == "runtime_recovery_required"
    assert result["operator_verdict"]["decision_mode"] == "intervene_now"
    assert result["operator_verdict"]["primary_step_id"] == "continue_or_relaunch"
    assert result["recommended_command"].endswith(
        "study launch --profile " + str(profile_ref.resolve()) + " --study-id 001-risk"
    )
    assert result["recommended_commands"][0]["step_id"] == "continue_or_relaunch"
    assert result["recommended_commands"][0]["surface_kind"] == "launch_study"
    assert result["recovery_contract"]["contract_kind"] == "study_recovery_contract"
    assert result["recovery_contract"]["lane_id"] == "runtime_recovery_required"
    assert result["recovery_contract"]["action_mode"] == "continue_or_relaunch"
    assert result["autonomy_contract"]["contract_kind"] == "study_autonomy_contract"
    assert result["autonomy_contract"]["autonomy_state"] == "runtime_recovery"
    projection = result["research_runtime_control_projection"]
    assert projection["surface_kind"] == "research_runtime_control_projection"
    assert projection["session_lineage_surface"]["field_path"] == "family_checkpoint_lineage"
    assert projection["restore_point_surface"]["field_path"] == "autonomy_contract.restore_point"
    assert projection["progress_surface"]["field_path"] == "operator_status_card.current_focus"
    assert projection["artifact_pickup_surface"]["field_path"] == "refs.evaluation_summary_path"
    assert str(study_root / "artifacts" / "publication_eval" / "latest.json") in projection["artifact_pickup_surface"]["pickup_refs"]
    assert str(study_root / "artifacts" / "controller_decisions" / "latest.json") in projection["artifact_pickup_surface"][
        "pickup_refs"
    ]
    assert projection["research_gate_surface"]["approval_gate_field"] == "needs_user_decision"
    assert projection["research_gate_surface"]["legacy_approval_gate_field"] == "needs_physician_decision"
    assert projection["research_gate_surface"]["approval_gate_required"] is False
    assert projection["research_gate_surface"]["interrupt_policy"] == "continue_or_relaunch"
    assert result["latest_events"][0]["category"] == "opl_runtime_owner_handoff"
    assert "OPL owner handoff recorded" in result["latest_events"][0]["summary"]
    assert any("runtime recovery retry budget exhausted" in item for item in result["current_blockers"])
    assert "OPL current_control_state" in result["next_system_action"]
    assert "MedDeepScientist" not in result["next_system_action"]
    assert result["refs"]["opl_runtime_owner_handoff_path"] == str(opl_runtime_owner_handoff_path)
    markdown = render_study_progress_markdown(result)
    assert markdown.strip()


def test_study_progress_autonomy_contract_projects_restore_point_from_checkpoint_lineage(
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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "当前同线质量修复仍在继续。",
            },
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-001",
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "family_checkpoint_lineage": {
                "version": "family-checkpoint-lineage.v1",
                "resume_contract": {
                    "resume_mode": "resume_from_checkpoint",
                    "human_gate_required": False,
                },
            },
            "pending_user_interaction": {},
            "interaction_arbitration": None,
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["autonomy_contract"]["autonomy_state"] == "autonomous_progress"
    assert result["autonomy_contract"]["latest_outer_loop_dispatch"] is None
    assert result["autonomy_contract"]["restore_point"] == {
        "resume_mode": "resume_from_checkpoint",
        "continuation_policy": "wait_for_user_or_resume",
        "continuation_reason": "运行停在未变化的定稿总结态",
        "human_gate_required": False,
        "summary": "当前恢复点采用 resume_from_checkpoint；continuation policy 为 wait_for_user_or_resume；最近一次续跑原因是运行停在未变化的定稿总结态。",
    }
    projection = result["research_runtime_control_projection"]
    assert projection["session_lineage_surface"]["lineage_version"] == "family-checkpoint-lineage.v1"
    assert projection["session_lineage_surface"]["continuation_anchor"] == "decision"
    assert projection["restore_point_surface"]["lineage_anchor_field"] == "family_checkpoint_lineage.resume_contract"
    assert projection["research_gate_surface"]["approval_gate_required"] is False
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
