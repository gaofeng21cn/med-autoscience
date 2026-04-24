def test_ensure_study_runtime_archives_invalid_partial_quest_root_before_create(
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
    )
    invalid_quest_root = profile.runtime_root / "001-risk"
    write_text(invalid_quest_root / "paper" / "medical_analysis_contract.json", '{"status":"unsupported"}\n')
    created: dict[str, object] = {}

    monkeypatch.setattr(module, "_timestamp_slug", lambda: "20260402T010203Z")
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

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        created["payload"] = payload
        assert not invalid_quest_root.exists()
        write_text(invalid_quest_root / "quest.yaml", "quest_id: 001-risk\n")
        return {
            "ok": True,
            "snapshot": {
                "quest_id": "001-risk",
                "quest_root": str(invalid_quest_root),
                "status": "created",
            },
        }

    monkeypatch.setattr(_managed_runtime_transport(module), "create_quest", fake_create_quest)
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(run_hydration=lambda **kwargs: make_startup_hydration_report(kwargs["quest_root"])),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(run_validation=lambda **kwargs: make_startup_hydration_validation_report(kwargs["quest_root"])),
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    archived_root = (
        profile.med_deepscientist_runtime_root
        / "recovery"
        / "invalid_partial_quest_roots"
        / "001-risk-20260402T010203Z"
    )
    assert result["partial_quest_recovery"]["status"] == "archived_invalid_partial_quest_root"
    assert result["partial_quest_recovery"]["archived_root"] == str(archived_root)
    assert archived_root.joinpath("paper", "medical_analysis_contract.json").exists()
    assert created["payload"]["quest_id"] == "001-risk"


