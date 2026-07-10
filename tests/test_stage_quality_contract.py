from __future__ import annotations

import pytest

from med_autoscience.stage_quality_contract import (
    REQUIRED_STAGE_QUALITY_PACK_IDS,
    STRONG_PROMOTION_EVIDENCE_KINDS,
    build_stage_quality_pack_contract,
)


def _packs() -> dict[str, dict]:
    contract = build_stage_quality_pack_contract()
    assert contract["pack_ids"] == list(REQUIRED_STAGE_QUALITY_PACK_IDS)
    return {pack["pack_id"]: pack for pack in contract["packs"]}


def test_stage_quality_contract_assigns_verdicts_to_independent_reviewers() -> None:
    contract = build_stage_quality_pack_contract()
    boundary = contract["authority_boundary"]

    assert boundary["quality_pack_can_emit_verdict"] is False
    assert boundary["self_review_can_close_quality_gate"] is False
    assert boundary["independent_reviewer_or_auditor_receipt_required"] is True
    assert boundary["same_executor_context_can_satisfy_reviewer"] is False
    assert boundary["truth_owner"] == "MedAutoScience"
    assert boundary["opl_can_write_mas_truth"] is False
    assert boundary["opl_can_authorize_quality_verdict"] is False
    assert boundary["opl_can_authorize_publication_readiness"] is False

    for pack in _packs().values():
        assert pack["role"] == "quality_input_and_reviewer_rubric"
        assert pack["publication_readiness_authority"] is False
        assert pack["quality_verdict_authority"] is False
        assert pack["authority_boundary"]["truth_owner"] == "MedAutoScience"
        assert pack["authority_boundary"]["independent_reviewer_or_auditor_receipt_required"] is True


def test_stable_quality_packs_require_strong_non_documentary_evidence() -> None:
    strong_kinds = set(STRONG_PROMOTION_EVIDENCE_KINDS)

    for pack in _packs().values():
        promotion = pack["promotion_evidence"]
        assert set(promotion["strong_evidence_kinds"]) == strong_kinds
        assert all(item["evidence_kind"] not in {"docs_only", "ordinary_tests"} for item in promotion["evidence"])
        if pack["maturity_status"] == "stable_contract":
            assert promotion["stable_strong_evidence_satisfied"] is True
            assert any(
                item["strength"] == "strong" and item["evidence_kind"] in strong_kinds
                for item in promotion["evidence"]
            )


@pytest.mark.parametrize(
    ("archetype", "guidelines"),
    [
        ("observational_or_cohort_or_registry", ["STROBE"]),
        ("diagnostic_or_prognostic_model", ["TRIPOD", "TRIPOD-AI"]),
        ("randomized_or_intervention", ["CONSORT"]),
        ("systematic_review_or_meta_analysis", ["PRISMA"]),
        ("diagnostic_accuracy", ["STARD"]),
        ("case_report_or_case_series", ["CARE"]),
    ],
)
def test_reporting_guideline_selection_is_owned_by_study_archetype(
    archetype: str,
    guidelines: list[str],
) -> None:
    reporting_pack = _packs()["reporting_guideline_pack"]
    selections = {item["study_archetype"]: item for item in reporting_pack["guideline_selection"]}

    assert selections[archetype]["guideline_families"] == guidelines


def test_ai_ml_reporting_requires_a_clinical_base_guideline() -> None:
    reporting_pack = _packs()["reporting_guideline_pack"]
    selection = next(
        item for item in reporting_pack["guideline_selection"] if item["study_archetype"] == "ai_ml_medical_study"
    )

    assert selection["requires_clinical_base_guideline"] is True
    assert {"STROBE", "TRIPOD", "CONSORT", "PRISMA", "STARD", "CARE"} <= set(
        selection["clinical_base_guideline_options"]
    )
