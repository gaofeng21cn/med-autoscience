from __future__ import annotations

import importlib

from .shared import *  # noqa: F403,F401


def test_mas_action_catalog_drives_cli_product_entry_skill_and_mcp_metadata(tmp_path: Path) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()
    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    skill_catalog = product_entry.build_skill_catalog(profile=profile, profile_ref=profile_ref)
    mcp_tools = {tool["name"]: tool for tool in mcp_server.build_tool_manifest()}

    assert manifest["family_action_catalog"] == catalog
    assert skill_catalog["action_catalog"] == catalog
    assert catalog["authority_boundary"] == {
        "domain_truth_owner": "MedAutoScience",
        "opl_role": "projection_consumer_only",
        "write_policy": "no_domain_truth_writes",
    }

    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}
    product_entry_projection = {
        item["action_key"]: item for item in action_catalog.project_mas_action_catalog("product_entry", catalog)
    }
    skill_projection = {
        item["action_id"]: item for item in action_catalog.project_mas_action_catalog("skill", catalog)
    }
    mcp_projection = {
        item["name"]: item for item in action_catalog.project_mas_action_catalog("mcp", neutral_catalog)
    }

    for action_id, cli_item in cli_projection.items():
        assert manifest["product_entry_shell"][action_id]["command"] == cli_item["command"]
        assert manifest["product_entry_shell"][action_id]["surface_kind"] == cli_item["surface_kind"]
        assert manifest["product_entry_shell"][action_id]["purpose"] == cli_item["summary"]

        assert product_entry_projection[action_id]["command"] == cli_item["command"]
        assert product_entry_projection[action_id]["surface_kind"] == cli_item["surface_kind"]
        assert product_entry_projection[action_id]["summary"] == cli_item["summary"]

        assert skill_projection[action_id]["command"] == cli_item["command"]
        assert skill_projection[action_id]["surface_kind"] == cli_item["surface_kind"]
        assert skill_projection[action_id]["summary"] == cli_item["summary"]

    assert skill_catalog["skills"][0]["domain_projection"]["shell_commands"] == {
        action_id: cli_item["command"] for action_id, cli_item in cli_projection.items()
    }
    assert skill_catalog["skills"][0]["domain_projection"]["action_catalog_projection"] == list(skill_projection.values())

    product_entry_mcp = mcp_projection["product_entry"]
    product_entry_tool = mcp_tools["product_entry"]
    assert product_entry_tool["description"].startswith(product_entry_mcp["description"])
    assert product_entry_tool["inputSchema"]["properties"]["mode"] == product_entry_mcp["input_schema"]
    assert product_entry_tool["metadata"]["action_catalog_projection"] == product_entry_mcp

    assert mcp_tools["study_progress"]["metadata"]["action_catalog_projection"] == mcp_projection["study_progress"]
    assert mcp_tools["study_runtime"]["metadata"]["action_catalog_projection"] == mcp_projection["study_runtime"]


def test_mas_action_catalog_projects_sidecar_bridge_without_new_mcp_tool(tmp_path: Path) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile_ref = tmp_path / "profile.local.toml"
    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()

    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}
    product_entry_projection = {
        item["action_key"]: item for item in action_catalog.project_mas_action_catalog("product_entry", catalog)
    }
    skill_projection = {
        item["action_id"]: item for item in action_catalog.project_mas_action_catalog("skill", catalog)
    }
    mcp_projection = {
        item["name"]: item for item in action_catalog.project_mas_action_catalog("mcp", neutral_catalog)
    }
    mcp_tool_names = {tool["name"] for tool in mcp_server.build_tool_manifest()}

    sidecar_export = cli_projection["sidecar_export"]
    assert sidecar_export["effect"] == "read_only"
    assert sidecar_export["command"] == (
        "medautosci sidecar export --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert sidecar_export["surface_kind"] == "mas_family_sidecar_export"

    sidecar_dispatch = cli_projection["sidecar_dispatch"]
    assert sidecar_dispatch["effect"] == "mutating"
    assert sidecar_dispatch["command"] == "medautosci sidecar dispatch --task <task.json> --format json"
    assert sidecar_dispatch["surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert "guarded dispatch receipt" in sidecar_dispatch["summary"]
    assert "OPL/Hermes typed queue" in sidecar_dispatch["summary"]
    assert "does not authorize domain truth" in sidecar_dispatch["summary"]
    assert "publication quality" in sidecar_dispatch["summary"]
    assert "artifact gate" in sidecar_dispatch["summary"]
    assert "current package" in sidecar_dispatch["summary"]

    assert product_entry_projection["sidecar_export"]["command"] == sidecar_export["command"]
    assert product_entry_projection["sidecar_dispatch"]["command"] == sidecar_dispatch["command"]
    assert skill_projection["sidecar_export"]["effect"] == "read_only"
    assert skill_projection["sidecar_dispatch"]["effect"] == "mutating"

    assert mcp_projection["sidecar_export"]["descriptor_only"] is True
    assert mcp_projection["sidecar_export"]["public_runtime"] is False
    assert mcp_projection["sidecar_dispatch"]["descriptor_only"] is True
    assert mcp_projection["sidecar_dispatch"]["public_runtime"] is False
    assert {"sidecar_export", "sidecar_dispatch"}.isdisjoint(mcp_tool_names)


def test_product_entry_manifest_exposes_mas_family_stage_control_plane_descriptor(tmp_path: Path) -> None:
    agent_entry = importlib.import_module("med_autoscience.agent_entry")
    stage_knowledge_plane = importlib.import_module("med_autoscience.controllers.stage_knowledge_plane")
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    route_payload = agent_entry.load_entry_modes_payload()
    stage_contract = stage_knowledge_plane.stage_knowledge_plane_contract()

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
        "src/med_autoscience/agent_entry/resources/agent_entry_modes.yaml"
    )
    assert descriptor["source_refs"]["knowledge_plane_contract_source"] == (
        "med_autoscience.stage_knowledge_contract.stage_knowledge_plane_contract"
    )
    assert descriptor["source_refs"]["packet_contract_surfaces"] == list(stage_contract["packet_contracts"])

    snapshot = descriptor["route_contract_snapshot"]
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
    assert descriptor["seed_corpus_ref"]["ref"] == (
        "docs/policies/study-workflow/publication_route_memory_seed_fixture.json"
    )
    assert descriptor["seed_corpus_ref"]["role"] == "repo_source_seed_fixture"
    assert descriptor["writeback_receipt_locator_ref"]["ref"] == (
        "portfolio/research_memory/publication_route_memory/writeback_receipts"
    )
    assert descriptor["writeback_receipt_locator_ref"]["role"] == "domain_owned_router_receipts"
    assert descriptor["freshness"]["refresh_policy"] == "rebuild_product_entry_manifest_before_opl_discovery"
    assert descriptor["migration_readiness"]["status"] == "workspace_apply_closure_ready"
    assert descriptor["migration_readiness"]["seed_fixture_status"] == "repo_source_fixture_available"
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
