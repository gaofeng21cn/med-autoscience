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
            "sha256:7e50ce27f04c5fe801d4da0b385265def3c7e6df1d32b8f3b8ec29410ba5545c"
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


def test_foundry_consumer_has_no_local_framework_dependency() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependency_names = {
        dependency.split(" ", 1)[0].split("@", 1)[0].strip()
        for dependency in pyproject["project"]["dependencies"]
    }

    assert "opl-framework" not in dependency_names
