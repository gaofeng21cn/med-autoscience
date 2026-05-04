from __future__ import annotations

import pytest

from med_autoscience.controllers.supervisor_action_requests import (
    build_ai_reviewer_publication_eval_request,
    build_publication_gate_specificity_request,
)


def test_publication_gate_specificity_request_packet_names_required_target_types() -> None:
    packet = build_publication_gate_specificity_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="publication_eval/latest.json",
        source_action={
            "action_id": "publication-eval-action::return_to_controller::publication-blockers::specificity",
            "reason": "Gate only named generic blocker labels.",
            "work_unit_fingerprint": "publication-blockers::specificity",
            "next_work_unit": {
                "unit_id": "gate_needs_specificity",
                "lane": "controller",
                "summary": "Ask the publication gate to identify concrete blocker targets.",
            },
        },
        blocking_gaps=[
            {
                "gap_id": "gap-005",
                "gap_type": "claim",
                "summary": "claim_evidence_consistency_failed",
                "evidence_refs": ["artifacts/reports/publishability_gate/latest.json"],
            }
        ],
    )

    assert packet["surface"] == "supervisor_action_request"
    assert packet["request_id"] == "publication_gate_specificity_required::002-risk::quest-002"
    assert packet["request_kind"] == "publication_gate_specificity_required"
    assert packet["authority"] == "observability_only"
    assert packet["authoritative"] is False
    assert packet["can_clear_quality_gate"] is False
    assert packet["manual_study_patch_allowed"] is False
    assert packet["paper_patch_allowed"] is False
    assert packet["current_package_patch_allowed"] is False
    assert packet["medical_conclusion_allowed"] is False
    assert packet["target_requirements"] == {
        "claim_targets_required": True,
        "figure_targets_required": True,
        "table_targets_required": True,
        "metric_targets_required": True,
        "source_path_targets_required": True,
    }
    assert packet["requested_target_types"] == ["claim", "figure", "table", "metric", "source_path"]
    assert packet["requested_targets"] == []
    assert packet["source_action_ref"] == {
        "action_id": "publication-eval-action::return_to_controller::publication-blockers::specificity",
        "work_unit_id": "gate_needs_specificity",
        "work_unit_fingerprint": "publication-blockers::specificity",
        "source_surface": "publication_eval/latest.json",
    }
    assert packet["blocking_gap_refs"] == [
        {
            "gap_id": "gap-005",
            "gap_type": "claim",
            "summary": "claim_evidence_consistency_failed",
            "evidence_refs": ["artifacts/reports/publishability_gate/latest.json"],
        }
    ]
    assert "claim/figure/table/metric/source_path" in packet["request_summary"]


def test_ai_reviewer_publication_eval_request_packet_is_reviewer_owned_without_authority() -> None:
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="ai_reviewer_runtime_workflow_state",
        workflow_state={
            "quality_authority": {
                "owner": "mechanical_projection",
                "state": "projection_only",
                "policy_id": "publication_gate_projection_v1",
                "ai_reviewer_required": True,
                "mechanical_projection_can_authorize_quality": False,
            },
            "route_back": {
                "required": True,
                "target": "ai_reviewer",
                "reason": "Mechanical publication eval cannot authorize finalize/submission quality closure.",
                "source": "publication_eval",
            },
            "blockers": ["publication_eval_not_ai_reviewer_authority"],
            "refs": {
                "publication_eval": {
                    "relative_path": "artifacts/publication_eval/latest.json",
                    "present": True,
                    "valid": True,
                }
            },
        },
    )

    assert packet["request_kind"] == "return_to_ai_reviewer_workflow"
    assert packet["request_owner"] == "ai_reviewer"
    assert packet["authority"] == "observability_only"
    assert packet["authoritative"] is False
    assert packet["can_clear_quality_gate"] is False
    assert packet["manual_study_patch_allowed"] is False
    assert packet["paper_patch_allowed"] is False
    assert packet["current_package_patch_allowed"] is False
    assert packet["medical_conclusion_allowed"] is False
    assert packet["required_publication_eval_provenance"] == {
        "owner": "ai_reviewer",
        "source_kind": "publication_eval_ai_reviewer",
        "policy_id": "medical_publication_critique_v1",
        "ai_reviewer_required": False,
    }
    assert packet["requested_artifact"] == {
        "surface": "publication_eval/latest.json",
        "writer": "ai_reviewer_publication_eval_workflow",
        "materialization_mode": "request_only",
    }
    assert packet["source_workflow_ref"] == {
        "surface": "ai_reviewer_runtime_workflow_state",
        "authority_owner": "mechanical_projection",
        "authority_state": "projection_only",
        "route_back_required": True,
        "route_back_target": "ai_reviewer",
    }
    assert packet["blockers"] == ["publication_eval_not_ai_reviewer_authority"]


def test_request_builder_rejects_prepopulated_specificity_targets() -> None:
    with pytest.raises(ValueError, match="request packet must not prepopulate gate specificity targets"):
        build_publication_gate_specificity_request(
            study_id="002-risk",
            quest_id="quest-002",
            source_surface="publication_eval/latest.json",
            source_action={"action_id": "action-1"},
            blocking_gaps=[],
            requested_targets=[{"target_type": "claim", "target_id": "claim-1"}],
        )
