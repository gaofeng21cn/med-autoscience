from __future__ import annotations

from typing import Any

from med_autoscience.study_task_intake_revision import task_intake_is_reviewer_revision


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _integer_value(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _mapping_value(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def evaluation_summary_has_open_reviewer_first_blockers(
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    if not isinstance(evaluation_summary, dict):
        return False
    study_quality_truth = _mapping_value(evaluation_summary.get("study_quality_truth"))
    reviewer_first = _mapping_value(study_quality_truth.get("reviewer_first"))
    if not reviewer_first:
        return False
    if reviewer_first.get("ready") is True:
        return False
    status = _non_empty_text(reviewer_first.get("status"))
    if status in {"ready", "clear", "closed", "complete", "completed"}:
        return False
    open_concern_count = _integer_value(reviewer_first.get("open_concern_count"))
    if open_concern_count is not None:
        return open_concern_count > 0
    return reviewer_first.get("ready") is False and status in {
        "blocked",
        "partial",
        "review_required",
        "needs_review",
        "not_ready",
    }


def reviewer_revision_has_open_reviewer_first_blockers(
    payload: dict[str, Any] | None,
    *,
    evaluation_summary: dict[str, Any] | None,
) -> bool:
    return task_intake_is_reviewer_revision(payload) and evaluation_summary_has_open_reviewer_first_blockers(
        evaluation_summary
    )
