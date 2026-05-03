def _runtime_pause_status(module, *, profile, study_root, quest_root):
    return module.StudyRuntimeStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "001-risk", "auto_resume": True},
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": False,
            "workspace_contracts": {"overall_ready": True},
            "startup_data_readiness": {"status": "clear"},
            "startup_boundary_gate": {"allow_compute_stage": True},
            "runtime_reentry_gate": {"allow_runtime_entry": True},
            "study_completion_contract": {"status": "absent", "ready": False},
            "controller_first_policy_summary": "summary",
            "automation_ready_summary": "ready",
            "decision": "pause",
            "reason": "human_takeover_requested",
        }
    )


def _runtime_pause_context(module, *, profile, study_root):
    return module._build_execution_context(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        source="test-human-takeover",
    )


def _raise_control_timeout(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
    raise RuntimeError("Quest control request failed: timed out")


def test_execute_pause_runtime_decision_accepts_effective_pause_after_control_timeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
                "stop_reason": "user_pause",
            }
        )
        + "\n",
    )
    status = _runtime_pause_status(module, profile=profile, study_root=study_root, quest_root=quest_root)
    context = _runtime_pause_context(module, profile=profile, study_root=study_root)
    monkeypatch.setattr(_managed_runtime_transport(module), "pause_quest", _raise_control_timeout)

    outcome = module._execute_pause_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.PAUSE
    assert status.decision is module.StudyRuntimeDecision.PAUSE
    assert status.reason is module.StudyRuntimeReason.HUMAN_TAKEOVER_REQUESTED
    assert status.quest_status is module.StudyRuntimeQuestStatus.PAUSED
    assert status.to_dict()["pause_postcondition"] == {
        "effective": True,
        "source": "runtime_state",
        "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
        "runtime_state_status": "paused",
        "active_run_id": None,
        "worker_running": False,
        "control_transport_error": "Quest control request failed: timed out",
    }
    assert outcome.daemon_step("pause")["pause_postcondition"]["effective"] is True


def test_execute_pause_runtime_decision_blocks_when_timeout_leaves_worker_live(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-001",
                "worker_running": True,
            }
        )
        + "\n",
    )
    status = _runtime_pause_status(module, profile=profile, study_root=study_root, quest_root=quest_root)
    context = _runtime_pause_context(module, profile=profile, study_root=study_root)
    monkeypatch.setattr(_managed_runtime_transport(module), "pause_quest", _raise_control_timeout)

    outcome = module._execute_pause_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.BLOCKED
    assert status.decision is module.StudyRuntimeDecision.BLOCKED
    assert status.reason is module.StudyRuntimeReason.PAUSE_REQUEST_FAILED
    assert status.quest_status is module.StudyRuntimeQuestStatus.RUNNING
    assert status.to_dict()["pause_postcondition"]["effective"] is False
    assert outcome.daemon_step("pause")["status"] == "unavailable"
