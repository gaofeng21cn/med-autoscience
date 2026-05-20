from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_routes_stale_ai_reviewer_eval_before_publication_gate_recheck(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_route_scan")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval = {
        "schema_version": 1,
        "eval_id": f"publication-eval::{study_id}::{study_id}::2026-05-19T21:46:11+00:00",
        "study_id": study_id,
        "quest_id": study_id,
        "emitted_at": "2026-05-19T21:46:11+00:00",
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "ready"}},
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "schema_version": 1,
            "task_id": f"study-task::{study_id}::20260520T163325Z",
            "study_id": study_id,
            "quest_id": study_id,
            "emitted_at": "2026-05-20T16:33:25+00:00",
            "task_intake_kind": "reviewer_revision",
            "task_intent": (
                "Reviewer revision: evaluate whether the current manuscript now meets high-quality "
                "medical journal prose standards."
            ),
        },
    )

    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("stale AI reviewer authority must not redrive publication gate recheck")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fail_if_called)
    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_id": study_id,
                "quest_root": str(quest_root),
                "quest_status": "running",
                "decision": "resume",
                "reason": "domain_transition_publication_gate_blocker",
                "active_run_id": "run-stale-ai-reviewer",
                "runtime_liveness_audit": {
                    "status": "live",
                    "active_run_id": "run-stale-ai-reviewer",
                    "runtime_audit": {
                        "worker_running": True,
                        "active_run_id": "run-stale-ai-reviewer",
                    },
                },
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "recover_runtime",
                    "attempt_state": "recovering",
                    "retry_budget_remaining": 3,
                    "blocking_reasons": ["live_worker_meaningful_artifact_delta_timeout"],
                },
                "controller_work_unit_next_route": {
                    "recommended_next_route": "return_to_publication_gate_recheck",
                    "owner": "publication_gate",
                    "quality_gate_relaxation_allowed": False,
                    "runtime_relaunch_required": False,
                },
                "domain_transition": {
                    "decision_type": "publication_gate_blocker",
                    "owner": "publication_gate",
                    "controller_action": "run_gate_clearing_batch",
                    "next_work_unit": {"unit_id": "publication_gate_recheck", "lane": "review"},
                },
                "publication_eval": publication_eval,
                "study_truth_snapshot": {
                    "truth_epoch": "truth-epoch-stale-ai-reviewer",
                    "source_signature": "truth-source-stale-ai-reviewer",
                },
            },
            {
                "study_id": study_id,
                "quest_id": study_id,
                "current_stage": "publication_supervision",
                "paper_stage": "review",
                "supervision": {"active_run_id": "run-stale-ai-reviewer", "health_status": "live"},
                "ai_repair_lifecycle": {
                    "state": "blocked",
                    "blocked_reason": "publication_gate_recheck_required",
                    "next_owner": "publication_gate",
                    "external_supervisor_required": False,
                },
                "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
            },
            study_id,
            publication_eval,
        ),
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        apply_safe_actions=True,
        apply_runtime_platform_repair=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    action = study["action_queue"][0]
    assert action["reason"] == "ai_reviewer_assessment_stale_after_reviewer_revision"
    assert action["owner"] == "ai_reviewer"
    assert action["required_output_surface"] == "artifacts/publication_eval/latest.json"
    assert study["why_not_applied"] == "ai_reviewer_assessment_stale_after_reviewer_revision"
    assert study["blocked_reason"] == "ai_reviewer_assessment_stale_after_reviewer_revision"
    assert study["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["next_owner"] == "ai_reviewer"
    assert study["owner_route"]["owner_reason"] == "ai_reviewer_assessment_stale_after_reviewer_revision"
    assert study["owner_route"]["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
