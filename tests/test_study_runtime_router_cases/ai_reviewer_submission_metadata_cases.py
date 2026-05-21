from .shared import *  # noqa: F403


def _write_ai_reviewer_prose_quality_route(
    *,
    study_root: Path,
    quest_root: Path,
) -> None:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    eval_id = f"publication-eval::{study_root.name}::{quest_root.name}::2026-05-15T16:15:21+00:00"
    write_text(
        publication_eval_path,
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": eval_id,
                "study_id": study_root.name,
                "quest_id": quest_root.name,
                "emitted_at": "2026-05-15T16:15:21+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(study_root / "paper"),
                    "submission_minimal_ref": str(
                        study_root / "paper" / "submission_minimal" / "submission_manifest.json"
                    ),
                },
                "verdict": {"overall_verdict": "promising", "primary_claim_status": "supported"},
                "quality_assessment": {
                    "clinical_significance": {"status": "ready"},
                    "evidence_strength": {"status": "ready"},
                    "novelty_positioning": {"status": "ready"},
                    "human_review_readiness": {"status": "ready"},
                    "medical_journal_prose_quality": {
                        "status": "underdefined",
                        "summary": "AI reviewer must close medical-journal prose quality before finalize.",
                    },
                },
                "recommended_actions": [
                    {
                        "action_type": "continue_same_line",
                        "route_target": "review",
                        "work_unit_fingerprint": (
                            "domain-transition::ai_reviewer_re_eval::"
                            "ai_reviewer_medical_prose_quality_review"
                        ),
                        "next_work_unit": {
                            "unit_id": "ai_reviewer_medical_prose_quality_review",
                            "lane": "review",
                            "summary": (
                                "Re-run AI reviewer manuscript-quality review and close "
                                "medical_journal_prose_quality before finalize."
                            ),
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        controller_decision_path,
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": f"study-decision::{study_root.name}::ai-reviewer-prose-quality",
                "study_id": study_root.name,
                "quest_id": quest_root.name,
                "emitted_at": "2026-05-15T16:33:20+00:00",
                "decision_type": "continue_same_line",
                "charter_ref": {
                    "charter_id": f"charter::{study_root.name}::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": f"runtime-escalation::{study_root.name}::{quest_root.name}::ai-reviewer",
                    "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "latest.json"),
                    "summary_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "latest.json"),
                },
                "publication_eval_ref": {
                    "eval_id": eval_id,
                    "artifact_path": str(publication_eval_path),
                },
                "requires_human_confirmation": False,
                "controller_actions": [
                    {
                        "action_type": "return_to_ai_reviewer_workflow",
                        "payload_ref": str(controller_decision_path),
                    }
                ],
                "reason": "AI reviewer must close subjective medical prose quality before finalize.",
                "route_target": "review",
                "route_key_question": "当前稿件是否已经通过 AI reviewer-owned publication evaluation？",
                "route_rationale": "Medical prose quality is a reviewer-owned judgment, not submission metadata.",
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
                ),
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                    "summary": (
                        "Re-run AI reviewer manuscript-quality review and close "
                        "medical_journal_prose_quality before finalize."
                    ),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )


def _write_current_ai_reviewer_write_routeback(
    *,
    study_root: Path,
    quest_root: Path,
) -> None:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    manuscript_path = study_root / "paper" / "draft.md"
    write_text(manuscript_path, "# Draft\n\nCurrent manuscript needs clean external validation story repair.\n")
    write_text(
        publication_eval_path,
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": f"publication-eval::{study_root.name}::{quest_root.name}::current-write-routeback",
                "study_id": study_root.name,
                "quest_id": quest_root.name,
                "emitted_at": "2026-05-19T21:46:11+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                },
                "verdict": {"overall_verdict": "blocked", "primary_claim_status": "partial"},
                "quality_assessment": {
                    "clinical_significance": {"status": "ready"},
                    "evidence_strength": {"status": "partial"},
                    "novelty_positioning": {"status": "partial"},
                    "human_review_readiness": {"status": "blocked"},
                    "medical_journal_prose_quality": {
                        "status": "blocked",
                        "summary": "Story-facing sections must be rewritten before publication gate.",
                    },
                },
                "reviewer_operating_system": {
                    "currentness_checks": {
                        "medical_prose_review": {
                            "status": "current",
                            "request_digest": "sha256:request-current",
                            "manuscript_ref": str(manuscript_path),
                            "manuscript_digest": "sha256:manuscript-current",
                            "route_back_required": True,
                            "route_target": "write",
                        }
                    }
                },
                "recommended_actions": [
                    {
                        "action_id": "ai-reviewer-action::return-to-write-clean-story",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "requires_controller_decision": True,
                        "route_target": "write",
                        "work_unit_fingerprint": "ai_reviewer_story_clean_external_validation_v3",
                        "next_work_unit": {
                            "unit_id": "manuscript_story_repair",
                            "lane": "write",
                            "summary": "Rewrite as a clean external-validation manuscript.",
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        controller_decision_path,
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": f"study-decision::{study_root.name}::current-write-routeback",
                "study_id": study_root.name,
                "quest_id": quest_root.name,
                "emitted_at": "2026-05-19T21:46:12+00:00",
                "decision_type": "route_back_same_line",
                "route_target": "analysis-campaign",
                "route_key_question": "manuscript_story_repair",
                "reason": "Run one controller-owned quality repair batch before returning to publishability gate.",
                "requires_human_confirmation": False,
                "controller_actions": [
                    {
                        "action_type": "run_quality_repair_batch",
                        "payload_ref": str(controller_decision_path),
                    }
                ],
                "next_work_unit": {
                    "unit_id": "manuscript_story_repair",
                    "lane": "write",
                    "summary": "Repair the paper story around the current evidence and claim boundary.",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )


def test_paused_submission_metadata_package_routes_to_ai_reviewer_quality_owner(
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
        paper_framing_summary="Clinical survival framing is fixed around mortality transportability.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
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
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=["author_metadata", "ethics_statement", "ai_declaration"],
    )
    write_synced_submission_delivery(study_root, quest_root)
    _write_ai_reviewer_prose_quality_route(study_root=study_root, quest_root=quest_root)
    gate_report = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-15T16:15:21+00:00",
        "quest_id": "001-risk",
        "paper_root": str(study_root / "paper"),
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "supervisor_phase": "bundle_stage_ready",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": False,
        "current_required_action": "continue_bundle_stage",
        "deferred_downstream_actions": [],
        "controller_stage_note": "bundle-stage work is unlocked but AI prose review remains owner-routed",
    }
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
        decision_module.publication_gate_controller,
        "build_gate_state",
        lambda quest_root: object(),
    )
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: gate_report,
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(
        profile=profile,
        study_id="001-risk",
        include_progress_projection=False,
    )

    assert result["decision"] == "resume"
    assert result["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert result["domain_transition"]["decision_type"] == "ai_reviewer_re_eval"
    assert result["domain_transition"]["controller_action"] == "return_to_ai_reviewer_workflow"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"


def test_waiting_submission_metadata_package_routes_current_ai_reviewer_write_routeback(
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
        paper_framing_summary="Clinical survival framing is fixed around external validation.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "waiting_for_user",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 1,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "last_controller_decision_authorization": {
                    "decision_id": "study-decision::001-risk::stale-ai-reviewer-recheck",
                    "route_target": "review",
                    "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                    "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_submission_metadata_only_bundle(quest_root, blocking_item_ids=["author_metadata", "ethics_statement"])
    write_synced_submission_delivery(study_root, quest_root)
    _write_current_ai_reviewer_write_routeback(study_root=study_root, quest_root=quest_root)
    gate_report = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-19T21:46:12+00:00",
        "quest_id": "001-risk",
        "paper_root": str(study_root / "paper"),
        "status": "blocked",
        "allow_write": False,
        "blockers": ["medical_journal_prose_quality_blocked"],
        "supervisor_phase": "publishability_gate_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": True,
        "current_required_action": "return_to_publishability_gate",
        "deferred_downstream_actions": [],
        "controller_stage_note": "route back to write to close reviewer-first manuscript concerns",
    }
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        module,
        "_resume_quest",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("write route-back handoff must not call resume_quest")
        ),
    )

    status = module.study_runtime_status(
        profile=profile,
        study_id="001-risk",
        include_progress_projection=False,
    )
    result = module.ensure_study_runtime(
        profile=profile,
        study_id="001-risk",
        explicit_user_wakeup=True,
        source="user_explicit_wakeup",
    )

    assert status["decision"] == "blocked"
    assert status["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert status["domain_transition"]["decision_type"] == "route_back_same_line"
    assert status["domain_transition"]["owner"] == "write"
    assert status["domain_transition"]["next_work_unit"]["unit_id"] == "manuscript_story_repair"
    assert status["interaction_arbitration"]["classification"] == "domain_transition_runtime_redrive"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["quest_status"] == "waiting_for_user"
    assert result["opl_runtime_owner_route_handoff"]["queue_owner"] == "one-person-lab"


def test_user_paused_submission_metadata_package_routes_current_ai_reviewer_transition(
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
        paper_framing_summary="Clinical survival framing is fixed around mortality transportability.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "paused",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "finalize",
                "continuation_reason": "decision:stale-submission-metadata",
                "stop_reason": "user_pause",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=["author_metadata", "ethics_statement", "ai_declaration"],
    )
    write_synced_submission_delivery(study_root, quest_root)
    _write_ai_reviewer_prose_quality_route(study_root=study_root, quest_root=quest_root)
    gate_report = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-15T16:15:21+00:00",
        "quest_id": "001-risk",
        "paper_root": str(study_root / "paper"),
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "supervisor_phase": "bundle_stage_ready",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": False,
        "current_required_action": "continue_bundle_stage",
        "deferred_downstream_actions": [],
        "controller_stage_note": "bundle-stage work is unlocked but AI prose review remains owner-routed",
    }
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
        decision_module.publication_gate_controller,
        "build_gate_state",
        lambda quest_root: object(),
    )
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: gate_report,
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )

    result = module.study_runtime_status(
        profile=profile,
        study_id="001-risk",
        include_progress_projection=False,
    )

    assert result["decision"] == "resume"
    assert result["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert result["interaction_arbitration"]["classification"] == "domain_transition_runtime_redrive"
    assert result["domain_transition"]["controller_action"] == "return_to_ai_reviewer_workflow"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"


def test_live_submission_metadata_package_keeps_ai_reviewer_quality_owner(
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
        paper_framing_summary="Clinical survival framing is fixed around mortality transportability.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-ai-reviewer-live",
                "worker_running": True,
                "pending_user_message_count": 0,
            }
        )
        + "\n",
    )
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=["author_metadata", "ethics_statement", "ai_declaration"],
    )
    write_synced_submission_delivery(study_root, quest_root)
    _write_ai_reviewer_prose_quality_route(study_root=study_root, quest_root=quest_root)
    gate_report = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-15T16:15:21+00:00",
        "quest_id": "001-risk",
        "paper_root": str(study_root / "paper"),
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "supervisor_phase": "bundle_stage_ready",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": False,
        "current_required_action": "continue_bundle_stage",
        "deferred_downstream_actions": [],
        "controller_stage_note": "bundle-stage work is unlocked but AI prose review remains owner-routed",
    }
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
        decision_module.publication_gate_controller,
        "build_gate_state",
        lambda quest_root: object(),
    )
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: gate_report,
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
            "source": "mas_runtime_core_turn_lifecycle",
            "active_run_id": "run-ai-reviewer-live",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "mas_runtime_core_turn_lifecycle",
                "active_run_id": "run-ai-reviewer-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {"ok": True, "status": "none"},
        },
    )

    result = module.study_runtime_status(
        profile=profile,
        study_id="001-risk",
        include_progress_projection=False,
    )

    assert result["quest_status"] == "running"
    assert result["active_run_id"] == "run-ai-reviewer-live"
    assert result["decision"] == "resume"
    assert result["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert result["domain_transition"]["owner"] == "ai_reviewer"


def test_live_submission_metadata_package_keeps_current_ai_reviewer_write_routeback(
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
        paper_framing_summary="Clinical survival framing is fixed around external validation.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-write-routeback-live",
                "worker_running": True,
                "pending_user_message_count": 0,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=["author_metadata", "ethics_statement", "ai_declaration"],
    )
    write_synced_submission_delivery(study_root, quest_root)
    _write_current_ai_reviewer_write_routeback(study_root=study_root, quest_root=quest_root)
    gate_report = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-19T21:46:12+00:00",
        "quest_id": "001-risk",
        "paper_root": str(study_root / "paper"),
        "status": "blocked",
        "allow_write": False,
        "blockers": ["medical_journal_prose_quality_blocked"],
        "supervisor_phase": "publishability_gate_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": True,
        "current_required_action": "return_to_publishability_gate",
        "deferred_downstream_actions": [],
        "controller_stage_note": "route back to write to close reviewer-first manuscript concerns",
    }
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_report", lambda state: gate_report)
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
            "source": "mas_runtime_core_turn_lifecycle",
            "active_run_id": "run-write-routeback-live",
            "runner_live": True,
            "bash_live": True,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "mas_runtime_core_turn_lifecycle",
                "active_run_id": "run-write-routeback-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {"ok": True, "status": "none"},
        },
    )

    result = module.study_runtime_status(
        profile=profile,
        study_id="001-risk",
        include_progress_projection=False,
    )

    assert result["quest_status"] == "running"
    assert result["active_run_id"] == "run-write-routeback-live"
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["domain_transition"]["decision_type"] == "route_back_same_line"
    assert result["domain_transition"]["owner"] == "write"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "manuscript_story_repair"
    assert result["interaction_arbitration"]["classification"] == "domain_transition_runtime_redrive"


