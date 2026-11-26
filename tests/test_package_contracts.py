from __future__ import annotations

import ast
import importlib
import json
import os
import re
import subprocess
import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v2_manifest_projects_owner_identity_without_legacy_carrier_mirrors() -> None:
    root_manifest_path = ROOT / "opl-package.json"
    descriptor = json.loads((ROOT / "contracts/domain_descriptor.json").read_text(encoding="utf-8"))
    manifest = json.loads(root_manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "opl.package.v2"
    assert manifest["identity"]["id"] == descriptor["agent_id"] == descriptor["package_id"] == "mas"
    assert manifest["identity"]["intent"] == descriptor["kind"] == "agent"
    assert manifest["provides"]["agent"] == {"stages_ref": "agent/stages/manifest.json"}
    assert manifest["provides"]["skills"] == [
        {
            "id": "med-autoscience",
            "path": "./skills/med-autoscience",
            "exposure": "default",
        }
    ]
    assert manifest["provides"]["contribution_handler"] == {
        "kind": "cli",
        "argv": ["./bin/mas-app-contribution"],
        "transport": "stdin_json_stdout_json",
    }
    assert manifest["host_hints"]["codex"]["plugin_name"] == "med-autoscience"

    for retired_path in (
        ROOT / "contracts/opl_agent_package_manifest.json",
        ROOT / "contracts/carrier_projection.json",
        ROOT / ".codex-plugin",
        ROOT / ".agents",
        ROOT / "app-contribution-adapter.json",
        ROOT / "plugins",
        ROOT / "scripts/materialize_plugin_carrier.py",
    ):
        assert not retired_path.exists(), f"Retired v1 artifact still exists: {retired_path}"

    def nested_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | {
                key for nested in value.values() for key in nested_keys(nested)
            }
        if isinstance(value, list):
            return {key for nested in value for key in nested_keys(nested)}
        return set()

    forbidden_owner_lifecycle_keys = {
        "activation_materialization",
        "carrier_source_commit",
        "codex_distribution",
        "codex_surface",
        "consumer_profile_id",
        "dependency_kind",
        "developer_distribution",
        "install_owner",
        "install_update_source",
        "last_known_good",
        "lifecycle",
        "lock",
        "missing_or_incompatible_policy",
        "opl_distribution",
        "opl_managed_surface",
        "package_core",
        "provider_manifest_ref",
        "receipt",
        "release_set_receipt_ref",
        "repair_command_templates",
        "required_for",
        "resolver",
        "rollback_ref",
        "status_command_templates",
        "sync_command_refs",
        "sync_scopes",
        "version_requirement",
    }
    assert nested_keys(manifest).isdisjoint(forbidden_owner_lifecycle_keys)


def test_package_manifest_owns_home_presentation_bytes() -> None:
    package = json.loads((ROOT / "opl-package.json").read_text(encoding="utf-8"))
    identity = package["identity"]

    assert identity["icon"] == "assets/branding/medautoscience-logo.png"
    assert (ROOT / identity["icon"]).is_file()
    assert identity["name"] == {
        "zh-CN": "Med Auto Science",
        "en-US": "Med Auto Science",
    }
    assert identity["summary"] == {
        "zh-CN": "医学研究选题、文献分析、数据分析、论文写作、审稿、返修与投稿。",
        "en-US": (
            "Medical research planning, literature review, data analysis, manuscript "
            "writing, peer review, revision, and submission."
        ),
    }
    assert identity["routing_summary"] == {
        "zh-CN": "科研、论文、数据分析、审稿、返修和投稿",
        "en-US": (
            "research, papers, data analysis, peer review, revision, and submission"
        ),
    }
    assert identity["home_shortcuts"] == [
        {
            "id": "research",
            "label": {
                "zh-CN": "开展科研工作",
                "en-US": "Research",
            },
            "default_visible": True,
            "target": {
                "kind": "agent",
                "ref": "mas",
            },
        }
    ]


def test_package_plugin_and_python_versions_are_one_semver() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package = json.loads((ROOT / "opl-package.json").read_text(encoding="utf-8"))
    identity = package["identity"]
    codex_hint = package["host_hints"]["codex"]

    assert identity["version"] == pyproject["project"]["version"]
    assert re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", identity["version"])
    assert "distribution_payload" not in package
    assert identity["id"] == "mas"
    assert codex_hint["plugin_name"] == "med-autoscience"
    assert codex_hint["sync_enabled"] is True
    assert package["distribution"] == {
        "oci": "ghcr.io/gaofeng21cn/one-person-lab-packages/mas",
        "visibility": "public",
    }
    assert pyproject["project"]["scripts"] == {
        "mas-foundry-owner-gate": (
            "med_autoscience.authority_handlers.foundry_owner_gate:main"
        )
    }
    assert identity["repository"] == "https://github.com/gaofeng21cn/med-autoscience"
    assert (ROOT / identity["icon"]).is_file()
    prompt_text = json.dumps(identity["default_prompts"]).lower()
    assert "doctor" not in prompt_text
    assert "controller" not in prompt_text

    assert (ROOT / "skills/med-autoscience/SKILL.md").is_file()
    assert (ROOT / "skills/med-autoscience/agents/openai.yaml").is_file()
    assert not any((ROOT / "src/med_autoscience/cli").glob("*.py"))
    assert not (ROOT / "scripts/install-codex-plugin.sh").exists()
    assert not (ROOT / "plugins").exists()


def test_codex_host_hints_and_zero_static_marketplace_files() -> None:
    package = json.loads((ROOT / "opl-package.json").read_text(encoding="utf-8"))
    codex_hint = package["host_hints"]["codex"]

    assert codex_hint == {
        "sync_enabled": True,
        "plugin_name": "med-autoscience",
        "category": "Research",
        "brand_color": "#1F7A8C",
        "capabilities": ["Interactive", "Write"],
    }
    assert package["permissions"]["workspace"]["access"] == "read_write"
    assert package["dependencies"]["runtimes"] == [
        {"name": "python", "version": ">=3.12"}
    ]
    assert not (ROOT / ".agents/plugins/marketplace.json").exists()
    assert not (ROOT / ".codex-plugin/plugin.json").exists()


def test_v2_package_keeps_hosted_runtime_owned_by_the_repo() -> None:
    package = json.loads((ROOT / "opl-package.json").read_text(encoding="utf-8"))
    descriptor = json.loads(
        (ROOT / "contracts/domain_descriptor.json").read_text(encoding="utf-8")
    )

    assert package["schema_version"] == "opl.package.v2"
    assert package["provides"]["agent"]["stages_ref"] == "agent/stages/manifest.json"

    for relative_path in (
        "contracts/domain_descriptor.json",
        descriptor["action_catalog_ref"],
        "contracts/domain_handler_registry.json",
        package["provides"]["agent"]["stages_ref"],
        "skills/med-autoscience/SKILL.md",
        "bin/mas-app-contribution",
        "src/med_autoscience/__init__.py",
    ):
        assert (ROOT / relative_path).is_file(), relative_path

    action_catalog = json.loads(
        (ROOT / descriptor["action_catalog_ref"]).read_text(encoding="utf-8")
    )
    stage_manifest = json.loads(
        (ROOT / package["provides"]["agent"]["stages_ref"]).read_text(encoding="utf-8")
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
    for binding in handlers.values():
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
    assert len(catalog["actions"]) == 12
    for action in catalog["actions"]:
        binding = action["execution_binding"]
        if binding["kind"] == "stage_binding":
            assert (ROOT / binding["stage_manifest_ref"]).is_file()


def test_historical_validator_release_set_stays_out_of_package_currentness() -> None:
    package = json.loads((ROOT / "opl-package.json").read_text(encoding="utf-8"))
    release = json.loads(
        (ROOT / "contracts/mas_validator_release_set_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )

    assert package["identity"]["version"] != release["package_version"]
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
    package = json.loads((ROOT / "opl-package.json").read_text(encoding="utf-8"))
    dependencies = package["dependencies"]["packages"]

    assert [item["id"] for item in dependencies] == ["mas-scholar-skills"]
    dependency = dependencies[0]
    assert dependency["id"] == "mas-scholar-skills"
    assert dependency["optional"] is False
    assert set(dependency) == {"id", "optional", "required_capabilities"}
    assert dependency["required_capabilities"] == [
        "mas-scholar-skills",
        "medical-manuscript-writing",
        "medical-manuscript-review",
        "medical-figure-design",
        "medical-figure-style",
        "medical-figure-composer",
        "medical-research-lit",
        "medical-statistical-review",
        "medical-table-design",
        "medical-submission-prep",
        "medical-data-governance",
    ]


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


def test_v2_package_tracks_skills_and_bin_without_plugins_mirror() -> None:
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "ls-files",
            "-z",
            "--",
            "plugins",
            ".codex-plugin",
            ".agents",
        ],
        capture_output=True,
        check=True,
    )
    existing_legacy = [
        item.decode("utf-8", errors="surrogateescape")
        for item in proc.stdout.split(b"\0")
        if item and (ROOT / item.decode("utf-8", errors="surrogateescape")).exists()
    ]
    assert existing_legacy == []
    assert not (ROOT / "plugins").exists()
    assert not (ROOT / ".codex-plugin").exists()
    assert not (ROOT / ".agents").exists()
    assert (ROOT / "skills/med-autoscience/SKILL.md").read_bytes() == (
        ROOT / "agent/primary_skill/SKILL.md"
    ).read_bytes()
    assert (ROOT / "skills/med-autoscience/agents/openai.yaml").is_file()
    assert os.access(ROOT / "bin/mas-app-contribution", os.X_OK)
