from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.runtime_control import decision_trace_ledger
from med_autoscience.runtime_control import owner_route_attempt_protocol


ROUTED_ACTION_TYPES = (
    "publication_gate_specificity_required",
    "current_package_freshness_required",
    "artifact_display_surface_materialization_required",
    "return_to_ai_reviewer_workflow",
    "canonical_paper_inputs_rehydrate_required",
    "run_quality_repair_batch",
    "run_gate_clearing_batch",
)
ALLOWED_ACTION_TYPES = (
    *ROUTED_ACTION_TYPES,
    "unit_harmonized_external_validation_rerun",
    "recover_transport_model_provenance",
    "methodology_reframe_route_decision",
    "provenance_limited_harmonization_audit",
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
    work_unit_fingerprint = _work_unit_fingerprint(
        status=status,
        progress=progress,
        actions=normalized_actions,
        source_fingerprint=source_fingerprint,
    )
    source_eval_id = _source_eval_id(status=status, progress=progress, actions=normalized_actions)
    work_unit_id = _work_unit_id(status=status, progress=progress, actions=normalized_actions)
    current_owner = _current_owner(status=status, progress=progress, active_run_id=active_run_id)
    trace_projection = decision_trace_ledger.decision_trace_projection(
        status,
        progress,
        *normalized_actions,
    )
    if decision_trace_ledger.repeated_failed_path_suppressed(
        actions=normalized_actions,
        trace_projection=trace_projection,
    ):
        trace_projection = {**trace_projection, "repeated_failed_path_suppressed": True}
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": route_epoch,
        "runtime_health_epoch": _runtime_health_epoch(status, progress),
        "work_unit_fingerprint": work_unit_fingerprint,
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
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "blocked_reason": owner_reason,
            "publication_eval_path": _publication_eval_path(
                status=status,
                progress=progress,
                actions=normalized_actions,
            ),
            "quest_root": _text(status.get("quest_root")) or _text(progress.get("quest_root")),
            "study_macro_state": _macro_state_source_ref(status, progress),
        },
    }
    route.update(trace_projection)
    _attach_decision_trace_source_refs(route)
    route["idempotency_key"] = _idempotency_key(
        study_id=study_id,
        route_epoch=route_epoch,
        source_fingerprint=source_fingerprint,
        next_owner=owner,
        owner_reason=owner_reason,
        allowed_actions=allowed_actions,
    )
    return owner_route_attempt_protocol.decorate_owner_route(route)


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
    trace_projection = decision_trace_ledger.decision_trace_projection(payload, source_refs)
    payload.update({key: value for key, value in trace_projection.items() if key not in payload})
    _attach_decision_trace_source_refs(payload)
    return owner_route_attempt_protocol.decorate_owner_route(payload)


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
    normalized_actions = [dict(action) for action in actions]
    owner_route = build_owner_route(
        study_id=study_id,
        quest_id=quest_id,
        status=status,
        progress=progress,
        actions=normalized_actions,
        blocked_reason=blocked_reason,
        next_owner=next_owner,
        active_run_id=active_run_id,
    )
    actions = decision_trace_ledger.filter_actions_consuming_recorded_failed_paths(
        actions=normalized_actions,
        trace_projection=owner_route,
    )
    owner_route = _attach_consumed_failed_path_refs_from_filtered_actions(
        owner_route=owner_route,
        original_actions=normalized_actions,
        filtered_actions=actions,
    )
    return owner_route, decorate_actions(actions=actions, owner_route=owner_route)


