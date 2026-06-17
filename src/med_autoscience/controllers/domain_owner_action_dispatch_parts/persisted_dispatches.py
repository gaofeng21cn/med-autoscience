from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.owner_callable_adapter_projection import owner_callable_adapters
from med_autoscience.runtime_control import owner_route as owner_route_part

from . import accepted_owner_gate_decision
from . import consumed_default_executor_dispatch_filter
from . import consumed_writer_handoff_filter
from . import current_writer_handoff
from . import fresh_progress_owner_actions
from . import opl_execution_preflight
from . import owner_request_selection
from . import persisted_handoff_selection
from . import progress_blocking_selection
from . import runtime_current_dispatch_selection
from . import scan_route_currentness
from . import stage_native_dispatch_selection
from . import stage_artifact_publication_handoff_currentness
from . import terminal_closeout_owner_answer_dispatch


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
        if (
            not provider_hosted_stage_run_current
            and stage_native_dispatch_selection.dispatch_uses_stage_native_next_action(payload)
            and not stage_native_dispatch_selection.next_action_matches_dispatch(
                profile=profile,
                study_id=study_id,
                dispatch=payload,
            )
        ):
            continue
        scan_payload = scan_latest_payload(profile)
        current_study = scan_route_currentness.scan_study(scan_payload, study_id)
        consumer_dispatch_current = _consumer_latest_matches_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=payload,
        )
        scan_route_current = (
            consumer_dispatch_current
            and scan_route_currentness.dispatch_currentness_score(payload, current_study) > (0, 0)
        )
        stage_native_next_action_current = stage_native_dispatch_selection.next_action_matches_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=payload,
        )
        if (
            not provider_hosted_stage_run_current
            and stage_native_dispatch_selection.next_action(
                profile=profile, study_id=study_id
            )
            is not None
            and not stage_native_next_action_current
        ):
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
            and not accepted_owner_gate_decision.dispatch_matches_study_progress(
                profile=profile, study_id=study_id, dispatch=payload
            )
            and not _fresh_progress_owner_action_selectable(
                current_study=current_study,
                progress=_mapping(fresh_progress),
                dispatch=payload,
            )
            and not live_provider_attempt_owner_route_from_scan_payload(
                scan_payload=scan_payload,
                study_id=study_id,
                dispatch=payload,
            )
            and not provider_hosted_stage_run_current
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
    fresh_progress: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    fresh_progress = (
        dict(fresh_progress)
        if isinstance(fresh_progress, Mapping)
        else stage_native_dispatch_selection.read_fresh_study_progress(profile=profile, study_id=study_id)
    )
    progress_envelope_blocks_dispatch_selection = (
        progress_blocking_selection.fresh_progress_envelope_blocks_dispatch_selection(
            fresh_progress
        )
    )
    terminal_closeout_owner_answer = _terminal_closeout_owner_answer_required(fresh_progress)
    current_study = scan_route_currentness.scan_study(scan_payload, study_id)
    current_study = _with_consumed_transition_owner_route(current_study)
    stage_native_next_action = None if action_types else stage_native_dispatch_selection.next_action(
        profile=profile,
        study_id=study_id,
    )
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
    consumer_dispatches = _terminal_closeout_owner_answer_dispatches_only(
        progress=fresh_progress,
        dispatches=consumer_dispatches,
    )
    paper_recovery_successor_dispatches = _paper_recovery_successor_dispatches(
        progress=fresh_progress,
        dispatches=consumer_dispatches,
    )
    if paper_recovery_successor_dispatches:
        stage_native_next_action = None
    if stage_native_next_action is not None and stage_native_dispatch_selection.next_action_superseded_by_current_control(
        profile=profile,
        study_id=study_id,
        next_action=stage_native_next_action,
        current_study=current_study,
        consumer_dispatches=consumer_dispatches,
        runtime_current_dispatches_only=_runtime_current_dispatches_only,
    ):
        stage_native_next_action = None
    effective_action_types = action_types
    if stage_native_next_action is not None and (
        stage_native_action_type := _text(stage_native_next_action.get("action_type"))
    ) is not None:
        effective_action_types = (stage_native_action_type,)
    if stage_native_next_action is not None:
        consumer_dispatches = stage_native_dispatch_selection.next_action_dispatches_only(
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
        if paper_recovery_successor_dispatches:
            return [
                payload
                for payload in paper_recovery_successor_dispatches
                if _text(payload.get("action_type")) in supported_action_types
            ]
        selected = [
            payload
            for payload in current_dispatches
            if _text(payload.get("action_type")) in supported_action_types
        ]
        selected_by_key = {
            (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type"))): index
            for index, payload in enumerate(selected)
        }
        for payload in paper_recovery_successor_dispatches:
            if _text(payload.get("action_type")) not in supported_action_types:
                continue
            key = (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type")))
            if key in selected_by_key:
                continue
            selected_by_key[key] = len(selected)
            selected.append(payload)
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
                    require_current_authority=not terminal_closeout_owner_answer,
                    fresh_progress=fresh_progress,
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
                scan_route_currentness.dispatch_currentness_score(payload, current_study) <= (0, 0)
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
                )
                and not accepted_owner_gate_decision.dispatch_matches_progress(
                    progress=fresh_progress,
                    dispatch=payload,
                )
                and not _fresh_progress_owner_action_selectable(
                    current_study=current_study,
                    progress=fresh_progress,
                    dispatch=payload,
                )
                and not opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
                    payload
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
        if progress_envelope_blocks_dispatch_selection:
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
        if accepted_owner_gate_selected := accepted_owner_gate_decision.dispatches_only(
            progress=fresh_progress, dispatches=selected
        ):
            return accepted_owner_gate_selected
        if runtime_current_selected:
            return runtime_current_selected
        if current_selected:
            return current_selected
        if stage_native_next_action is not None:
            stage_native_selected = stage_native_dispatch_selection.next_action_dispatches_only(
                next_action=stage_native_next_action,
                dispatches=selected,
            )
            if stage_native_selected:
                return stage_native_selected
        if scan_route_currentness.consumed_transition_owner_route(current_study):
            return []
        if progress_envelope_blocks_dispatch_selection:
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
                require_current_authority=not terminal_closeout_owner_answer,
                fresh_progress=fresh_progress,
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
            )
            continue
        elif key not in selected_keys:
            selected.append(payload)
            selected_keys.add(key)
            selected_by_key[key] = len(selected) - 1
    selected = _consumed_transition_current_dispatches_only(
        current_study=current_study,
        dispatches=selected,
        profile=profile,
        study_id=study_id,
    )
    if scan_route_currentness.consumed_transition_owner_route(current_study) and not selected:
        return []
    if stage_native_next_action is not None:
        stage_native_selected = stage_native_dispatch_selection.next_action_dispatches_only(
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
    if progress_envelope_blocks_dispatch_selection:
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
        return []
    if accepted_owner_gate_selected := accepted_owner_gate_decision.dispatches_only(
        progress=fresh_progress, dispatches=selected
    ):
        return accepted_owner_gate_selected
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
    if progress_envelope_blocks_dispatch_selection:
        return []
    if _current_control_authority_present(current_study):
        return []
    return selected


def _selected_dispatches_only(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
    current_study: Mapping[str, Any],
    fresh_progress: Mapping[str, Any],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for dispatch in dispatches:
        action_type = _text(dispatch.get("action_type")) or ""
        if scan_route_currentness.dispatch_currentness_score(dispatch, current_study) > (0, 0):
            selected.append(dispatch)
            continue
        if _terminal_closeout_owner_answer_required(
            fresh_progress
        ) and _dispatch_matches_terminal_closeout_owner_answer(
            progress=fresh_progress,
            dispatch=dispatch,
        ):
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
        if accepted_owner_gate_decision.dispatch_matches_progress(
            progress=fresh_progress,
            dispatch=dispatch,
        ):
            selected.append(dispatch)
            continue
        if _fresh_progress_owner_action_selectable(
            current_study=current_study,
            progress=fresh_progress,
            dispatch=dispatch,
        ):
            selected.append(dispatch)
            continue
        if opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
            dispatch
        ):
            selected.append(dispatch)
            continue
        if stage_native_dispatch_selection.next_action_matches_dispatch(
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
        if not _current_control_authority_present(current_study) and not scan_route_currentness.dispatch_owner_route(dispatch):
            selected.append(dispatch)
    return selected


def _consumed_transition_current_dispatches_only(
    *,
    current_study: Mapping[str, Any],
    dispatches: list[dict[str, Any]],
    profile: WorkspaceProfile,
    study_id: str,
) -> list[dict[str, Any]]:
    if not scan_route_currentness.consumed_transition_owner_route(current_study):
        return dispatches
    if stage_artifact_publication_handoff_currentness.is_current(current_study):
        return dispatches
    current: list[dict[str, Any]] = []
    for dispatch in dispatches:
        action_type = _text(dispatch.get("action_type")) or ""
        if opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
            dispatch
        ):
            current.append(dispatch)
            continue
        if current_writer_handoff.current_quality_repair_writer_handoff_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=dispatch,
        ):
            current.append(dispatch)
            continue
        if (
            scan_route_currentness.matching_consumed_transition_route(
                current_study=current_study,
                dispatch=dispatch,
            )
            is not None
        ):
            current.append(dispatch)
    return current


def _dispatches_selectable_despite_blocking_progress(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
    current_study: Mapping[str, Any],
    fresh_progress: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if _dispatch_selectable_despite_blocking_progress(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
            current_study=current_study,
            fresh_progress=fresh_progress,
        )
    ]


def _dispatch_selectable_despite_blocking_progress(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
    current_study: Mapping[str, Any],
    fresh_progress: Mapping[str, Any],
) -> bool:
    if opl_execution_preflight.provider_hosted_exact_stage_run_current_execution_authority(
        dispatch
    ):
        return True
    if not progress_blocking_selection.blocking_progress_allows_current_dispatch_selection(
        fresh_progress
    ):
        return False
    action_type = _text(dispatch.get("action_type")) or ""
    if scan_route_currentness.dispatch_currentness_score(dispatch, current_study) > (0, 0):
        return True
    if _terminal_closeout_owner_answer_required(
        fresh_progress
    ) and _dispatch_matches_terminal_closeout_owner_answer(
        progress=fresh_progress,
        dispatch=dispatch,
    ):
        return True
    if owner_request_matches_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return True
    if live_provider_attempt_owner_route_from_scan_payload(
        scan_payload={"studies": [dict(current_study)]},
        study_id=study_id,
        dispatch=dispatch,
    ):
        return True
    if accepted_owner_gate_decision.dispatch_matches_progress(
        progress=fresh_progress,
        dispatch=dispatch,
    ):
        return True
    if _fresh_progress_owner_action_selectable(
        current_study=current_study,
        progress=fresh_progress,
        dispatch=dispatch,
    ):
        return True
    if stage_native_dispatch_selection.next_action_matches_dispatch(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
    ):
        return True
    if current_writer_handoff.current_quality_repair_writer_handoff_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return True
    return False


def _without_unauthorized_stage_native_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return stage_native_dispatch_selection.without_unauthorized_dispatches(
        profile=profile,
        study_id=study_id,
        dispatches=dispatches,
    )


def _scan_action_queue_matches_dispatch(
    *,
    current_study: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    return scan_route_currentness.current_action_queue_owner_route(current_study, dispatch=dispatch) is not None


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
    return scan_route_currentness.with_consumed_transition_owner_route(current_study)


def _fresh_progress_owner_action_selectable(
    *,
    current_study: Mapping[str, Any],
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    return fresh_progress_owner_actions.fresh_progress_owner_action_selectable(
        current_study=current_study,
        progress=progress,
        dispatch=dispatch,
    )


def _paper_recovery_successor_dispatches(
    *,
    progress: Mapping[str, Any],
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if fresh_progress_owner_actions.dispatch_matches_paper_recovery_successor(
            progress=progress,
            dispatch=dispatch,
        )
    ]


def _current_control_authority_present(current_study: Mapping[str, Any]) -> bool:
    return bool(
        owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
        or _mapping(current_study.get("current_work_unit"))
        or current_study.get("action_queue")
        or current_study.get("running_provider_attempt") is True
    )


def _terminal_closeout_owner_answer_dispatches_only(
    *,
    progress: Mapping[str, Any],
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return terminal_closeout_owner_answer_dispatch.terminal_closeout_owner_answer_dispatches_only(
        progress=progress,
        dispatches=dispatches,
        dispatch_work_unit_id=_dispatch_work_unit_id,
    )


def _terminal_closeout_owner_answer_required(progress: Mapping[str, Any]) -> bool:
    return terminal_closeout_owner_answer_dispatch.terminal_closeout_owner_answer_required(progress)


def _dispatch_matches_terminal_closeout_owner_answer(
    *,
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    return terminal_closeout_owner_answer_dispatch.dispatch_matches_terminal_closeout_owner_answer(
        progress=progress,
        dispatch=dispatch,
        dispatch_work_unit_id=_dispatch_work_unit_id,
    )


def read_fresh_study_progress(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any]:
    return stage_native_dispatch_selection.read_fresh_study_progress(profile=profile, study_id=study_id)


def dispatch_matches_terminal_closeout_owner_answer(
    *,
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    return _dispatch_matches_terminal_closeout_owner_answer(progress=progress, dispatch=dispatch)


def consumed_transition_current_control_present(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
) -> bool:
    return bool(scan_route_currentness.consumed_transition_owner_route(scan_route_currentness.scan_study(scan_payload, study_id)))


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
    current_study = scan_route_currentness.scan_study(scan_payload, study_id)
    consumer_score = scan_route_currentness.dispatch_currentness_score(consumer_dispatch, current_study)
    persisted_score = scan_route_currentness.dispatch_currentness_score(persisted_dispatch, current_study)
    if persisted_score > consumer_score:
        return dict(persisted_dispatch)
    return dict(consumer_dispatch)


def _dispatch_currentness_score(dispatch: Mapping[str, Any], current_study: Mapping[str, Any]) -> tuple[int, int]:
    return scan_route_currentness.dispatch_currentness_score(dispatch, current_study)


def _dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return scan_route_currentness.dispatch_owner_route(dispatch)


def _dispatch_work_unit_id(dispatch: Mapping[str, Any]) -> str | None:
    return fresh_progress_owner_actions.dispatch_work_unit_id(dispatch)



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
    for dispatch in _owner_callable_adapter_items(latest):
        payload = _with_owner_callable_adapter_semantics(_mapping(dispatch))
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
    return _with_owner_callable_adapter_semantics(payload)


def _owner_callable_adapter_items(payload: Mapping[str, Any]) -> list[object]:
    return owner_callable_adapters(payload)


def _with_owner_callable_adapter_semantics(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(dispatch)
    payload.setdefault("adapter_kind", "opl_authorized_owner_callable_adapter")
    payload.setdefault("target_runtime_owner", "one-person-lab")
    payload.setdefault("target_runtime_owner_authority_required", True)
    payload.setdefault("mas_creates_opl_outbox", False)
    payload.setdefault("mas_creates_opl_event", False)
    payload.setdefault("mas_creates_opl_stage_run", False)
    payload.setdefault("mas_dispatch_authority", False)
    payload.setdefault("dispatch_ready_for_execution_authority", False)
    return payload


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