def test_ensure_study_runtime_refreshes_startup_hydration_for_existing_created_quest_when_resume_is_blocked(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
    )
    _write_requested_baseline_ref(study_root, {"baseline_id": "demo-baseline"})
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(module, "_utc_now", lambda: "2026-04-05T06:00:00+00:00")
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
        lambda *, profile, quest_root: calls.append(("prepare_overlay", quest_root)) or make_runtime_overlay_result(),
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

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
    escalation_payload = json.loads(escalation_path.read_text(encoding="utf-8"))
    launch_report = json.loads(Path(result["launch_report_path"]).read_text(encoding="utf-8"))

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_boundary_not_ready_for_resume"
    assert result["startup_hydration_validation"]["status"] == "clear"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is True
    assert result["runtime_escalation_ref"] == {
        "record_id": escalation_payload["record_id"],
        "artifact_path": str(escalation_path),
        "summary_ref": result["launch_report_path"],
    }
    assert escalation_payload["schema_version"] == 1
    assert escalation_payload["study_id"] == "001-risk"
    assert escalation_payload["quest_id"] == "001-risk"
    assert escalation_payload["emitted_at"] == "2026-04-05T06:00:00+00:00"
    assert escalation_payload["trigger"] == {
        "trigger_id": "startup_boundary_not_ready_for_resume",
        "source": "startup_boundary_gate",
    }
    assert escalation_payload["scope"] == "quest"
    assert escalation_payload["severity"] == "quest"
    assert escalation_payload["reason"] == "startup_boundary_not_ready_for_resume"
    assert escalation_payload["recommended_actions"] == ["refresh_startup_hydration", "controller_review_required"]
    assert escalation_payload["summary_ref"] == result["launch_report_path"]
    assert escalation_payload["artifact_path"] == str(escalation_path)
    assert set(escalation_payload["evidence_refs"]) == {
        str(quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json"),
        str(quest_root / "artifacts" / "reports" / "startup" / "hydration_validation_report.json"),
    }
    assert escalation_payload["runtime_context_refs"] == {"launch_report_path": result["launch_report_path"]}
    assert "runtime_escalation_record" not in result
    assert "runtime_escalation_record" not in launch_report
    assert result["startup_context_sync"]["ok"] is True
    assert result["startup_context_sync"]["quest_id"] == "001-risk"
    assert result["startup_context_sync"]["snapshot"]["requested_baseline_ref"] == {
        "baseline_id": "demo-baseline"
    }
    synced_contract = result["startup_context_sync"]["snapshot"]["startup_contract"]
    assert "runtime_escalation_record" not in synced_contract
    assert "runtime_escalation_ref" not in synced_contract
    assert calls == [
        ("prepare_overlay", quest_root),
        ("sync_startup_context", "001-risk", "full_research", {"baseline_id": "demo-baseline"}),
        ("hydrate", quest_root),
        ("validate", quest_root),
    ]


def test_ensure_study_runtime_blocks_when_existing_created_quest_overlay_refresh_still_fails(
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
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
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
        lambda *, profile, quest_root: calls.append("prepare_overlay")
        or make_runtime_overlay_result(all_roots_ready=False),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "update_quest_startup_context",
        lambda **kwargs: pytest.fail("update_quest_startup_context should not run when overlay refresh stays broken"),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: pytest.fail("hydration should not run when overlay refresh stays broken")
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: pytest.fail("validation should not run when overlay refresh stays broken")
        ),
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "runtime_overlay_not_ready"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is False
    assert calls == ["prepare_overlay"]


def test_ensure_study_runtime_uses_protocol_refresh_gate_for_blocked_existing_quest(
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
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"created"}\n')
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
        module.StudyRuntimeStatus,
        "should_refresh_startup_hydration_while_blocked",
        lambda self: False,
    )
    monkeypatch.setattr(
        module,
        "quest_hydration_controller",
        SimpleNamespace(
            run_hydration=lambda **kwargs: calls.append("hydrate")
            or make_startup_hydration_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "startup_hydration_validation_controller",
        SimpleNamespace(
            run_validation=lambda **kwargs: calls.append("validate")
            or make_startup_hydration_validation_report(kwargs["quest_root"])
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_prepare_runtime_overlay",
        lambda *, profile, quest_root: calls.append("prepare_overlay") or make_runtime_overlay_result(),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "startup_boundary_not_ready_for_resume"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is True
    assert calls == ["prepare_overlay"]


def test_ensure_study_runtime_materializes_overlay_for_non_resumable_existing_quest(
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
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"completed"}\n')
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
        lambda **kwargs: pytest.fail("startup context sync should not run for non-resumable completed quest"),
        raising=False,
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_exists_with_non_resumable_state"
    assert result["runtime_overlay"]["audit"]["all_roots_ready"] is True
    assert calls == ["prepare_overlay"]


def test_ensure_study_runtime_resumes_paused_quest(monkeypatch, tmp_path: Path) -> None:
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
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert calls == [
        ("resume", "001-risk"),
    ]


def test_ensure_study_runtime_resume_rehydrates_when_runtime_reentry_requires_startup_hydration(
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
        runtime_reentry_required_paths=[],
        runtime_reentry_require_startup_hydration=True,
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
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
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "resume"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
        ("resume", "001-risk"),
    ]


def test_study_runtime_status_records_missing_supervisor_tick_audit_for_existing_managed_quest(
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

    assert result["supervisor_tick_audit"]["required"] is True
    assert result["supervisor_tick_audit"]["status"] == "missing"
    assert result["supervisor_tick_audit"]["reason"] == "supervisor_tick_report_missing"
    assert result["supervisor_tick_audit"]["latest_report_path"] == str(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    )
    assert result["supervisor_tick_audit"]["stale_after_seconds"] == 600


def test_study_runtime_status_marks_supervisor_tick_audit_stale_when_latest_report_is_too_old(
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_text(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "recorded_at": "2026-04-10T09:00:00+00:00",
                "health_status": "inactive",
            },
            ensure_ascii=False,
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
        decision_module,
        "_supervisor_tick_now",
        lambda: decision_module.datetime.fromisoformat("2026-04-10T09:30:00+00:00"),
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["supervisor_tick_audit"]["required"] is True
    assert result["supervisor_tick_audit"]["status"] == "stale"
    assert result["supervisor_tick_audit"]["reason"] == "supervisor_tick_report_stale"
    assert result["supervisor_tick_audit"]["latest_recorded_at"] == "2026-04-10T09:00:00+00:00"
    assert result["supervisor_tick_audit"]["seconds_since_latest_recorded_at"] == 1800


def test_study_runtime_status_records_supervisor_tick_transition_from_fresh_to_stale(
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    write_text(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "recorded_at": "2026-04-10T09:25:00+00:00",
                "health_status": "inactive",
            },
            ensure_ascii=False,
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

    now_state = {"value": "2026-04-10T09:30:00+00:00"}
    monkeypatch.setattr(
        decision_module,
        "_supervisor_tick_now",
        lambda: decision_module.datetime.fromisoformat(now_state["value"]),
    )

    fresh_result = module.study_runtime_status(profile=profile, study_id="001-risk")
    now_state["value"] = "2026-04-10T09:50:00+00:00"
    stale_result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert fresh_result["supervisor_tick_audit"]["status"] == "fresh"
    assert stale_result["supervisor_tick_audit"]["status"] == "stale"
    assert "runtime_event_ref" not in fresh_result
    assert "runtime_event_ref" not in stale_result


def test_ensure_study_runtime_blocks_resume_when_runtime_reentry_hydration_validation_fails(
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
        runtime_reentry_required_paths=[],
        runtime_reentry_require_startup_hydration=True,
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
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
            or make_startup_hydration_validation_report(
                kwargs["quest_root"],
                status="blocked",
                blockers=["unsupported_medical_analysis_contract"],
            )
        ),
        raising=False,
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda *, runtime_root, quest_id, source: calls.append(("resume", quest_id)) or {"ok": True, "status": "running"},
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "hydration_validation_failed"
    assert calls == [
        ("hydrate", profile.runtime_root / "001-risk"),
        ("validate", profile.runtime_root / "001-risk"),
    ]


def test_ensure_study_runtime_blocks_when_managed_skill_audit_is_required_but_overlay_is_disabled(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = replace(make_profile(tmp_path), enable_medical_overlay=False)
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
        runtime_reentry_required_paths=[],
        runtime_reentry_require_managed_skill_audit=True,
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')

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

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "managed_skill_audit_not_available"
