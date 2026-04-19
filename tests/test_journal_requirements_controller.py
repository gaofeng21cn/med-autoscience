from __future__ import annotations

import importlib
from pathlib import Path


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_resolve_journal_requirements_controller_writes_durable_outputs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.journal_requirements")
    study_root = tmp_path / "studies" / "001-guideline-aligned-triple-trend"
    write_text(study_root / "study.yaml", "study_id: 001-guideline-aligned-triple-trend\n")

    result = module.resolve_journal_requirements(
        study_root=study_root,
        journal_name="Rheumatology International",
        official_guidelines_url="https://example.org/ri-guide",
        publication_profile="general_medical_journal",
        requirements_payload={
            "abstract_word_cap": 250,
            "title_word_cap": 30,
            "keyword_limit": 6,
            "main_display_budget": 6,
            "table_budget": 2,
            "figure_budget": 4,
            "supplementary_allowed": True,
            "title_page_required": True,
            "blinded_main_document": False,
            "reference_style_family": "AMA",
            "required_sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"],
            "declaration_requirements": ["Funding", "Conflict of Interest", "Ethics"],
            "submission_checklist_items": ["title_page", "main_document", "figures"],
        },
    )

    assert result["status"] == "resolved"
    assert result["journal_slug"] == "rheumatology-international"
    assert result["requirements_path"].endswith("requirements.json")
    assert result["requirements_markdown_path"].endswith("requirements.md")


def test_resolve_journal_requirements_controller_can_use_explicit_slug(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.journal_requirements")
    study_root = tmp_path / "studies" / "001-guideline-aligned-triple-trend"
    write_text(study_root / "study.yaml", "study_id: 001-guideline-aligned-triple-trend\n")

    result = module.resolve_journal_requirements(
        study_root=study_root,
        journal_slug="rheumatology-international",
        journal_name="Rheumatology International",
        official_guidelines_url="https://example.org/ri-guide",
        requirements_payload={"abstract_word_cap": 250},
    )

    assert result["journal_slug"] == "rheumatology-international"
