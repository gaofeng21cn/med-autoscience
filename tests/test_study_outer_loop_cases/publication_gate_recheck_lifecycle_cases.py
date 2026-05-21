from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_build_runtime_watch_outer_loop_tick_request_honors_closed_publication_work_unit_lifecycle(
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
            "eval_id": "publication-eval::001-risk::quest-001::2026-05-20T07:30:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-05-20T07:30:00+00:00",
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
            "verdict": {
                "overall_verdict": "blocked",
                "primary_claim_status": "partial",
                "summary": "Publication gate must recheck the repaired manuscript.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "must_fix",
                    "summary": "stale write blocker already repaired; gate recheck pending",
                    "evidence_refs": [str(study_root / "paper")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-stale-write",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Stale publication eval still points to manuscript story repair.",
                    "route_target": "write",
                    "route_key_question": "Repair manuscript story.",
                    "route_rationale": "This stale action must not outrank closed work-unit lifecycle.",
                    "evidence_refs": [str(study_root / "paper")],
                    "requires_controller_decision": True,
                    "next_work_unit": {
                        "unit_id": "manuscript_story_repair",
                        "lane": "write",
                        "summary": "Repair the paper story around the current evidence and claim boundary.",
                    },
                    "work_unit_fingerprint": "publication-blockers::stale-write",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
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
        },
    )
    gate_report = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
        "current_required_action": "return_to_publishability_gate",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        _runtime_watch_tick_request_module().publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": study_root / "paper"})(),
    )
    monkeypatch.setattr(_runtime_watch_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(
        _runtime_watch_tick_request_module(),
        "recommended_task_intake_action",
        lambda **_: {
            "action_id": "task-intake::001-risk::write",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Task intake would otherwise relaunch manuscript story repair.",
            "route_target": "write",
            "route_key_question": "Repair manuscript story.",
            "route_rationale": "Stale task intake must not outrank closed work-unit lifecycle.",
            "requires_controller_decision": True,
            "controller_action_type": "run_quality_repair_batch",
            "next_work_unit": {
                "unit_id": "manuscript_story_repair",
                "lane": "write",
                "summary": "Repair the paper story around the current evidence and claim boundary.",
            },
            "work_unit_fingerprint": "publication-blockers::stale-write",
        },
    )
    monkeypatch.setattr(
        module.quality_repair_batch,
        "build_quality_repair_batch_recommended_action",
        lambda **_: {
            "action_id": "quality-repair::001-risk::write",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Quality batch would otherwise relaunch manuscript story repair.",
            "route_target": "write",
            "route_key_question": "Repair manuscript story.",
            "route_rationale": "Stale quality batch must not outrank closed work-unit lifecycle.",
            "requires_controller_decision": True,
            "controller_action_type": "run_quality_repair_batch",
            "next_work_unit": {
                "unit_id": "manuscript_story_repair",
                "lane": "write",
                "summary": "Repair the paper story around the current evidence and claim boundary.",
            },
            "work_unit_fingerprint": "publication-blockers::stale-write",
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "run-001",
            "reason": "controller_work_unit_evidence_adopted",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["reason"] == "publication_gate_recheck_required"
    assert request["route_target"] == "review"
    assert request["next_work_unit"]["unit_id"] == "publication_gate_recheck"
    assert request["controller_actions"] == [
        {
            "action_type": "run_gate_clearing_batch",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
