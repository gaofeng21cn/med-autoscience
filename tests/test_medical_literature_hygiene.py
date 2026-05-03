from __future__ import annotations

import importlib
import json
from pathlib import Path


def _dump_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_medical_literature_hygiene_fails_closed_when_evidence_ledger_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_literature_hygiene")
    paper_root = tmp_path / "paper"
    paper_root.mkdir(parents=True)
    (paper_root / "references.bib").write_text("@article{ref1,title={Reference}}\n", encoding="utf-8")

    projection = module.build_medical_literature_hygiene_projection(paper_root=paper_root)

    assert projection["surface"] == "medical_literature_hygiene_projection"
    assert projection["status"] == "blocked"
    assert projection["blockers"] == ["evidence_ledger_missing"]
    assert projection["authority"] == {
        "can_replace_medical_literature_review": False,
        "can_authorize_publication_quality": False,
    }


def test_medical_literature_hygiene_projects_clear_key_and_provenance_coverage(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_literature_hygiene")
    paper_root = tmp_path / "paper"
    (paper_root / "build").mkdir(parents=True)
    (paper_root / "build" / "review_manuscript.md").write_text(
        "Clinical reporting follows the cohort standard [@strobe2021] and cites trial evidence [@pmid_12345].\n",
        encoding="utf-8",
    )
    (paper_root / "references.bib").write_text(
        "\n".join(
            [
                "@article{pmid_12345,",
                "  title = {Trial Evidence},",
                "  doi = {10.1000/trial},",
                "  pmid = {12345},",
                "}",
                "@misc{strobe2021,",
                "  title = {STROBE Statement},",
                "  url = {https://www.strobe-statement.org/},",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _dump_json(
        paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "items": [
                {
                    "citation_key": "pmid_12345",
                    "source_kind": "pubmed",
                    "pmid": "12345",
                    "doi": "10.1000/trial",
                },
                {
                    "citation_key": "strobe2021",
                    "source_kind": "guideline",
                    "guideline_family": "STROBE",
                    "url": "https://www.strobe-statement.org/",
                },
            ],
        },
    )

    projection = module.build_medical_literature_hygiene_projection(paper_root=paper_root)

    assert projection["status"] == "clear"
    assert projection["blockers"] == []
    assert projection["coverage"] == {
        "manuscript_citation_key_count": 2,
        "reference_key_count": 2,
        "ledger_citation_key_count": 2,
        "pubmed_provenance_count": 1,
        "doi_provenance_count": 1,
        "guideline_provenance_count": 1,
    }


def test_medical_literature_hygiene_blocks_key_drift_duplicates_and_unsupported_provenance(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_literature_hygiene")
    paper_root = tmp_path / "paper"
    (paper_root / "build").mkdir(parents=True)
    (paper_root / "build" / "review_manuscript.md").write_text(
        "The draft cites a supported source [@pmid_12345] and a missing source [@missing_key].\n",
        encoding="utf-8",
    )
    (paper_root / "references.bib").write_text(
        "\n".join(
            [
                "@article{pmid_12345,",
                "  title = {First},",
                "}",
                "@article{pmid_12345,",
                "  title = {Duplicate},",
                "}",
                "@article{unused_key,",
                "  title = {Unused},",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _dump_json(
        paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "items": [
                {
                    "citation_key": "pmid_12345",
                    "source_kind": "local_note",
                },
                {
                    "citation_key": "ledger_only",
                    "source_kind": "doi",
                    "doi": "10.1000/ledger-only",
                },
            ],
        },
    )

    projection = module.build_medical_literature_hygiene_projection(paper_root=paper_root)

    assert projection["status"] == "blocked"
    assert projection["blockers"] == [
        "duplicate_citation_keys",
        "citation_key_sync_failed",
        "unsupported_citation_blockers_present",
    ]
    assert projection["duplicate_citation_keys"] == ["pmid_12345"]
    assert projection["citation_key_sync"] == {
        "manuscript_keys_missing_from_references": ["missing_key"],
        "manuscript_keys_missing_from_ledger": ["missing_key"],
        "reference_keys_missing_from_ledger": ["unused_key"],
        "ledger_keys_missing_from_references": ["ledger_only"],
    }
    assert projection["unsupported_citation_blockers"] == [
        {
            "citation_key": "pmid_12345",
            "reason": "missing_pubmed_doi_or_guideline_provenance",
        }
    ]
