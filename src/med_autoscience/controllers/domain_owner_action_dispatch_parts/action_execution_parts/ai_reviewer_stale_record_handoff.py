from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...domain_action_request_lifecycle import (
    AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
    AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
)
from .ai_reviewer_record_production import build_ai_reviewer_record_production_request


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def stale_ai_reviewer_record_handoff(
    *,
    request: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
    lifecycle: Mapping[str, Any],
) -> dict[str, Any] | None:
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if blocked_reason not in {
        AI_REVIEWER_RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN,
        AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT,
    }:
        return None
    record_request_kind = (
        "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
        if blocked_reason == AI_REVIEWER_RECORD_STALE_AFTER_CURRENT_MANUSCRIPT
        else "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization"
    )
    required_currentness_refs = _string_items(lifecycle.get("required_currentness_refs"))
    return {
        "reason": blocked_reason,
        "payload": {
            "stale_record_ref": _text(lifecycle.get("stale_record_ref")),
            "required_currentness_refs": required_currentness_refs,
            "ai_reviewer_record_production_request": build_ai_reviewer_record_production_request(
                request=request,
                required_refs=required_refs,
                stale_record_ref=_text(lifecycle.get("stale_record_ref")),
                required_currentness_refs=required_currentness_refs,
                request_kind=record_request_kind,
            ),
            "next_required_actions": [
                record_request_kind,
                "rematerialize_ai_reviewer_request",
                "return_to_ai_reviewer_workflow",
            ],
        },
    }


__all__ = ["stale_ai_reviewer_record_handoff"]
