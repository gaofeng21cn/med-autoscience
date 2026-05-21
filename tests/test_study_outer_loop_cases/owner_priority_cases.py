from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_runtime_watch_outer_loop_routes_startup_freshness_gate_before_stale_task_intake(
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
            "eval_id": "publication-eval::001-risk::quest-001::2026-05-05T10:11:17+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-05-05T10:11:17+00:00",
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
                "summary": "Publication gate is blocked by current package freshness and reviewer story issues.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-delivery",
                    "gap_type": "delivery",
                    "severity": "must_fix",
                    "summary": "stale_study_delivery_mirror",
                    "evidence_refs": [str(publication_eval_path)],
                },
                {
                    "gap_id": "gap-story",
                    "gap_type": "reporting",
                    "severity": "must_fix",
                    "summary": "reviewer_first_concerns_unresolved",
                    "evidence_refs": [str(publication_eval_path)],
                },
            ],
            "recommended_actions": [
                {
                    "action_id": "action-write",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Route back to write after startup freshness is resolved.",
                    "route_target": "write",
                    "route_key_question": "manuscript_story_repair: Repair the paper story around the current evidence and claim boundary.",
                    "route_rationale": "The reviewer-facing story needs repair.",
                    "evidence_refs": [str(publication_eval_path)],
                    "work_unit_fingerprint": "publication-blockers::dm002",
                    "next_work_unit": {
                        "unit_id": "manuscript_story_repair",
                        "lane": "write",
                        "summary": "Repair the paper story around the current evidence and claim boundary.",
                    },
                    "blocking_work_units": [
                        {
                            "unit_id": "manuscript_story_repair",
                            "lane": "write",
                            "summary": "Repair the paper story around the current evidence and claim boundary.",
                        },
                        {
                            "unit_id": "submission_minimal_refresh",
                            "lane": "finalize",
                            "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
                        },
                    ],
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
        task_intent="旧 reviewer revision intake 要求回到补充分析。",
        constraints=("不得绕过 publication gate。",),
        evidence_boundary=("只处理 gate 指名的具体 blocker。",),
        first_cycle_outputs=("paper/rebuttal/review_matrix.md and action_plan.md",),
    )
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "supervisor_phase": "publishability_gate_blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "medical_publication_surface_blocked",
            "reviewer_first_concerns_unresolved",
            "submission_hardening_incomplete",
            "submission_surface_qc_failure_present",
        ],
        "study_delivery_status": "stale_source_mismatch",
        "study_delivery_stale_reason": "delivery_manifest_source_mismatch",
        "submission_minimal_authority_status": "stale_source_missing",
        "medical_publication_surface_named_blockers": [
            "reviewer_first_concerns_unresolved",
            "submission_hardening_incomplete",
        ],
        "medical_publication_surface_route_back_recommendation": "return_to_write",
        "blocking_artifact_refs": [
            {
                "blocker": "stale_study_delivery_mirror",
                "artifact_path": str(study_root / "manuscript" / "delivery_manifest.json"),
                "artifact_role": "study_delivery_mirror",
                "stale_reason": "delivery_manifest_source_mismatch",
            },
            {
                "blocker": "reviewer_first_concerns_unresolved",
                "artifact_path": str(study_root / "paper" / "review" / "review_ledger.json"),
                "source_path": str(study_root / "paper" / "review" / "review_ledger.json"),
            },
        ],
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(_runtime_watch_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: dict(gate_report))

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "reason": "quest_marked_running_but_no_live_session",
            "continuation_reason": "current_package_freshness_required",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["controller_actions"] == [
        {
            "action_type": "run_gate_clearing_batch",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    assert request["route_target"] == "finalize"
    assert request["next_work_unit"]["unit_id"] in {"submission_minimal_refresh", "submission_delivery_sync_closure"}


def test_runtime_watch_outer_loop_routes_startup_freshness_gate_before_publication_eval_work_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution")
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    runtime_escalation_ref = _write_runtime_escalation_record(module, quest_root, study_root)
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": (
                "publication-eval::002-dm-china-us-mortality-attribution::quest-002::"
                "2026-05-05T10:53:41+00:00"
            ),
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-05T10:53:41+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::002-dm-china-us-mortality-attribution::v1",
                "publication_objective": "mortality attribution manuscript",
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
                "summary": "Publication eval recommends an analysis work-unit, but startup freshness is still required.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "gap-analysis",
                    "gap_type": "evidence",
                    "severity": "must_fix",
                    "summary": "claim_evidence_consistency_failed",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-analysis",
                    "action_type": "bounded_analysis",
                    "priority": "now",
                    "reason": "Repair claim-evidence and story blockers.",
                    "route_target": "analysis-campaign",
                    "route_key_question": (
                        "analysis_claim_evidence_repair: Repair claim-evidence, story, figure, "
                        "and results traceability blockers."
                    ),
                    "route_rationale": "The current publication eval still has analysis blockers.",
                    "evidence_refs": [str(publication_eval_path)],
                    "work_unit_fingerprint": "publication-blockers::analysis",
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
                        },
                        {
                            "unit_id": "submission_minimal_refresh",
                            "lane": "finalize",
                            "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
                        },
                    ],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    gate_report = {
        "status": "blocked",
        "current_required_action": "complete_bundle_stage",
        "supervisor_phase": "publishability_gate_blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "submission_surface_qc_failure_present",
        ],
        "study_delivery_status": "stale_source_mismatch",
        "study_delivery_stale_reason": "delivery_manifest_source_mismatch",
        "submission_minimal_authority_status": "stale_source_missing",
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "blocking_artifact_refs": [
            {
                "blocker": "stale_submission_minimal_authority",
                "artifact_path": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
                "artifact_role": "submission_minimal",
            }
        ],
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(_runtime_watch_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: dict(gate_report))

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "reason": "quest_marked_running_but_no_live_session",
            "continuation_state": {
                "continuation_reason": "current_package_freshness_required",
                "continuation_policy": "auto",
            },
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["controller_actions"] == [
        {
            "action_type": "run_gate_clearing_batch",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    assert request["route_target"] == "finalize"
    assert request["next_work_unit"]["unit_id"] == "submission_minimal_refresh"


def test_runtime_watch_outer_loop_routes_bundle_stage_ready_before_stale_task_intake(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution")
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    runtime_escalation_ref = _write_runtime_escalation_record(
        module,
        quest_root,
        study_root,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-002",
    )
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": (
                "publication-eval::002-dm-china-us-mortality-attribution::quest-002::"
                "2026-05-12T13:24:00+00:00"
            ),
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-12T13:24:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::002-dm-china-us-mortality-attribution::v1",
                "publication_objective": "mortality attribution manuscript",
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
                "summary": "Gate replay is clear; bundle-stage authority sync is now the critical path.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-submission-authority",
                    "gap_type": "delivery",
                    "severity": "important",
                    "summary": "submission_authority_sync_closure",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::route_back_same_line::submission-authority",
                    "action_type": "route_back_same_line",
                    "priority": "now",
                    "reason": "Continue bundle-stage submission authority sync.",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "The publication gate is clear and bundle-stage authority sync is current critical path.",
                    "evidence_refs": [str(publication_eval_path)],
                    "work_unit_fingerprint": "publication-blockers::submission-authority",
                    "next_work_unit": {
                        "unit_id": "submission_authority_sync_closure",
                        "lane": "finalize",
                        "summary": "Regenerate submission authority signatures, then replay the publication gate.",
                    },
                    "blocking_work_units": [
                        {
                            "unit_id": "submission_authority_sync_closure",
                            "lane": "finalize",
                            "summary": "Regenerate submission authority signatures, then replay the publication gate.",
                        }
                    ],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="旧 reviewer revision intake 要求回到补充统计分析；这是 gate replay clear 之前的旧任务。",
        constraints=("不得绕过 publication gate。",),
        evidence_boundary=("统计扩展限于旧 task intake 指定范围。",),
        first_cycle_outputs=("完成旧分层统计分析并写回 manuscript。",),
    )
    gate_report = {
        "generated_at": "2026-05-12T13:24:00+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
        "medical_publication_surface_status": "clear",
        "submission_minimal_authority_status": "current",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(_runtime_watch_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: dict(gate_report))
    monkeypatch.setattr(
        module.gate_clearing_batch,
        "build_gate_clearing_batch_recommended_action",
        lambda **_: pytest.fail("clear bundle-stage gate should use publication eval route, not replay gate-clearing"),
    )
    monkeypatch.setattr(
        module.quality_repair_batch,
        "build_quality_repair_batch_recommended_action",
        lambda **_: pytest.fail("clear bundle-stage gate should not dispatch quality repair"),
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "mas-run-002",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "finalize"
    assert request["next_work_unit"]["unit_id"] == "submission_authority_sync_closure"
    assert request["work_unit_fingerprint"] == "domain-transition::bundle_stage_finalize::submission_authority_sync_closure"
    assert request["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_runtime_watch_outer_loop_routes_bundle_ready_eval_review_unit_to_finalize_work_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution")
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    runtime_escalation_ref = _write_runtime_escalation_record(
        module,
        quest_root,
        study_root,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-002",
    )
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": (
                "publication-eval::002-dm-china-us-mortality-attribution::quest-002::"
                "2026-05-13T16:15:57+00:00"
            ),
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-13T16:15:57+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::002-dm-china-us-mortality-attribution::v1",
                "publication_objective": "mortality attribution manuscript",
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
                "summary": "bundle-stage work is unlocked and can proceed on the critical path",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-001",
                    "gap_type": "reporting",
                    "severity": "optional",
                    "summary": "bundle-stage work is unlocked and can proceed on the critical path",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::continue_same_line::review",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "bundle-stage work is unlocked and can proceed on the critical path",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "bundle-stage work is unlocked and can proceed on the critical path",
                    "evidence_refs": [str(publication_eval_path)],
                    "work_unit_fingerprint": "publication-blockers::review",
                    "next_work_unit": {
                        "unit_id": "publication_gate_blocker_review",
                        "lane": "review",
                        "summary": "Review the current publication gate blockers and select the narrowest repair unit.",
                    },
                    "blocking_work_units": [
                        {
                            "unit_id": "publication_gate_blocker_review",
                            "lane": "review",
                            "summary": "Review the current publication gate blockers and select the narrowest repair unit.",
                        }
                    ],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="用户已要求作为 reviewer_revision 重新激活同一论文线，必须补充分析并重写 canonical paper source。",
        constraints=("完成前维持 audit preview only / not submission-ready 判断。",),
        evidence_boundary=("新增计算只限于验证或呈现已有 claim 所必需的敏感性边界。",),
        trusted_inputs=("用户审稿式反馈要求重开同一论文线。",),
        first_cycle_outputs=(
            "paper/rebuttal/review_matrix.md and action_plan.md covering all feedback items.",
            "revised canonical manuscript source with narrowed clinical claims.",
        ),
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::002-dm::2026-05-13T16:15:57+00:00",
            "emitted_at": "2026-05-13T16:15:57+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is already closed and only finalize-level bundle cleanup remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_assessment": {"human_review_readiness": {"status": "ready"}},
            "quality_execution_lane": {
                "lane_id": "submission_hardening",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "summary": "Only finalize-level submission hardening remains.",
            },
        },
    )
    gate_report = {
        "generated_at": "2026-05-13T16:28:13+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
        "medical_publication_surface_status": "clear",
        "study_delivery_status": "current",
        "submission_minimal_authority_status": "current",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(_runtime_watch_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: dict(gate_report))
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
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "mas-run-002",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "finalize"
    assert request["next_work_unit"] is None
    assert request["work_unit_fingerprint"] is None
    assert request["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]


def test_runtime_watch_outer_loop_routes_bundle_blocked_eval_review_unit_to_finalize_work_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-dpcc-primary-care-phenotype-treatment-gap")
    quest_root = profile.managed_runtime_home / "quests" / "quest-003"
    runtime_escalation_ref = _write_runtime_escalation_record(
        module,
        quest_root,
        study_root,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-003",
    )
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::quest-003::latest",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "quest-003",
            "emitted_at": "2026-05-13T22:45:40+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::003-dpcc-primary-care-phenotype-treatment-gap::v1",
                "publication_objective": "primary care treatment gap manuscript",
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
                "summary": "bundle-stage work is unlocked and can proceed on the critical path",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-submission-authority",
                    "gap_type": "delivery",
                    "severity": "important",
                    "summary": "stale_submission_minimal_authority",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::continue_same_line::review",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "bundle-stage work is unlocked and can proceed on the critical path",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "bundle-stage work is unlocked and can proceed on the critical path",
                    "evidence_refs": [str(publication_eval_path)],
                    "work_unit_fingerprint": "publication-blockers::review",
                    "next_work_unit": {
                        "unit_id": "publication_gate_blocker_review",
                        "lane": "review",
                        "summary": "Review the current publication gate blockers and select the narrowest repair unit.",
                    },
                    "blocking_work_units": [
                        {
                            "unit_id": "publication_gate_blocker_review",
                            "lane": "review",
                            "summary": "Review the current publication gate blockers and select the narrowest repair unit.",
                        }
                    ],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        study_root=study_root,
        entry_mode="full_research",
        task_intent="旧 manuscript revision work unit。",
        constraints=("不得绕过 publication gate。",),
        first_cycle_outputs=("revised canonical manuscript source",),
    )
    gate_report = {
        "generated_at": "2026-05-13T22:45:40+00:00",
        "status": "blocked",
        "allow_write": False,
        "blockers": ["stale_submission_minimal_authority"],
        "current_required_action": "complete_bundle_stage",
        "supervisor_phase": "bundle_stage_blocked",
        "study_delivery_status": "current",
        "submission_minimal_authority_status": "stale_source_changed",
        "submission_minimal_evaluated_source_signature": "source::new",
        "submission_minimal_authority_source_signature": "source::old",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(_runtime_watch_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: dict(gate_report))
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
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "quest-003",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "mas-run-003",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "current_required_action": "continue_bundle_stage",
                "publication_gate_allows_direct_write": True,
            },
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "finalize"
    assert request["next_work_unit"]["unit_id"] == "submission_authority_sync_closure"
    assert request["work_unit_fingerprint"] != "publication-blockers::review"


def test_runtime_watch_outer_loop_keeps_current_write_task_intake_before_clear_bundle_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_charter(study_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-05-12T14:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-05-12T14:00:00+00:00",
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
                "summary": "Only bundle-stage cleanup remains.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "gap-bundle",
                    "gap_type": "delivery",
                    "severity": "optional",
                    "summary": "Only optional submission-bundle cleanup remains.",
                    "evidence_refs": [str(publication_eval_path)],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::continue-finalize",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only finalize-level bundle cleanup remains on the current paper line.",
                    "route_target": "finalize",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "route_rationale": "The publication gate is clear and only finalize-level cleanup remains.",
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
            "Revise the manuscript after human reviewer feedback: unify manuscript.docx and paper.pdf, "
            "remove draft/internal wording, strengthen endpoint definitions, and align figure/table numbering."
        ),
        constraints=("Keep the paper positioned as a single-center internally validated clinical risk stratification tool.",),
        trusted_inputs=("Human reviewer feedback supplied in Codex thread.",),
        first_cycle_outputs=(),
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": "evaluation-summary::001-risk::2026-05-12T14:01:00+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "quality_repair_required",
                "summary": "Latest reviewer feedback reopens the same manuscript line.",
                "current_required_action": "continue_write_stage",
                "route_target": "write",
            },
        },
    )
    gate_report = {
        "generated_at": "2026-05-12T14:00:00+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
    }
    monkeypatch.setattr(module.gate_clearing_batch, "resolve_profile_for_study_root", lambda root: profile)
    monkeypatch.setattr(_runtime_watch_tick_request_module().publication_gate_controller, "build_gate_report", lambda state: dict(gate_report))

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "active_run_id": "mas-run-001",
            "reason": "quest_already_running",
        },
    )

    assert request is not None
    assert request["decision_type"] == "continue_same_line"
    assert request["route_target"] == "write"
    assert request["controller_actions"] == [
        {
            "action_type": "ensure_study_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
