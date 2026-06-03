from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_receipt_consumption,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_control import owner_route as owner_route_part


def current_quality_repair_writer_handoff_route(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    action_type = _text(dispatch.get("action_type")) or ""
    if not current_quality_repair_writer_handoff_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return None
    route = dispatch_owner_route(dispatch)
    if not route:
        return None
    if not owner_route_part.route_allows_action(action=dispatch, owner_route=route):
        return None
    return route


def current_quality_repair_writer_handoff_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> bool:
    if not self_authorized_quality_repair_writer_handoff(
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return False
    batch = _read_json_object(
        profile.studies_root / study_id / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    )
    if not batch:
        return False
    if _text(batch.get("status")) != "handoff_ready":
        return False
    if _text(batch.get("next_owner")) != "write":
        return False
    handoff = _mapping(batch.get("writer_worker_handoff"))
    if _text(handoff.get("dispatch_authority")) != "quality_repair_batch_writer_handoff":
        return False
    if _text(handoff.get("action_type")) != "run_quality_repair_batch":
        return False
    if _text(handoff.get("next_executable_owner")) != "write":
        return False
    batch_eval_id = _text(batch.get("source_eval_id")) or dispatch_source_eval_id(handoff)
    dispatch_eval_id = dispatch_source_eval_id(dispatch)
    if batch_eval_id is None or dispatch_eval_id is None or batch_eval_id != dispatch_eval_id:
        return False
    batch_action_id = _text(handoff.get("action_id"))
    dispatch_action_id = _text(dispatch.get("action_id"))
    if batch_action_id and dispatch_action_id and batch_action_id != dispatch_action_id:
        return False
    if consumed_quality_repair_writer_handoff_dispatch(
        profile=profile,
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return False
    return True


def consumed_quality_repair_writer_handoff_dispatch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
) -> bool:
    if not self_authorized_quality_repair_writer_handoff(
        study_id=study_id,
        action_type=action_type,
        dispatch=dispatch,
    ):
        return False
    route = raw_dispatch_owner_route(dispatch) or dispatch_owner_route(dispatch)
    if not route:
        return False
    return bool(
        default_executor_execution_receipt_consumption(
            study_root=profile.studies_root / study_id,
            owner_route=route,
            actions=[{"action_type": "run_quality_repair_batch"}],
        )
    )


def self_authorized_quality_repair_writer_handoff(
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
    route = dispatch_owner_route(dispatch)
    route_reason = _text(route.get("owner_reason")) or _text(route.get("failure_signature"))
    if _text(route.get("next_owner")) != "write":
        return False
    if route_reason != "manuscript_story_surface_delta_missing":
        return False
    return owner_route_part.route_allows_action(action=dispatch, owner_route=route)


def dispatch_source_eval_id(dispatch: Mapping[str, Any]) -> str | None:
    route = dispatch_owner_route(dispatch)
    source_refs = _mapping(route.get("source_refs"))
    route_basis = _mapping(_mapping(route.get("currentness_contract")).get("basis")) or _mapping(
        source_refs.get("owner_route_currentness_basis")
    )
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    prompt_basis = _mapping(prompt_contract.get("owner_route_currentness_basis"))
    source_action = _mapping(dispatch.get("source_action"))
    source_action_refs = _mapping(source_action.get("source_refs"))
    return (
        _text(source_action.get("source_eval_id"))
        or _text(source_action_refs.get("source_eval_id"))
        or _text(source_refs.get("source_eval_id"))
        or _text(route_basis.get("source_eval_id"))
        or _text(prompt_basis.get("source_eval_id"))
        or _text(dispatch.get("source_eval_id"))
    )


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def raw_dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))


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
    "consumed_quality_repair_writer_handoff_dispatch",
    "current_quality_repair_writer_handoff_dispatch",
    "current_quality_repair_writer_handoff_route",
    "dispatch_owner_route",
    "dispatch_source_eval_id",
    "raw_dispatch_owner_route",
    "self_authorized_quality_repair_writer_handoff",
]
