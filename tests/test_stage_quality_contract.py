from __future__ import annotations

from med_autoscience.stage_quality_contract import (
    REQUIRED_STAGE_QUALITY_PACK_IDS,
    STRONG_PROMOTION_EVIDENCE_KINDS,
    build_stage_quality_pack_contract,
)


def test_stage_quality_contract_defines_required_pack_boundaries_and_refs() -> None:
    contract = build_stage_quality_pack_contract()

    assert contract["surface_kind"] == "mas_stage_quality_pack_contract"
    assert contract["version"] == "mas-stage-quality-pack-contract.v1"
    assert contract["pack_ids"] == list(REQUIRED_STAGE_QUALITY_PACK_IDS)
    assert contract["authority_boundary"] == {
        "pack_role": "quality_input_and_reviewer_rubric",
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "truth_owner": "MedAutoScience",
        "opl_role": "descriptor_ref_freshness_locator_consumer",
        "opl_can_write_mas_truth": False,
        "opl_can_authorize_quality_verdict": False,
        "opl_can_authorize_publication_readiness": False,
    }

    packs = {pack["pack_id"]: pack for pack in contract["packs"]}
    assert set(packs) == set(REQUIRED_STAGE_QUALITY_PACK_IDS)
    for pack_id, pack in packs.items():
        assert pack["pack_id"] == pack_id
        assert pack["role"] == "quality_input_and_reviewer_rubric"
        assert pack["maturity_status"] in {"beta_contract", "stable_contract"}
        assert pack["promotion_evidence"]["maturity_model"] == "mas_contract_maturity_not_vendor_skill_status"
        assert pack["promotion_evidence"]["stable_requires_strong_evidence"] is True
        assert pack["promotion_evidence"]["may_authorize_publication_readiness"] is False
        assert pack["promotion_evidence"]["may_authorize_quality_verdict"] is False
        assert pack["promotion_evidence"]["evidence"]
        assert pack["publication_readiness_authority"] is False
        assert pack["quality_verdict_authority"] is False
        assert pack["applies_to"]["stages"]
        assert pack["applies_to"]["study_archetypes"]
        assert pack["authority_boundary"]["truth_owner"] == "MedAutoScience"
        assert pack["authority_boundary"]["can_authorize_publication_readiness"] is False
        assert pack["owner_refs"]
        assert pack["required_refs"]
        assert any(ref["ref_kind"] in {"surface_kind", "workspace_locator", "json_pointer"} for ref in pack["required_refs"])

    assert packs["medical_claim_evidence_pack"]["applies_to"]["stages"] == ["write", "review", "finalize", "decision"]
    expert_pack = packs["ai_native_expert_judgment_pack"]
    assert "write" in expert_pack["applies_to"]["stages"]
    assert "review" in expert_pack["applies_to"]["stages"]
    assert expert_pack["required_refs"] == [
        {
            "ref_kind": "surface_kind",
            "ref": "AI reviewer workflow",
            "role": "open_expert_review_required",
        },
        {
            "ref_kind": "surface_kind",
            "ref": "stage_quality_pack_contract",
            "role": "quality_floor_not_ceiling",
        },
    ]
    assert "paper/evidence/evidence_ledger.json" in {
        ref["ref"] for ref in packs["medical_claim_evidence_pack"]["required_refs"]
    }
    assert packs["human_gate_pack"]["applies_to"]["stages"] == ["all_boundary_changing_stages"]


def test_stable_quality_pack_maturity_requires_strong_promotion_evidence() -> None:
    contract = build_stage_quality_pack_contract()
    strong_evidence_kinds = set(STRONG_PROMOTION_EVIDENCE_KINDS)

    for pack in contract["packs"]:
        promotion = pack["promotion_evidence"]
        assert set(promotion["strong_evidence_kinds"]) == strong_evidence_kinds

        evidence = promotion["evidence"]
        assert all(item["evidence_kind"] not in {"docs_only", "ordinary_tests"} for item in evidence)
        strong_evidence = [
            item
            for item in evidence
            if item["strength"] == "strong" and item["evidence_kind"] in strong_evidence_kinds
        ]

        if pack["maturity_status"] == "stable_contract":
            assert promotion["stable_strong_evidence_satisfied"] is True
            assert strong_evidence
        else:
            assert promotion["stable_strong_evidence_satisfied"] is False


