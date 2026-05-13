from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_build_runtime_watch_outer_loop_tick_request_routes_quality_repair_batch_before_task_intake(
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
        module.publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": study_root / "paper"})(),
    )
    monkeypatch.setattr(module.publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(
        module,
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

    request = module.build_runtime_watch_outer_loop_tick_request(
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


def test_study_outer_loop_tick_records_control_plane_route_blocked_quality_repair(
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
        module.study_runtime_router,
        "study_runtime_status",
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
    assert action_result["status"] == "control_plane_route_blocked"
    assert action_result["blocked_reason"] == "control_plane_route_blocked"
    assert "publication_supervisor_state.bundle_tasks_downstream_only" in action_result["message"]
