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
