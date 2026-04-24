def test_study_runtime_status_keeps_explicit_manual_finish_contract_parked_even_when_stopped_auto_continuation_has_pending_messages(
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
    _write_manual_finish_contract(
        study_root,
        {
            "status": "active",
            "summary": "当前 study 已转入人工打磨收尾；MAS 只需保持兼容性与监督入口。",
            "next_action_summary": "继续保持兼容性与监督入口；如需重新自动续跑，再显式 rerun 或 relaunch。",
            "compatibility_guard_only": True,
        },
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "continuation_policy": "auto",
                "continuation_anchor": "write",
                "continuation_reason": "decision:decision-continue-001",
                "stop_reason": "user_stop",
                "active_interaction_id": "progress-001",
                "pending_user_message_count": 9,
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "stopped"


def test_study_runtime_status_parks_bundle_only_handoff_before_invalid_blocking_resume(
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
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    write_text(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "quality_closure_truth": {"state": "bundle_only_remaining"},
                "quality_review_loop": {"closure_state": "bundle_only_remaining"},
                "quality_assessment": {"human_review_readiness": {"status": "ready"}},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "stopped",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:decision-handoff-001",
                "active_interaction_id": "progress-invalid-001",
            },
            ensure_ascii=False,
        )
        + "\n",
    )
    write_text(
        quest_root / ".ds" / "worktrees" / "paper-main" / "artifacts" / "progress" / "progress-invalid-001.json",
        json.dumps(
            {
                "kind": "progress",
                "schema_version": 1,
                "artifact_id": "progress-invalid-001",
                "id": "progress-invalid-001",
                "quest_id": "001-risk",
                "status": "active",
                "message": "Human-review package has been handed off.",
                "summary": "Waiting for the outer controller.",
                "expects_reply": True,
                "reply_mode": "blocking",
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
    study_progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress_module,
        "build_study_progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "current_stage": "manual_finishing",
            "current_stage_summary": "Human-review package is ready.",
            "paper_stage": "manual_finishing",
            "paper_stage_summary": "Human-review package is ready.",
            "next_system_action": "Wait for explicit user resume.",
            "needs_physician_decision": False,
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "stopped"
    assert result["interaction_arbitration"]["classification"] == "invalid_blocking"


def test_study_runtime_status_refreshes_stale_launch_report_for_stopped_quest(
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
    quest_root = profile.runtime_root / "001-risk"
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
    write_text(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        json.dumps(
            {
                "decision": "resume",
                "reason": "quest_paused",
                "quest_status": "active",
                "recorded_at": "2026-04-08T09:42:28Z",
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

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert result["quest_status"] == "stopped"
    assert result["runtime_summary_alignment"] == {
        "source_of_truth": "study_runtime_status",
        "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
        "runtime_state_status": "stopped",
        "source_active_run_id": None,
        "source_runtime_liveness_status": None,
        "source_supervisor_tick_status": "missing",
        "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        "launch_report_exists": True,
        "launch_report_quest_status": "active",
        "launch_report_active_run_id": None,
        "launch_report_runtime_liveness_status": None,
        "launch_report_supervisor_tick_status": None,
        "aligned": False,
        "mismatch_reason": "launch_report_quest_status_mismatch",
        "status_sync_applied": True,
    }
    refreshed_launch_report = json.loads(
        (study_root / "artifacts" / "runtime" / "last_launch_report.json").read_text(encoding="utf-8")
    )
    assert refreshed_launch_report["decision"] == "blocked"
    assert refreshed_launch_report["reason"] == "quest_stopped_requires_explicit_rerun"
    assert refreshed_launch_report["quest_status"] == "stopped"


def test_ensure_study_runtime_explicitly_relaunches_stopped_quest(monkeypatch, tmp_path: Path) -> None:
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
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
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

    result = module.ensure_study_runtime(
        profile=profile,
        study_id="001-risk",
        allow_stopped_relaunch=True,
        source="medautosci-test",
    )

    assert result["decision"] == "relaunch_stopped"
    assert result["reason"] == "quest_stopped_explicit_relaunch_requested"
    assert result["quest_status"] == "active"
    assert resumed == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
    binding = yaml.safe_load((study_root / "runtime_binding.yaml").read_text(encoding="utf-8"))
    assert binding["last_action"] == "relaunch_stopped"
    launch_report = json.loads((study_root / "artifacts" / "runtime" / "last_launch_report.json").read_text(encoding="utf-8"))
    assert launch_report["decision"] == "relaunch_stopped"
    assert launch_report["reason"] == "quest_stopped_explicit_relaunch_requested"
    assert launch_report["daemon_result"]["resume"]["action"] == "resume"


def test_study_runtime_status_reopened_task_intake_does_not_keep_bundle_only_handoff_parked(
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
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
    assert result["reason"] == "quest_waiting_on_invalid_blocking"
    assert result["quest_status"] == "stopped"
    assert result["progress_projection"]["quality_closure_truth"]["state"] == "quality_repair_required"
    assert result["progress_projection"]["quality_closure_truth"]["current_required_action"] == "return_to_analysis_campaign"
    assert result["progress_projection"]["quality_execution_lane"]["lane_id"] == "general_quality_repair"


def test_ensure_study_runtime_auto_resumes_stopped_quest_after_reopened_task_intake(
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
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
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

    result = module.ensure_study_runtime(
        profile=profile,
        study_id="001-risk",
        source="medautosci-test",
    )

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_on_invalid_blocking"
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
    assert launch_report["reason"] == "quest_waiting_on_invalid_blocking"
    assert launch_report["daemon_result"]["action"] == "resume"


def test_study_runtime_status_parks_reopened_task_intake_after_fresh_bundle_only_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    quest_root = profile.runtime_root / "001-risk"
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
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    write_text(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "summary_id": "evaluation-summary::001-risk::quest-001::2099-01-01T00:00:00+00:00",
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "emitted_at": "2099-01-01T00:00:00+00:00",
                "quality_closure_truth": {
                    "state": "bundle_only_remaining",
                    "current_required_action": "continue_bundle_stage",
                },
                "quality_review_loop": {
                    "closure_state": "bundle_only_remaining",
                },
                "quality_assessment": {
                    "human_review_readiness": {
                        "status": "ready",
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
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
            "generated_at": "2099-01-01T00:00:00+00:00",
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
    study_progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress_module,
        "build_study_progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "current_stage": "manual_finishing",
            "current_stage_summary": "当前论文线已到投稿包里程碑。",
            "paper_stage": "manual_finishing",
            "paper_stage_summary": "当前论文线已到投稿包里程碑。",
            "next_system_action": "等待显式接力。",
            "needs_physician_decision": False,
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "stopped"


def test_ensure_study_runtime_parks_reopened_task_intake_after_fresh_bundle_only_closeout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
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
    quest_root = profile.runtime_root / "001-risk"
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
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    write_text(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "summary_id": "evaluation-summary::001-risk::quest-001::2099-01-01T00:00:00+00:00",
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "emitted_at": "2099-01-01T00:00:00+00:00",
                "quality_closure_truth": {
                    "state": "bundle_only_remaining",
                    "current_required_action": "continue_bundle_stage",
                },
                "quality_review_loop": {
                    "closure_state": "bundle_only_remaining",
                },
                "quality_assessment": {
                    "human_review_readiness": {
                        "status": "ready",
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"stopped"}\n')
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
            "generated_at": "2099-01-01T00:00:00+00:00",
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
    study_progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress_module,
        "build_study_progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "current_stage": "manual_finishing",
            "current_stage_summary": "当前论文线已到投稿包里程碑。",
            "paper_stage": "manual_finishing",
            "paper_stage_summary": "当前论文线已到投稿包里程碑。",
            "next_system_action": "等待显式接力。",
            "needs_physician_decision": False,
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda **kwargs: pytest.fail("resume_quest should not run after bundle-only closeout has already been re-established"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["quest_status"] == "stopped"


def test_study_runtime_status_keeps_explicit_rerun_for_reopened_task_intake_after_manual_takeover_stop(
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

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert result["quest_status"] == "stopped"
