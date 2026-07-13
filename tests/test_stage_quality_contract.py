from __future__ import annotations

from med_autoscience.stage_quality_contract import (
    REQUIRED_STAGE_QUALITY_PACK_IDS,
    STRONG_PROMOTION_EVIDENCE_KINDS,
    build_stage_quality_pack_contract,
)


def test_stage_quality_packs_are_non_authority_and_require_strong_evidence() -> None:
    contract = build_stage_quality_pack_contract()
    boundary = contract["authority_boundary"]

    assert contract["pack_ids"] == list(REQUIRED_STAGE_QUALITY_PACK_IDS)
    assert {pack["pack_id"] for pack in contract["packs"]} == set(REQUIRED_STAGE_QUALITY_PACK_IDS)
    assert boundary["quality_pack_can_emit_verdict"] is False
    assert boundary["self_review_can_close_quality_gate"] is False
    assert boundary["same_executor_context_can_satisfy_reviewer"] is False
    assert boundary["independent_reviewer_or_auditor_receipt_required"] is True
    assert boundary["truth_owner"] == "MedAutoScience"
    assert boundary["opl_can_write_mas_truth"] is False
    assert boundary["opl_can_authorize_quality_verdict"] is False
    assert boundary["opl_can_authorize_publication_readiness"] is False

    strong_kinds = set(STRONG_PROMOTION_EVIDENCE_KINDS)
    for pack in contract["packs"]:
        assert pack["role"] == "quality_input_and_reviewer_rubric"
        assert pack["publication_readiness_authority"] is False
        assert pack["quality_verdict_authority"] is False
        promotion = pack["promotion_evidence"]
        assert set(promotion["strong_evidence_kinds"]) == strong_kinds
        if pack["maturity_status"] == "stable_contract":
            assert promotion["stable_strong_evidence_satisfied"] is True
            assert any(
                item["strength"] == "strong"
                and item["evidence_kind"] in strong_kinds
                for item in promotion["evidence"]
            )


def test_computational_biomechanics_receives_domain_quality_packs() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}

    for pack_id in (
        "statistical_analysis_pack",
        "statistical_reporting_pack",
        "reporting_guideline_pack",
        "display_to_claim_pack",
        "route_memory_pack",
        "stop_loss_pack",
    ):
        assert "computational_biomechanics" in packs[pack_id]["applies_to"]["study_archetypes"]

    selection = packs["reporting_guideline_pack"]["guideline_selection"]
    computational = next(
        item for item in selection if item["study_archetype"] == "computational_biomechanics"
    )
    assert computational["guideline_families"] == ["COMPUTATIONAL_BIOMECHANICS"]
