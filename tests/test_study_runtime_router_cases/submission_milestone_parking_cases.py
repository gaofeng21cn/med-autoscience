from .shared import *  # noqa: F403
def test_ensure_study_runtime_keeps_refreshed_submission_package_milestone_parked(
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
                "status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_publication_gate_state",
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_text(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "decision_type": "continue_same_line",
                "reason": "Submission-package milestone remains parked; keep the runtime stopped until explicit resume.",
                "route_target": "finalize",
                "controller_actions": [{"action_type": "stop_runtime"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "quality_closure_truth": {
                    "state": "bundle_only_remaining",
                    "current_required_action": "continue_bundle_stage",
                    "route_target": "finalize",
                },
                "quality_review_loop": {"closure_state": "bundle_only_remaining"},
                "quality_assessment": {
                    "human_review_readiness": {"status": "ready"},
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
    study_progress_module = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress_module,
        "build_study_progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "current_stage": "manual_finishing",
            "current_stage_summary": "当前论文线已到投稿包里程碑。",
            "paper_stage": "bundle_stage_ready",
            "paper_stage_summary": "当前论文线已到投稿包里程碑。",
            "next_system_action": "等待显式接力。",
            "needs_physician_decision": False,
        },
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
            "status": "none",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 1,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "resume_quest",
        lambda **kwargs: pytest.fail("refreshed submission-package parking must not auto-resume"),
    )

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_parked_on_unchanged_finalize_state"
    assert result["runtime_liveness_audit"]["status"] == "none"
    assert result["continuation_state"]["continuation_policy"] == "wait_for_user_or_resume"
    assert result["continuation_state"]["continuation_reason"] == "unchanged_publication_gate_state"


def test_study_runtime_status_keeps_live_labeled_delivered_package_without_worker_parked(
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
    write_synced_submission_delivery(study_root, quest_root, include_submission_checklist=False)
    current_package_root = study_root / "manuscript" / "current_package"
    (current_package_root / "figures").mkdir(parents=True, exist_ok=True)
    (current_package_root / "figures" / "Figure1.png").write_text("figure", encoding="utf-8")
    (current_package_root / "tables").mkdir(parents=True, exist_ok=True)
    (current_package_root / "tables" / "Table1.md").write_text("table", encoding="utf-8")
    write_text(
        current_package_root / "audit" / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "figures": [{"figure_id": "Figure1"}],
                "tables": [{"table_id": "Table1"}],
                "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
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
                "status": "active",
                "active_run_id": None,
                "worker_running": False,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "runtime_platform_repair_redrive",
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
            "status": "blocked",
            "allow_write": False,
            "blockers": ["stale_submission_minimal_authority"],
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "complete_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage blockers remain on the finalize path",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 1,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["quest_status"] == "active"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["auto_runtime_parked"]["parked"] is True
    assert result["auto_runtime_parked"]["parked_state"] == "external_metadata_pending"
    assert result["progress_projection"]["current_stage"] == "auto_runtime_parked"
    assert result["progress_projection"]["supervision"]["active_run_id"] is None
    assert result["progress_projection"]["supervision"]["health_status"] == "parked"
    assert result["runtime_health_snapshot"]["attempt_state"] == "awaiting_explicit_resume"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_recovery_retry_budget_exhausted" not in result["runtime_health_snapshot"]["blocking_reasons"]
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] != "recover_runtime"


def test_study_runtime_status_keeps_paused_delivered_package_without_worker_parked(
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
    write_synced_submission_delivery(study_root, quest_root, include_submission_checklist=False)
    current_package_root = study_root / "manuscript" / "current_package"
    (current_package_root / "figures").mkdir(parents=True, exist_ok=True)
    (current_package_root / "figures" / "Figure1.png").write_text("figure", encoding="utf-8")
    (current_package_root / "tables").mkdir(parents=True, exist_ok=True)
    (current_package_root / "tables" / "Table1.md").write_text("table", encoding="utf-8")
    write_text(
        current_package_root / "audit" / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "figures": [{"figure_id": "Figure1"}],
                "tables": [{"table_id": "Table1"}],
                "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
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
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
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
            "status": "blocked",
            "allow_write": False,
            "blockers": ["stale_submission_minimal_authority"],
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "complete_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage blockers remain on the finalize path",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 1,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="001-risk")

    assert result["quest_status"] == "paused"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["auto_runtime_parked"]["parked"] is True
    assert result["progress_projection"]["current_stage"] == "auto_runtime_parked"
    assert result["runtime_health_snapshot"]["attempt_state"] == "awaiting_explicit_resume"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_recovery_retry_budget_exhausted" not in result["runtime_health_snapshot"]["blocking_reasons"]
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] != "external_supervisor_required"


def test_mechanical_projection_current_package_does_not_park_abnormal_active_runtime(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Cross-population mortality attribution framing remains under reviewer revision.",
        paper_urls=["https://example.org/paper-2"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "calibration"],
    )
    quest_root = profile.runtime_root / "002-risk"
    write_synced_submission_delivery(study_root, quest_root)
    write_text(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "002-risk",
                "quest_id": "002-risk",
                "emitted_at": "2026-05-05T09:25:21+00:00",
                "assessment_provenance": {
                    "owner": "mechanical_projection",
                    "ai_reviewer_required": True,
                },
                "verdict": {
                    "overall_verdict": "blocked",
                    "primary_claim_status": "partial",
                },
                "gaps": [
                    {"gap_type": "delivery", "severity": "must_fix"},
                    {"gap_type": "claim", "severity": "must_fix"},
                ],
                "recommended_actions": [
                    {
                        "action_id": "action-ai-reviewer",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "priority": "now",
                    }
                ],
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
                "status": "active",
                "active_run_id": None,
                "worker_running": False,
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "002-risk"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "allow_write": False,
            "blockers": ["publication_eval_ai_reviewer_required"],
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "return_to_ai_reviewer_workflow",
            "deferred_downstream_actions": [],
            "controller_stage_note": "AI reviewer must assess the current package before delivery parking.",
        },
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 1,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="002-risk")

    assert result["quest_status"] == "active"
    assert result["decision"] == "resume"
    assert result["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert "quest_marked_running_but_no_live_session" in result["runtime_health_snapshot"]["blocking_reasons"]
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] in {
        "recover_runtime",
        "external_supervisor_required",
    }


def test_study_runtime_status_pauses_live_delivered_package_after_clear_bundle_gate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Cross-population mortality attribution framing has a current milestone package.",
        paper_urls=["https://example.org/paper-2"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "calibration"],
    )
    quest_root = profile.runtime_root / "002-risk"
    write_synced_submission_delivery(study_root, quest_root, include_submission_checklist=False)
    current_package_root = study_root / "manuscript" / "current_package"
    (current_package_root / "figures").mkdir(parents=True, exist_ok=True)
    (current_package_root / "figures" / "Figure1.png").write_text("figure", encoding="utf-8")
    (current_package_root / "tables").mkdir(parents=True, exist_ok=True)
    (current_package_root / "tables" / "Table1.md").write_text("table", encoding="utf-8")
    write_text(
        current_package_root / "audit" / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "figures": [{"figure_id": "Figure1"}],
                "tables": [{"table_id": "Table1"}],
                "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
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
                "status": "active",
                "active_run_id": "run-live-delivered",
                "worker_running": True,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_text(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "002-risk",
                "quest_id": "002-risk",
                "status": "clear",
                "allow_write": True,
                "blockers": [],
                "current_required_action": "continue_bundle_stage",
                "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "002-risk"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "clear",
            "allow_write": True,
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
            "source": "mas_runtime_core_turn_lifecycle",
            "active_run_id": "run-live-delivered",
            "runner_live": True,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "mas_runtime_core_turn_lifecycle",
                "active_run_id": "run-live-delivered",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 1,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )

    result = module.study_runtime_status(profile=profile, study_id="002-risk")

    assert result["quest_status"] == "active"
    assert result["decision"] == "pause"
    assert result["reason"] == "quest_waiting_for_submission_metadata"
    assert result["auto_runtime_parked"]["parked"] is True
    assert result["auto_runtime_parked"]["parked_state"] == "external_metadata_pending"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "await_explicit_resume"
