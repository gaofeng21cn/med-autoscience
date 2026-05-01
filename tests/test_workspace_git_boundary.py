from __future__ import annotations

import importlib
from pathlib import Path
import subprocess


def test_init_workspace_dry_run_reports_workspace_git_plan(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "dry-run-git-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="dry-run-git",
        dry_run=True,
        force=False,
    )

    assert str(workspace_root / ".gitignore") in result["created_files"]
    assert result["workspace_git"] == {
        "enabled": True,
        "initialized": False,
        "already_initialized": False,
        "would_initialize": True,
        "git_dir": str(workspace_root / ".git"),
        "gitignore_path": str(workspace_root / ".gitignore"),
    }
    assert not workspace_root.exists()


def test_init_workspace_creates_outer_git_boundary_and_ignores_mds_quests(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "git-boundary-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="git-boundary",
        dry_run=False,
        force=False,
    )

    assert (workspace_root / ".git").exists()
    assert result["workspace_git"]["enabled"] is True
    assert result["workspace_git"]["initialized"] is True
    assert result["workspace_git"]["already_initialized"] is False
    workspace_gitignore = workspace_root / ".gitignore"
    assert workspace_gitignore.is_file()
    assert "ops/med-deepscientist/runtime/quests/" in workspace_gitignore.read_text(encoding="utf-8")

    nested_quest_payload = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "001" / "scratch.txt"
    nested_quest_payload.parent.mkdir(parents=True, exist_ok=True)
    nested_quest_payload.write_text("runtime-owned\n", encoding="utf-8")
    check_ignore = subprocess.run(
        ["git", "check-ignore", str(nested_quest_payload.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_ignore.returncode == 0
    branch_name = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=workspace_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    relative_paths = subprocess.run(
        ["git", "config", "worktree.useRelativePaths"],
        cwd=workspace_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    assert branch_name == "main"
    assert relative_paths == "true"
    assert _git_config(workspace_root, "gc.auto") == "0"
    assert _git_config(workspace_root, "gc.autoPackLimit") == "0"
    assert _git_config(workspace_root, "maintenance.auto") == "false"

    large_download = workspace_root / "portfolio" / "data_assets" / "public" / "downloads" / "asset.zip"
    large_download.parent.mkdir(parents=True, exist_ok=True)
    large_download.write_text("data\n", encoding="utf-8")
    check_large_download = subprocess.run(
        ["git", "check-ignore", str(large_download.relative_to(workspace_root))],
        cwd=workspace_root,
        check=False,
        text=True,
        capture_output=True,
    )
    assert check_large_download.returncode == 0


def test_init_workspace_backfills_gitignore_and_git_config_for_existing_repo(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "existing-git-workspace"
    workspace_root.mkdir()
    subprocess.run(["git", "init"], cwd=workspace_root, check=True, text=True, capture_output=True)
    (workspace_root / ".gitignore").write_text("custom-local-rule/\n", encoding="utf-8")

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="existing-git",
        dry_run=False,
        force=False,
    )

    assert result["workspace_git"]["initialized"] is False
    assert result["workspace_git"]["already_initialized"] is True
    workspace_gitignore = (workspace_root / ".gitignore").read_text(encoding="utf-8")
    assert "custom-local-rule/" in workspace_gitignore
    assert "datasets/standardized_longitudinal/" in workspace_gitignore
    assert "storage_audit/" in workspace_gitignore
    assert _git_config(workspace_root, "worktree.useRelativePaths") == "true"
    assert _git_config(workspace_root, "gc.auto") == "0"
    assert _git_config(workspace_root, "gc.autoPackLimit") == "0"
    assert _git_config(workspace_root, "maintenance.auto") == "false"


def test_init_workspace_can_skip_workspace_git_initialization(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "no-git-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="no-git",
        dry_run=False,
        force=False,
        initialize_git=False,
    )

    assert result["workspace_git"] == {
        "enabled": False,
        "initialized": False,
        "already_initialized": False,
        "would_initialize": False,
        "git_dir": str(workspace_root / ".git"),
        "gitignore_path": str(workspace_root / ".gitignore"),
    }
    assert not (workspace_root / ".git").exists()
    assert (workspace_root / ".gitignore").is_file()


def _git_config(workspace_root: Path, key: str) -> str:
    return subprocess.run(
        ["git", "config", "--get", key],
        cwd=workspace_root,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
