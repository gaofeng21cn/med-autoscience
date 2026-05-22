from __future__ import annotations

from collections.abc import Mapping
from typing import Any


STALE_AFTER_REVIEWER_REVISION_REASON = "ai_reviewer_assessment_stale_after_reviewer_revision"
ANALYSIS_HARMONIZATION_COMPLETED_REVIEW_REASON = "analysis_harmonization_completed_ai_reviewer_review_required"
RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON = "ai_reviewer_record_stale_after_current_manuscript"
RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN_REASON = "ai_reviewer_record_stale_after_unit_harmonized_rerun"


def ai_reviewer_required_action(*, reason: str) -> dict[str, Any]:
    return {
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "request_owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": reason,
        "summary": "Request an AI reviewer-owned publication_eval assessment.",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "paper_package_mutation_allowed": False,
    }


def stale_reviewer_revision_required(ai_reviewer_assessment: Mapping[str, Any]) -> bool:
    return (
        ai_reviewer_assessment.get("missing") is True
        and _text(ai_reviewer_assessment.get("blocked_reason")) == STALE_AFTER_REVIEWER_REVISION_REASON
    )


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ANALYSIS_HARMONIZATION_COMPLETED_REVIEW_REASON",
    "RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON",
    "RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN_REASON",
    "STALE_AFTER_REVIEWER_REVISION_REASON",
    "ai_reviewer_required_action",
    "stale_reviewer_revision_required",
]
