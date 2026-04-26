def test_study_runtime_status_resumes_live_stale_decision_after_write_stage_ready(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "active_interaction_id": "progress-live-001",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-live-001",
                "pending_user_message_count": 0,
            }
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "clear",
            "blockers": [],
            "supervisor_phase": "write_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_write_stage",
            "deferred_downstream_actions": ["continue_bundle_stage"],
            "controller_stage_note": "write stage is clear and should continue",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live-001",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-live-001"],
            },
        },
    )
    study_progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress_module,
        "build_study_progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "current_stage": "manual_finishing",
            "current_stage_summary": "当前论文线已到投稿包里程碑。",
            "paper_stage": "bundle_stage_ready",
            "paper_stage_summary": "当前论文线已到投稿包里程碑。",
            "next_system_action": "等待显式接力。",
            "needs_physician_decision": False,
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stale_decision_after_write_stage_ready"
    assert result["publication_supervisor_state"]["current_required_action"] == "continue_write_stage"
    assert result["execution_owner_guard"]["supervisor_only"] is True
    assert result["execution_owner_guard"]["publication_gate_allows_direct_write"] is True


def test_study_runtime_status_resumes_live_stale_decision_after_bundle_stage_ready(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "active_interaction_id": "progress-live-001",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-live-001",
                "pending_user_message_count": 0,
            }
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
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live-001",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-live-001"],
            },
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stale_decision_after_write_stage_ready"
    assert result["publication_supervisor_state"]["current_required_action"] == "continue_bundle_stage"
    assert result["execution_owner_guard"]["supervisor_only"] is True
    assert result["execution_owner_guard"]["publication_gate_allows_direct_write"] is True


