#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

DEFAULT_LIMIT = 1000
BASELINE = {
    'src/med_autoscience/controllers/runtime_watch.py': 1499,
    'src/med_autoscience/cli.py': 1475,
    'src/med_autoscience/controllers/study_outer_loop.py': 1410,
    'src/med_autoscience/controllers/gate_clearing_batch.py': 1363,
    'src/med_autoscience/controllers/study_runtime_execution.py': 1346,
    'src/med_autoscience/controllers/mainline_status.py': 1301,
    'src/med_autoscience/controllers/product_entry_parts/workspace_surfaces.py': 1292,
    'tests/product_entry_cases/chunk_02.py': 1289,
    'tests/product_entry_cases/chunk_04.py': 1265,
    'src/med_autoscience/controllers/workspace_init.py': 1186,
    'tests/product_entry_cases/chunk_05.py': 1180,
    'src/med_autoscience/controllers/study_progress_parts/projection.py': 1155,
    'src/med_autoscience/runtime_transport/med_deepscientist.py': 1146,
    'src/med_autoscience/controllers/product_entry_parts/manifest_surfaces.py': 1122,
    'src/med_autoscience/controllers/time_to_event_direct_migration.py': 1094,
    'tests/study_progress_cases/chunk_05.py': 1075,
    'src/med_autoscience/controllers/product_entry_parts/shared_base.py': 1020,
}
CODE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', '.mts', '.cts', '.sh', '.bash', '.zsh', '.rs', '.go'
}
IGNORED_PARTS = {'node_modules', 'dist', 'build', 'coverage', '.venv', '__pycache__'}
IGNORED_SUFFIXES = ('.min.js',)


def main() -> int:
    parser = argparse.ArgumentParser(description='Enforce the tracked code line budget.')
    parser.add_argument('--list', action='store_true', help='list tracked code files over the default budget')
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    tracked_files = subprocess.run(
        ['git', 'ls-files'], cwd=repo_root, check=True, text=True, stdout=subprocess.PIPE
    ).stdout.splitlines()

    oversize: list[tuple[str, int]] = []
    failures: list[str] = []
    for relative_path in tracked_files:
        if not is_code_file(relative_path):
            continue
        absolute_path = repo_root / relative_path
        if not absolute_path.is_file():
            continue
        line_count = count_lines(absolute_path)
        if line_count <= DEFAULT_LIMIT:
            continue
        oversize.append((relative_path, line_count))
        allowed = BASELINE.get(relative_path)
        if allowed is None:
            failures.append(
                f'{relative_path}: {line_count} lines exceeds {DEFAULT_LIMIT} line budget; '
                'split into focused modules or add an explicit reviewed baseline'
            )
        elif line_count > allowed:
            failures.append(
                f'{relative_path}: {line_count} lines exceeds locked baseline {allowed}; split before growing this file'
            )

    oversize.sort(key=lambda item: (-item[1], item[0]))
    if args.list:
        for relative_path, line_count in oversize:
            print(f'{line_count:6d} {relative_path}')
        return 0

    for relative_path in BASELINE:
        if not (repo_root / relative_path).exists():
            failures.append(f'{relative_path}: stale line-budget baseline entry; remove it after deleting or renaming the file')

    if failures:
        print(f'line budget check failed ({len(failures)} issue{"s" if len(failures) != 1 else ""}):')
        for failure in failures:
            print(f'- {failure}')
        return 1
    return 0


def is_code_file(relative_path: str) -> bool:
    path = Path(relative_path)
    if any(part in IGNORED_PARTS for part in path.parts):
        return False
    if relative_path.endswith(IGNORED_SUFFIXES):
        return False
    return path.suffix in CODE_EXTENSIONS


def count_lines(path: Path) -> int:
    content = path.read_text(encoding='utf-8')
    if not content:
        return 0
    return len(content.splitlines())


if __name__ == '__main__':
    raise SystemExit(main())
