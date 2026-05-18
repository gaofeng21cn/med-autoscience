from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any


ROUTED_ACTION_TYPES = (
    "runtime_platform_repair",
    "publication_gate_specificity_required",
    "current_package_freshness_required",
    "artifact_display_surface_materialization_required",
    "return_to_ai_reviewer_workflow",
    "canonical_paper_inputs_rehydrate_required",
)
ALLOWED_ACTION_TYPES = (
    *ROUTED_ACTION_TYPES,
    "unit_harmonized_external_validation_rerun",
    "recover_transport_model_provenance",
    "methodology_reframe_route_decision",
)


def build_owner_route(
    *,
    study_id: str,
    quest_id: str | None,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: Iterable[Mapping[str, Any]],
    blocked_reason: str | None,
    next_owner: str | None,
    active_run_id: str | None,
) -> dict[str, Any]:
    normalized_actions = [dict(action) for action in actions]
    owner = next_owner or _owner_from_actions(normalized_actions)
    allowed_actions = [
        action_type
        for action_type in ALLOWED_ACTION_TYPES
        if any(
            _text(action.get("action_type")) == action_type
            and _action_matches_route_owner(action=action, route_owner=owner)
            for action in normalized_actions
        )
    ]
    owner_reason = blocked_reason or _reason_from_actions(normalized_actions)
    truth = _mapping(status.get("study_truth_snapshot")) or _mapping(progress.get("study_truth_snapshot"))
    route_epoch = _text(truth.get("truth_epoch")) or _text(truth.get("authority_epoch")) or _fallback_epoch(
        status=status,
        progress=progress,
    )
    source_fingerprint = _text(truth.get("source_signature")) or _source_fingerprint(
        status=status,
        progress=progress,
        actions=normalized_actions,
        allowed_actions=allowed_actions,
        owner=owner,
        owner_reason=owner_reason,
    )
    current_owner = _current_owner(status=status, progress=progress, active_run_id=active_run_id)
    route = {
        "surface": "runtime_supervisor_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": route_epoch,
        "runtime_health_epoch": _runtime_health_epoch(status, progress),
        "work_unit_fingerprint": _work_unit_fingerprint(
            status=status,
            progress=progress,
            actions=normalized_actions,
            source_fingerprint=source_fingerprint,
        ),
        "failure_signature": owner_reason,
        "trace_id": _trace_id(
            study_id=study_id,
            route_epoch=route_epoch,
            source_fingerprint=source_fingerprint,
            next_owner=owner,
            owner_reason=owner_reason,
        ),
        "route_epoch": route_epoch,
        "source_fingerprint": source_fingerprint,
        "current_owner": current_owner,
        "next_owner": owner,
        "owner_reason": owner_reason,
        "active_run_id": active_run_id,
        "allowed_actions": allowed_actions,
        "blocked_actions": [action for action in ROUTED_ACTION_TYPES if action not in set(allowed_actions)],
        "idempotency_scope": "study_quest_owner_route",
        "source_refs": {
            "study_truth_epoch": _text(truth.get("truth_epoch")),
            "runtime_health_epoch": _runtime_health_epoch(status, progress),
            "publication_eval_path": _text(_mapping(progress.get("refs")).get("publication_eval_path")),
            "quest_root": _text(status.get("quest_root")) or _text(progress.get("quest_root")),
            "study_macro_state": _macro_state_source_ref(status, progress),
        },
    }
    route["idempotency_key"] = _idempotency_key(
        study_id=study_id,
        route_epoch=route_epoch,
        source_fingerprint=source_fingerprint,
        next_owner=owner,
        owner_reason=owner_reason,
        allowed_actions=allowed_actions,
    )
    return route


def decorate_actions(*, actions: Iterable[Mapping[str, Any]], owner_route: Mapping[str, Any]) -> list[dict[str, Any]]:
    normalized_route = ensure_owner_route_v2(owner_route)
    decorated: list[dict[str, Any]] = []
    for action in actions:
        payload = dict(action)
        payload["owner_route"] = dict(normalized_route)
        handoff_packet = dict(_mapping(payload.get("handoff_packet")))
        handoff_packet["owner_route"] = dict(normalized_route)
        handoff_packet["idempotency_key"] = _text(normalized_route.get("idempotency_key"))
        payload["handoff_packet"] = handoff_packet
        decorated.append(payload)
    return decorated


