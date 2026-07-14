#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LIMIT = 1000
CODE_SUFFIXES = frozenset(
    {
        ".py",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".mts",
        ".cts",
        ".sh",
        ".bash",
        ".zsh",
        ".rs",
        ".go",
    }
)
IGNORED_PARTS = frozenset(
    {
        ".git",
        ".codegraph",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "node_modules",
        "dist",
        "build",
        "coverage",
        "__pycache__",
    }
)


def _code_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.rglob("*")
        if path.is_file()
        and path.suffix in CODE_SUFFIXES
        and not any(part in IGNORED_PARTS for part in path.relative_to(REPO_ROOT).parts)
        and not path.name.endswith(".min.js")
    )


def _line_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except UnicodeDecodeError:
        return 0


def _oversized_files() -> list[tuple[Path, int]]:
    return [
        (path, line_count)
        for path in _code_files()
        if (line_count := _line_count(path)) > DEFAULT_LIMIT
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description='Report tracked code files over the preferred line budget.')
    parser.add_argument('--list', action='store_true', help='list tracked code files over the default budget')
    parser.add_argument('--strict', action='store_true', help='compatibility alias; line budget remains advisory')
    args = parser.parse_args()

    oversized = _oversized_files()
    if args.list:
        for path, line_count in oversized:
            print(f"{line_count:6d} {path.relative_to(REPO_ROOT).as_posix()}")
        return 0

    if oversized:
        suffix = "s" if len(oversized) != 1 else ""
        print(f"line budget advisory found {len(oversized)} issue{suffix}:")
        for path, line_count in oversized:
            relative_path = path.relative_to(REPO_ROOT).as_posix()
            print(
                f"- {relative_path}: {line_count} lines exceeds the preferred "
                f"{DEFAULT_LIMIT}-line boundary; split by semantic responsibility"
            )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
