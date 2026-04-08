from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.display_pack_loader import (
    load_enabled_local_display_pack_template_records,
    load_enabled_local_display_pack_templates,
    load_enabled_local_display_packs,
)


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


def _write_template_manifest(pack_root: Path, *, entrypoint: str = "pkg.module:render") -> None:
    template_root = pack_root / "templates" / "roc_curve_binary"
    template_root.mkdir(parents=True, exist_ok=True)
    (template_root / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "roc_curve_binary"',
                'full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary"',
                'kind = "evidence_figure"',
                'display_name = "ROC Curve (Binary Outcome)"',
                'paper_family_ids = ["A"]',
                'audit_family = "Prediction Performance"',
                'renderer_family = "r_ggplot2"',
                'input_schema_ref = "binary_prediction_curve_inputs_v1"',
                'qc_profile_ref = "publication_evidence_curve"',
                'required_exports = ["png", "pdf"]',
                'execution_mode = "python_plugin"',
                f'entrypoint = "{entrypoint}"',
                "paper_proven = false",
            )
        )
        + "\n",
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


def test_load_enabled_local_display_pack_templates_reads_enabled_pack_templates(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)

    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    _write_pack_manifest(
        pack_root,
        pack_id="fenggaolab.org.medical-display-core",
    )
    _write_template_manifest(pack_root)

    manifests = load_enabled_local_display_pack_templates(repo_root)

    assert [item.full_template_id for item in manifests] == [
        "fenggaolab.org.medical-display-core::roc_curve_binary"
    ]
    assert manifests[0].display_class_id == "prediction_performance"


def test_load_enabled_local_display_pack_template_records_preserves_pack_root(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)

    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    _write_pack_manifest(
        pack_root,
        pack_id="fenggaolab.org.medical-display-core",
    )
    _write_template_manifest(pack_root)

    records = load_enabled_local_display_pack_template_records(repo_root)

    assert len(records) == 1
    assert records[0].pack_root == pack_root
    assert records[0].template_manifest.full_template_id == "fenggaolab.org.medical-display-core::roc_curve_binary"


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
