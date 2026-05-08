from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _publication_eval_base_payload(
    *,
    study_root: Path,
    quest_root: Path,
) -> dict[str, object]:
    return {
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
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [
                str(study_root / "paper"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
            ],
            "ai_reviewer_required": False,
        },
    }


def test_refresh_parked_submission_milestone_allows_admin_metadata_handoff_gap(
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
            **_publication_eval_base_payload(study_root=study_root, quest_root=quest_root),
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Human-review package is ready and only administrative submission metadata remains.",
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
                    "summary": "Final bundle proofing should confirm citation/provenance surfaces.",
                    "evidence_refs": [str(publication_eval_path)],
                },
            ],
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only administrative metadata and final proofing remain.",
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
            "summary_id": "evaluation-summary::001-risk::2026-04-24T04:49:03+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is already closed and only administrative bundle cleanup remains.",
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
                "route_key_question": "Complete final bundle proofing and administrative submission metadata.",
                "summary": "Only administrative submission handoff cleanup remains.",
            },
            "quality_review_loop": {
                "closure_state": "bundle_only_remaining",
                "current_phase": "bundle_hardening",
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
            "quest_status": "active",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_status": "none",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            },
            "runtime_escalation_ref": runtime_escalation_ref,
        },
        source="submission-minimal-post-materialization",
        recorded_at="2026-04-24T04:49:03+00:00",
    )

    assert result is not None
    assert result["status"] == "refreshed"
    payload = json.loads((study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8"))
    assert payload["route_target"] == "finalize"
    assert payload["controller_actions"][0]["action_type"] == "stop_runtime"


def test_refresh_parked_submission_milestone_rejects_important_scientific_gap(
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
            **_publication_eval_base_payload(study_root=study_root, quest_root=quest_root),
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Human-review package is close, but a scientific evidence gap remains.",
                "stop_loss_pressure": "watch",
            },
            "gaps": [
                {
                    "gap_id": "external-validation-evidence-gap",
                    "gap_type": "evidence",
                    "severity": "important",
                    "summary": "External validation evidence is still incomplete.",
                    "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
                }
            ],
            "recommended_actions": [
                {
                    "action_id": "action-001",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Scientific evidence gap must remain a manuscript-body blocker.",
                    "route_target": "finalize",
                    "route_key_question": "Do not park while scientific evidence remains incomplete.",
                    "route_rationale": "A scientific evidence gap is still open.",
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
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "route_target": "finalize",
            },
            "quality_assessment": {"human_review_readiness": {"status": "ready"}},
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
    )

    assert result is None
