from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


BANNED_DIRECTORY_NAMES = frozenset(
    {
        "ops",
        "build",
        "dist",
        "tmp",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
    }
)
BANNED_FILE_NAMES = frozenset({".DS_Store"})
BANNED_SUFFIXES = (".egg-info",)
ALLOWED_ROOT_DIRECTORIES = frozenset({".git", ".worktrees"})
ALLOWED_ROOT_FILES = frozenset({"RTK.md"})
ACTIVE_SURFACE_ROOTS = (
    "src/",
    "tests/",
    "contracts/",
    "profiles/",
    "agent/",
    "runtime/authority_functions/",
)
ACTIVE_PATH_DENYLIST = (
    (
        re.compile(r"(^|/)(dhd|domain[-_]health[-_]diagnostic)(/|\.|_|-|$)", re.I),
        "retired_dhd_active_path",
    ),
    (
        re.compile(r"(^|/)owner[-_]route[-_]reconcile(/|\.|_|-|$)", re.I),
        "retired_owner_route_reconcile_active_path",
    ),
    (
        re.compile(r"(^|/)domain[-_]owner[-_]action[-_]dispatch(/|\.|_|-|$)", re.I),
        "retired_domain_owner_action_dispatch_active_path",
    ),
    (
        re.compile(r"(^|/)default[-_]executor(/|\.|_|-|$)", re.I),
        "retired_default_executor_active_path",
    ),
    (
        re.compile(r"(^|/)progress[-_]portal(/|\.|_|-|$)", re.I),
        "retired_progress_portal_active_path",
    ),
    (
        re.compile(r"(^|/)runtime[-_]storage[-_]maintenance(/|\.|_|-|$)", re.I),
        "retired_runtime_storage_maintenance_active_path",
    ),
    (
        re.compile(r"(^|/)sqlite[-_]sidecars?(/|\.|_|-|$)", re.I),
        "retired_sqlite_sidecars_active_path",
    ),
    (
        re.compile(
            r"(^|/)(local[-_]launchd[-_]scheduler|workspace[-_]local[-_]scheduler|"
            r"mas[-_]supervision[-_]scheduler|supervision[-_]scheduler|"
            r"mas[-_]default[-_]generic[-_]scheduler|mas[-_]owned[-_]generic[-_]scheduler|"
            r"mas[-_]runtime[-_]scheduler|scheduler[-_]owner.*(mas|med[-_]autoscience|local|workspace)|"
            r"(mas|med[-_]autoscience|local|workspace).*scheduler[-_]owner)(/|\.|_|-|$)",
            re.I,
        ),
        "retired_mas_local_scheduler_active_path",
    ),
)
ENTRYPOINT_PATHS = frozenset(
    {
        "src/med_autoscience/mcp_server/__init__.py",
        "src/med_autoscience/cli/__init__.py",
        "src/med_autoscience/cli/parser.py",
    }
)
ENTRYPOINT_TOKEN_DENYLIST = {
    "domain-health-diagnostic": "retired_domain_health_diagnostic_entrypoint",
    "domain-owner-action-dispatch": "retired_domain_owner_action_dispatch_entrypoint",
    "owner-route-reconcile": "retired_owner_route_reconcile_entrypoint",
    "default-executor": "retired_default_executor_entrypoint",
    "progress-portal": "retired_progress_portal_entrypoint",
}


def _default_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=True,
    )
    return Path(result.stdout.strip()).resolve()


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_banned_directory(name: str) -> bool:
    return name in BANNED_DIRECTORY_NAMES or name.endswith(BANNED_SUFFIXES)


def _is_banned_file(name: str) -> bool:
    return name in BANNED_FILE_NAMES or name.endswith(BANNED_SUFFIXES)


def audit_filesystem(root: Path) -> list[str]:
    violations: list[str] = []

    for current_root, dirnames, filenames in os.walk(root, topdown=True):
        current_path = Path(current_root)
        is_repo_root = current_path == root
        kept_dirnames: list[str] = []

        for dirname in sorted(dirnames):
            directory_path = current_path / dirname
            if is_repo_root and dirname in ALLOWED_ROOT_DIRECTORIES:
                continue
            if _is_banned_directory(dirname):
                violations.append(_relative(directory_path, root))
                continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for filename in sorted(filenames):
            if is_repo_root and filename in ALLOWED_ROOT_FILES:
                continue
            file_path = current_path / filename
            if _is_banned_file(filename):
                violations.append(_relative(file_path, root))

    return violations


