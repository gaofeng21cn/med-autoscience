from __future__ import annotations

import json
from pathlib import Path
import tomllib

import pytest


pytestmark = pytest.mark.meta
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
    assert package["version"] == "0.2.9"
    assert package["distribution_payload"]["immutable_tag"] == package["version"]
    assert package["agent_id"] == package["package_id"] == "mas"
    assert package["codex_surface"]["plugin_id"] == "med-autoscience"
    assert "scripts" not in pyproject["project"]

    prompt_text = json.dumps(plugin["interface"]["defaultPrompt"]).lower()
    assert "doctor" not in prompt_text
    assert "controller" not in prompt_text


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

    assert release["package_version"] == package["version"] == "0.2.9"
    assert package["release_set_receipt_ref"] == (
        "contracts/mas_validator_release_set_receipt.json"
    )
    assert release["source_ref"] == "refs/tags/v0.2.9"
    assert release["supported_scope"]["kind"] == "exact_byte_domain_validator"
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

    internal_actions = {
        action["action_id"]: action
        for action in catalog["actions"]
        if action["action_id"]
        in {
            "candidate_admission_authority_evaluate",
            "paper_mission_authority_evaluate",
        }
    }
    assert len(internal_actions) == 2
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


def test_scholarskills_is_a_managed_hard_dependency_not_a_sixth_agent() -> None:
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
    assert dependency["required"] is True
    assert dependency["dependency_kind"] == "hard_runtime_dependency"
    assert dependency["version_requirement"] == ">=0.2.0 <0.3.0"
    assert package["distribution_payload"]["required_skill_pack_lock_refs"] == [
        "opl://agent-package-lock/mas-scholar-skills/0.2.3/"
        "managed-ghcr-capability-package"
    ]
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
