from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_supervisor_scan_routes_clean_paper_authority_cutover_to_ai_reviewer(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_supervisor_scan")
    migration = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_json(
        study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json",
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration",
            "status": "awaiting_new_mas_authority",
            "study_id": study_id,
        },
    )
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    _write_json(
        request_path,
        {
            "surface": "supervisor_action_request",
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_id": f"return_to_ai_reviewer_workflow::{study_id}",
            "request_owner": "ai_reviewer",
            "input_contract": {
                "required_refs": {},
                "all_required_refs_present": True,
                "missing_or_invalid_refs": [],
            },
        },
    )
    status_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / study_id),
        "quest_status": "waiting_for_user",
        "active_run_id": None,
        "runtime_health_snapshot": {
            "canonical_runtime_action": "observe",
            "attempt_state": "parked",
            "blocking_reasons": [],
        },
        "publication_eval": {
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "legacy_recheck",
                "ai_reviewer_required": False,
            },
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-epoch-cutover",
            "source_signature": "truth-source-cutover",
        },
        "study_macro_state": {
            "writer_state": "parked",
            "reason": "external_info",
        },
    }
    progress_payload = {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": study_id,
        "current_stage": "auto_runtime_parked",
        "paper_stage": "bundle_stage_ready",
        "refs": {"publication_eval_path": str(study_root / "artifacts" / "publication_eval" / "latest.json")},
        "supervision": {"active_run_id": None, "health_status": "parked"},
        "quality_review_loop": {"closure_state": "review_required"},
        "ai_reviewer_request_lifecycle": {
            "surface": "ai_reviewer_request_lifecycle",
            "state": "requested",
            "request_id": f"return_to_ai_reviewer_workflow::{study_id}",
            "request_owner": "ai_reviewer",
            "refs": {"request_path": str(request_path)},
        },
    }

    monkeypatch.setattr(
        module,
        "_read_study_projection_inputs",
        lambda **_: (
            status_payload,
            progress_payload,
            study_id,
            migration.cutover_publication_eval_payload(study_root=study_root),
        ),
    )

    result = module.supervisor_scan(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        developer_supervisor_mode="developer_apply_safe",
        persist_surfaces=False,
    )

    study = result["studies"][0]
    assert study["ai_reviewer_assessment"]["missing"] is True
    assert study["ai_reviewer_assessment"]["owner"] == "ai_reviewer"
    assert [item["action_type"] for item in study["action_queue"]] == ["return_to_ai_reviewer_workflow"]
    assert study["blocked_reason"] == "paper_authority_clean_migration_required"
    assert study["next_owner"] == "ai_reviewer"
