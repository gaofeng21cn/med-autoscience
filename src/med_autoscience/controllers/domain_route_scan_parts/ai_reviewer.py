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
    request_lifecycle = _mapping(progress.get("ai_reviewer_request_lifecycle"))
    request_state = _text(request_lifecycle.get("state"))
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    owner = _text(provenance.get("owner"))
    if owner == "paper_authority_cutover":
        return {
            "present": False,
            "owner": "ai_reviewer",
            "required": True,
            "missing": True,
            "request_state": request_state or "requested",
            "request_id": _text(request_lifecycle.get("request_id")),
            "request_path": _text(_mapping(request_lifecycle.get("refs")).get("request_path")),
            "blocked_reason": "ai_reviewer_assessment_required",
            "cutover_receipt_ref": _text(publication_eval.get("cutover_receipt_ref")),
        }
    if request_state in {"requested", "assigned"}:
        request_owner = _text(request_lifecycle.get("request_owner")) or "ai_reviewer"
        return {
            "present": False,
            "owner": request_owner,
            "required": True,
            "missing": True,
            "request_state": request_state,
            "request_id": _text(request_lifecycle.get("request_id")),
            "request_path": _text(_mapping(request_lifecycle.get("refs")).get("request_path")),
            "blocked_reason": "ai_reviewer_assessment_required",
        }
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
