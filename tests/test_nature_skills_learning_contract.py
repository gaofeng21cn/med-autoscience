from __future__ import annotations

from med_autoscience.stage_quality_contract import (
    JOURNAL_FAMILY_QUALITY_PACK_IDS,
    STRONG_PROMOTION_EVIDENCE_KINDS,
    build_stage_quality_pack_contract,
)


def test_nature_skills_learning_packs_are_not_authority_surfaces() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}

    for pack_id in JOURNAL_FAMILY_QUALITY_PACK_IDS:
        pack = packs[pack_id]
        clean_room = pack["clean_room_absorption"]
        forbidden = {item["authority_id"]: item for item in pack["forbidden_authority"]}

        assert clean_room["source_project"] == "nature-skills"
        assert clean_room["status_signal_consumed_as"] == "upstream_readme_status_only_not_mas_authority"
        assert clean_room["vendor_dependency"] is False
        assert clean_room["runtime_dependency"] is False
        assert clean_room["default_skill_source"] is False
        assert clean_room["publication_authority"] is False

        assert forbidden["vendor_skill_authority"]["forbidden"] is True
        assert forbidden["runtime_authority"]["forbidden"] is True
        assert forbidden["default_skill_authority"]["forbidden"] is True
        assert forbidden["publication_readiness_authority"]["forbidden"] is True
        assert forbidden["quality_verdict_authority"]["forbidden"] is True
        assert forbidden["mas_truth_write_authority"]["forbidden"] is True

        assert pack["publication_readiness_authority"] is False
        assert pack["quality_verdict_authority"] is False
        assert pack["authority_boundary"]["can_authorize_submission_readiness"] is False
        assert pack["authority_boundary"]["can_write_domain_truth"] is False


def test_journal_family_required_reviewer_outputs_are_auditable() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}
    allowed_output_ids = {"refs", "blocker_or_readiness", "owner_receipt_ref", "reviewer_record"}

    for pack_id in JOURNAL_FAMILY_QUALITY_PACK_IDS:
        outputs = packs[pack_id]["required_reviewer_output"]
        output_ids = {output["output_id"] for output in outputs}

        assert "refs" in output_ids
        assert "blocker_or_readiness" in output_ids
        assert output_ids & {"owner_receipt_ref", "reviewer_record"}
        assert output_ids <= allowed_output_ids
        for output in outputs:
            assert output["required"] is True
            assert output["may_authorize_publication_readiness"] is False
            assert output["may_authorize_quality_verdict"] is False


def test_nature_writing_and_statistical_reporting_are_quality_inputs_only() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}

    argument_pack = packs["manuscript_argument_pack"]
    assert argument_pack["clean_room_absorption"]["source_project"] == "nature-skills"
    assert argument_pack["clean_room_absorption"]["runtime_dependency"] is False
    assert argument_pack["clean_room_absorption"]["publication_authority"] is False
    assert {"one_sentence_argument", "paragraph_flow_review", "hedging_and_overclaim_check"} <= set(
        argument_pack["journal_family_patterns"]
    )
    assert {field["field_id"] for field in argument_pack["acceptance_evidence_fields"]} == {
        "argument_spine_refs",
        "section_job_map_refs",
        "claim_boundary_refs",
    }
    assert argument_pack["required_reviewer_output"][-1]["output_id"] == "reviewer_record"
    assert argument_pack["required_reviewer_output"][-1]["may_authorize_quality_verdict"] is False

    reporting_pack = packs["statistical_reporting_pack"]
    assert reporting_pack["clean_room_absorption"]["source_project"] == "nature-skills"
    assert reporting_pack["clean_room_absorption"]["vendor_dependency"] is False
    assert {
        "effect_size_confidence_interval_p_value_trace",
        "missingness_and_exclusion_trace",
        "model_performance_calibration_external_validation_trace",
        "multiplicity_sensitivity_subgroup_assumption_trace",
    } <= set(reporting_pack["journal_family_patterns"])
    assert {field["field_id"] for field in reporting_pack["acceptance_evidence_fields"]} == {
        "effect_estimate_refs",
        "denominator_missingness_refs",
        "model_validation_refs",
    }
    assert reporting_pack["required_reviewer_output"][-1]["output_id"] == "owner_receipt_ref"
    assert reporting_pack["required_reviewer_output"][-1]["may_authorize_publication_readiness"] is False

    for pack in (argument_pack, reporting_pack):
        assert pack["publication_readiness_authority"] is False
        assert pack["quality_verdict_authority"] is False
        assert pack["authority_boundary"]["can_authorize_submission_readiness"] is False
        assert pack["authority_boundary"]["can_write_domain_truth"] is False


