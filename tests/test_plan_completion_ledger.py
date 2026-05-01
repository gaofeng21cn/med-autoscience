from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO_ROOT / "docs" / "program" / "plan_completion_ledger.md"


def test_plan_completion_ledger_tracks_required_closeout_fields() -> None:
    text = LEDGER_PATH.read_text(encoding="utf-8")

    for field in (
        "planned",
        "implemented",
        "verified",
        "pushed",
        "cleaned",
        "live_validated",
        "superseded",
        "blocked",
    ):
        assert f"| {field} |" in text or f"| {field} " in text


def test_plan_completion_ledger_keeps_upstream_prs_pending_until_review_closes() -> None:
    text = LEDGER_PATH.read_text(encoding="utf-8")

    for pr_number in ("#65", "#66", "#67"):
        assert f"| {pr_number} |" in text
        assert "merged_upstream" in text
    for pr_number in ("#71", "#72", "#73", "#74"):
        assert f"| {pr_number} |" in text
    upstream_rows = [line for line in text.splitlines() if line.startswith("| #")]
    assert sum("opened_pending_upstream_review" in line for line in upstream_rows) == 4
    assert "open upstream PR 只能记录为 `opened_pending_upstream_review`" in text
