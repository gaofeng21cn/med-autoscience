from __future__ import annotations

from med_autoscience.opl_domain_pack import hypothesis_portfolio_pack as portfolio_pack
from med_autoscience.opl_domain_pack.hypothesis_portfolio_pack import (
    HYPOTHESIS_PORTFOLIO_ADVISORY_REFS,
    HYPOTHESIS_PORTFOLIO_PROGRESS_ENHANCEMENT_REFS,
    HYPOTHESIS_PORTFOLIO_REQUIRED_REFS,
    build_hypothesis_portfolio_evidence_pack_contract,
    build_hypothesis_portfolio_evidence_pack_descriptor,
    stage_hypothesis_portfolio_evidence_pack_contract,
)


VALIDATOR_REF = (
    "src/med_autoscience/opl_domain_pack/hypothesis_portfolio_pack.py::"
    "validate_hypothesis_portfolio_candidate_refs"
)


def _complete_candidate() -> dict[str, object]:
    return {
        "candidate_id": "candidate-001",
        "study_id": "study-001",
        "quest_id": "quest-001",
        "route_stage": "idea",
        "currentness_basis": "controller_decisions/latest.json",
        **{ref: f"refs/{ref}.json" for ref in HYPOTHESIS_PORTFOLIO_REQUIRED_REFS},
        "ranking_ref": "refs/ranking.json",
        "proximity_ref": "refs/proximity.json",
    }


def _validate_candidate(candidate: dict[str, object], **kwargs: object) -> dict[str, object]:
    validator = getattr(portfolio_pack, "validate_hypothesis_portfolio_candidate_refs", None)
    assert callable(validator), "hypothesis portfolio validator must be exposed"
    return validator(candidate, **kwargs)


def test_hypothesis_portfolio_candidate_can_promote_only_with_required_refs() -> None:
    result = _validate_candidate(_complete_candidate())

    assert result["status"] == "validated"
    assert result["can_promote_candidate"] is True
    assert result["missing_ref_families"] == []
    assert result["required_ref_families"] == HYPOTHESIS_PORTFOLIO_REQUIRED_REFS
    assert result["advisory_ref_families"] == HYPOTHESIS_PORTFOLIO_ADVISORY_REFS
    assert result["advisory_refs_are_authority"] is False
    assert result["promotion_authority_boundary"] == {
        "ranking_or_proximity_can_authorize_promotion": False,
        "mas_owner_receipt_or_typed_blocker_required": True,
        "independent_reviewer_or_auditor_receipt_required": True,
        "human_gate_receipt_required": True,
    }


def test_hypothesis_portfolio_candidate_missing_required_refs_fails_closed() -> None:
    candidate = _complete_candidate()
    for ref in (
        "supporting_evidence_ref",
        "contradicting_evidence_ref",
        "novelty_ref",
        "independent_reviewer_or_auditor_receipt_ref",
        "owner_receipt_or_typed_blocker_ref",
    ):
        candidate.pop(ref)

    result = _validate_candidate(
        candidate,
        route_back_owner="idea",
    )

    assert result["status"] == "typed_blocker"
    assert result["can_promote_candidate"] is False
    assert result["blocker_id"] == "missing_hypothesis_portfolio_ref_family"
    assert result["route_back_owner"] == "idea"
    assert result["missing_ref_families"] == [
        "supporting_evidence_ref",
        "contradicting_evidence_ref",
        "novelty_ref",
        "independent_reviewer_or_auditor_receipt_ref",
        "owner_receipt_or_typed_blocker_ref",
    ]
    assert result["typed_blocker"] == {
        "blocker_id": "missing_hypothesis_portfolio_ref_family",
        "blocker_family": "hypothesis_portfolio_missing_required_ref",
        "route_back_owner": "idea",
        "missing_ref_families": result["missing_ref_families"],
        "required_action": "record_missing_refs_or_return_route_back_owner_typed_blocker",
    }


def test_advisory_refs_never_authorize_hypothesis_promotion() -> None:
    result = _validate_candidate(
        {
            "candidate_id": "candidate-advisory-only",
            "ranking_ref": "refs/ranking.json",
            "proximity_ref": "refs/proximity.json",
            "debate_ref": "refs/debate.json",
            "tournament_ref": "refs/tournament.json",
            "evolution_ref": "refs/evolution.json",
        },
        route_back_owner="decision",
    )

    assert result["status"] == "typed_blocker"
    assert result["can_promote_candidate"] is False
    assert result["advisory_refs_are_authority"] is False
    assert result["present_advisory_ref_families"] == HYPOTHESIS_PORTFOLIO_ADVISORY_REFS
    assert result["blocker_id"] == "missing_hypothesis_portfolio_ref_family"
    assert set(result["missing_ref_families"]) == set(HYPOTHESIS_PORTFOLIO_REQUIRED_REFS)


