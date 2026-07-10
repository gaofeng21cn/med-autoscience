from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.stage_quality_contract import (
    JOURNAL_FAMILY_QUALITY_PACK_IDS,
    build_stage_quality_pack_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ADOPTION_CONTRACT = REPO_ROOT / "contracts/nature_skills_learning_adoption.json"
GLOBAL_FORBIDDEN_AUTHORITY = {
    "vendor_runner_dependency",
    "default_skill_source",
    "second_selector",
    "always_on_advisory_scan",
    "publication_readiness_authority",
    "quality_verdict_authority",
    "mas_truth_write_authority",
}


def test_nature_skills_learning_packs_are_not_authority_surfaces() -> None:
    packs = {
        item["pack_id"]: item
        for item in build_stage_quality_pack_contract()["packs"]
    }

    for pack_id in JOURNAL_FAMILY_QUALITY_PACK_IDS:
        pack = packs[pack_id]
        clean_room = pack["clean_room_absorption"]
        forbidden = {
            item["authority_id"]
            for item in pack["forbidden_authority"]
            if item["forbidden"] is True
        }

        assert clean_room["source_project"] == "nature-skills"
        assert clean_room["vendor_dependency"] is False
        assert clean_room["runtime_dependency"] is False
        assert clean_room["publication_authority"] is False
        assert {
            "vendor_skill_authority",
            "runtime_authority",
            "default_skill_authority",
            "publication_readiness_authority",
            "quality_verdict_authority",
            "mas_truth_write_authority",
        } <= forbidden
        assert pack["publication_readiness_authority"] is False
        assert pack["quality_verdict_authority"] is False
        assert pack["authority_boundary"]["can_write_domain_truth"] is False


def test_nature_skills_adoption_contract_keeps_pattern_owners_non_authoritative() -> None:
    contract = json.loads(ADOPTION_CONTRACT.read_text(encoding="utf-8"))
    adoptions = contract["adoptions"]
    pattern_ids = [item["pattern_id"] for item in adoptions]

    assert set(contract["global_forbidden_authority"]) == GLOBAL_FORBIDDEN_AUTHORITY
    assert len(pattern_ids) == 12
    assert len(pattern_ids) == len(set(pattern_ids))
    assert {item["landing_status"] for item in adoptions} == {
        "contract_projection_landed",
        "owner_surface_landed",
    }
    for adoption in adoptions:
        assert adoption["owner_surfaces"]
        assert "publication_readiness_authority" in adoption["forbidden_authority"]
        assert "quality_verdict_authority" in adoption["forbidden_authority"]
