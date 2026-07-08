from __future__ import annotations

from typing import Any

from .shared import _display_text, _mapping_copy, _non_empty_text


def quality_review_loop_action_required(
    evaluation_summary_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(evaluation_summary_payload, dict):
        return None
    quality_closure_truth = _mapping_copy(evaluation_summary_payload.get("quality_closure_truth"))
    quality_review_loop = _mapping_copy(evaluation_summary_payload.get("quality_review_loop"))
    if not quality_review_loop:
        return None
    closure_state = _non_empty_text(quality_review_loop.get("closure_state")) or _non_empty_text(
        quality_closure_truth.get("state")
    )
    current_phase = _non_empty_text(quality_review_loop.get("current_phase"))
    if closure_state == "bundle_only_remaining":
        return None
    if closure_state != "quality_repair_required" and current_phase not in {
        "revision_required",
        "re_review_required",
    }:
        return None
    blocking_issues = [
        str(item).strip()
        for item in (quality_review_loop.get("blocking_issues") or [])
        if str(item).strip()
    ]
    next_review_focus = [
        str(item).strip()
        for item in (quality_review_loop.get("next_review_focus") or [])
        if str(item).strip()
    ]
    recommended_next_action = _non_empty_text(quality_review_loop.get("recommended_next_action")) or _display_text(
        quality_review_loop.get("recommended_next_action")
    )
    summary = (
        _non_empty_text(quality_review_loop.get("summary"))
        or _display_text(quality_review_loop.get("summary"))
        or _non_empty_text(quality_closure_truth.get("summary"))
        or _display_text(quality_closure_truth.get("summary"))
    )
    if recommended_next_action is None and summary is None and not blocking_issues:
        return None
    corpus = " ".join([summary or "", recommended_next_action or "", *blocking_issues, *next_review_focus]).lower()
    return {
        "summary": summary,
        "recommended_next_action": recommended_next_action,
        "blocking_issues": blocking_issues,
        "next_review_focus": next_review_focus,
        "mentions_ai_reviewer": any(
            marker in corpus
            for marker in (
                "ai reviewer",
                "ai_reviewer",
                "assessment_provenance.owner=ai_reviewer",
                "reviewer-authored",
            )
        ),
    }
