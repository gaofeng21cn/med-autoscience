from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.gate_clearing_batch_work_units import PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
from med_autoscience.controllers.domain_action_request_materializer_parts import current_action_selection
from med_autoscience.controllers.owner_route_reconcile_parts import domain_route_contract
from med_autoscience.runtime_control import owner_route as owner_route_part

from . import owner_request_currentness
from . import owner_request_paths
from . import consumed_transition_currentness
from . import consumed_writer_handoff_filter
from . import current_writer_handoff
from . import persisted_handoff_selection
from . import publication_owner_materialization_currentness
from . import runtime_current_dispatch_selection
from . import writer_handoff_currentness


SUPERVISION_LATEST_RELATIVE_PATH = domain_route_contract.SUPERVISION_LATEST_RELATIVE_PATH
OWNER_REQUEST_RELATIVE_PATHS = owner_request_paths.OWNER_REQUEST_RELATIVE_PATHS


def scan_latest_payload(profile: WorkspaceProfile) -> dict[str, Any] | None:
    return _read_json_object(_scan_latest_path(profile))


def current_scan_study(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    latest = scan_latest_payload(profile)
    if latest is None:
        return None
    study = _scan_study(latest, study_id)
    return study or None


def current_scan_stall(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any]:
    return _mapping(_mapping(current_scan_study(profile=profile, study_id=study_id)).get("paper_progress_stall"))


def explicit_action_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    supported_action_types: frozenset[str],
    dispatch_relative_root: Path,
    require_current_authority: bool = True,
) -> list[dict[str, Any]]:
    dispatches: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for action_type in action_types:
        if action_type not in supported_action_types:
            continue
        path = profile.studies_root / study_id / dispatch_relative_root / f"{action_type}.json"
        payload = _read_json_object(path)
        if not payload:
            continue
        if _text(payload.get("study_id")) != study_id:
            continue
        if _text(payload.get("action_type")) != action_type:
            continue
        if _text(payload.get("dispatch_status")) != "ready":
            continue
        refs = _mapping(payload.get("refs"))
        payload["refs"] = {**refs, "dispatch_path": str(path)}
        if require_current_authority and (
            not owner_request_matches_dispatch(
                profile=profile,
                study_id=study_id,
                action_type=action_type,
                dispatch=payload,
            )
            and live_provider_attempt_owner_route_from_scan_payload(
                scan_payload=scan_latest_payload(profile),
                study_id=study_id,
                dispatch=payload,
            )
            is None
            and not current_writer_handoff.self_authorized_quality_repair_writer_handoff(
                study_id=study_id,
                action_type=action_type,
                dispatch=payload,
            )
        ):
            continue
        key = (str(path), action_type)
        if key in seen:
            continue
        seen.add(key)
        dispatches.append(payload)
    return dispatches


