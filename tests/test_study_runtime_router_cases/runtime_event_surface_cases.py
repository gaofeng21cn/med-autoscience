def _write_runtime_escalation_record_for_status_test(
    *,
    protocol,
    quest_root: Path,
    launch_report_path: Path,
):
    return protocol.write_runtime_escalation_record(
        quest_root=quest_root,
        record=protocol.RuntimeEscalationRecord(
            schema_version=1,
            record_id="runtime-escalation::001-risk::001-risk::startup_boundary_not_ready_for_resume::2026-04-05T06:00:00+00:00",
            study_id="001-risk",
            quest_id="001-risk",
            emitted_at="2026-04-05T06:00:00+00:00",
            trigger=protocol.RuntimeEscalationTrigger(
                trigger_id="startup_boundary_not_ready_for_resume",
                source="startup_boundary_gate",
            ),
            scope="quest",
            severity="quest",
            reason="startup_boundary_not_ready_for_resume",
            recommended_actions=("refresh_startup_hydration", "controller_review_required"),
            evidence_refs=(
                str(quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json"),
                str(quest_root / "artifacts" / "reports" / "startup" / "hydration_validation_report.json"),
            ),
            runtime_context_refs={"launch_report_path": str(launch_report_path)},
            summary_ref=str(launch_report_path),
            artifact_path=None,
        ),
    )


def _write_native_runtime_event_for_status_test(*, quest_root: Path, quest_id: str, quest_status: str) -> dict[str, object]:
    artifact_path = quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json"
    payload = {
        "schema_version": 1,
        "event_id": f"runtime-event::{quest_id}::{quest_status}::2026-04-11T00:00:00+00:00",
        "quest_id": quest_id,
        "emitted_at": "2026-04-11T00:00:00+00:00",
        "event_source": "daemon_app",
        "event_kind": "runtime_control_applied",
        "summary_ref": f"quest:{quest_id}:{quest_status}",
        "status_snapshot": {
            "quest_status": quest_status,
            "display_status": quest_status,
            "active_run_id": "run-native",
            "runtime_liveness_status": "live" if quest_status == "running" else "none",
            "worker_running": quest_status == "running",
            "stop_reason": None,
            "continuation_policy": "resume_allowed",
            "continuation_anchor": "decision",
            "continuation_reason": "native_runtime_truth",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
        "outer_loop_input": {
            "quest_status": quest_status,
            "display_status": quest_status,
            "active_run_id": "run-native",
            "runtime_liveness_status": "live" if quest_status == "running" else "none",
            "worker_running": quest_status == "running",
            "stop_reason": None,
            "continuation_policy": "resume_allowed",
            "continuation_anchor": "decision",
            "continuation_reason": "native_runtime_truth",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
        "artifact_path": str(artifact_path),
        "summary": f"native runtime event for {quest_status}",
    }
    write_text(
        artifact_path,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )
    return payload


def test_study_runtime_status_reads_only_runtime_escalation_ref_from_quest_artifact_when_blocked_refresh_is_active(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8").replace("  auto_resume: true\n", "  auto_resume: false\n"),
        encoding="utf-8",
    )
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    written_record = _write_runtime_escalation_record_for_status_test(
        protocol=protocol,
        quest_root=quest_root,
        launch_report_path=launch_report_path,
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_initialized_but_auto_resume_disabled"
    assert result["runtime_escalation_ref"] == written_record.ref().to_dict()
    assert "runtime_escalation_record" not in result
    assert "runtime_escalation_ref" not in result["execution"]
    serialized_result = json.dumps(result, ensure_ascii=False)
    assert "runtime_context_refs" not in serialized_result
    assert "recommended_actions" not in serialized_result


def test_study_runtime_status_does_not_expose_runtime_escalation_ref_for_non_med_deepscientist_execution(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
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
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8").replace(
            "  engine: med-deepscientist\n",
            "  engine: lightweight-runtime\n",
        ),
        encoding="utf-8",
    )
    quest_root = profile.runtime_root / "001-risk"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_runtime_escalation_record_for_status_test(
        protocol=protocol,
        quest_root=quest_root,
        launch_report_path=launch_report_path,
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "lightweight"
    assert result["reason"] == "study_execution_not_managed_runtime_backend"
    assert "runtime_escalation_ref" not in result


def test_study_runtime_status_does_not_echo_stale_runtime_escalation_ref_after_block_clears(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_runtime_escalation_record_for_status_test(
        protocol=protocol,
        quest_root=quest_root,
        launch_report_path=launch_report_path,
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_initialized_waiting_to_start"
    assert "runtime_escalation_ref" not in result


def test_study_runtime_status_uses_profile_default_hermes_substrate_for_legacy_managed_execution(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    profile = profile.__class__(**{**profile.__dict__, "managed_runtime_backend_id": "hermes"})
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')

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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["execution"]["runtime_backend_id"] == "hermes"
    assert result["execution"]["runtime_backend"] == "hermes"
    assert result["execution"]["runtime_engine_id"] == "hermes"
    assert result["execution"]["research_backend_id"] == "med_deepscientist"
    assert result["execution"]["research_engine_id"] == "med-deepscientist"
    assert result["decision"] == "resume"
    assert result["reason"] == "quest_initialized_waiting_to_start"


def test_study_runtime_status_uses_native_runtime_event_ref_for_managed_runtime(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
    native_event = _write_native_runtime_event_for_status_test(
        quest_root=quest_root,
        quest_id="001-risk",
        quest_status="stopped",
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
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {"quest_id": quest_id, "active_run_id": "run-native"},
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": "run-native",
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "runtime_event_ref": {
                "event_id": str(native_event["event_id"]),
                "artifact_path": str(native_event["artifact_path"]),
                "summary_ref": str(native_event["summary_ref"]),
            },
            "runtime_event": native_event,
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert result["runtime_event_ref"] == {
        "event_id": str(native_event["event_id"]),
        "artifact_path": str(native_event["artifact_path"]),
        "summary_ref": str(native_event["summary_ref"]),
    }
    assert result["runtime_event"] == native_event


def test_ensure_study_runtime_uses_native_runtime_event_ref_after_managed_transition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    native_event = _write_native_runtime_event_for_status_test(
        quest_root=quest_root,
        quest_id="001-risk",
        quest_status="running",
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
        lambda *, runtime_root, quest_id, source: {
            "ok": True,
            "status": "running",
            "snapshot": {
                "quest_id": quest_id,
                "status": "running",
                "active_run_id": "run-resumed",
            },
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {"quest_id": quest_id, "active_run_id": "run-native"},
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-native",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "runtime_event_ref": {
                "event_id": str(native_event["event_id"]),
                "artifact_path": str(native_event["artifact_path"]),
                "summary_ref": str(native_event["summary_ref"]),
            },
            "runtime_event": native_event,
        },
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["runtime_event_ref"] == {
        "event_id": str(native_event["event_id"]),
        "artifact_path": str(native_event["artifact_path"]),
        "summary_ref": str(native_event["summary_ref"]),
    }
    assert result["runtime_event"] == native_event


def test_study_runtime_status_emits_family_orchestration_companion_fields(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running","active_run_id":"run-native"}\n')
    native_event = _write_native_runtime_event_for_status_test(
        quest_root=quest_root,
        quest_id="001-risk",
        quest_status="running",
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
            "active_run_id": "run-native",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "active_run_id": "run-native",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "active_run_id": "run-native",
                "worker_running": True,
            },
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {"quest_id": quest_id, "active_run_id": "run-native"},
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-native",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "runtime_event_ref": {
                "event_id": str(native_event["event_id"]),
                "artifact_path": str(native_event["artifact_path"]),
                "summary_ref": str(native_event["summary_ref"]),
            },
            "runtime_event": native_event,
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    envelope = result["family_event_envelope"]
    checkpoint = result["family_checkpoint_lineage"]
    assert envelope["version"] == "family-event-envelope.v1"
    assert envelope["target_domain_id"] == "medautoscience"
    assert envelope["session"]["study_id"] == "001-risk"
    assert envelope["session"]["quest_id"] == "001-risk"
    assert envelope["session"]["active_run_id"] == "run-native"
    assert envelope["payload"]["runtime_decision"] == result["decision"]
    assert checkpoint["version"] == "family-checkpoint-lineage.v1"
    assert checkpoint["session"]["active_run_id"] == "run-native"
    assert checkpoint["producer"]["event_envelope_id"] == envelope["envelope_id"]
    assert checkpoint["resume_contract"]["resume_mode"] == "resume_from_checkpoint"
    assert result["family_human_gates"] == []


def test_study_runtime_status_prefers_executor_kind_for_family_source_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
    _write_execution_overrides(
        study_root,
        executor="codex_cli_autonomous",
        executor_kind="hermes_native_proof",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running","active_run_id":"run-native"}\n')
    native_event = _write_native_runtime_event_for_status_test(
        quest_root=quest_root,
        quest_id="001-risk",
        quest_status="running",
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
            "active_run_id": "run-native",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "active_run_id": "run-native",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "active_run_id": "run-native",
                "worker_running": True,
            },
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {"quest_id": quest_id, "active_run_id": "run-native"},
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-native",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "runtime_event_ref": {
                "event_id": str(native_event["event_id"]),
                "artifact_path": str(native_event["artifact_path"]),
                "summary_ref": str(native_event["summary_ref"]),
            },
            "runtime_event": native_event,
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    envelope = result["family_event_envelope"]
    assert envelope["session"]["source_surface"] == "hermes_native_proof"


@pytest.mark.parametrize(
    ("launch_report_overrides", "expected_mismatch_reason", "existing_supervision_health_status"),
    [
        ({"active_run_id": "run-launch"}, "launch_report_active_run_id_mismatch", "live"),
        (
            {"runtime_liveness_audit": {"status": "none", "active_run_id": "run-live"}},
            "launch_report_runtime_liveness_status_mismatch",
            "live",
        ),
        (
            {"supervisor_tick_audit": {"status": "stale"}},
            "launch_report_supervisor_tick_status_mismatch",
            "degraded",
        ),
        (
            {
                "publication_supervisor_state": {
                    "supervisor_phase": "bundle_stage_ready",
                    "phase_owner": "publication_gate",
                    "upstream_scientific_anchor_ready": True,
                    "bundle_tasks_downstream_only": False,
                    "current_required_action": "continue_bundle_stage",
                    "deferred_downstream_actions": [],
                    "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
                }
            },
            "launch_report_publication_supervisor_state_mismatch",
            "live",
        ),
    ],
)
def test_study_runtime_status_runtime_summary_alignment_detects_runtime_surface_mismatch(
    monkeypatch,
    tmp_path: Path,
    launch_report_overrides: dict[str, object],
    expected_mismatch_reason: str,
    existing_supervision_health_status: str,
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running","active_run_id":"run-live"}\n')
    write_text(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "recorded_at": "2026-04-10T09:25:00+00:00",
                "health_status": existing_supervision_health_status,
            },
            ensure_ascii=False,
        )
        + "\n",
    )
    launch_report_payload = {
        "decision": "noop",
        "reason": "quest_already_running",
        "quest_status": "running",
        "active_run_id": "run-live",
        "runtime_liveness_audit": {"status": "live", "active_run_id": "run-live"},
        "supervisor_tick_audit": {"status": "fresh"},
        "publication_supervisor_state": {
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": (
                "paper bundle exists, but the active blockers still belong to the publishability surface; "
                "bundle suggestions stay downstream-only until the gate clears"
            ),
        },
        "recorded_at": "2026-04-10T09:20:00+00:00",
    }
    launch_report_payload.update(launch_report_overrides)
    write_text(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        json.dumps(launch_report_payload, ensure_ascii=False, indent=2) + "\n",
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
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "live",
                "session_count": 1,
                "live_session_count": 1,
                "live_session_ids": ["sess-1"],
            },
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resolve_daemon_url",
        lambda *, runtime_root: "http://127.0.0.1:21999",
    )
    monkeypatch.setattr(
        decision_module,
        "_supervisor_tick_now",
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
            "controller_stage_note": (
                "paper bundle exists, but the active blockers still belong to the publishability surface; "
                "bundle suggestions stay downstream-only until the gate clears"
            ),
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["runtime_summary_alignment"]["aligned"] is False
    assert result["runtime_summary_alignment"]["mismatch_reason"] == expected_mismatch_reason
    assert result["runtime_summary_alignment"]["source_active_run_id"] == "run-live"
    assert result["runtime_summary_alignment"]["source_runtime_liveness_status"] == "live"
    assert result["runtime_summary_alignment"]["source_supervisor_tick_status"] == "fresh"
    refreshed_launch_report = json.loads(
        (study_root / "artifacts" / "runtime" / "last_launch_report.json").read_text(encoding="utf-8")
    )
    assert refreshed_launch_report["active_run_id"] == "run-live"
    assert refreshed_launch_report["runtime_liveness_audit"]["status"] == "live"
    assert refreshed_launch_report["supervisor_tick_audit"]["status"] == "fresh"
    assert refreshed_launch_report["supervisor_tick_audit"]["last_known_health_status"] == "live"
    assert result["supervisor_tick_audit"]["last_known_health_status"] == "live"
    assert refreshed_launch_report["publication_supervisor_state"]["supervisor_phase"] == "publishability_gate_blocked"
    assert refreshed_launch_report["publication_supervisor_state"]["bundle_tasks_downstream_only"] is True
    refreshed_runtime_supervision = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json").read_text(encoding="utf-8")
    )
    assert refreshed_runtime_supervision["health_status"] == "live"
    assert refreshed_runtime_supervision["active_run_id"] == "run-live"
    assert refreshed_runtime_supervision["runtime_liveness_status"] == "live"
    assert refreshed_runtime_supervision["runtime_decision"] == "noop"
