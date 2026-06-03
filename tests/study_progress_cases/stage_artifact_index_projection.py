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
                    "stage_progress_status": "artifact_contract_required",
                    "required_output_refs": [
                        {
                            "role": "canonical_stage_output",
                            "ref": "paper/current_draft.md",
                        }
                    ],
                    "artifact_classification": {
                        "missing": ["tables/subgroup_sensitivity.csv"],
                        "owner_receipt_refs": ["artifacts/owner_receipts/write/latest.json"],
                        "fail_closed_reason": "missing_required_output",
                        "semantic_validation": {
                            "status": "missing_domain_receipt",
                        },
                        "consumability": {
                            "status": "blocked",
                            "failed_checks": ["domain_validation"],
                        },
                        "lineage": {
                            "status": "observed",
                        },
                        "retention": {
                            "status": "covered",
                        },
                    },
                    "current_pointer": {
                        "promotion_state": "receipt_required",
                    },
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
                    "stage_progress_status": "artifact_contract_required",
                    "required_output_refs": [
                        {
                            "role": "canonical_stage_output",
                            "ref": "paper/current_draft.md",
                        }
                    ],
                    "artifact_classification": {
                        "missing": ["tables/subgroup_sensitivity.csv"],
                        "owner_receipt_refs": ["artifacts/owner_receipts/write/latest.json"],
                        "fail_closed_reason": "missing_required_output",
                        "semantic_validation": {
                            "status": "missing_domain_receipt",
                        },
                        "consumability": {
                            "status": "blocked",
                            "failed_checks": ["domain_validation"],
                        },
                        "lineage": {
                            "status": "observed",
                        },
                        "retention": {
                            "status": "covered",
                        },
                    },
                    "current_pointer": {
                        "promotion_state": "receipt_required",
                    },
                }
            ],
        }
    assert result["stage_kernel_projection"]["surface_kind"] == "stage_kernel_projection"
    assert result["stage_kernel_projection"]["current_stage"] == "write"
    assert result["stage_kernel_projection"]["artifact_roles"] == [
        {
            "role": "canonical_stage_output",
            "ref": "paper/current_draft.md",
        }
    ]
    assert result["stage_kernel_projection"]["missing_outputs"] == [
        "tables/subgroup_sensitivity.csv"
    ]
    assert result["stage_kernel_projection"]["accepted_receipts"] == [
        "artifacts/owner_receipts/write/latest.json"
    ]
    assert result["stage_kernel_projection"]["blocker"] == {
        "blocker_id": "missing_required_output",
        "stage_id": "write",
        "failed_checks": ["domain_validation"],
        "semantic_validation_status": "missing_domain_receipt",
        "consumability_status": "blocked",
        "opl_can_override": False,
    }
