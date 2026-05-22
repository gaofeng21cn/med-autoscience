from __future__ import annotations

from tests.test_study_runtime_router_cases.shared import *  # noqa: F403


def test_explicit_stopped_relaunch_reopens_failed_reviewer_revision_invalid_blocking(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Unit-harmonized validation needs uncertainty and calibration repair.",
        paper_urls=["https://example.org/paper-2"],
        journal_shortlist=["Diabetes Research and Clinical Practice"],
        minimum_sci_ready_evidence_package=["external_validation", "calibration"],
    )
    quest_root = profile.runtime_root / study_id
    runtime_health_kernel = importlib.import_module("med_autoscience.controllers.runtime_health_kernel")
    for sequence in range(1, 4):
        runtime_health_kernel.append_runtime_health_event(
            study_root=study_root,
            study_id=study_id,
            quest_id=study_id,
            event_type="recover_attempt",
            payload={
                "attempt_state": "failed",
                "failure_reason": "quest_marked_running_but_no_live_session",
            },
            recorded_at=f"2026-05-21T14:4{sequence}:00+00:00",
        )
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "failed",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "blocked_turn_closeout": {
                    "run_id": "run-blocked",
                    "blocked_reason": "control_plane_route_blocked_bundle_build",
                    "next_owner": "MAS/controller route authorization owner",
                    "closeout_path": str(quest_root / "artifacts" / "runtime" / "turn_closeouts" / "run-blocked.json"),
                },
                "last_controller_decision_authorization": {
                    "source": "owner_route_reconcile_platform_repair",
                    "work_unit_id": "submission_minimal_refresh",
                    "work_unit_fingerprint": "publication-blockers::current",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=["author_metadata", "ethics_statement"],
    )
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": study_id,
                "emitted_at": "2026-05-21T14:50:14+00:00",
                "entry_mode": "full_research",
                "task_intent": "Reviewer revision: add uncertainty intervals and grouped calibration.",
                "constraints": [
                    "Treat this as explicit user wakeup after submission-package parking.",
                    "Do not keep the previous submission-ready state as current truth.",
                ],
                "first_cycle_outputs": ["revised manuscript package"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    _materialize_bundle_only_remaining_evaluation_summary(study_root=study_root, quest_root=quest_root)
    evaluation_summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    evaluation_summary = json.loads(evaluation_summary_path.read_text(encoding="utf-8"))
    study_quality_truth = dict(evaluation_summary.get("study_quality_truth") or {})
    study_quality_truth["reviewer_first"] = {
        **dict(study_quality_truth.get("reviewer_first") or {}),
        "ready": False,
        "status": "blocked",
        "open_concern_count": 1,
    }
    evaluation_summary["study_quality_truth"] = study_quality_truth
    write_text(evaluation_summary_path, json.dumps(evaluation_summary, ensure_ascii=False, indent=2) + "\n")

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
    calls: list[str] = []
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("explicit terminal relaunch must not call resume_quest")
        ),
    )
    monkeypatch.setattr(
        module,
        "_relaunch_stopped_quest",
        lambda *, runtime_root, quest_id, source, runtime_backend: calls.append("relaunch_stopped")
        or {
            "ok": True,
            "status": "running",
            "started": True,
            "scheduled": True,
            "snapshot": {"quest_id": quest_id, "status": "running", "active_run_id": "run-relaunched"},
        },
    )

    status = module.progress_projection(
        profile=profile,
        study_id=study_id,
        include_progress_projection=False,
    )
    result = module.ensure_study_runtime(
        profile=profile,
        study_id=study_id,
        allow_stopped_relaunch=True,
        explicit_user_wakeup=True,
        source="user_explicit_wakeup",
    )

    assert status["decision"] == "resume"
    assert status["reason"] == "quest_waiting_on_invalid_blocking"
    assert status["quest_status"] == "failed"
    assert result["decision"] == "relaunch_stopped"
    assert result["reason"] == "quest_stopped_explicit_relaunch_requested"
    assert result["quest_status"] == "running"
    assert result["runtime_health_snapshot"]["retry_budget_remaining"] == 2
    assert result["control_plane_snapshot"]["route_authorization"]["runtime_recovery_allowed"] is True
    assert "runtime_recovery_retry_budget_exhausted" not in result["runtime_health_snapshot"]["blocking_reasons"]
    assert "runtime_recovery_retry_budget_exhausted" not in result["control_plane_snapshot"]["blocking_reasons"]
    assert calls == ["relaunch_stopped"]
