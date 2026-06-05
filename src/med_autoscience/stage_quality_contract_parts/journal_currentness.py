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


def build_source_citation_authority_pack() -> dict[str, object]:
    return {
        "pack_id": "source_citation_authority_pack",
        "clean_room_absorption": {
            "source_project": "kaust-ark/ARK",
            "source_pattern": "api_first_citation_and_no_fabricated_references",
            "absorbed_as": "mas_native_source_authority_pack",
            "runtime_dependency": False,
            "vendor_dependency": False,
            "foreign_source_authority": False,
        },
        "source_project": "kaust-ark/ARK",
        "absorbed_as": "mas_native_source_citation_authority_descriptor",
        "descriptor_only": True,
        "llm_role": "candidate_selection_and_claim_alignment_only",
        "llm_may_author_authoritative_citation_record": False,
        "required_source_families": [
            "PubMed",
            "DOI",
            "CrossRef",
            "ClinicalTrials",
            "dataset_manifest",
            "guideline_source",
            "manual_curator_receipt",
        ],
        "authority_boundary": {
            "source_readiness_verdict_authority": False,
            "publication_readiness_authority": False,
            "quality_verdict_authority": False,
            "may_write_source_truth": False,
        },
        "progress_first_policy": {
            "missing_currentness_behavior": "source_refresh_work_unit",
            "critical_claim_missing_source_behavior": "typed_blocker",
            "noncritical_missing_source_behavior": "reviewer_route_back_or_source_refresh",
            "may_block_unrelated_agent_progress": False,
        },
        "llm_role_detail": {
            "may_select_candidate_citations": True,
            "may_rank_or_explain_candidate_support": True,
            "may_author_authoritative_citation_records": False,
            "may_author_bibtex_or_reference_manager_records": False,
        },
        "citation_entry_required_fields": [
            "claim_segment_id",
            "candidate_citation_ref",
            "source_family",
            "source_identifier_or_locator",
            "source_api_or_human_provenance_ref",
            "currentness_digest_ref",
            "checked_at",
            "expires_or_stale_after",
        ],
        "medical_source_families": [
            {
                "family_id": "pubmed",
                "display_name": "PubMed",
                "required_provenance": "source_api_result_ref",
                "authoritative_record_source": "source_api_or_manual_curator_receipt",
            },
            {
                "family_id": "doi",
                "display_name": "DOI",
                "required_provenance": "doi_resolution_or_content_negotiation_ref",
                "authoritative_record_source": "source_api_or_manual_curator_receipt",
            },
            {
                "family_id": "crossref",
                "display_name": "CrossRef",
                "required_provenance": "crossref_api_result_ref",
                "authoritative_record_source": "source_api_or_manual_curator_receipt",
            },
            {
                "family_id": "clinicaltrials",
                "display_name": "ClinicalTrials",
                "required_provenance": "registry_api_or_record_locator_ref",
                "authoritative_record_source": "source_api_or_manual_curator_receipt",
            },
            {
                "family_id": "dataset_manifest",
                "display_name": "Dataset manifest",
                "required_provenance": "dataset_manifest_ref",
                "authoritative_record_source": "manifest_owner_or_manual_curator_receipt",
            },
            {
                "family_id": "guideline_source",
                "display_name": "Guideline source",
                "required_provenance": "official_guideline_source_ref",
                "authoritative_record_source": "source_owner_or_manual_curator_receipt",
            },
            {
                "family_id": "manual_curator_receipt",
                "display_name": "Manual curator receipt",
                "required_provenance": "manual_curator_receipt_ref",
                "authoritative_record_source": "human_curator_receipt",
            },
        ],
        "legacy_authority_boundary_detail": {
            "may_authorize_publication_readiness": False,
            "may_authorize_source_readiness_verdict": False,
            "may_authorize_quality_verdict": False,
            "may_write_authoritative_citation_record": False,
            "may_write_authoritative_bibtex": False,
        },
        "allowed_outputs": [
            "reviewer_input",
            "auditor_input",
            "typed_blocker",
            "source_refresh_work_unit",
        ],
        "forbidden_outputs": [
            "publication_readiness",
            "source_readiness_verdict",
            "quality_verdict",
            "llm_authored_bibtex",
            "llm_authored_authoritative_citation_record",
        ],
        "progress_first_currentness_policy": {
            "missing_currentness_digest_behavior": "emit_source_refresh_work_unit",
            "source_refresh_work_unit_required_fields": [
                "claim_segment_id",
                "source_family",
                "stale_or_missing_field",
                "refresh_route",
                "owner",
                "acceptance_evidence_ref",
            ],
            "typed_blocker_only_when": [
                "critical_claim_has_no_source_api_or_human_provenance",
                "critical_claim_source_identifier_conflict",
                "hard_gate_source_family_missing_for_claim_type",
            ],
            "non_hard_gate_gaps_must_not_block_progress": True,
        },
    }


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
            "source_preflight_refs",
            "source_failure_refs",
            "fallback_route_refs",
            "mesh_terms_or_reason_not_applicable",
            "mesh_strategy_proof_refs",
            "keyword_queries",
            "source_tier_attempts",
            "deduplication_basis",
            "dedup_result_refs",
            "id_conversion_refs",
            "search_checked_at",
            "search_expires_or_stale_after",
        ],
        "multi_source_search_required": True,
        "mesh_strategy_required_for_biomedical_claims": True,
        "insufficient_source_behavior": "typed_blocker_or_reference_only",
        "failed_or_degraded_source_behavior": "typed_blocker_or_explicit_fallback_ref",
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
    "build_source_citation_authority_pack",
]
