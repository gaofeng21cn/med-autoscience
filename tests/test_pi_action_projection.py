from __future__ import annotations

from med_autoscience.controllers.pi_action_projection import (
    ACTION_ORDER,
    build_pi_action_projection,
    compact_pi_action_projection,
)
from med_autoscience.mcp_server_parts.study_progress_projection import compact_study_progress_projection


def test_pi_action_projection_maps_study_progress_surfaces_to_doctor_categories() -> None:
    payload = {
        "study_id": "001-risk",
        "recommended_command": "medautosci study-progress --study-id 001-risk",
        "current_blockers": [
            "reference_gaps_present",
            "statistical_reporting_incomplete",
            "claim_evidence_map_missing_or_incomplete",
        ],
        "medical_paper_readiness": {
            "overall_status": "blocked",
            "capability_surfaces": [
                {
                    "surface_key": "literature_scout",
                    "status": "missing",
                    "required_for_ready": True,
                    "missing_reason": "missing references and guideline anchors",
                },
                {
                    "surface_key": "statistical_discipline_operations",
                    "status": "partial",
                    "required_for_ready": True,
                    "missing_reason": "statistical sensitivity and subgroup plan incomplete",
                },
                {
                    "surface_key": "target_journal_writing_layer",
                    "status": "missing",
                    "required_for_ready": True,
                    "missing_reason": "ai_reviewer journal writing workflow missing",
                },
                {
                    "surface_key": "real_study_soak_matrix_evidence",
                    "status": "partial",
                    "required_for_ready": True,
                    "missing_reason": "submission package rebuild proof pending",
                },
            ],
        },
        "quality_execution_lane": {
            "lane_id": "claim_evidence",
            "summary": "primary claim evidence is too weak and should be downgraded",
        },
        "same_line_route_truth": {
            "same_line_state": "bounded_analysis",
            "summary": "same_line route_back remains available for bounded analysis",
        },
        "control_plane_snapshot": {
            "canonical_next_action": "switch_line_after_stop_loss",
            "blocking_reasons": ["stop_loss memo requests switch line"],
        },
        "refs": {
            "study_truth_snapshot_path": "/tmp/study-truth.json",
            "publication_eval_path": "/tmp/publication_eval/latest.json",
        },
    }

    projection = build_pi_action_projection(payload)

    assert projection["surface"] == "pi_action_projection"
    assert projection["read_model"] == "L2_pi_action_projection_read_model"
    assert projection["authority"] == "projection_only"
    assert projection["projection_only"] is True
    assert projection["study_id"] == "001-risk"
    assert [item["category"] for item in projection["categories"]] == list(ACTION_ORDER)
    assert projection["primary_category"] == "补文献"
    assert all(item["projection_only"] is True for item in projection["categories"])
    assert all(item["can_set_canonical_next_action"] is False for item in projection["categories"])
    assert all(item["can_authorize_publication_readiness"] is False for item in projection["categories"])
    assert all(item["can_authorize_submission"] is False for item in projection["categories"])
    assert projection["authority_contract"] == {
        "projection_only": True,
        "can_set_canonical_next_action": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission": False,
        "can_mutate_runtime": False,
        "canonical_next_action_authority": (
            "StudyTruthKernel, RuntimeHealthKernel, AI reviewer-backed publication_eval/latest.json, "
            "controller_decisions/latest.json, and canonical artifact proof"
        ),
    }
    assert "study_progress" in projection["source_surfaces"]
    assert "medical_paper_readiness" in projection["source_surfaces"]
    assert projection["categories"][0]["evidence_refs"] == [
        "/tmp/study-truth.json",
        "/tmp/publication_eval/latest.json",
    ]


def test_compact_pi_action_projection_preserves_projection_only_boundary() -> None:
    full = build_pi_action_projection(
        {
            "study_id": "002-revision",
            "next_system_action": "return_to_ai_reviewer_workflow before submission package rebuild",
            "ai_reviewer_request_lifecycle": {
                "request_kind": "return_to_ai_reviewer_workflow",
                "summary": "AI reviewer recheck required",
            },
        }
    )

    compact = compact_pi_action_projection(full)

    assert compact == {
        "surface": "pi_action_projection",
        "schema_version": 1,
        "read_model": "L2_pi_action_projection_read_model",
        "authority": "projection_only",
        "projection_only": True,
        "study_id": "002-revision",
        "primary_category": "进入 AI reviewer",
        "summary": "PI action projection 建议先处理「进入 AI reviewer」，并同步关注：进入 submission package rebuild",
        "categories": [
            {
                "category": "进入 AI reviewer",
                "label": "进入 AI reviewer",
                "recommended_step_id": "enter_ai_reviewer",
                "summary": "进入 AI reviewer-backed 质量、写作或返修闭环，补齐 reviewer provenance。",
                "projection_only": True,
                "can_authorize_publication_readiness": False,
                "can_authorize_submission": False,
                "can_set_canonical_next_action": False,
            },
            {
                "category": "进入 submission package rebuild",
                "label": "进入 submission package rebuild",
                "recommended_step_id": "rebuild_submission_package",
                "summary": "质量与授权面已足够接近交付，下一步从 canonical source 重建投稿包。",
                "projection_only": True,
                "can_authorize_publication_readiness": False,
                "can_authorize_submission": False,
                "can_set_canonical_next_action": False,
            },
        ],
        "authority_contract": {
            "projection_only": True,
            "can_set_canonical_next_action": False,
            "can_authorize_publication_readiness": False,
            "can_authorize_submission": False,
            "can_mutate_runtime": False,
        },
    }


def test_mcp_compact_study_progress_keeps_pi_action_projection() -> None:
    full = {
        "schema_version": 1,
        "study_id": "003-package",
        "current_stage": "manual_finishing",
        "next_system_action": "进入 submission package rebuild",
        "pi_action_projection": build_pi_action_projection(
            {
                "study_id": "003-package",
                "next_system_action": "进入 submission package rebuild",
            }
        ),
    }

    compact = compact_study_progress_projection(full)

    assert compact["pi_action_projection"]["surface"] == "pi_action_projection"
    assert compact["pi_action_projection"]["primary_category"] == "进入 submission package rebuild"
    assert compact["pi_action_projection"]["authority_contract"]["can_authorize_submission"] is False