def owner_route_matches(*, dispatch: Mapping[str, Any], current_route: Mapping[str, Any] | None) -> bool:
    dispatch_route = ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )
    normalized_current_route = ensure_owner_route_v2(_mapping(current_route))
    if not dispatch_route or not normalized_current_route:
        return False
    if not _currentness_matches(dispatch_route=dispatch_route, current_route=normalized_current_route):
        return False
    dispatch_allowed = {_text(item) for item in dispatch_route.get("allowed_actions") or []}
    current_allowed = {_text(item) for item in normalized_current_route.get("allowed_actions") or []}
    dispatch_allowed.discard(None)
    current_allowed.discard(None)
    return (
        bool(dispatch_allowed)
        and dispatch_allowed == current_allowed
        and _macro_state_source_ref_matches(dispatch_route, normalized_current_route)
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


def _currentness_matches(*, dispatch_route: Mapping[str, Any], current_route: Mapping[str, Any]) -> bool:
    comparisons = (
        ("route_epoch", _text(dispatch_route.get("route_epoch")), _text(current_route.get("route_epoch"))),
        (
            "source_fingerprint",
            _text(dispatch_route.get("source_fingerprint")),
            _text(current_route.get("source_fingerprint")),
        ),
        ("next_owner", _text(dispatch_route.get("next_owner")), _text(current_route.get("next_owner"))),
    )
    for _key, dispatch_value, current_value in comparisons:
        if current_value and dispatch_value != current_value:
            return False
    return _basis_matches(dispatch_route=dispatch_route, current_route=current_route)


def _basis_matches(*, dispatch_route: Mapping[str, Any], current_route: Mapping[str, Any]) -> bool:
    dispatch_basis = owner_route_attempt_protocol.currentness_basis(dispatch_route)
    current_basis = owner_route_attempt_protocol.currentness_basis(current_route)
    for key in ("source_eval_id", "work_unit_id", "work_unit_fingerprint", "truth_epoch", "runtime_health_epoch"):
        current_value = _text(current_basis.get(key))
        dispatch_value = _text(dispatch_basis.get(key))
        if current_value and dispatch_value and current_value != dispatch_value:
            return False
        if current_value and not dispatch_value and key in {"work_unit_id", "work_unit_fingerprint", "truth_epoch"}:
            return False
    return bool(_text(current_basis.get("work_unit_id")) or _text(current_basis.get("work_unit_fingerprint")))


def _macro_state_source_ref_matches(dispatch_route: Mapping[str, Any], current_route: Mapping[str, Any]) -> bool:
    dispatch_macro = _mapping(_mapping(dispatch_route.get("source_refs")).get("study_macro_state"))
    current_macro = _mapping(_mapping(current_route.get("source_refs")).get("study_macro_state"))
    if not current_macro:
        return True
    if not dispatch_macro:
        return False
    for key in ("writer_state", "user_next", "reason", "source_fingerprint"):
        current_value = _text(current_macro.get(key))
        if current_value and _text(dispatch_macro.get(key)) != current_value:
            return False
    return True


def _attach_decision_trace_source_refs(route: dict[str, Any]) -> None:
    source_refs = dict(_mapping(route.get("source_refs")))
    if route.get("decision_trace_refs"):
        source_refs["decision_trace_refs"] = list(route.get("decision_trace_refs") or [])
    if route.get("failed_path_refs"):
        source_refs["failed_path_refs"] = list(route.get("failed_path_refs") or [])
    if route.get("consumed_failed_path_refs"):
        source_refs["consumed_failed_path_refs"] = list(route.get("consumed_failed_path_refs") or [])
    route["source_refs"] = source_refs


def _attach_consumed_failed_path_refs_from_filtered_actions(
    *,
    owner_route: Mapping[str, Any],
    original_actions: list[Mapping[str, Any]],
    filtered_actions: list[Mapping[str, Any]],
) -> dict[str, Any]:
    if len(filtered_actions) == len(original_actions):
        return dict(owner_route)
    recorded_refs = set(_text_items(owner_route.get("failed_path_refs")))
    recorded_refs.update(_text_items(owner_route.get("consumed_failed_path_refs")))
    if not recorded_refs:
        return dict(owner_route)
    filtered_ids = {_action_identity(action) for action in filtered_actions}
    consumed_refs: list[str] = []
    for action in original_actions:
        if _action_identity(action) in filtered_ids:
            continue
        consumed_refs.extend(ref for ref in _action_failed_path_refs(action) if ref in recorded_refs)
    consumed_refs = _unique_texts(
        [
            *_text_items(owner_route.get("consumed_failed_path_refs")),
            *consumed_refs,
        ]
    )
    if not consumed_refs:
        return dict(owner_route)
    route = dict(owner_route)
    route["consumed_failed_path_refs"] = consumed_refs
    route["repeated_failed_path_suppressed"] = True
    failed_path_ledger = dict(_mapping(route.get("failed_path_ledger")))
    if failed_path_ledger:
        failed_path_ledger["consumed_refs"] = consumed_refs
        failed_path_ledger["body_included"] = False
        failed_path_ledger["route_authority"] = False
        route["failed_path_ledger"] = failed_path_ledger
    _attach_decision_trace_source_refs(route)
    return route


def _action_identity(action: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    return (
        _text(action.get("action_id")),
        _text(action.get("action_type")),
        _text(action.get("work_unit_fingerprint")),
    )


def _action_failed_path_refs(action: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "consumes_failed_path_refs",
        "consumed_failed_path_refs",
        "failed_path_refs",
    ):
        refs.extend(_text_items(action.get(key)))
    return _unique_texts(refs)


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, Mapping | bytes):
        return []
    if not isinstance(value, list | tuple | set):
        return []
    return _unique_texts(item for item in value if _text(item) is not None)


def _unique_texts(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _text(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


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


def _source_eval_id(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
) -> str | None:
    for action in actions:
        if text := _text(action.get("source_eval_id")):
            return text
        controller_route = _mapping(action.get("controller_route"))
        if text := _text(controller_route.get("source_eval_id")) or _text(controller_route.get("publication_eval_id")):
            return text
    publication_eval = _mapping(status.get("publication_eval")) or _mapping(progress.get("publication_eval"))
    return _text(publication_eval.get("eval_id")) or _text(publication_eval.get("source_eval_id"))


def _work_unit_id(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
) -> str | None:
    if text := _work_unit_id_from_actions(actions):
        return text
    transition = _mapping(status.get("domain_transition")) or _mapping(progress.get("domain_transition"))
    if text := _work_unit_text(transition.get("next_work_unit")):
        return text
    publication_eval = _mapping(status.get("publication_eval")) or _mapping(progress.get("publication_eval"))
    return _work_unit_id_from_recommended_actions(publication_eval)


def _work_unit_id_from_actions(actions: list[Mapping[str, Any]]) -> str | None:
    for action in actions:
        if text := _text(action.get("work_unit_id")):
            return text
        if text := _work_unit_text(action.get("next_work_unit")):
            return text
        if text := _text(action.get("executable_work_unit")) or _text(action.get("controller_work_unit_id")):
            return text
        controller_route = _mapping(action.get("controller_route"))
        if text := _text(controller_route.get("work_unit_id")) or _work_unit_text(controller_route.get("next_work_unit")):
            return text
    return None


def _work_unit_id_from_recommended_actions(publication_eval: Mapping[str, Any]) -> str | None:
    for action in publication_eval.get("recommended_actions") or []:
        if not isinstance(action, Mapping):
            continue
        if text := _text(action.get("work_unit_id")) or _work_unit_text(action.get("next_work_unit")):
            return text
    return None


def _publication_eval_path(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[Mapping[str, Any]],
) -> str | None:
    for action in actions:
        controller_route = _mapping(action.get("controller_route"))
        publication_eval_ref = _mapping(controller_route.get("publication_eval_ref"))
        if text := _text(publication_eval_ref.get("artifact_path")):
            return text
        if text := _text(controller_route.get("publication_eval_path")):
            return text
    return _text(_mapping(progress.get("refs")).get("publication_eval_path")) or _text(
        _mapping(status.get("refs")).get("publication_eval_path")
    )


def _work_unit_text(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


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
