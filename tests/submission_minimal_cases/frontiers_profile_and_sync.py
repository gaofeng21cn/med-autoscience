from .shared import *

def test_create_submission_minimal_package_skips_missing_planned_table_entries(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "table1",
                    "status": "rendered_and_cleaned",
                    "path": "paper/tables/T1_summary.md",
                },
                {
                    "table_id": "table3",
                    "status": "planned_from_trusted_reports",
                    "path": "paper/tables/T3_missing.md",
                },
            ],
        },
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    assert (submission_root / "tables" / "table1.md").exists()
    assert not (submission_root / "tables" / "table3.md").exists()


def test_create_submission_minimal_package_syncs_study_delivery_when_context_is_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    package_builder = importlib.import_module("med_autoscience.controllers.submission_minimal_parts.package_builder")
    paper_root = make_paper_workspace(tmp_path)
    called: dict[str, object] = {}

    def fake_can_sync(*, paper_root: Path) -> bool:
        called["can_sync_paper_root"] = paper_root
        return True

    def fake_sync(
        *,
        paper_root: Path,
        stage: str,
        publication_profile: str = "general_medical_journal",
    ) -> dict:
        called["sync_paper_root"] = paper_root
        called["sync_stage"] = stage
        called["sync_publication_profile"] = publication_profile
        return {"stage": stage, "publication_profile": publication_profile}

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", fake_can_sync)
    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert called["can_sync_paper_root"] == paper_root
    assert called["sync_paper_root"] == paper_root
    assert called["sync_stage"] == "submission_minimal"
    assert called["sync_publication_profile"] == "general_medical_journal"
    assert manifest["delivery_sync"] == {
        "stage": "submission_minimal",
        "publication_profile": "general_medical_journal",
    }
    assert manifest["readme_path"] == "paper/submission_minimal/README.md"
    readme_text = (paper_root / "submission_minimal" / "README.md").read_text(encoding="utf-8")
    assert "paper/submission_minimal/" in readme_text
    assert "manuscript/" in readme_text


def test_create_submission_minimal_package_replays_post_materialization_sync_when_context_is_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    package_builder = importlib.import_module("med_autoscience.controllers.submission_minimal_parts.package_builder")
    paper_root = make_paper_workspace(tmp_path)
    called: dict[str, object] = {}

    monkeypatch.setattr(package_builder.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        package_builder.study_delivery_sync,
        "sync_study_delivery",
        lambda **_: {"stage": "submission_minimal"},
    )

    def fake_replay(*, paper_root: Path) -> dict[str, object]:
        called["paper_root"] = paper_root
        return {
            "status": "synced",
            "quest_root": "/tmp/runtime/quests/quest-001",
        }

    monkeypatch.setattr(package_builder, "replay_post_submission_minimal_sync", fake_replay)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert called["paper_root"] == paper_root
    assert manifest["delivery_sync"] == {"stage": "submission_minimal"}
    assert manifest["post_materialization_sync"] == {
        "status": "synced",
        "quest_root": "/tmp/runtime/quests/quest-001",
    }


