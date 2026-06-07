from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
    request_owner_for_action_type,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.owner_route_reconcile_parts import (
    action_decorators,
    domain_route_contract,
    domain_transition_actions,
)
from med_autoscience.runtime_control import owner_route as owner_route_part


def current_actions_for_studies(
    *,
    profile: WorkspaceProfile | None = None,
    scan_payload: Mapping[str, Any],
    study_ids: tuple[str, ...],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]]]:
    ignored: list[dict[str, Any]] = []
    if not study_ids:
        actions = scan_payload.get("action_queue")
        return (list(actions), ignored) if isinstance(actions, list) else (None, ignored)
    per_study_actions: list[dict[str, Any]] = []
    requested = set(study_ids)
    stage_native_actions = _stage_native_next_actions(profile=profile, study_ids=study_ids)
    stage_native_by_study = {
        study_id: action for action in stage_native_actions if (study_id := _text(action.get("study_id"))) is not None
    }
    top_level_actions = [
        dict(action) for action in scan_payload.get("action_queue") or [] if isinstance(action, Mapping)
    ]
    matched_requested_study = False
    for study in scan_payload.get("studies") or []:
        study_payload = _mapping(study)
        study_id = _text(study_payload.get("study_id"))
        if study_id not in requested:
            continue
        matched_requested_study = True
        if study_id in stage_native_by_study:
            per_study_actions.append(stage_native_by_study[study_id])
            ignored.extend(
                _ignored_action(action, "superseded_by_stage_native_next_action")
                for action in [
                    *_top_level_study_actions(study=study_payload, top_level_actions=top_level_actions),
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
            )
            continue
        study_actions, study_ignored = _current_study_actions(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        per_study_actions.extend(study_actions)
        ignored.extend(study_ignored)
    for study_id, action in stage_native_by_study.items():
        if not any(_text(item.get("study_id")) == study_id for item in per_study_actions):
            per_study_actions.append(action)
    if per_study_actions or matched_requested_study:
        return per_study_actions, ignored
    actions = scan_payload.get("action_queue")
    return (list(actions), ignored) if isinstance(actions, list) else (None, ignored)


def _stage_native_next_actions(
    *,
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
) -> list[dict[str, Any]]:
    if profile is None:
        return []
    actions: list[dict[str, Any]] = []
    for study_id in study_ids:
        action = _stage_native_next_action(profile=profile, study_id=study_id)
        if action is not None:
            actions.append(action)
    return actions


def _stage_native_next_action(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    study_root = profile.studies_root / study_id
    next_action = _read_json_mapping(study_root / "control" / "next_action.json")
    if next_action is None:
        return None
    action_type = _text(next_action.get("action_id")) or _text(next_action.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return None
    if _text(next_action.get("status")) != "ready_for_owner_action":
        return None
    owner = _text(next_action.get("owner")) or request_owner_for_action_type(action_type)
    quest_id = _read_quest_id(study_root=study_root, fallback=study_id)
    owner_route = _stage_native_owner_route(
        study_id=study_id,
        quest_id=quest_id,
        action_type=action_type,
        owner=owner,
        next_action=next_action,
    )
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"stage-native-next-action::{study_id}::{action_type}",
        "reason": action_type,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": "stage_native_workspace_next_action",
        "required_output_surface": _text(next_action.get("target_surface"))
        or _text(next_action.get("required_output_surface"))
        or "artifacts/reports/medical_publication_surface/latest.json",
        "source_surface": _text(next_action.get("source_surface")),
        "stage_index_ref": _text(next_action.get("stage_index_ref")),
        "current_stage_id": _text(next_action.get("current_stage_id")),
        "current_package_status": _text(next_action.get("current_package_status")),
        "owner_route": owner_route,
        "handoff_packet": {
            "owner": owner,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "owner_route": owner_route,
            "source_surface": _text(next_action.get("source_surface")),
        },
    }


def _stage_native_owner_route(
    *,
    study_id: str,
    quest_id: str,
    action_type: str,
    owner: str,
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    current_stage_id = _text(next_action.get("current_stage_id")) or "unknown_stage"
    source_surface = _text(next_action.get("source_surface")) or "control/next_action.json"
    fingerprint = f"stage-native-next-action::{current_stage_id}::{action_type}::{source_surface}"
    epoch = f"stage-native-next-action::{study_id}::{current_stage_id}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": epoch,
        "runtime_health_epoch": epoch,
        "work_unit_fingerprint": fingerprint,
        "failure_signature": action_type,
        "trace_id": f"owner-route-trace::{study_id}::{action_type}",
        "route_epoch": epoch,
        "source_fingerprint": fingerprint,
        "current_owner": "mas_controller",
        "next_owner": owner,
        "owner_reason": action_type,
        "active_run_id": None,
        "allowed_actions": [action_type],
        "blocked_actions": sorted(item for item in SUPPORTED_ACTION_TYPES if item != action_type),
        "source_refs": {
            "work_unit_id": action_type,
            "work_unit_fingerprint": fingerprint,
            "source_surface": source_surface,
            "stage_index_ref": _text(next_action.get("stage_index_ref")),
            "current_stage_id": current_stage_id,
            "owner_route_currentness_basis": {
                "truth_epoch": epoch,
                "runtime_health_epoch": epoch,
                "work_unit_id": action_type,
                "work_unit_fingerprint": fingerprint,
            },
        },
        "idempotency_key": f"owner-route::{study_id}::{epoch}::{owner}::{action_type}",
    }


def _read_json_mapping(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _read_quest_id(*, study_root: Path, fallback: str) -> str:
    study_yaml = study_root / "study.yaml"
    try:
        text = study_yaml.read_text(encoding="utf-8")
    except OSError:
        return fallback
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == "quest_id":
            return value.strip().strip("\"'") or fallback
    return fallback


def _current_study_actions(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    top_level_study_actions = _top_level_study_actions(study=study, top_level_actions=top_level_actions)
    queue_actions, queue_source = _study_queue_actions(
        study=study,
        top_level_study_actions=top_level_study_actions,
    )
    current_queue_actions = [
        action for action in queue_actions if _queue_action_allowed_by_current_study_route(action, study)
    ]
    if current_queue_actions:
        return current_queue_actions, []
    transition_actions = _domain_transition_current_actions(study)
    if not transition_actions:
        if queue_source == "per_study_empty":
            return [], [
                _ignored_action(action, "superseded_by_current_study_empty_action_queue")
                for action in top_level_study_actions
            ]
        if _current_execution_is_authoritative(study):
            return [], [
                _ignored_action(action, "superseded_by_current_execution_envelope")
                for action in top_level_study_actions
            ]
        return queue_actions, []
    ignored = [_ignored_action(action, "superseded_by_current_domain_transition") for action in queue_actions]
    if queue_source == "per_study_empty":
        ignored.extend(
            _ignored_action(action, "superseded_by_current_domain_transition")
            for action in top_level_study_actions
        )
    return transition_actions, ignored


def _study_queue_actions(
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
            actions.append(_attach_owner_route_if_missing(payload, owner_route))
        return actions, "per_study" if actions else "per_study_empty"
    if _current_execution_is_authoritative(study):
        return [], "current_execution_envelope"
    for action in top_level_study_actions:
        payload = dict(action)
        if quest_id is not None:
            payload["quest_id"] = _text(payload.get("quest_id")) or quest_id
        actions.append(_attach_owner_route_if_missing(payload, owner_route))
    return actions, "top_level"


def _top_level_study_actions(
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


def _attach_owner_route_if_missing(action: Mapping[str, Any], owner_route: Mapping[str, Any]) -> dict[str, Any]:
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


def _domain_transition_current_actions(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    study_id = _text(study.get("study_id"))
    if study_id is None:
        return []
    generated = domain_transition_actions.actions(study)
    if not generated:
        return []
    quest_id = _text(study.get("quest_id"))
    owner_route = _domain_transition_owner_route(study=study, generated=generated, study_id=study_id, quest_id=quest_id)
    if not owner_route:
        return []
    decorated_actions: list[dict[str, Any]] = []
    for action in generated:
        if not isinstance(action, Mapping):
            continue
        action_type = _text(action.get("action_type"))
        if action_type not in SUPPORTED_ACTION_TYPES:
            continue
        decorated = action_decorators.decorate_action(
            study_id=study_id,
            quest_id=quest_id,
            action=action,
            request_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
            control_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
            forbidden_actions=list(domain_route_contract.SUPERVISION_FORBIDDEN_ACTIONS),
        )
        decorated["study_id"] = study_id
        if quest_id is not None:
            decorated["quest_id"] = quest_id
        routed = owner_route_part.decorate_actions(actions=[decorated], owner_route=owner_route)[0]
        if _action_allowed_by_owner_route(routed, owner_route):
            decorated_actions.append(routed)
    return decorated_actions


def _domain_transition_owner_route(
    *,
    study: Mapping[str, Any],
    generated: list[dict[str, Any]],
    study_id: str,
    quest_id: str | None,
) -> dict[str, Any]:
    transition = _mapping(study.get("domain_transition"))
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if (
        _text(completion.get("status")) in {"consumed", "receipt_consumed", "completed"}
        and _text(transition.get("controller_action")) is not None
        and _mapping(transition.get("next_work_unit"))
    ):
        current_study = _study_with_owner_route_currentness(study, generated=generated)
        return owner_route_part.build_owner_route(
            study_id=study_id,
            quest_id=quest_id,
            status=current_study,
            progress={},
            actions=generated,
            blocked_reason=_text(generated[0].get("reason")),
            next_owner=_text(generated[0].get("owner")) or _text(generated[0].get("request_owner")),
            active_run_id=_text(current_study.get("active_run_id")),
        )
    return owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))


def domain_transition_owner_route_for_study(study: Mapping[str, Any]) -> dict[str, Any]:
    study_payload = _mapping(study)
    study_id = _text(study_payload.get("study_id"))
    if study_id is None:
        return {}
    generated = domain_transition_actions.actions(study_payload)
    if not generated:
        return {}
    return _domain_transition_owner_route(
        study=study_payload,
        generated=generated,
        study_id=study_id,
        quest_id=_text(study_payload.get("quest_id")),
    )


def _queue_action_allowed_by_current_study_route(action: Mapping[str, Any], study: Mapping[str, Any]) -> bool:
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    return bool(owner_route) and _action_allowed_by_owner_route(action, owner_route)


def _action_allowed_by_owner_route(action: Mapping[str, Any], owner_route: Mapping[str, Any]) -> bool:
    action_type = _text(action.get("action_type")) or "unknown_action"
    return owner_route_part.route_allows_action(
        action={
            **dict(action),
            "next_executable_owner": _owner_from_action(action, action_type),
            "action_type": action_type,
        },
        owner_route=owner_route,
    )


def _current_execution_is_authoritative(study: Mapping[str, Any]) -> bool:
    envelope = _mapping(study.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    return state_kind in {
        "typed_blocker",
        "blocked_typed_owner",
        "parked",
        "executable_owner_action",
        "running_provider_attempt",
    }


def _study_with_owner_route_currentness(
    study: Mapping[str, Any],
    *,
    generated: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = dict(study)
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(payload.get("owner_route")))
    if not owner_route or not _owner_route_currentness_applies_to_generated(
        owner_route=owner_route,
        generated=generated,
    ):
        return payload
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(_mapping(owner_route.get("currentness_contract")).get("basis")) or _mapping(
        source_refs.get("owner_route_currentness_basis")
    )
    if "runtime_health_snapshot" not in payload and (runtime_epoch := _text(basis.get("runtime_health_epoch"))):
        payload["runtime_health_snapshot"] = {"runtime_health_epoch": runtime_epoch}
    if "study_truth_snapshot" not in payload:
        truth_epoch = _text(basis.get("truth_epoch")) or _text(owner_route.get("truth_epoch"))
        source_signature = _text(owner_route.get("source_fingerprint"))
        if truth_epoch or source_signature:
            payload["study_truth_snapshot"] = {
                key: value
                for key, value in {
                    "truth_epoch": truth_epoch,
                    "source_signature": source_signature,
                }.items()
                if value is not None
            }
    if "publication_eval" not in payload and (source_eval_id := _text(basis.get("source_eval_id"))):
        payload["publication_eval"] = {"eval_id": source_eval_id}
    return payload


def _owner_route_currentness_applies_to_generated(
    *,
    owner_route: Mapping[str, Any],
    generated: list[dict[str, Any]],
) -> bool:
    if any(_action_allowed_by_owner_route(action, owner_route) for action in generated):
        return True
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(_mapping(owner_route.get("currentness_contract")).get("basis")) or _mapping(
        source_refs.get("owner_route_currentness_basis")
    )
    route_work_unit_id = _text(basis.get("work_unit_id")) or _text(source_refs.get("work_unit_id"))
    route_work_unit_fingerprint = _text(basis.get("work_unit_fingerprint")) or _text(
        source_refs.get("work_unit_fingerprint")
    )
    if route_work_unit_id is None and route_work_unit_fingerprint is None:
        return False
    for action in generated:
        action_work_unit_id = (
            _text(action.get("controller_work_unit_id"))
            or _text(action.get("executable_work_unit"))
            or _work_unit_id(action.get("next_work_unit"))
        )
        action_work_unit_fingerprint = _text(action.get("work_unit_fingerprint"))
        if (
            route_work_unit_id is not None
            and route_work_unit_id == action_work_unit_id
            and (
                _action_allowed_by_owner_route(action, owner_route)
                or _ai_reviewer_record_production_work_unit(action_work_unit_id)
            )
        ):
            return True
        if (
            route_work_unit_fingerprint is not None
            and action_work_unit_fingerprint is not None
            and route_work_unit_fingerprint != action_work_unit_fingerprint
        ):
            continue
        if (
            route_work_unit_fingerprint is not None
            and action_work_unit_fingerprint is not None
            and route_work_unit_fingerprint == action_work_unit_fingerprint
        ):
            return True
    return False


def _ai_reviewer_record_production_work_unit(work_unit_id: str | None) -> bool:
    return work_unit_id in domain_transition_actions.AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS


def _owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or _request_owner_for_action_type(action_type)
    )


def _request_owner_for_action_type(action_type: str) -> str:
    from med_autoscience.controllers.default_executor_action_policy import request_owner_for_action_type

    return request_owner_for_action_type(action_type)


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _ignored_action(action: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "study_id": _text(action.get("study_id")),
        "action_type": _text(action.get("action_type")),
        "action_id": _text(action.get("action_id")),
        "reason": reason,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["current_actions_for_studies", "domain_transition_owner_route_for_study"]