def ensure_owner_route_v2(route: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(route)
    if not payload:
        return {}
    route_epoch = _text(payload.get("truth_epoch")) or _text(payload.get("route_epoch")) or "unknown"
    source_fingerprint = _text(payload.get("source_fingerprint")) or _text(payload.get("idempotency_key")) or route_epoch
    owner_reason = _text(payload.get("failure_signature")) or _text(payload.get("owner_reason"))
    next_owner = _text(payload.get("next_owner"))
    source_refs = _mapping(payload.get("source_refs"))
    runtime_health_epoch = _text(payload.get("runtime_health_epoch")) or _text(source_refs.get("runtime_health_epoch"))
    work_unit_fingerprint = _text(payload.get("work_unit_fingerprint")) or source_fingerprint
    payload.update(
        {
            "schema_version": 2,
            "truth_epoch": route_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_fingerprint": work_unit_fingerprint,
            "failure_signature": owner_reason,
            "trace_id": _text(payload.get("trace_id"))
            or _trace_id(
                study_id=_text(payload.get("study_id")) or "unknown-study",
                route_epoch=route_epoch,
                source_fingerprint=source_fingerprint,
                next_owner=next_owner,
                owner_reason=owner_reason,
            ),
            "route_epoch": route_epoch,
            "source_fingerprint": source_fingerprint,
        }
    )
    return payload


def route_and_decorate_actions(
    *,
    study_id: str,
    quest_id: str | None,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: Iterable[Mapping[str, Any]],
    blocked_reason: str | None,
    next_owner: str | None,
    active_run_id: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    owner_route = build_owner_route(
        study_id=study_id,
        quest_id=quest_id,
        status=status,
        progress=progress,
        actions=actions,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        active_run_id=active_run_id,
    )
    return owner_route, decorate_actions(actions=actions, owner_route=owner_route)


def owner_route_matches(*, dispatch: Mapping[str, Any], current_route: Mapping[str, Any] | None) -> bool:
    dispatch_route = ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )
    normalized_current_route = ensure_owner_route_v2(_mapping(current_route))
    if not dispatch_route or not normalized_current_route:
        return False
    return (
        _text(dispatch_route.get("idempotency_key")) == _text(normalized_current_route.get("idempotency_key"))
        and _text(dispatch_route.get("route_epoch")) == _text(normalized_current_route.get("route_epoch"))
        and _text(dispatch_route.get("source_fingerprint")) == _text(normalized_current_route.get("source_fingerprint"))
        and _text(dispatch_route.get("next_owner")) == _text(normalized_current_route.get("next_owner"))
        and _text(dispatch_route.get("owner_reason")) == _text(normalized_current_route.get("owner_reason"))
    )


def route_allows_action(*, action: Mapping[str, Any], owner_route: Mapping[str, Any] | None = None) -> bool:
    route = _mapping(owner_route) or _mapping(action.get("owner_route")) or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    if not route:
        return False
    route_owner = _text(route.get("next_owner"))
    action_owner = _text(action.get("next_executable_owner")) or _text(action.get("owner")) or _text(action.get("request_owner")) or _text(
        action.get("recommended_owner")
    )
    if not _action_matches_route_owner(action=action, route_owner=route_owner, action_owner=action_owner):
        return False
    action_type = _text(action.get("action_type"))
    allowed_actions = {_text(item) for item in route.get("allowed_actions") or []}
    allowed_actions.discard(None)
    return bool(allowed_actions) and action_type in allowed_actions


def _owner_from_actions(actions: list[Mapping[str, Any]]) -> str | None:
    for action in actions:
        if text := _action_owner(action):
            return text
    return None


def _action_owner(action: Mapping[str, Any]) -> str | None:
    for key in ("owner", "request_owner", "recommended_owner"):
        if text := _text(action.get(key)):
            return text
    handoff = _mapping(action.get("handoff_packet"))
    for key in ("owner", "request_owner", "recommended_owner", "next_executable_owner"):
        if text := _text(handoff.get(key)):
            return text
    return None


def _action_matches_route_owner(
    *,
    action: Mapping[str, Any],
    route_owner: str | None,
    action_owner: str | None = None,
) -> bool:
    if route_owner is None:
        return action_owner is None
    resolved_action_owner = action_owner if action_owner is not None else _action_owner(action)
    if resolved_action_owner == route_owner:
        return True
    if (
        route_owner == "external_supervisor"
        and _text(action.get("action_type")) == "runtime_platform_repair"
        and resolved_action_owner == "external_engineering_agent"
    ):
        return True
    if route_owner == "external_supervisor" and _text(action.get("authority")) == "external_supervisor":
        return resolved_action_owner in {None, "external_engineering_agent", "external_supervisor"}
    return False


def _reason_from_actions(actions: list[Mapping[str, Any]]) -> str | None:
    for action in actions:
        if text := _text(action.get("reason")) or _text(action.get("action_type")):
            return text
    return None


def _current_owner(*, status: Mapping[str, Any], progress: Mapping[str, Any], active_run_id: str | None) -> str | None:
    if active_run_id is not None:
        return "managed_runtime"
    macro_state = _macro_state(status, progress)
    if _macro_state_is_controller_stop(macro_state):
        return "controller_stop"
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("parked") is True and not _failed_non_resumable_auto_redrive(status, progress):
        return "controller_stop"
    quest_status = _text(status.get("quest_status"))
    if quest_status in {"stopped", "paused"}:
        return "controller_stop"
    return "mas_controller"


def _macro_state(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, Any]:
    return _mapping(status.get("study_macro_state")) or _mapping(progress.get("study_macro_state"))


def _macro_state_is_controller_stop(macro_state: Mapping[str, Any]) -> bool:
    if _text(macro_state.get("writer_state")) != "parked":
        return False
    return _text(macro_state.get("reason")) in {"external_info", "stop_loss", "user_stop"}


def _failed_non_resumable_auto_redrive(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("quest_status")) != "failed":
        return False
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    observed_state = _mapping(runtime_health.get("observed_quest_state"))
    continuation_state = _mapping(status.get("continuation_state")) or _mapping(progress.get("continuation_state"))
    if _text(continuation_state.get("continuation_policy")) in {"wait_for_user_or_resume", "manual", "manual_hold"}:
        return False
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    failure = _mapping(auto_parked.get("runtime_failure_classification"))
    if failure.get("requires_human_gate") is True or failure.get("external_blocker") is True:
        return False
    return bool(
        _text(status.get("reason")) == "quest_exists_with_non_resumable_state"
        or _text(observed_state.get("reason")) == "quest_exists_with_non_resumable_state"
    )


def _macro_state_source_ref(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, Any] | None:
    macro_state = _macro_state(status, progress)
    if not macro_state:
        return None
    return {
        "writer_state": _text(macro_state.get("writer_state")),
        "user_next": _text(macro_state.get("user_next")),
        "reason": _text(macro_state.get("reason")),
        "source_fingerprint": _text(macro_state.get("source_fingerprint")),
    }


def _fallback_epoch(*, status: Mapping[str, Any], progress: Mapping[str, Any]) -> str:
    for value in (
        status.get("truth_epoch"),
        progress.get("truth_epoch"),
        status.get("quest_id"),
        progress.get("quest_id"),
        status.get("study_id"),
    ):
        if text := _text(value):
            return text
    return "unknown"


def _source_fingerprint(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
    allowed_actions: list[str],
    owner: str | None,
    owner_reason: str | None,
) -> str:
    payload = {
        "status": {
            "quest_status": _text(status.get("quest_status")),
            "reason": _text(status.get("reason")),
            "active_run_id": _text(status.get("active_run_id")),
        },
        "progress": {
            "current_stage": _text(progress.get("current_stage")),
            "paper_stage": _text(progress.get("paper_stage")),
        },
        "actions": [_fingerprint_action(action) for action in actions],
        "allowed_actions": allowed_actions,
        "owner": owner,
        "owner_reason": owner_reason,
    }
    digest = hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()[:24]
    return f"owner-route-source::{digest}"


def _runtime_health_epoch(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    return _text(_mapping(status.get("runtime_health_snapshot")).get("runtime_health_epoch")) or _text(
        _mapping(progress.get("runtime_health_snapshot")).get("runtime_health_epoch")
    )


def _work_unit_fingerprint(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
    source_fingerprint: str,
) -> str:
    for action in actions:
        if text := _text(action.get("work_unit_fingerprint")):
            return text
        controller_route = _mapping(action.get("controller_route"))
        if text := _text(controller_route.get("work_unit_fingerprint")):
            return text
    publication_eval = _mapping(status.get("publication_eval")) or _mapping(progress.get("publication_eval"))
    for action in publication_eval.get("recommended_actions") or []:
        if not isinstance(action, Mapping):
            continue
        if text := _text(action.get("work_unit_fingerprint")):
            return text
        next_work_unit = _mapping(action.get("next_work_unit"))
        if text := _text(next_work_unit.get("fingerprint")):
            return text
    return source_fingerprint


def _trace_id(
    *,
    study_id: str,
    route_epoch: str,
    source_fingerprint: str,
    next_owner: str | None,
    owner_reason: str | None,
) -> str:
    digest = hashlib.sha256(
        _stable_json(
            {
                "study_id": study_id,
                "route_epoch": route_epoch,
                "source_fingerprint": source_fingerprint,
                "next_owner": next_owner,
                "owner_reason": owner_reason,
            }
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"owner-route-trace::{study_id}::{digest}"


def _idempotency_key(
    *,
    study_id: str,
    route_epoch: str,
    source_fingerprint: str,
    next_owner: str | None,
    owner_reason: str | None,
    allowed_actions: list[str],
) -> str:
    digest = hashlib.sha256(
        _stable_json(
            {
                "study_id": study_id,
                "route_epoch": route_epoch,
                "source_fingerprint": source_fingerprint,
                "next_owner": next_owner,
                "owner_reason": owner_reason,
                "allowed_actions": allowed_actions,
            }
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"owner-route::{study_id}::{route_epoch}::{next_owner or 'none'}::{owner_reason or 'none'}::{digest}"


def _fingerprint_action(action: Mapping[str, Any]) -> dict[str, Any]:
    ignored_keys = {
        "action_id",
        "handoff_packet",
        "owner_route",
        "status",
    }
    return {
        key: value
        for key, value in sorted(action.items())
        if key not in ignored_keys and value not in (None, "", [], {})
    }


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ROUTED_ACTION_TYPES",
    "build_owner_route",
    "decorate_actions",
    "ensure_owner_route_v2",
    "owner_route_matches",
    "route_allows_action",
    "route_and_decorate_actions",
]
