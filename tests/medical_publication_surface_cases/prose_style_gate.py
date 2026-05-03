from .shared import *


def test_build_report_blocks_structurally_complete_work_report_prose(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        medical_prose_review_verdict="block",
    )
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
    assert "ai_medical_prose_review_missing_or_incomplete" not in report["blockers"]
    assert "medical_journal_prose_style_not_met" in report["blockers"]
    assert report["medical_journal_prose_style_valid"] is False
    assert report["medical_journal_prose_ai_verdict"] == "block"
    assert report["medical_journal_prose_style_hit_count"] >= 4
    assert report["medical_journal_prose_mechanical_flag_count"] >= 4
    assert any(hit["pattern_id"] == "figure_table_subject_results_sentence" for hit in report["top_hits"])
    assert any(hit["pattern_id"] == "unsupported_no_difference_claim" for hit in report["top_hits"])


def test_build_report_blocks_transportability_framework_jargon_before_export(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    paper_root = _paper_root_from_quest(quest_root)
    framework_text = """
## Introduction

The clinical problem is external validation of mortality risk prediction across diabetes cohorts.

## Materials and Methods

### Study design and cohort

The cohort definition followed the prespecified external validation protocol.

### Variable definition and measurement

Predictors were harmonized across the source datasets.

### Model building

The transportability-first framing used a bounded outcome-scale audit.

### Validation framework

Calibration and discrimination were assessed in the validation cohort.

## Results

### Primary analysis

The validation retained an honest non-zero ordering signal despite clinically shallow absolute-risk separation.

### Secondary analysis

Risk estimates were interpreted within cohort-level calibration limits.

## Discussion

These findings support model recalibration before clinical interpretation.
"""
    (paper_root / "draft.md").write_text(framework_text, encoding="utf-8")
    (paper_root / "build" / "review_manuscript.md").write_text(framework_text, encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))
    analysis_plane_pattern_ids = {
        pattern_id for pattern_id, _, _ in module.medical_surface_policy.get_analysis_plane_jargon_patterns()
    }

    assert report["status"] == "blocked"
    assert "analysis_plane_jargon_present_on_manuscript_surface" in report["blockers"]
    assert report["analysis_plane_jargon_hit_count"] >= 4
    assert "transportability_first_framing" in analysis_plane_pattern_ids
    assert "bounded_outcome_scale_audit" in analysis_plane_pattern_ids
    assert "honest_non_zero" in analysis_plane_pattern_ids
    assert "clinically_shallow" in analysis_plane_pattern_ids


def test_build_report_requires_ai_prose_review_before_subjective_style_closure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        include_medical_prose_review=False,
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "ai_medical_prose_review_missing_or_incomplete" in report["blockers"]
    assert "medical_journal_prose_style_not_met" not in report["blockers"]
    assert report["medical_journal_prose_style_valid"] is False


def test_build_report_blocks_ai_reviewer_backed_work_report_verdict(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        medical_prose_review_verdict="block",
    )

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "blocked"
    assert "medical_journal_prose_style_not_met" in report["blockers"]
    assert report["medical_journal_prose_ai_verdict"] == "block"


def test_build_report_accepts_medical_journal_style_prose(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert report["status"] == "clear"
    assert "medical_journal_prose_style_not_met" not in report["blockers"]
    assert report["medical_journal_prose_style_valid"] is True
    assert report["medical_journal_prose_style_hit_count"] == 0
    assert report["medical_journal_prose_ai_verdict"] == "clear"


def test_build_report_keeps_pattern_hits_as_evidence_when_ai_reviewer_clears_prose(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True, medical_prose_review_verdict="clear")
    paper_root = _paper_root_from_quest(quest_root)
    pattern_hit_text = """
## Introduction

Patients undergoing surgery need a clear clinical framing for postoperative risk interpretation.

## Materials and Methods

### Study design and cohort

The cohort was assembled from consecutive eligible cases.

### Variable definition and measurement

Variables were extracted from the prespecified clinical record.

### Model building

The model was fit using the prespecified predictors.

### Validation framework

Validation used internal resampling.

## Results

### Primary analysis

Figure 1 shows that the model worked well.

## Discussion

The findings support restrained follow-up stratification language within the study limitations.
"""
    (paper_root / "draft.md").write_text(pattern_hit_text, encoding="utf-8")
    (paper_root / "build" / "review_manuscript.md").write_text(pattern_hit_text, encoding="utf-8")

    report = module.build_surface_report(module.build_surface_state(quest_root))

    assert "medical_journal_prose_style_not_met" not in report["blockers"]
    assert report["medical_journal_prose_ai_verdict"] == "clear"
    assert report["medical_journal_prose_mechanical_flag_count"] >= 1
    assert any(hit["pattern_id"] == "figure_table_subject_results_sentence" for hit in report["top_hits"])
