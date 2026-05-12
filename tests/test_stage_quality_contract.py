from __future__ import annotations

from med_autoscience.stage_quality_contract import (
    REQUIRED_STAGE_QUALITY_PACK_IDS,
    build_stage_quality_pack_contract,
)


def test_stage_quality_contract_defines_required_pack_boundaries_and_refs() -> None:
    contract = build_stage_quality_pack_contract()

    assert contract["surface_kind"] == "mas_stage_quality_pack_contract"
    assert contract["version"] == "mas-stage-quality-pack-contract.v1"
    assert contract["pack_ids"] == list(REQUIRED_STAGE_QUALITY_PACK_IDS)
    assert contract["authority_boundary"] == {
        "pack_role": "quality_input_and_reviewer_rubric",
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "truth_owner": "MedAutoScience",
        "opl_role": "descriptor_ref_freshness_locator_consumer",
        "opl_can_write_mas_truth": False,
        "opl_can_authorize_quality_verdict": False,
        "opl_can_authorize_publication_readiness": False,
    }

    packs = {pack["pack_id"]: pack for pack in contract["packs"]}
    assert set(packs) == set(REQUIRED_STAGE_QUALITY_PACK_IDS)
    for pack_id, pack in packs.items():
        assert pack["pack_id"] == pack_id
        assert pack["role"] == "quality_input_and_reviewer_rubric"
        assert pack["publication_readiness_authority"] is False
        assert pack["quality_verdict_authority"] is False
        assert pack["applies_to"]["stages"]
        assert pack["applies_to"]["study_archetypes"]
        assert pack["authority_boundary"]["truth_owner"] == "MedAutoScience"
        assert pack["authority_boundary"]["can_authorize_publication_readiness"] is False
        assert pack["owner_refs"]
        assert pack["required_refs"]
        assert any(ref["ref_kind"] in {"surface_kind", "workspace_locator", "json_pointer"} for ref in pack["required_refs"])

    assert packs["medical_claim_evidence_pack"]["applies_to"]["stages"] == ["write", "review", "finalize", "decision"]
    assert "paper/evidence/evidence_ledger.json" in {
        ref["ref"] for ref in packs["medical_claim_evidence_pack"]["required_refs"]
    }
    assert packs["human_gate_pack"]["applies_to"]["stages"] == ["all_boundary_changing_stages"]


def test_reporting_guideline_selection_covers_required_families_and_clinical_base_guideline() -> None:
    contract = build_stage_quality_pack_contract()
    reporting_pack = {pack["pack_id"]: pack for pack in contract["packs"]}["reporting_guideline_pack"]
    selections = {
        selection["study_archetype"]: selection for selection in reporting_pack["guideline_selection"]
    }

    assert selections["observational_or_cohort_or_registry"]["guideline_families"] == ["STROBE"]
    assert selections["diagnostic_or_prognostic_model"]["guideline_families"] == ["TRIPOD", "TRIPOD-AI"]
    assert selections["randomized_or_intervention"]["guideline_families"] == ["CONSORT"]
    assert selections["systematic_review_or_meta_analysis"]["guideline_families"] == ["PRISMA"]
    assert selections["diagnostic_accuracy"]["guideline_families"] == ["STARD"]
    assert selections["case_report_or_case_series"]["guideline_families"] == ["CARE"]

    ai_ml = selections["ai_ml_medical_study"]
    assert "AI/ML extension" in ai_ml["guideline_families"]
    assert ai_ml["requires_clinical_base_guideline"] is True
    assert set(ai_ml["clinical_base_guideline_options"]) >= {
        "STROBE",
        "TRIPOD",
        "TRIPOD-AI",
        "CONSORT",
        "PRISMA",
        "STARD",
        "CARE",
    }
