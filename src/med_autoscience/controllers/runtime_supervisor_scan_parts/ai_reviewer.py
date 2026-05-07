from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def assessment(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    owner = _text(provenance.get("owner"))
    reasons = set(blocking_reasons)
    required = bool(provenance.get("ai_reviewer_required")) or "publication_eval.ai_reviewer_required" in reasons
    present = owner == "ai_reviewer"
    missing = not present and (required or bool(progress.get("quality_review_loop")))
    return {
        "present": present,
        "owner": owner,
        "required": required,
        "missing": missing,
    }


def status(ai_reviewer_assessment: Mapping[str, Any]) -> dict[str, Any]:
    if ai_reviewer_assessment.get("present") is True:
        status_value = "present"
    elif ai_reviewer_assessment.get("missing") is True:
        status_value = "trace_missing"
    else:
        status_value = "not_required"
    return {
        "status": status_value,
        "owner": _text(ai_reviewer_assessment.get("owner")),
        "trace_complete": ai_reviewer_assessment.get("present") is True,
        "blocked_reason": "ai_reviewer_assessment_required" if ai_reviewer_assessment.get("missing") is True else None,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["assessment", "status"]
