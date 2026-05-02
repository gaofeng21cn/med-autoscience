from __future__ import annotations

import importlib

import pytest


pytestmark = pytest.mark.meta


def test_real_paper_ai_first_soak_contract_freezes_observational_schema() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    contract = module.build_real_paper_ai_first_soak_contract()

    assert contract["surface"] == "real_paper_ai_first_soak"
    assert contract["schema_version"] == 1
    assert contract["purpose"] == "measure_ai_first_flow_rework_and_quality"
    assert contract["manual_study_artifact_patch_allowed"] is False
    assert contract["canonical_flow_only"] is True
    assert contract["observational_evidence_only"] is True
    assert contract["quality_gate_relaxation_allowed"] is False
    assert contract["mechanical_ready_can_authorize_quality"] is False
    assert contract["artifact_patch_targets"] == []
    assert [line["paper_id"] for line in contract["paper_lines"]] == [
        "nf-pitnet-003",
        "dpcc-003",
        "dpcc-004",
    ]
    assert contract["evidence_schema"]["required_fields"] == [
        "paper_id",
        "quality_authorization_source",
        "artifact_rebuild_source",
        "route_back_count",
        "route_back_reasons",
        "ai_reviewer_intervention_points",
        "mechanical_ready_overreach_detected",
        "final_blockers",
        "manual_gate",
    ]
    assert contract["authority_requirements"] == {
        "quality_authorization_source": "ai_reviewer_backed_publication_eval_or_manual_gate",
        "artifact_rebuild_source": "canonical_sources_and_ai_reviewer_quality_decision",
        "route_back_reasons": "structured_rework_taxonomy",
        "ai_reviewer_intervention_points": "reviewer_operating_system_trace",
        "manual_gate": "explicit_human_decision",
    }


def test_real_paper_ai_first_soak_recording_entry_is_observational_only() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    observation = module.build_real_paper_ai_first_soak_observation(
        paper_id="nf-pitnet-003",
        quality_authorization_source="artifacts/publication_eval/latest.json",
        artifact_rebuild_source="canonical_sources_and_ai_reviewer_quality_decision",
        route_back_reasons=["medical_prose_review_route_back", "claim_evidence_alignment"],
        ai_reviewer_intervention_points=["pre_draft_readiness", "publication_eval"],
        mechanical_ready_overreach_detected=True,
        final_blockers=["manual_gate_waiting"],
        manual_gate={"required": True, "state": "waiting_for_human_authorization"},
    )

    assert observation["surface"] == "real_paper_ai_first_soak_observation"
    assert observation["paper_id"] == "nf-pitnet-003"
    assert observation["route_back_count"] == 2
    assert observation["manual_study_artifact_patch_allowed"] is False
    assert observation["canonical_flow_only"] is True
    assert observation["observational_evidence_only"] is True
    assert observation["artifact_write_paths"] == []

    validation = module.validate_real_paper_ai_first_soak_observation(observation)

    assert validation["ok"] is True
    assert validation["issues"] == []


