from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_current_write_routeback_supersedes_stale_runtime_recovery_and_metadata_action(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / study_id
    publication_eval_path = _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": study_id,
                "auto_resume": True,
            },
            "quest_id": study_id,
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "runtime_health_snapshot": {
                "attempt_state": "escalated",
                "canonical_runtime_action": "escalate_runtime",
                "running_provider_attempt": False,
                "last_known_run_id": "opl-stage-attempt://sat_dm002_terminal_attempt",
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "publication gate remains blocked and recommends returning to write.",
            },
            "domain_transition": {
                "study_id": study_id,
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "next_work_unit": {
                    "unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
                    "lane": "write",
                    "summary": (
                        "Expand methods/model/display provenance and keep claims limited to risk "
                        "ordering plus recalibration-required absolute risk."
                    ),
                },
                "controller_action": "request_opl_stage_attempt",
                "owner": "write",
                "typed_blocker": None,
            },
            "interaction_arbitration": None,
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": "opl-stage-attempt://sat_dm002_current_write_attempt",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
                "next_action_summary": "继续按周期 supervisor tick 监管当前托管运行。",
                "latest_recorded_at": "2026-05-27T00:00:00+00:00",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id=study_id)

    assert result["current_stage"] == "publication_supervision"
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["intervention_lane"]["lane_id"] == "quality_floor_blocker"
    assert result["intervention_lane"]["route_target"] == "write"
    assert result["intervention_lane"]["work_unit_id"] == (
        "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
    )
    assert "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass" in (
        result["current_stage_summary"]
    )
    assert "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass" in (
        result["next_system_action"]
    )
    assert "显式 resume" not in result["next_system_action"]
    assert "补元数据" not in result["next_system_action"]
    assert result["operator_status_card"]["handling_state"] == "scientific_or_quality_repair_in_progress"
    assert "OPL current_control_state" not in result["operator_status_card"]["current_focus"]
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)
