def test_study_runtime_status_pauses_live_reviewer_intake_after_proven_bundle_closeout(
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
        task_intent="根据审稿意见执行 manuscript revision，并清理 Methods/Figure/Table feedback。",
        constraints=("不得按旧 submission-ready/finalize 判断直接收口。",),
        first_cycle_outputs=("revision checklist mapping each reviewer concern to manuscript deltas",),
    )
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    _materialize_bundle_only_remaining_evaluation_summary(study_root=study_root, quest_root=quest_root)
    evaluation_summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    evaluation_summary = json.loads(evaluation_summary_path.read_text(encoding="utf-8"))
    evaluation_summary["emitted_at"] = "2099-01-01T00:00:00+00:00"
    evaluation_summary["promotion_gate_status"] = {
        **dict(evaluation_summary.get("promotion_gate_status") or {}),
        "status": "clear",
        "allow_write": True,
        "current_required_action": "continue_bundle_stage",
        "blockers": [],
    }
    evaluation_summary["quality_closure_truth"] = {
        **dict(evaluation_summary.get("quality_closure_truth") or {}),
        "state": "bundle_only_remaining",
        "current_required_action": "continue_bundle_stage",
    }
    quality_review_loop = dict(evaluation_summary.get("quality_review_loop") or {})
    quality_review_loop["closure_state"] = "bundle_only_remaining"
    evaluation_summary["quality_review_loop"] = quality_review_loop
    quality_assessment = dict(evaluation_summary.get("quality_assessment") or {})
    quality_assessment["human_review_readiness"] = {
        **dict(quality_assessment.get("human_review_readiness") or {}),
        "status": "ready",
    }
    evaluation_summary["quality_assessment"] = quality_assessment
    study_quality_truth = dict(evaluation_summary.get("study_quality_truth") or {})
    study_quality_truth["reviewer_first"] = {
        **dict(study_quality_truth.get("reviewer_first") or {}),
        "ready": True,
        "status": "ready",
    }
    evaluation_summary["study_quality_truth"] = study_quality_truth
    write_text(evaluation_summary_path, json.dumps(evaluation_summary, ensure_ascii=False, indent=2) + "\n")
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

    assert result["decision"] == "pause", result
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["publication_supervisor_state"]["current_required_action"] == "continue_bundle_stage"
