from __future__ import annotations

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
    assert catalog["authority_boundary"] | {
        "domain_truth_owner": "MedAutoScience",
        "opl_role": "projection_consumer_only",
        "write_policy": "no_domain_truth_writes",
        "descriptor_projection_owner": "one-person-lab",
        "domain_handler_target_owner": "MedAutoScience",
    } == catalog["authority_boundary"]
    assert catalog["catalog_role"] == (
        "domain_action_intent_and_handler_target_input_for_opl_generated_descriptors"
    )
    assert catalog["descriptor_projection_owner"] == "one-person-lab"
    assert catalog["domain_handler_target_owner"] == "MedAutoScience"
    assert catalog["domain_repo_can_own_generated_surface"] is False

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


def test_product_entry_manifest_exposes_functional_consumer_boundary(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    boundary = manifest["functional_consumer_boundary"]

    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["status"] == "opl_consumes_generic_surfaces_mas_retains_domain_authority_pack"
    assert boundary["consumer_role"] == "domain_authority_pack_thin_program_surface"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert boundary["no_active_caller_required"] is True
    assert boundary["no_active_caller_proof"]["default_caller_count"] == 0
    assert boundary["no_active_caller_proof"]["default_manager"] == "opl"
    assert boundary["legacy_local_scheduler_cleanup_only_proof"]["install_allowed"] is False
    assert boundary["runtime_lifecycle_sqlite_role"]["mas_may_claim_generic_persistence_engine"] is False
    assert boundary["mas_does_not_own"] == [
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_transition_runner",
        "generic_workbench",
        "generic_memory_locator",
        "generic_artifact_lifecycle",
        "generic_observability",
    ]
    assert set(boundary["mas_retains"]) == {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "memory_writeback_decision",
        "domain_transition_table",
        "owner_receipt",
        "typed_blocker",
        "safe_action_refs",
    }
    assert boundary["declarative_pack_compiler_input"]["compiler_owner"] == "one-person-lab"
    assert boundary["declarative_pack_compiler_input"]["mas_long_term_code_owner"] == (
        "minimal_authority_functions_only"
    )
    assert boundary["generated_surface_handoff"]["generated_surface_owner"] == "one-person-lab"
    assert boundary["generated_surface_handoff"]["long_term_mas_owner"] is False
    assert boundary["generated_surface_handoff"]["mas_handwritten_shell_expansion_allowed"] is False
    handoff_ids = {
        item["surface_id"]
        for item in boundary["generated_surface_handoff"]["handoff_surfaces"]
    }
    assert "skill" in handoff_ids
    assert boundary["minimal_authority_function_manifest"]["function_ids"] == [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "artifact_mutation_authorization",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
        "owner_receipt_signer",
        "medical_helper_implementation",
    ]
    authority = boundary["minimal_authority_function_manifest"]
    assert authority["semantic_model"] == (
        "ai_first_stage_quality_gate_boundaries_not_script_function_verdicts"
    )
    independent_policy = authority["independent_executor_reviewer_agent_policy"]
    assert independent_policy["required"] is True
    assert independent_policy["separate_invocation_required"] is True
    assert independent_policy["separate_context_record_required"] is True
    assert independent_policy["separate_task_record_required"] is True
    assert independent_policy["separate_receipt_required"] is True
    assert independent_policy["self_review_closes_quality_gate"] is False
    assert authority["boundary_ids"] == [
        "publication_quality_stage_gate_boundary",
        "ai_reviewer_quality_stage_gate_boundary",
        "artifact_mutation_stage_gate_boundary",
        "publication_route_memory_accept_reject_stage_gate_boundary",
        "source_readiness_stage_gate_boundary",
    ]
    assert {
        item["program_role"] for item in authority["stage_quality_gate_boundaries"]
    } == {"validator", "materializer", "guard"}
    assert all(
        item["requires_ai_first_record"] is True
        and item["route_back_semantics"].startswith("route_back_to_")
        and item["typed_blocker_semantics"].endswith("_blocker")
        for item in authority["stage_quality_gate_boundaries"]
    )
    assert "product_entry_manifest.functional_consumer_boundary" in boundary["proof_surfaces"]
    assert "mas_owned_generic_queue" in boundary["forbidden_regressions"]
