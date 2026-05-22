from .shared import *  # noqa: F403
from .publication_gate_recheck_lifecycle_cases_cases.test_stale_lifecycle_currentness import *  # noqa: F403,F401
from .publication_gate_recheck_lifecycle_cases_cases.test_story_surface_delta_routes import *  # noqa: F403,F401


def test_progress_projection_routes_closed_work_unit_lifecycle_to_publication_gate_recheck(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="External validation framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstudy_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-001",
                "runner_live": True,
                "bash_live": True,
                "runtime_audit": {
                    "ok": True,
                    "status": "live",
                    "source": "mas_runtime_core_turn_lifecycle",
                    "active_run_id": "run-001",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
                "bash_session_audit": {"ok": True, "status": "none"},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    stale_work_unit = {
        "unit_id": "manuscript_story_repair",
        "lane": "write",
        "summary": "Rewrite the manuscript story around current evidence.",
    }
    eval_id = "publication-eval::001-risk::001-risk::2026-05-20T07:30:00+00:00"
    write_text(
        publication_eval_path,
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": eval_id,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-05-20T07:30:00+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                },
                "reviewer_operating_system": {
                    "currentness_checks": {
                        "medical_prose_review": {
                            "status": "current",
                            "route_back_required": True,
                            "request_digest": "request-digest",
                            "manuscript_ref": "paper/manuscript.md",
                            "manuscript_digest": "manuscript-digest",
                            "route_target": "write",
                        }
                    }
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "partial",
                        "summary": "Stale route-back remains in the prior AI reviewer projection.",
                    }
                },
                "recommended_actions": [
                    {
                        "action_id": "stale-write-route-back",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "reason": "Stale AI reviewer projection still points to manuscript story repair.",
                        "route_target": "write",
                        "route_key_question": "Repair manuscript story.",
                        "route_rationale": "This stale action must not outrank a closed work-unit lifecycle.",
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": "publication-blockers::stale-write",
                        "next_work_unit": stale_work_unit,
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
                "decision_id": "study-decision::001-risk::stale-write",
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-05-20T07:35:00+00:00",
                "decision_type": "route_back_same_line",
                "publication_eval_ref": {"eval_id": eval_id, "artifact_path": str(publication_eval_path)},
                "requires_human_confirmation": False,
                "controller_actions": [
                    {"action_type": "ensure_study_runtime", "payload_ref": str(controller_decision_path)}
                ],
                "route_target": "write",
                "route_key_question": "Repair manuscript story.",
                "route_rationale": "Stale controller decision mirrors the prior AI reviewer projection.",
                "work_unit_fingerprint": "publication-blockers::stale-write",
                "next_work_unit": stale_work_unit,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "source_eval_id": eval_id,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "status": "owner_handoff",
                "work_unit": stale_work_unit,
                "unit_statuses": [{"unit_id": "manuscript_story_repair", "status": "owner_handoff"}],
                "gate_replay_status": "pending_recheck",
                "terminal_consumed": True,
                "next_owner": "publication_gate",
                "recommended_next_route": "return_to_publication_gate_recheck",
                "closed_by": "controller_work_unit_evidence_adoption",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    gate_report = {
        "schema_version": 1,
        "status": "blocked",
        "allow_write": False,
        "blockers": ["medical_publication_surface_blocked"],
        "supervisor_phase": "publishability_gate_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": True,
        "current_required_action": "return_to_publishability_gate",
        "deferred_downstream_actions": [],
        "controller_stage_note": "Return to publication gate after the closed work-unit handoff.",
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

    result = module.progress_projection(
        profile=profile,
        study_id="001-risk",
        include_progress_projection=False,
    )

    assert result["quest_status"] == "running"
    assert result["active_run_id"] == "run-default"
    assert result["domain_transition"]["decision_type"] == "publication_gate_blocker"
    assert result["domain_transition"]["owner"] == "publication_gate"
    assert result["domain_transition"]["controller_action"] == "run_gate_clearing_batch"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "publication_gate_recheck"
    assert result["domain_transition"]["next_work_unit"]["source_work_unit"]["unit_id"] == "manuscript_story_repair"
    assert result["reason"] == "domain_transition_publication_gate_blocker"
    assert result["interaction_arbitration"]["reason_code"] == "domain_transition_publication_gate_blocker"


def test_progress_projection_does_not_requeue_publication_gate_recheck_lifecycle_to_itself(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="External validation framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstudy_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "running",
                "active_run_id": "run-001",
                "runner_live": True,
                "bash_live": True,
                "runtime_audit": {
                    "ok": True,
                    "status": "live",
                    "source": "mas_runtime_core_turn_lifecycle",
                    "active_run_id": "run-001",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
                "bash_session_audit": {"ok": True, "status": "none"},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    eval_id = "publication-eval::001-risk::001-risk::2026-05-20T07:30:00+00:00"
    write_text(
        publication_eval_path,
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": eval_id,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-05-20T07:30:00+00:00",
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "publication_eval_ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                },
                "reviewer_operating_system": {
                    "currentness_checks": {
                        "medical_prose_review": {
                            "status": "current",
                            "route_back_required": True,
                            "request_digest": "request-digest",
                            "manuscript_ref": "paper/manuscript.md",
                            "manuscript_digest": "manuscript-digest",
                            "route_target": "write",
                        }
                    }
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "blocked",
                        "summary": "The AI reviewer still requires story-level manuscript repair.",
                    }
                },
                "recommended_actions": [
                    {
                        "action_id": "return-to-write-clean-story",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "reason": "The current manuscript needs story-level write repair.",
                        "route_target": "write",
                        "route_key_question": "Repair manuscript story.",
                        "route_rationale": "The publication gate replay has already run; route to write.",
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": "publication-blockers::write-clean-story",
                        "next_work_unit": {
                            "unit_id": "manuscript_story_repair",
                            "lane": "write",
                            "summary": "Rewrite the manuscript story around current evidence.",
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
                "decision_id": "study-decision::001-risk::gate-recheck",
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-05-20T07:55:10+00:00",
                "decision_type": "route_back_same_line",
                "publication_eval_ref": {"eval_id": eval_id, "artifact_path": str(publication_eval_path)},
                "requires_human_confirmation": False,
                "controller_actions": [
                    {"action_type": "run_gate_clearing_batch", "payload_ref": str(controller_decision_path)}
                ],
                "route_target": "review",
                "route_key_question": "已完成的 publication work unit 是否通过 publication gate replay？",
                "route_rationale": "Replay the gate for a closed controller work unit.",
                "work_unit_fingerprint": "publication-gate-recheck::closed-work-unit",
                "next_work_unit": {
                    "unit_id": "publication_gate_recheck",
                    "lane": "review",
                    "summary": "Replay the publication gate for the closed controller work unit.",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "status": "owner_handoff",
                "work_unit": {
                    "unit_id": "publication_gate_recheck",
                    "lane": "review",
                    "summary": "Replay the publication gate for the closed controller work unit.",
                },
                "unit_statuses": [{"unit_id": "publication_gate_recheck", "status": "owner_handoff"}],
                "gate_replay_status": "pending_recheck",
                "terminal_consumed": True,
                "next_owner": "publication_gate",
                "recommended_next_route": "return_to_publication_gate_recheck",
                "closed_by": "controller_work_unit_evidence_adoption",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    gate_report = {
        "schema_version": 1,
        "status": "blocked",
        "allow_write": False,
        "blockers": ["medical_publication_surface_blocked"],
        "supervisor_phase": "publishability_gate_blocked",
        "phase_owner": "publication_gate",
        "upstream_scientific_anchor_ready": True,
        "bundle_tasks_downstream_only": True,
        "current_required_action": "return_to_publishability_gate",
        "deferred_downstream_actions": [],
        "controller_stage_note": "Gate replay is blocked; route back to write.",
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

    result = module.progress_projection(
        profile=profile,
        study_id="001-risk",
        include_progress_projection=False,
    )

    assert result["quest_status"] == "running"
    assert result["domain_transition"]["decision_type"] == "route_back_same_line"
    assert result["domain_transition"]["owner"] == "write"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "manuscript_story_repair"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] != "publication_gate_recheck"
