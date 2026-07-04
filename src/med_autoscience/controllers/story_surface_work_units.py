from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
    UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS,
)
from med_autoscience.controllers.next_action_envelope import (
    FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL,
    FAMILY_PAPER_WRITE_PROSE_REPAIR,
)

CANONICAL_ACTION_FAMILY_PAPER_WRITE = FAMILY_PAPER_WRITE_PROSE_REPAIR
CANONICAL_ACTION_FAMILY_SUBMISSION_MATERIALIZE = FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL

PAPER_WRITE_ACTION_FAMILIES = frozenset(
    {
        FAMILY_PAPER_WRITE_PROSE_REPAIR,
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
        FAMILY_PAPER_PACKAGE_SUBMISSION_MINIMAL,
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
        "medical_methods_and_registry_reporting_repair",
        "treatment_gap_reporting_repair",
    }
)
CLAIM_EVIDENCE_ALIGNMENT_WRITE_WORK_UNIT_IDS = frozenset(
    {
        "claim_evidence_alignment_repair",
        "current_manuscript_claim_evidence_alignment_repair",
    }
)
SUBMISSION_PACKAGE_WORK_UNIT_IDS = frozenset(
    {
        "controller_owned_publication_repair",
        "submission_authority_sync_closure",
        "submission_delivery_sync_closure",
        "submission_minimal_refresh",
    }
)
PUBLICATION_GATE_REPLAY_ROUTE_FAMILY_WORK_UNIT_IDS = frozenset(
    unit_id
    for unit_id in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
    if unit_id != "ai_reviewer_record_gate_consumption"
)
AI_REVIEWER_QUALITY_AUTHORITY_WORK_UNIT_IDS = frozenset(
    {
        "ai_reviewer_recheck",
        "ai_reviewer_medical_prose_quality_review",
        "produce_ai_reviewer_publication_eval_record_against_current_analysis_harmonization",
        "produce_ai_reviewer_publication_eval_record_against_current_inputs",
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
    for unit_id in _candidate_work_unit_ids(payload):
        if unit_id in SUBMISSION_PACKAGE_WORK_UNIT_IDS or unit_id in PUBLICATION_GATE_REPLAY_ROUTE_FAMILY_WORK_UNIT_IDS:
            return CANONICAL_ACTION_FAMILY_SUBMISSION_MATERIALIZE
        if (
            is_story_surface_delta_write_work_unit(unit_id)
            or is_claim_evidence_alignment_write_work_unit(unit_id)
            or unit_id in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS
            or unit_id in AI_REVIEWER_QUALITY_AUTHORITY_WORK_UNIT_IDS
        ):
            return CANONICAL_ACTION_FAMILY_PAPER_WRITE
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


def _candidate_work_unit_ids(payload: object) -> list[str]:
    mapping = _mapping(payload)
    if not mapping:
        return []
    candidates: list[str] = []
    for key in ("work_unit_id", "unit_id", "next_work_unit", "controller_next_work_unit"):
        value = mapping.get(key)
        if isinstance(value, Mapping):
            candidates.extend(_candidate_work_unit_ids(value))
        elif text := _text(value):
            candidates.append(text)
    for key in (
        "current_work_unit_binding",
        "current_work_unit",
        "work_unit",
        "owner_route",
        "source_action",
        "repair_work_unit",
    ):
        value = mapping.get(key)
        if isinstance(value, Mapping):
            candidates.extend(_candidate_work_unit_ids(value))
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
    "SUBMISSION_PACKAGE_WORK_UNIT_IDS",
    "PUBLICATION_GATE_REPLAY_ROUTE_FAMILY_WORK_UNIT_IDS",
    "AI_REVIEWER_QUALITY_AUTHORITY_WORK_UNIT_IDS",
    "action_family_is_paper_write",
    "action_family_is_story_surface_write",
    "action_family_is_submission_materialize",
    "canonical_action_family",
    "is_claim_evidence_alignment_write_work_unit",
    "is_story_surface_delta_write_work_unit",
]
