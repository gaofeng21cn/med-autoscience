from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CANONICAL_ACTION_FAMILY_PAPER_WRITE = "paper_write"
CANONICAL_ACTION_FAMILY_SUBMISSION_MATERIALIZE = "submission_materialize"

PAPER_WRITE_ACTION_FAMILIES = frozenset(
    {
        "paper_write",
        "write",
        "write_repair",
        "prose_repair",
        "story_repair",
        "paper_story_repair",
        "manuscript_story_repair",
        "medical_prose_write_repair",
        "medical_prose_quality_repair",
        "quality_repair",
    }
)
SUBMISSION_MATERIALIZE_ACTION_FAMILIES = frozenset(
    {
        "submission_materialize",
        "submission_package",
        "submission_package_materialize",
        "submission_minimal",
        "submission_refresh",
        "submission_authority_sync",
        "submission_delivery_sync",
    }
)

STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS = frozenset(
    {
        "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
        "dm002_after_story_repair_medical_prose_hardening",
        "dm002_current_publication_hardening_after_ai_reviewer_eval",
        "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
        "dm002_current_manuscript_reporting_consistency_write_repair",
        "dm002_medical_prose_write_repair_after_quality_batch",
        "dm002_same_line_publication_paper_repair",
        "dm002_same_line_display_table_package_repair",
        "dm002_same_line_methods_display_package_repair",
        "dm003_publication_gate_replay_after_current_ai_reviewer_record",
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "dm003_medical_prose_authority_revise",
        "consume_current_ai_reviewer_record_then_replay_publication_gate",
        "manuscript_story_repair",
        "medical_prose_and_publishability_gate_repair",
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


def canonical_action_family(payload: object) -> str | None:
    for family in _candidate_action_families(payload):
        if action_family_is_paper_write(family):
            return CANONICAL_ACTION_FAMILY_PAPER_WRITE
        if action_family_is_submission_materialize(family):
            return CANONICAL_ACTION_FAMILY_SUBMISSION_MATERIALIZE
    return None


def action_family_is_paper_write(family: object) -> bool:
    return _family_text(family) in PAPER_WRITE_ACTION_FAMILIES


def action_family_is_submission_materialize(family: object) -> bool:
    return _family_text(family) in SUBMISSION_MATERIALIZE_ACTION_FAMILIES


def action_family_is_story_surface_write(family: object) -> bool:
    return _family_text(family) in PAPER_WRITE_ACTION_FAMILIES


def _candidate_action_families(payload: object) -> list[str]:
    mapping = _mapping(payload)
    if not mapping:
        return []
    candidates: list[str] = []
    for key in ("action_family", "canonical_action_family", "owner_action_family"):
        if text := _text(mapping.get(key)):
            candidates.append(text)
    for key in (
        "next_action",
        "next_work_unit",
        "current_work_unit_binding",
        "current_work_unit",
        "work_unit",
        "owner_route",
        "source_action",
        "repair_work_unit",
    ):
        value = mapping.get(key)
        if isinstance(value, Mapping):
            candidates.extend(_candidate_action_families(value))
    return _dedupe_text(candidates)


def _family_text(value: object) -> str | None:
    text = _text(value)
    return text.replace("-", "_").lower() if text is not None else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _dedupe_text(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "CANONICAL_ACTION_FAMILY_PAPER_WRITE",
    "CANONICAL_ACTION_FAMILY_SUBMISSION_MATERIALIZE",
    "PAPER_WRITE_ACTION_FAMILIES",
    "SUBMISSION_MATERIALIZE_ACTION_FAMILIES",
    "STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS",
    "CLAIM_EVIDENCE_ALIGNMENT_WRITE_WORK_UNIT_IDS",
    "action_family_is_paper_write",
    "action_family_is_story_surface_write",
    "action_family_is_submission_materialize",
    "canonical_action_family",
    "is_claim_evidence_alignment_write_work_unit",
    "is_story_surface_delta_write_work_unit",
]
