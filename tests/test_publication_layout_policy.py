from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_REF = "contracts/publication_layout_policy.json"
EXPECTED_OUTPUTS = ["paper.pdf", "paper_with_supplementary.pdf"]


def read_json(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_publication_layout_policy_has_two_user_modes_and_two_core_pdfs() -> None:
    policy = read_json(POLICY_REF)

    assert policy["surface_kind"] == "mas_publication_layout_consumption_policy.v1"
    assert policy["owner"] == "MedAutoScience"
    assert [mode["mode"] for mode in policy["user_modes"]] == [
        "target_journal_specified",
        "target_journal_unspecified",
    ]
    provider = policy["provider_contract"]
    assert provider["package_id"] == "mas-scholar-skills"
    assert provider["minimum_version"] == "0.2.12"
    assert provider["module_id"] == "mas-scholar-skills.submit"
    assert provider["professional_skill_id"] == "medical-submission-prep"
    assert provider["template_source_policy"] == (
        "scholarskills_is_the_single_template_and_journal_profile_source_"
        "mas_does_not_vendor_or_fork_assets"
    )

    delivery = policy["delivery_contract"]
    outputs = delivery["core_pdf_outputs"]
    assert [output["file_name"] for output in outputs] == EXPECTED_OUTPUTS
    assert [output["includes_supplementary"] for output in outputs] == [False, True]
    assert delivery["separate_supplementary_members_required_when_present"] is True
    assert delivery["combined_reader_pdf_is_automatically_a_submission_upload"] is False
    assert delivery["third_reader_edition_allowed"] is False
    assert not (ROOT / "packs/medical-publication-layouts").exists()


def test_layout_resolution_is_fail_open_for_authoring_but_not_compliance() -> None:
    policy = read_json(POLICY_REF)
    selection = policy["selection_consumption"]
    freshness = policy["freshness_and_network_policy"]
    boundary = policy["authority_boundary"]

    assert selection["consumer_stage_ids"] == [
        "manuscript_authoring",
        "finalize_and_publication_handoff",
    ]
    assert selection["selection_ref"] == "publication_layout_selection_ref"
    assert selection["ordinary_authoring_may_be_blocked_by_profile_freshness"] is False
    assert selection["unknown_journal_effect"] == (
        "continue_with_general_reader_profile_and_mark_journal_specific_export_pending"
    )
    assert selection["stale_profile_effect"] == (
        "continue_ordinary_authoring_and_require_refresh_only_before_formal_submission"
    )
    assert selection["missing_catalog_or_asset_effect"] == (
        "continue_canonical_authoring_and_record_reader_export_quality_debt"
    )
    assert freshness["ordinary_authoring_network_requirement"] == "none"
    assert freshness["official_refresh_trigger"] == (
        "formal_submission_or_explicit_current_journal_compliance_request"
    )
    assert boundary["template_selection_can_authorize_journal_compliance"] is False
    assert boundary["template_selection_can_authorize_submission_readiness"] is False
    assert boundary["formal_submission_authority_remains_human_or_mas_owner"] is True


def test_package_and_stage_surfaces_consume_the_single_layout_policy() -> None:
    package = read_json("contracts/opl_agent_package_manifest.json")
    pack_input = read_json("contracts/pack_compiler_input.json")
    capability_map = read_json("contracts/capability_map.json")
    dependency = package["capability_dependencies"][0]

    assert dependency["package_id"] == "mas-scholar-skills"
    assert dependency["version_requirement"] == ">=0.2.12 <0.3.0"
    assert pack_input["required_domain_pack_paths"].count(POLICY_REF) == 1
    assert pack_input["source_refs"]["publication_layout_policy_ref"] == POLICY_REF
    assert pack_input["source_refs"]["required_domain_pack_paths"].count(POLICY_REF) == 1

    submission_capability = next(
        capability
        for capability in capability_map["capabilities"]
        if capability["capability_id"] == "medical-submission-prep"
    )
    policy_projections = [
        ref
        for ref in submission_capability["runtime_projection_refs"]
        if ref["ref"] == POLICY_REF
    ]
    assert policy_projections == [
        {
            "ref_kind": "contract_ref",
            "ref": POLICY_REF,
            "role": "mas_publication_layout_selection_consumption_policy",
        }
    ]
    assert POLICY_REF in submission_capability["canonical_paths"]

    authoring = (ROOT / "agent/prompts/manuscript_authoring.md").read_text(
        encoding="utf-8"
    )
    finalize = (ROOT / "agent/prompts/finalize_and_publication_handoff.md").read_text(
        encoding="utf-8"
    )
    for text in (authoring, finalize):
        assert POLICY_REF in text
        assert "publication_layout_selection_ref" in text
        assert "paper.pdf" in text
        assert "paper_with_supplementary.pdf" in text
        assert "third reader edition" in text
