from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_build_domain_health_diagnostic_outer_loop_tick_request_stops_live_runtime_after_fast_lane_closeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
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
            "eval_id": "publication-eval::001-risk::quest-001::2099-04-28T00:32:47+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2099-04-28T00:32:47+00:00",
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
                "summary": "Bundle-stage blockers remain after manual foreground finishing.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_submission_minimal_authority",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::route_back_same_line::publication-blockers",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Route back to finalize to close submission-readiness gaps.",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "Route back to finalize to close submission-readiness gaps.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    task_payload = task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "用户已对当前投稿包给出新的审稿式反馈；这是 reviewer revision / manuscript revision，"
            "必须先把反馈拆成可审计 action matrix。"
        ),
        constraints=("不得手工 patch manuscript/current_package 投影作为最终修复。",),
        first_cycle_outputs=("review_matrix/action_plan mapping all user concerns to manuscript revisions",),
    )
    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "task_intake"
        / "manuscript_fast_lane_closeout_20260428T001900Z.json",
        {
            "schema_version": 1,
            "record_type": "manuscript_fast_lane_closeout",
            "surface_kind": "manuscript_fast_lane_closeout",
            "created_at": "2099-04-28T00:19:00Z",
            "source_task_id": task_payload["task_id"],
            "status": "completed",
            "completion_state": "foreground_fast_lane_completed",
            "execution_owner": "codex_foreground_under_mas_controller",
            "canonical_write_surface": "paper/",
            "projection_surface": "manuscript/current_package/",
            "auto_resume_policy": "do_not_resume_superseded_task_intake",
            "scope": {
                "existing_evidence_only": True,
                "canonical_paper_text_or_structure_only": True,
                "new_analysis_performed": False,
            },
            "validation": {
                "canonical_paper_writeback_complete": True,
                "export_sync_complete": True,
                "qc_complete": True,
                "package_consistency_checked": True,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2099-04-28T00:32:47+00:00",
            "emitted_at": "2099-04-28T00:32:47+00:00",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Scientific revision is closed; only downstream package handoff remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_review_loop": {
                "closure_state": "bundle_only_remaining",
                "current_phase": "bundle_stage_ready",
            },
        },
    )
    gate_report = {
        "generated_at": "2099-04-28T00:32:47+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
        "medical_publication_surface_status": "clear",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        _domain_health_diagnostic_tick_request_module().publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": study_root / "paper"})(),
    )
    monkeypatch.setattr(_domain_health_diagnostic_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "build_gate_clearing_batch_recommended_action",
        lambda **_: pytest.fail("fast lane closeout should suppress autonomous gate-clearing resume"),
    )
    monkeypatch.setattr(
        module.quality_repair_batch,
        "build_quality_repair_batch_recommended_action",
        lambda **_: pytest.fail("fast lane closeout should suppress autonomous quality-repair resume"),
    )

    request = module.build_domain_health_diagnostic_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "run-001",
            "reason": "quest_already_running",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "write"
    assert request["reason"] == (
        "Manuscript fast lane closeout supersedes the latest task intake; stop the live runtime and wait for explicit resume."
    )
    assert request["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_build_domain_health_diagnostic_outer_loop_tick_request_does_not_stop_when_fast_lane_closeout_has_blocked_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-05-03T16:10:00+00:00",
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-05-03T16:10:00+00:00",
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
                "summary": "Publication gate remains blocked after foreground fast-lane closeout.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "must_fix",
                    "summary": "medical_publication_surface_blocked",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::route_back_same_line::publication-blockers",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Route back to write to close reviewer-first publication-surface concerns.",
                    "route_target": "write",
                    "route_key_question": "Which reviewer-first publication-surface concern remains open?",
                    "route_rationale": "The publication gate is still blocked after foreground fast-lane closeout.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    task_payload = task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-dm-cvd-mortality-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "用户已对当前 CVD 风险预测投稿包给出新的审稿式反馈；这是 reviewer revision / manuscript revision，"
            "必须先把反馈拆成可审计 action matrix。"
        ),
        constraints=("不得手工 patch manuscript/current_package 投影作为最终修复。",),
        first_cycle_outputs=("review_matrix/action_plan mapping all user concerns to manuscript revisions",),
    )
    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "task_intake"
        / "manuscript_fast_lane_closeout_20260428T005000Z.json",
        {
            "schema_version": 1,
            "record_type": "manuscript_fast_lane_closeout",
            "surface_kind": "manuscript_fast_lane_closeout",
            "created_at": "2026-04-28T00:50:00Z",
            "source_task_id": task_payload["task_id"],
            "status": "completed",
            "completion_state": "foreground_fast_lane_completed",
            "execution_owner": "codex_foreground_under_mas_controller",
            "canonical_write_surface": "paper/",
            "projection_surface": "manuscript/current_package/",
            "auto_resume_policy": "do_not_resume_superseded_task_intake",
            "scope": {
                "existing_evidence_only": True,
                "canonical_paper_text_or_structure_only": True,
                "new_analysis_performed": False,
            },
            "validation": {
                "canonical_paper_writeback_complete": True,
                "export_sync_complete": True,
                "qc_complete": True,
                "package_consistency_checked": True,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-dm-cvd-mortality-risk::2026-05-03T16:10:00+00:00",
            "emitted_at": "2026-05-03T16:10:00+00:00",
            "quality_closure_truth": {
                "state": "review_required",
                "summary": "当前 publication_eval 只是机械投影；必须先由 AI reviewer 给出质量闭环判断。",
                "current_required_action": "return_to_ai_reviewer",
                "route_target": "publication_eval",
            },
            "quality_review_loop": {
                "closure_state": "review_required",
                "current_phase": "revision_required",
                "recommended_next_action": "先发起 AI reviewer 复评。",
            },
        },
    )
    gate_report = {
        "status": "blocked",
        "allow_write": False,
        "blockers": [
            "stale_submission_minimal_authority",
            "medical_publication_surface_blocked",
            "reviewer_first_concerns_unresolved",
            "claim_evidence_consistency_failed",
            "submission_hardening_incomplete",
        ],
        "current_required_action": "return_to_publishability_gate",
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
        "supervisor_phase": "publishability_gate_blocked",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        _domain_health_diagnostic_tick_request_module().publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": study_root / "paper"})(),
    )
    monkeypatch.setattr(_domain_health_diagnostic_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: gate_report)

    request = module.build_domain_health_diagnostic_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-dm-cvd-mortality-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "run-001",
            "reason": "quest_already_running",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["controller_actions"][0]["action_type"] != "stop_runtime"
    assert request["reason"] != (
        "Manuscript fast lane closeout supersedes the latest task intake; stop the live runtime and wait for explicit resume."
    )