def test_reporting_guideline_selection_covers_required_families_and_clinical_base_guideline() -> None:
    contract = build_stage_quality_pack_contract()
    reporting_pack = {pack["pack_id"]: pack for pack in contract["packs"]}["reporting_guideline_pack"]
    selections = {
        selection["study_archetype"]: selection for selection in reporting_pack["guideline_selection"]
    }

    assert selections["observational_or_cohort_or_registry"]["guideline_families"] == ["STROBE"]
    assert selections["diagnostic_or_prognostic_model"]["guideline_families"] == ["TRIPOD", "TRIPOD-AI"]
    assert selections["randomized_or_intervention"]["guideline_families"] == ["CONSORT"]
    assert selections["systematic_review_or_meta_analysis"]["guideline_families"] == ["PRISMA"]
    assert selections["diagnostic_accuracy"]["guideline_families"] == ["STARD"]
    assert selections["case_report_or_case_series"]["guideline_families"] == ["CARE"]

    ai_ml = selections["ai_ml_medical_study"]
    assert "AI/ML extension" in ai_ml["guideline_families"]
    assert ai_ml["requires_clinical_base_guideline"] is True
    assert set(ai_ml["clinical_base_guideline_options"]) >= {
        "STROBE",
        "TRIPOD",
        "TRIPOD-AI",
        "CONSORT",
        "PRISMA",
        "STARD",
        "CARE",
    }


