from __future__ import annotations

from med_autoscience.stage_quality_contract import (
    JOURNAL_FAMILY_QUALITY_PACK_IDS,
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