def audit_tracked_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=True,
        capture_output=True,
        check=True,
    )
    violations: list[str] = []
    for raw_path in result.stdout.split("\0"):
        if not raw_path:
            continue
        parts = Path(raw_path).parts
        if not parts:
            continue
        if parts[0] in ALLOWED_ROOT_DIRECTORIES:
            continue
        if any(_is_banned_directory(part) for part in parts[:-1]):
            violations.append(raw_path)
            continue
        if _is_banned_file(parts[-1]):
            violations.append(raw_path)
    return violations


def audit_active_surface_residue(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=True,
        capture_output=True,
        check=True,
    )
    violations: list[str] = []
    entrypoint_paths = ENTRYPOINT_PATHS | _discover_entrypoint_paths(root)
    for raw_path in result.stdout.split("\0"):
        if not raw_path:
            continue
        if not raw_path.startswith(ACTIVE_SURFACE_ROOTS):
            continue
        for pattern, reason in ACTIVE_PATH_DENYLIST:
            if pattern.search(raw_path):
                violations.append(f"{raw_path}: {reason}")
                break
        if raw_path in entrypoint_paths:
            path = root / raw_path
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for token, reason in ENTRYPOINT_TOKEN_DENYLIST.items():
                if token in text:
                    violations.append(f"{raw_path}: {reason}")
    return violations


def _discover_entrypoint_paths(root: Path) -> frozenset[str]:
    cli_root = root / "src" / "med_autoscience"
    if not cli_root.is_dir():
        return frozenset()
    return frozenset(
        _relative(path, root)
        for path in cli_root.rglob("parser.py")
        if path.is_file()
    )


def cleanup_ignored_artifacts(root: Path) -> list[str]:
    removed: list[str] = []

    for current_root, dirnames, filenames in os.walk(root, topdown=True):
        current_path = Path(current_root)
        is_repo_root = current_path == root
        kept_dirnames: list[str] = []

        for dirname in sorted(dirnames):
            directory_path = current_path / dirname
            if is_repo_root and dirname in ALLOWED_ROOT_DIRECTORIES:
                continue
            if _is_banned_directory(dirname):
                relative_path = _relative(directory_path, root)
                if _is_git_ignored(root, relative_path):
                    _remove_path(directory_path)
                    removed.append(relative_path)
                    continue
            kept_dirnames.append(dirname)
        dirnames[:] = kept_dirnames

        for filename in sorted(filenames):
            if is_repo_root and filename in ALLOWED_ROOT_FILES:
                continue
            file_path = current_path / filename
            if _is_banned_file(filename):
                relative_path = _relative(file_path, root)
                if _is_git_ignored(root, relative_path):
                    _remove_path(file_path)
                    removed.append(relative_path)

    return removed


def _is_git_ignored(root: Path, relative_path: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", relative_path],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def _remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        for child in path.iterdir():
            _remove_path(child)
        try:
            path.rmdir()
        except FileNotFoundError:
            return
        return
    path.unlink(missing_ok=True)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit repo-local hygiene artifacts.")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root to audit. Defaults to the current git root.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Remove banned artifacts only when they are already ignored by git.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or []))
    root = (args.root or _default_repo_root()).resolve()
    if not root.is_dir():
        print(f"repo hygiene audit: root is not a directory: {root}", file=sys.stderr)
        return 2

    if args.fix:
        removed = cleanup_ignored_artifacts(root)
        for path in removed:
            print(f"repo hygiene audit removed ignored artifact: {path}")

    violations = sorted(
        set(
            audit_filesystem(root)
            + audit_tracked_paths(root)
            + audit_active_surface_residue(root)
        )
    )
    if violations:
        print(
            "repo hygiene audit failed: banned checkout artifacts or retired active surfaces detected",
            file=sys.stderr,
        )
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    print("repo hygiene audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
