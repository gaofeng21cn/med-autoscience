from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_keeps_upstream_quality_repair_owned_by_mas_controller_when_resume_reports_package_freshness(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = "quest-dm002"
    work_unit_fingerprint = "publication-blockers::497d1260db522f01"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": "publication-eval::dm002::current",
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "route_back_same_line",
                "work_unit_fingerprint": work_unit_fingerprint,
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence and bounded analysis issues before delivery freshness.",
                },
                "specificity_targets": [
                    {
                        "target_kind": "claim",
                        "target_id": "primary_claim",
                        "source_path": str(study_root / "paper" / "claim_evidence_map.json"),
                    }
                ],
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "current-analysis-claim-evidence-repair",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "ensure_study_runtime"}],
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": work_unit_fingerprint,
            "next_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence and bounded analysis issues before delivery freshness.",
            },
        },
    )
    _write_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "status": "active",
            "quest_id": quest_id,
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "same_fingerprint_auto_turn_count": 4,
        },
    )

    def fake_ensure_study_runtime(**_: object) -> dict[str, object]:
        runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
        authorization = runtime_state["last_controller_decision_authorization"]
        assert authorization["decision_id"] == "current-analysis-claim-evidence-repair"
        assert authorization["work_unit_id"] == "analysis_claim_evidence_repair"
        return {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_status": "active",
            "decision": "blocked",
            "reason": "resume_request_failed",
            "resume_postcondition": {
                "effective": False,
                "failure_mode": "no_live_run_started",
                "blocked_reason": "current_package_freshness_required",
                "terminal_reason": "current_package_freshness_required",
                "terminal_source": "controller_work_unit_authorization",
            },
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
        }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure_study_runtime)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "quest_status": "active",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_liveness_audit": {
                "active_run_id": None,
                "runtime_audit": {"worker_running": False, "active_run_id": None},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": publication_eval,
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            "publication_supervisor_state": {"bundle_tasks_downstream_only": True},
            "supervision": {"active_run_id": None, "health_status": "recovering"},
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    action_types = [item["action_type"] for item in study["action_queue"]]
    assert study["runtime_platform_repair_apply"]["dispatch_status"] == "blocked"
    assert study["runtime_platform_repair_apply"]["reason"] == "runtime_controller_redrive_required"
    assert study["runtime_platform_repair_apply"]["current_controller_authorization_written"] is True
    assert action_types == ["runtime_platform_repair"]
    assert "current_package_freshness_required" not in action_types
    assert study["ai_repair_lifecycle"]["blocked_reason"] == "runtime_controller_redrive_required"
    assert study["ai_repair_lifecycle"]["next_owner"] == "mas_controller"
    assert study["ai_repair_lifecycle"]["external_supervisor_required"] is False
    assert study["blocked_reason"] == "runtime_controller_redrive_required"
    assert study["next_owner"] == "mas_controller"
    assert study["owner_route"]["next_owner"] == "mas_controller"
    assert study["owner_route"]["allowed_actions"] == ["runtime_platform_repair"]
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False
