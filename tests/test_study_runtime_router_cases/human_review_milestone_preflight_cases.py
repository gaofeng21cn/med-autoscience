def test_study_runtime_status_keeps_delivered_human_review_milestone_parked_before_preflight_contracts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-endocrine-burden-followup",
        quest_id="003-endocrine-burden-followup-managed-20260402",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Endocrine follow-up burden manuscript is ready for human review.",
        paper_urls=["https://example.org/paper-3"],
        journal_shortlist=["Pituitary"],
        minimum_sci_ready_evidence_package=["follow_up_burden_table"],
    )
    quest_root = profile.runtime_root / "003-endocrine-burden-followup-managed-20260402"
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_publication_gate_state",
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_text(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "decision_type": "continue_same_line",
                "reason": "Human-review milestone reached; stop the live runtime and wait for explicit resume.",
                "route_target": "finalize",
                "controller_actions": [{"action_type": "stop_runtime"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    _materialize_bundle_only_remaining_evaluation_summary(study_root=study_root, quest_root=quest_root)
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": False,
            "runtime_contract": {"ready": True},
            "launcher_contract": {
                "ready": False,
                "issues": ["launcher_contract.med_deepscientist_launcher_not_placeholder"],
            },
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "003-endocrine-burden-followup"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "clear",
            "blockers": [],
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {"ok": True, "status": "none", "session_count": 0, "live_session_count": 0},
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="003-endocrine-burden-followup")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_parked_on_unchanged_finalize_state", result
    assert result["auto_runtime_parked"]["parked"] is True
    assert result["auto_runtime_parked"]["parked_state"] == "package_ready_handoff"
    assert result["runtime_health_snapshot"]["attempt_state"] == "awaiting_explicit_resume"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "await_explicit_resume"
