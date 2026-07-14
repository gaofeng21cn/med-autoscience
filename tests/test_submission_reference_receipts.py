from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.controllers.submission_minimal.shared_base import (
    SubmissionReferenceProviderReceiptRequired,
    auto_repair_submission_reference_gaps,
    materialize_and_validate_submission_references,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _pubmed_receipt() -> dict[str, object]:
    return {
        "receipt_ref": "opl://connect/references/verify/pubmed-12345",
        "provider_evidence": [
            {
                "reference_id": "pmid:12345",
                "provider": "pubmed",
                "lookup_status": "found",
                "status": "matched",
                "match_status": "identifier_matched",
                "matched_identifiers": {"pmid": "12345"},
                "metadata": {
                    "title": "Receipt-backed paper",
                    "authors": [{"given": "Ada", "family": "Lovelace"}],
                    "journal": "BMC Medicine",
                    "year": 2024,
                },
            }
        ],
    }


def test_submission_reference_gap_without_receipt_is_request_only(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = workspace_root / "studies" / "study-001" / "paper"
    source_markdown_path = paper_root / "manuscript.md"
    _write(source_markdown_path, "Evidence-backed claim [@pmid_12345].\n")

    report = auto_repair_submission_reference_gaps(
        paper_root=paper_root,
        workspace_root=workspace_root,
        source_markdown_path=source_markdown_path,
        references_path=None,
    )

    assert report["status"] == "request_only"
    assert report["requested_pmids"] == ["12345"]
    assert report["unresolved_citation_keys"] == ["pmid_12345"]
    assert report["provider_receipt_refs"] == []
    assert report["provider_resolution_request"] == {
        "action_id": "opl_connect_reference_verification",
        "request_only": True,
        "references": [{"id": "pmid:12345", "pmid": "12345"}],
        "providers": ["pubmed"],
        "identifier_provider": "pubmed",
    }
    assert not (paper_root / "references.bib").exists()


def test_submission_materialization_surfaces_missing_receipt_as_typed_request(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = workspace_root / "studies" / "study-001" / "paper"
    submission_root = paper_root / ".submission-staging"
    source_markdown_path = paper_root / "manuscript.md"
    _write(source_markdown_path, "Evidence-backed claim [@pmid_12345].\n")
    submission_root.mkdir(parents=True)

    with pytest.raises(SubmissionReferenceProviderReceiptRequired) as exc_info:
        materialize_and_validate_submission_references(
            paper_root=paper_root,
            submission_root=submission_root,
            workspace_root=workspace_root,
            source_markdown_path=source_markdown_path,
        )

    error = exc_info.value
    assert error.provider_resolution["status"] == "request_only"
    assert error.provider_resolution["unresolved_citation_keys"] == ["pmid_12345"]
    assert error.provider_resolution_request == {
        "action_id": "opl_connect_reference_verification",
        "request_only": True,
        "references": [{"id": "pmid:12345", "pmid": "12345"}],
        "providers": ["pubmed"],
        "identifier_provider": "pubmed",
    }


def test_submission_reference_gap_consumes_receipt_and_materializes_bibtex(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = workspace_root / "studies" / "study-001" / "paper"
    submission_root = paper_root / ".submission-staging"
    source_markdown_path = paper_root / "manuscript.md"
    _write(source_markdown_path, "Evidence-backed claim [@pmid_12345].\n")
    submission_root.mkdir(parents=True)

    references_manifest, references_source_path, coverage = materialize_and_validate_submission_references(
        paper_root=paper_root,
        submission_root=submission_root,
        workspace_root=workspace_root,
        source_markdown_path=source_markdown_path,
        provider_receipts=(_pubmed_receipt(),),
    )

    assert references_manifest is not None
    assert references_source_path == paper_root / "references.bib"
    assert coverage["status"] == "complete"
    assert coverage["auto_repair"]["status"] == "repaired"
    assert coverage["auto_repair"]["fetched_pmids"] == ["12345"]
    assert coverage["auto_repair"]["workspace_literature_sync"]["status"] == "opl_source_intake_required"
    assert coverage["auto_repair"]["workspace_literature_sync"]["record_count"] == 1
    references_text = (submission_root / "references.bib").read_text(encoding="utf-8")
    assert "@article{pmid_12345," in references_text
    assert "author = {Ada Lovelace}" in references_text
    assert "pmid = {12345}" in references_text
