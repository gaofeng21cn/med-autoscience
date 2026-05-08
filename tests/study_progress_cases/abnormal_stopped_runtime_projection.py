from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_does_not_project_abnormal_stopped_blocked_bundle_as_package_handoff(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-dm-cvd-mortality-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8")
        + "\n".join(
            [
                "",
                "manual_finish:",
                "  status: active",
                "  summary: Historical manual-finish compatibility guard.",
                "  next_action_summary: Keep compatibility only.",
                "  compatibility_guard_only: true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    publication_eval_path = _write_publication_eval(
        study_root,
        quest_root,
        assessment_provenance={"owner": "mechanical_projection", "ai_reviewer_required": True},
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-dm-cvd-mortality-risk",
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
            "quest_status": "stopped",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_stopped_by_controller_guard",
            "runtime_reason": "quest_stopped_by_controller_guard",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "complete_bundle_stage",
                "controller_stage_note": "bundle-stage work is blocked and still needs controller-owned repair.",
            },
            "runtime_liveness_audit": {
                "status": "not_live",
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["quest_stopped_by_controller_guard"],
            },
            "runtime_supervision": {
                "health_status": "escalated",
                "summary": "The quest is stopped even though the controller requires resume.",
                "next_action_summary": "Relaunch the managed runtime before treating any package as delivered.",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_recorded_at": "2026-05-05T02:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "publication_eval": {
                "overall_verdict": "blocked",
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            },
            "continuation_state": {
                "quest_status": "stopped",
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "quest_stopped_by_controller_guard",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-dm-cvd-mortality-risk")

    assert result["current_stage"] == "managed_runtime_escalated"
    assert result["paper_stage"] == "bundle_stage_blocked"
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["auto_runtime_parked"]["auto_execution_complete"] is False
    assert result["operator_status_card"]["handling_state"] == "runtime_recovering"
    assert result["operator_status_card"]["human_surface_freshness"] == "monitoring_runtime"
    assert result["operator_status_card"]["user_visible_verdict"] == "MAS 正在处理 runtime recovery，当前 study 仍处在受管修复中。"
    assert result["operator_status_card"]["handling_state"] != "package_ready_handoff"
    assert "投稿包/人审包交付" not in result["operator_status_card"]["user_visible_verdict"]
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)