def selected_dispatches(
    *, profile: WorkspaceProfile, study_id: str, action_types: tuple[str, ...],
    consumer_payload: Mapping[str, Any] | None, consumer_latest_path: Path,
    scan_payload: Mapping[str, Any] | None, supported_action_types: frozenset[str],
    dispatch_relative_root: Path,
) -> list[dict[str, Any]]:
    current_study = _scan_study(scan_payload, study_id)
    current_study = _with_consumed_transition_owner_route(current_study)
    consumer_dispatches = current_consumer_dispatches(
        study_id=study_id,
        consumer_payload=consumer_payload,
        consumer_latest_path=consumer_latest_path,
    )
    consumer_dispatches = consumed_writer_handoff_filter.without_consumed_quality_repair_writer_handoffs(
        profile=profile,
        study_id=study_id,
        dispatches=consumer_dispatches,
    )
    current_dispatches = runtime_current_dispatch_selection.current_dispatches_only(
        dispatches=consumer_dispatches,
        current_study=current_study,
        dispatch_currentness_score=_dispatch_currentness_score,
    )
    requested = set(action_types)
    if not action_types:
        selected = [
            payload
            for payload in current_dispatches
            if _text(payload.get("action_type")) in supported_action_types
        ]
        selected_by_key = {
            (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type"))): index
            for index, payload in enumerate(selected)
        }
        for payload in consumed_writer_handoff_filter.without_consumed_quality_repair_writer_handoffs(
            profile=profile,
            study_id=study_id,
            dispatches=explicit_action_dispatches(
                profile=profile,
                study_id=study_id,
                action_types=tuple(sorted(supported_action_types)),
                supported_action_types=supported_action_types,
                dispatch_relative_root=dispatch_relative_root,
                require_current_authority=True,
            ),
        ):
            action_type = _text(payload.get("action_type")) or ""
            if (
                _dispatch_currentness_score(payload, current_study) <= (0, 0)
                and not owner_request_matches_dispatch(
                    profile=profile,
                    study_id=study_id,
                    action_type=action_type,
                    dispatch=payload,
                )
                and not current_writer_handoff.current_quality_repair_writer_handoff_dispatch(
                    profile=profile,
                    study_id=study_id,
                    action_type=action_type,
                    dispatch=payload,
                )
            ):
                continue
            key = (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type")))
            if key in selected_by_key:
                index = selected_by_key[key]
                selected[index] = _prefer_current_dispatch(
                    profile=profile,
                    consumer_dispatch=selected[index],
                    persisted_dispatch=payload,
                    scan_payload=scan_payload,
                    study_id=study_id,
                )
                continue
            selected_by_key[key] = len(selected)
            selected.append(payload)
        current_selected = _selected_dispatches_only(
            profile=profile,
            study_id=study_id,
            dispatches=selected,
            current_study=current_study,
        )
        runtime_current_selected = _runtime_current_dispatches_only(
            study_id=study_id,
            dispatches=selected,
            current_study=current_study,
        )
        if runtime_current_selected:
            return runtime_current_selected
        if current_selected:
            return current_selected
        if _consumed_transition_owner_route(current_study):
            return []
        return [
            payload
            for payload in consumer_dispatches
            if _text(payload.get("action_type")) in supported_action_types
            if not runtime_current_dispatch_selection.current_route_allows_dispatch_action(
                current_study=current_study,
                dispatch=payload,
                current_owner_route_from_scan=lambda study, selected_dispatch: _current_owner_route_from_scan(
                    study,
                    dispatch=selected_dispatch,
                ),
                route_allows_action=lambda selected_dispatch, route: owner_route_part.route_allows_action(
                    action=selected_dispatch,
                    owner_route=route,
                ),
            )
        ]
    selected = [
        payload
        for payload in consumer_dispatches
        if _text(payload.get("action_type")) in requested
    ]
    selected_keys = {
        (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type")))
        for payload in selected
    }
    selected_by_key = {
        (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type"))): index
        for index, payload in enumerate(selected)
    }
    for payload in consumer_dispatches:
        if _text(payload.get("action_type")) not in requested:
            continue
        key = (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type")))
        if key in selected_by_key:
            continue
        selected.append(payload)
        selected_keys.add(key)
        selected_by_key[key] = len(selected) - 1
    for payload in consumed_writer_handoff_filter.without_consumed_quality_repair_writer_handoffs(
        profile=profile,
        study_id=study_id,
        dispatches=explicit_action_dispatches(
            profile=profile,
            study_id=study_id,
            action_types=action_types,
            supported_action_types=supported_action_types,
            dispatch_relative_root=dispatch_relative_root,
            require_current_authority=True,
        ),
    ):
        key = (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type")))
        if key in selected_by_key:
            index = selected_by_key[key]
            selected[index] = _prefer_current_dispatch(
                profile=profile,
                consumer_dispatch=selected[index],
                persisted_dispatch=payload,
                scan_payload=scan_payload,
                study_id=study_id,
            )
            continue
        elif key not in selected_keys:
            selected.append(payload)
            selected_keys.add(key)
            selected_by_key[key] = len(selected) - 1
    runtime_current_selected = _runtime_current_dispatches_only(
        study_id=study_id,
        dispatches=selected,
        current_study=current_study,
    )
    if runtime_current_selected:
        return runtime_current_selected
    current_selected = _selected_dispatches_only(
        profile=profile,
        study_id=study_id,
        dispatches=selected,
        current_study=current_study,
    )
    if current_selected:
        return current_selected
    return selected

def _selected_dispatches_only(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
    current_study: Mapping[str, Any],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for dispatch in dispatches:
        action_type = _text(dispatch.get("action_type")) or ""
        if _dispatch_currentness_score(dispatch, current_study) > (0, 0):
            selected.append(dispatch)
            continue
        if owner_request_matches_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=dispatch,
        ):
            selected.append(dispatch)
            continue
        if live_provider_attempt_owner_route_from_scan_payload(
            scan_payload=scan_latest_payload(profile),
            study_id=study_id,
            dispatch=dispatch,
        ):
            selected.append(dispatch)
            continue
        if current_writer_handoff.current_quality_repair_writer_handoff_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=dispatch,
        ):
            selected.append(dispatch)
            continue
        if not _dispatch_owner_route(dispatch):
            selected.append(dispatch)
    return selected


def _runtime_current_dispatches_only(
    *,
    study_id: str,
    dispatches: list[dict[str, Any]],
    current_study: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return runtime_current_dispatch_selection.runtime_current_dispatches_only(
        study_id=study_id,
        dispatches=dispatches,
        current_study=current_study,
        dispatch_currentness_score=_dispatch_currentness_score,
        live_provider_attempt_owner_route_from_scan_payload=live_provider_attempt_owner_route_from_scan_payload,
    )


def _with_consumed_transition_owner_route(current_study: Mapping[str, Any]) -> dict[str, Any]:
    study = dict(current_study)
    transition_route = _consumed_transition_owner_route(study)
    if transition_route:
        study["owner_route"] = transition_route
    return study


def _consumed_transition_owner_route(current_study: Mapping[str, Any]) -> dict[str, Any]:
    transition = _mapping(current_study.get("domain_transition"))
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return {}
    route = current_action_selection.domain_transition_owner_route_for_study(current_study)
    if _gate_replay_route(route):
        return route
    if _text(transition.get("controller_action")) is None:
        return {}
    next_work_unit = _mapping(transition.get("next_work_unit"))
    if not next_work_unit:
        return {}
    action_type = _action_type_for_consumed_transition(transition=transition, next_work_unit=next_work_unit)
    if action_type is None:
        return {}
    study_id = _text(current_study.get("study_id"))
    if study_id is None:
        return {}
    owner = _owner_for_consumed_transition(action_type=action_type, transition=transition)
    work_unit_id = _text(next_work_unit.get("unit_id")) or _text(next_work_unit.get("work_unit_id"))
    truth = _mapping(current_study.get("study_truth_snapshot"))
    route_epoch = _text(truth.get("truth_epoch")) or _text(truth.get("authority_epoch")) or study_id
    source_fingerprint = _text(truth.get("source_signature")) or (
        f"domain-transition::{_text(transition.get('decision_type')) or 'current'}::{work_unit_id or action_type}"
    )
    current_route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    current_basis = _mapping(_mapping(current_route.get("currentness_contract")).get("basis")) or _mapping(
        _mapping(current_route.get("source_refs")).get("owner_route_currentness_basis")
    )
    runtime_health_epoch = _text(_mapping(current_study.get("runtime_health_snapshot")).get("runtime_health_epoch")) or _text(
        current_basis.get("runtime_health_epoch")
    )
    owner_reason = work_unit_id or _text(transition.get("decision_type")) or action_type
    work_unit_fingerprint = (
        _text(transition.get("work_unit_fingerprint"))
        or _text(next_work_unit.get("fingerprint"))
        or f"domain-transition::{_text(transition.get('decision_type')) or 'current'}::{work_unit_id or action_type}"
    )
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": _text(current_study.get("quest_id")),
        "truth_epoch": route_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "failure_signature": owner_reason,
        "trace_id": f"owner-route-trace::{study_id}::consumed-transition::{action_type}",
        "route_epoch": route_epoch,
        "source_fingerprint": source_fingerprint,
        "current_owner": _text(current_study.get("current_owner")) or "mas_controller",
        "next_owner": owner,
        "owner_reason": owner_reason,
        "active_run_id": _text(current_study.get("active_run_id")),
        "allowed_actions": [action_type],
        "blocked_actions": [item for item in OWNER_REQUEST_RELATIVE_PATHS if item != action_type],
        "idempotency_key": f"owner-route::{study_id}::{route_epoch}::{owner}::{owner_reason}",
        "source_refs": {
            "source_eval_id": _text(completion.get("eval_id"))
            or _text(transition.get("source_eval_id"))
            or _text(transition.get("publication_eval_id"))
            or _text(_mapping(transition.get("publication_eval_ref")).get("eval_id"))
            or _text(_mapping(current_study.get("publication_eval")).get("eval_id"))
            or _text(current_basis.get("source_eval_id")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "runtime_health_epoch": runtime_health_epoch,
            "blocked_reason": owner_reason,
            "receipt_ref": _text(completion.get("receipt_ref")),
        },
    }
    return owner_route_part.ensure_owner_route_v2(route)


def _gate_replay_route(route: Mapping[str, Any]) -> bool:
    if not route:
        return False
    source_refs = _mapping(route.get("source_refs"))
    return (
        _text(route.get("next_owner")) == "gate_clearing_batch"
        and "run_gate_clearing_batch" in {_text(item) for item in route.get("allowed_actions") or []}
        and _text(source_refs.get("work_unit_id")) in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
    )


def _action_type_for_consumed_transition(
    *,
    transition: Mapping[str, Any],
    next_work_unit: Mapping[str, Any],
) -> str | None:
    decision_type = _text(transition.get("decision_type"))
    route_target = _text(transition.get("route_target"))
    controller_action = _text(transition.get("controller_action"))
    work_unit_id = _text(next_work_unit.get("unit_id")) or _text(next_work_unit.get("work_unit_id"))
    if work_unit_id in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return "run_gate_clearing_batch"
    if decision_type == "route_back_same_line" and route_target == "write":
        return "run_quality_repair_batch"
    if controller_action == "run_gate_clearing_batch":
        return "run_gate_clearing_batch"
    if controller_action == "return_to_ai_reviewer_workflow":
        return "return_to_ai_reviewer_workflow"
    if controller_action == "request_opl_stage_attempt" and work_unit_id:
        return "run_quality_repair_batch"
    return None


def _owner_for_consumed_transition(*, action_type: str, transition: Mapping[str, Any]) -> str:
    if action_type == "run_quality_repair_batch":
        return "write"
    if action_type == "run_gate_clearing_batch":
        return "gate_clearing_batch"
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    return _text(transition.get("owner")) or "med-autoscience"


def _prefer_current_dispatch(
    *,
    profile: WorkspaceProfile,
    consumer_dispatch: Mapping[str, Any],
    persisted_dispatch: Mapping[str, Any],
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
) -> dict[str, Any]:
    action_type = _text(persisted_dispatch.get("action_type")) or ""
    if persisted_handoff_selection.persisted_handoff_supersedes_consumer_inline(
        study_id=study_id,
        action_type=action_type,
        consumer_dispatch=consumer_dispatch,
        persisted_dispatch=persisted_dispatch,
        owner_request_current=owner_request_matches_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=persisted_dispatch,
        ),
    ):
        return dict(persisted_dispatch)
    current_study = _scan_study(scan_payload, study_id)
    consumer_score = _dispatch_currentness_score(consumer_dispatch, current_study)
    persisted_score = _dispatch_currentness_score(persisted_dispatch, current_study)
    if persisted_score > consumer_score:
        return dict(persisted_dispatch)
    return dict(consumer_dispatch)


def _dispatch_currentness_score(dispatch: Mapping[str, Any], current_study: Mapping[str, Any]) -> tuple[int, int]:
    route = _current_owner_route_from_scan(current_study, dispatch=dispatch)
    bridged_route = writer_handoff_currentness.bridged_quality_repair_writer_handoff_route_from_study(
        current_study=current_study,
        dispatch=dispatch,
    )
    publication_owner_bridged_route = (
        publication_owner_materialization_currentness.bridged_publication_owner_materialization_route_from_study(
            current_study=current_study,
            dispatch=dispatch,
        )
    )
    route_current = 1 if _dispatch_matches_current_route(dispatch=dispatch, current_route=route) else 0
    if bridged_route is not None or publication_owner_bridged_route is not None:
        route_current = 1
    stall_current = 1 if _dispatch_stall_matches_scan(dispatch=dispatch, current_study=current_study) else 0
    return route_current, stall_current


def _dispatch_matches_current_route(
    *,
    dispatch: Mapping[str, Any],
    current_route: Mapping[str, Any] | None,
) -> bool:
    return bool(
        current_route
        and owner_route_part.owner_route_matches(dispatch=dispatch, current_route=current_route)
        and owner_route_part.route_allows_action(action=dispatch, owner_route=current_route)
    )


def _current_owner_route_from_scan(
    current_study: Mapping[str, Any],
    *,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    consumed_transition_route = _matching_consumed_transition_route(
        current_study=current_study,
        dispatch=dispatch,
    )
    if consumed_transition_route is not None:
        return consumed_transition_route
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if _dispatch_matches_current_route(dispatch=dispatch, current_route=route):
        return route
    action_route = _current_action_queue_owner_route(current_study, dispatch=dispatch)
    if action_route is not None:
        return action_route
    if route:
        return route
    return None


def current_owner_route_from_scan_payload(
    *, scan_payload: Mapping[str, Any] | None, study_id: str, dispatch: Mapping[str, Any] | None
) -> tuple[dict[str, Any] | None, str | None]:
    current_study = _scan_study(scan_payload, study_id)
    if dispatch is not None:
        consumed_transition_route = _matching_consumed_transition_route(
            current_study=current_study,
            dispatch=dispatch,
        )
        if consumed_transition_route is not None:
            basis = "consumed_transition_gate_replay" if _gate_replay_route(consumed_transition_route) else "consumed_transition_owner_action"
            return consumed_transition_route, basis
    if dispatch is None:
        route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
        if route:
            return route, "scan_latest"
        return None, None
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if _dispatch_matches_current_route(dispatch=dispatch, current_route=route):
        return route, "scan_latest"
    action_route = _current_action_queue_owner_route(current_study, dispatch=dispatch)
    if action_route is not None:
        return action_route, "scan_action_queue"
    if route:
        return route, "scan_latest"
    return None, None


def _matching_consumed_transition_route(
    *,
    current_study: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    route = _consumed_transition_owner_route(current_study)
    if not route:
        return None
    return consumed_transition_currentness.matching_route_for_dispatch(
        dispatch=dispatch,
        transition_route=route,
        gate_replay=_gate_replay_route(route),
    )


def live_provider_attempt_owner_route_from_scan_payload(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    current_study = _scan_study(scan_payload, study_id)
    if current_study.get("running_provider_attempt") is not True:
        return None
    live_attempt = _mapping(current_study.get("opl_provider_attempt")) or current_study
    if not _live_provider_attempt_matches_dispatch(live_attempt=live_attempt, dispatch=dispatch):
        return None
    route = _dispatch_owner_route(dispatch)
    if not route:
        return None
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=route):
        return None
    return route


def bridged_quality_repair_writer_handoff_route_from_scan_payload(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    return writer_handoff_currentness.bridged_quality_repair_writer_handoff_route_from_scan_payload(
        scan_payload=scan_payload,
        study_id=study_id,
        dispatch=dispatch,
    )


def bridged_quality_repair_writer_handoff_route(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    return bridged_quality_repair_writer_handoff_route_from_scan_payload(
        scan_payload=scan_latest_payload(profile),
        study_id=study_id,
        dispatch=dispatch,
    )


def bridged_publication_owner_materialization_route_from_scan_payload(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    return publication_owner_materialization_currentness.bridged_publication_owner_materialization_route_from_scan_payload(
        scan_payload=scan_payload,
        study_id=study_id,
        dispatch=dispatch,
    )


def bridged_publication_owner_materialization_route(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    return bridged_publication_owner_materialization_route_from_scan_payload(
        scan_payload=scan_latest_payload(profile),
        study_id=study_id,
        dispatch=dispatch,
    )


def _current_action_queue_owner_route(
    current_study: Mapping[str, Any],
    *,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    action_type = _text(dispatch.get("action_type"))
    for action in current_study.get("action_queue") or []:
        payload = _mapping(action)
        if _text(payload.get("action_type")) != action_type:
            continue
        route = owner_route_part.ensure_owner_route_v2(_mapping(payload.get("owner_route")))
        if not route:
            continue
        if not owner_route_part.owner_route_matches(dispatch=dispatch, current_route=route):
            continue
        if not owner_route_part.route_allows_action(action=dispatch, owner_route=route):
            continue
        return route
    return None


def _dispatch_stall_matches_scan(*, dispatch: Mapping[str, Any], current_study: Mapping[str, Any]) -> bool:
    current_stall = _mapping(current_study.get("paper_progress_stall"))
    if not current_stall:
        return False
    dispatch_stall = _mapping(dispatch.get("paper_progress_stall")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("paper_progress_stall")
    )
    if not dispatch_stall:
        return False
    dispatch_fingerprint = _text(dispatch_stall.get("action_fingerprint"))
    current_fingerprint = _text(current_stall.get("action_fingerprint"))
    return dispatch_fingerprint is not None and dispatch_fingerprint == current_fingerprint


def _live_provider_attempt_matches_dispatch(
    *,
    live_attempt: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    if live_attempt.get("running_provider_attempt") is not True:
        return False
    live_action_type = _text(live_attempt.get("action_type"))
    action_type = _text(dispatch.get("action_type"))
    if live_action_type is None or action_type is None or live_action_type != action_type:
        return False
    live_work_unit = _work_unit_id(live_attempt.get("work_unit_id"))
    dispatch_work_unit = _dispatch_work_unit_id(dispatch)
    if live_work_unit is None or dispatch_work_unit is None or live_work_unit != dispatch_work_unit:
        return False
    live_dispatch_ref = _text(live_attempt.get("dispatch_ref"))
    if live_dispatch_ref is None:
        return True
    dispatch_path = _text(_mapping(dispatch.get("refs")).get("dispatch_path"))
    if dispatch_path is None:
        return False
    normalized_dispatch_path = dispatch_path.replace("\\", "/")
    normalized_live_ref = live_dispatch_ref.replace("\\", "/")
    return normalized_dispatch_path == normalized_live_ref or normalized_dispatch_path.endswith(f"/{normalized_live_ref}")


def _dispatch_work_unit_id(dispatch: Mapping[str, Any]) -> str | None:
    route = _dispatch_owner_route(dispatch)
    route_refs = _mapping(route.get("source_refs"))
    route_basis = _mapping(route_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    return (
        _work_unit_id(route_refs.get("work_unit_id"))
        or _work_unit_id(route_basis.get("work_unit_id"))
        or _work_unit_id(prompt_contract.get("next_work_unit"))
        or _work_unit_id(dispatch.get("next_work_unit"))
        or _work_unit_id(source_action.get("next_work_unit"))
    )


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _scan_study(scan_payload: Mapping[str, Any] | None, study_id: str) -> dict[str, Any]:
    latest = _mapping(scan_payload)
    for study in latest.get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            return payload
    return {}


def current_consumer_dispatches(
    *,
    study_id: str,
    consumer_payload: Mapping[str, Any] | None,
    consumer_latest_path: Path,
) -> list[dict[str, Any]]:
    latest = dict(consumer_payload) if consumer_payload is not None else _read_json_object(consumer_latest_path)
    if latest is None:
        return []
    dispatches: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None]] = set()
    for dispatch in latest.get("default_executor_dispatches") or []:
        payload = _mapping(dispatch)
        if _text(payload.get("study_id")) != study_id:
            continue
        if _text(payload.get("dispatch_status")) != "ready":
            continue
        refs = _mapping(payload.get("refs"))
        dispatch_path = _text(refs.get("dispatch_path"))
        if dispatch_path is None:
            continue
        key = (dispatch_path, _text(payload.get("action_type")))
        if key in seen:
            continue
        seen.add(key)
        dispatches.append(payload)
    return dispatches


def owner_request_route(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    return _owner_request_effective_route(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    )


def owner_request_matches_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> bool:
    return (
        _owner_request_effective_route(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=dispatch,
        )
        is not None
    )


def _owner_request_effective_route(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    return _owner_request_effective_route_for_scan(
        request=owner_request_payload(profile, study_id, action_type),
        scan_payload=scan_latest_payload(profile),
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    )


def _owner_request_effective_route_for_scan(
    *,
    request: Mapping[str, Any] | None,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not _owner_request_basics_match_dispatch(
        request=request,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return None
    request_route = _request_owner_route(request=request or {}, action_type=action_type, dispatch=dispatch)
    if not (
        owner_route_part.owner_route_matches(dispatch=dispatch, current_route=request_route)
        and owner_route_part.route_allows_action(action=dispatch, owner_route=request_route)
    ):
        return None
    current_study = _scan_study(scan_payload, study_id)
    if not _owner_request_current_against_scan(
        request_route=request_route,
        current_study=current_study,
        dispatch=dispatch,
    ):
        return None
    return owner_route_part.ensure_owner_route_v2(request_route)


def _owner_request_basics_match_dispatch(
    *,
    request: Mapping[str, Any] | None,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> bool:
    dispatch_owner = _text(dispatch.get("next_executable_owner")) or _text(_dispatch_owner_route(dispatch).get("next_owner"))
    return owner_request_currentness.request_basics_match_dispatch(
        request=request,
        action_type=action_type,
        dispatch_owner=dispatch_owner,
    )


def _owner_request_current_against_scan(
    *,
    request_route: Mapping[str, Any],
    current_study: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    if not current_study:
        return True
    if live_provider_attempt_owner_route_from_scan_payload(
        scan_payload={"studies": [dict(current_study)]},
        study_id=_text(current_study.get("study_id")) or _text(request_route.get("study_id")) or "",
        dispatch=dispatch,
    ) is not None:
        return True
    consumed_transition_route = _matching_consumed_transition_route(
        current_study=current_study,
        dispatch=dispatch,
    )
    if consumed_transition_route is not None:
        return True
    scan_route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if _dispatch_matches_current_route(dispatch=dispatch, current_route=scan_route):
        return True
    if _current_action_queue_owner_route(current_study, dispatch=dispatch) is not None:
        return True
    return owner_request_currentness.route_basis_matches_current_study(
        request_route=request_route,
        current_study=current_study,
        consumed_transition_route=_consumed_transition_owner_route(current_study),
    )


def _request_owner_route(
    *,
    request: Mapping[str, Any],
    action_type: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    request_route = _mapping(request.get("owner_route")) or _mapping(_mapping(request.get("owner_pickup")).get("owner_route"))
    if not request_route:
        request_route = _owner_request_fallback_route(action_type=action_type, dispatch=dispatch)
    return owner_route_part.ensure_owner_route_v2(request_route)


def _owner_request_fallback_route(*, action_type: str, dispatch: Mapping[str, Any]) -> dict[str, Any]:
    if action_type != "return_to_ai_reviewer_workflow":
        return {}
    dispatch_route = _dispatch_owner_route(dispatch)
    if not dispatch_route:
        return {}
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=dispatch_route):
        return {}
    return dispatch_route


owner_request_payload = owner_request_paths.owner_request_payload
owner_request_path = owner_request_paths.owner_request_path


def _dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _scan_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "SUPERVISION_LATEST_RELATIVE_PATH",
    "bridged_publication_owner_materialization_route",
    "bridged_publication_owner_materialization_route_from_scan_payload",
    "bridged_quality_repair_writer_handoff_route",
    "bridged_quality_repair_writer_handoff_route_from_scan_payload",
    "current_scan_stall",
    "current_scan_study",
    "current_owner_route_from_scan_payload",
    "current_consumer_dispatches",
    "explicit_action_dispatches",
    "live_provider_attempt_owner_route_from_scan_payload",
    "owner_request_matches_dispatch",
    "owner_request_payload",
    "owner_request_path",
    "owner_request_route",
    "selected_dispatches",
    "scan_latest_payload",
]