def test_active_submission_metadata_package_redrives_current_ai_reviewer_write_routeback_without_live_worker(
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
        paper_framing_summary="Clinical survival framing is fixed around external validation.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "active",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=["author_metadata", "ethics_statement", "ai_declaration"],
    )
    write_synced_submission_delivery(study_root, quest_root)
    _write_current_ai_reviewer_write_routeback(study_root=study_root, quest_root=quest_root)
    gate_report = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-19T21:46:12+00:00",
        "quest_id": "001-risk",
        "paper_root": str(study_root / "paper"),
        "status": "blocked",
        "allow_write": False,
        "blockers": ["medical_journal_prose_quality_blocked"],
        "supervisor_phase": "publishability_gate_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": True,
        "current_required_action": "return_to_publishability_gate",
        "deferred_downstream_actions": [],
        "controller_stage_note": "route back to write to close reviewer-first manuscript concerns",
    }
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
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_report", lambda state: gate_report)
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
            "status": "none",
            "source": "mas_runtime_core_turn_lifecycle",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "mas_runtime_core_turn_lifecycle",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {"ok": True, "status": "none"},
        },
    )

    result = module.study_runtime_status(
        profile=profile,
        study_id="001-risk",
        include_progress_projection=False,
    )

    assert result["quest_status"] == "active"
    assert result.get("active_run_id") is None
    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["domain_transition"]["decision_type"] == "route_back_same_line"
    assert result["domain_transition"]["owner"] == "write"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "manuscript_story_repair"
    assert result["interaction_arbitration"]["classification"] == "domain_transition_runtime_redrive"
