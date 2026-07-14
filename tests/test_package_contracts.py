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
    assert package["version"] == "0.2.2"
    assert package["distribution_payload"]["immutable_tag"] == package["version"]
    assert "scripts" not in pyproject["project"]

    prompt_text = json.dumps(plugin["interface"]["defaultPrompt"]).lower()
    assert "doctor" not in prompt_text
    assert "controller" not in prompt_text


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
