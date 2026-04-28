from .shared import *

def test_inspect_submission_source_markdown_counts_short_f_headings_as_figures(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "Submission Manuscript"
---

# Figures

## F1. Main figure

![](figures/F1_main.png)

Legend text for the short-F main figure.
""",
    )

    inspection = module.inspect_submission_source_markdown(source_markdown)

    assert inspection["figure_block_count"] == 1
    assert inspection["figure_blocks_with_images"] == 1
    assert inspection["figure_blocks_with_legends"] == 1


def test_inspect_submission_source_markdown_counts_independent_figure_legends_section(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "Submission Manuscript"
---

# Figures

## Figure 1. Main figure

![](figures/F1_main.png)

# Figure Legends

Figure 1. Legend text for the independent figure legend section.

# Tables

## Table 1

| Characteristic | Value |
| --- | --- |
| Age | 52 |
""",
    )

    inspection = module.inspect_submission_source_markdown(source_markdown)

    assert inspection["figure_block_count"] == 1
    assert inspection["figure_blocks_with_images"] == 1
    assert inspection["figure_blocks_with_legends"] == 1


def test_inspect_submission_source_markdown_treats_lowercase_figure_legends_as_separate_section(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "Submission Manuscript"
---

# Figures

## Figure 1. Main figure

![](figures/F1_main.png)

# Figure legends

## Figure 1. Main figure

Legend text for the lowercase independent figure legend section.

# Tables

## Table 1

| Characteristic | Value |
| --- | --- |
| Age | 52 |
""",
    )

    inspection = module.inspect_submission_source_markdown(source_markdown)

    assert inspection["figure_block_count"] == 1
    assert inspection["figure_blocks_with_images"] == 1
    assert inspection["figure_blocks_with_legends"] == 1


def test_create_submission_minimal_package_supports_manuscript_shaped_draft_without_front_matter(
    tmp_path: Path,
) -> None:
    from docx import Document

    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_manuscript_shaped_draft_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    compiled_submission_markdown = submission_root / "manuscript_submission.md"
    assert compiled_submission_markdown.exists()

    submission_markdown = compiled_submission_markdown.read_text(encoding="utf-8")
    assert submission_markdown.startswith("---\n")
    assert 'title: "Manuscript-Shaped Draft Title"' in submission_markdown
    assert "bibliography: ../references.bib" in submission_markdown
    assert "bibliography: ../../references.bib" not in submission_markdown
    assert "title: \"Article Title\"" not in submission_markdown
    assert "\n# Materials and Methods\n\nStudy methods paragraph.\n" in submission_markdown
    assert "Draft abstract methods." in submission_markdown
    assert manifest["manuscript"]["source_markdown_path"] == "paper/submission_minimal/manuscript_submission.md"

    document = Document(submission_root / "manuscript.docx")
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    assert paragraphs[0] == "Manuscript-Shaped Draft Title"
    assert any("Study methods paragraph." in paragraph for paragraph in paragraphs)
    assert any("A primary source" in paragraph for paragraph in paragraphs)


def test_create_submission_minimal_package_supports_front_matter_manuscript_shaped_draft(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_manuscript_shaped_draft_workspace(tmp_path)
    write_text(
        paper_root / "draft.md",
        """---
title: "Front Matter Manuscript-Shaped Draft"
bibliography: references.bib
---

## Abstract

Structured abstract paragraph.

## Introduction

Frontmatter introduction paragraph.

## Methods

Frontmatter methods paragraph.

## Results

Frontmatter results paragraph.

## Discussion

Frontmatter discussion paragraph.
""",
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(
        encoding="utf-8"
    )
    assert 'title: "Front Matter Manuscript-Shaped Draft"' in submission_markdown
    for heading in ["# Abstract", "# Introduction", "# Materials and Methods", "# Results", "# Discussion"]:
        assert submission_markdown.splitlines().count(heading) == 1
    for paragraph in [
        "Structured abstract paragraph.",
        "Frontmatter introduction paragraph.",
        "Frontmatter methods paragraph.",
        "Frontmatter results paragraph.",
        "Frontmatter discussion paragraph.",
    ]:
        assert submission_markdown.count(paragraph) == 1


def test_create_submission_minimal_package_filters_internal_instruction_semantics_from_figure_legends(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "direct_message": "The paper should open with this burden-architecture figure.",
                    "clinical_implication": "The figure summarizes the observed cohort architecture.",
                    "interpretation_boundary": "Do not recast this figure as causal proof.",
                    "panel_messages": [
                        {"panel_id": "A", "message": "Panel A must not claim external validation."}
                    ],
                    "threshold_semantics": "Thresholds are descriptive operating points.",
                    "recommendation_boundary": "This figure should not be framed as treatment guidance.",
                }
            ],
        },
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(
        encoding="utf-8"
    )
    assert "The figure summarizes the observed cohort architecture." in submission_markdown
    assert "Thresholds are descriptive operating points." in submission_markdown
    assert "paper should" not in submission_markdown.lower()
    assert "do not recast" not in submission_markdown.lower()
    assert "must not" not in submission_markdown.lower()
    assert "should not" not in submission_markdown.lower()


def test_create_submission_minimal_package_preserves_top_level_figures_in_manuscript_shaped_draft(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_manuscript_shaped_draft_workspace(tmp_path)
    draft_path = paper_root / "draft.md"

    write_png(paper_root / "figures" / "F1.png")
    write_text(
        draft_path,
        draft_path.read_text(encoding="utf-8")
        + """

# Figures

## Figure 1. Preserved top-level figure

![](figures/F1.png)

Preserved legend for the manuscript-shaped top-level figures block.
""",
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    submission_markdown = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")

    assert submission_markdown.splitlines().count("# Main Figures") == 1
    assert "## Figure 1. Preserved top-level figure" in submission_markdown
    assert "![](figures/Figure1.png)" in submission_markdown
    assert "Preserved legend for the manuscript-shaped top-level figures block." in submission_markdown

    manuscript_surface_qc = manifest["manuscript"]["surface_qc"]
    assert manuscript_surface_qc["status"] == "pass"
    assert manuscript_surface_qc["source_markdown"]["figure_blocks_with_images"] == 1
    assert manuscript_surface_qc["source_markdown"]["figure_blocks_with_legends"] == 1


def test_create_submission_minimal_package_accepts_materialized_submission_source_from_compile_report(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_materialized_submission_source_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert (submission_root / "manuscript_source.md").exists()
    submission_markdown = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    assert 'title: "Materialized Submission Title"' in submission_markdown
    assert "# Main Figures" in submission_markdown
    assert "## Figure 1. Main figure" in submission_markdown
    assert "![F1](figures/Figure1.png)" in submission_markdown
    assert "Materialized figure caption." in submission_markdown
    manuscript_surface_qc = manifest["manuscript"]["surface_qc"]
    assert manuscript_surface_qc["status"] == "pass"
    assert manifest["manuscript"]["source_markdown_alias_role"] == "authority_note"
    assert manuscript_surface_qc["authority_note"]["role_clarity_pass"] is True

    with zipfile.ZipFile(submission_root / "manuscript.docx") as archive:
        names = archive.namelist()
        document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    assert any(name.startswith("word/media/") for name in names)
    assert "<w:drawing" in document_xml

    pdf_reader = PdfReader(str(submission_root / "paper.pdf"))
    assert sum(len(page.images) for page in pdf_reader.pages) >= 1


def test_describe_submission_minimal_authority_accepts_materialized_submission_source_from_compile_report(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_materialized_submission_source_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    authority = module.describe_submission_minimal_authority(paper_root=paper_root)

    assert authority["status"] == "current"
    assert authority["stale_reason"] is None
    assert authority["recorded_source_signature"] == manifest["source_signature"]
    assert authority["source_signature"] == manifest["source_signature"]


def test_create_submission_minimal_package_falls_back_when_compile_report_points_to_missing_submission_source(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_current_draft_workspace(tmp_path)

    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "source_markdown_path": "paper/submission_minimal/manuscript_source.md",
            "pdf_path": "paper/paper.pdf",
        },
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    submission_markdown = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    assert 'title: "Current Draft Title"' in submission_markdown
    assert manifest["manuscript"]["source_markdown_path"] == "paper/submission_minimal/manuscript_submission.md"


def test_create_submission_minimal_package_materializes_references_and_pending_front_matter(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_current_draft_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
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
        "output_path": "paper/submission_minimal/references.bib",
        "entry_count": 1,
    }
    assert manifest["front_matter_placeholders"] == {
        "authors": "pending",
        "affiliations": "pending",
        "corresponding_author": "pending",
        "funding": "pending",
        "conflict_of_interest": "pending",
        "ethics": "pending",
        "data_availability": "pending",
    }


def test_build_submission_manuscript_surface_qc_flags_stale_docx_and_pdf_against_newer_source_markdown(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    source_markdown_path = submission_root / "manuscript_submission.md"
    docx_path = submission_root / "manuscript.docx"
    pdf_path = submission_root / "paper.pdf"

    source_markdown_text = source_markdown_path.read_text(encoding="utf-8")
    source_markdown_path.write_text(
        f"{source_markdown_text}\n<!-- freshness regression -->\n",
        encoding="utf-8",
    )
    os.utime(docx_path, (1000, 1000))
    os.utime(pdf_path, (1000, 1000))
    os.utime(source_markdown_path, (2000, 2000))

    manuscript_surface_qc = module.build_submission_manuscript_surface_qc(
        publication_profile="general_medical_journal",
        source_markdown_path=source_markdown_path,
        docx_path=docx_path,
        pdf_path=pdf_path,
        expected_main_figure_count=manifest["manuscript"]["surface_qc"]["expected_main_figure_count"],
    )

    failure_reasons = {item["failure_reason"] for item in manuscript_surface_qc["failures"]}
    assert manuscript_surface_qc["status"] == "fail"
    assert "submission_docx_older_than_source_markdown" in failure_reasons
    assert "submission_pdf_older_than_source_markdown" in failure_reasons


def test_build_submission_manuscript_surface_qc_flags_duplicate_sections_and_internal_instructions(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_source.md"
    write_text(
        source_markdown,
        """---
title: "Submission Manuscript"
---

# Abstract

Structured abstract.

## Introduction

First introduction.

## Methods

Methods paragraph.

## Results

Results paragraph.

## Discussion

Discussion paragraph.

# Introduction

Repeated introduction from a projection splice.

# Figure Legends

## Figure 1. Architecture

The manuscript should open with this burden-architecture figure. Use as the main-text local architecture evidence only; do not recast it as predictive superiority. This figure must not be reframed as causal proof.
""",
    )

    manuscript_surface_qc = module.build_submission_manuscript_surface_qc(
        publication_profile="general_medical_journal",
        source_markdown_path=source_markdown,
        docx_path=tmp_path / "manuscript.docx",
        pdf_path=tmp_path / "paper.pdf",
        expected_main_figure_count=0,
    )

    failure_reasons = {item["failure_reason"] for item in manuscript_surface_qc["failures"]}
    assert manuscript_surface_qc["status"] == "fail"
    assert "submission_source_markdown_duplicate_sections" in failure_reasons
    assert "submission_source_markdown_internal_instruction_leakage" in failure_reasons