def test_real_paper_ai_first_soak_observation_from_runtime_snapshot_extracts_observability_evidence() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    observation = module.build_real_paper_ai_first_soak_observation_from_runtime_snapshot(
        paper_id="dpcc-003",
        runtime_snapshot_bundle={
            "progress_snapshot": {
                "current_blockers": ["manual_gate_waiting"],
                "manual_gate": {"required": True, "state": "waiting_for_human_authorization"},
            },
            "quality_snapshot": {
                "quality_authorization_source": "ai_reviewer_backed_publication_eval_or_manual_gate",
                "route_back_count": 2,
                "route_back_reasons": [
                    "medical_prose_review_route_back",
                    "claim_evidence_alignment",
                ],
                "ai_reviewer_intervention_points": [
                    "pre_draft_readiness",
                    "publication_eval",
                ],
                "mechanical_ready_overreach_detected": True,
                "final_blockers": ["manual_gate_waiting"],
            },
            "artifact_snapshot": {
                "artifact_rebuild_source": "canonical_sources_and_ai_reviewer_quality_decision",
                "current_package_from_canonical_source": True,
            },
            "operations_dashboard_summary": {
                "surface": "ai_first_operations_dashboard_summary",
                "user_view": {
                    "blockers": ["manual_gate_waiting"],
                    "human_review_required": True,
                },
                "maintainer_view": {
                    "ai_reviewer_trace": {"complete": True},
                    "route_back": {"count": 2, "target": "write"},
                    "artifact_stale": {"current_package_from_canonical_source": True},
                },
                "authority": {
                    "observability_can_authorize_quality": False,
                    "observability_can_mutate_runtime": False,
                },
            },
        },
    )

    assert observation["surface"] == "real_paper_ai_first_soak_observation"
    assert observation["paper_id"] == "dpcc-003"
    assert observation["quality_authorization_source"] == (
        "ai_reviewer_backed_publication_eval_or_manual_gate"
    )
    assert observation["artifact_rebuild_source"] == (
        "canonical_sources_and_ai_reviewer_quality_decision"
    )
    assert observation["route_back_count"] == 2
    assert observation["route_back_reasons"] == [
        "medical_prose_review_route_back",
        "claim_evidence_alignment",
    ]
    assert observation["ai_reviewer_intervention_points"] == [
        "pre_draft_readiness",
        "publication_eval",
    ]
    assert observation["mechanical_ready_overreach_detected"] is True
    assert observation["final_blockers"] == ["manual_gate_waiting"]
    assert observation["manual_gate"] == {
        "required": True,
        "state": "waiting_for_human_authorization",
    }
    assert observation["manual_study_artifact_patch_allowed"] is False
    assert observation["canonical_flow_only"] is True
    assert observation["observational_evidence_only"] is True
    assert observation["artifact_write_paths"] == []

    validation = module.validate_real_paper_ai_first_soak_observation(observation)

    assert validation["ok"] is True
    assert validation["issues"] == []


def test_real_paper_ai_first_soak_observation_from_snapshot_fails_closed_when_authority_is_missing() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")

    observation = module.build_real_paper_ai_first_soak_observation_from_runtime_snapshot(
        paper_id="dpcc-004",
        operations_dashboard_summary={
            "surface": "ai_first_operations_dashboard_summary",
            "user_view": {
                "blockers": ["publication_eval_stale"],
                "human_review_required": True,
            },
            "maintainer_view": {
                "ai_reviewer_trace": {"complete": False},
                "route_back": {"count": 1, "target": "ai_reviewer"},
                "artifact_stale": {
                    "stale_artifact_count": 1,
                    "current_package_from_canonical_source": False,
                },
            },
            "authority": {
                "observability_can_authorize_quality": False,
                "observability_can_mutate_runtime": False,
            },
        },
    )

    assert observation["quality_authorization_source"] == "missing_ai_reviewer_quality_authorization"
    assert observation["artifact_rebuild_source"] == "missing_canonical_artifact_rebuild_source"
    assert observation["route_back_count"] == 1
    assert observation["route_back_reasons"] == []
    assert observation["ai_reviewer_intervention_points"] == []
    assert observation["mechanical_ready_overreach_detected"] is False
    assert observation["final_blockers"] == ["publication_eval_stale"]
    assert observation["manual_gate"] == {
        "required": True,
        "state": "human_review_required",
    }

    validation = module.validate_real_paper_ai_first_soak_observation(observation)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "quality_authorization_source_missing",
        "artifact_rebuild_source_not_canonical",
        "route_back_reasons_missing",
        "ai_reviewer_intervention_points_missing",
    }


def test_real_paper_ai_first_soak_validation_rejects_bypass_and_schema_drift() -> None:
    module = importlib.import_module("med_autoscience.controllers.real_paper_ai_first_soak")
    observation = module.build_real_paper_ai_first_soak_observation(
        paper_id="dpcc-003",
        quality_authorization_source="current_package.zip",
        artifact_rebuild_source="submission_minimal",
        route_back_reasons=[],
        ai_reviewer_intervention_points=[],
        mechanical_ready_overreach_detected=False,
        final_blockers=[],
        manual_gate={},
    )
    observation["manual_study_artifact_patch_allowed"] = True
    observation["canonical_flow_only"] = False
    observation["observational_evidence_only"] = False
    observation["artifact_write_paths"] = ["submission_minimal/"]

    validation = module.validate_real_paper_ai_first_soak_observation(observation)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "manual_artifact_patching_enabled",
        "canonical_flow_not_required",
        "observational_evidence_not_enforced",
        "artifact_write_path_present",
        "quality_authority_uses_derived_artifact",
        "artifact_rebuild_source_not_canonical",
        "route_back_reasons_missing",
        "ai_reviewer_intervention_points_missing",
        "manual_gate_missing",
    }
