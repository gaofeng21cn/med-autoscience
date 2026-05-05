from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from med_autoscience.runtime_protocol.runtime_lifecycle_contract import SQLITE_GITIGNORE_PATTERNS


WORKSPACE_GITIGNORE_ENTRIES = (
    ".DS_Store",
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "ops/medautoscience/config.env",
    "ops/medautoscience/logs/",
    "ops/med-deepscientist/config.env",
    "ops/med-deepscientist/runtime/quests/",
    "ops/med-deepscientist/runtime/archives/**",
    "!ops/med-deepscientist/runtime/archives/README.md",
    "ops/med-deepscientist/runtime/recovery/**",
    "ops/med-deepscientist/runtime/runtime/**",
    "ops/med-deepscientist/runtime/logs/",
    "ops/med-deepscientist/runtime/memory/",
    "ops/med-deepscientist/runtime/config/",
    "ops/med-deepscientist/runtime/python-env/",
    "ops/med-deepscientist/runtime/uv-cache/",
    "ops/med-deepscientist/runtime/bundle/",
    "ops/med-deepscientist/runtime/tools/",
    "ops/med-deepscientist/runtime/*.pid",
    "ops/med-deepscientist/runtime/*.sock",
    "ops/med-deepscientist/paper/**",
    "ops/med-deepscientist/styles/frontiers_word_templates/**",
    "tmp/",
    ".tmp/",
    *SQLITE_GITIGNORE_PATTERNS,
    "inbox/**",
    "!inbox/README.md",
    "storage_audit/",
    "refs/**/logs/**",
    "refs/**/data/**",
    "refs/**/site/**",
    "refs/**/reports/experiment_results/**",
    "refs/**/*.pdf",
    "refs/**/*.png",
    "refs/**/*.jpg",
    "refs/**/*.jpeg",
    "refs/**/*.zip",
    "refs/**/*.html",
    "refs/**/*.Rhistory",
    "refs/**/.cursorignore",
    "refs/**/.cursor/**",
    "datasets/raw/",
    "datasets/**/raw/",
    "datasets/restricted_raw/",
    "datasets/deidentified_longitudinal/",
    "datasets/standardized_longitudinal/",
    "datasets/external/",
    "datasets/**/*.csv",
    "datasets/**/*.tsv",
    "datasets/**/*.xlsx",
    "datasets/**/*.xls",
    "datasets/**/*.parquet",
    "datasets/**/*.pkl",
    "datasets/**/*.sqlite",
    "datasets/**/*.db",
    "!datasets/**/dataset_manifest.yaml",
    "!datasets/**/*.md",
    "!datasets/**/*.json",
    "registry/raw_snapshots/**",
    "portfolio/data_assets/public/downloads/",
    "portfolio/data_assets/private/diffs/",
    "portfolio/data_assets/private/pruned_releases/",
    "portfolio/**/*.csv",
    "portfolio/**/*.tsv",
    "portfolio/**/*.xlsx",
    "portfolio/**/*.xls",
    "portfolio/**/*.parquet",
    "portfolio/**/*.pkl",
    "ops/framework_refs/_repo_compare/**",
    "!ops/framework_refs/README.md",
    "studies/*/artifacts/**",
    "!studies/*/artifacts/README.md",
    "!studies/*/artifacts/evidence_ledger.json",
    "!studies/*/artifacts/review_ledger.json",
    "studies/*/runtime_binding.yaml",
    "studies/*/manuscript/current_package/**",
    "studies/*/manuscript/journal_packages/**",
    "studies/*/manuscript/*_submission_*/**",
    "studies/*/manuscript/*.zip",
    "studies/*/manuscript/*.pdf",
    "studies/*/manuscript/*.docx",
    "studies/*/manuscript/*manifest.json",
    "studies/*/manuscript/delivery_status.json",
    "studies/*/paper/submission_minimal/**",
    "studies/*/paper/build/**",
    "studies/*/paper/latex/**",
    "studies/*/paper/direct_migration/**",
    "studies/*/paper/figures/**",
    "studies/*/paper/tables/**",
    "studies/*/paper/derived/**",
    "studies/*/submission_packages/**",
    "studies/*/analysis/**/*.csv",
    "studies/*/analysis/**/*.tsv",
    "studies/*/analysis/**/*.xlsx",
    "studies/*/analysis/**/*.xls",
    "studies/*/analysis/**/*.parquet",
    "studies/*/analysis/**/*.pkl",
    "studies/*/analysis/**/*.png",
    "studies/*/analysis/**/*.jpg",
    "studies/*/analysis/**/*.jpeg",
    "studies/*/analysis/**/*.pdf",
    "studies/*/analysis/**/*.svg",
    "studies/*/analysis/**/derived/**",
)

WORKSPACE_GIT_CONFIG_ENTRIES = (
    ("worktree.useRelativePaths", "true"),
    ("gc.auto", "0"),
    ("gc.autoPackLimit", "0"),
    ("maintenance.auto", "false"),
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
        configure_existing_workspace_git(workspace_root=workspace_root)
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
    _configure_workspace_git(git_bin=git_bin, workspace_root=workspace_root)
    return _workspace_git_payload(
        workspace_root=workspace_root,
        enabled=True,
        initialized=True,
        already_initialized=False,
        would_initialize=False,
    )


def configure_existing_workspace_git(*, workspace_root: Path) -> bool:
    if not (workspace_root / ".git").exists():
        return False
    git_bin = shutil.which("git") or "git"
    _configure_workspace_git(git_bin=git_bin, workspace_root=workspace_root)
    return True


def _configure_workspace_git(*, git_bin: str, workspace_root: Path) -> None:
    for key, value in WORKSPACE_GIT_CONFIG_ENTRIES:
        _run_git(git_bin, ["config", key, value], workspace_root=workspace_root)
