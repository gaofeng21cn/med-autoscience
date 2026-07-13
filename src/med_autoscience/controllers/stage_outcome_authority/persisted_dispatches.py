from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from . import consumer_dispatch_readback
from . import consumed_owner_callable_dispatch_filter
from . import consumed_writer_handoff_filter
from . import current_writer_handoff
from . import opl_execution_preflight
from . import owner_request_selection
from . import persisted_dispatch_selection
from . import persisted_handoff_selection
from . import progress_blocking_selection
from . import runtime_current_dispatch_selection
from . import scan_route_currentness
from . import stage_native_dispatch_selection


SUPERVISION_LATEST_RELATIVE_PATH = scan_route_currentness.SUPERVISION_LATEST_RELATIVE_PATH
CONSUMER_LATEST_RELATIVE_PATH = Path("runtime/artifacts/supervision/consumer/latest.json")
OWNER_REQUEST_RELATIVE_PATHS = owner_request_selection.OWNER_REQUEST_RELATIVE_PATHS
scan_latest_payload = scan_route_currentness.scan_latest_payload
current_owner_route_from_scan_payload = scan_route_currentness.current_owner_route_from_scan_payload
diagnostic_owner_route_from_scan_payload = scan_route_currentness.diagnostic_owner_route_from_scan_payload
live_provider_attempt_owner_route_from_scan_payload = (
    scan_route_currentness.live_provider_attempt_owner_route_from_scan_payload
)
bridged_quality_repair_writer_handoff_route_from_scan_payload = (
    scan_route_currentness.bridged_quality_repair_writer_handoff_route_from_scan_payload
)
bridged_quality_repair_writer_handoff_route = scan_route_currentness.bridged_quality_repair_writer_handoff_route
bridged_publication_owner_materialization_route_from_scan_payload = (
    scan_route_currentness.bridged_publication_owner_materialization_route_from_scan_payload
)
bridged_publication_owner_materialization_route = (
    scan_route_currentness.bridged_publication_owner_materialization_route
)
owner_request_matches_dispatch = owner_request_selection.owner_request_matches_dispatch
owner_request_payload = owner_request_selection.owner_request_payload
owner_request_path = owner_request_selection.owner_request_path
owner_request_route = owner_request_selection.owner_request_route
current_study_with_consumed_transition_route = (
    persisted_dispatch_selection.current_study_with_consumed_transition_route
)
current_materialized_dispatches_for_current_route = (
    persisted_dispatch_selection.current_materialized_dispatches_for_current_route
)
read_fresh_study_progress = persisted_dispatch_selection.read_fresh_study_progress
dispatch_matches_terminal_closeout_owner_answer = (
    persisted_dispatch_selection.dispatch_matches_terminal_closeout_owner_answer
)
consumed_transition_current_control_present = (
    persisted_dispatch_selection.consumed_transition_current_control_present
)


def current_scan_study(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    latest = scan_latest_payload(profile)
    if latest is None:
        return None
    study = scan_route_currentness.scan_study(latest, study_id)
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
    fresh_progress: Mapping[str, Any] | None = None,
    allow_missing_authority_blocker_projection: bool = False,
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
        provider_hosted_stage_run_current = (
            opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
                payload
            )
        )
        scan_payload = scan_latest_payload(profile)
        current_study = scan_route_currentness.scan_study(scan_payload, study_id)
        consumer_dispatch_current = _consumer_latest_matches_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=payload,
        )
        scan_route_current = (
            consumer_dispatch_current
            and _dispatch_currentness_score(payload, current_study) > (0, 0)
        )
        stage_native_execution_current = stage_native_dispatch_selection.dispatch_has_current_execution_proof(
            profile=profile,
            study_id=study_id,
            dispatch=payload,
        )
        stage_native_missing_authority_blocker_projection = (
            allow_missing_authority_blocker_projection
            and stage_native_dispatch_selection.dispatch_uses_stage_native_next_action(payload)
            and not stage_native_execution_current
        )
        if current_writer_handoff.fresh_progress_ticket_supersedes_action(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            fresh_progress=fresh_progress,
        ):
            scan_route_current = False
        current_authority = _explicit_dispatch_current_authority(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=payload,
            fresh_progress=fresh_progress,
            current_study=current_study,
            scan_payload=scan_payload,
            scan_route_current=scan_route_current,
            provider_hosted_stage_run_current=provider_hosted_stage_run_current,
            stage_native_execution_current=stage_native_execution_current,
        )
        if (
            require_current_authority
            and not current_authority
            and not _explicit_request_requires_opl_blocker_projection(
                action_types=action_types,
                dispatch=payload,
            )
            and not stage_native_missing_authority_blocker_projection
        ):
            continue
        key = (str(path), action_type)
        if key in seen:
            continue
        seen.add(key)
        dispatches.append(payload)
    return dispatches


