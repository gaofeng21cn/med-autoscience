from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.display_pack_loader import load_enabled_local_display_packs


def _write_display_pack_config(repo_root: Path) -> None:
    config_dir = repo_root / "config"
    config_dir.mkdir()
    (config_dir / "display_packs.toml").write_text(
        """
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "display-packs/fenggaolab.org.medical-display-core"

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-extra"
path = "display-packs/fenggaolab.org.medical-display-extra"

[[sources]]
kind = "git"
pack_id = "fenggaolab.org.medical-display-remote"
path = "display-packs/fenggaolab.org.medical-display-remote"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_pack_manifest(pack_root: Path, *, pack_id: str) -> None:
    (pack_root / "templates").mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        (
            f'pack_id = "{pack_id}"\n'
            'version = "0.1.0"\n'
            'display_api_version = "1"\n'
            'default_execution_mode = "python_plugin"\n'
        ),
        encoding="utf-8",
    )


def test_load_enabled_local_display_packs_reads_repo_config(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)

    _write_pack_manifest(
        repo_root / "display-packs" / "fenggaolab.org.medical-display-core",
        pack_id="fenggaolab.org.medical-display-core",
    )

    manifests = load_enabled_local_display_packs(repo_root)

    assert [item.pack_id for item in manifests] == ["fenggaolab.org.medical-display-core"]


def test_load_enabled_local_display_packs_uses_repo_root_for_source_path(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)

    _write_pack_manifest(
        repo_root / "display-packs" / "fenggaolab.org.medical-display-core",
        pack_id="fenggaolab.org.medical-display-core",
    )

    manifests = load_enabled_local_display_packs(repo_root)

    assert manifests[0].version == "0.1.0"


def test_load_enabled_local_display_packs_fails_on_pack_id_mismatch(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)

    _write_pack_manifest(
        repo_root / "display-packs" / "fenggaolab.org.medical-display-core",
        pack_id="fenggaolab.org.other-pack",
    )

    with pytest.raises(ValueError, match="pack_id mismatch"):
        load_enabled_local_display_packs(repo_root)
