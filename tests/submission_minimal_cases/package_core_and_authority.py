from .shared import *

import pytest

def test_create_submission_minimal_package_creates_output_directory_and_copies_pdf(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert submission_root.exists()
    assert (submission_root / "paper.pdf").exists()
    assert manifest["output_root"] == "paper/submission_minimal"


def test_create_submission_minimal_package_writes_manifest_and_docx_path(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    manifest_path = submission_root / "submission_manifest.json"
    docx_path = submission_root / "manuscript.docx"

    assert manifest_path.exists()
    assert docx_path.exists()

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_payload["publication_profile"] == "general_medical_journal"
    assert manifest_payload["citation_style"] == "AMA"
    assert manifest_payload["output_root"] == "paper/submission_minimal"
    assert manifest_payload["manuscript"]["pdf_path"] == "paper/submission_minimal/paper.pdf"
    assert manifest_payload["manuscript"]["docx_path"] == "paper/submission_minimal/manuscript.docx"
    assert manifest_payload["naming_map"]["figures"] == {
        "F1": "Figure1",
        "FS1": "SupplementaryFigureS1",
    }
    assert manifest_payload["naming_map"]["tables"] == {
        "T1": "Table1",
    }
    assert manifest_payload["figures"][0]["source_paths"] == [
        "paper/figures/F1_main.pdf",
        "paper/figures/F1_main.png",
    ]
    assert manifest_payload["tables"][0]["source_paths"] == [
        "paper/tables/T1_summary.csv",
        "paper/tables/T1_summary.md",
    ]
    assert manifest_payload == manifest


def test_general_medical_submission_source_alias_is_authority_note_and_appendix_stays_in_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    review_manuscript_path = paper_root / "build" / "review_manuscript.md"
    write_text(
        review_manuscript_path,
        review_manuscript_path.read_text(encoding="utf-8")
        + """

# Appendix: Retained Public Evidence After Screening

The retained MRI dataset is the mapping-pituitary MRI cohort, which contributes 136 total cases.
The retained omics dataset is the GSE169498 transcriptomic series, which preserves a clean invasiveness-labeled biology surface.
""",
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    source_note = (submission_root / "manuscript_source.md").read_text(encoding="utf-8")
    submission_text = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")

    assert manifest["manuscript"]["source_markdown_alias_role"] == "authority_note"
    assert not any(line.lstrip().startswith("#") for line in source_note.splitlines())
    for phrase in (
        "authority note",
        "not the full manuscript",
        "Canonical full manuscript surface",
        "Export-ready submission projection",
        "source signature",
    ):
        assert phrase in source_note
    for study_specific_phrase in (
        "mapping-pituitary",
        "GSE169498",
        "transcriptomic series",
        "invasiveness-labeled biology surface",
    ):
        assert study_specific_phrase not in source_note
        assert study_specific_phrase in submission_text
    assert "# Appendix: Retained Public Evidence After Screening" in submission_text
    surface_qc = manifest["manuscript"]["surface_qc"]
    assert surface_qc["status"] == "pass"
    assert surface_qc["authority_note"]["role_clarity_pass"] is True
    assert surface_qc["authority_note"]["forbidden_study_anchor_hits"] == []


def test_create_submission_minimal_package_preserves_existing_package_when_materialization_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    package_builder = importlib.import_module("med_autoscience.controllers.submission_minimal_parts.package_builder")
    paper_root = make_paper_workspace(tmp_path)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    manifest_path = submission_root / "submission_manifest.json"
    pdf_path = submission_root / "paper.pdf"
    docx_path = submission_root / "manuscript.docx"

    old_manifest = '{"sentinel":"old-manifest"}\n'
    old_pdf = b"%PDF-1.4\n%old-pdf\n"
    old_docx = b"old-docx"
    manifest_path.write_text(old_manifest, encoding="utf-8")
    pdf_path.write_bytes(old_pdf)
    docx_path.write_bytes(old_docx)

    original_export_pdf = package_builder.export_pdf

    def failing_export_pdf(*args, **kwargs):
        original_export_pdf(*args, **kwargs)
        raise RuntimeError("simulated pdf export failure")

    monkeypatch.setattr(package_builder, "export_pdf", failing_export_pdf)

    with pytest.raises(RuntimeError, match="simulated pdf export failure"):
        module.create_submission_minimal_package(
            paper_root=paper_root,
            publication_profile="general_medical_journal",
        )

    assert submission_root.exists()
    assert manifest_path.read_text(encoding="utf-8") == old_manifest
    assert pdf_path.read_bytes() == old_pdf
    assert docx_path.read_bytes() == old_docx


def test_describe_submission_minimal_authority_detects_changed_compiled_markdown(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    current = module.describe_submission_minimal_authority(paper_root=paper_root)
    assert current["status"] == "current"

    write_text(
        paper_root / "build" / "review_manuscript.md",
        "# Updated review manuscript\n\nLate-stage authority change.\n",
    )

    stale = module.describe_submission_minimal_authority(paper_root=paper_root)
    assert stale["status"] == "stale_source_changed"
    assert stale["stale_reason"] == "submission_source_signature_mismatch"


def test_describe_submission_minimal_authority_flags_legacy_manifest_when_source_is_newer(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )
    manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    manifest.pop("source_signature", None)
    manifest.pop("source_contract", None)
    dump_json(manifest_path, manifest)

    current = module.describe_submission_minimal_authority(paper_root=paper_root)
    assert current["status"] == "current"

    write_text(
        paper_root / "build" / "review_manuscript.md",
        "# Updated review manuscript\n\nLegacy package is now stale.\n",
    )

    stale = module.describe_submission_minimal_authority(paper_root=paper_root)
    assert stale["status"] == "stale_source_changed"
    assert stale["stale_reason"] == "submission_source_newer_than_manifest"


def test_describe_submission_minimal_authority_ignores_source_mtime_only_drift(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    references_path = paper_root / "references.bib"
    references_stat = references_path.stat()
    os.utime(
        references_path,
        ns=(references_stat.st_atime_ns, references_stat.st_mtime_ns + 1_000_000_000),
    )

    authority = module.describe_submission_minimal_authority(paper_root=paper_root)

    assert authority["status"] == "current"
    assert authority["stale_reason"] is None
    assert authority["source_signature"] == manifest["source_signature"]


def test_create_submission_minimal_package_canonicalizes_authoritative_worktree_source_paths(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_authoritative_worktree_source_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    source_paths = [item["path"] for item in manifest["source_contract"]["source_files"]]
    assert all(not path.startswith("/") for path in source_paths)
    assert "paper/figures/generated/F1.png" in source_paths
    assert "paper/tables/generated/T1.csv" in source_paths
    assert (paper_root / "submission_minimal" / "tables" / "Table1.csv").read_text(encoding="utf-8") == (
        "Characteristic,Value\nAge,99\n"
    )

    authority = module.describe_submission_minimal_authority(paper_root=paper_root)
    assert authority["status"] == "current"


def test_create_submission_minimal_package_defaults_to_ama_citation_style(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["citation_style"] == "AMA"


def test_create_submission_minimal_package_copies_figures_and_tables(tmp_path: Path) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    paper_root = make_paper_workspace(tmp_path)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    expected_paths = [
        submission_root / "figures" / "Figure1.pdf",
        submission_root / "figures" / "Figure1.png",
        submission_root / "figures" / "SupplementaryFigureS1.pdf",
        submission_root / "figures" / "SupplementaryFigureS1.png",
        submission_root / "tables" / "Table1.csv",
        submission_root / "tables" / "Table1.md",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_create_submission_minimal_package_uses_existing_figure_exports_when_catalog_lists_missing_alternative(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                    "title": "Main figure",
                    "export_paths": [
                        "paper/figures/F1_main.png",
                        "paper/figures/F1_main.pdf",
                        "paper/figures/F1_main.svg",
                    ],
                }
            ],
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert (submission_root / "figures" / "Figure1.png").exists()
    assert (submission_root / "figures" / "Figure1.pdf").exists()
    assert not (submission_root / "figures" / "Figure1.svg").exists()
    assert manifest["figures"][0]["source_paths"] == [
        "paper/figures/F1_main.png",
        "paper/figures/F1_main.pdf",
    ]
    source_contract_paths = [item["path"] for item in manifest["source_contract"]["source_files"]]
    assert "paper/figures/F1_main.png" in source_contract_paths
    assert "paper/figures/F1_main.pdf" in source_contract_paths
    assert "paper/figures/F1_main.svg" not in source_contract_paths

    authority = module.describe_submission_minimal_authority(paper_root=paper_root)
    assert authority["status"] == "current"
    assert authority["missing_source_paths"] == []


def test_create_submission_minimal_package_authority_ignores_post_gate_evidence_ledger_refresh(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    package_builder = importlib.import_module("med_autoscience.controllers.submission_minimal_parts.package_builder")
    paper_root = make_paper_workspace(tmp_path)
    write_text(paper_root / "evidence_ledger.json", '{"schema_version":1,"items":[]}' + "\n")

    monkeypatch.setattr(package_builder.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)

    def sync_study_delivery(*, paper_root: Path, stage: str, publication_profile: str) -> dict:
        write_text(paper_root / "evidence_ledger.json", '{"schema_version":1,"items":[{"id":"post-sync"}]}' + "\n")
        return {"status": "synced", "stage": stage, "publication_profile": publication_profile}

    monkeypatch.setattr(package_builder.study_delivery_sync, "sync_study_delivery", sync_study_delivery)
    monkeypatch.setattr(
        package_builder,
        "replay_post_submission_minimal_sync",
        lambda *, paper_root: {"status": "synced"},
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert "paper/evidence_ledger.json" not in manifest["source_contract"]["source_paths"]

    write_text(paper_root / "evidence_ledger.json", '{"schema_version":1,"items":[{"id":"gate-refresh"}]}' + "\n")

    authority = module.describe_submission_minimal_authority(paper_root=paper_root)
    assert authority["status"] == "current"


def test_create_submission_minimal_package_general_profile_writes_figure_legends_and_tables(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "Figure1",
                    "story_role": "overall_performance_and_clinical_utility",
                    "research_question": "Does the main figure support the paper-facing interpretation?",
                    "direct_message": "The primary display item supports the manuscript-facing clinical message.",
                    "clinical_implication": "The figure can be read as a reviewer-facing legend rather than a slide-style caption.",
                    "interpretation_boundary": "The figure legend does not establish a treatment recommendation by itself.",
                    "panel_messages": [
                        {"panel_id": "A", "message": "Panel A summarizes the main paper-facing interpretation."}
                    ],
                    "legend_glossary": [
                        {
                            "term": "treat all",
                            "explanation": "Assumes every patient is managed as high risk at the chosen threshold."
                        }
                    ],
                    "threshold_semantics": "Thresholds are illustrative operating points rather than mandated cut-offs.",
                    "stratification_basis": "Displayed groups follow the prespecified manuscript presentation.",
                    "recommendation_boundary": "Clinical decisions should not rely on this figure alone.",
                    "renderer_contract": {
                        "figure_semantics": "evidence",
                        "renderer_family": "python",
                        "selection_rationale": "The legend is derived from an audited paper-facing figure.",
                        "fallback_on_failure": False,
                        "failure_action": "block_and_fix_environment"
                    }
                }
            ],
        },
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "# Figure Legends" in submission_markdown
    assert "## Figure 1. Main figure" in submission_markdown
    assert "Caption." in submission_markdown
    assert "The primary display item supports the manuscript-facing clinical message." in submission_markdown
    assert submission_markdown.count("The primary display item supports the manuscript-facing clinical message.") == 1
    assert "Panel A summarizes the main paper-facing interpretation." in submission_markdown
    assert submission_markdown.count("Panel A summarizes the main paper-facing interpretation.") == 1
    assert (
        "Abbreviations: treat all, Assumes every patient is managed as high risk at the chosen threshold."
        in submission_markdown
    )
    assert "# Tables" in submission_markdown
    assert "## Table 1" in submission_markdown
    assert "| Characteristic | Value |" in submission_markdown


def test_create_submission_minimal_package_general_profile_embeds_figures_into_docx_and_pdf(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    submission_markdown = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "# Figures" in submission_markdown
    assert "## Figure 1. Main figure" in submission_markdown
    assert "![](../figures/F1_main.png)" in submission_markdown
    assert "Caption." in submission_markdown
    assert manifest["manuscript"]["pdf_path"] == "paper/submission_minimal/paper.pdf"

    with zipfile.ZipFile(submission_root / "manuscript.docx") as archive:
        names = archive.namelist()
        document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    assert any(name.startswith("word/media/") for name in names)
    assert "<w:drawing" in document_xml

    pdf_reader = PdfReader(str(submission_root / "paper.pdf"))
    assert sum(len(page.images) for page in pdf_reader.pages) >= 1


def test_inspect_submission_docx_surface_treats_directory_placeholder_as_missing() -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")

    stats = module.inspect_submission_docx_surface(Path(""))

    assert stats == {
        "exists": False,
        "embedded_image_count": 0,
        "drawing_count": 0,
    }


def test_create_submission_minimal_package_accepts_current_bundle_contract_shape(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "pdf_path": "paper/paper.pdf",
        },
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/build/review_manuscript.md",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
            "included_assets": [
                {"path": "paper/paper.pdf", "kind": "compiled_pdf", "status": "present"},
            ],
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert (submission_root / "manuscript.docx").exists()
    assert (submission_root / "paper.pdf").exists()
    assert manifest["manuscript"]["source_markdown_path"] == "paper/submission_minimal/manuscript_submission.md"
    assert manifest["manuscript"]["pdf_path"] == "paper/submission_minimal/paper.pdf"


def test_resolve_compiled_markdown_path_skips_submission_surface_candidates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"

    write_text(
        submission_root / "manuscript_source.md",
        """---
title: "Wrong self-referential manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

Wrong self reference text.
""",
    )

    resolved = module.resolve_compiled_markdown_path(
        workspace_root=paper_root.parent,
        bundle_manifest={
            "schema_version": 1,
            "draft_path": "paper/build/review_manuscript.md",
        },
        compile_report={
            "source_markdown_path": "paper/submission_minimal/manuscript_source.md",
            "source_markdown": "paper/submission_minimal/manuscript_source.md",
        },
        excluded_roots=(submission_root,),
    )

    assert resolved == paper_root / "build" / "review_manuscript.md"


def test_resolve_compiled_pdf_path_skips_submission_surface_candidates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"

    write_text(submission_root / "paper.pdf", "%PDF-1.4\n%self referential pdf\n")

    resolved = module.resolve_compiled_pdf_path(
        workspace_root=paper_root.parent,
        bundle_manifest={
            "schema_version": 1,
            "pdf_path": "paper/paper.pdf",
        },
        compile_report={
            "output_pdf": "paper/submission_minimal/paper.pdf",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        },
        excluded_roots=(submission_root,),
    )

    assert resolved == paper_root / "paper.pdf"


def test_create_submission_minimal_package_skips_self_referential_compiled_sources(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    submission_root = paper_root / "submission_minimal"

    write_text(
        submission_root / "manuscript_source.md",
        """---
title: "Wrong self-referential manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

Wrong self reference text.

# Main Figures

## Figure 1. Wrong figure

Wrong caption.

![](../figures/F1_main.png)
""",
    )
    write_text(submission_root / "paper.pdf", "%PDF-1.4\n%self referential pdf\n")
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown_path": "paper/submission_minimal/manuscript_source.md",
            "source_markdown": "paper/submission_minimal/manuscript_source.md",
            "output_pdf": "paper/submission_minimal/paper.pdf",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        },
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/build/review_manuscript.md",
            "pdf_path": "paper/paper.pdf",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "This is a manuscript citation [@ref1]." in submission_markdown
    assert "Wrong self reference text." not in submission_markdown


def test_create_submission_minimal_package_prefers_compiled_markdown_over_draft_path(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    write_text(
        paper_root / "draft.md",
        """# Draft

## Title

Wrong draft title

## Abstract

Wrong draft abstract.
""",
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "draft_path": "paper/draft.md",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
        },
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert 'title: "Test Medical Manuscript"' in submission_markdown
    assert 'bibliography: ../references.bib' in submission_markdown
    assert "Wrong draft title" not in submission_markdown


def test_create_submission_minimal_package_accepts_current_figure_and_table_catalog_shape(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "figure1",
                    "role": "paper_main",
                    "planned_exports": ["paper/figures/F1_main.pdf", "paper/figures/F1_main.png"],
                }
            ],
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "table1",
                    "path": "paper/tables/T1_summary.md",
                }
            ],
        },
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert (submission_root / "figures" / "figure1.pdf").exists()
    assert (submission_root / "figures" / "figure1.png").exists()
    assert (submission_root / "tables" / "table1.md").exists()
