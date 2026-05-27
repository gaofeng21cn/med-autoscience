from __future__ import annotations

from tests.product_entry_cases.action_catalog_parity_cases.shared import *  # noqa: F403,F401


def test_product_entry_manifest_exposes_life_science_source_discovery_pack(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    stage_quality_contract = importlib.import_module("med_autoscience.stage_quality_contract")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    pack_contract = stage_quality_contract.build_stage_quality_pack_contract()
    descriptor = manifest["family_stage_control_plane_descriptor"]

    assert "life_science_source_discovery_pack" in pack_contract["pack_ids"]
    assert descriptor["source_refs"]["life_science_source_discovery_pack_source"] == (
        "med_autoscience.stage_quality_contract.build_stage_quality_pack_contract"
    )
    assert descriptor["quality_pack_contract"]["source_discovery_pack_ref"] == (
        "/product_entry_manifest/stage_quality_pack_contract/packs/life_science_source_discovery_pack"
    )
    assert descriptor["quality_pack_contract"]["external_source_plugin_dependency"] is False
    assert descriptor["quality_pack_contract"]["source_discovery_authority"] is False
    assert manifest["stage_quality_pack_contract"] == pack_contract
