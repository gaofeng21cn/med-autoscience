from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.owner_route_reconcile_cases.owner_route_test_helpers import assert_owner_route_required
from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_does_not_repair_paused_delivered_package_without_live_worker(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    quest_root = profile.runtime_root / "quest-dm"
    _write_json(
        study_root / "manuscript" / "delivery_manifest.json",
        {
            "schema_version": 1,
            "stage": "submission_minimal",
            "surface_roles": {
                "human_facing_current_package_root": str(study_root / "manuscript" / "current_package"),
                "human_facing_current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
            },
        },
    )
    (study_root / "manuscript" / "current_package").mkdir(parents=True, exist_ok=True)
    (study_root / "manuscript" / "current_package" / "manuscript.docx").write_text("docx", encoding="utf-8")
    (study_root / "manuscript" / "current_package" / "paper.pdf").write_text("pdf", encoding="utf-8")
    (study_root / "manuscript" / "current_package.zip").write_text("zip", encoding="utf-8")
    status_payload = {
        "study_id": "001-dm-cvd-mortality-risk",
        "study_root": str(study_root),
        "quest_id": "quest-dm",
        "quest_root": str(quest_root),
        "quest_status": "paused",
        "decision": "blocked",
        "reason": "quest_waiting_for_submission_metadata",
        "active_run_id": None,
        "auto_runtime_parked": {
            "parked": True,
            "parked_state": "external_metadata_pending",
            "auto_execution_complete": True,
        },
        "runtime_liveness_audit": {
            "active_run_id": None,
            "runtime_audit": {"worker_running": False, "active_run_id": None},
        },
        "runtime_health_snapshot": {
            "canonical_runtime_action": "await_explicit_resume",
            "attempt_state": "parked",
            "blocking_reasons": ["quest_waiting_for_submission_metadata"],
        },
        "publication_eval": {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "recommended_actions": [],
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "current_stage": "auto_runtime_parked",
            "paper_stage": "bundle_stage_blocked",
            "auto_runtime_parked": status_payload["auto_runtime_parked"],
            "supervision": {"active_run_id": None, "health_status": "parked"},
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert [item["action_type"] for item in study["action_queue"]] == []
    assert study["why_not_applied"] is None
    assert study["blocked_reason"] is None
    assert study["next_owner"] is None
    assert study["external_supervisor_required"] is False
    assert study["paper_package_mutated"] is False


def test_scan_domain_routes_prefers_current_ai_reviewer_publication_eval_over_stale_status_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm")
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
            },
            "recommended_actions": [
                {
                    "action_type": "return_to_finalize",
                    "next_work_unit": {"unit_id": "submission_minimal_refresh"},
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "study_root": str(study_root),
            "quest_id": "quest-dm",
            "quest_root": str(profile.runtime_root / "quest-dm"),
            "quest_status": "active",
            "runtime_liveness_audit": {
                "active_run_id": "run-live",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-live"},
            },
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
                "recommended_actions": [{"next_work_unit": {"unit_id": "gate_needs_specificity"}}],
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "001-dm-cvd-mortality-risk",
            "paper_stage": "bundle_stage_blocked",
            "refs": {"publication_eval_path": str(publication_eval_path)},
            "supervision": {"active_run_id": "run-live", "health_status": "live"},
            "quality_review_loop": {"closure_state": "review_required"},
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("001-dm-cvd-mortality-risk",),
        apply_safe_actions=True,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["present"] is True
    assert study["ai_reviewer_assessment"]["missing"] is False
    assert [item["action_type"] for item in study["action_queue"]] == []
