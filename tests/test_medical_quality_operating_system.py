from __future__ import annotations

import importlib


def test_quality_os_selects_strobe_with_record_overlay_for_real_world_observation() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    contract = module.build_medical_quality_operating_system_contract(
        study_archetype="real_world_data",
        manuscript_family="clinical_observation",
    )

    assert contract["surface"] == "medical_quality_operating_system_contract"
    assert contract["guideline_selection"]["primary_guideline_family"] == "STROBE"
    assert contract["guideline_selection"]["overlay_guideline_families"] == ["RECORD"]
    assert contract["quality_contract"]["owner_surface"] == "study_charter.paper_quality_contract"
    assert contract["quality_contract"]["authority_surfaces"] == {
        "study_charter_owner": "study_charter.paper_quality_contract",
        "evidence_ledger": "paper/evidence_ledger.json",
        "review_ledger": "paper/review_ledger.json",
        "publication_eval": "artifacts/publication_eval/latest.json",
        "reporting_guideline_checklist": "reporting_guideline_checklist.json",
    }
    assert contract["quality_contract"]["first_draft_quality_floor"]["required_before"] == (
        "first_full_draft"
    )
    assert contract["quality_contract"]["stronger_paper_shape_scan"]["status"] == (
        "required_before_first_full_draft"
    )
    assert contract["quality_contract"]["completion_claim_policy"][
        "mechanical_repair_complete_equals_scientific_quality_complete"
    ] is False


def test_quality_os_selects_ai_guidelines_without_record_overlay_when_not_rwd() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    prediction_contract = module.build_medical_quality_operating_system_contract(
        study_archetype="clinical_classifier",
        manuscript_family="ai_prediction_model",
    )
    trial_contract = module.build_medical_quality_operating_system_contract(
        study_archetype="randomized_trial",
        manuscript_family="ai_trial",
    )

    assert prediction_contract["guideline_selection"]["primary_guideline_family"] == "TRIPOD+AI"
    assert prediction_contract["guideline_selection"]["overlay_guideline_families"] == []
    assert trial_contract["guideline_selection"]["primary_guideline_family"] == "CONSORT-AI"
    assert trial_contract["guideline_selection"]["overlay_guideline_families"] == []


def test_quality_os_selects_expected_non_ai_guideline_families() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.medical_quality_operating_system"
    )

    assert module.select_reporting_guideline_families(
        study_archetype="clinical_classifier",
        manuscript_family="prediction_model",
    ) == {
        "primary_guideline_family": "TRIPOD",
        "overlay_guideline_families": [],
    }
    assert module.select_reporting_guideline_families(
        study_archetype="randomized_trial",
        manuscript_family="randomized_trial",
    )["primary_guideline_family"] == "CONSORT"
    assert module.select_reporting_guideline_families(
        study_archetype="systematic_review",
        manuscript_family="systematic_review",
    )["primary_guideline_family"] == "PRISMA"
