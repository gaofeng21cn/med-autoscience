from .shared import *  # noqa: F403


def test_study_runtime_status_routes_stale_ai_reviewer_eval_to_recheck_before_closed_gate_lifecycle(
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
                            "route_target": "write",
                        }
                    }
                },
                "quality_assessment": {
                    "medical_journal_prose_quality": {"status": "ready"}
                },
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "route_target": "write",
                        "next_work_unit": {
                            "unit_id": "manuscript_story_repair",
                            "lane": "write",
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
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "task_id": "study-task::001-risk::20260520T163325Z",
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-05-20T16:33:25+00:00",
                "task_intake_kind": "reviewer_revision",
                "task_intent": "Reviewer revision: current manuscript requires new medical journal quality review.",
                "constraints": ["Route stale AI reviewer conclusions back to AI reviewer before gate replay."],
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
                    "unit_id": "manuscript_story_repair",
                    "lane": "write",
                    "summary": "Rewrite the manuscript story around current evidence.",
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
        "controller_stage_note": "Latest reviewer revision requires a fresh AI reviewer assessment.",
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

    result = module.study_runtime_status(
        profile=profile,
        study_id="001-risk",
        include_progress_projection=False,
    )

    assert result["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert result["domain_transition"]["decision_type"] == "ai_reviewer_re_eval"
    assert result["domain_transition"]["owner"] == "ai_reviewer"
    assert result["domain_transition"]["controller_action"] == "return_to_ai_reviewer_workflow"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"
