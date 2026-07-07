from tests.submission_minimal_cases.shared import *


def test_create_submission_minimal_package_writes_general_supplementary_table_preview(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    write_text(paper_root / "tables" / "S1_missingness.csv", "Variable,Missing\nBMI,0\n")
    write_text(
        paper_root / "tables" / "S1_missingness.md",
        "\\newpage\n\n# Supplementary Table S1. Missingness atlas\n\n| Variable | Missing |\n| --- | --- |\n| BMI | 0 |\n",
    )
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table_catalog = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    table_catalog["tables"].append(
        {
            "table_id": "S1",
            "paper_role": "supplementary",
            "title": "Missingness atlas",
            "caption": "Supplementary completeness summary.",
            "asset_paths": [
                "paper/tables/S1_missingness.csv",
                "paper/tables/S1_missingness.md",
            ],
        }
    )
    dump_json(table_catalog_path, table_catalog)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    supplementary_tables_markdown_path = submission_root / "supplementary_tables.md"
    supplementary_figures_markdown_path = submission_root / "supplementary_figures.md"
    supplementary_markdown_path = submission_root / "supplementary_material.md"
    supplementary_pdf_path = submission_root / "supplementary_material.pdf"
    supplementary_tables_pdf_path = submission_root / "supplementary_tables.pdf"
    supplementary_figures_pdf_path = submission_root / "supplementary_figures.pdf"
    combined_docx_path = submission_root / "manuscript_with_supplementary.docx"
    combined_pdf_path = submission_root / "paper_with_supplementary.pdf"
    assert supplementary_tables_markdown_path.exists()
    assert supplementary_figures_markdown_path.exists()
    assert supplementary_markdown_path.exists()
    assert supplementary_pdf_path.exists()
    assert supplementary_tables_pdf_path.exists()
    assert supplementary_figures_pdf_path.exists()
    assert combined_docx_path.exists()
    assert combined_pdf_path.exists()

    supplementary_markdown = supplementary_markdown_path.read_text(encoding="utf-8")
    assert "Supplementary Table S1. Missingness atlas" in supplementary_markdown
    assert supplementary_markdown.count("Supplementary Table S1. Missingness atlas") == 1
    assert "Supplementary completeness summary." in supplementary_markdown
    assert "| BMI | 0 |" in supplementary_markdown
    assert "Supplementary Figure S1. Supplementary figure" in supplementary_markdown
    assert "![](figures/SupplementaryFigureS1.png){width=100%}" in supplementary_markdown

    manifest = json.loads((submission_root / "audit" / "submission_manifest.json").read_text(encoding="utf-8"))
    assert manifest["supplementary_material"]["source_markdown_path"] == (
        "paper/submission_minimal/supplementary_material.md"
    )
    assert manifest["supplementary_material"]["pdf_path"] == (
        "paper/submission_minimal/supplementary_material.pdf"
    )
    assert manifest["supplementary_material"]["combined_review_docx_path"] == (
        "paper/submission_minimal/manuscript_with_supplementary.docx"
    )
    assert manifest["supplementary_material"]["combined_review_pdf_path"] == (
        "paper/submission_minimal/paper_with_supplementary.pdf"
    )
    supplementary_page_count = len(PdfReader(str(supplementary_pdf_path)).pages)
    assert supplementary_page_count == (
        len(PdfReader(str(supplementary_tables_pdf_path)).pages)
        + len(PdfReader(str(supplementary_figures_pdf_path)).pages)
    )
    assert len(PdfReader(str(combined_pdf_path)).pages) == (
        len(PdfReader(str(submission_root / "paper.pdf")).pages) + supplementary_page_count
    )


def test_create_submission_minimal_package_materializes_deferred_supplementary_figures(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    figure_catalog["figures"] = [figure_catalog["figures"][0]]
    figure_catalog["deferred_figures"] = [
        {
            "figure_id": "F4",
            "paper_role": "supplementary",
            "display_role": "deferred_context_not_main_evidence",
            "title": "Deferred threshold-utility context",
            "caption": "Deferred context retained as supplementary support.",
        }
    ]
    dump_json(figure_catalog_path, figure_catalog)
    output_png_path = paper_root / "figures" / "generated" / "F4_time_to_event_decision_curve.png"
    output_pdf_path = paper_root / "figures" / "generated" / "F4_time_to_event_decision_curve.pdf"
    write_png(output_png_path)
    write_text(output_pdf_path, "%PDF-1.4\n%deferred figure\n")
    dump_json(
        paper_root / "build" / "display_pack_render_requests" / "F4.render_request.json",
        {
            "output_png_path": str(output_png_path.resolve()),
            "output_pdf_path": str(output_pdf_path.resolve()),
            "output_svg_path": None,
        },
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    supplementary_figures_markdown_path = submission_root / "supplementary_figures.md"
    combined_docx_path = submission_root / "manuscript_with_supplementary.docx"
    combined_pdf_path = submission_root / "paper_with_supplementary.pdf"

    assert supplementary_figures_markdown_path.exists()
    assert combined_docx_path.exists()
    assert combined_pdf_path.exists()
    supplementary_markdown = supplementary_figures_markdown_path.read_text(encoding="utf-8")
    assert "Supplementary Figure S1. Deferred threshold-utility context" in supplementary_markdown
    assert "Deferred context retained as supplementary support." in supplementary_markdown
    assert "![](figures/Figure4.png){width=100%}" in supplementary_markdown

    manifest = json.loads((submission_root / "audit" / "submission_manifest.json").read_text(encoding="utf-8"))
    assert manifest["supplementary_material"]["source_markdown_path"] == (
        "paper/submission_minimal/supplementary_figures.md"
    )
    assert manifest["supplementary_material"]["combined_review_docx_path"] == (
        "paper/submission_minimal/manuscript_with_supplementary.docx"
    )
    assert manifest["supplementary_material"]["combined_review_pdf_path"] == (
        "paper/submission_minimal/paper_with_supplementary.pdf"
    )


def test_create_submission_minimal_package_recovers_inline_supplementary_tables_without_catalog_entries(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    write_text(
        paper_root / "draft.md",
        """# Current MAS Draft Title

## Abstract

Current draft abstract.

## Introduction

Current draft introduction with citation [@ref1].

## Methods

Current draft methods.

## Results

Current draft results.

## Supplementary Tables

### Supplementary Table S1. Missingness and plausibility of phenotype-defining variables

| Variable | Missing |
| --- | --- |
| BMI | 0 |

## Discussion

Current draft discussion.

## Conclusion

Current draft conclusion.
""",
    )
    dump_json(
        paper_root / "build" / "compile_report.json",
        {
            "schema_version": 1,
            "source_markdown_path": "paper/draft.md",
            "output_pdf": "paper/paper.pdf",
        },
    )

    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    figure_catalog["figures"][1]["display_role"] = "deferred_context_not_main_evidence"
    dump_json(figure_catalog_path, figure_catalog)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    supplementary_markdown_path = submission_root / "supplementary_material.md"
    supplementary_pdf_path = submission_root / "supplementary_material.pdf"
    combined_docx_path = submission_root / "manuscript_with_supplementary.docx"
    combined_pdf_path = submission_root / "paper_with_supplementary.pdf"

    assert supplementary_markdown_path.exists()
    assert supplementary_pdf_path.exists()
    assert combined_docx_path.exists()
    assert combined_pdf_path.exists()

    supplementary_markdown = supplementary_markdown_path.read_text(encoding="utf-8")
    assert "# Supplementary Tables" in supplementary_markdown
    assert "Supplementary Table S1. Missingness and plausibility of phenotype-defining variables" in supplementary_markdown
    assert "| BMI | 0 |" in supplementary_markdown

    submission_text = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "Supplementary Table S1. Missingness and plausibility of phenotype-defining variables" not in submission_text

    manifest = json.loads((submission_root / "audit" / "submission_manifest.json").read_text(encoding="utf-8"))
    assert manifest["supplementary_material"]["source_markdown_path"] == (
        "paper/submission_minimal/supplementary_material.md"
    )
    assert manifest["supplementary_material"]["pdf_path"] == (
        "paper/submission_minimal/supplementary_material.pdf"
    )
    assert manifest["supplementary_material"]["combined_review_docx_path"] == (
        "paper/submission_minimal/manuscript_with_supplementary.docx"
    )
    assert manifest["supplementary_material"]["combined_review_pdf_path"] == (
        "paper/submission_minimal/paper_with_supplementary.pdf"
    )
