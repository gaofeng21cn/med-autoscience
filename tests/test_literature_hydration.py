from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def test_literature_hydration_exports_records_bib_and_coverage_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    quest_root.mkdir(parents=True, exist_ok=True)

    report = module.run_literature_hydration(
        quest_root=quest_root,
        records=[
            {
                "record_id": "pmid:12345",
                "title": "Prediction model paper",
                "authors": ["A. Author"],
                "year": 2024,
                "journal": "BMC Medicine",
                "doi": "10.1000/example",
                "pmid": "12345",
                "pmcid": None,
                "arxiv_id": None,
                "abstract": "Structured abstract",
                "full_text_availability": "abstract_only",
                "source_priority": 2,
                "citation_payload": {"journal": "BMC Medicine"},
                "local_asset_paths": [],
                "relevance_role": "anchor",
                "claim_support_scope": ["primary_claim"],
            }
        ],
    )

    records_path = quest_root / "literature" / "pubmed" / "records.jsonl"
    references_bib_path = quest_root / "paper" / "references.bib"
    coverage_path = quest_root / "paper" / "reference_coverage_report.json"

    assert records_path.exists()
    assert references_bib_path.exists()
    assert coverage_path.exists()
    assert report["record_count"] == 1
    assert report["records_path"] == str(records_path)
    assert report["references_bib_path"] == str(references_bib_path)
    assert report["coverage_report_path"] == str(coverage_path)

    records_payload = records_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(records_payload) == 1
    assert json.loads(records_payload[0])["record_id"] == "pmid:12345"

    bib_text = references_bib_path.read_text(encoding="utf-8")
    assert "@article{pmid_12345," in bib_text
    assert "title = {Prediction model paper}" in bib_text
    assert "doi = {10.1000/example}" in bib_text

    coverage_payload = json.loads(coverage_path.read_text(encoding="utf-8"))
    assert coverage_payload["record_count"] == 1
    assert coverage_payload["records_with_doi"] == 1
    assert coverage_payload["records_with_pmid"] == 1


def test_literature_hydration_rejects_invalid_record_schema(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"

    with pytest.raises(ValueError, match="authors"):
        module.run_literature_hydration(
            quest_root=quest_root,
            records=[
                {
                    "record_id": "pmid:12345",
                    "title": "Prediction model paper",
                    "authors": "A. Author",
                    "year": 2024,
                    "journal": "BMC Medicine",
                    "doi": "10.1000/example",
                    "pmid": "12345",
                    "pmcid": None,
                    "arxiv_id": None,
                    "abstract": "Structured abstract",
                    "full_text_availability": "abstract_only",
                    "source_priority": 2,
                    "citation_payload": {"journal": "BMC Medicine"},
                    "local_asset_paths": [],
                    "relevance_role": "anchor",
                    "claim_support_scope": ["primary_claim"],
                }
            ],
        )
