from __future__ import annotations

from tests.test_study_runtime_router_cases.shared import *  # noqa: F403

def test_progress_projection_keeps_write_route_when_story_surface_delta_is_missing(
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
                "blocked_turn_closeout": {
                    "run_id": "run-story-blocked",
                    "blocked_reason": "platform_repair_required_work_unit_redrive_budget_exhausted_without_result_evidence_and_publication_gate_allow_write_false",
                    "next_owner": "MAS/controller",
                    "closeout_path": str(
                        quest_root / "artifacts" / "runtime" / "turn_closeouts" / "run-story-blocked.json"
                    ),
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    eval_id = "publication-eval::001-risk::001-risk::2026-05-20T07:30:00+00:00"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
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
                        "summary": "The current manuscript needs story-level write repair.",
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
                        "route_rationale": "The story surface has not changed yet.",
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": "ai_reviewer_story_clean_external_validation_v3",
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
                    "source_work_unit": {
                        "unit_id": "manuscript_story_repair",
                        "lane": "write",
                        "summary": "Repair the paper story around the current evidence and claim boundary.",
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    lifecycle_payload = {
        "schema_version": 1,
        "source_eval_id": eval_id,
        "study_id": "001-risk",
        "quest_id": "001-risk",
        "status": "owner_handoff",
        "work_unit": {
            "unit_id": "manuscript_story_repair",
            "lane": "write",
            "summary": "Repair the paper story around the current evidence and claim boundary.",
        },
        "unit_statuses": [{"unit_id": "manuscript_story_repair", "status": "owner_handoff"}],
        "gate_replay_status": "pending_recheck",
        "terminal_consumed": True,
        "next_owner": "publication_gate",
        "recommended_next_route": "return_to_publication_gate_recheck",
        "closed_by": "controller_work_unit_evidence_adoption",
    }
    write_text(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        json.dumps(lifecycle_payload, ensure_ascii=False, indent=2) + "\n",
    )
    write_text(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "source_eval_id": eval_id,
                "status": "blocked",
                "ok": False,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "next_owner": "write",
                "repair_execution_evidence": {
                    "status": "blocked",
                    "blockers": ["manuscript_story_surface_delta_missing"],
                },
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
        "controller_stage_note": "Story repair still lacks a manuscript surface delta.",
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

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["interaction_arbitration"]["classification"] == "domain_transition_runtime_redrive"
    assert result["domain_transition"]["decision_type"] == "route_back_same_line"
    assert result["domain_transition"]["owner"] == "write"
    assert result["domain_transition"]["controller_action"] == "ensure_study_runtime"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "manuscript_story_repair"


def test_progress_projection_routes_completed_story_repair_to_ai_reviewer_recheck(
    monkeypatch,
    tmp_path: Path,
) -> None:
    repair_work_unit_id = "manuscript_story_repair"
    repair_work_unit_summary = "Repair the paper story around the current evidence and claim boundary."
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
                "last_controller_decision_authorization": {
                    "decision_id": "study-decision::001-risk::gate-recheck",
                    "controller_actions": ["run_gate_clearing_batch"],
                    "route_target": "review",
                    "work_unit_id": "publication_gate_recheck",
                    "work_unit_fingerprint": "publication-gate-recheck::closed-work-unit",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    eval_id = "publication-eval::001-risk::001-risk::2026-05-20T07:30:00+00:00"
    draft_path = study_root / "paper" / "draft.md"
    build_path = study_root / "paper" / "build" / "review_manuscript.md"
    write_text(draft_path, "# Current draft\n\nClean external-validation manuscript story.\n")
    write_text(build_path, "# Current review manuscript\n\nClean external-validation manuscript story.\n")
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
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
                "verdict": {"overall_verdict": "blocked", "primary_claim_status": "partial"},
                "quality_assessment": {
                    "clinical_significance": {"status": "ready"},
                    "evidence_strength": {"status": "partial"},
                    "novelty_positioning": {"status": "partial"},
                    "human_review_readiness": {"status": "blocked"},
                    "medical_journal_prose_quality": {
                        "status": "blocked",
                        "summary": "Old AI reviewer finding asked for manuscript story repair.",
                    },
                },
                "reviewer_operating_system": {
                    "currentness_checks": {
                        "medical_prose_review": {
                            "status": "current",
                            "request_digest": "sha256:request-current",
                            "manuscript_ref": str(draft_path),
                            "manuscript_digest": "sha256:manuscript-before-repair",
                            "route_back_required": True,
                            "route_target": "write",
                        }
                    }
                },
                "recommended_actions": [
                    {
                        "action_id": "return-to-write-clean-story",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "reason": "The prior reviewer finding requested story repair.",
                        "route_target": "write",
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": "ai_reviewer_story_clean_external_validation_v3",
                        "next_work_unit": {
                            "unit_id": repair_work_unit_id,
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
                "publication_eval_ref": {"eval_id": eval_id, "artifact_path": str(publication_eval_path)},
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
                    "source_work_unit": {
                        "unit_id": repair_work_unit_id,
                        "lane": "write",
                        "summary": repair_work_unit_summary,
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    lifecycle_payload = {
        "schema_version": 1,
        "source_eval_id": eval_id,
        "study_id": "001-risk",
        "quest_id": "001-risk",
        "status": "owner_handoff",
        "work_unit": {
            "unit_id": repair_work_unit_id,
            "lane": "write",
            "summary": repair_work_unit_summary,
        },
        "unit_statuses": [{"unit_id": repair_work_unit_id, "status": "owner_handoff"}],
        "gate_replay_status": "pending_recheck",
        "terminal_consumed": True,
        "next_owner": "publication_gate",
        "recommended_next_route": "return_to_publication_gate_recheck",
        "closed_by": "controller_work_unit_evidence_adoption",
    }
    write_text(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        json.dumps(lifecycle_payload, ensure_ascii=False, indent=2) + "\n",
    )
    ai_reviewer_request_path = (
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    )
    write_text(
        ai_reviewer_request_path,
        json.dumps({"request_id": "ai-reviewer-recheck::001-risk"}, ensure_ascii=False, indent=2) + "\n",
    )
    repair_evidence = {
        "surface": "repair_execution_evidence",
        "schema_version": 1,
        "study_id": "001-risk",
        "quest_id": "001-risk",
        "status": "progress_delta_candidate",
        "repair_work_unit": lifecycle_payload["work_unit"],
        "review_finding": {"source_eval_id": eval_id},
        "source_refs": [str(publication_eval_path)],
        "changed_artifact_refs": [
            {"path": str(draft_path), "artifact_role": "canonical_manuscript_story_surface"}
        ],
        "canonical_artifact_delta": {
            "status": "fresh",
            "meaningful_artifact_delta": True,
            "changed_artifact_ref_count": 1,
            "artifact_refs": [
                {"path": str(draft_path), "artifact_role": "canonical_manuscript_story_surface"}
            ],
        },
        "gate_replay_target": "publication_gate",
        "gate_replay_required": True,
        "gate_replay_done": True,
        "gate_replay_refs": [str(publication_eval_path)],
        "ai_reviewer_recheck_required": True,
        "ai_reviewer_recheck_done": True,
        "ai_reviewer_recheck_request_ref": str(ai_reviewer_request_path),
        "manuscript_surface_hygiene": {
            "required": True,
            "status": "clear",
            "blockers": [],
            "story_surface_delta_required": True,
            "story_surface_delta_present": True,
            "story_surface_delta_refs": [
                {"path": str(draft_path), "artifact_role": "canonical_manuscript_story_surface"}
            ],
        },
        "progress_delta_candidate": True,
        "blockers": [],
        "quality_authorized": False,
        "submission_authorized": False,
        "current_package_write_authorized": False,
    }
    write_text(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        json.dumps(repair_evidence, ensure_ascii=False, indent=2) + "\n",
    )
    write_text(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "source_eval_id": eval_id,
                "status": "executed",
                "ok": True,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "repair_execution_evidence": repair_evidence,
                "repair_execution_evidence_path": str(
                    study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
                ),
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
        "controller_stage_note": "Story repair has changed the manuscript; AI reviewer must re-evaluate.",
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

    assert result["decision"] == "resume"
    assert result["reason"] == "domain_transition_ai_reviewer_re_eval"
    assert result["domain_transition"]["decision_type"] == "ai_reviewer_re_eval"
    assert result["domain_transition"]["owner"] == "ai_reviewer"
    assert result["domain_transition"]["controller_action"] == "return_to_ai_reviewer_workflow"
    assert result["domain_transition"]["next_work_unit"]["unit_id"] == "ai_reviewer_medical_prose_quality_review"
