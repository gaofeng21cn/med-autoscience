from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_routes_ai_reviewer_package_freshness_mismatch_to_artifact_owner(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    current_eval_id = "publication-eval::dm002::current-ai-reviewer"
    stale_eval_id = "publication-eval::dm002::stale-package"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": current_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "recommended_actions": [
            {
                "action_type": "continue_same_line",
                "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck::continue_bundle_stage",
                "next_work_unit": {
                    "unit_id": "bundle_stage_continuation",
                    "lane": "controller",
                    "summary": "Continue downstream bundle-stage handling after AI reviewer recheck.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {
            "schema_version": 1,
            "status": "fresh",
            "source_eval_id": stale_eval_id,
            "current_package_root": str(study_root / "manuscript" / "current_package"),
            "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "schema_version": 1,
            "study_id": study_id,
            "generated_at": "2026-05-17T09:08:45+00:00",
            "executions": [
                {
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_workflow_failed",
                    "error": "current_package_freshness_source_eval_id_mismatch",
                    "next_owner": "ai_reviewer",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {
            "schema_version": 1,
            "decision_id": "return-to-ai-reviewer",
            "study_id": study_id,
            "quest_id": quest_id,
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "route_target": "review",
            "work_unit_fingerprint": "domain-transition::ai_reviewer_re_eval::ai_reviewer_recheck",
            "next_work_unit": {
                "unit_id": "ai_reviewer_recheck",
                "lane": "review",
                "summary": "Return current manuscript and evidence refs to AI reviewer.",
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "waiting_for_user",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "controller_action": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "next_work_unit": {"unit_id": "ai_reviewer_recheck"},
        },
        "publication_eval": publication_eval,
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-ai-reviewer",
            "source_signature": "truth-source-ai-reviewer",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_ready",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "study_truth_snapshot": status_payload["study_truth_snapshot"],
    }
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["current_package_freshness_required"]
    action = study["action_queue"][0]
    assert action["owner"] == "artifact_os"
    assert action["source_blocked_reason"] == "ai_reviewer_workflow_failed"
    assert action["source_error"] == "current_package_freshness_source_eval_id_mismatch"
    assert action["current_package_freshness"]["source_eval_id"] == stale_eval_id
    assert action["current_package_freshness"]["expected_source_eval_id"] == current_eval_id
    assert study["why_not_applied"] == "current_package_freshness_required"
    assert study["blocked_reason"] == "current_package_freshness_required"
    assert study["next_owner"] == "artifact_os"
    assert study["owner_route"]["allowed_actions"] == ["current_package_freshness_required"]
