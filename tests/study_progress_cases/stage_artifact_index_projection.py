from __future__ import annotations

import importlib
from pathlib import Path

from .shared import make_profile, write_study


def test_study_progress_consumes_stage_artifact_index_projection(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    projection_module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    observed: dict[str, object] = {}

    def fake_build_stage_artifact_index(*, study_id, study_root):
        observed["study_id"] = study_id
        observed["study_root"] = study_root
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

    monkeypatch.setattr(
        projection_module,
        "build_stage_artifact_index",
        fake_build_stage_artifact_index,
    )

    result = module.read_study_progress(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        sync_runtime_summary=False,
    )

    assert observed == {"study_id": "001-risk", "study_root": study_root}
    assert result["stage_artifact_index"] == {
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
