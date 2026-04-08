from __future__ import annotations

from pathlib import Path
import subprocess

from med_autoscience.display_pack_lock import build_display_pack_lock_payload


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write_local_pack_config(repo_root: Path) -> None:
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "display_packs.toml").write_text(
        """
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "display-packs/fenggaolab.org.medical-display-core"
version = "0.1.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_git_pack_config(repo_root: Path, *, relative_repo_path: str) -> None:
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "display_packs.toml").write_text(
        f"""
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "git_repo"
pack_id = "fenggaolab.org.medical-display-core"
path = "{relative_repo_path}"
pack_subdir = "packs/core"
version = "0.2.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_pack_manifest(pack_root: Path, *, version: str) -> None:
    (pack_root / "templates" / "roc_curve_binary").mkdir(parents=True, exist_ok=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                f'version = "{version}"',
                'display_api_version = "1"',
                'default_execution_mode = "python_plugin"',
                'summary = "test pack"',
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_template_manifest(template_root: Path) -> None:
    (template_root / "examples").mkdir(parents=True, exist_ok=True)
    (template_root / "goldens").mkdir(parents=True, exist_ok=True)
    (template_root / "exemplars").mkdir(parents=True, exist_ok=True)
    (template_root / "audit").mkdir(parents=True, exist_ok=True)
    (template_root / "examples" / "input.json").write_text("{}", encoding="utf-8")
    (template_root / "goldens" / "main.png").write_text("png", encoding="utf-8")
    (template_root / "exemplars" / "source.md").write_text("# exemplar", encoding="utf-8")
    (template_root / "audit" / "notes.md").write_text("# audit", encoding="utf-8")
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
                'golden_case_paths = ["goldens/main.png"]',
                'exemplar_refs = ["Nature Medicine 2025 Figure 2"]',
                'execution_mode = "python_plugin"',
                'entrypoint = "pkg.module:render"',
                "paper_proven = false",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def test_build_display_pack_lock_payload_captures_template_asset_inventory(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_local_pack_config(repo_root)

    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    _write_pack_manifest(pack_root, version="0.1.0")
    _write_template_manifest(pack_root / "templates" / "roc_curve_binary")

    payload = build_display_pack_lock_payload(repo_root=repo_root)

    pack_entry = payload["enabled_packs"][0]
    template_entry = pack_entry["templates"][0]

    assert pack_entry["template_count"] == 1
    assert template_entry["template_id"] == "roc_curve_binary"
    assert template_entry["template_manifest_path"].endswith("templates/roc_curve_binary/template.toml")
    assert len(template_entry["template_manifest_sha256"]) == 64
    assert template_entry["golden_case_paths"] == ["goldens/main.png"]
    assert template_entry["exemplar_refs"] == ["Nature Medicine 2025 Figure 2"]
    assert template_entry["examples_dir"].endswith("templates/roc_curve_binary/examples")
    assert template_entry["examples_file_count"] == 1
    assert template_entry["goldens_dir"].endswith("templates/roc_curve_binary/goldens")
    assert template_entry["goldens_file_count"] == 1
    assert template_entry["exemplars_dir"].endswith("templates/roc_curve_binary/exemplars")
    assert template_entry["exemplars_file_count"] == 1
    assert template_entry["audit_dir"].endswith("templates/roc_curve_binary/audit")
    assert template_entry["audit_file_count"] == 1


def test_build_display_pack_lock_payload_captures_git_repo_source_provenance(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    git_repo_root = tmp_path / "display-core-git"
    git_repo_root.mkdir()
    _write_git_pack_config(repo_root, relative_repo_path="../display-core-git")

    pack_root = git_repo_root / "packs" / "core"
    _write_pack_manifest(pack_root, version="0.2.0")
    _write_template_manifest(pack_root / "templates" / "roc_curve_binary")

    _git(git_repo_root, "init", "-b", "main")
    _git(git_repo_root, "config", "user.name", "Test User")
    _git(git_repo_root, "config", "user.email", "test@example.com")
    _git(git_repo_root, "add", ".")
    _git(git_repo_root, "commit", "-m", "Initial display pack")
    expected_commit = _git(git_repo_root, "rev-parse", "HEAD")

    payload = build_display_pack_lock_payload(repo_root=repo_root)

    pack_entry = payload["enabled_packs"][0]

    assert pack_entry["source_kind"] == "git_repo"
    assert pack_entry["source_path"] == "../display-core-git"
    assert pack_entry["pack_subdir"] == "packs/core"
    assert pack_entry["git_commit"] == expected_commit
    assert pack_entry["git_is_dirty"] is False
    assert pack_entry["resolved_source_root"].endswith("display-core-git")
