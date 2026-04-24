def test_study_runtime_status_refreshes_runtime_supervision_when_launch_report_is_already_aligned(
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running","active_run_id":"run-live"}\n')
    write_text(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "recorded_at": "2026-04-10T09:25:00+00:00",
                "health_status": "degraded",
                "runtime_decision": "blocked",
                "runtime_reason": "running_quest_live_session_audit_failed",
                "quest_status": "running",
                "runtime_liveness_status": "unknown",
                "worker_running": True,
                "active_run_id": "run-old",
            },
            ensure_ascii=False,
        )
        + "\n",
    )
    write_text(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        json.dumps(
            {
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

    assert result["runtime_summary_alignment"]["aligned"] is True
    refreshed_runtime_supervision = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json").read_text(encoding="utf-8")
    )
    assert refreshed_runtime_supervision["health_status"] == "live"
    assert refreshed_runtime_supervision["active_run_id"] == "run-live"
    assert refreshed_runtime_supervision["runtime_liveness_status"] == "live"
    assert refreshed_runtime_supervision["runtime_decision"] == "noop"


def test_ensure_study_runtime_uses_custom_quest_id_for_existing_runtime(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="001-risk-reentry",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    _write_requested_baseline_ref(study_root, {"baseline_id": "demo-baseline"})
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk-reentry"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk-reentry\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"idle"}\n')
    calls: list[tuple[str, object]] = []

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
            run_hydration=lambda **kwargs: calls.append(("hydrate", kwargs["quest_root"]))
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append(("validate", kwargs["quest_root"]))
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append(
            ("sync_startup_context", quest_id, startup_contract.get("scope"), requested_baseline_ref)
        )
        or {
            "ok": True,
            "snapshot": {
                "quest_id": quest_id,
                "startup_contract": startup_contract,
                "requested_baseline_ref": requested_baseline_ref,
            },
        },
        raising=False,
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "active"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert result["quest_id"] == "001-risk-reentry"
    assert result["quest_root"] == str(profile.runtime_root / "001-risk-reentry")
    assert result["quest_status"] == "active"
    assert result["startup_context_sync"]["ok"] is True
    assert result["startup_context_sync"]["quest_id"] == "001-risk-reentry"
    assert result["startup_context_sync"]["snapshot"]["requested_baseline_ref"] == {
        "baseline_id": "demo-baseline"
    }
    assert calls == [
        ("sync_startup_context", "001-risk-reentry", "full_research", {"baseline_id": "demo-baseline"}),
        ("resume", "001-risk-reentry"),
    ]


def test_ensure_study_runtime_blocks_when_analysis_bundle_is_not_ready(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
        minimum_sci_ready_evidence_package=["external_validation"],
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
        module.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "ensure_bundle", "ready": False},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "study_runtime_analysis_bundle_not_ready"
    assert result["analysis_bundle"]["ready"] is False


def test_ensure_study_runtime_pauses_running_quest_when_runtime_overlay_audit_fails(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    paused: dict[str, object] = {}

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
            "active_run_id": "run-001",
            "runner_live": True,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "quest_session_runtime_audit",
                "active_run_id": "run-001",
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
        module.overlay_installer,
        "audit_runtime_medical_overlay",
        lambda **kwargs: {
            "all_roots_ready": False,
            "surface_count": 2,
            "surfaces": [{"surface": "quest"}, {"surface": "worktree"}],
        },
    )

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        paused["runtime_root"] = runtime_root
        paused["quest_id"] = quest_id
        paused["source"] = source
        return {"ok": True, "status": "paused"}

    monkeypatch.setattr(_managed_runtime_transport(module), "pause_quest", fake_pause_quest)

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "pause"
    assert result["reason"] == "runtime_overlay_audit_failed_for_running_quest"
    assert result["quest_status"] == "paused"
    assert paused == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }


def test_ensure_study_runtime_repairs_live_runtime_overlay_before_pausing(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    calls: list[tuple[str, Path]] = []

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
            "active_run_id": "run-001",
            "runner_live": True,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "quest_session_runtime_audit",
                "active_run_id": "run-001",
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
        module,
        "_audit_runtime_overlay",
        lambda *, profile, quest_root: {
            "all_roots_ready": False,
            "surface_count": 2,
            "surfaces": [{"surface": "quest"}, {"surface": "worktree"}],
        },
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append(("prepare_overlay", quest_root))
        or make_runtime_overlay_result(all_roots_ready=True),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "pause_quest",
        lambda **kwargs: pytest.fail("pause_quest should not run after overlay refresh succeeds"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "noop"
    assert result["reason"] == "quest_already_running"
    assert result["quest_status"] == "running"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is True
    assert calls == [("prepare_overlay", quest_root)]


def test_build_startup_contract_separates_runtime_owned_subset_from_controller_extensions(tmp_path: Path) -> None:
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    ownership = importlib.import_module("med_autoscience.startup_contract")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
        scientific_followup_questions=[
            "Why is the 5-year all-cause mortality gap between China and the US so large?",
        ],
        explanation_targets=[
            "Decompose the observed mortality gap into endpoint alignment, follow-up/censoring, case-mix shift, score compression, and residual unexplained components.",
        ],
        manuscript_conclusion_redlines=[
            "Do not conclude only that the China-trained absolute-risk model is non-transportable.",
        ],
    )
    study_payload = yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8"))
    execution = router._execution_payload(study_payload)

    startup_contract = router._build_startup_contract(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )

    runtime_owned = ownership.runtime_owned_startup_contract(startup_contract)
    controller_extensions = ownership.controller_owned_startup_contract_extensions(startup_contract)

    assert runtime_owned == {
        "schema_version": 4,
        "user_language": "zh",
        "need_research_paper": True,
        "decision_policy": "autonomous",
        "launch_mode": "custom",
        "custom_profile": startup_contract["custom_profile"],
        "baseline_execution_policy": startup_contract["baseline_execution_policy"],
    }
    assert controller_extensions["scope"] == startup_contract["scope"]
    assert controller_extensions["entry_state_summary"] == startup_contract["entry_state_summary"]
    assert controller_extensions["startup_boundary_gate"] == startup_contract["startup_boundary_gate"]
    assert controller_extensions["runtime_reentry_gate"] == startup_contract["runtime_reentry_gate"]
    assert controller_extensions["medical_analysis_contract_summary"] == startup_contract["medical_analysis_contract_summary"]
    assert controller_extensions["medical_reporting_contract_summary"] == startup_contract["medical_reporting_contract_summary"]
    assert controller_extensions["submission_targets"] == startup_contract["submission_targets"]
    assert controller_extensions["study_charter_ref"] == startup_contract["study_charter_ref"]
    assert controller_extensions["controller_summary_ref"] == startup_contract["controller_summary_ref"]
    charter_ref = startup_contract["study_charter_ref"]
    assert charter_ref["charter_id"] == "charter::001-risk::v1"
    assert charter_ref["artifact_path"] == str((study_root / "artifacts" / "controller" / "study_charter.json").resolve())
    charter_payload = json.loads(Path(charter_ref["artifact_path"]).read_text(encoding="utf-8"))
    assert charter_payload["charter_id"] == charter_ref["charter_id"]
    assert charter_payload["publication_objective"] == "Build a submission-ready survival-risk study."
    assert charter_payload["scientific_followup_questions"] == [
        "Why is the 5-year all-cause mortality gap between China and the US so large?",
    ]
    assert charter_payload["explanation_targets"] == [
        "Decompose the observed mortality gap into endpoint alignment, follow-up/censoring, case-mix shift, score compression, and residual unexplained components.",
    ]
    assert charter_payload["manuscript_conclusion_redlines"] == [
        "Do not conclude only that the China-trained absolute-risk model is non-transportable.",
    ]
    controller_summary_ref = startup_contract["controller_summary_ref"]
    assert controller_summary_ref["summary_id"] == "controller-summary::001-risk::v1"
    assert controller_summary_ref["artifact_path"] == str(
        (study_root / "artifacts" / "controller" / "controller_summary.json").resolve()
    )
    controller_summary_payload = json.loads(Path(controller_summary_ref["artifact_path"]).read_text(encoding="utf-8"))
    assert controller_summary_payload["summary_id"] == controller_summary_ref["summary_id"]
    assert controller_summary_payload["study_charter_ref"] == charter_ref
    assert controller_summary_payload["controller_policy"]["startup_boundary_gate"] == startup_contract["startup_boundary_gate"]
    assert controller_summary_payload["controller_policy"]["runtime_reentry_gate"] == startup_contract["runtime_reentry_gate"]
    assert controller_summary_payload["controller_policy"]["journal_shortlist"] == startup_contract["journal_shortlist"]
    assert controller_summary_payload["controller_policy"]["medical_analysis_contract_summary"] == startup_contract["medical_analysis_contract_summary"]
    assert controller_summary_payload["controller_policy"]["medical_reporting_contract_summary"] == startup_contract["medical_reporting_contract_summary"]
    assert controller_summary_payload["controller_policy"]["submission_targets"] == startup_contract["submission_targets"]
    assert controller_summary_payload["route_trigger_authority"] == {
        "decision_policy": "autonomous",
        "launch_profile": "continue_existing_state",
        "startup_contract_profile": "paper_required_autonomous",
    }
    assert "custom_brief" in controller_extensions
    assert "Why is the 5-year all-cause mortality gap between China and the US so large?" in controller_extensions["custom_brief"]
    assert "Decompose the observed mortality gap into endpoint alignment, follow-up/censoring, case-mix shift, score compression, and residual unexplained components." in controller_extensions["custom_brief"]
    assert "Do not conclude only that the China-trained absolute-risk model is non-transportable." in controller_extensions["custom_brief"]


def test_compose_startup_contract_rejects_runtime_owned_and_extension_overlap() -> None:
    ownership = importlib.import_module("med_autoscience.startup_contract")

    with pytest.raises(ValueError, match="startup contract ownership overlap"):
        ownership.compose_startup_contract(
            runtime_owned={"launch_mode": "custom"},
            controller_extensions={"launch_mode": "should-not-overlap"},
        )


def test_ensure_study_runtime_keeps_live_audit_blocked_even_if_overlay_audit_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')

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
            "ok": False,
            "status": "unknown",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": False,
                "status": "unknown",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": None,
                "worker_pending": None,
                "stop_requested": None,
                "error": "daemon unavailable",
            },
            "bash_session_audit": {
                "ok": False,
                "status": "unknown",
                "session_count": None,
                "live_session_count": None,
                "live_session_ids": [],
                "error": "daemon unavailable",
            },
            "error": "daemon unavailable | daemon unavailable",
        },
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "audit_runtime_medical_overlay",
        lambda **kwargs: {
            "all_roots_ready": False,
            "surface_count": 2,
            "surfaces": [{"surface": "quest"}, {"surface": "worktree"}],
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "pause_quest",
        lambda **kwargs: pytest.fail("pause_quest should not run when live-session audit is unknown"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "running_quest_live_session_audit_failed"
    assert result["runtime_liveness_audit"]["status"] == "unknown"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is False


def test_study_runtime_status_reports_waiting_for_user_quest_as_blocked(monkeypatch, tmp_path: Path) -> None:
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"waiting_for_user"}\n')
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
    assert result["reason"] == "quest_waiting_for_user"
    assert result["quest_status"] == "waiting_for_user"


def test_study_runtime_status_embeds_progress_projection_by_default(monkeypatch, tmp_path: Path) -> None:
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running"}\n')
    write_text(
        quest_root / ".ds" / "bash_exec" / "summary.json",
        json.dumps(
            {
                "session_count": 1,
                "running_count": 1,
                "latest_session": {
                    "bash_id": "bash-001",
                    "status": "running",
                    "updated_at": "2026-04-11T01:02:00+00:00",
                    "last_progress": {
                        "ts": "2026-04-11T01:02:00+00:00",
                        "message": "完成外部验证数据清点，正在整理论文证据面。",
                    },
                },
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["progress_projection"]["study_id"] == "001-risk"
    assert result["progress_projection"]["current_stage_summary"]
    assert any(
        "完成外部验证数据清点" in str(item.get("summary") or "")
        for item in result["progress_projection"]["latest_events"]
    )
    assert result["progress_projection"]["next_system_action"]


def test_study_runtime_status_materializes_stable_publication_eval_latest(
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_text(
        study_root / "artifacts" / "controller" / "study_charter.json",
        json.dumps(
            {
                "schema_version": 1,
                "charter_id": "charter::001-risk::v1",
                "study_id": "001-risk",
                "publication_objective": "risk stratification external validation",
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
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-03T04:00:00+00:00",
            "anchor_kind": "missing",
            "anchor_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
            "quest_id": "001-risk",
            "run_id": "run-1",
            "main_result_path": str(quest_root / "artifacts" / "results" / "main_result.json"),
            "paper_root": str(study_root / "paper"),
            "compile_report_path": None,
            "latest_gate_path": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
            "medical_publication_surface_report_path": None,
            "medical_publication_surface_current": False,
            "allow_write": False,
            "recommended_action": "return_to_publishability_gate",
            "status": "blocked",
            "blockers": ["missing_post_main_publishability_gate"],
            "write_drift_detected": False,
            "required_non_scalar_deliverables": [],
            "present_non_scalar_deliverables": [],
            "missing_non_scalar_deliverables": [],
            "paper_bundle_manifest_path": None,
            "submission_minimal_manifest_path": None,
            "submission_minimal_present": False,
            "submission_minimal_docx_present": False,
            "submission_minimal_pdf_present": False,
            "medical_publication_surface_status": None,
            "submission_surface_qc_failures": [],
            "archived_submission_surface_roots": [],
            "unmanaged_submission_surface_roots": [],
            "manuscript_terminology_violations": [],
            "headline_metrics": {},
            "primary_metric_delta_vs_baseline": None,
            "results_summary": "summary",
            "conclusion": "conclusion",
            "controller_note": "note",
            "supervisor_phase": "scientific_anchor_missing",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": False,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    latest_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    assert latest_eval_path.is_file()
    payload = json.loads(latest_eval_path.read_text(encoding="utf-8"))

    assert result["publication_supervisor_state"]["supervisor_phase"] == "scientific_anchor_missing"
    assert payload["eval_id"] == "publication-eval::001-risk::001-risk::2026-04-03T04:00:00+00:00"
    assert payload["study_id"] == "001-risk"
    assert payload["quest_id"] == "001-risk"
    assert payload["charter_context_ref"] == {
        "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "charter_id": "charter::001-risk::v1",
        "publication_objective": "risk stratification external validation",
    }
    assert payload["verdict"]["overall_verdict"] == "blocked"
    assert payload["verdict"]["primary_claim_status"] == "blocked"
    assert payload["recommended_actions"][0]["action_type"] == "return_to_controller"
    assert payload["recommended_actions"][0]["requires_controller_decision"] is True
