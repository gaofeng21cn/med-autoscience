from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_bounded_analysis_frontier_policy_defines_candidate_board() -> None:
    doc = (REPO_ROOT / "docs/policies/bounded_analysis_frontier_policy.md").read_text(encoding="utf-8")
    for term in ("explore", "exploit", "fusion", "debug", "stop"):
        assert term in doc
    for field in ("target_claim_or_concern", "expected_evidence_gain", "clinical_interpretability", "decision_reason"):
        assert field in doc
    assert "不能变成无限分析扩张" in doc
    assert "Plateau 规则" in doc
