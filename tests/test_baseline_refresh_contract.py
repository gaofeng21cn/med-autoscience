from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_baseline_refresh_contract_requires_explicit_refresh_record() -> None:
    doc = _read("docs/runtime/baseline_refresh_contract.md")
    assert "不能静默覆盖旧结果" in doc
    assert "record_type: baseline_refresh" in doc
    assert "previous_baseline_ref" in doc
    assert "refreshed_baseline_ref" in doc
    assert "affected_surfaces" in doc
    assert "return_to_baseline" in doc


def test_baseline_overlay_points_to_refresh_contract() -> None:
    template = _read("src/med_autoscience/overlay/templates/medical-research-baseline.block.md")
    assert "Baseline refresh discipline" in template
    assert "Do not silently overwrite baseline truth" in template
    assert "docs/runtime/baseline_refresh_contract.md" in template
