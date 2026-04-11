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


def test_literature_hydration_preserves_existing_materialized_surface_when_payload_is_empty(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    worktree_root = quest_root / ".ds" / "worktrees" / "paper-main"
    (worktree_root / "paper").mkdir(parents=True, exist_ok=True)
    (worktree_root / "literature" / "pubmed").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)
    (quest_root / "literature" / "pubmed").mkdir(parents=True, exist_ok=True)

    worktree_records = [
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
        },
        {
            "record_id": "pmid:67890",
            "title": "Calibration paper",
            "authors": ["B. Author"],
            "year": 2025,
            "journal": "Heart",
            "doi": "10.1000/example-2",
            "pmid": "67890",
            "pmcid": None,
            "arxiv_id": None,
            "abstract": "Structured abstract",
            "full_text_availability": "abstract_only",
            "source_priority": 2,
            "citation_payload": {"journal": "Heart"},
            "local_asset_paths": [],
            "relevance_role": "anchor",
            "claim_support_scope": ["primary_claim"],
        },
    ]
    worktree_report = module.run_literature_hydration(
        quest_root=worktree_root,
        records=worktree_records,
    )
    assert worktree_report["record_count"] == 2

    (quest_root / "paper" / "references.bib").write_text("", encoding="utf-8")
    (quest_root / "literature" / "pubmed" / "records.jsonl").write_text("", encoding="utf-8")

    report = module.run_literature_hydration(
        quest_root=quest_root,
        records=[],
    )

    records_path = quest_root / "literature" / "pubmed" / "records.jsonl"
    references_bib_path = quest_root / "paper" / "references.bib"

    assert report["record_count"] == 2
    assert report["source_mode"] == "preserved_existing_surface"
    assert len(records_path.read_text(encoding="utf-8").strip().splitlines()) == 2
    assert references_bib_path.read_text(encoding="utf-8").count("@article{") == 2


def test_literature_hydration_uses_study_reference_context_and_clears_stale_surface_when_selection_is_empty(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.literature_hydration")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)
    (quest_root / "literature" / "pubmed").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "references.bib").write_text("@article{stale,\n}\n", encoding="utf-8")
    (quest_root / "literature" / "pubmed" / "records.jsonl").write_text(
        json.dumps({"record_id": "stale:1"}) + "\n",
        encoding="utf-8",
    )

    report = module.run_literature_hydration(
        quest_root=quest_root,
        records=[],
        workspace_literature={
            "registry_path": str(tmp_path / "workspace" / "portfolio" / "research_memory" / "literature" / "registry.jsonl")
        },
        study_reference_context={
            "workspace_registry_path": str(
                tmp_path / "workspace" / "portfolio" / "research_memory" / "literature" / "registry.jsonl"
            ),
            "record_count": 0,
            "records": [],
        },
    )

    assert report["record_count"] == 0
    assert report["source_mode"] == "study_reference_context"
    assert (quest_root / "paper" / "references.bib").read_text(encoding="utf-8") == ""
    assert (quest_root / "literature" / "pubmed" / "records.jsonl").read_text(encoding="utf-8") == ""
