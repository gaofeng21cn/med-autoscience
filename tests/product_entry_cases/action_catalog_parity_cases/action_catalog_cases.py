from __future__ import annotations

from tests.standard_agent_purity_helpers import assert_standard_agent_purity_boundary

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

    shell_commands = skill_catalog["skills"][0]["domain_projection"]["shell_commands"]
    assert shell_commands | {
        action_id: cli_item["command"] for action_id, cli_item in cli_projection.items()
    } == shell_commands
    assert shell_commands["product_entry_status"] == manifest["product_entry_shell"]["product_entry_status"]["command"]
    assert shell_commands["workspace_cockpit"] == manifest["product_entry_shell"]["workspace_cockpit"]["command"]
    assert manifest["product_entry_shell"]["product_entry_status"]["authority_boundary"]["host_owner"] == "one-person-lab"
    assert manifest["product_entry_shell"]["workspace_cockpit"]["authority_boundary"]["host_owner"] == "one-person-lab"
    assert manifest["product_entry_shell"]["product_entry_status"]["authority_boundary"]["mas_repo_local_default_caller"] is False
    assert manifest["product_entry_shell"]["workspace_cockpit"]["authority_boundary"]["mas_repo_local_default_caller"] is False
    assert skill_catalog["skills"][0]["domain_projection"]["action_catalog_projection"] == list(skill_projection.values())

    assert "product_entry" not in mcp_projection
    assert "product_entry" not in mcp_tools

    assert mcp_tools["study_progress"]["metadata"]["action_catalog_projection"] == mcp_projection["study_progress"]
    assert "study_runtime" not in mcp_tools
    assert "study_runtime" not in mcp_projection


def test_mas_action_catalog_exposes_study_state_matrix_for_opl_transition_runner(tmp_path: Path) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}
    product_entry_projection = {
        item["action_key"]: item for item in action_catalog.project_mas_action_catalog("product_entry", catalog)
    }
    skill_projection = {
        item["action_id"]: item for item in action_catalog.project_mas_action_catalog("skill", catalog)
    }
    mcp_projection = {
        item["name"]: item for item in action_catalog.project_mas_action_catalog(
            "mcp",
            action_catalog.build_mas_action_catalog(),
        )
    }
    mcp_tool_names = {tool["name"] for tool in mcp_server.build_tool_manifest()}

    matrix = cli_projection["study_state_matrix"]
    assert matrix["effect"] == "read_only"
    assert matrix["surface_kind"] == "study_state_matrix"
    assert matrix["command"] == (
        "uv run python -m med_autoscience.cli study-state-matrix --profile "
        + str(profile_ref.resolve())
        + " --format json"
    )

    action = {item["action_id"]: item for item in catalog["actions"]}["study_state_matrix"]
    assert action["authority_boundary"]["surface_authority"] == (
        "domain_transition_read_model_materialization"
    )
    assert action["authority_boundary"]["runner_owner"] == "OPL Framework"
    assert action["authority_boundary"]["domain_transition_owner"] == "MedAutoScience"
    assert action["authority_boundary"]["can_write_domain_truth"] is False
    assert action["authority_boundary"]["can_execute_domain_action"] is False
    assert action["authority_boundary"]["can_authorize_publication_quality"] is False
    assert action["authority_boundary"]["can_authorize_submission_readiness"] is False

    assert manifest["product_entry_shell"]["study_state_matrix"]["command"] == matrix["command"]
    assert product_entry_projection["study_state_matrix"]["command"] == matrix["command"]
    assert skill_projection["study_state_matrix"]["command"] == matrix["command"]
    assert mcp_projection["study_state_matrix"]["descriptor_only"] is True
    assert mcp_projection["study_state_matrix"]["public_runtime"] is False
    assert "study_state_matrix" not in mcp_tool_names


