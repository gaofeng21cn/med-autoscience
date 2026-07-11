from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.ai_reviewer_record_work_units import (
    CURRENT_MANUSCRIPT_AI_REVIEWER_RECORD_WORK_UNIT,
)
from med_autoscience.controllers.paper_mission_owner_surface import action_decorators
from med_autoscience.controllers.paper_mission_owner_surface import ai_reviewer_actions


def decorate_record_consumption_actions(
    *,
    study_id: str,
    quest_id: str | None,
    actions: list[Mapping[str, Any]] | None,
    request_allowed_write_surfaces: list[str],
    control_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
) -> list[dict[str, Any]] | None:
    if actions is None:
        return None
    return [
        action_decorators.decorate_action(
            study_id=study_id,
            quest_id=quest_id,
            action=action,
            request_allowed_write_surfaces=request_allowed_write_surfaces,
            control_allowed_write_surfaces=control_allowed_write_surfaces,
            forbidden_actions=forbidden_actions,
        )
        for action in actions
    ]


def current_manuscript_record_action(
    ai_reviewer_assessment: Mapping[str, Any],
) -> dict[str, Any]:
    action = ai_reviewer_actions.ai_reviewer_required_action(
        reason=ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON
    )
    action["summary"] = (
        "The request-bound AI reviewer record predates the current manuscript; produce a new AI reviewer "
        "publication-eval record against the current manuscript before refreshing publication_eval/latest.json."
    )
    return _record_production_action(
        action=action,
        work_unit_id=CURRENT_MANUSCRIPT_AI_REVIEWER_RECORD_WORK_UNIT,
        required_refs=_string_items(ai_reviewer_assessment.get("required_currentness_refs")),
        stale_record_ref=_text(ai_reviewer_assessment.get("stale_record_ref")),
        source_ref=_text(ai_reviewer_assessment.get("source_ref")),
    )


def current_inputs_record_action(
    ai_reviewer_assessment: Mapping[str, Any],
) -> dict[str, Any]:
    action = ai_reviewer_actions.ai_reviewer_required_action(
        reason=ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_INPUTS_REASON
    )
    action["summary"] = (
        "The request-bound AI reviewer record predates current paper inputs; produce a new AI reviewer "
        "publication-eval record against the current inputs before refreshing publication_eval/latest.json."
    )
    return _record_production_action(
        action=action,
        work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        required_refs=_string_items(ai_reviewer_assessment.get("required_currentness_refs")),
        stale_record_ref=_text(ai_reviewer_assessment.get("stale_record_ref")),
        source_ref=_text(ai_reviewer_assessment.get("source_ref")),
    )


def current_manuscript_digest_mismatch_action(
    controller_route: Mapping[str, Any],
) -> dict[str, Any]:
    action = ai_reviewer_actions.ai_reviewer_required_action(
        reason=ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON
    )
    action["summary"] = (
        "The quality repair batch found that the AI reviewer-bound manuscript digest no longer matches "
        "the canonical manuscript; produce a current AI reviewer publication-eval record before any "
        "writer redrive."
    )
    action = _record_production_action(
        action=action,
        work_unit_id=CURRENT_MANUSCRIPT_AI_REVIEWER_RECORD_WORK_UNIT,
        required_refs=_string_items(controller_route.get("required_currentness_refs")),
        stale_record_ref=_text(controller_route.get("stale_record_ref")),
        source_ref=_text(controller_route.get("source_ref")),
    )
    action["controller_route"] = dict(controller_route)
    action["work_unit_fingerprint"] = _text(controller_route.get("work_unit_fingerprint"))
    action["source_eval_id"] = _text(controller_route.get("publication_eval_id"))
    return action


def _record_production_action(
    *,
    action: dict[str, Any],
    work_unit_id: str,
    required_refs: list[str],
    stale_record_ref: str | None,
    source_ref: str | None,
) -> dict[str, Any]:
    action["required_output_surface"] = "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    action["next_work_unit"] = work_unit_id
    action["executable_work_unit"] = work_unit_id
    action["controller_work_unit_id"] = work_unit_id
    action["publication_eval_latest_write_allowed"] = False
    action["controller_decision_write_allowed"] = False
    action["record_only_surface"] = True
    if required_refs:
        action["required_currentness_refs"] = required_refs
    if stale_record_ref:
        action["stale_record_ref"] = stale_record_ref
    if source_ref:
        action["source_ref"] = source_ref
    return action


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "current_inputs_record_action",
    "current_manuscript_digest_mismatch_action",
    "current_manuscript_record_action",
    "decorate_record_consumption_actions",
]
