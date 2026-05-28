from __future__ import annotations


STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS = frozenset(
    {
        "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
        "dm002_current_publication_hardening_after_ai_reviewer_eval",
        "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
        "dm002_current_manuscript_reporting_consistency_write_repair",
        "dm002_same_line_publication_paper_repair",
        "dm002_same_line_display_table_package_repair",
        "dm002_same_line_methods_display_package_repair",
        "manuscript_story_repair",
        "medical_prose_write_repair",
        "treatment_gap_reporting_repair",
    }
)
CLAIM_EVIDENCE_ALIGNMENT_WRITE_WORK_UNIT_IDS = frozenset(
    {
        "claim_evidence_alignment_repair",
        "current_manuscript_claim_evidence_alignment_repair",
    }
)


def is_story_surface_delta_write_work_unit(unit_id: object) -> bool:
    return str(unit_id or "").strip() in STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS


def is_claim_evidence_alignment_write_work_unit(unit_id: object) -> bool:
    return str(unit_id or "").strip() in CLAIM_EVIDENCE_ALIGNMENT_WRITE_WORK_UNIT_IDS


__all__ = [
    "STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS",
    "CLAIM_EVIDENCE_ALIGNMENT_WRITE_WORK_UNIT_IDS",
    "is_claim_evidence_alignment_write_work_unit",
    "is_story_surface_delta_write_work_unit",
]
