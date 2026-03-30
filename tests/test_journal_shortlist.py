from __future__ import annotations

import importlib
from pathlib import Path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_resolve_journal_shortlist_contract_accepts_evidence_backed_shortlist(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.journal_shortlist")
    study_root = tmp_path / "studies" / "001-risk"
    write_text(
        study_root / "study.yaml",
        """study_id: 001-risk
journal_shortlist:
  - Diabetes Research and Clinical Practice
journal_shortlist_evidence:
  - journal_name: Diabetes Research and Clinical Practice
    selection_band: primary_fit
    fit_summary: Strong diabetes clinical prediction fit.
    risk_summary: Still requires a full evidence package.
    official_scope_sources:
      - https://example.org/drcp/scope
    similar_paper_examples:
      - title: Example mortality paper
        journal: Diabetes Research and Clinical Practice
        year: 2024
        source_url: https://example.org/paper
        similarity_rationale: Same diabetes mortality prediction surface.
    tier_snapshot:
      source: manual_snapshot
      retrieved_on: 2026-03-30
      quartile: Q1
    confidence: high
""",
    )

    contract = module.resolve_journal_shortlist_contract(study_root=study_root)

    assert contract is not None
    assert contract.ready is True
    assert contract.shortlist == ("Diabetes Research and Clinical Practice",)
    assert contract.candidate_count == 1
    assert contract.uncovered_shortlist_entries == ()


def test_resolve_journal_shortlist_contract_detects_uncovered_entries(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.journal_shortlist")
    study_root = tmp_path / "studies" / "001-risk"
    write_text(
        study_root / "study.yaml",
        """study_id: 001-risk
journal_shortlist:
  - Diabetes Research and Clinical Practice
  - Heart
journal_shortlist_evidence:
  - journal_name: Diabetes Research and Clinical Practice
    selection_band: primary_fit
    fit_summary: Strong diabetes clinical prediction fit.
    risk_summary: Still requires a full evidence package.
    official_scope_sources:
      - https://example.org/drcp/scope
    similar_paper_examples:
      - title: Example mortality paper
        journal: Diabetes Research and Clinical Practice
        year: 2024
        source_url: https://example.org/paper
        similarity_rationale: Same diabetes mortality prediction surface.
    tier_snapshot:
      source: manual_snapshot
      retrieved_on: 2026-03-30
      quartile: Q1
    confidence: high
""",
    )

    contract = module.resolve_journal_shortlist_contract(study_root=study_root)

    assert contract is not None
    assert contract.ready is False
    assert contract.uncovered_shortlist_entries == ("Heart",)


def test_resolve_journal_shortlist_contract_requires_tier_signal(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.journal_shortlist")
    study_root = tmp_path / "studies" / "001-risk"
    write_text(
        study_root / "study.yaml",
        """study_id: 001-risk
journal_shortlist_evidence:
  - journal_name: Diabetes Research and Clinical Practice
    selection_band: primary_fit
    fit_summary: Strong diabetes clinical prediction fit.
    risk_summary: Still requires a full evidence package.
    official_scope_sources:
      - https://example.org/drcp/scope
    similar_paper_examples:
      - title: Example mortality paper
        journal: Diabetes Research and Clinical Practice
        year: 2024
        source_url: https://example.org/paper
        similarity_rationale: Same diabetes mortality prediction surface.
    tier_snapshot:
      source: manual_snapshot
      retrieved_on: 2026-03-30
    confidence: high
""",
    )

    try:
        module.resolve_journal_shortlist_contract(study_root=study_root)
    except ValueError as exc:
        assert "tier_snapshot requires at least one of quartile" in str(exc)
    else:
        raise AssertionError("expected ValueError")