def test_journal_family_quality_pack_consumption_is_descriptor_only() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}

    for pack_id in JOURNAL_FAMILY_QUALITY_PACK_IDS:
        pack = packs[pack_id]
        consumption = pack["quality_pack_consumption"]

        assert consumption["consumer_roles"] == ["reviewer_agent", "auditor_agent"]
        assert consumption["consumed_as"] == "explicit_quality_pack_descriptor"
        assert consumption["required_contract_refs"]
        assert consumption["required_output_classes"] == [
            output["output_id"] for output in pack["required_reviewer_output"]
        ]
        assert consumption["opl_consumption_role"] == "descriptor_ref_freshness_locator_only"
        assert consumption["opl_may_authorize_quality_verdict"] is False
        assert consumption["opl_may_authorize_publication_readiness"] is False
        assert consumption["opl_may_write_mas_truth"] is False

        evidence_fields = pack["acceptance_evidence_fields"]
        assert len(evidence_fields) >= 3
        for field in evidence_fields:
            assert field["field_id"]
            assert field["role"]
            assert field["required"] is True


def test_nature_skills_status_pattern_becomes_contract_maturity_not_vendor_authority() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}
    strong_evidence_kinds = set(STRONG_PROMOTION_EVIDENCE_KINDS)

    for pack_id in JOURNAL_FAMILY_QUALITY_PACK_IDS:
        pack = packs[pack_id]
        promotion = pack["promotion_evidence"]

        assert pack["maturity_status"] in {"beta_contract", "stable_contract"}
        assert promotion["maturity_model"] == "mas_contract_maturity_not_vendor_skill_status"
        assert promotion["upstream_status_signal"] == "draft_beta_stable_skill_status_pattern_learned"
        assert promotion["stable_requires_strong_evidence"] is True
        assert set(promotion["strong_evidence_kinds"]) == strong_evidence_kinds
        assert promotion["may_authorize_publication_readiness"] is False
        assert promotion["may_authorize_quality_verdict"] is False

        evidence = promotion["evidence"]
        assert evidence
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


