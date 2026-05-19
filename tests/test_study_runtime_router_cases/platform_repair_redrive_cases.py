from .shared import *  # noqa: F403


def _set_mtime(path: Path, timestamp: int) -> None:
    import os

    os.utime(path, (timestamp, timestamp))


def test_study_runtime_status_resumes_platform_repair_current_controller_redrive_despite_existing_adoption(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="prediction_model",
        paper_framing_summary="Prediction framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.runtime_root / "003-dpcc"
    write_text(quest_root / "quest.yaml", "quest_id: 003-dpcc\n")
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
                "last_controller_decision_authorization": {
                    "source": "runtime_supervisor_scan_platform_repair",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    runtime_escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
    write_text(
        controller_decision_path,
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "decision-analysis-003",
                "study_id": "003-dpcc",
                "quest_id": "003-dpcc",
                "emitted_at": "2026-05-09T12:09:27+00:00",
                "decision_type": "bounded_analysis",
                "charter_ref": {
                    "charter_id": "charter::003-dpcc::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::003-dpcc::controller-redrive",
                    "artifact_path": str(runtime_escalation_path),
                    "summary_ref": str(runtime_escalation_path),
                },
                "publication_eval_ref": {
                    "eval_id": "publication-eval::003-dpcc::latest",
                    "artifact_path": str(publication_eval_path),
                },
                "requires_human_confirmation": False,
                "controller_actions": [
                    {
                        "action_type": "run_quality_repair_batch",
                        "payload_ref": str(controller_decision_path),
                    }
                ],
                "reason": "Route stalled quality repair into the current managed runtime.",
                "route_target": "analysis-campaign",
                "route_key_question": "Repair claim-evidence blockers.",
                "route_rationale": "Current publication gate requires controller-owned quality repair.",
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence blockers.",
                },
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        publication_eval_path,
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::003-dpcc::latest",
                "emitted_at": "2026-05-09T12:10:00+00:00",
                "recommended_actions": [
                    {
                        "action_type": "bounded_analysis",
                        "route_target": "analysis-campaign",
                        "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                        "next_work_unit": {
                            "unit_id": "analysis_claim_evidence_repair",
                            "lane": "analysis-campaign",
                            "summary": "Repair claim-evidence blockers.",
                        },
                        "specificity_targets": [
                            {
                                "target_kind": "claim",
                                "target_id": "claim_evidence_map",
                                "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                            }
                        ],
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="artifact_written",
        payload={
            "active_run_id": "run-003-old",
            "report_ref": str(quest_root / "artifacts" / "supervision" / "controller_consumption" / "latest.json"),
            "created_at": "2026-05-09T11:58:53Z",
            "work_unit_id": "analysis_claim_evidence_repair",
            "route_target": "analysis-campaign",
            "recommended_next_route": "handoff_to_next_owner",
            "source": "medautosci-test",
            "analysis_lane_status": "exhausted_for_current_fingerprint",
            "next_owner": "write/ai_reviewer",
            "next_work_unit": "manuscript_story_repair",
            "result": {"meaningful_artifact_delta": True},
        },
        recorded_at="2026-05-09T12:10:00+00:00",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "003-dpcc"),
    )
    monkeypatch.setattr(
        module,
        "_inspect_quest_live_execution",
        lambda **kwargs: {
            "ok": True,
            "status": "none",
            "active_run_id": None,
            "worker_running": False,
            "snapshot": {"status": "active", "active_run_id": None, "worker_running": False},
            "runtime_audit": {"status": "none", "active_run_id": None, "worker_running": False},
            "bash_session_audit": {"ok": True, "status": "none"},
        },
    )

    result = module._status_payload(
        profile=profile,
        study_id="003-dpcc",
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        entry_mode=None,
    )

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_marked_running_but_no_live_session"
    assert result["continuation_state"]["continuation_reason"] == "controller_work_unit_pending"
    assert "controller_work_unit_evidence_adoption" not in result


def test_study_runtime_status_hides_stale_authorization_when_newer_hard_methodology_handoff_exists(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(
        profile.workspace_root,
        study_id,
        quest_id=study_id,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="External validation framing is blocked by HDL unit harmonization.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / study_id
    write_text(quest_root / "quest.yaml", f"quest_id: {study_id}\nstudy_id: {study_id}\n")
    stale_work_unit = {
        "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
        "lane": "analysis-campaign",
        "summary": "Reframe the invalid transported-model claim.",
    }
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "waiting_for_user",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
                "blocked_turn_closeout": {
                    "run_id": "mas-run-dm002-hard",
                    "blocked_reason": "unit_harmonized_rerun_required",
                    "next_owner": "analysis_harmonization_owner",
                    "closeout_path": str(
                        quest_root / "artifacts" / "runtime" / "turn_closeouts" / "mas-run-dm002-hard.json"
                    ),
                },
                "last_controller_decision_authorization": {
                    "decision_id": "study-decision::dm002::methodology-reframe",
                    "source": "cli",
                    "route_target": "analysis-campaign",
                    "route_key_question": "medical_prose_quality_analysis_source_documentation_repair",
                    "work_unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                    "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
                    "controller_actions": ["ensure_study_runtime"],
                    "next_work_unit": stale_work_unit,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    analysis_path = study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json"
    source_path = study_root / "artifacts" / "controller" / "source_provenance" / "latest.json"
    quality_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    write_synced_submission_delivery(study_root, quest_root)
    eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::hard-methodology",
        "study_id": study_id,
        "quest_id": study_id,
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
        },
        "quality_assessment": {
            "medical_journal_prose_quality": {
                "status": "partial",
                "summary": "Prose quality is stale behind a hard methodology blocker.",
            },
        },
        "recommended_actions": [
            {
                "action_type": "bounded_analysis",
                "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::medical_prose_quality_route_back_analysis",
                "route_target": "analysis-campaign",
                "next_work_unit": {
                    "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
                    "lane": "analysis-campaign",
                    "summary": "Close AI reviewer evidence gaps.",
                },
            }
        ],
    }
    write_text(publication_eval_path, json.dumps(eval_payload, ensure_ascii=False, indent=2) + "\n")
    write_text(
        controller_decision_path,
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "study-decision::dm002::methodology-reframe",
                "study_id": study_id,
                "quest_id": study_id,
                "emitted_at": "2026-05-18T23:48:19+00:00",
                "decision_type": "route_back_same_line",
                "publication_eval_ref": {
                    "eval_id": eval_payload["eval_id"],
                    "artifact_path": str(publication_eval_path),
                },
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::dm002",
                    "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation.json"),
                    "summary_ref": str(quest_root / "artifacts" / "reports" / "escalation.json"),
                },
                "requires_human_confirmation": False,
                "controller_actions": [{"action_type": "ensure_study_runtime", "payload_ref": str(controller_decision_path)}],
                "route_target": "analysis-campaign",
                "route_key_question": "Can DM002 continue without original transported model provenance?",
                "route_rationale": "Route back for methodology reframe before manuscript work.",
                "work_unit_fingerprint": "decision::methodology_reframe_route_decision",
                "next_work_unit": stale_work_unit,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    for path, payload in (
        (
            analysis_path,
            {
                "surface": "analysis_harmonization_owner_result",
                "study_id": study_id,
                "owner": "analysis_harmonization_owner",
                "work_unit": "unit_harmonized_external_validation_rerun",
                "status": "blocked",
                "blocked_reason": "unit_harmonized_rerun_required",
                "typed_blocker_owner": "analysis_harmonization_owner",
                "typed_blocker": {
                    "blocker_id": "unit_harmonized_rerun_required",
                    "blocking_reasons": ["cox_model_application_provenance_insufficient_for_rerun"],
                },
                "unit_harmonized_rerun_completed": False,
            },
        ),
        (
            source_path,
            {
                "surface": "source_provenance_owner_result",
                "study_id": study_id,
                "owner": "source_provenance_owner",
                "work_unit": "recover_transport_model_provenance",
                "status": "blocked",
                "blocked_reason": "transport_model_provenance_recovery_required",
                "typed_blocker_owner": "source_provenance_owner",
                "typed_blocker": {"blocker_id": "transport_model_provenance_recovery_required"},
                "transport_model_provenance_recovered": False,
                "provenance_search": {
                    "searched": True,
                    "accepted_bundle_ref": None,
                    "result_summary_acceptance_allowed": False,
                    "substitute_refit_allowed": False,
                },
            },
        ),
        (
            quality_path,
            {
                "schema_version": 1,
                "status": "blocked",
                "ok": False,
                "study_id": study_id,
                "quest_id": study_id,
                "blocked_reason": "unit_harmonized_rerun_required",
                "next_owner": "analysis_harmonization_owner",
                "next_work_unit": "unit_harmonized_external_validation_rerun",
                "hard_methodology_target": {
                    "target_id": "hdl_unit_standardized_sensitivity",
                    "required_owner": "analysis_harmonization_owner",
                    "required_next_work_unit": "unit_harmonized_external_validation_rerun",
                    "typed_blocker": "unit_harmonized_rerun_required",
                },
                "quality_gate_relaxation_allowed": False,
                "current_package_write_allowed": False,
            },
        ),
    ):
        write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    write_text(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "surface_kind": "paper_authority_clean_migration",
                "status": "new_mas_authority_established",
                "study_id": study_id,
                "new_mas_authority": {
                    "owner": "ai_reviewer",
                    "publication_eval_ref": str(publication_eval_path),
                    "eval_id": eval_payload["eval_id"],
                    "established_at": "2026-05-18T00:00:00+00:00",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    for path, timestamp in (
        (analysis_path, 100),
        (source_path, 200),
        (publication_eval_path, 250),
        (controller_decision_path, 300),
        (quality_path, 400),
    ):
        _set_mtime(path, timestamp)
    gate_report = {
        "schema_version": 1,
        "gate_kind": "publishability_control",
        "generated_at": "2026-05-19T00:00:00+00:00",
        "quest_id": study_id,
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
        "controller_stage_note": "Hard methodology handoff supersedes stale AI reviewer prose transition.",
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
        lambda *, workspace_root: _clear_readiness_report(workspace_root, study_id),
    )

    result = module.study_runtime_status(
        profile=profile,
        study_id=study_id,
        include_progress_projection=False,
    )

    assert result["quest_status"] == "waiting_for_user"
    assert result["decision"] == "resume"
    assert result["reason"] == "quest_waiting_platform_repair_redrive"
    assert result["blocked_turn_closeout"]["blocked_reason"] == "unit_harmonized_rerun_required"
    assert result["blocked_turn_closeout"]["next_owner"] == "analysis_harmonization_owner"
    assert "domain_transition" not in result
    assert "last_controller_decision_authorization" not in result
