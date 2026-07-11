from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.family


def test_foundry_agent_series_is_a_refs_only_domain_consumer_contract() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts" / "foundry_agent_series.json").read_text(
            encoding="utf-8"
        )
    )

    assert contract["surface_kind"] == "opl_foundry_agent_series_consumer"
    assert contract["version"] == "foundry-agent-series-consumer.v1"
    assert contract["canonical_policy_export"] == (
        "opl-framework/foundry-agent-series-policy"
    )
    assert contract["canonical_series_contract_ref"] == (
        "contracts/opl-framework/foundry-agent-series-contract.json"
    )
    assert contract["canonical_skeleton_contract_ref"] == (
        "contracts/opl-framework/standard-domain-agent-skeleton-contract.json"
    )
    assert contract["shared_policy_release"] == {
        "policy_release_contract_ref": (
            "contracts/opl-framework/foundry-agent-series-policy-release.json"
        ),
        "policy_bundle_fingerprint": (
            "sha256:503f515e8fa08b3f81ce28cac461368c609d4565de239c9f95c3f910cb758ed5"
        ),
        "fingerprint_algorithm": "sha256:stable-json",
        "domain_contract_policy_release_pin_required": True,
        "domain_adapter_must_not_copy_policy_body_as_authority": True,
        "consumer_alignment_check": "foundry:policy-release",
    }
    assert "ai_reviewer_or_auditor_record_refs" in contract["domain_delta"][
        "domain_output_refs"
    ]
    assert contract["domain_delta"]["minimal_authority_functions_ref"] == (
        "contracts/pack_compiler_input.json#/minimal_authority_functions"
    )
    assert contract["authority_boundary"]
    assert all(value is False for value in contract["authority_boundary"].values())


def test_foundry_consumer_does_not_restore_framework_release_authority() -> None:
    contract_path = REPO_ROOT / "contracts" / "foundry_agent_series.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "shared_release_pin_strategy" not in contract
    assert contract["canonical_policy_export"] == (
        "opl-framework/foundry-agent-series-policy"
    )
    assert not (
        REPO_ROOT
        / "contracts"
        / "opl-framework"
        / "foundry-agent-series-policy-release.json"
    ).exists()
    dependency_names = {
        dependency.split(" ", 1)[0].split("@", 1)[0].strip()
        for dependency in pyproject["project"]["dependencies"]
    }
    assert dependency_names.isdisjoint({"opl-framework", "opl-framework-shared"})
    contract_text = contract_path.read_text(encoding="utf-8")
    assert "opl-framework-shared" not in contract_text
    assert "latest-stable" not in contract_text
