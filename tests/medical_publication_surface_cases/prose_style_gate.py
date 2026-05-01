from .shared import *


def test_build_report_blocks_structurally_complete_work_report_prose(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    paper_root = _paper_root_from_quest(quest_root)
    work_report_text = """
## Introduction

This project has completed the cohort extraction and analysis surface preparation for the current manuscript package.

The first clinical question was whether the model improved the comparison. The answer was yes, and the current bundle now has the required figures and tables.

We therefore report the controller-approved manuscript route and keep the remaining submission tasks outside the current package.

## Materials and Methods

### Study design and cohort

The cohort was assembled from the locked project workspace.

### Variable definition and measurement

Variables were checked through the controller checklist and current analysis surface.

### Model building

The model registry was refreshed before the writing route continued.

### Validation framework

Validation outputs were synchronized into the paper bundle.

## Results

### Primary analysis

Figure 1 shows that the model worked well. Table 1 summarizes the results.

### Secondary analysis

There was no difference between the groups, and the manuscript remains ready for review.

## Discussion

The manuscript should be read as a controlled analysis surface with a bounded claim route.

This is the best model for clinical use.

Limitations are recorded in the claim boundary surface.
"""
    (paper_root / "draft.md").write_text(work_report_text, encoding="utf-8")
    (paper_root / "build" / "review_manuscript.md").write_text(work_report_text, encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "medical_journal_prose_style_not_met" in report["blockers"]
    assert report["medical_journal_prose_style_valid"] is False
    assert report["medical_journal_prose_style_hit_count"] >= 4
    assert any(hit["pattern_id"] == "figure_table_subject_results_sentence" for hit in report["top_hits"])
    assert any(hit["pattern_id"] == "unsupported_no_difference_claim" for hit in report["top_hits"])


def test_build_report_accepts_medical_journal_style_prose(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "medical_journal_prose_style_not_met" not in report["blockers"]
    assert report["medical_journal_prose_style_valid"] is True
    assert report["medical_journal_prose_style_hit_count"] == 0
