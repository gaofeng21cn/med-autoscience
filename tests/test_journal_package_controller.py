from __future__ import annotations

import base64
import importlib
import json
from pathlib import Path


PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/x8AAwMCAO+aRX0AAAAASUVORK5CYII="
)


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(PNG_1X1_BASE64))


def make_package_workspace(tmp_path: Path) -> tuple[Path, Path]:
    study_root = tmp_path / "studies" / "001-guideline-aligned-triple-trend"
    paper_root = study_root / "paper"
    write_text(study_root / "study.yaml", "study_id: 001-guideline-aligned-triple-trend\n")
    write_text(paper_root / "submission_minimal" / "manuscript.docx", "docx")
    write_text(paper_root / "submission_minimal" / "paper.pdf", "%PDF-1.4\n")
    write_text(paper_root / "submission_minimal" / "figures" / "Figure1.pdf", "%PDF-1.4\n")
    write_png(paper_root / "submission_minimal" / "figures" / "Figure1.png")
    write_text(paper_root / "submission_minimal" / "tables" / "Table1.csv", "a,b\n1,2\n")
    write_text(paper_root / "submission_minimal" / "tables" / "Table1.md", "| a | b |\n| --- | --- |\n| 1 | 2 |\n")
    dump_json(
        paper_root / "submission_minimal" / "submission_manifest.json",
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
            "front_matter_placeholders": {
                "authors": "pending",
                "ethics": "pending",
            },
            "manuscript": {
                "docx_path": "paper/submission_minimal/manuscript.docx",
                "pdf_path": "paper/submission_minimal/paper.pdf",
            },
        },
    )
    return paper_root, study_root


def test_materialize_journal_package_writes_stable_shallow_package(tmp_path: Path) -> None:
    package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    requirements_module = importlib.import_module("med_autoscience.journal_requirements")
    paper_root, study_root = make_package_workspace(tmp_path)

    requirements_module.write_journal_requirements(
        study_root=study_root,
        requirements=requirements_module.JournalRequirements(
            journal_name="Rheumatology International",
            journal_slug="rheumatology-international",
            official_guidelines_url="https://example.org/ri-guide",
            publication_profile="general_medical_journal",
            abstract_word_cap=250,
            title_word_cap=None,
            keyword_limit=None,
            main_text_word_cap=None,
            main_display_budget=6,
            table_budget=2,
            figure_budget=4,
            supplementary_allowed=True,
            title_page_required=True,
            blinded_main_document=False,
            reference_style_family="AMA",
            required_sections=(),
            declaration_requirements=(),
            submission_checklist_items=(),
            template_assets=(),
        ),
    )

    result = package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug="rheumatology-international",
        publication_profile="general_medical_journal",
    )

    package_root = study_root / "submission_packages" / "rheumatology-international"
    assert result["status"] == "materialized"
    assert (package_root / "main_manuscript.docx").exists()
    assert (package_root / "main_manuscript.pdf").exists()
    assert (package_root / "journal_requirements_snapshot.json").exists()
    assert (package_root / "submission_manifest.json").exists()
    assert (package_root / "SUBMISSION_TODO.md").exists()
    assert (package_root / "rheumatology-international_submission_package.zip").exists()


def test_materialized_journal_package_survives_manuscript_delivery_sync_refresh(tmp_path: Path) -> None:
    package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    requirements_module = importlib.import_module("med_autoscience.journal_requirements")
    delivery_sync = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    paper_root, study_root = make_package_workspace(tmp_path)

    requirements_module.write_journal_requirements(
        study_root=study_root,
        requirements=requirements_module.JournalRequirements(
            journal_name="Rheumatology International",
            journal_slug="rheumatology-international",
            official_guidelines_url="https://example.org/ri-guide",
            publication_profile="general_medical_journal",
            abstract_word_cap=250,
            title_word_cap=None,
            keyword_limit=None,
            main_text_word_cap=None,
            main_display_budget=6,
            table_budget=2,
            figure_budget=4,
            supplementary_allowed=True,
            title_page_required=True,
            blinded_main_document=False,
            reference_style_family="AMA",
            required_sections=(),
            declaration_requirements=(),
            submission_checklist_items=(),
            template_assets=(),
        ),
    )
    package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug="rheumatology-international",
        publication_profile="general_medical_journal",
    )

    delivery_sync.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    assert (
        study_root / "submission_packages" / "rheumatology-international" / "submission_manifest.json"
    ).exists()
