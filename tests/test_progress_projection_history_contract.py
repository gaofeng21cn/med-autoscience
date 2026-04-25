from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_progress_projection_history_contract_separates_summary_and_detail_layers() -> None:
    doc = (REPO_ROOT / "docs/runtime/progress_projection_history_contract.md").read_text(encoding="utf-8")
    assert "Summary layer" in doc
    assert "Detail layer" in doc
    assert "Admin ops layer" in doc
    assert "heavy detail load 不得阻塞 current blocker 和 next action" in doc
    assert "前台先给可行动真相，细节按需展开" in doc
