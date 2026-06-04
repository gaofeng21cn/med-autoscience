from __future__ import annotations

from collections.abc import Mapping
from typing import Any

DOMAIN_OWNER = "MedAutoScience"
HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF = (
    "agent/knowledge/hypothesis_portfolio_evidence_pack.md"
)
HYPOTHESIS_PORTFOLIO_VALIDATOR_REF = (
    "src/med_autoscience/opl_domain_pack/hypothesis_portfolio_pack.py::"
    "validate_hypothesis_portfolio_candidate_refs"
)
HYPOTHESIS_PORTFOLIO_REQUIRED_REFS = [
    "hypothesis_candidate_ref",
    "assumption_ref",
    "sub_assumption_ref",
    "supporting_evidence_ref",
    "contradicting_evidence_ref",
    "novelty_ref",
    "source_provenance_ref",
    "testability_ref",
    "safety_risk_ref",
    "negative_failed_path_ref",
    "independent_reviewer_or_auditor_receipt_ref",
    "human_gate_receipt_ref",
    "owner_receipt_or_typed_blocker_ref",
]
HYPOTHESIS_PORTFOLIO_ADVISORY_REFS = [
    "ranking_ref",
    "proximity_ref",
    "debate_ref",
    "tournament_ref",
    "evolution_ref",
]
HYPOTHESIS_PORTFOLIO_FORBIDDEN_FAMILY_ACTIONS = [
    "promote_hypothesis_to_route_authority",
    "treat_ranking_or_proximity_as_authority",
    "close_hypothesis_independent_review_gate",
]
HYPOTHESIS_PORTFOLIO_AUTHORITY_FLAGS = {
    "can_authorize_route_by_ranking": False,
    "can_close_hypothesis_independent_review_gate": False,
}
PROMOTION_AUTHORITY_BOUNDARY = {
    "ranking_or_proximity_can_authorize_promotion": False,
    "mas_owner_receipt_or_typed_blocker_required": True,
    "independent_reviewer_or_auditor_receipt_required": True,
    "human_gate_receipt_required": True,
}


def _present_ref(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_present_ref(item) for item in value)
    return True


def validate_hypothesis_portfolio_candidate_refs(
    candidate: Mapping[str, Any],
    *,
    route_back_owner: str = "decision",
) -> dict[str, object]:
    missing_ref_families = [
        ref_family
        for ref_family in HYPOTHESIS_PORTFOLIO_REQUIRED_REFS
        if not _present_ref(candidate.get(ref_family))
    ]
    present_advisory_ref_families = [
        ref_family
        for ref_family in HYPOTHESIS_PORTFOLIO_ADVISORY_REFS
        if _present_ref(candidate.get(ref_family))
    ]
    result: dict[str, object] = {
        "surface_kind": "mas_hypothesis_portfolio_candidate_validation",
        "validator_ref": HYPOTHESIS_PORTFOLIO_VALIDATOR_REF,
        "candidate_id": candidate.get("candidate_id"),
        "status": "validated" if not missing_ref_families else "typed_blocker",
        "can_promote_candidate": not missing_ref_families,
        "required_ref_families": list(HYPOTHESIS_PORTFOLIO_REQUIRED_REFS),
        "advisory_ref_families": list(HYPOTHESIS_PORTFOLIO_ADVISORY_REFS),
        "present_advisory_ref_families": present_advisory_ref_families,
        "missing_ref_families": missing_ref_families,
        "advisory_refs_are_authority": False,
        "promotion_authority_boundary": dict(PROMOTION_AUTHORITY_BOUNDARY),
    }
    if missing_ref_families:
        typed_blocker = {
            "blocker_id": "missing_hypothesis_portfolio_ref_family",
            "blocker_family": "hypothesis_portfolio_missing_required_ref",
            "route_back_owner": route_back_owner,
            "missing_ref_families": missing_ref_families,
            "required_action": "record_missing_refs_or_return_route_back_owner_typed_blocker",
        }
        result.update(
            {
                "blocker_id": typed_blocker["blocker_id"],
                "route_back_owner": route_back_owner,
                "typed_blocker": typed_blocker,
            }
        )
    return result