def test_journal_family_quality_packs_are_projection_only_clean_room_absorptions() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}

    expected_journal_packs = {
        "journal_response_pack",
        "data_availability_fair_pack",
        "citation_integrity_pack",
        "figure_evidence_contract_pack",
        "manuscript_argument_pack",
        "paper_reader_grounding_pack",
        "paper_presentation_pack",
        "statistical_reporting_pack",
    }
    assert expected_journal_packs <= set(REQUIRED_STAGE_QUALITY_PACK_IDS)
    assert expected_journal_packs <= set(packs)

    for pack_id in expected_journal_packs:
        pack = packs[pack_id]
        assert pack["role"] == "quality_input_and_reviewer_rubric"
        assert pack["publication_readiness_authority"] is False
        assert pack["quality_verdict_authority"] is False
        assert pack["authority_boundary"]["can_authorize_publication_readiness"] is False
        assert pack["authority_boundary"]["can_write_domain_truth"] is False
        assert pack["clean_room_absorption"]["source_project"] == "nature-skills"
        assert pack["clean_room_absorption"]["vendor_dependency"] is False
        assert pack["clean_room_absorption"]["runtime_dependency"] is False
        assert pack["clean_room_absorption"]["publication_authority"] is False
        assert pack["clean_room_absorption"]["absorbed_as"] == "mas_native_contract_pattern"
        assert pack["required_refs"]
        assert pack["acceptance_evidence_fields"]
        assert pack["required_reviewer_output"]
        assert pack["forbidden_authority"]
        assert pack["quality_pack_consumption"]["consumer_roles"] == ["reviewer_agent", "auditor_agent"]
        assert pack["quality_pack_consumption"]["opl_consumption_role"] == "descriptor_ref_freshness_locator_only"
        assert pack["quality_pack_consumption"]["opl_may_authorize_quality_verdict"] is False
        assert pack["quality_pack_consumption"]["opl_may_authorize_publication_readiness"] is False
        assert pack["quality_pack_consumption"]["opl_may_write_mas_truth"] is False

    response_pack = packs["journal_response_pack"]
    assert response_pack["journal_family_patterns"] == [
        "stable_comment_ids",
        "comment_response_tracker",
        "action_mapping",
        "missing_author_input_flags",
        "readiness_state",
    ]
    assert "review" in response_pack["applies_to"]["stages"]

    data_pack = packs["data_availability_fair_pack"]
    assert data_pack["journal_family_patterns"] == [
        "dataset_to_location_mapping",
        "restricted_data_access_route",
        "repository_identifier",
        "datacite_style_dataset_citation",
        "fair_metadata_checklist",
    ]

    citation_pack = packs["citation_integrity_pack"]
    assert citation_pack["journal_family_patterns"] == [
        "claim_segment_id",
        "candidate_citation_refs",
        "support_grade",
        "metadata_only_review_required",
        "reference_manager_export_note",
    ]
    assert [source["tier"] for source in citation_pack["literature_search_source_pack"]["source_tiers"]] == [
        "T1",
        "T2",
        "T3",
    ]
    assert citation_pack["literature_search_source_pack"]["multi_source_search_required"] is True
    assert citation_pack["literature_search_source_pack"]["mesh_strategy_required_for_biomedical_claims"] is True
    assert citation_pack["journal_policy_currentness_pack"]["official_policy_refs_required"] is True
    assert citation_pack["journal_policy_currentness_pack"]["missing_or_stale_policy_ref_behavior"] == (
        "blocker_or_reference_only"
    )
    assert citation_pack["citation_verification_pack"]["verification_output_fields"] == [
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
    ]
    assert "metadata_only_candidate" in citation_pack["citation_verification_pack"]["allowed_statuses"]

    source_authority = citation_pack["source_citation_authority_pack"]
    assert source_authority["clean_room_absorption"] == {
        "source_project": "kaust-ark/ARK",
        "source_pattern": "api_first_citation_and_no_fabricated_references",
        "absorbed_as": "mas_native_source_authority_pack",
        "runtime_dependency": False,
        "vendor_dependency": False,
        "foreign_source_authority": False,
    }
    assert source_authority["llm_role"] == "candidate_selection_and_claim_alignment_only"
    assert source_authority["llm_may_author_authoritative_citation_record"] is False
    assert source_authority["required_source_families"] == [
        "PubMed",
        "DOI",
        "CrossRef",
        "ClinicalTrials",
        "dataset_manifest",
        "guideline_source",
        "manual_curator_receipt",
    ]
    assert source_authority["authority_boundary"] == {
        "source_readiness_verdict_authority": False,
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "may_write_source_truth": False,
    }
    assert source_authority["progress_first_policy"] == {
        "missing_currentness_behavior": "source_refresh_work_unit",
        "critical_claim_missing_source_behavior": "typed_blocker",
        "noncritical_missing_source_behavior": "reviewer_route_back_or_source_refresh",
        "may_block_unrelated_agent_progress": False,
    }

    figure_pack = packs["figure_evidence_contract_pack"]
    assert figure_pack["journal_family_patterns"] == [
        "core_claim",
        "evidence_chain",
        "panel_role",
        "source_data_refs",
        "statistics_refs",
        "export_contract",
        "qa_risks",
    ]

    argument_pack = packs["manuscript_argument_pack"]
    assert argument_pack["journal_family_patterns"] == [
        "paper_type_logic",
        "one_sentence_argument",
        "section_job_map",
        "claim_evidence_boundary_map",
        "paragraph_flow_review",
        "hedging_and_overclaim_check",
    ]
    assert "write" in argument_pack["applies_to"]["stages"]
    assert "review" in argument_pack["applies_to"]["stages"]

    reporting_pack = packs["statistical_reporting_pack"]
    assert reporting_pack["journal_family_patterns"] == [
        "sample_size_and_denominator_trace",
        "effect_size_confidence_interval_p_value_trace",
        "missingness_and_exclusion_trace",
        "model_performance_calibration_external_validation_trace",
        "multiplicity_sensitivity_subgroup_assumption_trace",
        "software_version_and_reproducible_analysis_refs",
    ]
    assert "analysis-campaign" in reporting_pack["applies_to"]["stages"]
    assert "journal-resolution" in reporting_pack["applies_to"]["stages"]


def test_journal_policy_and_citation_currentness_cannot_authorize_quality_without_current_refs() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}

    citation_pack = packs["citation_integrity_pack"]
    policy_pack = citation_pack["journal_policy_currentness_pack"]
    verification_pack = citation_pack["citation_verification_pack"]
    search_pack = citation_pack["literature_search_source_pack"]

    assert policy_pack["forbidden_outputs_without_current_official_refs"] == [
        "publication_readiness",
        "quality_verdict",
        "submission_readiness",
    ]
    assert policy_pack["missing_or_stale_policy_ref_behavior"] == "blocker_or_reference_only"
    assert policy_pack["may_authorize_quality_verdict"] is False
    assert policy_pack["may_authorize_publication_readiness"] is False

    assert verification_pack["unverified_or_missing_behavior"] == "typed_blocker_or_reference_only"
    assert verification_pack["metadata_only_candidate_behavior"] == (
        "cannot_support_claim_without_abstract_or_publisher_check"
    )
    assert verification_pack["may_authorize_quality_verdict"] is False
    assert verification_pack["may_authorize_publication_readiness"] is False

    assert search_pack["insufficient_source_behavior"] == "typed_blocker_or_reference_only"
    assert all(source["may_authorize_quality_verdict"] is False for source in search_pack["source_tiers"])
    assert citation_pack["forbidden_authority"]
    assert {item["authority_id"] for item in citation_pack["forbidden_authority"]} >= {
        "publication_readiness_authority",
        "quality_verdict_authority",
        "mas_truth_write_authority",
    }