def _explicit_dispatch_current_authority(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
    fresh_progress: Mapping[str, Any] | None,
    current_study: Mapping[str, Any],
    scan_payload: Mapping[str, Any] | None,
    scan_route_current: bool,
    provider_hosted_stage_run_current: bool,
    stage_native_execution_current: bool,
) -> bool:
    return (
        owner_request_matches_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=dispatch,
            fresh_progress=fresh_progress,
        )
        or scan_route_current
        or live_provider_attempt_owner_route_from_scan_payload(
            scan_payload=scan_payload,
            study_id=study_id,
            dispatch=dispatch,
        )
        or provider_hosted_stage_run_current
        or stage_native_execution_current
        or current_writer_handoff.current_quality_repair_writer_handoff_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=dispatch,
            fresh_progress=fresh_progress,
        )
    )


def _explicit_request_requires_opl_blocker_projection(
    *,
    action_types: tuple[str, ...],
    dispatch: Mapping[str, Any],
) -> bool:
    if not action_types:
        return False
    action_type = _text(dispatch.get("action_type"))
    if action_type is None or action_type not in action_types:
        return False
    if _text(dispatch.get("dispatch_status")) != "ready":
        return False
    if not _is_ai_route_context_projection(dispatch):
        return False
    if opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
        dispatch
    ):
        return False
    return True


