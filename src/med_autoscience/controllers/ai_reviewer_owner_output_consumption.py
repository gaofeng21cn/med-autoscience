from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.controllers.ai_reviewer_record_work_units import (
    AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS,
    CURRENT_MANUSCRIPT_AI_REVIEWER_RECORD_WORK_UNIT,
)
from med_autoscience.controllers.owner_route_reconcile_parts import action_decorators
from med_autoscience.controllers.owner_route_reconcile_parts import ai_reviewer_actions
from med_autoscience.controllers.owner_route_reconcile_parts import domain_transition_actions


def current_request_lifecycle(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    return domain_action_request_lifecycle.project_ai_reviewer_request_lifecycle(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )


def record_consumption_domain_transition_actions(
    *,
    status: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    request_lifecycle: Mapping[str, Any] | None,
) -> list[dict[str, Any]] | None:
    actions = domain_transition_actions.actions(status, publication_eval_payload=publication_eval_payload)
    if actions is None or not _all_ai_reviewer_record_consumption_actions(actions):
        return None
    return [
        with_owner_output_consumption(
            payload=action,
            publication_eval_payload=publication_eval_payload,
            lifecycle=request_lifecycle,
        )
        for action in actions
    ]


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


def ledger_from_lifecycle(
    *,
    lifecycle: Mapping[str, Any] | None,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    payload = _mapping(lifecycle)
    if payload.get("assessment_written") is not True:
        return None
    if _text(payload.get("blocked_reason")) is not None:
        return None
    refs = _mapping(payload.get("refs"))
    record_ref = (
        _text(payload.get("publication_eval_record_ref"))
        or _text(payload.get("assessment_ref"))
        or _text(payload.get("record_ref"))
    )
    if record_ref is None:
        record_ref = _text(refs.get("publication_eval_record_ref")) or _text(refs.get("assessment_ref"))
    if record_ref is None:
        record_ref = _text(_mapping(_mapping(publication_eval_payload).get("assessment_provenance")).get("record_ref"))
    if record_ref is None:
        return None
    eval_id = _text(_mapping(publication_eval_payload).get("eval_id")) or _text(payload.get("eval_id"))
    if eval_id is None:
        return None
    ledger = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "record_ref": record_ref,
        "eval_id": eval_id,
        "consumption_mode": "refs_only_current_ai_reviewer_record",
        "next_action": "honor_ai_reviewer_publication_eval_authority",
    }
    if required_refs := _string_items(payload.get("consumed_currentness_refs")):
        ledger["required_currentness_refs"] = required_refs
    return ledger


def with_owner_output_consumption(
    *,
    payload: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    lifecycle: Mapping[str, Any] | None,
) -> dict[str, Any]:
    result = dict(payload)
    ledger = ledger_from_lifecycle(
        lifecycle=lifecycle,
        publication_eval_payload=publication_eval_payload,
    )
    if ledger is not None:
        result["owner_output_consumption"] = ledger
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _all_ai_reviewer_record_consumption_actions(actions: list[Mapping[str, Any]]) -> bool:
    return bool(actions) and all(_action_work_unit_id(action) in AI_REVIEWER_RECORD_CONSUMPTION_WORK_UNIT_IDS for action in actions)


def _action_work_unit_id(action: Mapping[str, Any]) -> str | None:
    return (
        _text(action.get("controller_work_unit_id"))
        or _text(action.get("executable_work_unit"))
        or _text(action.get("next_work_unit"))
        or _text(_mapping(action.get("next_work_unit")).get("unit_id"))
    )


__all__ = [
    "current_request_lifecycle",
    "current_manuscript_digest_mismatch_action",
    "current_manuscript_record_action",
    "decorate_record_consumption_actions",
    "ledger_from_lifecycle",
    "record_consumption_domain_transition_actions",
    "with_owner_output_consumption",
]
