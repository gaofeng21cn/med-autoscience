from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_build_runtime_watch_outer_loop_tick_request_keeps_stopped_submission_milestone_parked(
    tmp_path: Path,
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
            "eval_id": "publication-eval::001-risk::quest-001::ai-reviewer::2026-05-04T12:22:30+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-05-04T12:22:30+00:00",
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
                "summary": "AI reviewer closed the milestone manuscript quality loop.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "admin-metadata-closeout",
                    "gap_type": "delivery",
                    "severity": "important",
                    "summary": (
                        "Author-confirmed title-page, declaration wording, and final submission metadata still "
                        "require external confirmation before actual submission-ready release."
                    ),
                    "evidence_refs": [str(study_root / "paper" / "review" / "review_ledger.json")],
                },
                {
                    "gap_id": "final-provenance-proof",
                    "gap_type": "reporting",
                    "severity": "optional",
                    "summary": "Final bundle proofing should confirm package provenance.",
                    "evidence_refs": [str(publication_eval_path)],
                },
            ],
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical question is already publication-ready.",
                    "evidence_refs": [str(publication_eval_path)],
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence chain is already closed.",
                    "evidence_refs": [str(publication_eval_path)],
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Contribution boundary is already explicit.",
                    "evidence_refs": [str(publication_eval_path)],
                },
                "medical_journal_prose_quality": {
                    "status": "ready",
                    "summary": "Medical journal prose is ready for human review.",
                    "evidence_refs": [str(publication_eval_path)],
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "The milestone current package is ready for human review.",
                    "evidence_refs": [str(publication_eval_path)],
                },
            },
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::ai-reviewer::milestone-package-handoff",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": (
                        "AI reviewer quality assessment supports milestone package handoff; remaining work is "
                        "final administrative metadata and bundle proofing, not manuscript-body repair."
                    ),
                    "route_target": "finalize",
                    "route_key_question": "Complete final bundle proofing and administrative submission metadata.",
                    "route_rationale": "Scientific claims and prose quality are ready for human review.",
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
            "summary_id": "evaluation-summary::001-risk::quest-001::2026-05-04T12:22:30+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is closed; only administrative bundle cleanup remains.",
                "current_required_action": "continue_bundle_stage",
                "route_target": "finalize",
            },
            "quality_review_loop": {
                "closure_state": "bundle_only_remaining",
                "current_phase": "bundle_hardening",
                "recommended_next_phase": "finalize",
            },
        },
    )

    request = module.build_runtime_watch_outer_loop_tick_request(
        study_root=study_root,
        status_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "stopped",
            "active_run_id": None,
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_liveness_status": "unknown",
            "runtime_escalation_ref": runtime_escalation_ref,
            "continuation_state": {
                "quest_status": "stopped",
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            },
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
