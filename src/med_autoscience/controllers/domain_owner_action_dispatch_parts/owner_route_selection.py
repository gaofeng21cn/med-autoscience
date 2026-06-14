from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.runtime_control import owner_route_attempt_protocol

from . import accepted_owner_gate_decision
from . import consumed_transition_owner_routes
from . import current_writer_handoff
from . import persisted_dispatches


PAPER_RECOVERY_OWNER_CALLABLE_BRIDGE_AUTHORITY = (
    "domain_action_request_materializer_paper_recovery_owner_callable"
)


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route"))
        or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def owner_route_block_reason(
    *,
    dispatch: Mapping[str, Any],
    current_route: Mapping[str, Any] | None,
) -> str | None:
    if not dispatch_owner_route(dispatch):
        return "owner_route_missing"
    if current_route is None:
        return "current_owner_route_missing"
    if not owner_route_part.owner_route_matches(dispatch=dispatch, current_route=current_route):
        return "owner_route_stale"
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=current_route):
        return "owner_route_next_owner_mismatch"
    if not owner_route_attempt_protocol.route_protocol_dispatchable(
        current_route,
        action_type=_text(dispatch.get("action_type")),
    ):
        return "owner_route_currentness_basis_missing"
    return None


def execution_owner_route(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
    scan_payload: Mapping[str, Any] | None,
    fresh_progress: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    terminal_route = _terminal_closeout_owner_answer_dispatch_route(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
        fresh_progress=fresh_progress,
    )
    if terminal_route is not None:
        return terminal_route, "terminal_closeout_owner_answer_dispatch"
    stage_native_route = _stage_native_dispatch_owner_route(dispatch)
    if (
        stage_native_route is not None
        and owner_route_block_reason(dispatch=dispatch, current_route=stage_native_route) is None
    ):
        return stage_native_route, "stage_native_workspace_next_action"
    bridged_route = persisted_dispatches.bridged_quality_repair_writer_handoff_route(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
    )
    if (
        bridged_route is not None
        and owner_route_block_reason(dispatch=dispatch, current_route=bridged_route) is None
    ):
        return bridged_route, "bridged_writer_handoff"
    current_writer_route = current_writer_handoff.current_quality_repair_writer_handoff_route(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
    )
    if (
        current_writer_route is not None
        and owner_route_block_reason(dispatch=dispatch, current_route=current_writer_route) is None
    ):
        return current_writer_route, "current_writer_handoff"
    publication_bridge_route = persisted_dispatches.bridged_publication_owner_materialization_route(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
    )
    if (
        publication_bridge_route is not None
        and owner_route_block_reason(dispatch=dispatch, current_route=publication_bridge_route) is None
    ):
        return publication_bridge_route, "bridged_publication_owner_materialization"
    accepted_gate_route = accepted_owner_gate_decision.dispatch_owner_route_for_progress(
        fresh_progress,
        dispatch,
    )
    if accepted_gate_route and owner_route_block_reason(
        dispatch=dispatch,
        current_route=accepted_gate_route,
    ) is None:
        return accepted_gate_route, "accepted_owner_gate_decision"
    if not _consumed_transition_owner_route(scan_payload=scan_payload, study_id=study_id) and (
        fresh_progress_route := _fresh_progress_current_owner_action_route(
            fresh_progress=fresh_progress,
            dispatch=dispatch,
        )
    ) is not None:
        return fresh_progress_route, "fresh_progress_current_owner_action"
    if not dispatch_uses_bridge_authority(dispatch):
        scan_route, scan_route_basis = _current_owner_route(
            profile,
            study_id,
            dispatch=dispatch,
            scan_payload=scan_payload,
        )
        route_block_reason = owner_route_block_reason(dispatch=dispatch, current_route=scan_route)
        if scan_route_basis != "dispatch_owner_route" and route_block_reason is None:
            return scan_route, scan_route_basis or "scan_latest"
        live_attempt_route = persisted_dispatches.live_provider_attempt_owner_route_from_scan_payload(
            scan_payload=scan_payload,
            study_id=study_id,
            dispatch=dispatch,
        )
        if (
            live_attempt_route is not None
            and owner_route_block_reason(dispatch=dispatch, current_route=live_attempt_route) is None
        ):
            return live_attempt_route, "live_provider_attempt_dispatch"
    request_route = persisted_dispatches.owner_request_route(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    )
    if request_route is not None:
        return request_route, "owner_request"
    dispatch_route = dispatch_owner_route(dispatch)
    if (
        _dispatch_bridge_authority(dispatch) == PAPER_RECOVERY_OWNER_CALLABLE_BRIDGE_AUTHORITY
        and dispatch_route
        and owner_route_block_reason(dispatch=dispatch, current_route=dispatch_route) is None
    ):
        return dispatch_route, "paper_recovery_owner_callable"
    if (
        dispatch_uses_bridge_authority(dispatch)
        and dispatch_route
        and owner_route_block_reason(dispatch=dispatch, current_route=dispatch_route) is None
    ):
        return dispatch_route, "dispatch_owner_route_bridge"
    if dispatch_uses_bridge_authority(dispatch):
        return None, "bridge_currentness_failed"
    scan_route, scan_route_basis = _current_owner_route(
        profile,
        study_id,
        dispatch=dispatch,
        scan_payload=scan_payload,
    )
    route_block_reason = owner_route_block_reason(dispatch=dispatch, current_route=scan_route)
    if scan_route_basis != "dispatch_owner_route" and route_block_reason is None:
        return scan_route, scan_route_basis or "scan_latest"
    live_attempt_route = persisted_dispatches.live_provider_attempt_owner_route_from_scan_payload(
        scan_payload=scan_payload,
        study_id=study_id,
        dispatch=dispatch,
    )
    if (
        live_attempt_route is not None
        and owner_route_block_reason(dispatch=dispatch, current_route=live_attempt_route) is None
    ):
        return live_attempt_route, "live_provider_attempt_dispatch"
    diagnostic_route, diagnostic_basis = _diagnostic_owner_route(
        profile,
        study_id,
        dispatch=dispatch,
        scan_payload=scan_payload,
    )
    return diagnostic_route, diagnostic_basis or scan_route_basis or "scan_latest"


def dispatch_uses_bridge_authority(dispatch: Mapping[str, Any]) -> bool:
    return _dispatch_bridge_authority(dispatch) is not None


def _dispatch_bridge_authority(dispatch: Mapping[str, Any]) -> str | None:
    route = dispatch_owner_route(dispatch)
    refs = _mapping(route.get("source_refs"))
    return _text(refs.get("bridge_authority"))


def _current_owner_route(
    profile: WorkspaceProfile,
    study_id: str,
    *,
    dispatch: Mapping[str, Any] | None = None,
    scan_payload: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    return persisted_dispatches.current_owner_route_from_scan_payload(
        scan_payload=scan_payload
        if scan_payload is not None
        else persisted_dispatches.scan_latest_payload(profile),
        study_id=study_id,
        dispatch=dispatch,
    )


def _consumed_transition_owner_route(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
) -> dict[str, Any] | None:
    return consumed_transition_owner_routes.consumed_transition_owner_route(
        _scan_study(scan_payload, study_id)
    ) or None


def _diagnostic_owner_route(
    profile: WorkspaceProfile,
    study_id: str,
    *,
    dispatch: Mapping[str, Any] | None = None,
    scan_payload: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    return persisted_dispatches.diagnostic_owner_route_from_scan_payload(
        scan_payload=scan_payload
        if scan_payload is not None
        else persisted_dispatches.scan_latest_payload(profile),
        study_id=study_id,
        dispatch=dispatch,
    )


def _fresh_progress_current_owner_action_route(
    *,
    fresh_progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    route = dispatch_owner_route(dispatch)
    if not route or owner_route_block_reason(dispatch=dispatch, current_route=route) is not None:
        return None
    for action in _fresh_progress_current_owner_actions(fresh_progress):
        if _current_owner_action_identity_matches_dispatch(
            progress=fresh_progress,
            action=action,
            dispatch=dispatch,
        ):
            return route
    return None


def _fresh_progress_current_owner_actions(progress: Mapping[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    current_action = _mapping(progress.get("current_executable_owner_action"))
    if _text(current_action.get("action_type")) is not None:
        actions.append(current_action)
    current_work_unit = _mapping(progress.get("current_work_unit"))
    if (
        _text(current_work_unit.get("status")) == "executable_owner_action"
        and _text(current_work_unit.get("action_type")) is not None
    ):
        actions.append(current_work_unit)
    return actions


def _current_owner_action_identity_matches_dispatch(
    *,
    progress: Mapping[str, Any],
    action: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    action_type = _text(action.get("action_type"))
    if action_type is None or action_type != _text(dispatch.get("action_type")):
        return False
    progress_study_id = _text(action.get("study_id")) or _text(progress.get("study_id"))
    dispatch_study_id = _text(dispatch.get("study_id"))
    if progress_study_id is None or dispatch_study_id != progress_study_id:
        return False
    action_owner = (
        _text(action.get("next_owner"))
        or _text(action.get("owner"))
        or _text(action.get("next_executable_owner"))
    )
    dispatch_owner = (
        _text(dispatch.get("next_executable_owner"))
        or _text(dispatch.get("owner"))
        or _text(dispatch_owner_route(dispatch).get("next_owner"))
    )
    if action_owner is None or dispatch_owner != action_owner:
        return False
    action_work_unit = _owner_action_work_unit_id(action)
    dispatch_work_unit = _dispatch_work_unit_id(dispatch)
    if action_work_unit is None or dispatch_work_unit != action_work_unit:
        return False
    action_fingerprint = _owner_action_work_unit_fingerprint(action)
    if action_fingerprint is None:
        return False
    return action_fingerprint in _dispatch_work_unit_fingerprint_values(dispatch)


def _owner_action_work_unit_id(action: Mapping[str, Any]) -> str | None:
    return (
        _work_unit_id(action.get("work_unit_id"))
        or _work_unit_id(action.get("next_work_unit"))
        or _work_unit_id(action.get("work_unit"))
    )


def _owner_action_work_unit_fingerprint(action: Mapping[str, Any]) -> str | None:
    return (
        _text(action.get("work_unit_fingerprint"))
        or _text(action.get("action_fingerprint"))
        or _text(action.get("source_fingerprint"))
    )


def _dispatch_work_unit_id(dispatch: Mapping[str, Any]) -> str | None:
    route = dispatch_owner_route(dispatch)
    refs = _mapping(route.get("source_refs"))
    basis = _mapping(refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    return (
        _work_unit_id(refs.get("work_unit_id"))
        or _work_unit_id(basis.get("work_unit_id"))
        or _work_unit_id(prompt_contract.get("next_work_unit"))
        or _work_unit_id(dispatch.get("next_work_unit"))
        or _work_unit_id(source_action.get("next_work_unit"))
    )


def _dispatch_work_unit_fingerprint_values(dispatch: Mapping[str, Any]) -> set[str]:
    route = dispatch_owner_route(dispatch)
    refs = _mapping(route.get("source_refs"))
    basis = _mapping(refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(route.get("currentness_contract")).get("basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    prompt_basis = _mapping(prompt_contract.get("owner_route_currentness_basis"))
    source_action = _mapping(dispatch.get("source_action"))
    values = (
        dispatch.get("work_unit_fingerprint"),
        dispatch.get("action_fingerprint"),
        dispatch.get("source_fingerprint"),
        prompt_contract.get("work_unit_fingerprint"),
        prompt_contract.get("action_fingerprint"),
        prompt_basis.get("work_unit_fingerprint"),
        route.get("work_unit_fingerprint"),
        route.get("source_fingerprint"),
        refs.get("work_unit_fingerprint"),
        basis.get("work_unit_fingerprint"),
        source_action.get("work_unit_fingerprint"),
        source_action.get("action_fingerprint"),
    )
    return {text for value in values if (text := _text(value)) is not None}


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


def _terminal_closeout_owner_answer_dispatch_route(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
    fresh_progress: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    progress = (
        fresh_progress
        if fresh_progress is not None
        else persisted_dispatches.read_fresh_study_progress(profile=profile, study_id=study_id)
    )
    if not persisted_dispatches.dispatch_matches_terminal_closeout_owner_answer(
        progress=progress,
        dispatch=dispatch,
    ):
        return None
    dispatch_route = dispatch_owner_route(dispatch)
    if not dispatch_route:
        return None
    if owner_route_block_reason(dispatch=dispatch, current_route=dispatch_route) is not None:
        return None
    return dispatch_route


def _stage_native_dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any] | None:
    source_action = _mapping(dispatch.get("source_action"))
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_surface = _text(source_action.get("source_surface")) or _text(
        _mapping(dispatch_owner_route(dispatch).get("source_refs")).get("source_surface")
    )
    if _text(source_action.get("authority")) != "stage_native_workspace_next_action":
        return None
    if source_surface not in {
        "artifacts/supervision/paper_clean_room_rebuild/latest.json",
        "artifacts/reports/medical_publication_surface/latest.json",
    }:
        return None
    route = dispatch_owner_route(dispatch)
    currentness = _mapping(_mapping(route.get("source_refs")).get("owner_route_currentness_basis"))
    if not currentness:
        currentness = _mapping(prompt_contract.get("owner_route_currentness_basis"))
    if not currentness:
        return None
    return route or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "dispatch_owner_route",
    "execution_owner_route",
    "owner_route_block_reason",
]
