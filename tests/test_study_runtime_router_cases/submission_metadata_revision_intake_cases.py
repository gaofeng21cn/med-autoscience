def test_explicit_reviewer_revision_intake_resumes_paused_delivered_package(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=[
            "author_metadata",
            "ethics_statement",
            "human_subjects_consent_statement",
            "ai_declaration",
        ],
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "emitted_at": "2026-04-25T03:00:00+00:00",
                "entry_mode": "full_research",
                "task_intent": "Reviewer revision: absorb reviewer feedback and revise manuscript tables and figures.",
                "constraints": [
                    "Treat this as explicit user wakeup after submission-package parking.",
                    "Do not keep the previous submission-ready/finalize parking state as current truth.",
                ],
                "first_cycle_outputs": ["revised manuscript package"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    calls: list[str] = []
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
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append("prepare_overlay") or make_runtime_overlay_result(),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append("sync_context")
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append("resume")
        or {"ok": True, "status": "running", "snapshot": {"status": "running"}},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="user_explicit_wakeup")

    assert result["decision"] == "resume"
    assert result["quest_status"] == "running"
    assert calls == ["prepare_overlay", "sync_context", "resume"]


def test_explicit_reviewer_revision_intake_keeps_live_delivered_package_running(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-revision",
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "emitted_at": "2026-04-25T03:00:00+00:00",
                "entry_mode": "full_research",
                "task_intent": "Reviewer revision: absorb reviewer feedback and revise manuscript tables and figures.",
                "constraints": [
                    "Treat this as explicit user wakeup after submission-package parking.",
                    "Do not keep the previous submission-ready/finalize parking state as current truth.",
                ],
                "first_cycle_outputs": ["revised manuscript package"],
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
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live-revision",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-revision",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {"ok": True, "status": "none"},
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "pause_quest",
        lambda **kwargs: pytest.fail("pause_quest should not run for explicit reviewer revision wakeup"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="user_explicit_wakeup")

    assert result["decision"] == "noop"
    assert result["reason"] == "quest_already_running"
    assert result["quest_status"] == "running"


def test_runtime_platform_repair_redrive_does_not_reopen_reviewer_revision_package_without_worker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "active",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "emitted_at": "2026-04-25T03:00:00+00:00",
                "entry_mode": "full_research",
                "task_intent": "Reviewer revision: absorb reviewer feedback and revise manuscript tables and figures.",
                "constraints": [
                    "Treat this as explicit user wakeup after submission-package parking.",
                    "Do not keep the previous submission-ready/finalize parking state as current truth.",
                ],
                "first_cycle_outputs": ["revised manuscript package"],
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
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
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
                "session_count": 1,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda **kwargs: pytest.fail("platform repair redrive must not reopen reviewer revision without a live worker"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="runtime_platform_repair")

    assert result["quest_status"] == "active"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["auto_runtime_parked"]["parked"] is True


def test_paused_runtime_platform_repair_redrive_does_not_resume_reviewer_revision_package(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "emitted_at": "2026-04-25T03:00:00+00:00",
                "entry_mode": "full_research",
                "task_intent": "Reviewer revision: absorb reviewer feedback and revise manuscript tables and figures.",
                "constraints": [
                    "Treat this as explicit user wakeup after submission-package parking.",
                    "Do not keep the previous submission-ready/finalize parking state as current truth.",
                ],
                "first_cycle_outputs": ["revised manuscript package"],
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
        "resume_quest",
        lambda **kwargs: pytest.fail("paused platform repair redrive must not resume reviewer revision package"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="runtime_platform_repair")

    assert result["quest_status"] == "paused"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["auto_runtime_parked"]["parked"] is True
