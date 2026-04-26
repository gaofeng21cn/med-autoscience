from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


WORKSPACE_GITIGNORE_ENTRIES = (
    ".DS_Store",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "ops/medautoscience/logs/",
    "ops/med-deepscientist/runtime/quests/",
    "ops/med-deepscientist/runtime/logs/",
    "ops/med-deepscientist/runtime/memory/",
    "ops/med-deepscientist/runtime/config/",
    "ops/med-deepscientist/runtime/python-env/",
    "ops/med-deepscientist/runtime/uv-cache/",
    "ops/med-deepscientist/runtime/bundle/",
    "ops/med-deepscientist/runtime/tools/",
    "ops/med-deepscientist/runtime/*.pid",
    "ops/med-deepscientist/runtime/*.sock",
    "datasets/raw/",
    "datasets/**/raw/",
)


def is_workspace_gitignore_path(path: Path) -> bool:
    return path.name == ".gitignore"


def render_workspace_gitignore() -> str:
    return (
        "# MedAutoScience workspace-local Git boundary.\n"
        "# MDS quest repos own their own Git state under ops/med-deepscientist/runtime/quests/.\n"
        + "\n".join(WORKSPACE_GITIGNORE_ENTRIES)
        + "\n"
    )


def merge_workspace_gitignore_content(existing_content: str) -> str:
    existing_lines = [line.rstrip("\n") for line in existing_content.splitlines()]
    existing_set = set(existing_lines)
    missing_entries = [entry for entry in WORKSPACE_GITIGNORE_ENTRIES if entry not in existing_set]
    if not missing_entries:
        return existing_content
    base = existing_content.rstrip()
    separator = "\n\n" if base else ""
    return f"{base}{separator}{chr(10).join(missing_entries)}\n"


def _workspace_git_payload(
    *,
    workspace_root: Path,
    enabled: bool,
    initialized: bool,
    already_initialized: bool,
    would_initialize: bool,
) -> dict[str, object]:
    return {
        "enabled": enabled,
        "initialized": initialized,
        "already_initialized": already_initialized,
        "would_initialize": would_initialize,
        "git_dir": str(workspace_root / ".git"),
        "gitignore_path": str(workspace_root / ".gitignore"),
    }


def workspace_git_plan(*, workspace_root: Path, initialize_git: bool, dry_run: bool) -> dict[str, object]:
    already_initialized = (workspace_root / ".git").exists()
    return _workspace_git_payload(
        workspace_root=workspace_root,
        enabled=initialize_git,
        initialized=False,
        already_initialized=already_initialized,
        would_initialize=bool(initialize_git and dry_run and not already_initialized),
    )


def _run_git(git_bin: str, args: list[str], *, workspace_root: Path) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            [git_bin, *args],
            cwd=workspace_root,
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git executable is required to initialize a MedAutoScience workspace Git boundary.") from exc
    if result.returncode != 0:
        command = " ".join(["git", *args])
        message = result.stderr.strip() or result.stdout.strip() or f"{command} failed"
        raise RuntimeError(message)
    return result


def ensure_workspace_git(*, workspace_root: Path, initialize_git: bool) -> dict[str, object]:
    already_initialized = (workspace_root / ".git").exists()
    if not initialize_git:
        return _workspace_git_payload(
            workspace_root=workspace_root,
            enabled=False,
            initialized=False,
            already_initialized=already_initialized,
            would_initialize=False,
        )
    if already_initialized:
        return _workspace_git_payload(
            workspace_root=workspace_root,
            enabled=True,
            initialized=False,
            already_initialized=True,
            would_initialize=False,
        )
    git_bin = shutil.which("git") or "git"
    _run_git(git_bin, ["init"], workspace_root=workspace_root)
    _run_git(git_bin, ["branch", "-M", "main"], workspace_root=workspace_root)
    _run_git(git_bin, ["config", "worktree.useRelativePaths", "true"], workspace_root=workspace_root)
    return _workspace_git_payload(
        workspace_root=workspace_root,
        enabled=True,
        initialized=True,
        already_initialized=False,
        would_initialize=False,
    )
