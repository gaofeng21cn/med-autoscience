from __future__ import annotations

import re
from typing import Any, Mapping

AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON = (
    "ai_reviewer_record_manuscript_story_provenance_leakage"
)
AI_REVIEWER_RECORD_STORY_LEAKAGE_NEXT_REQUIRED_ACTIONS = (
    "produce_ai_reviewer_publication_eval_record_against_current_medical_prose_style_v3",
    "rematerialize_ai_reviewer_request",
    "return_to_ai_reviewer_workflow",
)
MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS = frozenset(
    {
        "clinical_significance",
        "novelty_positioning",
    }
)

_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_PATTERNS = (
    re.compile(
        r"\bforegrounds?\b.{0,120}\b(?:data[-\s]?harmonization|unit[-\s]?harmonization|harmonization lesson)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bdefensible contribution\b.{0,120}\bharmonization[-\s]?sensitive\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\breframe novelty\b.{0,120}\bharmonization\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bmanuscript must treat\b.{0,120}\b(?:raw[-\s]?HDL|raw[-\s]?scale|harmonization failure signal)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\braw[-\s]?HDL run\b.{0,120}\bharmonization failure signal\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bunit harmonization changed the central interpretation\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:story|novelty|contribution|main finding|central interpretation)\b.{0,120}\bunit[-\s]?harmoniz(?:ed|ation)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bunit[-\s]?harmoniz(?:ed|ation)\b.{0,120}\b(?:story|novelty|contribution|main finding|central interpretation)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bunit alignment\b.{0,120}\b(?:restor|rescu|explain)\w*\b",
        re.IGNORECASE,
    ),
)
_SENSITIVE_DIMENSION_FIELDS = (
    "summary",
    "reviewer_reason",
    "reviewer_revision_advice",
)
_FUTURE_LIMITATION_FIELDS = (
    "limitation",
    "impact_on_claim",
    "required_future_analysis_data_or_design",
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def detect_manuscript_story_provenance_leakage(*, field_path: str, text: str) -> dict[str, str] | None:
    if not text:
        return None
    for pattern in _MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_PATTERNS:
        if pattern.search(text):
            return {
                "reason": "manuscript_story_provenance_leakage",
                "field_path": field_path,
            }
    return None


def reject_manuscript_story_provenance_leakage(*, field_path: str, text: str) -> None:
    leakage = detect_manuscript_story_provenance_leakage(field_path=field_path, text=text)
    if leakage is not None:
        raise ValueError(
            "AI reviewer publication eval workflow detected manuscript_story_provenance_leakage "
            f"in {field_path}"
        )


def ai_reviewer_record_story_provenance_leakage(record: Mapping[str, Any]) -> dict[str, str] | None:
    quality_assessment = _mapping(record.get("quality_assessment"))
    for dimension in MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS:
        dimension_payload = _mapping(quality_assessment.get(dimension))
        for field in _SENSITIVE_DIMENSION_FIELDS:
            leakage = detect_manuscript_story_provenance_leakage(
                field_path=f"quality_assessment.{dimension}.{field}",
                text=_text(dimension_payload.get(field)),
            )
            if leakage is not None:
                return leakage
    for index, item in enumerate(_list(record.get("future_facing_limitations_plan"))):
        if not isinstance(item, Mapping):
            continue
        for field in _FUTURE_LIMITATION_FIELDS:
            leakage = detect_manuscript_story_provenance_leakage(
                field_path=f"future_facing_limitations_plan[{index}].{field}",
                text=_text(item.get(field)),
            )
            if leakage is not None:
                return leakage
    return None


def ai_reviewer_record_story_provenance_leakage_dispatch_blocker(
    lifecycle: Mapping[str, Any],
) -> dict[str, Any] | None:
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if blocked_reason != AI_REVIEWER_RECORD_MANUSCRIPT_STORY_PROVENANCE_LEAKAGE_BLOCKED_REASON:
        return None
    return {
        "reason": blocked_reason,
        "payload": {
            "stale_record_ref": _text(lifecycle.get("stale_record_ref")),
            "leakage_reason": _text(lifecycle.get("leakage_reason")),
            "leakage_field_path": _text(lifecycle.get("leakage_field_path")),
            "next_required_actions": list(AI_REVIEWER_RECORD_STORY_LEAKAGE_NEXT_REQUIRED_ACTIONS),
        },
    }
