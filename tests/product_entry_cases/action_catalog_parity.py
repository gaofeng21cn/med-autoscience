from __future__ import annotations

import importlib
import json

from .shared import *  # noqa: F403,F401


def _write_opl_production_proof(path: Path) -> None:
    checks = {
        "external_temporal_server_reachable": True,
        "managed_worker_ready": True,
        "worker_completed_attempt": True,
        "worker_restart_requery": True,
        "signal_history_preserved": True,
        "typed_closeout_required_for_completed": True,
        "missing_closeout_blocks_completion": True,
        "retry_or_dead_letter_boundary_observed": True,
        "domain_truth_boundary_preserved": True,
    }
    path.write_text(
        json.dumps(
            {
                "family_runtime_residency_proof": {
                    "surface_kind": "opl_temporal_production_residency_proof",
                    "provider_kind": "temporal",
                    "closeout_status": "production_residency_proven",
                    "production_residency_proof": {
                        "surface_kind": "opl_temporal_external_production_residency_proof",
                        "provider_kind": "temporal",
                        "closeout_status": "production_residency_proven",
                        "runtime_snapshot": {
                            "address_source": "managed_local_service_state",
                            "lifecycle_status": "ready",
                            "server_reachable": True,
                            "worker_ready": True,
                            "task_queue": "opl-stage-attempts",
                        },
                        "proof_receipt": {
                            "receipt_kind": "temporal_production_residency_proof",
                            "receipt_status": "proven",
                            "completed_workflow_id": "wf-complete",
                            "blocked_workflow_id": "wf-blocked",
                        },
                        "checks": checks,
                    },
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


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
    assert "OPL provider queue" in sidecar_dispatch["summary"]
    assert "explicit OPL opt-in executor/proof refs only" in sidecar_dispatch["summary"]
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


def test_product_entry_manifest_exposes_foundry_agent_product_positioning(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    positioning = manifest["product_positioning"]

    assert positioning["surface_kind"] == "mas_product_positioning"
    assert positioning["public_role"] == "Foundry Agent"
    assert positioning["package_role"] == "OPL-compatible package built on OPL Framework"
    assert positioning["framework"] == "OPL Framework"
    assert positioning["direct_app_skill_path"] is True
    assert positioning["authority_boundary"] == {
        "medical_research_truth_owner": "MedAutoScience",
        "quality_verdict_owner": "MedAutoScience",
        "runtime_owner": "OPL provider/runtime manager for generic cadence; MedAutoScience for domain owner receipts",
        "artifact_publication_authority_owner": "MedAutoScience",
        "opl_role": "framework_package_host_and_projection_consumer",
        "opl_is_runtime_kernel": False,
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
    }
    assert set(positioning["non_goals"]) == {
        "no_new_runtime_mechanism",
        "not_an_opl_runtime_kernel_claim",
        "not_a_default_hermes_target",
        "not_a_default_mds_target",
        "not_a_default_local_scheduler_target",
    }


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


def test_product_entry_manifest_exposes_provider_guarded_soak_read_model_with_typed_blockers(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    provider_contract = manifest["opl_provider_ready_contract"]
    read_model = manifest["provider_guarded_soak_read_model"]

    assert read_model == provider_contract["provider_guarded_soak_read_model"]
    assert read_model["surface_kind"] == "provider_guarded_soak_read_model"
    assert read_model["version"] == "provider-guarded-soak-read-model.v1"
    assert read_model["mode"] == "descriptor_read_model"
    assert read_model["target_studies"] == ["DM002", "DM003", "Obesity"]
    assert read_model["expected_surface_shape"] == {
        "provider_proof_surface": "real_paper_autonomy_provider_hosted_paper_proof",
        "guarded_apply_surface": "real_paper_autonomy_guarded_apply_proof",
        "closeout_packet_surface": "domain_stage_closeout_packet",
        "typed_blocker_surface": "mas_provider_guarded_soak_typed_blocker",
    }
    assert read_model["provider_availability"]["status"] == "typed_blocker"
    assert read_model["provider_availability"]["provider_attempt_available"] is False
    assert read_model["provider_availability"]["blocker"]["blocker_id"] == (
        "provider_guarded_soak_provider_unavailable"
    )
    assert read_model["provider_completion_semantics"] == {
        "provider_completion_is_paper_closure": False,
        "queue_completion_is_paper_closure": False,
        "paper_closure_requires_mas_owner_receipt": True,
        "mutation_proof_surface": "MAS owner receipt",
    }

    coverage = {item["target_study"]: item for item in read_model["target_coverage"]}
    assert set(coverage) == {"DM002", "DM003", "Obesity"}
    assert all(item["status"] == "typed_blocker" for item in coverage.values())
    assert all(item["write_permitted"] is False for item in coverage.values())
    assert all(item["provider_completion_is_paper_closure"] is False for item in coverage.values())
    assert all(item["paper_closure_requires_mas_owner_receipt"] is True for item in coverage.values())

    proof = read_model["no_forbidden_write_proof"]
    assert proof["surface_kind"] == "mas_opl_forbidden_write_guard_proof"
    assert proof["result"] == "blocked_provider_completion_is_not_paper_closure"
    assert proof["provider_completion_is_paper_closure"] is False
    assert proof["queue_completion_is_paper_closure"] is False
    assert proof["paper_closure_requires_mas_owner_receipt"] is True
    assert proof["only_mas_owner_receipt_can_prove_mutation"] is True
    assert proof["can_write_domain_truth"] is False
    assert proof["can_write_current_package"] is False
    assert proof["can_authorize_publication_quality"] is False

    owner_contract = manifest["owner_receipt_contract"]
    assert owner_contract == provider_contract["owner_receipt_contract"]
    assert manifest["domain_owner_receipt_contract"] == owner_contract
    assert owner_contract["surface_kind"] == "domain_owner_receipt_contract"
    assert owner_contract["accepted_return_shapes"] == [
        "domain_receipt",
        "typed_blocker",
        "no_regression_evidence",
    ]
    assert owner_contract["receipt_ref_policy"]["opl_persists"] == "receipt_refs_only"
    assert owner_contract["receipt_ref_policy"]["memory_body_externalized"] is True
    assert owner_contract["typed_blocker"]["blocker_id"] == "mas_live_owner_receipt_soak_pending"
    assert owner_contract["forbidden_write_guard"]["forbidden_requested_writes"] == []
    assert owner_contract["authority_boundary"]["can_write_domain_truth"] is False
    assert owner_contract["authority_boundary"]["can_write_artifact_gate"] is False
    assert owner_contract["authority_boundary"]["can_write_memory_body"] is False

    lifecycle_requests = manifest["lifecycle_apply_requests"]
    lifecycle_proof = manifest["lifecycle_guarded_apply_proof"]
    assert lifecycle_requests == provider_contract["lifecycle_apply_requests"]
    assert lifecycle_proof == provider_contract["lifecycle_guarded_apply_proof"]
    assert {request["action_kind"] for request in lifecycle_requests} == {
        "cleanup",
        "restore",
        "retention",
    }
    assert any(
        request["owner_scope"] == "opl_owned_ledger"
        and request["domain_receipt_required"] is False
        for request in lifecycle_requests
    )
    assert all(
        request["domain_receipt_required"] is True
        for request in lifecycle_requests
        if request["owner_scope"] == "domain_owned_artifact"
    )
    assert lifecycle_proof["apply_status"] == "blocked_domain_receipt_required"
    assert lifecycle_proof["domain_receipt_required_count"] == 2
    assert lifecycle_proof["domain_receipt_refs"] == []
    assert lifecycle_proof["authority_boundary"]["opl_can_apply_owned_ledger_or_locator"] is True
    assert lifecycle_proof["authority_boundary"]["opl_writes_domain_artifact"] is False
    assert lifecycle_proof["authority_boundary"]["domain_artifact_mutation_requires_mas_receipt"] is True

    assert manifest["skill_catalog"]["skills"][0]["domain_projection"][
        "stage_skill_surface_projection"
    ] == manifest["stage_skill_surface_projection"]


def test_product_entry_manifest_consumes_opl_production_proof_for_provider_availability(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    proof_ref = tmp_path / "opl-production-proof.json"
    _write_opl_production_proof(proof_ref)

    manifest = product_entry.build_product_entry_manifest(
        profile=profile,
        profile_ref=profile_ref,
        opl_production_proof_ref=proof_ref,
    )
    read_model = manifest["provider_guarded_soak_read_model"]
    availability = read_model["provider_availability"]

    assert manifest["opl_provider_ready_contract"]["provider_topology"]["provider_state"] == (
        "production_residency_proven"
    )
    assert availability["status"] == "available"
    assert availability["provider_attempt_available"] is True
    assert availability["proof_ref"] == str(proof_ref)
    assert availability["proof_receipt"]["receipt_status"] == "proven"
    assert availability["runtime_snapshot"]["worker_ready"] is True
    managed_state = manifest["managed_temporal_state_consistency"]
    assert managed_state == manifest["opl_provider_ready_contract"]["managed_temporal_state_consistency"]
    assert managed_state["status"] == "consistent"
    assert managed_state["managed_state"]["address_source"] == "managed_local_service_state"
    assert managed_state["managed_state"]["lifecycle_status"] == "ready"
    assert managed_state["managed_state"]["server_reachable"] is True
    assert managed_state["managed_state"]["worker_ready"] is True
    assert managed_state["opl_status_projection"] == {
        "provider": "temporal",
        "read_model_owner": "one-person-lab",
        "managed_service_state": "ready",
        "worker_state": "ready",
        "attempt_query_ready": True,
        "retry_dead_letter_state_visible": True,
    }
    assert managed_state["authority_boundary"]["can_write_domain_truth"] is False
    assert availability["semantics"]["provider_completion_is_paper_closure"] is False
    assert availability["semantics"]["paper_closure_requires_mas_owner_receipt"] is True
    assert read_model["provider_completion_semantics"]["paper_closure_requires_mas_owner_receipt"] is True
    assert read_model["no_forbidden_write_proof"]["result"] == "configured"
    assert all(
        item["status"] == "provider_available_guarded_apply_pending"
        for item in read_model["target_coverage"]
    )
    assert all(item["write_permitted"] is False for item in read_model["target_coverage"])
    assert all(
        item["paper_closure_requires_mas_owner_receipt"] is True
        for item in read_model["target_coverage"]
    )
    residency_read_model = manifest["provider_residency_read_model"]
    assert residency_read_model == manifest["opl_provider_ready_contract"]["provider_residency_read_model"]
    assert residency_read_model["status"] == "ready"
    assert all(item["status"] == "receipt_observed" for item in residency_read_model["checks"])
    assert residency_read_model["authority_boundary"]["can_write_domain_truth"] is False
    tombstone = manifest["legacy_retirement_tombstone_proof"]
    assert tombstone == manifest["opl_provider_ready_contract"]["legacy_retirement_tombstone_proof"]
    assert tombstone["surface_kind"] == "mas_legacy_retirement_tombstone_proof"
    assert tombstone["status"] == "no_active_default_caller_proven"
    assert tombstone["active_default_callers"] == []
    assert {item["classification"] for item in tombstone["retired_or_tombstoned_surfaces"]} == {
        "explicit_optional_executor_adapter",
        "retired_no_default_caller",
        "fixture_or_provenance_only",
        "standalone_diagnostics_only",
    }
    assert tombstone["physical_tombstone_refs"] == [
        "contracts/runtime/legacy-active-path-tombstones.json",
        "docs/history/runtime/legacy_active_path_tombstones.md",
    ]
    assert tombstone["removal_policy"]["current_action"] == "legacy_active_path_tombstones_landed"
    assert tombstone["authority_boundary"]["can_authorize_submission_readiness"] is False
def test_product_entry_manifest_exposes_provider_residency_typed_blocker(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    provider_contract = manifest["opl_provider_ready_contract"]
    read_model = manifest["provider_residency_read_model"]

    assert read_model == provider_contract["provider_residency_read_model"]
    assert read_model["surface_kind"] == "provider_runtime_residency_read_model"
    assert read_model["version"] == "provider-runtime-residency-read-model.v1"
    assert read_model["status"] == "typed_blocker"
    assert read_model["provider_owner"] == "one-person-lab"
    assert read_model["domain_owner"] == "med-autoscience"
    assert read_model["provider_available"] is False
    assert read_model["required_evidence"] == [
        "temporal_production_residency",
        "worker_restart_requery",
        "retry_dead_letter",
        "long_soak_receipt",
    ]
    assert {item["check_id"] for item in read_model["checks"]} == set(read_model["required_evidence"])
    assert all(item["status"] == "typed_blocker" for item in read_model["checks"])
    assert all(item["body_included"] is False for item in read_model["checks"])
    assert all(item["write_permitted"] is False for item in read_model["checks"])
    assert read_model["typed_blocker"]["blocker_id"] == "production_provider_residency_evidence_missing"
    assert read_model["typed_blocker"]["missing_evidence"] == read_model["required_evidence"]
    assert read_model["consumer_contract"]["mas_owned_provider_kernel"] is False
    assert read_model["consumer_contract"]["provider_completion_is_paper_closure"] is False
    assert read_model["consumer_contract"]["queue_completion_is_paper_closure"] is False
    assert read_model["consumer_contract"]["paper_progress_requires_mas_owner_receipt"] is True
    assert read_model["authority_boundary"]["can_write_domain_truth"] is False
    assert read_model["authority_boundary"]["can_write_current_package"] is False
    assert read_model["authority_boundary"]["can_authorize_publication_quality"] is False
    assert read_model["authority_boundary"]["can_write_memory_body"] is False


def test_provider_residency_read_model_requires_all_opl_receipts() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.opl_provider_ready_adapter")

    payload = adapter.build_provider_residency_read_model(
        provider_available=True,
        receipt_refs={
            "temporal_production_residency": "opl://provider/temporal-residency.json",
            "worker_restart_requery": "opl://provider/worker-restart.json",
            "retry_dead_letter": "opl://provider/retry-dead-letter.json",
            "long_soak_receipt": "opl://provider/long-soak.json",
        },
    )

    assert payload["status"] == "ready"
    assert payload["typed_blocker"] is None
    assert all(item["status"] == "receipt_observed" for item in payload["checks"])
    assert all(item["body_included"] is False for item in payload["checks"])
    assert payload["consumer_contract"]["mas_consumes"] == [
        "sidecar_task",
        "typed_receipt",
        "receipt_refs",
    ]
    assert payload["authority_boundary"]["can_write_domain_truth"] is False
    assert payload["authority_boundary"]["can_authorize_publication_quality"] is False

    missing = adapter.build_provider_residency_read_model(
        provider_available=True,
        receipt_refs={
            "temporal_production_residency": "opl://provider/temporal-residency.json",
        },
    )
    assert missing["status"] == "typed_blocker"
    assert missing["typed_blocker"]["missing_evidence"] == [
        "worker_restart_requery",
        "retry_dead_letter",
        "long_soak_receipt",
    ]


def test_product_entry_manifest_exposes_legacy_residue_audit_without_default_callers(
    tmp_path: Path,
) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    audit = manifest["legacy_residue_audit"]

    assert audit["surface_kind"] == "mas_legacy_residue_audit"
    assert audit["status"] == "default_callers_retired_with_references_retained"
    assert audit["scan_policy"] == {
        "docs_are_not_machine_truth": True,
        "stale_term_scan_is_review_input_only": True,
        "delete_only_when_replacement_proof_and_no_default_caller": True,
    }
    assert audit["summary"]["default_caller_count"] == 0
    assert audit["summary"]["cleanup_pending_count"] == 0
    assert audit["summary"]["tombstoned_count"] == 1
    assert audit["summary"]["retired_no_default_caller_count"] == 1
    assert "provider_runtime_residency_read_model" in audit["replacement_surfaces"]
    by_id = {item["residue_id"]: item for item in audit["findings"]}
    assert by_id["hermes_agent_executor_adapter"]["default_caller"] is False
    assert by_id["hermes_agent_executor_adapter"]["disposition"] == "retain_reference"
    assert by_id["hermes_gateway_cron_scheduler"]["disposition"] == "retired_no_default_caller"
    assert by_id["med_deepscientist_backend_reference"]["current_role"] == (
        "historical_fixture_provenance_parity_oracle"
    )
    assert by_id["hosted_runtime_binding_wording"]["disposition"] == "tombstoned"
    assert by_id["hosted_runtime_binding_wording"]["delete_allowed"] is False
    assert "contracts/runtime/legacy-active-path-tombstones.json" in by_id[
        "hosted_runtime_binding_wording"
    ]["replacement_proof_refs"]
    assert all(item["body_included"] is False for item in audit["findings"])
    assert audit["authority_boundary"]["audit_can_delete_code"] is False
    assert audit["authority_boundary"]["audit_can_change_runtime_defaults"] is False


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
