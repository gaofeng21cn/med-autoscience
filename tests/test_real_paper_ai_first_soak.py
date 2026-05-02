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
