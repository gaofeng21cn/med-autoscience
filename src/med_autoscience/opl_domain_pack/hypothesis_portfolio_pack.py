from __future__ import annotations

DOMAIN_OWNER = "MedAutoScience"
HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF = (
    "agent/knowledge/hypothesis_portfolio_evidence_pack.md"
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


def build_hypothesis_portfolio_evidence_pack_descriptor() -> dict[str, object]:
    return {
        "surface_kind": "mas_hypothesis_portfolio_evidence_pack_descriptor",
        "schema_version": 1,
        "owner": DOMAIN_OWNER,
        "knowledge_ref": HYPOTHESIS_PORTFOLIO_EVIDENCE_PACK_REF,
        "portfolio_role": "mas_owned_refs_first_hypothesis_candidate_portfolio",
        "candidate_required_refs": list(HYPOTHESIS_PORTFOLIO_REQUIRED_REFS),
        "advisory_only_refs": list(HYPOTHESIS_PORTFOLIO_ADVISORY_REFS),
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
        "required_ref_families": list(descriptor["candidate_required_refs"]),
        "advisory_ref_families": list(descriptor["advisory_only_refs"]),
    }