def test_remaining_nature_skills_patterns_land_as_extension_contracts() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}

    expected = {
        "journal_response_pack": {
            "reviewer_response_edge_case_contract": {
                "learned_from": "nature-response",
                "required_fields": {
                    "editor_instruction_ids",
                    "stable_reviewer_comment_ids",
                    "action_label",
                    "missing_author_input_state",
                    "appeal_like_case_route",
                },
                "blocker": "journal_response_traceability_blocker",
            }
        },
        "data_availability_fair_pack": {
            "restricted_access_fair_metadata_contract": {
                "learned_from": "nature-data",
                "required_fields": {
                    "result_supporting_dataset_inventory",
                    "dataset_access_route",
                    "generated_reused_third_party_class",
                    "access_route",
                    "restriction_reason",
                    "restricted_access_process_ref",
                    "repository_identifier_or_blocker",
                    "available_upon_request_blocker_ref",
                    "fair_metadata_check_ref",
                },
                "blocker": "data_availability_or_fair_metadata_blocker",
            }
        },
        "citation_integrity_pack": {
            "strict_citation_scope_and_export_contract": {
                "learned_from": "nature-citation",
                "required_fields": {
                    "claim_segment_id",
                    "source_segment_ref",
                    "claim_boundary",
                    "batch_strategy_ref",
                    "accepted_journal_scope",
                    "identifier_refs",
                    "support_grade",
                    "contradictory_or_limiting_refs",
                    "metadata_only_candidate_flag",
                    "reference_export_format",
                },
                "blocker": "citation_support_or_export_blocker",
            }
        },
        "figure_evidence_contract_pack": {
            "figure_backend_export_qa_contract": {
                "learned_from": "nature-figure",
                "required_fields": {
                    "core_conclusion",
                    "evidence_chain",
                    "panel_map",
                    "selected_backend",
                    "backend_exclusivity_proof",
                    "export_formats",
                    "visual_qa_ref",
                },
                "blocker": "figure_export_or_source_data_blocker",
            }
        },
        "manuscript_argument_pack": {
            "prose_polish_claim_boundary_contract": {
                "learned_from": "nature-polishing",
                "required_fields": {
                    "paper_type",
                    "section_role",
                    "reader_question",
                    "reader_question_sequence",
                    "writing_failure_mode",
                    "section_architecture_id",
                    "evidence_ladder_refs",
                    "hedging_calibration",
                    "overclaim_detection_ref",
                },
                "blocker": "manuscript_argument_or_overclaim_blocker",
            }
        },
        "paper_reader_grounding_pack": {
            "full_paper_reader_source_map_contract": {
                "learned_from": "nature-reader",
                "required_fields": {
                    "source_map_ref",
                    "stable_text_block_ids",
                    "caption_block_ids",
                    "figure_or_table_asset_ids",
                    "page_and_block_anchors",
                    "source_grounded_followup_refs",
                },
                "blocker": "reader_source_map_or_anchor_blocker",
            }
        },
        "paper_presentation_pack": {
            "pptx_asset_manifest_and_package_qa_contract": {
                "learned_from": "nature-paper2ppt",
                "required_fields": {
                    "presentation_logic",
                    "evidence_spine",
                    "selected_figure_asset_refs",
                    "asset_manifest_ref",
                    "text_overflow_check_ref",
                    "pptx_reopen_or_package_qa_ref",
                },
                "blocker": "presentation_asset_or_package_qa_blocker",
            }
        },
    }

    for pack_id, expected_contracts in expected.items():
        contracts = {
            extension["contract_id"]: extension
            for extension in packs[pack_id]["extension_contracts"]
        }
        assert set(expected_contracts) <= set(contracts)

        for contract_id, expectation in expected_contracts.items():
            extension = contracts[contract_id]
            assert extension["learned_from"] == expectation["learned_from"]
            assert expectation["required_fields"] <= set(extension["required_fields"])
            assert extension["typed_blocker_if_missing"] == expectation["blocker"]
            assert extension["may_authorize_publication_readiness"] is False
            assert extension["may_authorize_quality_verdict"] is False


def test_figure_and_citation_extensions_keep_output_integrity_without_authority() -> None:
    contract = build_stage_quality_pack_contract()
    packs = {pack["pack_id"]: pack for pack in contract["packs"]}
    figure_contract = {
        item["contract_id"]: item
        for item in packs["figure_evidence_contract_pack"]["extension_contracts"]
    }["figure_backend_export_qa_contract"]
    citation_contract = {
        item["contract_id"]: item
        for item in packs["citation_integrity_pack"]["extension_contracts"]
    }["strict_citation_scope_and_export_contract"]

    assert "cross_backend_visual_fallback" in figure_contract["forbidden_shortcuts"]
    assert "figure_without_source_data_or_statistics_trace" in figure_contract["forbidden_shortcuts"]
    assert {"ENW", "RIS", "Zotero RDF"} <= set(citation_contract["allowed_export_formats"])

    for extension in (figure_contract, citation_contract):
        assert extension["may_authorize_publication_readiness"] is False
        assert extension["may_authorize_quality_verdict"] is False


def test_academic_search_source_pack_records_preflight_fallback_and_id_conversion_refs() -> None:
    contract = build_stage_quality_pack_contract()
    citation_pack = {
        pack["pack_id"]: pack for pack in contract["packs"]
    }["citation_integrity_pack"]
    search_pack = citation_pack["literature_search_source_pack"]

    assert {
        "source_preflight_refs",
        "source_failure_refs",
        "fallback_route_refs",
        "mesh_strategy_proof_refs",
        "dedup_result_refs",
        "id_conversion_refs",
    } <= set(search_pack["search_strategy_fields"])
    assert search_pack["failed_or_degraded_source_behavior"] == (
        "typed_blocker_or_explicit_fallback_ref"
    )
    assert search_pack["may_authorize_quality_verdict"] is False
    assert search_pack["may_authorize_publication_readiness"] is False
