from __future__ import annotations

import importlib
from pathlib import Path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_resolve_journal_shortlist_controller_returns_absent_when_no_evidence(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.journal_shortlist")
    study_root = tmp_path / "studies" / "001-risk"
    write_text(study_root / "study.yaml", "study_id: 001-risk\n")

    result = module.resolve_journal_shortlist(study_root=study_root)

    assert result["status"] == "absent"
    assert result["candidate_count"] == 0


def test_resolve_journal_shortlist_controller_returns_invalid_for_bad_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.journal_shortlist")
    study_root = tmp_path / "studies" / "001-risk"
    write_text(
        study_root / "study.yaml",
        """study_id: 001-risk
journal_shortlist_evidence:
  - journal_name: Heart
    selection_band: invalid_band
    fit_summary: x
    risk_summary: y
    official_scope_sources:
      - https://example.org
    similar_paper_examples:
      - title: Example
        journal: Heart
        year: 2024
        source_url: https://example.org/paper
        similarity_rationale: Similar.
    tier_snapshot:
      source: manual_snapshot
      retrieved_on: 2026-03-30
      quartile: Q1
    confidence: high
""",
    )

    result = module.resolve_journal_shortlist(study_root=study_root)

    assert result["status"] == "invalid"
    assert "selection_band" in result["errors"][0]


def test_resolve_journal_shortlist_controller_returns_incomplete_for_uncovered_shortlist(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.journal_shortlist")
    study_root = tmp_path / "studies" / "001-risk"
    write_text(
        study_root / "study.yaml",
        """study_id: 001-risk
journal_shortlist:
  - Heart
  - Diabetes Research and Clinical Practice
journal_shortlist_evidence:
  - journal_name: Heart
    selection_band: stretch
    fit_summary: Strong cardiovascular story.
    risk_summary: Hard to reach.
    official_scope_sources:
      - https://example.org/heart
    similar_paper_examples:
      - title: Example
        journal: Heart
        year: 2024
        pmid: "123456"
        similarity_rationale: Similar.
    tier_snapshot:
      source: manual_snapshot
      retrieved_on: 2026-03-30
      quartile: Q1
    confidence: medium
""",
    )

    result = module.resolve_journal_shortlist(study_root=study_root)

    assert result["status"] == "incomplete"
    assert result["uncovered_shortlist_entries"] == ["Diabetes Research and Clinical Practice"]
