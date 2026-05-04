from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_artifact_inventory_projection_defines_inspectable_workspace_items() -> None:
    doc = (REPO_ROOT / "docs/runtime/artifact_inventory_projection.md").read_text(encoding="utf-8")
    for field in ("artifact_id", "artifact_type", "path", "owner_surface", "freshness_status", "resume_relevance"):
        assert field in doc
    for artifact_type in ("manuscript", "table", "figure", "evidence_ledger", "review_ledger", "publication_eval", "runtime_log", "delivery_package"):
        assert artifact_type in doc
    assert "inventory 是 projection，不是 authority" in doc


def test_delivery_docs_explain_layout_statuses_and_user_handoff_boundaries() -> None:
    inventory_doc = (REPO_ROOT / "docs/runtime/artifact_inventory_projection.md").read_text(encoding="utf-8")
    delivery_doc = (REPO_ROOT / "docs/runtime/delivery_plane_contract_map.md").read_text(encoding="utf-8")
    combined = inventory_doc + "\n" + delivery_doc

    for status in ("v2", "legacy", "unknown"):
        assert status in combined
    for phrase in (
        "打开投稿文件",
        "核查 audit/",
        "核查 reproducibility/",
        "不是 edit source",
    ):
        assert phrase in combined
    assert "delivery/" + "current/" not in combined
