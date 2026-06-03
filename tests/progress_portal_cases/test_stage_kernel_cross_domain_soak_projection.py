from __future__ import annotations

import importlib

from .helpers import progress_payload


def _stage_kernel_projection(*, soak_status: str) -> dict[str, object]:
    lanes = [
        {
            "domain_id": "MAS",
            "status": soak_status,
            "readiness": "stage_attempt_active" if soak_status == "running" else "controller_stale_artifact_delta_present",
            "authority_owner": "med-autoscience",
            "authority_function": "medical_research_artifact_authority",
            "artifact_role": "research_evidence_pack",
            "human_gate_state": "not_required",
            "export_readiness": "not_ready",
            "stage_folder_ref": "opl/stages/mas/write",
            "app_workbench_ref": "opl/workbench/mas/write",
            "artifact_gallery_ref": "opl/artifacts/mas/write",
            "stage_progress_log_ref": "opl/stage_progress/mas/write.json",
            "next_owner": {
                "owner": "MedAutoScience",
                "action": "continue_stage_attempt" if soak_status == "running" else "repair_controller_currentness",
            },
            "typed_blocker": {}
            if soak_status == "running"
            else {
                "blocker_id": "controller_stale_with_artifact_delta",
                "required_owner_surface": "stage_kernel_current_pointer_rebuild",
            },
            "artifact_delta_refs": [] if soak_status == "running" else ["opl/artifacts/mas/write/delta.json"],
            "source_refs": ["opl/stages/mas/write/current.json"],
        },
        {
            "domain_id": "MAG",
            "status": "no_live_run",
            "readiness": "awaiting_stage_attempt",
            "authority_owner": "med-auto-grant",
            "authority_function": "grant_authoring_authority",
            "artifact_role": "grant_package",
            "human_gate_state": "not_required",
            "export_readiness": "not_ready",
            "stage_folder_ref": "opl/stages/mag/draft",
            "app_workbench_ref": "opl/workbench/mag/draft",
            "artifact_gallery_ref": "opl/artifacts/mag/draft",
            "stage_progress_log_ref": "opl/stage_progress/mag/draft.json",
            "next_owner": {
                "owner": "MedAutoGrant",
                "action": "start_stage_attempt",
            },
            "typed_blocker": {},
            "artifact_delta_refs": [],
            "source_refs": ["opl/stages/mag/draft/current.json"],
        },
        {
            "domain_id": "OMA",
            "status": "no_live_run",
            "readiness": "awaiting_stage_attempt",
            "authority_owner": "opl-meta-agent",
            "authority_function": "agent_foundry_authority",
            "artifact_role": "agent_test_pack",
            "human_gate_state": "not_required",
            "export_readiness": "not_ready",
            "stage_folder_ref": "opl/stages/oma/build",
            "app_workbench_ref": "opl/workbench/oma/build",
            "artifact_gallery_ref": "opl/artifacts/oma/build",
            "stage_progress_log_ref": "opl/stage_progress/oma/build.json",
            "next_owner": {
                "owner": "OPLMetaAgent",
                "action": "start_stage_attempt",
            },
            "typed_blocker": {},
            "artifact_delta_refs": [],
            "source_refs": ["opl/stages/oma/build/current.json"],
        },
        {
            "domain_id": "RCA",
            "status": "no_live_run",
            "readiness": "awaiting_stage_attempt",
            "authority_owner": "redcube-ai",
            "authority_function": "visual_deliverable_authority",
            "artifact_role": "visual_delivery_pack",
            "human_gate_state": "not_required",
            "export_readiness": "not_ready",
            "stage_folder_ref": "opl/stages/rca/render",
            "app_workbench_ref": "opl/workbench/rca/render",
            "artifact_gallery_ref": "opl/artifacts/rca/render",
            "stage_progress_log_ref": "opl/stage_progress/rca/render.json",
            "next_owner": {
                "owner": "RedCubeAI",
                "action": "start_stage_attempt",
            },
            "typed_blocker": {},
            "artifact_delta_refs": [],
            "source_refs": ["opl/stages/rca/render/current.json"],
        },
    ]
    return {
        "surface_kind": "stage_kernel_projection",
        "current_stage": "write",
        "artifact_roles": [],
        "missing_outputs": [],
        "accepted_receipts": ["artifacts/owner_receipts/write/latest.json"],
        "semantic_validation": {},
        "consumability": {},
        "lineage": {},
        "retention": {},
        "current_pointer": {},
        "blocker": {},
        "next_owner": {
            "owner": "ai_reviewer",
            "action": "return_to_ai_reviewer_workflow",
        },
        "provider_liveness": {
            "running_provider_attempt": soak_status == "running",
        },
        "cross_domain_soak": {
            "surface_kind": "stage_kernel_cross_domain_soak",
            "readiness_summary": "MAS/MAG/OMA/RCA Stage Kernel lane status is projected from stage folders.",
            "lanes": lanes,
            "source_refs": ["opl/stage-kernel/cross-domain-soak/latest.json"],
        },
    }


