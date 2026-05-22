from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_owner_route_reconcile_keeps_writer_handoff_blocker_after_quality_batch_handoff_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    reconcile = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    quest_root = profile.runtime_root / quest_id
    eval_id = "publication-eval::dm002::current-write-route-back"
    publication_eval = {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
        "verdict": {"overall_verdict": "blocked", "primary_claim_status": "partial"},
        "quality_assessment": {"medical_journal_prose_quality": {"status": "blocked"}},
        "recommended_actions": [
            {
                "action_id": "return-to-write",
                "action_type": "route_back_same_line",
                "route_target": "write",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm002_same_line_publication_paper_repair"
                ),
                "next_work_unit": {
                    "unit_id": "dm002_same_line_publication_paper_repair",
                    "lane": "write",
                    "summary": "Repair the manuscript body against current AI reviewer prose findings.",
                },
            }
        ],
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": eval_id,
            "status": "handoff_ready",
            "ok": True,
            "study_id": study_id,
            "quest_id": quest_id,
            "blocked_reason": None,
            "next_owner": "write",
            "writer_worker_handoff": {
                "dispatch_status": "ready",
                "next_executable_owner": "write",
                "typed_blocker_if_unresolved": "manuscript_story_surface_delta_missing",
            },
            "repair_execution_evidence": {
                "status": "blocked",
                "progress_delta_candidate": False,
                "blockers": ["manuscript_story_surface_delta_missing"],
                "canonical_artifact_delta": {
                    "status": "blocked",
                    "meaningful_artifact_delta": False,
                },
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "quest_status": "completed",
        "decision": "completed",
        "reason": "completed",
        "active_run_id": None,
        "publication_eval": publication_eval,
        "study_completion_contract": {"ready": True, "status": "resolved"},
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-dm002-write-handoff",
            "source_signature": "truth-source-dm002-write-handoff",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "current_stage": "managed_runtime_supervision_gap",
        "paper_stage": "publishability_gate_blocked",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "study_completion_contract": {"ready": True, "status": "resolved"},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
    }
    monkeypatch.setattr(
        reconcile,
        "_read_study_projection_inputs",
        lambda **_: (status_payload, progress_payload, quest_id, publication_eval),
    )

    result = reconcile.scan_domain_routes(
        profile=profile,
        study_ids=[study_id],
        developer_supervisor_mode="developer_apply_safe",
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert [action["action_type"] for action in study["action_queue"]] == ["run_quality_repair_batch"]
    action = study["action_queue"][0]
    assert action["owner"] == "write"
    assert action["reason"] == "manuscript_story_surface_delta_missing"
    assert action["next_work_unit"] == "dm002_same_line_publication_paper_repair"
    assert action["quality_repair_batch_ref"] == str(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    )
    assert action["paper_package_mutation_allowed"] is False
    assert action["current_package_write_allowed"] is False
    assert action["medical_claim_authoring_allowed"] is False
    assert study["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert study["next_owner"] == "write"
    assert study["owner_route"]["allowed_actions"] == ["run_quality_repair_batch"]
