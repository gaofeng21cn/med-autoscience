from __future__ import annotations

import pytest

from med_autoscience.controllers.supervisor_action_requests import (
    build_ai_reviewer_publication_eval_request,
    build_publication_gate_specificity_request,
)
from med_autoscience.controllers.supervisor_action_request_lifecycle import (
    default_ai_reviewer_request_input_refs,
    materialize_ai_reviewer_request,
    project_ai_reviewer_request_lifecycle,
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
    assert packet["quality_gate_relaxation_allowed"] is False
    assert packet["paper_package_mutation_allowed"] is False
    assert packet["manual_study_patch_allowed"] is False
    assert packet["paper_patch_allowed"] is False
    assert packet["current_package_patch_allowed"] is False
    assert packet["medical_claim_authoring_allowed"] is False
    assert packet["medical_conclusion_allowed"] is False
    assert packet["forbidden_actions"] == [
        "paper_package_mutation",
        "manual_study_patch",
        "quality_gate_relaxation",
        "medical_claim_authoring",
    ]
    assert packet["target_requirements"] == {
        "claim_targets_required": True,
        "figure_targets_required": True,
        "table_targets_required": True,
        "metric_targets_required": True,
        "source_path_targets_required": True,
    }
    assert packet["requested_target_types"] == ["claim", "figure", "table", "metric", "source_path"]
    assert packet["missing_target_kinds"] == ["claim", "figure", "table", "metric", "source_path"]
    assert packet["requested_targets"] == []
    assert packet["gate_owner"] == "publication_gate"
    assert packet["next_controller_write"] == {
        "surface": "publication_eval/latest.json",
        "writer": "publication_gate_controller",
        "materialization_mode": "controller_request_only",
        "required_fields": [
            "recommended_actions[].specificity_targets[].target_kind",
            "recommended_actions[].specificity_targets[].target_id",
            "recommended_actions[].specificity_targets[].source_path",
            "recommended_actions[].specificity_targets[].blocking_reason",
        ],
        "must_include_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
        "forbidden_materializations": [
            "manuscript_patch",
            "current_package_patch",
            "paper_package_mutation",
        ],
    }
    assert [item["target_kind"] for item in packet["owner_visible_checklist"]] == [
        "claim",
        "figure",
        "table",
        "metric",
        "source_path",
    ]
    assert {item["owner"] for item in packet["owner_visible_checklist"]} == {"publication_gate"}
    assert {item["status"] for item in packet["owner_visible_checklist"]} == {"missing"}
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


def test_ai_reviewer_default_input_refs_use_existing_draft_manuscript_source(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "003-nf"
    paper_root = study_root / "paper"
    paper_root.mkdir(parents=True)
    (paper_root / "draft.md").write_text("# Draft\n\nCurrent canonical manuscript.\n", encoding="utf-8")
    (paper_root / "medical_manuscript_blueprint.json").write_text('{"schema_version":1}\n', encoding="utf-8")
    (paper_root / "claim_evidence_map.json").write_text('{"claims":[]}\n', encoding="utf-8")
    (study_root / "artifacts" / "publication_eval").mkdir(parents=True)
    (study_root / "artifacts" / "publication_eval" / "medical_prose_review.json").write_text(
        '{"schema_version":1}\n',
        encoding="utf-8",
    )
    (study_root / "artifacts" / "publication_eval" / "latest.json").write_text(
        '{"schema_version":1}\n',
        encoding="utf-8",
    )

    refs = default_ai_reviewer_request_input_refs(study_root=study_root)

    assert refs["manuscript"]["relative_path"] == "paper/draft.md"
    assert refs["manuscript"]["present"] is True
    assert refs["manuscript"]["valid"] is True
    assert refs["medical_manuscript_blueprint"]["relative_path"] == "paper/medical_manuscript_blueprint.json"
    assert refs["claim_evidence_map"]["relative_path"] == "paper/claim_evidence_map.json"
    assert refs["medical_prose_review"]["relative_path"] == "artifacts/publication_eval/medical_prose_review.json"
    assert refs["publication_gate_projection"]["relative_path"] == "artifacts/publication_eval/latest.json"


def test_ai_reviewer_default_input_refs_fall_back_to_paper_medical_prose_review(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "obesity-atlas"
    paper_root = study_root / "paper"
    paper_root.mkdir(parents=True)
    (paper_root / "draft.md").write_text("# Draft\n\nCurrent canonical manuscript.\n", encoding="utf-8")
    (paper_root / "medical_prose_review.json").write_text('{"schema_version":1}\n', encoding="utf-8")

    refs = default_ai_reviewer_request_input_refs(study_root=study_root)

    assert refs["medical_prose_review"]["relative_path"] == "paper/medical_prose_review.json"
    assert refs["medical_prose_review"]["present"] is True
    assert refs["medical_prose_review"]["valid"] is True


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
    assert packet["quality_gate_relaxation_allowed"] is False
    assert packet["paper_package_mutation_allowed"] is False
    assert packet["manual_study_patch_allowed"] is False
    assert packet["paper_patch_allowed"] is False
    assert packet["current_package_patch_allowed"] is False
    assert packet["medical_claim_authoring_allowed"] is False
    assert packet["medical_conclusion_allowed"] is False
    assert packet["forbidden_actions"] == [
        "paper_package_mutation",
        "manual_study_patch",
        "quality_gate_relaxation",
        "medical_claim_authoring",
    ]
    assert packet["required_publication_eval_provenance"] == {
        "owner": "ai_reviewer",
        "source_kind": "publication_eval_ai_reviewer",
        "policy_id": "medical_publication_critique_v1",
        "ai_reviewer_required": False,
    }
    assert packet["request_lifecycle"] == {
        "state": "requested",
        "allowed_states": ["requested", "assigned", "assessment_written", "blocked", "stale"],
        "assigned_to": None,
        "assessment_ref": None,
        "blocked_reason": None,
        "authority": "observability_only",
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
    }
    assert packet["input_contract"]["required_surfaces"] == [
        "manuscript",
        "evidence_ledger",
        "review_ledger",
        "study_charter",
        "medical_manuscript_blueprint",
        "claim_evidence_map",
        "medical_prose_review",
        "publication_gate_projection",
    ]
    assert packet["input_contract"]["all_required_refs_present"] is False
    assert packet["required_output"] == {
        "surface": "publication_eval/latest.json",
        "writer": "ai_reviewer_publication_eval_workflow",
        "owner": "ai_reviewer",
        "source_kind": "publication_eval_ai_reviewer",
        "writeback_required": True,
        "assessment_written_lifecycle_state": "assessment_written",
        "pre_writeback_authority": "observability_only",
        "pre_writeback_can_authorize_quality": False,
        "pre_writeback_can_authorize_finalize": False,
        "pre_writeback_can_authorize_submission": False,
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


def test_ai_reviewer_request_accepts_required_input_refs_and_lifecycle_assignment() -> None:
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="ai_reviewer_runtime_workflow_state",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
            "blockers": ["publication_eval_not_ai_reviewer_authority"],
        },
        input_refs={
            "manuscript": {"relative_path": "paper/manuscript.md"},
            "evidence_ledger": {"relative_path": "paper/evidence_ledger.json"},
            "review_ledger": {"relative_path": "paper/review/review_ledger.json"},
            "study_charter": {"relative_path": "artifacts/controller/study_charter.json"},
            "medical_manuscript_blueprint": {"relative_path": "paper/medical_manuscript_blueprint.json"},
            "claim_evidence_map": {"relative_path": "paper/claim_evidence_map.json"},
            "medical_prose_review": {"relative_path": "artifacts/publication_eval/medical_prose_review.json"},
            "publication_gate_projection": {"relative_path": "artifacts/publication_eval/latest.json"},
        },
        lifecycle_state="assigned",
        assigned_to="ai_reviewer",
    )

    assert packet["request_lifecycle"]["state"] == "assigned"
    assert packet["request_lifecycle"]["assigned_to"] == "ai_reviewer"
    assert packet["input_contract"]["all_required_refs_present"] is True
    assert packet["input_contract"]["missing_or_invalid_refs"] == []
    assert set(packet["input_contract"]["required_refs"]) == {
        "manuscript",
        "evidence_ledger",
        "review_ledger",
        "study_charter",
        "medical_manuscript_blueprint",
        "claim_evidence_map",
        "medical_prose_review",
        "publication_gate_projection",
    }
    assert packet["authority"] == "observability_only"
    assert packet["can_clear_quality_gate"] is False
    assert packet["required_output"]["pre_writeback_can_authorize_quality"] is False


def test_ai_reviewer_request_lifecycle_projects_blocked_and_assessment_written(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    blocked_packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="ai_reviewer_runtime_workflow_state",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
            "blockers": ["publication_eval_not_ai_reviewer_authority"],
        },
    )
    materialize_ai_reviewer_request(study_root=study_root, packet=blocked_packet)

    blocked = project_ai_reviewer_request_lifecycle(study_root=study_root)
    assert blocked is not None
    assert blocked["state"] == "blocked"
    assert blocked["authority"] == "observability_only"
    assert blocked["can_authorize_quality"] is False
    assert "manuscript_ref_missing" in blocked["blockers"]

    assigned_packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="ai_reviewer_runtime_workflow_state",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
            "blockers": ["publication_eval_not_ai_reviewer_authority"],
        },
        input_refs={
            "manuscript": {"relative_path": "paper/manuscript.md"},
            "evidence_ledger": {"relative_path": "paper/evidence_ledger.json"},
            "review_ledger": {"relative_path": "paper/review/review_ledger.json"},
            "study_charter": {"relative_path": "artifacts/controller/study_charter.json"},
        },
        lifecycle_state="assigned",
        assigned_to="ai_reviewer",
    )
    materialize_ai_reviewer_request(study_root=study_root, packet=assigned_packet)

    assessment_written = project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload={
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "ai_reviewer_required": False,
            }
        },
    )
    assert assessment_written is not None
    assert assessment_written["state"] == "assessment_written"
    assert assessment_written["requested_state"] == "assigned"
    assert assessment_written["assessment_written"] is True
    assert assessment_written["required_output"]["surface"] == "publication_eval/latest.json"
    assert assessment_written["can_authorize_finalize"] is False


