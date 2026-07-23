from __future__ import annotations

import importlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_package_plugin_and_python_versions_are_one_semver() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package = json.loads(
        (ROOT / "contracts/opl_agent_package_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    plugin = json.loads(
        (
            ROOT
            / "plugins/med-autoscience/.codex-plugin/plugin.json"
        ).read_text(encoding="utf-8")
    )

    assert package["version"] == pyproject["project"]["version"] == plugin["version"]
    assert package["version"] == "0.2.17"
    assert "distribution_payload" not in package
    assert package["agent_id"] == package["package_id"] == "mas"
    assert package["codex_surface"]["plugin_id"] == "med-autoscience"
    assert "scripts" not in pyproject["project"]
    assert plugin["name"] == "med-autoscience"
    assert plugin["repository"] == "https://github.com/gaofeng21cn/med-autoscience"
    assert plugin["skills"] == "./skills/"
    assert "mcpServers" not in plugin
    assert plugin["interface"]["displayName"] == "Med Auto Science"
    assert plugin["interface"]["composerIcon"] == plugin["interface"]["logo"]
    plugin_root = ROOT / "plugins/med-autoscience"
    assert (plugin_root / plugin["interface"]["composerIcon"]).is_file()
    assert (plugin_root / "skills/med-autoscience/agents/openai.yaml").is_file()
    assert not (plugin_root / "bin/medautosci-mcp").exists()
    assert not (ROOT / "plugins/mas").exists()
    assert not (ROOT / ".agents/plugins/marketplace.json").exists()
    assert not any((ROOT / "src/med_autoscience/cli").glob("*.py"))
    assert not (ROOT / "scripts/install-codex-plugin.sh").exists()

    prompt_text = json.dumps(plugin["interface"]["defaultPrompt"]).lower()
    assert "doctor" not in prompt_text
    assert "controller" not in prompt_text


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


def test_validator_release_set_preserves_managed_provenance_gate() -> None:
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

    assert release["release_set_id"] == "mas-validator-0.2.17"
    assert release["package_version"] == package["version"] == "0.2.17"
    assert package["release_set_receipt_ref"] == (
        "contracts/mas_validator_release_set_receipt.json"
    )
    assert release["source_ref"] == "refs/tags/v0.2.17"
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


def test_scholarskills_is_a_managed_optional_enhancement_not_a_sixth_agent() -> None:
    package = json.loads(
        (ROOT / "contracts/opl_agent_package_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    dependencies = package["capability_dependencies"]

    assert len(dependencies) == 1
    dependency = dependencies[0]
    assert dependency["package_id"] == "mas-scholar-skills"
    assert dependency["kind"] == "framework_capability_package"
    assert dependency["required"] is False
    assert dependency["dependency_kind"] == "optional_enhancement"
    assert dependency["version_requirement"] == ">=0.2.12 <0.3.0"
    assert package["codex_surface"]["standalone_distribution"] == (
        "repo_carrier_source"
    )

    active_truth_paths = [
        "README.md",
        "README.zh-CN.md",
        "bootstrap/README.md",
        "docs/architecture.md",
        "docs/invariants.md",
        "docs/whitepapers/mas-whitepaper.md",
        "docs/references/integration/codex_plugin.md",
        "docs/active/stage_surface_standardization_program.md",
    ]
    active_truth = {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in active_truth_paths
    }
    forbidden_legacy_claims = [
        "required `mas-scholar-skills` closure",
        "必需的 `mas-scholar-skills` 闭包",
        "原子解析 MAS 与 `mas-scholar-skills` 依赖闭包",
        "`mas-scholar-skills` 是 MAS 的必需能力包",
        "`mas-scholar-skills` 是 MAS 硬依赖",
        "产品依赖闭包",
        "operational_ready=false",
        "进入同一 package closure transaction",
        "对当前依赖闭包和 scope materialization fail-closed 修复",
        "在这些 lifecycle transaction 内完成依赖闭包解析",
        "required knowledge / ScholarSkills / tool affordances",
    ]
    for path, text in active_truth.items():
        for legacy_claim in forbidden_legacy_claims:
            assert legacy_claim not in text, f"{path} retains {legacy_claim}"
    for path in active_truth_paths[:6]:
        text = active_truth[path]
        assert (
            "可选专业增强" in text or "optional professional enhancement" in text
        )
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
    assert package["codex_surface"]["bundled_capability_package_ids"] == [
        "mas-scholar-skills"
    ]
    assert dependency["activation_materialization"]["required"] is False
    assert dependency["activation_materialization"]["receipt_required"] is False
    assert dependency["missing_or_incompatible_policy"] == (
        "continue_with_consumer_core_and_record_diagnostic"
    )


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