def _consumer_latest_matches_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> bool:
    dispatch_path = _text(_mapping(dispatch.get("refs")).get("dispatch_path"))
    if dispatch_path is None:
        return False
    for candidate in consumer_dispatch_readback.current_consumer_dispatches(
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
    fresh_progress: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    fresh_progress = (
        dict(fresh_progress)
        if isinstance(fresh_progress, Mapping)
        else stage_native_dispatch_selection.read_fresh_study_progress(profile=profile, study_id=study_id)
    )
    legal_hard_stop_blocks_dispatch_selection = (
        progress_blocking_selection.legal_hard_stop_blocks_dispatch_selection(
            fresh_progress
        )
    )
    terminal_closeout_owner_answer = _terminal_closeout_owner_answer_required(fresh_progress)
    current_study = scan_route_currentness.scan_study(scan_payload, study_id)
    current_study = _with_consumed_transition_owner_route(current_study)
    consumer_dispatches = consumer_dispatch_readback.current_consumer_dispatches(
        study_id=study_id,
        consumer_payload=consumer_payload,
        consumer_latest_path=consumer_latest_path,
    )
    consumer_dispatches = consumed_writer_handoff_filter.without_consumed_quality_repair_writer_handoffs(
        profile=profile,
        study_id=study_id,
        dispatches=consumer_dispatches,
    )
    consumer_dispatches = consumed_owner_callable_dispatch_filter.without_consumed_owner_callable_adapters(
        profile=profile,
        study_id=study_id,
        dispatches=consumer_dispatches,
    )
    consumer_dispatches = _terminal_closeout_owner_answer_dispatches_only(
        progress=fresh_progress,
        dispatches=consumer_dispatches,
    )
    effective_action_types = action_types
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
        for payload in consumed_owner_callable_dispatch_filter.without_consumed_owner_callable_adapters(
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
                    require_current_authority=not terminal_closeout_owner_answer,
                    fresh_progress=fresh_progress,
                    allow_missing_authority_blocker_projection=False,
                ),
            ),
        ):
            if terminal_closeout_owner_answer and not _dispatch_matches_terminal_closeout_owner_answer(
                progress=fresh_progress,
                dispatch=payload,
            ):
                continue
            action_type = _text(payload.get("action_type")) or ""
            if (
                _dispatch_currentness_score(payload, current_study) <= (0, 0)
                and not (
                    terminal_closeout_owner_answer
                    and _dispatch_matches_terminal_closeout_owner_answer(
                        progress=fresh_progress,
                        dispatch=payload,
                    )
                )
                and not owner_request_matches_dispatch(
                    profile=profile,
                    study_id=study_id,
                    action_type=action_type,
                    dispatch=payload,
                    fresh_progress=fresh_progress,
                )
                and not opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
                    payload
                )
                and not current_writer_handoff.current_quality_repair_writer_handoff_dispatch(
                    profile=profile,
                    study_id=study_id,
                    action_type=action_type,
                    dispatch=payload,
                    fresh_progress=fresh_progress,
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
                    fresh_progress=fresh_progress,
                )
                continue
            selected_by_key[key] = len(selected)
            selected.append(payload)
        selected = _consumed_transition_current_dispatches_only(
            current_study=current_study,
            dispatches=selected,
            profile=profile,
            study_id=study_id,
        )
        if scan_route_currentness.consumed_transition_owner_route(current_study) and not selected:
            return []
        current_selected = _selected_dispatches_only(
            profile=profile,
            study_id=study_id,
            dispatches=selected,
            current_study=current_study,
            fresh_progress=fresh_progress,
        )
        runtime_current_selected = _runtime_current_dispatches_only(
            study_id=study_id,
            dispatches=selected,
            current_study=current_study,
        )
        if legal_hard_stop_blocks_dispatch_selection:
            runtime_current_selected = _dispatches_selectable_despite_blocking_progress(
                profile=profile,
                study_id=study_id,
                dispatches=runtime_current_selected,
                current_study=current_study,
                fresh_progress=fresh_progress,
            )
            current_selected = _dispatches_selectable_despite_blocking_progress(
                profile=profile,
                study_id=study_id,
                dispatches=current_selected,
                current_study=current_study,
                fresh_progress=fresh_progress,
            )
        if runtime_current_selected:
            return runtime_current_selected
        if current_selected:
            return current_selected
        if scan_route_currentness.consumed_transition_owner_route(current_study):
            return []
        if legal_hard_stop_blocks_dispatch_selection:
            return []
        if _current_control_authority_present(current_study):
            return []
        return [
            payload
            for payload in consumer_dispatches
            if _text(payload.get("action_type")) in supported_action_types
            and not _stage_native_dispatch_missing_opl_proof(payload)
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
    for payload in consumed_owner_callable_dispatch_filter.without_consumed_owner_callable_adapters(
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
                require_current_authority=not terminal_closeout_owner_answer,
                fresh_progress=fresh_progress,
                allow_missing_authority_blocker_projection=bool(action_types),
            ),
        ),
    ):
        if terminal_closeout_owner_answer and not _dispatch_matches_terminal_closeout_owner_answer(
            progress=fresh_progress,
            dispatch=payload,
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
                fresh_progress=fresh_progress,
            )
            continue
        elif key not in selected_keys:
            selected.append(payload)
            selected_keys.add(key)
            selected_by_key[key] = len(selected) - 1
    stage_native_missing_proof_selected = [
        payload for payload in selected if _stage_native_dispatch_missing_opl_proof(payload)
    ]
    selected = _consumed_transition_current_dispatches_only(
        current_study=current_study,
        dispatches=selected,
        profile=profile,
        study_id=study_id,
    )
    if scan_route_currentness.consumed_transition_owner_route(current_study) and not selected:
        return []
    runtime_current_selected = _runtime_current_dispatches_only(
        study_id=study_id,
        dispatches=selected,
        current_study=current_study,
    )
    if legal_hard_stop_blocks_dispatch_selection:
        runtime_current_selected = _dispatches_selectable_despite_blocking_progress(
            profile=profile,
            study_id=study_id,
            dispatches=runtime_current_selected,
            current_study=current_study,
            fresh_progress=fresh_progress,
        )
        current_selected_candidate = _selected_dispatches_only(
            profile=profile,
            study_id=study_id,
            dispatches=selected,
            current_study=current_study,
            fresh_progress=fresh_progress,
        )
        current_selected_candidate = _dispatches_selectable_despite_blocking_progress(
            profile=profile,
            study_id=study_id,
            dispatches=current_selected_candidate,
            current_study=current_study,
            fresh_progress=fresh_progress,
        )
        if current_selected_candidate:
            return current_selected_candidate
        if runtime_current_selected:
            return runtime_current_selected
        diagnostic_selected = runtime_current_dispatch_selection.diagnostic_dispatches_only(
            dispatches=selected,
            current_control_authority_present=_current_control_authority_present(current_study),
            dispatch_owner_route=_dispatch_owner_route,
        )
        if diagnostic_selected:
            return diagnostic_selected
        if stage_native_missing_proof_selected and action_types:
            return stage_native_missing_proof_selected
        return []
    if runtime_current_selected:
        return runtime_current_selected
    current_selected = _selected_dispatches_only(
        profile=profile,
        study_id=study_id,
        dispatches=selected,
        current_study=current_study,
        fresh_progress=fresh_progress,
    )
    if current_selected:
        return current_selected
    diagnostic_selected = runtime_current_dispatch_selection.diagnostic_dispatches_only(
        dispatches=selected,
        current_control_authority_present=_current_control_authority_present(current_study),
        dispatch_owner_route=_dispatch_owner_route,
    )
    if diagnostic_selected:
        return diagnostic_selected
    if stage_native_missing_proof_selected and action_types:
        return stage_native_missing_proof_selected
    if legal_hard_stop_blocks_dispatch_selection:
        return []
    if _current_control_authority_present(current_study):
        return []
    return selected


