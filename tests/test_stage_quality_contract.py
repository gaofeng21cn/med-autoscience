from __future__ import annotations

from med_autoscience.stage_quality_contract import (
    REQUIRED_STAGE_QUALITY_PACK_IDS,
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
