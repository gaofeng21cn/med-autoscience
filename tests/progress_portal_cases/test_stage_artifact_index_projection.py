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


def _stage_kernel_projection() -> dict[str, object]:
    return {
        "surface_kind": "stage_kernel_projection",
        "current_stage": "write",
        "artifact_roles": [
            {
                "role": "canonical_stage_output",
                "ref": "paper/current_draft.md",
            }
        ],
        "missing_outputs": ["tables/subgroup_sensitivity.csv"],
        "accepted_receipts": ["artifacts/owner_receipts/write/latest.json"],
        "semantic_validation": {},
        "consumability": {},
        "lineage": {},
        "retention": {},
        "current_pointer": {},
        "promotion": {
            "surface_kind": "opl_stage_current_pointer_promotion_audit",
            "status": "blocked",
            "fail_closed": True,
            "authority_boundary": {
                "writes_current_pointer": False,
            },
        },
        "lineage_retention": {
            "surface_kind": "opl_stage_lineage_retention_drilldown",
            "status": "blocked",
            "cleanup_authorized": False,
        },
        "state_index": {
            "status": "ready_for_opl_sidecar_ingest",
            "row_count": 0,
            "sqlite_record_counts_as_stage_complete": False,
        },
        "blocker": {
            "blocker_id": "subgroup_sensitivity_missing",
            "owner": "writer",
        },
        "next_owner": {
            "owner": "ai_reviewer",
            "action": "return_to_ai_reviewer_workflow",
        },
        "provider_liveness": {
            "running_provider_attempt": True,
            "active_stage_attempt_id": "stage-attempt-001",
            "source_ref": "artifacts/runtime/opl_current_control_state/latest.json",
        },
    }


def test_progress_portal_workbench_projects_stage_operating_layer_for_selected_study() -> None:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = progress_payload()
    progress["stage_artifact_index"] = _stage_artifact_index()
    progress["stage_kernel_projection"] = _stage_kernel_projection()

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=progress,
        generated_at="2026-05-08T01:05:00+00:00",
    )

    study = payload["mas_opl_runtime_workbench_projection"]["studies"][0]
    assert payload["mas_opl_runtime_workbench_projection"]["authority"] == {
        "opl_role": "workbench_readback_projection_consumer_only",
        "mas_truth_owner": True,
        "page_scope": "study",
        "writes_mas_truth": False,
        "claims_publication_ready": False,
        "current_truth_source": "stage_kernel_projection",
        "can_transport_operator_action": False,
        "can_emit_runtime_command": False,
        "operator_intent_refs_are_inert": True,
        "external_opl_workbench_shell_required": True,
        "forbidden_writes": [
            "study_truth",
            "publication_judgment",
            "quality_verdict",
            "runtime_authority",
            "artifact_authority",
            "runtime_state",
            "runtime_sqlite",
            "terminal_commands",
            "current_package",
            "evidence_ledger",
            "review_ledger",
        ],
    }
    assert study["information_hierarchy"] == {
        "primary_progress": ["stage_operating_layer"],
        "secondary_diagnostics": [
            "stage_artifact_index",
            "progress_first",
            "paper_route_lens",
            "reference_projection",
        ],
        "diagnostic_surfaces_are_primary_progress": False,
        "current_truth_source": "stage_kernel_projection",
    }
    assert study["stage_operating_layer"] == {
        "surface_kind": "mas_opl_stage_operating_layer",
        "schema_version": 1,
        "status": "observed",
        "display_role": "primary_progress",
        "current_truth_source": "stage_kernel_projection",
        "current_stage": "write",
        "artifact_roles": [
            {
                "role": "canonical_stage_output",
                "ref": "paper/current_draft.md",
            }
        ],
        "missing_outputs": ["tables/subgroup_sensitivity.csv"],
        "accepted_receipts": ["artifacts/owner_receipts/write/latest.json"],
        "semantic_validation": {},
        "consumability": {},
        "lineage": {},
        "retention": {},
        "current_pointer": {},
        "promotion": {
            "surface_kind": "opl_stage_current_pointer_promotion_audit",
            "status": "blocked",
            "fail_closed": True,
            "authority_boundary": {
                "writes_current_pointer": False,
            },
        },
        "lineage_retention": {
            "surface_kind": "opl_stage_lineage_retention_drilldown",
            "status": "blocked",
            "cleanup_authorized": False,
        },
        "state_index": {
            "status": "ready_for_opl_sidecar_ingest",
            "row_count": 0,
            "sqlite_record_counts_as_stage_complete": False,
        },
        "blocker": {
            "blocker_id": "subgroup_sensitivity_missing",
            "owner": "writer",
        },
        "next_owner": {
            "owner": "ai_reviewer",
            "action": "return_to_ai_reviewer_workflow",
        },
        "provider_liveness": {
            "running_provider_attempt": True,
            "active_stage_attempt_id": "stage-attempt-001",
            "source_ref": "artifacts/runtime/opl_current_control_state/latest.json",
        },
        "authority": {
            "opl_role": "stage_operating_layer_projection_consumer_only",
            "writes_mas_truth": False,
            "claims_publication_ready": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_artifact_mutation": False,
            "can_write_artifact_body": False,
            "current_truth_source": "stage_kernel_projection",
        },
    }
    assert study["stage_artifact_index"] == _stage_artifact_index()
    assert study["reference_projection"]["lanes"]["stage_artifact_index"] == {
        "lane_id": "stage_artifact_index",
        "status": "observed",
        "diagnostic_tier": "secondary",
        "derived_projection": True,
        "is_truth_source": False,
        "current_truth_source": "stage_kernel_projection",
        "surface_kind": "stage_artifact_index",
        "current_stage": "write",
        "next_owner_action": {
            "owner": "ai_reviewer",
            "action": "return_to_ai_reviewer_workflow",
            "action_ref_role": "stage_artifact_index_next_owner_action_ref",
            "authority": False,
            "can_execute": False,
            "can_generate_action": False,
            "can_authorize_provider_admission": False,
            "display_command_ref_only": True,
            "requires_opl_current_control_readback": True,
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
            "claims_publication_ready": False,
            "body_free": True,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_artifact_mutation": False,
            "can_write_memory_body": False,
            "current_truth_source": "stage_kernel_projection",
        },
    }


def test_progress_portal_workbench_fails_closed_without_stage_kernel_projection() -> None:
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
    assert study["stage_operating_layer"] == {
        "surface_kind": "mas_opl_stage_operating_layer",
        "schema_version": 1,
        "status": "pending",
        "display_role": "primary_progress",
        "current_truth_source": "stage_kernel_projection",
        "summary": "等待 MAS stage_kernel_projection；Workbench fail-closed 为 pending lane。",
        "pending_lane": {
            "required_surface": "stage_kernel_projection",
            "display_only": True,
            "fail_closed": True,
        },
        "authority": {
            "opl_role": "stage_operating_layer_projection_consumer_only",
            "writes_mas_truth": False,
            "claims_publication_ready": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_artifact_mutation": False,
            "can_write_artifact_body": False,
            "current_truth_source": "stage_kernel_projection",
        },
    }
    assert study["reference_projection"]["lanes"]["stage_artifact_index"]["diagnostic_tier"] == "secondary"
    assert study["reference_projection"]["lanes"]["stage_artifact_index"]["derived_projection"] is True
    assert study["reference_projection"]["lanes"]["stage_artifact_index"]["is_truth_source"] is False
