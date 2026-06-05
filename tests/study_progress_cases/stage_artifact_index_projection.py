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
    assert result["stage_kernel_projection"]["stage_run_profile_ref"] == "contracts/stage_run_kernel_profile.json"
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


def test_stage_kernel_projection_exposes_stage_run_transition_authority() -> None:
    projection_module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.stage_kernel_projection"
    )

    result = projection_module.stage_kernel_projection_from_artifact_index(
        {
            "surface_kind": "stage_artifact_index",
            "domain_stage_pack_ref": "contracts/mas-paper-study-stage-pack.json",
            "stage_artifact_runtime_contract_ref": "contracts/opl-framework/stage-artifact-runtime-contract.json",
            "current_stage": {"stage_id": "07-independent_review_and_revision"},
            "next_owner_action": {
                "owner": "07-independent_review_and_revision",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
            },
            "provider_liveness": {"running_provider_attempt": False},
            "stages": [
                {
                    "stage_id": "07-independent_review_and_revision",
                    "stage_progress_status": "artifact_contract_broken",
                    "required_output_refs": [
                        {
                            "role": "independent_reviewer_record",
                            "ref": "artifacts/stage_outputs/07-independent_review_and_revision/outputs/ai_reviewer_record.json",
                        }
                    ],
                    "stage_folder_contract": {
                        "manifest_ref": "artifacts/stage_outputs/07-independent_review_and_revision/stage_manifest.json",
                        "receipt_ref": "artifacts/stage_outputs/07-independent_review_and_revision/receipts/owner_receipt.json",
                    },
                    "artifact_classification": {
                        "current": [],
                        "missing": [],
                        "fail_closed_reason": "receipt_required",
                        "owner_receipt_refs": [],
                        "typed_blocker_refs": [
                            "artifacts/stage_outputs/07-independent_review_and_revision/receipts/typed_blocker.json"
                        ],
                        "semantic_validation": {"status": "typed_blocker"},
                        "consumability": {
                            "status": "blocked",
                            "failed_checks": ["domain_validation"],
                        },
                        "promotion": {"state": "receipt_required"},
                    },
                    "current_pointer": {
                        "stage_id": "07-independent_review_and_revision",
                        "attempt_id": "attempt-ai-reviewer-001",
                        "terminal_status": "success",
                    },
                    "physical_stage_folder_kernel": {"status": "observed"},
                }
            ],
        }
    )

    stage_run = result["stage_run"]
    assert stage_run["surface_kind"] == "stage_run_kernel_projection"
    assert stage_run["state"] == "TypedBlocked"
    assert stage_run["stage_id"] == "07-independent_review_and_revision"
    assert stage_run["attempt_id"] == "attempt-ai-reviewer-001"
    assert stage_run["generation"] == "attempt-ai-reviewer-001"
    assert stage_run["transition_authority"] == {
        "owner_receipt_or_typed_blocker_required": True,
        "file_presence_counts_as_completion": False,
        "provider_completion_counts_as_domain_completion": False,
        "latest_projection_counts_as_transition_authority": False,
        "read_model_counts_as_transition_authority": False,
    }
    assert stage_run["domain_outcome"] == {
        "owner_receipt_refs": [],
        "typed_blocker_refs": [
            "artifacts/stage_outputs/07-independent_review_and_revision/receipts/typed_blocker.json"
        ],
        "domain_accepted": False,
        "typed_blocked": True,
    }
    assert result["current_owner_delta"] == {
        "surface_kind": "stage_run_current_owner_delta",
        "schema_version": 1,
        "stage_id": "07-independent_review_and_revision",
        "state": "TypedBlocked",
        "owner": "ai_reviewer",
        "action_type": "resolve_typed_blocker",
        "typed_blocker_refs": [
            "artifacts/stage_outputs/07-independent_review_and_revision/receipts/typed_blocker.json"
        ],
        "owner_receipt_refs": [],
        "projection_only": True,
        "writes_transition_authority": False,
    }
    assert result["authority"]["derived_projection"] is True
    assert result["authority"]["writes_mas_truth"] is False
    assert result["authority"]["can_authorize_quality_verdict"] is False
