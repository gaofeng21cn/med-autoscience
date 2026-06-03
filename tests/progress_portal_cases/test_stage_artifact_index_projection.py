from __future__ import annotations

import importlib

from .helpers import progress_payload


def _stage_artifact_index() -> dict[str, object]:
    return {
        "surface_kind": "stage_artifact_index",
        "current_stage": "write",
        "next_owner_action": {
            "owner": "ai_reviewer",
            "action": "return_to_ai_reviewer_workflow",
        },
        "stale_platform_repairs": [
            {
                "repair_id": "read_model_reconcile_001",
                "reason": "superseded_by_current_stage_artifact",
            }
        ],
        "stages": [
            {
                "stage_id": "write",
                "artifact_refs": ["paper/current_draft.md"],
                "owner_receipt_refs": ["artifacts/owner_receipts/write/latest.json"],
            }
        ],
    }


def test_progress_portal_workbench_projects_stage_artifact_index_for_selected_study() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = progress_payload()
    progress["stage_artifact_index"] = _stage_artifact_index()

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=progress,
        generated_at="2026-05-08T01:05:00+00:00",
    )

    study = payload["mas_opl_runtime_workbench_projection"]["studies"][0]
    assert study["stage_artifact_index"] == _stage_artifact_index()
    assert study["reference_projection"]["lanes"]["stage_artifact_index"] == {
        "lane_id": "stage_artifact_index",
        "status": "observed",
        "surface_kind": "stage_artifact_index",
        "current_stage": "write",
        "next_owner_action": {
            "owner": "ai_reviewer",
            "action": "return_to_ai_reviewer_workflow",
        },
        "stale_platform_repairs": [
            {
                "repair_id": "read_model_reconcile_001",
                "reason": "superseded_by_current_stage_artifact",
            }
        ],
        "stage_count": 1,
        "stages": [
            {
                "stage_id": "write",
                "artifact_refs": ["paper/current_draft.md"],
                "owner_receipt_refs": ["artifacts/owner_receipts/write/latest.json"],
            }
        ],
        "authority": {
            "opl_role": "workbench_projection_consumer_only",
            "writes_mas_truth": False,
            "body_free": True,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_artifact_mutation": False,
            "can_write_memory_body": False,
        },
    }
