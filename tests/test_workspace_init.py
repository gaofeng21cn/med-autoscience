from __future__ import annotations

import importlib
import json
import os
from pathlib import Path


def test_init_workspace_dry_run_reports_plan_without_writing_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "diabetes-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="diabetes",
        dry_run=True,
        force=False,
    )

    assert result["dry_run"] is True
    assert result["workspace_root"] == str(workspace_root)
    assert result["workspace_name"] == "diabetes"
    assert result["created_directories"]
    assert result["created_files"]
    assert not workspace_root.exists()


def test_init_workspace_creates_minimal_workspace_and_entry_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "glioma-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="glioma",
        dry_run=False,
        force=False,
    )

    assert result["dry_run"] is False
    assert workspace_root.exists()
    assert (workspace_root / "datasets").is_dir()
    assert (workspace_root / "contracts").is_dir()
    assert (workspace_root / "studies").is_dir()
    assert (workspace_root / "portfolio" / "data_assets").is_dir()
    assert (workspace_root / "ops" / "medautoscience" / "bin").is_dir()
    assert (workspace_root / "ops" / "deepscientist" / "bin").is_dir()

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "glioma.local.toml"
    assert profile_path.is_file()
    profile_text = profile_path.read_text(encoding="utf-8")
    assert 'name = "glioma"' in profile_text
    assert f'workspace_root = "{workspace_root}"' in profile_text
    assert 'default_startup_anchor_policy = "scout_first_for_continue_existing_state"' in profile_text
    assert 'legacy_code_execution_policy = "forbid_without_user_approval"' in profile_text
    assert 'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]' in profile_text

    med_config = workspace_root / "ops" / "medautoscience" / "config.env"
    deep_config = workspace_root / "ops" / "deepscientist" / "config.env"
    assert med_config.is_file()
    assert deep_config.is_file()

    show_profile = workspace_root / "ops" / "medautoscience" / "bin" / "show-profile"
    enter_study = workspace_root / "ops" / "medautoscience" / "bin" / "enter-study"
    resolve_journal_shortlist = workspace_root / "ops" / "medautoscience" / "bin" / "resolve-journal-shortlist"
    ds_doctor = workspace_root / "ops" / "deepscientist" / "bin" / "doctor"
    assert show_profile.is_file()
    assert enter_study.is_file()
    assert resolve_journal_shortlist.is_file()
    assert ds_doctor.is_file()
    assert os.access(show_profile, os.X_OK)
    assert os.access(enter_study, os.X_OK)
    assert os.access(resolve_journal_shortlist, os.X_OK)
    assert os.access(ds_doctor, os.X_OK)

    root_readme = workspace_root / "README.md"
    assert root_readme.is_file()
    root_readme_text = root_readme.read_text(encoding="utf-8")
    assert "workspace" in root_readme_text.lower()
    assert "ops/medautoscience/bin/show-profile" in root_readme_text
    assert "不要直接通过 DeepScientist UI、CLI 或 daemon HTTP API 发起研究 quest" in root_readme_text

    deepscientist_readme = workspace_root / "ops" / "deepscientist" / "README.md"
    assert deepscientist_readme.is_file()
    deepscientist_readme_text = deepscientist_readme.read_text(encoding="utf-8")
    assert "runtime 运维面" in deepscientist_readme_text
    assert "不是研究入口" in deepscientist_readme_text
    assert "ops/medautoscience/bin/enter-study" in deepscientist_readme_text

    workspace_rules = workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md"
    assert workspace_rules.is_file()
    workspace_rules_text = workspace_rules.read_text(encoding="utf-8")
    assert "优先复用 MedAutoScience 已覆盖的成熟 controller / CLI / overlay skill" in workspace_rules_text
    assert "边界明确且 startup-ready 后，默认切入 DeepScientist managed runtime 的自动持续推进" in workspace_rules_text


def test_init_workspace_is_idempotent_and_force_overwrites_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "pituitary-workspace"

    first = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=False,
    )
    assert first["created_files"]

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "pituitary.local.toml"
    profile_path.write_text("# local edit\n", encoding="utf-8")

    second = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=False,
    )
    assert str(profile_path) in second["skipped_files"]
    assert profile_path.read_text(encoding="utf-8") == "# local edit\n"

    third = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=True,
    )
    assert str(profile_path) in third["overwritten_files"]
    assert 'name = "pituitary"' in profile_path.read_text(encoding="utf-8")
