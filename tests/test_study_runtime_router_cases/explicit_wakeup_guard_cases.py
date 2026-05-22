from .shared import *  # noqa: F403


def _patch_ready_workspace(monkeypatch, module: object, *, study_id: str) -> None:
    monkeypatch.setattr(
        module.analysis_bundle_controller,
        "ensure_study_runtime_analysis_bundle",
        lambda: {"action": "already_ready", "ready": True},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "ensure_medical_overlay",
        lambda **kwargs: {"selected_action": "noop", "post_status": {"all_targets_ready": True}},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "materialize_runtime_medical_overlay",
        lambda **kwargs: {"materialized_surface_count": 1, "surfaces": []},
    )
    monkeypatch.setattr(
        module.overlay_installer,
        "audit_runtime_medical_overlay",
        lambda **kwargs: {"all_roots_ready": True, "surface_count": 1, "surfaces": []},
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, study_id),
    )


def _write_managed_study(profile, study_id: str) -> tuple[Path, Path]:
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / study_id
    write_text(quest_root / "quest.yaml", f"quest_id: {study_id}\n")
    return study_root, quest_root


def test_explicit_user_wakeup_keeps_typed_blocker_when_runtime_state_cannot_record(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "user_pause",
                "continuation_reason": "user_pause",
                "stop_reason": "user_pause",
                "user_pause_contract": {
                    "recorded_at": "2026-05-06T05:08:51+00:00",
                    "resume_requires_explicit_wakeup": True,
                    "source": "test-human-takeover",
                },
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    execution_module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    monkeypatch.setattr(
        execution_module._runtime_events,
        "record_explicit_user_wakeup",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("unrecorded wakeup must not resume")),
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id=study_id,
        explicit_user_wakeup=True,
        source="user_explicit_wakeup",
    )

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_user_paused_requires_explicit_wakeup"
    assert "explicit_user_wakeup" not in result
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert "last_explicit_user_wakeup" not in runtime_state


def test_explicit_user_wakeup_resumes_human_takeover_pause_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "controller_review",
                "continuation_anchor": "human_takeover",
                "continuation_reason": "human_takeover_requested",
                "human_takeover_contract": {
                    "recorded_at": "2026-05-15T16:22:57+00:00",
                    "resume_requires_explicit_wakeup": True,
                    "source": "cli",
                    "recommended_actions": [
                        "manual_runtime_review_required",
                        "controller_review_required",
                    ],
                },
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    calls: list[str] = []
    monkeypatch.setattr(
        module.managed_runtime_transport,
        "update_quest_startup_context",
        lambda *, runtime_root, quest_id, startup_contract, requested_baseline_ref=None: calls.append("sync_context")
        or {"ok": True, "snapshot": {"quest_id": quest_id, "startup_contract": startup_contract}},
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda *, runtime_root, quest_id, source, runtime_backend: calls.append("resume")
        or {"ok": True, "status": "running", "snapshot": {"status": "running", "active_run_id": "run-explicit"}},
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id=study_id,
        explicit_user_wakeup=True,
        source="user_explicit_wakeup",
    )

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_paused"
    assert result["quest_status"] == "running"
    assert result["explicit_user_wakeup"]["status"] == "recorded"
    assert result["explicit_user_wakeup"]["cleared_human_takeover"] is True
    assert calls == ["sync_context", "resume"]
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert "human_takeover_contract" not in runtime_state
    assert runtime_state["last_explicit_user_wakeup"]["source"] == "user_explicit_wakeup"
    assert runtime_state["last_explicit_user_wakeup"]["cleared_human_takeover"] is True


