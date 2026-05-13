from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _ready_repair_payload(
    *,
    study_id: str,
    quest_id: str,
    action_type: str = "controller_repair",
    repair_kind: str = "bounded_work_unit_redrive",
    owner: str = "mas_controller",
    risk: str = "medium",
    auto_apply_allowed: bool = True,
) -> dict[str, object]:
    return {
        "surface": "autonomy_repair_orchestration",
        "schema_version": 1,
        "state": "ready_for_repair",
        "study_id": study_id,
        "quest_id": quest_id,
        "action_count": 1,
        "actions": [
            {
                "action_type": action_type,
                "repair_kind": repair_kind,
                "owner": owner,
                "risk": risk,
                "auto_apply_allowed": auto_apply_allowed,
            }
        ],
        "quality_gate_relaxation_allowed": False,
    }


def _runtime_recovery_status(
    *,
    study_root: Path,
    quest_root: Path,
    study_id: str,
    quest_id: str,
    decision: str = "resume",
    supervisor_only: bool = False,
    repair_authorized: bool = True,
) -> dict[str, object]:
    payload = {
        **make_study_runtime_status_payload(
            study_id=study_id,
            decision=decision,
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "running",
        "runtime_health_snapshot": {
            "canonical_runtime_action": "recover_runtime",
            "attempt_state": "recovering",
            "blocking_reasons": ["quest_marked_running_but_no_live_session"],
        },
        "control_plane_snapshot": {
            "dispatch_gate": {"state": "open", "dispatch_allowed": True, "blocking_reasons": []},
            "route_authorization": {"runtime_recovery_allowed": True},
            "blocking_reasons": [],
        },
    }
    if repair_authorized:
        payload["controller_repair_authorization_ref"] = {
            "surface": "controller_repair_authorization",
            "authorized": True,
            "action": "runtime_recovery",
            "work_unit_id": "runtime_recovery",
            "controller_action_type": "ensure_study_runtime",
            "control_surface": "runtime_watch",
        }
    if supervisor_only:
        payload["execution_owner_guard"] = {"supervisor_only": True, "active_run_id": "run-live"}
        payload["control_plane_snapshot"]["blocking_reasons"] = ["execution_owner_guard.supervisor_only"]
    return payload


def _live_controller_work_unit_status(
    *,
    study_root: Path,
    quest_root: Path,
    study_id: str,
    quest_id: str,
    repair_kind: str = "analysis_claim_evidence_redrive",
) -> dict[str, object]:
    active_run_id = f"run-{study_id}"
    work_unit_id = (
        "analysis_claim_evidence_repair"
        if repair_kind == "analysis_claim_evidence_redrive"
        else "submission_authority_sync_closure"
    )
    route_target = "analysis-campaign" if repair_kind == "analysis_claim_evidence_redrive" else "controller"
    controller_actions = ["run_quality_repair_batch"] if repair_kind == "analysis_claim_evidence_redrive" else ["ensure_study_runtime"]
    return {
        **make_study_runtime_status_payload(
            study_id=study_id,
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "running",
        "active_run_id": active_run_id,
        "execution_owner_guard": {"supervisor_only": True, "active_run_id": active_run_id},
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": active_run_id,
            "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": active_run_id},
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "continue_supervising_runtime",
            "attempt_state": "live",
            "retry_budget_remaining": 3,
            "blocking_reasons": [],
            "worker_liveness_state": {
                "state": "live",
                "worker_running": True,
                "active_run_id": active_run_id,
            },
        },
        "control_plane_snapshot": {
            "dispatch_gate": {
                "state": "open",
                "dispatch_allowed": True,
                "blocking_reasons": ["execution_owner_guard.supervisor_only"],
            },
            "blocking_reasons": ["execution_owner_guard.supervisor_only"],
        },
        "last_controller_decision_authorization": {
            "source": "runtime_watch",
            "delivery_mode": "managed_runtime_chat",
            "active_run_id": active_run_id,
            "route_target": route_target,
            "work_unit_id": work_unit_id,
            "controller_actions": controller_actions,
            "next_work_unit": {
                "unit_id": work_unit_id,
                "lane": route_target,
                "summary": "MAS controller-owned live work unit.",
            },
        },
    }


def _write_bundle_only_publication_surfaces(*, study_root: Path, quest_root: Path, study_id: str, quest_id: str) -> None:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    dump_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": f"publication-eval::{study_id}::{quest_id}::ai-reviewer::2026-05-04T12:22:30+00:00",
            "study_id": study_id,
            "quest_id": quest_id,
            "emitted_at": "2026-05-04T12:22:30+00:00",
            "evaluation_scope": "publication",
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "AI reviewer supports milestone package handoff.",
                "stop_loss_pressure": "none",
            },
            "gaps": [
                {
                    "gap_id": "admin-metadata-closeout",
                    "gap_type": "delivery",
                    "severity": "important",
                    "summary": "Author-confirmed title-page, declaration wording, and final submission metadata remain.",
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
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "The human-facing current package is ready for review.",
                    "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
                }
            },
            "recommended_actions": [
                {
                    "action_id": "milestone-package-handoff",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "reason": "Only administrative metadata and bundle proofing remain.",
                    "route_target": "finalize",
                    "route_key_question": "Complete final bundle proofing and administrative submission metadata.",
                    "route_rationale": "Scientific claims and prose quality are ready for human review.",
                    "requires_controller_decision": True,
                }
            ],
        },
    )
    dump_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "summary_id": f"evaluation-summary::{study_id}::{quest_id}::2026-05-04T12:22:30+00:00",
            "overall_verdict": "promising",
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "summary": "Core scientific quality is closed; only bundle/admin handoff remains.",
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

__all__ = [name for name in globals() if not name.startswith("__")]
