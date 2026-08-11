from __future__ import annotations

import ast
import importlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_native_carrier_descriptor_projects_owner_identity_without_lifecycle_authority() -> None:
    owner_manifest_path = ROOT / "contracts/opl_agent_package_manifest.json"
    root_manifest_path = ROOT / "opl-package.json"
    assert root_manifest_path.read_bytes() == owner_manifest_path.read_bytes()

    owner_descriptor = json.loads(owner_manifest_path.read_text(encoding="utf-8"))
    root_descriptor = json.loads(root_manifest_path.read_text(encoding="utf-8"))
    carrier_descriptor = json.loads(
        (ROOT / "plugins/med-autoscience/opl-package.json").read_text(
            encoding="utf-8"
        )
    )
    nested_plugin = json.loads(
        (ROOT / "plugins/med-autoscience/.codex-plugin/plugin.json").read_text(
            encoding="utf-8"
        )
    )
    portable_plugin = json.loads(
        (ROOT / "plugins/med-autoscience/plugin.json").read_text(encoding="utf-8")
    )
    root_plugin = json.loads(
        (ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
    )

    assert root_descriptor == owner_descriptor

    projected_owner_fields = {
        "surface_kind",
        "kind",
        "agent_id",
        "package_id",
        "display_name",
        "publisher",
        "version",
        "source",
        "carrier_source_role",
        "domain_descriptor_ref",
        "task_provider_ref",
        "action_catalog_ref",
        "view_refs",
        "requires",
        "presentation",
    }
    assert set(carrier_descriptor) == projected_owner_fields | {
        "capability_dependencies",
        "codex_surface",
    }
    for field in projected_owner_fields:
        assert carrier_descriptor[field] == owner_descriptor[field]

    projected_codex_fields = {
        "configured_codex_plugin_carrier",
        "plugin_id",
        "required_capability_package_ids",
        "required_skill_ids",
        "standalone_distribution",
        "user_install_action_count",
    }
    assert set(carrier_descriptor["codex_surface"]) == projected_codex_fields
    for field in projected_codex_fields:
        assert (
            carrier_descriptor["codex_surface"][field]
            == owner_descriptor["codex_surface"][field]
        )

    assert (
        carrier_descriptor["capability_dependencies"]
        == owner_descriptor["capability_dependencies"]
    )
    assert carrier_descriptor["requires"] == [
        {"package_id": "mas-scholar-skills", "presence": "required"}
    ]
    assert carrier_descriptor["agent_id"] == carrier_descriptor["package_id"] == "mas"
    assert carrier_descriptor["carrier_source_role"] == (
        "codex_plugin_default_carrier_not_package_truth"
    )
    assert (
        carrier_descriptor["codex_surface"]["plugin_id"]
        == root_plugin["name"]
        == nested_plugin["name"]
        == portable_plugin["name"]
    )
    assert (
        carrier_descriptor["version"]
        == root_plugin["version"]
        == nested_plugin["version"]
        == portable_plugin["version"]
    )
    assert carrier_descriptor["codex_surface"]["configured_codex_plugin_carrier"] == (
        root_descriptor["codex_surface"]["configured_codex_plugin_carrier"]
    )

    def nested_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | {
                key for nested in value.values() for key in nested_keys(nested)
            }
        if isinstance(value, list):
            return {key for nested in value for key in nested_keys(nested)}
        return set()

    legacy_authority_keys = {
        "activation_materialization",
        "consumer_profile_id",
        "dependency_kind",
        "install_owner",
        "install_update_source",
        "last_known_good",
        "lifecycle",
        "lock",
        "opl_managed_surface",
        "package_core",
        "receipt",
        "release_set_receipt_ref",
        "repair_command_templates",
        "resolver",
        "rollback_ref",
        "status_command_templates",
        "sync_command_refs",
        "version_requirement",
    }
    assert nested_keys(carrier_descriptor).isdisjoint(legacy_authority_keys)

    forbidden_owner_lifecycle_keys = {
        "activation_materialization",
        "carrier_source_commit",
        "codex_distribution",
        "consumer_profile_id",
        "dependency_kind",
        "developer_distribution",
        "install_owner",
        "install_update_source",
        "missing_or_incompatible_policy",
        "opl_distribution",
        "provider_manifest_ref",
        "release_set_receipt_ref",
        "repair_command_templates",
        "required_for",
        "status_command_templates",
        "sync_command_refs",
        "sync_scopes",
        "version_requirement",
    }
    assert nested_keys(owner_descriptor).isdisjoint(forbidden_owner_lifecycle_keys)


def test_package_manifest_owns_home_presentation_bytes() -> None:
    package = json.loads(
        (ROOT / "contracts/opl_agent_package_manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert package["presentation"] == {
        "display_name_i18n": {
            "zh-CN": "Med Auto Science",
            "en-US": "Med Auto Science",
        },
        "description_i18n": {
            "zh-CN": (
                "医学研究选题、文献分析、数据分析、论文写作、审稿、返修与投稿。"
            ),
            "en-US": (
                "Medical research planning, literature review, data analysis, manuscript "
                "writing, peer review, revision, and submission."
            ),
        },
        "session_routing_summary_i18n": {
            "zh-CN": "科研、论文、数据分析、审稿、返修和投稿",
            "en-US": (
                "research, papers, data analysis, peer review, revision, and "
                "submission"
            ),
        },
        "home_shortcuts": [
            {
                "shortcut_id": "research",
                "label_i18n": {
                    "zh-CN": "科研",
                    "en-US": "Research",
                },
                "default_visible": True,
                "user_configurable": True,
                "route": {
                    "route_kind": "agent_package_shortcut",
                    "executor": "codex_cli",
                    "codex_visible_entry": package["codex_surface"]["plugin_id"],
                },
            }
        ],
    }


def test_package_plugin_and_python_versions_are_one_semver() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package = json.loads(
        (ROOT / "contracts/opl_agent_package_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    root_plugin = json.loads(
        (ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
    )
    nested_plugin = json.loads(
        (
            ROOT
            / "plugins/med-autoscience/.codex-plugin/plugin.json"
        ).read_text(encoding="utf-8")
    )
    portable_plugin = json.loads(
        (ROOT / "plugins/med-autoscience/plugin.json").read_text(encoding="utf-8")
    )

    assert (
        package["version"]
        == pyproject["project"]["version"]
        == root_plugin["version"]
        == nested_plugin["version"]
        == portable_plugin["version"]
    )
    assert package["version"] == "0.2.27"
    assert "distribution_payload" not in package
    assert package["agent_id"] == package["package_id"] == "mas"
    assert package["codex_surface"]["plugin_id"] == "med-autoscience"
    assert package["codex_surface"]["configured_codex_plugin_carrier"] == {
        "kind": "codex_plugin_manager",
        "plugin_selector": "med-autoscience@med-autoscience",
        "executor_route": "codex_cli",
        "marketplace_source": "gaofeng21cn/med-autoscience",
        "publication_ref": (
            "ghcr.io/gaofeng21cn/one-person-lab-packages/mas:latest-stable"
        ),
    }
    assert pyproject["project"]["scripts"] == {
        "mas-foundry-owner-gate": (
            "med_autoscience.authority_handlers.foundry_owner_gate:main"
        )
    }
    assert root_plugin["name"] == nested_plugin["name"] == "med-autoscience"
    assert root_plugin["repository"] == nested_plugin["repository"] == (
        "https://github.com/gaofeng21cn/med-autoscience"
    )
    assert root_plugin["skills"] == "./plugins/med-autoscience/skills/"
    assert nested_plugin["skills"] == "./skills/"
    assert portable_plugin["$schema"] == (
        "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    )
    assert set(portable_plugin) <= {
        "$schema",
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "extensions",
    }
    assert portable_plugin["extensions"]["com.openai"]["interface"] == (
        nested_plugin["interface"]
    )
    assert not (ROOT / "plugins/med-autoscience/mcp.json").exists()
    for plugin_root, plugin in (
        (ROOT, root_plugin),
        (ROOT / "plugins/med-autoscience", nested_plugin),
    ):
        assert "mcpServers" not in plugin
        assert plugin["interface"]["displayName"] == "Med Auto Science"
        assert plugin["interface"]["composerIcon"] == plugin["interface"]["logo"]
        assert (plugin_root / plugin["interface"]["composerIcon"]).is_file()
        prompt_text = json.dumps(plugin["interface"]["defaultPrompt"]).lower()
        assert "doctor" not in prompt_text
        assert "controller" not in prompt_text

    nested_plugin_root = ROOT / "plugins/med-autoscience"
    assert (nested_plugin_root / "skills/med-autoscience/agents/openai.yaml").is_file()
    assert not (nested_plugin_root / "bin/medautosci-mcp").exists()
    assert not (ROOT / "plugins/mas").exists()
    assert not any((ROOT / "src/med_autoscience/cli").glob("*.py"))
    assert not (ROOT / "scripts/install-codex-plugin.sh").exists()


def test_repo_marketplace_exposes_only_the_codex_plugin_carrier() -> None:
    package = json.loads(
        (ROOT / "contracts/opl_agent_package_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    plugin = json.loads(
        (ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
    )

    assert marketplace["name"] == "med-autoscience"
    assert marketplace["interface"] == {"displayName": "Med Auto Science"}
    assert marketplace["plugins"] == [
        {
            "name": "med-autoscience",
            "source": {
                "source": "local",
                "path": "./plugins/med-autoscience",
            },
            "policy": {
                "installation": "AVAILABLE",
                "authentication": "ON_INSTALL",
            },
            "category": "Research",
        }
    ]

    entry = marketplace["plugins"][0]
    plugin_root = ROOT / entry["source"]["path"]
    assert (plugin_root / "plugin.json").is_file()
    assert (plugin_root / ".codex-plugin/plugin.json").is_file()
    assert entry["name"] == plugin["name"] == package["codex_surface"]["plugin_id"]
    assert entry["category"] == plugin["interface"]["category"]
    assert package["package_id"] == "mas"
    assert "products" not in entry["policy"]


def test_nested_native_carrier_keeps_hosted_runtime_owned_by_the_repo() -> None:
    package_path = ROOT / "opl-package.json"
    owner_manifest_path = ROOT / "contracts/opl_agent_package_manifest.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    plugin = json.loads(
        (ROOT / "plugins/med-autoscience/.codex-plugin/plugin.json").read_text(
            encoding="utf-8"
        )
    )
    marketplace = json.loads(
        (ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
    )

    assert package_path.read_bytes() == owner_manifest_path.read_bytes()
    assert marketplace["plugins"][0]["source"] == {
        "source": "local",
        "path": "./plugins/med-autoscience",
    }
    assert plugin["skills"] == "./skills/"

    for relative_path in (
        package["domain_descriptor_ref"],
        package["action_catalog_ref"],
        "contracts/domain_handler_registry.json",
        "agent/stages/manifest.json",
        "src/med_autoscience/__init__.py",
    ):
        assert (ROOT / relative_path.split("#", 1)[0]).is_file(), relative_path

    action_catalog = json.loads(
        (ROOT / package["action_catalog_ref"]).read_text(encoding="utf-8")
    )
    stage_manifest = json.loads(
        (ROOT / "agent/stages/manifest.json").read_text(encoding="utf-8")
    )
    stage_actions = {
        action["action_id"]
        for action in action_catalog["actions"]
        if action["execution_binding"]["kind"] == "stage_binding"
    }
    assert stage_actions == {stage["stage_id"] for stage in stage_manifest["stages"]}
    for stage in stage_manifest["stages"]:
        for ref in (
            stage["policy_ref"],
            stage["prompt_ref"],
            *stage["knowledge_refs"],
            *stage["quality_gate_refs"],
        ):
            assert (ROOT / ref).is_file(), ref

    registry = json.loads(
        (ROOT / "contracts/domain_handler_registry.json").read_text(encoding="utf-8")
    )
    handlers = {
        entry["handler_id"]: entry["binding"] for entry in registry["handlers"]
    }
    handler_refs = {
        action["execution_binding"]["handler_ref"].removeprefix("handler:")
        for action in action_catalog["actions"]
        if action["execution_binding"]["kind"] == "handler_ref"
    }
    assert handler_refs <= handlers.keys()
    for handler_id in handlers:
        binding = handlers[handler_id]
        module_path = ROOT / "src" / Path(*binding["module"].split("."))
        source_path = module_path.with_suffix(".py")
        if not source_path.is_file():
            source_path = module_path / "__init__.py"
        assert source_path.is_file(), binding["module"]
        module = ast.parse(source_path.read_text(encoding="utf-8"))
        assert any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == binding["callable"]
            for node in ast.walk(module)
        ), (binding["module"], binding["callable"])


def test_package_import_and_hosted_entry_sources_resolve() -> None:
    package = importlib.import_module("med_autoscience")
    paper_handler = importlib.import_module(
        "med_autoscience.authority_handlers.paper_mission"
    )
    candidate_handler = importlib.import_module(
        "med_autoscience.authority_handlers.candidate_admission"
    )
    build_currentness_handler = importlib.import_module(
        "med_autoscience.authority_handlers.build_dependency_currentness"
    )
    lifecycle_handler = importlib.import_module(
        "med_autoscience.authority_handlers.study_lifecycle_reactivation"
    )
    provisioning_handler = importlib.import_module(
        "med_autoscience.authority_handlers.qualification_work_item_provisioning"
    )
    try:
        installed_version = version("med-autoscience")
    except PackageNotFoundError:
        installed_version = "0+unknown"

    assert package.__version__ == installed_version
    assert callable(paper_handler.evaluate_paper_mission_authority)
    assert callable(candidate_handler.evaluate_candidate_admission_authority)
    assert callable(
        build_currentness_handler.evaluate_build_dependency_currentness_authority
    )
    assert callable(
        lifecycle_handler.evaluate_study_lifecycle_reactivation_authority
    )
    assert callable(
        provisioning_handler.evaluate_qualification_work_item_provisioning_authority
    )
    assert (ROOT / "agent/primary_skill/SKILL.md").is_file()

    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )
    assert len(catalog["actions"]) == 11
    for action in catalog["actions"]:
        binding = action["execution_binding"]
        if binding["kind"] == "stage_binding":
            assert (ROOT / binding["stage_manifest_ref"]).is_file()


def test_historical_validator_release_set_stays_out_of_package_currentness() -> None:
    package = json.loads(
        (ROOT / "contracts/opl_agent_package_manifest.json").read_text(encoding="utf-8")
    )
    release = json.loads(
        (ROOT / "contracts/mas_validator_release_set_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )

    assert package["version"] == "0.2.27"
    assert "release_set_receipt_ref" not in package
    assert release["release_set_id"] == "mas-validator-0.2.24"
    assert release["package_version"] == "0.2.24"
    assert release["source_ref"] == "refs/tags/v0.2.24"
    assert "source_commit" not in release
    assert release["supported_scope"]["kind"] == "exact_byte_domain_validator"
    assert (
        release["supported_scope"][
            "qualification_work_item_provisioning_validation"
        ]
        is True
    )
    assert "tests/test_qualification_work_item_provisioning_authority.py" in (
        release["verification"]["focused_test_refs"]
    )
    assert {
        "contracts/schemas/v2/mas-qualification-work-item-provisioning-authority.input.schema.json",
        "contracts/schemas/v2/mas-qualification-work-item-provisioning-authority.output.schema.json",
    }.issubset(release["verification"]["schema_refs"])
    assert release["trust_boundary"] == {
        "independent_trust_root": False,
        "malicious_host_complete_self_consistent_forgery_resistance": False,
        "self_consistent_hashes_authenticate_bytes_not_issuer": True,
        "requires_managed_authority_attempt_provenance": True,
        "requires_owner_ledger_provenance": True,
        "provenance_gate_owner": "one-person-lab",
        "missing_provenance_effect": "fail_closed",
    }
    assert release["clearance"] == {
        "package_validator_ready_after_release_readback": True,
        "authoring_clearance": False,
        "launch_clearance": False,
        "publication_clearance": False,
        "submission_clearance": False,
    }
    assert release["verification"]["exact_commit_and_artifact_binding"] == (
        "annotated_tag_and_final_remote_readback"
    )

    internal_actions = {
        action["action_id"]: action
        for action in catalog["actions"]
        if action["action_id"]
        in {
            "candidate_admission_authority_evaluate",
            "build_dependency_currentness_authority_evaluate",
            "paper_mission_authority_evaluate",
        }
    }
    assert len(internal_actions) == 3
    for action in internal_actions.values():
        boundary = action["authority_boundary"]
        assert boundary["independent_trust_root"] is False
        assert (
            boundary["malicious_host_complete_self_consistent_forgery_resistance"]
            is False
        )
        assert boundary["requires_managed_authority_attempt_provenance"] is True
        assert boundary["requires_owner_ledger_provenance"] is True
        assert boundary["missing_provenance_effect"] == "fail_closed"
        assert boundary["authoring_or_launch_clearance"] is False


def test_stage_route_contract_has_one_canonical_package_source() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest_lines = {
        line.strip()
        for line in (ROOT / "MANIFEST.in").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    pack_input = json.loads(
        (ROOT / "contracts/pack_compiler_input.json").read_text(encoding="utf-8")
    )

    canonical = ROOT / "agent/stages/stage_route_contract.yaml"
    packaged_mirror = ROOT / "src/med_autoscience/resources/stage_route_contract.yaml"
    resources_root = ROOT / "src/med_autoscience/resources"
    assert canonical.is_file()
    assert not packaged_mirror.exists()
    assert not any(path.is_file() for path in resources_root.rglob("*"))
    assert pyproject["tool"]["setuptools"]["package-data"] == {
        "med_autoscience.styles": ["*.csl"]
    }
    assert "include agent/stages/stage_route_contract.yaml" in manifest_lines
    assert all("src/med_autoscience/resources" not in line for line in manifest_lines)
    assert pack_input["source_refs"]["required_domain_pack_paths"].count(
        "agent/stages/stage_route_contract.yaml"
    ) == 1


def test_scholarskills_is_required_presence_and_callability_not_a_sixth_agent() -> None:
    package = json.loads(
        (ROOT / "contracts/opl_agent_package_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    dependencies = package["capability_dependencies"]

    assert [item["package_id"] for item in dependencies] == [
        "mas-scholar-skills"
    ]
    dependency = dependencies[0]
    assert dependency["package_id"] == "mas-scholar-skills"
    assert dependency["required"] is True
    assert dependency["capability_abi"] == "mas-scholar-skills.v1"
    assert set(dependency) == {
        "module_id",
        "package_id",
        "required",
        "capability_abi",
        "required_export_ids",
        "required_module_ids",
        "authority_boundary",
    }
    assert package["codex_surface"]["standalone_distribution"] == (
        "repo_carrier_source"
    )

    active_truth_paths = [
        "README.md",
        "README.zh-CN.md",
        "bootstrap/README.md",
        "docs/architecture.md",
        "docs/invariants.md",
        "docs/decisions.md",
        "docs/status.md",
        "docs/active/mas-ideal-state-gap-plan.md",
        "docs/whitepapers/mas-whitepaper.md",
        "docs/references/integration/codex_plugin.md",
        "docs/active/stage_surface_standardization_program.md",
        "agent/primary_skill/SKILL.md",
        "plugins/med-autoscience/skills/med-autoscience/SKILL.md",
    ]
    active_truth = {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in active_truth_paths
    }
    forbidden_optional_claims = [
        "optional professional enhancement",
        "可选专业增强",
        "not enter MAS's hard dependency closure",
        "不进入 MAS 的硬依赖闭包",
        "不是 MAS 硬依赖",
        "optional Provider",
        "optional enhancement gap",
        "continue_with_consumer_core_and_record_diagnostic",
    ]
    for path, text in active_truth.items():
        for optional_claim in forbidden_optional_claims:
            assert optional_claim not in text, f"{path} retains {optional_claim}"
    required_truth_claims = {
        "README.md": "required `mas-scholar-skills` dependency closure",
        "README.zh-CN.md": "必需的 `mas-scholar-skills` 依赖闭包",
        "bootstrap/README.md": "MAS 与 `mas-scholar-skills` required dependency closure",
        "docs/architecture.md": "`mas-scholar-skills` 是 MAS 的 required capability dependency",
        "docs/invariants.md": "`mas-scholar-skills` 是 MAS 硬依赖",
        "docs/decisions.md": "ScholarSkills 硬依赖",
        "docs/status.md": "MAS required capability dependency",
        "docs/active/mas-ideal-state-gap-plan.md": "required dependency",
        "docs/whitepapers/mas-whitepaper.md": "必需能力依赖",
        "docs/references/integration/codex_plugin.md": "MAS root package 及其 required dependency closure",
        "docs/active/stage_surface_standardization_program.md": (
            "required knowledge / ScholarSkills / tool affordances"
        ),
        "agent/primary_skill/SKILL.md": (
            "Use the installed `mas-scholar-skills` capability package"
        ),
        "plugins/med-autoscience/skills/med-autoscience/SKILL.md": (
            "Use the installed `mas-scholar-skills` capability package"
        ),
    }
    for path, required_claim in required_truth_claims.items():
        assert required_claim in active_truth[path], f"{path} lacks {required_claim}"
    assert dependency["required_module_ids"] == [
        "mas-scholar-skills.display",
        "mas-scholar-skills.tables",
        "mas-scholar-skills.stats",
        "mas-scholar-skills.lit",
        "mas-scholar-skills.write",
        "mas-scholar-skills.review",
        "mas-scholar-skills.submit",
        "mas-scholar-skills.data",
        "mas-scholar-skills.reference-provider-adapters",
        "mas-scholar-skills.scientific-search-adapters",
    ]
    assert package["codex_surface"]["user_install_action_count"] == 1
    assert package["codex_surface"]["required_capability_package_ids"] == [
        "mas-scholar-skills"
    ]
    assert dependency["authority_boundary"] == {
        "can_write_domain_truth": False,
        "can_sign_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_write_runtime_queue": False,
    }


def test_submission_resources_are_host_or_package_provisioned_without_fallback() -> None:
    requirements = json.loads(
        (ROOT / "contracts/submission-resource-requirements.json").read_text(
            encoding="utf-8"
        )
    )

    assert requirements["missing_resource_output"] == {
        "status": "request_only",
        "action_id": "opl_pack_provision_submission_resource",
    }
    assert requirements["hosted_receipt_consumer"] == {
        "owner": "OPL Pack",
        "consumer": "opl_hosted_stage_action_preflight",
        "request_action_id": "opl_pack_provision_submission_resource",
        "receipt_surface_kind": "opl_pack_submission_resource_receipt",
        "receipt_version": "opl-pack-submission-resource-receipt.v1",
        "required_fields": [
            "surface_kind",
            "version",
            "request_id",
            "package_id",
            "resource_id",
            "exact_path",
            "content_sha256",
            "materialization_status",
            "package_lifecycle_receipt_ref",
        ],
        "accepted_materialization_status": "materialized",
        "consumption_policy": (
            "validate_exact_path_and_digest_then_pass_refs_to_the_stage_attempt"
        ),
        "missing_or_mismatched_receipt_effect": (
            "return_the_same_request_only_action_without_local_fallback"
        ),
    }
    assert requirements["authority_boundary"] == {
        "mas_can_download_resources": False,
        "network_fallback_allowed": False,
        "requires_existing_exact_path": True,
        "mas_can_materialize_or_repair_resource": False,
        "pack_receipt_is_medical_or_submission_verdict": False,
        "pack_receipt_is_owner_receipt": False,
    }
    bundled = requirements["resources"]["frontiers_harvard_csl"]["package_path"]
    assert (ROOT / bundled).is_file()