def _workbench_soak_projection(*, soak_status: str) -> dict[str, object]:
    module = importlib.import_module("med_autoscience.controllers.progress_portal")
    progress = progress_payload()
    progress["stage_kernel_projection"] = _stage_kernel_projection(soak_status=soak_status)

    payload = module.build_progress_portal_payload(
        profile_name="diabetes",
        workspace_root="/workspace",
        study_id="001-risk",
        progress_payload=progress,
        generated_at="2026-06-03T01:05:00+00:00",
    )

    return payload["mas_opl_runtime_workbench_projection"]["studies"][0]["stage_operating_layer"]["cross_domain_soak"]


def test_stage_operating_layer_projects_running_cross_domain_soak_summary() -> None:
    soak = _workbench_soak_projection(soak_status="running")

    assert soak["status"] == "running"
    assert soak["lane_counts"] == {
        "total": 4,
        "running": 1,
        "blocked": 0,
        "stale_controller_with_artifact_delta": 0,
        "no_live_run": 3,
    }
    assert soak["required_domain_lanes"] == ["MAS", "MAG", "OMA", "RCA"]
    assert soak["missing_required_lanes"] == []
    assert soak["all_required_lanes_present"] is True
    assert soak["authority_summary"] == {
        "stage_kernel_owner": "one-person-lab",
        "workbench_role": "read_only_projection",
        "writes_domain_truth": False,
        "writes_mas_truth": False,
        "can_authorize_domain_readiness": False,
        "can_authorize_artifact_mutation": False,
        "current_truth_source": "stage_kernel_projection",
    }
    assert soak["lanes"][0] == {
        "domain_id": "MAS",
        "status": "running",
        "readiness": "stage_attempt_active",
        "authority_owner": "med-autoscience",
        "authority_function": "medical_research_artifact_authority",
        "artifact_role": "research_evidence_pack",
        "human_gate_state": "not_required",
        "export_readiness": "not_ready",
        "stage_folder_ref": "opl/stages/mas/write",
        "app_workbench_ref": "opl/workbench/mas/write",
        "artifact_gallery_ref": "opl/artifacts/mas/write",
        "stage_progress_log_ref": "opl/stage_progress/mas/write.json",
        "artifact_delta_refs": [],
        "next_owner": {
            "owner": "MedAutoScience",
            "action": "continue_stage_attempt",
        },
        "typed_blocker": {},
        "source_refs": [
            "opl/stages/mas/write/current.json",
            "opl/stages/mas/write",
            "opl/workbench/mas/write",
            "opl/artifacts/mas/write",
            "opl/stage_progress/mas/write.json",
        ],
        "authority": {
            "domain_authority_owner": "med-autoscience",
            "domain_authority_retained": True,
            "workbench_can_write_domain_truth": False,
            "workbench_can_authorize_domain_readiness": False,
            "workbench_can_mutate_artifact_body": False,
        },
    }
    assert soak["authority"] == {
        "opl_role": "stage_kernel_cross_domain_soak_projection_consumer_only",
        "writes_domain_truth": False,
        "writes_mas_truth": False,
        "claims_publication_ready": False,
        "can_authorize_domain_readiness": False,
        "can_authorize_artifact_mutation": False,
        "can_write_artifact_body": False,
        "current_truth_source": "stage_kernel_projection",
    }


def test_stage_operating_layer_projects_stale_controller_artifact_delta_soak_summary() -> None:
    soak = _workbench_soak_projection(soak_status="stale-controller-with-artifact-delta")

    assert soak["status"] == "stale_controller_with_artifact_delta"
    assert soak["lane_counts"] == {
        "total": 4,
        "running": 0,
        "blocked": 0,
        "stale_controller_with_artifact_delta": 1,
        "no_live_run": 3,
    }
    assert soak["lanes"][0]["status"] == "stale_controller_with_artifact_delta"
    assert soak["lanes"][0]["typed_blocker"] == {
        "blocker_id": "controller_stale_with_artifact_delta",
        "required_owner_surface": "stage_kernel_current_pointer_rebuild",
    }
    assert soak["lanes"][0]["artifact_delta_refs"] == ["opl/artifacts/mas/write/delta.json"]
    assert soak["lanes"][0]["authority"]["workbench_can_write_domain_truth"] is False
