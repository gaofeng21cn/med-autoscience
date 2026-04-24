def test_ensure_study_runtime_keeps_explicit_rerun_for_reopened_task_intake_after_manual_takeover_stop(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
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
    write_auditable_current_package(study_root)
    current_package_root = study_root / "manuscript" / "current_package"
    (current_package_root / "submission_checklist.json").unlink()
    write_text(current_package_root / "submission_manifest.json", '{"schema_version":1}\n')
    quest_root = profile.runtime_root / "001-risk"
    _materialize_bundle_only_remaining_evaluation_summary(study_root=study_root, quest_root=quest_root)
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "按最新专家意见重新打开同一论文线的修订任务；当前稿件不能按已达投稿包里程碑直接收口，"
            "并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        constraints=("本轮不得直接按外投收口。",),
        first_cycle_outputs=("补充分层统计分析并写回 manuscript。",),
    )
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "stop_reason": "controller_stop:codex-human-takeover",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
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
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda **kwargs: pytest.fail("resume_quest should not run after an explicit manual takeover stop"),
    )

    result = module.ensure_study_runtime(
        profile=profile,
        study_id="001-risk",
        source="medautosci-test",
    )

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert result["quest_status"] == "stopped"


def test_study_runtime_status_keeps_explicit_rerun_for_manual_takeover_stop_with_invalid_blocking_progress(
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
    interaction_id = "progress-invalid-001"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "active_interaction_id": interaction_id,
                "stop_reason": "controller_stop:codex-human-takeover",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-continue-001",
            }
        )
        + "\n",
    )
    progress_path = quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / f"{interaction_id}.json"
    write_text(
        progress_path,
        json.dumps(
            {
                "kind": "progress",
                "schema_version": 1,
                "artifact_id": interaction_id,
                "id": interaction_id,
                "quest_id": "001-risk",
                "created_at": "2026-04-09T01:24:52+00:00",
                "updated_at": "2026-04-09T01:24:52+00:00",
                "status": "active",
                "message": "[等待决策] 这一步已经处理完，等待 Gateway 接管并转发给用户。",
                "summary": "等待 Gateway 侧转发新的用户指令。",
                "interaction_phase": "ack",
                "importance": "info",
                "interaction_id": interaction_id,
                "expects_reply": False,
                "reply_mode": "threaded",
                "surface_actions": [],
                "options": [],
                "allow_free_text": True,
                "reply_schema": {"type": "free_text"},
                "guidance_vm": {"requires_user_decision": False},
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
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {
                "status": "stopped",
                "waiting_interaction_id": None,
                "default_reply_interaction_id": interaction_id,
                "pending_decisions": [],
                "active_interaction_id": interaction_id,
            },
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        raising=False,
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert result["quest_status"] == "stopped"
    assert result["interaction_arbitration"]["classification"] == "invalid_blocking"
    assert result["interaction_arbitration"]["action"] == "resume"
    assert result["interaction_arbitration"]["source_artifact_path"] == str(progress_path)


def test_ensure_study_runtime_keeps_explicit_rerun_for_manual_takeover_stop_with_invalid_blocking_progress(
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
    interaction_id = "progress-invalid-001"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "active_interaction_id": interaction_id,
                "stop_reason": "controller_stop:codex-human-takeover",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-continue-001",
            }
        )
        + "\n",
    )
    write_text(
        quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / f"{interaction_id}.json",
        json.dumps(
            {
                "kind": "progress",
                "schema_version": 1,
                "artifact_id": interaction_id,
                "id": interaction_id,
                "quest_id": "001-risk",
                "created_at": "2026-04-09T01:24:52+00:00",
                "updated_at": "2026-04-09T01:24:52+00:00",
                "status": "active",
                "message": "[等待决策] 这一步已经处理完，等待 Gateway 接管并转发给用户。",
                "summary": "等待 Gateway 侧转发新的用户指令。",
                "interaction_phase": "ack",
                "importance": "info",
                "interaction_id": interaction_id,
                "expects_reply": False,
                "reply_mode": "threaded",
                "surface_actions": [],
                "options": [],
                "allow_free_text": True,
                "reply_schema": {"type": "free_text"},
                "guidance_vm": {"requires_user_decision": False},
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
        "get_quest_session",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "quest_id": quest_id,
            "snapshot": {
                "status": "stopped",
                "waiting_interaction_id": None,
                "default_reply_interaction_id": interaction_id,
                "pending_decisions": [],
                "active_interaction_id": interaction_id,
            },
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        raising=False,
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda **kwargs: pytest.fail("resume_quest should not run after a manual takeover stop"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert result["quest_status"] == "stopped"


def test_study_runtime_status_auto_resumes_controller_owned_stopped_completion_request_when_publication_gate_is_blocked(
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
    interaction_id = "decision-completion-001"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "active_run_id": None,
                "active_interaction_id": interaction_id,
                "stop_reason": "controller_stop:ds-launcher",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-continue-001",
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
                "status": "stopped",
                "active_interaction_id": interaction_id,
            },
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        raising=False,
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_completion_requested_before_publication_gate_clear"
    assert result["quest_status"] == "stopped"
    assert result["pending_user_interaction"]["interaction_id"] == interaction_id
    assert result["interaction_arbitration"] == {
        "classification": "premature_completion_request",
        "action": "resume",
        "reason_code": "completion_requested_before_publication_gate_clear",
        "requires_user_input": False,
        "valid_blocking": False,
        "kind": "decision",
        "decision_type": "quest_completion_approval",
        "source_artifact_path": str(decision_path),
        "publication_gate_status": "blocked",
        "publication_gate_blockers": ["forbidden_manuscript_terminology"],
        "publication_gate_required_action": "return_to_publishability_gate",
        "controller_stage_note": (
            "Runtime completion approval was requested before the MAS publication gate cleared; "
            "resume the managed runtime so it fixes publication blockers instead of asking the user."
        ),
    }


def test_ensure_study_runtime_auto_resumes_controller_owned_stopped_completion_request_when_publication_gate_is_blocked(
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
                "status": "stopped",
                "active_run_id": None,
                "active_interaction_id": interaction_id,
                "stop_reason": "controller_stop:ds-launcher",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-continue-001",
            }
        )
        + "\n",
    )
    write_text(
        quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "decisions" / f"{interaction_id}.json",
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
                "status": "stopped",
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

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_completion_requested_before_publication_gate_clear"
    assert result["quest_status"] == "active"
    assert resumed == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
    binding = yaml.safe_load((study_root / "runtime_binding.yaml").read_text(encoding="utf-8"))
    assert binding["last_action"] == "resume"
    launch_report = json.loads((study_root / "artifacts" / "runtime" / "last_launch_report.json").read_text(encoding="utf-8"))
    assert launch_report["decision"] == "resume"
    assert launch_report["reason"] == "quest_completion_requested_before_publication_gate_clear"
    assert launch_report["daemon_result"]["action"] == "resume"
    runtime_supervision = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json").read_text(encoding="utf-8")
    )
    assert runtime_supervision["runtime_decision"] == "resume"
    assert runtime_supervision["health_status"] == "recovering"


def test_study_runtime_status_auto_resumes_controller_guard_stopped_quest_when_publication_gate_is_blocked(
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stopped_by_controller_guard"
    assert result["quest_status"] == "stopped"


def test_study_runtime_status_auto_resumes_controller_guard_stopped_quest_when_bundle_stage_is_blocked(
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_stopped_by_controller_guard"
    assert result["quest_status"] == "stopped"
