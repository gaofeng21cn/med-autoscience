from tests.submission_minimal_cases.shared import *

from med_autoscience.controllers.submission_minimal_parts.markdown_surface_qc import inspect_submission_docx_surface
from med_autoscience.controllers.submission_minimal_parts.package_builder import create_submission_minimal_package


def test_export_pdf_uses_submission_layout_header_for_fixed_figures_and_wide_tables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    export_renderers = importlib.import_module(
        "med_autoscience.controllers.submission_minimal_parts.export_renderers"
    )
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "Submission"
---

# Main Figures

## Figure 2. Later figure

![](figures/Figure2.png)

## Figure 1. Earlier figure

![](figures/Figure1.png)

# Main Tables

## Table 1. Wide table

| A very long header | Another very long header |
| --- | --- |
| A | B |
""",
    )
    output_pdf = tmp_path / "paper.pdf"
    calls: list[dict[str, Any]] = []

    def fake_run(command, *, cwd, check):
        calls.append({"command": command, "cwd": cwd, "check": check})
        output_pdf.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(export_renderers.subprocess, "run", fake_run)

    export_renderers.export_pdf(
        compiled_markdown_path=source_markdown,
        paper_root=tmp_path,
        output_pdf_path=output_pdf,
        csl_path=tmp_path / "style.csl",
    )

    assert calls
    command = calls[0]["command"]
    assert command[command.index("--include-in-header") + 1] == "submission_pdf_layout.tex"
    assert "--pdf-engine=xelatex" in command
    assert "geometry:margin=0.82in" in command
    assert "linestretch=1.06" in command
    header_text = (tmp_path / "submission_pdf_layout.tex").read_text(encoding="utf-8")
    assert "\\usepackage{newtxtext}" in header_text
    assert "\\definecolor{MASAccent}{HTML}{145C68}" in header_text
    assert "\\titleformat{\\section}{\\Large\\bfseries\\color{MASAccent}}" in header_text
    assert "\\captionsetup{font=small,labelfont=bf" in header_text
    assert "\\floatplacement{figure}{H}" in header_text
    assert "\\AtBeginEnvironment{longtable}{\\small" in header_text
    assert "\\setlength{\\tabcolsep}{4pt}" in header_text
    assert "\\begin{landscape}" not in header_text


def test_create_submission_minimal_package_general_profile_writes_figure_legends_and_tables(tmp_path: Path) -> None:
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

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_markdown = (paper_root / "submission_minimal" / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "# Figure Legends" in submission_markdown
    assert "## Figure 1. Main figure" in submission_markdown
    legend_block = submission_markdown.split("## Figure 1. Main figure", 1)[1].split("# Main Tables", 1)[0]
    assert "\n\nAbbreviations:" not in legend_block
    assert "Caption." in submission_markdown
    assert "The primary display item supports the manuscript-facing clinical message." in submission_markdown
    assert submission_markdown.count("The primary display item supports the manuscript-facing clinical message.") == 1
    assert "Panel A summarizes the main paper-facing interpretation." in submission_markdown
    assert submission_markdown.count("Panel A summarizes the main paper-facing interpretation.") == 1
    assert "The figure can be read as a reviewer-facing legend" not in submission_markdown
    assert "The figure legend does not establish a treatment recommendation" not in submission_markdown
    assert "Thresholds are illustrative operating points" not in submission_markdown
    assert "Clinical decisions should not rely on this figure alone" not in submission_markdown
    assert (
        "Abbreviations: treat all, Assumes every patient is managed as high risk at the chosen threshold."
        in submission_markdown
    )
    assert "# Main Tables" in submission_markdown
    assert "## Table 1" in submission_markdown
    assert "| Characteristic | Value |" in submission_markdown


def test_create_submission_minimal_package_general_profile_embeds_figures_into_docx_and_pdf(
    tmp_path: Path,
    real_submission_exports,
) -> None:
    paper_root = make_paper_workspace(tmp_path)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    submission_markdown = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "# Main Figures" in submission_markdown
    assert "## Figure 1. Main figure" in submission_markdown
    assert "![](figures/Figure1.png){width=100%}" in submission_markdown
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
    stats = inspect_submission_docx_surface(Path(""))

    assert stats == {
        "exists": False,
        "embedded_image_count": 0,
        "drawing_count": 0,
    }


def test_general_medical_docx_markdown_keeps_wide_main_tables(tmp_path: Path) -> None:
    profile_builders = importlib.import_module(
        "med_autoscience.controllers.submission_minimal_parts.profile_builders"
    )
    paper_root = make_paper_workspace(tmp_path)
    write_text(
        paper_root / "tables" / "T4_wide.md",
        "\n".join(
            [
                "| BMI category | A | B | C | D | E | F | G | H |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| Overweight | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |",
            ]
        ) + "\n",
    )
    write_text(paper_root / "tables" / "T4_wide.csv", "BMI category,A,B,C,D,E,F,G,H\nOverweight,1,2,3,4,5,6,7,8\n")
    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table_catalog = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    table_catalog["tables"].append(
        {
            "table_id": "T4",
            "paper_role": "main_text",
            "title": "Adult multidimensional metabolic phenotype profile by BMI category",
            "caption": "Wide table preview.",
            "asset_paths": [
                "paper/tables/T4_wide.csv",
                "paper/tables/T4_wide.md",
            ],
        }
    )
    dump_json(table_catalog_path, table_catalog)

    output_path = profile_builders.build_general_medical_submission_markdown(
        compiled_markdown_path=paper_root / "build" / "review_manuscript.md",
        submission_root=paper_root / "submission_minimal",
        compiled_markdown_text=(paper_root / "build" / "review_manuscript.md").read_text(encoding="utf-8"),
        output_name="manuscript_submission_docx.md",
        allow_landscape_latex_for_tables=False,
    )
    markdown_text = output_path.read_text(encoding="utf-8")
    assert "## Table 4. Adult multidimensional metabolic phenotype profile by BMI category" in markdown_text
    assert "| BMI category | A | B | C | D | E | F | G | H |" in markdown_text
    assert r"\begin{landscape}" not in markdown_text
