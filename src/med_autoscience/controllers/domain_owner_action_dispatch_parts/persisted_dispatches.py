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
    "run_quality_repair_batch": Path("artifacts/supervision/requests/quality_repair_batch/latest.json"),
    "unit_harmonized_external_validation_rerun": Path("artifacts/supervision/requests/analysis_harmonization/latest.json"),
    "recover_transport_model_provenance": Path("artifacts/supervision/requests/source_provenance/latest.json"),
    "methodology_reframe_route_decision": Path("artifacts/supervision/requests/decision/latest.json"),
    "provenance_limited_harmonization_audit": Path(
        "artifacts/supervision/requests/provenance_limited_harmonization/latest.json"
    ),
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
            if not _self_authorized_quality_repair_writer_handoff(
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
    scan_payload: Mapping[str, Any] | None,
    supported_action_types: frozenset[str],
    dispatch_relative_root: Path,
) -> list[dict[str, Any]]:
    current_dispatches = current_consumer_dispatches(
        study_id=study_id,
        consumer_payload=consumer_payload,
        consumer_latest_path=consumer_latest_path,
    )
    if not action_types:
        return current_dispatches
    requested = set(action_types)
    selected = [payload for payload in current_dispatches if _text(payload.get("action_type")) in requested]
    selected_keys = {
        (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type")))
        for payload in selected
    }
    selected_by_key = {
        (_text(_mapping(payload.get("refs")).get("dispatch_path")), _text(payload.get("action_type"))): index
        for index, payload in enumerate(selected)
    }
    for payload in explicit_action_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=action_types,
        supported_action_types=supported_action_types,
        dispatch_relative_root=dispatch_relative_root,
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
    return selected


def _prefer_current_dispatch(
    *,
    profile: WorkspaceProfile,
    consumer_dispatch: Mapping[str, Any],
    persisted_dispatch: Mapping[str, Any],
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
) -> dict[str, Any]:
    if _persisted_quality_repair_writer_handoff_supersedes_consumer_inline(
        profile=profile,
        study_id=study_id,
        consumer_dispatch=consumer_dispatch,
        persisted_dispatch=persisted_dispatch,
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
    route_current = (
        1
        if route
        and owner_route_part.owner_route_matches(dispatch=dispatch, current_route=route)
        and owner_route_part.route_allows_action(action=dispatch, owner_route=route)
        else 0
    )
    stall_current = 1 if _dispatch_stall_matches_scan(dispatch=dispatch, current_study=current_study) else 0
    return route_current, stall_current


def _current_owner_route_from_scan(
    current_study: Mapping[str, Any],
    *,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if route:
        return route
    action_type = _text(dispatch.get("action_type"))
    for action in current_study.get("action_queue") or []:
        payload = _mapping(action)
        if _text(payload.get("action_type")) != action_type:
            continue
        route = owner_route_part.ensure_owner_route_v2(_mapping(payload.get("owner_route")))
        if route:
            return route
    return None


def current_owner_route_from_scan_payload(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
    dispatch: Mapping[str, Any] | None,
) -> tuple[dict[str, Any] | None, str | None]:
    current_study = _scan_study(scan_payload, study_id)
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if route:
        return route, "scan_latest"
    if dispatch is None:
        return None, None
    action_route = _current_action_queue_owner_route(current_study, dispatch=dispatch)
    if action_route is not None:
        return action_route, "scan_action_queue"
    return None, None


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
    request = owner_request_payload(profile, study_id, action_type)
    if not _owner_request_basics_match_dispatch(
        request=request,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return None
    request_route = _request_owner_route(request=request, action_type=action_type, dispatch=dispatch)
    if owner_route_part.owner_route_matches(dispatch=dispatch, current_route=request_route) and owner_route_part.route_allows_action(
        action=dispatch,
        owner_route=request_route,
    ):
        return owner_route_part.ensure_owner_route_v2(request_route)
    if _request_accepts_bridged_quality_repair_writer_handoff(
        request=request or {},
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    ):
        route = _dispatch_owner_route(dispatch)
        return route or None
    return None


def _owner_request_basics_match_dispatch(
    *,
    request: Mapping[str, Any] | None,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> bool:
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
    return True


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


def _request_accepts_bridged_quality_repair_writer_handoff(
    *,
    request: Mapping[str, Any],
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> bool:
    if _text(request.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return False
    if not _self_authorized_quality_repair_writer_handoff(
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return False
    route = _dispatch_owner_route(dispatch)
    route_refs = _mapping(route.get("source_refs"))
    if _text(route_refs.get("bridge_authority")) != "quality_repair_batch_writer_handoff_currentness_bridge":
        return False
    request_source_action = _mapping(request.get("source_action"))
    dispatch_source_action = _mapping(dispatch.get("source_action"))
    if not request_source_action or not dispatch_source_action:
        return False
    return _quality_repair_source_actions_match(
        request_source_action=request_source_action,
        dispatch_source_action=dispatch_source_action,
    )


def _quality_repair_source_actions_match(
    *,
    request_source_action: Mapping[str, Any],
    dispatch_source_action: Mapping[str, Any],
) -> bool:
    for key in ("surface", "blocked_reason", "source_eval_id"):
        expected = _text(dispatch_source_action.get(key))
        if expected is not None and _text(request_source_action.get(key)) != expected:
            return False
    expected_work_unit = _work_unit_id(dispatch_source_action.get("next_work_unit"))
    if expected_work_unit is not None and _work_unit_id(request_source_action.get("next_work_unit")) != expected_work_unit:
        return False
    expected_evidence_ref = _text(dispatch_source_action.get("repair_execution_evidence_ref"))
    if (
        expected_evidence_ref is not None
        and _text(request_source_action.get("repair_execution_evidence_ref")) != expected_evidence_ref
    ):
        return False
    return True


def _self_authorized_quality_repair_writer_handoff(
    *,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> bool:
    if action_type != "run_quality_repair_batch":
        return False
    if _text(dispatch.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return False
    if _text(dispatch.get("study_id")) != study_id:
        return False
    if _text(dispatch.get("next_executable_owner")) != "write":
        return False
    source_action = _mapping(dispatch.get("source_action"))
    if _text(source_action.get("surface")) != "quality_repair_batch":
        return False
    if _text(source_action.get("blocked_reason")) != "manuscript_story_surface_delta_missing":
        return False
    route = _dispatch_owner_route(dispatch)
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    if _text(route.get("next_owner")) != "write":
        return False
    if route_reason != "manuscript_story_surface_delta_missing":
        return False
    return owner_route_part.route_allows_action(action=dispatch, owner_route=route)


def _persisted_quality_repair_writer_handoff_supersedes_consumer_inline(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    consumer_dispatch: Mapping[str, Any],
    persisted_dispatch: Mapping[str, Any],
) -> bool:
    action_type = _text(persisted_dispatch.get("action_type"))
    if not _self_authorized_quality_repair_writer_handoff(
        study_id=study_id,
        action_type=action_type or "",
        dispatch=persisted_dispatch,
    ):
        return False
    if not owner_request_matches_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type or "",
        dispatch=persisted_dispatch,
    ):
        return False
    return not _self_authorized_quality_repair_writer_handoff(
        study_id=study_id,
        action_type=_text(consumer_dispatch.get("action_type")) or "",
        dispatch=consumer_dispatch,
    )


def _owner_request_fallback_route(*, action_type: str, dispatch: Mapping[str, Any]) -> dict[str, Any]:
    if action_type != "return_to_ai_reviewer_workflow":
        return {}
    dispatch_route = _dispatch_owner_route(dispatch)
    if not dispatch_route:
        return {}
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=dispatch_route):
        return {}
    return dispatch_route


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


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "current_owner_route_from_scan_payload",
    "current_consumer_dispatches",
    "explicit_action_dispatches",
    "owner_request_matches_dispatch",
    "owner_request_payload",
    "owner_request_path",
    "owner_request_route",
    "selected_dispatches",
]