def test_mas_action_catalog_projects_domain_handler_without_new_mcp_tool(tmp_path: Path) -> None:
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

    domain_handler_export = cli_projection["domain_handler_export"]
    assert domain_handler_export["effect"] == "read_only"
    assert domain_handler_export["command"] == (
        "medautosci domain-handler export --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert domain_handler_export["surface_kind"] == "mas_family_domain_handler_export"

    domain_handler_dispatch = cli_projection["domain_handler_dispatch"]
    assert domain_handler_dispatch["effect"] == "mutating"
    assert domain_handler_dispatch["command"] == "medautosci domain-handler dispatch --task <task.json> --format json"
    assert domain_handler_dispatch["surface_kind"] == "mas_family_domain_handler_dispatch_receipt"
    assert "owner-route dispatch receipt" in domain_handler_dispatch["summary"]
    assert "typed queue task" in domain_handler_dispatch["summary"]
    assert "explicit OPL opt-in executor/proof refs only" in domain_handler_dispatch["summary"]
    assert "does not authorize domain truth" in domain_handler_dispatch["summary"]
    assert "publication quality" in domain_handler_dispatch["summary"]
    assert "artifact gate" in domain_handler_dispatch["summary"]
    assert "current package" in domain_handler_dispatch["summary"]

    assert product_entry_projection["domain_handler_export"]["command"] == domain_handler_export["command"]
    assert product_entry_projection["domain_handler_dispatch"]["command"] == domain_handler_dispatch["command"]
    assert skill_projection["domain_handler_export"]["effect"] == "read_only"
    assert skill_projection["domain_handler_dispatch"]["effect"] == "mutating"

    assert mcp_projection["domain_handler_export"]["descriptor_only"] is True
    assert mcp_projection["domain_handler_export"]["public_runtime"] is False
    assert mcp_projection["domain_handler_dispatch"]["descriptor_only"] is True
    assert mcp_projection["domain_handler_dispatch"]["public_runtime"] is False
    assert {"domain_handler_export", "domain_handler_dispatch"}.isdisjoint(mcp_tool_names)


def test_mas_action_catalog_exposes_display_pack_agent_capability_as_grouped_mcp_runtime(
    tmp_path: Path,
) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile_ref = tmp_path / "profile.local.toml"
    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()
    actions = {item["action_id"]: item for item in catalog["actions"]}
    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}
    product_entry_projection = {
        item["action_key"]: item for item in action_catalog.project_mas_action_catalog("product_entry", catalog)
    }
    skill_projection = {
        item["action_id"]: item for item in action_catalog.project_mas_action_catalog("skill", catalog)
    }
    mcp_projection_items = [
        item
        for item in action_catalog.project_mas_action_catalog("mcp", neutral_catalog)
        if item["name"] == "display_pack_agent"
    ]
    mcp_metadata_by_tool = action_catalog.action_catalog_metadata_by_mcp_tool(neutral_catalog)
    mcp_tool_names = {tool["name"] for tool in mcp_server.build_tool_manifest()}

    expected_actions = {
        "display_pack_capability_discover": ("display_pack_agent_capability", "discover"),
        "display_pack_figure_plan": ("display_pack_agent_figure_plan", "plan"),
        "display_pack_preflight": ("display_pack_agent_preflight", "preflight"),
        "display_pack_render": ("display_pack_agent_render_receipt", "render"),
    }
    assert expected_actions.keys() <= actions.keys()
    assert "display_pack_agent" in mcp_tool_names
    assert len(mcp_projection_items) == len(expected_actions)
    assert {item["name"] for item in mcp_projection_items} == {"display_pack_agent"}
    assert {item["surface_kind"] for item in mcp_projection_items} == {
        surface_kind for surface_kind, _mode in expected_actions.values()
    }
    assert mcp_metadata_by_tool["display_pack_agent"]["surface_kind"] == "mas_mcp_tool_group_projection"
    assert {item["name"] for item in mcp_metadata_by_tool["display_pack_agent"]["actions"]} == {
        "display_pack_agent"
    }
    assert {item["surface_kind"] for item in mcp_metadata_by_tool["display_pack_agent"]["actions"]} == {
        surface_kind for surface_kind, _mode in expected_actions.values()
    }
    assert {
        item["surface_kind"]: item["input_schema"]
        for item in mcp_metadata_by_tool["display_pack_agent"]["actions"]
    }["display_pack_agent_figure_plan"]["required"] == ["figure_request"]
    for action_id, (surface_kind, mode) in expected_actions.items():
        action = actions[action_id]
        cli_item = cli_projection[action_id]
        mcp_descriptor = action["supported_surfaces"]["mcp"]
        assert cli_item["surface_kind"] == surface_kind
        assert product_entry_projection[action_id]["surface_kind"] == surface_kind
        assert skill_projection[action_id]["surface_kind"] == surface_kind
        assert mcp_descriptor["tool_name"] == "display_pack_agent"
        assert mcp_descriptor["mode"] == mode
        assert mcp_descriptor["descriptor_only"] is False
        assert mcp_descriptor["public_runtime"] is True
        assert action["authority_boundary"]["can_mutate_data_or_statistics"] is False
        assert action["authority_boundary"]["can_authorize_publication_readiness"] is False
        assert action["authority_boundary"]["can_replace_owner_receipt"] is False

    assert actions["display_pack_render"]["effect"] == "mutating"
    assert actions["display_pack_render"]["authority_boundary"]["helper_write_policy"] == (
        "display_artifacts_and_refs_only"
    )


