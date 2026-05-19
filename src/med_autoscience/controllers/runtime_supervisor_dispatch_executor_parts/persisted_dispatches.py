from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


OWNER_REQUEST_RELATIVE_PATHS = {
    "publication_gate_specificity_required": Path("artifacts/supervision/requests/publication_gate_specificity/latest.json"),
    "current_package_freshness_required": Path("artifacts/supervision/requests/current_package_freshness/latest.json"),
    "artifact_display_surface_materialization_required": Path(
        "artifacts/supervision/requests/artifact_display_materialization/latest.json"
    ),
    "return_to_ai_reviewer_workflow": Path("artifacts/supervision/requests/ai_reviewer/latest.json"),
    "canonical_paper_inputs_rehydrate_required": Path(
        "artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json"
    ),
    "unit_harmonized_external_validation_rerun": Path("artifacts/supervision/requests/analysis_harmonization/latest.json"),
    "recover_transport_model_provenance": Path("artifacts/supervision/requests/source_provenance/latest.json"),
    "methodology_reframe_route_decision": Path("artifacts/supervision/requests/decision/latest.json"),
}


def explicit_action_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    supported_action_types: frozenset[str],
    dispatch_relative_root: Path,
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
        if not owner_request_matches_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=action_type,
            dispatch=payload,
        ):
            continue
        key = (str(path), action_type)
        if key in seen:
            continue
        seen.add(key)
        dispatches.append(payload)
    return dispatches


def selected_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_types: tuple[str, ...],
    consumer_payload: Mapping[str, Any] | None,
    consumer_latest_path: Path,
    supported_action_types: frozenset[str],
    dispatch_relative_root: Path,
    managed_runtime_dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    current_dispatches = current_consumer_dispatches(
        study_id=study_id,
        consumer_payload=consumer_payload,
        consumer_latest_path=consumer_latest_path,
    )
    if not current_dispatches and managed_runtime_dispatches:
        return managed_runtime_dispatches
    if not action_types:
        return current_dispatches
    requested = set(action_types)
    selected = [payload for payload in current_dispatches if _text(payload.get("action_type")) in requested]
    selected_keys = {
        (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type")))
        for payload in selected
    }
    for payload in explicit_action_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=action_types,
        supported_action_types=supported_action_types,
        dispatch_relative_root=dispatch_relative_root,
    ):
        key = (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type")))
        if key not in selected_keys:
            selected.append(payload)
            selected_keys.add(key)
    return selected


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
    if not owner_request_matches_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return None
    request = owner_request_payload(profile, study_id, action_type)
    request_route = _mapping(_mapping(request).get("owner_route")) or _mapping(
        _mapping(_mapping(request).get("owner_pickup")).get("owner_route")
    )
    route = owner_route_part.ensure_owner_route_v2(request_route)
    return route or None


def owner_request_matches_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> bool:
    request = owner_request_payload(profile, study_id, action_type)
    if not request:
        return False
    request_kind = _text(request.get("request_kind")) or _text(request.get("action_type"))
    if request_kind != action_type:
        return False
    if _text(request.get("status")) not in {None, "requested", "applied", "pending"}:
        return False
    request_owner = (
        _text(request.get("request_owner"))
        or _text(request.get("expected_owner"))
        or _text(request.get("next_executable_owner"))
        or _text(request.get("assigned_to"))
    )
    dispatch_owner = _text(dispatch.get("next_executable_owner")) or _text(_dispatch_owner_route(dispatch).get("next_owner"))
    if request_owner is not None and dispatch_owner is not None and request_owner != dispatch_owner:
        return False
    request_route = _mapping(request.get("owner_route")) or _mapping(_mapping(request.get("owner_pickup")).get("owner_route"))
    if not owner_route_part.owner_route_matches(dispatch=dispatch, current_route=request_route):
        return False
    return owner_route_part.route_allows_action(action=dispatch, owner_route=request_route)


def owner_request_payload(profile: WorkspaceProfile, study_id: str, action_type: str) -> dict[str, Any] | None:
    path = owner_request_path(profile, study_id, action_type)
    if path is None:
        return None
    return _read_json_object(path)


def owner_request_path(profile: WorkspaceProfile, study_id: str, action_type: str) -> Path | None:
    relative_path = OWNER_REQUEST_RELATIVE_PATHS.get(action_type)
    if relative_path is None:
        return None
    return profile.studies_root / study_id / relative_path


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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "current_consumer_dispatches",
    "explicit_action_dispatches",
    "owner_request_matches_dispatch",
    "owner_request_payload",
    "owner_request_path",
    "owner_request_route",
    "selected_dispatches",
]
