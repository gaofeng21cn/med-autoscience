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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
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
    monkeypatch.setattr(module.publication_gate_controller, "build_gate_report", lambda state: dict(gate_report))

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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-002"
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
    monkeypatch.setattr(module.publication_gate_controller, "build_gate_report", lambda state: dict(gate_report))

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
