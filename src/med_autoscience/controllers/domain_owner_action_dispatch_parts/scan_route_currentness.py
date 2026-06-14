from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import domain_route_contract
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part

from . import consumed_transition_owner_routes
from . import fresh_progress_owner_actions
from . import publication_owner_materialization_currentness
from . import stage_native_dispatch_selection
from . import writer_handoff_currentness


SUPERVISION_LATEST_RELATIVE_PATH = domain_route_contract.SUPERVISION_LATEST_RELATIVE_PATH


def scan_latest_payload(profile: WorkspaceProfile) -> dict[str, Any] | None:
    return _read_json_object(profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH)


def dispatch_currentness_score(dispatch: Mapping[str, Any], current_study: Mapping[str, Any]) -> tuple[int, int]:
    route = current_owner_route_from_scan(current_study, dispatch=dispatch)
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
    route_current = 1 if dispatch_matches_current_route(dispatch=dispatch, current_route=route) else 0
    if (
        dispatch_matches_current_route(dispatch=dispatch, current_route=bridged_route)
        or dispatch_matches_current_route(dispatch=dispatch, current_route=publication_owner_bridged_route)
    ):
        route_current = 1
    stall_current = 1 if _dispatch_stall_matches_scan(dispatch=dispatch, current_study=current_study) else 0
    return route_current, stall_current


def dispatch_matches_current_route(
    *,
    dispatch: Mapping[str, Any],
    current_route: Mapping[str, Any] | None,
) -> bool:
    return bool(
        current_route
        and owner_route_part.owner_route_matches(dispatch=dispatch, current_route=current_route)
        and owner_route_part.route_allows_action(action=dispatch, owner_route=current_route)
    )


def current_owner_route_from_scan(
    current_study: Mapping[str, Any],
    *,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    consumed_transition_route = matching_consumed_transition_route(
        current_study=current_study,
        dispatch=dispatch,
    )
    if consumed_transition_route is not None:
        return consumed_transition_route
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if dispatch_matches_current_route(dispatch=dispatch, current_route=route):
        return route
    action_route = current_action_queue_owner_route(current_study, dispatch=dispatch)
    if action_route is not None:
        return action_route
    return None


def current_owner_route_from_scan_payload(
    *, scan_payload: Mapping[str, Any] | None, study_id: str, dispatch: Mapping[str, Any] | None
) -> tuple[dict[str, Any] | None, str | None]:
    current_study = scan_study(scan_payload, study_id)
    if dispatch is not None:
        consumed_transition_route = matching_consumed_transition_route(
            current_study=current_study,
            dispatch=dispatch,
        )
        if consumed_transition_route is not None:
            basis = (
                "consumed_transition_gate_replay"
                if gate_replay_route(consumed_transition_route)
                else "consumed_transition_owner_action"
            )
            return consumed_transition_route, basis
    if dispatch is None:
        route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
        if route:
            return route, "scan_latest"
        return None, None
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if dispatch_matches_current_route(dispatch=dispatch, current_route=route):
        return route, "scan_latest"
    action_route = current_action_queue_owner_route(current_study, dispatch=dispatch)
    if action_route is not None:
        return action_route, "scan_action_queue"
    return None, None


def diagnostic_owner_route_from_scan_payload(
    *, scan_payload: Mapping[str, Any] | None, study_id: str, dispatch: Mapping[str, Any] | None
) -> tuple[dict[str, Any] | None, str | None]:
    current_study = scan_study(scan_payload, study_id)
    if dispatch is not None:
        consumed_transition_route = matching_consumed_transition_route(
            current_study=current_study,
            dispatch=dispatch,
        )
        if consumed_transition_route is not None:
            basis = (
                "consumed_transition_gate_replay"
                if gate_replay_route(consumed_transition_route)
                else "consumed_transition_owner_action"
            )
            return consumed_transition_route, basis
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if route:
        return route, "scan_latest"
    if dispatch is not None:
        action_route = current_action_queue_owner_route(current_study, dispatch=dispatch)
        if action_route is not None:
            return action_route, "scan_action_queue"
    return None, None


def matching_consumed_transition_route(
    *,
    current_study: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    return consumed_transition_owner_routes.matching_consumed_transition_route(
        current_study=current_study,
        dispatch=dispatch,
    )


def consumed_transition_owner_route(current_study: Mapping[str, Any]) -> dict[str, Any]:
    return consumed_transition_owner_routes.consumed_transition_owner_route(current_study)


def with_consumed_transition_owner_route(current_study: Mapping[str, Any]) -> dict[str, Any]:
    return consumed_transition_owner_routes.with_consumed_transition_owner_route(current_study)


def gate_replay_route(route: Mapping[str, Any]) -> bool:
    return consumed_transition_owner_routes.gate_replay_route(route)


def live_provider_attempt_owner_route_from_scan_payload(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    current_study = scan_study(scan_payload, study_id)
    if current_study.get("running_provider_attempt") is not True:
        return None
    live_attempt = _mapping(current_study.get("opl_provider_attempt")) or current_study
    if not _live_provider_attempt_matches_dispatch(live_attempt=live_attempt, dispatch=dispatch):
        return None
    route = dispatch_owner_route(dispatch)
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


def current_action_queue_owner_route(
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


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return stage_native_dispatch_selection.dispatch_owner_route(dispatch)


def scan_study(scan_payload: Mapping[str, Any] | None, study_id: str) -> dict[str, Any]:
    latest = _mapping(scan_payload)
    for study in latest.get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            return payload
    return {}


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
    return fresh_progress_owner_actions.dispatch_work_unit_id(dispatch)


def _work_unit_id(value: object) -> str | None:
    return fresh_progress_owner_actions.work_unit_id(value)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


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
    "consumed_transition_owner_route",
    "current_action_queue_owner_route",
    "current_owner_route_from_scan_payload",
    "diagnostic_owner_route_from_scan_payload",
    "dispatch_currentness_score",
    "dispatch_matches_current_route",
    "dispatch_owner_route",
    "gate_replay_route",
    "live_provider_attempt_owner_route_from_scan_payload",
    "matching_consumed_transition_route",
    "scan_latest_payload",
    "scan_study",
    "with_consumed_transition_owner_route",
]
