from __future__ import annotations

from copy import deepcopy

import pytest

from med_autoscience.policies.publication_critique import (
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_ai_reviewer_operating_system_contract,
    build_revision_action_contract,
    build_weight_contract,
)


def test_publication_critique_policy_owns_scoring_and_revision_actions() -> None:
    policy = DEFAULT_PUBLICATION_CRITIQUE_POLICY

    assert build_weight_contract(policy) == {
        "clinical_significance": 25,
        "evidence_strength": 30,
        "novelty_positioning": 20,
        "medical_journal_prose_quality": 15,
        "human_review_readiness": 10,
    }
    assert build_revision_action_contract(policy) == (
        "tighten_clinical_framing",
        "close_evidence_gap",
        "tighten_novelty_framing",
        "refresh_review_surface",
        "stabilize_submission_bundle",
    )


def test_ai_reviewer_contract_is_the_quality_authority_boundary() -> None:
    contract = build_ai_reviewer_operating_system_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)

    assert contract["owner"] == "ai_reviewer"
    assert contract["mechanical_projection_can_authorize_quality"] is False
    assert contract["required_provenance"] == {
        "assessment_owner": "ai_reviewer",
        "policy_id": "medical_publication_critique_v1",
        "ai_reviewer_required": False,
    }
    assert contract["ai_native_expert_judgment"]["role"] == "primary_quality_signal"
    assert contract["ai_native_expert_judgment"]["contracts_are_floor_not_ceiling"] is True
    assert {
        "future_facing_limitations_plan",
        "revision_delta_audit",
    } <= set(contract["required_trace_fields"])
    assert contract["revision_delta_audit"]["discipline"][
        "unresolved_hard_items_must_route_to_owner_or_human_gate"
    ] is True


@pytest.mark.parametrize(
    "missing_field",
    [
        "ai_native_expert_judgment",
        "future_facing_limitations_plan",
        "revision_delta_audit",
    ],
)
def test_ai_reviewer_contract_fails_closed_when_authority_trace_is_incomplete(
    missing_field: str,
) -> None:
    policy = deepcopy(DEFAULT_PUBLICATION_CRITIQUE_POLICY)
    policy["ai_reviewer_operating_system"].pop(missing_field)

    with pytest.raises(ValueError, match=missing_field):
        build_ai_reviewer_operating_system_contract(policy)


def test_registry_quality_floor_cannot_be_cleared_by_wording_alone() -> None:
    contract = build_ai_reviewer_operating_system_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)
    floor = contract["sci_clinical_registry_review"]["registry_initial_draft_quality_floor"]

    assert floor["any_red_flag_requires_major_or_blocker_row"] is True
    assert floor["cannot_be_cleared_by_restrained_wording_alone"] is True


from tests.test_quality_repair_batch_cases.upstream_paper_owner_surface import (
    test_canonical_paper_owner_surface_rejects_untrusted_projection,
    test_quality_repair_batch_routes_to_producer_and_materializes_owner_delta,
)
