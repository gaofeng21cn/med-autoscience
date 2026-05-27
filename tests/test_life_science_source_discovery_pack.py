from __future__ import annotations

from med_autoscience.stage_quality_contract import build_stage_quality_pack_contract


def _life_science_pack() -> dict[str, object]:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}
    return packs["life_science_source_discovery_pack"]


def test_life_science_source_discovery_pack_exposes_openai_plugin_patterns_as_mas_refs() -> None:
    pack = _life_science_pack()

    assert pack["role"] == "quality_input_and_reviewer_rubric"
    assert pack["maturity_status"] == "beta_contract"
    assert pack["clean_room_absorption"] == {
        "source_project": "openai-life-science-research",
        "source_repository": "https://github.com/openai/plugins",
        "source_path": "plugins/life-science-research",
        "observed_head": "603a6e80711116e3584c33ecb8897548ed03d4f6",
        "absorbed_as": "mas_native_source_discovery_contract_pattern",
        "license_boundary": "proprietary_plugin_no_code_copy",
        "vendor_dependency": False,
        "runtime_dependency": False,
        "publication_authority": False,
        "default_skill_source": False,
    }

    source_pack = pack["life_science_source_discovery_pack"]
    assert source_pack["router_pattern"] == {
        "entrypoint": "research-router-skill",
        "route_to_minimum_useful_sources": True,
        "normalize_entities_before_retrieval": True,
        "parallelize_only_independent_evidence_lanes": True,
        "final_synthesis_owner": "mas_stage_executor_or_reviewer",
    }
    assert source_pack["required_record_fields"] == [
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
    ]
    assert source_pack["may_authorize_source_readiness_verdict"] is False
    assert source_pack["may_authorize_quality_verdict"] is False
    assert source_pack["may_authorize_publication_readiness"] is False


def test_life_science_source_discovery_pack_prioritizes_high_value_builtin_sources() -> None:
    source_pack = _life_science_pack()["life_science_source_discovery_pack"]
    families = {family["family_id"]: family for family in source_pack["source_families"]}

    assert list(families) == [
        "literature_and_public_study_discovery",
        "human_genetics_and_variant_evidence",
        "target_disease_and_functional_context",
        "clinical_translational_and_pharmacology",
        "omics_structure_and_specialized_context",
    ]
    assert families["literature_and_public_study_discovery"]["initial_builtin_sources"] == [
        "ncbi-entrez-skill",
        "ncbi-pmc-skill",
        "biorxiv-skill",
        "clinicaltrials-skill",
        "ncbi-datasets-skill",
    ]
    assert families["human_genetics_and_variant_evidence"]["initial_builtin_sources"] == [
        "opentargets-skill",
        "gwas-catalog-skill",
        "clinvar-variation-skill",
        "gnomad-graphql-skill",
        "ensembl-skill",
        "gtex-eqtl-skill",
        "locus-to-gene-mapper-skill",
    ]
    assert families["clinical_translational_and_pharmacology"]["initial_builtin_sources"] == [
        "clinicaltrials-skill",
        "chembl-skill",
        "pharmgkb-skill",
        "cbioportal-skill",
        "civic-skill",
    ]
    assert source_pack["implementation_policy"] == {
        "first_batch": "minimal_mas_owned_public_api_clients_or_wrappers",
        "copy_external_plugin_code": False,
        "preserve_upstream_skill_names_as_provenance_labels": True,
        "raw_payload_body_policy": "workspace_locator_only_save_raw_only_on_request",
        "network_success_is_readiness": False,
        "script_success_is_quality": False,
    }