def test_missing_progress_enhancement_refs_do_not_block_complete_candidate() -> None:
    candidate = _complete_candidate()

    result = _validate_candidate(candidate)

    assert result["status"] == "validated"
    assert result["can_promote_candidate"] is True
    assert result["progress_enhancement_ref_families"] == HYPOTHESIS_PORTFOLIO_PROGRESS_ENHANCEMENT_REFS
    assert result["present_progress_enhancement_ref_families"] == []
    assert result["missing_progress_enhancement_ref_families"] == HYPOTHESIS_PORTFOLIO_PROGRESS_ENHANCEMENT_REFS
    assert result["progress_enhancement_refs_block_route"] is False
    assert result["progress_enhancement_authority_boundary"] == {
        "missing_progress_enhancement_ref_blocks_route": False,
        "next_delta_tournament_authorizes_next_attempt_only": True,
        "micro_candidates_can_block_selected_owner_action": False,
        "critique_hint_can_close_quality_gate": False,
        "memory_lesson_body_required": False,
        "meta_review_runs_every_attempt": False,
        "opportunistic_prefetch_blocks_mainline": False,
    }


def test_progress_enhancement_authority_leak_fails_closed() -> None:
    candidate = _complete_candidate()
    candidate.update(
        {
            "next_delta_tournament_ref": "refs/route-option-board.json",
            "micro_candidate_board_ref": "refs/micro-candidates.json",
            "progress_enhancement_authority": {
                "closes_quality_gate": True,
                "counts_prefetch_as_paper_progress": True,
            },
        }
    )

    result = _validate_candidate(candidate, route_back_owner="decision")

    assert result["status"] == "typed_blocker"
    assert result["can_promote_candidate"] is False
    assert result["blocker_id"] == "progress_enhancement_authority_leak"
    assert result["forbidden_authority_claims"] == [
        "closes_quality_gate",
        "counts_prefetch_as_paper_progress",
    ]
    assert result["typed_blocker"] == {
        "blocker_id": "progress_enhancement_authority_leak",
        "blocker_family": "progress_enhancement_must_remain_advisory",
        "route_back_owner": "decision",
        "forbidden_authority_claims": result["forbidden_authority_claims"],
        "required_action": "remove_authority_claim_or_return_route_back_owner_typed_blocker",
    }


def test_hypothesis_portfolio_contract_exposes_fail_closed_validator() -> None:
    descriptor = build_hypothesis_portfolio_evidence_pack_descriptor()
    contract = build_hypothesis_portfolio_evidence_pack_contract()
    stage_contract = stage_hypothesis_portfolio_evidence_pack_contract()

    for surface in (descriptor, contract, stage_contract):
        assert surface["validator_ref"] == VALIDATOR_REF
        assert surface["candidate_promotion_requires_validator"] is True
        assert surface["advisory_refs_are_authority"] is False
        assert surface["progress_enhancement_refs_block_route"] is False

    assert contract["candidate_validation_output_contract"] == {
        "success_status": "validated",
        "blocked_status": "typed_blocker",
        "can_promote_candidate_requires": "all_required_ref_families_present",
        "missing_required_ref_blocker_id": "missing_hypothesis_portfolio_ref_family",
        "route_back_owner_required_when_blocked": True,
    }
    assert contract["progress_enhancement_contract"] == {
        "role": "advisory_progress_accelerator",
        "missing_progress_enhancement_ref_blocks_route": False,
        "max_reusable_memory_lesson_refs_per_attempt": 1,
        "meta_review_triggered_only_by": [
            "stop_loss_candidate",
            "repeated_failure",
            "human_gate_pressure",
            "claim_boundary_drift",
            "no_loop_budget_exhausted",
        ],
        "opportunistic_prefetch_blocks_mainline": False,
    }
    assert stage_contract["fail_closed_output_shape"] == {
        "status": "typed_blocker",
        "blocker_id": "missing_hypothesis_portfolio_ref_family",
        "route_back_owner": "required",
    }
