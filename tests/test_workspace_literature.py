from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def _record(*, record_id: str, title: str, doi: str, pmid: str | None = None) -> dict[str, object]:
    return {
        "record_id": record_id,
        "title": title,
        "authors": ["A. Author"],
        "year": 2024,
        "journal": "BMC Medicine",
        "doi": doi,
        "pmid": pmid,
        "pmcid": None,
        "arxiv_id": None,
        "abstract": "Structured abstract",
        "full_text_availability": "metadata_only",
        "source_priority": 3,
        "citation_payload": {"doi": doi},
        "local_asset_paths": [],
        "relevance_role": "anchor_paper",
        "claim_support_scope": ["paper_framing"],
    }


def test_init_workspace_literature_creates_canonical_scaffold_and_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_literature")
    workspace_root = tmp_path / "workspace"

    result = module.init_workspace_literature(workspace_root=workspace_root)

    literature_root = workspace_root / "portfolio" / "research_memory" / "literature"
    registry_path = literature_root / "registry.jsonl"
    bibliography_path = literature_root / "references.bib"
    coverage_path = literature_root / "coverage" / "latest.json"

    assert result["workspace_literature_root"] == str(literature_root)
    assert registry_path.is_file()
    assert bibliography_path.is_file()
    assert coverage_path.is_file()

    coverage_payload = json.loads(coverage_path.read_text(encoding="utf-8"))
    assert coverage_payload["record_count"] == 0
    assert coverage_payload["records_with_doi"] == 0

    status = module.workspace_literature_status(workspace_root=workspace_root)

    assert status["workspace_literature_exists"] is True
    assert status["workspace_literature_root"] == str(literature_root)
    assert status["registry_path"] == str(registry_path)
    assert status["references_bib_path"] == str(bibliography_path)
    assert status["coverage_report_path"] == str(coverage_path)
    assert status["record_count"] == 0
    assert status["references_bib_entry_count"] == 0


def test_sync_workspace_literature_dedupes_same_identifier_into_canonical_registry(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_literature")
    workspace_root = tmp_path / "workspace"

    result = module.sync_workspace_literature(
        workspace_root=workspace_root,
        records=[
            _record(record_id="seed-anchor", title="Prediction model paper", doi="10.1000/example"),
            _record(record_id="dup-anchor", title="Prediction model paper", doi="10.1000/example"),
        ],
    )

    registry_path = workspace_root / "portfolio" / "research_memory" / "literature" / "registry.jsonl"
    bibliography_path = workspace_root / "portfolio" / "research_memory" / "literature" / "references.bib"
    coverage_path = workspace_root / "portfolio" / "research_memory" / "literature" / "coverage" / "latest.json"
    registry_lines = [line for line in registry_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert result["record_count"] == 1
    assert len(registry_lines) == 1
    assert json.loads(registry_lines[0])["relevance_role"] == "canonical_reference"
    assert bibliography_path.read_text(encoding="utf-8").count("@article{") == 1
    assert json.loads(coverage_path.read_text(encoding="utf-8"))["record_count"] == 1


def test_sync_workspace_literature_rejects_conflicting_records_for_same_canonical_identity(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_literature")
    workspace_root = tmp_path / "workspace"

    with pytest.raises(ValueError, match="conflicting canonical literature record"):
        module.sync_workspace_literature(
            workspace_root=workspace_root,
            records=[
                _record(record_id="seed-anchor", title="Prediction model paper", doi="10.1000/example"),
                _record(record_id="dup-anchor", title="Different paper title", doi="10.1000/example"),
            ],
        )
