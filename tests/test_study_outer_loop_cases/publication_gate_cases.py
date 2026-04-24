from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_build_runtime_watch_outer_loop_tick_request_ignores_stale_task_intake_after_bundle_only_closeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-24T04:41:53+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-24T04:41:53+00:00",
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
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Human-review package is ready and only finalize-level cleanup remains.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "optional",
                    "summary": "Only optional submission-bundle cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only finalize-level bundle cleanup remains on the current paper line.",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "The paper itself is ready for human review and only finalize-level cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "当前稿件不能按已达投稿包里程碑直接收口；必须补做分层统计分析，"
            "并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        constraints=("本轮不得直接按外投收口。",),
        evidence_boundary=("统计扩展限于预设 subgroup / association analysis。",),
        first_cycle_outputs=("价格顾虑有/无分层的生物制剂使用结构比较表与统计检验结果。",),
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2099-04-24T23:59:59+00:00",
            "emitted_at": "2099-04-24T23:59:59+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is already closed and only finalize-level bundle cleanup remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
        },
    )
    gate_report = {
        "status": "clear",
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
        "paper_line_open_supplementary_count": 0,
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_current": True,
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        module.publication_gate_controller,
        "build_gate_state",
        lambda root: type("GateState", (), {"paper_root": study_root / "paper"})(),
    )
    monkeypatch.setattr(module.publication_gate_controller, "build_gate_report", lambda state: gate_report)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "build_gate_clearing_batch_recommended_action",
        lambda **_: None,
    )
    monkeypatch.setattr(
        module.quality_repair_batch,
        "build_quality_repair_batch_recommended_action",
        lambda **_: None,
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "run-001",
            "reason": "quest_already_running",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "finalize"
    assert request["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
def test_build_runtime_watch_outer_loop_tick_request_autoparks_without_runtime_escalation_ref(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
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
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Human-review package is ready and only bundle-stage cleanup remains.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "optional",
                    "summary": "Only optional submission-bundle cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical question is already publication-ready.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Clinical framing is stable.",
                    "reviewer_revision_advice": "Only minor bundle cleanup remains.",
                    "reviewer_next_round_focus": "Keep the clinician-facing framing consistent across surfaces.",
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence chain is already closed.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Evidence posture is stable.",
                    "reviewer_revision_advice": "Only refresh delivery surfaces if needed.",
                    "reviewer_next_round_focus": "Keep evidence references synchronized across package surfaces.",
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Contribution boundary is already explicit.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "Novelty framing is fixed.",
                    "reviewer_revision_advice": "Do not expand the claim boundary.",
                    "reviewer_next_round_focus": "Keep contribution wording aligned with the frozen charter.",
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "The human-facing current package is ready for review.",
                    "evidence_refs": [str(publication_eval_path)],
                    "reviewer_reason": "The review package is synchronized.",
                    "reviewer_revision_advice": "Only keep bundle surfaces aligned.",
                    "reviewer_next_round_focus": "Double-check package surface consistency before submission.",
                },
            },
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only finalize-level bundle cleanup remains on the current paper line.",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "The paper itself is ready for human review and only finalize-level cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-05T06:00:00+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is already closed and only bundle cleanup remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "run-001",
            "reason": "quest_already_running",
        },
    )

    assert request is not None
    assert request["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
def test_refresh_parked_submission_milestone_controller_decision_writes_parked_finalize_record(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-24T04:41:53+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-24T04:41:53+00:00",
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
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Human-review package is ready and only finalize-level cleanup remains.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "optional",
                    "summary": "Only optional submission-bundle cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only finalize-level bundle cleanup remains on the current paper line.",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "The paper itself is ready for human review and only finalize-level cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-24T04:49:03+00:00",
            "emitted_at": "2026-04-24T04:49:03+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is already closed and only finalize-level bundle cleanup remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
        },
    )

    result = module.refresh_parked_submission_milestone_controller_decision(
        profile=profile,
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "stopped",
            "reason": "quest_waiting_for_submission_metadata",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
        source="submission-minimal-post-materialization",
        recorded_at="2026-04-24T04:49:03+00:00",
    )

    assert result is not None
    assert result["status"] == "refreshed"
    assert result["decision_type"] == "continue_same_line"
    assert result["route_target"] == "finalize"
    payload = json.loads((study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8"))
    assert payload["decision_type"] == "continue_same_line"
    assert payload["route_target"] == "finalize"
    assert payload["requires_human_confirmation"] is False
    assert payload["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
def test_build_runtime_watch_outer_loop_tick_request_skips_autonomous_dispatch_for_parked_submission_milestone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-24T04:41:53+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-24T04:41:53+00:00",
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
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Human-review package is ready and only finalize-level cleanup remains.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "delivery",
                    "severity": "optional",
                    "summary": "Only optional submission-bundle cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only finalize-level bundle cleanup remains on the current paper line.",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "The paper itself is ready for human review and only finalize-level cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-24T04:49:03+00:00",
            "emitted_at": "2026-04-24T04:49:03+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is already closed and only finalize-level bundle cleanup remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_assessment": {
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human-review package is ready.",
                }
            },
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
        },
    )
    parked_status = {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "reason": "quest_waiting_for_submission_metadata",
        "runtime_escalation_ref": runtime_escalation_ref,
        "continuation_state": {
            "quest_status": "waiting_for_user",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "decision",
            "continuation_reason": "paper_bundle_submitted",
            "runtime_state_path": str(profile.runtime_root / "001-risk" / ".ds" / "runtime_state.json"),
        },
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    refreshed = module.refresh_parked_submission_milestone_controller_decision(
        profile=profile,
        study_root=study_root,
        status_payload=parked_status,
        source="submission-minimal-post-materialization",
        recorded_at="2026-04-24T04:49:03+00:00",
    )

    assert refreshed is not None
    monkeypatch.setattr(
        module,
        "read_publication_eval_latest",
        lambda **_: pytest.fail("parked submission milestone should not re-enter publication-eval autonomous dispatch"),
    )
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "resolve_profile_for_study_root",
        lambda root: pytest.fail("parked submission milestone should not resolve batch profiles"),
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload=parked_status,
    )

    assert request is None
