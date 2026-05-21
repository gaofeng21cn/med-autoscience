from __future__ import annotations

from tests.test_study_runtime_router_cases.shared import *  # noqa: F403


def test_execute_pause_runtime_decision_records_nested_pause_daemon_step(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")
    status = module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(profile.workspace_root / "studies" / "001-risk"),
            "entry_mode": "full_research",
            "execution": {"quest_id": "001-risk", "auto_resume": True},
            "quest_id": "001-risk",
            "quest_root": str(profile.runtime_root / "001-risk"),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(profile.workspace_root / "studies" / "001-risk" / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "pause",
            "reason": "runtime_reentry_not_ready_for_running_quest",
        }
    )
    context = module._build_execution_context(
        profile=profile,
        study_id="001-risk",
        study_root=profile.workspace_root / "studies" / "001-risk",
        study_payload=yaml.safe_load((profile.workspace_root / "studies" / "001-risk" / "study.yaml").read_text(encoding="utf-8")),
        source="test",
    )
    monkeypatch.setattr(
        transport,
        "pause_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "paused"},
    )

    outcome = module._execute_pause_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.PAUSE
    assert outcome.daemon_result == {"pause": {"ok": True, "status": "paused"}}
    assert outcome.daemon_step("pause") == {"ok": True, "status": "paused"}
    assert status.quest_status is module.StudyRuntimeQuestStatus.PAUSED


def test_pause_study_runtime_records_takeover_and_persists_pause(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    seen: dict[str, object] = {}

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
        transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "active_run_id": "run-001",
            "worker_running": True,
            "bash_session_audit": {"ok": True, "status": "none"},
        },
    )
    monkeypatch.setattr(
        transport,
        "pause_quest",
        lambda *, runtime_root, quest_id, source: {
            "ok": True,
            "status": "paused",
            "snapshot": {"status": "paused", "active_run_id": None},
        },
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "persist_runtime_artifacts",
        lambda **kwargs: seen.setdefault("persist_calls", []).append(kwargs)
        or module.study_runtime_protocol.StudyRuntimeArtifacts(
            runtime_binding_path=kwargs["runtime_binding_path"],
            launch_report_path=kwargs["launch_report_path"],
            startup_payload_path=kwargs["startup_payload_path"],
        ),
    )

    result = module.pause_study_runtime(
        profile=profile,
        study_root=study_root,
        source="test-human-takeover",
    )

    assert result["decision"] == "pause"
    assert result["reason"] == "human_takeover_requested"
    assert result["quest_status"] == "paused"
    assert result["foreground_takeover"]["status"] == "runtime_paused_for_human_takeover"
    assert len(seen["persist_calls"]) == 1
    assert seen["persist_calls"][0]["last_action"] == "pause"
    assert seen["persist_calls"][0]["daemon_result"]["status"] == "paused"


def test_pause_study_runtime_clears_stale_platform_repair_redrive(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "001-risk"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        runtime_state_path,
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
        transport,
        "pause_quest",
        lambda *, runtime_root, quest_id, source: {
            "ok": True,
            "status": "paused",
            "snapshot": {"status": "paused", "active_run_id": None, "worker_running": False},
        },
    )

    result = module.pause_study_runtime(
        profile=profile,
        study_root=study_root,
        source="test-human-takeover",
    )
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))

    assert result["decision"] == "pause"
    assert result["quest_status"] == "paused"
    assert "stop_reason" not in runtime_state
    assert runtime_state["continuation_policy"] == "controller_review"
    assert runtime_state["continuation_anchor"] == "human_takeover"
    assert runtime_state["continuation_reason"] == "human_takeover_requested"
    assert runtime_state["last_platform_repair_redrive_clearance"]["source"] == "test-human-takeover"
    assert runtime_state["human_takeover_contract"]["source"] == "test-human-takeover"


def test_ensure_study_runtime_persists_legacy_resume_daemon_result_shape_after_explicit_wakeup(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
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
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(runtime_state_path, '{"status":"paused"}\n')
    seen: dict[str, object] = {}

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
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "active"},
    )
    monkeypatch.setattr(
        module.study_runtime_protocol,
        "persist_runtime_artifacts",
        lambda **kwargs: seen.setdefault("persist_calls", []).append(kwargs)
        or module.study_runtime_protocol.StudyRuntimeArtifacts(
            runtime_binding_path=kwargs["runtime_binding_path"],
            launch_report_path=kwargs["launch_report_path"],
            startup_payload_path=kwargs["startup_payload_path"],
        ),
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id="001-risk",
        explicit_user_wakeup=True,
        source="medautosci-test",
    )

    assert result["decision"] == "resume"
    assert result["explicit_user_wakeup"]["cleared_bare_paused"] is True
    assert len(seen["persist_calls"]) == 1
    assert seen["persist_calls"][0]["last_action"] == "resume"
    assert seen["persist_calls"][0]["daemon_result"] == {"ok": True, "status": "active"}
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert runtime_state["last_explicit_user_wakeup"]["cleared_bare_paused"] is True


def test_execute_runtime_decision_rejects_unknown_decision(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-risk")

    resolved_study_id, resolved_study_root, study_payload = module._resolve_study(
        profile=profile,
        study_id="001-risk",
        study_root=None,
    )
    status = module._status_state(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=None,
    )
    status.decision = "unexpected_action"
    status.reason = module.StudyRuntimeReason.QUEST_ALREADY_COMPLETED
    context = module._build_execution_context(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        source="test",
    )

    with pytest.raises(ValueError, match="unsupported study runtime decision"):
        module._execute_runtime_decision(status=status, context=context)
