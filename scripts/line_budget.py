#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from med_autoscience.controllers.boundary_fitness import (  # noqa: E402
    DEFAULT_BASELINE,
    PREFERRED_LINE_LIMIT,
    audit_boundary_fitness,
)


DEFAULT_LIMIT = PREFERRED_LINE_LIMIT
BASELINE = DEFAULT_BASELINE


def main() -> int:
    parser = argparse.ArgumentParser(description='Enforce the tracked code line budget.')
    parser.add_argument('--list', action='store_true', help='list tracked code files over the default budget')
    args = parser.parse_args()

    report = audit_boundary_fitness(REPO_ROOT, baseline=BASELINE)
    if args.list:
        for finding in report.oversized_findings:
            print(f"{finding.line_count:6d} {finding.path}")
        return 0

    failures = report.blocking_findings
    if failures:
        print(f'line budget check failed ({len(failures)} issue{"s" if len(failures) != 1 else ""}):')
        for failure in failures:
            print(f'- {failure.path}: {failure.message}; {failure.recommendation}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
