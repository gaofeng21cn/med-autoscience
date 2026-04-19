from __future__ import annotations

import importlib
from pathlib import Path


def test_slugify_journal_name_normalizes_human_title() -> None:
    module = importlib.import_module("med_autoscience.journal_requirements")

    assert module.slugify_journal_name("Rheumatology International") == "rheumatology-international"
    assert module.slugify_journal_name("Journal of Clinical Endocrinology & Metabolism") == (
        "journal-of-clinical-endocrinology-metabolism"
    )


def test_write_and_load_journal_requirements_round_trip(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.journal_requirements")
    study_root = tmp_path / "studies" / "001-guideline-aligned-triple-trend"

    requirements = module.JournalRequirements(
        journal_name="Rheumatology International",
        journal_slug="rheumatology-international",
        official_guidelines_url="https://example.org/ri-guide",
        publication_profile="general_medical_journal",
        abstract_word_cap=250,
        title_word_cap=30,
        keyword_limit=6,
        main_text_word_cap=3500,
        main_display_budget=6,
        table_budget=2,
        figure_budget=4,
        supplementary_allowed=True,
        title_page_required=True,
        blinded_main_document=False,
        reference_style_family="AMA",
        required_sections=("Abstract", "Introduction", "Methods", "Results", "Discussion"),
        declaration_requirements=("Funding", "Conflict of Interest", "Ethics"),
        submission_checklist_items=("title_page", "main_document", "figures"),
        template_assets=(),
    )

    result = module.write_journal_requirements(
        study_root=study_root,
        requirements=requirements,
    )

    assert result["journal_slug"] == "rheumatology-international"
    assert (study_root / "paper" / "journal_requirements" / "rheumatology-international" / "requirements.json").exists()
    assert (study_root / "paper" / "journal_requirements" / "rheumatology-international" / "requirements.md").exists()

    loaded = module.load_journal_requirements(
        study_root=study_root,
        journal_slug="rheumatology-international",
    )

    assert loaded is not None
    assert loaded.abstract_word_cap == 250
    assert loaded.title_page_required is True
    assert loaded.reference_style_family == "AMA"
