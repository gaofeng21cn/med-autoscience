from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.study_task_intake import read_latest_task_intake, task_intake_is_reviewer_revision


def assessment(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
    blocking_reasons: list[str],
    study_root: Path | None = None,
) -> dict[str, Any]:
    request_lifecycle = _mapping(progress.get("ai_reviewer_request_lifecycle"))
    if not request_lifecycle and study_root is not None:
        request_lifecycle = _mapping(
            domain_action_request_lifecycle.project_ai_reviewer_request_lifecycle(
                study_root=study_root,
                publication_eval_payload=publication_eval,
            )
        )
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
    stale_revision = _stale_after_reviewer_revision(
        study_root=study_root,
        publication_eval=publication_eval,
        owner=owner,
    )
    if stale_revision is not None:
        return stale_revision
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
        "blocked_reason": (
            _text(ai_reviewer_assessment.get("blocked_reason")) or "ai_reviewer_assessment_required"
            if ai_reviewer_assessment.get("missing") is True
            else None
        ),
    }


def _stale_after_reviewer_revision(
    *,
    study_root: Path | None,
    publication_eval: Mapping[str, Any],
    owner: str | None,
) -> dict[str, Any] | None:
    if owner != "ai_reviewer" or study_root is None:
        return None
    task_intake = read_latest_task_intake(study_root=study_root)
    if not task_intake_is_reviewer_revision(task_intake):
        return None
    task_emitted_at = _surface_emitted_at(task_intake)
    if task_emitted_at is None:
        return None
    publication_eval_emitted_at = _surface_emitted_at(publication_eval)
    if publication_eval_emitted_at is not None and publication_eval_emitted_at >= task_emitted_at:
        return None
    return {
        "present": False,
        "owner": "ai_reviewer",
        "required": True,
        "missing": True,
        "blocked_reason": "ai_reviewer_assessment_stale_after_reviewer_revision",
        "task_id": _text(task_intake.get("task_id")),
        "task_emitted_at": _text(task_intake.get("emitted_at") or task_intake.get("generated_at") or task_intake.get("created_at")),
        "publication_eval_emitted_at": _text(
            publication_eval.get("emitted_at") or publication_eval.get("generated_at") or publication_eval.get("created_at")
        ),
    }


def _surface_emitted_at(payload: Mapping[str, Any]) -> datetime | None:
    return _timestamp(payload.get("emitted_at") or payload.get("generated_at") or payload.get("created_at"))


def _timestamp(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["assessment", "status"]
