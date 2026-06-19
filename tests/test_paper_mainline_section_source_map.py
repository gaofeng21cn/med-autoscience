from __future__ import annotations

from med_autoscience.paper_mainline_section_source_map import (
    build_paper_section_source_map_readback,
)


def _complete_section_map() -> dict[str, object]:
    return {
        "schema_version": 1,
        "section_id": "results.primary",
        "section_role": "primary_results",
        "draft_block_refs": ["draft:block/results-primary"],
        "claim_refs": ["claim:primary-outcome"],
        "evidence_refs": ["evidence:primary-model-table"],
        "source_map_refs": ["source-map:results-primary"],
        "reviewer_repair_refs": ["reviewer-repair:hedging-primary-outcome"],
    }


def test_complete_readback_is_refs_only_fail_open_and_non_authoritative() -> None:
    readback = build_paper_section_source_map_readback(_complete_section_map())

    assert readback["surface_kind"] == "mas_paper_section_source_map_readback"
    assert readback["schema_version"] == 1
    assert readback["status"] == "complete"
    assert readback["refs_only"] is True
    assert readback["fail_open"] is True
    assert readback["mainline_waits_for_readback"] is False
    assert readback["can_block_current_owner_action"] is False
    assert readback["missing_fields"] == []
    assert readback["typed_blocker_candidate"] is None

    assert readback["section"] == {
        "section_id": "results.primary",
        "section_role": "primary_results",
    }
    assert readback["refs"] == {
        "draft_block_refs": ["draft:block/results-primary"],
        "claim_refs": ["claim:primary-outcome"],
        "evidence_refs": ["evidence:primary-model-table"],
        "source_map_refs": ["source-map:results-primary"],
        "reviewer_repair_refs": ["reviewer-repair:hedging-primary-outcome"],
    }
    assert readback["authority_boundary"] == {
        "can_write_mas_truth": False,
        "can_mutate_paper_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
    }
    assert readback["external_provenance_refs"] == [
        {
            "source_project": "nature-skills",
            "source_ref": "nature-skills@1cb9070:skills/nature-writing",
            "absorbed_as": "section_contract_to_draft_block_ref_pattern",
            "copied_upstream_text": False,
        },
        {
            "source_project": "nature-skills",
            "source_ref": "nature-skills@1cb9070:skills/nature-polishing",
            "absorbed_as": "section_aware_claim_boundary_and_overclaim_ref_pattern",
            "copied_upstream_text": False,
        },
        {
            "source_project": "nature-skills",
            "source_ref": "nature-skills@1cb9070:skills/nature-reader",
            "absorbed_as": "source_map_and_reader_anchor_ref_pattern",
            "copied_upstream_text": False,
        },
    ]
    assert readback["contract_refs"] == [
        {
            "pack_id": "manuscript_argument_pack",
            "extension_contract_id": "prose_polish_claim_boundary_contract",
            "typed_blocker_if_missing": "manuscript_argument_or_overclaim_blocker",
        },
        {
            "pack_id": "paper_reader_grounding_pack",
            "extension_contract_id": "full_paper_reader_source_map_contract",
            "typed_blocker_if_missing": "reader_source_map_or_anchor_blocker",
        },
    ]


def test_missing_reader_source_map_fields_emit_reader_blocker_candidate() -> None:
    section_map = _complete_section_map()
    section_map["source_map_refs"] = []

    readback = build_paper_section_source_map_readback(section_map)

    assert readback["status"] == "typed_blocker_candidate"
    assert readback["missing_fields"] == ["source_map_refs"]
    assert readback["can_block_current_owner_action"] is False
    assert readback["typed_blocker_candidate"] == {
        "blocker_type": "reader_source_map_or_anchor_blocker",
        "missing_fields": ["source_map_refs"],
        "refs_only": True,
        "fail_open": True,
        "can_block_current_owner_action": False,
        "recommended_owner_action": "repair_section_source_map_refs",
        "authority_boundary": readback["authority_boundary"],
    }


def test_missing_argument_fields_emit_manuscript_blocker_candidate() -> None:
    section_map = _complete_section_map()
    section_map["claim_refs"] = []
    section_map["reviewer_repair_refs"] = []

    readback = build_paper_section_source_map_readback(section_map)

    assert readback["status"] == "typed_blocker_candidate"
    assert readback["missing_fields"] == ["claim_refs", "reviewer_repair_refs"]
    assert readback["typed_blocker_candidate"]["blocker_type"] == (
        "manuscript_argument_or_overclaim_blocker"
    )
    assert readback["typed_blocker_candidate"]["recommended_owner_action"] == (
        "repair_section_argument_or_reviewer_refs"
    )


def test_schema_and_identity_fields_are_required_and_refs_are_normalized() -> None:
    readback = build_paper_section_source_map_readback(
        {
            "schema_version": "1",
            "section_id": "  intro.context  ",
            "section_role": "  introduction  ",
            "draft_block_refs": ("draft:block/intro", None, ""),
            "claim_refs": ["claim:intro"],
            "evidence_refs": ["evidence:intro"],
            "source_map_refs": ["source-map:intro"],
            "reviewer_repair_refs": ["repair:intro"],
        }
    )

    assert readback["status"] == "typed_blocker_candidate"
    assert readback["section"] == {
        "section_id": "intro.context",
        "section_role": "introduction",
    }
    assert readback["refs"]["draft_block_refs"] == ["draft:block/intro"]
    assert readback["missing_fields"] == ["schema_version"]
    assert readback["typed_blocker_candidate"]["blocker_type"] == (
        "manuscript_argument_or_overclaim_blocker"
    )
