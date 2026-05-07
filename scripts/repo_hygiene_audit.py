from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


BANNED_DIRECTORY_NAMES = frozenset(
    {
        "ops",
        "build",
        "dist",
        "tmp",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
    }
)
BANNED_FILE_NAMES = frozenset({".DS_Store"})
BANNED_SUFFIXES = (".egg-info",)
ALLOWED_ROOT_DIRECTORIES = frozenset({".git", ".venv", ".worktrees"})
ALLOWED_ROOT_FILES = frozenset({"RTK.md"})


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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit repo-local hygiene artifacts.")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root to audit. Defaults to the current git root.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or []))
    root = (args.root or _default_repo_root()).resolve()
    if not root.is_dir():
        print(f"repo hygiene audit: root is not a directory: {root}", file=sys.stderr)
        return 2

    violations = sorted(set(audit_filesystem(root) + audit_tracked_paths(root)))
    if violations:
        print("repo hygiene audit failed: banned checkout artifacts detected", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    print("repo hygiene audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
