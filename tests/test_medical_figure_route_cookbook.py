from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_medical_figure_route_cookbook_covers_core_paper_routes() -> None:
    doc = (REPO_ROOT / "docs/capabilities/medical-display/medical_figure_route_cookbook.md").read_text(encoding="utf-8")
    for route in ("baseline_table", "forest_effect", "kaplan_meier", "calibration_curve", "decision_curve", "shap_summary", "trajectory_panel"):
        assert route in doc
    assert "每条 figure route 都必须声明医学问题" in doc
    assert "上游 AI benchmark 图模板不直接进入 MAS" in doc
