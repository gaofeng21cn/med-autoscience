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


def test_study_runtime_status_does_not_resume_paused_delivered_package_from_stale_revision_intake(
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
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    main_result_path = quest_root / "artifacts" / "results" / "main_result.json"
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
            }
        )
        + "\n",
    )
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
    gate_report = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-05T08:29:10+00:00",
        "quest_id": "001-risk",
        "paper_root": str(paper_root),
        "latest_gate_path": str(gate_report_path),
        "main_result_path": str(main_result_path),
        "submission_minimal_manifest_path": str(paper_root / "submission_minimal" / "submission_manifest.json"),
        "status": "blocked",
        "allow_write": False,
        "blockers": ["submission_surface_qc_failure_present"],
        "supervisor_phase": "bundle_stage_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": False,
        "current_required_action": "complete_bundle_stage",
        "deferred_downstream_actions": [],
        "controller_stage_note": "bundle-stage blockers remain on the finalize path",
    }
    work_unit_fingerprint = importlib.import_module(
        "med_autoscience.controllers.publication_work_units"
    ).derive_publication_work_units(gate_report)["fingerprint"]
    write_text(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::001-risk::001-risk::2026-05-05T08:29:10+00:00",
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-05-05T08:29:34+00:00",
                "evaluation_scope": "publication",
                "charter_context_ref": {
                    "ref": str(charter_path),
                    "charter_id": "charter::001-risk::v1",
                    "publication_objective": "Deliver a manuscript-safe submission package.",
                },
                "runtime_context_refs": {
                    "runtime_escalation_ref": str(
                        quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                    ),
                    "main_result_ref": str(main_result_path),
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(paper_root),
                    "submission_minimal_ref": str(paper_root / "submission_minimal" / "submission_manifest.json"),
                },
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "ai_reviewer_publication_assessment",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                },
                "verdict": {
                    "overall_verdict": "blocked",
                    "primary_claim_status": "partial",
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "blocked",
                        "summary": "AI reviewer judged the current package not ready for journal submission.",
                        "evidence_refs": [str(gate_report_path)],
                    }
                },
                "gaps": [
                    {"gap_type": "delivery", "severity": "must_fix"},
                    {"gap_type": "reporting", "severity": "must_fix"},
                ],
                "recommended_actions": [
                    {
                        "action_id": "action-explicit-user-handoff",
                        "action_type": "await_user_submission_metadata",
                        "priority": "later",
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "specificity_targets": [
                            {
                                "target_kind": "claim",
                                "target_id": "claim_evidence_map",
                                "source_path": str(paper_root / "claim_evidence_map.json"),
                                "blocking_reason": "submission_surface_qc_failure_present",
                            },
                            {
                                "target_kind": "figure",
                                "target_id": "figure_catalog",
                                "source_path": str(paper_root / "figures" / "figure_catalog.json"),
                                "blocking_reason": "submission_surface_qc_failure_present",
                            },
                            {
                                "target_kind": "table",
                                "target_id": "submission_table_or_manifest",
                                "source_path": str(paper_root / "submission_minimal" / "submission_manifest.json"),
                                "blocking_reason": "submission_surface_qc_failure_present",
                            },
                            {
                                "target_kind": "metric",
                                "target_id": "main_result_metrics",
                                "source_path": str(main_result_path),
                                "blocking_reason": "submission_surface_qc_failure_present",
                            },
                            {
                                "target_kind": "source_path",
                                "target_id": "publication_gate_source_path",
                                "source_path": str(gate_report_path),
                                "blocking_reason": "submission_surface_qc_failure_present",
                            },
                        ],
                    }
                ],
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
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda **kwargs: pytest.fail("read-only status must not resume from stale revision intake"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["quest_status"] == "paused"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["auto_runtime_parked"]["parked"] is True
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] != "external_supervisor_required"


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
    current_package_root = study_root / "manuscript" / "current_package"
    (current_package_root / "figures").mkdir(parents=True, exist_ok=True)
    (current_package_root / "figures" / "Figure1.png").write_text("figure", encoding="utf-8")
    (current_package_root / "tables").mkdir(parents=True, exist_ok=True)
    (current_package_root / "tables" / "Table1.md").write_text("table", encoding="utf-8")
    write_text(
        current_package_root / "audit" / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "figures": [{"figure_id": "Figure1"}],
                "tables": [{"table_id": "Table1"}],
                "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
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
    current_package_root = study_root / "manuscript" / "current_package"
    (current_package_root / "figures").mkdir(parents=True, exist_ok=True)
    (current_package_root / "figures" / "Figure1.png").write_text("figure", encoding="utf-8")
    (current_package_root / "tables").mkdir(parents=True, exist_ok=True)
    (current_package_root / "tables" / "Table1.md").write_text("table", encoding="utf-8")
    write_text(
        current_package_root / "audit" / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "figures": [{"figure_id": "Figure1"}],
                "tables": [{"table_id": "Table1"}],
                "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
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