def test_build_runtime_watch_outer_loop_tick_request_prefers_quality_review_loop_re_review(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-05T05:58:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "risk stratification external validation",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(study_root / "paper"),
                "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "partial",
                "summary": "Publication eval itself still reflects the pre-re-review state.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "important",
                    "summary": "A previous reporting gap existed.",
                    "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Older publication eval would still route back to write.",
                    "route_target": "write",
                    "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
                    "route_rationale": "This is the stale pre-re-review route.",
                    "evidence_refs": [str(publication_eval_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-04-05T06:00:00+00:00",
            "overall_verdict": "promising",
            "primary_claim_status": "partial",
            "stop_loss_pressure": "none",
            "verdict_summary": "Revision is complete and MAS should re-review.",
            "requires_controller_decision": True,
            "quality_review_loop": {
                "policy_id": "publication-critique.v1",
                "loop_id": "quality-review-loop::001-risk::2026-04-05T06:00:00+00:00",
                "closure_state": "quality_repair_required",
                "lane_id": "general_quality_repair",
                "current_phase": "re_review_required",
                "current_phase_label": "等待复评",
                "recommended_next_phase": "re_review",
                "recommended_next_phase_label": "发起复评",
                "active_plan_id": "quality-plan::001-risk::v1",
                "active_plan_execution_status": "completed",
                "blocking_issue_count": 1,
                "blocking_issues": ["外部验证结果与主结论是否真正闭环"],
                "next_review_focus": ["外部验证结果与主结论是否真正闭环"],
                "re_review_ready": True,
                "summary": "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。",
                "recommended_next_action": "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。",
            },
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "review"
    assert request["route_key_question"] == "外部验证结果与主结论是否真正闭环"
    assert request["route_rationale"] == "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。"
    assert request["reason"] == "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。"
    assert request["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime_relaunch_stopped",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
def test_build_runtime_watch_outer_loop_tick_request_handles_gate_clearing_batch_profile_resolution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    _write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "build_gate_clearing_batch_recommended_action",
        lambda **kwargs: None,
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "reason": "publication_quality_gap",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
def test_study_outer_loop_tick_dispatches_pause_runtime_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    charter_ref = _write_charter(study_root)
    publication_eval_ref = _write_publication_eval(study_root, quest_root)
    seen: dict[str, object] = {}

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "startup_boundary_not_ready_for_resume",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router.managed_runtime_transport,
        "pause_quest",
        lambda **kwargs: (
            seen.setdefault("pause_kwargs", kwargs),
            {"ok": True, "quest_id": "quest-001", "status": "paused", "snapshot": {"status": "paused"}},
        )[1],
    )

    result = module.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="continue_same_line",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "pause_runtime",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Pause the current runtime before further controller review.",
        source="test-source",
        recorded_at="2026-04-05T06:10:00+00:00",
    )

    assert seen["pause_kwargs"] == {
        "runtime_root": profile.med_deepscientist_runtime_root,
        "quest_id": "quest-001",
        "source": "test-source",
    }
    assert module.study_runtime_router.managed_runtime_transport is module.study_runtime_router.med_deepscientist_transport
    assert result["dispatch_status"] == "executed"
    assert result["executed_controller_action"]["action_type"] == "pause_runtime"
    assert result["executed_controller_action"]["result"]["status"] == "paused"
