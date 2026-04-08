from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.display_pack_loader import (
    load_enabled_local_display_pack_records,
    load_enabled_local_display_pack_template_records,
    load_enabled_local_display_pack_templates,
    load_enabled_local_display_packs,
    resolve_display_pack_selection,
)


def _write_display_pack_config(repo_root: Path, *, version: str = "0.1.0") -> None:
    config_dir = repo_root / "config"
    config_dir.mkdir()
    (config_dir / "display_packs.toml").write_text(
        f"""
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "display-packs/fenggaolab.org.medical-display-core"
version = "{version}"

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


def _write_paper_display_pack_config(
    paper_root: Path,
    *,
    version: str = "0.2.0",
    inherit_repo_defaults: bool = True,
) -> None:
    (paper_root / "display_packs.toml").write_text(
        f"""
inherit_repo_defaults = {"true" if inherit_repo_defaults else "false"}
enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "paper-display-packs/fenggaolab.org.medical-display-core"
version = "{version}"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_pack_manifest(pack_root: Path, *, pack_id: str, version: str = "0.1.0") -> None:
    (pack_root / "templates").mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        (
            f'pack_id = "{pack_id}"\n'
            f'version = "{version}"\n'
            'display_api_version = "1"\n'
            'default_execution_mode = "python_plugin"\n'
            'summary = "test pack"\n'
        ),
        encoding="utf-8",
    )


def _write_template_manifest(
    pack_root: Path,
    *,
    entrypoint: str = "pkg.module:render",
) -> None:
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
    assert manifests[0].version == "0.1.0"


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
    assert records[0].source_config.declared_in == "repo"


def test_load_enabled_local_display_packs_fails_on_pack_id_mismatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)

    _write_pack_manifest(
        repo_root / "display-packs" / "fenggaolab.org.medical-display-core",
        pack_id="fenggaolab.org.other-pack",
    )

    with pytest.raises(ValueError, match="pack_id mismatch"):
        load_enabled_local_display_packs(repo_root)


def test_load_enabled_local_display_packs_rejects_requested_version_mismatch(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root, version="0.2.0")

    _write_pack_manifest(
        repo_root / "display-packs" / "fenggaolab.org.medical-display-core",
        pack_id="fenggaolab.org.medical-display-core",
        version="0.1.0",
    )

    with pytest.raises(ValueError, match="version mismatch"):
        load_enabled_local_display_packs(repo_root)


def test_paper_display_pack_config_overrides_repo_source_and_version(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root, version="0.1.0")
    repo_pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    _write_pack_manifest(
        repo_pack_root,
        pack_id="fenggaolab.org.medical-display-core",
        version="0.1.0",
    )
    _write_template_manifest(repo_pack_root, entrypoint="repo_pack.renderers:render")

    paper_root = tmp_path / "paper"
    paper_root.mkdir()
    _write_paper_display_pack_config(paper_root, version="0.2.0")
    paper_pack_root = paper_root / "paper-display-packs" / "fenggaolab.org.medical-display-core"
    _write_pack_manifest(
        paper_pack_root,
        pack_id="fenggaolab.org.medical-display-core",
        version="0.2.0",
    )
    _write_template_manifest(paper_pack_root, entrypoint="paper_pack.renderers:render")

    selection = resolve_display_pack_selection(repo_root, paper_root=paper_root)
    records = load_enabled_local_display_pack_records(repo_root, paper_root=paper_root)
    template_records = load_enabled_local_display_pack_template_records(repo_root, paper_root=paper_root)

    assert selection.paper_config_present is True
    assert selection.enabled_pack_ids == ("fenggaolab.org.medical-display-core",)
    assert records[0].pack_root == paper_pack_root
    assert records[0].pack_manifest.version == "0.2.0"
    assert records[0].source_config.declared_in == "paper"
    assert template_records[0].template_manifest.entrypoint == "paper_pack.renderers:render"


def test_paper_display_pack_config_can_disable_repo_defaults(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)
    paper_root = tmp_path / "paper"
    paper_root.mkdir()
    _write_paper_display_pack_config(paper_root, inherit_repo_defaults=False)

    selection = resolve_display_pack_selection(repo_root, paper_root=paper_root)

    assert selection.inherit_repo_defaults is False
    assert selection.enabled_pack_ids == ("fenggaolab.org.medical-display-core",)