def test_create_submission_minimal_package_frontiers_family_profile_creates_journal_specific_assets(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    frontiers_root = tmp_path / "frontiers_resources"
    manuscript_template = frontiers_root / "Frontiers_Template.docx"
    supplementary_template = frontiers_root / "Supplementary_Material.docx"
    csl_path = frontiers_root / "frontiers.csl"

    write_docx(manuscript_template, "Frontiers manuscript template")
    write_docx(supplementary_template, "Frontiers supplementary template")
    csl_path.write_text(module.default_ama_csl_path().read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_TEMPLATE_DOCX", str(manuscript_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_SUPPLEMENTARY_TEMPLATE_DOCX", str(supplementary_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_CSL", str(csl_path))

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="frontiers_family_harvard",
    )

    submission_root = paper_root / "journal_submissions" / "frontiers_family_harvard"
    assert submission_root.exists()
    assert manifest["publication_profile"] == "frontiers_family_harvard"
    assert manifest["citation_style"] == "FrontiersHarvard"
    assert manifest["readme_path"] == "paper/journal_submissions/frontiers_family_harvard/README.md"
    assert (submission_root / "manuscript.docx").exists()
    assert (submission_root / "Supplementary_Material.docx").exists()
    assert (submission_root / "paper.pdf").exists()
    assert "paper/journal_submissions/frontiers_family_harvard/" in (
        submission_root / "README.md"
    ).read_text(encoding="utf-8")
    assert manifest["manuscript"]["docx_path"] == "paper/journal_submissions/frontiers_family_harvard/manuscript.docx"
    assert (
        manifest["supplementary_material"]["docx_path"]
        == "paper/journal_submissions/frontiers_family_harvard/Supplementary_Material.docx"
    )
    assert manifest["journal_target"]["journal_family"] == "Frontiers"
    assert manifest["journal_target"]["reference_style_family"] == "FrontiersHarvard"


def test_create_submission_minimal_package_rejects_legacy_frontiers_profile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    frontiers_root = tmp_path / "frontiers_resources"
    manuscript_template = frontiers_root / "Frontiers_Template.docx"
    supplementary_template = frontiers_root / "Supplementary_Material.docx"
    csl_path = frontiers_root / "frontiers.csl"

    write_docx(manuscript_template, "Frontiers manuscript template")
    write_docx(supplementary_template, "Frontiers supplementary template")
    csl_path.write_text(module.default_ama_csl_path().read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_TEMPLATE_DOCX", str(manuscript_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_SUPPLEMENTARY_TEMPLATE_DOCX", str(supplementary_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_CSL", str(csl_path))

    try:
        module.create_submission_minimal_package(
            paper_root=paper_root,
            publication_profile="frontiers_in_physiology",
        )
    except ValueError as exc:
        assert "unsupported publication profile" in str(exc)
    else:
        raise AssertionError("legacy Frontiers profile should be rejected")


def test_create_submission_minimal_package_frontiers_family_profile_preserves_reference_doc_parts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    frontiers_root = tmp_path / "frontiers_resources"
    manuscript_template = frontiers_root / "Frontiers_Template.docx"
    supplementary_template = frontiers_root / "Supplementary_Material.docx"
    csl_path = frontiers_root / "frontiers.csl"

    write_docx(manuscript_template, "Frontiers manuscript template")
    write_docx(supplementary_template, "Frontiers supplementary template")
    csl_path.write_text(module.default_ama_csl_path().read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_TEMPLATE_DOCX", str(manuscript_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_SUPPLEMENTARY_TEMPLATE_DOCX", str(supplementary_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_CSL", str(csl_path))

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="frontiers_family_harvard",
    )

    output_docx_path = paper_root / "journal_submissions" / "frontiers_family_harvard" / "manuscript.docx"
    with zipfile.ZipFile(output_docx_path) as archive:
        footer_names = [name for name in archive.namelist() if name.startswith("word/footer")]
        assert footer_names


def test_create_submission_minimal_package_frontiers_family_uses_figure_semantics_manifest_for_legends(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    frontiers_root = tmp_path / "frontiers_resources"
    manuscript_template = frontiers_root / "Frontiers_Template.docx"
    supplementary_template = frontiers_root / "Supplementary_Material.docx"
    csl_path = frontiers_root / "frontiers.csl"

    write_docx(manuscript_template, "Frontiers manuscript template")
    write_docx(supplementary_template, "Frontiers supplementary template")
    csl_path.write_text(module.default_ama_csl_path().read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_TEMPLATE_DOCX", str(manuscript_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_SUPPLEMENTARY_TEMPLATE_DOCX", str(supplementary_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_CSL", str(csl_path))

    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "story_role": "overall_performance_and_clinical_utility",
                    "research_question": "Does the clinically informed model improve utility beyond the reference model?",
                    "direct_message": "Calibration and clinical utility improved, whereas discrimination gains were modest.",
                    "clinical_implication": "Supports preoperative counseling and postoperative surveillance planning.",
                    "interpretation_boundary": "This figure does not establish a recommended intervention threshold.",
                    "panel_messages": [
                        {"panel_id": "A", "message": "Discrimination is only one component of the figure-level interpretation."}
                    ],
                    "legend_glossary": [
                        {
                            "term": "treat all",
                            "explanation": "Assumes every patient is managed as high risk at the chosen threshold."
                        },
                        {
                            "term": "treat none",
                            "explanation": "Assumes no patient is managed as high risk at the chosen threshold."
                        },
                    ],
                    "threshold_semantics": "Thresholds are illustrative operating points rather than recommended cut-offs.",
                    "stratification_basis": "Risk groups are display-oriented rather than prespecified clinical bins.",
                    "recommendation_boundary": "No formal threshold recommendation is made from this figure alone.",
                    "renderer_contract": {
                        "figure_semantics": "evidence",
                        "renderer_family": "python",
                        "selection_rationale": "The legend is derived from an audited evidence figure exported from the locked analysis stack.",
                        "fallback_on_failure": False,
                        "failure_action": "block_and_fix_environment"
                    }
                }
            ],
        },
    )

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="frontiers_family_harvard",
    )

    frontiers_markdown = (
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "frontiers_manuscript.md"
    ).read_text(encoding="utf-8")
    assert "Calibration and clinical utility improved" in frontiers_markdown
    assert "treat all" in frontiers_markdown
    assert "Assumes every patient is managed as high risk" in frontiers_markdown
    assert "illustrative operating points rather than recommended cut-offs" in frontiers_markdown
    assert "No formal threshold recommendation is made from this figure alone" in frontiers_markdown


def test_create_submission_minimal_package_frontiers_family_syncs_into_study_family_package(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    # keep this assertion impossible for current implementation so the new sync contract is explicit
    frontiers_root = tmp_path / "frontiers_resources"
    manuscript_template = frontiers_root / "Frontiers_Template.docx"
    supplementary_template = frontiers_root / "Supplementary_Material.docx"
    csl_path = frontiers_root / "frontiers.csl"

    write_docx(manuscript_template, "Frontiers manuscript template")
    write_docx(supplementary_template, "Frontiers supplementary template")
    csl_path.write_text(module.default_ama_csl_path().read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_TEMPLATE_DOCX", str(manuscript_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_SUPPLEMENTARY_TEMPLATE_DOCX", str(supplementary_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_CSL", str(csl_path))

    called: dict[str, object] = {}

    def fake_can_sync(*, paper_root: Path) -> bool:
        return True

    def fake_sync(*, paper_root: Path, stage: str, publication_profile: str = "general_medical_journal") -> dict:
        called["paper_root"] = paper_root
        called["stage"] = stage
        called["publication_profile"] = publication_profile
        return {"stage": stage, "publication_profile": publication_profile}

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", fake_can_sync)
    monkeypatch.setattr(module.study_delivery_sync, "sync_study_delivery", fake_sync)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="frontiers_family_harvard",
    )

    assert called["paper_root"] == paper_root
    assert called["stage"] == "submission_minimal"
    assert called["publication_profile"] == "frontiers_family_harvard"


def test_create_submission_minimal_package_frontiers_family_uses_admin_gap_notes_not_prompt_placeholders(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)
    frontiers_root = tmp_path / "frontiers_resources"
    manuscript_template = frontiers_root / "Frontiers_Template.docx"
    supplementary_template = frontiers_root / "Supplementary_Material.docx"
    csl_path = frontiers_root / "frontiers.csl"

    write_docx(manuscript_template, "Frontiers manuscript template")
    write_docx(supplementary_template, "Frontiers supplementary template")
    csl_path.write_text(module.default_ama_csl_path().read_text(encoding="utf-8"), encoding="utf-8")

    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_TEMPLATE_DOCX", str(manuscript_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_SUPPLEMENTARY_TEMPLATE_DOCX", str(supplementary_template))
    monkeypatch.setenv("DEEPSCIENTIST_FRONTIERS_CSL", str(csl_path))

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="frontiers_family_harvard",
    )

    frontiers_markdown = (
        paper_root / "journal_submissions" / "frontiers_family_harvard" / "frontiers_manuscript.md"
    ).read_text(encoding="utf-8")

    forbidden_prompt_fragments = (
        "[To be completed before submission.]",
        "[Please replace this sentence",
        "[Please add the exact",
        "[Optional; complete",
        "[Revise this statement",
    )
    assert not any(fragment in frontiers_markdown for fragment in forbidden_prompt_fragments)
    assert "Authors: Pending author confirmation before formal submission." in frontiers_markdown
    assert "Consent or waiver statement pending author confirmation before formal submission." in frontiers_markdown
    assert "Author contributions pending author confirmation before formal submission." in frontiers_markdown


def test_create_submission_minimal_package_builds_submission_facing_docx_for_current_draft_shape(
    tmp_path: Path,
) -> None:
    from docx import Document

    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_current_draft_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    compiled_submission_markdown = submission_root / "manuscript_submission.md"
    assert compiled_submission_markdown.exists()

    submission_markdown = compiled_submission_markdown.read_text(encoding="utf-8")
    assert submission_markdown.startswith("---\n")
    assert 'title: "Current Draft Title"' in submission_markdown
    assert "bibliography: ../references.bib" in submission_markdown
    assert "\n# Abstract\n" in submission_markdown
    assert "\n# Conclusion\n" in submission_markdown
    assert not submission_markdown.startswith("# Draft")
    assert manifest["manuscript"]["source_markdown_path"] == "paper/submission_minimal/manuscript_submission.md"

    document = Document(submission_root / "manuscript.docx")
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    assert paragraphs[0] == "Current Draft Title"
    assert "Draft" not in paragraphs[:3]
    assert any("A primary source" in paragraph for paragraph in paragraphs)
    assert not any("ref1?" in paragraph for paragraph in paragraphs)


def test_create_submission_minimal_package_current_draft_falls_back_to_catalog_backed_figures(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_current_draft_workspace(tmp_path)

    dump_json(
        paper_root / "figure_semantics_manifest.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "direct_message": "Catalog-backed fallback keeps the main manuscript figure visible.",
                    "panel_messages": [
                        {
                            "panel_id": "A",
                            "message": "The primary display remains embedded even when the draft omits a Main Figures section.",
                        }
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
    submission_markdown = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "\n# Figures\n" in submission_markdown
    assert "## Figure 1. Main figure" in submission_markdown
    assert "![](../figures/F1_main.png)" in submission_markdown
    assert "Catalog-backed fallback keeps the main manuscript figure visible." in submission_markdown
    assert "Panel A: The primary display remains embedded even when the draft omits a Main Figures section." in submission_markdown

    manuscript_surface_qc = manifest["manuscript"]["surface_qc"]
    assert manuscript_surface_qc["status"] == "pass"
    assert manuscript_surface_qc["source_markdown"]["figure_blocks_with_images"] == 1
    assert manuscript_surface_qc["source_markdown"]["figure_blocks_with_legends"] == 1

    with zipfile.ZipFile(submission_root / "manuscript.docx") as archive:
        names = archive.namelist()
        document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    assert any(name.startswith("word/media/") for name in names)
    assert "<w:drawing" in document_xml

    pdf_reader = PdfReader(str(submission_root / "paper.pdf"))
    assert sum(len(page.images) for page in pdf_reader.pages) >= 1


def test_create_submission_minimal_package_uses_catalog_backed_figures_when_main_figure_section_has_only_legends(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    write_text(
        paper_root / "build" / "review_manuscript.md",
        """---
title: "Legend-only Medical Manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

Legend-only manuscript abstract with evidence [@ref1].

# Main Figures

## Figure 1. Main figure

Caption only. The inline image line was dropped from the reviewer manuscript.

# Main Tables

| Characteristic | Value |
| --- | --- |
| Age | 52 |
""",
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    submission_markdown = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "\n# Figures\n" in submission_markdown
    assert "## Figure 1. Main figure" in submission_markdown
    assert "![](../figures/F1_main.png)" in submission_markdown
    assert "Caption only. The inline image line was dropped from the reviewer manuscript." in submission_markdown
    assert manifest["manuscript"]["surface_qc"]["status"] == "pass"
    assert manifest["manuscript"]["surface_qc"]["source_markdown"]["figure_blocks_with_images"] == 1

    with zipfile.ZipFile(submission_root / "manuscript.docx") as archive:
        names = archive.namelist()
        document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    assert any(name.startswith("word/media/") for name in names)
    assert "<w:drawing" in document_xml


def test_create_submission_minimal_package_supports_short_f_figure_headings_from_review_manuscript(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    write_text(
        paper_root / "build" / "review_manuscript.md",
        """---
title: "Short F Medical Manuscript"
bibliography: ../references.bib
link-citations: true
---

# Abstract

Short-F manuscript abstract with evidence [@ref1].

# Main Figures

## F1. Main figure

Caption retained under the short F heading.

![](../figures/F1_main.png){ width=100% }

# Main Tables

| Characteristic | Value |
| --- | --- |
| Age | 52 |
""",
    )

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    submission_markdown = (submission_root / "manuscript_submission.md").read_text(encoding="utf-8")
    assert "\n# Figures\n" in submission_markdown
    assert "## Figure 1. Main figure" in submission_markdown
    assert "![](../figures/F1_main.png)" in submission_markdown
    assert "Caption retained under the short F heading." in submission_markdown
    assert manifest["manuscript"]["surface_qc"]["status"] == "pass"
    assert manifest["manuscript"]["surface_qc"]["source_markdown"]["figure_blocks_with_images"] == 1
    assert manifest["manuscript"]["surface_qc"]["source_markdown"]["figure_blocks_with_legends"] == 1

    with zipfile.ZipFile(submission_root / "manuscript.docx") as archive:
        names = archive.namelist()
        document_xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    assert any(name.startswith("word/media/") for name in names)
    assert "<w:drawing" in document_xml


def test_inspect_submission_source_markdown_counts_alt_text_inline_figures(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "Submission Manuscript"
---

# Figures

## Figure 1. Main figure

![F1](figures/F1_main.png)

Legend text for the main figure.
""",
    )

    inspection = module.inspect_submission_source_markdown(source_markdown)

    assert inspection["figure_block_count"] == 1
    assert inspection["figure_blocks_with_images"] == 1
    assert inspection["figure_blocks_with_legends"] == 1


def test_inspect_submission_source_markdown_accepts_main_figures_alias(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    source_markdown = tmp_path / "manuscript_submission.md"
    write_text(
        source_markdown,
        """---
title: "Submission Manuscript"
---

# Main Figures

## Figure 1. Main figure

![](figures/F1_main.png)

Legend text for the main figure under the Main Figures alias.
""",
    )

    inspection = module.inspect_submission_source_markdown(source_markdown)

    assert inspection["figure_block_count"] == 1
    assert inspection["figure_blocks_with_images"] == 1
    assert inspection["figure_blocks_with_legends"] == 1
