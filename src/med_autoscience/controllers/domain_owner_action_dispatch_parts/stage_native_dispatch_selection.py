from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import stage_native_next_action_admission
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part

from . import progress_blocking_selection


RuntimeCurrentDispatches = Callable[..., list[dict[str, Any]]]


def next_action(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    payload = _read_json_object(profile.studies_root / study_id / "control" / "next_action.json")
    if not payload:
        return None
    if _text(payload.get("status")) != "ready_for_owner_action":
        return None
    action_type = next_action_type(payload)
    if action_type is None:
        return None
    if not stage_native_next_action_admission.default_dispatch_allowed(payload):
        return None
    return {
        **payload,
        "action_type": action_type,
    }


def next_action_superseded_by_current_control(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    next_action: Mapping[str, Any],
    current_study: Mapping[str, Any],
    consumer_dispatches: list[dict[str, Any]],
    runtime_current_dispatches_only: RuntimeCurrentDispatches,
) -> bool:
    if not current_study:
        return False
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    allowed_actions = {_text(item) for item in route.get("allowed_actions") or []}
    allowed_actions.discard(None)
    if progress_blocking_selection.fresh_progress_typed_blocker_reason(
        _mapping(read_fresh_study_progress(profile=profile, study_id=study_id).get("current_execution_envelope"))
    ) == "medical_paper_readiness_missing" and (
        not allowed_actions
        or "complete_medical_paper_readiness_surface" in allowed_actions
        or _text(next_action.get("action_type")) in allowed_actions
    ):
        return False
    current_dispatches = runtime_current_dispatches_only(
        study_id=study_id,
        dispatches=consumer_dispatches,
        current_study=current_study,
    )
    if current_dispatches:
        return not bool(
            next_action_dispatches_only(
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


def next_action_dispatches_only(
    *,
    next_action: Mapping[str, Any],
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if dispatch_matches_next_action(next_action=next_action, dispatch=dispatch)
    ]


def next_action_matches_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> bool:
    current_next_action = next_action(profile=profile, study_id=study_id)
    if current_next_action is None:
        return False
    return dispatch_matches_next_action(next_action=current_next_action, dispatch=dispatch)


def dispatch_matches_next_action(
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
    route = dispatch_owner_route(dispatch)
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


def next_action_type(next_action: Mapping[str, Any]) -> str | None:
    direct = _text(next_action.get("action_type"))
    if direct is not None:
        return direct
    action_id = _text(next_action.get("action_id"))
    if action_id is not None and not action_id.startswith("stage-native-next-action::"):
        return action_id
    return None


def without_unauthorized_dispatches(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if not dispatch_uses_stage_native_next_action(dispatch)
        or next_action_matches_dispatch(
            profile=profile,
            study_id=study_id,
            dispatch=dispatch,
        )
    ]


def dispatch_uses_stage_native_next_action(dispatch: Mapping[str, Any]) -> bool:
    return stage_native_next_action_admission.dispatch_uses_stage_native_next_action(dispatch)


def read_fresh_study_progress(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any]:
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


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
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
    "dispatch_matches_next_action",
    "dispatch_owner_route",
    "dispatch_uses_stage_native_next_action",
    "next_action",
    "next_action_dispatches_only",
    "next_action_matches_dispatch",
    "next_action_superseded_by_current_control",
    "next_action_type",
    "read_fresh_study_progress",
    "without_unauthorized_dispatches",
]
