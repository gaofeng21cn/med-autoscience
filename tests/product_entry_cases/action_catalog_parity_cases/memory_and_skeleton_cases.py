from __future__ import annotations

from .shared import *  # noqa: F403,F401

def test_product_entry_manifest_exposes_publication_route_memory_descriptor(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    descriptor = manifest["domain_memory_descriptor"]

    assert descriptor["surface_kind"] == "family_domain_memory_ref"
    assert descriptor["version"] == "family-domain-memory-ref.v1"
    assert descriptor["memory_ref_id"] == "mas_publication_route_memory"
    assert descriptor["target_domain_id"] == "med-autoscience"
    assert descriptor["owner"] == "MedAutoScience"
    assert descriptor["memory_family"] == "publication_route_memory"
    assert descriptor["memory_pack_ref"]["ref"] == "docs/policies/study-workflow/publication_route_memory_policy.md"
    assert descriptor["memory_pack_ref"]["workspace_locator"] == "portfolio/research_memory/publication_route_memory"
    assert descriptor["stage_applicability"] == ["scout", "idea", "decision", "analysis-campaign", "review"]
    assert descriptor["retrieval_contract_ref"]["ref"] == "stage_knowledge_packet"
    assert descriptor["writeback_contract_ref"]["ref"] == "stage_memory_closeout_packet"
    assert descriptor["receipt_contract_ref"]["ref"] == "memory_write_router_receipt"
    assert descriptor["recall_projection_ref"]["ref"] == "stage_recall_index"
    assert descriptor["migration_plan_ref"]["ref"] == (
        "docs/policies/study-workflow/publication_route_memory_policy.md#migration-plan"
    )
    assert descriptor["migration_plan_ref"]["role"] == "domain_owned_migration_plan"
    assert descriptor["canonical_body_ref"]["ref"] == (
        "docs/policies/study-workflow/publication_route_memory_library.md"
    )
    assert descriptor["canonical_body_ref"]["role"] == "markdown_first_memory_body"
    assert descriptor["canonical_body_ref"]["opl_body_owner"] is False
    assert descriptor["seed_corpus_ref"]["ref"] == (
        "docs/policies/study-workflow/publication_route_memory_seed_fixture.json"
    )
    assert descriptor["seed_corpus_ref"]["role"] == "repo_source_seed_index"
    assert descriptor["writeback_receipt_locator_ref"]["ref"] == (
        "portfolio/research_memory/publication_route_memory/writeback_receipts"
    )
    assert descriptor["writeback_receipt_locator_ref"]["role"] == "domain_owned_router_receipts"
    assert descriptor["freshness"]["refresh_policy"] == "rebuild_product_entry_manifest_before_opl_discovery"
    assert descriptor["migration_readiness"]["status"] == "workspace_apply_closure_ready"
    assert descriptor["migration_readiness"]["canonical_body_status"] == "markdown_source_available"
    assert descriptor["migration_readiness"]["seed_index_status"] == "repo_source_index_available"
    assert descriptor["migration_readiness"]["memory_body_migration"] == "domain_owned_workspace_apply_available"
    assert descriptor["migration_readiness"]["writeback_receipt_locator_status"] == "workspace_locator_declared"
    assert descriptor["migration_readiness"]["opl_apply_allowed"] is False

    authority = descriptor["authority_boundary"]
    assert authority["opl_role"] == "locator_projection_owner"
    assert authority["domain_memory_owner"] == "MedAutoScience"
    assert "memory_store_owner" in authority["forbidden_opl_authority"]
    assert "publication_route_decision_owner" in authority["forbidden_opl_authority"]
    assert authority["can_write_domain_truth"] is False
    assert authority["can_authorize_quality_verdict"] is False
    assert authority["can_authorize_publication_quality"] is False
    assert authority["can_authorize_submission_readiness"] is False
    assert authority["can_promote_memory_to_evidence"] is False
    assert authority["can_write_artifacts"] is False

    stage_plane = manifest["family_stage_control_plane"]
    stages_with_route_memory = {
        stage["stage_id"]
        for stage in stage_plane["stages"]
        if any(ref["ref"] == "mas_publication_route_memory" for ref in stage.get("knowledge_refs", []))
    }
    assert {
        "direction_and_route_selection",
        "bounded_analysis_campaign",
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    } <= stages_with_route_memory
    assert "baseline_and_evidence_setup" not in stages_with_route_memory


def test_standard_domain_agent_skeleton_projects_quality_pack_locator_without_authority(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    skeleton = manifest["standard_domain_agent_skeleton"]

    assert skeleton["mapping_mode"] == "repo_source_physical_anchors_landed"
    anchors = skeleton["repo_source_anchor_status"]
    assert anchors["status"] == "landed"
    assert anchors["missing_anchor_ids"] == []
    assert {item["anchor_id"] for item in anchors["anchors"]} == {
        "agent",
        "contracts",
        "runtime",
        "docs",
    }
    assert all(item["exists"] is True for item in anchors["anchors"])
    assert all(item["body_included"] is False for item in anchors["anchors"])
    quality_locator = skeleton["quality_pack_locator"]
    assert quality_locator == {
        "ref_kind": "json_pointer",
        "ref": "/product_entry_manifest/stage_quality_pack_contract",
        "freshness_ref": "/product_entry_manifest/stage_quality_pack_contract/freshness",
        "locator_ref": "/product_entry_manifest/stage_quality_pack_contract/pack_locators",
        "authority_boundary_ref": "/product_entry_manifest/stage_quality_pack_contract/authority_boundary",
        "opl_projection_boundary": "descriptor_ref_freshness_locator_only",
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
    }
    assert "src/med_autoscience/stage_quality_contract.py" in skeleton["skeleton"]["agent/quality_gates"]
    assert skeleton["default_new_surface_slots"]["quality"] == "agent/quality_gates"
    assert "agent/stages/stage_route_contract.yaml" in skeleton["skeleton"]["agent/stages"]
    quality_slot = {
        item["slot_id"]: item for item in skeleton["physical_skeleton_layout_audit"]["slots"]
    }["agent/quality_gates"]
    assert skeleton["physical_skeleton_layout_audit"]["status"] == "repo_source_physical_anchors_landed"
    assert quality_slot["surface_class"] == "quality"
    assert quality_slot["default_for_new_surfaces"] is True
    assert quality_slot["repo_paths"][0] == "src/med_autoscience/stage_quality_contract.py"
    assert skeleton["authority_boundary"]["forbidden_opl_authority"] == [
        "domain_truth",
        "quality_verdict",
        "canonical_artifact_blob",
        "publication_or_export_gate",
    ]


def test_manifest_exposes_body_free_workspace_runtime_evidence_receipt_with_typed_blocker(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    receipt = manifest["workspace_runtime_evidence_receipt"]

    assert receipt == manifest["opl_provider_ready_contract"]["workspace_runtime_evidence_receipt"]
    assert receipt["surface_kind"] == "mas_workspace_runtime_evidence_receipt"
    assert receipt["mode"] == "body_free_refs_only"
    assert receipt["status"] == "typed_blocker"
    assert receipt["typed_blocker"]["blocker_id"] == "mas_live_workspace_runtime_owner_receipt_missing"
    assert receipt["owner_receipt_refs"] == []
    assert receipt["locator_ref"] == "/product_entry_manifest/workspace_runtime_artifact_root_locator"
    assert receipt["live_apply_claims"] == {
        "provider_hosted_live_apply_claimed": False,
        "long_soak_claimed": False,
        "publication_closure_claimed": False,
        "paper_progress_requires_mas_owner_receipt": True,
    }
    assert any(
        ref["role"] == "study_root" and ref["study_id"] == "001-risk" and ref["exists"] is True
        for ref in receipt["observed_refs"]
    )
    assert all(ref["body_included"] is False for ref in receipt["observed_refs"])
    assert all(ref["write_permitted"] is False for ref in receipt["observed_refs"])
    assert receipt["authority_boundary"]["can_authorize_submission_readiness"] is False


def test_workspace_runtime_evidence_receipt_observes_mas_owner_receipt_refs(
    tmp_path: Path,
) -> None:
    adapter = importlib.import_module("med_autoscience.controllers.opl_provider_ready_adapter")

    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    owner_receipt = study_root / "artifacts" / "runtime" / "owner_route" / "latest.json"
    write_text(
        owner_receipt,
        json.dumps(
            {
                "surface_kind": "mas_owner_route_receipt",
                "study_id": "001-risk",
                "result": "typed_blocker",
                "body_included": False,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    receipt = adapter.build_workspace_runtime_evidence_receipt_surface(profile=profile)

    assert receipt["status"] == "workspace_runtime_evidence_refs_observed"
    assert receipt["typed_blocker"] is None
    assert receipt["owner_receipt_refs"] == [str(owner_receipt)]
    owner_refs = [ref for ref in receipt["observed_refs"] if ref["role"] == "owner_route_receipt"]
    assert owner_refs == [
        {
            "ref_kind": "workspace_path",
            "role": "owner_route_receipt",
            "ref": str(owner_receipt),
            "exists": True,
            "body_included": False,
            "write_permitted": False,
            "study_id": "001-risk",
        }
    ]
    assert receipt["live_apply_claims"]["publication_closure_claimed"] is False
