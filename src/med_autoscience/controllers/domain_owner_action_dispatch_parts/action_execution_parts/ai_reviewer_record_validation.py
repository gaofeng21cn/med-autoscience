from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_AI_REVIEWER_REQUIRED_RECORD_FIELDS = (
    "quality_assessment",
    "future_facing_limitations_plan",
)
_AI_REVIEWER_REQUIRED_REVIEWER_OS_FIELDS = (
    "input_bundle",
    "rubric_scores",
    "decision_matrix",
    "provenance_checks",
    "route_back_decision",
    "future_facing_limitations_plan",
)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def ai_reviewer_record_blocker(record: Mapping[str, Any]) -> dict[str, Any] | None:
    if not request_record_owner_acceptable(record):
        return {
            "reason": "ai_reviewer_record_missing",
            "payload": {
                "owner_record_requirements": ai_reviewer_record_requirements(),
            },
        }
    missing_fields = missing_ai_reviewer_record_fields(record)
    if missing_fields:
        return {
            "reason": "ai_reviewer_record_incomplete",
            "payload": {
                "missing_record_fields": missing_fields,
                "owner_record_requirements": ai_reviewer_record_requirements(),
            },
        }
    return None


def ai_reviewer_owned_record(record: Mapping[str, Any]) -> bool:
    provenance = _mapping(record.get("assessment_provenance"))
    return (
        _text(provenance.get("owner")) == "ai_reviewer"
        and _text(provenance.get("source_kind")) == "publication_eval_ai_reviewer"
        and provenance.get("ai_reviewer_required") is False
    )


def request_record_owner_acceptable(record: Mapping[str, Any]) -> bool:
    provenance = _mapping(record.get("assessment_provenance"))
    if not provenance:
        return True
    return ai_reviewer_owned_record(record)


def missing_ai_reviewer_record_fields(record: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    quality_assessment = record.get("quality_assessment")
    if not isinstance(quality_assessment, Mapping):
        missing.append("quality_assessment")
    future_plan = record.get("future_facing_limitations_plan")
    if not isinstance(future_plan, list) or not future_plan:
        missing.append("future_facing_limitations_plan")
    return missing


def ai_reviewer_record_requirements() -> dict[str, list[str]]:
    return {
        "required_record_fields": list(_AI_REVIEWER_REQUIRED_RECORD_FIELDS),
        "required_reviewer_operating_system_fields": list(_AI_REVIEWER_REQUIRED_REVIEWER_OS_FIELDS),
    }


__all__ = [
    "ai_reviewer_record_blocker",
    "ai_reviewer_record_requirements",
    "ai_reviewer_owned_record",
    "missing_ai_reviewer_record_fields",
]
