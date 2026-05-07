from __future__ import annotations

import subprocess
from pathlib import Path


def test_retired_entry_status_name_is_absent_from_active_tracked_surfaces() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    forbidden_terms = ("front" + "desk", "product-" + "front" + "desk", "product_" + "front" + "desk")
    allowed_prefixes = (
        "docs/history/",
        "docs/references/plan_completion_ledger.md",
        "tests/test_product_entry_naming_retirement.py",
    )
    tracked = subprocess.check_output(["git", "ls-files"], cwd=repo_root, text=True).splitlines()

    offenders: list[str] = []
    for relative_path in tracked:
        if relative_path.startswith(allowed_prefixes):
            continue
        path = repo_root / relative_path
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(term in relative_path or term in text for term in forbidden_terms):
            offenders.append(relative_path)

    assert offenders == []
