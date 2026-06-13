from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    current_action_authority,
    domain_transition_current_actions,
    stage_native_next_action,
)
from med_autoscience.runtime_control import owner_route as owner_route_part


def current_study_actions(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
    readiness_action_type: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    study_actions = top_level_study_actions(study=study, top_level_actions=top_level_actions)
    queue_actions, queue_source = study_queue_actions(
        study=study,
        top_level_study_actions=study_actions,
    )
    current_queue_actions = [
        action for action in queue_actions if queue_action_allowed_by_current_study_route(action, study)
    ]
    if current_queue_actions:
        return current_queue_actions, _ignored_actions_superseded_by_readiness_blocker_repair(
            queue_actions=queue_actions,
            selected_actions=current_queue_actions,
            readiness_action_type=readiness_action_type,
        )
    transition_actions = domain_transition_current_actions.current_actions(study)
    if not transition_actions:
        if queue_source == "per_study_empty":
            return [], [
                ignored_action(action, "superseded_by_current_study_empty_action_queue")
                for action in study_actions
            ]
        if current_execution_is_authoritative(study):
            return [], [
                ignored_action(action, "superseded_by_current_execution_envelope")
                for action in study_actions
            ]
        stale_route_actions = [
            action for action in queue_actions if queue_action_disallowed_by_current_study_route(action, study)
        ]
        if stale_route_actions:
            stale_ids = {_action_identity(action) for action in stale_route_actions}
            remaining_actions = [
                action for action in queue_actions if _action_identity(action) not in stale_ids
            ]
            return remaining_actions, [
                ignored_action(action, "superseded_by_current_owner_route_action_queue")
                for action in stale_route_actions
            ]
        return queue_actions, []
    ignored = [ignored_action(action, "superseded_by_current_domain_transition") for action in queue_actions]
    if queue_source == "per_study_empty":
        ignored.extend(
            ignored_action(action, "superseded_by_current_domain_transition")
            for action in study_actions
        )
    return transition_actions, ignored


def current_owner_route_queue_actions(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
    readiness_action_type: str,
) -> list[dict[str, Any]]:
    queue_actions, _queue_source = study_queue_actions(
        study=study,
        top_level_study_actions=top_level_study_actions(
            study=study,
            top_level_actions=top_level_actions,
        ),
    )
    return [
        action
        for action in queue_actions
        if _text(action.get("action_type")) != readiness_action_type
        and queue_action_allowed_by_current_study_route(action, study)
    ]


def study_queue_actions(
    *,
    study: Mapping[str, Any],
    top_level_study_actions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    study_id = _text(study.get("study_id"))
    quest_id = _text(study.get("quest_id"))
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    actions: list[dict[str, Any]] = []
    if "action_queue" in study:
        for action in study.get("action_queue") or []:
            if not isinstance(action, Mapping):
                continue
            payload = dict(action)
            if study_id is not None:
                payload["study_id"] = _text(payload.get("study_id")) or study_id
            if quest_id is not None:
                payload["quest_id"] = _text(payload.get("quest_id")) or quest_id
            actions.append(attach_owner_route_if_missing(payload, owner_route))
        return actions, "per_study" if actions else "per_study_empty"
    if current_execution_is_authoritative(study):
        return [], "current_execution_envelope"
    for action in top_level_study_actions:
        payload = dict(action)
        if quest_id is not None:
            payload["quest_id"] = _text(payload.get("quest_id")) or quest_id
        actions.append(attach_owner_route_if_missing(payload, owner_route))
    return actions, "top_level"


def top_level_study_actions(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    study_id = _text(study.get("study_id"))
    return [
        dict(action)
        for action in top_level_actions
        if isinstance(action, Mapping) and _text(action.get("study_id")) == study_id
    ]


def attach_owner_route_if_missing(action: Mapping[str, Any], owner_route: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(action)
    if not owner_route:
        return payload
    handoff = dict(_mapping(payload.get("handoff_packet")))
    if _mapping(payload.get("owner_route")) or _mapping(handoff.get("owner_route")):
        return payload
    payload["owner_route"] = dict(owner_route)
    handoff["owner_route"] = dict(owner_route)
    if idempotency_key := _text(owner_route.get("idempotency_key")):
        handoff["idempotency_key"] = idempotency_key
    payload["handoff_packet"] = handoff
    return payload


def queue_action_allowed_by_current_study_route(action: Mapping[str, Any], study: Mapping[str, Any]) -> bool:
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    if not owner_route or not current_action_authority.action_allowed_by_owner_route(
        action,
        owner_route,
    ):
        return False
    action_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route"))
        or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    )
    return not action_route or owner_route_part.owner_route_matches(
        dispatch=action,
        current_route=owner_route,
    )


def queue_action_disallowed_by_current_study_route(
    action: Mapping[str, Any],
    study: Mapping[str, Any],
) -> bool:
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    if not owner_route:
        return False
    action_type = _text(action.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return False
    allowed_actions = {_text(item) for item in owner_route.get("allowed_actions") or []}
    allowed_actions.discard(None)
    if bool(allowed_actions) and action_type not in allowed_actions:
        return True
    action_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route"))
        or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    )
    return bool(action_route) and not owner_route_part.owner_route_matches(
        dispatch=action,
        current_route=owner_route,
    )


def current_execution_is_authoritative(study: Mapping[str, Any]) -> bool:
    envelope = _mapping(study.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    return state_kind in {
        "typed_blocker",
        "blocked_typed_owner",
        "parked",
        "executable_owner_action",
        "running_provider_attempt",
    }


def ignored_action(action: Mapping[str, Any], reason: str) -> dict[str, Any]:
    if stage_native_next_action.is_diagnostic_action(action):
        reason = stage_native_next_action.diagnostic_blocked_reason(action)
    return {
        "study_id": _text(action.get("study_id")),
        "action_type": _text(action.get("action_type")),
        "action_id": _text(action.get("action_id")),
        "reason": reason,
    }


def unique_actions(actions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for action in actions:
        identity = _action_identity(action)
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(dict(action))
    return unique


def _ignored_actions_superseded_by_readiness_blocker_repair(
    *,
    queue_actions: list[dict[str, Any]],
    selected_actions: list[dict[str, Any]],
    readiness_action_type: str,
) -> list[dict[str, Any]]:
    if not any(
        _readiness_blocker_derived_repair_action(action, readiness_action_type=readiness_action_type)
        for action in selected_actions
    ):
        return []
    ignored: list[dict[str, Any]] = []
    selected_fingerprints = {
        _text(action.get("work_unit_fingerprint"))
        for action in selected_actions
        if _text(action.get("work_unit_fingerprint")) is not None
    }
    for action in queue_actions:
        if _text(action.get("work_unit_fingerprint")) in selected_fingerprints:
            continue
        if _text(action.get("action_type")) != readiness_action_type:
            continue
        ignored.append(ignored_action(action, "superseded_by_readiness_blocker_derived_repair"))
    return ignored


def _readiness_blocker_derived_repair_action(
    action: Mapping[str, Any],
    *,
    readiness_action_type: str,
) -> bool:
    if _text(action.get("reason")) != "medical_paper_readiness_repair_required":
        return False
    return _text(action.get("readiness_blocker_followup_superseded")) == readiness_action_type


def _action_identity(action: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    return (
        _text(action.get("study_id")),
        _text(action.get("action_type")),
        _text(action.get("action_id")),
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "attach_owner_route_if_missing",
    "current_execution_is_authoritative",
    "current_owner_route_queue_actions",
    "current_study_actions",
    "ignored_action",
    "top_level_study_actions",
    "unique_actions",
]
