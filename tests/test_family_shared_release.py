from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience import family_shared_release as module


OWNER_COMMIT = "bc20e23c7fd9088a33db31c87d1e3075dac3144b"
pytestmark = pytest.mark.family


def _write_owner_release_contract(*, owner_repo_root: Path, owner_commit: str = OWNER_COMMIT) -> None:
    contract_path = owner_repo_root / "contracts" / "family-release" / "shared-owner-release.json"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        json.dumps(
            {
                "contract_kind": "family_shared_owner_release.v1",
                "owner_repo": "one-person-lab",
                "owner_commit": owner_commit,
                "consumers": [
                    {
                        "repo_id": "medautoscience",
                        "repo_dir": "med-autoscience",
                        "verify_command": "scripts/verify.sh family",
                        "targets": [
                            {"file": "pyproject.toml", "kind": "python_dependency"},
                            {"file": "uv.lock", "kind": "python_lock"},
                        ],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_consumer_pin_files(*, repo_root: Path, owner_commit: str = OWNER_COMMIT) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "med-autoscience"',
                "dependencies = [",
                f'  "opl-harness-shared @ git+https://github.com/gaofeng21cn/one-person-lab.git@{owner_commit}#subdirectory=python/opl-harness-shared",',
                "]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (repo_root / "uv.lock").write_text(
        "\n".join(
            [
                "version = 1",
                f'source = {{ git = "https://github.com/gaofeng21cn/one-person-lab.git?subdirectory=python%2Fopl-harness-shared&rev={owner_commit}#{owner_commit}" }}',
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_current_checkout_family_shared_pins_align_with_opl_release_contract(tmp_path: Path) -> None:
    repo_root = tmp_path / "med-autoscience"
    owner_repo_root = tmp_path / "one-person-lab"
    _write_owner_release_contract(owner_repo_root=owner_repo_root)
    _write_consumer_pin_files(repo_root=repo_root)

    inspection = module.inspect_current_repo_family_shared_alignment(
        repo_root_override=repo_root,
        owner_repo_root=owner_repo_root,
    )

    assert inspection["status"] == "aligned"
    assert inspection["owner_commit"] == OWNER_COMMIT
    assert inspection["verify_command"] == "scripts/verify.sh family"
    assert [item["status"] for item in inspection["findings"]] == ["aligned", "aligned"]
    assert all(item["pins"] == [inspection["owner_commit"]] for item in inspection["findings"])


def test_foundry_agent_series_contract_pins_opl_owner_release_contract() -> None:
    contract = json.loads(
        (module.repo_root() / "contracts" / "foundry_agent_series.json").read_text(
            encoding="utf-8"
        )
    )

    assert contract["contract_version_policy"] == {
        "breaking_change_requires_new_version": True,
        "compatible_version_range": ["foundry-agent-series.v1"],
        "current_version": "foundry-agent-series.v1",
        "domain_contract_ref": "contracts/foundry_agent_series.json",
        "domain_descriptor_must_reference_domain_contract": True,
        "exact_version_pin_required": True,
    }
    release_pin = contract["shared_release_pin_strategy"]
    assert release_pin["owner_release_contract_ref"] == (
        "contracts/family-release/shared-owner-release.json"
    )
    assert release_pin["owner_commit_pin_required"] is True
    assert release_pin["owner_commit_pin"] == "ab30fb9c1b86de034c95bc5b4ebdf89eafa86e44"
    assert release_pin["domain_dependency_pin_required"] is True
    assert release_pin["consumer_alignment_check"] == "family:shared-release"
    assert release_pin["domain_contract_version_pin_does_not_authorize_domain_truth"] is True
    assert contract["shared_policy_release"] == {
        "policy_release_contract_ref": (
            "contracts/opl-framework/foundry-agent-series-policy-release.json"
        ),
        "policy_bundle_fingerprint": (
            "sha256:5d77102e99e6e49acd88714cd94dcafe0969b8f2a5529928d753002ac3d4619d"
        ),
        "fingerprint_algorithm": "sha256:stable-json",
        "domain_contract_policy_release_pin_required": True,
        "domain_adapter_must_not_copy_policy_body_as_authority": True,
        "consumer_alignment_check": "foundry:policy-release",
    }


def test_family_shared_alignment_uses_repo_root_by_default(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "med-autoscience"
    owner_repo_root = tmp_path / "one-person-lab"
    _write_owner_release_contract(owner_repo_root=owner_repo_root)
    _write_consumer_pin_files(repo_root=repo_root)
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    inspection = module.inspect_current_repo_family_shared_alignment()

    assert inspection["repo_id"] == "medautoscience"
    assert Path(inspection["repo_root"]) == repo_root
    assert inspection["verify_command"] == "scripts/verify.sh family"
