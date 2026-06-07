from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from med_autoscience.runtime_protocol.domain_authority_refs_index import SQLITE_GITIGNORE_PATTERNS


WORKSPACE_GITIGNORE_ENTRIES = (
    ".DS_Store",
    "ops/medautoscience/.venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "ops/medautoscience/config.env",
    "ops/medautoscience/logs/",
    "ops/mas/config.env",
    "runtime/quests/",
    "runtime/archives/**",
    "!runtime/archives/README.md",
    "runtime/restore_index/**",
    "!runtime/restore_index/README.md",
    "runtime/recovery/**",
    "runtime/runtime/**",
    "runtime/logs/",
    "runtime/memory/",
    "runtime/config/",
    "runtime/python-env/",
    "runtime/uv-cache/",
    "runtime/bundle/",
    "runtime/tools/",
    "runtime/*.pid",
    "runtime/*.sock",
    "runtime/artifacts/",
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
    "archive/legacy_root_surfaces/refs/**/logs/**",
    "archive/legacy_root_surfaces/refs/**/data/**",
    "archive/legacy_root_surfaces/refs/**/site/**",
    "archive/legacy_root_surfaces/refs/**/reports/experiment_results/**",
    "archive/legacy_root_surfaces/refs/**/*.pdf",
    "archive/legacy_root_surfaces/refs/**/*.png",
    "archive/legacy_root_surfaces/refs/**/*.jpg",
    "archive/legacy_root_surfaces/refs/**/*.jpeg",
    "archive/legacy_root_surfaces/refs/**/*.zip",
    "archive/legacy_root_surfaces/refs/**/*.html",
    "archive/legacy_root_surfaces/refs/**/*.Rhistory",
    "archive/legacy_root_surfaces/refs/**/.cursorignore",
    "archive/legacy_root_surfaces/refs/**/.cursor/**",
    "data/datasets/raw/",
    "data/datasets/**/raw/",
    "data/datasets/restricted_raw/",
    "data/datasets/deidentified_longitudinal/",
    "data/datasets/standardized_longitudinal/",
    "data/datasets/external/",
    "data/datasets/**/*.csv",
    "data/datasets/**/*.tsv",
    "data/datasets/**/*.xlsx",
    "data/datasets/**/*.xls",
    "data/datasets/**/*.parquet",
    "data/datasets/**/*.pkl",
    "data/datasets/**/*.sqlite",
    "data/datasets/**/*.db",
    "!data/datasets/**/dataset_manifest.yaml",
    "!data/datasets/**/*.md",
    "!data/datasets/**/*.json",
    "registry/raw_snapshots/**",
    "memory/portfolio/data_assets/public/downloads/",
    "memory/portfolio/data_assets/private/diffs/",
    "memory/portfolio/data_assets/private/pruned_releases/",
    "memory/portfolio/**/*.csv",
    "memory/portfolio/**/*.tsv",
    "memory/portfolio/**/*.xlsx",
    "memory/portfolio/**/*.xls",
    "memory/portfolio/**/*.parquet",
    "memory/portfolio/**/*.pkl",
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

QUEST_LOCAL_GIT_RETIREMENT_POLICY = {
    "status": "retired",
    "daily_lifecycle": False,
    "compatibility_scope": ["legacy_import", "restore"],
}


def is_workspace_gitignore_path(path: Path) -> bool:
    return path.name == ".gitignore"


def render_workspace_gitignore() -> str:
    return (
        "# MedAutoScience workspace-local Git boundary.\n"
        "# OPL current-control-state owns runtime lifecycle; MAS keeps domain refs and legacy quest roots ignored for provenance.\n"
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
        "quest_local_git_policy": dict(QUEST_LOCAL_GIT_RETIREMENT_POLICY),
    }


def workspace_git_plan(*, workspace_root: Path, initialize_git: bool, dry_run: bool) -> dict[str, object]:
    already_initialized = (workspace_root / ".git").exists()
    return _workspace_git_payload(
        workspace_root=workspace_root,
        enabled=bool(initialize_git or already_initialized),
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
    if already_initialized:
        configure_existing_workspace_git(workspace_root=workspace_root)
        return _workspace_git_payload(
            workspace_root=workspace_root,
            enabled=True,
            initialized=False,
            already_initialized=True,
            would_initialize=False,
        )
    if not initialize_git:
        return _workspace_git_payload(
            workspace_root=workspace_root,
            enabled=False,
            initialized=False,
            already_initialized=False,
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
