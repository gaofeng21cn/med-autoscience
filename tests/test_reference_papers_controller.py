from __future__ import annotations

import importlib
from pathlib import Path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_resolve_reference_papers_controller_returns_audit_summary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.reference_papers")
    quest_root = tmp_path / "workspace" / "ops" / "deepscientist" / "runtime" / "quests" / "002-early-risk"
    write_text(
        quest_root / "quest.yaml",
        """quest_id: 002-early-risk
startup_contract:
  reference_papers:
    - id: smith2024
      title: A mature classifier paper
      pmid: "12345678"
      role: anchor_paper
      borrow_contract:
        - evaluation package
        - discussion structure
""",
    )

    result = module.resolve_reference_papers(quest_root=quest_root)

    assert result["status"] == "resolved"
    assert result["quest_root"] == str(quest_root)
    assert result["paper_count"] == 1
    assert result["stage_requirements"] == {
        "scout": "required",
        "idea": "required",
        "write": "advisory",
    }
    assert result["papers"][0]["source_kind"] == "pmid"
    assert result["papers"][0]["role"] == "anchor_paper"
