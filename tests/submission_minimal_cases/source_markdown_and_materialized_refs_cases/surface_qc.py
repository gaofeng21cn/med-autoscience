from tests.submission_minimal_cases.shared import *


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
        expected_main_figure_count=manifest["manuscript"]["surface_qc"][
            "expected_main_figure_count"
        ],
    )

    failure_reasons = {
        item["failure_reason"] for item in manuscript_surface_qc["failures"]
    }
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

    failure_reasons = {
        item["failure_reason"] for item in manuscript_surface_qc["failures"]
    }
    assert manuscript_surface_qc["status"] == "fail"
    assert "submission_source_markdown_duplicate_sections" in failure_reasons
    assert "submission_source_markdown_internal_instruction_leakage" in failure_reasons


def test_build_submission_manuscript_surface_qc_flags_display_directive_in_legends(
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

# Figure Legends

## Figure 1. Cohort flow

The first display should account for the cohort before phenotype interpretation.
""",
    )

    manuscript_surface_qc = module.build_submission_manuscript_surface_qc(
        publication_profile="general_medical_journal",
        source_markdown_path=source_markdown,
        docx_path=tmp_path / "manuscript.docx",
        pdf_path=tmp_path / "paper.pdf",
        expected_main_figure_count=0,
    )

    failure_reasons = {
        item["failure_reason"] for item in manuscript_surface_qc["failures"]
    }
    assert manuscript_surface_qc["status"] == "fail"
    assert "submission_source_markdown_internal_instruction_leakage" in failure_reasons


def test_build_submission_manuscript_surface_qc_blocks_engineering_prose_residue_in_legends(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "Submission Manuscript"
---

# Abstract

Structured abstract.

# Main Figures

## Figure 1. Model comparison

![](figures/Figure1.png)

# Figure Legends

## Figure 1. Model comparison

Calibration and decision-curve evidence across candidate packages within the prespecified clinical threshold window.
""",
    )

    manuscript_surface_qc = module.build_submission_manuscript_surface_qc(
        publication_profile="general_medical_journal",
        source_markdown_path=source_markdown,
        docx_path=tmp_path / "manuscript.docx",
        pdf_path=tmp_path / "paper.pdf",
        expected_main_figure_count=0,
    )

    failure_reasons = {
        item["failure_reason"] for item in manuscript_surface_qc["failures"]
    }
    assert manuscript_surface_qc["status"] == "fail"
    assert "submission_source_markdown_medical_journal_prose_residue" in failure_reasons


def test_build_submission_manuscript_surface_qc_blocks_registry_burden_figure_wording(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "Submission Manuscript"
---

# Abstract

Structured abstract.

# Main Figures

## Figure 2. BMI-category metabolic comorbidity burden in available registry fields

![](figures/Figure2.png)

# Figure Legends

## Figure 3. Registry variable availability

PHQ-9 and GAD-7 availability is not interpreted as whole-alliance psychobehavioral burden.
""",
    )

    manuscript_surface_qc = module.build_submission_manuscript_surface_qc(
        publication_profile="general_medical_journal",
        source_markdown_path=source_markdown,
        docx_path=tmp_path / "manuscript.docx",
        pdf_path=tmp_path / "paper.pdf",
        expected_main_figure_count=0,
    )

    assert manuscript_surface_qc["status"] == "fail"
    prose_hits = [
        hit
        for item in manuscript_surface_qc["failures"]
        for hit in item.get("medical_journal_prose_hits", [])
    ]
    assert "descriptive_registry_burden_caption_overclaim" in {
        hit["pattern_id"] for hit in prose_hits
    }


def test_build_submission_manuscript_surface_qc_allows_population_burden_boundary_caveat(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "Submission Manuscript"
---

# Abstract

Structured abstract.

# Limitations

Source counts do not establish population-level burden or national representativeness. Available-record denominators vary across variables.
""",
    )

    manuscript_surface_qc = module.build_submission_manuscript_surface_qc(
        publication_profile="general_medical_journal",
        source_markdown_path=source_markdown,
        docx_path=tmp_path / "manuscript.docx",
        pdf_path=tmp_path / "paper.pdf",
        expected_main_figure_count=0,
    )

    prose_hits = [
        hit
        for item in manuscript_surface_qc["failures"]
        for hit in item.get("medical_journal_prose_hits", [])
    ]
    assert "descriptive_registry_burden_caption_overclaim" not in {
        hit["pattern_id"] for hit in prose_hits
    }


def test_build_submission_manuscript_surface_qc_blocks_internal_quality_record_language(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "External Validation Manuscript"
---

# Methods

The external-validation cohort had linked mortality information available in the accepted analysis records.

# Results

Calibration slope and Brier score were not available from the verified outputs.

# Discussion

The exact source-code environment remains a source-documentation gap that requires author confirmation before external submission.
""",
    )

    manuscript_surface_qc = module.build_submission_manuscript_surface_qc(
        publication_profile="general_medical_journal",
        source_markdown_path=source_markdown,
        docx_path=tmp_path / "manuscript.docx",
        pdf_path=tmp_path / "paper.pdf",
        expected_main_figure_count=0,
    )

    failure_reasons = {
        item["failure_reason"] for item in manuscript_surface_qc["failures"]
    }
    assert manuscript_surface_qc["status"] == "fail"
    assert "submission_source_markdown_medical_journal_prose_residue" in failure_reasons
    prose_failure = next(
        item
        for item in manuscript_surface_qc["failures"]
        if item["failure_reason"]
        == "submission_source_markdown_medical_journal_prose_residue"
    )
    pattern_ids = {
        hit["pattern_id"] for hit in prose_failure["medical_journal_prose_hits"]
    }
    assert "verified_output_or_source_documentation_residue" in pattern_ids
    assert "submission_placeholder_instruction_residue" in pattern_ids


def test_build_submission_manuscript_surface_qc_blocks_invalid_analysis_history_story(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "External Validation Manuscript"
---

# Discussion

The raw-scale sensitivity check showed that the earlier transported-score failure
was a unit-harmonization lesson rather than a stable clinical finding.
""",
    )

    manuscript_surface_qc = module.build_submission_manuscript_surface_qc(
        publication_profile="general_medical_journal",
        source_markdown_path=source_markdown,
        docx_path=tmp_path / "manuscript.docx",
        pdf_path=tmp_path / "paper.pdf",
        expected_main_figure_count=0,
    )

    failure_reasons = {
        item["failure_reason"] for item in manuscript_surface_qc["failures"]
    }
    assert manuscript_surface_qc["status"] == "fail"
    assert "submission_source_markdown_medical_journal_prose_residue" in failure_reasons
    prose_failure = next(
        item
        for item in manuscript_surface_qc["failures"]
        if item["failure_reason"]
        == "submission_source_markdown_medical_journal_prose_residue"
    )
    pattern_ids = {
        hit["pattern_id"] for hit in prose_failure["medical_journal_prose_hits"]
    }
    assert "invalid_analysis_history_residue" in pattern_ids
