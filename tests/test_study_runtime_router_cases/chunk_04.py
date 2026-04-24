def test_ensure_study_runtime_auto_resumes_controller_guard_stopped_quest_when_publication_gate_is_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "active_interaction_id": "progress-controller-guard-001",
                "stop_reason": "controller_stop:medautosci-figure-loop-guard",
                "continuation_policy": "auto",
                "continuation_anchor": "analysis-campaign",
                "continuation_reason": "decision:decision-continue-001",
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
            "blockers": ["medical_publication_surface_blocked"],
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "paper bundle exists, but blockers still belong to the publishability surface",
        },
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

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stopped_by_controller_guard"
    assert result["quest_status"] == "active"
    assert resumed == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
    binding = yaml.safe_load((study_root / "runtime_binding.yaml").read_text(encoding="utf-8"))
    assert binding["last_action"] == "resume"


def test_ensure_study_runtime_auto_resumes_controller_guard_stopped_quest_when_bundle_stage_is_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "active_interaction_id": "progress-controller-guard-001",
                "stop_reason": "controller_stop:medautosci-figure-loop-guard",
                "continuation_policy": "auto",
                "continuation_anchor": "write",
                "continuation_reason": "decision:decision-continue-001",
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
            "blockers": ["submission_minimal_incomplete"],
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "complete_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
        },
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

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stopped_by_controller_guard"
    assert result["quest_status"] == "active"
    assert resumed == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
    binding = yaml.safe_load((study_root / "runtime_binding.yaml").read_text(encoding="utf-8"))
    assert binding["last_action"] == "resume"


def test_study_runtime_status_auto_resumes_controller_guard_stopped_quest_when_write_stage_is_ready(
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
                "status": "stopped",
                "active_run_id": None,
                "active_interaction_id": "progress-controller-guard-001",
                "stop_reason": "controller_stop:medautosci-figure-loop-guard",
                "continuation_policy": "auto",
                "continuation_anchor": "write",
                "continuation_reason": "decision:decision-continue-001",
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stale_decision_after_write_stage_ready"
    assert result["quest_status"] == "stopped"
    assert result["publication_supervisor_state"]["current_required_action"] == "continue_write_stage"


def test_ensure_study_runtime_auto_resumes_controller_guard_stopped_quest_when_write_stage_is_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "active_interaction_id": "progress-controller-guard-001",
                "stop_reason": "controller_stop:medautosci-figure-loop-guard",
                "continuation_policy": "auto",
                "continuation_anchor": "write",
                "continuation_reason": "decision:decision-continue-001",
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
    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stale_decision_after_write_stage_ready"
    assert result["quest_status"] == "active"
    assert resumed == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
    assert len(queue["pending"]) == 1
    assert "publication gate 已放行写作" in queue["pending"][0]["content"]
    binding = yaml.safe_load((study_root / "runtime_binding.yaml").read_text(encoding="utf-8"))
    assert binding["last_action"] == "resume"


def test_execute_runtime_decision_returns_terminal_outcome_for_completed_status(tmp_path: Path) -> None:
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
    status.set_decision("completed", "quest_already_completed")
    context = module._build_execution_context(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        source="test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.COMPLETED
    assert outcome.daemon_result is None
    assert outcome.startup_payload_path is None


def test_execute_resume_runtime_decision_records_nested_resume_daemon_step(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
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
            "quest_status": "paused",
            "runtime_binding_path": str(profile.workspace_root / "studies" / "001-risk" / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "resume",
            "reason": "quest_paused",
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
        module,
        "_sync_existing_quest_startup_context",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "quest_id": kwargs["quest_id"],
                "startup_contract": kwargs["create_payload"]["startup_contract"],
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_run_startup_hydration",
        lambda **kwargs: (
            module.study_runtime_protocol.StartupHydrationReport.from_payload(
                make_startup_hydration_report(kwargs["quest_root"])
            ),
            module.study_runtime_protocol.StartupHydrationValidationReport.from_payload(
                make_startup_hydration_validation_report(kwargs["quest_root"])
            ),
        ),
    )
    monkeypatch.setattr(
        transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    outcome = module._execute_resume_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.RESUME
    assert outcome.daemon_result == {"resume": {"ok": True, "status": "running"}}
    assert outcome.daemon_step("resume") == {"ok": True, "status": "running"}
    assert status.quest_status is module.StudyRuntimeQuestStatus.RUNNING


@pytest.mark.parametrize(
    ("resume_reason",),
    [
        ("quest_marked_running_but_no_live_session",),
        ("quest_parked_on_unchanged_finalize_state",),
    ],
)
def test_execute_resume_runtime_decision_skips_startup_hydration_for_managed_runtime_recovery(
    monkeypatch,
    tmp_path: Path,
    resume_reason: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    transport = _managed_runtime_transport(module)
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
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
            "quest_status": "active",
            "runtime_binding_path": str(profile.workspace_root / "studies" / "001-risk" / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "resume",
                "reason": resume_reason,
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
        module,
        "_sync_existing_quest_startup_context",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "quest_id": kwargs["quest_id"],
                "startup_contract": kwargs["create_payload"]["startup_contract"],
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_run_startup_hydration",
        lambda **kwargs: pytest.fail("startup hydration should not run for managed runtime recovery"),
    )
    monkeypatch.setattr(
        transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {"ok": True, "status": "running"},
    )

    outcome = module._execute_resume_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.RESUME
    assert outcome.daemon_result == {"resume": {"ok": True, "status": "running"}}
    assert outcome.daemon_step("resume") == {"ok": True, "status": "running"}
    assert status.quest_status is module.StudyRuntimeQuestStatus.RUNNING


def test_execute_resume_runtime_decision_blocks_when_resume_request_has_no_effect(
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
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
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
            "quest_status": "waiting_for_user",
            "runtime_binding_path": str(profile.workspace_root / "studies" / "001-risk" / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "resume",
            "reason": "quest_waiting_on_invalid_blocking",
            "interaction_arbitration": {
                "classification": "invalid_blocking",
                "action": "resume",
                "requires_user_input": False,
            },
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
        module,
        "_sync_existing_quest_startup_context",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "quest_id": kwargs["quest_id"],
                "startup_contract": kwargs["create_payload"]["startup_contract"],
            },
        },
    )
    monkeypatch.setattr(
        transport,
        "resume_quest",
        lambda *, runtime_root, quest_id, source: {
            "ok": True,
            "quest_id": quest_id,
            "scheduled": False,
            "started": False,
            "queued": False,
            "snapshot": {
                "status": "waiting_for_user",
                "active_run_id": None,
            },
        },
    )

    outcome = module._execute_resume_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.BLOCKED
    assert status.decision is module.StudyRuntimeDecision.BLOCKED
    assert status.reason is module.StudyRuntimeReason.RESUME_REQUEST_FAILED
    assert status.quest_status is module.StudyRuntimeQuestStatus.WAITING_FOR_USER
    assert status.to_dict()["resume_postcondition"] == {
        "effective": False,
        "failure_mode": "waiting_state_preserved",
        "snapshot_status": "waiting_for_user",
        "active_run_id": None,
        "scheduled": False,
        "started": False,
        "queued": False,
    }


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

def test_ensure_study_runtime_persists_legacy_resume_daemon_result_shape(
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
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

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert len(seen["persist_calls"]) == 1
    assert seen["persist_calls"][0]["last_action"] == "resume"
    assert seen["persist_calls"][0]["daemon_result"] == {"ok": True, "status": "active"}


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
