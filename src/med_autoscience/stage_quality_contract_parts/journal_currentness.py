from __future__ import annotations


LITERATURE_SEARCH_SOURCE_PACKS: tuple[str, ...] = (
    "citation_integrity_pack",
    "paper_reader_grounding_pack",
)

JOURNAL_POLICY_CURRENTNESS_PACKS: tuple[str, ...] = (
    "journal_response_pack",
    "data_availability_fair_pack",
    "citation_integrity_pack",
)


def build_literature_search_source_pack() -> dict[str, object]:
    return {
        "source_tiers": [
            {
                "tier": "T1",
                "role": "official_structured_source",
                "examples": ["PubMed", "CrossRef", "arXiv"],
                "may_authorize_quality_verdict": False,
            },
            {
                "tier": "T2",
                "role": "limited_structured_discovery_source",
                "examples": ["Semantic Scholar", "bioRxiv", "medRxiv"],
                "may_authorize_quality_verdict": False,
            },
            {
                "tier": "T3",
                "role": "manual_or_unstable_discovery_only",
                "examples": ["Google Scholar", "Web of Science", "Scopus", "CNKI", "WanFang"],
                "may_authorize_quality_verdict": False,
            },
        ],
        "search_strategy_fields": [
            "domain_route",
            "mesh_terms_or_reason_not_applicable",
            "keyword_queries",
            "source_tier_attempts",
            "deduplication_basis",
            "search_checked_at",
            "search_expires_or_stale_after",
        ],
        "multi_source_search_required": True,
        "mesh_strategy_required_for_biomedical_claims": True,
        "insufficient_source_behavior": "typed_blocker_or_reference_only",
        "may_authorize_quality_verdict": False,
        "may_authorize_publication_readiness": False,
    }


def build_journal_policy_currentness_pack() -> dict[str, object]:
    return {
        "official_policy_refs_required": True,
        "required_policy_ref_fields": [
            "journal_or_publisher",
            "official_policy_url_or_locator",
            "policy_scope",
            "checked_at",
            "expires_or_stale_after",
            "currentness_state",
            "blocker_ref_if_missing_or_stale",
        ],
        "currentness_states": ["current", "stale", "missing", "manual_verification_required"],
        "missing_or_stale_policy_ref_behavior": "blocker_or_reference_only",
        "forbidden_outputs_without_current_official_refs": [
            "publication_readiness",
            "quality_verdict",
            "submission_readiness",
        ],
        "may_authorize_quality_verdict": False,
        "may_authorize_publication_readiness": False,
    }


def build_citation_verification_pack() -> dict[str, object]:
    return {
        "verification_output_fields": [
            "claim_segment_id",
            "citation_ref",
            "identifier_refs",
            "source_tier",
            "metadata_match_state",
            "support_grade",
            "evidence_basis",
            "checked_at",
            "expires_or_stale_after",
            "blocker_ref_if_unverified",
        ],
        "allowed_statuses": [
            "verified",
            "mismatch",
            "not_found",
            "suspicious",
            "manual_needed",
            "metadata_only_candidate",
        ],
        "metadata_only_candidate_behavior": "cannot_support_claim_without_abstract_or_publisher_check",
        "unverified_or_missing_behavior": "typed_blocker_or_reference_only",
        "may_authorize_quality_verdict": False,
        "may_authorize_publication_readiness": False,
    }


__all__ = [
    "JOURNAL_POLICY_CURRENTNESS_PACKS",
    "LITERATURE_SEARCH_SOURCE_PACKS",
    "build_citation_verification_pack",
    "build_journal_policy_currentness_pack",
    "build_literature_search_source_pack",
]

