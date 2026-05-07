from .shared import *  # noqa: F403


def test_study_runtime_status_invalidates_stale_live_launch_report_when_no_worker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    write_text(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        json.dumps(
            {
                "decision": "noop",
                "reason": "quest_already_running",
                "quest_status": "running",
                "active_run_id": "run-stale-launch",
                "runtime_liveness_status": "live",
                "runtime_liveness_audit": {
                    "status": "live",
                    "active_run_id": "run-stale-launch",
                    "runtime_audit": {
                        "status": "live",
                        "active_run_id": "run-stale-launch",
                        "worker_running": True,
                    },
                },
                "recorded_at": "2026-04-10T09:20:00+00:00",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "daemon_turn_worker",
            "active_run_id": None,
            "worker_running": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 0,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resolve_daemon_url",
        lambda *, runtime_root: "http://127.0.0.1:21999",
    )
    _patch_decision_supervisor_tick_now(
        monkeypatch,
        decision_module,
        lambda: decision_module.datetime.fromisoformat("2026-04-10T09:30:00+00:00"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "publishability gate still owns the critical path",
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result.get("active_run_id") is None
    assert "autonomous_runtime_notice" not in result
    assert "execution_owner_guard" not in result
    assert result["runtime_liveness_audit"]["status"] == "none"
    assert result["runtime_summary_alignment"]["aligned"] is False
    assert result["runtime_summary_alignment"]["launch_report_stale"] is True
    assert result["runtime_summary_alignment"]["stale_launch_report_active_run_id"] == "run-stale-launch"
    assert result["progress_projection"]["active_run_id"] is None
    assert result["progress_projection"]["supervision"]["active_run_id"] is None
    refreshed_launch_report = json.loads(
        (study_root / "artifacts" / "runtime" / "last_launch_report.json").read_text(encoding="utf-8")
    )
    assert refreshed_launch_report.get("active_run_id") is None
    assert refreshed_launch_report["runtime_liveness_status"] == "none"
    assert refreshed_launch_report["runtime_liveness_audit"]["status"] == "none"
    assert refreshed_launch_report["last_known_run_id"] == "run-stale-launch"
    assert refreshed_launch_report["stale_launch_report_invalidated"] is True