def test_explicit_user_wakeup_records_owner_route_for_stopped_pending_user_message_redrive(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 2,
                "continuation_policy": "auto",
                "continuation_anchor": "user_message_queue",
                "continuation_reason": "runtime_platform_repair_resume_existing_pending_user_message",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("pending user-message redrive belongs to OPL runtime owner")
        ),
    )
    monkeypatch.setattr(
        module,
        "_relaunch_stopped_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("pending user-message redrive must not relaunch provider worker")
        ),
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id=study_id,
        explicit_user_wakeup=True,
        source="user_explicit_wakeup",
    )

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["quest_status"] == "stopped"
    assert result["explicit_user_wakeup"]["status"] == "recorded"
    assert result["explicit_user_wakeup"]["cleared_pending_user_message_redrive"] is True
    assert result["explicit_user_wakeup"]["handoff_kind"] == "opl_runtime_owner_route"
    assert result["interaction_arbitration"]["classification"] == "opl_runtime_owner_route_handoff"
    assert result["opl_runtime_owner_route_handoff"]["queue_owner"] == "one-person-lab"
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert runtime_state["last_explicit_user_wakeup"]["source"] == "user_explicit_wakeup"
    assert runtime_state["last_explicit_user_wakeup"]["cleared_pending_user_message_redrive"] is True
    assert runtime_state["pending_user_message_count"] == 2
    assert runtime_state["continuation_policy"] == "auto"
    assert runtime_state["continuation_anchor"] == "user_message_queue"
    assert runtime_state["continuation_reason"] == "runtime_platform_repair_resume_existing_pending_user_message"
    handoff_record = json.loads(
        (study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert handoff_record["runtime_state_mutated"] is False
    assert handoff_record["handoff"]["recommended_task_kind"] == "domain_route/reconcile-apply"


def test_explicit_user_wakeup_records_owner_route_for_stopped_redrive_with_stale_human_takeover_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    study_root, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 2,
                "continuation_policy": "auto",
                "continuation_anchor": "user_message_queue",
                "continuation_reason": "runtime_platform_repair_resume_existing_pending_user_message",
                "human_takeover_contract": {
                    "recorded_at": "2026-05-17T06:11:10+00:00",
                    "resume_requires_explicit_wakeup": True,
                    "source": "cli",
                },
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("stale human-takeover pending redrive belongs to OPL runtime owner")
        ),
    )
    monkeypatch.setattr(
        module,
        "_relaunch_stopped_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("stale human-takeover pending redrive must not relaunch provider worker")
        ),
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id=study_id,
        explicit_user_wakeup=True,
        source="user_explicit_wakeup",
    )

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["quest_status"] == "stopped"
    assert result["explicit_user_wakeup"]["cleared_pending_user_message_redrive"] is True
    assert result["explicit_user_wakeup"]["handoff_kind"] == "opl_runtime_owner_route"
    assert result["interaction_arbitration"]["classification"] == "opl_runtime_owner_route_handoff"
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert "human_takeover_contract" not in runtime_state
    assert runtime_state["last_explicit_user_wakeup"]["cleared_stale_human_takeover_contract"] is True
    assert runtime_state["continuation_anchor"] == "user_message_queue"
    handoff_record = json.loads(
        (study_root / "artifacts" / "supervision" / "owner_route_handoff" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert handoff_record["runtime_state_mutated"] is False


def test_explicit_user_wakeup_does_not_release_unknown_stopped_runtime(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "001-risk"
    _, quest_root = _write_managed_study(profile, study_id)
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    write_text(
        runtime_state_path,
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 2,
                "continuation_policy": "auto",
                "continuation_anchor": "user_message_queue",
                "continuation_reason": "unknown_legacy_reason",
            }
        )
        + "\n",
    )
    _patch_ready_workspace(monkeypatch, module, study_id=study_id)
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("unknown stopped runtime must stay blocked")),
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id=study_id,
        explicit_user_wakeup=True,
        source="user_explicit_wakeup",
    )

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert "explicit_user_wakeup" not in result
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert "last_explicit_user_wakeup" not in runtime_state
    assert runtime_state["continuation_reason"] == "unknown_legacy_reason"
