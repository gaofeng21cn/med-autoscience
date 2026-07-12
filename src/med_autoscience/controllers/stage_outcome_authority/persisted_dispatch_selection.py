from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.stage_outcome_authority import owner_route_policy as owner_route_part

from . import current_writer_handoff
from . import fresh_progress_owner_actions
from . import opl_execution_preflight
from . import owner_request_selection
from . import persisted_handoff_selection
from . import progress_blocking_selection
from . import runtime_current_dispatch_selection
from . import scan_route_currentness
from . import publication_handoff_currentness
from . import stage_native_dispatch_selection
from . import terminal_closeout_owner_answer_dispatch


def selected_dispatches_only(
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
        if dispatch_currentness_score(dispatch, current_study) > (0, 0):
            selected.append(dispatch)
            continue
        if terminal_closeout_owner_answer_required(
            fresh_progress
        ) and dispatch_matches_terminal_closeout_owner_answer(
            progress=fresh_progress,
            dispatch=dispatch,
        ):
            selected.append(dispatch)
            continue
        if owner_request_selection.owner_request_matches_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=dispatch,
            fresh_progress=fresh_progress,
        ):
            selected.append(dispatch)
            continue
        if scan_route_currentness.live_provider_attempt_owner_route_from_scan_payload(
            scan_payload=scan_route_currentness.scan_latest_payload(profile),
            study_id=study_id,
            dispatch=dispatch,
        ):
            selected.append(dispatch)
            continue
        if fresh_progress_owner_action_selectable(
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
        if current_writer_handoff.current_quality_repair_writer_handoff_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=dispatch,
            fresh_progress=fresh_progress,
        ):
            selected.append(dispatch)
            continue
        if not current_control_authority_present(current_study) and not scan_route_currentness.dispatch_owner_route(dispatch):
            selected.append(dispatch)
    return selected


def consumed_transition_current_dispatches_only(
    *,
    current_study: Mapping[str, Any],
    dispatches: list[dict[str, Any]],
    profile: WorkspaceProfile,
    study_id: str,
) -> list[dict[str, Any]]:
    if not scan_route_currentness.consumed_transition_owner_route(current_study):
        return dispatches
    if publication_handoff_currentness.is_current(current_study):
        return dispatches
    current: list[dict[str, Any]] = []
    for dispatch in dispatches:
        action_type = _text(dispatch.get("action_type")) or ""
        if is_ready_mas_foreground_owner_callable(dispatch) and (
            scan_route_currentness.matching_consumed_transition_route(
                current_study=current_study,
                dispatch=dispatch,
            )
            is not None
        ):
            current.append(dispatch)
            continue
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


def is_ready_mas_foreground_owner_callable(dispatch: Mapping[str, Any]) -> bool:
    return (
        _text(dispatch.get("adapter_kind")) == "mas_foreground_owner_callable_adapter"
        and _text(dispatch.get("dispatch_status")) == "ready"
        and dispatch.get("mas_dispatch_authority") is True
        and _text(dispatch.get("target_runtime_owner")) == "med-autoscience"
    )


def current_study_with_consumed_transition_route(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
) -> dict[str, Any]:
    return with_consumed_transition_owner_route(scan_route_currentness.scan_study(scan_payload, study_id))


def current_materialized_dispatches_for_current_route(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
    current_study: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not dispatches:
        return []
    if scan_route_currentness.consumed_transition_owner_route(current_study):
        return consumed_transition_current_dispatches_only(
            current_study=current_study,
            dispatches=dispatches,
            profile=profile,
            study_id=study_id,
        )
    runtime_current = runtime_current_dispatch_selection.current_dispatches_only(
        dispatches=dispatches,
        current_study=current_study,
        dispatch_currentness_score=dispatch_currentness_score,
    )
    return runtime_current or dispatches


def dispatches_selectable_despite_blocking_progress(
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
        if dispatch_selectable_despite_blocking_progress(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
            current_study=current_study,
            fresh_progress=fresh_progress,
        )
    ]


def dispatch_selectable_despite_blocking_progress(
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
    if dispatch_currentness_score(dispatch, current_study) > (0, 0):
        return True
    if terminal_closeout_owner_answer_required(
        fresh_progress
    ) and dispatch_matches_terminal_closeout_owner_answer(
        progress=fresh_progress,
        dispatch=dispatch,
    ):
        return True
    if owner_request_selection.owner_request_matches_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
        fresh_progress=fresh_progress,
    ):
        return True
    if scan_route_currentness.live_provider_attempt_owner_route_from_scan_payload(
        scan_payload={"studies": [dict(current_study)]},
        study_id=study_id,
        dispatch=dispatch,
    ):
        return True
    if fresh_progress_owner_action_selectable(
        current_study=current_study,
        progress=fresh_progress,
        dispatch=dispatch,
    ):
        return True
    if current_writer_handoff.current_quality_repair_writer_handoff_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
        fresh_progress=fresh_progress,
    ):
        return True
    return False


