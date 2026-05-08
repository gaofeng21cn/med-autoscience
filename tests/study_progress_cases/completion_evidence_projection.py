from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_does_not_project_study_completed_when_completion_contract_is_not_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-002",
                "auto_resume": False,
            },
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "completed",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {
                "ready": False,
                "status": "incomplete",
                "completion_status": "completed",
                "summary": "论文交付声明已写，但 final submission evidence 还没真正补齐。",
                "missing_evidence_paths": ["manuscript/final/submission_manifest.json"],
            },
            "decision": "blocked",
            "reason": "study_completion_contract_not_ready",
            "publication_supervisor_state": {
                "supervisor_phase": "scientific_anchor_missing",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": False,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "reason": "supervisor_tick_report_fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_report_path": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "latest_recorded_at": "2026-04-10T09:00:00+00:00",
                "seconds_since_latest_recorded_at": 30,
                "expected_interval_seconds": 300,
                "stale_after_seconds": 600,
            },
            "continuation_state": {
                "quest_status": "completed",
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": None,
                "continuation_reason": None,
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["current_stage"] == "runtime_blocked"
    assert "收尾/交付" not in result["current_stage_summary"]
    assert result["intervention_lane"]["lane_id"] == "completion_evidence_required"
    assert result["operator_status_card"]["handling_state"] == "completion_evidence_required"
    assert "final submission 证据" in result["operator_status_card"]["current_focus"]
    assert any("final submission 证据还未补齐" in item for item in result["current_blockers"])


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
