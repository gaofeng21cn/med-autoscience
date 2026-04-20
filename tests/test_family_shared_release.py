from __future__ import annotations

import json
from pathlib import Path

from med_autoscience import family_shared_release as module


OWNER_COMMIT = "bc20e23c7fd9088a33db31c87d1e3075dac3144b"


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
    assert [item["status"] for item in inspection["findings"]] == ["aligned", "aligned"]
    assert all(item["pins"] == [inspection["owner_commit"]] for item in inspection["findings"])


def test_family_shared_alignment_uses_repo_root_by_default(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "med-autoscience"
    owner_repo_root = tmp_path / "one-person-lab"
    _write_owner_release_contract(owner_repo_root=owner_repo_root)
    _write_consumer_pin_files(repo_root=repo_root)
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    inspection = module.inspect_current_repo_family_shared_alignment()

    assert inspection["repo_id"] == "medautoscience"
    assert Path(inspection["repo_root"]) == repo_root
