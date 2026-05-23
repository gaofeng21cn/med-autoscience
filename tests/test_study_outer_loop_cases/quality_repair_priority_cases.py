from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_build_domain_health_diagnostic_outer_loop_tick_request_routes_quality_repair_batch_before_task_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-25T04:41:53+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-25T04:41:53+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(
                    study_root / "paper" / "submission_minimal" / "submission_manifest.json"
                ),
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "Quality-floor blockers remain before the paper line can continue.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "must_fix",
                    "summary": "claim_evidence_map_missing_or_incomplete",
                    "evidence_refs": [str(study_root / "paper")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-task-intake",
                    "action_type": "bounded_analysis",
                    "priority": "now",
                    "reason": "Return to the same line for bounded repair.",
                    "route_target": "analysis-campaign",
                    "route_key_question": "Which claim-evidence repair is still blocking publishability?",
                    "route_rationale": "Publication gate selected a MAS-owned quality repair work unit.",
                    "evidence_refs": [str(study_root / "paper")],
                    "requires_controller_decision": True,
                    "next_work_unit": {
                        "unit_id": "analysis_claim_evidence_repair",
                        "lane": "analysis-campaign",
                        "summary": "Repair claim-evidence and results traceability blockers.",
                    },
                    "work_unit_fingerprint": "publication-blockers::quality",
                }
            ],
        },
    )
    gate_report = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_map_missing_or_incomplete"],
        "bundle_tasks_downstream_only": True,
    }
    _write_json(
        study_root / "artifacts" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-25T04:42:53+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-25T04:42:53+00:00",
            "quality_closure_truth": {
                "state": "quality_repair_required",
                "summary": "Hard publication-quality blockers remain open.",
                "current_required_action": "return_to_publishability_gate",
                "route_target": "review",
            },
            "quality_execution_lane": {
                "lane_id": "general_quality_repair",
                "route_target": "review",
                "route_key_question": "Which deterministic claim-evidence repair is still blocking publishability?",
                "summary": "Run deterministic repair units, then replay the publishability gate.",
            },
        },
    )
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        _domain_health_diagnostic_tick_request_module().publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": study_root / "paper"})(),
    )
    monkeypatch.setattr(_domain_health_diagnostic_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(
        _domain_health_diagnostic_tick_request_module(),
        "recommended_task_intake_action",
        lambda **_: {
            "action_id": "task-intake::001-risk::analysis-campaign",
            "action_type": "bounded_analysis",
            "priority": "now",
            "reason": "Task intake would otherwise relaunch the managed runner.",
            "route_target": "analysis-campaign",
            "route_key_question": "Which claim-evidence repair is still blocking publishability?",
            "route_rationale": "The paper needs bounded analysis repair.",
            "requires_controller_decision": True,
            "controller_action_type": "ensure_study_runtime",
            "next_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence and results traceability blockers.",
            },
            "work_unit_fingerprint": "publication-blockers::quality",
        },
    )

    request = module.build_domain_health_diagnostic_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "active",
            "runtime_liveness_status": "stale",
            "active_run_id": None,
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "route_back_same_line"
    assert request["route_target"] == "review"
    assert request["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert request["controller_actions"] == [
        {
            "action_type": "run_quality_repair_batch",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_ai_reviewer_currentness_preempts_stale_methodology_intake_and_repair_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-05-19T17:55:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-05-19T17:55:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "policy_id": "publication_gate_projection_v1",
                "source_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
                "ai_reviewer_required": True,
                "mechanical_projection_used_as_quality_authority": False,
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "Bundle-stage blockers remain; subjective prose quality needs AI reviewer.",
                "stop_loss_pressure": "watch",
            },
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical framing is ready.",
                    "evidence_refs": [str(study_root / "paper")],
                },
                "evidence_strength": {
                    "status": "blocked",
                    "summary": "Publication gate still reports evidence and delivery blockers.",
                    "evidence_refs": [str(study_root / "paper")],
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Novelty framing is ready.",
                    "evidence_refs": [str(study_root / "paper")],
                },
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "Mechanical projection cannot authorize medical journal prose quality.",
                    "evidence_refs": [str(study_root / "paper")],
                },
                "human_review_readiness": {
                    "status": "blocked",
                    "summary": "Human review waits for AI reviewer prose quality and gate closure.",
                    "evidence_refs": [str(study_root / "paper")],
                },
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_submission_minimal_authority",
                    "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::return_to_controller::stale-submission",
                    "action_type": "return_to_controller",
                    "priority": "now",
                    "reason": "Stale submission projection needs gate specificity.",
                    "evidence_refs": [
                        str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
                    ],
                    "requires_controller_decision": True,
                    "work_unit_fingerprint": "publication-blockers::stale-submission",
                    "next_work_unit": {
                        "unit_id": "gate_needs_specificity",
                        "lane": "controller",
                        "summary": "Ask the publication gate to identify concrete targets.",
                    },
                    "blocking_work_units": [
                        {
                            "unit_id": "gate_needs_specificity",
                            "lane": "controller",
                            "summary": "Ask the publication gate to identify concrete targets.",
                        }
                    ],
                    "specificity_targets": [
                        {
                            "target_kind": "claim",
                            "target_id": "claim_evidence_map",
                            "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                            "blocking_reason": "stale_submission_minimal_authority",
                        }
                    ],
                }
            ],
        },
    )
    gate_report = {
        "status": "blocked",
        "allow_write": False,
        "blockers": [
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "medical_publication_surface_blocked",
            "submission_hardening_incomplete",
            "submission_surface_qc_failure_present",
        ],
        "current_required_action": "complete_bundle_stage",
        "supervisor_phase": "bundle_stage_blocked",
        "bundle_tasks_downstream_only": False,
        "medical_publication_surface_status": "blocked",
        "submission_minimal_authority_status": "stale_source_changed",
        "study_delivery_status": "stale_source_changed",
    }
    stale_analysis_action = {
        "action_id": "quality-repair-batch::stale-analysis",
        "action_type": "bounded_analysis",
        "priority": "now",
        "reason": "Stale batch route must not override AI reviewer currentness.",
        "route_target": "analysis-campaign",
        "route_key_question": "analysis_claim_evidence_repair",
        "route_rationale": "Old task-intake methodology route residue.",
        "requires_controller_decision": True,
        "controller_action_type": "run_quality_repair_batch",
        "next_work_unit": {
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
        },
        "blocking_work_units": [
            {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
            }
        ],
        "work_unit_fingerprint": "publication-blockers::stale-analysis",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        _domain_health_diagnostic_tick_request_module().publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": study_root / "paper"})(),
    )
    monkeypatch.setattr(_domain_health_diagnostic_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(_domain_health_diagnostic_tick_request_module(), "recommended_task_intake_action", lambda **_: stale_analysis_action)
    monkeypatch.setattr(module.quality_repair_batch, "build_quality_repair_batch_recommended_action", lambda **_: stale_analysis_action)
    monkeypatch.setattr(module.gate_clearing_batch, "build_gate_clearing_batch_recommended_action", lambda **_: None)

    request = module.build_domain_health_diagnostic_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "mas-run-001",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_blocked",
                "current_required_action": "complete_bundle_stage",
                "bundle_tasks_downstream_only": False,
                "publication_gate_allows_direct_write": False,
            },
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "review"
    assert request["controller_actions"] == [
        {
            "action_type": "return_to_ai_reviewer_workflow",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    assert request["work_unit_fingerprint"] == (
        "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck"
    )
    assert request["next_work_unit"]["unit_id"] == "ai_reviewer_recheck"


def test_current_ai_reviewer_route_back_preempts_gate_and_quality_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution")
    quest_root = profile.managed_runtime_home / "quests" / "002-dm-china-us-mortality-attribution"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::002::current-ai-reviewer-route-back",
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "emitted_at": "2026-05-22T02:04:07+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::002-dm-china-us-mortality-attribution::v1",
                "publication_objective": "external validation of diabetes mortality risk transportability",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(
                    quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                ),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": [str(study_root / "paper" / "draft.md")],
                "ai_reviewer_required": False,
            },
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "AI reviewer routes the current manuscript back to write.",
                "stop_loss_pressure": "high",
            },
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical framing is ready for current evidence.",
                    "evidence_refs": [str(study_root / "paper" / "draft.md")],
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Analysis evidence is current enough for write repair.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "latest.json")],
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Transportability claim boundary is explicit.",
                    "evidence_refs": [str(study_root / "paper" / "draft.md")],
                },
                "medical_journal_prose_quality": {
                    "status": "blocked",
                    "summary": "Current prose review requires narrow write repair.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json")],
                },
                "human_review_readiness": {
                    "status": "blocked",
                    "summary": "Human review waits for the write repair and gate replay.",
                    "evidence_refs": [str(study_root / "paper" / "draft.md")],
                }
            },
            "reviewer_operating_system": {
                "contract_id": "medical_publication_ai_reviewer_os_v1",
                "input_bundle": {
                    "manuscript": str(study_root / "paper" / "draft.md"),
                    "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                    "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
                    "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
                    "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
                    "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
                    "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                    "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                },
                "rubric_scores": {},
                "decision_matrix": [{"dimension": "medical_journal_prose_quality", "status": "blocked"}],
                "currentness_checks": {
                    "medical_prose_review": {
                        "status": "current",
                        "request_ref": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
                        "request_digest": "sha256:current-route-back-request",
                        "manuscript_ref": str(study_root / "paper" / "draft.md"),
                        "manuscript_digest": "sha256:current-route-back-manuscript",
                        "route_back_required": True,
                        "route_target": "write",
                    },
                    "current_package_freshness": {
                        "status": "downstream_pending",
                        "source_eval_id": "publication-eval::002::current-ai-reviewer-route-back",
                    }
                },
                "future_facing_limitations_plan": [
                    {
                        "limitation": "The current manuscript still needs narrow prose repair.",
                        "impact_on_claim": "No claim expansion is authorized before write repair.",
                        "required_future_analysis_data_or_design": "Re-run reviewer currentness after substantive changes.",
                        "current_manuscript_wording_must_be_restrained": True,
                    }
                ],
                "provenance_checks": {
                    "assessment_owner": "ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                    "mechanical_projection_used_as_quality_authority": False,
                },
                "route_back_decision": {
                    "recommended_action": "route_back_same_line",
                    "rationale": "Current AI reviewer prose review routes the same paper line back to write.",
                },
            },
            "future_facing_limitations_plan": [
                {
                    "limitation": "The current manuscript still needs narrow prose repair.",
                    "impact_on_claim": "No claim expansion is authorized before write repair.",
                    "required_future_analysis_data_or_design": "Re-run reviewer currentness after substantive changes.",
                    "current_manuscript_wording_must_be_restrained": True,
                }
            ],
            "gaps": [
                {
                    "gap_id": "dm002-current-prose-repair",
                    "gap_type": "reporting",
                    "severity": "must_fix",
                    "summary": "Current AI reviewer prose review requires write repair.",
                    "evidence_refs": [str(study_root / "paper" / "draft.md")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "route-back-same-line-write-paper-repair",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "The current AI reviewer finding routes the same paper line back to write.",
                    "route_target": "write",
                    "route_key_question": "Can the current external-validation evidence be absorbed into clean manuscript prose?",
                    "route_rationale": "AI reviewer currentness is closed and the remaining issue is write-owner paper repair.",
                    "evidence_refs": [
                        str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
                        str(study_root / "paper" / "draft.md"),
                    ],
                    "requires_controller_decision": True,
                    "work_unit_fingerprint": "dm002_current_ai_reviewer_write_repair",
                    "next_work_unit": {
                        "unit_id": "dm002_same_line_publication_paper_repair",
                        "lane": "write",
                        "summary": "Repair current manuscript prose against the current AI reviewer findings.",
                    },
                    "blocking_work_units": [
                        {
                            "unit_id": "dm002_same_line_publication_paper_repair",
                            "lane": "write",
                            "summary": "Repair current manuscript prose against the current AI reviewer findings.",
                        }
                    ],
                }
            ],
        },
    )
    gate_report = {
        "status": "blocked",
        "allow_write": False,
        "blockers": [
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "medical_publication_surface_blocked",
        ],
        "current_required_action": "return_to_publishability_gate",
        "supervisor_phase": "publishability_gate_blocked",
        "medical_publication_surface_status": "blocked",
    }
    stale_batch_action = {
        "action_id": "quality-repair-batch::stale-gate",
        "action_type": "route_back_same_line",
        "priority": "now",
        "reason": "Stale gate batch must not override the current AI reviewer route-back.",
        "route_target": "finalize",
        "route_key_question": "stale package refresh",
        "route_rationale": "Old gate-clearing residue.",
        "requires_controller_decision": True,
        "controller_action_type": "run_gate_clearing_batch",
        "next_work_unit": {
            "unit_id": "submission_minimal_refresh",
            "lane": "finalize",
            "summary": "Stale downstream package refresh.",
        },
        "blocking_work_units": [
            {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Stale downstream package refresh.",
            }
        ],
        "work_unit_fingerprint": "publication-blockers::stale-gate",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        _domain_health_diagnostic_tick_request_module().publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": study_root / "paper"})(),
    )
    monkeypatch.setattr(
        _domain_health_diagnostic_tick_request_module().publication_gate_controller,
        "build_gate_report",
        lambda state: gate_report,
    )
    monkeypatch.setattr(_domain_health_diagnostic_tick_request_module(), "recommended_task_intake_action", lambda **_: None)
    monkeypatch.setattr(module.quality_repair_batch, "build_quality_repair_batch_recommended_action", lambda **_: stale_batch_action)
    monkeypatch.setattr(module.gate_clearing_batch, "build_gate_clearing_batch_recommended_action", lambda **_: stale_batch_action)

    request = module.build_domain_health_diagnostic_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "quest_status": "waiting_for_user",
            "runtime_liveness_status": "parked",
            "active_run_id": None,
            "reason": "domain_transition_ai_reviewer_re_eval",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "route_back_same_line"
    assert request["route_target"] == "write"
    assert request["controller_actions"] == [
        {
            "action_type": "run_quality_repair_batch",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    assert request["work_unit_fingerprint"] == "domain-transition::route_back_same_line::dm002_same_line_publication_paper_repair"
    assert request["next_work_unit"]["unit_id"] == "dm002_same_line_publication_paper_repair"


def test_quality_repair_batch_preserves_ai_reviewer_methodology_analysis_work_unit(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_repair_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_id = "quest-001"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    work_unit = {
        "unit_id": "medical_prose_quality_analysis_source_documentation_repair",
        "lane": "analysis-campaign",
        "summary": (
            "Materialize or type-block model reproducibility, uncertainty, calibration, "
            "and HDL harmonization evidence before prose/finalize review."
        ),
    }
    publication_eval_payload = {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-05-18T09:12:34+00:00",
        "study_id": "001-risk",
        "quest_id": quest_id,
        "emitted_at": "2026-05-18T09:12:34+00:00",
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "HDL/unit harmonization blocks medical-journal readiness.",
        },
        "recommended_actions": [
            {
                "action_id": "publication-eval-action::bounded_analysis::medical-prose-quality",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": (
                    "The reviewer-owned prose verdict is blocked by analysis/source-documentation gaps, "
                    "including HDL/unit harmonization."
                ),
                "route_target": "analysis-campaign",
                "route_key_question": "unit-harmonized external validation rerun or typed blocker",
                "route_rationale": "Analysis owner must close the methodologic blocker before prose review.",
                "requires_controller_decision": True,
                "work_unit_fingerprint": (
                    "domain-transition::ai_reviewer_re_eval::medical_prose_quality_route_back_analysis"
                ),
                "next_work_unit": dict(work_unit),
                "blocking_work_units": [dict(work_unit)],
            }
        ],
    }
    _write_json(publication_eval_path, publication_eval_payload)
    _write_json(
        study_root / "artifacts" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-05-18T09:12:35+00:00",
            "study_id": "001-risk",
            "quest_id": quest_id,
            "emitted_at": "2026-05-18T09:12:35+00:00",
            "quality_closure_truth": {
                "state": "quality_repair_required",
                "summary": "A methodologic analysis blocker remains open.",
                "current_required_action": "return_to_analysis_campaign",
                "route_target": "analysis-campaign",
            },
            "quality_execution_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "analysis-campaign",
                "route_key_question": "unit-harmonized external validation rerun or typed blocker",
                "summary": "Return to the analysis/harmonization owner before prose or finalize.",
            },
        },
    )

    action = module.build_quality_repair_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        gate_report={
            "status": "blocked",
            "allow_write": False,
            "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
            "current_required_action": "return_to_publishability_gate",
            "medical_publication_surface_status": "blocked",
            "medical_publication_surface_named_blockers": ["missing_medical_story_contract"],
            "blocking_artifact_refs": [{"source_path": "analysis/clean_room_execution/20_transportability"}],
            "bundle_tasks_downstream_only": True,
        },
    )

    assert action is not None
    assert action["route_target"] == "analysis-campaign"
    assert action["work_unit_fingerprint"] == (
        "domain-transition::ai_reviewer_re_eval::medical_prose_quality_route_back_analysis"
    )
    assert action["next_work_unit"] == work_unit
    assert action["blocking_work_units"] == [work_unit]


def test_study_outer_loop_tick_records_authority_route_blocked_quality_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    def blocked_quality_repair_batch(**_: object) -> dict[str, object]:
        raise PermissionError(
            "control plane route blocked paper_write: dispatch_gate_blocked, "
            "publication_supervisor_state.bundle_tasks_downstream_only"
        )

    monkeypatch.setattr(module.quality_repair_batch, "run_quality_repair_batch", blocked_quality_repair_batch)

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=_write_charter(study_root),
        publication_eval_ref=publication_eval_ref,
        decision_type="route_back_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "run_quality_repair_batch",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Quality repair should be attempted only through authorized MAS controller routes.",
        source="test-source",
        recorded_at="2026-04-25T04:45:00+00:00",
    )

    assert result["dispatch_status"] == "blocked"
    assert result["executed_controller_action"]["action_type"] == "run_quality_repair_batch"
    action_result = result["executed_controller_action"]["result"]
    assert action_result["ok"] is False
    assert action_result["status"] == "authority_route_blocked"
    assert action_result["blocked_reason"] == "authority_route_blocked"
    assert "publication_supervisor_state.bundle_tasks_downstream_only" in action_result["message"]
