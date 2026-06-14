from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part

from . import current_writer_handoff
from . import owner_request_currentness
from . import owner_request_paths
from . import scan_route_currentness
from . import stage_artifact_publication_handoff_currentness


OWNER_REQUEST_RELATIVE_PATHS = owner_request_paths.OWNER_REQUEST_RELATIVE_PATHS
owner_request_payload = owner_request_paths.owner_request_payload
owner_request_path = owner_request_paths.owner_request_path


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
        scan_payload=scan_route_currentness.scan_latest_payload(profile),
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
    current_study = scan_route_currentness.scan_study(scan_payload, study_id)
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
    dispatch_owner = _text(dispatch.get("next_executable_owner")) or _text(
        scan_route_currentness.dispatch_owner_route(dispatch).get("next_owner")
    )
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
    if (
        stage_artifact_publication_handoff_currentness.is_current(current_study)
        and _text(dispatch.get("action_type")) != "publication_handoff_owner_gate"
    ):
        return False
    if (
        scan_route_currentness.live_provider_attempt_owner_route_from_scan_payload(
            scan_payload={"studies": [dict(current_study)]},
            study_id=_text(current_study.get("study_id")) or _text(request_route.get("study_id")) or "",
            dispatch=dispatch,
        )
        is not None
    ):
        return True
    consumed_transition_route = scan_route_currentness.matching_consumed_transition_route(
        current_study=current_study,
        dispatch=dispatch,
    )
    if consumed_transition_route is not None:
        return True
    scan_route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if scan_route_currentness.dispatch_matches_current_route(dispatch=dispatch, current_route=scan_route):
        return True
    if scan_route_currentness.current_action_queue_owner_route(current_study, dispatch=dispatch) is not None:
        return True
    return owner_request_currentness.route_basis_matches_current_study(
        request_route=request_route,
        current_study=current_study,
        consumed_transition_route=scan_route_currentness.consumed_transition_owner_route(current_study),
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
    dispatch_route = scan_route_currentness.dispatch_owner_route(dispatch)
    if not dispatch_route:
        return {}
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=dispatch_route):
        return {}
    return dispatch_route


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "OWNER_REQUEST_RELATIVE_PATHS",
    "owner_request_matches_dispatch",
    "owner_request_path",
    "owner_request_payload",
    "owner_request_route",
]