def test_ai_reviewer_request_lifecycle_resolves_stale_eval_review_ref_to_paper_review(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "obesity-atlas"
    paper_root = study_root / "paper"
    (paper_root / "review").mkdir(parents=True)
    (paper_root / "draft.md").write_text("# Draft\n\nCurrent canonical manuscript.\n", encoding="utf-8")
    (paper_root / "evidence_ledger.json").write_text('{"schema_version":1}\n', encoding="utf-8")
    (paper_root / "review" / "review_ledger.json").write_text('{"schema_version":1}\n', encoding="utf-8")
    (paper_root / "medical_manuscript_blueprint.json").write_text('{"schema_version":1}\n', encoding="utf-8")
    (paper_root / "claim_evidence_map.json").write_text('{"schema_version":1}\n', encoding="utf-8")
    (paper_root / "medical_prose_review.json").write_text('{"schema_version":1}\n', encoding="utf-8")
    (study_root / "artifacts" / "controller").mkdir(parents=True)
    (study_root / "artifacts" / "controller" / "study_charter.json").write_text(
        '{"schema_version":1}\n',
        encoding="utf-8",
    )
    (study_root / "artifacts" / "publication_eval").mkdir(parents=True)
    (study_root / "artifacts" / "publication_eval" / "latest.json").write_text(
        '{"schema_version":1}\n',
        encoding="utf-8",
    )
    input_refs = default_ai_reviewer_request_input_refs(study_root=study_root)
    input_refs["medical_prose_review"] = {
        "surface": "medical_prose_review",
        "path": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "relative_path": "artifacts/publication_eval/medical_prose_review.json",
        "required": True,
        "present": False,
        "valid": False,
    }
    packet = build_ai_reviewer_publication_eval_request(
        study_id="obesity-atlas",
        quest_id="quest-obesity",
        source_surface="quality_repair_batch",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "review_required"},
            "route_back": {"required": True, "target": "ai_reviewer"},
            "blockers": ["ai_reviewer_recheck_required"],
        },
        input_refs=input_refs,
    )
    materialize_ai_reviewer_request(study_root=study_root, packet=packet)

    lifecycle = project_ai_reviewer_request_lifecycle(study_root=study_root)

    assert lifecycle is not None
    assert lifecycle["state"] == "requested"
    assert "medical_prose_review_missing" not in lifecycle["blockers"]
    assert "medical_prose_review" not in lifecycle["input_contract"]["missing_or_invalid_refs"]
    assert (
        lifecycle["input_contract"]["required_refs"]["medical_prose_review"]["relative_path"]
        == "paper/medical_prose_review.json"
    )


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


def test_ai_reviewer_request_rejects_unknown_lifecycle_state() -> None:
    with pytest.raises(ValueError, match="request_lifecycle.state must be one of"):
        build_ai_reviewer_publication_eval_request(
            study_id="002-risk",
            quest_id="quest-002",
            source_surface="ai_reviewer_runtime_workflow_state",
            workflow_state={"quality_authority": {}, "route_back": {}},
            lifecycle_state="ready",
        )
