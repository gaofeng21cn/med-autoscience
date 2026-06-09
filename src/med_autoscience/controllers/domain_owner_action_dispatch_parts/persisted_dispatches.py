from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers import stage_native_next_action_admission
from med_autoscience.controllers.owner_route_reconcile_parts import domain_route_contract
from med_autoscience.runtime_control import owner_route as owner_route_part

from . import consumed_transition_owner_routes
from . import owner_request_currentness
from . import owner_request_paths
from . import consumed_default_executor_dispatch_filter
from . import consumed_writer_handoff_filter
from . import current_writer_handoff
from . import persisted_handoff_selection
from . import publication_owner_materialization_currentness
from . import runtime_current_dispatch_selection
from . import stage_artifact_publication_handoff_currentness
from . import writer_handoff_currentness


SUPERVISION_LATEST_RELATIVE_PATH = domain_route_contract.SUPERVISION_LATEST_RELATIVE_PATH
CONSUMER_LATEST_RELATIVE_PATH = Path("runtime/artifacts/supervision/consumer/latest.json")
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
        if stage_native_next_action_admission.dispatch_uses_stage_native_next_action(
            payload
        ) and not _stage_native_next_action_matches_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=payload,
        ):
            continue
        scan_payload = scan_latest_payload(profile)
        current_study = _scan_study(scan_payload, study_id)
        consumer_dispatch_current = _consumer_latest_matches_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=payload,
        )
        scan_route_current = (
            consumer_dispatch_current
            and _dispatch_currentness_score(payload, current_study) > (0, 0)
        )
        stage_native_next_action_current = _stage_native_next_action_matches_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=payload,
        )
        if _stage_native_next_action(profile=profile, study_id=study_id) is not None and not stage_native_next_action_current:
            continue
        if current_writer_handoff.fresh_progress_ticket_supersedes_action(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
        ):
            scan_route_current = False
        if require_current_authority and (
            not owner_request_matches_dispatch(
                profile=profile,
                study_id=study_id,
                action_type=action_type,
                dispatch=payload,
            )
            and not scan_route_current
            and not live_provider_attempt_owner_route_from_scan_payload(
                scan_payload=scan_payload,
                study_id=study_id,
                dispatch=payload,
            )
            and not stage_native_next_action_current
            and not current_writer_handoff.current_quality_repair_writer_handoff_dispatch(
                profile=profile,
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


def _consumer_latest_matches_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> bool:
    dispatch_path = _text(_mapping(dispatch.get("refs")).get("dispatch_path"))
    if dispatch_path is None:
        return False
    for candidate in current_consumer_dispatches(
        study_id=study_id,
        consumer_payload=None,
        consumer_latest_path=profile.workspace_root / CONSUMER_LATEST_RELATIVE_PATH,
    ):
        if _text(candidate.get("action_type")) != _text(dispatch.get("action_type")):
            continue
        candidate_path = _text(_mapping(candidate.get("refs")).get("dispatch_path"))
        if candidate_path is None:
            continue
        if Path(candidate_path).expanduser().resolve() == Path(dispatch_path).expanduser().resolve():
            return True
    return False


def selected_dispatches(
    *, profile: WorkspaceProfile, study_id: str, action_types: tuple[str, ...],
    consumer_payload: Mapping[str, Any] | None, consumer_latest_path: Path,
    scan_payload: Mapping[str, Any] | None, supported_action_types: frozenset[str],
    dispatch_relative_root: Path,
) -> list[dict[str, Any]]:
    if _fresh_progress_envelope_blocks_dispatch_selection(profile=profile, study_id=study_id):
        return []
    current_study = _scan_study(scan_payload, study_id)
    current_study = _with_consumed_transition_owner_route(current_study)
    stage_native_next_action = None if action_types else _stage_native_next_action(profile=profile, study_id=study_id)
    consumer_dispatches = current_consumer_dispatches(
        study_id=study_id,
        consumer_payload=consumer_payload,
        consumer_latest_path=consumer_latest_path,
    )
    consumer_dispatches = _without_unauthorized_stage_native_dispatches(
        profile=profile,
        study_id=study_id,
        dispatches=consumer_dispatches,
    )
    consumer_dispatches = consumed_writer_handoff_filter.without_consumed_quality_repair_writer_handoffs(
        profile=profile,
        study_id=study_id,
        dispatches=consumer_dispatches,
    )
    consumer_dispatches = consumed_default_executor_dispatch_filter.without_consumed_default_executor_dispatches(
        profile=profile,
        study_id=study_id,
        dispatches=consumer_dispatches,
    )
    if stage_native_next_action is not None and _stage_native_next_action_superseded_by_current_control(
        profile=profile,
        study_id=study_id,
        next_action=stage_native_next_action,
        current_study=current_study,
        consumer_dispatches=consumer_dispatches,
    ):
        stage_native_next_action = None
    effective_action_types = action_types
    if stage_native_next_action is not None and (
        stage_native_action_type := _text(stage_native_next_action.get("action_type"))
    ) is not None:
        effective_action_types = (stage_native_action_type,)
    if stage_native_next_action is not None:
        consumer_dispatches = _stage_native_next_action_dispatches_only(
            next_action=stage_native_next_action,
            dispatches=consumer_dispatches,
        )
    current_dispatches = runtime_current_dispatch_selection.current_dispatches_only(
        dispatches=consumer_dispatches,
        current_study=current_study,
        dispatch_currentness_score=_dispatch_currentness_score,
    )
    requested = set(effective_action_types)
    if not effective_action_types:
        selected = [
            payload
            for payload in current_dispatches
            if _text(payload.get("action_type")) in supported_action_types
        ]
        selected_by_key = {
            (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type"))): index
            for index, payload in enumerate(selected)
        }
        for payload in consumed_default_executor_dispatch_filter.without_consumed_default_executor_dispatches(
            profile=profile,
            study_id=study_id,
            dispatches=consumed_writer_handoff_filter.without_consumed_quality_repair_writer_handoffs(
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
        if stage_native_next_action is not None:
            stage_native_selected = _stage_native_next_action_dispatches_only(
                next_action=stage_native_next_action,
                dispatches=selected,
            )
            if stage_native_selected:
                return stage_native_selected
        if _consumed_transition_owner_route(current_study):
            return []
        if _current_control_authority_present(current_study):
            return []
        return [
            payload
            for payload in consumer_dispatches
            if _text(payload.get("action_type")) in supported_action_types
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
    for payload in consumed_default_executor_dispatch_filter.without_consumed_default_executor_dispatches(
        profile=profile,
        study_id=study_id,
        dispatches=consumed_writer_handoff_filter.without_consumed_quality_repair_writer_handoffs(
            profile=profile,
            study_id=study_id,
            dispatches=explicit_action_dispatches(
                profile=profile,
                study_id=study_id,
                action_types=effective_action_types,
                supported_action_types=supported_action_types,
                dispatch_relative_root=dispatch_relative_root,
                require_current_authority=True,
            ),
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
    if stage_native_next_action is not None:
        stage_native_selected = _stage_native_next_action_dispatches_only(
            next_action=stage_native_next_action,
            dispatches=selected,
        )
        if stage_native_selected:
            return stage_native_selected
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
    if _current_control_authority_present(current_study):
        return []
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
        if _stage_native_next_action_matches_dispatch(
            profile=profile,
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
        if not _current_control_authority_present(current_study) and not _dispatch_owner_route(dispatch):
            selected.append(dispatch)
    return selected


def _without_unauthorized_stage_native_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if not stage_native_next_action_admission.dispatch_uses_stage_native_next_action(dispatch)
        or _stage_native_next_action_matches_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
        )
    ]


def _scan_action_queue_matches_dispatch(
    *,
    current_study: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    return _current_action_queue_owner_route(current_study, dispatch=dispatch) is not None


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
    return consumed_transition_owner_routes.with_consumed_transition_owner_route(current_study)


def _current_control_authority_present(current_study: Mapping[str, Any]) -> bool:
    return bool(
        owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
        or _mapping(current_study.get("current_work_unit"))
        or current_study.get("action_queue")
        or current_study.get("running_provider_attempt") is True
    )


def _fresh_progress_envelope_blocks_dispatch_selection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> bool:
    progress = _read_fresh_study_progress(profile=profile, study_id=study_id)
    envelope = _mapping(progress.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind == "typed_blocker" and _fresh_progress_typed_blocker_reason(envelope) == "medical_paper_readiness_missing":
        return False
    return state_kind in {"typed_blocker", "parked", "running_provider_attempt"}


def _fresh_progress_typed_blocker_reason(envelope: Mapping[str, Any]) -> str | None:
    blocker = _mapping(envelope.get("typed_blocker"))
    return (
        _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("reason"))
    )


def _stage_native_next_action_superseded_by_current_control(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    next_action: Mapping[str, Any],
    current_study: Mapping[str, Any],
    consumer_dispatches: list[dict[str, Any]],
) -> bool:
    if not current_study:
        return False
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    allowed_actions = {_text(item) for item in route.get("allowed_actions") or []}
    allowed_actions.discard(None)
    if _fresh_progress_typed_blocker_reason(
        _mapping(_read_fresh_study_progress(profile=profile, study_id=study_id).get("current_execution_envelope"))
    ) == "medical_paper_readiness_missing" and (
        not allowed_actions
        or "complete_medical_paper_readiness_surface" in allowed_actions
        or _text(next_action.get("action_type")) in allowed_actions
    ):
        return False
    current_dispatches = _runtime_current_dispatches_only(
        study_id=study_id,
        dispatches=consumer_dispatches,
        current_study=current_study,
    )
    if current_dispatches:
        return not bool(
            _stage_native_next_action_dispatches_only(
                next_action=next_action,
                dispatches=current_dispatches,
            )
        )
    if not allowed_actions:
        return False
    action_type = _text(next_action.get("action_type"))
    owner = _text(next_action.get("owner"))
    return not owner_route_part.route_allows_action(
        action={
            "action_type": action_type,
            "owner": owner,
            "next_executable_owner": owner,
        },
        owner_route=route,
    )


def _stage_native_next_action(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    payload = _read_json_object(profile.studies_root / study_id / "control" / "next_action.json")
    if not payload:
        return None
    if _text(payload.get("status")) != "ready_for_owner_action":
        return None
    action_type = _stage_native_next_action_type(payload)
    if action_type is None:
        return None
    if not stage_native_next_action_admission.default_dispatch_allowed(payload):
        return None
    return {
        **payload,
        "action_type": action_type,
    }


def _stage_native_next_action_dispatches_only(
    *,
    next_action: Mapping[str, Any],
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if _dispatch_matches_stage_native_next_action(next_action=next_action, dispatch=dispatch)
    ]


def _stage_native_next_action_matches_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> bool:
    next_action = _stage_native_next_action(profile=profile, study_id=study_id)
    if next_action is None:
        return False
    return _dispatch_matches_stage_native_next_action(next_action=next_action, dispatch=dispatch)


def _dispatch_matches_stage_native_next_action(
    *,
    next_action: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    action_type = _text(next_action.get("action_type"))
    if action_type is None or _text(dispatch.get("action_type")) != action_type:
        return False
    owner = _text(next_action.get("owner"))
    if owner is not None and _text(dispatch.get("next_executable_owner")) != owner:
        return False
    source_action = _mapping(dispatch.get("source_action"))
    if _text(source_action.get("authority")) != "stage_native_workspace_next_action":
        return False
    route = _dispatch_owner_route(dispatch)
    source_refs = _mapping(route.get("source_refs"))
    source_surface = _text(next_action.get("source_surface"))
    if source_surface is not None and source_surface not in {
        _text(source_action.get("source_surface")),
        _text(source_refs.get("source_surface")),
    }:
        return False
    current_stage_id = _text(next_action.get("current_stage_id"))
    if current_stage_id is not None and current_stage_id not in {
        _text(source_action.get("current_stage_id")),
        _text(source_refs.get("current_stage_id")),
    }:
        return False
    return True


def _stage_native_next_action_type(next_action: Mapping[str, Any]) -> str | None:
    direct = _text(next_action.get("action_type"))
    if direct is not None:
        return direct
    action_id = _text(next_action.get("action_id"))
    if action_id is not None and not action_id.startswith("stage-native-next-action::"):
        return action_id
    return None


def _read_fresh_study_progress(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any]:
    try:
        from med_autoscience.controllers import study_progress

        payload = study_progress.read_study_progress(
            profile=profile,
            study_id=study_id,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        )
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _consumed_transition_owner_route(current_study: Mapping[str, Any]) -> dict[str, Any]:
    return consumed_transition_owner_routes.consumed_transition_owner_route(current_study)


def _gate_replay_route(route: Mapping[str, Any]) -> bool:
    return consumed_transition_owner_routes.gate_replay_route(route)


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
    if (
        _dispatch_matches_current_route(dispatch=dispatch, current_route=bridged_route)
        or _dispatch_matches_current_route(dispatch=dispatch, current_route=publication_owner_bridged_route)
    ):
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
    return None, None


def diagnostic_owner_route_from_scan_payload(
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
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if route:
        return route, "scan_latest"
    if dispatch is not None:
        action_route = _current_action_queue_owner_route(current_study, dispatch=dispatch)
        if action_route is not None:
            return action_route, "scan_action_queue"
    return None, None


def _matching_consumed_transition_route(
    *,
    current_study: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    return consumed_transition_owner_routes.matching_consumed_transition_route(
        current_study=current_study,
        dispatch=dispatch,
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
    inline_dispatch = _inline_default_executor_dispatch(latest, study_id=study_id)
    if inline_dispatch is not None:
        return [inline_dispatch]
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


def _inline_default_executor_dispatch(payload: Mapping[str, Any], *, study_id: str) -> dict[str, Any] | None:
    if _text(payload.get("surface")) != "default_executor_dispatch_request":
        return None
    if _text(payload.get("study_id")) != study_id:
        return None
    if _text(payload.get("dispatch_status")) != "ready":
        return None
    refs = _mapping(payload.get("refs"))
    if not _text(refs.get("dispatch_path")):
        return None
    if not _text(payload.get("action_type")):
        return None
    return dict(payload)


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
    if current_writer_handoff.fresh_progress_ticket_supersedes_action(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
    ):
        return None
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
    if stage_artifact_publication_handoff_currentness.is_current(current_study) and _text(dispatch.get("action_type")) != "publication_handoff_owner_gate":
        return False
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
    "diagnostic_owner_route_from_scan_payload",
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