_selected_dispatches_only = persisted_dispatch_selection.selected_dispatches_only
_consumed_transition_current_dispatches_only = (
    persisted_dispatch_selection.consumed_transition_current_dispatches_only
)
_is_ready_mas_foreground_owner_callable = (
    persisted_dispatch_selection.is_ready_mas_foreground_owner_callable
)
_dispatches_selectable_despite_blocking_progress = (
    persisted_dispatch_selection.dispatches_selectable_despite_blocking_progress
)
_dispatch_selectable_despite_blocking_progress = (
    persisted_dispatch_selection.dispatch_selectable_despite_blocking_progress
)
_runtime_current_dispatches_only = persisted_dispatch_selection.runtime_current_dispatches_only
_with_consumed_transition_owner_route = (
    persisted_dispatch_selection.with_consumed_transition_owner_route
)
_current_control_authority_present = (
    persisted_dispatch_selection.current_control_authority_present
)
_terminal_closeout_owner_answer_dispatches_only = (
    persisted_dispatch_selection.terminal_closeout_owner_answer_dispatches_only
)
_terminal_closeout_owner_answer_required = (
    persisted_dispatch_selection.terminal_closeout_owner_answer_required
)
_dispatch_matches_terminal_closeout_owner_answer = (
    persisted_dispatch_selection.dispatch_matches_terminal_closeout_owner_answer
)
_prefer_current_dispatch = persisted_dispatch_selection.prefer_current_dispatch
_dispatch_currentness_score = persisted_dispatch_selection.dispatch_currentness_score
_stage_native_dispatch_missing_opl_proof = (
    persisted_dispatch_selection.stage_native_dispatch_missing_opl_proof
)
_dispatch_owner_route = persisted_dispatch_selection.dispatch_owner_route
_dispatch_work_unit_id = persisted_dispatch_selection.dispatch_work_unit_id
_is_ai_route_context_projection = (
    persisted_dispatch_selection.is_ai_route_context_projection
)

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
    "consumed_transition_current_control_present",
    "current_scan_stall",
    "current_scan_study",
    "current_owner_route_from_scan_payload",
    "diagnostic_owner_route_from_scan_payload",
    "explicit_action_dispatches",
    "live_provider_attempt_owner_route_from_scan_payload",
    "owner_request_matches_dispatch",
    "owner_request_payload",
    "owner_request_path",
    "owner_request_route",
    "selected_dispatches",
    "scan_latest_payload",
]
