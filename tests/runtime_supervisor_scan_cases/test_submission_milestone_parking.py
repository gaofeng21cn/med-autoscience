from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ready_quality_dimension(ref: Path) -> dict[str, object]:
    return {
        "status": "ready",
        "summary": "Ready for milestone human review.",
        "evidence_refs": [str(ref)],
    }


def test_supervisor_scan_parks_submission_milestone_instead_of_platform_repair(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")
    quest_root = profile.runtime_root / "quest-nf"
    runtime_escalation_ref = {
        "record_id": "runtime-escalation::003-endocrine-burden-followup::quest-nf::stale-runtime",
        "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
        "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
    }
    _write_json(
        Path(runtime_escalation_ref["artifact_path"]),
        {
            "schema_version": 1,
            "record_id": runtime_escalation_ref["record_id"],
            "study_id": "003-endocrine-burden-followup",
            "quest_id": "quest-nf",
            "emitted_at": "2026-05-04T12:22:30+00:00",
            "trigger": {
                "trigger_id": "runtime_recovery_retry_budget_exhausted",
                "source": "runtime_supervisor_scan",
            },
            "scope": "quest",
            "severity": "quest",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "recommended_actions": ["controller_review_required"],
            "evidence_refs": [str(study_root / "artifacts" / "runtime" / "last_launch_report.json")],
            "runtime_context_refs": {
                "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
            "summary_ref": runtime_escalation_ref["summary_ref"],
            "artifact_path": runtime_escalation_ref["artifact_path"],
        },
    )
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    _write_json(
        runtime_state_path,
        {
            "status": "active",
            "quest_id": "quest-nf",
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "last_controller_decision_authorization": {
                "decision_id": "old-finalize",
                "route_target": "finalize",
                "work_unit_id": "Complete final bundle proofing and administrative metadata",
                "controller_actions": ["ensure_study_runtime"],
                "active_run_id": "run-stale",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "003-endocrine-burden-followup",
            "quest_id": "quest-nf",
            "emitted_at": "2026-05-04T12:22:30+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::003-endocrine-burden-followup::v1",
                "publication_objective": "Deliver a manuscript-safe submission package.",
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
            "eval_id": "publication-eval::nf003::ai-reviewer",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": [str(study_root / "paper")],
                "ai_reviewer_required": False,
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "Scientific claims are supported; only final administrative metadata remains.",
                "stop_loss_pressure": "none",
            },
            "quality_assessment": {
                "clinical_significance": _ready_quality_dimension(study_root / "paper"),
                "evidence_strength": _ready_quality_dimension(quest_root / "artifacts" / "results" / "main_result.json"),
                "novelty_positioning": _ready_quality_dimension(study_root / "paper"),
                "medical_journal_prose_quality": _ready_quality_dimension(study_root / "paper"),
                "human_review_readiness": _ready_quality_dimension(
                    study_root / "paper" / "submission_minimal" / "submission_manifest.json"
                ),
            },
            "recommended_actions": [
                {
                    "action_id": "publication-eval-action::milestone-package-handoff",
                    "action_type": "continue_same_line",
                    "priority": "now",
                    "requires_controller_decision": True,
                    "route_target": "finalize",
                    "route_key_question": "Complete final bundle proofing and administrative submission metadata.",
                    "route_rationale": "Scientific claims and prose quality are ready for human review.",
                    "reason": "AI reviewer quality assessment supports milestone package handoff.",
                    "evidence_refs": [str(study_root / "paper")],
                }
            ],
            "gaps": [
                {
                    "gap_id": "admin-metadata-closeout",
                    "gap_type": "delivery",
                    "severity": "important",
                    "summary": "Author-confirmed title-page, declaration wording, and final submission metadata remain.",
                    "evidence_refs": [str(study_root / "paper")],
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json",
        {
            "schema_version": 1,
            "quality_closure_truth": {
                "state": "bundle_only_remaining",
                "route_target": "finalize",
                "summary": "Core scientific quality is closed; only bundle/admin closeout remains.",
            },
            "quality_execution_lane": {
                "route_target": "finalize",
                "route_key_question": "Complete final bundle proofing and administrative submission metadata.",
            },
            "quality_assessment": {"human_review_readiness": {"status": "ready"}},
        },
    )

    class FakeBackend:
        BACKEND_ID = "hermes"

        def stop_quest(self, *, runtime_root: Path | None = None, quest_id: str, source: str, **_: object) -> dict[str, object]:
            assert runtime_root == profile.managed_runtime_home
            runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
            runtime_state.update(
                {
                    "status": "stopped",
                    "stop_reason": f"controller_stop:{source}",
                    "active_run_id": None,
                    "worker_running": False,
                    "continuation_policy": "wait_for_user_or_resume",
                    "continuation_reason": "submission_milestone_parked",
                }
            )
            _write_json(runtime_state_path, runtime_state)
            return {"ok": True, "status": "stopped", "quest_id": quest_id, "source": source}

    monkeypatch.setattr(
        module.study_runtime_router,
        "_managed_runtime_backend_for_execution",
        lambda *_args, **_kwargs: FakeBackend(),
    )

    def fake_runtime_status(**_: object) -> dict[str, object]:
        runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
        active = runtime_state["status"] != "stopped"
        return {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_root": str(quest_root),
            "quest_status": runtime_state["status"],
            "reason": "runtime_recovery_retry_budget_exhausted" if active else "quest_waiting_for_submission_metadata",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {"status": "not_live", "worker_running": False, "active_run_id": None},
            },
            "continuation_state": {
                "quest_status": runtime_state["status"],
                "active_run_id": None,
                "continuation_policy": "auto" if active else "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending" if active else "submission_milestone_parked",
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated" if active else "idle",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"] if active else [],
            },
            "runtime_escalation_ref": runtime_escalation_ref,
        }

    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", fake_runtime_status)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "paper_stage": "bundle_stage_ready",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "supervision": {"active_run_id": None, "health_status": "recovering"},
        },
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    controller_decision = json.loads(
        (study_root / "artifacts" / "controller_decisions" / "latest.json").read_text(encoding="utf-8")
    )
    runtime_state = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    lifecycle = json.loads(
        (study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json").read_text(encoding="utf-8")
    )
    assert study["submission_milestone_parked_refresh"]["dispatch_status"] == "applied"
    assert study["submission_milestone_parked_refresh"]["reason"] == "submission_milestone_parked"
    assert study["submission_milestone_parked_refresh"]["controller_decision"]["status"] == "refreshed"
    assert study["submission_milestone_parked_refresh"]["stop_result"]["status"] == "stopped"
    assert study["ai_repair_lifecycle"]["state"] == "parked"
    assert study["ai_repair_lifecycle"]["external_supervisor_required"] is False
    assert lifecycle["state"] == "parked"
    assert lifecycle["external_supervisor_required"] is False
    assert lifecycle["blocked_reason"] is None
    assert study["action_queue"] == []
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["external_supervisor_required"] is False
    assert controller_decision["controller_actions"] == [
        {
            "action_type": "stop_runtime",
            "payload_ref": str((study_root / "artifacts" / "controller_decisions" / "latest.json").resolve()),
        }
    ]
    assert "Submission-package milestone remains parked" in controller_decision["reason"]
    assert runtime_state["status"] == "stopped"
    assert runtime_state["continuation_policy"] == "wait_for_user_or_resume"
    assert study["paper_package_mutated"] is False
