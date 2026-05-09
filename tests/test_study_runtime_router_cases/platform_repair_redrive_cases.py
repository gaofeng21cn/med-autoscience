from .shared import *  # noqa: F403


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
