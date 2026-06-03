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
                        "decision_receipt_refs": ["artifacts/owner_receipts/write/decision.json"],
                        "fail_closed_reason": "missing_required_output",
                        "latest_attempt_id": "attempt-001",
                        "promotion": {
                            "state": "receipt_required",
                            "pointer_stage_matches": True,
                            "pointer_attempt_matches": True,
                            "pointer_terminal_status": "success",
                            "latest_attempt_id": "attempt-001",
                        },
                        "semantic_validation": {
                            "status": "missing_domain_receipt",
                        },
                        "consumability": {
                            "status": "blocked",
                            "failed_checks": ["domain_validation"],
                        },
                        "lineage": {
                            "status": "observed",
                            "lineage_events_ref": "lineage/events.jsonl",
                            "lineage_graph_ref": "lineage/graph.json",
                        },
                        "retention": {
                            "status": "covered",
                            "restore_refs": ["restore/proof.json"],
                            "retention_refs": ["retention/policy.json"],
                        },
                    },
                    "current_pointer": {
                        "stage_id": "write",
                        "attempt_id": "attempt-001",
                        "terminal_status": "success",
                        "artifact_refs": ["paper/current_draft.md"],
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
                        "decision_receipt_refs": ["artifacts/owner_receipts/write/decision.json"],
                        "fail_closed_reason": "missing_required_output",
                        "latest_attempt_id": "attempt-001",
                        "promotion": {
                            "state": "receipt_required",
                            "pointer_stage_matches": True,
                            "pointer_attempt_matches": True,
                            "pointer_terminal_status": "success",
                            "latest_attempt_id": "attempt-001",
                        },
                        "semantic_validation": {
                            "status": "missing_domain_receipt",
                        },
                        "consumability": {
                            "status": "blocked",
                            "failed_checks": ["domain_validation"],
                        },
                        "lineage": {
                            "status": "observed",
                            "lineage_events_ref": "lineage/events.jsonl",
                            "lineage_graph_ref": "lineage/graph.json",
                        },
                        "retention": {
                            "status": "covered",
                            "restore_refs": ["restore/proof.json"],
                            "retention_refs": ["retention/policy.json"],
                        },
                    },
                    "current_pointer": {
                        "stage_id": "write",
                        "attempt_id": "attempt-001",
                        "terminal_status": "success",
                        "artifact_refs": ["paper/current_draft.md"],
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
    assert result["stage_kernel_projection"]["state_index"]["index_authority"] == (
        "derived_refs_only_rebuildable_read_model"
    )
    assert result["stage_kernel_projection"]["state_index"]["sqlite_record_counts_as_stage_complete"] is False
    assert result["stage_kernel_projection"]["state_index"]["derived_index_rebuildable"] is True
    assert result["stage_kernel_projection"]["promotion"]["surface_kind"] == (
        "opl_stage_current_pointer_promotion_audit"
    )
    assert result["stage_kernel_projection"]["promotion"]["fail_closed"] is True
    assert "partial_commit" in result["stage_kernel_projection"]["promotion"]["fail_closed_reasons"]
    assert result["stage_kernel_projection"]["promotion"]["authority_boundary"][
        "writes_current_pointer"
    ] is False
    assert result["stage_kernel_projection"]["lineage_retention"]["surface_kind"] == (
        "opl_stage_lineage_retention_drilldown"
    )
    assert result["stage_kernel_projection"]["lineage_retention"]["cleanup_authorized"] is False
    assert result["stage_kernel_projection"]["lineage_retention"]["retention_restore_gate"][
        "cleanup_authorized_by_projection"
    ] is False