def test_mas_action_catalog_exposes_scientific_capability_registry_as_public_mcp_runtime(
    tmp_path: Path,
) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile_ref = tmp_path / "profile.local.toml"
    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()
    actions = {item["action_id"]: item for item in catalog["actions"]}
    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}
    mcp_projection = action_catalog.action_catalog_metadata_by_mcp_tool(neutral_catalog)
    mcp_tools = {tool["name"]: tool for tool in mcp_server.build_tool_manifest()}

    action = actions["scientific_capability_registry"]
    boundary = action["authority_boundary"]
    cli_item = cli_projection["scientific_capability_registry"]
    mcp_item = mcp_projection["scientific_capability_registry"]

    assert cli_item["surface_kind"] == "mas_scientific_capability_registry"
    assert "scientific-capability-registry --mode <index|resolve|invoke>" in cli_item["command"]
    assert mcp_item["descriptor_only"] is False
    assert mcp_item["public_runtime"] is True
    assert mcp_item["input_schema"]["required"] == ["mode"]
    assert mcp_item["input_schema"]["properties"]["mode"]["enum"] == ["index", "resolve", "invoke"]
    assert "scientific_capability_registry" in mcp_tools
    assert mcp_tools["scientific_capability_registry"]["metadata"] == mcp_item

    assert boundary["surface_authority"] == "current_delta_bound_capability_resolver"
    assert boundary["helper_write_policy"] == "refs_only_capability_invocation"
    assert boundary["can_write_publication_eval"] is False
    assert boundary["can_write_controller_decisions"] is False
    assert boundary["can_write_current_package"] is False
    assert boundary["can_write_owner_receipt"] is False
    assert boundary["can_write_typed_blocker"] is False
    assert boundary["can_authorize_publication_quality"] is False
    assert boundary["can_authorize_submission_readiness"] is False
    assert boundary["can_block_current_owner_action"] is False
    assert boundary["can_launch_external_runtime"] is False
    assert boundary["can_create_default_selector"] is False


def test_mas_action_catalog_exposes_publication_aftercare_plan_as_refs_only_surface(tmp_path: Path) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    actions = {item["action_id"]: item for item in catalog["actions"]}
    cli_projection = {item["action_id"]: item for item in action_catalog.project_mas_action_catalog("cli", catalog)}

    aftercare = actions["publication_aftercare_plan"]
    aftercare_cli = cli_projection["publication_aftercare_plan"]
    assert aftercare["effect"] == "read_only"
    assert aftercare_cli["surface_kind"] == "mas_publication_aftercare_plan"
    assert aftercare["authority_boundary"]["can_write_publication_eval"] is False
    assert aftercare["authority_boundary"]["can_write_controller_decisions"] is False
    assert aftercare["authority_boundary"]["can_write_current_package"] is False
    assert aftercare["authority_boundary"]["can_dispatch_runtime_owner_task"] is False
    assert aftercare["authority_boundary"]["can_emit_owner_route_task_refs"] is True
    assert aftercare["authority_boundary"]["runtime_owner_task_dispatch_policy"] == (
        "forbidden_mas_emits_refs_or_typed_blockers_only"
    )
    assert "publication_eval" in aftercare["summary"]
    assert "current_package" in aftercare["summary"]
    assert manifest["family_action_catalog"]["actions"] == catalog["actions"]
    assert manifest["product_entry_shell"]["publication_aftercare_plan"]["command"] == aftercare_cli["command"]


def test_mas_action_catalog_exposes_lightweight_executor_receipt_as_descriptor_only_contract(
    tmp_path: Path,
) -> None:
    action_catalog = importlib.import_module("med_autoscience.action_catalog")
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")
    mcp_server = importlib.import_module("med_autoscience.mcp_server")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()
    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    skill_catalog = product_entry.build_skill_catalog(profile=profile, profile_ref=profile_ref)
    actions = {item["action_id"]: item for item in catalog["actions"]}
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

    receipt_action = actions["lightweight_executor_receipt"]
    receipt_cli = cli_projection["lightweight_executor_receipt"]
    boundary = receipt_action["authority_boundary"]

    assert receipt_action["effect"] == "read_only"
    assert receipt_cli["surface_kind"] == "mas_lightweight_executor_receipt_contract"
    assert receipt_cli["command"] == (
        "medautosci domain-handler export --profile " + str(profile_ref.resolve()) + " --format json"
    )
    assert boundary["surface_authority"] == "executor_receipt_contract_read_model"
    assert boundary["can_execute_command"] is False
    assert boundary["can_start_docker"] is False
    assert boundary["can_mount_docker_socket"] is False
    assert boundary["can_write_owner_receipt"] is False
    assert boundary["can_write_typed_blocker"] is False
    assert boundary["can_authorize_publication_quality"] is False
    assert boundary["can_authorize_submission_readiness"] is False
    assert boundary["can_block_current_owner_action"] is False

    assert product_entry_projection["lightweight_executor_receipt"]["command"] == receipt_cli["command"]
    assert skill_projection["lightweight_executor_receipt"]["command"] == receipt_cli["command"]
    assert manifest["family_action_catalog"]["actions"] == catalog["actions"]
    assert manifest["product_entry_shell"]["lightweight_executor_receipt"]["command"] == receipt_cli["command"]
    assert skill_catalog["skills"][0]["domain_projection"]["shell_commands"][
        "lightweight_executor_receipt"
    ] == receipt_cli["command"]

    assert mcp_projection["lightweight_executor_receipt"]["descriptor_only"] is True
    assert mcp_projection["lightweight_executor_receipt"]["public_runtime"] is False
    assert "lightweight_executor_receipt" not in mcp_tool_names


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
    assert boundary["status"] == "opl_consumes_generic_surfaces_mas_supplies_domain_authority_pack"
    assert boundary["consumer_role"] == "domain_authority_pack_thin_program_surface"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert_standard_agent_purity_boundary(boundary)
    assert boundary["domain_authority_refs_index_role"]["mas_may_claim_generic_persistence_engine"] is False
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
    assert set(boundary["mas_domain_authority_surfaces"]) == {
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