def runtime_current_dispatches_only(
    *,
    study_id: str,
    dispatches: list[dict[str, Any]],
    current_study: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return runtime_current_dispatch_selection.runtime_current_dispatches_only(
        study_id=study_id,
        dispatches=dispatches,
        current_study=current_study,
        dispatch_currentness_score=dispatch_currentness_score,
        live_provider_attempt_owner_route_from_scan_payload=scan_route_currentness.live_provider_attempt_owner_route_from_scan_payload,
    )


def with_consumed_transition_owner_route(current_study: Mapping[str, Any]) -> dict[str, Any]:
    return scan_route_currentness.with_consumed_transition_owner_route(current_study)


def fresh_progress_owner_action_selectable(
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


def current_control_authority_present(current_study: Mapping[str, Any]) -> bool:
    return bool(owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route"))))


def terminal_closeout_owner_answer_dispatches_only(
    *,
    progress: Mapping[str, Any],
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return terminal_closeout_owner_answer_dispatch.terminal_closeout_owner_answer_dispatches_only(
        progress=progress,
        dispatches=dispatches,
        dispatch_work_unit_id=dispatch_work_unit_id,
    )


def terminal_closeout_owner_answer_required(progress: Mapping[str, Any]) -> bool:
    return terminal_closeout_owner_answer_dispatch.terminal_closeout_owner_answer_required(progress)


def dispatch_matches_terminal_closeout_owner_answer(
    *,
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    return terminal_closeout_owner_answer_dispatch.dispatch_matches_terminal_closeout_owner_answer(
        progress=progress,
        dispatch=dispatch,
        dispatch_work_unit_id=dispatch_work_unit_id,
    )


def read_fresh_study_progress(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any]:
    return stage_native_dispatch_selection.read_fresh_study_progress(profile=profile, study_id=study_id)


def consumed_transition_current_control_present(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
) -> bool:
    return bool(scan_route_currentness.consumed_transition_owner_route(scan_route_currentness.scan_study(scan_payload, study_id)))


def prefer_current_dispatch(
    *,
    profile: WorkspaceProfile,
    consumer_dispatch: Mapping[str, Any],
    persisted_dispatch: Mapping[str, Any],
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
    fresh_progress: Mapping[str, Any],
) -> dict[str, Any]:
    action_type = _text(persisted_dispatch.get("action_type")) or ""
    if persisted_handoff_selection.persisted_handoff_supersedes_consumer_inline(
        study_id=study_id,
        action_type=action_type,
        consumer_dispatch=consumer_dispatch,
        persisted_dispatch=persisted_dispatch,
        owner_request_current=owner_request_selection.owner_request_matches_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=persisted_dispatch,
            fresh_progress=fresh_progress,
        ),
    ):
        return dict(persisted_dispatch)
    current_study = scan_route_currentness.scan_study(scan_payload, study_id)
    consumer_score = dispatch_currentness_score(consumer_dispatch, current_study)
    persisted_score = dispatch_currentness_score(persisted_dispatch, current_study)
    if (
        is_ai_route_context_projection(consumer_dispatch)
        and persisted_score >= consumer_score
        and persisted_score > (0, 0)
    ):
        return dict(persisted_dispatch)
    if persisted_score > consumer_score:
        return dict(persisted_dispatch)
    return dict(consumer_dispatch)


def dispatch_currentness_score(dispatch: Mapping[str, Any], current_study: Mapping[str, Any]) -> tuple[int, int]:
    if stage_native_dispatch_missing_opl_proof(dispatch):
        return (0, 0)
    return scan_route_currentness.dispatch_currentness_score(dispatch, current_study)


def stage_native_dispatch_missing_opl_proof(dispatch: Mapping[str, Any]) -> bool:
    return (
        stage_native_dispatch_selection.dispatch_uses_stage_native_next_action(dispatch)
        and not stage_native_dispatch_selection.dispatch_has_opl_execution_proof(dispatch)
    )


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return scan_route_currentness.dispatch_owner_route(dispatch)


def dispatch_work_unit_id(dispatch: Mapping[str, Any]) -> str | None:
    return fresh_progress_owner_actions.dispatch_work_unit_id(dispatch)


def is_ai_route_context_projection(dispatch: Mapping[str, Any]) -> bool:
    return (
        _text(dispatch.get("surface")) == "mas_ai_route_context_projection"
        or dispatch.get("owner_callable_carrier_projection_only") is True
    )


def mapping(value: object) -> dict[str, Any]:
    return _mapping(value)


def text(value: object) -> str | None:
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
