from __future__ import annotations

from .shared import *  # noqa: F403,F401

def test_product_entry_manifest_exposes_mas_family_stage_control_plane_descriptor(tmp_path: Path) -> None:
    stage_knowledge_plane = importlib.import_module("med_autoscience.controllers.stage_knowledge_plane")
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    stage_route_contract = importlib.import_module("med_autoscience.stage_route_contract")
    stage_surface_contract = importlib.import_module("med_autoscience.stage_surface_contract")
    stage_quality_contract = importlib.import_module("med_autoscience.stage_quality_contract")
    stage_skill_surface_projection = importlib.import_module(
        "med_autoscience.stage_skill_surface_projection"
    )

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    route_payload = stage_route_contract.load_stage_route_contract_payload()
    stage_contract = stage_knowledge_plane.stage_knowledge_plane_contract()
    stage_surface = stage_surface_contract.build_stage_surface_contract()

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    descriptor = manifest["family_stage_control_plane_descriptor"]
    nested_descriptor = manifest["opl_family_persistence_lifecycle_owner_route_adoption"]["payload"][
        "family_stage_control_plane_descriptor"
    ]

    assert descriptor == nested_descriptor
    assert descriptor["surface_kind"] == "family_stage_control_plane_descriptor"
    assert descriptor["domain_id"] == "med-autoscience"
    assert descriptor["capability_id"] == "stage_led_autonomy"
    assert descriptor["source_refs"]["inventory"] == (
        "docs/references/integration/stage_led_autonomy_family_inventory.md"
    )
    assert descriptor["source_refs"]["route_contract_source"] == (
        "agent/stages/stage_route_contract.yaml"
    )
    assert descriptor["source_refs"]["knowledge_plane_contract_source"] == (
        "med_autoscience.stage_knowledge_contract.stage_knowledge_plane_contract"
    )
    assert descriptor["source_refs"]["quality_pack_contract_source"] == (
        "med_autoscience.stage_quality_contract.build_stage_quality_pack_contract"
    )
    assert descriptor["source_refs"]["stage_deliverable_index_contract_source"] == (
        "med_autoscience.stage_surface_contract.build_stage_surface_contract"
    )
    assert descriptor["source_refs"]["packet_contract_surfaces"] == list(stage_contract["packet_contracts"])
    assert descriptor["source_refs"]["quality_pack_contract_surfaces"] == [
        "mas_stage_quality_pack_contract",
        "stage_quality_pack_projection",
    ]
    assert descriptor["source_refs"]["stage_skill_surface_projection_source"] == (
        "med_autoscience.stage_skill_surface_projection.build_stage_skill_surface_projection"
    )

    snapshot = descriptor["route_contract_snapshot"]
    assert snapshot["source"] == "agent/stages/stage_route_contract.yaml"
    assert snapshot["route_ids"] == list(route_payload["route_contracts"])
    assert snapshot["route_count"] == len(route_payload["route_contracts"])
    assert snapshot["entry_mode_count"] == len(route_payload["modes"])
    assert snapshot["descriptor_derives_routes"] is False

    assert descriptor["stage_knowledge_plane"]["exploratory_stages"] == stage_contract["exploratory_stages"]
    assert descriptor["stage_knowledge_plane"]["packet_surfaces"] == list(stage_contract["packet_contracts"])
    assert descriptor["stage_packets"] == {
        "knowledge_packet": "stage_knowledge_packet",
        "memory_closeout_packet": "stage_memory_closeout_packet",
        "memory_write_router_receipt": "memory_write_router_receipt",
        "stage_recall_index": "stage_recall_index",
    }
    assert descriptor["memory_control"]["can_promote_memory_to_evidence"] is False
    assert descriptor["stage_deliverable_index"] == {
        "surface_kind": "mas_stage_deliverable_index",
        "version": "mas-stage-deliverable-index.v1",
        "role": "human_audit_and_opl_locator",
        "stage_count": len(stage_surface["stage_cards"]),
        "locator_ref": "/product_entry_manifest/family_stage_control_plane_descriptor/stage_deliverable_index",
        "stage_refs": stage_surface["stage_deliverable_index"]["stage_refs"],
        "human_review_page_refs": stage_surface["stage_deliverable_index"]["human_review_page_refs"],
        "source_refs": stage_surface["stage_deliverable_index"]["source_refs"],
        "human_review_policy": stage_surface["stage_deliverable_index"]["human_review_policy"],
        "review_page_policy": stage_surface["stage_deliverable_index"]["review_page_policy"],
        "authority_boundary": stage_surface["stage_deliverable_index"]["authority_boundary"],
        "opl_projection_boundary": "read_only_locator_no_truth_write",
        "auto_advance_boundary": {
            "default_blocks_auto_advance": False,
            "blocking_only_when": "mas_human_gate_boundary_triggered",
            "opl_can_block_auto_advance": False,
            "opl_can_mark_publication_ready": False,
        },
    }
    assert descriptor["stage_deliverable_index"]["human_review_policy"]["mode"] == (
        "optional_human_review_annotation"
    )
    assert descriptor["stage_deliverable_index"]["human_review_policy"]["default_blocks_auto_advance"] is False
    assert descriptor["stage_deliverable_index"]["human_review_policy"]["annotation_can_authorize_quality_verdict"] is False
    assert descriptor["stage_deliverable_index"]["human_review_policy"][
        "annotation_can_authorize_submission_readiness"
    ] is False
    assert descriptor["stage_deliverable_index"]["review_page_policy"]["paper_asset_delta_policy"][
        "can_authorize_artifact_authority"
    ] is False
    assert descriptor["stage_deliverable_index"]["review_page_policy"]["claim_trace_policy"][
        "can_authorize_quality_verdict"
    ] is False
    assert descriptor["stage_deliverable_index"]["review_page_policy"]["freshness_signal_policy"][
        "freshness_signal_can_authorize_submission_readiness"
    ] is False
    quality_pack_contract = stage_quality_contract.build_stage_quality_pack_contract()
    assert descriptor["quality_pack_contract"] == {
        "surface_kind": "stage_quality_pack_projection",
        "contract_ref": "med_autoscience.stage_quality_contract.build_stage_quality_pack_contract",
        "pack_ids": list(stage_quality_contract.REQUIRED_STAGE_QUALITY_PACK_IDS),
        "pack_count": len(stage_quality_contract.REQUIRED_STAGE_QUALITY_PACK_IDS),
        "pack_role": "quality_input_and_reviewer_rubric",
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "freshness_ref": "/product_entry_manifest/stage_quality_pack_contract/freshness",
        "locator_ref": "/product_entry_manifest/stage_quality_pack_contract/pack_locators",
        "authority_boundary_ref": "/product_entry_manifest/stage_quality_pack_contract/authority_boundary",
    }
    stage_skill_projection = stage_skill_surface_projection.build_stage_skill_surface_projection()
    assert descriptor["stage_skill_surface_projection"] == stage_skill_projection
    assert manifest["stage_skill_surface_projection"] == stage_skill_projection
    assert set(stage_skill_projection) == {
        "surface_kind",
        "version",
        "skill_locator",
        "freshness",
        "quality_pack_refs",
        "stage_card_ref",
        "authority_boundary",
    }
    assert stage_skill_projection["surface_kind"] == "stage_skill_surface_projection"
    assert stage_skill_projection["skill_locator"] == {
        "ref_kind": "json_pointer",
        "ref": "/skill_catalog/skills/0",
        "role": "mas_domain_skill_descriptor",
    }
    assert stage_skill_projection["quality_pack_refs"] == list(
        stage_quality_contract.REQUIRED_STAGE_QUALITY_PACK_IDS
    )
    assert stage_skill_projection["stage_card_ref"]["ref"] == (
        "/product_entry_manifest/family_stage_control_plane/stages"
    )
    assert stage_skill_projection["freshness"]["refresh_policy"] == (
        "rebuild_product_entry_manifest_before_opl_discovery"
    )
    assert stage_skill_projection["authority_boundary"] == {
        "truth_owner": "MedAutoScience",
        "quality_owner": "MedAutoScience",
        "publication_readiness_owner": "MedAutoScience",
        "opl_role": "descriptor_ref_freshness_locator_consumer",
        "allowed_fields": [
            "skill_locator",
            "freshness",
            "quality_pack_refs",
            "stage_card_ref",
            "authority_boundary",
        ],
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_close_paper": False,
    }
    assert manifest["stage_quality_pack_contract"] == quality_pack_contract
    assert quality_pack_contract["authority_boundary"]["pack_role"] == "quality_input_and_reviewer_rubric"
    assert quality_pack_contract["authority_boundary"]["publication_readiness_authority"] is False
    assert quality_pack_contract["authority_boundary"]["opl_can_write_mas_truth"] is False
    assert quality_pack_contract["freshness"]["refresh_policy"] == (
        "rebuild_product_entry_manifest_before_opl_discovery"
    )
    assert set(stage_quality_contract.REQUIRED_STAGE_QUALITY_PACK_IDS) == set(
        quality_pack_contract["pack_ids"]
    )
    journal_pack = {
        pack["pack_id"]: pack for pack in quality_pack_contract["packs"]
    }["journal_response_pack"]
    assert journal_pack["clean_room_absorption"] == {
        "source_project": "nature-skills",
        "absorbed_as": "mas_native_contract_pattern",
        "vendor_dependency": False,
        "runtime_dependency": False,
        "publication_authority": False,
        "default_skill_source": False,
    }
    assert journal_pack["authority_boundary"]["can_write_domain_truth"] is False
    reporting_pack = {
        pack["pack_id"]: pack for pack in quality_pack_contract["packs"]
    }["reporting_guideline_pack"]
    ai_ml_selection = {
        selection["study_archetype"]: selection for selection in reporting_pack["guideline_selection"]
    }["ai_ml_medical_study"]
    assert ai_ml_selection["requires_clinical_base_guideline"] is True
    assert "dispatch_mas_exported_task" in descriptor["allowed_family_actions"]
    assert "replace_route_contract" in descriptor["forbidden_family_actions"]

    authority = descriptor["authority_boundary"]
    assert authority["opl_role"] == "read_only_descriptor_consumer"
    assert authority["can_write_domain_truth"] is False
    assert authority["can_authorize_publication_quality"] is False
    assert authority["can_authorize_submission_readiness"] is False
    assert authority["publication_eval_owner"] == "MedAutoScience"
    assert authority["publication_gate_owner"] == "MedAutoScience"

    stage_plane = manifest["family_stage_control_plane"]
    assert stage_plane["surface_kind"] == "family_stage_control_plane"
    assert stage_plane["version"] == "family-stage-control-plane.v1"
    assert stage_plane["plane_id"] == "med_autoscience_stage_control_plane"
    assert stage_plane["target_domain_id"] == "med-autoscience"
    assert stage_plane["authority_boundary"]["opl_role"] == "projection_consumer_only"
    assert stage_plane["authority_boundary"]["can_write_domain_truth"] is False
    assert stage_plane["authority_boundary"]["can_authorize_publication_quality"] is False
    assert stage_plane["authority_boundary"]["can_authorize_submission_readiness"] is False
    assert stage_plane["stage_action_parity"]["status"] == "aligned"
    assert stage_plane["stage_action_parity"]["missing_action_refs"] == []
    assert stage_plane["freshness"]["refresh_policy"] == "rebuild_product_entry_manifest_before_opl_discovery"
    assert {
        "direction_and_route_selection",
        "baseline_and_evidence_setup",
        "bounded_analysis_campaign",
        "manuscript_authoring",
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    } == {stage["stage_id"] for stage in stage_plane["stages"]}

    action_ids = {action["action_id"] for action in manifest["family_action_catalog"]["actions"]}
    route_ids = set(route_payload["route_contracts"])
    for stage in stage_plane["stages"]:
        assert stage["owner"] == "MedAutoScience"
        assert stage["authority_boundary"]["maps_existing_routes_only"] is True
        assert stage["authority_boundary"]["can_replace_route_contract"] is False
        assert set(stage["allowed_action_refs"]) <= action_ids
        assert set(stage["domain_stage_refs"]) <= route_ids
        assert stage["handoff"]["next_owner"] == "MedAutoScience"
        assert stage["freshness"]["stale_if_source_refs_missing"] is True
        assert any(ref["role"] == "deep_descriptor" for ref in stage["source_refs"])
        assert any(ref["role"] == "stage_deliverable_index" for ref in stage["source_refs"])
        assert {"ref_kind": "repo_path", "ref": "agent/stages/stage_route_contract.yaml", "role": "route_contract"} in stage[
            "prompt_refs"
        ]
        assert stage["deliverable_index_ref"] == {
            "ref_kind": "json_pointer",
            "ref": "/product_entry_manifest/family_stage_control_plane_descriptor/stage_deliverable_index",
            "role": "stage_deliverable_index",
            "opl_projection_boundary": "read_only_locator_no_truth_write",
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "human_review_blocks_auto_advance_by_default": False,
            "blocking_only_when": "mas_human_gate_boundary_triggered",
        }
        assert set(stage["quality_pack_refs"]) <= set(quality_pack_contract["pack_ids"])
        assert stage["quality_pack_projection"]["role"] == "quality_input_and_reviewer_rubric"
        assert stage["quality_pack_projection"]["publication_readiness_authority"] is False
        assert stage["quality_pack_projection"]["quality_verdict_authority"] is False
        assert stage["quality_pack_projection"]["locator_ref"] == (
            "/product_entry_manifest/stage_quality_pack_contract/pack_locators"
        )
        assert stage["stage_skill_surface_projection"]["surface_kind"] == "stage_skill_surface_projection"
        assert stage["stage_skill_surface_projection"]["stage_card_ref"]["ref"] == (
            f"/product_entry_manifest/family_stage_control_plane/stages/{stage['stage_id']}"
        )
        assert set(stage["stage_skill_surface_projection"]) == set(stage_skill_projection)
        assert stage["stage_skill_surface_projection"]["authority_boundary"]["can_close_paper"] is False
        assert stage["authority_boundary"]["can_authorize_publication_quality"] is False


