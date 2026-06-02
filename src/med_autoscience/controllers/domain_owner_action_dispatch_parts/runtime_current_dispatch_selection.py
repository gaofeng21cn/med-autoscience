from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


CurrentnessScore = Callable[[Mapping[str, Any], Mapping[str, Any]], tuple[int, int]]
LiveProviderRoute = Callable[..., Mapping[str, Any] | None]
CurrentRouteForDispatch = Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any] | None]
RouteAllowsAction = Callable[[Mapping[str, Any], Mapping[str, Any]], bool]


def current_dispatches_only(
    *,
    dispatches: list[dict[str, Any]],
    current_study: Mapping[str, Any],
    dispatch_currentness_score: CurrentnessScore,
) -> list[dict[str, Any]]:
    if not current_study:
        return dispatches
    return [
        dispatch
        for dispatch in dispatches
        if dispatch_currentness_score(dispatch, current_study) > (0, 0)
    ]


def current_route_allows_dispatch_action(
    *,
    current_study: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    current_owner_route_from_scan: CurrentRouteForDispatch,
    route_allows_action: RouteAllowsAction,
) -> bool:
    current_route = current_owner_route_from_scan(current_study, dispatch)
    return bool(current_route and route_allows_action(dispatch, current_route))


def runtime_current_dispatches_only(
    *,
    study_id: str,
    dispatches: list[dict[str, Any]],
    current_study: Mapping[str, Any],
    dispatch_currentness_score: CurrentnessScore,
    live_provider_attempt_owner_route_from_scan_payload: LiveProviderRoute,
) -> list[dict[str, Any]]:
    if not current_study:
        return []
    scan_payload = {"studies": [dict(current_study)]}
    selected: list[dict[str, Any]] = []
    for dispatch in dispatches:
        if dispatch_currentness_score(dispatch, current_study) > (0, 0):
            selected.append(dispatch)
            continue
        if live_provider_attempt_owner_route_from_scan_payload(
            scan_payload=scan_payload,
            study_id=study_id,
            dispatch=dispatch,
        ):
            selected.append(dispatch)
    return selected


__all__ = [
    "current_dispatches_only",
    "current_route_allows_dispatch_action",
    "runtime_current_dispatches_only",
]
