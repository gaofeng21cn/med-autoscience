#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
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
    parser = argparse.ArgumentParser(description='Report tracked code files over the preferred line budget.')
    parser.add_argument('--list', action='store_true', help='list tracked code files over the default budget')
    parser.add_argument('--strict', action='store_true', help='exit non-zero when tracked code exceeds the budget')
    args = parser.parse_args()

    report = audit_boundary_fitness(REPO_ROOT, baseline=BASELINE)
    if args.list:
        for finding in report.oversized_findings:
            print(f"{finding.line_count:6d} {finding.path}")
        return 0

    failures = report.blocking_findings
    if failures:
        strict = args.strict or os.environ.get('MAS_LINE_BUDGET_STRICT') == '1'
        mode = 'failed' if strict else 'advisory found'
        print(f'line budget {mode} {len(failures)} issue{"s" if len(failures) != 1 else ""}:')
        for failure in failures:
            print(f'- {failure.path}: {failure.message}; {failure.recommendation}')
        if strict:
            return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
