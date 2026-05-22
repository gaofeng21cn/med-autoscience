from __future__ import annotations

from tests.test_study_runtime_router_cases.shared import *  # noqa: F403

def test_progress_projection_ignores_stale_publication_gate_recheck_lifecycle_for_current_write_route(
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
                "status": "waiting_for_user",
                "active_run_id": None,
                "worker_running": False,
                "pending_user_message_count": 0,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "turn_closeout",
                "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    current_eval_id = "publication-eval::001-risk::001-risk::2026-05-21T08:30:00+00:00"
    stale_eval_id = "publication-eval::001-risk::001-risk::2026-05-20T07:30:00+00:00"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    write_text(
        publication_eval_path,
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": current_eval_id,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-05-21T08:30:00+00:00",
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
                            "request_digest": "request-current",
                            "manuscript_ref": "paper/draft.md",
                            "manuscript_digest": "manuscript-current",
                            "route_target": "write",
                        }
                    }
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {
                        "status": "partial",
                        "summary": "The current reviewer finding requires medical prose write repair.",
                    }
                },
                "recommended_actions": [
                    {
                        "action_id": "current-medical-prose-write-repair",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "reason": "The current manuscript needs medical prose write repair.",
                        "route_target": "write",
                        "route_key_question": "Repair medical manuscript prose quality.",
                        "route_rationale": "Current AI reviewer prose assessment routes back to write.",
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": "publication-blockers::medical-prose-current",
                        "next_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                            "summary": "Revise the manuscript to medical journal prose standards.",
                        },
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    write_text(
        controller_decision_path,
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "study-decision::001-risk::gate-recheck",
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-05-20T09:10:08+00:00",
                "decision_type": "route_back_same_line",
                "publication_eval_ref": {"eval_id": stale_eval_id, "artifact_path": str(publication_eval_path)},
                "requires_human_confirmation": False,
                "controller_actions": [
                    {"action_type": "run_gate_clearing_batch", "payload_ref": str(controller_decision_path)}
                ],
                "route_target": "review",
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
                "source_eval_id": stale_eval_id,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "status": "owner_handoff",
                "work_unit": {
                    "unit_id": "manuscript_story_repair",
                    "lane": "write",
                    "summary": "Prior manuscript story repair.",
                },
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
        "controller_stage_note": "Current AI reviewer finding routes to write.",
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

    assert result["domain_transition"]["decision_type"] == "route_back_same_line"
    assert result["domain_transition"]["owner"] == "write"
    assert result["domain_transition"]["controller_action"] == "ensure_study_runtime"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "medical_prose_write_repair"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] != "publication_gate_recheck"