def test_autosci_research_lifecycle_patterns_land_as_quality_pack_contracts() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}

    expected = {
        "ai_native_expert_judgment_pack": {
            "independent_reviewer_verdict_mapping_contract": {
                "learned_from": "autosci-review",
                "fields": {
                    "reviewer_record_ref",
                    "separate_invocation_receipt_ref",
                    "verdict",
                    "source_ref_mapping",
                    "artifact_ref_mapping",
                    "evidence_ref_mapping",
                },
                "blocker": "independent_reviewer_verdict_mapping_blocker",
            }
        },
        "life_science_source_discovery_pack": {
            "proposal_action_source_discovery_contract": {
                "learned_from": "autosci-discover-daily-arxiv",
                "fields": {
                    "candidate_record_ref",
                    "dedup_basis_ref",
                    "decision_artifact_ref",
                    "source_adapter_rejection_log_ref",
                },
                "blocker": "source_discovery_proposal_action_blocker",
            },
            "typed_knowledge_graph_edge_contract": {
                "learned_from": "autosci-runtime-schema",
                "fields": {
                    "entity_ref",
                    "semantic_edge_ref",
                    "edge_evidence_ref",
                    "citation_ref_if_bibliographic",
                    "reverse_ref_or_terminal_exception",
                },
                "blocker": "research_graph_ref_consistency_blocker",
            },
        },
        "route_memory_pack": {
            "negative_research_memory_contract": {
                "learned_from": "autosci-ideate",
                "fields": {
                    "failed_or_rejected_item_ref",
                    "failure_reason",
                    "do_not_repeat_scope",
                    "memory_write_router_receipt_ref",
                },
                "blocker": "negative_memory_or_duplicate_route_blocker",
            }
        },
        "statistical_analysis_pack": {
            "experiment_lifecycle_receipt_contract": {
                "learned_from": "autosci-exp-design-run-eval",
                "fields": {
                    "idea_or_hypothesis_ref",
                    "deploy_receipt_ref",
                    "monitor_refs",
                    "collect_receipt_ref",
                    "evaluation_verdict_ref",
                    "controller_next_route_ref",
                },
                "blocker": "experiment_lifecycle_receipt_blocker",
            }
        },
        "paper_presentation_pack": {
            "source_dag_render_qa_artifact_contract": {
                "learned_from": "autosci-poster",
                "fields": {
                    "source_dag_ref",
                    "figure_asset_manifest_ref",
                    "selected_asset_refs",
                    "render_output_ref",
                    "overflow_or_visual_qa_ref",
                    "artifact_authority_receipt_ref_or_typed_blocker",
                },
                "blocker": "presentation_render_qa_or_artifact_authority_blocker",
            }
        },
    }

    for pack_id, expected_contracts in expected.items():
        pack = packs[pack_id]
        assert pack["autosci_clean_room_absorption"] == {
            "source_project": "AutoSci/OmegaWiki",
            "source_repository": "https://github.com/skyllwt/AutoSci",
            "observed_head": "d89cc72a884a2d091b6fac5719f30b4c64d2c6bd",
            "absorbed_as": "mas_native_contract_pattern",
            "vendor_dependency": False,
            "runtime_dependency": False,
            "default_skill_source": False,
            "copy_external_runtime_or_slash_commands": False,
            "publication_authority": False,
            "artifact_authority": False,
        }
        contracts = {item["contract_id"]: item for item in pack["autosci_extension_contracts"]}
        assert set(expected_contracts) == set(contracts)
        for contract_id, expectation in expected_contracts.items():
            item = contracts[contract_id]
            assert item["learned_from"] == expectation["learned_from"]
            assert expectation["fields"] <= set(item["required_fields"])
            assert item["typed_blocker_if_missing"] == expectation["blocker"]
            assert item["may_authorize_publication_readiness"] is False
            assert item["may_authorize_quality_verdict"] is False
