from dataclasses import asdict
import importlib
import re

from tests.submission_minimal_cases.shared import *

from med_autoscience.literature_records import LiteratureRecord
from med_autoscience.controllers.submission_minimal.package_builder import (
    create_submission_minimal_package,
)


def test_create_submission_minimal_package_materializes_references_and_pending_front_matter(
    tmp_path: Path,
) -> None:
    paper_root = make_current_draft_workspace(tmp_path)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    copied_references_path = submission_root / "references.bib"
    assert copied_references_path.exists()
    assert copied_references_path.read_text(encoding="utf-8") == (
        paper_root / "references.bib"
    ).read_text(encoding="utf-8")

    assert manifest["references"] == {
        "source_path": "paper/references.bib",
        "source_kind": "paper_references",
        "output_path": "paper/submission_minimal/references.bib",
        "entry_count": 1,
        "coverage": {
            "status": "complete",
            "citation_key_count": 1,
            "missing_citation_keys": [],
        },
    }
    assert manifest["front_matter_placeholders"] == {
        "authors": "pending",
        "affiliations": "pending",
        "corresponding_author": "pending",
        "funding": "pending",
        "conflict_of_interest": "pending",
        "ethics": "pending",
        "data_availability": "pending",
        "analytic_data_lock_date": "pending",
        "registry_enrollment_period": "pending",
    }


def test_create_submission_minimal_package_uses_workspace_literature_references_when_paper_refs_missing(
    tmp_path: Path,
) -> None:
    paper_root = make_current_draft_workspace(tmp_path)
    workspace_root = paper_root.parent
    (paper_root / "references.bib").unlink()
    workspace_references_path = workspace_root / "memory" / "portfolio" / "research_memory" / "literature" / "references.bib"
    write_text(
        workspace_references_path,
        """@article{ref1,
  title={A workspace primary source},
  author={Author, A. and Author, B.},
  journal={Journal},
  year={2024}
}
""",
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    submission_markdown = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    copied_references_path = submission_root / "references.bib"
    assert "bibliography: references.bib" in submission_markdown
    assert copied_references_path.read_text(encoding="utf-8") == workspace_references_path.read_text(
        encoding="utf-8"
    )
    assert manifest["references"]["source_path"] == "memory/portfolio/research_memory/literature/references.bib"
    assert manifest["references"]["source_kind"] == "workspace_literature"
    assert manifest["references"]["coverage"] == {
        "status": "complete",
        "citation_key_count": 1,
        "missing_citation_keys": [],
    }


def test_general_medical_submission_renders_bibliography_when_refs_exist_without_inline_citations(
    tmp_path: Path,
) -> None:
    paper_root = make_manuscript_shaped_draft_workspace(tmp_path)
    draft_text = (paper_root / "draft.md").read_text(encoding="utf-8")
    write_text(
        paper_root / "draft.md",
        re.sub(r"\s*\[@ref1\]", "", draft_text),
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(
        encoding="utf-8"
    )
    assert "bibliography: references.bib" in submission_markdown
    assert "nocite: '@*'" in submission_markdown
    assert "\n# References\n" in submission_markdown
    assert manifest["references"]["coverage"] == {
        "status": "nocite_all",
        "citation_key_count": 0,
        "bib_entry_count": 1,
        "missing_citation_keys": [],
        "rendered_bibliography_policy": "pandoc_nocite_all",
    }


def test_create_submission_minimal_package_auto_hydrates_missing_pubmed_references(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    shared_base = importlib.import_module("med_autoscience.controllers.submission_minimal.shared_base")
    paper_root = make_current_draft_workspace(tmp_path)
    write_text(
        paper_root / "draft.md",
        (paper_root / "draft.md").read_text(encoding="utf-8").replace("[@ref1]", "[@pmid_12345]"),
    )
    write_text(paper_root / "references.bib", "")
    fetched_record = LiteratureRecord(
        record_id="pmid:12345",
        title="PubMed hydrated evidence",
        authors=("A. Author",),
        year=2025,
        journal="Lancet",
        doi="10.1000/pubmed",
        pmid="12345",
        pmcid=None,
        arxiv_id=None,
        abstract=None,
        full_text_availability="abstract_only",
        source_priority=2,
        citation_payload={"source": "test"},
        local_asset_paths=(),
        relevance_role="candidate",
        claim_support_scope=(),
    )
    synced_records: list[dict[str, object]] = []

    monkeypatch.setattr(
        shared_base.pubmed_adapter,
        "fetch_pubmed_summary",
        lambda *, pmids: [fetched_record] if pmids == ["12345"] else [],
    )
    monkeypatch.setattr(
        shared_base.workspace_literature_controller,
        "sync_workspace_literature",
        lambda *, workspace_root, records: synced_records.extend(records) or {"status": "synchronized"},
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    paper_references_text = (paper_root / "references.bib").read_text(encoding="utf-8")
    submission_references_text = (paper_root / "submission_minimal" / "references.bib").read_text(
        encoding="utf-8"
    )
    assert "@article{pmid_12345," in paper_references_text
    assert "title = {PubMed hydrated evidence}" in submission_references_text
    assert manifest["references"]["coverage"]["status"] == "complete"
    assert manifest["references"]["coverage"]["auto_repair"]["status"] == "repaired"
    assert manifest["references"]["coverage"]["auto_repair"]["fetched_pmids"] == ["12345"]
    assert manifest["references"]["coverage"]["auto_repair"]["workspace_literature_sync"] == {
        "status": "synchronized"
    }
    assert synced_records == [asdict(fetched_record)]


def test_create_submission_minimal_package_rejects_unrepairable_missing_reference_keys(
    tmp_path: Path,
) -> None:
    shared_base = importlib.import_module("med_autoscience.controllers.submission_minimal.shared_base")
    paper_root = make_current_draft_workspace(tmp_path)
    write_text(
        paper_root / "draft.md",
        (paper_root / "draft.md").read_text(encoding="utf-8").replace("[@ref1]", "[@missing_key]"),
    )
    write_text(paper_root / "references.bib", "")

    with pytest.raises(shared_base.SubmissionReferenceCoverageError, match="missing_key"):
        create_submission_minimal_package(
            paper_root=paper_root,
            publication_profile="general_medical_journal",
        )
