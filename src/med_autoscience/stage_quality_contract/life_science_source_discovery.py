from __future__ import annotations


LIFE_SCIENCE_SOURCE_DISCOVERY_PACK_ID = "life_science_source_discovery_pack"
OPENAI_LIFE_SCIENCE_RESEARCH_OBSERVED_HEAD = "603a6e80711116e3584c33ecb8897548ed03d4f6"


def build_life_science_source_discovery_pack() -> dict[str, object]:
    return {
        "router_pattern": {
            "entrypoint": "research-router-skill",
            "route_to_minimum_useful_sources": True,
            "normalize_entities_before_retrieval": True,
            "parallelize_only_independent_evidence_lanes": True,
            "final_synthesis_owner": "mas_stage_executor_or_reviewer",
        },
        "source_families": [
            {
                "family_id": "literature_and_public_study_discovery",
                "mas_owner_surface": "literature_intelligence_os_and_evidence_ledger_refs",
                "initial_builtin_sources": [
                    "ncbi-entrez-skill",
                    "ncbi-pmc-skill",
                    "biorxiv-skill",
                    "clinicaltrials-skill",
                    "ncbi-datasets-skill",
                ],
            },
            {
                "family_id": "human_genetics_and_variant_evidence",
                "mas_owner_surface": "source_readiness_refs_and_claim_evidence_refs",
                "initial_builtin_sources": [
                    "opentargets-skill",
                    "gwas-catalog-skill",
                    "clinvar-variation-skill",
                    "gnomad-graphql-skill",
                    "ensembl-skill",
                    "gtex-eqtl-skill",
                    "locus-to-gene-mapper-skill",
                ],
            },
            {
                "family_id": "target_disease_and_functional_context",
                "mas_owner_surface": "stage_knowledge_packet_and_review_ledger_refs",
                "initial_builtin_sources": [
                    "human-protein-atlas-skill",
                    "uniprot-skill",
                    "reactome-skill",
                    "string-skill",
                    "quickgo-skill",
                ],
            },
            {
                "family_id": "clinical_translational_and_pharmacology",
                "mas_owner_surface": "source_readiness_refs_and_reviewer_caveat_refs",
                "initial_builtin_sources": [
                    "clinicaltrials-skill",
                    "chembl-skill",
                    "pharmgkb-skill",
                    "cbioportal-skill",
                    "civic-skill",
                ],
            },
            {
                "family_id": "omics_structure_and_specialized_context",
                "mas_owner_surface": "optional_stage_evidence_refs",
                "initial_builtin_sources": [
                    "alphafold-skill",
                    "rcsb-pdb-skill",
                    "pride-skill",
                    "metabolights-skill",
                    "mgnify-skill",
                    "cellxgene-skill",
                ],
            },
        ],
        "required_record_fields": [
            "source_family",
            "source_id",
            "entity_kind",
            "normalized_entity_ref",
            "query_ref",
            "retrieved_at",
            "checked_at",
            "expires_or_stale_after",
            "raw_payload_locator",
            "summary_ref",
            "evidence_grade",
            "study_design_or_assay_caveats",
            "ancestry_tissue_species_or_cohort_caveats",
            "conflict_refs",
            "typed_blocker_ref_if_incomplete",
        ],
        "implementation_policy": {
            "first_batch": "minimal_mas_owned_public_api_clients_or_wrappers",
            "copy_external_plugin_code": False,
            "preserve_upstream_skill_names_as_provenance_labels": True,
            "raw_payload_body_policy": "workspace_locator_only_save_raw_only_on_request",
            "network_success_is_readiness": False,
            "script_success_is_quality": False,
        },
        "may_authorize_source_readiness_verdict": False,
        "may_authorize_quality_verdict": False,
        "may_authorize_publication_readiness": False,
    }


def build_life_science_clean_room_absorption() -> dict[str, object]:
    return {
        "source_project": "openai-life-science-research",
        "source_repository": "https://github.com/openai/plugins",
        "source_path": "plugins/life-science-research",
        "observed_head": OPENAI_LIFE_SCIENCE_RESEARCH_OBSERVED_HEAD,
        "absorbed_as": "mas_native_source_discovery_contract_pattern",
        "license_boundary": "proprietary_plugin_no_code_copy",
        "vendor_dependency": False,
        "runtime_dependency": False,
        "publication_authority": False,
        "default_skill_source": False,
    }


__all__ = [
    "LIFE_SCIENCE_SOURCE_DISCOVERY_PACK_ID",
    "OPENAI_LIFE_SCIENCE_RESEARCH_OBSERVED_HEAD",
    "build_life_science_clean_room_absorption",
    "build_life_science_source_discovery_pack",
]