def test_ensure_study_runtime_enqueues_controller_reply_for_premature_completion_request(
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
    quest_root = profile.runtime_root / "001-risk"
    study_root = profile.workspace_root / "studies" / "001-risk"
    interaction_id = "decision-completion-001"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "waiting_for_user",
                "active_interaction_id": interaction_id,
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    decision_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-main"
        / "artifacts"
        / "decisions"
        / f"{interaction_id}.json"
    )
    write_text(
        decision_path,
        json.dumps(
            {
                "kind": "decision",
                "schema_version": 1,
                "artifact_id": interaction_id,
                "id": interaction_id,
                "quest_id": "001-risk",
                "created_at": "2026-04-09T01:24:52+00:00",
                "updated_at": "2026-04-09T01:24:52+00:00",
                "message": "[等待决策] 批准 completion。",
                "summary": "请求批准 completion。",
                "interaction_id": interaction_id,
                "expects_reply": True,
                "reply_mode": "blocking",
                "allow_free_text": True,
                "reply_schema": {"decision_type": "quest_completion_approval"},
                "guidance_vm": {"requires_user_decision": True},
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "blockers": ["forbidden_manuscript_terminology"],
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "paper bundle exists, but blockers still belong to the publishability surface",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {
                "status": "waiting_for_user",
                "waiting_interaction_id": interaction_id,
                "default_reply_interaction_id": interaction_id,
                "pending_decisions": [interaction_id],
                "active_interaction_id": interaction_id,
            },
        },
        raising=False,
    )
    resumed: dict[str, object] = {}

    def fake_resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        resumed.update(
            {
                "runtime_root": runtime_root,
                "quest_id": quest_id,
                "source": source,
            }
        )
        return {
            "ok": True,
            "quest_id": quest_id,
            "action": "resume",
            "status": "active",
            "snapshot": {
                "quest_id": quest_id,
                "status": "active",
            },
        }

    monkeypatch.setattr(_managed_runtime_transport(module), "resume_quest", fake_resume_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    queued_message = queue["pending"][0]
    updated_runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_completion_requested_before_publication_gate_clear"
    assert result["quest_status"] == "active"
    assert resumed == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
    assert len(queue["pending"]) == 1
    assert queued_message["source"] == "medautosci-test"
    assert queued_message["reply_to_interaction_id"] == interaction_id
    assert "暂不结题" in queued_message["content"]
    assert "publication gate" in queued_message["content"]
    assert updated_runtime_state["pending_user_message_count"] == 1
    binding = yaml.safe_load((study_root / "runtime_binding.yaml").read_text(encoding="utf-8"))
    assert binding["last_action"] == "resume"
    launch_report = json.loads((study_root / "artifacts" / "runtime" / "last_launch_report.json").read_text(encoding="utf-8"))
    assert launch_report["decision"] == "resume"
    assert launch_report["reason"] == "quest_completion_requested_before_publication_gate_clear"
    assert launch_report["daemon_result"]["action"] == "resume"


def test_ensure_study_runtime_queues_controller_message_for_live_write_drift_without_redundant_resume(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
                "pending_user_message_count": 0,
            }
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "blockers": [
                "active_run_drifting_into_write_without_gate_approval",
                "missing_reporting_guideline_checklist",
            ],
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live-001",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-live-001"],
            },
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda *, runtime_root, quest_id, source: pytest.fail("resume_quest should not run for an already-live reroute"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    updated_runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_drifting_into_write_without_gate_approval"
    assert len(queue["pending"]) == 1
    assert "publication gate 尚未放行写作" in queue["pending"][0]["content"]
    assert updated_runtime_state["pending_user_message_count"] == 1


def test_ensure_study_runtime_force_restarts_live_write_drift_after_repeated_same_fingerprint(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "active_interaction_id": "progress-live-001",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-live-001",
                "same_fingerprint_auto_turn_count": 3,
                "pending_user_message_count": 0,
            }
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "blockers": [
                "active_run_drifting_into_write_without_gate_approval",
                "medical_publication_surface_blocked",
            ],
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live-001",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-live-001"],
            },
        },
    )
    calls: list[tuple[str, str]] = []

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        calls.append(("pause", source))
        return {
            "ok": True,
            "quest_id": quest_id,
            "action": "pause",
            "snapshot": {
                "quest_id": quest_id,
                "status": "paused",
            },
        }

    def fake_resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        calls.append(("resume", source))
        return {
            "ok": True,
            "quest_id": quest_id,
            "action": "resume",
            "status": "active",
            "snapshot": {
                "quest_id": quest_id,
                "status": "active",
            },
        }

    monkeypatch.setattr(_managed_runtime_transport(module), "pause_quest", fake_pause_quest)
    monkeypatch.setattr(_managed_runtime_transport(module), "resume_quest", fake_resume_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_drifting_into_write_without_gate_approval"
    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert calls == [("pause", "medautosci-test"), ("resume", "medautosci-test")]
    assert len(queue["pending"]) == 1
    assert "publication gate 尚未放行写作" in queue["pending"][0]["content"]
    assert result["controller_reroute_restart"]["forced"] is True
    assert result["controller_reroute_restart"]["same_fingerprint_auto_turn_count"] == 3
    launch_report = json.loads((profile.workspace_root / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json").read_text(encoding="utf-8"))
    assert launch_report["daemon_result"]["action"] == "resume"


def test_ensure_study_runtime_force_restarts_live_write_drift_without_explicit_gate_blocker(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "active_interaction_id": "progress-live-001",
                "continuation_policy": "auto",
                "continuation_anchor": "write",
                "continuation_reason": "write:finish_proofing_and_submission_checks",
                "same_fingerprint_auto_turn_count": 3,
                "pending_user_message_count": 0,
            }
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "blockers": [
                "medical_publication_surface_blocked",
                "claim_evidence_consistency_failed",
            ],
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live-001",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-live-001"],
            },
        },
    )
    calls: list[tuple[str, str]] = []

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        calls.append(("pause", source))
        return {
            "ok": True,
            "quest_id": quest_id,
            "action": "pause",
            "snapshot": {
                "quest_id": quest_id,
                "status": "paused",
            },
        }

    def fake_resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        calls.append(("resume", source))
        return {
            "ok": True,
            "quest_id": quest_id,
            "action": "resume",
            "status": "active",
            "snapshot": {
                "quest_id": quest_id,
                "status": "active",
            },
        }

    monkeypatch.setattr(_managed_runtime_transport(module), "pause_quest", fake_pause_quest)
    monkeypatch.setattr(_managed_runtime_transport(module), "resume_quest", fake_resume_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_drifting_into_write_without_gate_approval"
    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert calls == [("pause", "medautosci-test"), ("resume", "medautosci-test")]
    assert len(queue["pending"]) == 1
    assert "publication gate 尚未放行写作" in queue["pending"][0]["content"]
    assert result["controller_reroute_restart"]["forced"] is True
    assert result["controller_reroute_restart"]["same_fingerprint_auto_turn_count"] == 3


def test_ensure_study_runtime_queues_controller_message_for_live_write_stage_ready_without_redundant_resume(
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-live-001",
                "active_interaction_id": "progress-live-001",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-live-001",
                "pending_user_message_count": 0,
            }
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "clear",
            "blockers": [],
            "supervisor_phase": "write_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_write_stage",
            "deferred_downstream_actions": ["continue_bundle_stage"],
            "controller_stage_note": "write stage is clear and should continue",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live-001",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-001",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-live-001"],
            },
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda *, runtime_root, quest_id, source: pytest.fail("resume_quest should not run for an already-live write-stage reroute"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    updated_runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stale_decision_after_write_stage_ready"
    assert len(queue["pending"]) == 1
    assert "publication gate 已放行写作" in queue["pending"][0]["content"]
    assert updated_runtime_state["pending_user_message_count"] == 1