def build_hypothesis_portfolio_evidence_pack_descriptor() -> dict[str, object]:
    return {
        "surface_kind": "mas_hypothesis_portfolio_evidence_pack_descriptor",
        "schema_version": 1,
        "owner": DOMAIN_OWNER,
        "knowledge_ref": HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF,
        "portfolio_role": "mas_owned_refs_first_hypothesis_candidate_portfolio",
        "candidate_required_refs": list(HYPOTHESIS_PORTFOLIO_REQUIRED_REFS),
        "advisory_only_refs": list(HYPOTHESIS_PORTFOLIO_ADVISORY_REFS),
        "validator_ref": HYPOTHESIS_PORTFOLIO_VALIDATOR_REF,
        "candidate_promotion_requires_validator": True,
        "advisory_refs_are_authority": False,
        "fail_closed_policy": (
            "missing_required_candidate_ref_family_returns_typed_blocker_with_route_back_owner"
        ),
        "authority_boundary": {
            "hypothesis_truth_owner": DOMAIN_OWNER,
            "evidence_interpretation_owner": DOMAIN_OWNER,
            "quality_publication_artifact_authority_owner": DOMAIN_OWNER,
            "ranking_and_proximity_authority": "advisory_only",
            "opl_role": "refs_projection_transport_and_display_only",
            "opl_can_write_hypothesis_truth": False,
            "opl_can_promote_evidence": False,
            "opl_can_authorize_route_by_ranking": False,
            "opl_can_close_independent_review_gate": False,
            "opl_can_authorize_publication_quality": False,
            "opl_can_authorize_artifact_mutation": False,
        },
    }


def build_hypothesis_portfolio_evidence_pack_contract() -> dict[str, object]:
    descriptor = build_hypothesis_portfolio_evidence_pack_descriptor()
    authority = dict(descriptor["authority_boundary"])  # type: ignore[index]
    authority.update(
        {
            "novelty_source_provenance_owner": DOMAIN_OWNER,
            "testability_safety_owner": DOMAIN_OWNER,
            "negative_failed_path_owner": DOMAIN_OWNER,
            "opl_can_accept_novelty": False,
            "opl_can_declare_testability_or_safety": False,
        }
    )
    return {
        "surface_kind": "mas_hypothesis_portfolio_evidence_pack_contract",
        "schema_version": 1,
        "owner": DOMAIN_OWNER,
        "knowledge_ref": HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF,
        "portfolio_role": "mas_owned_hypothesis_candidate_and_evidence_ref_pack",
        "candidate_required_ref_families": list(HYPOTHESIS_PORTFOLIO_REQUIRED_REFS),
        "advisory_ref_families": list(HYPOTHESIS_PORTFOLIO_ADVISORY_REFS),
        "validator_ref": HYPOTHESIS_PORTFOLIO_VALIDATOR_REF,
        "candidate_promotion_requires_validator": True,
        "advisory_refs_are_authority": False,
        "candidate_validation_output_contract": {
            "success_status": "validated",
            "blocked_status": "typed_blocker",
            "can_promote_candidate_requires": "all_required_ref_families_present",
            "missing_required_ref_blocker_id": "missing_hypothesis_portfolio_ref_family",
            "route_back_owner_required_when_blocked": True,
        },
        "advisory_only_fields": [
            "ranking",
            "proximity",
            "elo_like_score",
            "debate_winner",
            "candidate_evolution_order",
        ],
        "fail_closed_missing_ref_policy": (
            "emit_typed_blocker_naming_missing_hypothesis_portfolio_ref_family_and_route_back_owner"
        ),
        "authority_boundary": authority,
    }


def stage_hypothesis_portfolio_evidence_pack_contract() -> dict[str, object]:
    descriptor = build_hypothesis_portfolio_evidence_pack_descriptor()
    return {
        "descriptor_ref": (
            "/product_entry_manifest/family_stage_control_plane_descriptor/"
            "hypothesis_portfolio_evidence_pack"
        ),
        "knowledge_ref": HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF,
        "consumption_boundary": "refs_only_no_body_no_authority_transfer",
        "ranking_and_proximity_authority": "advisory_only",
        "validator_ref": HYPOTHESIS_PORTFOLIO_VALIDATOR_REF,
        "candidate_promotion_requires_validator": True,
        "advisory_refs_are_authority": False,
        "required_ref_families": list(descriptor["candidate_required_refs"]),
        "advisory_ref_families": list(descriptor["advisory_only_refs"]),
        "fail_closed_output_shape": {
            "status": "typed_blocker",
            "blocker_id": "missing_hypothesis_portfolio_ref_family",
            "route_back_owner": "required",
        },
    }
